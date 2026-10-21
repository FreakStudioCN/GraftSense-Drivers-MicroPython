# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Tony DiCola, VynDragon, FreakStudio
# @File    : drv2605l.py
# @Description : TI DRV2605/DRV2605L 触觉反馈电机驱动芯片的I2C驱动类实现
# @License : MIT

__version__ = "1.0.0"
__author__ = "Tony DiCola, VynDragon, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

import time

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


# ======================================== 全局变量 ============================================

# DRV2605 默认 I2C 地址
_DRV2605_ADDR = const(0x5A)

# DRV2605 内部寄存器地址
_DRV2605_REG_STATUS = const(0x00)
_DRV2605_REG_MODE = const(0x01)
_DRV2605_REG_RTPIN = const(0x02)
_DRV2605_REG_LIBRARY = const(0x03)
_DRV2605_REG_WAVESEQ1 = const(0x04)
_DRV2605_REG_WAVESEQ2 = const(0x05)
_DRV2605_REG_WAVESEQ3 = const(0x06)
_DRV2605_REG_WAVESEQ4 = const(0x07)
_DRV2605_REG_WAVESEQ5 = const(0x08)
_DRV2605_REG_WAVESEQ6 = const(0x09)
_DRV2605_REG_WAVESEQ7 = const(0x0A)
_DRV2605_REG_WAVESEQ8 = const(0x0B)
_DRV2605_REG_GO = const(0x0C)
_DRV2605_REG_OVERDRIVE = const(0x0D)
_DRV2605_REG_SUSTAINPOS = const(0x0E)
_DRV2605_REG_SUSTAINNEG = const(0x0F)
_DRV2605_REG_BREAK = const(0x10)
_DRV2605_REG_AUDIOCTRL = const(0x11)
_DRV2605_REG_AUDIOLVL = const(0x12)
_DRV2605_REG_AUDIOMAX = const(0x13)
_DRV2605_REG_RATEDV = const(0x16)
_DRV2605_REG_CLAMPV = const(0x17)
_DRV2605_REG_AUTOCALCOMP = const(0x18)
_DRV2605_REG_AUTOCALEMP = const(0x19)
_DRV2605_REG_FEEDBACK = const(0x1A)
_DRV2605_REG_CONTROL1 = const(0x1B)
_DRV2605_REG_CONTROL2 = const(0x1C)
_DRV2605_REG_CONTROL3 = const(0x1D)
_DRV2605_REG_CONTROL4 = const(0x1E)
_DRV2605_REG_VBAT = const(0x21)
_DRV2605_REG_LRARESON = const(0x22)

# GO 寄存器位定义
_GO_BIT = const(0x01)

# 操作模式常量
MODE_INTTRIG = const(0x00)
MODE_EXTTRIGEDGE = const(0x01)
MODE_EXTTRIGLVL = const(0x02)
MODE_PWMANALOG = const(0x03)
MODE_AUDIOVIBE = const(0x04)
MODE_REALTIME = const(0x05)
MODE_DIAGNOS = const(0x06)
MODE_AUTOCAL = const(0x07)

# 波形库常量
LIBRARY_EMPTY = const(0x00)
LIBRARY_TS2200A = const(0x01)
LIBRARY_TS2200B = const(0x02)
LIBRARY_TS2200C = const(0x03)
LIBRARY_TS2200D = const(0x04)
LIBRARY_TS2200E = const(0x05)
LIBRARY_LRA = const(0x06)

# 设备状态寄存器 - 芯片 ID 位掩码和期望值
_STATUS_DEVICE_ID_MASK = const(0xE0)
_STATUS_DEVICE_ID_SHIFT = const(5)
_EXPECTED_DEVICE_IDS = (3, 7)

