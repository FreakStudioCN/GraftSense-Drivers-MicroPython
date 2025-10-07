# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:13
# @Author  : 缪贵成
# @File    : nec.py
# @Description : nec协议红外发送
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
from  . import IR

# ======================================== 全局变量 ============================================

_TBURST = const(563)
_T_ONE = const(1687)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class NEC(IR):
    """
    NEC 协议红外发送类，仅 RP2 平台，支持标准 NEC 和 Samsung 扩展。

    Attributes:
        valid (tuple): 最大可用地址、数据和切换标志 (addr_max, data_max, toggle_max)。
        samsung (bool): 是否为 Samsung 协议。
        继承自 IR 类的属性，包括 _rmt, _arr, _mva, verbose, carrier, aptr, _busy 等。

    Methods:
        __init__(pin, freq=38000, verbose=False) -> None: 初始化 NEC 对象。
        _bit(b: int) -> None: 发送单个二进制位。
        tx(addr: int, data: int, _) -> None: 发送完整 NEC 信号帧。
        repeat() -> None: 发送重复码信号帧。

    Notes:
        addr < 256 时自动补充地址校验位。
        支持标准 NEC 和 Samsung 变体。
        子类调用 transmit() 会自动使用 tx() 填充 _arr。
    ==========================================

    NEC infrared transmitter class for RP2 platform, supports standard NEC and Samsung protocols.

    Attributes:
        valid (tuple): Maximum address, data, and toggle (addr_max, data_max, toggle_max).
        samsung (bool): Whether using Samsung protocol.
        Inherits from IR: _rmt, _arr, _mva, verbose, carrier, aptr, _busy.

    Methods:
        __init__(pin, freq=38000, verbose=False) -> None: Initialize NEC object.
        _bit(b: int) -> None: Transmit a single binary bit.
        tx(addr: int, data: int, _) -> None: Transmit a complete NEC frame.
        repeat() -> None: Transmit a repeat frame.

    Notes:
        For addr < 256, address complement is automatically appended.
        Supports standard NEC and Samsung variants.
        Calling transmit() uses tx() to populate _arr.
    """

    valid = (0xffff, 0xff, 0)  # Max addr, data, toggle
    samsung = False

    def __init__(self, pin, freq: int=38000, verbose: bool=False) -> None:
        """
        初始化 NEC 对象。

        Args:
            pin (Pin): 红外 LED 引脚。
            freq (int, optional): 载波频率，默认 38000Hz。
            verbose (bool, optional): 是否打印调试信息。

        Notes:
            调用 IR 基类初始化，设置脉冲数组大小 68，载波占空比 33%。
            支持标准 NEC 和 Samsung 协议。
        ==========================================
        Initialize NEC object.

        Args:
            pin (Pin): IR LED pin.
            freq (int, optional): Carrier frequency, default 38000Hz.
            verbose (bool, optional): Enable debug printing.

        Notes:
            Calls IR base class initializer with array size 68, duty 33%.
            Supports standard NEC and Samsung protocol.
        """
        super().__init__(pin, freq, 68, 33, verbose)

    def _bit(self, b: int) -> None:
        """
        发送单个二进制位。

        Args:
            b (int): 二进制位 0 或 1。

        Notes:
            对应脉冲序列为 563μs 高电平 + 562/1687μs 低电平。
        ==========================================

        Transmit a single binary bit.

        Args:
            b (int): Binary bit, 0 or 1.

        Notes:
            Pulse pattern: 563μs high + 562/1687μs low depending on bit.
        """
        self.append(_TBURST, _T_ONE if b else _TBURST)

    def tx(self, addr: int, data: int, _) -> None:
        """
        发送完整 NEC 信号帧。

        Args:
            addr (int): 协议地址。
            data (int): 协议数据。
            _ : 忽略参数，用于兼容 transmit 接口的 toggle。

        Notes:
            addr < 256 时会自动生成校验位。
            Samsung 协议使用 4500μs 前导码，高低电平各 4500μs。
            标准 NEC 协议使用 9000μs 前导高电平 + 4500μs 前导低电平。
        ==========================================

        Transmit a complete NEC frame.

        Args:
            addr (int): Protocol address.
            data (int): Protocol data.
            _ : Ignored, for toggle compatibility.


        Notes:
            For addr < 256, complement bits are automatically appended.
            Samsung protocol uses 4500μs leader high and low.
            Standard NEC uses 9000μs leader high + 4500μs low.
        """
        if self.samsung:
            self.append(4500, 4500)
        else:
            self.append(9000, 4500)
        if addr < 256:
            if self.samsung:
                addr |= addr << 8
            else:
                addr |= ((addr ^ 0xff) << 8)
        for _ in range(16):
            self._bit(addr & 1)
            addr >>= 1
        data |= ((data ^ 0xff) << 8)
        for _ in range(16):
            self._bit(data & 1)
            data >>= 1
        self.append(_TBURST)

    def repeat(self) -> None:
        """
        发送 NEC 重复码帧。

        Notes:
            重复码帧为 9000μs 高电平 + 2250μs 低电平 + 563μs 高电平。
        ==========================================

        Transmit NEC repeat frame.
        Notes:
            Repeat frame pattern: 9000μs high + 2250μs low + 563μs high.
        """
        self.aptr = 0
        self.append(9000, 2250, _TBURST)
        self.trigger()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
