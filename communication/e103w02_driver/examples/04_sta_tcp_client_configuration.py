# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/8/20
# @Author  : FreakStudio
# @File    : 04_sta_tcp_client_configuration.py
# @Description : E103-W02 STA Wi-Fi与TCP Client配置示例
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

WIFI_SSID = "YOUR_ROUTER_SSID"
WIFI_PASSWORD = "YOUR_ROUTER_PASSWORD"
DHCP_STA_IP = "192.168.1.200"
DHCP_MASK = "255.255.255.0"
DHCP_GATEWAY = "192.168.1.1"
DHCP_DNS = "192.168.1.1"
REMOTE_IP = "192.168.1.100"
REMOTE_PORT = 8889
LOCAL_PORT = 8887

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17), timeout=0)
device = E103W02(uart)

# ========================================  主程序  ============================================

try:
    if not APPLY_CONFIGURATION:
        print("Configuration is locked; edit the parameters and set APPLY_CONFIGURATION = True")
    elif WIFI_SSID == "YOUR_ROUTER_SSID" or WIFI_PASSWORD == "YOUR_ROUTER_PASSWORD":
        raise ValueError("replace the Wi-Fi placeholders before applying configuration")
    else:
        device.enter_command_mode()
        print(device.set_role(E103W02.ROLE_STA))
        print(device.set_sta(WIFI_SSID, E103W02.SECURITY_WPA2, WIFI_PASSWORD))
        # The official DHCP command syntax still requires all four address fields.
        print(device.set_sta_ip(E103W02.IP_MODE_DHCP, DHCP_STA_IP, DHCP_MASK, DHCP_GATEWAY, DHCP_DNS))
        print(
            device.set_socket(
                E103W02.PROTOCOL_TCP,
                E103W02.SOCKET_CLIENT,
                REMOTE_IP,
                REMOTE_PORT,
                LOCAL_PORT,
            )
        )
        print("Restarting E103-W02 to join Wi-Fi and open the TCP client")
        print(device.reset(confirm=True))
except KeyboardInterrupt:
    print("Example stopped by user")
except OSError as exc:
    print("E103-W02 hardware error: %s" % exc)
except Exception as exc:
    print("E103-W02 STA configuration failed: %s" % exc)
finally:
    device.deinit()
    del device
    del uart
    print("Example finished")