# GO 位轮询默认超时时间（毫秒）
_DEFAULT_GO_TIMEOUT_MS = const(5000)
# GO 位轮询间隔（毫秒）
_GO_POLL_INTERVAL_MS = const(10)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Effect:
    """
    DRV2605 波形序列效果

    封装一个波形效果的 ID，支持读取和设置效果 ID。

    Attributes:
        _effect_id (int): 效果 ID (0-123)

    Methods:
        __init__(): 使用效果 ID 初始化效果对象
        raw_value: 返回原始效果 ID（用于写入寄存器）
        id: 获取或设置效果 ID

    Notes:
        - 效果 ID 范围 0-123，参考 DRV2605 数据手册中的效果表
    ==========================================
    DRV2605 waveform sequence effect.

    Encapsulates a single waveform effect ID with read/write access.

    Attributes:
        _effect_id (int): Effect ID (0-123)

    Methods:
        __init__(): Initialize effect with an effect ID
        raw_value: Return raw effect ID for register writes
        id: Get or set effect ID

    Notes:
        - Effect ID range 0-123, see DRV2605 datasheet effect table
    """

    def __init__(self, effect_id):
        """
        初始化效果对象

        Args:
            effect_id (int): 波形效果 ID，取值范围 0-123

        Returns:
            None

        Raises:
            ValueError: 效果 ID 不在 0-123 范围内

        Notes:
            - 效果 ID 对应 DRV2605 数据手册中的波形效果表
            - ISR-safe: 否
        ==========================================
        Initialize effect object.

        Args:
            effect_id (int): Waveform effect ID, range 0-123

        Returns:
            None

        Raises:
            ValueError: If effect ID is not within 0-123

        Notes:
            - Effect ID maps to waveform table in DRV2605 datasheet
            - ISR-safe: No
        """
        self._effect_id = 0
        self.id = effect_id

    @property
    def raw_value(self):
        """
        获取原始效果 ID 值，用于写入寄存器

        Returns:
            int: 效果 ID

        Notes:
            - ISR-safe: 是（仅读取属性，无副作用）
        ==========================================
        Get raw effect ID value for register writes.

        Returns:
            int: Effect ID

        Notes:
            - ISR-safe: Yes (read-only property, no side effects)
        """
        return self._effect_id

    @property
    def id(self):
        """
        获取效果 ID

        Returns:
            int: 效果 ID

        Notes:
            - ISR-safe: 是（仅读取属性，无副作用）
        ==========================================
        Get effect ID.

        Returns:
            int: Effect ID

        Notes:
            - ISR-safe: Yes (read-only property, no side effects)
        """
        return self._effect_id

    @id.setter
    def id(self, effect_id):
        """
        设置效果 ID

        Args:
            effect_id (int): 波形效果 ID，取值范围 0-123

        Raises:
            ValueError: 效果 ID 不在 0-123 范围内

        Notes:
            - ISR-safe: 否
        ==========================================
        Set effect ID.

        Args:
            effect_id (int): Waveform effect ID, range 0-123

        Raises:
            ValueError: If effect ID is not within 0-123

        Notes:
            - ISR-safe: No
        """
        if not 0 <= effect_id <= 123:
            raise ValueError("Effect ID must be a value within 0-123")
        self._effect_id = effect_id

    def __repr__(self):
        return "{}({})".format(type(self).__qualname__, self.id)


class Pause:
    """
    DRV2605 波形序列暂停/延时

    在波形序列中插入延时，由 bit 7 标志表示。

    Attributes:
        _duration (int): 编码后的延时值（最高位为等待标志）

    Methods:
        __init__(): 使用秒数初始化暂停对象
        raw_value: 返回原始编码值（用于写入寄存器）
        duration: 获取或设置暂停时长（秒）

    Notes:
        - 延时范围 0.0 ~ 1.27 秒
        - 内部编码：bit 7 始终置 1 表示等待指令，低 7 位为厘秒值
    ==========================================
    DRV2605 waveform sequence timed delay.

    Inserts a delay in the waveform sequence, indicated by bit 7 flag.

    Attributes:
        _duration (int): Encoded delay value (MSB indicates wait command)

    Methods:
        __init__(): Initialize pause with duration in seconds
        raw_value: Return raw encoded value for register writes
        duration: Get or set pause duration in seconds

    Notes:
        - Duration range 0.0 ~ 1.27 seconds
        - Internal encoding: bit 7 always set for wait command, lower 7 bits = centiseconds
    """

    def __init__(self, duration):
        """
        初始化暂停对象

        Args:
            duration (float): 暂停时长（秒），取值范围 0.0 ~ 1.27

        Returns:
            None

        Raises:
            ValueError: 时长不在 0.0 ~ 1.27 范围内

        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize pause object.

        Args:
            duration (float): Pause duration in seconds, range 0.0 ~ 1.27

        Returns:
            None

        Raises:
            ValueError: If duration is not within 0.0 ~ 1.27

        Notes:
            - ISR-safe: No
        """
        # bit 7 必须置 1 表示等待指令
        self._duration = 0x80
        self.duration = duration

    @property
    def raw_value(self):
        """
        获取原始编码值，用于写入寄存器

        Returns:
            int: 编码后的延时值

        Notes:
            - ISR-safe: 是（仅读取属性，无副作用）
        ==========================================
        Get raw encoded value for register writes.

        Returns:
            int: Encoded delay value

        Notes:
            - ISR-safe: Yes (read-only property, no side effects)
        """
        return self._duration

    @property
    def duration(self):
        """
        获取暂停时长（秒）

        Returns:
            float: 暂停时长（秒）

        Notes:
            - ISR-safe: 是（仅读取属性，无副作用）
        ==========================================
        Get pause duration in seconds.

        Returns:
            float: Pause duration in seconds

        Notes:
            - ISR-safe: Yes (read-only property, no side effects)
        """
        # 去除等待标志位并转换为秒
        return (self._duration & 0x7F) / 100.0

    @duration.setter
    def duration(self, duration):
        """
        设置暂停时长（秒）

        Args:
            duration (float): 暂停时长（秒），取值范围 0.0 ~ 1.27

        Raises:
            ValueError: 时长不在 0.0 ~ 1.27 范围内

        Notes:
            - ISR-safe: 否
        ==========================================
        Set pause duration in seconds.

        Args:
            duration (float): Pause duration in seconds, range 0.0 ~ 1.27

        Raises:
            ValueError: If duration is not within 0.0 ~ 1.27

        Notes:
            - ISR-safe: No
        """
        if not 0.0 <= duration <= 1.27:
            raise ValueError("Pause duration must be a value within 0.0-1.27")
        # 添加等待标志位并转换为厘秒
        self._duration = 0x80 | round(duration * 100.0)

    def __repr__(self):
        return "{}({})".format(type(self).__qualname__, self.duration)


