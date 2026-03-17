# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午6:00
# @Author  : basanovase
# @File    : core.py
# @Description : SIM800模块驱动 实现基础AT指令通信、拨号、挂断、获取网络时间等功能 参考自:https://github.com/basanovase/sim800
# @License : MIT

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入machine模块，用于硬件外设控制
import machine

# 导入utime模块，用于时间相关操作
import utime


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class SIM800:
    """
    SIM800模块驱动类
    实现SIM800模块的基础AT指令通信、拨号、挂断、信号质量查询、网络时间获取等核心功能
    Attributes:
        uart (machine.UART): UART通信对象，用于与SIM800模块通信
                             UART communication object for communicating with SIM800 module

    Methods:
        __init__(uart): 初始化SIM800模块UART通信对象并执行基础配置
                        Initialize SIM800 module UART communication object and execute basic configuration
        send_command(command, timeout=1000): 发送AT指令并获取模块响应
                                             Send AT command and get module response
        read_response(timeout=1000): 非阻塞式读取UART总线上的模块响应数据
                                     Read module response data on UART bus in non-blocking mode
        initialize(): 初始化SIM800模块基础配置（关闭回显、设置全功能模式等）
                      Initialize SIM800 module basic configuration (turn off echo, set full function mode, etc.)
        get_signal_quality(): 获取模块信号质量（RSSI/误码率）
                              Get module signal quality (RSSI/bit error rate)
        get_phone_number(): 获取SIM卡中存储的电话号码
                            Get phone number stored in SIM card
        get_manufacturer(): 获取模块制造商信息
                            Get module manufacturer information
        get_serial_number(): 获取模块序列号（IMEI/MEID/ESN）
                            Get module serial number (IMEI/MEID/ESN)
        reset(): 软件重置SIM800模块
                 Reset SIM800 module via software command
        dial_number(number): 拨打指定电话号码
                             Dial the specified phone number
        hang_up(): 挂断当前通话
                   Hang up the current call
        get_network_time(): 获取网络时间并解析为结构化字典数据
                            Get network time and parse to structured dictionary data

    Notes:
        1. 所有AT指令通信基于UART异步传输，默认波特率115200
        2. 网络时间解析失败时返回None，需做异常处理
        3. 拨号指令需在号码末尾添加分号，否则会进入语音拨号模式

    ==========================================
    SIM800 Module Driver Class
    Implement core functions of SIM800 module such as basic AT command communication, dialing, hanging up, signal quality query, network time acquisition, etc.
    Attributes:
        uart (machine.UART): UART communication object for communicating with SIM800 module

    Methods:
        __init__(uart): Initialize SIM800 module UART communication object and execute basic configuration
        send_command(command, timeout=1000): Send AT command and get module response
        read_response(timeout=1000): Read module response data on UART bus in non-blocking mode
        initialize(): Initialize SIM800 module basic configuration (turn off echo, set full function mode, etc.)
        get_signal_quality(): Get module signal quality (RSSI/bit error rate)
        get_phone_number(): Get phone number stored in SIM card
        get_manufacturer(): Get module manufacturer information
        get_serial_number(): Get module serial number (IMEI/MEID/ESN)
        reset(): Reset SIM800 module via software command
        dial_number(number): Dial the specified phone number
        hang_up(): Hang up the current call
        get_network_time(): Get network time and parse to structured dictionary data

    Notes:
        1. All AT command communication is based on UART asynchronous transmission, default baud rate is 115200
        2. Return None when network time parsing fails, exception handling is required
        3. The dial command needs to add a semicolon at the end of the number, otherwise it will enter voice dialing mode
    """

    def __init__(self, uart: machine.UART) -> None:
        """
        初始化SIM800模块
        验证UART参数有效性并创建通信对象，自动调用initialize()完成模块基础配置
        Args:
            uart (machine.UART): UART通信对象，需预先初始化（指定端口、波特率等）
                                 UART communication object, need to be initialized in advance (specify port, baud rate, etc.)

        Raises:
            TypeError: 当uart参数为None或非machine.UART实例时触发
                       Triggered when uart parameter is None or not an instance of machine.UART

        Notes:
            初始化时会自动调用initialize()方法进行模块基础配置
            The initialize() method is automatically called for module basic configuration during initialization

        ==========================================
        Initialize SIM800 module
        Verify UART parameter validity and create communication object, automatically call initialize() to complete module basic configuration
        Args:
            uart (machine.UART): UART communication object, need to be initialized in advance (specify port, baud rate, etc.)

        Raises:
            TypeError: Triggered when uart parameter is None or not an instance of machine.UART

        Notes:
            The initialize() method is automatically called for module basic configuration during initialization
        """
        # 验证uart参数是否为None
        if uart is None:
            raise TypeError("uart parameter cannot be None, must be machine.UART instance")
        # 验证uart参数类型是否为machine.UART实例
        if not isinstance(uart, machine.UART):
            raise TypeError(f"Expected uart type machine.UART, got {type(uart).__name__} instead")

        # 创建UART通信对象
        self.uart = uart
        # 调用初始化方法配置模块
        self.initialize()

    def send_command(self, command: str, timeout: int = 1000) -> bytes:
        """
        发送AT指令并获取响应
        自动为指令添加回车符，等待模块响应后读取并返回UART总线上的响应数据
        Args:
            command (str): 要发送的AT指令字符串（不含回车符）
                           AT command string to send (without carriage return)
            timeout (int, optional): 响应读取超时时间，单位毫秒，默认1000ms
                                     Response read timeout in milliseconds, default 1000ms

        Raises:
            TypeError: 当command参数为None或非字符串类型时触发
                       Triggered when command parameter is None or not a string type
            ValueError: 当timeout参数小于0时触发
                        Triggered when timeout parameter is less than 0

        Returns:
            bytes: UART总线上读取到的响应数据
                   Response data read on UART bus

        Notes:
            发送指令时会自动添加回车符\r
            A carriage return \r is automatically added when sending the command

        ==========================================
        Send AT command and get response
        Automatically add carriage return to the command, wait for module response then read and return response data on UART bus
        Args:
            command (str): AT command string to send (without carriage return)
            timeout (int, optional): Response read timeout in milliseconds, default 1000ms

        Raises:
            TypeError: Triggered when command parameter is None or not a string type
            ValueError: Triggered when timeout parameter is less than 0

        Returns:
            bytes: Response data read on UART bus

        Notes:
            A carriage return \r is automatically added when sending the command
        """
        # 验证command参数是否为None
        if command is None:
            raise TypeError("command parameter cannot be None, must be string")
        # 验证command参数类型是否为字符串
        if not isinstance(command, str):
            raise TypeError(f"Expected command type str, got {type(command).__name__} instead")
        # 验证timeout参数是否为非负整数
        if not isinstance(timeout, int):
            raise TypeError(f"Expected timeout type int, got {type(timeout).__name__} instead")
        if timeout < 0:
            raise ValueError(f"timeout must be non-negative integer, got {timeout}")

        # 发送AT指令，末尾添加回车符
        self.uart.write(command + "\r")
        # 短暂延时，等待模块响应
        utime.sleep_ms(100)
        # 读取并返回响应数据
        return self.read_response(timeout)

    def read_response(self, timeout: int = 1000) -> bytes:
        """
        读取UART总线上的响应数据
        非阻塞式循环读取UART缓冲区数据，直到超时或无新数据可读
        Args:
            timeout (int, optional): 读取超时时间，单位毫秒，默认1000ms
                                     Read timeout in milliseconds, default 1000ms

        Raises:
            TypeError: 当timeout参数非整数类型时触发
                       Triggered when timeout parameter is not an integer type
            ValueError: 当timeout参数小于0时触发
                        Triggered when timeout parameter is less than 0

        Returns:
            bytes: 读取到的响应数据，如果超时返回空字节串
                   Read response data, empty bytes if timeout

        Notes:
            采用非阻塞方式读取，持续检测UART缓冲区直到超时
            Read in non-blocking mode, continuously check UART buffer until timeout

        ==========================================
        Read response data on UART bus
        Read UART buffer data in non-blocking loop until timeout or no new data to read
        Args:
            timeout (int, optional): Read timeout in milliseconds, default 1000ms

        Raises:
            TypeError: Triggered when timeout parameter is not an integer type
            ValueError: Triggered when timeout parameter is less than 0

        Returns:
            bytes: Read response data, empty bytes if timeout

        Notes:
            Read in non-blocking mode, continuously check UART buffer until timeout
        """
        # 验证timeout参数类型是否为整数
        if not isinstance(timeout, int):
            raise TypeError(f"Expected timeout type int, got {type(timeout).__name__} instead")
        # 验证timeout参数是否为非负整数
        if timeout < 0:
            raise ValueError(f"timeout must be non-negative integer, got {timeout}")

        # 记录开始时间
        start_time = utime.ticks_ms()
        # 初始化响应数据缓冲区
        response = b""
        # 循环读取直到超时
        while utime.ticks_diff(utime.ticks_ms(), start_time) < timeout:
            # 检查UART是否有可用数据
            if self.uart.any():
                # 读取所有可用数据并追加到缓冲区
                response += self.uart.read(self.uart.any())
        # 返回读取到的响应数据
        return response

    def initialize(self) -> None:
        """
        初始化SIM800模块基础配置
        依次发送测试指令、关闭回显指令、全功能模式指令，完成模块基础初始化
        Args:
            None

        Returns:
            None

        Notes:
            依次发送AT(测试连通性)、ATE0(关闭回显)、AT+CFUN=1(设置全功能模式)指令
            Send AT (test connectivity), ATE0 (turn off echo), AT+CFUN=1 (set full function mode) commands in sequence

        ==========================================
        Initialize SIM800 module basic configuration
        Send test command, echo off command, full function mode command in sequence to complete module basic initialization
        Args:
            None

        Returns:
            None

        Notes:
            Send AT (test connectivity), ATE0 (turn off echo), AT+CFUN=1 (set full function mode) commands in sequence
        """
        # 发送AT指令测试模块连通性
        self.send_command("AT")
        # 发送ATE0指令关闭回显
        self.send_command("ATE0")
        # 发送AT+CFUN=1指令设置模块为全功能模式
        self.send_command("AT+CFUN=1")

    def get_signal_quality(self) -> bytes:
        """
        获取SIM800模块的信号质量
        发送AT+CSQ指令查询信号强度(RSSI)和误码率(BER)，返回原始响应数据
        Args:
            None

        Returns:
            bytes: 信号质量查询指令的响应数据
                   Response data of signal quality query command

        Notes:
            使用AT+CSQ指令查询信号质量，响应格式通常为: +CSQ: <rssi>,<ber>
            <rssi>范围0-31(31为最好)，99表示无信号；<ber>为误码率，99表示未知
            Use AT+CSQ command to query signal quality, response format: +CSQ: <rssi>,<ber>
            <rssi> range 0-31 (31 is best), 99 means no signal; <ber> is bit error rate, 99 means unknown

        ==========================================
        Get signal quality of SIM800 module
        Send AT+CSQ command to query signal strength (RSSI) and bit error rate (BER), return original response data
        Args:
            None

        Returns:
            bytes: Response data of signal quality query command

        Notes:
            Use AT+CSQ command to query signal quality, response format: +CSQ: <rssi>,<ber>
            <rssi> range 0-31 (31 is best), 99 means no signal; <ber> is bit error rate, 99 means unknown
        """
        # 发送信号质量查询指令并返回响应
        return self.send_command("AT+CSQ")

    def get_phone_number(self) -> bytes:
        """
        获取SIM卡存储的电话号码
        发送AT+CNUM指令查询SIM卡中存储的MSISDN号码，返回原始响应数据
        Args:
            None

        Returns:
            bytes: 号码查询指令的响应数据
                   Response data of phone number query command

        Notes:
            使用AT+CNUM指令查询SIM卡中存储的MSISDN号码
            响应包含号码类型和对应的电话号码
            Use AT+CNUM command to query MSISDN number stored in SIM card
            Response includes number type and corresponding phone number

        ==========================================
        Get phone number stored in SIM card
        Send AT+CNUM command to query MSISDN number stored in SIM card, return original response data
        Args:
            None

        Returns:
            bytes: Response data of phone number query command

        Notes:
            Use AT+CNUM command to query MSISDN number stored in SIM card
            Response includes number type and corresponding phone number
        """
        # 发送号码查询指令并返回响应
        return self.send_command("AT+CNUM")

    def get_manufacturer(self) -> bytes:
        """
        获取模块制造商信息
        发送AT+CGMI指令查询模块制造商标识，返回原始响应数据
        Args:
            None

        Returns:
            bytes: 制造商查询指令的响应数据
                   Response data of manufacturer query command

        Notes:
            使用AT+CGMI指令查询模块制造商标识
            通常返回模块生产厂商名称(如SIMCOM)
            Use AT+CGMI command to query module manufacturer identity
            Usually returns module manufacturer name (e.g. SIMCOM)

        ==========================================
        Get module manufacturer information
        Send AT+CGMI command to query module manufacturer identity, return original response data
        Args:
            None

        Returns:
            bytes: Response data of manufacturer query command

        Notes:
            Use AT+CGMI command to query module manufacturer identity
            Usually returns module manufacturer name (e.g. SIMCOM)
        """
        # 发送制造商查询指令并返回响应
        return self.send_command("AT+CGMI")

    def get_serial_number(self) -> bytes:
        """
        获取模块序列号
        发送AT+CGSN指令查询模块的IMEI/MEID/ESN等序列号信息，返回原始响应数据
        Args:
            None

        Returns:
            bytes: 序列号查询指令的响应数据
                   Response data of serial number query command

        Notes:
            使用AT+CGSN指令查询模块的IMEI/MEID/ESN等序列号信息
            对于GSM模块，通常返回15位的IMEI号码
            Use AT+CGSN command to query module serial number (IMEI/MEID/ESN)
            For GSM modules, usually returns 15-digit IMEI number

        ==========================================
        Get module serial number
        Send AT+CGSN command to query module serial number (IMEI/MEID/ESN), return original response data
        Args:
            None

        Returns:
            bytes: Response data of serial number query command

        Notes:
            Use AT+CGSN command to query module serial number (IMEI/MEID/ESN)
            For GSM modules, usually returns 15-digit IMEI number
        """
        # 发送序列号查询指令并返回响应
        return self.send_command("AT+CGSN")

    def reset(self) -> bytes:
        """
        重置SIM800模块
        发送AT+CFUN=1,1软件重置指令，返回模块重置响应数据
        Args:
            None

        Returns:
            bytes: 模块重置指令的响应数据
                   Response data of module reset command

        Notes:
            使用AT+CFUN=1,1指令进行软件重置
            Use AT+CFUN=1,1 command for software reset

        ==========================================
        Reset SIM800 module
        Send AT+CFUN=1,1 software reset command, return module reset response data
        Args:
            None

        Returns:
            bytes: Response data of module reset command

        Notes:
            Use AT+CFUN=1,1 command for software reset
        """
        # 发送重置指令并返回响应
        return self.send_command("AT+CFUN=1,1")

    def dial_number(self, number: str) -> bytes:
        """
        拨打指定电话号码
        拼接ATD指令并发送，号码末尾自动添加分号以进入普通拨号模式
        Args:
            number (str): 要拨打的电话号码（数字字符串）
                          Phone number to dial (numeric string)

        Raises:
            TypeError: 当number参数为None或非字符串类型时触发
                       Triggered when number parameter is None or not a string type
            ValueError: 当number参数为空字符串时触发
                        Triggered when number parameter is an empty string

        Returns:
            bytes: 拨号指令的响应数据
                   Response data of dial command

        Notes:
            使用ATD指令进行拨号，号码末尾必须加分号;
            Use ATD command for dialing, number must end with semicolon ;

        ==========================================
        Dial the specified phone number
        Splice and send ATD command, automatically add semicolon at the end of number to enter normal dial mode
        Args:
            number (str): Phone number to dial (numeric string)

        Raises:
            TypeError: Triggered when number parameter is None or not a string type
            ValueError: Triggered when number parameter is an empty string

        Returns:
            bytes: Response data of dial command

        Notes:
            Use ATD command for dialing, number must end with semicolon ;
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

        # 发送拨号指令并返回响应
        return self.send_command(f"ATD{number};")

    def hang_up(self) -> bytes:
        """
        挂断当前通话
        发送ATH指令挂断正在进行的通话，返回指令响应数据
        Args:
            None

        Returns:
            bytes: 挂断指令的响应数据
                   Response data of hang up command

        Notes:
            使用ATH指令挂断通话
            Use ATH command to hang up the call

        ==========================================
        Hang up the current call
        Send ATH command to hang up ongoing call, return command response data
        Args:
            None

        Returns:
            bytes: Response data of hang up command

        Notes:
            Use ATH command to hang up the call
        """
        # 发送挂断指令并返回响应
        return self.send_command("ATH")

    def get_network_time(self) -> dict | None:
        """
        获取网络时间并解析为结构化数据
        发送AT+CCLK?指令获取网络时间字符串，解析为包含年月日时分秒时区的字典
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

        ==========================================
        Get network time and parse to structured data
        Send AT+CCLK? command to get network time string, parse to dictionary containing year, month, day, hour, minute, second and timezone
        Args:
            None

        Returns:
            dict or None: Parsed time dictionary in format {'year':2025, 'month':9, 'day':8, 'hour':18, 'minute':0, 'second':0, 'timezone':'+08'}
                          Return None if parsing fails

        Notes:
            Use AT+CCLK? command to get network time, response format example: +CCLK: "25/09/08,18:00:00+08"
        """
        # 发送获取网络时间指令并获取响应
        response = self.send_command("AT+CCLK?")
        # 将字节串响应转换为字符串
        response_str = response.decode("utf-8") if isinstance(response, bytes) else response

        # 检查响应中是否包含时间数据
        if "+CCLK:" in response_str:
            try:
                # 提取时间字符串部分
                time_str = response_str.split("+CCLK:")[1].split('"')[1]
                # 分割日期和时间部分
                date_part, time_part = time_str.split(",")
                # 解析年月日
                year, month, day = date_part.split("/")

                # 处理时区信息
                if "+" in time_part:
                    # 分离时间和时区(+)
                    time_only, tz = time_part.split("+")
                    tz = "+" + tz
                elif "-" in time_part[2:]:
                    # 分离时间和时区(-)
                    idx = time_part.rfind("-")
                    time_only = time_part[:idx]
                    tz = time_part[idx:]
                else:
                    # 无时区信息时使用默认值
                    time_only = time_part
                    tz = "+00"

                # 解析时分秒
                hour, minute, second = time_only.split(":")

                # 返回结构化的时间数据
                return {
                    "year": int(year) + 2000,
                    "month": int(month),
                    "day": int(day),
                    "hour": int(hour),
                    "minute": int(minute),
                    "second": int(second),
                    "timezone": tz,
                }
            except (IndexError, ValueError):
                # 解析失败返回None
                return None
        # 无时间数据返回None
        return None


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
