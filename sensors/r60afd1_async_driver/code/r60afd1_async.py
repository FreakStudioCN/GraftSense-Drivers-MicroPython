"""R60AFD1 cooperative single-reader UART adapter."""
# SPDX-License-Identifier: MIT
# Copyright (c) GraftSense
# Async adaptation for R60AFD1
# Hardware transport: UART framed protocol
# Async level: cooperative_nonblocking
# Static gates pass; hardware unverified.
# See README.md for timing and lifecycle details.

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from _gs_r60afd1_r60afd1 import R60AFD1


class _R60AFD1State(R60AFD1):
    """Allocate protocol state without the synchronous startup sequence."""
    def __init__(self):
        pass

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class R60AFD1Async:
    """Single-reader cooperative UART driver."""

    def __init__(self, data_processor, parse_interval=20, **configuration):
        if not hasattr(data_processor, "read_and_parse") or not hasattr(data_processor, "build_and_send_frame"):
            raise ValueError("data_processor must provide frame parsing and frame writing")
        if parse_interval <= 0 or parse_interval > 500:
            raise ValueError("parse_interval must be in the range 1..500 ms")
        self.data_processor = data_processor
        self.parse_interval = parse_interval
        self._running = False
        self._reader_task = None
        self._operation_lock = asyncio.Lock()
        self._io_lock = asyncio.Lock()
        self._last_error = None
        self._latest_frame = None
        self._dropped_frames = 0
        self._configuration = {"presence_enabled": True, "track_report_enabled": True, "energy_report_enabled": True, "height_ratio_enabled": True, "fall_detection_enabled": True, "static_stay_enabled": True, "static_distance": 30, "motion_distance": 30, "max_retries": 3, "retry_delay": 100, "init_timeout": 5000}
        self._configuration.update(configuration)
        self._state = _R60AFD1State()
        self._state.data_processor = data_processor
        self._state._query_in_progress = False
        self._state._query_response_received = False
        self._state._query_result = None
        self._state._current_query_type = None
        self._state._initialization_complete = False
        self._state._configuration_errors = []
        for name, value in self._configuration.items():
            setattr(self._state, name, value)
        self._state.presence_enabled = self._configuration["presence_enabled"]
        self._state.product_model = ""
        self._state.product_id = ""
        self._state.hardware_model = ""
        self._state.firmware_version = ""

    def __getattr__(self, name):
        return getattr(self._state, name)

    async def _retry_operation_async(self, operation, *args, timeout=200):
        retries = self._configuration["max_retries"]
        delay = self._configuration["retry_delay"]
        for attempt in range(retries + 1):
            success, value = await operation(*args, timeout=timeout)
            if success:
                return True, value
            if attempt < retries:
                await asyncio.sleep_ms(delay)
        return False, None
    async def initialize_async(self):
        """Run the source information, confirmation, configuration and verification phases."""
        if self._state._initialization_complete:
            return
        timeout = self._configuration.get("init_timeout", 5000)
        for query in (self.query_product_model_async, self.query_product_id_async, self.query_hardware_model_async, self.query_firmware_version_async):
            success, _value = await query(timeout=timeout)
            if not success:
                raise RuntimeError("R60AFD1 device information initialization failed")
        deadline = time.ticks_add(time.ticks_ms(), timeout)
        initialized = False
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            success, initialized = await self.query_init_complete_async(timeout=500)
            if success and initialized:
                break
            await asyncio.sleep_ms(200)
        if not initialized:
            success, _value = await self.reset_module_async(timeout=1000)
            if not success:
                raise RuntimeError("R60AFD1 reset during initialization failed")
            await asyncio.sleep_ms(3000)
            deadline = time.ticks_add(time.ticks_ms(), 10000)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                success, initialized = await self.query_init_complete_async(timeout=500)
                if success and initialized:
                    break
                await asyncio.sleep_ms(200)
            if not initialized:
                raise RuntimeError("R60AFD1 device initialization not complete")
        configuration_steps = []
        angle_keys = ("install_angle_x", "install_angle_y", "install_angle_z")
        if all(key in self._configuration for key in angle_keys) and any(self._configuration[key] != 0 for key in angle_keys):
            configuration_steps.append(("Install Angle", self.set_install_angle_async, tuple(self._configuration[key] for key in angle_keys)))
        if self._configuration.get("install_height", 0) > 0:
            configuration_steps.append(("Install Height", self.set_install_height_async, (self._configuration["install_height"],)))
        presence_enabled = self._configuration["presence_enabled"]
        configuration_steps.append(("Human Presence", self.set_presence_switch_async, (presence_enabled,)))
        if presence_enabled:
            for key, name, operation in (("static_distance", "Static Distance", self.set_static_distance_async), ("motion_distance", "Motion Distance", self.set_motion_distance_async), ("no_person_timeout", "No Person Timeout", self.set_no_person_time_async), ("presence_threshold", "Presence Threshold", self.set_presence_threshold_async)):
                if self._configuration.get(key, 0) > 0:
                    configuration_steps.append((name, operation, (self._configuration[key],)))
            for key, name, operation in (("energy_report_enabled", "Energy Reporting", self.set_energy_report_switch_async), ("height_ratio_enabled", "Height Ratio", self.set_height_ratio_switch_async), ("track_report_enabled", "Track Reporting", self.set_track_switch_async)):
                configuration_steps.append((name, operation, (self._configuration[key],)))
            if self._configuration.get("track_report_enabled") and self._configuration.get("track_report_frequency", 0) > 0:
                configuration_steps.append(("Track Frequency", self.set_track_frequency_async, (self._configuration["track_report_frequency"],)))
        fall_enabled = self._configuration["fall_detection_enabled"]
        configuration_steps.append(("Fall Detection", self.set_fall_detection_switch_async, (fall_enabled,)))
        if fall_enabled:
            for key, name, operation, minimum in (("fall_duration", "Fall Duration", self.set_fall_duration_async, 0), ("fall_sensitivity", "Fall Sensitivity", self.set_fall_sensitivity_async, 0), ("fall_break_height", "Fall Break Height", self.set_fall_break_height_async, -1), ("height_accumulation_time", "Height Accumulation Time", self.set_height_accumulation_time_async, -1)):
                if self._configuration.get(key, minimum) > minimum:
                    configuration_steps.append((name, operation, (self._configuration[key],)))
            static_enabled = self._configuration["static_stay_enabled"]
            configuration_steps.append(("Static Stay", self.set_static_stay_switch_async, (static_enabled,)))
            if static_enabled and self._configuration.get("static_stay_duration", 0) > 0:
                configuration_steps.append(("Static Stay Duration", self.set_static_stay_duration_async, (self._configuration["static_stay_duration"],)))
        for name, operation, args in configuration_steps:
            success, _value = await self._retry_operation_async(operation, *args, timeout=200)
            if not success:
                self._state._configuration_errors.append("Failed configuration: " + name)
        verification_steps = [("Device Initialization", self.query_init_complete_async)]
        if presence_enabled:
            verification_steps.append(("Human Presence", self.query_presence_switch_async))
        if self._configuration["track_report_enabled"]:
            verification_steps.append(("Track Reporting", self.query_track_switch_async))
        if self._configuration["energy_report_enabled"]:
            verification_steps.append(("Energy Reporting", self.query_energy_report_switch_async))
        if self._configuration["height_ratio_enabled"]:
            verification_steps.append(("Height Ratio", self.query_height_ratio_switch_async))
        if self._configuration["static_stay_enabled"]:
            verification_steps.append(("Static Stay", self.query_static_stay_switch_async))
        if fall_enabled:
            verification_steps.append(("Fall Detection", self.query_fall_detection_switch_async))
        for name, operation in verification_steps:
            success, _value = await self._retry_operation_async(operation, timeout=500)
            if not success:
                self._state._configuration_errors.append("Verification failed: " + name)
        self._state._initialization_complete = True
    async def start(self):
        if not self._running:
            self._running = True
            self._reader_task = asyncio.create_task(self._reader_loop())

    async def _reader_loop(self):
        while self._running:
            try:
                async with self._io_lock:
                    frames = self.data_processor.read_and_parse()
                for frame in frames:
                    R60AFD1.update_properties_from_frame(self._state, frame)
                    if self._latest_frame is not None:
                        self._dropped_frames += 1
                    self._latest_frame = frame
            except OSError as error:
                self._last_error = error
            except Exception as error:
                self._last_error = error
            await asyncio.sleep_ms(self.parse_interval)

    async def _execute_operation_async(self, operation, data=None, timeout=200):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        await self.start()
        async with self._operation_lock:
            command = R60AFD1.COMMAND_MAP.get(operation)
            if command is None:
                raise ValueError("Unknown R60 operation")
            self._state._query_in_progress = True
            self._state._query_response_received = False
            self._state._query_result = None
            self._state._current_query_type = operation
            try:
                payload = command["data"] if data is None else data
                async with self._io_lock:
                    frame = self.data_processor.build_and_send_frame(command["control_byte"], command["command_byte"], payload)
                if not frame:
                    return False, None
                deadline = time.ticks_add(time.ticks_ms(), timeout)
                while not self._state._query_response_received:
                    if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                        return False, None
                    await asyncio.sleep_ms(5)
                return True, self._state._query_result
            finally:
                self._state._query_in_progress = False
                self._state._query_response_received = False
                self._state._query_result = None
                self._state._current_query_type = None

    async def next_frames_async(self):
        """Return at most one latest frame; dropped count is exposed in status."""
        frame = self._latest_frame
        self._latest_frame = None
        return [] if frame is None else [frame]
    async def get_configuration_status_async(self):
        return {"initialization_complete": self._state._initialization_complete, "configuration_errors": self._state._configuration_errors[:], "dropped_frames": self._dropped_frames, "device_info": {"product_model": self._state.product_model, "product_id": self._state.product_id, "hardware_model": self._state.hardware_model, "firmware_version": self._state.firmware_version}}

    async def query_heartbeat_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HEARTBEAT, timeout=timeout)

    async def stop(self):
        self._running = False
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

    async def reset_module_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_MODULE_RESET, timeout=timeout)

    async def query_product_model_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_PRODUCT_MODEL, timeout=timeout)

    async def query_product_id_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_PRODUCT_ID, timeout=timeout)

    async def query_hardware_model_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HARDWARE_MODEL, timeout=timeout)

    async def query_firmware_version_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_FIRMWARE_VERSION, timeout=timeout)

    async def query_init_complete_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_INIT_COMPLETE, timeout=timeout)

    async def query_scene_info_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_SCENE_INFO, timeout=timeout)

    async def query_install_angle_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_INSTALL_ANGLE, timeout=timeout)

    async def query_install_height_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_INSTALL_HEIGHT, timeout=timeout)

    async def auto_measure_height_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_AUTO_HEIGHT_MEASURE, timeout=timeout)

    async def query_presence_switch_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH, timeout=timeout)

    async def query_presence_status_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HUMAN_EXISTENCE_INFO, timeout=timeout)

    async def query_motion_status_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HUMAN_MOTION_INFO, timeout=timeout)

    async def query_body_motion_param_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_BODY_MOTION_PARAM, timeout=timeout)

    async def query_height_ratio_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HEIGHT_RATIO, timeout=timeout)

    async def query_track_point_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_TRACK_POINT, timeout=timeout)

    async def query_track_frequency_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_TRACK_FREQUENCY, timeout=timeout)

    async def query_track_switch_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_TRACK_SWITCH, timeout=timeout)

    async def query_static_distance_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_STATIC_DISTANCE, timeout=timeout)

    async def query_motion_distance_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_MOTION_DISTANCE, timeout=timeout)

    async def query_no_person_time_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_NO_PERSON_TIME, timeout=timeout)

    async def query_presence_threshold_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_PRESENCE_THRESHOLD, timeout=timeout)

    async def query_energy_report_switch_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_ENERGY_REPORT_SWITCH, timeout=timeout)

    async def query_max_energy_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_MAX_ENERGY, timeout=timeout)

    async def query_fall_detection_switch_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_FALL_DETECTION_SWITCH, timeout=timeout)

    async def query_fall_status_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_FALL_STATUS, timeout=timeout)

    async def query_fall_duration_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_FALL_DURATION, timeout=timeout)

    async def query_static_stay_duration_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_STATIC_STAY_DURATION, timeout=timeout)

    async def query_static_stay_switch_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_STATIC_STAY_SWITCH, timeout=timeout)

    async def query_static_stay_status_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_STATIC_STAY_STATUS, timeout=timeout)

    async def query_height_accumulation_time_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HEIGHT_ACCUMULATION_TIME, timeout=timeout)

    async def query_fall_break_height_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_FALL_BREAK_HEIGHT, timeout=timeout)

    async def query_height_ratio_switch_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_HEIGHT_RATIO_SWITCH, timeout=timeout)

    async def query_fall_sensitivity_async(self, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_QUERY_FALL_SENSITIVITY, timeout=timeout)

    async def set_presence_switch_async(self, enabled=True, timeout=200):
        op = R60AFD1.TYPE_CONTROL_HUMAN_PRESENCE_ON if enabled else R60AFD1.TYPE_CONTROL_HUMAN_PRESENCE_OFF
        return await self._execute_operation_async(op, timeout=timeout)

    async def set_fall_detection_switch_async(self, enabled=True, timeout=200):
        op = R60AFD1.TYPE_CONTROL_FALL_DETECTION_ON if enabled else R60AFD1.TYPE_CONTROL_FALL_DETECTION_OFF
        return await self._execute_operation_async(op, timeout=timeout)

    async def set_static_stay_switch_async(self, enabled=True, timeout=200):
        op = R60AFD1.TYPE_CONTROL_STATIC_STAY_ON if enabled else R60AFD1.TYPE_CONTROL_STATIC_STAY_OFF
        return await self._execute_operation_async(op, timeout=timeout)

    async def set_energy_report_switch_async(self, enabled=True, timeout=200):
        op = R60AFD1.TYPE_CONTROL_ENERGY_REPORT_ON if enabled else R60AFD1.TYPE_CONTROL_ENERGY_REPORT_OFF
        return await self._execute_operation_async(op, timeout=timeout)

    async def set_height_ratio_switch_async(self, enabled=True, timeout=200):
        op = R60AFD1.TYPE_CONTROL_HEIGHT_RATIO_ON if enabled else R60AFD1.TYPE_CONTROL_HEIGHT_RATIO_OFF
        return await self._execute_operation_async(op, timeout=timeout)

    async def set_track_switch_async(self, enabled=True, timeout=200):
        return await self._execute_operation_async(R60AFD1.TYPE_SET_TRACK_SWITCH, bytes([1 if enabled else 0]), timeout)

    async def set_install_angle_async(self, angle_x, angle_y, angle_z, timeout=200):
        data = bytes([(angle_x >> 8) & 255, angle_x & 255, (angle_y >> 8) & 255, angle_y & 255, (angle_z >> 8) & 255, angle_z & 255])
        return await self._execute_operation_async(R60AFD1.TYPE_SET_INSTALL_ANGLE, data, timeout)

    async def _set_u16_async(self, op, value, maximum, timeout):
        if value < 0 or value > maximum:
            raise ValueError("Value is outside the supported range")
        return await self._execute_operation_async(op, bytes([(value >> 8) & 255, value & 255]), timeout)

    async def _set_u32_async(self, op, value, minimum, maximum, timeout):
        if value < minimum or value > maximum:
            raise ValueError("Value is outside the supported range")
        return await self._execute_operation_async(op, bytes([(value >> 24) & 255, (value >> 16) & 255, (value >> 8) & 255, value & 255]), timeout)

    async def set_install_height_async(self, value, timeout=200):
        return await self._set_u16_async(R60AFD1.TYPE_SET_INSTALL_HEIGHT, value, 65535, timeout)

    async def set_static_distance_async(self, value, timeout=200):
        return await self._set_u16_async(R60AFD1.TYPE_SET_STATIC_DISTANCE, value, 300, timeout)

    async def set_motion_distance_async(self, value, timeout=200):
        return await self._set_u16_async(R60AFD1.TYPE_SET_MOTION_DISTANCE, value, 300, timeout)

    async def set_no_person_time_async(self, value, timeout=200):
        return await self._set_u32_async(R60AFD1.TYPE_SET_NO_PERSON_TIME, value, 6, 1799, timeout)

    async def set_presence_threshold_async(self, value, timeout=200):
        return await self._set_u32_async(R60AFD1.TYPE_SET_PRESENCE_THRESHOLD, value, 0, 4294967295, timeout)

    async def set_fall_duration_async(self, value, timeout=200):
        return await self._set_u32_async(R60AFD1.TYPE_SET_FALL_DURATION, value, 6, 179, timeout)

    async def set_static_stay_duration_async(self, value, timeout=200):
        return await self._set_u32_async(R60AFD1.TYPE_SET_STATIC_STAY_DURATION, value, 61, 3599, timeout)

    async def set_height_accumulation_time_async(self, value, timeout=200):
        return await self._set_u32_async(R60AFD1.TYPE_SET_HEIGHT_ACCUMULATION_TIME, value, 0, 300, timeout)

    async def set_fall_break_height_async(self, value, timeout=200):
        return await self._set_u16_async(R60AFD1.TYPE_SET_FALL_BREAK_HEIGHT, value, 150, timeout)

    async def set_track_frequency_async(self, value, timeout=200):
        return await self._set_u32_async(R60AFD1.TYPE_SET_TRACK_FREQUENCY, value, 0, 4294967295, timeout)

    async def set_fall_sensitivity_async(self, value, timeout=200):
        if value < 0 or value > 3:
            raise ValueError("Fall sensitivity is outside the supported range")
        return await self._execute_operation_async(R60AFD1.TYPE_SET_FALL_SENSITIVITY, bytes([value]), timeout)




# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================

