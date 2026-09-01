# ADR 0001: Position-First Single-Review Architecture

- Status: Accepted
- Date: 2026-09-01

## Context

Existing research-idea evaluators commonly apply one generic rubric to a title, motivation, and method, then average novelty, feasibility, validity, and significance scores. This confuses idea maturity with quality, paper presentation with scientific value, and missing evidence with negative evidence. It also lets an early positioning error contaminate literature retrieval and every later judgment.

IdeaPartner V1 must support incomplete and developed research ideas while remaining controllable by a researcher. It is a single-review workflow, not yet a stateful long-term companion.

## Decision

Adopt a position-first workflow:

```text
M0 intake
→ M1 structured positioning
→ mandatory researcher confirmation
→ M2 review routing and maturity calibration
→ M3 historical evolution tree and layered field prior
→ M4 six-part idea reconstruction
→ M5 conditioned dependency-chain review
→ M6 lightweight challenge
→ M7 synthesis
```

M5 is not a scorecard. It compiles contribution type, maturity, and field evidence norms into four dependent research-judgment tasks:

```text
M5-A problem legitimacy/value ─┐
                               ├→ M5-C logic/mechanism → M5-D researchability
M5-B knowledge contribution ───┘
```

Contribution types are not detached reviewer plugins. They change the questions, evidence requirements, applicability, and gates inside every M5 task.

The final researcher-facing report exposes M4, M5, and M7. M2, M3, and M6 remain traceable support processes whose evidence appears where it affects a judgment.

## Alternatives Considered

### Generic weighted rubric

Rejected because fatal problem, novelty, or alignment failures can be hidden by unrelated high scores, and early ideas are penalized for missing mature-proposal details.

### Many parallel expert personas

Rejected because personas do not reliably create independent expertise, shared model blind spots produce pseudo-consensus, and parallel reviewers ignore dependency between problem, contribution, mechanism, and validation.

### Exhaustive survey before positioning

Rejected because it is expensive and easily searches the wrong field or track. Positioning must first constrain the evidence task.

## Consequences

- The workflow deliberately pauses after M1, so a review may require two user turns.
- Retrieval can trigger exceptional re-positioning when strong evidence changes the primary field, track, or contribution type.
- No 0–100 score or venue acceptance prediction is produced.
- Unknown, not-yet-assessable, and contradicted claims remain distinct.
- An M5-A/B/C blocker rejects only the current formulation or contribution claim; an M5-D blocker normally rejects only the current execution plan.
- V1 favors auditability and researcher control over fully autonomous throughput.
