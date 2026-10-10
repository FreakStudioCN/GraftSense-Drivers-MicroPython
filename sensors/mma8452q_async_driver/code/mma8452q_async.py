"""Async adapters for the MMA8452Q source driver.

Each adapter call performs one short, synchronous I2C property operation; it
does not claim that the underlying bus transaction is pre-emptible.
"""

from mma8452q import CBits, MMA8452Q, RegisterStruct


# ======================================== 全局变量 ============================================

_UNSET = object()


# ======================================== 功能函数 ============================================


class _PropertyAsyncAdapter:
    """Expose source-driver properties through explicit async adapter APIs."""

    async def _property_async(self, name, value=_UNSET):
        if value is not _UNSET:
            setattr(self, name, value)
        return getattr(self, name)



    async def acceleration_async(self):
        return self.acceleration

    async def operation_mode_async(self, value=_UNSET):
        return await self._property_async("operation_mode", value)

    async def scale_range_async(self, value=_UNSET):
        return await self._property_async("scale_range", value)

    async def data_rate_async(self, value=_UNSET):
        return await self._property_async("data_rate", value)

    async def high_pass_filter_async(self, value=_UNSET):
        return await self._property_async("high_pass_filter", value)

    async def high_pass_filter_cutoff_async(self, value=_UNSET):
        return await self._property_async("high_pass_filter_cutoff", value)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()


# ======================================== 自定义类 ============================================


class CBitsAsync(_PropertyAsyncAdapter, CBits):
    pass


class RegisterStructAsync(_PropertyAsyncAdapter, RegisterStruct):
    pass


class MMA8452QAsync(_PropertyAsyncAdapter, MMA8452Q):
    pass


# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================