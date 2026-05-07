# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/07 00:00
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
import micropython
from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import BaseSensorEx, Iterator, get_error_str, check_value
from sensor_pack_2.bitfield import bit_field_info, BitFields
from sensor_pack_2.regmod import RegistryRO, RegistryRW

# ======================================== 全局变量 ============================================

# 传感器状态元组定义
sensor_status = namedtuple("sensor_status", "power_on int_status data_status")

# MAIN_CTRL 寄存器位域定义
_main_control_reg = (
    bit_field_info(name="soft_reset", position=range(4, 5), valid_values=None),
    bit_field_info(name="UVS_mode", position=range(3, 4), valid_values=None),
    bit_field_info(name="ALS_UVS_enable", position=range(1, 2), valid_values=None),
)

# ALS_UVS_MEAS_RATE 寄存器位域定义
_meas_rate_reg = (
    bit_field_info(name="resolution", position=range(4, 7), valid_values=range(6)),
    bit_field_info(name="meas_rate", position=range(3), valid_values=range(6)),
)

# ALS_UVS_GAIN 寄存器位域定义
_gain_reg = (bit_field_info(name="gain", position=range(3), valid_values=range(5)),)

# PART_ID 寄存器位域定义
_id_reg = (
    bit_field_info(name="part_id", position=range(4, 8), valid_values=None),
    bit_field_info(name="rev_id", position=range(4), valid_values=None),
)

