"""R60AMP1 asynchronous radar demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin
from _gs_r60amp1_data_flow_processor import DataFlowProcessor
from _gs_r60amp1_hc08 import HC08
from r60amp1 import format_time
from r60amp1_async import R60AMP1Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================

async def source_demo_api_mapping(device, hc0):
    """Run the source demonstration queries through their async API mappings."""
    await device.query_body_motion_param_async()
    await device.query_firmware_version_async()
    await device.query_hardware_model_async()
    await device.query_heartbeat_async()
    await device.query_human_presence_switch_async()
    await device.query_init_complete_async()
    await device.query_motion_info_async()
    await device.query_presence_status_async()
    await device.query_product_id_async()
    await device.query_product_model_async()
    await device.query_trajectory_info_async()
    hc0.send_data("source demo mapping\n")
    format_time()

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)
    uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9), timeout=0)
    processor = DataFlowProcessor(uart)
    hc0 = HC08(uart1)
    device = R60AMP1Async(processor, parse_interval=20, presence_enabled=True, max_retries=3, retry_delay=100, init_timeout=5000)
    try:
        await device.initialize_async()
        await device.start()
        status = await device.get_configuration_status_async()
        print("Configuration errors:", len(status["configuration_errors"]))
        while True:
            success, presence = await device.query_presence_status_async()
            if success:
                hc0.send_data("presence_status: %s\n" % presence)
            await asyncio.sleep_ms(2000)
    finally:
        await device.aclose()

asyncio.run(main())

