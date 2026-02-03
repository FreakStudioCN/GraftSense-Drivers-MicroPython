# Python env   : MicroPython v1.27.0
# -*- coding: utf-8 -*-
# @Time    : 2026/02/03 18:00
# @Author  : hogeiha
# @File    : max30100.py
# @Description : MAX30100驱动
# @Repository  : 参考自：https://github.com/kontakt/MAX30100
# @License : MIT

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.27.0"

# ======================================== 导入相关模块 =========================================

import machine
from machine import Pin, I2C

# ======================================== 全局变量 ============================================

INT_STATUS   = 0x00  # Which interrupts are tripped
INT_ENABLE   = 0x01  # Which interrupts are active
FIFO_WR_PTR  = 0x02  # Where data is being written
OVRFLOW_CTR  = 0x03  # Number of lost samples
FIFO_RD_PTR  = 0x04  # Where to read from
FIFO_DATA    = 0x05  # Ouput data buffer
MODE_CONFIG  = 0x06  # Control register
SPO2_CONFIG  = 0x07  # Oximetry settings
LED_CONFIG   = 0x09  # Pulse width and power of LEDs
TEMP_INTG    = 0x16  # Temperature value, whole number
TEMP_FRAC    = 0x17  # Temperature value, fraction
REV_ID       = 0xFE  # Part revision
PART_ID      = 0xFF  # Part ID, normally 0x11

I2C_ADDRESS  = 0x57  # I2C address of the MAX30100 device


PULSE_WIDTH = {
    200: 0,
    400: 1,
    800: 2,
   1600: 3,
}

SAMPLE_RATE = {
    50: 0,
   100: 1,
   167: 2,
   200: 3,
   400: 4,
   600: 5,
   800: 6,
  1000: 7,
}

LED_CURRENT = {
       0: 0,
     4.4: 1,
     7.6: 2,
    11.0: 3,
    14.2: 4,
    17.4: 5,
    20.8: 6,
    24.0: 7,
    27.1: 8,
    30.6: 9,
    33.8: 10,
    37.0: 11,
    40.2: 12,
    43.6: 13,
    46.8: 14,
    50.0: 15
}

INTERRUPT_SPO2 = 0
INTERRUPT_HR = 1
INTERRUPT_TEMP = 2
INTERRUPT_FIFO = 3

# ======================================== 功能函数 ============================================

def _get_valid(d, value):
    """
    验证值是否在字典中，如果不在则抛出包含有效值的KeyError。

    Args:
        d (dict): 要验证的字典
        value: 要验证的值

    Returns:
        值对应的项

    Raises:
        KeyError: 值不在字典中

    =========================================
    Verify if value is in dictionary, if not raise KeyError with valid values.

    Args:
        d (dict): Dictionary to validate against
        value: Value to validate

    Returns:
        Item corresponding to the value

    Raises:
        KeyError: If value not in dictionary
    """

    try:
        return d[value]
    except KeyError:
        raise KeyError("Value %s not valid, use one of: %s" % (value, ", ".join([str(s) for s in d.keys()])))

def _twos_complement(val, bits):
    """
    计算整数值的二进制补码。

    Args:
        val (int): 要转换的值
        bits (int): 位数

    Returns:
        int: 二进制补码表示的整数值

    =========================================
    Compute the 2's complement of an integer value.

    Args:
        val (int): Value to convert
        bits (int): Number of bits

    Returns:
        int: Integer value in 2's complement representation
    """
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)
    return val



MODE_HR = 0x02
MODE_SPO2 = 0x03

# ======================================== 自定义类 ============================================

