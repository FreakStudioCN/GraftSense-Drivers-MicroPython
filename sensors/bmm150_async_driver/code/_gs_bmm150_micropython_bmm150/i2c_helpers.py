# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2023/01/01 00:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C 寄存器操作辅助类（基于 Adafruit Register 库）
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class CBits:
    """
    I2C 寄存器位操作描述符类

    Attributes:
        bit_mask (int): 位掩码
        register (int): 寄存器地址
        star_bit (int): 起始位位置
        lenght (int): 寄存器宽度（字节数）
        lsb_first (bool): 是否 LSB 优先

    Methods:
        __get__(): 读取寄存器指定位
        __set__(): 写入寄存器指定位

    Notes:
        - 用作类属性描述符，自动处理位级读写
        - 依赖宿主对象的 _i2c 和 _address 属性
        - 基于 Adafruit Register i2c_bits 实现

    ==========================================
    I2C register bit operation descriptor class.

    Attributes:
        bit_mask (int): Bit mask
        register (int): Register address
        star_bit (int): Start bit position
        lenght (int): Register width in bytes
        lsb_first (bool): LSB first flag

    Methods:
        __get__(): Read specified bits from register
        __set__(): Write specified bits to register

    Notes:
        - Used as class attribute descriptor for automatic bit-level access
        - Depends on host object's _i2c and _address attributes
        - Based on Adafruit Register i2c_bits implementation
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
        初始化位操作描述符

        Args:
            num_bits (int): 位数量
            register_address (int): 寄存器地址
            start_bit (int): 起始位位置
            register_width (int): 寄存器宽度（字节数），默认 1
            lsb_first (bool): 是否 LSB 优先，默认 True

        Returns:
            None

        Raises:
            ValueError: 参数类型或范围错误

        Notes:
            - ISR-safe: 是（仅初始化，不涉及 I/O）

        ==========================================
        Initialize bit operation descriptor.

        Args:
            num_bits (int): Number of bits
            register_address (int): Register address
            start_bit (int): Start bit position
            register_width (int): Register width in bytes, default 1
            lsb_first (bool): LSB first flag, default True

        Returns:
            None

        Raises:
            ValueError: Invalid parameter type or range

        Notes:
            - ISR-safe: Yes (initialization only, no I/O)
        """
        # 参数校验
        if not isinstance(num_bits, int) or num_bits <= 0:
            raise ValueError("num_bits must be positive int, got %s" % num_bits)
        if not isinstance(register_address, int) or register_address < 0:
            raise ValueError("register_address must be non-negative int")
        if not isinstance(start_bit, int) or start_bit < 0:
            raise ValueError("start_bit must be non-negative int")
        if not isinstance(register_width, int) or register_width <= 0:
            raise ValueError("register_width must be positive int")

        # 计算位掩码
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.star_bit = start_bit
        self.lenght = register_width
        self.lsb_first = lsb_first

    def __get__(self, obj, objtype=None) -> int:
        """
        读取寄存器指定位

        Args:
            obj (object): 宿主对象实例
            objtype (type): 宿主对象类型

        Returns:
            int: 读取的位值

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否（涉及 I2C 读操作）
            - 依赖宿主对象的 _i2c 和 _address 属性

        ==========================================
        Read specified bits from register.

        Args:
            obj (object): Host object instance
            objtype (type): Host object type

        Returns:
            int: Read bit value

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No (involves I2C read)
            - Depends on host object's _i2c and _address attributes
        """
        # 读取寄存器原始值
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 字节序转换
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取目标位
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        写入寄存器指定位

        Args:
            obj (object): 宿主对象实例
            value (int): 要写入的位值

        Returns:
            None

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否（涉及 I2C 读写操作）
            - 依赖宿主对象的 _i2c 和 _address 属性
            - 采用读-修改-写模式，保留其他位不变

        ==========================================
        Write specified bits to register.

        Args:
            obj (object): Host object instance
            value (int): Bit value to write

        Returns:
            None

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No (involves I2C read-write)
            - Depends on host object's _i2c and _address attributes
            - Uses read-modify-write pattern to preserve other bits
        """
        # 读取寄存器当前值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 字节序转换
        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清除目标位
        reg &= ~self.bit_mask

        # 设置新值
        value <<= self.star_bit
        reg |= value

        # 转换为字节并写入
        reg = reg.to_bytes(self.lenght, "big")
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    I2C 寄存器结构体操作描述符类

    Attributes:
        format (str): struct 格式字符串
        register (int): 寄存器地址
        lenght (int): 数据长度（字节数）

    Methods:
        __get__(): 读取寄存器并解包
        __set__(): 打包并写入寄存器

    Notes:
        - 用作类属性描述符，自动处理结构体读写
        - 依赖宿主对象的 _i2c 和 _address 属性
        - 基于 Adafruit Register i2c_struct 实现

    ==========================================
    I2C register struct operation descriptor class.

    Attributes:
        format (str): struct format string
        register (int): Register address
        lenght (int): Data length in bytes

    Methods:
        __get__(): Read register and unpack
        __set__(): Pack and write to register

    Notes:
        - Used as class attribute descriptor for automatic struct access
        - Depends on host object's _i2c and _address attributes
        - Based on Adafruit Register i2c_struct implementation
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化结构体操作描述符

        Args:
            register_address (int): 寄存器地址
            form (str): struct 格式字符串（如 "B", "<H", ">I"）

        Returns:
            None

        Raises:
            ValueError: 参数类型或格式错误

        Notes:
            - ISR-safe: 是（仅初始化，不涉及 I/O）

        ==========================================
        Initialize struct operation descriptor.

        Args:
            register_address (int): Register address
            form (str): struct format string (e.g., "B", "<H", ">I")

        Returns:
            None

        Raises:
            ValueError: Invalid parameter type or format

        Notes:
            - ISR-safe: Yes (initialization only, no I/O)
        """
        # 参数校验
        if not isinstance(register_address, int) or register_address < 0:
            raise ValueError("register_address must be non-negative int")
        if not isinstance(form, str) or len(form) == 0:
            raise ValueError("form must be non-empty string")

        self.format = form
        self.register = register_address
        # 计算格式字符串对应的字节长度
        self.lenght = struct.calcsize(form)

    def __get__(self, obj, objtype=None):
        """
        读取寄存器并解包

        Args:
            obj (object): 宿主对象实例
            objtype (type): 宿主对象类型

        Returns:
            int | tuple: 解包后的值（单值返回 int，多值返回 tuple）

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否（涉及 I2C 读操作）
            - 依赖宿主对象的 _i2c 和 _address 属性
            - 长度 ≤2 字节返回单值，>2 字节返回 tuple

        ==========================================
        Read register and unpack.

        Args:
            obj (object): Host object instance
            objtype (type): Host object type

        Returns:
            int | tuple: Unpacked value (single value returns int, multiple values return tuple)

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No (involves I2C read)
            - Depends on host object's _i2c and _address attributes
            - Returns single value for ≤2 bytes, tuple for >2 bytes
        """
        # 读取寄存器数据
        raw_data = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 解包数据
        if self.lenght <= 2:
            # 单值返回
            value = struct.unpack(self.format, memoryview(raw_data))[0]
        else:
            # 多值返回 tuple
            value = struct.unpack(self.format, memoryview(raw_data))

        return value

    def __set__(self, obj, value) -> None:
        """
        打包并写入寄存器

        Args:
            obj (object): 宿主对象实例
            value (int | tuple): 要写入的值

        Returns:
            None

        Raises:
            RuntimeError: I2C 通信失败
            struct.error: 值与格式不匹配

        Notes:
            - ISR-safe: 否（涉及 I2C 写操作）
            - 依赖宿主对象的 _i2c 和 _address 属性

        ==========================================
        Pack and write to register.

        Args:
            obj (object): Host object instance
            value (int | tuple): Value to write

        Returns:
            None

        Raises:
            RuntimeError: I2C communication failed
            struct.error: Value does not match format

        Notes:
            - ISR-safe: No (involves I2C write)
            - Depends on host object's _i2c and _address attributes
        """
        # 打包数据
        mem_value = struct.pack(self.format, value)

        # 写入寄存器
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
