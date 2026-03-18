# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午9:00
# @Author  : basanovase
# @File    : tcpip.py
# @Description : SIM7600模块TCP/IP功能类 实现APN配置、网络连接管理、数据收发等TCP/IP通信功能 参考自：https://github.com/basanovase/sim7600
# @License : MIT
__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class TCPIP:
    """
    SIM7600模块TCP/IP功能类
    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法

    Methods:
        __init__(sim7600): 初始化TCP/IP功能类
        set_apn(apn, user="", password=""): 配置APN参数及认证信息
        open_connection(protocol, remote_ip, remote_port): 打开网络连接
        close_connection(): 关闭网络连接
        send_data(data): 发送网络数据
        receive_data(): 接收网络数据

    Notes:
        所有TCP/IP通信操作依赖SIM7600核心对象的AT指令发送和UART读写能力，使用前需确保核心对象方法正常可用
        网络连接建立前必须先配置正确的APN参数，不同运营商的APN参数不同（如移动：cmnet，联通：3gnet，电信：ctnet）

    ==========================================
    SIM7600 Module TCP/IP Function Class
    Attributes:
        sim7600 (object): SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): Initialize TCP/IP function class
        set_apn(apn, user="", password=""): Configure APN parameters and authentication information
        open_connection(protocol, remote_ip, remote_port): Open network connection
        close_connection(): Close network connection
        send_data(data): Send network data
        receive_data(): Receive network data

    Notes:
        All TCP/IP communication operations depend on the AT command sending and UART read/write capabilities of the SIM7600 core object, ensure the core object methods are available before use
        Correct APN parameters must be configured before establishing a network connection, different operators have different APN parameters (e.g., China Mobile: cmnet, China Unicom: 3gnet, China Telecom: ctnet)
    """

    def __init__(self, sim7600: object) -> None:
        """
        初始化TCP/IP功能类
        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法

        Raises:
            TypeError: 当sim7600参数为None时触发
            AttributeError: 当sim7600对象缺少必要方法（send_command/write_uart/read_uart）时触发

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成网络通信

        ==========================================
        Initialize TCP/IP function class
        Args:
            sim7600 (object): SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Raises:
            TypeError: Triggered when sim7600 parameter is None
            AttributeError: Triggered when sim7600 object lacks necessary methods (send_command/write_uart/read_uart)

        Notes:
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete network communication
        """
        # 检查sim7600参数是否为None
        if sim7600 is None:
            raise TypeError("sim7600 parameter cannot be None")
        # 检查sim7600对象是否包含必要方法
        required_methods = ["send_command", "write_uart", "read_uart"]
        for method in required_methods:
            if not hasattr(sim7600, method) or not callable(getattr(sim7600, method)):
                raise AttributeError(f"sim7600 object must implement {method} method")
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def set_apn(self, apn: str, user: str = "", password: str = "") -> None:
        """
        配置APN参数及认证信息
        Args:
            apn (str): 接入点名称(Access Point Name)，如"cmnet"、"3gnet"、"internet"等
            user (str, optional): APN认证用户名，默认为空字符串
            password (str, optional): APN认证密码，默认为空字符串

        Raises:
            TypeError: 当apn/user/password非字符串类型时触发
            ValueError: 当apn为空字符串时触发

        Notes:
            使用AT+CGDCONT配置PDP上下文，仅当用户名和密码都不为空时才配置认证信息
            不同运营商的APN参数不同，需根据实际使用的SIM卡运营商配置

        ==========================================
        Configure APN parameters and authentication information
        Args:
            apn (str): Access Point Name, such as "cmnet", "3gnet", "internet", etc.
            user (str, optional): APN authentication username, default empty string
            password (str, optional): APN authentication password, default empty string

        Raises:
            TypeError: Triggered when apn/user/password is not string type
            ValueError: Triggered when apn is empty string

        Notes:
            Use AT+CGDCONT to configure PDP context, configure authentication information only when both username and password are not empty
            Different operators have different APN parameters, which need to be configured according to the operator of the actual SIM card used
        """
        # 检查apn参数类型和有效性
        if not isinstance(apn, str):
            raise TypeError("apn parameter must be string type")
        if len(apn.strip()) == 0:
            raise ValueError("apn parameter cannot be empty string")
        # 检查user参数类型
        if not isinstance(user, str):
            raise TypeError("user parameter must be string type")
        # 检查password参数类型
        if not isinstance(password, str):
            raise TypeError("password parameter must be string type")
        # 配置PDP上下文，设置APN和IP协议类型（上下文ID为1）
        self.sim7600.send_command(f'AT+CGDCONT=1,"IP","{apn}"')
        # 判断是否需要配置APN认证信息（用户名和密码都非空时）
        if user and password:
            # 配置APN认证用户名和密码（认证类型1为PAP认证）
            self.sim7600.send_command(f'AT+CGAUTH=1,1,"{user}","{password}"')

    def open_connection(self, protocol: str, remote_ip: str, remote_port: int) -> bytes:
        """
        打开网络连接
        Args:
            protocol (str): 网络协议类型，仅支持"TCP"、"UDP"
            remote_ip (str): 远程服务器IP地址（IPv4格式）
            remote_port (int): 远程服务器端口号（1-65535）

        Raises:
            TypeError: 当protocol/remote_ip非字符串、remote_port非整数类型时触发
            ValueError: 当protocol非TCP/UDP、remote_ip为空、remote_port超出有效范围时触发

        Notes:
            先使用AT+NETOPEN打开网络服务，再使用AT+CIPOPEN建立指定类型的网络连接（通道0）
            建立连接前需确保APN已正确配置，否则连接会失败

        ==========================================
        Open network connection
        Args:
            protocol (str): Network protocol type, only supports "TCP", "UDP"
            remote_ip (str): Remote server IP address (IPv4 format)
            remote_port (int): Remote server port number (1-65535)

        Raises:
            TypeError: Triggered when protocol/remote_ip is not string, remote_port is not integer type
            ValueError: Triggered when protocol is not TCP/UDP, remote_ip is empty, remote_port is out of valid range

        Notes:
            First use AT+NETOPEN to open network service, then use AT+CIPOPEN to establish specified type of network connection (channel 0)
            Ensure APN is correctly configured before establishing connection, otherwise the connection will fail
        """
        # 检查protocol参数类型和有效性
        if not isinstance(protocol, str):
            raise TypeError("protocol parameter must be string type")
        protocol = protocol.upper()
        if protocol not in ["TCP", "UDP"]:
            raise ValueError("protocol parameter must be 'TCP' or 'UDP'")
        # 检查remote_ip参数类型和有效性
        if not isinstance(remote_ip, str):
            raise TypeError("remote_ip parameter must be string type")
        if len(remote_ip.strip()) == 0:
            raise ValueError("remote_ip parameter cannot be empty string")
        # 检查remote_port参数类型和有效性
        if not isinstance(remote_port, int):
            raise TypeError("remote_port parameter must be integer type")
        if remote_port < 1 or remote_port > 65535:
            raise ValueError("remote_port parameter must be between 1 and 65535")
        # 发送打开网络服务指令，初始化网络承载
        self.sim7600.send_command("AT+NETOPEN")
        # 发送建立网络连接指令（通道0）并返回响应
        return self.sim7600.send_command(f'AT+CIPOPEN=0,"{protocol}","{remote_ip}",{remote_port}')

    def close_connection(self) -> bytes:
        """
        关闭网络连接
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CIPCLOSE=0关闭通道0的网络连接，释放相关网络资源
            网络使用完成后建议及时关闭连接，以节省模块功耗

        ==========================================
        Close network connection
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CIPCLOSE=0 to close network connection of channel 0 and release related network resources
            It is recommended to close the connection in time after network use to save module power consumption
        """
        # 发送关闭网络连接指令（通道0）并返回响应
        return self.sim7600.send_command("AT+CIPCLOSE=0")

    def send_data(self, data: str) -> bytes:
        """
        发送网络数据
        Args:
            data (str): 要发送的字符串数据

        Raises:
            TypeError: 当data非字符串类型时触发
            ValueError: 当data为空字符串时触发

        Notes:
            先发送AT+CIPSEND指定通道0和数据长度，再通过UART发送实际数据，最后读取响应
            发送数据前需确保网络连接已成功建立，否则数据发送会失败

        ==========================================
        Send network data
        Args:
            data (str): String data to send

        Raises:
            TypeError: Triggered when data is not string type
            ValueError: Triggered when data is empty string

        Notes:
            First send AT+CIPSEND to specify channel 0 and data length, then send actual data via UART, finally read response
            Ensure network connection is successfully established before sending data, otherwise data sending will fail
        """
        # 检查data参数类型和有效性
        if not isinstance(data, str):
            raise TypeError("data parameter must be string type")
        if len(data.strip()) == 0:
            raise ValueError("data parameter cannot be empty string")
        # 发送指定数据长度的指令（通道0），告知模块即将发送的数据长度
        self.sim7600.send_command(f"AT+CIPSEND=0,{len(data)}")
        # 通过UART发送实际数据内容到模块
        self.sim7600.write_uart(data)
        # 读取并返回数据发送后的响应数据
        return self.sim7600.read_uart()

    def receive_data(self) -> bytes:
        """
        接收网络数据
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CIPRXGET=2,0读取通道0接收到的所有数据
            接收数据前需确保网络连接已建立且有数据到达，否则返回空数据

        ==========================================
        Receive network data
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CIPRXGET=2,0 to read all data received on channel 0
            Ensure network connection is established and data arrives before receiving data, otherwise return empty data
        """
        # 发送读取网络数据指令（通道0，读取所有可用数据）并返回响应
        return self.sim7600.send_command("AT+CIPRXGET=2,0")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
