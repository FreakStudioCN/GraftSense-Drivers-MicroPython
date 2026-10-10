# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : FreakStudio
# @File    : ft6336.py
# @Description : FT6336/FT6336U I2C touch driver candidate
# @License : Apache-2.0

__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "Apache-2.0"
__platform__ = "MicroPython v1.23"

# 预留 ISR 异常调试缓冲区
import micropython

micropython.alloc_emergency_exception_buf(100)

# const() 兼容导入
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import time

# ======================================== 导入相关模块 =========================================
# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================


class FT6336:
    # 实例属性槽（内存优化）
    __slots__ = ("_i2c", "_addr", "_reset_pin", "_irq_pin", "_debug", "_triggered", "_point", "_buf4")

    """
    FT6336/FT6336U I2C 电容触摸控制器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _reset_pin (Pin): 复位引脚（可为 None）
        _irq_pin (Pin): 中断引脚（可为 None）
        _debug (bool): 调试日志开关
        _triggered (bool): 触摸中断触发标志
        _point (dict): 缓存的上次触摸点数据（可为 None）
    Methods:
        reset(): 硬件复位
        read_chip_id(): 读取芯片 ID
        enable_gesture(): 启用手势识别
        get_touch_count(): 获取触摸点数
        read_point(): 读取触摸点坐标
        get_gesture(): 读取手势代码
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 默认 I2C 地址 0x38，芯片 ID 0x64
        - IRQ 处理函数为 ISR-safe，仅设置标志位
        - 当前仅读取 touch1 数据，多点触控扩展待完成
        - 源自 Waveshare Apache-2.0 参考实现
    ==========================================
    FT6336/FT6336U I2C capacitive touch controller driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _reset_pin (Pin): Reset pin (may be None)
        _irq_pin (Pin): Interrupt pin (may be None)
        _debug (bool): Debug logging switch
        _triggered (bool): Touch interrupt trigger flag
        _point (dict): Cached last touch point data (may be None)
    Methods:
        reset(): Hardware reset
        read_chip_id(): Read chip ID
        enable_gesture(): Enable gesture recognition
        get_touch_count(): Get touch point count
        read_point(): Read touch point coordinates
        get_gesture(): Read gesture code
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Default I2C address 0x38, chip ID 0x64
        - IRQ handler is ISR-safe, only sets a flag
        - Currently only reads touch1 data, multi-touch expansion pending
        - Based on Waveshare Apache-2.0 reference implementation
    """

    # 类级常量：I2C 地址与芯片 ID
    DEFAULT_ADDRESS = const(0x38)
    EXPECTED_CHIP_ID = const(0x64)

    # 寄存器地址
    REG_CHIP_ID = const(0xA3)
    REG_TD_STATUS = const(0x02)
    REG_TOUCH1_XH = const(0x03)
    REG_GESTURE_ENABLE = const(0xD0)
    REG_GESTURE_OUTPUT = const(0xD3)

    # 复位时序常量（ms）
    _RESET_DELAY_MS = const(200)

    def __init__(self, i2c, address=None, reset_pin=None, irq_pin=None, callback=None, trigger=0, gesture=False, verify=False, debug=False):
        """
        初始化 FT6336 触摸控制器
        Args:
            i2c: I2C 总线实例（须支持 readfrom_mem/readfrom_mem_into/writeto_mem）
            address (int): 设备 I2C 地址，默认 0x38
            reset_pin (Pin): 复位引脚实例，可选
            irq_pin (Pin): 中断引脚实例，可选
            callback (callable): 中断回调函数，可选（默认使用内部 ISR 处理）
            trigger (int): 中断触发条件，默认 Pin.IRQ_FALLING
            gesture (bool): 是否启用手势识别，默认 False
            verify (bool): 是否验证芯片 ID，默认 False
            debug (bool): 是否开启调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: 参数类型错误
            RuntimeError: 芯片 ID 验证失败
        Notes:
            - ISR-safe: 否（初始化阶段执行 I2C 通信）
            - 若提供 irq_pin，将在内部注册中断回调
        ==========================================
        Initialize FT6336 touch controller.
        Args:
            i2c: I2C bus instance (must support readfrom_mem/readfrom_mem_into/writeto_mem)
            address (int): Device I2C address, default 0x38
            reset_pin (Pin): Reset pin instance, optional
            irq_pin (Pin): Interrupt pin instance, optional
            callback (callable): Interrupt callback, optional (default uses internal ISR handler)
            trigger (int): Interrupt trigger condition, default Pin.IRQ_FALLING
            gesture (bool): Enable gesture recognition, default False
            verify (bool): Verify chip ID, default False
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: Chip ID verification failed
        Notes:
            - ISR-safe: No (performs I2C communication during init)
            - If irq_pin is provided, interrupt callback will be registered internally
        """
        # 校验 I2C 实例
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem()")
        self._i2c = i2c

        # 校验并设置地址
        if address is None:
            self._addr = self.DEFAULT_ADDRESS
        else:
            if not isinstance(address, int):
                raise ValueError("address must be int, got %s" % type(address))
            if address < 0x00 or address > 0x7F:
                raise ValueError("address must be 0x00~0x7F, got 0x%02X" % address)
            self._addr = address

        # 校验 reset_pin
        if reset_pin is not None:
            if not hasattr(reset_pin, "value"):
                raise ValueError("reset_pin must be a Pin instance")
        self._reset_pin = reset_pin

        # 校验 irq_pin
        if irq_pin is not None:
            if not hasattr(irq_pin, "irq"):
                raise ValueError("irq_pin must be a Pin instance")
        self._irq_pin = irq_pin

        # 校验 gesture
        if not isinstance(gesture, bool):
            raise ValueError("gesture must be bool, got %s" % type(gesture))

        # 校验 verify
        if not isinstance(verify, bool):
            raise ValueError("verify must be bool, got %s" % type(verify))

        # 校验 debug
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))
        self._debug = debug

        # 校验 callback
        if callback is not None:
            if not callable(callback):
                raise ValueError("callback must be callable, got %s" % type(callback))

        # 校验 trigger
        if not isinstance(trigger, int):
            raise ValueError("trigger must be int, got %s" % type(trigger))

        # 内部状态初始化
        self._triggered = True
        self._point = None
        self._buf4 = bytearray(4)

        # 执行硬件复位
        if self._reset_pin is not None:
            self.reset()

        # 手势识别配置
        self.enable_gesture(gesture)

        # 芯片 ID 验证
        if verify and self.read_chip_id() != self.EXPECTED_CHIP_ID:
            raise RuntimeError("FT6336 chip id mismatch")

        # 注册中断回调
        if self._irq_pin is not None:
            # 使用外部回调或内部 ISR 处理
            if trigger == 0:
                # Pin.IRQ_FALLING 的标准整数值
                trig = 2
            else:
                trig = trigger
            handler = callback if callback is not None else self._irq_handler
            self._irq_pin.irq(handler=handler, trigger=trig)

    def reset(self):
        """
        硬件复位 FT6336（低电平脉冲复位）
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: 复位引脚未配置
        Notes:
            - ISR-safe: 否（调用 time.sleep_ms）
            - 复位后触摸触发标志置为 True
        ==========================================
        Hardware reset FT6336 (active-low pulse reset).
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: Reset pin not configured
        Notes:
            - ISR-safe: No (calls time.sleep_ms)
            - Touch trigger flag set to True after reset
        """
        if self._reset_pin is None:
            raise RuntimeError("Reset pin not configured")
        self._log("Performing hardware reset")
        # 拉低产生复位脉冲
        self._reset_pin.value(1)
        time.sleep_ms(self._RESET_DELAY_MS)
        self._reset_pin.value(0)
        time.sleep_ms(self._RESET_DELAY_MS)
        self._reset_pin.value(1)
        time.sleep_ms(self._RESET_DELAY_MS)
        # 复位后标记触摸就绪
        self._triggered = True

    def read_chip_id(self):
        """
        读取芯片 ID 寄存器
        Args:
            无
        Returns:
            int: 芯片 ID（期望值 0x64）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否（执行 I2C 通信）
        ==========================================
        Read chip ID register.
        Args:
            None
        Returns:
            int: Chip ID (expected 0x64)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No (performs I2C communication)
        """
        self._log("Reading chip ID from reg 0x%02X" % self.REG_CHIP_ID)
        try:
            return self._i2c.readfrom_mem(self._addr, self.REG_CHIP_ID, 1)[0]
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X: %s" % (self.REG_CHIP_ID, e))

    def enable_gesture(self, enable=True):
        """
        启用手势识别功能
        Args:
            enable (bool): True 启用，False 禁用
        Returns:
            None
        Raises:
            ValueError: 参数类型错误
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否（执行 I2C 通信）
            - 启用后可通过 get_gesture() 读取手势代码
        ==========================================
        Enable gesture recognition.
        Args:
            enable (bool): True to enable, False to disable
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No (performs I2C communication)
            - After enabling, gesture codes can be read via get_gesture()
        """
        if not isinstance(enable, bool):
            raise ValueError("enable must be bool, got %s" % type(enable))
        self._log("Setting gesture enable to %s" % enable)
        try:
            self._i2c.writeto_mem(
                self._addr,
                self.REG_GESTURE_ENABLE,
                bytes([0x01 if enable else 0x00]),
            )
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X: %s" % (self.REG_GESTURE_ENABLE, e))

    def get_touch_count(self):
        """
        获取当前触摸点数
        Args:
            无
        Returns:
            int: 触摸点数（0~5）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否（执行 I2C 通信）
        ==========================================
        Get current touch point count.
        Args:
            None
        Returns:
            int: Touch point count (0~5)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No (performs I2C communication)
        """
        self._log("Reading touch count from reg 0x%02X" % self.REG_TD_STATUS)
        try:
            return self._i2c.readfrom_mem(self._addr, self.REG_TD_STATUS, 1)[0] & 0x0F
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X: %s" % (self.REG_TD_STATUS, e))

    def read_point(self):
        """
        读取触摸点坐标（touch1）
        Args:
            无
        Returns:
            dict: {"x": x, "y": y, "points": count}，无触摸时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否（执行 I2C 通信）
            - 当前仅读取 touch1 数据，多点触控扩展待完成
            - 若配置了 IRQ 引脚，仅在中断触发后返回有效数据
        ==========================================
        Read touch point coordinates (touch1).
        Args:
            None
        Returns:
            dict: {"x": x, "y": y, "points": count}, or None if no touch
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No (performs I2C communication)
            - Currently only reads touch1 data, multi-touch expansion pending
            - If IRQ pin is configured, valid data is returned only after interrupt trigger
        """
        # 若配置了 IRQ 引脚且未触发，跳过读取
        if not self._triggered and self._irq_pin is not None:
            return None

        # 清除触发标志
        self._triggered = False

        # 读取触摸点数
        count = self.get_touch_count()
        if count == 0:
            self._point = None
            return None

        # 读取 touch1 坐标数据（4字节）
        self._log("Reading touch1 data from reg 0x%02X" % self.REG_TOUCH1_XH)
        try:
            self._i2c.readfrom_mem_into(self._addr, self.REG_TOUCH1_XH, self._buf4)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X: %s" % (self.REG_TOUCH1_XH, e))

        # 解析 X 坐标：高4位来自 buf4[0] 低4位，拼合 buf4[1]
        x = ((self._buf4[0] & 0x0F) << 8) | self._buf4[1]
        # 解析 Y 坐标：高4位来自 buf4[2] 低4位，拼合 buf4[3]
        y = ((self._buf4[2] & 0x0F) << 8) | self._buf4[3]

        # 缓存并返回触摸点数据
        self._point = {"x": x, "y": y, "points": count}
        self._log("Touch point: x=%d, y=%d, count=%d" % (x, y, count))
        return self._point

    def get_gesture(self):
        """
        读取手势代码
        Args:
            无
        Returns:
            int: 手势代码（0=无手势，1=上滑，2=下滑，3=左滑，4=右滑）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否（执行 I2C 通信）
            - 需先调用 enable_gesture(True) 启用手势识别
        ==========================================
        Read gesture code.
        Args:
            None
        Returns:
            int: Gesture code (0=None, 1=Swipe Up, 2=Swipe Down, 3=Swipe Left, 4=Swipe Right)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No (performs I2C communication)
            - Requires enable_gesture(True) to be called first
        """
        self._log("Reading gesture from reg 0x%02X" % self.REG_GESTURE_OUTPUT)
        try:
            return self._i2c.readfrom_mem(self._addr, self.REG_GESTURE_OUTPUT, 1)[0]
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X: %s" % (self.REG_GESTURE_OUTPUT, e))

    def deinit(self):
        """
        释放硬件资源，取消中断注册
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 调用后设备实例不可再使用
        ==========================================
        Release hardware resources, unregister interrupt.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - After calling, the device instance should not be reused
        """
        self._log("Deinitializing FT6336")
        # 取消中断回调注册
        if self._irq_pin is not None and hasattr(self._irq_pin, "irq"):
            self._irq_pin.irq(handler=None)

    def _log(self, msg):
        """
        调试日志输出（内部使用）
        Args:
            msg (str): 日志消息
        Returns:
            None
        Notes:
            - ISR-safe: 否（print 涉及内存分配）
            - 仅在 _debug=True 时输出
        ==========================================
        Debug log output (internal use).
        Args:
            msg (str): Log message
        Returns:
            None
        Notes:
            - ISR-safe: No (print involves memory allocation)
            - Only outputs when _debug=True
        """
        if self._debug:
            print("[FT6336] %s" % msg)

    def _irq_handler(self, pin):
        """
        中断服务函数（ISR-safe，仅设置触发标志位）
        Args:
            pin (Pin): 触发中断的引脚
        Returns:
            None
        Notes:
            - ISR-safe: 是（仅设置布尔标志位，无内存分配、无 I/O 操作）
        ==========================================
        Interrupt service routine (ISR-safe, only sets trigger flag).
        Args:
            pin (Pin): The pin that triggered the interrupt
        Returns:
            None
        Notes:
            - ISR-safe: Yes (only sets boolean flag, no memory allocation, no I/O)
        """
        self._triggered = True


# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
