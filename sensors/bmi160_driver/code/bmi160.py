# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Jose D. Montoya
# @File    : bmi160.py
# @Description : BMI160 6轴惯性测量单元（加速度计+陀螺仪）I2C 驱动
# @License : MIT

__version__ = "0.0.0+auto.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import time
from micropython import const
from i2c_helpers import CBits, RegisterStruct


# ======================================== 全局变量 ============================================

# --- I2C 地址与寄存器地址 ---
_I2C_ADDR = const(0x69)
_REG_WHOAMI = const(0x00)
_ERROR_CODE = const(0x02)
_COMMAND = const(0x7E)
_ACCEL_CONFIG = const(0x40)
_ACC_RANGE = const(0x41)
_GYRO_CONFIG = const(0x42)
_GYRO_RANGE = const(0x43)

# 复位命令
RESET_COMMAND = const(0xB6)

# --- 加速度计输出数据率（ODR） ---
BANDWIDTH_25_32 = const(0b0001)  # 25/32 Hz
BANDWIDTH_25_16 = const(0b0010)  # 25/16 Hz
BANDWIDTH_25_8 = const(0b0011)  # 25/8 Hz
BANDWIDTH_25_4 = const(0b0100)  # 25/4 Hz
BANDWIDTH_25_2 = const(0b0101)  # 25/2 Hz
BANDWIDTH_25 = const(0b0110)  # 25 Hz
BANDWIDTH_50 = const(0b0111)  # 50 Hz
BANDWIDTH_100 = const(0b1000)  # 100 Hz
BANDWIDTH_200 = const(0b1001)  # 200 Hz
BANDWIDTH_400 = const(0b1010)  # 400 Hz
BANDWIDTH_800 = const(0b1011)  # 800 Hz
BANDWIDTH_1600 = const(0b1100)  # 1600 Hz
BANDWIDTH_3200 = const(0b1101)  # 3200 Hz
# 加速度计有效 ODR 值元组
bandwidth_values = (
    BANDWIDTH_25_32,
    BANDWIDTH_25_16,
    BANDWIDTH_25_8,
    BANDWIDTH_25_4,
    BANDWIDTH_25_2,
    BANDWIDTH_25,
    BANDWIDTH_50,
    BANDWIDTH_100,
    BANDWIDTH_200,
    BANDWIDTH_400,
    BANDWIDTH_800,
    BANDWIDTH_1600,
    BANDWIDTH_3200,
)
# 陀螺仪有效 ODR 值元组（最低 25 Hz）
gyro_bandwidth_values = (
    BANDWIDTH_25,
    BANDWIDTH_50,
    BANDWIDTH_100,
    BANDWIDTH_200,
    BANDWIDTH_400,
    BANDWIDTH_800,
    BANDWIDTH_1600,
    BANDWIDTH_3200,
)

# --- 加速度计量程 ---
ACCEL_RANGE_2G = const(0b0011)
ACCEL_RANGE_4G = const(0b0101)
ACCEL_RANGE_8G = const(0b1000)
ACCEL_RANGE_16G = const(0b1100)
acc_range_values = (ACCEL_RANGE_2G, ACCEL_RANGE_4G, ACCEL_RANGE_8G, ACCEL_RANGE_16G)

# --- 加速度计欠采样模式 ---
NO_UNDERSAMPLE = const(0)
UNDERSAMPLE = const(1)
acc_sample_values = (NO_UNDERSAMPLE, UNDERSAMPLE)

# --- 加速度计带宽参数 ---
FILTER = const(0)
AVERAGING = const(1)
acc_bandwidth_values = (FILTER, AVERAGING)

# 加速度数据寄存器地址
ACC_X_LSB = const(0x12)
ACC_Y_LSB = const(0x14)
ACC_Z_LSB = const(0x16)

# --- 加速度计电源模式 ---
ACC_POWER_SUSPEND = const(0x10)
ACC_POWER_NORMAL = const(0x11)
ACC_POWER_LOWPOWER = const(0x12)
acc_power_mode_values = (ACC_POWER_LOWPOWER, ACC_POWER_NORMAL, ACC_POWER_SUSPEND)

# 温度数据寄存器地址
TEMP_LSB = const(0x20)

