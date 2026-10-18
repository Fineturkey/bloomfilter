"""Small repeatable benchmark harness; does not implement unfinished strategies."""
import argparse
import json
import platform
import sqlite3
import statistics
import tempfile
from pathlib import Path
from .data import generate
from .experiment import run


TIMING_METRICS = ("query_seconds", "filter_build_seconds")


def summarize(runs):
    if not runs:
        raise ValueError("At least one measured run is required")
    return {
        name: {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        }
        for name in TIMING_METRICS
        for values in [[entry[name] for entry in runs]]
    }


def benchmark(rows=1000, overlap=0.1, payload_bytes=32, seed=42, repeats=3, warmups=1):
    if repeats < 1 or warmups < 0:
        raise ValueError("repeats must be positive and warmups must be nonnegative")
    measured = []
    # Generate once and reuse the same databases across all runs. Clean up on failure.
    with tempfile.TemporaryDirectory(prefix="bloomjoin-benchmark-") as directory:
        paths = generate(directory, rows, overlap, payload_bytes, seed)
        for index in range(warmups + repeats):
            metrics = run(*paths, strategy="full")
            if metrics.get("verified") is not True:
                raise AssertionError("Cannot benchmark an unverified result")
            if index >= warmups:
                measured.append({"repeat": index - warmups + 1, **metrics})
    return {
        "configuration": {"rows_per_site": rows, "overlap": overlap,
                          "payload_bytes": payload_bytes, "seed": seed,
                          "repeats": repeats, "warmups": warmups, "strategy": "full"},
        "environment": {"python": platform.python_version(),
                        "platform": platform.platform(), "sqlite": sqlite3.sqlite_version},
        "measurement": {
            "network": "loopback TCP",
            "bytes": "application messages plus framing, both directions counted once",
            "timing": "configuration send through exact join; excludes generation, process startup/connection, reference validation",
            "warmups": "executed and verified; excluded from runs and summaries",
        },
        "runs": measured,
        "timing_seconds": summarize(measured),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--overlap", type=float, default=0.1)
    parser.add_argument("--payload-bytes", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark.json"))
    args = parser.parse_args()
    report = benchmark(args.rows, args.overlap, args.payload_bytes, args.seed,
                       args.repeats, args.warmups)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
