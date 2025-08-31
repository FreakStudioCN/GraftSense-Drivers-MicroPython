# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:12
# @Author  : 缪贵成
# @File    : __init__.py
# @Description : 红外发射部分基类
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from sys import platform
RP2 = platform == 'rp2'
if RP2:
    from .rp2_rmt import RP2_RMT
from array import array
from time import ticks_us, ticks_diff, sleep_ms
from micropython import const

# ======================================== 全局变量 ============================================

# ===========================================常量 =============================================

STOP = const(0)  # End of data

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class IR:
    """
    RP2 平台红外发射抽象基类，负责生成脉冲数组并通过 RP2_RMT 发送。

    Attributes:
        _rmt (RP2_RMT): RP2_RMT 实例，用于发送脉冲。
        _arr (array): 存储高低电平持续时间的数组，单位 μs。
        _mva (memoryview): 指向 _arr 的内存视图。
        verbose (bool): 是否打印调试信息。
        carrier (bool): 当前载波状态。
        aptr (int): 当前数组索引。
        _busy (bool): 是否正在发送红外信号。

    Methods:
        __init__(pin, cfreq, asize, duty, verbose) -> None: 初始化 IR 对象。
        _cb(t) -> None: 内部回调函数，用于物理发送。
        busy() -> bool: 检查发送状态。
        transmit(addr, data, toggle=0, validate=False) -> None: 发送红外信号。
        trigger() -> None: 启动发送。
        append(*times) -> None: 添加脉冲时间。
        add(t) -> None: 增加最后一个脉冲时间。

    Notes:
        仅支持 RP2 平台。
        子类需实现 tx() 方法以填充协议数据。
        verbose 为 True 时会打印调试信息。

    ==========================================

    Abstract IR transmitter class for RP2 platform.

    Attributes:
        _rmt (RP2_RMT): RP2 RMT instance to send pulses.
        _arr (array): Array storing pulse durations in μs.
        _mva (memoryview): Memory view of _arr.
        verbose (bool): Enable debug printing.
        carrier (bool): Current carrier state.
        aptr (int): Current index in the array.
        _busy (bool): Whether transmission is in progress.

    Methods:
        __init__(pin, cfreq, asize, duty, verbose) -> None: Initialize IR object.
        _cb(t) -> None: Internal callback function for transmission.
        busy() -> bool: Check if transmitter is busy.
        transmit(addr, data, toggle=0, validate=False) -> None: Send IR signal.
        trigger() -> None: Trigger physical transmission.
        append(*times) -> None: Append pulse durations.
        add(t) -> None: Increase last pulse duration.

    Notes:
        Only supports RP2 platform.
        Subclasses must implement tx() to populate protocol data.
        Verbose prints debug info if True.
    """

    _active_high = True
    _space = 0
    timeit = False

    def __init__(self, pin, cfreq: int, asize: int, duty: int, verbose: bool) -> None:
        """
        初始化 IR 对象，仅 RP2 平台。

        Args:
            pin (Pin): 红外 LED 引脚。
            cfreq (int): 载波频率，单位 Hz。
            asize (int): 脉冲数组大小。
            duty (int): 占空比百分比。
            verbose (bool): 是否打印调试信息。

        Notes:
            初始化 RP2_RMT 实例。
        ==========================================

        Initialize IR object for RP2 platform.

        Args:
            pin (Pin): IR LED pin.
            cfreq (int): Carrier frequency in Hz.
            asize (int): Array size for pulse storage.
            duty (int): Duty ratio in %.
            verbose (bool): Enable debug printing.

        Notes:
            Initializes RP2_RMT instance.
        """
        self._rmt = RP2_RMT(pin_pulse=None, carrier=(pin, cfreq, duty))
        asize += 1
        self._arr = array('H', (0 for _ in range(asize)))
        self._mva = memoryview(self._arr)
        self.verbose = verbose
        self.carrier = False
        self.aptr = 0
        self._busy = False
        self._tcb = self._cb

    def _cb(self, t) -> None:
        """
        内部回调函数（RP2 平台不使用）
        。
        Args:
            t: 定时器对象（忽略）。

        Notes:
            RP2 平台通过 RMT 自动发送，无需回调。
        ==========================================

        Internal callback function (unused on RP2).

        Args:
            t: Timer object (ignored).

        Notes:
            RP2 automatically handles transmission via RMT.
        """
        pass

    def busy(self) -> bool:
        """
        检查发送状态。

        Returns:
            bool: True 表示仍在发送，False 表示空闲。

        Notes:
            调用 RP2_RMT.busy() 检查状态。
        ==========================================

        Check if IR transmitter is busy.

        Returns:
            bool: True if transmitting, False if idle.

        Notes:
            Uses RP2_RMT.busy() to check state.
        """
        return self._rmt.busy()

    def transmit(self, addr: int, data: int, toggle: int=0, validate: bool=False) -> None:
        """
        发送红外信号，子类需实现 tx() 方法。

        Args:
            addr (int): 协议地址。
            data (int): 协议数据。
            toggle (int, optional): NEC 协议切换标志，默认 0。
            validate (bool, optional): 是否校验 addr/data/toggle 范围。

        Raises:
            ValueError: 当 validate=True 且 addr/data/toggle 越界。

        Notes:
            发送前会等待前一次发送完成。
        ==========================================

        Send IR signal; subclasses must implement tx().

        Args:
            addr (int): Protocol address.
            data (int): Protocol data.
            toggle (int, optional): NEC toggle flag, default 0.
            validate (bool, optional): Validate addr/data/toggle range.

        Raises:
            ValueError: If validate=True and addr/data/toggle out of range.

        Notes:
            Waits for previous transmission to complete.
        """
        while self.busy():
            pass
        self.aptr = 0
        self.carrier = False
        self.tx(addr, data, toggle)
        self.trigger()
        sleep_ms(1)

    def trigger(self) -> None:
        """
        启动实际发送。

        Notes:
            自动在数组末尾添加 STOP。
        ==========================================

        Trigger physical IR transmission.

        Notes:
            Automatically appends STOP at end of array.
        """
        self.append(STOP)
        self.aptr = 0
        self._rmt.send(self._arr)

    def append(self, *times: int) -> None:
        """
        向脉冲数组添加一个或多个时间段。

        Args:
            *times (int): 一个或多个脉冲时间（μs）。

        Notes:
            自动切换载波状态。
        ==========================================

        Append one or more pulse durations to array.

        Args:
            *times (int): One or more pulse durations (μs).

        Notes:
            Carrier state toggled automatically.
        """
        for t in times:
            self._arr[self.aptr] = t
            self.aptr += 1
            self.carrier = not self.carrier
            if self.verbose:
                print('append', t, 'carrier', self.carrier)

    def add(self, t: int) -> None:
        """
        增加最后一个脉冲时间段（双相编码）。

        Args:
            t (int): 增加的时间段（μs），必须大于 0。

        Raises:
            AssertionError: 当 t <= 0。

        Notes:
            不影响 carrier 状态。
        ==========================================

        Increase last pulse duration (biphase encoding).

        Args:
            t (int): Duration to add (μs), must be > 0.

        Raises:
            AssertionError: If t <= 0.

        Notes:
            Does not affect carrier state.
        """
        assert t > 0
        if self.verbose:
            print('add', t)
        self._arr[self.aptr - 1] += t

