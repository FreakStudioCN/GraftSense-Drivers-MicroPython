# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/3/21 下午7:13   
# @Author  : 李清水            
# @File    : dac_waveformgenerator.py       
# @Description : 使用DS3502芯片生成正弦波、三角波、锯齿波的类
# 这部分代码由 leeqingshui 开发，采用CC BY-NC 4.0许可协议

# ======================================== 导入相关模块 =========================================

# 导入数学库用于计算正弦波
import math
# 导入硬件模块
from machine import Timer
# 导入ds3502模块用于控制数字电位器芯片
from ds3502 import DS3502

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class WaveformGenerator:
    def __init__(self, dac: 'DS3502', frequency: float = 1, amplitude: float = 1.65, offset: float = 1.65,
                 waveform: str = 'sine', rise_ratio: float = 0.5, vref: float = 3.3) -> None:
        """
        初始化波形发生器实例。

        该方法用于初始化波形发生器的基本设置，包括 DS3502 对象、信号频率、幅度、偏移、波形类型、三角波的上升斜率以及偏置电压。

        Args:
            dac (DS3502): DS3502 数字电位器实例，用于生成波形信号。
            frequency (float, optional): 信号频率，默认值为 1 Hz。必须大于 0 并小于等于 10 Hz。
            amplitude (float, optional): 信号幅度，默认值为 1.65V。必须在 0 到 vref 之间。
            offset (float, optional): 直流偏移，默认值为 1.65V。必须在 0 到 vref 之间。
            waveform (str, optional): 波形类型，可以是 'sine'（正弦波）、'square'（方波）或 'triangle'（三角波），默认值为 'sine'。
            rise_ratio (float, optional): 三角波的上升斜率，默认为 0.5，值必须在 0 到 1 之间。
            vref (float, optional): 偏置电压，默认值为 3.3V。必须大于 0。

        Returns:
            None: 此方法没有返回值。

        Raises:
            ValueError: 如果传入的参数不在预定范围内，将抛出该异常。
        """
        # 参数输入检查
        if not (0 < frequency <= 10):
            raise ValueError("Frequency must be between 0 and 10 Hz.")
        if not (0 <= amplitude <= vref):
            raise ValueError(f"Amplitude must be between 0 and {vref}V.")
        if not (0 <= offset <= vref):
            raise ValueError(f"Offset must be between 0 and {vref}V.")
        if not (0 <= amplitude + offset <= vref):
            raise ValueError(f"Amplitude + offset must be between 0 and {vref}V.")
        if waveform not in ['sine', 'square', 'triangle']:
            raise ValueError("Waveform must be 'sine', 'square', or 'triangle'.")
        if not (0 <= rise_ratio <= 1):
            raise ValueError("Rise ratio must be between 0 and 1.")
        if vref <= 0:
            raise ValueError("Vref must be greater than 0.")

        # 保存 DS3502 对象
        self.dac = dac

        # 初始化定时器对象
        self.timer = Timer(-1)

        # 保存波形生成器的参数
        self.frequency = frequency  # 信号频率
        self.amplitude = amplitude  # 信号幅度
        self.offset = offset  # 直流偏移
        self.waveform = waveform  # 波形类型
        self.rise_ratio = rise_ratio  # 三角波上升沿比例
        self.vref = vref  # 偏置电压

        # 固定 50 个采样点
        self.sample_rate = 50

        # DS3502 的分辨率为 7 位（128 级）
        self.dac_resolution = 127

        # 根据波形类型生成采样点数据
        self.samples = self.generate_samples()

        # 初始化当前采样点索引
        self.index = 0

    def generate_samples(self) -> list[int]:
        """
        根据波形类型生成采样点数据。

        Returns:
            list[int]: 包含转换为 DS3502 数值的采样点列表。
        """
        # 将电压值转换为 DS3502 值的函数
        def to_dac_value(voltage):
            # DS3502 的分辨率为 7 位，电压范围为 0 到 vref
            return int(voltage / self.vref * self.dac_resolution)

        # 初始化一个列表用于存储生成的采样点数据
        samples = []

        # 根据选定的波形生成采样点数据
        if self.waveform == 'sine':
            # 正弦波
            for i in range(self.sample_rate):
                angle = 2 * math.pi * i / self.sample_rate
                voltage = self.offset + self.amplitude * math.sin(angle)
                samples.append(to_dac_value(voltage))

        elif self.waveform == 'square':
            # 方波
            for i in range(self.sample_rate):
                if i < self.sample_rate // 2:
                    # 高电平
                    voltage = self.offset + self.amplitude
                else:
                    # 低电平
                    voltage = self.offset - self.amplitude
                samples.append(to_dac_value(voltage))

        elif self.waveform == 'triangle':
            # 三角波
            for i in range(self.sample_rate):
                if i < self.sample_rate * self.rise_ratio:
                    voltage = self.offset + 2 * self.amplitude * (
                            i / (self.sample_rate * self.rise_ratio)) - self.amplitude
                else:
                    voltage = self.offset + 2 * self.amplitude * (
                            (self.sample_rate - i) / (self.sample_rate * (1 - self.rise_ratio))) - self.amplitude
                samples.append(to_dac_value(voltage))

        return samples

    def update(self, t: Timer) -> None:
        """
        定时器回调函数，用于输出下一个采样点的数据。

        Args:
            t (Timer): 定时器对象。
        """
        # 将当前采样点的数据写入 DS3502
        self.dac.write_wiper(self.samples[self.index])
        # 更新采样点索引
        self.index = (self.index + 1) % self.sample_rate

    def start(self) -> None:
        """
        启动波形生成器，开始定时器。
        """
        self.timer.init(freq=self.frequency * self.sample_rate, mode=Timer.PERIODIC, callback=self.update)

    def stop(self) -> None:
        """
        停止波形生成器，停止定时器。
        """
        self.timer.deinit()
        self.index = 0

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================