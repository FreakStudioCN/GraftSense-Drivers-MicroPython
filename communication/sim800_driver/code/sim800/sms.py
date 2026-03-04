# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午7:30
# @Author  : basanovase
# @File    : sms.py
# @Description : SIM800模块SMS扩展类 实现短信格式设置、发送、读取、删除等短信相关功能
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

class SIM800SMS(SIM800):
    """
    SIM800模块SMS扩展类
    SIM800 Module SMS Extension Class

    继承自SIM800基类，扩展实现短信格式设置、发送、读取、删除等短信相关功能
    Inherits from SIM800 base class, extends to implement SMS format setting, sending, reading, deleting and other SMS-related functions

    Attributes:
        uart (machine.UART): 继承自SIM800基类的UART通信对象
                             UART communication object inherited from SIM800 base class
        baud (int): 继承自SIM800基类的UART波特率
                    UART baud rate inherited from SIM800 base class

    Methods:
        set_sms_format(format="1"): 设置短信格式
                                    Set SMS format
        send_sms(number, message): 发送短信
                                   Send SMS message
        read_sms(index=1): 读取指定索引的短信
                           Read SMS with specified index
        delete_sms(index): 删除指定索引的短信
                           Delete SMS with specified index
        read_all_sms(): 读取所有短信
                        Read all SMS messages
        delete_all_sms(): 删除所有短信
                          Delete all SMS messages
    """

    def set_sms_format(self, format="1"):
        """
        设置短信格式
        Set SMS format

        Args:
            format (str, optional): 短信格式类型，"0"为PDU模式，"1"为文本模式，默认"1"
                                    SMS format type, "0" for PDU mode, "1" for text mode, default "1"

        Returns:
            bytes: 设置指令的响应数据
                   Response data of set command

        Notes:
            使用AT+CMGF指令设置短信格式，文本模式更易使用，PDU模式支持中文等扩展字符集
            Use AT+CMGF command to set SMS format, text mode is easier to use, PDU mode supports extended character sets like Chinese
        """
        # 发送设置短信格式指令并返回响应
        return self.send_command(f'AT+CMGF={format}')

    def send_sms(self, number, message):
        """
        发送短信
        Send SMS message

        Args:
            number (str): 接收短信的手机号码
                          Mobile phone number to receive SMS
            message (str): 要发送的短信内容
                           SMS content to send

        Returns:
            bytes: 短信发送后的响应数据
                   Response data after SMS sending

        Notes:
            先发送AT+CMGS指令指定接收号码，再发送短信内容，末尾添加ASCII码26(CTRL+Z)表示结束
            First send AT+CMGS command to specify recipient number, then send SMS content, add ASCII code 26 (CTRL+Z) at end to indicate completion
        """
        # 发送指定接收号码的指令
        self.send_command(f'AT+CMGS="{number}"')
        # 发送短信内容并添加结束符(ASCII 26)
        self.uart.write(message + chr(26))
        # 读取并返回发送响应
        return self.read_response()

    def read_sms(self, index=1):
        """
        读取指定索引的短信
        Read SMS with specified index

        Args:
            index (int, optional): 短信存储索引，默认1
                                   SMS storage index, default 1

        Returns:
            bytes: 包含短信内容的响应数据
                   Response data containing SMS content

        Notes:
            使用AT+CMGR指令读取指定索引的短信，索引从1开始
            Use AT+CMGR command to read SMS with specified index, index starts from 1
        """
        # 发送读取指定索引短信的指令并返回响应
        return self.send_command(f'AT+CMGR={index}')

    def delete_sms(self, index):
        """
        删除指定索引的短信
        Delete SMS with specified index

        Args:
            index (int): 要删除的短信索引
                         Index of SMS to delete

        Returns:
            bytes: 删除指令的响应数据
                   Response data of delete command

        Notes:
            使用AT+CMGD指令删除指定索引的短信，删除后后续短信索引会重新排序
            Use AT+CMGD command to delete SMS with specified index, subsequent SMS indexes will be reordered after deletion
        """
        # 发送删除指定索引短信的指令并返回响应
        return self.send_command(f'AT+CMGD={index}')

    def read_all_sms(self):
        """
        读取所有短信
        Read all SMS messages

        Args:
            None

        Returns:
            bytes: 包含所有短信内容的响应数据
                   Response data containing all SMS content

        Notes:
            使用AT+CMGL="ALL"指令读取存储的所有短信
            Use AT+CMGL="ALL" command to read all stored SMS messages
        """
        # 发送读取所有短信的指令并返回响应
        return self.send_command('AT+CMGL="ALL"')

    def delete_all_sms(self):
        """
        删除所有短信
        Delete all SMS messages

        Args:
            None

        Returns:
            bytes: 删除所有短信指令的响应数据
                   Response data of delete all SMS command

        Notes:
            使用AT+CMGDA="DEL ALL"指令删除存储的所有短信，操作不可逆
            Use AT+CMGDA="DEL ALL" command to delete all stored SMS messages, operation is irreversible
        """
        # 发送删除所有短信的指令并返回响应
        return self.send_command('AT+CMGDA="DEL ALL"')

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================