# Scoring rubric

How a reading becomes three numbers, and what evidence each one is allowed to
use. The point is that rigor stops being a vibe: the providers return real
citation counts, venues and dates, so the score can rest on them.

## Contents

- [The three axes](#the-three-axes)
- [Weighting](#weighting)
- [Citation normalization](#citation-normalization)
- [Retractions and corrections](#retractions-and-corrections)
- [Traps and strengths](#traps-and-strengths)
- [What not to do](#what-not-to-do)

## The three axes

Each 0-10, scored on the *reading*, not on the raw abstract.

### relevance — how directly this addresses the stated build problem

Evidence: the reading's `relevanceNote` and `approach`. A brilliant paper about
a different problem scores low. This is the axis where being honest costs the
least and helps the most.

### practicality — could a small team implement or adapt this

Evidence: the reading's `borrow`, plus:

- `has_code: true` and a live repository is a strong positive — an existing
  implementation is the difference between "buildable" and "buildable in
  principle". An `archived` repository is weaker than a maintained one.
- Requirements for exotic infrastructure (quantum hardware, thousand-GPU
  training runs, unpublished datasets) drive this down regardless of quality.

### rigor — how much real evidence stands behind the claim

Evidence, in order of weight:

1. `citations`, normalized for age (below). A well-cited paper has been checked
   by other people.
2. `venue` and `extra.peer_reviewed`. A journal or conference paper has passed
   review; `"arXiv preprint"` has not. Preprints are not disqualified — much of
   the best systems work is preprint-only — but an unreviewed, uncited preprint
   should not outscore a reviewed, replicated result.
3. What the abstract itself claims: benchmarks, proofs, a shipped system versus
   a purely conceptual proposal.
4. Full-text evidence, when Phase 4 escalated the document.

`citations: null` means the provider has no count (arXiv publishes none), not
that the paper has zero. Do not score it as zero — fall back to the other
signals and say the count was unavailable.

## Weighting

```
total = 0.4 * relevance + 0.4 * practicality + 0.2 * rigor
```

Practicality and relevance dominate because the deliverable is a build
decision, not a survey. Rigor is the tiebreaker: a rigorous but impractical
cluster loses to a rougher, buildable one. A well-evidenced paper that doesn't
fit the problem is still the wrong pick.

## Citation normalization

Raw counts favour old work mechanically. Compare against age:

```
citations_per_year = citations / max(1, current_year - publication_year + 1)
```

Rough calibration for computer science, to be applied with judgement rather
than as a lookup table:

| citations/year | reading |
|---|---|
| 0-1 | little external validation yet |
| 2-10 | noticed |
| 10-50 | influential in its niche |
| 50+ | field-defining |

A 2026 paper with 3 citations and a 2010 paper with 40 are roughly equivalent
on this axis. Say the count and the year in the output so the reader can judge
for themselves.

## Retractions and corrections

Non-negotiable, because this is the failure the whole check exists to prevent:

- `retraction_status: retracted` — the document may be discussed, never used as
  a primary citation, and the retraction must be stated in the output.
- `has-correction` — usable, with the correction named.
- `unknown` — no provider could check. Say so; do not present it as clean.

Add `crossref` to `--sources` when the recommendation will lean hard on one or
two papers.

## Traps and strengths

Every scored document gets a **strength**: the one concrete thing its approach
gets right, required even for weak papers.

A **trap** is optional and reserved for a real, actionable warning implied by
the document's *own stated limitation* — "solid up to N nodes, breaks under
concurrent writers", not "more research is needed". A trap is a heads-up, not a
verdict.

Pitfalls travel across clusters: a limitation named by a paper in a rejected
cluster still belongs in the final avoid-list.

## What not to do

- Don't infer a citation count, a venue, or a date that the providers didn't
  return. If it isn't in the data, it isn't in the score.
- Don't let novelty stand in for rigor. New and unverified is not strong.
- Don't average the axes into a single opinion and lose the shape — a
  `[rel9 prac3 rig8]` paper and a `[rel6 prac8 rig6]` paper score similarly and
  mean completely different things.
