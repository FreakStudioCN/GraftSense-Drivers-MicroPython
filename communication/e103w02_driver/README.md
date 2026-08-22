# EBYTE E103-W02 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [公共 API](#公共-api)
- [安全说明](#安全说明)
- [注意事项](#注意事项)
- [真机验证](#真机验证)
- [官方资料限制](#官方资料限制)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本包为 EBYTE E103-W02 UART Wi-Fi 模块提供 MicroPython 驱动。驱动仅使用两份 E103-W02 官方手册明确出现的命令，不使用 ESP8266、ESP32、ESP-AT 或其他模块协议。

UART 对象由调用者创建并注入。驱动不拥有 UART 生命周期，也不会在导入或构造时发送命令。

## 主要功能

- AT 模式与透明传输模式切换
- 固件版本、序列号、MAC、网络状态及总体状态查询
- STA/AP 角色、凭证和 IP 配置
- NORMAL/MQTT/HTTP/MULTIS/MULTIC 模式查询与设置
- TCP/UDP 主 Socket 查询与设置
- UART 参数查询与受限设置
- 透明模式原始数据读、写和按行读取
- 带显式确认锁的重启与恢复出厂
- 所有轮询均有超时边界

OneNET、MQTT 细项、HTTP 细项、AirKiss、SmartConfig、多 Socket、心跳包和注册包不属于此版本的公共 API。

## 硬件要求

| 连接 | 当前项目接线 |
|---|---|
| RP2040 TX | GP16 → MTX → E103 GPIO2/RX |
| RP2040 RX | GP17 ← MRX ← E103 GPIO1/TX |
| GND | CN1-1 |
| 载板供电 | CN1-2，+5 V 输入；载板转换为 3.3 V |

GP16/GP17 是当前项目配置，不是 E103-W02 固定引脚。载板 UART 路径为 3.3 V 直连，无电平转换器。

## 软件环境

- MicroPython v1.x
- 默认 UART：115200 baud、8N1
- 无第三方运行依赖

## 文件结构

```text
e103w02_driver/
├── code/
│   ├── e103w02.py
│   └── main.py
├── examples/
│   ├── 01_basic_information.py
│   ├── 02_ap_tcp_server_demo.py
│   ├── 03_ap_configuration.py
│   └── 04_sta_tcp_client_configuration.py
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

- `code/e103w02.py`：可提交和安装的驱动文件。
- `code/main.py`：默认只读查询与 AP TCP Server 双向透传演示。
- `examples/01_basic_information.py`：完整只读查询示例。
- `examples/02_ap_tcp_server_demo.py`：AP/TCP Server 持续收发示例。
- `examples/03_ap_configuration.py`：AP 名称、密码和信道配置，默认锁定。
- `examples/04_sta_tcp_client_configuration.py`：STA/TCP Client 配置，默认锁定。
- `package.json`：MicroPython 包管理元数据。

## 快速开始

将 `code/e103w02.py` 和 `code/main.py` 上传到 RP2040 文件系统根目录，然后软复位运行：

```powershell
mpremote connect COM48 cp code/e103w02.py :e103w02.py
mpremote connect COM48 cp code/main.py :main.py
mpremote connect COM48 reset
```

请把 `COM48` 替换为实际串口。若只想临时运行某个示例而不覆盖板上 `main.py`：

```powershell
mpremote connect COM48 exec "exec(open('01_basic_information.py').read())"
```

`main.py` 采用仓库通信驱动的直接运行式示例结构：上电后先执行只读 AT 查询，再持续发送带编号的透明数据并等待电脑端回显。所有写配置、UART、重启和恢复出厂测试开关默认均为 `False`。运行前应确认模块保持 AP、NORMAL、TCP Server 配置，并在电脑端启动 TCP 回显工具。

```python
from machine import Pin, UART
from e103w02 import E103W02

uart = UART(
    0,
    baudrate=115200,
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(16),
    rx=Pin(17),
    timeout=0,
)

wifi = E103W02(uart)
wifi.enter_command_mode()
try:
    print(wifi.get_version())
    print(wifi.get_mac())
    print(wifi.get_status())
finally:
    wifi.exit_command_mode()
```

透明传输链路已经预先配置并处于数据模式时：

```python
wifi.write(b"hello\r\n")
data = wifi.read(timeout_ms=1000)
print(data)
```

### PC 端透明传输测试

当模块保持默认 AP `EBT_EF6A9F`、TCP Server `192.168.1.1:8887` 配置时，先让电脑连接该 AP，再打开“TCP&UDP测试工具”：创建 TCP 客户端，目标 IP 填 `192.168.1.1`、目标端口填 `8887`，点击“连接”。接收区应持续出现 RP2040 发出的编号消息；在发送区输入文本并发送，RP2040 终端应显示对应接收数据。

## 教学与文档示例

示例按照“接线与初始化 → 查询或配置 → 观察终端输出 → 完成通信实验”的顺序组织：

- `01_basic_information.py`：只读查询，适合作为首次上电实验。
- `02_ap_tcp_server_demo.py`：持续发送带编号的数据，并接收电脑端原样回传；这是当前已完成真机验证的主要演示。
- `03_ap_configuration.py`：修改 AP 名称、WPA2 密码和信道，默认带写配置锁。
- `04_sta_tcp_client_configuration.py`：配置路由器凭据及 TCP Client，默认带写配置锁，使用前必须替换占位参数。

将某个示例复制为 RP2040 根目录的 `main.py`，并同时上传 `e103w02.py`。所有改变模块持久配置的示例默认 `APPLY_CONFIGURATION = False`，确认参数后才允许解锁。

## 公共 API

### 模式与底层事务

- `enter_command_mode(timeout_ms=None)`
- `exit_command_mode(timeout_ms=None)`
- `send_command(command, timeout_ms=None)`
- `is_command_mode()`

### 基本查询

- `get_all_state()` → `AT+ALLSTATE`
- `get_version()` → `AT+VER=?`
- `get_device_sn()` → `AT+DEVSN=?`
- `get_mac()` → `AT+MAC=?`
- `get_status()` → `AT+STATUS=?`

### Wi-Fi 与网络

- `get_role()` / `set_role()` → `AT+ROLE`
- `get_mode()` / `set_mode()` → `AT+MODE`
- `get_sta()` / `set_sta()` → `AT+STA`
- `get_sta_ip()` / `set_sta_ip()` → `AT+STAIP`
- `get_ap()` / `set_ap()` → `AT+AP`
- `get_ap_ip()` / `set_ap_ip()` → `AT+APIP`
- `get_ap_channel()` / `set_ap_channel()` → `AT+CHAN`
- `get_socket()` / `set_socket()` → `AT+SOCK`

### UART、重启与恢复出厂

- `get_uart_config()` / `set_uart_config()` → `AT+UART`
- `reset(confirm=True)` → `AT+RST`
- `restore_factory_defaults(confirm=True)` → `AT+RESTORE`

### 透明数据

- `write(data)`
- `read(size=None, timeout_ms=0)`
- `readline(timeout_ms=0, max_bytes=1024)`
- `deinit()`

所有 AT API 返回清理完全匹配命令回显后的原始响应字符串，不把未定义的错误格式强行解释成成功或失败。

## 安全说明

- `reset()` 必须显式传入 `confirm=True`。
- `restore_factory_defaults()` 必须显式传入 `confirm=True`，会清除持久配置。
- `set_uart_config()` 不会自动重配置外部 UART；它可能使主机立即失联，应在独立加锁测试中执行。
- STA/AP/IP/Socket/模式设置可能改变持久网络配置，示例默认不调用。
- `main.py` 会执行只读查询和透明数据收发，但不会调用任何持久配置、重启或恢复出厂 API。

## 注意事项

- GP16 接模块 RX（MTX），GP17 接模块 TX（MRX），两端必须共地。
- AT 模式和透明传输模式不能同时收发；执行透明通信前必须退出 AT 模式。
- 修改 AP/STA/Socket/UART 参数后可能需要重启模块；先记录原配置。
- 恢复出厂会清除持久配置，应单独进行真机测试。
- 驱动不解析手册未定义的统一成功/失败语法，调用者应结合原始响应判断结果。

## 真机验证

截至 2026-08-20，已在 RP2040（GP16/GP17）和 E103-W02 实物上完成：

- 基本信息、状态、AP/STA、IP、Socket、UART 查询。
- 默认 AP + TCP Server 双向透明传输，使用“TCP&UDP测试工具”。
- AP SSID、WPA2 密码修改后重新连接。
- STA 加入路由器并作为 TCP Client 与电脑 TCP Server 双向通信。
- 通过板载按键恢复出厂设置。

尚未单独执行自动化的 `AT+UART` 改参和 `AT+RESTORE` 命令回归；这两项继续保持显式锁定。

## 官方资料限制

参考资料：

- `E103-W02_Datasheet_CN_V3.3.pdf`
- `E103-W02_UserManual_CN_1.1.pdf`

两份资料的 AT 表内容相同，并未定义统一错误响应、精确响应终止符、异步文本事件或 `+++` guard timing。为适应该限制：

- 构造参数 `command_terminator` 可覆盖，默认 `b"\r\n"`。
- 事务使用总超时和静默窗口收包。
- API 返回原始响应，避免伪造协议结论。
- `+++` 前由调用者保证链路空闲。

本版本的已验证范围见“真机验证”；未验证项目不会在默认示例中自动执行。

## 版本记录

| 版本 | 日期 | 作者 | 说明 |
|---|---|---|---|
| 1.0.0 | 2026-08-19 | FreakStudio | 首个完整常用功能版本 |

## 联系方式

问题与改进建议请通过 GraftSense-Drivers-MicroPython_Fork 仓库的 Issue 或 Pull Request 提交。

## 许可协议

MIT License，详见 `LICENSE`。
