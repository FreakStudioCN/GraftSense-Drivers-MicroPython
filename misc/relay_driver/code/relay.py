# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/28 下午3:00
# @Author  : 李清水
# @File    : main.py
# @Description : 单通道继电器控制类 RelayController，支持普通继电器和磁保持继电器两种类型，提供开关控制方法

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import Pin, Timer

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class RelayController:
    """
    RelayController类用于控制单通道继电器，支持普通继电器和磁保持继电器两种类型。

    Attributes:
        RELAY_TYPES (dict): 继电器类型字典，包含支持的继电器类型及其描述。
        pin1 (Pin): 控制引脚1 GPIO对象（普通继电器）或H桥IN1引脚 GPIO对象（磁保持继电器）。
        pin2 (Pin): 仅磁保持继电器需要，H桥IN2引脚 GPIO对象。
        _pulse_timer (Timer): 用于磁保持继电器脉冲控制的定时器对象。
        relay_type (str): 当前继电器类型('normal'或'latching')。

    Methods:
        __init__(relay_type: str, pin1: int, pin2: int = None) -> None:
            初始化继电器控制器，配置控制引脚和定时器。

        _reset_pins(timer: Timer = None) -> None:
            定时器回调函数，脉冲结束后复位所有引脚。

        on() -> None:
            吸合继电器（普通继电器给高电平，磁保持继电器发送短脉冲）。

        off() -> None:
            释放继电器（普通继电器给低电平，磁保持继电器发送反向短脉冲）。

        toggle() -> None:
            切换继电器状态（仅普通继电器可用）。

        deinit() -> None:
            释放资源，包括定时器和GPIO引脚。

        get_state() -> bool:
            获取继电器当前状态（仅普通继电器准确）。

    ==========================================

    The RelayController class is used to control single-channel relays, supporting both normal relays and latching relays.

    Attributes:
        RELAY_TYPES (dict): Dictionary of relay types, containing supported relay types and their descriptions.
        pin1 (Pin): GPIO object for control pin1 (normal relay) or H-bridge IN1 pin (latching relay).
        pin2 (Pin): Only required for latching relay, GPIO object for H-bridge IN2 pin.
        _pulse_timer (Timer): Timer object used for pulse control of latching relays.
        relay_type (str): Current relay type ('normal' or 'latching').

    Methods:
        __init__(relay_type: str, pin1: int, pin2: int = None) -> None:
            Initializes the relay controller, configures control pins and timer.

        _reset_pins(timer: Timer = None) -> None:
            Timer callback function that resets all pins after pulse ends.

        on() -> None:
            Energize the relay (high level for normal relay, short pulse for latching relay).

        off() -> None:
            De-energize the relay (low level for normal relay, reverse short pulse for latching relay).

        toggle() -> None:
            Toggle relay state (only available for normal relays).

        get_state() -> bool:
            Get current relay state (only accurate for normal relays).

        deinit() -> None:
            Release resources, including timer and GPIO pins.
    """
    # 类属性：继电器类型字典
    RELAY_TYPES = {
        # 普通单线圈继电器
        'normal': 'Standard single-coil relay',
        # 双稳态磁保持继电器(需H桥驱动)
        'latching': 'Bistable latching relay (requires H-bridge)'
    }

    def __init__(self, relay_type: str, pin1: int, pin2: int = None) -> None:
        """
        初始化继电器控制器。

        该方法用于初始化继电器控制器，根据继电器类型配置相应的控制引脚和定时器。

        Args:
            relay_type (str): 继电器类型，必须是 RELAY_TYPES 中的键值 ('normal' 或 'latching')。
            pin1 (int): 控制引脚1 GPIO编号（普通继电器）或H桥IN1引脚 GPIO编号（磁保持继电器）。
            pin2 (int, optional): 仅磁保持继电器需要，H桥IN2引脚 GPIO编号，默认为 None。

        Returns:
            None: 此方法没有返回值。

        Raises:
            ValueError: 如果 relay_type 不是 'normal' 或 'latching' 则抛出异常。
            ValueError: 如果 relay_type 为 'latching' 但未提供 pin2 则抛出异常。
            ValueError: 如果 pin1 或 pin2 不是整数则抛出异常。

        =================================

        Initializes the relay controller.

        This method initializes the relay controller, configuring the corresponding control pins and timer according to the relay type.

        Args:
            relay_type (str): Relay type, must be a key in RELAY_TYPES ('normal' or 'latching').
            pin1 (int): GPIO pin index for control pin1 (normal relay) or H-bridge IN1 pin (latching relay).
            pin2 (int, optional): Only required for latching relay, GPIO pin index for H-bridge IN2 pin, default is None.

        Returns:
            None: This method does not return any value.

        Raises:
            ValueError: If relay_type is not 'normal' or 'latching'.
            ValueError: If relay_type is 'latching' but pin2 is not provided.
            ValueError: If pin1 or pin2 is not an integer.
        """
        # 判断pin1和pin2是否为整数
        if not isinstance(pin1, int) or (pin2 is not None and not isinstance(pin2, int)):
            raise TypeError("pin1 and pin2 must be integers")

        self.relay_type = relay_type.lower()

        # 验证继电器类型
        if self.relay_type not in self.RELAY_TYPES:
            raise ValueError(f"Invalid relay type. Must be one of: {list(self.RELAY_TYPES.keys())}")

        # 初始化控制引脚
        self.pin1 = Pin(pin1, Pin.OUT)
        self.pin1.value(1)

        # 创建虚拟定时器用于非阻塞脉冲
        self._pulse_timer = Timer(-1)

        # 磁保持继电器需要两个引脚
        if self.relay_type == 'latching':
            if pin2 is None:
                raise ValueError("Latching relay requires both pin1 and pin2 for H-bridge control")
            self.pin2 = Pin(pin2, Pin.OUT)
            self.pin2.value(0)
            self.off()

        # 添加状态跟踪属性
        self._last_state = False

    def get_state(self) -> bool:
        """
        获取继电器当前状态。

        注意：对于普通继电器，返回实际引脚状态；对于磁保持继电器，返回最后一次设置的状态（可能不准确）。

        Args:
            None: 此方法不接受任何参数。

        Returns:
            bool: True表示吸合状态，False表示释放状态。

        Raises:
            None: 该方法不抛出异常。

        =================================

        Get current relay state.

        Note: For normal relays, returns actual pin state; for latching relays,
        returns last set state (may not be accurate).

        Args:
            None: This method does not accept any parameters.

        Returns:
            bool: True indicates energized state, False indicates de-energized state.

        Raises:
            None: This method does not raise any exceptions.
        """
        if self.relay_type == 'normal':
            return bool(not self.pin1.value())
        else:
            return self._last_state

    def _reset_pins(self, timer: Timer = None) -> None:
        """
        定时器回调函数：脉冲结束后复位所有引脚。

        该方法作为定时器回调函数，在脉冲结束后将所有控制引脚置为低电平。

        Args:
            timer (Timer, optional): 触发回调的定时器实例，默认为 None。

        Returns:
            None: 此方法没有返回值。

        Raises:
            None: 该方法不抛出异常。

        =================================

        Timer callback function: Reset all pins after pulse.

        This method serves as a timer callback function that resets all control pins to low level after the pulse ends.

        Args:
            timer (Timer, optional): The timer instance that triggered the callback, default is None.

        Returns:
            None: This method does not return any value.

        Raises:
            None: This method does not raise any exceptions.
        """
        self.pin1.value(0)
        if hasattr(self, 'pin2'):
            self.pin2.value(0)

    def on(self) -> None:
        """
        吸合继电器。

        该方法用于控制继电器吸合。对于普通继电器直接给低电平，对于磁保持继电器发送短脉冲。

        Args:
            None: 此方法不接受任何参数。

        Returns:
            None: 此方法没有返回值。

        Raises:
            None: 该方法不抛出异常。

        =================================

        Energize the relay.

        This method is used to control the relay to energize. For normal relays, it directly provides a high level,
        while for latching relays, it sends a short pulse.

        Args:
            None: This method does not accept any parameters.

        Returns:
            None: This method does not return any value.

        Raises:
            None: This method does not raise any exceptions.
        """
        if self.relay_type == 'normal':
            # 普通继电器直接给低电平
            self.pin1.value(0)
        else:
            # 磁保持继电器需要短脉冲
            # 取消已有定时器
            self._pulse_timer.deinit()
            # 先设置方向
            self.pin2.value(0)
            # 开始正向脉冲
            self.pin1.value(1)
            # 设置50ms后自动复位（非阻塞）
            self._pulse_timer.init(mode=Timer.ONE_SHOT,
                                   period=50,
                                   callback=self._reset_pins)
        self._last_state = True

    def off(self) -> None:
        """
        释放继电器。

        该方法用于控制继电器释放。对于普通继电器直接给高电平，对于磁保持继电器发送反向短脉冲。

        Args:
            None: 此方法不接受任何参数。

        Returns:
            None: 此方法没有返回值。

        Raises:
            None: 该方法不抛出异常。

        =================================

        De-energize the relay.

        This method is used to control the relay to de-energize. For normal relays, it directly provides a low level,
        while for latching relays, it sends a reverse short pulse.

        Args:
            None: This method does not accept any parameters.

        Returns:
            None: This method does not return any value.

        Raises:
            None: This method does not raise any exceptions.
        """
        if self.relay_type == 'normal':
            # 普通继电器直接给低电平
            self.pin1.value(1)
        else:
            # 磁保持需要反向脉冲
            self._pulse_timer.deinit()
            # 先设置方向
            self.pin1.value(0)
            # 开始反向脉冲
            self.pin2.value(1)
            self._pulse_timer.init(mode=Timer.ONE_SHOT,
                                   period=50,
                                   callback=self._reset_pins)
        self._last_state = False

    def toggle(self) -> None:
        """
        切换继电器状态（仅普通继电器可用）。

        该方法用于切换普通继电器的开关状态。

        Args:
            None: 此方法不接受任何参数。

        Returns:
            None: 此方法没有返回值。

        Raises:
            None: 该方法不抛出异常。

        =================================

        Toggle relay state (only available for normal relays).

        This method is used to toggle the switch state of normal relays.

        Args:
            None: This method does not accept any parameters.

        Returns:
            None: This method does not return any value.

        Raises:
            None: This method does not raise any exceptions.
        """
        if self.relay_type == 'normal':
            # 普通继电器直接取反
            self.pin1.value(not self.pin1.value())
            self._last_state = bool(self.pin1.value())
        else:
            # 磁保持继电器根据记录状态切换脉冲
            if self._last_state:
                self.off()
            else:
                self.on()

    def deinit(self):
        """
        释放资源（程序结束时调用）。

        该方法用于释放继电器控制器使用的所有资源，包括定时器和GPIO引脚。

        Args:
            None: 此方法不接受任何参数。

        Returns:
            None: 此方法没有返回值。

        Raises:
            None: 该方法不抛出异常。

        =================================

        Release resources (called when program ends).

        This method is used to release all resources used by the relay controller, including timers and GPIO pins.

        Args:
            None: This method does not accept any parameters.

        Returns:
            None: This method does not return any value.

        Raises:
            None: This method does not raise any exceptions.
        """
        self._pulse_timer.deinit()
        # 确保继电器处于安全状态
        self.off()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================