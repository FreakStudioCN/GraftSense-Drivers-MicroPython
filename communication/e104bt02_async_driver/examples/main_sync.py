# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/18
# @Author  : FreakStudio
# @File    : main.py
# @Description : E104-BT02 basic query and transparent transfer example
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, UART

from e104bt02 import E104BT02, E104BT02Error

# ======================================== 全局变量 ============================================

UART_ID = 0
UART_TX_PIN = 16
UART_RX_PIN = 17
UART_BAUDRATE = 19200
UART_PARITY = None
UART_STOP_BITS = 1
MODE_RELEASE_WAIT_SECONDS = 15
TRANSPARENT_READ_TIMEOUT_MS = 200
LOOP_DELAY_SECONDS = 0.05
UART_TO_BLE_PAYLOAD = b"Hello from RP2040"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: E104-BT02 test")
print("Keep P06/WKP in the verified awake state.")
print("Hold MODE so P00/MOD is low for AT queries.")

# 使用已经通过真机验证的 RP2040 UART 接线。
uart0 = UART(
    UART_ID,
    baudrate=UART_BAUDRATE,
    tx=Pin(UART_TX_PIN),
    rx=Pin(UART_RX_PIN),
    parity=UART_PARITY,
    stop=UART_STOP_BITS,
)

# 将调用者创建的 UART 对象注入正式驱动。
module = E104BT02(uart0)

# ========================================  主程序 ============================================

try:
    # 配置模式下只执行具有代表性的安全查询。
    print("baudrate=%d" % module.get_baudrate())
    print("module_name=%s" % module.get_module_name())
    print("state=%s" % module.get_state())
    print("mtu=%d" % module.get_mtu())
    print("role=%s" % module.get_role())
    print("mac=%s" % module.get_mac())

    # MODE 由用户人工释放；等待时间只是示例操作窗口，不是官方时序。
    print("Release MODE now so P00/MOD becomes high.")
    print("Connect E104-BT02 from the BLE central.")
    print("Enable FFF1 Notify.")
    print("Use FFF2 Write to send BLE data to RP2040.")
    for remaining in range(MODE_RELEASE_WAIT_SECONDS, 0, -1):
        print("Transparent mode starts in %d second(s)." % remaining)
        time.sleep(1)

    # 进入透明阶段后不再发送任何 AT 查询。
    print("UART -> BLE")
    print("TX: %s" % repr(UART_TO_BLE_PAYLOAD))
    written = module.send(UART_TO_BLE_PAYLOAD)
    print("TX bytes: %d" % written)

    while True:
        # 使用有限超时读取，避免主循环永久阻塞。
        data = module.read(timeout_ms=TRANSPARENT_READ_TIMEOUT_MS)
        if data:
            print("BLE -> UART")
            print("RX: %s" % repr(data))
            print("RX bytes: %d" % len(data))

            # 将收到的数据原样回传，演示双向透明通信。
            print("UART -> BLE echo")
            print("TX: %s" % repr(data))
            echo_written = module.send(data)
            print("TX bytes: %d" % echo_written)
        time.sleep(LOOP_DELAY_SECONDS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as err:
    print("Hardware communication error: %s" % str(err))
except Exception as err:
    if isinstance(err, E104BT02Error):
        print("E104-BT02 driver error: %s" % str(err))
    else:
        print("Unexpected error: %s" % str(err))
finally:
    print("Cleaning up resources...")
    # 驱动只释放 UART 引用；UART 硬件由本示例负责关闭。
    module.close()
    uart0.deinit()
    del module
    del uart0
    print("Program exited")
