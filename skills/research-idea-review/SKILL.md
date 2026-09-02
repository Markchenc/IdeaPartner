---
name: research-idea-review
description: Evidence-grounded, researcher-facing review of one early or developed research idea through a checkpointed, context-isolated Codex pipeline. Use when a researcher wants to position, evaluate, stress-test, or decide whether to pursue an idea. Not for reviewing a finished manuscript, generating an unrelated idea pool, ranking many ideas, or long-term research coaching.
---

# Research Idea Review

Review one research idea as an evolving scientific claim, not a miniature finished paper. Determine what is assessable at its current maturity, construct a targeted field prior, and expose uncertainty instead of manufacturing completeness.

## Operating mode

For a full review, read [runtime orchestration](references/runtime-orchestration.md) and use `scripts/idea_review.py`. The Python runtime owns state, checkpoints, task packets, artifact lineage, evidence identity, and the three core validation families. Codex owns researcher interaction, retrieval, scientific judgment, and synthesis.

Run bounded cognitive tasks in fresh Codex worker contexts when isolation is available. A worker must use its generated task packet and artifact contract; never substitute shared chat history for required inputs. M4, every M5 task, M6, and M7 explicitly receive M1, M2, and canonical M3 artifacts. Do not remove these repeated dependencies.

## Non-negotiable scientific rules

- Do not turn missing idea content into model-authored claims.
- Do not penalize an early idea for details that are not yet required.
- Do not infer novelty from failed retrieval.
- Do not use one weighted quality score or predict venue acceptance.
- Do not simulate expertise with decorative personas. Separate tasks by evidence and dependency.
- Distinguish scientific potential from present-day executability.
- A real source is not automatically supporting evidence. Bind literature-dependent claims to an inspected source and exact locator in M3.
- Treat unresolved retrieval as uncertainty, not non-existence.

## Workflow

### M0–M1: intake and structured positioning

Read [positioning and routing](references/positioning-and-routing.md). Initialize a run, emit `m1-positioning`, and ingest the isolated worker result.

Show the complete M1 positioning card to the researcher. **Stop the turn and wait for explicit confirmation or correction. Do not execute the confirmation command, M2, retrieval, or any later task in the same turn.**

### M2: review routing

After the researcher confirms, record the checkpoint and execute `m2-route`. M2 checks preliminary alignment, calibrates maturity, scopes M3, and compiles the contribution- and maturity-conditioned route. It does not issue final quality judgments.

### M3: targeted domain prior

Read [domain prior](references/domain-prior.md). Dispatch `m3-foundation`, `m3-data`, and `m3-frontier` to separate workers; they may run in parallel. Ingest them with live source verification. Then dispatch `m3-synthesis` as an independent grounding and integration task.

M3 produces a historical evolution tree, layered field map, verified closest-work set, canonical evidence claims, coverage audit, and current-idea attachment. If evidence materially changes the positioning, stop at the generated post-M3 checkpoint.

### M4: reconstruct the review object

Read [idea reconstruction](references/idea-reconstruction.md) and execute `m4-reconstruction`. Organize the idea into six sections while carrying M1, M2, and M3 forward explicitly. Preserve researcher-stated, evidence-supported, inferred, and missing content.

### M5–M6: conditioned dependency-chain review

Read [review chain](references/review-chain.md). Execute M5-A and M5-B independently, then M5-C from A/B, then M5-D from C and all earlier retained context. Every task receives the confirmed positioning, route, canonical field prior, and M4 idea.

Execute `m6-challenge` only after A–D. Select at most three challenges that can materially change a consequential judgment.

### M7: synthesize for the researcher

Read [report format](references/report-format.md) and execute `m7-synthesis`. Validate the complete run before presenting `07-final-report.md`. The visible report contains M4, M5, and M7; M1–M3 and M6 appear only where they shape a conclusion or evidence trail.

## Failure behavior

- If a checkpoint is pending, ask the researcher and stop.
- If an artifact is stale, regenerate from the earliest stale stage; do not reuse downstream prose.
- If source identity is unverified, it may guide search but cannot support an evidence claim, blocker, or final citation.
- If a source exists but its relation to a claim is not grounded, return to M3 synthesis for inspection and a locator.
- If evidence coverage is insufficient, narrow the conclusion, retrieve more, ask the researcher, or abstain.
- A blocker requires direct canonical M3 evidence and must state whether it blocks the formulation, contribution claim, or execution plan.

Read [artifact contracts](references/artifact-contracts.md) only when producing or checking a worker submission.
