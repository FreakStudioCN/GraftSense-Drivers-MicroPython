# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:12
# @Author  : 缪贵成
# @File    : nec.py
# @Description : nec协议解码，包含三星nec变体
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC YB-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from time import ticks_diff
from machine import Pin
from . import IR_RX

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class NEC_ABC(IR_RX):
    """
    NEC 协议解码基类，用于标准 NEC、扩展 NEC 和 Samsung IR 信号的解码。

    Attributes:
        _extended (bool): 是否使用扩展地址模式。
        _addr (int): 最后一次解码得到的地址。
        _leader (int): 前导脉冲长度（微秒），Samsung 为 2.5ms，其他为 4ms。

    Methods:
        __init__(pin, extended, samsung, callback, *args) -> None:
            初始化 NEC_ABC 对象，设置引脚、扩展模式和 Samsung 模式。
        decode(_) -> None:
            解码捕获到的脉冲数据，并执行回调函数。

    Notes:
        该类用于处理 NEC、NEC扩展、Samsung 协议红外信号。
        decode 方法会自动调用 do_callback，将结果返回给用户回调。
        异常码包括 REPEAT、BADSTART、BADBLOCK、BADREP、OVERRUN、BADDATA、BADADDR。

    ==========================================

    NEC protocol base class for decoding standard NEC, extended NEC and Samsung IR signals.

    Attributes:
        _extended (bool): Extended address mode enabled.
        _addr (int): Last decoded address.
        _leader (int): Leader pulse duration in microseconds, 2.5ms for Samsung, 4ms otherwise.

    Methods:
        __init__(pin, extended, samsung, callback, *args) -> None:
            Initialize NEC_ABC object with pin, extended mode, and Samsung mode.
        decode(_) -> None:
            Decode captured pulse sequence and execute user callback.

    Notes:
        Handles NEC, extended NEC, and Samsung IR protocols.
        decode automatically calls do_callback to invoke user callback.
        Error codes include REPEAT, BADSTART, BADBLOCK, BADREP, OVERRUN, BADDATA, BADADDR.
    """

    def __init__(self, pin: Pin, extended: bool, samsung: bool, callback, *args) -> None:
        """
        初始化 NEC_ABC 对象。

        Args:
            pin (Pin): 接收 IR 信号的引脚。
            extended (bool): 是否使用扩展地址模式。
            samsung (bool): 是否为 Samsung 协议模式。
            callback (function): 用户回调函数，接收 cmd, addr, ext。
            *args: 可选附加参数传递给回调函数。

        Notes:
            初始化父类 IR_RX，设置边沿数 68，超时时间 80ms。
            根据 Samsung 模式选择前导脉冲长度。

        ==========================================

        Initialize NEC_ABC object.

        Args:
            pin (Pin): Input pin for IR signal.
            extended (bool): Enable extended address mode.
            samsung (bool): Samsung protocol mode.
            callback (function): User callback accepting cmd, addr, ext.
            *args: Optional extra arguments passed to callback.

        Notes:
            Initializes parent IR_RX with 68 edges and 80ms timeout.
            Sets leader pulse length according to Samsung mode.
        """
        super().__init__(pin, 68, 80, callback, *args)
        self._extended = extended
        self._addr = 0
        self._leader = 2500 if samsung else 4000

    def decode(self, _) -> None:
        """
        解码 NEC 或 Samsung 红外信号，并触发用户回调。

        Args:
            _ : 占位参数，由定时器回调传入，不使用。

        Raises:
            RuntimeError: 当捕获数据异常，如 REPEAT、BADSTART、BADBLOCK、BADREP、OVERRUN、BADDATA、BADADDR。

        Notes:
            decode 会解析边沿脉冲并计算地址和命令。
            根据 NEC 协议校验命令和地址完整性。
            异常情况下 cmd 会对应错误码，REPEAT 使用上次地址。
            成功解析后调用 do_callback 将结果返回用户回调。

        ==========================================

        Decode NEC or Samsung IR signal and invoke user callback.

        Args:
            _ : Placeholder argument from timer callback, unused.

        Raises:
            RuntimeError: When captured data is invalid, e.g., REPEAT, BADSTART, BADBLOCK, BADREP, OVERRUN, BADDATA, BADADDR.

        Notes:
            decode parses edge pulses to calculate address and command.
            Verifies command and address according to NEC protocol.
            On error, cmd corresponds to error code; REPEAT uses last address.
            Successfully decoded data triggers do_callback to invoke user callback.
        """
        try:
            if self.edge > 68:
                raise RuntimeError(self.OVERRUN)
            width = ticks_diff(self._times[1], self._times[0])
            if width < self._leader:
                raise RuntimeError(self.BADSTART)
            width = ticks_diff(self._times[2], self._times[1])
            if width > 3000:
                if self.edge < 68:
                    raise RuntimeError(self.BADBLOCK)
                val = 0
                for edge in range(3, 68 - 2, 2):
                    val >>= 1
                    if ticks_diff(self._times[edge + 1], self._times[edge]) > 1120:
                        val |= 0x80000000
            elif width > 1700:
                raise RuntimeError(self.REPEAT if self.edge == 4 else self.BADREP)
            else:
                raise RuntimeError(self.BADSTART)
            addr = val & 0xff
            cmd = (val >> 16) & 0xff
            if cmd != (val >> 24) ^ 0xff:
                raise RuntimeError(self.BADDATA)
            if addr != ((val >> 8) ^ 0xff) & 0xff:
                if not self._extended:
                    raise RuntimeError(self.BADADDR)
                addr |= val & 0xff00
            self._addr = addr
        except RuntimeError as e:
            cmd = e.args[0]
            addr = self._addr if cmd == self.REPEAT else 0
        self.do_callback(cmd, addr, 0, self.REPEAT)

