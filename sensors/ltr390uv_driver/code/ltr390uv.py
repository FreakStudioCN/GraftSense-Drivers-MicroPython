# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : octaprog7
# @File    : ltr390uv.py
# @Description : LTR-390UV-01光照和紫外线传感器驱动模块
# @License : MIT
__version__ = "0.1.0"
__author__ = "octaprog7"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================
import time
from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import BaseSensorEx, Iterator, get_error_str, check_value
from sensor_pack_2.bitfield import bit_field_info
from sensor_pack_2.bitfield import BitFields
from sensor_pack_2.regmod import RegistryRO, RegistryRW


# ======================================== 全局变量 ============================================
# 传感器状态元组定义
sensor_status = namedtuple("sensor_status", "power_on int_status data_status")

# MAIN_CTRL寄存器位域定义
_main_control_reg = (
    bit_field_info(name="soft_reset", position=range(4, 5), valid_values=None),
    bit_field_info(name="UVS_mode", position=range(3, 4), valid_values=None),
    bit_field_info(name="ALS_UVS_enable", position=range(1, 2), valid_values=None),
)

# ALS_UVS_MEAS_RATE寄存器位域定义
_meas_rate_reg = (
    bit_field_info(name="resolution", position=range(4, 7), valid_values=range(6)),
    bit_field_info(name="meas_rate", position=range(3), valid_values=range(6)),
)

# ALS_UVS_GAIN寄存器位域定义
_gain_reg = (bit_field_info(name="gain", position=range(3), valid_values=range(5)),)

# PART_ID寄存器位域定义
_id_reg = (
    bit_field_info(name="part_id", position=range(4, 8), valid_values=None),
    bit_field_info(name="rev_id", position=range(4), valid_values=None),
)

