# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午4:52
# @Author  : Anonymous
# @File    : functions.py
# @Description : Modbus协议数据单元(PDU)构建与解析函数，包括读取/写入线圈、寄存器，数据格式转换等。
# @License : MIT
__version__ = "0.1.0"
__author__ = "Anonymous"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# system packages
import struct

# custom packages
from . import const as Const

# typing not natively supported on MicroPython
from .typing import List, Optional, Union

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def read_coils(starting_address: int, quantity: int) -> bytes:
    """
    创建读取线圈的Modbus协议数据单元(PDU)。

    Args:
        starting_address (int): 起始地址。
        quantity (int): 线圈数量，范围1-2000。

    Returns:
        bytes: 打包后的Modbus消息。

    Raises:
        ValueError: 如果quantity超出有效范围。

    Notes:
        功能码为 Const.READ_COILS (0x01)。

    ==========================================
    Create Modbus Protocol Data Unit for reading coils.

    Args:
        starting_address (int): The starting address.
        quantity (int): Quantity of coils, range 1-2000.

    Returns:
        bytes: Packed Modbus message.

    Raises:
        ValueError: If quantity is out of valid range.

    Notes:
        Function code is Const.READ_COILS (0x01).
    """
    if not (1 <= quantity <= 2000):
        raise ValueError("Invalid number of coils")

    return struct.pack(">BHH", Const.READ_COILS, starting_address, quantity)


def read_discrete_inputs(starting_address: int, quantity: int) -> bytes:
    """
    创建读取离散输入的Modbus协议数据单元(PDU)。

    Args:
        starting_address (int): 起始地址。
        quantity (int): 离散输入数量，范围1-2000。

    Returns:
        bytes: 打包后的Modbus消息。

    Raises:
        ValueError: 如果quantity超出有效范围。

    Notes:
        功能码为 Const.READ_DISCRETE_INPUTS (0x02)。

    ==========================================
    Create Modbus Protocol Data Unit for reading discrete inputs.

    Args:
        starting_address (int): The starting address.
        quantity (int): Quantity of discrete inputs, range 1-2000.

    Returns:
        bytes: Packed Modbus message.

    Raises:
        ValueError: If quantity is out of valid range.

    Notes:
        Function code is Const.READ_DISCRETE_INPUTS (0x02).
    """
    if not (1 <= quantity <= 2000):
        raise ValueError("Invalid number of discrete inputs")

    return struct.pack(">BHH", Const.READ_DISCRETE_INPUTS, starting_address, quantity)


def read_holding_registers(starting_address: int, quantity: int) -> bytes:
    """
    创建读取保持寄存器的Modbus协议数据单元(PDU)。

    Args:
        starting_address (int): 起始地址。
        quantity (int): 寄存器数量，范围1-125。

    Returns:
        bytes: 打包后的Modbus消息。

    Raises:
        ValueError: 如果quantity超出有效范围。

    Notes:
        功能码为 Const.READ_HOLDING_REGISTERS (0x03)。

    ==========================================
    Create Modbus Protocol Data Unit for reading holding registers.

    Args:
        starting_address (int): The starting address.
        quantity (int): Quantity of registers, range 1-125.

    Returns:
        bytes: Packed Modbus message.

    Raises:
        ValueError: If quantity is out of valid range.

    Notes:
        Function code is Const.READ_HOLDING_REGISTERS (0x03).
    """
    if not (1 <= quantity <= 125):
        raise ValueError("Invalid number of holding registers")

    return struct.pack(">BHH", Const.READ_HOLDING_REGISTERS, starting_address, quantity)


def read_input_registers(starting_address: int, quantity: int) -> bytes:
    """
    创建读取输入寄存器的Modbus协议数据单元(PDU)。

    Args:
        starting_address (int): 起始地址。
        quantity (int): 寄存器数量，范围1-125。

    Returns:
        bytes: 打包后的Modbus消息。

    Raises:
        ValueError: 如果quantity超出有效范围。

    Notes:
        功能码为 Const.READ_INPUT_REGISTER (0x04)。

    ==========================================
    Create Modbus Protocol Data Unit for reading input registers.

    Args:
        starting_address (int): The starting address.
        quantity (int): Quantity of registers, range 1-125.

    Returns:
        bytes: Packed Modbus message.

    Raises:
        ValueError: If quantity is out of valid range.

    Notes:
        Function code is Const.READ_INPUT_REGISTER (0x04).
    """
    if not (1 <= quantity <= 125):
        raise ValueError("Invalid number of input registers")

    return struct.pack(">BHH", Const.READ_INPUT_REGISTER, starting_address, quantity)


