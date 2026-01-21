# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : ecg_module_cmd
# @Description : 心率串口模块命令发送解析
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin, Timer
import time
from data_flow_processor import DataFlowProcessor
from ad8232 import AD8232
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

def voltage_to_16bit(voltage, V_min=-1, V_max=2):
    """
    将电压值映射到0-65535（16位无符号整数范围）。

    Args:
        voltage (float): 输入的电压值。
        V_min (float): 理论最小电压值，默认为-1V。
        V_max (float): 理论最大电压值，默认为2V。

    Returns:
        int: 映射后的16位整数（0-65535）。

    Process:
        1. 将电压值限制在[V_min, V_max]范围内。
        2. 进行线性归一化处理，映射到[0, 1]区间。
        3. 将归一化值转换为0-65535的整数。

    Note:
        - 该映射用于将模拟电压信号转换为数字量进行传输。
        - 默认电压范围适用于典型ECG信号幅值。

    ==========================================

    Map voltage value to 0-65535 (16-bit unsigned integer range).

    Args:
        voltage (float): Input voltage value.
        V_min (float): Theoretical minimum voltage, defaults to -1V.
        V_max (float): Theoretical maximum voltage, defaults to 2V.

    Returns:
        int: Mapped 16-bit integer (0-65535).

    Process:
        1. Clamp voltage value within [V_min, V_max] range.
        2. Perform linear normalization, mapping to [0, 1] interval.
        3. Convert normalized value to integer in range 0-65535.

    Note:
        - This mapping converts analog voltage signals to digital quantities for transmission.
        - Default voltage range is suitable for typical ECG signal amplitudes.
    """
    # 限制在范围内
    voltage_clipped = max(V_min, min(V_max, voltage))

    # 线性映射
    normalized = (voltage_clipped - V_min) / (V_max - V_min)
    return round(normalized * 65535)

