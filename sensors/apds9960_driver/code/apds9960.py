# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : Rune Langøy
# @File    : APDS9960.py
# @Description : APDS9960 low-memory driver: ambient light, color (RGBC), and proximity sensing
# @License : MIT

__version__ = "1.0.0"
__author__ = "Rune Langøy"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from time import sleep

# ======================================== 全局变量 ============================================

# 全局 I2C 2 字节复用缓冲区，避免频繁内存分配
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================

# 本驱动暂无需要抽离的通用功能函数

# ======================================== 自定义类 ============================================


class I2CEX:
    """
    I2C 寄存器读写辅助基类，封装单字节和双字节的读写、位操作以及重试逻辑。
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        _reg_write_bit(): 修改寄存器指定位的值
        _write_byte(): 单字节写入寄存器
        _read_byte(): 单字节读取寄存器
        _write_2byte(): 双字节（小端）写入寄存器
        _read_2byte(): 双字节（小端）读取寄存器
        _log(): 条件日志输出
    Notes:
        - 本类作为基类使用，不单独实例化
        - 所有 I/O 操作均通过传入的 I2C 实例完成
        - 瞬态 I2C 错误自动重试（默认 2 次，间隔 5ms）
        - ISR-safe: 否
    ==========================================
    I2C register read/write helper base class providing byte/word operations,
    bit manipulation, and automatic retry.

    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug log toggle
    Methods:
        _reg_write_bit(): Modify a single bit in a register
        _write_byte(): Write a single byte to a register
        _read_byte(): Read a single byte from a register
        _write_2byte(): Write two bytes (little-endian) to a register
        _read_2byte(): Read two bytes (little-endian) from a register
        _log(): Conditional debug log output
    Notes:
        - This class is used as a base class, not instantiated directly
        - All I/O operations use the externally provided I2C instance
        - Transient I2C errors are automatically retried (default 2 times, 5ms apart)
        - ISR-safe: No
    """

    def __init__(self, i2c, address: int, debug: bool = False) -> None:
        """
        初始化 I2C 辅助基类
        Args:
            i2c (I2C): I2C 总线实例（须具备 readfrom_mem / writeto_mem 协议方法）
            address (int): 设备 I2C 地址
            debug (bool): 是否输出调试日志，默认 False
        Raises:
            ValueError: i2c 参数不是合法的 I2C 实例，或 address 不是 int
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize I2C helper base class.

        Args:
            i2c (I2C): I2C bus instance (must support readfrom_mem / writeto_mem)
            address (int): Device I2C address
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: If i2c is not a valid I2C instance, or address is not int
        Notes:
            - ISR-safe: No
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if not isinstance(address, int) or not 0 <= address <= 0x7F:
            raise ValueError("address must be an I2C address from 0x00 to 0x7F")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        # 参数校验：i2c 必须具有 I2C 协议方法
        if hasattr(i2c, "readfrom_mem") is False:
            raise ValueError("i2c must be an I2C instance with readfrom_mem, got %s" % type(i2c))
        # 参数校验：address 必须是 int
        if isinstance(address, int) is False:
            raise ValueError("address must be int, got %s" % type(address))
        self._i2c = i2c
        self._address = address
        self._debug = debug

    def _log(self, msg: str) -> None:
        """
        条件调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - ISR-safe: 否
        ==========================================
        Conditional debug log output.
        Args:
            msg (str): Log message
        Notes:
            - ISR-safe: No
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[I2CEX] %s" % msg)

    def _reg_write_bit(self, reg: int, bit_pos: int, bit_val: bool, retries: int = 2, delay_ms: int = 5) -> None:
        """
        读取寄存器值、修改指定位、写回寄存器
        Args:
            reg (int): 寄存器地址
            bit_pos (int): 位位置（0-7）
            bit_val (bool): True 置位，False 清零
            retries (int): I2C 操作重试次数，默认 2
            delay_ms (int): 重试间隔（毫秒），默认 5
        Raises:
            ValueError: bit_pos 超出 0-7 范围
            RuntimeError: I2C 通信失败（重试耗尽）
        Side Effects:
            - 修改硬件寄存器
        Notes:
            - ISR-safe: 否
        ==========================================
        Read register, modify a single bit, write back.

        Args:
            reg (int): Register address
            bit_pos (int): Bit position (0-7)
            bit_val (bool): True to set bit, False to clear
            retries (int): I2C retry count, default 2
            delay_ms (int): Retry interval in ms, default 5
        Raises:
            ValueError: bit_pos out of 0-7 range
            RuntimeError: I2C communication failed (retries exhausted)
        Side Effects:
            - Modifies hardware register
        Notes:
            - ISR-safe: No
        """
        # 参数校验：位位置范围
        if bit_pos < 0 or bit_pos > 7:
            raise ValueError("bit_pos must be 0~7, got %d" % bit_pos)
        # 读取当前寄存器值
        val = self._read_byte(reg, retries=retries, delay_ms=delay_ms)
        # 根据 bit_val 置位或清零
        if bit_val:
            val = val | (1 << bit_pos)
        else:
            val = val & ~(1 << bit_pos)
        # 写回寄存器
        self._write_byte(reg, val, retries=retries, delay_ms=delay_ms)

    def _write_byte(self, reg: int, val: int, retries: int = 2, delay_ms: int = 5) -> None:
        """
        向 I2C 寄存器写入单字节
        Args:
            reg (int): 寄存器地址
            val (int): 写入值（0-255）
            retries (int): 重试次数，默认 2
            delay_ms (int): 重试间隔（毫秒），默认 5
        Raises:
            ValueError: val 超出 0-255 范围
            RuntimeError: I2C 通信失败（重试耗尽）
        Side Effects:
            - 修改硬件寄存器
        Notes:
            - ISR-safe: 否
        ==========================================
        Write a single byte to an I2C register.

        Args:
            reg (int): Register address
            val (int): Value to write (0-255)
            retries (int): Retry count, default 2
            delay_ms (int): Retry interval in ms, default 5
        Raises:
            ValueError: val out of 0-255 range
            RuntimeError: I2C communication failed (retries exhausted)
        Side Effects:
            - Modifies hardware register
        Notes:
            - ISR-safe: No
        """
        # 参数校验：值范围
        if val < 0 or val > 255:
            raise ValueError("val must be 0~255, got %d" % val)
        # I2C 写操作（含重试）
        for attempt in range(retries + 1):
            try:
                self._i2c.writeto_mem(self._address, reg, bytes((val,)))
                return
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (reg, retries)) from e
                sleep(delay_ms / 1000.0)

    def _read_byte(self, reg: int, retries: int = 2, delay_ms: int = 5) -> int:
        """
        从 I2C 寄存器读取单字节
        Args:
            reg (int): 寄存器地址
            retries (int): 重试次数，默认 2
            delay_ms (int): 重试间隔（毫秒），默认 5
        Returns:
            int: 寄存器值（0-255）
        Raises:
            RuntimeError: I2C 通信失败（重试耗尽）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read a single byte from an I2C register.

        Args:
            reg (int): Register address
            retries (int): Retry count, default 2
            delay_ms (int): Retry interval in ms, default 5
        Returns:
            int: Register value (0-255)
        Raises:
            RuntimeError: I2C communication failed (retries exhausted)
        Notes:
            - ISR-safe: No
        """
        # I2C 读操作（含重试）
        for attempt in range(retries + 1):
            try:
                val = self._i2c.readfrom_mem(self._address, reg, 1)
                return int.from_bytes(val, "big", False)
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (reg, retries)) from e
                sleep(delay_ms / 1000.0)

    def _write_2byte(self, reg: int, val: int, retries: int = 2, delay_ms: int = 5) -> None:
        """
        向 I2C 寄存器写入双字节（小端序）
        Args:
            reg (int): 寄存器地址
            val (int): 写入值（0-65535）
            retries (int): 重试次数，默认 2
            delay_ms (int): 重试间隔（毫秒），默认 5
        Raises:
            ValueError: val 超出 0-65535 范围
            RuntimeError: I2C 通信失败（重试耗尽）
        Side Effects:
            - 修改硬件寄存器
        Notes:
            - ISR-safe: 否
        ==========================================
        Write two bytes (little-endian) to an I2C register.

        Args:
            reg (int): Register address
            val (int): Value to write (0-65535)
            retries (int): Retry count, default 2
            delay_ms (int): Retry interval in ms, default 5
        Raises:
            ValueError: val out of 0-65535 range
            RuntimeError: I2C communication failed (retries exhausted)
        Side Effects:
            - Modifies hardware register
        Notes:
            - ISR-safe: No
        """
        # 参数校验：双字节值范围
        if val < 0 or val > 65535:
            raise ValueError("val must be 0~65535, got %d" % val)
        # 使用全局复用缓冲区，小端序填充
        _BUF2[0] = val & 0xFF
        _BUF2[1] = (val >> 8) & 0xFF
        # I2C 写操作（含重试）
        for attempt in range(retries + 1):
            try:
                self._i2c.writeto_mem(self._address, reg, _BUF2)
                return
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (reg, retries)) from e
                sleep(delay_ms / 1000.0)

    def _read_2byte(self, reg: int, retries: int = 2, delay_ms: int = 5) -> int:
        """
        从 I2C 寄存器读取双字节（小端序）
        Args:
            reg (int): 寄存器地址
            retries (int): 重试次数，默认 2
            delay_ms (int): 重试间隔（毫秒），默认 5
        Returns:
            int: 寄存器值（0-65535）
        Raises:
            RuntimeError: I2C 通信失败（重试耗尽）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read two bytes (little-endian) from an I2C register.

        Args:
            reg (int): Register address
            retries (int): Retry count, default 2
            delay_ms (int): Retry interval in ms, default 5
        Returns:
            int: Register value (0-65535)
        Raises:
            RuntimeError: I2C communication failed (retries exhausted)
        Notes:
            - ISR-safe: No
        """
        # I2C 读操作（含重试）
        for attempt in range(retries + 1):
            try:
                val = self._i2c.readfrom_mem(self._address, reg, 2)
                return int.from_bytes(val, "little", False)
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (reg, retries)) from e
                sleep(delay_ms / 1000.0)


