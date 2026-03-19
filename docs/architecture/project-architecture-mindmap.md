# SmartTool-Link Project Architecture Mind Map

This file is prepared for demos and presentations.
You can preview it in any Markdown tool that supports Mermaid.

## Mind Map

```mermaid
mindmap
  root((SmartTool-Link))
    Project Goal
      Industrial IoT monitoring gateway
      End-to-end telemetry loop
      Predictive maintenance
      Real-time alerting
    Runtime Platforms
      Windows 10/11
      Ubuntu 18.04-22.04
      macOS
    Core Architecture
      Sensing Layer
        C++14
        BaseSensor abstraction
        Temperature sensor
        Vibration sensor
        Current sensor
        Device simulator
        Anomaly injection
      Transport Layer
        MQTT
        Paho MQTT
        Mosquitto broker
        QoS 1 delivery
        JSON telemetry payloads
        Reconnect strategy
      Processing Layer
        Python 3.10
        Telemetry processor
        Health scoring
        Threshold-based anomaly detection
        Sample generation
        Continuous fault simulation
      Storage Layer
        SQLite first
        MySQL optional
        Telemetry table
        Device heartbeats
        Maintenance logs
        Stored procedures
        Dual-write support
      Visualization Layer
        Streamlit dashboard
        Plotly charts
        Fleet overview
        Single-device drilldown
        Alert Desk
        Maintenance Log
        Simulation Lab
    Key Workflows
      Device telemetry flow
        Sensors
        C++ gateway
        MQTT broker
        Python processor
        SQLite or MySQL
        Dashboard
      Alert workflow
        Anomaly detected
        Alert appears
        Acknowledge alert
        Inspection event
        Maintenance complete
        Return to service
      Simulation workflow
        Burst injection
        Continuous injection
        Overheat
        Overload
        Vibration spike
        Power surge
    Dashboard Capabilities
      Hero status panel
      Health gauge
      Sensor load chart
      Fleet status cards
      Status duration
      Time window filter
      Auto refresh
      Alert state filter
      CSV export
    Project Structure
      src/
        device/
        comm/
        config/
      app/
        analytics/
        processor/
        storage/
        dashboard/
      sql/
        schema/
        procedures/
      config/
        app/
        mqtt/
        database/
      scripts/
        setup/
        run/
        test/
      docs/
      tests/
      data/
```

## End-to-End Flow

```mermaid
flowchart LR
    A[Sensors / Simulator] --> B[C++ Gateway]
    B --> C[MQTT Broker]
    C --> D[Python Processor]
    D --> E[(SQLite / MySQL)]
    E --> F[Streamlit Dashboard]
    F --> G[Alert Desk / Fleet View / Maintenance Log]
```

## Presentation Talking Points

- The project is a full industrial IoT loop from device simulation to dashboard operations.
- C++ focuses on edge collection and gateway publishing, while Python focuses on processing and visualization.
- MQTT decouples edge and backend, making the system extensible and resilient.
- SQLite gives a lightweight local development path, while MySQL supports future production scaling.
- The dashboard is not only visual; it also supports alerts, maintenance actions, filtering, exports, and simulation.
