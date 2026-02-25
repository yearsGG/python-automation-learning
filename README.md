# VisualNetAutomator - Python网络设备自动化巡检平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-v2.1-blue.svg)](https://github.com/yearsGG/python-automation-learning)

一款为网络工程师和NetDevOps初学者设计的、功能完整的网络设备自动化巡检平台。集成可视化SSH/Telnet交互、批量设备巡检、性能监控、报告生成和告警通知功能。

---

## 🚀 项目亮点 (Key Features)

### v2.1 新增功能 🎉
- **🌐 双路径连通性测试**: 支持直接ping和SSH跳转ping两种方式测试网络连通性
- **📋 批量Ping测试**: 支持批量测试多个目标设备的连通性
- **📊 详细统计信息**: 提供丢包率、RTT（往返时间）等详细网络性能指标
- **🔧 Web界面集成**: 在前端界面提供直观的ping测试模态框和结果展示
- **🔄 TextFSM模板支持**: 新增华为VRP ping命令输出解析模板

### v2.0 新增功能 🎉
- **📊 批量设备巡检**: 支持多线程并发巡检，自动采集设备CPU、内存、接口状态等性能指标
- **🏓 Ping连通性检测**: 批量Ping测试，快速识别离线设备
- **📈 报告生成**: 自动生成文本/Excel巡检报告，支持历史数据对比
- **⚠️ 智能告警**: 阈值告警功能，支持邮件通知（可选）
- **⚙️ 配置化管理**: 通过INI配置文件管理设备列表和巡检参数

### v1.0 核心功能
- **🎨 可视化交互**: 所有发送和接收的数据都带有彩色高亮，清晰区分指令、设备回显和工具日志
- **🧠 记忆功能**: 自动记忆上一次的设备提示符，简化连续命令的执行，代码更简洁
- **🔐 SSH & Telnet 双协议支持**: 提供 `VisualSSH` 和 `VisualTelnet` 两个类，无缝切换安全与兼容模式
- **🔄 自动翻页**: 智能识别并处理华为VRP等系统的`---- More ----`翻页提示，自动发送空格
- **🧩 模块化设计**: 代码结构清晰，易于理解和扩展，可方便地集成到更大型的自动化项目中

## ✨ 效果演示 (Screenshots)

为了直观地展示本工具的价值，下面将对比**传统手动SSH**与**使用VisualSSH自动化**两种方式的终端界面。

### 1. 传统终端手动SSH连接
这是我们日常使用的标准SSH客户端（如PowerShell）的界面，信息清晰但缺乏高亮，所有输出都混在一起，不利于快速定位问题。

![手动SSH连接演示](image/ter_text.png "手动SSH连接")

### 2. 使用 VisualSSH 的自动化连接
这是通过本项目的 `VisualSSH` 工具执行相同操作的输出。可以看到，**发送的指令（蓝色）**、**接收的数据（绿色）**以及**工具的内部状态日志（青色/品红色）**都被清晰地区分，极大地提高了调试效率和可读性。这正是本项目的核心价值所在！

![VisualSSH连接演示](image/ssh_text.png "Python自动化连接")

## 🤔 项目背景 (Motivation)

作为一名深入学习华为HCIP的网络工程学生，我深刻理解从命令行（CLI）到自动化编程（NetDevOps）的思维转变过程。在编写Python自动化脚本的初期，我们常常困惑于：
- 脚本到底向设备发送了什么？
- 设备真实地返回了什么？
- 脚本为什么会在某个`read_until`操作卡住？

`VisualNetAutomator`正是为了解决这些痛点而生。它将底层的`paramiko`和`telnetlib`交互过程完全透明化，通过丰富的颜色日志，让我能像看电影一样观察到脚本与网络设备“对话”的每一个细节，极大地提升了自动化脚本的开发和调试效率。

## 🛠️ 技术栈 (Tech Stack)

