from machine import Pin, PWM


class UVMatrixAsync:
    """Task-context facade for bounded Pin/PWM operations; construction is inert."""
    def __init__(self, pin, pwm_freq=1000):
        if not isinstance(pin, int):
            raise ValueError("Pin must be an integer")
        self._pin_number = pin
        self._pwm_freq = pwm_freq
        self._digital = None
        self._pwm = None
        self._state = False

    async def initialize_async(self):
        if self._pwm is None:
            self._digital = Pin(self._pin_number, Pin.OUT)
            self._pwm = PWM(self._digital)
            self._pwm.freq(self._pwm_freq)
            self._pwm.duty_u16(0)

    def _require_initialized(self):
        if self._pwm is None:
            raise RuntimeError("call initialize_async() before operating UVMatrix")

    async def on_async(self):
        self._require_initialized(); self._pwm.duty_u16(32766); self._state = True

    async def off_async(self):
        self._require_initialized(); self._pwm.duty_u16(0); self._state = False

    async def toggle_async(self):
        if self._state:
            await self.off_async()
        else:
            await self.on_async()

    async def set_brightness_async(self, duty):
        self._require_initialized()
        if not 0 <= duty <= 512:
            raise ValueError("PWM duty must be 0-512")
        self._pwm.duty_u16(int(duty * 65535 / 1023))

    async def get_state_async(self):
        return self._state

    async def digital_async(self):
        self._require_initialized(); return self._digital

    async def pwm_async(self):
        self._require_initialized(); return self._pwm

    async def aclose(self):
        if self._pwm is not None:
            self._pwm.duty_u16(0)
            self._pwm.deinit()
            self._pwm = None
            self._state = False
