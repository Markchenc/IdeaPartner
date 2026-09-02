from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    artifact_id: str
    artifact_path: str
    dependencies: tuple[str, ...]
    objective: str
    instruction_file: str
    instruction_section: str
    required_payload_keys: tuple[str, ...]
    checkpoint: str | None = None


INPUT_ARTIFACT_ID = "m0-input"


ARTIFACT_PURPOSES = {
    "m0-input": "Preserve the researcher's original wording, boundaries, and omissions.",
    "m1-positioning": "Use the researcher-confirmed domain, scenario, object, difficulty, contribution, and maturity.",
    "m2-route": "Apply the calibrated maturity, review route, evidence scope, and contribution lens.",
    "m3-foundation": "Use historical branches, canonical definitions, consensus, controversies, and classic work.",
    "m3-data": "Use datasets, benchmarks, metrics, protocols, resources, and known data risks.",
    "m3-frontier": "Use recent work, practice, open tensions, negative results, and adjacent-field collisions.",
    "m3-synthesis": "Use the verified evolution tree, field map, closest work, evidence coverage, and idea attachment.",
    "m4-reconstruction": "Review the exact six-part idea object while preserving provenance and missingness.",
    "m5-a": "Carry forward the problem-legitimacy judgment, evidence, alternatives, and blockers.",
    "m5-b": "Carry forward the contribution-positioning judgment and closest-work comparison.",
    "m5-c": "Carry forward the audited problem-to-mechanism chain and retained assumptions.",
    "m5-d": "Carry forward researchability, feasibility conditions, and execution blockers.",
    "m6-challenge": "Integrate the targeted adversarial checks and their changes to M5 judgments.",
}


