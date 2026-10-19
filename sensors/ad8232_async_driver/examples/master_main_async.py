"""Async version of the original master_code/main.py protocol example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, UART
from _gs_ad8232_master_data_flow_processor import DataFlowProcessor
from _gs_ad8232_ad8232_uart import AD8232_DataFlowProcessor


async def main():
    module_uart = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
    waveform_uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
    client = AD8232_DataFlowProcessor(DataFlowProcessor(module_uart))
    receive_task = asyncio.create_task(client.run_async())
    try:
        await client.control_ad8232_start_stop_async(True)
        await client.set_active_output_async(True)
        while True:
            lead_status = await client.query_off_detection_status_async()
            waveform_uart.write("{},{}\r\n".format(client.ecg_value, client.filtered_ecg_value))
            print("lead_status:{},heart_rate:{}".format(lead_status, client.heart_rate))
            await asyncio.sleep_ms(10)
    finally:
        client.stop()
        receive_task.cancel()
        await asyncio.sleep_ms(0)


if __name__ == "__main__":
    asyncio.run(main())
