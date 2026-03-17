# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午8:00
# @Author  : alankrantas
# @File    : gprs.py
# @Description : SIM800模块GPRS扩展类 实现GPRS附着/分离、APN配置、TCP通信、GSM定位等功能
# @License : MIT

__version__ = "1.0.0"
__author__ = "alankrantas"
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


class SIM800GPRS(SIM800):
    """
    SIM800模块GPRS扩展类
    继承自SIM800基类，扩展实现GPRS附着/分离、APN配置、TCP通信、GSM基站定位等GPRS相关功能

    Attributes:
        uart (machine.UART): 继承自SIM800基类的UART通信对象，用于与SIM800模块通信
                             UART communication object inherited from SIM800 base class for communicating with SIM800 module

    Methods:
        attach_gprs(): 附着GPRS网络，为后续数据通信建立基础
                       Attach to GPRS network to establish foundation for subsequent data communication
        detach_gprs(): 分离GPRS网络，释放GPRS网络资源
                       Detach from GPRS network to release GPRS network resources
        set_apn(apn, user='', pwd=''): 设置APN参数并激活GPRS PDP上下文
                                       Set APN parameters and activate GPRS PDP context
        get_ip_address(): 获取GPRS网络分配的本地IP地址
                          Get local IP address assigned by GPRS network
        start_tcp_connection(mode, ip, port): 与目标服务器建立TCP连接
                                               Establish TCP connection with target server
        send_data_tcp(data): 向已建立的TCP连接发送字符串数据
                             Send string data to established TCP connection
        close_tcp_connection(): 关闭当前TCP连接，释放网络连接资源
                                Close current TCP connection to release network connection resources
        shutdown_gprs(): 关闭GPRS PDP上下文，释放所有GPRS相关网络资源
                         Shutdown GPRS PDP context to release all GPRS-related network resources
        get_gsm_location(): 获取GSM基站定位信息（LAC/CI等）
                            Get GSM base station location information (LAC/CI, etc.)

    Notes:
        1. 使用GPRS功能前必须先完成GPRS附着(attach_gprs)和APN配置(set_apn)
        2. TCP通信需先建立连接，通信完成后需关闭连接避免资源泄露
        3. GSM定位功能依赖运营商网络支持，部分地区可能无法获取有效数据

    ==========================================
    SIM800 Module GPRS Extension Class
    Inherits from SIM800 base class, extends to implement GPRS attach/detach, APN configuration, TCP communication, GSM base station positioning and other GPRS-related functions

    Attributes:
        uart (machine.UART): UART communication object inherited from SIM800 base class for communicating with SIM800 module

    Methods:
        attach_gprs(): Attach to GPRS network to establish foundation for subsequent data communication
        detach_gprs(): Detach from GPRS network to release GPRS network resources
        set_apn(apn, user='', pwd=''): Set APN parameters and activate GPRS PDP context
        get_ip_address(): Get local IP address assigned by GPRS network
        start_tcp_connection(mode, ip, port): Establish TCP connection with target server
        send_data_tcp(data): Send string data to established TCP connection
        close_tcp_connection(): Close current TCP connection to release network connection resources
        shutdown_gprs(): Shutdown GPRS PDP context to release all GPRS-related network resources
        get_gsm_location(): Get GSM base station location information (LAC/CI, etc.)

    Notes:
        1. Must complete GPRS attachment (attach_gprs) and APN configuration (set_apn) before using GPRS functions
        2. TCP communication requires establishing connection first, and closing connection after communication to avoid resource leakage
        3. GSM positioning function depends on operator network support, valid data may not be obtained in some regions
    """

    def __init__(self, uart: machine.UART) -> None:
        """
        初始化SIM800GPRS扩展类
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
        Initialize SIM800GPRS extension class
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

    def attach_gprs(self) -> bytes:
        """
        附着GPRS网络
        发送AT+CGATT=1指令完成GPRS网络附着，是所有GPRS数据通信的前提

        Args:
            None

        Returns:
            bytes: 附着指令的响应数据，包含网络附着结果
                   Response data of attach command, including network attachment result

        Notes:
            使用AT+CGATT=1指令附着GPRS网络，附着成功后才能进行后续数据通信
            Use AT+CGATT=1 command to attach to GPRS network, subsequent data communication is only possible after successful attachment

        ==========================================
        Attach to GPRS network
        Send AT+CGATT=1 command to complete GPRS network attachment, which is a prerequisite for all GPRS data communication

        Args:
            None

        Returns:
            bytes: Response data of attach command, including network attachment result

        Notes:
            Use AT+CGATT=1 command to attach to GPRS network, subsequent data communication is only possible after successful attachment
        """
        # 发送GPRS附着指令并返回响应
        return self.send_command("AT+CGATT=1")

    def detach_gprs(self) -> bytes:
        """
        分离GPRS网络
        发送AT+CGATT=0指令完成GPRS网络分离，释放GPRS网络占用的资源

        Args:
            None

        Returns:
            bytes: 分离指令的响应数据，包含网络分离结果
                   Response data of detach command, including network detachment result

        Notes:
            使用AT+CGATT=0指令分离GPRS网络，分离后无法进行数据通信
            Use AT+CGATT=0 command to detach from GPRS network, data communication is not possible after detachment

        ==========================================
        Detach from GPRS network
        Send AT+CGATT=0 command to complete GPRS network detachment, release resources occupied by GPRS network

        Args:
            None

        Returns:
            bytes: Response data of detach command, including network detachment result

        Notes:
            Use AT+CGATT=0 command to detach from GPRS network, data communication is not possible after detachment
        """
        # 发送GPRS分离指令并返回响应
        return self.send_command("AT+CGATT=0")

    def set_apn(self, apn: str, user: str = "", pwd: str = "") -> bytes:
        """
        设置APN并激活GPRS上下文
        先配置APN参数，再激活GPRS PDP上下文，为获取IP地址和TCP通信做准备

        Args:
            apn (str): 接入点名称(Access Point Name)，如"cmnet"、"3gnet"等
                       Access Point Name, such as "cmnet", "3gnet", etc.
            user (str, optional): APN用户名，默认为空字符串
                                  APN username, default empty string
            pwd (str, optional): APN密码，默认为空字符串
                                 APN password, default empty string

        Raises:
            TypeError: 当apn/user/pwd参数为None或非字符串类型时触发
                       Triggered when apn/user/pwd parameter is None or not a string type
            ValueError: 当apn参数为空字符串时触发
                        Triggered when apn parameter is an empty string

        Returns:
            bytes: 激活GPRS上下文指令的响应数据，包含上下文激活结果
                   Response data of activate GPRS context command, including context activation result

        Notes:
            先使用AT+CSTT设置APN参数，再使用AT+CIICR激活GPRS PDP上下文
            First use AT+CSTT to set APN parameters, then use AT+CIICR to activate GPRS PDP context

        ==========================================
        Set APN and activate GPRS context
        Configure APN parameters first, then activate GPRS PDP context to prepare for obtaining IP address and TCP communication

        Args:
            apn (str): Access Point Name, such as "cmnet", "3gnet", etc.
            user (str, optional): APN username, default empty string
            pwd (str, optional): APN password, default empty string

        Raises:
            TypeError: Triggered when apn/user/pwd parameter is None or not a string type
            ValueError: Triggered when apn parameter is an empty string

        Returns:
            bytes: Response data of activate GPRS context command, including context activation result

        Notes:
            First use AT+CSTT to set APN parameters, then use AT+CIICR to activate GPRS PDP context
        """
        # 验证apn参数是否为None
        if apn is None:
            raise TypeError("apn parameter cannot be None, must be string")
        # 验证apn参数类型是否为字符串
        if not isinstance(apn, str):
            raise TypeError(f"Expected apn type str, got {type(apn).__name__} instead")
        # 验证apn参数是否为空字符串
        if len(apn.strip()) == 0:
            raise ValueError("apn parameter cannot be empty string")
        # 验证user参数是否为None
        if user is None:
            raise TypeError("user parameter cannot be None, must be string")
        # 验证user参数类型是否为字符串
        if not isinstance(user, str):
            raise TypeError(f"Expected user type str, got {type(user).__name__} instead")
        # 验证pwd参数是否为None
        if pwd is None:
            raise TypeError("pwd parameter cannot be None, must be string")
        # 验证pwd参数类型是否为字符串
        if not isinstance(pwd, str):
            raise TypeError(f"Expected pwd type str, got {type(pwd).__name__} instead")

        # 发送设置APN参数指令
        self.send_command(f'AT+CSTT="{apn}","{user}","{pwd}"')
        # 发送激活GPRS上下文指令并返回响应
        return self.send_command("AT+CIICR")

    def get_ip_address(self) -> bytes:
        """
        获取GPRS分配的IP地址
        发送AT+CIFSR指令获取GPRS网络为模块分配的本地IP地址

        Args:
            None

        Returns:
            bytes: 包含IP地址的响应数据，格式通常为"xxx.xxx.xxx.xxx"
                   Response data containing IP address, usually in "xxx.xxx.xxx.xxx" format

        Notes:
            使用AT+CIFSR指令获取GPRS网络分配的本地IP地址，需先激活GPRS上下文
            Use AT+CIFSR command to get local IP address assigned by GPRS network, GPRS context must be activated first

        ==========================================
        Get IP address assigned by GPRS
        Send AT+CIFSR command to get local IP address assigned to the module by GPRS network

        Args:
            None

        Returns:
            bytes: Response data containing IP address, usually in "xxx.xxx.xxx.xxx" format

        Notes:
            Use AT+CIFSR command to get local IP address assigned by GPRS network, GPRS context must be activated first
        """
        # 发送获取IP地址指令并返回响应
        return self.send_command("AT+CIFSR")

    def start_tcp_connection(self, mode: str, ip: str, port: int) -> bytes:
        """
        建立TCP连接
        发送AT+CIPSTART指令与目标服务器建立TCP连接，需先完成GPRS附着和APN配置

        Args:
            mode (str): 连接模式，通常为"TCP"
                        Connection mode, usually "TCP"
            ip (str): 目标服务器IP地址（IPv4格式）
                      Target server IP address (IPv4 format)
            port (int): 目标服务器端口号（1-65535）
                        Target server port number (1-65535)

        Raises:
            TypeError: 当mode/ip参数为None或非字符串类型、port参数非整数类型时触发
                       Triggered when mode/ip parameter is None or not a string type, or port parameter is not an integer type
            ValueError: 当mode参数非"TCP"、ip参数为空字符串、port参数超出1-65535范围时触发
                        Triggered when mode parameter is not "TCP", ip parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: 建立连接指令的响应数据，包含连接建立结果
                   Response data of establish connection command, including connection establishment result

        Notes:
            使用AT+CIPSTART指令建立TCP连接，需先完成GPRS附着和APN配置
            Use AT+CIPSTART command to establish TCP connection, GPRS attachment and APN configuration must be completed first

        ==========================================
        Establish TCP connection
        Send AT+CIPSTART command to establish TCP connection with target server, GPRS attachment and APN configuration must be completed first

        Args:
            mode (str): Connection mode, usually "TCP"
            ip (str): Target server IP address (IPv4 format)
            port (int): Target server port number (1-65535)

        Raises:
            TypeError: Triggered when mode/ip parameter is None or not a string type, or port parameter is not an integer type
            ValueError: Triggered when mode parameter is not "TCP", ip parameter is empty string, or port parameter is out of 1-65535 range

        Returns:
            bytes: Response data of establish connection command, including connection establishment result

        Notes:
            Use AT+CIPSTART command to establish TCP connection, GPRS attachment and APN configuration must be completed first
        """
        # 验证mode参数是否为None
        if mode is None:
            raise TypeError("mode parameter cannot be None, must be string")
        # 验证mode参数类型是否为字符串
        if not isinstance(mode, str):
            raise TypeError(f"Expected mode type str, got {type(mode).__name__} instead")
        # 验证mode参数是否为"TCP"
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
                        Triggered when data parameter is an empty string

        Returns:
            bytes: 数据发送后的响应数据，包含数据发送结果
                   Response data after data sending, including data sending result

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
            ValueError: Triggered when data parameter is an empty string

        Returns:
            bytes: Response data after data sending, including data sending result

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
        # 读取并返回发送响应
        return self.read_response()

    def close_tcp_connection(self) -> bytes:
        """
        关闭TCP连接
        发送AT+CIPCLOSE=1指令关闭当前TCP连接，释放网络连接资源

        Args:
            None

        Returns:
            bytes: 关闭连接指令的响应数据，包含连接关闭结果
                   Response data of close connection command, including connection close result

        Notes:
            使用AT+CIPCLOSE=1指令关闭TCP连接，释放网络资源
            Use AT+CIPCLOSE=1 command to close TCP connection and release network resources

        ==========================================
        Close TCP connection
        Send AT+CIPCLOSE=1 command to close current TCP connection and release network connection resources

        Args:
            None

        Returns:
            bytes: Response data of close connection command, including connection close result

        Notes:
            Use AT+CIPCLOSE=1 command to close TCP connection and release network resources
        """
        # 发送关闭TCP连接指令并返回响应
        return self.send_command("AT+CIPCLOSE=1")

    def shutdown_gprs(self) -> bytes:
        """
        关闭GPRS PDP上下文
        发送AT+CIPSHUT指令关闭GPRS PDP上下文，释放所有GPRS相关网络资源

        Args:
            None

        Returns:
            bytes: 关闭GPRS指令的响应数据，包含上下文关闭结果
                   Response data of shutdown GPRS command, including context close result

        Notes:
            使用AT+CIPSHUT指令关闭GPRS PDP上下文，释放所有GPRS相关资源
            Use AT+CIPSHUT command to close GPRS PDP context and release all GPRS-related resources

        ==========================================
        Shutdown GPRS PDP context
        Send AT+CIPSHUT command to close GPRS PDP context and release all GPRS-related network resources

        Args:
            None

        Returns:
            bytes: Response data of shutdown GPRS command, including context close result

        Notes:
            Use AT+CIPSHUT command to close GPRS PDP context and release all GPRS-related resources
        """
        # 发送关闭GPRS指令并返回响应
        return self.send_command("AT+CIPSHUT")

    def get_gsm_location(self) -> bytes:
        """
        获取GSM基站定位信息
        发送AT+CIPGSMLOC=1,1指令获取基于GSM基站的位置信息

        Args:
            None

        Returns:
            bytes: 包含GSM基站定位信息的响应数据，包含LAC、CI、信号强度等参数
                   Response data containing GSM base station location information, including LAC, CI, signal strength and other parameters

        Notes:
            使用AT+CIPGSMLOC=1,1指令获取基于GSM基站的位置信息，包含LAC和CI等基站参数
            Use AT+CIPGSMLOC=1,1 command to get location information based on GSM base station, including LAC, CI and other base station parameters

        ==========================================
        Get GSM base station location information
        Send AT+CIPGSMLOC=1,1 command to get location information based on GSM base station

        Args:
            None

        Returns:
            bytes: Response data containing GSM base station location information, including LAC, CI, signal strength and other parameters

        Notes:
            Use AT+CIPGSMLOC=1,1 command to get location information based on GSM base station, including LAC, CI and other base station parameters
        """
        # 发送获取GSM定位信息指令
        response = self.send_command("AT+CIPGSMLOC=1,1")
        # 返回定位响应数据
        return response


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
