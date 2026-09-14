# Stage 2: integrated review and challenge

Run in one stage-worker context. Read original idea and plan. Iterate question → retrieval → evidence batch → judgment → strongest counterargument → next useful question. Do not start a worker per dimension.

Account for four dimensions:
- value: reality, formulation and importance of the problem;
- contribution: increment over inspected closest work, distinguishing difference from novelty and value;
- mechanism: whether the intervention addresses the difficulty and what simpler explanation competes;
- testability: discriminating observations/experiments and feasibility under stated constraints.

Maturity changes depth: early ideas need a plausible claim and investigation path, not a finished experiment; developed ideas need baselines, controls and credible execution conditions. Do not turn unknown into a poor score.

For consequential conclusions, perform the most relevant challenge: closest-prior substitution, simpler alternative, or weakest-assumption falsification. Record the strongest counterargument and uncertainty in the judgment itself, not another challenge document.

Register evidence incrementally using evidence-add and the retrieval reference. All literature judgments use active claim versions. Candidate sources may motivate searches but cannot support findings. Input-based reasoning uses original locators; inference is labelled and explained. Source identity verification does not establish entailment.

Maintain current questions, judgments, closest comparisons, decision and stop record. Answer every planned/researched question, including unanswered ones. Use stop reason decision_supported, budget_exhausted or retrieval_unavailable. Budget limits never mean novelty established.

On recheck, inspect the named gap and update affected conclusions. Preserve valid prior work. Submit the current compact review once the gap is resolved or remains explicitly uncertain. Do not restart M1 or construct a full field map.

Use the review/evidence sections of artifact-contracts.md. On recovery read the supplied previous_review and optional recovery draft; raw search history is not a required dependency.
