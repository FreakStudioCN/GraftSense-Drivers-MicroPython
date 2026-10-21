"""Cooperative, single-reader async facade for EWM550 UWB UART commands."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from ewm550_uwb import EWM550_UWB


class EWM550_UWBAsync(EWM550_UWB):
    """Preserves the EWM550 AT protocol while serializing UART transactions."""

    def __init__(self, uart, rx_timeout_ms=600):
        super().__init__(uart, rx_timeout_ms)
        self._uart_lock = asyncio.Lock()
        self._closed = False

    def _deadline(self, timeout_ms):
        return time.ticks_add(time.ticks_ms(), timeout_ms)

    async def _read_uart_async(self, deadline, drain=False):
        """The only UART reader: drain stale bytes or await one response."""
        if drain:
            while self._uart.any():
                self._uart.read()
            return None
        while not self._uart.any():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return None
            await asyncio.sleep_ms(5)
        return self._uart.read()

    async def _exchange_async(self, command, expect_response=True):
        if self._closed or self._uart is None:
            return False, "UART is closed"
        async with self._uart_lock:
            try:
                await self._read_uart_async(self._deadline(0), drain=True)
                self._uart.write(command)
                # Source requires a 30 ms command guard and a 50 ms response guard.
                await asyncio.sleep_ms(30)
                if not expect_response:
                    return True, "exit success"
                await asyncio.sleep_ms(50)
                response = await self._read_uart_async(self._deadline(self.rx_timeout_ms))
                if response is None:
                    return False, "no data"
                return True, response.decode("utf-8").strip()
            except Exception as exc:
                return False, "UART transaction error: {}".format(exc)

    @staticmethod
    def _reply(ok, response, expected, failure):
        if ok and (response == expected if isinstance(expected, str) else response.startswith(expected)):
            return True, response
        return False, "{}: {}".format(failure, response if response else "no response")

    async def enter_at_mode_async(self):
        return self._reply(*(await self._exchange_async(b"+++")), "AT_MODE", "enter AT mode failed")

    async def exit_at_mode_async(self):
        return await self._exchange_async(b"AT+EXIT", False)

    async def check_async(self):
        return self._reply(*(await self._exchange_async(b"AT")), "+OK", "module unresponsive")

    async def restore_factory_settings_async(self):
        return self._reply(*(await self._exchange_async(b"AT+RESTORE")), "+OK", "restore failed")

    async def reset_module_async(self):
        ok, response = await self._exchange_async(b"AT+RESET")
        ok, response = self._reply(ok, response, "+OK", "reset failed")
        if ok:
            await asyncio.sleep_ms(100)
        return ok, response

    async def _set_async(self, command, value, validator, attr, failure):
        if not validator(value):
            return False, failure[0]
        ok, response = await self._exchange_async(command.format(value).encode())
        ok, response = self._reply(ok, response, "+OK", failure[1])
        if ok:
            setattr(self, attr, value)
        return ok, response

    async def _get_async(self, command, prefix, attr, convert, failure):
        ok, response = await self._exchange_async(command)
        if ok and response.startswith(prefix):
            try:
                value = convert(response.split(":", 1)[1].strip().strip("<>"))
            except (ValueError, IndexError, KeyError):
                return False, "{}: invalid response".format(failure)
            setattr(self, attr, value)
            return True, str(value)
        return False, "{}: {}".format(failure, response if response else "no response")

    async def get_version_async(self):
        ok, response = await self._exchange_async(b"AT+VERSION")
        if ok and response.startswith("VERSION:"):
            self.version = response.split(":", 1)[1].strip()
            return True, self.version
        return False, "get version failed: {}".format(response if response else "no response")

    async def set_role_async(self, role): return await self._set_async("AT+ROLE={}", role, lambda x: x in self.Role.values(), "role", ("invalid role, must be {}".format(self.Role.values()), "set role failed"))
    async def get_role_async(self): return await self._get_async(b"AT+ROLE=?", "ROLE:", "role", int, "get role failed")
    async def set_channel_async(self, ch): return await self._set_async("AT+CH={}", ch, lambda x: x in self.CHANNEL.values(), "ch", ("invalid channel, must be {}".format(self.CHANNEL.values()), "set channel failed"))
    async def get_channel_async(self): return await self._get_async(b"AT+CH=?", "CH:", "ch", int, "get channel failed")

    async def set_baud_async(self, baud_param):
        if baud_param not in self.Baud:
            return False, "invalid baud param, must be {}".format(self.Baud.keys())
        ok, response = await self._exchange_async("AT+BAUD={}".format(baud_param).encode())
        ok, response = self._reply(ok, response, "+OK", "set baud failed")
        if ok: self.baud = self.Baud[baud_param]
        return ok, response
    async def get_baud_async(self):
        ok, response = await self._exchange_async(b"AT+BAUD=?")
        if ok and response.startswith("BAUD:"):
            try:
                value = int(response.split(":", 1)[1].strip()); self.baud = self.Baud[value]
                return True, str(value)
            except (ValueError, IndexError, KeyError): pass
        return False, "get baud failed: {}".format(response if response else "no response")

    async def set_power_async(self, power): return await self._set_async("AT+POWER={}", power, lambda x: x in self.POWER.values(), "power", ("invalid power, must be {}".format(self.POWER.values()), "set power failed"))
    async def get_power_async(self): return await self._get_async(b"AT+POWER=?", "POWER:", "power", int, "get power failed")
    async def set_responder_num_async(self, num): return await self._set_async("AT+RESPONDER_NUM={}", num, lambda x: 1 <= x <= 5, "responder_num", ("invalid responder num, must be 1-5", "set responder num failed"))
    async def get_responder_num_async(self): return await self._get_async(b"AT+RESPONDER_NUM=?", "RESPONDER_NUM:", "responder_num", int, "get responder num failed")

    async def _set_address_async(self, command, addr, length, attr, failure):
        addr = addr.strip().upper()
        if len(addr) != length or not all(c in "0123456789ABCDEF" for c in addr):
            return False, failure[0]
        ok, response = await self._exchange_async(command.format(addr).encode())
        ok, response = self._reply(ok, response, "+OK", failure[1])
        if ok: setattr(self, attr, addr)
        return ok, response
    async def set_src_addr_async(self, addr): return await self._set_address_async("AT+SRCADDR={}", addr, 4, "src_addr", ("invalid src addr, must be 4 hex chars (0000-FFFF)", "set src addr failed"))
    async def get_src_addr_async(self): return await self._get_async(b"AT+SRCADDR=?", "SRC_ADDR:", "src_addr", str, "get src addr failed")
    async def set_dst_addr_async(self, addr): return await self._set_address_async("AT+DSTADDR={}", addr, 20, "dst_addr", ("invalid dst addr, must be 20 hex chars", "set dst addr failed"))
    async def get_dst_addr_async(self): return await self._get_async(b"AT+DSTADDR=?", "DST_ADDR:", "dst_addr", str, "get dst addr failed")
    async def set_print_interval_async(self, intv): return await self._set_async("AT+INTV={}", intv, lambda x: 30 <= x <= 2000, "intv", ("invalid intv, must be 30-2000ms", "set intv failed"))
    async def get_print_interval_async(self): return await self._get_async(b"AT+INTV=?", "INTV:", "intv", int, "get intv failed")
    async def enter_sleep_mode_async(self, sleep_mode): return await self._set_async("AT+SLEEP={}", sleep_mode, lambda x: x in self.SLEEP.values(), "sleep_mode", ("invalid sleep mode, must be {}".format(self.SLEEP.values()), "set sleep failed"))

    async def parse_ranging_data_async(self, data):
        return self.parse_ranging_data(data)

    async def aclose(self):
        async with self._uart_lock:
            self._closed = True
            self._uart = None