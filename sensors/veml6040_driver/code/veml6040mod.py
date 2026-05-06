# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2022/01/01 00:00
# @Author  : Roman Shevchik (goctaprog@gmail.com)
# @File    : veml6040mod.py
# @Description : VEML6040 RGBW颜色传感器驱动，支持自动/单次测量、积分时间配置、迭代器接口
# @License : MIT

__version__ = "1.0.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import array
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, Iterator, check_value, all_none
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _check_integration_time(integr_time: int):
    """
    校验积分时间参数合法性（0~5）
    Args:
        integr_time (int): 积分时间索引，0~5
            0=40ms, 1=80ms, 2=160ms, 3=320ms, 4=640ms, 5=1280ms
    Raises:
        ValueError: integr_time超出范围
    Notes:
        - ISR-safe: 是
    ==========================================
    Validate integration time parameter (0~5).
    Args:
        integr_time (int): Integration time index, 0~5
            0=40ms, 1=80ms, 2=160ms, 3=320ms, 4=640ms, 5=1280ms
    Raises:
        ValueError: integr_time out of range
    Notes:
        - ISR-safe: Yes
    """
    check_value(integr_time, range(6), "Invalid integration_time value: %d" % integr_time)


def get_g_max_lux(integr_time: int) -> tuple:
    """
    根据积分时间索引返回G_SENSITIVITY和最大可检测照度
    Args:
        integr_time (int): 积分时间索引，0~5
    Returns:
        tuple: (G_SENSITIVITY, MAX_DETECTABLE_LUX)
    Raises:
        ValueError: integr_time超出范围
    Notes:
        - ISR-safe: 是
    ==========================================
    Return G_SENSITIVITY and MAX_DETECTABLE_LUX for given integration time index.
    Args:
        integr_time (int): Integration time index, 0~5
    Returns:
        tuple: (G_SENSITIVITY, MAX_DETECTABLE_LUX)
    Raises:
        ValueError: integr_time out of range
    Notes:
        - ISR-safe: Yes
    """
    _check_integration_time(integr_time)
    k = 1 / (1 << integr_time)
    return 0.25168 * k, 16496 * k


# ======================================== 自定义类 ============================================


