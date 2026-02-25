# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 上午11:22
# @Author  : 李清水
# @File    : buzzer.py
# @Description : 蜂鸣器驱动文件
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time

# 导入硬件相关的模块
from machine import Pin, PWM

# ======================================== 全局变量 ============================================

# 音符到频率的映射
NOTE_FREQS = {
    "C4": 261,
    "D4": 293,
    "E4": 329,
    "F4": 349,
    "G4": 392,
    "A4": 440,
    "B4": 493,
    "C5": 523,
    "D5": 587,
    "E5": 659,
    "F5": 698,
    "G5": 784,
    "A5": 880,
    "B5": 987,
    "C3": 130,
    "D3": 146,
    "E3": 164,
    "F3": 174,
    "G3": 196,
    "A3": 220,
    "B3": 246,
}

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Buzzer:
    """
    蜂鸣器类，用于通过 PWM 驱动蜂鸣器播放音符和旋律。

    该类封装了蜂鸣器的控制逻辑，支持播放单个音符和一段旋律。
    通过 PWM 调节频率和占空比，可以实现不同音调和时长的声音效果。

    Attributes:
        buzzer (PWM): 蜂鸣器的 PWM 实例，用于控制频率和占空比。

    Methods:
        __init__(pin: int) -> None: 初始化蜂鸣器实例。
        play_tone(frequency: int, duration: int) -> None: 播放一个音符。
        play_melody(melody: list) -> None: 播放一段旋律。

    Notes:
        duty_u16=32768 表示 50% 占空比。
        melody 中每个元素为 (note, duration)，如 ('C4', 500)。
        NOTE_FREQS 字典需预定义，映射音符名称到频率。
        每个音符间默认有 10ms 间隔。

    ==========================================

    Buzzer class for driving a buzzer via PWM to play tones and melodies.

    This class encapsulates control logic for the buzzer, supporting
    both single tone playback and melody playback. By adjusting PWM
    frequency and duty cycle, different pitches and durations can be produced.

    Attributes:
        buzzer (PWM): PWM instance bound to buzzer for frequency and duty control.

    Methods:
        __init__(pin: int) -> None: Initialize buzzer instance.
        play_tone(frequency: int, duration: int) -> None: Play a single tone.
        play_melody(melody: list) -> None: Play a melody.

    Notes:
        duty_u16=32768 sets 50% duty cycle.
        melody elements are (note, duration), e.g., ('C4', 500).
        NOTE_FREQS dictionary must be predefined mapping note names to frequencies.
        Default gap of 10ms is inserted between notes.
    """

    def __init__(self, pin: int):
        """
        初始化蜂鸣器实例。

        Args:
            pin (int): 蜂鸣器连接的 GPIO 引脚编号。

        ==========================================

        Initialize buzzer instance.

        Args:
            pin (int): GPIO pin number connected to the buzzer.
        """
        # 设置PWM驱动蜂鸣器
        self.buzzer = PWM(Pin(pin))
        # 初始频率为2000
        self.buzzer.freq(2000)
        # 初始占空比为0
        self.buzzer.duty_u16(0)

    def play_tone(self, frequency: int, duration: int) -> None:
        """
        播放一个音符。

        Args:
            frequency (int): 音符频率（Hz）。
            duration (int): 持续时间（毫秒）。

        Returns:
            None

        ==========================================

        Play a single tone.

        Args:
            frequency (int): Frequency of the tone in Hz.
            duration (int): Duration of the tone in milliseconds.

        Returns:
            None
        """
        # 设置蜂鸣器的频率
        self.buzzer.freq(frequency)
        # 设置占空比为50%
        self.buzzer.duty_u16(32768)
        # 持续时间
        time.sleep_ms(duration)
        # 停止发声
        self.buzzer.duty_u16(0)

    def play_melody(self, melody: list) -> None:
        """
        播放一段旋律。

        Args:
            melody (list): 音符和持续时间的列表。
                           每个元素为元组 (note, duration)，
                           note 为音符名（如 'C4'），duration 为持续时间（毫秒）。
        Returns:
            None

        ==========================================

        Play a melody.

        Args:
            melody (list): List of (note, duration) tuples.
                           note is note name (e.g., 'C4'),
                           duration is duration in milliseconds.

        Returns:
            None
        """
        for note, duration in melody:
            # 根据音符获取频率
            frequency = NOTE_FREQS.get(note, 0)
            if frequency:
                # 播放音符
                self.play_tone(frequency, duration)
            # 每个音符之间的间隔
            time.sleep_ms(10)

    def stop_tone(self) -> None:
        """
        停止播放
        ==========================================
        stop playing
        """
        self.buzzer.duty_u16(0)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
