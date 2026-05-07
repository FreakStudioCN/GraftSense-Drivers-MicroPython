# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/07 00:00
# @Author  : goctaprog
# @File    : opt3001mod.py
# @Description : OPT3001 环境光传感器（ALS）驱动，基于 sensor_pack_2 框架
# @License : MIT

__version__ = "1.0.0"
__author__ = "goctaprog"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython
from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, IBaseSensorEx, Iterator, check_value
from sensor_pack_2.bitfield import bit_field_info, BitFields

# ======================================== 全局变量 ============================================

_REG_RESULT = micropython.const(0x00)
_REG_CONFIG = micropython.const(0x01)
_REG_MAN_ID = micropython.const(0x7E)
_REG_DEV_ID = micropython.const(0x7F)

_ADDR_MIN = micropython.const(0x44)
_ADDR_MAX = micropython.const(0x48)

opt3001_id = namedtuple("opt3001_id", "manufacturer_id device_id")
opt3001_config = namedtuple("config_opt3001", "RN CT M OVF CRF FH FL L POL ME FC")
opt3001_meas_data = namedtuple("opt3001_meas_data", "lux full_scale_range")
opt3001_meas_raw = namedtuple("opt3001_meas_raw", "exponent fractional")
_opt3001_lsb_fsr = namedtuple("_opt3001_lsb_fsr", "LSB FSR")
OPT3001_data_status = namedtuple("OPT3001_data_status", "conversion_ready overflow")

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class OPT3001(DeviceEx, IBaseSensorEx, Iterator):
    """
    OPT3001 环境光传感器（ALS）驱动类，基于 sensor_pack_2 框架
    Attributes:
        _bit_fields (BitFields): 配置寄存器位域操作对象
    Methods:
        get_id(): 读取制造商 ID 和设备 ID
        start_measurement(): 配置并启动测量
        get_measurement_value(): 读取测量结果
        get_data_status(): 读取数据就绪状态
        get_conversion_cycle_time(): 获取当前转换周期时长
        get_cfg_reg(): 读取原始配置寄存器
        set_cfg_reg(): 写入原始配置寄存器
        get_config_hr(): 以命名元组形式返回当前配置
        read_config_from_sensor(): 从传感器刷新配置缓存
        write_config_to_sensor(): 将缓存配置写入传感器
        is_single_shot_mode(): 判断是否为单次测量模式
        is_continuously_mode(): 判断是否为连续测量模式
        deinit(): 释放资源，停止测量
    Notes:
        - 依赖外部传入 BusAdapter 实例，不在内部创建总线
        - 继承自 sensor_pack_2 框架，多重继承为框架强制要求
    ==========================================
    OPT3001 Ambient Light Sensor (ALS) driver, based on sensor_pack_2 framework.
    Attributes:
        _bit_fields (BitFields): Bit-field handler for config register
    Methods:
        get_id(): Read manufacturer ID and device ID
        start_measurement(): Configure and start measurement
        get_measurement_value(): Read measurement result
        get_data_status(): Read data ready status
        get_conversion_cycle_time(): Get current conversion cycle time
        get_cfg_reg(): Read raw config register
        set_cfg_reg(): Write raw config register
        get_config_hr(): Return current config as namedtuple
        read_config_from_sensor(): Refresh config cache from sensor
        write_config_to_sensor(): Write cached config to sensor
        is_single_shot_mode(): Check if in single-shot mode
        is_continuously_mode(): Check if in continuous mode
        deinit(): Release resources, stop measurement
    Notes:
        - Requires externally provided BusAdapter instance
        - Multiple inheritance is required by sensor_pack_2 framework
    """

    # 默认 I2C 地址
    I2C_DEFAULT_ADDR = micropython.const(0x44)

    _CONFIG_FIELDS = (
        bit_field_info(name="RN", position=range(12, 16), valid_values=range(13), description="Range number field."),
        bit_field_info(name="CT", position=range(11, 12), valid_values=None, description="Conversion time field."),
        bit_field_info(name="M", position=range(9, 11), valid_values=range(4), description="Mode of conversion operation field."),
        bit_field_info(name="OVF", position=range(8, 9), valid_values=None, description="Overflow flag."),
        bit_field_info(name="CRF", position=range(7, 8), valid_values=None, description="Conversion ready."),
        bit_field_info(name="FH", position=range(6, 7), valid_values=None, description="Flag high."),
        bit_field_info(name="FL", position=range(5, 6), valid_values=None, description="Flag low."),
        bit_field_info(name="L", position=range(4, 5), valid_values=None, description="Latch field."),
        bit_field_info(name="POL", position=range(3, 4), valid_values=None, description="Polarity."),
        bit_field_info(name="ME", position=range(2, 3), valid_values=None, description="Mask exponent."),
        bit_field_info(name="FC", position=range(2), valid_values=None, description="Fault count."),
    )

    def __init__(self, adapter: bus_service.BusAdapter, address: int = I2C_DEFAULT_ADDR) -> None:
        """
        初始化 OPT3001 传感器驱动
        Args:
            adapter (BusAdapter): sensor_pack_2 总线适配器实例
            address (int): I2C 设备地址，范围 0x44~0x47，默认 0x44
        Returns:
            None
        Raises:
            ValueError: adapter 为 None 或类型错误、address 超出范围
        Notes:
            - ISR-safe: 否
            - 副作用：初始化位域缓存，不写入硬件寄存器
        ==========================================
        Initialize OPT3001 sensor driver.
        Args:
            adapter (BusAdapter): sensor_pack_2 bus adapter instance
            address (int): I2C device address, range 0x44~0x47, default 0x44
        Returns:
            None
        Raises:
            ValueError: adapter is None or wrong type, address out of range
        Notes:
            - ISR-safe: No
            - Side effect: Initializes bit-field cache, does not write hardware registers
        """
        if adapter is None:
            raise ValueError("adapter must not be None")
        if not hasattr(adapter, "read_reg"):
            raise ValueError("adapter must be a BusAdapter instance")
        check_value(address, range(_ADDR_MIN, _ADDR_MAX), "Invalid I2C address: 0x%02X" % address)
        DeviceEx.__init__(self, adapter, address, True)
        self._bit_fields = BitFields(fields_info=OPT3001._CONFIG_FIELDS)

    def get_cfg_reg(self) -> int:
        """
        从传感器读取原始配置寄存器值
        Args:
            无
        Returns:
            int: 16 位原始配置寄存器值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw configuration register from sensor.
        Args:
            None
        Returns:
            int: 16-bit raw config register value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            return self.read_reg_16(_REG_CONFIG)
        except OSError as e:
            raise RuntimeError("I2C read config reg failed") from e

    def set_cfg_reg(self, value: int) -> int:
        """
        向传感器写入原始配置寄存器值
        Args:
            value (int): 16 位配置寄存器值
        Returns:
            int: 写入的值
        Raises:
            ValueError: value 类型错误
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：修改传感器硬件配置寄存器
        ==========================================
        Write raw configuration register to sensor.
        Args:
            value (int): 16-bit config register value
        Returns:
            int: Written value
        Raises:
            ValueError: value is not int
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Modifies sensor hardware config register
        """
        if not isinstance(value, int):
            raise ValueError("value must be int, got %s" % type(value))
        try:
            return self.write_reg_16(_REG_CONFIG, value)
        except OSError as e:
            raise RuntimeError("I2C write config reg failed") from e

    def get_config_hr(self) -> opt3001_config:
        """
        以命名元组形式返回当前缓存的配置字段
        Args:
            无
        Returns:
            opt3001_config: 包含所有配置字段的命名元组
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 返回缓存值，非实时硬件值；如需实时值请先调用 read_config_from_sensor()
        ==========================================
        Return current cached config fields as namedtuple.
        Args:
            None
        Returns:
            opt3001_config: Namedtuple with all config fields
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Returns cached value; call read_config_from_sensor() first for live value
        """
        return opt3001_config(
            RN=self.lux_range_index,
            CT=self.long_conversion_time,
            M=self.mode,
            OVF=self.overflow,
            CRF=self.conversion_ready,
            FH=self.flag_high,
            FL=self.flag_low,
            L=self.latch,
            POL=self.polarity,
            ME=self.mask_exponent,
            FC=self.fault_count,
        )

    def read_config_from_sensor(self, return_value: bool = False) -> opt3001_config:
        """
        从传感器读取配置并刷新内部缓存
        Args:
            return_value (bool): 为 True 时返回配置命名元组，默认 False
        Returns:
            opt3001_config 或 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：更新内部位域缓存
        ==========================================
        Read config from sensor and refresh internal cache.
        Args:
            return_value (bool): If True, return config namedtuple; default False
        Returns:
            opt3001_config or None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Updates internal bit-field cache
        """
        raw = self.get_cfg_reg()
        self._set_config_field(value=raw, field_name=None)
        if return_value:
            return self.get_config_hr()

    def write_config_to_sensor(self) -> int:
        """
        将内部缓存的配置写入传感器寄存器
        Args:
            无
        Returns:
            int: 写入的原始配置值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：修改传感器硬件配置寄存器
        ==========================================
        Write cached config to sensor register.
        Args:
            None
        Returns:
            int: Raw config value written
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Modifies sensor hardware config register
        """
        _cfg = self._get_config_field(field_name=None)
        self.set_cfg_reg(_cfg)
        return _cfg

    def get_id(self) -> opt3001_id:
        """
        读取制造商 ID 和设备 ID
        Args:
            无
        Returns:
            opt3001_id: 包含 manufacturer_id 和 device_id 的命名元组
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read manufacturer ID and device ID.
        Args:
            None
        Returns:
            opt3001_id: Namedtuple with manufacturer_id and device_id
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            man_id = self.read_reg_16(_REG_MAN_ID)
            dev_id = self.read_reg_16(_REG_DEV_ID)
        except OSError as e:
            raise RuntimeError("I2C read ID failed") from e
        return opt3001_id(manufacturer_id=man_id, device_id=dev_id)

    def get_conversion_cycle_time(self) -> int:
        """
        获取当前配置下的转换周期时长（毫秒）
        Args:
            无
        Returns:
            int: 100 或 800（毫秒）
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 配置变更后需重新调用
        ==========================================
        Get conversion cycle time in ms for current config.
        Args:
            None
        Returns:
            int: 100 or 800 (ms)
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Call again after config changes
        """
        if self.long_conversion_time:
            return 800
        return 100

    def start_measurement(self, continuously: bool = True, lx_range_index: int = 12, refresh: bool = False) -> None:
        """
        配置测量参数并启动测量
        Args:
            continuously (bool): True 为连续模式（mode=3），False 为单次（mode=1）
            lx_range_index (int): 量程索引 0~12，12 为自动量程
            refresh (bool): True 时启动后从传感器刷新配置缓存
        Returns:
            None
        Raises:
            ValueError: 参数类型或范围错误
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：修改传感器工作模式和量程配置寄存器
        ==========================================
        Configure and start measurement.
        Args:
            continuously (bool): True for continuous (mode=3), False for single-shot (mode=1)
            lx_range_index (int): Range index 0~12, 12=auto full-scale
            refresh (bool): If True, refresh config cache from sensor after start
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type or range
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Modifies sensor mode and range config register
        """
        if not isinstance(continuously, bool):
            raise ValueError("continuously must be bool")
        if not isinstance(lx_range_index, int) or lx_range_index < 0 or lx_range_index > 12:
            raise ValueError("lx_range_index must be 0~12, got %s" % lx_range_index)
        self.mode = 3 if continuously else 1
        self.lux_range_index = lx_range_index
        self.write_config_to_sensor()
        if refresh:
            self.read_config_from_sensor(return_value=False)

    def get_measurement_value(self, value_index: int = 0) -> tuple:
        """
        读取测量结果
        Args:
            value_index (int): 0 返回原始数据 opt3001_meas_raw，1 返回处理后照度 opt3001_meas_data
        Returns:
            tuple: opt3001_meas_raw 或 opt3001_meas_data
        Raises:
            ValueError: value_index 不为 0 或 1
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read measurement result.
        Args:
            value_index (int): 0=raw opt3001_meas_raw, 1=processed opt3001_meas_data
        Returns:
            tuple: opt3001_meas_raw or opt3001_meas_data
        Raises:
            ValueError: value_index not 0 or 1
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        if value_index not in (0, 1):
            raise ValueError("value_index must be 0 or 1, got %s" % value_index)
        try:
            raw = self.read_reg_16(_REG_RESULT, signed=False)
        except OSError as e:
            raise RuntimeError("I2C read result reg failed") from e
        _exponent = (raw & 0xF000) >> 12
        _fractional = raw & 0x0FFF
        if value_index == 0:
            return opt3001_meas_raw(exponent=_exponent, fractional=_fractional)
        _data = OPT3001._get_lsb_fsr(_exponent)
        _lux = _data.LSB * _fractional
        return opt3001_meas_data(lux=_lux, full_scale_range=_data.FSR)

    def get_data_status(self) -> OPT3001_data_status:
        """
        读取数据就绪状态和溢出标志
        Args:
            无
        Returns:
            OPT3001_data_status: 包含 conversion_ready 和 overflow 字段
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：刷新内部配置缓存
        ==========================================
        Read data ready status and overflow flag.
        Args:
            None
        Returns:
            OPT3001_data_status: Namedtuple with conversion_ready and overflow
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Refreshes internal config cache
        """
        self.read_config_from_sensor(return_value=False)
        return OPT3001_data_status(conversion_ready=self.conversion_ready, overflow=self.overflow)

    def is_single_shot_mode(self) -> bool:
        """
        判断传感器是否处于单次测量模式
        Args:
            无
        Returns:
            bool: True 表示单次测量模式
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if sensor is in single-shot mode.
        Args:
            None
        Returns:
            bool: True if in single-shot mode
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self.mode == 1

    def is_continuously_mode(self) -> bool:
        """
        判断传感器是否处于连续测量模式
        Args:
            无
        Returns:
            bool: True 表示连续测量模式（mode 为 2 或 3）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if sensor is in continuous mode.
        Args:
            None
        Returns:
            bool: True if in continuous mode (mode 2 or 3)
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self.mode == 2 or self.mode == 3

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

    def __next__(self) -> opt3001_meas_data:
        """
        迭代器接口：连续模式下数据就绪时返回原始测量值
        Args:
            无
        Returns:
            opt3001_meas_raw 或 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 仅在连续测量模式且数据就绪时返回有效值
        ==========================================
        Iterator: return raw measurement in continuous mode when data is ready.
        Args:
            None
        Returns:
            opt3001_meas_raw or None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Returns valid data only in continuous mode when conversion is ready
        """
        ds = self.get_data_status()
        if self.is_continuously_mode() and ds.conversion_ready:
            return self.get_measurement_value(0)

    @property
    def lux_range_index(self) -> int:
        """
        照度量程索引（RN 字段）。0~11 固定量程，12 自动量程
        ==========================================
        Lux range index (RN field). 0~11 fixed, 12 auto full-scale.
        """
        return self._get_config_field("RN")

    @lux_range_index.setter
    def lux_range_index(self, value: int) -> None:
        self._set_config_field(value, "RN")

    @property
    def long_conversion_time(self) -> bool:
        """
        转换时间（CT 字段）。False=100ms，True=800ms
        ==========================================
        Conversion time (CT field). False=100ms, True=800ms.
        """
        return self._get_config_field("CT")

    @long_conversion_time.setter
    def long_conversion_time(self, value: bool) -> None:
        self._set_config_field(value, "CT")

    @property
    def mode(self) -> int:
        """
        工作模式（M 字段）。0=省电，1=单次，2/3=连续
        ==========================================
        Operation mode (M field). 0=power-save, 1=single-shot, 2/3=continuous.
        """
        return self._get_config_field("M")

    @mode.setter
    def mode(self, value: int) -> None:
        self._set_config_field(value, "M")

    @property
    def overflow(self) -> bool:
        """
        溢出标志（OVF 字段）。True 表示测量值超出当前量程
        ==========================================
        Overflow flag (OVF field). True if measurement exceeds current range.
        """
        return self._get_config_field("OVF")

    @property
    def conversion_ready(self) -> bool:
        """
        转换就绪标志（CRF 字段）。True 表示转换完成，数据可读
        ==========================================
        Conversion ready flag (CRF field). True when conversion is complete.
        """
        return self._get_config_field("CRF")

    @property
    def flag_high(self) -> bool:
        """
        高阈值比较标志（FH 字段）。True 表示测量值超过高阈值
        ==========================================
        High flag (FH field). True if result exceeds high-limit register.
        """
        return self._get_config_field("FH")

    @property
    def flag_low(self) -> bool:
        """
        低阈值比较标志（FL 字段）。True 表示测量值低于低阈值
        ==========================================
        Low flag (FL field). True if result is below low-limit register.
        """
        return self._get_config_field("FL")

    @property
    def latch(self) -> bool:
        """
        锁存模式（L 字段）。控制 INT 引脚和 FH/FL 标志的报告方式
        ==========================================
        Latch field (L). Controls INT pin and FH/FL reporting style.
        """
        return self._get_config_field("L")

    @latch.setter
    def latch(self, value: bool) -> None:
        self._set_config_field(value, "L")

    @property
    def polarity(self) -> bool:
        """
        INT 引脚极性（POL 字段）。False=低有效，True=高有效
        ==========================================
        INT pin polarity (POL field). False=active-low, True=active-high.
        """
        return self._get_config_field("POL")

    @polarity.setter
    def polarity(self, value: bool) -> None:
        self._set_config_field(value, "POL")

    @property
    def mask_exponent(self) -> bool:
        """
        指数屏蔽位（ME 字段）。True 时结果寄存器指数字段被屏蔽为 0
        ==========================================
        Mask exponent (ME field). True masks exponent field in result register.
        """
        return self._get_config_field("ME")

    @mask_exponent.setter
    def mask_exponent(self, value: bool) -> None:
        self._set_config_field(value, "ME")

    @property
    def fault_count(self) -> int:
        """
        故障计数（FC 字段）。触发 INT 引脚所需的连续超限次数
        ==========================================
        Fault count (FC field). Consecutive out-of-range results needed to trigger INT.
        """
        return self._get_config_field("FC")

    @fault_count.setter
    def fault_count(self, value: int) -> None:
        self._set_config_field(value, "FC")

    def _get_config_field(self, field_name=None):
        """从位域缓存读取指定字段值，field_name 为 None 时返回完整源值"""
        bf = self._bit_fields
        if field_name is None:
            return bf.source
        return bf[field_name]

    def _set_config_field(self, value: int, field_name=None) -> None:
        """向位域缓存写入指定字段值，field_name 为 None 时写入完整源值"""
        bf = self._bit_fields
        if field_name is None:
            bf.source = value
            return
        bf[field_name] = value

    @staticmethod
    def _get_lsb_fsr(exp_raw: int) -> _opt3001_lsb_fsr:
        """
        根据指数字段计算 LSB 精度和满量程范围
        Args:
            exp_raw (int): 原始指数值，范围 0~11
        Returns:
            _opt3001_lsb_fsr: LSB 和 FSR 值（单位 Lux）；exp_raw 超范围时两者均为 None
        Notes:
            - ISR-safe: 是
        ==========================================
        Calculate LSB and FSR from exponent field.
        Args:
            exp_raw (int): Raw exponent, range 0~11
        Returns:
            _opt3001_lsb_fsr: LSB and FSR in Lux; both None if out of range
        Notes:
            - ISR-safe: Yes
        """
        if exp_raw < 0 or exp_raw > 11:
            return _opt3001_lsb_fsr(None, None)
        _lsb = 0.01 * (1 << exp_raw)
        _fsr = 40.95 * (1 << exp_raw)
        return _opt3001_lsb_fsr(_lsb, _fsr)

    def deinit(self) -> None:
        """
        释放传感器资源，将传感器置于省电模式
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：将传感器 mode 设为 0（省电模式）并写入寄存器
        ==========================================
        Release sensor resources, set sensor to power-save mode.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Sets sensor mode to 0 (power-save) and writes register
        """
        self.mode = 0
        self.write_config_to_sensor()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
