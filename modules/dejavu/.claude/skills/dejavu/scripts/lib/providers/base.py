"""The provider contract: search(query, filters) -> normalized Document[].

Every provider reports diagnostics alongside its documents. That is not
bookkeeping — the original skill's worst failure mode was an invalid arXiv
category returning HTTP 200 with zero results and no signal, which is
indistinguishable from "no prior art exists" unless the provider says so out
loud. `notes` is where a provider says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..document import Document


@dataclass
class Query:
    """What to look for. Providers ignore the filters that don't apply to them."""

    terms: list = field(default_factory=list)
    categories: list = field(default_factory=list)  # arXiv-style ids
    limit: int = 10
    since_years: int = 0  # 0 means no recency filter
    use_cache: bool = True

    def phrase(self) -> str:
        """The terms as one free-text query, for providers without a field syntax."""
        return " ".join(t.strip() for t in self.terms if t.strip())


@dataclass
class ProviderResult:
    provider: str
    documents: list = field(default_factory=list)
    total_available: int | None = None
    notes: list = field(default_factory=list)
    queries: list = field(default_factory=list)
    failed: bool = False

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "documents": [d.to_dict() for d in self.documents],
            "total_available": self.total_available,
            "notes": self.notes,
            "queries": self.queries,
            "failed": self.failed,
        }


class Provider:
    """Base class. Subclasses implement `search` and return a ProviderResult."""

    name = "base"

    def search(self, query: Query) -> ProviderResult:  # pragma: no cover - interface
        raise NotImplementedError

    # Shared helpers -------------------------------------------------------

    @staticmethod
    def within_years(doc: Document, since_years: int) -> bool:
        """Keep documents newer than the cutoff; keep undated ones rather than guess."""
        if since_years <= 0:
            return True
        year = doc.year
        if year is None:
            return True
        import datetime

        return year >= datetime.date.today().year - since_years

    @staticmethod
    def apply_recency_filter(result: ProviderResult, since_years: int) -> None:
        """Drop documents older than the cutoff, and SAY how many were dropped.

        A silent filter is the same bug as a silent empty search: a provider
        that found 6,000 papers and returned none because they all predate the
        cutoff looks identical to a provider that found nothing at all. The
        first means "widen your window", the second means "this is unexplored".
        """
        if since_years <= 0:
            return
        kept = [d for d in result.documents if Provider.within_years(d, since_years)]
        dropped = len(result.documents) - len(kept)
        if dropped:
            oldest_kept = min((d.year for d in kept if d.year), default=None)
            result.notes.append(
                f"{dropped} of {len(result.documents)} {result.provider} results were older "
                f"than the {since_years}-year window and were dropped"
                + (f" (oldest kept: {oldest_kept})" if oldest_kept else "")
                + ". Raise --since-years to include them; foundational work is often older."
            )
        result.documents = kept


def registry() -> dict:
    """Providers available to `search.py`, keyed by the name used on the CLI."""
    from . import arxiv, crossref, europepmc, openalex

    return {
        arxiv.ArxivProvider.name: arxiv.ArxivProvider,
        openalex.OpenAlexProvider.name: openalex.OpenAlexProvider,
        crossref.CrossrefProvider.name: crossref.CrossrefProvider,
        europepmc.EuropePMCProvider.name: europepmc.EuropePMCProvider,
    }
