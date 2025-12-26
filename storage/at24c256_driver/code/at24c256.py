# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/27 上午10:44   
# @Author  : 李清水            
# @File    : main.py       
# @Description : I2C类实验。读写外部EEPROM芯片AT24C256
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 时间相关的模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class AT24CXX:
    """
    AT24CXX 系列 EEPROM 存储器驱动类。
    支持多种容量的 EEPROM 芯片，提供字节读写、页写入和顺序读取功能。
    兼容 AT24C32, AT24C64, AT24C128, AT24C256, AT24C512 等芯片。

    Attributes:
    i2c: I2C 接口实例，用于与 EEPROM 通信。
    chip_size (int): EEPROM 芯片容量，单位字节。
    addr (int): 芯片的 I2C 设备地址，默认为 0x50。
    max_address (int): 用户可操作的最大地址，等于 chip_size - 1。

    Methods:
        __init__(self, i2c, chip_size=AT24C512, addr=0x50):
            初始化 AT24CXX 类实例。
        write_byte(self, address, data):
            向指定地址写入一个字节。
        read_byte(self, address):
            从指定地址读取一个字节。
        write_page(self, address, data):
            向指定地址写入一页数据，自动处理跨页情况。
        read_sequence(self, start_address, length):
            顺序读取指定长度的数据。

    Notes:
        EEPROM 写入需要一定时间（典型 5ms），写入操作后需要适当延时。
        页大小为 64 字节，跨页写入会自动分段处理。
        地址范围为 0 到 chip_size-1，超出范围会抛出 ValueError。

    ==========================================
    AT24CXX series EEPROM memory driver class.
    Supports various capacity EEPROM chips, provides byte read/write, page write and sequential read functions.
    Compatible with AT24C32, AT24C64, AT24C128, AT24C256, AT24C512 and other chips.

    Attributes:
        i2c: I2C interface instance for communicating with EEPROM.
        chip_size (int): EEPROM chip capacity in bytes.
        addr (int): Chip I2C device address, default is 0x50.
        max_address (int): Maximum address user can operate, equals chip_size - 1.

    Methods:
        __init__(self, i2c, chip_size=AT24C512, addr=0x50):
            Initialize AT24CXX class instance.
        write_byte(self, address, data):
            Write one byte to specified address.
        read_byte(self, address):
            Read one byte from specified address.
        write_page(self, address, data):
            Write one page of data to specified address, automatically handles cross-page situations.
        read_sequence(self, start_address, length):
            Sequentially read data of specified length.

    Notes:
        EEPROM writing requires certain time (typically 5ms), need appropriate delay after write operations.
        Page size is 64 bytes, cross-page writing will be automatically segmented.
        Address range is 0 to chip_size-1, exceeding range will raise ValueError.
    """
    # 类常量：定义 EEPROM 不同容量
    # 4KiB
    AT24C32 = 4096
    # 8KiB
    AT24C64 = 8192
    # 16KiB
    AT24C128 = 16384
    # 32KiB
    AT24C256 = 32768
    # 64KiB
    AT24C512 = 65536
    def __init__(self, i2c, chip_size=AT24C512, addr=0x50):
        """
        初始化 AT24CXX 类实例。

        Args:
            i2c (machine.I2C): I2C 接口实例。
            chip_size (int, optional): EEPROM 芯片容量，默认为 AT24C512。
            addr (int, optional): 芯片设备的 I2C 地址，默认为 0x50。

        Raises:
            ValueError: 如果芯片容量不在支持范围内。

        ==========================================

        Initialize AT24CXX class instance.

        Args:
            i2c (machine.I2C): I2C interface instance.
            chip_size (int, optional): EEPROM chip capacity, default is AT24C512.
            addr (int, optional): Chip device I2C address, default is 0x50.

        Raises:
            ValueError: If chip capacity is not in supported range.
        """
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
        """
        向指定地址写入一个字节。

        Args:
            address (int): 写入的地址。
            data (int): 要写入的数据，范围 0-255。

        Returns:
            None

        Raises:
            ValueError: 如果地址超出范围或数据超出 0-255 范围。

        Notes:
            写入操作后会自动延时 5ms 等待 EEPROM 写入完成。

        ==========================================

        Write one byte to specified address.

        Args:
            address (int): Write address.
            data (int): Data to write, range 0-255.

        Returns:
            None

        Raises:
            ValueError: If address is out of range or data exceeds 0-255 range.

        Notes:
            Automatically delays 5ms after write operation to wait for EEPROM write completion.
        """
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
        """
        从指定地址读取一个字节。

        Args:
            address (int): 读取的地址。

        Returns:
            int: 读取的数据，范围 0-255。

        Raises:
            ValueError: 如果地址超出范围。

        ==========================================

        Read one byte from specified address.

        Args:
            address (int): Read address.

        Returns:
            int: Read data, range 0-255.

        Raises:
            ValueError: If address is out of range.
        """
        # 检查地址是否在有效范围内
        if address < 0 or address > self.max_address:
            raise ValueError("address is out of range")

        # 从指定地址读取一个字节
        value_read = self.i2c.readfrom_mem(self.addr, address, 1, addrsize=16)
        # 转换为整数并返回，使用大端序进行转换
        return int.from_bytes(value_read, "big")

    def write_page(self, address, data):
        """
        向指定地址写入一页数据，自动处理跨页情况。

        Args:
            address (int): 写入的起始地址。
            data (bytes): 要写入的数据字节序列。

        Returns:
            None

        Raises:
            ValueError: 如果地址超出范围、数据超出 0-255 范围或数据长度超出芯片容量。

        Notes:
            页大小为 64 字节，如果写入数据跨越页边界，会自动分段写入。
            每段写入后都会延时 5ms 等待 EEPROM 写入完成。

        ==========================================

        Write one page of data to specified address, automatically handles cross-page situations.

        Args:
            address (int): Write starting address.
            data (bytes): Data byte sequence to write.

        Returns:
            None

        Raises:
            ValueError: If address is out of range, data exceeds 0-255 range, or data length exceeds chip capacity.

        Notes:
            Page size is 64 bytes, if write data crosses page boundary, automatically segments and writes.
            Delays 5ms after each segment write to wait for EEPROM write completion.
        """
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
        """
        顺序读取指定长度的数据。

        Args:
            start_address (int): 读取的起始地址。
            length (int): 要读取的字节数。

        Returns:
            bytes: 读取的数据字节序列。

        Raises:
            ValueError: 如果起始地址或读取范围超出芯片容量。

        ==========================================

        Sequentially read data of specified length.

        Args:
            start_address (int): Read starting address.
            length (int): Number of bytes to read.

        Returns:
            bytes: Read data byte sequence.

        Raises:
            ValueError: If starting address or read range exceeds chip capacity.
        """
        # 检查起始地址和长度是否在有效范围内
        if start_address < 0 or (start_address + length) > self.max_address:
            raise ValueError("address is out of range")

        # 从指定起始地址读取指定长度的数据
        return self.i2c.readfrom_mem(self.addr, start_address, length, addrsize=16)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================