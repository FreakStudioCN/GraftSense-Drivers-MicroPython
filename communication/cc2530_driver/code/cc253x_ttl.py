# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : ben0i0d
# @File    : hc14_lora.py
# @Description : hc14_lora驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC YB-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CC253xError(Exception):
    """
    CC253x 模块相关的基础异常类，所有自定义异常均继承自此类。  

    Base exception class for CC253x module.  
    All custom exceptions are derived from this class.
    """
    pass


class PacketTooLargeError(CC253xError):
    """
    当发送的数据包超过 CC253x 模块支持的最大负载时抛出。  

    Raised when the packet size exceeds the maximum supported payload of CC253x.
    """
    pass


class CommandFailedError(CC253xError):
    """
    当 CC253x 模块返回 ERR 或命令执行失败时抛出。  

    Raised when CC253x module returns ERR or a command execution fails.
    """
    pass


class NotJoinedError(CC253xError):
    """
    当尝试在未入网状态下执行需要网络的操作时抛出。  

    Raised when an operation requiring network join is attempted but the module is not joined.
    """
    pass


class InvalidParameterError(CC253xError):
    """
    当提供给 CC253x 模块的参数不合法或超出范围时抛出。  

    Raised when an invalid or out-of-range parameter is provided to CC253x module.
    """
    pass


