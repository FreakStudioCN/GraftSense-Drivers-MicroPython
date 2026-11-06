"""Recompute the documented last-five-second bench acceptance from telemetry CSV.

python recompute_acceptance.py --csv ../docs/tuning/samples.csv --check ../docs/tuning/basic-acceptance.json
All paths are resolved from the caller's working directory.
"""

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, pstdev

from pid_response_metrics import response_metrics


def recompute(path):
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            values = [
                float(row[name])
                for name in ["phase", "period_ms", "elapsed_ms"] + [f"target{i}" for i in range(1, 5)] + [f"rpm{i}" for i in range(1, 5)]
            ]
            if not all(math.isfinite(value) for value in values):
                raise ValueError("Telemetry must contain finite values")
            rows.append(values)
    if not rows:
        raise ValueError("Telemetry CSV has no samples")
    result = []
    for phase in sorted({row[0] for row in rows}):
        selected = sorted((row for row in rows if row[0] == phase), key=lambda row: row[2])
        tail = [row for row in selected if row[2] >= selected[-1][2] - 5000]
        if tail[-1][2] - tail[0][2] < 4800:
            raise ValueError("At least approximately five seconds of tail samples are required")
        for motor in range(4):
            target = tail[-1][3 + motor]
            if not target or any(row[3 + motor] != target for row in tail):
                raise ValueError("Expected a constant nonzero target in each tail")
            values = [row[7 + motor] for row in tail]
            average, deviation = mean(values), pstdev(values)
            result.append(
                dict(
                    phase=int(phase),
                    motor=motor + 1,
                    target=target,
                    mean=round(average, 3),
                    std=round(deviation, 3),
                    overshoot=response_metrics(selected, motor)["overshoot_pct"],
                    passed=abs(average - target) <= max(2, abs(target) * 0.05) and deviation <= max(3, abs(target) * 0.1),
                )
            )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--check", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = recompute(args.csv)
    if args.check and result != json.loads(args.check.read_text(encoding="utf-8-sig")):
        raise SystemExit("Recomputed acceptance differs from saved JSON")
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(result)} entries recomputed; {sum(row['passed'] for row in result)} meet the stated bench criteria")


if __name__ == "__main__":
    main()
