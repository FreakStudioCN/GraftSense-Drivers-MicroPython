# DY-SV19T 语音播放模块驱动 - MicroPython版本

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
DY-SV19T 是一款支持 UART 串口控制的语音播放模块，广泛应用于语音提示、智能硬件、机器人等场景。驱动支持音频播放、暂停、停止、音量调节、EQ、循环模式、插播、组合播放等丰富功能，便于开发者快速集成到 MicroPython 项目。

---

## 主要功能
- **音频播放控制**：支持播放、暂停、停止、上一首、下一首
- **音量与均衡调节**：音量 0~30，EQ 多种模式
- **循环与随机播放**：多种循环/顺序/随机模式
- **指定曲目/路径播放**：支持按曲目号或路径播放、插播
- **组合播放**：支持 ZH 文件夹下多曲目组合播放
- **播放进度查询**：支持自动上报与主动查询播放时间
- **状态与信息查询**：盘符、曲目、文件夹、短文件名等
- **参数校验与异常处理**：接口参数严格校验，错误提示清晰

---

## 硬件要求
### 推荐测试硬件
- 树莓派 Pico/Pico W
- DY-SV19T 语音播放模块
- 杜邦线若干

### 模块引脚说明
| DY-SV19T 引脚 | 功能描述 |
|--------------|----------|
| VCC          | 电源正极（3.3V/5V） |
| GND          | 电源负极 |
| TX           | 串口输出（接开发板 RX） |
| RX           | 串口输入（接开发板 TX） |

---

## 文件说明
### dy_sv19t.py
驱动核心，包含 DYSV19T 类及所有控制/查询方法。
```python
class DS1232:
    """
    该类控制外部 DS1232 看门狗模块，通过周期性翻转 WDI 引脚喂狗，避免 MCU 被复位。

    Attributes:
        wdi (Pin): machine.Pin 实例，用于输出喂狗脉冲。
        state (int): 当前 WDI 引脚输出状态，0 或 1。
        timer (Timer): machine.Timer 实例，用于周期性喂狗。

    Methods:
        __init__(wdi_pin: int, feed_interval: int = 1000) -> None: 初始化看门狗并启动定时喂狗。
        stop() -> None: 停止自动喂狗，将 WDI 引脚置低。
        kick() -> None: 手动喂狗，立即翻转一次 WDI 引脚。

    Notes:
        初始化时会创建 Timer 对象以定时翻转 WDI。
        _feed 为内部回调方法，不建议直接调用。
        该类方法大多非 ISR-safe，Timer 回调 _feed 是 ISR-safe。
        stop() 后 WDI 引脚保持低电平，DS1232 将在超时后复位 MCU。

    ==========================================

    DS1232_Watchdog driver for controlling an external DS1232 watchdog module.
    Periodically toggles WDI pin to prevent MCU reset.

    Attributes:
        wdi (Pin): machine.Pin instance for feeding pulses.
        state (int): Current WDI output state, 0 or 1.
        timer (Timer): machine.Timer instance for periodic feeding.

    Methods:
        __init__(wdi_pin: int, feed_interval: int = 1000) -> None: Initialize the watchdog and start automatic feeding.
        stop() -> None: Stop automatic feeding and set WDI low.
        kick() -> None: Manually feed the watchdog by toggling WDI once.

    Notes:
        Initializes a Timer to periodically toggle WDI.
        _feed is an internal callback method, not recommended for direct user call.
        Most methods are not ISR-safe; _feed callback is ISR-safe.
        After stop(), WDI remains low; DS1232 will reset MCU on timeout.
    """

    def __init__(self, wdi_pin: int, feed_interval: int = 1000) -> None:
```
### main.py
主程序，演示模块初始化、播放控制、查询、组合播放等功能。

---

## 软件设计核心思想

### 模块化设计
- 驱动与应用分离，接口清晰
- 所有命令/查询均为方法调用，参数校验严格

### 串口通信协议
- 所有命令均按模块协议帧格式发送
- 响应帧自动解析与校验，异常自动处理

### 参数与错误处理
- 所有接口参数类型与范围校验
- 错误信息明确，便于调试

### 兼容性与扩展性
- 仅依赖 MicroPython 标准库
- 支持多种硬件平台

---

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| DY-SV19T 引脚 | Pico GPIO 引脚 |
|---------------|----------------|
| VCC           | 3.3V/5V        |
| GND           | GND            |
| TX            | GP1 (接 RX)    |
| RX            | GP0 (接 TX)    |

> **注意：**
> - 串口波特率需设为 9600 8N1
> - VCC 支持 3.3V 或 5V，建议使用稳定电源

---

### 软件依赖

- **固件版本**：MicroPython v1.19+
- **内置库**：
  - `machine`（UART、Pin、Timer 控制）
  - `time`（延时与计时）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `dy_sv19t.py` 和 `main.py` 到开发板
3. 根据硬件连接修改 `main.py` 中的 UART 配置
4. 运行 `main.py`，测试语音播放功能

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:35
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : DY-SV19T 示例

from machine import UART, Pin, Timer
import time
from dy_sv19t import *

# 初始化 UART
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
player = DYSV19T(uart, default_volume=20)

# 设置音量、EQ、循环模式、输出通道
player.set_volume(20)
player.set_eq(player.EQ_ROCK)
player.set_play_mode(player.MODE_SINGLE_STOP)
player.set_dac_channel(player.CH_MP3)

# 播放指定曲目
player.select_track(1, play=True)

# 查询播放状态与信息
print("状态:", player.query_status())
print("当前盘符:", player.query_current_disk())
print("当前曲目:", player.query_current_track())
print("总曲目数:", player.query_total_tracks())
print("当前播放时间:", player.query_current_track_time())
print("短文件名:", player.query_short_filename())

# 组合播放示例
player.start_combination_playlist(['01', '02', '03'])
time.sleep(5)
player.end_combination_playlist()
```

## 注意事项

**串口配置**
- 波特率需为 9600，数据位 8，停止位 1，无校验
- TX/RX 接线需与开发板串口对应

**音频文件要求**
- 路径需以 / 起始，文件夹名 1~8 字节，仅允许 A-Z/0-9/_
- 文件名建议采用 8.3 格式，支持 MP3/WAV

**电源要求**
- 建议使用稳定 3.3V/5V 电源
- 大功率喇叭建议单独供电

**其他**
- 查询方法超时返回 None，不抛异常
- 控制方法写串口失败可能抛 IOError

**联系方式**
- 如有问题或建议，请联系开发者： 📧 邮箱：10696531183@qq.com 💻 GitHub：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython

**许可协议**

本项目除 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0) 许可协议发布。
版权归 FreakStudio 所有。