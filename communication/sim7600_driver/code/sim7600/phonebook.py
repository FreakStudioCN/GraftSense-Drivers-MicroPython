# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午10:30
# @Author  : alankrantas
# @File    : phonebook.py
# @Description : SIM7600模块电话本功能类 实现联系人添加、读取、删除、列表查询等电话本管理功能
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
class Phonebook:
    """
    SIM7600模块电话本功能类
    SIM7600 Module Phonebook Function Class

    封装SIM7600模块的电话本管理功能，包括联系人添加、读取、删除和存储位置查询等核心功能
    Encapsulates phonebook management functions of SIM7600 module, including core functions such as contact addition, reading, deletion and storage location query

    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command方法用于发送AT指令
                          SIM7600 module core object, must contain send_command method for sending AT commands

    Methods:
        __init__(sim7600): 初始化电话本功能类
                           Initialize phonebook function class
        add_contact(storage, index, name, number): 添加联系人到指定存储位置
                                                   Add contact to specified storage location
        read_contact(storage, index): 读取指定存储位置和索引的联系人
                                      Read contact from specified storage location and index
        delete_contact(storage, index): 删除指定存储位置和索引的联系人
                                        Delete contact from specified storage location and index
        list_contacts(storage): 查询指定存储位置的电话本信息
                                Query phonebook information of specified storage location
    """

    def __init__(self, sim7600):
        """
        初始化电话本功能类
        Initialize phonebook function class

        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command方法
                              SIM7600 module core object, must implement send_command method

        Returns:
            None

        Notes:
            依赖SIM7600核心对象的send_command方法进行AT指令通信，实现电话本管理
            Depends on the send_command method of the SIM7600 core object for AT command communication to implement phonebook management
        """
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def add_contact(self, storage, index, name, number):
        """
        添加联系人到指定存储位置
        Add contact to specified storage location

        Args:
            storage (str): 存储位置标识，如"SM"(SIM卡)、"ME"(模块内部)
                           Storage location identifier, such as "SM" (SIM card), "ME" (module internal)
            index (int): 联系人存储索引，从1开始计数
                         Contact storage index, counting from 1
            name (str): 联系人姓名
                        Contact name
            number (str): 联系人电话号码
                          Contact phone number

        Returns:
            None

        Notes:
            使用AT+CPBW指令添加联系人，129表示电话本号码类型为国际格式(E.164)
            Use AT+CPBW command to add contact, 129 indicates that the phonebook number type is international format (E.164)
        """
        # 发送添加联系人指令，配置索引、号码、类型和姓名
        self.sim7600.send_command(f'AT+CPBW={index},"{number}",129,"{name}"')

    def read_contact(self, storage, index):
        """
        读取指定存储位置和索引的联系人
        Read contact from specified storage location and index

        Args:
            storage (str): 存储位置标识，如"SM"(SIM卡)、"ME"(模块内部)
                           Storage location identifier, such as "SM" (SIM card), "ME" (module internal)
            index (int): 联系人存储索引，从1开始计数
                         Contact storage index, counting from 1

        Returns:
            bytes: 包含联系人信息的响应数据
                   Response data containing contact information

        Notes:
            使用AT+CPBR指令读取指定索引的联系人信息，返回数据包含姓名、号码等内容
            Use AT+CPBR command to read contact information of specified index, return data includes name, number and other content
        """
        # 发送读取联系人指令并返回响应
        return self.sim7600.send_command(f'AT+CPBR={index}')

    def delete_contact(self, storage, index):
        """
        删除指定存储位置和索引的联系人
        Delete contact from specified storage location and index

        Args:
            storage (str): 存储位置标识，如"SM"(SIM卡)、"ME"(模块内部)
                           Storage location identifier, such as "SM" (SIM card), "ME" (module internal)
            index (int): 要删除的联系人索引，从1开始计数
                         Index of contact to delete, counting from 1

        Returns:
            bytes: 删除联系人指令的响应数据
                   Response data of delete contact command

        Notes:
            使用AT+CPBW指令仅指定索引即可删除对应位置的联系人
            Use AT+CPBW command with only index specified to delete contact at corresponding position
        """
        # 发送删除联系人指令并返回响应
        return self.sim7600.send_command(f'AT+CPBW={index}')

    def list_contacts(self, storage):
        """
        查询指定存储位置的电话本信息
        Query phonebook information of specified storage location

        Args:
            storage (str): 存储位置标识，如"SM"(SIM卡)、"ME"(模块内部)、"EN"(紧急号码)
                           Storage location identifier, such as "SM" (SIM card), "ME" (module internal), "EN" (emergency number)

        Returns:
            bytes: 包含电话本存储信息的响应数据
                   Response data containing phonebook storage information

        Notes:
            使用AT+CPBS指令设置并查询指定存储位置的电话本信息，返回容量、已用空间等数据
            Use AT+CPBS command to set and query phonebook information of specified storage location, return capacity, used space and other data
        """
        # 发送查询电话本信息指令并返回响应
        return self.sim7600.send_command(f'AT+CPBS="{storage}"')

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================