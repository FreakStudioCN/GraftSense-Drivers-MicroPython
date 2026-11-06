"""Metrics from timestamped telemetry; no plotting or device dependencies.

Overshoot is the largest observed excursion beyond the signed target, relative
to the step size from zero. Settling uses the raw sampled +/-5% target band and
requires at least one second inside the band through the end of the record.
No settling time means the record does not demonstrate settling by this rule.
"""

from statistics import mean, pstdev


def response_metrics(rows, motor):
    active = [row for row in rows if row[3 + motor] != 0]
    if not active:
        return {}
    target = active[0][3 + motor]
    if any(row[3 + motor] != target for row in active):
        raise ValueError("Expected one step from zero to a constant target")
    times = [(row[2] - active[0][2]) / 1000 for row in active]
    values = [row[7 + motor] for row in active]
    band = abs(target) * 0.05
    outside = [i for i, value in enumerate(values) if abs(value - target) > band]
    candidate = outside[-1] + 1 if outside else 0
    settling = times[candidate] if candidate < len(times) and times[-1] - times[candidate] >= 1 else None
    direction = 1 if target > 0 else -1
    tail = [value for t, value in zip(times, values) if t >= max(0, times[-1] - 2)]
    return dict(
        target=float(target),
        overshoot_pct=round(max(0, max(direction * v for v in values) - abs(target)) / abs(target) * 100, 2),
        settling_s=settling,
        mean_tail_rpm=round(mean(tail), 3),
        std_tail_rpm=round(pstdev(tail), 3),
        band_rpm=band,
    )


def last_reference_segment(rows, motor):
    """Select the latest contiguous constant-reference segment for step metrics."""
    if not rows:
        return []
    target = rows[-1][3 + motor]
    if not target:
        return []
    start = len(rows) - 1
    while start > 0 and rows[start - 1][3 + motor] == target:
        start -= 1
    return rows[start:]
