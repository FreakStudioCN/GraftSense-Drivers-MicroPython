"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from bus_dc_motor import BusDCMotor

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class BusDCMotorAsync(SyncAdapterMixin, BusDCMotor):
    """Async facade; each delegated call remains a short sync transaction."""

    async def set_motor_speed_async(self, motor, speed):
        return super().set_motor_speed(motor, speed)

    async def stop_motor_async(self, motor):
        return super().stop_motor(motor)

    async def break_motor_async(self, motor):
        return super().break_motor(motor)
