# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-
# @Time    : 2025/4/18
# @Author  : hogeiha
# @File    : encoder_wheel_switch.py
# @Description : 拨轮开关库函数（适配Raspberry Pi Pico）

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, Timer

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class EncoderWheelSwitch:
    """
        EncoderWheelSwitch 类用于控制拨轮开关（UP/DOWN双引脚），支持防抖、中断触发、状态读取

        Attributes:
            pin_up: UP信号GPIO引脚编号
            pin_down: DOWN信号GPIO引脚编号
            debounce_ms: 消抖时间（默认20ms）
            idle_state: 空闲状态电平（high=1，low=0，默认high）

        Methods:
            __init__(self, pin_up: int, pin_down: int, debounce_ms: int = 20, idle_state: int = 1,
                     callback_up: callable = None, callback_down: callable = None):
                初始化拨轮开关实例，配置引脚、消抖时间、空闲电平、触发回调
            get_raw_state(self) -> tuple[bool, bool]:
                读取UP/DOWN引脚原始电平状态，返回(UP电平, DOWN电平)
            enable_irq(self) -> bool:
                开启UP/DOWN引脚中断（双边缘触发），返回开启是否成功
            disable_irq(self) -> bool:
                关闭UP/DOWN引脚中断，停止防抖定时器，返回关闭是否成功

    ==========================================
        EncoderWheelSwitch Class is used to control encoder wheel switch (UP/DOWN dual pins),
        supporting debounce, interrupt trigger and state reading.

        Attributes:
            pin_up: GPIO pin number for UP signal
            pin_down: GPIO pin number for DOWN signal
            debounce_ms: Debounce time (default 20ms)
            idle_state: Idle state level (high=1, low=0, default high)

        Methods:
            __init__(self, pin_up: int, pin_down: int, debounce_ms: int = 20, idle_state: int = 1,
                     callback_up: callable = None, callback_down: callable = None):
                Initialize encoder wheel switch instance, configure pins, debounce time, idle level and trigger callbacks
            get_raw_state(self) -> tuple[bool, bool]:
                Read raw level state of UP/DOWN pins, return (UP level, DOWN level)
            enable_irq(self) -> bool:
                Enable UP/DOWN pin interrupt (double edge trigger), return whether enabled successfully
            disable_irq(self) -> bool:
                Disable UP/DOWN pin interrupt, stop debounce timer, return whether disabled successfully
    """

    high, low = (1, 0)

    def __init__(self, pin_up: int, pin_down: int, debounce_ms: int = 20, idle_state: int = 1,
                 callback_up: callable = None, callback_down: callable = None):
        """
        初始化拨轮开关实例

        该实例用于控制双引脚拨轮开关，支持防抖和中断触发回调

        Args:
            pin_up (int): UP信号GPIO引脚编号
            pin_down (int): DOWN信号GPIO引脚编号
            debounce_ms (int): 消抖时间（默认20ms，范围1-100ms）
            idle_state (int): 空闲状态电平（high=1，low=0，默认high）
            callback_up (callable): UP引脚触发回调函数（无参数）
            callback_down (callable): DOWN引脚触发回调函数（无参数）

        Returns:
            None: 此方法无返回值

        Raises:
            None: 该方法不抛出异常，仅打印参数错误提示
        =====================================
        Initialize EncoderWheelSwitch instance

        This instance is used to control dual-pin encoder wheel switch, supporting debounce and interrupt trigger callbacks

        Args:
            pin_up (int): GPIO pin number for UP signal
            pin_down (int): GPIO pin number for DOWN signal
            debounce_ms (int): Debounce time (default 20ms, range 1-100ms)
            idle_state (int): Idle state level (high=1, low=0, default high)
            callback_up (callable): Callback function triggered by UP pin (no parameters)
            callback_down (callable): Callback function triggered by DOWN pin (no parameters)

        Returns:
            None: This method returns no value

        Raises:
            None: This method does not raise exceptions, only prints parameter error prompts
        """
        # 参数合法性校验
        if not isinstance(pin_up, int) or not isinstance(pin_down, int):
            print("pin_up and pin_down must be integer!")
            return
        if idle_state not in (self.high, self.low):
            print("idle_state must be high(1) or low(0)!")
            return
        if not isinstance(debounce_ms, int) or debounce_ms < 1 or debounce_ms > 100:
            print("debounce_ms must be integer between 1 and 100!")
            return

        # 基础参数初始化
        self.pin_up_num = pin_up
        self.pin_down_num = pin_down
        self.debounce_ms = debounce_ms
        self.idle_state = idle_state
        self.callback_up = callback_up
        self.callback_down = callback_down

        # 配置引脚（根据空闲状态设置上拉/下拉）
        pull = Pin.PULL_UP if idle_state == self.high else Pin.PULL_DOWN
        self.pin_up = Pin(pin_up, Pin.IN, pull)
        self.pin_down = Pin(pin_down, Pin.IN, pull)

        # 记录引脚稳定状态
        self.last_up_state = self.pin_up.value()
        self.last_down_state = self.pin_down.value()

        # 防抖定时器（虚拟定时器）
        self.debounce_timer_up = None
        self.debounce_timer_down = None

        # 中断启用标记
        self.irq_enabled = False

    def get_raw_state(self) -> tuple[bool, bool]:
        """
        读取UP/DOWN引脚原始电平状态

        Args:
            None: 无参数

        Returns:
            tuple[bool, bool]: (UP电平状态, DOWN电平状态)，True=高电平，False=低电平
        =====================================
        Read raw level state of UP/DOWN pins

        Args:
            None: No parameters

        Returns:
            tuple[bool, bool]: (UP level state, DOWN level state), True=high level, False=low level
        """
        up_state = bool(self.pin_up.value())
        down_state = bool(self.pin_down.value())
        return (up_state, down_state)

    def _debounce_handler_up(self, timer):
        """
        UP引脚防抖处理函数（定时器回调）
        =====================================
        UP pin debounce handler (timer callback)
        """
        current_state = self.pin_up.value()
        # 状态变化且非空闲状态时触发回调
        if current_state != self.last_up_state:
            if current_state != self.idle_state and self.callback_up:
                self.callback_up()
            self.last_up_state = current_state
        self.debounce_timer_up = None

    def _debounce_handler_down(self, timer):
        """
        DOWN引脚防抖处理函数（定时器回调）
        =====================================
        DOWN pin debounce handler (timer callback)
        """
        current_state = self.pin_down.value()
        # 状态变化且非空闲状态时触发回调
        if current_state != self.last_down_state:
            if current_state != self.idle_state and self.callback_down:
                self.callback_down()
            self.last_down_state = current_state
        self.debounce_timer_down = None

    def _irq_handler_up(self, pin):
        """
        UP引脚中断处理函数（触发防抖定时器）
        =====================================
        UP pin interrupt handler (trigger debounce timer)
        """
        if self.debounce_timer_up:
            self.debounce_timer_up.deinit()
        self.debounce_timer_up = Timer(-1)
        self.debounce_timer_up.init(
            period=self.debounce_ms,
            mode=Timer.ONE_SHOT,
            callback=self._debounce_handler_up
        )

    def _irq_handler_down(self, pin):
        """
        DOWN引脚中断处理函数（触发防抖定时器）
        =====================================
        DOWN pin interrupt handler (trigger debounce timer)
        """
        if self.debounce_timer_down:
            self.debounce_timer_down.deinit()
        self.debounce_timer_down = Timer(-1)
        self.debounce_timer_down.init(
            period=self.debounce_ms,
            mode=Timer.ONE_SHOT,
            callback=self._debounce_handler_down
        )

    def enable_irq(self) -> bool:
        """
        开启UP/DOWN引脚外部中断（双边缘触发）

        Returns:
            bool: 中断开启是否成功
        =====================================
        Enable UP/DOWN pin external interrupt (double edge trigger)

        Returns:
            bool: Whether interrupt is enabled successfully
        """
        try:
            # 配置双边缘触发中断
            self.pin_up.irq(
                trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                handler=self._irq_handler_up
            )
            self.pin_down.irq(
                trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                handler=self._irq_handler_down
            )
            self.irq_enabled = True
            return True
        except Exception as e:
            print(f"Enable IRQ failed: {e}")
            return False

    def disable_irq(self) -> bool:
        """
        关闭UP/DOWN引脚外部中断，停止防抖定时器

        Returns:
            bool: 中断关闭是否成功
        =====================================
        Disable UP/DOWN pin external interrupt, stop debounce timer

        Returns:
            bool: Whether interrupt is disabled successfully
        """
        try:
            # 停止防抖定时器
            if self.debounce_timer_up:
                self.debounce_timer_up.deinit()
                self.debounce_timer_up = None
            if self.debounce_timer_down:
                self.debounce_timer_down.deinit()
                self.debounce_timer_down = None

            # 关闭中断
            if self.irq_enabled:
                self.pin_up.irq(handler=None)
                self.pin_down.irq(handler=None)
                self.irq_enabled = False
            return True
        except Exception as e:
            print(f"Disable IRQ failed: {e}")
            return False

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
