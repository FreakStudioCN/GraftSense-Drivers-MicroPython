"""Cooperative UART client for the AD8232 ECG-module protocol."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


class AD8232_DataFlowProcessor:
    """Host-side protocol client; UART parsing is performed by :meth:`run_async`."""

    DEBUG_ENABLED = False

    def __init__(self, data_flow_processor, parse_interval=5):
        self.DataFlowProcessor = data_flow_processor
        self.parse_interval = parse_interval
        self._is_running = False
        self.ecg_value = 0
        self.filtered_ecg_value = 0
        self.heart_rate = 0
        self.active_reporting = False
        self.reporting_frequency = 100
        self.lead_status = 0
        self.operating_status = 0

    def update_properties_from_frame(self, frame):
        data = frame.get("data", b"")
        if not data:
            return
        command = frame.get("frame_type")
        if command == 0x01 and len(data) >= 2:
            self.ecg_value = (data[0] << 8) | data[1]
        elif command == 0x02 and len(data) >= 2:
            self.filtered_ecg_value = (data[0] << 8) | data[1]
        elif command == 0x03:
            self.lead_status = data[0]
        elif command == 0x04:
            self.reporting_frequency = data[0]
        elif command == 0x05:
            self.active_reporting = bool(data[0])
        elif command in (0x06, 0x07):
            self.operating_status = data[0]
        elif command == 0x08:
            self.heart_rate = data[0]

    async def run_async(self, stop_event=None):
        """Own all UART reads in one task and update the protocol cache."""
        self._is_running = True
        try:
            while self._is_running and not (stop_event and stop_event.is_set()):
                for frame in self.DataFlowProcessor.read_and_parse():
                    self.update_properties_from_frame(frame)
                await asyncio.sleep_ms(self.parse_interval)
        finally:
            self._is_running = False

    def stop(self):
        self._is_running = False

    async def _send_async(self, frame_type, value=0):
        self.DataFlowProcessor.build_and_send_frame(frame_type, bytes([value]))
        await asyncio.sleep_ms(0)

    async def query_raw_ecg_data_async(self):
        await self._send_async(0x01)
        return self.ecg_value

    async def query_off_detection_status_async(self):
        await self._send_async(0x03)
        return self.lead_status

    async def query_filtered_ecg_data_async(self):
        await self._send_async(0x02)
        return self.filtered_ecg_value

    async def set_active_output_mode_async(self):
        await self._send_async(0x04, 0x02)
        return self.reporting_frequency

    async def set_active_output_async(self, state):
        await self._send_async(0x05, int(bool(state)))
        return self.active_reporting

    async def control_ad8232_start_stop_async(self, state):
        await self._send_async(0x06, int(bool(state)))
        return self.operating_status

    async def query_module_status_async(self):
        await self._send_async(0x07)
        return self.operating_status

    async def query_heart_rate_async(self):
        await self._send_async(0x08)
        return self.heart_rate
