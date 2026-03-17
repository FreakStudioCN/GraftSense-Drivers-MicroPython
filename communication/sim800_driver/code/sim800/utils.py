# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午6:30
# @Author  : basanovase
# @File    : utils.py
# @Description : SIM800模块工具类 提供UART通信、指令发送、响应等待等通用工具函数 参考自:https://github.com/basanovase/sim800
# @License : MIT
# @Platform: MicroPython v1.23.0

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入machine模块，用于UART类型注解和硬件操作
import machine

# 导入utime模块，用于时间戳和延时操作
import utime


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class SIM800Utils:
    """
    SIM800模块工具类
    提供SIM800模块通信所需的通用工具函数，所有方法均为静态方法，无需实例化即可调用

    Attributes:
        无类属性，所有方法均为静态方法，仅依赖传入的UART对象完成通信操作
        No class attributes, all methods are static and only rely on incoming UART objects for communication operations

    Methods:
        wait_for_response(uart, expected_response, timeout=5000): 循环检查UART缓冲区，等待指定响应字符串，超时返回None
                                                                 Continuously check UART buffer, wait for specified response string, return None if timeout
        clear_uart_buffer(uart): 清空UART接收缓冲区，确保新指令响应不受历史数据干扰
                                 Clear UART receive buffer to ensure new command responses are not interfered by historical data
        send_command(uart, command, wait_for="OK", timeout=2000): 标准化发送AT指令流程（清缓冲区→发指令→等响应）
                                                                 Standardize AT command sending process (clear buffer → send command → wait for response)

    Notes:
        1. 所有方法均做了参数合法性校验，避免空值和非法参数导致的运行异常
        2. 响应等待采用非阻塞式轮询（100ms间隔），兼顾响应速度和系统资源占用
        3. 所有字符串编码/解码均使用UTF-8，兼容大部分AT指令响应格式

    ==========================================
    SIM800 Module Utility Class
    Provide common utility functions for SIM800 module communication, all methods are static and can be called without instantiation

    Attributes:
        No class attributes, all methods are static and only rely on incoming UART objects for communication operations

    Methods:
        wait_for_response(uart, expected_response, timeout=5000): Continuously check UART buffer, wait for specified response string, return None if timeout
        clear_uart_buffer(uart): Clear UART receive buffer to ensure new command responses are not interfered by historical data
        send_command(uart, command, wait_for="OK", timeout=2000): Standardize AT command sending process (clear buffer → send command → wait for response)

    Notes:
        1. All methods include parameter validity checks to avoid runtime exceptions caused by null values and illegal parameters
        2. Response waiting uses non-blocking polling (100ms interval) to balance response speed and system resource usage
        3. All string encoding/decoding uses UTF-8, compatible with most AT command response formats
    """

    @staticmethod
    def wait_for_response(uart: machine.UART, expected_response: str, timeout: int = 5000) -> str | None:
        """
        等待指定UART响应
        循环轮询UART缓冲区，直到接收到期望响应或超时，返回完整响应字符串（UTF-8解码）

        Args:
            uart (machine.UART): UART通信对象，必须是已初始化的machine.UART实例
                                 UART communication object, must be an initialized machine.UART instance
            expected_response (str): 期望接收到的响应字符串（如"OK"、"READY"）
                                     Expected response string (e.g., "OK", "READY")
            timeout (int, optional): 等待超时时间，单位毫秒，默认5000ms（5秒）
                                     Wait timeout in milliseconds, default 5000ms (5 seconds)

        Raises:
            TypeError: 当uart参数为None、expected_response参数为None或非字符串类型时触发
                       Triggered when uart parameter is None, or expected_response parameter is None/not a string type
            ValueError: 当timeout参数小于等于0时触发
                        Triggered when timeout parameter is less than or equal to 0

        Returns:
            str or None: 接收到的完整响应字符串（UTF-8解码），超时则返回None
                         Complete received response string (UTF-8 decoded), return None if timeout

        Notes:
            每100ms检查一次UART缓冲区，直到超时或接收到期望响应
            Check UART buffer every 100ms until timeout or expected response is received

        ==========================================
        Wait for specified UART response
        Continuously poll UART buffer until expected response is received or timeout, return complete response string (UTF-8 decoded)

        Args:
            uart (machine.UART): UART communication object, must be an initialized machine.UART instance
            expected_response (str): Expected response string (e.g., "OK", "READY")
            timeout (int, optional): Wait timeout in milliseconds, default 5000ms (5 seconds)

        Raises:
            TypeError: Triggered when uart parameter is None, or expected_response parameter is None/not a string type
            ValueError: Triggered when timeout parameter is less than or equal to 0

        Returns:
            str or None: Complete received response string (UTF-8 decoded), return None if timeout

        Notes:
            Check UART buffer every 100ms until timeout or expected response is received
        """
        # 校验uart参数是否为None
        if uart is None:
            raise TypeError("uart parameter cannot be None, must be an initialized machine.UART instance")
        # 校验expected_response参数是否为None或非字符串
        if expected_response is None:
            raise TypeError("expected_response parameter cannot be None, must be a string")
        if not isinstance(expected_response, str):
            raise TypeError(f"Expected expected_response type str, got {type(expected_response).__name__} instead")
        # 校验timeout参数是否合法
        if timeout <= 0:
            raise ValueError(f"timeout parameter must be greater than 0, got {timeout}")

        # 记录等待开始的时间戳（毫秒）
        start_time = utime.ticks_ms()
        # 初始化字节类型的响应缓冲区，用于拼接接收到的原始数据
        response = b""

        # 循环等待响应，直到超时
        while utime.ticks_diff(utime.ticks_ms(), start_time) < timeout:
            # 检查UART缓冲区是否有可用数据
            if uart.any():
                # 读取缓冲区中所有可用字节并追加到响应缓冲区
                response += uart.read(uart.any())
                # 检查响应缓冲区是否包含期望的响应字符串（编码为字节串匹配）
                if expected_response.encode("utf-8") in response:
                    # 将完整响应字节串解码为UTF-8字符串并返回
                    return response.decode("utf-8")
            # 短暂延时（100ms）后继续轮询，避免过度占用CPU
            utime.sleep_ms(100)

        # 超时未接收到期望响应，返回None
        return None

    @staticmethod
    def clear_uart_buffer(uart: machine.UART) -> None:
        """
        清空UART缓冲区
        循环读取UART接收缓冲区所有数据直到为空，确保发送新指令前无历史数据残留

        Args:
            uart (machine.UART): UART通信对象，必须是已初始化的machine.UART实例
                                 UART communication object, must be an initialized machine.UART instance

        Raises:
            TypeError: 当uart参数为None时触发
                       Triggered when uart parameter is None

        Returns:
            None

        Notes:
            循环读取UART缓冲区直到为空，确保发送新指令前缓冲区干净
            Read UART buffer in loop until empty to ensure clean buffer before sending new commands

        ==========================================
        Clear UART buffer
        Continuously read all data from UART receive buffer until empty, ensure no historical data remains before sending new commands

        Args:
            uart (machine.UART): UART communication object, must be an initialized machine.UART instance

        Raises:
            TypeError: Triggered when uart parameter is None

        Returns:
            None

        Notes:
            Read UART buffer in loop until empty to ensure clean buffer before sending new commands
        """
        # 校验uart参数是否为None
        if uart is None:
            raise TypeError("uart parameter cannot be None, must be an initialized machine.UART instance")

        # 循环读取缓冲区数据直到为空
        while uart.any():
            # 读取缓冲区所有可用数据（不保存），完成清空操作
            uart.read()

    @staticmethod
    def send_command(uart: machine.UART, command: str, wait_for: str = "OK", timeout: int = 2000) -> str | None:
        """
        发送AT指令并等待响应
        标准化AT指令发送流程：清空缓冲区→发送指令（自动加回车）→等待指定响应

        Args:
            uart (machine.UART): UART通信对象，必须是已初始化的machine.UART实例
                                 UART communication object, must be an initialized machine.UART instance
            command (str): 要发送的AT指令字符串（不含回车符，如"AT+CMGF=1"）
                           AT command string to send (without carriage return, e.g., "AT+CMGF=1")
            wait_for (str, optional): 期望等待的响应字符串，默认"OK"（AT指令通用成功响应）
                                      Expected response string to wait for, default "OK" (general success response for AT commands)
            timeout (int, optional): 响应等待超时时间，单位毫秒，默认2000ms（2秒）
                                     Response wait timeout in milliseconds, default 2000ms (2 seconds)

        Raises:
            TypeError: 当uart参数为None、command参数为None或非字符串类型、wait_for参数为None或非字符串类型时触发
                       Triggered when uart parameter is None, command parameter is None/not a string type, or wait_for parameter is None/not a string type
            ValueError: 当command参数为空字符串、timeout参数小于等于0时触发
                        Triggered when command parameter is empty string, or timeout parameter is less than or equal to 0

        Returns:
            str or None: 接收到的完整响应字符串（UTF-8解码），超时则返回None
                         Complete received response string (UTF-8 decoded), return None if timeout

        Notes:
            发送指令前会先清空UART缓冲区，指令末尾自动添加回车符\r
            Clear UART buffer before sending command, automatically add carriage return \r at end of command

        ==========================================
        Send AT command and wait for response
        Standardize AT command sending process: clear buffer → send command (auto add carriage return) → wait for specified response

        Args:
            uart (machine.UART): UART communication object, must be an initialized machine.UART instance
            command (str): AT command string to send (without carriage return, e.g., "AT+CMGF=1")
            wait_for (str, optional): Expected response string to wait for, default "OK" (general success response for AT commands)
            timeout (int, optional): Response wait timeout in milliseconds, default 2000ms (2 seconds)

        Raises:
            TypeError: Triggered when uart parameter is None, command parameter is None/not a string type, or wait_for parameter is None/not a string type
            ValueError: Triggered when command parameter is empty string, or timeout parameter is less than or equal to 0

        Returns:
            str or None: Complete received response string (UTF-8 decoded), return None if timeout

        Notes:
            Clear UART buffer before sending command, automatically add carriage return \r at end of command
        """
        # 校验uart参数是否为None
        if uart is None:
            raise TypeError("uart parameter cannot be None, must be an initialized machine.UART instance")
        # 校验command参数是否为None、非字符串或空字符串
        if command is None:
            raise TypeError("command parameter cannot be None, must be a non-empty string")
        if not isinstance(command, str):
            raise TypeError(f"Expected command type str, got {type(command).__name__} instead")
        if len(command.strip()) == 0:
            raise ValueError("command parameter cannot be empty string")
        # 校验wait_for参数是否为None或非字符串
        if wait_for is None:
            raise TypeError("wait_for parameter cannot be None, must be a string")
        if not isinstance(wait_for, str):
            raise TypeError(f"Expected wait_for type str, got {type(wait_for).__name__} instead")
        # 校验timeout参数是否合法
        if timeout <= 0:
            raise ValueError(f"timeout parameter must be greater than 0, got {timeout}")

        # 发送指令前清空UART缓冲区，避免历史数据干扰响应判断
        SIM800Utils.clear_uart_buffer(uart)
        # 发送AT指令，末尾自动添加回车符\r（AT指令标准结束符）
        uart.write(command + "\r")
        # 等待并返回指定响应，复用wait_for_response方法
        return SIM800Utils.wait_for_response(uart, wait_for, timeout)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
