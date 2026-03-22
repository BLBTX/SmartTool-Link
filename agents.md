# SmartTool-Link: Industrial IoT Device Monitoring & Analysis Gateway

## 1. 项目概述 (Project Overview)
**SmartTool-Link** 是一个端到端的物联网（IoT）集成解决方案，旨在实现工业设备（如动力工具、传感器网络）的高可靠性数据采集、远程传输与实时分析。系统实现了从底层硬件仿真到边缘网关，再到后端数据持久化与可视化看板的完整闭环。

* **核心目标**：提供一套低延迟、可扩展的设备状态监控体系，支持预测性维护与实时故障告警。
* **应用领域**：生产线自动化监控、远程设备资产管理、传感器数据集成分析。

---

## 2. 技术架构 (Technical Architecture)

| 层级 | 核心技术 | 功能描述 |
| :--- | :--- | :--- |
| **感应层 (Sensing)** | **C++ 11/14** | 多传感器数据仿真，支持 I2C/SPI 协议逻辑封装。 |
| **传输层 (Transport)** | **MQTT (Paho)** | 异步非阻塞消息通信，支持 QoS 1 级别消息交付保障。 |
| **持久层 (Storage)** | **SQL (MySQL/SQLite)** | 结构化存储设备遥测数据，集成**存储过程 (Stored Procedures)** 优化高频查询。 |
| **处理层 (Processor)** | **Python 3.10** | 自动化数据解析、异常逻辑检测及复杂业务规则处理。 |
| **展示层 (Visualization)** | **Streamlit / Plotly** | 实时数据叙事（Data Storytelling），提供多维度交互式看板。 |

---

## 2.1 运行环境与兼容平台 (Runtime & Platform Support)

* **支持操作系统**：Windows 10/11、Ubuntu 18.04 ~ 22.04、macOS。
* **C++ 工具链**：要求支持 **C++14**；Windows 推荐 **MSVC / Visual Studio Build Tools 2022**，Linux/macOS 推荐 **GCC 9+** 或 **Clang 12+**。
* **构建系统**：推荐使用 **CMake 3.20+** 统一管理跨平台编译流程。
* **Python 环境**：要求 **Python 3.10**，推荐使用 **venv** 隔离依赖。
* **消息中间件**：推荐使用 **Mosquitto** 作为 MQTT Broker，便于在 Windows、Linux、macOS 上统一部署与调试。
* **数据库策略**：开发环境优先使用 **SQLite**，便于跨平台快速启动；生产或高并发场景可切换至 **MySQL**。

---

## 3. 核心功能模块 (Core Modules)

### 3.1 边缘采集引擎 (`/src/device/`)
* **硬件抽象层 (HAL)**：采用面向对象设计，通过 `BaseSensor` 基类抽象化传感器行为，支持动态加载温度、振动、电流等模拟插件。
* **异常注入逻辑**：内置工况模拟器，可人为触发“过载”、“过热”等异常状态，验证系统容错能力。

### 3.2 异步通信网关 (`/src/comm/`)
* **弹性连接**：实现自动重连逻辑（Auto-reconnect）与离线缓存机制，确保在网络抖动时数据不丢失。
* **数据序列化**：采用轻量级 JSON 格式进行数据封装，确保跨平台系统间的协议兼容性。

### 3.3 数据库逻辑组件 (`/sql/`)
* **性能优化**：通过 SQL 存储过程实现数据预聚合（Data Aggregation），减少应用层计算开销。
* **健康审计**：设计专用表结构记录设备心跳与维护日志，支持全生命周期追踪。

### 3.4 数据分析应用 (`/app/`)
* **健康评分系统**：基于 Python 开发的算法模块，根据振动频率与电流波动计算设备的“健康得分”。
* **自动化可视化**：动态生成实时曲线与历史趋势图表，辅助技术人员快速定位故障根源。

---

## 4. 关键实现细节 (Implementation Details)

### C++ 异步消息上报示例
```cpp
// 核心发布逻辑：非阻塞发送设备遥测数据
void DeviceGateway::publish_telemetry(const nlohmann::json& data) {
    auto msg = mqtt::make_message(TOPIC_TELEMETRY, data.dump());
    msg->set_qos(1); // 确保至少交付一次
    mqtt_client.publish(msg); 
}
```

---

## 5. 今日修改记录 (Today Build Log)

**日期**：2026-03-18

