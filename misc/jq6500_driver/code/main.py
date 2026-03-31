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
        print("\n【1. Basic configuration】")
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
        print("\n【2. Playback control】")
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
        print("\n【3. Position playback】")

        # 按索引播放（和烧录顺序一致）
        player.play_by_index(file_index=1)
        print("Play internal FLASH file by index 1")
        time.sleep(3)

        # 4. 信息查询（适配内部FLASH）
        print("\n【4. Device information query】")
        # 查询内部FLASH文件总数（替换SD卡为FLASH）
        print(f"Total files in internal FLASH: {player.get_file_count(Player.SRC_BUILTIN)}")
        print(f"Current file playback progress: {player.get_position()} seconds")
        print(f"Current file total duration: {player.get_length()} seconds")
        print(f"Firmware version: {player.get_version()}")

        # 5. 循环模式切换
        print("\n【5. Looping mode switch】")
        player.set_looping(Player.LOOP_ALL)  # 全部循环
        print(f"Switched to all loop mode: {player.get_looping()} (0=All loop)")
        time.sleep(3)

        # 6. 重置与暂停
        player.pause()
        player.reset()  # 软复位
        print("\nDemonstration ended, device paused and reset")

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
