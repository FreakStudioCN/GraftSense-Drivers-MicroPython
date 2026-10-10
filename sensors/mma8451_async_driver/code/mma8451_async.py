"""Async adapter for the MMA8451 source driver."""

from micropython_mma8451.mma8451 import MMA8451


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MMA8451Async(MMA8451):
    """Expose short source-driver I2C property reads through explicit APIs."""

    async def acceleration_async(self):
        return self.acceleration

    async def data_rate_async(self, value=None):
        if value is not None:
            self.data_rate = value
        return self.data_rate

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()


# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================