- **核心语言**: Python 3
- **Web框架**: Flask (v2.1新增)
- **SSH协议库**: `paramiko`
- **Telnet协议库**: `telnetlib` (Python标准库)
- **终端彩色输出**: `colorama`
- **数据解析**: `textfsm` (v2.1新增)
- **前端**: Bootstrap 5, JavaScript (v2.1新增)
- **数据库**: SQLite (v2.1新增)

## ⚙️ 安装与环境准备 (Installation)

1. **克隆本项目到本地**
   ```bash
   git clone https://github.com/yearsGG/python-automation-learning.git
   cd python-automation-learning
   ```

2. **创建`requirements.txt`文件**
   在项目根目录下创建一个名为 `requirements.txt` 的文件，并写入以下内容：
   ```text
   paramiko
   colorama
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

## 📚 如何使用 (Quick Start)

### 方式一：Web界面操作（v2.1新增推荐）

1. **启动Web应用**
    ```bash
    cd src
    python run.py
    ```

2. **访问Web界面**
    - 打开浏览器访问 `http://localhost:5002`
    - 在设备管理界面添加设备信息
    - 使用可视化界面进行设备巡检和ping测试

3. **使用双路径Ping功能**
    - 点击”Ping测试”按钮
    - 选择测试方法：
      - **直接Ping**：从服务器直接ping目标设备
      - **SSH跳转Ping**：通过已连接的网络设备ping其他目标
    - 配置测试参数（包数量、超时时间等）
    - 查看详细的连通性统计信息

---

### 方式二：API调用（v2.1新增）

1. **直接Ping测试**
    ```bash
    curl -X POST http://localhost:5002/api/ping/direct/1 \
      -H “Content-Type: application/json” \
      -d '{“target_ip”: “8.8.8.8”, “count”: 5, “timeout”: 3}'
    ```

2. **SSH跳转Ping测试**
    ```bash
    curl -X POST http://localhost:5002/api/ping/via-ssh/1 \
      -H “Content-Type: application/json” \
      -d '{“target_ip”: “192.168.2.1”, “count”: 5, “timeout”: 3}'
    ```

3. **批量Ping测试**
    ```bash
    curl -X POST http://localhost:5002/api/ping/batch \
      -H “Content-Type: application/json” \
      -d '{“targets”: [“8.8.8.8”, “1.1.1.1”], “method”: “direct”}'
    ```

---

### 方式三：快速巡检（v2.0推荐）

1. **配置设备列表**

编辑 `inspection_config.ini` 文件，添加你要巡检的设备：

```ini
[devices]
count = 2

device1_name = SW-Core1
device1_host = 192.168.1.1
device1_port = 22
device1_username = admin
device1_password = yourpassword

device2_name = R-WAN1
device2_host = 192.168.1.2
device2_port = 22
device2_username = admin
device2_password = yourpassword
```

2. **运行巡检**

```bash
python main_inspection.py
```

3. **查看报告**

巡检完成后，在 `reports/` 目录下查看生成的报告文件。

---

### 方式四：可视化调试（v1.0核心功能）

下面是一个使用 `VisualSSH` 连接一台华为设备并执行命令的简单示例 (`main.py`)：

```python
from my_visual_ssh import VisualSSH
from colorama import Fore, Style

# --- 设备连接信息 ---
HOST = '192.168.85.254'
USER = 'netconftest'
PASSWORD = 'YourPassword@123'

# --- 设备提示符信息 ---
USER_PROMPT = b'>'
SYSTEM_PROMPT = b']'

ssh = None
try:
    # 1. 初始化并建立SSH连接
    ssh = VisualSSH(HOST, username=USER, password=PASSWORD)

    # 2. 等待用户视图提示符，并存入”记忆”
    ssh.read_until(USER_PROMPT)

    # 3. 进入系统视图
    ssh.write(b”system-view”)

    # 4. 等待系统视图提示符，并更新”记忆”
    ssh.read_until(SYSTEM_PROMPT)

    # 5. 使用execute()方法，它将自动使用记忆中的']'作为结束标志
    output = ssh.execute(b”display ip interface brief”)
    print(output)

finally:
    # 确保连接被关闭
    if ssh:
        ssh.close()
```

