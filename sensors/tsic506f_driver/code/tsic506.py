# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/07 11:00
# @Author  : Robert Hammelrath
# @File    : tsic506.py
# @Description : TSIC506F PIO driver on RP2040 one-wire bus
# @License : MIT
# flake8: noqa
# pylint: disable=undefined-variable,unsubscriptable-object

# ======================================== 导入相关模块 =========================================
import micropython

from array import array
from machine import Pin, disable_irq, enable_irq
from micropython import alloc_emergency_exception_buf, const

# 为 ISR 回调预留紧急异常缓冲区（100 字节）
alloc_emergency_exception_buf(100)

try:
    import rp2
except ImportError:
    raise ImportError("tsic506 requires RP2040 MicroPython firmware with rp2/PIO support")

# ======================================== 全局变量 ============================================
__version__ = "1.0.0"
__author__ = "Robert Hammelrath"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"
# RP2040 PIO 依赖
__chip__ = "RP2040"

_HAS_SCHEDULE = hasattr(micropython, "schedule")
_HAS_NATIVE = hasattr(micropython, "native")
_HAS_VIPER = hasattr(micropython, "viper")

# ======================================== 功能函数 ============================================


def _identity(function: callable) -> callable:
    """在缺少 native/viper 装饰器时保持函数原样。"""
    return function


_native = micropython.native if _HAS_NATIVE else _identity
_viper = micropython.viper if _HAS_VIPER else _identity


def _log(enabled: bool, msg: str) -> None:
    """
    输出调试日志
    Args:
        enabled (bool): 是否启用调试输出
        msg (str): 日志内容
    Raises:
        ValueError: 参数类型错误
    Notes:
        - 默认关闭，避免无条件打印
    """
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be bool, got %s" % type(enabled))
    if not isinstance(msg, str):
        raise ValueError("msg must be str, got %s" % type(msg))
    if enabled:
        print("[TSIC506F] %s" % msg)


@rp2.asm_pio(autopush=True, push_thresh=32)
def _count_pulse_len() -> rp2.PIO:
    # 初始化计数为 0
    set(x, 0)
    # 等待数据线拉低
    wait(0, pin, 0)
    label("falling")
    jmp(x_dec, "next")
    label("next")
    # 数据线为低时继续计数，为高时跳出循环
    jmp(pin, "leapfrog")
    jmp("falling")
    label("leapfrog")
    # 将脉冲长度推送到 RX FIFO，并触发 IRQ
    in_(x, 32)
    irq(rel(0))


@rp2.asm_pio(autopush=True, push_thresh=32)
def _detect_long_pulse() -> rp2.PIO:
    # 重置长脉冲判断计数器
    label("reset_countdown")
    set(x, 31)
    wait(1, pin, 0)
    label("not_long_enough")
    # 检测数据线是否过早变为低电平
    jmp(pin, "leapfrog")
    jmp("reset_countdown")
    label("leapfrog")
    # 继续倒数，确认长脉冲；等待下一帧开始
    jmp(x_dec, "not_long_enough")[13]
    irq(rel(0))
    wait(0, pin, 0)


# ======================================== 自定义类 ============================================


class TSIC506FNotRunning(Exception):
    """Raised when temperature reading is requested before state machines start."""


class TSIC506FWrongParity(Exception):
    """Raised when TSIC506F parity check fails."""


# 保留旧异常别名，兼容旧示例
ZACwireNotRunning = TSIC506FNotRunning
ZACwireWrongParity = TSIC506FWrongParity


