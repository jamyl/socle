"""Hugging Face daily papers provider.

Signal enrichment, not a search engine. The endpoint takes no query: verified
live on 2026-08-16, `?search=`, `?q=` and `?query=` are all ignored — the same
three papers came back for `search=diffusion` and for a nonsense term as for no
parameter at all. So this provider fetches the recent daily-papers feed and
matches the terms client-side. Anything older than that window is invisible
here, and a zero result means "not in the recent feed", never "not published".

What it buys us is the signal no paper API carries: how much attention a
preprint is getting right now (upvotes) and whether the authors shipped code
alongside it (`paper.githubRepo`). `paper.id` is the arXiv id, so these records
merge into the arXiv ones during dedup rather than double-counting.

API: https://huggingface.co/api/daily_papers?limit=N (returns a JSON array)
"""

from __future__ import annotations

from .. import cache, http
from ..document import Document, normalize_arxiv_id
from .base import Provider, ProviderResult, Query

API = "https://huggingface.co/api/daily_papers"

# How much of the feed to pull before matching locally. Confirmed to return 100
# entries; asking for more of a feed we filter ourselves only costs bandwidth.
FEED_LIMIT = 100


def parse_daily_papers(payload: list):
    """Parse the daily-papers array into Documents.

    The interesting fields live under `paper`; the envelope carries the
    submission metadata (`publishedAt`, `numComments`, `submittedBy`).
    """
    documents = []
    for entry in payload or []:
        paper = entry.get("paper") or {}
        arxiv_id = normalize_arxiv_id(paper.get("id"))
        if not arxiv_id:
            continue

        published = paper.get("publishedAt") or entry.get("publishedAt") or ""
        # Present on roughly half the feed, absent on the rest — absence means
        # "no code was linked", not "no code exists", hence None over False.
        github_repo = paper.get("githubRepo")

        documents.append(
            Document(
                id=f"hfpapers:{arxiv_id}",
                title=paper.get("title") or entry.get("title") or "",
                abstract=paper.get("summary") or entry.get("summary") or "",
                venue="Hugging Face daily papers",
                date=published[:10] or None,
                # Upvotes are a community attention signal, read into the same
                # slot citations occupy elsewhere: both count people who found
                # the work worth marking. They are days old, not years.
                citations=paper.get("upvotes"),
                urls={"landing": f"https://huggingface.co/papers/{arxiv_id}"},
                source="hfpapers",
                has_code=True if github_repo else None,
                authors=[a.get("name") for a in (paper.get("authors") or []) if a.get("name")],
                arxiv_id=arxiv_id,
                categories=list(paper.get("ai_keywords") or []),
                extra={
                    "github_repo": github_repo,
                    "github_stars": paper.get("githubStars"),
                    "upvotes": paper.get("upvotes"),
                    "comments": entry.get("numComments"),
                    "submitted_by": (entry.get("submittedBy") or {}).get("name"),
                },
            )
        )

    return documents


def matches_terms(doc: Document, terms: list) -> bool:
    """Client-side stand-in for the query the endpoint won't accept.

    A term matches if it appears in the title, the abstract or the keywords;
    with no terms every paper matches, which is the honest reading of "show me
    what's recent".
    """
    haystack = " ".join([doc.title, doc.abstract, " ".join(doc.categories)]).lower()
    wanted = [t.strip().lower() for t in terms if t.strip()]
    return not wanted or any(t in haystack for t in wanted)


class HuggingFacePapersProvider(Provider):
    name = "hfpapers"

    def search(self, query: Query) -> ProviderResult:
        result = ProviderResult(provider=self.name)

        phrase = query.phrase()
        result.queries.append(phrase)
        result.notes.append(
            "Hugging Face daily papers takes no query parameter (verified live: search/q/query "
            "are ignored). Fetched the recent feed and matched the terms locally, so this "
            "provider can only surface papers trending in the last few days — absence here "
            "says nothing about the literature."
        )
        url = http.build_url(API, {"limit": FEED_LIMIT})

        try:
            response = http.get(
                url,
                accept="application/json",
                cache_ttl=cache.TTL_SEARCH,
                use_cache=query.use_cache,
            )
        except http.HTTPError as exc:
            result.notes.append(f"Hugging Face daily papers request failed: {exc}")
            result.failed = True
            return result

        if response.stale:
            result.notes.append(
                "Served a cached (stale) Hugging Face daily-papers feed — network unavailable."
            )

        try:
            documents = parse_daily_papers(response.json())
        except ValueError as exc:
            result.notes.append(f"Hugging Face daily papers returned unparseable JSON: {exc}")
            result.failed = True
            return result

        # Deliberately left None. Everywhere else `total_available` answers
        # "how many documents does this source hold that match the query" —
        # arXiv's totalResults, OpenAlex's meta.count, GitHub's total_count.
        # This endpoint cannot answer that at all: it returns a fixed recent
        # feed and ignores every query parameter. Reporting the feed size here
        # would read as "100 matched, 0 returned", which is false. The pool
        # size belongs in a note, where it is labelled as a pool size.
        # The pool size is already stated in the notes above and below, where
        # it is labelled as a feed rather than a corpus.
        result.total_available = None

        for doc in documents:
            if not matches_terms(doc, query.terms):
                continue
            result.documents.append(doc)
            if len(result.documents) >= query.limit:
                break

        if not result.documents:
            result.notes.append(
                f"No paper in the last {len(documents)} daily papers matched '{phrase}'. "
                "That is a recency signal only — check the paper providers for the literature."
            )

        self.apply_recency_filter(result, query.since_years)
        return result
