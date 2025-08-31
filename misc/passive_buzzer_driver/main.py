# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/19 下午9:09   
# @Author  : 李清水            
# @File    : main.py       
# @Description : PWM类使用，驱动蜂鸣器播放MIDI音乐

# ======================================== 导入相关模块 =========================================

# 导入硬件相关的模块
from machine import Pin, PWM
# 导入时间相关模块
import time

# ======================================== 全局变量 ============================================

# 音符到频率的映射
NOTE_FREQS = {
    'C4': 261, 'D4': 293, 'E4': 329, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 493,
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784, 'A5': 880, 'B5': 987,
    'C3': 130, 'D3': 146, 'E3': 164, 'F3': 174, 'G3': 196, 'A3': 220, 'B3': 246
}

# 小星星的旋律和节奏:即每个音符和其对应持续时间
MELODY = [
    ('C4', 400), ('C4', 400), ('G4', 400), ('G4', 400), ('A4', 400), ('A4', 400), ('G4', 800),
    ('F4', 400), ('F4', 400), ('E4', 400), ('E4', 400), ('D4', 400), ('D4', 400), ('C4', 800),
    ('G4', 400), ('G4', 400), ('F4', 400), ('F4', 400), ('E4', 400), ('E4', 400), ('D4', 800),
    ('G4', 400), ('G4', 400), ('F4', 400), ('F4', 400), ('E4', 400), ('E4', 400), ('D4', 800),
    ('C4', 400), ('C4', 400), ('G4', 400), ('G4', 400), ('A4', 400), ('A4', 400), ('G4', 800),
    ('F4', 400), ('F4', 400), ('E4', 400), ('E4', 400), ('D4', 400), ('D4', 400), ('C4', 800)
]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 蜂鸣器类
class Buzzer:
    """
    蜂鸣器类，用于通过PWM驱动蜂鸣器播放音符和旋律。

    该类封装了对蜂鸣器的控制逻辑，支持播放单个音符和一段旋律。通过PWM调节频率和占空比，
    可以实现不同音调和时长的声音效果。

    Attributes:
        buzzer (PWM): 蜂鸣器的PWM实例，用于控制频率和占空比。

    Methods:
        __init__(self, pin: int):
            初始化蜂鸣器类实例。

        play_tone(self, frequency: int, duration: int) -> None:
            播放一个音符。

        play_melody(self, melody: list) -> None:
            播放一段旋律。
    """

    def __init__(self, pin: int):
        """
        初始化蜂鸣器。

        Args:
            pin (int): 蜂鸣器连接的GPIO引脚编号。
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
            frequency (int): 音符的频率（赫兹）。
            duration (int): 音符的持续时间（毫秒）。

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
            melody (list): 旋律的音符和持续时间列表，每个元素为一个元组 (note, duration)。
                           note为音符名称（如 'C4'），duration为持续时间（毫秒）。

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

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio : Use PWM to drive a buzzer to play MIDI music")
# 初始化蜂鸣器对象
buzzer = Buzzer(pin=9)

# ========================================  主程序  ===========================================

# 循环播放音乐
while True:
    # 播放旋律《致爱丽丝》
    buzzer.play_melody(MELODY)