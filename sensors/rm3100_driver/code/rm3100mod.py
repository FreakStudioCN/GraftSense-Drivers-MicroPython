# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2022/01/01 00:00
# @Author  : Roman Shevchik (goctaprog@gmail.com)
# @File    : rm3100mod.py
# @Description : RM3100三轴地磁传感器驱动，支持单次/连续测量、自检、周期计数配置
# @License : MIT

__version__ = "1.0.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import struct
import micropython
from sensor_pack import bus_service, geosensmod
from sensor_pack.base_sensor import check_value, Iterator
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

@micropython.native
def _axis_to_int(axis) -> int:
    """
    将轴名称集合转换为整数（0~7）
    Args:
        axis: 包含 'X'/'Y'/'Z' 的字符串或集合
    Returns:
        int: 0=无轴, 1=X, 2=Y, 3=XY, 4=Z, 5=XZ, 6=YZ, 7=XYZ
    Raises:
        无
    Notes:
        - ISR-safe: 是
    ==========================================
    Convert axis name set to integer (0~7).
    Args:
        axis: String or set containing 'X'/'Y'/'Z'
    Returns:
        int: 0=none, 1=X, 2=Y, 3=XY, 4=Z, 5=XZ, 6=YZ, 7=XYZ
    Notes:
        - ISR-safe: Yes
    """
    _axis = 0
    _str_axis = 'XYZ'
    for index, axs in enumerate(_str_axis):
        if axs in axis or str.lower(axis) in axis:
            _axis += 2 ** index
    return _axis


@micropython.native
def _axis_name_to_int(axis_name: str) -> int:
    """
    将轴名称转换为索引（'x'/'X'→0, 'y'/'Y'→1, 'z'/'Z'→2）
    Args:
        axis_name (str): 轴名称，'x'/'y'/'z'（大小写不敏感）
    Returns:
        int: 0(X), 1(Y), 2(Z)
    Raises:
        ValueError: axis_name不在合法范围
    Notes:
        - ISR-safe: 是
    ==========================================
    Convert axis name to index ('x'/'X'→0, 'y'/'Y'→1, 'z'/'Z'→2).
    Args:
        axis_name (str): Axis name, 'x'/'y'/'z' (case insensitive)
    Returns:
        int: 0(X), 1(Y), 2(Z)
    Raises:
        ValueError: axis_name not in valid range
    Notes:
        - ISR-safe: Yes
    """
    an = axis_name.lower()
    check_value(ord(an[0]), range(120, 123), f"Invalid axis name: {axis_name}")
    return ord(an[0]) - 120  # 0, 1, 2


@micropython.native
def _int_to_axis_name(axis: int) -> str:
    """
    将轴索引转换为名称（0→'x', 1→'y', 2→'z'）
    """
    check_value(axis, range(3), "Invalid axis: %d" % axis)
    a = 'x', 'y', 'z'
    return a[axis]


@micropython.native
def _axis_name_to_reg_addr(axis_name: str, offset: int, multiplier: int) -> int:
    """将轴名称转换为对应寄存器地址"""
    return offset + multiplier * _axis_name_to_int(axis_name)


def _axis_name_to_ccr_addr(axis_name: str) -> int:
    """将轴名称转换为周期计数寄存器(CCR)地址"""
    return _axis_name_to_reg_addr(axis_name, 4, 2)


def _axis_name_to_mxyz_addr(axis_name: str) -> int:
    """将轴名称转换为测量结果寄存器(MXYZ)地址"""
    return _axis_name_to_reg_addr(axis_name, 0x24, 3)


def get_conversion_cycle_time(update_rate: int) -> int:
    """
    根据更新率返回转换周期时间（微秒）
    Args:
        update_rate (int): 更新率，0~13（0=600Hz, 1=300Hz, ..., 13=~0.075Hz）
    Returns:
        int: 转换周期时间（微秒）
    Raises:
        ValueError: update_rate超出范围
    Notes:
        - ISR-safe: 是
    ==========================================
    Return conversion cycle time in microseconds based on update rate.
    Args:
        update_rate (int): Update rate, 0~13 (0=600Hz, 1=300Hz, ..., 13=~0.075Hz)
    Returns:
        int: Conversion cycle time in microseconds
    Raises:
        ValueError: update_rate out of range
    Notes:
        - ISR-safe: Yes
    """
    check_value(update_rate, range(14), "Invalid update rate: %d" % update_rate)
    return 1667 * (2 ** update_rate)


