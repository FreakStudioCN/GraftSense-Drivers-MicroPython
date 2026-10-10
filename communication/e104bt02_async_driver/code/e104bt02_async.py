"""Cooperative, single-reader E104-BT02 UART facade."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
import e104bt02 as _wire
from e104bt02 import E104BT02, E104BT02Error, E104BT02TimeoutError, E104BT02FrameError, E104BT02ResponseError

class E104BT02Async(E104BT02):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs); self._uart_lock=asyncio.Lock(); self._closed=False
    async def _read_chunk_async(self,deadline,drain=False):
        if drain:
            while self._uart.any(): self._uart.read()
            return b""
        while not self._uart.any():
            if time.ticks_diff(deadline,time.ticks_ms())<=0:return None
            await asyncio.sleep_ms(self._poll_interval_ms)
        return self._uart.read(self._uart.any())
    async def _flush_input_async(self,quiet_ms=80):
        deadline=time.ticks_add(time.ticks_ms(),self._timeout_ms); quiet=time.ticks_ms()
        while time.ticks_diff(deadline,time.ticks_ms())>0:
            if self._uart.any(): await self._read_chunk_async(time.ticks_ms(), drain=True);quiet=time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(),quiet)>=quiet_ms:return
            await asyncio.sleep_ms(self._poll_interval_ms)
    async def _read_at_frame_async(self,timeout_ms=0):
        deadline=time.ticks_add(time.ticks_ms(),self._resolve_timeout(timeout_ms));frame=bytearray();active=False
        while time.ticks_diff(deadline,time.ticks_ms())>0:
            chunk=await self._read_chunk_async(deadline)
            if not chunk:continue
            for value in chunk:
                if not active:
                    if value==_wire.FRAME_START:active=True;frame=bytearray((value,))
                    continue
                frame.append(value)
                if len(frame)>self._max_frame_len:raise E104BT02FrameError("AT response frame exceeded driver max_frame_len")
                if value==_wire.FRAME_END:return bytes(frame)
        if active:raise E104BT02TimeoutError("No complete E104-BT02 AT frame before timeout. Ensure the module is awake and P00/MOD is low.")
        raise E104BT02TimeoutError("No valid E104-BT02 AT response. Ensure the module is awake and P00/MOD is low.")
    async def _payload_async(self,frame,timeout_ms=0):
        async with self._uart_lock:
            await self._flush_input_async(); self._send_at_frame(frame)
            return _wire._strip_frame(await self._read_at_frame_async(timeout_ms))
    async def _ascii_async(self,frame,timeout_ms=0):
        text=_wire._decode_ascii(await self._payload_async(frame,timeout_ms))
        if text in _wire.ERROR_PAYLOADS:raise E104BT02ResponseError("Module returned error response: %s"%text)
        return text
    async def _ok_async(self,frame,timeout_ms=0):
        if await self._ascii_async(frame,timeout_ms)!=_wire.SUCCESS_OK:raise E104BT02ResponseError("Unexpected success response")
        return True
    async def get_baudrate_async(self,timeout_ms=0):return int(await self._ascii_async(_wire.COMMAND_COMBAUD,timeout_ms))
    async def set_baudrate_async(self,baudrate,timeout_ms=0):return await self._ok_async(_wire._build_at_frame(_wire.COMMAND_BAUD_PREFIX+str(baudrate).encode()),timeout_ms)
    async def restore_factory_defaults_async(self,timeout_ms=0):return await self._ok_async(_wire.COMMAND_RESTORE,timeout_ms)
    async def get_stop_bits_async(self,timeout_ms=0):
        value=await self._ascii_async(_wire.COMMAND_STOPBIT,timeout_ms);return 1 if value=="STOPBITS1" else 2 if value=="STOPBITS2" else (_ for _ in ()).throw(E104BT02ResponseError("Unexpected STOPBIT response: %s"%value))
    async def get_parity_async(self,timeout_ms=0):
        value=await self._ascii_async(_wire.COMMAND_PARITY,timeout_ms);return {"NOP":"none","EVENP":"even","ODDP":"odd"}.get(value) or (_ for _ in ()).throw(E104BT02ResponseError("Unexpected PARITY response: %s"%value))
    async def get_module_name_async(self,timeout_ms=0):return await self._ascii_async(_wire.COMMAND_MNAME,timeout_ms)
    async def get_factory_name_async(self,timeout_ms=0):return await self._ascii_async(_wire.COMMAND_FNAME,timeout_ms)
    async def get_software_version_async(self,timeout_ms=0):return await self._ascii_async(_wire.COMMAND_SVER,timeout_ms)
    async def get_hardware_version_async(self,timeout_ms=0):return await self._ascii_async(_wire.COMMAND_HVER,timeout_ms)
    async def get_serial_number_raw_async(self,timeout_ms=0):return await self._payload_async(_wire.COMMAND_MSN,timeout_ms)
    async def get_serial_number_async(self,timeout_ms=0):return _wire._decode_ascii((await self.get_serial_number_raw_async(timeout_ms)).rstrip(b'\x00'))
    async def get_state_async(self,timeout_ms=0):return await self._ascii_async(_wire.COMMAND_STATE,timeout_ms)
    async def get_mtu_async(self,timeout_ms=0):return int(await self._ascii_async(_wire.COMMAND_MMTU,timeout_ms))
    async def get_role_async(self,timeout_ms=0):return await self._ascii_async(_wire.COMMAND_ROLETYPE,timeout_ms)
    async def get_mac_raw_async(self,timeout_ms=0):
        value=await self._payload_async(_wire.COMMAND_MAC,timeout_ms)
        if len(value)!=6:raise E104BT02ResponseError("MAC payload must be 6 bytes")
        return value
    async def get_mac_async(self,timeout_ms=0):return _wire.mac_bytes_to_text(await self.get_mac_raw_async(timeout_ms))
    async def set_module_name_async(self,name,timeout_ms=0):return await self._ok_async(_wire._build_at_frame(_wire.COMMAND_NAME_PREFIX+name.encode('ascii')),timeout_ms)
    async def set_mtu_async(self,mtu,timeout_ms=0):return await self._ok_async(_wire._build_at_frame(_wire.COMMAND_MTU_PREFIX+str(mtu).encode()),timeout_ms)
    async def get_advertising_state_async(self,timeout_ms=0):
        value=await self._ascii_async(_wire.COMMAND_ADVSTATE,timeout_ms);return 'on' if value=='ADVON' else 'off' if value=='ADVOFF' else (_ for _ in ()).throw(E104BT02ResponseError("Unexpected ADVSTATE response: %s"%value))
    async def start_advertising_async(self,timeout_ms=0):return await self._ok_async(_wire.COMMAND_STARTADV,timeout_ms)
    async def stop_advertising_async(self,timeout_ms=0):return await self._ok_async(_wire.COMMAND_STOPADV,timeout_ms)
    async def set_advertising_interval_async(self,units,timeout_ms=0):return await self._ok_async(_wire._build_at_frame(_wire.COMMAND_ADVGAP_PREFIX+str(units).encode()),timeout_ms)
    async def get_advertising_interval_async(self,timeout_ms=0):return int((await self._ascii_async(_wire.COMMAND_AGAP,timeout_ms))[1:])
    async def send_async(self,data):
        async with self._uart_lock:return self.send(data)
    async def read_async(self,max_bytes=0,timeout_ms=0):
        deadline=time.ticks_add(time.ticks_ms(),self._resolve_timeout(timeout_ms))
        async with self._uart_lock:
            data=await self._read_chunk_async(deadline)
            return bytes(data[:max_bytes]) if data and max_bytes else bytes(data or b'')
    async def read_available_async(self):
        async with self._uart_lock:
            return bytes(await self._read_chunk_async(time.ticks_ms()) or b'') if self._uart.any() else b''
    async def any_async(self):return self.any()
    async def deinit_async(self):
        async with self._uart_lock:self._closed=True;self._uart=None
    async def close_async(self):await self.deinit_async()
    async def aclose(self):await self.deinit_async()