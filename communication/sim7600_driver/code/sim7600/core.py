# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:00
# @Author  : basanovase
# @File    : core.py
# @Description : SIM7600模块基础功能类 实现UART通信、模块启停、网络连接、状态监控等核心基础功能 参考自：https://github.com/basanovase/sim7600
# @License : MIT
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
    Attributes:
        uart (machine.UART): UART通信对象，用于与SIM7600模块进行数据交互

    Methods:
        __init__(uart): 初始化SIM7600模块UART通信
        send_command(command, timeout=3000): 发送AT指令并获取响应
        power_on(): 开启模块全功能模式
        power_off(): 关闭模块电源
        reset_module(): 重置模块
        set_power_mode(mode): 设置模块功耗模式
        monitor_voltage(): 监控模块电池电压
        connect(apn, user='', password=''): 建立GPRS网络连接
        disconnect(): 断开GPRS网络连接
        get_network_status(): 获取网络注册状态
        set_flight_mode(enable): 设置飞行模式
        check_sim_card(): 检查SIM卡是否插入及状态
        check_network_registration(): 检查网络注册状态
        check_network_attach(): 检查网络附着状态
        get_signal_quality(): 检查信号质量

    Notes:
        该类是SIM7600模块所有扩展功能类的基础父类，所有AT指令通信均基于UART串口实现

    ==========================================
    SIM7600 Module Basic Function Class
    Attributes:
        uart (machine.UART): UART communication object for data interaction with SIM7600 module

    Methods:
        __init__(uart): Initialize SIM7600 module UART communication
        send_command(command, timeout=3000): Send AT command and get response
        power_on(): Turn on module full function mode
        power_off(): Turn off module power
        reset_module(): Reset module
        set_power_mode(mode): Set module power consumption mode
        monitor_voltage(): Monitor module battery voltage
        connect(apn, user='', password=''): Establish GPRS network connection
        disconnect(): Disconnect GPRS network connection
        get_network_status(): Get network registration status
        set_flight_mode(enable): Set flight mode
        check_sim_card(): Check if SIM card is inserted and its status
        check_network_registration(): Check network registration status
        check_network_attach(): Check network attach status
        get_signal_quality(): Check signal quality

    Notes:
        This class is the basic parent class of all extended function classes of the SIM7600 module, and all AT command communication is implemented based on UART serial port
    """

    def __init__(self, uart: machine.UART) -> None:
        """
        初始化SIM7600模块UART通信
        Args:
            uart (machine.UART): UART通信对象，需预先配置好波特率、引脚等参数

        Raises:
            TypeError: 当uart参数为None时触发
            TypeError: 当uart参数非machine.UART类型时触发

        Notes:
            根据指定的UART对象建立与SIM7600模块的物理连接，UART对象需提前完成初始化配置

        ==========================================
        Initialize SIM7600 module UART communication
        Args:
            uart (machine.UART): UART communication object, need to pre-configure baud rate, pins and other parameters

        Raises:
            TypeError: Triggered when uart parameter is None
            TypeError: Triggered when uart parameter is not machine.UART type

        Notes:
            Establish physical connection with SIM7600 module according to the specified UART object, the UART object needs to complete initialization configuration in advance
        """
        # 检查uart参数是否为None
        if uart is None:
            raise TypeError("uart parameter cannot be None")
        # 检查uart参数类型是否为machine.UART
        if not isinstance(uart, machine.UART):
            raise TypeError(f"Expected uart type machine.UART, got {type(uart).__name__} instead")
        # 初始化UART通信对象，配置波特率、发送引脚、接收引脚
        self.uart = uart

    def send_command(self, command: str, timeout: int = 3000) -> str:
        """
        发送AT指令并获取响应
        Args:
            command (str): 要发送的AT指令字符串（不含结束符）
            timeout (int, optional): 响应超时时间，单位毫秒，默认3000ms

        Raises:
            TypeError: 当command参数非字符串类型时触发
            ValueError: 当command参数为空字符串时触发
            TypeError: 当timeout参数非整数类型时触发
            ValueError: 当timeout参数小于等于0时触发

        Notes:
            自动为指令添加\r\n结束符，循环读取响应直到超时，所有响应数据解码为字符串后拼接返回

        ==========================================
        Send AT command and get response
        Args:
            command (str): AT command string to send (without terminator)
            timeout (int, optional): Response timeout in milliseconds, default 3000ms

        Raises:
            TypeError: Triggered when command parameter is not string type
            ValueError: Triggered when command parameter is empty string
            TypeError: Triggered when timeout parameter is not integer type
            ValueError: Triggered when timeout parameter is less than or equal to 0

        Notes:
            Automatically add \r\n terminator to command, cycle to read response until timeout, decode all response data to string and return after concatenation
        """
        # 检查command参数类型和有效性
        if not isinstance(command, str):
            raise TypeError("command parameter must be string type")
        if len(command.strip()) == 0:
            raise ValueError("command parameter cannot be empty string")
        # 检查timeout参数类型和有效性
        if not isinstance(timeout, int):
            raise TypeError("timeout parameter must be integer type")
        if timeout <= 0:
            raise ValueError("timeout parameter must be greater than 0")
        # 为AT指令添加回车换行结束符
        command += "\r\n"
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
        return "".join(response)

    def check_sim_card(self) -> str:
        """
        检查SIM卡是否插入及状态
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CPIN?指令查询SIM卡状态
            响应示例: +CPIN: READY（已就绪）, +CPIN: SIM PIN（需要PIN码）等

        ==========================================
        Check if SIM card is inserted and its status
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CPIN? command to query SIM card status
            Response example: +CPIN: READY (ready), +CPIN: SIM PIN (PIN code required), etc.
        """
        return self.send_command("AT+CPIN?")

    def check_network_registration(self) -> str:
        """
        检查网络注册状态
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CEREG?指令查询网络注册状态
            响应格式: +CEREG: <n>,<stat>[,<lac>,<ci>[,<AcT>]]
            <stat>取值: 0=未注册, 1=已注册本地网, 2=正在搜索, 3=注册被拒, 4=未知, 5=已注册漫游网

        ==========================================
        Check network registration status
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CEREG? command to query network registration status
            Response format: +CEREG: <n>,<stat>[,<lac>,<ci>[,<AcT>]]
            <stat> values: 0=not registered, 1=registered to local network, 2=searching, 3=registration rejected, 4=unknown, 5=registered to roaming network
        """
        return self.send_command("AT+CEREG?")

    def check_network_attach(self) -> str:
        """
        检查网络附着状态
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGATT?指令查询PS域附着状态
            响应示例: +CGATT: 1（已附着）, +CGATT: 0（未附着）

        ==========================================
        Check network attach status
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGATT? command to query PS domain attach status
            Response example: +CGATT: 1 (attached), +CGATT: 0 (not attached)
        """
        return self.send_command("AT+CGATT?")

    def get_signal_quality(self) -> str:
        """
        检查信号质量
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CSQ指令查询信号质量，响应格式: +CSQ: <rssi>,<ber>
            <rssi> 范围0-31（31为最佳），99表示无信号；<ber>为误码率

        ==========================================
        Check signal quality
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CSQ command to query signal quality, response format: +CSQ: <rssi>,<ber>
            <rssi> range 0-31 (31 is best), 99 means no signal; <ber> is bit error rate
        """
        return self.send_command("AT+CSQ")

    def power_on(self) -> str:
        """
        开启模块全功能模式
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CFUN=1指令将模块设置为全功能模式，启用所有射频功能

        ==========================================
        Turn on module full function mode
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CFUN=1 command to set module to full function mode, enable all RF functions
        """
        # 发送开启全功能模式指令并返回响应
        return self.send_command("AT+CFUN=1")

    def power_off(self) -> str:
        """
        关闭模块电源
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CPOF指令关闭模块电源，模块将进入低功耗关机状态

        ==========================================
        Turn off module power
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CPOF command to turn off module power, module will enter low-power shutdown state
        """
        # 发送关闭模块电源指令并返回响应
        return self.send_command("AT+CPOF")

    def reset_module(self) -> str:
        """
        重置模块
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CRESET指令软重置模块，模块会重启并恢复默认配置

        ==========================================
        Reset module
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CRESET command to soft reset module, module will restart and restore default configuration
        """
        # 发送模块重置指令并返回响应
        return self.send_command("AT+CRESET")

    def set_power_mode(self, mode: int) -> str:
        """
        设置模块功耗模式
        Args:
            mode (int): 功耗模式值，0-禁用睡眠/1-轻睡眠/2-深度睡眠

        Raises:
            TypeError: 当mode参数非整数类型时触发
            ValueError: 当mode参数不在0-2范围内时触发

        Notes:
            使用AT+CSCLK指令设置模块睡眠模式，不同模式对应不同的功耗水平和响应速度

        ==========================================
        Set module power consumption mode
        Args:
            mode (int): Power consumption mode value, 0-disable sleep/1-light sleep/2-deep sleep

        Raises:
            TypeError: Triggered when mode parameter is not integer type
            ValueError: Triggered when mode parameter is not in the range of 0-2

        Notes:
            Use AT+CSCLK command to set module sleep mode, different modes correspond to different power consumption levels and response speeds
        """
        # 检查mode参数类型和范围
        if not isinstance(mode, int):
            raise TypeError("mode parameter must be integer type")
        if mode < 0 or mode > 2:
            raise ValueError("mode parameter must be 0, 1 or 2")
        # 发送设置功耗模式指令并返回响应
        return self.send_command(f"AT+CSCLK={mode}")

    def monitor_voltage(self) -> str:
        """
        监控模块电池电压
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CBC指令查询模块电池电压和电量状态，响应格式为:+CBC: <batt_status>,<batt_voltage>,<batt_percent>

        ==========================================
        Monitor module battery voltage
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CBC command to query module battery voltage and power status, response format: +CBC: <batt_status>,<batt_voltage>,<batt_percent>
        """
        # 发送监控电压指令并返回响应
        return self.send_command("AT+CBC")

    def connect(self, apn: str, user: str = "", password: str = "") -> str:
        """
        建立GPRS网络连接
        Args:
            apn (str): 接入点名称(Access Point Name)，如"cmnet"、"3gnet"等
            user (str, optional): APN认证用户名，默认为空字符串
            password (str, optional): APN认证密码，默认为空字符串

        Raises:
            TypeError: 当apn、user或password参数非字符串类型时触发
            ValueError: 当apn参数为空字符串时触发

        Notes:
            依次执行GPRS附着、设置APN参数、激活PDP上下文、获取IP地址，完成网络连接建立

        ==========================================
        Establish GPRS network connection
        Args:
            apn (str): Access Point Name, such as "cmnet", "3gnet", etc.
            user (str, optional): APN authentication username, default empty string
            password (str, optional): APN authentication password, default empty string

        Raises:
            TypeError: Triggered when apn, user or password parameter is not string type
            ValueError: Triggered when apn parameter is empty string

        Notes:
            Execute GPRS attach, set APN parameters, activate PDP context, get IP address in sequence to complete network connection establishment
        """
        # 检查apn参数类型和有效性
        if not isinstance(apn, str):
            raise TypeError("apn parameter must be string type")
        if len(apn.strip()) == 0:
            raise ValueError("apn parameter cannot be empty string")
        # 检查user和password参数类型
        if not isinstance(user, str):
            raise TypeError("user parameter must be string type")
        if not isinstance(password, str):
            raise TypeError("password parameter must be string type")
        # 执行GPRS网络附着
        self.send_command("AT+CGATT=1")
        # 设置APN参数及认证信息
        self.send_command(f'AT+CSTT="{apn}","{user}","{password}"')
        # 激活PDP上下文
        self.send_command("AT+CIICR")
        # 获取分配的IP地址并返回
        return self.send_command("AT+CIFSR")

    def disconnect(self) -> str:
        """
        断开GPRS网络连接
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGATT=0指令分离GPRS网络，断开所有数据连接

        ==========================================
        Disconnect GPRS network connection
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGATT=0 command to detach from GPRS network and disconnect all data connections
        """
        # 发送断开网络连接指令并返回响应
        return self.send_command("AT+CGATT=0")

    def get_network_status(self) -> str:
        """
        获取网络注册状态
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CREG?指令查询网络注册状态，响应格式为:+CREG: <n>,<stat>，stat=1表示已注册本地网络

        ==========================================
        Get network registration status
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CREG? command to query network registration status, response format: +CREG: <n>,<stat>, stat=1 means registered to local network
        """
        # 发送查询网络状态指令并返回响应
        return self.send_command("AT+CREG?")

    def set_flight_mode(self, enable: bool) -> str:
        """
        设置飞行模式
        Args:
            enable (bool): True-开启飞行模式/False-关闭飞行模式

        Raises:
            TypeError: 当enable参数非布尔类型时触发

        Notes:
            使用AT+CFUN指令设置飞行模式，enable=True时设置为0（禁用射频），enable=False时设置为1（启用射频）

        ==========================================
        Set flight mode
        Args:
            enable (bool): True-enable flight mode/False-disable flight mode

        Raises:
            TypeError: Triggered when enable parameter is not boolean type

        Notes:
            Use AT+CFUN command to set flight mode, set to 0 (disable RF) when enable=True, set to 1 (enable RF) when enable=False
        """
        # 检查enable参数类型
        if not isinstance(enable, bool):
            raise TypeError("enable parameter must be boolean type")
        # 发送设置飞行模式指令并返回响应
        return self.send_command(f"AT+CFUN={0 if enable else 1}")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