def _from_bytes(source: bytes, big_byte_order: bool = True, signed=False) -> int:
    """字节序列转整数"""
    order = tuple(reversed(source)) if big_byte_order else tuple(source)
    n = sum(byte << 8 * index for index, byte in enumerate(order))
    if signed and order and (order[-1] & 0x80):
        n -= 1 << 8 * len(order)
    return n


def _to_str(source: bytes) -> str:
    """字节序列转十六进制字符串"""
    res = ''
    for item in source:
        res += "0x%x " % item
    return res


# ======================================== 自定义类 ============================================


class RM3100(geosensmod.GeoMagneticSensor, Iterator):
    """
    RM3100三轴地磁传感器驱动类（I2C接口）
    Attributes:
        _i2c (I2C): I2C总线实例
        _address (int): 设备I2C地址，0x20~0x23
        _update_rate (int): 更新率，0~13
    Methods:
        get_id(): 读取芯片版本ID
        is_continuous_meas_mode(): 判断是否连续测量模式
        is_data_ready(): 判断数据是否就绪
        perform_self_test(): 执行自检
        start_measure(): 启动测量
        get_axis_cycle_count(): 获取轴周期计数
        set_axis_cycle_count(): 设置轴周期计数
        get_meas_result(): 获取测量结果
        deinit(): 释放资源
    Notes:
        - 依赖外部传入I2C适配器实例
        - 初始化时自动配置DRC寄存器
    ==========================================
    RM3100 3-axis geomagnetic sensor driver (I2C interface).
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address, 0x20~0x23
        _update_rate (int): Update rate, 0~13
    Methods:
        get_id(): Read chip revision ID
        is_continuous_meas_mode(): Check if in continuous measurement mode
        is_data_ready(): Check if data is ready
        perform_self_test(): Perform self-test
        start_measure(): Start measurement
        get_axis_cycle_count(): Get axis cycle count
        set_axis_cycle_count(): Set axis cycle count
        get_meas_result(): Get measurement result
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C adapter instance
        - Auto-configures DRC register on init
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x20):
        """
        初始化RM3100传感器
        Args:
            adapter: I2C总线适配器实例
            address (int): I2C设备地址，0x20~0x23，默认0x20
        Returns:
            None
        Raises:
            ValueError: address超出范围
        Notes:
            - ISR-safe: 否
            - 副作用：写入DRC寄存器配置
        ==========================================
        Initialize RM3100 sensor.
        Args:
            adapter: I2C bus adapter instance
            address (int): I2C device address, 0x20~0x23, default 0x20
        Returns:
            None
        Raises:
            ValueError: address out of range
        Notes:
            - ISR-safe: No
            - Side effects: Writes DRC register config
        """
        self._buf_2 = bytearray((0 for _ in range(2)))
        self._buf_3 = bytearray((0 for _ in range(3)))
        self._buf_9 = bytearray((0 for _ in range(9)))
        self._update_rate = 6
        check_value(address, range(0x20, 0x24), "Invalid address value: 0x%x" % address)
        super().__init__(adapter=adapter, address=address, big_byte_order=True)
        self.setup()

    def _read_reg(self, reg_addr: int, bytes_count: int = 1) -> bytes:
        """
        读取寄存器值
        Args:
            reg_addr (int): 寄存器地址
            bytes_count (int): 读取字节数，默认1
        Returns:
            bytes: 读取到的字节数据
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read register value.
        Args:
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read, default 1
        Returns:
            bytes: Read byte data
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def read_buf_from_mem(self, mem_addr: int, buf: bytearray):
        """
        从设备内存地址读取数据到缓冲区
        Args:
            mem_addr (int): 设备内存起始地址
            buf (bytearray): 目标缓冲区，读取字节数由缓冲区长度决定
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read data from device memory address into buffer.
        Args:
            mem_addr (int): Device memory start address
            buf (bytearray): Target buffer; bytes read equals buffer length
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self.adapter.read_buf_from_mem(self.address, mem_addr, buf)

    def _write_reg(self, reg_addr: int, value: int, bytes_count: int = 1):
        """
        向寄存器写入值
        Args:
            reg_addr (int): 寄存器地址
            value (int): 写入值
            bytes_count (int): 写入字节数，默认1
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write value to register.
        Args:
            reg_addr (int): Register address
            value (int): Value to write
            bytes_count (int): Number of bytes to write, default 1
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        bo = self._get_byteorder_as_str()[0]
        self.adapter.write_register(self.address, reg_addr, value, bytes_count, bo)

    def _set_update_rate(self, update_rate: int):
        """
        设置连续测量模式的更新率
        Args:
            update_rate (int): 更新率，0~13（0=600Hz, ..., 13=~0.075Hz）
        Returns:
            None
        Raises:
            ValueError: update_rate超出范围
        Notes:
            - ISR-safe: 否
            - 副作用：写入TMRC寄存器(0x0B)
        ==========================================
        Set update rate for continuous measurement mode.
        Args:
            update_rate (int): Update rate, 0~13 (0=600Hz, ..., 13=~0.075Hz)
        Returns:
            None
        Raises:
            ValueError: update_rate out of range
        Notes:
            - ISR-safe: No
            - Side effects: Writes TMRC register (0x0B)
        """
        check_value(update_rate, range(14), "Invalid update rate: %d" % update_rate)
        # 写入TMRC寄存器，基准值0x92加上更新率偏移
        self._write_reg(0x0B, 0x92 + update_rate)
        self._update_rate = update_rate

    def _get_update_rate(self) -> int:
        """
        读取当前更新率
        Returns:
            int: 当前更新率，0~13
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current update rate.
        Returns:
            int: Current update rate, 0~13
        Notes:
            - ISR-safe: No
        """
        self._update_rate = self._read_reg(0x0B)[0] - 0x92
        return self._update_rate

    def _get_cmm(self) -> int:
        """
        读取CMM寄存器值
        Returns:
            int: CMM寄存器值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read CMM register value.
        Returns:
            int: CMM register value
        Notes:
            - ISR-safe: No
        """
        return self._read_reg(0x01)[0]

    def get_id(self) -> int:
        """
        读取芯片版本ID（REVID寄存器）
        Args:
            无
        Returns:
            int: 芯片版本ID
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read chip revision ID (REVID register).
        Args:
            None
        Returns:
            int: Chip revision ID
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._read_reg(0x36)[0]

    def is_continuous_meas_mode(self) -> bool:
        """
        判断是否处于连续测量模式
        Args:
            无
        Returns:
            bool: True=连续测量模式，False=单次测量模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if in continuous measurement mode.
        Args:
            None
        Returns:
            bool: True=continuous mode, False=single mode
        Notes:
            - ISR-safe: No
        """
        return 0 != (0x01 & self._get_cmm())

    def is_single_meas_mode(self) -> bool:
        """
        判断是否处于单次测量模式
        Args:
            无
        Returns:
            bool: True=单次测量模式，False=连续测量模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if in single measurement mode.
        Args:
            None
        Returns:
            bool: True=single mode, False=continuous mode
        Notes:
            - ISR-safe: No
        """
        return 0 == (0x01 & self._get_cmm())

    def get_status(self) -> tuple:
        """
        读取传感器状态寄存器
        Args:
            无
        Returns:
            tuple: (drdy,) — DRDY位，True表示数据就绪
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor status register.
        Args:
            None
        Returns:
            tuple: (drdy,) — DRDY bit, True means data ready
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        stat = self._read_reg(0x34)[0]
        return 0 != (stat & 0x80),

    def is_data_ready(self) -> bool:
        """
        判断测量数据是否就绪
        Args:
            无
        Returns:
            bool: True=数据就绪，False=数据未就绪
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if measurement data is ready.
        Args:
            None
        Returns:
            bool: True=data ready, False=not ready
        Notes:
            - ISR-safe: No
        """
        return self.get_status()[0]

    def perform_self_test(self) -> tuple:
        """
        执行内置自检程序
        Args:
            无
        Returns:
            tuple: (z_ok, y_ok, x_ok, timeout_period, lr_periods)
                   z_ok/y_ok/x_ok: 各轴自检通过标志
                   timeout_period: 超时周期（0~3）
                   lr_periods: LR周期（0~3）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：临时修改CMM/HSHAKE/BIST寄存器，完成后清除STE位
        ==========================================
        Perform built-in self-test.
        Args:
            None
        Returns:
            tuple: (z_ok, y_ok, x_ok, timeout_period, lr_periods)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Temporarily modifies CMM/HSHAKE/BIST registers; clears STE bit on exit
        """
        bist_addr = 0x33
        poll_addr = 0x00
        cmm_addr = 0x00
        hshake_addr = 0x35
        try:
            # 停止连续测量，配置握手寄存器
            self._write_reg(reg_addr=0x00, value=0x70)
            self._write_reg(reg_addr=0x35, value=0x08)
            # 启动内置自检
            self._write_reg(bist_addr, 0x8F)
            # 触发三轴测量
            self._write_reg(poll_addr, 0x70)
            counter = 0
            while True:
                time.sleep_ms(10)
                if counter > 3 or self.get_status()[0]:
                    break
                counter += 1
            bist = self._read_reg(bist_addr)[0]
            # 解析各轴自检结果及周期参数
            return 0 != bist & 0x40, 0 != bist & 0x20, 0 != bist & 0x10, (bist & 0b1100) >> 2, bist & 0b11
        finally:
            # 清除STE位，退出自检模式
            self._write_reg(reg_addr=bist_addr, value=0x00)

    def soft_reset(self):
        """
        执行软件复位（预留接口）
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Perform software reset (reserved interface).
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        pass

    def start_measure(self, axis, update_rate: int = 6,
                      single_mode: bool = True, full_meas_seq: bool = True):
        """
        启动单次或连续测量
        Args:
            axis: 包含轴名称的字符串或集合，如 'XYZ'、{'X','Y','Z'}
            update_rate (int): 连续模式更新率，0~13，默认6
            single_mode (bool): True=单次测量，False=连续测量，默认True
            full_meas_seq (bool): True=全部轴完成后DRDY置1，False=任一轴完成即置1，默认True
        Returns:
            None
        Raises:
            ValueError: update_rate超出范围
        Notes:
            - ISR-safe: 否
            - 副作用：写入CMM/POLL寄存器
        ==========================================
        Start single or continuous measurement.
        Args:
            axis: String or set containing axis names, e.g. 'XYZ' or {'X','Y','Z'}
            update_rate (int): Continuous mode update rate, 0~13, default 6
            single_mode (bool): True=single measurement, False=continuous, default True
            full_meas_seq (bool): True=DRDY set after all axes done, False=after any axis, default True
        Returns:
            None
        Raises:
            ValueError: update_rate out of range
        Notes:
            - ISR-safe: No
            - Side effects: Writes CMM/POLL registers
        """
        _axis = _axis_to_int(axis=axis)
        # CMM和POLL寄存器中轴位从第4位开始
        _axis <<= 4
        data_ready_mode = 0 if full_meas_seq else 1
        if not single_mode:
            # 连续测量模式：设置更新率并写入CMM寄存器
            self._set_update_rate(update_rate)
            self._write_reg(reg_addr=0x01, value=_axis | (data_ready_mode << 2) | 0x01)
        else:
            # 单次测量模式：禁用连续模式，触发单次测量
            self._write_reg(reg_addr=0x01, value=0)
            self._write_reg(reg_addr=0x00, value=_axis)

    def set_axis_cycle_count(self, axis_name: str, value: int):
        """
        设置指定轴的周期计数值
        Args:
            axis_name (str): 轴名称，'x'/'y'/'z'（大小写不敏感）
            value (int): 周期计数值，建议范围30~400，默认200
        Returns:
            None
        Raises:
            ValueError: axis_name不合法
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入对应轴的CCR寄存器
        ==========================================
        Set cycle count for specified axis.
        Args:
            axis_name (str): Axis name, 'x'/'y'/'z' (case insensitive)
            value (int): Cycle count, recommended range 30~400, default 200
        Returns:
            None
        Raises:
            ValueError: Invalid axis_name
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes corresponding axis CCR register
        """
        addr = _axis_name_to_ccr_addr(axis_name)
        bo_t = self._get_byteorder_as_str()
        # 将16位周期计数值按字节序打包写入CCR寄存器
        bts = struct.pack(bo_t[1] + "H", value)
        self.adapter.write_register(self.address, addr, bts, 0, '')

    def get_axis_cycle_count(self, axis_name: str) -> int:
        """
        读取指定轴的周期计数值
        Args:
            axis_name (str): 轴名称，'x'/'y'/'z'（大小写不敏感）
        Returns:
            int: 周期计数值
        Raises:
            ValueError: axis_name不合法
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read cycle count for specified axis.
        Args:
            axis_name (str): Axis name, 'x'/'y'/'z' (case insensitive)
        Returns:
            int: Cycle count value
        Raises:
            ValueError: Invalid axis_name
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        addr = _axis_name_to_ccr_addr(axis_name)
        #bts = self._read_reg(addr, 2)
        bts = self._buf_2
        # 复用缓冲区读取2字节CCR寄存器
        self.read_buf_from_mem(addr, bts)
        return self.unpack(fmt_char="H", source=bts)[0]

    def read_raw(self, axis_name: int) -> int:
        """
        读取指定轴的原始24位测量值
        Args:
            axis_name (int): 轴索引，0=X, 1=Y, 2=Z
        Returns:
            int: 有符号24位原始磁场值
        Raises:
            ValueError: axis_name超出范围
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw 24-bit measurement value for specified axis.
        Args:
            axis_name (int): Axis index, 0=X, 1=Y, 2=Z
        Returns:
            int: Signed 24-bit raw magnetic field value
        Raises:
            ValueError: axis_name out of range
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        addr = _axis_name_to_mxyz_addr(_int_to_axis_name(axis_name))
        #bts = self._read_reg(reg_addr=addr, bytes_count=3)  # 24 bit value (int24)
        bts = self._buf_3
        # 复用缓冲区读取3字节测量结果
        self.read_buf_from_mem(addr, bts)
        return _from_bytes(source=bts, big_byte_order=True, signed=True)

    def _get_all_meas_result(self) -> tuple:
        """
        一次性读取三轴全部测量结果（最快读取方式）
        Args:
            无
        Returns:
            tuple: (x, y, z) 三轴有符号24位原始磁场值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 一次I2C事务读取9字节，效率最高
        ==========================================
        Read all three-axis measurement results in one call (fastest method).
        Args:
            None
        Returns:
            tuple: (x, y, z) signed 24-bit raw magnetic field values
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Reads 9 bytes in a single I2C transaction for maximum efficiency
        """
        bts = self._buf_9
        # 从0x24起一次读取9字节（三轴各3字节）
        self.read_buf_from_mem(0x24, bts)
        t = (_from_bytes(source=bts[3 * index:3 * (index + 1)], big_byte_order=True, signed=True) for index in range(3))
        return tuple(t)

    def setup(self):
        """
        配置传感器工作模式（DRC寄存器）
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入DRC寄存器，设置DRC0=0, DRC1=1
        ==========================================
        Configure sensor operating mode (DRC register).
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes DRC register, sets DRC0=0, DRC1=1
        """
        # DRC0=0, DRC1=1，配置数据就绪控制
        self._write_reg(reg_addr=0x35, value=0x0A)
        pass

    def __iter__(self):
        return self

    def __next__(self):
        """
        迭代器接口，仅在连续测量模式下返回数据
        Returns:
            tuple or None: 数据就绪时返回三轴测量结果，否则返回None
        Notes:
            - ISR-safe: 否
            - 仅在连续测量模式下有效
        ==========================================
        Iterator interface, returns data only in continuous measurement mode.
        Returns:
            tuple or None: Three-axis measurement result if ready, else None
        Notes:
            - ISR-safe: No
            - Only valid in continuous measurement mode
        """
        if self.is_continuous_meas_mode() and self.is_data_ready():
            return self.get_axis(-1)
        return None

    def deinit(self):
        """
        释放传感器资源，停止所有测量
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入CMM寄存器停止连续测量
        ==========================================
        Release sensor resources and stop all measurements.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes CMM register to stop continuous measurement
        """
        # 写入0停止连续测量模式
        self._write_reg(reg_addr=0x01, value=0x00)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
