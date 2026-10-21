# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : FreakStudio
# @File    : mp34dt05.py
# @Description : MP34DT05 MEMS 麦克风 PDM 驱动（RP2040 PIO）
# @License : MIT
# flake8: noqa
# pylint: disable=undefined-variable,unsubscriptable-object

# ======================================== 导入相关模块 =========================================
import micropython

# 为 ISR 回调预留紧急异常缓冲区（100 字节）
micropython.alloc_emergency_exception_buf(100)

try:
    import rp2
except ImportError:
    raise ImportError("mp34dt05 requires RP2040 MicroPython firmware with rp2/PIO support")
import array
from uctypes import addressof
from machine import Pin
from micropython import const

# ======================================== 全局变量 ============================================
__version__ = "1.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"
# RP2040 PIO 依赖
__chip__ = "RP2040"

# ======================================== 功能函数 ============================================


# PIO PDM 采样程序
# PDM 时钟频率 3.072 MHz，每 8 个 PIO 步为一个 PDM 时钟周期
# 每次触发 IRQ 时产生 8 个 32-bit 样本字写入 RX FIFO
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.IN_LOW, fifo_join=rp2.PIO.JOIN_RX)
def _pio_sample() -> rp2.PIO:
    # 每次 IRQ 采样 8 个 32-bit 字
    set(y, 8)

    label("WORDSTART")
    # 每个字 32 bits（-2 用于循环优化）
    set(x, 30)

    label("SAMPLE")
    # 时钟引脚拉高
    set(pins, 1)[2]
    wrap_target()
    # 在时钟上升沿后 >105ns 采样数据引脚
    in_(pins, 1)
    # 输入数据进入 ISR
    # 时钟引脚拉低
    set(pins, 0)[2]
    # 循环采样
    jmp(x_dec, "SAMPLE")

    # 最后一个 bit 采样（比正常短 3 步，为 push/jmp/set 留时间）
    set(pins, 1)[2]
    in_(pins, 1)
    set(pins, 0)
    # 将 ISR 推入 RX FIFO（不阻塞）
    push(noblock)

    jmp(y_dec, "WORDSTART")
    # 触发 IRQ，主循环从 RX FIFO 读取
    irq(rel(0))

    # 重置计数器并循环回 WORDSTART，同时保持时序
    set(pins, 1)
    set(y, 8)
    set(x, 30)
    # 隐式 wrap（不消耗时钟周期）


