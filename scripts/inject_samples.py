#!/usr/bin/env python3
"""
JSON Error Sample Injector
Injects valid and invalid JSON samples into trace_history.jsonl.
Run from the project root: python scripts/inject_samples.py [--mode valid|invalid|all]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

TRACE_FILE = "data/trace_history.jsonl"

VALID_SAMPLES = [
    {
        "ts": "2026-04-20T08:00:00Z",
        "user_id_hash": "sample_valid_01",
        "session_id": "inject_session",
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "message": "What is the P95 latency threshold?",
        "answer": "The P95 latency threshold defined in SLOs is 2000ms.",
        "latency_ms": 310,
        "tokens_in": 40,
        "tokens_out": 85,
        "cost_usd": 0.000795,
        "quality": 0.9,
        "relevancy": 0.8,
        "faithfulness": 0.9,
    },
    {
        "ts": "2026-04-20T08:01:00Z",
        "user_id_hash": "sample_valid_02",
        "session_id": "inject_session",
        "feature": "summary",
        "model": "claude-sonnet-4-5",
        "message": "Summarize error handling policy",
        "answer": "All errors must be logged with correlation IDs and classified by error_type.",
        "latency_ms": 450,
        "tokens_in": 52,
        "tokens_out": 98,
        "cost_usd": 0.001026,
        "quality": 0.8,
        "relevancy": 0.8,
        "faithfulness": 0.9,
    },
]

# Invalid samples - missing required fields or wrong types
INVALID_SAMPLES = [
    # Missing 'ts' field
    {
        "user_id_hash": "err_missing_ts",
        "session_id": "err_session",
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "message": "Missing timestamp test",
        "answer": "This log is missing the ts field.",
        "latency_ms": 100,
        "tokens_in": 20,
        "tokens_out": 30,
        "cost_usd": 0.00015,
        "quality": 0.5,
        "relevancy": 0.5,
        "faithfulness": 0.5,
    },
    # Wrong type: latency_ms is a string instead of int
    {
        "ts": "2026-04-20T08:02:00Z",
        "user_id_hash": "err_wrong_type",
        "session_id": "err_session",
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "message": "Wrong type for latency_ms",
        "answer": "This log has latency_ms as a string instead of int.",
        "latency_ms": "high",  # <-- WRONG TYPE
        "tokens_in": 20,
        "tokens_out": 30,
        "cost_usd": 0.00015,
        "quality": 0.5,
        "relevancy": 0.5,
        "faithfulness": 0.5,
    },
    # Quality score out of range (>1.0)
    {
        "ts": "2026-04-20T08:03:00Z",
        "user_id_hash": "err_out_of_range",
        "session_id": "err_session",
        "feature": "terminal",
        "model": "claude-sonnet-4-5",
        "message": "Quality out of range test",
        "answer": "This log has a quality score outside the 0-1 range.",
        "latency_ms": 200,
        "tokens_in": 25,
        "tokens_out": 40,
        "cost_usd": 0.0002,
        "quality": 9.5,    # <-- OUT OF RANGE
        "relevancy": 0.5,
        "faithfulness": 0.5,
    },
    # Negative latency (invalid)
    {
        "ts": "2026-04-20T08:04:00Z",
        "user_id_hash": "err_negative_latency",
        "session_id": "err_session",
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "message": "Negative latency test",
        "answer": "Latency cannot be negative - this is a corrupted record.",
        "latency_ms": -500,  # <-- INVALID
        "tokens_in": 30,
        "tokens_out": 50,
        "cost_usd": 0.0003,
        "quality": 0.5,
        "relevancy": 0.5,
        "faithfulness": 0.5,
    },
]


def validate_sample(record: dict) -> tuple[bool, list[str]]:
    """Basic validation of a trace record."""
    errors = []
    required_fields = ["ts", "user_id_hash", "session_id", "feature", "model",
                       "message", "answer", "latency_ms", "tokens_in", "tokens_out",
                       "cost_usd", "quality", "relevancy", "faithfulness"]

    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")

    if "latency_ms" in record and not isinstance(record["latency_ms"], int):
        errors.append(f"Field 'latency_ms' must be int, got {type(record['latency_ms']).__name__}")

    if "quality" in record and isinstance(record["quality"], float | int):
        if not 0.0 <= record["quality"] <= 1.0:
            errors.append(f"Field 'quality' must be in [0.0, 1.0], got {record['quality']}")

    if "latency_ms" in record and isinstance(record["latency_ms"], int):
        if record["latency_ms"] < 0:
            errors.append(f"Field 'latency_ms' must be >= 0, got {record['latency_ms']}")

    return len(errors) == 0, errors


def inject(samples: list[dict], force: bool = False) -> None:
    os.makedirs("data", exist_ok=True)

    injected = 0
    skipped = 0

    print(f"\n{'='*55}")
    print(f"  Injecting {len(samples)} sample(s) → {TRACE_FILE}")
    print(f"{'='*55}")

    for i, sample in enumerate(samples, 1):
        is_valid, errors = validate_sample(sample)

        print(f"\n[Sample {i}] user_id_hash={sample.get('user_id_hash', '?')} | feature={sample.get('feature', '?')}")

        if not is_valid:
            print(f"  ⚠  Validation Issues ({len(errors)}):")
            for e in errors:
                print(f"     ❌ {e}")
            if force:
                print("  ⚡ Force-injecting despite errors...")
            else:
                print("  ⛔ Skipped (use --force to inject anyway).")
                skipped += 1
                continue

        with open(TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample) + "\n")
        print("  ✅ Injected successfully.")
        injected += 1

    print(f"\n{'='*55}")
    print(f"  Done. Injected: {injected} | Skipped: {skipped}")
    print(f"{'='*55}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject JSON samples into trace history.")
    parser.add_argument("--mode", choices=["valid", "invalid", "all"], default="all",
                        help="Which samples to inject (default: all)")
    parser.add_argument("--force", action="store_true",
                        help="Force inject even invalid samples (for error demonstration)")
    args = parser.parse_args()

    samples: list[dict] = []
    if args.mode in ("valid", "all"):
        samples.extend(VALID_SAMPLES)
    if args.mode in ("invalid", "all"):
        samples.extend(INVALID_SAMPLES)

    inject(samples, force=args.force)


if __name__ == "__main__":
    main()
