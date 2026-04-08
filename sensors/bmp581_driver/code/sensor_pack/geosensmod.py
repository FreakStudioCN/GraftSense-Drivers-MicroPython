# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026-03-23 下午5:00
# @Author  : octaprog7
# @File    : geo_magnetic_sensor.py
# @Description : 地磁传感器基类模块，提供轴名称转换、寄存器地址计算等辅助功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# MicroPython
# mail: goctaprog@gmail.com
# MIT license

# ======================================== 导入相关模块 =========================================

from sensor_pack.base_sensor import BaseSensor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _axis_to_int(axis: [set, str]) -> int:
    """
    将包含轴名称的集合或字符串转换为整数掩码
    Args:
        axis (set, str): 包含 'X', 'Y', 'Z' 的集合或字符串

    Returns:
        int: 0-7 的整数，位 0 对应 X，位 1 对应 Y，位 2 对应 Z

    Notes:
        输入示例：{'X', 'Y'} 返回 3 (0b011)；'XZ' 返回 5 (0b101)

    ==========================================
    Convert a set or string containing axis names to an integer mask
    Args:
        axis (set, str): Set or string containing 'X', 'Y', 'Z'

    Returns:
        int: Integer from 0 to 7, bit 0 for X, bit 1 for Y, bit 2 for Z

    Notes:
        Example: {'X', 'Y'} returns 3 (0b011); 'XZ' returns 5 (0b101)
    """
    _axis = 0
    _str_axis = "XYZ"
    for index, axs in enumerate(_str_axis):
        if axs in axis or str.lower(axis) in axis:
            _axis += 2**index

    return _axis


def _axis_name_to_int(axis_name: str) -> int:
    """
    将轴名称字符串转换为整数索引
    Args:
        axis_name (str): 轴名称，如 'x', 'X', 'y', 'Y', 'z', 'Z'

    Returns:
        int: 0 (X), 1 (Y), 2 (Z)

    Raises:
        ValueError: 当轴名称无效时

    ==========================================
    Convert axis name string to integer index
    Args:
        axis_name (str): Axis name, e.g., 'x', 'X', 'y', 'Y', 'z', 'Z'

    Returns:
        int: 0 (X), 1 (Y), 2 (Z)

    Raises:
        ValueError: When axis name is invalid
    """
    an = axis_name.lower()
    if not ord(an[0]) in range(120, 123):
        raise ValueError(f"Invalid axis name: {axis_name}")
    return ord(an[0]) - 120  # 0, 1, 2


def check_axis_value(axis: int) -> None:
    """
    检查轴数值是否有效（0, 1, 2）
    Args:
        axis (int): 轴索引

    Raises:
        ValueError: 当轴索引不在 0-2 范围内时

    ==========================================
    Check if axis index is valid (0, 1, 2)
    Args:
        axis (int): Axis index

    Raises:
        ValueError: When axis index is not in 0-2 range
    """
    if axis not in range(3):
        raise ValueError(f"Invalid axis name: {axis}")


def _axis_number_to_str(axis: int) -> str:
    """
    将轴索引转换为字符串
    Args:
        axis (int): 0 (X), 1 (Y), 2 (Z)

    Returns:
        str: 'x', 'y', 'z'

    Raises:
        ValueError: 当轴索引无效时

    ==========================================
    Convert axis index to string
    Args:
        axis (int): 0 (X), 1 (Y), 2 (Z)

    Returns:
        str: 'x', 'y', 'z'

    Raises:
        ValueError: When axis index is invalid
    """
    check_axis_value(axis)
    an = "x", "y", "z"
    return an[axis]


def axis_name_to_reg_addr(axis_name: int, offset: int, multiplier: int) -> int:
    """
    将轴索引转换为寄存器地址
    Args:
        axis_name (int): 轴索引 (0,1,2)
        offset (int): 基础地址偏移
        multiplier (int): 每个轴占用的寄存器数量

    Returns:
        int: 对应轴的寄存器地址

    ==========================================
    Convert axis index to register address
    Args:
        axis_name (int): Axis index (0,1,2)
        offset (int): Base address offset
        multiplier (int): Number of registers per axis

    Returns:
        int: Register address for the axis
    """
    return offset + multiplier * axis_name


# ======================================== 自定义类 ============================================


