"""Cooperative MQ-series ADC driver with an IRQ-to-task handoff."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================
_BUILTIN_POLYS = {'MQ2': (0.0, 100.0, -20.0), 'MQ4': (0.0, 200.0, -40.0), 'MQ7': (0.0, 50.0, -8.0)}

# ======================================== 功能函数 ============================================
def _evaluate(coefficients, value):
    result = 0.0
    power = 1.0
    for coefficient in coefficients:
        result += coefficient * power
        power *= value
    return result

# ======================================== 自定义类 ============================================
class MQXAsync:
    """Cooperative MQ ADC driver; the Pin IRQ only records pending work."""

    def __init__(self, adc, comp_pin=None, callback=None, rl_ohm=10000, vref=3.3, poll_ms=20, irq_trigger=None):
        if not hasattr(adc, 'read_u16') and not hasattr(adc, 'read'):
            raise ValueError('adc must provide read_u16() or read()')
        if comp_pin is not None and not hasattr(comp_pin, 'irq'):
            raise ValueError('comp_pin must provide irq()')
        self._adc = adc
        self._comp_pin = comp_pin
        self._callback = callback
        self._poll_ms = poll_ms
        self._irq_trigger = irq_trigger
        self._irq_pending = False
        self._running = False
        self._worker = None
        self._selected_builtin = None
        self._custom_poly = None
        self.rl_ohm = rl_ohm
        self.vref = vref
        self.last_raw = 0
        self.last_voltage = 0.0

    def _irq_handler(self, pin):
        self._irq_pending = True

    def select_builtin(self, name):
        if name not in _BUILTIN_POLYS:
            raise ValueError('unknown MQ sensor: %s' % name)
        self._selected_builtin = name
        self._custom_poly = None

    async def start(self):
        if self._running:
            return
        self._running = True
        if self._comp_pin is not None:
            if self._irq_trigger is None:
                self._comp_pin.irq(handler=self._irq_handler)
            else:
                self._comp_pin.irq(trigger=self._irq_trigger, handler=self._irq_handler)
        self._worker = asyncio.create_task(self._irq_worker())

    async def aclose(self):
        self._running = False
        if self._comp_pin is not None:
            self._comp_pin.irq(handler=None)
        task = self._worker
        if task is not None:
            task.cancel()
            try:
                await task
            except BaseException:
                pass
            self._worker = None

    async def read_voltage_async(self):
        raw = self._adc.read_u16() if hasattr(self._adc, 'read_u16') else self._adc.read()
        self.last_raw = int(raw)
        self.last_voltage = self.last_raw / 65535.0 * self.vref
        await asyncio.sleep_ms(0)
        return self.last_voltage

    async def read_ppm_async(self, samples=1, delay_ms=0, sensor=None):
        if not isinstance(samples, int) or samples < 1 or not isinstance(delay_ms, int) or delay_ms < 0:
            raise ValueError('samples and delay_ms must be non-negative')
        old_builtin, old_custom = self._selected_builtin, self._custom_poly
        if sensor is not None:
            self.select_builtin(sensor)
        coefficients = self._custom_poly or (_BUILTIN_POLYS.get(self._selected_builtin) if self._selected_builtin else None)
        if coefficients is None:
            self._selected_builtin, self._custom_poly = old_builtin, old_custom
            raise RuntimeError('no polynomial coefficients selected')
        total = 0.0
        for index in range(samples):
            total += _evaluate(coefficients, await self.read_voltage_async())
            if index + 1 < samples:
                await asyncio.sleep_ms(delay_ms)
        self._selected_builtin, self._custom_poly = old_builtin, old_custom
        return total / samples

    async def _irq_worker(self):
        while self._running:
            if self._irq_pending:
                self._irq_pending = False
                voltage = await self.read_voltage_async()
                if self._callback is not None:
                    self._callback(voltage)
            await asyncio.sleep_ms(self._poll_ms)

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================