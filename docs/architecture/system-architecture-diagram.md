# SmartTool-Link 系统架构图

适合技术汇报、答辩、项目说明书、系统设计文档。

## 正式架构框图

```mermaid
flowchart LR
    subgraph S1[感应层 Sensing]
        A1[温度传感器]
        A2[振动传感器]
        A3[电流传感器]
        A4[异常模拟器]
    end

    subgraph S2[边缘网关 Edge Gateway]
        B1[C++ Device Simulator]
        B2[BaseSensor / HAL]
        B3[Telemetry Serializer]
        B4[MQTT Publisher]
        B5[Runtime Settings]
    end

    subgraph S3[传输层 Transport]
        C1[Mosquitto Broker]
        C2[MQTT Topic]
        C3[QoS 1 Delivery]
    end

    subgraph S4[处理层 Processor]
        D1[Python Processor]
        D2[Health Score Engine]
        D3[Threshold Detection]
        D4[Simulation Engine]
    end

    subgraph S5[持久层 Storage]
        E1[(SQLite)]
        E2[(MySQL)]
        E3[telemetry]
        E4[device_heartbeats]
        E5[maintenance_logs]
        E6[Stored Procedures]
    end

    subgraph S6[展示层 Visualization]
        F1[Streamlit Dashboard]
        F2[Fleet View]
        F3[Device Drilldown]
        F4[Alert Desk]
        F5[Maintenance Log]
        F6[Simulation Lab]
    end

    subgraph S7[运行与配置 Runtime]
        G1[config/app]
        G2[config/mqtt]
        G3[config/database]
        G4[scripts/run]
        G5[scripts/test]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    B2 --> B1
    B5 --> B1
    B1 --> B3
    B3 --> B4
    B4 --> C1
    C1 --> C2
    C2 --> D1
    C3 --> D1
    D1 --> D2
    D1 --> D3
    D4 --> D1
    D1 --> E1
    D1 --> E2
    E1 --> E3
    E1 --> E4
    E1 --> E5
    E2 --> E6
    E1 --> F1
    E2 --> F1
    F1 --> F2
    F1 --> F3
    F1 --> F4
    F1 --> F5
    F1 --> F6
    G1 -.控制阈值/模拟参数.-> D1
    G2 -.控制Broker/Topic.-> B4
    G3 -.控制数据库连接.-> D1
    G4 -.启动网关/处理器/看板.-> F1
    G5 -.验证E2E链路.-> D1
```

## 数据流视角

```mermaid
sequenceDiagram
    participant Device as Sensors/Simulator
    participant Gateway as C++ Gateway
    participant Broker as MQTT Broker
    participant Processor as Python Processor
    participant DB as SQLite/MySQL
    participant Dashboard as Dashboard

    Device->>Gateway: 生成温度/振动/电流数据
    Gateway->>Broker: 发布 JSON 遥测消息
    Broker->>Processor: 转发 MQTT Telemetry
    Processor->>Processor: 健康评分 / 阈值判断
    Processor->>DB: 写入 telemetry / heartbeats / maintenance
    Dashboard->>DB: 查询最新状态 / 历史趋势 / 告警 / 维护记录
    Dashboard-->>User: 展示 Fleet 总览与单设备视图
```

## 展示建议

- 面向管理层：先用 `executive-mindmap.md`
- 面向技术评审：用本文件的“正式架构框图”
- 面向流程说明：用本文件的“数据流视角”

## 讲解顺序

- 先讲 5 层架构：采集、传输、处理、存储、展示
- 再讲端到端链路：C++ -> MQTT -> Python -> SQL -> Dashboard
- 最后讲项目亮点：多设备 Fleet、告警闭环、维护记录、异常模拟
