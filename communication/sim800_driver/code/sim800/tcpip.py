# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午7:00
# @Author  : basanovase
# @File    : tcpip.py
# @Description : SIM800模块TCP/IP扩展类 实现TCP/UDP通信、HTTP请求、FTP文件传输等网络功能 参考自:https://github.com/basanovase/sim800
# @License : MIT

__version__ = "1.0.0"
__author__ = "basanovase"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入machine模块，用于硬件外设控制
import machine

# 从核心模块导入SIM800基类
from .core import SIM800


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class SIM800TCPIP(SIM800):
    """
    SIM800模块TCP/IP扩展类
    继承自SIM800基类，扩展实现TCP/UDP通信、HTTP请求、FTP文件传输等网络功能

    Attributes:
        uart (machine.UART): 继承自SIM800基类的UART通信对象，用于与SIM800模块进行AT指令交互
                             UART communication object inherited from SIM800 base class for AT command interaction with SIM800 module

    Methods:
        start_tcp_connection(mode, ip, port): 与目标服务器建立TCP连接，为TCP数据传输建立基础
                                               Establish TCP connection with target server to lay foundation for TCP data transmission
        send_data_tcp(data): 向已建立的TCP连接发送字符串数据
                             Send string data to established TCP connection
        receive_data_tcp(): 读取从TCP服务器接收到的数据
                            Receive data from TCP server
        close_tcp_connection(): 关闭当前TCP连接，释放网络资源
                                Close current TCP connection to release network resources
        start_udp_connection(ip, port): 与目标服务器建立UDP连接
                                        Establish UDP connection with target server
        send_data_udp(data): 向已建立的UDP连接发送字符串或字节数据
                             Send string or bytes data to established UDP connection
        receive_data_udp(max_length=1460): 读取指定最大长度的UDP接收数据
                                           Receive UDP data of specified maximum length
        close_udp_connection(): 关闭当前UDP连接，释放网络资源
                                Close current UDP connection to release network resources
        shutdown_gprs(): 关闭GPRS PDP上下文，释放所有GPRS相关网络资源
                         Shutdown GPRS PDP context to release all GPRS-related network resources
        get_ip_address(): 获取GPRS网络分配给模块的本地IP地址
                          Get local IP address assigned to module by GPRS network
        http_init(): 初始化HTTP服务上下文，为HTTP请求做准备
                     Initialize HTTP service context to prepare for HTTP requests
        http_set_param(param, value): 设置HTTP请求参数（如URL、CID等）
                                      Set HTTP request parameters (such as URL, CID, etc.)
        http_get(url): 向指定URL发送HTTP GET请求并获取响应
                       Send HTTP GET request to specified URL and get response
        http_post(url, data): 向指定URL发送HTTP POST请求并携带表单/JSON数据
                              Send HTTP POST request to specified URL with form/JSON data
        http_terminate(): 终止HTTP服务上下文，释放HTTP相关资源
                          Terminate HTTP service context to release HTTP-related resources
        ftp_init(server, username, password, port=21): 初始化FTP连接，配置服务器信息和登录凭证
                                                       Initialize FTP connection and configure server info and login credentials
        ftp_get_file(filename, remote_path): 从FTP服务器指定路径下载指定文件
                                             Download specified file from specified path of FTP server
        ftp_put_file(filename, remote_path, data): 将指定数据以指定文件名上传到FTP服务器指定路径
                                                   Upload specified data as specified filename to specified path of FTP server
        ftp_close(): 关闭FTP连接，释放SAPBR承载资源
                     Close FTP connection to release SAPBR bearer resources

    Notes:
        1. 使用TCP/UDP功能前需先完成GPRS附着和APN配置
        2. HTTP请求需先调用http_init初始化，使用完成后调用http_terminate释放资源
        3. FTP操作依赖SAPBR承载激活，操作完成后需调用ftp_close关闭连接

    ==========================================
    SIM800 Module TCP/IP Extension Class
    Inherits from SIM800 base class, extends to implement TCP/UDP communication, HTTP requests, FTP file transfer and other network functions

    Attributes:
        uart (machine.UART): UART communication object inherited from SIM800 base class for AT command interaction with SIM800 module

    Methods:
        start_tcp_connection(mode, ip, port): Establish TCP connection with target server to lay foundation for TCP data transmission
        send_data_tcp(data): Send string data to established TCP connection
        receive_data_tcp(): Receive data from TCP server
        close_tcp_connection(): Close current TCP connection to release network resources
        start_udp_connection(ip, port): Establish UDP connection with target server
        send_data_udp(data): Send string or bytes data to established UDP connection
        receive_data_udp(max_length=1460): Receive UDP data of specified maximum length
        close_udp_connection(): Close current UDP connection to release network resources
        shutdown_gprs(): Shutdown GPRS PDP context to release all GPRS-related network resources
        get_ip_address(): Get local IP address assigned to module by GPRS network
        http_init(): Initialize HTTP service context to prepare for HTTP requests
        http_set_param(param, value): Set HTTP request parameters (such as URL, CID, etc.)
        http_get(url): Send HTTP GET request to specified URL and get response
        http_post(url, data): Send HTTP POST request to specified URL with form/JSON data
        http_terminate(): Terminate HTTP service context to release HTTP-related resources
        ftp_init(server, username, password, port=21): Initialize FTP connection and configure server info and login credentials
        ftp_get_file(filename, remote_path): Download specified file from specified path of FTP server
        ftp_put_file(filename, remote_path, data): Upload specified data as specified filename to specified path of FTP server
        ftp_close(): Close FTP connection to release SAPBR bearer resources

    Notes:
        1. GPRS attachment and APN configuration must be completed before using TCP/UDP functions
        2. HTTP requests require calling http_init for initialization first, and http_terminate to release resources after use
        3. FTP operations depend on SAPBR bearer activation, need to call ftp_close to close connection after operation
    """

    def __init__(self, uart: machine.UART) -> None:
        """
        初始化SIM800TCPIP扩展类
        继承并复用SIM800基类的初始化逻辑，添加UART参数的None显式检查

        Args:
            uart (machine.UART): UART通信对象，需预先初始化（指定端口、波特率等）
                                 UART communication object, need to be initialized in advance (specify port, baud rate, etc.)

        Raises:
            TypeError: 当uart参数为None或非machine.UART实例时触发
                       Triggered when uart parameter is None or not an instance of machine.UART

        Notes:
            初始化时会自动调用SIM800基类的initialize()方法完成模块基础配置
            The initialize() method of SIM800 base class is automatically called to complete module basic configuration during initialization

        ==========================================
        Initialize SIM800TCPIP extension class
        Inherit and reuse the initialization logic of SIM800 base class, add explicit None check for UART parameter

        Args:
            uart (machine.UART): UART communication object, need to be initialized in advance (specify port, baud rate, etc.)

        Raises:
            TypeError: Triggered when uart parameter is None or not an instance of machine.UART

        Notes:
            The initialize() method of SIM800 base class is automatically called to complete module basic configuration during initialization
        """
        # 验证uart参数是否为None
        if uart is None:
            raise TypeError("uart parameter cannot be None, must be machine.UART instance")
        # 验证uart参数类型是否为machine.UART实例
        if not isinstance(uart, __import__("machine").UART):
            raise TypeError(f"Expected uart type machine.UART, got {type(uart).__name__} instead")

        # 调用父类初始化方法
        super().__init__(uart)

    def start_tcp_connection(self, mode: str, ip: str, port: int) -> bytes:
        """
        建立TCP连接
        发送AT+CIPSTART指令与目标服务器建立TCP连接，是TCP数据传输的前提

        Args:
            mode (str): 连接模式，通常为"TCP"
                        Connection mode, usually "TCP"
            ip (str): 目标服务器IP地址（IPv4格式）
                      Target server IP address (IPv4 format)
            port (int): 目标服务器端口号（1-65535）
                        Target server port number (1-65535)

        Raises:
            TypeError: 当mode/ip参数为None或非字符串类型、port参数为None或非整数类型时触发
                       Triggered when mode/ip parameter is None or not a string type, or port parameter is None or not an integer type
            ValueError: 当mode参数非"TCP"、ip参数为空字符串、port参数超出1-65535范围时触发
                        Triggered when mode parameter is not "TCP", ip parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: AT指令响应数据，包含连接建立结果（成功/失败）
                   AT command response data, including connection establishment result (success/failure)

        Notes:
            使用AT+CIPSTART指令建立TCP连接
            Use AT+CIPSTART command to establish TCP connection

        ==========================================
        Establish TCP connection
        Send AT+CIPSTART command to establish TCP connection with target server, which is a prerequisite for TCP data transmission

        Args:
            mode (str): Connection mode, usually "TCP"
            ip (str): Target server IP address (IPv4 format)
            port (int): Target server port number (1-65535)

        Raises:
            TypeError: Triggered when mode/ip parameter is None or not a string type, or port parameter is None or not an integer type
            ValueError: Triggered when mode parameter is not "TCP", ip parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: AT command response data, including connection establishment result (success/failure)

        Notes:
            Use AT+CIPSTART command to establish TCP connection
        """
        # 验证mode参数是否为None
        if mode is None:
            raise TypeError("mode parameter cannot be None, must be string")
        # 验证mode参数类型是否为字符串
        if not isinstance(mode, str):
            raise TypeError(f"Expected mode type str, got {type(mode).__name__} instead")
        # 验证mode参数值是否为"TCP"
        if mode != "TCP":
            raise ValueError(f"mode parameter must be 'TCP', got {mode}")
        # 验证ip参数是否为None
        if ip is None:
            raise TypeError("ip parameter cannot be None, must be string")
        # 验证ip参数类型是否为字符串
        if not isinstance(ip, str):
            raise TypeError(f"Expected ip type str, got {type(ip).__name__} instead")
        # 验证ip参数是否为空字符串
        if len(ip.strip()) == 0:
            raise ValueError("ip parameter cannot be empty string")
        # 验证port参数是否为None
        if port is None:
            raise TypeError("port parameter cannot be None, must be integer")
        # 验证port参数类型是否为整数
        if not isinstance(port, int):
            raise TypeError(f"Expected port type int, got {type(port).__name__} instead")
        # 验证port参数范围
        if port < 1 or port > 65535:
            raise ValueError(f"port parameter must be between 1 and 65535, got {port}")

        # 发送建立TCP连接指令并返回响应
        return self.send_command(f'AT+CIPSTART="{mode}","{ip}","{port}"')

    def send_data_tcp(self, data: str) -> bytes:
        """
        发送TCP数据
        先指定数据长度，再发送实际数据，完成TCP数据传输

        Args:
            data (str): 要发送的字符串数据
                        String data to send

        Raises:
            TypeError: 当data参数为None或非字符串类型时触发
                       Triggered when data parameter is None or not a string type
            ValueError: 当data参数为空字符串时触发
                        Triggered when data parameter is empty string

        Returns:
            bytes: 数据发送后的响应数据，包含发送结果（成功/失败）
                   Response data after data sending, including sending result (success/failure)

        Notes:
            先发送AT+CIPSEND指令指定数据长度，再发送实际数据，末尾添加ASCII码26(CTRL+Z)表示结束
            First send AT+CIPSEND command to specify data length, then send actual data, add ASCII code 26 (CTRL+Z) at end to indicate completion

        ==========================================
        Send TCP data
        Specify data length first, then send actual data to complete TCP data transmission

        Args:
            data (str): String data to send

        Raises:
            TypeError: Triggered when data parameter is None or not a string type
            ValueError: Triggered when data parameter is empty string

        Returns:
            bytes: Response data after data sending, including sending result (success/failure)

        Notes:
            First send AT+CIPSEND command to specify data length, then send actual data, add ASCII code 26 (CTRL+Z) at end to indicate completion
        """
        # 验证data参数是否为None
        if data is None:
            raise TypeError("data parameter cannot be None, must be string")
        # 验证data参数类型是否为字符串
        if not isinstance(data, str):
            raise TypeError(f"Expected data type str, got {type(data).__name__} instead")
        # 验证data参数是否为空字符串
        if len(data.strip()) == 0:
            raise ValueError("data parameter cannot be empty string")

        # 发送数据长度指令
        self.send_command(f"AT+CIPSEND={len(data)}")
        # 发送实际数据并添加结束符(ASCII 26)
        self.uart.write(data + chr(26))
        # 读取并返回响应
        return self.read_response()

    def receive_data_tcp(self) -> bytes:
        """
        接收TCP数据
        发送AT+CIPRXGET=2指令读取从TCP服务器接收到的数据

        Args:
            None

        Returns:
            bytes: 接收到的TCP数据响应，包含原始数据内容
                   Received TCP data response, including raw data content

        Notes:
            使用AT+CIPRXGET=2指令读取接收到的TCP数据
            Use AT+CIPRXGET=2 command to read received TCP data

        ==========================================
        Receive TCP data
        Send AT+CIPRXGET=2 command to read data received from TCP server

        Args:
            None

        Returns:
            bytes: Received TCP data response, including raw data content

        Notes:
            Use AT+CIPRXGET=2 command to read received TCP data
        """
        # 发送读取TCP数据指令并返回响应
        return self.send_command("AT+CIPRXGET=2")

    def close_tcp_connection(self) -> bytes:
        """
        关闭TCP连接
        发送AT+CIPCLOSE=1指令关闭当前TCP连接，释放网络资源

        Args:
            None

        Returns:
            bytes: 关闭连接指令的响应数据，包含连接关闭结果
                   Response data of close connection command, including connection close result

        Notes:
            使用AT+CIPCLOSE=1指令关闭TCP连接
            Use AT+CIPCLOSE=1 command to close TCP connection

        ==========================================
        Close TCP connection
        Send AT+CIPCLOSE=1 command to close current TCP connection and release network resources

        Args:
            None

        Returns:
            bytes: Response data of close connection command, including connection close result

        Notes:
            Use AT+CIPCLOSE=1 command to close TCP connection
        """
        # 发送关闭TCP连接指令并返回响应
        return self.send_command("AT+CIPCLOSE=1")

    def start_udp_connection(self, ip: str, port: int) -> bytes:
        """
        建立UDP连接
        发送AT+CIPSTART指令与目标服务器建立UDP连接

        Args:
            ip (str): 目标服务器IP地址（IPv4格式）
                      Target server IP address (IPv4 format)
            port (int): 目标服务器端口号（1-65535）
                        Target server port number (1-65535)

        Raises:
            TypeError: 当ip参数为None或非字符串类型、port参数为None或非整数类型时触发
                       Triggered when ip parameter is None or not a string type, or port parameter is None or not an integer type
            ValueError: 当ip参数为空字符串、port参数超出1-65535范围时触发
                        Triggered when ip parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: AT指令响应数据，包含连接建立结果
                   AT command response data, including connection establishment result

        Notes:
            使用AT+CIPSTART指令建立UDP连接
            Use AT+CIPSTART command to establish UDP connection

        ==========================================
        Establish UDP connection
        Send AT+CIPSTART command to establish UDP connection with target server

        Args:
            ip (str): Target server IP address (IPv4 format)
            port (int): Target server port number (1-65535)

        Raises:
            TypeError: Triggered when ip parameter is None or not a string type, or port parameter is None or not an integer type
            ValueError: Triggered when ip parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: AT command response data, including connection establishment result

        Notes:
            Use AT+CIPSTART command to establish UDP connection
        """
        # 验证ip参数是否为None
        if ip is None:
            raise TypeError("ip parameter cannot be None, must be string")
        # 验证ip参数类型是否为字符串
        if not isinstance(ip, str):
            raise TypeError(f"Expected ip type str, got {type(ip).__name__} instead")
        # 验证ip参数是否为空字符串
        if len(ip.strip()) == 0:
            raise ValueError("ip parameter cannot be empty string")
        # 验证port参数是否为None
        if port is None:
            raise TypeError("port parameter cannot be None, must be integer")
        # 验证port参数类型是否为整数
        if not isinstance(port, int):
            raise TypeError(f"Expected port type int, got {type(port).__name__} instead")
        # 验证port参数范围
        if port < 1 or port > 65535:
            raise ValueError(f"port parameter must be between 1 and 65535, got {port}")

        # 发送建立UDP连接指令并返回响应
        return self.send_command(f'AT+CIPSTART="UDP","{ip}","{port}"')

    def send_data_udp(self, data: str | bytes) -> bytes:
        """
        发送UDP数据
        支持字符串和字节数据类型，自动处理编码和结束符添加

        Args:
            data (str/bytes): 要发送的字符串或字节数据
                              String or bytes data to send

        Raises:
            TypeError: 当data参数为None或非字符串/字节类型时触发
                       Triggered when data parameter is None or not a string/bytes type
            ValueError: 当data参数为空字符串/空字节串时触发
                        Triggered when data parameter is empty string/empty bytes

        Returns:
            bytes: 数据发送后的响应数据，包含发送结果
                   Response data after data sending, including sending result

        Notes:
            字符串数据会自动编码为UTF-8字节串，末尾添加字节26表示结束
            String data is automatically encoded to UTF-8 bytes, add byte 26 at end to indicate completion

        ==========================================
        Send UDP data
        Support string and bytes data types, automatically handle encoding and end character addition

        Args:
            data (str/bytes): String or bytes data to send

        Raises:
            TypeError: Triggered when data parameter is None or not a string/bytes type
            ValueError: Triggered when data parameter is empty string/empty bytes

        Returns:
            bytes: Response data after data sending, including sending result

        Notes:
            String data is automatically encoded to UTF-8 bytes, add byte 26 at end to indicate completion
        """
        # 验证data参数是否为None
        if data is None:
            raise TypeError("data parameter cannot be None, must be str or bytes")
        # 验证data参数类型是否为字符串或字节
        if not isinstance(data, (str, bytes)):
            raise TypeError(f"Expected data type str or bytes, got {type(data).__name__} instead")
        # 验证data参数是否为空
        if (isinstance(data, str) and len(data.strip()) == 0) or (isinstance(data, bytes) and len(data) == 0):
            raise ValueError("data parameter cannot be empty")

        # 判断数据类型，字符串转换为字节串
        if isinstance(data, str):
            data = data.encode("utf-8")
        # 发送数据长度指令
        self.send_command(f"AT+CIPSEND={len(data)}")
        # 发送实际数据并添加结束符(字节26)
        self.uart.write(data + bytes([26]))
        # 读取并返回响应
        return self.read_response()

    def receive_data_udp(self, max_length: int = 1460) -> bytes:
        """
        接收UDP数据
        发送AT+CIPRXGET=2指令读取指定最大长度的UDP接收数据

        Args:
            max_length (int, optional): 最大接收数据长度，默认1460字节（UDP MTU）
                                        Maximum receive data length, default 1460 bytes (UDP MTU)

        Raises:
            TypeError: 当max_length参数为None或非整数类型时触发
                       Triggered when max_length parameter is None or not an integer type
            ValueError: 当max_length参数小于1或大于1460时触发
                        Triggered when max_length parameter is less than 1 or greater than 1460

        Returns:
            bytes: 接收到的UDP数据响应，包含指定长度内的原始数据
                   Received UDP data response, including raw data within specified length

        Notes:
            使用AT+CIPRXGET=2指令读取指定长度的UDP数据
            Use AT+CIPRXGET=2 command to read UDP data of specified length

        ==========================================
        Receive UDP data
        Send AT+CIPRXGET=2 command to read UDP data of specified maximum length

        Args:
            max_length (int, optional): Maximum receive data length, default 1460 bytes (UDP MTU)

        Raises:
            TypeError: Triggered when max_length parameter is None or not an integer type
            ValueError: Triggered when max_length parameter is less than 1 or greater than 1460

        Returns:
            bytes: Received UDP data response, including raw data within specified length

        Notes:
            Use AT+CIPRXGET=2 command to read UDP data of specified length
        """
        # 验证max_length参数是否为None
        if max_length is None:
            raise TypeError("max_length parameter cannot be None, must be integer")
        # 验证max_length参数类型是否为整数
        if not isinstance(max_length, int):
            raise TypeError(f"Expected max_length type int, got {type(max_length).__name__} instead")
        # 验证max_length参数范围
        if max_length < 1 or max_length > 1460:
            raise ValueError(f"max_length parameter must be between 1 and 1460, got {max_length}")

        # 发送读取UDP数据指令并返回响应
        return self.send_command(f"AT+CIPRXGET=2,{max_length}")

    def close_udp_connection(self) -> bytes:
        """
        关闭UDP连接
        发送AT+CIPCLOSE=1指令关闭当前UDP连接，释放网络资源

        Args:
            None

        Returns:
            bytes: 关闭连接指令的响应数据，包含连接关闭结果
                   Response data of close connection command, including connection close result

        Notes:
            使用AT+CIPCLOSE=1指令关闭UDP连接
            Use AT+CIPCLOSE=1 command to close UDP connection

        ==========================================
        Close UDP connection
        Send AT+CIPCLOSE=1 command to close current UDP connection and release network resources

        Args:
            None

        Returns:
            bytes: Response data of close connection command, including connection close result

        Notes:
            Use AT+CIPCLOSE=1 command to close UDP connection
        """
        # 发送关闭UDP连接指令并返回响应
        return self.send_command("AT+CIPCLOSE=1")

    def shutdown_gprs(self) -> bytes:
        """
        关闭GPRS连接
        发送AT+CIPSHUT指令关闭GPRS PDP上下文，释放所有GPRS相关网络资源

        Args:
            None

        Returns:
            bytes: 关闭GPRS指令的响应数据，包含上下文关闭结果
                   Response data of shutdown GPRS command, including context close result

        Notes:
            使用AT+CIPSHUT指令关闭GPRS PDP上下文
            Use AT+CIPSHUT command to close GPRS PDP context

        ==========================================
        Shutdown GPRS connection
        Send AT+CIPSHUT command to close GPRS PDP context and release all GPRS-related network resources

        Args:
            None

        Returns:
            bytes: Response data of shutdown GPRS command, including context close result

        Notes:
            Use AT+CIPSHUT command to close GPRS PDP context
        """
        # 发送关闭GPRS指令并返回响应
        return self.send_command("AT+CIPSHUT")

    def get_ip_address(self) -> bytes:
        """
        获取本机IP地址
        发送AT+CIFSR指令获取GPRS网络分配给模块的本地IP地址

        Args:
            None

        Returns:
            bytes: 包含IP地址的响应数据，格式为"xxx.xxx.xxx.xxx"
                   Response data containing IP address, in "xxx.xxx.xxx.xxx" format

        Notes:
            使用AT+CIFSR指令获取已分配的本地IP地址
            Use AT+CIFSR command to get assigned local IP address

        ==========================================
        Get local IP address
        Send AT+CIFSR command to get local IP address assigned to module by GPRS network

        Args:
            None

        Returns:
            bytes: Response data containing IP address, in "xxx.xxx.xxx.xxx" format

        Notes:
            Use AT+CIFSR command to get assigned local IP address
        """
        # 发送获取IP地址指令并返回响应
        return self.send_command("AT+CIFSR")

    def http_init(self) -> bytes:
        """
        初始化HTTP服务
        发送AT+HTTPINIT指令初始化HTTP服务上下文，为HTTP请求做准备

        Args:
            None

        Returns:
            bytes: 初始化指令的响应数据，包含初始化结果
                   Response data of initialization command, including initialization result

        Notes:
            使用AT+HTTPINIT指令初始化HTTP服务上下文
            Use AT+HTTPINIT command to initialize HTTP service context

        ==========================================
        Initialize HTTP service
        Send AT+HTTPINIT command to initialize HTTP service context to prepare for HTTP requests

        Args:
            None

        Returns:
            bytes: Response data of initialization command, including initialization result

        Notes:
            Use AT+HTTPINIT command to initialize HTTP service context
        """
        # 发送HTTP初始化指令并返回响应
        return self.send_command("AT+HTTPINIT")

    def http_set_param(self, param: str, value: str) -> bytes:
        """
        设置HTTP参数
        发送AT+HTTPPARA指令设置HTTP请求参数（如URL、CID等）

        Args:
            param (str): 参数名称，如"URL"、"CID"等
                         Parameter name, such as "URL", "CID", etc.
            value (str): 参数值
                         Parameter value

        Raises:
            TypeError: 当param/value参数为None或非字符串类型时触发
                       Triggered when param/value parameter is None or not a string type
            ValueError: 当param参数为空字符串时触发
                        Triggered when param parameter is empty string

        Returns:
            bytes: 设置参数指令的响应数据，包含参数设置结果
                   Response data of set parameter command, including parameter setting result

        Notes:
            使用AT+HTTPPARA指令设置HTTP请求参数
            Use AT+HTTPPARA command to set HTTP request parameters

        ==========================================
        Set HTTP parameters
        Send AT+HTTPPARA command to set HTTP request parameters (such as URL, CID, etc.)

        Args:
            param (str): Parameter name, such as "URL", "CID", etc.
            value (str): Parameter value

        Raises:
            TypeError: Triggered when param/value parameter is None or not a string type
            ValueError: Triggered when param parameter is empty string

        Returns:
            bytes: Response data of set parameter command, including parameter setting result

        Notes:
            Use AT+HTTPPARA command to set HTTP request parameters
        """
        # 验证param参数是否为None
        if param is None:
            raise TypeError("param parameter cannot be None, must be string")
        # 验证param参数类型是否为字符串
        if not isinstance(param, str):
            raise TypeError(f"Expected param type str, got {type(param).__name__} instead")
        # 验证param参数是否为空字符串
        if len(param.strip()) == 0:
            raise ValueError("param parameter cannot be empty string")
        # 验证value参数是否为None
        if value is None:
            raise TypeError("value parameter cannot be None, must be string")
        # 验证value参数类型是否为字符串
        if not isinstance(value, str):
            raise TypeError(f"Expected value type str, got {type(value).__name__} instead")

        # 发送设置HTTP参数指令并返回响应
        return self.send_command(f'AT+HTTPPARA="{param}","{value}"')

    def http_get(self, url: str) -> bytes:
        """
        发送HTTP GET请求
        先设置URL参数，再发送AT+HTTPACTION=0指令执行GET请求并获取响应

        Args:
            url (str): 请求的URL地址（完整格式，如"http://example.com/api"）
                       Requested URL address (full format, such as "http://example.com/api")

        Raises:
            TypeError: 当url参数为None或非字符串类型时触发
                       Triggered when url parameter is None or not a string type
            ValueError: 当url参数为空字符串时触发
                        Triggered when url parameter is empty string

        Returns:
            bytes: GET请求的响应数据，包含HTTP状态码和响应内容
                   Response data of GET request, including HTTP status code and response content

        Notes:
            先设置URL参数，再发送AT+HTTPACTION=0指令执行GET请求
            First set URL parameter, then send AT+HTTPACTION=0 command to execute GET request

        ==========================================
        Send HTTP GET request
        Set URL parameter first, then send AT+HTTPACTION=0 command to execute GET request and get response

        Args:
            url (str): Requested URL address (full format, such as "http://example.com/api")

        Raises:
            TypeError: Triggered when url parameter is None or not a string type
            ValueError: Triggered when url parameter is empty string

        Returns:
            bytes: Response data of GET request, including HTTP status code and response content

        Notes:
            First set URL parameter, then send AT+HTTPACTION=0 command to execute GET request
        """
        # 验证url参数是否为None
        if url is None:
            raise TypeError("url parameter cannot be None, must be string")
        # 验证url参数类型是否为字符串
        if not isinstance(url, str):
            raise TypeError(f"Expected url type str, got {type(url).__name__} instead")
        # 验证url参数是否为空字符串
        if len(url.strip()) == 0:
            raise ValueError("url parameter cannot be empty string")

        # 设置HTTP请求URL参数
        self.http_set_param("URL", url)
        # 发送HTTP GET请求指令
        self.send_command("AT+HTTPACTION=0")
        # 读取并返回响应
        return self.read_response()

    def http_post(self, url: str, data: str) -> bytes:
        """
        发送HTTP POST请求
        先设置URL参数，再配置POST数据，最后发送AT+HTTPACTION=1指令执行POST请求

        Args:
            url (str): 请求的URL地址（完整格式，如"http://example.com/api"）
                       Requested URL address (full format, such as "http://example.com/api")
            data (str): POST请求的表单数据或JSON数据（如"name=test&age=18"或'{"name":"test"}'）
                        Form data or JSON data for POST request (such as "name=test&age=18" or '{"name":"test"}')

        Raises:
            TypeError: 当url/data参数为None或非字符串类型时触发
                       Triggered when url/data parameter is None or not a string type
            ValueError: 当url参数为空字符串、data参数为空字符串时触发
                        Triggered when url parameter is empty string or data parameter is empty string

        Returns:
            bytes: POST请求的响应数据，包含HTTP状态码和响应内容
                   Response data of POST request, including HTTP status code and response content

        Notes:
            使用AT+HTTPDATA指令设置POST数据，超时时间10秒，再发送AT+HTTPACTION=1执行POST请求
            Use AT+HTTPDATA command to set POST data with 10-second timeout, then send AT+HTTPACTION=1 to execute POST request

        ==========================================
        Send HTTP POST request
        Set URL parameter first, then configure POST data, finally send AT+HTTPACTION=1 command to execute POST request

        Args:
            url (str): Requested URL address (full format, such as "http://example.com/api")
            data (str): Form data or JSON data for POST request (such as "name=test&age=18" or '{"name":"test"}')

        Raises:
            TypeError: Triggered when url/data parameter is None or not a string type
            ValueError: Triggered when url parameter is empty string or data parameter is empty string

        Returns:
            bytes: Response data of POST request, including HTTP status code and response content

        Notes:
            Use AT+HTTPDATA command to set POST data with 10-second timeout, then send AT+HTTPACTION=1 to execute POST request
        """
        # 验证url参数是否为None
        if url is None:
            raise TypeError("url parameter cannot be None, must be string")
        # 验证url参数类型是否为字符串
        if not isinstance(url, str):
            raise TypeError(f"Expected url type str, got {type(url).__name__} instead")
        # 验证url参数是否为空字符串
        if len(url.strip()) == 0:
            raise ValueError("url parameter cannot be empty string")
        # 验证data参数是否为None
        if data is None:
            raise TypeError("data parameter cannot be None, must be string")
        # 验证data参数类型是否为字符串
        if not isinstance(data, str):
            raise TypeError(f"Expected data type str, got {type(data).__name__} instead")
        # 验证data参数是否为空字符串
        if len(data.strip()) == 0:
            raise ValueError("data parameter cannot be empty string")

        # 设置HTTP请求URL参数
        self.http_set_param("URL", url)
        # 设置POST数据长度和超时时间(10000ms)
        self.send_command(f"AT+HTTPDATA={len(data)},10000")
        # 发送POST数据
        self.uart.write(data)
        # 发送HTTP POST请求指令
        self.send_command("AT+HTTPACTION=1")
        # 读取并返回响应
        return self.read_response()

    def http_terminate(self) -> bytes:
        """
        终止HTTP服务
        发送AT+HTTPTERM指令关闭HTTP服务上下文，释放HTTP相关资源

        Args:
            None

        Returns:
            bytes: 终止HTTP服务指令的响应数据，包含终止结果
                   Response data of terminate HTTP service command, including termination result

        Notes:
            使用AT+HTTPTERM指令关闭HTTP服务上下文
            Use AT+HTTPTERM command to close HTTP service context

        ==========================================
        Terminate HTTP service
        Send AT+HTTPTERM command to close HTTP service context and release HTTP-related resources

        Args:
            None

        Returns:
            bytes: Response data of terminate HTTP service command, including termination result

        Notes:
            Use AT+HTTPTERM command to close HTTP service context
        """
        # 发送终止HTTP服务指令并返回响应
        return self.send_command("AT+HTTPTERM")

    def ftp_init(self, server: str, username: str, password: str, port: int = 21) -> bytes:
        """
        初始化FTP连接
        依次配置SAPBR、FTP服务器信息和登录凭证，完成FTP连接初始化

        Args:
            server (str): FTP服务器IP地址或域名（如"192.168.1.100"或"ftp.example.com"）
                          FTP server IP address or domain name (such as "192.168.1.100" or "ftp.example.com")
            username (str): FTP登录用户名
                            FTP login username
            password (str): FTP登录密码
                            FTP login password
            port (int, optional): FTP服务器端口号，默认21
                                  FTP server port number, default 21

        Raises:
            TypeError: 当server/username/password参数为None或非字符串类型、port参数为None或非整数类型时触发
                       Triggered when server/username/password parameter is None or not a string type, or port parameter is None or not an integer type
            ValueError: 当server/username参数为空字符串、port参数超出1-65535范围时触发
                        Triggered when server/username parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: 设置FTP密码后的响应数据，包含FTP初始化结果
                   Response data after setting FTP password, including FTP initialization result

        Notes:
            依次配置GPRS上下文、激活SAPBR、设置FTP服务器信息和登录凭证
            Configure GPRS context, activate SAPBR, set FTP server info and login credentials in sequence

        ==========================================
        Initialize FTP connection
        Configure SAPBR, FTP server info and login credentials in sequence to complete FTP connection initialization

        Args:
            server (str): FTP server IP address or domain name (such as "192.168.1.100" or "ftp.example.com")
            username (str): FTP login username
            password (str): FTP login password
            port (int, optional): FTP server port number, default 21

        Raises:
            TypeError: Triggered when server/username/password parameter is None or not a string type, or port parameter is None or not an integer type
            ValueError: Triggered when server/username parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: Response data after setting FTP password, including FTP initialization result

        Notes:
            Configure GPRS context, activate SAPBR, set FTP server info and login credentials in sequence
        """
        # 验证server参数是否为None
        if server is None:
            raise TypeError("server parameter cannot be None, must be string")
        # 验证server参数类型是否为字符串
        if not isinstance(server, str):
            raise TypeError(f"Expected server type str, got {type(server).__name__} instead")
        # 验证server参数是否为空字符串
        if len(server.strip()) == 0:
            raise ValueError("server parameter cannot be empty string")
        # 验证username参数是否为None
        if username is None:
            raise TypeError("username parameter cannot be None, must be string")
        # 验证username参数类型是否为字符串
        if not isinstance(username, str):
            raise TypeError(f"Expected username type str, got {type(username).__name__} instead")
        # 验证username参数是否为空字符串
        if len(username.strip()) == 0:
            raise ValueError("username parameter cannot be empty string")
        # 验证password参数是否为None
        if password is None:
            raise TypeError("password parameter cannot be None, must be string")
        # 验证password参数类型是否为字符串
        if not isinstance(password, str):
            raise TypeError(f"Expected password type str, got {type(password).__name__} instead")
        # 验证port参数是否为None
        if port is None:
            raise TypeError("port parameter cannot be None, must be integer")
        # 验证port参数类型是否为整数
        if not isinstance(port, int):
            raise TypeError(f"Expected port type int, got {type(port).__name__} instead")
        # 验证port参数范围
        if port < 1 or port > 65535:
            raise ValueError(f"port parameter must be between 1 and 65535, got {port}")

        # 设置SAPBR连接类型为GPRS
        self.send_command('AT+SAPBR=3,1,"Contype","GPRS"')
        # 激活SAPBR承载
        self.send_command("AT+SAPBR=1,1")
        # 设置FTP使用的CID
        self.send_command("AT+FTPCID=1")
        # 设置FTP服务器地址
        self.send_command(f'AT+FTPSERV="{server}"')
        # 设置FTP服务器端口
        self.send_command(f"AT+FTPPORT={port}")
        # 设置FTP登录用户名
        self.send_command(f'AT+FTPUN="{username}"')
        # 设置FTP登录密码并返回响应
        return self.send_command(f'AT+FTPPW="{password}"')

    def ftp_get_file(self, filename: str, remote_path: str) -> bytes:
        """
        从FTP服务器下载文件
        配置下载路径和文件名，发送AT+FTPGET指令从FTP服务器下载指定文件

        Args:
            filename (str): 要下载的文件名（包含扩展名，如"test.txt"）
                            File name to download (including extension, such as "test.txt")
            remote_path (str): 远程文件路径（如"/data/"）
                               Remote file path (such as "/data/")

        Raises:
            TypeError: 当filename/remote_path参数为None或非字符串类型时触发
                       Triggered when filename/remote_path parameter is None or not a string type
            ValueError: 当filename参数为空字符串时触发
                        Triggered when filename parameter is empty string

        Returns:
            bytes: 文件下载指令的响应数据，包含下载结果和文件内容
                   Response data of file download command, including download result and file content

        Notes:
            超时时间设置为10秒，最大读取长度1024字节
            Timeout set to 10 seconds, maximum read length 1024 bytes

        ==========================================
        Download file from FTP server
        Configure download path and file name, send AT+FTPGET command to download specified file from FTP server

        Args:
            filename (str): File name to download (including extension, such as "test.txt")
            remote_path (str): Remote file path (such as "/data/")

        Raises:
            TypeError: Triggered when filename/remote_path parameter is None or not a string type
            ValueError: Triggered when filename parameter is empty string

        Returns:
            bytes: Response data of file download command, including download result and file content

        Notes:
            Timeout set to 10 seconds, maximum read length 1024 bytes
        """
        # 验证filename参数是否为None
        if filename is None:
            raise TypeError("filename parameter cannot be None, must be string")
        # 验证filename参数类型是否为字符串
        if not isinstance(filename, str):
            raise TypeError(f"Expected filename type str, got {type(filename).__name__} instead")
        # 验证filename参数是否为空字符串
        if len(filename.strip()) == 0:
            raise ValueError("filename parameter cannot be empty string")
        # 验证remote_path参数是否为None
        if remote_path is None:
            raise TypeError("remote_path parameter cannot be None, must be string")
        # 验证remote_path参数类型是否为字符串
        if not isinstance(remote_path, str):
            raise TypeError(f"Expected remote_path type str, got {type(remote_path).__name__} instead")

        # 设置FTP下载文件路径
        self.send_command(f'AT+FTPGETPATH="{remote_path}"')
        # 设置FTP下载文件名
        self.send_command(f'AT+FTPGETNAME="{filename}"')
        # 启动FTP下载
        self.send_command("AT+FTPGET=1")
        # 读取下载文件数据(超时10000ms)并返回响应
        return self.send_command("AT+FTPGET=2,1024", timeout=10000)

    def ftp_put_file(self, filename: str, remote_path: str, data: str | bytes) -> bytes:
        """
        上传文件到FTP服务器
        配置上传路径和文件名，发送指定数据到FTP服务器指定路径

        Args:
            filename (str): 要上传的文件名（包含扩展名，如"test.txt"）
                            File name to upload (including extension, such as "test.txt")
            remote_path (str): 远程文件路径（如"/upload/"）
                               Remote file path (such as "/upload/")
            data (str/bytes): 要上传的文件数据（字符串或字节格式）
                              File data to upload (string or bytes format)

        Raises:
            TypeError: 当filename/remote_path参数为None或非字符串类型、data参数为None或非字符串/字节类型时触发
                       Triggered when filename/remote_path parameter is None or not a string type, or data parameter is None or not a string/bytes type
            ValueError: 当filename参数为空字符串、data参数为空字符串/空字节串时触发
                        Triggered when filename parameter is empty string, or data parameter is empty string/empty bytes

        Returns:
            bytes: 文件上传后的响应数据，包含上传结果
                   Response data after file upload, including upload result

        Notes:
            字符串数据会自动编码为UTF-8字节串，支持字节串和字符串两种数据格式
            String data is automatically encoded to UTF-8 bytes, supports both bytes and string data formats

        ==========================================
        Upload file to FTP server
        Configure upload path and file name, send specified data to specified path of FTP server

        Args:
            filename (str): File name to upload (including extension, such as "test.txt")
            remote_path (str): Remote file path (such as "/upload/")
            data (str/bytes): File data to upload (string or bytes format)

        Raises:
            TypeError: Triggered when filename/remote_path parameter is None or not a string type, or data parameter is None or not a string/bytes type
            ValueError: Triggered when filename parameter is empty string, or data parameter is empty string/empty bytes

        Returns:
            bytes: Response data after file upload, including upload result

        Notes:
            String data is automatically encoded to UTF-8 bytes, supports both bytes and string data formats
        """
        # 验证filename参数是否为None
        if filename is None:
            raise TypeError("filename parameter cannot be None, must be string")
        # 验证filename参数类型是否为字符串
        if not isinstance(filename, str):
            raise TypeError(f"Expected filename type str, got {type(filename).__name__} instead")
        # 验证filename参数是否为空字符串
        if len(filename.strip()) == 0:
            raise ValueError("filename parameter cannot be empty string")
        # 验证remote_path参数是否为None
        if remote_path is None:
            raise TypeError("remote_path parameter cannot be None, must be string")
        # 验证remote_path参数类型是否为字符串
        if not isinstance(remote_path, str):
            raise TypeError(f"Expected remote_path type str, got {type(remote_path).__name__} instead")
        # 验证data参数是否为None
        if data is None:
            raise TypeError("data parameter cannot be None, must be str or bytes")
        # 验证data参数类型是否为字符串或字节
        if not isinstance(data, (str, bytes)):
            raise TypeError(f"Expected data type str or bytes, got {type(data).__name__} instead")
        # 验证data参数是否为空
        if (isinstance(data, str) and len(data.strip()) == 0) or (isinstance(data, bytes) and len(data) == 0):
            raise ValueError("data parameter cannot be empty")

        # 设置FTP上传文件路径
        self.send_command(f'AT+FTPPUTPATH="{remote_path}"')
        # 设置FTP上传文件名
        self.send_command(f'AT+FTPPUTNAME="{filename}"')
        # 启动FTP上传
        self.send_command("AT+FTPPUT=1")
        # 设置上传数据长度
        self.send_command(f"AT+FTPPUT=2,{len(data)}")
        # 发送上传数据(自动转换为字节串)
        self.uart.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        # 读取并返回响应
        return self.read_response()

    def ftp_close(self) -> bytes:
        """
        关闭FTP连接
        发送AT+SAPBR=0,1指令关闭SAPBR承载，终止FTP连接并释放资源

        Args:
            None

        Returns:
            bytes: 关闭FTP连接指令的响应数据，包含连接关闭结果
                   Response data of close FTP connection command, including connection close result

        Notes:
            使用AT+SAPBR=0,1指令关闭SAPBR承载来终止FTP连接
            Use AT+SAPBR=0,1 command to close SAPBR bearer to terminate FTP connection

        ==========================================
        Close FTP connection
        Send AT+SAPBR=0,1 command to close SAPBR bearer to terminate FTP connection and release resources

        Args:
            None

        Returns:
            bytes: Response data of close FTP connection command, including connection close result

        Notes:
            Use AT+SAPBR=0,1 command to close SAPBR bearer to terminate FTP connection
        """
        # 发送关闭FTP连接指令并返回响应
        return self.send_command("AT+SAPBR=0,1")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
