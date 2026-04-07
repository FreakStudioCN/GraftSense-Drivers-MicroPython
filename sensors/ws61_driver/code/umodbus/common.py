# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午4:52
# @Author  : Anonymous
# @File    : common.py
# @Description : Modbus公共模块，包含请求类、异常类以及通用的Modbus功能函数（读写线圈、寄存器等）。
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
from . import functions

# typing not natively supported on MicroPython
from .typing import List, Optional, Tuple, Union

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class Request(object):
    """
    解构通过TCP或串口接收到的请求数据。

    Attributes:
        _itf: 通信接口对象。
        unit_addr (int): 单元地址（从站地址）。
        function (int): 功能码。
        register_addr (int): 寄存器起始地址。
        quantity (int): 寄存器/线圈数量（若适用）。
        data (bytes): 请求携带的数据（写操作时有效）。

    Methods:
        send_response(): 发送响应。
        send_exception(): 发送异常响应。

    Raises:
        ModbusException: 当请求数据不符合Modbus规范时抛出。

    Notes:
        根据功能码不同，解析规则不同：读操作解析数量，写操作解析数据。

    ==========================================
    Deconstruct request data received via TCP or Serial.

    Attributes:
        _itf: Communication interface object.
        unit_addr (int): Unit address (slave address).
        function (int): Function code.
        register_addr (int): Starting register address.
        quantity (int): Number of registers/coils (if applicable).
        data (bytes): Data carried in the request (valid for write operations).

    Methods:
        send_response(): Send a response.
        send_exception(): Send an exception response.

    Raises:
        ModbusException: Raised when request data does not conform to Modbus specification.

    Notes:
        Parsing rules vary by function code: read operations parse quantity, write operations parse data.
    """
    def __init__(self, interface, data: bytearray) -> None:
        """
        初始化请求对象，解析原始数据。

        Args:
            interface: 通信接口对象（需支持 send_response 和 send_exception_response）。
            data (bytearray): 原始请求数据（不含CRC，含单元地址和PDU）。

        Raises:
            ModbusException: 当数据长度、数量或数值不符合规范时抛出。

        ==========================================
        Initialize the request object, parse raw data.

        Args:
            interface: Communication interface object (must support send_response and send_exception_response).
            data (bytearray): Raw request data (without CRC, includes unit address and PDU).

        Raises:
            ModbusException: Raised when data length, quantity or value does not conform to specification.
        """
        self._itf = interface
        self.unit_addr = data[0]
        self.function, self.register_addr = struct.unpack_from('>BH', data, 1)

        if self.function in [Const.READ_COILS, Const.READ_DISCRETE_INPUTS]:
            self.quantity = struct.unpack_from('>H', data, 4)[0]

            if self.quantity < 0x0001 or self.quantity > 0x07D0:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)

            self.data = None
        elif self.function in [Const.READ_HOLDING_REGISTERS, Const.READ_INPUT_REGISTER]:
            self.quantity = struct.unpack_from('>H', data, 4)[0]

            if self.quantity < 0x0001 or self.quantity > 0x007D:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)

            self.data = None
        elif self.function == Const.WRITE_SINGLE_COIL:
            self.quantity = None
            self.data = data[4:6]

            # allowed values: 0x0000 or 0xFF00
            if (self.data[0] not in [0x00, 0xFF]) or self.data[1] != 0x00:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
        elif self.function == Const.WRITE_SINGLE_REGISTER:
            self.quantity = None
            self.data = data[4:6]
            # all values allowed
        elif self.function == Const.WRITE_MULTIPLE_COILS:
            self.quantity = struct.unpack_from('>H', data, 4)[0]
            if self.quantity < 0x0001 or self.quantity > 0x07D0:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
            self.data = data[7:]
            if len(self.data) != ((self.quantity - 1) // 8) + 1:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
        elif self.function == Const.WRITE_MULTIPLE_REGISTERS:
            self.quantity = struct.unpack_from('>H', data, 4)[0]
            if self.quantity < 0x0001 or self.quantity > 0x007B:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
            self.data = data[7:]
            if len(self.data) != self.quantity * 2:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
        else:
            # Not implemented functions
            self.quantity = None
            self.data = data[4:]

    def send_response(self,
                      values: Optional[list] = None,
                      signed: bool = True) -> None:
        """
        通过配置的接口发送响应。

        Args:
            values (Optional[list], optional): 要返回的数据值列表（读操作时使用）。默认为None。
            signed (bool, optional): 是否使用有符号格式。默认为True。

        Notes:
            调用接口的 send_response 方法。

        ==========================================
        Send a response via the configured interface.

        Args:
            values (Optional[list], optional): List of data values to return (for read operations). Defaults to None.
            signed (bool, optional): Whether to use signed format. Defaults to True.

        Notes:
            Calls the interface's send_response method.
        """
        self._itf.send_response(self.unit_addr,
                                self.function,
                                self.register_addr,
                                self.quantity,
                                self.data,
                                values,
                                signed)

    def send_exception(self, exception_code: int) -> None:
        """
        发送异常响应。

        Args:
            exception_code (int): 异常码（如 Const.ILLEGAL_FUNCTION）。

        Notes:
            调用接口的 send_exception_response 方法。

        ==========================================
        Send an exception response.

        Args:
            exception_code (int): The exception code (e.g., Const.ILLEGAL_FUNCTION).

        Notes:
            Calls the interface's send_exception_response method.
        """
        self._itf.send_exception_response(self.unit_addr,
                                          self.function,
                                          exception_code)


class ModbusException(Exception):
    """
    用于表示Modbus错误的异常类。

    Attributes:
        function_code (int): 导致异常的功能码。
        exception_code (int): Modbus异常码。

    ==========================================
    Exception for signaling Modbus errors.

    Attributes:
        function_code (int): The function code that caused the exception.
        exception_code (int): The Modbus exception code.
    """
    def __init__(self, function_code: int, exception_code: int) -> None:
        """
        初始化Modbus异常。

        Args:
            function_code (int): 引发异常的功能码。
            exception_code (int): Modbus异常码。

        ==========================================
        Initialize the Modbus exception.

        Args:
            function_code (int): The function code that caused the exception.
            exception_code (int): The Modbus exception code.
        """
        self.function_code = function_code
        self.exception_code = exception_code


class CommonModbusFunctions(object):
    """
    公共Modbus功能函数类，封装了所有标准的Modbus客户端操作。

    提供了读取/写入线圈、离散输入、保持寄存器、输入寄存器的方法。
    所有方法都通过 _send_receive 发送PDU并验证响应。

    Methods:
        read_coils(): 读取线圈。
        read_discrete_inputs(): 读取离散输入。
        read_holding_registers(): 读取保持寄存器。
        read_input_registers(): 读取输入寄存器。
        write_single_coil(): 写单个线圈。
        write_single_register(): 写单个寄存器。
        write_multiple_coils(): 写多个线圈。
        write_multiple_registers(): 写多个寄存器。

    Notes:
        子类需要实现 _send_receive 方法（如 Serial 或 TCP）。

    ==========================================
    Common Modbus functions class, encapsulates all standard Modbus client operations.

    Provides methods for reading/writing coils, discrete inputs, holding registers, input registers.
    All methods send PDU via _send_receive and validate the response.

    Methods:
        read_coils(): Read coils.
        read_discrete_inputs(): Read discrete inputs.
        read_holding_registers(): Read holding registers.
        read_input_registers(): Read input registers.
        write_single_coil(): Write single coil.
        write_single_register(): Write single register.
        write_multiple_coils(): Write multiple coils.
        write_multiple_registers(): Write multiple registers.

    Notes:
        Subclasses must implement the _send_receive method (e.g., Serial or TCP).
    """
    def __init__(self):
        """
        初始化公共Modbus功能函数类。

        ==========================================
        Initialize the common Modbus functions class.
        """
        pass

    def read_coils(self,
                   slave_addr: int,
                   starting_addr: int,
                   coil_qty: int) -> List[bool]:
        """
        读取线圈（COILS）。

        Args:
            slave_addr (int): 从站地址。
            starting_addr (int): 线圈起始地址。
            coil_qty (int): 要读取的线圈数量。

        Returns:
            List[bool]: 读取的线圈状态列表。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.READ_COILS (0x01)。

        ==========================================
        Read coils (COILS).

        Args:
            slave_addr (int): The slave address.
            starting_addr (int): The coil starting address.
            coil_qty (int): The amount of coils to read.

        Returns:
            List[bool]: List of read coil states.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.READ_COILS (0x01).
        """
        modbus_pdu = functions.read_coils(starting_address=starting_addr,
                                          quantity=coil_qty)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=True)

        status_pdu = functions.bytes_to_bool(byte_list=response,
                                             bit_qty=coil_qty)

        return status_pdu

    def read_discrete_inputs(self,
                             slave_addr: int,
                             starting_addr: int,
                             input_qty: int) -> List[bool]:
        """
        读取离散输入（ISTS）。

        Args:
            slave_addr (int): 从站地址。
            starting_addr (int): 离散输入起始地址。
            input_qty (int): 要读取的离散输入数量。

        Returns:
            List[bool]: 读取的离散输入状态列表。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.READ_DISCRETE_INPUTS (0x02)。

        ==========================================
        Read discrete inputs (ISTS).

        Args:
            slave_addr (int): The slave address.
            starting_addr (int): The discrete input starting address.
            input_qty (int): The amount of discrete inputs to read.

        Returns:
            List[bool]: List of read discrete input states.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.READ_DISCRETE_INPUTS (0x02).
        """
        modbus_pdu = functions.read_discrete_inputs(
            starting_address=starting_addr,
            quantity=input_qty)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=True)

        status_pdu = functions.bytes_to_bool(byte_list=response,
                                             bit_qty=input_qty)

        return status_pdu

    def read_holding_registers(self,
                               slave_addr: int,
                               starting_addr: int,
                               register_qty: int,
                               signed: bool = True) -> Tuple[int, ...]:
        """
        读取保持寄存器（HREGS）。

        Args:
            slave_addr (int): 从站地址。
            starting_addr (int): 保持寄存器起始地址。
            register_qty (int): 要读取的寄存器数量。
            signed (bool, optional): 是否使用有符号整数。默认为True。

        Returns:
            Tuple[int, ...]: 读取的寄存器值元组。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.READ_HOLDING_REGISTERS (0x03)。

        ==========================================
        Read holding registers (HREGS).

        Args:
            slave_addr (int): The slave address.
            starting_addr (int): The holding register starting address.
            register_qty (int): The amount of holding registers to read.
            signed (bool, optional): Whether to use signed integers. Defaults to True.

        Returns:
            Tuple[int, ...]: Tuple of read register values.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.READ_HOLDING_REGISTERS (0x03).
        """
        modbus_pdu = functions.read_holding_registers(
            starting_address=starting_addr,
            quantity=register_qty)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=True)

        register_value = functions.to_short(byte_array=response, signed=signed)

        return register_value

    def read_input_registers(self,
                             slave_addr: int,
                             starting_addr: int,
                             register_qty: int,
                             signed: bool = True) -> Tuple[int, ...]:
        """
        读取输入寄存器（IREGS）。

        Args:
            slave_addr (int): 从站地址。
            starting_addr (int): 输入寄存器起始地址。
            register_qty (int): 要读取的寄存器数量。
            signed (bool, optional): 是否使用有符号整数。默认为True。

        Returns:
            Tuple[int, ...]: 读取的寄存器值元组。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.READ_INPUT_REGISTER (0x04)。

        ==========================================
        Read input registers (IREGS).

        Args:
            slave_addr (int): The slave address.
            starting_addr (int): The input register starting address.
            register_qty (int): The amount of input registers to read.
            signed (bool, optional): Whether to use signed integers. Defaults to True.

        Returns:
            Tuple[int, ...]: Tuple of read register values.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.READ_INPUT_REGISTER (0x04).
        """
        modbus_pdu = functions.read_input_registers(
            starting_address=starting_addr,
            quantity=register_qty)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=True)

        register_value = functions.to_short(byte_array=response, signed=signed)

        return register_value

    def write_single_coil(self,
                          slave_addr: int,
                          output_address: int,
                          output_value: Union[int, bool]) -> bool:
        """
        写单个线圈。

        Args:
            slave_addr (int): 从站地址。
            output_address (int): 线圈地址。
            output_value (Union[int, bool]): 输出值（True/1 或 False/0）。

        Returns:
            bool: 操作成功返回True，否则False。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.WRITE_SINGLE_COIL (0x05)。

        ==========================================
        Write a single coil.

        Args:
            slave_addr (int): The slave address.
            output_address (int): The coil address.
            output_value (Union[int, bool]): Output value (True/1 or False/0).

        Returns:
            bool: True if operation succeeded, False otherwise.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.WRITE_SINGLE_COIL (0x05).
        """
        modbus_pdu = functions.write_single_coil(output_address=output_address,
                                                 output_value=output_value)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_SINGLE_COIL,
            address=output_address,
            value=output_value,
            signed=False)

        return operation_status

    def write_single_register(self,
                              slave_addr: int,
                              register_address: int,
                              register_value: int,
                              signed: bool = True) -> bool:
        """
        写单个寄存器。

        Args:
            slave_addr (int): 从站地址。
            register_address (int): 寄存器地址。
            register_value (int): 要写入的值。
            signed (bool, optional): 是否使用有符号格式。默认为True。

        Returns:
            bool: 操作成功返回True，否则False。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.WRITE_SINGLE_REGISTER (0x06)。

        ==========================================
        Write a single register.

        Args:
            slave_addr (int): The slave address.
            register_address (int): The register address.
            register_value (int): The value to write.
            signed (bool, optional): Whether to use signed format. Defaults to True.

        Returns:
            bool: True if operation succeeded, False otherwise.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.WRITE_SINGLE_REGISTER (0x06).
        """
        modbus_pdu = functions.write_single_register(
            register_address=register_address,
            register_value=register_value,
            signed=signed)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_SINGLE_REGISTER,
            address=register_address,
            value=register_value,
            signed=signed)

        return operation_status

    def write_multiple_coils(self,
                             slave_addr: int,
                             starting_address: int,
                             output_values: List[Union[int, bool]]) -> bool:
        """
        写多个线圈。

        Args:
            slave_addr (int): 从站地址。
            starting_address (int): 起始线圈地址。
            output_values (List[Union[int, bool]]): 线圈值列表。

        Returns:
            bool: 操作成功返回True，否则False。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.WRITE_MULTIPLE_COILS (0x0F)。

        ==========================================
        Write multiple coils.

        Args:
            slave_addr (int): The slave address.
            starting_address (int): The starting coil address.
            output_values (List[Union[int, bool]]): List of coil values.

        Returns:
            bool: True if operation succeeded, False otherwise.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.WRITE_MULTIPLE_COILS (0x0F).
        """
        modbus_pdu = functions.write_multiple_coils(
            starting_address=starting_address,
            value_list=output_values)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_MULTIPLE_COILS,
            address=starting_address,
            quantity=len(output_values))

        return operation_status

    def write_multiple_registers(self,
                                 slave_addr: int,
                                 starting_address: int,
                                 register_values: List[int],
                                 signed: bool = True) -> bool:
        """
        写多个寄存器。

        Args:
            slave_addr (int): 从站地址。
            starting_address (int): 起始寄存器地址。
            register_values (List[int]): 寄存器值列表。
            signed (bool, optional): 是否使用有符号格式。默认为True。

        Returns:
            bool: 操作成功返回True，否则False。

        Raises:
            OSError: 通信错误或CRC错误。
            ValueError: 响应验证失败或从站返回异常。

        Notes:
            功能码为 Const.WRITE_MULTIPLE_REGISTERS (0x10)。

        ==========================================
        Write multiple registers.

        Args:
            slave_addr (int): The slave address.
            starting_address (int): The starting register address.
            register_values (List[int]): List of register values.
            signed (bool, optional): Whether to use signed format. Defaults to True.

        Returns:
            bool: True if operation succeeded, False otherwise.

        Raises:
            OSError: Communication error or CRC error.
            ValueError: Response validation failed or slave returned exception.

        Notes:
            Function code is Const.WRITE_MULTIPLE_REGISTERS (0x10).
        """
        modbus_pdu = functions.write_multiple_registers(
            starting_address=starting_address,
            register_values=register_values,
            signed=signed)

        response = self._send_receive(slave_addr=slave_addr,
                                      modbus_pdu=modbus_pdu,
                                      count=False)

        if response is None:
            return False

        operation_status = functions.validate_resp_data(
            data=response,
            function_code=Const.WRITE_MULTIPLE_REGISTERS,
            address=starting_address,
            quantity=len(register_values),
            signed=signed
        )

        return operation_status

# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================