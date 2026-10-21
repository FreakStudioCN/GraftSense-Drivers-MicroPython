"""Cooperative, serialized UART facade for E103-W02 AT and transparent modes."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from e103w02 import E103W02, _to_bytes


class E103W02Async(E103W02):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._uart_lock = asyncio.Lock()
        self._closed = False

    async def _read_bytes_async(self, deadline, count=0, drain=False):
        """Single UART reader for drain, AT and transparent paths."""
        if drain:
            while self._uart_any(): self._uart.read()
            return b""
        while not self._uart_any():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0: return None
            await asyncio.sleep_ms(2)
        try:
            return self._uart.read(self._uart_any() if count == 0 else min(self._uart_any(), count))
        except OSError as exc:
            raise RuntimeError("UART read failed") from exc

    async def _read_response_async(self, timeout_ms=None):
        timeout = self._timeout_ms if timeout_ms is None else timeout_ms
        deadline = time.ticks_add(time.ticks_ms(), timeout)
        data = bytearray(); last_data = None
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            available = self._uart_any()
            if available:
                chunk = await self._read_bytes_async(deadline)
                if chunk:
                    data.extend(chunk); last_data = time.ticks_ms()
            elif data and time.ticks_diff(time.ticks_ms(), last_data) >= self._idle_ms:
                break
            await asyncio.sleep_ms(2)
        return bytes(data).decode("utf-8", "ignore").strip()

    async def _drain_input_async(self):
        await self._read_bytes_async(time.ticks_ms(), drain=True)

    async def _send_command_locked_async(self, command, timeout_ms=None):
        if not isinstance(command, str) or not command.startswith("AT+") or "\r" in command or "\n" in command:
            raise ValueError("command must be an AT+ command without CR/LF")
        if not self._command_mode: raise RuntimeError("not in command mode")
        await self._drain_input_async()
        self._write_bytes(command.encode() + self._terminator)
        return self._remove_echo(await self._read_response_async(timeout_ms), command)

    async def enter_command_mode_async(self, timeout_ms=None):
        async with self._uart_lock:
            if self._command_mode: return "Entered AT mode"
            await self._drain_input_async(); self._write_bytes(b"+++")
            response = await self._read_response_async(timeout_ms)
            if "Entered AT mode" not in response: raise RuntimeError(response or "enter AT mode timeout")
            self._command_mode=True; return response
    async def exit_command_mode_async(self, timeout_ms=None):
        async with self._uart_lock:
            response=await self._send_command_locked_async("AT+EXIT",timeout_ms)
            if "Exited AT" not in response: raise RuntimeError(response or "exit AT mode timeout")
            self._command_mode=False; return response
    async def send_command_async(self, command, timeout_ms=None):
        async with self._uart_lock:return await self._send_command_locked_async(command,timeout_ms)

    async def get_all_state_async(self,timeout_ms=None): return await self.send_command_async("AT+ALLSTATE",timeout_ms)
    async def get_version_async(self,timeout_ms=None): return await self.send_command_async("AT+VER=?",timeout_ms)
    async def get_device_sn_async(self,timeout_ms=None): return await self.send_command_async("AT+DEVSN=?",timeout_ms)
    async def get_mac_async(self,timeout_ms=None): return await self.send_command_async("AT+MAC=?",timeout_ms)
    async def get_status_async(self,timeout_ms=None): return await self.send_command_async("AT+STATUS=?",timeout_ms)
    async def get_role_async(self,timeout_ms=None): return await self.send_command_async("AT+ROLE=?",timeout_ms)
    async def set_role_async(self,role,timeout_ms=None): return await self.send_command_async("AT+ROLE={}".format(role),timeout_ms)
    async def get_mode_async(self,timeout_ms=None): return await self.send_command_async("AT+MODE=?",timeout_ms)
    async def set_mode_async(self,mode,timeout_ms=None): return await self.send_command_async("AT+MODE={}".format(mode),timeout_ms)
    async def get_sta_async(self,timeout_ms=None): return await self.send_command_async("AT+STA=?",timeout_ms)
    async def set_sta_async(self,ssid,security,password,timeout_ms=None): return await self.send_command_async("AT+STA={},{},{}".format(ssid,security,password),timeout_ms)
    async def get_sta_ip_async(self,timeout_ms=None): return await self.send_command_async("AT+STAIP=?",timeout_ms)
    async def set_sta_ip_async(self,ip_mode,ip,mask,gateway,dns,timeout_ms=None): return await self.send_command_async("AT+STAIP={},{},{},{},{}".format(ip_mode,ip,mask,gateway,dns),timeout_ms)
    async def get_ap_async(self,timeout_ms=None): return await self.send_command_async("AT+AP=?",timeout_ms)
    async def set_ap_async(self,ssid,security,password,timeout_ms=None): return await self.send_command_async("AT+AP={},{},{}".format(ssid,security,password),timeout_ms)
    async def get_ap_ip_async(self,timeout_ms=None): return await self.send_command_async("AT+APIP=?",timeout_ms)
    async def set_ap_ip_async(self,ip,mask,gateway,dns,timeout_ms=None): return await self.send_command_async("AT+APIP={},{},{},{}".format(ip,mask,gateway,dns),timeout_ms)
    async def get_ap_channel_async(self,timeout_ms=None): return await self.send_command_async("AT+CHAN=?",timeout_ms)
    async def set_ap_channel_async(self,channel,timeout_ms=None): return await self.send_command_async("AT+CHAN={}".format(channel),timeout_ms)
    async def get_socket_async(self,timeout_ms=None): return await self.send_command_async("AT+SOCK=?",timeout_ms)
    async def set_socket_async(self,protocol,socket_role,remote_ip,remote_port,local_port,timeout_ms=None): return await self.send_command_async("AT+SOCK={},{},{},{},{}".format(protocol,socket_role,remote_ip,remote_port,local_port),timeout_ms)
    async def get_uart_config_async(self,timeout_ms=None): return await self.send_command_async("AT+UART=?",timeout_ms)
    async def set_uart_config_async(self,baudrate,data_bits,parity,stop_bits,timeout_ms=None): return await self.send_command_async("AT+UART={},{},{},{}".format(baudrate,data_bits,parity,stop_bits),timeout_ms)
    async def reset_async(self,confirm=False,timeout_ms=None):
        if not confirm: raise ValueError("reset requires confirm=True")
        return await self.send_command_async("AT+RESET",timeout_ms)
    async def restore_factory_defaults_async(self,confirm=False,timeout_ms=None):
        if not confirm: raise ValueError("restore requires confirm=True")
        return await self.send_command_async("AT+RESTORE",timeout_ms)

    async def write_async(self,data):
        payload = _to_bytes(data)
        async with self._uart_lock:
            if self._command_mode:
                raise RuntimeError("exit command mode before writing transparent data")
            return self._write_bytes(payload)
    async def read_async(self,size=None,timeout_ms=0):
        if size is not None and (not isinstance(size, int) or size <= 0):
            raise ValueError("size must be a positive int or None")
        timeout=self._timeout_ms if timeout_ms is None else timeout_ms
        if not isinstance(timeout, int):
            raise TypeError("timeout_ms must be int")
        if timeout < 0:
            raise ValueError("timeout_ms cannot be negative")
        async with self._uart_lock:
            if self._command_mode:
                raise RuntimeError("exit command mode before reading transparent data")
            deadline=time.ticks_add(time.ticks_ms(),timeout)
            while True:
                n=self._uart_any()
                if n:
                    data = await self._read_bytes_async(deadline, 0 if size is None else size)
                    return data if data is not None else b""
                if timeout == 0 or time.ticks_diff(deadline,time.ticks_ms())<=0:
                    return b""
                await asyncio.sleep_ms(2)
    async def readline_async(self,timeout_ms=0,max_bytes=1024):
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms < 0:
            raise ValueError("timeout_ms cannot be negative")
        if not isinstance(max_bytes, int):
            raise TypeError("max_bytes must be int")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be greater than 0")
        result=bytearray()
        async with self._uart_lock:
            if self._command_mode:
                raise RuntimeError("exit command mode before reading transparent data")
            deadline=time.ticks_add(time.ticks_ms(),timeout_ms)
            while len(result)<max_bytes:
                n=self._uart_any()
                if n:
                    item=await self._read_bytes_async(deadline, 1)
                    if item:
                        result.extend(item)
                        if item==b"\n":break
                        if len(result) % 32 == 0:
                            await asyncio.sleep_ms(0)
                elif timeout_ms == 0 or time.ticks_diff(deadline,time.ticks_ms())<=0:
                    break
                else:
                    await asyncio.sleep_ms(2)
        return bytes(result)
    async def is_command_mode_async(self): return self._command_mode
    async def deinit_async(self):
        async with self._uart_lock:self._closed=True;self._uart=None
    async def aclose(self): await self.deinit_async()
