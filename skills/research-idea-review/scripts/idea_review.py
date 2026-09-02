#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from idea_review_runtime import __version__
from idea_review_runtime.evidence import LiveSourceVerifier
from idea_review_runtime.pipeline import PipelineError, ReviewPipeline


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("idea-%Y%m%d-%H%M%S")


def _load_pipeline(run_dir: str, verification_mode: str = "live") -> ReviewPipeline:
    return ReviewPipeline(
        Path(run_dir),
        source_verifier=LiveSourceVerifier(enabled=verification_mode == "live"),
    )


def command_init(args: argparse.Namespace) -> None:
    idea_path = Path(args.idea_file)
    idea_text = idea_path.read_text(encoding="utf-8")
    pipeline = ReviewPipeline.create(
        Path(args.runs_dir),
        idea_text,
        run_id=args.run_id or _default_run_id(),
        source_verifier=LiveSourceVerifier(),
    )
    _print_json({"run_dir": str(pipeline.run_dir), **pipeline.status()})


def command_status(args: argparse.Namespace) -> None:
    _print_json(_load_pipeline(args.run_dir, "deferred").status())


def command_emit_task(args: argparse.Namespace) -> None:
    pipeline = _load_pipeline(args.run_dir, "deferred")
    packet = pipeline.emit_task(args.task_id, refresh=args.refresh)
    packet_path = pipeline.run_dir / "tasks" / f"{args.task_id}.json"
    _print_json(
        {
            "task_id": args.task_id,
            "task_packet": str(packet_path),
            "state": pipeline.compute_state(),
            "input_artifacts": [item["artifact_id"] for item in packet["inputs"]],
        }
    )


def command_confirm(args: argparse.Namespace) -> None:
    pipeline = _load_pipeline(args.run_dir, "deferred")
    if args.checkpoint == "positioning":
        pipeline.confirm_positioning(args.note)
    else:
        pipeline.confirm_post_m3(args.note)
    _print_json(pipeline.status())


def command_ingest(args: argparse.Namespace) -> None:
    pipeline = _load_pipeline(args.run_dir, args.verification_mode)
    artifact_path = pipeline.ingest(
        args.task_id,
        Path(args.submission),
        replace=args.replace,
    )
    _print_json(
        {
            "task_id": args.task_id,
            "artifact": str(artifact_path),
            "verification_mode": args.verification_mode,
            "state": pipeline.compute_state(),
        }
    )


def command_validate(args: argparse.Namespace) -> None:
    result = _load_pipeline(args.run_dir, "deferred").validate_run()
    _print_json(result)
    if not result["valid"]:
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic artifact runtime for the IdeaPartner research-idea-review skill."
    )
    parser.add_argument("--version", action="version", version=f"IdeaPartner runtime {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new review run from an idea Markdown file")
    init_parser.add_argument("idea_file", help="UTF-8 Markdown or text file containing the researcher's idea")
    init_parser.add_argument("--runs-dir", default=".idea-review/runs", help="Parent directory for review runs")
    init_parser.add_argument("--run-id", help="Stable run identifier; generated when omitted")
    init_parser.set_defaults(handler=command_init)

    status_parser = subparsers.add_parser("status", help="Show run state, ready tasks, artifacts, and checkpoints")
    status_parser.add_argument("run_dir")
    status_parser.set_defaults(handler=command_status)

    emit_parser = subparsers.add_parser("emit-task", help="Create a dependency-pinned task packet")
    emit_parser.add_argument("run_dir")
    emit_parser.add_argument("task_id")
    emit_parser.add_argument("--refresh", action="store_true", help="Emit a new packet for a completed task")
    emit_parser.set_defaults(handler=command_emit_task)

    confirm_parser = subparsers.add_parser("confirm", help="Record an explicit researcher checkpoint decision")
    confirm_parser.add_argument("run_dir")
    confirm_parser.add_argument("--checkpoint", choices=("positioning", "post-m3"), default="positioning")
    confirm_parser.add_argument("--note", required=True, help="Researcher confirmation or correction note")
    confirm_parser.set_defaults(handler=command_confirm)

    ingest_parser = subparsers.add_parser("ingest", help="Validate and store an isolated worker submission")
    ingest_parser.add_argument("run_dir")
    ingest_parser.add_argument("task_id")
    ingest_parser.add_argument("submission", help="Path to the worker submission JSON")
    ingest_parser.add_argument("--replace", action="store_true", help="Replace an existing artifact version")
    ingest_parser.add_argument(
        "--verification-mode",
        choices=("live", "deferred"),
        default="live",
        help="Resolve M3 source identities now, or retain them as unverified candidates",
    )
    ingest_parser.set_defaults(handler=command_ingest)

    validate_parser = subparsers.add_parser("validate", help="Audit core run invariants")
    validate_parser.add_argument("run_dir")
    validate_parser.set_defaults(handler=command_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except PipelineError as error:
        print(f"IdeaPartner pipeline error: {error}", file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"IdeaPartner input error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
