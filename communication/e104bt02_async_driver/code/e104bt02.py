# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/18
# @Author  : FreakStudio
# @File    : e104bt02.py
# @Description : EBYTE E104-BT02 UART driver
# @License : MIT

__version__ = "1.3.1"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time

try:
    from micropython import const
except ImportError:

    def const(value: int) -> int:
        return value


# ======================================== 全局变量 ============================================

FRAME_START: int = const(0x3C)
FRAME_END: int = const(0x3E)
DEFAULT_TIMEOUT_MS: int = const(500)
DEFAULT_POLL_INTERVAL_MS: int = const(5)
MAX_FRAME_LEN: int = const(160)

COMMAND_COMBAUD: bytes = b"<COMBAUD>"
COMMAND_BAUD_PREFIX: bytes = b"BAUD"
COMMAND_STOPBIT: bytes = b"<STOPBIT>"
COMMAND_PARITY: bytes = b"<PARITY>"
COMMAND_MNAME: bytes = b"<MNAME>"
COMMAND_NAME_PREFIX: bytes = b"NAME"
COMMAND_FNAME: bytes = b"<FNAME>"
COMMAND_SVER: bytes = b"<SVER>"
COMMAND_HVER: bytes = b"<HVER>"
COMMAND_MSN: bytes = b"<MSN>"
COMMAND_STATE: bytes = b"<STATE>"
COMMAND_MMTU: bytes = b"<MMTU>"
COMMAND_MTU_PREFIX: bytes = b"MTU"
COMMAND_ROLETYPE: bytes = b"<ROLETYPE>"
COMMAND_MAC: bytes = b"<MAC>"
COMMAND_ADVSTATE: bytes = b"<ADVSTATE>"
COMMAND_STARTADV: bytes = b"<STARTADV>"
COMMAND_STOPADV: bytes = b"<STOPADV>"
COMMAND_AGAP: bytes = b"<AGAP>"
COMMAND_ADVGAP_PREFIX: bytes = b"ADVGAP"
COMMAND_RESTORE: bytes = b"<RESTORE>"

ERROR_PAYLOADS: tuple = ("INVALID_ERR", "HT_ERR", "LEN_ERR", "RANGE_ERR")
SUCCESS_OK: str = "OK"
SUPPORTED_BAUDRATES: tuple = (4800, 9600, 19200, 38400, 57600, 115200)

# ======================================== 功能函数 ============================================


def _ticks_ms() -> int:
    return time.ticks_ms()


def _ticks_diff(new: int, old: int) -> int:
    return time.ticks_diff(new, old)


def _sleep_ms(value: int) -> None:
    time.sleep_ms(value)


def bytes_to_hex(data: bytes) -> str:
    """
    将 bytes 转换为空格分隔的十六进制字符串，便于记录硬件通信日志。

    Convert bytes to a space-separated hexadecimal string for communication logs.
    """
    if data is None:
        raise ValueError("data cannot be None")
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes or bytearray")
    return " ".join("%02X" % byte for byte in data)


def mac_bytes_to_text(payload: bytes) -> str:
    """
    将 6 字节 BLE MAC payload 转换为 AA:BB:CC:DD:EE:FF 格式。

    Convert a 6-byte BLE MAC payload to AA:BB:CC:DD:EE:FF format.
    """
    if payload is None:
        raise ValueError("payload cannot be None")
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("payload must be bytes or bytearray")
    if len(payload) != 6:
        raise ValueError("MAC payload must be 6 bytes")
    return ":".join("%02X" % byte for byte in payload)


def _decode_ascii(payload: bytes) -> str:
    if payload is None:
        raise ValueError("payload cannot be None")
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("payload must be bytes or bytearray")
    try:
        return bytes(payload).decode("ascii")
    except UnicodeError as err:
        raise E104BT02FrameError("Response payload is not ASCII: %s" % str(err))


def _strip_frame(frame: bytes) -> bytes:
    if frame is None:
        raise ValueError("frame cannot be None")
    if not isinstance(frame, (bytes, bytearray)):
        raise TypeError("frame must be bytes or bytearray")
    if len(frame) < 2:
        raise E104BT02FrameError("Response frame is too short")
    if frame[0] != FRAME_START or frame[-1] != FRAME_END:
        raise E104BT02FrameError("Response is not a complete E104-BT02 frame")
    return bytes(frame[1:-1])


