# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午4:52
# @Author  : Anonymous
# @File    : main.py
# @Description : Modbus寄存器抽象类，用于管理线圈、保持寄存器、离散输入和输入寄存器。
# @License : MIT

__version__ = "0.1.0"
__author__ = "Anonymous"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# system packages
import time

# custom packages
from . import functions
from . import const as Const
from .common import Request

# typing not natively supported on MicroPython
from .typing import Callable, dict_keys, List, Optional, Union

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Modbus(object):
    """
    Modbus寄存器抽象类，提供对线圈、保持寄存器、离散输入和输入寄存器的统一管理。
    支持添加、删除、读取和写入寄存器值，并记录被外部修改的寄存器。

    Attributes:
        _itf (Callable): 底层接口抽象，用于获取请求和发送响应。
        _addr_list (List[int]): 本设备支持的单元地址列表。
        _available_register_types (list): 支持的寄存器类型列表。
        _register_dict (dict): 存储所有寄存器配置的字典。
        _default_vals (dict): 每种寄存器类型的默认值。
        _changeable_register_types (list): 允许被外部修改的寄存器类型。
        _changed_registers (dict): 存储被外部修改过的寄存器及其时间戳。

    Methods:
        process(): 处理接收到的Modbus请求。
        add_coil(): 添加线圈。
        remove_coil(): 移除线圈。
        set_coil(): 设置线圈值。
        get_coil(): 获取线圈值。
        add_hreg(): 添加保持寄存器。
        remove_hreg(): 移除保持寄存器。
        set_hreg(): 设置保持寄存器值。
        get_hreg(): 获取保持寄存器值。
        add_ist(): 添加离散输入。
        remove_ist(): 移除离散输入。
        set_ist(): 设置离散输入值。
        get_ist(): 获取离散输入值。
        add_ireg(): 添加输入寄存器。
        remove_ireg(): 移除输入寄存器。
        set_ireg(): 设置输入寄存器值。
        get_ireg(): 获取输入寄存器值。
        setup_registers(): 批量配置寄存器。

    Notes:
        线圈和离散输入的值类型为 bool 或 List[bool]。
        保持寄存器和输入寄存器的值类型为 int 或 List[int]。
        仅线圈和保持寄存器可被外部修改，修改记录可通过 changed_registers 属性获取。

    ==========================================
    Modbus register abstraction class providing unified management of coils,
    holding registers, discrete inputs and input registers.
    Supports adding, removing, reading and writing register values,
    and records externally modified registers.

    Attributes:
        _itf (Callable): Underlying interface abstraction for request and response.
        _addr_list (List[int]): List of supported unit addresses.
        _available_register_types (list): List of supported register types.
        _register_dict (dict): Dictionary storing all register configurations.
        _default_vals (dict): Default value for each register type.
        _changeable_register_types (list): Register types that can be externally modified.
        _changed_registers (dict): Stores externally modified registers with timestamps.

    Methods:
        process(): Process incoming Modbus requests.
        add_coil(): Add a coil.
        remove_coil(): Remove a coil.
        set_coil(): Set coil value.
        get_coil(): Get coil value.
        add_hreg(): Add a holding register.
        remove_hreg(): Remove a holding register.
        set_hreg(): Set holding register value.
        get_hreg(): Get holding register value.
        add_ist(): Add a discrete input.
        remove_ist(): Remove a discrete input.
        set_ist(): Set discrete input value.
        get_ist(): Get discrete input value.
        add_ireg(): Add an input register.
        remove_ireg(): Remove an input register.
        set_ireg(): Set input register value.
        get_ireg(): Get input register value.
        setup_registers(): Batch configure registers.

    Notes:
        Coil and discrete input values are bool or List[bool].
        Holding and input register values are int or List[int].
        Only coils and holding registers can be externally modified;
        modification records can be accessed via changed_registers property.
    """

    def __init__(self, itf, addr_list: List[int]) -> None:
        """
        初始化Modbus寄存器抽象类。

        Args:
            itf (Callable): 底层接口抽象，需提供 get_request 和 send_response 等方法。
            addr_list (List[int]): 本设备支持的Modbus单元地址列表。

        Notes:
            内部初始化所有寄存器类型的空字典，并设置默认值和变更记录字典。

        ==========================================
        Initialize the Modbus register abstraction class.

        Args:
            itf (Callable): Underlying interface abstraction providing get_request and send_response methods.
            addr_list (List[int]): List of Modbus unit addresses supported by this device.

        Notes:
            Initializes empty dictionaries for all register types, default values and change records.
        """
        self._itf = itf
        self._addr_list = addr_list

        # modbus register types with their default value
        self._available_register_types = ["COILS", "HREGS", "IREGS", "ISTS"]
        self._register_dict = dict()
        for reg_type in self._available_register_types:
            self._register_dict[reg_type] = dict()
        self._default_vals = dict(zip(self._available_register_types, [False, 0, 0, False]))

        # registers which can be set by remote device
        self._changeable_register_types = ["COILS", "HREGS"]
        self._changed_registers = dict()
        for reg_type in self._changeable_register_types:
            self._changed_registers[reg_type] = dict()

    def process(self) -> bool:
        """
        处理接收到的Modbus请求，根据功能码分发到读或写处理。

        Returns:
            bool: 成功处理请求返回True，否则返回False。

        Notes:
            如果请求的功能码无效，会发送异常响应。仅支持线圈、离散输入、保持寄存器和输入寄存器的读写操作。

        ==========================================
        Process incoming Modbus requests, dispatch to read or write handler based on function code.

        Returns:
            bool: True if request processed successfully, False otherwise.

        Notes:
            Sends exception response for invalid function codes. Only supports read/write for coils,
            discrete inputs, holding registers and input registers.
        """
        reg_type = None
        req_type = None

        request = self._itf.get_request(unit_addr_list=self._addr_list, timeout=0)
        if request is None:
            return False

        if request.function == Const.READ_COILS:
            # Coils (setter+getter) [0, 1]
            # function 01 - read single register
            reg_type = "COILS"
            req_type = "READ"
        elif request.function == Const.READ_DISCRETE_INPUTS:
            # Ists (only getter) [0, 1]
            # function 02 - read input status (discrete inputs/digital input)
            reg_type = "ISTS"
            req_type = "READ"
        elif request.function == Const.READ_HOLDING_REGISTERS:
            # Hregs (setter+getter) [0, 65535]
            # function 03 - read holding register
            reg_type = "HREGS"
            req_type = "READ"
        elif request.function == Const.READ_INPUT_REGISTER:
            # Iregs (only getter) [0, 65535]
            # function 04 - read input registers
            reg_type = "IREGS"
            req_type = "READ"
        elif request.function == Const.WRITE_SINGLE_COIL or request.function == Const.WRITE_MULTIPLE_COILS:
            # Coils (setter+getter) [0, 1]
            # function 05 - write single coil
            # function 15 - write multiple coil
            reg_type = "COILS"
            req_type = "WRITE"
        elif request.function == Const.WRITE_SINGLE_REGISTER or request.function == Const.WRITE_MULTIPLE_REGISTERS:
            # Hregs (setter+getter) [0, 65535]
            # function 06 - write holding register
            # function 16 - write multiple holding register
            reg_type = "HREGS"
            req_type = "WRITE"
        else:
            request.send_exception(Const.ILLEGAL_FUNCTION)

        if reg_type:
            if req_type == "READ":
                self._process_read_access(request=request, reg_type=reg_type)
            elif req_type == "WRITE":
                self._process_write_access(request=request, reg_type=reg_type)

        return True

    def _create_response(self, request: Request, reg_type: str) -> Union[List[bool], List[int]]:
        """
        根据请求的起始地址和数量，从寄存器字典中提取数据构造响应。

        Args:
            request (Request): Modbus请求对象。
            reg_type (str): 寄存器类型，如'COILS'、'HREGS'等。

        Returns:
            Union[List[bool], List[int]]: 按地址顺序排列的寄存器值列表。

        Notes:
            如果寄存器不存在，则使用默认值填充。线圈和离散输入的默认值为False，寄存器默认值为0。
            注意数据字节顺序问题，详见注释。

        ==========================================
        Build response data from register dictionary according to request start address and quantity.

        Args:
            request (Request): Modbus request object.
            reg_type (str): Register type, e.g. 'COILS', 'HREGS', etc.

        Returns:
            Union[List[bool], List[int]]: List of register values in address order.

        Notes:
            Uses default value if register not present. Default is False for coils/discrete inputs,
            0 for registers. Note byte order issue as described in comments.
        """
        data = []
        default_value = {"val": 0}
        reg_dict = self._register_dict[reg_type]

        if reg_type in ["COILS", "ISTS"]:
            default_value = {"val": False}

        for addr in range(request.register_addr, request.register_addr + request.quantity):
            value = reg_dict.get(addr, default_value)["val"]

            if isinstance(value, (list, tuple)):
                data.extend(value)
            else:
                data.append(value)

        # caution LSB vs MSB
        # [
        #   1, 0, 1, 1, 0, 0, 1, 1,     # 0xB3
        #   1, 1, 0, 1, 0, 1, 1, 0,     # 0xD6
        #   1, 0, 1                     # 0x5
        # ]
        # but should be, documented at #38, see
        # https://github.com/brainelectronics/micropython-modbus/issues/38
        # this is only an issue of data provisioning as client/slave,
        # it has thereby NOT to be fixed in
        # :py:function:`umodbus.functions.bytes_to_bool`
        # [
        #   1, 1, 0, 0, 1, 1, 0, 1,     # 0xCD
        #   0, 1, 1, 0, 1, 0, 1, 1,     # 0x6B
        #   1, 0, 1                     # 0x5
        # ]
        #       27 .... 20
        # CD    1100 1101
        #
        #       35 .... 28
        # 6B    0110 1011
        #
        #       43 .... 36
        # 05    0000 0101
        #
        # 1011 0011   1101 0110   1010 0000

        return data

    def _process_read_access(self, request: Request, reg_type: str) -> None:
        """
        处理读请求：检查地址有效性，调用回调（若存在），发送响应数据。

        Args:
            request (Request): Modbus请求对象。
            reg_type (str): 寄存器类型。

        Raises:
            (通过request.send_exception发送异常) 如果地址无效，发送非法数据地址异常。

        Notes:
            如果寄存器配置了on_get_cb回调，则在发送响应前调用该回调。

        ==========================================
        Process read request: check address validity, invoke callback if present, send response data.

        Args:
            request (Request): Modbus request object.
            reg_type (str): Register type.

        Raises:
            (Exception sent via request.send_exception) If address invalid, send illegal data address exception.

        Notes:
            If register has on_get_cb callback, it is called before sending response.
        """
        address = request.register_addr

        if address in self._register_dict[reg_type]:

            if self._register_dict[reg_type][address].get("on_get_cb", 0):
                vals = self._create_response(request=request, reg_type=reg_type)
                _cb = self._register_dict[reg_type][address]["on_get_cb"]
                _cb(reg_type=reg_type, address=address, val=vals)

            vals = self._create_response(request=request, reg_type=reg_type)
            request.send_response(vals)
        else:
            request.send_exception(Const.ILLEGAL_DATA_ADDRESS)

    def _process_write_access(self, request: Request, reg_type: str) -> None:
        """
        处理写请求：解析数据，更新寄存器值，记录变更，调用回调。

        Args:
            request (Request): Modbus请求对象。
            reg_type (str): 寄存器类型，仅支持'COILS'或'HREGS'。

        Raises:
            (通过request.send_exception发送异常) 数据无效时发送非法数据值异常；
            地址无效时发送非法数据地址异常；其他寄存器类型尝试写操作发送非法功能异常。

        Notes:
            仅线圈和保持寄存器支持写操作。写成功后更新变更记录并调用on_set_cb回调。

        ==========================================
        Process write request: parse data, update register values, record change, invoke callback.

        Args:
            request (Request): Modbus request object.
            reg_type (str): Register type, only 'COILS' or 'HREGS' supported.

        Raises:
            (Exception sent via request.send_exception) If data invalid send illegal data value exception;
            if address invalid send illegal data address exception; write on other register types sends illegal function exception.

        Notes:
            Only coils and holding registers support write operations. After successful write,
            change record is updated and on_set_cb callback is invoked.
        """
        address = request.register_addr
        val = 0
        valid_register = False

        if address in self._register_dict[reg_type]:
            if request.data is None:
                request.send_exception(Const.ILLEGAL_DATA_VALUE)
                return

            if reg_type == "COILS":
                valid_register = True

                if request.function == Const.WRITE_SINGLE_COIL:
                    val = request.data[0]
                    if 0x00 < val < 0xFF:
                        valid_register = False
                        request.send_exception(Const.ILLEGAL_DATA_VALUE)
                    else:
                        val = [(val == 0xFF)]
                elif request.function == Const.WRITE_MULTIPLE_COILS:
                    tmp = int.from_bytes(request.data, "big")
                    val = [bool(tmp & (1 << n)) for n in range(request.quantity)]

                if valid_register:
                    self.set_coil(address=address, value=val)
            elif reg_type == "HREGS":
                valid_register = True
                val = list(functions.to_short(byte_array=request.data, signed=False))

                if request.function in [Const.WRITE_SINGLE_REGISTER, Const.WRITE_MULTIPLE_REGISTERS]:
                    self.set_hreg(address=address, value=val)
            else:
                # nothing except holding registers or coils can be set
                request.send_exception(Const.ILLEGAL_FUNCTION)

            if valid_register:
                request.send_response()
                self._set_changed_register(reg_type=reg_type, address=address, value=val)
                if self._register_dict[reg_type][address].get("on_set_cb", 0):
                    _cb = self._register_dict[reg_type][address]["on_set_cb"]
                    _cb(reg_type=reg_type, address=address, val=val)
        else:
            request.send_exception(Const.ILLEGAL_DATA_ADDRESS)

    def add_coil(
        self,
        address: int,
        value: Union[bool, List[bool]] = False,
        on_set_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None,
        on_get_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None,
    ) -> None:
        """
        添加一个线圈到寄存器字典。

        Args:
            address (int): 线圈地址。
            value (Union[bool, List[bool]], optional): 默认值，可以是单个bool或bool列表。默认为False。
            on_set_cb (Callable, optional): 当线圈被写入时的回调函数，签名为 (reg_type, address, value) -> None。
            on_get_cb (Callable, optional): 当线圈被读取时的回调函数，签名为 (reg_type, address, value) -> None。

        Notes:
            如果value是列表，则会从address开始依次添加多个线圈。

        ==========================================
        Add a coil to the register dictionary.

        Args:
            address (int): Coil address.
            value (Union[bool, List[bool]], optional): Default value, can be single bool or list of bools. Defaults to False.
            on_set_cb (Callable, optional): Callback when coil is written, signature (reg_type, address, value) -> None.
            on_get_cb (Callable, optional): Callback when coil is read, signature (reg_type, address, value) -> None.

        Notes:
            If value is a list, multiple coils will be added starting from address.
        """
        self._set_reg_in_dict(reg_type="COILS", address=address, value=value, on_set_cb=on_set_cb, on_get_cb=on_get_cb)

    def remove_coil(self, address: int) -> Union[None, bool, List[bool]]:
        """
        从寄存器字典中移除一个线圈。

        Args:
            address (int): 线圈地址。

        Returns:
            Union[None, bool, List[bool]]: 被移除的线圈值，如果地址不存在则返回None。

        ==========================================
        Remove a coil from the register dictionary.

        Args:
            address (int): Coil address.

        Returns:
            Union[None, bool, List[bool]]: Removed coil value, or None if address does not exist.
        """
        return self._remove_reg_from_dict(reg_type="COILS", address=address)

    def set_coil(self, address: int, value: Union[bool, List[bool]] = False) -> None:
        """
        设置线圈的值。

        Args:
            address (int): 线圈地址。
            value (Union[bool, List[bool]], optional): 新值，单个bool或bool列表。默认为False。

        Notes:
            如果value是列表，则会从address开始依次设置多个线圈的值。

        ==========================================
        Set the coil value.

        Args:
            address (int): Coil address.
            value (Union[bool, List[bool]], optional): New value, single bool or list of bools. Defaults to False.

        Notes:
            If value is a list, multiple coils will be set starting from address.
        """
        self._set_reg_in_dict(reg_type="COILS", address=address, value=value)

    def get_coil(self, address: int) -> Union[bool, List[bool]]:
        """
        获取线圈的值。

        Args:
            address (int): 线圈地址。

        Returns:
            Union[bool, List[bool]]: 线圈当前值。

        Raises:
            KeyError: 如果地址不存在。

        ==========================================
        Get the coil value.

        Args:
            address (int): Coil address.

        Returns:
            Union[bool, List[bool]]: Current coil value.

        Raises:
            KeyError: If address does not exist.
        """
        return self._get_reg_in_dict(reg_type="COILS", address=address)

    @property
    def coils(self) -> dict_keys:
        """
        获取所有已配置的线圈地址列表。

        Returns:
            dict_keys: 线圈地址的键视图。

        ==========================================
        Get list of all configured coil addresses.

        Returns:
            dict_keys: Key view of coil addresses.
        """
        return self._get_regs_of_dict(reg_type="COILS")

    def add_hreg(
        self,
        address: int,
        value: Union[int, List[int]] = 0,
        on_set_cb: Callable[[str, int, List[int]], None] = None,
        on_get_cb: Callable[[str, int, List[int]], None] = None,
    ) -> None:
        """
        添加一个保持寄存器到寄存器字典。

        Args:
            address (int): 寄存器地址。
            value (Union[int, List[int]], optional): 默认值，单个整数或整数列表。默认为0。
            on_set_cb (Callable, optional): 写入时的回调，签名为 (reg_type, address, value) -> None。
            on_get_cb (Callable, optional): 读取时的回调，签名为 (reg_type, address, value) -> None。

        ==========================================
        Add a holding register to the register dictionary.

        Args:
            address (int): Register address.
            value (Union[int, List[int]], optional): Default value, single int or list of ints. Defaults to 0.
            on_set_cb (Callable, optional): Callback on write, signature (reg_type, address, value) -> None.
            on_get_cb (Callable, optional): Callback on read, signature (reg_type, address, value) -> None.
        """
        self._set_reg_in_dict(reg_type="HREGS", address=address, value=value, on_set_cb=on_set_cb, on_get_cb=on_get_cb)

    def remove_hreg(self, address: int) -> Union[None, int, List[int]]:
        """
        从寄存器字典中移除一个保持寄存器。

        Args:
            address (int): 寄存器地址。

        Returns:
            Union[None, int, List[int]]: 被移除的寄存器值，如果地址不存在则返回None。

        ==========================================
        Remove a holding register from the register dictionary.

        Args:
            address (int): Register address.

        Returns:
            Union[None, int, List[int]]: Removed register value, or None if address does not exist.
        """
        return self._remove_reg_from_dict(reg_type="HREGS", address=address)

    def set_hreg(self, address: int, value: Union[int, List[int]] = 0) -> None:
        """
        设置保持寄存器的值。

        Args:
            address (int): 寄存器地址。
            value (Union[int, List[int]], optional): 新值，单个整数或整数列表。默认为0。

        ==========================================
        Set the holding register value.

        Args:
            address (int): Register address.
            value (Union[int, List[int]], optional): New value, single int or list of ints. Defaults to 0.
        """
        self._set_reg_in_dict(reg_type="HREGS", address=address, value=value)

    def get_hreg(self, address: int) -> Union[int, List[int]]:
        """
        获取保持寄存器的值。

        Args:
            address (int): 寄存器地址。

        Returns:
            Union[int, List[int]]: 寄存器当前值。

        Raises:
            KeyError: 如果地址不存在。

        ==========================================
        Get the holding register value.

        Args:
            address (int): Register address.

        Returns:
            Union[int, List[int]]: Current register value.

        Raises:
            KeyError: If address does not exist.
        """
        return self._get_reg_in_dict(reg_type="HREGS", address=address)

    @property
    def hregs(self) -> dict_keys:
        """
        获取所有已配置的保持寄存器地址列表。

        Returns:
            dict_keys: 寄存器地址的键视图。

        ==========================================
        Get list of all configured holding register addresses.

        Returns:
            dict_keys: Key view of register addresses.
        """
        return self._get_regs_of_dict(reg_type="HREGS")

    def add_ist(
        self, address: int, value: Union[bool, List[bool]] = False, on_get_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None
    ) -> None:
        """
        添加一个离散输入到寄存器字典。

        Args:
            address (int): 离散输入地址。
            value (Union[bool, List[bool]], optional): 默认值，单个bool或bool列表。默认为False。
            on_get_cb (Callable, optional): 读取时的回调，签名为 (reg_type, address, value) -> None。

        Notes:
            离散输入是只读的，不支持写入，因此没有 on_set_cb 参数。

        ==========================================
        Add a discrete input to the register dictionary.

        Args:
            address (int): Discrete input address.
            value (Union[bool, List[bool]], optional): Default value, single bool or list of bools. Defaults to False.
            on_get_cb (Callable, optional): Callback on read, signature (reg_type, address, value) -> None.

        Notes:
            Discrete inputs are read-only, no on_set_cb parameter.
        """
        self._set_reg_in_dict(reg_type="ISTS", address=address, value=value, on_get_cb=on_get_cb)

    def remove_ist(self, address: int) -> Union[None, bool, List[bool]]:
        """
        从寄存器字典中移除一个离散输入。

        Args:
            address (int): 离散输入地址。

        Returns:
            Union[None, bool, List[bool]]: 被移除的值，如果地址不存在则返回None。

        ==========================================
        Remove a discrete input from the register dictionary.

        Args:
            address (int): Discrete input address.

        Returns:
            Union[None, bool, List[bool]]: Removed value, or None if address does not exist.
        """
        return self._remove_reg_from_dict(reg_type="ISTS", address=address)

    def set_ist(self, address: int, value: bool = False) -> None:
        """
        设置离散输入的值（注意：离散输入本应是只读的，但此方法允许内部修改）。

        Args:
            address (int): 离散输入地址。
            value (bool, optional): 新值。默认为False。

        ==========================================
        Set the discrete input value (note: discrete inputs are read-only by specification, but this method allows internal modification).

        Args:
            address (int): Discrete input address.
            value (bool, optional): New value. Defaults to False.
        """
        self._set_reg_in_dict(reg_type="ISTS", address=address, value=value)

    def get_ist(self, address: int) -> Union[bool, List[bool]]:
        """
        获取离散输入的值。

        Args:
            address (int): 离散输入地址。

        Returns:
            Union[bool, List[bool]]: 当前值。

        Raises:
            KeyError: 如果地址不存在。

        ==========================================
        Get the discrete input value.

        Args:
            address (int): Discrete input address.

        Returns:
            Union[bool, List[bool]]: Current value.

        Raises:
            KeyError: If address does not exist.
        """
        return self._get_reg_in_dict(reg_type="ISTS", address=address)

    @property
    def ists(self) -> dict_keys:
        """
        获取所有已配置的离散输入地址列表。

        Returns:
            dict_keys: 地址键视图。

        ==========================================
        Get list of all configured discrete input addresses.

        Returns:
            dict_keys: Key view of addresses.
        """
        return self._get_regs_of_dict(reg_type="ISTS")

    def add_ireg(
        self, address: int, value: Union[int, List[int]] = 0, on_get_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None
    ) -> None:
        """
        添加一个输入寄存器到寄存器字典。

        Args:
            address (int): 输入寄存器地址。
            value (Union[int, List[int]], optional): 默认值，单个整数或整数列表。默认为0。
            on_get_cb (Callable, optional): 读取时的回调，签名为 (reg_type, address, value) -> None。

        Notes:
            输入寄存器是只读的，不支持写入，因此没有 on_set_cb 参数。

        ==========================================
        Add an input register to the register dictionary.

        Args:
            address (int): Input register address.
            value (Union[int, List[int]], optional): Default value, single int or list of ints. Defaults to 0.
            on_get_cb (Callable, optional): Callback on read, signature (reg_type, address, value) -> None.

        Notes:
            Input registers are read-only, no on_set_cb parameter.
        """
        self._set_reg_in_dict(reg_type="IREGS", address=address, value=value, on_get_cb=on_get_cb)

    def remove_ireg(self, address: int) -> Union[None, int, List[int]]:
        """
        从寄存器字典中移除一个输入寄存器。

        Args:
            address (int): 输入寄存器地址。

        Returns:
            Union[None, int, List[int]]: 被移除的值，如果地址不存在则返回None。

        ==========================================
        Remove an input register from the register dictionary.

        Args:
            address (int): Input register address.

        Returns:
            Union[None, int, List[int]]: Removed value, or None if address does not exist.
        """
        return self._remove_reg_from_dict(reg_type="IREGS", address=address)

    def set_ireg(self, address: int, value: Union[int, List[int]] = 0) -> None:
        """
        设置输入寄存器的值（注意：输入寄存器本应是只读的，但此方法允许内部修改）。

        Args:
            address (int): 输入寄存器地址。
            value (Union[int, List[int]], optional): 新值。默认为0。

        ==========================================
        Set the input register value (note: input registers are read-only by specification, but this method allows internal modification).

        Args:
            address (int): Input register address.
            value (Union[int, List[int]], optional): New value. Defaults to 0.
        """
        self._set_reg_in_dict(reg_type="IREGS", address=address, value=value)

    def get_ireg(self, address: int) -> Union[int, List[int]]:
        """
        获取输入寄存器的值。

        Args:
            address (int): 输入寄存器地址。

        Returns:
            Union[int, List[int]]: 当前值。

        Raises:
            KeyError: 如果地址不存在。

        ==========================================
        Get the input register value.

        Args:
            address (int): Input register address.

        Returns:
            Union[int, List[int]]: Current value.

        Raises:
            KeyError: If address does not exist.
        """
        return self._get_reg_in_dict(reg_type="IREGS", address=address)

    @property
    def iregs(self) -> dict_keys:
        """
        获取所有已配置的输入寄存器地址列表。

        Returns:
            dict_keys: 地址键视图。

        ==========================================
        Get list of all configured input register addresses.

        Returns:
            dict_keys: Key view of addresses.
        """
        return self._get_regs_of_dict(reg_type="IREGS")

    def _set_reg_in_dict(
        self,
        reg_type: str,
        address: int,
        value: Union[bool, int, List[bool], List[int]],
        on_set_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None,
        on_get_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None,
    ) -> None:
        """
        在寄存器字典中设置一个或多个寄存器的值。支持单个值或列表（自动展开为连续地址）。

        Args:
            reg_type (str): 寄存器类型。
            address (int): 起始地址。
            value (Union[bool, int, List[bool], List[int]]): 要设置的值，单个或列表。
            on_set_cb (Callable, optional): 写入回调。
            on_get_cb (Callable, optional): 读取回调。

        Raises:
            KeyError: 如果reg_type不是有效的寄存器类型。

        Notes:
            如果value是列表，则从address开始依次设置每个元素。

        ==========================================
        Set value of one or more registers in the register dictionary. Supports single value or list (auto-expand to consecutive addresses).

        Args:
            reg_type (str): Register type.
            address (int): Start address.
            value (Union[bool, int, List[bool], List[int]]): Value to set, single or list.
            on_set_cb (Callable, optional): Write callback.
            on_get_cb (Callable, optional): Read callback.

        Raises:
            KeyError: If reg_type is not a valid register type.

        Notes:
            If value is a list, each element is set starting from address.
        """
        if not self._check_valid_register(reg_type=reg_type):
            raise KeyError("{} is not a valid register type of {}".format(reg_type, self._available_register_types))

        if isinstance(value, (list, tuple)):
            # flatten the list and add single registers only
            for idx, val in enumerate(value):
                this_addr = address + idx
                self._set_single_reg_in_dict(reg_type=reg_type, address=this_addr, value=val, on_set_cb=on_set_cb, on_get_cb=on_get_cb)
        else:
            self._set_single_reg_in_dict(reg_type=reg_type, address=address, value=value, on_set_cb=on_set_cb, on_get_cb=on_get_cb)

    def _set_single_reg_in_dict(
        self,
        reg_type: str,
        address: int,
        value: Union[bool, int],
        on_set_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None,
        on_get_cb: Callable[[str, int, Union[List[bool], List[int]]], None] = None,
    ) -> None:
        """
        在寄存器字典中设置单个寄存器的值。

        Args:
            reg_type (str): 寄存器类型。
            address (int): 寄存器地址。
            value (Union[bool, int]): 要设置的值。
            on_set_cb (Callable, optional): 写入回调。
            on_get_cb (Callable, optional): 读取回调。

        Notes:
            如果该地址已存在，则保留原有的回调函数（除非本次提供了新的可调用回调）。

        ==========================================
        Set value of a single register in the register dictionary.

        Args:
            reg_type (str): Register type.
            address (int): Register address.
            value (Union[bool, int]): Value to set.
            on_set_cb (Callable, optional): Write callback.
            on_get_cb (Callable, optional): Read callback.

        Notes:
            If the address already exists, existing callbacks are retained unless new callable ones are provided.
        """
        data = {"val": value}

        # if the register exists already in the register dict a "set_*"
        # function might have called this functions
        if address in self._register_dict[reg_type]:
            # try to get the (already) registered callback function from the
            # register dict of this address with the this time call function
            # parameter callback value as fallback
            on_set_cb = self._register_dict[reg_type][address].get("on_set_cb", on_set_cb)

            on_get_cb = self._register_dict[reg_type][address].get("on_get_cb", on_get_cb)

        if callable(on_set_cb):
            data["on_set_cb"] = on_set_cb

        if callable(on_get_cb):
            data["on_get_cb"] = on_get_cb

        self._register_dict[reg_type][address] = data

    def _remove_reg_from_dict(self, reg_type: str, address: int) -> Union[None, bool, int, List[bool], List[int]]:
        """
        从寄存器字典中移除指定地址的寄存器。

        Args:
            reg_type (str): 寄存器类型。
            address (int): 寄存器地址。

        Returns:
            Union[None, bool, int, List[bool], List[int]]: 被移除的寄存器值，如果不存在则返回None。

        Raises:
            KeyError: 如果reg_type无效。

        ==========================================
        Remove register at specified address from register dictionary.

        Args:
            reg_type (str): Register type.
            address (int): Register address.

        Returns:
            Union[None, bool, int, List[bool], List[int]]: Removed register value, or None if not exist.

        Raises:
            KeyError: If reg_type is invalid.
        """
        if not self._check_valid_register(reg_type=reg_type):
            raise KeyError("{} is not a valid register type of {}".format(reg_type, self._available_register_types))

        return self._register_dict[reg_type].pop(address, None)

    def _get_reg_in_dict(self, reg_type: str, address: int) -> Union[bool, int, List[bool], List[int]]:
        """
        从寄存器字典中获取指定地址的寄存器值。

        Args:
            reg_type (str): 寄存器类型。
            address (int): 寄存器地址。

        Returns:
            Union[bool, int, List[bool], List[int]]: 寄存器当前值。

        Raises:
            KeyError: 如果reg_type无效或地址不存在。

        ==========================================
        Get register value at specified address from register dictionary.

        Args:
            reg_type (str): Register type.
            address (int): Register address.

        Returns:
            Union[bool, int, List[bool], List[int]]: Current register value.

        Raises:
            KeyError: If reg_type is invalid or address does not exist.
        """
        if not self._check_valid_register(reg_type=reg_type):
            raise KeyError("{} is not a valid register type of {}".format(reg_type, self._available_register_types))

        if address in self._register_dict[reg_type]:
            return self._register_dict[reg_type][address]["val"]
        else:
            raise KeyError("No {} available for the register address {}".format(reg_type, address))

    def _get_regs_of_dict(self, reg_type: str) -> dict_keys:
        """
        获取指定寄存器类型的所有已配置地址。

        Args:
            reg_type (str): 寄存器类型。

        Returns:
            dict_keys: 地址的键视图。

        Raises:
            KeyError: 如果reg_type无效。

        ==========================================
        Get all configured addresses for a given register type.

        Args:
            reg_type (str): Register type.

        Returns:
            dict_keys: Key view of addresses.

        Raises:
            KeyError: If reg_type is invalid.
        """
        if not self._check_valid_register(reg_type=reg_type):
            raise KeyError("{} is not a valid register type of {}".format(reg_type, self._available_register_types))

        return self._register_dict[reg_type].keys()

    def _check_valid_register(self, reg_type: str) -> bool:
        """
        检查寄存器类型是否有效。

        Args:
            reg_type (str): 寄存器类型。

        Returns:
            bool: 如果类型在 _available_register_types 中则返回True，否则False。

        ==========================================
        Check if register type is valid.

        Args:
            reg_type (str): Register type.

        Returns:
            bool: True if type is in _available_register_types, else False.
        """
        if reg_type in self._available_register_types:
            return True
        else:
            return False

    @property
    def changed_registers(self) -> dict:
        """
        获取所有被外部修改过的寄存器记录。

        Returns:
            dict: 结构为 {reg_type: {address: {'val': value, 'time': ticks_ms}}}。

        ==========================================
        Get all registers that have been externally modified.

        Returns:
            dict: Structure {reg_type: {address: {'val': value, 'time': ticks_ms}}}.
        """
        return self._changed_registers

    @property
    def changed_coils(self) -> dict:
        """
        获取被外部修改过的线圈记录。

        Returns:
            dict: {address: {'val': value, 'time': ticks_ms}}。

        ==========================================
        Get externally modified coils.

        Returns:
            dict: {address: {'val': value, 'time': ticks_ms}}.
        """
        return self._changed_registers["COILS"]

    @property
    def changed_hregs(self) -> dict:
        """
        获取被外部修改过的保持寄存器记录。

        Returns:
            dict: {address: {'val': value, 'time': ticks_ms}}。

        ==========================================
        Get externally modified holding registers.

        Returns:
            dict: {address: {'val': value, 'time': ticks_ms}}.
        """
        return self._changed_registers["HREGS"]

    def _set_changed_register(self, reg_type: str, address: int, value: Union[bool, int, List[bool], List[int]]) -> None:
        """
        将寄存器标记为已修改，记录新值和当前时间戳。

        Args:
            reg_type (str): 寄存器类型，必须在 _changeable_register_types 中。
            address (int): 寄存器地址。
            value (Union[bool, int, List[bool], List[int]]): 新值。

        Raises:
            KeyError: 如果reg_type不可被外部修改。

        Notes:
            如果value是列表，则会为列表中的每个元素分别记录。

        ==========================================
        Mark register as changed, record new value and current timestamp.

        Args:
            reg_type (str): Register type, must be in _changeable_register_types.
            address (int): Register address.
            value (Union[bool, int, List[bool], List[int]]): New value.

        Raises:
            KeyError: If reg_type cannot be externally modified.

        Notes:
            If value is a list, each element is recorded separately.
        """
        if reg_type in self._changeable_register_types:
            if isinstance(value, (list, tuple)):
                for idx, val in enumerate(value):
                    content = {"val": val, "time": time.ticks_ms()}
                    self._changed_registers[reg_type][address + idx] = content
            else:
                content = {"val": value, "time": time.ticks_ms()}
                self._changed_registers[reg_type][address] = content
        else:
            raise KeyError("{} can not be changed externally".format(reg_type))

    def _remove_changed_register(self, reg_type: str, address: int, timestamp: int) -> bool:
        """
        从变更记录中移除指定寄存器（仅当时间戳匹配时）。

        Args:
            reg_type (str): 寄存器类型。
            address (int): 寄存器地址。
            timestamp (int): 变更时的时间戳（毫秒）。

        Returns:
            bool: 成功移除返回True，否则False。

        Raises:
            KeyError: 如果reg_type无效。

        ==========================================
        Remove register from change records only if timestamp matches.

        Args:
            reg_type (str): Register type.
            address (int): Register address.
            timestamp (int): Timestamp of change (milliseconds).

        Returns:
            bool: True if removed successfully, False otherwise.

        Raises:
            KeyError: If reg_type is invalid.
        """
        result = False

        if reg_type in self._changeable_register_types:
            _changed_register_timestamp = self._changed_registers[reg_type][address]["time"]

            if _changed_register_timestamp == timestamp:
                self._changed_registers[reg_type].pop(address, None)
                result = True
        else:
            raise KeyError("{} is not a valid register type of {}".format(reg_type, self._changeable_register_types))

        return result

    def setup_registers(self, registers: dict = dict(), use_default_vals: Optional[bool] = False) -> None:
        """
        批量配置所有类型的寄存器。

        Args:
            registers (dict, optional): 寄存器配置字典，结构为 {reg_type: {name: {'register': addr, 'val': value, 'len': length, 'on_set_cb': cb, 'on_get_cb': cb}}}。默认为空字典。
            use_default_vals (Optional[bool], optional): 是否使用默认值（False或0）代替配置中的val。默认为False。

        Notes:
            支持根据'len'字段创建多个连续寄存器。
            只读类型（ISTS, IREGS）的on_set_cb会被忽略。

        ==========================================
        Batch configure all register types.

        Args:
            registers (dict, optional): Register configuration dictionary, structure {reg_type: {name: {'register': addr, 'val': value, 'len': length, 'on_set_cb': cb, 'on_get_cb': cb}}}. Defaults to empty.
            use_default_vals (Optional[bool], optional): Whether to use default values (False or 0) instead of configured val. Defaults to False.

        Notes:
            Supports creating multiple consecutive registers via 'len' field.
            on_set_cb is ignored for read-only types (ISTS, IREGS).
        """
        if len(registers):
            for reg_type, default_val in self._default_vals.items():
                if reg_type in registers:
                    for reg, val in registers[reg_type].items():
                        address = val["register"]

                        if use_default_vals:
                            if "len" in val:
                                value = [default_val] * val["len"]
                            else:
                                value = default_val
                        else:
                            value = val["val"]

                        on_set_cb = val.get("on_set_cb", None)
                        on_get_cb = val.get("on_get_cb", None)

                        if reg_type == "COILS":
                            self.add_coil(address=address, value=value, on_set_cb=on_set_cb, on_get_cb=on_get_cb)
                        elif reg_type == "HREGS":
                            self.add_hreg(address=address, value=value, on_set_cb=on_set_cb, on_get_cb=on_get_cb)
                        elif reg_type == "ISTS":
                            self.add_ist(address=address, value=value, on_get_cb=on_get_cb)  # only getter
                        elif reg_type == "IREGS":
                            self.add_ireg(address=address, value=value, on_get_cb=on_get_cb)  # only getter
                        else:
                            # invalid register type
                            pass
                else:
                    pass


# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================
