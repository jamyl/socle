"""The normalized Document contract every provider returns.

This is the whole point of the provider layer: the core loop (isolated read →
score → cluster → converge) never learns whether a document came from arXiv,
OpenAlex, Europe PMC or an SEC filing. Adding a source means writing one
provider that fills this shape — nothing downstream changes.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field

# retraction_status values. "unknown" is honest and load-bearing: it means no
# provider in this run could answer the question, which is different from
# "clear" (a provider looked and found nothing wrong).
CLEAR = "clear"
RETRACTED = "retracted"
HAS_CORRECTION = "has-correction"
UNKNOWN = "unknown"

_RETRACTION_RANK = {UNKNOWN: 0, CLEAR: 1, HAS_CORRECTION: 2, RETRACTED: 3}


@dataclass
class Document:
    id: str
    title: str
    abstract: str = ""
    venue: str | None = None
    date: str | None = None  # ISO 8601 date, YYYY-MM-DD
    citations: int | None = None
    urls: dict = field(default_factory=dict)  # abs / pdf / html / landing
    source: str = ""
    retraction_status: str = UNKNOWN
    has_code: bool | None = None

    # Identity and reading support. Not part of the minimum contract, but the
    # isolated read needs authors, and dedup across providers needs the ids.
    authors: list = field(default_factory=list)
    doi: str | None = None
    arxiv_id: str | None = None
    categories: list = field(default_factory=list)
    sources: list = field(default_factory=list)  # every provider that surfaced it
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.sources and self.source:
            self.sources = [self.source]

    @property
    def year(self) -> int | None:
        if not self.date or len(self.date) < 4 or not self.date[:4].isdigit():
            return None
        return int(self.date[:4])

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_doi(doi: str | None) -> str | None:
    """Strip the many DOI spellings down to the bare `10.x/y` form.

    Providers hand back DOIs in at least three shapes — `10.1/x`,
    `https://doi.org/10.1/x`, `doi:10.1/x` — and dedup silently fails if they
    aren't reduced to one.
    """
    if not doi:
        return None
    value = doi.strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:", "", value)
    return value or None


def normalize_arxiv_id(value: str | None) -> str | None:
    """Reduce an arXiv reference to its bare, version-less id."""
    if not value:
        return None
    text = value.strip().lower()
    text = re.sub(r"^https?://arxiv\.org/(abs|pdf|html)/", "", text)
    text = re.sub(r"^arxiv:", "", text)
    text = re.sub(r"\.pdf$", "", text)
    text = re.sub(r"v\d+$", "", text)
    # OpenAlex records arXiv preprints under a DOI of the form 10.48550/arxiv.ID
    text = re.sub(r"^10\.48550/arxiv\.", "", text)
    return text or None


def normalize_title(title: str) -> str:
    """A comparison key for titles: accents, case, punctuation and spacing removed."""
    folded = unicodedata.normalize("NFKD", title or "")
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    folded = folded.lower()
    folded = re.sub(r"[^a-z0-9]+", " ", folded)
    return folded.strip()


def identity_keys(doc: Document) -> list:
    """Every key under which this document might match another provider's copy."""
    keys = []
    doi = normalize_doi(doc.doi)
    if doi:
        keys.append(f"doi:{doi}")
    arx = normalize_arxiv_id(doc.arxiv_id)
    if arx:
        keys.append(f"arxiv:{arx}")
    title = normalize_title(doc.title)
    if len(title) > 20:  # short titles collide across unrelated works
        keys.append(f"title:{title}")
    return keys


def merge(primary: Document, other: Document) -> Document:
    """Fold two records of the same work into one, keeping the better field each time.

    "Better" is defined per field rather than per record because no provider
    wins on everything: arXiv has the full abstract, OpenAlex has the citation
    count and the retraction flag, Crossref has the venue.
    """
    merged = Document(**primary.to_dict())

    if len(other.abstract or "") > len(merged.abstract or ""):
        merged.abstract = other.abstract
    if not merged.venue and other.venue:
        merged.venue = other.venue
    if not merged.date and other.date:
        merged.date = other.date
    if other.citations is not None:
        merged.citations = max(merged.citations or 0, other.citations)
    if not merged.doi and other.doi:
        merged.doi = other.doi
    if not merged.arxiv_id and other.arxiv_id:
        merged.arxiv_id = other.arxiv_id
    if other.has_code:
        merged.has_code = True
    if len(other.authors) > len(merged.authors):
        merged.authors = list(other.authors)

    # A retraction seen by any provider outranks a clean bill from another.
    if _RETRACTION_RANK[other.retraction_status] > _RETRACTION_RANK[merged.retraction_status]:
        merged.retraction_status = other.retraction_status

    merged.urls = {**other.urls, **merged.urls}
    merged.categories = sorted(set(merged.categories) | set(other.categories))
    merged.sources = sorted(set(merged.sources) | set(other.sources))
    merged.extra = {**other.extra, **merged.extra}
    return merged


def dedup(documents: list) -> list:
    """Collapse duplicates across providers, preserving first-seen order.

    Transitive matches matter here: OpenAlex may share a DOI with Crossref and
    a title with arXiv, making all three the same work even though arXiv and
    Crossref share no key directly.
    """
    by_key: dict = {}
    ordered: list = []

    for doc in documents:
        keys = identity_keys(doc)
        hit_index = None
        for key in keys:
            if key in by_key:
                hit_index = by_key[key]
                break

        if hit_index is None:
            ordered.append(doc)
            index = len(ordered) - 1
        else:
            ordered[hit_index] = merge(ordered[hit_index], doc)
            index = hit_index

        for key in identity_keys(ordered[index]):
            by_key.setdefault(key, index)

    return ordered