class ALS(I2CEX):
    """
    APDS9960 环境光（ALS）和颜色（RGBC）传感功能类
    Attributes:
        _i2c (I2C): I2C 总线实例（继承自 I2CEX）
    Methods:
        enableSensor(): 启用/禁用光传感器
        setInterruptThreshold(): 设置光照中断阈值
        clearInterrupt(): 清除光照中断
        enableInterrupt(): 启用/禁用光照硬件中断
    Properties:
        eLightGain: 光传感器增益（0-3）
        ambientLightLevel: 环境光强度（0-1025）
        redLightLevel: 红光分量（0-1025）
        greenLightLevel: 绿光分量（0-1025）
        blueLightLevel: 蓝光分量（0-1025）
    Notes:
        - 依赖外部传入的 I2C 实例
        - ISR-safe: 否
    ==========================================
    APDS9960 Ambient Light Sense (ALS) and Color Sense (RGBC) driver.

    Attributes:
        _i2c (I2C): I2C bus instance (inherited from I2CEX)
    Methods:
        enableSensor(): Enable/disable light sensor
        setInterruptThreshold(): Set light interrupt thresholds
        clearInterrupt(): Clear light interrupt
        enableInterrupt(): Enable/disable light hardware interrupt
    Properties:
        eLightGain: Light sensor gain (0-3)
        ambientLightLevel: Ambient light level (0-1025)
        redLightLevel: Red light component (0-1025)
        greenLightLevel: Green light component (0-1025)
        blueLightLevel: Blue light component (0-1025)
    Notes:
        - Requires externally provided I2C instance
        - ISR-safe: No
    """

    # 类级常量 - I2C 地址
    _ADDR = 0x39

    # 类级常量 - 寄存器地址
    _REG_ENABLE = 0x80
    _REG_ATIME = 0x81
    _REG_AILTL = 0x84
    _REG_AILTH = 0x85
    _REG_AIHTL = 0x86
    _REG_AIHTH = 0x87
    _REG_PERS = 0x8C
    _REG_CONTROL = 0x8F
    _REG_CDATAL = 0x94
    _REG_RDATAL = 0x96
    _REG_GDATAL = 0x98
    _REG_BDATAL = 0x9A
    _REG_AICLEAR = 0xE6

    # 类级常量 - 位定义
    _BIT_AEN = 1
    _BIT_AIEN = 4

    # 类级常量 - ALS 增益选项
    GAIN_1X = 0
    GAIN_2X = 1
    GAIN_16X = 2
    GAIN_64X = 3

    def __init__(self, i2c, debug: bool = False) -> None:
        """
        初始化 ALS 光传感器功能类
        Args:
            i2c (I2C): I2C 总线实例（须具备 readfrom_mem / writeto_mem 方法）
            debug (bool): 是否输出调试日志，默认 False
        Raises:
            ValueError: i2c 不是合法的 I2C 实例
        Notes:
            - 设备 I2C 地址固定为 0x39
            - ISR-safe: 否
        ==========================================
        Initialize ALS ambient light sensor class.

        Args:
            i2c (I2C): I2C bus instance (must support readfrom_mem / writeto_mem)
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: If i2c is not a valid I2C instance
        Notes:
            - Device I2C address is fixed at 0x39
            - ISR-safe: No
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        super().__init__(i2c, self._ADDR, debug)

    def enableSensor(self, on: bool = True) -> None:
        """
        启用或禁用光传感器
        Args:
            on (bool): True 启用，False 禁用，默认 True
        Raises:
            ValueError: on 不是 bool 类型
        Side Effects:
            - 修改 ENABLE 寄存器的 AEN 位
        Notes:
            - ISR-safe: 否
        ==========================================
        Enable or disable the light sensor.

        Args:
            on (bool): True to enable, False to disable, default True
        Raises:
            ValueError: If on is not bool type
        Side Effects:
            - Modifies the AEN bit in the ENABLE register
        Notes:
            - ISR-safe: No
        """
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool")
        # 参数校验：on 必须是 bool
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool, got %s" % type(on))
        # 设置 ENABLE 寄存器中的 ALS 使能位（bit 1）
        self._reg_write_bit(self._REG_ENABLE, self._BIT_AEN, on)

    @property
    def eLightGain(self) -> int:
        """
        获取/设置光传感器接收增益
        Getter:
            Returns: 当前增益值（0=1x, 1=2x, 2=16x, 3=64x）
        Setter:
            Args: eGain (int): 增益值（0-3）
            Raises: ValueError: eGain 不是 int 或超出范围
        Side Effects:
            - Setter 修改 CONTROL 寄存器的低 2 位
        Notes:
            - ISR-safe: 否
        ==========================================
        Get/set the receiver gain for light measurements.

        Getter:
            Returns: Current gain value (0=1x, 1=2x, 2=16x, 3=64x)
        Setter:
            Args: eGain (int): Gain value (0-3)
            Raises: ValueError: If eGain is not int or out of range
        Side Effects:
            - Setter modifies the lower 2 bits of the CONTROL register
        Notes:
            - ISR-safe: No
        """
        # 读取 CONTROL 寄存器，提取低 2 位增益值
        val = self._read_byte(self._REG_CONTROL)
        val = val & 0b00000011
        return val

    @eLightGain.setter
    def eLightGain(self, eGain: int) -> None:
        """设置光传感器增益。Set the ambient-light sensor gain.

        Raises: ValueError: 增益不是 0 至 3 的整数。Raised when gain is not an integer from 0 to 3.
        Notes: 修改控制寄存器。Updates the control register.
        """
        # 参数校验：eGain 必须是 int 类型
        if isinstance(eGain, int) is False:
            raise ValueError("eGain must be int, got %s" % type(eGain))
        # 参数校验：eGain 范围 0-3
        if eGain < 0 or eGain > 3:
            raise ValueError("eGain must be 0~3, got %d" % eGain)
        # 读取 CONTROL 寄存器当前值
        val = self._read_byte(self._REG_CONTROL)
        # 清除低 2 位，写入新增益值
        eGain &= 0b00000011
        val &= 0b11111100
        val |= eGain
        # 写回 CONTROL 寄存器
        self._write_byte(self._REG_CONTROL, val)

    @property
    def ambientLightLevel(self) -> int:
        """
        读取环境光强度（Clear 通道数据）
        Returns:
            int: 环境光强度（0-1025）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 返回 CDATAL 和 CDATAH 组合的 16 位值
            - ISR-safe: 否
        ==========================================
        Read ambient light level (Clear channel data).

        Returns:
            int: Ambient light level (0-1025)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Returns 16-bit value from CDATAL + CDATAH registers
            - ISR-safe: No
        """
        return self._read_2byte(self._REG_CDATAL)

    @property
    def redLightLevel(self) -> int:
        """
        读取红光分量（Red 通道数据）
        Returns:
            int: 红光分量（0-1025）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 返回 RDATAL 和 RDATAH 组合的 16 位值
            - ISR-safe: 否
        ==========================================
        Read red light level (Red channel data).

        Returns:
            int: Red light level (0-1025)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Returns 16-bit value from RDATAL + RDATAH registers
            - ISR-safe: No
        """
        return self._read_2byte(self._REG_RDATAL)

    @property
    def greenLightLevel(self) -> int:
        """
        读取绿光分量（Green 通道数据）
        Returns:
            int: 绿光分量（0-1025）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 返回 GDATAL 和 GDATAH 组合的 16 位值
            - ISR-safe: 否
        ==========================================
        Read green light level (Green channel data).

        Returns:
            int: Green light level (0-1025)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Returns 16-bit value from GDATAL + GDATAH registers
            - ISR-safe: No
        """
        return self._read_2byte(self._REG_GDATAL)

    @property
    def blueLightLevel(self) -> int:
        """
        读取蓝光分量（Blue 通道数据）
        Returns:
            int: 蓝光分量（0-1025）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 返回 BDATAL 和 BDATAH 组合的 16 位值
            - ISR-safe: 否
        ==========================================
        Read blue light level (Blue channel data).

        Returns:
            int: Blue light level (0-1025)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Returns 16-bit value from BDATAL + BDATAH registers
            - ISR-safe: No
        """
        return self._read_2byte(self._REG_BDATAL)

    def setInterruptThreshold(self, high: int = 0, low: int = 20, persistance: int = 4) -> None:
        """
        设置光照中断阈值和持续次数
        Args:
            high (int): 中断高阈值（0-1025），默认 0
            low (int): 中断低阈值（0-1025），默认 20
            persistance (int): 连续触发次数（0-7），超过 7 自动截断为 7，默认 4
        Raises:
            ValueError: 参数类型或范围错误
        Side Effects:
            - 修改 AILT、AIHT、PERS 寄存器
        Notes:
            - ISR-safe: 否
        ==========================================
        Set light interrupt thresholds and persistence.

        Args:
            high (int): Interrupt high threshold (0-1025), default 0
            low (int): Interrupt low threshold (0-1025), default 20
            persistance (int): Consecutive trigger count (0-7), capped at 7, default 4
        Raises:
            ValueError: If parameter type or range is invalid
        Side Effects:
            - Modifies AILT, AIHT, and PERS registers
        Notes:
            - ISR-safe: No
        """
        # 参数校验：类型检查
        if isinstance(high, int) is False:
            raise ValueError("high must be int, got %s" % type(high))
        if isinstance(low, int) is False:
            raise ValueError("low must be int, got %s" % type(low))
        if isinstance(persistance, int) is False:
            raise ValueError("persistance must be int, got %s" % type(persistance))
        # 参数校验：阈值范围
        if high < 0 or high > 1025:
            raise ValueError("high must be 0~1025, got %d" % high)
        if low < 0 or low > 1025:
            raise ValueError("low must be 0~1025, got %d" % low)
        # 持续次数截断到 7
        if persistance > 7:
            persistance = 7
        if persistance < 0:
            persistance = 0
        # 设置 ALS 低阈值和高阈值（双字节写入）
        self._write_2byte(self._REG_AILTL, low)
        self._write_2byte(self._REG_AIHTL, high)
        # 修改 PERS 寄存器的低 4 位（APERS），保留高 4 位（PPERS）
        val = self._read_byte(self._REG_PERS)
        val = val & 0b11111000
        val = val | persistance
        self._write_byte(self._REG_PERS, val)

    def clearInterrupt(self) -> None:
        """
        清除光照中断标志
        Side Effects:
            - 读取 AICLEAR 寄存器，使 IRQ HW 输出拉低
        Notes:
            - 必须在中断处理中调用以允许新的中断触发
            - ISR-safe: 否
        ==========================================
        Clear the light interrupt flag.

        Side Effects:
            - Reads the AICLEAR register, pulling IRQ HW output low
        Notes:
            - Must be called in interrupt handler to allow new interrupts
            - ISR-safe: No
        """
        # 读取 AICLEAR 寄存器清除所有非手势中断
        self._read_byte(self._REG_AICLEAR)

    def enableInterrupt(self, on: bool = True) -> None:
        """
        启用或禁用光照硬件中断
        Args:
            on (bool): True 启用，False 禁用，默认 True
        Raises:
            ValueError: on 不是 bool 类型
        Side Effects:
            - 修改 ENABLE 寄存器的 AIEN 位
            - 调用 clearInterrupt() 清除挂起的中断
        Notes:
            - 中断阈值通过 setInterruptThreshold() 设定
            - ISR-safe: 否
        ==========================================
        Enable or disable light hardware interrupt.

        Args:
            on (bool): True to enable, False to disable, default True
        Raises:
            ValueError: If on is not bool type
        Side Effects:
            - Modifies the AIEN bit in the ENABLE register
            - Calls clearInterrupt() to clear pending interrupts
        Notes:
            - Interrupt thresholds are set via setInterruptThreshold()
            - ISR-safe: No
        """
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool")
        # 参数校验
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool, got %s" % type(on))
        # 设置 ENABLE 寄存器中的 ALS 中断使能位（bit 4）
        self._reg_write_bit(self._REG_ENABLE, self._BIT_AIEN, on)
        # 清除挂起的中断
        self.clearInterrupt()

    def deinit(self) -> None:
        """
        释放 ALS 资源
        Side Effects:
            - 禁用光传感器
        Notes:
            - ISR-safe: 否
        ==========================================
        Release ALS resources.

        Side Effects:
            - Disables the light sensor
        Notes:
            - ISR-safe: No
        """
        # 禁用光传感器
        self.enableSensor(False)


class PROX(I2CEX):
    """
    APDS9960 接近检测功能类
    Attributes:
        _i2c (I2C): I2C 总线实例（继承自 I2CEX）
    Methods:
        enableSensor(): 启用/禁用接近传感器
        setInterruptThreshold(): 设置接近中断阈值
        clearInterrupt(): 清除接近中断
        enableInterrupt(): 启用/禁用接近硬件中断
    Properties:
        eProximityGain: 接近检测增益（0-3）
        eLEDCurrent: LED 驱动电流（0-3）
        proximityLevel: 接近检测值（0-255）
    Notes:
        - 依赖外部传入的 I2C 实例
        - ISR-safe: 否
    ==========================================
    APDS9960 proximity detection driver.

    Attributes:
        _i2c (I2C): I2C bus instance (inherited from I2CEX)
    Methods:
        enableSensor(): Enable/disable proximity sensor
        setInterruptThreshold(): Set proximity interrupt thresholds
        clearInterrupt(): Clear proximity interrupt
        enableInterrupt(): Enable/disable proximity hardware interrupt
    Properties:
        eProximityGain: Proximity detection gain (0-3)
        eLEDCurrent: LED drive current (0-3)
        proximityLevel: Proximity detection value (0-255)
    Notes:
        - Requires externally provided I2C instance
        - ISR-safe: No
    """

    # 类级常量 - I2C 地址
    _ADDR = 0x39

    # 类级常量 - 寄存器地址
    _REG_ENABLE = 0x80
    _REG_PILT = 0x89
    _REG_PIHT = 0x8B
    _REG_PERS = 0x8C
    _REG_CONTROL = 0x8F
    _REG_PDATA = 0x9C
    _REG_PICLEAR = 0xE5
    _REG_AICLEAR = 0xE7

    # 类级常量 - 位定义
    _BIT_PEN = 2
    _BIT_PIEN = 5

    # 类级常量 - 接近增益选项
    PGAIN_1X = 0
    PGAIN_2X = 1
    PGAIN_4X = 2
    PGAIN_8X = 3

    # 类级常量 - LED 电流选项
    LED_100MA = 0
    LED_50MA = 1
    LED_25MA = 2
    LED_12_5MA = 3

    def __init__(self, i2c, debug: bool = False) -> None:
        """
        初始化接近传感器功能类
        Args:
            i2c (I2C): I2C 总线实例（须具备 readfrom_mem / writeto_mem 方法）
            debug (bool): 是否输出调试日志，默认 False
        Raises:
            ValueError: i2c 不是合法的 I2C 实例
        Notes:
            - 设备 I2C 地址固定为 0x39
            - ISR-safe: 否
        ==========================================
        Initialize proximity sensor class.

        Args:
            i2c (I2C): I2C bus instance (must support readfrom_mem / writeto_mem)
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: If i2c is not a valid I2C instance
        Notes:
            - Device I2C address is fixed at 0x39
            - ISR-safe: No
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        super().__init__(i2c, self._ADDR, debug)

    def enableSensor(self, on: bool = True) -> None:
        """
        启用或禁用接近传感器
        Args:
            on (bool): True 启用，False 禁用，默认 True
        Raises:
            ValueError: on 不是 bool 类型
        Side Effects:
            - 修改 ENABLE 寄存器的 PEN 位
        Notes:
            - ISR-safe: 否
        ==========================================
        Enable or disable the proximity sensor.

        Args:
            on (bool): True to enable, False to disable, default True
        Raises:
            ValueError: If on is not bool type
        Side Effects:
            - Modifies the PEN bit in the ENABLE register
        Notes:
            - ISR-safe: No
        """
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool")
        # 参数校验
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool, got %s" % type(on))
        # 设置 ENABLE 寄存器中的接近使能位（bit 2）
        self._reg_write_bit(self._REG_ENABLE, self._BIT_PEN, on)

    def setInterruptThreshold(self, high: int = 0, low: int = 20, persistance: int = 4) -> None:
        """
        设置接近中断阈值和持续次数
        Args:
            high (int): 中断高阈值（0-255），默认 0
            low (int): 中断低阈值（0-255），默认 20
            persistance (int): 连续触发次数（0-7），超过 7 自动截断为 7，默认 4
        Raises:
            ValueError: 参数类型或范围错误
        Side Effects:
            - 修改 PILT、PIHT、PERS 寄存器
        Notes:
            - ISR-safe: 否
        ==========================================
        Set proximity interrupt thresholds and persistence.

        Args:
            high (int): Interrupt high threshold (0-255), default 0
            low (int): Interrupt low threshold (0-255), default 20
            persistance (int): Consecutive trigger count (0-7), capped at 7, default 4
        Raises:
            ValueError: If parameter type or range is invalid
        Side Effects:
            - Modifies PILT, PIHT, and PERS registers
        Notes:
            - ISR-safe: No
        """
        # 参数校验：类型检查
        if isinstance(high, int) is False:
            raise ValueError("high must be int, got %s" % type(high))
        if isinstance(low, int) is False:
            raise ValueError("low must be int, got %s" % type(low))
        if isinstance(persistance, int) is False:
            raise ValueError("persistance must be int, got %s" % type(persistance))
        # 参数校验：阈值范围（单字节 0-255）
        if high < 0 or high > 255:
            raise ValueError("high must be 0~255, got %d" % high)
        if low < 0 or low > 255:
            raise ValueError("low must be 0~255, got %d" % low)
        # 持续次数截断到 7
        if persistance > 7:
            persistance = 7
        if persistance < 0:
            persistance = 0
        # 设置接近低阈值和高阈值（单字节写入）
        self._write_byte(self._REG_PILT, low)
        self._write_byte(self._REG_PIHT, high)
        # 修改 PERS 寄存器的高 4 位（PPERS），保留低 4 位（APERS）
        val = self._read_byte(self._REG_PERS)
        val = val & 0b00011111
        val = val | (persistance << 4)
        self._write_byte(self._REG_PERS, val)

    def clearInterrupt(self) -> None:
        """
        清除接近中断标志
        Side Effects:
            - 写入 0 到 AICLEAR 寄存器
            - 读取 PICLEAR 寄存器
            - 使 IRQ HW 输出拉低
        Notes:
            - 必须在中断处理中调用以允许新的中断触发
            - ISR-safe: 否
        ==========================================
        Clear the proximity interrupt flag.

        Side Effects:
            - Writes 0 to AICLEAR register
            - Reads PICLEAR register
            - Pulls IRQ HW output low
        Notes:
            - Must be called in interrupt handler to allow new interrupts
            - ISR-safe: No
        """
        # 写入 0 到 AICLEAR 清除所有中断
        self._write_byte(self._REG_AICLEAR, 0)
        # 读取 PICLEAR 清除接近中断
        self._read_byte(self._REG_PICLEAR)

    def enableInterrupt(self, on: bool = True) -> None:
        """
        启用或禁用接近硬件中断
        Args:
            on (bool): True 启用，False 禁用，默认 True
        Raises:
            ValueError: on 不是 bool 类型
        Side Effects:
            - 修改 ENABLE 寄存器的 PIEN 位
            - 调用 clearInterrupt() 清除挂起的中断
        Notes:
            - 中断阈值通过 setInterruptThreshold() 设定
            - ISR-safe: 否
        ==========================================
        Enable or disable proximity hardware interrupt.

        Args:
            on (bool): True to enable, False to disable, default True
        Raises:
            ValueError: If on is not bool type
        Side Effects:
            - Modifies the PIEN bit in the ENABLE register
            - Calls clearInterrupt() to clear pending interrupts
        Notes:
            - Interrupt thresholds are set via setInterruptThreshold()
            - ISR-safe: No
        """
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool")
        # 参数校验
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool, got %s" % type(on))
        # 设置 ENABLE 寄存器中的接近中断使能位（bit 5）
        self._reg_write_bit(self._REG_ENABLE, self._BIT_PIEN, on)
        # 清除挂起的中断
        self.clearInterrupt()

    @property
    def eProximityGain(self) -> int:
        """
        获取/设置接近检测接收增益
        Getter:
            Returns: 当前增益值（0=1x, 1=2x, 2=4x, 3=8x）
        Setter:
            Args: eGain (int): 增益值（0-3）
            Raises: ValueError: eGain 不是 int 或超出范围
        Side Effects:
            - Setter 修改 CONTROL 寄存器的位 2-3
        Notes:
            - ISR-safe: 否
        ==========================================
        Get/set the receiver gain for proximity detection.

        Getter:
            Returns: Current gain value (0=1x, 1=2x, 2=4x, 3=8x)
        Setter:
            Args: eGain (int): Gain value (0-3)
            Raises: ValueError: If eGain is not int or out of range
        Side Effects:
            - Setter modifies bits 2-3 of the CONTROL register
        Notes:
            - ISR-safe: No
        """
        # 读取 CONTROL 寄存器，提取位 2-3 的接近增益值
        val = self._read_byte(self._REG_CONTROL)
        val = (val >> 2) & 0b00000011
        return val

    @eProximityGain.setter
    def eProximityGain(self, eGain: int) -> None:
        """设置接近检测增益。Set the proximity sensor gain.

        Raises: ValueError: 增益不是 0 至 3 的整数。Raised when gain is not an integer from 0 to 3.
        Notes: 修改控制寄存器。Updates the control register.
        """
        # 参数校验：eGain 必须是 int 类型
        if isinstance(eGain, int) is False:
            raise ValueError("eGain must be int, got %s" % type(eGain))
        # 参数校验：eGain 范围 0-3
        if eGain < 0 or eGain > 3:
            raise ValueError("eGain must be 0~3, got %d" % eGain)
        # 读取 CONTROL 寄存器当前值
        val = self._read_byte(self._REG_CONTROL)
        # 清除位 2-3，写入新增益值
        eGain &= 0b00000011
        eGain = eGain << 2
        val &= 0b11110011
        val |= eGain
        # 写回 CONTROL 寄存器
        self._write_byte(self._REG_CONTROL, val)

    @property
    def eLEDCurrent(self) -> int:
        """
        获取/设置接近检测 LED 驱动电流
        Getter:
            Returns: 当前电流档位（0=100mA, 1=50mA, 2=25mA, 3=12.5mA）
        Setter:
            Args: eCurrent (int): 电流档位（0-3）
            Raises: ValueError: eCurrent 不是 int 或超出范围
        Side Effects:
            - Setter 修改 CONTROL 寄存器的位 6-7
        Notes:
            - ISR-safe: 否
        ==========================================
        Get/set LED drive current for proximity detection.

        Getter:
            Returns: Current level (0=100mA, 1=50mA, 2=25mA, 3=12.5mA)
        Setter:
            Args: eCurrent (int): Current level (0-3)
            Raises: ValueError: If eCurrent is not int or out of range
        Side Effects:
            - Setter modifies bits 6-7 of the CONTROL register
        Notes:
            - ISR-safe: No
        """
        # 读取 CONTROL 寄存器，提取位 6-7 的 LED 电流值
        val = self._read_byte(self._REG_CONTROL)
        val = val >> 6
        return val

    @eLEDCurrent.setter
    def eLEDCurrent(self, eCurrent: int) -> None:
        """设置接近检测 LED 电流。Set the proximity LED drive current.

        Raises: ValueError: 电流档位不是 0 至 3 的整数。Raised when the current setting is not an integer from 0 to 3.
        Notes: 修改控制寄存器。Updates the control register.
        """
        # 参数校验：eCurrent 必须是 int 类型
        if isinstance(eCurrent, int) is False:
            raise ValueError("eCurrent must be int, got %s" % type(eCurrent))
        # 参数校验：eCurrent 范围 0-3
        if eCurrent < 0 or eCurrent > 3:
            raise ValueError("eCurrent must be 0~3, got %d" % eCurrent)
        # 读取 CONTROL 寄存器当前值
        val = self._read_byte(self._REG_CONTROL)
        # 清除位 6-7，写入新电流值
        eCurrent &= 0b00000011
        eCurrent = eCurrent << 6
        val &= 0b00111111
        val |= eCurrent
        # 写回 CONTROL 寄存器
        self._write_byte(self._REG_CONTROL, val)

    @property
    def proximityLevel(self) -> int:
        """
        读取接近检测值
        Returns:
            int: 接近检测值（0-255）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 值越大表示物体越近
            - ISR-safe: 否
        ==========================================
        Read proximity detection value.

        Returns:
            int: Proximity value (0-255)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Higher values indicate closer objects
            - ISR-safe: No
        """
        return self._read_byte(self._REG_PDATA)

    def deinit(self) -> None:
        """
        释放接近传感器资源
        Side Effects:
            - 禁用接近传感器
        Notes:
            - ISR-safe: 否
        ==========================================
        Release proximity sensor resources.

        Side Effects:
            - Disables the proximity sensor
        Notes:
            - ISR-safe: No
        """
        # 禁用接近传感器
        self.enableSensor(False)