# MAIN_STATUS寄存器位域定义
_main_status_reg = (
    bit_field_info(name="power_on", position=range(5, 6), valid_values=None),
    bit_field_info(name="int_status", position=range(4, 5), valid_values=None),
    bit_field_info(name="data_status", position=range(3, 4), valid_values=None),
)


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class LTR390UV(BaseSensorEx, Iterator):
    """
    LTR-390UV光照和紫外线传感器驱动类
    Attributes:
        _id_reg (RegistryRO): 只读ID寄存器对象
        _status_reg (RegistryRO): 只读状态寄存器对象
        _meas_rate_reg (RegistryRW): 读写测量速率寄存器对象
        _gain_reg (RegistryRW): 读写增益寄存器对象
        ctrl_reg (RegistryRW): 读写控制寄存器对象
        _buf_3 (bytearray): 3字节数据缓冲区
        _uv_sens (int): UV灵敏度值
        _uv_mode (bool): UV模式标志
        _resolution (int): 分辨率值
        _meas_rate (int): 测量速率值
        _gain (int): 增益值
        _enabled (bool): 使能标志

    Methods:
        get_status(): 获取传感器状态
        get_conversion_cycle_time(): 获取转换周期时间
        get_id(): 获取器件ID
        soft_reset(): 软件复位
        set_active(): 设置工作模式
        start_measurement(): 启动测量配置
        get_illumination(): 获取光照度值
        __next__(): 迭代器协议实现

    Notes:
        该传感器支持可见光和紫外线测量模式

    ==========================================
    LTR-390UV light and UV sensor driver class
    Attributes:
        _id_reg (RegistryRO): Read-only ID register object
        _status_reg (RegistryRO): Read-only status register object
        _meas_rate_reg (RegistryRW): Read-write measurement rate register object
        _gain_reg (RegistryRW): Read-write gain register object
        ctrl_reg (RegistryRW): Read-write control register object
        _buf_3 (bytearray): 3-byte data buffer
        _uv_sens (int): UV sensitivity value
        _uv_mode (bool): UV mode flag
        _resolution (int): Resolution value
        _meas_rate (int): Measurement rate value
        _gain (int): Gain value
        _enabled (bool): Enable flag

    Methods:
        get_status(): Get sensor status
        get_conversion_cycle_time(): Get conversion cycle time
        get_id(): Get device ID
        soft_reset(): Software reset
        set_active(): Set active mode
        start_measurement(): Start measurement configuration
        get_illumination(): Get illumination value
        __next__(): Iterator protocol implementation

    Notes:
        This sensor supports both visible light and UV measurement modes
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x53):
        """
        初始化LTR-390UV传感器
        Args:
            adapter (bus_service.BusAdapter): 总线适配器对象
            address (int): I2C设备地址，默认0x53

        Raises:
            无

        Notes:
            初始化所有寄存器对象和数据缓冲区

        ==========================================
        Initialize LTR-390UV sensor
        Args:
            adapter (bus_service.BusAdapter): Bus adapter object
            address (int): I2C device address, default 0x53

        Raises:
            None

        Notes:
            Initialize all register objects and data buffer
        """
        super().__init__(adapter, address, False)
        self._id_reg = RegistryRO(device=self, address=0x06, fields=BitFields(_id_reg), byte_len=None)
        self._status_reg = RegistryRO(device=self, address=0x07, fields=BitFields(_main_status_reg), byte_len=None)
        self._meas_rate_reg = RegistryRW(device=self, address=0x04, fields=BitFields(_meas_rate_reg), byte_len=None)
        self._gain_reg = RegistryRW(device=self, address=0x05, fields=BitFields(_gain_reg), byte_len=None)
        self.ctrl_reg = RegistryRW(device=self, address=0x00, fields=BitFields(_main_control_reg), byte_len=None)
        # 3字节数据缓冲区
        self._buf_3 = bytearray((0 for _ in range(3)))
        # UV灵敏度默认值2300
        self._uv_sens = 2300
        # 状态变量初始化
        self._uv_mode = None
        self._resolution = None
        self._meas_rate = None
        self._gain = None
        self._enabled = None

    def get_status(self) -> sensor_status:
        """
        获取传感器状态
        Args:
            无

        Returns:
            sensor_status: 包含power_on、int_status、data_status的命名元组

        Notes:
            读取MAIN_STATUS寄存器并解析状态位

        ==========================================
        Get sensor status
        Args:
            None

        Returns:
            sensor_status: Named tuple containing power_on, int_status, data_status

        Notes:
            Read MAIN_STATUS register and parse status bits
        """
        _reg = self._status_reg
        _reg.read()
        return sensor_status(power_on=_reg["power_on"], int_status=_reg["int_status"], data_status=_reg["data_status"])

    def get_conversion_cycle_time(self) -> int:
        """
        获取转换周期时间
        Args:
            无

        Returns:
            int: 转换周期时间（毫秒）

        Raises:
            无

        Notes:
            必须先调用start_measurement方法设置meas_rate

        ==========================================
        Get conversion cycle time
        Args:
            None

        Returns:
            int: Conversion cycle time in milliseconds

        Raises:
            None

        Notes:
            Must call start_measurement first to set meas_rate
        """
        return LTR390UV._meas_rate_to_ms(self.meas_rate)

    @staticmethod
    def _meas_rate_to_resolution(meas_rate: int) -> int:
        """
        将测量速率转换为分辨率
        Args:
            meas_rate (int): 测量速率值(0-5)

        Returns:
            int: 对应的分辨率值(0-4)

        Raises:
            ValueError: 当meas_rate不在有效范围内时

        Notes:
            13位分辨率未被使用

        ==========================================
        Convert measurement rate to resolution
        Args:
            meas_rate (int): Measurement rate value (0-5)

        Returns:
            int: Corresponding resolution value (0-4)

        Raises:
            ValueError: When meas_rate is not in valid range

        Notes:
            13-bit resolution is not used
        """
        vr = range(6)
        check_value(meas_rate, vr, get_error_str("meas_rate", meas_rate, vr))
        _resol = 4, 3, 2, 1, 0, 0
        return _resol[meas_rate]

    @staticmethod
    def _meas_rate_to_ms(meas_rate: int) -> int:
        """
        将测量速率转换为毫秒时间
        Args:
            meas_rate (int): 测量速率值(0-5)

        Returns:
            int: 对应的转换时间（毫秒）

        Raises:
            ValueError: 当meas_rate不在有效范围内时

        Notes:
            无

        ==========================================
        Convert measurement rate to milliseconds
        Args:
            meas_rate (int): Measurement rate value (0-5)

        Returns:
            int: Corresponding conversion time in milliseconds

        Raises:
            ValueError: When meas_rate is not in valid range

        Notes:
            None
        """
        vr = range(6)
        check_value(meas_rate, vr, get_error_str("meas_rate", meas_rate, vr))
        _conv_time = 25, 50, 100, 200, 500, 1000
        return _conv_time[meas_rate]

    def get_id(self) -> tuple:
        """
        获取器件ID和修订版本
        Args:
            无

        Returns:
            tuple: (part_id, rev_id) 部件ID和修订ID

        Notes:
            读取PART_ID寄存器

        ==========================================
        Get device ID and revision
        Args:
            None

        Returns:
            tuple: (part_id, rev_id) Part ID and revision ID

        Notes:
            Read PART_ID register
        """
        _reg = self._id_reg
        _reg.read()
        return _reg["part_id"], _reg["rev_id"]

    def soft_reset(self):
        """
        软件复位传感器
        Args:
            无

        Raises:
            ValueError: 当软件复位失败时

        Notes:
            设置soft_reset位并等待复位完成

        ==========================================
        Software reset sensor
        Args:
            None

        Raises:
            ValueError: When software reset fails

        Notes:
            Set soft_reset bit and wait for reset completion
        """
        _reg = self.ctrl_reg
        _reg["soft_reset"] = 1
        _reg.write()
        # 等待复位完成
        for i in range(3):
            time.sleep_ms(10)
            try:
                _reg.read()
                if not _reg["soft_reset"]:
                    break
            except OSError as ex:
                if 110 == ex.errno:
                    pass
                else:
                    raise ex
        else:
            raise ValueError("soft_reset error!")

    @property
    def gain(self) -> [int, None]:
        """获取增益值"""
        return self._gain

    @property
    def meas_rate(self) -> [int, None]:
        """获取测量速率值"""
        return self._meas_rate

    @property
    def resolution(self) -> [int, None]:
        """获取分辨率值"""
        return self._resolution

    @property
    def uv_mode(self) -> [bool, None]:
        """获取UV模式状态"""
        return self._uv_mode

    @property
    def in_standby(self) -> bool:
        """检查是否处于待机模式"""
        return not self._enabled

    @property
    def uv_sensitivity(self) -> int:
        """获取UV灵敏度值"""
        return self._uv_sens

    @uv_sensitivity.setter
    def uv_sensitivity(self, value: int):
        """
        设置UV灵敏度
        Args:
            value (int): UV灵敏度值(1-9999)

        Raises:
            ValueError: 当value不在有效范围内时

        Notes:
            无

        ==========================================
        Set UV sensitivity
        Args:
            value (int): UV sensitivity value (1-9999)

        Raises:
            ValueError: When value is not in valid range

        Notes:
            None
        """
        rng = range(1, 10_000)
        check_value(value, rng, get_error_str("UV sensitivity", value, rng))
        self._uv_sens = value

    def set_active(self, value: bool = True):
        """
        设置传感器工作模式
        Args:
            value (bool): True为工作模式，False为待机模式

        Notes:
            无

        ==========================================
        Set sensor active mode
        Args:
            value (bool): True for active mode, False for standby mode

        Notes:
            None
        """
        _reg = self.ctrl_reg
        _reg.read()
        _reg["ALS_UVS_enable"] = value
        _reg.write()
        # 读取确认状态
        _reg.read()
        self._enabled = _reg["ALS_UVS_enable"]

    def start_measurement(self, uv_mode: bool, meas_rate: int = 1, gain: int = 3, enable: bool = True):
        """
        启动测量配置
        Args:
            uv_mode (bool): True为UV模式，False为可见光模式
            meas_rate (int): 测量速率(0-5)，默认1
            gain (int): 增益值(0-4)，默认3
            enable (bool): 使能测量，默认True

        Notes:
            配置所有测量参数并启动传感器

        ==========================================
        Start measurement configuration
        Args:
            uv_mode (bool): True for UV mode, False for visible light mode
            meas_rate (int): Measurement rate (0-5), default 1
            gain (int): Gain value (0-4), default 3
            enable (bool): Enable measurement, default True

        Notes:
            Configure all measurement parameters and start sensor
        """
        if uv_mode is None:
            raise ValueError("uv_mode cannot be None")
        if meas_rate is None:
            raise ValueError("meas_rate cannot be None")
        if gain is None:
            raise ValueError("gain cannot be None")
        if enable is None:
            raise ValueError("enable cannot be None")

        _reg = self._meas_rate_reg
        _reg.read()
        _reg["meas_rate"] = meas_rate
        _reg["resolution"] = LTR390UV._meas_rate_to_resolution(meas_rate)
        _reg.write()

        _reg = self._gain_reg
        _reg.read()
        _reg["gain"] = gain
        _reg.write()

        _reg = self.ctrl_reg
        _reg.read()
        _reg["ALS_UVS_enable"] = enable
        _reg["UVS_mode"] = uv_mode
        _reg.write()

        # 读取并保存配置
        _reg = self._meas_rate_reg
        _reg.read()
        self._meas_rate = _reg["meas_rate"]
        self._resolution = _reg["resolution"]

        _reg = self._gain_reg
        _reg.read()
        self._gain = _reg["gain"]

        _reg = self.ctrl_reg
        _reg.read()
        self._uv_mode = _reg["UVS_mode"]
        self._enabled = _reg["ALS_UVS_enable"]

    def get_illumination(self, raw: bool = True, w_fac: float = 1.0) -> [int, float]:
        """
        获取光照度值
        Args:
            raw (bool): True返回原始值，False返回换算值
            w_fac (float): 权重因子，默认1.0

        Returns:
            int or float: 光照度值

        Notes:
            UV模式下只能返回原始值

        ==========================================
        Get illumination value
        Args:
            raw (bool): True for raw value, False for converted value
            w_fac (float): Weight factor, default 1.0

        Returns:
            int or float: Illumination value

        Notes:
            Only raw value can be returned in UV mode
        """
        addr = 0x10 if self.uv_mode else 0x0D
        buf = self._buf_3
        self.read_buf_from_mem(addr, buf, 1)
        val = buf[0] + 256 * buf[1] + 65536 * buf[2]
        # UV模式只返回原始值
        if raw or self.uv_mode:
            return val
        _gain = 1, 3, 6, 9, 18
        x = 0.25 * 2**self.resolution
        _tmp = _gain[self.gain] * x
        return 0.6 * w_fac * val / _tmp

    def __next__(self) -> [float, int, None]:
        """
        迭代器协议实现
        Args:
            无

        Returns:
            float or int or None: 光照度值或None

        Notes:
            无

        ==========================================
        Iterator protocol implementation
        Args:
            None

        Returns:
            float or int or None: Illumination value or None

        Notes:
            None
        """
        if self.uv_mode is None:
            return None
        return self.get_illumination(raw=False)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
