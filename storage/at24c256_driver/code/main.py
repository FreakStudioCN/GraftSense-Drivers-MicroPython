# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/27 上午10:44   
# @Author  : 李清水            
# @File    : main.py       
# @Description : I2C类实验。读写外部EEPROM芯片AT24C256

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import I2C, Pin
from at24c256 import AT24CXX
# 时间相关的模块
import time

# ======================================== 全局变量 ============================================

# AT24C256芯片地址为0x50，即0b1010000
# 高7位为地址位，低1位为读写控制位，0为写，1为读
AT24C256_ADDRESS = 0x50

# 定义要写入的字节数
DATA_SIZE = 128
# 生成0到127的字节序列
data_to_write = bytes(range(DATA_SIZE))

# ======================================== 功能函数 ============================================

def erase_data(at24cxx, start_address, length):
    """
    将指定区域的数据擦除为0xFF
    :param at24cxx   [AT24CXX]: AT24CXX类实例
    :param start_address [int]: 起始地址
    :param length        [int]: 写入长度
    :return: None
    """

    # 生成一个长度为length、数据均为0xFF的字节数据
    data_to_erase = bytes([0xFF] * length)
    # 将其连续写入指定区域
    at24cxx.write_page(start_address, data_to_erase)

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Read and Write AT24C256")

# 创建硬件I2C的实例，使用I2C0外设，时钟频率为100KHz，SDA引脚为4，SCL引脚为5
i2c_at24c256 = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=100000)

# 创建AT24C256的实例
at24c256 = AT24CXX(i2c_at24c256, AT24CXX.AT24C256, AT24C256_ADDRESS)

# ========================================  主程序  ===========================================

# 验证读取的单字节和128个字节是否完成了掉电存储
if at24c256.read_byte(0) == 0xAB and list(at24c256.read_sequence(1, DATA_SIZE)) == list(data_to_write):
    print("Data verification successful. Data retained after power cycle.")
    # 擦除前三个页面的数据
    erase_data(at24c256, 0, DATA_SIZE + 1)
# 判断为初次写入实验
else:
    # 擦除前三个页面的数据
    print("Erase the data of the first three pages")
    erase_data(at24c256, 0, DATA_SIZE + 1)

    # 写入单字节：写入0xAB到地址0x00
    print("Writing single byte...")
    at24c256.write_byte(0x00, 0xAB)
    print("Written single byte 0xAB at address 0x00.")

    # 读取单字节，读取地址0x00的数据
    print("Reading single byte...")
    single_byte = at24c256.read_byte(0x00)
    print(f"Read single byte: {single_byte:#04x}")

    # 写入128个字节到地址0x01
    print("Writing 128 bytes...")
    at24c256.write_page(0x01, data_to_write)
    print("Written 128 bytes starting at address 0x01.")

    # 读取128个字节，起始地址为0x01
    print("Reading 128 bytes...")
    read_data = at24c256.read_sequence(0x01, DATA_SIZE)
    print(f"Read 128 bytes: {list(read_data)}")