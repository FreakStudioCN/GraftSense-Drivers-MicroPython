# E22-900M22S MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [公开-API](#公开-api)
- [演示方式](#演示方式)
- [注意事项](#注意事项)
- [验证状态](#验证状态)
- [来源与归属](#来源与归属)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本项目将 EBYTE E22-900M22S（SX1262）与板载 RP2040-Zero 封装为一个由 UART 控制的 LoRa 模块。外部 RP2040 Pico/Zero 只需连接 3.3 V UART 和 GND，即可通过 `E22UARTClient` 完成初始化、发送、接收和状态查询。

```text
外部 RP2040 -- UART --> 板载 RP2040-Zero -- SPI --> E22-900M22S (SX1262)
```

## 主要功能

- SX1262 SPI 复位、BUSY 有界等待和状态读取。
- E22-900M22S TCXO 2.2 V 和 DIO2 自动 RF switch 配置。
- 850.0–930.0 MHz 频率与 -9–22 dBm 功率参数校验。
- LoRa TX/RX、DIO1 IRQ、FIFO、RSSI 和 SNR 读取。
- UART JSON 协议、板载 bridge 和外部 RP2040 封装 API。
- 定向 20 包演示与任意 UTF-8 文本交互演示。

## 硬件要求

- 双向无线演示需要 2 套 E22-900M22S + 板载 RP2040-Zero。
- 2 个外部 RP2040 Pico/Zero 主控。
- 2 根匹配测试频率的 915 MHz 天线。
- 稳定的 3.3 V UART 电平和共地连接。

### 板载 RP2040-Zero 到 E22

| E22 信号 | GPIO |
|---|---:|
| MISO | GP0 |
| NSS/CS | GP1 |
| SCK | GP2 |
| MOSI | GP3 |
| NRST | GP4 |
| BUSY | GP5 |
| DIO1 | GP6 |

板载 UART1 使用 GP8 TX / GP9 RX，115200 8N1。DIO2 由 SX1262 控制 RF switch，DIO3 为 TCXO 提供 2.2 V。

### 外部主控到 LoRa 板

| 外部主控 | LoRa 板 UART |
|---|---|
| TX（A1 GP0 / C1 GP16） | RX（板载 GP9） |
| RX（A1 GP1 / C1 GP17） | TX（板载 GP8） |
| GND | GND |

## 软件环境

| 项目 | 要求 |
|---|---|
| 固件 | MicroPython v1.23.0 或更高版本（RP2） |
| 驱动版本 | 1.0.0 |
| PC 工具 | Python 3 + `mpremote` |
| 运行时外部依赖 | 无 |

驱动运行时通过依赖注入接收 SPI、Pin 和 UART 对象，不在库内部绑定具体 MCU；因此发布包标记为兼容标准 MicroPython 端口。当前实机验证平台为 RP2040-Zero/Pico，`code/main.py` 和 `examples/` 中的 GPIO 配置也以 RP2040 为准。移植到其他 MicroPython 主控时，需要按目标端口重新创建并注入这些硬件对象。

## 文件结构

```text
lora_driver/
├── code/                         # 规范化运行码
│   ├── _sx126x.py                   # SX126X 常量
│   ├── sx126x.py                    # SPI 传输与 TX/RX 状态机
│   ├── sx1262.py                    # SX1262 初始化与 PA
│   ├── e22_900m22s.py               # E22 专用适配层
│   ├── e22_uart_protocol.py         # UART 协议
│   ├── e22_uart_bridge.py           # 板载 bridge
│   ├── e22_uart_client.py           # 外部 RP2040 API
│   └── main.py                      # LoRa 板载 Zero 入口
├── examples/
│   ├── pico_uart_example.py         # UART API 最小示例
│   ├── pico_node_tx.py              # 20 包发送示例
│   └── pico_node_rx.py              # 20 包接收示例
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|---|---|
| `code/_sx126x.py` | SX126X 命令、寄存器、IRQ 和 LoRa 参数常量 |
| `code/sx126x.py` | 依赖注入的 SPI 传输、BUSY 超时与 TX/RX 底层状态机 |
| `code/sx1262.py` | SX1262 LoRa 初始化、PA 功率、发送和接收流程 |
| `code/e22_900m22s.py` | E22-900M22S 频率、TCXO 2.2 V、DIO2 RF switch 与功率约束适配层 |
| `code/e22_uart_protocol.py` | UART bridge 与 client 共用的换行 JSON 协议 |
| `code/e22_uart_bridge.py` | 板载 MCU 命令解析与 E22 API 调度 |
| `code/e22_uart_client.py` | 外部 MicroPython 主控使用的阻塞式高层 API |
| `code/main.py` | RP2040-Zero 板载 SPI/Pin/UART 组合入口 |
| `examples/pico_uart_example.py` | UART API 初始化示例 |
| `examples/pico_node_tx.py` | 20 包 LoRa 发送验证示例 |
| `examples/pico_node_rx.py` | 20 包 LoRa 接收验证示例 |

## 快速开始

1. 为两个 LoRa 板安装匹配频率的天线。
2. 向每个 LoRa 板载 Zero 上传 `code/` 中的 `_sx126x.py`、`sx126x.py`、`sx1262.py`、`e22_900m22s.py`、`e22_uart_protocol.py`、`e22_uart_bridge.py` 和 `main.py`。
3. 向每个外部 RP2040 上传 `code/e22_uart_protocol.py` 和 `code/e22_uart_client.py`。
4. 根据外部主控引脚调整示例中的 UART TX/RX，再运行 `examples/pico_uart_example.py`。

`package.json` 覆盖除 `main.py` 外的全部 7 个运行时模块。外部主控实际只需 import `e22_uart_client.py` 和 `e22_uart_protocol.py`。

## 公开 API

```python
from machine import Pin, UART
from e22_uart_client import E22UARTClient

uart = UART(0, 115200, tx=Pin(0), rx=Pin(1), timeout=0)
e22 = E22UARTClient(uart)
print(e22.ping())
print(e22.initialize(915.0, output_power_dbm=0))
e22.send(b"hello")
payload, rssi_dbm, snr_db = e22.receive(timeout_ms=5000)
```

| API | 返回值 | 说明 |
|---|---|---|
| `ping()` | `dict` | 检查 bridge 和协议版本 |
| `initialize(...)` | `dict` | 配置频率、LoRa 参数和功率 |
| `send(data, timeout_ms)` | `int` | 发送 1–255 字节 |
| `receive(max_length, timeout_ms)` | `tuple` | 返回 `(payload, rssi_dbm, snr_db)` |
| `status()` | `dict` | 读取 bridge 与底层状态 |

## 演示方式

两个外部 RP2040 均完成驱动文件上传后，先在接收端运行 RX 示例，再在发送端运行 TX 示例：

```powershell
py -m mpremote connect <RX_COM> run examples/pico_node_rx.py
py -m mpremote connect <TX_COM> run examples/pico_node_tx.py
```

预期分别输出 `RX_NODE_PASS COUNT=20` 和 `TX_NODE_PASS COUNT=20`。反向测试时交换发送与接收端口。

## 注意事项

| 类别 | 限制 |
|---|---|
| 频率 | 850.0–930.0 MHz；必须遵守当地无线电法规 |
| 天线 | 发射前必须连接匹配频率和接口的天线 |
| 功率 | 硬件上限 22 dBm；桌面测试建议 0 dBm |
| UART | 3.3 V TTL、115200 8N1；不可连 RS-232 电平 |
| 依赖注入 | SPI、Pin 和 UART 由组合入口创建，驱动类内不创建 |
| 超时 | BUSY、TX、RX 和 UART 请求都使用有界超时 |

## 验证状态

- SPI、Reset、GetStatus、Standby、TCXO 2.2 V、DIO2 RF switch：PASS。
- 两套实机 UART 控制链路：PASS。
- 915 MHz、0 dBm、A→B 和 B→A 双向 LoRa：PASS。
- 20 包定向演示、任意 UTF-8 文本、二进制/32/64 字节数据：PASS。
- RSSI/SNR、RX 超时恢复、频率和功率校验：PASS。

上述结论仅覆盖 915 MHz、0 dBm、短距离条件，不代表最大功率、距离、灵敏度或长期稳定性认证。

## 来源与归属

SX126X/SX1262 结构主要参考 MIT 许可的 FreakStudioCN/GraftSense-Drivers-MicroPython `communication/sx1262_driver`，其实现谱系包含 E H Ong 的 micropySX126X 与 Jan Gromes 的 RadioLib。E22-900M22S 频率、TCXO、DIO2 RF switch 和引脚约束来自 EBYTE 官方资料及本项目硬件分析。

## 版本记录

| 版本 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| 1.0.0 | 2026-08-24 | FreakStudio | 首个正式发布版：完成 SX1262/E22 驱动、UART bridge/client、TX/RX 及双节点真机验证 |

## 联系方式

- GitHub: [FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)
- Email: support@freakstudio.cn

## 许可协议

MIT License

Copyright (c) 2018 Jan Gromes
Copyright (c) 2020 E H Ong
Copyright (c) 2026 GraftSense
Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
