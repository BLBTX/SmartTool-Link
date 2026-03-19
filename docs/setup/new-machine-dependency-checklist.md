# SmartTool-Link 新电脑安装依赖检查清单

适用场景：把项目迁移到一台新的 Windows / Ubuntu / macOS 电脑时，先按这份清单检查，再执行一键启动脚本。

---

## 1. 必备基础环境

### 1.1 Python

- 要求：`Python 3.10+`
- 检查命令：

```bash
python --version
```

通过标准：输出版本不低于 `3.10`

---

### 1.2 pip

- 用途：安装 Python 依赖
- 检查命令：

```bash
python -m pip --version
```

通过标准：命令可执行

---

### 1.3 Git

- 用途：拉取项目代码
- 检查命令：

```bash
git --version
```

通过标准：命令可执行

---

## 2. Python 运行依赖

项目会自动安装以下依赖，但建议确认网络和 pip 可用：

- `paho-mqtt`
- `mysql-connector-python`
- `pandas`
- `plotly`
- `streamlit`

检查文件：

- `app/requirements.txt`

安装命令：

```bash
python -m pip install -r app/requirements.txt
```

---

## 3. MQTT Broker 依赖

### 3.1 Mosquitto

- 用途：本地 MQTT Broker
- 非必须：如果只跑 sample 模式，可以先不装
- 推荐安装：如果要跑端到端 MQTT 链路，必须安装

检查命令：

```bash
mosquitto -h
```

或检查路径：

- Windows：`C:\Program Files\Mosquitto\mosquitto.exe`
- Windows：`C:\Program Files (x86)\Mosquitto\mosquitto.exe`
- Linux：`/usr/sbin/mosquitto`
- macOS：`/opt/homebrew/sbin/mosquitto`

通过标准：命令可执行或文件存在

---

## 4. C++ 构建依赖

### 4.1 CMake

- 用途：构建 C++ 网关
- 检查命令：

```bash
cmake --version
```

通过标准：版本不低于 `3.20`

---

### 4.2 C++ 编译器

- Windows：推荐 `MSVC / Visual Studio Build Tools 2022`
- Linux：推荐 `g++ 9+`
- macOS：推荐 `clang 12+`

检查命令：

```bash
cl
```

或：

```bash
g++ --version
```

或：

```bash
clang++ --version
```

通过标准：至少一个编译器可用

---

## 5. 可选数据库依赖

### 5.1 SQLite

- 默认开发路径使用 SQLite
- Python 标准库已自带 `sqlite3`
- 一般不需要额外安装

验证方法：

```bash
python scripts/setup/init_db.py
```

通过标准：成功初始化 `data/runtime/smarttool_link.db`

---

### 5.2 MySQL

- 用途：可选双写与存储过程演示
- 非必须：本地开发可不装

检查命令：

```bash
mysql --version
```

或确认服务是否可连接：

```bash
python scripts/setup/init_mysql.py
```

通过标准：MySQL 客户端存在，或初始化脚本可连通数据库

---

## 6. 推荐安装顺序

1. 安装 `Python 3.10+`
2. 安装 `Git`
3. 安装 `CMake`
4. 安装一个 C++ 编译器
5. 可选安装 `Mosquitto`
6. 可选安装 `MySQL`
7. 拉取项目代码
8. 运行一键脚本

---

## 7. 一键迁移命令

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/quickstart.ps1
```

### Linux / macOS

```bash
bash scripts/setup/quickstart.sh
```

### 通用 Python 方式

```bash
python scripts/setup/quickstart.py --run
```

---

## 8. 最小可运行条件

如果你只想最快跑起项目，至少满足下面 3 项：

- Python 3.10+
- pip 可用
- Streamlit 依赖能安装

这时可以走 sample 模式，不依赖 Mosquitto 和 MySQL。

推荐命令：

```bash
python scripts/setup/quickstart.py --run --mode sample
```

---

## 9. 完整演示条件

如果你要展示完整链路，建议满足下面条件：

- Python 3.10+
- pip 可用
- Mosquitto 已安装
- CMake 可用
- C++ 编译器可用

推荐命令：

```bash
python scripts/setup/quickstart.py --run --mode mqtt
```

---

## 10. 故障排查建议

### 问题：`python` 不存在

- 说明 Python 没装或没加 PATH

### 问题：`mosquitto` 不存在

- 可以先用 sample 模式启动
- 若要跑 MQTT E2E，再安装 Mosquitto

### 问题：`cmake` 不存在

- 不影响 Python 链路
- 只会影响 C++ 网关构建

### 问题：MySQL 初始化失败

- 本地没有启动 MySQL 服务
- 不影响 SQLite 开发模式

---

## 11. 建议你最终检查的 5 条命令

```bash
python --version
python -m pip --version
cmake --version
mosquitto -h
python scripts/setup/quickstart.py --run --mode sample
```

如果这几条大部分能通过，项目迁移到新电脑基本就没有大问题。
