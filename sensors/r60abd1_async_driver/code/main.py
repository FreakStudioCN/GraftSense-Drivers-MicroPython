"""R60ABD1 asynchronous UART radar demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from data_flow_processor_async import DataFlowProcessorAsync, R60ABD1Async
from r60abd1 import format_time

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 115200
UART_TX_PIN = 16
UART_RX_PIN = 17
QUERY_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================
async def run_source_demo(device):
    """Execute the source example's command coverage using async transactions."""
    await device.enable_abnormal_struggle_monitor_async()
    await device.enable_no_person_timing_async()
    await device.enable_sleep_monitor_async()
    await device.query_abnormal_struggle_switch_async()
    await device.query_awake_duration_async()
    await device.query_bed_status_async()
    await device.query_breath_info_async()
    await device.query_breath_monitor_switch_async()
    await device.query_breath_value_async()
    await device.query_breath_waveform_async()
    await device.query_breath_waveform_report_switch_async()
    await device.query_deep_sleep_duration_async()
    await device.query_firmware_version_async()
    await device.query_hardware_model_async()
    await device.query_heart_rate_monitor_switch_async()
    await device.query_heart_rate_value_async()
    await device.query_heart_rate_waveform_async()
    await device.query_heart_rate_waveform_report_switch_async()
    await device.query_heartbeat_async()
    await device.query_human_body_motion_param_async()
    await device.query_human_direction_async()
    await device.query_human_distance_async()
    await device.query_human_motion_info_async()
    await device.query_human_presence_switch_async()
    await device.query_init_complete_async()
    await device.query_light_sleep_duration_async()
    await device.query_low_breath_threshold_async()
    await device.query_no_person_timing_duration_async()
    await device.query_no_person_timing_status_async()
    await device.query_no_person_timing_switch_async()
    await device.query_product_id_async()
    await device.query_product_model_async()
    await device.query_radar_range_boundary_async()
    await device.query_sleep_anomaly_async()
    await device.query_sleep_comprehensive_status_async()
    await device.query_sleep_end_duration_async()
    await device.query_sleep_monitor_switch_async()
    await device.query_sleep_quality_level_async()
    await device.query_sleep_quality_score_async()
    await device.query_sleep_statistics_async()
    await device.query_sleep_status_async()
    await device.query_struggle_sensitivity_async()
    await device.set_low_breath_threshold_async(10)
    await device.set_no_person_timing_duration_async(30)
    await device.set_sleep_end_duration_async(120)
    await device.set_struggle_sensitivity_async(1)

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    device = None
    try:
        uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN), timeout=0)
        processor = DataFlowProcessorAsync(uart)
        device = R60ABD1Async(processor, parse_interval=20)
        await device.initialize_async()
        await device.start()
        await run_source_demo(device)
        while True:
            success, presence = await device.query_presence_status_async()
            if success:
                print('%s Presence: %s' % (format_time(), 'Someone' if presence == 1 else 'No one'))
            await asyncio.sleep_ms(QUERY_INTERVAL_MS)
    except KeyboardInterrupt:
        print('%s Program interrupted by user' % format_time())
    finally:
        if device is not None:
            await device.aclose()
        print('%s R60ABD1 resources released' % format_time())

asyncio.run(main())