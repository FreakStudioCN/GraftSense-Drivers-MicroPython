# ======================================== 导入相关模块 =========================================
from machine import Pin, ADC
import uasyncio as asyncio
from mgx_async import MGXAsync

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
last_irq_voltage = None


def mg_irq_signal(voltage: float) -> None:
    """Receive the worker result without I/O in the IRQ callback chain."""
    global last_irq_voltage
    last_irq_voltage = voltage

# ======================================== 主程序 ==============================================
async def main() -> None:
    await asyncio.sleep_ms(3000)
    print("Measuring Gas Concentration with MG Series Gas Sensor Modules")
    mg = MGXAsync(ADC(Pin(26)), Pin(19, Pin.IN), mg_irq_signal, rl_ohm=10000, vref=3.3)
    mg.select_builtin("MG811")
    print("===== MG Sensor Test Program Started =====")
    try:
        await mg.start()
        while True:
            print("Voltage: {:.3f} V".format(await mg.read_voltage_async()))
            print("Gas concentration: {:.2f} ppm".format(await mg.read_ppm_async(samples=5, delay_ms=200)))
            print("-" * 40)
            await asyncio.sleep_ms(2000)
    finally:
        await mg.aclose()
        print("Sensor resources released.")

asyncio.run(main())
