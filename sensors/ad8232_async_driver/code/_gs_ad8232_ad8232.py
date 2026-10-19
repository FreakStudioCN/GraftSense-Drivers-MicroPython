# Python env   : MicroPython v1.24.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : ad8232.py
# @Description : ad8232 模块驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.24 with ulab"

# ======================================== 导入相关模块 =========================================

from machine import ADC, Pin, Timer, UART
import time
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class AD8232:
    """
    AD8232心率传感器驱动类（适用于Raspberry Pi Pico）。

    该类提供AD8232心率传感器的完整驱动功能，支持模拟信号采集、导联脱落检测、
    传感器开关控制以及心率相关参数计算。通过ADC和GPIO接口与传感器通信。

    Attributes:
        MAX_BUFFER (int): 数据缓冲区最大长度常量。
        adc (ADC): ADC采集实例。
        loff_plus (Pin): 导联脱落检测正极引脚。
        loff_minus (Pin): 导联脱落检测负极引脚。
        sdn_pin (int/None): 传感器使能（SDN）引脚号。
        sdn (Pin): 传感器使能（SDN）控制引脚实例。
        prev_data (list): 历史数据缓冲区。
        sum_data (int): 数据总和。
        max_data (int): 最大数据值。
        avg_data (int): 平均数据值。
        roundrobin (int): 循环缓冲区索引。
        count_data (int): 数据计数。
        lead_status (bool): 导联连接状态（True表示脱落）。
        period (int): 心跳周期（毫秒）。
        last_period (int): 上一个心跳周期。
        millis_timer (int): 计时器毫秒值。
        frequency (float): 心率频率（Hz）。
        beats_per_min (float): 心率（次/分钟）。
        operating_status (int): 传感器工作状态（1:开，0:关，2:未知）。
        new_data (int): 最新采集的ADC原始数据。

    Methods:
        __init__(): 初始化AD8232传感器实例。
        off(): 关闭AD8232传感器。
        on(): 打开AD8232传感器。
        read_raw(): 读取原始ADC数据。
        check_leads_off(): 检查导联是否脱落。

    ==========================================

    AD8232 heart rate sensor driver class (for Raspberry Pi Pico).

    This class provides complete driver functionality for AD8232 heart rate sensor,
    supporting analog signal acquisition, lead-off detection, sensor power control,
    and heart rate parameter calculation. Communicates with sensor via ADC and GPIO interfaces.

    Attributes:
        MAX_BUFFER (int): Maximum data buffer length constant.
        adc (ADC): ADC acquisition instance.
        loff_plus (Pin): Lead-off detection positive pin.
        loff_minus (Pin): Lead-off detection negative pin.
        sdn_pin (int/None): Sensor Enable (SDN) pin number.
        sdn (Pin): Sensor Enable (SDN) control pin instance.
        prev_data (list): Historical data buffer.
        sum_data (int): Sum of data.
        max_data (int): Maximum data value.
        avg_data (int): Average data value.
        roundrobin (int): Circular buffer index.
        count_data (int): Data count.
        lead_status (bool): Lead connection status (True indicates detachment).
        period (int): Heartbeat period (milliseconds).
        last_period (int): Previous heartbeat period.
        millis_timer (int): Timer millisecond value.
        frequency (float): Heart rate frequency (Hz).
        beats_per_min (float): Heart rate (beats per minute).
        operating_status (int): Sensor operating status (1: on, 0: off, 2: unknown).
        new_data (int): Latest acquired ADC raw data.

    Methods:
        __init__(): Initialize AD8232 sensor instance.
        off(): Turn off AD8232 sensor.
        on(): Turn on AD8232 sensor.
        read_raw(): Read raw ADC data.
        check_leads_off(): Check if leads are detached.
    """

    def __init__(self, adc_pin=26, loff_plus_pin=16, loff_minus_pin=17, sdn_pin=None):
        """
        初始化AD8232心率传感器 (Pico版本)

        注意: Pico的ADC引脚是26-28 (GP26-28)，不是34
        参数:
            adc_pin: ADC输入引脚 (GP26, GP27, 或 GP28)
            loff_plus_pin: 导联脱落检测+ (GP16)
            loff_minus_pin: 导联脱落检测- (GP17)
            sdn_pin: 传感器使能(SDN)引脚，可选。用于控制传感器电源。

        ==========================================

        Initialize AD8232 heart rate sensor (Pico version)

        Note: Pico's ADC pins are 26-28 (GP26-28), not 34
        Args:
            adc_pin: ADC input pin (GP26, GP27, or GP28)
            loff_plus_pin: Lead-off detection + (GP16)
            loff_minus_pin: Lead-off detection - (GP17)
            sdn_pin: Sensor Enable (SDN) pin, optional. Used to control sensor power.
        """
        # ADC引脚初始化 (Pico的ADC)
        self.adc = ADC(Pin(adc_pin))
        # 导联脱落检测引脚
        self.loff_plus = Pin(loff_plus_pin, Pin.IN, Pin.PULL_UP)
        self.loff_minus = Pin(loff_minus_pin, Pin.IN, Pin.PULL_UP)

        self.sdn_pin = sdn_pin
        self.sdn = Pin(self.sdn_pin, Pin.OUT)

        # 数据缓冲区参数
        self.MAX_BUFFER = const(100)
        self.prev_data = [0] * self.MAX_BUFFER
        self.sum_data = 0
        self.max_data = 0
        self.avg_data = 0
        self.roundrobin = 0
        self.count_data = 0
        self.lead_status = False
        # 心率计算参数
        self.period = 0
        self.last_period = 0
        self.millis_timer = time.ticks_ms()
        self.frequency = 0.0
        self.beats_per_min = 0.0
        # 工作状态可能浮空，所以默认值是2 (未知)
        self.operating_status = 2
        # 数据采集状态
        self.new_data = 0

        print(f"AD8232 initialization complete - ADC pin: GP{adc_pin}")
        print(f"Lead detection: LO+ GP{loff_plus_pin}, LO- GP{loff_minus_pin}")
        print(f"SDN pin: {'Not configured' if sdn_pin is None else 'GP' + str(sdn_pin)}")

    def off(self):
        """
        关闭AD8232传感器 (如果有SDN引脚)

        注意:
            - 仅当初始化时提供了`sdn_pin`参数时此功能才有效。
            - 关闭传感器会将其工作状态（`operating_status`）设置为3。

        ==========================================

        Turn off AD8232 sensor (if SDN pin is configured)

        Note:
            - This function only works if the `sdn_pin` parameter was provided during initialization.
            - Turning off the sensor sets its operating status (`operating_status`) to 3.
        """
        if self.sdn_pin is not None:
            self.sdn.value(0)  # 设置为低电平关闭传感器
            self.operating_status = 3
            print("AD8232 sensor has been turned off")
        else:
            print("SDN pin is not configured, unable to turn off the sensor")

    def on(self):
        """
        打开AD8232传感器 (如果有SDN引脚)

        注意:
            - 仅当初始化时提供了`sdn_pin`参数时此功能才有效。
            - 打开传感器会将其工作状态（`operating_status`）设置为1。

        ==========================================

        Turn on AD8232 sensor (if SDN pin is configured)

        Note:
            - This function only works if the `sdn_pin` parameter was provided during initialization.
            - Turning on the sensor sets its operating status (`operating_status`) to 1.
        """
        if self.sdn_pin is not None:
            self.sdn.value(1)  # 设置为高电平打开传感器
            self.operating_status = 1
            print("The AD8232 sensor is turned on")
        else:
            print("The SDN pin is not configured, so the sensor cannot be turned on.")

    def read_raw(self):
        """
        读取原始ADC数据 (12位, 0-4095)
        对应Arduino: newData = analogRead(pin)

        返回:
            int: 12位ADC原始值 (0-4095)，存储在`self.new_data`属性中。

        ==========================================

        Read raw ADC data (12-bit, 0-4095)
        Corresponds to Arduino: newData = analogRead(pin)

        Returns:
            int: 12-bit ADC raw value (0-4095), stored in the `self.new_data` attribute.
        """
        self.new_data = self.adc.read_u16() >> 4  # 16位转12位 (0-4095)
        return self.new_data

    def check_leads_off(self):
        """
        检查导联是否脱落
        返回: True - 导联脱落, False - 正常连接

        工作原理:
            - 当导联正常连接时，两个引脚都是低电平(0)
            - 当导联脱落时，至少一个引脚是高电平(1)

        ==========================================

        Check if leads are detached
        Returns: True - leads detached, False - normal connection

        Working principle:
            - When leads are normally connected, both pins are low (0)
            - When leads are detached, at least one pin is high (1)
        """
        # 当导联正常连接时，两个引脚都是低电平(0)
        # 当导联脱落时，至少一个引脚是高电平(1)
        self.lead_status = self.loff_plus.value() == 1 or self.loff_minus.value() == 1
        return self.lead_status


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
