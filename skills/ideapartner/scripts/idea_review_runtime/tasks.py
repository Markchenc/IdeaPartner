"""Three cognitive stages; retrieval batches are not agent tasks."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    artifact_id: str
    dependencies: tuple[str, ...]
    instruction_file: str
    objective: str

TASKS = {s.task_id: s for s in (
    TaskSpec("s1-plan", "plan", ("input",), "positioning-and-routing.md",
             "Identify original claims, boundaries and decision-changing questions."),
    TaskSpec("s2-review", "review", ("input", "plan"), "review-chain.md",
             "Investigate decision-relevant questions and challenge consequential judgments."),
    TaskSpec("s3-report", "report", ("input", "plan", "review"), "report-format.md",
             "Check original-idea fidelity; deliver six-part reconstruction and review."),
)}
TASK_ORDER = tuple(TASKS)
