# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 CST816 触摸驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time

from cst816 import CST816, GESTURE_NONE, GESTURE_UP, GESTURE_DOWN
from cst816 import GESTURE_LEFT, GESTURE_RIGHT, GESTURE_CLICK
from cst816 import GESTURE_DOUBLE_CLICK, GESTURE_LONG_PRESS

# ======================================== 全局变量 ============================================

# 引脚配置（请根据实际接线修改）
SCL_PIN = 22  # I2C 时钟引脚
SDA_PIN = 21  # I2C 数据引脚
I2C_FREQ = 400000  # I2C 频率（Hz）
RST_PIN = 25  # 复位引脚（可选，设为 None 禁用）
IRQ_PIN = 26  # 中断引脚（可选，设为 None 禁用）

# CST816 默认 I2C 地址（0x15，与 FT 系列 0x38 不同）
CST816_ADDR = 0x15

# 触摸屏分辨率
TOUCH_WIDTH = 240
TOUCH_HEIGHT = 240

# 打印间隔（ms）
PRINT_INTERVAL = 500

# 手势名称映射表
GESTURE_NAMES = {
    GESTURE_NONE: "none",
    GESTURE_UP: "up",
    GESTURE_DOWN: "down",
    GESTURE_LEFT: "left",
    GESTURE_RIGHT: "right",
    GESTURE_CLICK: "click",
    GESTURE_DOUBLE_CLICK: "double_click",
    GESTURE_LONG_PRESS: "long_press",
}

# I2C 设备扫描相关
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================


def gesture_name(gesture):
    """
    将手势常量转换为可读名称。

    Args:
        gesture (int): 手势常量值

    Returns:
        str: 手势名称
    ==========================================
    Convert gesture constant to readable name.

    Args:
        gesture (int): Gesture constant value

    Returns:
        str: Gesture name
    """
    return GESTURE_NAMES.get(gesture, "unknown(%d)" % gesture)


# ======================================== 自定义类 ============================================

# （本测试文件不需要自定义类）

# ======================================== 初始化配置 ==========================================

# 等待设备就绪
time.sleep(3)

print("FreakStudio: CST816/CST816S/CST816T/CST816D touch driver test")
print("")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: scl=%d, sda=%d, freq=%d" % (SCL_PIN, SDA_PIN, I2C_FREQ))

# I2C 设备扫描
# 注意：CST816 在屏幕未触摸时可能不响应 I2C，扫描列表中可能找不到设备
# 触摸屏幕后再运行扫描可提高发现几率
print("Scanning I2C bus...")
devices = i2c.scan()
if devices:
    print("I2C devices found: %s" % [hex(d) for d in devices])
else:
    print("No I2C devices found in scan")
    print("Note: CST816 may not respond to I2C when screen is untouched")
    print("Try touching the screen and re-run the scan")

# 检查目标地址
if CST816_ADDR in devices:
    print("CST816 found at address 0x%02X" % CST816_ADDR)
else:
    print("CST816 not found at expected address 0x%02X" % CST816_ADDR)
    print("This is expected if screen is untouched - CST816 may not appear in scan")

# 初始化复位引脚（若配置）
rst_pin = None
if RST_PIN is not None:
    rst_pin = Pin(RST_PIN, Pin.OUT, value=1)
    print("Reset pin configured: GPIO%d" % RST_PIN)

# 初始化中断引脚（若配置）
irq_pin = None
if IRQ_PIN is not None:
    irq_pin = Pin(IRQ_PIN, Pin.IN)
    print("Interrupt pin configured: GPIO%d" % IRQ_PIN)

# 创建 CST816 驱动实例
touch = CST816(
    i2c,
    address=CST816_ADDR,
    reset_pin=rst_pin,
    irq_pin=irq_pin,
    width=TOUCH_WIDTH,
    height=TOUCH_HEIGHT,
    debug=False,
)
print("CST816 driver initialized")
print("")

# 尝试读取芯片信息
# CST816 在未触摸时可能不响应 I2C，读取结果可能为 None
# 触摸屏幕后再读取可提高成功率
try:
    chip_id = touch.read_chip_id()
    if chip_id is not None:
        print("Chip ID: 0x%02X" % chip_id)
    else:
        print("Chip ID: read failed (screen may be untouched)")
except Exception as e:
    print("Chip ID read error: %s" % str(e))

try:
    revision = touch.read_revision()
    if revision is not None:
        print("Firmware revision: 0x%02X (%d)" % (revision, revision))
    else:
        print("Firmware revision: read failed (screen may be untouched)")
except Exception as e:
    print("Firmware revision read error: %s" % str(e))

print("")
print("Touch polling started. Touch the screen to see data.")
print("Press Ctrl+C to exit.")
print("")

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 读取触摸点数据
        point = touch.read_point()

        # 定时打印状态信息
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            if point is not None:
                # 有触摸数据，打印坐标和手势
                g_name = gesture_name(point["gesture"])
                print("Touch: x=%d, y=%d, gesture=%s, event=%d, count=%d" % (point["x"], point["y"], g_name, point["event"], touch.get_touch_count()))
            else:
                # 无触摸数据
                is_touched = touch.touched()
                print("Touch: idle, touched=%s, count=%d" % (str(is_touched), touch.get_touch_count()))

            last_print_time = current_time

        # 短暂延时，降低 CPU 占用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    touch.deinit()
    del touch
    print("Program exited")
