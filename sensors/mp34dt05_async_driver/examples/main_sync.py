# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 MP34DT05 MEMS 麦克风驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin
from mp34dt05 import MP34DT05

# ======================================== 全局变量 ============================================
# 缓冲区处理计数
buffer_processed_count = 0
# 缓冲区处理完成标志
buffer_ready = False
# 就绪的缓冲区索引
ready_buffer_idx = 0

# 数据打印间隔（ms）
print_interval = 2000
# 上次打印时间戳（ms）
last_print_time = 0
mic = None


# ======================================== 功能函数 ============================================
def buffer_handler(idx: int):
    """
    缓冲区就绪回调函数
    当 PDM 采样填满一个缓冲区后，通过 micropython.schedule 调用此函数
    Args:
        idx (int): 就绪的缓冲区索引（0 或 1）
    Notes:
        - 在 micropython.schedule 调度上下文中执行（非 ISR）
        - 应在此函数中调用 get_buffer(idx) 获取数据进行处理
    """
    global buffer_processed_count, buffer_ready, ready_buffer_idx
    # 递增缓冲区处理计数
    buffer_processed_count += 1
    # 设置就绪标志，供主循环读取
    buffer_ready = True
    ready_buffer_idx = idx


def do_stop():
    """停止采样（模式切换，默认注释调用，可 REPL 手动触发）"""
    mic.stop()
    print("Microphone sampling stopped")


def do_start():
    """恢复采样（模式切换，默认注释调用，可 REPL 手动触发）"""
    mic.start()
    print("Microphone sampling resumed")


# ======================================== 自定义类 ============================================
# 无自定义类，全部逻辑在主程序中

# ======================================== 初始化配置 ==========================================
# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing MP34DT05 MEMS microphone PDM driver...")

# 初始化 PDM 麦克风引脚
# PDM 时钟引脚（Arduino Nano RP2040 Connect: GPIO23）
pdm_clk = Pin(23, Pin.OUT)
# PDM 数据引脚（Arduino Nano RP2040 Connect: GPIO22）
pdm_data = Pin(22, Pin.IN)

# 创建 MP34DT05 驱动实例，注册缓冲区就绪回调
mic = MP34DT05(pdm_clk, pdm_data, handler=buffer_handler, buf_len=1024)

# 启动 PDM 采样
print("Starting PDM sampling...")
mic.start()
print("Microphone ready, buffer_handler will be called when data is available")

# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频读取：打印采样统计信息
            print("Buffers processed: %d | Active: %s" % (buffer_processed_count, mic.is_active))
            last_print_time = current_time

        # 检查是否有缓冲区就绪
        if buffer_ready:
            buffer_ready = False
            # 获取就绪的缓冲区数据进行处理
            buf = mic.get_buffer(ready_buffer_idx)
            # 计算缓冲区中音频样本的平均幅值（简单统计）
            if len(buf) > 0:
                # 计算样本 DC 偏置（PDM 空闲值约为 128）
                avg = sum(buf) // len(buf)
                print("Buffer[%d] ready, avg=%d (len=%d)" % (ready_buffer_idx, avg, len(buf)))

        # 以下为模式切换函数，默认注释执行，可 REPL 手动调用
        # do_stop()               # 停止采样，REPL 手动触发
        # do_start()              # 恢复采样，REPL 手动触发

        # 短延时降低 CPU 占用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    mic.stop()
    mic.deinit()
    mic = None
    print("Program exited")
