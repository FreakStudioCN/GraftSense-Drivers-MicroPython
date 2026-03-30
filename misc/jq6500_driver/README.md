# jq6500_driver - MicroPython JQ6500 语音模块驱动库

# jq6500_driver - MicroPython JQ6500 语音模块驱动库

---

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

jq6500_driver 是隶属于 **GraftSense-Drivers-MicroPython** 项目 misc 模块的 MicroPython 驱动库，专为 JQ6500 语音播放模块设计，提供轻量、高效的串口控制接口，兼容广泛的 MicroPython 芯片与固件版本，可快速实现语音播放、音量调节等功能。

## 主要功能

- 支持 JQ6500 语音模块的初始化与基础串口通信控制
- 提供播放、暂停、停止、音量调节、曲目切换等核心操作 API
- 无特定芯片与固件依赖，可在主流 MicroPython 设备上稳定运行
- 遵循 MIT 协议开源，允许自由使用、修改与分发

## 硬件要求

- **主控设备**：任意支持 MicroPython 的开发板（如 ESP32、RP2040、STM32 等）
- **语音模块**：JQ6500 系列语音播放模块（UART 串口通信版本）
- **连接配件**：杜邦线（用于连接开发板 UART 引脚与 JQ6500 模块）
- **电源**：3.3V 或 5V 电源（需匹配 JQ6500 模块供电规格）

## 文件说明

## 软件设计核心思想

1. **轻量高效**：代码精简，仅保留 JQ6500 模块核心通信与控制功能，适配 MicroPython 资源受限环境，减少内存与性能开销
2. **高度兼容**：通过 `package.json` 声明无特定芯片 / 固件依赖，确保在各类 MicroPython 设备上稳定运行
3. **模块化架构**：驱动逻辑与配置分离，符合 GraftSense-Drivers-MicroPython 项目整体规范，便于维护与功能扩展
4. **易用性优先**：封装底层串口指令操作，提供直观的上层 API，降低开发者使用门槛，快速实现语音播放功能

## 使用说明

