"""MS5611 asynchronous pressure sensor demonstration."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C
from ms5611_async import MS5611Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================


def init_i2c():
    try:
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        print(f"I2C initialized successfully, scanned devices: {[hex(address) for address in i2c.scan()]}")
        return i2c
    except Exception as error:
        print(f"I2C initialization failed: {error}")
        return None


def set_rate(sensor, name, value, values):
    try:
        if value not in values:
            print(f"Invalid value {value}, skipping")
            return False
        setattr(sensor, name, value)
        print(f"Set successfully - Current {name}: {getattr(sensor, name)} (Value: {value})")
        return True
    except Exception as error:
        print(f"Failed to set {name}: {error}")
        return False


async def read(sensor):
    try:
        return await sensor.measurements_async(), True
    except OSError as error:
        print(f"Failed to read measurements: {error}")
    except Exception as error:
        print(f"Unknown error: {error}")
    return (0.0, 0.0), False


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: MS5611 pressure sensor test with oversampling rate configuration")
    i2c_bus = init_i2c()
    if not i2c_bus:
        raise SystemExit("I2C initialization failed, program exited")
    sensor = MS5611Async(i2c_bus, address=0x77)
    try:
        print("MS5611 sensor initialized successfully")
        print("\\n" + "=" * 65)
        print("=== 1. Temperature Oversampling Rate Configuration (Pressure OSR=4096)")
        set_rate(sensor, "pressure_oversample_rate", sensor.PRESS_OSR_4096, sensor.pressure_oversample_rate_values)
        for rate in sensor.temperature_oversample_rate_values:
            if set_rate(sensor, "temperature_oversample_rate", rate, sensor.temperature_oversample_rate_values):
                print("    3 consecutive measurements:")
                for index in range(3):
                    (temp, press), success = await read(sensor)
                    if success:
                        print(f"      Measurement {index + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
                    await asyncio.sleep_ms(500)
            await asyncio.sleep_ms(1000)
        print("=== 2. Pressure Oversampling Rate Configuration (Temperature OSR=4096)")
        set_rate(sensor, "temperature_oversample_rate", sensor.TEMP_OSR_4096, sensor.temperature_oversample_rate_values)
        for rate in sensor.pressure_oversample_rate_values:
            if set_rate(sensor, "pressure_oversample_rate", rate, sensor.pressure_oversample_rate_values):
                print("    3 consecutive measurements:")
                for index in range(3):
                    (temp, press), success = await read(sensor)
                    if success:
                        print(f"      Measurement {index + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
                    await asyncio.sleep_ms(500)
            await asyncio.sleep_ms(1000)
        print("=== 3. Combined Oversampling Rate Demo (Low/Medium/High)")
        combinations = ((sensor.TEMP_OSR_256, sensor.PRESS_OSR_256), (sensor.TEMP_OSR_1024, sensor.PRESS_OSR_1024), (sensor.TEMP_OSR_4096, sensor.PRESS_OSR_4096))
        for index, (temp_rate, pressure_rate) in enumerate(combinations):
            print(f"\\n  Combination {index + 1}:")
            set_rate(sensor, "temperature_oversample_rate", temp_rate, sensor.temperature_oversample_rate_values)
            set_rate(sensor, "pressure_oversample_rate", pressure_rate, sensor.pressure_oversample_rate_values)
            temperatures, pressures = [], []
            for sample in range(5):
                (temp, press), success = await read(sensor)
                if success:
                    temperatures.append(temp)
                    pressures.append(press)
                    print(f"      Measurement {sample + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
                await asyncio.sleep_ms(300)
            if temperatures and pressures:
                print(f"      Average - Temperature: {sum(temperatures) / len(temperatures):.2f}°C, Pressure: {sum(pressures) / len(pressures):.2f}KPa")
                print(f"      Temperature fluctuation: ±{max(temperatures) - min(temperatures):.2f}°C")
                print(f"      Pressure fluctuation: ±{max(pressures) - min(pressures):.2f}KPa")
        print("=== 4. Final Sensor Configuration and Continuous Measurement")
        set_rate(sensor, "temperature_oversample_rate", sensor.TEMP_OSR_4096, sensor.temperature_oversample_rate_values)
        set_rate(sensor, "pressure_oversample_rate", sensor.PRESS_OSR_4096, sensor.pressure_oversample_rate_values)
        print("\\n  Continuous measurement (10 times, highest precision):")
        for index in range(10):
            (temp, press), success = await read(sensor)
            if success:
                print(f"    Measurement {index + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
            await asyncio.sleep_ms(800)
        print("\\n=== Demo completed ===")
    finally:
        await sensor.aclose()


if __name__ == "__main__":
    asyncio.run(main())