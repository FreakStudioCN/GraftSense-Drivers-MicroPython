# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : hogeiha
# @File    : tsl2561.py
# @Description : TSL2561 数字光照强度传感器 I2C 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from machine import I2C, SoftI2C
from micropython import const
from math import pow

# ======================================== 全局变量 ============================================

# TSL2561 命令位，取值 0x80
COMMAND_BIT = const(0x80)

# TSL2561 控制寄存器，取值 0x00
REG_CONTROL = const(0x00)

# TSL2561 时序寄存器，取值 0x01
REG_TIMING = const(0x01)

# TSL2561 ID 寄存器，取值 0x0A
REG_ID = const(0x0A)

# TSL2561 可见光和红外通道低字节寄存器，取值 0x0C
REG_DATA0LOW = const(0x0C)

# TSL2561 可见光和红外通道高字节寄存器，取值 0x0D
REG_DATA0HIGH = const(0x0D)

# TSL2561 红外通道低字节寄存器，取值 0x0E
REG_DATA1LOW = const(0x0E)

# TSL2561 红外通道高字节寄存器，取值 0x0F
REG_DATA1HIGH = const(0x0F)

# TSL2561 上电命令，取值 0x03
CONTROL_POWER_ON = const(0x03)

# TSL2561 断电命令，取值 0x00
CONTROL_POWER_OFF = const(0x00)

# 快速积分时间，约 13.7ms
T_FAST = const(0b00)

# 中速积分时间，约 101ms
T_MEDIUM = const(0b01)

# 慢速积分时间，约 402ms
T_SLOW = const(0b10)

# 手动积分模式
T_MANUAL = const(0b11)

