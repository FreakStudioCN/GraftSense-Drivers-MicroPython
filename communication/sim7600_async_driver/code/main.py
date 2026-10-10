"""Cooperative SIM7600 modem demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, UART
from sim7600_async import CallingAsync, GPSAsync, HTTPAsync, LBSAsync, SMSAsync
from sim7600_async_v4 import SIM7600AsyncV4 as SIM7600

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 115200
UART_TX_PIN = 16
UART_RX_PIN = 17
RUN_SERVICE_ACTIONS = False
TEST_PHONE_NUMBER = "+8619524162376"

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Perform bounded modem queries; costly service actions remain opt-in."""
    await asyncio.sleep_ms(3000)
    modem = SIM7600(UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN)))
    try:
        calling = CallingAsync(modem)
        sms = SMSAsync(modem)
        gps = GPSAsync(modem)
        lbs = LBSAsync(modem)
        http = HTTPAsync(modem)
        print(await modem.check_sim_card_async())
        print(await modem.get_signal_quality_async())
        print(await modem.check_network_registration_async())
        print(await modem.check_network_attach_async())
        print(await modem.send_command_async("AT+CGMR"))
        # These real modem actions are opt-in because they can place calls, send SMS,
        # change network state, or consume mobile data on a provisioned device.
        if RUN_SERVICE_ACTIONS:
            await calling.make_call_async(TEST_PHONE_NUMBER)
            await calling.hang_up_async()
            await calling.answer_call_async()
            await calling.call_status_async()
            await calling.set_call_volume_async(5)
            await sms.set_sms_mode_async()
            await sms.send_sms_async(TEST_PHONE_NUMBER, "SIM7600 async example")
            await sms.list_sms_async("ALL")
            await gps.disable_gps_async()
            await gps.set_satellite_beidou_async()
            await gps.enable_gps_async()
            await gps.start_search_satellite_async()
            await gps.get_gps_info_async()
            await lbs.start_network_async()
            await lbs.get_lbs_coords_async(1)
            await lbs.get_lbs_full_async(4)
            await lbs.stop_network_async()
            await http.set_apn_async()
            await http.get_ip_async()
            await http.enable_http_async()
            await http.set_url_async("https://example.invalid")
            await http.http_data_async(0)
            await http.send_head_async(0)
            await http.get_head_async()
            await http.get_read_async()
            await http.disable_http_async()
        while True:
            await asyncio.sleep_ms(1000)
    finally:
        await modem.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())