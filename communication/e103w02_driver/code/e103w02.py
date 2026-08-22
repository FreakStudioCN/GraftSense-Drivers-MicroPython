# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/19
# @Author  : FreakStudio
# @File    : e103w02.py
# @Description : EBYTE E103-W02 UART Wi-Fi module driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.x"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const

# ======================================== 全局变量 ============================================

_DEFAULT_TIMEOUT_MS = const(1500)
_DEFAULT_IDLE_MS = const(120)
_POLL_INTERVAL_MS = const(5)

# ======================================== 功能函数 ============================================


def _to_bytes(data: object) -> bytes:
    """将字符串或字节数据转换为 bytes。Convert str/bytes-like data to bytes."""
    if data is None:
        raise ValueError("data cannot be None")
    if isinstance(data, str):
        return data.encode("utf-8")
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, memoryview):
        return bytes(data)
    raise TypeError("data must be str, bytes, bytearray, or memoryview")


def _validate_ipv4(value: str, name: str) -> None:
    """校验点分十进制 IPv4。Validate an IPv4 dotted-decimal string."""
    if not isinstance(value, str):
        raise TypeError("%s must be str" % name)
    parts = value.split(".")
    if len(parts) != 4:
        raise ValueError("%s must be an IPv4 address" % name)
    for part in parts:
        if not part.isdigit() or int(part) < 0 or int(part) > 255:
            raise ValueError("%s must be an IPv4 address" % name)


def _validate_port(port: int, name: str) -> None:
    """校验网络端口。Validate a network port."""
    if not isinstance(port, int):
        raise TypeError("%s must be int" % name)
    if port < 1 or port > 65535:
        raise ValueError("%s must be between 1 and 65535" % name)


# ======================================== 自定义类 ============================================


