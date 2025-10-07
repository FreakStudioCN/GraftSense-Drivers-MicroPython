# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:12
# @Author  : 缪贵成
# @File    : __init__.py
# @Description : 红外接收模块基类
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, Timer
from array import array
from time import ticks_us

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class IR_RX:
    """
    该类是红外接收器基类，用于捕获和解析红外遥控信号。

    Attributes:
        Timer_id (int): 定时器 ID，默认为 -1 表示使用软件定时器，可被覆盖。
        REPEAT (int): 重复码标志值。
        BADSTART (int): 错误码，表示起始码错误。
        BADBLOCK (int): 错误码，表示数据块错误。
        BADREP (int): 错误码，表示重复码错误。
        OVERRUN (int): 错误码，表示接收数据溢出。
        BADDATA (int): 错误码，表示数据错误。
        BADADDR (int): 错误码，表示地址错误。

    Methods:
        __init__(pin: Pin, nedges: int, tblock: int, callback, *args) -> None:
            初始化红外接收对象，设置引脚、中断和回调函数。
        _cb_pin(line) -> None:
            引脚中断回调，记录信号沿的时间戳。
        do_callback(cmd: int, addr: int, ext: int, thresh: int = 0) -> None:
            执行用户回调或错误回调。
        error_function(func) -> None:
            设置错误处理回调函数。
        close() -> None:
            关闭接收器，注销中断和定时器。

    Notes:
        本类为协议解码器基类，具体协议需在子类中实现。
        回调函数在中断上下文中触发，需保证执行快速安全。

    ==========================================

    Base class for IR receiver, used for capturing and decoding IR remote signals.

    Attributes:
        Timer_id (int): Timer ID. Default -1 means software timer, can be overridden.
        REPEAT (int): Repeat code indicator.
        BADSTART (int): Error code for bad start.
        BADBLOCK (int): Error code for bad block.
        BADREP (int): Error code for bad repeat.
        OVERRUN (int): Error code for overrun.
        BADDATA (int): Error code for bad data.
        BADADDR (int): Error code for bad address.

    Methods:
        __init__(pin: Pin, nedges: int, tblock: int, callback, *args) -> None:
            Initialize IR receiver, configure pin, IRQ, and callback.
        _cb_pin(line) -> None:
            Pin IRQ callback. Store edge timestamps.
        do_callback(cmd: int, addr: int, ext: int, thresh: int = 0) -> None:
            Run user callback or error handler.
        error_function(func) -> None:
            Set error handler function.
        close() -> None:
            Close receiver, disable IRQ and timer.

    Notes:
        This is a protocol decoder base class; specific protocols must extend it.
        Callbacks are triggered in IRQ context; must be fast and safe.
    """

    Timer_id = -1  # Software timer but enable override
    # Result/error codes
    REPEAT = -1
    BADSTART = -2
    BADBLOCK = -3
    BADREP = -4
    OVERRUN = -5
    BADDATA = -6
    BADADDR = -7

    def __init__(self, pin: Pin, nedges: int, tblock: int, callback, *args) -> None:
        """
        初始化红外接收对象。

        Args:
            pin (Pin): 用于接收红外信号的输入引脚。
            nedges (int): 需要捕获的边沿数量。
            tblock (int): 定时器超时周期（ms）。
            callback (function): 用户定义的回调函数，参数为 (cmd, addr, ext, *args)。
            *args: 传递给回调函数的额外参数。

        Notes:
            在初始化过程中会配置引脚中断和软件定时器。
            回调函数会在接收完成或错误时被调用。

        ==========================================

        Initialize IR receiver.

        Args:
            pin (Pin): Input pin for IR signal.
            nedges (int): Number of edges to capture.
            tblock (int): Timer timeout in ms.
            callback (function): User callback function (cmd, addr, ext, *args).
            *args: Extra arguments passed to callback.

        Notes:
            Pin IRQ and Timer are configured during init.
        """

        self._pin = pin
        self._nedges = nedges
        self._tblock = tblock
        self.callback = callback
        self.args = args
        self._errf = lambda _: None
        self.verbose = False

        self._times = array("i", (0 for _ in range(nedges + 1)))  # +1 for overrun
        pin.irq(handler=self._cb_pin, trigger=(Pin.IRQ_FALLING | Pin.IRQ_RISING))
        self.edge = 0
        self.tim = Timer(self.Timer_id)  # Default is software timer
        self.cb = self.decode

    def _cb_pin(self, line) -> None:
        """
        引脚中断回调，记录每个信号沿的时间戳。

        Args:
            line: 中断源（未使用）。

        Notes:
            首次触发中断时启动定时器。
            捕获的时间戳存入数组，用于后续解码。

        ==========================================

        Pin IRQ callback. Save timestamp of each edge.

        Args:
            line: IRQ source (unused).

        Notes:
            Timer starts on first edge.
            Timestamps stored in array.
        """

        t = ticks_us()
        if self.edge <= self._nedges:  # Allow 1 extra pulse to record overrun
            if not self.edge:  # First edge received
                self.tim.init(period=self._tblock, mode=Timer.ONE_SHOT, callback=self.cb)
            self._times[self.edge] = t
            self.edge += 1

    def do_callback(self, cmd: int, addr: int, ext: int, thresh: int = 0) -> None:

        """
        执行用户回调函数或错误处理函数。

        Args:
            cmd (int): 接收到的命令码或错误码。
            addr (int): 地址字段。
            ext (int): 扩展字段。
            thresh (int): 最小阈值，cmd 小于该值时视为错误。


        Notes:
            当 cmd >= thresh 时调用用户回调。
            否则调用错误处理函数。

        ==========================================

        Execute user callback or error function.

        Args:
            cmd (int): Command or error code.
            addr (int): Address field.
            ext (int): Extension field.
            thresh (int): Threshold. If cmd < thresh => error.

        Notes:
            Calls user callback if cmd valid, else error function.
        """
        self.edge = 0
        if cmd >= thresh:
            self.callback(cmd, addr, ext, *self.args)
        else:
            self._errf(cmd)

    def error_function(self, func) -> None:
        """
        设置错误处理回调函数。

        Args:
            func (function): 错误处理函数，参数为错误码。

        Notes:
            默认错误处理为空函数。
            用户可通过此方法自定义错误回调。

        ==========================================

        Set error handler function.

        Args:
            func (function): Error handler taking error code.

        Notes:
            Default is no-op. User can override.
        """
        self._errf = func

    def close(self) -> None:
        """
        关闭红外接收器，注销中断与定时器。

        Notes:
            调用后对象不再接收红外信号。
            需在不再使用时调用以释放硬件资源。

        ==========================================

        Close IR receiver. Disable IRQ and timer.

        Notes:
            Frees hardware resources.
        """
        self._pin.irq(handler=None)
        self.tim.deinit()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
