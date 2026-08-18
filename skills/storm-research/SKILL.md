---
name: storm-research
description: AI-assisted multi-perspective deep research (STORM workflow) — pin the question, run parallel perspective research, cross-validate, map contradictions, synthesize verdict-first with evidence labels, and peer-review the output. Use for deep multi-source research, market/business feasibility analysis, website teardowns, company due diligence, or research-grade article/paper briefings.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, storm, multi-perspective, contradiction-map, synthesis, peer-review, evidence-labeling]
    category: research
---

# STORM Research (Multi-Perspective Deep Research)

## What STORM is

STORM is an AI-assisted **research workflow**, not a prompt trick or a summary template. Its value is research structure: question quality, perspective diversity, blind-spot discovery, reliability labeling — not answer speed.

Core loop: **pin the question → parallel perspective research → cross-validation → contradiction map → verdict-first synthesis → peer review.**

## When to use

- Deep multi-source research on a topic, market, company, or website
- Business / startup feasibility analysis (360°)
- Website teardown or company due diligence
- Research-grade article / paper / report briefing
- Any question where a single-shot answer is not enough

Do **not** use for: one-sentence answers, literal translation, or pure fact extraction with no synthesis.

## Workflow

### 1. Pin the question / premise first (the most important step)

- Define exactly what is being asked, sold, or evaluated. Write it as one line at the top of the report.
- For business analysis: confirm what is sold (product vs service vs raw material vs processed output). A premise error invalidates every downstream section and costs a full re-analysis — one clarifying question up front beats a re-run.
- Before reading results, write a short prediction: what do we expect the evidence to show, and what would change our mind.

### 2. Parallel perspective research

Prefer 3 parallel leaf subagents, each with a distinct lens. Common split:

- ① **Market & competition** — size, players, unit economics, who actually pays
- ② **Technical / product reality** — per-stage feasibility, MVP boundary, costs
- ③ **Organization & execution** — team gaps, partnerships, success/death cases, validation design

Each brief must be **self-contained**: the exact question, known constraints/background, and output requirements. Require in the brief:

- Verdict-first structure, no hedging
- Every claim labeled 【Fact】/【Media-reported】/【Inference】(or local equivalents)
- Sources with publication dates
- "Not found" stated honestly instead of invented data

Fallback when no subagent orchestration is available: batched web searches (2–3 rounds, 4–6 queries each), retrying failed queries with different phrasing.

### 3. Cross-validation

- **Subagent summaries are self-reports.** Verify every key number yourself before it enters the report (2–3 search batches, official sources preferred).
- Short or ambiguous domain terms get search-polluted — rephrase with 2+ domain terms, quote the domain (e.g. `"example.com" pricing`).
- Conflicting figures are usually **measurement-frame differences, not errors**. Report both side by side with the conflict flagged, and list the frames explicitly (e.g. five different definitions of "usable rate").

### 4. Contradiction map

Answer six questions:

1. Which claims are in tension?
2. Which perspective supports each claim?
3. Which perspective would object?
4. What evidence would resolve the disagreement?
5. What does everyone agree on?
6. What did nobody discuss?

**Do not smooth over contradictions.** If two views cannot both be true, say so. Force at least one skeptical perspective into every research pass.

### 5. Verdict-first synthesis

Report skeleton (adapt to the question):

1. **Executive judgments** — numbered, verdict-first, each with key numbers and source markers
2. **Methodology** — framework, evidence-labeling scheme, credibility tiers, **limitations declared up front** (unverified figures, missing data)
3. **Definitions & frames** — glossary of terms and measurement frames to prevent concept collisions
4. **Domain sections** — market / competition / technical / organizational, as applicable; tables carry a credibility column
5. **Contradiction map** — direct collisions, strongest/weakest evidence, consensus, blind spot
6. **Conclusions ranked by reliability**
7. **Validation checklist** — numbered, with red-line items (what must be true for this to work)
8. **Peer review** — weakest link, blind spots, confidence, what a strict reviewer would ask
9. **Sources** — numbered, hyperlinked; every key claim points back

Writing rules: conclusion first, no hedging, name the evidence behind each claim, name missing evidence when a claim is weak, give usable judgments ("X is not feasible for a solo builder in 6 months"), avoid generic filler ("this highlights the importance of…").

### 6. Evidence labeling (throughout)

- 【Fact】— cross-verifiable
- 【Media-reported】— single source / third-party claim
- 【Inference】— analysis or reasoning
- Single-source numbers (paywalled columns, vendor claims) → low credibility, kept in a separate list
- Vendor self-reported metrics are marketing denominators — label as unverified
- Date every price/figure; snapshots expire

### 7. Peer review pass (before delivery)

Check: coverage (did we answer the question / preserve the argument?) · perspective diversity (≥1 skeptical view) · evidence discipline (strong vs weak separated) · contradictions named · blind spots identified · actionability · confidence labeled. If a major issue surfaces, revise before responding.

## Summary mode (article / paper / report briefing)

A lighter pass of the same workflow when the input is a single source and the output is a briefing, not a full research report.

Compact structure:

```markdown
## Core judgment        — 1–2 paragraphs, the single most important takeaway (no preamble)
## Author's claims      — 3–5 bullet claims
## Multi-perspective scan — practitioner / academic / skeptic / economist / historian (adapt to domain)
## Contradiction map    — main conflicts / strongest evidence / weakest evidence / consensus / blind spot
## Findings             — 3–5 ranked by reliability
## Reader's next step
## Self-review          — weakest link / missing perspective / confidence
```

Source handling: retrieve the full source when possible; preserve URL, title, author, date; separate what the author explicitly says from your synthesis; never invent missing evidence; state the limitation if the source is partial, paywalled, or truncated.

