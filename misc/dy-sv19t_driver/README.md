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
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

# 导入 UART 和 Pin 用于硬件串口与引脚配置
from machine import UART, Pin, Timer
# 导入 time 提供延时与时间控制
import time
# 导入驱动与常量（DYSV19T、VOLUME_MAX、DISK_*、MODE_*、CH_* 等）
from dy_sv19t import *

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def tick(timer):
    """
    定时器回调函数
    Args:
        timer:为监测播放进度条的定时器
    Raises:
        TypeError:计时器必须是Timer的一个实例

    ============================================================

    Args:
        timer: a timer used to monitor the playback progress bar
     Raises:
         TypeError:timer must be an instance of Timer
    """
    if not isinstance(timer, Timer):
        raise TypeError("timer must be an instance of Timer")
    # 查看播放进度方法
    hms = player.check_play_time_send()
    if hms:
        h, m, s = hms
        print("[auto time] h:m:s =", h, m, s)

def play_track_demo():
    """

    通过文件路径直接播放一段音频，监听播放进度并等待播放结束。

    ==========================================================

    Use the combined playback function to play multiple track combinations
    and end the combined playback after a specified time.

    """
    # 根据文件路径选择立即播放
    player.play_disk_path(player.DISK_SD, "/AA./01.MP3")
    # 开始监听播放进度
    player.enable_play_time_send()
    print("Enable automatic reporting of playback time, monitoring 3 times...")
    # 关闭监听播放进度
    # player.disable_play_time_send()

    # 等待结束
    while player.query_status():
        pass
    print("play_track_demo ends")

def select_and_play_demo():

    """
    选择曲目但不立即播放，并展示暂停、恢复、切换曲目的用法。

    ==========================================================

    Select a track without playing it immediately, and demonstrate the usage of pause,
    resume, and track switching.
    """
    # 根据文件路径选择不播放：曲目序号是由存储顺序决定！
    player.select_track(1, play=False)
    print("Select track 1 no play")
    # 5秒后播放曲目1
    time.sleep(5)
    # 开始播放之前当前选择的曲目
    player.play()

    # 暂停当前播放
    # player.pause()
    # time.sleep(4)

    # 恢复播放到“播放”状态
    # player.play()
    # time.sleep(2)

    # 跳转到下一曲目
    # player.next_track()
    # time.sleep(4)

    # 返回上一曲目
    # player.prev_track()
    # time.sleep(4)

    # 停止播放
    # player.stop()
    # 等待结束
    while player.query_status():
        pass
    print("play_track_demo ends")


def repeat_area_demo():
    """
    设置 A-B 区间复读，并在一段时间后关闭复读。
    ==========================================================
    Set the A-B interval for repeated reading and turn off the repeated reading after a period of time.
    """
    print("repeat_area_demo")
    # 设置 A-B 复读区间（起点分:秒，终点分:秒）
    player.select_track(4, play=False)
    # 播放
    player.play()
    # 设置复读从0分20秒到0分25秒截取复读
    player.repeat_area(0, 20, 0, 25)
    # 等待复读效果
    time.sleep(20)
    # 关闭复读效果
    player.end_repeat()
    # 等待复读关闭后效果
    time.sleep(20)
    # 停止播放
    player.stop()
    print("repeat_area_demo ends")

def loop_mode_demo():
    """
    设置循环播放模式，并指定循环次数。
    ==========================================================
    Set the loop playback mode and specify the number of loops.
    """
    # 设置播放模式支持循环次数设置
    player.set_play_mode(player.MODE_SINGLE_LOOP)
    # 设定循环次数为 3（注意部分模式不支持，若不支持会在驱动层抛参数错误）
    player.set_loop_count(3)
    # 播放第一段音频，立即播放
    player.select_track(1, play=True)
    time.sleep(10)
    # 设置播放模式为单曲停止
    player.set_play_mode(player.MODE_SINGLE_STOP)



