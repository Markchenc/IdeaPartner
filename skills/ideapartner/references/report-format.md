# Researcher-Facing Synthesis (M7)

The final response contains three visible parts: M4, M5, and M7. Follow the researcher's language. Prefer an auditable explanation over exhaustive prose. The isolated M7 worker must read the original input, M1, M2, M3 synthesis, M4, M5-A/B/C/D, and M6 from its task packet; final synthesis is not allowed to rely on a supervisor's memory of those artifacts.

## Part I: M4 structured idea

Present the six sections from [idea reconstruction](idea-reconstruction.md):

1. problem definition;
2. limitations/core difficulty;
3. core research/contribution design;
4. method construction;
5. experimental setting;
6. expected difficulties.

Call out inferred and missing content where it changes the review.

## Part II: M5 conditioned review

State the confirmed maturity, contribution type, and field/track evidence norms that shaped the review. Then report M5-A through M5-D in dependency order.

For each task include:

- current judgment and status;
- strongest supporting evidence;
- strongest counterevidence or alternative;
- key unknowns and coverage limits;
- blocker, if any, and its scope;
- what evidence would change the judgment;
- recommended revision or verification.

Integrate citations where they support a specific claim. Do not include a separate literature dump.

Use only canonical M3 evidence claim IDs retained by M4–M6. List every claim ID used by a literature-dependent statement in the M7 `citation_claim_ids` closure list, then render its verified source citation near that statement. If the desired statement has no canonical claim, narrow it or return to M3; do not attach a plausible paper ad hoc.

## Part III: M7 synthesis

Synthesize rather than average. Include:

- overall scientific-potential judgment;
- strongest part of the idea;
- most consequential current problem;
- fatal, repairable, and unresolved issues;
- whether the contribution claim survives closest-work comparison;
- whether the current solution logic is aligned;
- whether the idea is scientifically testable and presently executable;
- what to retain, revise, and verify;
- the next highest-information action;
- evidence that should trigger pivot or stop.

Use a calibrated conclusion such as:

- worth continuing;
- promising but needs reframing;
- contribution may hold but evidence is insufficient;
- current contribution is subsumed by prior work;
- problem is valuable but the solution direction is misaligned;
- scientifically researchable but currently resource-blocked;
- no reliable judgment is possible yet.

Do not output a 0–100 score, weighted total, conference-style accept/reject, or certainty unsupported by the evidence record.

Return `report_markdown`, `conclusion`, and `citation_claim_ids` according to [artifact contracts](artifact-contracts.md). After ingestion, present the runtime-generated `07-final-report.md` only if `validate` reports no core integrity error.
