# CH9121的串口转以太网模块 MicroPython驱动
# -*- coding: utf-8 -*-
# @Time    : 2026/3/2
# @Author  : hogeiha
# @File    : kt403a.py
# @Description : CH9121的串口转以太网模块 MicroPython驱动，适用于基于MicroPython的项目开发。
# @License : MIT
# @Platform : MicroPython v1.23.0


__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython异步IO模块，用于异步串口通信
import uasyncio as asyncio

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CH9121:
    """
    CH9121串口转网络模块异步驱动类，基于uasyncio实现对CH9121模块的配置与数据收发。
    支持模块工作模式、网络参数、串口参数的配置，以及异步数据读写操作，适配MicroPython环境。

    Attributes:
        CH9121.TCP_CLIENT (int): 模块工作模式常量 - TCP客户端（值为0）
        CH9121.TCP_SERVER (int): 模块工作模式常量 - TCP服务器（值为1）
        CH9121.UDP_CLIENT (int): 模块工作模式常量 - UDP客户端（值为2）
        CH9121.UDP_SERVER (int): 模块工作模式常量 - UDP服务器（值为3）
        uart (UART): MicroPython UART实例，用于与CH9121模块通信
        cfg (Pin): 配置模式控制引脚实例（低电平进入配置模式）
        w (StreamWriter): 异步串口写数据流对象
        r (StreamReader): 异步串口读数据流对象

    Methods:
        __init__(uart, cfg):
            初始化CH9121模块驱动实例，创建异步读写流对象
        _config(cmd, n=1):
            私有方法 - 进入配置模式并发送配置指令，读取响应数据
        get_mode():
            获取模块当前工作模式
        get_local_ip():
            获取模块本地IP地址
        get_subnet_mask():
            获取模块子网掩码
        get_gateway():
            获取模块网关地址
        get_local_port():
            获取模块本地端口号
        get_target_ip():
            获取模块目标IP地址
        get_target_port():
            获取模块目标端口号
        set_mode(mode):
            设置模块工作模式
        set_baud_rate(baud):
            设置模块串口波特率
        set_local_ip(ip):
            设置模块本地IP地址
        set_gateway(ip):
            设置模块网关地址
        set_local_port(x):
            设置模块本地端口号
        set_target_ip(ip):
            设置模块目标IP地址
        set_target_port(x):
            设置模块目标端口号
        write(x):
            异步写入数据到模块串口
        read(n):
            异步从模块串口读取指定长度数据
        readline():
            异步读取模块串口数据直到换行符
        reset():
            复位CH9121模块

    ==========================================

    CH9121 serial to network module asynchronous driver class, implementing configuration and data
    transmission/reception for CH9121 module based on uasyncio.
    Supports configuration of module working mode, network parameters, serial port parameters,
    and asynchronous data read/write operations, adapted to MicroPython environment.

    Attributes:
        CH9121.TCP_CLIENT (int): Module working mode constant - TCP Client (value 0)
        CH9121.TCP_SERVER (int): Module working mode constant - TCP Server (value 1)
        CH9121.UDP_CLIENT (int): Module working mode constant - UDP Client (value 2)
        CH9121.UDP_SERVER (int): Module working mode constant - UDP Server (value 3)
        uart (UART): MicroPython UART instance for communication with CH9121 module
        cfg (Pin): Configuration mode control pin instance (low level enters configuration mode)
        w (StreamWriter): Asynchronous serial write stream object
        r (StreamReader): Asynchronous serial read stream object

    Methods:
        __init__(uart, cfg):
            Initialize CH9121 module driver instance and create asynchronous read/write stream objects
        _config(cmd, n=1):
            Private method - Enter configuration mode, send configuration command and read response data
        get_mode():
            Get current working mode of the module
        get_local_ip():
            Get local IP address of the module
        get_subnet_mask():
            Get subnet mask of the module
        get_gateway():
            Get gateway address of the module
        get_local_port():
            Get local port number of the module
        get_target_ip():
            Get target IP address of the module
        get_target_port():
            Get target port number of the module
        set_mode(mode):
            Set working mode of the module
        set_baud_rate(baud):
            Set serial port baud rate of the module
        set_local_ip(ip):
            Set local IP address of the module
        set_gateway(ip):
            Set gateway address of the module
        set_local_port(x):
            Set local port number of the module
        set_target_ip(ip):
            Set target IP address of the module
        set_target_port(x):
            Set target port number of the module
        write(x):
            Asynchronously write data to module serial port
        read(n):
            Asynchronously read specified length data from module serial port
        readline():
            Asynchronously read data from module serial port until newline character
        reset():
            Reset CH9121 module
    """

    # 工作模式常量 - TCP客户端模式
    TCP_CLIENT = 0
    # 工作模式常量 - TCP服务器模式
    TCP_SERVER = 1
    # 工作模式常量 - UDP客户端模式
    UDP_CLIENT = 2
    # 工作模式常量 - UDP服务器模式
    UDP_SERVER = 3

    def __init__(self, uart, cfg):
        """
        初始化CH9121模块驱动实例，创建异步读写流对象。

        Args:
            uart (UART): 已初始化的MicroPython UART实例（需匹配模块波特率）
            cfg (Pin): 配置模式控制引脚（输出模式）

        Notes:
            cfg引脚低电平进入配置模式，高电平退出配置模式；
            异步流对象基于传入的UART实例创建，用于异步数据收发

        ---
        Initialize CH9121 module driver instance and create asynchronous read/write stream objects.

        Args:
            uart (UART): Initialized MicroPython UART instance (must match module baud rate)
            cfg (Pin): Configuration mode control pin (output mode)

        Notes:
            cfg pin low level enters configuration mode, high level exits configuration mode;
            asynchronous stream objects are created based on the incoming UART instance for asynchronous data transmission/reception
        """
        # 保存UART通信实例
        self.uart = uart
        # 保存配置模式控制引脚实例
        self.cfg = cfg
        # 创建异步串口写数据流对象
        self.w = asyncio.StreamWriter(uart, {})
        # 创建异步串口读数据流对象
        self.r = asyncio.StreamReader(uart)

    async def _config(self, cmd, n=1):
        """
        私有方法：进入配置模式，发送配置指令并读取响应数据。

        Args:
            cmd (bytes): 配置指令字节串（不含帧头）
            n (int, 可选): 期望读取的响应字节数，默认值1

        Returns:
            bytes: 模块返回的响应数据（长度为n）

        Notes:
            配置帧格式：0x57 0xab + 指令；
            cfg引脚拉低进入配置模式，操作完成后拉高退出；
            读取响应时最多等待0.1秒，确保数据接收完整

        ---
        Private method: Enter configuration mode, send configuration command and read response data.

        Args:
            cmd (bytes): Configuration command byte string (without frame header)
            n (int, optional): Expected number of response bytes to read, default value 1

        Returns:
            bytes: Response data returned by the module (length n)

        Notes:
            Configuration frame format: 0x57 0xab + command;
            cfg pin pulled low to enter configuration mode, pulled high to exit after operation;
            Wait up to 0.1 seconds when reading response to ensure complete data reception
        """
        # 将配置引脚拉低，进入配置模式
        self.cfg.value(0)
        # 发送配置指令帧（帧头0x57 0xab + 指令）
        await self.w.awrite("\x57\xab" + cmd)
        # 初始化响应数据缓冲区
        resp = b""
        # 循环读取直到获取指定长度的响应数据
        while len(resp) < n:
            # 等待0.1秒，让模块处理指令并返回响应
            await asyncio.sleep(0.1)
            # 读取n字节响应数据
            resp = await self.r.read(n)
        # 将配置引脚拉高，退出配置模式
        self.cfg.value(1)
        # 返回响应数据
        return resp

    async def get_mode(self):
        """
        获取CH9121模块当前的工作模式。

        Returns:
            int: 工作模式值（0=CH9121.TCP_CLIENT, 1=CH9121.TCP_SERVER, 2=CH9121.UDP_CLIENT, 3=CH9121.UDP_SERVER）

        Notes:
            读取指令：0x60；返回1字节模式值

        ---
        Get current working mode of CH9121 module.

        Returns:
            int: Working mode value (0=CH9121.TCP_CLIENT, 1=CH9121.TCP_SERVER, 2=CH9121.UDP_CLIENT, 3=CH9121.UDP_SERVER)

        Notes:
            Read command: 0x60; returns 1-byte mode value
        """
        # 发送读取模式指令（0x60），获取1字节响应
        mode = await self._config("\x60", 4)
        # 将字节转换为整数并返回
        return ord(mode)

    async def get_local_ip(self):
        """
        获取CH9121模块的本地IP地址。

        Returns:
            tuple: IP地址四元组 (a, b, c, d)，对应IPv4的四个段

        Notes:
            读取指令：0x61；返回4字节IP地址（大端序）

        ---
        Get local IP address of CH9121 module.

        Returns:
            tuple: IP address quadruple (a, b, c, d), corresponding to four segments of IPv4

        Notes:
            Read command: 0x61; returns 4-byte IP address (big-endian)
        """
        # 发送读取本地IP指令（0x61），获取4字节响应
        x = await self._config("\x61", 4)
        # 将4字节数据转换为IP地址四元组并返回
        return (x[0], x[1], x[2], x[3])

    async def get_subnet_mask(self):
        """
        获取CH9121模块的子网掩码。

        Returns:
            tuple: 子网掩码四元组 (a, b, c, d)，对应IPv4的四个段

        Notes:
            读取指令：0x62；返回4字节子网掩码（大端序）

        ---
        Get subnet mask of CH9121 module.

        Returns:
            tuple: Subnet mask quadruple (a, b, c, d), corresponding to four segments of IPv4

        Notes:
            Read command: 0x62; returns 4-byte subnet mask (big-endian)
        """
        # 发送读取子网掩码指令（0x62），获取4字节响应
        x = await self._config("\x62", 4)
        # 将4字节数据转换为子网掩码四元组并返回
        return (x[0], x[1], x[2], x[3])

    async def get_gateway(self):
        """
        获取CH9121模块的网关地址。

        Returns:
            tuple: 网关地址四元组 (a, b, c, d)，对应IPv4的四个段

        Notes:
            读取指令：0x63；返回4字节网关地址（大端序）

        ---
        Get gateway address of CH9121 module.

        Returns:
            tuple: Gateway address quadruple (a, b, c, d), corresponding to four segments of IPv4

        Notes:
            Read command: 0x63; returns 4-byte gateway address (big-endian)
        """
        # 发送读取网关地址指令（0x63），获取4字节响应
        x = await self._config("\x63", 4)
        # 将4字节数据转换为网关地址四元组并返回
        return (x[0], x[1], x[2], x[3])

    async def get_local_port(self):
        """
        获取CH9121模块的本地端口号。

        Returns:
            int: 本地端口号（0-65535）

        Notes:
            读取指令：0x64；返回2字节端口号（小端序）

        ---
        Get local port number of CH9121 module.

        Returns:
            int: Local port number (0-65535)

        Notes:
            Read command: 0x64; returns 2-byte port number (little-endian)
        """
        # 发送读取本地端口指令（0x64），获取2字节响应
        x = await self._config("\x64", 2)
        # 将小端序2字节数据转换为端口号整数并返回
        return int.from_bytes(x, "little")

    async def get_target_ip(self):
        """
        获取CH9121模块的目标IP地址（客户端模式下）。

        Returns:
            tuple: 目标IP地址四元组 (a, b, c, d)，对应IPv4的四个段

        Notes:
            读取指令：0x65；返回4字节IP地址（大端序）；
            服务器模式下该值无意义

        ---
        Get target IP address of CH9121 module (in client mode).

        Returns:
            tuple: Target IP address quadruple (a, b, c, d), corresponding to four segments of IPv4

        Notes:
            Read command: 0x65; returns 4-byte IP address (big-endian);
            This value is meaningless in server mode
        """
        # 发送读取目标IP指令（0x65），获取4字节响应
        x = await self._config("\x65", 4)
        # 将4字节数据转换为目标IP地址四元组并返回
        return (x[0], x[1], x[2], x[3])

    async def get_target_port(self):
        """
        获取CH9121模块的目标端口号（客户端模式下）。

        Returns:
            int: 目标端口号（0-65535）

        Notes:
            读取指令：0x66；返回2字节端口号（小端序）；
            服务器模式下该值无意义

        ---
        Get target port number of CH9121 module (in client mode).

        Returns:
            int: Target port number (0-65535)

        Notes:
            Read command: 0x66; returns 2-byte port number (little-endian);
            This value is meaningless in server mode
        """
        # 发送读取目标端口指令（0x66），获取2字节响应
        x = await self._config("\x66", 2)
        # 将小端序2字节数据转换为端口号整数并返回
        return int.from_bytes(x, "little")

    async def set_mode(self, mode):
        """
        设置CH9121模块的工作模式。

        Args:
            mode (int): 工作模式（0=CH9121.TCP_CLIENT, 1=CH9121.TCP_SERVER, 2=CH9121.UDP_CLIENT, 3=CH9121.UDP_SERVER）

        Returns:
            bytes: 模块返回的响应数据

        Notes:
            设置指令：0x10 + 1字节模式值（小端序）；
            模式值超出范围可能导致模块工作异常

        ---
        Set working mode of CH9121 module.

        Args:
            mode (int): Working mode (0=CH9121.TCP_CLIENT, 1=CH9121.TCP_SERVER, 2=CH9121.UDP_CLIENT, 3=CH9121.UDP_SERVER)

        Returns:
            bytes: Response data returned by the module

        Notes:
            Set command: 0x10 + 1-byte mode value (little-endian);
            Mode values outside the range may cause abnormal module operation
        """
        # 发送设置模式指令（0x10 + 1字节模式值），获取响应
        x = await self._config(b"\x10" + mode.to_bytes(1, "little"))
        # 返回响应数据
        return x

    async def set_baud_rate(self, baud):
        """
        设置CH9121模块的串口波特率。

        Args:
            baud (int): 波特率值（支持常见波特率：9600/19200/38400/115200等）

        Returns:
            bytes: 模块返回的响应数据

        Notes:
            设置指令：0x21 + 4字节波特率值（小端序）；
            设置后需确保UART通信波特率同步更新

        ---
        Set serial port baud rate of CH9121 module.

        Args:
            baud (int): Baud rate value (supports common baud rates: 9600/19200/38400/115200, etc.)

        Returns:
            bytes: Response data returned by the module

        Notes:
            Set command: 0x21 + 4-byte baud rate value (little-endian);
            Ensure UART communication baud rate is updated synchronously after setting
        """
        # 发送设置波特率指令（0x21 + 4字节波特率值），获取响应
        x = await self._config(b"\x21" + baud.to_bytes(4, "little"))
        # 返回响应数据
        return x

    async def set_local_ip(self, ip):
        """
        设置CH9121模块的本地IP地址。

        Args:
            ip (tuple): IP地址四元组 (a, b, c, d)，如 (192, 168, 1, 100)

        Returns:
            bytes: 模块返回的响应数据

        Notes:
            设置指令：0x11 + 4字节IP地址（大端序）；
            IP地址需符合IPv4规范，否则模块可能无法正常联网

        ---
        Set local IP address of CH9121 module.

        Args:
            ip (tuple): IP address quadruple (a, b, c, d), e.g. (192, 168, 1, 100)

        Returns:
            bytes: Response data returned by the module

        Notes:
            Set command: 0x11 + 4-byte IP address (big-endian);
            IP address must comply with IPv4 specifications, otherwise the module may not connect to the network normally
        """
        # 发送设置本地IP指令（0x11 + 4字节IP地址），获取响应
        x = await self._config(b"\x11" + bytes(bytearray(ip)))
        # 返回响应数据
        return x

    async def set_gateway(self, ip):
        """
        设置CH9121模块的网关地址。

        Args:
            ip (tuple): 网关地址四元组 (a, b, c, d)，如 (192, 168, 1, 1)

        Returns:
            bytes: 模块返回的响应数据

        Notes:
            设置指令：0x13 + 4字节网关地址（大端序）；
            网关地址需与本地IP在同一网段，否则无法访问外网

        ---
        Set gateway address of CH9121 module.

        Args:
            ip (tuple): Gateway address quadruple (a, b, c, d), e.g. (192, 168, 1, 1)

        Returns:
            bytes: Response data returned by the module

        Notes:
            Set command: 0x13 + 4-byte gateway address (big-endian);
            Gateway address must be in the same network segment as local IP, otherwise external network access is not possible
        """
        # 发送设置网关地址指令（0x13 + 4字节网关地址），获取响应
        x = await self._config(b"\x13" + bytes(bytearray(ip)))
        # 返回响应数据
        return x

    async def set_local_port(self, x):
        """
        设置CH9121模块的本地端口号。

        Args:
            x (int): 本地端口号（0-65535）

        Returns:
            bytes: 模块返回的响应数据

        Notes:
            设置指令：0x14 + 2字节端口号（小端序）；
            建议使用1024以上的端口号，避免占用系统端口

        ---
        Set local port number of CH9121 module.

        Args:
            x (int): Local port number (0-65535)

        Returns:
            bytes: Response data returned by the module

        Notes:
            Set command: 0x14 + 2-byte port number (little-endian);
            It is recommended to use port numbers above 1024 to avoid occupying system ports
        """
        # 发送设置本地端口指令（0x14 + 2字节端口号），获取响应
        x = await self._config(b"\x14" + x.to_bytes(2, "little"))
        # 返回响应数据
        return x

    async def set_target_ip(self, ip):
        """
        设置CH9121模块的目标IP地址（客户端模式下）。

        Args:
            ip (tuple): 目标IP地址四元组 (a, b, c, d)

        Returns:
            bytes: 模块返回的响应数据

        Notes:
            设置指令：0x15 + 4字节目标IP地址（大端序）；
            仅在TCP/UDP客户端模式下生效

        ---
        Set target IP address of CH9121 module (in client mode).

        Args:
            ip (tuple): Target IP address quadruple (a, b, c, d)

        Returns:
            bytes: Response data returned by the module

        Notes:
            Set command: 0x15 + 4-byte target IP address (big-endian);
            Only effective in TCP/UDP client mode
        """
        # 发送设置目标IP指令（0x15 + 4字节目标IP地址），获取响应
        x = await self._config(b"\x15" + bytes(bytearray(ip)))
        # 返回响应数据
        return x

    async def set_target_port(self, x):
        """
        设置CH9121模块的目标端口号（客户端模式下）。

        Args:
            x (int): 目标端口号（0-65535）

        Returns:
            bytes: 模块返回的响应数据

        Notes:
            设置指令：0x16 + 2字节端口号（小端序）；
            仅在TCP/UDP客户端模式下生效

        ---
        Set target port number of CH9121 module (in client mode).

        Args:
            x (int): Target port number (0-65535)

        Returns:
            bytes: Response data returned by the module

        Notes:
            Set command: 0x16 + 2-byte port number (little-endian);
            Only effective in TCP/UDP client mode
        """
        # 发送设置目标端口指令（0x16 + 2字节端口号），获取响应
        x = await self._config(b"\x16" + x.to_bytes(2, "little"))
        # 返回响应数据
        return x

    async def write(self, x):
        """
        异步写入数据到CH9121模块的串口。

        Args:
            x (bytes): 待写入的字节数据

        Returns:
            int: 实际写入的字节数

        Notes:
            非配置模式下的数据传输接口；
            使用异步写方法确保不阻塞事件循环

        ---
        Asynchronously write data to the serial port of CH9121 module.

        Args:
            x (bytes): Byte data to be written

        Returns:
            int: Actual number of bytes written

        Notes:
            Data transmission interface in non-configuration mode;
            Use asynchronous write method to ensure no blocking of event loop
        """
        # 异步写入数据并返回实际写入的字节数
        return await self.w.awrite(x)

    async def read(self, n):
        """
        异步从CH9121模块的串口读取指定长度的数据。

        Args:
            n (int): 期望读取的字节数

        Returns:
            bytes: 读取到的字节数据（长度可能小于n）

        Notes:
            非配置模式下的数据接收接口；
            无数据时会等待直到有数据或超时

        ---
        Asynchronously read specified length of data from the serial port of CH9121 module.

        Args:
            n (int): Expected number of bytes to read

        Returns:
            bytes: Read byte data (length may be less than n)

        Notes:
            Data reception interface in non-configuration mode;
            Waits until data is available or timeout when no data
        """
        # 异步读取n字节数据并返回
        return await self.r.read(n)

    async def readline(self):
        """
        异步从CH9121模块的串口读取数据直到换行符。

        Returns:
            bytes: 读取到的行数据（包含换行符）

        Notes:
            适用于文本数据的按行读取；
            换行符为\\n或\\r\\n

        ---
        Asynchronously read data from the serial port of CH9121 module until newline character.

        Returns:
            bytes: Read line data (including newline character)

        Notes:
            Suitable for line-by-line reading of text data;
            Newline characters are \\n or \\r\\n
        """
        # 异步读取一行数据并返回
        return await self.r.readline()

    async def reset(self):
        """
        复位CH9121模块，恢复默认配置（部分参数除外）。

        Notes:
            复位指令帧：0x57 0xab 0x02；
            复位过程约需1秒，复位后需重新配置网络参数

        ---
        Reset CH9121 module to restore default configuration (except some parameters).

        Notes:
            Reset command frame: 0x57 0xab 0x02;
            Reset process takes about 1 second, network parameters need to be reconfigured after reset
        """
        # 发送模块复位指令帧（0x57 0xab 0x02）
        await self.w.awrite(b"\x57\xab\x02")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
