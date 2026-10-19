# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午4:52
# @Author  : jposada202020
# @File    : i2c_helpers.py
# @Description : I2C通信辅助模块，提供位操作和寄存器结构体操作，支持I2C设备寄存器特定位段读写和结构体格式解析 参考自：https://github.com/jposada202020/MicroPython_MMA8451
# @License : MIT

__version__ = "0.1.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入struct模块，用于二进制数据的打包和解包操作
import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
        对I2C设备寄存器中的特定位段进行读写操作
        Attributes:
            bit_mask (int): 用于提取/修改目标位段的位掩码
            register (int): 目标寄存器地址
            star_bit (int): 位段起始位索引（0为最低位）
            lenght (int): 寄存器宽度（字节数）
            lsb_first (bool): 字节序标识，True为LSB优先，False为MSB优先

        Methods:
            __init__: 初始化CBits实例，配置位操作的参数
            __get__: 读取寄存器中指定的位段值
            __set__: 将值写入寄存器的指定位段

        Notes:
            1. 支持单字节和多字节寄存器的位操作
            2. 依赖于调用对象具备_i2c（I2C通信对象）和_address（设备地址）属性
            3. 位索引从0开始，最低有效位为0

    ==========================================
    Read and write specific bit fields in I2C device registers
    Attributes:
        bit_mask (int): Bit mask for extracting/modifying target bit fields
        register (int): Target register address
        star_bit (int): Start bit index of the bit field (0 for LSB)
        lenght (int): Register width in bytes
        lsb_first (bool): Byte order flag, True for LSB first, False for MSB first

    Methods:
        __init__: Initialize CBits instance with bit operation parameters
        __get__: Read the value of the specified bit field in the register
        __set__: Write a value to the specified bit field in the register

    Notes:
        1. Supports bit operations on single-byte and multi-byte registers
        2. Depends on the calling object having _i2c (I2C communication object) and _address (device address) attributes
        3. Bit index starts from 0, with the least significant bit as 0
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width=1,
        lsb_first=True,
    ) -> None:
        """
        初始化CBits实例，配置位操作的核心参数
        Args:
            num_bits (int): 要操作的位段长度（位数）
            register_address (int): 目标寄存器地址
            start_bit (int): 位段起始位索引（0为最低位）
            register_width (int, optional): 寄存器宽度（字节数），默认值1
            lsb_first (bool, optional): 字节序标识，True为LSB优先，默认值True

        Raises:
            无

        Notes:
            1. 位掩码会根据num_bits和start_bit自动计算
            2. register_width用于处理多字节寄存器（如2字节的16位寄存器）


        ==========================================
        Initialize CBits instance with core parameters for bit operations
        Args:
            num_bits (int): Length of the bit field to operate on (number of bits)
            register_address (int): Target register address
            start_bit (int): Start bit index of the bit field (0 for LSB)
            register_width (int, optional): Register width in bytes, default 1
            lsb_first (bool, optional): Byte order flag, True for LSB first, default True

        Raises:
            None

        Notes:
            1. Bit mask is automatically calculated based on num_bits and start_bit
            2. register_width is used to handle multi-byte registers (e.g., 16-bit registers with 2 bytes)
        """
        # 计算位掩码，用于提取或修改指定范围的位
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        # 存储目标寄存器地址
        self.register = register_address
        # 存储位段起始位索引
        self.star_bit = start_bit
        # 存储寄存器宽度（字节数）
        self.lenght = register_width
        # 存储字节序标识
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj,
        objtype=None,
    ) -> int:
        """
        读取寄存器中指定位段的值
        Args:
            obj: 调用该属性的对象实例，需包含_i2c和_address属性
            objtype: 对象类型，默认None

        Raises:
            无

        Notes:
            1. 通过I2C读取寄存器原始数据后，按字节序重组为整数
            2. 使用位掩码提取目标位段的值并右移到最低位


        ==========================================
        Read the value of the specified bit field in the register
        Args:
            obj: Instance of the object calling this property, must contain _i2c and _address attributes
            objtype: Type of the object, default None

        Raises:
            None

        Notes:
            1. Reads raw register data via I2C and reconstructs it into an integer according to byte order
            2. Uses bit mask to extract the target bit field value and shift it to the least significant bit
        """
        # 从I2C设备读取指定寄存器的原始字节数据
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 根据lsb_first配置重组字节序为整数
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取特定位段的值并右移到最低位
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        将值写入寄存器的指定位段
        Args:
            obj: 调用该属性的对象实例，需包含_i2c和_address属性
            value (int): 要写入的位段值

        Raises:
            无

        Notes:
            1. 先读取寄存器当前值，清除目标位段后写入新值
            2. 按字节序重组为字节数据后写回寄存器


        ==========================================
        Write a value to the specified bit field in the register
        Args:
            obj: Instance of the object calling this property, must contain _i2c and _address attributes
            value (int): Value to write to the bit field

        Raises:
            None

        Notes:
            1. First reads the current register value, clears the target bit field, then writes the new value
            2. Reconstructs into byte data according to byte order and writes back to the register
        """
        # 读取寄存器当前的原始字节数据
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 重组字节序得到寄存器的整数值
        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]
        # 清除寄存器中目标位段的原有值
        reg &= ~self.bit_mask

        # 将新值左移到目标位段位置并合并到寄存器值中
        value <<= self.star_bit
        reg |= value
        # 将整数转换为指定长度的字节数据（大端序）
        reg = reg.to_bytes(self.lenght, "big")

        # 将修改后的数据写回I2C设备寄存器
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
        将I2C设备寄存器数据解析为指定结构体格式，支持读写操作
        Attributes:
            format (str): struct模块兼容的格式字符串（如'B'表示单字节，'H'表示16位无符号整数）
            register (int): 目标寄存器地址
            lenght (int): 数据字节长度（由format自动计算）

        Methods:
            __init__: 初始化RegisterStruct实例，配置寄存器地址和结构体格式
            __get__: 读取寄存器数据并解析为指定格式的值
            __set__: 将值按指定格式打包后写入寄存器

        Notes:
            1. 依赖于调用对象具备_i2c（I2C通信对象）和_address（设备地址）属性
            2. 数据长度≤2字节时返回单个值，否则返回元组
            3. 写入时使用大端序（big-endian）打包数据

    ==========================================
    Parse I2C device register data into a specified struct format, supporting read/write operations
    Attributes:
        format (str): struct module compatible format string (e.g., 'B' for single byte, 'H' for 16-bit unsigned integer)
        register (int): Target register address
        lenght (int): Data length in bytes (automatically calculated from format)

    Methods:
        __init__: Initialize RegisterStruct instance with register address and struct format
        __get__: Read register data and parse it into a value in the specified format
        __set__: Pack the value into the specified format and write it to the register

    Notes:
        1. Depends on the calling object having _i2c (I2C communication object) and _address (device address) attributes
        2. Returns a single value when data length ≤ 2 bytes, otherwise returns a tuple
        3. Uses big-endian to pack data when writing
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct实例，配置寄存器地址和结构体格式
        Args:
            register_address (int): 目标寄存器地址
            form (str): struct模块兼容的格式字符串

        Raises:
            无

        Notes:
            1. 数据长度由struct.calcsize自动计算，无需手动指定
            2. 支持所有struct模块的标准格式字符（如'b'/'B'/'h'/'H'/'i'/'I'等）


        ==========================================
        Initialize RegisterStruct instance with register address and struct format
        Args:
            register_address (int): Target register address
            form (str): struct module compatible format string

        Raises:
            None

        Notes:
            1. Data length is automatically calculated by struct.calcsize, no need to specify manually
            2. Supports all standard format characters of the struct module (e.g., 'b'/'B'/'h'/'H'/'i'/'I' etc.)
        """
        # 存储结构体格式字符串
        self.format = form
        # 存储目标寄存器地址
        self.register = register_address
        # 计算格式字符串对应的字节长度
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        """
        读取寄存器数据并解析为指定格式的值
        Args:
            obj: 调用该属性的对象实例，需包含_i2c和_address属性
            objtype: 对象类型，默认None

        Raises:
            无

        Notes:
            1. 使用memoryview优化数据读取性能
            2. 数据长度≤2字节时返回解包后的第一个值（单个值），否则返回完整元组


        ==========================================
        Read register data and parse it into a value in the specified format
        Args:
            obj: Instance of the object calling this property, must contain _i2c and _address attributes
            objtype: Type of the object, default None

        Raises:
            None

        Notes:
            1. Uses memoryview to optimize data reading performance
            2. Returns the first unpacked value (single value) when data length ≤ 2 bytes, otherwise returns the full tuple
        """
        # 从I2C设备读取指定寄存器的原始字节数据
        data = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)
        # 根据格式字符串解包数据，长度≤2字节时返回单个值，否则返回元组
        if self.lenght <= 2:
            value = struct.unpack(self.format, memoryview(data))[0]
        else:
            value = struct.unpack(self.format, memoryview(data))
        return value

    def __set__(self, obj, value) -> None:
        """
        将值按指定格式打包后写入寄存器
        Args:
            obj: 调用该属性的对象实例，需包含_i2c和_address属性
            value: 要写入的值（单个值或元组，需与格式字符串匹配）

        Raises:
            无

        Notes:
            1. 使用大端序（big-endian）将值转换为字节数据
            2. 写入的值类型和数量必须与格式字符串匹配


        ==========================================
        Pack the value into the specified format and write it to the register
        Args:
            obj: Instance of the object calling this property, must contain _i2c and _address attributes
            value: Value to write (single value or tuple, must match the format string)

        Raises:
            None

        Notes:
            1. Converts the value to byte data using big-endian
            2. The type and number of values to write must match the format string
        """
        # 将值转换为指定长度的字节数据（大端序）
        mem_value = value.to_bytes(self.lenght, "big")
        # 将打包后的字节数据写回I2C设备寄存器
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
