"""Async R60ABD1 transport and source-compatible command APIs."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from data_flow_processor import DataFlowProcessor
from r60abd1 import R60ABD1

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class DataFlowProcessorAsync(DataFlowProcessor):
    """Bounded frame parser adapter."""

    async def read_and_parse_async(self):
        return self.read_and_parse()

    async def aclose(self):
        return None

class R60ABD1Async(R60ABD1):
    """Single-reader R60ABD1 driver with cooperative command waits."""

    def _start_timer(self):
        """Timer parsing is replaced by _reader_loop()."""

    def _complete_initialization(self):
        """Source configuration is exposed as awaitable command APIs."""

    def __init__(self, data_processor, parse_interval=200, presence_enabled=True,
                 heart_rate_enabled=True, heart_rate_waveform_enabled=False,
                 breath_monitoring_enabled=True, breath_waveform_enabled=False,
                 sleep_monitoring_enabled=True, abnormal_struggle_enabled=False,
                 struggle_sensitivity=1, no_person_timing_enabled=False,
                 no_person_timing_duration=30, sleep_cutoff_duration=120,
                 max_retries=3, retry_delay=100, init_timeout=5000):
        if not hasattr(data_processor, "read_and_parse") or not hasattr(data_processor, "build_and_send_frame"):
            raise ValueError("data_processor must provide frame parsing and frame writing")
        if not 1 <= parse_interval <= 500 or max_retries < 0 or retry_delay < 0 or init_timeout <= 0:
            raise ValueError("invalid R60ABD1 timing parameters")
        self.data_processor = data_processor
        self.parse_interval, self.max_retries = parse_interval, max_retries
        self.retry_delay, self.init_timeout = retry_delay, init_timeout
        self.presence_enabled = presence_enabled
        self.heart_rate_enabled, self.heart_rate_waveform_enabled = heart_rate_enabled, heart_rate_waveform_enabled
        self.breath_monitoring_enabled, self.breath_waveform_enabled = breath_monitoring_enabled, breath_waveform_enabled
        self.sleep_monitoring_enabled, self.abnormal_struggle_enabled = sleep_monitoring_enabled, abnormal_struggle_enabled
        self.struggle_sensitivity, self.no_person_timing_enabled = struggle_sensitivity, no_person_timing_enabled
        self.no_person_timing_duration, self.sleep_cutoff_duration = no_person_timing_duration, sleep_cutoff_duration
        self._is_running = False
        self._initialization_complete = False
        self._configuration_errors = []
        self._query_in_progress = False
        self._query_response_received = False
        self._query_result = None
        self._current_query_type = None
        self._query_timeout = 200
        self._timer = None
        self._reader_task = None
        self._operation_lock = asyncio.Lock()
        self._io_lock = asyncio.Lock()
        self._last_error = None
        self.product_model = self.product_id = self.hardware_model = self.firmware_version = ""
        self.heartbeat_last_received = self.heartbeat_timeout_count = self.heartbeat_interval = 0
        self.system_initialized = False
        self.system_initialized_timestamp = self.module_reset_timestamp = 0
        self.module_reset_flag = self.radar_in_range = False
        self.presence_status = self.motion_status = self.movement_parameter = self.human_distance = 0
        self.human_position_x = self.human_position_y = self.human_position_z = 0
        self.breath_status = self.breath_value = self.heart_rate_value = 0
        self.breath_waveform = [0, 0, 0, 0, 0]
        self.heart_rate_waveform = [0, 0, 0, 0, 0]
        self.bed_status = self.sleep_status = self.awake_duration = self.light_sleep_duration = self.deep_sleep_duration = 0
        self.sleep_quality_score = self.sleep_quality_rating = self.sleep_anomaly = self.abnormal_struggle_status = self.no_person_timing_status = 0
        self.sleep_comprehensive_status = {}
    async def _retry_operation_async(self, operation, timeout=200):
        for attempt in range(self.max_retries + 1):
            success, value = await operation(timeout=timeout)
            if success:
                return True, value
            if attempt < self.max_retries:
                await asyncio.sleep_ms(self.retry_delay)
        return False, None
    async def initialize_async(self):
        """Run the source information -> init-confirmation sequence cooperatively."""
        if self._initialization_complete:
            return
        for query in (self.query_product_model_async, self.query_product_id_async, self.query_hardware_model_async, self.query_firmware_version_async):
            success, _value = await query(timeout=self.init_timeout)
            if not success:
                raise RuntimeError("R60ABD1 device information initialization failed")
        success, initialized = await self.query_init_complete_async(timeout=self.init_timeout)
        if not success or not initialized:
            raise RuntimeError("R60ABD1 device initialization not complete")
        configuration_steps = []
        configuration_steps.append((self.enable_human_presence_async if self.presence_enabled else self.disable_human_presence_async, "Human Presence"))
        if self.heart_rate_enabled:
            configuration_steps.append((self.enable_heart_rate_monitor_async, "Heart Rate Monitor"))
            configuration_steps.append((self.enable_heart_rate_waveform_report_async if self.heart_rate_waveform_enabled else self.disable_heart_rate_waveform_report_async, "Heart Rate Waveform Report"))
        else:
            configuration_steps.append((self.disable_heart_rate_monitor_async, "Heart Rate Monitor"))
        if self.breath_monitoring_enabled:
            configuration_steps.append((self.enable_breath_monitor_async, "Breath Monitor"))
            configuration_steps.append((self.enable_breath_waveform_report_async if self.breath_waveform_enabled else self.disable_breath_waveform_report_async, "Breath Waveform Report"))
        else:
            configuration_steps.append((self.disable_breath_monitor_async, "Breath Monitor"))
        if self.sleep_monitoring_enabled:
            configuration_steps.append((self.enable_sleep_monitor_async, "Sleep Monitor"))
            if self.abnormal_struggle_enabled:
                configuration_steps.append((self.enable_abnormal_struggle_monitor_async, "Abnormal Struggle Monitor"))
                configuration_steps.append((lambda timeout=200: self.set_struggle_sensitivity_async(self.struggle_sensitivity, timeout=timeout), "Struggle Sensitivity"))
            else:
                configuration_steps.append((self.disable_abnormal_struggle_monitor_async, "Abnormal Struggle Monitor"))
            if self.no_person_timing_enabled:
                configuration_steps.append((self.enable_no_person_timing_async, "No Person Timing"))
                configuration_steps.append((lambda timeout=200: self.set_no_person_timing_duration_async(self.no_person_timing_duration, timeout=timeout), "No Person Timing Duration"))
            else:
                configuration_steps.append((self.disable_no_person_timing_async, "No Person Timing"))
            configuration_steps.append((lambda timeout=200: self.set_sleep_end_duration_async(self.sleep_cutoff_duration, timeout=timeout), "Sleep End Duration"))
        else:
            configuration_steps.append((self.disable_sleep_monitor_async, "Sleep Monitor"))
        for operation, name in configuration_steps:
            success, _value = await self._retry_operation_async(operation, timeout=200)
            if not success:
                self._configuration_errors.append("Failed to " + name)
        verification_steps = [(self.query_init_complete_async, "Device Initialization"), (self.query_radar_range_boundary_async, "Radar Range")]
        if self.presence_enabled:
            verification_steps.append((self.query_human_presence_switch_async, "Presence Detection"))
        if self.heart_rate_enabled:
            verification_steps.append((self.query_heart_rate_monitor_switch_async, "Heart Rate Monitor"))
        if self.breath_monitoring_enabled:
            verification_steps.append((self.query_breath_monitor_switch_async, "Breath Monitor"))
        if self.sleep_monitoring_enabled:
            verification_steps.append((self.query_sleep_monitor_switch_async, "Sleep Monitor"))
        for operation, name in verification_steps:
            success, _value = await self._retry_operation_async(operation, timeout=500)
            if not success:
                self._configuration_errors.append("Verification failed: " + name)
        self._initialization_complete = True
    async def start(self):
        if not self._is_running:
            self._is_running = True
            self._reader_task = asyncio.create_task(self._reader_loop())

    async def _reader_loop(self):
        while self._is_running:
            try:
                async with self._io_lock:
                    frames = self.data_processor.read_and_parse()
                for frame in frames:
                    self.update_properties_from_frame(frame)
            except Exception as error:
                self._last_error = error
            await asyncio.sleep_ms(self.parse_interval)

    async def _execute_operation_async(self, operation_type, data=None, timeout=200):
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError('timeout must be a positive integer')
        await self.start()
        async with self._operation_lock:
            command = self.COMMAND_MAP.get(operation_type)
            if command is None:
                raise ValueError('unknown R60ABD1 operation')
            self._query_in_progress = True
            self._query_response_received = False
            self._query_result = None
            self._current_query_type = operation_type
            try:
                payload = command['data'] if data is None else data
                async with self._io_lock:
                    frame = self.data_processor.build_and_send_frame(command['control_byte'], command['command_byte'], payload)
                if not frame:
                    return False, None
                deadline = time.ticks_add(time.ticks_ms(), timeout)
                while not self._query_response_received:
                    if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                        return False, None
                    await asyncio.sleep_ms(5)
                return True, self._query_result
            finally:
                self._query_in_progress = False
                self._query_response_received = False
                self._query_result = None
                self._current_query_type = None

    async def stop(self):
        self._is_running = False
        task = self._reader_task
        if task is not None:
            task.cancel()
            try:
                await task
            except BaseException:
                pass
            self._reader_task = None

    async def aclose(self):
        await self.stop()
        if self._timer is not None:
            self._timer.deinit()
    async def query_heartbeat_async(self, timeout=200) -> tuple:
        """查询心跳包（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HEARTBEAT, timeout=timeout)

    async def reset_module_async(self, timeout=500) -> tuple:
        """模组复位（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_MODULE_RESET, timeout=timeout)

    async def query_product_model_async(self, timeout=200) -> tuple:
        """查询产品型号（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_PRODUCT_MODEL, timeout=timeout)

    async def query_product_id_async(self, timeout=200) -> tuple:
        """查询产品ID（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_PRODUCT_ID, timeout=timeout)

    async def query_hardware_model_async(self, timeout=200) -> tuple:
        """查询硬件型号（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HARDWARE_MODEL, timeout=timeout)

    async def query_firmware_version_async(self, timeout=200) -> tuple:
        """查询固件版本（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_FIRMWARE_VERSION, timeout=timeout)

    async def query_init_complete_async(self, timeout=200) -> tuple:
        """查询初始化是否完成（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_INIT_COMPLETE, timeout=timeout)

    async def query_radar_range_boundary_async(self, timeout=200) -> tuple:
        """查询雷达探测范围越界状态（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_RADAR_RANGE_BOUNDARY, timeout=timeout)

    async def enable_human_presence_async(self, timeout=200) -> tuple:
        """
        打开人体存在功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_HUMAN_PRESENCE_ON, timeout=timeout)

    async def disable_human_presence_async(self, timeout=200) -> tuple:
        """
        关闭人体存在功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_HUMAN_PRESENCE_OFF, timeout=timeout)

    async def query_human_presence_switch_async(self, timeout=200) -> tuple:
        """
        查询人体存在开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH, timeout=timeout)

    async def query_presence_status_async(self, timeout=200) -> tuple:
        """查询存在信息状态（阻塞式）"""
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HUMAN_EXISTENCE_INFO, timeout=timeout)

    async def query_human_motion_info_async(self, timeout=200) -> tuple:
        """
        查询运动信息（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 运动状态)
                    - 运动状态: 必须是 R60ABD1.MOTION_NONE, R60ABD1.MOTION_STATIC, R60ABD1.MOTION_ACTIVE 中的一个

        Raises:
            ValueError: 如果返回的运动状态不是预定义的有效值
        """
        success, motion_status = await self._execute_operation_async(R60ABD1.TYPE_QUERY_HUMAN_MOTION_INFO, timeout=timeout)
        # 验证返回的运动状态是否有效
        if success and motion_status not in (R60ABD1.MOTION_NONE, R60ABD1.MOTION_STATIC, R60ABD1.MOTION_ACTIVE):
            raise ValueError(f"Invalid motion status: {motion_status}")

        return success, motion_status

    async def query_human_body_motion_param_async(self, timeout=200) -> tuple:
        """
        查询体动参数（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 体动参数值)
                    - 体动参数值: 0-100
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HUMAN_BODY_MOTION_PARAM, timeout=timeout)

    async def query_human_distance_async(self, timeout=200) -> tuple:
        """
        查询人体距离（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 人体距离)
                    - 人体距离: 0-65535 cm
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HUMAN_DISTANCE, timeout=timeout)

    async def query_human_direction_async(self, timeout=200) -> tuple:
        """
        查询人体方位（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 方位坐标)
                    - 方位坐标: (x, y, z) 三元组，单位cm
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HUMAN_DIRECTION, timeout=timeout)

    async def enable_heart_rate_monitor_async(self, timeout=200) -> tuple:
        """
        打开心率监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_HEART_RATE_MONITOR_ON, timeout=timeout)

    async def disable_heart_rate_monitor_async(self, timeout=200) -> tuple:
        """
        关闭心率监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_HEART_RATE_MONITOR_OFF, timeout=timeout)

    async def query_heart_rate_monitor_switch_async(self, timeout=200) -> tuple:
        """
        查询心率监测开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HEART_RATE_MONITOR_SWITCH, timeout=timeout)

    async def enable_heart_rate_waveform_report_async(self, timeout=200) -> tuple:
        """
        打开心率波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_ON, timeout=timeout)

    async def disable_heart_rate_waveform_report_async(self, timeout=200) -> tuple:
        """
        关闭心率波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_OFF, timeout=timeout)

    async def query_heart_rate_waveform_report_switch_async(self, timeout=200) -> tuple:
        """
        查询心率波形上报开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HEART_RATE_WAVEFORM_REPORT_SWITCH, timeout=timeout)

    async def query_heart_rate_value_async(self, timeout=200) -> tuple:
        """
        查询心率数值（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 心率数值)
                    - 心率数值: 60-120 次/分
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HEART_RATE_VALUE, timeout=timeout)

    async def query_heart_rate_waveform_async(self, timeout=200) -> tuple:
        """
        查询心率波形（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 心率波形数据)
                    - 心率波形数据: 5个字节的波形数据列表
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_HEART_RATE_WAVEFORM, timeout=timeout)

    async def enable_breath_monitor_async(self, timeout=200) -> tuple:
        """
        打开呼吸监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_BREATH_MONITOR_ON, timeout=timeout)

    async def disable_breath_monitor_async(self, timeout=200) -> tuple:
        """
        关闭呼吸监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_BREATH_MONITOR_OFF, timeout=timeout)

    async def query_breath_monitor_switch_async(self, timeout=200) -> tuple:
        """
        查询呼吸监测开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_BREATH_MONITOR_SWITCH, timeout=timeout)

    async def set_low_breath_threshold_async(self, threshold, timeout=200) -> tuple:
        """
        设置低缓呼吸判读阈值（阻塞式）

        Args:
            threshold: 阈值数值，范围10-20
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if threshold < 10 or threshold > 20:
            raise ValueError("Low breath threshold must be between 10 and 20")

        data = bytes([threshold])
        return await self._execute_operation_async(R60ABD1.TYPE_SET_LOW_BREATH_THRESHOLD, data=data, timeout=timeout)

    async def query_low_breath_threshold_async(self, timeout=200) -> tuple:
        """
        查询低缓呼吸判读阈值（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 阈值数值)
                    - 阈值数值: 10-20
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_LOW_BREATH_THRESHOLD, timeout=timeout)

    async def query_breath_info_async(self, timeout=200) -> tuple:
        """
        查询呼吸信息（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 呼吸状态)
                    - 呼吸状态: 必须是 R60ABD1.BREATH_NORMAL, R60ABD1.BREATH_HIGH,
                               R60ABD1.BREATH_LOW, R60ABD1.BREATH_NONE 中的一个

        Raises:
            ValueError: 如果返回的呼吸状态不是预定义的有效值
        """
        success, breath_status = await self._execute_operation_async(R60ABD1.TYPE_QUERY_BREATH_INFO, timeout=timeout)
        # 验证返回的呼吸状态是否有效
        if success and breath_status not in (R60ABD1.BREATH_NORMAL, R60ABD1.BREATH_HIGH, R60ABD1.BREATH_LOW, R60ABD1.BREATH_NONE):
            raise ValueError(f"Invalid breath status: {breath_status}")

        return success, breath_status

    async def query_breath_value_async(self, timeout=200) -> tuple:
        """
        查询呼吸数值（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 呼吸数值)
                    - 呼吸数值: 0-35 次/分
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_BREATH_VALUE, timeout=timeout)

    async def enable_breath_waveform_report_async(self, timeout=200) -> tuple:
        """
        打开呼吸波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_BREATH_WAVEFORM_REPORT_ON, timeout=timeout)

    async def disable_breath_waveform_report_async(self, timeout=200) -> tuple:
        """
        关闭呼吸波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_BREATH_WAVEFORM_REPORT_OFF, timeout=timeout)

    async def query_breath_waveform_report_switch_async(self, timeout=200) -> tuple:
        """
        查询呼吸波形上报开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_BREATH_WAVEFORM_REPORT_SWITCH, timeout=timeout)

    async def query_breath_waveform_async(self, timeout=200) -> tuple:
        """
        查询呼吸波形（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 呼吸波形数据)
                    - 呼吸波形数据: 5个字节的波形数据列表
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_BREATH_WAVEFORM, timeout=timeout)

    async def enable_sleep_monitor_async(self, timeout=200) -> tuple:
        """
        打开睡眠监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_SLEEP_MONITOR_ON, timeout=timeout)

    async def disable_sleep_monitor_async(self, timeout=200) -> tuple:
        """
        关闭睡眠监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_SLEEP_MONITOR_OFF, timeout=timeout)

    async def query_sleep_monitor_switch_async(self, timeout=200) -> tuple:
        """
        查询睡眠监测开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_MONITOR_SWITCH, timeout=timeout)

    async def enable_abnormal_struggle_monitor_async(self, timeout=200) -> tuple:
        """
        打开异常挣扎状态监测（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_ABNORMAL_STRUGGLE_ON, timeout=timeout)

    async def disable_abnormal_struggle_monitor_async(self, timeout=200) -> tuple:
        """
        关闭异常挣扎状态监测（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_ABNORMAL_STRUGGLE_OFF, timeout=timeout)

    async def query_abnormal_struggle_switch_async(self, timeout=200) -> tuple:
        """
        查询异常挣扎状态开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_ABNORMAL_STRUGGLE_SWITCH, timeout=timeout)

    async def query_abnormal_struggle_status_async(self, timeout=200) -> tuple:
        """
        查询异常挣扎状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 挣扎状态)
                    - 挣扎状态: 必须是 R60ABD1.STRUGGLE_NONE, R60ABD1.STRUGGLE_NORMAL,
                               R60ABD1.STRUGGLE_ABNORMAL 中的一个

        Raises:
            ValueError: 如果返回的挣扎状态不是预定义的有效值
        """
        success, struggle_status = await self._execute_operation_async(R60ABD1.TYPE_QUERY_ABNORMAL_STRUGGLE_STATUS, timeout=timeout)
        # 验证返回的挣扎状态是否有效
        if success and struggle_status not in (R60ABD1.STRUGGLE_NONE, R60ABD1.STRUGGLE_NORMAL, R60ABD1.STRUGGLE_ABNORMAL):
            raise ValueError(f"Invalid struggle status: {struggle_status}")

        return success, struggle_status

    async def set_struggle_sensitivity_async(self, sensitivity, timeout=200) -> tuple:
        """
        设置挣扎状态判读灵敏度（阻塞式）

        Args:
            sensitivity: 灵敏度 (0=低, 1=中, 2=高)
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if sensitivity not in [R60ABD1.SENSITIVITY_LOW, R60ABD1.SENSITIVITY_MEDIUM, R60ABD1.SENSITIVITY_HIGH]:
            raise ValueError("Sensitivity must be 0 (low), 1 (medium), or 2 (high)")

        data = bytes([sensitivity])
        return await self._execute_operation_async(R60ABD1.TYPE_SET_STRUGGLE_SENSITIVITY, data=data, timeout=timeout)

    async def query_struggle_sensitivity_async(self, timeout=200) -> tuple:
        """
        查询挣扎状态判读灵敏度（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 灵敏度值)
                    - 灵敏度值: 0-低, 1-中, 2-高
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_STRUGGLE_SENSITIVITY, timeout=timeout)

    async def enable_no_person_timing_async(self, timeout=200) -> tuple:
        """
        打开无人计时功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_NO_PERSON_TIMING_ON, timeout=timeout)

    async def disable_no_person_timing_async(self, timeout=200) -> tuple:
        """
        关闭无人计时功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return await self._execute_operation_async(R60ABD1.TYPE_CONTROL_NO_PERSON_TIMING_OFF, timeout=timeout)

    async def query_no_person_timing_switch_async(self, timeout=200) -> tuple:
        """
        查询无人计时功能开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_SWITCH, timeout=timeout)

    async def set_no_person_timing_duration_async(self, duration, timeout=200) -> tuple:
        """
        设置无人计时时长（阻塞式）

        Args:
            duration: 时长数值，范围30-180分钟，步长10分钟
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if duration < 30 or duration > 180 or duration % 10 != 0:
            raise ValueError("No person timing duration must be between 30-180 minutes in steps of 10")

        data = bytes([duration])
        return await self._execute_operation_async(R60ABD1.TYPE_SET_NO_PERSON_TIMING_DURATION, data=data, timeout=timeout)

    async def query_no_person_timing_duration_async(self, timeout=200) -> tuple:
        """
        查询无人计时时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 30-180分钟
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_DURATION, timeout=timeout)

    async def set_sleep_end_duration_async(self, duration, timeout=200) -> tuple:
        """
        设置睡眠截止时长（阻塞式）

        Args:
            duration: 时长数值，范围5-120分钟
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if duration < 5 or duration > 120:
            raise ValueError("Sleep end duration must be between 5-120 minutes")

        data = bytes([duration])
        return await self._execute_operation_async(R60ABD1.TYPE_SET_SLEEP_END_DURATION, data=data, timeout=timeout)

    async def query_sleep_end_duration_async(self, timeout=200) -> tuple:
        """
        查询睡眠截止时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 5-120分钟
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_END_DURATION, timeout=timeout)

    async def query_no_person_timing_status_async(self, timeout=200) -> tuple:
        """
        查询无人计时状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 无人计时状态)
                    - 无人计时状态: 必须是 R60ABD1.NO_PERSON_TIMING_NONE, R60ABD1.NO_PERSON_TIMING_NORMAL,
                                   R60ABD1.NO_PERSON_TIMING_ABNORMAL 中的一个

        Raises:
            ValueError: 如果返回的无人计时状态不是预定义的有效值
        """
        success, timing_status = await self._execute_operation_async(R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_STATUS, timeout=timeout)

        # 验证返回的无人计时状态是否有效
        if success and timing_status not in (R60ABD1.NO_PERSON_TIMING_NONE, R60ABD1.NO_PERSON_TIMING_NORMAL, R60ABD1.NO_PERSON_TIMING_ABNORMAL):
            raise ValueError(f"Invalid no person timing status: {timing_status}")

        return success, timing_status

    async def query_bed_status_async(self, timeout=200) -> tuple:
        """
        查询入床/离床状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 床状态)
                    - 床状态: 必须是 R60ABD1.BED_LEAVE, R60ABD1.BED_ENTER, R60ABD1.BED_NONE 中的一个

        Raises:
            ValueError: 如果返回的床状态不是预定义的有效值
        """
        success, bed_status = await self._execute_operation_async(R60ABD1.TYPE_QUERY_BED_STATUS, timeout=timeout)
        # 验证返回的床状态是否有效
        if success and bed_status not in (R60ABD1.BED_LEAVE, R60ABD1.BED_ENTER, R60ABD1.BED_NONE):
            raise ValueError(f"Invalid bed status: {bed_status}")

        return success, bed_status

    async def query_sleep_status_async(self, timeout=200) -> tuple:
        """
        查询睡眠状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 睡眠状态)
                    - 睡眠状态: 必须是 R60ABD1.SLEEP_DEEP, R60ABD1.SLEEP_LIGHT,
                               R60ABD1.SLEEP_AWAKE, R60ABD1.SLEEP_NONE 中的一个

        Raises:
            ValueError: 如果返回的睡眠状态不是预定义的有效值
        """
        success, sleep_status = await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_STATUS, timeout=timeout)
        # 验证返回的睡眠状态是否有效
        if success and sleep_status not in (R60ABD1.SLEEP_DEEP, R60ABD1.SLEEP_LIGHT, R60ABD1.SLEEP_AWAKE, R60ABD1.SLEEP_NONE):
            raise ValueError(f"Invalid sleep status: {sleep_status}")

        return success, sleep_status

    async def query_awake_duration_async(self, timeout=200) -> tuple:
        """
        查询清醒时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 分钟数
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_AWAKE_DURATION, timeout=timeout)

    async def query_light_sleep_duration_async(self, timeout=200) -> tuple:
        """
        查询浅睡时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 分钟数
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_LIGHT_SLEEP_DURATION, timeout=timeout)

    async def query_deep_sleep_duration_async(self, timeout=200) -> tuple:
        """
        查询深睡时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 分钟数
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_DEEP_SLEEP_DURATION, timeout=timeout)

    async def query_sleep_quality_score_async(self, timeout=200) -> tuple:
        """
        查询睡眠质量评分（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 评分数值)
                    - 评分数值: 0-100
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_QUALITY_SCORE, timeout=timeout)

    async def query_sleep_comprehensive_status_async(self, timeout=200) -> tuple:
        """
        查询睡眠综合状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 综合状态数据)
                    - 综合状态数据: 8字节的睡眠综合状态
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_COMPREHENSIVE_STATUS, timeout=timeout)

    async def query_sleep_anomaly_async(self, timeout=200) -> tuple:
        """
        查询睡眠异常（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 异常状态)
                    - 异常状态: 必须是 R60ABD1.SLEEP_ANOMALY_SHORT, R60ABD1.SLEEP_ANOMALY_LONG,
                               R60ABD1.SLEEP_ANOMALY_NO_PERSON, R60ABD1.SLEEP_ANOMALY_NONE 中的一个

        Raises:
            ValueError: 如果返回的异常状态不是预定义的有效值
        """
        success, anomaly_status = await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_ANOMALY, timeout=timeout)
        # 验证返回的异常状态是否有效
        if success and anomaly_status not in (
            R60ABD1.SLEEP_ANOMALY_SHORT,
            R60ABD1.SLEEP_ANOMALY_LONG,
            R60ABD1.SLEEP_ANOMALY_NO_PERSON,
            R60ABD1.SLEEP_ANOMALY_NONE,
        ):
            raise ValueError(f"Invalid sleep anomaly status: {anomaly_status}")

        return success, anomaly_status

    async def query_sleep_statistics_async(self, timeout=200) -> tuple:
        """
        查询睡眠统计（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 统计数据)
                    - 统计数据: 12字节的睡眠统计信息
        """
        return await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_STATISTICS, timeout=timeout)

    async def query_sleep_quality_level_async(self, timeout=200) -> tuple:
        """
        查询睡眠质量评级（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 质量评级)
                    - 质量评级: 必须是 R60ABD1.SLEEP_QUALITY_NONE, R60ABD1.SLEEP_QUALITY_GOOD,
                               R60ABD1.SLEEP_QUALITY_NORMAL, R60ABD1.SLEEP_QUALITY_POOR 中的一个

        Raises:
            ValueError: 如果返回的质量评级不是预定义的有效值
        """
        success, quality_level = await self._execute_operation_async(R60ABD1.TYPE_QUERY_SLEEP_QUALITY_LEVEL, timeout=timeout)
        # 验证返回的质量评级是否有效
        if success and quality_level not in (
            R60ABD1.SLEEP_QUALITY_NONE,
            R60ABD1.SLEEP_QUALITY_GOOD,
            R60ABD1.SLEEP_QUALITY_NORMAL,
            R60ABD1.SLEEP_QUALITY_POOR,
        ):
            raise ValueError(f"Invalid sleep quality level: {quality_level}")

        return success, quality_level

    async def _handle_query_response_async(self, expected_type, response_data, response_name="") -> None:
        """
        统一处理查询响应

        Args:
            expected_type: 期望的查询类型
            response_data: 响应数据
            response_name: 响应名称（用于调试）
        """
        # 情况1:正确时间正确读取
        if self._query_in_progress and self._current_query_type == expected_type and not self._query_response_received:

            self._query_result = response_data
            self._query_response_received = True

            if R60ABD1.DEBUG_ENABLED:
                query_name = self.QUERY_NAME_MAP.get(expected_type, f"Unknown({expected_type})")
                print(f"[Query] {query_name} response received: {response_data}")

        # 情况2:当前正在进行其他类型的查询，但收到了本响应
        elif self._query_in_progress and self._current_query_type != expected_type:
            if R60ABD1.DEBUG_ENABLED:
                current_query = self.QUERY_NAME_MAP.get(self._current_query_type, f"Unknown({self._current_query_type})")
                print(f"[Query] Unexpected {response_name} response during {current_query} query: {response_data}")

        # 情况3:没有查询在进行，但收到了查询响应
        elif not self._query_in_progress:
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Query] Unsolicited {response_name} response: {response_data}")

    async def _update_property_with_debug_async(self, property_name, new_value, debug_message) -> None:
        """
        更新属性并输出调试信息。

        Args:
            property_name: 属性名称。
            new_value: 新值。
            debug_message: 调试信息。

        Note:
            - 使用setattr动态设置属性值。
            - 如果启用调试模式，输出调试信息。

        ==========================================

        Update property with debug output.

        Args:
            property_name: Property name.
            new_value: New value.
            debug_message: Debug message.

        Note:
            - Use setattr to dynamically set property value.
            - Output debug information if debug mode is enabled.
        """
        setattr(self, property_name, new_value)
        if R60ABD1.DEBUG_ENABLED:
            print(debug_message)

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================