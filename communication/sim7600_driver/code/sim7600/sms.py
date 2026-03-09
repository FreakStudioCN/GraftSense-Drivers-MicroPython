# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午9:30
# @Author  : alankrantas
# @File    : sms.py
# @Description : SIM7600模块SMS功能类 实现短信发送、读取、删除、列表查询等短信相关功能
# @License : MIT
# @Platform: MicroPython v1.23.0

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
    SIM7600 Module SMS Function Class

    封装SIM7600模块的短信相关功能，包括短信发送、读取、删除和按状态查询短信列表等核心功能
    Encapsulates SMS-related functions of SIM7600 module, including core functions such as SMS sending, reading, deletion and SMS list query by status

    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法
                          SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): 初始化SMS功能类
                           Initialize SMS function class
        send_sms(number, message): 发送短信到指定号码
                                   Send SMS to specified phone number
        read_sms(index): 读取指定索引的短信
                         Read SMS with specified index
        delete_sms(index): 删除指定索引的短信
                           Delete SMS with specified index
        list_sms(status): 按状态查询短信列表
                          Query SMS list by status
    """

    def __init__(self, sim7600):
        """
        初始化SMS功能类
        Initialize SMS function class

        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法
                              SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Returns:
            None

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成短信操作
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete SMS operations
        """
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def send_sms(self, number, message):
        """
        发送短信到指定号码
        Send SMS to specified phone number

        Args:
            number (str): 接收短信的手机号码
                          Mobile phone number to receive SMS
            message (str): 要发送的短信内容
                           SMS content to send

        Returns:
            bytes: 短信发送后的响应数据
                   Response data after SMS sending

        Notes:
            先发送AT+CMGS指令指定接收号码，再发送短信内容并添加\x1A(ASCII 26/CTRL+Z)作为结束符
            First send AT+CMGS command to specify recipient number, then send SMS content and add \x1A (ASCII 26/CTRL+Z) as end character
        """
        # 发送指定接收号码的短信发送指令
        self.sim7600.send_command(f'AT+CMGS="{number}"')
        # 发送短信内容并添加结束符(ASCII 26)
        self.sim7600.write_uart(message + "\x1A")
        # 读取并返回短信发送后的响应数据
        return self.sim7600.read_uart()

    def read_sms(self, index):
        """
        读取指定索引的短信
        Read SMS with specified index

        Args:
            index (int): 短信存储索引，从1开始计数
                         SMS storage index, counting from 1

        Returns:
            bytes: 包含短信内容的响应数据
                   Response data containing SMS content

        Notes:
            使用AT+CMGR指令读取指定索引的短信，索引对应SIM卡内的短信存储位置
            Use AT+CMGR command to read SMS with specified index, index corresponds to SMS storage location in SIM card
        """
        # 发送读取指定索引短信的指令并返回响应
        return self.sim7600.send_command(f"AT+CMGR={index}")

    def delete_sms(self, index):
        """
        删除指定索引的短信
        Delete SMS with specified index

        Args:
            index (int): 要删除的短信索引，从1开始计数
                         Index of SMS to delete, counting from 1

        Returns:
            bytes: 删除短信指令的响应数据
                   Response data of delete SMS command

        Notes:
            使用AT+CMGD指令删除指定索引的短信，删除后后续短信索引会重新排序
            Use AT+CMGD command to delete SMS with specified index, subsequent SMS indexes will be reordered after deletion
        """
        # 发送删除指定索引短信的指令并返回响应
        return self.sim7600.send_command(f"AT+CMGD={index}")

    def list_sms(self, status):
        """
        按状态查询短信列表
        Query SMS list by status

        Args:
            status (str): 短信状态筛选条件，可选值:"REC UNREAD"(未读)、"REC READ"(已读)、"STO UNSENT"(未发送)、"STO SENT"(已发送)、"ALL"(全部)
                          SMS status filter condition, optional values: "REC UNREAD" (unread), "REC READ" (read), "STO UNSENT" (unsent), "STO SENT" (sent), "ALL" (all)

        Returns:
            bytes: 包含指定状态短信列表的响应数据
                   Response data containing SMS list of specified status

        Notes:
            使用AT+CMGL指令按状态筛选并列出所有符合条件的短信
            Use AT+CMGL command to filter and list all SMS that meet the conditions by status
        """
        # 发送按状态查询短信列表的指令并返回响应
        return self.sim7600.send_command(f'AT+CMGL="{status}"')


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
