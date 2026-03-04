# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午6:00
# @Author  : hogeiha
# @File    : sim800.py
# @Description : SIM800模块驱动 实现基础AT指令通信、拨号、挂断、获取网络时间等功能
# @License : MIT
# @Platform: MicroPython v1.23.0

# ======================================== 导入相关模块 =========================================
# 导入machine模块，用于硬件外设控制
import machine
# 导入utime模块，用于时间相关操作
import utime

# ======================================== 全局变量 ============================================
# 模块版本号
__version__ = "1.0.0"
# 模块作者
__author__ = "hogeiha"
# 开源许可证
__license__ = "MIT"
# 运行平台
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class SIM800:
    """
    SIM800模块驱动类
    SIM800 Module Driver Class
    
    Attributes:
        uart (machine.UART): UART通信对象，用于与SIM800模块通信
                             UART communication object for communicating with SIM800 module
        baud (int): UART波特率，默认115200
                    UART baud rate, default 115200
    
    Methods:
        __init__(uart_pin, baud=115200): 初始化SIM800模块
                                         Initialize SIM800 module
        send_command(command, timeout=1000): 发送AT指令并获取响应
                                             Send AT command and get response
        read_response(timeout=1000): 读取UART总线上的响应数据
                                     Read response data on UART bus
        initialize(): 初始化SIM800模块基础配置
                      Initialize SIM800 module basic configuration
        reset(): 重置SIM800模块
                 Reset SIM800 module
        dial_number(number): 拨打指定电话号码
                             Dial the specified phone number
        hang_up(): 挂断当前通话
                   Hang up the current call
        get_network_time(): 获取网络时间并解析为结构化数据
                            Get network time and parse to structured data
    """
    
    def __init__(self, uart_pin, baud=115200):
        """
        初始化SIM800模块
        Initialize SIM800 module
        
        Args:
            uart_pin (int): UART端口号，例如0、1、2
                            UART port number, e.g. 0, 1, 2
            baud (int, optional): UART通信波特率，默认115200
                                  UART communication baud rate, default 115200
        
        Returns:
            None
        
        Notes:
            初始化时会自动调用initialize()方法进行模块基础配置
            The initialize() method is automatically called for module basic configuration during initialization
        """
        # 创建UART通信对象
        self.uart = machine.UART(uart_pin, baudrate=baud)
        # 调用初始化方法配置模块
        self.initialize()

    def send_command(self, command, timeout=1000):
        """
        发送AT指令并获取响应
        Send AT command and get response
        
        Args:
            command (str): 要发送的AT指令字符串（不含回车符）
                           AT command string to send (without carriage return)
            timeout (int, optional): 响应读取超时时间，单位毫秒，默认1000ms
                                     Response read timeout in milliseconds, default 1000ms
        
        Returns:
            bytes: UART总线上读取到的响应数据
                   Response data read on UART bus
        
        Notes:
            发送指令时会自动添加回车符\r
            A carriage return \r is automatically added when sending the command
        """
        # 发送AT指令，末尾添加回车符
        self.uart.write(command + '\r')
        # 短暂延时，等待模块响应
        utime.sleep_ms(100)  
        # 读取并返回响应数据
        return self.read_response(timeout)

    def read_response(self, timeout=1000):
        """
        读取UART总线上的响应数据
        Read response data on UART bus
        
        Args:
            timeout (int, optional): 读取超时时间，单位毫秒，默认1000ms
                                     Read timeout in milliseconds, default 1000ms
        
        Returns:
            bytes: 读取到的响应数据，如果超时返回空字节串
                   Read response data, empty bytes if timeout
        
        Notes:
            采用非阻塞方式读取，持续检测UART缓冲区直到超时
            Read in non-blocking mode, continuously check UART buffer until timeout
        """
        # 记录开始时间
        start_time = utime.ticks_ms()
        # 初始化响应数据缓冲区
        response = b''
        # 循环读取直到超时
        while (utime.ticks_diff(utime.ticks_ms(), start_time) < timeout):
            # 检查UART是否有可用数据
            if self.uart.any():
                # 读取所有可用数据并追加到缓冲区
                response += self.uart.read(self.uart.any())
        # 返回读取到的响应数据
        return response

    def initialize(self):
        """
        初始化SIM800模块基础配置
        Initialize SIM800 module basic configuration
        
        Args:
            None
        
        Returns:
            None
        
        Notes:
            依次发送AT(测试连通性)、ATE0(关闭回显)、AT+CFUN=1(设置全功能模式)指令
            Send AT (test connectivity), ATE0 (turn off echo), AT+CFUN=1 (set full function mode) commands in sequence
        """
        # 发送AT指令测试模块连通性
        self.send_command('AT')  
        # 发送ATE0指令关闭回显
        self.send_command('ATE0')  
        # 发送AT+CFUN=1指令设置模块为全功能模式
        self.send_command('AT+CFUN=1')  

    def reset(self):
        """
        重置SIM800模块
        Reset SIM800 module
        
        Args:
            None
        
        Returns:
            bytes: 模块重置指令的响应数据
                   Response data of module reset command
        
        Notes:
            使用AT+CFUN=1,1指令进行软件重置
            Use AT+CFUN=1,1 command for software reset
        """
        # 发送重置指令并返回响应
        return self.send_command('AT+CFUN=1,1')  

    def dial_number(self, number):
        """
        拨打指定电话号码
        Dial the specified phone number
        
        Args:
            number (str): 要拨打的电话号码
                          Phone number to dial
        
        Returns:
            bytes: 拨号指令的响应数据
                   Response data of dial command
        
        Notes:
            使用ATD指令进行拨号，号码末尾必须加分号;
            Use ATD command for dialing, number must end with semicolon ;
        """
        # 发送拨号指令并返回响应
        return self.send_command(f'ATD{number};')

    def hang_up(self):
        """
        挂断当前通话
        Hang up the current call
        
        Args:
            None
        
        Returns:
            bytes: 挂断指令的响应数据
                   Response data of hang up command
        
        Notes:
            使用ATH指令挂断通话
            Use ATH command to hang up the call
        """
        # 发送挂断指令并返回响应
        return self.send_command('ATH')

    def get_network_time(self):
        """
        获取网络时间并解析为结构化数据
        Get network time and parse to structured data
        
        Args:
            None
        
        Returns:
            dict or None: 解析后的时间字典，格式为{'year':2025, 'month':9, 'day':8, 'hour':18, 'minute':0, 'second':0, 'timezone':'+08'}
                          Parsed time dictionary in format {'year':2025, 'month':9, 'day':8, 'hour':18, 'minute':0, 'second':0, 'timezone':'+08'}
                          解析失败返回None
                          Return None if parsing fails
        
        Notes:
            使用AT+CCLK?指令获取网络时间，响应格式示例: +CCLK: "25/09/08,18:00:00+08"
            Use AT+CCLK? command to get network time, response format example: +CCLK: "25/09/08,18:00:00+08"
        """
        # 发送获取网络时间指令并获取响应
        response = self.send_command('AT+CCLK?')
        # 将字节串响应转换为字符串
        response_str = response.decode('utf-8') if isinstance(response, bytes) else response

        # 检查响应中是否包含时间数据
        if '+CCLK:' in response_str:
            try:
                # 提取时间字符串部分
                time_str = response_str.split('+CCLK:')[1].split('"')[1]
                # 分割日期和时间部分
                date_part, time_part = time_str.split(',')
                # 解析年月日
                year, month, day = date_part.split('/')

                # 处理时区信息
                if '+' in time_part:
                    # 分离时间和时区(+)
                    time_only, tz = time_part.split('+')
                    tz = '+' + tz
                elif '-' in time_part[2:]:  
                    # 分离时间和时区(-)
                    idx = time_part.rfind('-')
                    time_only = time_part[:idx]
                    tz = time_part[idx:]
                else:
                    # 无时区信息时使用默认值
                    time_only = time_part
                    tz = '+00'

                # 解析时分秒
                hour, minute, second = time_only.split(':')

                # 返回结构化的时间数据
                return {
                    'year': int(year) + 2000,
                    'month': int(month),
                    'day': int(day),
                    'hour': int(hour),
                    'minute': int(minute),
                    'second': int(second),
                    'timezone': tz
                }
            except (IndexError, ValueError):
                # 解析失败返回None
                return None
        # 无时间数据返回None
        return None

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================