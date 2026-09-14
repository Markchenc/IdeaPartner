# Runtime orchestration

The supervisor dispatches exactly three main cognitive roles, each in a separate worker context. It uses status and compact exceptions, not every worker's full prose. Automatically proceed between stages; there is no confirm command.

The runtime is `scripts/idea_review.py` relative to this skill. Use its absolute path from the researcher's workspace. Runs default to `.idea-review/runs/`; never put research outputs in the installed skill.

## Commands

```text
python <runtime> init <idea.md> --run-id <id> --max-rechecks 1 --review-deadline-minutes 30
python <runtime> status <run>
python <runtime> emit-task <run> s1-plan
python <runtime> ingest <run> s1-plan <submission.json>
python <runtime> emit-task <run> s2-review
python <runtime> evidence-add <run> <batch.json>
python <runtime> ingest <run> s2-review <submission.json>
python <runtime> emit-task <run> s3-report
python <runtime> ingest <run> s3-report <submission.json>
python <runtime> validate <run>
```

emit-task returns task_packet and packet_id. Send the packet path to the stage worker. The worker reads the packet's required inputs, its instruction and relevant contract section, then writes to submission_path. Submission is {task_id, packet_id, payload}; no model-authored input/version summaries.

The runtime stores immutable snapshots and binds inputs to packet IDs. It detects stale versions; this does not prove that a model consumed or correctly understood those inputs.

## Stage-two loop

Keep the s2 agent context across retrievals. Before new research, check status.research_allowed. The timer begins at the first s2 packet and does not reset on re-emission. At expiry, stop new retrieval and submit the current review with uncertainty; report generation remains allowed. The runtime cannot interrupt an already running host tool.

Each meaningful batch uses evidence-add, not another worker. Its result includes accepted/candidate claims, alias IDs, source versions and cache hits. Use returned canonical IDs/versions. On network failure keep candidate sources separate; do not use them as verified support. Deferred mode is for temporary network unavailability, not a shortcut to verification.

For long work save a compact current-review draft and unresolved questions at recovery_path. This is optional recovery data, never a canonical report input. Following context loss, read the current plan, saved draft and required evidence snapshot entries rather than rerun finished research.

## Report and recheck

s3 reads original input, plan, review and its evidence_view. That view includes all cited support, counterevidence and closest-work evidence; the complete ledger is optional, not required. Reopen decisive passages when checking the central conclusion.

If a material gap remains, submit recheck_request instead of payload. The runtime returns to s2; continue that worker with a new packet containing the request and previous review. Resubmit only the current integrated review, then run s3 again. Default one recheck. At limit_reached, finish using the same report packet with explicit limitations; do not loop or ask for workflow confirmation.

## Completion and failure

Show the manifest's versioned final_report path after validate is valid and state is FINALIZED. final-report.md is a convenience copy; the manifest points to the authoritative version.

Stale packet: re-emit the affected task. Evidence conflict: retry the batch against current state with the same content/ID; never force overwrite. Schema error: repair the submission. Unknown source: retain uncertainty or supply verified evidence. None of these failures creates a positioning approval gate.

schema_version=1 runs are read-only. New work must initialize v2 from input.md; use the old release to continue the original v1 workflow. Do not convert old judgments automatically.
