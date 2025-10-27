# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:00
# @Author  : 侯钧瀚
# @File    : r60abd1.py
# @Description : r60abd1毫米波驱动 for micropython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.2.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

#导入 time 提供延时与时间控制
import time

import machine

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def _u16_be(b0, b1):
    """
    无符号 16 位整数（大端）。

    Args:
        b0 (int): 高字节。
        b1 (int): 低字节。

    Returns:
        int: 组合后的无符号整数。
    ==========================================
    Unsigned 16-bit big-endian integer.

    Args:
        b0 (int): High byte.
        b1 (int): Low byte.

    Returns:
        int: Combined unsigned integer.
    """
    return ((b0 & 0xFF) << 8) | (b1 & 0xFF)


def _s16_be(b0, b1):
    """
    有符号 16 位整数（大端）。

    Args:
        b0 (int): 高字节。
        b1 (int): 低字节。

    Returns:
        int: 组合后的有符号整数。
    ==========================================
    Signed 16-bit big-endian integer.

    Args:
        b0 (int): High byte.
        b1 (int): Low byte.

    Returns:
        int: Combined signed integer.
    """
    v = _u16_be(b0, b1)
    return v - 0x10000 if (v & 0x8000) else v


def _q_u8(self, ctl, cmd):
    """
    通用查询：返回 1 字节无符号整数。

    Args:
        ctl (int): 控制字节。
        cmd (int): 命令字节。

    Returns:
        int | None: 无符号整数 (0–255)，查询失败返回 None。
    ==========================================
    Generic query: return 1-byte unsigned integer.

    Args:
        ctl (int): Control byte.
        cmd (int): Command byte.

    Returns:
        int | None: Unsigned integer (0–255), or None if query failed.
    """
    data = self.query_and_wait(ctl, cmd, b"\x0F")
    if not data:
        return None
    return data[0]


def _q_u16(self, ctl, cmd):
    """
    通用查询：返回 2 字节无符号整数（大端）。

    Args:
        ctl (int): 控制字节。
        cmd (int): 命令字节。

    Returns:
        int | None: 无符号整数，查询失败返回 None。
    ==========================================
    Generic query: return 2-byte unsigned integer (big-endian).

    Args:
        ctl (int): Control byte.
        cmd (int): Command byte.

    Returns:
        int | None: Unsigned integer, or None if query failed.
    """
    data = self.query_and_wait(ctl, cmd, b"\x0F")
    if data is None or len(data) < 2:
        return None
    return self._u16_be(data[0], data[1])


def _q_wave(self, ctl, cmd):
    """
    通用查询：返回波形数组。

    Args:
        ctl (int): 控制字节。
        cmd (int): 命令字节。

    Returns:
        list[int] | None: 波形数组，查询失败返回 None。
    ==========================================
    Generic query: return waveform data.

    Args:
        ctl (int): Control byte.
        cmd (int): Command byte.

    Returns:
        list[int] | None: Waveform as a list of integers, or None if query failed.
    """
    data = self.query_and_wait(ctl, cmd, b"\x0F")
    if data is None:
        return None
    return list(data)

# ======================================== 自定义类 ============================================

