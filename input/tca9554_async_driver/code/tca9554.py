# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : FreakStudio
# @File    : tca9554.py
# @Description : TCA9554 8-bit I2C IO expander driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


from machine import I2C

# ======================================== 全局变量 ============================================

# TCA9554 默认 I2C 地址
TCA9554_DEFAULT_ADDR = const(0x20)

# TCA9554 寄存器地址
TCA9554_REG_INPUT = const(0x00)
TCA9554_REG_OUTPUT = const(0x01)
TCA9554_REG_POLARITY = const(0x02)
TCA9554_REG_CONFIG = const(0x03)

# 引脚方向常量（方向寄存器: 1=输入, 0=输出）
TCA9554_INPUT = const(1)
TCA9554_OUTPUT = const(0)

# 引脚电平常量
TCA9554_LOW = const(0)
TCA9554_HIGH = const(1)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class TCA9554:
    """
    TCA9554 8位 I2C GPIO 扩展器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址 (0x20-0x27)
        _config (int): 方向配置寄存器镜像 (1=输入, 0=输出)
        _output (int): 输出寄存器镜像
        _debug (bool): 调试日志开关
    Methods:
        is_connected(): 检查设备是否连接
        pin_mode(): 设置单个引脚方向
        pin_mode8(): 设置全部8个引脚方向
        write(): 设置单个引脚输出电平
        write_port(): 设置全部8个引脚输出电平
        read(): 读取单个引脚输入电平
        read_input8(): 读取全部8个引脚输入电平
        read_output8(): 读取全部8个引脚输出电平
        set_polarity(): 设置单个引脚极性反转
        set_polarity8(): 设置全部8个引脚极性反转
        deinit(): 释放资源，所有引脚恢复输入模式
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 方向寄存器: 1=输入, 0=输出，严禁对调
        - 参考 RobTillaart Arduino TCA9554 驱动逻辑
    ==========================================
    TCA9554 8-bit I2C GPIO expander driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address (0x20-0x27)
        _config (int): Direction register mirror (1=input, 0=output)
        _output (int): Output register mirror
        _debug (bool): Debug log switch
    Methods:
        is_connected(): Check if device is connected
        pin_mode(): Set single pin direction
        pin_mode8(): Set all 8 pins direction
        write(): Set single pin output level
        write_port(): Set all 8 pins output level
        read(): Read single pin input level
        read_input8(): Read all 8 pins input level
        read_output8(): Read all 8 pins output level
        set_polarity(): Set single pin polarity inversion
        set_polarity8(): Set all 8 pins polarity inversion
        deinit(): Release resources, restore all pins to input mode
    Notes:
        - Requires externally provided I2C instance
        - Direction register: 1=input, 0=output, do NOT swap
        - Based on RobTillaart Arduino TCA9554 driver logic
    """

    __slots__ = ("_i2c", "_address", "_config", "_output", "_debug")

    def __init__(self, i2c: I2C, address: int = TCA9554_DEFAULT_ADDR, config: int = 0xFF, output: int = 0x00, debug: bool = False) -> None:
        """
        初始化 TCA9554 驱动
        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x20，范围 0x20-0x27
            config (int): 初始方向配置，默认 0xFF（全部输入）
            output (int): 初始输出值，默认 0x00
            debug (bool): 调试日志开关，默认 False
        Returns:
            None
        Raises:
            ValueError: 参数类型或值无效
            RuntimeError: I2C 通信失败
        Notes:
            - 方向寄存器: 1=输入, 0=输出
        ==========================================
        Initialize TCA9554 driver.
        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x20, range 0x20-0x27
            config (int): Initial direction config, default 0xFF (all input)
            output (int): Initial output value, default 0x00
            debug (bool): Debug log switch, default False
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type or value
            RuntimeError: I2C communication failed
        Notes:
            - Direction register: 1=input, 0=output
        """
        # 参数校验：I2C 实例必须具有 readfrom_mem 方法
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem()")
        # 参数校验：地址类型检查
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        # 参数校验：地址范围检查
        if address < 0x20 or address > 0x27:
            raise ValueError("address must be 0x20..0x27, got 0x%02X" % address)
        # 参数校验：config 类型检查
        if not isinstance(config, int):
            raise ValueError("config must be int, got %s" % type(config))
        # 参数校验：output 类型检查
        if not isinstance(output, int):
            raise ValueError("output must be int, got %s" % type(output))
        # 参数校验：debug 类型检查
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._config = config & 0xFF
        self._output = output & 0xFF
        self._debug = debug

        # 初始化硬件：写入输出寄存器
        self.write_port(self._output)
        # 初始化硬件：写入方向配置寄存器
        self.pin_mode8(self._config)
        self._log("TCA9554 initialized at 0x%02X" % self._address)

    def is_connected(self) -> bool:
        """
        检查设备是否连接（I2C 探测）
        Returns:
            bool: 设备响应则返回 True，否则返回 False
        Notes:
            - 通过尝试读取输入寄存器来检测设备是否存在
            - ISR-safe: 否
        ==========================================
        Check if device is connected (I2C probe).
        Returns:
            bool: True if device responds, False otherwise
        Notes:
            - Detects device by attempting to read input register
            - ISR-safe: No
        """
        # 直接 I2C 探测读取，不经过包装层
        try:
            self._i2c.readfrom_mem(self._address, TCA9554_REG_INPUT, 1)
            return True
        except OSError:
            return False

    def pin_mode(self, pin: int, mode: int) -> None:
        """
        设置单个引脚的方向模式
        Args:
            pin (int): 引脚编号 0-7
            mode (int): TCA9554_INPUT 或 TCA9554_OUTPUT
        Returns:
            None
        Raises:
            ValueError: 引脚编号或模式无效
            RuntimeError: I2C 通信失败
        Notes:
            - 修改硬件方向寄存器
            - 方向寄存器: 1=输入, 0=输出
            - ISR-safe: 否
        ==========================================
        Set single pin direction mode.
        Args:
            pin (int): Pin number 0-7
            mode (int): TCA9554_INPUT or TCA9554_OUTPUT
        Returns:
            None
        Raises:
            ValueError: Invalid pin number or mode
            RuntimeError: I2C communication failed
        Notes:
            - Modifies hardware direction register
            - Direction register: 1=input, 0=output
            - ISR-safe: No
        """
        # 校验引脚编号
        self._check_pin(pin)
        # 根据模式设置或清除方向位（1=输入置位，0=输出清除）
        if mode == TCA9554_INPUT:
            self._config |= 1 << pin
        elif mode == TCA9554_OUTPUT:
            self._config &= ~(1 << pin)
        else:
            raise ValueError("mode must be TCA9554_INPUT or TCA9554_OUTPUT")
        # 写入硬件方向配置寄存器
        self.pin_mode8(self._config)

    def pin_mode8(self, mask: int) -> None:
        """
        设置全部8个引脚的方向模式
        Args:
            mask (int): 8位方向掩码，每 bit 1=输入, 0=输出
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 修改硬件方向寄存器
            - ISR-safe: 否
        ==========================================
        Set all 8 pins direction mode.
        Args:
            mask (int): 8-bit direction mask, each bit 1=input, 0=output
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Modifies hardware direction register
            - ISR-safe: No
        """
        # 更新方向配置镜像
        self._config = mask & 0xFF
        # 写入硬件方向配置寄存器
        self._write_u8(TCA9554_REG_CONFIG, self._config)

    def write(self, pin: int, value: int) -> None:
        """
        设置单个引脚的输出电平
        Args:
            pin (int): 引脚编号 0-7
            value (int): TCA9554_HIGH 或 TCA9554_LOW
        Returns:
            None
        Raises:
            ValueError: 引脚编号无效
            RuntimeError: I2C 通信失败
        Notes:
            - 修改硬件输出寄存器
            - 仅对被配置为输出的引脚生效
            - ISR-safe: 否
        ==========================================
        Set single pin output level.
        Args:
            pin (int): Pin number 0-7
            value (int): TCA9554_HIGH or TCA9554_LOW
        Returns:
            None
        Raises:
            ValueError: Invalid pin number
            RuntimeError: I2C communication failed
        Notes:
            - Modifies hardware output register
            - Only effective for pins configured as output
            - ISR-safe: No
        """
        # 校验引脚编号
        self._check_pin(pin)
        # 根据电平值设置或清除输出位
        if value:
            self._output |= 1 << pin
        else:
            self._output &= ~(1 << pin)
        # 写入硬件输出寄存器
        self.write_port(self._output)

    def write_port(self, value: int) -> None:
        """
        设置全部8个引脚的输出电平
        Args:
            value (int): 8位输出值，每 bit 1=高电平, 0=低电平
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 修改硬件输出寄存器
            - ISR-safe: 否
        ==========================================
        Set all 8 pins output level.
        Args:
            value (int): 8-bit output value, each bit 1=high, 0=low
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Modifies hardware output register
            - ISR-safe: No
        """
        # 更新输出镜像
        self._output = value & 0xFF
        # 写入硬件输出寄存器
        self._write_u8(TCA9554_REG_OUTPUT, self._output)

    def read(self, pin: int) -> int:
        """
        读取单个引脚的输入电平
        Args:
            pin (int): 引脚编号 0-7
        Returns:
            int: 引脚电平（0 或 1）
        Raises:
            ValueError: 引脚编号无效
            RuntimeError: I2C 通信失败
        Notes:
            - 读取硬件输入寄存器
            - ISR-safe: 否
        ==========================================
        Read single pin input level.
        Args:
            pin (int): Pin number 0-7
        Returns:
            int: Pin level (0 or 1)
        Raises:
            ValueError: Invalid pin number
            RuntimeError: I2C communication failed
        Notes:
            - Reads hardware input register
            - ISR-safe: No
        """
        # 校验引脚编号
        self._check_pin(pin)
        # 读取输入寄存器并提取对应位
        return (self.read_input8() >> pin) & 0x01

    def read_input8(self) -> int:
        """
        读取全部8个引脚的输入电平
        Returns:
            int: 8位输入值，每 bit 对应一个引脚
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 读取硬件输入寄存器
            - ISR-safe: 否
        ==========================================
        Read all 8 pins input level.
        Returns:
            int: 8-bit input value, each bit corresponds to a pin
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads hardware input register
            - ISR-safe: No
        """
        # 读取硬件输入寄存器
        return self._read_u8(TCA9554_REG_INPUT)

    def read_output8(self) -> int:
        """
        读取全部8个引脚的输出电平
        Returns:
            int: 8位输出值，每 bit 对应一个引脚
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 读取硬件输出寄存器
            - ISR-safe: 否
        ==========================================
        Read all 8 pins output level.
        Returns:
            int: 8-bit output value, each bit corresponds to a pin
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads hardware output register
            - ISR-safe: No
        """
        # 读取硬件输出寄存器
        return self._read_u8(TCA9554_REG_OUTPUT)

    def set_polarity(self, pin: int, invert: bool) -> None:
        """
        设置单个引脚的极性反转
        Args:
            pin (int): 引脚编号 0-7
            invert (bool): True 反转极性, False 正常极性
        Returns:
            None
        Raises:
            ValueError: 引脚编号无效
            RuntimeError: I2C 通信失败
        Notes:
            - 修改硬件极性寄存器
            - ISR-safe: 否
        ==========================================
        Set single pin polarity inversion.
        Args:
            pin (int): Pin number 0-7
            invert (bool): True to invert polarity, False for normal
        Returns:
            None
        Raises:
            ValueError: Invalid pin number
            RuntimeError: I2C communication failed
        Notes:
            - Modifies hardware polarity register
            - ISR-safe: No
        """
        # 校验引脚编号
        self._check_pin(pin)
        # 读取当前极性寄存器值
        value = self._read_u8(TCA9554_REG_POLARITY)
        # 根据反转标志设置或清除对应位
        if invert:
            value |= 1 << pin
        else:
            value &= ~(1 << pin)
        # 写入硬件极性寄存器
        self._write_u8(TCA9554_REG_POLARITY, value)

    def set_polarity8(self, mask: int) -> None:
        """
        设置全部8个引脚的极性反转
        Args:
            mask (int): 8位极性掩码，每 bit 1=反转, 0=正常
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 修改硬件极性寄存器
            - ISR-safe: 否
        ==========================================
        Set all 8 pins polarity inversion.
        Args:
            mask (int): 8-bit polarity mask, each bit 1=invert, 0=normal
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Modifies hardware polarity register
            - ISR-safe: No
        """
        # 写入硬件极性寄存器
        self._write_u8(TCA9554_REG_POLARITY, mask & 0xFF)

    def deinit(self) -> None:
        """
        释放资源，将所有引脚恢复为输入模式
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 设置所有引脚为输入（0xFF），安全释放 IO
            - ISR-safe: 否
        ==========================================
        Release resources, restore all pins to input mode.
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Sets all pins to input (0xFF), safely release IO
            - ISR-safe: No
        """
        # 将所有引脚恢复为输入模式（高阻态，安全释放）
        self.pin_mode8(0xFF)
        self._log("TCA9554 deinitialized")

    # ======================== 私有方法 ========================

    async def pin_mode8_async(self, mask): self.pin_mode8(mask)
    async def write_port_async(self, value): self.write_port(value)
    async def read_output8_async(self): return self.read_output8()
    async def read_input8_async(self): return self.read_input8()
    async def set_polarity_async(self, pin, invert): self.set_polarity(pin, invert)
    async def read_async(self, pin): return self.read(pin)

    def _log(self, msg: str) -> None:
        """
        输出调试日志
        Args:
            msg (str): 日志消息
        Returns:
            None
        Notes:
            - 仅在 self._debug 为 True 时输出
            - ISR-safe: 否
        ==========================================
        Output debug log.
        Args:
            msg (str): Log message
        Returns:
            None
        Notes:
            - Only outputs when self._debug is True
            - ISR-safe: No
        """
        if self._debug:
            print("[TCA9554] %s" % msg)

    def _read_u8(self, reg: int) -> int:
        """
        从指定寄存器读取一个字节
        Args:
            reg (int): 寄存器地址
        Returns:
            int: 读取的字节值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read one byte from specified register.
        Args:
            reg (int): Register address
        Returns:
            int: Byte value read
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            return self._i2c.readfrom_mem(self._address, reg, 1)[0]
        except OSError:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg)

    def _write_u8(self, reg: int, value: int) -> None:
        """
        向指定寄存器写入一个字节
        Args:
            reg (int): 寄存器地址
            value (int): 要写入的字节值
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write one byte to specified register.
        Args:
            reg (int): Register address
            value (int): Byte value to write
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            self._i2c.writeto_mem(self._address, reg, bytes([value & 0xFF]))
        except OSError:
            raise RuntimeError("I2C write failed at reg 0x%02X" % reg)

    def _check_pin(self, pin: int) -> None:
        """
        校验引脚编号是否在有效范围
        Args:
            pin (int): 引脚编号
        Returns:
            None
        Raises:
            ValueError: 引脚编号超出 0-7 范围
        Notes:
            - ISR-safe: 否
        ==========================================
        Validate pin number is in valid range.
        Args:
            pin (int): Pin number
        Returns:
            None
        Raises:
            ValueError: Pin number out of 0-7 range
        Notes:
            - ISR-safe: No
        """
        if pin < 0 or pin > 7:
            raise ValueError("pin must be 0..7, got %d" % pin)


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
