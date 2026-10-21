from machine import Pin, PWM


class PowerLEDAsync:
    """Task-context facade for bounded Pin/PWM operations; construction is inert."""
    def __init__(self, pin, pwm_freq=1000):
        if not isinstance(pin, int):
            raise ValueError("Pin must be an integer")
        if pwm_freq <= 0 or pwm_freq > 1000:
            raise ValueError("PWM frequency out of range (1-1000 Hz)")
        self._pin_number = pin
        self._pwm_freq = pwm_freq
        self._pin = None
        self._pwm = None
        self._state = False

    async def initialize_async(self):
        if self._pwm is None:
            self._pin = Pin(self._pin_number, Pin.OUT)
            self._pwm = PWM(self._pin)
            self._pwm.freq(self._pwm_freq)
            self._pwm.duty_u16(0)

    def _require_initialized(self):
        if self._pwm is None:
            raise RuntimeError("call initialize_async() before operating PowerLED")

    async def on_async(self):
        self._require_initialized(); self._pwm.duty_u16(65535); self._state = True

    async def off_async(self):
        self._require_initialized(); self._pwm.duty_u16(0); self._state = False

    async def toggle_async(self):
        if self._state:
            await self.off_async()
        else:
            await self.on_async()

    async def set_brightness_async(self, duty):
        self._require_initialized()
        if duty < 0 or duty > 1023:
            raise ValueError("Duty must be 0-1023")
        self._pwm.duty_u16(int(duty * 65535 / 1023))
        self._state = duty > 0

    async def get_state_async(self):
        return self._state

    async def digital_async(self):
        self._require_initialized(); return self._pin

    async def pwm_async(self):
        self._require_initialized(); return self._pwm

    async def aclose(self):
        if self._pwm is not None:
            self._pwm.duty_u16(0)
            self._pwm.deinit()
            self._pwm = None
            self._state = False
