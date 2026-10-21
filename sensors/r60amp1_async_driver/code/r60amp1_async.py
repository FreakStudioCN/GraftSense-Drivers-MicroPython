"""R60AMP1 cooperative single-reader UART adapter."""
# SPDX-License-Identifier: MIT
# Copyright (c) GraftSense
# Async adaptation for R60AMP1
# Hardware transport: UART framed protocol
# Async level: cooperative_nonblocking
# Static gates pass; hardware unverified.
# See README.md for timing and lifecycle details.

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from r60amp1 import R60AMP1


class _R60AMP1State(R60AMP1):
    """Allocate protocol state without the synchronous startup sequence."""
    def __init__(self):
        pass

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class R60AMP1Async:
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
        self._configuration = configuration.copy()
        self._state = _R60AMP1State()
        self._state.data_processor = data_processor
        self._state._query_in_progress = False
        self._state._query_response_received = False
        self._state._query_result = None
        self._state._current_query_type = None
        self._state._initialization_complete = False
        self._state._configuration_errors = []
        for name, value in configuration.items():
            setattr(self._state, name, value)
        self._state.presence_enabled = configuration.get("presence_enabled", True)
        self._state.product_model = ""
        self._state.product_id = ""
        self._state.hardware_model = ""
        self._state.firmware_version = ""

    def __getattr__(self, name):
        return getattr(self._state, name)

    async def _retry_operation_async(self, operation, *args, timeout=200):
        retries = self._configuration.get("max_retries", 3)
        delay = self._configuration.get("retry_delay", 100)
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
                raise RuntimeError("R60AMP1 device information initialization failed")
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
                raise RuntimeError("R60AMP1 reset during initialization failed")
            await asyncio.sleep_ms(3000)
            deadline = time.ticks_add(time.ticks_ms(), 10000)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                success, initialized = await self.query_init_complete_async(timeout=500)
                if success and initialized:
                    break
                await asyncio.sleep_ms(200)
            if not initialized:
                raise RuntimeError("R60AMP1 device initialization not complete")
        operation = self.enable_human_presence_async if self._configuration.get("presence_enabled", True) else self.disable_human_presence_async
        success, _value = await self._retry_operation_async(operation, timeout=200)
        if not success:
            self._state._configuration_errors.append("Failed configuration: Human Presence")
        success, _value = await self.query_human_presence_switch_async(timeout=500)
        if not success:
            self._state._configuration_errors.append("Verification failed: Presence Detection")
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
                    R60AMP1.update_properties_from_frame(self._state, frame)
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
            command = R60AMP1.COMMAND_MAP.get(operation)
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

    async def query_heartbeat_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_HEARTBEAT, timeout=timeout)

    async def reset_module_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_MODULE_RESET, timeout=timeout)

    async def query_product_model_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_PRODUCT_MODEL, timeout=timeout)

    async def query_product_id_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_PRODUCT_ID, timeout=timeout)

    async def query_hardware_model_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_HARDWARE_MODEL, timeout=timeout)

    async def query_firmware_version_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_FIRMWARE_VERSION, timeout=timeout)

    async def query_init_complete_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_INIT_COMPLETE, timeout=timeout)

    async def query_human_presence_switch_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH, timeout=timeout)

    async def query_presence_status_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_PRESENCE_STATUS, timeout=timeout)

    async def query_motion_info_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_MOTION_INFO, timeout=timeout)

    async def query_body_motion_param_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_BODY_MOTION_PARAM, timeout=timeout)

    async def query_trajectory_info_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_QUERY_TRAJECTORY_INFO, timeout=timeout)

    async def enable_human_presence_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_CONTROL_HUMAN_PRESENCE_ON, timeout=timeout)

    async def disable_human_presence_async(self, timeout=200):
        return await self._execute_operation_async(R60AMP1.TYPE_CONTROL_HUMAN_PRESENCE_OFF, timeout=timeout)


# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================

