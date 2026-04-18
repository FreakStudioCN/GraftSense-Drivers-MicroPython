# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Roman Shevchik
# @File    : regmod.py
# @Description : 硬件寄存器表示，支持只读和读写寄存器，并提供位域访问
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, get_error_str, check_value
from sensor_pack_2.bitfield import BitFields

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class BaseRegistry:
    """
    硬件寄存器基类，表示一个具有位域结构的寄存器
    Attributes:
        _device (DeviceEx | None): 所属设备对象
        _address (int): 寄存器地址
        _fields (BitFields): 位域信息存储对象
        _byte_len (int): 寄存器字节宽度（1或2字节）
        _value (int): 寄存器当前缓存值

    Methods:
        _get_width(): 根据位域信息计算寄存器所需字节数
        __len__(): 返回位域个数
        __getitem__(): 通过位域名获取位域值
        __setitem__(): 通过位域名设置位域值
        value(): 获取当前缓存的寄存器值
        byte_len(): 获取寄存器字节宽度

    Notes:
        仅支持1或2字节宽的寄存器，位域步长必须为1

    ==========================================
    Base class for hardware register with bit fields
    Attributes:
        _device (DeviceEx | None): associated device object
        _address (int): register address
        _fields (BitFields): bit field storage object
        _byte_len (int): register width in bytes (1 or 2 bytes)
        _value (int): current cached register value

    Methods:
        _get_width(): calculate required bytes from bit fields
        __len__(): return number of bit fields
        __getitem__(): get field value by field name
        __setitem__(): set field value by field name
        value(): get current cached register value
        byte_len(): get register width in bytes

    Notes:
        Only supports 1 or 2 byte wide registers, field step must be 1
    """

    def _get_width(self) -> int:
        """
        根据位域信息计算寄存器所需字节数
        Returns:
            int: 寄存器字节宽度（1或2）

        Notes:
            位域最大位位置决定字节数

        ==========================================
        Calculate required register bytes from bit field information
        Returns:
            int: register width in bytes (1 or 2)

        Notes:
            Byte count is determined by the highest bit position
        """
        mx = max(map(lambda val: val.position.stop, self._fields))
        return 1 + int((mx - 1) / 8)

    def __init__(self, device: DeviceEx | None, address: int, fields: BitFields, byte_len: int | None = None) -> None:
        """
        初始化寄存器对象
        Args:
            device (DeviceEx | None): 所属设备对象，可为None
            address (int): 寄存器地址
            fields (BitFields): 位域信息对象
            byte_len (int | None): 寄存器字节宽度，若为None则自动计算

        Raises:
            ValueError: 当byte_len不在1-2范围，或位域范围超出寄存器宽度，或步长不为1时

        Notes:
            验证每个位域的起始、结束位及步长

        ==========================================
        Initialize register object
        Args:
            device (DeviceEx | None): associated device object, can be None
            address (int): register address
            fields (BitFields): bit field information object
            byte_len (int | None): register width in bytes, auto-calculated if None

        Raises:
            ValueError: if byte_len not in 1-2, or bit field range exceeds register width, or step not 1

        Notes:
            Validates start, stop bits and step of each field
        """
        check_value(byte_len, range(1, 3), get_error_str("byte_len", byte_len, range(1, 3)))
        self._device = device
        self._address = address
        self._fields = fields
        # 寄存器字节宽度：1或2字节，更大需修改read方法
        self._byte_len = byte_len if byte_len else self._get_width()
        # 验证每个位域的范围和步长
        _k = 8 * self._byte_len
        for field in fields:
            check_value(field.position.start, range(_k), get_error_str("field.position.start", field.position.start, range(_k)))
            check_value(field.position.stop - 1, range(_k), get_error_str("field.position.stop", field.position.stop, range(_k)))
            check_value(field.position.step, range(1, 2), get_error_str("field.position.step", field.position.step, range(1, 2)))  # step must be 1
        # 缓存的寄存器值
        self._value = 0

    def __len__(self) -> int:
        """返回寄存器中位域的个数"""
        return len(self._fields)

    def __getitem__(self, key: str) -> int:
        """
        通过位域名获取当前缓存寄存器中该位域的值
        Args:
            key (str): 位域名称

        Returns:
            int: 位域值（可能为bool或int）

        Notes:
            内部会临时设置BitFields的源值为当前缓存值

        ==========================================
        Get bit field value from current cached register by field name
        Args:
            key (str): field name

        Returns:
            int: field value (bool or int)

        Notes:
            Temporarily sets BitFields source to current cached value internally
        """
        lnk = self._fields
        lnk.field_name = key
        lnk.source = self.value
        return lnk.get_field_value(validate=False)

    def __setitem__(self, key: str, value: int) -> int:
        """
        通过位域名设置当前缓存寄存器中该位域的值（不写入硬件）
        Args:
            key (str): 位域名称
            value (int): 要设置的值

        Returns:
            int: 修改后的完整寄存器值

        Notes:
            仅更新内部缓存，不触发硬件写操作

        ==========================================
        Set bit field value in current cached register by field name (does not write to hardware)
        Args:
            key (str): field name
            value (int): value to set

        Returns:
            int: modified full register value

        Notes:
            Only updates internal cache, does not trigger hardware write
        """
        lnk = self._fields
        lnk.field_name = key
        lnk.source = self.value
        _tmp = lnk.set_field_value(value=value)
        self._value = _tmp
        return _tmp

    @property
    def value(self) -> int:
        """获取当前缓存的寄存器值"""
        return self._value

    @property
    def byte_len(self) -> int:
        """获取寄存器字节宽度（1或2）"""
        return self._byte_len


