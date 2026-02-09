# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/18
# @Author  : zker         
# @File    : touchkey.py       
# @Description : 触控按键库函数

__version__ = "0.1.0"
__author__ = "zker"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython的引脚和定时器控制模块
from machine import Pin, Timer

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class TouchKey:
    """
        TouchButton 类用于控制机械或触摸按键，通过更改函数参数的值来更改闲置状态电平，

        Attributes:
            pin_num:用于控制片选引脚的GPIO对象。
            idle_stete:用于设置空闲状态电平（high = 1， low = 0）
            debounce_time:用于设置防抖电平（默认50ms）


        Methods:
             __init__(self, pin_num: int, idle_state: int, debounce_time: int=50, press_callback: callable=None, release_callback: callable=None):
                 初始化TouchKey实列，配置连接端口，空闲状态电平，防抖时间。
             _irq_handler(self, pin):
                 检测并配置定时器
             _debounce_handler(self):
                设置按键的防抖时间，范围为）到100
             get_state(self):
                状态获取函数

    ==========================================
        TouchButton Class is used Controls mechanical or touch buttons by modifying the idle state level through function parameter values.

        Attributes:
            pin_num: GPIO object for controlling the chip-select pin.
            idle_state: Sets the idle state level (high = 1, low = 0).
            debounce_time: Sets the debounce time (default: 50 ms).
            press_callback: Callback function triggered on button press.
            release_callback: Callback function triggered on button release.

    """
    high, low = (1, 0)

    def __init__(self, pin_num: int, idle_state: int, debounce_time: int=50, press_callback: callable=None, release_callback: callable=None):
        """
        初始化TouchButton 实列 。
        
        该实列用于控制机械或触摸按键，通过更改函数参数的值来更改闲置状态电平。
        
        Args:
            pin_num（int）:接收按键信号GPIO编号，用于提供输出信号
            idle_stete（int）:用于设置空闲状态电平（high = 1， low = 0）
            debounce_time（int）:用于设置防抖电平（默认50ms）
            press_callback：按下回调函数
            release_callback：松开回调函数
        
        Returns:
               None: 此方法没有返回值。
               
        Raises:     
                None: 该方法不抛出异常。
        
         =================================
         
        Initialize a TouchButton instance

        This instance is used to control mechanical or touch buttons by modifying the idle state level through function parameter values.

        Args:
            pin_num: GPIO object for controlling the chip-select pin.
            idle_ state: Sets the idle state level (high = 1, low = 0).
            debounce_time: Sets the debounce time (default: 50 ms).
            press_callback: Callback function triggered on button press.
            release_callback: Callback function triggered on button release.

        Returns:
            None: This method does not return any value.

        Raises:
            None: This method does not raise any exceptions.

        """
        # 对入口参数进行限定与判断
        if not isinstance(pin_num, int):
            print("The pin_num must be int ")
            return
        if idle_state not in (TouchKey.low, TouchKey.high):
            print("The idle_state must be low or high")
            return
        if not isinstance(debounce_time, int) or debounce_time <= 0 or debounce_time > 100:
            print("The debounce_time must be between 0 and 100")
            return

        # 初始化idle_state为入口参数
        self.idle_state = idle_state
        # 初始化debounce_time为入口参数
        self.debounce_time = debounce_time
        # 初始化press_callback为对应函数
        self.press_callback = press_callback
        # 初始化release_callback为对应函数
        self.release_callback = release_callback

        # 根据空闲状态配置引脚的上拉/下拉电阻
        pull = Pin.PULL_UP if idle_state == 1 else Pin.PULL_DOWN
        self.pin = Pin(pin_num, Pin.IN, pull)
        
        # 初始化稳定状态为当前实际引脚值
        self.last_stable_state = self.pin.value()
        
        # 配置双边缘触发中断
        self.pin.irq(
            #设置中断触发的条件
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            #定义中断发生时执行的函数
            handler=self._irq_handler
        )
        
        # 防抖定时器None表示未激活
        self.debounce_timer = None
 
    def _irq_handler(self, pin):
        """
        设置定时器相关参数。

        该方法用于设置定时器，若没有定时器则会生成虚拟定时器

         Args:
             pin(int):引脚编号,此值应该为MCU的合法有效数值

         Returns:
             None: 此方法没有返回值

        Raises:
            PinError:如果输入的值不是合法的数值，将抛出异常

        =====================================

        Set timer-related parameters

        This method configures the timer. If no physical timer exists, it creates a virtual timer.

        Args:
            pin (int): Pin number, which must be a valid and legal value for the MCU.

        Returns:
            None: This method does not return a value.

        Raises:
            PinError: Raised if the input value is invalid.
        """
        # 检查是否存在定时器，若参数不为None则执行销毁
        if self.debounce_timer:
            self.debounce_timer.deinit()
        # 建立虚拟定时器
        self.debounce_timer = Timer(-1)
        self.debounce_timer.init(
            # 设置等待时间
            period=self.debounce_time,
            # 单触发模式
            mode=Timer.ONE_SHOT,
            # 时间到后执行函数
            callback=lambda t: self._debounce_handler()
        )

    def _debounce_handler(self):
        """
        防抖时间结束执行

        该方法通过状态判断来检测按键是否被按下或者释放

        Args:
            None:这个方法没有参数

        :return:
            None:这个方法没有返回值

        =====================================
        Handle debounce completion

        This method checks the button state after the debounce time has elapsed to detect press or release events.

        Args:
            None: This method takes no arguments.

        Returns:
            None: This method returns no value.

        """
        current_value = self.pin.value()
        if current_value != self.last_stable_state:
            # 状态变化有效
            # 检测当前状态电平
            if current_value == self.idle_state:
                if self.release_callback:
                    # 松开回调
                    self.release_callback()
            else:
                if self.press_callback:
                    # 按下回调
                    self.press_callback()
            # 更新稳定状态记录
            self.last_stable_state = current_value
        self.debounce_timer = None


    def get_state(self):
        """
        此方法用于获取状态

        Args:
            None:这个方法没有参数

        Returns:
            idle_state:返回按键当前的电平状态

        =====================================
        Retrieves the current state

        This method is used to obtain the current electrical level state of the button.

        Args:
            None: This method takes no arguments.

        Returns:
            idle_state (int): Returns the current idle state level of the button 。

        """
        return self.last_stable_state != self.idle_state

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================