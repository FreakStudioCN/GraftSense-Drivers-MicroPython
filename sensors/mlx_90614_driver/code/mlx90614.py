# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/27 上午11:50
# @Author  : 缪贵成
# @File    : mlx90614.py
# @Description : mlx90614双温区传感器
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

#导入模块用于数据打包和解包
import ustruct
from machine import I2C, Pin

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

class SensorBase:
    """
    基类，提供寄存器读取与温度换算功能。

    Attributes:
        i2c (I2C): 已初始化的 I2C 对象。
        address (int): 设备 I2C 地址。
        dual_zone (bool): 是否支持双温区（仅部分 MLX90614 型号）。

    Methods:
        _read16(register: int) -> int: 从寄存器读取 16 位原始值（内部方法）。
        _read_temp(register: int) -> float: 从寄存器读取温度并转换为摄氏度（内部方法）。
        read_ambient() -> float: 读取环境温度（℃）。
        read_object() -> float: 读取物体温度（℃）。
        read_object2() -> float: 读取第二路物体温度（℃），仅双温区可用。

    Notes:
        不直接使用外部调用，只提供给子类继承使用。

    ==========================================

    Base class providing register read and temperature conversion.

    Attributes:
        i2c (I2C): Initialized I2C object.
        address (int): Device I2C address.
        dual_zone (bool): True if dual-zone sensor (only some MLX90614 models).

    Methods:
        _read16(register: int) -> int: Read 16-bit raw value from register (internal method).
        _read_temp(register: int) -> float: Read temperature from register and convert to Celsius (internal method).
        read_ambient() -> float: Read ambient temperature (℃).
        read_object() -> float: Read object temperature (℃).
        read_object2() -> float: Read second object temperature (℃), dual-zone only.

    Notes:
        Not intended for direct use. Designed for subclass inheritance.
    """

    def _read16(self, register: int) -> int:
        """
        从寄存器读取 16 位原始值（内部使用）。

        Args:
            register (int): 寄存器地址。

        Returns:
            int: 16 位原始值。

        Notes:
            仅内部方法，不直接暴露给外部调用。

        ==========================================

        Read 16-bit raw value from register (internal use).

        Args:
            register (int): Register address.

        Returns:
            int: 16-bit raw value.

        Notes:
            Internal use only.
        """
        data = self.i2c.readfrom_mem(self.address, register, 2)
        # 小端字节序，H表示16位无符号整数，返回一个元组，取第0个数据表示取元组的数据
        return ustruct.unpack('<H', data)[0]

    def _read_temp(self, register: int) -> float:
        """
        从寄存器读取温度并转换为摄氏度（内部使用）。

        Args:
            register (int): 寄存器地址。

        Returns:
            float: 温度值（℃）。

        Notes:
            返回值经过 0.02 系数缩放并由开尔文转为摄氏度。

        ==========================================

        Read temperature from register and convert to Celsius (internal use).

        Args:
            register (int): Register address.

        Returns:
            float: Temperature in Celsius.

        Notes:
            Scaled by 0.02 per LSB and converted from Kelvin.
        """
        temp = self._read16(register)
        temp *= 0.02
        temp -= 273.15
        return temp

    def read_ambient(self) -> float:
        """
        读取环境温度（℃）。
        Returns:
            float: 环境温度。

        Notes:
            调用 _read_temp 读取寄存器 0x06。

        ==========================================

        Read ambient temperature (℃).

        Returns:
            float: Ambient temperature.

        Notes:
            Reads register 0x06 internally using _read_temp.
        """
        #从环境温度寄存器里面读取值
        return self._read_temp(self._REGISTER_TA)

    def read_object(self) -> float:
        """
        读取物体温度（℃）。

        Returns:
            float: 物体温度。

        Notes:
            调用 _read_temp 读取寄存器 0x07。

        ==========================================

        Read object temperature (℃).

        Returns:
            float: Object temperature.

        Notes:
            Reads register 0x07 internally using _read_temp.
        """
        return self._read_temp(self._REGISTER_TOBJ1)

    def read_object2(self) -> float:
        """
        读取第二路物体温度（℃），仅双温区可用。

        Returns:
            float: 第二路物体温度。

        Raises:
            RuntimeError: 非双温区传感器调用时。

        Notes:
            调用 _read_temp 读取寄存器 0x08。

        ==========================================

        Read second object temperature (℃), dual-zone only.

        Returns:
            float: Second object temperature.

        Raises:
            RuntimeError: If device is not dual-zone.

        Notes:
            Reads register 0x08 internally using _read_temp.
        """
        if self.dual_zone:
            return self._read_temp(self._REGISTER_TOBJ2)
        else:
            raise RuntimeError("Device only has one thermopile")

    @property
    def ambient(self) -> float:
        """
        获取环境温度，等同于 read_ambient() 方法。

        Returns:
            float: 环境温度，单位摄氏度（℃）。

        Notes:
            仅读取最近一次测量值。
            可直接通过 sensor.ambient 访问。

        ==========================================

        Get ambient temperature, equivalent to read_ambient() method.

        Returns:
            float: Ambient temperature in Celsius (℃).

        Notes:
            Returns the most recent measurement.
            Can be accessed directly via sensor.ambient.
        """
        return self.read_ambient()

    @property
    def object(self) -> float:
        """
        获取物体温度，等同于 read_object() 方法。

        Returns:
            float: 物体温度，单位摄氏度（℃）。

        Notes:
            仅读取最近一次测量值。
            可直接通过 sensor.object 访问。

        ==========================================

        Get object temperature, equivalent to read_object() method.

        Returns:
            float: Object temperature in Celsius (℃).

        Notes:
            Returns the most recent measurement.
            Can be accessed directly via sensor.object.
        """
        return self.read_object()

    @property
    def object2(self) -> float:
        """
        获取第二路物体温度，等同于 read_object2() 方法。

        Returns:
            float: 第二路物体温度，单位摄氏度（℃）。

        Notes:
            仅读取最近一次测量值。
            可直接通过 sensor.object2 访问。

        ==========================================

        Get second object temperature, equivalent to read_object2() method.

        Returns:
            float: Second object temperature in Celsius (℃).

        Notes:
            Returns the most recent measurement.
            Can be accessed directly via sensor.object2.
        """
        return self.read_object2()

