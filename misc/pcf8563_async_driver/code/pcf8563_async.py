"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from pcf8563 import *

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class PCF8563Async(SyncAdapterMixin, PCF8563):
    """Async facade; each delegated call remains a short sync transaction."""

    async def seconds_async(self):
        return super().seconds()

    async def minutes_async(self):
        return super().minutes()

    async def hours_async(self):
        return super().hours()

    async def day_async(self):
        return super().day()

    async def date_async(self):
        return super().date()

    async def month_async(self):
        return super().month()

    async def year_async(self):
        return super().year()

    async def datetime_async(self):
        return super().datetime()

    async def write_all_async(self, seconds: int | None=None, minutes: int | None=None, hours: int | None=None, day: int | None=None, date: int | None=None, month: int | None=None, year: int | None=None):
        return super().write_all(seconds, minutes, hours, day, date, month, year)

    async def set_datetime_async(self, dt: tuple):
        return super().set_datetime(dt)

    async def write_now_async(self):
        return super().write_now()

    async def set_clk_out_frequency_async(self, frequency: int=CLOCK_CLK_OUT_FREQ_1_HZ):
        return super().set_clk_out_frequency(frequency)

    async def check_if_alarm_on_async(self):
        return super().check_if_alarm_on()

    async def turn_alarm_off_async(self):
        return super().turn_alarm_off()

    async def clear_alarm_async(self):
        return super().clear_alarm()

    async def check_for_alarm_interrupt_async(self):
        return super().check_for_alarm_interrupt()

    async def enable_alarm_interrupt_async(self):
        return super().enable_alarm_interrupt()

    async def disable_alarm_interrupt_async(self):
        return super().disable_alarm_interrupt()

    async def set_daily_alarm_async(self, hours: int | None=None, minutes: int | None=None, date: int | None=None, weekday: int | None=None):
        return super().set_daily_alarm(hours, minutes, date, weekday)
