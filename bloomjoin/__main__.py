import argparse
import json
from pathlib import Path
from .data import generate
from .experiment import run


def main():
    parser = argparse.ArgumentParser(description="Generate SQLite data and run a verified distributed join")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--overlap", type=float, default=0.1)
    parser.add_argument("--payload-bytes", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("results/baseline.json"))
    args = parser.parse_args()
    paths = generate(args.data_dir, args.rows, args.overlap, args.payload_bytes, args.seed)
    metrics = run(*paths)
    metrics["configuration"] = {"rows_per_site": args.rows, "overlap": args.overlap,
                                "payload_bytes": args.payload_bytes, "seed": args.seed}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