def insert_track_demo():
    """
    在播放过程中插入另一段音频。
    Insert another audio segment during playback.
    """
    print("insert_track_demo")
    # 播放第四段音频，立即播放
    player.select_track(4, play=True)
    # 等待正常播放
    time.sleep(10)
    # 插入第一段音频
    player.insert_track(player.DISK_SD, 1)
    # 等待结束
    while player.query_status():
        pass
    print("insert_track_demo ends")


def combination_playlist_demo():
    """

    播放多个曲目组合，并在指定时间后结束组合播放。
    =========================================================
    Use the combined playback function to play multiple
    track combinations and end the combined playback after a specified time.

    """
    print("combination_playlist_demo")
    player.start_combination_playlist(['Z1', 'Z2'])
    # 留出 2 秒以便组合播放启动
    time.sleep(10)
    # 结束组合播放
    player.end_combination_playlist()
    print("combination_playlist_demo ends")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试消息
print("FreakStudio:  DY-SV19T Play Test ")
# 初始化硬件串口：选择 UART1，波特率 9600，TX=GP4，RX=GP5（需与模块连线一致）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建定时器
tim = Timer()
# 初始化定时器：每 1000ms（1秒）触发一次
tim.init(period=1000, mode=Timer.PERIODIC, callback=tick)
# 创建播放器实例：设定默认音量/盘符/模式/通道与读取超时
player = DYSV19T(
    # 传入已配置的 UART 实例
    uart,
    # 默认音量设置为最大（0~30）
    default_volume=DYSV19T.VOLUME_MAX,
    # 默认工作盘符选择 SD 卡
    default_disk=DYSV19T.DISK_SD,
    # 默认播放模式设置为“单曲播放后停止”
    default_play_mode=DYSV19T.MODE_SINGLE_STOP,
    # 默认输出通道设置为 MP3 通道
    default_dac_channel=DYSV19T.CH_MP3,
    # 串口读取超时 600ms
    timeout_ms=600,
)

# ========================================  主程序  ===========================================
# 将音量调整到 20（范围 0~30）
player.set_volume(20)
# 设置均衡为摇滚 EQ_ROCK
player.set_eq(player.EQ_ROCK)
# 设置循环模式为目录顺序播放后停止 MODE_DIR_SEQUENCE
player.set_play_mode(player.MODE_SINGLE_STOP)
# 选择输出通道为 MP3 数字通道
player.set_dac_channel(player.CH_MP3)
# 通过曲目序号直接播放一段音频，监听播放进度并等待播放结束。

player.query_status()
# 查询当前盘符：返回 DISK_USB/DISK_SD/DISK_FLASH 或 None，并更新内部 current_disk
player.query_current_disk()
# 查询当前曲目号：返回 1..65535 或 None
player.query_current_track()
# 查询当前曲目总播放时间：返回 (h,m,s) 或 None
player.query_current_track_time()
# 查询当前短文件名（8.3）：返回 ASCII 短名或 None
player.query_short_filename()
# 查询设备总曲目数：返回整数或 None
player.query_total_tracks()
# 查询当前文件夹首曲：返回曲目号或 None
player.query_folder_first_track()
# 查询当前文件夹曲目总数：返回整数或 None
player.query_folder_total_tracks()
# 查询在线盘符位图：bit0=USB, bit1=SD, bit2=FLASH
player.query_online_disks()

# 通过曲目序号直接播放一段音频，监听播放进度并等待播放结束。
play_track_demo()

# 选择曲目但不立即播放，并展示暂停、恢复、切换曲目的用法
select_and_play_demo()

# 设置 A-B 区间复读，并在一段时间后关闭复读。
repeat_area_demo()

# 在播放过程中插入另一段音频。
insert_track_demo()

# 播放多个曲目组合，并在指定时间后结束组合播放。
combination_playlist_demo()

# 设置循环播放模式，并指定循环次数。
loop_mode_demo()


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