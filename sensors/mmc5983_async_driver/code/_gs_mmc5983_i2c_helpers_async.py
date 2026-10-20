"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_mmc5983_micropython_mmc5983.i2c_helpers import *

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class CBitsAsync(SyncAdapterMixin, CBits):
    """Async facade; each delegated call remains a short sync transaction."""

    pass

class RegisterStructAsync(SyncAdapterMixin, RegisterStruct):
    """Async facade; each delegated call remains a short sync transaction."""

    pass

