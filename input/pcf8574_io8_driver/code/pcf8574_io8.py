# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/23 下午5:44
# @Author  : 缪贵成
# @File    : pcf8574_io8.py
# @Description : 8位IO扩展模块读取电平测试驱动文件
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from pcf8574 import PCF8574

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class PCF8574IO8:
    """
    该类封装 PCF8574 8 位 IO 扩展器，提供端口级（2bit）和单引脚的输入/输出控制。

    Attributes:
        _pcf (PCF8574): 已实例化的 PCF8574 对象。
        _cache (int): 内部缓存的 8 位寄存器值，写操作时同步更新。
        _ports_default (dict): 存储每个 PORT（0..3）的默认状态，格式 {port: (bit1, bit0)}。

    Methods:
        configure_port(port: int, state: tuple[int, int]) -> None: 配置某个端口的默认状态并立即写入。
        set_port(port: int, value: int) -> None: 设置某个端口（2 位）的输出值。
        get_port(port: int) -> int: 读取端口当前电平值（返回 0..3）。
        set_pin(pin: int, value: int) -> None: 设置单个引脚电平（0=拉低，1=高阻）。
        get_pin(pin: int) -> int: 读取单个引脚电平（0/1）。
        read_all() -> int: 读取完整的 8 位输入状态。
        write_all(byte: int) -> None: 写入完整的 8 位输出值。
        refresh() -> None: 把缓存值写回设备。
        ports_state() -> dict: 返回所有端口的默认状态字典。
        deinit() -> None: 释放对象引用。

    Notes:
        - PCF8574 输出为准双向（开漏/高阻），写 1 = 高阻态，非推挽强高。
        - 读操作会临时将引脚置高阻，读完后恢复默认状态。
        - I2C 相关方法均非 ISR-safe，不可在中断服务中直接调用。

    ==========================================

    Wrapper class for PCF8574 8-bit IO expander. Supports port-level (2-bit)
    and single-pin operations with default state restore.

    Attributes:
        _pcf (PCF8574): Instance of PCF8574.
        _cache (int): Cached 8-bit register value.
        _ports_default (dict): Default states of each port.

    Methods:
        configure_port(...) -> None: Configure and apply default state of a port.
        set_port(...) -> None: Set output value of a port (2 bits).
        get_port(...) -> int: Read current level of a port.
        set_pin(...) -> None: Set single pin state.
        get_pin(...) -> int: Read single pin state.
        read_all() -> int: Read all 8 bits input state.
        write_all(byte) -> None: Write all 8 bits output state.
        refresh() -> None: Write cache to device.
        ports_state() -> dict: Return default states of all ports.
        deinit() -> None: Release references.

    Notes:
        - Outputs are quasi-bidirectional: writing 1 = high-Z, not strong high.
        - Read ops temporarily set pins high-Z then restore.
        - Methods performing I2C are not ISR-safe.
    """

    def __init__(self, pcf: PCF8574, ports_init: dict[int, tuple[int, int]] | None = None):
        """
        初始化驱动。

        Args:
            pcf (PCF8574): 已实例化的 PCF8574 对象。
            ports_init (dict): 初始配置，形如 {0:(a,b), 1:(c,d), ...}。
                               每个端口对应两位初始状态，0=拉低，1=高阻。可选。

        Raises:
            TypeError: 当 pcf 不是 PCF8574 实例时。

        Notes:
            初始化会根据 ports_init 配置端口，否则默认全部高阻态。
            调用会进行 I2C 写操作，非 ISR-safe。

        ==========================================

        Initialize driver.

        Args:
            pcf (PCF8574): Instance of PCF8574.
            ports_init (dict): Optional initial state {port: (bit1, bit0)}.

        Raises:
            TypeError: If pcf is not instance of PCF8574.

        Notes:
            Initializes with given states or defaults to high-Z.
            Not ISR-safe.
        """
        if not isinstance(pcf, PCF8574):
            raise TypeError("pcf must be an instance of PCF8574")
        self._pcf = pcf
        # 默认所有引脚高阻
        self._cache = 0xFF
        self._ports_default = {i: (1, 1) for i in range(4)}

        if ports_init:
            for port, state in ports_init.items():
                self.configure_port(port, state)
        else:
            self.refresh()

    def configure_port(self, port: int, state: tuple[int, int]):
        """
        配置某个 PORT 的默认状态，并立即写入。

        Args:
            port (int): 端口索引 0..3。
            state (tuple): (bit1, bit0)，每位 0=拉低，1=高阻。

        Raises:
            ValueError: 当端口参数和状态参数不合法时候。

        Notes:
            修改缓存并立即写入设备。
            非 ISR-safe。

        ==========================================

        Configure default state of a PORT.

        Args:
            port (int): Port index 0..3.
            state (tuple): (bit1, bit0), each bit 0=low, 1=high-Z.

        Raises:
            ValueError: When the port parameter and the status parameter are invalid.

        Notes:
            Updates cache and writes immediately.
            Not ISR-safe.
        """
        if port not in range(4):
            raise ValueError("port must be 0..3")
        if len(state) != 2 or any(bit not in (0, 1) for bit in state):
            raise ValueError("state must be (0/1, 0/1)")
        self._ports_default[port] = tuple(state)
        self._update_cache_port(port, state)
        self.refresh()

    def set_port(self, port: int, value: int):
        """
        设置指定端口（PORT0..PORT3）的两位输出值。

        Args:
            port (int): 端口索引 0..3。
            value (int): 两位值 0..3，映射到 (msb, lsb)。

        Raises:
            ValueError: 当 port 或 value 超出范围时。

        Notes:
            更新缓存并写回 PCF8574。
            写 1 = 高阻。

        ==========================================

        Set output value for given port.

        Args:
            port (int): Port index 0..3.
            value (int): 2-bit value 0..3.

        Raises:
            ValueError: If params out of range.

        Notes:
            Updates cache and writes back.
            Writing 1 = high-Z.
        """
        if port not in range(4):
            raise ValueError("port must be 0..3")
        if not (0 <= value <= 3):
            raise ValueError("value must be 0..3")
        state = (value >> 1 & 1, value & 1)
        self._update_cache_port(port, state)
        self.refresh()

    def get_port(self, port: int) -> int:
        """
        读取指定端口当前电平。

        Args:
            port (int): 端口索引 0..3。

        Returns:
            int: 返回 0..3。

        Raises:
            ValueError: 当 port 不在范围时。

        Notes:
            临时将端口置高阻以获取真实输入电平。
            读完后恢复默认状态。
            非 ISR-safe。

        ==========================================

        Read current level of port.

        Args:
            port (int): Port index 0..3.

        Returns:
            int: Value 0..3.

        Raises:
            ValueError: If port out of range.

        Notes:
            Temporarily set port high-Z to read input.
            Restores default state after read.
            Not ISR-safe.
        """
        if port not in range(4):
            raise ValueError("port must be 0..3")
        pins = [port * 2, port * 2 + 1]
        saved_state = [self._get_cache_bit(p) for p in pins]

        for p in pins:
            self._set_cache_bit(p, 1)
        self.refresh()
        value = self._pcf.port
        result = ((value >> pins[0]) & 1) << 1 | ((value >> pins[1]) & 1)

        for p, bit in zip(pins, saved_state):
            self._set_cache_bit(p, bit)
        self.refresh()
        return result

    def set_pin(self, pin: int, value: int):
        """
        设置单个引脚。

        Args:
            pin (int): 引脚索引 0..7。
            value (int): 0=拉低，1=高阻。

        Raises:
            ValueError: 当参数不合法时。

        Notes:
            修改缓存并写回。
            非 ISR-safe。

        ==========================================

        Set single pin.

        Args:
            pin (int): Pin index 0..7.
            value (int): 0=low, 1=high-Z.

        Raises:
            ValueError: If invalid params.

        Notes:
            Updates cache and writes.
            Not ISR-safe.
        """
        if pin not in range(8):
            raise ValueError("pin must be 0..7")
        if value not in (0, 1):
            raise ValueError("value must be 0 or 1")
        self._set_cache_bit(pin, value)
        self.refresh()

    def get_pin(self, pin: int) -> int:
        """
        读取单个引脚电平。

        Args:
            pin (int): 引脚索引 0..7。

        Returns:
            int: 电平值 0 或 1。

        Raises:
            ValueError: 当 pin 超出范围时。

        Notes:
            临时释放该引脚为高阻，读取电平，再恢复。
            非 ISR-safe。

        ==========================================

        Read single pin level.

        Args:
            pin (int): Pin index 0..7.

        Returns:
            int: Level 0 or 1.

        Raises:
            ValueError: If pin out of range.

        Notes:
            Temporarily releases pin to high-Z for read, then restores.
            Not ISR-safe.
        """
        if pin not in range(8):
            raise ValueError("pin must be 0..7")
        saved = self._get_cache_bit(pin)
        self._set_cache_bit(pin, 1)
        self.refresh()
        value = self._pcf.port
        result = (value >> pin) & 1
        self._set_cache_bit(pin, saved)
        self.refresh()
        return result

    def read_all(self) -> int:
        """
        读取 PCF8574 的完整 8 位输入状态。

        Returns:
            int: 输入状态，0..255。

        Notes:
            读取前先将所有位设为高阻。
            读完后恢复缓存。
            非 ISR-safe。

        ==========================================

        Read all 8-bit input state.

        Returns:
            int: 0..255.

        Notes:
            Sets all pins high-Z before read.
            Restores cache after.
            Not ISR-safe.
        """
        saved = self._cache
        self._cache = 0xFF
        self.refresh()
        value = self._pcf.port
        self._cache = saved
        self.refresh()
        return value

    def write_all(self, byte: int):
        """
        写入整字节。

        Args:
            byte (int): 0..255。

        Raises:
            ValueError: 当 byte 超出范围时。

        Notes:
            覆盖缓存并写入设备。
            非 ISR-safe。

        ==========================================

        Write full byte.

        Args:
            byte (int): 0..255.

        Raises:
            ValueError: If byte out of range.

        Notes:
            Overwrites cache and writes.
            Not ISR-safe.
        """
        if not (0 <= byte <= 0xFF):
            raise ValueError("byte must be 0..255")
        self._cache = byte
        self.refresh()

    def refresh(self):
        """
        把缓存写回设备。

        Notes:
            同步缓存到硬件寄存器。
            非 ISR-safe。

        ==========================================

        Write cache to device.

        Notes:
            Syncs cache to hardware.
            Not ISR-safe.
        """
        self._pcf.port = self._cache

    def ports_state(self) -> dict[int, tuple[int, int]]:
        """
        返回当前缓存的每个端口默认状态。

        Returns:
            dict: {port: (bit1, bit0)}。

        Notes:
            仅返回缓存值，不访问硬件。

        ==========================================

        Return default states of all ports.

        Returns:
            dict: {port: (bit1, bit0)}.

        Notes:
            Returns cache only, no hardware access.
        """
        return dict(self._ports_default)

    def deinit(self):
        """
        释放资源。

        Notes:
            将 _pcf 设置为 None。
            非 ISR-safe。

        ==========================================

        Deinitialize.

        Notes:
            Set _pcf to None.
            Not ISR-safe.
        """
        self._pcf = None

    def _update_cache_port(self, port: int, state: tuple[int, int]):
        """
        更新缓存中某个 PORT 的两位状态。

        Args:
            port (int): 端口索引，范围 0..3。
            state (tuple[int, int]): 两位状态，(msb, lsb)，位值 0=拉低，1=高阻。

        Notes:
            - 内部方法，仅用于更新缓存。
            - 不直接写 I2C，仅修改缓存。

        ==========================================

        Update the cached 2-bit state of a given PORT.

        Args:
            port (int): Port index, range 0..3.
            state (tuple[int, int]): Two-bit state (msb, lsb).
                0 = drive low, 1 = release (high-Z).

        Notes:
            - Internal helper method.
            - Does not write to I2C, only updates cache.
        """
        pins = [port * 2, port * 2 + 1]
        for p, bit in zip(pins, state):
            self._set_cache_bit(p, bit)

    def _set_cache_bit(self, pin: int, value: int):
        """
        更新缓存的某一位。

        Args:
            pin (int): 引脚索引，范围 0..7。
            value (int): 位值，0=拉低，1=高阻。

        Notes:
            - 内部方法，仅更新缓存，不直接写 I2C。

        ==========================================

        Update a single bit in the cache.

        Args:
            pin (int): Pin index, range 0..7.
            value (int): Bit value, 0=drive low, 1=release (high-Z).

        Notes:
            - Internal helper method.
            - Does not perform I2C write.
        """
        if value:
            self._cache |= (1 << pin)
        else:
            self._cache &= ~(1 << pin)

    def _get_cache_bit(self, pin: int) -> int:
        """
        获取缓存的某一位。

        Args:
            pin (int): 引脚索引，范围 0..7。

        Returns:
            int: 缓存的位值（0 或 1）。

        Notes:
            - 内部方法，仅读取缓存，不进行 I2C 通信。

        ==========================================

        Get a single bit from the cache.

        Args:
            pin (int): Pin index, range 0..7.

        Returns:
            int: Cached bit value (0 or 1).

        Notes:
            - Internal helper method.
            - No I2C communication, only cache read.
        """
        return (self._cache >> pin) & 1

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
