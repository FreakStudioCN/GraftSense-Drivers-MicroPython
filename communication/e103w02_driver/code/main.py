# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/8/20
# @Author  : FreakStudio
# @File    : main.py
# @Description : E103-W02参数查询与AP TCP Server透明传输示例，适配Raspberry Pi Pico
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.x"

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于上电延时和循环发送间隔
import time

# 从machine模块导入引脚和UART串口控制类
from machine import Pin, UART

# 导入E103-W02驱动类
from e103w02 import E103W02

# ======================================== 全局变量 ============================================

# UART0串口配置，适配当前项目RP2040的GP16/GP17接线
UART_ID = 0
UART_BAUDRATE = 115200
UART_TX_PIN = 16
UART_RX_PIN = 17

# 透明传输测试参数
SEND_INTERVAL_SECONDS = 2
RECEIVE_TIMEOUT_MS = 1500

# 所有会修改模块配置或状态的操作默认锁定
RUN_CONFIGURATION_TESTS = False
RUN_UART_CONFIGURATION_TEST = False
RUN_RESET_TEST = False
RUN_FACTORY_RESTORE_TEST = False
RUN_RAW_COMMAND_TEST = False
RUN_READLINE_TEST = False

TEST_SSID = "YOUR_WIFI_SSID"
TEST_PASSWORD = "YOUR_WIFI_PASSWORD"
TEST_REMOTE_IP = "192.168.1.100"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保RP2040和E103-W02模块完成上电初始化
time.sleep(3)
print("FreakStudio: Initialize E103-W02 module and hardware")

# 当前载板接口命名以主控为基准：GP16连接MTX，GP17连接MRX
uart = UART(
    UART_ID,
    baudrate=UART_BAUDRATE,
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(UART_TX_PIN),
    rx=Pin(UART_RX_PIN),
    timeout=0,
)

# 创建E103-W02驱动对象；构造过程不会发送AT指令
wifi = E103W02(uart)

# ========================================  主程序  ============================================

try:
    # 使用官方+++转义序列从透明传输模式进入AT模式
    wifi.enter_command_mode()
    try:
        # 查询模块基本信息
        print("[E103-W02 Version]: %s" % wifi.get_version())
        print("[E103-W02 Device SN]: %s" % wifi.get_device_sn())
        print("[E103-W02 MAC]: %s" % wifi.get_mac())
        print("[E103-W02 All State]: %s" % wifi.get_all_state())

        # 查询当前Wi-Fi与网络配置，不修改模块持久参数
        print("[E103-W02 Status]: %s" % wifi.get_status())
        print("[E103-W02 Role]: %s" % wifi.get_role())
        print("[E103-W02 STA]: %s" % wifi.get_sta())
        print("[E103-W02 STA IP]: %s" % wifi.get_sta_ip())
        print("[E103-W02 AP]: %s" % wifi.get_ap())
        print("[E103-W02 AP IP]: %s" % wifi.get_ap_ip())
        print("[E103-W02 AP Channel]: %s" % wifi.get_ap_channel())
        print("[E103-W02 Run Mode]: %s" % wifi.get_mode())
        print("[E103-W02 Socket]: %s" % wifi.get_socket())
        print("[E103-W02 UART]: %s" % wifi.get_uart_config())
        print("[E103-W02 Driver AT Mode]: %s" % wifi.is_command_mode())

        if RUN_RAW_COMMAND_TEST:
            print("[E103-W02 Raw]: %s" % wifi.send_command("AT+VER=?"))

        if RUN_CONFIGURATION_TESTS:
            if TEST_SSID == "YOUR_WIFI_SSID" or TEST_PASSWORD == "YOUR_WIFI_PASSWORD":
                raise ValueError("replace configuration placeholders before unlocking tests")
            print(wifi.set_role(E103W02.ROLE_STA))
            print(wifi.set_mode(E103W02.MODE_NORMAL))
            print(wifi.set_sta(TEST_SSID, E103W02.SECURITY_WPA2, TEST_PASSWORD))
            print(wifi.set_sta_ip(E103W02.IP_MODE_DHCP, "192.168.1.200", "255.255.255.0", "192.168.1.1", "192.168.1.1"))
            print(wifi.set_ap("E103_W02_TEST", E103W02.SECURITY_WPA2, "change_me_123"))
            print(wifi.set_ap_ip("192.168.1.1", "255.255.255.0", "192.168.1.1", "192.168.1.1"))
            print(wifi.set_ap_channel(11))
            print(wifi.set_socket(E103W02.PROTOCOL_TCP, E103W02.SOCKET_CLIENT, TEST_REMOTE_IP, 8889, 8887))

        if RUN_UART_CONFIGURATION_TEST:
            print(wifi.set_uart_config(115200, 8, 0, 1))

        if RUN_FACTORY_RESTORE_TEST:
            print(wifi.restore_factory_defaults(confirm=True))

        if RUN_RESET_TEST:
            print(wifi.reset(confirm=True))
    finally:
        # 查询结束后退出AT模式，恢复UART与网络之间的透明传输
        if wifi.is_command_mode():
            wifi.exit_command_mode()

    print("\nConnect the PC to the AP, then connect a TCP client to 192.168.1.1:8887")

    # 初始化消息计数器，用于区分每次透明传输的数据
    count = 1

    # 持续执行UART到TCP、TCP到UART的双向透明传输实验
    while True:
        # 构造带计数器和换行符的测试消息
        message = "E103-W02 message %d\r\n" % count

        # 通过UART将测试消息交给E103-W02透明发送至TCP客户端
        wifi.write(message)
        print("\n[Transparent TX]: %s" % message.strip())

        # 在限定时间内等待电脑端原样回传数据
        response = wifi.read(timeout_ms=RECEIVE_TIMEOUT_MS)
        if response:
            print("[Transparent RX]: %s" % response)
        else:
            print("[Transparent RX]: No data (check PC Wi-Fi and TCP client)")

        if RUN_READLINE_TEST:
            print("[Transparent Line]: %s" % wifi.readline(timeout_ms=RECEIVE_TIMEOUT_MS))

        # 更新计数器并等待下一次发送
        count += 1
        time.sleep(SEND_INTERVAL_SECONDS)
except KeyboardInterrupt:
    print("\nE103-W02 example stopped by user")
except OSError as exc:
    print("E103-W02 hardware error: %s" % exc)
except Exception as exc:
    print("E103-W02 example failed: %s" % exc)
finally:
    # 驱动不拥有外部UART对象，仅清理内部模式状态
    wifi.deinit()
    del wifi
    del uart
    print("E103-W02 example finished")