def write_single_coil(output_address: int, output_value: Union[int, bool]) -> bytes:
    """
    创建写单个线圈的Modbus协议数据单元(PDU)。

    Args:
        output_address (int): 线圈地址。
        output_value (Union[int, bool]): 输出值，True/1对应0xFF00，False/0对应0x0000。

    Returns:
        bytes: 打包后的Modbus消息。

    Raises:
        ValueError: 如果output_value不是合法值。

    Notes:
        功能码为 Const.WRITE_SINGLE_COIL (0x05)。根据Modbus规范，True会被转换为0xFF00。

    ==========================================
    Create Modbus message to update single coil.

    Args:
        output_address (int): The output address.
        output_value (Union[int, bool]): Output value, True/1 maps to 0xFF00, False/0 maps to 0x0000.

    Returns:
        bytes: Packed Modbus message.

    Raises:
        ValueError: If output_value is illegal.

    Notes:
        Function code is Const.WRITE_SINGLE_COIL (0x05). True is converted to 0xFF00 per Modbus spec.
    """
    if output_value not in [0x0000, 0xFF00, False, True, 0, 1]:
        raise ValueError("Illegal coil value")

    if output_value not in [0x0000, 0xFF00]:
        if output_value:
            output_value = 0xFF00
        else:
            output_value = 0x0000

    return struct.pack(">BHH", Const.WRITE_SINGLE_COIL, output_address, output_value)


def write_single_register(register_address: int, register_value: int, signed: bool = True) -> bytes:
    """
    创建写单个寄存器的Modbus协议数据单元(PDU)。

    Args:
        register_address (int): 寄存器地址。
        register_value (int): 要写入的值。
        signed (bool, optional): 是否使用有符号格式。默认为True。

    Returns:
        bytes: 打包后的Modbus消息。

    Notes:
        功能码为 Const.WRITE_SINGLE_REGISTER (0x06)。

    ==========================================
    Create Modbus message to write a single register.

    Args:
        register_address (int): The register address.
        register_value (int): Value to write.
        signed (bool, optional): Whether to use signed format. Defaults to True.

    Returns:
        bytes: Packed Modbus message.

    Notes:
        Function code is Const.WRITE_SINGLE_REGISTER (0x06).
    """
    fmt = "h" if signed else "H"

    return struct.pack(">BH" + fmt, Const.WRITE_SINGLE_REGISTER, register_address, register_value)


def write_multiple_coils(starting_address: int, value_list: List[Union[int, bool]]) -> bytes:
    """
    创建写多个线圈的Modbus协议数据单元(PDU)。

    Args:
        starting_address (int): 起始地址。
        value_list (List[Union[int, bool]]): 线圈值列表，每个元素为0/1或False/True。

    Returns:
        bytes: 打包后的Modbus消息。

    Raises:
        ValueError: 如果value_list长度不在1-2000之间。

    Notes:
        功能码为 Const.WRITE_MULTIPLE_COILS (0x0F)。数据按位打包为字节。

    ==========================================
    Create Modbus message to write multiple coils.

    Args:
        starting_address (int): The starting address.
        value_list (List[Union[int, bool]]): List of coil values, each 0/1 or False/True.

    Returns:
        bytes: Packed Modbus message.

    Raises:
        ValueError: If length of value_list is not between 1 and 2000.

    Notes:
        Function code is Const.WRITE_MULTIPLE_COILS (0x0F). Data is packed into bytes bitwise.
    """
    if not (1 <= len(value_list) <= 0x07B0):
        raise ValueError("Invalid quantity of outputs")

    sectioned_list = [value_list[i : i + 8] for i in range(0, len(value_list), 8)]  # noqa: E501

    output_value = []
    for index, byte in enumerate(sectioned_list):
        # see https://github.com/brainelectronics/micropython-modbus/issues/22
        # output = sum(v << i for i, v in enumerate(byte))
        output = 0
        for bit in byte:
            output = (output << 1) | bit
        output_value.append(output)

    fmt = "B" * len(output_value)
    quantity = len(value_list)
    byte_count = quantity // 8
    if quantity % 8:
        byte_count += 1

    return struct.pack(">BHHB" + fmt, Const.WRITE_MULTIPLE_COILS, starting_address, quantity, byte_count, *output_value)


