# R60ABD1 毫米波传感器驱动 - MicroPython版本

## 目录
- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介
本项目为基于 R60ABD1 毫米波传感器的 MicroPython 驱动，支持人体存在检测、运动参数、距离、位置、心率、睡眠等数据采集功能。适用于智能家居、健康监测、环境感知等场景。

> 注意：仅适用于常规信息采集，不建议用于高可靠性或安全关键场合。

---

## 主要功能
- 实时人体存在检测
- 运动方向与强度参数采集
- 距离与三维位置查询
- 心率值与心率波形查询
- 睡眠结束时间查询
- 挣扎敏感度查询与配置接口
- 统一的高层协议接口，易于集成

---

## 硬件要求

### 推荐测试硬件
- 树莓派 Pico / Pico W 或其他兼容 MicroPython 的开发板  
- R60ABD1 毫米波传感器模块  
- 若干杜邦线

### 模块引脚说明
| 引脚 | 功能 |
|------|------|
| VCC  | 电源正极（3.3V - 5V） |
| GND  | 电源负极 |
| TX   | 串口发送（接 MCU RX） |
| RX   | 串口接收（接 MCU TX） |

---

## 文件说明

### r60abd1.py：驱动核心，实现协议构建、解析与常用查询函数（存在、运动、距离、心率等）。  
#### 类定义
```python
class R60ABD1:
    """
    该类提供了对 R60ABD1 毫米波雷达模块的协议解析与高层接口封装，支持通过 UART 与模块通信完成存在检测、运动参数、距离、三维位置、心率、睡眠等信息的查询与控制。
    注意：模块返回值有物理与协议范围限制，超出或异常情况将返回 None。

    Attributes:
        uart (UART): 已初始化的 UART 实例，用于与模块通信（必须由外部创建并传入）。
        _control (int): 内部使用的默认控制字节（例：0x80）。
        _timeout_ms (int): 查询/接收超时时间，单位毫秒。
        _rx_buf (bytearray): 非阻塞接收时使用的滚动缓冲区（内部实现细节，不应外部修改）。

    Methods:
        __init__(uart):
            初始化解析器，接收一个已准备好的 UART 实例，清除串口残留数据并设置默认超时时间。

        build_frame(control: int, cmd: int, data: bytes = b"") -> bytes:
            根据协议构造完整帧：帧头 + ctl + cmd + len(2B) + data + checksum + 帧尾。

        parse_response(resp: bytes) -> dict:
            解析并校验一帧完整响应，返回字典 {"control": int, "cmd": int, "data": bytes}，校验失败抛出 ValueError。

        recv_response() -> tuple[int, int, bytes] | None:
            阻塞接收并解析单帧响应，内部实现字节级有限状态机，校验头/尾/长度/校验和，成功返回 (control, cmd, data)，超时返回 None。

        send_frame(control: int, cmd: int, data: bytes = b""):
            发送一帧数据到模块，失败抛出 IOError。

        query_and_wait(control: int, command: int, send_data: bytes = b"") -> bytes | None:
            发送请求并循环等待匹配 control/command 的响应，返回响应的数据区 bytes。

        disable_all_reports():
            禁用模块的所有主动上报（根据协议发送若干关闭上报命令）。

        q_presence() -> int | None:
            查询存在检测结果，返回 1 表示有人，0 表示无人，失败返回 None。

        q_motion_param() -> tuple | None:
            查询运动参数（方向、强度等），返回解析后的元组或 None。

        q_distance() -> int | None:
            查询目标距离（单位：cm），协议返回两字节大端无符号整数，超时或非法返回 None。

        q_position() -> tuple[int, int, int] | None:
            查询目标三维位置或方向，返回 (x, y, z) 三个有符号 16 位大端整数（单位：度或协议定义的单位），异常返回 None。

        q_hr_value() -> int | None:
            查询心率值（BPM），返回整数或 None。

        q_hr_waveform() -> list[int] | None:
            查询心率波形，返回中心化后的数据数组（例如每点 = raw - 128），或 None。

        q_sleep_end_time() -> str | None:
            查询最近一次睡眠结束时间，返回格式化字符串 "YYYY-MM-DD HH:MM:SS" 或 None。

        q_struggle_sensitivity() -> int | None:
            查询挣扎敏感度设置，返回数值或 None。

    ==========================================
     Attributes:
        uart (UART): An initialized UART instance used for communication with the module (must be created externally and passed in).
        _control (int): Default control byte used internally (e.g.: 0x80).
        _timeout_ms (int): Timeout period for queries/reception, in milliseconds.
        _rx_buf (bytearray): Rolling buffer used for non-blocking reception (internal implementation detail, should not be modified externally).

    Methods:
        __init__(uart):
            Initializes the parser, receives a prepared UART instance, clears residual serial port data, and sets the default timeout period.

        build_frame(control: int, cmd: int, data: bytes = b"") -> bytes:
            Constructs a complete frame according to the protocol: frame header + ctl + cmd + len(2B) + data + checksum + frame tail.

        parse_response(resp: bytes) -> dict:
            Parses and verifies a complete response frame, returns a dictionary {"control": int, "cmd": int, "data": bytes}, and throws a ValueError if verification fails.

        recv_response() -> tuple[int, int, bytes] | None:
            Blocking reception and parsing of a single response frame, internally implements a byte-level finite state machine, verifies header/tail/length/checksum, returns (control, cmd, data) on success, and None on timeout.

        send_frame(control: int, cmd: int, data: bytes = b""):
            Sends a frame of data to the module, throws an IOError on failure.

        query_and_wait(control: int, command: int, send_data: bytes = b"") -> bytes | None:
            Sends a request and loops to wait for a response matching the control/command, returns the data area bytes of the response.

        disable_all_reports():
            Disables all active reports of the module (sends several report closing commands according to the protocol).

        q_presence() -> int | None:
            Queries the presence detection result, returns 1 indicating someone is present, 0 indicating no one is present, and None on failure.

        q_motion_param() -> tuple | None:
            Queries motion parameters (direction, intensity, etc.), returns the parsed tuple or None.

        q_distance() -> int | None:
            Queries the target distance (unit: cm), the protocol returns a 2-byte big-endian unsigned integer, returns None on timeout or if invalid.

        q_position() -> tuple[int, int, int] | None:
            Queries the target's 3D position or direction, returns (x, y, z) three signed 16-bit big-endian integers (unit: degrees or as defined by the protocol), returns None on exception.

        q_hr_value() -> int | None:
            Queries the heart rate value (BPM), returns an integer or None.

        q_hr_waveform() -> list[int] | None:
            Queries the heart rate waveform, returns a centralized data array (e.g., each point = raw - 128), or None.

        q_sleep_end_time() -> str | None:
            Queries the end time of the most recent sleep, returns a formatted string "YYYY-MM-DD HH:MM:SS" or None.

        q_struggle_sensitivity() -> int | None:
            Queries the struggle sensitivity setting, returns a value or None.
    """
    def __init__(self, uart):
```

