# Core Data Flow

## 核心结论

如果面试官问“这个项目最核心的数据流处理在哪”，可以这样回答：

- 采集与发送核心在 [`src/device/simulator/device_simulator.cpp`](src/device/simulator/device_simulator.cpp)
- 消息接收核心在 [`app/processor/main.py`](app/processor/main.py)
- 数据处理与落库核心在 [`app/storage/sqlite_store.py`](app/storage/sqlite_store.py)

其中，[`app/storage/sqlite_store.py`](app/storage/sqlite_store.py) 是整条后端处理链路里最核心的文件。

---

## 按数据流看关键文件

### 1. [`src/main.cpp`](src/main.cpp)

这是 C++ 网关入口。

它负责：

- 读取运行配置
- 创建 MQTT 发布器
- 创建设备模拟器
- 循环采样并发布遥测数据

如果你要从“系统是怎么启动的”开始讲，可以先打开这个文件。

---

### 2. [`src/device/simulator/device_simulator.cpp`](src/device/simulator/device_simulator.cpp)

这是设备侧采样核心。

它负责：

- 注册温度、振动、电流传感器
- 从各个传感器采样
- 组装成一条完整的遥测消息
- 调用 MQTT 发布逻辑

如果你要讲“设备数据是怎么产生的”，这个文件最关键。

---

### 3. [`src/comm/serializer/telemetry_message.cpp`](src/comm/serializer/telemetry_message.cpp)

这是遥测序列化核心。

它负责：

- 把 C++ 内存中的遥测结构转成 JSON
- 输出 `device_id`、`tick`、`timestamp`、`metrics` 等字段

这是“设备数据变成可传输消息”的关键一步。

---

### 4. [`src/comm/mqtt/mqtt_publisher.cpp`](src/comm/mqtt/mqtt_publisher.cpp)

这是 MQTT 发布核心。

它负责：

- 连接 MQTT Broker
- 通过原生 Paho MQTT 或 fallback 路径发布 JSON 消息

这是“边缘侧数据进入消息中间件”的关键文件。

---

### 5. [`app/processor/main.py`](app/processor/main.py)

这是 Python 处理器入口，也是消息接收核心。

它负责：

- 选择 `sample` 模式或 `mqtt` 模式
- 订阅 MQTT Topic
- 接收并解析 JSON 消息
- 调用统一处理入口 `process_payload()`

如果你要讲“消息到后端以后怎么继续处理”，这个文件一定要讲。

---

### 6. [`app/storage/sqlite_store.py`](app/storage/sqlite_store.py)

这是整个项目最核心的后端处理文件。

它负责：

- 标准化遥测数据
- 读取阈值配置
- 计算健康评分
- 判断是否异常
- 写入 SQLite
- 更新设备状态
- 生成最新快照
- 在启用时同步写入 MySQL

如果只选一个文件来代表“核心数据处理逻辑”，就是这个文件。

你可以直接这样说：

> 最核心的数据处理在 [`app/storage/sqlite_store.py`](app/storage/sqlite_store.py)，因为这里把原始遥测转换成了带健康评分、异常标记和设备状态的数据，并完成了最终持久化。

---

### 7. [`app/dashboard/main.py`](app/dashboard/main.py)

这是结果消费端。

它不负责原始数据处理，但负责：

- 从数据库读取最新遥测
- 读取历史趋势
- 读取 Fleet 汇总
- 读取告警和维护记录
- 展示成可交互 Dashboard

如果你要讲“处理结果最后怎么被用户看到”，就讲这个文件。

---

## 一条完整链路

可以把整个核心数据流概括成：

[`src/main.cpp`](src/main.cpp)
-> [`src/device/simulator/device_simulator.cpp`](src/device/simulator/device_simulator.cpp)
-> [`src/comm/serializer/telemetry_message.cpp`](src/comm/serializer/telemetry_message.cpp)
-> [`src/comm/mqtt/mqtt_publisher.cpp`](src/comm/mqtt/mqtt_publisher.cpp)
-> [`app/processor/main.py`](app/processor/main.py)
-> [`app/storage/sqlite_store.py`](app/storage/sqlite_store.py)
-> [`app/dashboard/main.py`](app/dashboard/main.py)

---

## 面试时最推荐展示的三个文件

如果时间有限，最推荐展示这三个文件：

1. [`src/device/simulator/device_simulator.cpp`](src/device/simulator/device_simulator.cpp)
   - 讲设备数据怎么产生
2. [`app/processor/main.py`](app/processor/main.py)
   - 讲后端怎么接收 MQTT 消息
3. [`app/storage/sqlite_store.py`](app/storage/sqlite_store.py)
   - 讲后端怎么做核心处理和落库

---

## 一句话回答模板

如果面试官直接问：**“你的核心数据流在哪个文件？”**

你可以回答：

> 项目的核心数据流是从 [`src/device/simulator/device_simulator.cpp`](src/device/simulator/device_simulator.cpp) 生成遥测，经 [`src/comm/mqtt/mqtt_publisher.cpp`](src/comm/mqtt/mqtt_publisher.cpp) 发到 MQTT，再由 [`app/processor/main.py`](app/processor/main.py) 接收，最后在 [`app/storage/sqlite_store.py`](app/storage/sqlite_store.py) 完成标准化、健康评分、异常判定和落库。其中最核心的处理文件是 [`app/storage/sqlite_store.py`](app/storage/sqlite_store.py)。