class R60ABD1:
    """
    该类提供了对 R60ABD1 毫米波雷达模块的协议解析与高层接口封装，支持通过 UART 与模块通信完成存在检测、运动参数、距离、三维位置、心率、睡眠等信息的查询与控制。
    注意：模块返回值有物理与协议范围限制，超出或异常情况将返回 None。

    Attributes:
        uart (UART): 已初始化的 UART 实例，用于与模块通信（必须由外部创建并传入）。
        _control (int): 内部使用的默认控制字节（例：0x80）。
        _timeout_ms (int): 查询/接收超时时间，单位毫秒。
        _rx_buf (bytearray): 非阻塞接收时使用的滚动缓冲区（内部实现细节，不应外部修改）。

    Methods:
        __init__(uart):
            初始化解析器，接收一个已准备好的 UART 实例，清除串口残留数据并设置默认超时时间。

        build_frame(control: int, cmd: int, data: bytes = b"") -> bytes:
            根据协议构造完整帧：帧头 + ctl + cmd + len(2B) + data + checksum + 帧尾。

        recv_response() -> tuple[int, int, bytes] | None:
            阻塞接收并解析单帧响应，内部实现字节级有限状态机，校验头/尾/长度/校验和，成功返回 (control, cmd, data)，超时返回 None。

        send_frame(control: int, cmd: int, data: bytes = b""):
            发送一帧数据到模块，失败抛出 IOError。

        query_and_wait(control: int, command: int, send_data: bytes = b"") -> bytes | None:
            发送请求并循环等待匹配 control/command 的响应，返回响应的数据区 bytes。

        disable_all_reports():
            禁用模块的所有主动上报（根据协议发送若干关闭上报命令）。

        q_presence() -> int | None:
            查询存在检测结果，返回 1 表示有人，0 表示无人，失败返回 None。

        q_motion_param() -> tuple | None:
            查询运动参数（方向、强度等），返回解析后的元组或 None。

        q_distance() -> int | None:
            查询目标距离（单位：cm），协议返回两字节大端无符号整数，超时或非法返回 None。

        q_position() -> tuple[int, int, int] | None:
            查询目标三维位置或方向，返回 (x, y, z) 三个有符号 16 位大端整数（单位：度或协议定义的单位），异常返回 None。

        q_hr_value() -> int | None:
            查询心率值（BPM），返回整数或 None。

        q_hr_waveform() -> list[int] | None:
            查询心率波形，返回中心化后的数据数组（例如每点 = raw - 128），或 None。

        q_sleep_end_time() -> str | None:
            查询最近一次睡眠结束时间，返回格式化字符串 "YYYY-MM-DD HH:MM:SS" 或 None。

        q_struggle_sensitivity() -> int | None:
            查询挣扎敏感度设置，返回数值或 None。

    ==========================================
     Attributes:
        uart (UART): An initialized UART instance used for communication with the module (must be created externally and passed in).
        _control (int): Default control byte used internally (e.g.: 0x80).
        _timeout_ms (int): Timeout period for queries/reception, in milliseconds.
        _rx_buf (bytearray): Rolling buffer used for non-blocking reception (internal implementation detail, should not be modified externally).

    Methods:
        __init__(uart):
            Initializes the parser, receives a prepared UART instance, clears residual serial port data, and sets the default timeout period.

        build_frame(control: int, cmd: int, data: bytes = b"") -> bytes:
            Constructs a complete frame according to the protocol: frame header + ctl + cmd + len(2B) + data + checksum + frame tail.
        recv_response() -> tuple[int, int, bytes] | None:
            Blocking reception and parsing of a single response frame, internally implements a byte-level finite state machine, verifies header/tail/length/checksum, returns (control, cmd, data) on success, and None on timeout.

        send_frame(control: int, cmd: int, data: bytes = b""):
            Sends a frame of data to the module, throws an IOError on failure.

        query_and_wait(control: int, command: int, send_data: bytes = b"") -> bytes | None:
            Sends a request and loops to wait for a response matching the control/command, returns the data area bytes of the response.

        disable_all_reports():
            Disables all active reports of the module (sends several report closing commands according to the protocol).

        q_presence() -> int | None:
            Queries the presence detection result, returns 1 indicating someone is present, 0 indicating no one is present, and None on failure.

        q_motion_param() -> tuple | None:
            Queries motion parameters (direction, intensity, etc.), returns the parsed tuple or None.

        q_distance() -> int | None:
            Queries the target distance (unit: cm), the protocol returns a 2-byte big-endian unsigned integer, returns None on timeout or if invalid.

        q_position() -> tuple[int, int, int] | None:
            Queries the target's 3D position or direction, returns (x, y, z) three signed 16-bit big-endian integers (unit: degrees or as defined by the protocol), returns None on exception.

        q_hr_value() -> int | None:
            Queries the heart rate value (BPM), returns an integer or None.

        q_hr_waveform() -> list[int] | None:
            Queries the heart rate waveform, returns a centralized data array (e.g., each point = raw - 128), or None.

        q_sleep_end_time() -> str | None:
            Queries the end time of the most recent sleep, returns a formatted string "YYYY-MM-DD HH:MM:SS" or None.

        q_struggle_sensitivity() -> int | None:
            Queries the struggle sensitivity setting, returns a value or None.
    """
    def __init__(self, uart):
        """
        初始化协议解析器。

        Args:
            uart: 已初始化的 UART 对象，必须支持 any()/read()/write() 方法。

        Raises:
            ValueError: 当 uart 为 None 时抛出。

        Notes:
            - 初始化时会清除 UART 缓冲中的残留数据。
            - 内部固定 control = 0x80，默认超时时间 300 ms。
        ==========================================
        Initialize the protocol handler.

        Args:
            uart: An initialized UART object that supports any()/read()/write().

        Raises:
            ValueError: Raised if uart is None.

        Notes:
            - Clears residual UART data during init.
            - Internal default control = 0x80, timeout = 300 ms.
        """

        if uart is None:
            raise ValueError("uart is None")
        self.uart = uart

         # 协议固定量（写死即可，用不到就别暴露）
        self._control = 0x80
        self._timeout_ms = 300

        # 非阻塞解析的滚动缓冲（recv_response 用）
        self._rx_buf = bytearray()

        # 清掉上电残留
        n = self.uart.any()
        if n:
            self.uart.read(n)


    def build_frame(self, control: int, cmd: int, data: bytes = b"") -> bytes:
        """
        构造一帧完整的协议数据。

        Args:
            control (int): 控制字节。
            cmd (int): 命令字节。
            data (bytes): 数据区（可为空）。

        Returns:
            bytes: 构造好的完整帧。

        Raises:
            ValueError: data 类型不是 bytes 或 bytearray。

        Notes:
            帧格式: 2字节头 "SY" + ctl + cmd + 2字节长度 + 数据 + 1字节和校验 + 2字节尾 "TC"。
        ==========================================
        Build a complete protocol frame.

        Args:
            control (int): Control byte.
            cmd (int): Command byte.
            data (bytes): Data payload (optional).

        Returns:
            bytes: The constructed frame.

        Raises:
            ValueError: If data is not bytes or bytearray.

        Notes:
            Frame format: "SY" + ctl + cmd + 2-byte length + data + 1-byte checksum + "TC".
        """
        # 参数与类型检查
        control = int(control)
        cmd = int(cmd)
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data must be bytes or bytearray")

        n = len(data)
        # 总长度 = 2头 +1ctl +1cmd +2len +n数据 +1sum +2尾
        frame = bytearray(2 + 1 + 1 + 2 + n + 1 + 2)
        frame[0] = 0x53  # 'S'
        frame[1] = 0x59  # 'Y'
        frame[2] = control
        frame[3] = cmd
        frame[4] = (n >> 8) & 0xFF  # LEN_H，大端
        frame[5] = n & 0xFF         # LEN_L
        if n:
            frame[6:6 + n] = data

        # 低 8 位累加和（含帧头，不含校验与尾部）
        s = 0
        for b in frame[:6 + n]:
            s = (s + b) & 0xFF
        frame[6 + n] = s

        frame[-2] = 0x54  # 'T'
        frame[-1] = 0x43  # 'C'
        return bytes(frame)

    def recv_response(self):
        """
        接收并解析一帧响应（阻塞直到超时）。

        Returns:
            tuple[int, int, bytes] | None: (control, cmd, data)，若超时返回 None。

        Notes:
            - 内部实现为有限状态机：逐字节搜帧头 -> 长度 -> 完整帧。
            - 自动校验头/尾/长度/累加和，坏帧会丢弃并继续搜索。
        ==========================================
        Receive and parse one response frame (blocking until timeout).

        Returns:
            tuple[int, int, bytes] | None: (control, cmd, data), or None if timeout.

        Notes:
            - Implements a byte-by-byte state machine.
            - Automatically validates header/footer/length/checksum.
              Invalid frames are discarded.
        """

        timeout_ms = getattr(self, "timeout_ms", 100)

        t0 = time.ticks_ms()
        buf = bytearray()
        state = 0  # 0:找0x53, 1:找0x59, 2:已得6字节头, 3:收满
        need_total = None  # 全帧长度 = 2头+1ctl+1cmd+2len+n+1sum+2尾 = 9+n

        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            b = self.uart.read(1)
            if not b:
                time.sleep_ms(1)
                continue
            x = b[0]

            if state == 0:
                if x == 0x53:  # 'S'
                    buf = bytearray([0x53]);
                    state = 1
                else:
                    continue
            elif state == 1:
                if x == 0x59:  # 'Y'
                    buf.append(0x59);
                    state = 2
                else:
                    state = 0;
                    buf = bytearray()
            elif state == 2:
                buf.append(x)
                if len(buf) == 6:
                    n = (buf[4] << 8) | buf[5]
                    need_total = 9 + n
                    state = 3
            elif state == 3:
                buf.append(x)
                if need_total is not None and len(buf) == need_total:
                    # 校验并解析
                    try:
                        if not (buf[0] == 0x53 and buf[1] == 0x59): raise ValueError
                        if not (buf[-2] == 0x54 and buf[-1] == 0x43): raise ValueError
                        n = (buf[4] << 8) | buf[5]
                        data = bytes(buf[6:6 + n]) if n else b""
                        s = 0
                        for v in buf[:6 + n]:
                            s = (s + v) & 0xFF
                        if s != buf[6 + n]: raise ValueError
                        ctrl = buf[2]
                        cmd = buf[3]  # 返回命令字

                        return (ctrl,cmd, data)
                    except ValueError:
                        # 坏帧：丢弃并重新找帧头
                        state = 0;
                        buf = bytearray();
                        need_total = None
                        continue
        return None

    def send_frame(self, control: int, cmd: int, data: bytes = b""):
        """
        发送一帧数据。

        Args:
            control (int): 控制字节。
            cmd (int): 命令字节。
            data (bytes): 数据负载。

        Raises:
            IOError: UART 写入失败。
        ==========================================
        Send one frame.

        Args:
            control (int): Control byte.
            cmd (int): Command byte.
            data (bytes): Data payload.

        Raises:
            IOError: If UART write fails.
        """

        try:
            self.uart.write(self.build_frame(control, cmd, data))
        except IOError as e:
            raise IOError("UART write failed") from e

    def query_and_wait(self, control: int, command: int, send_data: bytes = b""):
        """
        发送一帧并等待对应响应。

        Args:
            control (int): 控制字节。
            command (int): 命令字节。
            send_data (bytes): 要发送的数据。

        Returns:
            bytes: 响应帧中的数据区。

        Notes:
            - 内部会循环：send_frame -> recv_response。
            - 直到收到匹配 control/command 的响应才返回。
        ==========================================
        Send one frame and wait for the matching response.

        Args:
            control (int): Control byte.
            command (int): Command byte.
            send_data (bytes): Data to send.

        Returns:
            bytes: Data field of the response.

        Notes:
            - Loops: send_frame -> recv_response.
            - Returns only when control/command match.
        """
        while True:
            # 1) 发送
            self.send_frame(control, command, send_data)

            # 2) 接收一次（recv_response 内部自带等待/超时）
            ret = self.recv_response()  # -> (ctrl, cmd, data) 或 None
            if ret is not None:
                ctrl, cmd, data = ret
                if (ctrl & 0xFF) == (control & 0xFF) and (cmd & 0xFF) == (command & 0xFF):
                    return data  # 命中，返回 data

    def disable_all_reports(self):
        """
        禁用所有上报。

        Notes:
            内部依次发送 (0x80,0x00)，(0x81,0x00)，(0x84,0x00)，(0x85,0x00)。
        ==========================================
        Disable all reports.

        Notes:
            Internally sends (0x80,0x00), (0x81,0x00), (0x84,0x00), (0x85,0x00).
        """
        self.query_and_wait(0x80, 0x00, b"\x00")
        self.query_and_wait(0x81, 0x00, b"\x00")
        self.query_and_wait(0x84, 0x00, b"\x00")
        self.query_and_wait(0x85, 0x00, b"\x00")

    def q_presence(self):
        """
        查询存在检测结果 (Presence)。

        Returns:
            bool: True 表示有人存在，False 表示无人。

        Notes:
            - 发送 (0x80, 0x01) 请求。
            - 返回数据长度应为 1 字节，值为 0 或 1。
        ==========================================
        Query presence detection result.

        Returns:
            bool: True if presence detected, False otherwise.

        Notes:
            - Sends (0x80, 0x01).
            - Response data length = 1 byte, value 0 or 1.
        """

        data = self.query_and_wait(0x80, 0x81, b"\x0F")
        if not data:  # None 或 空
            return None
        return 1 if data[0] == 1 else 0

    def q_motion_param(self):
        """
        查询运动参数。

        Returns:
            tuple[int, int]: (运动方向, 运动强度)。

        Notes:
            - 发送 (0x80, 0x02) 请求。
            - 返回数据 2 字节: direction, strength。
        ==========================================
        Query motion parameters.

        Returns:
            tuple[int, int]: (direction, strength).

        Notes:
            - Sends (0x80, 0x02).
            - Response contains 2 bytes: direction, strength.
        """
        data = self.query_and_wait(0x80, 0x83, b"\x0F")
        if not data:
            return None
        return data[0]

    def q_distance(self):
        """
        查询目标距离。

        Returns:
            int: 距离，单位 cm。

        Notes:
            - 发送 (0x80, 0x03) 请求。
            - 返回数据为 2 字节无符号整数 (cm)。
        ==========================================
        Query target distance.

        Returns:
            int: Distance in cm.

        Notes:
            - Sends (0x80, 0x03).
            - Response contains 2-byte unsigned integer (cm).
        """

        data = self.query_and_wait(0x80, 0x84, b"\x0F")
        if data is None or len(data) < 2:
            return None
        return _u16_be(data[0], data[1])

    def q_position(self):
        """
        查询目标位置。

        Returns:
            tuple[int, int]: (水平角度, 垂直角度)，单位度。

        Notes:
            - 发送 (0x80, 0x04) 请求。
            - 返回数据 2 字节: horizontal, vertical。
        ==========================================
        Query target position.

        Returns:
            tuple[int, int]: (horizontal angle, vertical angle) in degrees.

        Notes:
            - Sends (0x80, 0x04).
            - Response contains 2 bytes: horizontal, vertical.
        """

        data = self.query_and_wait(0x80, 0x85, b"\x0F")
        if data is None or len(data) < 6:
            return None
        x = _s16_be(data[0], data[1])
        y = _s16_be(data[2], data[3])
        z = _s16_be(data[4], data[5])
        return (x, y, z)

    # ===== 心率（查询类） =====
    def q_hr_value(self):
        """
        查询心率值。

        Returns:
            int: 心率值 (BPM)。

        Notes:
            - 发送 (0x81, 0x01) 请求。
            - 返回数据 2 字节无符号整数。
        ==========================================
        Query heart rate value.

        Returns:
            int: Heart rate in BPM.

        Notes:
            - Sends (0x81, 0x01).
            - Response contains 2-byte unsigned integer.
        """

        data = self.query_and_wait(0x85, 0x82, b"\x0F")
        if not data:
            return None
        return data[0]

    def q_hr_waveform(self):
        """
        查询心率波形数据。

        Returns:
            bytes: 波形数据（原始字节流）。

        Notes:
            - 发送 (0x81, 0x02) 请求。
            - 返回的数据长度可变。
        ==========================================
        Query heart rate waveform data.

        Returns:
            bytes: Raw waveform data.

        Notes:
            - Sends (0x81, 0x02).
            - Response data length is variable.
        """

        data = self.query_and_wait(0x85, 0x85, b"\x0F")
        # 超时 / 无数据
        if data is None:
            return None
        # 期望 5 字节；不足则判为无效
        if len(data) < 5:
            return None
        # 解析：原始[0..255]，协议基线为128，减去128得到中心化波形
        return [data[0] - 128, data[1] - 128, data[2] - 128, data[3] - 128, data[4] - 128]

    # ===== 睡眠（查询类） =====
    def q_sleep_end_time(self):
        """
        查询最近一次睡眠结束时间。

        Returns:
            str: 格式化时间字符串 "YYYY-MM-DD HH:MM:SS"。

        Notes:
            - 发送 (0x84, 0x01) 请求。
            - 返回数据为 6 字节: year, month, day, hour, minute, second。
        ==========================================
        Query the most recent sleep end time.

        Returns:
            str: Formatted timestamp "YYYY-MM-DD HH:MM:SS".

        Notes:
            - Sends (0x84, 0x01).
            - Response contains 6 bytes: year, month, day, hour, minute, second.
        """

        data = self.query_and_wait(0x84, 0x96, b"\x0F")
        if not data:
            return None
        return data[0]

    def q_struggle_sensitivity(self):
        """
        查询挣扎敏感度设置。

        Returns:
            int: 当前敏感度值 (0-255)。

        Notes:
            - 发送 (0x85, 0x01) 请求。
            - 返回数据 1 字节。
        ==========================================
        Query struggle sensitivity setting.

        Returns:
            int: Current sensitivity value (0-255).

        Notes:
            - Sends (0x85, 0x01).
            - Response contains 1 byte.
        """

        data = self.query_and_wait(0x84, 0x91, b"\x0F")
        if not data:
            return None
        return data[0]

    cmd_map = {
        (0x80, 0x05): "b_text"  # 使用方法名字符串避免类级别前向引用
    }

    def b_text(self, data):
        print("触发成功")
        print(data)

    def b_recv_response(self):
        ret = self.recv_response()
        if ret is not None:
            ctrl, cmd, data = ret
            handler = self.cmd_map.get((ctrl, cmd), None)
            if handler is None:
                return None
            # 支持两种映射：方法名字符串或直接可调用对象
            if isinstance(handler, str):
                func = getattr(self, handler, None)
            else:
                func = handler
            if callable(func):
                try:
                    return func(data)
                except Exception:
                    return None
            return None
# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================