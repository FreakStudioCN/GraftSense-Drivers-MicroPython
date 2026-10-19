"""Async limit-switch adapter for task-context debounce consumption."""
from _gs_limit_switch_limit_switch import LimitSwitch


class LimitSwitchAsync(LimitSwitch):
    """Timer callbacks only record state; public async reads run in task context."""

    async def read_async(self):
        return LimitSwitch.read(self)

    async def set_callback_async(self, callback):
        return LimitSwitch.set_callback(self, callback)

    async def enable_async(self):
        return LimitSwitch.enable(self)

    async def disable_async(self):
        return LimitSwitch.disable(self)

    async def pending_state_async(self):
        state = getattr(self, "_pending_state", None)
        self._pending_state = None
        return state

    async def service_async(self):
        state = await self.pending_state_async()
        if state is not None and self._callback is not None:
            self._callback(state)
        return state

    async def aclose(self):
        LimitSwitch.disable(self)
        self._callback = None
