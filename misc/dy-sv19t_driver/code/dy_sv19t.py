# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:00
# @Author  : 侯钧瀚
# @File    : dy_sv19t.py
# @Description : DY-SV19T 语音播放模块驱动（UART，按API要求补齐）
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.2.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入 const 用于常量定义
from micropython import const
# 导入 time 提供延时与时间控制
import time

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class DYSV19T:
    """
    DY-SV19T 音频模块控制类（UART）。支持：播放/暂停/停止、上下曲、音量、EQ、循环模式、
    指定曲目/路径播放、插播、快进快退、复读、查询状态/曲目/时间、组合播放（ZH）。

    Attributes:
        uart: UART 实例（需提前按 9600 8N1 初始化）
        timeout_ms (int): 串口读取超时时间（毫秒）
        play_state (int): 播放状态（PLAY_*）
        current_disk (int): 当前盘符（DISK_*）
        volume (int): 当前音量（0~30）
        play_mode (int): 播放模式（MODE_*）
        eq (int): EQ 模式（EQ_*）
        dac_channel (int): DAC 输出通道（CH_*）

    Notes:
        - 帧结构：AA CMD LEN DATA... SM。SM 为从 AA 到最后一个 DATA 字节逐字节求和取低 8 位。
        - 16 位数值：高字节在前（big-endian）。
        - 路径必须以 '/' 起始，文件夹名 1..8 字节，字符集仅允许 A-Z/0-9/_（另允许协议格式符 '*' 和 '.'）。
        - 查询方法在超时未取到完整帧时返回 None，不抛异常；控制方法写串口失败可能抛 IOError/IOError。
    ==========================================

    DY-SV19T audio module controller (UART). Features: play/pause/stop, next/prev,
    volume, EQ, loop mode, select track/path, insert track/path, seek, repeat,
    status/track/time queries, combination playlist (ZH).

    Attributes:
        uart: UART instance (pre-configured 9600 8N1)
        timeout_ms (int): UART read timeout (ms)
        play_state (int): Playback state (PLAY_*)
        current_disk (int): Current disk (DISK_*)
        volume (int): Volume 0..30
        play_mode (int): Loop mode (MODE_*)
        eq (int): EQ mode (EQ_*)
        dac_channel (int): DAC channel (CH_*)

    Notes:
        - Frame: AA CMD LEN DATA... SM. SM is the low 8-bit sum from AA to last DATA.
        - 16-bit values are big-endian (high then low).
        - Path must start with '/', folder name 1..8 bytes, allowed charset A-Z/0-9/_
          (and '*' '.' as protocol format symbols).
        - Query methods return None on timeout; control methods may raise IOError/IOError on write failure.
    """
    # 盘符
    DISK_USB = const(0x00)
    DISK_SD = const(0x01)
    DISK_FLASH = const(0x02)
    DISK_NONE = const(0xFF)

    # 播放状态
    PLAY_STOP = const(0x00)
    PLAY_PLAY = const(0x01)
    PLAY_PAUSE = const(0x02)

    # 播放模式（loop）
    MODE_FULL_LOOP = const(0x00)
    MODE_SINGLE_LOOP = const(0x01)
    MODE_SINGLE_STOP = const(0x02)  # 默认
    MODE_FULL_RANDOM = const(0x03)
    MODE_DIR_LOOP = const(0x04)
    MODE_DIR_RANDOM = const(0x05)
    MODE_DIR_SEQUENCE = const(0x06)
    MODE_SEQUENCE = const(0x07)

    # EQ
    EQ_NORMAL = const(0x00)
    EQ_POP = const(0x01)
    EQ_ROCK = const(0x02)
    EQ_JAZZ = const(0x03)
    EQ_CLASSIC = const(0x04)

    # DAC 输出通道
    CH_MP3 = const(0x00)
    CH_AUX = const(0x01)
    CH_MP3_AUX = const(0x02)

    # 其它常量
    VOLUME_MIN = const(0)
    VOLUME_MAX = const(30)
    DEFAULT_BAUD = const(9600)

    def __init__(self, uart, *,
                 default_volume: int = VOLUME_MAX,
                 default_disk: int = DISK_USB,
                 default_play_mode: int = MODE_SINGLE_STOP,
                 default_dac_channel: int = CH_MP3,
                 timeout_ms: int = 500):
        """
        初始化驱动实例；仅保存状态与参数校验，不主动向模块发命令。

        Args:
            uart: UART 实例（需已配置 9600 8N1），必须具备 read()/write()
            default_volume (int): 默认音量 0..30
            default_disk (int): 默认盘符（DISK_*）
            default_play_mode (int): 默认播放模式（MODE_*）
            default_dac_channel (int): 默认 DAC 输出（CH_*）
            timeout_ms (int): 读取超时（毫秒）

        Raises:
            ValueError: 任一参数超出允许范围或类型不符
        ==========================================

        Initialize driver; only stores defaults and validates params.

        Args:
            uart: UART instance (9600 8N1) providing read()/write()
            default_volume (int): 0..30
            default_disk (int): One of DISK_*
            default_play_mode (int): One of MODE_*
            default_dac_channel (int): One of CH_*
            timeout_ms (int): Read timeout in ms

        Raises:
            ValueError: If any argument is out of range or wrong type
        """
        if uart is None or not hasattr(uart, 'read') or not hasattr(uart, 'write'):
            raise ValueError("Invalid UART instance, must have read()/write() / 无效的UART实例")
        if not (self.VOLUME_MIN <= int(default_volume) <= self.VOLUME_MAX):
            raise ValueError("default_volume must be within 0..30")
        if default_disk not in (self.DISK_USB, self.DISK_SD, self.DISK_FLASH, self.DISK_NONE):
            raise ValueError("default_disk must be a DISK_* constant")
        if default_play_mode not in (
            self.MODE_FULL_LOOP, self.MODE_SINGLE_LOOP, self.MODE_SINGLE_STOP,
            self.MODE_FULL_RANDOM, self.MODE_DIR_LOOP, self.MODE_DIR_RANDOM,
            self.MODE_DIR_SEQUENCE, self.MODE_SEQUENCE,
        ):
            raise ValueError("default_play_mode must be a MODE_* constant")
        if default_dac_channel not in (self.CH_MP3, self.CH_AUX, self.CH_MP3_AUX):
            raise ValueError("default_dac_channel must be a CH_* constant")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")

        self.uart = uart
        self.timeout_ms = int(timeout_ms)

        # 运行态属性（查询后/命令成功后由驱动维护）
        self.play_state = self.PLAY_STOP
        self.current_disk = int(default_disk)
        self.volume = int(default_volume)
        self.play_mode = int(default_play_mode)
        self.eq = self.EQ_NORMAL
        self.dac_channel = int(default_dac_channel)

    def _u16(self, value: int) -> tuple:
        """
        将 0..65535 转为 (H,L) 两个字节。

        Args:
            value (int): 要编码的无符号 16 位整数

        Raises:
            ValueError: value 不在 0..65535
        ==========================================

        Convert 0..65535 to (H, L) bytes.

        Args:
            value (int): Unsigned 16-bit integer

        Raises:
            ValueError: If value is not in 0..65535
        """
        value = int(value)
        if not (0 <= value <= 0xFFFF):
            raise ValueError("The parameter must be in the range of 0..65535")
        return (value >> 8) & 0xFF, value & 0xFF

    def _validate_disk(self, disk: int) -> int:
        """
        校验盘符是否为 USB/SD/FLASH。

        Args:
            disk (int): 盘符常量

        Raises:
            ValueError: 非法盘符
        ==========================================

        Validate disk is one of USB/SD/FLASH.

        Args:
            disk (int): Disk constant

        Raises:
            ValueError: If disk is invalid
        """
        if disk not in (self.DISK_USB, self.DISK_SD, self.DISK_FLASH):
            raise ValueError("The disk must be DISK_USB/SD/FLASH and must be online.")
        return int(disk)

    def _validate_mode(self, mode: int) -> int:
        """
        校验播放模式常量。

        Args:
            mode (int): 播放模式

        Raises:
            ValueError: 非法模式
        ==========================================

        Validate loop mode constant.

        Args:
            mode (int): Loop mode

        Raises:
            ValueError: If mode invalid
        """
        if mode not in (
            self.MODE_FULL_LOOP, self.MODE_SINGLE_LOOP, self.MODE_SINGLE_STOP,
            self.MODE_FULL_RANDOM, self.MODE_DIR_LOOP, self.MODE_DIR_RANDOM,
            self.MODE_DIR_SEQUENCE, self.MODE_SEQUENCE,
        ):
            raise ValueError("mode must be a MODE_* constant")
        return int(mode)

    def _validate_eq(self, eq: int) -> int:
        """
        校验 EQ 常量。

        Args:
            eq (int): EQ 模式

        Raises:
            ValueError: 非法 EQ
        ==========================================

        Validate EQ constant.

        Args:
            eq (int): EQ mode

        Raises:
            ValueError: If eq invalid
        """
        if eq not in (self.EQ_NORMAL, self.EQ_POP, self.EQ_ROCK, self.EQ_JAZZ, self.EQ_CLASSIC):
            raise ValueError("eq must be an EQ_* constant")
        return int(eq)

    def _validate_channel(self, ch: int) -> int:
        """
        校验 DAC 输出通道常量。

        Args:
            ch (int): 通道常量

        Raises:
            ValueError: 非法通道
        ==========================================

        Validate output channel constant.

            ch (int): Channel constant

        Raises:
            ValueError: If ch invalid
        """
        if ch not in (self.CH_MP3, self.CH_AUX, self.CH_MP3_AUX):
            raise ValueError("ch must be a CH_* constant")
        return int(ch)

    def _validate_path(self, path: str) -> bytes:
        """
        校验并编码路径字符串。

        Args:
            path (str): 目标路径（如 '/MUSIC/01.MP3' 或 '/ZH/*.WAV'）

        Raises:
            ValueError: 路径为空、未以'/'起始、含非法字符或段长非法
        ==========================================

        Validate and encode path string.

        Args:
            path (str): Path such as '/MUSIC/01.MP3' or '/ZH/*.WAV'

        Raises:
            ValueError: If empty, not starting with '/', contains invalid chars, or segment length invalid
        """
        if not isinstance(path, str) or not path:
            raise ValueError("The path must start with '/'")
        if path[0] != '/':
            raise ValueError("The path must start with '/'")
        # 允许的字符集：A-Z, 0-9, '_', '/', '*', '.'
        for ch in path:
            o = ord(ch)
            if ch in ('/', '*', '.'):
                continue
            if ch == '_':
                continue
            if 48 <= o <= 57:  # 0-9
                continue
            if 65 <= o <= 90:  # A-Z
                continue
            raise ValueError("path contains illegal characters: only A-Z/0-9/_, and protocol formatters '*', '.', '/' are allowed")
        # 校验每段（按 '/' 分割的文件夹名）长度 1..8；'*' 属于格式符不过不作为段内容校验
        seg = ""
        for ch in path[1:]:  # 跳过开头 '/'
            if ch == '/':
                if not (1 <= len(seg) <= 8):
                    raise ValueError("The length of the folder name must be 1..8 bytes")
                seg = ""
            elif ch in ('*', '.'):
                # 到达文件名或扩展名格式区，结束文件夹段校验
                break
            else:
                seg += ch
        return path.encode('ascii')

    def _build_frame(self, cmd: int, data: bytes) -> bytes:
        """
        构造完整帧：AA CMD LEN DATA... SM

        Args:
            cmd (int): 命令码
            data (bytes): 载荷数据

        Raises:
            ValueError: data 非 bytes/bytearray 类型
        ==========================================

        Build a complete frame: AA CMD LEN DATA... SM

        
            cmd (int): Command code
            data (bytes): Payload data

        Raises:
            ValueError: If data is not bytes/bytearray
        """
        cmd = int(cmd)
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data 必须为 bytes/bytearray")
        frame = bytearray(3 + len(data) + 1)
        frame[0] = 0xAA
        frame[1] = cmd
        frame[2] = len(data)
        if data:
            frame[3:3+len(data)] = data
        sm = 0
        for b in frame[:-1]:
            sm = (sm + b) & 0xFF
        frame[-1] = sm
        return bytes(frame)

    def _parse_response(self, resp: bytes):
        """
        解析并校验响应帧，返回 { 'cmd': int, 'data': bytes }。

        Args:
            resp (bytes): 原始响应帧字节序列

        Raises:
            ValueError: 响应过短、起始码错误、长度不匹配或校验和不匹配
        ==========================================

        Parse & validate response frame, return {'cmd': int, 'data': bytes}.

        Raises:
            ValueError: If too short, bad start byte, length mismatch, or checksum mismatch
        """
        if not resp or len(resp) < 4:
            raise ValueError("The response is too short.")
        if resp[0] != 0xAA:
            raise ValueError("Initial code error")
        cmd = resp[1]
        n   = resp[2]
        if len(resp) != 4 + n - 0:  # AA CMD LEN DATA(n) SM
            raise ValueError("Length mismatch")
        sm = 0
        for b in resp[:-1]:
            sm = (sm + b) & 0xFF
        if sm != resp[-1]:
            raise ValueError("The volume must be between 0..30")
        data = resp[3:3+n] if n else b""
        return {'cmd': cmd, 'data': data}

    def _recv_response(self, expected_cmd: int = None, timeout_ms: int = None):
        """
        读取一帧响应；若 expected_cmd 提供则仅返回匹配的帧；超时返回 None。

        Args:
            expected_cmd (int|None): 期望的命令码；None 表示接受任意
            timeout_ms (int|None): 覆盖默认超时时间；None 使用 self.timeout_ms

        Raises:
            无（函数内部吞掉解析错误并继续读取）
        ==========================================

        Read one response frame; if expected_cmd given, only return matching; None on timeout.

        Args:
            expected_cmd (int|None): Expected command code or None
            timeout_ms (int|None): Override default timeout in ms

        Raises:
            None (parsing errors are ignored to continue seeking)
        """
        if timeout_ms is None:
            timeout_ms = self.timeout_ms
        t0 = time.ticks_ms()
        buf = bytearray()
        state = 0  # 0: seek AA, 1: got AA, waiting CMD/LEN/DATA/SM
        need = 0
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            b = self.uart.read(1)
            if not b:
                # 小睡一会儿避免空转
                time.sleep_ms(1)
                continue
            x = b[0]
            if state == 0:
                if x == 0xAA:
                    buf = bytearray([0xAA])
                    state = 1
            elif state == 1:
                buf.append(x)
                if len(buf) == 3:
                    need = 4 + buf[2]  # total length including SM
                if len(buf) >= 3 and len(buf) == need:
                    # 完整帧到达
                    try:
                        parsed = self._parse_response(buf)
                    except ValueError:
                        # 丢弃并重新寻找起始
                        state = 0
                        buf = bytearray()
                        continue
                    if (expected_cmd is None) or (parsed['cmd'] == expected_cmd):
                        return bytes(buf)
                    # 不匹配继续寻找下一帧
                    state = 0
                    buf = bytearray()
        return None

    def _send_frame(self, cmd: int):
        """
        发送无数据载荷的通用指令帧。

        Args:
            cmd (int): 命令码

        Raises:
            IOError: 串口写入失败时可能由底层抛出
        ==========================================

        Send a generic command with empty payload.

        Args:
            cmd (int): Command code

        Raises:
            IOError: May be raised by underlying UART write
        """
        # 发送无数据的通用命令
        try:
            self.uart.write(self._build_frame(cmd, b""))
        except IOError as e:
            raise IOError("UART Write failed") from e

    def play(self):
        """
        播放（AA 02 00 SM）。

        ==========================================

        Start playback (AA 02 00 SM).

        Raises:
            IOError: If UART write fails
        """
        self._send_frame(0x02)
        self.play_state = self.PLAY_PLAY

    def pause(self):
        """
        暂停（AA 03 00 SM）。

        ==========================================

        Pause (AA 03 00 SM).

        """
        self._send_frame(0x03)
        self.play_state = self.PLAY_PAUSE

    def stop(self):
        """
        停止（AA 04 00 SM）。

        ==========================================

        Stop (AA 04 00 SM).

        """
        self._send_frame(0x04)
        self.play_state = self.PLAY_STOP

    def prev_track(self):
        """
        上一首（AA 05 00 SM）。

        ==========================================

        Previous song (AA 05 00 SM).

        """
        self._send_frame(0x05)

    def next_track(self):
        """
        下一首（AA 06 00 SM）。


        ==========================================

        Next (AA 06 00 SM).

            Skip to next track.
        """
        self._send_frame(0x06)

    def select_track(self, track_no: int, play: bool = True):
        """
        指定曲目号 1..65535；play=True 直接播放（AA 07 02 H L SM），否则仅选曲（AA 1F 02 H L SM）。

        Args:
            track_no (int): 曲目号，范围 1..65535
            play (bool): True 立即播放；False 仅预选

        Select track 1..65535; play immediately if True, else select only.

        Args:
            track_no (int): Track number 1..65535
            play (bool): True to play now, False to preselect only

        """
        # 验证track_no 输出H,L
        H, L = self._u16(track_no)
        if play:
            self.uart.write(self._build_frame(0x07, bytes([H, L])))
            self.play_state = self.PLAY_PLAY
        else:
            self.uart.write(self._build_frame(0x1F, bytes([H, L])))

    def play_disk_path(self, disk: int, path: str):
        """
        按盘符+路径播放（AA 08 <len> <disk> <path...> SM）。

        Args:
            disk (int): 盘符（DISK_*）
            path (str): 形如 '/DIR/NAME.MP3' 的路径
        ==========================================

        Play by disk + path (AA 08 <len> <disk> <path...> SM).

        Args:
            disk (int): One of DISK_*
            path (str): Path like '/DIR/NAME.MP3'
        """
        path = path.replace('.', '*')
        # 校验盘符
        d = self._validate_disk(disk)
        # 校验路径
        pb = self._validate_path(path)
        self.uart.write(self._build_frame(0x08, bytes([d]) + pb))
        self.play_state = self.PLAY_PLAY
        self.current_disk = d

    def insert_track(self, disk: int, track_no: int):
        """
        插播曲目（AA 16 03 <disk> <H> <L> SM）。

        Args:
            disk (int): 盘符（DISK_*）
            track_no (int): 曲目号 1..65535

        ==========================================

        Insert a track (AA 16 03 <disk> <H> <L> SM).

        Args:
            disk (int): One of DISK_*
            track_no (int): 1..65535

        """
        # 校验盘符
        d = self._validate_disk(disk)
        # 校验track_no 处理出H,L
        H, L = self._u16(track_no)
        self.uart.write(self._build_frame(0x16, bytes([d, H, L])))

    def insert_path(self, disk: int, path: str):
        """
        插播路径（AA 17 <len> <disk> <path...> SM）。

        Args:
            disk (int): 盘符（DISK_*）
            path (str): 路径（需以'/'起始）

        ==========================================

        Insert by path (AA 17 <len> <disk> <path...> SM).


        Args:
            disk (int): One of DISK_*
            path (str): Path (must start with '/')
        """
        path = path.replace('.', '*')
        # 验证文件
        d = self._validate_disk(disk)
        # 验证路径
        pb = self._validate_path(path)
        self.uart.write(self._build_frame(0x17, bytes([d]) + pb))

    def end_insert(self):
        """
        结束插播：等价于结束播放（AA 10 00 SM）。

        ==========================================

        End insertion: use stop playing (AA 10 00 SM).

        """
        self._send_frame(0x10)

    # 音量 / EQ / 通道
    def set_volume(self, vol: int):
        """
        设置音量 0..30（AA 13 01 <vol> SM）。

        Args:
            vol (int): 期望音量 0..30

        Raises:
            ValueError: 音量越界
        ==========================================

        Set volume 0..30 (AA 13 01 <vol> SM).

        Args:
            vol (int): Desired volume 0..30

        Raises:
            ValueError: If out of range
        """
        vol = int(vol)
        if not (self.VOLUME_MIN <= vol <= self.VOLUME_MAX):
            raise ValueError("The volume must be between 0..30")
        self.uart.write(self._build_frame(0x13, bytes([vol])))
        self.volume = vol

    def volume_up(self):
        """
        音量+（AA 14 00 SM）。

        ==========================================

        Volume up (AA 14 00 SM).

        """
        self._send_frame(0x14)

    def volume_down(self):
        """
        音量-（AA 15 00 SM）。

        ==========================================

        Volume down (AA 15 00 SM).
        """
        self._send_frame(0x15)

    def set_eq(self, eq: int):
        """
        设置 EQ（AA 1A 01 <eq> SM）。

        Args:
            eq (int): EQ 常量（EQ_*）
        ==========================================

        Set EQ (AA 1A 01 <eq> SM).


        Args:
            eq (int): One of EQ_*

        """
        # 验证eq
        e = self._validate_eq(eq)
        self.uart.write(self._build_frame(0x1A, bytes([e])))
        self.eq = e

    def set_dac_channel(self, ch: int):
        """
        设置 DAC 通道（AA 1D 01 <ch> SM）。

        Args:
            ch (int): CH_* 常量
        ==========================================

        Set DAC output channel (AA 1D 01 <ch> SM).

        Args:
            ch (int): One of CH_*
        """
        # 校验 DAC 输出通道常量
        c = self._validate_channel(ch)
        self.uart.write(self._build_frame(0x1D, bytes([c])))
        self.dac_channel = c

    # 循环/复读/快进快退
    def set_play_mode(self, mode: int):
        """
        设置播放模式（AA 18 01 <mode> SM）。

        Args:
            mode (int): MODE_* 常量

        ==========================================

        Set loop mode (AA 18 01 <mode> SM).

        Args:
            mode (int): One of MODE_*

        """
        # 校验播放模式
        m = self._validate_mode(mode)
        self.uart.write(self._build_frame(0x18, bytes([m])))
        self.play_mode = m

    def set_loop_count(self, count: int):
        """
        设置循环次数 1..65535（AA 19 02 H L SM）。

        Args:
            count (int): 循环次数 1..65535

        Raises:
            ValueError: count 越界 或 当前播放模式不支持设置循环次数
        ==========================================

        Set loop count 1..65535 (AA 19 02 H L SM).

        Args:
            count (int): Repeat count 1..65535

        Raises:
            ValueError: If count out of range or current mode unsupported
        """
        # 验证count 并且输出H,L
        H, L = self._u16(count)
        self.uart.write(self._build_frame(0x19, bytes([H, L])))
        if self.play_mode in ( 0x02, 0x03, 0x05, 0x06, 0x07):
            # 单曲停止、全盘随机、目录随机、目录顺序、全盘
            raise ValueError("The playback mode is incorrect, it supports \n(MODE_FULL_LOOP, MODE_SINGLE_LOOP, MODE_DIR_LOOP, MODE_SEQUENCE)")

    def repeat_area(self, start_min: int, start_sec: int, end_min: int, end_sec: int):
        """
        区间复读（AA 20 04 s_min s_sec e_min e_sec SM），分秒 0..59。

        Args:
            start_min (int): 起始分钟 0..59
            start_sec (int): 起始秒 0..59
            end_min (int): 结束分钟 0..59
            end_sec (int): 结束秒 0..59

        Raises:
            ValueError: 任一分秒越界
        ==========================================

        A-B repeat, minutes/seconds 0..59.

        Args:
            start_min (int): 0..59
            start_sec (int): 0..59
            end_min (int): 0..59
            end_sec (int): 0..59

        Raises:
            ValueError: If any minute/second out of range
        """
        for x in (start_min, start_sec, end_min, end_sec):
            v = int(x)
            if not (0 <= v <= 59):
                raise ValueError("Minutes/seconds must be in the range of 0..59")
        data = bytes([int(start_min), int(start_sec), int(end_min), int(end_sec)])
        self.uart.write(self._build_frame(0x20, data))

    def end_repeat(self):
        """
        结束复读（AA 21 00 SM）。

        ==========================================

        End A-B repeat (AA 21 00 SM).

        """
        self._send_frame(0x21)

    def seek_back(self, seconds: int):
        """
        快退 seconds（AA 22 02 H L SM）。



        Args:
            seconds (int): 回退的秒数 0..65535

        ==========================================

        Seek backward seconds (AA 22 02 H L SM).

        Args:
            seconds (int): 0..65535

        """
        # 验证seconds 并且输出H,L
        H, L = self._u16(seconds)
        self.uart.write(self._build_frame(0x22, bytes([H, L])))

    def seek_forward(self, seconds: int):
        """
        快进 seconds（AA 23 02 H L SM）。

        Args:
            seconds (int): 前进的秒数 0..65535

        ==========================================

        Seek forward seconds (AA 23 02 H L SM).

        Args:
            seconds (int): 0..65535

        """
        # 验证seconds 并且输出H,L
        H, L = self._u16(seconds)
        self.uart.write(self._build_frame(0x23, bytes([H, L])))

    # 查询类（解析并更新属性；超时返回 None）
    def query_status(self):
        """
        查询播放状态（AA 01 00 -> AA 01 01 <state> SM）。

        ==========================================

        Query play state; return int or None.

        """
        self._send_frame(0x01)
        resp = self._recv_response(expected_cmd=0x01)
        if not resp:
            return None
        parsed = self._parse_response(resp)
        if len(parsed['data']) == 1:
            st = parsed['data'][0]
            self.play_state = st
            return st
        return None

    def query_online_disks(self):
        """
        查询在线盘符位图 bit0 USB / bit1 SD / bit2 FLASH（AA 09 00）。

        ==========================================

        Query online disks bitmap; return int or None.

        """
        self._send_frame(0x09)
        resp = self._recv_response(expected_cmd=0x09)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        return d[0] if len(d) == 1 else None

    def query_current_disk(self):
        """
        查询当前盘符（AA 0A 00）。返回 DISK_* 或 None，并更新 current_disk。

        ==========================================

        Query current disk; return DISK_* or None.

        """
        self._send_frame(0x0A)
        resp = self._recv_response(expected_cmd=0x0A)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        if len(d) == 1:
            self.current_disk = d[0]
            return d[0]
        return None

    def query_total_tracks(self):
        """
        查询总曲目数（AA 0C 00 -> AA 0C 02 H L）。返回 int 或 None。

        ==========================================

        Query total tracks; return int or None.
        """
        self._send_frame(0x0C)
        resp = self._recv_response(expected_cmd=0x0C)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        if len(d) == 2:
            return (d[0] << 8) | d[1]
        return None

    def query_current_track(self):
        """
        查询当前曲目号（AA 0D 00 -> AA 0D 02 H L）。

        ==========================================

        Query current track number.

        """
        self._send_frame(0x0D)
        resp = self._recv_response(expected_cmd=0x0D)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        if len(d) == 2:
            return (d[0] << 8) | d[1]
        return None

    def query_folder_first_track(self):
        """
        查询当前文件夹首曲（AA 11 00 -> AA 11 02 H L）。

        ==========================================

        Query first track index in current folder.

        """
        self._send_frame(0x11)
        resp = self._recv_response(expected_cmd=0x11)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        if len(d) == 2:
            return (d[0] << 8) | d[1]
        return None

    def query_folder_total_tracks(self):
        """
        查询当前文件夹曲目数（AA 12 00 -> AA 12 02 H L）。

        ==========================================

        Query number of tracks in current folder.


        """
        self._send_frame(0x12)
        resp = self._recv_response(expected_cmd=0x12)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        if len(d) == 2:
            return (d[0] << 8) | d[1]
        return None

    def query_short_filename(self):
        """
        查询短文件名（AA 1E 00 -> AA 1E <len> <bytes..>）。返回 str 或 None。

        ==========================================

        Query short file name; return str or None.

        """
        self._send_frame(0x1E)
        resp = self._recv_response(expected_cmd=0x1E)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        try:
            return d.decode('ascii') if d else ""
        except Exception:
            return None

    def query_current_track_time(self):
        """
        查询当前播放时间 h:m:s（AA 24 00 -> AA 24 03 h m s）。返回 (h,m,s) 或 None。

        ==========================================

        Query current play time tuple (h,m,s) or None.
        """
        self._send_frame(0x24)
        resp = self._recv_response(expected_cmd=0x24)
        if not resp:
            return None
        d = self._parse_response(resp)['data']
        if len(d) == 3:
            return (d[0], d[1], d[2])
        return None

    # 组合播放（ZH）
    def start_combination_playlist(self, short_names):
        """
        组合播放（ZH 文件夹）。short_names 为 2 字节短名列表，如 ['01','02']。

        Args:
            short_names (list[str]|tuple[str]): 由 2 字节字符串组成的列表/元组（'01'..'ZZ'）

        Raises:
            ValueError: 列表为空、元素不是长度为 2 的 A-Z/0-9 字符串
        ==========================================

        Start combination playlist under ZH; short_names like ['01','02'].

        Args:
            short_names (list[str]|tuple[str]): 2-char strings ('01'..'ZZ')

        Raises:
            ValueError: If empty list or any element invalid
        """
        if not isinstance(short_names, (list, tuple)) or not short_names:
            raise ValueError("short_names 必须为非空列表")
        bb = bytearray()
        for s in short_names:
            if not isinstance(s, str) or len(s) != 2:
                raise ValueError("The  name must be a 2-byte string, for example '01'")
            # 仅允许 A-Z/0-9
            for ch in s:
                o = ord(ch)
                if not (48 <= o <= 57 or 65 <= o <= 90):
                    raise ValueError(" names are only allowed to contain A-Z or 0-9")
            bb.extend(s.encode('ascii'))
        self.uart.write(self._build_frame(0x1B, bytes(bb)))

    def end_combination_playlist(self):
        """
        结束组合播放（AA 1C 00）。

        ==========================================

        End combination playlist (AA 1C 00).



        """
        self._send_frame(0x1C)

    # 播放时间自动上报
    def enable_play_time_send(self):
        """
        使能播放时间自动上报（AA 25 00）。

        ==========================================

        Enable play-time auto report (AA 25 00).

        """
        self._send_frame(0x25)

    def disable_play_time_send(self):
        """
        关闭播放时间自动上报（AA 26 00）。

        ==========================================

        Disable play-time auto report (AA 26 00).

        """
        self._send_frame(0x26)

    def check_play_time_send(self):
        """
        播放进度解析并返回
        ==========================================
        Parse the playback progress and return it
        """
        # 接收期望命令 0x25 的上报帧，超时 1500ms
        resp = self._recv_response(expected_cmd=0x25)
        # 若成功收到完整帧
        if resp:
            # 解析帧得到数据段
            parsed = self._parse_response(resp)
            d = parsed['data']
            # 数据长度为 3 字节时按 (h, m, s) 打印
            if len(d) == 3:
                return d[0], d[1], d[2]


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================