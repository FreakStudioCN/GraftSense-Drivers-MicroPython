try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from flame_sensor_async import FlameSensorAsync


flame_event = False

def flame_detected_callback():
    global flame_event
    flame_event = True


async def main():
    global flame_event
    flame_sensor = None
    try:
        print("FreakStudio:Testing Flame Sensor")
        await asyncio.sleep_ms(3000)
        flame_sensor = FlameSensorAsync(
            analog_pin=26,
            digital_pin=19,
            callback=flame_detected_callback,
        )
        await flame_sensor.enable_async()
        print("=== Flame Sensor Initialized. Monitoring AO voltage... ===")
        while True:
            voltage = await flame_sensor.get_voltage_async()
            if flame_event:
                print("Flame detected!")
                flame_event = False
            print("AO Voltage: {:.2f} V".format(voltage))
            await asyncio.sleep_ms(1000)
    except KeyboardInterrupt:
        print("=== Test Stopped by User ===")
    finally:
        if flame_sensor is not None:
            await flame_sensor.disable_async()
            await flame_sensor.aclose()


if __name__ == "__main__":
    asyncio.run(main())
