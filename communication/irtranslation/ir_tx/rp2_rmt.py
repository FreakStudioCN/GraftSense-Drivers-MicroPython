# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:13
# @Author  : 缪贵成
# @File    : rp2_rmt.py
# @Description : RP2 平台的 IR 发射驱动库,为上层协议提供接口
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, PWM
import rp2

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=32)
def pulsetrain():
    """
    生成高低脉冲序列（μs），用于 IR 信号发送。

    Notes:
        FIFO 中每个值表示高或低电平的持续时间（微秒）。
        autopull=True, pull_thresh=32 表示每次自动拉取 32 位数据。
        用于 IR 信号发送的脉冲序列，依赖 RP2 状态机执行。

    ==========================================

    Generate high/low pulse train (μs) for IR transmission.

    Notes:
        Each FIFO value represents the duration of a high or low pulse in microseconds.
        autopull=True, pull_thresh=32 means 32-bit data is automatically pulled per cycle.
        Used by RP2 state machine to output IR pulses.
    """
    wrap_target()
    out(x, 32)  # 高电平持续时间 (μs)
    irq(rel(0))
    set(pins, 1)  # 设置引脚高电平
    label("loop")
    jmp(x_dec, "loop")
    irq(rel(0))
    set(pins, 0)  # 设置引脚低电平
    out(y, 32)  # 低电平持续时间
    label("loop_lo")
    jmp(y_dec, "loop_lo")
    wrap()

@rp2.asm_pio(autopull=True, pull_thresh=32)
def irqtrain():
    """
    仅触发 IRQ 的 PIO 程序，用于空脉冲状态机驱动。

    Notes:
        自动从 FIFO 拉取 32 位数据。
        用于 RP2_RMT 空脉冲状态机，仅生成计时中断（IRQ）。

    ==========================================

    PIO program that only triggers IRQ for state machine control.

    Notes:
        Automatically pulls 32-bit data from FIFO.
        Used by RP2_RMT empty-pulse state machine to generate timing interrupts.
    """
    wrap_target()
    out(x, 32)  # 持续时间
    irq(rel(0))
    label("loop")
    jmp(x_dec, "loop")
    wrap()

# ======================================== 自定义类 ============================================

class DummyPWM:
    """
    虚拟 PWM 类，用于无载波时占位。

    Methods:
        duty_u16(_) -> None: 虚拟设置占空比，无实际作用。

    Notes:
        该类仅占位，不操作硬件。
        用于 RP2_RMT 在没有载波时保持接口一致性。

    ==========================================

    Dummy PWM class, placeholder when no carrier is used.

    Methods:
        duty_u16(_) -> None: Dummy method to set duty cycle.

    Notes:
        Placeholder, does not affect hardware.
        Used by RP2_RMT when no carrier is configured.
    """
    def duty_u16(self, _):
        """
        设置 PWM 占空比（无实际作用）。

        Args:
            _ : 占空比值，忽略。

        Notes:
            仅占位，不操作硬件
        ==========================================

        Set PWM duty cycle (dummy).

        Args:
            _ : duty value, ignored.

        Notes:
            Placeholder, does not affect hardware
        """
        pass

