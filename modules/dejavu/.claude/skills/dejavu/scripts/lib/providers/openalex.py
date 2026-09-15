"""OpenAlex works API provider.

The cross-domain counterweight to arXiv: 260M+ works with no subject ceiling,
plus the two fields arXiv cannot give us — a citation count and a retraction
flag that was actually checked. No key needed; `mailto` buys the polite pool.

API docs: https://docs.openalex.org/api-entities/works
"""

from __future__ import annotations

from .. import cache, http
from ..document import CLEAR, RETRACTED, Document, normalize_arxiv_id, normalize_doi
from .base import Provider, ProviderResult, Query

API = "https://api.openalex.org/works"


def reconstruct_abstract(inverted_index: dict | None) -> str:
    """Rebuild the running text from OpenAlex's {word: [positions]} index.

    OpenAlex never ships an abstract as a string — for licensing reasons it
    publishes only the word-to-positions map, and the isolated read is worth
    little without prose. A missing index is normal rather than an error:
    older records and, in the sample checked, retracted ones carry none.
    """
    if not inverted_index:
        return ""
    slots = {}
    for word, positions in inverted_index.items():
        for position in positions:
            slots[position] = word
    return " ".join(slots[i] for i in sorted(slots))


def parse_works(payload: dict):
    """Parse a /works response into (documents, total_count).

    `meta.count` is the whole corpus size behind the query, not the page size;
    like arXiv's totalResults it is what distinguishes "nothing exists" from
    "we only asked for ten".
    """
    total = (payload.get("meta") or {}).get("count")

    documents = []
    for work in payload.get("results") or []:
        short_id = (work.get("id") or "").rsplit("/", 1)[-1]
        if not short_id:
            continue

        primary = work.get("primary_location") or {}
        source = primary.get("source") or {}
        best_oa = work.get("best_oa_location") or {}
        open_access = work.get("open_access") or {}

        urls = {
            "landing": primary.get("landing_page_url"),
            "pdf": primary.get("pdf_url") or best_oa.get("pdf_url"),
            "oa": open_access.get("oa_url"),
        }
        urls = {k: v for k, v in urls.items() if v}

        doi = normalize_doi(work.get("doi"))
        # OpenAlex has no arXiv id field; preprints are recorded under a
        # 10.48550/arxiv.<id> DOI, which normalize_arxiv_id reduces to the id.
        arxiv_id = normalize_arxiv_id(doi) if (doi or "").startswith("10.48550/arxiv.") else None

        topics = [t.get("display_name") for t in (work.get("topics") or []) if t.get("display_name")]
        primary_topic = (work.get("primary_topic") or {}).get("display_name")
        if not topics and primary_topic:
            topics = [primary_topic]

        documents.append(
            Document(
                id=f"openalex:{short_id}",
                title=work.get("title") or work.get("display_name") or "",
                abstract=reconstruct_abstract(work.get("abstract_inverted_index")),
                venue=source.get("display_name") or None,
                date=work.get("publication_date") or None,
                citations=work.get("cited_by_count"),
                urls=urls,
                source="openalex",
                # OpenAlex looked at the question, so "clear" is honest here in
                # a way it would not be for a provider that never checks.
                retraction_status=RETRACTED if work.get("is_retracted") else CLEAR,
                has_code=None,  # OpenAlex publishes no code links
                authors=[
                    (a.get("author") or {}).get("display_name")
                    for a in (work.get("authorships") or [])
                    if (a.get("author") or {}).get("display_name")
                ],
                doi=doi,
                arxiv_id=arxiv_id,
                categories=topics,
                extra={
                    "oa_status": open_access.get("oa_status"),
                    "type": work.get("type"),
                    # Field-weighted citation impact: citations normalised
                    # against the field, so 2 cites in maths beats 20 in bio.
                    "fwci": work.get("fwci"),
                    "referenced_works_count": len(work.get("referenced_works") or []),
                    "source_type": source.get("type"),
                    "peer_reviewed": source.get("type") == "journal",
                },
            )
        )

    return documents, total


class OpenAlexProvider(Provider):
    name = "openalex"

    def search(self, query: Query) -> ProviderResult:
        result = ProviderResult(provider=self.name)

        phrase = query.phrase()
        result.queries.append(phrase)
        url = http.build_url(
            API,
            {
                "search": phrase,
                "per-page": query.limit,
                # OpenAlex meters callers by credit; an identified caller is
                # routed to the faster, more forgiving pool.
                "mailto": http.contact(),
            },
        )

        try:
            response = http.get(
                url,
                accept="application/json",
                cache_ttl=cache.TTL_SEARCH,
                use_cache=query.use_cache,
            )
        except http.HTTPError as exc:
            result.notes.append(f"OpenAlex request failed for '{phrase}': {exc}")
            result.failed = True
            return result

        if response.stale:
            result.notes.append(
                f"Served a cached (stale) OpenAlex response for '{phrase}' — network unavailable."
            )

        try:
            documents, total = parse_works(response.json())
        except ValueError as exc:
            result.notes.append(f"OpenAlex returned unparseable JSON for '{phrase}': {exc}")
            result.failed = True
            return result

        result.total_available = total
        if total == 0:
            result.notes.append(
                f"OpenAlex reported count=0 for '{phrase}'. The query is valid but matched "
                "nothing — either the terms are too specific or this really is unexplored "
                "ground. Not padded."
            )

        result.documents.extend(documents)
        self.apply_recency_filter(result, query.since_years)

        return result
