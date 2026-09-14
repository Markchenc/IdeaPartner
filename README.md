# IdeaPartner

A three-stage, evidence-grounded review of one research idea. Plan the review, investigate decision-changing questions, then reconstruct the original idea and deliver a report.

## Requirements

- A Codex host with local skills, filesystem access and isolated worker contexts.
- Python 3.11 or newer; no third-party runtime dependencies.
- Research tools and network access for source verification. Unresolved sources remain candidates, and the review may conclude with insufficient evidence.

## Current version

This checkout implements runtime/plugin **2.0.0**. It does not imply a v2.0.0 GitHub tag has been published. Install the local plugin or the local `skills/ideapartner` folder through your host's existing installation workflow. The canonical skill name remains `ideapartner`; implicit invocation remains enabled.

Invoke with:

~~~text
$ideapartner Review this research idea: <your idea>
~~~

The supervisor completes the workflow without positioning or repositioning confirmation:

1. **s1-plan:** short original-claim and decision-question brief.
2. **s2-review:** targeted research, evidence batches, four-dimensional review and consequential challenges in one worker.
3. **s3-report:** six-part original-idea reconstruction, assessment, limitations and next actions in a fresh worker.

No mandatory historical tree or full field map. No separate agent for every dimension or search. The final worker receives the current review and the evidence it cites, including counterevidence, rather than the entire research transcript.

## Runtime quick start

From the repository root:

~~~text
python skills/ideapartner/scripts/idea_review.py init idea.md --run-id my-review
python skills/ideapartner/scripts/idea_review.py status .idea-review/runs/my-review
python skills/ideapartner/scripts/idea_review.py emit-task .idea-review/runs/my-review s1-plan
~~~

Give the returned task packet to a stage worker. Ingest its submission and automatically follow ready_tasks:

~~~text
python skills/ideapartner/scripts/idea_review.py ingest .idea-review/runs/my-review s1-plan submission.json
~~~

During s2, save meaningful evidence batches:

~~~text
python skills/ideapartner/scripts/idea_review.py evidence-add .idea-review/runs/my-review batch.json
~~~

Source identity is verified separately from semantic support. Candidate or snippet-only evidence cannot support a decisive contribution judgment. Evidence references retain source and claim versions; changing relevant evidence invalidates affected results.

The research deadline defaults to 30 minutes from the first s2 packet; configure it with --review-deadline-minutes. Expiry stops new research, not qualified review/report completion. At most one targeted recheck is allowed by default (--max-rechecks). These are configurable bounds, not measured optimal settings.

Python creates packets and validates artifacts; it does not launch models or independently perform literature research. The host supervisor implements stage isolation. Source metadata/locators and schema validation cannot prove semantic correctness.

## Output and recovery

The final report contains the six original-idea sections, four review dimensions, one decision, suggestions and limitations. Inferred or missing content is explicitly labelled. Recommendations are separate from the researcher's original idea.

~~~text
python skills/ideapartner/scripts/idea_review.py validate .idea-review/runs/my-review
~~~

Present the versioned report in status.exports when validation succeeds and state is FINALIZED. final-report.md is a convenience copy. Immutable snapshots and a run lock protect manifest updates; uncommitted files do not become authoritative.

Stage 2 can save a compact recovery-review.json draft; a resumed worker reads it and the required evidence without redoing completed research.

## Compatibility

Schema v1 runs are read-only in v2. They are not automatically migrated. Initialize a new run from the original input, or use the previous release to continue an old run. Existing installed copies do not change merely because this repository is edited.

## Development

~~~text
python -m unittest discover -s tests -v
~~~

Tests use deterministic source-verifier fixtures and cover normal completion, stale packets, evidence identity and versions, counterevidence forwarding, bounded rechecks, report fidelity structure, failed commits and Unicode packaging. They do not establish literature-review quality or real token savings; evaluate those on held-out research ideas with comparable host/model settings.

See [implementation design](docs/plans/2026-09-14-three-stage-runtime-design.md), [skill entrypoint](skills/ideapartner/SKILL.md), and [artifact contracts](skills/ideapartner/references/artifact-contracts.md).
