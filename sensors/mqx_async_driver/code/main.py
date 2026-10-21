"""MQ-series gas sensor asynchronous demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import ADC, Pin
from mqx_async import MQXAsync

# ======================================== 全局变量 ============================================
ADC_PIN = 26
COMPARATOR_PIN = 19

# ======================================== 功能函数 ============================================
def mq_callback(voltage):
    print('[IRQ] Voltage: %.3f V' % voltage)

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = MQXAsync(ADC(Pin(ADC_PIN)), Pin(COMPARATOR_PIN, Pin.IN), mq_callback, rl_ohm=10000, vref=3.3)
    sensor.select_builtin('MQ2')
    try:
        await sensor.start()
        while True:
            print('Voltage: %.3f V' % await sensor.read_voltage_async())
            print('Gas concentration: %.2f ppm' % await sensor.read_ppm_async(samples=5, delay_ms=200))
            await asyncio.sleep_ms(2000)
    finally:
        await sensor.aclose()

asyncio.run(main())