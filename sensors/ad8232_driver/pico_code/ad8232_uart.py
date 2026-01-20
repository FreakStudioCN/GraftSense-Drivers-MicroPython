
from machine import UART, Pin, Timer
import micropython

class AD8232_DataFlowProcessor:
    DEBUG_ENABLED = False  # 调试模式开关
    def __init__(self, DataFlowProcessor, parse_interval=5):
        """
        初始化AD8232_UART实例。

        Args:
            DataFlowProcessor: 已初始化的DataFlowProcessor实例。
            parse_interval: 解析数据帧的时间间隔，单位为毫秒，默认值为10ms。

        Note:
            - 创建DataFlowProcessor实例用于数据处理。
            - 初始化定时器和运行状态标志。
            - 启动定时器以定期解析数据帧。
            """
        self.DataFlowProcessor = DataFlowProcessor
        self.parse_interval = parse_interval  # 解析间隔时间，单位为毫秒
        self._timer = Timer()
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
            - 设置定时器为周期性模式，周期为parse_interval毫秒。
            - 定时器回调函数为_timer_callback。
            - 同时设置运行状态标志为True。

        ==========================================

        Start timer.

        Note:
            - Set timer to periodic mode with period of parse_interval milliseconds.
            - Timer callback function is _timer_callback.
            - Also set running status flag to True.
        """
        self._is_running = True
        self._timer.init(period=self.parse_interval, mode=Timer.PERIODIC, callback=self._timer_callback)

    def _timer_callback(self, timer):
        """
        定时器回调函数，定期解析数据帧。

        Args:
            timer: 定时器实例。

        Note:
            - 检查设备是否在运行状态。
            - 调用DataFlowProcessor的解析方法获取数据帧。
            - 使用micropython.schedule安全地异步处理每个帧。

        ==========================================

        Timer callback function, periodically parses data frames.

        Args:
            timer: Timer instance.

        Note:
            - Check if device is in running state.
            - Call DataFlowProcessor's parsing method to get data frames.
            - Use micropython.schedule to safely asynchronously process each frame.
        """
        if not self._is_running:
            return

        # 调用DataFlowProcessor的解析方法
        frames = self.DataFlowProcessor.read_and_parse()

        # 对每个解析到的帧使用micropython.schedule进行异步处理
        for frame in frames:
            # 使用micropython.schedule安全地调用属性更新方法
            micropython.schedule(self.update_properties_from_frame, frame)

    def update_properties_from_frame(self, frame):
        command = frame['frame_type']
        data = frame['data']
        if len(data) == 0:
            return
        # 在这里根据命令和数据更新属性
        # 查询原始心电数据
        if command == 0x01:
            self.ecg_value = data[0]
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("ECG Value:", self.ecg_value)

        # 滤波后心电数据
        elif command == 0x02:
            self.filtered_ecg_value = data[0]
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("ECG Value:", self.filtered_ecg_value)
        # 脱落状态检测
        elif command == 0x03:
            self.lead_status = data[0]
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Lead Status:", self.lead_status)
        # 上报频率
        elif command == 0x04:
            # 上报频率 100HZ, 125HZ, 50HZ
            if data[0] in [100, 125, 50]:
                self.reporting_frequency = data[0]
                if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                    print("Reporting Frequency set to:", self.reporting_frequency)

        # 主动上报模式设置
        elif command == 0x05:
            self.active_reporting = bool(data[0])
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Active Reporting set to:", self.active_reporting)
        # 工作状态
        elif command == 0x06:
            # 0: 停止, 1: 运行
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
            self.operating_status = data[0]
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Operating Status:", self.operating_status)
        # 查询心率
        elif command == 0x08:
            self.heart_rate = data[0]
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("Heart Rate:", self.heart_rate)

    def query_raw_ecg_data(self):
        """查询原始心电数据"""
        # AA 55 01 01 00 01 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x01, bytes([0x00]))
        return self.ecg_value
    def query_off_detection_status(self):
        """查询脱落检测状态"""
        # AA 55 03 01 00 03 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x03, bytes([0x00]))
        return self.lead_status
    def query_filtered_ecg_data(self):
        """查询滤波后心电数据"""
        # AA 55 02 01 00 02 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x02, bytes([0x00]))

        return self.filtered_ecg_value


    def set_active_output_mode(self):
        """设置主动输出模式"""
        # AA 55 04 01 02 06 0D 0A
        # 注意：这里数据是02，不是01
        self.DataFlowProcessor.build_and_send_frame(0x04, bytes([0x02]))
        return self.reporting_frequency

    def set_active_output(self, state):
        """设置主动输出（0关 1开）"""
        # AA 55 05 01 00 05 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x05, bytes([state]))

        return self.active_reporting
    def control_ad8232_start_stop(self, state):
        """控制 AD8232 启停（0关 1开）"""
        # AA 55 06 01 00 06 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x06, bytes([state]))
        return self.operating_status
    def query_module_status(self):
        """查询模块工作状态"""
        # AA 55 07 01 00 07 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x07, bytes([0x00]))
        return self.operating_status
    def query_heart_rate(self):
        """查询心率值"""
        # AA 55 08 01 00 08 0D 0A
        self.DataFlowProcessor.build_and_send_frame(0x08, bytes([0x00]))
        return self.heart_rate