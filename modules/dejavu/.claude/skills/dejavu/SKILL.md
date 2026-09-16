---
name: dejavu
description: Grounds a coding agent's architecture decisions in real prior art before it builds something new. Searches arXiv, OpenAlex, Crossref and Europe PMC through bundled deterministic scripts, spawns one isolated read per paper, scores and clusters them, checks retractions and existing code, then converges on ONE recommended path with citations, a first step, and known prior-art pitfalls to avoid. Use on /dejavu, before designing non-trivial architecture, algorithms, ML/systems techniques, or protocols, or when the user asks "has anyone solved this", "what's the state of the art", or "am I about to rebuild something that already exists". Skip for trivial CRUD, glue code, or closed phrasing ("just", "quick", "standard").
license: MIT
argument-hint: "<the thing you are about to build>"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/search.py *), Bash(${CLAUDE_SKILL_DIR}/scripts/fulltext.py *), Bash(${CLAUDE_SKILL_DIR}/scripts/codesearch.py *), Read
---

# dejavu

Vibecoders don't waste hours because they lack skill. They waste hours because
they start building before checking whether the hard part has already been
solved and published, with the failure modes already known. This skill makes
the agent read the prior art first — and read it in isolation, so no source
anchors another.

$ARGUMENTS

## Pre-flight (run before Phase 0)

This skill is expensive: real HTTP against several APIs plus roughly one
isolated read per paper (typically 10-20). Don't pay that when there's no real
prior art to find.

**Step 1.** If the user typed `/dejavu`, or asked to "check prior art", "check
arXiv", or "run dejavu" — they opted in. Skip to Phase 0.

