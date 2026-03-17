# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/17 下午3:45
# @Author  : lewisxhe
# @File    : pcf8563.py
# @Description : PCF8563 RTC实时时钟模块驱动，实现时间读写、闹钟设置、时钟输出配置参考自：https://github.com/lewisxhe/PCF8563_PythonLibrary
# @License : MIT

__version__ = "1.0.0"
__author__ = "lewisxhe"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C
from micropython import const

# ======================================== 全局变量 ============================================
# PCF8563 I2C从机地址
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

# 电压低标志位掩码
PCF8563_VOL_LOW_MASK = const(0x80)
# 分钟寄存器数据掩码
PCF8563_minuteS_MASK = const(0x7F)
# 小时寄存器数据掩码
PCF8563_HOUR_MASK = const(0x3F)
# 星期寄存器数据掩码
PCF8563_WEEKDAY_MASK = const(0x07)
# 世纪标志位掩码
PCF8563_CENTURY_MASK = const(0x80)
# 日期寄存器数据掩码
PCF8563_DAY_MASK = const(0x3F)
# 月份寄存器数据掩码
PCF8563_MONTH_MASK = const(0x1F)
# 定时器控制位掩码
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

# 无闹钟匹配值
PCF8563_NO_ALARM = const(0xFF)
# 闹钟使能标志
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

# 时钟输出 32.768KHz
CLOCK_CLK_OUT_FREQ_32_DOT_768KHZ = const(0x80)
# 时钟输出 1.024KHz
CLOCK_CLK_OUT_FREQ_1_DOT_024KHZ = const(0x81)
# 时钟输出 32KHz
CLOCK_CLK_OUT_FREQ_32_KHZ = const(0x82)
# 时钟输出 1Hz
CLOCK_CLK_OUT_FREQ_1_HZ = const(0x83)
# 时钟输出高阻抗模式
CLOCK_CLK_HIGH_IMPEDANCE = const(0x00)

# 允许的时钟输出频率值列表（用于参数验证）
ALLOWED_CLK_FREQUENCIES = (
    CLOCK_CLK_OUT_FREQ_32_DOT_768KHZ,
    CLOCK_CLK_OUT_FREQ_1_DOT_024KHZ,
    CLOCK_CLK_OUT_FREQ_32_KHZ,
    CLOCK_CLK_OUT_FREQ_1_HZ,
    CLOCK_CLK_HIGH_IMPEDANCE,
)


# ======================================== 功能函数 ============================================
def convert_sys_dt_to_rtc_dt(sys_dt: tuple) -> tuple:
    """
    将系统时间元组转换为RTC适配格式
    Convert system time tuple to RTC compatible format

    Args:
        sys_dt (tuple): 系统本地时间元组
    Returns:
        tuple: RTC驱动可用的时间元组
    Raises:
        ValueError: 输入元组长度不足
    Notes:
        系统星期(0=周一)转为RTC星期(0=周日)

    ==========================================
    English description
    Args:
        sys_dt (tuple): System local time tuple
    Returns:
        tuple: RTC compatible time tuple
    Raises:
        ValueError: Input tuple length is insufficient
    Notes:
    Convert system week(0=Monday) to RTC week(0=Sunday)
    """
    if len(sys_dt) < 7:
        raise ValueError(f"Input time tuple length insufficient: {len(sys_dt)}")

    sys_year = sys_dt[0]
    sys_month = sys_dt[1]
    sys_day = sys_dt[2]
    sys_hour = sys_dt[3]
    sys_minute = sys_dt[4]
    sys_second = sys_dt[5]
    sys_weekday = sys_dt[6]

    rtc_year = sys_year % 100
    rtc_weekday = (sys_weekday + 1) % 7

    rtc_dt = (rtc_year, sys_month, sys_day, rtc_weekday, sys_hour, sys_minute, sys_second)

    return rtc_dt


