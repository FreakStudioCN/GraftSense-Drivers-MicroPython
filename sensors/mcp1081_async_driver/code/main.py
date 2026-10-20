try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from mcp1081_mer_async import MERAsync
from mcp1081_modbus_rtu_async import ModbusRTUMasterAsync

async def main():
    host = sensor = None
    try:
        await asyncio.sleep_ms(3000)
        host = ModbusRTUMasterAsync(pins=(16, 17), baudrate=9600, data_bits=8, stop_bits=1, parity=None, uart_id=0)
        sensor = MERAsync(host, slave_addr=1)
        print(await sensor.read_node_address_async(), await sensor.read_hw_version_async(), await sensor.read_fw_version_async(), await sensor.read_device_uid_async())
        print(await sensor.read_filter_count_async(), await sensor.read_fit_mode_async(), await sensor.read_alarm_levels_async(), await sensor.read_full_level_async())
        while True:
            print(await sensor.read_measurements_async())
            await asyncio.sleep_ms(1000)
    finally:
        if sensor is not None: sensor.deinit()
        if host is not None: await host.aclose()
if __name__ == '__main__': asyncio.run(main())