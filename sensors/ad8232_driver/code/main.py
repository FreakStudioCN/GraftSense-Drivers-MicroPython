from machine import UART, Pin, Timer
import time
from data_flow_processor import DataFlowProcessor

# 初始化UART0：TX=16, RX=17，波特率115200
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)

# 创建DataFlowProcessor实例
processor = DataFlowProcessor(uart)