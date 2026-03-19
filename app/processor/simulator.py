from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from ..analytics.health_score import calculate_health_score
from ..storage.sqlite_store import load_app_config
from ..storage.sqlite_store import load_thresholds
from ..storage.sqlite_store import persist_telemetry


DEFAULT_ANOMALY_PROFILES = {
    "normal": {
        "label": "Normal",
        "description": "Baseline telemetry with healthy operating values.",
        "multipliers": {"temperature": 0.72, "vibration": 0.68, "current": 0.7},
        "offsets": {"temperature": -2.0, "vibration": -0.1, "current": -0.2},
        "status": "active",
    },
    "overheat": {
        "label": "Overheat",
        "description": "Drive temperature above the configured thermal limit.",
        "multipliers": {"temperature": 1.18, "vibration": 0.82, "current": 0.94},
        "offsets": {"temperature": 5.0, "vibration": 0.0, "current": 0.2},
        "status": "warning",
    },
    "overload": {
        "label": "Overload",
        "description": "Increase electrical load and associated heat.",
        "multipliers": {"temperature": 1.02, "vibration": 0.92, "current": 1.22},
        "offsets": {"temperature": 2.0, "vibration": 0.15, "current": 1.4},
        "status": "warning",
    },
    "vibration_spike": {
        "label": "Vibration Spike",
        "description": "Inject excessive vibration to mimic bearing or alignment issues.",
        "multipliers": {"temperature": 0.92, "vibration": 1.28, "current": 0.9},
        "offsets": {"temperature": 0.8, "vibration": 0.9, "current": 0.0},
        "status": "warning",
    },
    "power_surge": {
        "label": "Power Surge",
        "description": "Combine current surge with heat rise for fault injection demos.",
        "multipliers": {"temperature": 1.1, "vibration": 0.98, "current": 1.3},
        "offsets": {"temperature": 3.5, "vibration": 0.2, "current": 1.8},
        "status": "warning",
    },
}


