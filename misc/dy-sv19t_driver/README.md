# GraftSense-基于 DY-SV19T 的语音播放模块（MicroPython）

# GraftSense-基于 DY-SV19T 的语音播放模块（MicroPython）

# GraftSense 基于 DY-SV19T 的语音播放模块

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

## 简介

本模块是 FreakStudio GraftSense 基于 DY-SV19T 的语音播放模块，通过 DY-SV19T 芯片实现音频文件存储与输出，采用 UART 通信接口，具备操作简单、支持多种音频格式、音质清晰等核心优势，兼容 Grove 接口标准。适用于电子 DIY 语音提醒实验、智能语音提示演示、物联网语音交互项目等场景，为系统提供可靠的语音交互能力。

## 主要功能

### 硬件层面

1. 通信接口：UART 全双工通信，固定波特率 9600 8N1，接口引脚兼容 Grove 标准，接线清晰；
2. 存储与下载：支持 USB 下载音频文件，兼容 USB/SD 卡/板载 Flash 三种存储介质；
3. 音频输出：SPK+/SPK-引脚可直接驱动喇叭，无需额外功放，音质稳定；
4. 供电兼容：支持 3.3V/5V 双电压供电，内置电源滤波电路，抑制噪声干扰；
5. 辅助设计：电源指示灯实时显示供电状态，Mini-USB 接口便于首次初始化配置。

### 软件层面

1. 核心驱动封装：基于 MicroPython 封装 DYSV19T 类，覆盖播放/暂停/停止、曲目选择、音量调节等基础操作；
2. 高级功能支持：提供插播、组合播放、区间复读、EQ 调节、播放模式配置等复杂交互能力；
3. 状态监测：支持播放状态、当前曲目、播放时间等信息查询，可开启播放时间自动上报；
4. 灵活控制：支持快进/快退、循环次数设置、DAC 通道切换等精细化控制功能。

## 硬件要求

### 核心接口要求

1. UART 通信接口：需提供 TX/RX 引脚，模块 MRX 接 MCU RXD、模块 MTX 接 MCU TXD，波特率固定 9600 8N1；
2. 供电要求：VCC 支持 3.3V/5V 输入，GND 需与主控板共地，确保供电稳定；
3. 音频输出：SPK+/SPK-引脚需连接喇叭，无额外功放也可正常发声；
4. 初始化要求：首次使用需通过 Mini-USB 线连接上位机，完成音频文件下载与模块初始化。

### 硬件连接规范

1. UART 接线：严禁交叉连接（模块 MRX≠MCU TXD、模块 MTX≠MCU RXD），否则通信失败；
2. 电源稳定性：避免供电电压波动，建议搭配滤波电容使用，防止音质失真；
3. 存储介质：使用 SD 卡时需确保卡内音频文件命名符合模块规范（仅支持 A-Z、0-9、_）。

## 文件说明

| 文件名      | 功能说明                                                                                     |
| ----------- | -------------------------------------------------------------------------------------------- |
| dy_sv19t.py | 封装 DY-SV19T 语音播放模块核心驱动，包含各类常量定义、基础播放控制、高级交互、状态查询等方法 |
| main.py     | 完整示例程序，包含 UART 初始化、播放器实例化、基础参数配置、状态监测及各类播放功能演示       |

## 软件设计核心思想

### 1. 常量标准化设计

将模块的存储介质、播放状态、播放模式、EQ 模式、DAC 通道等参数封装为常量（如 DISK_SD、PLAY_PLAY、EQ_ROCK），避免魔法数字，提升代码可读性与可维护性。

### 2. 接口分层封装

- 基础层：封装 play()/pause()/stop()等核心播放控制方法，简化基础操作；
- 进阶层：提供插播、组合播放、区间复读等高级功能方法，覆盖复杂交互场景；
- 监测层：实现播放状态、曲目、时间等查询方法，支持自动上报播放时间，便于状态监控；
- 配置层：封装音量、EQ、播放模式等配置方法，统一参数设置入口。

### 3. 易用性优化

- 初始化时支持默认参数配置（默认音量、盘符、播放模式等），减少重复代码；
- 内置超时机制，避免通信阻塞；
- 方法参数清晰，返回值标准化（如播放时间返回(h,m,s)元组），降低使用门槛。

## 使用说明

### 1. 硬件接线

- UART 连接：模块 MRX → 主控板 RXD 引脚，模块 MTX → 主控板 TXD 引脚；
- 供电连接：模块 VCC 接 3.3V/5V，GND 接主控板 GND，确认电源指示灯 LED1 常亮；
- 音频输出：SPK+、SPK-引脚连接喇叭，无需额外功放；
- 初始化连接：首次使用通过 Mini-USB 线连接模块与上位机，完成音频文件下载。