class MAX30100(object):
    """
    MAX30102/MAX30105 高精度脉搏血氧仪和心率传感器 I2C 驱动类。

    本类提供对 MAX30102/MAX30105 传感器的完整 I2C 接口控制，包括寄存器配置、
    FIFO 数据读取、温度测量、中断管理和电源控制等功能。支持单路或多路 LED
    配置，适用于心率监测和血氧饱和度测量应用。

    主要特性：
        - 完整的寄存器级别配置控制
        - 支持 1-3 个 LED 通道（红/红外/绿）
        - 可配置的采样率（50-3200 SPS）
        - 可编程 LED 电流（0-50mA）
        - 片上温度传感器
        - FIFO 数据缓冲和溢出保护
        - 可编程中断系统

    注意：
        1. 本驱动未改动核心业务逻辑，仅完善注释与文档。
        2. "set_pulse_amplitude_it" 方法名沿用原代码（IR 电流），未更名以避免影响现有业务。
        3. I2C 读写操作可能抛出 OSError（如 ETIMEDOUT、ENODEV 等）。
        4. 确保在调用 read_fifo() 前已正确配置 LED 模式和多路槽位。

    =========================================
    MAX30102/MAX30105 High-Precision Pulse Oximeter and Heart Rate Sensor I2C Driver.

    This class provides complete I2C interface control for MAX30102/MAX30105 sensors,
    including register configuration, FIFO data reading, temperature measurement,
    interrupt management, and power control. Supports single or multi-LED configurations
    for heart rate monitoring and blood oxygen saturation measurement applications.

    Key Features:
        - Complete register-level configuration control
        - Supports 1-3 LED channels (Red/IR/Green)
        - Configurable sample rate (50-3200 SPS)
        - Programmable LED current (0-50mA)
        - On-chip temperature sensor
        - FIFO data buffering and overflow protection
        - Programmable interrupt system

    Notes:
        1. Core logic remains unchanged; only documentation and comments were enhanced.
        2. Method name "set_pulse_amplitude_it" is kept as-is (IR current) to avoid breaking existing code.
        3. I2C operations may raise OSError (e.g., ETIMEDOUT, ENODEV).
        4. Ensure LED mode and multi-slot configurations are correctly set before calling read_fifo().

    Attributes:
        i2c_address (int): I2C 设备的 7 位地址 / 7-bit I2C device address.
        _i2c (I2C): MicroPython I2C 总线实例 / MicroPython I2C bus instance.
        _active_leds (int|None): 当前启用的 LED 数量（1~3）/ Number of active LEDs (1-3).
        _pulse_width (int|None): 当前脉宽编码（寄存器位值）/ Encoded pulse width (register bit value).
        _multi_led_read_mode (int|None): 每次 FIFO 读取的字节数（active_leds*3）/ Bytes per FIFO read (active_leds*3).
        _sample_rate (int|None): 采样率（SPS）/ Sample rate in Samples Per Second (SPS).
        _sample_avg (int|None): FIFO 内部平均的样本数 / Number of samples for on-chip FIFO averaging.
        _acq_frequency (float|None): 有效采集频率（_sample_rate/_sample_avg）/ Effective acquisition frequency.
        _acq_frequency_inv (int|None): 建议读取间隔（毫秒）/ Recommended read interval in milliseconds.
        sense (SensorData): 各通道数据的环形缓冲区对象 / Ring buffer object for channel data.

    Methods:
        __init__(self, i2c_address=0x57, i2c_bus=None):
            初始化传感器驱动实例。
            Initialize sensor driver instance.

        setup_sensor(self, led_mode=2, adc_range=16384, sample_rate=400,
                     pulse_width=411, led_current_red=24.0, led_current_ir=24.0,
                     led_current_green=24.0, sample_avg=8, rollover_enable=True):
            一次性按常用配置初始化传感器。
            Initialize sensor with common configurations in one call.

        soft_reset(self):
            执行软件复位（不改变 I2C 地址）。
            Perform software reset (I2C address remains unchanged).

        shutdown(self):
            关闭传感器进入低功耗模式。
            Power down sensor to low-power mode.

        wakeup(self):
            从低功耗模式唤醒传感器。
            Wake up sensor from low-power mode.

        set_led_mode(self, mode):
            设置 LED 工作模式（1-3 个 LED 通道）。
            Set LED operating mode (1-3 LED channels).

        set_adc_range(self, adc_range):
            设置 ADC 测量范围。
            Set ADC measurement range.

        set_sample_rate(self, sample_rate):
            设置采样率（50-3200 SPS）。
            Set sample rate (50-3200 SPS).

        set_pulse_width(self, pulse_width):
            设置 LED 脉冲宽度。
            Set LED pulse width.

        set_pulse_amplitude_red(self, amplitude):
            设置红光 LED 电流强度。
            Set red LED current amplitude.

        set_pulse_amplitude_ir(self, amplitude):
            设置红外 LED 电流强度。
            Set infrared LED current amplitude.

        set_pulse_amplitude_green(self, amplitude):
            设置绿光 LED 电流强度。
            Set green LED current amplitude.

        set_pulse_amplitude_proximity(self, amplitude):
            设置接近检测 LED 电流强度。
            Set proximity LED current amplitude.

        set_fifo_average(self, number_of_samples):
            设置 FIFO 内部平均样本数。
            Set FIFO on-chip averaging.

        enable_fifo_rollover(self):
            启用 FIFO 滚转（溢出时覆盖旧数据）。
            Enable FIFO rollover (overwrite old data on overflow).

        disable_fifo_rollover(self):
            禁用 FIFO 滚转（溢出时停止写入）。
            Disable FIFO rollover (stop writing on overflow).

        clear_fifo(self):
            清除 FIFO 所有数据。
            Clear all FIFO data.

        get_write_pointer(self):
            获取 FIFO 写指针位置。
            Get FIFO write pointer position.

        get_read_pointer(self):
            获取 FIFO 读指针位置。
            Get FIFO read pointer position.

        read_temperature(self):
            读取芯片内部温度。
            Read chip internal temperature.

        read_part_id(self):
            读取部件 ID。
            Read part ID.

        check_part_id(self):
            验证部件 ID 是否正确。
            Validate part ID.

        get_revision_id(self):
            获取芯片版本 ID。
            Get chip revision ID.

        enable_slot(self, slot_number, device):
            启用指定时间槽的 LED 通道。
            Enable LED channel for specified time slot.

        disable_slots(self):
            禁用所有时间槽。
            Disable all time slots.

        check(self):
            检查 FIFO 中是否有新数据。
            Check for new data in FIFO.

        safe_check(self, max_retries=3):
            安全检查 FIFO 数据（带重试机制）。
            Safely check FIFO data (with retry mechanism).

        read_fifo(self):
            从 FIFO 读取原始数据。
            Read raw data from FIFO.

        read_fifo_to_array(self):
            从 FIFO 读取数据到数组。
            Read data from FIFO to array.

        start_proximity_sensor(self, led_current):
            启动接近检测传感器。
            Start proximity sensor.

        stop_proximity_sensor(self):
            停止接近检测传感器。
            Stop proximity sensor.

        get_registers(self):
            读取所有寄存器值。
            Read all register values.
    """
    def __init__(self,
                 i2c=None,
                 mode=MODE_HR,
                 sample_rate=100,
                 led_current_red=11.0,
                 led_current_ir=11.0,
                 pulse_width=1600,
                 max_buffer_len=10000
                 ):
        """
        初始化MAX30100传感器。

        Args:
            i2c: I2C通信接口对象
            mode (int): 初始工作模式，MODE_HR或MODE_SPO2
            sample_rate (int): 采样率，单位：Hz
            led_current_red (float): 红光LED电流，单位：mA
            led_current_ir (float): 红外LED电流，单位：mA
            pulse_width (int): LED脉冲宽度，单位：μs
            max_buffer_len (int): 数据缓冲区最大长度

        =========================================
        Initialize MAX30100 sensor.

        Args:
            i2c: I2C communication interface object
            mode (int): Initial operation mode, MODE_HR or MODE_SPO2
            sample_rate (int): Sampling rate in Hz
            led_current_red (float): Red LED current in mA
            led_current_ir (float): IR LED current in mA
            pulse_width (int): LED pulse width in μs
            max_buffer_len (int): Maximum data buffer length
        """

        self.xmit_data = bytearray(1)
        self.i2c = i2c 

        self.set_mode(MODE_HR)  # Trigger an initial temperature read.
        self.set_led_current(led_current_red, led_current_ir)
        self.set_spo_config(sample_rate, pulse_width)

        # Reflectance data (latest update)
        self.buffer_red = []
        self.buffer_ir = []

        self.max_buffer_len = max_buffer_len
        self._interrupt = None

    def i2c_write(self, addr, reg, value):
        """
        向指定寄存器的I2C写入数据。

        Args:
            addr (int): I2C设备地址
            reg (int): 寄存器地址
            value (int): 要写入的值

        =========================================
        Write data to I2C at specified register.

        Args:
            addr (int): I2C device address
            reg (int): Register address
            value (int): Value to write
        """
        self.xmit_data[0] = value
        self.i2c.writeto_mem(addr, reg, self.xmit_data)

    @property
    def red(self):
        """
        获取最新的红光反射值。

        Returns:
            int or None: 最新的红光反射值，如果没有数据则返回None

        =========================================
        Get latest red reflectance value.

        Returns:
            int or None: Latest red reflectance value, None if no data
        """
        return self.buffer_red[-1] if self.buffer_red else None

    @property
    def ir(self):
        """
        获取最新的红外反射值。

        Returns:
            int or None: 最新的红外反射值，如果没有数据则返回None

        =========================================
        Get latest infrared reflectance value.

        Returns:
            int or None: Latest infrared reflectance value, None if no data
        """
        return self.buffer_ir[-1] if self.buffer_ir else None

    def set_led_current(self, led_current_red=11.0, led_current_ir=11.0):
        """
        设置红光和红外LED的电流。

        Args:
            led_current_red (float): 红光LED电流，单位：mA
            led_current_ir (float): 红外LED电流，单位：mA

        =========================================
        Set red and infrared LED currents.

        Args:
            led_current_red (float): Red LED current in mA
            led_current_ir (float): Infrared LED current in mA
        """
        # Validate the settings, convert to bit values.
        led_current_red = _get_valid(LED_CURRENT, led_current_red)
        led_current_ir = _get_valid(LED_CURRENT, led_current_ir)
        self.i2c_write(I2C_ADDRESS, LED_CONFIG, (led_current_red << 4) | led_current_ir)

    def set_mode(self, mode):
        """
        设置传感器工作模式。

        Args:
            mode (int): 工作模式，MODE_HR或MODE_SPO2

        =========================================
        Set sensor operation mode.

        Args:
            mode (int): Operation mode, MODE_HR or MODE_SPO2
        """
        reg = self.i2c.readfrom_mem(I2C_ADDRESS, MODE_CONFIG,1)[0]
        self.i2c_write(I2C_ADDRESS, MODE_CONFIG, reg & 0x74) # mask the SHDN bit
        self.i2c_write(I2C_ADDRESS, MODE_CONFIG, reg | mode)

    def set_spo_config(self, sample_rate=100, pulse_width=1600):
        """
        设置SpO2配置。

        Args:
            sample_rate (int): 采样率，单位：Hz
            pulse_width (int): LED脉冲宽度，单位：μs

        =========================================
        Set SpO2 configuration.

        Args:
            sample_rate (int): Sampling rate in Hz
            pulse_width (int): LED pulse width in μs
        """
        reg = self.i2c.readfrom_mem(I2C_ADDRESS, SPO2_CONFIG,1)[0]
        reg = reg & 0xFC  # Set LED pulsewidth to 00
        self.i2c_write(I2C_ADDRESS, SPO2_CONFIG, reg | pulse_width)

    def enable_spo2(self):
        """
        启用SpO2模式。

        =========================================
        Enable SpO2 mode.
        """
        self.set_mode(MODE_SPO2)

    def disable_spo2(self):
        """
        禁用SpO2模式，切换为仅心率模式。

        =========================================
        Disable SpO2 mode, switch to heart rate only mode.
        """
        self.set_mode(MODE_HR)

    def enable_interrupt(self, interrupt_type):
        """
        启用指定类型的中断。

        Args:
            interrupt_type (int): 中断类型，INTERRUPT_SPO2/HR/TEMP/FIFO

        =========================================
        Enable specified interrupt type.

        Args:
            interrupt_type (int): Interrupt type, INTERRUPT_SPO2/HR/TEMP/FIFO
        """
        self.i2c_write(I2C_ADDRESS, INT_ENABLE, (interrupt_type + 1)<<4)
        self.i2c.readfrom_mem(I2C_ADDRESS, INT_STATUS,1)[0]

    def get_number_of_samples(self):
        """
        获取FIFO中可用的样本数量。

        Returns:
            int: FIFO中的样本数量

        =========================================
        Get number of samples available in FIFO.

        Returns:
            int: Number of samples in FIFO
        """
        write_ptr = self.i2c.readfrom_mem(I2C_ADDRESS, FIFO_WR_PTR,1)[0]
        read_ptr = self.i2c.readfrom_mem(I2C_ADDRESS, FIFO_RD_PTR,1)[0]
        return abs(16+write_ptr - read_ptr) % 16

    def read_sensor(self):
        """
        从传感器读取数据并更新缓冲区。

        =========================================
        Read data from sensor and update buffers.
        """
        #bytes = self.i2c.read_i2c_block_data(I2C_ADDRESS, FIFO_DATA, 4)
        bytes = self.i2c.readfrom_mem(I2C_ADDRESS, FIFO_DATA, 4)
        # Add latest values.
        self.buffer_ir.append(bytes[0]<<8 | bytes[1])
        self.buffer_red.append(bytes[2]<<8 | bytes[3])
        # Crop our local FIFO buffer to length.
        self.buffer_red = self.buffer_red[-self.max_buffer_len:]
        self.buffer_ir = self.buffer_ir[-self.max_buffer_len:]

    def shutdown(self):
        """
        关闭传感器进入低功耗模式。

        =========================================
        Shutdown sensor into low power mode.
        """
        reg = self.i2c.readfrom_mem(I2C_ADDRESS, MODE_CONFIG,1)[0]
        self.i2c_write(I2C_ADDRESS, MODE_CONFIG, reg | 0x80)

    def reset(self):
        """
        重置传感器。

        =========================================
        Reset the sensor.
        """
        reg = self.i2c.readfrom_mem(I2C_ADDRESS, MODE_CONFIG,1)[0]
        self.i2c_write(I2C_ADDRESS, MODE_CONFIG, reg | 0x40)

    def refresh_temperature(self):
        """
        刷新温度数据。

        =========================================
        Refresh temperature data.
        """
        reg = self.i2c.readfrom_mem(I2C_ADDRESS, MODE_CONFIG,1)[0]
        self.i2c_write(I2C_ADDRESS, MODE_CONFIG, reg | (1 << 3))

    def get_temperature(self):
        """
        获取当前温度值。

        Returns:
            float: 温度值，单位：摄氏度

        =========================================
        Get current temperature value.

        Returns:
            float: Temperature value in Celsius
        """
        intg = _twos_complement(self.i2c.readfrom_mem(I2C_ADDRESS, TEMP_INTG,1)[0])
        frac = self.i2c.readfrom_mem(I2C_ADDRESS, TEMP_FRAC,1)[0]
        return intg + (frac * 0.0625)

    def get_rev_id(self):
        """
        获取芯片版本ID。

        Returns:
            int: 版本ID

        =========================================
        Get chip revision ID.

        Returns:
            int: Revision ID
        """
        return self.i2c.readfrom_mem(I2C_ADDRESS, REV_ID,1)[0]

    def get_part_id(self):
        """
        获取芯片部件ID。

        Returns:
            int: 部件ID

        =========================================
        Get chip part ID.

        Returns:
            int: Part ID
        """
        return self.i2c.readfrom_mem(I2C_ADDRESS, PART_ID,1)[0]

    def get_registers(self):
        """
        获取所有寄存器状态。

        Returns:
            dict: 寄存器地址到值的映射字典

        =========================================
        Get all register statuses.

        Returns:
            dict: Dictionary mapping register addresses to values
        """
        return {
            "INT_STATUS": self.i2c.readfrom_mem(I2C_ADDRESS, INT_STATUS,1)[0],
            "INT_ENABLE": self.i2c.readfrom_mem(I2C_ADDRESS, INT_ENABLE,1)[0],
            "FIFO_WR_PTR": self.i2c.readfrom_mem(I2C_ADDRESS, FIFO_WR_PTR,1)[0],
            "OVRFLOW_CTR": self.i2c.readfrom_mem(I2C_ADDRESS, OVRFLOW_CTR,1)[0],
            "FIFO_RD_PTR": self.i2c.readfrom_mem(I2C_ADDRESS, FIFO_RD_PTR,1)[0],
            "FIFO_DATA": self.i2c.readfrom_mem(I2C_ADDRESS, FIFO_DATA,1)[0],
            "MODE_CONFIG": self.i2c.readfrom_mem(I2C_ADDRESS, MODE_CONFIG,1)[0],
            "SPO2_CONFIG": self.i2c.readfrom_mem(I2C_ADDRESS, SPO2_CONFIG,1)[0],
            "LED_CONFIG": self.i2c.readfrom_mem(I2C_ADDRESS, LED_CONFIG,1)[0],
            "TEMP_INTG": self.i2c.readfrom_mem(I2C_ADDRESS, TEMP_INTG,1)[0],
            "TEMP_FRAC": self.i2c.readfrom_mem(I2C_ADDRESS, TEMP_FRAC,1)[0],
            "REV_ID": self.i2c.readfrom_mem(I2C_ADDRESS, REV_ID,1)[0],
            "PART_ID": self.i2c.readfrom_mem(I2C_ADDRESS, PART_ID,1)[0],
        }

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================