class RP2_RMT:
    """
       RP2 平台红外遥控仿真类，使用 PIO 状态机和可选 PWM 载波。

       Attributes:
           pwm (PWM/DummyPWM): PWM 实例，如果未提供载波则为 DummyPWM。
           duty (tuple of int): PWM 高低占空比。
           sm (StateMachine): RP2 状态机实例。
           apt (int): 当前数组索引，用于跟踪发送数据。
           arr (list/array): 当前发送的脉冲数组。
           ict (int or None): 当前 IRQ 计数。
           icm (int): STOP 指示索引，用于判断结束。
           reps (int): 重复次数，0 表示无限重复。

       Methods:
           send(ar, reps=1, check=True) -> None: 发送 IR 脉冲序列。
           busy() -> bool: 查询状态机是否忙。
           cancel() -> None: 取消正在发送的脉冲。

       Notes:
           该类仅适用于 RP2 (Raspberry Pi Pico) 平台。
           send 方法会启动状态机，非 ISR-safe，发送过程依赖 IRQ 回调。
           请确保发送数组以 STOP (0) 结尾。

       ==========================================

       RP2 IR remote emulation class using PIO state machine and optional PWM carrier.

       Attributes:
           pwm (PWM/DummyPWM): PWM instance, DummyPWM if no carrier is provided.
           duty (tuple of int): PWM high/low duty cycle.
           sm (StateMachine): RP2 state machine instance.
           apt (int): Current array pointer.
           arr (list/array): Current pulse array being sent.
           ict (int or None): Current IRQ count.
           icm (int): Index of STOP marker to indicate end.
           reps (int): Repeat count, 0 means infinite repetition.

       Methods:
           send(ar, reps=1, check=True) -> None: Send IR pulse sequence.
           busy() -> bool: Check if state machine is busy.
           cancel() -> None: Cancel ongoing pulse sending.

       Notes:
           This class is RP2 (Raspberry Pi Pico) specific.
           send() initiates the state machine, non ISR-safe, relies on IRQ callback.
           Ensure pulse arrays end with STOP (0) to terminate properly.
       """
    def __init__(self, pin_pulse=None, carrier=None, sm_no=0, sm_freq: int = 1_000_000) -> None:
        """
        初始化 RP2_RMT 对象。

        Args:
            pin_pulse (Pin, optional): 发送脉冲引脚。
            carrier (tuple, optional): (pin, freq, duty) 载波参数。
            sm_no (int, optional): 使用的状态机编号。
            sm_freq (int, optional): 状态机运行频率，默认 1MHz。

        Notes:
            如果 carrier 为 None，则使用 DummyPWM。
            根据 pin_pulse 选择 irqtrain 或 pulsetrain 状态机。
        ==========================================

        Initialize RP2_RMT object.

        Args:
            pin_pulse (Pin, optional): Pulse output pin.
            carrier (tuple, optional): (pin, freq, duty) carrier parameters.
            sm_no (int, optional): State machine number.
            sm_freq (int, optional): State machine frequency, default 1MHz.

        Notes:
            Uses DummyPWM if carrier is None.
            Selects irqtrain or pulsetrain based on pin_pulse.
        """
        if carrier is None:
            self.pwm = DummyPWM()
            self.duty = (0, 0)
        else:
            pin_car, freq, duty = carrier
            self.pwm = PWM(pin_car)
            self.pwm.freq(freq)
            self.pwm.duty_u16(0)
            self.duty = (int(0xFFFF * duty // 100), 0)
        if pin_pulse is None:
            self.sm = rp2.StateMachine(sm_no, irqtrain, freq=sm_freq)
        else:
            self.sm = rp2.StateMachine(sm_no, pulsetrain, freq=sm_freq, set_base=pin_pulse)
        self.apt = 0
        self.arr = None
        self.ict = None
        self.icm = 0
        self.reps = 0
        rp2.PIO(0).irq(handler=self._cb, trigger=1 << (sm_no + 8), hard=True)

    def _cb(self, pio) -> None:
        """
        IRQ 回调函数，用于填充 FIFO 并切换 PWM 占空比。

        Args:
            pio: 被触发的 PIO 对象。

        Notes:
            FIFO 数据为 μs 脉冲长度。
            STOP 后根据 reps 重复发送。
        ==========================================

        IRQ callback to feed FIFO and toggle PWM duty.

        Args:
            pio: triggered PIO object.

        Notes:
            FIFO values represent μs pulse duration.
            Repeats sequence if reps > 1.
        """
        if self.ict is not None:
            self.pwm.duty_u16(self.duty[self.ict & 1])
            self.ict += 1
            if d := self.arr[self.apt]:
                self.sm.put(d)
                self.apt += 1
            else:
                if r := self.reps != 1:
                    if r:
                        self.reps -= 1
                    self.sm.put(self.arr[0])
                    self.apt = 1
                    self.ict = 1

    def send(self, ar, reps: int = 1, check: bool = True) -> None:
        """
        发送脉冲序列。

        Args:
            ar (list/array): μs 脉冲数组，以 0 结尾。
            reps (int, optional): 重复发送次数，0 表示无限。
            check (bool, optional): 是否检查序列结尾。

        Notes:
            自动在数组结尾添加 STOP。
            确保脉冲序列以低电平结束，避免载波残留。
        ==========================================

        Send pulse sequence.

        Args:
            ar (list/array): μs pulse array, terminated with 0.
            reps (int, optional): number of repeats, 0 = forever.
            check (bool, optional): validate sequence ending.

        Notes:
            STOP is automatically appended.
            Ensure sequence ends with low level to avoid carrier remain.
        """
        self.sm.active(0)
        self.reps = reps
        ar[-1] = 0
        for x, d in enumerate(ar):
            if d == 0:
                break
        if check and x & 1:
            ar[x] = 1
            x += 1
            ar[x] = 0
        self.icm = x
        mv = memoryview(ar)
        n = min(x, 4)
        self.sm.put(mv[0:n])
        self.arr = ar
        self.apt = n
        self.ict = 0
        self.sm.active(1)

    def busy(self) -> bool:
        """
        检查 RMT 是否仍在发送中。

        Returns:
            bool: True 表示忙，False 表示空闲。

        Notes:
            根据 IRQ 计数判断。
        ==========================================

        Check if RMT is busy.

        Returns:
            bool: True if busy, False if idle.
        Notes:
            Determined from IRQ count.
        """
        if self.ict is None:
            return False
        return self.ict < self.icm

    def cancel(self) -> None:
        """
        取消发送，设置 reps=1。

        Notes:
            下一次 IRQ 将结束发送。
        ==========================================

        Cancel sending sequence.

        Notes:
            Next IRQ will terminate transmission.
        """
        self.reps = 1

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

