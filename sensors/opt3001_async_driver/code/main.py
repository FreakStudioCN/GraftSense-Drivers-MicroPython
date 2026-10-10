"""OPT3001 asynchronous light-sensor demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from opt3001mod_async import OPT3001Async

# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDRS = (0x44, 0x45)
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000

# ======================================== 功能函数 ============================================
def show_header(info, width=32):
    print('-' * width)
    print(info)
    print('-' * width)

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    print('FreakStudio: OPT3001 light sensor test')
    i2c_bus = None
    sensor = None
    try:
        i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        devices_list = i2c_bus.scan()
        if not devices_list:
            raise RuntimeError('I2C scan found no devices')
        for address in devices_list:
            if address in TARGET_SENSOR_ADDRS:
                try:
                    sensor = OPT3001Async(I2cAdapter(i2c_bus), address)
                    break
                except Exception as exc:
                    print('Sensor init failed:', exc)
        if sensor is None:
            raise RuntimeError('No target sensor found on I2C bus')
        identity = await sensor.get_id_async()
        print('manufacturer id: 0x%x; device id: 0x%x' %
              (identity.manufacturer_id, identity.device_id))
        show_header('Single measurement mode')
        sensor.long_conversion_time = False
        await sensor.start_measurement_async(continuously=False, lx_range_index=10)
        print(await sensor.read_config_from_sensor_async(return_value=True))
        cycle_time = await sensor.get_conversion_cycle_time_async()
        for _ in range(10):
            await asyncio.sleep_ms(cycle_time + 50)
            status = await sensor.get_data_status_async()
            if status.conversion_ready:
                print(await sensor.get_measurement_value_async(value_index=1))
            await sensor.start_measurement_async(continuously=False, lx_range_index=12)
        show_header('Automatic measurement mode')
        sensor.long_conversion_time = True
        await sensor.start_measurement_async(continuously=True, lx_range_index=12)
        print(await sensor.read_config_from_sensor_async(return_value=True))
        cycle_time = await sensor.get_conversion_cycle_time_async()
        while True:
            await asyncio.sleep_ms(cycle_time)
            status = await sensor.get_data_status_async()
            if status.conversion_ready:
                print(await sensor.get_measurement_value_async(value_index=1))
    finally:
        if sensor is not None:
            await sensor.deinit_async()
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, 'deinit', None)
            if deinit is not None:
                deinit()
asyncio.run(main())