class NEC_16(NEC_ABC):
    """
    NEC 16-bit 地址协议类。
    继承 NEC_ABC，固定扩展模式，非 Samsung 模式。

    Methods:
        __init__(pin: Pin, callback, *args) -> None: 初始化 NEC_16 对象。

    Notes:
        调用父类 NEC_ABC 初始化。
        适用于扩展 NEC 16-bit 地址红外信号解码。

    ==========================================

    NEC 16-bit address protocol class.

    Inherits NEC_ABC with fixed extended mode and non-Samsung mode.

    Methods:
        __init__(pin: Pin, callback, *args) -> None: Initialize NEC_16 object.

    Notes:
        Calls parent NEC_ABC to initialize.
        Suitable for extended NEC 16-bit address IR signal decoding.
    """

    def __init__(self, pin: Pin, callback, *args) -> None:
        """
        初始化 NEC_16 对象。
        Args:
            pin (Pin): IR 接收引脚。
            callback (function): 用户回调函数。
            *args: 附加参数传递给回调函数。

        Notes:
            调用父类 NEC_ABC 构造函数完成初始化。
            不会抛出异常。

        ==========================================

        Initialize NEC_16 object.

        Args:
            pin (Pin): IR input pin.
            callback (function): User callback function.
            *args: Extra arguments passed to callback.

        Notes:
            Calls parent NEC_ABC constructor to initialize.
            No exceptions are raised.
        """
        super().__init__(pin, True, False, callback, *args)


class SAMSUNG(NEC_ABC):
    """
    Samsung 协议类。

    继承 NEC_ABC，固定扩展模式和 Samsung 模式。

    Methods:
        __init__(pin: Pin, callback, *args) -> None: 初始化 SAMSUNG 对象。

    Notes:
        调用父类 NEC_ABC 初始化。
        适用于 Samsung 红外信号解码。

    ==========================================

    Samsung protocol class.

    Inherits NEC_ABC with fixed extended and Samsung mode.

    Methods:
        __init__(pin: Pin, callback, *args) -> None: Initialize SAMSUNG object.

    Notes:
        Calls parent NEC_ABC to initialize.
        Suitable for Samsung IR signal decoding.
    """

    def __init__(self, pin: Pin, callback, *args) -> None:
        """
        初始化 SAMSUNG 对象。

        Args:
            pin (Pin): IR 接收引脚。
            callback (function): 用户回调函数。
            *args: 附加参数传递给回调函数。

        Notes:
            调用父类 NEC_ABC 构造函数完成初始化。
            不会抛出异常。

        ==========================================

        Initialize SAMSUNG object.

        Args:
            pin (Pin): IR input pin.
            callback (function): User callback function.
            *args: Extra arguments passed to callback.

        Notes:
            Calls parent NEC_ABC constructor to initialize.
            No exceptions are raised.
        """
        super().__init__(pin, True, True, callback, *args)
