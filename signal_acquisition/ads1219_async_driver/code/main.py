try:
 import uasyncio as asyncio
except ImportError:
 import asyncio
from machine import Pin,I2C
from ads1219 import ADS1219
from ads1219_async import ADS1219Async
async def main():
 await asyncio.sleep(3)
 i2c=I2C(0,scl=Pin(5),sda=Pin(4),freq=100000)
 a=None
 try:
  address=next((x for x in i2c.scan() if x in [0x40,0x41,0x42,0x43]),None)
  if address is None:raise RuntimeError('ADS1219 not found')
  adc=ADS1219(i2c=i2c,address=address);a=ADS1219Async(adc)
  await a.set_channel_async(ADS1219.CHANNEL_AIN1);await a.set_conversion_mode_async(ADS1219.CM_SINGLE);await a.set_gain_async(ADS1219.GAIN_1X);await a.set_data_rate_async(ADS1219.DR_20_SPS);await a.set_vref_async(ADS1219.VREF_INTERNAL)
  result=await a.read_data_async();print('result = %s, mV = %.2f'%(result,result*ADS1219.VREF_INTERNAL_MV/ADS1219.POSITIVE_CODE_RANGE))
 finally:
  try:
   if a is not None:await a.aclose()
  finally:
   i2c.deinit()
asyncio.run(main())
