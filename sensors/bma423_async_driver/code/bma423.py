# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Salvatore Sanfilippo, FreakStudio
# @File    : bma423.py
# @Description : BMA423 加速度传感器驱动，支持 Bosch 特征引擎（计步/活动/倾斜检测）
# @License : MIT

__version__ = "1.0.0"
__author__ = "Salvatore Sanfilippo, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# 为 ISR 预留紧急异常缓冲区
try:
    from micropython import const, alloc_emergency_exception_buf

    alloc_emergency_exception_buf(100)
except ImportError:

    def const(value):
        return value

    def alloc_emergency_exception_buf(size):
        pass


from machine import Pin
import time

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# 寄存器地址常量（硬件固定值，不可修改）
REG_CHIP_ID = const(0x00)
REG_INT_STATUS_0 = const(0x1C)
REG_INT_STATUS_1 = const(0x1D)
REG_STEP_COUNTER_0 = const(0x1E)
REG_TEMPERATURE = const(0x22)
REG_INTERNAL_STATUS = const(0x2A)
REG_ACC_CONF = const(0x40)
REG_ACC_RANGE = const(0x41)
REG_PWR_CONF = const(0x7C)
REG_PWR_CTL = const(0x7D)
REG_CMD = const(0x7E)
REG_INT1_IO_CTRL = const(0x53)
REG_INT2_IO_CTRL = const(0x54)
REG_INT_LATCH = const(0x55)
REG_INT1_MAP = const(0x56)
REG_INT2_MAP = const(0x57)
REG_INT_MAP_DATA = const(0x58)
REG_INIT_CTRL = const(0x59)
REG_CONFIG_ADDR_LSB = const(0x5B)
REG_CONFIG_ADDR_MSB = const(0x5C)
REG_CONFIG_DATA = const(0x5E)
FEATURES_IN_SIZE = const(70)

# 加速度数据寄存器起始地址
REG_ACC_X_LSB = const(0x12)

# 命令常量
REG_CMD_SOFTRESET = const(0xB6)

# I2C 重试参数
I2C_RETRIES = const(2)
I2C_RETRY_DELAY_MS = const(5)

# 初始化超时时间（毫秒）
ASIC_INIT_TIMEOUT_MS = const(1000)

# 复用缓冲区（减少内存分配）
_BUF8 = bytearray(8)

# ======================================== 功能函数 ============================================


def _convert_to_int12(raw_value: int) -> int:
    """
    将原始 12 位补码数据转换为有符号整数
    Args:
        raw_value (int): 12 位原始值（带符号位的补码）
    Returns:
        int: 有符号整数值
    ==========================================
    Convert raw 12-bit two's complement to signed integer.
    Args:
        raw_value (int): 12-bit raw value in two's complement
    Returns:
        int: Signed integer value
    """
    if not raw_value & 0x800:
        return raw_value
    return -(((~raw_value) & 0x7FF) + 1)


def _normalize_reading(raw_value: int, acc_range: int) -> float:
    """
    将 12 位加速度值归一化为以 g 为单位的加速度
    Args:
        raw_value (int): 有符号 12 位加速度值
        acc_range (int): 当前加速度量程（2/4/8/16 g）
    Returns:
        float: 以 g 为单位的加速度值
    ==========================================
    Normalize 12-bit acceleration to g units.
    Args:
        raw_value (int): Signed 12-bit acceleration value
        acc_range (int): Current acceleration range (2/4/8/16 g)
    Returns:
        float: Acceleration value in g
    """
    return acc_range / 2047.0 * raw_value


# ======================================== 自定义类 ============================================


