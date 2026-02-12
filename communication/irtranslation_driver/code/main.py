# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:11
# @Author  : 缪贵成
# @File    : main.py
# @Description : nec_16协议基于树莓派pico的测试文件  已通过

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
import time
from machine import Pin
# 导入第三方驱动模块
from ir_tx.nec import NEC
# nec_16三个参数在回调函数中
from ir_rx.nec import NEC_16

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 如果使用nec_8需要传入不定长参数，，此处是nec_16
def ir_callback(addr: int, cmd: int, repeat: bool) -> None:
    """
    NEC 协议接收回调函数（3 参数版）。

    Args:
        addr (int): 接收到的地址
        cmd (int): 接收到的命令码
        repeat (bool): 是否为重复码 (True = 是, False = 否)

    Notes:
        回调函数由 NEC 接收模块调用，非 ISR-safe。
        输出接收到的数据到串口。

    ==========================================

    NEC IR signal receive callback (3-parameter version).

    Args:
        addr (int): Received address
        cmd (int): Received command
        repeat (bool): Repeat flag (True = yes, False = no)
    Notes:
        Called by NEC IR receiver. Not ISR-safe.
        Prints received data to REPL.
    """
    print(f"[RX] Address=0x{addr:04X}, Cmd=0x{cmd:02X}, Repeat={repeat}")

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio:Infrared transceiver test")

# 发射管接 GP6
TX_PIN = Pin(6, Pin.OUT)
# 接收头接 GP14
RX_PIN = Pin(14, Pin.IN)
# 38kHz 发射
ir_tx = NEC(TX_PIN, freq=38000)
# 接收 NEC
ir_rx = NEC_16(RX_PIN, ir_callback)
print("[System] Ready... TX=GP6, RX=GP14")

# ========================================  主程序  ===========================================
while True:
    print("[TX] Sending NEC signal...")
    # 地址=0x10, 命令=0x20
    ir_tx.transmit(0x10, 0x20)
    time.sleep(2)