def write_multiple_registers(starting_address: int, register_values: List[int], signed: bool = True) -> bytes:
    """
    创建写多个寄存器的Modbus协议数据单元(PDU)。

    Args:
        starting_address (int): 起始地址。
        register_values (List[int]): 寄存器值列表。
        signed (bool, optional): 是否使用有符号格式。默认为True。

    Returns:
        bytes: 打包后的Modbus消息。

    Raises:
        ValueError: 如果register_values长度不在1-123之间。

    Notes:
        功能码为 Const.WRITE_MULTIPLE_REGISTERS (0x10)。每个寄存器占2字节。

    ==========================================
    Create Modbus message to write multiple registers.

    Args:
        starting_address (int): The starting address.
        register_values (List[int]): List of register values.
        signed (bool, optional): Whether to use signed format. Defaults to True.

    Returns:
        bytes: Packed Modbus message.

    Raises:
        ValueError: If length of register_values is not between 1 and 123.

    Notes:
        Function code is Const.WRITE_MULTIPLE_REGISTERS (0x10). Each register occupies 2 bytes.
    """
    if not (1 <= len(register_values) <= 123):
        raise ValueError("Invalid number of registers")

    quantity = len(register_values)
    byte_count = quantity * 2
    fmt = ("h" if signed else "H") * quantity

    return struct.pack(">BHHB" + fmt, Const.WRITE_MULTIPLE_REGISTERS, starting_address, quantity, byte_count, *register_values)


def validate_resp_data(data: bytes, function_code: int, address: int, value: int = None, quantity: int = None, signed: bool = True) -> bool:
    """
    验证Modbus响应数据是否与请求匹配。

    Args:
        data (bytes): 响应数据（不含地址和CRC）。
        function_code (int): 请求的功能码。
        address (int): 请求的地址。
        value (int, optional): 请求的值（写单个寄存器/线圈时使用）。
        quantity (int, optional): 请求的数量（写多个寄存器/线圈时使用）。
        signed (bool, optional): 是否使用有符号格式。默认为True。

    Returns:
        bool: 验证通过返回True，否则False。

    Notes:
        对于写单个线圈，响应中的值会被转换为bool进行比较。

    ==========================================
    Validate the response data against the request.

    Args:
        data (bytes): Response data (excluding address and CRC).
        function_code (int): Requested function code.
        address (int): Requested address.
        value (int, optional): Requested value (for single write).
        quantity (int, optional): Requested quantity (for multiple write).
        signed (bool, optional): Whether to use signed format. Defaults to True.

    Returns:
        bool: True if valid, False otherwise.

    Notes:
        For write single coil, response value is converted to bool for comparison.
    """
    fmt = ">H" + ("h" if signed else "H")

    if function_code in [Const.WRITE_SINGLE_COIL, Const.WRITE_SINGLE_REGISTER]:
        resp_addr, resp_value = struct.unpack(fmt, data)

        # if bool(True) or int(1) is used as "output_value" of
        # "write_single_coil" it will be internally converted to int(0xFF00),
        # see Modbus specification, which is actually int(65280).
        # Due to the non binary, but real value comparison of "value" and
        # "resp_value", it would never match without the next two lines
        # see #21
        if function_code == Const.WRITE_SINGLE_COIL:
            resp_value = bool(resp_value)
            value = bool(value)

        if (address == resp_addr) and (value == resp_value):
            return True
    elif function_code in [Const.WRITE_MULTIPLE_COILS, Const.WRITE_MULTIPLE_REGISTERS]:
        resp_addr, resp_qty = struct.unpack(fmt, data)

        if (address == resp_addr) and (quantity == resp_qty):
            return True

    return False


