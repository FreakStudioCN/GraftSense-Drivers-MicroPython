# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/15 下午3:30
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : MMC5603驱动I2C通信辅助模块，提供位字段和寄存器结构体操作
# @License : MIT
__version__ = "1.0.0"
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
    用于操作单个寄存器中位字段的描述符类。
    支持读取和写入指定范围内的位。

    Attributes:
        bit_mask (int): 位掩码，覆盖目标位区域
        register (int): 目标寄存器地址
        star_bit (int): 起始位位置(0-based LSB)
        lenght (int): 寄存器宽度(字节数)
        lsb_first (bool): 多字节时是否为小端序

    Methods:
        __get__(obj, objtype): 读取位字段值
        __set__(obj, value): 写入位字段值

    Notes:
        使用描述符协议，需附加到具有_i2c和_address属性的类实例上。

    ==========================================
    Descriptor class for manipulating bit fields within a single register.
    Supports reading and writing a specified range of bits.

    Attributes:
        bit_mask (int): Bit mask covering the target bit region
        register (int): Target register address
        star_bit (int): Start bit position (0-based LSB)
        lenght (int): Register width in bytes
        lsb_first (bool): Little-endian order for multi-byte registers

    Methods:
        __get__(obj, objtype): Read the bit field value
        __set__(obj, value): Write the bit field value

    Notes:
        Uses descriptor protocol, must be attached to a class instance with _i2c and _address attributes.
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
        初始化CBits描述符实例。

        Args:
            num_bits (int): 位字段的位数，取值范围1-8(单字节)或1-16(双字节)
            register_address (int): 寄存器地址，0-255
            start_bit (int): 起始位索引(LSB从0开始)，0-7
            register_width (int): 寄存器字节宽度，1或2，默认1
            lsb_first (bool): 多字节时是否为小端序，默认True

        Raises:
            ValueError: 任何参数为None或取值范围无效
            TypeError: 参数类型错误

        Notes:
            位掩码根据num_bits和start_bit自动计算。

        ==========================================
        Initialize the CBits descriptor instance.

        Args:
            num_bits (int): Number of bits in the field, range 1-8 (single byte) or 1-16 (two bytes)
            register_address (int): Register address, 0-255
            start_bit (int): Start bit index (LSB 0-based), 0-7
            register_width (int): Register byte width, 1 or 2, default 1
            lsb_first (bool): Little-endian order for multi-byte registers, default True

        Raises:
            ValueError: Any parameter is None or out of valid range
            TypeError: Parameter type error

        Notes:
            Bit mask is automatically calculated from num_bits and start_bit.
        """
        # 参数验证
        if num_bits is None:
            raise ValueError("num_bits cannot be None")
        if register_address is None:
            raise ValueError("register_address cannot be None")
        if start_bit is None:
            raise ValueError("start_bit cannot be None")
        if register_width is None:
            raise ValueError("register_width cannot be None")
        if lsb_first is None:
            raise ValueError("lsb_first cannot be None")

        if not isinstance(num_bits, int):
            raise TypeError("num_bits must be an integer")
        if not isinstance(register_address, int):
            raise TypeError("register_address must be an integer")
        if not isinstance(start_bit, int):
            raise TypeError("start_bit must be an integer")
        if not isinstance(register_width, int):
            raise TypeError("register_width must be an integer")
        if not isinstance(lsb_first, bool):
            raise TypeError("lsb_first must be a boolean")

        if num_bits < 1 or num_bits > 16:
            raise ValueError("num_bits must be between 1 and 16")
        if register_address < 0 or register_address > 0xFF:
            raise ValueError("register_address must be between 0 and 255")
        if start_bit < 0 or start_bit > 7:
            raise ValueError("start_bit must be between 0 and 7")
        if register_width not in (1, 2):
            raise ValueError("register_width must be 1 or 2")

        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.star_bit = start_bit
        self.lenght = register_width
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj,
        objtype=None,
    ) -> int:
        """
        读取位字段的当前值。

        Args:
            obj: 拥有该描述符的实例对象
            objtype: 拥有该描述符的类(可选)

        Returns:
            int: 位字段的整数值

        Notes:
            从I2C设备读取寄存器数据，根据lsb_first和lenght组合成整数后提取位字段。

        ==========================================
        Read the current value of the bit field.

        Args:
            obj: Instance object owning this descriptor
            objtype: Class owning this descriptor (optional)

        Returns:
            int: Integer value of the bit field

        Notes:
            Reads register data from I2C device, assembles integer based on lsb_first and lenght,
            then extracts the bit field.
        """
        # 读取寄存器数据
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 组合成整数
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取位字段
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        设置位字段的值。

        Args:
            obj: 拥有该描述符的实例对象
            value (int): 要写入的值，必须能容纳于num_bits位中

        Raises:
            ValueError: value为None或超出位字段范围
            TypeError: value不是整数类型

        Notes:
            先读取当前寄存器值，修改目标位后写回。

        ==========================================
        Set the value of the bit field.

        Args:
            obj: Instance object owning this descriptor
            value (int): Value to write, must fit within num_bits

        Raises:
            ValueError: value is None or out of bit field range
            TypeError: value is not an integer

        Notes:
            Reads current register value, modifies target bits, then writes back.
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError("Value must be an integer")

        # 计算最大值
        max_val = (1 << (self.bit_mask.bit_length() - self.star_bit)) - 1
        if value < 0 or value > max_val:
            raise ValueError(f"Value must be between 0 and {max_val}")

        # 读取当前寄存器值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 组合成整数
        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清除目标位并设置新值
        reg &= ~self.bit_mask
        value <<= self.star_bit
        reg |= value

        # 写回寄存器
        reg = reg.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    将整个寄存器或连续寄存器区域映射为结构体的描述符类。
    使用struct格式字符串进行打包/解包。

    Attributes:
        format (str): struct格式字符串，如'<H'表示小端无符号短整型
        register (int): 起始寄存器地址
        lenght (int): 寄存器区域字节长度

    Methods:
        __get__(obj, objtype): 读取并解包寄存器数据
        __set__(obj, value): 打包并写入寄存器数据

    Notes:
        支持任意长度的寄存器区域，返回tuple或单个数值。

    ==========================================
    Descriptor class mapping a whole register or contiguous register region to a struct.
    Uses struct format strings for packing/unpacking.

    Attributes:
        format (str): Struct format string, e.g. '<H' for little-endian unsigned short
        register (int): Starting register address
        lenght (int): Byte length of the register region

    Methods:
        __get__(obj, objtype): Read and unpack register data
        __set__(obj, value): Pack and write register data

    Notes:
        Supports arbitrary length register regions, returns tuple or single value.
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct描述符实例。

        Args:
            register_address (int): 起始寄存器地址，0-255
            form (str): struct格式字符串，必须非空且有效

        Raises:
            ValueError: 任何参数为None或form为空字符串
            TypeError: 参数类型错误

        Notes:
            根据form计算所需字节长度。

        ==========================================
        Initialize the RegisterStruct descriptor instance.

        Args:
            register_address (int): Starting register address, 0-255
            form (str): Struct format string, must be non-empty and valid

        Raises:
            ValueError: Any parameter is None or form is empty string
            TypeError: Parameter type error

        Notes:
            Byte length is calculated from the format string.
        """
        # 参数验证
        if register_address is None:
            raise ValueError("register_address cannot be None")
        if form is None:
            raise ValueError("format string cannot be None")

        if not isinstance(register_address, int):
            raise TypeError("register_address must be an integer")
        if not isinstance(form, str):
            raise TypeError("format string must be a string")

        if register_address < 0 or register_address > 0xFF:
            raise ValueError("register_address must be between 0 and 255")
        if len(form) == 0:
            raise ValueError("format string cannot be empty")

        self.format = form
        self.register = register_address
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        """
        读取寄存器区域并解包为Python对象。

        Args:
            obj: 拥有该描述符的实例对象
            objtype: 拥有该描述符的类(可选)

        Returns:
            Union[int, tuple]: 如果格式只有一个元素则返回数值，否则返回tuple

        Notes:
            长度<=2字节时返回单个数值，否则返回tuple。

        ==========================================
        Read register region and unpack to Python object.

        Args:
            obj: Instance object owning this descriptor
            objtype: Class owning this descriptor (optional)

        Returns:
            Union[int, tuple]: Single value if format has one element, otherwise tuple

        Notes:
            Returns single value for length <=2 bytes, otherwise tuple.
        """
        # 读取寄存器数据
        data = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 解包
        if self.lenght <= 2:
            value = struct.unpack(self.format, memoryview(data))[0]
        else:
            value = struct.unpack(self.format, memoryview(data))
        return value

    def __set__(self, obj, value):
        """
        将Python对象打包并写入寄存器区域。

        Args:
            obj: 拥有该描述符的实例对象
            value: 要写入的值(类型需匹配format)

        Raises:
            ValueError: value为None
            TypeError: value类型与format不匹配

        Notes:
            自动将value打包为大端字节序并写入。

        ==========================================
        Pack Python object and write to register region.

        Args:
            obj: Instance object owning this descriptor
            value: Value to write (type must match format)

        Raises:
            ValueError: value is None
            TypeError: value type does not match format

        Notes:
            Automatically packs value as big-endian and writes.
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")

        # 注意：不进行深度类型验证，因为struct.pack会抛出相应异常
        # 将值打包为大端字节序
        mem_value = value.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================


# ======================================== 主程序 ============================================