class AD8232_DataFlowProcessor:
    """
           AD8232心电传感器与数据流处理器的集成类。

           该类整合AD8232传感器、ECG信号处理器和数据流处理器，实现心电数据的
           采集、处理、通信协议转换和上报功能。支持主动上报和查询响应两种模式。

           Attributes:
               DEBUG_ENABLED (bool): 调试模式开关。
               ECGSignalProcessor: ECG信号处理器实例。
               DataFlowProcessor: 数据流处理器实例。
               AD8232: AD8232传感器实例。
               parse_interval (int): 解析数据帧的时间间隔（毫秒）。
               _timer (Timer): 数据解析定时器。
               _report_timer (Timer): 数据上报定时器。
               _is_running (bool): 运行状态标志。
               ecg_value (int): 原始心电数据（16位映射值）。
               filtered_ecg_value (int): 滤波后心电数据（16位映射值）。
               heart_rate (int): 心率值（次/分钟）。
               active_reporting (bool): 主动上报模式开关。
               reporting_frequency (int): 上报频率（Hz）。
               lead_status (int): 导联连接状态（0正常，1脱落）。
               operating_status (int): 工作状态（0停止，1运行）。

           Methods:
               __init__(): 初始化AD8232_DataFlowProcessor实例。
               _start_timer(): 启动定时器。
               _report_timer_callback(): 上报定时器回调函数。
               _timer_callback(): 解析定时器回调函数。
               update_properties_from_frame(): 根据接收帧更新属性并响应。

           ==========================================

           AD8232 ECG sensor and data flow processor integration class.

           This class integrates AD8232 sensor, ECG signal processor, and data flow processor,
           implementing ECG data acquisition, processing, communication protocol conversion,
           and reporting functions. Supports both active reporting and query response modes.

           Attributes:
               DEBUG_ENABLED (bool): Debug mode switch.
               ECGSignalProcessor: ECG signal processor instance.
               DataFlowProcessor: Data flow processor instance.
               AD8232: AD8232 sensor instance.
               parse_interval (int): Data frame parsing interval (milliseconds).
               _timer (Timer): Data parsing timer.
               _report_timer (Timer): Data reporting timer.
               _is_running (bool): Running status flag.
               ecg_value (int): Raw ECG data (16-bit mapped value).
               filtered_ecg_value (int): Filtered ECG data (16-bit mapped value).
               heart_rate (int): Heart rate value (beats per minute).
               active_reporting (bool): Active reporting mode switch.
               reporting_frequency (int): Reporting frequency (Hz).
               lead_status (int): Lead connection status (0 normal, 1 detached).
               operating_status (int): Operating status (0 stopped, 1 running).

           Methods:
               __init__(): Initialize AD8232_DataFlowProcessor instance.
               _start_timer(): Start timers.
               _report_timer_callback(): Reporting timer callback function.
               _timer_callback(): Parsing timer callback function.
               update_properties_from_frame(): Update properties and respond based on received frames.
           """

    DEBUG_ENABLED = True  # 调试模式开关

    def __init__(self, DataFlowProcessor,AD8232,ECGSignalProcessor, parse_interval=10):
        """
        初始化AD8232_DataFlowProcessor实例。

        Args:
            DataFlowProcessor: 已初始化的DataFlowProcessor实例。
            AD8232: 已初始化的AD8232传感器实例。
            ECGSignalProcessor: 已初始化的ECG信号处理器实例。
            parse_interval (int): 解析数据帧的时间间隔，单位为毫秒，默认值为10ms。

        Note:
            - 创建数据解析和上报定时器。
            - 初始化所有数据属性为默认值。
            - 默认上报频率为100Hz。
            - 启动定时器开始数据处理循环。

        ==========================================

        Initialize AD8232_DataFlowProcessor instance.

        Args:
            DataFlowProcessor: Initialized DataFlowProcessor instance.
            AD8232: Initialized AD8232 sensor instance.
            ECGSignalProcessor: Initialized ECG signal processor instance.
            parse_interval (int): Data frame parsing interval in milliseconds, defaults to 10ms.

        Note:
            - Create data parsing and reporting timers.
            - Initialize all data attributes to default values.
            - Default reporting frequency is 100Hz.
            - Start timers to begin data processing loop.
        """
        self.ECGSignalProcessor = ECGSignalProcessor
        self.DataFlowProcessor = DataFlowProcessor
        self.AD8232 = AD8232
        self.parse_interval = parse_interval  # 解析间隔时间，单位为毫秒
        self._timer = Timer()
        self._report_timer = Timer()
        self._is_running = False
        # 原始心电数据
        self.ecg_value = 0
        # 滤波后心电数据
        self.filtered_ecg_value= 0
        # 心率
        self.heart_rate = 0
        # 主动上报模式
        self.active_reporting = False

        # 上报频率
        self.reporting_frequency = 100  # 单位：HZ
        # 导联状态
        self.lead_status = 0
        # 工作状态
        self.operating_status = 0
        self._start_timer()

    def _start_timer(self):
        """
        启动定时器。

        Note:
            - 设置解析定时器为周期性模式，周期为parse_interval毫秒。
            - 设置上报定时器周期根据上报频率计算。
            - 启动两个定时器并设置运行状态标志为True。

        ==========================================

        Start timers.

        Note:
            - Set parsing timer to periodic mode with period of parse_interval milliseconds.
            - Set reporting timer period calculated from reporting frequency.
            - Start both timers and set running status flag to True.
        """
        self._is_running = True
        self._timer.init(period=self.parse_interval, mode=Timer.PERIODIC, callback=self._timer_callback)
        self._report_timer.init(period=int(1000/self.reporting_frequency),mode=Timer.PERIODIC,callback=self._report_timer_callback)

    def _report_timer_callback(self, timer):
        """
        上报定时器回调函数，执行主动上报。

        Args:
            timer: 定时器实例。

        Process:
            1. 更新所有传感器数据属性。
            2. 如果主动上报模式开启，按协议格式发送各种数据帧。
            3. 上报数据类型包括：原始ECG、滤波后ECG、导联状态、工作状态、心率。

        Note:
            - 上报频率由reporting_frequency属性控制。
            - 使用DataFlowProcessor构建和发送协议帧。

        ==========================================

        Reporting timer callback function, executes active reporting.

        Args:
            timer: Timer instance.

        Process:
            1. Update all sensor data attributes.
            2. If active reporting mode is enabled, send various data frames in protocol format.
            3. Reported data types include: raw ECG, filtered ECG, lead status, operating status, heart rate.

        Note:
            - Reporting frequency is controlled by reporting_frequency attribute.
            - Use DataFlowProcessor to build and send protocol frames.
        """
        self.ecg_value = voltage_to_16bit(self.ECGSignalProcessor.raw_val_dc)
        self.lead_status = self.AD8232.check_leads_off()
        self.operating_status = self.AD8232.operating_status
        self.filtered_ecg_value = voltage_to_16bit(self.ECGSignalProcessor.filtered_val)
        self.heart_rate = int(self.ECGSignalProcessor.heart_rate)

        if self.active_reporting:
            # 主动上报原始心电数据
            data = bytearray(2)
            data[0] = (self.ecg_value >> 8) & 0xFF
            data[1] = self.ecg_value & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x01, data)

            # 主动上报滤波后心电数据
            data = bytearray(2)
            data[0] = (self.filtered_ecg_value >> 8) & 0xFF
            data[1] = self.filtered_ecg_value & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x02, data)

            # 主动上报导联状态
            data = bytearray(1)
            data[0] = self.lead_status & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x03, data)

            # 主动上报工作状态
            data = bytearray(1)
            data[0] = self.operating_status & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x07, data)

            # 主动上报心率
            data = bytearray(1)
            data[0] = self.heart_rate & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x08, data)

    def _timer_callback(self, timer):
        """
        解析定时器回调函数，定期处理接收到的数据帧。

        Args:
            timer: 定时器实例。

        Process:
            1. 检查运行状态，如果停止则直接返回。
            2. 调用DataFlowProcessor读取并解析串口数据。
            3. 对每个解析到的帧使用micropython.schedule进行异步处理。

        Note:
            - 使用micropython.schedule确保中断安全。
            - 解析间隔由parse_interval属性控制。

        ==========================================

        Parsing timer callback function, periodically processes received data frames.

        Args:
            timer: Timer instance.

        Process:
            1. Check running status, return directly if stopped.
            2. Call DataFlowProcessor to read and parse serial data.
            3. Use micropython.schedule for asynchronous processing of each parsed frame.

        Note:
            - Use micropython.schedule to ensure interrupt safety.
            - Parsing interval is controlled by parse_interval attribute.
        """
        if not self._is_running:
            return

        # 调用DataFlowProcessor的解析方法
        frames = self.DataFlowProcessor.read_and_parse()

        # 对每个解析到的帧使用micropython.schedule进行异步处理
        for frame in frames:
            # 使用micropython.schedule安全地调用属性更新方法
            micropython.schedule(self.update_properties_from_frame, frame)

    def update_properties_from_frame(self,frame):
        """
        根据接收到的协议帧更新属性并发送响应。

        Args:
            frame (dict): 解析后的协议帧字典。

        Process:
            1. 提取帧类型（命令）和数据内容。
            2. 根据命令类型执行相应操作：
               - 查询类命令：读取当前属性值并发送响应帧。
               - 设置类命令：更新属性值并发送确认帧。
            3. 调试模式下打印操作信息。

        Command mapping:
            0x01: 查询原始心电数据
            0x02: 查询滤波后心电数据
            0x03: 查询导联脱落状态
            0x04: 设置上报频率
            0x05: 设置主动上报模式
            0x06: 设置工作状态（启停控制）
            0x07: 查询工作状态
            0x08: 查询心率值

        Note:
            - 所有响应帧使用相同的帧类型代码，便于上位机识别。
            - 无效命令或数据会打印错误信息但不会崩溃。

        ==========================================

        Update properties and send responses based on received protocol frames.

        Args:
            frame (dict): Parsed protocol frame dictionary.

        Process:
            1. Extract frame type (command) and data content.
            2. Execute corresponding operations based on command type:
               - Query commands: Read current property values and send response frames.
               - Setting commands: Update property values and send confirmation frames.
            3. Print operation information in debug mode.

        Command mapping:
            0x01: Query raw ECG data
            0x02: Query filtered ECG data
            0x03: Query lead detachment status
            0x04: Set reporting frequency
            0x05: Set active reporting mode
            0x06: Set operating status (start/stop control)
            0x07: Query operating status
            0x08: Query heart rate value

        Note:
            - All response frames use same frame type codes for easy host identification.
            - Invalid commands or data print error messages but don't crash.
        """
        command = frame['frame_type']
        data = frame['data']
        if len(data) == 0:
            return
        # 在这里根据命令和数据更新属性
        # 查询原始心电数据
        if command == 0x01:
            ecg_value = self.ecg_value
            data = bytearray(2)
            data[0] = (ecg_value >> 8) & 0xFF
            data[1] = ecg_value & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x01, data)
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("ECG Value:", ecg_value)

        # 滤波后心电数据
        elif command == 0x02:
            filtered_ecg_value = self.filtered_ecg_value
            data = bytearray(2)
            data[0] = (filtered_ecg_value >> 8) & 0xFF
            data[1] = filtered_ecg_value & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x02, data)
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("filtered_ecg Value:", filtered_ecg_value)
        # 脱落状态检测
        elif command == 0x03:
            lead_status = self.lead_status
            data = bytearray(1)
            data[0] = lead_status & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x03, data)
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Lead Status:", lead_status)
        # 上报频率
        elif command == 0x04:
            # 上报频率 100HZ, 125HZ, 50HZ
            if data[0] in [100, 125, 50]:
                self.reporting_frequency = data[0]
                self._report_timer.init(period=int(1000 / self.reporting_frequency), mode=Timer.PERIODIC,callback=self._report_timer_callback)
                self.DataFlowProcessor.build_and_send_frame(0x04, bytes(data[0]))
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Reporting Frequency set to:", self.reporting_frequency)
            else:
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Invalid Reporting Frequency:", data[0])

        # 主动上报模式设置
        elif command == 0x05:
            self.active_reporting = bool(data[0])
            self.DataFlowProcessor.build_and_send_frame(0x05, bytes(data[0]))
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Active Reporting set to:", self.active_reporting)
        # 工作状态
        elif command == 0x06:
            # 0: 停止, 1: 运行
            if data[0] == 0:
                self.AD8232.off()
                self.operating_status = data[0]
                self.DataFlowProcessor.build_and_send_frame(0x05, bytes(data[0]))
            elif data[0] == 1:
                self.AD8232.on()
                self.operating_status = data[0]
                self.DataFlowProcessor.build_and_send_frame(0x05, bytes(data[0]))
            else:
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Invalid Operating Status:", data[0])
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Operating Status set to:", self.operating_status)

        # 查询工作状态
        elif command == 0x07:
            operating_status = self.operating_status
            data = bytearray(1)
            data[0] = operating_status & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x07, data)
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Operating Status:", operating_status)
        # 查询心率
        elif command == 0x08:
            heart_rate = self.heart_rate
            data = bytearray(1)
            data[0] = heart_rate & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x08, data)
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Heart Rate:", heart_rate)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================