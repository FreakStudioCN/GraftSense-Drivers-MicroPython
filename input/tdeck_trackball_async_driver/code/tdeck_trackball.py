# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/21 00:00
# @Author  : FreakStudio
# @File    : tdeck_trackball.py
# @Description : LILYGO T-Deck Plus 轨迹球 GPIO 轮询驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# 导入相关模块
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import time
from machine import Pin

# 全局变量
# 默认引脚映射（按 LILYGO T-Deck 官方 UnitTest/mouse_read）
# 右方向: GPIO2  (BOARD_TBOX_G02)
DEFAULT_PIN_RIGHT = const(2)
# 上方向: GPIO3  (BOARD_TBOX_G01)
DEFAULT_PIN_UP = const(3)
# 左方向: GPIO1  (BOARD_TBOX_G04)
DEFAULT_PIN_LEFT = const(1)
# 下方向: GPIO15 (BOARD_TBOX_G03)
DEFAULT_PIN_DOWN = const(15)
# 中心按键: GPIO0 (BOARD_BOOT_PIN — 同时是 ESP32-S3 BOOT 引脚，只能输入读取)
DEFAULT_PIN_BUTTON = const(0)

# 方向索引常量
_IDX_RIGHT = const(0)
_IDX_UP = const(1)
_IDX_LEFT = const(2)
_IDX_DOWN = const(3)

# 功能函数

# 自定义类


