# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : hts221.py
# @Description : ST HTS221 温湿度传感器驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================
from micropython import const
from i2c_helpers import CBits, RegisterStruct

try:
    from time import sleep_ms, ticks_diff, ticks_ms
except ImportError:
    from utime import sleep_ms, ticks_diff, ticks_ms

# ======================================== 全局变量 ============================================
__version__ = "1.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# WHO_AM_I 寄存器地址
_WHO_AM_I = const(0x0F)

# 控制寄存器地址
_CTRL_REG1 = const(0x20)
_CTRL_REG2 = const(0x21)
_CTRL_REG3 = const(0x22)
# 状态寄存器地址
_STATUS_REG = const(0x27)

# 湿度数据输出寄存器（LSB，地址与 0x80 以启用多字节读取）
_HUMIDITY_OUT_L = const(0x28 | 0x80)
# 温度数据输出寄存器（LSB，地址与 0x80 以启用多字节读取）
_TEMP_OUT_L = const(0x2A | 0x80)

# 湿度校准 LSB 值寄存器
_H0_RH_X2 = const(0x30)
_H1_RH_X2 = const(0x31)

# 温度校准值寄存器（T0, T1 各 10 位）
_T0_DEGC_X8 = const(0x32)
_T1_DEGC_X8 = const(0x33)
# T0 和 T1 的高 2 位（各 10 位）
_T1_T0_MSB = const(0x35)

# 湿度校准输出值寄存器
_H0_T0_OUT = const(0x36 | 0x80)
_H1_T1_OUT = const(0x3A | 0x80)

# 温度校准输出值寄存器
_T0_OUT = const(0x3C | 0x80)
_T1_OUT = const(0x3E | 0x80)

# 数据速率选项
# 单次测量模式
ONE_SHOT = const(0b00)
# 1 Hz 连续测量
RATE_1_HZ = const(0b01)
# 7 Hz 连续测量
RATE_7_HZ = const(0b10)
# 12.5 Hz 连续测量
RATE_12_5_HZ = const(0b11)
data_rate_values = (ONE_SHOT, RATE_1_HZ, RATE_7_HZ, RATE_12_5_HZ)

_WAIT_TIMEOUT_MS = const(1000)
_WAIT_POLL_MS = const(2)

# 块数据更新选项
# 禁用块数据更新
BDU_DISABLED = const(0b0)
# 启用块数据更新（推荐）
BDU_ENABLED = const(0b1)
block_data_update_values = (BDU_DISABLED, BDU_ENABLED)

# WHO_AM_I 期望值
_HTS221_CHIP_ID = const(0xBC)

# ======================================== 功能函数 ============================================
# 无独立功能函数，所有操作封装在类中


