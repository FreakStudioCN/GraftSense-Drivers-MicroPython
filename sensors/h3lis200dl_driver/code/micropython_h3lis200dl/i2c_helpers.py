# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024-03-27
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C通信辅助工具类库，提供位操作和结构体寄存器访问功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================
import struct


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class CBits:
    """
    Changes bits from a byte register
    字节寄存器位操作描述符类，用于读写寄存器中的特定位段

    Attributes:
        bit_mask (int): 位掩码，用于隔离目标位
        register (int): 寄存器地址
        star_bit (int): 起始位位置（LSB为0）
        lenght (int): 寄存器宽度（字节数）
        lsb_first (bool): 字节序是否为小端模式

    Notes:
        - 作为描述符使用时，需绑定到支持I2C读写的设备对象
        - 依赖设备对象具有_i2c和_address属性
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        # 参数None显式检查
        if None in (num_bits, register_address, start_bit):
            raise ValueError("num_bits, register_address, start_bit cannot be None")

        # 计算指定位数对应的掩码并移位到起始位
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        # 寄存器地址
        self.register = register_address
        # 起始位位置
        self.star_bit = start_bit
        # 寄存器宽度（字节数）
        self.lenght = register_width
        # 字节序标志，True表示小端（LSB在前）
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj: object,
        objtype: type = None,
    ) -> int:
        """
        描述符getter方法，读取寄存器中的特定位段

        Args:
            obj: 绑定描述符的设备对象
            objtype: 所有者类（描述符协议要求）

        Returns:
            int: 提取出的位段整数值

        Notes:
            - 从设备地址读取指定长度的寄存器值
            - 根据字节序组合多字节寄存器值
            - 应用掩码并右移得到目标位段
        """
        # 从I2C设备读取寄存器原始字节数据
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 组合多个字节为整数
        reg = 0
        # 默认处理顺序：从高位字节到低位字节（大端）
        order = range(len(mem_value) - 1, -1, -1)
        # 如果是小端模式则反转处理顺序
        if not self.lsb_first:
            order = reversed(order)
        # 按顺序组合字节
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 应用掩码并右移到起始位，得到目标位段值
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj: object, value: int) -> None:
        """
        描述符setter方法，写入寄存器中的特定位段

        Args:
            obj: 绑定描述符的设备对象
            value: 要写入的整数值

        Raises:
            ValueError: 当value为None时抛出

        Notes:
            - 保持寄存器中其他位不变，只修改目标位段
            - 执行读-修改-写操作确保原子性
        """
        # 参数None显式检查
        if value is None:
            raise ValueError("value cannot be None")

        # 读取当前寄存器值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 组合多个字节为整数
        reg = 0
        # 根据字节序确定处理顺序
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        # 按顺序组合字节
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清空目标位段（使用掩码取反）
        reg &= ~self.bit_mask

        # 将新值移位到正确位置并合并到寄存器值
        value <<= self.star_bit
        reg |= value
        # 将整数转换为字节串（大端格式）
        reg = reg.to_bytes(self.lenght, "big")

        # 写回寄存器
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    Register Struct
    寄存器结构体描述符类，用于读写整个寄存器结构

    Attributes:
        format (str): struct模块格式字符串，定义数据结构
        register (int): 寄存器地址
        lenght (int): 数据长度（字节数），由格式字符串计算得出

    Notes:
        - 用于读取和写入整个寄存器数据
        - 支持struct模块的所有格式字符
        - 当数据长度>2时返回元组，否则返回标量值
    """

    def __init__(self, register_address: int, form: str) -> None:
        # 参数None显式检查
        if None in (register_address, form):
            raise ValueError("register_address and form cannot be None")

        # struct格式字符串
        self.format = form
        # 寄存器地址
        self.register = register_address
        # 计算格式字符串对应的字节长度
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj: object,
        objtype: type = None,
    ) -> any:
        """
        描述符getter方法，读取并解析寄存器结构

        Args:
            obj: 绑定描述符的设备对象
            objtype: 所有者类（描述符协议要求）

        Returns:
            any: 解析后的数据，标量或元组

        Notes:
            - 长度≤2时返回单个值，否则返回元组
            - 使用memoryview避免不必要的内存复制
        """
        # 读取原始寄存器数据
        if self.lenght <= 2:
            # 长度小于等于2字节时，返回解包后的单个值
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            # 长度大于2字节时，返回解包后的元组
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj: object, value: int) -> None:
        """
        描述符setter方法，将整数值写入寄存器

        Args:
            obj: 绑定描述符的设备对象
            value: 要写入的整数值

        Raises:
            ValueError: 当value为None时抛出

        Notes:
            - 将整数转换为指定长度的字节串
            - 以大端格式写入寄存器
        """
        # 参数None显式检查
        if value is None:
            raise ValueError("value cannot be None")

        # 将整数转换为大端字节串
        mem_value = value.to_bytes(self.lenght, "big")
        # 写入寄存器
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
