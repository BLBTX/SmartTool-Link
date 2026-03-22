from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any
from typing import cast

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    simulator = importlib.import_module("app.processor.simulator")
    sqlite_store = importlib.import_module("app.storage.sqlite_store")
    inject_simulated_payloads = simulator.inject_simulated_payloads
    list_anomaly_profiles = simulator.list_anomaly_profiles
    list_device_profiles = simulator.list_device_profiles
    create_maintenance_log = sqlite_store.create_maintenance_log
    fetch_device_overview = sqlite_store.fetch_device_overview
    fetch_latest_telemetry = sqlite_store.fetch_latest_telemetry
    fetch_recent_alerts = sqlite_store.fetch_recent_alerts
    fetch_recent_maintenance = sqlite_store.fetch_recent_maintenance
    fetch_recent_telemetry = sqlite_store.fetch_recent_telemetry
else:
    from ..processor.simulator import inject_simulated_payloads
    from ..processor.simulator import list_anomaly_profiles
    from ..processor.simulator import list_device_profiles
    from ..storage.sqlite_store import create_maintenance_log
    from ..storage.sqlite_store import fetch_device_overview
    from ..storage.sqlite_store import fetch_latest_telemetry
    from ..storage.sqlite_store import fetch_recent_alerts
    from ..storage.sqlite_store import fetch_recent_maintenance
    from ..storage.sqlite_store import fetch_recent_telemetry


COLOR_PALETTE = {
    "bg": "#f3efe6",
    "surface": "#fffaf0",
    "ink": "#182028",
    "muted": "#6e6c68",
    "good": "#2f855a",
    "warn": "#c77700",
    "alert": "#b83245",
    "accent": "#195d7a",
    "accent_soft": "#cfe5eb",
}
FLEET_LABEL = "Fleet Overview"
TIME_WINDOW_OPTIONS = {
    "Last 15 min": 0.25,
    "Last 1 hour": 1.0,
    "Last 6 hours": 6.0,
    "Last 24 hours": 24.0,
    "Recent sample set": 0.0,
}
AUTO_REFRESH_OPTIONS = {
    "Off": 0,
    "10 sec": 10,
    "30 sec": 30,
    "60 sec": 60,
}
ALERT_FILTER_OPTIONS = {
    "All alerts": "all",
    "Unacknowledged": "unacknowledged",
    "Acknowledged": "acknowledged",
    "Maintained": "maintained",
}


def load_latest_telemetry() -> dict[str, object]:
    """Load the newest persisted telemetry snapshot for dashboard rendering."""
    return fetch_latest_telemetry()


def classify_health_band(score: float) -> str:
    """Group a health score into operational severity bands."""
    if score >= 85:
        return "Stable"
    if score >= 70:
        return "Watch"
    return "Alert"


def load_recent_history() -> pd.DataFrame:
    """Load recent telemetry history from SQLite for trend visualization."""
    history = fetch_recent_telemetry(limit=96)
    frame = pd.DataFrame(history)
    if frame.empty:
        return frame
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="mixed", utc=True)
    frame["health_band"] = frame["health_score"].apply(classify_health_band)
    return frame.sort_values(by=["timestamp", "device_id"]).reset_index(drop=True)


def load_device_frame() -> pd.DataFrame:
    """Load fleet-level rollups for multi-device monitoring."""
    frame = pd.DataFrame(fetch_device_overview(limit=24))
    if frame.empty:
        return frame
    frame["last_recorded_at"] = pd.to_datetime(frame["last_recorded_at"], format="mixed", utc=True)
    frame["health_band"] = frame["avg_health_score"].apply(classify_health_band)
    return frame


def load_alert_frame() -> pd.DataFrame:
    """Load recent alert events for operational review."""
    frame = pd.DataFrame(fetch_recent_alerts(limit=30))
    if frame.empty:
        return frame
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="mixed", utc=True)
    frame["health_band"] = frame["health_score"].apply(classify_health_band)
    return frame


def filter_alerts_by_state(frame: pd.DataFrame, alert_filter_key: str) -> pd.DataFrame:
    """Filter alerts by acknowledgement/maintenance state."""
    if frame.empty:
        return frame
    desired_state = ALERT_FILTER_OPTIONS.get(alert_filter_key, "all")
    if desired_state == "all":
        return frame.copy()
    filtered = frame.loc[frame["alert_state"] == desired_state].copy()
    return cast(pd.DataFrame, filtered)


