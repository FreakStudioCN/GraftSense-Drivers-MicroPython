# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/1 上午11:22
# @Author  : ben0i0d
# @File    : dht22.py
# @Description : dht22驱动文件
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"
__chip__ = "RP2040"

# ======================================== 导入相关模块 =========================================

import utime
from machine import Pin
from utime import *
from math import fabs
from rp2 import asm_pio, StateMachine, PIO

# ======================================== 全局变量 ============================================

_irq_count = 0
temp_data = bytearray([0 for i in range(5)])

EIGHT_1_BIT_MASK = const(0b11111111)
SEVEN_1_BIT_MASK = const(0b01111111)

# ======================================== 功能函数 ============================================

@asm_pio(set_init=PIO.OUT_HIGH, autopush=True, push_thresh=8)
def dht_get_data():
    """
    DHT 传感器 PIO 程序，用于通过状态机读取 40 位温湿度数据。

    Workflow:
        1. 等待 sm.put() 触发启动。
        2. 向 DHT 传感器发送起始低电平信号（至少 18ms）。
        3. 等待传感器的响应信号。
        4. 循环读取 40 位数据（5 个字节，每字节触发一次 IRQ）。
        5. 数据读取完成后，将数据引脚保持为高电平。

    Notes:
        - 每收到 8 位数据，会触发一次 IRQ，由 handle_dht_irq() 读取 FIFO。
        - 本程序利用计数寄存器 x、y 控制循环（x 用于位计数，y 用于字节计数）。
        - 由于 PIO 的精确时序，能够稳定解析 DHT11/DHT22 的信号。

    ==========================================

    PIO program for reading 40-bit data from a DHT sensor.

    Workflow:
        1. Wait for sm.put() to trigger start.
        2. Send initial low-level signal to the sensor (≥18ms).
        3. Wait for sensor response signal.
        4. Loop to read 40 bits (5 bytes, each triggers an IRQ).
        5. After reading completes, keep the data pin high.

    Notes:
        - Every 8 bits, an IRQ is triggered; handle_dht_irq() reads FIFO.
        - Register x is used for bit counting, y for byte counting.
        - PIO timing ensures stable communication with DHT11/DHT22.
    """
    
    # 等待 sm.put() 触发运行，否则一直等待
    pull()
    # y 用来计数字节
    set(y, 4)
    # 等待 8 次循环（当 x 到 0 时还会再执行一次，x-- 发生在 jmp 比较之后）
    set(x, 7)
    set(pindirs, 1)
    # 发送初始化信号，并保持低电平 9 个周期，总共 10 个周期
    set(pins, 0)[9]
    label('init_wait_loop')
    # nop 占 1 个周期，再等待 8 个周期，加上跳转指令本身 1 个周期，总共 10 个周期
    nop()[8]
    jmp(x_dec, 'init_wait_loop')
    
    # 等待初始化响应
    set(pindirs, 0)
    wait(1, pin, 0)
    wait(0, pin, 0)
    wait(1, pin, 0)
    
    # 开始读取传感器数据
    label('receive_new_byte')
    set(x, 7)
    label('receive_new_bit')
    wait(0, pin, 0)
    # 当引脚为高电平时再额外等待 2 个周期（共 3 个周期）。
    # 因此在 30us 后，直接将引脚电平值写入 ISR
    wait(1, pin, 0)[2]
    in_(pins, 1)
    jmp(x_dec, 'receive_new_bit')
    # 已经接收了 8 位数据，触发 IRQ 读取 FIFO，同时开始接收下一个字节
    irq(rel(0))
    jmp(y_dec, 'receive_new_byte')
    # 设置引脚为输出并拉高，让数据引脚保持高电平。
    # 这样下次拉低初始化信号时可以触发新的数据读取
    set(pindirs, 1)
    set(pins, 1)



