"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from ds3231maxim import *

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class BusAdapterAsync(SyncAdapterMixin, BusAdapter):
    """Async facade; each delegated call remains a short sync transaction."""

    async def read_register_async(self, device_addr: int, reg_addr: int, bytes_count: int):
        return super().read_register(device_addr, reg_addr, bytes_count)

    async def write_register_async(self, device_addr: int, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str):
        return super().write_register(device_addr, reg_addr, value, bytes_count, byte_order)

    async def read_async(self, device_addr: int, n_bytes: int):
        return super().read(device_addr, n_bytes)

    async def write_async(self, device_addr: int, buf: bytes):
        return super().write(device_addr, buf)

class I2cAdapterAsync(SyncAdapterMixin, I2cAdapter):
    """Async facade; each delegated call remains a short sync transaction."""

    async def write_register_async(self, device_addr: int, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str):
        return super().write_register(device_addr, reg_addr, value, bytes_count, byte_order)

    async def read_register_async(self, device_addr: int, reg_addr: int, bytes_count: int):
        return super().read_register(device_addr, reg_addr, bytes_count)

    async def read_async(self, device_addr: int, n_bytes: int):
        return super().read(device_addr, n_bytes)

    async def read_buf_from_mem_async(self, device_addr: int, mem_addr: int, buf: bytearray):
        return super().read_buf_from_mem(device_addr, mem_addr, buf)

    async def write_async(self, device_addr: int, buf: bytes):
        return super().write(device_addr, buf)

    async def write_buf_to_mem_async(self, device_addr: int, mem_addr: int, buf: bytes):
        return super().write_buf_to_mem(device_addr, mem_addr, buf)

class DeviceAsync(SyncAdapterMixin, Device):
    """Async facade; each delegated call remains a short sync transaction."""

    async def unpack_async(self, fmt_char: str, source: bytes):
        return super().unpack(fmt_char, source)

    async def is_big_byteorder_async(self):
        return super().is_big_byteorder()

class BaseSensorAsync(SyncAdapterMixin, BaseSensor):
    """Async facade; each delegated call remains a short sync transaction."""

    async def get_id_async(self):
        return super().get_id()

    async def soft_reset_async(self):
        return super().soft_reset()

class IteratorAsync(SyncAdapterMixin, Iterator):
    """Async facade; each delegated call remains a short sync transaction."""

    pass

class DS3231Async(SyncAdapterMixin, DS3231):
    """Async facade; each delegated call remains a short sync transaction."""

    async def get_status_async(self):
        return super().get_status()

    async def set_status_async(self, new_value: int):
        return super().set_status(new_value)

    async def get_alarm_flags_async(self, clear: bool=True):
        return super().get_alarm_flags(clear)

    async def get_control_async(self):
        return super().get_control()

    async def set_control_async(self, value: int):
        return super().set_control(value)

    async def get_temperature_async(self):
        return super().get_temperature()

    async def get_aging_offset_async(self):
        return super().get_aging_offset()

    async def get_time_async(self):
        return super().get_time()

    async def set_time_async(self, local_time: tuple[int, int, int, int, int, int, int, int]):
        return super().set_time(local_time)

    async def get_alarm_async(self, alarm_id: int=0):
        return super().get_alarm(alarm_id)

    async def set_alarm_async(self, alarm_time: tuple, match_value: int=2, alarm_id: int=0):
        return super().set_alarm(alarm_time, match_value, alarm_id)

    async def control_alarm_interrupt_async(self, irq_alarm_1_enable: bool=False, irq_alarm_0_enable: bool=False):
        return super().control_alarm_interrupt(irq_alarm_1_enable, irq_alarm_0_enable)