class GeoMagneticSensor(BaseSensor):
    """
    地磁传感器基类，定义磁场测量的标准接口
    Methods:
        get_axis(): 获取指定轴或所有轴的磁场测量值
        _get_all_meas_result(): 获取所有轴测量结果（需子类实现）
        is_data_ready(): 检查数据是否就绪
        is_continuous_meas_mode(): 检查是否处于连续测量模式
        is_single_meas_mode(): 检查是否处于单次测量模式
        in_standby_mode(): 检查是否处于待机模式
        perform_self_test(): 执行自检
        get_conversion_cycle_time(): 获取转换周期时间
        get_meas_result(): 获取指定轴的原始测量值
        read_raw(): 读取原始数据（需子类实现）
        get_status(): 获取传感器状态
        start_measure(): 启动测量

    Notes:
        子类必须实现 _get_all_meas_result() 和 read_raw() 等抽象方法。

    ==========================================
    Base class for geomagnetic sensors, defining standard interface for magnetic field measurement
    Methods:
        get_axis(): Get measurement for specified axis or all axes
        _get_all_meas_result(): Get measurement results for all axes (must be implemented by subclass)
        is_data_ready(): Check if data is ready
        is_continuous_meas_mode(): Check if continuous measurement mode is enabled
        is_single_meas_mode(): Check if single measurement mode is enabled
        in_standby_mode(): Check if sensor is in standby mode
        perform_self_test(): Perform self-test
        get_conversion_cycle_time(): Get conversion cycle time
        get_meas_result(): Get raw measurement value for specified axis
        read_raw(): Read raw data (must be implemented by subclass)
        get_status(): Get sensor status
        start_measure(): Start measurement

    Notes:
        Subclasses must implement abstract methods _get_all_meas_result() and read_raw().
    """

    def get_axis(self, axis: [int, str]) -> [int, tuple]:
        """
        获取指定轴或所有轴的磁场测量值
        Args:
            axis (int, str): 轴索引 (0,1,2) 或字符串 ('x','y','z')，或 -1 表示所有轴

        Returns:
            int, tuple: 指定轴的测量值（int），或所有轴的元组 (X,Y,Z)

        Notes:
            如果 axis == -1，则返回 _get_all_meas_result() 的结果。

        ==========================================
        Get magnetic field measurement for specified axis or all axes
        Args:
            axis (int, str): Axis index (0,1,2) or string ('x','y','z'), or -1 for all axes

        Returns:
            int, tuple: Measurement value for specified axis (int), or tuple (X,Y,Z) for all axes

        Notes:
            If axis == -1, returns result of _get_all_meas_result().
        """
        if isinstance(axis, int) and -1 == axis:
            return self._get_all_meas_result()
        return self.get_meas_result(axis)

    def _get_all_meas_result(self) -> tuple:
        """
        获取所有轴测量结果（子类必须实现）
        Returns:
            tuple: 包含 X, Y, Z 测量值的元组

        Raises:
            NotImplementedError: 子类未实现时抛出

        ==========================================
        Get measurement results for all axes (must be implemented by subclass)
        Returns:
            tuple: Tuple containing X, Y, Z measurement values

        Raises:
            NotImplementedError: When not implemented by subclass
        """
        raise NotImplementedError

    def is_data_ready(self) -> bool:
        """
        检查数据是否就绪
        Returns:
            bool: True 表示数据就绪，False 表示未就绪

        ==========================================
        Check if data is ready
        Returns:
            bool: True if data ready, False otherwise
        """
        raise NotImplementedError

    def is_continuous_meas_mode(self) -> bool:
        """
        检查是否处于连续测量模式
        Returns:
            bool: True 表示连续测量模式，False 表示非连续模式

        ==========================================
        Check if continuous measurement mode is enabled
        Returns:
            bool: True if continuous measurement mode, False otherwise
        """
        raise NotImplementedError

    def is_single_meas_mode(self) -> bool:
        """
        检查是否处于单次测量模式
        Returns:
            bool: True 表示单次测量模式，False 表示非单次模式

        ==========================================
        Check if single measurement mode is enabled
        Returns:
            bool: True if single measurement mode, False otherwise
        """
        raise NotImplementedError

    def in_standby_mode(self) -> bool:
        """
        检查是否处于待机模式
        Returns:
            bool: True 表示待机模式，False 表示非待机模式

        ==========================================
        Check if sensor is in standby mode
        Returns:
            bool: True if standby mode, False otherwise
        """
        raise NotImplementedError

    def perform_self_test(self) -> None:
        """
        执行自检
        ==========================================
        Perform self-test
        """
        raise NotImplementedError

    def get_conversion_cycle_time(self) -> int:
        """
        获取转换周期时间
        Returns:
            int: 转换周期时间（毫秒或微秒）

        ==========================================
        Get conversion cycle time
        Returns:
            int: Conversion cycle time (milliseconds or microseconds)
        """
        raise NotImplementedError

    def get_meas_result(self, axis_name: [str, int]) -> int:
        """
        获取指定轴的原始测量值
        Args:
            axis_name (str, int): 轴名称（'x','y','z'）或索引（0,1,2）

        Returns:
            int: 原始测量值

        ==========================================
        Get raw measurement value for specified axis
        Args:
            axis_name (str, int): Axis name ('x','y','z') or index (0,1,2)

        Returns:
            int: Raw measurement value
        """
        _axis = axis_name if isinstance(axis_name, int) else _axis_name_to_int(axis_name)
        return self.read_raw(_axis)

    def read_raw(self, axis: int) -> int:
        """
        读取指定轴的原始数据（子类必须实现）
        Args:
            axis (int): 轴索引 (0,1,2)

        Returns:
            int: 原始数据

        ==========================================
        Read raw data for specified axis (must be implemented by subclass)
        Args:
            axis (int): Axis index (0,1,2)

        Returns:
            int: Raw data
        """
        raise NotImplementedError

    def get_status(self):
        """
        获取传感器状态
        ==========================================
        Get sensor status
        """
        raise NotImplementedError

    def start_measure(self) -> None:
        """
        启动测量
        ==========================================
        Start measurement
        """
        raise NotImplementedError


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
