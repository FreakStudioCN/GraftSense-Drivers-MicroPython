# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/5 下午3:00
# @Author  : hogeiha
# @File    : snr9816_tts.py
# @Description : SNR9816 TTS语音合成芯片驱动模块

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

import struct
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class SNR9816_TTS:
    """
    SNR9816_TTS类，用于通过UART接口控制SNR9816 TTS语音合成芯片。

    该类封装了SNR9816芯片的通信协议，支持文本合成、状态查询、播放控制及语音参数设置等功能。支持中英文混合文本的语音合成，并可通过指令调节语音参数。

    Attributes:
        _uart (UART): 已配置的UART对象（波特率115200，数据位8，校验位N，停止位1）。
        frame_header (int): 协议帧头固定值0xFD。
        cmd_synthesis (int): 文本合成命令0x01。
        cmd_status (int): 状态查询命令0x21。
        cmd_pause (int): 暂停合成命令0x03。
        cmd_resume (int): 恢复合成命令0x04。
        cmd_stop (int): 停止合成命令0x02。
        encoding_gb2312 (int): GB2312编码标识0x01（当前未使用）。
        encoding_utf8 (int): UTF-8编码标识0x04（当前实际使用）。

    Methods:
        synthesize_text(text: str) -> bool:
            发送文本进行语音合成（使用UTF-8编码）。
        query_status() -> str:
            查询芯片状态，返回"IDLE"（空闲）或"BUSY"（忙碌）。
        pause_synthesis() -> bool:
            暂停当前正在进行的语音合成。
        resume_synthesis() -> bool:
            恢复被暂停的语音合成。
        stop_synthesis() -> bool:
            停止当前语音合成。
        set_voice(voice_type: int) -> bool:
            设置发音人（0=女声，1=男声）。
        set_volume(level: int) -> bool:
            设置音量级别（0-9，0最小，9最大）。
        set_speed(level: int) -> bool:
            设置语速级别（0-9，0最快，9最慢）。
        set_tone(level: int) -> bool:
            设置语调级别（0-9，0最低，9最高）。
        play_ringtone(num: int) -> bool:
            播放系统铃声（1-5）。
        play_message_tone(num: int) -> bool:
            播放信息提示音（1-5）。
        play_alert_tone(num: int) -> bool:
            播放警示音（1-5）。

    注意事项：
        1. 合成文本不支持繁体字和生僻字。
        2. 所有控制指令均通过封装后的协议帧发送。
        3. 语音参数设置通过插入特定控制文本（如"[v5]"）实现。

    ====================================================================

    SNR9816_TTS class for controlling the SNR9816 TTS synthesis chip via UART interface.

    This class encapsulates the communication protocol of the SNR9816 chip, supporting text synthesis, status query, playback control, and voice parameter adjustment. It supports mixed Chinese-English text synthesis and allows voice parameter adjustment via commands.

    Attributes:
        _uart (UART): Configured UART object (baud rate 115200, data bits 8, parity N, stop bits 1).
        frame_header (int): Fixed protocol frame header value 0xFD.
        cmd_synthesis (int): Text synthesis command 0x01.
        cmd_status (int): Status query command 0x21.
        cmd_pause (int): Pause synthesis command 0x03.
        cmd_resume (int): Resume synthesis command 0x04.
        cmd_stop (int): Stop synthesis command 0x02.
        encoding_gb2312 (int): GB2312 encoding identifier 0x01 (currently unused).
        encoding_utf8 (int): UTF-8 encoding identifier 0x04 (currently used).

    Methods:
        synthesize_text(text: str) -> bool:
            Send text for speech synthesis (using UTF-8 encoding).
        query_status() -> str:
            Query chip status, returns "IDLE" or "BUSY".
        pause_synthesis() -> bool:
            Pause current speech synthesis.
        resume_synthesis() -> bool:
            Resume paused speech synthesis.
        stop_synthesis() -> bool:
            Stop current speech synthesis.
        set_voice(voice_type: int) -> bool:
            Set voice type (0=female, 1=male).
        set_volume(level: int) -> bool:
            Set volume level (0-9, 0=minimum, 9=maximum).
        set_speed(level: int) -> bool:
            Set speech rate (0-9, 0=fastest, 9=slowest).
        set_tone(level: int) -> bool:
            Set tone level (0-9, 0=lowest, 9=highest).
        play_ringtone(num: int) -> bool:
            Play system ringtone (1-5).
        play_message_tone(num: int) -> bool:
            Play message tone (1-5).
        play_alert_tone(num: int) -> bool:
            Play alert tone (1-5).

    Notes:
        1. Synthesized text does not support traditional Chinese characters or rare characters.
        2. All control commands are sent via encapsulated protocol frames.
        3. Voice parameters are set by inserting specific control text (e.g., "[v5]").
    """
    def __init__(self, uart):
        """
        构造函数，初始化SNR9816 TTS语音合成模块。

        Args:
            uart (UART): 已配置的UART对象，波特率115200，数据位8，校验位N，停止位1。

        ============================================

        Constructor to initialize the SNR9816 TTS speech synthesis module.

        Args:
            uart (UART): Configured UART object with baud rate 115200,
                        data bits 8, parity N, stop bits 1.

        """
        self._uart = uart
        self.frame_header = 0xFD
        self.cmd_synthesis = 0x01
        self.cmd_status = 0x21
        self.cmd_pause = 0x03
        self.cmd_resume = 0x04
        self.cmd_stop = 0x02
        # 编码方式
        # mpython 不支持 gb2312 编码，所以这里只用 utf-8
        self.encoding_gb2312 = 0x01
        self.encoding_utf8 = 0x04

    def _send_frame(self, cmd, encoding, data_bytes):
        """
        内部方法：发送协议帧到SNR9816模块。

        Args:
            cmd (int): 命令字，如0x01为合成命令。
            encoding (int): 编码方式，0x01为GB2312，0x04为UTF-8。
            data_bytes (bytes): 文本/控制数据的字节串。

        Returns:
            bool: True表示发送成功，False表示发送失败。

        ============================================

        Internal method: Send protocol frame to SNR9816 module.

        Args:
            cmd (int): Command byte, e.g., 0x01 for synthesis command.
            encoding (int): Encoding method, 0x01 for GB2312, 0x04 for UTF-8.
            data_bytes (bytes): Byte string of text/control data.

        Returns:
            bool: True if sent successfully, False if failed.

        """
        if encoding is not 0x04:
            raise ValueError("encoding must be 0x04 (UTF-8)")
        try:
            # 命令字 + 编码参数 + 数据
            length = len(data_bytes) + 2
            length_bytes = struct.pack('>H', length)  # 大端，2字节
            frame = struct.pack('B', self.frame_header) + length_bytes
            frame += struct.pack('B', cmd) + struct.pack('B', encoding) + data_bytes
            self._uart.write(frame)
            return True
        except:
            return False

    def _check_response(self, expected_response=None, timeout_ms=100):
        """
        内部方法：检查模块响应。

        Args:
            expected_response (int|None): 期望的响应字节值。如果为None，则返回实际接收的字节
            timeout_ms (int): 超时时间，单位为毫秒，默认100ms。

        Returns:
            如果expected_response为None: 返回实际接收的字节值（int），超时返回None
            如果指定了expected_response: True表示收到期望响应，False表示超时或未收到期望响应

        ============================================

        Internal method: Check module response.

        Args:
            expected_response (int|None): Expected response byte value. If None, returns actual received byte.
            timeout_ms (int): Timeout in milliseconds, default 100ms.

        Returns:
            If expected_response is None: returns actual received byte (int), None if timeout.
            If expected_response is specified: True if expected response received, False if timeout or not received.
        """
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self._uart.any():
                response = self._uart.read(1)
                if response:
                    received_byte = response[0]
                    if expected_response is None:
                        return received_byte  # 返回实际字节值
                    elif received_byte == expected_response:
                        return True  # 匹配期望值
                    else:
                        return False  # 不匹配期望值
            # 可添加短暂延时避免CPU占用过高
            # time.sleep_ms(1)

        # 超时情况
        if expected_response is None:
            return None  # 超时返回None
        else:
            return False  # 超时返回False

    def synthesize_text(self, text: str):
        """
        合成指定文本为语音。

        Args:
            text (str): 待合成的文本字符串，不支持繁体字和生僻字。

        Returns:
            bool: True表示指令发送成功，False表示发送失败。

        Note:
            实际使用UTF-8编码发送

        ============================================

        Synthesize specified text to speech.

        Args:
            text (str): Text string to be synthesized. Does not support traditional Chinese or rare characters.

        Returns:
            bool: True if command sent successfully, False if failed.

        Note:
            Actually uses UTF-8 encoding to send
        """
        status = self.query_status()
        if status != "IDLE":
            print(f"Chip is busy (status: {status}), cannot synthesize now.")
            return False

        data_bytes = text.encode('utf-8')
        return self._send_frame(self.cmd_synthesis, self.encoding_utf8, data_bytes)

    def query_status(self) -> str:
        """
        查询芯片当前工作状态。

        Returns:
            str: "IDLE"表示芯片空闲，"BUSY"表示芯片忙碌，"UNKNOWN"表示状态未知。

        ============================================

        Query the current working status of the chip.

        Returns:
            str: "IDLE" means chip is idle, "BUSY" means chip is busy, "UNKNOWN" means status is unknown.
        """

        self.cmd = bytes([0xFD, 0x00, 0x01, 0x21])
        self._uart.write(self.cmd)
        self.response = self._check_response(expected_response=None, timeout_ms=100)
        if self.response is 0x4E:
            return "BUSY"
        if self.response is 0x4F:
            return "IDLE"
        return "UNKNOWN"

    def pause_synthesis(self) -> bool:
        """
        暂停当前正在进行的语音合成。

        Returns:
            bool: True表示暂停指令发送成功且收到确认响应，False表示失败。

        ============================================

        Pause the currently ongoing speech synthesis.

        Returns:
            bool: True if pause command sent successfully and acknowledgment received, False if failed.
        """
        self.cmd = bytes([0XFD, 0X00, 0X01, 0X03])
        self.response = self._check_response(expected_response=None, timeout_ms=100)
        if self._uart.write(self.cmd):
            if self.response is 0x41:
                return True
        return False

    def resume_synthesis(self) -> bool:
        """
        继续已暂停的语音合成。

        Returns:
            bool: True表示继续指令发送成功且收到确认响应，False表示失败。

        ============================================

        Resume the paused speech synthesis.

        Returns:
            bool: True if resume command sent successfully and acknowledgment received, False if failed.
        """
        self.cmd = bytes([0XFD, 0X00, 0X01, 0X04])
        self.response = self._check_response(expected_response=None, timeout_ms=100)
        if self._uart.write(self.cmd):
            if self.response is 0x41:
                return True
        return False

    def stop_synthesis(self) -> bool:
        """
        终止当前语音合成。

        Returns:
            bool: True表示停止指令发送成功且收到确认响应，False表示失败。

        ============================================

        Stop the current speech synthesis.

        Returns:
            bool: True if stop command sent successfully and acknowledgment received, False if failed.
        """
        self.cmd = bytes([0XFD, 0X00, 0X01, 0X02])
        self.response = self._check_response(expected_response=None, timeout_ms=100)
        if self._uart.write(self.cmd):
            if self.response is 0x41:
                return True
        return False

    def set_voice(self, voice_type: int) -> bool:
        """
        设置发音人类型。

        Args:
            voice_type (int): 0=女声，1=男声。

        Returns:
            bool: True表示指令发送成功，False表示失败。

        Raises:
            ValueError: 如果voice_type不是0或1。

        ============================================

        Set the voice type.

        Args:
            voice_type (int): 0=female voice, 1=male voice.

        Returns:
            bool: True if command sent successfully, False if failed.

        Raises:
            ValueError: If voice_type is not 0 or 1.
        """
        if voice_type not in (0, 1):
            raise ValueError("voice_type must be 0 (female) or 1 (male)")
        text = f"[m{voice_type}]"
        return self.synthesize_text(text)

    def set_volume(self, level: int) -> bool:
        """
        设置语音合成音量级别。

        Args:
            level (int): 音量级别，范围0-9，0为最小，9为最大。

        Returns:
            bool: True表示指令发送成功，False表示失败。

        Raises:
            ValueError: 如果level不在0-9范围内。

        ============================================

        Set the volume level for speech synthesis.

        Args:
            level (int): Volume level, range 0-9, 0 is minimum, 9 is maximum.

        Returns:
            bool: True if command sent successfully, False if failed.

        Raises:
            ValueError: If level is not in range 0-9.
        """
        if level < 0 or level > 9:
            raise ValueError("level must be between 0 and 9")
        text = f"[v{level}]"
        return self.synthesize_text(text)

    def set_speed(self, level: int) -> bool:
        """
        设置语音合成语速级别。

        Args:
            level (int): 语速级别，范围0-9，0为最快，9为最慢。

        Returns:
            bool: True表示指令发送成功，False表示失败。

        Raises:
            ValueError: 如果level不在0-9范围内。

        ============================================

        Set the speech rate level for synthesis.

        Args:
            level (int): Speech rate level, range 0-9, 0 is fastest, 9 is slowest.

        Returns:
            bool: True if command sent successfully, False if failed.

        Raises:
            ValueError: If level is not in range 0-9.
        """
        if level < 0 or level > 9:
            raise ValueError("level must be between 0 and 9")
        text = f"[s{level}]"
        return self.synthesize_text(text)

    def set_tone(self, level: int) -> bool:
        """
        设置语音合成语调级别。

        Args:
            level (int): 语调级别，范围0-9，0为最低，9为最高。

        Returns:
            bool: True表示指令发送成功，False表示失败。

        Raises:
            ValueError: 如果level不在0-9范围内。

        ============================================

        Set the tone level for speech synthesis.

        Args:
            level (int): Tone level, range 0-9, 0 is lowest, 9 is highest.

        Returns:
            bool: True if command sent successfully, False if failed.

        Raises:
            ValueError: If level is not in range 0-9.
        """
        if level < 0 or level > 9:
            raise ValueError("level must be between 0 and 9")
        text = f"[t{level}]"
        return self.synthesize_text(text)

    def play_ringtone(self, num: int) -> bool:
        """
        播放系统铃声。

        Args:
            num (int): 铃声编号，范围1-5，对应ring_1到ring_5。

        Returns:
            bool: True表示指令发送成功，False表示失败。

        Raises:
            ValueError: 如果num不在1-5范围内。

        ============================================

        Play system ringtone.

        Args:
            num (int): Ringtone number, range 1-5, corresponding to ring_1 to ring_5.

        Returns:
            bool: True if command sent successfully, False if failed.

        Raises:
            ValueError: If num is not in range 1-5.
        """
        if num < 1 or num > 5:
            return False
        text = f"ring_{num}"
        return self.synthesize_text(text)

    def play_message_tone(self, num: int) -> bool:
        """
        播放信息提示音。

        Args:
            num (int): 提示音编号，范围1-5，对应message_1到message_5。

        Returns:
            bool: True表示指令发送成功，False表示失败。

        Raises:
            ValueError: 如果num不在1-5范围内。

        ============================================

        Play message notification tone.

        Args:
            num (int): Message tone number, range 1-5, corresponding to message_1 to message_5.

        Returns:
            bool: True if command sent successfully, False if failed.

        Raises:
            ValueError: If num is not in range 1-5.
        """
        if num < 1 or num > 5:
            raise ValueError("num must be between 1 and 5")
        text = f"message_{num}"
        return self.synthesize_text(text)


    def play_alert_tone(self, num: int) -> bool:
        """
        播放警示音。

        Args:
            num (int): 警示音编号，范围1-5，对应alert_1到alert_5。

        Returns:
            bool: True表示指令发送成功，False表示失败。

        Raises:
            ValueError: 如果num不在1-5范围内。

        ============================================

        Play alert tone.

        Args:
            num (int): Alert tone number, range 1-5, corresponding to alert_1 to alert_5.

        Returns:
            bool: True if command sent successfully, False if failed.

        Raises:
            ValueError: If num is not in range 1-5.
        """
        if num < 1 or num > 5:
            raise ValueError("num must be between 1 and 5")
        text = f"alert_{num}"
        return self.synthesize_text(text)

    # ======================================== 初始化配置 ==========================================

    # ========================================  主程序  ===========================================
