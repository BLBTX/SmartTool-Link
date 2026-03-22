# SmartTool-Link 项目理解说明 / Project Reading Guide

## 1. 阅读目标 / Reading Goal

中文：这份说明用于帮助你快速理解 SmartTool-Link 的整体架构、核心模块调用关系、运行链路和展示重点。推荐先从“系统做什么”入手，再看“数据如何流动”，最后进入“具体代码如何实现”。

English: This guide helps you quickly understand SmartTool-Link's architecture, core module interactions, runtime flow, and presentation highlights. Start with what the system does, then follow how data flows, and finally inspect how the code implements each stage.

---

## 2. 推荐阅读顺序 / Recommended Reading Order

### Step 1. 先看项目定位 / Start with project positioning

- [`agents.md`](../../agents.md)
- [`README.md`](../../README.md)

中文：先读这两个文件，建立对项目目标、技术栈、五层架构和今日建设成果的整体认识。重点关注：项目解决什么问题、有哪些层、当前已经实现到什么程度。

English: Read these two files first to build a high-level understanding of the project goals, tech stack, five-layer architecture, and current implementation status. Focus on what problem it solves, what layers exist, and how far the implementation has progressed.

你要回答的问题 / Questions to answer:

- 这是一个什么系统？/ What kind of system is this?
- 端到端链路是什么？/ What is the end-to-end flow?
- 当前有哪些核心能力？/ What core capabilities already exist?

---

### Step 2. 再看配置入口 / Then inspect the configuration entry points

- [`config/app/app.example.json`](../../config/app/app.example.json)
- [`config/mqtt/mqtt.example.json`](../../config/mqtt/mqtt.example.json)
- [`config/database/database.example.json`](../../config/database/database.example.json)

中文：这些配置文件是理解系统行为的最快入口。你能从这里看到设备 ID、阈值、模拟设备、Broker、Topic、数据库路径、双写策略等关键运行参数。

English: These config files are the fastest way to understand how the system behaves. They show device IDs, thresholds, simulated devices, broker/topic settings, database paths, and dual-write strategy.

你要回答的问题 / Questions to answer:

- 系统默认如何运行？/ How does the system run by default?
- 告警阈值从哪里来？/ Where do alert thresholds come from?
- 多设备和异常模拟是怎么配置的？/ How are multi-device simulation and anomaly scenarios configured?

---

### Step 3. 看启动脚本，理解运行方式 / Read the run scripts to understand execution

- [`scripts/setup/init_db.py`](../../scripts/setup/init_db.py)
- [`scripts/run/start_broker.py`](../../scripts/run/start_broker.py)
- [`scripts/run/run_processor.py`](../../scripts/run/run_processor.py)
- [`scripts/run/run_dashboard.py`](../../scripts/run/run_dashboard.py)
- [`scripts/test/run_mqtt_e2e.py`](../../scripts/test/run_mqtt_e2e.py)
- [`scripts/test/run_cpp_gateway_e2e.py`](../../scripts/test/run_cpp_gateway_e2e.py)

中文：先理解脚本，再进源码，会更容易知道每个模块在系统里扮演什么角色。这些脚本直接体现了项目的启动顺序和验证路径。

English: Understanding the scripts before diving into the source makes it easier to see each module's role. These scripts directly reveal the startup order and verification path.

推荐理解顺序 / Suggested execution view:

1. 初始化数据库 / Initialize database
2. 启动 Broker / Start broker
3. 启动处理器 / Start processor
4. 启动看板 / Start dashboard
5. 跑端到端测试 / Run end-to-end tests

---

### Step 4. 阅读 C++ 网关主链路 / Read the C++ gateway main path

- [`src/main.cpp`](../../src/main.cpp)
- [`src/config/runtime_settings.cpp`](../../src/config/runtime_settings.cpp)
- [`src/device/simulator/device_simulator.cpp`](../../src/device/simulator/device_simulator.cpp)
- [`src/comm/serializer/telemetry_message.cpp`](../../src/comm/serializer/telemetry_message.cpp)
- [`src/comm/mqtt/mqtt_publisher.cpp`](../../src/comm/mqtt/mqtt_publisher.cpp)

中文：这一部分是“边缘侧”主链路。建议按“入口 -> 配置 -> 采样 -> 序列化 -> 发布”的顺序读。

English: This is the edge-side main path. Read it in the order of entry -> config -> sampling -> serialization -> publishing.

调用逻辑 / Call logic:

1. [`src/main.cpp`](../../src/main.cpp) 读取运行配置 / loads runtime settings
2. 创建 `MqttPublisher` / creates publisher
3. 创建 `DeviceSimulator` / creates device simulator
4. 注册温度、振动、电流传感器 / registers temperature, vibration, current sensors
5. 生成 `TelemetryMessage` / generates telemetry message
6. 转成 JSON / serializes to JSON
7. 发布到 MQTT / publishes to MQTT

---

### Step 5. 阅读 Python 处理链路 / Read the Python processing path

- [`app/processor/main.py`](../../app/processor/main.py)
- [`app/processor/simulator.py`](../../app/processor/simulator.py)
- [`app/analytics/health_score.py`](../../app/analytics/health_score.py)
- [`app/storage/sqlite_store.py`](../../app/storage/sqlite_store.py)
- [`app/storage/mysql_store.py`](../../app/storage/mysql_store.py)

中文：这一部分是“后端处理核心”。建议按“接收数据 -> 计算健康分 -> 判定异常 -> 写入存储”的顺序读。