class RegistryRO(BaseRegistry):
    """
    只读寄存器，支持从硬件读取值并缓存
    Methods:
        read(): 从设备读取寄存器值并更新缓存

    Notes:
        若设备对象为None，read方法不执行任何操作

    ==========================================
    Read-only register, supports reading from hardware and caching
    Methods:
        read(): read register value from device and update cache

    Notes:
        Does nothing if device object is None
    """

    def read(self) -> int | None:
        """
        从设备读取寄存器值并更新内部缓存
        Returns:
            int | None: 读取到的寄存器值，若设备不可用则返回None

        Notes:
            根据字节宽度自动选择解包格式（B或H）

        ==========================================
        Read register value from device and update internal cache
        Returns:
            int | None: read register value, or None if device not available

        Notes:
            Automatically selects unpack format (B or H) based on byte width
        """
        # 显式检查设备对象是否为None
        if not self._device:
            return None
        bl = self._byte_len
        by = self._device.read_reg(self._address, bl)
        fmt = "B" if 1 == bl else "H"
        self._value = self._device.unpack(fmt, by)[0]
        return self._value


class RegistryRW(RegistryRO):
    """
    读写寄存器，支持读取和写入硬件
    Methods:
        write(): 将当前缓存值（或指定值）写入硬件寄存器

    Notes:
        继承自RegistryRO，写入前需确保设备对象有效

    ==========================================
    Read-write register, supports reading from and writing to hardware
    Methods:
        write(): write current cached value (or given value) to hardware register

    Notes:
        Inherits from RegistryRO; device must be valid before write
    """

    def write(self, value: int | None = None) -> None:
        """
        将值写入硬件寄存器
        Args:
            value (int | None): 要写入的值，若为None则使用当前缓存值

        Returns:
            None

        Notes:
            若设备对象为None，则不做任何操作

        ==========================================
        Write value to hardware register
        Args:
            value (int | None): value to write, uses current cache if None

        Returns:
            None

        Notes:
            Does nothing if device object is None
        """
        if self._device:
            val = value if value is not None else self.value
            self._device.write_reg(self._address, val, self._byte_len)


# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================
