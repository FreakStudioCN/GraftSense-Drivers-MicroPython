# DS1232驱动 - MicroPython版本
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

DS1232 是一款单电源电压监控器与看门狗定时器（Voltage Supervisor/Watchdog），用于保证单片机或数字系统在电压异常或系统死锁时可靠复位。它集成了电压监测、手动复位输入、看门狗定时器以及可选复位延时输出，广泛应用于嵌入式系统、工业控制和安全关键电路。本项目提供基于 MicroPython 的驱动示例，便于快速检测复位信号和看门狗触发状态。

> **注意**：适用于 3.3V 或 5V 系统的电压监控，不可用于高精度 ADC 测量或模拟信号处理。

---

## 主要功能

* 电压监测：检测 Vcc 是否低于设定阈值，自动触发复位信号
* 看门狗功能：在 MCU 死锁或程序异常时自动复位系统
* 手动复位：通过外部按钮触发复位
* 输出状态监测：可通过 GPIO 读取复位状态或看门狗触发状态
* MicroPython 示例：可快速集成复位和状态检测功能

---

## 硬件要求

### 推荐测试硬件

* MicroPython 开发板（如树莓派 Pico）
* DS1232 芯片
* 杜邦线若干
* 复位按钮（可选）
* 电源 3.3V 或 5V

### 模块引脚说明

| DS1232 引脚 | 功能描述         | 连接说明                      |
| --------- | ------------ | ------------------------- |
| Vcc       | 电源输入         | 接开发板 3.3V 或 5V            |
| GND       | 接地           | 接开发板 GND                  |
| /RST      | 复位输出（低有效）    | 接 MCU 复位引脚，或外接 LED 观察状态   |
| WDI       | 看门狗输入        | MCU 定期脉冲信号，保持看门狗计时器不触发复位  |
| /WDO      | 看门狗输出        | 触发看门狗复位时输出低电平，可接 MCU /LED |
| MR        | 手动复位         | 外接按钮拉低触发复位                |
| Vbh/Vbl   | 电压检测阈值设置（可选） | 根据芯片规格设置分压电阻（可选）          |

---

## 文件说明
### ds1232.py

该文件实现 **DS1232 看门狗模块** 的核心驱动功能，仅包含 `DS1232` 类，用于控制外部 DS1232 芯片的喂狗和状态监控。

`DS1232` 类封装了 WDI 喂狗逻辑和 Timer 定时器控制，提供 MCU 周期性翻转 WDI 引脚以避免 DS1232 超时复位。类中包含两个主要属性：

* `wdi`：`machine.Pin` 实例，用于输出喂狗脉冲。
* `state`：当前 WDI 引脚输出状态（0 或 1）。

类的主要方法包括：

* `__init__(wdi_pin: int, feed_interval: int = 1000)`：初始化 DS1232 驱动，绑定 WDI 引脚并启动定时喂狗。
* `kick() -> None`：手动喂狗，立即翻转一次 WDI 引脚。
* `stop() -> None`：停止自动喂狗，将 WDI 引脚置低，触发 DS1232 超时复位。
* `_feed()`：内部方法，由 Timer 回调周期性调用，实现 ISR-safe 的 WDI 翻转逻辑。

---

### main.py

该文件为 DS1232 看门狗功能测试程序，无自定义类，仅包含程序入口逻辑。

核心功能：

* 初始化 WDI 与 RST 引脚
* 创建 `DS1232` 驱动实例并启动定时喂狗
* 配置 RST 引脚中断回调，用于检测 DS1232 复位触发
* 可通过定时器模拟喂狗失败，触发系统复位
* 无限循环中打印运行状态，并检查系统复位标志

程序特点：

* 支持手动喂狗与定时喂狗并存
* 可通过 `system_reset_flag` 检测复位事件
* 支持通过 Ctrl+C 安全停止程序并释放硬件资源

---

## 软件设计核心思想

* **模块化**：将看门狗控制、Timer 定时喂狗和复位检测拆分为独立方法，便于维护与扩展。
* **硬件解耦**：WDI 和 RST 引脚由应用层传入，驱动类不负责硬件初始化，兼容不同 MicroPython 开发板。
* **可靠性**：Timer 回调实现 ISR-safe 喂狗，确保 MCU 在正常运行状态下不被 DS1232 复位。
* **灵活性**：提供手动喂狗和自动喂狗接口，可用于测试、调试和实际系统保护。

---
好的，你希望把这段滑动变阻器的“使用说明”修改为 **DS1232 看门狗模块** 的版本。根据你之前提供的类和示例，我整理如下：

---

## 使用说明
### 硬件接线（树莓派 Pico 示例）

| DS1232 引脚 | Pico 引脚     | 接线功能                            |
| --------- | ----------- | ------------------------------- |
| Vcc       | 3.3V（Pin36） | 电源输入                            |
| GND       | GND（Pin38）  | 接地                              |
| WDI       | GP4（Pin6）   | 喂狗脉冲输出                          |
| RST       | GP5（Pin7）   | MCU复位输入（低电平触发，可接 LED 或 MCU复位引脚） |
| MR（可选）    | 外接按钮        | 手动触发复位                          |
| WDO（可选）   | GPx         | 看门狗输出状态监测                       |

### 软件依赖

* 固件：MicroPython v1.23+
* 内置库：`machine`（Pin/Timer控制）、`time`（延时）
* 开发工具：Thonny、PyCharm 等

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `ds1232.py` 和 `main.py` 到开发板
3. 根据实际接线修改 `main.py` 中 WDI、RST 引脚定义
4. 运行 `main.py`，观察：

   * WDI 脉冲周期性翻转（喂狗正常）
   * RST 引脚触发事件打印日志
   * 停止喂狗后 DS1232 超时复位 MCU（可通过 LED 或打印观察）

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/8/25 下午6:46   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 外部DS1232看门狗模块测试程序

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin, Timer
# 导入时间相关模块
import time

