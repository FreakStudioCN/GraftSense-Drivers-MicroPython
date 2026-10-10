"""R60AFD1 asynchronous radar demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin
from data_flow_processor import DataFlowProcessor
from hc08 import HC08
from r60afd1 import format_time
from r60afd1_async import R60AFD1Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================

async def source_demo_api_mapping(device, hc0):
    """Run the source demonstration queries through their async API mappings."""
    await device.query_body_motion_param_async()
    await device.query_energy_report_switch_async()
    await device.query_fall_break_height_async()
    await device.query_fall_detection_switch_async()
    await device.query_fall_duration_async()
    await device.query_fall_sensitivity_async()
    await device.query_fall_status_async()
    await device.query_firmware_version_async()
    await device.query_hardware_model_async()
    await device.query_heartbeat_async()
    await device.query_height_accumulation_time_async()
    await device.query_height_ratio_async()
    await device.query_height_ratio_switch_async()
    await device.query_init_complete_async()
    await device.query_install_angle_async()
    await device.query_install_height_async()
    await device.query_max_energy_async()
    await device.query_motion_distance_async()
    await device.query_motion_status_async()
    await device.query_no_person_time_async()
    await device.query_presence_status_async()
    await device.query_presence_switch_async()
    await device.query_presence_threshold_async()
    await device.query_product_id_async()
    await device.query_product_model_async()
    await device.query_scene_info_async()
    await device.query_static_distance_async()
    await device.query_static_stay_duration_async()
    await device.query_static_stay_status_async()
    await device.query_static_stay_switch_async()
    await device.query_track_frequency_async()
    await device.query_track_point_async()
    await device.query_track_switch_async()
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
    device = R60AFD1Async(processor, presence_enabled=True, track_report_enabled=True, energy_report_enabled=True, height_ratio_enabled=True, fall_detection_enabled=True, static_stay_enabled=True, static_distance=50, motion_distance=100, parse_interval=20, max_retries=3, retry_delay=100, init_timeout=5000)
    try:
        await device.initialize_async()
        await device.start()
        status = await device.get_configuration_status_async()
        print("Configuration errors:", len(status["configuration_errors"]))
        await device.set_install_height_async(240)
        await device.set_fall_break_height_async(100)
        await device.set_fall_sensitivity_async(3)
        await device.set_fall_duration_async(6)
        await device.set_static_stay_duration_async(90)
        while True:
            success, presence = await device.query_presence_status_async()
            if success:
                hc0.send_data("presence_status: %s\n" % presence)
            await asyncio.sleep_ms(2000)
    finally:
        await device.aclose()

asyncio.run(main())