# 陀螺仪数据寄存器地址
GYRO_X_LSB = const(0x0C)
GYRO_Y_LSB = const(0x0E)
GYRO_Z_LSB = const(0x10)

# --- 陀螺仪滤波器截止频率 ---
GYRO_NORMAL = const(0b10)
GYRO_OSR2 = const(0b01)
GYRO_OSR4 = const(0b00)
gyro_cutoffs_values = (GYRO_OSR4, GYRO_OSR2, GYRO_NORMAL)

# --- 陀螺仪电源模式 ---
GYRO_POWER_SUSPEND = const(0x14)
GYRO_POWER_NORMAL = const(0x15)
GYRO_POWER_FASTSTARTUP = const(0x17)
gyro_power_modes = (GYRO_POWER_SUSPEND, GYRO_POWER_NORMAL, GYRO_POWER_FASTSTARTUP)

# --- 陀螺仪量程 ---
GYRO_RANGE_2000 = const(0b000)
GYRO_RANGE_1000 = const(0b001)
GYRO_RANGE_500 = const(0b010)
GYRO_RANGE_250 = const(0b011)
GYRO_RANGE_125 = const(0b100)
gyro_values = (
    GYRO_RANGE_125,
    GYRO_RANGE_250,
    GYRO_RANGE_500,
    GYRO_RANGE_1000,
    GYRO_RANGE_2000,
)

