# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : dy_sv19t.py
# @Description : DY-SV19T 语音播放模块驱动
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"
# ======================================== 导入相关模块 =========================================
#导入常量模块
from micropython import const
# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class DYSV19T:
    """
    DYSV19T 音频模块控制类，通过 UART 实现播放、音量、磁盘选择、状态查询等功能。

    Attributes:
        DISK_USB, DISK_SD, DISK_FLASH, DISK_NONE: 磁盘常量
        PLAY_STOP, PLAY_PLAY, PLAY_PAUSE: 播放状态常量
        MODE_*, EQ_*, CH_*: 播放模式、均衡器、通道常量
        VOLUME_MIN, VOLUME_MAX, DEFAULT_BAUD: 音量与波特率常量

    Methods:
        __init__(uart, ...): 初始化
        play(): 播放
        stop(): 停止
        pause(): 暂停
        set_volume(volume): 设置音量
        query_status(): 查询播放状态
        query_current_disk(): 查询当前磁盘
    ==========================================

    DYSV19T audio module controller via UART, supports playback, volume, disk selection, status query, etc.

    Attributes:
        DISK_USB, DISK_SD, DISK_FLASH, DISK_NONE: Disk constants
        PLAY_STOP, PLAY_PLAY, PLAY_PAUSE: Playback status
        MODE_*, EQ_*, CH_*: Play mode, EQ, channel constants
        VOLUME_MIN, VOLUME_MAX, DEFAULT_BAUD: Volume and baudrate

    Methods:
        __init__(uart, ...): Initialize
        play(): Play
        stop(): Stop
        pause(): Pause
        set_volume(volume): Set volume
        query_status(): Query playback status
        query_current_disk(): Query current disk
    """

    DISK_USB = const(0x00)
    DISK_SD = const(0x01)
    DISK_FLASH = const(0x02)
    DISK_NONE = const(0xFF)

    PLAY_STOP = const(0x00)
    PLAY_PLAY = const(0x01)
    PLAY_PAUSE = const(0x02)

    MODE_FULL_LOOP = const(0x00)
    MODE_SINGLE_LOOP = const(0x01)
    MODE_SINGLE_STOP = const(0x02)
    MODE_FULL_RANDOM = const(0x03)
    MODE_DIR_LOOP = const(0x04)
    MODE_DIR_RANDOM = const(0x05)
    MODE_DIR_SEQUENCE = const(0x06)
    MODE_SEQUENCE = const(0x07)

    EQ_NORMAL = const(0x00)
    EQ_POP = const(0x01)
    EQ_ROCK = const(0x02)
    EQ_JAZZ = const(0x03)
    EQ_CLASSIC = const(0x04)

    CH_MP3 = const(0x00)
    CH_AUX = const(0x01)
    CH_MP3_AUX = const(0x02)

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
        初始化 DYSV19T 类。

        Args:
            uart: UART 实例
            default_volume (int): 默认音量 0-30
            default_disk (int): 默认磁盘
            default_play_mode (int): 默认播放模式
            default_dac_channel (int): 默认 DAC 通道
            timeout_ms (int): UART 超时 ms

        Raises:
            ValueError: uart 不能为空

        ==========================================

        Initialize DYSV19T class.

        Args:
            uart: UART instance
            default_volume (int): Default volume 0-30
            default_disk (int): Default disk
            default_play_mode (int): Default play mode
            default_dac_channel (int): Default DAC channel
            timeout_ms (int): UART timeout ms

        Raises:
            ValueError: If uart is None
        """
        if not uart:
            raise ValueError("UART 实例不能为空 / UART instance required")
        self.uart = uart
        self.volume = default_volume
        self.current_disk = default_disk
        self.play_mode = default_play_mode
        self.dac_channel = default_dac_channel
        self.play_state = self.PLAY_STOP
        self.timeout_ms = timeout_ms

    def build_frame(self, cmd: int, data: bytes) -> bytes:
        """
        构建带校验和的帧。

        Args:
            cmd (int): 命令字节
            data (bytes): 数据

        Returns:
            bytes: 完整帧

        ==========================================

        Build frame with checksum.

        Args:
            cmd (int): Command byte
            data (bytes): Data

        Returns:
            bytes: Complete frame
        """
        frame = bytearray([0xAA, cmd, len(data)] + list(data))
        checksum = sum(frame) & 0xFF
        frame.append(checksum)
        return bytes(frame)

    def send_frame(self, frame: bytes):
        """
        通过 UART 发送帧。

        Args:
            frame (bytes): 要发送的帧

        ==========================================

        Send frame via UART.

        Args:
            frame (bytes): Frame to send
        """
        self.uart.write(frame)

    def recv_response(self, expected_cmd: int = None) -> bytes:
        """
        接收模块响应。

        Args:
            expected_cmd (int, optional): 期望命令字节

        Returns:
            bytes: 响应数据，未匹配返回 None

        ==========================================

        Receive module response.

        Args:
            expected_cmd (int, optional): Expected command byte

        Returns:
            bytes: Response data, None if not matched
        """
        response = self.uart.read(256)
        if response and (expected_cmd is None or response[1] == expected_cmd):
            return response
        return None

    def play(self):
        """
        播放音频。

        ==========================================

        Start audio playback.
        """
        frame = self.build_frame(0x02, b'\x00')
        self.send_frame(frame)
        self.play_state = self.PLAY_PLAY

    def stop(self):
        """
        停止播放。

        ==========================================

        Stop audio playback.
        """
        frame = self.build_frame(0x04, b'\x00')
        self.send_frame(frame)
        self.play_state = self.PLAY_STOP

    def pause(self):
        """
        暂停播放。

        ==========================================

        Pause audio playback.
        """
        frame = self.build_frame(0x03, b'\x00')
        self.send_frame(frame)
        self.play_state = self.PLAY_PAUSE

    def set_volume(self, volume: int):
        """
        设置音量。

        Args:
            volume (int): 音量 0-30

        Raises:
            ValueError: 音量超范围

        ==========================================

        Set volume.

        Args:
            volume (int): Volume 0-30

        Raises:
            ValueError: If out of range
        """
        if not (self.VOLUME_MIN <= volume <= self.VOLUME_MAX):
            raise ValueError("音量必须在 0 到 30 之间 / Volume must be 0-30")
        frame = self.build_frame(0x13, bytes([volume]))
        self.send_frame(frame)
        self.volume = volume

    def query_status(self):
        """
        查询播放状态。

        Returns:
            int: 当前状态，未响应返回 None

        ==========================================

        Query playback status.

        Returns:
            int: Current status, None if no response
        """
        frame = self.build_frame(0x01, b'\x00')
        self.send_frame(frame)
        response = self.recv_response(0x01)
        return response[2] if response else None

    def query_current_disk(self):
        """
        查询当前磁盘。

        Returns:
            int: 当前磁盘，未响应返回 None

        ==========================================

        Query current disk.

        Returns:
            int: Current disk, None if no response
        """
        frame = self.build_frame(0x0A, b'\x00')
        self.send_frame(frame)
        response = self.recv_response(0x0A)
        return response[2] if response else None

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================