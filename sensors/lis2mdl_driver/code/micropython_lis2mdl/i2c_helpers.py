# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/16 下午2:30
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C通信辅助工具，提供位操作和寄存器结构体读写功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class CBits:
    """
    用于操作寄存器中特定位域的类
    支持从多字节寄存器中读取或写入指定范围的比特位

    Attributes:
        bit_mask (int): 位掩码，用于提取目标比特位
        register (int): 寄存器地址
        star_bit (int): 起始位位置（从0开始计数）
        lenght (int): 寄存器宽度（字节数）
        lsb_first (bool): 是否为小端字节序

    Methods:
        __get__(): 读取位域值
        __set__(): 写入位域值

    Notes:
        支持跨字节位域操作，自动处理字节序
        所有操作基于I2C读写原语实现

    ==========================================
    Class for operating specific bit fields in registers
    Supports reading or writing specified bit ranges from multi-byte registers

    Attributes:
        bit_mask (int): Bit mask for extracting target bits
        register (int): Register address
        star_bit (int): Start bit position (counting from 0)
        lenght (int): Register width (in bytes)
        lsb_first (bool): Whether little-endian byte order is used

    Methods:
        __get__(): Read bit field value
        __set__(): Write bit field value

    Notes:
        Supports cross-byte bit field operations, automatically handles byte order
        All operations are based on I2C read/write primitives
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        """
        初始化CBits实例

        Args:
            num_bits (int): 位域宽度（比特数）
            register_address (int): 寄存器地址
            start_bit (int): 起始位位置
            register_width (int): 寄存器字节宽度，默认为1
            lsb_first (bool): 是否小端字节序，默认为True

        Raises:
            None

        Notes:
            无

        ==========================================
        Initialize CBits instance

        Args:
            num_bits (int): Bit field width (number of bits)
            register_address (int): Register address
            start_bit (int): Start bit position
            register_width (int): Register byte width, defaults to 1
            lsb_first (bool): Whether little-endian byte order, defaults to True

        Raises:
            None

        Notes:
            None
        """
        # 计算位掩码，用于提取和设置特定位域
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        # 存储寄存器地址
        self.register = register_address
        # 存储起始位位置
        self.star_bit = start_bit
        # 存储寄存器字节长度
        self.lenght = register_width
        # 存储字节序标志
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj,
        objtype=None,
    ) -> int:
        """
        读取位域值（描述符的getter方法）

        Args:
            obj: 拥有该描述符的实例对象
            objtype: 拥有该描述符的类类型（可选）

        Returns:
            int: 提取后的位域值

        Raises:
            None

        Notes:
            从I2C设备读取寄存器数据，然后根据位掩码和起始位提取目标值

        ==========================================
        Read bit field value (descriptor getter)

        Args:
            obj: Instance object owning this descriptor
            objtype: Class type owning this descriptor (optional)

        Returns:
            int: Extracted bit field value

        Raises:
            None

        Notes:
            Read register data from I2C device, then extract target value based on bit mask and start bit
        """
        # 从I2C设备读取寄存器数据
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 将字节数据组合成整数
        reg = 0
        # 确定字节序处理顺序
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        # 按顺序组合字节
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 应用位掩码并右移提取目标位域
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        写入位域值（描述符的setter方法）

        Args:
            obj: 拥有该描述符的实例对象
            value (int): 要写入的位域值

        Raises:
            None

        Notes:
            先读取当前寄存器值，更新目标位域后写回设备
            确保不影响其他位域

        ==========================================
        Write bit field value (descriptor setter)

        Args:
            obj: Instance object owning this descriptor
            value (int): Bit field value to write

        Raises:
            None

        Notes:
            Read current register value first, update target bit field then write back to device
            Ensure other bit fields are not affected
        """
        # 读取当前寄存器值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 将字节数据组合成整数
        reg = 0
        # 确定字节序处理顺序
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        # 按顺序组合字节
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清除目标位域
        reg &= ~self.bit_mask

        # 将新值左移到正确位置并合并
        value <<= self.star_bit
        reg |= value

        # 将整数转换回字节数组（大端序）
        reg = reg.to_bytes(self.lenght, "big")

        # 写回I2C设备
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    用于将寄存器映射为结构化数据的类
    支持使用struct格式字符串自动打包/解包寄存器数据

    Attributes:
        format (str): struct模块格式字符串
        register (int): 寄存器地址
        lenght (int): 数据长度（字节数）

    Methods:
        __get__(): 读取并解包寄存器数据
        __set__(): 打包并写入寄存器数据

    Notes:
        支持多种数据类型，通过struct格式字符串指定
        长度小于等于2字节时返回标量值，否则返回元组

    ==========================================
    Class for mapping registers to structured data
    Supports automatic packing/unpacking of register data using struct format strings

    Attributes:
        format (str): struct module format string
        register (int): Register address
        lenght (int): Data length (in bytes)

    Methods:
        __get__(): Read and unpack register data
        __set__(): Pack and write register data

    Notes:
        Supports multiple data types specified by struct format string
        Returns scalar value when length <= 2 bytes, otherwise returns tuple
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct实例

        Args:
            register_address (int): 寄存器地址
            form (str): struct模块格式字符串

        Raises:
            None

        Notes:
            自动计算格式字符串对应的数据长度

        ==========================================
        Initialize RegisterStruct instance

        Args:
            register_address (int): Register address
            form (str): struct module format string

        Raises:
            None

        Notes:
            Automatically calculate data length from format string
        """
        # 存储格式字符串
        self.format = form
        # 存储寄存器地址
        self.register = register_address
        # 计算格式字符串对应的字节长度
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        """
        读取并解包寄存器数据（描述符的getter方法）

        Args:
            obj: 拥有该描述符的实例对象
            objtype: 拥有该描述符的类类型（可选）

        Returns:
            根据格式字符串解包后的数据，长度<=2返回标量，否则返回元组

        Raises:
            None

        Notes:
            根据数据长度自动选择返回标量或元组

        ==========================================
        Read and unpack register data (descriptor getter)

        Args:
            obj: Instance object owning this descriptor
            objtype: Class type owning this descriptor (optional)

        Returns:
            Unpacked data according to format string, returns scalar when length<=2 else tuple

        Raises:
            None

        Notes:
            Automatically choose return scalar or tuple based on data length
        """
        # 判断数据长度，小于等于2字节时返回标量值
        if self.lenght <= 2:
            # 读取并解包单个值
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            # 读取并解包多个值，返回元组
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj, value) -> None:
        """
        打包并写入寄存器数据（描述符的setter方法）

        Args:
            obj: 拥有该描述符的实例对象
            value: 要写入的数据（类型与格式字符串匹配）

        Raises:
            None

        Notes:
            使用struct模块将数据打包后写入I2C设备

        ==========================================
        Pack and write register data (descriptor setter)

        Args:
            obj: Instance object owning this descriptor
            value: Data to write (type must match format string)

        Raises:
            None

        Notes:
            Pack data using struct module then write to I2C device
        """
        # 使用格式字符串打包数据
        mem_value = struct.pack(self.format, value)
        # 写入I2C设备
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
