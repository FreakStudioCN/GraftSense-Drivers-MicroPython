# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/27 上午10:44   
# @Author  : 李清水            
# @File    : main.py       
# @Description : I2C类实验。读写外部EEPROM芯片AT24C256

# ======================================== 导入相关模块 =========================================

# 时间相关的模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class AT24CXX:
    # 用于AT24CXX系列EEPROM的驱动类，支持多种容量的EEPROM

    # 类变量：定义 EEPROM 不同大小
    AT24C32 = 4096      # 4KiB
    AT24C64 = 8192      # 8KiB
    AT24C128 = 16384    # 16KiB
    AT24C256 = 32768    # 32KiB
    AT24C512 = 65536    # 64KiB

    def __init__(self, i2c, chip_size=AT24C512, addr=0x50):
        '''
        初始化AT24CXX类实例
        :param i2c        [machine.I2C]: I2C接口实例
        :param chip_size          [int]: EEPROM芯片容量
        :param addr               [int]: 芯片设备的I2C地址，默认为0x50
        '''
        # 判断EEPROM芯片容量是否在AT24CXX类定义的范围内
        if chip_size not in [AT24CXX.AT24C32, AT24CXX.AT24C64, AT24CXX.AT24C128,
                             AT24CXX.AT24C256, AT24CXX.AT24C512]:
            raise ValueError("chip_size is not in the range of AT24CXX")

        self.i2c = i2c
        self.chip_size = chip_size
        self.addr = addr
        # 用户可以操作芯片的最大地址
        self.max_address = chip_size - 1

    def write_byte(self, address, data):
        '''
        向指定地址写入一个字节
        :param address   [int]: 写入的地址
        :param data      [int]: 要写入的数据，范围0-255
        :return: None
        '''
        # 检查地址是否在有效范围内
        if address < 0 or address > self.max_address:
            raise ValueError('address is out of range')

        # 检查数据是否在有效范围内
        if data < 0 or data > 255:
            raise ValueError("data must be 0-255")

        # 从用户指定内存地址address开始，将bytes([data])写入设备地址为addr的EEPROM
        # 内存地址为16位，两个字节
        self.i2c.writeto_mem(self.addr, address, bytes([data]), addrsize=16)
        # 延时5ms，等待EEPROM写入完成
        time.sleep_ms(5)

    def read_byte(self, address):
        '''
        从指定地址读取一个字节
        :param address  [int]: 读取的地址
        :return         [int]: 读取的数据
        '''
        # 检查地址是否在有效范围内
        if address < 0 or address > self.max_address:
            raise ValueError("address is out of range")

        # 从指定地址读取一个字节
        value_read = self.i2c.readfrom_mem(self.addr, address, 1, addrsize=16)
        # 转换为整数并返回，使用大端序进行转换
        return int.from_bytes(value_read, "big")

    def write_page(self, address, data):
        '''
        向指定地址写入一页数据，处理跨页情况
        :param address    [int]: 写入的起始地址
        :param data     [bytes]: 要写入的数据，最大长度不受限制，为字节序列
        :return: None
        '''
        # 检查地址是否在有效范围内
        if address < 0 or address > self.max_address:
            raise ValueError("address is out of range")

        # 检查列表中数据是否超出范围
        for i in data:
            if i < 0 or i > 255:
                raise ValueError("data must be 0-255")

        # 结合起始地址检查data长度是否超出范围
        if address + len(data) > self.max_address:
            raise ValueError("data exceeds maximum limit")

        # 获取起始页的边界
        page_boundary = (address // 64 + 1) * 64

        # 分段写入数据
        while data:
            # 计算当前写入的字节数
            write_length = min(len(data), page_boundary - address)

            # 向指定地址写入一页数据
            self.i2c.writeto_mem(self.addr, address, data[:write_length], addrsize=16)
            # 写入后延时以确保完成
            time.sleep_ms(5)

            # 更新地址和数据
            address += write_length
            data = data[write_length:]

            # 更新页边界
            page_boundary = (address // 64 + 1) * 64

            # 如果当前地址超出最大地址，则停止写入
            if address > self.max_address:
                raise ValueError("address exceeds maximum limit")

    def read_sequence(self, start_address, length):
        '''
        顺序读取指定长度的数据
        :param start_address  [int]: 读取的起始地址
        :param length         [int]: 读取的字节数
        :return             [bytes]: 读取的数据
        '''
        # 检查起始地址和长度是否在有效范围内
        if start_address < 0 or (start_address + length) > self.max_address:
            raise ValueError("address is out of range")

        # 从指定起始地址读取指定长度的数据
        return self.i2c.readfrom_mem(self.addr, start_address, length, addrsize=16)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================