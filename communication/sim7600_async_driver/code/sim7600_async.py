try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time


class SIM7600Async:
    def __init__(self, uart):
        if not hasattr(uart, "read") or not hasattr(uart, "write") or not hasattr(uart, "any"):
            raise ValueError("uart must provide read, write, and any")
        self.uart = uart
        self._lock = asyncio.Lock()

    def _read_uart_once(self):
        """Single UART consumer; public transactions hold ``_lock``."""
        return self.uart.read()

    async def _read_until_unlocked(self, expected, timeout_ms):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        chunks = []
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self.uart.any():
                data = self._read_uart_once()
                if data:
                    chunks.append(data)
                    response = b"".join(chunks)
                    if any(token in response for token in expected):
                        return response
            await asyncio.sleep_ms(10)
        raise RuntimeError("SIM7600 command timeout")

    async def _command_unlocked(self, command, timeout_ms=3000, expected=(b"\r\nOK\r\n", b"\r\nERROR\r\n")):
        while self.uart.any():
            self._read_uart_once()
        self.uart.write((command + "\r\n").encode())
        return await self._read_until_unlocked(expected, timeout_ms)

    async def command_async(self, command, timeout_ms=3000):
        async with self._lock:
            return (await self._command_unlocked(command, timeout_ms)).decode()

    async def check_sim_card_async(self): return await self.command_async("AT+CPIN?")
    async def get_signal_quality_async(self): return await self.command_async("AT+CSQ")
    async def check_network_registration_async(self): return await self.command_async("AT+CEREG?")
    async def check_network_attach_async(self): return await self.command_async("AT+CGATT?")
    async def aclose(self): self.uart = None


class CallingAsync:
    def __init__(self, sim7600): self.sim7600 = sim7600
    async def make_call_async(self, number): return await self.sim7600.command_async("ATD{};".format(number))
    async def hang_up_async(self): return await self.sim7600.command_async("ATH")
    async def answer_call_async(self): return await self.sim7600.command_async("ATA")
    async def call_status_async(self): return await self.sim7600.command_async("AT+CLCC")
    async def set_call_volume_async(self, level): return await self.sim7600.command_async("AT+CLVL={}".format(level))


class SMSAsync:
    def __init__(self, sim7600): self.sim7600 = sim7600
    async def set_sms_mode_async(self, gmgf=1, csmp="17,11,0,0", CSCS="IRA"):
        await self.sim7600.command_async("AT+CMGF={}".format(gmgf)); await self.sim7600.command_async('AT+CSMP={}'.format(csmp)); return await self.sim7600.command_async('AT+CSCS="{}"'.format(CSCS))
    async def send_sms_async(self, number, message, timeout_ms=60000):
        if not isinstance(number, str) or not number.strip():
            raise ValueError("number parameter cannot be empty")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message parameter cannot be empty")
        async with self.sim7600._lock:
            prompt = await self.sim7600._command_unlocked('AT+CMGS="{}"'.format(number), timeout_ms, (b">", b"\r\nERROR\r\n"))
            if b">" not in prompt:
                return prompt.decode()
            self.sim7600.uart.write(message.encode() + b"\x1a")
            return (await self.sim7600._read_until_unlocked((b"\r\nOK\r\n", b"\r\nERROR\r\n"), timeout_ms)).decode()
    async def list_sms_async(self, status): return await self.sim7600.command_async('AT+CMGL="{}"'.format(status))


class GPSAsync:
    def __init__(self, sim7600): self.sim7600 = sim7600
    async def disable_gps_async(self): return await self.sim7600.command_async("AT+CGPS=0")
    async def set_satellite_beidou_async(self): return await self.sim7600.command_async("AT+CGPSNMEA=196608")
    async def enable_gps_async(self): return await self.sim7600.command_async("AT+CGPS=1")
    async def start_search_satellite_async(self): return await self.sim7600.command_async("AT+CGPSFTM=1")
    async def get_gps_info_async(self): return await self.sim7600.command_async("AT+CGPSINFO")


class LBSAsync:
    def __init__(self, sim7600): self.sim7600 = sim7600
    async def start_network_async(self): return await self.sim7600.command_async("AT+CNETSTART")
    async def stop_network_async(self): return await self.sim7600.command_async("AT+CNETSTOP")
    async def get_lbs_coords_async(self, command): return await self.sim7600.command_async("AT+CLBS={}".format(command))
    async def get_lbs_full_async(self, command): return await self.sim7600.command_async("AT+CLBS={}".format(command))


class HTTPAsync:
    def __init__(self, sim7600): self.sim7600 = sim7600
    async def set_apn_async(self, cid=1, pdp_type="IP", apn="CMNET"): return await self.sim7600.command_async('AT+CGDCONT={},"{}","{}"'.format(cid,pdp_type,apn))
    async def get_ip_async(self): return await self.sim7600.command_async("AT+CGCONTRDP")
    async def enable_http_async(self): return await self.sim7600.command_async("AT+HTTPINIT")
    async def disable_http_async(self): return await self.sim7600.command_async("AT+HTTPTERM")
    async def set_url_async(self, url): return await self.sim7600.command_async('AT+HTTPPARA="URL","{}"'.format(url))
    async def send_head_async(self, content_type): return await self.sim7600.command_async("AT+HTTPACTION={}".format(content_type), 10000)
    async def get_head_async(self): return await self.sim7600.command_async("AT+HTTPHEAD")
    async def get_read_async(self, offset=0, length=512): return await self.sim7600.command_async("AT+HTTPREAD={},{}".format(offset,length))
    async def http_data_async(self, data_len, timeout=1000, data=None):
        if data is None:
            return await self.sim7600.command_async("AT+HTTPDATA={},{}".format(data_len, timeout), timeout)
        payload = data.encode() if isinstance(data, str) else bytes(data)
        if len(payload) != data_len:
            raise ValueError("data_len must equal payload length")
        async with self.sim7600._lock:
            prompt = await self.sim7600._command_unlocked("AT+HTTPDATA={},{}".format(data_len, timeout), timeout, (b"DOWNLOAD", b"\r\nERROR\r\n"))
            if b"DOWNLOAD" not in prompt:
                return prompt.decode()
            self.sim7600.uart.write(payload)
            return (await self.sim7600._read_until_unlocked((b"\r\nOK\r\n", b"\r\nERROR\r\n"), timeout)).decode()
