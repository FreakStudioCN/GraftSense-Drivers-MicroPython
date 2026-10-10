"""Cooperative, serialized UART facade for HC-08."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from hc08 import HC08


class HC08Async(HC08):
    def __init__(self, uart, rx_timeout_ms=600):
        super().__init__(uart, rx_timeout_ms)
        self._uart_lock = asyncio.Lock()
        self._closed = False

    async def _read_uart_async(self, deadline, size=None):
        """The only reader for command and transparent-mode responses."""
        while not self._uart.any():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return None
            await asyncio.sleep_ms(10)
        return self._uart.read(size) if size else self._uart.read()

    async def _command_async(self, command, timeout_ms=None):
        if self._closed or self._uart is None: return False, "UART is closed"
        async with self._uart_lock:
            try:
                self._uart.write(command)
                # Source command guard is 50 ms; response waits cooperatively to deadline.
                await asyncio.sleep_ms(50)
                data = await self._read_uart_async(time.ticks_add(time.ticks_ms(), timeout_ms or self.rx_timeout_ms))
                if data is None: return False, "no response"
                return True, data.decode("utf-8").strip()
            except Exception:
                return False, "UART transaction error"

    async def _set_async(self, command, value, validator, attr):
        if not validator(value): return False, "invalid value"
        ok, response = await self._command_async(command(value))
        if not ok: return False, response
        setattr(self, attr, value)
        return True, response

    async def check_async(self):
        ok, response = await self._command_async(b"AT")
        return (response == "OK"), response if ok else "no response"
    async def get_rx_async(self):
        ok, response = await self._command_async(b"AT+RX")
        if not ok: return False, "no response"
        status = {}
        for line in response.splitlines():
            if ":" in line:
                key, value = line.split(":", 1); status[key.strip()] = value.strip()
        return True, status
    async def factory_default_async(self):
        ok, response = await self._command_async(b"AT+DEFAULT")
        await asyncio.sleep_ms(200)
        return ok, response or "params redefault complete"
    async def reset_async(self):
        ok, response = await self._command_async(b"AT+RESET")
        return True, response or "reset complete" if ok else response
    async def get_version_async(self):
        ok, response = await self._command_async(b"AT+VERSION")
        if ok: self.version = response; return True, response
        return False, "no response"
    async def set_role_async(self, role): return await self._set_async(lambda x: b"AT+ROLE=" + (b"S" if x == self.Role["SLAVE"] else b"M"), role, lambda x: x in self.Role.values(), "role")
    async def get_role_async(self):
        ok, response = await self._command_async(b"AT+ROLE=?")
        if not ok: return False, "no response"
        self.role = self.Role["MASTER"] if "M" in response else self.Role["SLAVE"]
        return True, response
    async def set_name_async(self, name):
        if len(name) > 12: return False, "name invalid, longer than 12"
        ok, response = await self._command_async("AT+NAME={}".format(name).encode())
        if ok: self.name = name; return True, response
        return False, "no response"
    async def get_name_async(self):
        ok, response = await self._command_async(b"AT+NAME=?")
        if ok: self.name=response; return True,response
        return False,"no response"
    async def set_addr_async(self, addr12):
        ok, err = self._valid_addr(addr12)
        if not ok: return False, err
        ok, response = await self._command_async("AT+ADDR={}".format(addr12).encode())
        if ok: self.addr=addr12; return True,response
        return False,"no response"
    async def get_addr_async(self):
        ok,response=await self._command_async(b"AT+ADDR=?")
        if ok:self.addr=response;return True,response
        return False,"no response"
    async def set_rfpm_async(self, rfpm):
        if rfpm not in (4,0,-6,-23):return False,"invalid rfpm"
        ok,response=await self._command_async("AT+RFPM={}".format(self.rfpm_param[rfpm]).encode())
        if ok:self.rfpm=rfpm;return True,response
        return False,"no response"
    async def get_rfpm_async(self):
        ok,response=await self._command_async(b"AT+RFPM=?")
        if ok:self.rfpm=response;return True,response
        return False,"no response"
    async def set_baud_async(self, baud_rate, parity):
        if baud_rate not in (1200,2400,4800,9600,19200,38400,57600,115200):return False,"invalid baud"
        if parity not in (self.PARITY_NONE,self.PARITY_EVEN,self.PARITY_ODD):return False,"invalid parity"
        ok,response=await self._command_async("AT+BAUD={},{}".format(baud_rate,parity).encode())
        if ok:self.baud=baud_rate;return True,response
        return False,"no response"
    async def get_baud_async(self):
        ok,response=await self._command_async(b"AT+BAUD=?")
        if not ok:return False,"no response"
        try:self.baud=int(response.split(",")[0]);return True,response
        except Exception:return False,"parse error"
    async def clear_async(self):
        ok,response=await self._command_async(b"AT+CLEAR")
        return True,response or "cleared" if ok else response

    async def send_data_async(self, data):
        if isinstance(data,str):data=data.encode()
        elif not isinstance(data,(bytes,bytearray)):return False,"invalid type: data must be str or bytes"
        async with self._uart_lock:
            try:return True,self._uart.write(data)
            except Exception as exc:return False,"uart error: {}".format(exc)
    async def recv_data_async(self, timeout_ms=None, min_bytes=1):
        deadline=time.ticks_add(time.ticks_ms(),timeout_ms or self.rx_timeout_ms); buf=bytearray()
        async with self._uart_lock:
            while time.ticks_diff(deadline,time.ticks_ms())>0:
                data=await self._read_uart_async(deadline)
                if data:
                    buf.extend(data)
                    if len(buf)>=min_bytes:return True,bytes(buf)
            return False,None
    async def recv_until_async(self, terminator=b"\n", timeout_ms=None):
        deadline=time.ticks_add(time.ticks_ms(),timeout_ms or self.rx_timeout_ms); buf=bytearray()
        async with self._uart_lock:
            while time.ticks_diff(deadline,time.ticks_ms())>0:
                data=await self._read_uart_async(deadline,1)
                if data:
                    buf.extend(data)
                    if buf.endswith(terminator):return True,bytes(buf)
            return False,None
    async def wake_from_sleep_async(self):
        async with self._uart_lock:
            try:self._uart.write(b"\xff"*10);return True,"woke"
            except Exception as exc:return False,"uart error: {}".format(exc)
    async def aclose(self):
        async with self._uart_lock:self._closed=True;self._uart=None