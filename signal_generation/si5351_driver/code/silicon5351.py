# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : silicon5351.py
# @Description : silicon5351时钟驱动 for MicroPython，代码参考自：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : MIT

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================

# 导入micropython内置库
import sys
# 导入常量模块
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class SI5351_I2C:
    """
       基于 SI5351 的 I2C 时钟发生器驱动类。支持配置 PLL 倍频、Multisynth 分频，
       控制输出通道的使能、相位、极性和驱动能力，可产生多路可调频率的时钟信号。

       Attributes:
           i2c: MicroPython 或 CircuitPython 的 I2C 实例。
           crystal (int): 晶振频率（Hz）。
           address (int): I2C 地址，默认 0x60。
           vco (dict): PLL VCO 频率缓存 {pll_id: vco_freq}。
           pll (dict): 输出通道使用的 PLL 选择 {output: pll_id}。
           quadrature (dict): 是否启用正交输出 {output: bool}。
           invert (dict): 是否启用反相输出 {output: bool}。
           drive_strength (dict): 输出驱动能力配置 {output: 驱动等级}。
           div (dict): Multisynth 分频缓存 {output: divisor}。

       Methods:
           __init__(i2c, crystal, load, address): 初始化并配置晶振与寄存器。
           _read_bulk(register, nbytes): 从寄存器批量读取字节。
           _write_bulk(register, values): 向寄存器批量写入字节。
           _read(register): 读取单个寄存器。
           _write(register, value): 写入单个寄存器。
           write_config(...): 写入 PLL 或 Multisynth 的配置。
           set_phase(output, div): 设置输出相位。
           reset_pll(pll): 复位 PLL。
           init_multisynth(output, integer_mode): 初始化 Multisynth 输出。
           approximate_fraction(...): 分数逼近算法。
           init_clock(...): 初始化输出通道状态。
           enable_output(output): 使能指定输出。
           disable_output(output): 禁用指定输出。
           setup_pll(pll, mul, num, denom): 配置 PLL 倍频。
           setup_multisynth(...): 配置 Multisynth 分频。
           set_freq_fixedpll(output, freq): 在固定 PLL 下设置输出频率。
           set_freq_fixedms(output, freq): 在固定 Multisynth 下设置输出频率。
           disabled_states(output, state): 设置输出禁用时的状态。
           disable_oeb(mask): 屏蔽 OEB 引脚对输出的控制。
       ==========================================
       I2C driver for the SI5351 clock generator. Supports PLL multiplication,
       Multisynth division, and control of output enable, phase, polarity,
       and drive strength, allowing generation of multiple adjustable clocks.

       Attributes:
           i2c: MicroPython or CircuitPython I2C instance.
           crystal (int): Crystal frequency (Hz).
           address (int): I2C address (default 0x60).
           vco (dict): Cached PLL VCO frequencies {pll_id: vco_freq}.
           pll (dict): PLL selection for each output {output: pll_id}.
           quadrature (dict): Quadrature output enable {output: bool}.
           invert (dict): Inverted output enable {output: bool}.
           drive_strength (dict): Output drive strength {output: level}.
           div (dict): Cached Multisynth divisors {output: divisor}.

       Methods:
           __init__(i2c, crystal, load, address): Initialize crystal and registers.
           _read_bulk(register, nbytes): Read multiple bytes from a register.
           _write_bulk(register, values): Write multiple bytes to a register.
           _read(register): Read a single register.
           _write(register, value): Write a single register.
           write_config(...): Configure PLL or Multisynth registers.
           set_phase(output, div): Set phase offset for an output.
           reset_pll(pll): Reset a PLL (A or B).
           init_multisynth(output, integer_mode): Initialize a Multisynth output.
           approximate_fraction(...): Fraction approximation helper.
           init_clock(...): Initialize output channel state.
           enable_output(output): Enable a clock output.
           disable_output(output): Disable a clock output.
           setup_pll(pll, mul, num, denom): Configure PLL frequency multiplier.
           setup_multisynth(...): Configure Multisynth divider.
           set_freq_fixedpll(output, freq): Set output frequency with fixed PLL.
           set_freq_fixedms(output, freq): Set output frequency with fixed Multisynth.
           disabled_states(output, state): Set disabled state for outputs.
           disable_oeb(mask): Disable OEB pin control for given outputs.
       """
    SI5351_I2C_ADDRESS_DEFAULT = const(0x60)

    SI5351_CRYSTAL_LOAD_6PF = const(1)
    SI5351_CRYSTAL_LOAD_8PF = const(2)
    SI5351_CRYSTAL_LOAD_10PF = const(3)

    SI5351_CLK_DRIVE_STRENGTH_2MA = const(0)
    SI5351_CLK_DRIVE_STRENGTH_4MA = const(1)
    SI5351_CLK_DRIVE_STRENGTH_6MA = const(2)
    SI5351_CLK_DRIVE_STRENGTH_8MA = const(3)

    SI5351_DIS_STATE_LOW = const(0)
    SI5351_DIS_STATE_HIGH = const(1)
    SI5351_DIS_STATE_HIGH_IMPEDANCE = const(2)
    SI5351_DIS_STATE_NEVER_DISABLED = const(3)
    SI5351_MULTISYNTH_RX_MAX = const(7)
    SI5351_MULTISYNTH_C_MAX = const(1048575)  # fits in [19:0] or 2**20-1

    SI5351_MULTISYNTH_DIV_MIN = const(8)  # 4 and 6 only allowed in integer mode
    SI5351_MULTISYNTH_DIV_MAX = const(2048)  # DIV_MAX = 128 for quadrature

    SI5351_MULTISYNTH_MUL_MIN = const(15)
    SI5351_MULTISYNTH_MUL_MAX = const(90)

    # SI5351_REGISTER_PLL_RESET
    SI5351_PLL_RESET_A = const(1 << 5)
    SI5351_PLL_RESET_B = const(1 << 7)

    # SI5351_REGISTER_CLKn_CONTROL
    SI5351_CLK_POWERDOWN = const(1 << 7)
    SI5351_CLK_INPUT_MULTISYNTH_N = const(3 << 2)
    SI5351_CLK_INTEGER_MODE = const(1 << 6)
    SI5351_CLK_PLL_SELECT_A = const(0 << 5)
    SI5351_CLK_PLL_SELECT_B = const(1 << 5)
    SI5351_CLK_INVERT = const(1 << 4)

    # registers
    SI5351_REGISTER_DEVICE_STATUS = const(0)
    SI5351_REGISTER_OUTPUT_ENABLE_CONTROL = const(3)
    SI5351_REGISTER_OEB_ENABLE_CONTROL = const(9)
    SI5351_REGISTER_CLK0_CONTROL = const(16)
    SI5351_REGISTER_DIS_STATE_1 = const(24)
    SI5351_REGISTER_DIS_STATE_2 = const(25)
    SI5351_REGISTER_PLL_A = const(26)
    SI5351_REGISTER_PLL_B = const(34)
    SI5351_REGISTER_MULTISYNTH0_PARAMETERS_1 = const(42)
    SI5351_REGISTER_MULTISYNTH1_PARAMETERS_1 = const(50)
    SI5351_REGISTER_MULTISYNTH2_PARAMETERS_1 = const(58)
    SI5351_REGISTER_CLK0_PHOFF = const(165)
    SI5351_REGISTER_PLL_RESET = const(177)
    SI5351_REGISTER_CRYSTAL_LOAD = const(183)

    def _read_bulk(self, register, nbytes):
        """
        从指定寄存器连续读取多个字节。

        Args:
            register (int): 起始寄存器地址。
            nbytes (int): 需要读取的字节数。

        Returns:
            bytearray: 读取到的数据缓冲区。
        ==========================================
        Read multiple bytes starting from a given register.

        Args:
            register (int): Starting register address.
            nbytes (int): Number of bytes to read.

        Returns:
            bytearray: Buffer containing the read data.

        """

        buf = bytearray(nbytes)
        self.i2c.readfrom_mem_into(self.address, register, buf)
        return buf

    def _write_bulk(self, register, values):
        """
        向指定寄存器连续写入多个字节。

        Args:
            register (int): 起始寄存器地址。
            values (list[int]): 要写入的字节序列。
        ==========================================
        Write multiple bytes to a given register.

        Args:
            register (int): Starting register address.
            values (list[int]): List of bytes to write.
        """
        self.i2c.writeto_mem(self.address, register, bytes(values))

    def _read(self, register):
        """
        从寄存器读取一个字节。

        Args:
            register (int): 寄存器地址。

        Returns:
            int: 读取到的单字节数据。
        ==========================================
        Read a single byte from a register.

        Args:
            register (int): Register address.

        Returns:
            int: The byte value read from register.
        """
        return self._read_bulk(register, 1)[0]

    def _write(self, register, value):
        """
        向寄存器写入一个字节。

        Args:
            register (int): 寄存器地址。
            value (int): 要写入的值。
        ==========================================
        Write a single byte to a register.

        Args:
            register (int): Register address.
            value (int): Value to write.
        """
        self._write_bulk(register, [value])

    def write_config(self, reg, whole, num, denom, rdiv):
        """
        按照分频配置写入 PLL 或 Multisynth 参数。

        Args:
            reg (int): 配置寄存器地址（0x00~0xFF）。
            whole (int): 整数部分，通常 0..16383。
            num (int): 分数分子。
            denom (int): 分数分母，不能为 0。
            rdiv (int): 附加二分频因子 (0..7)。

        Raises:
            TypeError: 如果参数类型不正确。
            ValueError: 如果参数值超出允许范围。
            
        ==========================================
        Write PLL or Multisynth configuration.

        Args:
            reg (int): Register address to configure (0x00..0xFF).
            whole (int): Integer part of divider (0..16383).
            num (int): Numerator of fractional divider.
            denom (int): Denominator of fractional divider (non-zero).
            rdiv (int): Additional divide-by-2^rdiv factor (0..7).

        Raises:
            TypeError: If argument types are invalid.
            ValueError: If argument values are out of range.
        """
        # 类型检查
        for name, value in zip(
                ["reg", "whole", "num", "denom", "rdiv"],
                [reg, whole, num, denom, rdiv]
        ):
            if not isinstance(value, int):
                raise TypeError(f"{name} must be an int")

        # 值检查
        if not 0 <= reg <= 0xFF:
            raise ValueError("reg must be 0x00..0xFF")
        if not 0 <= whole <= 16383:
            raise ValueError("whole must be 0..16383")
        if denom == 0:
            raise ValueError("denom cannot be 0")
        if not 0 <= rdiv <= 7:
            raise ValueError("rdiv must be 0..7")

        # 计算寄存器值
        P1 = 128 * whole + int(128.0 * num / denom) - 512
        P2 = 128 * num - denom * int(128.0 * num / denom)
        P3 = denom

        # 写入寄存器
        self._write_bulk(reg, [
            (P3 & 0x0FF00) >> 8,
            (P3 & 0x000FF),
            (P1 & 0x30000) >> 16 | rdiv << 4,
            (P1 & 0x0FF00) >> 8,
            (P1 & 0x000FF),
            (P3 & 0xF0000) >> 12 | (P2 & 0xF0000) >> 16,
            (P2 & 0x0FF00) >> 8,
            (P2 & 0x000FF)
        ])

    def set_phase(self, output, div):
        """
        设置指定输出的相位偏移。

        Args:
            output (int): 输出通道编号 (clkout)，通常 0..2。
            div (int): 相位偏移值，单位为分频周期的 tick，0..255。

        Raises:
            TypeError: 如果 output 或 div 不是 int。
            ValueError: 如果 output 或 div 不在允许范围内。
            
        ==========================================
        Set phase offset for a given output.

        Args:
            output (int): Clock output number (clkout), usually 0..2.
            div (int): Phase offset value in ticks of divider period, 0..255.

        Raises:
            TypeError: If output or div is not an int.
            ValueError: If output or div is out of range.
        """
        # 类型检查
        if not isinstance(output, int):
            raise TypeError("output must be an int")
        if not isinstance(div, int):
            raise TypeError("div must be an int")

        # 值检查
        if not 0 <= output <= 2:
            raise ValueError("output must be in range 0..2")
        if not 0 <= div <= 255:
            raise ValueError("div must be in range 0..255")

        self._write(self.SI5351_REGISTER_CLK0_PHOFF + output, div & 0xFF)

    def reset_pll(self, pll):
        """
        复位指定的 PLL。

        Args:
            pll (int): PLL 编号 (0=PLLA, 1=PLLB)。

        Raises:
            TypeError: 如果 pll 不是 int。
            ValueError: 如果 pll 不在 0 或 1 范围内。

        ==========================================
        Reset the specified PLL.

        Args:
            pll (int): PLL number (0=PLLA, 1=PLLB).

        Raises:
            TypeError: If pll is not an int.
            ValueError: If pll is not 0 or 1.
        """
        # 类型检查
        if not isinstance(pll, int):
            raise TypeError("pll must be an int")
        # 值检查
        if pll not in (0, 1):
            raise ValueError("pll must be 0 (PLLA) or 1 (PLLB)")
        if pll == 0: value = self.SI5351_PLL_RESET_A
        if pll == 1: value = self.SI5351_PLL_RESET_B
        self._write(self.SI5351_REGISTER_PLL_RESET, value)

    def init_multisynth(self, output, integer_mode):
        """
        初始化指定输出的 Multisynth 控制寄存器。

        Args:
            output (int): 输出通道编号 (clkout)，通常 0..2。
            integer_mode (bool): 是否启用整数分频模式。

        Raises:
            TypeError: 如果 output 不是 int 或 integer_mode 不是 bool。
            ValueError: 如果 output 不在允许范围内。

        Notes:
            会根据 invert / quadrature / pll 配置设置控制位。

        ==========================================
        Initialize Multisynth control register for an output.

        Args:
            output (int): Clock output number (clkout), usually 0..2.
            integer_mode (bool): Whether to enable integer division mode.

        Raises:
            TypeError: If output is not int or integer_mode is not bool.
            ValueError: If output is out of range.

        Notes:
            Configures control bits according to invert, quadrature, and pll selection.
        """
        # 类型检查
        if not isinstance(output, int):
            raise TypeError("output must be an int")
        if not isinstance(integer_mode, bool):
            raise TypeError("integer_mode must be a bool")
        # 值检查
        if not 0 <= output <= 2:
            raise ValueError("output must be in range 0..2")

        pll = self.pll[output]
        value = self.SI5351_CLK_INPUT_MULTISYNTH_N
        value |= self.drive_strength[output]
        if integer_mode:
            value |= self.SI5351_CLK_INTEGER_MODE
        if self.invert[output] or self.quadrature[output]:
            value |= self.SI5351_CLK_INVERT
        if pll == 0:
            value |= self.SI5351_CLK_PLL_SELECT_A
        if pll == 1:
            value |= self.SI5351_CLK_PLL_SELECT_B
        self._write(self.SI5351_REGISTER_CLK0_CONTROL + output, value)

    def approximate_fraction(self, n, d, max_denom):
        """
        将分数 (n/d) 近似为分母不超过 max_denom 的分数。

        Args:
            n (int): 原始分子。
            d (int): 原始分母，不能为 0。
            max_denom (int): 允许的最大分母，必须大于 0。

        Returns:
            tuple[int, int]: 近似后的 (num, denom)。

        Raises:
            TypeError: 如果 n、d 或 max_denom 不是 int。
            ValueError: 如果 d 为 0 或 max_denom <= 0。

        Notes:
            算法基于 CPython fractions 模块。
            https://github.com/python/cpython/blob/master/Lib/fractions.py

        ==========================================
        Approximate fraction (n/d) with denominator not exceeding max_denom.

        Args:
            n (int): Original numerator.
            d (int): Original denominator, cannot be 0.
            max_denom (int): Maximum allowed denominator, must be > 0.

        Returns:
            tuple[int, int]: Approximated (num, denom).

        Raises:
            TypeError: If n, d, or max_denom is not int.
            ValueError: If d is 0 or max_denom <= 0.

        Notes:
            Algorithm adapted from CPython fractions module.
            https://github.com/python/cpython/blob/master/Lib/fractions.py
        """
        # 类型检查
        for name, value in zip(["n", "d", "max_denom"], [n, d, max_denom]):
            if not isinstance(value, int):
                raise TypeError(f"{name} must be an int")

        # 值检查
        if d == 0:
            raise ValueError("d (denominator) cannot be 0")
        if max_denom <= 0:
            raise ValueError("max_denom must be positive")

        denom = d
        if denom > max_denom:
            num = n
            p0 = 0
            q0 = 1
            p1 = 1
            q1 = 0
            while denom != 0:
                a = num // denom
                b = num % denom
                q2 = q0 + a * q1
                if q2 > max_denom:
                    break
                p2 = p0 + a * p1
                p0 = p1
                q0 = q1
                p1 = p2
                q1 = q2
                num = denom
                denom = b
            n = p1
            d = q1
        return n, d

    ###

    def __init__(self,
                 i2c,
                 crystal,
                 load=SI5351_CRYSTAL_LOAD_10PF,
                 address=SI5351_I2C_ADDRESS_DEFAULT):
        """
        初始化 SI5351 对象：

        Args:
            i2c: I2C 总线对象。
            crystal (float): 晶振频率，单位 Hz。
            load (int, optional): 晶振负载电容，可选值为
                SI5351_CRYSTAL_LOAD_6PF / SI5351_CRYSTAL_LOAD_8PF / SI5351_CRYSTAL_LOAD_10PF。
                默认 SI5351_CRYSTAL_LOAD_10PF。
            address (int, optional): I2C 地址，默认 SI5351_I2C_ADDRESS_DEFAULT。

        Raises:
            TypeError: 如果 i2c 不是 I2C 实例，或 crystal 不是 float/int，load 或 address 不是 int。
            ValueError: 如果 load 或 address 不在允许范围内。

        ==================================
        Initialize SI5351 object:
        Configure I2C bus, crystal frequency, crystal load capacitance,
        and I2C address. During initialization, the constructor waits
        until the chip finishes power-on self-test, disables all outputs,
        and sets the crystal load value.
        """
        # 类型检查
        from machine import I2C  # 假设使用 MicroPython I2C
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an I2C instance")
        if not isinstance(crystal, (int, float)):
            raise TypeError("crystal must be int or float")
        if not isinstance(load, int):
            raise TypeError("load must be an int")
        if not isinstance(address, int):
            raise TypeError("address must be an int")

        # 值检查
        allowed_loads = (self.SI5351_CRYSTAL_LOAD_6PF,
                         self.SI5351_CRYSTAL_LOAD_8PF,
                         self.SI5351_CRYSTAL_LOAD_10PF)
        if load not in allowed_loads:
            raise ValueError(f"load must be one of {allowed_loads}")
        if not 0x00 <= address <= 0x7F:
            raise ValueError("address must be 7-bit (0x00..0x7F)")
        self.i2c = i2c
        self.crystal = crystal
        self.address = address
        self.vco = {}
        self.pll = {}
        self.quadrature = {}
        self.invert = {}
        self.drive_strength = {}
        self.div = {}
        # wait until chip initializes before writing registers
        while self._read(self.SI5351_REGISTER_DEVICE_STATUS) & 0x80:
            pass
        # disable outputs 
        self._write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, 0xFF)
        # power down all 8 output drivers
        values = [self.SI5351_CLK_POWERDOWN] * 8
        self._write_bulk(self.SI5351_REGISTER_CLK0_CONTROL, values)
        # set crystal load value
        self._write(self.SI5351_REGISTER_CRYSTAL_LOAD, load << 6)

    def init_clock(self, output, pll, quadrature=False, invert=False,
                   drive_strength=SI5351_CLK_DRIVE_STRENGTH_8MA):
        """
        初始化指定的时钟输出 (clkout)。

        Args:
            output (int): 输出通道编号，通常 0..2。
            pll (int): 使用的 PLL (0=PLLA, 1=PLLB)。
            quadrature (bool): 是否启用正交输出。
            invert (bool): 是否反相输出。
            drive_strength (int): 输出驱动强度 (mA)，通常使用 SI5351_CLK_DRIVE_STRENGTH_* 常量。

        Raises:
            TypeError: 参数类型错误。
            ValueError: output 或 pll 值超出允许范围，drive_strength 不合法。

        Notes:
            仅更新库的内部状态，不会立即写入芯片。

        ==========================================
        Initialize a given clock output (clkout).

        Args:
            output (int): Clock output number, usually 0..2.
            pll (int): PLL to use (0=PLLA, 1=PLLB).
            quadrature (bool): Enable quadrature output.
            invert (bool): Invert output.
            drive_strength (int): Output drive strength in mA, typically SI5351_CLK_DRIVE_STRENGTH_*.

        Raises:
            TypeError: If argument types are incorrect.
            ValueError: If output or pll is out of range, or drive_strength is invalid.

        Notes:
            Only updates library state, no immediate I2C writes.
        """
        # 类型检查
        if not isinstance(output, int):
            raise TypeError("output must be int")
        if not isinstance(pll, int):
            raise TypeError("pll must be int")
        if not isinstance(quadrature, bool):
            raise TypeError("quadrature must be bool")
        if not isinstance(invert, bool):
            raise TypeError("invert must be bool")
        if not isinstance(drive_strength, int):
            raise TypeError("drive_strength must be int")

        # 值检查
        if not 0 <= output <= 2:
            raise ValueError("output must be in range 0..2")
        if pll not in (0, 1):
            raise ValueError("pll must be 0 (PLLA) or 1 (PLLB)")
        allowed_drives = (
            self.SI5351_CLK_DRIVE_STRENGTH_2MA,
            self.SI5351_CLK_DRIVE_STRENGTH_4MA,
            self.SI5351_CLK_DRIVE_STRENGTH_6MA,
            self.SI5351_CLK_DRIVE_STRENGTH_8MA
        )
        if drive_strength not in allowed_drives:
            raise ValueError(f"drive_strength must be one of {allowed_drives}")

        self.pll[output] = pll
        self.quadrature[output] = quadrature
        self.invert[output] = invert
        self.drive_strength[output] = drive_strength
        self.div[output] = None

    def enable_output(self, output):
        """
        使能指定的时钟输出。

        Args:
            output (int): 输出通道编号，通常 0..2。

        Raises:
            TypeError: 如果 output 不是 int。
            ValueError: 如果 output 不在允许范围内。
            
        ==========================================
        Enable the given clock output.

        Args:
            output (int): Clock output number, usually 0..2.

        Raises:
            TypeError: If output is not int.
            ValueError: If output is out of range.
        """
        # 类型检查
        if not isinstance(output, int):
            raise TypeError("output must be an int")
        # 值检查
        if not 0 <= output <= 2:
            raise ValueError("output must be in range 0..2")
        mask = self._read(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL)
        self._write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, mask & ~(1 << output))

    def disable_output(self, output):
        """
        禁用指定的时钟输出。

        Args:
            output (int): 输出通道编号，通常 0..2。

        Raises:
            TypeError: 如果 output 不是 int。
            ValueError: 如果 output 不在允许范围内。

        ==========================================
        Disable the given clock output.

        Args:
            output (int): Clock output number, usually 0..2.

        Raises:
            TypeError: If output is not int.
            ValueError: If output is out of range.
        """
        # 类型检查
        if not isinstance(output, int):
            raise TypeError("output must be an int")
        # 值检查
        if not 0 <= output <= 2:
            raise ValueError("output must be in range 0..2")
        mask = self._read(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL)
        self._write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, mask | (1 << output))

    def setup_pll(self, pll, mul, num=0, denom=1):
        """
        设置 PLL 的倍频参数。

        Args:
            pll (int): PLL 编号 (0=PLLA, 1=PLLB)。
            mul (int): 整数倍数 [15-90]。
            num (int): 分数分子 [0-1048574]。
            denom (int): 分数分母 [1-1048575]。

        Raises:
            TypeError: 参数类型错误。
            ValueError: 参数值不在允许范围。

        Notes:
            实际频率 = (mul + num/denom) * crystal。

        ==========================================
        Configure PLL multiplier.

        Args:
            pll (int): PLL number (0=PLLA, 1=PLLB).
            mul (int): Integer multiplier [15-90].
            num (int): Fractional numerator [0-1048574].
            denom (int): Fractional denominator [1-1048575].

        Raises:
            TypeError: If argument types are incorrect.
            ValueError: If argument values are out of allowed range.

        Notes:
            Actual PLL frequency = (mul + num/denom) * crystal.
        """
        # 类型检查
        for name, val in (("pll", pll), ("mul", mul), ("num", num), ("denom", denom)):
            if not isinstance(val, int):
                raise TypeError(f"{name} must be int")

        # 值检查
        if pll not in (0, 1):
            raise ValueError("pll must be 0 (PLLA) or 1 (PLLB)")
        if not 15 <= mul <= 90:
            raise ValueError("mul must be in range 15..90")
        if not 0 <= num <= 1048574:
            raise ValueError("num must be in range 0..1048574")
        if not 1 <= denom <= 1048575:
            raise ValueError("denom must be in range 1..1048575")

        vco = self.crystal * (mul + num / denom)
        if pll == 0:
            reg = self.SI5351_REGISTER_PLL_A
        if pll == 1:
            reg = self.SI5351_REGISTER_PLL_B
        self.write_config(reg, whole=mul, num=num, denom=denom, rdiv=0)
        self.vco[pll] = vco

    def setup_multisynth(self, output, div, num=0, denom=1, rdiv=0):
        """
        设置指定输出的 Multisynth 分频器。

        Args:
            output (int): 输出通道编号。
            div (int): 整数分频因子 [4-2047]。
            num (int): 分数分子 [0-1048574]。
            denom (int): 分数分母 [1-1048575]。
            rdiv (int): 附加二分频因子 (log2)。

        Raises:
            ValueError: 当 div 无效时div (int): 整数分频因子 [4-2047]。

        Notes:
            会同步相位并复位 PLL，以保证输出一致性。
        ==========================================
        Configure Multisynth divider for given output.

        Args:
            output (int): Clock output number.
            div (int): Integer divider [4-2047].
            num (int): Fractional numerator [0-1048574].
            denom (int): Fractional denominator [1-1048575].
            rdiv (int): Additional divide-by-2^rdiv.

        Raises:
            ValueError: If div is invalid.div (int): Integer divider [4-2047].

        Notes:
            Synchronizes phase and resets PLL to align outputs.
        """

        if type(div) is not int or div < 4:
            raise ValueError('bad multisynth divisor：div (int): Integer divider [4-2047].')
        if output == 0: reg = self.SI5351_REGISTER_MULTISYNTH0_PARAMETERS_1
        if output == 1: reg = self.SI5351_REGISTER_MULTISYNTH1_PARAMETERS_1
        if output == 2: reg = self.SI5351_REGISTER_MULTISYNTH2_PARAMETERS_1
        self.write_config(reg, whole=div, num=num, denom=denom, rdiv=rdiv)
        if self.div[output] != div:
            pll = self.pll[output]
            self.set_phase(output, div if self.quadrature[output] else 0)
            self.reset_pll(pll)  # only after MS setup, syncs all clocks of pll
            integer_mode = (num == 0)
            self.init_multisynth(output, integer_mode=integer_mode)
            self.div[output] = div

    def set_freq_fixedpll(self, output, freq):
        """
        设置固定 PLL 下的输出频率。

        Args:
            output (int): 输出通道编号。
            freq (float): 目标频率 (Hz)。

        Raises:
            ValueError: 当分频因子超出范围时。

        Notes:
            需先调用 init_clock() 与 setup_pll()。
        ==========================================
        Set output frequency using fixed PLL.

        Args:
            output (int): Clock output number.
            freq (float): Target frequency in Hz.

        Raises:
            ValueError: If divisor is out of range.

        Notes:
            Requires prior calls to init_clock() and setup_pll().
        """

        pll = self.pll[output]
        vco = self.vco[pll]

        # determine rdiv
        for rdiv in range(self.SI5351_MULTISYNTH_RX_MAX + 1):
            if freq * self.SI5351_MULTISYNTH_DIV_MAX > vco: break
            freq *= 2
        else:
            raise ValueError('maximum Rx divisor exceeded')

        # determine divisor: div + num / denom
        vco = int(10 * vco)
        denom = int(10 * freq)
        num = vco % denom
        div = vco // denom  # div = 4,6,[8+0/1048575 to 2047]
        if (div < self.SI5351_MULTISYNTH_DIV_MIN or
                div >= self.SI5351_MULTISYNTH_DIV_MAX):
            raise ValueError('multisynth divisor out of range')
        max_denom = self.SI5351_MULTISYNTH_C_MAX
        num, denom = self.approximate_fraction(num, denom, max_denom=max_denom)
        self.setup_multisynth(output, div=div, num=num, denom=denom, rdiv=rdiv)

    def set_freq_fixedms(self, output, freq):
        """
        设置固定 Multisynth 下的输出频率。

        Args:
            output (int): 输出通道编号，通常 0..2。
            freq (float): 目标频率 (Hz)，必须为正数。

        Raises:
            TypeError: 参数类型错误。
            ValueError: output 不在允许范围，freq <= 0，或 PLL 倍频因子超出范围。

        Notes:
            需先调用 init_clock() 与 setup_multisynth()。

        ==========================================
        Set output frequency by adjusting PLL multiplier with fixed Multisynth.

        Args:
            output (int): Clock output number, usually 0..2.
            freq (float): Target frequency in Hz, must be positive.

        Raises:
            TypeError: If argument types are incorrect.
            ValueError: If output is out of range, freq <= 0, or PLL multiplier out of range.

        Notes:
            Requires prior calls to init_clock() and setup_multisynth().
        """
        if not isinstance(output, int):
            raise TypeError("output must be an int")
        if not isinstance(freq, (int, float)):
            raise TypeError("freq must be int or float")

        # 值检查
        if not 0 <= output <= 2:
            raise ValueError("output must be in range 0..2")
        if freq <= 0:
            raise ValueError("freq must be positive")
        pll = self.pll[output]
        crystal = self.crystal
        vco = freq * div * 2 ** rdiv

        # determine multiplicand: mul + num / denom
        vco = int(10 * vco)
        denom = int(10 * crystal)
        num = vco % denom
        mul = vco // denom  # mul = 15+0/1048575 to 90
        if (mul < self.SI5351_MULTISYNTH_MUL_MIN or
                mul >= self.SI5351_MULTISYNTH_MUL_MAX):
            raise ValueError('pll multiplier out of range')
        max_denom = self.SI5351_MULTISYNTH_C_MAX
        num, denom = self.approximate_fraction(num, denom, max_denom=max_denom)
        self.setup_pll(pll, mul=mul, num=num, denom=denom)

    ###

    def disabled_states(self, output, state):
        """
        设置指定输出在禁用时的状态。

        Args:
            output (int): 输出通道编号，通常 0..7。
            state (int): 禁用状态，0=低电平, 1=高电平, 2=高阻, 3=永不禁用。

        Raises:
            TypeError: 参数类型错误。
            ValueError: output 或 state 不在允许范围。

        ==========================================
        Configure disabled state for an output.

        Args:
            output (int): Clock output number, usually 0..7.
            state (int): Disabled state: 0=low, 1=high, 2=high-Z, 3=never disabled.

        Raises:
            TypeError: If argument types are incorrect.
            ValueError: If output or state is out of allowed range.
        """
        # 类型检查
        if not isinstance(output, int):
            raise TypeError("output must be an int")
        if not isinstance(state, int):
            raise TypeError("state must be an int")

        # 值检查
        if not 0 <= output <= 7:
            raise ValueError("output must be in range 0..7")
        if not 0 <= state <= 3:
            raise ValueError("state must be 0..3")
        if output < 4:
            reg = self.SI5351_REGISTER_DIS_STATE_1
        else:
            reg = self.SI5351_REGISTER_DIS_STATE_2
            output -= 4
        value = self._read(reg)
        s = [(value >> (n * 2)) & 0x3 for n in range(4)]
        s[output] = state
        self._write(reg, s[3] << 6 | s[2] << 4 | s[1] << 2 | s[0])

    def disable_oeb(self, mask):
        """
        禁用指定通道的 OEB 引脚功能。

        Args:
            mask (int): 通道掩码，每一位对应一个 clkout (0..7)。

        Raises:
            TypeError: 参数类型错误。
            ValueError: mask 不在 0..0xFF 范围。
            
        ==========================================
        Disable OEB pin support for given outputs.

        Args:
            mask (int): Bitmask of clock outputs to disable OEB (0..0xFF).

        Raises:
            TypeError: If mask is not an int.
            ValueError: If mask is out of range 0..0xFF.
        """

        # 类型检查
        if not isinstance(mask, int):
            raise TypeError("mask must be an int")

        # 值检查
        if not 0 <= mask <= 0xFF:
            raise ValueError("mask must be in range 0..0xFF")

        self._write(self.SI5351_REGISTER_OEB_ENABLE_CONTROL, mask & 0xFF)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================