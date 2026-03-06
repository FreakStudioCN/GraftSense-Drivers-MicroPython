# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午8:00
# @Author  : alankrantas
# @File    : gprs.py
# @Description : SIM800模块GPRS扩展类 实现GPRS附着/分离、APN配置、TCP通信、GSM定位等功能
# @License : MIT
# @Platform: MicroPython v1.23.0

# ======================================== 导入相关模块 =========================================

# 从核心模块导入SIM800基类
from .core import SIM800

# ======================================== 全局变量 ============================================

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class SIM800GPRS(SIM800):
    """
    SIM800模块GPRS扩展类
    SIM800 Module GPRS Extension Class

    继承自SIM800基类，扩展实现GPRS附着/分离、APN配置、TCP通信、GSM基站定位等GPRS相关功能
    Inherits from SIM800 base class, extends to implement GPRS attach/detach, APN configuration, TCP communication, GSM base station positioning and other GPRS-related functions

    Attributes:
        uart (machine.UART): 继承自SIM800基类的UART通信对象
                             UART communication object inherited from SIM800 base class
        baud (int): 继承自SIM800基类的UART波特率
                    UART baud rate inherited from SIM800 base class

    Methods:
        attach_gprs(): 附着GPRS网络
                       Attach to GPRS network
        detach_gprs(): 分离GPRS网络
                       Detach from GPRS network
        set_apn(apn, user='', pwd=''): 设置APN并激活GPRS上下文
                                       Set APN and activate GPRS context
        get_ip_address(): 获取GPRS分配的IP地址
                          Get IP address assigned by GPRS
        start_tcp_connection(mode, ip, port): 建立TCP连接
                                               Establish TCP connection
        send_data_tcp(data): 发送TCP数据
                             Send TCP data
        close_tcp_connection(): 关闭TCP连接
                                Close TCP connection
        shutdown_gprs(): 关闭GPRS PDP上下文
                         Shutdown GPRS PDP context
        get_gsm_location(): 获取GSM基站定位信息
                            Get GSM base station location information
    """

    def attach_gprs(self):
        """
        附着GPRS网络
        Attach to GPRS network

        Args:
            None

        Returns:
            bytes: 附着指令的响应数据
                   Response data of attach command

        Notes:
            使用AT+CGATT=1指令附着GPRS网络，附着成功后才能进行后续数据通信
            Use AT+CGATT=1 command to attach to GPRS network, subsequent data communication is only possible after successful attachment
        """
        # 发送GPRS附着指令并返回响应
        return self.send_command("AT+CGATT=1")

    def detach_gprs(self):
        """
        分离GPRS网络
        Detach from GPRS network

        Args:
            None

        Returns:
            bytes: 分离指令的响应数据
                   Response data of detach command

        Notes:
            使用AT+CGATT=0指令分离GPRS网络，分离后无法进行数据通信
            Use AT+CGATT=0 command to detach from GPRS network, data communication is not possible after detachment
        """
        # 发送GPRS分离指令并返回响应
        return self.send_command("AT+CGATT=0")

    def set_apn(self, apn, user="", pwd=""):
        """
        设置APN并激活GPRS上下文
        Set APN and activate GPRS context

        Args:
            apn (str): 接入点名称(Access Point Name)，如"cmnet"、"3gnet"等
                       Access Point Name, such as "cmnet", "3gnet", etc.
            user (str, optional): APN用户名，默认为空字符串
                                  APN username, default empty string
            pwd (str, optional): APN密码，默认为空字符串
                                 APN password, default empty string

        Returns:
            bytes: 激活GPRS上下文指令的响应数据
                   Response data of activate GPRS context command

        Notes:
            先使用AT+CSTT设置APN参数，再使用AT+CIICR激活GPRS PDP上下文
            First use AT+CSTT to set APN parameters, then use AT+CIICR to activate GPRS PDP context
        """
        # 发送设置APN参数指令
        self.send_command(f'AT+CSTT="{apn}","{user}","{pwd}"')
        # 发送激活GPRS上下文指令并返回响应
        return self.send_command("AT+CIICR")

    def get_ip_address(self):
        """
        获取GPRS分配的IP地址
        Get IP address assigned by GPRS

        Args:
            None

        Returns:
            bytes: 包含IP地址的响应数据
                   Response data containing IP address

        Notes:
            使用AT+CIFSR指令获取GPRS网络分配的本地IP地址，需先激活GPRS上下文
            Use AT+CIFSR command to get local IP address assigned by GPRS network, GPRS context must be activated first
        """
        # 发送获取IP地址指令并返回响应
        return self.send_command("AT+CIFSR")

    def start_tcp_connection(self, mode, ip, port):
        """
        建立TCP连接
        Establish TCP connection

        Args:
            mode (str): 连接模式，通常为"TCP"
                        Connection mode, usually "TCP"
            ip (str): 目标服务器IP地址
                      Target server IP address
            port (int): 目标服务器端口号
                        Target server port number

        Returns:
            bytes: 建立连接指令的响应数据
                   Response data of establish connection command

        Notes:
            使用AT+CIPSTART指令建立TCP连接，需先完成GPRS附着和APN配置
            Use AT+CIPSTART command to establish TCP connection, GPRS attachment and APN configuration must be completed first
        """
        # 发送建立TCP连接指令并返回响应
        return self.send_command(f'AT+CIPSTART="{mode}","{ip}","{port}"')

    def send_data_tcp(self, data):
        """
        发送TCP数据
        Send TCP data

        Args:
            data (str): 要发送的字符串数据
                        String data to send

        Returns:
            bytes: 数据发送后的响应数据
                   Response data after data sending

        Notes:
            先发送AT+CIPSEND指令指定数据长度，再发送实际数据，末尾添加ASCII码26(CTRL+Z)表示结束
            First send AT+CIPSEND command to specify data length, then send actual data, add ASCII code 26 (CTRL+Z) at end to indicate completion
        """
        # 发送数据长度指令
        self.send_command(f"AT+CIPSEND={len(data)}")
        # 发送实际数据并添加结束符(ASCII 26)
        self.uart.write(data + chr(26))
        # 读取并返回发送响应
        return self.read_response()

    def close_tcp_connection(self):
        """
        关闭TCP连接
        Close TCP connection

        Args:
            None

        Returns:
            bytes: 关闭连接指令的响应数据
                   Response data of close connection command

        Notes:
            使用AT+CIPCLOSE=1指令关闭TCP连接，释放网络资源
            Use AT+CIPCLOSE=1 command to close TCP connection and release network resources
        """
        # 发送关闭TCP连接指令并返回响应
        return self.send_command("AT+CIPCLOSE=1")

    def shutdown_gprs(self):
        """
        关闭GPRS PDP上下文
        Shutdown GPRS PDP context

        Args:
            None

        Returns:
            bytes: 关闭GPRS指令的响应数据
                   Response data of shutdown GPRS command

        Notes:
            使用AT+CIPSHUT指令关闭GPRS PDP上下文，释放所有GPRS相关资源
            Use AT+CIPSHUT command to close GPRS PDP context and release all GPRS-related resources
        """
        # 发送关闭GPRS指令并返回响应
        return self.send_command("AT+CIPSHUT")

    def get_gsm_location(self):
        """
        获取GSM基站定位信息
        Get GSM base station location information

        Args:
            None

        Returns:
            bytes: 包含GSM基站定位信息的响应数据
                   Response data containing GSM base station location information

        Notes:
            使用AT+CIPGSMLOC=1,1指令获取基于GSM基站的位置信息，包含LAC和CI等基站参数
            Use AT+CIPGSMLOC=1,1 command to get location information based on GSM base station, including LAC, CI and other base station parameters
        """
        # 发送获取GSM定位信息指令
        response = self.send_command("AT+CIPGSMLOC=1,1")
        # 返回定位响应数据
        return response


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
