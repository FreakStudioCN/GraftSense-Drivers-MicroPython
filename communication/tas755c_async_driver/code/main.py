"""Cooperative TAS755C Ethernet-module demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, UART
from tas_755c_eth_async_v3 import TAS_755C_ETHAsyncV3 as TAS_755C_ETH

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 16
UART_RX_PIN = 17
RUN_PROVISIONING = False

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Query configured network parameters using the UART async adapter."""
    await asyncio.sleep_ms(3000)
    device = TAS_755C_ETH(UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN)))
    try:
        print(await device.enter_command_mode_async())
        print(await device.get_ip_config_async())
        print(await device.get_tcp_config_async())
        if RUN_PROVISIONING:
            await device.set_ip_config_async(0, "192.168.2.251", "192.168.2.1", "255.255.255.0", "223.5.5.5")
            await device.set_tcp_config_async(8080, 9000, 0, '"www.cnblogs.com"')
            await device.set_http_config_async(1, 0, 1)
            await device.save_async()
            await device.restart_async()
            await device.enter_command_mode_async()
            await device.send_data_async(b"http.request.test")
            if await device.has_data_async():
                print(await device.read_data_async())
        print(await device.enter_data_mode_async())
    finally:
        await device.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())