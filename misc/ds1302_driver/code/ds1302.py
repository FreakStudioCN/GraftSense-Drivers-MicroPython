# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/10/3 下午2:41   
# @Author  : 李清水            
# @File    : ds1302.py       
# @Description : 自定义DS1302类控制芯片

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import Pin
# 导入MicroPython相关模块
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义DS1302芯片控制类
class DS1302:
    """
    DS1302类，用于通过三线接口（CLK、DIO、CS）操作DS1302实时时钟芯片。

    该类封装了对DS1302芯片的通信，提供了读取和设置时间、日期、星期等功能。
    支持启动和停止时钟，以及读写芯片内部的RAM寄存器。

    Attributes:
        clk (Pin): 时钟引脚，用于产生时钟信号。
        dio (Pin): 数据引脚，用于读写数据。
        cs  (Pin): 片选引脚，用于使能芯片通信。

    Methods:
        __init__(self, clk: Pin, dio: Pin, cs: Pin) -> None:
            初始化DS1302类实例。

        _dec2hex(self, dat: int) -> int:
            将十进制数转换为十六进制数。

        _hex2dec(self, dat: int) -> int:
            将十六进制数转换为十进制数。

        _write_byte(self, dat: int) -> None:
            写入一个字节到DS1302。

        _read_byte(self) -> int:
            从DS1302读取一个字节。

        _get_reg(self, reg: int) -> int:
            获取指定寄存器的值。

        _set_reg(self, reg: int, dat: int) -> None:
            设置指定寄存器的值。

        _wr(self, reg: int, dat: int) -> None:
            写入数据到寄存器，并设置写保护。

        start(self) -> None:
            启动时钟。

        stop(self) -> None:
            停止时钟。

        second(self) -> int:
            获取当前秒数。

        second(self, value: int) -> None:
            设置秒数。

        minute(self) -> int:
            获取当前分钟数。

        minute(self, value: int) -> None:
            设置分钟数。

        hour(self) -> int:
            获取当前小时数。

        hour(self, value: int) -> None:
            设置小时数。

        weekday(self) -> int:
            获取当前星期数。

        weekday(self, value: int) -> None:
            设置星期数。

        day(self) -> int:
            获取当前日期。

        day(self, value: int) -> None:
            设置日期。

        month(self) -> int:
            获取当前月份。

        month(self, value: int) -> None:
            设置月份。

        year(self) -> int:
            获取当前年份。

        year(self, value: int) -> None:
            设置年份。

        date_time(self, dat: list[int] | None = None) -> list[int] | None:
            获取或设置完整的日期和时间。

        ram(self, reg: int, dat: int | None = None) -> int | None:
            读取或写入RAM寄存器的值。
    """
    # 类变量：定义DS1302芯片寄存器地址
    DS1302_REG_SECOND = const(0x80)  # 秒寄存器
    DS1302_REG_MINUTE = const(0x82)  # 分寄存器
    DS1302_REG_HOUR = const(0x84)    # 时寄存器
    DS1302_REG_DAY = const(0x86)     # 日寄存器
    DS1302_REG_MONTH = const(0x88)   # 月寄存器
    DS1302_REG_WEEKDAY = const(0x8A) # 星期寄存器
    DS1302_REG_YEAR = const(0x8C)    # 年寄存器
    DS1302_REG_WP = const(0x8E)      # 写保护寄存器
    DS1302_REG_CTRL = const(0x90)    # 控制寄存器
    DS1302_REG_RAM = const(0xC0)     # RAM寄存器

    def __init__(self, clk: Pin, dio: Pin, cs: Pin) -> None:
        """
        初始化DS1302类。

        Args:
            clk (Pin): 时钟引脚。
            dio (Pin): 数据引脚。
            cs  (Pin): 片选引脚。

        Returns:
            None
        """

        self.clk = clk
        self.dio = dio
        self.cs = cs

        # 初始化时钟引脚为输出
        self.clk.init(Pin.OUT)
        # 初始化片选引脚为输出
        self.cs.init(Pin.OUT)

    def _dec2hex(self, dat: int) -> int:
        """
        将十进制转换为十六进制。

        Args:
            dat (int): 要转换的十进制数。

        Returns:
            int: 转换后的十六进制数。
        """
        return (dat // 10) * 16 + (dat % 10)

    def _hex2dec(self, dat: int) -> int:
        """
        将十六进制转换为十进制。

        Args:
            dat (int): 要转换的十六进制数。

        Returns:
            int: 转换后的十进制数。
        """
        return (dat // 16) * 10 + (dat % 16)

    def _write_byte(self, dat: int) -> None:
        """
        写入一个字节到DS1302。

        Args:
            dat (int): 要写入的字节。

        Returns:
            None
        """
        # 设置数据引脚为输出
        self.dio.init(Pin.OUT)

        # 写入8位数据
        for i in range(8):
            # 写入每一位，上升沿写入数据
            self.dio.value((dat >> i) & 1)
            # 产生时钟信号
            self.clk.value(1)
            self.clk.value(0)

    def _read_byte(self) -> int:
        """
        从DS1302读取一个字节。

        Returns:
            int: 读取到的字节。
        """
        # 初始化临时变量
        d = 0

        # 设置数据引脚为输入
        self.dio.init(Pin.IN)

        # 依次读取八位数据
        for i in range(8):
            # 读取每一位，下降沿读取数据
            d = d | (self.dio.value() << i)
            # 产生时钟信号
            self.clk.value(1)
            self.clk.value(0)
        return d

    def _get_reg(self, reg: int) -> int:
        """
        获取指定寄存器的值。

        Args:
            reg (int): 寄存器地址。

        Returns:
            int: 寄存器的值。
        """
        # 启动通信
        self.cs.value(1)
        # 写入寄存器地址
        self._write_byte(reg)
        # 读取数据
        t = self._read_byte()
        # 结束通信
        self.cs.value(0)
        return t

    def _set_reg(self, reg: int, dat: int) -> None:
        """
        设置指定寄存器的值。

        Args:
            reg (int): 寄存器地址。
            dat (int): 要写入的数据。

        Returns:
            None
        """
        # 启动通信
        self.cs.value(1)
        # 写入寄存器地址
        self._write_byte(reg)
        # 写入数据
        self._write_byte(dat)
        # 结束通信
        self.cs.value(0)

    def _wr(self, reg: int, dat: int) -> None:
        """
        写入数据到寄存器，并设置写保护。

        Args:
            reg (int): 寄存器地址。
            dat (int): 要写入的数据。

        Returns:
            None
        """
        # 禁用写保护
        self._set_reg(DS1302.DS1302_REG_WP, 0)
        # 写入数据
        self._set_reg(reg, dat)
        # 启用写保护
        self._set_reg(DS1302.DS1302_REG_WP, 0x80)

    def start(self) -> None:
        """
        启动时钟。
        Args:
            None

        Returns:
            None
        """
        # 读取秒寄存器
        t = self._get_reg(DS1302.DS1302_REG_SECOND + 1)
        # 取消停止位
        self._wr(DS1302.DS1302_REG_SECOND, t & 0x7f)

    def stop(self) -> None:
        """
        停止时钟。
        Args:
            None

        Returns:
            None
        """
        # 读取秒寄存器
        t = self._get_reg(DS1302.DS1302_REG_SECOND + 1)
        # 设置停止位
        self._wr(DS1302.DS1302_REG_SECOND, t | 0x80)

    @property
    def second(self) -> int:
        """
        获取秒。
        Args:
            None

        Returns:
            int: 当前秒。
        """
        return self._hex2dec(self._get_reg(DS1302.DS1302_REG_SECOND + 1)) % 60

    @second.setter
    def second(self, value: int) -> None:
        """
        设置秒。

        Args:
            value (int): 要设置的秒数。

        Returns:
            None
        """
        self._wr(DS1302.DS1302_REG_SECOND, self._dec2hex(value % 60))

    @property
    def minute(self) -> int:
        """
        获取分。
        Args:
            None

        Returns:
            int: 当前分。
        """
        return self._hex2dec(self._get_reg(DS1302.DS1302_REG_MINUTE + 1))

    @minute.setter
    def minute(self, value: int) -> None:
        """
        设置分。

        Args:
            value (int): 要设置的分钟数。

        Returns:
            None
        """
        self._wr(DS1302.DS1302_REG_MINUTE, self._dec2hex(value % 60))

    @property
    def hour(self) -> int:
        """
        获取时。
        Args:
            None

        Returns:
            int: 当前时。
        """
        return self._hex2dec(self._get_reg(DS1302.DS1302_REG_HOUR + 1))

    @hour.setter
    def hour(self, value: int) -> None:
        """
        设置时。

        Args:
            value (int): 要设置的小时数。

        Returns:
            None
        """
        self._wr(DS1302.DS1302_REG_HOUR, self._dec2hex(value % 24))

    @property
    def weekday(self) -> int:
        """
        获取星期。
        Args:
            None

        Returns:
            int: 当前星期。
        """
        return self._hex2dec(self._get_reg(DS1302.DS1302_REG_WEEKDAY + 1))

    @weekday.setter
    def weekday(self, value: int) -> None:
        """
        设置星期。

        Args:
            value (int): 要设置的星期数。

        Returns:
            None
        """
        self._wr(DS1302.DS1302_REG_WEEKDAY, self._dec2hex(value % 8))

    @property
    def day(self) -> int:
        """
        获取日。
        Args:
            None

        Returns:
            int: 当前日。
        """
        return self._hex2dec(self._get_reg(DS1302.DS1302_REG_DAY + 1))

    @day.setter
    def day(self, value: int) -> None:
        """
        设置日。

        Args:
            value (int): 要设置的日。

        Returns:
            None
        """
        self._wr(DS1302.DS1302_REG_DAY, self._dec2hex(value % 32))

    @property
    def month(self) -> int:
        """
        获取月。
        Args:
            None

        Returns:
            int: 当前月。
        """
        return self._hex2dec(self._get_reg(DS1302.DS1302_REG_MONTH + 1))

    @month.setter
    def month(self, value: int) -> None:
        """
        设置月。

        Args:
            value (int): 要设置的月。

        Returns:
            None
        """
        self._wr(DS1302.DS1302_REG_MONTH, self._dec2hex(value % 13))

    @property
    def year(self) -> int:
        """
        获取年。
        Args:
            None

        Returns:
            int: 当前年。
        """
        return self._hex2dec(self._get_reg(DS1302.DS1302_REG_YEAR + 1)) + 2000

    @year.setter
    def year(self, value: int) -> None:
        """
        设置年。

        Args:
            value (int): 要设置的年。

        Returns:
            None
        """
        self._wr(DS1302.DS1302_REG_YEAR, self._dec2hex(value % 100))

    def date_time(self, dat: list[int] | None = None) -> list[int] | None:
        """
        获取或设置日期和时间。

        Args:
            dat (list[int] | None): 日期和时间数据 [年, 月, 日, 星期, 时, 分, 秒]。如果为 None，则获取当前时间。

        Returns:
            list[int] | None: 如果 dat 为 None，返回 [年, 月, 日, 星期, 时, 分, 秒]；否则返回 None。
        """
        if dat is None:
            return [self.year, self.month, self.day, self.weekday, self.hour, self.minute, self.second]
        else:
            self.year = dat[0]
            self.month = dat[1]
            self.day = dat[2]
            self.weekday = dat[3]
            self.hour = dat[4]
            self.minute = dat[5]
            self.second = dat[6]

    def ram(self, reg: int, dat: int | None = None) -> int | None:
        """
        读取或写入RAM寄存器。

        Args:
            reg (int): 寄存器地址。
            dat (int | None): 要写入的数据。如果为 None，则读取数据。

        Returns:
            int | None: 如果 dat 为 None，返回读取的数据；否则返回 None。
        """
        if dat is None:
            return self._get_reg(DS1302.DS1302_REG_RAM + 1 + (reg % 31) * 2)
        else:
            self._wr(DS1302.DS1302_REG_RAM + (reg % 31) * 2, dat)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================