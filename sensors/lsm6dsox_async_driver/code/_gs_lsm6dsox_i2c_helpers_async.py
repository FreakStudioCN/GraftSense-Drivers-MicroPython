# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : GraftSense Async Conversion
# @File    : i2c_helpers_async.py
# @Description : Asynchronous runtime helper
# @License : MIT

# ======================================== imports =============================================

"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_lsm6dsox_i2c_helpers import *

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================


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

# ======================================== init ================================================

# ======================================== main ================================================