**Step 2** (only if Step 1 didn't match). Three questions; if any answer is no,
ABORT and implement directly.

1. **Is there a technical mechanism to research?** Naming a variable, wiring a
   CRUD form, or gluing two documented SDKs together has no prior-art question.
   A caching strategy, a consensus scheme, a ranking or retrieval approach, an
   ML training/inference technique, a protocol — anything where "the naive
   version breaks at scale" — does.
2. **Is the user about to commit real effort?** A one-off script doesn't earn a
   literature search. A component that anchors the architecture does.
3. **Did they leave the approach open?** If they named the specific
   algorithm/paper/library, or said "just do it the simple way", they've
   converged. Don't re-open it.

On ABORT, optionally add one sentence: *"If you want this checked against
prior art first, run `/dejavu <your problem>`."*

## The loop

Fetching is not divergence. Find real documents, read each in isolation, then
converge. Skipping isolation turns this into a model guessing about papers it
hasn't read.

### Phase 0 — Categorize

Map the build problem onto 3-5 arXiv categories and 3-6 concrete search terms —
the technical mechanism words ("cache invalidation", not "caching system").

Category ids are **validated against the real 155-category taxonomy** before any
query runs, so a wrong guess produces a named error with suggestions instead of
an empty result set. Browse ids in
[references/categories.md](references/categories.md) — read it only if the
obvious `cs.*` categories don't fit (physics, bio, econ, math problems).

### Phase 1 — Fetch (deterministic script, no WebFetch)

Run the bundled script. It handles proxies, rate limits, retries, caching and
cross-provider dedup, and it never summarizes — you get the APIs' own data.

```bash
${CLAUDE_SKILL_DIR}/scripts/search.py \
  --terms "term one" "term two" "term three" \
  --categories cs.DB cs.DC \
  --sources arxiv,openalex \
  --limit 6 --since-years 8
```

Add `--sources arxiv,openalex,crossref,europepmc` for biomedical, chemistry or
cross-disciplinary problems. Use `--brief` first if you only need a triage
listing. Full source/field details:
[references/providers.md](references/providers.md).

**Read the `diagnostics` block before anything else.** It tells you when a
category was invalid, when a provider returned `totalResults=0`, when a
provider failed, and when an answer came from stale cache. Report what it says
— never present a degraded run as a clean one.

If the run is thin, retry once with the terms dropped or with more sources. If
it's still thin, **say so**: zero relevant prior art is a real, useful finding.

*Fallback:* only if the script cannot run (no `python3`), use WebFetch against
`https://export.arxiv.org/api/query?search_query=cat:<CAT>+AND+all:"<term>"&max_results=4`
— and state in your output that the deterministic path was unavailable, because
WebFetch summarizes and truncates.

### Phase 2 — Diverge (one isolated read per document)

For every document, spawn a **parallel** sub-agent **with `model: haiku`**. One per document. Each gets
only: the build problem, that ONE document's title/abstract/authors/year/venue,
and this instruction:

> You are in DIVERGENT READ mode. You have exactly one paper's metadata and one
> build problem. You do not know what other papers exist — do not assume,
> invent, or gesture at a broader survey. Read this as if scouting prior art for
> someone about to build the stated thing from scratch. Never quote more than a
> few consecutive words — paraphrase.
> Extract: **approach** (1-2 sentences, the core mechanism), **borrow** (1
> sentence, the single most concrete implementable takeaway, imperative: "Use X
> to do Y"; if too tangential, say so plainly), **limitation** (1 sentence, the
> load-bearing weakness or breaking condition), **relevanceNote** (1 clause on
> fit).
> Output JSON only: `{"approach":"...","borrow":"...","limitation":"...","relevanceNote":"..."}`

**Critical invariant.** These reads must be parallel and isolated. A read that
has seen other abstracts starts summarizing the SET instead of grounding in the
ONE document in front of it — a subtle failure, because the output still looks
paper-specific.

### Phase 3 — Score and cluster

**Score** each reading 0-10 on relevance, practicality and rigor. Rigor is
evidence-based, not vibes: use the real `citations`, `venue`, `date` and
`extra.peer_reviewed` fields the providers returned, normalized for age — a
2024 paper with 30 citations is not weaker than a 2005 paper with 300. Full
rubric and weights: [references/scoring.md](references/scoring.md).

Flag a **trap** when a document's own stated limitation implies a failure mode a
builder would otherwise rediscover the hard way. Always pair it with a
**strength**.

**Any document whose `retraction_status` is `retracted` or `has-correction` must
be surfaced explicitly and must not be the primary citation.** This is checked
systematically now, not left to whether a withdrawal notice happened to appear
in the abstract.

**Cluster** the readings into 3-6 groups by underlying architectural angle (not
by paper, not by keyword): "cache-invalidation plays", "consensus-free plays",
"learned-index plays".

### Phase 4 — Escalate the winner to full text

Pick the leading cluster, then read the **top 3 documents of that cluster only**
in full text:

```bash
${CLAUDE_SKILL_DIR}/scripts/fulltext.py --id 2311.02384
```

It cascades arXiv HTML → ar5iv → Europe PMC open access and returns the
method/evaluation/limitation sections. If it reports `tier: unavailable`, that
paper stays abstract-only — say so rather than inventing detail. Bound it to
three: full text everywhere would multiply cost for no gain, since only the
recommended path needs that depth.

Optionally check whether the thing already exists as code:

```bash
${CLAUDE_SKILL_DIR}/scripts/codesearch.py --terms "cache invalidation" --limit 5
```

A maintained repository answers "am I about to rebuild something" better than a
paper does. Feed it into practicality.

### Phase 5 — Converge (one path, not a shortlist)

1. **Pick ONE cluster** — the strongest relevance + practicality combination.
   Not the most novel, not the most cited: the one an engineer should build.
   This is the point of departure from open-ended research. "Here are 4 papers,
   you decide" is exactly the time-wasting this skill exists to prevent.
2. **Synthesize**: a 4-8 sentence implementation sketch (actionable, not a
   lit-review), citations (id + title + url + role: "primary mechanism" /
   "supporting evidence" / "failure mode to avoid"), the first concrete step,
   the load-bearing risk, and an **avoid** list drawn from *every* document's
   limitation — a pitfall named by a paper in a rejected cluster still counts.
3. **Name the runner-ups**: one honest sentence per non-chosen cluster on the
   trade-off that lost it the pick.
4. **One open thread**: a question the documents raise but don't answer.

## Output shape

1. **Searched.** Sources, categories, terms, document count — plus any
   diagnostic that degraded the run.
2. **Papers read.** Grouped by cluster. Each: id, title, one-line approach,
   score chips `[rel8 prac6 rig7]`, and citation count where known.
3. **Prior-art pitfalls.** Traps and any retracted/corrected source.
4. **THE PATH.** The chosen cluster: sketch, citations, first step,
   load-bearing risk, avoid-list. Make this bold and unmissable.
5. **Alternates considered.** One line each.
6. **Open thread.**

## Anti-patterns

- **Cross-contaminated reads.** If a read mentions "compared to the other papers
  here" or "collectively these show", isolation broke — re-run it alone.
- **Hallucinated citations.** Never state a detail that wasn't in the fetched
  data. The scripts return real API output; if it isn't there, don't claim it.
- **Shortlist-as-cop-out.** Ending with "here are 3 good options" defeats the
  purpose. Commit.
- **Padding a thin result set.** Few relevant papers is a valid finding. Say so.
- **Silent degradation.** An invalid category, a failed provider, a stale cache
  hit, or an unavailable full text must appear in the output. The whole point of
  the diagnostics block is that a broken run should never look like a clean one.
- **Treating an abstract as the whole paper.** Keep "borrow" and "avoid" at the
  level the fetched text actually supports — unless Phase 4 escalated it.

## Cost

1 categorize + N isolated reads (typically 12-20) + 1 score + 1 cluster + up to
3 full-text reads + 1 converge ≈ N+6 agent-shaped calls, plus real HTTP. Cached
runs re-use previous fetches and work offline. Not for every design decision —
for the ones where getting the architecture wrong costs real rework.

## Setup notes

Set `DEJAVU_CONTACT` to your email. Every API here either asks for or rewards a
declared contact address (and the SEC filing tools require one). Cache lives in
`~/.cache/dejavu`; override with `DEJAVU_CACHE_DIR`, inspect with
`scripts/search.py --cache-stats`.

The same scripts back the `dejavu` command-line tool, so a run in either place
warms the cache for the other.
