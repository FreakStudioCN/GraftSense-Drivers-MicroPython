# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午3:31
# @Author  : 缪贵成
# @File    : lm386_speaker.py
# @Description : 基于LM386的功率放大扬声器模块驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, PWM
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class LMSpeaker:
    """
    该类控制基于 LM386 功率放大器的扬声器模块，提供音调播放、音符序列播放和音量调节功能。

    Attributes:
        pin (Pin): machine.Pin 实例，PWM 输出引脚。
        freq (int): 默认 PWM 频率，单位 Hz。
        _pwm (PWM): machine.PWM 实例，用于产生方波信号。

    Methods:
        play_tone(frequency: int, duration: float) -> None: 播放指定频率和时长的单音。
        play_sequence(notes: list[tuple[int, float]]) -> None: 播放一系列音符序列。
        set_volume(percent: int) -> None: 设置音量百分比（1–100%）。
        stop() -> None: 停止播放并静音。

    Notes:
        - 占空比通过 PWM 控制，不同平台 duty 范围不同（ESP32/8266 0–1023，RP2040/STM32 0–65535）。
        - 本类不进行音频解码，只产生方波驱动 LM386。
        - 在 ISR 中调用可能不安全，请使用 micropython.schedule 延迟执行。

    ==========================================

    LMSpeaker driver for LM386 amplifier-based speaker module.
    Provides tone playing, note sequences, and volume control.

    Attributes:
        pin (Pin): machine.Pin instance for PWM output.
        freq (int): default PWM frequency in Hz.
        _pwm (PWM): machine.PWM instance for waveform generation.

    Methods:
        play_tone(frequency: int, duration: float) -> None: Play a single tone.
        play_sequence(notes: list[tuple[int, float]]) -> None: Play a sequence of notes.
        set_volume(percent: int) -> None: Set output volume in percentage (1–100%).
        stop() -> None: Stop output and mute speaker.

    Notes:
        - PWM duty mapping depends on platform (0–1023 or 0–65535).
        - Only generates square waves, no audio decoding.
        - Not ISR-safe. Use micropython.schedule for deferred calls.
    """
    def __init__(self, pin: int, freq: int = 1000):
        """
        初始化扬声器模块。

        Args:
            pin (int): PWM 输出引脚编号。
            freq (int): 默认 PWM 频率，单位 Hz，默认 1000 Hz。

        Notes:
            初始化时会立即配置 PWM，但不会产生声音。

        ==========================================

        Initialize LMSpeaker.

        Args:
            pin (int): Pin number for PWM output.
            freq (int): Default PWM frequency in Hz. Default is 1000 Hz.

        Notes:
            PWM is configured at init but kept muted.
        """
        self.pin = Pin(pin)
        self.freq = freq
        self._pwm = None
        self._init_pwm()

    def _init_pwm(self):
        """
        初始化 PWM 硬件并静音。

        Notes:
            仅供内部使用。

        ==========================================

        Initialize PWM hardware and mute output.

        Notes:
            Internal use only.
        """
        self._pwm = PWM(self.pin)
        self._pwm.freq(self.freq)
        self._pwm.duty_u16(0)  # mute by default (0–65535)

    def play_tone(self, frequency: int, duration: float):
        """
        播放指定频率的单音。

        Args:
            frequency (int): 音调频率，单位 Hz。
            duration (float): 持续时间，单位秒。

        Notes:
            播放后会自动调用 stop() 静音。

        ==========================================

        Play a tone with given frequency.

        Args:
            frequency (int): Tone frequency in Hz.
            duration (float): Duration in seconds.

        Notes:
            stop() is called automatically after playback.
        """
        # 人耳可听频率理论在20Hz-20kHz
        self._pwm.freq(frequency)
        self._pwm.duty_u16(32768)
        time.sleep(duration)
        self.stop()

    def play_sequence(self, notes: list[tuple[int, float]]):
        """
        播放一系列音符序列。

        Args:
            notes (list): 列表，每个元素为 (frequency:int, duration:float)。

        Notes:
            每个音符间有约 0.05 秒间隔。

        ==========================================

        Play a sequence of notes.

        Args:
            notes (list): List of tuples (frequency:int, duration:float).

        Notes:
            Adds ~0.05s pause between notes.
        """
        for freq, dur in notes:
            self.play_tone(freq, dur)
            # short pause between notes
            time.sleep(0.05)

    def set_volume(self, percent: int):
        """
        设置音量百分比（1–100）。

        Args:
            percent (int): 音量百分比，范围 1–100。

        Raises:
            RuntimeError: 如果 PWM 驱动不支持 duty 设置。

        Notes:
            内部会根据平台映射到 0–65535 或 0–1023。

        ==========================================

        Set speaker volume (1–100%).

        Args:
            percent (int): Volume percentage.

        Raises:
            RuntimeError: If PWM driver unsupported.

        Notes:
            Duty mapped to platform-specific range (0–65535 or 0–1023).
        """
        # Clamp percent into [1, 100]
        percent = max(1, min(100, percent))
        # Map to PWM duty range
        if hasattr(self._pwm, "duty_u16"):
            # MicroPython (0–65535)
            duty = int(percent / 100 * 65535)
            self._pwm.duty_u16(duty)
        elif hasattr(self._pwm, "duty"):
            # MicroPython ESP8266/ESP32 (0–1023)
            duty = int(percent / 100 * 1023)
            self._pwm.duty(duty)
        else:
            raise RuntimeError("Unsupported PWM driver")

    def stop(self):
        """
        停止播放并静音。

        Notes:
            通过 duty=0 实现静音。

        ==========================================

        Stop playback and mute.

        Notes:
            Mute achieved by setting duty=0.
        """
        self._pwm.duty_u16(0)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