def handle_dht_irq(sm):
    """
    DHT 中断回调函数，从 PIO FIFO 中读取 1 个字节数据并存入缓存。

    Args:
        sm (StateMachine): 触发中断的状态机对象。

    Notes:
        - 每接收 1 个字节（8 位）会触发一次 IRQ。
        - 数据按顺序写入 temp_data 缓存：
          [湿度高字节, 湿度低字节, 温度高字节, 温度低字节, 校验和]。
        - _irq_count 用于跟踪当前写入的字节索引。

    ==========================================

    DHT interrupt callback function, reads 1 byte from PIO FIFO into buffer.

    Args:
        sm (StateMachine): State machine that triggered the interrupt.

    Notes:
        - An IRQ is triggered for every received byte (8 bits).
        - Data is written sequentially into temp_data buffer:
          [humidity high, humidity low, temperature high, temperature low, checksum].
        - _irq_count keeps track of the current byte index.
    """
    global _irq_count, temp_data
    temp_data[_irq_count] = (sm.get())
    _irq_count += 1

# ======================================== 自定义类 ============================================

class DHT(object):
    def __init__(self, pin: Pin, state_machine_id: int = 0, min_interval: int = 2000):
        """
        DHT 传感器驱动，用于通过状态机读取温湿度数据。

        Attributes:
            _pin (Pin): 连接到 DHT 传感器数据引脚的 Pin 对象。
            _last_pull_time (int): 上一次成功获取数据的时间戳（ms）。
            _temperature (float): 最近一次测得的温度值（℃）。
            _humidity (float): 最近一次测得的湿度值（%）。
            _min_interval (int): 两次采集之间的最小间隔时间（毫秒）。
            _sm (StateMachine): PIO 状态机对象，用于和 DHT 传感器通信。

        Methods:
            __init__(pin: Pin, state_machine_id: int = 0, min_interval: int = 2000) -> None: 初始化 DHT 传感器通信。
            _get_data_from_sensor(force: bool = False) -> None: 从 DHT 传感器读取数据（内部方法）。
            get_temperature(force: bool = False) -> float: 获取温度值。
            get_humidity(force: bool = False) -> float: 获取湿度值。
            get_temperature_and_humidity(force: bool = False) -> (float, float): 同时获取温度和湿度。

        Notes:
            - 默认最小间隔 2000ms（适用于 DHT22）。DHT11 的推荐间隔更长。
            - 温度单位为摄氏度（℃），湿度为百分比（%）。
            - 数据校验采用校验和方式，若失败则返回 None。
            - 采集依赖 PIO 状态机，请确保相应固件支持。
        ==========================================

        DHT driver for reading temperature and humidity via state machine.

        Attributes:
            _pin (Pin): Pin object connected to the DHT sensor's data pin.
            _last_pull_time (int): Timestamp (ms) of the last successful data retrieval.
            _temperature (float): Last measured temperature (°C).
            _humidity (float): Last measured humidity (%).
            _min_interval (int): Minimum time interval between two reads (ms).
            _sm (StateMachine): PIO state machine object for handling DHT communication.

        Methods:
            __init__(pin: Pin, state_machine_id:# humidity data is 10x of actual value int = 0, min_interval: int = 2000) -> None: Initialize communication with DHT sensor.
            _get_data_from_sensor(force: bool = False) -> None: Retrieve data from DHT sensor (internal method).
            get_temperature(force: bool = False) -> float: Get temperature.
            get_humidity(force: bool = False) -> float: Get humidity.
            get_temperature_and_humidity(force: bool = False) -> (float, float): Get both temperature and humidity.

        Notes:
            - Default minimum interval is 2000ms (for DHT22). DHT11 requires longer intervals.
            - Temperature is in Celsius (°C), humidity in percentage (%).
            - Data validation uses checksum; if validation fails, returns None.
            - Data acquisition relies on PIO state machine; ensure firmware support.
        """
        self._pin = pin
        self._last_pull_time = None
        self._temperature = None
        self._humidity = None
        self._min_interval = min_interval
        # 1 个周期应为 10 微秒，1 秒 = 1,000,000 微秒，因此频率应为 100,000 Hz
        self._sm = StateMachine(state_machine_id, dht_get_data, freq=100000, set_base=pin)
        self._sm.irq(handle_dht_irq)
        self._sm.active(1)
    
    def _get_data_from_sensor(self, force: bool = False):
        """
        从 DHT 传感器读取一次完整的温湿度数据（内部方法）。

        Args:
            force (bool): 是否强制与传感器通信，忽略最小间隔限制。

        Returns:
            None: 采集结果直接更新到对象属性 `_temperature` 和 `_humidity`。
                如果校验失败或数据不足，属性保持 None。

        Notes:
            - 本方法为内部方法，用户一般通过 `get_temperature()`、`get_humidity()` 
            或 `get_temperature_and_humidity()` 间接调用。
            - 若 `_irq_count` != 5 或校验和不匹配，则采集失败。

        ==========================================

        Retrieve one full set of temperature and humidity data from the DHT sensor (internal method).

        Args:
            force (bool): Force communication with the sensor, ignoring the minimum interval limit.

        Returns:
            None: Results are stored in object attributes `_temperature` and `_humidity`.
                If checksum validation fails or data is incomplete, attributes remain None.

        Notes:
            - This is an internal method. Typically accessed indirectly via
            `get_temperature()`, `get_humidity()`, or `get_temperature_and_humidity()`.
            - If `_irq_count` != 5 or checksum does not match, the acquisition fails.
        """
        if force or self._last_pull_time is None or \
                fabs(ticks_diff(ticks_ms(), self._last_pull_time)) > self._min_interval:
            global _irq_count, temp_data
            _irq_count = 0
            for i in range(5):
                temp_data[i] = 0
            
            # 启动状态机
            self._sm.put(0)
            
            # 等待状态机工作完成
            utime.sleep_ms(20)
            
            if _irq_count != 5:
                print("Didn't receive enough data. Received {} byte(s).".format(len(temp_data)))
                return
            
            # 数据校验：第 1+2+3+4 个字节的和（低 8 位）应等于第 5 个字节
            check_sum = (temp_data[0] + temp_data[1] + temp_data[2] + temp_data[3]) & EIGHT_1_BIT_MASK
            if check_sum != temp_data[4]:
                print('Data validation error.')
                return
            
            # 温度数据占最后 15 位，若最高位为 1，则为负数。实际值为原始数据除以 10
            raw_temperature = ((temp_data[2] & SEVEN_1_BIT_MASK) << 8) + temp_data[3]
            self._temperature = raw_temperature / 10
            if temp_data[2] >> 7 == 1:
                self._temperature *= -1
            
            raw_humidity = (temp_data[0] << 8) + temp_data[1]
            # 湿度数据为原始值除以 10
            self._humidity = raw_humidity / 10
            
            self._last_pull_time = ticks_ms()
    
    def get_temperature(self, force: bool = False) -> float:
        """
        获取温度数据。

        Args:
            force (bool): 是否强制与传感器通信，忽略最小间隔限制。

        Returns:
            float: 最近一次测得的温度值（℃）。

        Notes:
            如果校验失败，返回值可能为 None。

        ==========================================

        Get temperature data.

        Args:
            force (bool): Force communication with the sensor, ignoring minimum interval.

        Returns:
            float: Last measured temperature in Celsius (°C).

        Notes:
            If checksum validation fails, the return value may be None.
        """
        self._get_data_from_sensor(force)
        return self._temperature
    
    def get_humidity(self, force: bool = False) -> float:
        """
        获取湿度数据。

        Args:
            force (bool): 是否强制与传感器通信，忽略最小间隔限制。

        Returns:
            float: 最近一次测得的湿度值（%）。

        Notes:
            如果校验失败，返回值可能为 None。

        ==========================================

        Get humidity data.

        Args:
            force (bool): Force communication with the sensor, ignoring minimum interval.

        Returns:
            float: Last measured humidity in percentage (%).

        Notes:
            If checksum validation fails, the return value may be None.
        """
        self._get_data_from_sensor(force)
        return self._humidity
    
    def get_temperature_and_humidity(self, force: bool = False) -> (float, float):
        """
        同时获取温度和湿度数据。

        Args:
            force (bool): 是否强制与传感器通信，忽略最小间隔限制。

        Returns:
            (float, float): 一个二元组，包含最近一次测得的温度（℃）和湿度（%）。

        Notes:
            如果校验失败，返回值可能为 (None, None)。

        ==========================================

        Get both temperature and humidity data.

        Args:
            force (bool): Force communication with the sensor, ignoring minimum interval.

        Returns:
            (float, float): A tuple containing the last measured temperature (°C) and humidity (%).

        Notes:
            If checksum validation fails, returns (None, None).
        """
        self._get_data_from_sensor(force)
        return self._temperature, self._humidity

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================