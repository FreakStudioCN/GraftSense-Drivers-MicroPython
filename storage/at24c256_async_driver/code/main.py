try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from at24c256_async import AT24CXXAsync


async def erase_data_async(at24cxx, start_address, length):
    await at24cxx.write_page_async(start_address, bytes([0xFF] * length))


async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2024/9/27 上午10:44
    # @Author  : 李清水
    # @File    : main.py
    # @Description : I2C类实验。读写外部EEPROM芯片AT24C256

    # ======================================== 导入相关模块 =========================================

    # 时间相关的模块

    # ======================================== 全局变量 ============================================

    # AT24C256芯片地址为0x50，即0b1010000
    # 高7位为地址位，低1位为读写控制位，0为写，1为读
    AT24C256_ADDRESS = 0x50

    # 定义要写入的字节数
    DATA_SIZE = 128
    # 生成0到127的字节序列
    data_to_write = bytes(range(DATA_SIZE))

    # ======================================== 功能函数 ============================================


    # ======================================== 初始化配置 ==========================================

    # 上电延时3s
    await asyncio.sleep(3)
    # 打印调试消息
    print("FreakStudio: Read and Write AT24C256")

    # 创建硬件I2C的实例，使用I2C0外设，时钟频率为100KHz，SDA引脚为4，SCL引脚为5
    i2c_at24c256 = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=100000)

    # 创建AT24C256的实例
    at24c256 = AT24CXXAsync(i2c_at24c256, AT24CXXAsync.AT24C256, AT24C256_ADDRESS)

    # ========================================  主程序  ===========================================

    # 验证读取的单字节和128个字节是否完成了掉电存储
    try:
        retained = await at24c256.read_byte_async(0)
        stored = await at24c256.read_sequence_async(1, DATA_SIZE)
        if retained == 0xAB and list(stored) == list(data_to_write):
            print("Data verification successful. Data retained after power cycle.")
            await erase_data_async(at24c256, 0, DATA_SIZE + 1)
        else:
            print("Erase the data of the first three pages")
            await erase_data_async(at24c256, 0, DATA_SIZE + 1)
            print("Writing single byte...")
            await at24c256.write_byte_async(0x00, 0xAB)
            print(f"Read single byte: {await at24c256.read_byte_async(0x00):#04x}")
            print("Writing 128 bytes...")
            await at24c256.write_page_async(0x01, data_to_write)
            print(f"Read 128 bytes: {list(await at24c256.read_sequence_async(0x01, DATA_SIZE))}")
    finally:
        await at24c256.aclose()
        i2c_at24c256.deinit()

if __name__ == '__main__':
    asyncio.run(main())
