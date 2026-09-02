# Codex-Native Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the research-idea review skill into a resumable Codex-native pipeline that isolates cognitive tasks while preserving M1–M3 dependencies and enforcing only checkpoint, evidence, and provenance integrity.

**Architecture:** A standard-library Python runtime stores one artifact graph per review run and emits self-contained task packets for isolated Codex workers. Every downstream artifact records the exact upstream digests it consumed; the runtime blocks missing, stale, or unacknowledged dependencies and keeps verified sources separate from unsupported assertions. The skill remains the supervisor and user-facing interaction layer.

**Tech Stack:** Python 3 standard library, JSON/JSONL artifacts, Markdown skill references, `unittest`, Git.

---

### Task 1: Record the V1.1 architecture

**Files:**
- Create: `docs/adr/0002-codex-native-artifact-pipeline.md`
- Create: `docs/plans/2026-09-02-codex-native-pipeline.md`

**Steps:**
1. Document the supervisor/runtime/worker/evidence separation.
2. Make the complete M1–M7 dependency graph explicit.
3. Limit validation to checkpoints, evidence integrity, and provenance.
4. Record the limits of identifier and semantic verification.

### Task 2: Write state and dependency tests

**Files:**
- Create: `tests/test_pipeline.py`
- Create: `skills/research-idea-review/scripts/idea_review_runtime/__init__.py`

**Steps:**
1. Write a test that initializes a run and ingests M1.
2. Verify M2 cannot be emitted before researcher confirmation.
3. Confirm positioning and verify M2 becomes ready.
4. Verify M4 cannot run until M1, M2, and synthesized M3 exist.
5. Verify replacing an upstream artifact makes a downstream artifact stale.
6. Run: `python -m unittest discover -s tests -v` and observe the expected initial failures.

### Task 3: Implement the artifact pipeline

**Files:**
- Create: `skills/research-idea-review/scripts/idea_review.py`
- Create: `skills/research-idea-review/scripts/idea_review_runtime/artifacts.py`
- Create: `skills/research-idea-review/scripts/idea_review_runtime/pipeline.py`
- Create: `skills/research-idea-review/scripts/idea_review_runtime/tasks.py`
- Create: `skills/research-idea-review/scripts/idea_review_runtime/validation.py`

**Steps:**
1. Define the task graph and complete dependency lists.
2. Implement run initialization and atomic manifest/artifact writes.
3. Emit task packets with exact paths, digests, purposes, and output contracts.
4. Require worker submissions to acknowledge how every dependency was used.
5. Enforce the positioning checkpoint and dependency freshness during emission and ingestion.
6. Add CLI commands for `init`, `status`, `emit-task`, `confirm`, `ingest`, and `validate`.
7. Run the state and dependency tests until they pass.

### Task 4: Write evidence and provenance tests

**Files:**
- Modify: `tests/test_pipeline.py`
- Create: `tests/test_evidence.py`

**Steps:**
1. Test source verification through an injected fake resolver.
2. Test that an unresolved source cannot support an M3 claim or M5 blocker.
3. Test that every cited source is registered in M3.
4. Test that an evidence-supported M4 item requires a verified source.
5. Test that inferred or missing content cannot masquerade as retrieved evidence.
6. Run the tests and observe the expected failures before implementation.

### Task 5: Implement source and provenance integrity

**Files:**
- Create: `skills/research-idea-review/scripts/idea_review_runtime/evidence.py`
- Modify: `skills/research-idea-review/scripts/idea_review_runtime/pipeline.py`
- Modify: `skills/research-idea-review/scripts/idea_review_runtime/validation.py`

**Steps:**
1. Define normalized source and claim-evidence records.
2. Implement DOI, arXiv, OpenAlex, and first-party URL resolvers with bounded timeouts.
3. Ignore self-declared verification and attach runtime-generated verification results.
4. Allow unresolved candidates to remain visible but prohibit them from supporting review claims.
5. Enforce citation closure and direct verified sources for blockers.
6. Enforce the four provenance states only where idea content or evidence enters the pipeline.
7. Run all unit tests until they pass.

### Task 6: Rebuild the skill orchestration and M3 workflow

**Files:**
- Modify: `skills/research-idea-review/SKILL.md`
- Modify: `skills/research-idea-review/references/domain-prior.md`
- Modify: `skills/research-idea-review/references/positioning-and-routing.md`
- Modify: `skills/research-idea-review/references/idea-reconstruction.md`
- Modify: `skills/research-idea-review/references/review-chain.md`
- Modify: `skills/research-idea-review/references/report-format.md`
- Create: `skills/research-idea-review/references/runtime-orchestration.md`
- Create: `skills/research-idea-review/references/artifact-contracts.md`
- Modify: `skills/research-idea-review/agents/openai.yaml`

**Steps:**
1. Make the Python runtime mandatory for full reviews.
2. Define the supervisor's compact context and the isolated worker protocol.
3. Split M3 into foundation/history, data/infrastructure, frontier/practice, and synthesis workers.
4. Require M4–M7 task packets to include M1, M2, and synthesized M3 explicitly.
5. Define focused recovery behavior for evidence gaps and evidence-triggered repositioning.
6. Keep existing scientific review semantics while removing duplicated procedural prose.

### Task 7: Verify and publish

**Files:**
- Modify: `README.md`

**Steps:**
1. Document how to start, inspect, resume, and validate a review run.
2. Run: `python -m unittest discover -s tests -v` and expect all tests to pass.
3. Run the bundled Codex skill validator on `skills/research-idea-review`.
4. Check all local Markdown links and scan the repository for accidental credentials.
5. Review the full diff for unnecessary validation or hidden context reliance.
6. Commit the implementation on `feat/codex-native-pipeline`.
7. Push the branch to `origin`.