# MAIN_STATUS 寄存器位域定义
_main_status_reg = (
    bit_field_info(name="power_on", position=range(5, 6), valid_values=None),
    bit_field_info(name="int_status", position=range(4, 5), valid_values=None),
    bit_field_info(name="data_status", position=range(3, 4), valid_values=None),
)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class LTR390UV(BaseSensorEx, Iterator):
    """
    LTR-390UV 光照和紫外线传感器驱动类，基于 sensor_pack_2 框架
    Attributes:
        _id_reg (RegistryRO): 只读 ID 寄存器对象
        _status_reg (RegistryRO): 只读状态寄存器对象
        _meas_rate_reg (RegistryRW): 读写测量速率寄存器对象
        _gain_reg (RegistryRW): 读写增益寄存器对象
        ctrl_reg (RegistryRW): 读写控制寄存器对象
        _buf_3 (bytearray): 3 字节数据缓冲区
        _uv_sens (int): UV 灵敏度值
        _uv_mode (bool): UV 模式标志
        _resolution (int): 分辨率值
        _meas_rate (int): 测量速率值
        _gain (int): 增益值
        _enabled (bool): 使能标志
    Methods:
        get_status(): 获取传感器状态
        get_conversion_cycle_time(): 获取转换周期时间
        get_id(): 获取器件 ID
        soft_reset(): 软件复位
        set_active(): 设置工作模式
        start_measurement(): 启动测量配置
        get_illumination(): 获取光照度值
        deinit(): 停用传感器，进入待机模式
    Notes:
        - 该传感器支持可见光和紫外线测量模式
        - 使用 sensor_pack_2 框架，多重继承为框架强制要求
    ==========================================
    LTR-390UV light and UV sensor driver class, based on sensor_pack_2 framework.
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
        deinit(): Disable sensor, enter standby mode
    Notes:
        - Supports both visible light and UV measurement modes
        - Uses sensor_pack_2 framework; multiple inheritance is framework-forced
    """

    # 默认 I2C 地址
    I2C_DEFAULT_ADDR = micropython.const(0x53)

    def __init__(self, adapter: bus_service.BusAdapter, address: int = I2C_DEFAULT_ADDR) -> None:
        """
        初始化 LTR-390UV 传感器
        Args:
            adapter (BusAdapter): sensor_pack_2 总线适配器实例
            address (int): I2C 设备地址，默认 0x53
        Returns:
            None
        Raises:
            ValueError: adapter 为 None 或类型错误
        Notes:
            - ISR-safe: 否
            - 副作用：初始化所有寄存器对象和数据缓冲区，不写入硬件
        ==========================================
        Initialize LTR-390UV sensor.
        Args:
            adapter (BusAdapter): sensor_pack_2 bus adapter instance
            address (int): I2C device address, default 0x53
        Returns:
            None
        Raises:
            ValueError: adapter is None or wrong type
        Notes:
            - ISR-safe: No
            - Side effect: Initializes register objects and data buffer, no hardware writes
        """
        if adapter is None:
            raise ValueError("adapter must not be None")
        if not hasattr(adapter, "read_reg"):
            raise ValueError("adapter must be a BusAdapter instance")
        super().__init__(adapter, address, False)
        self._id_reg = RegistryRO(device=self, address=0x06, fields=BitFields(_id_reg), byte_len=None)
        self._status_reg = RegistryRO(device=self, address=0x07, fields=BitFields(_main_status_reg), byte_len=None)
        self._meas_rate_reg = RegistryRW(device=self, address=0x04, fields=BitFields(_meas_rate_reg), byte_len=None)
        self._gain_reg = RegistryRW(device=self, address=0x05, fields=BitFields(_gain_reg), byte_len=None)
        self.ctrl_reg = RegistryRW(device=self, address=0x00, fields=BitFields(_main_control_reg), byte_len=None)
        # 3 字节数据缓冲区，复用避免频繁分配
        self._buf_3 = bytearray(3)
        # UV 灵敏度默认值 2300
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
            sensor_status: 包含 power_on、int_status、data_status 的命名元组
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 读取 MAIN_STATUS 寄存器并解析状态位
        ==========================================
        Get sensor status.
        Args:
            None
        Returns:
            sensor_status: Named tuple with power_on, int_status, data_status
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Reads MAIN_STATUS register and parses status bits
        """
        _reg = self._status_reg
        try:
            _reg.read()
        except OSError as e:
            raise RuntimeError("I2C read status register failed") from e
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
            - ISR-safe: 否
            - 须先调用 start_measurement() 设置 meas_rate 后调用
        ==========================================
        Get conversion cycle time.
        Args:
            None
        Returns:
            int: Conversion cycle time in milliseconds
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Must call start_measurement() first to set meas_rate
        """
        return LTR390UV._meas_rate_to_ms(self.meas_rate)

    def get_id(self) -> tuple:
        """
        获取器件 ID 和修订版本
        Args:
            无
        Returns:
            tuple: (part_id, rev_id) 部件 ID 和修订 ID
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 读取 PART_ID 寄存器
        ==========================================
        Get device ID and revision.
        Args:
            None
        Returns:
            tuple: (part_id, rev_id) Part ID and revision ID
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Reads PART_ID register
        """
        _reg = self._id_reg
        try:
            _reg.read()
        except OSError as e:
            raise RuntimeError("I2C read ID register failed") from e
        return _reg["part_id"], _reg["rev_id"]

    def soft_reset(self) -> None:
        """
        软件复位传感器
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败或复位超时
        Notes:
            - ISR-safe: 否
            - 副作用：设置 soft_reset 位，等待复位完成（最多重试 3 次）
        ==========================================
        Software reset sensor.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed or reset timed out
        Notes:
            - ISR-safe: No
            - Side effect: Sets soft_reset bit and waits for reset completion (up to 3 retries)
        """
        _reg = self.ctrl_reg
        _reg["soft_reset"] = 1
        try:
            _reg.write()
        except OSError as e:
            raise RuntimeError("I2C write soft_reset failed") from e
        # 等待复位完成，errno 110（ETIMEDOUT）为设备未就绪，继续等待
        for _ in range(3):
            time.sleep_ms(10)
            try:
                _reg.read()
                if not _reg["soft_reset"]:
                    break
            except OSError as ex:
                if 110 == ex.errno:
                    pass
                else:
                    raise RuntimeError("I2C error during soft reset") from ex
        else:
            raise RuntimeError("Soft reset did not complete within timeout")

    def set_active(self, value: bool = True) -> None:
        """
        设置传感器工作模式
        Args:
            value (bool): True 为工作模式，False 为待机模式
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：修改 ALS_UVS_enable 位，更新 _enabled 缓存
        ==========================================
        Set sensor active mode.
        Args:
            value (bool): True for active mode, False for standby mode
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Modifies ALS_UVS_enable bit, updates _enabled cache
        """
        _reg = self.ctrl_reg
        try:
            _reg.read()
            _reg["ALS_UVS_enable"] = value
            _reg.write()
            # 读取确认状态
            _reg.read()
        except OSError as e:
            raise RuntimeError("I2C read/write ctrl_reg failed") from e
        self._enabled = _reg["ALS_UVS_enable"]

    def start_measurement(self, uv_mode: bool, meas_rate: int = 1, gain: int = 3, enable: bool = True) -> None:
        """
        启动测量配置
        Args:
            uv_mode (bool): True 为 UV 模式，False 为可见光模式
            meas_rate (int): 测量速率（0~5），默认 1
            gain (int): 增益值（0~4），默认 3
            enable (bool): 使能测量，默认 True
        Returns:
            None
        Raises:
            ValueError: uv_mode/meas_rate/gain/enable 参数为 None 或超出范围
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：配置所有测量参数并启动传感器，更新内部缓存
        ==========================================
        Start measurement configuration.
        Args:
            uv_mode (bool): True for UV mode, False for visible light mode
            meas_rate (int): Measurement rate (0~5), default 1
            gain (int): Gain value (0~4), default 3
            enable (bool): Enable measurement, default True
        Returns:
            None
        Raises:
            ValueError: uv_mode/meas_rate/gain/enable is None or out of range
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Configures all measurement params, starts sensor, updates cache
        """
        if uv_mode is None:
            raise ValueError("uv_mode cannot be None")
        if meas_rate is None:
            raise ValueError("meas_rate cannot be None")
        if gain is None:
            raise ValueError("gain cannot be None")
        if enable is None:
            raise ValueError("enable cannot be None")
        try:
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
        except OSError as e:
            raise RuntimeError("I2C error during start_measurement") from e

    def get_illumination(self, raw: bool = True, w_fac: float = 1.0) -> object:
        """
        获取光照度值
        Args:
            raw (bool): True 返回原始值，False 返回换算值
            w_fac (float): 权重因子，默认 1.0
        Returns:
            int: raw=True 或 UV 模式时返回原始整数值
            float: raw=False 且 ALS 模式时返回换算照度值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - UV 模式下只能返回原始值
        ==========================================
        Get illumination value.
        Args:
            raw (bool): True for raw value, False for converted value
            w_fac (float): Weight factor, default 1.0
        Returns:
            int: Raw integer value when raw=True or in UV mode
            float: Converted lux value when raw=False and in ALS mode
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Only raw value is returned in UV mode
        """
        addr = 0x10 if self.uv_mode else 0x0D
        buf = self._buf_3
        try:
            self.read_buf_from_mem(addr, buf, 1)
        except OSError as e:
            raise RuntimeError("I2C read illumination data failed") from e
        val = buf[0] + 256 * buf[1] + 65536 * buf[2]
        # UV 模式只返回原始值
        if raw or self.uv_mode:
            return val
        _gain = 1, 3, 6, 9, 18
        x = 0.25 * 2**self.resolution
        _tmp = _gain[self.gain] * x
        return 0.6 * w_fac * val / _tmp

    def __iter__(self):
        """
        返回迭代器自身（Iterator 协议）
        Returns:
            self
        Notes:
            - ISR-safe: 是
        ==========================================
        Return iterator self (Iterator protocol).
        Returns:
            self
        Notes:
            - ISR-safe: Yes
        """
        return self

    def __next__(self) -> object:
        """
        迭代器协议实现：返回换算后的光照度值
        Args:
            无
        Returns:
            float 或 int 或 None: 光照度值；uv_mode 未设置时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Iterator protocol: return converted illumination value.
        Args:
            None
        Returns:
            float or int or None: Illumination value; None if uv_mode not set
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        if self.uv_mode is None:
            return None
        return self.get_illumination(raw=False)

    @property
    def gain(self) -> int:
        """增益值（start_measurement 前为 None）"""
        return self._gain

    @property
    def meas_rate(self) -> int:
        """测量速率值（start_measurement 前为 None）"""
        return self._meas_rate

    @property
    def resolution(self) -> int:
        """分辨率值（start_measurement 前为 None）"""
        return self._resolution

    @property
    def uv_mode(self) -> bool:
        """UV 模式标志（start_measurement 前为 None）"""
        return self._uv_mode

    @property
    def in_standby(self) -> bool:
        """是否处于待机模式"""
        return not self._enabled

    @property
    def uv_sensitivity(self) -> int:
        """UV 灵敏度值，默认 2300"""
        return self._uv_sens

    @uv_sensitivity.setter
    def uv_sensitivity(self, value: int) -> None:
        """
        设置 UV 灵敏度
        Args:
            value (int): UV 灵敏度值（1~9999）
        Raises:
            ValueError: value 超出范围
        Notes:
            - ISR-safe: 是
        ==========================================
        Set UV sensitivity.
        Args:
            value (int): UV sensitivity value (1~9999)
        Raises:
            ValueError: value out of range
        Notes:
            - ISR-safe: Yes
        """
        rng = range(1, 10_000)
        check_value(value, rng, get_error_str("UV sensitivity", value, rng))
        self._uv_sens = value

    @staticmethod
    def _meas_rate_to_resolution(meas_rate: int) -> int:
        """将测量速率（0~5）转换为对应分辨率索引（0~4，13 位未使用）"""
        vr = range(6)
        check_value(meas_rate, vr, get_error_str("meas_rate", meas_rate, vr))
        _resol = 4, 3, 2, 1, 0, 0
        return _resol[meas_rate]

    @staticmethod
    def _meas_rate_to_ms(meas_rate: int) -> int:
        """将测量速率（0~5）转换为对应转换时间（ms）"""
        vr = range(6)
        check_value(meas_rate, vr, get_error_str("meas_rate", meas_rate, vr))
        _conv_time = 25, 50, 100, 200, 500, 1000
        return _conv_time[meas_rate]

    def deinit(self) -> None:
        """
        停用传感器，进入待机模式
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：关闭 ALS_UVS_enable，传感器进入待机低功耗状态
        ==========================================
        Disable sensor, enter standby mode.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Clears ALS_UVS_enable, sensor enters standby low-power state
        """
        self.set_active(False)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
