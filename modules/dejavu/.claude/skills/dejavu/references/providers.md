# Providers reference

Which source to ask, what each one actually returns, and the field mappings the
scripts perform. Every shape here was confirmed against a live response — no
field is documented that wasn't observed.

## Contents

- [Choosing sources](#choosing-sources)
- [The normalized Document](#the-normalized-document)
- [arxiv](#arxiv)
- [openalex](#openalex)
- [crossref](#crossref)
- [europepmc](#europepmc)
- [Code prior art: github, hfpapers](#code-prior-art-github-hfpapers)
- [Not used, and why](#not-used-and-why)
- [Rate limits and etiquette](#rate-limits-and-etiquette)
- [Diagnostics](#diagnostics)

## Choosing sources

| Problem shape | `--sources` |
|---|---|
| CS / systems / ML, the common case | `arxiv,openalex` (default) |
| Physics, math, quantitative biology | `arxiv,openalex` with the right category |
| Biomedical, chemistry, clinical | `arxiv,openalex,europepmc` |
| Anything where venue or retraction matters | add `crossref` |
| "Does an implementation already exist?" | `codesearch.py` (github, hfpapers) |

Two providers is usually the right number. Each extra source costs a round trip
and adds documents that must each earn an isolated read.

## The normalized Document

Every provider returns this shape. The core loop never learns which source a
document came from.

| Field | Meaning |
|---|---|
| `id` | `<provider>:<native id>`, stable across runs |
| `title`, `abstract` | Text the isolated read works from |
| `venue` | Journal, conference or `"arXiv preprint"` |
| `date` | ISO `YYYY-MM-DD` |
| `citations` | Real count where the provider has one, else `null` |
| `urls` | `abs` / `pdf` / `html` / `landing` / `oa`, only when present |
| `source`, `sources` | Provider that returned it; every provider that matched it |
| `retraction_status` | `clear` / `retracted` / `has-correction` / `unknown` |
| `has_code` | `true` when a repository is known |
| `authors`, `doi`, `arxiv_id`, `categories` | Identity and reading support |
| `extra` | Provider-specific signals, incl. `peer_reviewed` |

`unknown` is not a synonym for `clear`. It means no provider in this run could
answer the question — a failed lookup must never be reported as a clean bill of
health.

### Deduplication

Documents are merged across providers on DOI, then arXiv id, then normalized
title, transitively. Merging is per field, because no provider wins on
everything: arXiv has the full abstract, OpenAlex the citation count and
retraction flag, Crossref the venue. A retraction seen by any provider survives
the merge.

## arxiv

`https://export.arxiv.org/api/query` — Atom XML, no key.

The only source with a subject taxonomy, and the best abstracts. Confirmed to
carry `arxiv:doi` and `arxiv:journal_ref`, so a preprint that was later
published gives up its DOI and venue without a second lookup.

- Query form: `cat:cs.DB AND (all:"cache invalidation" OR all:consistency)`
- Category ids validated against the full 155-category taxonomy before the
  request is sent. See [categories.md](categories.md).
- `opensearch:totalResults` is read and reported. A valid-but-empty search is
  reported as such — this is the fix for the failure where an invalid category
  returned HTTP 200 with zero results and looked like "no prior art exists".
- No citation counts: arXiv doesn't publish them. Pair with OpenAlex.

## openalex

`https://api.openalex.org/works` — JSON, no key, `mailto` for the polite pool.

The discovery workhorse: citations, venue, open-access status and the
retraction flag in a single call, across journals and repositories rather than
preprints alone.

- `abstract_inverted_index` is reconstructed into plain text by the provider —
  OpenAlex does not return a plain abstract.
- `is_retracted` maps to `retracted` / `clear`. This is a real check, so `clear`
  is honest here.
- arXiv preprints carry a `10.48550/arxiv.<ID>` DOI, which is converted back to
  a bare arXiv id so the two providers' copies merge instead of double-counting.

## crossref

`https://api.crossref.org/works` — JSON, no key, `mailto` for the polite pool.

Used for venue, citation counts and — most importantly — the retraction check.

- `filter=updates:<DOI>` returns the notices that update a DOI, each carrying
  `update-to[].type` (`retraction`, `erratum`, …). This is how a withdrawn
  paper is caught systematically instead of by luck.
- Abstracts are often missing and JATS-wrapped when present. Crossref is a
  metadata source here, not a reading source.

## europepmc

`https://www.ebi.ac.uk/europepmc/webservices/rest/search` — JSON, no key.

Biomedical and life-science coverage, plus open-access full text.

- `resultType=core` is required to get `abstractText`; the default omits it.
- `source` is a corpus code: `MED` (peer-reviewed), `PPR` (preprint). This is
  also the practical route to bioRxiv/medRxiv content.
- No retraction flag in the search response, so `retraction_status` stays
  `unknown` unless Crossref fills it in.

## Code prior art: github, hfpapers

Run through `codesearch.py`, not `search.py`.

- **github** — repository search, unauthenticated. Stars stand in for
  `citations`; `pushed_at` and `archived` say whether it's alive. Capped at 2
  requests per run because the unauthenticated search limit is 10/minute. Set
  `GITHUB_TOKEN` to raise the ceiling.
- **hfpapers** — the Hugging Face daily papers index. `paper.id` is an arXiv id,
  so entries merge with arXiv results; `upvotes` is a community-attention
  signal, not a citation count.

## Not used, and why

- **Semantic Scholar** — returns HTTP 429 immediately without an API key
  (verified twice). Would be a good source with a key; excluded deliberately
  because this skill requires none.
- **bioRxiv API** — `api.biorxiv.org/details/...` lists by date interval or DOI
  only, with no keyword search. Preprints are reached through Europe PMC
  (`source=PPR`) or OpenAlex instead.
- **SEDAR+** — no public API; the site is a bot-protected JavaScript
  application. Canadian filings are out of scope rather than scraped.

## Rate limits and etiquette

`lib/http.py` enforces per-host spacing that survives across process
invocations, so several script calls in a row can't breach a limit:

| Host | Spacing | Source of the number |
|---|---|---|
| `export.arxiv.org`, `arxiv.org`, ar5iv | 3.0 s | arXiv terms of use: one request per three seconds, single connection |
| `api.crossref.org` | 0.34 s | Observed `x-rate-limit-limit: 3` per `1s` |
| `*.sec.gov` | 0.11 s | SEC: "max request rate: 10 requests/second" |
| `api.github.com` | 6.0 s | Observed unauthenticated search limit of 10/min |
| `api.openalex.org` | 0.2 s | No published per-second limit; politeness |
| others | 0.5 s | Conservative default |

Set `DEJAVU_CONTACT` to a real email. Every API here either asks for or rewards
it, and the SEC filing tools refuse to run without it.

## Diagnostics

Every run returns a `diagnostics` block. Read it before the documents:

- `notes` — invalid category ids (with suggestions), zero-result searches,
  provider failures, stale cache hits
- `providers[].total_available` — how much the source actually had
- `providers[].failed` / `all_providers_failed`
- exit code `2` means every requested provider failed

A degraded run must be reported as degraded. That is the entire reason this
block exists.
