"""Legacy dynamic facades retained as non-runtime provenance text.

The implementation below exposes only explicit, source-compatible async
operations.  A register transaction remains a bounded synchronous I2C call.
"""

"""

class PortAsync(Port):
    async def call_async(self, method, *args, **kwargs):
        # Honest sync-adapter boundary: one source operation may briefly block.
        return getattr(self, method)(*args, **kwargs)

    async def mode_async(self, *args, **kwargs):
        return super().mode(*args, **kwargs)

    async def input_polarity_async(self, *args, **kwargs):
        return super().input_polarity(*args, **kwargs)

    async def interrupt_enable_async(self, *args, **kwargs):
        return super().interrupt_enable(*args, **kwargs)

    async def default_value_async(self, *args, **kwargs):
        return super().default_value(*args, **kwargs)

    async def interrupt_compare_default_async(self, *args, **kwargs):
        return super().interrupt_compare_default(*args, **kwargs)

    async def io_config_async(self, *args, **kwargs):
        return super().io_config(*args, **kwargs)

    async def pullup_async(self, *args, **kwargs):
        return super().pullup(*args, **kwargs)

    async def interrupt_flag_async(self, *args, **kwargs):
        return super().interrupt_flag(*args, **kwargs)

    async def interrupt_captured_async(self, *args, **kwargs):
        return super().interrupt_captured(*args, **kwargs)

    async def gpio_async(self, *args, **kwargs):
        return super().gpio(*args, **kwargs)

    async def output_latch_async(self, *args, **kwargs):
        return super().output_latch(*args, **kwargs)

    async def init_async(self, *args, **kwargs):
        return super().init(*args, **kwargs)

    async def config_async(self, *args, **kwargs):
        return super().config(*args, **kwargs)

    async def pin_async(self, *args, **kwargs):
        return super().pin(*args, **kwargs)

    async def interrupt_triggered_gpio_async(self, *args, **kwargs):
        return super().interrupt_triggered_gpio(*args, **kwargs)

    async def interrupt_captured_gpio_async(self, *args, **kwargs):
        return super().interrupt_captured_gpio(*args, **kwargs)

    async def value_async(self, *args, **kwargs):
        return super().value(*args, **kwargs)

    async def input_async(self, *args, **kwargs):
        return super().input(*args, **kwargs)

    async def output_async(self, *args, **kwargs):
        return super().output(*args, **kwargs)

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class MCP23017Async(MCP23017):
    async def call_async(self, method, *args, **kwargs):
        # Honest sync-adapter boundary: one source operation may briefly block.
        return getattr(self, method)(*args, **kwargs)

    async def mode_async(self, *args, **kwargs):
        return super().mode(*args, **kwargs)

    async def input_polarity_async(self, *args, **kwargs):
        return super().input_polarity(*args, **kwargs)

    async def interrupt_enable_async(self, *args, **kwargs):
        return super().interrupt_enable(*args, **kwargs)

    async def default_value_async(self, *args, **kwargs):
        return super().default_value(*args, **kwargs)

    async def interrupt_compare_default_async(self, *args, **kwargs):
        return super().interrupt_compare_default(*args, **kwargs)

    async def io_config_async(self, *args, **kwargs):
        return super().io_config(*args, **kwargs)

    async def pullup_async(self, *args, **kwargs):
        return super().pullup(*args, **kwargs)

    async def interrupt_flag_async(self, *args, **kwargs):
        return super().interrupt_flag(*args, **kwargs)

    async def interrupt_captured_async(self, *args, **kwargs):
        return super().interrupt_captured(*args, **kwargs)

    async def gpio_async(self, *args, **kwargs):
        return super().gpio(*args, **kwargs)

    async def output_latch_async(self, *args, **kwargs):
        return super().output_latch(*args, **kwargs)

    async def init_async(self, *args, **kwargs):
        return super().init(*args, **kwargs)

    async def config_async(self, *args, **kwargs):
        return super().config(*args, **kwargs)

    async def pin_async(self, *args, **kwargs):
        return super().pin(*args, **kwargs)

    async def interrupt_triggered_gpio_async(self, *args, **kwargs):
        return super().interrupt_triggered_gpio(*args, **kwargs)

    async def interrupt_captured_gpio_async(self, *args, **kwargs):
        return super().interrupt_captured_gpio(*args, **kwargs)

    async def value_async(self, *args, **kwargs):
        return super().value(*args, **kwargs)

    async def input_async(self, *args, **kwargs):
        return super().input(*args, **kwargs)

    async def output_async(self, *args, **kwargs):
        return super().output(*args, **kwargs)

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class VirtualPinAsync(VirtualPin):
    async def call_async(self, method, *args, **kwargs):
        # Honest sync-adapter boundary: one source operation may briefly block.
        return getattr(self, method)(*args, **kwargs)

    async def mode_async(self, *args, **kwargs):
        return super().mode(*args, **kwargs)

    async def input_polarity_async(self, *args, **kwargs):
        return super().input_polarity(*args, **kwargs)

    async def interrupt_enable_async(self, *args, **kwargs):
        return super().interrupt_enable(*args, **kwargs)

    async def default_value_async(self, *args, **kwargs):
        return super().default_value(*args, **kwargs)

    async def interrupt_compare_default_async(self, *args, **kwargs):
        return super().interrupt_compare_default(*args, **kwargs)

    async def io_config_async(self, *args, **kwargs):
        return super().io_config(*args, **kwargs)

    async def pullup_async(self, *args, **kwargs):
        return super().pullup(*args, **kwargs)

    async def interrupt_flag_async(self, *args, **kwargs):
        return super().interrupt_flag(*args, **kwargs)

    async def interrupt_captured_async(self, *args, **kwargs):
        return super().interrupt_captured(*args, **kwargs)

    async def gpio_async(self, *args, **kwargs):
        return super().gpio(*args, **kwargs)

    async def output_latch_async(self, *args, **kwargs):
        return super().output_latch(*args, **kwargs)

    async def init_async(self, *args, **kwargs):
        return super().init(*args, **kwargs)

    async def config_async(self, *args, **kwargs):
        return super().config(*args, **kwargs)

    async def pin_async(self, *args, **kwargs):
        return super().pin(*args, **kwargs)

    async def interrupt_triggered_gpio_async(self, *args, **kwargs):
        return super().interrupt_triggered_gpio(*args, **kwargs)

    async def interrupt_captured_gpio_async(self, *args, **kwargs):
        return super().interrupt_captured_gpio(*args, **kwargs)

    async def value_async(self, *args, **kwargs):
        return super().value(*args, **kwargs)

    async def input_async(self, *args, **kwargs):
        return super().input(*args, **kwargs)

    async def output_async(self, *args, **kwargs):
        return super().output(*args, **kwargs)

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

"""

from mcp23017 import MCP23017


class MCP23017Async(MCP23017):
    """Explicit async adapter for MCP23017 register transactions."""

    async def init_async(self):
        return MCP23017.init(self)

    async def config_async(self, pin, mode=None, pullup=None, polarity=None):
        return MCP23017.config(self, pin, mode, pullup, polarity)

    async def pin_async(self, pin, mode=None, pullup=None, polarity=None, value=None):
        return MCP23017.pin(self, pin, mode, pullup, polarity, value)

    async def interrupt_triggered_gpio_async(self, port):
        return MCP23017.interrupt_triggered_gpio(self, port)

    async def interrupt_captured_gpio_async(self, port):
        return MCP23017.interrupt_captured_gpio(self, port)

    async def aclose(self):
        self.i2c = None
