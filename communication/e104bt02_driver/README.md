# E104-BT02 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [API 参考](#api-参考)
- [工作模式与使用限制](#工作模式与使用限制)
- [硬件验证](#硬件验证)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

`e104bt02_driver` 是 EBYTE E104-BT02 BLE 透明传输模块的 MicroPython UART 驱动。驱动封装了经过官方资料核对及真实硬件验证的 AT 查询、常用配置、透明数据收发、波特率配置和恢复出厂配置功能。

驱动接收调用者创建的 UART 对象，不绑定开发板、UART 编号或 GPIO。当前版本没有实现 E104-BT02 的全部 AT 指令。

## 主要功能

- 支持无 CR/LF 的 `b"<COMMAND>"` AT 帧。
- 支持 ASCII 响应和二进制 MAC 响应解析。
- 提供 16 个只读查询 API。
- 提供模块名称、MTU、广播状态和广播间隔配置。
- 提供受限波特率配置和恢复出厂配置。
- 支持 BLE 透明模式下的 UART `bytes` 双向传输。
- 提供有限超时、最大帧长度保护及 MicroPython 兼容异常。
- `_flush_input()` 具有绝对超时，持续 RX 数据不会导致无限等待。

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / RP2040 或其他支持 MicroPython UART 的控制器
- EBYTE E104-BT02 BLE 模块
- 3.3 V UART 电平及可靠共地连接
- 可控制或人工操作的 P00/MOD 模式信号
- 确保模块处于唤醒状态的 P06/WKP 硬件条件

### 引脚连接

| E104-BT02 引脚 | 官方功能 | 主机连接 | 方向 |
| --- | --- | --- | --- |
| P04 | UART TX | 主机 UART RX | E104 -> 主机 |
| P05 | UART RX | 主机 UART TX | 主机 -> E104 |
| P00/MOD | 模式选择 | 按载板设计控制 | LOW 配置，HIGH 透明传输 |
| P06/WKP | 唤醒/睡眠控制 | 按载板设计处理 | 驱动不控制 |
| VCC | 模块供电 | 合规电源 | 电源 |
| GND | 地 | 主机 GND | 必须共地 |

真机回归使用 RP2040 `GP16 TX` 和 `GP17 RX`。这组 GPIO 只是测试接线，不是驱动的强制配置。

已验证自制载板采用主机视角网络名：

- RP2040 `GP16 TX` -> 载板 `MTX/TX` -> E104 `P05 RX`
- E104 `P04 TX` -> 载板 `MRX/RX` -> RP2040 `GP17 RX`

## 软件环境

| 项目 | 说明 |
| --- | --- |
| 驱动版本 | `1.3.1` |
| 运行环境 | MicroPython |
| 真机验证固件 | MicroPython v1.28.0 |
| 驱动声明平台 | MicroPython v1.23 及兼容版本 |
| 外部依赖 | 无 |
| 通信接口 | 调用者注入的 UART 对象 |

## 文件结构

```text
e104bt02_driver/
├── code/
│   ├── e104bt02.py
│   └── main.py
├── LICENSE
├── package.json
└── README.md
```

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `code/e104bt02.py` | E104-BT02 正式驱动 |
| `code/main.py` | RP2040 基础 AT 查询及 BLE/UART 双向透明传输示例 |
| `package.json` | GraftSense / mip 包元数据 |
| `README.md` | 安装、接线和 API 使用说明 |
| `LICENSE` | MIT 许可证全文 |

`main.py` 是示例文件，不包含在 `package.json.urls` 的安装映射中。

## 快速开始

1. 将 `code/e104bt02.py` 上传到 MicroPython 设备文件系统。
2. 按引脚表连接 UART，并确保主机与模块共地。
3. 将模块唤醒，并把 P00/MOD 置为 LOW 配置模式。
4. 创建 UART 对象并注入 `E104BT02`。

```python
from machine import Pin, UART
from e104bt02 import E104BT02, E104BT02Error

uart0 = UART(
    0,
    baudrate=19200,
    tx=Pin(16),
    rx=Pin(17),
    parity=None,
    stop=1,
)
module = E104BT02(uart0)

try:
    print("baudrate:", module.get_baudrate())
    print("name:", module.get_module_name())
    print("state:", module.get_state())
    print("mac:", module.get_mac())
except E104BT02Error as err:
    print("E104-BT02 error:", err)
```

透明传输时释放 MODE，使 P00/MOD 为 HIGH：

```python
module.send(b"RP2040_TO_E104")
data = module.read(timeout_ms=1000)
print(data)
```

透明数据始终使用 `bytes`；驱动不会自动进行 ASCII 或 UTF-8 编解码。

## 使用说明

1. 将 `e104bt02.py` 上传到 MicroPython 设备的根目录或模块搜索路径。
2. 按模块实际配置初始化 UART。出厂资料记录的 UART 参数为 `19200` baud、无校验、1 个停止位。
3. 执行 AT 查询或配置前，确保模块已经唤醒，并将 P00/MOD 置为 LOW。
4. 执行 BLE 透明传输前，释放 MODE，使 P00/MOD 回到 HIGH。
5. 调用配置类 API 后，根据对应功能要求人工同步主机 UART、模式信号或电源状态；驱动不会代替调用者控制这些硬件。

`code/main.py` 先执行 6 条代表性的安全查询，再提示用户人工释放 MODE，随后演示 UART -> BLE 主动发送、BLE -> UART 持续接收及原样 echo。示例不执行 setter、恢复出厂或重置操作。

## 示例程序

### 基础 AT 查询片段

以下代码展示 `code/main.py` 的配置阶段用法。运行前应按住 MODE，确保 P00/MOD 在整个查询期间保持 LOW。

```python
import time
from machine import Pin, UART

from e104bt02 import E104BT02, E104BT02Error

UART_ID = 0
UART_TX_PIN = 16
UART_RX_PIN = 17
UART_BAUDRATE = 19200
UART_PARITY = None
UART_STOP_BITS = 1

print("FreakStudio: E104-BT02 safe AT query example")
time.sleep(3)

uart0 = UART(
    UART_ID,
    baudrate=UART_BAUDRATE,
    tx=Pin(UART_TX_PIN),
    rx=Pin(UART_RX_PIN),
    parity=UART_PARITY,
    stop=UART_STOP_BITS,
)
module = E104BT02(uart0)

try:
    print("Hold MODE or set P00/MOD low before this AT query example.")
    print("The driver cannot detect or switch P00/MOD.")
    print("baudrate=%d" % module.get_baudrate())
    print("stop_bits=%d" % module.get_stop_bits())
    print("parity=%s" % module.get_parity())
    print("module_name=%s" % module.get_module_name())
    print("factory_name=%s" % module.get_factory_name())
    print("software_version=%s" % module.get_software_version())
    print("hardware_version=%s" % module.get_hardware_version())
    print("serial_number=%s" % module.get_serial_number())
    print("state=%s" % module.get_state())
    print("mtu=%d" % module.get_mtu())
    print("role=%s" % module.get_role())
    print("mac=%s" % module.get_mac())
    print("E104-BT02 safe AT query example finished")
except KeyboardInterrupt:
    print("Program interrupted by user")
except (ValueError, TypeError, E104BT02Error, OSError) as err:
    print("E104-BT02 example failed: %s" % str(err))
```

### BLE 透明传输

运行前释放 MODE，使 P00/MOD 为 HIGH，并由 BLE central 完成连接。以下代码将 UART 收到的 BLE 数据打印出来，再发送一段透明数据：

```python
from machine import Pin, UART
from e104bt02 import E104BT02

uart0 = UART(
    0,
    baudrate=19200,
    tx=Pin(16),
    rx=Pin(17),
    parity=None,
    stop=1,
)
module = E104BT02(uart0)

received = module.read(timeout_ms=20000)
print("BLE -> UART:", received)

payload = b"RP2040_TO_E104"
written = module.send(payload)
print("UART -> BLE bytes:", written)
```

UART 写入成功只表示数据已经交给 E104-BT02；UART -> BLE 是否成功仍应由 BLE central 的实际 Notify 数据确认。

## API 参考

### 查询 API

| API | 返回内容 |
| --- | --- |
| `get_baudrate()` | 模块报告的配置波特率 |
| `get_stop_bits()` | 停止位 |
| `get_parity()` | 校验配置 |
| `get_module_name()` | 模块名称 |
| `get_factory_name()` | 厂商名称 |
| `get_software_version()` | 软件版本 |
| `get_hardware_version()` | 硬件版本 |
| `get_serial_number()` | 去除末尾 NUL padding 的序列号 |
| `get_serial_number_raw()` | 原始序列号 payload |
| `get_state()` | BLE 连接状态 |
| `get_mtu()` | MTU 配置 |
| `get_role()` | 模块角色 |
| `get_mac()` | 文本格式 MAC 地址 |
| `get_mac_raw()` | 6 字节 MAC payload |
| `get_advertising_state()` | `"on"` 或 `"off"` |
| `get_advertising_interval()` | 广播间隔配置值 |

### 配置 API

| API | 说明 | 参数范围或限制 |
| --- | --- | --- |
| `set_module_name(name)` | 设置模块名称 | ASCII，1-18 bytes |
| `set_mtu(mtu)` | 设置 MTU | `20..128` |
| `start_advertising()` | 开启广播 | 配置模式 |
| `stop_advertising()` | 停止广播 | 配置模式 |
| `set_advertising_interval(interval_units)` | 设置广播间隔 | `32..16000` |
| `set_baudrate(baudrate)` | 设置模块 UART 波特率 | 见下方 allowlist |
| `restore_factory_defaults()` | 发送官方 `<RESTORE>` | 高影响操作 |

`set_baudrate()` 只允许以下两份官方资料共同确认的值：

```text
4800, 9600, 19200, 38400, 57600, 115200
```

不同官方资料对最大波特率存在冲突，因此驱动不开放 `230400` 和 `256000`。

### 透明传输 API

| API | 说明 |
| --- | --- |
| `send(data)` | 通过 UART 发送透明数据，返回写入字节数 |
| `read(max_bytes=0, timeout_ms=0)` | 在有限时间内读取透明数据 |
| `read_available()` | 读取当前可用数据 |
| `any()` | 返回 UART 当前可读字节数 |

### 生命周期 API

| API | 说明 |
| --- | --- |
| `close()` | 释放驱动内部 UART 引用 |
| `deinit()` | `close()` 的生命周期接口 |

`close()` 和 `deinit()` 不会关闭调用者创建的 UART 硬件对象。

### 异常类

```python
from e104bt02 import (
    E104BT02Error,
    E104BT02TimeoutError,
    E104BT02FrameError,
    E104BT02ResponseError,
)
```

## 工作模式与使用限制

### AT 配置模式

- 模块必须已唤醒。
- P00/MOD 必须为 LOW。
- 驱动不能检测或切换 P00/MOD。
- AT 帧格式为 `b"<COMMAND>"`，不附加 CR、LF 或 CRLF。

### 透明传输模式

- P00/MOD 必须为 HIGH。
- BLE central 侧已验证 GATT 为 Service `0xFFF0`、Notify/Read `0xFFF1`、Read/Write `0xFFF2`。
- GATT UUID 属于 BLE central 接口，不是本 UART 驱动的 API。

### 波特率配置

`set_baudrate()` 只修改模块配置，不会修改主机 UART、控制 MODE/WKP、重启模块或创建新 UART。`get_baudrate()` 返回模块报告的 configured baudrate，不能单独用来探测 active UART baudrate。

真机验证确认 setter 的 `<OK>` 使用切换前的 active baudrate 返回。配置值与 active UART baudrate 在模式切换过程中可能暂时不同，主机必须按受控流程同步 UART。

### 恢复出厂配置

`restore_factory_defaults()` 只有收到 `<OK>` 才返回 `True`。该返回值只表示命令得到确认，不表示所有参数已经激活、模块已经重启或主机 UART 已经同步。

真机测试观察到 RESTORE 后模块名称为 `E104-BT02-V5.0`、MTU 为 `100`，与部分官方文档默认值不一致。这些只能作为当前硬件观察值，不能声明为官方默认值。

## 硬件验证

测试环境：Raspberry Pi Pico / RP2040、MicroPython v1.28.0、UART0、19200 baud、无校验、1 个停止位。

| 验证项目 | 结果 |
| --- | --- |
| 安全 AT 查询 | 12 / 12 PASS |
| Formal AT regression v1.3.1 | 4 / 4 PASS |
| 二进制 MAC 响应 | PASS |
| BLE -> UART 透明传输 | PASS |
| UART -> BLE 透明传输 | PASS |
| 常用配置 API | PASS |
| `set_baudrate()` | PASS |
| `<RESTORE>` ACK 与 marker reset effect | PASS |
| 官方默认值一致性 | PARTIAL |
| `_flush_input()` 持续 RX 有限返回 mock | PASS |

正式透明传输回归使用 `FORMAL_BLE_TO_UART_01` 和 `FORMAL_UART_TO_BLE_01`，双向 21 bytes 均完整通过。完整 E104-BT02 AT 指令集尚未全部实现或完成硬件验证。

## 注意事项

| 类别 | 注意事项 |
| --- | --- |
| UART | 主机 TX 必须连接 E104 P05 RX，E104 P04 TX 必须连接主机 RX |
| 模式 | AT API 使用 P00/MOD LOW；透明传输使用 P00/MOD HIGH |
| 唤醒 | 驱动不控制 P06/WKP，调用前必须由硬件保证模块已唤醒 |
| 波特率 | setter 不会同步主机 UART；切换失败时不要盲目扫描或恢复出厂 |
| RESTORE | 属于破坏性操作，不应作为普通通信测试命令 |
| 数据类型 | 透明传输使用 `bytes`，不自动追加终止符或编码文本 |
| API 范围 | 未实现 role setter、UUID setter、reset、sleep、配对及 master scan/connect helper |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
| --- | --- | --- | --- |
| v1.3.1 | 2026-08-18 | FreakStudio | 为 UART 输入清理增加绝对超时，并完成最终非破坏性真机回归 |
| v1.3.0 | 2026-08-18 | FreakStudio | 增加恢复出厂配置 API |
| v1.2.0 | 2026-08-18 | FreakStudio | 增加常用配置及波特率配置 API |
| v1.0.0 | 2026-08-18 | FreakStudio | 初始正式驱动及双向透明传输支持 |

## 联系方式

- GitHub：[FreakStudioCN](https://github.com/FreakStudioCN)
- 邮箱：liqinghsui@freakstudio.cn

## 许可协议

```text
MIT License

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
```