### 2. 软件初始化

1. 初始化 UART：配置波特率 9600，指定 TX/RX 引脚，匹配模块通信参数；
2. 实例化 DYSV19T 类：设置默认音量、盘符、播放模式等参数，配置通信超时时间；
3. （可选）初始化定时器：用于监测播放进度、自动上报的播放时间等。

### 3. 核心操作

1. 基础控制：调用 play()/pause()/stop()控制播放状态，select_track()指定曲目播放；
2. 参数配置：调用 set_volume()/set_eq()/set_play_mode()调整播放参数；
3. 状态查询：调用 query_status()/query_current_track()获取播放状态；
4. 高级功能：调用 insert_track()实现插播，repeat_area()实现区间复读等。

## 示例程序

```python
from machine import UART, Pin, Timer
import time
from dy_sv19t import *

def tick(timer):
    """定时器回调，监测播放进度"""
    hms = player.check_play_time_send()
    if hms:
        h, m, s = hms
        print("[auto time] h:m:s =", h, m, s)

# 初始化配置
time.sleep(3)
print("FreakStudio:  DY-SV19T Play Test ")

# 初始化UART（波特率9600，TX=GP16，RX=GP17）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))

# 初始化定时器（1秒触发一次进度监测）
tim = Timer(-1)
tim.init(period=1000, mode=Timer.PERIODIC, callback=tick)

# 创建播放器实例
player = DYSV19T(
    uart,
    default_volume=DYSV19T.VOLUME_MAX,
    default_disk=DYSV19T.DISK_SD,
    default_play_mode=DYSV19T.MODE_SINGLE_STOP,
    default_dac_channel=DYSV19T.CH_MP3,
    timeout_ms=600,
)

# 基础设置
player.set_volume(20)          # 设置音量20
player.set_eq(player.EQ_ROCK)  # 设置EQ为摇滚
player.set_play_mode(player.MODE_SINGLE_STOP)  # 设置播放模式
player.set_dac_channel(player.CH_MP3)  # 设置输出通道

# 状态查询
player.query_status()
player.query_current_disk()
player.query_current_track()
player.query_current_track_time()
player.query_short_filename()
player.query_total_tracks()
player.query_folder_first_track()
player.query_folder_total_tracks()
player.query_online_disks()

# 使能播放时间上报
player.enable_play_time_send()
player.play()

# 示例演示（按需启用）
# play_track_demo()          # 按路径播放音频
# select_and_play_demo()     # 选择曲目并控制播放
# repeat_area_demo()         # 区间复读
# insert_track_demo()        # 插播音频
# combination_playlist_demo() # 组合播放
# loop_mode_demo()           # 循环模式设置
```

### 示例说明

1. UART 初始化：配置 UART0，波特率 9600，TX/RX 引脚与模块 MRX/MTX 对应连接；
2. 播放器初始化：设置默认音量、盘符、播放模式和输出通道，配置 600ms 通信超时；
3. 基础控制：调整音量、EQ 模式、播放模式等参数，查询各类播放状态信息；
4. 状态监测：启用播放时间自动上报，通过 1 秒定时器回调实时打印播放进度；
5. 扩展演示：预留插播、组合播放、区间复读等高级功能的调用入口，按需启用。

## 注意事项

1. UART 连接规范：

   - 模块 MRX → MCU RXD，模块 MTX → MCU TXD，严禁交叉连接，否则通信失败；
   - 波特率固定为 9600 8N1，不可修改；
2. 首次使用初始化：必须通过 Mini-USB 线连接模块和上位机，使用专用软件完成初始化，否则无法正常工作；
3. 音频文件规范：

   - 文件名仅支持 A-Z、0-9、_，路径以/开头，文件夹名长度 1~8 字节；
   - 组合播放（ZH 文件夹）的音频文件需命名为 2 字节短名（如 Z1、Z2）；
4. 播放模式兼容性：仅 MODE_FULL_LOOP、MODE_SINGLE_LOOP、MODE_DIR_LOOP、MODE_SEQUENCE 支持设置循环次数，其他模式会抛出参数错误；
5. 插播与组合播放：插播会中断当前播放，组合播放需提前将音频文件放入 ZH 文件夹并按短名命名；
6. 电源稳定性：模块供电需稳定，避免电压波动导致音质失真或播放异常。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2025 FreakStudio

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