class NEC_8(NEC_ABC):
    """
    NEC 8-bit 地址协议接收类。

    继承 NEC_ABC，实现固定非扩展模式和非 Samsung 模式的 NEC 协议接收。

    Attributes:
        _extended (bool): 是否为扩展模式，NEC_8 固定为 False。
        _addr (int): 当前接收的地址。
        _leader (int): 领导码长度，单位 μs，取决于 Samsung 模式，NEC_8 固定 4000。
        edge (int): 当前捕获的边沿数量（继承自 NEC_ABC）。
        _times (array): 捕获的脉冲时间数组（继承自 NEC_ABC）。
        verbose (bool): 调试信息开关（继承自 NEC_ABC）。

    Methods:
        __init__(pin: Pin, callback: function, *args) -> None:
            初始化 NEC_8 对象，设置固定模式和回调函数。
        decode(_) -> None:
            解析接收到的脉冲数据（继承自 NEC_ABC）。
        do_callback(cmd: int, addr: int, data: int, repeat: int) -> None:
            调用用户回调（继承自 NEC_ABC）。

    Notes:
        NEC_8 始终为 8-bit 地址模式。
        decode 方法会对收到的数据进行校验，错误时通过回调返回错误码。
        回调函数签名: func(cmd: int, addr: int, data: int, repeat: int)

    ==========================================

    NEC 8-bit address protocol receiver class.

    Inherits NEC_ABC, implements fixed non-extended and non-Samsung mode.

    Attributes:
        _extended (bool): Extended mode flag, fixed False for NEC_8.
        _addr (int): Currently received address.
        _leader (int): Leader pulse length in μs, fixed 4000 for NEC_8.
        edge (int): Number of captured edges (from NEC_ABC).
        _times (array): Captured pulse times (from NEC_ABC).
        verbose (bool): Debug output flag (from NEC_ABC).

    Methods:
        __init__(pin: Pin, callback: function, *args) -> None:
            Initialize NEC_8 object with fixed mode and user callback.
        decode(_) -> None:
            Decode received pulse data (from NEC_ABC).
        do_callback(cmd: int, addr: int, data: int, repeat: int) -> None:
            Call user callback (from NEC_ABC).

    Notes:
        NEC_8 always uses 8-bit address mode.
        decode method validates received data and reports errors via callback.
        Callback signature: func(cmd: int, addr: int, data: int, repeat: int)
    """

    def __init__(self, pin, callback, *args):
        """
        初始化 NEC_8 接收对象。

        Args:
            pin (Pin): 连接红外接收模块的 GPIO 引脚对象
            callback (function): 用户定义的回调函数，用于处理接收到的红外信号
            *args: 可选参数，传递给父类 NEC_ABC 的初始化方法

        Notes:
            NEC_8 固定为 8-bit 地址模式，非扩展模式，非 Samsung 模式
            回调函数签名一般为 func(cmd:int, addr:int, data:int, repeat:int)
            初始化会设置内部捕获缓冲、模式标志等
            继承自 NEC_ABC，所以 *args 会传给父类处理

        ==========================================

        Initialize NEC_8 IR receiver object.

        Args:
            pin (Pin): GPIO pin connected to the IR receiver
            callback (function): User-defined callback function to handle received IR signals
            *args: Optional arguments passed to parent class NEC_ABC __init__

        Notes:
            NEC_8 uses fixed 8-bit address mode, non-extended, non-Samsung
            Callback signature typically: func(cmd:int, addr:int, data:int, repeat:int)
            Initializes internal buffers and mode flags
            *args are forwarded to NEC_ABC parent initialization
        """

        super().__init__(pin, False, False, callback, *args)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