class TDeckTrackball:
    """
    LILYGO T-Deck Plus 板载轨迹球 GPIO 轮询驱动

    轨迹球不是 I2C/SPI 轨迹球 IC，而是由 Track Ball 组件 + 4 个 AN48841B
    Hall 开关 + TS-1187AB 中心按键组成的纯 GPIO 输入设备。该驱动通过轮询
    四个方向 GPIO 的电平变化来跟踪相对位移和中心按键状态。

    Attributes:
        _pins (tuple): 四个方向 Pin 对象的元组 (right, up, left, down)
        _button (Pin or None): 中心按键 Pin 对象
        _step (int): 每次电平变化的位移步长
        _x (int): 累计 X 轴相对位移
        _y (int): 累计 Y 轴相对位移
        _debug (bool): 调试日志开关
    Methods:
        poll(): 轮询 GPIO 并返回 (dx, dy, pressed)
        read(): poll() 的别名
        pressed(): 获取中心按键状态
        button_changed(): 检测上次 poll() 是否发生按键电平变化
        position(): 获取累计相对位置
        reset_position(): 重置累计位置
        reset_state(): 重新同步 GPIO 基线
        self_test(verbose): GPIO 电平读取检查
        deinit(): 释放硬件资源
    Notes:
        - 这是纯 GPIO 输入驱动，不是 I2C/SPI 轨迹球 IC 驱动
        - GPIO0 同时是 ESP32-S3 BOOT 引脚，驱动绝不将其配置为输出
        - 方向映射使用 LILYGO 官方 UnitTest 约定
        - 未在 T-Deck Plus 实物上硬件验证
    ==========================================
    GPIO polling driver for the LILYGO T-Deck trackball.

    The T-Deck trackball has no I2C/SPI controller. Movement is represented by
    edge changes on four Hall-switch GPIO inputs. The center press is GPIO0,
    which is also the ESP32-S3 BOOT pin; this driver never drives that pin.

    Attributes:
        _pins (tuple): Four direction Pin objects (right, up, left, down)
        _button (Pin or None): Center button Pin object
        _step (int): Displacement step per level change
        _x (int): Accumulated X-axis relative displacement
        _y (int): Accumulated Y-axis relative displacement
        _debug (bool): Debug log toggle
    Methods:
        poll(): Poll GPIO and return (dx, dy, pressed)
        read(): Alias for poll()
        pressed(): Get center button state
        button_changed(): Check if last poll() detected button level change
        position(): Get accumulated relative position
        reset_position(): Reset accumulated position
        reset_state(): Resync GPIO baseline
        self_test(verbose): GPIO level read check
        deinit(): Release hardware resources
    Notes:
        - This is a pure GPIO input driver, not an I2C/SPI trackball IC driver
        - GPIO0 is also the ESP32-S3 BOOT pin; never configured as output
        - Direction mapping follows LILYGO official UnitTest convention
        - Not hardware-verified on a real T-Deck Plus
    """

    def __init__(
        self,
        pin_right: int = DEFAULT_PIN_RIGHT,
        pin_up: int = DEFAULT_PIN_UP,
        pin_left: int = DEFAULT_PIN_LEFT,
        pin_down: int = DEFAULT_PIN_DOWN,
        pin_button: int = DEFAULT_PIN_BUTTON,
        step: int = 1,
        pull: int = Pin.PULL_UP,
        button_active_low: bool = True,
        debounce_ms: int = 0,
        debug: bool = False,
    ) -> None:
        """
        初始化 T-Deck 轨迹球驱动

        配置方向 GPIO 和中心按键 GPIO 的输入模式及初始状态。
        Args:
            pin_right (int): 右方向 GPIO 引脚号，默认 2 (G02)
            pin_up (int): 上方向 GPIO 引脚号，默认 3 (G01)
            pin_left (int): 左方向 GPIO 引脚号，默认 1 (G04)
            pin_down (int): 下方向 GPIO 引脚号，默认 15 (G03)
            pin_button (int): 中心按键 GPIO 引脚号，默认 0 (BOOT)
            step (int): 每次电平变化的位移步长，默认 1
            pull (int): GPIO 上下拉模式，默认 Pin.PULL_UP
            button_active_low (bool): 按键是否低电平有效，默认 True
            debounce_ms (int): 去抖延时（ms），0 表示不去抖，默认 0
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            TypeError: step 不是整数
            ValueError: step <= 0 或 debounce_ms < 0
        Notes:
            - GPIO0 同时是 BOOT 引脚，驱动绝不将其配置为输出模式
            - 方向映射：right=+X, up=-Y, left=-X, down=+Y（与 LILYGO UnitTest 一致）
            - 传入的 pin_* 参数会通过 _make_input_pin() 转换为 Pin 对象
        ==========================================
        Initialize T-Deck trackball driver.

        Configures direction GPIOs and center button GPIO as inputs.
        Args:
            pin_right (int): Right direction GPIO, default 2 (G02)
            pin_up (int): Up direction GPIO, default 3 (G01)
            pin_left (int): Left direction GPIO, default 1 (G04)
            pin_down (int): Down direction GPIO, default 15 (G03)
            pin_button (int): Center button GPIO, default 0 (BOOT)
            step (int): Displacement step per level change, default 1
            pull (int): GPIO pull mode, default Pin.PULL_UP
            button_active_low (bool): Button active low flag, default True
            debounce_ms (int): Debounce delay in ms, 0 to disable, default 0
            debug (bool): Enable debug log output, default False
        Raises:
            TypeError: step is not int
            ValueError: step <= 0 or debounce_ms < 0
        Notes:
            - GPIO0 is also the BOOT pin; never configured as output
            - Direction mapping: right=+X, up=-Y, left=-X, down=+Y
            - pin_* arguments are converted to Pin objects
        """
        # 参数校验
        if not isinstance(step, int):
            raise TypeError("step must be int")
        if step <= 0:
            raise ValueError("step must be > 0")
        if debounce_ms < 0:
            raise ValueError("debounce_ms must be >= 0")
        if not isinstance(debug, bool):
            raise TypeError("debug must be bool")

        self._debug = debug
        self._step = step
        self._button_active_low = bool(button_active_low)
        self._debounce_ms = debounce_ms

        # 初始化四个方向 GPIO 输入引脚
        self._pins = (
            self._make_input_pin(pin_right, pull),
            self._make_input_pin(pin_up, pull),
            self._make_input_pin(pin_left, pull),
            self._make_input_pin(pin_down, pull),
        )

        # 初始化中心按键 GPIO 输入引脚（GPIO0 只能是输入）
        self._button = None
        if pin_button is not None:
            self._button = self._make_input_pin(pin_button, pull)

        # 记录 GPIO 初始基线电平
        self._last = [pin.value() for pin in self._pins]
        self._last_button = self._button.value() if self._button else 1
        self._last_ms = [time.ticks_ms()] * 4
        self._button_changed = False
        self._x = 0
        self._y = 0

        self._log(
            "init: pins=(R%d,U%d,L%d,D%d,B%s) step=%d debounce=%d"
            % (
                pin_right if isinstance(pin_right, int) else -1,
                pin_up if isinstance(pin_up, int) else -1,
                pin_left if isinstance(pin_left, int) else -1,
                pin_down if isinstance(pin_down, int) else -1,
                str(pin_button),
                step,
                debounce_ms,
            )
        )

    def _log(self, msg: str) -> None:
        """
        条件日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - ISR-safe: 否（涉及 print 和字符串拼接）
        ==========================================
        Conditional log output.
        Args:
            msg (str): Log message
        Notes:
            - ISR-safe: No (uses print and string concatenation)
        """
        if self._debug:
            print("[TDeckTrackball] %s" % msg)

    def poll(self) -> tuple:
        """
        轮询 GPIO 输入并返回位移和按键状态

        检测四个方向引脚的电平变化，累加位移量。
        Returns:
            tuple: (dx, dy, pressed) — X 增量、Y 增量、中心按键是否按下
        Notes:
            - 副作用：更新内部累计位移和按键状态
            - 方向映射：right=+X, up=-Y, left=-X, down=+Y
            - 所有方向电平变化均被计数（与 LILYGO 官方逻辑一致）
            - ISR-safe: 否（涉及 GPIO 读取和 ticks_ms）
        ==========================================
        Poll GPIO inputs and return displacement and button state.

        Detects level changes and accumulates displacement.
        Returns:
            tuple: (dx, dy, pressed) — X delta, Y delta, center button pressed
        Notes:
            - Side effect: updates accumulated position and button state
            - Direction mapping: right=+X, up=-Y, left=-X, down=+Y
            - All direction level changes are counted
            - ISR-safe: No (involves GPIO reads and ticks_ms)
        """
        now = time.ticks_ms()
        dx = 0
        dy = 0

        # 检测四个方向 GPIO 的电平变化
        for index, pin in enumerate(self._pins):
            value = pin.value()
            if value == self._last[index]:
                continue
            # 去抖检查
            if self._debounce_ms:
                elapsed = time.ticks_diff(now, self._last_ms[index])
                if elapsed < self._debounce_ms:
                    continue
                self._last_ms[index] = now
            self._last[index] = value
            # 方向映射
            if index == _IDX_RIGHT:
                dx += self._step
            elif index == _IDX_UP:
                dy -= self._step
            elif index == _IDX_LEFT:
                dx -= self._step
            else:
                dy += self._step

        self._x += dx
        self._y += dy
        self._button_changed = False

        # 检测中心按键电平变化
        if self._button is not None:
            value = self._button.value()
            if value != self._last_button:
                self._last_button = value
                self._button_changed = True

        return dx, dy, self.pressed()

    def read(self) -> tuple:
        """
        poll() 的别名

        Returns:
            tuple: (dx, dy, pressed)
        Notes:
            - 副作用：与 poll() 相同
            - ISR-safe: 否
        ==========================================
        Alias for poll().

        Returns:
            tuple: (dx, dy, pressed)
        Notes:
            - Side effect: same as poll()
            - ISR-safe: No
        """
        return self.poll()

    def pressed(self) -> bool:
        """
        获取中心轨迹球按键是否按下

        Returns:
            bool: True 表示按键按下
        Notes:
            - 副作用：无
            - ISR-safe: 是（仅读取 GPIO 电平）
            - 当没有配置按键引脚时始终返回 False
        ==========================================
        Check if the center trackball button is pressed.

        Returns:
            bool: True if button is pressed
        Notes:
            - Side effect: None
            - ISR-safe: Yes (reads GPIO level only)
            - Always returns False when no button pin is configured
        """
        if self._button is None:
            return False
        value = self._button.value()
        if self._button_active_low:
            return value == 0
        return value == 1

    def button_changed(self) -> bool:
        """
        检测上次 poll() 是否检测到按键电平变化

        Returns:
            bool: True 表示按键状态发生了变化
        Notes:
            - 副作用：无
            - ISR-safe: 是（仅读取实例变量）
        ==========================================
        Check if the last poll() detected a button level change.

        Returns:
            bool: True if button state changed
        Notes:
            - Side effect: None
            - ISR-safe: Yes (reads instance variable only)
        """
        return self._button_changed

    def position(self) -> tuple:
        """
        获取累计相对位置

        Returns:
            tuple: (x, y) 累计相对位移
        Notes:
            - 副作用：无
            - ISR-safe: 是（仅读取实例变量）
        ==========================================
        Get accumulated relative position.

        Returns:
            tuple: (x, y) accumulated relative displacement
        Notes:
            - Side effect: None
            - ISR-safe: Yes (reads instance variable only)
        """
        return self._x, self._y

    def reset_position(self) -> None:
        """
        重置累计相对位置为 (0, 0)

        Notes:
            - 副作用：清零内部累加器
            - ISR-safe: 是（仅写入实例变量）
        ==========================================
        Reset accumulated relative position to (0, 0).

        Notes:
            - Side effect: clears internal accumulators
            - ISR-safe: Yes (writes instance variable only)
        """
        self._x = 0
        self._y = 0

    def reset_state(self) -> None:
        """
        重新同步 GPIO 基线电平

        更新所有方向的当前电平作为基线，不清除累计位移。
        Notes:
            - 副作用：更新内部 GPIO 基线
            - 用于在方向错误时重新校准基线
            - ISR-safe: 否（涉及 GPIO 读取）
        ==========================================
        Resync GPIO baseline levels.

        Updates all direction current levels as baseline without clearing
        accumulated displacement.
        Notes:
            - Side effect: updates internal GPIO baseline
            - Use to recalibrate baseline when direction is wrong
            - ISR-safe: No (involves GPIO reads)
        """
        self._last = [pin.value() for pin in self._pins]
        self._last_button = self._button.value() if self._button else 1
        now = time.ticks_ms()
        self._last_ms = [now] * 4
        self._button_changed = False

    def self_test(self, verbose: bool = True) -> bool:
        """
        运行非破坏性 GPIO 电平读取检查

        验证所有 GPIO 引脚都能读取到有效的 0 或 1 电平。
        Args:
            verbose (bool): 是否打印诊断信息，默认 True
        Returns:
            bool: True 表示所有 GPIO 读取正常
        Notes:
            - 副作用：无
            - 此方法只验证 GPIO 可读性，不验证方向映射正确性
            - 未在 T-Deck Plus 实物上验证
            - ISR-safe: 否（涉及 GPIO 读取和 print）
        ==========================================
        Run a non-destructive GPIO level read check.

        Verifies all GPIO pins can read valid 0 or 1 levels.
        Args:
            verbose (bool): Whether to print diagnostic info, default True
        Returns:
            bool: True if all GPIO reads are valid
        Notes:
            - Side effect: None
            - This only validates GPIO readability, not direction mapping
            - Not verified on real T-Deck Plus hardware
            - ISR-safe: No (involves GPIO reads and print)
        """
        try:
            levels = [pin.value() for pin in self._pins]
            if self._button is not None:
                levels.append(self._button.value())
            ok = True
            for level in levels:
                if level not in (0, 1):
                    ok = False
                    break
            if verbose:
                print("[TDeckTrackball] gpio levels: %s" % levels)
                print("[TDeckTrackball] gpio read ok: %s" % ok)
            return ok
        except Exception as exc:
            if verbose:
                print("[TDeckTrackball] self-test failed: %s" % exc)
            return False

    def deinit(self) -> None:
        """
        释放硬件资源

        清除所有 GPIO 引脚上的 IRQ 回调。
        Notes:
            - 副作用：取消所有引脚的 IRQ 处理器
            - ISR-safe: 否（涉及 Pin.irq 调用）
        ==========================================
        Release hardware resources.

        Clears IRQ callbacks on all GPIO pins.
        Notes:
            - Side effect: disables all pin IRQ handlers
            - ISR-safe: No (involves Pin.irq calls)
        """
        self._log("deinit")
        for pin in self._pins:
            try:
                pin.irq(handler=None)
            except Exception:
                pass
        if self._button is not None:
            try:
                self._button.irq(handler=None)
            except Exception:
                pass

    @staticmethod
    def _make_input_pin(pin, pull: int):
        """
        获取输入 Pin 对象

        若传入的已是 Pin 对象则直接返回，否则创建新的输入 Pin。
        Args:
            pin: Pin 对象或引脚编号
            pull (int): 上下拉模式
        Returns:
            Pin: 输入模式 Pin 对象
        Notes:
            - 绝不将 GPIO0 配置为输出模式
            - ISR-safe: 否（可能创建 Pin 对象）
        ==========================================
        Get input Pin object.

        Returns the pin if it is already a Pin object, otherwise creates one.
        Args:
            pin: Pin object or pin number
            pull (int): Pull-up/down mode
        Returns:
            Pin: Input mode Pin object
        Notes:
            - Never configures GPIO0 as output
            - ISR-safe: No (may create Pin object)
        """
        if hasattr(pin, "value"):
            return pin
        return Pin(pin, Pin.IN, pull)


# 初始化配置

# 主程序
