# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/16 18:00
# @Author  : 侯钧瀚
# @File    : heartratemonitor.py
# @Description : MAX30102/MAX30105 心率与PPG读取驱动 + 简易心率计算器（窗口平滑+峰值检测）
# @Repository  : 参考自：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : MIT

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入i2c类
from machine import I2C
# 导入ustruct
from ustruct import unpack
# 导入关于时间
import time
# 导入双端队列
from ucollections import deque
#导入常量
from micropython import const

# ======================================== 全局变量 ============================================

# I2C 地址（7位）
# 设备地址
MAX3010X_I2C_ADDRESS = const(0x57)  # 0xAE/0xAF 右移得到

# 状态寄存器
MAX30105_INT_STAT_1      = const(0x00)
MAX30105_INT_STAT_2      = const(0x01)
MAX30105_INT_ENABLE_1    = const(0x02)
MAX30105_INT_ENABLE_2    = const(0x03)

# FIFO 寄存器
MAX30105_FIFO_WRITE_PTR  = const(0x04)
MAX30105_FIFO_OVERFLOW   = const(0x05)
MAX30105_FIFO_READ_PTR   = const(0x06)
MAX30105_FIFO_DATA       = const(0x07)

# 配置寄存器
MAX30105_FIFO_CONFIG         = const(0x08)
MAX30105_MODE_CONFIG         = const(0x09)
MAX30105_PARTICLE_CONFIG     = const(0x0A)  # 数据手册 p.11 亦称 SPO2
MAX30105_LED1_PULSE_AMP      = const(0x0C)  # IR
MAX30105_LED2_PULSE_AMP      = const(0x0D)  # RED
MAX30105_LED3_PULSE_AMP      = const(0x0E)  # GREEN（若芯片支持）
MAX30105_LED_PROX_AMP        = const(0x10)
MAX30105_MULTI_LED_CONFIG_1  = const(0x11)
MAX30105_MULTI_LED_CONFIG_2  = const(0x12)

# 芯片温度寄存器
MAX30105_DIE_TEMP_INT    = const(0x1F)
MAX30105_DIE_TEMP_FRAC   = const(0x20)
MAX30105_DIE_TEMP_CONFIG = const(0x21)

# 接近检测门限寄存器
MAX30105_PROX_INT_THRESH = const(0x30)

# 器件信息寄存器
MAX30105_REVISION_ID     = const(0xFE)
MAX30105_PART_ID         = const(0xFF)  # 读数应为 0x15，与 MAX30102 相同
MAX_30105_EXPECTED_PART_ID = const(0x15)  # 兼容原命名

# 中断配置（参见数据手册 p.13, p.14）
MAX30105_INT_A_FULL_MASK        = const(0x7F)  # ~0b10000000
MAX30105_INT_A_FULL_ENABLE      = const(0x80)
MAX30105_INT_A_FULL_DISABLE     = const(0x00)

MAX30105_INT_DATA_RDY_MASK      = const(0xBF)  # ~0b01000000
MAX30105_INT_DATA_RDY_ENABLE    = const(0x40)
MAX30105_INT_DATA_RDY_DISABLE   = const(0x00)

MAX30105_INT_ALC_OVF_MASK       = const(0xDF)  # ~0b00100000
MAX30105_INT_ALC_OVF_ENABLE     = const(0x20)
MAX30105_INT_ALC_OVF_DISABLE    = const(0x00)

MAX30105_INT_PROX_INT_MASK      = const(0xEF)  # ~0b00010000
MAX30105_INT_PROX_INT_ENABLE    = const(0x10)
MAX30105_INT_PROX_INT_DISABLE   = const(0x00)

MAX30105_INT_DIE_TEMP_RDY_MASK  = const(0xFD)  # ~0b00000010
MAX30105_INT_DIE_TEMP_RDY_ENABLE= const(0x02)
MAX30105_INT_DIE_TEMP_RDY_DISABLE= const(0x00)

# FIFO 队列配置
MAX30105_SAMPLE_AVG_MASK    = const(0x1F)  # ~0b11100000
MAX30105_SAMPLE_AVG_1       = const(0x00)
MAX30105_SAMPLE_AVG_2       = const(0x20)
MAX30105_SAMPLE_AVG_4       = const(0x40)
MAX30105_SAMPLE_AVG_8       = const(0x60)
MAX30105_SAMPLE_AVG_16      = const(0x80)
MAX30105_SAMPLE_AVG_32      = const(0xA0)

MAX30105_ROLLOVER_MASK      = const(0xEF)
MAX30105_ROLLOVER_ENABLE    = const(0x10)
MAX30105_ROLLOVER_DISABLE   = const(0x00)

# “接近满”中断的掩码（默认 32 个样本）
MAX30105_A_FULL_MASK        = const(0xF0)

# 模式配置（p.19）
MAX30105_SHUTDOWN_MASK      = const(0x7F)
MAX30105_SHUTDOWN           = const(0x80)
MAX30105_WAKEUP             = const(0x00)

MAX30105_RESET_MASK         = const(0xBF)
MAX30105_RESET              = const(0x40)

MAX30105_MODE_MASK          = const(0xF8)
MAX30105_MODE_RED_ONLY      = const(0x02)
MAX30105_MODE_RED_IR_ONLY   = const(0x03)
MAX30105_MODE_MULTI_LED     = const(0x07)

# 粒子感应配置（p.19-20）
MAX30105_ADC_RANGE_MASK     = const(0x9F)
MAX30105_ADC_RANGE_2048     = const(0x00)
MAX30105_ADC_RANGE_4096     = const(0x20)
MAX30105_ADC_RANGE_8192     = const(0x40)
MAX30105_ADC_RANGE_16384    = const(0x60)

MAX30105_SAMPLERATE_MASK    = const(0xE3)
MAX30105_SAMPLERATE_50      = const(0x00)
MAX30105_SAMPLERATE_100     = const(0x04)
MAX30105_SAMPLERATE_200     = const(0x08)
MAX30105_SAMPLERATE_400     = const(0x0C)
MAX30105_SAMPLERATE_800     = const(0x10)
MAX30105_SAMPLERATE_1000    = const(0x14)
MAX30105_SAMPLERATE_1600    = const(0x18)
MAX30105_SAMPLERATE_3200    = const(0x1C)

MAX30105_PULSE_WIDTH_MASK   = const(0xFC)
MAX30105_PULSE_WIDTH_69     = const(0x00)
MAX30105_PULSE_WIDTH_118    = const(0x01)
MAX30105_PULSE_WIDTH_215    = const(0x02)
MAX30105_PULSE_WIDTH_411    = const(0x03)

# LED 电流档位（影响探测距离）
MAX30105_PULSE_AMP_LOWEST   = const(0x02)  # 0.4mA  ~4 inch
MAX30105_PULSE_AMP_LOW      = const(0x1F)  # 6.4mA  ~8 inch
MAX30105_PULSE_AMP_MEDIUM   = const(0x7F)  # 25.4mA ~8 inch
MAX30105_PULSE_AMP_HIGH     = const(0xFF)  # 50.0mA ~12 inch

# 多路 LED 模式配置（p.22）
MAX30105_SLOT1_MASK         = const(0xF8)
MAX30105_SLOT2_MASK         = const(0x8F)
MAX30105_SLOT3_MASK         = const(0xF8)
MAX30105_SLOT4_MASK         = const(0x8F)

