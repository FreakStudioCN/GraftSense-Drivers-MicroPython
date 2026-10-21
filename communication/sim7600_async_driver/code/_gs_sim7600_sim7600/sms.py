# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午9:30
# @Author  : basanovase
# @File    : sms.py
# @Description : SIM7600模块SMS功能类 实现短信发送、读取、删除、列表查询等短信相关功能 参考自：https://github.com/basanovase/sim7600
# @License : MIT
__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class SMS:
    """
    SIM7600模块SMS功能类
    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法

    Methods:
        __init__(sim7600): 初始化SMS功能类
        set_sms_mode(gmgf=1,csmp='17,11,0,0',CSCS="IRA"): 配置短信工作模式参数
        send_sms(number, message): 发送短信到指定号码
        read_sms(index): 读取指定索引的短信
        delete_sms(index): 删除指定索引的短信
        list_sms(status): 按状态查询短信列表

    Notes:
        所有短信操作依赖SIM7600核心对象的AT指令发送和UART读写能力，使用前需确保核心对象方法正常可用
        短信发送前建议先调用set_sms_mode配置工作模式，避免编码或格式错误

    ==========================================
    SIM7600 Module SMS Function Class
    Attributes:
        sim7600 (object): SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): Initialize SMS function class
        set_sms_mode(gmgf=1,csmp='17,11,0,0',CSCS="IRA"): Configure SMS working mode parameters
        send_sms(number, message): Send SMS to specified phone number
        read_sms(index): Read SMS with specified index
        delete_sms(index): Delete SMS with specified index
        list_sms(status): Query SMS list by status

    Notes:
        All SMS operations depend on the AT command sending and UART read/write capabilities of the SIM7600 core object, ensure the core object methods are available before use
        It is recommended to call set_sms_mode to configure working mode before sending SMS to avoid encoding or format errors
    """

    def __init__(self, sim7600: object) -> None:
        """
        初始化SMS功能类
        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法

        Raises:
            TypeError: 当sim7600参数为None时触发
            AttributeError: 当sim7600对象缺少必要方法（send_command/write_uart/read_uart）时触发

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成短信操作

        ==========================================
        Initialize SMS function class
        Args:
            sim7600 (object): SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Raises:
            TypeError: Triggered when sim7600 parameter is None
            AttributeError: Triggered when sim7600 object lacks necessary methods (send_command/write_uart/read_uart)

        Notes:
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete SMS operations
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

    def set_sms_mode(self, gmgf: int = 1, csmp: str = "17,11,0,0", CSCS: str = "IRA") -> None:
        """
        配置短信工作模式参数
        Args:
            gmgf (int, optional): 短信格式模式，1为文本模式，默认值1
            csmp (str, optional): 短信参数设置，默认值'17,11,0,0'
            CSCS (str, optional): 字符集设置，默认值"IRA"（兼容GSM 03.38编码）

        Raises:
            TypeError: 当gmgf非整数、csmp/CSCS非字符串类型时触发
            ValueError: 当gmgf小于0、csmp/CSCS为空字符串时触发

        Notes:
            依次配置短信格式、参数和字符集，为短信发送和读取提供正确的格式基础
            该方法需在发送/读取短信前调用，确保短信编码和格式正确

        ==========================================
        Configure SMS working mode parameters
        Args:
            gmgf (int, optional): SMS format mode, 1 for text mode, default value 1
            csmp (str, optional): SMS parameter setting, default value '17,11,0,0'
            CSCS (str, optional): Character set setting, default value "IRA" (compatible with GSM 03.38 encoding)

        Raises:
            TypeError: Triggered when gmgf is not integer, csmp/CSCS is not string type
            ValueError: Triggered when gmgf is less than 0, csmp/CSCS is empty string

        Notes:
            Configure SMS format, parameters and character set in sequence to provide correct format foundation for SMS sending and reading
            This method must be called before sending/reading SMS to ensure correct SMS encoding and format
        """
        # 检查gmgf参数类型和有效性
        if not isinstance(gmgf, int):
            raise TypeError("gmgf parameter must be integer type")
        if gmgf < 0:
            raise ValueError("gmgf parameter must be greater than or equal to 0")
        # 检查csmp参数类型和有效性
        if not isinstance(csmp, str):
            raise TypeError("csmp parameter must be string type")
        if len(csmp.strip()) == 0:
            raise ValueError("csmp parameter cannot be empty string")
        # 检查CSCS参数类型和有效性
        if not isinstance(CSCS, str):
            raise TypeError("CSCS parameter must be string type")
        if len(CSCS.strip()) == 0:
            raise ValueError("CSCS parameter cannot be empty string")
        # 配置短信格式为文本模式
        self.sim7600.send_command(f"AT+CMGF=1")
        # 配置短信参数
        self.sim7600.send_command(f"AT+CSMP=17,11,0,0")
        # 配置短信字符集
        self.sim7600.send_command(f'AT+CSCS="IRA" ')

    def send_sms(self, number: str, message: str) -> bytes:
        """
        发送短信到指定号码
        Args:
            number (str): 接收短信的手机号码
            message (str): 要发送的短信内容

        Raises:
            TypeError: 当number或message非字符串类型时触发
            ValueError: 当number为空字符串或格式不合法、message为空字符串时触发

        Notes:
            先发送AT+CMGS指令指定接收号码，再发送短信内容并添加\x1A(ASCII 26/CTRL+Z)作为结束符
            手机号码需包含国家码（如+8613800138000）或本地格式（如13800138000）

        ==========================================
        Send SMS to specified phone number
        Args:
            number (str): Mobile phone number to receive SMS
            message (str): SMS content to send

        Raises:
            TypeError: Triggered when number or message is not string type
            ValueError: Triggered when number is empty string or illegal format, message is empty string

        Notes:
            First send AT+CMGS command to specify recipient number, then send SMS content and add \x1A (ASCII 26/CTRL+Z) as end character
            Mobile phone number must include country code (e.g. +8613800138000) or local format (e.g. 13800138000)
        """
        # 检查number参数类型和有效性
        if not isinstance(number, str):
            raise TypeError("number parameter must be string type")
        if len(number.strip()) == 0:
            raise ValueError("number parameter cannot be empty string")
        # 检查message参数类型和有效性
        if not isinstance(message, str):
            raise TypeError("message parameter must be string type")
        if len(message.strip()) == 0:
            raise ValueError("message parameter cannot be empty string")
        # 发送指定接收号码的短信发送指令
        self.sim7600.send_command(f'AT+CMGS="{number}"')
        # 发送短信内容
        self.sim7600.uart.write(message)
        # 添加短信发送结束符(ASCII 26/CTRL+Z)
        self.sim7600.uart.write("\x1A")
        # 读取并返回短信发送后的响应数据
        return self.sim7600.uart.read()

    def read_sms(self, index: int) -> bytes:
        """
        读取指定索引的短信
        Args:
            index (int): 短信存储索引，从1开始计数

        Raises:
            TypeError: 当index非整数类型时触发
            ValueError: 当index小于1时触发

        Notes:
            使用AT+CMGR指令读取指定索引的短信，索引对应SIM卡内的短信存储位置
            读取前需确保set_sms_mode已配置正确的字符集，避免乱码

        ==========================================
        Read SMS with specified index
        Args:
            index (int): SMS storage index, counting from 1

        Raises:
            TypeError: Triggered when index is not integer type
            ValueError: Triggered when index is less than 1

        Notes:
            Use AT+CMGR command to read SMS with specified index, index corresponds to SMS storage location in SIM card
            Ensure set_sms_mode has configured correct character set before reading to avoid garbled characters
        """
        # 检查index参数类型和有效性
        if not isinstance(index, int):
            raise TypeError("index parameter must be integer type")
        if index < 1:
            raise ValueError("index parameter must be greater than or equal to 1")
        # 发送读取指定索引短信的指令并返回响应
        return self.sim7600.send_command(f"AT+CMGR={index}")

    def delete_sms(self, index: int) -> bytes:
        """
        删除指定索引的短信
        Args:
            index (int): 要删除的短信索引，从1开始计数

        Raises:
            TypeError: 当index非整数类型时触发
            ValueError: 当index小于1时触发

        Notes:
            使用AT+CMGD指令删除指定索引的短信，删除后后续短信索引会重新排序
            建议先调用list_sms获取有效索引后再执行删除操作

        ==========================================
        Delete SMS with specified index
        Args:
            index (int): Index of SMS to delete, counting from 1

        Raises:
            TypeError: Triggered when index is not integer type
            ValueError: Triggered when index is less than 1

        Notes:
            Use AT+CMGD command to delete SMS with specified index, subsequent SMS indexes will be reordered after deletion
            It is recommended to call list_sms to get valid index before executing delete operation
        """
        # 检查index参数类型和有效性
        if not isinstance(index, int):
            raise TypeError("index parameter must be integer type")
        if index < 1:
            raise ValueError("index parameter must be greater than or equal to 1")
        # 发送删除指定索引短信的指令并返回响应
        return self.sim7600.send_command(f"AT+CMGD={index}")

    def list_sms(self, status: str) -> bytes:
        """
        按状态查询短信列表
        Args:
            status (str): 短信状态筛选条件，可选值:"REC UNREAD"(未读)、"REC READ"(已读)、"STO UNSENT"(未发送)、"STO SENT"(已发送)、"ALL"(全部)

        Raises:
            TypeError: 当status非字符串类型时触发
            ValueError: 当status为空字符串或不在可选值范围内时触发

        Notes:
            使用AT+CMGL指令按状态筛选并列出所有符合条件的短信
            响应数据包含短信索引、状态、发送号码、时间和内容等信息

        ==========================================
        Query SMS list by status
        Args:
            status (str): SMS status filter condition, optional values: "REC UNREAD" (unread), "REC READ" (read), "STO UNSENT" (unsent), "STO SENT" (sent), "ALL" (all)

        Raises:
            TypeError: Triggered when status is not string type
            ValueError: Triggered when status is empty string or not in optional values range

        Notes:
            Use AT+CMGL command to filter and list all SMS that meet the conditions by status
            Response data includes SMS index, status, sending number, time and content etc.
        """
        # 检查status参数类型和有效性
        if not isinstance(status, str):
            raise TypeError("status parameter must be string type")
        if len(status.strip()) == 0:
            raise ValueError("status parameter cannot be empty string")
        # 定义合法的状态值列表
        valid_status = ["REC UNREAD", "REC READ", "STO UNSENT", "STO SENT", "ALL"]
        if status not in valid_status:
            raise ValueError(f"status parameter must be one of {valid_status}")
        # 发送按状态查询短信列表的指令并返回响应
        return self.sim7600.send_command(f'AT+CMGL="{status}"')


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
