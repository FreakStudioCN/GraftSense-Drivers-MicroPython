# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/8/20
# @Author  : FreakStudio
# @File    : 03_ap_configuration.py
# @Description : E103-W02 AP名称、密码及信道配置示例
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.x"

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, UART
from e103w02 import E103W02

# ======================================== 全局变量 ============================================

APPLY_CONFIGURATION = False

AP_SSID = "YOUR_E103_AP_SSID"
AP_SECURITY = E103W02.SECURITY_WPA2
AP_PASSWORD = "YOUR_E103_AP_PASSWORD"
AP_CHANNEL = 11

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17), timeout=0)
device = E103W02(uart)

# ========================================  主程序  ============================================

try:
    if not APPLY_CONFIGURATION:
        print("Configuration is locked; set APPLY_CONFIGURATION = True")
    elif AP_SSID == "YOUR_E103_AP_SSID" or AP_PASSWORD == "YOUR_E103_AP_PASSWORD":
        raise ValueError("replace the AP placeholders before applying configuration")
    else:
        device.enter_command_mode()
        print(device.set_role(E103W02.ROLE_AP))
        print(device.set_ap(AP_SSID, AP_SECURITY, AP_PASSWORD))
        print(device.set_ap_channel(AP_CHANNEL))
        print("Restarting E103-W02 to apply the AP configuration")
        print(device.reset(confirm=True))
        print("Reconnect the PC to the new AP: %s" % AP_SSID)
except KeyboardInterrupt:
    print("Example stopped by user")
except OSError as exc:
    print("E103-W02 hardware error: %s" % exc)
except Exception as exc:
    print("E103-W02 AP configuration failed: %s" % exc)
finally:
    device.deinit()
    del device
    del uart
    print("Example finished")