def load_maintenance_frame() -> pd.DataFrame:
    """Load recent maintenance and acknowledgement events."""
    frame = pd.DataFrame(fetch_recent_maintenance(limit=40))
    if frame.empty:
        return frame
    frame["created_at"] = pd.to_datetime(frame["created_at"], format="mixed", utc=True)
    return frame


def apply_dashboard_theme() -> None:
    """Apply a deliberate visual system for the monitoring surface."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(25, 93, 122, 0.18), transparent 28%),
                radial-gradient(circle at right 20%, rgba(199, 119, 0, 0.14), transparent 20%),
                linear-gradient(180deg, {COLOR_PALETTE['bg']} 0%, #f7f4ec 100%);
            color: {COLOR_PALETTE['ink']};
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        .hero-card {{
            background: linear-gradient(135deg, rgba(255,250,240,0.95), rgba(231,240,243,0.9));
            border: 1px solid rgba(24, 32, 40, 0.08);
            border-radius: 22px;
            padding: 1.3rem 1.4rem;
            box-shadow: 0 14px 40px rgba(24, 32, 40, 0.08);
            margin-bottom: 1rem;
        }}
        .status-chip {{
            display: inline-block;
            padding: 0.3rem 0.75rem;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}
        .status-good {{ background: rgba(47,133,90,0.14); color: {COLOR_PALETTE['good']}; }}
        .status-warn {{ background: rgba(199,119,0,0.14); color: {COLOR_PALETTE['warn']}; }}
        .status-alert {{ background: rgba(184,50,69,0.14); color: {COLOR_PALETTE['alert']}; }}
        .status-maintenance {{ background: rgba(25,93,122,0.14); color: {COLOR_PALETTE['accent']}; }}
        .metric-strip {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 1rem 0 1.3rem 0;
        }}
        .metric-card {{
            background: rgba(255,250,240,0.88);
            border: 1px solid rgba(24, 32, 40, 0.08);
            border-radius: 18px;
            padding: 0.95rem 1rem;
        }}
        .fleet-card {{
            background: rgba(255,250,240,0.92);
            border: 1px solid rgba(24, 32, 40, 0.08);
            border-radius: 18px;
            padding: 1rem 1rem 0.9rem 1rem;
            margin-bottom: 0.8rem;
            min-height: 165px;
        }}
        .fleet-card h4 {{ margin: 0.55rem 0 0.2rem 0; }}
        .fleet-card p {{ margin: 0.2rem 0; color: {COLOR_PALETTE['muted']}; font-size: 0.92rem; }}
        .metric-label {{ font-size: 0.8rem; color: {COLOR_PALETTE['muted']}; text-transform: uppercase; letter-spacing: 0.05em; }}
        .metric-value {{ font-size: 1.5rem; font-weight: 700; color: {COLOR_PALETTE['ink']}; }}
        .metric-note {{ font-size: 0.85rem; color: {COLOR_PALETTE['muted']}; }}
        @media (max-width: 900px) {{
            .metric-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    """Serialize a DataFrame for download actions."""
    return frame.to_csv(index=False).encode("utf-8")


def filter_frame_by_window(frame: pd.DataFrame, timestamp_column: str, hours: float) -> pd.DataFrame:
    """Filter a DataFrame to a trailing time window based on its latest timestamp."""
    if frame.empty or hours <= 0:
        return frame.copy()
    series = pd.to_datetime(frame[timestamp_column], format="mixed", utc=True)
    latest_timestamp = series.max()
    window_start = latest_timestamp - pd.Timedelta(hours=hours)
    filtered = frame.loc[series >= window_start].copy()
    return cast(pd.DataFrame, filtered)


def summarize_devices_from_history(history: pd.DataFrame, reference: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build fleet rollups from the currently visible telemetry window."""
    if history.empty:
        return pd.DataFrame(
            {
                "device_id": [],
                "sample_count": [],
                "avg_health_score": [],
                "max_temperature": [],
                "last_recorded_at": [],
                "anomaly_count": [],
                "health_band": [],
            }
        )

    grouped = history.groupby("device_id", as_index=False).agg(
        sample_count=("device_id", "size"),
        avg_health_score=("health_score", "mean"),
        max_temperature=("temperature", "max"),
        last_recorded_at=("timestamp", "max"),
        anomaly_count=("anomaly_flag", "sum"),
    )
    summary = cast(pd.DataFrame, grouped).sort_values(by="last_recorded_at", ascending=False)
    summary["avg_health_score"] = summary["avg_health_score"].round(2)
    summary["max_temperature"] = summary["max_temperature"].round(2)
    summary["health_band"] = summary["avg_health_score"].apply(classify_health_band)
    return merge_device_metadata(cast(pd.DataFrame, summary), reference if reference is not None else pd.DataFrame())


