try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, SoftI2C
from _gs_ina226_sensor_pack_2.bus_service import I2cAdapter
import _gs_ina226_ina_ti as ina_ti
from ina_ti_async import INA226Async


def show_header(info: str, width: int = 32):
    print(width * "-")
    print(info)
    print(width * "-")


async def main():
    sensor = None
    i2c_bus = None
    try:
        # Source startup stabilization wait; safely yields the event loop.
        await asyncio.sleep_ms(3000)
        print("FreakStudio: INA226 sensor initialization")
        TARGET_SENSOR_ADDRS = [0x40]
        i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
        devices_list = i2c_bus.scan()
        print("START I2C SCANNER")
        if len(devices_list) == 0:
            print("No i2c device !")
            raise SystemExit("I2C scan found no devices, program exited")
        print("i2c devices found:", len(devices_list))
        for device in devices_list:
            if device in TARGET_SENSOR_ADDRS:
                print("I2c hexadecimal address:", hex(device))
                try:
                    adaptor = I2cAdapter(i2c_bus)
                    sensor = INA226Async(
                        adapter=adaptor,
                        address=device,
                        shunt_resistance=0.01,
                    )
                    sensor.shunt_voltage_enabled = True
                    sensor.max_expected_current = 2.0
                    print("Sensor initialization successful")
                    break
                except Exception as error:
                    print("Sensor Initialization failed: {}".format(error))
                    continue
        else:
            raise Exception("No target sensor device found in I2C bus")

        cycles_count = 10
        show_header("INA226. Manual mode with settings")
        sensor.start_measurement(continuous=False, enable_calibration=True)
        print("configuration: {}".format(sensor.get_config()))
        wait_time_us = sensor.get_conversion_cycle_time()
        print("wait_time_us: {} us.".format(wait_time_us))
        for _ in range(cycles_count):
            await asyncio.sleep_ms(100)
            ds = await sensor.wait_for_conversion_async(wait_time_us)
            if not ds.conv_ready_flag:
                print("data status: {}".format(ds))
                continue
            shunt_v = sensor.get_shunt_voltage()
            bus_v = sensor.get_voltage()
            curr = sensor.get_current()
            pwr = sensor.get_power()
            print(
                "Shunt: {} V;\tBus: {}\tCurrent: {}\tpower: {}".format(
                    shunt_v,
                    bus_v,
                    curr,
                    pwr,
                )
            )
            sensor.start_measurement(continuous=False, enable_calibration=False)

        show_header("INA226. Automatic continuous mode")
        sensor.start_measurement(continuous=True, enable_calibration=True)
        print("configuration: {}".format(sensor.get_config()))
        while True:
            data = await sensor.read_measurement_async(wait_time_us)
            print(
                "data: {}, current: {}, pwr: {}".format(
                    data,
                    sensor.get_current(),
                    sensor.get_power(),
                )
            )
            await asyncio.sleep_ms(500)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, "deinit", None)
            if deinit is not None:
                deinit()


if __name__ == "__main__":
    asyncio.run(main())