class _DRV2605_Sequence:
    """
    DRV2605 波形序列槽位访问器（列表式索引）

    提供类似列表的接口，用于对 8 个波形序列槽位（slot 0-7）进行读写。
    每个槽位可存储一个 Effect 或 Pause 对象。

    Attributes:
        _drv2605 (DRV2605): 关联的 DRV2605 驱动实例

    Methods:
        __setitem__(): 将 Effect 或 Pause 写入指定槽位
        __getitem__(): 从指定槽位读取 Effect 或 Pause
        __iter__(): 遍历所有 8 个槽位
        __repr__(): 返回所有槽位字符串表示

    Notes:
        - 此类仅供 DRV2605 类内部使用，不应直接实例化
    ==========================================
    DRV2605 waveform sequence slot accessor (list-like indexing).

    Provides a list-like interface for reading/writing 8 waveform sequence slots (0-7).
    Each slot can hold an Effect or Pause object.

    Attributes:
        _drv2605 (DRV2605): Associated DRV2605 driver instance

    Methods:
        __setitem__(): Write Effect or Pause to a slot
        __getitem__(): Read Effect or Pause from a slot
        __iter__(): Iterate over all 8 slots
        __repr__(): Return string representation of all slots

    Notes:
        - Internal class for DRV2605 use only, do not instantiate directly
    """

    def __init__(self, drv2605_instance):
        """
        初始化序列访问器

        Args:
            drv2605_instance (DRV2605): DRV2605 驱动实例

        Returns:
            None

        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize sequence accessor.

        Args:
            drv2605_instance (DRV2605): DRV2605 driver instance

        Returns:
            None

        Notes:
            - ISR-safe: No
        """
        self._drv2605 = drv2605_instance

    def __setitem__(self, slot, effect):
        """
        将 Effect 或 Pause 写入指定槽位

        Args:
            slot (int): 槽位索引，取值范围 0-7
            effect (Effect | Pause): 要写入的效果或暂停对象

        Raises:
            IndexError: 槽位索引不在 0-7 范围内
            TypeError: 效果对象不是 Effect 或 Pause 类型

        Notes:
            - ISR-safe: 否
        ==========================================
        Write an Effect or Pause to a slot.

        Args:
            slot (int): Slot index, range 0-7
            effect (Effect | Pause): Effect or Pause object to write

        Raises:
            IndexError: If slot index is not within 0-7
            TypeError: If effect is not an Effect or Pause

        Notes:
            - ISR-safe: No
        """
        if not 0 <= slot <= 7:
            raise IndexError("Slot must be a value within 0-7")
        if not isinstance(effect, (Effect, Pause)):
            raise TypeError("Effect must be either an Effect or Pause")
        self._drv2605._write_u8(_DRV2605_REG_WAVESEQ1 + slot, effect.raw_value)

    def __getitem__(self, slot):
        """
        从指定槽位读取效果或暂停

        Args:
            slot (int): 槽位索引，取值范围 0-7

        Returns:
            Effect | Pause: 槽位的内容

        Raises:
            IndexError: 槽位索引不在 0-7 范围内

        Notes:
            - ISR-safe: 否
        ==========================================
        Read an effect or pause from a slot.

        Args:
            slot (int): Slot index, range 0-7

        Returns:
            Effect | Pause: Contents of the slot

        Raises:
            IndexError: If slot index is not within 0-7

        Notes:
            - ISR-safe: No
        """
        if not 0 <= slot <= 7:
            raise IndexError("Slot must be a value within 0-7")
        slot_contents = self._drv2605._read_u8(_DRV2605_REG_WAVESEQ1 + slot)
        # bit 7 置 1 表示暂停/等待指令
        if slot_contents & 0x80:
            return Pause((slot_contents & 0x7F) / 100.0)
        return Effect(slot_contents)

    def __iter__(self):
        """
        遍历所有 8 个波形序列槽位

        Returns:
            iterator: 槽位内容迭代器（Effect 或 Pause）

        Notes:
            - ISR-safe: 否
        ==========================================
        Iterate over all 8 waveform sequence slots.

        Returns:
            iterator: Slot contents iterator (Effect or Pause)

        Notes:
            - ISR-safe: No
        """
        for slot in range(0, 8):
            yield self[slot]

    def __repr__(self):
        return repr(list(self))


