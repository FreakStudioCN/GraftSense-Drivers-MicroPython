try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from tas_755c_eth import TAS_755C_ETH

class TAS_755C_ETHAsync(TAS_755C_ETH):
    def __init__(self, uart):
        super().__init__(uart); self._lock = asyncio.Lock()
    def _read_uart_once(self):
        """The command lock makes this the sole UART receive primitive."""
        return self._uart.read()
    async def _read_at_result_unlocked(self, timeout_ms):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        chunks = []
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self._uart.any():
                chunk = self._read_uart_once()
                if chunk:
                    chunks.append(chunk)
                    text = b"".join(chunks).decode("utf-8", "ignore")
                    if "OK" in text or "ERROR" in text:
                        return ("OK" in text and "ERROR" not in text, text)
            await asyncio.sleep_ms(10)
        raise RuntimeError("TAS755C AT response timeout")
    async def _at_async(self, command, timeout_ms=3000, raw=False):
        async with self._lock:
            self._uart.write(command if raw else (command + "\r\n").encode())
            return await self._read_at_result_unlocked(timeout_ms)
    async def enter_command_mode_async(self):
        async with self._lock:
            self._uart.write(b"+++")
            await asyncio.sleep_ms(50)
            return await self._read_at_result_unlocked(3000)
    async def enter_data_mode_async(self): return await self._at_async("ATO")
    async def set_ip_config_async(self, mode, ip, gateway, subnet, dns): return await self._at_async('AT+IPCONFIG={},{},{},{},{}'.format(mode,ip,gateway,subnet,dns))
    async def get_ip_config_async(self): return await self._at_async("AT+IPCONFIG?")
    async def set_tcp_config_async(self, local_port, remote_port, mode, remote_address): return await self._at_async('AT+TCPCFG={},{},{},{}'.format(local_port,remote_port,mode,remote_address))
    async def get_tcp_config_async(self): return await self._at_async("AT+TCPCFG?")
    async def set_http_config_async(self, net_status, method, header_return): return await self._at_async('AT+HTTPCFG={},{},{}'.format(net_status,method,header_return))
    async def save_async(self): return await self._at_async("AT&W")
    async def restart_async(self): return await self._at_async("AT+CFUN=1,1",10000)
    async def send_data_async(self, data):
        async with self._lock: return self._uart.write(data if isinstance(data,bytes) else data.encode())
    async def read_data_async(self, timeout_ms=3000):
        async with self._lock:
            deadline=time.ticks_add(time.ticks_ms(),timeout_ms)
            while time.ticks_diff(deadline,time.ticks_ms())>0:
                if self._uart.any(): return self._read_uart_once()
                await asyncio.sleep_ms(10)
        return b""
    async def aclose(self): self._uart=None
