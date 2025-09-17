# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 上午10:39
# @Author  : 缪贵成
# @File    : vl53l0x.py
# @Description : 基于vl53l0x的激光测距模块驱动文件
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
import struct
import time

# ======================================== 全局变量 ============================================

# 超时配置和启动相关配置
_IO_TIMEOUT = 1000
_SYSRANGE_START = const(0x00)
_EXTSUP_HV = const(0x89)
_MSRC_CONFIG = const(0x60)
_FINAL_RATE_RTN_LIMIT = const(0x44)
_SYSTEM_SEQUENCE = const(0x01)
_SPAD_REF_START = const(0x4f)
_SPAD_ENABLES = const(0xb0)
_REF_EN_START_SELECT = const(0xb6)
_SPAD_NUM_REQUESTED = const(0x4e)
_INTERRUPT_GPIO = const(0x0a)
_INTERRUPT_CLEAR = const(0x0b)
_GPIO_MUX_ACTIVE_HIGH = const(0x84)
_RESULT_INTERRUPT_STATUS = const(0x13)
_RESULT_RANGE_STATUS = const(0x14)
_OSC_CALIBRATE = const(0xf8)
_MEASURE_PERIOD = const(0x04)

SYSRANGE_START = 0x00

SYSTEM_THRESH_HIGH = 0x0C
SYSTEM_THRESH_LOW = 0x0E

SYSTEM_SEQUENCE_CONFIG = 0x01
SYSTEM_RANGE_CONFIG = 0x09
SYSTEM_INTERMEASUREMENT_PERIOD = 0x04

SYSTEM_INTERRUPT_CONFIG_GPIO = 0x0A

GPIO_HV_MUX_ACTIVE_HIGH = 0x84

SYSTEM_INTERRUPT_CLEAR = 0x0B

RESULT_INTERRUPT_STATUS = 0x13
RESULT_RANGE_STATUS = 0x14

RESULT_CORE_AMBIENT_WINDOW_EVENTS_RTN = 0xBC
RESULT_CORE_RANGING_TOTAL_EVENTS_RTN = 0xC0
RESULT_CORE_AMBIENT_WINDOW_EVENTS_REF = 0xD0
RESULT_CORE_RANGING_TOTAL_EVENTS_REF = 0xD4
RESULT_PEAK_SIGNAL_RATE_REF = 0xB6

ALGO_PART_TO_PART_RANGE_OFFSET_MM = 0x28

I2C_SLAVE_DEVICE_ADDRESS = 0x8A

MSRC_CONFIG_CONTROL = 0x60

PRE_RANGE_CONFIG_MIN_SNR = 0x27
PRE_RANGE_CONFIG_VALID_PHASE_LOW = 0x56
PRE_RANGE_CONFIG_VALID_PHASE_HIGH = 0x57
PRE_RANGE_MIN_COUNT_RATE_RTN_LIMIT = 0x64

FINAL_RANGE_CONFIG_MIN_SNR = 0x67
FINAL_RANGE_CONFIG_VALID_PHASE_LOW = 0x47
FINAL_RANGE_CONFIG_VALID_PHASE_HIGH = 0x48
FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT = 0x44

PRE_RANGE_CONFIG_SIGMA_THRESH_HI = 0x61
PRE_RANGE_CONFIG_SIGMA_THRESH_LO = 0x62

PRE_RANGE_CONFIG_VCSEL_PERIOD = 0x50
PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI = 0x51
PRE_RANGE_CONFIG_TIMEOUT_MACROP_LO = 0x52

SYSTEM_HISTOGRAM_BIN = 0x81
HISTOGRAM_CONFIG_INITIAL_PHASE_SELECT = 0x33
HISTOGRAM_CONFIG_READOUT_CTRL = 0x55

FINAL_RANGE_CONFIG_VCSEL_PERIOD = 0x70
FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI = 0x71
FINAL_RANGE_CONFIG_TIMEOUT_MACROP_LO = 0x72
CROSSTALK_COMPENSATION_PEAK_RATE_MCPS = 0x20

MSRC_CONFIG_TIMEOUT_MACROP = 0x46
#软件复位相关
SOFT_RESET_GO2_SOFT_RESET_N = 0xBF
IDENTIFICATION_MODEL_ID = 0xC0
IDENTIFICATION_REVISION_ID = 0xC2

OSC_CALIBRATE_VAL = 0xF8

GLOBAL_CONFIG_VCSEL_WIDTH = 0x32
GLOBAL_CONFIG_SPAD_ENABLES_REF_0 = 0xB0
GLOBAL_CONFIG_SPAD_ENABLES_REF_1 = 0xB1
GLOBAL_CONFIG_SPAD_ENABLES_REF_2 = 0xB2
GLOBAL_CONFIG_SPAD_ENABLES_REF_3 = 0xB3
GLOBAL_CONFIG_SPAD_ENABLES_REF_4 = 0xB4
GLOBAL_CONFIG_SPAD_ENABLES_REF_5 = 0xB5

GLOBAL_CONFIG_REF_EN_START_SELECT = 0xB6
DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD = 0x4E
DYNAMIC_SPAD_REF_EN_START_OFFSET = 0x4F
POWER_MANAGEMENT_GO1_POWER_FORCE = 0x80

VHV_CONFIG_PAD_SCL_SDA__EXTSUP_HV = 0x89

