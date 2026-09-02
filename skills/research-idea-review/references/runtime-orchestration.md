# Runtime Orchestration

Use the runtime for every full review. It turns the scientific workflow into an auditable artifact graph; it does not replace scientific judgment.

## Supervisor responsibility

The main Codex context is a supervisor. Keep only:

- the run directory and current state;
- the latest researcher checkpoint decision;
- ready, blocked, and stale task IDs;
- concise artifact summaries and exceptions requiring researcher attention.

Do not perform M3–M7 as one continuous hidden chain in the supervisor context. Generate a task packet and dispatch each bounded task to a fresh Codex worker context when isolated workers are available. A worker receives the packet path, not the entire chat transcript.

The supervisor remains responsible for:

- showing M1 to the researcher and actually waiting;
- deciding when a worker result needs another bounded retrieval pass;
- ingesting only completed submissions;
- presenting the final report and material limitations.

## Runtime entrypoint

The runtime uses only the Python standard library:

```text
scripts/idea_review.py
```

Run it from the researcher's workspace by using the script's absolute path. In the examples below, `<runtime>` means the absolute `scripts/idea_review.py` path inside this skill:

```bash
python <runtime> init idea.md --run-id <run-id>
python <runtime> status .idea-review/runs/<run-id>
python <runtime> emit-task .idea-review/runs/<run-id> m1-positioning
python <runtime> ingest .idea-review/runs/<run-id> m1-positioning <submission.json>
python <runtime> confirm .idea-review/runs/<run-id> --checkpoint positioning --note "<researcher response>"
python <runtime> validate .idea-review/runs/<run-id>
```

Resolve these paths relative to this skill directory. Put review runs in the researcher's current workspace, normally under `.idea-review/runs/`; never store them inside the installed skill.

## Worker protocol

For every ready task:

1. Run `emit-task`.
2. Start a fresh worker context.
3. Give it the absolute task-packet path and ask it to execute that packet exactly.
4. The worker reads:
   - every item in `inputs`, in full;
   - the specified instruction file and section;
   - the artifact contract for its task.
5. The worker writes the submission JSON to `output_contract.submission_path`.
6. Ingest the submission. Do not copy unvalidated prose into the next stage.

Each submission must acknowledge every input's registered artifact version and briefly state how that artifact changed the result. This is an auditable consumption record, not a request for generic summaries.

Each submission also provides a two-to-four-sentence `summary` and a short `attention_items` list. These are copied into the manifest for supervisor status tracking. They never replace full upstream artifacts in a worker packet.

M3-foundation, M3-data, and M3-frontier may run in parallel in separate contexts. M5-A and M5-B may also run in parallel. All other task ordering comes from the emitted dependency graph.

## Dependency preservation across isolated contexts

The task graph deliberately repeats important upstream artifacts:

- M4 reads original input, M1, M2, and M3 synthesis.
- Every M5 task reads original input, M1, M2, M3 synthesis, and M4; C additionally reads A/B, and D reads A/B/C.
- M6 and M7 again read original input, M1, M2, M3 synthesis, M4, and all required review artifacts.

Do not shorten a packet because an upstream worker “already knew” something. Paths are absolute, each artifact has a monotonic version, and ingestion compares the worker acknowledgements to the versions currently registered in the manifest. If M1, M2, or M3 is replaced, its version increments and later artifacts that consumed an older version become stale automatically.

Version binding protects workflow lineage; it does not claim that file bytes are authentic or that a cited paper exists. Source existence and metadata are checked by the evidence resolver. The manifest's complete read-modify-write transaction is protected by a cross-process file lock, and each process reloads the manifest only after acquiring that lock.

This proves that the correct artifacts were supplied, versioned, and acknowledged. It cannot prove that a model reasoned perfectly from them; task-specific output contracts and independent M3 grounding make misuse visible for review.

## Checkpoints

After M1 ingestion, show the positioning card and stop the current turn. Do not execute `confirm`, M2, or any retrieval until the researcher explicitly confirms or corrects the positioning.

If M3 reports `repositioning.required: true`, the runtime creates a second stop before M4. Show the evidence-driven change and ask the researcher. Confirm it only after an explicit response. If the correction changes canonical M1 content, replace M1 and rerun every artifact that becomes stale.

## Evidence verification modes

M3 discovery ingestion defaults to live verification. The runtime disregards any worker-authored `verification` field and resolves source identity using DOI/Crossref, arXiv, OpenAlex, or a public HTTPS resource.

Use deferred mode only when network resolution is temporarily unavailable:

```bash
python <runtime> ingest <run-dir> <m3-task> <submission.json> --verification-mode deferred
```

Deferred sources remain candidates. They cannot support an evidence claim, blocker, or final citation until a live-verified M3 artifact replaces them. Network failure means “unverified,” never “the work does not exist.”

## Recovery behavior

- Missing dependency: complete or regenerate the named upstream task.
- Stale dependency: re-emit and replace the earliest stale artifact, then follow the state forward.
- Unverified source: correct its identifier/metadata, retrieve a stronger direct source, or keep the affected conclusion uncertain.
- Unsupported evidence relation: return to M3 synthesis and ground the claim with an exact locator; do not patch the M5 wording.
- Checkpoint block: ask the researcher; never synthesize a confirmation.

Use `--replace` only for a deliberate new artifact version. Replacing upstream work is recoverable because old downstream files remain present but are marked stale.
