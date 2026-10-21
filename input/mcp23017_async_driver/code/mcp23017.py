# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午5:40
# @Author  : mcauser
# @File    : mcp23017.py
# @Description : MCP23017 16位I/O扩展器驱动  I2C接口，实现GPIO扩展、输入输出、上拉、中断功能 参考自:https://github.com/mcauser/micropython-mcp23017
# @License : MIT
__version__ = "0.1.4"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================


# ======================================== 全局变量 ============================================
# BANK=1模式下寄存器地址，方便计算
# I/O方向寄存器，1=输入，0=输出
_MCP_IODIR = const(0x00)
# 输入极性寄存器，1=反转，0=正常
_MCP_IPOL = const(0x01)
# 中断使能寄存器，1=使能中断，0=禁止
_MCP_GPINTEN = const(0x02)
# 中断默认比较值寄存器
_MCP_DEFVAL = const(0x03)
# 中断比较控制寄存器
_MCP_INTCON = const(0x04)
# 设备配置寄存器
_MCP_IOCON = const(0x05)
# 上拉电阻使能寄存器，1=使能上拉
_MCP_GPPU = const(0x06)
# 中断标志寄存器，只读
_MCP_INTF = const(0x07)
# 中断捕获值寄存器，只读
_MCP_INTCAP = const(0x08)
# GPIO端口数据寄存器
_MCP_GPIO = const(0x09)
# 输出锁存寄存器
_MCP_OLAT = const(0x0A)

