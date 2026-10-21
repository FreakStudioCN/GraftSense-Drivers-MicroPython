"""Explicit asynchronous OPT3001 API over bounded bus transactions."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_opt3001_opt3001mod import OPT3001


class OPT3001Async(OPT3001):
    """Source-compatible operations with explicit asynchronous entry points."""

    async def _yield_bus(self):
        await asyncio.sleep_ms(0)

    async def get_cfg_reg_async(self):
        value = self.get_cfg_reg()
        await self._yield_bus()
        return value

    async def set_cfg_reg_async(self, value):
        result = self.set_cfg_reg(value)
        await self._yield_bus()
        return result

    async def get_config_hr_async(self):
        return self.get_config_hr()

    async def read_config_from_sensor_async(self, return_value=False):
        result = self.read_config_from_sensor(return_value)
        await self._yield_bus()
        return result

    async def write_config_to_sensor_async(self):
        result = self.write_config_to_sensor()
        await self._yield_bus()
        return result

    async def get_id_async(self):
        result = self.get_id()
        await self._yield_bus()
        return result

    async def get_conversion_cycle_time_async(self):
        return self.get_conversion_cycle_time()

    async def start_measurement_async(self, continuously=True, lx_range_index=12,
                                      refresh=False):
        result = self.start_measurement(continuously, lx_range_index, refresh)
        await self._yield_bus()
        return result

    async def get_measurement_value_async(self, value_index=0):
        result = self.get_measurement_value(value_index)
        await self._yield_bus()
        return result

    async def get_data_status_async(self):
        result = self.get_data_status()
        await self._yield_bus()
        return result

    async def is_single_shot_mode_async(self):
        return self.is_single_shot_mode()

    async def is_continuously_mode_async(self):
        return self.is_continuously_mode()

    async def get_lux_range_index_async(self):
        return self.lux_range_index

    async def set_lux_range_index_async(self, value):
        self.lux_range_index = value
        return None

    async def get_long_conversion_time_async(self):
        return self.long_conversion_time

    async def set_long_conversion_time_async(self, value):
        self.long_conversion_time = value
        return None

    async def get_mode_async(self):
        return self.mode

    async def set_mode_async(self, value):
        self.mode = value
        return None

    async def get_overflow_async(self):
        return self.overflow

    async def get_conversion_ready_async(self):
        return self.conversion_ready

    async def get_flag_high_async(self):
        return self.flag_high

    async def get_flag_low_async(self):
        return self.flag_low

    async def get_latch_async(self):
        return self.latch

    async def set_latch_async(self, value):
        self.latch = value
        return None

    async def get_polarity_async(self):
        return self.polarity

    async def set_polarity_async(self, value):
        self.polarity = value
        return None

    async def get_mask_exponent_async(self):
        return self.mask_exponent

    async def set_mask_exponent_async(self, value):
        self.mask_exponent = value
        return None

    async def get_fault_count_async(self):
        return self.fault_count

    async def set_fault_count_async(self, value):
        self.fault_count = value
        return None

    async def deinit_async(self):
        result = self.deinit()
        await self._yield_bus()
        return result

    async def aclose(self):
        await self.deinit_async()