from __future__ import annotations

from typing import Mapping


DEFAULT_THRESHOLDS = {
    "temperature": 65.0,
    "vibration": 5.0,
    "current": 12.0,
}


def calculate_health_score(
    metrics: Mapping[str, float],
    thresholds: Mapping[str, float] | None = None,
) -> float:
    """Estimate a 0-100 health score from live device metrics."""
    active_thresholds = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        active_thresholds.update(thresholds)

    penalties = []
    for metric_name, limit in active_thresholds.items():
        value = float(metrics.get(metric_name, 0.0))
        utilization = min(value / limit, 1.5) if limit else 0.0
        penalties.append(max(utilization - 0.65, 0.0) * 55.0)

    score = 100.0 - sum(penalties)
    return round(max(min(score, 100.0), 0.0), 2)
