# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : ben0i0d
# @File    : cc253x_ttl.py
# @Description : cc253x_ttl驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC BY-NC 4.0"
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
        baud (int): 当前串口波特率。
        channel (int): 当前无线信道。
        panid (int): 当前 PANID。
        seek_time (int): 寻找网络时间（秒）。
        query_interval_ms (int): 查询间隔（毫秒）。

        PREFIX (int): 前导码常量。
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
            读取自定义短地址。
        set_custom_short_addr(short_addr):
            设置自定义短地址。
        send_transparent(data):
            透明模式发送数据。
        send_node_to_coord(data):
            节点向协调器发送数据。
        send_coord_to_node(short_addr, data):
            协调器向节点发送数据。
        send_node_to_node(source_addr, target_addr, data):
            节点向节点发送数据。
        recv_frame():
            接收并解析一帧。

    ==========================================

    CC253x TTL driver class supporting ZigBee control and transparent transmission,  
    operating via UART interface.  
    Provides configuration of PANID, channel, baud rate, short address,  
    query interval, sleep mode, and more.  
    Supports point-to-point communication between coordinator and nodes,  
    as well as transparent transmission mode with frame parsing support.  

    Attributes:
    _uart (UART): MicroPython UART instance, used for communicating with the CC253x module.
    baud (int): Current UART baud rate.
    channel (int): Current wireless channel.
    panid (int): Current PANID.
    seek_time (int): Network seeking time (seconds).
    query_interval_ms (int): Query interval (milliseconds).

    PREFIX (int): Preamble constant.
    DEFAULT_*: Default parameter constants (baud rate/channel/PANID/query interval, etc.).
    MAX_USER_PAYLOAD (int): Maximum user data length.
    TX_POST_DELAY_MS (int): Transmission delay after sending (milliseconds).
    SHORTADDR_COORDINATOR (int): Coordinator short address (0x0000).
    SHORTADDR_NOT_JOINED (int): Short address when not joined to network (0xFFFE).

    Methods:
        __init__(uart, role, ...):
            Initializes the driver class, sets up UART and default parameters.
        read_status():
            Queries whether the module has joined the network.
        set_query_interval(ms):
            Sets the query interval.
        reset_factory():
            Restores factory settings.
        read_panid_channel():
            Reads the PANID and channel.
        set_panid(panid):
            Sets the PANID.
        set_baud(baud_idx):
            Sets the baud rate index.
        set_seek_time(seconds):
            Sets the network seeking time.
        enter_sleep():
            Requests the module to enter sleep mode.
        read_mac():
            Reads the MAC address.
        read_short_addr():
            Reads the custom short address.
        set_custom_short_addr(short_addr):
            Sets the custom short address.
        send_transparent(data):
            Sends data in transparent mode.
        send_node_to_coord(data):
            Sends data from a node to the coordinator.
        send_coord_to_node(short_addr, data):
            Sends data from the coordinator to a node.
        send_node_to_node(source_addr, target_addr, data):
            Sends data from one node to another node.
        recv_frame():
            Receives and parses a frame.
    """

    # 前导与控制码
    PREFIX = const("02A879C3")  # 示例：也可用 bytes 表示
    # 默认值（const)
    DEFAULT_BAUD = const(9600)
    DEFAULT_CHANNEL = const(0x0B)
    DEFAULT_PANID = const(0xFFFF)
    DEFAULT_SEEK_TIME = const(10)  # 秒
    DEFAULT_QUERY_MS = const(3000)  # ms (3s)

    # 限制
    MAX_USER_PAYLOAD = const(32)  # 驱动强制最大用户数据长度（字节）
    TX_POST_DELAY_MS = const(100)  # 发送后延时（ms）

    # 特殊短地址
    SHORTADDR_COORDINATOR = const(0x0000)  # 协调器短地址始终 0x0000
    SHORTADDR_NOT_JOINED = const(0xFFFE)  # 表示未加入网络（驱动层约定）

    def __init__(self, uart, wake=None, baud=DEFAULT_BAUD, channel=DEFAULT_CHANNEL, panid=DEFAULT_PANID,
                 seek_time=DEFAULT_SEEK_TIME, query_interval_ms=DEFAULT_QUERY_MS):
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

    # 私有辅助方法
    def _send(self, cmd):
        """
        私有方法：发送 AT 命令并等待响应，直到收到 OK 或 ERROR。  

        Args:
            cmd (str): 完整的 AT 命令字符串。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)，True 表示成功，False 表示失败。

        Raises:
            CommandFailedError:设备未响应

        ==========================================
        Private method: Send an AT command and wait for response until OK or ERROR.  

        Args:
            cmd (str): Full AT command string.  

        Returns:
            Tuple[bool, str]: (status, response), True if success, False otherwise.

        Raises:
            CommandFailedError: Device not responding。

        """
        cmd = self.PREFIX + cmd
        self._uart.write(bytes.fromhex(cmd))
        time.sleep(0.05)
        if self._uart.any():
            resp = self._uart.read()
            tag = resp[4]
            resp = resp[5:]
            resp_hex = resp.hex()
            if tag in [1, 5, 12, 11, 14, 15,10]:
                return True, resp_hex
            else:
                if resp_hex == "4f4b":
                    return True, "success"
                elif resp_hex == "4552":
                    return False, "failure"
                raise CommandFailedError(f"Device not responding tag:{tag}")
        else:
            return False, 'No response from UART'

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
        status_map = {
            '02': 'Device has not joined the network',
            '06': 'EndDevice has joined the network',
            '07': 'Router has joined the network',
            '08': 'Coordinator is starting',
            '09': 'Coordinator has started'
        }
        status_code = self._send('01')[1]
        try:
            # 判断并返回状态
            if status_code in status_map:
                print(status_map[status_code])
                return status_code
            else:
                raise InvalidParameterError(f"Unknown status (Status code: {status_code})")
        except InvalidParameterError:
            return None

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

        ---
        Read PANID and channel.

        Returns:
            tuple[int, int]: (PANID, channel).

        """
        # 读取前清空 UART 缓冲区
        resp = self._uart.read()
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
            return self._send('06' + f'{baud_idx:02d}')[0]
        else:
            raise InvalidParameterError("baud index must be 0..4")


    def enter_lowpower(self) -> bool:
        """
        请求进入休眠模式。

        Returns:
            bool: 成功返回 True。

        ---
        Request sleep mode.

        Returns:
            bool: True if success.

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
        设置信道

        Args:
            channel (int): (0x0b-0x1a)

        Returns:
            bool: 成功返回 True。

        Raises:
            InvalidParameterError: 超出范围。
        ---
        Set network seek time.

        Args:
            channel (int): (0x0b-0x1a)

        Returns:
            bool: True if success.

        Raises:panid
            InvalidParameterError: If parameter is out of range.
        """
        if not channel in range(0x0b, 0x1a, 1):
            raise InvalidParameterError(f"channel must be [0x0b,0x1a,1]，channel={channel}！")
        return self._send('09' + f'{channel:02X}')[0]

    def send_node_to_coord(self, data: str) -> None:
        """
        节点发送数据到协调器。

        Args:
            data (bytes): 数据，长度 ≤ MAX_USER_PAYLOAD。

        ---
        Node sends data to coordinator.

        Args:
            data (bytes): Data, length ≤ MAX_USER_PAYLOAD.

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

        ---
        Coordinator sends data to node.

        Args:
            short_addr (int): Destination short address.
            data (bytes): Data, length ≤ MAX_USER_PAYLOAD.

        Raises:
            InvalidParameterError: If address is out of range.
        """
        if not (0 <= short_addr <= 0xFFFF):
            raise InvalidParameterError("short_addr out of range 0..65535")
        return self._send('0B' + f'{short_addr:04X}' + data.encode("utf-8").hex())[0]

    def read_mac(self) -> str:
        """
        读取 MAC 地址。

        Returns:
            bytes: 8 字节 MAC 地址。

        ---
        Read MAC address.

        Returns:
            bytes: 8-byte MAC address.
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

        ---
        Set custom short address.

        Args:
            short_addr (int): Short address (0–0xFFFF).

        Returns:
            bool: True if success.

        Raises:
            InvalidParameterError: If parameter is out of range.

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

        ---
        Read short address.

        Returns:
            int: 16-bit short address, or SHORTADDR_NOT_JOINED.

        """
        return self._send('0E')[1]

    def send_node_to_node(self, source_addr: int, target_addr:int, data: str) -> None:
        """
        节点发送数据到节点。

        Args:
            source_addr (int): 目标短地址。
            target_addr (int): 源短地址。
            data (bytes): 数据

        Raises:
            InvalidParameterError: 地址超出范围。

        ---
        The node sends data to another node.

        Args:
        source_addr (int): The target short address.
        target_addr (int): The source short address.
        data (bytes): The data

        Raises:
        InvalidParameterError: Address is out of range.

        """
        if not (0 <= source_addr <= 0xFFFF):
            raise InvalidParameterError("source_addr out of range 0..65535")
        if not (0 <= target_addr <= 0xFFFF):
            raise InvalidParameterError("target_addr out of range 0..65535")
        self._send('0F' + f'{source_addr:04X}' + f'{target_addr:04X}' + data.encode("utf-8").hex())

    # 点对点 / 透明数据发送（长度限制与延时）
    def send_transparent(self, data: bytes) -> None:
        """
        透明模式发送数据。
        Args:
            data (bytes): 数据

        ---
        Send transparent data.
        Args:
            data (bytes): Data
        """

        self._uart.write(data)


    def recv_frame(self):
        """
        接收并解析一帧数据。

        Returns:
            tuple: (mode, data, addr1, addr2)
                mode (str): 'transparent', 'node_to_node', 'node_to_coord', 'coord_to_node'
                data (bytes): 接收到的数据
                addr1 (str|None): 目的地址（如适用）
                addr2 (str|None): 源地址（如适用）
        Raises:
            CommandFailedError: 不支持的命令解析。
        ---
        Receive and parse one frame.
         Returns:
            tuple: (mode, data, addr1, addr2)
                mode (str): 'transparent', 'node_to_node', 'node_to_coord', 'coord_to_node'
                data (bytes): Received data
                addr1 (str|None): Destination address (if applicable)
                addr2 (str|None): Source address (if applicable)
        Raises:
            CommandFailedError: Unsupported command for parsing.

        """
        # 前导码
        header = '02a879c3'
        mode =None
        data = None
        addr1 = None
        addr2 = None

        if self._uart.any() != 0:
            # 读取数据
            data = self._uart.read()
            # 检查前导，无前导则透明传输
            if data[0:4].hex() != header:
                mode = 'transparent'
                return mode, data, addr1, addr2
            else:
                # 读取控制码
                cmd = data[4:5].hex()
                # 点对点解析
                if cmd == '0f':
                    mode = 'node_to_node'
                    # 目的地址
                    addr1 = data[5:7].hex()
                    # 源地址
                    addr2 = data[7:9].hex()
                    # 数据
                    data = data[9:len(data)]
                    return mode, data, addr1, addr2
                # 节点到协调器解析
                if cmd == '0a':
                    mode = 'node_to_coord'
                    # 协调器地址
                    addr1 = data[5:7].hex()
                    # 数据
                    data = data[7:len(data)]
                    return mode, data, addr1, addr2
                # 协调器到节点解析
                if cmd == '0b':
                    mode = 'coord_to_node'
                    data = data[5:len(data)]
                    return mode, data, addr1, addr2
                raise CommandFailedError(f'Command {cmd} not supported for parsing')
        else:
            return mode, data, addr1, addr2

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================