def merge_device_metadata(summary: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Merge device metadata such as status and maintenance timestamps into windowed summaries."""
    if summary.empty:
        return summary
    if reference.empty:
        enriched = summary.copy()
        enriched["device_name"] = enriched["device_id"]
        enriched["location"] = "Unknown"
        enriched["status"] = "active"
        enriched["last_maintenance_at"] = pd.NaT
        return enriched

    metadata_columns = ["device_id", "device_name", "location", "status", "last_maintenance_at"]
    merged = summary.merge(reference[metadata_columns], on="device_id", how="left")
    merged["device_name"] = merged["device_name"].fillna(merged["device_id"])
    merged["location"] = merged["location"].fillna("Unknown")
    merged["status"] = merged["status"].fillna("active")
    return cast(pd.DataFrame, merged)


def status_style(status: str) -> tuple[str, str]:
    """Map a device status to a badge class and display label."""
    normalized = status.strip().lower()
    if normalized in {"active", "healthy", "stable"}:
        return "status-good", "Active"
    if normalized in {"maintenance_review", "maintenance", "inspection"}:
        return "status-maintenance", "Maintenance"
    if normalized in {"watch", "warning"}:
        return "status-warn", normalized.replace("_", " ").title()
    return "status-alert", normalized.replace("_", " ").title() or "Alert"


def status_color(status: str) -> str:
    """Map a device status to a chart color."""
    badge_class, _ = status_style(status)
    if badge_class == "status-good":
        return COLOR_PALETTE["good"]
    if badge_class == "status-maintenance":
        return COLOR_PALETTE["accent"]
    if badge_class == "status-warn":
        return COLOR_PALETTE["warn"]
    return COLOR_PALETTE["alert"]


def format_status_duration(status_since: Any) -> str:
    """Render a friendly elapsed duration for the current device status."""
    if status_since is None:
        return "Duration unavailable"
    text_value = str(status_since)
    if text_value in {"", "NaT", "None", "nan"}:
        return "Duration unavailable"
    start = pd.to_datetime(text_value, format="mixed", utc=True)
    delta = pd.Timestamp.now(tz="UTC") - start
    minutes = max(int(delta.total_seconds() // 60), 0)
    if minutes < 60:
        return f"{minutes} min"
    hours, rem_minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {rem_minutes}m"
    days, rem_hours = divmod(hours, 24)
    return f"{days}d {rem_hours}h"


def render_fleet_status_cards(devices: pd.DataFrame) -> None:
    """Render fleet device status cards with badges and maintenance context."""
    if devices.empty:
        st.info("No fleet devices are available in the current time window.")
        return

    columns = st.columns(min(3, len(devices)))
    for index, (_, row) in enumerate(devices.iterrows()):
        badge_class, badge_label = status_style(str(row.get("status", "active")))
        maintenance_value = cast(Any, row.get("last_maintenance_at"))
        status_since_value = cast(Any, row.get("status_since"))
        maintenance_text = "No maintenance logged"
        maintenance_value_text = "" if maintenance_value is None else str(maintenance_value)
        if maintenance_value_text not in {"", "NaT", "None", "nan"}:
            maintenance_text = pd.to_datetime(maintenance_value_text, format="mixed", utc=True).strftime("%Y-%m-%d %H:%M:%S")
        last_recorded_at = pd.to_datetime(cast(Any, row["last_recorded_at"]), format="mixed", utc=True).strftime("%Y-%m-%d %H:%M:%S")
        duration_text = format_status_duration(status_since_value)
        with columns[index % len(columns)]:
            st.markdown(
                f"""
                <div class="fleet-card">
                    <span class="status-chip {badge_class}">{badge_label}</span>
                    <h4>{row.get('device_name', row['device_id'])}</h4>
                    <p><strong>{row['device_id']}</strong> · {row.get('location', 'Unknown')}</p>
                    <p>Health: <strong>{float(row['avg_health_score']):.2f}</strong> · Alerts: <strong>{int(row['anomaly_count'])}</strong></p>
                    <p>Status duration: <strong>{duration_text}</strong></p>
                    <p>Last telemetry: <strong>{last_recorded_at}</strong></p>
                    <p>Last maintenance: <strong>{maintenance_text}</strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"Open {row['device_id']}",
                key=f"fleet_card_open_{row['device_id']}",
                width="stretch",
            ):
                st.session_state["monitoring_scope"] = str(row["device_id"])
                st.rerun()


