# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/17 下午2:00
# @Author  : wybiral
# @File    : main.py
# @Description : CH9121串口转网络模块异步驱动，支持TCP/UDP的客户端/服务端模式配置与数据读写，封装了模块的配置指令发送、参数读写、数据透传等核心功能
# @License : MIT

__version__ = "0.1.0"
__author__ = "wybiral"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython异步IO模块，用于异步串口读写操作
import uasyncio as asyncio

# 导入Pin/UART基类用于参数类型验证（MicroPython标准库）
from machine import Pin, UART

# ======================================== 全局变量 ============================================

# CH9121工作模式常量 - TCP服务端模式
TCP_SERVER: int = 0
# CH9121工作模式常量 - TCP客户端模式
TCP_CLIENT: int = 1
# CH9121工作模式常量 - UDP服务端模式
UDP_SERVER: int = 2
# CH9121工作模式常量 - UDP客户端模式
UDP_CLIENT: int = 3

# CH9121支持的波特率列表（参考模块手册）
SUPPORTED_BAUDS: tuple[int, ...] = (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CH9121:
    """
    CH9121串口转网络模块异步驱动类
    提供CH9121模块的工作模式、网络参数（IP/端口/网关/子网掩码）配置，以及异步数据读写功能
    Attributes:
        uart (UART): 与CH9121通信的UART对象，需预先初始化
        cfg (Pin): 配置模式控制引脚对象（Pin类），低电平进入配置模式，高电平退出
        w (asyncio.StreamWriter): asyncio.StreamWriter对象，用于异步写数据到UART
        r (asyncio.StreamReader): asyncio.StreamReader对象，用于异步从UART读数据

    Methods:
        _config(): 私有方法，发送配置指令并读取响应，处理配置模式的引脚切换
        get_mode(): 获取当前工作模式
        get_local_ip(): 获取本地IP地址
        get_subnet_mask(): 获取子网掩码
        get_gateway(): 获取网关地址
        get_local_port(): 获取本地端口号
        get_target_ip(): 获取目标IP地址
        get_target_port(): 获取目标端口号
        set_mode(): 设置工作模式（TCP_SERVER/TCP_CLIENT/UDP_SERVER/UDP_CLIENT）
        set_baud_rate(): 设置串口波特率
        set_local_ip(): 设置本地IP地址
        set_gateway(): 设置网关地址
        set_local_port(): 设置本地端口号
        set_target_ip(): 设置目标IP地址
        set_target_port(): 设置目标端口号
        write(): 异步写入数据到模块
        read(): 异步读取指定长度的数据
        readline(): 异步按行读取数据
        reset(): 重置CH9121模块

    Notes:
        1. 配置模块前需确保cfg引脚拉低进入配置模式，配置完成后拉高退出
        2. 所有配置和读写操作均为异步，需在asyncio事件循环中执行
        3. 网络参数配置后需重启模块生效（可调用reset方法）

    ==========================================
    CH9121 Serial to Network Module Asynchronous Driver Class
    Provides configuration of working mode, network parameters (IP/port/gateway/subnet mask) for CH9121 module, and asynchronous data read/write functions
    Attributes:
        uart (UART): UART object for communicating with CH9121, needs to be initialized in advance
        cfg (Pin): Configuration mode control pin object (Pin class), low level enters configuration mode, high level exits
        w (asyncio.StreamWriter): asyncio.StreamWriter object for asynchronous writing data to UART
        r (asyncio.StreamReader): asyncio.StreamReader object for asynchronous reading data from UART

    Methods:
        _config(): Private method, sends configuration commands and reads responses, handles pin switching for configuration mode
        get_mode(): Gets the current working mode
        get_local_ip(): Gets the local IP address
        get_subnet_mask(): Gets the subnet mask
        get_gateway(): Gets the gateway address
        get_local_port(): Gets the local port number
        get_target_ip(): Gets the target IP address
        get_target_port(): Gets the target port number
        set_mode(): Sets the working mode (TCP_SERVER/TCP_CLIENT/UDP_SERVER/UDP_CLIENT)
        set_baud_rate(): Sets the serial baud rate
        set_local_ip(): Sets the local IP address
        set_gateway(): Sets the gateway address
        set_local_port(): Sets the local port number
        set_target_ip(): Sets the target IP address
        set_target_port(): Sets the target port number
        write(): Asynchronously writes data to the module
        read(): Asynchronously reads data of specified length
        readline(): Asynchronously reads data line by line
        reset(): Resets the CH9121 module

    Notes:
        1. Before configuring the module, ensure the cfg pin is pulled low to enter configuration mode, and pulled high to exit after configuration
        2. All configuration and read/write operations are asynchronous and need to be executed in the asyncio event loop
        3. Network parameter configuration takes effect after restarting the module (call reset method)
    """

    def __init__(self, uart: UART, cfg: Pin) -> None:
        """
        CH9121类初始化方法
        Args:
            uart (UART): UART对象，已初始化的串口实例，用于与CH9121通信
            cfg (Pin): Pin对象，配置模式控制引脚，低电平进入配置模式

        Raises:
            TypeError: 当uart参数不是UART实例或cfg参数不是Pin实例时触发

        Notes:
            1. 初始化StreamWriter和StreamReader用于异步串口操作
            2. cfg引脚需为输出模式，初始状态建议拉高

        ==========================================
        CH9121 Class Initialization Method
        Args:
            uart (UART): UART object, initialized serial port instance for communicating with CH9121
            cfg (Pin): Pin object, configuration mode control pin, low level enters configuration mode

        Raises:
            TypeError: Triggered when the uart parameter is not a UART instance or the cfg parameter is not a Pin instance

        Notes:
            1. Initializes StreamWriter and StreamReader for asynchronous serial port operations
            2. The cfg pin needs to be in output mode, and the initial state is recommended to be high
        """
        # 1. 验证uart参数类型：必须是machine.UART实例
        if uart is None:
            raise TypeError("uart parameter cannot be None, must be UART instance")
        if not isinstance(uart, UART):
            raise TypeError(f"Expected uart type UART, got {type(uart).__name__} instead")

        # 2. 验证cfg参数类型：必须是machine.Pin实例
        if cfg is None:
            raise TypeError("cfg parameter cannot be None, must be Pin instance")
        if not isinstance(cfg, Pin):
            raise TypeError(f"Expected cfg type Pin, got {type(cfg).__name__} instead")

        self.uart = uart
        self.cfg = cfg
        self.w = asyncio.StreamWriter(uart, {})
        self.r = asyncio.StreamReader(uart)

    async def _config(self, cmd: bytes, n: int = 1) -> bytes:
        """
        私有配置方法，发送配置指令并读取响应
        Args:
            cmd (bytes): 字节类型配置指令，CH9121的配置命令（如\x60获取模式）
            n (int): 整数类型，期望读取的响应字节数，默认1

        Raises:
            TypeError: 当cmd参数不是bytes类型或n参数不是int类型时触发
            ValueError: 当n参数小于1时触发

        Notes:
            1. 先拉低cfg引脚进入配置模式，发送指令后等待响应
            2. 配置完成后拉高cfg引脚退出配置模式
            3. 每次读取前延时0.1秒，确保模块有足够时间返回响应

        ==========================================
        Private Configuration Method, Sends Configuration Commands and Reads Responses
        Args:
            cmd (bytes): Byte-type configuration command, configuration command for CH9121 (e.g., \x60 to get mode)
            n (int): Integer type, expected number of response bytes to read, default 1

        Raises:
            TypeError: Triggered when the cmd parameter is not of bytes type or the n parameter is not of int type
            ValueError: Triggered when the n parameter is less than 1

        Notes:
            1. Pull down the cfg pin to enter configuration mode first, wait for response after sending command
            2. Pull up the cfg pin to exit configuration mode after configuration is completed
            3. Delay 0.1 seconds before each read to ensure the module has enough time to return a response
        """
        # 验证cmd参数类型是否为bytes
        if not isinstance(cmd, bytes):
            raise TypeError(f"cmd must be bytes, got {type(cmd).__name__}")
        # 验证n参数类型是否为int
        if not isinstance(n, int):
            raise TypeError(f"n must be int, got {type(n).__name__}")
        # 验证n参数是否大于等于1
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")

        # 拉低cfg引脚进入配置模式
        self.cfg.value(0)
        # 发送配置指令（前缀0x57 0xab为CH9121配置指令固定头）
        await self.w.awrite(b"\x57\xab" + cmd)
        resp = b""
        # 循环读取直到获取到指定长度的响应数据
        while len(resp) < n:
            # 延时0.1秒等待模块响应
            await asyncio.sleep(0.1)
            # 读取响应数据
            resp = await self.r.read(n)
        # 拉高cfg引脚退出配置模式
        self.cfg.value(1)
        return resp

    async def get_mode(self) -> int:
        """
        获取CH9121当前工作模式
        Args:
            无

        Returns:
            int: 当前工作模式值，对应常量TCP_SERVER(0)/TCP_CLIENT(1)/UDP_SERVER(2)/UDP_CLIENT(3)

        Raises:
            无

        Notes:
            1. 调用_config方法发送\x60指令，读取1字节响应
            2. 返回值为字节的ASCII码值，直接对应模式常量

        ==========================================
        Gets the Current Working Mode of CH9121
        Args:
            None

        Returns:
            int: Current working mode value, corresponding to constants TCP_SERVER(0)/TCP_CLIENT(1)/UDP_SERVER(2)/UDP_CLIENT(3)

        Raises:
            None

        Notes:
            1. Calls the _config method to send the \x60 command and read 1-byte response
            2. The return value is the ASCII code value of the byte, directly corresponding to the mode constant
        """
        # 发送获取模式指令并读取响应
        mode = await self._config(b"\x60")
        # 转换字节为整数返回
        return ord(mode)

    async def get_local_ip(self) -> tuple[int, int, int, int]:
        """
        获取CH9121本地IP地址
        Args:
            无

        Returns:
            tuple[int, int, int, int]: (ip1, ip2, ip3, ip4)，如(192, 168, 1, 100)

        Raises:
            无

        Notes:
            1. 调用_config方法发送\x61指令，读取4字节响应
            2. 4字节分别对应IP地址的四个段

        ==========================================
        Gets the Local IP Address of CH9121
        Args:
            None

        Returns:
            tuple[int, int, int, int]: (ip1, ip2, ip3, ip4), e.g., (192, 168, 1, 100)

        Raises:
            None

        Notes:
            1. Calls the _config method to send the \x61 command and read 4-byte response
            2. The 4 bytes correspond to the four segments of the IP address respectively
        """
        # 发送获取本地IP指令并读取4字节响应
        x = await self._config(b"\x61", 4)
        # 转换为IP四段元组返回
        return (x[0], x[1], x[2], x[3])

    async def get_subnet_mask(self) -> tuple[int, int, int, int]:
        """
        获取CH9121子网掩码
        Args:
            无

        Returns:
            tuple[int, int, int, int]: (mask1, mask2, mask3, mask4)，如(255, 255, 255, 0)

        Raises:
            无

        Notes:
            1. 调用_config方法发送\x62指令，读取4字节响应
            2. 4字节分别对应子网掩码的四个段

        ==========================================
        Gets the Subnet Mask of CH9121
        Args:
            None

        Returns:
            tuple[int, int, int, int]: (mask1, mask2, mask3, mask4), e.g., (255, 255, 255, 0)

        Raises:
            None

        Notes:
            1. Calls the _config method to send the \x62 command and read 4-byte response
            2. The 4 bytes correspond to the four segments of the subnet mask respectively
        """
        # 发送获取子网掩码指令并读取4字节响应
        x = await self._config(b"\x62", 4)
        # 转换为子网掩码四段元组返回
        return (x[0], x[1], x[2], x[3])

    async def get_gateway(self) -> tuple[int, int, int, int]:
        """
        获取CH9121网关地址
        Args:
            无

        Returns:
            tuple[int, int, int, int]: (gateway1, gateway2, gateway3, gateway4)，如(192, 168, 1, 1)

        Raises:
            无

        Notes:
            1. 调用_config方法发送\x63指令，读取4字节响应
            2. 4字节分别对应网关地址的四个段

        ==========================================
        Gets the Gateway Address of CH9121
        Args:
            None

        Returns:
            tuple[int, int, int, int]: (gateway1, gateway2, gateway3, gateway4), e.g., (192, 168, 1, 1)

        Raises:
            None

        Notes:
            1. Calls the _config method to send the \x63 command and read 4-byte response
            2. The 4 bytes correspond to the four segments of the gateway address respectively
        """
        # 发送获取网关指令并读取4字节响应
        x = await self._config(b"\x63", 4)
        # 转换为网关四段元组返回
        return (x[0], x[1], x[2], x[3])

    async def get_local_port(self) -> int:
        """
        获取CH9121本地端口号
        Args:
            无

        Returns:
            int: 本地端口号，如8080

        Raises:
            无

        Notes:
            1. 调用_config方法发送\x64指令，读取2字节响应
            2. 响应字节按小端序（little）转换为整数

        ==========================================
        Gets the Local Port Number of CH9121
        Args:
            None

        Returns:
            int: Local port number, e.g., 8080

        Raises:
            None

        Notes:
            1. Calls the _config method to send the \x64 command and read 2-byte response
            2. The response bytes are converted to integer in little-endian order
        """
        # 发送获取本地端口指令并读取2字节响应
        x = await self._config(b"\x64", 2)
        # 小端序转换为端口整数返回
        return int.from_bytes(x, "little")

    async def get_target_ip(self) -> tuple[int, int, int, int]:
        """
        获取CH9121目标IP地址（客户端模式下）
        Args:
            无

        Returns:
            tuple[int, int, int, int]: (ip1, ip2, ip3, ip4)，如(192, 168, 1, 200)

        Raises:
            无

        Notes:
            1. 调用_config方法发送\x65指令，读取4字节响应
            2. 仅在TCP/UDP客户端模式下该参数有效

        ==========================================
        Gets the Target IP Address of CH9121 (in client mode)
        Args:
            None

        Returns:
            tuple[int, int, int, int]: (ip1, ip2, ip3, ip4), e.g., (192, 168, 1, 200)

        Raises:
            None

        Notes:
            1. Calls the _config method to send the \x65 command and read 4-byte response
            2. This parameter is only valid in TCP/UDP client mode
        """
        # 发送获取目标IP指令并读取4字节响应
        x = await self._config(b"\x65", 4)
        # 转换为目标IP四段元组返回
        return (x[0], x[1], x[2], x[3])

    async def get_target_port(self) -> int:
        """
        获取CH9121目标端口号（客户端模式下）
        Args:
            无

        Returns:
            int: 目标端口号，如80

        Raises:
            无

        Notes:
            1. 调用_config方法发送\x66指令，读取2字节响应
            2. 响应字节按小端序（little）转换为整数
            3. 仅在TCP/UDP客户端模式下该参数有效

        ==========================================
        Gets the Target Port Number of CH9121 (in client mode)
        Args:
            None

        Returns:
            int: Target port number, e.g., 80

        Raises:
            None

        Notes:
            1. Calls the _config method to send the \x66 command and read 2-byte response
            2. The response bytes are converted to integer in little-endian order
            3. This parameter is only valid in TCP/UDP client mode
        """
        # 发送获取目标端口指令并读取2字节响应
        x = await self._config(b"\x66", 2)
        # 小端序转换为端口整数返回
        return int.from_bytes(x, "little")

    async def set_mode(self, mode: int) -> bytes:
        """
        设置CH9121工作模式
        Args:
            mode (int): 工作模式值，可选TCP_SERVER(0)/TCP_CLIENT(1)/UDP_SERVER(2)/UDP_CLIENT(3)

        Returns:
            bytes: 模块返回的响应数据

        Raises:
            TypeError: 当mode参数不是int类型时触发
            ValueError: 当mode参数不在0-3范围内时触发

        Notes:
            1. 调用_config方法发送\x10+模式字节指令
            2. 模式值按小端序转换为1字节
            3. 配置后需重启模块生效（调用reset方法）

        ==========================================
        Sets the Working Mode of CH9121
        Args:
            mode (int): Integer, working mode value, optional TCP_SERVER(0)/TCP_CLIENT(1)/UDP_SERVER(2)/UDP_CLIENT(3)

        Returns:
            bytes: Response data returned by the module

        Raises:
            TypeError: Triggered when the mode parameter is not of int type
            ValueError: Triggered when the mode parameter is not in the range of 0-3

        Notes:
            1. Calls the _config method to send \x10 + mode byte command
            2. The mode value is converted to 1 byte in little-endian order
            3. The configuration takes effect after restarting the module (call reset method)
        """
        # 验证mode参数类型是否为int
        if not isinstance(mode, int):
            raise TypeError(f"mode must be int, got {type(mode).__name__}")
        # 验证mode参数是否在合法范围内
        if mode not in (TCP_SERVER, TCP_CLIENT, UDP_SERVER, UDP_CLIENT):
            raise ValueError(f"mode must be 0-3, got {mode}")

        # 发送设置模式指令并返回响应
        x = await self._config(b"\x10" + mode.to_bytes(1, "little"))
        return x

    async def set_baud_rate(self, baud: int) -> bytes:
        """
        设置CH9121串口波特率
        Args:
            baud (int): 波特率值，如9600、115200等

        Returns:
            bytes: 模块返回的响应数据

        Raises:
            TypeError: 当baud参数不是int类型时触发
            ValueError: 当baud参数不在支持的波特率列表中时触发

        Notes:
            1. 调用_config方法发送\x21+波特率字节指令
            2. 波特率值按小端序转换为4字节
            3. 配置后需重启模块生效（调用reset方法）

        ==========================================
        Sets the Serial Baud Rate of CH9121
        Args:
            baud (int): Integer, baud rate value, e.g., 9600, 115200, etc.

        Returns:
            bytes: Response data returned by the module

        Raises:
            TypeError: Triggered when the baud parameter is not of int type
            ValueError: Triggered when the baud parameter is not in the supported baud rate list

        Notes:
            1. Calls the _config method to send \x21 + baud rate byte command
            2. The baud rate value is converted to 4 bytes in little-endian order
            3. The configuration takes effect after restarting the module (call reset method)
        """
        # 验证baud参数类型是否为int
        if not isinstance(baud, int):
            raise TypeError(f"baud must be int, got {type(baud).__name__}")
        # 验证baud参数是否在支持的波特率列表中
        if baud not in SUPPORTED_BAUDS:
            raise ValueError(f"baud must be in {SUPPORTED_BAUDS}, got {baud}")

        # 发送设置波特率指令并返回响应
        x = await self._config(b"\x21" + baud.to_bytes(4, "little"))
        return x

    async def set_local_ip(self, ip: tuple[int, int, int, int]) -> bytes:
        """
        设置CH9121本地IP地址
        Args:
            ip (tuple[int, int, int, int]): IP地址四个段，如(192, 168, 1, 100)

        Returns:
            bytes: 模块返回的响应数据

        Raises:
            TypeError: 当ip参数不是tuple类型时触发
            ValueError: 当ip参数长度不是4或网段值不在0-255范围内时触发

        Notes:
            1. 调用_config方法发送\x11+IP字节指令
            2. IP元组转换为字节数组后拼接至指令后
            3. 配置后需重启模块生效（调用reset方法）

        ==========================================
        Sets the Local IP Address of CH9121
        Args:
            ip (tuple[int, int, int, int]): Tuple, four segments of IP address, e.g., (192, 168, 1, 100)

        Returns:
            bytes: Response data returned by the module

        Raises:
            TypeError: Triggered when the ip parameter is not of tuple type
            ValueError: Triggered when the length of ip parameter is not 4 or the segment value is not in the range of 0-255

        Notes:
            1. Calls the _config method to send \x11 + IP byte command
            2. The IP tuple is converted to a byte array and appended to the command
            3. The configuration takes effect after restarting the module (call reset method)
        """
        # 验证ip参数类型是否为tuple
        if not isinstance(ip, tuple):
            raise TypeError(f"ip must be tuple, got {type(ip).__name__}")
        # 验证ip参数长度是否为4
        if len(ip) != 4:
            raise ValueError(f"ip must have 4 segments, got {len(ip)}")
        # 验证每个IP网段是否为0-255的整数
        for seg in ip:
            if not isinstance(seg, int) or seg < 0 or seg > 255:
                raise ValueError(f"IP segment must be 0-255 int, got {seg}")

        # 发送设置本地IP指令并返回响应
        x = await self._config(b"\x11" + bytes(bytearray(ip)))
        return x

    async def set_gateway(self, ip: tuple[int, int, int, int]) -> bytes:
        """
        设置CH9121网关地址
        Args:
            ip (tuple[int, int, int, int]): 网关地址四个段，如(192, 168, 1, 1)

        Returns:
            bytes: 模块返回的响应数据

        Raises:
            TypeError: 当ip参数不是tuple类型时触发
            ValueError: 当ip参数长度不是4或网段值不在0-255范围内时触发

        Notes:
            1. 调用_config方法发送\x13+网关字节指令
            2. 网关元组转换为字节数组后拼接至指令后
            3. 配置后需重启模块生效（调用reset方法）

        ==========================================
        Sets the Gateway Address of CH9121
        Args:
            ip (tuple[int, int, int, int]): Tuple, four segments of gateway address, e.g., (192, 168, 1, 1)

        Returns:
            bytes: Response data returned by the module

        Raises:
            TypeError: Triggered when the ip parameter is not of tuple type
            ValueError: Triggered when the length of ip parameter is not 4 or the segment value is not in the range of 0-255

        Notes:
            1. Calls the _config method to send \x13 + gateway byte command
            2. The gateway tuple is converted to a byte array and appended to the command
            3. The configuration takes effect after restarting the module (call reset method)
        """
        # 验证ip参数类型是否为tuple
        if not isinstance(ip, tuple):
            raise TypeError(f"ip must be tuple, got {type(ip).__name__}")
        # 验证ip参数长度是否为4
        if len(ip) != 4:
            raise ValueError(f"ip must have 4 segments, got {len(ip)}")
        # 验证每个网关网段是否为0-255的整数
        for seg in ip:
            if not isinstance(seg, int) or seg < 0 or seg > 255:
                raise ValueError(f"Gateway segment must be 0-255 int, got {seg}")

        # 发送设置网关指令并返回响应
        x = await self._config(b"\x13" + bytes(bytearray(ip)))
        return x

    async def set_local_port(self, port: int) -> bytes:
        """
        设置CH9121本地端口号
        Args:
            port (int): 本地端口号，如8080

        Returns:
            bytes: 模块返回的响应数据

        Raises:
            TypeError: 当port参数不是int类型时触发
            ValueError: 当port参数不在1-65535范围内时触发

        Notes:
            1. 调用_config方法发送\x14+端口字节指令
            2. 端口号按小端序转换为2字节
            3. 配置后需重启模块生效（调用reset方法）

        ==========================================
        Sets the Local Port Number of CH9121
        Args:
            port (int): Integer, local port number, e.g., 8080

        Returns:
            bytes: Response data returned by the module

        Raises:
            TypeError: Triggered when the port parameter is not of int type
            ValueError: Triggered when the port parameter is not in the range of 1-65535

        Notes:
            1. Calls the _config method to send \x14 + port byte command
            2. The port number is converted to 2 bytes in little-endian order
            3. The configuration takes effect after restarting the module (call reset method)
        """
        # 验证port参数类型是否为int
        if not isinstance(port, int):
            raise TypeError(f"port must be int, got {type(port).__name__}")
        # 验证port参数是否在合法端口范围内
        if port < 1 or port > 65535:
            raise ValueError(f"port must be 1-65535, got {port}")

        # 发送设置本地端口指令并返回响应
        x = await self._config(b"\x14" + port.to_bytes(2, "little"))
        return x

    async def set_target_ip(self, ip: tuple[int, int, int, int]) -> bytes:
        """
        设置CH9121目标IP地址（客户端模式下）
        Args:
            ip (tuple[int, int, int, int]): 目标IP地址四个段，如(192, 168, 1, 200)

        Returns:
            bytes: 模块返回的响应数据

        Raises:
            TypeError: 当ip参数不是tuple类型时触发
            ValueError: 当ip参数长度不是4或网段值不在0-255范围内时触发

        Notes:
            1. 调用_config方法发送\x15+目标IP字节指令
            2. 目标IP元组转换为字节数组后拼接至指令后
            3. 仅在TCP/UDP客户端模式下该配置有效
            4. 配置后需重启模块生效（调用reset方法）

        ==========================================
        Sets the Target IP Address of CH9121 (in client mode)
        Args:
            ip (tuple[int, int, int, int]): Tuple, four segments of target IP address, e.g., (192, 168, 1, 200)

        Returns:
            bytes: Response data returned by the module

        Raises:
            TypeError: Triggered when the ip parameter is not of tuple type
            ValueError: Triggered when the length of ip parameter is not 4 or the segment value is not in the range of 0-255

        Notes:
            1. Calls the _config method to send \x15 + target IP byte command
            2. The target IP tuple is converted to a byte array and appended to the command
            3. This configuration is only valid in TCP/UDP client mode
            4. The configuration takes effect after restarting the module (call reset method)
        """
        # 验证ip参数类型是否为tuple
        if not isinstance(ip, tuple):
            raise TypeError(f"ip must be tuple, got {type(ip).__name__}")
        # 验证ip参数长度是否为4
        if len(ip) != 4:
            raise ValueError(f"ip must have 4 segments, got {len(ip)}")
        # 验证每个目标IP网段是否为0-255的整数
        for seg in ip:
            if not isinstance(seg, int) or seg < 0 or seg > 255:
                raise ValueError(f"Target IP segment must be 0-255 int, got {seg}")

        # 发送设置目标IP指令并返回响应
        x = await self._config(b"\x15" + bytes(bytearray(ip)))
        return x

    async def set_target_port(self, port: int) -> bytes:
        """
        设置CH9121目标端口号（客户端模式下）
        Args:
            port (int): 目标端口号，如80

        Returns:
            bytes: 模块返回的响应数据

        Raises:
            TypeError: 当port参数不是int类型时触发
            ValueError: 当port参数不在1-65535范围内时触发

        Notes:
            1. 调用_config方法发送\x16+目标端口字节指令
            2. 目标端口号按小端序转换为2字节
            3. 仅在TCP/UDP客户端模式下该配置有效
            4. 配置后需重启模块生效（调用reset方法）

        ==========================================
        Sets the Target Port Number of CH9121 (in client mode)
        Args:
            port (int): Integer, target port number, e.g., 80

        Returns:
            bytes: Response data returned by the module

        Raises:
            TypeError: Triggered when the port parameter is not of int type
            ValueError: Triggered when the port parameter is not in the range of 1-65535

        Notes:
            1. Calls the _config method to send \x16 + target port byte command
            2. The target port number is converted to 2 bytes in little-endian order
            3. This configuration is only valid in TCP/UDP client mode
            4. The configuration takes effect after restarting the module (call reset method)
        """
        # 验证port参数类型是否为int
        if not isinstance(port, int):
            raise TypeError(f"port must be int, got {type(port).__name__}")
        # 验证port参数是否在合法端口范围内
        if port < 1 or port > 65535:
            raise ValueError(f"port must be 1-65535, got {port}")

        # 发送设置目标端口指令并返回响应
        x = await self._config(b"\x16" + port.to_bytes(2, "little"))
        return x

    async def write(self, data: bytes) -> int:
        """
        异步写入数据到CH9121模块
        Args:
            data (bytes): 要写入的数据

        Returns:
            int: 写入的字节数

        Raises:
            TypeError: 当data参数不是bytes类型时触发

        Notes:
            1. 直接调用StreamWriter的awrite方法
            2. 数据为透传模式下的业务数据，非配置指令

        ==========================================
        Asynchronously Writes Data to CH9121 Module
        Args:
            data (bytes): Byte string, data to be written

        Returns:
            int: Number of bytes written

        Raises:
            TypeError: Triggered when the data parameter is not of bytes type

        Notes:
            1. Directly calls the awrite method of StreamWriter
            2. The data is business data in transparent transmission mode, not configuration commands
        """
        # 验证data参数类型是否为bytes
        if not isinstance(data, bytes):
            raise TypeError(f"data must be bytes, got {type(data).__name__}")

        # 异步写入数据并返回写入的字节数
        return await self.w.awrite(data)

    async def read(self, n: int) -> bytes:
        """
        异步从CH9121模块读取指定长度的数据
        Args:
            n (int): 要读取的字节数

        Returns:
            bytes: 读取到的数据

        Raises:
            TypeError: 当n参数不是int类型时触发
            ValueError: 当n参数小于1时触发

        Notes:
            1. 直接调用StreamReader的read方法
            2. 读取的是透传模式下的业务数据，非配置响应

        ==========================================
        Asynchronously Reads Data of Specified Length from CH9121 Module
        Args:
            n (int): Integer, number of bytes to read

        Returns:
            bytes: Read data

        Raises:
            TypeError: Triggered when the n parameter is not of int type
            ValueError: Triggered when the n parameter is less than 1

        Notes:
            1. Directly calls the read method of StreamReader
            2. The read data is business data in transparent transmission mode, not configuration response
        """
        # 验证n参数类型是否为int
        if not isinstance(n, int):
            raise TypeError(f"n must be int, got {type(n).__name__}")
        # 验证n参数是否大于等于1
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")

        # 异步读取指定长度的数据并返回
        return await self.r.read(n)

    async def readline(self) -> bytes:
        """
        异步从CH9121模块按行读取数据
        Args:
            无

        Returns:
            bytes: 读取到的一行数据（以换行符为结束符）

        Raises:
            无

        Notes:
            1. 直接调用StreamReader的readline方法
            2. 适用于读取文本类换行分隔的业务数据

        ==========================================
        Asynchronously Reads Data Line by Line from CH9121 Module
        Args:
            None

        Returns:
            bytes: A line of read data (ending with a newline character)

        Raises:
            None

        Notes:
            1. Directly calls the readline method of StreamReader
            2. Suitable for reading text-based business data separated by newlines
        """
        # 异步按行读取数据并返回
        return await self.r.readline()

    async def reset(self) -> None:
        """
        重置CH9121模块
        Args:
            无

        Returns:
            无

        Raises:
            无

        Notes:
            1. 发送重置指令\x57\xab\x02，无需读取响应
            2. 配置参数后调用该方法使配置生效
            3. 重置过程约需1秒，建议延时后再进行后续操作

        ==========================================
        Resets the CH9121 Module
        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            1. Sends reset command \x57\xab\x02, no need to read response
            2. Call this method to make configuration take effect after configuring parameters
            3. The reset process takes about 1 second, it is recommended to delay before subsequent operations
        """
        # 发送模块重置指令
        await self.w.awrite(b"\x57\xab\x02")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
