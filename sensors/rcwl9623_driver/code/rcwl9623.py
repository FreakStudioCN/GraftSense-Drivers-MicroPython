# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/13 17:30
# @Author  : 缪贵成
# @File    : rcwl9623.py
# @Description : RCWL9623 收发一体超声波模块驱动，支持 GPIO/OneWire/UART/I2C 四种模式，包含详细时序注释
# @License : MIT

__version__ = "1.0.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入硬件模块
from machine import Pin, time_pulse_us

# 导入时间相关模块
import time

# 导入MicroPython中常量相关
from micropython import const

# ========================================== 全局变量 ===========================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class RCWL9623:
    """
    该类提供了对 RCWL9623 超声波测距模块的控制，支持 GPIO/OneWire/UART/I2C 四种工作模式。
    注意，该超声波芯片有效测量距离为25CM到700CM，超出范围将返回 None。

    Attributes:
        mode (int): 当前工作模式，取值为类常量之一：
            GPIO_MODE, ONEWIRE_MODE, UART_MODE, I2C_MODE。
        trig (Pin): GPIO 模式下的触发引脚对象（仅 GPIO 模式有效）。
        echo (Pin): GPIO 模式下的回波引脚对象（仅 GPIO 模式有效）。
        pin (Pin): OneWire 模式下的数据引脚对象（仅 OneWire 模式有效）。
        uart (UART): UART 模式下的串口实例（仅 UART 模式有效）。
        i2c (I2C): I2C 模式下的 I2C 实例（仅 I2C 模式有效）。
        addr (int): I2C 设备地址（仅 I2C 模式有效）。

    Methods:
        __init__(mode, *, gpio_pins=None, onewire_pin=None, uart=None, i2c=None, addr=None):
            初始化超声波模块，根据模式配置相应的接口。

        read_distance() -> float | None:
            读取距离（单位：厘米），如果失败则返回 None。

        _read_gpio() -> float | None:
            GPIO 模式下的测距实现（内部方法）。

        _read_onewire() -> float | None:
            OneWire 模式下的测距实现（内部方法）。

        _read_uart(max_retries=5) -> float | None:
            UART 模式下的测距实现（内部方法）。

        _read_i2c() -> float | None:
            I2C 模式下的测距实现（内部方法）。

    ==========================================
    This class provides control for the RCWL9623 ultrasonic distance sensor,
    supporting four operating modes: GPIO, OneWire, UART, and I2C.
    Note that the effective measurement distance of this ultrasonic chip is 25CM to 700CM,
    and the distance will return None if it exceeds the range.

    Attributes:
        mode (int): Current operating mode, one of the class constants:
            GPIO_MODE, ONEWIRE_MODE, UART_MODE, I2C_MODE.
        trig (Pin): Trigger pin object in GPIO mode (valid only in GPIO mode).
        echo (Pin): Echo pin object in GPIO mode (valid only in GPIO mode).
        pin (Pin): Data pin object in OneWire mode (valid only in OneWire mode).
        uart (UART): UART instance in UART mode (valid only in UART mode).
        i2c (I2C): I2C instance in I2C mode (valid only in I2C mode).
        addr (int): I2C device address (valid only in I2C mode).

    Methods:
        __init__(mode, *, gpio_pins=None, onewire_pin=None, uart=None, i2c=None, addr=None):
            Initialize the ultrasonic module with the specified interface configuration.

        read_distance() -> float | None:
            Read distance in centimeters, returns None on failure.

        _read_gpio() -> float | None:
            Distance measurement implementation for GPIO mode (internal method).

        _read_onewire() -> float | None:
            Distance measurement implementation for OneWire mode (internal method).

        _read_uart(max_retries=5) -> float | None:
            Distance measurement implementation for UART mode (internal method).

        _read_i2c() -> float | None:
            Distance measurement implementation for I2C mode (internal method).
    """

    # 工作模式常量
    GPIO_MODE, ONEWIRE_MODE, UART_MODE, I2C_MODE = [0, 1, 2, 3]
    # 固定I2C通信地址
    I2C_DEFAULT_ADDR = const(0x57)

    # 使用关键字参数传递，驱动只负责使用总线/串口实例，不负责创建/配置它们，硬件初始化（引脚选择、波特率、频率）由应用层统一管理，驱动变得更轻、更可复用，也减少驱动与硬件平台差异绑定的代码；
    # 同时，在实际嵌入式系统中，I2C 总线常被多个设备共享，强制传入实例可以避免驱动重复初始化并在外层统一管理总线资源；
    # 并且，使用 gpio_pins、onewire_pin、uart、i2c 这些命名参数，比通过一堆位置参数或混合参数更直观，减少调用出错概率（尤其是在多模式类里）。
    def __init__(self, mode: int, *, gpio_pins=None, onewire_pin=None, uart=None, i2c=None, addr=None):
        """
        初始化 RCWL9623 超声波测距模块驱动。

        Args:
            mode (int): 工作模式，必须为类常量之一：
                RCWL9623.GPIO_MODE / RCWL9623.ONEWIRE_MODE /
                RCWL9623.UART_MODE / RCWL9623.I2C_MODE。
            gpio_pins (tuple[int, int] | list[int, int] | None):
                仅在 GPIO 模式时使用，格式 (trig_pin, echo_pin)，两个引脚编号（整数）。
            onewire_pin (int | None):
                仅在 OneWire 模式时使用，单总线引脚编号（整数）。
            uart (object | None):
                仅在 UART 模式时使用。必须传入已初始化的 UART 实例（驱动不再创建）。
                要求提供的对象具备串口常用方法（例如 read、write）。
            i2c (object | None):
                仅在 I2C 模式时使用。必须传入已初始化的 I2C 实例（驱动不再创建）。
                要求提供的对象具备 I2C 常用方法（例如 readfrom、writeto）。
            addr (int | None):
                可选，I2C 设备地址；若不传则使用 RCWL9623.I2C_DEFAULT_ADDR。

        Returns:
            None

        Raises:
            ValueError: 当 mode 非法，或对应模式缺少必需参数，或传入参数类型不符合预期时抛出。
            ValueError: 当传入的 uart/i2c 对象不满足最小“鸭子类型”要求时抛出。

        注意:
            - 对于 UART 与 I2C 模式，调用者必须在外部完成实例的初始化与配置（例如引脚、波特率、频率等），
              驱动仅接收并使用传入的实例，便于总线共享与单元测试。
            - 方法会创建 Pin 实例用于 GPIO/OneWire 模式（调用方应确保所用引脚合法）。
            - 此方法执行非实时/非 ISR-safe 的操作（例如实例创建、属性检查），不可在中断上下文调用。

        ==========================================

        Initialize RCWL9623 ultrasonic distance sensor driver.

        Args:
            mode (int): Operating mode. Must be one of the class constants:
                RCWL9623.GPIO_MODE / RCWL9623.ONEWIRE_MODE /
                RCWL9623.UART_MODE / RCWL9623.I2C_MODE.
            gpio_pins (tuple[int, int] | list[int, int] | None):
                Used only when mode == RCWL9623.GPIO_MODE. Provide (trig_pin, echo_pin),
                two pin numbers (ints).
            onewire_pin (int | None):
                Used only when mode == RCWL9623.ONEWIRE_MODE. Single OneWire pin number (int).
            uart (object | None):
                Used only when mode == RCWL9623.UART_MODE. Must pass an initialized UART instance;
                the driver will not create the UART. The object is expected to implement common
                UART methods (e.g., read, write).
            i2c (object | None):
                Used only when mode == RCWL9623.I2C_MODE. Must pass an initialized I2C instance;
                the driver will not create the I2C. The object is expected to implement common
                I2C methods (e.g., readfrom, writeto).
            addr (int | None):
                Optional I2C device address; if omitted, RCWL9623.I2C_DEFAULT_ADDR is used.

        Returns:
            None

        Raises:
            ValueError: If mode is invalid, required parameters for the selected mode are missing,
                        or parameter types are incorrect.
            ValueError: If provided uart/i2c objects do not meet minimal duck-typing checks.

        Note:
            - For UART and I2C modes callers must initialize and configure the respective instances
              (pins, baudrate, frequency, etc.) outside this constructor. The driver accepts instances
              only, which simplifies bus sharing and unit testing.
            - The constructor will create Pin instances for GPIO/OneWire modes; ensure provided pin
              numbers are valid for your platform.
            - This initializer performs non-ISR-safe operations (object creation and attribute checks)
              and must not be invoked from interrupt context.
        """
        # 判断工作模式参数是否合法
        if mode not in [RCWL9623.GPIO_MODE, RCWL9623.ONEWIRE_MODE, RCWL9623.UART_MODE, RCWL9623.I2C_MODE]:
            raise ValueError("unknown mode: %s" % mode)

        # 保存工作模式
        self.mode = mode

        # ---------------- GPIO模式 ----------------
        if self.mode == RCWL9623.GPIO_MODE:
            if not (isinstance(gpio_pins, (tuple, list)) and len(gpio_pins) == 2):
                raise ValueError("GPIO mode requires gpio_pins=(trig_pin, echo_pin)")
            trig_pin, echo_pin = gpio_pins
            # 简单类型检查
            if not isinstance(trig_pin, int) or not isinstance(echo_pin, int):
                raise ValueError("gpio_pins must be two integers (pin numbers)")
            self.trig = Pin(trig_pin, Pin.OUT)
            self.echo = Pin(echo_pin, Pin.IN)

        # ---------------- OneWire模式 ----------------
        elif self.mode == RCWL9623.ONEWIRE_MODE:
            if onewire_pin is None or not isinstance(onewire_pin, int):
                raise ValueError("OneWire mode requires onewire_pin (int)")
            self.pin = Pin(onewire_pin, Pin.OUT)

        # ---------------- UART模式 ----------------
        elif self.mode == RCWL9623.UART_MODE:
            # 严格要求传入实例（不再创建）
            if uart is None:
                raise ValueError("UART mode requires an initialized UART instance via 'uart='")
            # 可进行简单的鸭子类型检测
            if not (hasattr(uart, "read") and hasattr(uart, "write")):
                raise ValueError("provided 'uart' does not look like a UART instance")
            self.uart = uart

        # ---------------- I2C模式 ----------------
        elif self.mode == RCWL9623.I2C_MODE:
            if i2c is None:
                raise ValueError("I2C mode requires an initialized I2C instance via 'i2c='")
            if not (hasattr(i2c, "readfrom") and hasattr(i2c, "writeto")):
                raise ValueError("provided 'i2c' does not look like an I2C instance")
            self.i2c = i2c
            self.addr = addr if addr is not None else RCWL9623.I2C_DEFAULT_ADDR

    def read_distance(self) -> float:
        """
        测距主函数 — 根据当前工作模式分发到对应的私有实现并返回距离。

        Args:
            无

        Returns:
            float: 测得距离（单位 cm）。
            None: 测距失败或超出可测范围，或对应私有实现返回 None。

        Raises:
            ValueError: 当实例未按构造函数约束初始化为合法模式时（通常由构造函数保证，不会在此方法中出现）。
            Exception: 私有实现执行期间抛出的异常会原样向上传播，调用方应根据需要捕获处理。

        注意:
            - 本方法只是分发到对应的 `_read_*` 私有方法并返回其结果；各私有方法负责具体的 I/O 操作与错误处理。
            - 该方法会进行 GPIO / UART / I2C 操作，**非** ISR-safe，不能在中断上下文中调用。
            - 私有实现约定返回数值类型（int 或 float）表示成功，返回 None 表示测距失败；若私有实现返回其他类型，则视为实现错误。

        ==========================================

        Main distance-read entry point — dispatches to the mode-specific private implementation and returns the measured distance.

        Args:
            None

        Returns:
            float: Measured distance in centimeters.
            None: Measurement failure or out-of-range (when the underlying private implementation returns None).

        Raises:
            ValueError: If the instance was not initialized with a valid mode (normally enforced by the constructor).
            Exception: Any exception raised by the underlying private reader will propagate to the caller.

        Note:
            - This method only dispatches to the corresponding `_read_*` private method; those implementations perform the actual I/O and error handling.
            - This routine performs GPIO/UART/I2C operations and is NOT ISR-safe — do not call from interrupt context.
            - Private implementations should return a numeric type (int or float) on success or None on failure; other return types are considered implementation errors.
        """
        # 根据工作模式分发到对应的私有实现
        if self.mode == RCWL9623.GPIO_MODE:
            return self._read_gpio()
        elif self.mode == RCWL9623.ONEWIRE_MODE:
            return self._read_onewire()
        elif self.mode == RCWL9623.UART_MODE:
            return self._read_uart()
        elif self.mode == RCWL9623.I2C_MODE:
            return self._read_i2c()

    def _read_gpio(self) -> float:
        """
        GPIO 模式测距实现。

        功能:
            使用 TRIG 引脚产生 >10µs 的触发脉冲，ECHO 引脚测量返回脉冲宽度（µs），
            根据声速计算距离（单位 cm）。

        Args:
            无

        Returns:
            float: 测得距离（cm），保留两位小数。
            None: 测距失败（如等待上/下降沿超时）或超出可测范围（<2 cm 或 >700 cm）。

        Raises:
            无（本实现通过返回 None 表示测距失败；不抛出异常）。

        注意:
            - 使用 time.sleep_us() / time.ticks_us() 等精确定时函数，依赖于阻塞延时，**非 ISR-safe**。
            - 采用声速 343 m/s 进行换算：distance_cm = duration_us * 34300 / 1e6 / 2。
            - 对上/下降沿等待有超时保护（以避免长时间阻塞），超时时返回 None。
            - 调用前请确保 self.trig 和 self.echo 已由构造函数正确创建并配置为输出/输入。

        ==========================================

        GPIO-mode distance read implementation.

        Purpose:
            Generate a >10µs trigger pulse on TRIG and measure the echo pulse width on ECHO (in µs),
            then compute distance in centimeters using the speed of sound.

        Args:
            None

        Returns:
            float: Measured distance in cm (rounded to 2 decimals).
            None: Measurement failed (timeout) or out of measurement range (<2 cm or >700 cm).

        Raises:
            None (this implementation returns None to indicate failure instead of raising).

        Note:
            - Uses blocking timing functions (time.sleep_us, time.ticks_us) and is NOT ISR-safe.
            - Uses speed of sound 343 m/s for calculation:
              distance_cm = duration_us * 34300 / 1e6 / 2.
            - Has timeouts when waiting for rising/falling edges; on timeout returns None.
            - Ensure self.trig and self.echo are initialized and valid before calling.
        """
        # 触发一个 10us 脉冲
        # 先给一个>10us的高电平，然后拉低
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        # 等待 ECHO 上升沿
        timeout = 1000000
        count = 0
        while self.echo.value() == 0:
            count += 1
            if count > timeout:
                # 长时间低电平超时
                return None
        start = time.ticks_us()

        # 等待 ECHO 下降沿
        count = 0
        while self.echo.value() == 1:
            count += 1
            if count > timeout:
                # 长时间高电平超时
                return None
        end = time.ticks_us()

        # 计算时间差 -> 距离
        duration = time.ticks_diff(end, start)
        # 声速 343m/s
        distance_cm = duration * 34300 / 1000000 / 2
        if distance_cm < 2 or distance_cm > 700:
            return None
        # 保留两位小数
        return round(distance_cm, 2)

    def _read_onewire(self) -> float:
        """
        OneWire 模式测距实现。

        功能:
            使用单总线时序触发模块并通过 time_pulse_us 测量回波高电平宽度，换算为距离（cm）。

        Args:
            无

        Returns:
            float: 测得距离（cm），保留两位小数。
            None: 测距失败（例如 time_pulse_us 超时或测得距离超出范围 <2 cm 或 >700 cm）。

        Raises:
            无（捕获 time_pulse_us 引发的 OSError 并返回 None）。

        注意:
            - 使用 time_pulse_us API 测量脉冲宽度，可能在不同平台上引发 OSError 超时，本函数对此做捕获并返回 None。
            - 单总线时序依赖模块数据手册，请确保硬件/时序与文档一致。
            - 此方法为阻塞调用，**非 ISR-safe**。

        ==========================================

        OneWire-mode distance read implementation.

        Purpose:
            Trigger the sensor using a single-wire timing sequence and measure the echo high pulse
            width using time_pulse_us, then convert to distance in centimeters.

        Args:
            None

        Returns:
            float: Measured distance in cm (rounded to 2 decimals).
            None: Measurement failure (time_pulse_us timeout) or out of measurement range (<2 cm or >700 cm).

        Raises:
            None (OSError from time_pulse_us is caught and treated as measurement failure).

        Note:
            - Relies on time_pulse_us for pulse-width measurement; different ports/platforms may raise OSError on timeout.
            - Follow sensor datasheet for correct single-wire timing.
            - This routine is blocking and NOT ISR-safe.
        """
        # 触发脉冲
        # 单总线时序图，详细可查看数据手册说明文档
        self.pin.init(Pin.OUT)
        self.pin.value(1)
        time.sleep_us(14)
        self.pin.value(0)
        time.sleep_us(14)
        self.pin.value(1)
        self.pin.init(Pin.IN)

        try:
            # 测量高电平脉冲宽度
            duration = time_pulse_us(self.pin, 1, 30000)
        except OSError:
            return None

        distance_cm = (duration * 340) / 2 / 10000
        if distance_cm < 2 or distance_cm > 700:
            return None
        return round(distance_cm, 2)

    def _read_uart(self, max_retries: int = 5) -> float:
        """
        UART 模式测距实现。

        功能:
            通过串口发送触发命令（0xA0），等待模块返回 3 字节数据，并将三字节拼接后换算为距离（cm）。
            支持重试机制（默认 max_retries=5）。

        Args:
            max_retries (int): 最大重试次数，默认 5。

        Returns:
            float: 测得距离（cm），保留两位小数。
            None: 测距失败（连续重试均未获得有效数据）或距离不在期望范围。

        Raises:
            Exception: 底层 UART 操作（write/read）可能抛出的异常会向上传播，调用者可根据需要捕获。

        注意:
            - 在每次发送前会清空串口输入缓冲以避免旧数据干扰。
            - 等待时间与数据格式（3 字节，拼接为一个整数后除以 10000）基于模块协议，具体请参照设备手册。
            - 串口读写为阻塞/IO 操作，**非 ISR-safe**，并且对波特率和串口配置有依赖，调用前请确保 UART 实例配置正确。
        ==========================================

        UART-mode distance read implementation.

        Purpose:
            Send trigger command (0xA0) via UART, wait for a 3-byte reply, combine bytes into a single value,
            and convert to centimeters. Retries up to max_retries.

        Args:
            max_retries (int): Maximum number of retries (default 5).

        Returns:
            float: Measured distance in cm (rounded to 2 decimals).
            None: Measurement failed after retries or result out of expected range.

        Raises:
            Exception: Underlying UART operations (write/read) may raise errors which propagate to caller.

        Note:
            - Clears UART input buffer before triggering to avoid stale data.
            - Protocol: 3-byte response combined as (b0<<16) + (b1<<8) + b2, then divided by 10000 to get cm.
            - Blocking IO — NOT ISR-safe. Ensure UART is properly configured (baudrate, pins) before use.
        """
        for _ in range(max_retries):
            while self.uart.any():
                # 清空缓存
                self.uart.read()
            # 触发测距
            self.uart.write(bytes([0xA0]))
            # 等待模块处理
            time.sleep_ms(150)

            if self.uart.any() >= 3:
                data = self.uart.read(3)
                if data and len(data) == 3:
                    # 读取三个字节移位运算拼接成一个结果 详细可查看数据手册
                    distance = (data[0] << 16) + (data[1] << 8) + data[2]
                    distance_cm = distance / 10000
                    if 25 <= distance_cm <= 700:
                        return round(distance_cm, 2)
            time.sleep_ms(30)
        return None

    def _read_i2c(self) -> float:
        """
        I2C 模式测距实现。

        功能:
            通过 I2C 向设备地址写入触发命令（0x01），等待并读取 3 字节返回，拼接后换算为距离（cm）。

        Args:
            无

        Returns:
            float: 测得距离（cm），保留两位小数。
            None: 测距失败或返回数据不符合预期。

        Raises:
            RuntimeError: I2C 读写过程中发生异常时抛出，异常信息会包含底层异常描述。

        注意:
            - 发送触发命令后有固定延时等待模块处理（此处为 120 ms）。
            - 读取到的 3 字节按 (b0<<16) + (b1<<8) + b2 组合，然后除以 10000 得到 cm。
            - I2C 操作是阻塞的，**非 ISR-safe**；请确保传入的 self.i2c 是已正确初始化的 I2C 实例并且总线可用。
        ==========================================

        I2C-mode distance read implementation.

        Purpose:
            Write trigger command (0x01) to the device via I2C, wait, then read 3 bytes and convert them
            into a distance in centimeters.

        Args:
            None

        Returns:
            float: Measured distance in cm (rounded to 2 decimals).
            None: Measurement failed or data invalid.

        Raises:
            RuntimeError: On underlying I2C read/write error; the original exception is included in the message.

        Note:
            - After writing the trigger command, a processing delay (120 ms) is required before reading.
            - Protocol: combine 3 bytes as (b0<<16) + (b1<<8) + b2, then divide by 10000 to get cm.
            - Blocking I2C operations — NOT ISR-safe. Ensure self.i2c and self.addr are correct and the bus is free.
        """
        try:
            # 发送触发测距命令
            self.i2c.writeto(self.addr, bytes([0x01]))
            time.sleep_ms(120)

            # 读取 3 字节数据
            data = self.i2c.readfrom(self.addr, 3)
            if len(data) == 3:
                distance = (data[0] << 16) + (data[1] << 8) + data[2]
                distance_cm = distance / 10000
                if 2 <= distance_cm <= 700:
                    return round(distance_cm, 2)
        except Exception as e:
            raise RuntimeError("I2C read error: %s" % e)
        return None


# ========================================  主程序  ===========================================
