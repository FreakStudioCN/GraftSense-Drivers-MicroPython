# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午7:30
# @Author  : basanovase
# @File    : sms.py
# @Description : SIM800模块SMS扩展类 实现短信格式设置、发送、读取、删除等短信相关功能 参考自:https://github.com/basanovase/sim800
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


class SIM800SMS(SIM800):
    """
    SIM800模块SMS扩展类
    继承自SIM800基类，扩展实现短信格式设置、发送、读取、删除等短信相关功能

    Attributes:
        uart (machine.UART): 继承自SIM800基类的UART通信对象，用于与SIM800模块通信
                             UART communication object inherited from SIM800 base class for communicating with SIM800 module

    Methods:
        set_sms_format(format="1"): 设置短信格式（文本/PDU模式），为短信收发做基础配置
                                    Set SMS format (text/PDU mode) to configure basic settings for SMS sending and receiving
        send_sms(number, message): 向指定手机号码发送文本短信
                                   Send text SMS to specified mobile phone number
        read_sms(index=1): 读取SIM卡中指定索引位置的短信内容
                           Read SMS content at specified index position in SIM card
        delete_sms(index): 删除SIM卡中指定索引位置的短信
                           Delete SMS at specified index position in SIM card
        read_all_sms(): 读取SIM卡中存储的所有短信内容
                        Read all SMS content stored in SIM card
        delete_all_sms(): 删除SIM卡中存储的所有短信（操作不可逆）
                          Delete all SMS stored in SIM card (irreversible operation)

    Notes:
        1. 短信操作前建议先调用set_sms_format设置为文本模式("1")，简化开发
        2. 短信索引从1开始，删除指定索引短信后后续索引会自动重排
        3. 删除所有短信操作不可逆，执行前需确认数据无需保留

    ==========================================
    SIM800 Module SMS Extension Class
    Inherits from SIM800 base class, extends to implement SMS format setting, sending, reading, deleting and other SMS-related functions

    Attributes:
        uart (machine.UART): UART communication object inherited from SIM800 base class for communicating with SIM800 module

    Methods:
        set_sms_format(format="1"): Set SMS format (text/PDU mode) to configure basic settings for SMS sending and receiving
        send_sms(number, message): Send text SMS to specified mobile phone number
        read_sms(index=1): Read SMS content at specified index position in SIM card
        delete_sms(index): Delete SMS at specified index position in SIM card
        read_all_sms(): Read all SMS content stored in SIM card
        delete_all_sms(): Delete all SMS stored in SIM card (irreversible operation)

    Notes:
        1. It is recommended to call set_sms_format to set text mode ("1") before SMS operations to simplify development
        2. SMS index starts from 1, subsequent indexes will be automatically reordered after deleting SMS with specified index
        3. Deleting all SMS is an irreversible operation, confirm data does not need to be retained before execution
    """

    def __init__(self, uart: machine.UART) -> None:
        """
        初始化SIM800SMS扩展类
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
        Initialize SIM800SMS extension class
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

    def set_sms_format(self, format: str = "1") -> bytes:
        """
        设置短信格式
        配置短信的收发模式（文本/PDU），文本模式更易使用，PDU模式支持扩展字符集

        Args:
            format (str, optional): 短信格式类型，"0"为PDU模式，"1"为文本模式，默认"1"
                                    SMS format type, "0" for PDU mode, "1" for text mode, default "1"

        Raises:
            TypeError: 当format参数为None或非字符串类型时触发
                       Triggered when format parameter is None or not a string type
            ValueError: 当format参数非"0"或"1"时触发
                        Triggered when format parameter is not "0" or "1"

        Returns:
            bytes: 设置指令的响应数据，包含格式设置结果
                   Response data of set command, including format setting result

        Notes:
            使用AT+CMGF指令设置短信格式，文本模式更易使用，PDU模式支持中文等扩展字符集
            Use AT+CMGF command to set SMS format, text mode is easier to use, PDU mode supports extended character sets like Chinese

        ==========================================
        Set SMS format
        Configure SMS sending and receiving mode (text/PDU), text mode is easier to use, PDU mode supports extended character sets

        Args:
            format (str, optional): SMS format type, "0" for PDU mode, "1" for text mode, default "1"

        Raises:
            TypeError: Triggered when format parameter is None or not a string type
            ValueError: Triggered when format parameter is not "0" or "1"

        Returns:
            bytes: Response data of set command, including format setting result

        Notes:
            Use AT+CMGF command to set SMS format, text mode is easier to use, PDU mode supports extended character sets like Chinese
        """
        # 验证format参数是否为None
        if format is None:
            raise TypeError("format parameter cannot be None, must be string")
        # 验证format参数类型是否为字符串
        if not isinstance(format, str):
            raise TypeError(f"Expected format type str, got {type(format).__name__} instead")
        # 验证format参数值是否合法
        if format not in ["0", "1"]:
            raise ValueError(f"format parameter must be '0' or '1', got {format}")

        # 发送设置短信格式指令并返回响应
        return self.send_command(f"AT+CMGF={format}")

    def send_sms(self, number: str, message: str) -> bytes:
        """
        发送短信
        向指定手机号码发送文本短信，自动处理指令发送和结束符添加

        Args:
            number (str): 接收短信的手机号码（数字字符串，支持国际区号格式）
                          Mobile phone number to receive SMS (numeric string, supports international area code format)
            message (str): 要发送的短信内容（文本模式下建议使用ASCII字符）
                           SMS content to send (ASCII characters are recommended in text mode)

        Raises:
            TypeError: 当number/message参数为None或非字符串类型时触发
                       Triggered when number/message parameter is None or not a string type
            ValueError: 当number参数为空字符串或message参数为空字符串时触发
                        Triggered when number parameter is empty string or message parameter is empty string

        Returns:
            bytes: 短信发送后的响应数据，包含发送结果（成功/失败）
                   Response data after SMS sending, including sending result (success/failure)

        Notes:
            先发送AT+CMGS指令指定接收号码，再发送短信内容，末尾添加ASCII码26(CTRL+Z)表示结束
            First send AT+CMGS command to specify recipient number, then send SMS content, add ASCII code 26 (CTRL+Z) at end to indicate completion

        ==========================================
        Send SMS message
        Send text SMS to specified mobile phone number, automatically handle command sending and end character addition

        Args:
            number (str): Mobile phone number to receive SMS (numeric string, supports international area code format)
            message (str): SMS content to send (ASCII characters are recommended in text mode)

        Raises:
            TypeError: Triggered when number/message parameter is None or not a string type
            ValueError: Triggered when number parameter is empty string or message parameter is empty string

        Returns:
            bytes: Response data after SMS sending, including sending result (success/failure)

        Notes:
            First send AT+CMGS command to specify recipient number, then send SMS content, add ASCII code 26 (CTRL+Z) at end to indicate completion
        """
        # 验证number参数是否为None
        if number is None:
            raise TypeError("number parameter cannot be None, must be string")
        # 验证number参数类型是否为字符串
        if not isinstance(number, str):
            raise TypeError(f"Expected number type str, got {type(number).__name__} instead")
        # 验证number参数是否为空字符串
        if len(number.strip()) == 0:
            raise ValueError("number parameter cannot be empty string")
        # 验证message参数是否为None
        if message is None:
            raise TypeError("message parameter cannot be None, must be string")
        # 验证message参数类型是否为字符串
        if not isinstance(message, str):
            raise TypeError(f"Expected message type str, got {type(message).__name__} instead")
        # 验证message参数是否为空字符串
        if len(message.strip()) == 0:
            raise ValueError("message parameter cannot be empty string")

        # 发送指定接收号码的指令
        self.send_command(f'AT+CMGS="{number}"')
        # 发送短信内容并添加结束符(ASCII 26)
        self.uart.write(message + chr(26))
        # 读取并返回发送响应
        return self.read_response()

    def read_sms(self, index: int = 1) -> bytes:
        """
        读取指定索引的短信
        读取SIM卡中指定索引位置存储的短信内容

        Args:
            index (int, optional): 短信存储索引，默认1（索引从1开始）
                                   SMS storage index, default 1 (index starts from 1)

        Raises:
            TypeError: 当index参数为None或非整数类型时触发
                       Triggered when index parameter is None or not an integer type
            ValueError: 当index参数小于1时触发
                        Triggered when index parameter is less than 1

        Returns:
            bytes: 包含短信内容的响应数据，格式为文本模式下的原始响应
                   Response data containing SMS content, in raw response format under text mode

        Notes:
            使用AT+CMGR指令读取指定索引的短信，索引从1开始
            Use AT+CMGR command to read SMS with specified index, index starts from 1

        ==========================================
        Read SMS with specified index
        Read SMS content stored at specified index position in SIM card

        Args:
            index (int, optional): SMS storage index, default 1 (index starts from 1)

        Raises:
            TypeError: Triggered when index parameter is None or not an integer type
            ValueError: Triggered when index parameter is less than 1

        Returns:
            bytes: Response data containing SMS content, in raw response format under text mode

        Notes:
            Use AT+CMGR command to read SMS with specified index, index starts from 1
        """
        # 验证index参数是否为None
        if index is None:
            raise TypeError("index parameter cannot be None, must be integer")
        # 验证index参数类型是否为整数
        if not isinstance(index, int):
            raise TypeError(f"Expected index type int, got {type(index).__name__} instead")
        # 验证index参数是否大于等于1
        if index < 1:
            raise ValueError(f"index parameter must be greater than or equal to 1, got {index}")

        # 发送读取指定索引短信的指令并返回响应
        return self.send_command(f"AT+CMGR={index}")

    def delete_sms(self, index: int) -> bytes:
        """
        删除指定索引的短信
        删除SIM卡中指定索引位置存储的短信

        Args:
            index (int): 要删除的短信索引（索引从1开始）
                         Index of SMS to delete (index starts from 1)

        Raises:
            TypeError: 当index参数为None或非整数类型时触发
                       Triggered when index parameter is None or not an integer type
            ValueError: 当index参数小于1时触发
                        Triggered when index parameter is less than 1

        Returns:
            bytes: 删除指令的响应数据，包含删除结果（成功/失败）
                   Response data of delete command, including deletion result (success/failure)

        Notes:
            使用AT+CMGD指令删除指定索引的短信，删除后后续短信索引会重新排序
            Use AT+CMGD command to delete SMS with specified index, subsequent SMS indexes will be reordered after deletion

        ==========================================
        Delete SMS with specified index
        Delete SMS stored at specified index position in SIM card

        Args:
            index (int): Index of SMS to delete (index starts from 1)

        Raises:
            TypeError: Triggered when index parameter is None or not an integer type
            ValueError: Triggered when index parameter is less than 1

        Returns:
            bytes: Response data of delete command, including deletion result (success/failure)

        Notes:
            Use AT+CMGD command to delete SMS with specified index, subsequent SMS indexes will be reordered after deletion
        """
        # 验证index参数是否为None
        if index is None:
            raise TypeError("index parameter cannot be None, must be integer")
        # 验证index参数类型是否为整数
        if not isinstance(index, int):
            raise TypeError(f"Expected index type int, got {type(index).__name__} instead")
        # 验证index参数是否大于等于1
        if index < 1:
            raise ValueError(f"index parameter must be greater than or equal to 1, got {index}")

        # 发送删除指定索引短信的指令并返回响应
        return self.send_command(f"AT+CMGD={index}")

    def read_all_sms(self) -> bytes:
        """
        读取所有短信
        读取SIM卡中存储的全部短信内容，返回原始响应数据

        Args:
            None

        Returns:
            bytes: 包含所有短信内容的响应数据，按索引顺序排列
                   Response data containing all SMS content, arranged in index order

        Notes:
            使用AT+CMGL="ALL"指令读取存储的所有短信
            Use AT+CMGL="ALL" command to read all stored SMS messages

        ==========================================
        Read all SMS messages
        Read all SMS content stored in SIM card and return raw response data

        Args:
            None

        Returns:
            bytes: Response data containing all SMS content, arranged in index order

        Notes:
            Use AT+CMGL="ALL" command to read all stored SMS messages
        """
        # 发送读取所有短信的指令并返回响应
        return self.send_command('AT+CMGL="ALL"')

    def delete_all_sms(self) -> bytes:
        """
        删除所有短信
        删除SIM卡中存储的全部短信，操作不可逆

        Args:
            None

        Returns:
            bytes: 删除所有短信指令的响应数据，包含删除结果（成功/失败）
                   Response data of delete all SMS command, including deletion result (success/failure)

        Notes:
            使用AT+CMGDA="DEL ALL"指令删除存储的所有短信，操作不可逆
            Use AT+CMGDA="DEL ALL" command to delete all stored SMS messages, operation is irreversible

        ==========================================
        Delete all SMS messages
        Delete all SMS stored in SIM card, operation is irreversible

        Args:
            None

        Returns:
            bytes: Response data of delete all SMS command, including deletion result (success/failure)

        Notes:
            Use AT+CMGDA="DEL ALL" command to delete all stored SMS messages, operation is irreversible
        """
        # 发送删除所有短信的指令并返回响应
        return self.send_command('AT+CMGDA="DEL ALL"')


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
