---
name: ideapartner
description: Review one early or developed research idea through three isolated stages, targeted evidence gathering, and a structured final report. Use for research positioning, novelty, method validity and next-step decisions, not finished-manuscript review.
---

# IdeaPartner

Complete the review end to end without positioning or repositioning confirmation. Preserve the original idea, distinguish facts from inference, and calibrate demands to its maturity.

## Three-stage execution

Read [runtime orchestration](references/runtime-orchestration.md). Use the Python runtime to create a run, emit packets, ingest results and validate the final export. Codex is the supervisor; Python does not launch models.

1. **s1-plan:** Run a fresh worker using [positioning and routing](references/positioning-and-routing.md). Produce a short claim-and-question plan. Continue automatically.
2. **s2-review:** Run a different worker using [integrated review](references/review-chain.md). Keep this worker active across targeted retrieval, evidence batches and challenges. Consult [targeted retrieval](references/domain-prior.md) when evidence is needed. Do not spawn agents per search or dimension.
3. **s3-report:** Run a fresh worker using [report format](references/report-format.md) and [idea reconstruction](references/idea-reconstruction.md). Deliver the six-part original idea plus assessment and next actions.

Use at most the configured number of targeted rechecks (default one), preferably by continuing the s2 worker. If it is unavailable, resume that responsibility from its recovery packet. Complete with qualified conclusions when retrieval or time is exhausted.

Do not substitute one hidden supervisor monologue for the three isolated stages. If the host cannot provide workers, disclose that isolation is unavailable rather than claim it happened.

## Scientific constraints

- Do not invent missing claims or penalize an early idea for unnecessary implementation detail.
- Use explicit working assumptions or conditional branches for ambiguity; do not pause for routine confirmation.
- Never infer novelty from a failed search. Distinguish different, novel and valuable.
- Inspect the decisive closest work beyond its title or abstract. Check substantive differences before concluding subsumption.
- Distinguish scientific testability from feasibility under the researcher's known constraints.
- Record supporting and opposing evidence, locators, and limitations. Source identity verification does not establish semantic support.
- Every retrieval batch must serve a decision-changing question. No mandatory historical tree or broad field map.
- Report improvements/pivots as suggestions separately from the original idea. Do not claim their novelty without checking.
- No weighted score or acceptance prediction.

Read only the needed [artifact contract](references/artifact-contracts.md) section. Use current judgments and evidence references as handoffs, not search transcripts or repeated analyses.