def _build_at_frame(command_payload: bytes) -> bytes:
    if command_payload is None:
        raise ValueError("command_payload cannot be None")
    if not isinstance(command_payload, (bytes, bytearray)):
        raise TypeError("command_payload must be bytes or bytearray")
    if len(command_payload) < 1:
        raise ValueError("command_payload must not be empty")
    if FRAME_START in command_payload or FRAME_END in command_payload:
        raise ValueError("command_payload cannot contain '<' or '>'")
    return bytes((FRAME_START,)) + bytes(command_payload) + bytes((FRAME_END,))


# ======================================== 自定义类 ============================================


class E104BT02Error(Exception):
    pass


class E104BT02TimeoutError(E104BT02Error):
    pass


class E104BT02FrameError(E104BT02Error):
    pass


class E104BT02ResponseError(E104BT02Error):
    pass


class E104BT02:
    """
    EBYTE E104-BT02 BLE 透明传输模块的 UART 驱动。

    本驱动只负责 UART 协议层，不创建 machine.UART 或 Pin，也不控制 P00/MOD 与 P06/WKP。
    AT 查询方法要求模块已经唤醒并处于配置模式，也就是 P00/MOD 为低电平。
    透明传输方法要求模块处于透明传输模式，也就是 P00/MOD 为高电平。
    当前版本实现经过真实硬件验证的安全查询、AT 帧解析、binary MAC 解析、基础透明 bytes 收发，
    以及常用配置 API 的第一批低/中风险接口。

    Attributes:
        _uart: 外部注入的 MicroPython UART 对象，必须支持 write()、read()、any()。
        _timeout_ms: AT 帧读取默认超时时间，单位 ms；这是驱动实现默认值，不是官方时序规格。
        _max_frame_len: AT 响应帧最大保护长度；这是驱动实现保护值，不是官方协议限制。
        _poll_interval_ms: UART 轮询间隔，单位 ms。

    Methods:
        get_baudrate(): 查询当前 UART baudrate。
        set_baudrate(): 配置模块 UART baudrate，不修改 host UART。
        restore_factory_defaults(): 发送官方 <RESTORE>，仅在收到 <OK> 后返回 True。
        get_stop_bits(): 查询当前 UART stop bits。
        get_parity(): 查询当前 UART parity。
        get_module_name(): 查询模块广播名称。
        get_factory_name(): 查询厂商名称。
        get_software_version(): 查询软件版本。
        get_hardware_version(): 查询硬件版本。
        get_serial_number(): 查询序列号，逻辑返回值会去除尾部 NUL padding。
        get_serial_number_raw(): 查询序列号原始 payload。
        get_state(): 查询当前连接状态。
        get_mtu(): 查询当前 BLE MTU 配置。
        get_role(): 查询当前 BLE role 字符串。
        get_mac(): 查询并格式化 BLE MAC。
        get_mac_raw(): 查询 BLE MAC 原始 6 字节 payload。
        set_module_name(): 配置模块名称。
        set_mtu(): 配置 BLE MTU。
        get_advertising_state(): 查询广播状态。
        start_advertising(): 开启广播。
        stop_advertising(): 停止广播。
        set_advertising_interval(): 配置广播间隔。
        get_advertising_interval(): 查询广播间隔。
        send(): 透明模式下发送 bytes。
        read(): 透明模式下限时读取 bytes。
        read_available(): 透明模式下读取当前 UART 缓冲中已有 bytes。
        any(): 返回 UART 当前可读字节数。
        close()/deinit(): 释放驱动对注入 UART 的引用，不关闭外部 UART 硬件。

    Notes:
        1. AT wire format 已验证为 b"<COMMAND>"，不添加 CR、LF 或 CRLF。
        2. <MAC> 的响应 payload 是 6 字节 binary，不能在底层统一 decode。
        3. P00/MOD 与 P06/WKP 当前硬件不由 RP2040 控制，驱动不会提供虚假的 GPIO API。
        4. 当前真实配置 MNAME=E104-BT02-V5.0、MMTU=100，这可能不同于出厂默认值，不代表故障。

    EBYTE E104-BT02 BLE transparent module UART driver.

    This driver only owns the UART protocol layer. It does not create machine.UART or Pin objects,
    and it does not control P00/MOD or P06/WKP. AT query methods require the module to be awake
    and already in configuration mode, with P00/MOD held low. Transparent data methods require
    transparent transmission mode, with P00/MOD high. This version implements the hardware-verified
    safe queries, AT frame parser, binary MAC parser, basic transparent bytes I/O, and the first
    low/medium-risk common configuration APIs.

    Attributes:
        _uart: Externally injected MicroPython UART object. It must provide write(), read(), and any().
        _timeout_ms: Default AT frame read timeout in milliseconds. This is a driver default, not an official timing spec.
        _max_frame_len: Maximum AT response frame guard length. This is a driver protection limit, not an official protocol limit.
        _poll_interval_ms: UART polling interval in milliseconds.

    Methods:
        get_baudrate(): Query current UART baudrate.
        set_baudrate(): Configure module UART baudrate without modifying the host UART.
        restore_factory_defaults(): Send official <RESTORE> and return True only after <OK> acknowledgment.
        get_stop_bits(): Query current UART stop bits.
        get_parity(): Query current UART parity.
        get_module_name(): Query module advertising name.
        get_factory_name(): Query factory name.
        get_software_version(): Query software version.
        get_hardware_version(): Query hardware version.
        get_serial_number(): Query serial number and strip trailing NUL padding from the logical result.
        get_serial_number_raw(): Query raw serial number payload.
        get_state(): Query connection state.
        get_mtu(): Query current BLE MTU setting.
        get_role(): Query current BLE role string.
        get_mac(): Query and format BLE MAC.
        get_mac_raw(): Query raw 6-byte BLE MAC payload.
        set_module_name(): Configure module name.
        set_mtu(): Configure BLE MTU.
        get_advertising_state(): Query advertising state.
        start_advertising(): Start advertising.
        stop_advertising(): Stop advertising.
        set_advertising_interval(): Configure advertising interval.
        get_advertising_interval(): Query advertising interval.
        send(): Send bytes in transparent mode.
        read(): Read bytes with timeout in transparent mode.
        read_available(): Read bytes already buffered by UART in transparent mode.
        any(): Return current UART readable byte count.
        close()/deinit(): Release this driver reference to the injected UART without closing external hardware.

    Notes:
        1. Verified AT wire format is b"<COMMAND>"; no CR, LF, or CRLF is appended.
        2. <MAC> response payload is 6 binary bytes and must not be decoded at the transport layer.
        3. P00/MOD and P06/WKP are not currently controlled by RP2040 hardware, so fake GPIO APIs are intentionally absent.
        4. The verified live configuration MNAME=E104-BT02-V5.0 and MMTU=100 may differ from factory defaults.
    """

    def __init__(
        self,
        uart: object,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        max_frame_len: int = MAX_FRAME_LEN,
    ) -> None:
        """
        初始化 E104BT02 驱动实例，绑定外部注入的 UART 对象。

        Args:
            uart: 已初始化 UART 对象，必须支持 write()、read()、any()。
            timeout_ms: 默认 AT 响应帧超时时间，单位 ms。
            max_frame_len: AT 响应帧最大保护长度。

        Initialize the E104BT02 driver with an externally created UART object.

        Args:
            uart: Initialized UART object. It must support write(), read(), and any().
            timeout_ms: Default AT response frame timeout in milliseconds.
            max_frame_len: Maximum AT response frame guard length.
        """
        if uart is None:
            raise ValueError("uart cannot be None")
        if not hasattr(uart, "write"):
            raise ValueError("uart object must provide write()")
        if not hasattr(uart, "read"):
            raise ValueError("uart object must provide read()")
        if not hasattr(uart, "any"):
            raise ValueError("uart object must provide any()")
        if isinstance(timeout_ms, bool):
            raise TypeError("timeout_ms must be int")
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be > 0")
        if isinstance(max_frame_len, bool):
            raise TypeError("max_frame_len must be int")
        if not isinstance(max_frame_len, int):
            raise TypeError("max_frame_len must be int")
        if max_frame_len < 8:
            raise ValueError("max_frame_len must be >= 8")

        self._uart = uart
        self._timeout_ms = timeout_ms
        self._max_frame_len = max_frame_len
        self._poll_interval_ms = DEFAULT_POLL_INTERVAL_MS

    def get_baudrate(self, timeout_ms: int = 0) -> int:
        """
        查询当前 UART baudrate。调用前模块必须已唤醒并处于配置模式，P00/MOD 为低电平。

        Query the current UART baudrate. The module must be awake and in configuration mode with P00/MOD low.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return int(self._query_ascii(COMMAND_COMBAUD, timeout_ms))

    def set_baudrate(self, baudrate: int, timeout_ms: int = 0) -> bool:
        """
        配置模块 UART baudrate。成功后调用者必须自行重新配置 host UART。

        Configure module UART baudrate. After success, the caller must reconfigure the host UART.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        if isinstance(baudrate, bool):
            raise TypeError("baudrate must be int")
        if not isinstance(baudrate, int):
            raise TypeError("baudrate must be int")
        if baudrate not in SUPPORTED_BAUDRATES:
            raise ValueError("baudrate must be one of %s" % (repr(SUPPORTED_BAUDRATES),))
        frame = _build_at_frame(COMMAND_BAUD_PREFIX + str(baudrate).encode("ascii"))
        self._execute_ok(frame, timeout_ms)
        return True

    def restore_factory_defaults(self, timeout_ms: int = 0) -> bool:
        """
        Execute the official factory-reset command and wait for the official <OK> acknowledgment.

        The module must already be awake and in configuration mode with P00/MOD low.
        This method returns True only when the module acknowledges <RESTORE> with <OK>.
        It does not prove that all defaults are already activated and does not verify post-reset communication state.
        The caller or test procedure must verify activation timing and resulting default values separately.

        This method does not:
        - control P00/MOD
        - control P06/WKP
        - reconfigure the host UART
        - reboot or power-cycle the module
        - reconnect BLE
        - restore previous user configuration
        """
        # Official command evidence:
        # AT Manual section 4.2 (PDF p7 / footer p8), Datasheet CN section 6.2 (PDF p10 / footer p9).
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        self._execute_ok(COMMAND_RESTORE, timeout_ms)
        return True

    def get_stop_bits(self, timeout_ms: int = 0) -> int:
        """
        查询当前 UART stop bits。调用前模块必须已唤醒并处于配置模式，P00/MOD 为低电平。

        Query the current UART stop bits. The module must be awake and in configuration mode with P00/MOD low.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        text = self._query_ascii(COMMAND_STOPBIT, timeout_ms)
        if text == "STOPBITS1":
            return 1
        if text == "STOPBITS2":
            return 2
        raise E104BT02ResponseError("Unexpected STOPBIT response: %s" % text)

    def get_parity(self, timeout_ms: int = 0) -> str:
        """
        查询当前 UART parity，返回 none/even/odd。调用前模块必须已唤醒并处于配置模式。

        Query current UART parity and return none/even/odd. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        text = self._query_ascii(COMMAND_PARITY, timeout_ms)
        if text == "NOP":
            return "none"
        if text == "EVENP":
            return "even"
        if text == "ODDP":
            return "odd"
        raise E104BT02ResponseError("Unexpected PARITY response: %s" % text)

    def get_module_name(self, timeout_ms: int = 0) -> str:
        """
        查询模块名称。调用前模块必须已唤醒并处于配置模式。

        Query module name. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return self._query_ascii(COMMAND_MNAME, timeout_ms)

    def get_factory_name(self, timeout_ms: int = 0) -> str:
        """
        查询厂商名称。调用前模块必须已唤醒并处于配置模式。

        Query factory name. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return self._query_ascii(COMMAND_FNAME, timeout_ms)

    def get_software_version(self, timeout_ms: int = 0) -> str:
        """
        查询软件版本。调用前模块必须已唤醒并处于配置模式。

        Query software version. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return self._query_ascii(COMMAND_SVER, timeout_ms)

    def get_hardware_version(self, timeout_ms: int = 0) -> str:
        """
        查询硬件版本。调用前模块必须已唤醒并处于配置模式。

        Query hardware version. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return self._query_ascii(COMMAND_HVER, timeout_ms)

    def get_serial_number(self, timeout_ms: int = 0) -> str:
        """
        查询序列号逻辑值。真实硬件观察到响应尾部可能带 NUL，本方法将其作为尾部 padding 去除。

        Query logical serial number. Hardware testing observed a trailing NUL, which this method strips as trailing padding.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return _decode_ascii(self.get_serial_number_raw(timeout_ms).rstrip(b"\x00"))

    def get_serial_number_raw(self, timeout_ms: int = 0) -> bytes:
        """
        查询序列号原始 payload，用于保留包括尾部 NUL 在内的真实响应。

        Query raw serial number payload, preserving the real response including any trailing NUL byte.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return self._query_payload(COMMAND_MSN, timeout_ms)

    def get_state(self, timeout_ms: int = 0) -> str:
        """
        查询连接状态。调用前模块必须已唤醒并处于配置模式。

        Query connection state. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return self._query_ascii(COMMAND_STATE, timeout_ms)

    def get_mtu(self, timeout_ms: int = 0) -> int:
        """
        查询当前 BLE MTU 配置。调用前模块必须已唤醒并处于配置模式。

        Query current BLE MTU setting. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return int(self._query_ascii(COMMAND_MMTU, timeout_ms))

    def get_role(self, timeout_ms: int = 0) -> str:
        """
        查询当前 role 字符串，保留模块实际响应文本。调用前模块必须已唤醒并处于配置模式。

        Query current role string and preserve the module response text. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return self._query_ascii(COMMAND_ROLETYPE, timeout_ms)

    def get_mac(self, timeout_ms: int = 0) -> str:
        """
        查询 BLE MAC 并返回 AA:BB:CC:DD:EE:FF 格式。<MAC> 响应 payload 为 binary bytes。

        Query BLE MAC and return AA:BB:CC:DD:EE:FF format. The <MAC> response payload is binary bytes.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        return mac_bytes_to_text(self.get_mac_raw(timeout_ms))

    def get_mac_raw(self, timeout_ms: int = 0) -> bytes:
        """
        查询 BLE MAC 原始 6 字节 payload。调用前模块必须已唤醒并处于配置模式。

        Query raw 6-byte BLE MAC payload. The module must be awake and in configuration mode.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        payload = self._query_payload(COMMAND_MAC, timeout_ms)
        if len(payload) != 6:
            raise E104BT02ResponseError("MAC payload must be 6 bytes")
        return payload

    def set_module_name(self, name: str, timeout_ms: int = 0) -> bool:
        """
        配置模块名称。官方 <NAMExxx> 参数为最长 18 字节 ASCII 字符串。

        Configure module name. The official <NAMExxx> parameter is an ASCII string up to 18 bytes.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        if name is None:
            raise ValueError("name cannot be None")
        if not isinstance(name, str):
            raise TypeError("name must be str")
        try:
            payload = name.encode("ascii")
        except UnicodeError as err:
            raise ValueError("name must contain only ASCII characters: %s" % str(err))
        if len(payload) < 1:
            raise ValueError("name must not be empty")
        if len(payload) > 18:
            raise ValueError("name must be <= 18 ASCII bytes")
        self._execute_ok(_build_at_frame(COMMAND_NAME_PREFIX + payload), timeout_ms)
        return True

    def set_mtu(self, mtu: int, timeout_ms: int = 0) -> bool:
        """
        配置 BLE MTU。官方 <MTUx> 参数范围为 20-128，下一次 BLE 连接生效。

        Configure BLE MTU. The official <MTUx> range is 20-128 and takes effect on the next BLE connection.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        if isinstance(mtu, bool):
            raise TypeError("mtu must be int")
        if not isinstance(mtu, int):
            raise TypeError("mtu must be int")
        if mtu < 20 or mtu > 128:
            raise ValueError("mtu must be in range 20..128")
        self._execute_ok(_build_at_frame(COMMAND_MTU_PREFIX + str(mtu).encode("ascii")), timeout_ms)
        return True

    def get_advertising_state(self, timeout_ms: int = 0) -> str:
        """
        查询广播状态，返回 on/off。官方响应为 <ADVON> 或 <ADVOFF>。

        Query advertising state and return on/off. Official responses are <ADVON> or <ADVOFF>.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        text = self._query_ascii(COMMAND_ADVSTATE, timeout_ms)
        if text == "ADVON":
            return "on"
        if text == "ADVOFF":
            return "off"
        raise E104BT02ResponseError("Unexpected ADVSTATE response: %s" % text)

    def start_advertising(self, timeout_ms: int = 0) -> bool:
        """
        开启广播。官方命令为 <STARTADV>，成功响应为 <OK>。

        Start advertising. The official command is <STARTADV> and the success response is <OK>.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        self._execute_ok(COMMAND_STARTADV, timeout_ms)
        return True

    def stop_advertising(self, timeout_ms: int = 0) -> bool:
        """
        停止广播。官方命令为 <STOPADV>，成功响应为 <OK>。

        Stop advertising. The official command is <STOPADV> and the success response is <OK>.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        self._execute_ok(COMMAND_STOPADV, timeout_ms)
        return True

    def set_advertising_interval(self, interval_units: int, timeout_ms: int = 0) -> bool:
        """
        配置广播间隔。官方 <ADVGAPxxx> 参数范围为 32-16000，对应 20 ms-10 s。

        Configure advertising interval. The official <ADVGAPxxx> range is 32-16000, corresponding to 20 ms-10 s.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        if isinstance(interval_units, bool):
            raise TypeError("interval_units must be int")
        if not isinstance(interval_units, int):
            raise TypeError("interval_units must be int")
        if interval_units < 32 or interval_units > 16000:
            raise ValueError("interval_units must be in range 32..16000")
        frame = _build_at_frame(COMMAND_ADVGAP_PREFIX + str(interval_units).encode("ascii"))
        self._execute_ok(frame, timeout_ms)
        return True

    def get_advertising_interval(self, timeout_ms: int = 0) -> int:
        """
        查询广播间隔，返回官方 interval units 整数。官方响应示例为 <A1600>。

        Query advertising interval and return official interval units as an integer. The official response example is <A1600>.
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        text = self._query_ascii(COMMAND_AGAP, timeout_ms)
        if not text.startswith("A"):
            raise E104BT02ResponseError("Unexpected AGAP response: %s" % text)
        try:
            return int(text[1:])
        except ValueError:
            raise E104BT02ResponseError("Unexpected AGAP response: %s" % text)

    def send(self, data: bytes) -> int:
        """
        在透明传输模式下发送 bytes。调用前用户必须保证 P00/MOD 为高电平，且 BLE 连接状态符合应用需求。

        Send bytes in transparent mode. The user must ensure P00/MOD is high and BLE connection state matches the application need.
        """
        if data is None:
            raise ValueError("data cannot be None")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        if len(data) < 1:
            raise ValueError("data must not be empty")
        try:
            written = self._require_uart().write(data)
        except OSError as err:
            raise E104BT02Error("UART write failed: %s" % str(err))
        if written is None:
            return len(data)
        if written != len(data):
            raise E104BT02Error("UART write incomplete: wrote %s of %s bytes" % (written, len(data)))
        return written

    def read(self, max_bytes: int = 0, timeout_ms: int = 0) -> bytes:
        """
        在透明传输模式下限时读取 bytes。无数据时返回 b""，不会自动 decode。

        Read bytes with timeout in transparent mode. Returns b"" when no data arrives and never decodes automatically.
        """
        if max_bytes < 0:
            raise ValueError("max_bytes must be >= 0")
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        timeout = self._resolve_timeout(timeout_ms)
        start = _ticks_ms()
        uart = self._require_uart()

        while _ticks_diff(_ticks_ms(), start) < timeout:
            count = uart.any()
            if count:
                if max_bytes > 0 and count > max_bytes:
                    count = max_bytes
                chunk = uart.read(count)
                if chunk:
                    return bytes(chunk)
            _sleep_ms(self._poll_interval_ms)
        return b""

    def read_available(self) -> bytes:
        """
        读取当前 UART 缓冲中已经存在的透明传输 bytes；无数据时返回 b""。

        Read transparent bytes already buffered by UART. Returns b"" when no data is available.
        """
        uart = self._require_uart()
        count = uart.any()
        if count < 0:
            raise E104BT02Error("UART any() returned a negative value")
        if count == 0:
            return b""
        chunk = uart.read(count)
        if not chunk:
            return b""
        return bytes(chunk)

    def any(self) -> int:
        """
        返回 UART 当前可读字节数，用于透明传输轮询。

        Return current UART readable byte count for transparent transfer polling.
        """
        uart = self._require_uart()
        count = uart.any()
        if count < 0:
            raise E104BT02Error("UART any() returned a negative value")
        return count

    def deinit(self) -> None:
        """
        释放驱动对注入 UART 的引用；不关闭 UART 硬件，因为 UART 生命周期由调用者管理。

        Release this driver reference to the injected UART without closing the UART hardware.
        """
        uart = self._uart
        if uart is None:
            return
        self._uart = None

    def close(self) -> None:
        """
        deinit() 的别名，便于应用代码使用 close 语义。

        Alias of deinit() for applications that prefer close semantics.
        """
        self.deinit()

    def _require_uart(self) -> object:
        if self._uart is None:
            raise E104BT02Error("UART is not available")
        return self._uart

    def _resolve_timeout(self, timeout_ms: int) -> int:
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        if timeout_ms == 0:
            return self._timeout_ms
        return timeout_ms

    def _send_at_frame(self, frame: bytes) -> int:
        if frame is None:
            raise ValueError("frame cannot be None")
        if not isinstance(frame, (bytes, bytearray)):
            raise TypeError("frame must be bytes or bytearray")
        if len(frame) < 2:
            raise ValueError("frame must include start and end bytes")
        if frame[0] != FRAME_START or frame[-1] != FRAME_END:
            raise ValueError("frame must start with '<' and end with '>'")
        try:
            written = self._require_uart().write(frame)
        except OSError as err:
            raise E104BT02Error("UART write failed: %s" % str(err))
        if written is None:
            return len(frame)
        if written != len(frame):
            raise E104BT02Error("UART write incomplete: wrote %s of %s bytes" % (written, len(frame)))
        return written

    def _read_at_frame(self, timeout_ms: int = 0) -> bytes:
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        timeout = self._resolve_timeout(timeout_ms)
        start_time = _ticks_ms()
        frame = bytearray()
        in_frame = False
        uart = self._require_uart()

        while _ticks_diff(_ticks_ms(), start_time) < timeout:
            try:
                count = uart.any()
                if count:
                    chunk = uart.read(count)
                else:
                    chunk = None
            except OSError as err:
                raise E104BT02Error("UART read failed: %s" % str(err))

            if not chunk:
                _sleep_ms(self._poll_interval_ms)
                continue

            for byte in chunk:
                if not in_frame:
                    if byte == FRAME_START:
                        in_frame = True
                        frame = bytearray()
                        frame.append(byte)
                    continue

                frame.append(byte)
                if len(frame) > self._max_frame_len:
                    raise E104BT02FrameError("AT response frame exceeded driver max_frame_len")
                if byte == FRAME_END:
                    return bytes(frame)

        if in_frame:
            raise E104BT02TimeoutError("No complete E104-BT02 AT frame before timeout. Ensure the module is awake and P00/MOD is low.")
        raise E104BT02TimeoutError("No valid E104-BT02 AT response. Ensure the module is awake and P00/MOD is low.")

    def _query_payload(self, frame: bytes, timeout_ms: int = 0) -> bytes:
        if frame is None:
            raise ValueError("frame cannot be None")
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        self._flush_input()
        self._send_at_frame(frame)
        return _strip_frame(self._read_at_frame(timeout_ms))

    def _query_ascii(self, frame: bytes, timeout_ms: int = 0) -> str:
        if frame is None:
            raise ValueError("frame cannot be None")
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        text = _decode_ascii(self._query_payload(frame, timeout_ms))
        if text in ERROR_PAYLOADS:
            raise E104BT02ResponseError("Module returned error response: %s" % text)
        return text

    def _execute_ok(self, frame: bytes, timeout_ms: int = 0) -> None:
        text = self._query_ascii(frame, timeout_ms)
        if text != SUCCESS_OK:
            raise E104BT02ResponseError("Unexpected success response: %s" % text)

    def _flush_input(self, timeout_ms: int = 80) -> None:
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        uart = self._require_uart()
        overall_start = _ticks_ms()
        quiet_start = overall_start
        overall_timeout_ms = self._timeout_ms
        while _ticks_diff(_ticks_ms(), overall_start) < overall_timeout_ms:
            count = uart.any()
            if count:
                chunk = uart.read(count)
                if chunk:
                    quiet_start = _ticks_ms()
                    continue
            if _ticks_diff(_ticks_ms(), quiet_start) >= timeout_ms:
                return
            _sleep_ms(self._poll_interval_ms)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序 ============================================
