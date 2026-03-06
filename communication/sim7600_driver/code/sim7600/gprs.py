# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午11:30
# @Author  : alankrantas
# @File    : gprs.py
# @Description : SIM7600模块GPRS功能类 实现APN配置、GPRS启停、IP查询、数据收发等GPRS通信功能
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class GPRS:
    """
    SIM7600模块GPRS功能类
    SIM7600 Module GPRS Function Class

    封装SIM7600模块的GPRS网络通信功能，包括APN配置、GPRS附着/激活、IP地址查询、数据收发等核心功能
    Encapsulates GPRS network communication functions of SIM7600 module, including core functions such as APN configuration, GPRS attach/activate, IP address query, data sending and receiving

    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法
                          SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): 初始化GPRS功能类
                           Initialize GPRS function class
        set_apn(apn, user='', password=''): 配置GPRS的APN参数及认证信息
                                            Configure APN parameters and authentication information for GPRS
        enable_gprs(): 启用GPRS功能（附着+激活）
                       Enable GPRS function (attach + activate)
        disable_gprs(): 禁用GPRS功能（去激活+分离）
                        Disable GPRS function (deactivate + detach)
        get_ip_address(): 获取GPRS分配的IP地址
                          Get IP address assigned by GPRS
        send_data(data): 发送GPRS数据
                         Send GPRS data
        receive_data(): 接收GPRS数据
                        Receive GPRS data
    """

    def __init__(self, sim7600):
        """
        初始化GPRS功能类
        Initialize GPRS function class

        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法
                              SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Returns:
            None

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成GPRS通信
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete GPRS communication
        """
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def set_apn(self, apn, user="", password=""):
        """
        配置GPRS的APN参数及认证信息
        Configure APN parameters and authentication information for GPRS

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
            使用AT+CGDCONT配置PDP上下文1的APN参数，仅当用户名和密码都不为空时才配置认证信息
            Use AT+CGDCONT to configure APN parameters for PDP context 1, configure authentication information only when both username and password are not empty
        """
        # 配置PDP上下文1，设置APN和IP协议类型
        self.sim7600.send_command(f'AT+CGDCONT=1,"IP","{apn}"')
        # 判断是否需要配置APN认证信息
        if user and password:
            # 配置PDP上下文1的认证信息（PAP/CHAP模式）
            self.sim7600.send_command(f'AT+CGAUTH=1,1,"{user}","{password}"')

    def enable_gprs(self):
        """
        启用GPRS功能（附着+激活）
        Enable GPRS function (attach + activate)

        Args:
            None

        Returns:
            None

        Notes:
            先执行GPRS附着网络，再激活PDP上下文1，完成GPRS功能启用
            First perform GPRS attach to network, then activate PDP context 1 to complete GPRS function enabling
        """
        # 执行GPRS网络附着
        self.sim7600.send_command("AT+CGATT=1")
        # 激活PDP上下文1
        self.sim7600.send_command("AT+CGACT=1,1")

    def disable_gprs(self):
        """
        禁用GPRS功能（去激活+分离）
        Disable GPRS function (deactivate + detach)

        Args:
            None

        Returns:
            None

        Notes:
            先去激活PDP上下文1，再执行GPRS网络分离，释放GPRS相关资源
            First deactivate PDP context 1, then perform GPRS network detach to release GPRS-related resources
        """
        # 去激活PDP上下文1
        self.sim7600.send_command("AT+CGACT=0,1")
        # 执行GPRS网络分离
        self.sim7600.send_command("AT+CGATT=0")

    def get_ip_address(self):
        """
        获取GPRS分配的IP地址
        Get IP address assigned by GPRS

        Args:
            None

        Returns:
            bytes: 包含IP地址信息的AT指令响应数据
                   AT command response data containing IP address information

        Notes:
            使用AT+CIFSR指令获取GPRS网络分配的本地IP地址，需先完成GPRS附着和激活
            Use AT+CIFSR command to get local IP address assigned by GPRS network, GPRS attach and activate must be completed first
        """
        # 发送获取IP地址指令并返回响应
        return self.sim7600.send_command("AT+CIFSR")

    def send_data(self, data):
        """
        发送GPRS数据
        Send GPRS data

        Args:
            data (str): 要发送的字符串数据
                        String data to send

        Returns:
            None

        Notes:
            直接通过UART写入数据，需确保已建立GPRS数据连接
            Directly write data via UART, ensure GPRS data connection has been established
        """
        # 向UART写入要发送的GPRS数据
        self.sim7600.write_uart(data)

    def receive_data(self):
        """
        接收GPRS数据
        Receive GPRS data

        Args:
            None

        Returns:
            bytes: 从UART读取到的GPRS数据
                   GPRS data read from UART

        Notes:
            从UART读取接收到的GPRS数据，读取超时时间由SIM7600核心对象配置
            Read received GPRS data from UART, read timeout is configured by SIM7600 core object
        """
        # 读取并返回接收到的GPRS数据
        return self.sim7600.read_uart()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