class TSIC506F:
    """
    TSIC506F 高精度温度传感器驱动类（RP2040 PIO）
    Attributes:
        _pin (Pin): 数据引脚实例
        _sm0 (StateMachine): 脉冲长度采集状态机
        _sm1 (StateMachine): 长脉冲检测状态机
        _rawT (memoryview): 原始温度环形缓冲区
        errorcount (int): 累计解码错误数
        timeout_counter (int): 连续错误计数
        timeout_limit (int): 连续错误阈值
        dropped_frames (int): 因帧不完整或调度背压丢弃的帧数
    Methods:
        T(): 获取滤波后的摄氏温度
        decode(): 解码一帧 ZACwire 数据
        start(): 启动状态机
        stop(): 停止状态机
        deinit(): 释放硬件资源
    Notes:
        - 仅支持 RP2040，依赖 rp2.PIO
        - 使用双状态机分别采集脉宽和检测帧起始长脉冲
        - 解码在 micropython.schedule 调度的主上下文中执行
    ==========================================
    TSIC506F high precision temperature sensor driver (RP2040 PIO).
    Attributes:
        _pin (Pin): Data pin instance
        _sm0 (StateMachine): Pulse length acquisition state machine
        _sm1 (StateMachine): Long pulse detection state machine
        _rawT (memoryview): Raw temperature ring buffer
        errorcount (int): Total decode error count
        timeout_counter (int): Continuous error counter
        timeout_limit (int): Continuous error threshold
        dropped_frames (int): Frames discarded due to incomplete data or scheduling backpressure
    Methods:
        T(): Get filtered temperature in Celsius
        decode(): Decode one ZACwire frame
        start(): Start state machines
        stop(): Stop state machines
        deinit(): Release hardware resources
    Notes:
        - RP2040 only, requires rp2.PIO
        - Uses two state machines to acquire pulse widths and detect frame start long pulse
        - Decode runs in main context scheduled by micropython.schedule
    """

    BUFLEN = const(20)
    BITLEN = const(20)
    T_SCALE = const(2047)
    SM0_FREQ = const(3_000_000)
    SM1_FREQ = const(100_000)

    __slots__ = (
        "_pin",
        "_filter",
        "_sample_count",
        "errorcount",
        "buflen",
        "_buf_pos",
        "bitlen",
        "timeout_counter",
        "timeout_limit",
        "buf",
        "savedbuf",
        "bits",
        "rawT",
        "_buf",
        "_savedbuf",
        "_bits",
        "_rawT",
        "_sm0",
        "_sm1",
        "_count_callback",
        "_detect_callback",
        "_decode_callback",
        "_decode_pending",
        "_buffer_overflow",
        "dropped_frames",
        "_debug",
        "_startup_frames",
        "_startup_count",
    )

    def __init__(
        self,
        pin: Pin,
        sm: tuple = (0, 1),
        start: bool = False,
        filter: int = 1,
        startup_frames: int = 1,
        timeout: int = 4,
        debug: bool = False,
    ) -> None:
        """
        初始化 TSIC506F 驱动实例
        Args:
            pin (Pin): 传感器数据引脚实例
            sm (tuple): 两个 PIO 状态机编号
            start (bool): 是否立即启动状态机
            filter (int): 中值滤波窗口大小，必须 >= 1
            startup_frames (int): 上电后丢弃的初始有效帧数
            timeout (int): 允许的连续解码错误次数
            debug (bool): 是否启用调试日志
        Raises:
            ValueError: 参数类型或取值错误
        Notes:
            - 初始化后需调用 start() 开始采集（start=True 除外）
            - ISR-safe: 否
        ==========================================
        Initialize TSIC506F driver instance.
        Args:
            pin (Pin): Sensor data pin instance
            sm (tuple): Two PIO state machine ids
            start (bool): Start state machines immediately
            filter (int): Median filter window size, must be >= 1
            startup_frames (int): Initial valid frames to discard after power-up
            timeout (int): Allowed continuous decode errors
            debug (bool): Enable debug logging
        Raises:
            ValueError: Invalid parameter type or value
        Notes:
            - Call start() after init unless start=True
            - ISR-safe: No
        """
        # 参数校验：数据引脚必须是 Pin 实例
        if not hasattr(pin, "value"):
            raise ValueError("pin must be a Pin instance")
        # 参数校验：sm 必须是包含两个 int 的元组
        if not isinstance(sm, tuple) or len(sm) != 2:
            raise ValueError("sm must be a tuple with two items")
        for sm_id in sm:
            if not isinstance(sm_id, int):
                raise ValueError("sm ids must be int, got %s" % type(sm_id))
            if sm_id < 0:
                raise ValueError("sm ids must be >= 0")
        # 参数校验：start 必须是布尔值
        if not isinstance(start, bool):
            raise ValueError("start must be bool, got %s" % type(start))
        # 参数校验：filter 必须是正整数
        if not isinstance(filter, int) or filter < 1:
            raise ValueError("filter must be an int >= 1")
        # 参数校验：startup_frames 必须是非负整数
        if not isinstance(startup_frames, int) or startup_frames < 0:
            raise ValueError("startup_frames must be an int >= 0")
        # 参数校验：timeout 必须是正整数
        if not isinstance(timeout, int) or timeout < 1:
            raise ValueError("timeout must be an int >= 1")
        # 参数校验：debug 必须是布尔值
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._pin = pin
        self._filter = filter
        self._sample_count = 0
        self._startup_frames = startup_frames
        self._startup_count = 0
        self.errorcount = -1
        self.buflen = self.BUFLEN
        self._buf_pos = 0
        self.bitlen = self.BITLEN
        self.timeout_counter = 0
        self.timeout_limit = timeout
        self._decode_pending = False
        self._buffer_overflow = False
        self.dropped_frames = 0
        self._debug = debug

        # 预分配缓冲区，避免在中断调度路径中分配内存
        self.buf = array("l", [0] * self.buflen)
        self.savedbuf = array("l", [0] * self.buflen)
        self.bits = array("i", [0] * self.bitlen)
        self.rawT = array("f", [0.0] * self._filter)

        self._buf = memoryview(self.buf)
        self._savedbuf = memoryview(self.savedbuf)
        self._bits = memoryview(self.bits)
        self._rawT = memoryview(self.rawT)

        # 初始化两个 PIO 状态机
        self._sm0 = rp2.StateMachine(
            sm[0],
            _count_pulse_len,
            in_base=self._pin,
            jmp_pin=self._pin,
            freq=self.SM0_FREQ,
        )
        self._sm1 = rp2.StateMachine(
            sm[1],
            _detect_long_pulse,
            in_base=self._pin,
            jmp_pin=self._pin,
            freq=self.SM1_FREQ,
        )

        # 预绑定具名回调，避免在 ISR 路径中创建匿名函数对象
        self._count_callback = self._create_count_callback()
        self._detect_callback = self._create_detect_callback()
        self._decode_callback = self._create_decode_callback()
        self._sm0.irq(handler=self._count_callback)
        self._sm1.irq(handler=self._detect_callback)

        _log(self._debug, "initialized on pin=%s sm=%s" % (pin, sm))

        if start:
            self.start()

    def _create_count_callback(self) -> callable:
        """创建状态机 0 的具名预绑定 IRQ 回调。"""

        def count_callback(_state_machine: object) -> None:
            self._irq_count()

        return count_callback

    def _create_detect_callback(self) -> callable:
        """创建状态机 1 的具名预绑定 IRQ 回调。"""

        def detect_callback(_state_machine: object) -> None:
            self._irq_detect()

        return detect_callback

    def _create_decode_callback(self) -> callable:
        """创建 micropython.schedule 使用的具名预绑定回调。"""

        def decode_callback(_arg: int) -> None:
            self._scheduled_decode()

        return decode_callback

    @_viper
    def _irq_count(self) -> None:
        """
        保存状态机 0 读取到的脉冲长度计数。
        Notes:
            - ISR-safe: 是
        """
        # 始终读取 FIFO，防止溢出后 PIO 接收 FIFO 堵塞
        pulse_length = int(self._sm0.get())
        buffer_position = int(self._buf_pos)

        # 仅在预分配缓冲区有容量时写入，避免 IRQ 中发生数组越界
        if buffer_position < int(self.buflen):
            self._buf[buffer_position] = pulse_length
            self._buf_pos = buffer_position + 1
        else:
            # 当前帧已无空间，等待长脉冲帧边界后整体丢弃并恢复
            self._buffer_overflow = True

    @_native
    def _irq_detect(self) -> None:
        """
        备份当前帧数据，并在主上下文中调度解码。
        Notes:
            - ISR-safe: 是（只复制完整帧并调度，不执行解码或阻塞操作）
        """
        # 溢出或非完整帧不可解码；在帧边界复位后等待下一完整帧
        if self._buffer_overflow or int(self._buf_pos) != int(self.buflen):
            self._buffer_overflow = False
            self._buf_pos = 0
            self.dropped_frames = int(self.dropped_frames) + 1
            return

        # 已有解码任务在等待或执行时合并新帧，保护已备份的数据不被覆盖
        if self._decode_pending:
            self._buf_pos = 0
            self.dropped_frames = int(self.dropped_frames) + 1
            return

        # 仅复制完整帧，避免主上下文读取 ISR 正在填充的采集缓冲区
        self._savedbuf[:] = self._buf[:]
        self._buf_pos = 0
        self._decode_pending = True

        if _HAS_SCHEDULE:
            try:
                micropython.schedule(self._decode_callback, 0)
            except RuntimeError:
                # 调度队列已满时撤销 pending 标志，并记录本帧被丢弃
                self._decode_pending = False
                self.dropped_frames = int(self.dropped_frames) + 1
        else:
            # 无 schedule 时只设置待处理标志，由 T() 在主循环中处理
            pass

    @_native
    def _scheduled_decode(self) -> None:
        """
        在主上下文中清除调度标志并解码已备份帧。
        Notes:
            - ISR-safe: 否
        """
        # 共享标志由 IRQ 和主上下文共同访问，短暂关闭 IRQ 保证读写原子性
        irq_state = disable_irq()
        self._decode_pending = False
        enable_irq(irq_state)
        self.decode()

    def T(self) -> float:
        """
        获取滤波后的摄氏温度
        Returns:
            float: 温度值（℃）
        Raises:
            TSIC506FNotRunning: 状态机未运行或尚无有效采样
        Notes:
            - ISR-safe: 否
            - 使用中值滤波抑制偶发抖动
        ==========================================
        Get filtered temperature in Celsius.
        Returns:
            float: Temperature in Celsius
        Raises:
            TSIC506FNotRunning: State machines are not running or no valid sample yet
        Notes:
            - ISR-safe: No
            - Uses median filter to suppress occasional jitter
        """
        if not self._sm0.active():
            raise TSIC506FNotRunning("TSIC506F state machines are not running")

        # 未提供 schedule() 的固件在读取时同步完成已挂起的解码
        if not _HAS_SCHEDULE:
            irq_state = disable_irq()
            decode_pending = self._decode_pending
            enable_irq(irq_state)
            if decode_pending:
                self._scheduled_decode()

        if self._sample_count == 0:
            raise TSIC506FNotRunning("No valid TSIC506F sample yet")

        # 只对已接收到的有效样本取中值，避免把未填满的 0 值当作温度
        sample_count = self._sample_count
        index = sample_count // 2
        return sorted(self.rawT[:sample_count])[index] / self.T_SCALE * 70.0 - 10.0

    @_native
    def decode(self) -> int:
        """
        解码一帧 ZACwire 数据并更新温度缓冲区
        Returns:
            int: 解码成功返回 1，奇偶校验失败返回 0
        Notes:
            - 通过 micropython.schedule 在主上下文调用，避免在 ISR 中执行复杂逻辑
            - ISR-safe: 否
        ==========================================
        Decode one ZACwire frame and update the temperature buffer.
        Returns:
            int: 1 when decoding succeeded, 0 on parity error
        Notes:
            - Called in main context via micropython.schedule to keep ISR light
            - ISR-safe: No
        """
        bits = self._bits
        buf2 = self._savedbuf
        threshold = int(buf2[0])

        # 根据参考脉冲宽度解码低半字节
        bits[6] = int(buf2[6]) > threshold
        bits[7] = int(buf2[7]) > threshold
        bits[8] = int(buf2[8]) > threshold
        bits[9] = int(buf2[9]) > threshold

        # 解码高字节数据位
        bits[11] = int(buf2[11]) > threshold
        bits[12] = int(buf2[12]) > threshold
        bits[13] = int(buf2[13]) > threshold
        bits[14] = int(buf2[14]) > threshold
        bits[15] = int(buf2[15]) > threshold
        bits[16] = int(buf2[16]) > threshold
        bits[17] = int(buf2[17]) > threshold
        bits[18] = int(buf2[18]) > threshold
        bits[19] = int(buf2[19]) > threshold

        # 校验高字节奇偶位
        parity = int(bits[11]) + int(bits[12]) + int(bits[13]) + int(bits[14]) + int(bits[15]) + int(bits[16]) + int(bits[17]) + int(bits[18])
        if (parity % 2) != int(bits[19]):
            self.timeout_counter = int(self.timeout_counter) + 1
            self.errorcount = int(self.errorcount) + 1
            if int(self.timeout_counter) >= int(self.timeout_limit):
                # 达到连续错误上限后只保留计数，不抛异常，避免打断调度流程
                return 0
            return 0

        # 校验低半字节奇偶位
        parity = int(bits[6]) + int(bits[7]) + int(bits[8])
        if (parity % 2) != int(bits[9]):
            self.timeout_counter = int(self.timeout_counter) + 1
            self.errorcount = int(self.errorcount) + 1
            if int(self.timeout_counter) >= int(self.timeout_limit):
                # 达到连续错误上限后只保留计数，不抛异常，避免打断调度流程
                return 0
            return 0

        # 组合 11 位温度原始值
        temperature_raw = (
            int(bits[18])
            | (int(bits[17]) << 1)
            | (int(bits[16]) << 2)
            | (int(bits[15]) << 3)
            | (int(bits[14]) << 4)
            | (int(bits[13]) << 5)
            | (int(bits[12]) << 6)
            | (int(bits[11]) << 7)
            | (int(bits[8]) << 8)
            | (int(bits[7]) << 9)
            | (int(bits[6]) << 10)
        )

        # 上电后的前几帧可能输出 0（对应 -10℃），直接丢弃，避免首值异常
        if self._startup_count < self._startup_frames:
            self._startup_count = self._startup_count + 1
            return 1

        self.timeout_counter = 0
        rawT = self._rawT
        index = int(len(rawT)) - 1
        if self._sample_count == 0:
            # 首帧填充全部历史窗口，避免输出默认空值
            while index >= 0:
                rawT[index] = int(temperature_raw)
                index = index - 1
            self._sample_count = 1
        else:
            # 新值写入窗口头部，旧值依次后移
            while index > 0:
                rawT[index] = rawT[index - 1]
                index = index - 1
            rawT[0] = int(temperature_raw)
            if self._sample_count < len(rawT):
                self._sample_count = self._sample_count + 1
        return 1

    def start(self) -> None:
        """
        启动传感器采集
        Notes:
            - ISR-safe: 否
        ==========================================
        Start sensor capture.
        Notes:
            - ISR-safe: No
        """
        self._sm0.active(True)
        self._sm1.active(True)
        _log(self._debug, "state machines started")

    def stop(self) -> None:
        """
        停止传感器采集
        Notes:
            - ISR-safe: 否
        ==========================================
        Stop sensor capture.
        Notes:
            - ISR-safe: No
        """
        self._sm0.active(False)
        self._sm1.active(False)
        _log(self._debug, "state machines stopped")

    def deinit(self) -> None:
        """
        释放 PIO 资源
        Notes:
            - 停止状态机并清除 IRQ 处理器
            - 调用后设备不可再使用
            - ISR-safe: 否
        ==========================================
        Release PIO resources.
        Notes:
            - Stops state machines and clears IRQ handlers
            - Device is unusable after calling
            - ISR-safe: No
        """
        self.stop()
        try:
            self._sm0.irq(handler=None)
        except Exception:
            pass
        try:
            self._sm1.irq(handler=None)
        except Exception:
            pass
        _log(self._debug, "resources released")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
