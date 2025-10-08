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

import time
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
        self._uart.write(f'{cmd}\r\n'.encode())
        time.sleep(0.1)
        if self._uart.any():
            resp = self._uart.read().decode('utf-8')
            if 'OK' in resp:
                return True, resp
            else:
                return False, resp
        else:
            return False, 'No response from UART'

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

    def get_uart_config(self):
        """
        查询当前串口参数 (AT+UARTCFG?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current UART parameters (AT+UARTCFG?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+UARTCFG?"
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
        cmd = f"AT+UARTTIME={packet_time}"
        return self._send_at(cmd)

    def get_uart_time(self):
        """
        查询当前串口分包时间 (AT+UARTTIME?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current UART packet split time (AT+UARTTIME?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+UARTTIME?"
        return self._send_at(cmd)


    def set_mac_address(self, mac):
        """
        设置 MAC 地址 (AT+MACADDR)。  

        Args:
            mac (str): MAC 地址字符串 (格式: XX-XX-XX-XX-XX-XX)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Set MAC address (AT+MACADDR).  

        Args:
            mac (str): MAC address string (format: XX-XX-XX-XX-XX-XX).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+MACADDR={mac}"
        return self._send_at(cmd)

    def get_mac_address(self):
        """
        查询当前 MAC 地址 (AT+MACADDR?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MAC address (AT+MACADDR?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+MACADDR?"
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

    def get_ip_config(self):
        """
        查询当前 IP 配置 (AT+IPCONFIG?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current IP configuration (AT+IPCONFIG?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+IPCONFIG?"
        return self._send_at(cmd)


    def set_tcp_config(self, local_port, remote_port, mode, remote_address):
        """
        设置 TCP 配置 (AT+TCPCFG)。  

        Args:
            local_port (int): 本地端口。  
            remote_port (int): 远程端口。  
            mode (int): 连接模式 (0=TCP Client, 1=TCP Server, 2=UDP)。  
            remote_address (str): 远程服务器地址。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure TCP settings (AT+TCPCFG).  

        Args:
            local_port (int): Local port.  
            remote_port (int): Remote port.  
            mode (int): Connection mode (0=TCP Client, 1=TCP Server, 2=UDP).  
            remote_address (str): Remote server address.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+TCPCFG={local_port},{remote_port},{mode},{remote_address}"
        return self._send_at(cmd)

    def get_tcp_config(self):
        """
        查询当前 TCP 配置 (AT+TCPCFG?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current TCP configuration (AT+TCPCFG?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+TCPCFG?"
        return self._send_at(cmd)


    def set_secondary_server(self, local_port, remote_port, remote_address):
        """
        设置第二服务器地址配置 (AT+SECONDSERVERADDRES)。  

        Args:
            local_port (int): 本地端口。  
            remote_port (int): 远程端口。  
            remote_address (str): 第二服务器的 IP 或域名。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        =========================================
        Set secondary server address configuration (AT+SECONDSERVERADDRES).  

        Args:
            local_port (int): Local port.  
            remote_port (int): Remote port.  
            remote_address (str): IP or domain of the secondary server.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+SECONDSERVERADDRES={local_port},{remote_port},{remote_address}"
        return self._send_at(cmd)

    def get_secondary_server(self):
        """
        查询当前第二服务器地址配置 (AT+SECONDSERVERADDRES?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        =========================================
        Query current secondary server address configuration (AT+SECONDSERVERADDRES?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+SECONDSERVERADDRES?"
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
        cmd = f'AT+PATH="{path}"'
        return self._send_at(cmd)

    def get_http_path(self):
        """
        查询当前 HTTP 路径 (AT+PATH?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current HTTP path (AT+PATH?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+PATH?"
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
        cmd = f"AT+HTTPCFG={net_status},{method},{header_return}"
        return self._send_at(cmd)

    def get_http_config(self):
        """
        查询当前 HTTP 配置 (AT+HTTPCFG?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current HTTP configuration (AT+HTTPCFG?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+HTTPCFG?"
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
        cmd = f'AT+HTTPHEAD={length},"{content}"'
        return self._send_at(cmd)

    def get_http_header(self):
        """
        查询当前 HTTP Header (AT+HTTPHEAD?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current HTTP header (AT+HTTPHEAD?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+HTTPHEAD?"
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
        cmd = f'AT+KEEPALIVE={enable},{fmt},"{content}",{interval}'
        return self._send_at(cmd)

    def get_keepalive(self):
        """
        查询当前心跳包配置 (AT+KEEPALIVE?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current keepalive packet configuration (AT+KEEPALIVE?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+KEEPALIVE?"
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
        cmd = f'AT+REGIS={reg_type},{send_mode},{fmt},"{content}"'
        return self._send_at(cmd)

    def get_register(self):
        """
        查询当前注册包配置 (AT+REGIS?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current register packet configuration (AT+REGIS?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+REGIS?"
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

    def get_poll(self):
        """
        查询当前轮询配置 (AT+POLL?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current polling configuration (AT+POLL?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+POLL?"
        return self._send_at(cmd)


    def set_poll_str(self, index: int, enable: int, crc: int, hex_str: str):
        """
        设置轮询字符串 (AT+POLLSTR)。  

        Args:
            index (int): 字串号 (1-10)。  
            enable (int): 是否启用 (0=否, 1=是)。  
            crc (int): CRC 校验开关 (0=否, 1=是)。  
            hex_str (str): 轮询字符串内容 (16进制字符串)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure polling string (AT+POLLSTR).  

        Args:
            index (int): String ID (1-10).  
            enable (int): Enable (0=No, 1=Yes).  
            crc (int): Enable CRC (0=No, 1=Yes).  
            hex_str (str): Polling string content (hex string)。  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f'AT+POLLSTR={index},{enable},{crc},"{hex_str}"'
        return self._send_at(cmd)

    def get_poll_str(self):
        """
        查询当前轮询字符串配置 (AT+POLLSTR?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current polling string configuration (AT+POLLSTR?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+POLLSTR?"
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
        cmd = f"AT+TCPMODBUS={enable}"
        return self._send_at(cmd)

    def get_modbus(self):
        """
        查询当前 Modbus 转换配置 (AT+TCPMODBUS?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current Modbus conversion configuration (AT+TCPMODBUS?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+TCPMODBUS?"
        return self._send_at(cmd)


    # ==============================
    # MQTT 配置方法
    # ==============================

    def set_mqtt_client_id(self, client_id: str):
        """
        设置 MQTT Client ID (AT+CLIENTID)。  

        Args:
            client_id (str): 客户端 ID (0-128 字节)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT Client ID (AT+CLIENTID).  

        Args:
            client_id (str): Client ID (0-128 bytes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f'AT+CLIENTID="{client_id}"'
        return self._send_at(cmd)

    def get_mqtt_client_id(self):
        """
        查询当前 MQTT Client ID (AT+CLIENTID?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MQTT Client ID (AT+CLIENTID?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+CLIENTID?"
        return self._send_at(cmd)


    def set_mqtt_userpwd(self, username: str, password: str):
        """
        设置 MQTT 用户名和密码 (AT+USERPWD)。  

        Args:
            username (str): 用户名 (0-64 字节)。  
            password (str): 密码 (0-128 字节)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT username and password (AT+USERPWD).  

        Args:
            username (str): Username (0-64 bytes).  
            password (str): Password (0-128 bytes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f'AT+USERPWD="{username}","{password}"'
        return self._send_at(cmd)

    def get_mqtt_userpwd(self):
        """
        查询当前 MQTT 用户名和密码配置 (AT+USERPWD?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MQTT username and password configuration (AT+USERPWD?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+USERPWD?"
        return self._send_at(cmd)


    def set_mqtt_subtopic(self, sub_topic):
        """
        设置 MQTT 订阅主题 (AT+MQTTSUB)。  

        Args:
            sub_topic (str): 订阅主题。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT subscribe topic (AT+MQTTSUB).  

        Args:
            sub_topic (str): Subscribe topic.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f'AT+MQTTSUB="{sub_topic}"'
        return self._send_at(cmd)

    def get_mqtt_subtopic(self):
        """
        查询当前 MQTT 订阅主题 (AT+MQTTSUB?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MQTT subscribe topic (AT+MQTTSUB?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+MQTTSUB?"
        return self._send_at(cmd)

    def set_mqtt_pubtopic(self, pub_topic):
        """
        设置 MQTT 发布主题 (AT+MQTTPUB)。  

        Args:
            pub_topic (str): 发布主题。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT publish topic (AT+MQTTPUB).  

        Args:
            pub_topic (str): Publish topic.  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f'AT+MQTTPUB="{pub_topic}"'
        return self._send_at(cmd)

    def get_mqtt_pubtopic(self):
        """
        查询当前 MQTT 发布主题 (AT+MQTTPUB?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MQTT publish topic (AT+MQTTPUB?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+MQTTPUB?"
        return self._send_at(cmd)

    def set_mqtt_clean_session(self, clean_session: int):
        """
        设置 MQTT 清除会话标志 (AT+CLEANSESSION)。  

        Args:
            clean_session (int): 是否清理会话 (0=否, 1=是)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT clean session flag (AT+CLEANSESSION).  

        Args:
            clean_session (int): Clean session (0=No, 1=Yes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+CLEANSESSION={clean_session}"
        return self._send_at(cmd)

    def get_mqtt_clean_session(self):
        """3 
        查询当前 MQTT 清除会话标志 (AT+CLEANSESSION?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MQTT clean session flag (AT+CLEANSESSION?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+CLEANSESSION?"
        return self._send_at(cmd)


    def set_mqtt_retain(self, retain: int):
        """
        设置 MQTT 消息保留 (AT+RETAIN)。  

        Args:
            retain (int): 是否保留消息 (0=否, 1=是)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT retain message flag (AT+RETAIN).  

        Args:
            retain (int): Retain message (0=No, 1=Yes).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+RETAIN={retain}"
        return self._send_at(cmd)

    def get_mqtt_retain(self):
        """
        查询当前 MQTT 消息保留设置 (AT+RETAIN?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MQTT retain message flag (AT+RETAIN?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+RETAIN?"
        return self._send_at(cmd)

    def set_mqtt_keepalive(self, keepalive: int):
        """
        设置 MQTT 心跳保活时间 (AT+MQTTKEEP)。  

        Args:
            keepalive (int): 心跳时间，范围 60–65535 秒。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Configure MQTT keepalive time (AT+MQTTKEEP).  

        Args:
            keepalive (int): Keepalive time in seconds (60–65535).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = f"AT+MQTTKEEP={keepalive}"
        return self._send_at(cmd)

    def get_mqtt_keepalive(self):
        """
        查询当前 MQTT 心跳保活时间 (AT+MQTTKEEP?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current MQTT keepalive time (AT+MQTTKEEP?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+MQTTKEEP?"
        return self._send_at(cmd)

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
        cmd = f"AT+CIPHEAD={enable}"
        return self._send_at(cmd)

    def get_ciphead(self):
        """
        查询当前数据头配置 (AT+CIPHEAD?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current data header configuration (AT+CIPHEAD?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+CIPHEAD?"
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
        cmd = f"AT+LINKDELAY={delay}"
        return self._send_at(cmd)

    def get_link_delay(self):
        """
        查询当前连接延迟配置 (AT+LINKDELAY?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current link delay configuration (AT+LINKDELAY?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+LINKDELAY?"
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
        cmd = f"AT+LOG={net_status},{boot_msg},{exception_restart}"
        return self._send_at(cmd)


    def get_log(self):
        """
        查询当前日志选项配置 (AT+LOG?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current log options configuration (AT+LOG?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+LOG?"
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
        cmd = f"AT+STATUS={enable}"
        return self._send_at(cmd)

    def get_status(self):
        """
        查询当前状态配置 (AT+STATUS?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current status configuration (AT+STATUS?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+STATUS?"
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

    def get_pinmux(self):
        """
        查询当前引脚复用配置 (AT+PINMUX?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current pin multiplexing configuration (AT+PINMUX?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+PINMUX?"
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
        cmd = f"AT+DSCTIME={time_sec}"
        return self._send_at(cmd)

    def get_disconnect_time(self):
        """
        查询当前断开连接重启时间配置 (AT+DSCTIME?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current disconnect restart time configuration (AT+DSCTIME?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+DSCTIME?"
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
        cmd = f"AT+ACKTIME={time_sec}"
        return self._send_at(cmd)


    def get_ack_time(self):
        """
        查询当前无下行重启时间配置 (AT+ACKTIME?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current no-downlink restart time configuration (AT+ACKTIME?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+ACKTIME?"
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
        cmd = f"AT+PORTTIME={time_sec}"
        return self._send_at(cmd)

    def get_port_time(self):
        """
        查询当前无上行重启时间配置 (AT+PORTTIME?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current no-uplink restart time configuration (AT+PORTTIME?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+PORTTIME?"
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


    def get_restart_time(self):
        """
        查询当前周期性重启时间配置 (AT+RESTTIME?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current periodic restart time configuration (AT+RESTTIME?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+RESTTIME?"
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
        cmd = f'AT+DTUCLOUD={mode},"{account}","{password}"'
        return self._send_at(cmd)

    def get_dtu_cloud(self):
        """
        查询当前云平台配置 (AT+DTUCLOUD?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current cloud platform configuration (AT+DTUCLOUD?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+DTUCLOUD?"
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
        cmd = f'AT+WEBLOGIN="{username}","{password}"'
        return self._send_at(cmd)

    def get_web_login(self):
        """
        查询当前 Web 登录配置 (AT+WEBLOGIN?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query current Web login configuration (AT+WEBLOGIN?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+WEBLOGIN?"
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
        self._uart.write(b'+++')
        time.sleep(0.05)
        if self._uart.any():
            resp = self._uart.read()
        if resp.decode('utf-8').strip() == "OK":
            return True, ""
        return False, ""

    def enter_data_mode(self):
        """
        进入数据模式 (ATO)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Enter data mode (ATO).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "ATO"
        return self._send_at(cmd)

    def get_all(self):
        """
        查询所有配置 (AT+ALL?)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Query all configurations (AT+ALL?).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+ALL?"
        return self._send_at(cmd)
    
    def save(self):
        """
        保存当前配置 (AT&W)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Save current configuration (AT&W).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT&W"
        return self._send_at(cmd)
    
    def restart(self):
        """
        重启设备 (AT+CFUN=1,1)。  

        Returns:
            Tuple[bool, str]: (状态, 响应内容)。  

        ==========================================
        Restart device (AT+CFUN=1,1).  

        Returns:
            Tuple[bool, str]: (status, response).
        """
        cmd = "AT+CFUN=1,1"
        return self._send_at(cmd)



# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
