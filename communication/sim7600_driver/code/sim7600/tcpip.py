# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午9:00
# @Author  : alankrantas
# @File    : tcpip.py
# @Description : SIM7600模块TCP/IP功能类 实现APN配置、网络连接管理、数据收发等TCP/IP通信功能
# @License : MIT
# @Platform: MicroPython v1.23.0

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
    SIM7600 Module TCP/IP Function Class

    封装SIM7600模块的TCP/IP网络通信功能，包括APN配置、网络连接管理、数据发送与接收等核心功能
    Encapsulates TCP/IP network communication functions of SIM7600 module, including APN configuration, network connection management, data sending and receiving, and other core functions

    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法
                          SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): 初始化TCP/IP功能类
                           Initialize TCP/IP function class
        set_apn(apn, user='', password=''): 配置APN参数及认证信息
                                            Configure APN parameters and authentication information
        open_connection(protocol, remote_ip, remote_port): 打开网络连接
                                                           Open network connection
        close_connection(): 关闭网络连接
                            Close network connection
        send_data(data): 发送网络数据
                         Send network data
        receive_data(): 接收网络数据
                        Receive network data
    """

    def __init__(self, sim7600):
        """
        初始化TCP/IP功能类
        Initialize TCP/IP function class

        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法
                              SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Returns:
            None

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成网络通信
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete network communication
        """
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def set_apn(self, apn, user='', password=''):
        """
        配置APN参数及认证信息
        Configure APN parameters and authentication information

        Args:
            apn (str): 接入点名称(Access Point Name)，如"cmnet"、"3gnet"、"internet"等
                       Access Point Name, such as "cmnet", "3gnet", "internet", etc.
            user (str, optional): APN认证用户名，默认为空字符串
                                  APN authentication username, default empty string
            password (str, optional): APN认证密码，默认为空字符串
                                      APN authentication password, default empty string

        Returns:
            None

        Notes:
            使用AT+CGDCONT配置PDP上下文，仅当用户名和密码都不为空时才配置认证信息
            Use AT+CGDCONT to configure PDP context, configure authentication information only when both username and password are not empty
        """
        # 配置PDP上下文，设置APN和IP协议类型
        self.sim7600.send_command(f'AT+CGDCONT=1,"IP","{apn}"')
        # 判断是否需要配置APN认证信息
        if user and password:
            # 配置APN认证用户名和密码
            self.sim7600.send_command(f'AT+CGAUTH=1,1,"{user}","{password}"')

    def open_connection(self, protocol, remote_ip, remote_port):
        """
        打开网络连接
        Open network connection

        Args:
            protocol (str): 网络协议类型，如"TCP"、"UDP"
                            Network protocol type, such as "TCP", "UDP"
            remote_ip (str): 远程服务器IP地址
                             Remote server IP address
            remote_port (int): 远程服务器端口号
                               Remote server port number

        Returns:
            bytes: 打开连接指令的响应数据
                   Response data of open connection command

        Notes:
            先使用AT+NETOPEN打开网络服务，再使用AT+CIPOPEN建立指定类型的网络连接（通道0）
            First use AT+NETOPEN to open network service, then use AT+CIPOPEN to establish specified type of network connection (channel 0)
        """
        # 发送打开网络服务指令
        self.sim7600.send_command('AT+NETOPEN')
        # 发送建立网络连接指令并返回响应
        return self.sim7600.send_command(f'AT+CIPOPEN=0,"{protocol}","{remote_ip}",{remote_port}')

    def close_connection(self):
        """
        关闭网络连接
        Close network connection

        Args:
            None

        Returns:
            bytes: 关闭连接指令的响应数据
                   Response data of close connection command

        Notes:
            使用AT+CIPCLOSE=0关闭通道0的网络连接，释放相关网络资源
            Use AT+CIPCLOSE=0 to close network connection of channel 0 and release related network resources
        """
        # 发送关闭网络连接指令并返回响应
        return self.sim7600.send_command('AT+CIPCLOSE=0')

    def send_data(self, data):
        """
        发送网络数据
        Send network data

        Args:
            data (str): 要发送的字符串数据
                        String data to send

        Returns:
            bytes: 数据发送后的响应数据
                   Response data after data sending

        Notes:
            先发送AT+CIPSEND指定通道0和数据长度，再通过UART发送实际数据，最后读取响应
            First send AT+CIPSEND to specify channel 0 and data length, then send actual data via UART, finally read response
        """
        # 发送指定数据长度的指令（通道0）
        self.sim7600.send_command(f'AT+CIPSEND=0,{len(data)}')
        # 通过UART发送实际数据内容
        self.sim7600.write_uart(data)
        # 读取并返回数据发送后的响应
        return self.sim7600.read_uart()

    def receive_data(self):
        """
        接收网络数据
        Receive network data

        Args:
            None

        Returns:
            bytes: 包含接收数据的响应数据
                   Response data containing received data

        Notes:
            使用AT+CIPRXGET=2,0读取通道0接收到的所有数据
            Use AT+CIPRXGET=2,0 to read all data received on channel 0
        """
        # 发送读取网络数据指令并返回响应
        return self.sim7600.send_command('AT+CIPRXGET=2,0')

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================