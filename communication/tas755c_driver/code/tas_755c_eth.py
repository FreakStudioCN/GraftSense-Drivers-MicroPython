# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/11 下午10:12
# @Author  : ben0i0d
# @File    : tas755.py
# @Description : tas755驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC YB-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from time import ticks_diff
from machine import Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class TAS_755C_ETH:
    """
    TAS-755C 串口转以太网模块驱动类  
    - 通过 UART 与设备交互，采用 AT 命令进行配置  
    - 提供串口、网络、HTTP、心跳、注册、轮询、Modbus、MQTT、云平台等配置接口  
    - 内部封装 AT 命令发送与响应解析逻辑  
    - 返回值均为 (bool, str)，其中 bool 表示执行状态，str 为响应内容  

    本类既可作为配置控制器，也可用于设备发现与控制。  

    Methods:
        _send_at(cmd: str) -> (bool, str):
            发送一条 AT 命令并返回执行结果。
        set_uart_config(baud_rate, data_bits, parity, stop_bits) -> (bool, str):
            设置串口参数。
        set_uart_time(packet_time: int) -> (bool, str):
            设置串口分包时间。
        set_mac_address(mac: str) -> (bool, str):
            设置 MAC 地址。
        set_ip_config(mode: int, ip: str, gateway: str, subnet: str, dns: str) -> (bool, str):
            设置 IP 配置（静态或 DHCP）。
        set_tcp_config(local_port: int, remote_port: int, mode: int, remote_address: str) -> (bool, str):
            设置 TCP/UDP 配置。
        set_secondary_server(address: str) -> (bool, str):
            设置第二服务器地址。
        set_http_path(path: str) -> (bool, str):
            设置 HTTP 路径。
        set_http_config(net_status: int, method: int, header_return: int) -> (bool, str):
            设置 HTTP 配置。
        set_http_header(length: int, content: str) -> (bool, str):
            设置 HTTP Header。
        set_keepalive(enable: int, fmt: int, content: str, interval: int) -> (bool, str):
            设置心跳包。
        set_register(reg_type: int, send_mode: int, fmt: int, content: str) -> (bool, str):
            设置注册包。
        set_poll(enable: int, interval: int) -> (bool, str):
            设置轮询。
        set_poll_str(enable: int, crc: int, hex_str: str) -> (bool, str):
            设置轮询字符串。
        set_modbus(enable: int) -> (bool, str):
            设置 Modbus 转换。
        set_mqtt_client(client_id: str, username: str, password: str) -> (bool, str):
            设置 MQTT 客户端信息。
        set_mqtt_topics(sub_topic: str, pub_topic: str) -> (bool, str):
            设置 MQTT 订阅/发布主题。
        set_mqtt_options(clean_session: int, retain: int, keepalive: int) -> (bool, str):
            设置 MQTT 参数。
        set_ciphead(enable: int) -> (bool, str):
            设置数据头开关。
        set_link_delay(delay: int) -> (bool, str):
            设置连接延迟。
        set_log(net_status: int, boot_msg: int, exception_restart: int) -> (bool, str):
            设置日志选项。
        set_status(enable: int) -> (bool, str):
            设置状态输出。
        set_pinmux(mode: int) -> (bool, str):
            设置引脚复用。
        set_disconnect_time(time_sec: int) -> (bool, str):
            设置断开连接重启时间。
        set_ack_time(time_sec: int) -> (bool, str):
            设置无下行重启时间。
        set_port_time(time_sec: int) -> (bool, str):
            设置无上行重启时间。
        set_restart_time(time_sec: int) -> (bool, str):
            设置周期性重启时间。
        set_dtu_cloud(mode: int, account: str, password: str) -> (bool, str):
            设置 DTU 云平台。
        set_web_login(username: str, password: str) -> (bool, str):
            设置 Web 登录信息。
        enter_command_mode() -> (bool, str):
            进入命令模式。
        send_raw_command(command: str) -> (bool, str):
            发送原始 AT 命令。
        discovery() -> (bool, str):
            发送设备发现命令。
    ==========================================

    TAS-755C Serial-to-Ethernet module driver class  
    - Communicates with device via UART using AT commands  
    - Provides configuration interfaces for UART, Network, HTTP, Heartbeat, Register, Poll, Modbus, MQTT, Cloud, etc.  
    - Encapsulates AT command sending and response parsing  
    - Returns (bool, str), where bool is execution status, str is response content  

    This class can be used as a configuration controller as well as for device discovery and control.  

    Methods:
        _send_at(cmd: str) -> (bool, str):
            Send an AT command and return result.
        set_uart_config(baud_rate, data_bits, parity, stop_bits) -> (bool, str):
            Set UART parameters.
        set_uart_time(packet_time: int) -> (bool, str):
            Set UART packet time.
        set_mac_address(mac: str) -> (bool, str):
            Set MAC address.
        set_ip_config(mode: int, ip: str, gateway: str, subnet: str, dns: str) -> (bool, str):
            Set IP configuration (static or DHCP).
        set_tcp_config(local_port: int, remote_port: int, mode: int, remote_address: str) -> (bool, str):
            Set TCP/UDP configuration.
        set_secondary_server(address: str) -> (bool, str):
            Set secondary server address.
        set_http_path(path: str) -> (bool, str):
            Set HTTP path.
        set_http_config(net_status: int, method: int, header_return: int) -> (bool, str):
            Set HTTP configuration.
        set_http_header(length: int, content: str) -> (bool, str):
            Set HTTP header.
        set_keepalive(enable: int, fmt: int, content: str, interval: int) -> (bool, str):
            Set heartbeat packet.
        set_register(reg_type: int, send_mode: int, fmt: int, content: str) -> (bool, str):
            Set register packet.
        set_poll(enable: int, interval: int) -> (bool, str):
            Set polling.
        set_poll_str(enable: int, crc: int, hex_str: str) -> (bool, str):
            Set polling string.
        set_modbus(enable: int) -> (bool, str):
            Enable/disable Modbus conversion.
        set_mqtt_client(client_id: str, username: str, password: str) -> (bool, str):
            Set MQTT client information.
        set_mqtt_topics(sub_topic: str, pub_topic: str) -> (bool, str):
            Set MQTT subscribe/publish topics.
        set_mqtt_options(clean_session: int, retain: int, keepalive: int) -> (bool, str):
            Set MQTT options.
        set_ciphead(enable: int) -> (bool, str):
            Enable/disable data header.
        set_link_delay(delay: int) -> (bool, str):
            Set link delay.
        set_log(net_status: int, boot_msg: int, exception_restart: int) -> (bool, str):
            Set logging options.
        set_status(enable: int) -> (bool, str):
            Enable/disable status output.
        set_pinmux(mode: int) -> (bool, str):
            Set pin multiplexing.
        set_disconnect_time(time_sec: int) -> (bool, str):
            Set disconnect-restart time.
        set_ack_time(time_sec: int) -> (bool, str):
            Set no-downlink restart time.
        set_port_time(time_sec: int) -> (bool, str):
            Set no-uplink restart time.
        set_restart_time(time_sec: int) -> (bool, str):
            Set periodic restart time.
        set_dtu_cloud(mode: int, account: str, password: str) -> (bool, str):
            Set DTU cloud platform.
        set_web_login(username: str, password: str) -> (bool, str):
            Set Web login info.
        enter_command_mode() -> (bool, str):
            Enter command mode.
        send_raw_command(command: str) -> (bool, str):
            Send raw AT command.
        discovery() -> (bool, str):
            Discover devices.
    """
    # 串口与基础配置常量
    class UARTConfig:
        # 波特率选项
        BAUD_1200 = 1200
        BAUD_2400 = 2400
        BAUD_4800 = 4800
        BAUD_9600 = 9600
        BAUD_19200 = 19200
        BAUD_38400 = 38400
        BAUD_57600 = 57600
        BAUD_115200 = 115200
        BAUD_230400 = 230400
        
        # 数据位选项
        DATA_BITS_7 = 0
        DATA_BITS_8 = 1
        
        # 校验位选项
        PARITY_NONE = 0
        PARITY_ODD = 1
        PARITY_EVEN = 2
        
        # 停止位选项
        STOP_BITS_1 = 0
        STOP_BITS_2 = 1
        
        # 分包时间默认值
        PACKET_TIME_DEFAULT = 0

    class NetworkConfig:
        # IP配置模式
        IP_MODE_STATIC = 0
        IP_MODE_DHCP = 1
        
        # 工作模式
        MODE_TCP_CLIENT = 0
        MODE_TCP_SERVER = 1
        MODE_UDP_CLIENT = 2
        MODE_UDP_SERVER = 3
        MODE_DUAL_SERVER = 4
        MODE_IGMP = 5
        MODE_DTU_CLOUD = 6
        MODE_IOT_CLOUD = 7  # 不可用
        MODE_HTTP_PASSTHROUGH = 8
        MODE_MQTT = 9

    class HTTPConfig:
        # 网络状态
        HTTP_NET_DISABLED = 0
        HTTP_NET_ENABLED = 1
        
        # 方法
        HTTP_METHOD_POST = 0
        HTTP_METHOD_GET = 1
        
        # 包头返回
        HTTP_HEADER_DISABLED = 0
        HTTP_HEADER_ENABLED = 1

    class HeartbeatConfig:
        # 使能选项
        HEARTBEAT_DISABLED = 0
        HEARTBEAT_ENABLED = 1
        HEARTBEAT_EXTENDED = 2
        
        # 格式选项
        HEARTBEAT_FORMAT_ASCII = 0
        HEARTBEAT_FORMAT_HEX = 1

    class RegisterConfig:
        # 类型选项
        REGISTER_TYPE_NONE = 0
        REGISTER_TYPE_MAC = 1
        REGISTER_TYPE_CUSTOM = 2
        
        # 发送方式选项
        REGISTER_SEND_ONCE = 0
        REGISTER_SEND_PERIODIC = 1
        REGISTER_SEND_BOTH = 2
        
        # 格式选项
        REGISTER_FORMAT_ASCII = 0
        REGISTER_FORMAT_HEX = 1

    class PollConfig:
        # 使能选项
        POLL_DISABLED = 0
        POLL_ENABLED = 1
        
        # CRC选项
        POLL_CRC_DISABLED = 0
        POLL_CRC_ENABLED = 1

    class ModbusConfig:
        MODBUS_DISABLED = 0
        MODBUS_ENABLED = 1

    class MQTTConfig:
        # Clean session选项
        CLEAN_SESSION_DISABLED = 0
        CLEAN_SESSION_ENABLED = 1
        
        # Retain选项
        RETAIN_DISABLED = 0
        RETAIN_ENABLED = 1
        
        # 保持连接最小时间
        KEEPALIVE_MIN = 60

    class DataHeaderConfig:
        HEADER_DISABLED = 0
        HEADER_ENABLED = 1

    class LogConfig:
        # 网络状态日志
        LOG_NET_DISABLED = 0
        LOG_NET_ENABLED = 1
        
        # 开机提示日志
        LOG_BOOT_DISABLED = 0
        LOG_BOOT_ENABLED = 1
        
        # 异常重启提示日志
        LOG_EXCEPTION_DISABLED = 0
        LOG_EXCEPTION_ENABLED = 1

    class StatusConfig:
        STATUS_DISABLED = 0
        STATUS_ENABLED = 1

    class PinMuxConfig:
        PINMUX_NET_INDICATOR = 0
        PINMUX_HW_FLOW_CONTROL = 1
        PINMUX_RS485_DE_RE = 2

    class TimeoutConfig:
        # 禁用选项
        TIMEOUT_DISABLED = 0
        
        # 断开连接重启时间默认值
        DISCONNECT_TIME_DEFAULT = 120
        
        # 无响应重启时间默认值
        ACK_TIME_DEFAULT = 1800
        
        # 无数据重启时间默认值
        PORT_TIME_DEFAULT = 1800
        
        # 周期性重启时间默认值
        RESTART_TIME_DEFAULT = 0

    class CloudConfig:
        # 云平台模式
        CLOUD_MODE_DISABLED = 0
        CLOUD_MODE_ENABLED = 1
        CLOUD_MODE_LOCKED = 2

    # 通用常量
    class General:
        # 布尔选项
        DISABLED = 0
        ENABLED = 1
        
        # 默认端口
        DEFAULT_PORT = 10123
        
        # 默认心跳间隔
        DEFAULT_HEARTBEAT_INTERVAL = 0
        
        # 默认轮询间隔
        DEFAULT_POLL_INTERVAL = 0
        
        # UDP广播端口
        UDP_BROADCAST_PORT = 8081
        
        # 命令终止符
        COMMAND_TERMINATOR = "\r\n"
        
        # 命令模式进入序列
        COMMAND_MODE_ENTER = "+++"
        
        # MAC地址前缀
        MAC_PREFIX = "+MAC:"
        
        # 发现命令
        DISCOVERY_COMMAND = "at+tas"

    def __init__(self, uart):
        """
        初始化 TAS_755C_ETH 类实例。  

        Args:
            uart (object): 串口对象，需支持 write/read 方法。  

        ==========================================
        Initialize TAS_755C_ETH class instance.  

        Args:
            uart (object): UART object, must support write/read methods.
        """

        self._uart = uart

    def _send_at(self, cmd):
        """
        私有方法：发送 AT 命令并等待响应，直到收到 OK 或 ERROR。  

        Args:
            cmd (str): 完整的 AT 命令字符串。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)，True 表示成功，False 表示失败。  

        ==========================================
        Private method: Send an AT command and wait for response until OK or ERROR.  

        Args:
            cmd (str): Full AT command string.  

        Returns:
            Tuple[bool, str]: (status, response), True if success, False otherwise.
        """
        self._uart.write(cmd + self.General.COMMAND_TERMINATOR)
        response = []
        while True:
            line = self._uart.readline()
            if not line:
                break
            try:
                text = line.decode().strip()
            except:
                text = line.strip()
            if text == "OK":
                # 返回成功，附带之前收集的响应内容
                return True, "\n".join(response)
            if text.startswith("ERROR"):
                return False, text
            response.append(text)
        return False, "\n".join(response)

    def set_uart_config(self, baud_rate, data_bits, parity, stop_bits):
        """
        设置串口参数 (AT+UARTCFG)。  

        Args:
            baud_rate (int): 波特率。  
            data_bits (int): 数据位 (7 或 8)。  
            parity (int): 校验位 (0/1/2)。  
            stop_bits (int): 停止位 (1 或 2)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure UART parameters (AT+UARTCFG).  

        Args:
            baud_rate (int): Baud rate.  
            data_bits (int): Data bits (7 or 8).  
            parity (int): Parity bit (0/1/2).  
            stop_bits (int): Stop bits (1 or 2).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+UARTCFG={baud_rate},{data_bits},{parity},{stop_bits}"
        return self._send_at(cmd)

    def set_uart_time(self, packet_time):
        """
        设置串口分包时间 (AT+UARTTIME)。  

        Args:
            packet_time (int): 分包时间，单位 ms。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure UART packet split time (AT+UARTTIME).  

        Args:
            packet_time (int): Packet time in ms.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+UARTTIME=0,{packet_time}"
        return self._send_at(cmd)

    def set_mac_address(self, mac):
        """
        设置 MAC 地址 (AT+MACADDR)。  

        Args:
            mac (str): MAC 地址字符串 (格式: XX:XX:XX:XX:XX:XX)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Set MAC address (AT+MACADDR).  

        Args:
            mac (str): MAC address string (format: XX:XX:XX:XX:XX:XX).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+MACADDR={mac}"
        return self._send_at(cmd)

    # ==============================
    # 网络/TCP/UDP 配置方法
    # ==============================

    def set_ip_config(self, mode, ip, gateway, subnet, dns):
        """
        设置 IP 配置 (AT+IPCONFIG)。  

        Args:
            mode (int): 模式 (0=静态, 1=DHCP)。  
            ip (str): IP 地址。  
            gateway (str): 网关地址。  
            subnet (str): 子网掩码。  
            dns (str): DNS 服务器地址。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure IP settings (AT+IPCONFIG).  

        Args:
            mode (int): Mode (0=Static, 1=DHCP).  
            ip (str): IP address.  
            gateway (str): Gateway address.  
            subnet (str): Subnet mask.  
            dns (str): DNS server address.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+IPCONFIG={mode},{ip},{gateway},{subnet},{dns}"
        return self._send_at(cmd)

    def set_tcp_config(self, local_port, remote_port, mode, remote_address):
        """
        设置 TCP/UDP 配置 (AT+SOCKET)。  

        Args:
            local_port (int): 本地端口。  
            remote_port (int): 远程端口。  
            mode (int): 连接模式 (0=TCP Client, 1=TCP Server, 2=UDP)。  
            remote_address (str): 远程服务器地址。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure TCP/UDP settings (AT+SOCKET).  

        Args:
            local_port (int): Local port.  
            remote_port (int): Remote port.  
            mode (int): Connection mode (0=TCP Client, 1=TCP Server, 2=UDP).  
            remote_address (str): Remote server address.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+SOCKET=1,{mode},{local_port},{remote_port},{remote_address}"
        return self._send_at(cmd)

    def set_secondary_server(self, address):
        """
        设置第二服务器地址 (AT+SECONDSERVERADDR)。  

        Args:
            address (str): 第二服务器的 IP 或域名。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Set secondary server address (AT+SECONDSERVERADDR).  

        Args:
            address (str): IP or domain of secondary server.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+SECONDSERVERADDR={address}"
        return self._send_at(cmd)

    # ==============================
    # HTTP/Web 配置方法
    # ==============================

    def set_http_path(self, path):
        """
        设置 HTTP 路径 (AT+PATH)。  

        Args:
            path (str): HTTP 请求路径。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Set HTTP path (AT+PATH).  

        Args:
            path (str): HTTP request path.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+PATH=1,\"{path}\""
        return self._send_at(cmd)

    def set_http_config(self, net_status, method, header_return):
        """
        设置 HTTP 配置 (AT+HTTPCFG)。  

        Args:
            net_status (int): 网络状态 (0=禁用, 1=启用)。  
            method (int): 请求方法 (0=GET, 1=POST)。  
            header_return (int): 是否返回 Header (0=否, 1=是)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure HTTP settings (AT+HTTPCFG).  

        Args:
            net_status (int): Network status (0=disable, 1=enable).  
            method (int): Request method (0=GET, 1=POST).  
            header_return (int): Return header (0=No, 1=Yes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+HTTPCFG=1,{net_status},{method},{header_return}"
        return self._send_at(cmd)

    def set_http_header(self, length, content):
        """
        设置 HTTP Header (AT+HTTPHEAD)。  

        Args:
            length (int): Header 长度。  
            content (str): Header 内容。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Set HTTP header (AT+HTTPHEAD).  

        Args:
            length (int): Header length.  
            content (str): Header content.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+HTTPHEAD=1,{length},\"{content}\""
        return self._send_at(cmd)

    # ==============================
    # 心跳/注册/轮询 配置方法
    # ==============================

    def set_keepalive(self, enable, fmt, content, interval):
        """
        设置心跳包 (AT+KEEPALIVE)。  

        Args:
            enable (int): 是否启用 (0=否, 1=是)。  
            fmt (int): 格式 (0=HEX, 1=ASCII)。  
            content (str): 心跳内容。  
            interval (int): 心跳间隔 (秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure keepalive packet (AT+KEEPALIVE).  

        Args:
            enable (int): Enable (0=No, 1=Yes).  
            fmt (int): Format (0=HEX, 1=ASCII).  
            content (str): Keepalive content.  
            interval (int): Interval in seconds.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+KEEPALIVE={enable},{fmt},\"{content}\",{interval}"
        return self._send_at(cmd)

    def set_register(self, reg_type, send_mode, fmt, content):
        """
        设置注册包 (AT+REGIS)。  

        Args:
            reg_type (int): 注册类型。  
            send_mode (int): 发送模式。  
            fmt (int): 格式 (0=HEX, 1=ASCII)。  
            content (str): 注册内容。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure register packet (AT+REGIS).  

        Args:
            reg_type (int): Register type.  
            send_mode (int): Send mode.  
            fmt (int): Format (0=HEX, 1=ASCII).  
            content (str): Register content.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+REGIS={reg_type},{send_mode},{fmt},\"{content}\""
        return self._send_at(cmd)

    def set_poll(self, enable, interval):
        """
        设置轮询 (AT+POLL)。  

        Args:
            enable (int): 是否启用 (0=否, 1=是)。  
            interval (int): 轮询间隔 (秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure polling (AT+POLL).  

        Args:
            enable (int): Enable (0=No, 1=Yes).  
            interval (int): Polling interval in seconds.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+POLL={enable},{interval}"
        return self._send_at(cmd)

    def set_poll_str(self, enable, crc, hex_str):
        """
        设置轮询字符串 (AT+STRPOLL)。  

        Args:
            enable (int): 是否启用 (0=否, 1=是)。  
            crc (int): CRC 校验开关 (0=否, 1=是)。  
            hex_str (str): 轮询字符串内容。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure polling string (AT+STRPOLL).  

        Args:
            enable (int): Enable (0=No, 1=Yes).  
            crc (int): Enable CRC (0=No, 1=Yes).  
            hex_str (str): Polling string content.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+STRPOLL=1,1,{enable},{crc},\"{hex_str}\""
        return self._send_at(cmd)

    # ==============================
    # Modbus 配置方法
    # ==============================

    def set_modbus(self, enable):
        """
        设置 Modbus 转换 (AT+TCPMODBUS)。  

        Args:
            enable (int): 是否启用 (0=否, 1=是)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure Modbus conversion (AT+TCPMODBUS).  

        Args:
            enable (int): Enable (0=No, 1=Yes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+TCPMODBUS=1,{enable}"
        return self._send_at(cmd)

    # ==============================
    # MQTT 配置方法
    # ==============================

    def set_mqtt_client(self, client_id, username, password):
        """
        设置 MQTT 客户端信息 (AT+CLIENTID / AT+USERPWD)。  

        Args:
            client_id (str): 客户端 ID。  
            username (str): 用户名。  
            password (str): 密码。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT client info (AT+CLIENTID / AT+USERPWD).  

        Args:
            client_id (str): Client ID.  
            username (str): Username.  
            password (str): Password.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        status, data = self._send_at(f"AT+CLIENTID=\"{client_id}\"")
        if not status:
            return status, data
        return self._send_at(f"AT+USERPWD=\"{username}\",\"{password}\"")

    def set_mqtt_topics(self, sub_topic, pub_topic):
        """
        设置 MQTT 主题 (AT+MQTTSUB / AT+MQTTPUB)。  

        Args:
            sub_topic (str): 订阅主题。  
            pub_topic (str): 发布主题。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT topics (AT+MQTTSUB / AT+MQTTPUB).  

        Args:
            sub_topic (str): Subscribe topic.  
            pub_topic (str): Publish topic.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        status, data = self._send_at(f"AT+MQTTSUB=\"{sub_topic}\"")
        if not status:
            return status, data
        return self._send_at(f"AT+MQTTPUB=\"{pub_topic}\"")

    def set_mqtt_options(self, clean_session, retain, keepalive):
        """
        设置 MQTT 参数 (AT+CLEANSESSION / AT+RETAIN / AT+MQTTKEEP)。  

        Args:
            clean_session (int): 是否清理会话 (0=否, 1=是)。  
            retain (int): 保留消息 (0=否, 1=是)。  
            keepalive (int): 保活时间 (秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT options (AT+CLEANSESSION / AT+RETAIN / AT+MQTTKEEP).  

        Args:
            clean_session (int): Clean session (0=No, 1=Yes).  
            retain (int): Retain message (0=No, 1=Yes).  
            keepalive (int): Keepalive time in seconds.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        status, data = self._send_at(f"AT+CLEANSESSION={clean_session}")
        if not status:
            return status, data
        status, data = self._send_at(f"AT+RETAIN={retain}")
        if not status:
            return status, data
        return self._send_at(f"AT+MQTTKEEP={keepalive}")

    # ==============================
    # 数据头/网络传输 配置方法
    # ==============================

    def set_ciphead(self, enable):
        """
        设置数据头 (AT+CIPHEAD)。  

        Args:
            enable (int): 是否启用 (0=否, 1=是)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure data header (AT+CIPHEAD).  

        Args:
            enable (int): Enable (0=No, 1=Yes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+CIPHEAD=1,{enable}"
        return self._send_at(cmd)

    def set_link_delay(self, delay):
        """
        设置连接延迟 (AT+LINKDELAY)。  

        Args:
            delay (int): 延迟时间 (毫秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure link delay (AT+LINKDELAY).  

        Args:
            delay (int): Delay in ms.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+LINKDELAY=1,{delay}"
        return self._send_at(cmd)


    # ==============================
    # 日志/状态/引脚 配置方法
    # ==============================

    def set_log(self, net_status, boot_msg, exception_restart):
        """
        设置日志选项 (AT+LOG)。  

        Args:
            net_status (int): 网络状态日志。  
            boot_msg (int): 启动信息日志。  
            exception_restart (int): 异常重启日志。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure log options (AT+LOG).  

        Args:
            net_status (int): Network status log.  
            boot_msg (int): Boot message log.  
            exception_restart (int): Exception restart log.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+LOG=0,{net_status},{boot_msg},{exception_restart}"
        return self._send_at(cmd)

    def set_status(self, enable):
        """
        设置状态 (AT+STATUS)。  

        Args:
            enable (int): 是否启用状态输出 (0=否, 1=是)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure status output (AT+STATUS).  

        Args:
            enable (int): Enable status output (0=No, 1=Yes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+STATUS=0,{enable}"
        return self._send_at(cmd)

    def set_pinmux(self, mode):
        """
        设置引脚复用 (AT+PINMUX)。  

        Args:
            mode (int): 引脚复用模式。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure pin multiplexing (AT+PINMUX).  

        Args:
            mode (int): Pin multiplexing mode.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+PINMUX={mode}"
        return self._send_at(cmd)

    # ==============================
    # 超时/重启 配置方法
    # ==============================

    def set_disconnect_time(self, time_sec):
        """
        设置断开连接重启时间 (AT+DSCTIME)。  

        Args:
            time_sec (int): 时间 (秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure disconnect restart time (AT+DSCTIME).  

        Args:
            time_sec (int): Time in seconds.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+DSCTIME=0,{time_sec}"
        return self._send_at(cmd)

    def set_ack_time(self, time_sec):
        """
        设置无下行重启时间 (AT+ACKTIME)。  

        Args:
            time_sec (int): 时间 (秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure no-downlink restart time (AT+ACKTIME).  

        Args:
            time_sec (int): Time in seconds.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+ACKTIME=0,{time_sec}"
        return self._send_at(cmd)

    def set_port_time(self, time_sec):
        """
        设置无上行重启时间 (AT+PORTTIME)。  

        Args:
            time_sec (int): 时间 (秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure no-uplink restart time (AT+PORTTIME).  

        Args:
            time_sec (int): Time in seconds.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+PORTTIME=0,{time_sec}"
        return self._send_at(cmd)

    def set_restart_time(self, time_sec):
        """
        设置周期性重启时间 (AT+RESTTIME)。  

        Args:
            time_sec (int): 周期时间 (秒)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure periodic restart time (AT+RESTTIME).  

        Args:
            time_sec (int): Period time in seconds.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+RESTTIME={time_sec}"
        return self._send_at(cmd)

    # ==============================
    # 云平台/Web 登录 配置方法
    # ==============================

    def set_dtu_cloud(self, mode, account, password):
        """
        设置云平台 (AT+DTUCLOUD)。  

        Args:
            mode (int): 模式。  
            account (str): 账号。  
            password (str): 密码。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure cloud platform (AT+DTUCLOUD).  

        Args:
            mode (int): Mode.  
            account (str): Account.  
            password (str): Password.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+DTUCLOUD={mode},\"{account}\",\"{password}\""
        return self._send_at(cmd)

    def set_web_login(self, username, password):
        """
        设置 Web 登录 (AT+WEBLOGIN)。  

        Args:
            username (str): 用户名。  
            password (str): 密码。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure Web login (AT+WEBLOGIN).  

        Args:
            username (str): Username.  
            password (str): Password.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+WEBLOGIN=\"{username}\",\"{password}\""
        return self._send_at(cmd)

    # ==============================
    # 通用控制方法
    # ==============================

    def enter_command_mode(self):
        """
        进入命令模式 (+++)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Enter command mode (+++).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        self._uart.write(self.General.COMMAND_MODE_ENTER)
        line = self._uart.readline()
        if not line:
            return False, ""
        if line.decode().strip() == "OK":
            return True, ""
        return False, ""

    def send_raw_command(self, command):
        """
        发送原始 AT 命令。  

        Args:
            command (str): AT 命令字符串。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Send raw AT command.  

        Args:
            command (str): AT command string.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        return self._send_at(command)

    def discovery(self):
        """
        发现设备 (AT+TAS)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Discover device (AT+TAS).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        return self._send_at(self.General.DISCOVERY_COMMAND)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
