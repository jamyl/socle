"""Europe PMC REST provider.

The life-sciences half of the corpus, and the only practical way to reach
bioRxiv/medRxiv by keyword: api.biorxiv.org has no search endpoint, but Europe
PMC indexes those preprints under the "PPR" corpus alongside MEDLINE records,
so one call covers both published and preprint biology.

`resultType=core` is not optional — the default (lite) response carries no
abstract, and an abstract-less document is useless to the isolated read.

API docs: https://europepmc.org/RestfulWebService
"""

from __future__ import annotations

import html
import re

from .. import cache, http
from ..document import RETRACTED, UNKNOWN, Document, normalize_doi
from .base import Provider, ProviderResult, Query

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# `source` is Europe PMC's corpus code, and it is the only signal in the
# response that says what kind of record this is. Codes seen in live feeds.
SOURCE_LABELS = {
    "MED": "MEDLINE",
    "PMC": "PubMed Central",
    "PPR": "Preprint",
    "AGR": "Agricola",
    "PAT": "Patent",
}

# MEDLINE tags a retracted article with this publication type (observed on
# PMID 39862236). "Retraction of Publication" is the notice itself, a different
# record, so the match has to be exact rather than a substring test.
RETRACTED_PUB_TYPE = "retracted publication"

_SECTION_HEADER = re.compile(r"<(h[1-6]|title)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")


def plain_abstract(text: str | None) -> str:
    """Flatten Europe PMC's marked-up abstract into readable prose.

    `abstractText` arrives with structural markup — `<h4>Motivation</h4>` on
    MEDLINE records, `<title>Abstract</title><p>…` on preprints. Left alone,
    the reader model sees raw tags mid-sentence, so headers become inline
    `Header: ` labels and every other tag is dropped.
    """
    if not text:
        return ""
    cleaned = _SECTION_HEADER.sub(lambda m: f" {m.group(2).strip()}: ", text)
    cleaned = _TAG.sub(" ", cleaned)
    return " ".join(html.unescape(cleaned).split())


def _flag(value) -> bool:
    """Europe PMC spells its booleans as the strings "Y" / "N"."""
    return str(value).strip().upper() == "Y"


def _authors(record: dict) -> list:
    """Full names when the record carries them, else the `authorString` list.

    `authorList.author[].fullName` is the initials form ("Mattsson B");
    firstName/lastName are present on most records and read far better.
    """
    authors = []
    for author in (record.get("authorList") or {}).get("author", []):
        first, last = author.get("firstName"), author.get("lastName")
        name = f"{first} {last}" if first and last else author.get("fullName")
        if name:
            authors.append(name)
    if authors:
        return authors
    return [a.strip() for a in (record.get("authorString") or "").split(",") if a.strip()]


def _urls(record: dict) -> dict:
    """A landing page, preferring the open-access copy over the paywalled DOI."""
    entries = (record.get("fullTextUrlList") or {}).get("fullTextUrl", [])
    open_access = next(
        (e.get("url") for e in entries if e.get("availabilityCode") == "OA" and e.get("url")),
        None,
    )
    landing = open_access or next((e.get("url") for e in entries if e.get("url")), None)
    return {k: v for k, v in {"landing": landing, "oa": open_access}.items() if v}


def _date(record: dict) -> str | None:
    journal_info = record.get("journalInfo") or {}
    return (
        record.get("firstPublicationDate")
        or journal_info.get("printPublicationDate")
        or record.get("pubYear")  # a bare year is honest; inventing a month is not
        or None
    )


def _retraction_status(record: dict) -> str:
    pub_types = (record.get("pubTypeList") or {}).get("pubType", [])
    if any(str(t).strip().lower() == RETRACTED_PUB_TYPE for t in pub_types):
        return RETRACTED
    # Europe PMC publishes no "this work is fine" flag, so silence means
    # unknown here, never clear.
    return UNKNOWN


def parse_search(payload: dict):
    """Parse a search response into (documents, hit_count)."""
    hit_count = payload.get("hitCount")
    documents = []

    for record in (payload.get("resultList") or {}).get("result", []):
        source = record.get("source") or ""
        record_id = record.get("id") or ""
        if not record_id:
            continue

        journal = ((record.get("journalInfo") or {}).get("journal") or {}).get("title")

        documents.append(
            Document(
                # source+id is the composite key Europe PMC itself uses; ids are
                # only unique within a corpus.
                id=f"europepmc:{source}:{record_id}",
                title=" ".join((record.get("title") or "").split()),
                abstract=plain_abstract(record.get("abstractText")),
                venue=journal or SOURCE_LABELS.get(source, f"Europe PMC ({source})"),
                date=_date(record),
                citations=record.get("citedByCount"),
                urls=_urls(record),
                source="europepmc",
                retraction_status=_retraction_status(record),
                has_code=None,
                authors=_authors(record),
                doi=normalize_doi(record.get("doi")),
                extra={
                    "source": source,  # the corpus code, not Document.source
                    "pmid": record.get("pmid"),
                    "isOpenAccess": _flag(record.get("isOpenAccess")),
                    "inEPMC": _flag(record.get("inEPMC")),
                    "peer_reviewed": source == "MED",
                    "preprint": source == "PPR",
                },
            )
        )

    return documents, hit_count


class EuropePMCProvider(Provider):
    name = "europepmc"

    def search(self, query: Query) -> ProviderResult:
        result = ProviderResult(provider=self.name)

        phrase = query.phrase()
        url = http.build_url(
            API,
            {
                "query": phrase,
                "format": "json",
                "pageSize": query.limit,
                "resultType": "core",  # lite returns no abstract
            },
        )
        result.queries.append(phrase)

        try:
            response = http.get(
                url,
                accept="application/json",
                cache_ttl=cache.TTL_SEARCH,
                use_cache=query.use_cache,
            )
        except http.HTTPError as exc:
            result.notes.append(f"Europe PMC request failed for '{phrase}': {exc}")
            result.failed = True
            return result

        if response.stale:
            result.notes.append(
                f"Served a cached (stale) Europe PMC response for '{phrase}' — network unavailable."
            )

        try:
            documents, hit_count = parse_search(response.json())
        except ValueError as exc:
            result.notes.append(f"Europe PMC returned unparseable JSON for '{phrase}': {exc}")
            result.failed = True
            return result

        result.total_available = hit_count
        if hit_count == 0:
            result.notes.append(
                f"Europe PMC reported hitCount=0 for '{phrase}'. The query is valid but "
                "matched nothing — either the terms are too specific or this really is "
                "unexplored ground. Not padded."
            )

        result.documents.extend(documents)
        self.apply_recency_filter(result, query.since_years)
        return result
