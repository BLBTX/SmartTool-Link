from __future__ import annotations

import argparse
import importlib
import json
from threading import Event
from typing import Any
from urllib.parse import urlparse

from ..storage.sqlite_store import load_json_config
from ..storage.sqlite_store import persist_telemetry
from .simulator import build_sample_payloads


def load_mqtt_library() -> Any:
    """Load the paho MQTT library only when MQTT mode is used."""
    try:
        mqtt_library = importlib.import_module("paho.mqtt.client")
    except ModuleNotFoundError as error:  # pragma: no cover - depends on runtime env
        raise ModuleNotFoundError(
            "paho-mqtt is not installed. Run 'pip install -r app/requirements.txt'."
        ) from error
    return mqtt_library


def create_mqtt_client(client_id: str) -> Any:
    """Create a paho client that works across current callback APIs."""
    mqtt = load_mqtt_library()

    try:
        return mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
    except (AttributeError, TypeError):
        return mqtt.Client(client_id=client_id)


def parse_broker_uri(broker_uri: str) -> tuple[str, int]:
    """Extract MQTT host and port settings from a broker URI."""
    parsed = urlparse(broker_uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or 1883
    return host, port


def process_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize and store one telemetry payload."""
    stored = persist_telemetry(payload)
    print(json.dumps(stored, indent=2))
    return stored


def run_sample_once() -> list[dict[str, Any]]:
    """Generate and persist one local sample batch."""
    stored_messages = []
    for payload in build_sample_payloads():
        stored_messages.append(process_payload(payload))
    return stored_messages


def run_mqtt_listener(timeout_seconds: int, max_messages: int) -> list[dict[str, Any]]:
    """Subscribe to MQTT telemetry and persist a bounded number of messages."""
    mqtt = load_mqtt_library()

    mqtt_config = load_json_config("config/mqtt/mqtt.json", "config/mqtt/mqtt.example.json")
    host, port = parse_broker_uri(str(mqtt_config.get("broker_uri", "tcp://localhost:1883")))
    topic = str(mqtt_config.get("topic_telemetry", "smarttool/devices/telemetry"))
    qos = int(mqtt_config.get("qos", 1))
    client_id = str(
        mqtt_config.get(
            "processor_client_id",
            mqtt_config.get("client_id", "smarttool-link-gateway") + "-processor",
        )
    )

    done = Event()
    stored_messages: list[dict[str, Any]] = []
    callback_errors: list[Exception] = []

    client = create_mqtt_client(client_id)

    def on_connect(mqtt_client: Any, _userdata: object, _flags: object, _reason_code: object, _properties: object = None) -> None:
        mqtt_client.subscribe(topic, qos=qos)

    def on_message(_client: Any, _userdata: object, message: Any) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            stored_messages.append(process_payload(payload))
            if len(stored_messages) >= max_messages:
                done.set()
        except Exception as error:  # pragma: no cover - runtime callback safety
            callback_errors.append(error)
            done.set()

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, keepalive=30)
    client.loop_start()

    try:
        if not done.wait(timeout_seconds):
            raise TimeoutError(
                f"No MQTT telemetry received on topic '{topic}' within {timeout_seconds} seconds."
            )
        if callback_errors:
            raise callback_errors[0]
        return stored_messages
    finally:
        client.loop_stop()
        client.disconnect()


def build_parser() -> argparse.ArgumentParser:
    """Define CLI options for sample and MQTT-backed processing modes."""
    parser = argparse.ArgumentParser(description="SmartTool-Link telemetry processor")
    parser.add_argument("--mode", choices=("sample", "mqtt"), default="sample")
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--max-messages", type=int, default=1)
    parser.add_argument("--no-fallback-sample", action="store_true")
    return parser


def main() -> None:
    """Run the processor in sample mode or MQTT ingestion mode."""
    args = build_parser().parse_args()

    if args.mode == "sample":
        run_sample_once()
        return

    try:
        stored_messages = run_mqtt_listener(args.timeout_seconds, args.max_messages)
        print(f"Stored {len(stored_messages)} MQTT message(s).")
    except Exception as error:
        if args.no_fallback_sample:
            raise
        print(f"MQTT ingest unavailable, falling back to sample mode: {error}")
        run_sample_once()


if __name__ == "__main__":
    main()
