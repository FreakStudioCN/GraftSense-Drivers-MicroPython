# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:21
# @Author  : 侯钧瀚
# @File    : led_bar.py
# @Description : 基于SI5351芯片的时钟信号发生模块驱动
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0
# @参考代码 ：https://github.com/roseengineering/silicon5351
__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"
# ======================================== 导入相关模块 =========================================

from micropython import const

# ======================================== 全局变量 ============================================


SI5351_I2C_ADDRESS_DEFAULT      = const(0x60)

SI5351_CRYSTAL_LOAD_6PF         = const(1)
SI5351_CRYSTAL_LOAD_8PF         = const(2)
SI5351_CRYSTAL_LOAD_10PF        = const(3)

SI5351_CLK_DRIVE_STRENGTH_2MA   = const(0)
SI5351_CLK_DRIVE_STRENGTH_4MA   = const(1)
SI5351_CLK_DRIVE_STRENGTH_6MA   = const(2)
SI5351_CLK_DRIVE_STRENGTH_8MA   = const(3)

SI5351_DIS_STATE_LOW            = const(0)
SI5351_DIS_STATE_HIGH           = const(1)
SI5351_DIS_STATE_HIGH_IMPEDANCE = const(2)
SI5351_DIS_STATE_NEVER_DISABLED = const(3)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class SI5351_I2C:
    """
    SI5351 驱动类，用于通过 I2C 接口控制 SI5351 时钟发生器（MicroPython / Raspberry Pi Pico）。
    提供 PLL/Multisynth 参数配置、相位设置、输出使能/禁用等能力，覆盖常用的 CLK0/CLK1/CLK2 工作流程，适用于本振合成、时钟分配与频率合成场景。

    Attributes:
    i2c (I2C): MicroPython 的 machine.I2C 实例，用于与 SI5351 通信。
    crystal (int): 外部晶振频率，单位 Hz。
    address (int): I2C 地址（默认 0x60）。
    vco (dict): 各 PLL 的 VCO 频率缓存，键为 0/1，值单位 Hz。
    pll (dict): 各输出口所选的 PLL（0=PLLA，1=PLLB）。
    quadrature (dict): 各输出是否启用正交相位逻辑（库内相位处理用）。
    invert (dict): 各输出是否反相。
    drive_strength (dict): 各输出的驱动电流强度（2/4/6/8 mA）。
    div (dict): 各输出当前的 Multisynth 整数分频。
    rdiv (dict): 各输出当前的 Rx 分频幂（0..7，表示 2^rdiv）。

    Methods:
    init(i2c, crystal: int, load: int = SI5351_CRYSTAL_LOAD_10PF, address: int = 0x60) -> None:
    初始化驱动并完成上电后的基础寄存器配置（禁用输出、关闭驱动器、设置晶振负载）。
    init_clock(output: int, pll: int, quadrature: bool = False, invert: bool = False,
    drive_strength: int = SI5351_CLK_DRIVE_STRENGTH_8MA) -> None:
    初始化指定输出口的库内状态（不立即访问硬件）。
    setup_pll(pll: int, mul: int, num: int = 0, denom: int = 1) -> None:
    配置 PLL 频率为 crystal × (mul + num/denom)。
    setup_multisynth(output: int, div: int, num: int = 0, denom: int = 1, rdiv: int = 0) -> None:
    配置 Multisynth 分频与 Rx（2^rdiv）；若分频改变则进行相位设置与 PLL 同步。
    set_freq_fixedpll(output: int, freq_hz: int|float) -> None:
    在 PLL 固定的前提下，计算 Multisynth/Rx 以得到目标输出频率。
    set_freq_fixedms(output: int, freq_hz: int|float) -> None:
    在 Multisynth/Rx 固定的前提下，调整 PLL 倍频以得到目标输出频率。
    enable_output(output: int) -> None:
    使能指定输出口。
    disable_output(output: int) -> None:
    禁用指定输出口。
    disabled_states(output: int, state: int) -> None:
    设置输出在被禁用（软件或 OEB 引脚）时的电气状态（低/高/高阻/永不禁用）。
    disable_oeb(mask: int) -> None:
    屏蔽 OEB 引脚对指定输出通道的影响（按位掩码）。
    reset_pll(pll: int) -> None:
    复位并同步指定 PLL。
    set_phase(output: int, div: int) -> None:
    设置输出相位（以分频刻度，取低 8 位）。
    read_bulk(register: int, nbytes: int) -> bytearray:
    从指定寄存器开始读取连续字节。
    write_bulk(register: int, values: bytes|bytearray|list) -> None:
    向指定寄存器开始写入连续字节。
    read(register: int) -> int:
    读取单字节寄存器。
    write(register: int, value: int) -> None:
    写入单字节寄存器。
    write_config(reg: int, whole: int, num: int, denom: int, rdiv: int) -> None:
    打包并写入 Multisynth/PLL 参数字段。
    approximate_fraction(n: int, d: int, max_denom: int) -> tuple[int, int]:
    在分母上限内逼近分数，用于受硬件字段精度限制的近似。

    Notes:
    - 线程/ISR 限制：凡涉及 I2C 访问的方法 ISR-safe: no；如需在中断中触发，请使用 micropython.schedule 将操作延迟到主循环。
    - 资源需求：占用 1 路 I2C（SCL/SDA，3.3V 电平）；运行期使用少量字典缓存与临时缓冲（RAM 占用数 KB 量级，随实现而异）。
    - 兼容性/测试板信息：建议 MicroPython v1.19+；已在 Raspberry Pi Pico（RP2040）测试；其他主控需确保 3.3V I2C 与外部晶振参数匹配。
    - 功能覆盖：示例实现聚焦 CLK0/CLK1/CLK2 常用配置路径；更多输出/特性请按数据手册扩展。

    ==========================================

    SI5351 I2C driver for MicroPython (Raspberry Pi Pico / RP2040).
    Provides PLL/Multisynth configuration, phase control, and per-output enable/disable, focusing on common workflows for CLK0/CLK1/CLK2.

    Attributes:
    i2c (I2C): MicroPython machine.I2C instance for communication.
    crystal (int): External crystal frequency in Hz.
    address (int): I2C address (default 0x60).
    vco (dict): Cached VCO frequency per PLL (key 0/1), in Hz.
    pll (dict): Selected PLL per output (0=PLLA, 1=PLLB).
    quadrature (dict): Whether quadrature logic is enabled per output.
    invert (dict): Whether the output is inverted.
    drive_strength (dict): Output drive strength (2/4/6/8 mA).
    div (dict): Integer Multisynth divider per output.
    rdiv (dict): Rx divider power per output (0..7 meaning 2^rdiv).

    Methods:
    init(i2c, crystal: int, load: int = SI5351_CRYSTAL_LOAD_10PF, address: int = 0x60) -> None:
    Initialize the driver and perform basic power-up configuration (disable outputs, power down drivers, set crystal load).
    init_clock(output: int, pll: int, quadrature: bool = False, invert: bool = False,
    drive_strength: int = SI5351_CLK_DRIVE_STRENGTH_8MA) -> None:
    Prepare per-output library state (no immediate HW I/O).
    setup_pll(pll: int, mul: int, num: int = 0, denom: int = 1) -> None:
    Set PLL to crystal × (mul + num/denom).
    setup_multisynth(output: int, div: int, num: int = 0, denom: int = 1, rdiv: int = 0) -> None:
    Configure Multisynth and Rx (2^rdiv); when divider changes, set phase and reset PLL for sync.
    set_freq_fixedpll(output: int, freq_hz: int|float) -> None:
    With PLL fixed, compute MS/Rx to reach target frequency.
    set_freq_fixedms(output: int, freq_hz: int|float) -> None:
    With MS/Rx fixed, adjust PLL multiplier to reach target frequency.
    enable_output(output: int) -> None:
    Enable an output.
    disable_output(output: int) -> None:
    Disable an output.
    disabled_states(output: int, state: int) -> None:
    Configure disabled electrical state (low/high/Hi-Z/never).
    disable_oeb(mask: int) -> None:
    Disable OEB-pin response for selected outputs (bitmask).
    reset_pll(pll: int) -> None:
    Reset/synchronize a PLL.
    set_phase(output: int, div: int) -> None:
    Set output phase in divider-scale (LSB 8 bits).
    read_bulk(register: int, nbytes: int) -> bytearray:
    Read a consecutive register block.
    write_bulk(register: int, values: bytes|bytearray|list) -> None:
    Write a consecutive register block.
    read(register: int) -> int:
    Read one register byte.
    write(register: int, value: int) -> None:
    Write one register byte.
    write_config(reg: int, whole: int, num: int, denom: int, rdiv: int) -> None:
    Pack and write Multisynth/PLL parameter fields.
    approximate_fraction(n: int, d: int, max_denom: int) -> tuple[int, int]:
    Approximate a fraction under a denominator cap.

    Notes:
    - Thread/ISR: Any I2C-touching method is ISR-safe: no; use micropython.schedule to defer from ISRs.
    - Resources: Requires one I2C bus (SCL/SDA, 3.3V). Uses small dict caches and temporary buffers (RAM usage within a few KB, implementation-dependent).
    - Compatibility / Boards: MicroPython v1.19+; tested on Raspberry Pi Pico (RP2040). Other boards must ensure 3.3V I2C and matching external crystal spec.
    - Coverage: Example focuses on common register recipes for CLK0/1/2; extend per datasheet for additional outputs/features.
    """


    SI5351_MULTISYNTH_RX_MAX = const(7)
    SI5351_MULTISYNTH_C_MAX = const(1048575)

    SI5351_MULTISYNTH_DIV_MIN = const(8)
    SI5351_MULTISYNTH_DIV_MAX = const(2048)

    SI5351_MULTISYNTH_MUL_MIN = const(15)
    SI5351_MULTISYNTH_MUL_MAX = const(90)

    SI5351_PLL_RESET_A = const(1 << 5)
    SI5351_PLL_RESET_B = const(1 << 7)

    SI5351_CLK_POWERDOWN = const(1 << 7)
    SI5351_CLK_INPUT_MULTISYNTH_N = const(3 << 2)
    SI5351_CLK_INTEGER_MODE = const(1 << 6)
    SI5351_CLK_PLL_SELECT_A = const(0 << 5)
    SI5351_CLK_PLL_SELECT_B = const(1 << 5)
    SI5351_CLK_INVERT = const(1 << 4)

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

    def __init__(self, i2c, crystal, load=SI5351_CRYSTAL_LOAD_10PF,
                 address=SI5351_I2C_ADDRESS_DEFAULT):
        """
        构造驱动实例并完成芯片上电后的基础初始化：禁用全部输出、关闭驱动器、设置晶振负载电容。

        Args:
            i2c (I2C): machine.I2C 实例。
            crystal (int): 晶振频率，单位 Hz。
            load (int): 晶振负载（6/8/10 pF，对应常量）。
            address (int): I2C 地址。

        Raises:
            RuntimeError: I2C 通信失败。
            ValueError: 参数取值非法（晶振负载范围（6/8/10 pF）。

        Notes：
            - 副作用：写入多个寄存器；更新 self.i2c / self.crystal / self.address 等成员。
            - ISR-safe: no（涉及 I2C）。
        =========================================
        Initialize the driver instance and perform basic chip init: disable all outputs,
        power down drivers, set crystal load.

        Args:
            i2c (I2C): machine.I2C instance.
            crystal (int): Crystal frequency in Hz.
            load (int): Crystal load (6/8/10 pF via constants).
            address (int): I2C address.

        Raises:
            RuntimeError: On I2C errors.
            ValueError: Invalid parameter value (crystal oscillator load range (6/8/10 pF)).

        Notes：
            - Side effects: writes multiple registers; updates instance members.
            - ISR-safe: no (I2C involved).
        """
        self.i2c = i2c
        self.crystal = crystal
        self.address = address
        self.vco = {}
        self.pll = {}
        self.quadrature = {}
        self.invert = {}
        self.drive_strength = {}
        self.div = {}
        self.rdiv = {}

        # wait until chip initializes before writing registers
        while self.read(self.SI5351_REGISTER_DEVICE_STATUS) & 0x80:
            pass
        # disable outputs
        self.write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, 0xFF)
        # power down all 8 output drivers
        values = [self.SI5351_CLK_POWERDOWN] * 8
        self.write_bulk(self.SI5351_REGISTER_CLK0_CONTROL, values)
        # set crystal load value (bits [7:6])
        self.write(self.SI5351_REGISTER_CRYSTAL_LOAD, (load & 0x3) << 6)

    def read_bulk(self, register, nbytes):
        """
        从指定寄存器开始读取连续字节。

        Args:
            register (int): 起始寄存器地址。
            nbytes (int): 读取字节数。

        Returns:
            bytearray: 读取到的数据。

        Raises:
            RuntimeError: I2C 读取失败。

        Notes：
            - 副作用：与外设进行 I2C 通信。
            - ISR-safe: no（I2C + 内存分配）。
        =========================================
        Read a consecutive block starting at the given register.

        Args:
            register (int): Start register address.
            nbytes (int): Number of bytes to read.

        Returns:
            bytearray: Read data.

        Raises:
            RuntimeError: If I2C read fails.

        Notes：
            - Side effects: Performs I2C transaction.
            - ISR-safe: no (I2C + allocation).
        """
        buf = bytearray(nbytes)
        try:
            self.i2c.readfrom_mem_into(self.address, register, buf)
        except OSError as e:
            raise RuntimeError("I2C read error") from e
        return buf

    def write_bulk(self, register, values):
        """
        向指定寄存器开始写入连续字节。

        Args:
            register (int): 起始寄存器地址。
            values (list|bytes|bytearray): 待写入的字节序列。

        Raises:
            RuntimeError: I2C 写入失败。

        Notes：
            - 副作用：与外设进行 I2C 通信。
            - ISR-safe: no（I2C）。
        =========================================
        Write a consecutive byte sequence starting at the given register.

        Args:
            register (int): Start register address.
            values (list|bytes|bytearray): Bytes to write.

        Raises:
            RuntimeError: If I2C write fails.

        Notes：
            - Side effects: Performs I2C transaction.
            - ISR-safe: no (I2C).
        """
        try:
            self.i2c.writeto_mem(self.address, register, bytes(values))
        except OSError as e:
            raise RuntimeError("I2C write error") from e

    def read(self, register):
        """
        读取单个寄存器字节。

        Args:
            register (int): 寄存器地址。

        Returns:
            int: 读出的 0..255 字节值。

        Raises:
            RuntimeError: I2C 读取失败。

        Notes：
            - 副作用：I2C 通信一次。
            - ISR-safe: no。
        =========================================
        Read one byte from a register.

        Args:
            register (int): Register address.

        Returns:
            int: Byte value 0..255.

        Raises:
            RuntimeError: On I2C error.

        Notes：
            - Side effects: One I2C transaction.
            - ISR-safe: no.
        """
        return self.read_bulk(register, 1)[0]

    def write(self, register, value):
        """
        写入单个寄存器字节。

        Args:
            register (int): 寄存器地址。
            value (int): 写入值 0..255。

        Raises:
            RuntimeError: I2C 写入失败。

        Notes：
            - 副作用：I2C 通信一次。
            - ISR-safe: no。
        =========================================
        Write one byte to a register.

        Args:
            register (int): Register address.
            value (int): Byte value 0..255.


        Raises:
            RuntimeError: On I2C error.

        Notes：
            - Side effects: One I2C transaction.
            - ISR-safe: no.
        """
        self.write_bulk(register, [value])

    # ------------------------------- Low-level config packer -------------------------------
    def write_config(self, reg, whole, num, denom, rdiv):
        """
        将 (whole + num/denom, rdiv) 打包为芯片寄存器字段并一次性写入。

        Args:
            reg (int): 目标参数组首寄存器地址。
            whole (int): 整数部分。
            num (int): 分子部分。
            denom (int): 分母部分（>0）。
            rdiv (int): Rx 分频，0..7（表示 2^rdiv）。

        Raises:
            RuntimeError: I2C 写入失败。
            ValueError: 参数越界或 denom<=0。

        Notes：
            - 副作用：写寄存器，更新硬件状态。
            - ISR-safe: no（I2C）。
        =========================================
        Pack (whole + num/denom, rdiv) into register fields and write.

        Args:
            reg (int): Base register address of the parameter group.
            whole (int): Integer part.
            num (int): Numerator.
            denom (int): Denominator (>0).
            rdiv (int): Rx divider 0..7 (actual 2^rdiv).

        Raises:
            RuntimeError: On I2C write failure.
            ValueError: If arguments out of range or denom<=0.

        Notes：
            - Side effects: Writes registers, changes hardware state.
            - ISR-safe: no (I2C).
        """
        if denom <= 0:
            raise ValueError("denom must be > 0")
        P1 = 128 * whole + int(128.0 * num / denom) - 512
        P2 = 128 * num - denom * int(128.0 * num / denom)
        P3 = denom
        self.write_bulk(reg, [
            (P3 & 0x0FF00) >> 8,
            (P3 & 0x000FF),
            ((P1 & 0x30000) >> 16) | ((rdiv & 0x7) << 4),
            (P1 & 0x0FF00) >> 8,
            (P1 & 0x000FF),
            ((P3 & 0xF0000) >> 12) | ((P2 & 0xF0000) >> 16),
            (P2 & 0x0FF00) >> 8,
            (P2 & 0x000FF)
        ])

    def set_phase(self, output, div):
        """
        设置输出口的相位偏移（以分频数为基准的低 8 位）。

        Args:
            output (int): 输出口编号（0/1/2）。
            div (int): 相位步进（通常与整数分频相同），仅低 8 位有效。

        Raises:
            RuntimeError: I2C 写入失败。
            ValueError: output 越界。

        Notes：
            - 副作用：写相位寄存器；改变对应输出相位。
            - ISR-safe: no。
        =========================================
        Set phase offset for an output (LSB 8 bits of divider-scale).

        Args:
            output (int): Output index (0/1/2).
            div (int): Phase steps (often equals integer divider), LSB 8 bits used.

        Raises:
            RuntimeError: On I2C write failure.
            ValueError: If output out of range.

        Notes：
            - Side effects: Writes phase register; changes output phase.
            - ISR-safe: no.
        """
        if output not in (0, 1, 2):
            raise ValueError("output must be 0/1/2")
        self.write(self.SI5351_REGISTER_CLK0_PHOFF + output, int(div) & 0xFF)

    def reset_pll(self, pll):
        """
        复位指定 PLL（同步其下属输出）。

        Args:
            pll (int): PLL 编号（0=PLLA，1=PLLB）。

        Raises:
            RuntimeError: I2C 写入失败。
            ValueError: pll 非 0/1。

        Notes：
            - 副作用：写复位寄存器；可能导致相关输出瞬时相位对齐。
            - ISR-safe: no。
        =========================================
        Reset a specific PLL (synchronizes its outputs).

        Args:
            pll (int): PLL id (0=PLLA, 1=PLLB).

        Raises:
            RuntimeError: On I2C write failure.
            ValueError: If pll not 0/1.

        Notes：
            - Side effects: Writes reset register; may align phases.
            - ISR-safe: no.
        """
        if pll == 0:
            value = self.SI5351_PLL_RESET_A
        elif pll == 1:
            value = self.SI5351_PLL_RESET_B
        else:
            raise ValueError("pll must be 0 or 1")
        self.write(self.SI5351_REGISTER_PLL_RESET, value)

    def init_multisynth(self, output, integer_mode):
        """
        初始化 Multisynth 输出控制字（选择输入源/整数模式/反相/PLL）。

        Args:
            output (int): 输出口编号（0/1/2）。
            integer_mode (bool): 是否整数模式（num==0 时建议 True）。

        Raises:
            RuntimeError: I2C 写入失败。
            ValueError: 参数越界或未调用 init_clock() 设置状态。

        Notes：
            - 副作用：写 CLKx_CONTROL；使用 self.pll/self.invert/self.quadrature/self.drive_strength。
            - ISR-safe: no。
        =========================================
        Initialize Multisynth control word for an output.

        Args:
            output (int): Output index (0/1/2).
            integer_mode (bool): Enable integer mode (recommended when num==0).

        Raises:
            RuntimeError: On I2C write failure.
            ValueError: If out of range or state not prepared via init_clock().

        Notes：
            - Side effects: Writes CLKx_CONTROL; reads self.pll/invert/quadrature/drive_strength.
            - ISR-safe: no.
        """
        if output not in (0, 1, 2):
            raise ValueError("output must be 0/1/2")
        pll = self.pll[output]
        value = self.SI5351_CLK_INPUT_MULTISYNTH_N
        value |= self.drive_strength[output]
        if integer_mode:
            value |= self.SI5351_CLK_INTEGER_MODE
        if self.invert[output] or self.quadrature[output]:
            value |= self.SI5351_CLK_INVERT
        if pll == 0:
            value |= self.SI5351_CLK_PLL_SELECT_A
        elif pll == 1:
            value |= self.SI5351_CLK_PLL_SELECT_B
        else:
            raise ValueError("pll must be 0 or 1")
        self.write(self.SI5351_REGISTER_CLK0_CONTROL + output, value)

    def approximate_fraction(self, n, d, max_denom):
        """
        逼近分数 n/d，使分母不超过 max_denom；用于硬件字段精度限制下的最佳近似。

        Args:
            n (int): 分子。
            d (int): 分母（>0）。
            max_denom (int): 分母上限。

        Returns:
            tuple: (num:int, denom:int) 近似后的分子与分母。

        Raises:
            ValueError: d<=0 或 max_denom<1。

        Notes：
            - 副作用：无。
            - ISR-safe: no（涉及新对象分配，不建议在 ISR 调用）。
        =========================================
        Approximate fraction n/d under a maximum denominator.

        Args:
            n (int): Numerator.
            d (int): Denominator (>0).
            max_denom (int): Maximum allowed denominator.

        Returns:
            tuple: (num:int, denom:int) approximated fraction.

        Raises:
            ValueError: If d<=0 or max_denom<1.

        Notes：
            - Side effects: None.
            - ISR-safe: no (allocations involved).
        """
        if d <= 0 or max_denom < 1:
            raise ValueError("invalid denominator/max_denom")
        denom = d
        if denom > max_denom:
            num = n
            p0 = 0; q0 = 1; p1 = 1; q1 = 0
            while denom != 0:
                a = num // denom
                b = num % denom
                q2 = q0 + a * q1
                if q2 > max_denom:
                    break
                p2 = p0 + a * p1
                p0 = p1; q0 = q1; p1 = p2; q1 = q2
                num = denom; denom = b
            n = p1; d = q1
        return n, d

    def init_clock(self, output, pll, quadrature=False, invert=False,
                   drive_strength=SI5351_CLK_DRIVE_STRENGTH_8MA):
        """
        初始化输出口的库内状态（不立即写芯片）：选择 PLL、是否反相/正交、驱动强度等。

        Args:
            output (int): 输出口编号（0/1/2）。
            pll (int): 选择的 PLL（0/1）。
            quadrature (bool): 是否开启正交相位逻辑。
            invert (bool): 是否反相输出。
            drive_strength (int): 驱动强度常量（2/4/6/8 mA）。

        Raises:
            ValueError: 参数越界。

        Notes：
            - 副作用：更新内部缓存 self.pll/self.quadrature/self.invert/self.drive_strength/self.div/self.rdiv。
            - ISR-safe: yes（无 I2C；但有字典写入与分配，不建议在严格 ISR 场景使用）。
        =========================================
        Initialize library state for an output (no chip I/O yet).

        Args:
            output (int): Output index (0/1/2).
            pll (int): Selected PLL (0/1).
            quadrature (bool): Enable quadrature logic or not.
            invert (bool): Invert output or not.
            drive_strength (int): Drive strength constant (2/4/6/8 mA).

        Raises:
            ValueError: If arguments out of range.

        Notes：
            - Side effects: Updates internal caches (pll/quadrature/invert/drive_strength/div/rdiv).
            - ISR-safe: yes (no I2C; but allocations make ISR usage discouraged).
        """
        if output not in (0, 1, 2):
            raise ValueError("output must be 0/1/2")
        if pll not in (0, 1):
            raise ValueError("pll must be 0 or 1")
        self.pll[output] = pll
        self.quadrature[output] = quadrature
        self.invert[output] = invert
        self.drive_strength[output] = drive_strength
        self.div[output] = None
        self.rdiv[output] = 0

    def enable_output(self, output):
        """
        使能指定输出口。

        Args:
            output (int): 输出口编号（0..7；本驱动主要用于 0/1/2）。

        Raises:
            RuntimeError: I2C 访问失败。

        Notes：
            - 副作用：修改输出使能寄存器位。
            - ISR-safe: no。
        =========================================
        Enable a specific output.

        Args:
            output (int): Output index (0..7; mainly 0/1/2 here).

        Raises:
            RuntimeError: On I2C error.

        Notes：
            - Side effects: Modifies output enable register bits.
            - ISR-safe: no.
        """
        mask = self.read(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL)
        self.write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, mask & ~(1 << output))

    def disable_output(self, output):
        """
        禁用指定输出口。

        Args:
            output (int): 输出口编号（0..7）。

        Raises:
            RuntimeError: I2C 访问失败。

        Notes：
            - 副作用：修改输出使能寄存器位。
            - ISR-safe: no。
        =========================================
        Disable a specific output.

        Args:
            output (int): Output index (0..7).

        Raises:
            RuntimeError: On I2C error.

        Notes：
            - Side effects: Modifies output enable register bits.
            - ISR-safe: no.
        """
        mask = self.read(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL)
        self.write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, mask | (1 << output))

    def setup_pll(self, pll, mul, num=0, denom=1):
        """
        设置 PLL 频率为 crystal * (mul + num/denom)。

        Args:
            pll (int): PLL 编号（0/1）。
            mul (int): 整数倍（15..90）。
            num (int): 分子（0..1048574）。
            denom (int): 分母（1..1048575）。

        Raises:
            RuntimeError: I2C 写入失败。
            ValueError: 取值越界或 pll 非 0/1。

        Notes：
            - 副作用：写 PLL 参数寄存器；更新 self.vco[pll]。
            - ISR-safe: no。
        =========================================
        Configure PLL frequency to crystal * (mul + num/denom).

        Args:
            pll (int): PLL id (0/1).
            mul (int): Integer multiplier (15..90).
            num (int): Numerator (0..1048574).
            denom (int): Denominator (1..1048575).

        Raises:
            RuntimeError: On I2C write failure.
            ValueError: If out of range or pll not 0/1.

        Notes：
            - Side effects: Writes PLL registers; updates self.vco[pll].
            - ISR-safe: no.
        """
        if pll == 0:
            reg = self.SI5351_REGISTER_PLL_A
        elif pll == 1:
            reg = self.SI5351_REGISTER_PLL_B
        else:
            raise ValueError("pll must be 0 or 1")
        if not (self.SI5351_MULTISYNTH_MUL_MIN <= mul < self.SI5351_MULTISYNTH_MUL_MAX):
            raise ValueError("mul out of range")
        self.write_config(reg, whole=mul, num=num, denom=denom, rdiv=0)
        self.vco[pll] = self.crystal * (mul + num / denom)

    def setup_multisynth(self, output, div, num=0, denom=1, rdiv=0):
        """
        设置 Multisynth 分频（div + num/denom）与 Rx 分频（2^rdiv），并在分频变化时执行相位设置与 PLL 同步。

        Args:
            output (int): 输出口（0/1/2）。
            div (int): 整数分频（>=4；本库限制最终范围 [8..2047)）。
            num (int): 分子（0..1048574）。
            denom (int): 分母（1..1048575）。
            rdiv (int): Rx 分频幂，0..7 表示 2^rdiv。

        Raises:
            RuntimeError: I2C 写入失败。
            ValueError: 参数越界或不支持的输出口（0/1/2）。

        Notes：
            - 副作用：写 MS 寄存器；必要时 set_phase() 与 reset_pll()；更新 self.div/self.rdiv。
            - ISR-safe: no。
        =========================================
        Configure Multisynth divider (div + num/denom) and Rx (2^rdiv). If divider changes,
        perform phase setup and PLL reset to sync.

        Args:
            output (int): Output index (0/1/2).
            div (int): Integer divider (>=4; library limits final range [8..2047)).
            num (int): Numerator (0..1048574).
            denom (int): Denominator (1..1048575).
            rdiv (int): Rx divider power 0..7 (actual 2^rdiv).

        Raises:
            RuntimeError: On I2C write failure.
            ValueError: If arguments out of range or unsupported output.

        Notes：
            - Side effects: Writes MS regs; may call set_phase()/reset_pll(); updates self.div/self.rdiv.
            - ISR-safe: no.
        """
        if not isinstance(div, int) or div < 4:
            raise ValueError('bad multisynth divisor')
        if rdiv < 0 or rdiv > self.SI5351_MULTISYNTH_RX_MAX:
            raise ValueError('bad rdiv (0..7)')
        if output == 0:
            reg = self.SI5351_REGISTER_MULTISYNTH0_PARAMETERS_1
        elif output == 1:
            reg = self.SI5351_REGISTER_MULTISYNTH1_PARAMETERS_1
        elif output == 2:
            reg = self.SI5351_REGISTER_MULTISYNTH2_PARAMETERS_1
        else:
            raise ValueError('only CLK0/1/2 supported by this driver')

        self.write_config(reg, whole=div, num=num, denom=denom, rdiv=rdiv)
        prev_div = self.div.get(output, None)
        if prev_div != div:
            pll = self.pll[output]
            self.set_phase(output, div if self.quadrature[output] else 0)
            self.reset_pll(pll)
            integer_mode = (num == 0)
            self.init_multisynth(output, integer_mode=integer_mode)

        self.div[output] = div
        self.rdiv[output] = rdiv

    def set_freq_fixedpll(self, output, freq_hz):
        """
        在 PLL 频率已定的前提下，通过计算 Multisynth（含 Rx）实现给定输出频率。

        Args:
            output (int): 输出口（0/1/2）。
            freq_hz (int|float): 目标输出频率，单位 Hz。

        Raises:
            ValueError: 频率不可达或分频超界。
            RuntimeError: I2C 写入失败。

        Notes：
            - 前置条件：必须先调用 init_clock() 和 setup_pll()。
            - 副作用：调用 setup_multisynth() 并写寄存器；更新 self.div/self.rdiv。
            - ISR-safe: no。
        =========================================
        Given a fixed PLL frequency, compute Multisynth (with Rx) for the target output frequency.

        Args:
            output (int): Output index (0/1/2).
            freq_hz (int|float): Target frequency in Hz.

        Raises:
            ValueError: If frequency unreachable or divider out of range.
            RuntimeError: On I2C failure.

        Notes：
            - Precondition: init_clock() and setup_pll() must have been called.
            - Side effects: Calls setup_multisynth() and writes regs; updates self.div/self.rdiv.
            - ISR-safe: no.
        """
        pll = self.pll[output]
        vco = self.vco[pll]

        # determine rdiv
        rdiv = 0
        freq = float(freq_hz)
        while rdiv <= self.SI5351_MULTISYNTH_RX_MAX:
            if freq * self.SI5351_MULTISYNTH_DIV_MAX > vco:
                break
            freq *= 2.0
            rdiv += 1
        if rdiv > self.SI5351_MULTISYNTH_RX_MAX:
            raise ValueError('maximum Rx divisor exceeded')

        # determine divisor: div + num / denom
        vco10 = int(10 * vco)
        denom = int(10 * freq)
        num = vco10 % denom
        div = vco10 // denom
        if (div < self.SI5351_MULTISYNTH_DIV_MIN or
                div >= self.SI5351_MULTISYNTH_DIV_MAX):
            raise ValueError('multisynth divisor out of range')
        max_denom = self.SI5351_MULTISYNTH_C_MAX
        num, denom = self.approximate_fraction(num, denom, max_denom=max_denom)
        self.setup_multisynth(output, div=div, num=num, denom=denom, rdiv=rdiv)

    def set_freq_fixedms(self, output, freq_hz):
        """
        在 Multisynth（div/num/denom）与 Rx 固定的前提下，通过调整 PLL 倍频实现目标频率。

        Args:
            output (int): 输出口（0/1/2）。
            freq_hz (int|float): 目标输出频率，单位 Hz。

        Raises:
            ValueError: 未初始化 Multisynth/Rx 或 PLL 倍频越界。
            RuntimeError: I2C 写入失败。

        Notes：
            - 前置条件：需先 setup_multisynth() 固定分频、再调用本函数。
            - 副作用：调用 setup_pll() 并写寄存器；更新 self.vco。
            - ISR-safe: no。
        =========================================
        With fixed Multisynth (div/num/denom) and Rx, adjust PLL multiplier to hit the target frequency.

        Args:
            output (int): Output index (0/1/2).
            freq_hz (int|float): Target frequency in Hz.

        Raises:
            ValueError: If Multisynth/Rx not initialized or PLL multiplier out of range.
            RuntimeError: On I2C failure.

        Notes：
            - Precondition: Call setup_multisynth() first to fix divider; then call this.
            - Side effects: Calls setup_pll(); updates self.vco.
            - ISR-safe: no.
        """
        if output not in self.div or self.div[output] is None:
            raise ValueError('multisynth not initialized: call setup_multisynth() first')
        if output not in self.rdiv:
            raise ValueError('rdiv not initialized: call setup_multisynth() first')

        div = self.div[output]
        rdiv = self.rdiv[output]
        pll = self.pll[output]
        crystal = self.crystal

        vco = float(freq_hz) * div * (1 << rdiv)

        vco10 = int(10 * vco)
        denom = int(10 * crystal)
        num = vco10 % denom
        mul = vco10 // denom
        if (mul < self.SI5351_MULTISYNTH_MUL_MIN or
                mul >= self.SI5351_MULTISYNTH_MUL_MAX):
            raise ValueError('pll multiplier out of range')
        max_denom = self.SI5351_MULTISYNTH_C_MAX
        num, denom = self.approximate_fraction(num, denom, max_denom=max_denom)
        self.setup_pll(pll, mul=mul, num=num, denom=denom)

    def disabled_states(self, output, state):
        """
        设置输出在被禁用（软件或 OEB 引脚）时的电气状态。

        Args:
            output (int): 输出口（0..7）。
            state (int): 禁用状态常量（低/高/高阻/永不禁用）。

        Raises:
            RuntimeError: I2C 访问失败。
            ValueError: 参数越界。

        Notes：
            - 副作用：读改写 DIS_STATE1/2 寄存器。
            - ISR-safe: no。
        =========================================
        Set the electrical state for an output when disabled (by SW or OEB pin).

        Args:
            output (int): Output index (0..7).
            state (int): Disabled-state constant (low/high/Hi-Z/never).

        Raises:
            RuntimeError: On I2C error.
            ValueError: If out of range.

        Notes：
            - Side effects: RMW on DIS_STATE1/2 registers.
            - ISR-safe: no.
        """
        if output < 4:
            reg = self.SI5351_REGISTER_DIS_STATE_1
        else:
            reg = self.SI5351_REGISTER_DIS_STATE_2
            output -= 4
        if output not in (0, 1, 2, 3):
            raise ValueError("output out of range")
        value = self.read(reg)
        s = [(value >> (n * 2)) & 0x3 for n in range(4)]
        s[output] = state & 0x3
        self.write(reg, (s[3] << 6) | (s[2] << 4) | (s[1] << 2) | s[0])

    def disable_oeb(self, mask):
        """
        关闭指定输出对 OEB 引脚的响应（按位掩码）。

        Args:
            mask (int): 低 8 位位图；1 表示关闭该通道的 OEB 支持。

        Raises:
            RuntimeError: I2C 访问失败。

        Notes：
            - 副作用：写 OEB_ENABLE_CONTROL 寄存器。
            - ISR-safe: no。
        =========================================
        Disable OEB-pin response for selected outputs (bitmask).

        Args:
            mask (int): Low-8-bit bitmap; 1 disables OEB for that channel.

        Raises:
            RuntimeError: On I2C error.

        Notes：
            - Side effects: Writes OEB_ENABLE_CONTROL register.
            - ISR-safe: no.
        """
        self.write(self.SI5351_REGISTER_OEB_ENABLE_CONTROL, mask & 0xFF)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================