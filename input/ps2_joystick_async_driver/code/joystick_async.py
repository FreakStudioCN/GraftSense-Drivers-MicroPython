"""Cooperative PS2 joystick sampler with injected hardware objects."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


class JoystickAsync:
    conversion_factor = 3.3 / 65535

    def __init__(self, vrx_pin, vry_pin, vsw_pin=None, freq=100, callback=None):
        if not hasattr(vrx_pin, "read_u16") or not hasattr(vry_pin, "read_u16"):
            raise TypeError("vrx_pin and vry_pin must be injected ADC objects")
        if vsw_pin is not None and not hasattr(vsw_pin, "value"):
            raise TypeError("vsw_pin must be an injected Pin object or None")
        if not isinstance(freq, int) or freq <= 0:
            raise ValueError("freq must be a positive integer")
        self.adc_x, self.adc_y, self.sw = vrx_pin, vry_pin, vsw_pin
        self.freq, self.callback = freq, callback
        self.x_value = self.y_value = 0
        self.sw_value = 1
        self.filter_alpha, self.filtered_x, self.filtered_y = 0.2, 1.55, 1.55
        self._task, self._running = None, False

    def _sample(self):
        raw_x = self.adc_x.read_u16() * self.conversion_factor
        raw_y = self.adc_y.read_u16() * self.conversion_factor
        self.filtered_x = self.filter_alpha * raw_x + (1 - self.filter_alpha) * self.filtered_x
        self.filtered_y = self.filter_alpha * raw_y + (1 - self.filter_alpha) * self.filtered_y
        self.x_value, self.y_value = self.filtered_x, self.filtered_y
        if self.sw is not None:
            self.sw_value = self.sw.value()

    async def _sample_loop(self):
        period_ms = max(1, 1000 // self.freq)
        while self._running:
            self._sample()
            if self.callback is not None:
                result = self.callback((self.x_value, self.y_value, self.sw_value))
                if hasattr(result, "__await__"):
                    await result
            await asyncio.sleep_ms(period_ms)

    async def start_async(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._sample_loop())

    async def stop_async(self):
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def get_values(self):
        return self.x_value, self.y_value, self.sw_value

    async def get_values_async(self):
        return self.get_values()

    async def aclose(self):
        await self.stop_async()
