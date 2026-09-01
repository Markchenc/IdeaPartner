# Conditioned Review Chain (M5–M6)

M5 externalizes metacognition as dependent scientific-judgment tasks. It is not a list of independent scores.

## Compile the review lens

Before M5-A/B, combine:

```text
confirmed contribution type
× confirmed/calibrated maturity
× field and track evidence norms from M3
× the six-part M4 idea
```

This lens must change the questions, evidence requirements, applicability, and blocker semantics inside every task. Do not run contribution types as detached reviewer plugins or append an isolated “field fit” score.

When a secondary contribution is essential to the claim, integrate it only where it changes a task. Avoid duplicating a full second review.

## Dependency graph

```text
              ┌── M5-A problem legitimacy/value ──┐
M1–M4 inputs ─┤                                   ├── M5-C logic/mechanism ── M5-D researchability
              └── M5-B knowledge contribution ────┘
```

M5-A and M5-B may run independently. M5-C must consume both results. M5-D must consume the mechanism, assumptions, and claims retained by M5-C.

## Common result contract

Each task reports:

- judgment and applicability;
- supporting evidence;
- counterevidence or competing explanation;
- key assumptions;
- missing evidence and coverage limits;
- what would change the judgment;
- status;
- whether it blocks the current formulation or execution plan;
- a concrete revision or verification action.

Use `assessable`, `provisional`, `not_yet_assessable`, or `not_applicable` for applicability. Unknown is not a low score.

## M5-A: problem legitimacy and research value

### Cognitive task

Determine whether the phenomenon or need is real, whether the problem is constructed correctly, whether the claimed difficulty is a root bottleneck or a surface symptom, and what knowledge or practical value resolving it would create.

Check for benchmark/metric artifacts, boundary shifts, hidden changes of research object, and alternative explanations for the observed failure.

### Evidence

Use repeated observations, user/system/industrial evidence, historical failure, negative results, theoretical limitations, and field consensus or controversy. Paper count, popularity, and citations alone do not establish value.

### Status

`supported`, `needs_reframing`, `unresolved`, or `blocked`.

Abstain when the phenomenon has no inspectable evidence, central constructs conflict, or M3 does not cover the actual problem.

## M5-B: contribution positioning and knowledge increment

### Cognitive task

Attach the idea to the M3 evolution tree. Compare it with closest work and the natural next-step path. Locate differences in problem, framing, assumptions, mechanism, method, data, measurement, system, evidence, or application. Separate difference, novelty strength, and value.

Classify the current relation as `distinct`, `incremental`, `subsumed`, or `uncertain` and explain why. A transfer, replication, dataset, or application contribution is not invalid merely because its method is reused.

### Evidence

Inspect primary claims and implementations of closest work, terminology variants, historical rediscoveries, adjacent fields, code/benchmarks, dates, and retrieval coverage.

Only strong evidence that existing work substantially contains the core contribution can block the current contribution claim.

## M5-C: problem–contribution–method logic and mechanism

### Cognitive task

Build and audit:

```text
problem
→ core difficulty
→ contribution intervention point
→ method/mechanism/investigation logic
→ expected observable change
→ effect on the stated problem
```

Check whether the contribution targets the verified difficulty, whether each link has a defensible basis, whether the proposal relies on a hidden oracle or circular claim, and whether a simpler explanation or intervention is sufficient. Do not predict a benchmark result; judge why the route could work.

### Status

`coherent`, `partially_supported`, `misaligned`, or `not_yet_assessable`.

A blocker applies when the contribution does not act on the stated problem, core assumptions conflict, the reasoning is circular/non-falsifiable, or the method solves a different easier problem. State whether the problem remains valuable even when the current formulation fails.

## M5-D: researchability and conditional feasibility

### Cognitive task

Separate:

- **scientific testability**: whether the core claim can in principle be observed and distinguished from alternatives;
- **conditional feasibility**: whether the current researcher can execute the plan under stated data, access, time, team, compute, safety, and ethical constraints.

Identify observable variables, discriminating evidence, success/failure criteria, the cheapest decisive test, resource envelope, and residual learning value if the test fails.

### Status

`testable_now`, `testable_with_conditions`, `not_identifiable`, `resource_blocked`, or `unresolved`.

Unobservable core variables, non-discriminating validation, or unlawful/unethical data access can block execution. Resource limits normally block only the current plan, not scientific potential. Without researcher constraints, abstain from personalized feasibility claims.

## Contribution-conditioned questions inside the chain

