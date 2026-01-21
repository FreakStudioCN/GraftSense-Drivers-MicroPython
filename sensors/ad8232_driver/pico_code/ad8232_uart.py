# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : ad8232_uart.py
# @Description : ad8232_uart传感器驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin, Timer
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class AD8232_DataFlowProcessor:
    """
    AD8232心电传感器UART数据流处理客户端类。

    该类作为AD8232传感器与数据流处理器之间的客户端接口，实现协议数据帧的
    接收、解析和属性更新。支持查询和设置传感器参数，但不包含主动数据采集。

    Attributes:
        DEBUG_ENABLED (bool): 调试模式开关。
        DataFlowProcessor: 数据流处理器实例。
        parse_interval (int): 解析数据帧的时间间隔（毫秒）。
        _timer (Timer): 数据解析定时器。
        _is_running (bool): 运行状态标志。
        ecg_value (int): 原始心电数据（16位映射值）。
        filtered_ecg_value (int): 滤波后心电数据（16位映射值）。
        heart_rate (int): 心率值（次/分钟）。
        active_reporting (bool): 主动上报模式开关。
        reporting_frequency (int): 上报频率（Hz）。
        lead_status (int): 导联连接状态（0正常，1脱落）。
        operating_status (int): 工作状态（0停止，1运行）。

    Methods:
        __init__(): 初始化AD8232_DataFlowProcessor客户端实例。
        _start_timer(): 启动定时器。
        _timer_callback(): 解析定时器回调函数。
        update_properties_from_frame(): 根据接收帧更新属性。
        query_raw_ecg_data(): 查询原始心电数据。
        query_off_detection_status(): 查询脱落检测状态。
        query_filtered_ecg_data(): 查询滤波后心电数据。
        set_active_output_mode(): 设置主动输出模式。
        set_active_output(): 设置主动输出开关。
        control_ad8232_start_stop(): 控制AD8232启停。
        query_module_status(): 查询模块工作状态。
        query_heart_rate(): 查询心率值。

    ==========================================

    AD8232 ECG sensor UART data flow processing client class.

    This class serves as a client interface between AD8232 sensor and data flow processor,
    implementing protocol frame reception, parsing, and property updating. Supports querying
    and setting sensor parameters but does not include active data acquisition.

    Attributes:
        DEBUG_ENABLED (bool): Debug mode switch.
        DataFlowProcessor: Data flow processor instance.
        parse_interval (int): Data frame parsing interval (milliseconds).
        _timer (Timer): Data parsing timer.
        _is_running (bool): Running status flag.
        ecg_value (int): Raw ECG data (16-bit mapped value).
        filtered_ecg_value (int): Filtered ECG data (16-bit mapped value).
        heart_rate (int): Heart rate value (beats per minute).
        active_reporting (bool): Active reporting mode switch.
        reporting_frequency (int): Reporting frequency (Hz).
        lead_status (int): Lead connection status (0 normal, 1 detached).
        operating_status (int): Operating status (0 stopped, 1 running).

    Methods:
        __init__(): Initialize AD8232_DataFlowProcessor client instance.
        _start_timer(): Start timer.
        _timer_callback(): Parsing timer callback function.
        update_properties_from_frame(): Update properties based on received frames.
        query_raw_ecg_data(): Query raw ECG data.
        query_off_detection_status(): Query lead-off detection status.
        query_filtered_ecg_data(): Query filtered ECG data.
        set_active_output_mode(): Set active output mode.
        set_active_output(): Set active output switch.
        control_ad8232_start_stop(): Control AD8232 start/stop.
        query_module_status(): Query module operating status.
        query_heart_rate(): Query heart rate value.
    """
    DEBUG_ENABLED = False  # 调试模式开关

    def __init__(self, DataFlowProcessor, parse_interval=5):
        """
        初始化AD8232_DataFlowProcessor客户端实例。

        Args:
            DataFlowProcessor: 已初始化的DataFlowProcessor实例。
            parse_interval (int): 解析数据帧的时间间隔，单位为毫秒，默认值为5ms。

        Note:
            - 创建数据解析定时器。
            - 初始化所有数据属性为默认值。
            - 默认上报频率为100Hz。
            - 启动定时器开始数据解析循环。

        ==========================================

        Initialize AD8232_DataFlowProcessor client instance.

        Args:
            DataFlowProcessor: Initialized DataFlowProcessor instance.
            parse_interval (int): Data frame parsing interval in milliseconds, defaults to 5ms.

        Note:
            - Create data parsing timer.
            - Initialize all data attributes to default values.
            - Default reporting frequency is 100Hz.
            - Start timer to begin data parsing loop.
        """
        self.DataFlowProcessor = DataFlowProcessor
        self.parse_interval = parse_interval  # 解析间隔时间，单位为毫秒
        self._timer = Timer()
        self._is_running = False
        # 原始心电数据
        self.ecg_value = 0
        # 滤波后心电数据
        self.filtered_ecg_value = 0
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
            - 启动定时器并设置运行状态标志为True。

        ==========================================

        Start timer.

        Note:
            - Set parsing timer to periodic mode with period of parse_interval milliseconds.
            - Start timer and set running status flag to True.
        """
        self._is_running = True
        self._timer.init(period=self.parse_interval, mode=Timer.PERIODIC, callback=self._timer_callback)

    def _timer_callback(self, timer):
        """
        解析定时器回调函数，定期处理接收到的数据帧。

        Args:
            timer: 定时器实例。

        Process:
            1. 检查运行状态，如果停止则直接返回。
            2. 调用DataFlowProcessor读取并解析串口数据。
            3. 对每个解析到的帧进行同步处理。

        Note:
            - 解析间隔由parse_interval属性控制。
            - 使用同步处理方式，适用于简单的客户端场景。

        ==========================================

        Parsing timer callback function, periodically processes received data frames.

        Args:
            timer: Timer instance.

        Process:
            1. Check running status, return directly if stopped.
            2. Call DataFlowProcessor to read and parse serial data.
            3. Process each parsed frame synchronously.

        Note:
            - Parsing interval controlled by parse_interval attribute.
            - Uses synchronous processing suitable for simple client scenarios.
        """
        if not self._is_running:
            return

        # 调用DataFlowProcessor的解析方法
        frames = self.DataFlowProcessor.read_and_parse()
        # 解析内容
        for frame in frames:
            self.update_properties_from_frame(frame)

    def update_properties_from_frame(self, frame):
        """
        根据接收到的协议帧更新客户端属性。

        Args:
            frame (dict): 解析后的协议帧字典。

        Process:
            1. 提取帧类型（命令）和数据内容。
            2. 根据命令类型更新对应的属性值。
            3. 调试模式下打印属性变化。

        Command mapping:
            0x01: 设置原始心电数据
            0x02: 设置滤波后心电数据
            0x03: 设置导联脱落状态
            0x04: 设置上报频率
            0x05: 设置主动上报模式
            0x06: 设置工作状态
            0x07: 设置工作状态（重复）
            0x08: 设置心率值

        Note:
            - 此方法处理从传感器接收到的数据更新帧。
            - 仅更新本地属性，不发送响应帧。
            - 数据有效性检查较为简单。

        ==========================================

        Update client properties based on received protocol frames.

        Args:
            frame (dict): Parsed protocol frame dictionary.

        Process:
            1. Extract frame type (command) and data content.
            2. Update corresponding property values based on command type.
            3. Print property changes in debug mode.

        Command mapping:
            0x01: Set raw ECG data
            0x02: Set filtered ECG data
            0x03: Set lead-off status
            0x04: Set reporting frequency
            0x05: Set active reporting mode
            0x06: Set operating status
            0x07: Set operating status (duplicate)
            0x08: Set heart rate value

        Note:
            - This method handles data update frames received from sensor.
            - Only updates local properties, does not send response frames.
            - Data validity checks are relatively simple.
        """
        command = frame['frame_type']
        data = frame['data']
        if len(data) == 0:
            return
        # 在这里根据命令和数据更新属性
        # 查询原始心电数据
        if command == 0x01:
            if data:
                self.ecg_value = (data[0] << 8) | data[1]
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("ECG Value:", self.ecg_value)

        # 滤波后心电数据
        elif command == 0x02:
            if data:
                self.filtered_ecg_value = (data[0] << 8) | data[1]
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("ECG Value:", self.filtered_ecg_value)
        # 脱落状态检测
        elif command == 0x03:
            if data:
                self.lead_status = data[0]
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Lead Status:", self.lead_status)
        # 上报频率
        elif command == 0x04:
            # 上报频率 100HZ, 125HZ, 50HZ
            if data:
                if data[0] in [100, 125, 50]:
                    self.reporting_frequency = data[0]
                    if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                        print("Reporting Frequency set to:", self.reporting_frequency)

        # 主动上报模式设置
        elif command == 0x05:
            if data:
                self.active_reporting = bool(data[0])
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Active Reporting set to:", self.active_reporting)
        # 工作状态
        elif command == 0x06:
            # 0: 停止, 1: 运行
            if data:
                if data[0] == 0:
                    self.operating_status = data[0]
                elif data[0] == 1:
                    self.operating_status = data[0]
                else:
                    if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                        print("Invalid Operating Status:", data[0])
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Operating Status set to:", self.operating_status)

        # 查询工作状态
        elif command == 0x07:
            if data:
                self.operating_status = data[0]
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Operating Status:", self.operating_status)
        # 查询心率
        elif command == 0x08:
            if data:
                self.heart_rate = data[0]
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Heart Rate:", self.heart_rate)

    def query_raw_ecg_data(self):
        """
        查询原始心电数据。

        Returns:
            int: 当前存储的原始心电数据值。

        Process:
            1. 发送查询原始心电数据的协议帧。
            2. 返回本地存储的最新值。

        Note:
            - 协议帧格式：AA 55 01 01 00 01 0D 0A
            - 此方法会触发传感器发送最新数据，但返回的是本地缓存值。
            - 实际值需要通过update_properties_from_frame方法更新。

        ==========================================

        Query raw ECG data.

        Returns:
            int: Currently stored raw ECG data value.

        Process:
            1. Send protocol frame to query raw ECG data.
            2. Return locally stored latest value.

        Note:
            - Protocol frame format: AA 55 01 01 00 01 0D 0A
            - This method triggers sensor to send latest data, but returns locally cached value.
            - Actual value needs to be updated via update_properties_from_frame method.
        """
        # AA 55 01 01 00 01 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x01, bytes([0x00]))
        return self.ecg_value

    def query_off_detection_status(self):
        """
        查询脱落检测状态。

        Returns:
            int: 当前导联脱落状态（0正常，1脱落）。

        Process:
            1. 发送查询脱落检测状态的协议帧。
            2. 返回本地存储的最新状态。

        Note:
            - 协议帧格式：AA 55 03 01 00 03 0D 0A
            - 状态值需要等待传感器响应更新。

        ==========================================

        Query lead-off detection status.

        Returns:
            int: Current lead-off status (0 normal, 1 detached).

        Process:
            1. Send protocol frame to query lead-off detection status.
            2. Return locally stored latest status.

        Note:
            - Protocol frame format: AA 55 03 01 00 03 0D 0A
            - Status value needs to wait for sensor response update.
        """
        # AA 55 03 01 00 03 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x03, bytes([0x00]))
        return self.lead_status

    def query_filtered_ecg_data(self):
        """
        查询滤波后心电数据。

        Returns:
            int: 当前存储的滤波后心电数据值。

        Process:
            1. 发送查询滤波后心电数据的协议帧。
            2. 返回本地存储的最新值。

        Note:
            - 协议帧格式：AA 55 02 01 00 02 0D 0A
            - 滤波数据经过多级数字滤波器处理。

        ==========================================

        Query filtered ECG data.

        Returns:
            int: Currently stored filtered ECG data value.

        Process:
            1. Send protocol frame to query filtered ECG data.
            2. Return locally stored latest value.

        Note:
            - Protocol frame format: AA 55 02 01 00 02 0D 0A
            - Filtered data processed through multi-stage digital filters.
        """
        # AA 55 02 01 00 02 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x02, bytes([0x00]))

        return self.filtered_ecg_value

    def set_active_output_mode(self):
        """
        设置主动输出模式。

        Returns:
            int: 当前上报频率值。

        Process:
            1. 发送设置主动输出模式的协议帧。
            2. 返回当前上报频率。

        Note:
            - 协议帧格式：AA 55 04 01 02 06 0D 0A
            - 注意数据字段为0x02，表示设置动作。
            - 此方法固定设置主动输出模式，不支持参数化。

        ==========================================

        Set active output mode.

        Returns:
            int: Current reporting frequency value.

        Process:
            1. Send protocol frame to set active output mode.
            2. Return current reporting frequency.

        Note:
            - Protocol frame format: AA 55 04 01 02 06 0D 0A
            - Note data field is 0x02, indicating set action.
            - This method sets active output mode fixedly, does not support parameterization.
        """
        # AA 55 04 01 02 06 0D 0A
        # 注意：这里数据是02，不是01
        self.DataFlowProcessor.build_and_send_frame(0x04, bytes([0x02]))
        return self.reporting_frequency

    def set_active_output(self, state):
        """
        设置主动输出开关。

        Args:
            state (int): 开关状态（0关闭，1开启）。

        Returns:
            bool: 当前主动上报模式状态。

        Process:
            1. 发送设置主动输出开关的协议帧。
            2. 返回当前主动上报模式状态。

        Note:
            - 协议帧格式：AA 55 05 01 00 05 0D 0A
            - 状态参数会被转换为字节格式发送。

        ==========================================

        Set active output switch.

        Args:
            state (int): Switch status (0 off, 1 on).

        Returns:
            bool: Current active reporting mode status.

        Process:
            1. Send protocol frame to set active output switch.
            2. Return current active reporting mode status.

        Note:
            - Protocol frame format: AA 55 05 01 00 05 0D 0A
            - State parameter converted to byte format for sending.
        """
        # AA 55 05 01 00 05 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x05, bytes([state]))

        return self.active_reporting

    def control_ad8232_start_stop(self, state):
        """
        控制AD8232传感器启停。

        Args:
            state (int): 控制状态（0停止，1启动）。

        Returns:
            int: 当前工作状态。

        Process:
            1. 发送控制AD8232启停的协议帧。
            2. 返回当前工作状态。

        Note:
            - 协议帧格式：AA 55 06 01 00 06 0D 0A
            - 此命令控制传感器的电源状态。

        ==========================================

        Control AD8232 sensor start/stop.

        Args:
            state (int): Control status (0 stop, 1 start).

        Returns:
            int: Current operating status.

        Process:
            1. Send protocol frame to control AD8232 start/stop.
            2. Return current operating status.

        Note:
            - Protocol frame format: AA 55 06 01 00 06 0D 0A
            - This command controls sensor power status.
        """
        # AA 55 06 01 00 06 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x06, bytes([state]))
        return self.operating_status

    def query_module_status(self):
        """
        查询模块工作状态。

        Returns:
            int: 当前模块工作状态。

        Process:
            1. 发送查询模块工作状态的协议帧。
            2. 返回当前工作状态。

        Note:
            - 协议帧格式：AA 55 07 01 00 07 0D 0A
            - 状态包括：停止、运行、未知等。

        ==========================================

        Query module operating status.

        Returns:
            int: Current module operating status.

        Process:
            1. Send protocol frame to query module operating status.
            2. Return current operating status.

        Note:
            - Protocol frame format: AA 55 07 01 00 07 0D 0A
            - Status includes: stopped, running, unknown, etc.
        """
        # AA 55 07 01 00 07 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x07, bytes([0x00]))
        return self.operating_status

    def query_heart_rate(self):
        """
        查询心率值。

        Returns:
            int: 当前心率值（次/分钟）。

        Process:
            1. 发送查询心率值的协议帧。
            2. 返回当前心率值。

        Note:
            - 协议帧格式：AA 55 08 01 00 08 0D 0A
            - 心率值经过R波检测算法计算得出。

        ==========================================

        Query heart rate value.

        Returns:
            int: Current heart rate value (beats per minute).

        Process:
            1. Send protocol frame to query heart rate value.
            2. Return current heart rate value.

        Note:
            - Protocol frame format: AA 55 08 01 00 08 0D 0A
            - Heart rate value calculated through R-wave detection algorithm.
        """
        # AA 55 08 01 00 08 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x08, bytes([0x00]))
        return self.heart_rate

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