# Arm Thumb 汇编：将 PDM 原始样本转换为 PCM 并存入活动缓冲区
# r0 = __raw_sample_buf（8 字数组）
# r1 = __data 数组（元数据/状态）
@micropython.asm_thumb
def _asm_store_pcm_sample(r0, r1) -> int:
    # r2 = 过载暂存变量

    # 初始化
    # r4 = 缓冲区 0 起始地址（__data[3]）
    ldr(r4, [r1, 12])
    # r2 = 获取活动缓冲区索引（__data[1]）
    ldr(r2, [r1, 4])
    # 如果 __buf0 是活动缓冲区
    cmp(r2, 0)
    # 跳过
    beq(BUF0)
    # 否则：r4 = 缓冲区 1 起始地址（__data[4]）
    ldr(r4, [r1, 16])
    label(BUF0)
    # r3 = 获取当前采样索引（__data[2]）
    ldr(r3, [r1, 8])
    # 加上缓冲区索引偏移
    add(r4, r4, r3)

    # 采样缓冲区循环（SBL）
    # r5 = 当前样本运行置位计数
    mov(r5, 0)
    # r6 = 8 字 __raw_sample_buf 的起始索引
    mov(r6, 0)
    # __raw_sample_buf 循环 开始
    label(SBL_START)
    # 8 * 4 字节字 = 32 位
    cmp(r6, 32)
    # 缓冲区结束？跳转到 __raw_sample_buf 循环 结束
    beq(SBL_END)

    # 采样循环
    # r2 = __raw_sample_buf 的地址
    mov(r2, r0)
    # 加上 __raw_sample_buf 索引
    add(r2, r2, r6)
    # r7 = 当前样本
    ldr(r7, [r2, 0])

    # Brian Kernighan 位计数法
    # https://developer.arm.com/documentation/ka002486/latest
    # 采样循环 开始
    label(SL_START)
    # 如果样本递减到零
    cmp(r7, 0)
    # 跳转到采样循环 结束
    beq(SL_END)
    # 增加样本置位计数
    add(r5, 1)
    # r2 = 样本的临时副本
    mov(r2, r7)
    # 减 1（翻转最低有效位）
    sub(r2, 1)
    # 从样本中移除最低有效位
    and_(r7, r2)
    # 跳转回采样循环 开始
    b(SL_START)

    # 采样循环 结束
    label(SL_END)
    # 增加采样计数器一个字
    add(r6, 4)
    # 跳转到 __raw_sample_buf 循环 开始
    b(SBL_START)

    # 采样缓冲区循环 结束
    label(SBL_END)

    # 将采样置位计数存储到活动缓冲区的 buf[index] 位置
    # buf 是字节数组
    strb(r5, [r4, 0])

    # 递增并存储缓冲区索引
    # r2 = buf_len
    ldr(r2, [r1, 0])
    # 递增索引
    add(r3, 1)
    # 索引是否等于 buf_len？
    cmp(r3, r2)
    # 跳转到 SKIP_RESET
    bne(SKIP_RESET)
    # 重新初始化索引 = 0
    mov(r3, 0)

    # 交换缓冲区
    # r2 = 获取活动缓冲区索引（待翻转）
    ldr(r2, [r1, 4])
    cmp(r2, 0)
    # 如果缓冲区 0 不是活动缓冲区
    beq(BUF1)
    # 将缓冲区 0 设为活动
    mov(r2, 0)
    b(UPD_BUF)
    label(BUF1)
    # 否则：将缓冲区 1 设为活动
    mov(r2, 1)
    label(UPD_BUF)
    # 存储活动缓冲区索引
    str(r2, [r1, 4])

    label(SKIP_RESET)
    # 将 buf 索引存储回 __data
    str(r3, [r1, 8])