# TSL2561 默认 I2C 地址，取值 0x39
DEFAULT_ADDR = const(0x39)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class TSL2561:
    """
    TSL2561 数字光照强度传感器驱动类。
    Attributes:
        _i2c (I2C | SoftI2C): I2C 总线对象。
        _addr (int): 传感器 I2C 地址。
        _gain (bool): 是否启用 16 倍增益。
        _timing (int): 当前积分时间配置。

    Methods:
        set_power_up(): 设置传感器上电或断电。
        set_timing_gain(): 设置积分时间和增益。
        get_id(): 读取传感器 ID。
        read_raw(): 读取原始双通道光照数据。
        get_lumi(): 读取光照强度 lux。

    Notes:
        支持 Raspberry Pi Pico 的 machine.I2C 和 machine.SoftI2C。

    ==========================================
    TSL2561 digital luminosity sensor driver class.
    Attributes:
        _i2c (I2C | SoftI2C): I2C bus object.
        _addr (int): Sensor I2C address.
        _gain (bool): Whether 16x gain is enabled.
        _timing (int): Current integration timing setting.

    Methods:
        set_power_up(): Power the sensor on or off.
        set_timing_gain(): Set integration timing and gain.
        get_id(): Read sensor ID.
        read_raw(): Read raw two channel luminosity data.
        get_lumi(): Read luminosity in lux.

    Notes:
        Supports Raspberry Pi Pico machine.I2C and machine.SoftI2C.
    """

    def __init__(self, i2c, addr: int = DEFAULT_ADDR) -> None:
        """
        初始化 TSL2561 传感器。
        Args:
            i2c (I2C | SoftI2C): 已初始化的 I2C 总线对象。
            addr (int): 传感器 I2C 地址，默认 0x39。

        Raises:
            ValueError: I2C 对象为空或地址为空时抛出。
            TypeError: I2C 对象类型非法时抛出。
            OSError: 未扫描到目标地址时抛出。

        Notes:
            TSL2561 常见地址为 0x29、0x39、0x49。

        ==========================================
        Initialize TSL2561 sensor.
        Args:
            i2c (I2C | SoftI2C): Initialized I2C bus object.
            addr (int): Sensor I2C address, default 0x39.

        Raises:
            ValueError: Raised when I2C object or address is None.
            TypeError: Raised when I2C object type is invalid.
            OSError: Raised when target address is not found.

        Notes:
            Common TSL2561 addresses are 0x29, 0x39 and 0x49.
        """
        if i2c is None:
            raise ValueError("I2C object cannot be None")

        if addr is None:
            raise ValueError("Address cannot be None")

        if not isinstance(i2c, (I2C, SoftI2C)):
            raise TypeError("I2C object required")

        if addr not in i2c.scan():
            raise OSError("TSL2561 not found")

        self._i2c = i2c
        self._addr = addr
        self._gain = False
        self._timing = T_SLOW

        self.set_power_up(True)
        self.set_timing_gain(T_SLOW, gain=False)

    def _write_u8(self, reg: int, value: int) -> None:
        """
        写入 8 位寄存器。
        Args:
            reg (int): 寄存器地址。
            value (int): 写入数值。

        Raises:
            无

        Notes:
            自动添加 TSL2561 命令位。

        ==========================================
        Write an 8 bit register.
        Args:
            reg (int): Register address.
            value (int): Value to write.

        Raises:
            None

        Notes:
            TSL2561 command bit is added automatically.
        """
        if reg is None:
            raise ValueError("Register cannot be None")

        if value is None:
            raise ValueError("Value cannot be None")

        if not isinstance(reg, int):
            raise TypeError("Register must be integer")

        if not isinstance(value, int):
            raise TypeError("Value must be integer")

        if reg < 0 or reg > 0xFF:
            raise ValueError("Register out of range")

        if value < 0 or value > 0xFF:
            raise ValueError("Value out of range")

        self._i2c.writeto_mem(self._addr, COMMAND_BIT | reg, bytes([value]))

    def _read_u8(self, reg: int) -> int:
        """
        读取 8 位寄存器。
        Args:
            reg (int): 寄存器地址。

        Raises:
            无

        Notes:
            自动添加 TSL2561 命令位。

        ==========================================
        Read an 8 bit register.
        Args:
            reg (int): Register address.

        Raises:
            None

        Notes:
            TSL2561 command bit is added automatically.
        """
        if reg is None:
            raise ValueError("Register cannot be None")

        if not isinstance(reg, int):
            raise TypeError("Register must be integer")

        if reg < 0 or reg > 0xFF:
            raise ValueError("Register out of range")

        return self._i2c.readfrom_mem(self._addr, COMMAND_BIT | reg, 1)[0]

    def _read_u16(self, low_reg: int, high_reg: int) -> int:
        """
        读取 16 位小端寄存器值。
        Args:
            low_reg (int): 低字节寄存器地址。
            high_reg (int): 高字节寄存器地址。

        Raises:
            无

        Notes:
            TSL2561 数据寄存器为低字节在前。

        ==========================================
        Read a 16 bit little endian register value.
        Args:
            low_reg (int): Low byte register address.
            high_reg (int): High byte register address.

        Raises:
            None

        Notes:
            TSL2561 data registers are low byte first.
        """
        if low_reg is None:
            raise ValueError("Low register cannot be None")

        if high_reg is None:
            raise ValueError("High register cannot be None")

        if not isinstance(low_reg, int):
            raise TypeError("Low register must be integer")

        if not isinstance(high_reg, int):
            raise TypeError("High register must be integer")

        if low_reg < 0 or low_reg > 0xFF:
            raise ValueError("Low register out of range")

        if high_reg < 0 or high_reg > 0xFF:
            raise ValueError("High register out of range")

        low = self._read_u8(low_reg)
        high = self._read_u8(high_reg)

        return (high << 8) | low

    def set_power_up(self, state: bool = True) -> None:
        """
        设置传感器上电或断电。
        Args:
            state (bool): True 表示上电，False 表示断电。

        Raises:
            TypeError: state 不是布尔值时抛出。

        Notes:
            断电可降低功耗，但断电后无法读取光照数据。

        ==========================================
        Power the sensor on or off.
        Args:
            state (bool): True means power on and False means power off.

        Raises:
            TypeError: Raised when state is not boolean.

        Notes:
            Power off reduces consumption but disables luminosity reading.
        """
        if state is None:
            raise ValueError("State cannot be None")

        if not isinstance(state, bool):
            raise TypeError("State must be boolean")

        if state:
            self._write_u8(REG_CONTROL, CONTROL_POWER_ON)
        else:
            self._write_u8(REG_CONTROL, CONTROL_POWER_OFF)

    def set_timing_gain(
        self,
        timing: int = T_SLOW,
        gain: bool = False,
        manual_start: bool = True,
    ) -> None:
        """
        设置积分时间和增益。
        Args:
            timing (int): 积分时间配置。
            gain (bool): True 表示启用 16 倍增益。
            manual_start (bool): 手动模式下是否开始积分。

        Raises:
            ValueError: timing 取值非法时抛出。
            TypeError: gain 或 manual_start 类型非法时抛出。

        Notes:
            默认使用 402ms 慢速积分和 1 倍增益。

        ==========================================
        Set integration timing and gain.
        Args:
            timing (int): Integration timing setting.
            gain (bool): True enables 16x gain.
            manual_start (bool): Whether manual mode starts integration.

        Raises:
            ValueError: Raised when timing value is invalid.
            TypeError: Raised when gain or manual_start type is invalid.

        Notes:
            Default setting is 402ms slow integration and 1x gain.
        """
        if timing not in (T_FAST, T_MEDIUM, T_SLOW, T_MANUAL):
            raise ValueError("Invalid timing value")

        if not isinstance(gain, bool):
            raise TypeError("Gain must be boolean")

        if not isinstance(manual_start, bool):
            raise TypeError("Manual start must be boolean")

        value = timing

        if manual_start:
            value |= 0x08

        if gain:
            value |= 0x10

        self._write_u8(REG_TIMING, value)
        self._timing = timing
        self._gain = gain

    def get_id(self) -> tuple:
        """
        读取传感器 ID。
        Args:
            无

        Raises:
            无

        Notes:
            返回值为芯片型号编号和版本编号。

        ==========================================
        Read sensor ID.
        Args:
            None

        Raises:
            None

        Notes:
            Returns part number and revision number.
        """
        id_reg = self._read_u8(REG_ID)
        part_number = id_reg >> 4
        revision = id_reg & 0x0F

        return part_number, revision

    def read_raw(self) -> tuple:
        """
        读取原始双通道光照数据。
        Args:
            无

        Raises:
            无

        Notes:
            返回通道 0 和通道 1 的原始值。

        ==========================================
        Read raw two channel luminosity data.
        Args:
            None

        Raises:
            None

        Notes:
            Returns raw values of channel 0 and channel 1.
        """
        channel_0 = self._read_u16(REG_DATA0LOW, REG_DATA0HIGH)
        channel_1 = self._read_u16(REG_DATA1LOW, REG_DATA1HIGH)

        if not self._gain:
            channel_0 <<= 4
            channel_1 <<= 4

        return channel_0, channel_1

    def get_lumi(self) -> float:
        """
        读取光照强度。
        Args:
            无

        Raises:
            无

        Notes:
            返回单位为 lux 的光照强度估算值。

        ==========================================
        Read luminosity.
        Args:
            None

        Raises:
            None

        Notes:
            Returns estimated luminosity in lux.
        """
        channel_0, channel_1 = self.read_raw()
        lux = 0

        if channel_0 != 0:
            ratio = channel_1 / channel_0

            if ratio <= 0.5:
                lux = 0.0304 * channel_0 - 0.062 * channel_0 * pow(ratio, 1.4)
            elif ratio <= 0.61:
                lux = 0.0224 * channel_0 - 0.031 * channel_1
            elif ratio <= 0.8:
                lux = 0.0128 * channel_0 - 0.0153 * channel_1
            elif ratio <= 1.3:
                lux = 0.00146 * channel_0 - 0.00112 * channel_1
            else:
                lux = 0

        if lux < 0:
            lux = 0

        return lux

    @property
    def lux(self) -> float:
        """
        返回当前光照强度。
        Args:
            无

        Raises:
            无

        Notes:
            该属性等同于 get_lumi()。

        ==========================================
        Return current luminosity.
        Args:
            None

        Raises:
            None

        Notes:
            This property is equivalent to get_lumi().
        """
        return self.get_lumi()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