## 📁 项目结构

```
python自动化/
├── src/                      # 源代码目录
│   ├── run.py                # Flask Web应用主程序 (v2.1新增)
│   ├── core/                 # 核心功能模块
│   │   └── ssh_client.py     # SSH客户端类，包含ping_test方法 (v2.1增强)
│   ├── app/                  # Web应用组件
│   │   ├── templates/        # 前端模板
│   │   │   └── index.html    # 主页面，包含ping模态框 (v2.1增强)
│   │   └── static/           # 静态资源
│   ├── ntc-templates/        # TextFSM模板目录 (v2.1新增)
│   │   └── ntc_templates/
│   │       └── templates/
│   │           └── huawei_vrp_ping.textfsm  # 华为VRP ping解析模板 (v2.1新增)
│   ├── my_visual_ssh.py      # SSH可视化交互类
│   ├── my_visual_telnet.py   # Telnet可视化交互类
│   ├── device_inspector.py   # 设备巡检核心模块（v2.0新增）
│   ├── main_inspection.py    # 完整巡检主程序（v2.0新增）
│   ├── main_refactored.py    # 配置化的SSH执行示例
│   ├── main.py               # 简单SSH示例
│   └── app/                  # 应用数据
│       └── netops.db         # SQLite数据库文件
├── my_visual_ssh.py          # SSH可视化交互类
├── my_visual_telnet.py       # Telnet可视化交互类
├── device_inspector.py       # 设备巡检核心模块（v2.0新增）
├── main_inspection.py        # 完整巡检主程序（v2.0新增）
├── main_refactored.py        # 配置化的SSH执行示例
├── main.py                   # 简单SSH示例
├── config.ini                # 单设备配置文件
├── inspection_config.ini     # 巡检配置文件（v2.0新增）
├── requirements.txt          # Python依赖包列表
├── reports/                  # 巡检报告目录
├── log/                      # 日志文件目录
├── README.md                 # 本文档
├── 培训计划与职业发展路线图.md   # 学习规划文档
└── 实验网络拓扑设计.md          # 网络拓扑设计方案
```

## 🎓 学习资源

本项目附带了完整的学习规划文档：

- 📖 **[培训计划与职业发展路线图.md](培训计划与职业发展路线图.md)**: 
  - 从待培养阶段到中高级NetDevOps工程师的完整学习路径
  - 薄弱技能补强计划（NetworkX、Requests、Wireshark、Kubernetes等）
  - 3个月冲刺计划和职业发展建议

- 🌐 **[实验网络拓扑设计.md](实验网络拓扑设计.md)**:
  - 3种难度的网络拓扑方案（小型/中型/大型企业网络）
  - 详细的设备配置模板和IP地址规划
  - 自动化测试场景设计

## 🔮 未来计划 (Roadmap)

### v2.2 计划
- [ ] 集成SNMP数据采集功能（使用pysnmp）
- [ ] 使用NetworkX进行网络拓扑自动发现与可视化
- [ ] Excel格式巡检报告（带图表）
- [ ] 更多厂商设备支持（思科、Juniper等）

### v3.0 愿景
- [ ] 支持NETCONF/RESTCONF API
- [ ] 配置自动备份和变更检测
- [ ] 容器化部署（Docker + Kubernetes）
- [ ] 实时网络监控仪表板

## 许可证 (License)

本项目采用 [MIT](https://opensource.org/licenses/MIT) 许可证。

## 👤 关于作者 (About Me)

- **姓名**: 袁瑞
- **GitHub**: [@yearsGG](https://github.com/yearsGG)
- **邮箱**: rui.yuan.net@yearsgg.online

<!-- 别忘了把上面的GitHub链接和邮箱换成你自己的！ -->