ALGO_PHASECAL_LIM = 0x30
ALGO_PHASECAL_CONFIG_TIMEOUT = 0x30

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class VL53L0X:
    """
    该类控制VL53L0X激光测距传感器，提供初始化、测距和参数配置功能。

    Attributes:
        i2c (I2C): machine.I2C实例用于I2C总线通信。
        address (int): VL53L0X的I2C地址，默认0x29。
        _started (bool): 指示传感器是否已启动测距。
        measurement_timing_budget_us (int): 测量时间预算（微秒）。
        enables (dict): 序列步骤使能状态，包含tcc、dss、msrc、pre_range、final_range。
        timeouts (dict): 各阶段超时参数，包含多种超时相关配置。
        vcsel_period_type (list): VCSEL周期类型列表，包含"VcselPeriodPreRange"和"VcselPeriodFinalRange"。
        _stop_variable (int): 用于停止操作的内部变量。

    Methods:
        __init__(i2c, address=0x29) -> None: 初始化VL53L0X传感器实例。
        init(power2v8=True) -> None: 初始化传感器硬件配置。
        start(period=0) -> None: 启动传感器测距，支持周期性测量。
        stop() -> None: 停止传感器测距。
        read() -> int: 读取当前测距结果（毫米）。
        set_signal_rate_limit(limit_Mcps) -> bool: 设置信号速率限制。
        decode_Vcsel_period(reg_val) -> int: 解码VCSEL周期寄存器值。
        encode_Vcsel_period(period_pclks) -> int: 编码VCSEL周期为寄存器值。
        set_Vcsel_pulse_period(type, period_pclks) -> bool: 设置VCSEL脉冲周期。
        get_sequence_step_enables() -> None: 获取序列步骤使能状态。
        get_vcsel_pulse_period(type) -> int: 获取VCSEL脉冲周期。
        get_sequence_step_timeouts() -> None: 获取序列步骤超时参数。
        timeout_Mclks_to_microseconds(timeout_period_mclks, vcsel_period_pclks) -> float: 将Mclks超时转换为微秒。
        timeout_microseconds_to_Mclks(timeout_period_us, vcsel_period_pclks) -> float: 将微秒超时转换为Mclks。
        calc_macro_period(vcsel_period_pclks) -> float: 计算宏周期（纳秒）。
        decode_timeout(reg_val) -> int: 解码超时寄存器值。
        encode_timeout(timeout_mclks) -> int: 编码超时值为寄存器格式。
        set_measurement_timing_budget(budget_us) -> bool: 设置测量时间预算。
        perform_single_ref_calibration(vhv_init_byte) -> bool: 执行单次参考校准。

    Notes:
        - 该类依赖I2C通信，所有涉及I2C操作的方法非ISR-safe。
        - 初始化时会进行传感器硬件配置和校准，确保传感器正常工作。
        - 测量结果以毫米为单位，超出量程时可能返回无效值。

    ==========================================

    This class controls the VL53L0X laser ranging sensor, providing initialization, ranging and parameter configuration functions.

    Attributes:
        i2c (I2C): machine.I2C instance for I2C bus communication.
        address (int): I2C address of VL53L0X, default is 0x29.
        _started (bool): Indicates whether the sensor has started ranging.
        measurement_timing_budget_us (int): Measurement timing budget in microseconds.
        enables (dict): Sequence step enable status, including tcc, dss, msrc, pre_range, final_range.
        timeouts (dict): Timeout parameters for each stage, including various timeout-related configurations.
        vcsel_period_type (list): List of VCSEL period types, including "VcselPeriodPreRange" and "VcselPeriodFinalRange".
        _stop_variable (int): Internal variable used for stop operation.

    Methods:
        init(i2c, address=0x29) -> None: Initialize VL53L0X sensor instance.
        init(power2v8=True) -> None: Initialize sensor hardware configuration.
        start(period=0) -> None: Start sensor ranging, supporting periodic measurement.
        stop() -> None: Stop sensor ranging.
        read() -> int: Read current ranging result (in millimeters).
        set_signal_rate_limit(limit_Mcps) -> bool: Set signal rate limit.
        decode_Vcsel_period(reg_val) -> int: Decode VCSEL period register value.
        encode_Vcsel_period(period_pclks) -> int: Encode VCSEL period to register value.
        set_Vcsel_pulse_period(type, period_pclks) -> bool: Set VCSEL pulse period.
        get_sequence_step_enables() -> None: Get sequence step enable status.
        get_vcsel_pulse_period(type) -> int: Get VCSEL pulse period.
        get_sequence_step_timeouts() -> None: Get sequence step timeout parameters.
        timeout_Mclks_to_microseconds(timeout_period_mclks, vcsel_period_pclks) -> float: Convert timeout from Mclks to microseconds.
        timeout_microseconds_to_Mclks(timeout_period_us, vcsel_period_pclks) -> float: Convert timeout from microseconds to Mclks.
        calc_macro_period(vcsel_period_pclks) -> float: Calculate macro period (in nanoseconds).
        decode_timeout(reg_val) -> int: Decode timeout register value.
        encode_timeout(timeout_mclks) -> int: Encode timeout value to register format.
        set_measurement_timing_budget(budget_us) -> bool: Set measurement timing budget.
        perform_single_ref_calibration(vhv_init_byte) -> bool: Perform single reference calibration.


    Notes:
        - This class relies on I2C communication, all methods involving I2C operations are not ISR-safe.
        - Sensor hardware configuration and calibration are performed during initialization to ensure proper operation.
        - Measurement results are in millimeters, invalid values may be returned when out of range.
    """
    # 默认i2c地址0x29，部分手册描述0x52,根据实际情况进行修改
    def __init__(self, i2c, address=0x29):
        """
        初始化VL53L0X传感器实例。

        Args:
            i2c (I2C): machine.I2C实例，用于与传感器通信。
            address (int): 传感器的I2C地址，默认值为0x29。

        Raises:
            TypeError: 如果i2c不是machine.I2C实例。
            ValueError: 如果I2C地址不是整数或不在0x00到0x7F的范围内。

        Notes:
            初始化过程会调用init()方法进行硬件配置。

        ==========================================

        Initialize VL53L0X sensor instance.

        Args:
            i2c (I2C): machine.I2C instance for communication with the sensor.
            address (int): I2C address of the sensor, default is 0x29.

        Raises:
            TypeError: "i2c must be a machine.I2C instance."
            ValueError: If the I2C address is not an integer or not within the range of 0x00 to 0x7F.

        Notes:
            The initialization process will call the init() method for hardware configuration.
        """
        # 检查 i2c 参数是否为有效的 machine.I2C 实例
        if not hasattr(i2c, 'readfrom_mem') or not hasattr(i2c, 'writeto_mem'):
            raise TypeError("i2c must be a valid machine.I2C  instance")
        
        # 检查 address 是否为合法的 I2C 地址
        if not isinstance(address, int) or address < 0x00 or address > 0x7F:
            raise ValueError(" The I2C address must be an integer and within the range of 0x00 to 0x7F.")
        
        self.i2c = i2c
        self.address = address
        self.init()
        self._started = False
        self.measurement_timing_budget_us = 0
        self.set_measurement_timing_budget(self.measurement_timing_budget_us)
        self.enables = {"tcc": 0,
                        "dss": 0,
                        "msrc": 0,
                        "pre_range": 0,
                        "final_range": 0}
        self.timeouts = {"pre_range_vcsel_period_pclks": 0,
                         "msrc_dss_tcc_mclks": 0,
                         "msrc_dss_tcc_us": 0,
                         "pre_range_mclks": 0,
                         "pre_range_us": 0,
                         "final_range_vcsel_period_pclks": 0,
                         "final_range_mclks": 0,
                         "final_range_us": 0
                         }
        self.vcsel_period_type = ["VcselPeriodPreRange", "VcselPeriodFinalRange"]

    def _registers(self, register, values=None, _struct='B') -> tuple:
        """
        读写传感器寄存器（内部方法）。

        Args:
            register (int): 寄存器地址。
            values (tuple, optional): 要写入的值，为None时执行读取操作。
            _struct (str, optional): 用于打包/解包数据的格式字符串，默认'B'。

        Returns:
            tuple: 读取时返回解包后的值；写入时无返回。

        Notes:
            内部使用的寄存器操作方法，不建议直接调用。

        ==========================================

        Read/write sensor registers (internal method).

        Args:
            register (int): Register address.
            values (tuple, optional): Values to write, perform read operation when None.
            _struct (str, optional): Format string for packing/unpacking data, default 'B'.

        Returns:
            tuple: Unpacked values when reading; no return when writing.

        Notes:
            Internal register operation method, not recommended for direct call.
        """
        if values is None:
            size = struct.calcsize(_struct)
            data = self.i2c.readfrom_mem(self.address, register, size)
            values = struct.unpack(_struct, data)
            return values
        data = struct.pack(_struct, *values)
        self.i2c.writeto_mem(self.address, register, data)

    def _register(self, register, value=None, _struct='B') -> int:
        """
        读写单个传感器寄存器（内部方法）。

        Args:
            register (int): 寄存器地址。
            value (int, optional): 要写入的值，为None时执行读取操作。
            _struct (str, optional): 用于打包/解包数据的格式字符串，默认'B'。

        Returns:
            int: 读取时返回寄存器值；写入时无返回。

        Notes:
            内部使用的寄存器操作方法，不建议直接调用。

        ==========================================

        Read/write single sensor register (internal method).

        Args:
            register (int): Register address.
            value (int, optional): Value to write, perform read operation when None.
            _struct (str, optional): Format string for packing/unpacking data, default 'B'.

        Returns:
            int: Register value when reading; no return when writing.

        Notes:
            Internal register operation method, not recommended for direct call.
        """
        if value is None:
            return self._registers(register, _struct=_struct)[0]
        self._registers(register, (value,), _struct=_struct)

    def _flag(self, register=0x00, bit=0, value=None) -> bool:
        """
        操作寄存器的特定位（内部方法）。

        Args:
            register (int, optional): 寄存器地址，默认0x00。
            bit (int, optional): 要操作的位，默认0。
            value (bool, optional): 要设置的值，为None时读取位状态。

        Returns:
            bool: 当value为None时返回位状态；设置时无返回。

        Notes:
            内部使用的位操作方法，用于设置或检查寄存器的特定位。

        ==========================================

        Manipulate specific bit of register (internal method).

        Args:
            register (int, optional): Register address, default 0x00.
            bit (int, optional): Bit to manipulate, default 0.
            value (bool, optional): Value to set, read bit status when None.

        Returns:
            bool: Bit status when value is None; no return when setting.

        Notes:
            Internal bit operation method for setting or checking specific bits of registers.
        """
        data = self._register(register)
        mask = 1 << bit
        if value is None:
            return bool(data & mask)
        elif value:
            data |= mask
        else:
            data &= ~mask
        self._register(register, data)

    def _config(self, *config):
        """
        批量配置寄存器（内部方法）。

        Args:
            *config: 可变参数，每个元素为(register, value)元组，表示寄存器地址和值。

        Notes:
            用于一次性配置多个寄存器，提高初始化效率。

        ==========================================

        Batch configure registers (internal method).

        Args:
            *config: Variable parameters, each element is a (register, value) tuple representing register address and value.

        Notes:
            Used to configure multiple registers at once to improve initialization efficiency.
        """
        for register, value in config:
            self._register(register, value)

    def init(self, power2v8=True):
        """
        初始化传感器硬件配置。

        Args:
            power2v8 (bool, optional): 是否使用2.8V电源，默认True。

        Notes:
            执行传感器硬件复位、SPAD配置和校准等初始化操作。

        ==========================================

        Initialize sensor hardware configuration.

        Args:
            power2v8 (bool, optional): Whether to use 2.8V power supply, default True.

        Notes:
            Performs sensor hardware reset, SPAD configuration and calibration.
        """
        self._flag(_EXTSUP_HV, 0, power2v8)

        # I2C standard mode
        self._config(
            (0x88, 0x00),

            (0x80, 0x01),
            (0xff, 0x01),
            (0x00, 0x00),
        )
        self._stop_variable = self._register(0x91)
        self._config(
            (0x00, 0x01),
            (0xff, 0x00),
            (0x80, 0x00),
        )

        # disable signal_rate_msrc and signal_rate_pre_range limit checks
        self._flag(_MSRC_CONFIG, 1, True)
        self._flag(_MSRC_CONFIG, 4, True)

        # rate_limit = 0.25
        self._register(_FINAL_RATE_RTN_LIMIT, int(0.1 * (1 << 7)),
                       _struct='>H')

        self._register(_SYSTEM_SEQUENCE, 0xff)

        spad_count, is_aperture = self._spad_info()
        spad_map = bytearray(self._registers(_SPAD_ENABLES, _struct='6B'))

        # set reference spads
        self._config(
            (0xff, 0x01),
            (_SPAD_REF_START, 0x00),
            (_SPAD_NUM_REQUESTED, 0x2c),
            (0xff, 0x00),
            (_REF_EN_START_SELECT, 0xb4),
        )

        spads_enabled = 0
        for i in range(48):
            if i < 12 and is_aperture or spads_enabled >= spad_count:
                spad_map[i // 8] &= ~(1 << (i >> 2))
            elif spad_map[i // 8] & (1 << (i >> 2)):
                spads_enabled += 1

        self._registers(_SPAD_ENABLES, spad_map, _struct='6B')

        self._config(
            (0xff, 0x01),
            (0x00, 0x00),

            (0xff, 0x00),
            (0x09, 0x00),
            (0x10, 0x00),
            (0x11, 0x00),

            (0x24, 0x01),
            (0x25, 0xFF),
            (0x75, 0x00),

            (0xFF, 0x01),
            (0x4E, 0x2C),
            (0x48, 0x00),
            (0x30, 0x20),

            (0xFF, 0x00),
            (0x30, 0x09),
            (0x54, 0x00),
            (0x31, 0x04),
            (0x32, 0x03),
            (0x40, 0x83),
            (0x46, 0x25),
            (0x60, 0x00),
            (0x27, 0x00),
            (0x50, 0x06),
            (0x51, 0x00),
            (0x52, 0x96),
            (0x56, 0x08),
            (0x57, 0x30),
            (0x61, 0x00),
            (0x62, 0x00),
            (0x64, 0x00),
            (0x65, 0x00),
            (0x66, 0xA0),

            (0xFF, 0x01),
            (0x22, 0x32),
            (0x47, 0x14),
            (0x49, 0xFF),
            (0x4A, 0x00),

            (0xFF, 0x00),
            (0x7A, 0x0A),
            (0x7B, 0x00),
            (0x78, 0x21),

            (0xFF, 0x01),
            (0x23, 0x34),
            (0x42, 0x00),
            (0x44, 0xFF),
            (0x45, 0x26),
            (0x46, 0x05),
            (0x40, 0x40),
            (0x0E, 0x06),
            (0x20, 0x1A),
            (0x43, 0x40),

            (0xFF, 0x00),
            (0x34, 0x03),
            (0x35, 0x44),

            (0xFF, 0x01),
            (0x31, 0x04),
            (0x4B, 0x09),
            (0x4C, 0x05),
            (0x4D, 0x04),

            (0xFF, 0x00),
            (0x44, 0x00),
            (0x45, 0x20),
            (0x47, 0x08),
            (0x48, 0x28),
            (0x67, 0x00),
            (0x70, 0x04),
            (0x71, 0x01),
            (0x72, 0xFE),
            (0x76, 0x00),
            (0x77, 0x00),

            (0xFF, 0x01),
            (0x0D, 0x01),

            (0xFF, 0x00),
            (0x80, 0x01),
            (0x01, 0xF8),

            (0xFF, 0x01),
            (0x8E, 0x01),
            (0x00, 0x01),
            (0xFF, 0x00),
            (0x80, 0x00),
        )

        self._register(_INTERRUPT_GPIO, 0x04)
        self._flag(_GPIO_MUX_ACTIVE_HIGH, 4, False)
        self._register(_INTERRUPT_CLEAR, 0x01)

        # XXX Need to implement this.
        # budget = self._timing_budget()
        # self._register(_SYSTEM_SEQUENCE, 0xe8)
        # self._timing_budget(budget)

        self._register(_SYSTEM_SEQUENCE, 0x01)
        self._calibrate(0x40)
        self._register(_SYSTEM_SEQUENCE, 0x02)
        self._calibrate(0x00)

        self._register(_SYSTEM_SEQUENCE, 0xe8)

    def _spad_info(self) -> tuple:
        """
        获取SPAD（单光子雪崩二极管）信息（内部方法）。

        Returns:
            tuple: (count, is_aperture)，SPAD数量和是否为孔径类型。

        Raises:
            RuntimeError: 获取SPAD信息超时。

        Notes:
            用于初始化过程中配置SPAD参数。

        ==========================================

        Get SPAD (Single Photon Avalanche Diode) information (internal method).

        Returns:
            tuple: (count, is_aperture), SPAD count and whether it is aperture type.

        Raises:
            RuntimeError: Timeout when getting SPAD information.

        Notes:
            Used to configure SPAD parameters during initialization.
        """
        self._config(
            (0x80, 0x01),
            (0xff, 0x01),
            (0x00, 0x00),

            (0xff, 0x06),
        )
        self._flag(0x83, 3, True)
        self._config(
            (0xff, 0x07),
            (0x81, 0x01),

            (0x80, 0x01),

            (0x94, 0x6b),
            (0x83, 0x00),
        )
        for timeout in range(_IO_TIMEOUT):
            if self._register(0x83):
                break
            time.sleep_ms(1)
        else:
            raise RuntimeError("Timeout")
        self._config(
            (0x83, 0x01),
        )
        value = self._register(0x92)
        self._config(
            (0x81, 0x00),
            (0xff, 0x06),
        )
        self._flag(0x83, 3, False)
        self._config(
            (0xff, 0x01),
            (0x00, 0x01),

            (0xff, 0x00),
            (0x80, 0x00),
        )
        count = value & 0x7f
        is_aperture = bool(value & 0b10000000)
        return count, is_aperture

    def _calibrate(self, vhv_init_byte):
        """
        执行传感器校准（内部方法）。

        Args:
            vhv_init_byte (int): VHV初始化字节参数。

        Raises:
            RuntimeError: 校准超时。

        Notes:
            用于传感器初始化过程中的校准操作。

        ==========================================

        Perform sensor calibration (internal method).

        Args:
            vhv_init_byte (int): VHV initialization byte parameter.

        Raises:
            RuntimeError: Calibration timeout.

        Notes:
            Used for calibration during sensor initialization.
        """
        self._register(_SYSRANGE_START, 0x01 | vhv_init_byte)
        for timeout in range(_IO_TIMEOUT):
            if self._register(_RESULT_INTERRUPT_STATUS) & 0x07:
                break
            time.sleep_ms(1)
        else:
            raise RuntimeError("timeout")
        self._register(_INTERRUPT_CLEAR, 0x01)
        self._register(_SYSRANGE_START, 0x00)

    def start(self, period=0):
        """
        启动传感器测距功能。

        Args:
            period (int, optional): 周期性测量的周期（毫秒），0表示单次测量模式。

        Notes:
            启动后传感器将开始测距，可通过read()方法获取测量结果。

        ==========================================

        Start sensor ranging function.

        Args:
            period (int, optional): Period for periodic measurement in milliseconds, 0 for single measurement mode.

        Notes:
            After starting, the sensor will begin ranging, and results can be obtained via read() method.
        """
        self._config(
            (0x80, 0x01),
            (0xFF, 0x01),
            (0x00, 0x00),
            (0x91, self._stop_variable),
            (0x00, 0x01),
            (0xFF, 0x00),
            (0x80, 0x00),
        )
        if period:
            oscilator = self._register(_OSC_CALIBRATE, _struct='>H')
            if oscilator:
                period *= oscilator
            self._register(_MEASURE_PERIOD, period, _struct='>H')
            self._register(_SYSRANGE_START, 0x04)
        else:
            self._register(_SYSRANGE_START, 0x02)
        self._started = True

    def stop(self):
        """
        停止传感器测距功能。

        Notes:
            停止后传感器将不再进行测距操作，节省功耗。

        ==========================================

        Stop sensor ranging function.

        Notes:
            After stopping, the sensor will no longer perform ranging operations to save power.
        """
        self._register(_SYSRANGE_START, 0x01)
        self._config(
            (0xFF, 0x01),
            (0x00, 0x00),
            (0x91, self._stop_variable),
            (0x00, 0x01),
            (0xFF, 0x00),
        )
        self._started = False

    def read(self):
        """
        读取当前测距结果。

        Returns:
            int: 测距结果，单位为毫米（mm）。

        Raises:
            RuntimeError: 读取测量结果超时。

        Notes:
            如果传感器未启动，将先启动单次测量再读取结果。

        ==========================================

        Read current ranging result.

        Returns:
            int: Ranging result in millimeters (mm).

        Raises:
            RuntimeError: Timeout when reading measurement result.

        Notes:
            If the sensor is not started, it will first start a single measurement and then read the result.
        """
        if not self._started:
            self._config(
                (0x80, 0x01),
                (0xFF, 0x01),
                (0x00, 0x00),
                (0x91, self._stop_variable),
                (0x00, 0x01),
                (0xFF, 0x00),
                (0x80, 0x00),
                (_SYSRANGE_START, 0x01),
            )
            for timeout in range(_IO_TIMEOUT):
                if not self._register(_SYSRANGE_START) & 0x01:
                    break
                time.sleep_ms(1)
            else:
                raise RuntimeError("timeout")
        for timeout in range(_IO_TIMEOUT):
            if self._register(_RESULT_INTERRUPT_STATUS) & 0x07:
                break
            time.sleep_ms(1)
        else:
            raise RuntimeError("timeout")
        value = self._register(_RESULT_RANGE_STATUS + 10, _struct='>H')
        self._register(_INTERRUPT_CLEAR, 0x01)
        return value

    def set_signal_rate_limit(self, limit_Mcps) -> bool:
        """
        设置信号速率限制。

        Args:
            limit_Mcps (float): 信号速率限制，单位为Mcps（兆计数每秒）。

        Returns:
            bool: 配置成功返回True，否则返回False。

        Notes:
            合法范围为0到511.99 Mcps，超出范围将返回失败。

        ==========================================

        Set signal rate limit.

        Args:
            limit_Mcps (float): Signal rate limit in Mcps (Mega Counts Per Second).

        Returns:
            bool: True if configuration is successful, False otherwise.

        Notes:
            Valid range is 0 to 511.99 Mcps, out of range will return failure.
        """
        if limit_Mcps < 0 or limit_Mcps > 511.99:
            return False
        self._register(0x44, limit_Mcps * (1 << 7))
        return True

    def decode_Vcsel_period(self, reg_val) ->int:
        """
        解码VCSEL周期寄存器值。

        Args:
            reg_val (int): VCSEL周期寄存器值。

        Returns:
            int: 解码后的VCSEL周期（pclks）。

        Notes:
            将寄存器存储的VCSEL周期值转换为实际周期值。

        ==========================================

        Decode VCSEL period register value.

        Args:
            reg_val (int): VCSEL period register value.

        Returns:
            int: Decoded VCSEL period in pclks.

        Notes:
            Convert the VCSEL period value stored in the register to the actual period value.
        """
        return ((reg_val + 1) << 1)

    def encode_Vcsel_period(self, period_pclks) -> int:
        """
        编码VCSEL周期为寄存器值。

        Args:
            period_pclks (int): VCSEL周期（pclks）。

        Returns:
            int: 编码后的寄存器值。

        Notes:
            将实际VCSEL周期值转换为寄存器存储格式。

        ==========================================

        Encode VCSEL period to register value.

        Args:
            period_pclks (int): VCSEL period in pclks.

        Returns:
            int: Encoded register value.

        Notes:
            Convert the actual VCSEL period value to register storage format.
        """
        return (((period_pclks) >> 1) - 1)

    def set_Vcsel_pulse_period(self, type, period_pclks) -> bool:
        """
        设置VCSEL脉冲周期。

        Args:
            type (str): VCSEL周期类型，必须是vcsel_period_type中的元素。
            period_pclks (int): 脉冲周期（pclks）。

        Returns:
            bool: 配置成功返回True，否则返回False。

        Notes:
            支持的周期值取决于类型，超出范围将返回失败。

        ==========================================

        Set VCSEL pulse period.

        Args:
            type (str): VCSEL period type, must be an element in vcsel_period_type.
            period_pclks (int): Pulse period in pclks.

        Returns:
            bool: True if configuration is successful, False otherwise.

        Notes:
            Supported period values depend on the type, out of range will return failure.
        """
        vcsel_period_reg = self.encode_Vcsel_period(period_pclks)

        self.get_sequence_step_enables()
        self.get_sequence_step_timeouts()

        if type == self.vcsel_period_type[0]:
            if period_pclks == 12:
                self._register(PRE_RANGE_CONFIG_VALID_PHASE_HIGH, 0x18)
            elif period_pclks == 14:
                self._register(PRE_RANGE_CONFIG_VALID_PHASE_HIGH, 0x30)
            elif period_pclks == 16:
                self._register(PRE_RANGE_CONFIG_VALID_PHASE_HIGH, 0x40)
            elif period_pclks == 18:
                self._register(PRE_RANGE_CONFIG_VALID_PHASE_HIGH, 0x50)
            else:
                return False

            self._register(PRE_RANGE_CONFIG_VALID_PHASE_LOW, 0x08)
            self._register(PRE_RANGE_CONFIG_VCSEL_PERIOD, vcsel_period_reg)

            new_pre_range_timeout_mclks = self.timeout_microseconds_to_Mclks(self.timeouts["pre_range_us"],
                                                                             period_pclks)
            self._register(PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI, int(self.encode_timeout(new_pre_range_timeout_mclks)))

            new_msrc_timeout_mclks = self.timeout_microseconds_to_Mclks(self.timeouts["msrc_dss_tcc_us"],
                                                                        period_pclks)
            self._register(MSRC_CONFIG_TIMEOUT_MACROP, 255 if new_msrc_timeout_mclks > 256 else (new_msrc_timeout_mclks - 1))
        elif type == self.vcsel_period_type[1]:
            if period_pclks == 8:
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_HIGH, 0x10)
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_LOW, 0x08)
                self._register(GLOBAL_CONFIG_VCSEL_WIDTH, 0x02)
                self._register(ALGO_PHASECAL_CONFIG_TIMEOUT, 0x0C)
                self._register(0xFF, 0x01)
                self._register(ALGO_PHASECAL_LIM, 0x30)
                self._register(0xFF, 0x00)
            elif period_pclks == 10:
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_HIGH, 0x28)
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_LOW, 0x08)
                self._register(GLOBAL_CONFIG_VCSEL_WIDTH, 0x03)
                self._register(ALGO_PHASECAL_CONFIG_TIMEOUT, 0x09)
                self._register(0xFF, 0x01)
                self._register(ALGO_PHASECAL_LIM, 0x20)
                self._register(0xFF, 0x00)
            elif period_pclks == 12:
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_HIGH, 0x38)
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_LOW, 0x08)
                self._register(GLOBAL_CONFIG_VCSEL_WIDTH, 0x03)
                self._register(ALGO_PHASECAL_CONFIG_TIMEOUT, 0x08)
                self._register(0xFF, 0x01)
                self._register(ALGO_PHASECAL_LIM, 0x20)
                self._register(0xFF, 0x00)
            elif period_pclks == 14:
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_HIGH, 0x48)
                self._register(FINAL_RANGE_CONFIG_VALID_PHASE_LOW, 0x08)
                self._register(GLOBAL_CONFIG_VCSEL_WIDTH, 0x03)
                self._register(ALGO_PHASECAL_CONFIG_TIMEOUT, 0x07)
                self._register(0xFF, 0x01)
                self._register(ALGO_PHASECAL_LIM, 0x20)
                self._register(0xFF, 0x00)
            else:
                return False

            self._register(FINAL_RANGE_CONFIG_VCSEL_PERIOD, vcsel_period_reg)

            new_final_range_timeout_mclks = self.timeout_microseconds_to_Mclks(self.timeouts["final_range_us"], period_pclks)

            if self.enables["pre_range"]:
                new_final_range_timeout_mclks += 1
            self._register(FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI, self.encode_timeout(new_final_range_timeout_mclks))
        else:
            return False
        self.set_measurement_timing_budget(self.measurement_timing_budget_us)
        sequence_config = self._register(SYSTEM_SEQUENCE_CONFIG)
        self._register(SYSTEM_SEQUENCE_CONFIG, 0x02)
        self.perform_single_ref_calibration(0x0)
        self._register(SYSTEM_SEQUENCE_CONFIG, sequence_config)

        return True

    def get_sequence_step_enables(self):
        """
        获取序列步骤使能状态。

        Notes:
            结果存储在enables属性中，包含tcc、dss、msrc、pre_range和final_range的使能状态。

        ==========================================

        Get sequence step enable status.

        Notes:
            Results are stored in the enables attribute, including enable status of tcc, dss, msrc, pre_range and final_range.
        """
        sequence_config = self._register(0x01)

        self.enables["tcc"] = (sequence_config >> 4) & 0x1
        self.enables["dss"] = (sequence_config >> 3) & 0x1
        self.enables["msrc"] = (sequence_config >> 2) & 0x1
        self.enables["pre_range"] = (sequence_config >> 6) & 0x1
        self.enables["final_range"] = (sequence_config >> 7) & 0x1

    def get_vcsel_pulse_period(self, type) -> int:
        """
        获取VCSEL脉冲周期。

        Args:
            type (str): VCSEL周期类型，必须是vcsel_period_type中的元素。

        Returns:
            int: VCSEL脉冲周期（pclks），无效类型返回255。

        Notes:
            根据类型读取对应的寄存器并解码得到周期值。

        ==========================================

        Get VCSEL pulse period.

        Args:
            type (str): VCSEL period type, must be an element in vcsel_period_type.

        Returns:
            int: VCSEL pulse period in pclks, returns 255 for invalid type.

        Notes:
            Read and decode the corresponding register to get the period value according to the type.
        """
        if type == self.vcsel_period_type[0]:
            return self.decode_Vcsel_period(self._register(0x50))
        elif type == self.vcsel_period_type[1]:
            return self.decode_Vcsel_period(self._register(0x70))
        else:
            return 255

    def get_sequence_step_timeouts(self):
        """
        获取序列步骤超时参数。

        Notes:
            结果存储在timeouts属性中，包含各阶段的超时配置。

        ==========================================

        Get sequence step timeout parameters.

        Notes:
            Results are stored in the timeouts attribute, including timeout configurations for each stage.
        """
        self.timeouts["pre_range_vcsel_period_pclks"] = self.get_vcsel_pulse_period(self.vcsel_period_type[0])
        self.timeouts["msrc_dss_tcc_mclks"] = int(self._register(MSRC_CONFIG_TIMEOUT_MACROP)) + 1
        self.timeouts["msrc_dss_tcc_us"] = int(self.timeout_Mclks_to_microseconds(self.timeouts["msrc_dss_tcc_mclks"], self.timeouts["pre_range_vcsel_period_pclks"]))
        self.timeouts["pre_range_mclks"] = self.decode_timeout(self._register(PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI))
        self.timeouts["pre_range_us"] = int(self.timeout_Mclks_to_microseconds(self.timeouts["pre_range_mclks"],self.timeouts["pre_range_vcsel_period_pclks"]))
        self.timeouts["final_range_vcsel_period_pclks"] = self.get_vcsel_pulse_period(self.vcsel_period_type[1])
        self.timeouts["final_range_mclks"] = self.decode_timeout(self._register(FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI))

        if self.enables["pre_range"]:
            self.timeouts["final_range_mclks"] -= self.timeouts["pre_range_mclks"]
        self.timeouts["final_range_us"] = int(self.timeout_Mclks_to_microseconds(self.timeouts["final_range_mclks"],self.timeouts["final_range_vcsel_period_pclks"]))

    def timeout_Mclks_to_microseconds(self, timeout_period_mclks, vcsel_period_pclks) -> float:
        """
        将Mclks单位的超时转换为微秒。

        Args:
            timeout_period_mclks (int): Mclks单位的超时值。
            vcsel_period_pclks (int): VCSEL周期（pclks）。

        Returns:
            float: 转换后的微秒超时值。

        Notes:
            基于VCSEL周期计算宏周期，再转换为微秒。

        ==========================================

        Convert timeout in Mclks to microseconds.

        Args:
            timeout_period_mclks (int): Timeout value in Mclks.
            vcsel_period_pclks (int): VCSEL period in pclks.

        Returns:
            float: Converted timeout value in microseconds.

        Notes:
            Calculate macro period based on VCSEL period, then convert to microseconds.
        """
        macro_period_ns = self.calc_macro_period(vcsel_period_pclks)
        return ((timeout_period_mclks * macro_period_ns) + (macro_period_ns / 2)) / 1000

    def timeout_microseconds_to_Mclks(self, timeout_period_us, vcsel_period_pclks) -> float:
        """
        将微秒单位的超时转换为Mclks。

        Args:
            timeout_period_us (int): 微秒单位的超时值。
            vcsel_period_pclks (int): VCSEL周期（pclks）。

        Returns:
            float: 转换后的Mclks超时值。

        Notes:
            基于VCSEL周期计算宏周期，再转换为Mclks。

        ==========================================

        Convert timeout in microseconds to Mclks.

        Args:
            timeout_period_us (int): Timeout value in microseconds.
            vcsel_period_pclks (int): VCSEL period in pclks.

        Returns:
            float: Converted timeout value in Mclks.

        Notes:
            Calculate macro period based on VCSEL period, then convert to Mclks.
        """
        macro_period_ns = self.calc_macro_period(vcsel_period_pclks)
        return (((timeout_period_us * 1000) + (macro_period_ns / 2)) / macro_period_ns)

    def calc_macro_period(self, vcsel_period_pclks) -> float:
        """
        计算宏周期（纳秒）。

        Args:
            vcsel_period_pclks (int): VCSEL周期（pclks）。

        Returns:
            float: 宏周期值（纳秒）。

        Notes:
            宏周期基于VCSEL周期计算，用于超时单位转换。

        ==========================================

        Calculate macro period in nanoseconds.

        Args:
            vcsel_period_pclks (int): VCSEL period in pclks.

        Returns:
            float: Macro period value in nanoseconds.

        Notes:
            Macro period is calculated based on VCSEL period and used for timeout unit conversion.
        """
        return (((2304 * (vcsel_period_pclks) * 1655) + 500) / 1000)

    def decode_timeout(self, reg_val) -> int:
        """
        解码超时寄存器值。

        Args:
            reg_val (int): 超时寄存器值。

        Returns:
            int: 解码后的超时值（Mclks）。

        Notes:
            将寄存器存储的压缩格式超时值转换为实际Mclks值。

        ==========================================

        Decode timeout register value.

        Args:
            reg_val (int): Timeout register value.

        Returns:
            int: Decoded timeout value in Mclks.

        Notes:
            Convert the compressed format timeout value stored in the register to actual Mclks value.
        """
        return ((reg_val & 0x00FF) << ((reg_val & 0xFF00) >> 8)) + 1

    def encode_timeout(self, timeout_mclks) -> int:
        """
        编码超时值为寄存器格式。

        Args:
            timeout_mclks (int): Mclks单位的超时值。

        Returns:
            int: 编码后的寄存器值。

        Notes:
            将Mclks超时值转换为寄存器存储的压缩格式。

        ==========================================

        Encode timeout value to register format.

        Args:
            timeout_mclks (int): Timeout value in Mclks.

        Returns:
            int: Encoded register value.

        Notes:
            Convert Mclks timeout value to compressed format stored in register.
        """
        timeout_mclks = int(timeout_mclks)
        ls_byte = 0
        ms_byte = 0

        if timeout_mclks > 0:
            ls_byte = timeout_mclks - 1

            while (ls_byte & 0xFFFFFF00) > 0:
                ls_byte >>= 1
                ms_byte += 1
            return (ms_byte << 8) or (ls_byte & 0xFF)
        else:
            return 0

    def set_measurement_timing_budget(self, budget_us) -> bool:
        """
        设置测量时间预算。

        Args:
            budget_us (int): 时间预算（微秒）。

        Returns:
            bool: 配置成功返回True，否则返回False。

        Notes:
            最小时间预算为20000微秒，低于此值将返回失败。

        ==========================================

        Set measurement timing budget.

        Args:
            budget_us (int): Timing budget in microseconds.

        Returns:
            bool: True if configuration is successful, False otherwise.

        Notes:
            Minimum timing budget is 20000 microseconds, values below this will return failure.
        """
        start_overhead = 1320
        end_overhead = 960
        msrc_overhead = 660
        tcc_overhead = 590
        dss_overhead = 690
        pre_range_overhead = 660
        final_range_overhead = 550

        min_timing_budget = 20000

        if budget_us < min_timing_budget:
            return False
        used_budget_us = start_overhead + end_overhead

        self.get_sequence_step_enables()
        self.get_sequence_step_timeouts()

        if self.enables["tcc"]:
            used_budget_us += self.timeouts["msrc_dss_tcc_us"] + tcc_overhead
        if self.enables["dss"]:
            used_budget_us += 2 * self.timeouts["msrc_dss_tcc_us"] + dss_overhead
        if self.enables["msrc"]:
            used_budget_us += self.timeouts["msrc_dss_tcc_us"] + msrc_overhead
        if self.enables["pre_range"]:
            used_budget_us += self.timeouts["pre_range_us"] + pre_range_overhead
        if self.enables["final_range"]:
            used_budget_us += final_range_overhead

            if used_budget_us > budget_us:
                return False
            final_range_timeout_us = budget_us - used_budget_us
            final_range_timeout_mclks = self.timeout_microseconds_to_Mclks(final_range_timeout_us, self.timeouts["final_range_vcsel_period_pclks"])

            if self.enables["pre_range"]:
                final_range_timeout_mclks += self.timeouts["pre_range_mclks"]
            self._register(FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI, self.encode_timeout(final_range_timeout_mclks))
            self.measurement_timing_budget_us = budget_us
        return True

    def perform_single_ref_calibration(self, vhv_init_byte) -> bool:
        """
        执行单次参考校准。

        Args:
            vhv_init_byte (int): VHV初始化字节参数。

        Returns:
            bool: 校准成功返回True，超时返回False。

        Notes:
            用于传感器校准，确保测量精度。

        ==========================================

        Perform single reference calibration.

        Args:
            vhv_init_byte (int): VHV initialization byte parameter.

        Returns:
            bool: True if calibration is successful, False if timeout.

        Notes:
            Used for sensor calibration to ensure measurement accuracy.
        """

        start_time = time.ticks_ms()  # 记录开始时间（毫秒级）
        # 启动校准
        self._register(SYSRANGE_START, 0x01 | vhv_init_byte)
        # 等待校准完成，同时检查超时
        while (self._register(RESULT_INTERRUPT_STATUS) & 0x07) == 0:
            # 计算已过去的时间（处理可能的溢出情况）
            time_elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            # 检查是否超时
            if time_elapsed > _IO_TIMEOUT:
                return False
        # 校准成功，清理并返回
        self._register(SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._register(SYSRANGE_START, 0x00)
        return True

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
