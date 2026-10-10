"""Explicit lifecycle adapter for finite GPIO polling operations."""
from tdeck_trackball import TDeckTrackball, DEFAULT_PIN_RIGHT, DEFAULT_PIN_UP, DEFAULT_PIN_LEFT, DEFAULT_PIN_DOWN, DEFAULT_PIN_BUTTON

class TDeckTrackballAsync(TDeckTrackball):
    def __init__(self, pin_right=DEFAULT_PIN_RIGHT, pin_up=DEFAULT_PIN_UP, pin_left=DEFAULT_PIN_LEFT, pin_down=DEFAULT_PIN_DOWN, pin_button=DEFAULT_PIN_BUTTON, step=1, pull=None, button_active_low=True, debounce_ms=0, debug=False):
        self._pending_init = (pin_right, pin_up, pin_left, pin_down, pin_button, step, pull, button_active_low, debounce_ms, debug)
        self._initialized = False
    async def initialize_async(self):
        if not self._initialized:
            args = self._pending_init
            if args[6] is None:
                TDeckTrackball.__init__(self, args[0], args[1], args[2], args[3], args[4], args[5], button_active_low=args[7], debounce_ms=args[8], debug=args[9])
            else:
                TDeckTrackball.__init__(self, *args)
            self._initialized = True
    def _ready(self):
        if not self._initialized: raise RuntimeError("call initialize_async() before use")
    async def poll_async(self): self._ready(); return self.poll()
    async def read_async(self): self._ready(); return self.read()
    async def pressed_async(self): self._ready(); return self.pressed()
    async def button_changed_async(self): self._ready(); return self.button_changed()
    async def position_async(self): self._ready(); return self.position()
    async def reset_position_async(self): self._ready(); self.reset_position()
    async def reset_state_async(self): self._ready(); self.reset_state()
    async def self_test_async(self, verbose=True): self._ready(); return self.self_test(verbose)
    async def deinit_async(self):
        if self._initialized: self.deinit(); self._initialized = False
    async def aclose(self): await self.deinit_async()
