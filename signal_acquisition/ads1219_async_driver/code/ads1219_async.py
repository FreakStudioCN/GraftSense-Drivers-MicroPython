try:
 import uasyncio as asyncio
except ImportError:
 import asyncio
import time
class ADS1219Async:
 def __init__(self,adc):self._adc=adc;self._lock=asyncio.Lock();self._closed=False
 async def set_channel_async(self,v):
  async with self._lock:self._adc.set_channel(v)
 async def set_conversion_mode_async(self,v):
  async with self._lock:self._adc.set_conversion_mode(v)
 async def set_gain_async(self,v):
  async with self._lock:self._adc.set_gain(v)
 async def set_data_rate_async(self,v):
  async with self._lock:self._adc.set_data_rate(v)
 async def set_vref_async(self,v):
  async with self._lock:self._adc.set_vref(v)
 async def read_data_async(self,timeout_ms=1000):
  async with self._lock:
   single=(self._adc.read_config()&self._adc.CM_CONTINUOUS)==self._adc.CM_SINGLE
   if single:self._adc.start_sync()
  deadline=time.ticks_add(time.ticks_ms(),timeout_ms)
  while True:
   async with self._lock:ready=bool(self._adc.read_status()&0x80)
   if ready:break
   if time.ticks_diff(deadline,time.ticks_ms())<=0:raise RuntimeError('ADS1219 conversion timeout')
   await asyncio.sleep_ms(1)
  async with self._lock:return self._adc.read_data_irq()
 async def aclose(self):
  if not self._closed:
   async with self._lock:self._adc.powerdown();self._closed=True