SLOT_NONE                   = const(0x00)
SLOT_RED_LED                = const(0x01)
SLOT_IR_LED                 = const(0x02)
SLOT_GREEN_LED              = const(0x03)
SLOT_NONE_PILOT             = const(0x04)
SLOT_RED_PILOT              = const(0x05)
SLOT_IR_PILOT               = const(0x06)
SLOT_GREEN_PILOT            = const(0x07)

# 读取缓冲区大小（每色通道）
STORAGE_QUEUE_SIZE = const(4)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class HeartRateMonitor:
    """
    简易心率监测器：对输入样本做滑动窗口平滑与阈值峰值检测，估计 BPM。

    Attributes:
        sample_rate (int): 采样率（Hz）。
        window_size (int): 峰值检测窗口大小（样本数）。
        smoothing_window (int): 平滑窗口大小（样本数）。
        samples (list[float]): 原始样本序列。
        timestamps (list[int]): 样本的时间戳（ms, 使用 time.ticks_ms）。
        filtered_samples (list[float]): 平滑后的样本序列。

    Methods:
        add_sample(sample): 添加一个样本并更新平滑序列。
        find_peaks(): 在平滑序列中查找峰值点。
        calculate_heart_rate(): 根据相邻峰值时间差计算 BPM。

    Notes:
        - 峰值阈值采用近期窗口的动态阈值（min/max 的 50% 中点）。
        - 需要至少两个峰值才能计算心率。

    =========================================
    A light-weight HR monitor performing moving-window smoothing and threshold
    peak detection to estimate BPM.

    Attributes:
        sample_rate (int): Sampling rate in Hz.
        window_size (int): Peak detection window length in samples.
        smoothing_window (int): Moving average window length.
        samples (list[float]): Raw samples.
        timestamps (list[int]): Sample timestamps in ms (time.ticks_ms).
        filtered_samples (list[float]): Smoothed samples.

    Methods:
        add_sample(sample): Append a sample and update the smoothed list.
        find_peaks(): Detect peaks on the smoothed series.
        calculate_heart_rate(): Compute BPM from peak intervals.

    Notes:
        - The threshold is 50% between min and max of the recent window.
        - At least two peaks are required to compute BPM.
    """

    def __init__(self, sample_rate=100, window_size=10, smoothing_window=5):
        """
        初始化。

        Args:
            sample_rate (int): 采样率（Hz）。
            window_size (int): 峰值检测窗口大小。
            smoothing_window (int): 平滑窗口大小。

        Raises:
            ValueError: 当任一参数 <= 0。

        =========================================
        Initialize the monitor.

        Args:
            sample_rate (int): Sampling rate in Hz.
            window_size (int): Peak-detection window length.
            smoothing_window (int): Moving average window length.

        Raises:
            ValueError: If any parameter <= 0.
        """
        if sample_rate <= 0 or window_size <= 0 or smoothing_window <= 0:
            raise ValueError("sample_rate/window_size/smoothing_window must be > 0")
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.smoothing_window = smoothing_window
        self.samples = []
        self.timestamps = []
        self.filtered_samples = []

    def add_sample(self, sample):
        """
        添加一个新样本并更新平滑结果。

        Args:
            sample (float|int): 原始样本值。
        Raises:
            TypeError: 如果 sample 不是 int 或 float。
        =========================================
        Add a new sample and update the smoothed value.

        Args:
            sample (float|int): Raw sample value.
        Raises:
            TypeError: If sample is not int or float.
        """
        if not isinstance(sample, (int, float)):
            raise TypeError("sample must be an int or float")
        timestamp = time.ticks_ms()
        self.samples.append(sample)
        self.timestamps.append(timestamp)

        # 应用简单移动平均平滑
        if len(self.samples) >= self.smoothing_window:
            smoothed_sample = (
                sum(self.samples[-self.smoothing_window :]) / self.smoothing_window
            )
            self.filtered_samples.append(smoothed_sample)
        else:
            self.filtered_samples.append(sample)

        # 限制窗口长度
        if len(self.samples) > self.window_size:
            self.samples.pop(0)
            self.timestamps.pop(0)
            self.filtered_samples.pop(0)

    def find_peaks(self):
        """
        在平滑序列中查找峰值（基于动态阈值的三点法）。

        Returns:
            list[tuple[int, float]]: 峰值列表，每项为 (时间戳ms, 峰值幅度)。

        =========================================
        Find peaks on the smoothed samples using a simple three-point test with
        a dynamic threshold.

        Returns:
            list[tuple[int, float]]: Peaks as (timestamp_ms, amplitude).
        """
        peaks = []

        # 至少 3 个点才能判断峰值
        if len(self.filtered_samples) < 3:
            return peaks

        # 取最近窗口的最小/最大计算动态阈值
        recent_samples = self.filtered_samples[-self.window_size :]
        min_val = min(recent_samples)
        max_val = max(recent_samples)
        threshold = min_val + (max_val - min_val) * 0.5  # 50% 中点阈值

        for i in range(1, len(self.filtered_samples) - 1):
            if (
                self.filtered_samples[i] > threshold
                and self.filtered_samples[i - 1] < self.filtered_samples[i]
                and self.filtered_samples[i] > self.filtered_samples[i + 1]
            ):
                peak_time = self.timestamps[i]
                peaks.append((peak_time, self.filtered_samples[i]))

        return peaks

    def calculate_heart_rate(self):
        """
        计算心率（BPM）。

        Returns:
            float|None: 若峰值不足则返回 None，否则返回 BPM。

        =========================================
        Compute heart rate in BPM.

        Returns:
            float|None: BPM or None if not enough peaks are found.
        """
        peaks = self.find_peaks()

        # 峰值数不足
        if len(peaks) < 2:
            return None

        # 计算相邻峰值的平均间隔（ms）
        intervals = []
        for i in range(1, len(peaks)):
            interval = time.ticks_diff(peaks[i][0], peaks[i - 1][0])
            intervals.append(interval)

        average_interval = sum(intervals) / len(intervals)

        # 转换为 BPM（60000ms/分钟）
        heart_rate = 60000 / average_interval
        return heart_rate

class SensorData:
    """
    传感器数据缓存（环形队列）。

    Attributes:
        red (CircularBuffer): 红光通道缓存。
        IR (CircularBuffer): 红外通道缓存。
        green (CircularBuffer): 绿光通道缓存。

    =========================================
    Sensor data container backed by ring buffers.

    Attributes:
        red (CircularBuffer): Red channel buffer.
        IR (CircularBuffer): Infrared channel buffer.
        green (CircularBuffer): Green channel buffer.
    """

    def __init__(self):
        """
        初始化环形缓冲区。

        =========================================
        Initialize ring buffers for each channel.
        """
        self.red = CircularBuffer(STORAGE_QUEUE_SIZE)
        self.IR = CircularBuffer(STORAGE_QUEUE_SIZE)
        self.green = CircularBuffer(STORAGE_QUEUE_SIZE)