class E103W02:
    """
    EBYTE E103-W02 串口 Wi-Fi 模块驱动。

    UART 对象由调用者创建并注入。驱动提供常用官方 AT 配置、状态查询、
    AT/透传模式切换及原始透传数据收发。官方手册未定义统一错误语法，
    因而公共命令 API 返回清理回显后的原始响应文本。

    ==========================================
    EBYTE E103-W02 UART Wi-Fi module driver.

    The caller creates and injects the UART object. Command APIs return raw
    response text with the exact command echo removed because the official
    manuals do not define a universal error grammar.

    Attributes:
        ROLE_AP/ROLE_STA: 官方 Wi-Fi 角色常量。Official Wi-Fi role values.
        MODE_*: 官方运行模式常量。Official run-mode values.
        PROTOCOL_*: 官方 Socket 协议常量。Official socket protocol values.

    Methods:
        查询和设置模块参数、切换 AT/透传模式并收发透明数据。
        Query/configure the module, switch modes, and transfer raw data.

    Notes:
        所有方法均非 ISR 安全；调用者负责 UART 生命周期和并发互斥。
        Methods are not ISR-safe; the caller owns the UART and synchronization.
    """

    ROLE_AP = "AP"
    ROLE_STA = "STA"

    MODE_NORMAL = "NORMAL"
    MODE_MQTT = "MQTT"
    MODE_HTTP = "HTTP"
    MODE_MULTIS = "MULTIS"
    MODE_MULTIC = "MULTIC"

    PROTOCOL_TCP = "TCP"
    PROTOCOL_UDP = "UDP"
    SOCKET_CLIENT = "CLIENT"
    SOCKET_SERVER = "SERVER"

    SECURITY_OPEN = const(0)
    SECURITY_WEP = const(1)
    SECURITY_WPA2 = const(2)

    IP_MODE_DHCP = "DHCP"
    IP_MODE_STATIC = "STATIC"

    def __init__(
        self,
        uart: object,
        command_terminator: bytes = b"\r\n",
        timeout_ms: int = _DEFAULT_TIMEOUT_MS,
        idle_ms: int = _DEFAULT_IDLE_MS,
        debug: bool = False,
    ) -> None:
        """
        初始化驱动但不发送命令。Initialize without sending commands.

        Args:
            uart: 支持 write/read/any 的已初始化 UART 对象。
            command_terminator: 普通 AT 命令结束字节，默认 CRLF。
            timeout_ms: 命令总超时。
            idle_ms: 收到数据后的静默完成窗口。
            debug: 是否打印调试信息。

        Notes:
            不拥有 UART 生命周期；deinit() 不会关闭外部 UART。
            No UART I/O occurs during construction.
        Returns:
            None: 构造函数无返回值。Constructors do not return a value.
        Raises:
            TypeError/ValueError: 依赖或配置参数无效。Invalid dependency or configuration.
        """
        if uart is None:
            raise ValueError("uart cannot be None")
        if not hasattr(uart, "write") or not hasattr(uart, "read") or not hasattr(uart, "any"):
            raise TypeError("uart must provide write(), read(), and any()")
        if not isinstance(command_terminator, bytes):
            raise TypeError("command_terminator must be bytes")
        if len(command_terminator) == 0:
            raise ValueError("command_terminator cannot be empty")
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than 0")
        if not isinstance(idle_ms, int):
            raise TypeError("idle_ms must be int")
        if idle_ms <= 0 or idle_ms > timeout_ms:
            raise ValueError("idle_ms must be greater than 0 and not exceed timeout_ms")
        if not isinstance(debug, bool):
            raise TypeError("debug must be bool")

        self._uart = uart
        self._terminator = command_terminator
        self._timeout_ms = timeout_ms
        self._idle_ms = idle_ms
        self._debug = debug
        self._command_mode = False

    def enter_command_mode(self, timeout_ms: int = None) -> str:
        """
        使用官方 `+++` 进入 AT 模式。Enter AT mode with the official escape.

        Returns:
            str: 模块原始响应文本。
        Raises:
            ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes:
            官方手册未定义 guard time；调用者应确保 UART 当前空闲。
            产生 UART I/O，非 ISR 安全。Performs UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        self._drain_input()
        self._write_bytes(b"+++")
        response = self._read_response(timeout_ms)
        if "Entered AT mode" not in response:
            raise RuntimeError("E103-W02 did not confirm AT mode: %s" % response)
        self._command_mode = True
        return response

    def exit_command_mode(self, timeout_ms: int = None) -> str:
        """退出 AT 模式并回到透传。Exit AT mode and return to transparent mode.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: 模块原始响应。Raw module response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 产生 UART I/O，非 ISR 安全。Performs UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        response = self.send_command("AT+EXIT", timeout_ms)
        if "Exited AT" not in response:
            raise RuntimeError("E103-W02 did not confirm data mode: %s" % response)
        self._command_mode = False
        return response

    def send_command(self, command: str, timeout_ms: int = None) -> str:
        """
        发送手册中存在的原始 AT 命令。Send an official raw AT command.

        Args:
            command: 不含结束符的命令，必须以 `AT+` 开头。
            timeout_ms: 可选事务超时。
        Returns:
            str: 去除完全匹配命令回显后的原始响应。
        Raises:
            ValueError/TypeError/RuntimeError: 参数、模式或通信失败。
        Notes:
            产生 UART I/O，非 ISR 安全。Performs UART I/O; not ISR-safe.
        """
        if not isinstance(command, str):
            raise TypeError("command must be str")
        if not command.startswith("AT+"):
            raise ValueError("command must start with AT+")
        if "\r" in command or "\n" in command:
            raise ValueError("command must not contain CR or LF")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        if not self._command_mode:
            raise RuntimeError("enter_command_mode() must be called first")

        self._drain_input()
        self._write_bytes(command.encode("utf-8") + self._terminator)
        response = self._read_response(timeout_ms)
        return self._remove_echo(response, command)

    def get_all_state(self, timeout_ms: int = None) -> str:
        """执行全部官方查询。Execute all official state queries.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: 模块原始响应。Raw module response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；产生 UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+ALLSTATE", timeout_ms)

    def get_version(self, timeout_ms: int = None) -> str:
        """查询固件版本。Query firmware version.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: 固件版本响应。Firmware version response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；产生 UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+VER=?", timeout_ms)

    def get_device_sn(self, timeout_ms: int = None) -> str:
        """查询设备序列号。Query device serial number.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: 序列号响应。Serial-number response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；产生 UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+DEVSN=?", timeout_ms)

    def get_mac(self, timeout_ms: int = None) -> str:
        """查询模块 MAC。Query module MAC address.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: MAC 响应。MAC response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；产生 UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+MAC=?", timeout_ms)

    def get_status(self, timeout_ms: int = None) -> str:
        """查询 Wi-Fi IP 与网关状态。Query Wi-Fi IP and gateway status.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: 网络状态响应。Network status response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；产生 UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+STATUS=?", timeout_ms)

    def get_role(self, timeout_ms: int = None) -> str:
        """查询 AP/STA 角色。Query AP/STA role.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: 角色响应。Role response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；产生 UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+ROLE=?", timeout_ms)

    def set_role(self, role: str, timeout_ms: int = None) -> str:
        """设置 AP 或 STA 角色。Set AP or STA role.

        Args: role: 官方角色值。Official role value. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改模块配置；UART I/O，非 ISR 安全。Changes configuration; UART I/O; not ISR-safe.
        """
        if not isinstance(role, str):
            raise TypeError("role must be str")
        role = role.upper()
        if role not in (self.ROLE_AP, self.ROLE_STA):
            raise ValueError("role must be AP or STA")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+ROLE=%s" % role, timeout_ms)

    def get_mode(self, timeout_ms: int = None) -> str:
        """查询当前运行模式。Query current run mode.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: 运行模式响应。Run-mode response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+MODE=?", timeout_ms)

    def set_mode(self, mode: str, timeout_ms: int = None) -> str:
        """设置官方运行模式。Set an official run mode.

        Args: mode: 官方模式值。Official mode value. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改模块配置；UART I/O，非 ISR 安全。Changes configuration; UART I/O; not ISR-safe.
        """
        if not isinstance(mode, str):
            raise TypeError("mode must be str")
        mode = mode.upper()
        if mode not in (self.MODE_NORMAL, self.MODE_MQTT, self.MODE_HTTP, self.MODE_MULTIS, self.MODE_MULTIC):
            raise ValueError("unsupported E103-W02 mode")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+MODE=%s" % mode, timeout_ms)

    def get_sta(self, timeout_ms: int = None) -> str:
        """查询 STA 配置。Query STA configuration.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: STA 配置响应。STA configuration response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+STA=?", timeout_ms)

    def set_sta(self, ssid: str, security: int, password: str, timeout_ms: int = None) -> str:
        """设置 STA SSID、加密和密码。Set STA SSID, security, and password.

        Args: ssid/security/password: Wi-Fi 参数。Wi-Fi parameters. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改持久网络配置；UART I/O，非 ISR 安全。Changes network settings; not ISR-safe.
        """
        if not isinstance(ssid, str):
            raise TypeError("ssid must be str")
        if len(ssid.encode("utf-8")) < 1 or len(ssid.encode("utf-8")) > 32:
            raise ValueError("ssid must be 1 to 32 bytes")
        if not isinstance(security, int):
            raise TypeError("security must be int")
        if security not in (self.SECURITY_OPEN, self.SECURITY_WEP, self.SECURITY_WPA2):
            raise ValueError("security must be 0, 1, or 2")
        if not isinstance(password, str):
            raise TypeError("password must be str")
        if security != self.SECURITY_OPEN and (len(password.encode("utf-8")) < 8 or len(password.encode("utf-8")) > 63):
            raise ValueError("password must be 8 to 63 bytes for secured Wi-Fi")
        if "," in ssid or "," in password or "\r" in ssid or "\n" in ssid or "\r" in password or "\n" in password:
            raise ValueError("ssid and password cannot contain comma, CR, or LF")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+STA=%s,%d,%s" % (ssid, security, password), timeout_ms)

    def get_sta_ip(self, timeout_ms: int = None) -> str:
        """查询 STA IP 配置。Query STA IP configuration.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: STA IP 响应。STA IP response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+STAIP=?", timeout_ms)

    def set_sta_ip(self, ip_mode: str, ip: str, mask: str, gateway: str, dns: str, timeout_ms: int = None) -> str:
        """设置 STA DHCP/静态地址。Set STA DHCP/static address fields.

        Args: ip_mode/ip/mask/gateway/dns: 地址参数。Address fields. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改持久网络配置；UART I/O，非 ISR 安全。Changes network settings; not ISR-safe.
        """
        if not isinstance(ip_mode, str):
            raise TypeError("ip_mode must be str")
        ip_mode = ip_mode.upper()
        if ip_mode not in (self.IP_MODE_DHCP, self.IP_MODE_STATIC):
            raise ValueError("ip_mode must be DHCP or STATIC")
        _validate_ipv4(ip, "ip")
        _validate_ipv4(mask, "mask")
        _validate_ipv4(gateway, "gateway")
        _validate_ipv4(dns, "dns")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        command = "AT+STAIP=%s,%s,%s,%s,%s" % (ip_mode, ip, mask, gateway, dns)
        return self.send_command(command, timeout_ms)

    def get_ap(self, timeout_ms: int = None) -> str:
        """查询 AP 配置。Query AP configuration.

        Args: timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns: str: AP 配置响应。AP configuration response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+AP=?", timeout_ms)

    def set_ap(self, ssid: str, security: int, password: str, timeout_ms: int = None) -> str:
        """设置 AP SSID、加密和密码。Set AP SSID, security, and password.

        Args: ssid/security/password: AP 参数。AP parameters. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改持久网络配置；UART I/O，非 ISR 安全。Changes network settings; not ISR-safe.
        """
        if not isinstance(ssid, str):
            raise TypeError("ssid must be str")
        if len(ssid.encode("utf-8")) < 1 or len(ssid.encode("utf-8")) > 32:
            raise ValueError("ssid must be 1 to 32 bytes")
        if not isinstance(security, int):
            raise TypeError("security must be int")
        if security not in (self.SECURITY_OPEN, self.SECURITY_WEP, self.SECURITY_WPA2):
            raise ValueError("security must be 0, 1, or 2")
        if not isinstance(password, str):
            raise TypeError("password must be str")
        if security != self.SECURITY_OPEN and (len(password.encode("utf-8")) < 8 or len(password.encode("utf-8")) > 63):
            raise ValueError("password must be 8 to 63 bytes for secured Wi-Fi")
        if "," in ssid or "," in password or "\r" in ssid or "\n" in ssid or "\r" in password or "\n" in password:
            raise ValueError("ssid and password cannot contain comma, CR, or LF")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+AP=%s,%d,%s" % (ssid, security, password), timeout_ms)

    def get_ap_ip(self, timeout_ms: int = None) -> str:
        """查询 AP IP 配置。Query AP IP configuration.

        Args: timeout_ms: 可选超时。Optional timeout.
        Returns: str: AP IP 响应。AP IP response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+APIP=?", timeout_ms)

    def set_ap_ip(self, ip: str, mask: str, gateway: str, dns: str, timeout_ms: int = None) -> str:
        """设置 AP IP、掩码、网关和 DNS。Set AP IP, mask, gateway, and DNS.

        Args: ip/mask/gateway/dns: 地址参数。Address fields. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改持久配置；UART I/O，非 ISR 安全。Changes configuration; not ISR-safe.
        """
        _validate_ipv4(ip, "ip")
        _validate_ipv4(mask, "mask")
        _validate_ipv4(gateway, "gateway")
        _validate_ipv4(dns, "dns")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+APIP=%s,%s,%s,%s" % (ip, mask, gateway, dns), timeout_ms)

    def get_ap_channel(self, timeout_ms: int = None) -> str:
        """查询 AP 信道。Query AP channel.

        Args: timeout_ms: 可选超时。Optional timeout.
        Returns: str: AP 信道响应。AP channel response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+CHAN=?", timeout_ms)

    def set_ap_channel(self, channel: int, timeout_ms: int = None) -> str:
        """设置 AP 信道 1–11。Set AP channel from 1 to 11.

        Args: channel: 信道号。Channel number. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改持久配置；UART I/O，非 ISR 安全。Changes configuration; not ISR-safe.
        """
        if not isinstance(channel, int):
            raise TypeError("channel must be int")
        if channel < 1 or channel > 11:
            raise ValueError("channel must be between 1 and 11")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+CHAN=%d" % channel, timeout_ms)

    def get_socket(self, timeout_ms: int = None) -> str:
        """查询主 Socket 配置。Query main socket configuration.

        Args: timeout_ms: 可选超时。Optional timeout.
        Returns: str: Socket 配置响应。Socket configuration response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+SOCK=?", timeout_ms)

    def set_socket(
        self,
        protocol: str,
        socket_role: str,
        remote_ip: str,
        remote_port: int,
        local_port: int,
        timeout_ms: int = None,
    ) -> str:
        """设置主 TCP/UDP Socket。Configure the main TCP/UDP socket.

        Args: protocol/socket_role/remote_ip/remote_port/local_port: Socket 参数。Socket fields. timeout_ms: 可选超时。
        Returns: str: 模块响应。Module response.
        Raises: TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 修改持久网络配置；UART I/O，非 ISR 安全。Changes network settings; not ISR-safe.
        """
        if not isinstance(protocol, str):
            raise TypeError("protocol must be str")
        protocol = protocol.upper()
        if protocol not in (self.PROTOCOL_TCP, self.PROTOCOL_UDP):
            raise ValueError("protocol must be TCP or UDP")
        if not isinstance(socket_role, str):
            raise TypeError("socket_role must be str")
        socket_role = socket_role.upper()
        if socket_role not in (self.SOCKET_CLIENT, self.SOCKET_SERVER):
            raise ValueError("socket_role must be CLIENT or SERVER")
        _validate_ipv4(remote_ip, "remote_ip")
        _validate_port(remote_port, "remote_port")
        _validate_port(local_port, "local_port")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        command = "AT+SOCK=%s,%s,%s,%d,%d" % (protocol, socket_role, remote_ip, remote_port, local_port)
        return self.send_command(command, timeout_ms)

    def get_uart_config(self, timeout_ms: int = None) -> str:
        """查询模块 UART 参数。Query module UART parameters.

        Args: timeout_ms: 可选超时。Optional timeout.
        Returns: str: UART 参数响应。UART configuration response.
        Raises: ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        Notes: 仅查询；UART I/O，非 ISR 安全。Read-only UART I/O; not ISR-safe.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+UART=?", timeout_ms)

    def set_uart_config(self, baudrate: int, data_bits: int, parity: int, stop_bits: int, timeout_ms: int = None) -> str:
        """
        设置模块 UART 参数。Set module UART parameters.

        Notes:
            此调用不重配置外部 UART；应在专门加锁回归中使用。
            官方手册仅明确示例 parity=0，其他数值编码未确认。
        Args:
            baudrate/data_bits/parity/stop_bits: 模块 UART 参数。Module UART fields.
            timeout_ms: 可选事务超时。Optional transaction timeout.
        Returns:
            str: 模块响应。Module response.
        Raises:
            TypeError/ValueError/RuntimeError: 参数或通信失败。Invalid input or communication failure.
        """
        if not isinstance(baudrate, int):
            raise TypeError("baudrate must be int")
        if baudrate < 300 or baudrate > 3000000:
            raise ValueError("baudrate must be between 300 and 3000000")
        if not isinstance(data_bits, int) or data_bits not in (5, 6, 7, 8):
            raise ValueError("data_bits must be 5, 6, 7, or 8")
        if not isinstance(parity, int) or parity != 0:
            raise ValueError("only officially demonstrated parity value 0 is supported")
        if not isinstance(stop_bits, int) or stop_bits not in (1, 2):
            raise ValueError("stop_bits must be 1 or 2")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        return self.send_command("AT+UART=%d,%d,%d,%d" % (baudrate, data_bits, parity, stop_bits), timeout_ms)

    def reset(self, confirm: bool = False, timeout_ms: int = None) -> str:
        """发送官方重启命令。Send the official reboot command.

        Args: confirm: 显式确认锁。Explicit safety lock. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 重启前模块响应。Module response before reboot.
        Raises: TypeError/ValueError/RuntimeError: 未确认、参数或通信失败。Lock, input, or I/O failure.
        Notes: 模块重启并退出 AT 模式；非 ISR 安全。Reboots the module; not ISR-safe.
        """
        if not isinstance(confirm, bool):
            raise TypeError("confirm must be bool")
        if not confirm:
            raise RuntimeError("reset requires confirm=True")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        response = self.send_command("AT+RST", timeout_ms)
        self._command_mode = False
        return response

    def restore_factory_defaults(self, confirm: bool = False, timeout_ms: int = None) -> str:
        """恢复出厂设置。Restore factory defaults with an explicit destructive lock.

        Args: confirm: 显式确认锁。Explicit safety lock. timeout_ms: 可选超时。Optional timeout.
        Returns: str: 恢复前模块响应。Module response before restore.
        Raises: TypeError/ValueError/RuntimeError: 未确认、参数或通信失败。Lock, input, or I/O failure.
        Notes: 清除持久配置并退出 AT 模式；非 ISR 安全。Erases settings; not ISR-safe.
        """
        if not isinstance(confirm, bool):
            raise TypeError("confirm must be bool")
        if not confirm:
            raise RuntimeError("factory restore requires confirm=True")
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        response = self.send_command("AT+RESTORE", timeout_ms)
        self._command_mode = False
        return response

    def write(self, data: object) -> int:
        """在透传模式发送原始数据。Write raw data in transparent mode.

        Args: data: 字符串或字节数据。String or bytes-like payload.
        Returns: int: 已发送字节数。Number of bytes written.
        Raises: TypeError/ValueError/RuntimeError: 参数、模式或 UART 写入失败。
        Notes: 产生 UART I/O，非 ISR 安全。Performs UART I/O; not ISR-safe.
        """
        if data is None:
            raise ValueError("data cannot be None")
        payload = _to_bytes(data)
        if self._command_mode:
            raise RuntimeError("exit command mode before writing transparent data")
        return self._write_bytes(payload)

    def read(self, size: int = None, timeout_ms: int = 0) -> bytes:
        """读取透传数据。Read transparent data with an optional bounded timeout.

        Args: size: 最大字节数。Maximum bytes. timeout_ms: 有界等待时间。Bounded wait.
        Returns: bytes: 收到的数据或空字节串。Received data or empty bytes.
        Raises: TypeError/ValueError/RuntimeError: 参数、模式或 UART 读取失败。
        Notes: 轮询 UART，非 ISR 安全。Polls UART; not ISR-safe.
        """
        if size is not None and (not isinstance(size, int) or size <= 0):
            raise ValueError("size must be a positive int or None")
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms < 0:
            raise ValueError("timeout_ms cannot be negative")
        if self._command_mode:
            raise RuntimeError("exit command mode before reading transparent data")

        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            available = self._uart_any()
            if available:
                count = available if size is None else min(size, available)
                try:
                    data = self._uart.read(count)
                except OSError as exc:
                    raise RuntimeError("UART read failed") from exc
                return data if data is not None else b""
            if timeout_ms == 0 or time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return b""
            time.sleep_ms(_POLL_INTERVAL_MS)

    def readline(self, timeout_ms: int = 0, max_bytes: int = 1024) -> bytes:
        """读取至 LF、上限或超时。Read until LF, limit, or timeout.

        Args: timeout_ms: 有界等待时间。Bounded wait. max_bytes: 最大字节数。Maximum bytes.
        Returns: bytes: 收到的一行或部分数据。A line or partial payload.
        Raises: TypeError/ValueError/RuntimeError: 参数、模式或 UART 读取失败。
        Notes: 轮询 UART，非 ISR 安全。Polls UART; not ISR-safe.
        """
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms < 0:
            raise ValueError("timeout_ms cannot be negative")
        if not isinstance(max_bytes, int):
            raise TypeError("max_bytes must be int")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be greater than 0")
        if self._command_mode:
            raise RuntimeError("exit command mode before reading transparent data")

        result = bytearray()
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while len(result) < max_bytes:
            if self._uart_any():
                chunk = self.read(1, 0)
                if chunk:
                    result.extend(chunk)
                    if chunk == b"\n":
                        break
            elif timeout_ms == 0 or time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                break
            else:
                time.sleep_ms(_POLL_INTERVAL_MS)
        return bytes(result)

    def is_command_mode(self) -> bool:
        """返回驱动侧模式追踪状态。Return the driver's local mode state.

        Returns: bool: 驱动记录的 AT 模式状态。Locally tracked AT-mode state.
        Raises: 无。None.
        Notes: 不访问 UART，非模块实时查询；非 ISR 安全。No UART I/O; local state only; not ISR-safe.
        """
        return self._command_mode

    def _write_bytes(self, payload: bytes) -> int:
        if payload is None:
            raise ValueError("payload cannot be None")
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        try:
            written = self._uart.write(payload)
        except OSError as exc:
            raise RuntimeError("UART write failed") from exc
        if written is None:
            return len(payload)
        if written != len(payload):
            raise RuntimeError("UART write incomplete: %d of %d bytes" % (written, len(payload)))
        return written

    def _uart_any(self) -> int:
        try:
            return self._uart.any()
        except OSError as exc:
            raise RuntimeError("UART availability check failed") from exc

    def _read_response(self, timeout_ms: int = None) -> str:
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be a positive int or None")
        timeout = self._timeout_ms if timeout_ms is None else timeout_ms
        deadline = time.ticks_add(time.ticks_ms(), timeout)
        last_data = None
        response = bytearray()

        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            available = self._uart_any()
            if available:
                try:
                    chunk = self._uart.read(available)
                except OSError as exc:
                    raise RuntimeError("UART read failed") from exc
                if chunk:
                    response.extend(chunk)
                    last_data = time.ticks_ms()
            elif last_data is not None and time.ticks_diff(time.ticks_ms(), last_data) >= self._idle_ms:
                break
            else:
                time.sleep_ms(_POLL_INTERVAL_MS)

        if not response:
            raise RuntimeError("E103-W02 response timeout")
        try:
            text = bytes(response).decode("utf-8")
        except UnicodeError:
            text = "<binary:%s>" % bytes(response).hex()
        self._log("RX: %s" % text)
        return text.strip()

    def _remove_echo(self, response: str, command: str) -> str:
        if response is None or command is None:
            raise ValueError("response and command cannot be None")
        if not isinstance(response, str):
            raise TypeError("response must be str")
        if not isinstance(command, str):
            raise TypeError("command must be str")
        lines = response.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        filtered = []
        removed = False
        for line in lines:
            if not removed and line.strip() == command:
                removed = True
                continue
            if line != "":
                filtered.append(line)
        return "\n".join(filtered).strip()

    def _drain_input(self) -> None:
        try:
            available = self._uart_any()
            if available:
                self._uart.read(available)
        except OSError as exc:
            raise RuntimeError("UART drain failed") from exc

    def _log(self, message: str) -> None:
        if message is None:
            raise ValueError("message cannot be None")
        if not isinstance(message, str):
            raise TypeError("message must be str")
        if self._debug:
            print("[E103W02] %s" % message)

    def deinit(self) -> None:
        """
        释放驱动状态但不关闭外部 UART。Release state without closing UART.

        Returns:
            None: 无返回值。No return value.
        Raises:
            无。None.
        Notes:
            此方法无 UART I/O，且非 ISR 安全。No UART I/O; not ISR-safe.
        """
        self._command_mode = False


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
