# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/10/7 下午2:24   
# @Author  : 李清水            
# @File    : ads1115.py       
# @Description : 外置ADC芯片ADS1115驱动类，参考代码：https://github.com/robert-hh/ads1x15
# @License : MIT

__version__ = "0.1.0"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入MicroPython相关模块
from micropython import const
import micropython
# 导入硬件相关模块
from machine import Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义ADS1115类
class ADS1115:
    """
    ADS1115 16位高精度模数转换器驱动类。
    提供单端和差分输入模式，可配置增益、采样率和比较器功能。
    支持单次转换和连续转换模式，带有可配置警报引脚和中断回调。

    Attributes:
        i2c: I2C接口实例，用于与ADS1115通信。
        address (int): ADS1115的I2C设备地址（0x48-0x4B）。
        gain_index (int): 当前增益设置的索引。
        temp2 (bytearray): 临时缓冲区，用于读写寄存器操作。
        alert_pin (Pin, optional): 警报引脚对象。
        callback (function, optional): 警报中断回调函数。
        alert_trigger (int): 中断触发模式。
        mode (int): 当前转换模式配置值。

    Methods:
        __init__(self, i2c, address=0x48, gain=2, alert_pin=None, callback=None):
            初始化ADS1115实例。
        _get_gain_register_value(self, gain):
            根据增益值返回对应的寄存器配置值。
        _irq_handler(self, pin):
            内部中断处理程序。
        _write_register(self, register, value):
            写入寄存器。
        _read_register(self, register):
            读取寄存器的值。
        raw_to_v(self, raw):
            将原始ADC值转换为电压。
        set_conv(self, rate=4, channel1=0, channel2=None):
            设置转换速率和通道。
        read(self, rate=4, channel1=0, channel2=None):
            读取指定通道的ADC值。
        read_rev(self):
            读取转换结果并启动下一个转换。
        alert_start(self, rate=4, channel1=0, channel2=None,
                    threshold_high=0x4000, threshold_low=0, latched=False):
            启动持续测量，并设置ALERT引脚的阈值。
        conversion_start(self, rate=4, channel1=0, channel2=None):
            启动持续测量，基于ALERT/RDY引脚触发。
        alert_read(self):
            从持续测量中获取最后一次读取的转换结果。

    Notes:
        支持单端输入（0-3通道）和差分输入（0-1, 0-3, 1-3, 2-3组合）。
        增益范围从2/3倍（±6.144V）到16倍（±0.256V）。
        采样率从8 SPS到860 SPS可配置。

    ==========================================
    ADS1115 16-bit high precision analog-to-digital converter driver class.
    Provides single-ended and differential input modes, configurable gain, sampling rate and comparator functions.
    Supports single conversion and continuous conversion modes, with configurable alert pins and interrupt callbacks.

    Attributes:
        i2c: I2C interface instance for communicating with ADS1115.
        address (int): ADS1115 I2C device address (0x48-0x4B).
        gain_index (int): Current gain setting index.
        temp2 (bytearray): Temporary buffer for register read/write operations.
        alert_pin (Pin, optional): Alert pin object.
        callback (function, optional): Alert interrupt callback function.
        alert_trigger (int): Interrupt trigger mode.
        mode (int): Current conversion mode configuration value.

    Methods:
        __init__(self, i2c, address=0x48, gain=2, alert_pin=None, callback=None):
            Initialize ADS1115 instance.
        _get_gain_register_value(self, gain):
            Return corresponding register configuration value based on gain value.
        _irq_handler(self, pin):
            Internal interrupt handler.
        _write_register(self, register, value):
            Write to register.
        _read_register(self, register):
            Read register value.
        raw_to_v(self, raw):
            Convert raw ADC value to voltage.
        set_conv(self, rate=4, channel1=0, channel2=None):
            Set conversion rate and channels.
        read(self, rate=4, channel1=0, channel2=None):
            Read ADC value of specified channel.
        read_rev(self):
            Read conversion result and start next conversion.
        alert_start(self, rate=4, channel1=0, channel2=None,
                    threshold_high=0x4000, threshold_low=0, latched=False):
            Start continuous measurement and set ALERT pin thresholds.
        conversion_start(self, rate=4, channel1=0, channel2=None):
            Start continuous measurement based on ALERT/RDY pin triggering.
        alert_read(self):
            Get last read conversion result from continuous measurement.

    Notes:
        Supports single-ended input (channels 0-3) and differential input (0-1, 0-3, 1-3, 2-3 combinations).
        Gain range from 2/3x (±6.144V) to 16x (±0.256V).
        Sampling rate configurable from 8 SPS to 860 SPS.
    """

    # 寄存器地址常量
    # 转换寄存器
    REGISTER_CONVERT = const(0x00)
    # 配置寄存器
    REGISTER_CONFIG = const(0x01)
    # 低阈值寄存器
    REGISTER_LOWTHRESH = const(0x02)
    # 高阈值寄存器
    REGISTER_HITHRESH = const(0x03)

    # 配置寄存器位掩码和常量
    # 操作状态掩码
    OS_MASK = const(0x8000)
    # 写入：启动单次转换
    OS_SINGLE = const(0x8000)
    # 读取：转换进行中
    OS_BUSY = const(0x0000)
    # 读取：转换完成
    OS_NOTBUSY = const(0x8000)

    # 多路复用掩码
    MUX_MASK = const(0x7000)
    # 差分输入：AIN0 - AIN1（默认）
    MUX_DIFF_0_1 = const(0x0000)
    # 差分输入：AIN0 - AIN3
    MUX_DIFF_0_3 = const(0x1000)
    # 差分输入：AIN1 - AIN3
    MUX_DIFF_1_3 = const(0x2000)
    # 差分输入：AIN2 - AIN3
    MUX_DIFF_2_3 = const(0x3000)
    # 单端输入：AIN0
    MUX_SINGLE_0 = const(0x4000)
    # 单端输入：AIN1
    MUX_SINGLE_1 = const(0x5000)
    # 单端输入：AIN2
    MUX_SINGLE_2 = const(0x6000)
    # 单端输入：AIN3
    MUX_SINGLE_3 = const(0x7000)

    # 程度增益掩码
    PGA_MASK = const(0x0E00)
    # +/-6.144V 范围，增益 2/3
    PGA_6_144V = const(0x0000)
    # +/-4.096V 范围，增益 1
    PGA_4_096V = const(0x0200)
    # +/-2.048V 范围，增益 2（默认）
    PGA_2_048V = const(0x0400)
    # +/-1.024V 范围，增益 4
    PGA_1_024V = const(0x0600)
    # +/-0.512V 范围，增益 8
    PGA_0_512V = const(0x0800)
    # +/-0.256V 范围，增益 16
    PGA_0_256V = const(0x0A00)

    # 模式掩码
    MODE_MASK = const(0x0100)
    # 连续转换模式
    MODE_CONTIN = const(0x0000)
    # 单次转换模式（默认）
    MODE_SINGLE = const(0x0100)

    # 数据速率掩码
    DR_MASK = const(0x00E0)
    # 8 采样每秒
    DR_8SPS = const(0x0000)
    # 16 采样每秒
    DR_16SPS = const(0x0020)
    # 32 采样每秒
    DR_32SPS = const(0x0040)
    # 64 采样每秒
    DR_64SPS = const(0x0060)
    # 128 采样每秒（默认）
    DR_128SPS = const(0x0080)
    # 250 采样每秒
    DR_250SPS = const(0x00A0)
    # 475 采样每秒
    DR_475SPS = const(0x00C0)
    # 860 采样每秒
    DR_860SPS = const(0x00E0)

    # 比较模式掩码
    CMODE_MASK = const(0x0010)
    # 传统比较器模式，带迟滞（默认）
    CMODE_TRAD = const(0x0000)
    # 窗口比较器模式
    CMODE_WINDOW = const(0x0010)

    # 比较器极性掩码
    CPOL_MASK = const(0x0008)
    # ALERT/RDY 引脚低电平激活（默认）
    CPOL_ACTVLOW = const(0x0000)
    # ALERT/RDY 引脚高电平激活
    CPOL_ACTVHI = const(0x0008)

    # 比较器锁存掩码
    CLAT_MASK = const(0x0004)
    # 非锁存比较器（默认）
    CLAT_NONLAT = const(0x0000)
    # 锁存比较器
    CLAT_LATCH = const(0x0004)

    # 比较器队列掩码
    CQUE_MASK = const(0x0003)
    # 一次转换后触发 ALERT/RDY
    CQUE_1CONV = const(0x0000)
    # 两次转换后触发 ALERT/RDY
    CQUE_2CONV = const(0x0001)
    # 四次转换后触发 ALERT/RDY
    CQUE_4CONV = const(0x0002)
    # 禁用比较器，将 ALERT/RDY 拉高（默认）
    CQUE_NONE = const(0x0003)

    # 增益设置对应的寄存器值
    GAINS = (
        # 2/3x
        PGA_6_144V,
        # 1x
        PGA_4_096V,
        # 2x
        PGA_2_048V,
        # 4x
        PGA_1_024V,
        # 8x
        PGA_0_512V,
        # 16x
        PGA_0_256V
    )

    # 增益对应的电压范围
    GAINS_V = (
        # 2/3x
        6.144,
        # 1x
        4.096,
        # 2x
        2.048,
        # 4x
        1.024,
        # 8x
        0.512,
        # 16x
        0.256
    )

    # 通道对应的多路复用配置
    CHANNELS = {
        (0, None): MUX_SINGLE_0,
        (1, None): MUX_SINGLE_1,
        (2, None): MUX_SINGLE_2,
        (3, None): MUX_SINGLE_3,
        (0, 1): MUX_DIFF_0_1,
        (0, 3): MUX_DIFF_0_3,
        (1, 3): MUX_DIFF_1_3,
        (2, 3): MUX_DIFF_2_3,
    }

    # 数据速率设置对应的寄存器值
    RATES = (
        # 8 采样每秒
        DR_8SPS,
        # 16 采样每秒
        DR_16SPS,
        # 32 采样每秒
        DR_32SPS,
        # 64 采样每秒
        DR_64SPS,
        # 128 采样每秒（默认）
        DR_128SPS,
        # 250 采样每秒
        DR_250SPS,
        # 475 采样每秒
        DR_475SPS,
        # 860 采样每秒
        DR_860SPS
    )

    def __init__(self, i2c, address=0x48, gain=2, alert_pin=None, callback=None):
        """
        初始化 ADS1115 实例。

        Args:
            i2c (machine.I2C): I2C 对象。
            address (int, optional): ADS1115 的 I2C 地址，默认 0x48。
            gain (int, optional): 增益设置，默认 2 对应 +/-2.048V。
            alert_pin (int, optional): 警报引脚编号。
            callback (function, optional): 警报回调函数。

        Raises:
            ValueError: 如果地址不在 0x48-0x4B 范围内。
            ValueError: 如果增益值不在有效范围内。

        Notes:
            支持的增益值：2/3, 1, 2, 4, 8, 16。
            如果设置了警报引脚，默认使用下降沿触发中断。

        ==========================================

        Initialize ADS1115 instance.

        Args:
            i2c (machine.I2C): I2C object.
            address (int, optional): ADS1115 I2C address, default 0x48.
            gain (int, optional): Gain setting, default 2 corresponds to +/-2.048V.
            alert_pin (int, optional): Alert pin number.
            callback (function, optional): Alert callback function.

        Raises:
            ValueError: If address is not in range 0x48-0x4B.
            ValueError: If gain value is not in valid range.

        Notes:
            Supported gain values: 2/3, 1, 2, 4, 8, 16.
            If alert pin is set, uses falling edge trigger for interrupt by default.
        """
        # 判断ads1115的I2C通信地址是否为0x48、0x49、0x4A或0x4B
        if not 0x48 <= address <= 0x4B:
            raise ValueError("Invalid I2C address: 0x{:02X}".format(address))

        # 判断增益是否为2/3、1、2、4、8或16
        if gain not in (2/3, 1, 2, 4, 8, 16):
            raise ValueError("Invalid gain: {}".format(gain))

        # 存储 I2C 对象
        self.i2c = i2c
        # 存储设备地址
        self.address = address
        # 存储增益设置的索引
        try:
            self.gain_index = ADS1115.GAINS.index(self._get_gain_register_value(gain))
        except ValueError:
            raise ValueError("Gain setting not found in GAINS tuple.")

        # 临时存储字节数组，用于读写操作
        self.temp2 = bytearray(2)

        # 如果设置了警报引脚
        if alert_pin is not None:
            # 设置 ALERT 引脚为输入
            self.alert_pin = Pin(alert_pin, Pin.IN)
            # 存储用户回调函数
            self.callback = callback
            # 默认触发模式为下降沿
            self.alert_trigger = Pin.IRQ_FALLING
            # 设置中断处理程序
            self.alert_pin.irq(handler=lambda p: self._irq_handler(p), trigger=self.alert_trigger)

    def _get_gain_register_value(self, gain):
        """
        根据增益值返回对应的寄存器配置值。

        Args:
            gain (float): 增益值。

        Returns:
            int: 寄存器配置值。

        ==========================================

        Return corresponding register configuration value based on gain value.

        Args:
            gain (float): Gain value.

        Returns:
            int: Register configuration value.
        """
        gain_map = {
            2/3: ADS1115.GAINS[0],
            1:   ADS1115.GAINS[1],
            2:   ADS1115.GAINS[2],
            4:   ADS1115.GAINS[3],
            8:   ADS1115.GAINS[4],
            16:  ADS1115.GAINS[5]
        }
        return gain_map[gain]

    def _irq_handler(self, pin):
        """
        内部中断处理程序，使用 micropython.schedule 调度用户回调。

        Args:
            pin (machine.Pin): 触发中断的引脚对象。

        ==========================================

        Internal interrupt handler, uses micropython.schedule to schedule user callback.

        Args:
            pin (machine.Pin): Pin object that triggered interrupt.
        """
        if hasattr(self, 'callback') and self.callback:
            micropython.schedule(self.callback, pin)

    def _write_register(self, register, value):
        """
        写入寄存器。

        Args:
            register (int): 寄存器地址。
            value (int): 要写入的值。

        ==========================================

        Write to register.

        Args:
            register (int): Register address.
            value (int): Value to write.
        """
        # 取value的高八字节
        self.temp2[0] = (value >> 8) & 0xFF
        # 取value的低八字节
        self.temp2[1] = value & 0xFF
        # 写入寄存器
        self.i2c.writeto_mem(self.address, register, self.temp2)

    def _read_register(self, register):
        """
        读取寄存器的值。

        Args:
            register (int): 寄存器地址。

        Returns:
            int: 读取的值。

        ==========================================

        Read register value.

        Args:
            register (int): Register address.

        Returns:
            int: Read value.
        """
        # 读取寄存器
        self.i2c.readfrom_mem_into(self.address, register, self.temp2)
        # 合并高低字节并返回
        return (self.temp2[0] << 8) | self.temp2[1]

    def raw_to_v(self, raw):
        """
        将原始 ADC 值转换为电压。

        Args:
            raw (int): 原始 ADC 值。

        Returns:
            float: 转换后的电压值。

        Notes:
            转换公式：电压 = 原始值 × (满量程电压 / 32768)。

        ==========================================

        Convert raw ADC value to voltage.

        Args:
            raw (int): Raw ADC value.

        Returns:
            float: Converted voltage value.

        Notes:
            Conversion formula: voltage = raw value × (full scale voltage / 32768).
        """
        # 计算每位电压值
        v_p_b = ADS1115.GAINS_V[self.gain_index] / 32768
        # 返回转换后的电压
        return raw * v_p_b

    def set_conv(self, rate=4, channel1=0, channel2=None):
        """
        设置转换速率和通道。

        Args:
            rate (int, optional): 数据速率索引，默认 4 对应 128 SPS。
            channel1 (int, optional): 主通道编号。
            channel2 (int, optional): 差分通道编号。

        Raises:
            ValueError: 如果速率索引无效。
            ValueError: 如果通道编号无效。

        ==========================================

        Set conversion rate and channels.

        Args:
            rate (int, optional): Data rate index, default 4 corresponds to 128 SPS.
            channel1 (int, optional): Main channel number.
            channel2 (int, optional): Differential channel number.

        Raises:
            ValueError: If rate index is invalid.
            ValueError: If channel number is invalid.
        """
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))
        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 配置寄存器值
        self.mode = (ADS1115.CQUE_NONE      | ADS1115.CLAT_NONLAT |
                     ADS1115.CPOL_ACTVLOW   | ADS1115.CMODE_TRAD |
                     ADS1115.RATES[rate]    | ADS1115.MODE_SINGLE |
                     ADS1115.OS_SINGLE      | ADS1115.GAINS[self.gain_index] |
                     ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))

    def read(self, rate=4, channel1=0, channel2=None):
        """
        读取指定通道的 ADC 值。

        Args:
            rate (int, optional): 数据速率索引，默认 4 对应 128 SPS。
            channel1 (int, optional): 主通道编号。
            channel2 (int, optional): 差分通道编号。

        Returns:
            int: ADC 原始值，若为负值则进行补偿。

        Raises:
            ValueError: 如果速率索引或通道编号无效。

        Notes:
            使用单次转换模式，读取完成后自动等待转换完成。

        ==========================================

        Read ADC value of specified channel.

        Args:
            rate (int, optional): Data rate index, default 4 corresponds to 128 SPS.
            channel1 (int, optional): Main channel number.
            channel2 (int, optional): Differential channel number.

        Returns:
            int: ADC raw value, negative values are compensated.

        Raises:
            ValueError: If rate index or channel number is invalid.

        Notes:
            Uses single conversion mode, automatically waits for conversion to complete after reading.
        """
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))

        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 写入配置寄存器，启动转换
        self._write_register(
            ADS1115.REGISTER_CONFIG,
            (ADS1115.CQUE_NONE      | ADS1115.CLAT_NONLAT |
             ADS1115.CPOL_ACTVLOW   | ADS1115.CMODE_TRAD |
             ADS1115.RATES[rate]    | ADS1115.MODE_SINGLE |
             ADS1115.OS_SINGLE      | ADS1115.GAINS[self.gain_index] |
             ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))
        )
        # 等待转换完成
        while not (self._read_register(ADS1115.REGISTER_CONFIG) & ADS1115.OS_NOTBUSY):
            # 每次等待 1 毫秒
            time.sleep_ms(1)
        # 读取转换结果
        res = self._read_register(ADS1115.REGISTER_CONVERT)
        # 返回有符号结果
        return res if res < 32768 else res - 65536

    def read_rev(self):
        """
        读取转换结果并启动下一个转换。

        Returns:
            int: ADC 原始值，若为负值则进行补偿。

        Notes:
            需要在调用 set_conv() 方法设置转换模式后使用。

        ==========================================

        Read conversion result and start next conversion.

        Returns:
            int: ADC raw value, negative values are compensated.

        Notes:
            Need to use after calling set_conv() method to set conversion mode.
        """
        # 读取转换结果
        res = self._read_register(ADS1115.REGISTER_CONVERT)
        # 启动下一个转换
        self._write_register(ADS1115.REGISTER_CONFIG, self.mode)
        # 返回有符号结果
        return res if res < 32768 else res - 65536

    def alert_start(self, rate=4, channel1=0, channel2=None,
                    threshold_high=0x4000, threshold_low=0, latched=False):
        """
        启动持续测量，并设置 ALERT 引脚的阈值。

        Args:
            rate (int, optional): 数据速率索引，默认 4 对应 1600/128 SPS。
            channel1 (int, optional): 主通道编号。
            channel2 (int, optional): 差分通道编号。
            threshold_high (int, optional): 高阈值，默认 0x4000。
            threshold_low (int, optional): 低阈值，默认 0。
            latched (bool, optional): 是否锁存 ALERT 引脚，默认 False。

        Raises:
            ValueError: 如果速率索引或通道编号无效。
            ValueError: 如果高阈值小于低阈值。

        ==========================================

        Start continuous measurement and set ALERT pin thresholds.

        Args:
            rate (int, optional): Data rate index, default 4 corresponds to 1600/128 SPS.
            channel1 (int, optional): Main channel number.
            channel2 (int, optional): Differential channel number.
            threshold_high (int, optional): High threshold, default 0x4000.
            threshold_low (int, optional): Low threshold, default 0.
            latched (bool, optional): Whether to latch ALERT pin, default False.

        Raises:
            ValueError: If rate index or channel number is invalid.
            ValueError: If high threshold is less than low threshold.
        """
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))

        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 判断阈值是否正确设置
        if threshold_high < threshold_low:
            raise ValueError("Invalid threshold: {} > {}".format(threshold_high, threshold_low))

        # 设置低阈值寄存器
        self._write_register(ADS1115.REGISTER_LOWTHRESH, threshold_low)
        # 设置高阈值寄存器
        self._write_register(ADS1115.REGISTER_HITHRESH, threshold_high)

        # 配置 ALERT 引脚和比较器
        self._write_register(
            ADS1115.REGISTER_CONFIG,
            (ADS1115.CQUE_1CONV |
             (ADS1115.CLAT_LATCH if latched else ADS1115.CLAT_NONLAT) |
             ADS1115.CPOL_ACTVLOW | ADS1115.CMODE_TRAD |
             ADS1115.RATES[rate] | ADS1115.MODE_CONTIN |
             ADS1115.GAINS[self.gain_index] |
             ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))
        )

    def conversion_start(self, rate=4, channel1=0, channel2=None):
        """
        启动持续测量，基于 ALERT/RDY 引脚触发。

        Args:
            rate (int, optional): 数据速率索引，默认 4 对应 1600/128 SPS。
            channel1 (int, optional): 主通道编号。
            channel2 (int, optional): 差分通道编号。

        Raises:
            ValueError: 如果速率索引或通道编号无效。

        ==========================================

        Start continuous measurement based on ALERT/RDY pin triggering.

        Args:
            rate (int, optional): Data rate index, default 4 corresponds to 1600/128 SPS.
            channel1 (int, optional): Main channel number.
            channel2 (int, optional): Differential channel number.

        Raises:
            ValueError: If rate index or channel number is invalid.
        """
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))

        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 设置低阈值为 0
        self._write_register(ADS1115.REGISTER_LOWTHRESH, 0)
        # 设置高阈值为 0x8000
        self._write_register(ADS1115.REGISTER_HITHRESH, 0x8000)

        # 配置 ALERT 引脚和比较器，启动转换
        self._write_register(
            ADS1115.REGISTER_CONFIG,
            (ADS1115.CQUE_1CONV | ADS1115.CLAT_NONLAT |
             ADS1115.CPOL_ACTVLOW | ADS1115.CMODE_TRAD |
             ADS1115.RATES[rate] | ADS1115.MODE_CONTIN |
             ADS1115.GAINS[self.gain_index] |
             ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))
        )

    def alert_read(self):
        """
        从持续测量中获取最后一次读取的转换结果。

        Returns:
            int: ADC 原始值，若为负值则进行补偿。

        ==========================================

        Get last read conversion result from continuous measurement.

        Returns:
            int: ADC raw value, negative values are compensated.
        """
        # 读取转换结果
        res = self._read_register(ADS1115.REGISTER_CONVERT)
        # 返回有符号结果
        return res if res < 32768 else res - 65536

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================