class Player(IR):
    """
    IR 播放器类，仅 RP2 平台。
    Attributes:
        继承自 IR。

    Methods:
        __init__(pin, freq=38000, verbose=False, asize=68) -> None: 初始化播放器。
        play(lst) -> None: 播放脉冲列表。

    Notes:
    用于直接播放已知脉冲序列。
    ==========================================

    IR player class for RP2 platform.
    Attributes:
        Inherits from IR.

    Methods:
        __init__(pin, freq=38000, verbose=False, asize=68) -> None: Initialize player.
        play(lst) -> None: Play pulse list.

    Notes:
        Used to play known pulse sequences.
    """

    def __init__(self, pin, freq: int=38000, verbose: bool=False, asize: int=68) -> None:
        """
        初始化 Player 对象。

        Args:
            pin (Pin): 红外 LED 引脚。
            freq (int, optional): 载波频率，默认 38000Hz。
            verbose (bool, optional): 是否打印调试信息。
            asize (int, optional): 脉冲数组大小，默认 68。

        Notes:
            调用 IR 基类初始化。
        ==========================================

        Initialize Player object.

        Args:
            pin (Pin): IR LED pin.
            freq (int, optional): Carrier frequency, default 38000Hz.
            verbose (bool, optional): Enable debug printing.
            asize (int, optional): Array size, default 68.

        Notes:
            Calls base IR class initializer.
        """
        super().__init__(pin, freq, asize, 33, verbose)

    def play(self, lst) -> None:
        """
        播放已知脉冲列表。

        Args:
            lst (iterable): 包含脉冲时间的列表或元组。

        Notes:
            会将脉冲写入 _arr 并触发发送。
        ==========================================

        Play a known pulse list.
        Args:
            lst (iterable): List or tuple of pulse durations.


        Notes:
            Writes pulses to _arr and triggers transmission.
        """
        for x, t in enumerate(lst):
            self._arr[x] = t
        self.aptr = x + 1
        self.trigger()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