# ======================================== 自定义类 ============================================
class MP34DT05:
    """
    MP34DT05 MEMS 麦克风 PDM 驱动类（RP2040 PIO）
    Attributes:
        _sm (StateMachine): RP2040 PIO 状态机实例
        _raw_sample_buf (array): 原始 8 字采样缓冲区
        _buf0 (array): 双缓冲区 0（PCM 样本）
        _buf1 (array): 双缓冲区 1（PCM 样本）
        _data (array): 控制/元数据数组
        _active_buf (int): ISR 正在写入的缓冲区索引
        _buffer_handler (callable): 缓冲区就绪回调
        _debug (bool): 调试日志开关
        _active (bool): 采样运行状态
    Methods:
        start(): 启动 PDM 采样
        stop(): 停止 PDM 采样
        get_buffer(): 获取指定索引的缓冲区
        deinit(): 释放硬件资源
    Notes:
        - 仅支持 RP2040（依赖 PIO 和 Arm Thumb 汇编）
        - 使用双缓冲机制进行连续 PDM 采样
        - PDM 时钟频率：3.072 MHz
        - 缓冲区就绪时通过 micropython.schedule 回调用户 handler
    ==========================================
    MP34DT05 MEMS microphone PDM driver (RP2040 PIO).
    Attributes:
        _sm (StateMachine): RP2040 PIO state machine instance
        _raw_sample_buf (array): Raw 8-word sample buffer
        _buf0 (array): Double buffer 0 (PCM samples)
        _buf1 (array): Double buffer 1 (PCM samples)
        _data (array): Control/metadata array
        _active_buf (int): Buffer index ISR is writing to
        _buffer_handler (callable): Buffer ready callback
        _debug (bool): Debug log switch
        _active (bool): Sampling running state
    Methods:
        start(): Start PDM sampling
        stop(): Stop PDM sampling
        get_buffer(): Get buffer by index
        deinit(): Release hardware resources
    Notes:
        - RP2040 only (requires PIO and Arm Thumb assembly)
        - Uses double-buffering for continuous PDM sampling
        - PDM clock frequency: 3.072 MHz
        - Dispatches user handler via micropython.schedule when buffer is ready
    """

    # PDM 时钟频率（Hz）
    PDM_CLOCK_FREQ = const(3_072_000)
    # 每个 PDM 时钟周期的 PIO 步数
    PIO_STEPS = const(8)
    # 原始采样缓冲区大小（8 个 32-bit 字，与 RX FIFO 大小匹配）
    RAW_BUF_SIZE = const(8)

    def __init__(self, pdm_clk: Pin, pdm_data: Pin, handler=None, sm_id: int = 0, buf_len: int = 1024, debug: bool = False) -> None:
        """
        初始化 MP34DT05 麦克风驱动
        Args:
            pdm_clk (Pin): PDM 时钟引脚（输出）
            pdm_data (Pin): PDM 数据引脚（输入）
            handler (callable): 缓冲区就绪回调函数，接收签名 handler(buf_index: int)
            sm_id (int): PIO 状态机 ID（0~7），默认 0
            buf_len (int): 每个采样缓冲区的字节长度，默认 1024
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型错误或超出范围
        Notes:
            - 初始化后需调用 start() 开始采样
            - 缓冲区就绪时通过 micropython.schedule 非阻塞回调 handler
            - ISR-safe: 否
        ==========================================
        Initialize MP34DT05 microphone driver.
        Args:
            pdm_clk (Pin): PDM clock pin (output)
            pdm_data (Pin): PDM data pin (input)
            handler (callable): Buffer ready callback, signature handler(buf_index: int)
            sm_id (int): PIO state machine ID (0~7), default 0
            buf_len (int): Byte length of each sample buffer, default 1024
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type or out of range
        Notes:
            - Call start() after init to begin sampling
            - Dispatches handler via micropython.schedule (non-blocking) when buffer ready
            - ISR-safe: No
        """
        # 参数校验：检查 pdm_clk 是否为 Pin 实例
        if not hasattr(pdm_clk, "value"):
            raise ValueError("pdm_clk must be a Pin instance")
        # 参数校验：检查 pdm_data 是否为 Pin 实例
        if not hasattr(pdm_data, "value"):
            raise ValueError("pdm_data must be a Pin instance")
        # 参数校验：检查 sm_id 类型和范围
        if not isinstance(sm_id, int):
            raise ValueError("sm_id must be int, got %s" % type(sm_id))
        if sm_id < 0 or sm_id > 7:
            raise ValueError("sm_id must be 0~7, got %d" % sm_id)
        # 参数校验：检查 buf_len 类型和范围
        if not isinstance(buf_len, int):
            raise ValueError("buf_len must be int, got %s" % type(buf_len))
        if buf_len < 1:
            raise ValueError("buf_len must be >= 1, got %d" % buf_len)
        # 参数校验：检查 debug 类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))
        # 参数校验：检查 handler 是否为可调用对象或 None
        if handler is not None and not callable(handler):
            raise ValueError("handler must be callable or None")

        self._debug = debug
        self._active = False
        self._buffer_handler = handler
        self._active_buf = 0
        self._pdm_ready = False

        # 初始化 8 字原始采样缓冲区（PIO RX FIFO 一次读取 8 字）
        self._raw_sample_buf = array.array("I", [0 for _ in range(self.RAW_BUF_SIZE)])

        # 初始化双 PCM 采样缓冲区
        self._buf0 = array.array("B", [0 for _ in range(buf_len)])
        self._buf1 = array.array("B", [0 for _ in range(buf_len)])

        # 初始化元数据/控制数组
        # [0] = 缓冲区长度，[1] = 活动缓冲区索引，[2] = 当前采样索引
        # [3] = 缓冲区 0 起始地址，[4] = 缓冲区 1 起始地址
        self._data = array.array(
            "I",
            [
                buf_len,
                0,
                0,
                addressof(self._buf0),
                addressof(self._buf1),
            ],
        )

        # 初始化 PIO 状态机
        # PIO 频率 = PDM 时钟频率 * 每周期步数 = 3.072 MHz * 8 = 24.576 MHz
        self._sm = rp2.StateMachine(
            sm_id,
            _pio_sample,
            freq=self.PDM_CLOCK_FREQ * self.PIO_STEPS,
            set_base=pdm_clk,
            in_base=pdm_data,
        )

        # 注册 IRQ 处理器（使用软中断，hard=True 可能导致死锁）
        self._sm.irq(handler=self._irq_handler)

        self._log("initialized on SM%d, buf_len=%d" % (sm_id, buf_len))

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 _debug=True 时输出
            - ISR-safe: 是（仅读取实例变量）
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug=True
            - ISR-safe: Yes (reads instance variable only)
        """
        if self._debug:
            print("[MP34DT05] %s" % msg)

    def start(self) -> None:
        """
        启动 PDM 采样
        Notes:
            - 激活 PIO 状态机，开始 PDM 采样和 PCM 转换
            - 缓冲区就绪时通过 micropython.schedule 回调 handler
            - ISR-safe: 否
            - 重复调用安全（仅首次激活状态机）
        ==========================================
        Start PDM sampling.
        Notes:
            - Activates PIO state machine to begin PDM sampling and PCM conversion
            - Dispatches handler via micropython.schedule when buffer is ready
            - ISR-safe: No
            - Safe to call repeatedly (activates state machine only once)
        """
        if not self._active:
            self._sm.active(True)
            self._active = True
            self._log("sampling started")

    def stop(self) -> None:
        """
        停止 PDM 采样
        Notes:
            - 停用 PIO 状态机，停止 PDM 采样
            - ISR-safe: 否
            - 重复调用安全
        ==========================================
        Stop PDM sampling.
        Notes:
            - Deactivates PIO state machine to stop PDM sampling
            - ISR-safe: No
            - Safe to call repeatedly
        """
        if self._active:
            self._sm.active(False)
            self._active = False
            self._log("sampling stopped")

    def get_buffer(self, idx: int) -> array.array:
        """
        获取指定索引的采样缓冲区
        Args:
            idx (int): 缓冲区索引号（0 或 1）
        Returns:
            array: 字节数组缓冲区
        Raises:
            ValueError: 索引号无效
        Notes:
            - ISR-safe: 否
            - handler 回调中传入的 buf_index 即为此处的 idx
            - 通常在 handler 中调用此方法获取非活动缓冲区数据进行处理
        ==========================================
        Get sample buffer by index.
        Args:
            idx (int): Buffer index (0 or 1)
        Returns:
            array: Byte array buffer
        Raises:
            ValueError: Invalid buffer index
        Notes:
            - ISR-safe: No
            - The buf_index passed to handler callback is the idx used here
            - Typically called in handler to get inactive buffer data for processing
        """
        # 参数校验：缓冲区索引必须为 0 或 1
        if not isinstance(idx, int):
            raise ValueError("idx must be int, got %s" % type(idx))
        if idx not in (0, 1):
            raise ValueError("idx must be 0 or 1, got %d" % idx)

        if idx == 0:
            return self._buf0
        return self._buf1

    @property
    def is_active(self) -> bool:
        """
        获取采样运行状态
        Returns:
            bool: True 表示正在采样，False 表示已停止
        Notes:
            - ISR-safe: 是（仅读取实例变量）
        ==========================================
        Get sampling running state.
        Returns:
            bool: True if sampling, False if stopped
        Notes:
            - ISR-safe: Yes (reads instance variable only)
        """
        return self._active

    def deinit(self) -> None:
        """
        释放硬件资源
        停止采样并释放 PIO 状态机。
        Notes:
            - ISR-safe: 否
            - 调用后设备不可再使用
            - 清除 IRQ 处理器以解除引用循环
        ==========================================
        Release hardware resources.
        Stops sampling and releases PIO state machine.
        Notes:
            - ISR-safe: No
            - Device is unusable after calling
            - Clears IRQ handler to break reference cycle
        """
        self._log("deinitializing MP34DT05")
        # 停止状态机
        if self._active:
            self._sm.active(False)
            self._active = False
        # 清除 IRQ 处理器
        try:
            self._sm.irq(handler=None)
        except Exception:
            pass

    def _irq_handler(self, p) -> None:
        """PIO IRQ only records that FIFO work is pending."""
        self._pdm_ready = True

    def _process_pdm_ready(self):
        """Process at most one FIFO item outside the PIO IRQ context."""
        if not self._sm.rx_fifo():
            return False
        self._sm.get(self._raw_sample_buf)
        _asm_store_pcm_sample(self._raw_sample_buf, self._data)
        if self._active_buf != self._data[1]:
            if self._buffer_handler:
                self._buffer_handler(self._active_buf)
            self._active_buf = self._data[1]
        return True
# ========================================  主程序  ===========================================