class MLX90614(SensorBase):
    """
    MLX90614 传感器驱动类，支持单区/双区热电堆版本。

    Attributes:
        i2c (I2C): 已初始化的 I2C 对象。
        address (int): 设备地址。
        dual_zone (bool): 是否支持双温区，读取配置寄存器获取。

    Methods:
        init(i2c, address: int = None) -> None: 初始化传感器。
        read() -> dict: 一次性读取 ambient、object、object2 数据。
        get() -> dict: read 的别名方法。

    Notes:
        dual_zone 根据寄存器配置自动解析。

    ==========================================

    MLX90614 sensor driver class, supports single/dual thermopile versions.

    Attributes:
        i2c (I2C): Initialized I2C object.
        address (int): Device address.
        dual_zone (bool): True if dual-zone, parsed from configuration register.

    Methods:
        init(i2c, address: int = None) -> None: Initialize sensor.
        read() -> dict: Read ambient, object, object2 data at once.
        get() -> dict: Alias for read().

    Notes:
        dual_zone parsed automatically from device register.
    """

    _REGISTER_TA = 0x06
    _REGISTER_TOBJ1 = 0x07
    _REGISTER_TOBJ2 = 0x08

    def __init__(self, i2c, address: int = None):
        """
        初始化 MLX90614。

        Args:
            i2c (I2C): 已创建的 I2C 对象。
            address (int): 设备地址。

        Raises:
            TypeError: i2c 不是 I2C 实例，address 不是 int。
            ValueError: address 不在 MLX90614 的合法 I2C 地址范围内。

        Notes:
            dual_zone 根据寄存器配置自动解析。
            根据手册默认地址0x5a,实际上我们通过判断连接设备后扫描到的符合范围的设备地址进行I2C地址的传入。

        ==========================================

        Initialize MLX90614.

        Args:
            i2c (I2C): Initialized I2C object.
            address (int): Device address.

        Raises:
            TypeError: If i2c is not an I2C instance, or address is not int.
            ValueError: If address is out of MLX90614 allowed range.

        Notes:
            dual_zone parsed from configuration register.
            According to the manual, the default address is 0x5a. In practice, we pass the I2C address by determining the device address within the acceptable range after scanning the connected devices.
        """
        # 参数校验
        if not isinstance(i2c, I2C):
            raise TypeError(f"i2c must be an I2C instance, got {type(i2c).__name__}")
        if not isinstance(address, int):
            raise TypeError(f"address must be int, got {type(address).__name__}")
        if not (0x5A <= address <= 0x5D):
            raise ValueError(f"Invalid MLX90615 I2C address: 0x{address:x}")
        self.i2c = i2c
        self.address = address
        _config1 = i2c.readfrom_mem(address, 0x25, 2)
        _dz = ustruct.unpack('<H', _config1)[0] & (1 << 6)
        self.dual_zone = True if _dz else False

    def read(self) -> dict:
        """
        一次性读取传感器数据，返回字典。

        Returns:
            dict: {'ambient': float, 'object': float, 'object2': float 或 None}

        Notes:
            如果非双温区，object2 为 None。

        ==========================================

        Read all sensor data at once, return as dictionary.

        Returns:
            dict: {'ambient': float, 'object': float, 'object2': float or None}

        Notes:
            object2 is None if not dual-zone.
        """
        return {
            "ambient": self.read_ambient(),
            "object": self.read_object(),
            "object2": self.read_object2() if self.dual_zone else None,
        }

    def get(self) -> dict:
        """
        读取传感器数据的别名方法，功能与 read() 完全相同。

        Returns:
            dict: 返回传感器当前的测量数据，具体字段和说明参见 read() 方法。

        Notes:
            该方法仅作为 read() 的别名，方便统一接口调用。

        ==========================================

        Alias method for reading sensor data, identical to read().

        Returns:
            dict: Returns the current measurement data from the sensor.
                  See read() method for detailed field descriptions.

        Notes:
            This method is simply an alias of read(), provided for interface consistency.
        """
        return self.read()