# ======================================== 自定义类 ============================================
class HTS221:
    """
    HTS221 温湿度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        relative_humidity: 获取相对湿度值 (%rH)
        temperature: 获取温度值 (℃)
        data_rate: 获取/设置数据速率
        block_data_update: 获取/设置块数据更新模式
        take_measurements(): 触发单次测量（仅 ONE_SHOT 模式）
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 初始化时自动加载校准数据
        - 支持 12.5Hz 最大输出数据速率
    ==========================================
    HTS221 temperature and humidity sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        relative_humidity: Get relative humidity (%rH)
        temperature: Get temperature (Celsius)
        data_rate: Get/set data rate
        block_data_update: Get/set block data update mode
        take_measurements(): Trigger single measurement (ONE_SHOT mode only)
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Automatically loads calibration data on init
        - Supports up to 12.5Hz output data rate
    """

    # 类级常量
    # WHO_AM_I 设备ID寄存器
    _device_id = RegisterStruct(_WHO_AM_I, "<B")
    # 启动位（触发传感器重新校准）
    _boot_bit = CBits(1, _CTRL_REG2, 7)
    # 传感器使能位
    enabled = CBits(1, _CTRL_REG1, 7)
    # 数据速率选择位
    _data_rate = CBits(2, _CTRL_REG1, 0)
    # 块数据更新使能位
    _block_data_update = CBits(2, _CTRL_REG1, 2)

    # 单次测量触发位
    _one_shot_bit = CBits(1, _CTRL_REG2, 0)
    # 温度原始数据寄存器
    _raw_temperature = RegisterStruct(_TEMP_OUT_L, "<h")
    # 湿度原始数据寄存器
    _raw_humidity = RegisterStruct(_HUMIDITY_OUT_L, "<h")

    # 温度校准值 T0 低字节
    _t0_deg_c_x8_lsbyte = CBits(8, _T0_DEGC_X8, 0)
    # 温度校准值 T1 低字节
    _t1_deg_c_x8_lsbyte = CBits(8, _T1_DEGC_X8, 0)
    # T0/T1 高 2 位（各 10 位）
    _t1_t0_deg_c_x8_msbits = CBits(4, _T1_T0_MSB, 0)

    # 温度校准输出值寄存器
    _t0_out = RegisterStruct(_T0_OUT, "<h")
    _t1_out = RegisterStruct(_T1_OUT, "<h")

    # 湿度校准值寄存器
    _h0_rh_x2 = RegisterStruct(_H0_RH_X2, "<B")
    _h1_rh_x2 = RegisterStruct(_H1_RH_X2, "<B")

    # 湿度校准输出值寄存器
    _h0_t0_out = RegisterStruct(_H0_T0_OUT, "<h")
    _h1_t0_out = RegisterStruct(_H1_T1_OUT, "<h")

    def __init__(self, i2c, address: int = 0x5F, debug: bool = False) -> None:
        """
        初始化 HTS221 传感器
        Args:
            i2c (I2C): I2C 总线实例
            address (int): I2C 设备地址，默认 0x5F
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型错误
            RuntimeError: 设备未找到或 I2C 通信失败
        Notes:
            - 初始化时自动执行启动序列和加载校准数据
            - ISR-safe: 否
        ==========================================
        Initialize HTS221 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, default 0x5F
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: Device not found or I2C communication failed
        Notes:
            - Automatically executes boot sequence and loads calibration data
            - ISR-safe: No
        """
        # 参数校验：检查 i2c 参数类型
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：检查 address 参数类型和值范围
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0 or address > 0x7F:
            raise ValueError("address must be 0~0x7F, got 0x%02X" % address)
        # 参数校验：检查 debug 参数类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 读取设备 ID 验证设备存在
        try:
            chip_id = self._device_id
        except OSError as e:
            raise RuntimeError("Failed to communicate with HTS221 at 0x%02X" % address) from e
        if chip_id != _HTS221_CHIP_ID:
            raise RuntimeError("Failed to find HTS221: expected 0x%02X, got 0x%02X" % (_HTS221_CHIP_ID, chip_id))

        # 执行传感器启动序列（重新加载校准数据）
        self._boot()
        # 启用传感器
        self.enabled = True
        # 设置默认数据速率为 12.5 Hz
        self.data_rate = RATE_12_5_HZ
        # 启用块数据更新（防止读取时数据撕裂）
        self._block_data_update = BDU_ENABLED

        # 加载温度校准数据
        t1_t0_msbs = self._t1_t0_deg_c_x8_msbits
        # 读取 T0 校准值（10 位）
        self.calib_temp_value_0 = self._t0_deg_c_x8_lsbyte
        self.calib_temp_value_0 |= (t1_t0_msbs & 0b0011) << 8

        # 读取 T1 校准值（10 位）
        self.calibrated_value_1 = self._t1_deg_c_x8_lsbyte
        self.calibrated_value_1 |= (t1_t0_msbs & 0b1100) << 6

        # 除以 8 去除 x8 缩放
        self.calib_temp_value_0 >>= 3
        self.calibrated_value_1 >>= 3

        # 读取温度校准输出原始值
        self.calib_temp_meas_0 = self._t0_out
        self.calib_temp_meas_1 = self._t1_out

        # 加载湿度校准数据
        # 读取 H0 校准值并除以 2 去除 x2 缩放
        self.calib_hum_value_0 = self._h0_rh_x2
        self.calib_hum_value_0 >>= 1

        # 读取 H1 校准值并除以 2 去除 x2 缩放
        self.calib_hum_value_1 = self._h1_rh_x2
        self.calib_hum_value_1 >>= 1

        # 读取湿度校准输出原始值
        self.calib_hum_meas_0 = self._h0_t0_out
        self.calib_hum_meas_1 = self._h1_t0_out

    def _boot(self) -> None:
        """
        执行传感器启动序列
        触发重新加载校准数据到内部寄存器。
        Notes:
            - 启动完成后 _boot_bit 自动清零
        ==========================================
        Execute sensor boot sequence.
        Triggers reload of calibration data into internal registers.
        Notes:
            - _boot_bit auto-clears when boot completes
        """
        # 设置启动位触发校准数据重新加载
        self._boot_bit = True
        # 等待启动完成（_boot_bit 自动清零）
        start = ticks_ms()
        while self._boot_bit:
            if ticks_diff(ticks_ms(), start) >= _WAIT_TIMEOUT_MS:
                raise RuntimeError("HTS221 boot timeout")
            sleep_ms(_WAIT_POLL_MS)

    @property
    def relative_humidity(self) -> float:
        """
        获取当前相对湿度值
        Returns:
            float: 相对湿度百分比 (%rH)
        Notes:
            - ISR-safe: 否
            - 使用校准数据进行线性插值计算
        ==========================================
        Get current relative humidity.
        Returns:
            float: Relative humidity percentage (%rH)
        Notes:
            - ISR-safe: No
            - Uses calibration data for linear interpolation
        """
        # 计算校准斜率和偏移量
        calibrated_value_delta = self.calib_hum_value_1 - self.calib_hum_value_0
        calibrated_measurement_delta = self.calib_hum_meas_1 - self.calib_hum_meas_0

        calibration_value_offset = self.calib_hum_value_0
        calibrated_measurement_offset = self.calib_hum_meas_0
        # 零位调整原始测量值
        zeroed_measured_humidity = self._raw_humidity - calibrated_measurement_offset

        # 计算校准修正因子
        correction_factor = calibrated_value_delta / calibrated_measurement_delta

        # 应用线性校准
        adjusted_humidity = zeroed_measured_humidity * correction_factor + calibration_value_offset

        return adjusted_humidity

    @property
    def temperature(self) -> float:
        """
        获取当前温度值
        Returns:
            float: 温度值（℃）
        Notes:
            - ISR-safe: 否
            - 使用校准数据进行线性插值计算
        ==========================================
        Get current temperature.
        Returns:
            float: Temperature in Celsius
        Notes:
            - ISR-safe: No
            - Uses calibration data for linear interpolation
        """
        # 计算校准斜率和偏移量
        calibrated_value_delta = self.calibrated_value_1 - self.calib_temp_value_0
        calibrated_measurement_delta = self.calib_temp_meas_1 - self.calib_temp_meas_0

        calibration_value_offset = self.calib_temp_value_0
        calibrated_measurement_offset = self.calib_temp_meas_0
        # 零位调整原始测量值
        zeroed_measured_temp = self._raw_temperature - calibrated_measurement_offset

        # 计算校准修正因子
        correction_factor = calibrated_value_delta / calibrated_measurement_delta

        # 应用线性校准
        adjusted_temp = (zeroed_measured_temp * correction_factor) + calibration_value_offset

        return adjusted_temp

    @property
    def data_rate(self) -> str:
        """
        获取当前数据速率
        Returns:
            str: 数据速率名称字符串
        Notes:
            - 设置为 ONE_SHOT 时，只有调用 take_measurements() 才会更新测量值
            - ISR-safe: 否
        ==========================================
        Get current data rate.
        Returns:
            str: Data rate name string
        Notes:
            - When set to ONE_SHOT, measurements only update when take_measurements() is called
            - ISR-safe: No
        """
        # 速率名称映射表
        values = ("ONE_SHOT", "RATE_1_HZ", "RATE_7_HZ", "RATE_12_5_HZ")
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        # 写入数据速率寄存器
        self._data_rate = value

    def take_measurements(self, timeout_ms: int = _WAIT_TIMEOUT_MS) -> None:
        """
        触发单次测量
        仅在 data_rate 设置为 ONE_SHOT 时有效。
        Notes:
            - ISR-safe: 否
            - 等待测量完成后自动返回
        ==========================================
        Trigger a single measurement.
        Only meaningful when data_rate is set to ONE_SHOT.
        Notes:
            - ISR-safe: No
            - Returns automatically after measurement completes
        """
        # 设置单次测量触发位
        self._one_shot_bit = True
        # 等待测量完成（_one_shot_bit 自动清零）
        start = ticks_ms()
        while self._one_shot_bit:
            if ticks_diff(ticks_ms(), start) >= timeout_ms:
                raise RuntimeError("HTS221 one-shot measurement timeout")
            sleep_ms(_WAIT_POLL_MS)

    @property
    def block_data_update(self) -> str:
        """
        获取块数据更新模式
        BDU 用于防止读取输出寄存器的高位和低位之间数据被更新，
        导致数据不一致。推荐设置为 BDU_ENABLED。
        Returns:
            str: 块数据更新模式名称
        Notes:
            - ISR-safe: 否
        ==========================================
        Get block data update mode.
        BDU prevents output register updates between reading upper
        and lower register parts. Recommended to set BDU_ENABLED.
        Returns:
            str: Block data update mode name
        Notes:
            - ISR-safe: No
        """
        # 模式名称映射表
        values = ("BDU_DISABLED", "BDU_ENABLED")
        return values[self._block_data_update]

    @block_data_update.setter
    def block_data_update(self, value: int) -> None:
        if value not in block_data_update_values:
            raise ValueError("Value must be a valid block_data_update setting")
        # 写入块数据更新寄存器
        self._block_data_update = value

    def deinit(self) -> None:
        """
        释放传感器资源
        禁用传感器以降低功耗。
        Notes:
            - ISR-safe: 否
            - 调用后传感器停止采样
        ==========================================
        Release sensor resources.
        Disables the sensor to reduce power consumption.
        Notes:
            - ISR-safe: No
            - Sensor stops sampling after call
        """
        try:
            self.enabled = False
        except OSError:
            pass

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 _debug=True 时输出
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug=True
        """
        if self._debug:
            print("[HTS221] %s" % msg)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
