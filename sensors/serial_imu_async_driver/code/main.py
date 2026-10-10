# ======================================== 导入相关模块 =========================================
from machine import UART, Pin
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import gc
from imu_async import IMUAsync

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
async def main() -> None:
    await asyncio.sleep_ms(3000)
    print("FreakStudio : Using UART to communicate with IMU")
    uart = UART(1, 115200)
    uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)
    uart_pc = UART(0, 115200)
    uart_pc.init(bits=8, parity=None, stop=1, tx=0, rx=1, timeout=5)
    led = Pin(25, Pin.OUT, Pin.PULL_DOWN)
    imu_obj = IMUAsync(uart)
    try:
        await imu_obj.start()
        while True:
            led.on()
            await imu_obj.RecvData_async(timeout_ms=1000)
            led.off()
            print(" X-axis angle : ", imu_obj.angle_x)
            print(" Y-axis angle : ", imu_obj.angle_y)
            print(" Z-axis angle : ", imu_obj.angle_z)
            print(" the number of RAM remaining is %d bytes " % gc.mem_free())
            uart_pc.write("{:.2f}, {:.2f}, {:.2f}\r\n".format(imu_obj.angle_x, imu_obj.angle_y, imu_obj.angle_z))
            if gc.mem_free() < 220000:
                gc.collect()
            await asyncio.sleep_ms(0)
    finally:
        led.off()
        await imu_obj.aclose()
        print("The LED is off, and the program has exited.")

asyncio.run(main())
