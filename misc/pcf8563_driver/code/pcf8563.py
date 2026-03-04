# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午4:00
# @Author  : lewisxhe
# @File    : pcf8563.py
# @Description : PCF8563 RTC实时时钟模块驱动 实现时间读写、闹钟设置、时钟输出配置等功能
# @License : MIT
# @Platform: MicroPython v1.23.0

__version__ = "1.0.0"
__author__ = "lewisxhe"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 导入时间模块，用于系统时间交互
import time
# 导入I2C通信模块，用于与PCF8563进行数据交互
from machine import I2C
# 导入常量定义工具，用于定义硬件寄存器地址
from micropython import const

# ======================================== 全局变量 ============================================
# PCF8563模块I2C从机地址
PCF8563_SLAVE_ADDRESS = const(0x51)
# 状态寄存器1地址
PCF8563_STAT1_REG = const(0x00)
# 状态寄存器2地址
PCF8563_STAT2_REG = const(0x01)
# 秒寄存器地址
PCF8563_SEC_REG = const(0x02)
# 分寄存器地址
PCF8563_MIN_REG = const(0x03)
# 时寄存器地址
PCF8563_HR_REG = const(0x04)
# 日寄存器地址
PCF8563_DAY_REG = const(0x05)
# 星期寄存器地址
PCF8563_WEEKDAY_REG = const(0x06)
# 月寄存器地址
PCF8563_MONTH_REG = const(0x07)
# 年寄存器地址
PCF8563_YEAR_REG = const(0x08)
# 方波/时钟输出寄存器地址
PCF8563_SQW_REG = const(0x0D)
# 定时器寄存器1地址
PCF8563_TIMER1_REG = const(0x0E)
# 定时器寄存器2地址
PCF8563_TIMER2_REG = const(0x0F)

# 电压低掩码位
PCF8563_VOL_LOW_MASK = const(0x80)
# 分钟寄存器掩码位
PCF8563_minuteS_MASK = const(0x7F)
# 小时寄存器掩码位
PCF8563_HOUR_MASK = const(0x3F)
# 星期寄存器掩码位
PCF8563_WEEKDAY_MASK = const(0x07)
# 世纪掩码位
PCF8563_CENTURY_MASK = const(0x80)
# 日期寄存器掩码位
PCF8563_DAY_MASK = const(0x3F)
# 月份寄存器掩码位
PCF8563_MONTH_MASK = const(0x1F)
# 定时器控制掩码位
PCF8563_TIMER_CTL_MASK = const(0x03)

# 闹钟标志位
PCF8563_ALARM_AF = const(0x08)
# 定时器标志位
PCF8563_TIMER_TF = const(0x04)
# 闹钟中断使能位
PCF8563_ALARM_AIE = const(0x02)
# 定时器中断使能位
PCF8563_TIMER_TIE = const(0x01)
# 定时器使能位
PCF8563_TIMER_TE = const(0x80)
# 定时器频率选择位
PCF8563_TIMER_TD10 = const(0x03)

# 无闹钟标志
PCF8563_NO_ALARM = const(0xFF)
# 闹钟使能位
PCF8563_ALARM_ENABLE = const(0x80)
# 时钟输出使能位
PCF8563_CLK_ENABLE = const(0x80)

# 闹钟分钟寄存器地址
PCF8563_ALARM_MINUTES = const(0x09)
# 闹钟小时寄存器地址
PCF8563_ALARM_HOURS = const(0x0A)
# 闹钟日期寄存器地址
PCF8563_ALARM_DAY = const(0x0B)
# 闹钟星期寄存器地址
PCF8563_ALARM_WEEKDAY = const(0x0C)