# 导入 DS1232 看门狗模块
from ds1232 import DS1232

# ======================================== 全局变量 ============================================

# DS1232 WDI 引脚连接的 GPIO
WDI_PIN = 4
# DS1232 RST 引脚连接的 GPIO
RST_PIN = 5
# 喂狗间隔，单位 ms
FEED_INTERVAL = 300
# 延迟停止喂狗时间，单位 ms
STOP_FEED_DELAY = 10000

# 定义全局变量
wdg = None
stop_feed_timer = None
# 全局标记：检测是否触发 RST
system_reset_flag = False

# ======================================== 功能函数 ============================================

def rst_callback(pin: Pin) -> None:
    """
    DS1232 RST 引脚触发回调函数。

    当 DS1232 芯片的 RST 引脚触发时调用，用于设置系统复位标志，
    由主循环检测该标志后执行复位逻辑。

    Args:
        pin (Pin): 触发该回调的 GPIO 引脚对象。

    Returns:
        None

    ==========================================

    Callback for DS1232 RST pin trigger.

    Called when the RST pin of DS1232 is triggered.
    Sets a system reset flag to be checked by the main loop.

    Args:
        pin (Pin): GPIO pin object that triggered the callback.

    Returns:
        None
    """
    # 声明全局变量
    global system_reset_flag

    # 设置标志，主循环检测后跳出
    system_reset_flag = True
    print("DS1232 RST pin triggered.")

def stop_feed_callback(t: Timer) -> None:
    """
    定时器回调：停止自动喂狗，模拟喂狗失败以触发复位。

    此函数在定时器到期时调用，用于停止看门狗喂养，并解除自身定时器。

    Args:
        t (Timer): 触发回调的定时器对象。

    Returns:
        None

    ==========================================

    Timer callback: stop automatic watchdog feeding to simulate failure.

    This function is called when the timer expires.  
    It stops feeding the watchdog and disables the timer itself.

    Args:
        t (Timer): Timer object that triggered the callback.

    Returns:
        None
    """
    # 声明全局变量
    global wdg, stop_feed_timer

    print("Stop feeding watchdog.")
    # 停止喂狗
    wdg.stop()
    # 停掉本定时器，只执行一次
    stop_feed_timer.deinit()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio:: DS1232 Watchdog Test Program.")

# 初始化 DS1232 看门狗
wdg = DS1232(wdi_pin=WDI_PIN, feed_interval=FEED_INTERVAL)
# 立即手动喂狗
wdg.kick()

# 配置 RST 引脚为输入，带上拉，触发回调
rst_pin = Pin(RST_PIN, Pin.IN, Pin.PULL_UP)
rst_pin.irq(trigger=Pin.IRQ_FALLING, handler=rst_callback)

# 定义定时器，延迟停止喂狗
stop_feed_timer = Timer()
stop_feed_timer.init(period=STOP_FEED_DELAY, mode=Timer.ONE_SHOT, callback=stop_feed_callback)

# ========================================  主程序  ===========================================

# 开始喂狗
print("Start feeding watchdog.")

try:
    # 无限循环
    while True:
        # 打印带时间的日志
        current_time = time.ticks_ms()
        print(f"System running... Time: {current_time} ms")

        # 检测 RST 触发标志
        if system_reset_flag:
            print("System starting reset...")
            # 跳出 while 循环
            break

        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted.")
finally:
    # 停止喂狗
    wdg.stop()
    # 停掉定时器
    stop_feed_timer.deinit()
```
---

## 注意事项

### 电气特性限制

* **电源电压**：DS1232 支持 3.0V\~5.5V 电源供电，超出该范围可能损坏芯片。请确保 Vcc 与 MCU 电源匹配。
* **引脚电平限制**：

  * WDI、MR、RST、WDO 引脚输入电压不得超过 Vcc，否则可能损坏芯片。
  * WDI 输出脉冲仅用于驱动 DS1232，看门狗定时器，不可直接驱动大电流负载。
* **脉冲频率**：WDI 喂狗频率应满足芯片规格要求，过慢会导致复位，过快无影响但浪费功耗。

### 硬件接线与配置注意事项

* **共地要求**：DS1232 的 GND 必须与 MCU/开发板 GND 可靠连接，否则复位逻辑可能失效或产生误触发。
* **接线可靠性**：WDI 和 RST 引脚需确保焊接或插接牢固，松动可能导致喂狗信号丢失或复位异常。
* **上拉/下拉**：

  * RST 输出低有效，可通过上拉电阻连接 Vcc，确保复位未触发时为高电平。
  * MR 手动复位输入可加上拉电阻，避免悬空导致误触发。
* **信号线长度**：WDI、MR、RST 信号线应尽量短且远离强干扰源（电机、继电器、开关电源），必要时可加 RC 滤波。

### 环境影响

* **温度限制**：DS1232 工作温度为 -40℃~~+85℃（工业级）或 0℃~~+70℃（商业级），请根据芯片型号选择。
* **湿度限制**：相对湿度 >85% RH 时，应避免引脚受潮，以防引起漏电流或复位异常。
* **粉尘与腐蚀防护**：长期暴露在灰尘或腐蚀性气体环境中可能导致引脚氧化或接触不良，建议使用防护外壳或涂覆防护涂层。
* **机械振动**：虽然 DS1232 为固态芯片，但过大机械振动可能影响焊接或 PCB 连接可靠性，应固定良好。

---
### 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

---
### 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  

**版权归 FreakStudio 所有。**