# IOCON配置寄存器位定义
# 中断输出极性
_MCP_IOCON_INTPOL = const(2)
# 中断开漏输出使能
_MCP_IOCON_ODR = const(4)
# SDA引脚斜率控制禁止
_MCP_IOCON_DISSLW = const(16)
# 地址指针自增禁止
_MCP_IOCON_SEQOP = const(32)
# 中断引脚镜像使能
_MCP_IOCON_MIRROR = const(64)
# 寄存器分组模式
_MCP_IOCON_BANK = const(128)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class Port:
    """
    MCP23017单个端口类，代表8位PortA或PortB

    Attributes:
        _port (int): 端口编号，0表示PortA，1表示PortB
        _mcp (MCP23017): 所属的MCP23017对象
        mode (int): I/O方向寄存器值，1=输入，0=输出
        input_polarity (int): 输入极性寄存器值，1=反转，0=正常
        interrupt_enable (int): 中断使能寄存器值，1=使能
        default_value (int): 中断默认比较值寄存器值
        interrupt_compare_default (int): 中断比较控制寄存器值
        io_config (int): 芯片配置寄存器值
        pullup (int): 上拉使能寄存器值，1=使能
        interrupt_flag (int): 中断标志寄存器（只读）
        interrupt_captured (int): 中断捕获值寄存器（只读）
        gpio (int): GPIO端口数据寄存器值
        output_latch (int): 输出锁存寄存器值

    Methods:
        __init__(port, mcp): 初始化端口对象

    Notes:
        封装单个8位端口的所有寄存器操作，供MCP23017类使用

    ==========================================
    8-bit port class for MCP23017 (PortA or PortB)

    Attributes:
        _port (int): Port number 0=PortA,1=PortB
        _mcp (MCP23017): Parent MCP23017 object
        mode (int): I/O direction register, 1=input, 0=output
        input_polarity (int): Input polarity register, 1=invert, 0=normal
        interrupt_enable (int): Interrupt enable register, 1=enable
        default_value (int): Default compare value register
        interrupt_compare_default (int): Interrupt control register
        io_config (int): Configuration register
        pullup (int): Pull-up enable register, 1=enable
        interrupt_flag (int): Interrupt flag register (read-only)
        interrupt_captured (int): Interrupt capture register (read-only)
        gpio (int): GPIO port register
        output_latch (int): Output latch register

    Methods:
        __init__(port, mcp): Initialize port instance

    Notes:
        Handles all register operations for one 8-bit port
    """

    def __init__(self, port: int, mcp: "MCP23017") -> None:
        """
        构造函数，初始化端口对象

        Args:
            port (int): 端口编号 0=PortA,1=PortB
            mcp (MCP23017): 所属MCP23017实例

        Raises:
            ValueError: port或mcp为None
            TypeError: port不是整数或mcp不是MCP23017实例
            ValueError: port不是0或1

        Notes:
            保存端口编号与父对象引用

        ==========================================
        Constructor, initialize port instance

        Args:
            port (int): Port number 0=PortA,1=PortB
            mcp (MCP23017): Parent MCP23017 instance

        Raises:
            ValueError: port or mcp is None
            TypeError: port is not int or mcp is not MCP23017 instance
            ValueError: port is not 0 or 1

        Notes:
            Store port number and parent object
        """
        if port is None:
            raise ValueError("port cannot be None")
        if not isinstance(port, int):
            raise TypeError(f"port must be int, got {type(port).__name__}")
        if port < 0 or port > 1:
            raise ValueError(f"port must be 0 or 1, got {port}")
        if mcp is None:
            raise ValueError("mcp cannot be None")
        if not isinstance(mcp, MCP23017):
            raise TypeError(f"mcp must be MCP23017 instance, got {type(mcp).__name__}")

        self._port = port & 1
        self._mcp = mcp

    def _which_reg(self, reg: int) -> int:
        """
        根据当前BANK模式计算真实寄存器地址

        Args:
            reg (int): 基础寄存器地址（0x00-0x0A）

        Returns:
            int: 实际寄存器地址

        Raises:
            ValueError: reg为None
            TypeError: reg不是整数
            ValueError: reg超出0x00-0x0F范围

        Notes:
            支持BANK=0和BANK=1两种模式

        ==========================================
        Calculate real register address based on BANK mode

        Args:
            reg (int): Base register address (0x00-0x0A)

        Returns:
            int: Actual register address

        Raises:
            ValueError: reg is None
            TypeError: reg is not int
            ValueError: reg out of range 0x00-0x0F

        Notes:
            Support both BANK=0 and BANK=1 mode
        """
        if reg is None:
            raise ValueError("reg cannot be None")
        if not isinstance(reg, int):
            raise TypeError(f"reg must be int, got {type(reg).__name__}")
        if reg < 0 or reg > 0x0F:
            raise ValueError(f"reg must be 0x00-0x0F, got {hex(reg)}")

        if self._mcp._config & 0x80 == 0x80:
            return reg | (self._port << 4)
        else:
            return (reg << 1) + self._port

    def _flip_property_bit(self, reg: str, condition: int, bit: int) -> None:
        """
        对寄存器属性的特定位进行置1或清0操作

        Args:
            reg (str): 寄存器属性名（如'mode'）
            condition (int): True置1，False置0
            bit (int): 位掩码（1<<n）

        Raises:
            ValueError: 任何参数为None
            TypeError: reg不是字符串，condition不是bool，bit不是整数
            ValueError: bit超出0-255范围

        Notes:
            内部使用，用于批量修改引脚配置

        ==========================================
        Set or clear a specific bit in a register property

        Args:
            reg (str): Register property name (e.g., 'mode')
            condition (bool): True=set 1, False=set 0
            bit (int): Bit mask (1<<n)

        Raises:
            ValueError: Any parameter is None
            TypeError: reg is not str, condition is not bool, bit is not int
            ValueError: bit out of range 0-255

        Notes:
            Internal use for bulk pin configuration
        """
        if reg is None:
            raise ValueError("reg cannot be None")
        if not isinstance(reg, str):
            raise TypeError(f"reg must be str, got {type(reg).__name__}")
        if condition is None:
            raise ValueError("condition cannot be None")
        if not isinstance(condition, int):
            raise TypeError(f"condition must be int, got {type(condition).__name__}")
        if bit is None:
            raise ValueError("bit cannot be None")
        if not isinstance(bit, int):
            raise TypeError(f"bit must be int, got {type(bit).__name__}")
        if bit < 0 or bit > 255:
            raise ValueError(f"bit must be 0-255, got {bit}")

        if condition:
            setattr(self, reg, getattr(self, reg) | bit)
        else:
            setattr(self, reg, getattr(self, reg) & ~bit)

    def _read(self, reg: int) -> int:
        """
        从端口寄存器读取一个字节

        Args:
        reg (int): 寄存器基地址 (0x00-0x0A)

        Returns:
        int: 读取的字节值 (0-255)

        Raises:
        TypeError: 寄存器地址不是整数类型
        ValueError: 寄存器地址超出 0x00-0x0A 范围
        OSError: I2C 读取失败

        Notes:
        在自动计算端口偏移地址后读取

        =============================================
        Read one byte from port register

        Args:
            reg (int): Register base address (0x00-0x0A)

        Returns:
            int: Byte value read (0-255)

        Raises:
            TypeError: Register address is not integer type
            ValueError: Register address out of 0x00-0x0A range
            OSError: I2C read failure

        Notes:
            Read after calculating port offset address automatically
        """
        # 1. 检查reg是否为None
        if reg is None:
            raise TypeError("Register address cannot be None")

        # 2. 验证reg参数类型
        if not isinstance(reg, int):
            raise TypeError(f"Register address must be an integer type, current type: {type(reg).__name__}")

        # 3. 验证reg参数范围 (0x00-0x0A 即 0-10)
        if not (0x00 <= reg <= 0x0A):
            raise ValueError(f"Register address must be in the range 0x00-0x0A (0-10), current value: 0x{reg:02X}")

        # 4. 验证依赖对象是否有效（防止属性缺失/None）
        if not hasattr(self, "_mcp") or self._mcp is None:
            raise OSError("Parent MCP23017 object is not initialized (self._mcp is None)")
        if not hasattr(self._mcp, "_i2c") or self._mcp._i2c is None:
            raise OSError("I2C bus object is not initialized (self._mcp._i2c is None)")
        if not hasattr(self._mcp, "_address") or self._mcp._address is None:
            raise OSError("MCP23017 I2C address is not set (self._mcp._address is None)")

        # 5. 验证偏移地址计算结果
        offset_reg = self._which_reg(reg)
        if not isinstance(offset_reg, int) or offset_reg < 0:
            raise ValueError(f"Calculated offset register address is invalid: 0x{offset_reg:02X}")

        # 执行读取逻辑（捕获I2C底层异常并封装）
        try:
            return self._mcp._i2c.readfrom_mem(self._mcp._address, offset_reg, 1)[0]
        except Exception as e:
            raise OSError(f"I2C read failed from register 0x{reg:02X} (offset 0x{offset_reg:02X}): {str(e)}") from e

    def _write(self, reg: int, val: int) -> None:
        """
        向端口寄存器写入一个字节

        Args:
        reg (int): 寄存器基地址 (0x00-0x0A)
        val (int): 要写入的值 (0-65535)

        Raises:
        TypeError: 寄存器地址/值不是整数类型
        ValueError: 寄存器地址超出 0x00-0x0A 范围，或值超出 0-65535 范围
        OSError: I2C 写入失败

        Notes:
        写入配置寄存器时，需要与父对象的 _config 同步
        =======================================================
        Write one byte to port register

        Args:
            reg (int): Register base address (0x00-0x0A)
            val (int): Value to write (0-65535)

        Raises:
            TypeError: Register address/value is not integer type
            ValueError: Register address out of 0x00-0x0A range, or value out of 0-65535 range
            OSError: I2C write failure

        Notes:
            Synchronize to parent object's _config when writing to configuration register
        """
        # 1. 检查reg/val是否为None
        if reg is None:
            raise TypeError("Register address cannot be None")
        if val is None:
            raise TypeError("Write value cannot be None")

        # 2. 验证reg参数类型和范围
        if not isinstance(reg, int):
            raise TypeError(f"Register address must be an integer type, current type: {type(reg).__name__}")
        if not (0x00 <= reg <= 0x0A):
            raise ValueError(f"Register address must be in the range 0x00-0x0A (0-10), current value: 0x{reg:02X}")

        # 3. 验证val参数类型和范围
        if not isinstance(val, int):
            raise TypeError(f"Value to write must be an integer type, current type: {type(val).__name__}")
        if not (0 <= val <= 65535):
            raise ValueError(f"Value to write must be in the range 0-65535, current value: {val}")

        # 4. 验证依赖对象是否有效（防止属性缺失/None）
        if not hasattr(self, "_mcp") or self._mcp is None:
            raise OSError("Parent MCP23017 object is not initialized (self._mcp is None)")
        if not hasattr(self._mcp, "_i2c") or self._mcp._i2c is None:
            raise OSError("I2C bus object is not initialized (self._mcp._i2c is None)")
        if not hasattr(self._mcp, "_address") or self._mcp._address is None:
            raise OSError("MCP23017 I2C address is not set (self._mcp._address is None)")

        # 5. 验证偏移地址计算结果
        offset_reg = self._which_reg(reg)
        if not isinstance(offset_reg, int) or offset_reg < 0:
            raise ValueError(f"Calculated offset register address is invalid: 0x{offset_reg:02X}")

        # 执行写入逻辑（保留兜底保护，捕获I2C底层异常并封装）
        val &= 0xFF  # 仅保留低8位，符合1字节寄存器要求
        try:
            self._mcp._i2c.writeto_mem(self._mcp._address, offset_reg, bytearray([val]))
            # 同步配置寄存器值
            if reg == _MCP_IOCON:
                self._mcp._config = val
        except Exception as e:
            raise OSError(f"I2C write failed to register 0x{reg:02X} (offset 0x{offset_reg:02X}) with value 0x{val:02X}: {str(e)}") from e

    @property
    def mode(self) -> int:
        """
        I/O方向寄存器，1=输入，0=输出
        """
        return self._read(_MCP_IODIR)

    @mode.setter
    def mode(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65536:
            raise ValueError(f"val must be 0-65536, got {val}")
        self._write(_MCP_IODIR, val)

    @property
    def input_polarity(self) -> int:
        """
        输入极性寄存器，1=反转，0=正常
        """
        return self._read(_MCP_IPOL)

    @input_polarity.setter
    def input_polarity(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_IPOL, val)

    @property
    def interrupt_enable(self) -> int:
        """
        中断使能寄存器，1=使能
        """
        return self._read(_MCP_GPINTEN)

    @interrupt_enable.setter
    def interrupt_enable(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_GPINTEN, val)

    @property
    def default_value(self) -> int:
        """
        中断默认比较值寄存器
        """
        return self._read(_MCP_DEFVAL)

    @default_value.setter
    def default_value(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_DEFVAL, val)

    @property
    def interrupt_compare_default(self) -> int:
        """
        中断比较控制寄存器
        """
        return self._read(_MCP_INTCON)

    @interrupt_compare_default.setter
    def interrupt_compare_default(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_INTCON, val)

    @property
    def io_config(self) -> int:
        """
        芯片配置寄存器
        """
        return self._read(_MCP_IOCON)

    @io_config.setter
    def io_config(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_IOCON, val)

    @property
    def pullup(self) -> int:
        """
        上拉使能寄存器，1=上拉使能
        """
        return self._read(_MCP_GPPU)

    @pullup.setter
    def pullup(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_GPPU, val)

    @property
    def interrupt_flag(self) -> int:
        """
        中断标志寄存器，只读
        """
        return self._read(_MCP_INTF)

    @property
    def interrupt_captured(self) -> int:
        """
        中断捕获值寄存器，只读
        """
        return self._read(_MCP_INTCAP)

    @property
    def gpio(self) -> int:
        """
        GPIO端口数据寄存器
        """
        return self._read(_MCP_GPIO)

    @gpio.setter
    def gpio(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_GPIO, val)

    @property
    def output_latch(self) -> int:
        """
        输出锁存寄存器
        """
        return self._read(_MCP_OLAT)

    @output_latch.setter
    def output_latch(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self._write(_MCP_OLAT, val)


class MCP23017:
    """
    MCP23017 16位I/O扩展器驱动主类

    Attributes:
        _i2c (I2C): I2C总线对象
        _address (int): I2C从机地址
        _config (int): 配置寄存器缓存
        _virtual_pins (dict): 虚拟引脚对象缓存
        porta (Port): PortA端口对象
        portb (Port): PortB端口对象
        mode (int): 16位I/O方向，1=输入，0=输出
        input_polarity (int): 16位输入极性，1=反转
        interrupt_enable (int): 16位中断使能
        default_value (int): 16位中断默认值
        interrupt_compare_default (int): 16位中断比较模式
        io_config (int): 配置寄存器（8位）
        pullup (int): 16位上拉使能
        interrupt_flag (int): 16位中断标志（只读）
        interrupt_captured (int): 16位中断捕获值（只读）
        gpio (int): 16位GPIO值
        output_latch (int): 16位输出锁存值

    Methods:
        __init__(i2c, address): 构造函数，初始化I2C与设备
        init(): 初始化设备，检测是否在线，恢复默认配置
        config(interrupt_polarity, interrupt_open_drain, sda_slew, sequential_operation, interrupt_mirror, bank): 配置芯片工作模式
        pin(pin, mode, value, pullup, polarity, interrupt_enable, interrupt_compare_default, default_value): 单引脚配置与控制
        interrupt_triggered_gpio(port): 获取指定端口触发中断的引脚
        interrupt_captured_gpio(port): 获取中断触发时端口的电平状态
        __getitem__(pin): 以列表形式访问引脚，返回虚拟引脚对象

    Notes:
        提供16路GPIO的统一控制接口

    ==========================================
    MCP23017 16-bit I/O expander driver main class

    Attributes:
        _i2c (I2C): I2C bus object
        _address (int): I2C slave address
        _config (int): Config register cache
        _virtual_pins (dict): Virtual pin cache
        porta (Port): PortA instance
        portb (Port): PortB instance
        mode (int): 16-bit I/O direction, 1=input, 0=output
        input_polarity (int): 16-bit input polarity, 1=invert
        interrupt_enable (int): 16-bit interrupt enable
        default_value (int): 16-bit default compare value
        interrupt_compare_default (int): 16-bit interrupt compare mode
        io_config (int): Configuration register (8-bit)
        pullup (int): 16-bit pull-up enable
        interrupt_flag (int): 16-bit interrupt flag (read-only)
        interrupt_captured (int): 16-bit captured GPIO value (read-only)
        gpio (int): 16-bit GPIO value
        output_latch (int): 16-bit output latch value

    Methods:
        __init__(i2c, address): Constructor, init I2C and device
        init(): Initialize device, check presence, reset to default
        config(interrupt_polarity, interrupt_open_drain, sda_slew, sequential_operation, interrupt_mirror, bank): Configure chip mode
        pin(pin, mode, value, pullup, polarity, interrupt_enable, interrupt_compare_default, default_value): Single pin configuration and control
        interrupt_triggered_gpio(port): Get interrupt flag for given port
        interrupt_captured_gpio(port): Get GPIO value captured at interrupt
        __getitem__(pin): Access pin like a list, return VirtualPin object

    Notes:
        Provide unified 16-channel GPIO control
    """

    def __init__(self, i2c, address: int = 0x20) -> None:
        """
        构造函数，初始化I2C与设备

        Args:
            i2c: 初始化好的I2C对象
            address: 设备I2C地址，默认0x20

        Raises:
            ValueError: i2c或address为None
            TypeError: i2c不是I2C对象或address不是整数
            ValueError: address超出0x20-0x27范围

        Notes:
            保存I2C与地址，调用init完成初始化

        ==========================================
        Constructor, init I2C and device

        Args:
            i2c: Initialized I2C object
            address: I2C address default 0x20

        Raises:
            ValueError: i2c or address is None
            TypeError: i2c is not I2C object or address is not int
            ValueError: address out of range 0x20-0x27

        Notes:
            Save I2C info and call init
        """
        if i2c is None:
            raise ValueError("i2c cannot be None")
        # 检查i2c对象是否具有必要的方法（scan, readfrom_mem, writeto_mem）
        if not hasattr(i2c, "scan") or not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "writeto_mem"):
            raise AttributeError("i2c must have scan, readfrom_mem and writeto_mem methods")
        if address is None:
            raise ValueError("address cannot be None")
        if not isinstance(address, int):
            raise TypeError(f"address must be int, got {type(address).__name__}")
        if address < 0x20 or address > 0x27:
            raise ValueError(f"address must be 0x20-0x27, got {hex(address)}")

        self._i2c = i2c
        self._address = address
        self._config = 0x00
        self._virtual_pins = {}
        self.init()

    def init(self) -> None:
        """
        初始化设备，检测是否在线，恢复默认配置

        Raises:
            OSError: 设备未找到时抛出

        Notes:
            上电默认全输入，无上拉，无中断

        ==========================================
        Initialize device, check presence, reset to default

        Raises:
            OSError: When device not found

        Notes:
            Default all input, no pullup, no interrupt
        """
        if self._i2c.scan().count(self._address) == 0:
            raise OSError("MCP23017 not found at I2C address {:#x}".format(self._address))

        self.porta = Port(0, self)
        self.portb = Port(1, self)

        self.io_config = 0x00

        self.mode = 0xFFFF
        self.input_polarity = 0x0000
        self.interrupt_enable = 0x0000
        self.default_value = 0x0000
        self.interrupt_compare_default = 0x0000
        self.pullup = 0x0000
        self.gpio = 0x0000

    def config(
        self,
        interrupt_polarity: bool = None,
        interrupt_open_drain: bool = None,
        sda_slew: bool = None,
        sequential_operation: bool = None,
        interrupt_mirror: bool = None,
        bank: bool = None,
    ) -> None:
        """
        配置MCP23017工作模式

        Args:
            interrupt_polarity (bool, optional): 中断极性，True高有效，False低有效
            interrupt_open_drain (bool, optional): 中断开漏输出
            sda_slew (bool, optional): SDA斜率控制
            sequential_operation (bool, optional): 地址自增控制
            interrupt_mirror (bool, optional): 中断引脚镜像
            bank (bool, optional): 寄存器分组模式

        Raises:
            ValueError: 任何参数为None（但允许None表示不修改）
            TypeError: 参数非布尔值（若非None）

        Notes:
            所有参数为None时不修改对应位

        ==========================================
        Configure MCP23017 operating mode

        Args:
            interrupt_polarity (bool, optional): INT pin polarity, True=active high, False=active low
            interrupt_open_drain (bool, optional): INT open drain
            sda_slew (bool, optional): SDA slew rate control
            sequential_operation (bool, optional): Address increment
            interrupt_mirror (bool, optional): INT mirror
            bank (bool, optional): Register bank mode

        Raises:
            ValueError: Any parameter is None (None is allowed meaning no change)
            TypeError: Parameter is not bool if not None

        Notes:
            None means do not change corresponding bit
        """
        # 可选参数不检查None，但检查类型（如果不是None）
        if interrupt_polarity is not None and not isinstance(interrupt_polarity, bool):
            raise TypeError(f"interrupt_polarity must be bool or None, got {type(interrupt_polarity).__name__}")
        if interrupt_open_drain is not None and not isinstance(interrupt_open_drain, bool):
            raise TypeError(f"interrupt_open_drain must be bool or None, got {type(interrupt_open_drain).__name__}")
        if sda_slew is not None and not isinstance(sda_slew, bool):
            raise TypeError(f"sda_slew must be bool or None, got {type(sda_slew).__name__}")
        if sequential_operation is not None and not isinstance(sequential_operation, bool):
            raise TypeError(f"sequential_operation must be bool or None, got {type(sequential_operation).__name__}")
        if interrupt_mirror is not None and not isinstance(interrupt_mirror, bool):
            raise TypeError(f"interrupt_mirror must be bool or None, got {type(interrupt_mirror).__name__}")
        if bank is not None and not isinstance(bank, bool):
            raise TypeError(f"bank must be bool or None, got {type(bank).__name__}")

        io_config = self.porta.io_config

        if interrupt_polarity is not None:
            io_config = self._flip_bit(io_config, interrupt_polarity, _MCP_IOCON_INTPOL)
            if interrupt_polarity:
                interrupt_open_drain = False
        if interrupt_open_drain is not None:
            io_config = self._flip_bit(io_config, interrupt_open_drain, _MCP_IOCON_ODR)
        if sda_slew is not None:
            io_config = self._flip_bit(io_config, sda_slew, _MCP_IOCON_DISSLW)
        if sequential_operation is not None:
            io_config = self._flip_bit(io_config, sequential_operation, _MCP_IOCON_SEQOP)
        if interrupt_mirror is not None:
            io_config = self._flip_bit(io_config, interrupt_mirror, _MCP_IOCON_MIRROR)
        if bank is not None:
            io_config = self._flip_bit(io_config, bank, _MCP_IOCON_BANK)

        self.porta.io_config = io_config
        self._config = io_config

    def _flip_bit(self, value: int, condition: int, bit: int) -> int:
        """
        位操作工具函数，置1或清0

        Args:
            value (int): 原始值
            condition (int):  True置1，False置0
            bit (int): 位掩码

        Returns:
            int: 修改后的值

        Raises:
            ValueError: 任何参数为None
            TypeError: 参数类型错误
            ValueError: value或bit超出范围

        Notes:
            内部工具方法

        ==========================================
        Bit operation helper

        Args:
            value (int): Original value
            condition (int): True=set 1, False=set 0
            bit (int): Bit mask

        Returns:
            int: Modified value

        Raises:
            ValueError: Any parameter is None
            TypeError: Parameter type error
            ValueError: value or bit out of range

        Notes:
            Internal helper method
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if value < 0 or value > 65535:  # 16-bit value
            raise ValueError(f"value must be 0-65535, got {value}")
        if condition is None:
            raise ValueError("condition cannot be None")
        if not isinstance(condition, int):
            raise TypeError(f"condition must be int, got {type(condition).__name__}")
        if bit is None:
            raise ValueError("bit cannot be None")
        if not isinstance(bit, int):
            raise TypeError(f"bit must be int, got {type(bit).__name__}")
        if bit < 0 or bit > 32768:  # 最大位掩码 1<<15
            raise ValueError(f"bit must be 0-32768, got {bit}")

        if condition:
            value |= bit
        else:
            value &= ~bit
        return value

    def pin(
        self,
        pin: int,
        mode: int = None,
        value: int = None,
        pullup: int = None,
        polarity: int = None,
        interrupt_enable: int = None,
        interrupt_compare_default: int = None,
        default_value: int = None,
    ) -> bool | None:
        """
        单引脚配置与控制

        Args:
            pin (int): 引脚号0~15
            mode (int, optional): 方向 0输出 1输入
            value (int, optional): 输出电平（0或1）
            pullup (int, optional): 上拉使能（0或1）
            polarity (int, optional): 输入极性（0正常 1反转）
            interrupt_enable (int, optional): 中断使能（0或1）
            interrupt_compare_default (int, optional): 中断比较模式（0或1）
            default_value (int, optional): 中断默认值（0或1）

        Returns:
            bool | None: 无value参数时返回引脚电平（True=高，False=低）

        Raises:
            ValueError: pin为None或超出范围
            TypeError: 参数类型错误
            ValueError: 非None的参数值不是0或1

        Notes:
            自动区分PortA/PortB

        ==========================================
        Single pin configuration and control

        Args:
            pin (int): Pin number 0~15
            mode (int, optional): 0=output,1=input
            value (int, optional): Output level (0 or 1)
            pullup (int, optional): Pullup enable (0 or 1)
            polarity (int, optional): Input polarity (0=normal,1=invert)
            interrupt_enable (int, optional): Interrupt enable (0 or 1)
            interrupt_compare_default (int, optional): Interrupt compare mode (0 or 1)
            default_value (int, optional): Default compare value (0 or 1)

        Returns:
            bool | None: Pin level if value is None (True=high, False=low)

        Raises:
            ValueError: pin is None or out of range
            TypeError: Parameter type error
            ValueError: Non-None parameter value not 0 or 1

        Notes:
            Auto select PortA/PortB
        """
        if pin is None:
            raise ValueError("pin cannot be None")
        if not isinstance(pin, int):
            raise TypeError(f"pin must be int, got {type(pin).__name__}")
        if pin < 0 or pin > 15:
            raise ValueError(f"pin must be 0-15, got {pin}")

        # 检查所有可选参数类型和取值范围
        for name, val in [
            ("mode", mode),
            ("value", value),
            ("pullup", pullup),
            ("polarity", polarity),
            ("interrupt_enable", interrupt_enable),
            ("interrupt_compare_default", interrupt_compare_default),
            ("default_value", default_value),
        ]:
            if val is not None:
                if not isinstance(val, int):
                    raise TypeError(f"{name} must be int or None, got {type(val).__name__}")
                if val not in (0, 1):
                    raise ValueError(f"{name} must be 0 or 1, got {val}")

        port = self.portb if pin // 8 else self.porta
        bit = 1 << (pin % 8)

        if mode is not None:
            port._flip_property_bit("mode", mode & 1, bit)
        if value is not None:
            port._flip_property_bit("gpio", value & 1, bit)
        if pullup is not None:
            port._flip_property_bit("pullup", pullup & 1, bit)
        if polarity is not None:
            port._flip_property_bit("input_polarity", polarity & 1, bit)
        if interrupt_enable is not None:
            port._flip_property_bit("interrupt_enable", interrupt_enable & 1, bit)
        if interrupt_compare_default is not None:
            port._flip_property_bit("interrupt_compare_default", interrupt_compare_default & 1, bit)
        if default_value is not None:
            port._flip_property_bit("default_value", default_value & 1, bit)
        if value is None:
            return port.gpio & bit == bit

    def interrupt_triggered_gpio(self, port: int) -> int:
        """
        获取指定端口触发中断的引脚

        Args:
            port (int): 端口号 0=PortA,1=PortB

        Returns:
            int: 中断标志位（8位）

        Raises:
            ValueError: port为None或超出范围
            TypeError: port不是整数

        Notes:
            读取后自动清除

        ==========================================
        Get interrupt flag for given port

        Args:
            port (int): Port number 0=PortA,1=PortB

        Returns:
            int: Interrupt flag bits (8-bit)

        Raises:
            ValueError: port is None or out of range
            TypeError: port is not int

        Notes:
            Read clears interrupt flag
        """
        if port is None:
            raise ValueError("port cannot be None")
        if not isinstance(port, int):
            raise TypeError(f"port must be int, got {type(port).__name__}")
        if port not in (0, 1):
            raise ValueError(f"port must be 0 or 1, got {port}")

        p = self.portb if port else self.porta
        return p.interrupt_flag

    def interrupt_captured_gpio(self, port: int) -> int:
        """
        获取中断触发时端口的电平状态

        Args:
            port (int): 端口号 0=PortA,1=PortB

        Returns:
            int: 捕获的GPIO值（8位）

        Raises:
            ValueError: port为None或超出范围
            TypeError: port不是整数

        Notes:
            读取后清除中断

        ==========================================
        Get GPIO value captured at interrupt

        Args:
            port (int): Port number 0=PortA,1=PortB

        Returns:
            int: Captured GPIO value (8-bit)

        Raises:
            ValueError: port is None or out of range
            TypeError: port is not int

        Notes:
            Read clears interrupt
        """
        if port is None:
            raise ValueError("port cannot be None")
        if not isinstance(port, int):
            raise TypeError(f"port must be int, got {type(port).__name__}")
        if port not in (0, 1):
            raise ValueError(f"port must be 0 or 1, got {port}")

        p = self.portb if port else self.porta
        return p.interrupt_captured

    @property
    def mode(self) -> int:
        return self.porta.mode | (self.portb.mode << 8)

    @mode.setter
    def mode(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.mode = val
        self.portb.mode = val >> 8

    @property
    def input_polarity(self) -> int:
        return self.porta.input_polarity | (self.portb.input_polarity << 8)

    @input_polarity.setter
    def input_polarity(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.input_polarity = val
        self.portb.input_polarity = val >> 8

    @property
    def interrupt_enable(self) -> int:
        return self.porta.interrupt_enable | (self.portb.interrupt_enable << 8)

    @interrupt_enable.setter
    def interrupt_enable(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.interrupt_enable = val
        self.portb.interrupt_enable = val >> 8

    @property
    def default_value(self) -> int:
        return self.porta.default_value | (self.portb.default_value << 8)

    @default_value.setter
    def default_value(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.default_value = val
        self.portb.default_value = val >> 8

    @property
    def interrupt_compare_default(self) -> int:
        return self.porta.interrupt_compare_default | (self.portb.interrupt_compare_default << 8)

    @interrupt_compare_default.setter
    def interrupt_compare_default(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.interrupt_compare_default = val
        self.portb.interrupt_compare_default = val >> 8

    @property
    def io_config(self) -> int:
        return self.porta.io_config

    @io_config.setter
    def io_config(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 255:
            raise ValueError(f"val must be 0-255, got {val}")
        self.porta.io_config = val

    @property
    def pullup(self) -> int:
        return self.porta.pullup | (self.portb.pullup << 8)

    @pullup.setter
    def pullup(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.pullup = val
        self.portb.pullup = val >> 8

    @property
    def interrupt_flag(self) -> int:
        return self.porta.interrupt_flag | (self.portb.interrupt_flag << 8)

    @property
    def interrupt_captured(self) -> int:
        return self.porta.interrupt_captured | (self.portb.interrupt_captured << 8)

    @property
    def gpio(self) -> int:
        return self.porta.gpio | (self.portb.gpio << 8)

    @gpio.setter
    def gpio(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.gpio = val
        self.portb.gpio = val >> 8

    @property
    def output_latch(self) -> int:
        return self.porta.output_latch | (self.portb.output_latch << 8)

    @output_latch.setter
    def output_latch(self, val: int) -> None:
        if val is None:
            raise ValueError("val cannot be None")
        if not isinstance(val, int):
            raise TypeError(f"val must be int, got {type(val).__name__}")
        if val < 0 or val > 65535:
            raise ValueError(f"val must be 0-65535, got {val}")
        self.porta.output_latch = val
        self.portb.output_latch = val >> 8

    def __getitem__(self, pin: int) -> "VirtualPin":
        """
        以列表形式访问引脚，返回虚拟引脚对象

        Args:
            pin (int): 引脚号0~15

        Returns:
            VirtualPin: 虚拟引脚对象

        Raises:
            ValueError: pin为None
            TypeError: pin不是整数
            ValueError: pin超出0-15范围

        Notes:
            缓存已创建的虚拟引脚

        ==========================================
        Access pin like a list, return VirtualPin

        Args:
            pin (int): Pin number 0~15

        Returns:
            VirtualPin: Virtual pin object

        Raises:
            ValueError: pin is None
            TypeError: pin is not int
            ValueError: pin out of range 0-15

        Notes:
            Cache created virtual pins
        """
        if pin is None:
            raise ValueError("pin cannot be None")
        if not isinstance(pin, int):
            raise TypeError(f"pin must be int, got {type(pin).__name__}")
        if pin < 0 or pin > 15:
            raise ValueError(f"pin must be 0-15, got {pin}")

        if not pin in self._virtual_pins:
            self._virtual_pins[pin] = VirtualPin(pin, self.portb if pin // 8 else self.porta)
        return self._virtual_pins[pin]


class VirtualPin:
    """
    虚拟引脚类，用于单引脚独立控制

    Attributes:
        _pin (int): 端口内引脚号0~7
        _bit (int): 位掩码
        _port (Port): 所属端口对象

    Methods:
        __init__(pin, port): 构造函数，创建虚拟引脚
        __call__(): 对象调用时返回引脚值
        value(val): 读写引脚电平
        input(pull): 设置为输入，可选上拉
        output(val): 设置为输出，可选输出电平

    Notes:
        方便像控制内置GPIO一样控制扩展引脚

    ==========================================
    Virtual pin class for single pin control

    Attributes:
        _pin (int): Pin number in port 0~7
        _bit (int): Bit mask
        _port (Port): Parent port object

    Methods:
        __init__(pin, port): Constructor, create virtual pin
        __call__(): Return pin value when called
        value(val): Read/write pin level
        input(pull): Set as input, optional pullup
        output(val): Set as output, optional output level

    Notes:
        Control expander pin like native GPIO
    """

    def __init__(self, pin: int, port: Port) -> None:
        """
        构造函数，创建虚拟引脚

        Args:
            pin (int): 全局引脚号0~15
            port (Port): 所属端口

        Raises:
            ValueError: pin或port为None
            TypeError: pin不是整数或port不是Port实例
            ValueError: pin超出0-15范围

        Notes:
            计算位掩码与端口内引脚号

        ==========================================
        Constructor, create virtual pin

        Args:
            pin (int): Global pin 0~15
            port (Port): Parent port

        Raises:
            ValueError: pin or port is None
            TypeError: pin is not int or port is not Port instance
            ValueError: pin out of range 0-15

        Notes:
            Calc bit mask and local pin
        """
        if pin is None:
            raise ValueError("pin cannot be None")
        if not isinstance(pin, int):
            raise TypeError(f"pin must be int, got {type(pin).__name__}")
        if pin < 0 or pin > 15:
            raise ValueError(f"pin must be 0-15, got {pin}")
        if port is None:
            raise ValueError("port cannot be None")
        if not isinstance(port, Port):
            raise TypeError(f"port must be Port instance, got {type(port).__name__}")

        self._pin = pin % 8
        self._bit = 1 << self._pin
        self._port = port

    def __call__(self) -> int:
        """
        对象调用时返回引脚值

        Returns:
            int: 引脚电平（0或1）

        Notes:
            简化使用方式

        ==========================================
        Return pin value when called

        Returns:
            int: Pin level (0 or 1)

        Notes:
            Simplify usage
        """
        return self.value()

    def _flip_bit(self, value: int, condition: int) -> int:
        """
        翻转本引脚对应位

        Args:
            value (int): 原始值
            condition (int): True置1，False置0

        Returns:
            int: 新值

        Raises:
            ValueError: 参数为None
            TypeError: 参数类型错误
            ValueError: value超出0-255范围

        Notes:
            内部工具

        ==========================================
        Flip bit for this pin

        Args:
            value (int): Original value
            condition (bool): True=set 1

        Returns:
            int: New value

        Raises:
            ValueError: Parameter is None
            TypeError: Parameter type error
            ValueError: value out of range 0-255

        Notes:
            Internal helper
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if value < 0 or value > 255:
            raise ValueError(f"value must be 0-255, got {value}")
        if condition is None:
            raise ValueError("condition cannot be None")
        if not isinstance(condition, int):
            raise TypeError(f"condition must be int, got {type(condition).__name__}")

        return value | self._bit if condition else value & ~self._bit

    def _get_bit(self, value: int) -> int:
        """
        获取本引脚位状态

        Args:
            value (int): 寄存器值

        Returns:
            int: 0或1

        Raises:
            ValueError: value为None
            TypeError: value不是整数
            ValueError: value超出0-255范围

        Notes:
            内部工具

        ==========================================
        Get this pin bit state

        Args:
            value (int): Register value

        Returns:
            int: 0 or 1

        Raises:
            ValueError: value is None
            TypeError: value is not int
            ValueError: value out of range 0-255

        Notes:
            Internal helper
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if value < 0 or value > 255:
            raise ValueError(f"value must be 0-255, got {value}")

        return (value & self._bit) >> self._pin

    def value(self, val: int = None) -> int | None:
        """
        读写引脚电平

        Args:
            val (int, optional): 输出电平，None为读取

        Returns:
            int | None: 读取时返回电平（0或1），写入时返回None

        Raises:
            ValueError: val不是0或1（若非None）
            TypeError: val不是整数（若非None）

        Notes:
            输出模式下修改OLAT

        ==========================================
        Read/write pin level

        Args:
            val (int, optional): Output level, None=read

        Returns:
            int | None: Level when reading (0 or 1), None when writing

        Raises:
            ValueError: val is not 0 or 1 (if not None)
            TypeError: val is not int (if not None)

        Notes:
            Modify OLAT in output mode
        """
        if val is not None:
            if not isinstance(val, int):
                raise TypeError(f"val must be int or None, got {type(val).__name__}")
            if val not in (0, 1):
                raise ValueError(f"val must be 0 or 1, got {val}")
            self._port.gpio = self._flip_bit(self._port.gpio, val & 1)
        else:
            return self._get_bit(self._port.gpio)

    def input(self, pull: int = None) -> None:
        """
        设置为输入模式，可选上拉

        Args:
            pull (int, optional): 上拉使能（0或1）

        Raises:
            TypeError: pull不是整数（若非None）
            ValueError: pull不是0或1（若非None）

        Notes:
            mode=输入

        ==========================================
        Set as input, optional pullup

        Args:
            pull (int, optional): Pullup enable (0 or 1)

        Raises:
            TypeError: pull is not int (if not None)
            ValueError: pull is not 0 or 1 (if not None)

        Notes:
            mode=input
        """
        if pull is not None:
            if not isinstance(pull, int):
                raise TypeError(f"pull must be int or None, got {type(pull).__name__}")
            if pull not in (0, 1):
                raise ValueError(f"pull must be 0 or 1, got {pull}")

        self._port.mode = self._flip_bit(self._port.mode, 1)
        if pull is not None:
            self._port.pullup = self._flip_bit(self._port.pullup, pull & 1)

    def output(self, val: int = None) -> None:
        """
        设置为输出模式，可选输出电平

        Args:
            val (int, optional): 输出电平（0或1）

        Raises:
            TypeError: val不是整数（若非None）
            ValueError: val不是0或1（若非None）

        Notes:
            mode=输出

        ==========================================
        Set as output, optional level

        Args:
            val (int, optional): Output level (0 or 1)

        Raises:
            TypeError: val is not int (if not None)
            ValueError: val is not 0 or 1 (if not None)

        Notes:
            mode=output
        """
        if val is not None:
            if not isinstance(val, int):
                raise TypeError(f"val must be int or None, got {type(val).__name__}")
            if val not in (0, 1):
                raise ValueError(f"val must be 0 or 1, got {val}")

        self._port.mode = self._flip_bit(self._port.mode, 0)
        if val is not None:
            self._port.gpio = self._flip_bit(self._port.gpio, val & 1)


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
