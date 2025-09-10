# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : dy_sv19t.py
# @Description : DY-SV19T的语音播放模块驱动
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CCBYNC

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CCBYNC"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================

from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class DYSV19T:
    """
    DYSV19T 音频模块控制类
    ================================
    该类通过 UART 与 DYSV19T 音频模块进行通信，控制播放、音量、磁盘选择，并查询模块状态。

    公共方法:
    - play(): 开始音频播放。
    - stop(): 停止音频播放。
    - pause(): 暂停音频播放。
    - set_volume(volume: int): 设置音量。
    - query_status(): 查询当前状态。
    - query_current_disk(): 查询当前使用的磁盘。

    常量:
    - PLAY_STOP, PLAY_PLAY, PLAY_PAUSE: 播放状态。
    - MODE_*: 各种播放模式。
    - EQ_*: 均衡器预设。
    - CH_*: DAC 通道选项。
    DYSV19T Audio Module Control Class
    ================================
    This class communicates with the DYSV19T audio module via UART to control playback, volume, disk selection, and query the module status.

    Public Methods:
    - play(): Starts audio playback.
    - stop(): Stops audio playback.
    - pause(): Pauses audio playback.
    - set_volume(volume: int): Sets the volume.
    - query_status(): Queries the current status.
    - query_current_disk(): Queries the currently used disk.

    Constants:
    - PLAY_STOP, PLAY_PLAY, PLAY_PAUSE: Playback statuses.
    - MODE_*: Various playback modes.
    - EQ_*: Equalizer presets.
    - CH_*: DAC channel options.
    """

    # 磁盘常量
    DISK_USB = const(0x00)
    DISK_SD = const(0x01)
    DISK_FLASH = const(0x02)
    DISK_NONE = const(0xFF)

    # 播放状态常量
    PLAY_STOP = const(0x00)
    PLAY_PLAY = const(0x01)
    PLAY_PAUSE = const(0x02)

    # 播放模式常量
    MODE_FULL_LOOP = const(0x00)
    MODE_SINGLE_LOOP = const(0x01)
    MODE_SINGLE_STOP = const(0x02)
    MODE_FULL_RANDOM = const(0x03)
    MODE_DIR_LOOP = const(0x04)
    MODE_DIR_RANDOM = const(0x05)
    MODE_DIR_SEQUENCE = const(0x06)
    MODE_SEQUENCE = const(0x07)

    # 均衡器常量
    EQ_NORMAL = const(0x00)
    EQ_POP = const(0x01)
    EQ_ROCK = const(0x02)
    EQ_JAZZ = const(0x03)
    EQ_CLASSIC = const(0x04)

    # DAC 通道常量
    CH_MP3 = const(0x00)
    CH_AUX = const(0x01)
    CH_MP3_AUX = const(0x02)

    # 音量常量
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

        参数:
            uart (UART): 用于通信的 UART 实例。
            default_volume (int): 默认音量级别（0-30）。
            default_disk (int): 默认磁盘源。
            default_play_mode (int): 默认播放模式。
            default_dac_channel (int): 默认 DAC 通道。
            timeout_ms (int): UART 操作超时（单位：毫秒）。

        异常:
        ================================
            ValueError: 如果 uart 为 None。
            Initialize the DYSV19T class.

        Parameters:
            uart (UART): UART instance used for communication.
            default_volume (int): Default volume level (0-30).
            default_disk (int): Default disk source.
            default_play_mode (int): Default play mode.
            default_dac_channel (int): Default DAC channel.
            timeout_ms (int): Timeout for UART operations (in milliseconds).

        Exceptions:
            ValueError: If uart is None.
        """
        if not uart:
            raise ValueError("UART 实例不能为空")
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

        参数:
            cmd (int): 命令字节。
            data (bytes): 包含的数据。

        返回:
            bytes: 完整的帧，包括校验和。
        ================================
            Construct a frame with a checksum.

        Parameters:
            cmd (int): Command byte.
            data (bytes): Included data.

        Returns:
            bytes: Complete frame, including the checksum.

        """
        frame = bytearray([0xAA, cmd, len(data)] + list(data))
        checksum = sum(frame) & 0xFF
        frame.append(checksum)
        return bytes(frame)

    def send_frame(self, frame: bytes):
        """
        通过 UART 发送帧。

        参数:
            frame (bytes): 要发送的帧。
        ================================
        Send frames via UART.

        Parameters:
            frame (bytes): The frame to be sent.
        """
        self.uart.write(frame)

    def recv_response(self, expected_cmd: int = None) -> bytes:
        """
        接收模块的响应。

        参数:
            expected_cmd (int, 可选): 用于过滤响应的命令字节。

        返回:
            bytes: 模块的响应字节，若无响应则返回 None。
        ================================
        Receive the response from the module.

        Parameters:
            expected_cmd (int, optional): The command byte used to filter the response.

        Returns:
            bytes: The response bytes from the module; returns None if there is no response.
        """
        response = self.uart.read(256)
        if response and (response[1] == expected_cmd or expected_cmd is None):
            return response
        return None

    def play(self):
        """
        发送播放命令开始播放音频。
        ================================
        Send a play command to start playing the audio.
        """
        frame = self.build_frame(0x02, b'\x00')
        self.send_frame(frame)
        self.play_state = self.PLAY_PLAY

    def stop(self):
        """
        发送停止命令停止音频播放。
        ================================
        Send a stop command to stop audio playback.
        """
        frame = self.build_frame(0x04, b'\x00')
        self.send_frame(frame)
        self.play_state = self.PLAY_STOP

    def pause(self):
        """
        发送暂停命令暂停音频播放。
        ================================
        Send a pause command to pause audio playback.
        """
        frame = self.build_frame(0x03, b'\x00')
        self.send_frame(frame)
        self.play_state = self.PLAY_PAUSE

    def set_volume(self, volume: int):
        """
        设置音量。

        参数:
            volume (int): 音量级别，范围是 0 到 30。

        异常:
            ValueError: 如果音量超出范围（0-30）。
            Set the volume.
        ================================
        Parameters:
            volume (int): The volume level, ranging from 0 to 30.

        Exceptions:
            ValueError: If the volume is out of the range (0-30).
        """
        if volume < self.VOLUME_MIN or volume > self.VOLUME_MAX:
            raise ValueError("音量必须在 0 到 30 之间。")
        frame = self.build_frame(0x13, bytes([volume]))
        self.send_frame(frame)
        self.volume = volume

    def query_status(self):
        """
        查询当前模块的播放状态。

        返回:
            bytes: 模块的响应，指示当前状态。
        ================================
            Query the playback status of the current module.

        Returns:
            bytes: The module's response indicating the current status.
        """
        frame = self.build_frame(0x01, b'\x00')
        self.send_frame(frame)
        response = self.recv_response(0x01)
        return response[2] if response else None

    def query_current_disk(self):
        """
        查询当前使用的磁盘。

        返回:
            bytes: 模块的响应，指示当前使用的磁盘。
        ================================
              Query the currently used disk.

        Returns:
            bytes: The response of the module, indicating the currently used disk.
        """
        frame = self.build_frame(0x0A, b'\x00')
        self.send_frame(frame)
        response = self.recv_response(0x0A)
        return response[2] if response else None

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
