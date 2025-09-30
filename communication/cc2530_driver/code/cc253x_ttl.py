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
import binascii
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
    PREFIX = const("02A879C3")   # 示例：也可用 bytes 表示

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

    def __init__(self, uart, wake=None,baud=DEFAULT_BAUD,channel=DEFAULT_CHANNEL, panid=DEFAULT_PANID,seek_time=DEFAULT_SEEK_TIME, query_interval_ms=DEFAULT_QUERY_MS):
        """
        uart: 已初始化的 UART 实例（driver 只使用其 read/write）
        wake: 只有enddevice需要
        role: CC253xTTL.ROLE_*
        其余为默认值，驱动会在 __init__ 时将 UART 波特率设置为 baud（如果需要）
        """

        self._uart = uart
        self._wake = wake
        self.baud = baud
        self.channel = channel
        self.panid = panid
        self.seek_time = seek_time
        self.query_interval_ms = query_interval_ms

        # 内部接收缓冲
        self._recv_buf = bytearray()
        self._ensure_recv_buffer_capacity()

    # 私有辅助方法
    def _send(self, cmd):
        """
        私有方法：发送 AT 命令并等待响应，直到收到 OK 或 ERROR。  

        Args:
            cmd (str): 完整的 AT 命令字符串。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)，True 表示成功，False 表示失败。  

        ==========================================
        Private method: Send an AT command and wait for response until OK or ERROR.  

        Args:
            cmd (str): Full AT command string.  

        Returns:
            Tuple[bool, str]: (status, response), True if success, False otherwise.
        """
        cmd = self.PREFIX + cmd
        self._uart.write(bytes.fromhex(cmd))
        time.sleep(0.05)
        if self._uart.any():
            resp = self._uart.read()
            tag = resp[4]
            resp = resp[5:]
            resp_hex = resp.hex()
            if tag in [1, 5, 12, 14]:
                return True, resp_hex
            else:
                if resp_hex == "4f4b":
                    return True, "success"
                elif resp_hex == "4552":
                    return False, "failure"
        else:
            return False, 'No response from UART'

    def _recv(self):
        """
        私有方法：发送 AT 命令并等待响应，直到收到 OK 或 ERROR。  

        Args:
            cmd (str): 完整的 AT 命令字符串。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)，True 表示成功，False 表示失败。  

        ==========================================
        Private method: Send an AT command and wait for response until OK or ERROR.  

        Args:
            cmd (str): Full AT command string.  

        Returns:
            Tuple[bool, str]: (status, response), True if success, False otherwise.
        """
        if self._uart.any():
            resp = self._uart.read()[7:].decode('utf-8')
            return True, resp

    # 公共设置与查询 API
    def read_status(self) -> str:
        """
        查询入网状态。
        02：设备没有加入网络
        06：EndDevice已经入网
        07：Router已经入网
        08：Coordiator正在启动
        09：Coordinator已经启动

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
        return self._send('01')[1]
    
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
        return self._send('02' + f'{ms:04X}')[0]
    
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
        return self._send('03')[0]

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
        return self._send('02' + f'{panid:04X}')[0]

    def read_panid_channel(self) -> tuple[str, str]:
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
        resp = self._send('05')[1]
        return resp[:4], resp[4:]
    
    def set_baud(self, baud_idx: int) -> bool:
        """
        设置串口波特率索引。

        Args:
            baud_idx (int): 波特率索引（0–4）。
        00：9600
        01：19200
        02：38400
        03：57600
        04：115200

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
        if baud_idx in range(5):
            raise InvalidParameterError("baud index must be 0..4")
        return self._send('06' + f'{i:02d}')[0]

    def enter_lowpower(self) -> bool:
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
        return self._send('07')[0]

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
        return self._send('08' + f'{seconds:02X}')[0]
        
    def set_channel(self, channel: int) -> bool:
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

        Raises:panid
            InvalidParameterError: If parameter is out of range.
            CommandFailedError: If module returns ERR or times out.
        """
        if not channel in range(2405,2485,5):
            raise InvalidParameterError("channel must be [2405,2480,5]")
        return self._send('09' + f'{channel:02X}')[0]

    def send_node_to_coord(self, data: str) -> None:
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
        self._send('0A' + data.encode('utf-8').hex())

    def send_coord_to_node(self, short_addr: int, data: str) -> None:
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
        if not (0 <= short_addr <= 0xFFFF):
            raise InvalidParameterError("short_addr out of range 0..65535")
        return self._send('0B' + f'{short_addr:04X}' + data.encode("utf-8").hex())[0]

    def read_mac(self) -> str:
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
        return self._send('0C')[1]

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
            raise InvalidParameterError("short_addr out of range 0..65535")
        return self._send('0D' + f'{short_addr:04X}')

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
        return self._send('0E')[1]
    
    def send_node_to_node(self, source_addr: int, target_addr, data: str) -> None:
        """
        节点发送数据到节点。

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
        if not (0 <= source_addr <= 0xFFFF):
            raise InvalidParameterError("source_addr out of range 0..65535")
        if not (0 <= target_addr <= 0xFFFF):
            raise InvalidParameterError("target_addr out of range 0..65535")
        self._send('0F' + f'{target_addr:04X}' + f'{source_addr:04X}' + data.encode("utf-8").hex())

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
    

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
