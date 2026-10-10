# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/21 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 T-Deck Plus 板载 T-Keyboard 驱动（LILYGO ESP32-C3 I2C 键盘控制器）
# @License : MIT

# 导入相关模块
import time
from machine import I2C, Pin
from tdeck_keyboard import TDeckKeyboard

# 全局变量
# I2C 硬件引脚配置（LILYGO T-Deck/T-Deck Plus）
I2C_BUS = 0
PIN_SCL = 8
PIN_SDA = 18
I2C_FREQ = 400000

# 键盘 I2C 地址（ESP32-C3 控制器）
KEYBOARD_ADDR = 0x55

# 键盘供电引脚（可选，按实际硬件连接修改，None 表示不控制供电）
KEYBOARD_POWER_PIN = 10

# 定时打印间隔（ms）
last_print_time = 0
print_interval = 3000

# 功能函数


def test_keyboard_presence(kb):
    """检测键盘是否存在（低频，保留自动执行）"""
    try:
        present = kb.is_present()
        print("Keyboard at 0x%02X present: %s" % (KEYBOARD_ADDR, present))
        return present
    except Exception as e:
        print("Failed to detect keyboard: %s" % str(e))
        return False


def test_read_key(kb):
    """读取单个按键（低频，保留自动执行）"""
    try:
        key = kb.read_key()
        if key is not None:
            print("Key pressed: %s" % repr(key))
    except Exception as e:
        print("Failed to read key: %s" % str(e))


def test_keyboard_raw(kb):
    """Raw 矩阵模式读取（低频，默认注释调用，REPL 手动触发）"""
    try:
        kb.set_raw_mode()
        raw = kb.read_raw()
        keys = kb.pressed_keys(raw, include_special=True)
        print("Raw: %s | Keys: %s" % (list(raw), keys))
        kb.set_key_mode()
    except Exception as e:
        print("Failed to read raw matrix: %s" % str(e))


def test_backlight(kb, duty=128):
    """设置背光亮度（低频，默认注释调用，REPL 手动触发）"""
    try:
        kb.set_brightness(duty)
        print("Backlight set to %d" % duty)
    except Exception as e:
        print("Failed to set backlight: %s" % str(e))


# 自定义类

# 初始化配置
time.sleep(3)
print("FreakStudio: Testing T-Deck Plus T-Keyboard I2C driver")

# 预初始化变量，防止 finally 中 NameError
keyboard = None

# 初始化 I2C 总线
print("Initializing I2C bus %d (SCL=%d, SDA=%d, freq=%d)..." % (I2C_BUS, PIN_SCL, PIN_SDA, I2C_FREQ))
i2c = I2C(I2C_BUS, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=I2C_FREQ)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

if not devices:
    raise RuntimeError("No I2C device found on bus")

# 配置供电引脚（若使用）
power_pin = None
if KEYBOARD_POWER_PIN is not None:
    power_pin = Pin(KEYBOARD_POWER_PIN, Pin.OUT)

# 创建键盘驱动实例
print("Initializing T-Deck keyboard at address 0x%02X..." % KEYBOARD_ADDR)
keyboard = TDeckKeyboard(
    i2c,
    address=KEYBOARD_ADDR,
    power_pin=power_pin,
    startup_ms=100,
    debug=False,
)

# 键盘自检
print("Running keyboard self-test...")
if keyboard.self_test():
    print("Keyboard self-test passed (I2C communication OK)")
else:
    print("Keyboard self-test failed — check wiring and power")

print("T-Deck keyboard initialization successful!")

# 主程序
last_print_time = time.ticks_ms()

try:
    print("\n--- Keyboard Key Read Test ---")
    print("Press keys on the T-Deck keyboard...")

    main_loop_count = 0
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            main_loop_count += 1
            print("\n--- Main loop #%d ---" % main_loop_count)

            # 低频自动执行：检测设备存在性
            test_keyboard_presence(keyboard)

            last_print_time = current_time

        # 读取按键（非阻塞）
        test_read_key(keyboard)

        # 以下为高频/模式切换函数，默认注释执行，可 REPL 手动调用
        # test_keyboard_raw(keyboard)     # Raw 矩阵模式读取
        # test_backlight(keyboard, 200)   # 设置背光

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    try:
        if keyboard is not None:
            keyboard.deinit()
    except Exception:
        pass
    keyboard = None
    print("Program exited")