class DRV2605:
    """
    TI DRV2605/DRV2605L 触觉反馈电机驱动类

    通过 I2C 接口控制 DRV2605/DRV2605L 触觉驱动器，支持多种操作模式、
    波形效果库选择、实时播放和序列控制。

    Attributes:
        _device (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 是否启用调试日志
        _sequence (_DRV2605_Sequence): 波形序列槽位访问器
        mode (int): 当前操作模式
        library (int): 当前选中的波形库
        sequence: 类似列表的波形序列控制接口

    Methods:
        __init__(): 初始化芯片，配置默认参数并验证芯片 ID
        play(): 触发播放当前配置的波形效果序列
        play_effect(): 播放效果并等待完成或超时
        stop(): 停止振动
        set_waveform(): 设置指定槽位的波形效果
        use_ERM(): 配置为 ERM 电机模式（默认）
        use_LRM(): 配置为 LRA 线性谐振电机模式
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入的 I2C 实例，使用依赖注入模式
        - 上电默认模式为 MODE_INTTRIG，库为 LIBRARY_TS2200A
        - DRV2605 device_id=3, DRV2605L device_id=7
    ==========================================
    TI DRV2605/DRV2605L haptic feedback motor driver.

    Controls DRV2605/DRV2605L haptic drivers via I2C, supporting multiple modes,
    waveform library selection, real-time playback and sequence control.

    Attributes:
        _device (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug log enabled
        _sequence (_DRV2605_Sequence): Waveform sequence slot accessor
        mode (int): Current operation mode
        library (int): Currently selected waveform library
        sequence: List-like waveform sequence control interface

    Methods:
        __init__(): Initialize chip, configure defaults and verify chip ID
        play(): Trigger playback of configured effect sequence
        play_effect(): Play effect and wait for completion or timeout
        stop(): Stop vibration
        set_waveform(): Set waveform effect for a slot
        use_ERM(): Configure for ERM motor mode (default)
        use_LRM(): Configure for LRA linear resonant actuator mode
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance (dependency injection)
        - Power-on defaults: MODE_INTTRIG mode, LIBRARY_TS2200A library
        - DRV2605 device_id=3, DRV2605L device_id=7
    """

    # I2C 默认地址
    I2C_DEFAULT_ADDR = _DRV2605_ADDR

    # 类级 I2C 读写缓冲区（减少内存分配）
    _BUFFER = bytearray(1)

    # GO 位轮询默认超时时间（毫秒）
    DEFAULT_GO_TIMEOUT_MS = _DEFAULT_GO_TIMEOUT_MS

    def __init__(self, i2c, address=_DRV2605_ADDR, debug=False):
        """
        初始化 DRV2605/DRV2605L 触觉反馈驱动

        验证芯片 ID、配置初始寄存器并设为内部触发模式。

        Args:
            i2c: I2C 总线实例（需支持 readfrom_mem_into 和 writeto_mem 方法）
            address (int): I2C 设备地址，默认 0x5A
            debug (bool): 是否启用调试日志输出

        Returns:
            None

        Raises:
            ValueError: I2C 实例不支持所需接口时抛出
            RuntimeError: 无法检测到 DRV2605/DRV2605L 设备时抛出

        Notes:
            - 初始化时执行芯片 ID 校验（device_id 必须为 3 或 7）
            - ISR-safe: 否
        ==========================================
        Initialize DRV2605/DRV2605L haptic feedback driver.

        Verifies chip ID, configures initial registers and sets internal trigger mode.

        Args:
            i2c: I2C bus instance (must support readfrom_mem_into and writeto_mem)
            address (int): I2C device address, default 0x5A
            debug (bool): Enable debug log output

        Returns:
            None

        Raises:
            ValueError: If I2C instance does not support required interface
            RuntimeError: If DRV2605/DRV2605L device not detected

        Notes:
            - Performs chip ID verification on init (device_id must be 3 or 7)
            - ISR-safe: No
        """
        # I2C 参数校验 - 鸭子类型检查
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem_into")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance with writeto_mem")

        self._device = i2c
        self._address = address
        self._debug = debug

        # 芯片 ID 校验 - device_id 必须为 3 (DRV2605) 或 7 (DRV2605L)
        status = self._read_u8(_DRV2605_REG_STATUS)
        device_id = (status & _STATUS_DEVICE_ID_MASK) >> _STATUS_DEVICE_ID_SHIFT
        if device_id not in _EXPECTED_DEVICE_IDS:
            raise RuntimeError("Failed to find DRV2605, check wiring! Device ID: %d" % device_id)

        self._log("DRV2605 found, device_id=%d" % device_id)

        # 配置初始寄存器
        # 退出待机模式
        self._write_u8(_DRV2605_REG_MODE, 0x00)
        # 禁用实时播放
        self._write_u8(_DRV2605_REG_RTPIN, 0x00)
        # 设置默认波形序列：槽位 0 为强点击，其余为空
        self._write_u8(_DRV2605_REG_WAVESEQ1, 1)
        self._write_u8(_DRV2605_REG_WAVESEQ2, 0)
        # 禁用过驱
        self._write_u8(_DRV2605_REG_OVERDRIVE, 0)
        # 禁用维持时间
        self._write_u8(_DRV2605_REG_SUSTAINPOS, 0)
        self._write_u8(_DRV2605_REG_SUSTAINNEG, 0)
        # 禁用制动
        self._write_u8(_DRV2605_REG_BREAK, 0)
        # 设置音频最大输入电平
        self._write_u8(_DRV2605_REG_AUDIOMAX, 0x64)

        # 配置为 ERM 开环模式
        self.use_ERM()
        # 启用 ERM 开环模式
        control3 = self._read_u8(_DRV2605_REG_CONTROL3)
        self._write_u8(_DRV2605_REG_CONTROL3, control3 | 0x20)

        # 默认使用内部触发模式和 TS2200A 波形库
        self.mode = MODE_INTTRIG
        self.library = LIBRARY_TS2200A

        # 初始化序列访问器
        self._sequence = _DRV2605_Sequence(self)

        self._log("DRV2605 initialization complete")

    def _log(self, msg):
        """
        输出调试日志

        Args:
            msg (str): 日志消息

        Returns:
            None
        ==========================================
        Output debug log message.

        Args:
            msg (str): Log message

        Returns:
            None
        """
        if self._debug:
            print("[DRV2605] %s" % msg)

    def _read_u8(self, address):
        """
        从指定寄存器地址读取一个 8 位无符号值

        Args:
            address (int): 8 位寄存器地址

        Returns:
            int: 读取的 8 位值

        Raises:
            RuntimeError: I2C 通信失败时抛出

        Notes:
            - 使用类级 _BUFFER 复用，减少内存分配
            - ISR-safe: 否
        ==========================================
        Read an 8-bit unsigned value from specified register address.

        Args:
            address (int): 8-bit register address

        Returns:
            int: 8-bit value read

        Raises:
            RuntimeError: If I2C communication fails

        Notes:
            - Uses class-level _BUFFER for reduced memory allocation
            - ISR-safe: No
        """
        try:
            self._device.readfrom_mem_into(self._address, address, self._BUFFER)
        except OSError as e:
            raise RuntimeError("I2C read failed at address 0x%02X" % address) from e
        return self._BUFFER[0]

    def _write_u8(self, address, val):
        """
        向指定寄存器地址写入一个 8 位无符号值

        Args:
            address (int): 8 位寄存器地址
            val (int): 要写入的 8 位值

        Returns:
            None

        Raises:
            RuntimeError: I2C 通信失败时抛出

        Notes:
            - 使用类级 _BUFFER 复用，减少内存分配
            - ISR-safe: 否
        ==========================================
        Write an 8-bit unsigned value to specified register address.

        Args:
            address (int): 8-bit register address
            val (int): 8-bit value to write

        Returns:
            None

        Raises:
            RuntimeError: If I2C communication fails

        Notes:
            - Uses class-level _BUFFER for reduced memory allocation
            - ISR-safe: No
        """
        self._BUFFER[0] = val & 0xFF
        try:
            self._device.writeto_mem(self._address, address, self._BUFFER)
        except OSError as e:
            raise RuntimeError("I2C write failed at address 0x%02X" % address) from e

    def play(self):
        """
        触发播放当前配置的波形效果序列
        设置 GO 寄存器 bit 0 启动播放（无等待，立即返回）。

        Notes:
            - 调用后效果异步执行，不阻塞
            - 如需等待完成，请使用 play_effect()
            - ISR-safe: 否
        ==========================================
        Trigger playback of the configured waveform effect sequence.
        Sets GO register bit 0 to start playback (returns immediately, no wait).

        Notes:
            - Effect runs asynchronously after call, non-blocking
            - Use play_effect() if waiting for completion is required
            - ISR-safe: No
        """
        self._write_u8(_DRV2605_REG_GO, 1)

    def play_effect(self, timeout_ms=None):
        """
        播放效果并等待 GO 位清零（阻塞模式）或提供超时保护

        先触发播放，然后轮询 GO 寄存器等待 bit 0 清零（表示播放完成）。
        包含超时保护以防止死循环。

        Args:
            timeout_ms (int): 等待超时时间（毫秒），默认使用 DEFAULT_GO_TIMEOUT_MS (5000ms)。
                              设为 0 表示不等待（等同于 play()）。

        Returns:
            bool: True 表示播放完成，False 表示超时

        Notes:
            - 阻塞调用，等待效果播放完成
            - 包含超时保护，防止 GO 位卡死导致死循环
            - ISR-safe: 否
        ==========================================
        Play effect and wait for GO bit clear (blocking) with timeout protection.

        Triggers playback, then polls GO register waiting for bit 0 to clear
        (indicating completion). Includes timeout protection against infinite loops.

        Args:
            timeout_ms (int): Timeout in milliseconds, default DEFAULT_GO_TIMEOUT_MS (5000ms).
                              Set to 0 for non-blocking (equivalent to play()).

        Returns:
            bool: True if playback completed, False if timeout

        Notes:
            - Blocking call, waits for effect completion
            - Includes timeout protection against stuck GO bit
            - ISR-safe: No
        """
        # 触发播放
        self._write_u8(_DRV2605_REG_GO, 1)

        # 如果 timeout_ms 为 0，立即返回（非阻塞模式）
        if timeout_ms == 0:
            return True

        # 使用默认超时值
        if timeout_ms is None:
            timeout_ms = _DEFAULT_GO_TIMEOUT_MS

        self._log("play_effect: waiting for GO bit clear, timeout=%dms" % timeout_ms)

        # 轮询 GO bit 0 等待清零
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            status = self._read_u8(_DRV2605_REG_GO)
            # GO bit 0 清零表示播放完成
            if not (status & _GO_BIT):
                self._log("play_effect: GO bit cleared, playback complete")
                return True
            time.sleep_ms(_GO_POLL_INTERVAL_MS)

        # 超时
        self._log("play_effect: timeout waiting for GO bit clear")
        return False

    def stop(self):
        """
        停止振动
        清除 GO 寄存器 bit 0 以立即停止电机振动。

        Notes:
            - ISR-safe: 否
        ==========================================
        Stop vibrating the motor.
        Clears GO register bit 0 to immediately stop vibration.

        Notes:
            - ISR-safe: No
        """
        self._write_u8(_DRV2605_REG_GO, 0)

    @property
    def mode(self):
        """
        获取或设置芯片操作模式

        模式值：
          - MODE_INTTRIG (0): 内部触发，调用 play() 即振动（默认）
          - MODE_EXTTRIGEDGE (1): 外部触发，边沿模式
          - MODE_EXTTRIGLVL (2): 外部触发，电平模式
          - MODE_PWMANALOG (3): PWM/模拟输入模式
          - MODE_AUDIOVIBE (4): 音频转振动模式
          - MODE_REALTIME (5): 实时播放模式
          - MODE_DIAGNOS (6): 诊断模式
          - MODE_AUTOCAL (7): 自动校准模式

        Returns:
            int: 当前模式值 (0-7)

        Notes:
            - ISR-safe: 否（读取时访问 I2C 总线）
        ==========================================
        Get or set the chip operation mode.

        Mode values:
          - MODE_INTTRIG (0): Internal trigger, vibrates on play() call (default)
          - MODE_EXTTRIGEDGE (1): External trigger, edge mode
          - MODE_EXTTRIGLVL (2): External trigger, level mode
          - MODE_PWMANALOG (3): PWM/analog input mode
          - MODE_AUDIOVIBE (4): Audio-to-vibration mode
          - MODE_REALTIME (5): Real-time playback mode
          - MODE_DIAGNOS (6): Diagnostics mode
          - MODE_AUTOCAL (7): Auto-calibration mode

        Returns:
            int: Current mode value (0-7)

        Notes:
            - ISR-safe: No (accesses I2C bus during read)
        """
        return self._read_u8(_DRV2605_REG_MODE)

    @mode.setter
    def mode(self, val):
        """
        设置芯片操作模式

        Args:
            val (int): 模式值，取值范围 0-7

        Raises:
            ValueError: 模式值不在 0-7 范围内

        Notes:
            - ISR-safe: 否
        ==========================================
        Set chip operation mode.

        Args:
            val (int): Mode value, range 0-7

        Raises:
            ValueError: If mode value is not within 0-7

        Notes:
            - ISR-safe: No
        """
        if not 0 <= val <= 7:
            raise ValueError("Mode must be a value within 0-7")
        self._write_u8(_DRV2605_REG_MODE, val)

    @property
    def library(self):
        """
        获取或设置波形库

        波形库值：
          - LIBRARY_EMPTY (0): 空库
          - LIBRARY_TS2200A (1): TS2200 库 A（默认）
          - LIBRARY_TS2200B (2): TS2200 库 B
          - LIBRARY_TS2200C (3): TS2200 库 C
          - LIBRARY_TS2200D (4): TS2200 库 D
          - LIBRARY_TS2200E (5): TS2200 库 E
          - LIBRARY_LRA (6): LRA 线性谐振电机库

        Returns:
            int: 当前波形库值 (0-6)

        Notes:
            - ISR-safe: 否（读取时访问 I2C 总线）
        ==========================================
        Get or set the waveform library.

        Library values:
          - LIBRARY_EMPTY (0): Empty
          - LIBRARY_TS2200A (1): TS2200 library A (default)
          - LIBRARY_TS2200B (2): TS2200 library B
          - LIBRARY_TS2200C (3): TS2200 library C
          - LIBRARY_TS2200D (4): TS2200 library D
          - LIBRARY_TS2200E (5): TS2200 library E
          - LIBRARY_LRA (6): LRA library

        Returns:
            int: Current library value (0-6)

        Notes:
            - ISR-safe: No (accesses I2C bus during read)
        """
        return self._read_u8(_DRV2605_REG_LIBRARY) & 0x07

    @library.setter
    def library(self, val):
        """
        设置波形库

        Args:
            val (int): 波形库值，取值范围 0-6

        Raises:
            ValueError: 波形库值不在 0-6 范围内

        Notes:
            - ISR-safe: 否
        ==========================================
        Set waveform library.

        Args:
            val (int): Library value, range 0-6

        Raises:
            ValueError: If library value is not within 0-6

        Notes:
            - ISR-safe: No
        """
        if not 0 <= val <= 6:
            raise ValueError("Library must be a value within 0-6")
        self._write_u8(_DRV2605_REG_LIBRARY, val)

    @property
    def sequence(self):
        """
        获取波形序列槽位访问器（列表式索引）

        通过索引访问槽位 0-7。获取时返回 Effect 或 Pause 对象，
        设置时须传入 Effect 或 Pause 对象。

        示例:
            # 设置槽位 0 为效果 88
            drv.sequence[0] = Effect(88)
            # 读取槽位 0
            slot_0 = drv.sequence[0]

        Returns:
            _DRV2605_Sequence: 序列槽位访问器

        Notes:
            - ISR-safe: 否
        ==========================================
        Get waveform sequence slot accessor (list-like indexing).

        Access slots 0-7 by index. Returns Effect or Pause on read,
        requires Effect or Pause on write.

        Example:
            # Set slot 0 to effect 88
            drv.sequence[0] = Effect(88)
            # Read slot 0
            slot_0 = drv.sequence[0]

        Returns:
            _DRV2605_Sequence: Sequence slot accessor

        Notes:
            - ISR-safe: No
        """
        return self._sequence

    @property
    def realtime_value(self):
        """
        获取或设置实时播放模式输出值

        在 MODE_REALTIME 模式下，电机以连续振幅/方向驱动。
        设备默认期望带符号 8 位整数，具体效果取决于电机类型和开环/闭环模式。

        示例:
            drv.realtime_value = 0
            drv.mode = drv2605.MODE_REALTIME
            # 以 50% 振幅振动
            drv.realtime_value = 64
            time.sleep(0.5)
            # 以 100% 振幅振动
            drv.realtime_value = 127
            time.sleep(0.5)
            # 停止并返回内部触发模式
            drv.realtime_value = 0
            drv.mode = drv2605.MODE_INTTRIG

        Returns:
            int: 当前实时播放值

        Notes:
            - ISR-safe: 否（读取时访问 I2C 总线）
        ==========================================
        Get or set real-time playback output value.

        In MODE_REALTIME, motor is driven continuously with amplitude/direction
        determined by this value. Device expects signed 8-bit integer by default.

        Example:
            drv.realtime_value = 0
            drv.mode = drv2605.MODE_REALTIME
            # Buzz motor at 50% amplitude
            drv.realtime_value = 64
            time.sleep(0.5)
            # Buzz at 100% amplitude
            drv.realtime_value = 127
            time.sleep(0.5)
            # Stop and return to internal trigger mode
            drv.realtime_value = 0
            drv.mode = drv2605.MODE_INTTRIG

        Returns:
            int: Current real-time playback value

        Notes:
            - ISR-safe: No (accesses I2C bus during read)
        """
        return self._read_u8(_DRV2605_REG_RTPIN)

    @realtime_value.setter
    def realtime_value(self, val):
        """
        设置实时播放值

        Args:
            val (int): 实时播放值，范围 -127 到 255

        Raises:
            ValueError: 值不在 -127 到 255 范围内

        Notes:
            - ISR-safe: 否
        ==========================================
        Set real-time playback value.

        Args:
            val (int): Real-time playback value, range -127 to 255

        Raises:
            ValueError: If value is not within -127 to 255

        Notes:
            - ISR-safe: No
        """
        if not -127 <= val <= 255:
            raise ValueError("Real-Time Playback value must be between -127 and 255")
        self._write_u8(_DRV2605_REG_RTPIN, val)

    def set_waveform(self, effect_id, slot=0):
        """
        为指定槽位设置波形效果

        Args:
            effect_id (int): 波形效果 ID，取值范围 0-123
            slot (int): 序列槽位，取值范围 0-7，默认 0

        Raises:
            ValueError: 效果 ID 或槽位值超出范围

        Notes:
            - 最多可组合 8 个效果（槽位 0-7）
            - ISR-safe: 否
        ==========================================
        Set waveform effect for the specified slot.

        Args:
            effect_id (int): Waveform effect ID, range 0-123
            slot (int): Sequence slot, range 0-7, default 0

        Raises:
            ValueError: If effect ID or slot value is out of range

        Notes:
            - Up to 8 effects can be combined (slots 0-7)
            - ISR-safe: No
        """
        if not 0 <= effect_id <= 123:
            raise ValueError("Effect ID must be a value within 0-123")
        if not 0 <= slot <= 7:
            raise ValueError("Slot must be a value within 0-7")
        self._write_u8(_DRV2605_REG_WAVESEQ1 + slot, effect_id)

    def use_ERM(self):
        """
        配置为 ERM（偏心旋转质量）电机模式
        这是默认的电机类型，清除 FEEDBACK 寄存器的 N_ERM_LRA 位。

        Notes:
            - ISR-safe: 否
        ==========================================
        Configure for ERM (Eccentric Rotating Mass) motor mode.
        This is the default motor type. Clears N_ERM_LRA bit in FEEDBACK register.

        Notes:
            - ISR-safe: No
        """
        feedback = self._read_u8(_DRV2605_REG_FEEDBACK)
        self._write_u8(_DRV2605_REG_FEEDBACK, feedback & 0x7F)

    def use_LRM(self):
        """
        配置为 LRA（线性谐振执行器）电机模式
        设置 FEEDBACK 寄存器的 N_ERM_LRA 位以启用 LRA 驱动模式。

        Notes:
            - ISR-safe: 否
        ==========================================
        Configure for LRA (Linear Resonance Actuator) motor mode.
        Sets N_ERM_LRA bit in FEEDBACK register to enable LRA drive mode.

        Notes:
            - ISR-safe: No
        """
        feedback = self._read_u8(_DRV2605_REG_FEEDBACK)
        self._write_u8(_DRV2605_REG_FEEDBACK, feedback | 0x80)

    def deinit(self):
        """
        释放硬件资源
        停止振动、进入待机模式以降低功耗。

        Notes:
            - 调用后设备进入低功耗待机状态
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Stop vibration and enter standby mode to reduce power consumption.

        Notes:
            - Device enters low-power standby after calling
            - ISR-safe: No
        """
        # 停止振动
        self.stop()
        # 进入待机模式 (MODE 寄存器 bit 6 = 1)
        self._write_u8(_DRV2605_REG_MODE, 0x40)
        self._log("DRV2605 deinitialized")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