class VEML6040(DeviceEx, Iterator):
    """
    VEML6040 RGBW颜色传感器驱动类（I2C接口）
    Attributes:
        _integration_time (int): 积分时间索引，0~5
        _trig (bool): 单次触发标志
        _auto (bool): 自动测量模式标志
        _shutdown (bool): 传感器关断状态
        _buf_4 (array): 4通道16位无符号整数缓冲区
    Methods:
        get_conversion_cycle_time(): 返回当前积分时间对应的转换周期（ms）
        get_colors(): 读取RGBW四通道颜色数据
        start_measurement(): 启动自动或单次测量
        integration_time: 当前积分时间索引（只读属性）
        auto_mode: 是否自动测量模式（只读属性）
        shutdown: 传感器关断状态（可读写属性）
        deinit(): 关断传感器并释放资源
    Notes:
        - 依赖外部传入I2C适配器实例
        - 初始化时自动从传感器读取当前配置
        - I2C地址固定为0x10，不可更改
    ==========================================
    VEML6040 RGBW color sensor driver (I2C interface).
    Attributes:
        _integration_time (int): Integration time index, 0~5
        _trig (bool): Single-trigger flag
        _auto (bool): Auto measurement mode flag
        _shutdown (bool): Sensor shutdown state
        _buf_4 (array): 4-channel 16-bit unsigned integer buffer
    Methods:
        get_conversion_cycle_time(): Return conversion cycle time for current integration time (ms)
        get_colors(): Read RGBW four-channel color data
        start_measurement(): Start auto or single measurement
        integration_time: Current integration time index (read-only property)
        auto_mode: Whether in auto measurement mode (read-only property)
        shutdown: Sensor shutdown state (read/write property)
        deinit(): Shut down sensor and release resources
    Notes:
        - Requires externally provided I2C adapter instance
        - Automatically reads current config from sensor on init
        - I2C address fixed at 0x10, cannot be changed
    """

    def __init__(self, adapter: bus_service.BusAdapter, address=0x10):
        """
        初始化VEML6040传感器
        Args:
            adapter (BusAdapter): I2C总线适配器实例
            address (int): I2C设备地址，默认0x10（固定值）
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：从传感器读取当前配置并缓存到实例属性
        ==========================================
        Initialize VEML6040 sensor.
        Args:
            adapter (BusAdapter): I2C bus adapter instance
            address (int): I2C device address, default 0x10 (fixed)
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Reads current config from sensor and caches to instance attributes
        """
        super().__init__(adapter, address, False)
        self._integration_time = self._trig = self._auto = self._shutdown = None
        # 4通道16位无符号整数缓冲区（R/G/B/W）
        self._buf_4 = array.array("H", [0 for _ in range(4)])
        # 从传感器读取当前配置
        self._get_settings()

    def _get_settings(self):
        """
        从传感器读取当前配置并缓存到实例属性
        Notes:
            - ISR-safe: 否
            - 副作用：更新_integration_time/_trig/_auto/_shutdown
        ==========================================
        Read current config from sensor and cache to instance attributes.
        Notes:
            - ISR-safe: No
            - Side effects: Updates _integration_time/_trig/_auto/_shutdown
        """
        # 读取CONF寄存器（2字节，仅低字节有效）
        _conf = self._settings()
        # 解析各配置位：积分时间(bit6:4)、触发(bit2)、自动/手动(bit1)、关断(bit0)
        result = (0b0111_0000 & _conf) >> 4, 0 != (0b100 & _conf), 0 == (0b10 & _conf), 0b01 & _conf
        self._integration_time, self._trig, self._auto, self._shutdown = result

    @micropython.native
    def get_conversion_cycle_time(self) -> int:
        """
        返回当前积分时间对应的转换周期（毫秒）
        Args:
            无
        Returns:
            int: 转换周期（ms），40~1280
        Notes:
            - ISR-safe: 是
        ==========================================
        Return conversion cycle time for current integration time (milliseconds).
        Args:
            None
        Returns:
            int: Conversion cycle time (ms), 40~1280
        Notes:
            - ISR-safe: Yes
        """
        _check_integration_time(self._integration_time)
        return 40 * (1 << self._integration_time)

    def _settings(self,
                  it=None,
                  trig=None,
                  af=None,
                  sd=None,
                  ):
        """
        读取或写入CONF配置寄存器
        Args:
            it (int or None): 积分时间索引(bit6:4)，None=不修改
            trig (bool or None): 单次触发(bit2)，None=不修改
            af (bool or None): 强制模式(bit1)，None=不修改
            sd (bool or None): 关断(bit0)，None=不修改
        Returns:
            int or None: 所有参数为None时返回寄存器当前值，否则返回None
        Notes:
            - ISR-safe: 否
            - 副作用：写入时修改CONF寄存器
        ==========================================
        Read or write CONF configuration register.
        Args:
            it (int or None): Integration time index (bit6:4), None=no change
            trig (bool or None): Single trigger (bit2), None=no change
            af (bool or None): Force mode (bit1), None=no change
            sd (bool or None): Shutdown (bit0), None=no change
        Returns:
            int or None: Register value if all params None, else None
        Notes:
            - ISR-safe: No
            - Side effects: Writes CONF register when modifying
        """
        val = self.read_reg(0x00, 2)[0]
        if all_none(it, trig, af, sd):
            return val
        if it is not None:
            val &= ~0b0111_0000
            val |= it << 4
        if trig is not None:
            val &= ~(1 << 2)
            val |= trig << 2
        if af is not None:
            val &= ~(1 << 1)
            val |= af << 1
        if sd is not None:
            val &= 0xFE
            val |= sd
        self.write_reg(0x00, val, 2)

    def get_colors(self) -> tuple:
        """
        读取RGBW四通道颜色数据
        Args:
            无
        Returns:
            tuple: (red, green, blue, white) 各通道16位原始ADC值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read RGBW four-channel color data.
        Args:
            None
        Returns:
            tuple: (red, green, blue, white) 16-bit raw ADC values per channel
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        buf = self._buf_4
        for index in range(len(buf)):
            buf[index] = self.unpack(fmt_char="H", source=self.read_reg(0x08 + index, 2))[0]
        return tuple(buf)

    def start_measurement(self, integr_time: int, auto_mode: bool):
        """
        启动自动或单次测量
        Args:
            integr_time (int): 积分时间索引，0~5
                0=40ms, 1=80ms, 2=160ms, 3=320ms, 4=640ms, 5=1280ms
            auto_mode (bool): True=自动连续测量，False=单次触发测量
        Returns:
            None
        Raises:
            ValueError: integr_time超出范围
        Notes:
            - ISR-safe: 否
            - 副作用：写入CONF寄存器，更新缓存配置
        ==========================================
        Start auto or single measurement.
        Args:
            integr_time (int): Integration time index, 0~5
                0=40ms, 1=80ms, 2=160ms, 3=320ms, 4=640ms, 5=1280ms
            auto_mode (bool): True=auto continuous, False=single trigger
        Returns:
            None
        Raises:
            ValueError: integr_time out of range
        Notes:
            - ISR-safe: No
            - Side effects: Writes CONF register, updates cached config
        """
        _check_integration_time(integr_time)
        self._settings(it=integr_time, trig=not auto_mode, af=not auto_mode)
        # 更新缓存配置
        self._get_settings()

    @property
    def integration_time(self) -> int:
        """
        当前积分时间索引（只读）
        Returns:
            int: 积分时间索引，0~5
        Notes:
            - ISR-safe: 是
        ==========================================
        Current integration time index (read-only).
        Returns:
            int: Integration time index, 0~5
        Notes:
            - ISR-safe: Yes
        """
        return self._integration_time

    @property
    def auto_mode(self) -> bool:
        """
        是否处于自动连续测量模式（只读）
        Returns:
            bool: True=自动模式，False=单次模式
        Notes:
            - ISR-safe: 是
        ==========================================
        Whether in auto continuous measurement mode (read-only).
        Returns:
            bool: True=auto mode, False=single mode
        Notes:
            - ISR-safe: Yes
        """
        return 0 != self._auto

    @property
    def shutdown(self) -> bool:
        """
        传感器关断状态
        Returns:
            bool: True=已关断，False=正常工作
        Notes:
            - ISR-safe: 是
        ==========================================
        Sensor shutdown state.
        Returns:
            bool: True=shutdown, False=active
        Notes:
            - ISR-safe: Yes
        """
        return 0 != self._shutdown

    @shutdown.setter
    def shutdown(self, value: bool = True):
        """
        设置传感器关断状态
        Args:
            value (bool): True=关断传感器，False=启动传感器
        Notes:
            - ISR-safe: 否
            - 副作用：写入CONF寄存器sd位，更新_shutdown缓存
        ==========================================
        Set sensor shutdown state.
        Args:
            value (bool): True=shutdown sensor, False=enable sensor
        Notes:
            - ISR-safe: No
            - Side effects: Writes CONF register sd bit, updates _shutdown cache
        """
        self._settings(None, None, None, value)
        self._shutdown = value

    def __next__(self):
        """
        迭代器接口，仅在自动模式且未关断时返回颜色数据
        Returns:
            tuple or None: 自动模式且未关断时返回(R,G,B,W)，否则返回None
        Notes:
            - ISR-safe: 否
        ==========================================
        Iterator interface, returns color data only in auto mode when not shutdown.
        Returns:
            tuple or None: (R,G,B,W) in auto mode when active, else None
        Notes:
            - ISR-safe: No
        """
        if self.shutdown or not self.auto_mode:
            return None
        return self.get_colors()

    def deinit(self):
        """
        关断传感器并释放资源
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：设置shutdown=True停止测量
        ==========================================
        Shut down sensor and release resources.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Sets shutdown=True to stop measurement
        """
        self.shutdown = True


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