class APDS9960(I2CEX):
    """
    APDS9960 低内存占用驱动类，整合环境光、颜色和接近检测功能
    Attributes:
        prox (PROX): 接近检测功能实例
        als (ALS): 环境光/颜色检测功能实例
    Methods:
        powerOn(): 启用/禁用传感器电源
        deinit(): 释放所有资源
    Properties:
        statusRegister: 设备状态寄存器
    Notes:
        - 构造函数中执行芯片上电时序（先关后开）
        - prox 和 als 属性在 __init__ 中自动创建
        - 依赖外部传入的 I2C 实例
        - ISR-safe: 否
    ==========================================
    APDS9960 low-memory driver combining ALS, color, and proximity.

    Attributes:
        prox (PROX): Proximity sensor instance
        als (ALS): Ambient light / color sensor instance
    Methods:
        powerOn(): Enable/disable sensor power
        deinit(): Release all resources
    Properties:
        statusRegister: Device status register
    Notes:
        - Constructor performs chip power-on sequence (off then on)
        - prox and als attributes are auto-created in __init__
        - Requires externally provided I2C instance
        - ISR-safe: No
    """

    # 类级常量 - I2C 地址
    _ADDR = 0x39

    # 类级常量 - 寄存器地址
    _REG_ENABLE = 0x80
    _REG_STATUS = 0x93

    # 类级常量 - 位定义
    _BIT_PON = 0

    # 类级常量 - 上电时序延时（秒）
    _POWER_ON_DELAY = 0.05

    def __init__(self, i2c, debug: bool = False) -> None:
        """
        初始化 APDS9960 驱动
        Args:
            i2c (I2C): I2C 总线实例（须具备 readfrom_mem / writeto_mem 方法）
            debug (bool): 是否输出调试日志，默认 False
        Raises:
            ValueError: i2c 不是合法的 I2C 实例
        Side Effects:
            - 执行芯片上电时序（PON=0 → 延时 50ms → PON=1）
            - 创建 PROX 和 ALS 子功能实例
        Notes:
            - 设备 I2C 地址固定为 0x39
            - ISR-safe: 否
        ==========================================
        Initialize APDS9960 driver.

        Args:
            i2c (I2C): I2C bus instance (must support readfrom_mem / writeto_mem)
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: If i2c is not a valid I2C instance
        Side Effects:
            - Performs chip power-on sequence (PON=0 → 50ms delay → PON=1)
            - Creates PROX and ALS sub-instances
        Notes:
            - Device I2C address is fixed at 0x39
            - ISR-safe: No
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        super().__init__(i2c, self._ADDR, debug)
        # 芯片上电时序：先关闭电源
        self.powerOn(False)
        sleep(self._POWER_ON_DELAY)
        # 再开启电源
        self.powerOn(True)
        # 创建子功能模块实例
        self.prox = PROX(i2c, debug)
        self.als = ALS(i2c, debug)

    def powerOn(self, on: bool = True) -> None:
        """
        启用或禁用 APDS9960 传感器电源
        Args:
            on (bool): True 上电，False 掉电，默认 True
        Raises:
            ValueError: on 不是 bool 类型
        Side Effects:
            - 修改 ENABLE 寄存器的 PON 位
        Notes:
            - ISR-safe: 否
        ==========================================
        Enable or disable the APDS9960 sensor power.

        Args:
            on (bool): True to power on, False to power off, default True
        Raises:
            ValueError: If on is not bool type
        Side Effects:
            - Modifies the PON bit in the ENABLE register
        Notes:
            - ISR-safe: No
        """
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool")
        # 参数校验
        if isinstance(on, bool) is False:
            raise ValueError("on must be bool, got %s" % type(on))
        # 设置 ENABLE 寄存器中的电源使能位（bit 0）
        self._reg_write_bit(self._REG_ENABLE, self._BIT_PON, on)

    @property
    def statusRegister(self) -> int:
        """
        读取设备状态寄存器（0x93）
        Returns:
            int: 状态寄存器内容，各位含义如下：
                - Bit 7 CPSAT:  Clear 光电二极管饱和
                - Bit 6 PGSAT:  模拟饱和事件
                - Bit 5 PINT:   接近中断
                - Bit 4 AINT:   ALS 中断
                - Bit 3 DNC:    未使用
                - Bit 2 GINT:   手势中断
                - Bit 1 PVALID: 接近数据有效
                - Bit 0 AVALID: ALS 数据有效
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 只读寄存器，上电后初始值为 0x04
            - ISR-safe: 否
        ==========================================
        Read device status register (0x93).

        Returns:
            int: Status register contents, bit fields:
                - Bit 7 CPSAT:  Clear photodiode saturation
                - Bit 6 PGSAT:  Analog saturation event
                - Bit 5 PINT:   Proximity interrupt
                - Bit 4 AINT:   ALS interrupt
                - Bit 3 DNC:    Do not care
                - Bit 2 GINT:   Gesture interrupt
                - Bit 1 PVALID: Proximity data valid
                - Bit 0 AVALID: ALS data valid
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Read-only register, initialized to 0x04 at power-up
            - ISR-safe: No
        """
        return self._read_byte(self._REG_STATUS)

    def deinit(self) -> None:
        """
        释放所有传感器资源
        Side Effects:
            - 关闭传感器电源
            - 释放接近传感器
            - 释放光传感器
        Notes:
            - ISR-safe: 否
        ==========================================
        Release all sensor resources.

        Side Effects:
            - Powers off the sensor
            - Releases proximity sensor
            - Releases light sensor
        Notes:
            - ISR-safe: No
        """
        # 释放子功能模块
        if hasattr(self, "prox") and self.prox is not None:
            self.prox.deinit()
        if hasattr(self, "als") and self.als is not None:
            self.als.deinit()
        # 关闭传感器电源
        self.powerOn(False)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