1. **补充运行环境说明**：在本文档中新增跨平台运行章节，明确支持 Windows 10/11、Ubuntu 18.04~22.04、macOS，并约定 C++14、CMake 3.20+、Python 3.10、Mosquitto、SQLite/MySQL 的基础要求。
2. **创建项目目录骨架**：建立 `src/`、`app/`、`sql/`、`config/`、`scripts/`、`tests/`、`docs/`、`data/` 等目录，并细分设备、通信、处理、看板、配置、测试、数据子目录。
3. **补齐 C++ 基线工程**：新增 `CMakeLists.txt`、`src/main.cpp`、传感器抽象/模拟器/MQTT 发布器/JSON 序列化等基础源码，使网关能够生成温度、振动、电流遥测数据。
4. **补齐 Python 基线工程**：新增 `app/requirements.txt`、健康评分模块、处理器入口、Streamlit 看板入口，以及 Python 包结构初始化文件。
5. **补齐数据库与配置基线**：新增 `sql/schema/init.sql`、`config/mqtt/mqtt.example.json`、`config/database/database.example.json`、`config/app/app.example.json`，形成 SQLite 优先的本地开发路径。
6. **为关键函数补头注释**：给 C++/Python 主要入口、序列化、发布、处理、展示函数补充说明性注释与 docstring，方便后续继续扩展。
7. **接入 `nlohmann/json` 与可切换 MQTT 实现**：C++ 构建改为优先使用 `nlohmann/json`，并增加 `SMARTTOOL_ENABLE_REAL_MQTT` 开关；默认保留本地 stub / CLI fallback，真实模式支持 Paho MQTT。
8. **处理链路接入 SQLite**：Python 处理器从仅生成本地 JSON，升级为写入 SQLite、心跳表、最新快照，并让 Dashboard 改为优先从 SQLite 读取最新值和历史趋势。
9. **新增运行脚本**：补充 `scripts/setup/init_db.py`、`scripts/run/run_processor.py`、`scripts/run/run_dashboard.py`，统一数据库初始化、处理器执行与看板启动方式。
10. **安装并验证 Python 运行依赖**：安装 `paho-mqtt`、`plotly`、`streamlit`、`mysql-connector-python` 等依赖，并完成处理器、看板、本地数据库链路验证。
11. **安装并接入 Mosquitto**：在本机安装 Mosquitto，新增 `config/mqtt/mosquitto.conf` 与 `scripts/run/start_broker.py`，形成可本地启动的 MQTT Broker。
12. **打通端到端 MQTT 流程**：新增 `scripts/test/run_mqtt_e2e.py` 与 `scripts/test/run_cpp_gateway_e2e.py`，验证 Python 发布/订阅链路，以及 `C++ Gateway -> MQTT -> Python Processor -> SQLite` 全链路。
13. **增强 C++ 网关配置加载**：新增 `src/config/runtime_settings.h` 与 `src/config/runtime_settings.cpp`，让网关从 `config/app/*.json` 与 `config/mqtt/*.json` 读取设备 ID、发布次数、采样间隔、Broker、Topic、Client ID、QoS 等配置。
14. **补齐 MySQL 基线能力**：新增 `sql/schema/init_mysql.sql`、`sql/procedures/telemetry_mysql.sql`、`scripts/setup/init_mysql.py`，支持 MySQL 表结构、存储过程和初始化脚本。
15. **实现 SQLite/MySQL 双写扩展**：新增 `app/storage/mysql_store.py`，让 Python 处理器在配置允许时可以把同一批处理后的遥测同时写入 SQLite 与 MySQL。
16. **升级 Dashboard 为监控驾驶舱**：将看板改造成包含英雄区、健康仪表盘、实时负载柱状图、Fleet 级设备健康对比、历史趋势图、Fleet 汇总表、Alert Desk 的多视图页面。
17. **增加多设备视图和导出能力**：看板侧边栏新增 Fleet/单设备切换，支持导出遥测历史 CSV、告警 CSV、Fleet 汇总 CSV。
18. **补充 Fleet 查询与告警查询接口**：在 SQLite 存储层新增设备汇总、最近告警、带 `device_id` 的历史查询，支撑多设备看板与告警面板。
19. **完善原生 Paho MQTT 构建链路**：修正 Paho 版本与 CMake FetchContent 逻辑，最终成功构建 `build-real-mqtt-4/Debug/smarttool_gateway.exe`，并验证原生 Paho MQTT 网关链路可正常写入 SQLite。
20. **修复 MQTT 客户端冲突问题**：为处理器增加独立 `processor_client_id`，避免与网关共用同一个 Client ID 导致 Broker 断开连接。
21. **支持阈值配置化**：将温度、振动、电流阈值从硬编码改为从 `config/app/app.example.json` 读取，统一影响健康评分与异常判定。
22. **支持多设备模拟数据生成**：Sample 模式改为按 `simulated_devices` 批量生成多台设备遥测，便于 Dashboard 展示 Fleet 差异和告警状态。
23. **补充文档说明**：同步更新 `readme.md`，记录构建模式、运行命令、双写选项、MySQL 过程、阈值配置、多设备模拟数据等内容。
24. **补充维护记录能力**：在 SQLite 存储层新增维护日志写入与查询接口，支持 `ACK_ALERT`、巡检、维护完成、恢复投产等事件，并同步更新设备状态。
25. **增强 Alert Desk 交互**：Dashboard 新增告警确认表单、维护日志视图和维护记录 CSV 导出能力，使告警处理闭环从只读展示升级为可操作工作台。
26. **增加时间窗口筛选能力**：Dashboard 新增最近 15 分钟、1 小时、6 小时、24 小时和最近样本集等时间窗口，所有趋势图、告警面板和维护日志均可按窗口聚焦查看。
27. **增加自动刷新控制**：Dashboard 侧边栏新增手动刷新与自动刷新选项，利用 Streamlit fragment 定时重绘页面，便于值守场景下持续观察设备状态变化。
28. **增加异常模拟开关**：新增可配置的 `anomaly_profiles` 和模拟器模块，支持通过 Dashboard 的 `Simulation Lab` 一键注入过热、过载、振动异常等样本，快速验证告警与维护流程。
29. **增加设备状态徽章展示**：让 SQLite 持久层在设备总表中维护 `active`、`warning`、`maintenance_review` 等状态，并在 Dashboard Fleet 视图中以状态卡片和带状态颜色的健康对比图进行展示。
30. **增加状态持续时长展示**：利用设备心跳和维护事件推导 `status_since`，并在 Fleet 状态卡片与汇总表中显示每台设备当前状态已持续的时间。
31. **增加 Fleet 视图下钻入口**：为 Fleet 状态卡片增加“打开设备视图”按钮，使值守人员可直接从 Fleet 总览跳转到指定设备的单机监控页面。
32. **增加连续异常注入模式**：扩展模拟器和 Dashboard `Simulation Lab`，支持以指定 cadence 连续注入多批异常样本，用于演示持续故障、长时间告警和状态时长变化。
33. **增加告警状态筛选能力**：为 Alert Desk 增加全部、未确认、已确认、已维护等筛选项，并根据维护事件对每条告警计算 `alert_state`，便于值守人员区分处理阶段。
34. **增加一键迁移脚本**：新增 `scripts/setup/quickstart.py` 及 Windows/Linux/macOS 包装脚本，可在新电脑上一键复制配置、创建虚拟环境、安装依赖、初始化数据库、可选构建网关并启动演示栈。
35. **补充新电脑依赖检查清单**：新增 `docs/setup/new-machine-dependency-checklist.md`，整理 Python、pip、Git、CMake、编译器、Mosquitto、MySQL 的检查项、验证命令和最小可运行条件，便于迁移前预检。
36. **补充展示用架构文档**：新增 `docs/architecture/project-architecture-mindmap.md`、`docs/architecture/executive-mindmap.md`、`docs/architecture/system-architecture-diagram.md`，用于项目汇报、架构说明和技术展示。
37. **补充 XMind 导入与调用逻辑脑图**：新增 `docs/architecture/xmind-import-architecture.md` 与 `docs/architecture/core-module-call-logic-mindmap.md`，分别用于 XMind 导入和核心模块调用关系展示。
38. **补充项目阅读与面试讲解材料**：新增 `docs/architecture/project-reading-guide-bilingual.md` 与 `docs/architecture/interview-presentation-script-bilingual.md`，方便做项目理解、面试讲解和双语展示准备。
39. **统一仓库 README 命名**：将项目说明统一为 `README.md`，避免 `README.md` 与 `readme.md` 在跨平台 Git 场景下产生命名冲突。
40. **完成 GitHub 仓库初始化与首次推送**：新增根目录 `.gitignore`、初始化本地 Git 仓库、合并远端初始提交，并成功推送到 `git@github.com:BLBTX/SmartTool-Link.git` 的 `main` 分支。

