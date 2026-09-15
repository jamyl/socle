"""SEC EDGAR provider — the one finance-specific module in the stack.

Three endpoints, all verified live: full-text search over filing documents
(`efts.sec.gov/LATEST/search-index`), the per-company submissions index
(`data.sec.gov/submissions/CIK##########.json`), and XBRL company facts
(`data.sec.gov/api/xbrl/companyfacts/…`). Everything else — cache, HTTP,
throttling, the Document contract, dedup — is the shared layer, unchanged.

Two things are specific to this source and non-negotiable:

1. The SEC *requires* a declared User-Agent naming a contact, and caps clients
   at 10 requests/second (https://www.sec.gov/os/accessing-edgar-data). Where
   the academic APIs treat a contact as politeness, here it is policy, so this
   module refuses to make any request until `DEJAVU_CONTACT` is set. Fetching
   with a placeholder address would be a misrepresentation, not a shortcut.
2. A filing is not a reading unit. A 10-K runs to hundreds of pages, so
   `fetch_sections` splits it on its "Item N." headings and each section is
   read in isolation (PLAN.md §6).

SEDAR+ (Canadian filings) has no public API — probing returns 301/302 with
Radware bot-manager cookies, i.e. a protected JavaScript application. It is out
of scope and deliberately not scraped.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

from .. import cache, http
from ..document import CLEAR, HAS_CORRECTION, UNKNOWN, Document
from .base import Provider, ProviderResult, Query

FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
COMPANY_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"

# Filings are large — Apple's last 10-K primary document is ~1 MB of inline
# XBRL. A whole Item 1A can exceed a reader's useful window on its own, so each
# section is capped and the truncation is stated in the text rather than hidden.
MAX_SECTION_CHARS = 20000
# Below this, a match is almost always a table-of-contents line rather than the
# section itself; every 10-K lists its Items twice for that reason.
MIN_SECTION_CHARS = 400

# Concepts worth quoting in a materiality score. All are us-gaap tags observed
# in real companyfacts payloads; absent ones are reported, not faked.
DEFAULT_CONCEPTS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "NetIncomeLoss",
    "OperatingIncomeLoss",
    "Assets",
    "Liabilities",
    "StockholdersEquity",
]

CONTACT_REQUIRED = (
    "SEC EDGAR requires a declared User-Agent naming a contact "
    "(https://www.sec.gov/os/accessing-edgar-data). Set it before searching filings:\n"
    '  export DEJAVU_CONTACT="Your Name your@email"\n'
    "dejavu will not query the SEC with a placeholder address."
)


class ContactRequiredError(RuntimeError):
    """Raised instead of fetching when DEJAVU_CONTACT is unset or still the default."""


def require_contact() -> str:
    """Fail loudly *before* any SEC request if no real contact is declared."""
    value = http.contact()
    if value == http.DEFAULT_CONTACT:
        raise ContactRequiredError(CONTACT_REQUIRED)
    return value


def sec_headers() -> dict:
    """Override the shared User-Agent with the exact form the SEC asks for.

    Measured, not guessed: `dejavu/0.2.0 (https://github.com/…; mailto:…)` —
    the string every other provider gets — returns 403 from efts.sec.gov, and
    bisecting the header shows the project URL is what trips it. The SEC's own
    sample is `Sample Company Name AdminContact@<domain>`, so the contact alone
    is sent here (https://www.sec.gov/os/accessing-edgar-data).
    """
    return {"User-Agent": require_contact()}


# Parsing helpers ---------------------------------------------------------


def split_source_id(source_id: str) -> tuple:
    """Split an EDGAR full-text `_id` into (accession, primary document).

    The id is literally `0000320193-24-000123:aapl-20240928.htm`; the second
    half is the filename needed to build the document URL, and there is no
    other field in the hit that carries it.
    """
    accession, _, document = source_id.partition(":")
    return accession, (document or None)


def archive_url(cik: str, accession: str, document: str | None) -> str:
    """Canonical EDGAR URL: /Archives/edgar/data/{cik}/{accession-no-dashes}/{document}.

    Verified live: the CIK must be unpadded (a zero-padded CIK 301-redirects)
    and the accession number must have its dashes stripped in the directory
    segment while keeping them in the id.
    """
    bare_cik = str(int(cik)) if str(cik).isdigit() else str(cik)
    folder = accession.replace("-", "")
    base = f"{ARCHIVES}/{bare_cik}/{folder}"
    return f"{base}/{document}" if document else f"{base}/{accession}-index.htm"


def split_display_name(display: str) -> tuple:
    """`"Apple Inc.  (AAPL)  (CIK 0000320193)"` -> ("Apple Inc.", "AAPL")."""
    text = " ".join((display or "").split())
    cik_match = re.search(r"\(CIK\s+(\d+)\)\s*$", text)
    if cik_match:
        text = text[: cik_match.start()].strip()
    ticker = None
    ticker_match = re.search(r"\(([A-Z][A-Z0-9.\-]*)\)\s*$", text)
    if ticker_match:
        ticker = ticker_match.group(1)
        text = text[: ticker_match.start()].strip()
    return text, ticker


def parse_search(payload: dict, section: str | None = None):
    """Parse the Elasticsearch response into (documents, total_available).

    `total_available` matters for the same reason it does on arXiv: a filter
    that matches nothing has to be distinguishable from a field nobody has
    written about.
    """
    hits = (payload or {}).get("hits", {})
    total = hits.get("total", {}).get("value")

    documents = []
    for hit in hits.get("hits", []):
        source = hit.get("_source", {})
        accession = source.get("adsh") or ""
        _, document = split_source_id(hit.get("_id", ""))
        if not accession:
            continue

        cik = (source.get("ciks") or [""])[0]
        company, ticker = split_display_name((source.get("display_names") or [""])[0])
        form = source.get("form") or (source.get("root_forms") or [None])[0]
        period = source.get("period_ending")
        # 8-K hits carry their item numbers; 10-K/10-Q hits do not, so the
        # section is only known after fetch_sections has run.
        items = source.get("items") or []
        known_section = section or (items[0] if len(items) == 1 else None)

        title = " ".join(part for part in (company, form, period) if part)
        if known_section:
            title = f"{title} — {known_section}"

        documents.append(
            Document(
                id=f"{accession}#{known_section}" if known_section else accession,
                title=title,
                abstract="",  # filled per-section by fetch_sections; see filings.py --sections
                venue=form,
                date=source.get("file_date"),
                citations=None,  # no meaningful citation graph over filings
                urls={"landing": archive_url(cik, accession, document)},
                source="edgar",
                retraction_status=UNKNOWN,  # amendment status; needs submissions
                has_code=False,
                authors=[company] if company else [],
                categories=[c for c in (source.get("root_forms") or []) if c],
                extra={
                    "accession": accession,
                    "cik": cik,
                    "company": company,
                    "ticker": ticker,
                    "primary_document": document,
                    "form": form,
                    "file_type": source.get("file_type"),
                    "period_ending": period,
                    "items": items,
                    "sics": source.get("sics") or [],
                    "locations": source.get("biz_locations") or [],
                },
            )
        )

    return documents, total


def parse_submissions(payload: dict) -> dict:
    """Flatten `filings.recent`'s parallel arrays into one record per filing.

    The API stores each field as its own index-aligned list — `form[i]`,
    `accessionNumber[i]`, `primaryDocument[i]` describe the same filing — which
    is compact on the wire and unusable until it is zipped back together.
    """
    recent = ((payload or {}).get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    fields = ("accessionNumber", "filingDate", "reportDate", "primaryDocument", "items", "isXBRL")

    filings = []
    for index, form in enumerate(forms):
        record = {"form": form}
        for field in fields:
            values = recent.get(field) or []
            record[field] = values[index] if index < len(values) else None
        filings.append(record)

    return {
        "cik": payload.get("cik"),
        "name": payload.get("name"),
        "tickers": payload.get("tickers") or [],
        "sic": payload.get("sic"),
        "sic_description": payload.get("sicDescription"),
        "filings": filings,
    }


def amendment_status(accession: str, filings: list) -> str:
    """Reinterpret retraction_status as amendment status (PLAN.md §6).

    A filing is superseded when the company later filed the `/A` variant of the
    same form covering the same period — that is the filings-world equivalent of
    a correction notice.
    """
    this = next((f for f in filings if f.get("accessionNumber") == accession), None)
    if this is None:
        return UNKNOWN
    amended_form = f"{this.get('form')}/A"
    for other in filings:
        if other.get("form") != amended_form:
            continue
        if other.get("reportDate") and other["reportDate"] == this.get("reportDate"):
            return HAS_CORRECTION
    return CLEAR


# Section extraction ------------------------------------------------------

# Matches "Item 1A.", "ITEM 7 —", "Item 5.02" at the start of a line. The
# optional `.NN` covers 8-K item numbering, which is dotted rather than lettered.
ITEM_HEADING = re.compile(
    r"^item\s+(\d{1,2}(?:\.\d{2})?[a-z]?)\s*[.:\)\-–—]?\s*(.{0,120})$",
    re.IGNORECASE,
)

# Tags whose boundaries are real line breaks in the rendered filing. Everything
# else (span, font, ix:nonFraction …) only gets a space, so words that a filer
# split across inline tags still read as words.
_BLOCK_TAGS = {
    "p", "div", "br", "tr", "table", "td", "th", "li", "ul", "ol",
    "h1", "h2", "h3", "h4", "h5", "h6", "section", "hr", "body",
}
# Inline XBRL hides an enormous fact dump in these; it is machine metadata and
# would otherwise dominate the extracted text.
_SKIP_TAGS = {"script", "style", "ix:header", "ix:hidden"}


class _FilingTextExtractor(HTMLParser):
    """Turn filing HTML into plain lines, stdlib only (no third-party deps, ever)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")
        else:
            self._parts.append(" ")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0 and data.strip():
            self._parts.append(data)

    def text(self) -> str:
        joined = "".join(self._parts).replace("\xa0", " ")
        lines = [" ".join(line.split()) for line in joined.split("\n")]
        return "\n".join(line for line in lines if line)


def html_to_text(html: str) -> str:
    parser = _FilingTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.text()


def _clean_heading(number: str, tail: str) -> str:
    """"1A", "Risk Factors ......... 15" -> "Item 1A. Risk Factors"."""
    title = re.sub(r"[.…\s]{3,}.*$", "", tail).strip(" .:–—-")
    title = re.sub(r"\s+\d{1,4}$", "", title).strip()
    return f"Item {number.upper()}." + (f" {title}" if title else "")


def split_sections(text: str) -> list:
    """Split filing text into `[{"heading", "text"}]` on its Item headings.

    Two realities of filed HTML shape this: every 10-K prints its Item list
    once in the table of contents and once as the body, and some filers repeat a
    heading in a running header. Keeping, per item number, only the longest body
    resolves both without guessing at the document structure.
    """
    lines = text.split("\n")
    marks = []
    for index, line in enumerate(lines):
        match = ITEM_HEADING.match(line)
        if match:
            marks.append((index, match.group(1), match.group(2)))

    candidates = []
    for position, (index, number, tail) in enumerate(marks):
        end = marks[position + 1][0] if position + 1 < len(marks) else len(lines)
        body = "\n".join(lines[index + 1 : end]).strip()
        candidates.append((number.upper(), _clean_heading(number, tail), body, index))

    best = {}
    for number, heading, body, index in candidates:
        if len(body) < MIN_SECTION_CHARS:
            continue
        if number not in best or len(body) > len(best[number][1]):
            best[number] = (heading, body, index)

    sections = []
    for _, (heading, body, index) in sorted(best.items(), key=lambda item: item[1][2]):
        if len(body) > MAX_SECTION_CHARS:
            body = body[:MAX_SECTION_CHARS] + f"\n[truncated at {MAX_SECTION_CHARS} characters]"
        sections.append({"heading": heading, "text": body})
    return sections


def is_html_document(name: str | None) -> bool:
    return bool(name) and name.lower().endswith((".htm", ".html"))


# EDGAR's own index pages, and the XBRL/exhibit noise that shares the directory
# with the filing itself. An exhibit is a real document but it is not the
# filing, and its Item numbering (if any) belongs to a different scheme.
_INDEX_FILE = re.compile(r"(-index(-headers)?\.html?|^index\.html?)$", re.IGNORECASE)
# The digit bound keeps exhibit numbering (ex-101, ex1071, ex99) from also
# matching a ticker-plus-period filename like `ex-20241231.htm`.
_EXHIBIT_FILE = re.compile(r"exhibit|(^|[^a-z])ex[-_]?\d{1,4}(?!\d)", re.IGNORECASE)


def pick_html_document(index_payload: dict) -> dict | None:
    """Choose the main filing document from a directory listing.

    The largest non-exhibit, non-index HTML file is the filing: exhibits and
    EDGAR's own index pages are the only other .htm entries of any size, and the
    filing itself dwarfs them (11.6 MB against 121 KB in the case that exposed
    this). `size` is an empty string on some entries, so it is parsed defensively
    rather than trusted.
    """
    best = None
    for item in (index_payload.get("directory") or {}).get("item") or []:
        name = item.get("name") or ""
        if not is_html_document(name) or _INDEX_FILE.search(name) or _EXHIBIT_FILE.search(name):
            continue
        raw = str(item.get("size") or "").strip()
        size = int(raw) if raw.isdigit() else 0
        if best is None or size > best[0]:
            best = (size, {"name": name, "size": size})
    return best[1] if best else None


def filing_index(cik: str, accession: str, *, use_cache: bool = True) -> dict:
    """Fetch a filing's directory listing (`index.json`) — every file EDGAR stored."""
    url = f"{archive_url(cik, accession, None).rsplit('/', 1)[0]}/index.json"
    return http.get(
        url, headers=sec_headers(), cache_ttl=cache.TTL_DOCUMENT, use_cache=use_cache
    ).json()


def fetch_sections(accession: str, cik: str, primary_document: str, *, use_cache: bool = True):
    """Fetch a filing's main document and split it. Returns `(sections, notes)`.

    The notes are the point, not decoration. An empty section list has at least
    four different causes — the primary document is a PDF, the fetch 404'd, the
    directory holds no filing-grade HTML, or the text has no Item headings — and
    a reader who cannot tell them apart will read "no sections" as "nothing to
    disclose here". Every path out of this function that returns nothing says why.

    Cached with TTL_DOCUMENT: a filing addressed by accession number is
    immutable, so it never needs re-fetching.
    """
    sec_headers()  # refuse before any request if no contact is declared
    notes = []
    document = primary_document

    if not is_html_document(document):
        named = (
            f"the primary document '{primary_document}' is not HTML "
            "(likely a scanned or typeset PDF, which is never parsed here — stdlib only)"
            if primary_document
            else "the search hit names no primary document"
        )
        notes.append(
            f"{accession}: {named}. Looking for the filing's HTML copy in its EDGAR directory."
        )
        document = None

    used_index = False
    while True:
        if document is None:
            used_index = True
            try:
                chosen = pick_html_document(filing_index(cik, accession, use_cache=use_cache))
            except (http.HTTPError, ValueError) as exc:
                notes.append(f"{accession}: the filing's directory index could not be read ({exc}); "
                             "no sections were extracted.")
                return [], notes
            if chosen is None:
                notes.append(
                    f"{accession}: the filing directory lists no non-exhibit HTML document, so "
                    "there is nothing to split into sections. Read the filing at its landing URL "
                    "instead — this is a gap in the extraction, not an empty filing."
                )
                return [], notes
            document = chosen["name"]
            notes.append(
                f"{accession}: sections were extracted from '{document}' "
                f"({chosen['size']} bytes), found via the filing directory index, "
                f"not from the primary document named in the search hit."
            )

        url = archive_url(cik, accession, document)
        try:
            response = http.get(
                url, headers=sec_headers(), cache_ttl=cache.TTL_DOCUMENT, use_cache=use_cache
            )
            break
        except http.HTTPError as exc:
            notes.append(f"{accession}: fetching '{document}' failed ({exc}).")
            if used_index:
                notes.append(f"{accession}: no sections were extracted.")
                return [], notes
            document = None  # one retry, through the directory index

    sections = split_sections(html_to_text(response.body))
    if not sections:
        notes.append(
            f"{accession}: '{document}' parsed but no 'Item N.' headings matched, so it yielded "
            "no sections. Expect this on exhibits, wrappers and filings whose headings are "
            "images. The filing is not empty — it was not split. Read it at its landing URL."
        )
    return sections, notes


# XBRL facts --------------------------------------------------------------


def _latest_annual(concept: dict):
    """The most recent annual (10-K, full-year) observation for one concept."""
    annual = [
        entry
        for entry in (concept.get("units", {}).get("USD") or [])
        if str(entry.get("form", "")).startswith("10-K") and entry.get("fp") == "FY"
    ]
    if not annual:
        return None
    return max(annual, key=lambda entry: entry.get("end") or "")


def company_facts(cik: str, concepts: list | None = None, *, use_cache: bool = True) -> dict:
    """Most recent annual USD value per us-gaap concept, so a score can cite a number.

    Materiality is the finance rubric's version of "practicality" and it is
    worthless unquantified; this is where the figure comes from.
    """
    url = COMPANY_FACTS.format(cik=int(cik))
    payload = http.get(
        url, headers=sec_headers(), cache_ttl=cache.TTL_FILING_SEARCH, use_cache=use_cache
    ).json()

    wanted = concepts or DEFAULT_CONCEPTS
    us_gaap = (payload.get("facts") or {}).get("us-gaap") or {}

    found, missing = {}, []
    for name in wanted:
        entry = _latest_annual(us_gaap.get(name) or {})
        if entry is None:
            missing.append(name)
            continue
        found[name] = {
            "label": us_gaap[name].get("label"),
            "value": entry.get("val"),
            "unit": "USD",
            "period_end": entry.get("end"),
            "fiscal_year": entry.get("fy"),
            "form": entry.get("form"),
            "accession": entry.get("accn"),
        }

    return {
        "cik": payload.get("cik"),
        "entity_name": payload.get("entityName"),
        "concepts": found,
        "not_reported": missing,
    }


# Provider ----------------------------------------------------------------


class EdgarProvider(Provider):
    name = "edgar"

    def __init__(self, forms=None, ciks=None, date_from=None, date_to=None, sections=False):
        self.forms = list(forms or [])
        self.ciks = list(ciks or [])
        self.date_from = date_from
        self.date_to = date_to
        self.sections = sections

    def search(self, query: Query) -> ProviderResult:
        result = ProviderResult(provider=self.name)

        try:
            headers = sec_headers()
        except ContactRequiredError as exc:
            result.notes.append(str(exc))
            result.failed = True
            return result

        phrase = query.phrase()
        url = http.build_url(
            FULL_TEXT_SEARCH,
            {
                # The quotes are what make this a phrase search rather than an
                # OR over the words; without them "supply chain" matches "chain".
                "q": f'"{phrase}"' if " " in phrase else phrase,
                "forms": ",".join(self.forms),
                "ciks": ",".join(self.ciks),
                "startdt": self.date_from,
                "enddt": self.date_to,
            },
        )
        result.queries.append(url)

        try:
            response = http.get(
                url,
                accept="application/json",
                headers=headers,
                cache_ttl=cache.TTL_FILING_SEARCH,
                use_cache=query.use_cache,
            )
        except http.HTTPError as exc:
            result.notes.append(f"EDGAR full-text search failed: {exc}")
            result.failed = True
            return result

        if response.stale:
            result.notes.append(
                f"Served a cached (stale) EDGAR response for '{phrase}' — network unavailable."
            )

        try:
            documents, total = parse_search(response.json())
        except ValueError as exc:
            result.notes.append(f"EDGAR returned unparseable JSON: {exc}")
            result.failed = True
            return result

        result.total_available = total
        if total == 0:
            result.notes.append(
                f"EDGAR reported 0 filings matching '{phrase}'"
                + (f" in {', '.join(self.forms)}" if self.forms else "")
                + ". The query is valid and the answer is genuinely empty. Not padded."
            )

        result.documents = documents
        self.apply_recency_filter(result, query.since_years)
        result.documents = result.documents[: query.limit]

        # Full-text search only covers filings from 2001 onward — a silent floor
        # that looks like "this risk is recent" if nobody says it out loud.
        result.notes.append(
            "EDGAR full-text search covers filings from 2001 onward; anything earlier "
            "is invisible to this query."
        )
        self._annotate_amendments(result, query)
        return result

    def _annotate_amendments(self, result: ProviderResult, query: Query) -> None:
        """Fill retraction_status from submissions — only when scoped to one company.

        A cross-company search would need one submissions fetch per issuer (each
        a megabyte), so outside a CIK-scoped search the status stays UNKNOWN and
        the note says why rather than implying the filings were checked.
        """
        if len(self.ciks) != 1:
            if result.documents:
                result.notes.append(
                    "Amendment status is 'unknown': detecting a superseding /A filing "
                    "needs the issuer's submissions index, fetched only for a "
                    "--cik-scoped search."
                )
            return

        try:
            payload = http.get(
                SUBMISSIONS.format(cik=int(self.ciks[0])),
                accept="application/json",
                headers=sec_headers(),
                cache_ttl=cache.TTL_FILING_SEARCH,
                use_cache=query.use_cache,
            ).json()
        except (http.HTTPError, ValueError) as exc:
            result.notes.append(f"Could not check amendments for CIK {self.ciks[0]}: {exc}")
            return

        filings = parse_submissions(payload)["filings"]
        for doc in result.documents:
            doc.retraction_status = amendment_status(doc.extra["accession"], filings)