# 时钟输出频率-32.768KHz
CLOCK_CLK_OUT_FREQ_32_DOT_768KHZ = const(0x80)
# 时钟输出频率-1.024KHz
CLOCK_CLK_OUT_FREQ_1_DOT_024KHZ = const(0x81)
# 时钟输出频率-32KHz
CLOCK_CLK_OUT_FREQ_32_KHZ = const(0x82)
# 时钟输出频率-1Hz
CLOCK_CLK_OUT_FREQ_1_HZ = const(0x83)
# 时钟输出高阻抗模式
CLOCK_CLK_HIGH_IMPEDANCE = const(0x0)


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class PCF8563:
    """
    PCF8563 RTC实时时钟模块驱动类
    PCF8563 RTC Real-Time Clock Module Driver Class

    实现PCF8563实时时钟模块的完整功能控制，包括时间读取/写入、系统时间同步、闹钟设置/清除、
    时钟输出频率配置等核心功能，基于I2C通信协议实现与硬件模块的交互
    Implement complete function control of PCF8563 real-time clock module, including core functions such as time reading/writing, 
    system time synchronization, alarm setting/clearing, clock output frequency configuration, and realize interaction with hardware module based on I2C communication protocol

    Attributes:
        i2c (machine.I2C): I2C通信对象，用于与PCF8563模块进行数据交互
                           I2C communication object for data interaction with PCF8563 module
        address (int): PCF8563模块I2C设备地址，默认0x51
                       PCF8563 module I2C device address, default 0x51
        buffer (bytearray): 16字节数据缓冲区，用于I2C数据传输
                            16-byte data buffer for I2C data transmission
        bytebuf (memoryview): 单字节内存视图，优化单字节读写性能
                              Single-byte memory view to optimize single-byte read/write performance

    Methods:
        __init__(i2c, address=None): 初始化PCF8563 RTC模块驱动
                                     Initialize PCF8563 RTC module driver
        __write_byte(reg, val): 私有方法-向指定寄存器写入单字节数据
                                Private method - write single byte data to specified register
        __read_byte(reg): 私有方法-从指定寄存器读取单字节数据
                          Private method - read single byte data from specified register
        __bcd2dec(bcd): 私有方法-BCD码转换为十进制数
                        Private method - convert BCD code to decimal number
        __dec2bcd(dec): 私有方法-十进制数转换为BCD码
                        Private method - convert decimal number to BCD code
        seconds(): 获取当前秒数(0-59)
                   Get current seconds (0-59)
        minutes(): 获取当前分钟数(0-59)
                   Get current minutes (0-59)
        hours(): 获取当前小时数(0-23)
                 Get current hours (0-23)
        day(): 获取当前星期数(0-6)
               Get current weekday (0-6)
        date(): 获取当前日期(1-31)
                Get current date (1-31)
        month(): 获取当前月份(1-12)
                 Get current month (1-12)
        year(): 获取当前年份(0-99)
                Get current year (0-99)
        datetime(): 获取完整日期时间元组
                    Get complete datetime tuple
        write_all(seconds=None, minutes=None, hours=None, day=None, date=None, month=None, year=None): 写入指定时间字段
                                                                                                       Write specified time fields
        set_datetime(dt): 设置完整日期时间
                          Set complete datetime
        write_now(): 同步系统时间到RTC模块
                     Synchronize system time to RTC module
        set_clk_out_frequency(frequency=CLOCK_CLK_OUT_FREQ_1_HZ): 设置时钟输出频率
                                                                 Set clock output frequency
        check_if_alarm_on(): 检查闹钟是否触发
                             Check if alarm is triggered
        turn_alarm_off(): 关闭闹钟功能
                          Turn off alarm function
        clear_alarm(): 清除闹钟设置
                       Clear alarm settings
        check_for_alarm_interrupt(): 检查闹钟中断是否使能
                                     Check if alarm interrupt is enabled
        enable_alarm_interrupt(): 启用闹钟中断
                                  Enable alarm interrupt
        disable_alarm_interrupt(): 禁用闹钟中断
                                   Disable alarm interrupt
        set_daily_alarm(hours=None, minutes=None, date=None, weekday=None): 设置每日闹钟
                                                                            Set daily alarm
    """

    def __init__(self, i2c, address=None):
        """
        初始化PCF8563 RTC模块驱动
        Initialize PCF8563 RTC module driver

        Args:
            i2c (machine.I2C): I2C通信对象
                               I2C communication object
            address (int, optional): I2C设备地址，默认使用PCF8563_SLAVE_ADDRESS(0x51)
                                     I2C device address, default to PCF8563_SLAVE_ADDRESS(0x51)

        Returns:
            None

        Notes:
            初始化数据缓冲区和内存视图，优化I2C单字节读写性能
            Initialize data buffer and memory view to optimize I2C single-byte read/write performance
        """
        # 保存I2C通信对象
        self.i2c = i2c
        # 配置I2C设备地址（使用默认值或自定义值）
        self.address = address if address else PCF8563_SLAVE_ADDRESS
        # 初始化16字节数据缓冲区
        self.buffer = bytearray(16)
        # 创建单字节内存视图，用于高效读写
        self.bytebuf = memoryview(self.buffer[0:1])

    def __write_byte(self, reg, val):
        """
        私有方法-向指定寄存器写入单字节数据
        Private method - write single byte data to specified register

        Args:
            reg (int): 寄存器地址
                       Register address
            val (int): 要写入的字节数据(0-255)
                       Byte data to write (0-255)

        Returns:
            None

        Notes:
            内部使用方法，通过I2C寄存器写入接口实现单字节数据传输
            Internal use method, realize single-byte data transmission through I2C register write interface
        """
        # 将数据写入单字节缓冲区
        self.bytebuf[0] = val
        # 通过I2C写入指定寄存器地址的数据
        self.i2c.writeto_mem(self.address, reg, self.bytebuf)

    def __read_byte(self, reg):
        """
        私有方法-从指定寄存器读取单字节数据
        Private method - read single byte data from specified register

        Args:
            reg (int): 寄存器地址
                       Register address

        Returns:
            int: 读取到的字节数据(0-255)
                 Read byte data (0-255)

        Notes:
            内部使用方法，通过I2C寄存器读取接口实现单字节数据获取
            Internal use method, realize single-byte data acquisition through I2C register read interface
        """
        # 从指定寄存器读取数据到单字节缓冲区
        self.i2c.readfrom_mem_into(self.address, reg, self.bytebuf)
        # 返回读取到的字节数据
        return self.bytebuf[0]

    def __bcd2dec(self, bcd):
        """
        私有方法-BCD码转换为十进制数
        Private method - convert BCD code to decimal number

        Args:
            bcd (int): BCD码值(0-99对应的BCD编码)
                       BCD code value (BCD encoding corresponding to 0-99)

        Returns:
            int: 转换后的十进制数
                 Converted decimal number

        Notes:
            RTC模块存储时间使用BCD码格式，需转换为十进制便于使用
            RTC module stores time in BCD code format, which needs to be converted to decimal for easy use
        """
        # 高4位转换为十位，低4位转换为个位，合并为十进制数
        return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

    def __dec2bcd(self, dec):
        """
        私有方法-十进制数转换为BCD码
        Private method - convert decimal number to BCD code

        Args:
            dec (int): 十进制数(0-99)
                       Decimal number (0-99)

        Returns:
            int: 转换后的BCD码值
                 Converted BCD code value

        Notes:
            将十进制时间值转换为BCD码格式，用于写入RTC寄存器
            Convert decimal time value to BCD code format for writing to RTC register
        """
        # 拆分十位和个位
        tens, units = divmod(dec, 10)
        # 组合为BCD码（十位左移4位 + 个位）
        return (tens << 4) + units

    def seconds(self):
        """
        获取当前秒数(0-59)
        Get current seconds (0-59)

        Args:
            None

        Returns:
            int: 当前秒数(0-59)
                 Current seconds (0-59)

        Notes:
            读取秒寄存器并掩码掉电压低标志位，转换为十进制返回
            Read second register and mask out low voltage flag bit, convert to decimal and return
        """
        # 读取秒寄存器值并掩码，转换为十进制
        return self.__bcd2dec(self.__read_byte(PCF8563_SEC_REG) & 0x7F)

    def minutes(self):
        """
        获取当前分钟数(0-59)
        Get current minutes (0-59)

        Args:
            None

        Returns:
            int: 当前分钟数(0-59)
                 Current minutes (0-59)

        Notes:
            读取分寄存器并掩码，转换为十进制返回
            Read minute register and mask, convert to decimal and return
        """
        # 读取分寄存器值并掩码，转换为十进制
        return self.__bcd2dec(self.__read_byte(PCF8563_MIN_REG) & 0x7F)

    def hours(self):
        """
        获取当前小时数(0-23)
        Get current hours (0-23)

        Args:
            None

        Returns:
            int: 当前小时数(0-23)
                 Current hours (0-23)

        Notes:
            读取时寄存器并掩码，转换为十进制返回
            Read hour register and mask, convert to decimal and return
        """
        # 读取时寄存器值并掩码
        d = self.__read_byte(PCF8563_HR_REG) & 0x3F
        # 转换为十进制并返回
        return self.__bcd2dec(d & 0x3F)

    def day(self):
        """
        获取当前星期数(0-6)
        Get current weekday (0-6)

        Args:
            None

        Returns:
            int: 当前星期数(0-6)
                 Current weekday (0-6)

        Notes:
            读取星期寄存器并掩码，转换为十进制返回
            Read weekday register and mask, convert to decimal and return
        """
        # 读取星期寄存器值并掩码，转换为十进制
        return self.__bcd2dec(self.__read_byte(PCF8563_WEEKDAY_REG) & 0x07)

    def date(self):
        """
        获取当前日期(1-31)
        Get current date (1-31)

        Args:
            None

        Returns:
            int: 当前日期(1-31)
                 Current date (1-31)

        Notes:
            读取日寄存器并掩码，转换为十进制返回
            Read day register and mask, convert to decimal and return
        """
        # 读取日寄存器值并掩码，转换为十进制
        return self.__bcd2dec(self.__read_byte(PCF8563_DAY_REG) & 0x3F)

    def month(self):
        """
        获取当前月份(1-12)
        Get current month (1-12)

        Args:
            None

        Returns:
            int: 当前月份(1-12)
                 Current month (1-12)

        Notes:
            读取月寄存器并掩码，转换为十进制返回
            Read month register and mask, convert to decimal and return
        """
        # 读取月寄存器值并掩码，转换为十进制
        return self.__bcd2dec(self.__read_byte(PCF8563_MONTH_REG) & 0x1F)

    def year(self):
        """
        获取当前年份(0-99)
        Get current year (0-99)

        Args:
            None

        Returns:
            int: 当前年份(0-99)
                 Current year (0-99)

        Notes:
            PCF8563仅存储年份后两位，范围0-99，需自行处理世纪信息
            PCF8563 only stores the last two digits of the year, range 0-99, need to handle century information by yourself
        """
        # 读取年寄存器值，转换为十进制
        return self.__bcd2dec(self.__read_byte(PCF8563_YEAR_REG))

    def datetime(self):
        """
        获取完整日期时间元组
        Get complete datetime tuple

        Args:
            None

        Returns:
            tuple: (年, 月, 日, 星期, 时, 分, 秒)
                   (year, month, date, weekday, hour, minute, second)

        Notes:
            返回与time.localtime()格式兼容的时间元组（不含微秒和夏令时）
            Return time tuple compatible with time.localtime() format (without microseconds and DST)
        """
        # 组合完整的日期时间元组并返回
        return (self.year(), self.month(), self.date(),
                self.day(), self.hours(), self.minutes(),
                self.seconds())

    def write_all(self, seconds=None, minutes=None, hours=None, day=None,
                  date=None, month=None, year=None):
        """
        写入指定时间字段
        Write specified time fields

        Args:
            seconds (int, optional): 秒(0-59)，None则不修改
                                     Seconds (0-59), None means no modification
            minutes (int, optional): 分(0-59)，None则不修改
                                     Minutes (0-59), None means no modification
            hours (int, optional): 时(0-23)，None则不修改
                                   Hours (0-23), None means no modification
            day (int, optional): 星期(0-6)，None则不修改
                                 Weekday (0-6), None means no modification
            date (int, optional): 日(1-31)，None则不修改
                                  Date (1-31), None means no modification
            month (int, optional): 月(1-12)，None则不修改
                                   Month (1-12), None means no modification
            year (int, optional): 年(0-99)，None则不修改
                                  Year (0-99), None means no modification

        Returns:
            None

        Raises:
            ValueError: 当参数值超出有效范围时抛出
                        Raised when parameter value is out of valid range

        Notes:
            仅修改指定的时间字段，未指定的字段保持不变，所有参数需在有效范围内
            Only modify specified time fields, unspecified fields remain unchanged, all parameters must be within valid range
        """
        # 写入秒数（如果指定）
        if seconds is not None:
            # 验证秒数范围
            if seconds < 0 or seconds > 59:
                raise ValueError('Seconds is out of range [0,59].')
            # 转换为BCD码并写入寄存器
            seconds_reg = self.__dec2bcd(seconds)
            self.__write_byte(PCF8563_SEC_REG, seconds_reg)

        # 写入分钟（如果指定）
        if minutes is not None:
            # 验证分钟范围
            if minutes < 0 or minutes > 59:
                raise ValueError('Minutes is out of range [0,59].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_MIN_REG, self.__dec2bcd(minutes))

        # 写入小时（如果指定）
        if hours is not None:
            # 验证小时范围
            if hours < 0 or hours > 23:
                raise ValueError('Hours is out of range [0,23].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_HR_REG, self.__dec2bcd(hours))

        # 写入年份（如果指定）
        if year is not None:
            # 验证年份范围
            if year < 0 or year > 99:
                raise ValueError('Years is out of range [0,99].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_YEAR_REG, self.__dec2bcd(year))

        # 写入月份（如果指定）
        if month is not None:
            # 验证月份范围
            if month < 1 or month > 12:
                raise ValueError('Month is out of range [1,12].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_MONTH_REG, self.__dec2bcd(month))

        # 写入日期（如果指定）
        if date is not None:
            # 验证日期范围
            if date < 1 or date > 31:
                raise ValueError('Date is out of range [1,31].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_DAY_REG, self.__dec2bcd(date))

        # 写入星期（如果指定）
        if day is not None:
            # 验证星期范围
            if day < 0 or day > 6:
                raise ValueError('Day is out of range [0,6].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_WEEKDAY_REG, self.__dec2bcd(day))

    def set_datetime(self, dt):
        """
        设置完整日期时间
        Set complete datetime

        Args:
            dt (tuple): 时间元组，格式为(年, 月, 日, 星期, 时, 分, 秒)
                        Time tuple in format (year, month, date, weekday, hour, minute, second)

        Returns:
            None

        Notes:
            时间元组格式与datetime()返回值一致，年份仅取后两位(0-99)
            Time tuple format is consistent with datetime() return value, only last two digits of year are taken (0-99)
        """
        # 解析时间元组并写入所有字段
        self.write_all(dt[6], dt[5], dt[4], dt[3],
                       dt[2], dt[1], dt[0] % 100)

    def write_now(self):
        """
        同步系统时间到RTC模块
        Synchronize system time to RTC module

        Args:
            None

        Returns:
            None

        Notes:
            获取系统本地时间并写入RTC模块，实现时间同步
            Get system local time and write to RTC module to realize time synchronization
        """
        # 获取系统本地时间并设置到RTC
        self.set_datetime(time.localtime())

    def set_clk_out_frequency(self, frequency=CLOCK_CLK_OUT_FREQ_1_HZ):
        """
        设置时钟输出频率
        Set clock output frequency

        Args:
            frequency (int, optional): 输出频率常量，默认1Hz
                                       Output frequency constant, default 1Hz

        Returns:
            None

        Notes:
            支持的频率：32.768KHz/1.024KHz/32KHz/1Hz/高阻抗
            Supported frequencies: 32.768KHz/1.024KHz/32KHz/1Hz/high impedance
        """
        # 写入时钟输出频率配置
        self.__write_byte(PCF8563_SQW_REG, frequency)

    def check_if_alarm_on(self):
        """
        检查闹钟是否触发
        Check if alarm is triggered

        Args:
            None

        Returns:
            bool: True-闹钟已触发，False-未触发
                  True-alarm triggered, False-not triggered

        Notes:
            通过状态寄存器2的闹钟标志位判断闹钟状态
            Judge alarm status by alarm flag bit of status register 2
        """
        # 读取状态寄存器2并检查闹钟标志位
        return bool(self.__read_byte(PCF8563_STAT2_REG) & PCF8563_ALARM_AF)

    def turn_alarm_off(self):
        """
        关闭闹钟功能
        Turn off alarm function

        Args:
            None

        Returns:
            None

        Notes:
            清除闹钟标志位但保留闹钟设置，仅关闭当前触发状态
            Clear alarm flag bit but keep alarm settings, only turn off current trigger status
        """
        # 读取当前闹钟状态
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        # 清除闹钟标志位
        self.__write_byte(PCF8563_STAT2_REG, alarm_state & 0xf7)

    def clear_alarm(self):
        """
        清除闹钟设置
        Clear alarm settings

        Args:
            None

        Returns:
            None

        Notes:
            清除闹钟标志位和使能位，重置所有闹钟相关寄存器
            Clear alarm flag bit and enable bit, reset all alarm-related registers
        """
        # 读取当前闹钟状态
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        # 清除闹钟标志位
        alarm_state &= ~(PCF8563_ALARM_AF)
        # 保留定时器标志位
        alarm_state |= PCF8563_TIMER_TF
        # 写入更新后的状态
        self.__write_byte(PCF8563_STAT2_REG, alarm_state)

        # 重置闹钟分钟寄存器
        self.__write_byte(PCF8563_ALARM_MINUTES, 0x80)
        # 重置闹钟小时寄存器
        self.__write_byte(PCF8563_ALARM_HOURS, 0x80)
        # 重置闹钟日期寄存器
        self.__write_byte(PCF8563_ALARM_DAY, 0x80)
        # 重置闹钟星期寄存器
        self.__write_byte(PCF8563_ALARM_WEEKDAY, 0x80)

    def check_for_alarm_interrupt(self):
        """
        检查闹钟中断是否使能
        Check if alarm interrupt is enabled

        Args:
            None

        Returns:
            bool: True-中断已使能，False-未使能
                  True-interrupt enabled, False-not enabled

        Notes:
            检查状态寄存器2的闹钟中断使能位
            Check alarm interrupt enable bit of status register 2
        """
        # 读取状态寄存器2并检查闹钟中断使能位
        return bool(self.__read_byte(PCF8563_STAT2_REG) & 0x02)

    def enable_alarm_interrupt(self):
        """
        启用闹钟中断
        Enable alarm interrupt

        Args:
            None

        Returns:
            None

        Notes:
            设置闹钟中断使能位，清除闹钟标志位，保留定时器标志位
            Set alarm interrupt enable bit, clear alarm flag bit, keep timer flag bit
        """
        # 读取当前闹钟状态
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        # 清除闹钟标志位
        alarm_state &= ~PCF8563_ALARM_AF
        # 设置定时器标志位和闹钟中断使能位
        alarm_state |= (PCF8563_TIMER_TF | PCF8563_ALARM_AIE)
        # 写入更新后的状态
        self.__write_byte(PCF8563_STAT2_REG, alarm_state)

    def disable_alarm_interrupt(self):
        """
        禁用闹钟中断
        Disable alarm interrupt

        Args:
            None

        Returns:
            None

        Notes:
            清除闹钟中断使能位和标志位，保留定时器标志位
            Clear alarm interrupt enable bit and flag bit, keep timer flag bit
        """
        # 读取当前闹钟状态
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        # 清除闹钟标志位和中断使能位
        alarm_state &= ~(PCF8563_ALARM_AF | PCF8563_ALARM_AIE)
        # 设置定时器标志位
        alarm_state |= PCF8563_TIMER_TF
        # 写入更新后的状态
        self.__write_byte(PCF8563_STAT2_REG, alarm_state)

    def set_daily_alarm(self, hours=None, minutes=None, date=None, weekday=None):
        """
        设置每日闹钟
        Set daily alarm

        Args:
            hours (int, optional): 小时(0-23)，None则不设置该字段
                                   Hours (0-23), None means not set this field
            minutes (int, optional): 分钟(0-59)，None则不设置该字段
                                     Minutes (0-59), None means not set this field
            date (int, optional): 日期(1-31)，None则不设置该字段
                                  Date (1-31), None means not set this field
            weekday (int, optional): 星期(0-6)，None则不设置该字段
                                     Weekday (0-6), None means not set this field

        Returns:
            None

        Raises:
            ValueError: 当参数值超出有效范围时抛出
                        Raised when parameter value is out of valid range

        Notes:
            None参数表示该字段不参与闹钟匹配（任意值都触发），所有数值参数需在有效范围内
            None parameter means the field does not participate in alarm matching (any value triggers), all numeric parameters must be within valid range
        """
        # 设置闹钟分钟（如果指定）
        if minutes is None:
            # 不设置分钟匹配
            minutes = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_MINUTES, minutes)
        else:
            # 验证分钟范围
            if minutes < 0 or minutes > 59:
                raise ValueError('Minutes is out of range [0,59].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_ALARM_MINUTES,
                              self.__dec2bcd(minutes) & 0x7f)

        # 设置闹钟小时（如果指定）
        if hours is None:
            # 不设置小时匹配
            hours = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_HOURS, hours)
        else:
            # 验证小时范围
            if hours < 0 or hours > 23:
                raise ValueError('Hours is out of range [0,23].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_ALARM_HOURS, self.__dec2bcd(
                hours) & 0x7f)

        # 设置闹钟日期（如果指定）
        if date is None:
            # 不设置日期匹配
            date = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_DAY, date)
        else:
            # 验证日期范围
            if date < 1 or date > 31:
                raise ValueError('date is out of range [1,31].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_ALARM_DAY, self.__dec2bcd(
                date) & 0x7f)

        # 设置闹钟星期（如果指定）
        if weekday is None:
            # 不设置星期匹配
            weekday = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_WEEKDAY, weekday)
        else:
            # 验证星期范围
            if weekday < 0 or weekday > 6:
                raise ValueError('weekday is out of range [0,6].')
            # 转换为BCD码并写入寄存器
            self.__write_byte(PCF8563_ALARM_WEEKDAY, self.__dec2bcd(
                weekday) & 0x7f)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================