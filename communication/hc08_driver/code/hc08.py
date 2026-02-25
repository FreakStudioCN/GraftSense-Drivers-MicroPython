# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/6 下午10:12
# @Author  : ben0i0d
# @File    : hc08.py
# @Description : hc08 bluetooth驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class HC08:
    """
    HC08 BLE 模块驱动类，支持主从一体式蓝牙通信，基于 UART 接口进行 AT 命令控制与透传通信。
    提供角色切换、名称/地址/波特率/射频功率等参数配置接口，
    同时支持低功耗模式控制与透明数据传输。

    Attributes:
        _uart (UART): MicroPython UART 实例，用于与 HC08 模块通信。
        name (str): 当前蓝牙名称。
        role (int): 当前模块角色（主机/从机，使用 Role 常量）。
        baud (int): 当前串口波特率。
        addr (str): 蓝牙地址（12位十六进制字符串）。
        pin (str): PIN 码。
        version (str): 固件版本信息。
        rfpm (int): 射频功率（dBm）。
        cont (int): 可连接性（可连接/不可连接，使用 CONT 常量）。
        mode (int): 功耗模式（仅从机，使用 MODE 常量）。

        Role: 定义主从角色常量（SLAVE=0，MASTER=1）。
        RFPM: 定义射频功率常量（+4/0/-6/-23 dBm）。
        MODE: 功耗模式常量（FULL/1/2/3）。
        CONT: 可连接性常量（CONNECTABLE / NONCONNECTABLE）。
        BAUD: 波特率常量（1200–115200）。
        Parity: 校验位常量（NONE/EVEN/ODD）。

    Methods:
        __init__(uart, rx_timeout_ms=600):
            初始化驱动类，绑定 UART 并设置默认参数。
        check():
            发送 AT 检测通信是否正常。
        get_rx():
            查询基本参数（Name, Role, Baud, Addr, PIN）。
        factory_default():
            恢复出厂设置。
        reset():
            模块重启。
        get_version():
            查询固件版本。
        set_role(role) / get_role():
            设置/查询模块角色。
        set_name(name) / get_name():
            设置/查询蓝牙名称。
        set_addr(addr12) / get_addr():
            设置/查询蓝牙地址。
        set_rfpm(rfpm) / get_rfpm():
            设置/查询射频功率。
        set_baud(baud, parity) / get_baud():
            设置/查询波特率与校验位。
        clear():
            主机清除绑定的从机地址。
        send_data(data):
            透传模式发送数据。
        recv_data(timeout_ms=None, min_bytes=1):
            接收透传数据。
        recv_until(terminator=b'\\n', timeout_ms=None):
            接收直到遇到终止符。
        wake_from_sleep():
            唤醒低功耗模式下的模块。
        _valid_name(name):
            检查蓝牙名称是否合法。
        _valid_addr(addr12):
            检查蓝牙地址是否合法。
        _is_allowed_constant(value, allowed_tuple):
            检查参数值是否在允许的常量集合中。

    ==========================================

    HC08 BLE driver class supporting master/slave integrated Bluetooth communication.
    Operates via UART AT commands, providing parameter configuration
    (role, name, address, baud rate, RF power, etc.),
    power saving mode control, and transparent data transmission.

    Attributes:
        _uart (UART): MicroPython UART instance for communication.
        name (str): Current Bluetooth name.
        role (int): Current module role (MASTER/SLAVE).
        baud (int): Current UART baud rate.
        addr (str): Bluetooth address (12-char hex string).
        pin (str): PIN code.
        version (str): Firmware version string.
        rfpm (int): RF power (dBm).
        cont (int): Connectivity mode (CONNECTABLE/NONCONNECTABLE).
        mode (int): Power saving mode (slave only).

        Role: Master/Slave role constants (SLAVE=0, MASTER=1).
        RFPM: RF power constants (+4/0/-6/-23 dBm).
        MODE: Power saving mode constants (FULL/1/2/3).
        CONT: Connectivity constants (CONNECTABLE / NONCONNECTABLE).
        BAUD: Baud rate constants (1200–115200).
        Parity: Parity constants (NONE/EVEN/ODD).

    Methods:
        __init__(uart, rx_timeout_ms=600):
            Initialize driver with UART and defaults.
        check():
            Send AT and check communication.
        get_rx():
            Query basic params (Name, Role, Baud, Addr, PIN).
        factory_default():
            Restore factory settings.
        reset():
            Reset the module.
        get_version():
            Query firmware version.
        set_role(role) / get_role():
            Set/get module role.
        set_name(name) / get_name():
            Set/get Bluetooth name.
        set_addr(addr12) / get_addr():
            Set/get Bluetooth address.
        set_rfpm(rfpm) / get_rfpm():
            Set/get RF power.
        set_baud(baud, parity) / get_baud():
            Set/get baud rate and parity.
        clear():
            Master clears paired slave addresses.
        send_data(data):
            Send data in transparent mode.
        recv_data(timeout_ms=None, min_bytes=1):
            Receive transparent data.
        recv_until(terminator=b'\\n', timeout_ms=None):
            Receive until terminator encountered.
        wake_from_sleep():
            Wake up module from low-power mode.
        _valid_name(name):
            Validate Bluetooth name.
        _valid_addr(addr12):
            Validate Bluetooth address.
        _is_allowed_constant(value, allowed_tuple):
            Validate parameter against allowed constants.
    """

    # 角色常量
    Role = {"SLAVE": 0, "MASTER": 1}

    # 射频功率
    RFPM = {"RFPM_4DBM": 4, "RFPM_0DBM": 0, "RFPM_NEG6DB": -6, "RFPM_NEG23DB": -23}

    # 功耗模式（仅从机）
    MODE = {"MODE_FULL": 0, "MODE_1": 1, "MODE_2": 2, "MODE_3": 3}

    # 可连接性
    CONT = {"CONT_CONNECTABLE": 0, "CONT_NONCONNECTABLE": 1}

    # 波特率
    BAUD = {
        "BAUD_1200": 1200,
        "BAUD_2400": 2400,
        "BAUD_4800": 4800,
        "BAUD_9600": 9600,
        "BAUD_19200": 19200,
        "BAUD_38400": 38400,
        "BAUD_57600": 57600,
        "BAUD_115200": 115200,
    }

    # AT指令对应的参数映射
    rfpm_param = {4: 0, 0: 1, -6: 2, -23: 3}

    # 校验位映射
    PARITY_NONE = ("N",)
    PARITY_EVEN = ("E",)
    PARITY_ODD = "O"

    def __init__(self, uart, rx_timeout_ms=600):
        """
        初始化实例，绑定 UART 接口并配置默认参数。

        Args:
            uart: 已初始化的 UART 对象，必须支持 write()/any()/read() 方法。
            rx_timeout_ms (int, 可选): 接收超时时间，单位为毫秒，默认 600 ms。

        ---
        Initialize instance by binding UART interface and setting default parameters.

        Args:
            uart: Initialized UART object, must support write()/any()/read() methods.
            rx_timeout_ms (int, optional): Receive timeout in milliseconds, default 600 ms.
        """

        self._uart = uart
        # 设置uart.timeout 指定等待第一个字符的时间（以毫秒为单位）
        self.rx_timeout_ms = rx_timeout_ms
        # 蓝牙名称、角色、波特率、地址、PIN码、版本、射频功率、连接性、功耗模式
        self.name = None
        self.role = None
        self.baud = None
        self.addr = None
        self.pin = None
        self.version = None
        self.rfpm = None
        self.cont = None
        self.mode = None

    def _send(self, cmd: bytes) -> (bool, None | str):
        """
        向 UART 发送命令（不自动附加换行）。

        Args:
            cmd (bytes): 要发送的字节命令。

        Returns:
            (bool, str|None): (True, None) 表示成功，(False, 错误信息) 表示失败。

        ---
        Send a command to UART (without appending newline).

        Args:
            cmd (bytes): Command bytes to send.

        Returns:
            (bool, str|None): (True, None) if success, (False, error message) if failed.
        """

        try:
            self._uart.write(cmd)
            # 50ms 确保回传稳定
            time.sleep(0.05)
            return (True, None)
        except Exception:
            return (False, "send error")

    def _recv(self, timeout_ms=None) -> (bool, str | None):
        """
        从 UART 读取数据，支持超时，自动解码为字符串。

        Args:
            timeout_ms (int|None): 超时时间（毫秒），默认为 UART 实例的超时。

        Returns:
            (bool, str|None): (True, 解码字符串) 表示成功，
                              (False, None/错误信息) 表示超时或解码失败。

        ---
        Receive data from UART with timeout, decode into string.

        Args:
            timeout_ms (int|None): Timeout in milliseconds, defaults to UART timeout.

        Returns:
            (bool, str|None): (True, decoded string) if success,
                              (False, None/error message) if timeout or decode fails.
        """

        try:
            if self._uart.any():
                resp = self._uart.read()
            if resp == None:
                return False, "RECV NONE"
            return True, resp.decode("utf-8").strip()
        except Exception:
            return (False, "recv error")


    # AT指令
    def check(self) -> (bool, str | None):
        """
        发送 AT 指令，检测模块是否正常响应。

        Returns:
            (bool, str|None): (True, "OK") 表示模块正常，
                              (False, 错误信息) 表示失败。

        ---
        Send AT command to check if module responds.

        Returns:
            (bool, str|None): (True, "OK") if module is responsive,
                              (False, error message) otherwise.
        """

        ok, err = self._send(b"AT")
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        return (resp == "OK"), resp

    def get_rx(self) -> (bool, str | None):
        """
        发送 AT+RX，查询并解析基本参数（Name, Role, Baud, Addr, PIN）。

        Returns:
            (bool, str|None): (True, 原始响应) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 name, role, baud, addr, pin。

        ---
        Send AT+RX to query and parse basic parameters (Name, Role, Baud, Addr, PIN).

        Returns:
            (bool, str|None): (True, raw response) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attributes name, role, baud, addr, pin upon success.
        """

        ok, err = self._send(b"AT+RX")
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        status = {}
        for line in resp.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                status[key.strip()] = value.strip()
        return True, status

    def factory_default(self) -> (bool, str | None):
        """
        发送 AT+DEFAULT 恢复出厂设置。

        Returns:
            (bool, str|None): (True, 响应或 "rebooting") 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            模块会自动重启（约 200 ms）。

        ---
        Send AT+DEFAULT to restore factory settings.

        Returns:
            (bool, str|None): (True, response or "rebooting") if success,
                              (False, error message) otherwise.

        Notes:
            Module reboots automatically (~200 ms).
        """

        ok, err = self._send(b"AT+DEFAULT")
        if not ok:
            return False, err
        ok, resp = self._recv()
        time.sleep(0.2)
        return (ok, resp or "params redefault complete")

    def reset(self) -> (bool, str | None):
        """
        发送 AT+RESET 重启模块。

        Returns:
            (bool, str|None): (True, 响应或 "reset (no echo)") 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            某些固件无回显，但仍视为成功。

        ---
        Send AT+RESET to reboot the module.

        Returns:
            (bool, str|None): (True, response or "reset (no echo)") if success,
                              (False, error message) otherwise.

        Notes:
            Some firmware may not echo but still reboot successfully.
        """

        ok, err = self._send(b"AT+RESET")
        if not ok:
            return False, err
        ok, resp = self._recv()
        return True, resp or "reset complete"

    def get_version(self) -> (bool, str | None):
        """
        发送 AT+VERSION 查询固件版本。

        Returns:
            (bool, str|None): (True, 版本字符串) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 version。

        ---
        Send AT+VERSION to query firmware version.

        Returns:
            (bool, str|None): (True, version string) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute version upon success.
        """
        ok, err = self._send(b"AT+VERSION")
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.version = resp
        return True, resp

    def set_role(self, role: int) -> (bool, str | None):
        """
        设置模块角色（主机/从机）。

        Args:
            role (int): 角色常量，使用 Role.MASTER 或 Role.SLAVE。

        Returns:
            (bool, str|None): (True, 响应) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 role。

        ---
        Set module role (master/slave).

        Args:
            role (int): Role constant, use Role.MASTER or Role.SLAVE.

        Returns:
            (bool, str|None): (True, response) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute role upon success.
        """

        if role not in (HC08.Role.values()):
            return False, "invalid role"
        cmd = b"AT+ROLE=" + (b"S" if role == HC08.Role["SLAVE"] else b"M")
        ok, err = self._send(cmd)
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.role = role
        return True, resp

    def get_role(self) -> (bool, str | None):
        """
        查询模块当前角色。

        Returns:
            (bool, str|None): (True, 响应字符串) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 role。

        ---
        Query current module role.

        Returns:
            (bool, str|None): (True, response string) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute role upon success.
        """

        ok, err = self._send(b"AT+ROLE=?")
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.role = HC08.Role["MASTER"] if "M" in resp else HC08.Role["SLAVE"]
        return True, resp

    def set_name(self, name: str) -> (bool, str | None):
        """
        设置蓝牙名称。

        Args:
            name (str): 蓝牙名称，最长 12 字符，支持中文。

        Returns:
            (bool, str|None): (True, 响应) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 name。

        ---
        Set Bluetooth name.

        Args:
            name (str): Bluetooth name, up to 12 characters, UTF-8 supported.

        Returns:
            (bool, str|None): (True, response) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute name upon success.
        """
        if len(name) > 12:
            return False, "name invalid, longer than 12"
        ok, err = self._send(f"AT+NAME={name}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.name = name
        return True, resp

    def get_name(self) -> (bool, str | None):
        """
        查询蓝牙名称。

        Returns:
            (bool, str|None): (True, 名称字符串) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 name。

        ---
        Query Bluetooth name.

        Returns:
            (bool, str|None): (True, name string) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute name upon success.
        """

        ok, err = self._send(b"AT+NAME=?")
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.name = resp
        return True, resp

    def set_addr(self, addr12: str) -> (bool, str | None):
        """
        设置蓝牙地址。

        Args:
            addr12 (str): 12 位大写十六进制字符串。

        Returns:
            (bool, str|None): (True, 响应) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 addr。

        ---
        Set Bluetooth address.

        Args:
            addr12 (str): 12-character uppercase hexadecimal string.

        Returns:
            (bool, str|None): (True, response) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute addr upon success.
        """

        ok, err = self._valid_addr(addr12)
        if not ok:
            return False, err
        cmd = f"AT+ADDR={addr12}".encode()
        ok, err = self._send(cmd)
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.addr = addr12
        return True, resp

    def get_addr(self) -> (bool, str | None):
        """
        查询蓝牙地址。

        Returns:
            (bool, str|None): (True, 地址字符串) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 addr。

        ---
        Query Bluetooth address.

        Returns:
            (bool, str|None): (True, address string) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute addr upon success.
        """

        ok, err = self._send(b"AT+ADDR=?")
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.addr = resp
        return True, resp

    def set_rfpm(self, rfpm: int) -> (bool, str | None):
        """
        设置射频功率。

        Args:
            rfpm (int): 功率值，允许值为 (4, 0, -6, -23)。

        Returns:
            (bool, str|None): (True, 响应) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 rfpm。

        ---
        Set RF power.

        Args:
            rfpm (int): RF power level, allowed values (4, 0, -6, -23).

        Returns:
            (bool, str|None): (True, response) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute rfpm upon success.
        """

        if rfpm not in (4, 0, -6, -23):
            return False, "invalid rfpm"

        cmd = f"AT+RFPM={HC08.rfpm_param[rfpm]}".encode()
        ok, err = self._send(cmd)
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.rfpm = rfpm
        return True, resp

    def get_rfpm(self) -> (bool, str | None):
        """
        查询射频功率。

        Returns:
            (bool, str|None): (True, 响应字符串) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 rfpm。

        ---
        Query RF power.

        Returns:
            (bool, str|None): (True, response string) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute rfpm upon success.
        """

        ok, err = self._send(b"AT+RFPM=?")
        if not ok:
            return False, err
        ok, resp = self._recv()
        self.rfpm = resp
        return True, resp

    def set_baud(self, baud_rate: int, parity: str) -> (bool, str | None):
        """
        设置串口波特率与校验位。

        Args:
            baud_rate (int): 波特率，必须为允许值之一。
            parity (int, 可选): 校验方式，使用 Parity 常量。

        Returns:
            (bool, str|None): (True, 响应) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 baud。外部需同步调整 UART 配置。

        ---
        Set UART baud rate and parity.

        Args:
            baud_rate (int): Baud rate, must be one of the allowed values.
            parity (int, optional): Parity mode, use Parity constants.

        Returns:
            (bool, str|None): (True, response) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute baud upon success. External UART config must be updated accordingly.
        """

        if baud_rate not in (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200):
            return False, "invalid baud"
        if not parity in (HC08.PARITY_NONE, HC08.PARITY_EVEN, HC08.PARITY_ODD):
            return False, "invalid parity"
        cmd = f"AT+BAUD={baud_rate},{parity}".encode()
        ok, err = self._send(cmd)
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        self.baud = baud_rate
        return True, resp

    def get_baud(self) -> (bool, str | None):
        """
        查询串口波特率。

        Returns:
            (bool, str|None): (True, 响应字符串) 表示成功，
                              (False, 错误信息) 表示失败。

        Notes:
            成功时会更新实例属性 baud。

        ---
        Query UART baud rate.

        Returns:
            (bool, str|None): (True, response string) if success,
                              (False, error message) otherwise.

        Notes:
            Updates instance attribute baud upon success.
        """

        ok, err = self._send(b"AT+BAUD=?")
        if not ok:
            return False, err
        ok, resp = self._recv()
        if not ok:
            return False, "no response"
        try:
            rate, *_ = resp.split(",")
            self.baud = int(rate)
            return True, resp
        except:
            return False, "parse error"

    def clear(self) -> (bool, str | None):
        """
        主机模式下清除已记录的从机地址。

        Returns:
            (bool, str|None): (True, 响应或 "cleared") 表示成功，
                              (False, 错误信息) 表示失败。

        ---
        Clear recorded slave addresses (master mode only).

        Returns:
            (bool, str|None): (True, response or "cleared") if success,
                              (False, error message) otherwise.
        """

        ok, err = self._send(b"AT+CLEAR")
        if not ok:
            return False, err
        ok, resp = self._recv()
        return True, resp or "cleared"

    # 透传方法
    def send_data(self, data) -> (bool, int | str):
        """
        发送透传数据。

        Args:
            data (bytes|str): 待发送数据。

        Returns:
            (bool, int|str): (True, 写入字节数) 表示成功，
                              (False, 错误信息) 表示失败。

        ---
        Send transparent data.

        Args:
            data (bytes|str): Data to send.

        Returns:
            (bool, int|str): (True, number of bytes written) if success,
                              (False, error message) otherwise.
        """

        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, (bytes, bytearray)):
            return False, "invalid type: data must be str or bytes"
        try:
            n = self._uart.write(data)
            return True, n
        except Exception as e:
            return False, f"uart error: {e}"

    def recv_data(self, timeout_ms=None, min_bytes=1) -> (bool, bytes | None):
        """
        阻塞接收透传数据。

        Args:
            timeout_ms (int|None): 超时时间（毫秒）。
            min_bytes (int): 最小接收字节数。

        Returns:
            (bool, bytes|None): (True, 数据) 表示成功，
                                (False, None/错误信息) 表示失败。

        ---
        Receive transparent data (blocking).

        Args:
            timeout_ms (int|None): Timeout in milliseconds.
            min_bytes (int): Minimum bytes to receive.

        Returns:
            (bool, bytes|None): (True, data) if success,
                                (False, None/error message) otherwise.
        """

        deadline = time.ticks_add(time.ticks_ms(), timeout_ms or self._uart.timeout)
        buf = b""
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self._uart.any():
                buf += self._uart.read()
                if len(buf) >= min_bytes:
                    return True, buf
            else:
                time.sleep_ms(10)
        return False, None

    def recv_until(self, terminator=b"\n", timeout_ms=None) -> (bool, bytes | None):
        """
        接收数据直到遇到终止符或超时。

        Args:
            terminator (bytes): 终止符，默认为换行符。
            timeout_ms (int|None): 超时时间（毫秒）。

        Returns:
            (bool, bytes|None): (True, 数据) 表示成功，
                                (False, None) 表示超时。

        ---
        Receive data until terminator or timeout.

        Args:
            terminator (bytes): Terminator, default is newline.
            timeout_ms (int|None): Timeout in milliseconds.

        Returns:
            (bool, bytes|None): (True, data) if success,
                                (False, None) if timeout.
        """

        deadline = time.ticks_add(time.ticks_ms(), timeout_ms or self._uart.timeout)
        buf = b""
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self._uart.any():
                c = self._uart.read(1)
                if c:
                    buf += c
                    if buf.endswith(terminator):
                        return True, buf
            else:
                time.sleep_ms(10)
        return False, None

    def wake_from_sleep(self) -> (bool, str):
        """
        唤醒处于低功耗模式的模块。

        Returns:
            (bool, str): (True, "woke") 表示成功，
                         (False, 错误信息) 表示失败。

        Notes:
            根据手册要求，发送 10 个 0xFF 字节。

        ---
        Wake module from low-power mode.

        Returns:
            (bool, str): (True, "woke") if success,
                         (False, error message) otherwise.

        Notes:
            Sends 10 bytes of 0xFF as per datasheet recommendation.
        """

        try:
            self._uart.write(b"\xff" * 10)
            return True, "woke"
        except Exception as e:
            return False, f"uart error: {e}"

    # 辅助函数
    def _valid_name(self, name) -> (bool, str | None):
        """
        检查蓝牙名称是否合法。

        Args:
            name (str): 蓝牙名称。

        Returns:
            (bool, str|None): (True, None) 表示合法，
                              (False, 错误信息) 表示非法。

        ---
        Validate Bluetooth name.

        Args:
            name (str): Bluetooth name.

        Returns:
            (bool, str|None): (True, None) if valid,
                              (False, error message) if invalid.
        """

        if not isinstance(name, str):
            return False, "invalid type: name must be str"
        if not (1 <= len(name) <= 12):
            return False, "invalid name: must be 1~12 chars"
        return True, None

    def _valid_addr(self, addr12) -> (bool, str | None):
        """
        检查蓝牙地址是否合法。

        Args:
            addr12 (str): 蓝牙地址字符串。

        Returns:
            (bool, str|None): (True, None) 表示合法，
                              (False, 错误信息) 表示非法。

        ---
        Validate Bluetooth address.

        Args:
            addr12 (str): Bluetooth address string.

        Returns:
            (bool, str|None): (True, None) if valid,
                              (False, error message) if invalid.
        """

        if not isinstance(addr12, str):
            return False, "invalid type: addr must be str"
        if len(addr12) != 12:
            return False, "invalid addr: must be 12 chars"
        if not all(c in "0123456789ABCDEF" for c in addr12):
            return False, "invalid addr: must be uppercase hex"
        return True, None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