def _load_profiles() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load simulated device and anomaly profile config with defaults."""
    app_config = load_app_config()
    profiles = app_config.get("simulated_devices", [])
    if not profiles:
        profiles = [
            {
                "device_id": app_config.get("device_id", "tool-001"),
                "device_name": "Demo Power Tool",
                "location": "Lab-A",
                "status": "active",
                "base_metrics": {"temperature": 47.8, "vibration": 3.4, "current": 8.9},
                "variation": {"temperature": 1.2, "vibration": 0.25, "current": 0.3},
                "phase_offset": 0.0,
            }
        ]

    configured_profiles = dict(app_config.get("anomaly_profiles", {}))
    merged_profiles = dict(DEFAULT_ANOMALY_PROFILES)
    for scenario_name, scenario_payload in configured_profiles.items():
        existing = dict(merged_profiles.get(str(scenario_name), {}))
        existing.update(dict(scenario_payload))
        merged_profiles[str(scenario_name)] = existing

    return [dict(item) for item in profiles], merged_profiles


def list_device_profiles() -> list[dict[str, Any]]:
    """Return configured device profiles for simulation controls."""
    profiles, _ = _load_profiles()
    return profiles


def list_anomaly_profiles() -> dict[str, dict[str, Any]]:
    """Return available anomaly scenarios for simulation controls."""
    _, profiles = _load_profiles()
    return profiles


def _build_metrics(
    base_metrics: dict[str, Any],
    variation: dict[str, Any],
    phase: float,
    scenario_name: str,
    thresholds: dict[str, float],
    anomaly_profiles: dict[str, dict[str, Any]],
    intensity_scale: float = 1.0,
) -> dict[str, float]:
    """Build one metric set with optional anomaly shaping."""
    metrics = {
        "temperature": float(base_metrics.get("temperature", 42.0)) + math.sin(phase) * float(variation.get("temperature", 1.0)),
        "vibration": float(base_metrics.get("vibration", 2.5)) + math.cos(phase * 1.4) * float(variation.get("vibration", 0.2)),
        "current": float(base_metrics.get("current", 8.5)) + math.sin(phase * 0.8) * float(variation.get("current", 0.25)),
    }

    scenario = dict(anomaly_profiles.get(scenario_name, anomaly_profiles["normal"]))
    multipliers = dict(scenario.get("multipliers", {}))
    offsets = dict(scenario.get("offsets", {}))

    for metric_name in metrics:
        base_value = metrics[metric_name]
        multiplier = float(multipliers.get(metric_name, 1.0))
        offset = float(offsets.get(metric_name, 0.0)) * intensity_scale
        if scenario_name != "normal":
            multiplier = 1.0 + ((multiplier - 1.0) * intensity_scale)
        metrics[metric_name] = round(base_value * multiplier + offset, 3)

    if scenario_name != "normal":
        metrics["temperature"] = max(
            metrics["temperature"],
            round(thresholds["temperature"] * (1.0 + ((float(multipliers.get("temperature", 1.0)) - 1.0) * intensity_scale)), 3),
        )
        if scenario_name == "vibration_spike":
            metrics["vibration"] = max(metrics["vibration"], round(thresholds["vibration"] * (1.12 + 0.06 * intensity_scale), 3))
        if scenario_name in {"overload", "power_surge"}:
            metrics["current"] = max(metrics["current"], round(thresholds["current"] * (1.08 + 0.08 * intensity_scale), 3))

    return metrics


def build_sample_payloads(
    scenario_name: str = "normal",
    device_ids: list[str] | None = None,
    sample_count: int = 1,
    sample_interval_seconds: int = 1,
    continuous: bool = False,
) -> list[dict[str, object]]:
    """Build sample telemetry for configured devices under a chosen scenario."""
    thresholds = load_thresholds()
    device_profiles, anomaly_profiles = _load_profiles()
    selected_ids = set(device_ids or [])
    active_profiles = [profile for profile in device_profiles if not selected_ids or str(profile.get("device_id")) in selected_ids]
    if not active_profiles:
        active_profiles = device_profiles

    now = datetime.now(timezone.utc)
    phase_seed = now.timestamp() / 12.0
    payloads: list[dict[str, object]] = []

    for sample_index in range(max(sample_count, 1)):
        sample_timestamp = now + timedelta(seconds=sample_index * max(sample_interval_seconds, 1))
        intensity_scale = 1.0 if not continuous else min(1.0 + sample_index * 0.1, 1.45)
        for index, profile in enumerate(active_profiles):
            base_metrics = dict(profile.get("base_metrics", {}))
            variation = dict(profile.get("variation", {}))
            phase_step = 0.35 if not continuous else 0.22
            phase = phase_seed + float(profile.get("phase_offset", index * 0.9)) + sample_index * phase_step
            metrics = _build_metrics(
                base_metrics,
                variation,
                phase,
                scenario_name,
                thresholds,
                anomaly_profiles,
                intensity_scale=intensity_scale,
            )
            scenario_profile = anomaly_profiles.get(scenario_name, anomaly_profiles["normal"])

            payloads.append(
                {
                    "device_id": str(profile.get("device_id", f"tool-{index + 1:03d}")),
                    "device_name": str(profile.get("device_name", f"Demo Device {index + 1}")),
                    "location": str(profile.get("location", f"Zone-{index + 1}")),
                    "status": str(scenario_profile.get("status", profile.get("status", "active"))),
                    "timestamp": sample_timestamp.isoformat(),
                    "metrics": metrics,
                    "health_score": calculate_health_score(metrics, thresholds=thresholds),
                }
            )

    return payloads


def inject_simulated_payloads(
    scenario_name: str,
    device_ids: list[str] | None = None,
    sample_count: int = 1,
    sample_interval_seconds: int = 1,
    continuous: bool = False,
) -> list[dict[str, Any]]:
    """Persist one or more simulated payloads for dashboard and alert demos."""
    stored_messages: list[dict[str, Any]] = []
    for payload in build_sample_payloads(
        scenario_name=scenario_name,
        device_ids=device_ids,
        sample_count=sample_count,
        sample_interval_seconds=sample_interval_seconds,
        continuous=continuous,
    ):
        stored_messages.append(persist_telemetry(payload))
    return stored_messages
