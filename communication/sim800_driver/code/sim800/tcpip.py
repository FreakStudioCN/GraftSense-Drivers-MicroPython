# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午7:00
# @Author  : basanovase
# @File    : tcpip.py
# @Description : SIM800模块TCP/IP扩展类 实现TCP/UDP通信、HTTP请求、FTP文件传输等网络功能
# @License : MIT
# @Platform: MicroPython v1.23.0

# ======================================== 导入相关模块 =========================================

# 从核心模块导入SIM800基类
from .core import SIM800

# ======================================== 全局变量 ============================================

__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class SIM800TCPIP(SIM800):
    """
    SIM800模块TCP/IP扩展类
    SIM800 Module TCP/IP Extension Class

    继承自SIM800基类，扩展实现TCP/UDP通信、HTTP请求、FTP文件传输等网络功能
    Inherits from SIM800 base class, extends to implement TCP/UDP communication, HTTP requests, FTP file transfer and other network functions

    Attributes:
        uart (machine.UART): 继承自SIM800基类的UART通信对象
                             UART communication object inherited from SIM800 base class
        baud (int): 继承自SIM800基类的UART波特率
                    UART baud rate inherited from SIM800 base class

    Methods:
        start_tcp_connection(mode, ip, port): 建立TCP连接
                                               Establish TCP connection
        send_data_tcp(data): 发送TCP数据
                             Send TCP data
        receive_data_tcp(): 接收TCP数据
                            Receive TCP data
        close_tcp_connection(): 关闭TCP连接
                                Close TCP connection
        start_udp_connection(ip, port): 建立UDP连接
                                        Establish UDP connection
        send_data_udp(data): 发送UDP数据
                             Send UDP data
        receive_data_udp(max_length=1460): 接收UDP数据
                                           Receive UDP data
        close_udp_connection(): 关闭UDP连接
                                Close UDP connection
        shutdown_gprs(): 关闭GPRS连接
                         Shutdown GPRS connection
        get_ip_address(): 获取本机IP地址
                          Get local IP address
        http_init(): 初始化HTTP服务
                     Initialize HTTP service
        http_set_param(param, value): 设置HTTP参数
                                      Set HTTP parameters
        http_get(url): 发送HTTP GET请求
                       Send HTTP GET request
        http_post(url, data): 发送HTTP POST请求
                              Send HTTP POST request
        http_terminate(): 终止HTTP服务
                          Terminate HTTP service
        ftp_init(server, username, password, port=21): 初始化FTP连接
                                                       Initialize FTP connection
        ftp_get_file(filename, remote_path): 从FTP服务器下载文件
                                             Download file from FTP server
        ftp_put_file(filename, remote_path, data): 上传文件到FTP服务器
                                                   Upload file to FTP server
        ftp_close(): 关闭FTP连接
                     Close FTP connection
    """

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
            bytes: AT指令响应数据
                   AT command response data

        Notes:
            使用AT+CIPSTART指令建立TCP连接
            Use AT+CIPSTART command to establish TCP connection
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
        self.send_command(f'AT+CIPSEND={len(data)}')
        # 发送实际数据并添加结束符(ASCII 26)
        self.uart.write(data + chr(26))
        # 读取并返回响应
        return self.read_response()

    def receive_data_tcp(self):
        """
        接收TCP数据
        Receive TCP data

        Args:
            None

        Returns:
            bytes: 接收到的TCP数据响应
                   Received TCP data response

        Notes:
            使用AT+CIPRXGET=2指令读取接收到的TCP数据
            Use AT+CIPRXGET=2 command to read received TCP data
        """
        # 发送读取TCP数据指令并返回响应
        return self.send_command('AT+CIPRXGET=2')

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
            使用AT+CIPCLOSE=1指令关闭TCP连接
            Use AT+CIPCLOSE=1 command to close TCP connection
        """
        # 发送关闭TCP连接指令并返回响应
        return self.send_command('AT+CIPCLOSE=1')

    def start_udp_connection(self, ip, port):
        """
        建立UDP连接
        Establish UDP connection

        Args:
            ip (str): 目标服务器IP地址
                      Target server IP address
            port (int): 目标服务器端口号
                        Target server port number

        Returns:
            bytes: AT指令响应数据
                   AT command response data

        Notes:
            使用AT+CIPSTART指令建立UDP连接
            Use AT+CIPSTART command to establish UDP connection
        """
        # 发送建立UDP连接指令并返回响应
        return self.send_command(f'AT+CIPSTART="UDP","{ip}","{port}"')

    def send_data_udp(self, data):
        """
        发送UDP数据
        Send UDP data

        Args:
            data (str/bytes): 要发送的字符串或字节数据
                              String or bytes data to send

        Returns:
            bytes: 数据发送后的响应数据
                   Response data after data sending

        Notes:
            字符串数据会自动编码为UTF-8字节串，末尾添加字节26表示结束
            String data is automatically encoded to UTF-8 bytes, add byte 26 at end to indicate completion
        """
        # 判断数据类型，字符串转换为字节串
        if isinstance(data, str):
            data = data.encode('utf-8')
        # 发送数据长度指令
        self.send_command(f'AT+CIPSEND={len(data)}')
        # 发送实际数据并添加结束符(字节26)
        self.uart.write(data + bytes([26]))
        # 读取并返回响应
        return self.read_response()

    def receive_data_udp(self, max_length=1460):
        """
        接收UDP数据
        Receive UDP data

        Args:
            max_length (int, optional): 最大接收数据长度，默认1460字节
                                        Maximum receive data length, default 1460 bytes

        Returns:
            bytes: 接收到的UDP数据响应
                   Received UDP data response

        Notes:
            使用AT+CIPRXGET=2指令读取指定长度的UDP数据
            Use AT+CIPRXGET=2 command to read UDP data of specified length
        """
        # 发送读取UDP数据指令并返回响应
        return self.send_command(f'AT+CIPRXGET=2,{max_length}')

    def close_udp_connection(self):
        """
        关闭UDP连接
        Close UDP connection

        Args:
            None

        Returns:
            bytes: 关闭连接指令的响应数据
                   Response data of close connection command

        Notes:
            使用AT+CIPCLOSE=1指令关闭UDP连接
            Use AT+CIPCLOSE=1 command to close UDP connection
        """
        # 发送关闭UDP连接指令并返回响应
        return self.send_command('AT+CIPCLOSE=1')

    def shutdown_gprs(self):
        """
        关闭GPRS连接
        Shutdown GPRS connection

        Args:
            None

        Returns:
            bytes: 关闭GPRS指令的响应数据
                   Response data of shutdown GPRS command

        Notes:
            使用AT+CIPSHUT指令关闭GPRS PDP上下文
            Use AT+CIPSHUT command to close GPRS PDP context
        """
        # 发送关闭GPRS指令并返回响应
        return self.send_command('AT+CIPSHUT')

    def get_ip_address(self):
        """
        获取本机IP地址
        Get local IP address

        Args:
            None

        Returns:
            bytes: 包含IP地址的响应数据
                   Response data containing IP address

        Notes:
            使用AT+CIFSR指令获取已分配的本地IP地址
            Use AT+CIFSR command to get assigned local IP address
        """
        # 发送获取IP地址指令并返回响应
        return self.send_command('AT+CIFSR')

    def http_init(self):
        """
        初始化HTTP服务
        Initialize HTTP service

        Args:
            None

        Returns:
            bytes: 初始化指令的响应数据
                   Response data of initialization command

        Notes:
            使用AT+HTTPINIT指令初始化HTTP服务上下文
            Use AT+HTTPINIT command to initialize HTTP service context
        """
        # 发送HTTP初始化指令并返回响应
        return self.send_command('AT+HTTPINIT')

    def http_set_param(self, param, value):
        """
        设置HTTP参数
        Set HTTP parameters

        Args:
            param (str): 参数名称，如"URL"、"CID"等
                         Parameter name, such as "URL", "CID", etc.
            value (str): 参数值
                         Parameter value

        Returns:
            bytes: 设置参数指令的响应数据
                   Response data of set parameter command

        Notes:
            使用AT+HTTPPARA指令设置HTTP请求参数
            Use AT+HTTPPARA command to set HTTP request parameters
        """
        # 发送设置HTTP参数指令并返回响应
        return self.send_command(f'AT+HTTPPARA="{param}","{value}"')

    def http_get(self, url):
        """
        发送HTTP GET请求
        Send HTTP GET request

        Args:
            url (str): 请求的URL地址
                       Requested URL address

        Returns:
            bytes: GET请求的响应数据
                   Response data of GET request

        Notes:
            先设置URL参数，再发送AT+HTTPACTION=0指令执行GET请求
            First set URL parameter, then send AT+HTTPACTION=0 command to execute GET request
        """
        # 设置HTTP请求URL参数
        self.http_set_param("URL", url)
        # 发送HTTP GET请求指令
        self.send_command('AT+HTTPACTION=0')
        # 读取并返回响应
        return self.read_response()

    def http_post(self, url, data):
        """
        发送HTTP POST请求
        Send HTTP POST request

        Args:
            url (str): 请求的URL地址
                       Requested URL address
            data (str): POST请求的表单数据或JSON数据
                        Form data or JSON data for POST request

        Returns:
            bytes: POST请求的响应数据
                   Response data of POST request

        Notes:
            使用AT+HTTPDATA指令设置POST数据，超时时间10秒，再发送AT+HTTPACTION=1执行POST请求
            Use AT+HTTPDATA command to set POST data with 10-second timeout, then send AT+HTTPACTION=1 to execute POST request
        """
        # 设置HTTP请求URL参数
        self.http_set_param("URL", url)
        # 设置POST数据长度和超时时间(10000ms)
        self.send_command(f'AT+HTTPDATA={len(data)},10000')
        # 发送POST数据
        self.uart.write(data)
        # 发送HTTP POST请求指令
        self.send_command('AT+HTTPACTION=1')
        # 读取并返回响应
        return self.read_response()

    def http_terminate(self):
        """
        终止HTTP服务
        Terminate HTTP service

        Args:
            None

        Returns:
            bytes: 终止HTTP服务指令的响应数据
                   Response data of terminate HTTP service command

        Notes:
            使用AT+HTTPTERM指令关闭HTTP服务上下文
            Use AT+HTTPTERM command to close HTTP service context
        """
        # 发送终止HTTP服务指令并返回响应
        return self.send_command('AT+HTTPTERM')

    def ftp_init(self, server, username, password, port=21):
        """
        初始化FTP连接
        Initialize FTP connection

        Args:
            server (str): FTP服务器IP地址或域名
                          FTP server IP address or domain name
            username (str): FTP登录用户名
                            FTP login username
            password (str): FTP登录密码
                            FTP login password
            port (int, optional): FTP服务器端口号，默认21
                                  FTP server port number, default 21

        Returns:
            bytes: 设置FTP密码后的响应数据
                   Response data after setting FTP password

        Notes:
            依次配置GPRS上下文、激活SAPBR、设置FTP服务器信息和登录凭证
            Configure GPRS context, activate SAPBR, set FTP server info and login credentials in sequence
        """
        # 设置SAPBR连接类型为GPRS
        self.send_command('AT+SAPBR=3,1,"Contype","GPRS"')
        # 激活SAPBR承载
        self.send_command('AT+SAPBR=1,1')
        # 设置FTP使用的CID
        self.send_command(f'AT+FTPCID=1')
        # 设置FTP服务器地址
        self.send_command(f'AT+FTPSERV="{server}"')
        # 设置FTP服务器端口
        self.send_command(f'AT+FTPPORT={port}')
        # 设置FTP登录用户名
        self.send_command(f'AT+FTPUN="{username}"')
        # 设置FTP登录密码并返回响应
        return self.send_command(f'AT+FTPPW="{password}"')

    def ftp_get_file(self, filename, remote_path):
        """
        从FTP服务器下载文件
        Download file from FTP server

        Args:
            filename (str): 要下载的文件名
                            File name to download
            remote_path (str): 远程文件路径
                               Remote file path

        Returns:
            bytes: 文件下载指令的响应数据
                   Response data of file download command

        Notes:
            超时时间设置为10秒，最大读取长度1024字节
            Timeout set to 10 seconds, maximum read length 1024 bytes
        """
        # 设置FTP下载文件路径
        self.send_command(f'AT+FTPGETPATH="{remote_path}"')
        # 设置FTP下载文件名
        self.send_command(f'AT+FTPGETNAME="{filename}"')
        # 启动FTP下载
        self.send_command('AT+FTPGET=1')
        # 读取下载文件数据(超时10000ms)并返回响应
        return self.send_command('AT+FTPGET=2,1024', timeout=10000)

    def ftp_put_file(self, filename, remote_path, data):
        """
        上传文件到FTP服务器
        Upload file to FTP server

        Args:
            filename (str): 要上传的文件名
                            File name to upload
            remote_path (str): 远程文件路径
                               Remote file path
            data (str/bytes): 要上传的文件数据
                              File data to upload

        Returns:
            bytes: 文件上传后的响应数据
                   Response data after file upload

        Notes:
            字符串数据会自动编码为UTF-8字节串，支持字节串和字符串两种数据格式
            String data is automatically encoded to UTF-8 bytes, supports both bytes and string data formats
        """
        # 设置FTP上传文件路径
        self.send_command(f'AT+FTPPUTPATH="{remote_path}"')
        # 设置FTP上传文件名
        self.send_command(f'AT+FTPPUTNAME="{filename}"')
        # 启动FTP上传
        self.send_command('AT+FTPPUT=1')
        # 设置上传数据长度
        self.send_command(f'AT+FTPPUT=2,{len(data)}')
        # 发送上传数据(自动转换为字节串)
        self.uart.write(data if isinstance(data, bytes) else data.encode('utf-8'))
        # 读取并返回响应
        return self.read_response()

    def ftp_close(self):
        """
        关闭FTP连接
        Close FTP connection

        Args:
            None

        Returns:
            bytes: 关闭FTP连接指令的响应数据
                   Response data of close FTP connection command

        Notes:
            使用AT+SAPBR=0,1指令关闭SAPBR承载来终止FTP连接
            Use AT+SAPBR=0,1 command to close SAPBR bearer to terminate FTP connection
        """
        # 发送关闭FTP连接指令并返回响应
        return self.send_command('AT+SAPBR=0,1')

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================