def build_selected_payload(
    selected_device: str,
    fallback_payload: dict[str, object],
    history: pd.DataFrame,
    devices: pd.DataFrame,
) -> dict[str, object]:
    """Create the payload used by the hero cards and top-level charts.

    Fleet scope uses aggregated values, while device scope uses the latest
    visible sample for the selected device.
    """
    if selected_device == FLEET_LABEL:
        fallback_health = float(cast(float, fallback_payload["health_score"]))
        fleet_health = float(devices["avg_health_score"].mean()) if not devices.empty else fallback_health
        fleet_anomalies = int(devices["anomaly_count"].sum()) if not devices.empty else 0
        latest_timestamp = (
            devices["last_recorded_at"].max().strftime("%Y-%m-%d %H:%M:%S")
            if not devices.empty
            else str(fallback_payload["timestamp"])
        )
        metrics = cast(dict[str, float], fallback_payload["metrics"])
        return {
            "device_id": FLEET_LABEL,
            "timestamp": latest_timestamp,
            "metrics": metrics,
            "health_score": round(fleet_health, 2),
            "anomaly_flag": fleet_anomalies,
        }

    if history.empty:
        return fallback_payload

    device_history = history[history["device_id"] == selected_device]
    if device_history.empty:
        return fallback_payload

    latest_row = device_history.iloc[-1]
    return {
        "device_id": str(latest_row["device_id"]),
        "timestamp": latest_row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": {
            "temperature": float(latest_row["temperature"]),
            "vibration": float(latest_row["vibration"]),
            "current": float(latest_row["current"]),
        },
        "health_score": float(latest_row["health_score"]),
        "anomaly_flag": int(latest_row["anomaly_flag"]),
    }


def build_metrics_chart(metrics: dict[str, float]) -> go.Figure:
    """Render the current device metrics as a compact bar chart."""
    limits = {"temperature": 65.0, "vibration": 5.0, "current": 12.0}
    colors = [
        COLOR_PALETTE["warn"] if metrics[name] / limits[name] > 0.8 else COLOR_PALETTE["accent"]
        for name in metrics
    ]
    figure = go.Figure(
        go.Bar(
            x=[name.title() for name in metrics],
            y=list(metrics.values()),
            marker_color=colors,
            text=[f"{value:.2f}" for value in metrics.values()],
            textposition="outside",
        )
    )
    figure.update_layout(
        title="Live Sensor Load",
        xaxis_title="Metric",
        yaxis_title="Reading",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return figure


def build_health_gauge(score: float) -> go.Figure:
    """Render the equipment health score as a radial gauge."""
    color = COLOR_PALETTE["good"] if score >= 85 else COLOR_PALETTE["warn"] if score >= 70 else COLOR_PALETTE["alert"]
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": " /100"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "bgcolor": "rgba(0,0,0,0)",
                "steps": [
                    {"range": [0, 70], "color": "rgba(184, 50, 69, 0.18)"},
                    {"range": [70, 85], "color": "rgba(199, 119, 0, 0.16)"},
                    {"range": [85, 100], "color": "rgba(47, 133, 90, 0.14)"},
                ],
            },
        )
    )
    figure.update_layout(
        title="Equipment Health",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return figure


def build_history_chart(history: pd.DataFrame, selected_device: str) -> go.Figure:
    """Render trends for a single device or the whole fleet."""
    figure = go.Figure()
    if history.empty:
        return figure

    if selected_device == FLEET_LABEL:
        for device_id in history["device_id"].dropna().unique():
            device_frame = history[history["device_id"] == device_id]
            figure.add_trace(
                go.Scatter(
                    x=device_frame["timestamp"],
                    y=device_frame["health_score"],
                    name=str(device_id),
                    mode="lines+markers",
                )
            )
        figure.update_layout(
            title="Fleet Health Timeline",
            xaxis_title="Timestamp",
            yaxis_title="Health Score",
            yaxis={"range": [0, 100]},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.55)",
            legend={"orientation": "h", "y": 1.1},
            margin={"l": 20, "r": 20, "t": 60, "b": 20},
        )
        return figure

    figure.add_trace(
        go.Scatter(
            x=history["timestamp"],
            y=history["temperature"],
            name="Temperature",
            line={"color": COLOR_PALETTE["accent"], "width": 3},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=history["timestamp"],
            y=history["vibration"],
            name="Vibration",
            line={"color": COLOR_PALETTE["warn"], "width": 2},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=history["timestamp"],
            y=history["current"],
            name="Current",
            line={"color": "#2d7d64", "width": 2},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=history["timestamp"],
            y=history["health_score"],
            name="Health Score",
            yaxis="y2",
            line={"color": COLOR_PALETTE["alert"], "dash": "dash", "width": 2},
        )
    )
    figure.update_layout(
        title="Telemetry and Health Trend",
        xaxis_title="Timestamp",
        yaxis_title="Sensor Values",
        yaxis2={"title": "Health Score", "overlaying": "y", "side": "right", "range": [0, 100]},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.55)",
        legend={"orientation": "h", "y": 1.1},
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return figure


