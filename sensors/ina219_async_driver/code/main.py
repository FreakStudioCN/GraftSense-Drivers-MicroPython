try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from sensor_pack_2.bus_service import I2cAdapter
from ina_ti_async import INA219Async
async def main():
    i2c = None; sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        if 0x40 not in i2c.scan(): raise RuntimeError("INA219 not found at address 0x40")
        sensor = INA219Async(I2cAdapter(i2c), address=0x40, shunt_resistance=0.1)
        await sensor.set_bus_voltage_range_async(False)
        await sensor.set_bus_adc_resolution_async(0x03)
        await sensor.set_shunt_adc_resolution_async(0x03)
        await sensor.set_max_expected_current_async(2.0)
        await sensor.start_measurement_async(continuous=True, enable_calibration=True)
        wait_time_us = await sensor.get_conversion_cycle_time_async()
        last_print_time = time.ticks_ms()
        while True:
            if time.ticks_diff(time.ticks_ms(), last_print_time) >= 1000:
                await asyncio.sleep_ms((wait_time_us + 999) // 1000)
                print("Bus: {:.3f} V, Shunt: {:.6f} V, Current: {:.3f} A, Power: {:.3f} W".format(await sensor.get_voltage_async(), await sensor.get_shunt_voltage_async(), await sensor.get_current_async(), await sensor.get_power_async()))
                last_print_time = time.ticks_ms()
            await asyncio.sleep_ms(10)
    finally:
        if sensor is not None: await sensor.aclose()
        if i2c is not None:
            deinit=getattr(i2c,'deinit',None)
            if deinit is not None: deinit()
if __name__ == '__main__': asyncio.run(main())