# ======================================== 自定义类 ============================================
class PCF8563:
    """
    PCF8563 RTC实时时钟驱动类
    PCF8563 RTC real-time clock driver class

    Attributes:
        i2c (I2C): I2C通信对象
        address (int): I2C从机地址
        buffer (bytearray): I2C数据缓冲区
        bytebuf (memoryview): 单字节内存视图

    Methods:
        __init__: 初始化驱动
        __write_byte: 写单字节到寄存器
        __read_byte: 从寄存器读单字节
        __bcd2dec: BCD转十进制
        __dec2bcd: 十进制转BCD
        seconds: 获取秒
        minutes: 获取分
        hours: 获取时
        day: 获取星期
        date: 获取日期
        month: 获取月
        year: 获取年
        datetime: 获取完整时间
        write_all: 写入指定时间项
        set_datetime: 设置完整时间
        write_now: 同步系统时间到RTC
        set_clk_out_frequency: 设置时钟输出频率
        check_if_alarm_on: 查询闹钟是否触发
        turn_alarm_off: 关闭当前闹钟触发
        clear_alarm: 清除闹钟配置
        check_for_alarm_interrupt: 查询闹钟中断使能状态
        enable_alarm_interrupt: 使能闹钟中断
        disable_alarm_interrupt: 关闭闹钟中断
        set_daily_alarm: 设置每日闹钟

    Notes:
        基于I2C通信，使用BCD码存储时间

    ==========================================
    English description
    Attributes:
        i2c (I2C): I2C communication object
        address (int): I2C slave address
        buffer (bytearray): I2C data buffer
        bytebuf (memoryview): Single byte memory view

    Methods:
        __init__: Initialize driver
        __write_byte: Write byte to register
        __read_byte: Read byte from register
        __bcd2dec: BCD to decimal
        __dec2bcd: Decimal to BCD
        seconds: Get seconds
        minutes: Get minutes
        hours: Get hours
        day: Get weekday
        date: Get date
        month: Get month
        year: Get year
        datetime: Get full datetime
        write_all: Write specified time items
        set_datetime: Set full datetime
        write_now: Sync system time to RTC
        set_clk_out_frequency: Set clock output frequency
        check_if_alarm_on: Check alarm trigger
        turn_alarm_off: Turn off current alarm
        clear_alarm: Clear alarm config
        check_for_alarm_interrupt: Check alarm interrupt enable
        enable_alarm_interrupt: Enable alarm interrupt
        disable_alarm_interrupt: Disable alarm interrupt
        set_daily_alarm: Set daily alarm

    Notes:
        I2C based, time stored in BCD format
    """

    def __init__(self, i2c: I2C, address: int | None = None) -> None:
        """
        初始化PCF8563驱动
        Initialize PCF8563 driver

        Args:
            i2c (I2C): I2C对象
            address (int | None): I2C地址，默认None
        Returns:
            None
        Notes:
            地址为None时使用默认0x51

        ==========================================
        English description
        Args:
            i2c (I2C): I2C object
            address (int | None): I2C address, default None
        Returns:
            None
        Notes:
            Use default 0x51 if address is None
        """
        if i2c is None:
            raise ValueError("I2C object cannot be None")
        self.i2c = i2c
        self.address = address if address is not None else PCF8563_SLAVE_ADDRESS
        self.buffer = bytearray(16)
        self.bytebuf = memoryview(self.buffer[0:1])

    def __write_byte(self, reg: int, val: int) -> None:
        """
        向寄存器写入单字节
        Write single byte to register

        Args:
            reg (int): 寄存器地址
            val (int): 写入值
        Returns:
            None
        Raises:
            TypeError: If reg or val is not integer
            ValueError: If reg is out of 0-0x0F range or val is out of 0-255 range
        """
        # Parameter type validation
        if type(reg) is not int:
            raise TypeError(f"Register address must be integer, got {type(reg).__name__}")
        if type(val) is not int:
            raise TypeError(f"Write value must be integer, got {type(val).__name__}")

        # Parameter range validation
        if reg < 0 or reg > 0x0F:
            raise ValueError(f"Register address must be between 0 and 15 (0x0F), got {reg}")
        if val < 0 or val > 255:
            raise ValueError(f"Write value must be between 0 and 255, got {val}")

        self.bytebuf[0] = val
        self.i2c.writeto_mem(self.address, reg, self.bytebuf)

    def __read_byte(self, reg: int) -> int:
        """
        从寄存器读取单字节
        Read single byte from register

        Args:
            reg (int): 寄存器地址
        Returns:
            int: 读取到的字节
        Raises:
            TypeError: If reg is not integer
            ValueError: If reg is out of 0-0x0F range
        """
        # Parameter type validation
        if type(reg) is not int:
            raise TypeError(f"Register address must be integer, got {type(reg).__name__}")

        # Parameter range validation
        if reg < 0 or reg > 0x0F:
            raise ValueError(f"Register address must be between 0 and 15 (0x0F), got {reg}")

        self.i2c.readfrom_mem_into(self.address, reg, self.bytebuf)
        return self.bytebuf[0]

    def __bcd2dec(self, bcd: int) -> int:
        """
        BCD码转十进制
        BCD to decimal conversion

        Args:
            bcd (int): BCD code
        Returns:
            int: Decimal value
        Raises:
            TypeError: If bcd is not integer
            ValueError: If bcd is out of 0-255 range
        """
        # Parameter type validation
        if type(bcd) is not int:
            raise TypeError(f"BCD value must be integer, got {type(bcd).__name__}")

        # Parameter range validation
        if bcd < 0 or bcd > 255:
            raise ValueError(f"BCD value must be between 0 and 255, got {bcd}")

        return ((bcd & 0xF0) >> 4) * 10 + (bcd & 0x0F)

    def __dec2bcd(self, dec: int) -> int:
        """
        十进制转BCD码
        Decimal to BCD conversion

        Args:
            dec (int): Decimal number
        Returns:
            int: BCD code
        Raises:
            TypeError: If dec is not integer
            ValueError: If dec is out of 0-99 range
        """
        # Parameter type validation
        if type(dec) is not int:
            raise TypeError(f"Decimal value must be integer, got {type(dec).__name__}")

        # Parameter range validation
        if dec < 0 or dec > 99:
            raise ValueError(f"Decimal value must be between 0 and 99, got {dec}")

        tens, units = divmod(dec, 10)
        return (tens << 4) + units

    def seconds(self) -> int:
        """
        获取当前秒
        Get current seconds

        Args:
            None
        Returns:
            int: 秒(0-59)

        ==========================================
        English description
        Args:
            None
        Returns:
            int: Seconds(0-59)
        """
        return self.__bcd2dec(self.__read_byte(PCF8563_SEC_REG) & 0x7F)

    def minutes(self) -> int:
        """
        获取当前分钟
        Get current minutes

        Args:
            None
        Returns:
            int: 分钟(0-59)

        ==========================================
        English description
        Args:
            None
        Returns:
            int: Minutes(0-59)
        """
        return self.__bcd2dec(self.__read_byte(PCF8563_MIN_REG) & 0x7F)

    def hours(self) -> int:
        """
        获取当前小时
        Get current hours

        Args:
            None
        Returns:
            int: 小时(0-23)

        ==========================================
        English description
        Args:
            None
        Returns:
            int: Hours(0-23)
        """
        d = self.__read_byte(PCF8563_HR_REG) & 0x3F
        return self.__bcd2dec(d & 0x3F)

    def day(self) -> int:
        """
        获取当前星期
        Get current weekday

        Args:
            None
        Returns:
            int: 星期(0-6)

        ==========================================
        English description
        Args:
            None
        Returns:
            int: Weekday(0-6)
        """
        return self.__bcd2dec(self.__read_byte(PCF8563_WEEKDAY_REG) & 0x07)

    def date(self) -> int:
        """
        获取当前日期
        Get current date

        Args:
            None
        Returns:
            int: 日期(1-31)

        ==========================================
        English description
        Args:
            None
        Returns:
            int: Date(1-31)
        """
        return self.__bcd2dec(self.__read_byte(PCF8563_DAY_REG) & 0x3F)

    def month(self) -> int:
        """
        获取当前月份
        Get current month

        Args:
            None
        Returns:
            int: 月(1-12)

        ==========================================
        English description
        Args:
            None
        Returns:
            int: Month(1-12)
        """
        return self.__bcd2dec(self.__read_byte(PCF8563_MONTH_REG) & 0x1F)

    def year(self) -> int:
        """
        获取当前年份(后两位)
        Get current year(last two digits)

        Args:
            None
        Returns:
            int: 年(0-99)

        ==========================================
        English description
        Args:
            None
        Returns:
            int: Year(0-99)
        """
        return self.__bcd2dec(self.__read_byte(PCF8563_YEAR_REG))

    def datetime(self) -> tuple:
        """
        获取完整时间元组
        Get full datetime tuple

        Args:
            None
        Returns:
            tuple: (年,月,日,星期,时,分,秒)

        ==========================================
        English description
        Args:
            None
        Returns:
            tuple: (year,month,date,weekday,hour,minute,second)
        """
        return (self.year(), self.month(), self.date(), self.day(), self.hours(), self.minutes(), self.seconds())

    def write_all(
        self,
        seconds: int | None = None,
        minutes: int | None = None,
        hours: int | None = None,
        day: int | None = None,
        date: int | None = None,
        month: int | None = None,
        year: int | None = None,
    ) -> None:
        """
        批量写入时间字段
        Write time fields in batch

        Args:
            seconds (int | None): 秒
            minutes (int | None): 分
            hours (int | None): 时
            day (int | None): 星期
            date (int | None): 日期
            month (int | None): 月
            year (int | None): 年
        Returns:
            None
        Raises:
            ValueError: 参数超出合法范围

        ==========================================
        English description
        Args:
            seconds (int | None): Seconds
            minutes (int | None): Minutes
            hours (int | None): Hours
            day (int | None): Weekday
            date (int | None): Date
            month (int | None): Month
            year (int | None): Year
        Returns:
            None
        Raises:
            ValueError: Parameter out of valid range
        """
        if seconds is not None:
            if seconds < 0 or seconds > 59:
                raise ValueError("Seconds out of range [0,59].")
            self.__write_byte(PCF8563_SEC_REG, self.__dec2bcd(seconds))

        if minutes is not None:
            if minutes < 0 or minutes > 59:
                raise ValueError("Minutes out of range [0,59].")
            self.__write_byte(PCF8563_MIN_REG, self.__dec2bcd(minutes))

        if hours is not None:
            if hours < 0 or hours > 23:
                raise ValueError("Hours out of range [0,23].")
            self.__write_byte(PCF8563_HR_REG, self.__dec2bcd(hours))

        if year is not None:
            if year < 0 or year > 99:
                raise ValueError("Years out of range [0,99].")
            self.__write_byte(PCF8563_YEAR_REG, self.__dec2bcd(year))

        if month is not None:
            if month < 1 or month > 12:
                raise ValueError("Month out of range [1,12].")
            self.__write_byte(PCF8563_MONTH_REG, self.__dec2bcd(month))

        if date is not None:
            if date < 1 or date > 31:
                raise ValueError("Date out of range [1,31].")
            self.__write_byte(PCF8563_DAY_REG, self.__dec2bcd(date))

        if day is not None:
            if day < 0 or day > 6:
                raise ValueError("Day out of range [0,6].")
            self.__write_byte(PCF8563_WEEKDAY_REG, self.__dec2bcd(day))

    def set_datetime(self, dt: tuple) -> None:
        """
        设置完整时间
        Set full datetime

        Args:
            dt (tuple): 时间元组
        Returns:
            None

        ==========================================
        English description
        Args:
            dt (tuple): Time tuple
        Returns:
            None
        """
        if dt is None:
            raise ValueError("Datetime tuple cannot be None")
        self.write_all(dt[6], dt[5], dt[4], dt[3], dt[2], dt[1], dt[0] % 100)

    def write_now(self) -> None:
        """
        将系统时间写入RTC
        Write system time to RTC

        Args:
            None
        Returns:
            None

        ==========================================
        English description
        Args:
            None
        Returns:
            None
        """
        self.set_datetime(convert_sys_dt_to_rtc_dt(time.localtime()))

    def set_clk_out_frequency(self, frequency: int = CLOCK_CLK_OUT_FREQ_1_HZ) -> None:
        """
        设置时钟输出频率
        Set clock output frequency

        Args:
            frequency (int): 频率常量
        Returns:
            None
        Raises:
            TypeError: 频率值非整数
            ValueError: 频率值不在允许的列表中

        ==========================================
        English description
        Args:
            frequency (int): Frequency constant
        Returns:
            None
        Raises:
            TypeError: Frequency value is not integer
            ValueError: Frequency value not in allowed list
        """
        # 参数类型验证
        if not isinstance(frequency, int):
            raise TypeError(f"Frequency must be integer, got {type(frequency)}")
        # 参数范围验证（仅允许预定义的频率常量）
        if frequency not in ALLOWED_CLK_FREQUENCIES:
            raise ValueError(f"Frequency must be one of {ALLOWED_CLK_FREQUENCIES}, got {frequency}")

        self.__write_byte(PCF8563_SQW_REG, frequency)

    def check_if_alarm_on(self) -> bool:
        """
        检查闹钟是否触发
        Check if alarm is triggered

        Args:
            None
        Returns:
            bool: 触发状态

        ==========================================
        English description
        Args:
            None
        Returns:
            bool: Trigger status
        """
        return bool(self.__read_byte(PCF8563_STAT2_REG) & PCF8563_ALARM_AF)

    def turn_alarm_off(self) -> None:
        """
        关闭当前闹钟触发状态
        Turn off current alarm trigger

        Args:
            None
        Returns:
            None

        ==========================================
        English description
        Args:
            None
        Returns:
            None
        """
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        self.__write_byte(PCF8563_STAT2_REG, alarm_state & 0xF7)

    def clear_alarm(self) -> None:
        """
        清除所有闹钟配置
        Clear all alarm settings

        Args:
            None
        Returns:
            None

        ==========================================
        English description
        Args:
            None
        Returns:
            None
        """
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        alarm_state &= ~(PCF8563_ALARM_AF)
        alarm_state |= PCF8563_TIMER_TF
        self.__write_byte(PCF8563_STAT2_REG, alarm_state)

        self.__write_byte(PCF8563_ALARM_MINUTES, 0x80)
        self.__write_byte(PCF8563_ALARM_HOURS, 0x80)
        self.__write_byte(PCF8563_ALARM_DAY, 0x80)
        self.__write_byte(PCF8563_ALARM_WEEKDAY, 0x80)

    def check_for_alarm_interrupt(self) -> bool:
        """
        检查闹钟中断是否使能
        Check if alarm interrupt is enabled

        Args:
            None
        Returns:
            bool: 中断使能状态

        ==========================================
        English description
        Args:
            None
        Returns:
            bool: Interrupt enable status
        """
        return bool(self.__read_byte(PCF8563_STAT2_REG) & 0x02)

    def enable_alarm_interrupt(self) -> None:
        """
        使能闹钟中断
        Enable alarm interrupt

        Args:
            None
        Returns:
            None

        ==========================================
        English description
        Args:
            None
        Returns:
            None
        """
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        alarm_state &= ~PCF8563_ALARM_AF
        alarm_state |= PCF8563_TIMER_TF | PCF8563_ALARM_AIE
        self.__write_byte(PCF8563_STAT2_REG, alarm_state)

    def disable_alarm_interrupt(self) -> None:
        """
        关闭闹钟中断
        Disable alarm interrupt

        Args:
            None
        Returns:
            None

        ==========================================
        English description
        Args:
            None
        Returns:
            None
        """
        alarm_state = self.__read_byte(PCF8563_STAT2_REG)
        alarm_state &= ~(PCF8563_ALARM_AF | PCF8563_ALARM_AIE)
        alarm_state |= PCF8563_TIMER_TF
        self.__write_byte(PCF8563_STAT2_REG, alarm_state)

    def set_daily_alarm(self, hours: int | None = None, minutes: int | None = None, date: int | None = None, weekday: int | None = None) -> None:
        """
        设置每日闹钟
        Set daily alarm

        Args:
            hours (int | None): 小时
            minutes (int | None): 分钟
            date (int | None): 日期
            weekday (int | None): 星期
        Returns:
            None
        Raises:
            ValueError: 参数超出范围

        ==========================================
        English description
        Args:
            hours (int | None): Hours
            minutes (int | None): Minutes
            date (int | None): Date
            weekday (int | None): Weekday
        Returns:
            None
        Raises:
            ValueError: Parameter out of range
        """
        if minutes is None:
            minutes = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_MINUTES, minutes)
        else:
            if minutes < 0 or minutes > 59:
                raise ValueError("Minutes out of range [0,59].")
            self.__write_byte(PCF8563_ALARM_MINUTES, self.__dec2bcd(minutes) & 0x7F)

        if hours is None:
            hours = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_HOURS, hours)
        else:
            if hours < 0 or hours > 23:
                raise ValueError("Hours out of range [0,23].")
            self.__write_byte(PCF8563_ALARM_HOURS, self.__dec2bcd(hours) & 0x7F)

        if date is None:
            date = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_DAY, date)
        else:
            if date < 1 or date > 31:
                raise ValueError("date out of range [1,31].")
            self.__write_byte(PCF8563_ALARM_DAY, self.__dec2bcd(date) & 0x7F)

        if weekday is None:
            weekday = PCF8563_ALARM_ENABLE
            self.__write_byte(PCF8563_ALARM_WEEKDAY, weekday)
        else:
            if weekday < 0 or weekday > 6:
                raise ValueError("weekday out of range [0,6].")
            self.__write_byte(PCF8563_ALARM_WEEKDAY, self.__dec2bcd(weekday) & 0x7F)