def build_band_chart(history: pd.DataFrame) -> go.Figure:
    """Render the count of samples in each health severity band."""
    figure = go.Figure()
    if history.empty:
        return figure
    counts = history["health_band"].value_counts().reindex(["Stable", "Watch", "Alert"], fill_value=0)
    figure.add_trace(
        go.Bar(
            x=list(counts.index),
            y=list(counts.values),
            marker_color=[COLOR_PALETTE["good"], COLOR_PALETTE["warn"], COLOR_PALETTE["alert"]],
        )
    )
    figure.update_layout(
        title="Operational Severity Mix",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.55)",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return figure


def build_device_health_chart(devices: pd.DataFrame) -> go.Figure:
    """Render fleet average health by device."""
    figure = go.Figure()
    if devices.empty:
        return figure
    ranked = devices.sort_values(by="avg_health_score", ascending=True)
    colors = [status_color(str(status)) for status in ranked["status"]]
    figure.add_trace(
        go.Bar(
            x=ranked["avg_health_score"],
            y=ranked["device_id"],
            orientation="h",
            marker_color=colors,
            text=[f"{value:.2f}" for value in ranked["avg_health_score"]],
            textposition="outside",
        )
    )
    figure.update_layout(
        title="Fleet Average Health by Device",
        xaxis_title="Average Health Score",
        yaxis_title="Device",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.55)",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return figure