### main.py：示例主程序，演示驱动用法与常见查询流程。

---

## 软件设计核心思想

### 高层 API 封装
提供统一易用的查询接口（如 `q_presence()`、`q_distance()`、`q_hr_value()` 等），屏蔽底层帧构建与解析细节。

### 协议解析与校验
实现帧头/长度/校验/帧尾的严格校验，接收实现有限状态机以提高鲁棒性。

### 可移植与轻量
驱动仅依赖 MicroPython 标准库（`machine` / `time`），外部由应用层负责 UART/引脚初始化，便于在不同硬件间移植。

---

## 使用说明

### 硬件接线（以树莓派 Pico 为例）
| R60ABD1 引脚 | Pico GPIO 引脚 |
|--------------|----------------|
| VCC          | 3.3V 或 5V     |
| GND          | GND            |
| TX           | GP5（接 Pico RX） |
| RX           | GP4（接 Pico TX） |

注意：串口实例由上层创建并传入驱动，驱动不会创建 UART。

### 软件依赖
- MicroPython 固件：v1.23.0+ 推荐  
- 内置库：`machine`, `time`  
- 开发工具：PyCharm、Thonny 等

### 安装步骤
1. 将 MicroPython 固件烧录到开发板。  
2. 上传 `code/r60abd1.py` 与 `code/main.py` 到设备。  
3. 在 `main.py` 中根据实际引脚创建 UART 并实例化驱动。  
4. 运行 `main.py` 并观察串口输出或按需集成到应用。