class BMA423:
    """
    BMA423 加速度传感器驱动类
    支持加速度数据读取和 Bosch 特征引擎（计步/活动检测/倾斜检测等）
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _range (int): 加速度量程（2/4/8/16 g）
        _features_in (bytearray): 特征配置存储区
        _callback (callable): 中断回调函数
        _debug (bool): 调试日志开关
    Methods:
        reset(): 软复位设备
        enable_accelerometer(): 启用/禁用加速度计
        set_accelerometer_perf(): 设置性能模式
        set_accelerometer_avg(): 设置平均模式
        set_accelerometer_freq(): 设置采样频率
        set_advanced_power_save(): 设置高级省电模式
        set_range(): 设置加速度量程
        load_features_config(): 加载 Bosch 特征引擎配置
        enable_features_detection(): 启用特定特征检测
        get_steps(): 读取计步器数值
        get_xyz(): 读取三轴加速度值
        get_temperature(): 读取芯片温度
        enable_interrupt(): 配置中断引脚和事件映射
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - bma423conf.bin 文件必须与驱动文件位于同一目录
        - 特征检测功能依赖 Bosch 官方配置文件
        - 硬 IRQ 仅置标志；process_irq() 在任务或主循环中执行回调
    ==========================================
    BMA423 accelerometer driver with feature engine support.
    Supports acceleration data reading and Bosch feature engine
    (step counting, activity detection, tilt detection, etc.)
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _range (int): Acceleration range (2/4/8/16 g)
        _features_in (bytearray): Feature configuration storage
        _callback (callable): Interrupt callback function
        _debug (bool): Debug log switch
    Methods:
        reset(): Soft reset the device
        enable_accelerometer(): Enable/disable accelerometer
        set_accelerometer_perf(): Set performance mode
        set_accelerometer_avg(): Set averaging mode
        set_accelerometer_freq(): Set sampling frequency
        set_advanced_power_save(): Set advanced power saving
        set_range(): Set acceleration range
        load_features_config(): Load Bosch feature engine config
        enable_features_detection(): Enable specific feature detection
        get_steps(): Read step counter value
        get_xyz(): Read three-axis acceleration values
        get_temperature(): Read chip temperature
        enable_interrupt(): Configure interrupt pin and event mapping
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided I2C instance
        - bma423conf.bin must be in the same directory as this driver
        - Feature detection requires Bosch official configuration file
        - The hard IRQ sets a flag; process_irq() invokes callbacks in task/main-loop context
    """

    # 类级常量：I2C 默认地址（由 SDO 引脚电平决定）
    DEFAULT_ADDR_LOW = const(0x18)
    DEFAULT_ADDR_HIGH = const(0x19)

    # 芯片 ID 期望值
    EXPECTED_CHIP_ID = const(0x13)

    # 量程到寄存器值的映射
    RANGE_MAP = {2: 0, 4: 1, 8: 2, 16: 3}

    # 频率到寄存器值的映射
    FREQ_MAP = {25: 6, 50: 7, 100: 8, 200: 9, 400: 10, 800: 11, 1600: 12}

    # PWR_CTL 寄存器使能位
    PWR_ACC_EN = const(0x4)
    PWR_AUX_EN = const(0x1)

    # INT_IO_CTRL 寄存器配置位
    INT_OUTPUT_EN = const(0x8)
    INT_ACTIVE_HIGH = const(0x2)

    def __init__(self, i2c, acc_range: int = 2, debug: bool = False) -> None:
        """
        初始化 BMA423 加速度传感器
        Args:
            i2c (I2C): MicroPython I2C 总线实例
            acc_range (int): 加速度量程，可选 2/4/8/16，默认 2g
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            ValueError: 参数类型或值无效
            RuntimeError: 设备未找到或芯片 ID 不匹配
        Notes:
            - 自动扫描 I2C 总线查找设备（地址 0x18 或 0x19）
            - 初始化完成后加速度计处于工作状态
        ==========================================
        Initialize BMA423 accelerometer.
        Args:
            i2c (I2C): MicroPython I2C bus instance
            acc_range (int): Acceleration range, options 2/4/8/16, default 2g
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: Invalid parameter type or value
            RuntimeError: Device not found or chip ID mismatch
        Notes:
            - Auto-scans I2C bus for device (address 0x18 or 0x19)
            - Accelerometer is enabled after initialization
        """
        # 参数校验
        if not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem/writeto_mem")
        if acc_range not in (2, 4, 8, 16):
            raise ValueError("acc_range must be 2, 4, 8, or 16, got %s" % acc_range)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = None
        self._range = acc_range
        self._debug = debug
        self._callback = None
        self._features_in = bytearray(FEATURES_IN_SIZE)

        # 自动扫描 I2C 总线查找设备地址
        found_devices = i2c.scan()
        self._log("I2C bus scan: %s" % [hex(x) for x in found_devices])
        for addr in (self.DEFAULT_ADDR_LOW, self.DEFAULT_ADDR_HIGH):
            if addr in found_devices:
                self._addr = addr
                break
        if self._addr is None:
            raise RuntimeError("BMA423 not found on I2C bus (expected 0x18 or 0x19)")
        self._log("Device found at 0x%02X" % self._addr)

        # 软复位并校验芯片 ID
        self.reset()
        chip_id = self._read_reg(REG_CHIP_ID)[0]
        if chip_id != self.EXPECTED_CHIP_ID:
            raise RuntimeError("BMA423 chip ID mismatch: expected 0x%02X, got 0x%02X" % (self.EXPECTED_CHIP_ID, chip_id))
        self._log("Chip ID verified: 0x%02X" % chip_id)

        # 初始化默认参数，使加速度计进入工作状态
        self.enable_accelerometer(acc=True, aux=False)
        self.set_accelerometer_perf(True)
        self.set_accelerometer_avg(2)
        self.set_accelerometer_freq(100)
        self.set_advanced_power_save(False, False)
        self.set_range(acc_range)

    # ==================== 公共方法 ====================

    def reset(self) -> None:
        """
        软复位设备
        Notes:
            - 副作用：重置所有寄存器为默认值
            - 复位后需等待约 1 秒完成 ASIC 初始化
            - ISR-safe: 否
        ==========================================
        Soft reset the device.
        Notes:
            - Side effect: Resets all registers to defaults
            - Requires ~1 second wait for ASIC initialization
            - ISR-safe: No
        """
        self._write_reg(REG_CMD, REG_CMD_SOFTRESET)
        time.sleep(1)

    def enable_accelerometer(self, acc: bool = True, aux: bool = False) -> None:
        """
        启用或禁用加速度计和辅助传感器
        Args:
            acc (bool): 是否启用加速度计
            aux (bool): 是否启用辅助传感器
        Notes:
            - 副作用：修改 PWR_CTL 寄存器
            - ISR-safe: 否
        ==========================================
        Enable or disable accelerometer and auxiliary sensor.
        Args:
            acc (bool): Enable accelerometer
            aux (bool): Enable auxiliary sensor
        Notes:
            - Side effect: Modifies PWR_CTL register
            - ISR-safe: No
        """
        val = 0
        if acc:
            val |= self.PWR_ACC_EN
        if aux:
            val |= self.PWR_AUX_EN
        self._write_reg(REG_PWR_CTL, val)

    def set_accelerometer_perf(self, perf_mode: bool) -> None:
        """
        设置加速度计性能模式
        Args:
            perf_mode (bool): True 启用连续采样，False 关闭
        Notes:
            - 副作用：修改 ACC_CONF 寄存器 bit7
            - 性能模式下加速度计以指定采样率持续采样
            - ISR-safe: 否
        ==========================================
        Set accelerometer performance mode.
        Args:
            perf_mode (bool): True for continuous sampling, False to disable
        Notes:
            - Side effect: Modifies ACC_CONF register bit7
            - Performance mode enables continuous sampling at configured rate
            - ISR-safe: No
        """
        val = self._read_reg(REG_ACC_CONF)[0]
        val = (val & 0b01111111) | (int(perf_mode) << 7)
        self._write_reg(REG_ACC_CONF, val)

    def set_accelerometer_avg(self, avg_mode: int) -> None:
        """
        设置加速度计平均模式
        Args:
            avg_mode (int): 平均模式值
                - 性能模式开启时：0=OSR4, 1=OSR2, 2=Normal, 3=CIC
                - 性能模式关闭时：0=avg1, 1=avg2, 2=avg4, 3=avg8, 4=avg16, 5=avg32, 6=avg64, 7=avg128
        Raises:
            ValueError: avg_mode 超出有效范围
        Notes:
            - 副作用：修改 ACC_CONF 寄存器 bit[6:4]
            - ISR-safe: 否
        ==========================================
        Set accelerometer averaging mode.
        Args:
            avg_mode (int): Averaging mode value
                - Performance mode on: 0=OSR4, 1=OSR2, 2=Normal, 3=CIC
                - Performance mode off: 0=avg1, 1=avg2, 2=avg4, 3=avg8, 4=avg16, 5=avg32, 6=avg64, 7=avg128
        Raises:
            ValueError: avg_mode out of valid range
        Notes:
            - Side effect: Modifies ACC_CONF register bits[6:4]
            - ISR-safe: No
        """
        if not 0 <= avg_mode <= 7:
            raise ValueError("avg_mode must be 0-7, got %s" % avg_mode)
        val = self._read_reg(REG_ACC_CONF)[0]
        val = (val & 0b10001111) | (avg_mode << 4)
        self._write_reg(REG_ACC_CONF, val)

    def set_accelerometer_freq(self, freq: int) -> None:
        """
        设置加速度计采样频率
        Args:
            freq (int): 采样频率（Hz），支持 25/50/100/200/400/800/1600，
                       或直接传入寄存器原始值（0~12，不含 13~15）
        Raises:
            ValueError: 频率值无效
        Notes:
            - 副作用：修改 ACC_CONF 寄存器低 4 位
            - ISR-safe: 否
        ==========================================
        Set accelerometer sampling frequency.
        Args:
            freq (int): Sampling frequency in Hz, supports 25/50/100/200/400/800/1600,
                       or raw register value (0~12, excluding 13~15)
        Raises:
            ValueError: Invalid frequency value
        Notes:
            - Side effect: Modifies ACC_CONF register lower 4 bits
            - ISR-safe: No
        """
        if freq in self.FREQ_MAP:
            freq = self.FREQ_MAP[freq]
        if freq < 0 or freq > 12:
            raise ValueError("Invalid frequency or raw value: %s" % freq)
        val = self._read_reg(REG_ACC_CONF)[0]
        val = (val & 0b11110000) | freq
        self._write_reg(REG_ACC_CONF, val)

    def set_advanced_power_save(self, adp: bool = False, fifo_self_wakeup: bool = False) -> None:
        """
        设置高级省电模式
        Args:
            adp (bool): 是否启用高级省电模式（无采样时降低时钟速度）
            fifo_self_wakeup (bool): ADP 模式下 FIFO 是否自唤醒
        Notes:
            - 副作用：修改 PWR_CONF 寄存器
            - 启用 ADP 可能导致计步精度下降
            - ISR-safe: 否
        ==========================================
        Set advanced power saving mode.
        Args:
            adp (bool): Enable advanced power saving (slow clock when idle)
            fifo_self_wakeup (bool): FIFO self wakeup when ADP is active
        Notes:
            - Side effect: Modifies PWR_CONF register
            - ADP may reduce step counting accuracy
            - ISR-safe: No
        """
        val = (int(adp) & 1) | ((int(fifo_self_wakeup) & 1) << 1)
        self._write_reg(REG_PWR_CONF, val)

    def set_range(self, acc_range: int) -> None:
        """
        设置加速度量程
        Args:
            acc_range (int): 量程值，支持 2/4/8/16 g
        Raises:
            ValueError: 量程值无效
        Notes:
            - 副作用：修改 ACC_RANGE 寄存器，更新实例内部 _range 属性
            - 量程越大相对精度越低（12 位 ADC 分辨率固定）
            - ISR-safe: 否
        ==========================================
        Set acceleration range.
        Args:
            acc_range (int): Range in g, supports 2/4/8/16
        Raises:
            ValueError: Invalid range value
        Notes:
            - Side effect: Modifies ACC_RANGE register and updates _range
            - Larger range reduces relative precision (fixed 12-bit ADC)
            - ISR-safe: No
        """
        if acc_range not in self.RANGE_MAP:
            raise ValueError("acc_range must be 2, 4, 8, or 16, got %s" % acc_range)
        self._range = acc_range
        self._write_reg(REG_ACC_RANGE, self.RANGE_MAP[acc_range])

    def load_features_config(self) -> None:
        """
        加载 Bosch 特征引擎配置文件 (bma423conf.bin)

        此方法将 bma423conf.bin 中的二进制配置数据写入 BMA423 的 ASIC 存储器，
        启用特征检测引擎（计步、活动识别、倾斜检测等）。调用前必须确保
        bma423conf.bin 文件与驱动文件位于同一目录。
        Raises:
            RuntimeError: 配置文件传输失败或 ASIC 初始化超时
            OSError: bma423conf.bin 文件不存在
        Notes:
            - 副作用：修改 PWR_CONF/INIT_CTRL 和 ASIC 存储器内容
            - 初始化完成后自动验证写入数据完整性
            - 调用前需先完成加速度计基本配置
            - ISR-safe: 否
        ==========================================
        Load Bosch feature engine configuration from bma423conf.bin.

        Writes binary configuration data from bma423conf.bin into the
        BMA423 ASIC memory to enable feature detection (step counting,
        activity recognition, tilt detection, etc.). The bma423conf.bin
        file must be in the same directory as this driver.
        Raises:
            RuntimeError: Configuration transfer failed or ASIC init timeout
            OSError: bma423conf.bin file not found
        Notes:
            - Side effect: Modifies PWR_CONF/INIT_CTRL and ASIC memory
            - Verifies written data integrity after transfer
            - Basic accelerometer configuration should be done first
            - ISR-safe: No
        """
        # 保存并关闭高级省电模式以准备配置传输
        saved_pwr_conf = self._read_reg(REG_PWR_CONF)[0]
        self._write_reg(REG_PWR_CONF, 0x00)
        time.sleep_us(500)

        # 准备加载特征引擎配置
        self._write_reg(REG_INIT_CTRL, 0x00)
        self._transfer_config()
        self._write_reg(REG_INIT_CTRL, 0x01)

        # 等待 ASIC 初始化完成，带超时保护
        elapsed = 0
        status = 0
        while elapsed < ASIC_INIT_TIMEOUT_MS:
            status = self._read_reg(REG_INTERNAL_STATUS)[0] & 0b11111
            if status == 1:
                break
            time.sleep_ms(50)
            elapsed += 50
        if elapsed >= ASIC_INIT_TIMEOUT_MS:
            raise RuntimeError("BMA423 ASIC init timeout after %d ms, internal_status=0x%02X" % (ASIC_INIT_TIMEOUT_MS, status))

        self._log("Features engine initialized successfully")
        self._write_reg(REG_PWR_CONF, saved_pwr_conf)

    def enable_features_detection(self, *features: str) -> None:
        """
        启用特定特征检测功能
        Args:
            *features (str): 要启用的特征名称，当前支持 "step-count"
        Raises:
            ValueError: 传入不支持的特征名称
        Notes:
            - 副作用：修改 FEATURES_IN 配置区域并写入设备
            - 调用前必须先调用 load_features_config()
            - ISR-safe: 否
        ==========================================
        Enable specific feature detection.
        Args:
            *features (str): Feature names to enable, currently supports "step-count"
        Raises:
            ValueError: Unsupported feature name
        Notes:
            - Side effect: Modifies FEATURES_IN area and writes to device
            - Must call load_features_config() first
            - ISR-safe: No
        """
        self._read_features_in()
        for f in features:
            if f == "step-count":
                self._features_in[0x3B] |= 0x10
            else:
                raise ValueError("Unsupported feature: %s" % f)
        self._write_features_in()

    def get_xyz(self) -> tuple:
        """
        读取三轴加速度值
        Returns:
            tuple: (x, y, z) 三轴加速度值，单位为 g
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 从寄存器 0x12 起连续读取 6 字节原始数据
            - 原始 12 位数据经过补码转换和归一化处理
            - ISR-safe: 否
        ==========================================
        Read three-axis acceleration values.
        Returns:
            tuple: (x, y, z) acceleration in g units
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads 6 bytes from register 0x12
            - Raw 12-bit data converted from two's complement and normalized
            - ISR-safe: No
        """
        rawdata = self._read_reg(REG_ACC_X_LSB, 6)
        # 提取 12 位加速度值（每轴 2 字节小端格式）
        acc_x = (rawdata[0] >> 4) | (rawdata[1] << 4)
        acc_y = (rawdata[2] >> 4) | (rawdata[3] << 4)
        acc_z = (rawdata[4] >> 4) | (rawdata[5] << 4)
        # 补码转换 → 有符号整数
        acc_x = _convert_to_int12(acc_x)
        acc_y = _convert_to_int12(acc_y)
        acc_z = _convert_to_int12(acc_z)
        # 归一化为 g 值
        acc_x = _normalize_reading(acc_x, self._range)
        acc_y = _normalize_reading(acc_y, self._range)
        acc_z = _normalize_reading(acc_z, self._range)
        return (acc_x, acc_y, acc_z)

    def get_steps(self) -> int:
        """
        读取计步器数值
        Returns:
            int: 累计步数（32 位无符号整数）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 读取 4 字节小端数据
            - 需先启用 "step-count" 特征检测
            - ISR-safe: 否
        ==========================================
        Read step counter value.
        Returns:
            int: Cumulative step count (32-bit unsigned)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads 4 bytes in little-endian format
            - Requires "step-count" feature to be enabled first
            - ISR-safe: No
        """
        data = self._read_reg(REG_STEP_COUNTER_0, 4)
        return data[0] | data[1] << 8 | data[2] << 16 | data[3] << 24

    def get_temperature(self) -> float:
        """
        读取芯片温度
        Returns:
            float or None: 温度值（℃），无效读取时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 芯片内部温度传感器，精度有限
            - 原始值为基于 23°C 的偏移量（有符号 8 位补码）
            - ISR-safe: 否
        ==========================================
        Read chip temperature.
        Returns:
            float or None: Temperature in Celsius, None if reading is invalid
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Internal temperature sensor with limited accuracy
            - Raw value is signed 8-bit offset from 23°C
            - ISR-safe: No
        """
        raw = self._read_reg(REG_TEMPERATURE)[0]
        if raw == 0x80:
            return None
        if raw & 0x80:
            raw = -((~raw & 0xFF) + 1)
        return 23.0 + raw

    def configure_events(self, chip_pin: int, pin: Pin, callback: callable, events: list, trigger: int = Pin.IRQ_RISING) -> None:
        """
        配置中断引脚和事件映射
        Args:
            chip_pin (int): BMA423 芯片中断引脚编号（1 或 2）
            pin (Pin): 主机端 GPIO 引脚实例
            callback (callable): 中断触发时调用的回调函数，
                                 签名: callback(data) 其中 data 为 dict
            events (list): 要监听的事件列表，支持：
                           "step", "activity", "tilt", "any-none",
                           "data", "fifo-wm", "fifo-full"
            trigger (int): 中断触发条件，默认 Pin.IRQ_RISING
        Raises:
            ValueError: pin 无效、chip_pin 无效或事件名称不支持
        Notes:
            - 副作用：修改多个中断相关寄存器并注册硬件中断
            - 硬 IRQ 仅置标志；由 process_irq() 在任务或主循环中安全执行
            - 特征检测模式仅支持电平触发（latch mode）
            - 不支持同时订阅双击和单击事件
            - ISR-safe: 否（注册过程不可在 ISR 中调用）
        ==========================================
        Configure interrupt pin and event mapping.
        Args:
            chip_pin (int): BMA423 chip interrupt pin number (1 or 2)
            pin (Pin): Host GPIO pin instance
            callback (callable): Callback function called on interrupt,
                                 signature: callback(data) where data is dict
            events (list): Event names to listen for, supports:
                           "step", "activity", "tilt", "any-none",
                           "data", "fifo-wm", "fifo-full"
            trigger (int): Interrupt trigger condition, default Pin.IRQ_RISING
        Raises:
            ValueError: Invalid pin, chip_pin, or unsupported event name
        Notes:
            - Side effect: Modifies interrupt registers and registers hardware IRQ
            - The hard IRQ only records a flag; process_irq() invokes the callback safely in task/main-loop context
            - Feature detection only supports level-triggered (latch) mode
            - Does not support simultaneous double/single tap subscription
            - ISR-safe: No (registration must not be called from ISR)
        """
        # 参数校验
        if not hasattr(pin, "irq"):
            raise ValueError("pin must be a Pin instance with irq() method")
        if chip_pin not in (1, 2):
            raise ValueError("chip_pin must be 1 or 2, got %s" % chip_pin)
        if not callable(callback):
            raise ValueError("callback must be callable, got %s" % type(callback))
        if not isinstance(events, (list, tuple)):
            raise ValueError("events must be a list or tuple, got %s" % type(events))

        self._callback = callback

        # 特征检测需使用锁存模式
        self._write_reg(REG_INT_LATCH, 0x01)

        # 特征事件位映射（INT1/2_MAP 寄存器）
        feature_bits = {"any-none": 6, "tilt": 3, "activity": 2, "step": 1}
        # 数据事件位映射（INT_MAP_DATA 寄存器）
        # 格式：{事件名: [pin1_bit, pin2_bit]}
        data_bits = {"data": [2, 6], "fifo-wm": [1, 5], "fifo-full": [0, 4]}

        # 遍历事件列表，构建中断映射寄存器值
        feature_map = 0
        data_map = 0
        for e in events:
            if e in feature_bits:
                feature_map |= 1 << feature_bits[e]
            elif e in data_bits:
                data_map |= data_bits[e][chip_pin - 1]
            else:
                raise ValueError("Unknown event: %s" % e)

        # 写入特征中断映射寄存器
        if feature_map != 0:
            map_reg = REG_INT1_MAP if chip_pin == 1 else REG_INT2_MAP
            self._write_reg(map_reg, feature_map)

        # 写入数据中断映射寄存器
        if data_map != 0:
            self._write_reg(REG_INT_MAP_DATA, data_map)

        # 配置中断引脚电气特性（推挽输出、高电平有效、电平触发）
        ctrl_reg = REG_INT1_IO_CTRL if chip_pin == 1 else REG_INT2_IO_CTRL
        self._write_reg(ctrl_reg, self.INT_OUTPUT_EN | self.INT_ACTIVE_HIGH)

        # 注册主机端中断回调，通过 schedule 调度到主循环执行
        pin.irq(handler=self._irq_handler, trigger=trigger)

    def deinit(self) -> None:
        """
        释放硬件资源
        Notes:
            - 将加速度计和辅助传感器断电
            - 清除中断回调引用
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Notes:
            - Powers down accelerometer and auxiliary sensor
            - Clears interrupt callback reference
            - ISR-safe: No
        """
        self._callback = None
        self.enable_accelerometer(acc=False, aux=False)

    # ==================== 私有方法 ====================

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅在 debug=True 时输出
            - ISR-safe: 否
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Output only when debug=True
            - ISR-safe: No
        """
        if self._debug:
            print("[BMA423] %s" % msg)

    def _read_reg(self, reg: int, nbytes: int = 1) -> bytearray:
        """
        读取设备寄存器（带重试机制）
        Args:
            reg (int): 寄存器地址
            nbytes (int): 读取字节数
        Returns:
            bytearray: 读取到的数据
        Raises:
            RuntimeError: I2C 通信失败（重试后）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read device register (with retry).
        Args:
            reg (int): Register address
            nbytes (int): Number of bytes to read
        Returns:
            bytearray: Data read from register
        Raises:
            RuntimeError: I2C communication failed after retries
        Notes:
            - ISR-safe: No
        """
        buf = bytearray(nbytes)
        for attempt in range(I2C_RETRIES + 1):
            try:
                self._i2c.readfrom_mem_into(self._addr, reg, buf)
                return buf
            except OSError as e:
                if attempt == I2C_RETRIES:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (reg, I2C_RETRIES)) from e
                time.sleep_ms(I2C_RETRY_DELAY_MS)

    def _write_reg(self, reg: int, value: int) -> None:
        """
        写入设备寄存器（带重试机制）
        Args:
            reg (int): 寄存器地址
            value (int): 要写入的字节值
        Raises:
            RuntimeError: I2C 通信失败（重试后）
        Notes:
            - ISR-safe: 否
        ==========================================
        Write device register (with retry).
        Args:
            reg (int): Register address
            value (int): Byte value to write
        Raises:
            RuntimeError: I2C communication failed after retries
        Notes:
            - ISR-safe: No
        """
        for attempt in range(I2C_RETRIES + 1):
            try:
                self._i2c.writeto_mem(self._addr, reg, bytes([value]))
                return
            except OSError as e:
                if attempt == I2C_RETRIES:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (reg, I2C_RETRIES)) from e
                time.sleep_ms(I2C_RETRY_DELAY_MS)

    def _write_reg_buf(self, reg: int, buf: bytearray) -> None:
        """
        批量写入设备寄存器（带重试机制）
        Args:
            reg (int): 寄存器地址
            buf (bytearray): 要写入的数据缓冲区
        Raises:
            RuntimeError: I2C 通信失败（重试后）
        Notes:
            - ISR-safe: 否
        ==========================================
        Write buffer to device register (with retry).
        Args:
            reg (int): Register address
            buf (bytearray): Data buffer to write
        Raises:
            RuntimeError: I2C communication failed after retries
        Notes:
            - ISR-safe: No
        """
        for attempt in range(I2C_RETRIES + 1):
            try:
                self._i2c.writeto_mem(self._addr, reg, buf)
                return
            except OSError as e:
                if attempt == I2C_RETRIES:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (reg, I2C_RETRIES)) from e
                time.sleep_ms(I2C_RETRY_DELAY_MS)

    def _write_config_mem(self, idx: int, buf: bytearray) -> None:
        """
        向 ASIC 配置存储器写入数据
        Args:
            idx (int): 半字索引（硬件内部地址）
            buf (bytearray): 要写入的配置数据
        Notes:
            - 通过 0x5B/0x5C 寄存器设置目标地址，0x5E 作为数据端口
            - 每次写入 8 字节，连续写入相邻 ASIC 存储位置
            - ISR-safe: 否
        ==========================================
        Write data to ASIC configuration memory.
        Args:
            idx (int): Half-word index (hardware internal address)
            buf (bytearray): Configuration data to write
        Notes:
            - Sets target address via 0x5B/0x5C, uses 0x5E as data port
            - Writes 8 bytes at a time to consecutive ASIC memory locations
            - ISR-safe: No
        """
        self._write_reg(REG_CONFIG_ADDR_LSB, (idx // 2) & 0x0F)
        self._write_reg(REG_CONFIG_ADDR_MSB, (idx // 2) >> 4)
        self._write_reg_buf(REG_CONFIG_DATA, buf)

    def _read_config_mem(self, idx: int, count: int) -> bytearray:
        """
        从 ASIC 配置存储器读取数据
        Args:
            idx (int): 半字索引（硬件内部地址）
            count (int): 读取字节数
        Returns:
            bytearray: 从 ASIC 存储器读取的配置数据
        Notes:
            - 通过 0x5B/0x5C 寄存器设置目标地址，0x5E 作为数据端口
            - ISR-safe: 否
        ==========================================
        Read data from ASIC configuration memory.
        Args:
            idx (int): Half-word index (hardware internal address)
            count (int): Number of bytes to read
        Returns:
            bytearray: Configuration data read from ASIC memory
        Notes:
            - Sets target address via 0x5B/0x5C, uses 0x5E as data port
            - ISR-safe: No
        """
        self._write_reg(REG_CONFIG_ADDR_LSB, (idx // 2) & 0x0F)
        self._write_reg(REG_CONFIG_ADDR_MSB, (idx // 2) >> 4)
        return self._read_reg(REG_CONFIG_DATA, count)

    def _open_config_file(self):
        try:
            return open("bma423conf.bin", "rb")
        except OSError:
            base = globals().get("__file__", "")
            for sep in ("/", "\\"):
                if sep in base:
                    path = base.rsplit(sep, 1)[0] + sep + "bma423conf.bin"
                    try:
                        return open(path, "rb")
                    except OSError:
                        pass
        raise OSError("bma423conf.bin not found in current directory or driver directory")

    def _transfer_config(self) -> None:
        """
        通过 I2C 将 bma423conf.bin 二进制配置传输到 ASIC 存储器
        Raises:
            RuntimeError: 配置数据验证失败
            OSError: 配置文件读取失败
        Notes:
            - 传输完成后自动验证写入数据的完整性
            - ISR-safe: 否
        ==========================================
        Transfer bma423conf.bin binary config to ASIC memory via I2C.
        Raises:
            RuntimeError: Configuration data verification failed
            OSError: Configuration file read failed
        Notes:
            - Automatically verifies data integrity after transfer
            - ISR-safe: No
        """
        self._log("Uploading features configuration...")
        f = self._open_config_file()

        # 每次读取 8 字节，通过 I2C 写入 ASIC 存储器
        buf = bytearray(8)
        idx = 0
        while f.readinto(buf, 8) == 8:
            self._write_config_mem(idx, buf)
            idx += 8

        # 验证写入数据的完整性
        self._log("Verifying stored configuration...")
        f.seek(0)
        idx = 0
        while f.readinto(buf, 8) == 8:
            content = self._read_config_mem(idx, 8)
            idx += 8
            if content != buf:
                f.close()
                raise RuntimeError("Feature config data mismatch at offset %d" % idx)
        f.close()
        self._log("Config transferred: %d bytes" % idx)

    def _read_features_in(self) -> None:
        """
        从设备读取 FEATURES_IN 配置区域到内部缓冲区
        Notes:
            - 副作用：覆盖 self._features_in 的内容
            - ISR-safe: 否
        ==========================================
        Read FEATURES_IN configuration area from device.
        Notes:
            - Side effect: Overwrites self._features_in buffer
            - ISR-safe: No
        """
        for attempt in range(I2C_RETRIES + 1):
            try:
                self._i2c.readfrom_mem_into(self._addr, 0x5E, self._features_in)
                return
            except OSError as e:
                if attempt == I2C_RETRIES:
                    raise RuntimeError("Failed to read FEATURES_IN") from e
                time.sleep_ms(I2C_RETRY_DELAY_MS)

    def _write_features_in(self) -> None:
        """
        将内部缓冲区写入设备 FEATURES_IN 配置区域
        Notes:
            - 副作用：修改设备 FEATURES_IN 存储器内容
            - ISR-safe: 否
        ==========================================
        Write internal buffer to device FEATURES_IN area.
        Notes:
            - Side effect: Modifies device FEATURES_IN memory
            - ISR-safe: No
        """
        for attempt in range(I2C_RETRIES + 1):
            try:
                self._i2c.writeto_mem(self._addr, 0x5E, self._features_in)
                return
            except OSError as e:
                if attempt == I2C_RETRIES:
                    raise RuntimeError("Failed to write FEATURES_IN") from e
                time.sleep_ms(I2C_RETRY_DELAY_MS)

    def _irq_handler(self, pin) -> None:
        """Record an interrupt edge without allocation, I/O, or callbacks.

        Call process_irq() from a task or main loop to run the registered callback.
        """
        self._irq_pending = True

    def process_irq(self) -> bool:
        """Dispatch one pending IRQ callback in task/main-loop context."""
        if not self._irq_pending:
            return False
        self._irq_pending = False
        callback = self._callback
        if callback is not None:
            callback(None)
        return True

    # Source-compatible public API alias; this routine configures hardware outside ISR context.
    enable_interrupt = configure_events

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