class MAX30102(object):
    """
    MAX30102/MAX30105 传感器 I2C 驱动（寄存器配置、FIFO 读取、温度读取等）。

    Attributes:
        i2c_address (int): I2C 地址（7 位）。
        _i2c (I2C): MicroPython I2C 实例。
        _active_leds (int|None): 当前启用的 LED 数量（1~3）。
        _pulse_width (int|None): 当前脉宽编码（寄存器位值）。
        _multi_led_read_mode (int|None): 每次 FIFO 读取的字节数（active_leds*3）。
        _sample_rate (int|None): 采样率（SPS）。
        _sample_avg (int|None): FIFO 内部平均的样本数。
        _acq_frequency (float|None): 有效采集频率（_sample_rate/_sample_avg）。
        _acq_frequency_inv (int|None): 建议读取间隔（ms）。
        sense (SensorData): 各通道环形缓存。

    Methods:
        setup_sensor(...): 一次性按常用配置初始化。
        soft_reset(): 软复位。
        shutdown()/wakeup(): 掉电/唤醒。
        set_led_mode()/set_adc_range()/set_sample_rate()/set_pulse_width(): 基本配置。
        set_pulse_amplitude_*(): LED 电流设置。
        set_fifo_average()/enable_fifo_rollover()/clear_fifo(): FIFO 管理。
        get_write_pointer()/get_read_pointer(): FIFO 指针读。
        read_temperature(): 读芯片温度。
        read_part_id()/check_part_id()/get_revision_id(): 器件信息。
        enable_slot()/disable_slots(): 多路 LED 时间槽配置。
        check()/safe_check(): 轮询新数据。

    Notes:
        - 本驱动未改动核心业务逻辑，仅补齐注释与文档；
        - "set_pulse_amplitude_it" 方法名沿用原代码（IR 电流），未更名以避免影响业务；
        - I2C 读写可能抛出 OSError（如 ETIMEDOUT）。

    =========================================
    I2C driver for MAX30102/30105 (register/config/FIFO/temperature, etc.).

    Attributes:
        i2c_address (int): 7-bit I2C address.
        _i2c (I2C): MicroPython I2C instance.
        _active_leds (int|None): Number of active LEDs (1..3).
        _pulse_width (int|None): Encoded pulse width (register value).
        _multi_led_read_mode (int|None): Bytes per FIFO read (active_leds*3).
        _sample_rate (int|None): Sample rate in SPS.
        _sample_avg (int|None): FIFO on-chip averaging.
        _acq_frequency (float|None): Effective acquisition rate.
        _acq_frequency_inv (int|None): Suggested read interval (ms).
        sense (SensorData): Channel ring buffers.

    Methods:
        setup_sensor(...): Initialize once with common configurations.
        soft_reset(): Soft reset.
        shutdown()/wakeup(): Power down/wake up.
        set_led_mode()/set_adc_range()/set_sample_rate()/set_pulse_width(): Basic configurations.
        set_pulse_amplitude_*(): LED current setting.
        set_fifo_average()/enable_fifo_rollover()/clear_fifo(): FIFO management.
        get_write_pointer()/get_read_pointer(): FIFO pointer reading.
        read_temperature(): Read chip temperature.
        read_part_id()/

    Notes:
        - Core logic unchanged; only documentation/comments were added;
        - The method name "set_pulse_amplitude_it" is kept as-is (IR current);
        - I2C ops may raise OSError (e.g., ETIMEDOUT).
    """

    def __init__(self, i2c: I2C, i2c_hex_address=MAX3010X_I2C_ADDRESS):
        """
        构造函数，用于初始化 MAX3010X 传感器实例。

        Args:
            i2c (I2C): I2C 实例。
            i2c_hex_address (int): 器件地址（7 位，默认 0x57）。

        Raises:
            TypeError: 如果 i2c 不是 I2C 实例，或者 i2c_hex_address 不是 int。
            ValueError: 如果 i2c_hex_address 不在 0x00~0x7F 范围内。

        =========================================
        Constructor for MAX3010X sensor instance.

        Args:
            i2c (I2C): I2C instance.
            i2c_hex_address (int): 7-bit device address (default 0x57).

        Raises:
            TypeError: If i2c is not an I2C instance or i2c_hex_address is not an int.
            ValueError: If i2c_hex_address is not in the range 0x00–0x7F.
        """

        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an instance of I2C")
        if not isinstance(i2c_hex_address, int):
            raise TypeError("i2c_hex_address must be an int")

            # 地址范围检查（I2C 7-bit 地址）
        if not 0x00 <= i2c_hex_address <= 0x7F:
            raise ValueError("i2c_hex_address must be in 0x00–0x7F")
        self.i2c_address = i2c_hex_address
        self._i2c = i2c
        self._active_leds = None
        self._pulse_width = None
        self._multi_led_read_mode = None
        # 当前配置用于计算采样频率
        self._sample_rate = None
        self._sample_avg = None
        self._acq_frequency = None
        self._acq_frequency_inv = None
        # 传感器读数环形缓冲
        self.sense = SensorData()

    def setup_sensor(self, led_mode=2, adc_range=16384, sample_rate=400,
                     led_power=MAX30105_PULSE_AMP_MEDIUM, sample_avg=8,
                     pulse_width=411):
        """
        一次性按常用配置初始化设备并清 FIFO。

        Args:
            led_mode (int): 1=仅红，2=红+IR，3=红+IR+绿（30105）。
            adc_range (int): 2048/4096/8192/16384。
            sample_rate (int): 50~3200（SPS）。
            led_power (int): LED 电流寄存器值（0x02~0xFF）。
            sample_avg (int): FIFO 平均样本数（1/2/4/8/16/32）。
            pulse_width (int): 69/118/215/411（us）。

        Raises:
            TypeError: 参数类型不正确。
            ValueError: 参数值超出允许范围。

        =========================================
        Initialize sensor with common defaults and clear FIFO.

        Args:
            led_mode (int): 1=red, 2=red+IR, 3=red+IR+green (30105).
            adc_range (int): 2048/4096/8192/16384.
            sample_rate (int): 50..3200 SPS.
            led_power (int): LED current register value (0x02..0xFF).
            sample_avg (int): FIFO averaging (1/2/4/8/16/32).
            pulse_width (int): 69/118/215/411 us.

        Raises:
            TypeError: If any argument is not int.
            ValueError: If any argument is out of allowed range.
        """
        # 参数类型检查
        for arg_name, arg_value in [
            ("led_mode", led_mode),
            ("adc_range", adc_range),
            ("sample_rate", sample_rate),
            ("led_power", led_power),
            ("sample_avg", sample_avg),
            ("pulse_width", pulse_width),
        ]:
            if not isinstance(arg_value, int):
                raise TypeError(f"{arg_name} must be an int")

        # 参数值检查
        if led_mode not in (1, 2, 3):
            raise ValueError("led_mode must be 1, 2, or 3")
        if adc_range not in (2048, 4096, 8192, 16384):
            raise ValueError("adc_range must be one of 2048, 4096, 8192, 16384")
        if not 50 <= sample_rate <= 3200:
            raise ValueError("sample_rate must be between 50 and 3200")
        if not 0x02 <= led_power <= 0xFF:
            raise ValueError("led_power must be between 0x02 and 0xFF")
        if sample_avg not in (1, 2, 4, 8, 16, 32):
            raise ValueError("sample_avg must be 1,2,4,8,16,32")
        if pulse_width not in (69, 118, 215, 411):
            raise ValueError("pulse_width must be 69,118,215,411")

        # 软复位
        self.soft_reset()
        # FIFO 平均
        self.set_fifo_average(sample_avg)
        # 允许 FIFO 回绕
        self.enable_fifo_rollover()
        # LED 模式
        self.set_led_mode(led_mode)
        # ADC 量程
        self.set_adc_range(adc_range)
        # 采样率
        self.set_sample_rate(sample_rate)
        # 脉冲宽度
        self.set_pulse_width(pulse_width)
        # LED 电流
        self.set_pulse_amplitude_red(led_power)
        self.set_pulse_amplitude_it(led_power)
        self.set_pulse_amplitude_green(led_power)
        self.set_pulse_amplitude_proximity(led_power)
        # 清 FIFO
        self.clear_fifo()

    def __del__(self):
        """
        析构：设备转入低功耗。

        =========================================
        Destructor: put device into low power mode.
        """
        self.shutdown()

    def get_int_1(self):
        """
        读取中断状态寄存器 1。

        Returns:
            bytes: 原始寄存器值（1 字节）。

        =========================================
        Read interrupt status register 1.

        Returns:
            bytes: Raw register value (1 byte).
        """
        rev_id = self._i2c_read_register(MAX30105_INT_STAT_1)
        return rev_id

    def get_int_2(self):
        """
        读取中断状态寄存器 2。

        Returns:
            bytes: 原始寄存器值（1 字节）。

        =========================================
        Read interrupt status register 2.

        Returns:
            bytes: Raw register value (1 byte).
        """
        rev_id = self._i2c_read_register(MAX30105_INT_STAT_2)
        return rev_id

    def enable_a_full(self):
        """
        使能 FIFO 接近满中断。

        =========================================
        Enable the "almost full" FIFO interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_A_FULL_MASK, MAX30105_INT_A_FULL_ENABLE)

    def disable_a_full(self):
        """
        关闭 FIFO 接近满中断。

        =========================================
        Disable the "almost full" FIFO interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_A_FULL_MASK, MAX30105_INT_A_FULL_DISABLE)

    def enable_data_rdy(self):
        """
        使能新数据就绪中断。

        =========================================
        Enable the FIFO data-ready interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_DATA_RDY_MASK, MAX30105_INT_DATA_RDY_ENABLE)

    def disable_data_rdy(self):
        """
        关闭新数据就绪中断。

        =========================================
        Disable the FIFO data-ready interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_DATA_RDY_MASK, MAX30105_INT_DATA_RDY_DISABLE)

    def enable_alc_ovf(self):
        """
        使能环境光溢出中断。

        =========================================
        Enable ambient light overflow interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_ALC_OVF_MASK, MAX30105_INT_ALC_OVF_ENABLE)

    def disable_alc_ovf(self):
        """
        关闭环境光溢出中断。

        =========================================
        Disable ambient light overflow interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_ALC_OVF_MASK, MAX30105_INT_ALC_OVF_DISABLE)

    def enable_prox_int(self):
        """
        使能接近中断。

        =========================================
        Enable proximity interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_PROX_INT_MASK, MAX30105_INT_PROX_INT_ENABLE)

    def disable_prox_int(self):
        """
        关闭接近中断。

        =========================================
        Disable proximity interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_1, MAX30105_INT_PROX_INT_MASK, MAX30105_INT_PROX_INT_DISABLE)

    def enable_die_temp_rdy(self):
        """
        使能芯片温度完成中断。

        =========================================
        Enable die-temperature ready interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_2, MAX30105_INT_DIE_TEMP_RDY_MASK, MAX30105_INT_DIE_TEMP_RDY_ENABLE)

    def disable_die_temp_rdy(self):
        """
        关闭芯片温度完成中断。

        =========================================
        Disable die-temperature ready interrupt.
        """
        self.bitmask(MAX30105_INT_ENABLE_2, MAX30105_INT_DIE_TEMP_RDY_MASK, MAX30105_INT_DIE_TEMP_RDY_DISABLE)

    def soft_reset(self):
        """
        软复位（复位后等待 RESET 位自动清零）。

        =========================================
        Soft-reset the device and wait until the RESET bit clears.
        """
        self.set_bitmask(MAX30105_MODE_CONFIG, MAX30105_RESET_MASK, MAX30105_RESET)
        curr_status = -1
        while not ((curr_status & MAX30105_RESET) == 0):
            time.sleep_ms(10)
            curr_status = ord(self._i2c_read_register(MAX30105_MODE_CONFIG))

    def shutdown(self):
        """
        掉电进入低功耗（I2C 仍可访问，但不再更新测量）。

        =========================================
        Enter low-power shutdown (I2C remains responsive, measurements pause).
        """
        self.set_bitmask(MAX30105_MODE_CONFIG, MAX30105_SHUTDOWN_MASK, MAX30105_SHUTDOWN)

    def wakeup(self):
        """
        退出低功耗，恢复工作。

        =========================================
        Wake the device from shutdown.
        """
        self.set_bitmask(MAX30105_MODE_CONFIG, MAX30105_SHUTDOWN_MASK, MAX30105_WAKEUP)

    def set_led_mode(self, LED_mode):
        """
        设置 LED 采样模式。

        Args:
            LED_mode (int): 1=红；2=红+IR；3=红+IR+绿（仅 30105）。

        Raises:
            ValueError: 模式不支持。

        =========================================
        Set LED sampling mode.

        Args:
            LED_mode (int): 1=red; 2=red+IR; 3=red+IR+green (30105 only).

        Raises:
            ValueError: If mode not supported.
        """
        if LED_mode == 1:
            self.set_bitmask(MAX30105_MODE_CONFIG, MAX30105_MODE_MASK, MAX30105_MODE_RED_ONLY)
        elif LED_mode == 2:
            self.set_bitmask(MAX30105_MODE_CONFIG, MAX30105_MODE_MASK, MAX30105_MODE_RED_IR_ONLY)
        elif LED_mode == 3:
            self.set_bitmask(MAX30105_MODE_CONFIG, MAX30105_MODE_MASK, MAX30105_MODE_MULTI_LED)
        else:
            raise ValueError('Wrong LED mode:{0}!'.format(LED_mode))

        # 按模式设置时间槽
        self.enable_slot(1, SLOT_RED_LED)
        if LED_mode > 1:
            self.enable_slot(2, SLOT_IR_LED)
        if LED_mode > 2:
            self.enable_slot(3, SLOT_GREEN_LED)

        # 根据 LED 数决定 FIFO 一次读取的字节数（每 LED 3 字节）
        self._active_leds = LED_mode
        self._multi_led_read_mode = LED_mode * 3

    def set_adc_range(self, ADC_range):
        """
        设置 ADC 量程。

        Args:
            ADC_range (int): 2048/4096/8192/16384。

        Raises:
            ValueError: 量程不支持。

        =========================================
        Set ADC full-scale range.

        Args:
            ADC_range (int): 2048/4096/8192/16384.

        Raises:
            ValueError: If range not supported.
        """
        if ADC_range == 2048:
            r = MAX30105_ADC_RANGE_2048
        elif ADC_range == 4096:
            r = MAX30105_ADC_RANGE_4096
        elif ADC_range == 8192:
            r = MAX30105_ADC_RANGE_8192
        elif ADC_range == 16384:
            r = MAX30105_ADC_RANGE_16384
        else:
            raise ValueError('Wrong ADC range:{0}!'.format(ADC_range))

        self.set_bitmask(MAX30105_PARTICLE_CONFIG, MAX30105_ADC_RANGE_MASK, r)

    def set_sample_rate(self, sample_rate):

        """
        设置采样率（SPS）。

        Args:
            sample_rate (int): 50/100/200/400/800/1000/1600/3200。

        Raises:
            ValueError: 采样率不支持。

        =========================================
        Set sample rate (SPS).

        Args:
            sample_rate (int): 50/100/200/400/800/1000/1600/3200.

        Raises:
            ValueError: If rate not supported.
        """

        if sample_rate == 50:
            sr = MAX30105_SAMPLERATE_50
        elif sample_rate == 100:
            sr = MAX30105_SAMPLERATE_100
        elif sample_rate == 200:
            sr = MAX30105_SAMPLERATE_200
        elif sample_rate == 400:
            sr = MAX30105_SAMPLERATE_400
        elif sample_rate == 800:
            sr = MAX30105_SAMPLERATE_800
        elif sample_rate == 1000:
            sr = MAX30105_SAMPLERATE_1000
        elif sample_rate == 1600:
            sr = MAX30105_SAMPLERATE_1600
        elif sample_rate == 3200:
            sr = MAX30105_SAMPLERATE_3200
        else:
            raise ValueError('Wrong sample rate:{0}!'.format(sample_rate))

        self.set_bitmask(MAX30105_PARTICLE_CONFIG, MAX30105_SAMPLERATE_MASK, sr)
        # 保存采样率并刷新有效采集频率
        self._sample_rate = sample_rate
        self.update_acquisition_frequency()

    def set_pulse_width(self, pulse_width):

        """
        设置 LED 脉冲宽度（影响探测距离）。

        Args:
            pulse_width (int): 69/118/215/411。

        Raises:
            ValueError: 脉宽不支持。

        =========================================
        Set LED pulse width (affects detection range).

        Args:
            pulse_width (int): 69/118/215/411.

        Raises:
            ValueError: If width not supported.
        """

        if pulse_width == 69:
            pw = MAX30105_PULSE_WIDTH_69
        elif pulse_width == 118:
            pw = MAX30105_PULSE_WIDTH_118
        elif pulse_width == 215:
            pw = MAX30105_PULSE_WIDTH_215
        elif pulse_width == 411:
            pw = MAX30105_PULSE_WIDTH_411
        else:
            raise ValueError('Wrong pulse width:{0}!'.format(pulse_width))
        self.set_bitmask(MAX30105_PARTICLE_CONFIG, MAX30105_PULSE_WIDTH_MASK, pw)
        self._pulse_width = pw

    def set_active_leds_amplitude(self, amplitude):
        """
            按当前启用的 LED 数量批量设置电流。

            Args:
                amplitude (int): 电流寄存器值（0x02~0xFF）。

            Raises:
                TypeError: 如果 amplitude 不是 int 类型。
                ValueError: 如果 amplitude 不在 0x02~0xFF 范围内。

            =========================================
            Set LED current for all active LEDs.

            Args:
                amplitude (int): Current register value (0x02..0xFF).

            Raises:
                TypeError: If amplitude is not an int.
                ValueError: If amplitude is not in the range 0x02–0xFF.
            """
        # 参数类型检查
        if not isinstance(amplitude, int):
            raise TypeError("amplitude must be an int")
        # 参数值检查
        if not 0x02 <= amplitude <= 0xFF:
            raise ValueError("amplitude must be between 0x02 and 0xFF")
        if self._active_leds and self._active_leds > 0:
            self.set_pulse_amplitude_red(amplitude)
        if self._active_leds and self._active_leds > 1:
            self.set_pulse_amplitude_it(amplitude)
        if self._active_leds and self._active_leds > 2:
            self.set_pulse_amplitude_green(amplitude)

    def set_pulse_amplitude_red(self, amplitude):

        """
        设置红光 LED 电流。

        Args:
            amplitude (int): 电流寄存器值（0x02~0xFF）。

        Raises:
            TypeError: 如果 amplitude 不是 int 类型。
            ValueError: 如果 amplitude 不在 0x02~0xFF 范围内。

        =========================================
        Set RED LED current.

        Args:
            amplitude (int): Current register value (0x02..0xFF).

        Raises:
            TypeError: If amplitude is not an int.
            ValueError: If amplitude is not in the range 0x02–0xFF.
        """
        if not isinstance(amplitude, int):
            raise TypeError("amplitude must be an int")
            # 参数值检查
        if not 0x02 <= amplitude <= 0xFF:
            raise ValueError("amplitude must be between 0x02 and 0xFF")
        self._i2c_set_register(MAX30105_LED1_PULSE_AMP, amplitude)

    def set_pulse_amplitude_it(self, amplitude):

        """
        设置 IR LED 电流（沿用原方法名 it）。

        Args:
            amplitude (int): 电流寄存器值。
        Raises:
            TypeError: 如果 amplitude 不是 int 类型。
            ValueError: 如果 amplitude 不在 0x02~0xFF 范围内。

        =========================================
        Set IR LED current (method name kept as 'it').

        Args:
            amplitude (int): Current register value.
        Raises:
            TypeError: If amplitude is not an int.
            ValueError: If amplitude is not in the range 0x02–0xFF.
        """
        if not isinstance(amplitude, int):
            raise TypeError("amplitude must be an int")
            # 参数值检查
        if not 0x02 <= amplitude <= 0xFF:
            raise ValueError("amplitude must be between 0x02 and 0xFF")
        self._i2c_set_register(MAX30105_LED2_PULSE_AMP, amplitude)

    def set_pulse_amplitude_green(self, amplitude):

        """
        设置绿光 LED 电流（若芯片支持）。

        Args:
            amplitude (int): 电流寄存器值。
        Raises:
            TypeError: 如果 amplitude 不是 int 类型。
            ValueError: 如果 amplitude 不在 0x02~0xFF 范围内。
        =========================================
        Set GREEN LED current (if available).

        Args:
            amplitude (int): Current register value.
        Raises:
            TypeError: If amplitude is not an int.
            ValueError: If amplitude is not in the range 0x02–0xFF.
        """
        if not isinstance(amplitude, int):
            raise TypeError("amplitude must be an int")
            # 参数值检查
        if not 0x02 <= amplitude <= 0xFF:
            raise ValueError("amplitude must be between 0x02 and 0xFF")
        self._i2c_set_register(MAX30105_LED3_PULSE_AMP, amplitude)

    def set_pulse_amplitude_proximity(self, amplitude):

        """
        设置接近检测 LED 电流。

        Args:
            amplitude (int): 电流寄存器值。
        Raises:
            TypeError: 如果 amplitude 不是 int 类型。
            ValueError: 如果 amplitude 不在 0x02~0xFF 范围内。

        =========================================
        Set proximity LED current.

        Args:
            amplitude (int): Current register value.
        Raises:
            TypeError: If amplitude is not an int.
            ValueError: If amplitude is not in the range 0x02–0xFF.
        """
        if not isinstance(amplitude, int):
            raise TypeError("amplitude must be an int")
            # 参数值检查
        if not 0x02 <= amplitude <= 0xFF:
            raise ValueError("amplitude must be between 0x02 and 0xFF")
        self._i2c_set_register(MAX30105_LED3_PULSE_AMP, amplitude)
        self._i2c_set_register(MAX30105_LED_PROX_AMP, amplitude)

    def set_proximity_threshold(self, thresh_msb):
        """
        设置接近中断门限的高 8 位。

        Args:
            thresh_msb (int): 门限高 8 位（0x00~0xFF）。

        Raises:
            TypeError: 如果 thresh_msb 不是 int 类型。
            ValueError: 如果 thresh_msb 不在 0x00~0xFF 范围内。

        =========================================
        Set MSB part of proximity interrupt threshold.

        Args:
            thresh_msb (int): Threshold MSB value (0x00..0xFF).

        Raises:
            TypeError: If thresh_msb is not an int.
            ValueError: If thresh_msb is not in the range 0x00–0xFF.
        """
        # 类型检查
        if not isinstance(thresh_msb, int):
            raise TypeError("thresh_msb must be an int")
        # 值域检查
        if not 0x00 <= thresh_msb <= 0xFF:
            raise ValueError("thresh_msb must be between 0x00 and 0xFF")

        self._i2c_set_register(MAX30105_PROX_INT_THRESH, thresh_msb)

    def set_fifo_average(self, number_of_samples):

        """
        设置 FIFO 内部平均样本数。

        Args:
            number_of_samples (int): 1/2/4/8/16/32。

        Raises:
            ValueError: 不支持的平均样本数。

        =========================================
        Set FIFO on-chip averaging.

        Args:
            number_of_samples (int): 1/2/4/8/16/32.

        Raises:
            ValueError: If not supported.
        """

        if number_of_samples == 1:
            ns = MAX30105_SAMPLE_AVG_1
        elif number_of_samples == 2:
            ns = MAX30105_SAMPLE_AVG_2
        elif number_of_samples == 4:
            ns = MAX30105_SAMPLE_AVG_4
        elif number_of_samples == 8:
            ns = MAX30105_SAMPLE_AVG_8
        elif number_of_samples == 16:
            ns = MAX30105_SAMPLE_AVG_16
        elif number_of_samples == 32:
            ns = MAX30105_SAMPLE_AVG_32
        else:
            raise ValueError('Wrong number of samples:{0}!'.format(number_of_samples))
        self.set_bitmask(MAX30105_FIFO_CONFIG, MAX30105_SAMPLE_AVG_MASK, ns)
        # 保存并更新有效采集频率
        self._sample_avg = number_of_samples
        self.update_acquisition_frequency()

    def update_acquisition_frequency(self):

        """
        根据采样率与平均样本数计算有效采集频率与建议读取间隔。

        =========================================
        Update effective acquisition frequency and suggested read interval.
        """

        if None in [self._sample_rate, self._sample_avg]:
            return
        else:
            self._acq_frequency = self._sample_rate / self._sample_avg
            from math import ceil
            # 建议的读取间隔（ms）
            self._acq_frequency_inv = int(ceil(1000 / self._acq_frequency))

    def get_acquisition_frequency(self):

        """
        获取有效采集频率（SPS）。

        Returns:
            float|None: 采集频率。

        =========================================
        Get effective acquisition frequency in SPS.

        Returns:
            float|None: Frequency.
        """

        return self._acq_frequency

    def clear_fifo(self):

        """
        清空 FIFO 指针（推荐在开始读取前执行）。

        =========================================
        Clear FIFO pointers (recommended before starting reads).
        """
        self._i2c_set_register(MAX30105_FIFO_WRITE_PTR, 0)
        self._i2c_set_register(MAX30105_FIFO_OVERFLOW, 0)
        self._i2c_set_register(MAX30105_FIFO_READ_PTR, 0)

    def enable_fifo_rollover(self):

        """
        允许 FIFO 回绕覆盖旧数据。

        =========================================
        Enable FIFO rollover.
        """

        self.set_bitmask(MAX30105_FIFO_CONFIG, MAX30105_ROLLOVER_MASK, MAX30105_ROLLOVER_ENABLE)

    def disable_fifo_rollover(self):

        """
        禁止 FIFO 回绕。

        =========================================
        Disable FIFO rollover.
        """

        self.set_bitmask(MAX30105_FIFO_CONFIG, MAX30105_ROLLOVER_MASK, MAX30105_ROLLOVER_DISABLE)

    def set_fifo_almost_full(self, number_of_samples):

        """
        设置触发“接近满”中断的剩余空间阈值（反向编码）。

        Args:
            number_of_samples (int): 0x00=32 样本，0x0F=17 样本。

        =========================================
        Configure the threshold for "almost full" interrupt (reverse encoded).

        Args:
            number_of_samples (int): 0x00=32 samples, 0x0F=17 samples.
        """

        self.set_bitmask(MAX30105_FIFO_CONFIG, MAX30105_A_FULL_MASK, number_of_samples)

    def get_write_pointer(self):

        """
        读取 FIFO 写指针。

        Returns:
            bytes: 指针寄存器值（1 字节）。

        =========================================
        Read FIFO write pointer.

        Returns:
            bytes: Register value (1 byte).
        """
        wp = self._i2c_read_register(MAX30105_FIFO_WRITE_PTR)
        return wp

    def get_read_pointer(self):

        """
        读取 FIFO 读指针。

        Returns:
            bytes: 指针寄存器值（1 字节）。

        =========================================
        Read FIFO read pointer.

        Returns:
            bytes: Register value (1 byte).
        """
        wp = self._i2c_read_register(MAX30105_FIFO_READ_PTR)
        return wp

    def read_temperature(self):

        """
        读取芯片内部温度（℃）。

        Returns:
            float: 摄氏温度。

        =========================================
        Read die temperature in Celsius.

        Returns:
            float: Temperature in °C.
        """

        # 触发一次温度转换
        self._i2c_set_register(MAX30105_DIE_TEMP_CONFIG, 0x01)
        # 轮询完成位清零
        reading = ord(self._i2c_read_register(MAX30105_INT_STAT_2))
        time.sleep_ms(100)
        while (reading & MAX30105_INT_DIE_TEMP_RDY_ENABLE) > 0:
            reading = ord(self._i2c_read_register(MAX30105_INT_STAT_2))
        time.sleep_ms(1)
        # 读取整数与小数部分
        tempInt = ord(self._i2c_read_register(MAX30105_DIE_TEMP_INT))
        tempFrac = ord(self._i2c_read_register(MAX30105_DIE_TEMP_FRAC))
        return float(tempInt) + (float(tempFrac) * 0.0625)

    def set_prox_int_tresh(self, val):
        """
        设置接近中断门限。

        Args:
            val (int): 门限高 8 位（0x00~0xFF）。

        Raises:
            TypeError: 如果 val 不是 int 类型。
            ValueError: 如果 val 不在 0x00~0xFF 范围内。

        =========================================
        Set proximity interrupt threshold (alias of set_proximity_threshold).

        Args:
            val (int): Threshold MSB value (0x00..0xFF).

        Raises:
            TypeError: If val is not an int.
            ValueError: If val is not in the range 0x00–0xFF.
        """
        # 类型检查
        if not isinstance(val, int):
            raise TypeError("val must be an int")
        # 值域检查
        if not 0x00 <= val <= 0xFF:
            raise ValueError("val must be between 0x00 and 0xFF")

        self._i2c_set_register(MAX30105_PROX_INT_THRESH, val)

    def read_part_id(self):
        
        """
        读取器件 ID。

        Returns:
            bytes: ID 寄存器（1 字节）。

        =========================================
        Read part ID register.

        Returns:
            bytes: 1-byte value.
        """
        part_id = self._i2c_read_register(MAX30105_PART_ID)
        return part_id

    def check_part_id(self):

        """
        校验器件 ID 是否为预期值（0x15）。

        Returns:
            bool: 是否匹配。

        =========================================
        Check if part ID equals expected value (0x15).

        Returns:
            bool: True if matched.
        """

        part_id = ord(self.read_part_id())
        return part_id == MAX_30105_EXPECTED_PART_ID

    def get_revision_id(self):

        """
        读取修订 ID。

        Returns:
            int: 修订号。

        =========================================
        Read revision ID.

        Returns:
            int: Revision number.
        """
        rev_id = self._i2c_read_register(MAX30105_REVISION_ID)
        return ord(rev_id)

    def enable_slot(self, slot_number, device):
        """
        在多路 LED 模式下配置时间槽。

        Args:
            slot_number (int): 槽位 1..4。
            device (int): 槽位绑定：SLOT_* 常量之一。

        Raises:
            TypeError: 如果 device 不是 int。
            ValueError: 槽位编号不在 1..4，或 device 不在允许范围。

        =========================================
        Configure time slots for multi-LED mode.

        Args:
            slot_number (int): Slot index 1..4.
            device (int): One of SLOT_* constants.

        Raises:
            TypeError: If device is not an int.
            ValueError: If slot_number not in 1..4 or device invalid.
        """
        # slot_number 检查
        if slot_number not in (1, 2, 3, 4):
            raise ValueError(f"Wrong slot number: {slot_number}!")

        # device 类型和值检查
        allowed_devices = (SLOT_RED_LED, SLOT_IR_LED, SLOT_GREEN_LED, SLOT_NONE)  # 根据实际常量定义
        if not isinstance(device, int):
            raise TypeError("device must be an int")
        if device not in allowed_devices:
            raise ValueError(f"Invalid device: {device}, must be one of {allowed_devices}")

        # 配置寄存器
        if slot_number == 1:
            self.bitmask(MAX30105_MULTI_LED_CONFIG_1, MAX30105_SLOT1_MASK, device)
        elif slot_number == 2:
            self.bitmask(MAX30105_MULTI_LED_CONFIG_1, MAX30105_SLOT2_MASK, device << 4)
        elif slot_number == 3:
            self.bitmask(MAX30105_MULTI_LED_CONFIG_2, MAX30105_SLOT3_MASK, device)
        elif slot_number == 4:
            self.bitmask(MAX30105_MULTI_LED_CONFIG_2, MAX30105_SLOT4_MASK, device << 4)

    def disable_slots(self):
        """
        清空所有时间槽配置。

        =========================================
        Clear all time-slot assignments.
        """
        self._i2c_set_register(MAX30105_MULTI_LED_CONFIG_1, 0)
        self._i2c_set_register(MAX30105_MULTI_LED_CONFIG_2, 0)

    def _i2c_read_register(self, REGISTER, n_bytes=1):
        """
        读寄存器。

        Args:
            REGISTER (int): 寄存器地址。
            n_bytes (int): 读取字节数（默认 1）。

        Returns:
            bytes: 读取到的字节序列。

        =========================================
        Read register bytes.

        Args:
            REGISTER (int): Register address.
            n_bytes (int): Number of bytes to read (default 1).

        Returns:
            bytes: Raw bytes read.
        """
        self._i2c.writeto(self.i2c_address, bytearray([REGISTER]))
        return self._i2c.readfrom(self.i2c_address, n_bytes)

    def _i2c_set_register(self, REGISTER, VALUE):
        """
        写寄存器一个字节。

        Args:
            REGISTER (int): 寄存器地址。
            VALUE (int): 要写入的值（1 字节）。

        =========================================
        Write one byte to a register.

        Args:
            REGISTER (int): Register address.
            VALUE (int): 1-byte value to write.
        """
        self._i2c.writeto(self.i2c_address, bytearray([REGISTER, VALUE]))

    def set_bitmask(self, REGISTER, MASK, NEW_VALUES):
        """
        读取-掩码-合并-写回（便捷改位）。

        Args:
            REGISTER (int): 寄存器地址。
            MASK (int): 位掩码。
            NEW_VALUES (int): 新值（已对齐）。

        =========================================
        Read-mask-or-write helper.

        Args:
            REGISTER (int): Register address.
            MASK (int): Bit mask.
            NEW_VALUES (int): New value (already aligned).
        """
        newCONTENTS = (ord(self._i2c_read_register(REGISTER)) & MASK) | NEW_VALUES
        self._i2c_set_register(REGISTER, newCONTENTS)

    def bitmask(self, reg, slotMask, thing):
        """
        读取寄存器、按掩码保留位后与新值合并写回。

        Args:
            reg (int): 寄存器地址。
            slotMask (int): 位掩码。
            thing (int): 合并的新值。

        =========================================
        Read register, apply mask, OR with new value, then write back.

        Args:
            reg (int): Register address.
            slotMask (int): Bit mask.
            thing (int): New value.
        """
        originalContents = ord(self._i2c_read_register(reg))
        originalContents = originalContents & slotMask
        self._i2c_set_register(reg, originalContents | thing)

    def _fifo_bytes_to_int(self, fifo_bytes):
        """
        将 FIFO 中的 3 字节样本解码为整数，并按当前脉宽位宽右移。

        Args:
            fifo_bytes (bytes): 3 字节原始数据。

        Returns:
            int: 解码后的样本值。

        =========================================
        Decode a 3-byte FIFO sample into an integer and right-shift by the
        configured pulse width.

        Args:
            fifo_bytes (bytes): 3 raw bytes.

        Returns:
            int: Decoded sample value.
        """
        value = unpack(">i", b'\x00' + fifo_bytes)
        return (value[0] & 0x3FFFF) >> self._pulse_width

    def available(self):
        """
        返回红光通道可用样本数量。

        Returns:
            int: 可用样本数。

        =========================================
        Return number of available samples in RED buffer.

        Returns:
            int: Count.
        """
        number_of_samples = len(self.sense.red)
        return number_of_samples

    def get_red(self):
        """
        读取一个新的红光值（带超时轮询）。

        Returns:
            int: 红光样本值；若超时则返回 0。

        =========================================
        Get one RED sample with polling timeout.

        Returns:
            int: Sample value or 0 if timeout.
        """
        if self.safe_check(250):
            return self.sense.red.pop_head()
        else:
            return 0

    def get_ir(self):
        """
        读取一个新的 IR 值（带超时轮询）。

        Returns:
            int: IR 样本值；若超时则返回 0。

        =========================================
        Get one IR sample with polling timeout.

        Returns:
            int: Sample value or 0 if timeout.
        """
        if self.safe_check(250):
            return self.sense.IR.pop_head()
        else:
            return 0

    def get_green(self):
        """
        读取一个新的绿光值（带超时轮询）。

        Returns:
            int: 绿光样本值；若超时则返回 0。

        =========================================
        Get one GREEN sample with polling timeout.

        Returns:
            int: Sample value or 0 if timeout.
        """
        if self.safe_check(250):
            return self.sense.green.pop_head()
        else:
            return 0

    def pop_red_from_storage(self):
        """
        从缓存弹出一个红光样本（若为空返回 0）。

        Returns:
            int: 红光样本。

        =========================================
        Pop one RED sample from storage (0 if empty).

        Returns:
            int: Sample.
        """
        if len(self.sense.red) == 0:
            return 0
        else:
            return self.sense.red.pop()

    def pop_ir_from_storage(self):
        """
        从缓存弹出一个 IR 样本（若为空返回 0）。

        Returns:
            int: IR 样本。

        =========================================
        Pop one IR sample from storage (0 if empty).

        Returns:
            int: Sample.
        """
        if len(self.sense.IR) == 0:
            return 0
        else:
            return self.sense.IR.pop()

    def pop_green_from_storage(self):
        """
        从缓存弹出一个绿光样本（若为空返回 0）。

        Returns:
            int: 绿光样本。

        =========================================
        Pop one GREEN sample from storage (0 if empty).

        Returns:
            int: Sample.
        """
        if len(self.sense.green) == 0:
            return 0
        else:
            return self.sense.green.pop()

    def next_sample(self):
        """
        与 SparkFun 库行为对齐的占位函数：仅检查是否存在可用数据。

        Returns:
            bool|None: 有数据返回 True；否则返回 None。

        =========================================
        Placeholder for SparkFun compatibility: indicates if data is available.

        Returns:
            bool|None: True if data available; otherwise None.
        """
        if self.available():
            return True

    def check(self):
        """
        轮询读取 FIFO 新数据并写入环形缓冲。

        Returns:
            bool: 若有新数据返回 True，否则 False。

        =========================================
        Poll the sensor for new FIFO data and push into ring buffers.

        Returns:
            bool: True if new data found, else False.
        """
        read_pointer = ord(self.get_read_pointer())
        write_pointer = ord(self.get_write_pointer())

        # 判断是否有新数据
        if read_pointer != write_pointer:
            # 计算需要读取的样本数
            number_of_samples = write_pointer - read_pointer
            # 指针回绕处理（32 深度）
            if number_of_samples < 0:
                number_of_samples += 32

            for _ in range(number_of_samples):
                # 每个样本字节数 = active_leds * 3
                fifo_bytes = self._i2c_read_register(MAX30105_FIFO_DATA, self._multi_led_read_mode)

                # 按 LED 通道解码并压入环形缓冲
                if self._active_leds > 0:
                    self.sense.red.append(self._fifo_bytes_to_int(fifo_bytes[0:3]))
                if self._active_leds > 1:
                    self.sense.IR.append(self._fifo_bytes_to_int(fifo_bytes[3:6]))
                if self._active_leds > 2:
                    self.sense.green.append(self._fifo_bytes_to_int(fifo_bytes[6:9]))
                return True
        else:
            return False

    def safe_check(self, max_time_to_check):
        """
        在给定超时时间（ms）内循环调用 check() 直到有新数据或超时。

        Args:
            max_time_to_check (int): 超时（毫秒），必须为非负整数。

        Returns:
            bool: 有新数据返回 True；超时返回 False。

        Raises:
            TypeError: 如果 max_time_to_check 不是 int。
            ValueError: 如果 max_time_to_check 为负数。

        =========================================
        Poll check() until data arrives or timeout (ms) elapses.

        Args:
            max_time_to_check (int): Timeout in ms, must be a non-negative integer.

        Returns:
            bool: True if new data found; False on timeout.

        Raises:
            TypeError: If max_time_to_check is not an int.
            ValueError: If max_time_to_check is negative.
        """
        # 类型检查
        if not isinstance(max_time_to_check, int):
            raise TypeError("max_time_to_check must be an int")
        # 值检查
        if max_time_to_check < 0:
            raise ValueError("max_time_to_check must be non-negative")

        mark_time = time.ticks_ms()
        while True:
            if time.ticks_diff(time.ticks_ms(), mark_time) > max_time_to_check:
                return False
            if self.check():
                return True
            time.sleep_ms(1)

class CircularBuffer(object):
    """
    基于 deque 的简易环形缓冲区实现。

    Attributes:
        data (deque): 底层存储。
        max_size (int): 最大容量。

    Methods:
        append(item): 追加元素（满则丢弃最早元素）。
        pop(): 弹出最早元素。
        pop_head(): 弹出最新元素（注意：原实现含边界逻辑）。
        clear(): 清空。
        is_empty(): 是否为空。

    Notes:
        - 为保持与原代码逻辑一致，未更改 `pop_head` 的实现；其行为较非常规环形缓冲，使用时请注意。

    =========================================
    A minimal ring buffer backed by deque.

    Attributes:
        data (deque): Underlying storage.
        max_size (int): Capacity.

    Methods:
       append(item): Append an element (if full, discard the earliest element).
        pop(): Pop the earliest element.
        pop_head(): Pop the latest element (Note: The original implementation includes boundary logic).
        clear(): Clear all elements.
        is_empty(): Check if it is empty.

    Notes:
        - The original `pop_head` behavior is preserved verbatim; it is unusual
          for a ring buffer, so use with care.
    """

    def __init__(self, max_size):
        """
        初始化。

        Args:
            max_size (int): 容量上限，必须为正整数。

        Raises:
            TypeError: 如果 max_size 不是 int 类型。
            ValueError: 如果 max_size 小于等于 0。

        =========================================
        Initialize.

        Args:
            max_size (int): Capacity, must be a positive integer.

        Raises:
            TypeError: If max_size is not an int.
            ValueError: If max_size is not positive.
        """
        # 类型检查
        if not isinstance(max_size, int):
            raise TypeError("max_size must be an int")
        # 值检查
        if max_size <= 0:
            raise ValueError("max_size must be a positive integer")

        self.data = deque((), max_size, True)
        self.max_size = max_size

    def __len__(self):
        """
        返回当前元素数量。

        Returns:
            int: 元素个数。

        =========================================
        Return current number of elements.

        Returns:
            int: Count.
        """
        return len(self.data)

    def is_empty(self):
        """
        判断是否为空。

        Returns:
            bool: 是否为空。

        =========================================
        Check if empty.

        Returns:
            bool: True if empty.
        """
        return not bool(self.data)

    def append(self, item):
        """
        追加元素；若满，则丢弃最早元素再插入。

        Args:
            item (Any): 待插入元素。

        =========================================
        Append an item; drop the oldest if full.

        Args:
            item (Any): Item to append.
        """
        try:
            self.data.append(item)
        except IndexError:
            # 队列满，丢弃最早元素
            self.data.popleft()
            self.data.append(item)

    def pop(self):
        """
        弹出最早的元素。

        Returns:
            Any: 被弹出的元素。

        =========================================
        Pop the oldest element.

        Returns:
            Any: Popped element.
        """
        return self.data.popleft()

    def clear(self):
        """
        清空缓冲区。

        =========================================
        Clear the buffer.
        """
        self.data = deque((), self.max_size, True)

    def pop_head(self):
        """
        弹出“最新”元素（保留原有实现特性）。

        Returns:
            Any|int: 若空返回 0，否则返回元素。

        =========================================
        Pop the "newest" element (keeps original implementation semantics).

        Returns:
            Any|int: 0 if empty, els法 2：通过 GitHub 客户端e the element.
        """
        buffer_size = len(self.data)
        temp = self.data
        if buffer_size == 1:
            pass
        elif buffer_size > 1:
            self.data.clear()
            for _ in range(buffer_size - 1):
                # 注意：原实现会将 self.data 直接赋值为单个元素，行为非常规
                self.data = temp.popleft()
        else:
            return 0
        return temp.popleft()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================