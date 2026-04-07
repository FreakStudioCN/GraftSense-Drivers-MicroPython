# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午4:52
# @Author  : Anonymous
# @File    : modbus_tcp.py
# @Description : Modbus TCP协议实现，包括客户端（主站）和服务端（从站），支持TCP连接、请求响应处理。
# @License : MIT
__version__ = "0.1.0"
__author__ = "Anonymous"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# system packages
# import random
import struct
import socket
import time

# custom packages
from . import functions
from . import const as Const
from .common import Request, CommonModbusFunctions
from .common import ModbusException
from .modbus import Modbus

# typing not natively supported on MicroPython
from .typing import Optional, Tuple, Union

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class ModbusTCP(Modbus):
    """
    Modbus TCP客户端类，继承自Modbus抽象类。

    该类通过TCP/IP网络与Modbus TCP服务器通信，内部使用TCPServer作为接口。

    Attributes:
        _itf (TCPServer): TCP服务器接口对象。
        _addr_list (None): 地址列表未使用（TCP协议不使用单元地址列表）。

    Methods:
        __init__(): 初始化Modbus TCP客户端。
        bind(): 绑定本地IP和端口以接收请求。
        get_bound_status(): 获取绑定状态。

    Notes:
        TCP协议不需要从站地址列表，因此_addr_list为None。

    ==========================================
    Modbus TCP client class, inherits from Modbus abstract class.

    This class communicates with Modbus TCP servers over TCP/IP network, using TCPServer as interface.

    Attributes:
        _itf (TCPServer): TCP server interface object.
        _addr_list (None): Address list not used (TCP protocol does not use unit address list).

    Methods:
        __init__(): Initialize Modbus TCP client.
        bind(): Bind local IP and port to receive requests.
        get_bound_status(): Get bound status.

    Notes:
        TCP protocol does not require a slave address list, so _addr_list is None.
    """
    def __init__(self):
        """
        初始化Modbus TCP客户端。

        Notes:
            创建TCPServer实例作为接口，并将地址列表设为None。

        ==========================================
        Initialize Modbus TCP client.

        Notes:
            Creates TCPServer instance as interface and sets address list to None.
        """
        super().__init__(
            # set itf to TCPServer object, addr_list to None
            TCPServer(),
            None
        )

    def bind(self,
             local_ip: str,
             local_port: int = 502,
             max_connections: int = 10) -> None:
        """
        绑定本地IP和端口以接收传入请求。

        Args:
            local_ip (str): 监听请求的本设备IP地址。
            local_port (int, optional): 本设备端口，默认502。
            max_connections (int, optional): 最大连接数，默认10。

        Notes:
            调用内部TCPServer的bind方法。

        ==========================================
        Bind IP and port for incoming requests.

        Args:
            local_ip (str): IP of this device listening for requests.
            local_port (int, optional): Port of this device, default 502.
            max_connections (int, optional): Number of maximum connections, default 10.

        Notes:
            Calls the bind method of the internal TCPServer.
        """
        self._itf.bind(local_ip, local_port, max_connections)

    def get_bound_status(self) -> bool:
        """
        获取IP和端口的绑定状态。

        Returns:
            bool: 已绑定返回True，否则返回False。

        Raises:
            Exception: 如果内部接口没有is_bound属性或获取状态失败。

        ==========================================
        Get the IP and port binding status.

        Returns:
            bool: True if already bound, False otherwise.

        Raises:
            Exception: If internal interface has no is_bound attribute or status retrieval fails.
        """
        try:
            return self._itf.get_is_bound()
        except Exception:
            return False


