# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/16 下午8:16
# @Author  : 缪贵成
# @File    : tcs34725_color.py
# @Description : 基于TCS34725的颜色识别模块驱动文件，参考自https://github.com/adafruit/micropython-adafruit-tcs34725
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import machine
import time
import ustruct
from micropython import const
from machine import Pin

# ======================================== 全局变量 ============================================

_COMMAND_BIT = const(0x80)

_REGISTER_ENABLE = const(0x00)
_REGISTER_ATIME = const(0x01)

_REGISTER_AILT = const(0x04)
_REGISTER_AIHT = const(0x06)

_REGISTER_ID = const(0x12)

_REGISTER_APERS = const(0x0c)

_REGISTER_CONTROL = const(0x0f)

_REGISTER_SENSORID = const(0x12)

_REGISTER_STATUS = const(0x13)
_REGISTER_CDATA = const(0x14)
_REGISTER_RDATA = const(0x16)
_REGISTER_GDATA = const(0x18)
_REGISTER_BDATA = const(0x1a)

_ENABLE_AIEN = const(0x10)
_ENABLE_WEN = const(0x08)
_ENABLE_AEN = const(0x02)
_ENABLE_PON = const(0x01)

_GAINS = (1, 4, 16, 60)
_CYCLES = (0, 1, 2, 3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class TCS34725:
    """
    该类控制 TCS34725 RGB 光谱传感器，提供增益、积分时间、光谱数据读取和中断阈值配置。

    Attributes:
        i2c (I2C): machine.I2C 实例，用于 I2C 总线通信。
        address (int): 设备 I2C 地址。
        _active (bool): 当前传感器电源/测量状态。

    Methods:
        __init__(i2c, address: int = 0x29) -> None: 初始化 TCS34725 实例。
        _register8(register: int, value: int = None) -> int: 读写 8 位寄存器。
        _register16(register: int, value: int = None) -> int: 读写 16 位寄存器。
        active(value: bool = None) -> bool: 获取或设置传感器激活状态。
        sensor_id() -> int: 获取传感器 ID。
        integration_time(value: float = None) -> float: 获取或设置积分时间（ms）。
        gain(value: int = None) -> int: 获取或设置增益。
        _valid() -> bool: 检查数据是否可用。
        read(raw: bool = False) -> tuple: 读取光谱数据（RGB + Clear）。
        _temperature_and_lux(data: tuple) -> tuple: 将原始光谱数据转换为色温和光照。
        threshold(cycles: int = None, min_value: int = None, max_value: int = None) -> tuple: 设置或获取中断阈值。
        interrupt(value: bool = None) -> bool: 获取或清除中断状态。

    Notes:
        - 该类依赖 I2C 通信。
        - 不要在 ISR 中调用会执行 I2C 操作的方法（ISR-unsafe）。

    ==========================================

    TCS34725 driver for RGB color sensor.

    Attributes:
        i2c (I2C): I2C instance for communication.
        address (int): Device I2C address.
        _active (bool): Current sensor active state.

    Methods:__init__(i2c, address: int = 0x29) -> None: Initialize TCS34725 instance.
        _register8(register: int, value: int = None) -> int: Read and write 8-bit registers.
        _register16(register: int, value: int = None) -> int: Read and write 16-bit registers.
        active(value: bool = None) -> bool: Get or set sensor activation status.
        sensor_id() -> int: Get the sensor ID.
        integration_time(value: float = None) -> float: Get or set integration time (ms).
        gain(value: int = None) -> int: Get or set gain.
        _valid() -> bool: Check if data is available.
        read(raw: bool = False) -> tuple: Read spectral data (RGB Clear).
        _temperature_and_lux(data: tuple) -> tuple: Convert raw spectral data to color temperature and illumination.
        threshold(cycles: int = None, min_value: int = None, max_value: int = None) -> tuple: Set or get interrupt threshold.
        interrupt(value: bool = None) -> bool: Get or clear interrupt status.

    Notes:
        Methods performing I2C are not ISR-safe.
    """

    def __init__(self, i2c, address=None, int_pin: Pin = None, led_pin=None):
        """
        初始化 TCS34725 实例。

        Args:
            i2c (I2C): I2C 实例，必须已经初始化。
            address (int): 传感器 I2C 地址。
            int_pin(Pin):中断引脚。
            led_pin:led控制引脚编号。

        Raises:
            ValueError: address 不在规定范围内或者不是I2C实例。
            RuntimeError: 检测到错误的传感器 ID。

        Notes:
            初始化会读取 sensor ID 并设置默认积分时间。
            非 ISR-safe。

        ==========================================

        Initialize TCS34725 instance.

        Args:
            i2c (I2C): I2C instance, must be initialized.
            address (int): Device I2C address, default 0x29.
            int_pin:interrupt number.
            led_pin:led number.

        Raises:
            ValueError: The address is out of the specified range or is not an I2C instance..
            RuntimeError: Wrong sensor ID detected.

        Notes:
            Not ISR-safe.
        """
        if not isinstance(i2c, machine.I2C):
            raise ValueError("i2c parameter must be a machine.I2C instance")
        if not isinstance(address, int) or not (0x03 <= address <= 0x77):
            raise ValueError("address parameter must be int and in range 0x03~0x77")
        self.led_pin = led_pin
        self.i2c = i2c
        self.address = address
        self.int_pin = int_pin

        self._active = False
        # 设置积分时间，积分时间会影响这个传感器的检测精度和灵敏度
        self.integration_time(2.4)
        sensor_id = self.sensor_id()
        if sensor_id not in (0x44, 0x10):
            raise RuntimeError("wrong sensor id 0x{:x}".format(sensor_id))

    def _register8(self, register, value=None) -> int | None:
        """
        读写 8 位寄存器。

        Args:
            register (int): 寄存器地址。
            value (int | None): 要写入的值 (0..255)，None 表示执行读取操作。

        Returns:
            int: 当 value 为 None 时返回寄存器的当前值 (0..255)。
                 当执行写操作时返回 None。

        Notes:
            - 内部会自动加上 _COMMAND_BIT。
            - 非 ISR-safe。
        ==========================================

        Read or write an 8-bit register.

        Args:
            register (int): Register address.
            value (int | None): Value to write (0..255). None means read.

        Returns:
            int: Current register value (0..255) if reading, else None.

        Notes:
            - Automatically adds _COMMAND_BIT.
            - Not ISR-safe.
        """
        register |= _COMMAND_BIT
        if value is None:
            return self.i2c.readfrom_mem(self.address, register, 1)[0]
        data = ustruct.pack('<B', value)
        self.i2c.writeto_mem(self.address, register, data)

    def _register16(self, register, value=None) -> int | None:
        """
        读写 16 位寄存器。

        Args:
            register (int): 寄存器地址。
            value (int | None): 要写入的值 (0..65535)，None 表示执行读取操作。

        Returns:
            int: 当 value 为 None 时返回寄存器的当前值 (0..65535)。
                 当执行写操作时返回 None。

        Notes:
            - 内部会自动加上 _COMMAND_BIT。
            - 非 ISR-safe。
        ==========================================

        Read or write a 16-bit register.

        Args:
            register (int): Register address.
            value (int | None): Value to write (0..65535). None means read.

        Returns:
            int: Current register value (0..65535) if reading, else None.

        Notes:
            - Automatically adds _COMMAND_BIT.
            - Not ISR-safe.
        """
        register |= _COMMAND_BIT
        if value is None:
            data = self.i2c.readfrom_mem(self.address, register, 2)
            return ustruct.unpack('<H', data)[0]
        data = ustruct.pack('<H', value)
        self.i2c.writeto_mem(self.address, register, data)

    def active(self, value=None, led_pin: Pin = None) -> bool:
        """
        获取或设置传感器的激活状态。

        Args:
            value (bool, optional): True 激活，False 关闭。如果为 None，则返回当前状态。
            led_pin:板载指示灯

        Returns:
            bool: 当前传感器是否处于激活状态。

        Notes:
            - 激活传感器会先上电，然后启用 ADC。
            - 方法内部包含延时操作。

        ==========================================

        Get or set sensor active state.

        Args:
            value (bool, optional): True to activate, False to deactivate. None to get status,led_pin.
            Onboard indicator light

        Returns:
            bool: True if active, False otherwise.

        Notes:
            - Enabling sensor powers on and enables ADC.
            - Contains delay operations.

        """
        if led_pin is not None:
            if isinstance(led_pin, int):  # 若传入的是 GPIO 编号（如 25）
                self.led_pin = Pin(led_pin, Pin.OUT)
            elif isinstance(led_pin, Pin):  # 若传入的是已创建的 Pin 对象
                self.led_pin = led_pin
            else:
                raise ValueError("led_pin must be GPIO number (int) or Pin object")
        # 若未初始化过 led_pin，创建空属性避免后续报错
        if not hasattr(self, 'led_pin'):
            self.led_pin = None

        if value is None:
            return self._active
        value = bool(value)
        if self._active == value:
            return
        self._active = value
        enable = self._register8(_REGISTER_ENABLE)

        if value:
            # 激活传感器：上电 → 启用 ADC → 点亮 LED（若有）
            self._register8(_REGISTER_ENABLE, enable | _ENABLE_PON)
            time.sleep_ms(3)
            self._register8(_REGISTER_ENABLE, enable | _ENABLE_PON | _ENABLE_AEN)
            if self.led_pin is not None:
                self.led_pin.value(1)
        else:
            # 关闭传感器：关闭 ADC 和电源 → 熄灭 LED（若有）
            self._register8(_REGISTER_ENABLE, enable & ~(_ENABLE_PON | _ENABLE_AEN))
            if self.led_pin is not None:  # 仅在 led_pin 有效时操作
                self.led_pin.value(0)


    def sensor_id(self) -> int:
        """
        读取传感器 ID。

        Returns:
            int: 传感器 ID。

        Notes:
            - 合法的 ID 通常为 0x44 或 0x10。

        ==========================================

        Read sensor ID.

        Returns:
            int: Sensor ID.

        Notes:
            - Valid IDs are typically 0x44 or 0x10.
        """
        return self._register8(_REGISTER_SENSORID)

    def integration_time(self, value=None) -> float:
        """
        设置或获取积分时间（Integration Time）。

        Args:
            value (float, optional): 积分时间，单位毫秒。范围 2.4 ~ 614.4 ms。
                                     如果为 None，则返回当前积分时间。

        Returns:
            float: 当前有效积分时间（ms）。

        Notes:
            - 该方法会进行 I2C 写操作（非 ISR-safe）。
            - 值会被自动对齐到 2.4 ms 的倍数。
            - 设置时会立即更新寄存器。

        ==========================================

        Set or get integration time.

        Args:
            value (float, optional): Integration time in milliseconds (2.4–614.4 ms).
                                     If None, return current integration time.

        Returns:
            float: Effective integration time (ms).

        Notes:
            - Performs I2C write (not ISR-safe).
            - Value aligned to multiples of 2.4 ms.
            - Updates ATIME register immediately when set.
        """
        if value is None:
            return self._integration_time
        value = min(614.4, max(2.4, value))
        cycles = int(value / 2.4)
        self._integration_time = cycles * 2.4
        return self._register8(_REGISTER_ATIME, 256 - cycles)

    def gain(self, value) -> int:
        """
        设置或获取增益值。

        Args:
            value (int, optional): 增益值，可选 1, 4, 16, 60。
                                   如果为 None，则返回当前增益。

        Returns:
            int: 当前增益值。

        Raises:
            ValueError: 传入的结果不符合界定的值。

        Notes:
            - 增益值决定传感器对光强的灵敏度。

        ==========================================

        Set or get gain value.

        Args:
            value (int, optional): Gain value, must be 1, 4, 16, or 60.
                                   If None, return current gain.

        Returns:
            int: Current gain value.

        Raises:
            ValueError: If invalid gain provided.

        Notes:
            - Gain determines sensor sensitivity to light.
        """
        if value is None:
            return _GAINS[self._register8(_REGISTER_CONTROL)]
        if value not in _GAINS:
            raise ValueError("gain must be 1, 4, 16 or 60")
        return self._register8(_REGISTER_CONTROL, _GAINS.index(value))

    def _valid(self):

        return bool(self._register8(_REGISTER_STATUS) & 0x01)

    def read(self, raw=False) -> tuple:
        """
        读取传感器颜色数据。

        Args:
            raw (bool, optional): 如果为 True，则返回原始 (R, G, B, C) 数据；
                                  否则返回 (色温, 亮度)。

        Returns:
            tuple: 原始或转换后的测量数据。

        Notes:
            - 方法会阻塞直到数据有效。
            - 数据包括红、绿、蓝和透明通道。

        ==========================================

        Read sensor color data.

        Args:
            raw (bool, optional): True to return raw (R, G, B, C) data;
                                  False to return (CCT, Lux).

        Returns:
            tuple: Raw or converted measurement data.

        Notes:
            - Blocks until data is valid.
            - Includes Red, Green, Blue, and Clear channels.
        """
        was_active = self.active()
        self.active(True)
        while not self._valid():
            time.sleep_ms(int(self._integration_time + 0.9))
        data = tuple(self._register16(register) for register in (
            _REGISTER_RDATA,
            _REGISTER_GDATA,
            _REGISTER_BDATA,
            _REGISTER_CDATA,
        ))
        self.active(was_active)
        if raw:
            return data
        return self._temperature_and_lux(data)

    def _temperature_and_lux(self, data) -> tuple:
        """
        计算色温 (CCT) 与亮度 (Y)。

        Args:
            data (tuple): 原始通道数据，格式为 (R, G, B, C)，每项为 int。

        Returns:
            tuple: (cct, y)
                cct (float): 对应的相关色温，单位开尔文 (K)。
                y (float): 亮度分量 Y（线性亮度近似，单位与原始 ADC 一致）。

        Notes:
            - 该计算使用典型的 RGB -> XYZ 线性变换系数并估算 CCT。
            - 该方法非 ISR-safe，调用前请确保在任务上下文中执行。

        ==========================================

        Calculate correlated color temperature (CCT) and luminance component (Y).

        Args:
            data (tuple): Raw channel tuple (R, G, B, C) of ints.

        Returns:
            tuple: (cct, y)
                cct (float): Correlated color temperature in Kelvin.
                y (float): Luminance component Y (units same as ADC counts).

        Notes:
            - Uses linear RGB->XYZ transform and CCT approximation.
            - Not ISR-safe.
        """
        r, g, b, c = data
        x = -0.14282 * r + 1.54924 * g + -0.95641 * b
        y = -0.32466 * r + 1.57837 * g + -0.73191 * b
        z = -0.68202 * r + 0.77073 * g + 0.56332 * b
        d = x + y + z
        n = (x / d - 0.3320) / (0.1858 - y / d)
        cct = 449.0 * n ** 3 + 3525.0 * n ** 2 + 6823.3 * n + 5520.33
        return cct, y

    def threshold(self, cycles=None, min_value=None, max_value=None) -> tuple | None:
        """
        获取或设置近似中断阈值（persistence cycles 与上下阈值）。

        Args:
            cycles (int | None): 持续周期数，取值为 _CYCLES 中的某一项或 -1 表示禁用中断。
                                 如果为 None，则表示不修改 cycles。
            min_value (int | None): 下阈值（AILT），0..65535。None 表示不修改。
            max_value (int | None): 上阈值（AIHT），0..65535。None 表示不修改。

        Returns:
            tuple: (cycles, min_value, max_value)
                当三参数均为 None 时，作为查询返回当前 (cycles, min_value, max_value)。
                否则返回 None（执行写入操作）。

        Raises:
            ValueError: cycles、min_value 或 max_value 非法时抛出（例如 cycles 不在允许集合中或阈值超出 0..65535）。

        Notes:
            - 调用会执行 I2C 读写操作，非 ISR-safe。
            - cycles 为 -1 时表示禁用中断，否则应为 _CYCLES 中的值。

        ==========================================

        Get or set interrupt threshold (persistence cycles and low/high thresholds).

        Args:
            cycles (int | None): Persistence cycles; one of _CYCLES or -1 to disable interrupt.
                                 None to leave unchanged.
            min_value (int | None): Low threshold (AILT), 0..65535. None to leave unchanged.
            max_value (int | None): High threshold (AIHT), 0..65535. None to leave unchanged.

        Returns:
            tuple: (cycles, min_value, max_value) when querying (all args None).
            Otherwise returns None after performing writes.

        Raises:
            ValueError: If cycles/min_value/max_value are invalid.

        Notes:
            - Performs I2C read/write, not ISR-safe.
            - Use cycles == -1 to disable interrupt.
        """
        if cycles is None and min_value is None and max_value is None:
            min_value = self._register16(_REGISTER_AILT)
            max_value = self._register16(_REGISTER_AILT)
            if self._register8(_REGISTER_ENABLE) & _ENABLE_AIEN:
                cycles = _CYCLES[self._register8(_REGISTER_APERS) & 0x0f]
            else:
                cycles = -1
            return cycles, min_value, max_value
        if min_value is not None:
            self._register16(_REGISTER_AILT, min_value)
        if max_value is not None:
            self._register16(_REGISTER_AIHT, max_value)
        if cycles is not None:
            enable = self._register8(_REGISTER_ENABLE)
            if cycles == -1:
                self._register8(_REGISTER_ENABLE, enable & ~(_ENABLE_AIEN))
            else:
                self._register8(_REGISTER_ENABLE, enable | _ENABLE_AIEN)
                if cycles not in _CYCLES:
                    raise ValueError("invalid persistence cycles")
                self._register8(_REGISTER_APERS, _CYCLES.index(cycles))

    def interrupt(self, value=None) -> bool | None:
        """
        获取或清除中断标志。

        Args:
            value (bool | None): None 表示读取中断使能状态(返回 bool)。
                                 False 表示清除中断(写入清除命令)。
                                 传入 True 会抛出 ValueError(不允许设置为 True)。

        Returns:
            bool | None: 当 value 为 None 时返回当前中断使能状态（True/False）。
                         当执行清除操作时返回 None。

        Raises:
            ValueError: 当尝试传入 True(仅允许清除，不能设置为 True)时抛出。

        Notes:
            - 清除中断会向设备写入清除命令 0xE6。
            - 该方法会进行 I2C 读/写，非 ISR-safe。

        ==========================================

        Get or clear interrupt status.

        Args:
            value (bool | None): None to read status (returns bool).
                                 False to clear interrupt.
                                 Passing True is invalid and will raise ValueError.

        Returns:
            bool | None: Current interrupt-enable status when value is None, otherwise None.

        Raises:
            ValueError: If value is True (setting interrupt to True is not allowed).

        Notes:
            - Clears interrupt by writing 0xE6 to device.
            - Performs I2C operations, not ISR-safe.
        """
        if value is None:
            return bool(self._register8(_REGISTER_STATUS) & _ENABLE_AIEN)
        if value:
            raise ValueError("interrupt can only be cleared")
        self.i2c.writeto(self.address, b'\xe6')


def html_rgb(data) -> tuple:
    """
    将原始 RGBC 数据转换为线性校正后的 HTML RGB 值（0..255）。

    Args:
        data (tuple): 原始通道数据 (R, G, B, C)，每项为数值型。

    Returns:
        tuple: (red, green, blue) 三元组，浮点数或整数表示 0..255 的色彩分量。

    Notes:
        - 使用简单的伽玛/缩放近似对颜色进行映射。
        - 非 ISR-safe。

    ==========================================

    Convert raw RGBC to HTML RGB values (0..255).

    Args:
        data (tuple): Raw (R, G, B, C) channel values.

    Returns:
        tuple: (red, green, blue) each in 0..255 range (float).

    Notes:
        - Uses a simple gamma/scale approximation.
        - Not ISR-safe.
    """
    r, g, b, c = data
    red = pow((int((r / c) * 256) / 255), 2.5) * 255
    green = pow((int((g / c) * 256) / 255), 2.5) * 255
    blue = pow((int((b / c) * 256) / 255), 2.5) * 255
    return red, green, blue


def html_hex(data) -> str:
    """
    将原始 RGBC 数据转换为 HTML 16 进制颜色字符串。

    Args:
        data (tuple): 原始通道数据 (R, G, B, C)。

    Returns:
        str: 6 位十六进制颜色字符串，例如 'ff00cc'。

    ==========================================

    Convert raw RGBC to HTML hex color string.

    Args:
        data (tuple): Raw (R, G, B, C) channel values.

    Returns:
        str: 6-digit hex color string, e.g. 'ff00cc'.
    """
    r, g, b = html_rgb(data)
    return "{0:02x}{1:02x}{2:02x}".format(int(r),
                                          int(g),
                                          int(b))


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
