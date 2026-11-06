"""Rebuild timestamped transition timing JSON from the raw device log."""

import argparse
import json
from pathlib import Path

PARTS = (
    "software_disable",
    "hardware_off",
    "legacy_second_stop",
    "deadtime",
    "configure",
    "step_log",
    "core",
    "readback",
    "adc",
    "telemetry",
    "checks",
)
EVENTS = {0: "ordinary", 1: "start", 2: "reverse", 3: "emergency_stop"}


def summarize(text):
    phases = {}
    for line in text.splitlines():
        fields = line.strip().split(",")
        kind = fields[0]
        if kind not in ("BUS_CONFIG", "AUDIT", "PEAK", "MAX_PARTS", "SWITCH_EVENT", "BUS_RESULT", "END_PHASE", "PREFLIGHT"):
            continue
        phase = phases.setdefault(int(fields[1]), {"events": [], "peaks": {}, "audit": {}})
        if kind == "BUS_CONFIG":
            phase["config"] = dict(frequency=int(fields[2]), mode=fields[3])
        elif kind == "AUDIT":
            phase["audit"][fields[2]] = dict(zip(("count", "mean_us", "p95_upper_us", "p99_upper_us", "max_us"), map(int, fields[3:])))
        elif kind == "PEAK":
            duration, elapsed, event = map(int, fields[3:])
            phase["peaks"][fields[2]] = dict(duration_us=duration, elapsed_ms=elapsed, event=EVENTS[event])
        elif kind == "MAX_PARTS":
            phase["maximum_tick_parts_us"] = dict(zip(PARTS, map(int, fields[2:]), strict=True))
        elif kind == "SWITCH_EVENT":
            elapsed, event, work, writes, payload = map(int, fields[2:7])
            parts = dict(zip(PARTS, map(int, fields[7:]), strict=True))
            assert sum(parts.values()) <= work, "Overlapping component timing"
            phase["events"].append(
                dict(
                    elapsed_ms=elapsed,
                    event=EVENTS[event],
                    work_us=work,
                    off_writes=writes,
                    off_payload_bytes=payload if event == 3 else None,
                    parts_us=parts,
                    other_us=work - sum(parts.values()),
                )
            )
        elif kind == "BUS_RESULT":
            phase["result"] = dict(
                zip(
                    ("control_writes", "control_payload_bytes", "runtime_readbacks", "automatic_reverse_frames", "work_over20ms", "errors"),
                    map(int, fields[2:]),
                    strict=True,
                )
            )
        elif kind == "PREFLIGHT":
            phase["preflight"] = dict(count=int(fields[2]), errors=int(fields[3]))
        else:
            phase["completed"] = True
    assert len(phases) == 8 and "DONE" in text, "Incomplete campaign"
    for phase in phases.values():
        assert phase.get("completed") and phase["preflight"] == {"count": 100, "errors": 0}
        assert not phase["result"]["errors"]
        assert [e["event"] for e in phase["events"]] == ["start", "reverse", "emergency_stop"]
        expected = 16 if phase["config"]["mode"] == "legacy_sync" else 1
        assert [e["off_writes"] for e in phase["events"]] == [expected, expected, 8]
        maximum = phase["peaks"]["work"]
        assert maximum["duration_us"] == phase["audit"]["work"]["max_us"]
        phase["maximum_tick_other_us"] = maximum["duration_us"] - sum(phase["maximum_tick_parts_us"].values())
        assert phase["maximum_tick_other_us"] >= 0
    return phases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    data = summarize(args.log.read_text(encoding="utf-8"))
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("Eight cases complete; event counts, off writes and maximum components consistent.")


if __name__ == "__main__":
    main()
