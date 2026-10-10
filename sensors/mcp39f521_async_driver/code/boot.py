"""MCP39F521 boot-time network setup without a busy wait."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import gc
import time
import network
import webrepl
# ======================================== 全局变量 ============================================
SSID = '<WiFi networkid>'
PASSWORD = '<WiFi pass>'
CONNECT_TIMEOUT_MS = 30000
# ======================================== 功能函数 ============================================
async def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(SSID, PASSWORD)
        started = time.ticks_ms()
        while not sta_if.isconnected():
            if time.ticks_diff(time.ticks_ms(), started) >= CONNECT_TIMEOUT_MS:
                raise RuntimeError('WiFi connection timed out')
            await asyncio.sleep_ms(100)
    print('-- Network configuration:', sta_if.ifconfig())
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
webrepl.start()
gc.collect()
# ======================================== 主程序 ================================================
asyncio.run(do_connect())