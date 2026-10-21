# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : 缪贵成
# @File    : mgx_async.py
# @Description : MGX 协作 ADC 与 IRQ worker
# @License : MIT

# -*- coding: utf-8 -*-
# ======================================== 导入相关模块 =========================================
import uasyncio as asyncio

# ======================================== 全局变量 ============================================
_BUILTIN_POLYS = {"MG811": (0.0, 100.0, -20.0), "MG812": (0.0, 200.0, -40.0)}

# ======================================== 功能函数 ============================================
def _evaluate(coefficients: tuple, value: float) -> float:
    result = 0.0
    power = 1.0
    for coefficient in coefficients:
        result += coefficient * power
        power *= value
    return result

# ======================================== 自定义类 ============================================
class MGXAsync:
    """Cooperative MG811/MG812 ADC driver with an ISR-to-task handoff."""
    def __init__(self, adc, comp_pin=None, callback=None, rl_ohm: float = 10000,
                 vref: float = 3.3, poll_ms: int = 20, irq_trigger=None) -> None:
        if not hasattr(adc, "read_u16") and not hasattr(adc, "read"):
            raise ValueError("adc must provide read_u16() or read()")
        if comp_pin is not None and not hasattr(comp_pin, "irq"):
            raise ValueError("comp_pin must provide irq()")
        if callback is not None and not callable(callback):
            raise ValueError("callback must be callable or None")
        if rl_ohm <= 0 or vref <= 0 or not isinstance(poll_ms, int) or poll_ms < 1:
            raise ValueError("rl_ohm, vref and poll_ms must be positive")
        self._adc = adc
        self._comp_pin = comp_pin
        self._callback = callback
        self.rl = float(rl_ohm)
        self.vref = float(vref)
        self._poll_ms = poll_ms
        self._selected_builtin = None
        self._custom_poly = None
        self.last_raw = None
        self.last_voltage = None
        self._irq_pending = False
        self._running = False
        self._worker_task = None
        if comp_pin is not None:
            if irq_trigger is None:
                irq_trigger = getattr(comp_pin, "IRQ_RISING", 1) | getattr(comp_pin, "IRQ_FALLING", 2)
            comp_pin.irq(handler=self._irq, trigger=irq_trigger)

    def _irq(self, _pin) -> None:
        self._irq_pending = True

    async def start(self) -> None:
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._irq_worker())

    async def aclose(self) -> None:
        self._running = False
        if self._worker_task is not None:
            self._worker_task.cancel()
            self._worker_task = None
        if self._comp_pin is not None:
            self._comp_pin.irq(handler=None)
        await asyncio.sleep_ms(0)

    def select_builtin(self, name: str) -> None:
        key = str(name).upper()
        if key not in _BUILTIN_POLYS:
            raise ValueError("unknown builtin key: " + str(name))
        self._selected_builtin = key
        self._custom_poly = None

    def set_custom_polynomial(self, coefficients: tuple) -> None:
        if not hasattr(coefficients, "__iter__"):
            raise ValueError("coefficients must be iterable")
        self._custom_poly = tuple(coefficients)
        self._selected_builtin = None

    async def read_voltage_async(self) -> float:
        if hasattr(self._adc, "read_u16"):
            raw = self._adc.read_u16()
        else:
            raw = self._adc.read()
        self.last_raw = int(raw)
        self.last_voltage = self.last_raw / 65535.0 * self.vref
        await asyncio.sleep_ms(0)
        return self.last_voltage

    async def read_ppm_async(self, samples: int = 1, delay_ms: int = 0, sensor=None) -> float:
        if not isinstance(samples, int) or samples < 1 or not isinstance(delay_ms, int) or delay_ms < 0:
            raise ValueError("samples must be >= 1 and delay_ms must be >= 0")
        previous_builtin, previous_custom = self._selected_builtin, self._custom_poly
        if sensor is not None:
            self.select_builtin(sensor)
        coefficients = self._custom_poly or (_BUILTIN_POLYS.get(self._selected_builtin) if self._selected_builtin else None)
        if coefficients is None:
            self._selected_builtin, self._custom_poly = previous_builtin, previous_custom
            raise RuntimeError("unknown sensor or no polynomial coefficients")
        total = 0.0
        for index in range(samples):
            total += _evaluate(coefficients, await self.read_voltage_async())
            if index + 1 < samples and delay_ms:
                await asyncio.sleep_ms(delay_ms)
        self._selected_builtin, self._custom_poly = previous_builtin, previous_custom
        return total / samples

    async def _irq_worker(self) -> None:
        while self._running:
            if self._irq_pending:
                self._irq_pending = False
                voltage = await self.read_voltage_async()
                if self._callback is not None:
                    self._callback(voltage)
            await asyncio.sleep_ms(self._poll_ms)

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
