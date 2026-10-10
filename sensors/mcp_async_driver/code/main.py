import uasyncio as asyncio
from mer_async import MERAsync as MER


async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        sensor = MER(1, 0, 16, 17)
        print(await sensor.read_node_address_async(), await sensor.read_hw_version_async(), await sensor.read_fw_version_async(), await sensor.read_device_uid_async())
        print(await sensor.read_filter_count_async(), await sensor.read_low_power_enable_async(), await sensor.read_ref_level1_async(), await sensor.read_ref_level2_async(), await sensor.read_ref_level3_async())
        while True:
            print(await sensor.read_level_async(), await sensor.read_temp_async(), await sensor.read_capacitance_async(), await sensor.read_ratio_async(), await sensor.read_frequency_async())
            await asyncio.sleep_ms(1000)
    finally:
        close = getattr(sensor, 'aclose', None)
        if close is not None:
            await close()
        else:
            deinit = getattr(sensor, 'deinit', None)
            if deinit is not None:
                deinit()


if __name__ == '__main__':
    asyncio.run(main())