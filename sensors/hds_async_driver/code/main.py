try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from hds_async import HDSAsync as HDS
from hds_umodbus.serial import SerialAsync as ModbusRTUMaster

async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    modbus = ModbusRTUMaster(0, 9600, 8, 1, None, (Pin(16), Pin(17)))
    sensor = HDS(modbus, 1, 2, 50)
    try:
        print("Device: %s" % (await sensor.read_device_info_async()))
        while True:
            data = await sensor.read_basic_measurements_async()
            print("T={:.1f} C, C1={:.3f} pF, C2={:.3f} pF".format(data["temperature_c"], data["c1_pf"], data["c2_pf"]))
            await asyncio.sleep(1)
    finally:
        await sensor.aclose()
        await modbus.aclose()

asyncio.run(main())
