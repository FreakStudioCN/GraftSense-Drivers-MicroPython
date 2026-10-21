# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/21 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 T-Deck Plus 板载轨迹球 GPIO 驱动
# @License : MIT

# 导入相关模块
import time
from tdeck_trackball import TDeckTrackball

# 全局变量
# 轨迹球 GPIO 引脚配置（按 LILYGO T-Deck 官方 UnitTest）
# 右方向: GPIO2  (BOARD_TBOX_G02)
PIN_RIGHT = 2
# 上方向: GPIO3  (BOARD_TBOX_G01)
PIN_UP = 3
# 左方向: GPIO1  (BOARD_TBOX_G04)
PIN_LEFT = 1
# 下方向: GPIO15 (BOARD_TBOX_G03)
PIN_DOWN = 15
# 中心按键: GPIO0 (BOARD_BOOT_PIN — 同时是 ESP32-S3 BOOT 引脚)
PIN_BUTTON = 0

# 定时打印间隔（ms）
last_print_time = 0
print_interval = 2000

# 功能函数


def test_trackball_poll(tb):
    """轮询轨迹球并打印位移（低频，保留自动执行）"""
    try:
        dx, dy, pressed = tb.poll()
        x, y = tb.position()
        print("Pos=(%d,%d) dXY=(%d,%d) pressed=%s" % (x, y, dx, dy, pressed))
    except Exception as e:
        print("Failed to poll trackball: %s" % str(e))


def test_trackball_self_test(tb):
    """GPIO 电平自检（低频，保留自动执行）"""
    try:
        ok = tb.self_test()
        print("Trackball GPIO self-test: %s" % ("PASS" if ok else "FAIL"))
    except Exception as e:
        print("Failed to run self-test: %s" % str(e))


# 自定义类

# 初始化配置
time.sleep(3)
print("FreakStudio: Testing T-Deck Plus Trackball GPIO driver")

# 预初始化变量，防止 finally 中 NameError
trackball = None

# 创建轨迹球驱动实例
print("Initializing T-Deck trackball (R=%d, U=%d, L=%d, D=%d, BTN=%d)..." % (PIN_RIGHT, PIN_UP, PIN_LEFT, PIN_DOWN, PIN_BUTTON))
trackball = TDeckTrackball(
    pin_right=PIN_RIGHT,
    pin_up=PIN_UP,
    pin_left=PIN_LEFT,
    pin_down=PIN_DOWN,
    pin_button=PIN_BUTTON,
    step=1,
    debounce_ms=5,
    debug=False,
)

# 轨迹球自检
print("Running trackball self-test...")
test_trackball_self_test(trackball)

print("T-Deck trackball initialization successful!")
print("Note: GPIO0 is also the BOOT pin — this driver only reads it as input.")

# 主程序
last_print_time = time.ticks_ms()

try:
    print("\n--- Trackball Polling Test ---")
    print("Move the trackball or press the center button...")

    main_loop_count = 0
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            main_loop_count += 1
            print("\n--- Main loop #%d ---" % main_loop_count)

            # 低频自动执行：轮询轨迹球
            test_trackball_poll(trackball)

            last_print_time = current_time

        # 轨迹球轮询（每次循环执行）
        trackball.poll()

        # 检测按键变化事件
        if trackball.button_changed():
            print("Button changed: pressed=%s" % trackball.pressed())

        time.sleep_ms(5)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    try:
        if trackball is not None:
            trackball.deinit()
    except Exception:
        pass
    trackball = None
    print("Program exited")
