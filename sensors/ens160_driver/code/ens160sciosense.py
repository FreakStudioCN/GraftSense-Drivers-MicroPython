# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/21 16:52
# @Author  : FreakStudio
# @File    : ens160sciosense.py
# @Description : ENS160 数字金属氧化物多气体传感器驱动
# @License : MIT
s
__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython
from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import IBaseSensorEx, DeviceEx, IDentifier, Iterator, check_value

# ======================================== 全局变量 ============================================

# eCO2: 等效二氧化碳浓度 [ppm]；TVOC: 总挥发性有机化合物浓度 [ppb]；
# AQI: 空气质量指数（UBA标准）1=优秀..5=极差
ens160_air_params = namedtuple("ens160_air_params", "eco2 tvoc aqi")
# stat_as: bit7 运行模式激活；stat_error: bit6 错误标志；
# validity_flag: bit2-3 0=正常/1=预热/2=初始启动/3=无效
# new_data: bit1 新数据就绪；new_gpr: bit0 新GPR数据就绪
ens160_status = namedtuple("ens160_status", "stat_as stat_error validity_flag new_data new_gpr")
# int_pol: bit6 中断极性；int_cfg: bit5 引脚驱动；
# int_gpr: bit3 GPR中断；int_dat: bit1 DATA中断；int_en: bit0 总使能
ens160_config = namedtuple("ens160_config", "int_pol int_cfg int_gpr int_dat int_en")
ens160_firmware_version = namedtuple("ens160_firmware_version", "major minor release")

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class Ens160(IBaseSensorEx, IDentifier, Iterator):
    """
    ENS160 数字金属氧化物多气体传感器驱动类
    Attributes:
        _connector (DeviceEx): 设备通信连接器
        _check_crc (bool): 是否启用 CRC 校验
    Methods:
        start_measurement(start): 启动/暂停连续测量
        get_measurement_value(index): 读取测量值
        get_data_status(raw): 读取数据就绪状态
        set_ambient_temp(celsius): 写入温度补偿值
        set_humidity(rh): 写入湿度补偿值
        get_firmware_version(): 读取固件版本
        deinit(): 释放资源，进入深度睡眠
    Notes:
        - 依赖外部传入 I2cAdapter 实例，不在内部创建总线
        - CRC 校验使用 Sciosense 专有算法，需单独读取校验寄存器
    ==========================================
    ENS160 digital metal-oxide multi-gas sensor driver.
    Attributes:
        _connector (DeviceEx): Device communication connector
        _check_crc (bool): Whether CRC verification is enabled
    Methods:
        start_measurement(start): Start/pause continuous measurement
        get_measurement_value(index): Read measurement value
        get_data_status(raw): Read data ready status
        set_ambient_temp(celsius): Write temperature compensation
        set_humidity(rh): Write humidity compensation
        get_firmware_version(): Read firmware version
        deinit(): Release resources, enter deep sleep
    Notes:
        - Requires externally provided I2cAdapter instance
        - CRC uses Sciosense proprietary algorithm requiring separate register read
    """

    # 寄存器地址常量
    _REG_PART_ID = micropython.const(0x00)
    _REG_OPMODE  = micropython.const(0x10)
    _REG_CONFIG  = micropython.const(0x11)
    _REG_COMMAND = micropython.const(0x12)
    _REG_TEMP_IN = micropython.const(0x13)
    _REG_RH_IN   = micropython.const(0x15)
    _REG_STATUS  = micropython.const(0x20)
    _REG_AQI     = micropython.const(0x21)
    _REG_TVOC    = micropython.const(0x22)
    _REG_ECO2    = micropython.const(0x24)
    _REG_MISR    = micropython.const(0x38)
    _REG_GPR_RD  = micropython.const(0x48)

    # 工作模式常量
    _MODE_DEEP_SLEEP = micropython.const(0x00)
    _MODE_IDLE       = micropython.const(0x01)
    _MODE_STANDARD   = micropython.const(0x02)
    _MODE_RESET      = micropython.const(0xF0)

    # 内部命令常量
    _CMD_NOP        = micropython.const(0x00)
    _CMD_GET_APPVER = micropython.const(0x0E)
    _CMD_CLRGPR     = micropython.const(0xCC)

    # CRC 多项式
    _CRC_POLY = micropython.const(0x1D)

    # 默认 I2C 地址
    I2C_DEFAULT_ADDR = micropython.const(0x52)

    def __init__(self, adapter: bus_service.I2cAdapter, address: int = I2C_DEFAULT_ADDR,
                 check_crc: bool = True) -> None:
        """
        初始化 ENS160 驱动
        Args:
            adapter (I2cAdapter): I2C 适配器实例
            address (int): I2C 地址，0x52 或 0x53，默认 0x52
            check_crc (bool): 是否启用 CRC 校验，默认 True
        Returns:
            None
        Raises:
            ValueError: adapter 为 None 或 address 不合法
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize ENS160 driver.
        Args:
            adapter (I2cAdapter): I2C adapter instance
            address (int): I2C address, 0x52 or 0x53, default 0x52
            check_crc (bool): Enable CRC verification, default True
        Returns:
            None
        Raises:
            ValueError: adapter is None or address invalid
        Notes:
            - ISR-safe: No
        """
        if adapter is None:
            raise ValueError("adapter must not be None")
        if not hasattr(adapter, "read_register"):
            raise ValueError("adapter must be an I2cAdapter instance")
        if address not in (0x52, 0x53):
            raise ValueError("address must be 0x52 or 0x53, got 0x%02X" % address)
        self._connector = DeviceEx(adapter=adapter, address=address, big_byte_order=False)
        self._check_crc = check_crc

    # ---- 公共方法 ----

    def get_id(self) -> int:
        """
        读取传感器 Part Number
        Args:
            无
        Returns:
            int: Part Number（ENS160 期望值 0x0160）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor Part Number.
        Args:
            None
        Returns:
            int: Part Number (ENS160 expected 0x0160)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._connector.unpack("H", self._read_register(self._REG_PART_ID, 2))[0]

    def soft_reset(self) -> None:
        """
        软件复位传感器
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否；复位后需重新初始化
        ==========================================
        Software reset the sensor.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No; re-initialization required after reset
        """
        self._set_mode(self._MODE_RESET)

    def get_config(self, raw: bool = True):
        """
        读取当前中断配置
        Args:
            raw (bool): True 返回原始 int，False 返回 ens160_config，默认 True
        Returns:
            int 或 ens160_config: 当前配置值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current interrupt configuration.
        Args:
            raw (bool): True returns raw int, False returns ens160_config, default True
        Returns:
            int or ens160_config: Current configuration
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        raw_val = self._read_register(self._REG_CONFIG, 1)[0]
        return raw_val if raw else Ens160._to_config(raw_val)

    def set_config(self, new_config) -> None:
        """
        写入中断配置
        Args:
            new_config (int 或 ens160_config): 配置值
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write interrupt configuration.
        Args:
            new_config (int or ens160_config): Configuration value
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        if isinstance(new_config, ens160_config):
            new_config = Ens160._to_raw_config(new_config)
        self._connector.write_reg(self._REG_CONFIG, new_config, 1)

    def set_ambient_temp(self, value_in_celsius: float) -> None:
        """
        写入环境温度补偿值
        Args:
            value_in_celsius (float): 温度值（摄氏度），用于提高测量精度
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否；应从外部温度传感器读取后传入
        ==========================================
        Write ambient temperature compensation value.
        Args:
            value_in_celsius (float): Temperature in Celsius for accuracy improvement
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No; should be read from external temperature sensor
        """
        # 转换为寄存器格式：64 * (273.15 + T)
        t = int(64 * (273.15 + value_in_celsius))
        self._connector.write_reg(self._REG_TEMP_IN, t, 2)

    def set_humidity(self, rel_hum: int) -> None:
        """
        写入相对湿度补偿值
        Args:
            rel_hum (int): 相对湿度（%，0-100）
        Returns:
            None
        Raises:
            ValueError: rel_hum 超出 0-100 范围
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write relative humidity compensation value.
        Args:
            rel_hum (int): Relative humidity (%, 0-100)
        Returns:
            None
        Raises:
            ValueError: rel_hum out of range 0-100
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        check_value(rel_hum, range(101), "humidity must be 0-100, got %d" % rel_hum)
        # 寄存器格式：rel_hum << 9
        self._connector.write_reg(self._REG_RH_IN, rel_hum << 9, 2)

    def get_firmware_version(self) -> ens160_firmware_version:
        """
        读取固件版本
        Args:
            无
        Returns:
            ens160_firmware_version: 固件版本 (major, minor, release)
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read firmware version.
        Args:
            None
        Returns:
            ens160_firmware_version: Firmware version (major, minor, release)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        b = self._exec_cmd(self._CMD_GET_APPVER)
        return ens160_firmware_version(major=b[4], minor=b[5], release=b[6])

    def get_conversion_cycle_time(self) -> int:
        """
        返回测量周期时间
        Args:
            无
        Returns:
            int: 测量周期（ms），固定 1000ms
        Raises:
            无
        Notes:
            - ISR-safe: 是
        ==========================================
        Return measurement cycle time.
        Args:
            None
        Returns:
            int: Measurement period in ms, fixed 1000ms
        Raises:
            None
        Notes:
            - ISR-safe: Yes
        """
        return 1000

    def start_measurement(self, start: bool = True) -> None:
        """
        启动或暂停连续测量
        Args:
            start (bool): True=启动标准测量模式，False=切换至空闲模式，默认 True
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否；调用后需等待至少一个测量周期再读取数据
        ==========================================
        Start or pause continuous measurement.
        Args:
            start (bool): True=start standard mode, False=switch to idle, default True
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No; wait at least one cycle before reading data
        """
        self._set_mode(self._MODE_STANDARD if start else self._MODE_IDLE)

    def get_measurement_value(self, value_index):
        """
        读取测量值
        Args:
            value_index (int 或 None): 0=eCO2[ppm], 1=TVOC[ppb], 2=AQI[1-5], None=返回全部
        Returns:
            int 或 ens160_air_params: 对应测量值或全部数据
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否；建议先检查 get_data_status 确认新数据就绪
        ==========================================
        Read measurement value.
        Args:
            value_index (int or None): 0=eCO2[ppm], 1=TVOC[ppb], 2=AQI[1-5], None=all
        Returns:
            int or ens160_air_params: Requested measurement or all data
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No; check get_data_status for new data first
        """
        if value_index == 0:
            return self._get_eco2()
        if value_index == 1:
            return self._get_tvoc()
        if value_index == 2:
            return self._get_aqi()
        if value_index is None:
            return ens160_air_params(eco2=self._get_eco2(), tvoc=self._get_tvoc(), aqi=self._get_aqi())

    def get_data_status(self, raw: bool = True):
        """
        读取数据就绪状态
        Args:
            raw (bool): True 返回原始 int，False 返回 ens160_status，默认 True
        Returns:
            int 或 ens160_status: 当前状态
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read data ready status.
        Args:
            raw (bool): True returns raw int, False returns ens160_status, default True
        Returns:
            int or ens160_status: Current status
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._get_status(raw=raw)

    def is_single_shot_mode(self) -> bool:
        """
        是否处于单次测量模式
        Args:
            无
        Returns:
            bool: ENS160 不支持单次模式，始终返回 False
        Notes:
            - ISR-safe: 是
        ==========================================
        Whether in single-shot mode.
        Args:
            None
        Returns:
            bool: ENS160 does not support single-shot, always False
        Notes:
            - ISR-safe: Yes
        """
        return False

    def is_continuously_mode(self) -> bool:
        """
        是否处于连续测量模式
        Args:
            无
        Returns:
            bool: True=当前为标准连续测量模式
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Whether in continuous measurement mode.
        Args:
            None
        Returns:
            bool: True if currently in standard continuous mode
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._get_mode() == self._MODE_STANDARD

    def deinit(self) -> None:
        """
        释放资源，进入深度睡眠模式
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否；调用后传感器进入低功耗待机状态
        ==========================================
        Release resources and enter deep sleep mode.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No; sensor enters low-power standby after call
        """
        self._set_mode(self._MODE_DEEP_SLEEP)

    # ---- 迭代器 ----

    def __next__(self):
        """
        迭代器：连续模式下有新数据时返回测量值
        Args:
            无
        Returns:
            ens160_air_params 或 None: 新数据就绪时返回测量值，否则返回 None
        Notes:
            - ISR-safe: 否
        ==========================================
        Iterator: return measurement when new data available in continuous mode.
        Args:
            None
        Returns:
            ens160_air_params or None: Measurement if new data ready, else None
        Notes:
            - ISR-safe: No
        """
        if not self.is_continuously_mode():
            return None
        status = self.get_data_status(raw=False)
        # 检查新数据就绪标志位
        if status.new_data:
            return self.get_measurement_value(None)
        return None

    # ---- 私有方法 ----

    @staticmethod
    def _to_raw_config(cfg: ens160_config) -> int:
        n_bits = 6, 5, 3, 1, 0
        return sum(int(cfg[i]) << n_bits[i] for i in range(len(n_bits)))

    @staticmethod
    def _to_config(raw_cfg: int) -> ens160_config:
        n_bits = 6, 5, 3, 1, 0
        return ens160_config(*[bool(raw_cfg & (1 << b)) for b in n_bits])

    @staticmethod
    def _to_status(st: int) -> ens160_status:
        return ens160_status(
            stat_as=bool(st & 0x80),
            stat_error=bool(st & 0x40),
            validity_flag=(st & 0x0C) >> 2,
            new_data=bool(st & 0x02),
            new_gpr=bool(st & 0x01),
        )

    @staticmethod
    def _crc8(sequence, polynomial: int, init_value: int) -> int:
        # Sciosense 专有 CRC8 算法，需在读取数据前后各读一次校验寄存器
        crc = init_value & 0xFF
        for item in sequence:
            tmp = 0xFF & ((crc << 1) ^ item)
            crc = tmp if not (crc & 0x80) else tmp ^ polynomial
        return crc

    def _read_register(self, reg_addr: int, bytes_count: int = 2) -> bytes:
        # CRC 校验：读取数据前先获取上次校验值
        before = self._get_last_checksum() if self._check_crc else 0
        try:
            b = self._connector.read_reg(reg_addr, bytes_count)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg_addr) from e
        if self._check_crc and 0 <= reg_addr < 0x38:
            # 计算本次读取数据的 CRC 并与传感器返回值比对
            crc = Ens160._crc8(b, self._CRC_POLY, before)
            after = self._get_last_checksum()
            if crc != after:
                raise RuntimeError("CRC error: calc=0x%02X != read=0x%02X" % (crc, after))
        return b

    def _set_mode(self, new_mode: int) -> None:
        # 校验模式值合法性
        nm = check_value(new_mode, (0, 1, 2, 0xF0), "Invalid mode: 0x%02X" % new_mode)
        try:
            self._connector.write_reg(self._REG_OPMODE, nm, 1)
        except OSError as e:
            raise RuntimeError("I2C write failed at OPMODE") from e

    def _get_mode(self) -> int:
        return self._read_register(self._REG_OPMODE, 1)[0]

    def _exec_cmd(self, cmd: int) -> bytes:
        # 校验命令码合法性
        check_value(cmd, (0x00, 0x0E, 0xCC), "Invalid command: 0x%02X" % cmd)
        try:
            self._connector.write_reg(self._REG_COMMAND, cmd, 1)
        except OSError as e:
            raise RuntimeError("I2C write failed at COMMAND") from e
        return self._read_register(self._REG_GPR_RD, 8)

    def _get_status(self, raw: bool = True):
        reg_val = self._read_register(self._REG_STATUS, 1)[0]
        return reg_val if raw else Ens160._to_status(reg_val)

    def _get_aqi(self) -> int:
        return 0x07 & self._read_register(self._REG_AQI, 1)[0]

    def _get_tvoc(self) -> int:
        return self._connector.unpack("H", self._read_register(self._REG_TVOC, 2))[0]

    def _get_eco2(self) -> int:
        return self._connector.unpack("H", self._read_register(self._REG_ECO2, 2))[0]

    def _get_last_checksum(self) -> int:
        # 直接读取 CRC 寄存器，不经过 _read_register 避免递归
        return self._connector.read_reg(self._REG_MISR, 1)[0]

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
