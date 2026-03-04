# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午6:30
# @Author  : alankrantas
# @File    : utils.py
# @Description : SIM800模块工具类 提供UART通信、指令发送、响应等待等通用工具函数
# @License : MIT
# @Platform: MicroPython v1.23.0

# ======================================== 导入相关模块 =========================================

# 导入utime模块，用于时间相关操作
import utime

# ======================================== 全局变量 ============================================

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class SIM800Utils:
    """
    SIM800模块工具类
    SIM800 Module Utility Class

    提供SIM800模块通信所需的通用工具函数，所有方法均为静态方法
    Provide common utility functions for SIM800 module communication, all methods are static

    Attributes:
        无类属性，所有方法均为静态方法
        No class attributes, all methods are static methods

    Methods:
        wait_for_response(uart, expected_response, timeout=5000): 等待指定UART响应
                                                                 Wait for specified UART response
        clear_uart_buffer(uart): 清空UART缓冲区
                                 Clear UART buffer
        send_command(uart, command, wait_for="OK", timeout=2000): 发送AT指令并等待响应
                                                                 Send AT command and wait for response
    """

    @staticmethod
    def wait_for_response(uart, expected_response, timeout=5000):
        """
        等待指定UART响应
        Wait for specified UART response

        Args:
            uart (machine.UART): UART通信对象
                                 UART communication object
            expected_response (str): 期望接收到的响应字符串
                                     Expected response string to receive
            timeout (int, optional): 等待超时时间，单位毫秒，默认5000ms
                                     Wait timeout in milliseconds, default 5000ms

        Returns:
            str or None: 接收到的响应字符串（已解码为UTF-8），超时返回None
                         Received response string (decoded to UTF-8), return None if timeout

        Notes:
            每100ms检查一次UART缓冲区，直到超时或接收到期望响应
            Check UART buffer every 100ms until timeout or expected response is received
        """
        # 记录等待开始时间
        start_time = utime.ticks_ms()
        # 初始化响应数据缓冲区
        response = b''

        # 循环等待响应直到超时
        while utime.ticks_diff(utime.ticks_ms(), start_time) < timeout:
            # 检查UART是否有可用数据
            if uart.any():
                # 读取所有可用数据并追加到缓冲区
                response += uart.read(uart.any())
                # 检查是否包含期望的响应字符串
                if expected_response.encode() in response:
                    # 解码响应并返回
                    return response.decode('utf-8')
            # 短暂延时后继续检查
            utime.sleep_ms(100)

        # 超时返回None
        return None

    @staticmethod
    def clear_uart_buffer(uart):
        """
        清空UART缓冲区
        Clear UART buffer

        Args:
            uart (machine.UART): UART通信对象
                                 UART communication object

        Returns:
            None

        Notes:
            循环读取UART缓冲区直到为空，确保发送新指令前缓冲区干净
            Read UART buffer in loop until empty to ensure clean buffer before sending new commands
        """
        # 循环读取缓冲区数据直到为空
        while uart.any():
            uart.read()

    @staticmethod
    def send_command(uart, command, wait_for="OK", timeout=2000):
        """
        发送AT指令并等待响应
        Send AT command and wait for response

        Args:
            uart (machine.UART): UART通信对象
                                 UART communication object
            command (str): 要发送的AT指令字符串（不含回车符）
                           AT command string to send (without carriage return)
            wait_for (str, optional): 期望等待的响应字符串，默认"OK"
                                      Expected response string to wait for, default "OK"
            timeout (int, optional): 响应等待超时时间，单位毫秒，默认2000ms
                                     Response wait timeout in milliseconds, default 2000ms

        Returns:
            str or None: 接收到的响应字符串，超时返回None
                         Received response string, return None if timeout

        Notes:
            发送指令前会先清空UART缓冲区，指令末尾自动添加回车符\r
            Clear UART buffer before sending command, automatically add carriage return \r at end of command
        """
        # 发送指令前清空UART缓冲区
        SIM800Utils.clear_uart_buffer(uart)
        # 发送AT指令，末尾添加回车符
        uart.write(command + '\r')
        # 等待并返回响应
        return SIM800Utils.wait_for_response(uart, wait_for, timeout)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================