class TCP(CommonModbusFunctions):
    """
    TCP客户端通信类，处理套接字连接和Modbus数据解析。

    作为Modbus TCP主站，主动连接到从站设备，发送请求并接收响应。

    Attributes:
        _sock (socket.socket): TCP套接字。
        trans_id_ctr (int): 事务ID计数器，每次发送递增。

    Methods:
        __init__(): 初始化TCP连接。
        _create_mbap_hdr(): 创建Modbus应用协议头部。
        _validate_resp_hdr(): 验证响应头部。
        _send_receive(): 发送请求并接收响应。

    Notes:
        事务ID使用递增计数器生成，符合Modbus TCP规范。

    ==========================================
    TCP client communication class, handling socket connections and Modbus data parsing.

    As a Modbus TCP master, it actively connects to slave devices, sends requests and receives responses.

    Attributes:
        _sock (socket.socket): TCP socket.
        trans_id_ctr (int): Transaction ID counter, incremented on each send.

    Methods:
        __init__(): Initialize TCP connection.
        _create_mbap_hdr(): Create Modbus Application Protocol header.
        _validate_resp_hdr(): Validate response header.
        _send_receive(): Send request and receive response.

    Notes:
        Transaction ID uses an incrementing counter, compliant with Modbus TCP specification.
    """
    def __init__(self,
                 slave_ip: str,
                 slave_port: int = 502,
                 timeout: float = 5.0):
        """
        初始化TCP连接。

        Args:
            slave_ip (str): 从站IP地址。
            slave_port (int, optional): 从站端口，默认502。
            timeout (float, optional): 套接字超时时间（秒），默认5.0。

        Notes:
            使用socket.getaddrinfo解析地址，建立TCP连接，并设置超时。

        ==========================================
        Initialize TCP connection.

        Args:
            slave_ip (str): Slave IP address.
            slave_port (int, optional): Slave port, default 502.
            timeout (float, optional): Socket timeout in seconds, default 5.0.

        Notes:
            Uses socket.getaddrinfo to resolve address, establishes TCP connection and sets timeout.
        """
        self._sock = socket.socket()
        self.trans_id_ctr = 0

        # print(socket.getaddrinfo(slave_ip, slave_port))
        # [(2, 1, 0, '192.168.178.47', ('192.168.178.47', 502))]
        self._sock.connect(socket.getaddrinfo(slave_ip, slave_port)[0][-1])

        self._sock.settimeout(timeout)

    def _create_mbap_hdr(self,
                         slave_addr: int,
                         modbus_pdu: bytes) -> Tuple[bytes, int]:
        """
        创建Modbus应用协议头部（MBAP）。

        Args:
            slave_addr (int): 从站标识符（单元ID）。
            modbus_pdu (bytes): Modbus协议数据单元。

        Returns:
            Tuple[bytes, int]: MBAP头部字节和事务ID。

        Notes:
            事务ID使用递增计数器生成。MBAP结构：事务ID(2)、协议ID(2)、长度(2)、单元ID(1)。

        ==========================================
        Create Modbus Application Protocol header (MBAP).

        Args:
            slave_addr (int): Slave identifier (unit ID).
            modbus_pdu (bytes): Modbus Protocol Data Unit.

        Returns:
            Tuple[bytes, int]: MBAP header bytes and transaction ID.

        Notes:
            Transaction ID uses incrementing counter. MBAP structure: Transaction ID(2), Protocol ID(2), Length(2), Unit ID(1).
        """
        # only available on WiPy
        # trans_id = machine.rng() & 0xFFFF
        # use builtin function to generate random 24 bit integer
        # trans_id = random.getrandbits(24) & 0xFFFF
        # use incrementing counter as it's faster
        trans_id = self.trans_id_ctr
        self.trans_id_ctr += 1

        mbap_hdr = struct.pack(
            '>HHHB', trans_id, 0, len(modbus_pdu) + 1, slave_addr)

        return mbap_hdr, trans_id

    def _validate_resp_hdr(self,
                           response: bytearray,
                           trans_id: int,
                           slave_addr: int,
                           function_code: int,
                           count: bool = False) -> bytes:
        """
        验证响应头部。

        Args:
            response (bytearray): 接收到的原始响应数据。
            trans_id (int): 期望的事务ID。
            slave_addr (int): 期望的从站标识符。
            function_code (int): 请求的功能码。
            count (bool, optional): 响应是否包含字节计数字段，用于确定头部长度。默认False。

        Returns:
            bytes: 响应中的PDU数据（不含MBAP头部）。

        Raises:
            ValueError: 事务ID不匹配、协议ID无效、从站ID不匹配或从站返回异常。

        Notes:
            异常响应中功能码会加上ERROR_BIAS，此时抛出异常并包含异常码。

        ==========================================
        Validate the response header.

        Args:
            response (bytearray): Raw received response data.
            trans_id (int): Expected transaction ID.
            slave_addr (int): Expected slave identifier.
            function_code (int): Requested function code.
            count (bool, optional): Whether response contains a byte count field, used to determine header length. Default False.

        Returns:
            bytes: PDU data in response (excluding MBAP header).

        Raises:
            ValueError: Transaction ID mismatch, invalid protocol ID, slave ID mismatch, or slave returned exception.

        Notes:
            Exception response has function code plus ERROR_BIAS, raises exception with exception code.
        """
        rec_tid, rec_pid, rec_len, rec_uid, rec_fc = struct.unpack(
            '>HHHBB', response[:Const.MBAP_HDR_LENGTH + 1])

        if (trans_id != rec_tid):
            raise ValueError('wrong transaction ID')

        if (rec_pid != 0):
            raise ValueError('invalid protocol ID')

        if (slave_addr != rec_uid):
            raise ValueError('wrong slave ID')

        if (rec_fc == (function_code + Const.ERROR_BIAS)):
            raise ValueError('slave returned exception code: {:d}'.
                             format(rec_fc))

        hdr_length = (Const.MBAP_HDR_LENGTH + 2) if count else \
            (Const.MBAP_HDR_LENGTH + 1)

        return response[hdr_length:]

    def _send_receive(self,
                      slave_addr: int,
                      modbus_pdu: bytes,
                      count: bool) -> bytes:
        """
        发送Modbus消息并接收响应。

        Args:
            slave_addr (int): 从站标识符（单元ID）。
            modbus_pdu (bytes): 要发送的Modbus PDU。
            count (bool): 是否期望响应中包含字节计数字段。

        Returns:
            bytes: 验证后的Modbus数据（不含MBAP头部）。

        Raises:
            ValueError: 响应验证失败。
            OSError: 套接字错误。

        Notes:
            构造MBAP头部后通过套接字发送，然后接收响应并验证。

        ==========================================
        Send a Modbus message and receive the response.

        Args:
            slave_addr (int): Slave identifier (unit ID).
            modbus_pdu (bytes): Modbus PDU to send.
            count (bool): Whether the response is expected to contain a byte count field.

        Returns:
            bytes: Validated Modbus data (excluding MBAP header).

        Raises:
            ValueError: Response validation failed.
            OSError: Socket error.

        Notes:
            Builds MBAP header, sends via socket, then receives and validates response.
        """
        mbap_hdr, trans_id = self._create_mbap_hdr(slave_addr=slave_addr,
                                                   modbus_pdu=modbus_pdu)
        self._sock.send(mbap_hdr + modbus_pdu)

        response = self._sock.recv(256)
        modbus_data = self._validate_resp_hdr(response=response,
                                              trans_id=trans_id,
                                              slave_addr=slave_addr,
                                              function_code=modbus_pdu[0],
                                              count=count)

        return modbus_data


