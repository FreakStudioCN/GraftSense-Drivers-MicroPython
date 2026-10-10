# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from as726x_async import AS726XAsync
from as726x import AS726X, AS726X_GAIN_16X, AS726X_I2C_ADDR, AS726X_ONE_SHOT_READING_ALL_CHANNELS, SENSORTYPE_AS7263


AS726X = AS726XAsync

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: AS7263 spectral sensor RP2040 test")
    sensor = None
    try:
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
        print("I2C bus initialized: id=0 scl=5 sda=4 freq=100000")
        devices = i2c.scan()
        print("I2C scan result: %s" % [hex(device) for device in devices])
        if AS726X_I2C_ADDR not in devices:
            raise RuntimeError("AS7263 not found at address 0x%02X" % AS726X_I2C_ADDR)
        sensor = AS726X(i2c, AS726X_I2C_ADDR)
        if sensor.get_sensor_type() != SENSORTYPE_AS7263:
            raise RuntimeError("Unexpected AS726x device id")
        sensor.set_gain(AS726X_GAIN_16X)
        sensor.set_integration_time(50)
        sensor.set_measurement_mode(AS726X_ONE_SHOT_READING_ALL_CHANNELS)
        print("AS7263 initialized: addr=0x%02X gain=16X integration=50 mode=one-shot" % AS726X_I2C_ADDR)
        while True:
            try:
                await sensor.take_one_shot_sync_measurement()
                data = sensor.get_calibrated_rstuvw()
                print("AS7263 calibrated R=%.4f S=%.4f T=%.4f U=%.4f V=%.4f W=%.4f" % data)
            except OSError as error:
                print("I2C read failed: %s" % error)
            except Exception as error:
                print("Sensor read failed: %s" % error)
            await asyncio.sleep_ms(2000)
    finally:
        if sensor:
            sensor.deinit()
        print("Program exited")


# ======================================== 主程序 ==============================================
if __name__ == "__main__":
    asyncio.run(main())