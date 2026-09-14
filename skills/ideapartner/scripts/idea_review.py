#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from idea_review_runtime import __version__
from idea_review_runtime.pipeline import ReviewPipeline
from idea_review_runtime.evidence import LiveSourceVerifier
from idea_review_runtime.validation import PipelineError

def build_parser():
    parser = argparse.ArgumentParser(description="Three-stage IdeaPartner runtime")
    parser.add_argument("--version", action="version", version=f"IdeaPartner runtime {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("idea_file")
    init.add_argument("--runs-dir", default=".idea-review/runs")
    init.add_argument("--run-id")
    init.add_argument("--max-rechecks", type=int, default=1)
    init.add_argument("--review-deadline-minutes", type=float, default=30)
    for name in ("status", "validate"):
        commands.add_parser(name).add_argument("run_dir")
    emit = commands.add_parser("emit-task")
    emit.add_argument("run_dir"); emit.add_argument("task_id")
    emit.add_argument("--refresh", action="store_true")
    ingest = commands.add_parser("ingest")
    ingest.add_argument("run_dir"); ingest.add_argument("task_id"); ingest.add_argument("submission")
    ingest.add_argument("--replace", action="store_true")
    evidence = commands.add_parser("evidence-add")
    evidence.add_argument("run_dir"); evidence.add_argument("batch")
    evidence.add_argument("--verification-mode", choices=("live", "deferred"), default="live")
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            pipeline = ReviewPipeline.create(Path(args.runs_dir), Path(args.idea_file).read_text(encoding="utf-8-sig"),
                run_id=args.run_id or datetime.now(timezone.utc).strftime("idea-%Y%m%d-%H%M%S"),
                max_rechecks=args.max_rechecks, review_deadline_minutes=args.review_deadline_minutes)
            result = {"run_dir": str(pipeline.run_dir), **pipeline.status()}
        else:
            pipeline = ReviewPipeline(Path(args.run_dir),
                source_verifier=LiveSourceVerifier(enabled=getattr(args, "verification_mode", "deferred") == "live"))
            if args.command == "status": result = pipeline.status()
            elif args.command == "validate": result = pipeline.validate_run()
            elif args.command == "emit-task":
                packet = pipeline.emit_task(args.task_id, refresh=args.refresh)
                result = {"packet_id": packet["packet_id"], "task_packet": str(pipeline.run_dir / "tasks" / (packet["packet_id"] + ".json")),
                          "state": pipeline.compute_state()}
            elif args.command == "ingest": result = pipeline.ingest(args.task_id, Path(args.submission), replace=args.replace)
            else: result = pipeline.add_evidence(Path(args.batch))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command == "validate" and not result["valid"] else 0
    except (PipelineError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
