"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from attitude import *

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