# 标准重力加速度 (m/s²)，用于加速度原始值到物理单位的转换
_ACC_CONVERSION = const(9.80665)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class BMI160:
    """
    BMI160 6轴惯性测量单元驱动类，支持加速度计与陀螺仪数据读取及配置。

    Attributes:
        _i2c (I2C): I2C 总线实例（外部注入）
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关

    Methods:
        soft_reset(): 执行软复位
        error_code(): 读取并打印错误码（调试用）
        acceleration: 读取三轴加速度（m/s²）
        gyro: 读取三轴陀螺仪角速度（°/s）
        temperature: 读取温度（℃）
        acceleration_output_data_rate: 获取/设置加速度计输出数据率
        acceleration_range: 获取/设置加速度计量程
        acceleration_undersample: 获取/设置加速度计欠采样模式
        acceleration_bandwidth_parameter: 获取/设置加速度计带宽参数
        acc_power_mode(): 设置加速度计电源模式
        gyro_output_data_rate: 获取/设置陀螺仪输出数据率
        gyro_range: 获取/设置陀螺仪量程
        gyro_bandwidth_parameter: 获取/设置陀螺仪带宽参数
        gyro_power_mode: 获取/设置陀螺仪电源模式
        power_mode_status(): 读取并打印电源模式状态（调试用）
        deinit(): 释放资源

    Notes:
        - 依赖外部传入 I2C 实例，不在类内创建硬件总线
        - 所有 I2C 读写通过 CBits / RegisterStruct 描述符完成，非 ISR-safe
        - 传感器上电后默认加速度计 100 Hz、陀螺仪 100 Hz
    ==========================================
    BMI160 6-axis IMU (Accelerometer + Gyroscope) I2C driver.

    Attributes:
        _i2c (I2C): I2C bus instance (externally provided)
        _address (int): Device I2C address
        _debug (bool): Debug log flag

    Methods:
        soft_reset(): Perform soft reset
        error_code(): Read and print error codes (debug only)
        acceleration: Read 3-axis acceleration (m/s²)
        gyro: Read 3-axis gyroscope angular velocity (°/s)
        temperature: Read temperature (°C)
        acceleration_output_data_rate: Get/set accelerometer ODR
        acceleration_range: Get/set accelerometer range
        acceleration_undersample: Get/set accelerometer undersampling mode
        acceleration_bandwidth_parameter: Get/set accelerometer bandwidth setting
        acc_power_mode(): Set accelerometer power mode
        gyro_output_data_rate: Get/set gyroscope ODR
        gyro_range: Get/set gyroscope range
        gyro_bandwidth_parameter: Get/set gyroscope bandwidth setting
        gyro_power_mode: Get/set gyroscope power mode
        power_mode_status(): Read and print power mode status (debug only)
        deinit(): Release resources

    Notes:
        - Requires externally provided I2C instance
        - All I2C reads/writes via CBits/RegisterStruct descriptors; not ISR-safe
        - Sensor powers up with accelerometer 100 Hz, gyroscope 100 Hz default
    """

    # --- 类级寄存器描述符（通过 I2C 读写芯片寄存器） ---
    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _soft_reset = RegisterStruct(_COMMAND, "B")
    _error_code = RegisterStruct(_ERROR_CODE, "B")
    _acc_config = RegisterStruct(_ACCEL_CONFIG, "B")
    _power_mode = RegisterStruct(0x03, "B")
    _gyro_config = RegisterStruct(_GYRO_CONFIG, "B")

    # 加速度数据（小端有符号 16 位）
    _acc_data_x = RegisterStruct(ACC_X_LSB, "<h")
    _acc_data_y = RegisterStruct(ACC_Y_LSB, "<h")
    _acc_data_z = RegisterStruct(ACC_Z_LSB, "<h")
    _read = RegisterStruct(_COMMAND, "B")

    # ACC_CONF 寄存器 (0x40) — 加速度计配置
    _acc_us = CBits(1, _ACCEL_CONFIG, 7)  # 欠采样选择
    _acc_bwp = CBits(1, _ACCEL_CONFIG, 6)  # 带宽参数
    _acc_odr = CBits(4, _ACCEL_CONFIG, 0)  # 输出数据率

    # ACC_RANGE 寄存器 (0x41) — 加速度计量程
    _acc_range = CBits(4, _ACC_RANGE, 0)

    # 加速度计分辨率查找表（LSB/g 与量程对应）
    acceleration_scale = {
        "ACCEL_RANGE_2G": 16384,
        "ACCEL_RANGE_4G": 8192,
        "ACCEL_RANGE_8G": 4096,
        "ACCEL_RANGE_16G": 2048,
    }
    # 陀螺仪分辨率查找表（LSB/(°/s) 与量程对应）
    gyro_scale = {
        "GYRO_RANGE_2000": 16.4,
        "GYRO_RANGE_1000": 32.8,
        "GYRO_RANGE_500": 65.6,
        "GYRO_RANGE_250": 131.2,
        "GYRO_RANGE_125": 262.4,
    }

    # 温度数据
    _temp_data = RegisterStruct(TEMP_LSB, "<h")

    # 陀螺仪数据（小端有符号 16 位）
    _gyro_data_x = RegisterStruct(GYRO_X_LSB, "<h")
    _gyro_data_y = RegisterStruct(GYRO_Y_LSB, "<h")
    _gyro_data_z = RegisterStruct(GYRO_Z_LSB, "<h")

    # GYRO_CONF 寄存器 (0x42) — 陀螺仪配置
    _gyro_bwp = CBits(2, _GYRO_CONFIG, 4)  # 带宽参数
    _gyro_odr = CBits(4, _GYRO_CONFIG, 0)  # 输出数据率

    # GYRO_RANGE 寄存器 (0x43) — 陀螺仪量程
    _gyro_range = CBits(3, _GYRO_RANGE, 0)

    def __init__(self, i2c, address: int = 0x69, debug: bool = False) -> None:
        """
        初始化 BMI160 传感器驱动实例。

        Args:
            i2c (I2C): MicroPython I2C 总线实例（须支持 readfrom_mem / writeto_mem）
            address (int): 设备 I2C 地址，默认 0x69
            debug (bool): 是否启用调试日志输出，默认 False

        Returns:
            None

        Raises:
            ValueError: i2c 参数不是有效的 I2C 实例
            RuntimeError: 芯片 WHO_AM_I 校验失败，未找到 BMI160

        Notes:
            - 初始化成功后将依次执行：软复位 → 加速度计正常模式 → 陀螺仪正常模式
            - 非 ISR-safe
        ==========================================
        Initialize BMI160 sensor driver instance.

        Args:
            i2c (I2C): MicroPython I2C bus instance (must support readfrom_mem/writeto_mem)
            address (int): Device I2C address, default 0x69
            debug (bool): Enable debug log output, default False

        Returns:
            None

        Raises:
            ValueError: i2c is not a valid I2C instance
            RuntimeError: WHO_AM_I check failed, BMI160 not found

        Notes:
            - After init: soft reset → accelerometer normal mode → gyroscope normal mode
            - Not ISR-safe
        """
        # 参数校验：i2c 须具备 I2C 协议方法（鸭子类型检查）
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance with writeto_mem")
        # 参数校验：address 类型检查
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        # 参数校验：debug 类型检查
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # WHO_AM_I 校验：读取芯片 ID 寄存器，期望值 0xD1
        if self._device_id != 0xD1:
            raise RuntimeError("Failed to find BMI160 (WHO_AM_I mismatch)")

        # 上电初始化序列
        self.soft_reset()

        # 设置加速度计为正常模式
        self._read = 0x03
        time.sleep(0.1)
        self._read = ACC_POWER_NORMAL
        time.sleep(0.1)
        # 设置陀螺仪为正常模式
        self._read = GYRO_POWER_NORMAL
        time.sleep(0.1)

    def _log(self, msg: str) -> None:
        """
        调试日志输出（受 _debug 开关控制）。

        Args:
            msg (str): 日志消息内容

        Returns:
            None

        Notes:
            - ISR-safe: 否
        ==========================================
        Debug log output (controlled by _debug flag).

        Args:
            msg (str): Log message content

        Returns:
            None

        Notes:
            - ISR-safe: No
        """
        if msg is None:
            raise ValueError("msg must not be None")
        if self._debug:
            print("[BMI160] %s" % msg)

    def soft_reset(self) -> None:
        """
        执行软复位，重置所有寄存器为默认值。

        Returns:
            None

        Notes:
            - 复位后需等待约 15ms 使芯片重新就绪
            - 非 ISR-safe
        ==========================================
        Perform a soft reset, restoring all registers to defaults.

        Returns:
            None

        Notes:
            - Wait ~15ms after reset for chip to be ready
            - Not ISR-safe
        """
        self._soft_reset = RESET_COMMAND
        time.sleep(0.015)

    def error_code(self) -> None:
        """
        读取并输出错误码寄存器内容（调试用途，非正常工作流验证）。

        可能输出的错误类型：
        - Drop Command Error（丢命令错误）
        - 错误码 1/2：通用错误
        - 错误码 3：低功耗模式下中断使用预滤波数据
        - 错误码 6：无头模式下传感器 ODR 不匹配
        - 错误码 7：低功耗模式下使用了预滤波数据
        - Fatal Error（致命错误，NVM 损坏等，仅 POR 可清除）

        Returns:
            None

        Notes:
            - 副作用：读取寄存器后自动清除错误标志（bits 7:4）
            - 非 ISR-safe
        ==========================================
        Read and print error code register (debug only, not for normal verification).

        Possible errors:
        - Drop Command Error
        - Code 1/2: Generic error
        - Code 3: Low-power mode interrupt uses pre-filtered data
        - Code 6: Header-less mode ODR mismatch across sensors
        - Code 7: Pre-filtered data used in low-power mode
        - Fatal Error (NVM corruption, only cleared by POR)

        Returns:
            None

        Notes:
            - Side-effect: Reading clears error flags (bits 7:4)
            - Not ISR-safe
        """
        code_errors = {
            0: "No Error",
            1: "Error",
            2: "Error",
            3: "low-power mode and interrupt uses pre-filtered data",
            6: "ODRs of enabled sensors in header-less mode do not match",
            7: "pre-filtered data are used in low power mode",
        }
        # 读取错误码寄存器
        errors = self._error_code
        # 解析各标志位
        drop_cmd_err = (errors & 0x40) >> 6
        error_codes = (errors & 0x1E) >> 1
        fatal_error = errors & 0x01

        if drop_cmd_err:
            self._log("Drop Command Error")
        if code_errors[error_codes] != "No Error":
            self._log(code_errors[error_codes])
        if fatal_error:
            self._log("Fatal Error")

    @property
    def acceleration_undersample(self) -> str:
        """
        获取加速度计欠采样模式。

        Returns:
            str: 当前模式名称（"NO_UNDERSAMPLE" 或 "UNDERSAMPLE"）

        Notes:
            - ISR-safe: 否（涉及 I2C 读取）
            - 欠采样模式仅用于低功耗模式
        ==========================================
        Get accelerometer undersampling mode.

        Returns:
            str: Current mode ("NO_UNDERSAMPLE" or "UNDERSAMPLE")

        Notes:
            - ISR-safe: No (I2C read involved)
            - Undersampling only applies in low-power mode
        """
        sample_values = ("NO_UNDERSAMPLE", "UNDERSAMPLE")
        return sample_values[self._acc_us]

    @acceleration_undersample.setter
    def acceleration_undersample(self, value: int) -> None:
        """设置加速度计欠采样模式 / Set the accelerometer undersampling mode.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in acc_sample_values:
            raise ValueError("Value must be a valid acceleration undersample value")
        self._acc_us = value

    @property
    def acceleration_bandwidth_parameter(self) -> str:
        """
        获取加速度计带宽参数（滤波器模式或平均模式）。

        Returns:
            str: 当前设置（"FILTER" 或 "AVERAGING"）

        Notes:
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Get accelerometer bandwidth parameter (filter or averaging mode).

        Returns:
            str: Current setting ("FILTER" or "AVERAGING")

        Notes:
            - ISR-safe: No (I2C read involved)
        """
        values = ("FILTER", "AVERAGING")
        return values[self._acc_bwp]

    @acceleration_bandwidth_parameter.setter
    def acceleration_bandwidth_parameter(self, value: int) -> None:
        """设置加速度计带宽参数 / Set the accelerometer bandwidth parameter.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in acc_bandwidth_values:
            raise ValueError("Value must a be a valid Acceleration bandwidth setting")
        self._acc_bwp = value

    @property
    def acceleration_output_data_rate(self) -> str:
        """
        获取加速度计输出数据率（ODR）。
        ODR = 100 / 2^(8 - acc_odr)

        Returns:
            str: 当前 ODR 名称（如 "BANDWIDTH_100"）

        Notes:
            - 启动默认值：100 Hz
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Get accelerometer output data rate (ODR).
        ODR = 100 / 2^(8 - acc_odr)

        Returns:
            str: Current ODR name (e.g. "BANDWIDTH_100")

        Notes:
            - Power-on default: 100 Hz
            - ISR-safe: No (I2C read involved)
        """
        values = {
            BANDWIDTH_25_32: "BANDWIDTH_25_32",
            BANDWIDTH_25_16: "BANDWIDTH_25_16",
            BANDWIDTH_25_8: "BANDWIDTH_25_8",
            BANDWIDTH_25_4: "BANDWIDTH_25_4",
            BANDWIDTH_25_2: "BANDWIDTH_25_2",
            BANDWIDTH_25: "BANDWIDTH_25",
            BANDWIDTH_50: "BANDWIDTH_50",
            BANDWIDTH_100: "BANDWIDTH_100",
            BANDWIDTH_200: "BANDWIDTH_200",
            BANDWIDTH_400: "BANDWIDTH_400",
            BANDWIDTH_800: "BANDWIDTH_800",
            BANDWIDTH_1600: "BANDWIDTH_1600",
            BANDWIDTH_3200: "BANDWIDTH_3200",
        }
        return values[self._acc_odr]

    @acceleration_output_data_rate.setter
    def acceleration_output_data_rate(self, value: int) -> None:
        """设置加速度计输出数据率 / Set the accelerometer output data rate.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in bandwidth_values:
            raise ValueError("Value must be a valid Acceleration Data Rate setting")
        self._acc_odr = value

    @property
    def acceleration_range(self) -> str:
        """
        获取加速度计量程。

        Returns:
            str: 当前量程名称（"ACCEL_RANGE_2G" / "4G" / "8G" / "16G"）

        Notes:
            - 修改量程不会清除数据就绪位，建议改后读一次数据寄存器
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Get accelerometer range.

        Returns:
            str: Current range name ("ACCEL_RANGE_2G" / "4G" / "8G" / "16G")

        Notes:
            - Changing range does not clear data-ready bit; read data after change
            - ISR-safe: No (I2C read involved)
        """
        values = {
            3: "ACCEL_RANGE_2G",
            5: "ACCEL_RANGE_4G",
            8: "ACCEL_RANGE_8G",
            12: "ACCEL_RANGE_16G",
        }
        return values[self._acc_range]

    @acceleration_range.setter
    def acceleration_range(self, value: int) -> None:
        """设置加速度计量程 / Set the accelerometer measurement range.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in acc_range_values:
            raise ValueError("Value must be a valid Acceleration Range setting")
        self._acc_range = value

    @property
    def acceleration(self) -> tuple:
        """
        读取三轴加速度值（m/s²）。

        Returns:
            tuple: (acc_x, acc_y, acc_z) 三轴加速度，单位 m/s²

        Notes:
            - 根据当前量程自动选择分辨率进行转换
            - ISR-safe: 否（涉及多次 I2C 读取）
            - 副作用：读取数据寄存器（地址 0x12~0x17）
        ==========================================
        Read 3-axis acceleration (m/s²).

        Returns:
            tuple: (acc_x, acc_y, acc_z) acceleration in m/s²

        Notes:
            - Resolution auto-selected based on current range setting
            - ISR-safe: No (multiple I2C reads)
            - Side-effect: Reads data registers (0x12~0x17)
        """
        # 根据当前量程获取 LSB/g 分辨率因子，并转换为 m/s²
        factor = self.acceleration_scale[self.acceleration_range] / _ACC_CONVERSION
        # 读取三轴原始值并转换为物理单位
        x = self._acc_data_x / factor
        y = self._acc_data_y / factor
        z = self._acc_data_z / factor
        return x, y, z

    def power_mode_status(self) -> None:
        """
        读取并输出电源模式状态（调试用途）。

        输出加速度计、陀螺仪、磁力计的当前电源状态。

        Returns:
            None

        Notes:
            - 副作用：仅读取状态寄存器，无写入操作
            - 非 ISR-safe
        ==========================================
        Read and print power mode status (debug only).

        Prints current power state of accelerometer, gyroscope, and magnetometer.

        Returns:
            None

        Notes:
            - Side-effect: Read-only, no writes
            - Not ISR-safe
        """
        # 读取 PMU_STATUS 寄存器 (0x03)
        values = self._power_mode
        # 解析各传感器电源状态位
        acc_pmu_status = (values & 0x18) >> 4
        gyr_pmu_status = (values & 0xC) >> 2
        mag_pmu_status = values & 0x03

        acc_pmu_codes = {0: "Suspend", 1: "Normal", 2: "Low Power"}
        gyr_pmu_codes = {0: "Suspend", 1: "Normal", 3: "Fast Start - Up"}
        mag_pmu_codes = {0: "Suspend", 1: "Normal", 2: "Low Power"}

        self._log("Acceleration Power Mode: %s" % acc_pmu_codes[acc_pmu_status])
        self._log("Gyro Power Mode: %s" % gyr_pmu_codes[gyr_pmu_status])
        self._log("Mag Power Mode: %s" % mag_pmu_codes[mag_pmu_status])

    def acc_power_mode(self, value: int) -> None:
        """
        设置加速度计电源模式。

        Args:
            value (int): 电源模式（ACC_POWER_SUSPEND / ACC_POWER_NORMAL / ACC_POWER_LOWPOWER）

        Returns:
            None

        Raises:
            ValueError: 参数值不在有效范围内

        Notes:
            - 副作用：向 CMD 寄存器 (0x7E) 写入命令，10ms 延时等待生效
            - 非 ISR-safe
        ==========================================
        Set accelerometer power mode.

        Args:
            value (int): Power mode (ACC_POWER_SUSPEND / ACC_POWER_NORMAL / ACC_POWER_LOWPOWER)

        Returns:
            None

        Raises:
            ValueError: Value not in valid range

        Notes:
            - Side-effect: Writes command to CMD register (0x7E), 10ms settling delay
            - Not ISR-safe
        """
        if value not in acc_power_mode_values:
            raise ValueError("Value must be a valid Acceleration Power Mode Setting")
        # 通过 CMD 寄存器写入电源模式命令
        self._read = value
        time.sleep(0.1)

    @property
    def temperature(self) -> float:
        """
        读取温度值。

        Returns:
            float: 温度值（℃）

        Notes:
            - 分辨率：1/2^9 K/LSB，基准偏移 +23°C
            - 温度仅在陀螺仪正常模式下有效更新（每 10ms），否则每 1.28s 更新
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Read temperature.

        Returns:
            float: Temperature in Celsius

        Notes:
            - Resolution: 1/2^9 K/LSB, offset +23°C
            - Valid update rate: 10ms when gyro in normal mode, otherwise 1.28s
            - ISR-safe: No (I2C read involved)
        """
        # 温度原始值为 16 位有符号整数，转换为摄氏度
        return (self._temp_data * 1 / 2**9) + 23

    @property
    def gyro(self) -> tuple:
        """
        读取三轴陀螺仪角速度值。

        Returns:
            tuple: (gyro_x, gyro_y, gyro_z) 三轴角速度，单位 °/s

        Notes:
            - 根据当前量程自动选择分辨率进行转换
            - ISR-safe: 否（涉及多次 I2C 读取）
            - 副作用：读取数据寄存器（地址 0x0C~0x11）
        ==========================================
        Read 3-axis gyroscope angular velocity.

        Returns:
            tuple: (gyro_x, gyro_y, gyro_z) angular velocity in °/s

        Notes:
            - Resolution auto-selected based on current range
            - ISR-safe: No (multiple I2C reads)
            - Side-effect: Reads data registers (0x0C~0x11)
        """
        # 根据当前量程获取 LSB/(°/s) 分辨率因子
        factor = self.gyro_scale[self.gyro_range]
        # 读取三轴原始值并转换为物理单位
        x = self._gyro_data_x / factor
        y = self._gyro_data_y / factor
        z = self._gyro_data_z / factor
        return x, y, z

    @property
    def gyro_output_data_rate(self) -> str:
        """
        获取陀螺仪输出数据率（ODR）。
        ODR = 100 / 2^(8 - gyro_odr)

        Returns:
            str: 当前 ODR 名称（如 "BANDWIDTH_100"）

        Notes:
            - 启动默认值：100 Hz
            - 低于 25 Hz 的 ODR 不合法，会导致错误码
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Get gyroscope output data rate (ODR).
        ODR = 100 / 2^(8 - gyro_odr)

        Returns:
            str: Current ODR name (e.g. "BANDWIDTH_100")

        Notes:
            - Power-on default: 100 Hz
            - ODR below 25 Hz is illegal and will set error code
            - ISR-safe: No (I2C read involved)
        """
        values = {
            BANDWIDTH_25: "BANDWIDTH_25",
            BANDWIDTH_50: "BANDWIDTH_50",
            BANDWIDTH_100: "BANDWIDTH_100",
            BANDWIDTH_200: "BANDWIDTH_200",
            BANDWIDTH_400: "BANDWIDTH_400",
            BANDWIDTH_800: "BANDWIDTH_800",
            BANDWIDTH_1600: "BANDWIDTH_1600",
            BANDWIDTH_3200: "BANDWIDTH_3200",
        }
        return values[self._gyro_odr]

    @gyro_output_data_rate.setter
    def gyro_output_data_rate(self, value: int) -> None:
        """设置陀螺仪输出数据率 / Set the gyroscope output data rate.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in gyro_bandwidth_values:
            raise ValueError("Value must be a valid Gyro Data Rate setting")
        self._gyro_odr = value

    @property
    def gyro_bandwidth_parameter(self) -> str:
        """
        获取陀螺仪带宽参数（滤波器模式）。

        Returns:
            str: 当前设置（"GYRO_OSR4" / "GYRO_OSR2" / "GYRO_NORMAL"）

        Notes:
            - GYRO_NORMAL: 正常滤波器模式
            - GYRO_OSR2: 2倍过采样，带宽约为正常模式的一半
            - GYRO_OSR4: 4倍过采样，带宽约为正常模式的四分之一
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Get gyroscope bandwidth parameter (filter mode).

        Returns:
            str: Current setting ("GYRO_OSR4" / "GYRO_OSR2" / "GYRO_NORMAL")

        Notes:
            - GYRO_NORMAL: Standard filter mode
            - GYRO_OSR2: 2x oversampling, ~half bandwidth
            - GYRO_OSR4: 4x oversampling, ~quarter bandwidth
            - ISR-safe: No (I2C read involved)
        """
        values = ("GYRO_OSR4", "GYRO_OSR2", "GYRO_NORMAL")
        return values[self._gyro_bwp]

    @gyro_bandwidth_parameter.setter
    def gyro_bandwidth_parameter(self, value: int) -> None:
        """设置陀螺仪带宽参数 / Set the gyroscope bandwidth parameter.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in gyro_cutoffs_values:
            raise ValueError("Value must be a valid Gyro Bandwidth setting")
        self._gyro_bwp = value

    @property
    def gyro_power_mode(self) -> str:
        """
        获取陀螺仪电源模式。

        Returns:
            str: 当前模式名称（"GYRO_POWER_SUSPEND" / "GYRO_POWER_NORMAL" / "GYRO_POWER_FASTSTARTUP"）

        Notes:
            - 通过读取 CMD 寄存器 (0x7E) 获取当前模式
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Get gyroscope power mode.

        Returns:
            str: Current mode ("GYRO_POWER_SUSPEND" / "GYRO_POWER_NORMAL" / "GYRO_POWER_FASTSTARTUP")

        Notes:
            - Reads CMD register (0x7E) for current mode
            - ISR-safe: No (I2C read involved)
        """
        g_power_modes = {
            0: "GYRO_POWER_SUSPEND",
            1: "GYRO_POWER_NORMAL",
            3: "GYRO_POWER_FASTSTARTUP",
        }
        return g_power_modes[(self._power_mode >> 2) & 0x03]

    @gyro_power_mode.setter
    def gyro_power_mode(self, value: int) -> None:
        """设置陀螺仪电源模式 / Set the gyroscope power mode.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in gyro_power_modes:
            raise ValueError("Value must be a valid Gyro Power Mode")
        # 通过 CMD 寄存器写入电源模式命令
        self._read = value
        time.sleep(0.1)

    @property
    def gyro_range(self) -> str:
        """
        获取陀螺仪量程。

        Returns:
            str: 当前量程名称（"GYRO_RANGE_125" ~ "GYRO_RANGE_2000"）

        Notes:
            - 修改量程不会清除数据就绪位，建议改后读一次数据寄存器
            - ISR-safe: 否（涉及 I2C 读取）
        ==========================================
        Get gyroscope range.

        Returns:
            str: Current range ("GYRO_RANGE_125" ~ "GYRO_RANGE_2000")

        Notes:
            - Changing range does not clear data-ready bit; read data after change
            - ISR-safe: No (I2C read involved)
        """
        g_values = {
            GYRO_RANGE_2000: "GYRO_RANGE_2000",
            GYRO_RANGE_1000: "GYRO_RANGE_1000",
            GYRO_RANGE_500: "GYRO_RANGE_500",
            GYRO_RANGE_250: "GYRO_RANGE_250",
            GYRO_RANGE_125: "GYRO_RANGE_125",
        }
        return g_values[self._gyro_range]

    @gyro_range.setter
    def gyro_range(self, value: int) -> None:
        """设置陀螺仪量程 / Set the gyroscope measurement range.

        Args:
            value (int): 支持的配置值 / A supported configuration value.

        Raises:
            ValueError: 当配置值无效时 / If the value is invalid.
        """
        if value not in gyro_values:
            raise ValueError("Value must be a valid Gyro range")
        self._gyro_range = value

    def deinit(self) -> None:
        """
        释放传感器资源，将加速度计和陀螺仪置为挂起模式。

        Returns:
            None

        Notes:
            - 将加速度计和陀螺仪均设为 SUSPEND 模式以降低功耗
            - 不释放 I2C 总线（总线由调用方管理）
            - ISR-safe: 否
        ==========================================
        Release sensor resources, suspend both accelerometer and gyroscope.

        Returns:
            None

        Notes:
            - Sets both accelerometer and gyroscope to SUSPEND mode
            - Does not release I2C bus (managed by caller)
            - ISR-safe: No
        """
        # 将加速度计和陀螺仪均设为挂起模式以降低功耗
        self._read = ACC_POWER_SUSPEND
        time.sleep(0.1)
        self._read = GYRO_POWER_SUSPEND
        time.sleep(0.1)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
