import time

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import _gs_sht45_sht45 as sht45
from machine import I2C, Pin
from sht45_async import SHT45Async

try:
    import micropython
    micropython.alloc_emergency_exception_buf(100)
except (ImportError, AttributeError):
    pass

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
_PRINT_INTERVAL_MS = 2000


async def test_all_precision_modes(sht):
    print("\n=== Testing All Precision Modes ===")
    modes = [
        (sht45.HIGH_PRECISION, "HIGH_PRECISION"),
        (sht45.MEDIUM_PRECISION, "MEDIUM_PRECISION"),
        (sht45.LOW_PRECISION, "LOW_PRECISION"),
    ]
    for mode_value, mode_name in modes:
        sht.temperature_precision = mode_value
        print("Precision set to: %s" % mode_name)
        await asyncio.sleep_ms(500)
        temp, hum = await sht.measurements_async()
        print("  Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
    sht.temperature_precision = sht45.HIGH_PRECISION
    print("Precision restored to: %s" % sht.temperature_precision)


async def test_all_heater_settings(sht):
    print("\n=== Testing Heater Settings ===")
    powers = [
        (sht45.HEATER200mW, "HEATER200mW"),
        (sht45.HEATER110mW, "HEATER110mW"),
        (sht45.HEATER20mW, "HEATER20mW"),
    ]
    times = [(sht45.TEMP_1, "TEMP_1"), (sht45.TEMP_0_1, "TEMP_0_1")]
    for power_value, power_name in powers:
        for time_value, time_name in times:
            sht.heater_power = power_value
            sht.heat_time = time_value
            print("Heater: %s, Duration: %s" % (power_name, time_name))
            temp, hum = await sht.measurements_async()
            print("  Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
            await asyncio.sleep_ms(500)
    sht.heater_power = sht45.HEATER20mW
    sht.heat_time = sht45.TEMP_0_1
    sht.temperature_precision = sht45.HIGH_PRECISION
    print("Heater settings restored to default")


def test_invalid_params(sht):
    print("\n=== Testing Invalid Parameter Handling ===")
    for attribute in ("temperature_precision", "heater_power", "heat_time"):
        try:
            setattr(sht, attribute, 99)
            print("ERROR: Should have raised ValueError")
        except ValueError as exc:
            print("ValueError caught (%s): %s" % (attribute, exc))
    print("Invalid parameter tests passed")


async def main():
    sht = None
    i2c = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: SHT45 Temperature and Humidity Sensor Test")
        print("Author: %s" % sht45.__author__)
        print("Version: %s" % sht45.__version__)
        print("\nInitializing I2C (SCL=Pin(%d), SDA=Pin(%d))..." % (I2C_SCL_PIN, I2C_SDA_PIN))
        i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        print("Scanning I2C bus...")
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus")
        print("Found %d device(s): %s" % (len(devices), [hex(device) for device in devices]))
        sht_addr = SHT45Async.DEFAULT_ADDR
        if sht_addr not in devices:
            raise RuntimeError("Device not found at expected address 0x%02X" % sht_addr)
        print("SHT45 found at address 0x%02X" % sht_addr)
        sht = SHT45Async(i2c, address=sht_addr)
        print("SHT45 instance created")
        temp, hum = await sht.measurements_async()
        print("Initial reading: Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
        print("Sensor communication verified")
        print("\nInitial Configuration:")
        print("  Temperature Precision: %s" % sht.temperature_precision)
        print("  Heater Power: %s" % sht.heater_power)
        print("  Heat Time: %s" % sht.heat_time)
        print("\n--- Starting periodic measurements ---")
        print("(Interval: %d ms, I2C addr: 0x%02X)" % (_PRINT_INTERVAL_MS, sht_addr))
        print("Async application may call test_all_precision_modes(), test_all_heater_settings(), test_invalid_params(), or await sht.reset_async().")
        last_print_time = 0
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= _PRINT_INTERVAL_MS:
                temp, hum = await sht.measurements_async()
                print("[%d] Temperature: %.2f C, Humidity: %.2f %%RH" % (current_time // 1000, temp, hum))
                last_print_time = current_time
            await asyncio.sleep_ms(100)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except OSError as exc:
        print("Hardware communication error: %s" % exc)
    except Exception as exc:
        print("Unknown error: %s" % exc)
    finally:
        print("Cleaning up resources...")
        if sht is not None:
            await sht.aclose()
        print("Program exited")


asyncio.run(main())