Use this table to transform A–D, not to add a fifth reviewer.

| Contribution | M5-A: problem/value | M5-B: increment | M5-C: logic/mechanism | M5-D: researchability |
|---|---|---|---|---|
| New problem/framing | Is the phenomenon and construct real, and does the framing expose a missed problem? | Is this a substantive reorganization rather than new terminology? Does it yield new predictions or a research agenda? | Does the lens explain or connect observations better than current framings? | Can competing framings be distinguished with observable evidence? |
| Method/algorithm | Is the claimed technical bottleneck real and consequential? | What mechanism, architecture, objective, or capability differs from the natural next step? | Is the added mechanism necessary and aligned; can a simpler baseline suffice? | Can baselines, ablations, and diagnostic experiments isolate the claimed mechanism? |
| Theory | Is there a meaningful formal or explanatory gap? | Which assumptions, theorem, unification, or implication are new? | Are assumptions non-vacuous and conclusions logically connected to the target problem? | Is there a proof/counterexample route and, where relevant, testable implications? |
| Empirical discovery/measurement | Is the phenomenon meaningful rather than sampling or measurement artifact? | What new observation, construct, identification, or evidence is contributed? | Are confounds and alternative explanations addressed by the proposed design? | Can sampling and measurement distinguish the claim with adequate validity? |
| System/AI infrastructure | Is the bottleneck present in representative end-to-end workloads? | What system path changes beyond a local optimization? | Do local changes create net end-to-end benefit without cost displacement? | Are workloads, latency/throughput/cost/reliability metrics, compatibility, and deployment access adequate? |
| Dataset/benchmark | Is there a real measurement or coverage gap? | What construct, population, environment, annotation, or evaluation capability is added? | Do dataset and metric choices measure the intended capability rather than shortcuts? | Can validity, contamination, representation, reliability, and lifecycle value be assessed? |
| HCI/design research | Is there a real stakeholder need in a situated context? | What understanding, design knowledge, interaction, artifact, or theory is added? | Does the study/design logic connect context and human behavior to the claimed knowledge? | Are participants, methods, ecological validity, reflexivity, and ethics appropriate? |
| Application/translation | Is there a real stakeholder and workflow need? | What contextual, integration, or external-validity increment exists even if methods are reused? | Does the intervention fit the real workflow and constraints rather than a proxy task? | Are access, safety, regulation, deployment, and external evaluation feasible? |
| Replication/negative result | Is the original uncertainty important enough to resolve? | What new boundary, evidence, or resource-allocation consequence would result? | Does the design isolate the source of disagreement or failure? | Are fidelity, power, data comparability, and decisive outcomes adequate? |

## Maturity-conditioned depth inside the chain

### Early

- Run A fully.
- Use B primarily for positioning; mark an unclear contribution as provisional rather than weak.
- In C, inspect problem-to-perspective logic only; do not require a complete method.
- In D, ask whether a plausible research path and observable distinction exist; do not require a full experiment.

### Middle

- Run A/B/C fully at the method-direction level.
- In D, require a minimal discriminating validation, plausible data setting, and major resource conditions.
- Do not reject for missing implementation details that do not affect the core mechanism.

### Developed

- Run A–D fully.
- Require appropriate baseline logic, evaluation validity, resource fit, major robustness checks, and execution risks.
- Discuss reproducibility only when enough implementation and study detail exists.

## Conflict and blocker handling

Never average conflicting judgments. Diagnose:

- factual conflict: compare source quality and directness;
- scope conflict: verify reviewers evaluated the same claim;
- explanation conflict: preserve alternatives and name discriminating evidence;
- value conflict: expose field or stakeholder preferences;
- maturity conflict: use `not_yet_assessable`;
- retrieval conflict: keep novelty uncertain.

A blocker requires high-quality direct evidence that affects a core claim. A/B/C block continuing with the current formulation or contribution claim. D usually blocks executing the current plan. Explain whether reframing, narrowing, or redesigned validation can remove it.

## M6: lightweight challenge

Select at most three checks based on the most consequential M5 claims:

1. **Closest-prior substitution:** if the closest work replaces the proposed innovation, does the idea materially change?
2. **Simpler alternative:** is there a more direct explanation or intervention with the same expected value?
3. **Weakest assumption / minimal falsification:** which assumption is most fragile, and what cheap evidence could overturn it?

M6 does not produce a standalone report. Feed its result back into the affected M5 judgment by strengthening, weakening, or adding a blocker.