Default five perspectives (adapt to the domain, always keep ≥1 skeptical):

1. **Practitioner** — works with the topic daily; implementation, constraints, operational reality
2. **Academic** — evidence and theory; methods, validity, generalizability
3. **Skeptic** — challenges the mainstream view; overclaiming, selection bias, ignored counterexamples
4. **Economist** — incentives, costs, distribution of benefits, strategic behavior
5. **Historian** — analogies, cycles, precedents, what is genuinely new

Domain adaptations: technical → engineer/security reviewer/maintainer/user/competitor · business → operator/investor/customer/regulator/competitor · AI → model builder/product engineer/safety researcher/enterprise buyer/end user · paper → methodologist/domain expert/reviewer #2/practitioner/replication researcher.

Synthesis rules: start with a judgment, not a preamble; separate author claims from your analysis; rank by reliability, not rhetorical appeal; name the evidence behind each key claim; name missing evidence when a claim is weak; give implications without pretending uncertainty is gone. Avoid: "this article highlights the importance of…", title-restating summaries, over-balanced conclusions that refuse to choose, invented citations, speculation presented as evidence.

## Research-craft upgrades

Apply to serious briefings (from the "how to be good at research" playbook):

1. **Problem choice before answer generation** — ask what outcome we actually want and what would make us reframe the problem.
2. **Prediction before synthesis** — forecast expected results, then correct.
3. **Upgrade inputs** — prefer primary sources, appendices, limitations sections, raw transcripts and logs over summaries and trending pages.
4. **Write to expose gaps** — force assumptions and missing steps onto the page; writing is the cheapest defense against self-deception.
5. **Tighten the loop** — shrink ideas to the cheapest runnable version and compare against strong baselines.
6. **Stare at outputs** — read examples, failures, logs, and strange tails directly; aggregate scores are reassurance, not understanding.
7. **Purposeful wandering** — scan adjacent fields when the topic may be stuck inside a local consensus.
8. **Seek adversarial collaborators** — a critic who kills weak ideas early is worth more than another source.

## Variants

- **Business feasibility** — add unit-economics modeling: bottom-up cost build from public anchors (derived numbers labeled 【Inference】), a unified measurement frame across all compared schemes, an inverted-economics check (cost > selling price = death sentence; put it first), a sensitivity table (identify the few big controllable variables), and the repeat-purchase vs reuse-sale distinction (data usually has negative compounding: client exclusivity, bundling, free open-source alternatives).
- **Website teardown** — do quick first-party recon before delegating (HTTP headers, robots.txt, sitemap size, ads.txt — a monetization goldmine, JS fingerprints, WHOIS profile), then 3 perspectives (traffic/market, product/tech reverse-engineering, operations/compliance/risk). Verify any "smoking gun" claim yourself (curl the page).
- **Company / entity due diligence** — registry data (capital-structure anomalies, shareholders), domain WHOIS vs operating entity (shell clues), brand-vs-entity founding dates, license verification against official registries (PDF rosters, per-company official pages), and a marketing-claims-vs-official-docs comparison table.
- **Article / paper summary** — use the Summary mode above.

## Subagent brief template

```
Research the following question and return a structured report.

Question: [exact question]
Context: [known constraints, background, prior findings]
Perspectives to cover: [e.g. market size & competition / technical reality / organization]

Requirements:
1. Verdict-first structure: conclusions at the top, each with key numbers.
2. Label every claim: 【Fact】(cross-verifiable) / 【Media-reported】(single source) / 【Inference】(reasoning).
3. Include sources with publication dates for every figure.
4. If something cannot be found, say "not found" explicitly. Never invent data.
5. Flag conflicting figures and state the likely measurement-frame difference.
6. Write in [language: e.g. Chinese] unless instructed otherwise.
```

## One-shot prompt template (no orchestration available)

```text
Run a STORM-style research pass on: [QUESTION]

1. State the question/premise as you understand it (one line) before researching.
2. Research across at least 3 distinct perspectives (market, technical, organizational — adapt to domain; keep one skeptical view).
3. Build a contradiction map: direct conflicts, strongest/weakest evidence, consensus, blind spot.
4. Synthesize 3–5 key findings ranked by reliability, verdict-first.
5. Label every claim 【Fact】/【Media-reported】/【Inference】.
6. End with a peer-review pass: weakest link, missing perspective, confidence, what a strict reviewer would challenge.
7. Do not invent facts; state limitations up front.
8. Write in [language].
```

## Pitfalls

- **Premise error costs a full re-analysis** — pin the definition before deep research.
- **Narrative supply gap ≠ paying demand** — a "20× market gap" story and a real buyer list of a few dozen companies are different facts; report both separately.
- **Subagent claims are self-reports** — verify smoking-gun facts yourself (curl the page, check the official registry).
- **Acquisition / shutdown / partnership rumors spread** — a widely repeated "X acquired Y" can be false; verify against official news and primary press dated after the claimed event.
- **Contradictory numbers are usually frames, not errors** — list the definitions, don't average them.
- **Single-source numbers ≠ facts** — label low credibility.
- **Vendor metrics are marketing** — a seller's "98% usable" is a denominator claim, not a measurement.
- **Search pollution for short terms** — rephrase with domain context; one retry with different phrasing usually succeeds.
- **Price/figure snapshots expire** — date every number and re-verify before reuse.
- **After a premise correction, rewrite the whole report** — do not bolt addenda on top; re-derive conclusions from the corrected definition.
- **Patch tools can silently eat table rows** — after any multi-hunk table edit, check the diff.
- **Extractors drop list-item bodies** — content extractors silently strip `<li>` body text from clause-style pages (e.g. platform review guidelines). Save the HTML with curl and grep the clause numbers verbatim.

## License

MIT
