"""arXiv export API provider.

Reference implementation of the Document contract, and the one source that
carries a full abstract, a subject taxonomy, and — confirmed in real feeds —
`arxiv:doi` and `arxiv:journal_ref`, which give us the DOI needed for the
retraction check and a venue string without a second provider call.

API docs: https://info.arxiv.org/help/api
"""

from __future__ import annotations

from .. import cache, http, safe_xml, taxonomy
from ..document import Document, normalize_arxiv_id, normalize_doi
from .base import Provider, ProviderResult, Query

API = "https://export.arxiv.org/api/query"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def term_clause(term: str) -> str:
    """Quote multi-word terms so arXiv treats them as a phrase, not as OR'd words."""
    cleaned = term.strip().replace('"', "")
    return f'all:"{cleaned}"' if " " in cleaned else f"all:{cleaned}"


def build_search_query(category: str | None, terms: list) -> str:
    clauses = [term_clause(t) for t in terms if t.strip()]
    if category and clauses:
        return f"cat:{category} AND ({' OR '.join(clauses)})"
    if category:
        return f"cat:{category}"
    return " OR ".join(clauses)


def _text(node, path: str) -> str:
    found = node.find(path, NS)
    if found is None or found.text is None:
        return ""
    return " ".join(found.text.split())


def parse_feed(xml_text: str, searched_category: str | None = None):
    """Parse an Atom feed into (documents, total_results).

    `total_results` is the field the old implementation never read; without it
    an invalid category is indistinguishable from an empty field of research.
    """
    root = safe_xml.fromstring(xml_text)

    total_node = root.find("opensearch:totalResults", NS)
    total = None
    if total_node is not None and (total_node.text or "").strip().isdigit():
        total = int(total_node.text.strip())

    documents = []
    for entry in root.findall("atom:entry", NS):
        id_url = _text(entry, "atom:id")
        versioned = id_url.rsplit("/", 1)[-1] if id_url else ""
        bare = normalize_arxiv_id(versioned) or versioned
        if not bare:
            continue

        urls = {}
        for link in entry.findall("atom:link", NS):
            href = link.get("href", "")
            if link.get("title") == "pdf":
                urls["pdf"] = href
            elif link.get("rel") == "alternate":
                urls["abs"] = href
        urls.setdefault("abs", f"https://arxiv.org/abs/{bare}")
        urls.setdefault("pdf", f"https://arxiv.org/pdf/{bare}")
        # arXiv renders native HTML for recent submissions; the full-text tier
        # tries this first and falls back to ar5iv.
        urls.setdefault("html", f"https://arxiv.org/html/{versioned or bare}")

        # Every declared category, not just the one we searched under. The old
        # parser dropped these even though types.ts promised them.
        declared = [c.get("term") for c in entry.findall("atom:category", NS) if c.get("term")]
        if searched_category and searched_category not in declared:
            declared.append(searched_category)

        published = _text(entry, "atom:published")
        doi = normalize_doi(_text(entry, "arxiv:doi") or None)
        journal_ref = _text(entry, "arxiv:journal_ref") or None

        documents.append(
            Document(
                id=f"arxiv:{bare}",
                title=_text(entry, "atom:title"),
                abstract=_text(entry, "atom:summary"),
                venue=journal_ref or "arXiv preprint",
                date=published[:10] or None,
                citations=None,  # arXiv publishes no citation counts
                urls=urls,
                source="arxiv",
                has_code=None,
                authors=[
                    " ".join((a.text or "").split())
                    for a in entry.findall("atom:author/atom:name", NS)
                ],
                doi=doi,
                arxiv_id=bare,
                categories=declared,
                extra={
                    "version": versioned,
                    "updated": _text(entry, "atom:updated")[:10] or None,
                    "comment": _text(entry, "arxiv:comment") or None,
                    "primary_category": (
                        entry.find("arxiv:primary_category", NS).get("term")
                        if entry.find("arxiv:primary_category", NS) is not None
                        else None
                    ),
                    "peer_reviewed": bool(journal_ref),
                },
            )
        )

    return documents, total


class ArxivProvider(Provider):
    name = "arxiv"

    def search(self, query: Query) -> ProviderResult:
        result = ProviderResult(provider=self.name)

        categories = list(query.categories)
        invalid = [c for c in categories if not taxonomy.is_valid(c)]
        for bad in invalid:
            hint = ", ".join(taxonomy.suggest(bad)) or "no close match"
            result.notes.append(
                f"'{bad}' is not a real arXiv category id and was skipped "
                f"(closest real ids: {hint}). See references/categories.md."
            )
        categories = [c for c in categories if taxonomy.is_valid(c)]

        if not categories:
            if invalid:
                result.notes.append(
                    "No valid category survived validation; searched arXiv-wide instead."
                )
            categories = [None]  # a taxonomy-free, terms-only search

        seen_ids = set()
        zero_hit_categories = []

        for category in categories:
            search_query = build_search_query(category, query.terms)
            url = http.build_url(
                API,
                {
                    "search_query": search_query,
                    "start": 0,
                    "max_results": query.limit,
                    "sortBy": "relevance",
                    "sortOrder": "descending",
                },
            )
            result.queries.append(search_query)
            try:
                response = http.get(
                    url,
                    accept="application/atom+xml",
                    cache_ttl=cache.TTL_SEARCH,
                    use_cache=query.use_cache,
                )
            except http.HTTPError as exc:
                result.notes.append(f"arXiv request failed for {search_query}: {exc}")
                result.failed = True
                continue

            if response.stale:
                result.notes.append(
                    f"Served a cached (stale) arXiv response for '{search_query}' — network unavailable."
                )

            try:
                documents, total = parse_feed(response.body, category)
            except (safe_xml.ParseError, safe_xml.UnsafeXMLError) as exc:
                result.notes.append(f"arXiv returned unparseable XML for {search_query}: {exc}")
                result.failed = True
                continue

            if total is not None:
                result.total_available = (result.total_available or 0) + total
            if total == 0:
                zero_hit_categories.append(category or "arXiv-wide")

            for doc in documents:
                if doc.id in seen_ids:
                    continue
                seen_ids.add(doc.id)
                result.documents.append(doc)

        if zero_hit_categories:
            result.notes.append(
                "arXiv reported totalResults=0 for: "
                + ", ".join(zero_hit_categories)
                + ". The query is valid but matched nothing — either the terms are "
                "too specific or this really is unexplored ground. Not padded."
            )

        self.apply_recency_filter(result, query.since_years)
        return result