class CC253xTTL:
    """
    CC253x TTL 模块驱动类，支持 ZigBee 通信控制与透明传输，基于 UART 接口进行通信。  
    提供 PANID、信道、波特率、短地址、查询间隔、休眠等参数配置接口，  
    支持协调器与节点之间点对点数据收发，  
    并提供透明数据传输模式与接收帧解析机制。  

    Attributes:
        _uart (UART): MicroPython UART 实例，用于与 CC253x 模块通信。
        role (int): 当前模块角色（协调器/路由器/终端，使用 ROLE 常量）。
        baud (int): 当前串口波特率。
        channel (int): 当前无线信道。
        panid (int): 当前 PANID。
        seek_time (int): 寻找网络时间（秒）。
        query_interval_ms (int): 查询间隔（毫秒）。
        _recv_buf (bytearray): 内部接收缓冲区。

        PREFIX (int): 前导码常量。
        PREFIX_BYTES (bytes): 前导码字节序列。
        CMD_* (int): 控制命令常量。
        RESP_OK (bytes): 模块返回 OK 响应。
        RESP_ERR (bytes): 模块返回 ERR 响应。
        ROLE_COORDINATOR / ROLE_ROUTER / ROLE_ENDDEVICE (int): 角色常量。
        DEFAULT_*: 默认参数常量（波特率/信道/PANID/查询间隔等）。
        MAX_USER_PAYLOAD (int): 最大用户数据长度。
        TX_POST_DELAY_MS (int): 发送后延时（毫秒）。
        SHORTADDR_COORDINATOR (int): 协调器短地址（0x0000）。
        SHORTADDR_NOT_JOINED (int): 未入网时的短地址（0xFFFE）。

    Methods:
        __init__(uart, role, ...):
            初始化驱动类，设置 UART 与默认参数。
        read_status():
            查询模块是否已入网。
        set_query_interval(ms):
            设置查询间隔。
        reset_factory():
            恢复出厂设置。
        read_panid_channel():
            读取 PANID 与信道。
        set_panid(panid):
            设置 PANID。
        set_baud(baud_idx):
            设置波特率索引。
        set_seek_time(seconds):
            设置寻找网络时间。
        enter_sleep():
            请求模块进入休眠。
        read_mac():
            读取 MAC 地址。
        read_short_addr():
            读取短地址。
        is_joined():
            判断是否已入网。
        set_custom_short_addr(short_addr):
            设置自定义短地址。
        read_custom_short_addr():
            读取自定义短地址。
        send_transparent(data):
            透明模式发送数据。
        send_node_to_coord(data):
            节点向协调器发送数据。
        send_coord_to_node(short_addr, data):
            协调器向节点发送数据。
        send_custom_addr(dst_short, src_short, data):
            使用自定义源/目的地址发送数据。
        recv_frame(timeout_ms):
            接收并解析一帧。
        _uart_write_raw(frame):
            UART 写入底层方法。
        _uart_read_raw():
            UART 读取底层方法。
        _ensure_recv_buffer_capacity():
            确保接收缓冲区容量充足。
        _process_receive_buffer():
            解析缓冲区中的数据帧。
        _frame_expected_length(ctrl, header_bytes):
            计算期望帧长度。
        _validate_payload_length(payload):
            校验负载长度是否合法。
        _send_cmd_expect_ok(cmd, payload, timeout_ms):
            发送命令并等待 OK 响应。
        _wait_for_response(expected_cmd, timeout_ms):
            等待并返回指定命令的响应帧。

    ==========================================

    CC253x TTL driver class supporting ZigBee control and transparent transmission,  
    operating via UART interface.  
    Provides configuration of PANID, channel, baud rate, short address,  
    query interval, sleep mode, and more.  
    Supports point-to-point communication between coordinator and nodes,  
    as well as transparent transmission mode with frame parsing support.  

    Attributes:
        _uart (UART): MicroPython UART instance for CC253x communication.
        role (int): Current module role (Coordinator/Router/EndDevice).
        baud (int): Current UART baud rate.
        channel (int): Current RF channel.
        panid (int): Current PANID.
        seek_time (int): Network seeking time in seconds.
        query_interval_ms (int): Query interval in milliseconds.
        _recv_buf (bytearray): Internal receive buffer.

        PREFIX (int): Preamble constant.
        PREFIX_BYTES (bytes): Preamble as bytes.
        CMD_* (int): Command constants.
        RESP_OK (bytes): OK response constant.
        RESP_ERR (bytes): ERR response constant.
        ROLE_COORDINATOR / ROLE_ROUTER / ROLE_ENDDEVICE (int): Role constants.
        DEFAULT_*: Default parameter constants (baud, channel, PANID, etc.).
        MAX_USER_PAYLOAD (int): Maximum user payload length.
        TX_POST_DELAY_MS (int): Post-transmission delay in milliseconds.
        SHORTADDR_COORDINATOR (int): Coordinator short address (0x0000).
        SHORTADDR_NOT_JOINED (int): Not-joined short address (0xFFFE).

    Methods:
        __init__(uart, role, ...):
            Initialize driver with UART and default params.
        read_status():
            Query join status.
        set_query_interval(ms):
            Set query interval.
        reset_factory():
            Restore factory settings.
        read_panid_channel():
            Read PANID and channel.
        set_panid(panid):
            Set PANID.
        set_baud(baud_idx):
            Set baud rate index.
        set_seek_time(seconds):
            Set network seeking time.
        enter_sleep():
            Request module to sleep.
        read_mac():
            Read MAC address.
        read_short_addr():
            Read short address.
        is_joined():
            Check if module has joined a network.
        set_custom_short_addr(short_addr):
            Set custom short address.
        read_custom_short_addr():
            Read custom short address.
        send_transparent(data):
            Send data in transparent mode.
        send_node_to_coord(data):
            Node sends data to coordinator.
        send_coord_to_node(short_addr, data):
            Coordinator sends data to node.
        send_custom_addr(dst_short, src_short, data):
            Send data with custom source/destination address.
        recv_frame(timeout_ms):
            Receive and parse one frame.
        _uart_write_raw(frame):
            Low-level UART write.
        _uart_read_raw():
            Low-level UART read.
        _ensure_recv_buffer_capacity():
            Ensure receive buffer capacity.
        _process_receive_buffer():
            Parse frames from buffer.
        _frame_expected_length(ctrl, header_bytes):
            Compute expected frame length.
        _validate_payload_length(payload):
            Validate payload length.
        _send_cmd_expect_ok(cmd, payload, timeout_ms):
            Send command and wait for OK.
        _wait_for_response(expected_cmd, timeout_ms):
            Wait for and return response frame.
    """

    # 前导与控制码
    PREFIX = const(0x02A879C3)   # 示例：也可用 bytes 表示
    PREFIX_BYTES = b'\x02\xA8\x79\xC3'

    # 控制码
    CMD_STATUS                   = const(0x01)
    CMD_SET_QUERY_INTERVAL       = const(0x02)
    CMD_FACTORY_RESET            = const(0x03)
    CMD_SET_PANID                = const(0x04)
    CMD_READ_PANID_CHANNEL       = const(0x05)
    CMD_SET_BAUD                 = const(0x06)
    CMD_SLEEP                    = const(0x07)
    CMD_SET_SEEK_TIME            = const(0x08)
    CMD_SET_CHANNEL              = const(0x09)

    # 点对点控制码
    CMD_P2P_NODE_TO_COORD        = const(0x0A)
    CMD_P2P_COORD_TO_NODE        = const(0x0B)
    CMD_READ_MAC                 = const(0x0C)
    CMD_SET_CUSTOM_SHORT         = const(0x0D)
    CMD_READ_CUSTOM_SHORT        = const(0x0E)
    CMD_P2P_CUSTOM_ADDR          = const(0x0F)

    # 返回码（字节对），模块用 '4F 4B' 表示 OK，'45 52' 表示 ERR
    RESP_OK                      = b'OK'   # b'\x4F\x4B'
    RESP_ERR                     = b'ER'   # b'\x45\x52'

    # 身份（ROLE）
    ROLE_COORDINATOR = const(0x00)
    ROLE_ROUTER      = const(0x01)
    ROLE_ENDDEVICE   = const(0x02)

    # 默认值（const）
    DEFAULT_BAUD         = const(9600)
    DEFAULT_CHANNEL      = const(0x0B)
    DEFAULT_PANID        = const(0xFFFF)
    DEFAULT_SEEK_TIME    = const(10)    # 秒
    DEFAULT_QUERY_MS     = const(3000)  # ms (3s)

    # 限制
    MAX_USER_PAYLOAD     = const(32)    # 驱动强制最大用户数据长度（字节）
    TX_POST_DELAY_MS     = const(100)   # 发送后延时（ms）

    # 特殊短地址
    SHORTADDR_COORDINATOR = const(0x0000)  # 协调器短地址始终 0x0000
    SHORTADDR_NOT_JOINED  = const(0xFFFE)  # 表示未加入网络（驱动层约定）

    def __init__(self, uart, role, baud=DEFAULT_BAUD,channel=DEFAULT_CHANNEL, panid=DEFAULT_PANID,seek_time=DEFAULT_SEEK_TIME, query_interval_ms=DEFAULT_QUERY_MS):
        """
        uart: 已初始化的 UART 实例（driver 只使用其 read/write）
        role: CC253xTTL.ROLE_*
        其余为默认值，驱动会在 __init__ 时将 UART 波特率设置为 baud（如果需要）
        """

        self._uart = uart
        self.role = role
        self.baud = baud
        self.channel = channel
        self.panid = panid
        self.seek_time = seek_time
        self.query_interval_ms = query_interval_ms

        # 内部接收缓冲
        self._recv_buf = bytearray()
        self._ensure_recv_buffer_capacity()

        

    # 公共设置与查询 API
    def read_status(self) -> int:
        """
        查询入网状态。

        Returns:
            int: 入网状态码（来自模块返回的 1 字节值）。

        Raises:
            CommandFailedError: 响应超时或返回 ERR。

        ---
        Query join status.

        Returns:
            int: Join status code (1-byte value from module response).

        Raises:
            CommandFailedError: If response times out or returns ERR.
        """
        # 发送状态查询命令（CMD_STATUS），期待 payload 为 1 字节状态码或包含在回复 payload 里
        frame = self.PREFIX_BYTES + bytes([self.CMD_STATUS, 0x00])  # ctrl, len=0
        self._uart_write_raw(frame)
        resp = self._wait_for_response(self.CMD_STATUS, timeout_ms=500)
        # 解析：若 payload 长度 >=1，返回第一个字节作为状态
        payload = resp.get('data', b'')
        if len(payload) >= 1:
            return int(payload[0])
        # 若没有 payload，但 raw 含有 OK，则返回 0 表示 OK / unknown
        return 0
    
    def set_query_interval(self, ms: int) -> bool:
        """
        设置查询间隔。

        Args:
            ms (int): 查询间隔（0–65535 毫秒）。

        Returns:
            bool: 成功返回 True。

        Raises:
            InvalidParameterError: 参数超出范围。
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Set query interval.

        Args:
            ms (int): Query interval (0–65535 ms).

        Returns:
            bool: True if success.

        Raises:
            InvalidParameterError: If parameter is out of range.
            CommandFailedError: If module returns ERR or times out.
        """
        if not (0 <= ms <= 0xFFFF):
            raise InvalidParameterError("query interval out of range 0..65535")
        payload = bytes([(ms >> 8) & 0xFF, ms & 0xFF])
        return self._send_cmd_expect_ok(self.CMD_SET_QUERY_INTERVAL, payload)
    
    def reset_factory(self) -> bool:
        """
        恢复出厂设置。

        Returns:
            bool: 成功返回 True。

        Raises:
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Restore factory settings.

        Returns:
            bool: True if success.

        Raises:
            CommandFailedError: If module returns ERR or times out.
        """
        # CMD_FACTORY_RESET 无负载
        res = self._send_cmd_expect_ok(self.CMD_FACTORY_RESET, b'')
        # Note: 对 Coordinator 会导致 PANID 变更/节点清空，调用方需处理
        return res
            
    def read_panid_channel(self) -> tuple[int, int]:
        """
        读取 PANID 与信道。

        Returns:
            tuple[int, int]: (PANID, 信道)。

        Raises:
            CC253xError: 返回数据无效。
            CommandFailedError: 响应超时或返回 ERR。

        ---
        Read PANID and channel.

        Returns:
            tuple[int, int]: (PANID, channel).

        Raises:
            CC253xError: If invalid response is received.
            CommandFailedError: If response times out or returns ERR.
        """
        # 发送读取 PANID/CHANNEL 命令，期望 payload = panid_hi panid_lo channel
        self._uart_write_raw(bytes(self.PREFIX_BYTES) + bytes([self.CMD_READ_PANID_CHANNEL, 0x00]))
        resp = self._wait_for_response(self.CMD_READ_PANID_CHANNEL, timeout_ms=500)
        payload = resp.get('data', b'')
        if len(payload) >= 3:
            panid = (payload[0] << 8) | payload[1]
            channel = payload[2]
            return (panid, channel)
        raise CC253xError("Invalid response for PANID/CHANNEL")
    
    def set_panid(self, panid: int) -> bool:
        """
        设置 PANID。

        Args:
            panid (int): PANID (0–0xFFFF)。

        Returns:
            bool: 成功返回 True。

        Raises:
            InvalidParameterError: PANID 超出范围。
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Set PANID.

        Args:
            panid (int): PANID (0–0xFFFF).

        Returns:
            bool: True if success.

        Raises:
            InvalidParameterError: If PANID is out of range.
            CommandFailedError: If module returns ERR or times out.
        """
        if not (0 <= panid <= 0xFFFF):
            raise InvalidParameterError("panid must be 0..0xFFFF")
        payload = bytes([(panid >> 8) & 0xFF, panid & 0xFF])
        return self._send_cmd_expect_ok(self.CMD_SET_PANID, payload)
        
    def set_baud(self, baud_idx: int) -> bool:
        """
        设置串口波特率索引。

        Args:
            baud_idx (int): 波特率索引（0–4）。

        Returns:
            bool: 成功返回 True。

        Raises:
            InvalidParameterError: 索引超出范围。
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Set UART baud rate index.

        Args:
            baud_idx (int): Baud rate index (0–4).

        Returns:
            bool: True if success.

        Raises:
            InvalidParameterError: If index is out of range.
            CommandFailedError: If module returns ERR or times out.
        """
        if not (0 <= baud_idx <= 4):
            raise InvalidParameterError("baud index must be 0..4")
        payload = bytes([baud_idx])
        return self._send_cmd_expect_ok(self.CMD_SET_BAUD, payload)
    
    def set_seek_time(self, seconds: int) -> bool:
        """
        设置寻找网络时间。

        Args:
            seconds (int): 秒数（1–65）。

        Returns:
            bool: 成功返回 True。

        Raises:
            InvalidParameterError: 超出范围。
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Set network seek time.

        Args:
            seconds (int): Seconds (1–65).

        Returns:
            bool: True if success.

        Raises:
            InvalidParameterError: If parameter is out of range.
            CommandFailedError: If module returns ERR or times out.
        """
        if not (1 <= seconds <= 65):
            raise InvalidParameterError("seek time must be 1..65 seconds")
        payload = bytes([seconds])
        return self._send_cmd_expect_ok(self.CMD_SET_SEEK_TIME, payload)
        
    def enter_sleep(self) -> bool:
        """
        请求进入休眠模式。

        Returns:
            bool: 成功返回 True。

        Raises:
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Request sleep mode.

        Returns:
            bool: True if success.

        Raises:
            CommandFailedError: If module returns ERR or times out.
        """
        return self._send_cmd_expect_ok(self.CMD_SLEEP, b'')

    def read_mac(self) -> bytes:
        """
        读取 MAC 地址。

        Returns:
            bytes: 8 字节 MAC 地址。

        Raises:
            CC253xError: 数据长度不足。
            CommandFailedError: 响应超时或返回 ERR。

        ---
        Read MAC address.

        Returns:
            bytes: 8-byte MAC address.

        Raises:
            CC253xError: If response payload is too short.
            CommandFailedError: If response times out or returns ERR.
        """
        self._uart_write_raw(bytes(self.PREFIX_BYTES) + bytes([self.CMD_READ_MAC, 0x00]))
        resp = self._wait_for_response(self.CMD_READ_MAC, timeout_ms=500)
        payload = resp.get('data', b'')
        if len(payload) >= 8:
            return bytes(payload[:8])
        raise CC253xError("Invalid MAC read response")
    
    # 短地址与入网判断
    def read_short_addr(self) -> int:
        """
        读取短地址。

        Returns:
            int: 16 位短地址，或 SHORTADDR_NOT_JOINED。

        Raises:
            CommandFailedError: 响应超时或返回 ERR。

        ---
        Read short address.

        Returns:
            int: 16-bit short address, or SHORTADDR_NOT_JOINED.

        Raises:
            CommandFailedError: If response times out or returns ERR.
        """
        # 这里假定 read_custom_short_addr 或另一个命令返回短地址字段；如果设备有独立命令，请替换 CMD
        # 先尝试用读取自定义短地址命令（若设备使用其他命令读取短地址，请调整）
        self._uart_write_raw(bytes(self.PREFIX_BYTES) + bytes([self.CMD_READ_CUSTOM_SHORT, 0x00]))
        resp = self._wait_for_response(self.CMD_READ_CUSTOM_SHORT, timeout_ms=500)
        payload = resp.get('data', b'')
        if len(payload) >= 2:
            return (payload[0] << 8) | payload[1]
        # 兜底：若没有返回，用 NOT_JOINED 表示
        return self.SHORTADDR_NOT_JOINED
    
    def is_joined(self) -> bool:
        """
        判断是否已入网。

        Returns:
            bool: True 表示已入网，False 表示未入网。

        ---
        Check if joined.

        Returns:
            bool: True if joined, False otherwise.
        """
        sa = self.read_short_addr()
        return sa != self.SHORTADDR_NOT_JOINED
    
    def set_custom_short_addr(self, short_addr: int) -> bool:
        """
        设置自定义短地址。

        Args:
            short_addr (int): 短地址（0–0xFFFF）。

        Returns:
            bool: 成功返回 True。

        Raises:
            InvalidParameterError: 超出范围。
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Set custom short address.

        Args:
            short_addr (int): Short address (0–0xFFFF).

        Returns:
            bool: True if success.

        Raises:
            InvalidParameterError: If parameter is out of range.
            CommandFailedError: If module returns ERR or times out.
        """
        if not (0 <= short_addr <= 0xFFFF):
            raise InvalidParameterError("short_addr must be 0..0xFFFF")
        payload = bytes([(short_addr >> 8) & 0xFF, short_addr & 0xFF])
        return self._send_cmd_expect_ok(self.CMD_SET_CUSTOM_SHORT, payload)
    
    def read_custom_short_addr(self) -> int:
        """
        读取自定义短地址。

        Returns:
            int: 自定义短地址，默认 0xFFFF。

        Raises:
            CommandFailedError: 响应超时或返回 ERR。

        ---
        Read custom short address.

        Returns:
            int: Custom short address, default 0xFFFF.

        Raises:
            CommandFailedError: If response times out or returns ERR.
        """
        self._uart_write_raw(bytes(self.PREFIX_BYTES) + bytes([self.CMD_READ_CUSTOM_SHORT, 0x00]))
        resp = self._wait_for_response(self.CMD_READ_CUSTOM_SHORT, timeout_ms=500)
        payload = resp.get('data', b'')
        if len(payload) >= 2:
            return (payload[0] << 8) | payload[1]
        return 0xFFFF
    
    # 点对点 / 透明数据发送（长度限制与延时）
    def send_transparent(self, data: bytes) -> None:
        """
        透明模式发送数据。

        Args:
            data (bytes): 数据，长度 ≤ MAX_USER_PAYLOAD。

        Raises:
            InvalidParameterError: 数据前缀冲突。
            PacketTooLargeError: 数据长度超限。

        ---
        Send transparent data.

        Args:
            data (bytes): Data, length ≤ MAX_USER_PAYLOAD.

        Raises:
            InvalidParameterError: If data begins with PREFIX_BYTES.
            PacketTooLargeError: If data exceeds maximum payload length.
        """
        self._validate_payload_length(data)
        # 避免误触发前导码
        if len(data) >= 4 and data[:4] == self.PREFIX_BYTES:
            raise InvalidParameterError("transparent data begins with PREFIX_BYTES — would be treated as control frame. Escape or change payload.")
        # 直接写入
        self._uart_write_raw(data)
        time.sleep_ms(self.TX_POST_DELAY_MS)

    def send_node_to_coord(self, data: bytes) -> None:
        """
        节点发送数据到协调器。

        Args:
            data (bytes): 数据，长度 ≤ MAX_USER_PAYLOAD。

        Raises:
            PacketTooLargeError: 数据长度超限。

        ---
        Node sends data to coordinator.

        Args:
            data (bytes): Data, length ≤ MAX_USER_PAYLOAD.

        Raises:
            PacketTooLargeError: If data exceeds maximum payload length.
        """
        self._validate_payload_length(data)
        payload = bytes(data)
        frame = self.PREFIX_BYTES + bytes([self.CMD_P2P_NODE_TO_COORD, len(payload)]) + payload + self.RESP_OK  # note: append RESP_OK is harmless for send; module ignores
        self._uart_write_raw(frame)
        time.sleep_ms(self.TX_POST_DELAY_MS)

    def send_coord_to_node(self, short_addr: int, data: bytes) -> None:
        """
        协调器发送数据到指定节点。

        Args:
            short_addr (int): 目标短地址。
            data (bytes): 数据，长度 ≤ MAX_USER_PAYLOAD。

        Raises:
            InvalidParameterError: 地址超出范围。
            PacketTooLargeError: 数据长度超限。

        ---
        Coordinator sends data to node.

        Args:
            short_addr (int): Destination short address.
            data (bytes): Data, length ≤ MAX_USER_PAYLOAD.

        Raises:
            InvalidParameterError: If address is out of range.
            PacketTooLargeError: If data exceeds maximum payload length.
        """
        self._validate_payload_length(data)
        if not (0 <= short_addr <= 0xFFFF):
            raise InvalidParameterError("short_addr out of range")
        payload = bytes([(short_addr >> 8) & 0xFF, short_addr & 0xFF]) + data
        frame = self.PREFIX_BYTES + bytes([self.CMD_P2P_COORD_TO_NODE, len(payload)]) + payload
        self._uart_write_raw(frame)
        time.sleep_ms(self.TX_POST_DELAY_MS)

    def send_custom_addr(self, dst_short: int, src_short: int, data: bytes) -> None:
        """
        使用自定义源/目的短地址发送。

        Args:
            dst_short (int): 目的短地址。
            src_short (int): 源短地址。
            data (bytes): 数据，长度 ≤ MAX_USER_PAYLOAD。

        Raises:
            InvalidParameterError: 地址超出范围。
            PacketTooLargeError: 数据长度超限。

        ---
        Send with custom source/destination addresses.

        Args:
            dst_short (int): Destination short address.
            src_short (int): Source short address.
            data (bytes): Data, length ≤ MAX_USER_PAYLOAD.

        Raises:
            InvalidParameterError: If addresses are out of range.
            PacketTooLargeError: If data exceeds maximum payload length.
        """
        self._validate_payload_length(data)
        for s in (dst_short, src_short):
            if not (0 <= s <= 0xFFFF):
                raise InvalidParameterError("short addresses must be 0..0xFFFF")
        payload = bytes([(dst_short >> 8) & 0xFF, dst_short & 0xFF, (src_short >> 8) & 0xFF, src_short & 0xFF]) + data
        frame = self.PREFIX_BYTES + bytes([self.CMD_P2P_CUSTOM_ADDR, len(payload)]) + payload
        self._uart_write_raw(frame)
        time.sleep_ms(self.TX_POST_DELAY_MS)

    def recv_frame(self, timeout_ms: int = 0) -> dict | None:
        """
        接收并解析一帧数据。

        Args:
            timeout_ms (int, 可选): 超时时间（毫秒，0 表示非阻塞）。

        Returns:
            dict | None: 解析出的帧，或 None 表示超时。

        ---
        Receive and parse one frame.

        Args:
            timeout_ms (int, optional): Timeout in ms (0 = non-blocking).

        Returns:
            dict | None: Parsed frame, or None if timeout.
        """
        # 尝试解析缓冲区，若无完整帧则 _uart_read_raw 并循环等待直到超时或有帧解析出
        deadline = time.ticks_add(time.ticks_ms(), int(timeout_ms))
        while True:
            parsed = self._process_receive_buffer()
            if parsed:
                return parsed.pop(0)
            # 如果 timeout_ms == 0 表示非阻塞，立即返回 None
            if timeout_ms == 0:
                return None
            # 读一些数据并继续
            data = self._uart_read_raw(timeout_ms=50)
            if data:
                self._recv_buf.extend(data)
            if time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                return None
            
    # 私有串口 I/O 与解析相关（必须实现并使用）
    # 所有串口原始读写与解析流程均为私有方法，上层 API 一律调用这些私有方法。
    def _uart_write_raw(self, frame: bytes) -> None:
        """
        UART 底层写入。

        Args:
            frame (bytes): 原始数据帧。

        ---
        Low-level UART write.

        Args:
            frame (bytes): Raw data frame.
        """
        # 尝试兼容 MicroPython / pyserial 等常见接口
        self._uart.write(frame)
        time.sleep_ms(self.TX_POST_DELAY_MS)

    def _uart_read_raw(self) -> bytes:
        """
        UART 底层读取。

        Returns:
            bytes: 读取到的数据，可能为空。

        ---
        Low-level UART read.

        Returns:
            bytes: Data read, may be empty.
        """
        # 兼容多种 UART API：若 MicroPython 风格有 read(n) 或 read()，pyserial read() 等
        # timeout_ms 是本次读操作的超时（尽量短），并返回本次读到的数据（可能为空）
        data = self._uart.read()  # 直接读，不传参数，返回 None 或 bytes
        if data is None:
            return b''
        return data
    
    def _ensure_recv_buffer_capacity(self) -> None:
        """
        确保接收缓冲区存在并可扩展。

        ---
        Ensure receive buffer exists and expandable.
        """
        # 确保接收缓冲为合理大小（这是一个软约束，用于日志/将来扩展）
        if not isinstance(self._recv_buf, (bytearray, bytes)):
            self._recv_buf = bytearray()
        # 无需实际分配到 RECV_BUFFER_SIZE，只要能增长即可

    def _process_receive_buffer(self) -> list[dict]:
        """
        解析接收缓冲区。

        Returns:
            list[dict]: 解析出的帧列表。

        Raises:
            CC253xError: 帧长度不一致或解析错误。

        ---
        Process receive buffer.

        Returns:
            list[dict]: List of parsed frames.

        Raises:
            CC253xError: If frame length mismatch or parse error occurs.
        """
        frames = []
        buf = self._recv_buf

        # 快速搜索前导
        idx = buf.find(self.PREFIX_BYTES)
        if idx == -1:
            # 没有找到前导：如果缓冲为空或很短则返回空，调用方会继续读取
            if len(buf) == 0:
                return []
            # 将所有现有数据当作一个透明帧返回（caller 可能想逐个读取）
            frames.append({'ctrl': 0xFF, 'src_short': None, 'dst_short': None, 'data': bytes(buf), 'raw': bytes(buf)})
            # 清空缓冲区
            del buf[:]
            return frames

        # 丢弃前导前的噪声字节
        if idx > 0:
            del buf[:idx]

        # 现在 buf 以 PREFIX_BYTES 开头
        while True:
            if len(buf) < 6:  # prefix(4)+ctrl(1)+len(1) 最少 6 字节
                break
            # 读取 ctrl 和 len
            ctrl = buf[4]
            plen = buf[5]
            expected = 4 + 1 + 1 + plen + 2  # prefix + ctrl + len + payload + resp(2)
            if len(buf) < expected:
                # 不完整帧，等待更多字节
                break
            # 取出完整帧
            frame_bytes = bytes(buf[:expected])
            # payload 在位置 6:6+plen
            payload = bytes(buf[6:6+plen])
            resp = bytes(buf[6+plen:6+plen+2])
            # 从 payload 按常见布局尝试解析源/目的短地址（如果 ctrl 是点对点类）
            src_short = None
            dst_short = None
            if ctrl in (self.CMD_P2P_COORD_TO_NODE, self.CMD_P2P_NODE_TO_COORD, self.CMD_P2P_CUSTOM_ADDR):
                # 尝试解析头部短地址（若 payload 足够）
                # 对 COORD->NODE: payload 0..1 = dst short
                if ctrl == self.CMD_P2P_COORD_TO_NODE and len(payload) >= 2:
                    dst_short = (payload[0] << 8) | payload[1]
                    data = payload[2:]
                elif ctrl == self.CMD_P2P_NODE_TO_COORD:
                    # 节点->协调器通常没有 dst，src 可能在 payload 开头
                    if len(payload) >= 2:
                        src_short = (payload[0] << 8) | payload[1]
                        data = payload[2:]
                    else:
                        data = payload
                elif ctrl == self.CMD_P2P_CUSTOM_ADDR and len(payload) >= 4:
                    dst_short = (payload[0] << 8) | payload[1]
                    src_short = (payload[2] << 8) | payload[3]
                    data = payload[4:]
                else:
                    data = payload
            else:
                data = payload

            frames.append({
                'ctrl': ctrl,
                'src_short': src_short,
                'dst_short': dst_short,
                'data': bytes(data),
                'raw': frame_bytes,
                'resp': resp
            })
            # 移除已解析的字节
            del buf[:expected]
            # 继续查找下一个前导（若存在）
            idx2 = buf.find(self.PREFIX_BYTES)
            if idx2 == -1:
                # 也可能剩下透明数据（噪声），但我们先退出，等待下一次读取
                break
            if idx2 > 0:
                # 丢弃噪声
                del buf[:idx2]
            # 循环继续
        return frames
    
    def _frame_expected_length(self, ctrl: int, header_bytes: bytes) -> int:
        """
        计算期望帧长度。

        Args:
            ctrl (int): 控制码。
            header_bytes (bytes): 帧头数据。

        Returns:
            int: 期望帧总长度，错误返回 -1。

        ---
        Compute expected frame length.

        Args:
            ctrl (int): Control code.
            header_bytes (bytes): Header bytes.

        Returns:
            int: Expected total frame length, -1 if invalid.
        """
        # header_bytes 包含 ctrl 与 len 字节（或更多）；采用 _process_receive_buffer 使用的相同规则
        if len(header_bytes) < 2:
            return -1
        plen = header_bytes[1]
        return 4 + 1 + 1 + plen + 2
    
    def _validate_payload_length(self, payload: bytes) -> None:
        """
        校验负载长度。

        Args:
            payload (bytes): 负载数据。

        Raises:
            PacketTooLargeError: 数据超出 MAX_USER_PAYLOAD。

        ---
        Validate payload length.

        Args:
            payload (bytes): Payload data.

        Raises:
            PacketTooLargeError: If payload exceeds MAX_USER_PAYLOAD.
        """
        if len(payload) > self.MAX_USER_PAYLOAD:
            raise PacketTooLargeError(f"payload length {len(payload)} exceeds MAX_USER_PAYLOAD {self.MAX_USER_PAYLOAD}")
        
    # 私有辅助方法
    def _send_cmd_expect_ok(self, cmd: int, payload: bytes, timeout_ms: int=500) -> bool:
        """
        发送命令并等待 OK。

        Args:
            cmd (int): 控制码。
            payload (bytes): 命令负载。
            timeout_ms (int, 可选): 超时时间（毫秒）。

        Returns:
            bool: 成功返回 True。

        Raises:
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Send command and expect OK.

        Args:
            cmd (int): Control code.
            payload (bytes): Command payload.
            timeout_ms (int, optional): Timeout in ms.

        Returns:
            bool: True if success.

        Raises:
            CommandFailedError: If module returns ERR or times out.
        """
        
        # 简单同步等待：调用 recv_frame 直到拿到 ctrl == expected_ctrl 或遇到 resp 'ER'/'OK'
        deadline = time.ticks_add(time.ticks_ms(), int(timeout_ms))
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            frame = self.recv_frame(timeout_ms=50)
            if frame is None:
                continue
            # 跳过透明数据
            if frame.get('ctrl') == 0xFF:
                continue
            resp = frame.get('resp', b'')
            if resp == self.RESP_ERR:
                raise CommandFailedError("CMD returned ERR", frame.get('raw'))
            # 明确接受模块的 OK 响应或来自预期 control code 的帧作为成功
            if resp == self.RESP_OK or frame.get('ctrl') == cmd:
                return True
            # 否则继续等待
        raise CommandFailedError("Timeout waiting for response")

    def _wait_for_response(self, expected_cmd: int, timeout_ms: int = 500) -> dict:
        """
        等待并返回响应。

        Args:
            expected_cmd (int): 期望的控制码。
            timeout_ms (int, 可选): 超时时间（毫秒）。

        Returns:
            dict: 响应帧。

        Raises:
            CommandFailedError: 模块返回 ERR 或超时。

        ---
        Wait for response.

        Args:
            expected_cmd (int): Expected control code.
            timeout_ms (int, optional): Timeout in ms.

        Returns:
            dict: Response frame.

        Raises:
            CommandFailedError: If module returns ERR or times out.
        """
        deadline = time.ticks_add(time.ticks_ms(), int(timeout_ms))
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            frame = self.recv_frame(timeout_ms=50)
            if frame is None:
                continue
            # 跳过透明数据
            if frame.get('ctrl') == 0xFF:
                continue
            # 若收到 ERR，则直接抛出
            resp = frame.get('resp', b'')
            if resp == self.RESP_ERR:
                raise CommandFailedError("CMD returned ERR", frame.get('raw'))
            # 匹配期望 control code
            if frame.get('ctrl') == expected_cmd:
                return frame
            # 若不是期望帧，继续循环等待
        raise CommandFailedError("Timeout waiting for response")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
