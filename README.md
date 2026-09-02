# IdeaPartner

IdeaPartner is a collection of skills for the first mile of research: positioning, examining, and eventually developing research ideas before they become full proposals or papers.

## Current implementation

V1.1 provides a single-review Codex skill at [skills/research-idea-review](skills/research-idea-review/SKILL.md). It combines researcher-facing interaction with a deterministic Python artifact pipeline:

1. structure the idea's field, scenario, research object, difficulty, contribution type, and maturity;
2. stop for researcher confirmation;
3. compile a maturity- and contribution-conditioned review route;
4. construct a verified historical evolution tree and layered field prior through isolated literature workers;
5. reconstruct the idea into six provenance-tagged sections;
6. review it through the dependent M5-A/B/C/D chain;
7. run at most three targeted challenges and synthesize M4/M5/M7 for the researcher.

The skill deliberately avoids a single quality score, paper-acceptance prediction, and autonomous completion of missing idea content.

## Why the runtime exists

Separate agent contexts reduce context overload but can silently lose upstream assumptions. IdeaPartner therefore materializes dependencies as files. Every task packet lists all required artifacts by registered version, and every worker submission must acknowledge how it used them. Replacing an upstream artifact increments its version and makes consumers of the previous version stale. M4–M7 explicitly receive M1, M2, and canonical M3 rather than relying on shared conversation history.

Artifact versions preserve orchestration lineage; they are not evidence-authenticity checks. Literature existence and identity are validated separately through DOI, arXiv, OpenAlex, or public HTTPS resolution and metadata matching.

The runtime validates only three high-impact invariants:

- checkpoint and dependency order, including stale upstream versions;
- source identity, registered evidence closure, and direct evidence for blockers;
- provenance separation between researcher-stated, evidence-supported, inferred, and missing content.

Manifest read-modify-write transactions are serialized with a cross-process file lock, so M3 and M5 parallel workers cannot overwrite one another's manifest updates.

It does not validate prose style, arbitrary headings, answer length, or numeric scores.

## Repository layout

~~~text
skills/
  research-idea-review/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
      idea_review.py
      idea_review_runtime/
tests/
docs/
  adr/
  plans/
~~~

## Quick start

The runtime requires Python 3 and no third-party package. From the repository root:

~~~bash
python skills/research-idea-review/scripts/idea_review.py init /path/to/idea.md --run-id my-review
python skills/research-idea-review/scripts/idea_review.py status .idea-review/runs/my-review
python skills/research-idea-review/scripts/idea_review.py emit-task .idea-review/runs/my-review m1-positioning
~~~

Give the generated task packet to a fresh Codex worker and have it write the submission path specified in the packet. Then ingest it:

~~~bash
python skills/research-idea-review/scripts/idea_review.py ingest .idea-review/runs/my-review m1-positioning /path/to/submission.json
~~~

The pipeline now reports WAITING_FOR_POSITIONING_CONFIRMATION. Display M1 and wait for the researcher. Only after explicit confirmation:

~~~bash
python skills/research-idea-review/scripts/idea_review.py confirm .idea-review/runs/my-review --checkpoint positioning --note "Confirmed by researcher"
~~~

Continue with the task IDs reported by status. M3 source identity verification is live by default. A network-unresolved source remains visible as a candidate but cannot support an evidence claim or blocker.

Run the core integrity audit at any time:

~~~bash
python skills/research-idea-review/scripts/idea_review.py validate .idea-review/runs/my-review
~~~

See [runtime orchestration](skills/research-idea-review/references/runtime-orchestration.md) and [artifact contracts](skills/research-idea-review/references/artifact-contracts.md) for the worker protocol.

## Development

~~~bash
python -m unittest discover -s tests -v
~~~

## Continuous integration

GitHub Actions runs the runtime compilation and full test suite on Ubuntu and Windows with Python 3.11 and 3.13.

The planned V2 continuous companion will build on lessons from V1 after the single-review workflow has been exercised and revised.