def render_hero(payload: dict[str, object], history: pd.DataFrame, selected_device: str) -> None:
    """Render the top monitoring summary shown first during a demo."""
    payload_score = payload.get("health_score", 0.0)
    payload_anomaly = payload.get("anomaly_flag", 0)
    score = float(cast(float, payload_score))
    anomaly_flag = int(cast(int, payload_anomaly))
    band = classify_health_band(score)
    css_class = "status-good" if band == "Stable" else "status-warn" if band == "Watch" else "status-alert"
    anomaly_count = int(history["anomaly_flag"].sum()) if not history.empty else 0
    sample_count = len(history)
    scope_label = "fleet" if selected_device == FLEET_LABEL else f"device {payload['device_id']}"

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="status-chip {css_class}">{band}</div>
            <h1 style="margin:0.55rem 0 0.2rem 0;">SmartTool-Link Live Monitor</h1>
            <p style="margin:0; color:{COLOR_PALETTE['muted']};">
                Monitoring <strong>{scope_label}</strong> with the latest visible sample at <strong>{payload['timestamp']}</strong>.
                Current anomaly count in scope is <strong>{anomaly_count}</strong> across <strong>{sample_count}</strong> recent samples.
            </p>
            <div class="metric-strip">
                <div class="metric-card"><div class="metric-label">Health Score</div><div class="metric-value">{score:.2f}</div><div class="metric-note">Calculated from live thresholds</div></div>
                <div class="metric-card"><div class="metric-label">Samples</div><div class="metric-value">{sample_count}</div><div class="metric-note">Visible telemetry points</div></div>
                <div class="metric-card"><div class="metric-label">Peak Temperature</div><div class="metric-value">{(history['temperature'].max() if not history.empty else 0.0):.2f}</div><div class="metric-note">Recent observation window</div></div>
                <div class="metric-card"><div class="metric-label">Anomaly Markers</div><div class="metric-value">{anomaly_flag if selected_device != FLEET_LABEL else anomaly_count}</div><div class="metric-note">Flagged operating events</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Launch the Streamlit monitoring cockpit and wire up its controls."""
    st.set_page_config(page_title="SmartTool-Link Dashboard", layout="wide")
    apply_dashboard_theme()

    initial_history = load_recent_history()
    initial_devices = load_device_frame()
    anomaly_profiles = list_anomaly_profiles()
    anomaly_options = list(anomaly_profiles.keys())
    simulated_devices = [str(profile.get("device_id", "tool-001")) for profile in list_device_profiles()]

    device_options = [FLEET_LABEL]
    if not initial_devices.empty:
        device_options.extend(initial_devices["device_id"].astype(str).tolist())
    elif not initial_history.empty:
        device_options.extend(sorted(initial_history["device_id"].astype(str).unique().tolist()))

    if "monitoring_scope" not in st.session_state or str(st.session_state["monitoring_scope"]) not in device_options:
        st.session_state["monitoring_scope"] = FLEET_LABEL

    with st.sidebar:
        st.header("Control Deck")
        selected_device = st.selectbox("Monitoring scope", options=device_options, key="monitoring_scope")
        selected_window = st.selectbox("Time window", options=list(TIME_WINDOW_OPTIONS.keys()), index=2)
        selected_refresh = st.selectbox("Auto refresh", options=list(AUTO_REFRESH_OPTIONS.keys()), index=1)
        selected_alert_filter = st.selectbox("Alert filter", options=list(ALERT_FILTER_OPTIONS.keys()), index=0)
        if st.button("Refresh now", width="stretch"):
            st.rerun()
        st.caption("Switch between fleet-wide monitoring and individual device telemetry.")

        default_targets = simulated_devices if selected_device == FLEET_LABEL else [selected_device]
        valid_default_targets = [device_id for device_id in default_targets if device_id in simulated_devices]
        st.divider()
        st.subheader("Simulation Lab")
        with st.form("simulation_lab_form", clear_on_submit=False):
            selected_scenario = st.selectbox(
                "Scenario",
                options=anomaly_options,
                format_func=lambda key: str(anomaly_profiles.get(key, {}).get("label", key)),
            )
            injection_mode = st.selectbox(
                "Injection mode",
                options=["Burst", "Continuous fault"],
                index=0,
            )
            target_devices = st.multiselect(
                "Target devices",
                options=simulated_devices,
                default=valid_default_targets or simulated_devices[:1],
            )
            sample_burst = st.slider(
                "Sample burst" if injection_mode == "Burst" else "Continuous samples",
                min_value=1 if injection_mode == "Burst" else 3,
                max_value=5 if injection_mode == "Burst" else 20,
                value=2 if injection_mode == "Burst" else 8,
            )
            cadence_seconds = st.slider(
                "Cadence seconds",
                min_value=1,
                max_value=60,
                value=1 if injection_mode == "Burst" else 10,
            )
            st.caption(str(anomaly_profiles.get(selected_scenario, {}).get("description", "")))
            simulate_submitted = st.form_submit_button("Inject scenario", width="stretch")

        if simulate_submitted:
            stored = inject_simulated_payloads(
                selected_scenario,
                device_ids=target_devices or simulated_devices,
                sample_count=int(sample_burst),
                sample_interval_seconds=int(cadence_seconds),
                continuous=injection_mode == "Continuous fault",
            )
            st.success(
                f"Injected {len(stored)} telemetry event(s) for scenario '{selected_scenario}' in {injection_mode.lower()} mode."
            )
            st.rerun()
    time_window_hours = TIME_WINDOW_OPTIONS[selected_window]
    auto_refresh_seconds = AUTO_REFRESH_OPTIONS[selected_refresh]

    sidebar_history = filter_frame_by_window(load_recent_history(), "timestamp", time_window_hours)
    sidebar_alerts = filter_alerts_by_state(
        filter_frame_by_window(load_alert_frame(), "timestamp", time_window_hours),
        selected_alert_filter,
    )
    sidebar_maintenance = filter_frame_by_window(load_maintenance_frame(), "created_at", time_window_hours)
    sidebar_devices = summarize_devices_from_history(sidebar_history, initial_devices)

    with st.sidebar:
        st.caption(f"Window: {selected_window}")
        if auto_refresh_seconds > 0:
            st.caption(f"Auto refresh every {auto_refresh_seconds} seconds")
        else:
            st.caption("Auto refresh is disabled")

        if not sidebar_history.empty:
            st.download_button(
                "Export telemetry CSV",
                data=to_csv_bytes(sidebar_history.copy()),
                file_name="smarttool_telemetry_history.csv",
                mime="text/csv",
                width="stretch",
            )
        if not sidebar_alerts.empty:
            st.download_button(
                "Export alerts CSV",
                data=to_csv_bytes(sidebar_alerts.copy()),
                file_name="smarttool_alerts.csv",
                mime="text/csv",
                width="stretch",
            )
        if not sidebar_devices.empty:
            st.download_button(
                "Export fleet summary CSV",
                data=to_csv_bytes(sidebar_devices.copy()),
                file_name="smarttool_fleet_summary.csv",
                mime="text/csv",
                width="stretch",
            )
        if not sidebar_maintenance.empty:
            st.download_button(
                "Export maintenance CSV",
                data=to_csv_bytes(sidebar_maintenance.copy()),
                file_name="smarttool_maintenance_logs.csv",
                mime="text/csv",
                width="stretch",
            )

    def render_dashboard_body() -> None:
        """Render the main dashboard body for the current filter state."""
        latest_payload = load_latest_telemetry()
        history = filter_frame_by_window(load_recent_history(), "timestamp", time_window_hours)
        alerts = filter_alerts_by_state(
            filter_frame_by_window(load_alert_frame(), "timestamp", time_window_hours),
            selected_alert_filter,
        )
        maintenance = filter_frame_by_window(load_maintenance_frame(), "created_at", time_window_hours)
        devices = summarize_devices_from_history(history, load_device_frame())

        filtered_history = history.copy() if selected_device == FLEET_LABEL else history.loc[history["device_id"] == selected_device].copy()
        filtered_history = cast(pd.DataFrame, filtered_history)
        display_history = filtered_history if not filtered_history.empty else history
        display_history = cast(pd.DataFrame, display_history)
        filtered_alerts = alerts.copy() if selected_device == FLEET_LABEL else alerts.loc[alerts["device_id"] == selected_device].copy()
        filtered_alerts = cast(pd.DataFrame, filtered_alerts)
        filtered_maintenance = maintenance.copy() if selected_device == FLEET_LABEL else maintenance.loc[maintenance["device_id"] == selected_device].copy()
        filtered_maintenance = cast(pd.DataFrame, filtered_maintenance)
        active_payload = build_selected_payload(selected_device, latest_payload, history, devices)
        active_metrics = cast(dict[str, float], active_payload["metrics"])

        render_hero(active_payload, display_history, selected_device)

        if selected_device != FLEET_LABEL:
            if st.button("Back to Fleet Overview", key="back_to_fleet_overview", width="stretch"):
                st.session_state["monitoring_scope"] = FLEET_LABEL
                st.rerun()

        top_left, top_mid, top_right = st.columns([1.05, 1.3, 1.25])
        top_left.plotly_chart(build_health_gauge(float(cast(float, active_payload["health_score"]))), width="stretch")
        if selected_device == FLEET_LABEL:
            top_mid.plotly_chart(build_device_health_chart(devices), width="stretch")
        else:
            top_mid.plotly_chart(build_metrics_chart(active_metrics), width="stretch")
        top_right.plotly_chart(build_band_chart(display_history), width="stretch")

        st.plotly_chart(build_history_chart(display_history, selected_device), width="stretch")

        if history.empty:
            st.info("No telemetry falls inside the selected time window yet. Expand the window or run the processor again.")
            return

        operations, fleet_view, alert_desk, maintenance_log, raw = st.tabs(
            ["Operations View", "Fleet View", "Alert Desk", "Maintenance Log", "Raw Snapshot"]
        )

        with operations:
            display_frame = display_history.copy()
            display_frame["timestamp"] = pd.to_datetime(display_frame["timestamp"], format="mixed", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(display_frame, width="stretch", hide_index=True)

        with fleet_view:
            if devices.empty:
                st.info("Fleet rollups will appear after telemetry from at least one device is stored in the active time window.")
            else:
                render_fleet_status_cards(devices)
                fleet_frame = devices.copy()
                fleet_frame["last_recorded_at"] = pd.to_datetime(fleet_frame["last_recorded_at"], format="mixed", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
                if "last_maintenance_at" in fleet_frame.columns:
                    fleet_frame["last_maintenance_at"] = pd.to_datetime(fleet_frame["last_maintenance_at"], format="mixed", utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
                if "status_since" in fleet_frame.columns:
                    fleet_frame["status_duration"] = fleet_frame["status_since"].apply(format_status_duration)
                    fleet_frame["status_since"] = pd.to_datetime(fleet_frame["status_since"], format="mixed", utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
                st.dataframe(fleet_frame, width="stretch", hide_index=True)
                st.plotly_chart(build_device_health_chart(devices), width="stretch")

        with alert_desk:
            alert_sources = filtered_alerts if not filtered_alerts.empty else alerts
            device_choices: list[str] = []
            if not alert_sources.empty:
                device_choices = sorted(alert_sources["device_id"].astype(str).unique().tolist())
            elif selected_device != FLEET_LABEL:
                device_choices = [selected_device]
            else:
                device_choices = sorted([option for option in device_options if option != FLEET_LABEL])

            left_col, right_col = st.columns([1.4, 1.0])
            with left_col:
                if alert_sources.empty:
                    st.success(f"No alerts match the '{selected_alert_filter}' filter in the current time window.")
                else:
                    st.warning(
                        f"Showing {len(alert_sources)} alert event(s) for filter '{selected_alert_filter}' from the telemetry store."
                    )
                    alert_frame = alert_sources.copy()
                    alert_frame["timestamp"] = pd.to_datetime(alert_frame["timestamp"], format="mixed", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
                    st.dataframe(alert_frame, width="stretch", hide_index=True)

            with right_col:
                st.subheader("Acknowledge / Log Work")
                with st.form("maintenance_log_form", clear_on_submit=False):
                    ack_device = st.selectbox(
                        "Device",
                        options=device_choices if device_choices else ["tool-001"],
                        index=0,
                    )
                    event_type = st.selectbox(
                        "Event Type",
                        options=["ACK_ALERT", "INSPECTION", "MAINTENANCE_COMPLETE", "RETURN_TO_SERVICE"],
                        index=0,
                    )
                    description = st.text_area(
                        "Note",
                        value="Investigating anomaly and scheduling maintenance review.",
                        height=110,
                    )
                    submitted = st.form_submit_button("Save maintenance event", width="stretch")

                if submitted:
                    saved = create_maintenance_log(str(ack_device), str(event_type), description.strip())
                    st.success(
                        f"Logged {saved['event_type']} for {saved['device_id']} and set status to {saved['status']}."
                    )
                    st.rerun()

        with maintenance_log:
            maintenance_frame = filtered_maintenance if not filtered_maintenance.empty else maintenance
            if maintenance_frame.empty:
                st.info("No maintenance or acknowledgement events have been recorded in the active time window yet.")
            else:
                display_maintenance = maintenance_frame.copy()
                display_maintenance["created_at"] = pd.to_datetime(display_maintenance["created_at"], format="mixed", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
                st.dataframe(display_maintenance, width="stretch", hide_index=True)

        with raw:
            st.json(active_payload)

    if auto_refresh_seconds > 0:
        @st.fragment(run_every=f"{auto_refresh_seconds}s")
        def auto_refresh_fragment() -> None:
            render_dashboard_body()

        auto_refresh_fragment()
    else:
        render_dashboard_body()


if __name__ == "__main__":
    main()
