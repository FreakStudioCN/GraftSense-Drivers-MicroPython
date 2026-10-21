"""RM3100 asynchronous magnetometer demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from _gs_rm3100_sensor_pack.bus_service import I2cAdapter
from _gs_rm3100_rm3100mod import RM3100
from rm3100_async import RM3100Async
# ======================================== 全局变量 ============================================
I2C_SCL_PIN=5
I2C_SDA_PIN=4
I2C_FREQ=400000
TARGET_ADDRS=(0x20,0x21,0x22,0x23)
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor=None
    try:
        i2c=SoftI2C(sda=Pin(I2C_SDA_PIN),scl=Pin(I2C_SCL_PIN),freq=I2C_FREQ)
        address=next((item for item in i2c.scan() if item in TARGET_ADDRS),None)
        if address is None: raise RuntimeError('RM3100 not found')
        sensor=RM3100Async(RM3100(I2cAdapter(i2c),address=address))
        print('Self test:', await sensor.perform_self_test_async())
        print('ID:', await sensor.get_id_async())
        for axis in 'XYZ':
            print(axis, 'cycle count:', await sensor.get_axis_cycle_count_async(axis))
        await sensor.start_measure_async('XYZ',6,True)
        print('Continuous:', await sensor.is_continuous_meas_mode_async())
        print('Data ready:', await sensor.is_data_ready_async())
        if await sensor.wait_data_ready_async():
            for axis in 'XYZ':
                print(axis, await sensor.get_meas_result_async(axis))
        await sensor.start_measure_async('XYZ',6,False)
        while True:
            if await sensor.wait_data_ready_async():
                print(await sensor.get_axis_async(-1))
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None: await sensor.aclose()
asyncio.run(main())