class TCPServer(object):
    """
    Modbus TCP服务端类（从站），监听并接受客户端连接，处理Modbus请求。

    Attributes:
        _sock (socket.socket): 监听套接字。
        _client_sock (socket.socket): 当前连接的客户端套接字。
        _is_bound (bool): 是否已绑定IP和端口。
        _req_tid (int): 当前请求的事务ID，用于响应时回显。

    Methods:
        __init__(): 初始化TCPServer实例。
        is_bound: 属性，获取绑定状态。
        get_is_bound(): 获取绑定状态（兼容旧版）。
        bind(): 绑定IP和端口，开始监听。
        _send(): 发送Modbus响应给客户端。
        send_response(): 发送正常响应。
        send_exception_response(): 发送异常响应。
        _accept_request(): 接受并解析请求。
        get_request(): 在超时内获取请求。

    Notes:
        支持多连接，但同一时间只处理一个客户端连接（旧连接会被关闭）。
        事务ID从请求中提取并用于响应。

    ==========================================
    Modbus TCP server class (slave), listens for and accepts client connections, processes Modbus requests.

    Attributes:
        _sock (socket.socket): Listening socket.
        _client_sock (socket.socket): Currently connected client socket.
        _is_bound (bool): Whether IP and port are bound.
        _req_tid (int): Transaction ID of current request, echoed in response.

    Methods:
        __init__(): Initialize TCPServer instance.
        is_bound: Property, get bound status.
        get_is_bound(): Get bound status (legacy support).
        bind(): Bind IP and port, start listening.
        _send(): Send Modbus response to client.
        send_response(): Send normal response.
        send_exception_response(): Send exception response.
        _accept_request(): Accept and parse request.
        get_request(): Get request within timeout.

    Notes:
        Supports multiple connections but only one client at a time (old connection is closed).
        Transaction ID is extracted from request and echoed in response.
    """
    def __init__(self):
        """
        初始化TCPServer实例。

        ==========================================
        Initialize TCPServer instance.
        """
        self._sock = None
        self._client_sock = None
        self._is_bound = False

    @property
    def is_bound(self) -> bool:
        """
        获取IP和端口的绑定状态。

        Returns:
            bool: 已绑定返回True，否则False。

        ==========================================
        Get the IP and port binding status.

        Returns:
            bool: True if bound to IP and port, False otherwise.
        """
        return self._is_bound

    def get_is_bound(self) -> bool:
        """
        获取IP和端口的绑定状态（兼容旧版）。

        Returns:
            bool: 已绑定返回True，否则False。

        ==========================================
        Get the IP and port binding status (legacy support).

        Returns:
            bool: True if bound to IP and port, False otherwise.
        """
        return self._is_bound

    def bind(self,
             local_ip: str,
             local_port: int = 502,
             max_connections: int = 10):
        """
        绑定IP和端口，开始监听传入请求。

        Args:
            local_ip (str): 监听请求的本设备IP地址。
            local_port (int, optional): 本设备端口，默认502。
            max_connections (int, optional): 最大连接数，默认10。

        Notes:
            如果已有客户端连接或监听套接字，会先关闭它们。使用socket.getaddrinfo解析地址。

        ==========================================
        Bind IP and port for incoming requests.

        Args:
            local_ip (str): IP of this device listening for requests.
            local_port (int, optional): Port of this device, default 502.
            max_connections (int, optional): Number of maximum connections, default 10.

        Notes:
            Closes existing client or listening socket if present. Uses socket.getaddrinfo to resolve address.
        """
        if self._client_sock:
            self._client_sock.close()

        if self._sock:
            self._sock.close()

        self._sock = socket.socket()

        # print(socket.getaddrinfo(local_ip, local_port))
        # [(2, 1, 0, '192.168.178.47', ('192.168.178.47', 502))]
        self._sock.bind(socket.getaddrinfo(local_ip, local_port)[0][-1])

        self._sock.listen(max_connections)

        self._is_bound = True

    def _send(self, modbus_pdu: bytes, slave_addr: int) -> None:
        """
        发送Modbus协议数据单元给从站（实际为客户端）。

        Args:
            modbus_pdu (bytes): Modbus PDU。
            slave_addr (int): 从站地址（单元ID）。

        Notes:
            构造MBAP头部，使用保存的请求事务ID，通过客户端套接字发送。

        ==========================================
        Send Modbus Protocol Data Unit to slave (actually client).

        Args:
            modbus_pdu (bytes): Modbus PDU.
            slave_addr (int): Slave address (unit ID).

        Notes:
            Builds MBAP header with stored request transaction ID, sends via client socket.
        """
        size = len(modbus_pdu)
        fmt = 'B' * size
        adu = struct.pack('>HHHB' + fmt, self._req_tid, 0, size + 1, slave_addr, *modbus_pdu)
        self._client_sock.send(adu)

    def send_response(self,
                      slave_addr: int,
                      function_code: int,
                      request_register_addr: int,
                      request_register_qty: int,
                      request_data: list,
                      values: Optional[list] = None,
                      signed: bool = True) -> None:
        """
        发送正常响应给客户端。

        Args:
            slave_addr (int): 从站地址。
            function_code (int): 功能码。
            request_register_addr (int): 请求的寄存器起始地址。
            request_register_qty (int): 请求的寄存器数量。
            request_data (list): 请求中的原始数据。
            values (Optional[list], optional): 要返回的数据值列表（读响应）。默认为None。
            signed (bool, optional): 是否使用有符号格式。默认为True。

        Notes:
            使用functions.response构造PDU，然后调用_send发送。

        ==========================================
        Send a normal response to a client.

        Args:
            slave_addr (int): Slave address.
            function_code (int): Function code.
            request_register_addr (int): Requested starting register address.
            request_register_qty (int): Requested register quantity.
            request_data (list): Raw data from request.
            values (Optional[list], optional): Data values to return (for read response). Defaults to None.
            signed (bool, optional): Whether to use signed format. Defaults to True.

        Notes:
            Uses functions.response to build PDU, then calls _send.
        """
        modbus_pdu = functions.response(function_code,
                                        request_register_addr,
                                        request_register_qty,
                                        request_data,
                                        values,
                                        signed)
        self._send(modbus_pdu, slave_addr)

    def send_exception_response(self,
                                slave_addr: int,
                                function_code: int,
                                exception_code: int) -> None:
        """
        发送异常响应给客户端。

        Args:
            slave_addr (int): 从站地址。
            function_code (int): 原始功能码。
            exception_code (int): 异常码。

        Notes:
            使用functions.exception_response构造PDU。

        ==========================================
        Send an exception response to a client.

        Args:
            slave_addr (int): Slave address.
            function_code (int): Original function code.
            exception_code (int): Exception code.

        Notes:
            Uses functions.exception_response to build PDU.
        """
        modbus_pdu = functions.exception_response(function_code,
                                                  exception_code)
        self._send(modbus_pdu, slave_addr)

    def _accept_request(self,
                        accept_timeout: float,
                        unit_addr_list: list) -> Union[Request, None]:
        """
        接受、读取并解码基于套接字的请求。

        Args:
            accept_timeout (float): 套接字接受超时时间（秒）。
            unit_addr_list (list): 允许的单元地址列表。

        Returns:
            Union[Request, None]: 成功解析返回Request对象，否则返回None。

        Notes:
            如果accept超时（OSError 11），返回None。接收到空数据或解析失败也返回None。
            遇到ModbusException时会自动发送异常响应。

        ==========================================
        Accept, read and decode a socket based request.

        Args:
            accept_timeout (float): Socket accept timeout in seconds.
            unit_addr_list (list): List of allowed unit addresses.

        Returns:
            Union[Request, None]: Request object on success, None otherwise.

        Notes:
            If accept times out (OSError 11), returns None. Returns None on empty data or parse failure.
            Automatically sends exception response on ModbusException.
        """
        self._sock.settimeout(accept_timeout)
        new_client_sock = None

        try:
            new_client_sock, client_address = self._sock.accept()
        except OSError as e:
            if e.args[0] != 11:     # 11 = timeout expired
                raise e

        if new_client_sock is not None:
            if self._client_sock is not None:
                self._client_sock.close()

            self._client_sock = new_client_sock

            # recv() timeout, setting to 0 might lead to the following error
            # "Modbus request error: [Errno 11] EAGAIN"
            # This is a socket timeout error
            self._client_sock.settimeout(0.5)

        if self._client_sock is not None:
            try:
                req = self._client_sock.recv(128)

                if len(req) == 0:
                    return None

                req_header_no_uid = req[:Const.MBAP_HDR_LENGTH - 1]
                self._req_tid, req_pid, req_len = struct.unpack('>HHH', req_header_no_uid)
                req_uid_and_pdu = req[Const.MBAP_HDR_LENGTH - 1:Const.MBAP_HDR_LENGTH + req_len - 1]
            except OSError:
                # MicroPython raises an OSError instead of socket.timeout
                # print("Socket OSError aka TimeoutError: {}".format(e))
                return None
            except Exception:
                # print("Modbus request error:", e)
                self._client_sock.close()
                self._client_sock = None
                return None

            if (req_pid != 0):
                # print("Modbus request error: PID not 0")
                self._client_sock.close()
                self._client_sock = None
                return None

            if ((unit_addr_list is not None) and (req_uid_and_pdu[0] not in unit_addr_list)):
                return None

            try:
                return Request(self, req_uid_and_pdu)
            except ModbusException as e:
                self.send_exception_response(req[0],
                                             e.function_code,
                                             e.exception_code)
                return None

    def get_request(self,
                    unit_addr_list: Optional[list] = None,
                    timeout: int = None) -> Union[Request, None]:
        """
        在指定超时时间内检查是否有请求。

        Args:
            unit_addr_list (Optional[list], optional): 允许的单元地址列表，默认为None（接受所有）。
            timeout (int, optional): 超时时间（毫秒），默认为None（非阻塞）。

        Returns:
            Union[Request, None]: 请求对象，如果没有有效请求则返回None。

        Raises:
            Exception: 如果没有配置和绑定套接字。

        Notes:
            如果timeout > 0，循环等待直到超时。否则非阻塞调用_accept_request。

        ==========================================
        Check for request within the specified timeout.

        Args:
            unit_addr_list (Optional[list], optional): List of allowed unit addresses, default None (accept all).
            timeout (int, optional): Timeout in milliseconds, default None (non-blocking).

        Returns:
            Union[Request, None]: A request object, or None if no valid request.

        Raises:
            Exception: If no socket is configured and bound.

        Notes:
            If timeout > 0, loops until timeout. Otherwise non-blocking call to _accept_request.
        """
        if self._sock is None:
            raise Exception('Modbus TCP server not bound')

        if timeout > 0:
            start_ms = time.ticks_ms()
            elapsed = 0
            while True:
                if self._client_sock is None:
                    accept_timeout = None if timeout is None else (timeout - elapsed) / 1000
                else:
                    accept_timeout = 0
                req = self._accept_request(accept_timeout, unit_addr_list)
                if req:
                    return req
                elapsed = time.ticks_diff(start_ms, time.ticks_ms())
                if elapsed > timeout:
                    return None
        else:
            return self._accept_request(0, unit_addr_list)

# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================