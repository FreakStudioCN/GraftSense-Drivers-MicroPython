# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午11:00
# @Author  : basanovase
# @File    : http.py
# @Description : SIM7600模块HTTP功能类 实现APN配置、HTTP服务管理、GET/POST请求等HTTP通信功能 参考自：https://github.com/basanovase/sim7600
# @License : MIT
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
    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法

    Methods:
        __init__(sim7600): 初始化HTTP功能类
        set_apn(cid=1, pdp_type="IP", apn="CMNET"): 配置HTTP使用的APN参数及认证信息
        enable_http(): 启用HTTP服务并初始化上下文
        disable_http(): 禁用HTTP服务并关闭网络承载
        set_url(url): 设置HTTP请求的URL地址
        send_head(content_type): 设置HTTP请求的内容类型并发送
        get_head(): 读取响应头
        get_ip(): 获取模块分配的IP地址
        get_read(offset=0, length=512): 读取HTTP响应数据
        http_data(data_len, timeout=1000): 配置HTTP数据发送参数
        http_post_file(file_path,mode=1,offset=0): 从模块本地文件发送POST请求

    Notes:
        所有HTTP通信功能依赖SIM7600核心对象的AT指令发送能力，需确保核心对象方法正常可用

    ==========================================
    SIM7600 Module HTTP Function Class
    Attributes:
        sim7600 (object): SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): Initialize HTTP function class
        set_apn(cid=1, pdp_type="IP", apn="CMNET"): Configure APN parameters and authentication information for HTTP
        enable_http(): Enable HTTP service and initialize context
        disable_http(): Disable HTTP service and close network bearer
        set_url(url): Set URL address for HTTP request
        send_head(content_type): Set content type for HTTP request and send
        get_head(): Read response header
        get_ip(): Get IP address assigned to the module
        get_read(offset=0, length=512): Read HTTP response data
        http_data(data_len, timeout=1000): Configure HTTP data sending parameters
        http_post_file(file_path,mode=1,offset=0): Send POST request from module local file

    Notes:
        All HTTP communication functions depend on the AT command sending capability of the SIM7600 core object, ensure the core object methods are available
    """

    def __init__(self, sim7600: object) -> None:
        """
        初始化HTTP功能类
        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法

        Raises:
            TypeError: 当sim7600参数为None时触发
            AttributeError: 当sim7600对象缺少必要方法（send_command/write_uart/read_uart）时触发

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成HTTP通信

        ==========================================
        Initialize HTTP function class
        Args:
            sim7600 (object): SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Raises:
            TypeError: Triggered when sim7600 parameter is None
            AttributeError: Triggered when sim7600 object lacks necessary methods (send_command/write_uart/read_uart)

        Notes:
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete HTTP communication
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

    def set_apn(self, cid: int = 1, pdp_type: str = "IP", apn: str = "CMNET") -> str:
        """
        设置套接字上下文参数（配置PDP上下文）
        Args:
            cid (int): 上下文标识，默认值1（通常1为默认PDP上下文ID）
            pdp_type (str): PDP类型，默认值"IP"（IPv4协议）
            apn (str): 接入点名称，默认值"CMNET"（中国移动公网APN）

        Raises:
            TypeError: 当cid非整数、pdp_type/apn非字符串类型时触发
            ValueError: 当cid小于0或apn为空字符串时触发

        Notes:
            使用AT+CGSOCKCONT指令配置套接字上下文参数
            指令格式：AT+CGSOCKCONT=<cid>,"<pdp_type>","<apn>"
            该指令用于配置SIM7600模块的网络接入上下文，为后续网络通信（如TCP/UDP/HTTP）提供基础

        ==========================================
        Set socket context parameters (configure PDP context)
        Args:
            cid (int): Context identifier, default value 1 (usually 1 is the default PDP context ID)
            pdp_type (str): PDP type, default value "IP" (IPv4 protocol)
            apn (str): Access Point Name, default value "CMNET" (China Mobile public network APN)

        Raises:
            TypeError: Triggered when cid is not integer, pdp_type/apn is not string type
            ValueError: Triggered when cid is less than 0 or apn is empty string

        Notes:
            Use AT+CGSOCKCONT command to configure socket context parameters
            Command format: AT+CGSOCKCONT=<cid>,"<pdp_type>","<apn>"
            This command configures the network access context of the SIM7600 module,
            providing the foundation for subsequent network communications (e.g., TCP/UDP/HTTP)
        """
        # 检查cid参数类型和有效性
        if not isinstance(cid, int):
            raise TypeError("cid parameter must be integer type")
        if cid < 0:
            raise ValueError("cid parameter must be greater than or equal to 0")
        # 检查pdp_type参数类型
        if not isinstance(pdp_type, str):
            raise TypeError("pdp_type parameter must be string type")
        # 检查apn参数类型和有效性
        if not isinstance(apn, str):
            raise TypeError("apn parameter must be string type")
        if len(apn.strip()) == 0:
            raise ValueError("apn parameter cannot be empty string")
        # 发送配置PDP上下文指令并返回响应
        return self.sim7600.send_command(f'AT+CGSOCKCONT={cid},"{pdp_type}","{apn}"')

    def enable_http(self) -> str:
        """
        启用HTTP服务并初始化上下文
        Args:
            无

        Raises:
            无

        Notes:
            依次激活网络承载、查询IP地址、初始化HTTP服务上下文

        ==========================================
        Enable HTTP service and initialize context
        Args:
            None

        Raises:
            None

        Notes:
            Activate network bearer, query IP address, initialize HTTP service context in sequence
        """
        # 初始化HTTP服务上下文
        return self.sim7600.send_command("AT+HTTPINIT")

    def disable_http(self) -> str:
        """
        禁用HTTP服务并关闭网络承载
        Args:
            无

        Raises:
            无

        Notes:
            先终止HTTP服务上下文，再关闭网络承载，释放相关网络资源

        ==========================================
        Disable HTTP service and close network bearer
        Args:
            None

        Raises:
            None

        Notes:
            First terminate HTTP service context, then close network bearer to release related network resources
        """
        # 终止HTTP服务上下文
        return self.sim7600.send_command("AT+HTTPTERM")

    def set_url(self, url: str) -> str:
        """
        设置HTTP请求的URL地址
        Args:
            url (str): HTTP请求的目标URL地址

        Raises:
            TypeError: 当url参数非字符串类型时触发
            ValueError: 当url参数为空字符串时触发

        Notes:
            使用AT+HTTPPARA指令设置HTTP请求的URL参数

        ==========================================
        Set URL address for HTTP request
        Args:
            url (str): Target URL address for HTTP request

        Raises:
            TypeError: Triggered when url parameter is not string type
            ValueError: Triggered when url parameter is empty string

        Notes:
            Use AT+HTTPPARA command to set URL parameter for HTTP request
        """
        # 检查url参数类型和有效性
        if not isinstance(url, str):
            raise TypeError("url parameter must be string type")
        if len(url.strip()) == 0:
            raise ValueError("url parameter cannot be empty string")
        # 配置HTTP请求的URL参数
        return self.sim7600.send_command(f'AT+HTTPPARA="URL","{url}"')

    def send_head(self, content_type: str) -> str:
        """
        设置HTTP请求的内容类型并发送
        Args:
            content_type (str): HTTP请求的内容类型标识

        Raises:
            TypeError: 当content_type参数非字符串类型时触发
            ValueError: 当content_type参数为空字符串时触发

        Notes:
            使用AT+HTTPACTION指令设置并发送HTTP请求的内容类型参数

        ==========================================
        Set content type for HTTP request and send
        Args:
            content_type (str): Content type identifier for HTTP request

        Raises:
            TypeError: Triggered when content_type parameter is not string type
            ValueError: Triggered when content_type parameter is empty string

        Notes:
            Use AT+HTTPACTION command to set and send content type parameter of HTTP request
        """
        # 检查content_type参数类型和有效性
        if not isinstance(content_type, str):
            raise TypeError("content_type parameter must be string type")
        if len(content_type.strip()) == 0:
            raise ValueError("content_type parameter cannot be empty string")
        # 配置HTTP请求的内容类型参数
        return self.sim7600.send_command(f"AT+HTTPACTION={content_type}")

    def get_head(self) -> str:
        """
        读取响应头
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+HTTPHEAD指令读取HTTP响应头信息
            执行前需确保HTTP请求已发送并完成响应

        ==========================================
        Read response header
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+HTTPHEAD command to read HTTP response header information
            Ensure HTTP request has been sent and responded before execution
        """
        # 读取并返回响应头数据
        return self.sim7600.send_command("AT+HTTPHEAD")

    def get_ip(self) -> str:
        """
        获取模块分配的IP地址
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGCONTRDP指令查询PDP上下文的IP地址信息
            需在成功建立网络连接后调用该方法

        ==========================================
        Get IP address assigned to the module
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGCONTRDP command to query IP address information of PDP context
            This method must be called after successfully establishing network connection
        """
        # 发送查询IP地址指令并返回响应
        return self.sim7600.send_command(f"AT+CGCONTRDP")

    def get_read(self, offset: int = 0, length: int = 512) -> str:
        """
        读取HTTP响应数据
        Args:
            offset (int): 读取起始偏移量（字节），默认0（从响应开头读取）
            length (int): 单次读取的最大字节数，默认512（读取最多512字节）

        Raises:
            TypeError: 当offset或length非整数类型时触发
            ValueError: 当offset小于0或length小于0时触发

        Notes:
            使用AT+HTTPREAD指令读取HTTP响应数据
            1. offset=0, length=0 → 读取全部响应数据（AT+HTTPREAD=0,0）
            2. offset=0, length=512 → 从开头读取最多512字节（AT+HTTPREAD=0,512）
            3. 执行前需确保AT+HTTPACTION请求已完成（返回+HTTPACTION: 0,200,xxx）

        ==========================================
        Read HTTP response data
        Args:
            offset (int): Read start offset (bytes), default 0 (read from the beginning of the response)
            length (int): Maximum number of bytes to read at one time, default 512 (read up to 512 bytes)

        Raises:
            TypeError: Triggered when offset or length is not integer type
            ValueError: Triggered when offset is less than 0 or length is less than 0

        Notes:
            Use AT+HTTPREAD command to read HTTP response data
            1. offset=0, length=0 → Read all response data (AT+HTTPREAD=0,0)
            2. offset=0, length=512 → Read up to 512 bytes from the beginning (AT+HTTPREAD=0,512)
            3. Before execution, ensure AT+HTTPACTION request is completed (returns +HTTPACTION: 0,200,xxx)
        """
        # 检查offset参数类型和有效性
        if not isinstance(offset, int):
            raise TypeError("offset parameter must be integer type")
        if offset < 0:
            raise ValueError("offset parameter must be greater than or equal to 0")
        # 检查length参数类型和有效性
        if not isinstance(length, int):
            raise TypeError("length parameter must be integer type")
        if length < 0:
            raise ValueError("length parameter must be greater than or equal to 0")
        # 发送指令并返回响应数据
        return self.sim7600.send_command(f"AT+HTTPREAD={offset},{length}")

    def http_data(self, data_len: int, timeout: int = 1000) -> str:
        """
        实现AT+HTTPDATA指令（示例中AT+HTTPDATA=18,1000）
        Args:
            data_len (int): 要发送的POST数据长度（示例中18）
            timeout (int, optional): 数据输入超时时间（示例中1000ms）

        Raises:
            TypeError: 当data_len或timeout非整数类型时触发
            ValueError: 当data_len小于等于0或timeout小于0时触发

        Notes:
            AT+HTTPDATA指令用于设置POST数据的长度和输入超时时间
            执行后模块会返回DOWNLOAD提示符，此时需通过UART发送指定长度的POST数据

        ==========================================
        Implement AT+HTTPDATA command (AT+HTTPDATA=18,1000 in example)
        Args:
            data_len (int): Length of POST data to send (18 in example)
            timeout (int, optional): Data input timeout (1000ms in example)

        Raises:
            TypeError: Triggered when data_len or timeout is not integer type
            ValueError: Triggered when data_len is less than or equal to 0 or timeout is less than 0

        Notes:
            AT+HTTPDATA command is used to set the length of POST data and input timeout
            After execution, the module returns DOWNLOAD prompt, and then the specified length of POST data must be sent via UART
        """
        # 检查data_len参数类型和有效性
        if not isinstance(data_len, int):
            raise TypeError("data_len parameter must be integer type")
        if data_len <= 0:
            raise ValueError("data_len parameter must be greater than 0")
        # 检查timeout参数类型和有效性
        if not isinstance(timeout, int):
            raise TypeError("timeout parameter must be integer type")
        if timeout < 0:
            raise ValueError("timeout parameter must be greater than or equal to 0")
        # 发送AT+HTTPDATA指令并返回响应
        return self.sim7600.send_command(f"AT+HTTPDATA={data_len},{timeout}")

    def http_post_file(self, file_path: str, mode: int = 1, offset: int = 0) -> str:
        """
        实现AT+HTTPPOSTFILE指令（从模块本地文件发送POST请求）
        Args:
            file_path (str): 模块内文件路径（如"/usr/test.txt"）
            mode (int, optional): 文件读取模式，默认值1
            offset (int, optional): 文件读取起始偏移量，默认值0

        Raises:
            TypeError: 当file_path非字符串、mode/offset非整数类型时触发
            ValueError: 当file_path为空字符串、mode小于0或offset小于0时触发

        Notes:
            AT+HTTPPOSTFILE指令用于从SIM7600模块本地文件系统读取数据并发送POST请求
            需确保模块本地文件存在且有读取权限

        ==========================================
        Implement AT+HTTPPOSTFILE command (send POST request from module local file)
        Args:
            file_path (str): File path in the module (e.g., "/usr/test.txt")
            mode (int, optional): File reading mode, default value 1
            offset (int, optional): File reading start offset, default value 0

        Raises:
            TypeError: Triggered when file_path is not string, mode/offset is not integer type
            ValueError: Triggered when file_path is empty string, mode is less than 0 or offset is less than 0

        Notes:
            AT+HTTPPOSTFILE command is used to read data from SIM7600 module local file system and send POST request
            Ensure the module local file exists and has read permission
        """
        # 检查file_path参数类型和有效性
        if not isinstance(file_path, str):
            raise TypeError("file_path parameter must be string type")
        if len(file_path.strip()) == 0:
            raise ValueError("file_path parameter cannot be empty string")
        # 检查mode参数类型和有效性
        if not isinstance(mode, int):
            raise TypeError("mode parameter must be integer type")
        if mode < 0:
            raise ValueError("mode parameter must be greater than or equal to 0")
        # 检查offset参数类型和有效性
        if not isinstance(offset, int):
            raise TypeError("offset parameter must be integer type")
        if offset < 0:
            raise ValueError("offset parameter must be greater than or equal to 0")
        # 发送AT+HTTPPOSTFILE指令并返回响应
        return self.sim7600.send_command(f'AT+HTTPPOSTFILE="<file_path>",<mode>,<offset>')


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