class MLX90615(SensorBase):
    """
    MLX90615 传感器驱动类，仅单区热电堆版本。

    Attributes:
        i2c (I2C): 已初始化的 I2C 对象。
        address (int): 设备地址。
        dual_zone (bool): 总为 False，不支持双温区。

    Methods:
        __init__(i2c, address: int = None) -> None: 初始化传感器。

    Notes:
        不支持 object2。

    ==========================================

    MLX90615 sensor driver class, single thermopile only.

    Attributes:
        i2c (I2C): Initialized I2C object.
        address (int): Device address.
        dual_zone (bool): Always False, no dual-zone support.

    Methods:
        __init__(i2c, address: int = None) -> None: Initialize sensor.

    Notes:
        object2 is not available.
    """

    def __init__(self, i2c, address: int = None):
        """
        初始化 MLX90615。

        Args:
            i2c (I2C): 已创建的 I2C 对象。
            address (int): i2c设备地址。

        Raises:
            TypeError: i2c 不是 I2C 实例，address 不是 int。
            ValueError: address 不在 MLX90615 的合法 I2C 地址范围内。

        Notes:
            不支持 dual_zone。
            根据手册默认地址0x5b,实际上我们通过判断连接设备后扫描到的符合范围的设备地址进行I2C地址的传入。

        ==========================================

        Initialize MLX90615.

        Args:
            i2c (I2C): Initialized I2C object.
            address (int):i2c Device address.

        Raises:
            TypeError: If i2c is not an I2C instance, or address is not int.
            ValueError: If address is out of MLX90615 allowed range.

        Notes:
            dual_zone is always False.
            According to the manual, the default address is 0x5b. In practice, we pass the I2C address by determining the device address within the acceptable range after scanning the connected devices.
        """
        # 参数校验
        if not isinstance(i2c, I2C):
            raise TypeError(f"i2c must be an I2C instance, got {type(i2c).__name__}")

        if not isinstance(address, int):
            raise TypeError(f"address must be int, got {type(address).__name__}")

        if not (0x5A <= address <= 0x5D):
            raise ValueError(f"Invalid MLX90615 I2C address: 0x{address:x}")
        self.i2c = i2c
        self.address = address
        self.dual_zone = False

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
