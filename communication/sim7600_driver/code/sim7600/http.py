# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午11:00
# @Author  : alankrantas
# @File    : http.py
# @Description : SIM7600模块HTTP功能类 实现APN配置、HTTP服务管理、GET/POST请求等HTTP通信功能
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

class HTTP:
    """
    SIM7600模块HTTP功能类
    SIM7600 Module HTTP Function Class

    封装SIM7600模块的HTTP网络通信功能，包括APN配置、HTTP服务启停、URL设置、GET/POST请求发送等核心功能
    Encapsulates HTTP network communication functions of SIM7600 module, including core functions such as APN configuration, HTTP service start/stop, URL setting, GET/POST request sending

    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法
                          SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): 初始化HTTP功能类
                           Initialize HTTP function class
        set_apn(apn, user='', password=''): 配置HTTP使用的APN参数及认证信息
                                            Configure APN parameters and authentication information for HTTP
        enable_http(): 启用HTTP服务并初始化上下文
                       Enable HTTP service and initialize context
        disable_http(): 禁用HTTP服务并关闭网络承载
                        Disable HTTP service and close network bearer
        set_url(url): 设置HTTP请求的URL地址
                      Set URL address for HTTP request
        set_content(content_type): 设置HTTP请求的内容类型
                                   Set content type for HTTP request
        get(): 发送HTTP GET请求并获取响应
               Send HTTP GET request and get response
        post(data): 发送HTTP POST请求并获取响应
                    Send HTTP POST request and get response
        read_response(): 读取HTTP响应数据
                         Read HTTP response data
    """

    def __init__(self, sim7600):
        """
        初始化HTTP功能类
        Initialize HTTP function class

        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法
                              SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Returns:
            None

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成HTTP通信
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete HTTP communication
        """
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def set_apn(self, apn, user='', password=''):
        """
        配置HTTP使用的APN参数及认证信息
        Configure APN parameters and authentication information for HTTP

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
            使用AT+SAPBR指令配置承载1的APN参数，仅当用户名和密码都不为空时才配置认证信息
            Use AT+SAPBR command to configure APN parameters for bearer 1, configure authentication information only when both username and password are not empty
        """
        # 配置承载1的APN参数
        self.sim7600.send_command(f'AT+SAPBR=3,1,"APN","{apn}"')
        # 判断是否需要配置APN认证信息
        if user and password:
            # 配置APN认证用户名
            self.sim7600.send_command(f'AT+SAPBR=3,1,"USER","{user}"')
            # 配置APN认证密码
            self.sim7600.send_command(f'AT+SAPBR=3,1,"PWD","{password}"')

    def enable_http(self):
        """
        启用HTTP服务并初始化上下文
        Enable HTTP service and initialize context

        Args:
            None

        Returns:
            None

        Notes:
            依次激活网络承载、查询IP地址、初始化HTTP服务上下文
            Activate network bearer, query IP address, initialize HTTP service context in sequence
        """
        # 激活承载1的网络连接
        self.sim7600.send_command('AT+SAPBR=1,1')
        # 查询承载1的IP地址信息
        self.sim7600.send_command('AT+SAPBR=2,1')
        # 初始化HTTP服务上下文
        self.sim7600.send_command('AT+HTTPINIT')

    def disable_http(self):
        """
        禁用HTTP服务并关闭网络承载
        Disable HTTP service and close network bearer

        Args:
            None

        Returns:
            None

        Notes:
            先终止HTTP服务上下文，再关闭网络承载，释放相关网络资源
            First terminate HTTP service context, then close network bearer to release related network resources
        """
        # 终止HTTP服务上下文
        self.sim7600.send_command('AT+HTTPTERM')
        # 关闭承载1的网络连接
        self.sim7600.send_command('AT+SAPBR=0,1')

    def set_url(self, url):
        """
        设置HTTP请求的URL地址
        Set URL address for HTTP request

        Args:
            url (str): HTTP请求的目标URL地址
                       Target URL address for HTTP request

        Returns:
            None

        Notes:
            使用AT+HTTPPARA指令设置HTTP请求的URL参数
            Use AT+HTTPPARA command to set URL parameter for HTTP request
        """
        # 配置HTTP请求的URL参数
        self.sim7600.send_command(f'AT+HTTPPARA="URL","{url}"')

    def set_content(self, content_type):
        """
        设置HTTP请求的内容类型
        Set content type for HTTP request

        Args:
            content_type (str): HTTP内容类型，如"application/json"、"application/x-www-form-urlencoded"等
                                HTTP content type, such as "application/json", "application/x-www-form-urlencoded", etc.

        Returns:
            None

        Notes:
            使用AT+HTTPPARA指令设置HTTP请求的CONTENT参数，影响POST请求的数据格式
            Use AT+HTTPPARA command to set CONTENT parameter for HTTP request, which affects data format of POST request
        """
        # 配置HTTP请求的内容类型参数
        self.sim7600.send_command(f'AT+HTTPPARA="CONTENT","{content_type}"')

    def get(self):
        """
        发送HTTP GET请求并获取响应
        Send HTTP GET request and get response

        Args:
            None

        Returns:
            bytes: HTTP GET请求的响应数据
                   Response data of HTTP GET request

        Notes:
            使用AT+HTTPACTION=0指令执行GET请求，通过UART读取响应数据
            Use AT+HTTPACTION=0 command to execute GET request, read response data via UART
        """
        # 发送HTTP GET请求指令
        self.sim7600.send_command('AT+HTTPACTION=0')
        # 读取并返回GET请求的响应数据
        return self.sim7600.read_uart()

    def post(self, data):
        """
        发送HTTP POST请求并获取响应
        Send HTTP POST request and get response

        Args:
            data (str): POST请求的表单数据或JSON数据
                        Form data or JSON data for POST request

        Returns:
            bytes: HTTP POST请求的响应数据
                   Response data of HTTP POST request

        Notes:
            先使用AT+HTTPDATA指令设置POST数据（超时10秒），再执行POST请求并读取响应
            First use AT+HTTPDATA command to set POST data (10-second timeout), then execute POST request and read response
        """
        # 配置POST数据长度和超时时间(10000ms)
        self.sim7600.send_command(f'AT+HTTPDATA={len(data)},10000')
        # 发送POST请求的具体数据
        self.sim7600.write_uart(data)
        # 发送HTTP POST请求指令
        self.sim7600.send_command('AT+HTTPACTION=1')
        # 读取并返回POST请求的响应数据
        return self.sim7600.read_uart()

    def read_response(self):
        """
        读取HTTP响应数据
        Read HTTP response data

        Args:
            None

        Returns:
            bytes: 包含完整HTTP响应数据的AT指令响应
                   AT command response containing complete HTTP response data

        Notes:
            使用AT+HTTPREAD指令读取HTTP响应的全部数据内容
            Use AT+HTTPREAD command to read all data content of HTTP response
        """
        # 发送读取HTTP响应数据指令并返回响应
        return self.sim7600.send_command('AT+HTTPREAD')

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================