English: This is the backend processing core. Read it in the order of receiving data -> calculating health score -> detecting anomalies -> persisting data.

调用逻辑 / Call logic:

1. `main.py` 决定走 sample 模式还是 mqtt 模式 / chooses sample or MQTT mode
2. `process_payload()` 调用统一存储入口 / calls the unified persistence path
3. `sqlite_store.py` 做数据标准化、阈值判定、健康评分 / normalizes data, applies thresholds, computes health
4. `persist_sqlite_telemetry()` 写入设备、遥测、心跳 / writes devices, telemetry, heartbeats
5. `mysql_store.py` 在启用双写时镜像写入 MySQL / mirrors writes to MySQL when enabled
6. `simulator.py` 负责生成正常/异常/连续异常样本 / generates normal, fault, and continuous-fault demo payloads

---

### Step 6. 阅读 Dashboard，理解展示与操作闭环 / Read the dashboard to understand visualization and operations

- [`app/dashboard/main.py`](../../app/dashboard/main.py)

中文：这个文件很大，但建议按“数据加载 -> 过滤控制 -> Fleet 视图 -> Alert Desk -> Maintenance Log -> Simulation Lab”的顺序阅读。

English: This file is large, so read it in the order of data loading -> filtering controls -> fleet view -> alert desk -> maintenance log -> simulation lab.

重点能力 / Key capabilities:

- Fleet 总览 / Fleet overview
- 单设备下钻 / Single-device drilldown
- 状态徽章 / Status badges
- 状态时长 / Status duration
- 告警筛选 / Alert filtering
- 维护记录 / Maintenance logging
- 时间窗口 / Time window
- 自动刷新 / Auto refresh
- 异常模拟 / Fault simulation

---

### Step 7. 最后回头看数据库结构 / Finally inspect the database schema

- [`sql/schema/init.sql`](../../sql/schema/init.sql)
- [`sql/schema/init_mysql.sql`](../../sql/schema/init_mysql.sql)
- [`sql/procedures/telemetry_mysql.sql`](../../sql/procedures/telemetry_mysql.sql)

中文：这一步适合在你已经理解业务之后再看。这样你会更清楚为什么有 `telemetry`、`device_heartbeats`、`maintenance_logs` 这些表，以及为什么 MySQL 还需要存储过程。

English: This step makes more sense after you already understand the business flow. You will better understand why tables such as `telemetry`, `device_heartbeats`, and `maintenance_logs` exist, and why MySQL uses stored procedures.

---

## 3. 一句话理解每个核心模块 / One-line Understanding of Each Core Module

- [`src/`](../../src/)：边缘侧采集与 MQTT 发布 / edge collection and MQTT publishing
- [`app/processor/`](../../app/processor/)：后端接收、解析、异常检测 / backend ingest, parsing, anomaly detection
- [`app/analytics/`](../../app/analytics/)：健康评分算法 / health scoring
- [`app/storage/`](../../app/storage/)：SQLite/MySQL 存储抽象 / storage abstraction for SQLite/MySQL
- [`app/dashboard/`](../../app/dashboard/)：展示、告警工作台、维护记录、模拟演示 / visualization, alert desk, maintenance workflow, simulation
- [`sql/`](../../sql/)：数据库初始化和过程逻辑 / schema and stored procedures
- [`scripts/`](../../scripts/)：启动、初始化、测试入口 / startup, setup, and test entry points
- [`config/`](../../config/)：运行参数中心 / central runtime configuration

---

## 4. 最快理解项目的 5 个问题 / 5 Fast Questions to Understand the Project

1. 数据从哪里来？/ Where does the data come from?
2. 数据怎么传？/ How is the data transmitted?
3. 异常怎么判定？/ How are anomalies detected?
4. 数据落到哪里？/ Where is data persisted?
5. 用户在哪里看到并处理告警？/ Where does the user view and handle alerts?

如果你能完整回答这 5 个问题，就已经理解了这个项目的核心。

If you can answer these five questions clearly, you already understand the core of this project.

---

## 5. 建议的实际阅读路线 / Suggested Practical Reading Route



1. [`agents.md`](../../agents.md)
2. [`README.md`](../../README.md)
3. [`config/app/app.example.json`](../../config/app/app.example.json)
4. [`scripts/run/run_processor.py`](../../scripts/run/run_processor.py)
5. [`src/main.cpp`](../../src/main.cpp)
6. [`src/device/simulator/device_simulator.cpp`](../../src/device/simulator/device_simulator.cpp)
7. [`app/processor/main.py`](../../app/processor/main.py)
8. [`app/storage/sqlite_store.py`](../../app/storage/sqlite_store.py)
9. [`app/dashboard/main.py`](../../app/dashboard/main.py)
10. [`sql/schema/init.sql`](../../sql/schema/init.sql)

---

## 6. 如果是做展示，优先讲这三条 / If You Are Presenting, Emphasize These Three Points

- 这是一个从设备到看板的完整闭环系统 / It is a full loop from device to dashboard
- 不仅能监控，还能做告警确认、维护记录和异常演示 / It supports not only monitoring but also alert handling, maintenance logging, and fault simulation
- 架构具备从本地 SQLite 到 MySQL 扩展、从模拟数据到真实 MQTT 联调的演进路径 / The architecture can evolve from local SQLite to MySQL, and from simulation to real MQTT end-to-end integration