---

## 示例程序
```
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : r60abd1毫米波驱动 for micropython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0
# ======================================== 导入相关模块 =========================================

#MicroPython 提供的硬件接口类，用于串口通信和引脚控制模块
from machine import UART, Pin
#关于时间的模块
import time
#R60ABD1 模块驱动类（人体存在/心率/睡眠等传感器协议封装）模块
from r60abd1 import R60ABD1

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def show(label, value, unit=""):
    """
    打印带标签的数值：
    按格式输出标签、数值和可选单位。

    Args:
        label (str): 标签文本。
        value (Any): 显示的数值。
        unit (str, optional): 单位，默认为空字符串。

    ==================================
    Print labeled value:
    Output label, value, and optional unit in formatted style.

    Args:
        label (str): Label text.
        value (Any): Value to display.
        unit (str, optional): Unit string, defaults to empty.
    """
    print(f"→ {label}：{value}{unit}")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# # 打印调试消息
print("FreakStudio: Using R60ABD1 millimeter wave information collection")
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
dev = R60ABD1(uart)

# ========================================  主程序  ===========================================

dev.disable_all_reports()
print("\n【Query output】")
while True:
    val = dev.q_presence();            show("The existence of the human body", "exist" if val==1 else ("Does not exist" if val==0 else None))
    val = dev.q_motion_param();        show("Body movement parameters", val)
    val = dev.q_distance();            show("distance", val, " cm")
    pos = dev.q_position()
    if pos is None:
        show("direction (x,y,z)", None)
    else:
        x,y,z = pos; print(f"→ direction (x, y, z)：({x}, {y}, {z})")
        val = dev.q_hr_value();            show("heart rate", val, " bpm")
        wf = dev.q_hr_waveform()  # -> [-128..127] 的 5 个点，或 None
        if wf:print("HR waveform (centered):", wf)

    val = dev.q_sleep_end_time()
    show("Sleep deadline", val, " minute")
    val = dev.q_struggle_sensitivity()
    if val is None:
        show("Struggle sensitivity", None)
    else:
        mapping = {0:"low",1:"middle",2:"high"}; show("Struggle sensitivity", mapping.get(val, f"Unknown({val})"))
```


---

## 注意事项

### 数据有效性与范围
- 距离、心率等数据有物理测量范围限制，超出范围或异常帧会返回 `None` 或空值。  
- 建议对返回值做空值检查以保证程序鲁棒性。

### 电源与环境
- 建议 5V 供电并保持电源稳定；若使用 3.3V，请确认模块兼容性。  
- 避免高温、高湿和强电磁干扰环境。

### 通信与重试
- UART 通信可能偶发丢帧或噪声，建议在上层实现必要的重试或错误处理机制。

---

## 联系方式
如有问题或建议，请联系开发者：  
📧 邮箱：1098875044@qq.com  
💻 GitHub： https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython

---

## 许可协议
本项目（除 MicroPython 官方模块外）采用 CC BY-NC 4.0 许可。  
- 署名：请注明原作者与项目链接。  
- 非商业性使用：禁止商业用途。  
- 合理引用：可在注释或文档中注明来源。

版权归 FreakStudio 所有。