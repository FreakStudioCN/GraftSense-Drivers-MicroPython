"""Cooperative MWFD water-flow/bubble detector adapter."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from mwfd import MWFD

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class MWFDAsync(MWFD):
    """The hard IRQ only sets a flag; reading and callbacks run in task context."""

    async def irq_async(self, callback=None, trigger=None):
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")
        if trigger is None:
            self.irq(callback=callback)
        else:
            self.irq(callback=callback, trigger=trigger)

    async def read_async(self):
        return self.read()

    async def consume_irq_state_async(self):
        if not self._irq_pending:
            return None
        self._irq_pending = False
        state = self.read()
        if self._callback is not None:
            self._callback(state)
        return state

    async def aclose(self):
        self.irq(callback=None)

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================