# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 10:00:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C通信辅助类，提供位操作和寄存器结构体访问
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
    从字节寄存器中修改指定范围的位。
    Attributes:
        bit_mask (int): 位掩码，用于提取或清除目标位段。
        register (int): 目标寄存器的地址。
        star_bit (int): 位段起始位位置（LSB为0）。
        lenght (int): 寄存器宽度（字节数）。
        lsb_first (bool): 字节序是否为小端（True表示小端，False表示大端）。
    Methods:
        __get__(obj, objtype): 读取位段的值。
        __set__(obj, value): 设置位段的值。
    Notes:
        基于I2C通信，通过描述符方式访问寄存器位段。
        注意原始变量名拼写错误（star_bit, lenght），但保留原样。
    ==========================================

        Modify specific bit fields within a byte register.
    Attributes:
        bit_mask (int): Bit mask for extracting or clearing the target bit field.
        register (int): Address of the target register.
        star_bit (int): Start bit position (LSB is 0) of the bit field.
        lenght (int): Width of the register in bytes.
        lsb_first (bool): Byte order (True for little-endian, False for big-endian).
    Methods:
        __get__(obj, objtype): Read the bit field value.
        __set__(obj, value): Write the bit field value.
    Notes:
        I2C-based communication, accessing register bit fields via descriptor protocol.
        Note the original variable name typos (star_bit, lenght) are preserved.
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
        初始化CBits描述符。
        Args:
            num_bits (int): 位段宽度（位数），必须大于0。
            register_address (int): 寄存器地址，取值范围0-255。
            start_bit (int): 起始位位置（LSB为0），取值范围0-7。
            register_width (int): 寄存器宽度（字节数），默认为1，必须大于0。
            lsb_first (bool): 字节序，True为小端，False为大端，默认为True。
        Raises:
            TypeError: 参数类型不正确。
            ValueError: 参数取值超出合法范围。
        Notes:
            无
        =========================================

            Initialize the CBits descriptor.
        Args:
            num_bits (int): Width of the bit field in bits, must be >0.
            register_address (int): Register address, range 0-255.
            start_bit (int): Start bit position (LSB is 0), range 0-7.
            register_width (int): Register width in bytes, default 1, must be >0.
            lsb_first (bool): Byte order, True for little-endian, False for big-endian, default True.
        Raises:
            TypeError: Incorrect parameter type.
            ValueError: Parameter value out of valid range.
        Notes:
            None
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
            raise TypeError(f"num_bits must be int, got {type(num_bits).__name__}")
        if not isinstance(register_address, int):
            raise TypeError(f"register_address must be int, got {type(register_address).__name__}")
        if not isinstance(start_bit, int):
            raise TypeError(f"start_bit must be int, got {type(start_bit).__name__}")
        if not isinstance(register_width, int):
            raise TypeError(f"register_width must be int, got {type(register_width).__name__}")
        if not isinstance(lsb_first, bool):
            raise TypeError(f"lsb_first must be bool, got {type(lsb_first).__name__}")

        if num_bits <= 0:
            raise ValueError(f"num_bits must be >0, got {num_bits}")
        if register_address < 0 or register_address > 0xFF:
            raise ValueError(f"register_address must be 0-255, got {register_address}")
        if start_bit < 0 or start_bit > 7:
            raise ValueError(f"start_bit must be 0-7, got {start_bit}")
        if register_width <= 0:
            raise ValueError(f"register_width must be >0, got {register_width}")

        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.star_bit = start_bit
        self.lenght = register_width
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj: Optional[Any],
        objtype: Optional[Type] = None,
    ) -> int:
        """
        读取位段的值。
        Args:
            obj (Optional[Any]): 拥有该描述符的实例对象，若为None表示类访问。
            objtype (Optional[Type]): 实例所属的类，未使用。
        Returns:
            int: 提取出的位段值。
        Raises:
            AttributeError: 当通过类访问描述符或实例缺少I2C属性时。
        Notes:
            无
        =========================================

            Read the bit field value.
        Args:
            obj (Optional[Any]): Instance object owning this descriptor. If None, class-level access.
            objtype (Optional[Type]): Class of the instance (unused).
        Returns:
            int: Extracted bit field value.
        Raises:
            AttributeError: When accessing descriptor from class or instance lacks I2C attributes.
        Notes:
            None
        """
        # 验证obj是否为实例对象
        if obj is None:
            raise AttributeError("Cannot access CBits descriptor from class")

        # 验证实例具有必要的I2C属性
        if not hasattr(obj, "_i2c"):
            raise AttributeError("Instance missing '_i2c' attribute")
        if not hasattr(obj, "_address"):
            raise AttributeError("Instance missing '_address' attribute")

        # 原有逻辑：读取寄存器数据
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj: Optional[Any], value: int) -> None:
        """
        设置位段的值。
        Args:
            obj (Optional[Any]): 拥有该描述符的实例对象，若为None表示类访问。
            value (int): 要写入的值，必须适合位段宽度。
        Raises:
            AttributeError: 当通过类访问描述符或实例缺少I2C属性时。
            TypeError: value类型错误。
            ValueError: value超出位段表示范围。
        Notes:
            无
        =========================================

            Write the bit field value.
        Args:
            obj (Optional[Any]): Instance object owning this descriptor. If None, class-level access.
            value (int): Value to write, must fit within the bit field width.
        Raises:
            AttributeError: When accessing descriptor from class or instance lacks I2C attributes.
            TypeError: Incorrect type for value.
            ValueError: Value out of range for the bit field.
        Notes:
            None
        """
        # 验证obj
        if obj is None:
            raise AttributeError("Cannot access CBits descriptor from class")
        if not hasattr(obj, "_i2c"):
            raise AttributeError("Instance missing '_i2c' attribute")
        if not hasattr(obj, "_address"):
            raise AttributeError("Instance missing '_address' attribute")

        # 验证value类型和范围
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        max_val = (self.bit_mask >> self.star_bit) & 0xFFFFFFFF
        if value < 0 or value > max_val:
            raise ValueError(f"value must be 0-{max_val}, got {value}")

        # 原有逻辑：读取当前寄存器值，修改位段，写回
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]
        reg &= ~self.bit_mask

        value <<= self.star_bit
        reg |= value
        reg = reg.to_bytes(self.lenght, "big")

        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    将寄存器区域作为结构体（通过struct格式）访问。
    Attributes:
        format (str): struct模块的格式字符串，定义寄存器数据的解析方式。
        register (int): 起始寄存器地址。
        lenght (int): 寄存器区域的总字节数（由format计算得出）。
    Methods:
        __get__(obj, objtype): 读取结构体数据并解包。
        __set__(obj, value): 将值打包后写入寄存器区域。
    Notes:
        基于I2C通信，支持多字节寄存器连续读写。
        若长度<=2字节，__get__返回单个值；否则返回元组。
    ==========================================

        Access a register region as a struct (using struct format).
    Attributes:
        format (str): Struct module format string defining how to parse register data.
        register (int): Starting register address.
        lenght (int): Total byte length of the register region (calculated from format).
    Methods:
        __get__(obj, objtype): Read the struct data and unpack.
        __set__(obj, value): Pack the value and write to the register region.
    Notes:
        I2C-based communication, supports consecutive multi-byte register reads/writes.
        If length <= 2 bytes, __get__ returns a single value; otherwise a tuple.
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct描述符。
        Args:
            register_address (int): 起始寄存器地址，取值范围0-255。
            form (str): struct格式字符串，必须有效且长度>0。
        Raises:
            TypeError: 参数类型错误。
            ValueError: 参数取值无效或格式字符串导致计算长度为0。
        Notes:
            无
        =========================================

            Initialize the RegisterStruct descriptor.
        Args:
            register_address (int): Starting register address, range 0-255.
            form (str): Struct format string, must be valid and non-empty.
        Raises:
            TypeError: Incorrect parameter type.
            ValueError: Invalid parameter value or format string results in zero length.
        Notes:
            None
        """
        # 参数验证
        if register_address is None:
            raise ValueError("register_address cannot be None")
        if form is None:
            raise ValueError("form cannot be None")
        if not isinstance(register_address, int):
            raise TypeError(f"register_address must be int, got {type(register_address).__name__}")
        if not isinstance(form, str):
            raise TypeError(f"form must be str, got {type(form).__name__}")
        if register_address < 0 or register_address > 0xFF:
            raise ValueError(f"register_address must be 0-255, got {register_address}")
        if len(form) == 0:
            raise ValueError("form string cannot be empty")

        self.format = form
        self.register = register_address
        self.lenght = struct.calcsize(form)
        if self.lenght <= 0:
            raise ValueError(f"struct format '{form}' results in non-positive length {self.lenght}")

    def __get__(
        self,
        obj: Optional[Any],
        objtype: Optional[Type] = None,
    ):
        """
        读取寄存器结构体数据。
        Args:
            obj (Optional[Any]): 拥有该描述符的实例对象，若为None表示类访问。
            objtype (Optional[Type]): 实例所属的类，未使用。
        Returns:
            Union[int, Tuple]: 若总长度<=2返回单个解包值，否则返回解包元组。
        Raises:
            AttributeError: 当通过类访问描述符或实例缺少I2C属性时。
        Notes:
            无
        =========================================

            Read the register struct data.
        Args:
            obj (Optional[Any]): Instance object owning this descriptor. If None, class-level access.
            objtype (Optional[Type]): Class of the instance (unused).
        Returns:
            Union[int, Tuple]: Single unpacked value if total length <=2, else unpacked tuple.
        Raises:
            AttributeError: When accessing descriptor from class or instance lacks I2C attributes.
        Notes:
            None
        """
        # 验证obj
        if obj is None:
            raise AttributeError("Cannot access RegisterStruct descriptor from class")
        if not hasattr(obj, "_i2c"):
            raise AttributeError("Instance missing '_i2c' attribute")
        if not hasattr(obj, "_address"):
            raise AttributeError("Instance missing '_address' attribute")

        # 原有逻辑：读取数据并解包
        if self.lenght <= 2:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj: Optional[Any], value) -> None:
        """
        写入寄存器结构体数据。
        Args:
            obj (Optional[Any]): 拥有该描述符的实例对象，若为None表示类访问。
            value: 要写入的值，必须与struct格式匹配。
        Raises:
            AttributeError: 当通过类访问描述符或实例缺少I2C属性时。
            TypeError: value类型无法打包为指定格式。
            struct.error: 打包时数据不符合格式要求。
        Notes:
            无
        =========================================

            Write the register struct data.
        Args:
            obj (Optional[Any]): Instance object owning this descriptor. If None, class-level access.
            value: Value to write, must match the struct format.
        Raises:
            AttributeError: When accessing descriptor from class or instance lacks I2C attributes.
            TypeError: Value type cannot be packed into the specified format.
            struct.error: Data does not conform to format requirements during packing.
        Notes:
            None
        """
        # 验证obj
        if obj is None:
            raise AttributeError("Cannot access RegisterStruct descriptor from class")
        if not hasattr(obj, "_i2c"):
            raise AttributeError("Instance missing '_i2c' attribute")
        if not hasattr(obj, "_address"):
            raise AttributeError("Instance missing '_address' attribute")

        # 原有逻辑：打包并写入
        mem_value = value.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