1. 将 `code/jq6500.py` 文件上传至 MicroPython 开发板的文件系统
2. 在项目代码中导入 `jq6500` 模块
3. 根据硬件连接方式初始化 UART 串口（需匹配 JQ6500 模块波特率，通常为 9600）
4. 创建 JQ6500 驱动对象，调用 API 完成播放、音量调节等操作

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午3:30
# @Author  : rdagger
# @File    : main.py
# @Description : JQ6500播放器内部FLASH模式功能演示（精简版）

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin
from jq6500 import Player
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def demo_jq6500_flash():
    """
    JQ6500内部FLASH模式核心功能演示函数（精简版）
    Args:无

    Raises:
    Exception - 演示过程中出现的通用异常
    AttributeError - Player类中SRC_FLASH常量未定义时触发的异常

    Notes:
    1. 需提前将MP3文件烧录到JQ6500内部FLASH；
    2. 内部FLASH无文件夹功能，文件按烧录顺序编号；
    3. 已移除play_by_number方式，仅保留按索引播放

    ==========================================
    Core function demonstration for JQ6500 internal FLASH mode (simplified version)
    Args:None

    Raises:
    Exception - General exceptions during demonstration
    AttributeError - Exception triggered when SRC_FLASH constant is not defined in Player class

    Notes:
    1. MP3 files must be burned to JQ6500 internal FLASH in advance;
    2. Internal FLASH has no folder function, files are numbered in burning order;
    3. Removed play_by_number method, only keep playback by index
    """
    try:
        print("===== JQ6500 internal FLASH mode demonstration started =====")

        # 1. 基础配置（切换为内部FLASH音源）
        print("
【1. Basic configuration】")
        # 设置EQ为摇滚模式
        player.set_equalizer(Player.EQ_ROCK)
        print(f"Current EQ mode: {player.get_equalizer()} (2=Rock mode)")

        # 设置循环模式为单曲循环
        player.set_looping(Player.LOOP_ONE)
        print(f"Current looping mode: {player.get_looping()} (2=Single loop)")

        # 切换音源为内部FLASH（核心改动！替换SD卡为FLASH）
        player.set_source(Player.SRC_BUILTIN)  # SRC_BUILTIN为内部FLASH常量（需确认类中定义）
        print("Audio source switched to internal FLASH")

        # 2. 播放控制
        print("
【2. Playback control】")
        # 播放当前文件（默认从烧录的第一个文件开始）
        player.play()
        print("Start playback, current status:", player.get_status())  # 1=Playing
        time.sleep(3)  # 播放3秒

        # 暂停播放
        player.pause()
        print("Pause playback, current status:", player.get_status())  # 2=Paused
        time.sleep(2)

        # 恢复播放
        player.play()
        time.sleep(3)

        # 音量调节（加2次，减1次）
        player.volume_up()
        player.volume_up()
        player.volume_down()
        print(f"Current volume: {player.get_volume()} (Expected 16)")

        # 切换到下一曲（内部FLASH按烧录顺序切换）
        player.next()
        print("Switch to next track (Internal FLASH)")
        time.sleep(3)

        # 切换到上一曲
        player.prev()
        print("Switch to previous track (Internal FLASH)")
        time.sleep(3)

        # 3. 定位播放（内部FLASH按文件编号播放）
        print("
【3. Position playback】")

        # 按索引播放（和烧录顺序一致）
        player.play_by_index(file_index=1)
        print("Play internal FLASH file by index 1")
        time.sleep(3)

        # 4. 信息查询（适配内部FLASH）
        print("
【4. Device information query】")
        # 查询内部FLASH文件总数（替换SD卡为FLASH）
        print(f"Total files in internal FLASH: {player.get_file_count(Player.SRC_BUILTIN)}")
        print(f"Current file playback progress: {player.get_position()} seconds")
        print(f"Current file total duration: {player.get_length()} seconds")
        print(f"Firmware version: {player.get_version()}")

        # 5. 循环模式切换
        print("
【5. Looping mode switch】")
        player.set_looping(Player.LOOP_ALL)  # 全部循环
        print(f"Switched to all loop mode: {player.get_looping()} (0=All loop)")
        time.sleep(3)

        # 6. 重置与暂停
        player.pause()
        player.reset()  # 软复位
        print("
Demonstration ended, device paused and reset")

    except Exception as e:
        print(f"Error during demonstration: {e}")
    # 兼容处理：若Player类中SRC_FLASH未定义，用数值替代（通常FLASH=1，SD卡=2）
    except AttributeError:
        print("Tip: SRC_FLASH constant not defined, try replacing with value 1")
        player.set_source(1)  # 1=Internal FLASH，2=SD card (General value definition)

    finally:
        # 清理资源
        player.clean_up()
        uart.deinit()
        print("Resources cleaned up")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 初始化延迟，确保硬件就绪
time.sleep(3)
# 打印初始化完成提示
print("FreakStudio: JQ6500 internal FLASH playback demo initialization completed")

# 初始化UART（Raspberry Pi Pico的UART0，TX=16, RX=17，波特率固定9600）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17), timeout=100)

# 初始化JQ6500播放器，初始音量设为15（音量范围0-30）
player = Player(uart, volume=15)

# ========================================  主程序  ============================================

if __name__ == "__main__":
    demo_jq6500_flash()
while True:
    pass  # 主循环保持运行，等待用户操作或其他事件

```

_注：实际曲目编号与功能函数需以 __jq6500.py__ 中实现的 API 为准，以上为通用示例框架_

## 注意事项

1. **硬件接线**：确保开发板 UART TX/RX 引脚与 JQ6500 模块的 RX/TX 引脚交叉连接，且波特率与代码初始化参数一致
2. **电源规范**：JQ6500 模块需稳定供电，避免电压波动导致播放异常或硬件损坏
3. **SD 卡文件**：语音文件需提前存入 JQ6500 模块配套的 SD 卡，且文件名需按模块要求命名（如 0001.mp3）
4. **固件兼容**：本库无特定固件依赖，但需确保 MicroPython 固件支持 UART 串口通信功能
5. **时序控制**：发送指令后需预留适当延时，避免频繁操作导致模块响应异常

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源，完整协议内容如下：

```
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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
