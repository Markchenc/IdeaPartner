# Pipeline PR Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Correct dependency identity, concurrent manifest updates, source-type validation, CI coverage, and M5 contract documentation without redesigning the M5 scientific review in this PR.

**Architecture:** Replace content digests with monotonic artifact versions and require every task submission to consume the current registered version of each upstream artifact. Serialize every manifest read-modify-write transaction through a cross-platform process lock, while retaining source existence and metadata validation as a separate evidence concern. Keep the existing M5 payload contract as a transport boundary and defer scientific M5 redesign to a later PR.

**Tech Stack:** Python 3 standard library, JSON artifacts, `unittest`, GitHub Actions, Markdown.

---

### Task 1: Replace SHA dependencies with artifact versions

**Files:**
- Modify: `skills/research-idea-review/scripts/idea_review_runtime/artifacts.py`
- Modify: `skills/research-idea-review/scripts/idea_review_runtime/pipeline.py`
- Modify: `skills/research-idea-review/scripts/idea_review_runtime/validation.py`
- Modify: `tests/helpers.py`
- Modify: `tests/test_pipeline.py`

**Steps:**
1. Add tests asserting task packets and submissions use `artifact_version`, not `sha256`.
2. Store version 1 for new artifacts and increment the version on replacement.
3. Detect stale downstream artifacts by comparing recorded dependency versions with current manifest versions.
4. Remove file-digest checks from checkpoints, task packets, exports, and documentation.
5. Run the dependency and checkpoint tests.

### Task 2: Serialize manifest transactions

**Files:**
- Create: `skills/research-idea-review/scripts/idea_review_runtime/locking.py`
- Modify: `skills/research-idea-review/scripts/idea_review_runtime/pipeline.py`
- Modify: `tests/test_pipeline.py`

**Steps:**
1. Add a cross-process concurrency test that ingests two ready M3 workers simultaneously.
2. Implement a bounded Windows/POSIX exclusive file lock using only the standard library.
3. Under the lock, reload the manifest before every checkpoint, task-emission, and ingestion transaction.
4. Write the artifact and manifest before releasing the lock.
5. Verify both concurrent manifest updates survive on Windows and Linux-compatible code paths.

### Task 3: Enforce source-type identity policy

**Files:**
- Modify: `skills/research-idea-review/scripts/idea_review_runtime/evidence.py`
- Modify: `tests/test_evidence.py`
- Modify: `skills/research-idea-review/references/artifact-contracts.md`

**Steps:**
1. Add a failing test for an arbitrary `source_type` with a reachable URL.
2. Restrict values to paper, dataset, benchmark, repository, official_docs, and first_party_report.
3. Require URL-only identity title matching for every allowed source type; do not allow classification fallback.
4. Run evidence integrity tests.

### Task 4: Clarify the M5 artifact contract boundary

**Files:**
- Modify: `skills/research-idea-review/references/artifact-contracts.md`
- Modify: `skills/research-idea-review/references/review-chain.md`
- Modify: `docs/adr/0002-codex-native-artifact-pipeline.md`

**Steps:**
1. Explain that the M5 artifact contract is a stable inter-agent transport envelope, not the final M5 metacognitive ontology.
2. Explain which fields are currently enforced and which scientific semantics remain prompt/worker responsibilities.
3. Record that contribution-conditioned questions, judgment decomposition, conflict logic, and blocker semantics will be redesigned in a later PR.
4. Do not change M5 output keys or scientific evaluation behavior in this PR.

### Task 5: Add CI and finish verification

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `skills/research-idea-review/references/runtime-orchestration.md`

**Steps:**
1. Add a least-privilege GitHub Actions workflow for Ubuntu and Windows.
2. Run unit tests and Python compile checks in CI.
3. Run the full test suite locally.
4. Run the Codex skill validator, Markdown link check, diff check, and credential scan.
5. Commit and push the focused hardening changes to the existing feature branch.
