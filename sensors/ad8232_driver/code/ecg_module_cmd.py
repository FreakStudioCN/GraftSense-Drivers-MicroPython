from machine import UART, Pin, Timer
import time
from data_flow_processor import DataFlowProcessor
from ad8232 import AD8232
import micropython

def voltage_to_8bit(voltage, V_min=-1.5, V_max=1.5):
    """
    将电压值映射到0-255
    :param voltage: 输入的电压值
    :param V_min: 理论最小电压
    :param V_max: 理论最大电压
    :return: 0-255之间的整数
    """
    # 限制在范围内
    voltage_clipped = max(V_min, min(V_max, voltage))

    # 线性映射
    normalized = (voltage_clipped - V_min) / (V_max - V_min)
    return round(normalized * 255)

class AD8232_DataFlowProcessor:

    DEBUG_ENABLED = True  # 调试模式开关
    def __init__(self, DataFlowProcessor,AD8232,ECGSignalProcessor, parse_interval=10):
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
        self._report_timer.init(period=int(1000/self.reporting_frequency),mode=Timer.PERIODIC,callback=self._report_timer_callback)

    def _report_timer_callback(self, timer):
        """
        上报定时器回调函数，执行主动上报。

        Args:
            timer: 定时器实例。
        """
        self.ecg_value = voltage_to_8bit(self.ECGSignalProcessor.raw_val_dc)
        self.lead_status = self.AD8232.check_leads_off()
        self.operating_status = self.AD8232.operating_status
        self.filtered_ecg_value = voltage_to_8bit(self.ECGSignalProcessor.filtered_val)
        self.heart_rate = int(self.ECGSignalProcessor.heart_rate)

        if self.active_reporting:
            # 主动上报原始心电数据
            data = bytearray(1)
            data[0] = self.ecg_value & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x01, data)

            # 主动上报滤波后心电数据
            data = bytearray(1)
            data[0] = self.filtered_ecg_value & 0xFF
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

    def update_properties_from_frame(self,frame):

        command = frame['frame_type']
        data = frame['data']
        if len(data) == 0:
            return
        # 在这里根据命令和数据更新属性
        # 查询原始心电数据
        if command == 0x01:
            ecg_value = self.ecg_value
            data = bytearray(1)
            data[0] = ecg_value & 0xFF
            self.DataFlowProcessor.build_and_send_frame(0x01, data)
            if AD8232_DataFlowProcessor.DEBUG_ENABLED:
                print("ECG Value:", ecg_value)

        # 滤波后心电数据
        elif command == 0x02:
            filtered_ecg_value = self.filtered_ecg_value
            data = bytearray(1)
            data[0] = filtered_ecg_value & 0xFF
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
            # 上报频率 1HZ, 2HZ, 5HZ
            if data[0] in [1,2,5]:
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