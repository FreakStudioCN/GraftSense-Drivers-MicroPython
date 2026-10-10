# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : FreakStudio
# @File    : pcf85063.py
# @Description : PCF85063/PCF85063ATL RTC driver
# @License : Apache-2.0

__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "Apache-2.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import time

# ======================================== 全局变量 ============================================
# PCF85063 默认 I2C 地址
DEFAULT_ADDRESS = const(0x51)

# 寄存器地址
REG_CTRL1 = const(0x00)
REG_CTRL2 = const(0x01)
REG_SECONDS = const(0x04)
REG_ALARM_SECONDS = const(0x0B)

# 闹钟禁用标志位（bit 7 = 1 表示该闹钟字段禁用）
ALARM_DISABLE = const(0x80)


# ======================================== 功能函数 ============================================
def bcd_to_dec(value):
    """BCD to decimal conversion."""
    return (value >> 4) * 10 + (value & 0x0F)


def dec_to_bcd(value):
    """Decimal to BCD conversion."""
    return ((value // 10) << 4) | (value % 10)


# ======================================== 自定义类 ============================================
class PCF85063:
    """
    PCF85063/PCF85063ATL 低功耗 RTC 驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例（外部注入）
        _addr (int): 设备 I2C 地址
        _year_base (int): 年份基准偏移，寄存器中存储（实际年份 - _year_base）
        _debug (bool): 调试日志开关

    Methods:
        reset(): 执行软件复位
        datetime(): 获取或设置日期时间（兼容 machine.RTC 接口）
        set_datetime(): 设置日期时间
        read_datetime(): 读取日期时间
        set_alarm(): 配置闹钟
        enable_alarm_interrupt(): 启用/禁用闹钟中断输出
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入 I2C 实例，不在类内创建总线
        - 时间寄存器使用 BCD 格式存储，通过 bcd_to_dec/dec_to_bcd 转换
        - 年份以 _year_base 为基准进行偏移计算
    ==========================================
    PCF85063/PCF85063ATL low-power RTC driver.

    Attributes:
        _i2c (I2C): I2C bus instance (externally injected)
        _addr (int): Device I2C address
        _year_base (int): Year base offset, stored as (actual_year - _year_base)
        _debug (bool): Debug logging switch

    Methods:
        reset(): Perform soft reset
        datetime(): Get or set datetime (compatible with machine.RTC interface)
        set_datetime(): Set datetime
        read_datetime(): Read datetime
        set_alarm(): Configure alarm
        enable_alarm_interrupt(): Enable/disable alarm interrupt output
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance
        - Time registers use BCD format, converted via bcd_to_dec/dec_to_bcd
        - Year is offset by _year_base
    """

    __slots__ = ("_i2c", "_addr", "_year_base", "_debug")

    def __init__(self, i2c, address=None, year_base=1970, debug=False):
        """
        初始化 PCF85063 RTC 驱动

        Args:
            i2c (I2C): I2C 总线实例（外部注入，不可为 None）
            address (int): I2C 地址，默认 0x51（自动使用 DEFAULT_ADDRESS）
            year_base (int): 年份基准偏移，默认 1970
            debug (bool): 调试日志开关，默认 False

        Raises:
            ValueError: 参数为 None 或类型/范围无效

        Notes:
            - 不在此处初始化硬件，仅保存引用
            - year_base 用于年份偏移计算，例如：实际年份 2026 年，year_base=2000，
              则寄存器中存储 26；读回时自动加上 year_base 恢复为 2026
        ==========================================
        Initialize PCF85063 RTC driver.

        Args:
            i2c (I2C): I2C bus instance (externally injected, must not be None)
            address (int): I2C address, default 0x51 (auto-uses DEFAULT_ADDRESS)
            year_base (int): Year base offset, default 1970
            debug (bool): Debug logging switch, default False

        Raises:
            ValueError: Parameter is None or has invalid type/range

        Notes:
            - No hardware initialization, only stores references
            - year_base is used for year offset calculation, e.g. actual year 2026
              with year_base=2000, register stores 26; on read, adds year_base back to get 2026
        """
        # 参数校验：i2c 不能为 None 且必须具备 I2C 接口方法
        if i2c is None:
            raise ValueError("i2c must not be None")
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance")

        # 参数校验：address 类型和范围
        if address is None:
            address = DEFAULT_ADDRESS
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0 or address > 0x7F:
            raise ValueError("address must be 0~0x7F, got %d" % address)

        # 参数校验：year_base 类型和范围
        if not isinstance(year_base, int):
            raise ValueError("year_base must be int, got %s" % type(year_base))
        if year_base < 0:
            raise ValueError("year_base must be non-negative, got %d" % year_base)

        # 参数校验：debug 类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = address
        self._year_base = year_base
        self._debug = debug

    def _log(self, msg):
        """
        输出调试日志

        仅当 _debug 为 True 时打印，格式为 "[PCF85063] <msg>"
        """
        if self._debug:
            print("[PCF85063] %s" % msg)

    def _read_reg(self, reg, nbytes, retries=2, delay_ms=5):
        """
        读取寄存器（带重试机制）

        Args:
            reg (int): 寄存器起始地址
            nbytes (int): 读取字节数
            retries (int): 最大重试次数，默认 2
            delay_ms (int): 重试间隔（毫秒），默认 5

        Returns:
            bytearray: 读取到的数据

        Raises:
            RuntimeError: 所有重试均失败后抛出
        """
        buf = bytearray(nbytes)
        for attempt in range(retries + 1):
            try:
                self._i2c.readfrom_mem_into(self._addr, reg, buf)
                return buf
            except OSError:
                if attempt == retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (reg, retries))
                time.sleep_ms(delay_ms)
        return buf

    def _write_reg(self, reg, data, retries=2, delay_ms=5):
        """
        写入寄存器（带重试机制）

        Args:
            reg (int): 寄存器起始地址
            data (bytes): 写入数据
            retries (int): 最大重试次数，默认 2
            delay_ms (int): 重试间隔（毫秒），默认 5

        Raises:
            RuntimeError: 所有重试均失败后抛出
        """
        for attempt in range(retries + 1):
            try:
                self._i2c.writeto_mem(self._addr, reg, data)
                return
            except OSError:
                if attempt == retries:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (reg, retries))
                time.sleep_ms(delay_ms)

    def reset(self):
        """
        执行软件复位

        Notes:
            - 向 CTRL1 寄存器写入 0x58（设置 SR 软件复位位），
              触发内部复位序列，所有寄存器恢复默认值
            - 副作用：修改 CTRL1 寄存器内容
        ==========================================
        Perform soft reset.

        Notes:
            - Writes 0x58 to CTRL1 register (sets SR software reset bit),
              triggers internal reset sequence, all registers return to defaults
            - Side effect: modifies CTRL1 register contents
        """
        self._log("performing soft reset")
        self._write_reg(REG_CTRL1, b"\x58")

    def datetime(self, value=None):
        """
        获取或设置日期时间（兼容 machine.RTC 接口）

        Args:
            value (tuple): 7 元组 (year, month, day, weekday, hour, minute, second)
                           若为 None 则读取当前时间

        Returns:
            tuple: 读取时返回 7 元组 (year, month, day, weekday, hour, minute, second)
                   设置时返回 None

        Raises:
            ValueError: 设置时参数无效
            RuntimeError: I2C 通信失败

        Notes:
            - 兼容 machine.RTC.datetime() 接口，行为一致
            - 设置时自动将年份减去 _year_base 后写入寄存器
        ==========================================
        Get or set datetime (compatible with machine.RTC interface).

        Args:
            value (tuple): 7-tuple (year, month, day, weekday, hour, minute, second)
                           If None, read current datetime

        Returns:
            tuple: 7-tuple (year, month, day, weekday, hour, minute, second) when reading
                   None when setting

        Raises:
            ValueError: Invalid parameter when setting
            RuntimeError: I2C communication failed

        Notes:
            - Compatible with machine.RTC.datetime() interface
            - When setting, year is auto-offset by _year_base before writing
        """
        if value is None:
            return self.read_datetime()
        self.set_datetime(value)
        return None

    def set_datetime(self, value):
        """
        设置日期时间

        Args:
            value (tuple): 7 元组 (year, month, day, weekday, hour, minute, second)

        Raises:
            ValueError: 参数为 None 或类型/长度无效
            RuntimeError: I2C 通信失败

        Notes:
            - 年份自动减去 _year_base 后以 BCD 格式写入寄存器
            - 各时间字段均转换为 BCD 格式存储
            - 副作用：修改 RTC 当前时间
        ==========================================
        Set datetime.

        Args:
            value (tuple): 7-tuple (year, month, day, weekday, hour, minute, second)

        Raises:
            ValueError: Parameter is None or has invalid type/length
            RuntimeError: I2C communication failed

        Notes:
            - Year is auto-offset by _year_base and stored in BCD format
            - Each time field is converted to BCD format
            - Side effect: modifies RTC current time
        """
        # 参数校验：不能为 None
        if value is None:
            raise ValueError("value must not be None")
        # 参数校验：必须是元组或列表
        if not isinstance(value, (tuple, list)):
            raise ValueError("value must be tuple or list, got %s" % type(value))
        # 参数校验：至少包含 7 个元素
        if len(value) < 7:
            raise ValueError("value must have at least 7 elements, got %d" % len(value))

        year, month, day, weekday, hour, minute, second = value[:7]

        # 年份偏移计算：实际年份减去基准后存储
        year = year - self._year_base

        # 拼接 7 字节时间数据，各字段均转为 BCD 格式
        data = bytes(
            (
                dec_to_bcd(second),
                dec_to_bcd(minute),
                dec_to_bcd(hour),
                dec_to_bcd(day),
                dec_to_bcd(weekday),
                dec_to_bcd(month),
                dec_to_bcd(year),
            )
        )
        self._log("setting datetime: %s" % str(value[:7]))
        self._write_reg(REG_SECONDS, data)

    def read_datetime(self):
        """
        读取当前日期时间

        Returns:
            tuple: 7 元组 (year, month, day, weekday, hour, minute, second)

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - 从寄存器读取 7 字节 BCD 数据并转换为十进制
            - 读取后屏蔽各字段的无效位（如秒的 bit 7 为 OS 标志）
            - 年份自动加上 _year_base 后返回
        ==========================================
        Read current datetime.

        Returns:
            tuple: 7-tuple (year, month, day, weekday, hour, minute, second)

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - Reads 7 bytes of BCD data from registers and converts to decimal
            - Masks invalid bits after reading (e.g. bit 7 of seconds is OS flag)
            - Year is auto-offset by _year_base before returning
        """
        # 从 SECONDS 寄存器开始连续读取 7 个时间寄存器
        buf = self._read_reg(REG_SECONDS, 7)

        # 从 BCD 转换为十进制，同时屏蔽各字段的无效位
        second = bcd_to_dec(buf[0] & 0x7F)  # bit 7: OS 振荡停止标志
        minute = bcd_to_dec(buf[1] & 0x7F)  # bit 7: 未使用
        hour = bcd_to_dec(buf[2] & 0x3F)  # bit 7-6: 未使用
        day = bcd_to_dec(buf[3] & 0x3F)  # bit 7-6: 未使用
        weekday = bcd_to_dec(buf[4] & 0x07)  # bit 7-3: 未使用
        month = bcd_to_dec(buf[5] & 0x1F)  # bit 7-5: 未使用
        # 年份加上基准偏移后返回
        year = bcd_to_dec(buf[6]) + self._year_base

        result = (year, month, day, weekday, hour, minute, second)
        self._log("read datetime: %s" % str(result))
        return result

    def set_alarm(self, second=ALARM_DISABLE, minute=ALARM_DISABLE, hour=ALARM_DISABLE, day=ALARM_DISABLE, weekday=ALARM_DISABLE):
        """
        配置闹钟参数

        Args:
            second (int): 秒（0-59），默认 ALARM_DISABLE(0x80) 表示禁用此字段
            minute (int): 分（0-59），默认 ALARM_DISABLE(0x80)
            hour (int): 时（0-23），默认 ALARM_DISABLE(0x80)
            day (int): 日（1-31），默认 ALARM_DISABLE(0x80)
            weekday (int): 星期（0-6），默认 ALARM_DISABLE(0x80)

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - 每个时间字段可单独启用或禁用（设为 ALARM_DISABLE 即禁用）
            - 字段值超出范围时自动钳位到有效范围内（保留原有安全行为）
            - 闹钟触发需配合 enable_alarm_interrupt() 启用中断输出
            - 副作用：修改闹钟寄存器组，可能影响当前闹钟状态
        ==========================================
        Configure alarm parameters.

        Args:
            second (int): Seconds (0-59), default ALARM_DISABLE(0x80) to disable
            minute (int): Minutes (0-59), default ALARM_DISABLE(0x80)
            hour (int): Hours (0-23), default ALARM_DISABLE(0x80)
            day (int): Day (1-31), default ALARM_DISABLE(0x80)
            weekday (int): Weekday (0-6), default ALARM_DISABLE(0x80)

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - Each time field can be individually enabled or disabled (set to ALARM_DISABLE)
            - Out-of-range values are auto-clamped to valid range (preserving original safety)
            - Use enable_alarm_interrupt() to enable interrupt output when alarm triggers
            - Side effect: modifies alarm registers, may affect current alarm state
        """
        # 组装 5 字节闹钟寄存器数据
        # 每个字段经过 _alarm_value 处理：禁用检查 + 范围钳位 + BCD 转换
        data = bytes(
            (
                self._alarm_value(second, 0, 59),
                self._alarm_value(minute, 0, 59),
                self._alarm_value(hour, 0, 23),
                self._alarm_value(day, 1, 31),
                self._alarm_value(weekday, 0, 6),
            )
        )
        self._log("setting alarm: sec=%s min=%s hour=%s day=%s wday=%s" % (str(second), str(minute), str(hour), str(day), str(weekday)))
        self._write_reg(REG_ALARM_SECONDS, data)

    def enable_alarm_interrupt(self, enable=True):
        """
        启用或禁用闹钟中断输出

        Args:
            enable (bool): True 启用中断输出，False 禁用

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - 修改 CTRL2 寄存器的 AIE 位（bit 7）控制中断输出
            - 启用时同时清零 AF 闹钟标志位（bit 6），防止挂起的中断立即触发
            - 副作用：读取并修改 CTRL2 寄存器
        ==========================================
        Enable or disable alarm interrupt output.

        Args:
            enable (bool): True to enable interrupt output, False to disable

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - Modifies AIE bit (bit 7) of CTRL2 register to control interrupt output
            - When enabling, also clears AF alarm flag (bit 6) to prevent immediate trigger
            - Side effect: reads and modifies CTRL2 register
        """
        # 读取当前 CTRL2 寄存器值
        value = self._read_reg(REG_CTRL2, 1)[0]
        if enable:
            # 设置闹钟中断使能位 AIE
            value |= 0x80
            # 清零闹钟标志位 AF，防止挂起中断立即触发
            value &= ~0x40
        else:
            # 清零闹钟中断使能位 AIE
            value &= ~0x80

        self._log("setting alarm interrupt: %s" % ("enabled" if enable else "disabled"))
        self._write_reg(REG_CTRL2, bytes([value]))

    def deinit(self):
        """
        释放硬件资源

        Notes:
            - 自动禁用闹钟中断输出，避免引脚持续产生中断信号
            - 清除实例持有的硬件引用
            - 副作用：修改 CTRL2 寄存器（禁用 AIE 位）
        ==========================================
        Release hardware resources.

        Notes:
            - Disables alarm interrupt output to prevent lingering interrupt signals
            - Clears hardware references held by instance
            - Side effect: modifies CTRL2 register (disables AIE bit)
        """
        self._log("deinitializing")
        # 禁用闹钟中断输出，防止引脚持续产生中断
        self.enable_alarm_interrupt(False)
        # 清除硬件引用
        self._i2c = None
        self._addr = None

    def _alarm_value(self, value, low, high):
        """
        处理闹钟字段值：检查禁用标志、钳位范围、转 BCD 格式

        Args:
            value (int): 输入值
            low (int): 有效范围下限
            high (int): 有效范围上限

        Returns:
            int: 处理后的寄存器值（ALARM_DISABLE 或 BCD 编码值）
        """
        # 闹钟禁用标志直接返回
        if value == ALARM_DISABLE:
            return ALARM_DISABLE
        # 钳位到有效范围（保留原有安全行为）
        if value < low:
            value = low
        if value > high:
            value = high
        # 转换为 BCD 并清除 bit 7（确保使能标志有效）
        return dec_to_bcd(value) & 0x7F


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