TASKS = {
    spec.task_id: spec
    for spec in (
        TaskSpec(
            "m1-positioning",
            "m1-positioning",
            "01-positioning.json",
            ("m0-input",),
            "Convert the researcher's current idea into the complete M1 positioning card without inventing missing content.",
            "references/positioning-and-routing.md",
            "M1: structured positioning card",
            ("domains", "scenario", "research_object", "core_difficulty", "contribution", "maturity", "control"),
        ),
        TaskSpec(
            "m2-route",
            "m2-route",
            "02-route.json",
            ("m0-input", "m1-positioning"),
            "Compile the review route, calibrated maturity, evidence scope, and review-lens seed after confirmation.",
            "references/positioning-and-routing.md",
            "M2: route compilation after confirmation",
            ("maturity", "alignment_questions", "m3_scope", "m4_assessability", "review_lens_seed"),
            checkpoint="positioning",
        ),
        TaskSpec(
            "m3-foundation",
            "m3-foundation",
            "03-domain-prior/foundation.json",
            ("m0-input", "m1-positioning", "m2-route"),
            "Retrieve the field's problem history, terminology, canonical branches, consensus, controversies, and foundational work.",
            "references/domain-prior.md",
            "Phase 2: foundation and historical paths",
            ("scope", "queries", "sources", "evidence_claims", "coverage"),
        ),
        TaskSpec(
            "m3-data",
            "m3-data",
            "03-domain-prior/data-infrastructure.json",
            ("m0-input", "m1-positioning", "m2-route"),
            "Retrieve datasets, benchmarks, metrics, protocols, accessible resources, and data or measurement risks.",
            "references/domain-prior.md",
            "Phase 3: data and research infrastructure",
            ("scope", "queries", "sources", "evidence_claims", "coverage"),
        ),
        TaskSpec(
            "m3-frontier",
            "m3-frontier",
            "03-domain-prior/frontier-practice.json",
            ("m0-input", "m1-positioning", "m2-route"),
            "Retrieve recent closest work, negative results, industrial practice, adjacent collisions, and live frontier tensions.",
            "references/domain-prior.md",
            "Phase 4: frontier, practice, and collision search",
            ("scope", "queries", "sources", "evidence_claims", "coverage"),
        ),
        TaskSpec(
            "m3-synthesis",
            "m3-synthesis",
            "03-domain-prior/synthesis.json",
            ("m0-input", "m1-positioning", "m2-route", "m3-foundation", "m3-data", "m3-frontier"),
            "Synthesize verified M3 evidence into an evolution tree, layered field map, closest-work set, coverage audit, and idea attachment.",
            "references/domain-prior.md",
            "Phases 5–6: synthesis and coverage audit",
            ("evolution_tree", "field_map", "idea_attachment", "closest_work", "evidence_claims", "coverage", "repositioning"),
        ),
        TaskSpec(
            "m4-reconstruction",
            "m4-reconstruction",
            "04-structured-idea.json",
            ("m0-input", "m1-positioning", "m2-route", "m3-synthesis"),
            "Reconstruct the confirmed idea into six inspectable sections using M3 evidence while preserving provenance and missingness.",
            "references/idea-reconstruction.md",
            "Six-section structure",
            (
                "problem_definition",
                "limitations_and_core_difficulty",
                "contribution_design",
                "method_construction",
                "experimental_setting",
                "expected_difficulties",
            ),
            checkpoint="post-m3",
        ),
        TaskSpec(
            "m5-a",
            "m5-a",
            "05-review/review-a.json",
            ("m0-input", "m1-positioning", "m2-route", "m3-synthesis", "m4-reconstruction"),
            "Judge problem legitimacy and research value using the compiled maturity-, contribution-, and field-conditioned lens.",
            "references/review-chain.md",
            "M5-A: problem legitimacy and research value",
            ("review_lens", "judgments", "conclusion", "blocker"),
        ),
        TaskSpec(
            "m5-b",
            "m5-b",
            "05-review/review-b.json",
            ("m0-input", "m1-positioning", "m2-route", "m3-synthesis", "m4-reconstruction"),
            "Judge contribution positioning and knowledge increment against the evolution tree and closest work.",
            "references/review-chain.md",
            "M5-B: contribution positioning and knowledge increment",
            ("review_lens", "judgments", "conclusion", "blocker"),
        ),
        TaskSpec(
            "m5-c",
            "m5-c",
            "05-review/review-c.json",
            (
                "m0-input",
                "m1-positioning",
                "m2-route",
                "m3-synthesis",
                "m4-reconstruction",
                "m5-a",
                "m5-b",
            ),
            "Audit the problem-to-contribution-to-mechanism chain using the retained A/B judgments and field prior.",
            "references/review-chain.md",
            "M5-C: problem–contribution–method logic and mechanism",
            ("review_lens", "judgments", "conclusion", "blocker"),
        ),
        TaskSpec(
            "m5-d",
            "m5-d",
            "05-review/review-d.json",
            (
                "m0-input",
                "m1-positioning",
                "m2-route",
                "m3-synthesis",
                "m4-reconstruction",
                "m5-a",
                "m5-b",
                "m5-c",
            ),
            "Judge scientific testability and conditional feasibility from the mechanism and assumptions retained by M5-C.",
            "references/review-chain.md",
            "M5-D: researchability and conditional feasibility",
            ("review_lens", "judgments", "conclusion", "blocker"),
        ),
        TaskSpec(
            "m6-challenge",
            "m6-challenge",
            "06-challenge.json",
            (
                "m0-input",
                "m1-positioning",
                "m2-route",
                "m3-synthesis",
                "m4-reconstruction",
                "m5-a",
                "m5-b",
                "m5-c",
                "m5-d",
            ),
            "Run at most three high-information challenges and state exactly which M5 judgments they change.",
            "references/review-chain.md",
            "M6: lightweight challenge",
            ("selected_challenges", "updates"),
        ),
        TaskSpec(
            "m7-synthesis",
            "m7-synthesis",
            "07-synthesis.json",
            (
                "m0-input",
                "m1-positioning",
                "m2-route",
                "m3-synthesis",
                "m4-reconstruction",
                "m5-a",
                "m5-b",
                "m5-c",
                "m5-d",
                "m6-challenge",
            ),
            "Produce the researcher-facing M4/M5/M7 report without averaging conflicts or inventing evidence.",
            "references/report-format.md",
            "Researcher-facing synthesis",
            ("report_markdown", "conclusion", "citation_claim_ids"),
        ),
    )
}


TASK_ORDER = tuple(TASKS)
M3_DISCOVERY_TASKS = ("m3-foundation", "m3-data", "m3-frontier")
M5_TASKS = ("m5-a", "m5-b", "m5-c", "m5-d")