def response(
    function_code: int,
    request_register_addr: int,
    request_register_qty: int,
    request_data: list,
    value_list: Optional[list] = None,
    signed: bool = True,
) -> bytes:
    """
    构造Modbus响应协议数据单元(PDU)。

    Args:
        function_code (int): 功能码。
        request_register_addr (int): 请求的寄存器起始地址。
        request_register_qty (int): 请求的寄存器数量。
        request_data (list): 请求携带的原始数据（用于写操作响应）。
        value_list (Optional[list], optional): 要返回的数据值列表（用于读操作响应）。默认为None。
        signed (bool, optional): 是否使用有符号格式。默认为True。

    Returns:
        bytes: 打包后的响应PDU。

    Raises:
        ValueError: 对于读保持寄存器/输入寄存器，如果value_list长度无效。

    Notes:
        根据功能码不同，响应格式不同。支持读线圈/离散输入、读寄存器、写单/多线圈/寄存器。

    ==========================================
    Construct a Modbus response Protocol Data Unit (PDU).

    Args:
        function_code (int): Function code.
        request_register_addr (int): Requested starting register address.
        request_register_qty (int): Requested register quantity.
        request_data (list): Raw data from request (for write response).
        value_list (Optional[list], optional): Data values to return (for read response). Defaults to None.
        signed (bool, optional): Whether to use signed format. Defaults to True.

    Returns:
        bytes: Packed response PDU.

    Raises:
        ValueError: If value_list length is invalid for read holding/input registers.

    Notes:
        Response format varies by function code. Supports read coils/discrete inputs,
        read registers, write single/multiple coils/registers.
    """
    if function_code in [Const.READ_COILS, Const.READ_DISCRETE_INPUTS]:
        sectioned_list = [value_list[i : i + 8] for i in range(0, len(value_list), 8)]  # noqa: E501

        output_value = []
        for index, byte in enumerate(sectioned_list):
            # see https://github.com/brainelectronics/micropython-modbus/issues/22
            # output = sum(v << i for i, v in enumerate(byte))
            # see https://github.com/brainelectronics/micropython-modbus/issues/38
            output = 0
            for bit in byte:
                output = (output << 1) | bit
            output_value.append(output)

        fmt = "B" * len(output_value)
        return struct.pack(">BB" + fmt, function_code, ((len(value_list) - 1) // 8) + 1, *output_value)

    elif function_code in [Const.READ_HOLDING_REGISTERS, Const.READ_INPUT_REGISTER]:
        quantity = len(value_list)

        if not (0x0001 <= quantity <= 0x007D):
            raise ValueError("invalid number of registers")

        if signed is True or signed is False:
            fmt = ("h" if signed else "H") * quantity
        else:
            fmt = ""
            for s in signed:
                fmt += "h" if s else "H"

        return struct.pack(">BB" + fmt, function_code, quantity * 2, *value_list)

    elif function_code in [Const.WRITE_SINGLE_COIL, Const.WRITE_SINGLE_REGISTER]:
        return struct.pack(">BHBB", function_code, request_register_addr, *request_data)

    elif function_code in [Const.WRITE_MULTIPLE_COILS, Const.WRITE_MULTIPLE_REGISTERS]:
        return struct.pack(">BHH", function_code, request_register_addr, request_register_qty)


def exception_response(function_code: int, exception_code: int) -> bytes:
    """
    创建Modbus异常响应PDU。

    Args:
        function_code (int): 原始请求的功能码。
        exception_code (int): 异常码（如Const.ILLEGAL_FUNCTION等）。

    Returns:
        bytes: 打包后的异常响应消息。

    Notes:
        响应中的功能码 = 原始功能码 + Const.ERROR_BIAS (0x80)。

    ==========================================
    Create Modbus exception response PDU.

    Args:
        function_code (int): Original request function code.
        exception_code (int): Exception code (e.g., Const.ILLEGAL_FUNCTION).

    Returns:
        bytes: Packed exception response message.

    Notes:
        Function code in response = original function code + Const.ERROR_BIAS (0x80).
    """
    return struct.pack(">BB", Const.ERROR_BIAS + function_code, exception_code)


def bytes_to_bool(byte_list: bytes, bit_qty: Optional[int] = 1) -> List[bool]:
    """
    将字节转换为布尔值列表。

    Args:
        byte_list (bytes): 输入字节序列。
        bit_qty (Optional[int], optional): 要提取的位数，默认为1。如果大于8，则按字节处理。

    Returns:
        List[bool]: 布尔值列表，每个bool对应一个位（MSB优先）。

    Notes:
        每个字节被格式化为指定位数的二进制字符串，然后转换为bool列表。
        由于MicroPython缺少字符串格式化关键字支持，使用字符串拼接方式。

    ==========================================
    Convert bytes to list of boolean values.

    Args:
        byte_list (bytes): Input byte sequence.
        bit_qty (Optional[int], optional): Number of bits to extract, defaults to 1. If >8, processed per byte.

    Returns:
        List[bool]: List of booleans, each representing a bit (MSB first).

    Notes:
        Each byte is formatted as a binary string with specified width, then converted to bool list.
        Uses string concatenation due to lack of keyword support in MicroPython formatting.
    """
    bool_list = []

    for index, byte in enumerate(byte_list):
        this_qty = bit_qty

        if this_qty >= 8:
            this_qty = 8

        # evil hack for missing keyword support in MicroPython format()
        fmt = "{:0" + str(this_qty) + "b}"

        bool_list.extend([bool(int(x)) for x in fmt.format(byte)])

        bit_qty -= 8

    return bool_list


def to_short(byte_array: bytes, signed: bool = True) -> bytes:
    """
    将字节数组转换为整数元组（short类型）。

    Args:
        byte_array (bytes): 输入字节数组（长度应为偶数）。
        signed (bool, optional): 是否使用有符号整数。默认为True。

    Returns:
        bytes: 解包后的整数元组（实际返回struct.unpack的结果，是一个元组）。

    Notes:
        每2字节解包为一个short。大端字节序。

    ==========================================
    Convert bytes to tuple of integer values (short type).

    Args:
        byte_array (bytes): Input byte array (length must be even).
        signed (bool, optional): Whether to use signed integers. Defaults to True.

    Returns:
        bytes: Unpacked tuple of integers (result of struct.unpack, actually a tuple).

    Notes:
        Each 2 bytes unpack to one short. Big-endian byte order.
    """
    response_quantity = int(len(byte_array) / 2)
    fmt = ">" + (("h" if signed else "H") * response_quantity)

    return struct.unpack(fmt, byte_array)


def float_to_bin(num: float) -> bin:
    """
    将浮点数转换为二进制字符串（IEEE 754单精度）。

    Args:
        num (float): 输入浮点数。

    Returns:
        bin: 32位二进制字符串（实际返回str类型）。

    Notes:
        由于MicroPython缺少zfill方法，使用格式化填充前导零。

    ==========================================
    Convert floating point value to binary string (IEEE 754 single precision).

    Args:
        num (float): Input float.

    Returns:
        bin: 32-bit binary string (actually returns str).

    Notes:
        Uses formatting to pad leading zeros due to lack of zfill in MicroPython.
    """
    # no "zfill" available in MicroPython
    # return bin(struct.unpack('!I', struct.pack('!f', num))[0])[2:].zfill(32)

    return "{:0>{w}}".format(bin(struct.unpack("!I", struct.pack("!f", num))[0])[2:], w=32)


def bin_to_float(binary: str) -> float:
    """
    将二进制字符串转换为浮点数（IEEE 754单精度）。

    Args:
        binary (str): 32位二进制字符串。

    Returns:
        float: 转换后的浮点数。

    Notes:
        先转换为整数，再按IEEE 754格式解包为浮点数。

    ==========================================
    Convert binary string to floating point value (IEEE 754 single precision).

    Args:
        binary (str): 32-bit binary string.

    Returns:
        float: Converted floating point value.

    Notes:
        Converts to integer first, then unpacks as float per IEEE 754 format.
    """
    return struct.unpack("!f", struct.pack("!I", int(binary, 2)))[0]


def int_to_bin(num: int) -> str:
    """
    将整数转换为二进制字符串（无前导零填充）。

    Args:
        num (int): 输入整数。

    Returns:
        str: 二进制表示字符串。

    ==========================================
    Convert integer to binary string (no leading zero padding).

    Args:
        num (int): Input integer.

    Returns:
        str: Binary representation string.
    """
    return "{0:b}".format(num)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
