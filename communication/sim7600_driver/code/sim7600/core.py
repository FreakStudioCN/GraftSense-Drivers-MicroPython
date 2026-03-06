# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:00
# @Author  : alankrantas
# @File    : core.py
# @Description : SIM7600模块基础功能类 实现UART通信、模块启停、网络连接、状态监控等核心基础功能
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入硬件控制模块，用于UART串口配置
import machine
# 导入时间模块，用于超时判断和时间戳计算
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class SIM7600:
    """
    SIM7600模块基础功能类
    SIM7600 Module Basic Function Class

    实现SIM7600模块的核心基础功能，包括UART通信初始化、AT指令发送、模块电源管理、网络连接管理、状态监控等，
    是所有扩展功能类的基础父类
    Implement core basic functions of SIM7600 module, including UART communication initialization, AT command sending, 
    module power management, network connection management, status monitoring, etc., and is the basic parent class of all extended function classes

    Attributes:
        uart (machine.UART): UART通信对象，用于与SIM7600模块进行数据交互
                             UART communication object for data interaction with SIM7600 module

    Methods:
        __init__(uart_id, tx_pin, rx_pin, baudrate=115200): 初始化SIM7600模块UART通信
                                                            Initialize SIM7600 module UART communication
        send_command(command, timeout=3000): 发送AT指令并获取响应
                                             Send AT command and get response
        power_on(): 开启模块全功能模式
                    Turn on module full function mode
        power_off(): 关闭模块电源
                     Turn off module power
        reset_module(): 重置模块
                        Reset module
        set_power_mode(mode): 设置模块功耗模式
                              Set module power consumption mode
        monitor_voltage(): 监控模块电池电压
                           Monitor module battery voltage
        connect(apn, user='', password=''): 建立GPRS网络连接
                                            Establish GPRS network connection
        disconnect(): 断开GPRS网络连接
                      Disconnect GPRS network connection
        get_network_status(): 获取网络注册状态
                              Get network registration status
        set_flight_mode(enable): 设置飞行模式
                                 Set flight mode
    """

    def __init__(self, uart_id, tx_pin, rx_pin, baudrate=115200):
        """
        初始化SIM7600模块UART通信
        Initialize SIM7600 module UART communication

        Args:
            uart_id (int): UART外设编号（如0、1）
                           UART peripheral number (e.g. 0, 1)
            tx_pin (int/machine.Pin): UART发送引脚编号/对象
                                      UART transmit pin number/object
            rx_pin (int/machine.Pin): UART接收引脚编号/对象
                                      UART receive pin number/object
            baudrate (int, optional): UART通信波特率，默认115200
                                      UART communication baud rate, default 115200

        Returns:
            None

        Notes:
            根据指定的UART编号和引脚配置串口通信参数，建立与SIM7600模块的物理连接
            Configure serial communication parameters according to specified UART number and pins, establish physical connection with SIM7600 module
        """
        # 初始化UART通信对象，配置波特率、发送引脚、接收引脚
        self.uart = machine.UART(uart_id, baudrate=baudrate, tx=tx_pin, rx=rx_pin)

    def send_command(self, command, timeout=3000):
        """
        发送AT指令并获取响应
        Send AT command and get response

        Args:
            command (str): 要发送的AT指令字符串（不含结束符）
                           AT command string to send (without terminator)
            timeout (int, optional): 响应超时时间，单位毫秒，默认3000ms
                                     Response timeout in milliseconds, default 3000ms

        Returns:
            str: 拼接后的完整响应字符串
                 Concatenated complete response string

        Notes:
            自动为指令添加\r\n结束符，循环读取响应直到超时，所有响应数据解码为字符串后拼接返回
            Automatically add \r\n terminator to command, cycle to read response until timeout, decode all response data to string and return after concatenation
        """
        # 为AT指令添加回车换行结束符
        command += '\r\n'
        # 向UART写入AT指令
        self.uart.write(command)
        # 记录指令发送开始时间戳
        start_time = time.ticks_ms()
        # 初始化响应数据列表
        response = []
        # 循环读取响应直到超时
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            # 判断UART是否有可读取的数据
            if self.uart.any():
                # 读取UART数据并解码为字符串，添加到响应列表
                response.append(self.uart.read().decode())
        # 将响应列表拼接为完整字符串并返回
        return ''.join(response)

    def power_on(self):
        """
        开启模块全功能模式
        Turn on module full function mode

        Args:
            None

        Returns:
            str: AT指令响应字符串
                 AT command response string

        Notes:
            使用AT+CFUN=1指令将模块设置为全功能模式，启用所有射频功能
            Use AT+CFUN=1 command to set module to full function mode, enable all RF functions
        """
        # 发送开启全功能模式指令并返回响应
        return self.send_command('AT+CFUN=1')

    def power_off(self):
        """
        关闭模块电源
        Turn off module power

        Args:
            None

        Returns:
            str: AT指令响应字符串
                 AT command response string

        Notes:
            使用AT+CPOF指令关闭模块电源，模块将进入低功耗关机状态
            Use AT+CPOF command to turn off module power, module will enter low-power shutdown state
        """
        # 发送关闭模块电源指令并返回响应
        return self.send_command('AT+CPOF')

    def reset_module(self):
        """
        重置模块
        Reset module

        Args:
            None

        Returns:
            str: AT指令响应字符串
                 AT command response string

        Notes:
            使用AT+CRESET指令软重置模块，模块会重启并恢复默认配置
            Use AT+CRESET command to soft reset module, module will restart and restore default configuration
        """
        # 发送模块重置指令并返回响应
        return self.send_command('AT+CRESET')

    def set_power_mode(self, mode):
        """
        设置模块功耗模式
        Set module power consumption mode

        Args:
            mode (int): 功耗模式值，0-禁用睡眠/1-轻睡眠/2-深度睡眠
                        Power consumption mode value, 0-disable sleep/1-light sleep/2-deep sleep

        Returns:
            str: AT指令响应字符串
                 AT command response string

        Notes:
            使用AT+CSCLK指令设置模块睡眠模式，不同模式对应不同的功耗水平和响应速度
            Use AT+CSCLK command to set module sleep mode, different modes correspond to different power consumption levels and response speeds
        """
        # 发送设置功耗模式指令并返回响应
        return self.send_command(f'AT+CSCLK={mode}')

    def monitor_voltage(self):
        """
        监控模块电池电压
        Monitor module battery voltage

        Args:
            None

        Returns:
            str: 包含电压信息的AT指令响应字符串
                 AT command response string containing voltage information

        Notes:
            使用AT+CBC指令查询模块电池电压和电量状态，响应格式为:+CBC: <batt_status>,<batt_voltage>,<batt_percent>
            Use AT+CBC command to query module battery voltage and power status, response format: +CBC: <batt_status>,<batt_voltage>,<batt_percent>
        """
        # 发送监控电压指令并返回响应
        return self.send_command('AT+CBC')

    def connect(self, apn, user='', password=''):
        """
        建立GPRS网络连接
        Establish GPRS network connection

        Args:
            apn (str): 接入点名称(Access Point Name)，如"cmnet"、"3gnet"等
                       Access Point Name, such as "cmnet", "3gnet", etc.
            user (str, optional): APN认证用户名，默认为空字符串
                                  APN authentication username, default empty string
            password (str, optional): APN认证密码，默认为空字符串
                                      APN authentication password, default empty string

        Returns:
            str: 包含IP地址的AT指令响应字符串
                 AT command response string containing IP address

        Notes:
            依次执行GPRS附着、设置APN参数、激活PDP上下文、获取IP地址，完成网络连接建立
            Execute GPRS attach, set APN parameters, activate PDP context, get IP address in sequence to complete network connection establishment
        """
        # 执行GPRS网络附着
        self.send_command('AT+CGATT=1')
        # 设置APN参数及认证信息
        self.send_command(f'AT+CSTT="{apn}","{user}","{password}"')
        # 激活PDP上下文
        self.send_command('AT+CIICR')
        # 获取分配的IP地址并返回
        return self.send_command('AT+CIFSR')

    def disconnect(self):
        """
        断开GPRS网络连接
        Disconnect GPRS network connection

        Args:
            None

        Returns:
            str: AT指令响应字符串
                 AT command response string

        Notes:
            使用AT+CGATT=0指令分离GPRS网络，断开所有数据连接
            Use AT+CGATT=0 command to detach from GPRS network and disconnect all data connections
        """
        # 发送断开网络连接指令并返回响应
        return self.send_command('AT+CGATT=0')

    def get_network_status(self):
        """
        获取网络注册状态
        Get network registration status

        Args:
            None

        Returns:
            str: 包含网络注册状态的AT指令响应字符串
                 AT command response string containing network registration status

        Notes:
            使用AT+CREG?指令查询网络注册状态，响应格式为:+CREG: <n>,<stat>，stat=1表示已注册本地网络
            Use AT+CREG? command to query network registration status, response format: +CREG: <n>,<stat>, stat=1 means registered to local network
        """
        # 发送查询网络状态指令并返回响应
        return self.send_command('AT+CREG?')

    def set_flight_mode(self, enable):
        """
        设置飞行模式
        Set flight mode

        Args:
            enable (bool): True-开启飞行模式/False-关闭飞行模式
                           True-enable flight mode/False-disable flight mode

        Returns:
            str: AT指令响应字符串
                 AT command response string

        Notes:
            使用AT+CFUN指令设置飞行模式，enable=True时设置为0（禁用射频），enable=False时设置为1（启用射频）
            Use AT+CFUN command to set flight mode, set to 0 (disable RF) when enable=True, set to 1 (enable RF) when enable=False
        """
        # 发送设置飞行模式指令并返回响应
        return self.send_command(f'AT+CFUN={0 if enable else 1}')

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================