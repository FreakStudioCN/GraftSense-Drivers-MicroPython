try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from shtc3_async import SHTC3Async, SHTC3Error

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
SENSOR_ADDR = 0x70
EXPECTED_SENSOR_ID = 0x0807
SAMPLE_INTERVAL_MS = 2000


async def main():
    sensor = None
    try:
        print("FreakStudio: starting async driver demo")
        await asyncio.sleep_ms(3000)
        i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus %d" % I2C_ID)
        print("I2C devices found: %s" % [hex(addr) for addr in devices])
        if SENSOR_ADDR not in devices:
            raise RuntimeError("SHTC3 not found at address %s" % hex(SENSOR_ADDR))
        sensor = SHTC3Async(i2c, addr=SENSOR_ADDR)
        await sensor.initialize_async()
        chip_id = await sensor.read_id_async()
        print("SHTC3 ID: %s" % hex(chip_id))
        if chip_id == EXPECTED_SENSOR_ID:
            print("Device found: SHTC3 sensor verified successfully")
        else:
            print("Device found: ID %s (expected %s), continuing anyway" % (hex(chip_id), hex(EXPECTED_SENSOR_ID)))
        while True:
            try:
                temperature, humidity = await sensor.measure_async()
                print("Temperature: %.2f C, Humidity: %.2f %%" % (temperature, humidity))
            except SHTC3Error as error:
                print("Measurement failed: %s" % error)
            await asyncio.sleep_ms(SAMPLE_INTERVAL_MS)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as error:
        print("Hardware communication error: %s" % error)
    except Exception as error:
        print("Unknown error: %s" % error)
    finally:
        print("Cleaning up resources...")
        if sensor is not None:
            await sensor.aclose()
        print("Program exited")


asyncio.run(main())
