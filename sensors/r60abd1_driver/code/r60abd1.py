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

        # 其余：build_frame / parse_response / recv_response / send_frame ...

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

    def parse_response(self, resp: bytes):
        """
        解析一帧响应数据并校验。

        Args:
            resp (bytes): 完整的响应帧。

        Returns:
            dict: {"control": int, "cmd": int, "data": bytes}

        Raises:
            ValueError: 帧过短、头尾错误、长度不符或校验和不匹配。
        ==========================================
        Parse and validate a response frame.

        Args:
            resp (bytes): Full response frame.

        Returns:
            dict: {"control": int, "cmd": int, "data": bytes}

        Raises:
            ValueError: If frame too short, header/footer invalid, length mismatch, or checksum fails.
        """

        # 基础长度检查：最小 2头+1ctl+1cmd+2len+1sum+2尾 = 9
        if not resp or len(resp) < 9:
            raise ValueError("response is too short.")

        if not (resp[0] == 0x53 and resp[1] == 0x59):
            raise ValueError("Frame header error")
        if not (resp[-2] == 0x54 and resp[-1] == 0x43):
            raise ValueError("Frame end error")

        control = resp[2]
        cmd = resp[3]
        n = (resp[4] << 8) | resp[5]

        expected_len = 2 + 1 + 1 + 2 + n + 1 + 2  # = 9 + n
        if len(resp) != expected_len:
            raise ValueError("Length mismatch")

        data = resp[6:6 + n] if n else b""

        s = 0
        for b in resp[:6 + n]:  # 含头到数据末
            s = (s + b) & 0xFF
        if s != resp[6 + n]:
            raise ValueError("Checksum mismatch")

        return {"control": control, "cmd": cmd, "data": data}

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

        timeout_ms = getattr(self, "timeout_ms", 300)

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

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================