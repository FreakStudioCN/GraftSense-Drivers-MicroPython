# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/3/21 下午7:13   
# @Author  : 李清水            
# @File    : dac_waveformgenerator.py       
# @Description : 使用DS3502芯片生成正弦波、三角波、锯齿波的类
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

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
    """
    波形发生器类，用于通过 DS3502 生成正弦波、方波或三角波信号。

    Attributes:
        dac (DS3502): DS3502 数字电位器实例。
        timer (Timer): 定时器对象，用于定时输出采样点。
        frequency (float): 信号频率 (Hz)，范围 (0, 10]。
        amplitude (float): 信号幅度 (V)，范围 [0, vref]。
        offset (float): 信号直流偏移 (V)，范围 [0, vref]。
        waveform (str): 波形类型，可选值为 "sine"、"square"、"triangle"。
        rise_ratio (float): 三角波上升沿比例，范围 [0, 1]。
        vref (float): 参考电压 (V)，必须大于 0。
        sample_rate (int): 每个周期采样点数，固定为 50。
        dac_resolution (int): DS3502 分辨率，固定为 127 (7 位)。
        samples (list[int]): 存储生成的采样点数据 (DS3502 可写入值)。
        index (int): 当前采样点索引。

    Methods:
        __init__(dac, frequency=1, amplitude=1.65, offset=1.65,
                 waveform="sine", rise_ratio=0.5, vref=3.3) -> None: 初始化波形发生器。
        generate_samples() -> list[int]: 生成采样点数据。
        update(t: Timer) -> None: 定时器回调函数，输出下一个采样点。
        start() -> None: 启动波形发生器。
        stop() -> None: 停止波形发生器。

    Notes:
        - 采样点固定为 50 个。
        - DS3502 分辨率为 7 位 (128 个等级)。
        - 超出参数范围会抛出 ValueError。
    ==========================================

    Waveform generator class for generating sine, square, or triangle waveforms via DS3502.

    Attributes:
        dac (DS3502): DS3502 digital potentiometer instance.
        timer (Timer): Timer object for periodic sample output.
        frequency (float): Signal frequency (Hz), range (0, 10].
        amplitude (float): Signal amplitude (V), range [0, vref].
        offset (float): DC offset voltage (V), range [0, vref].
        waveform (str): Waveform type, one of "sine", "square", "triangle".
        rise_ratio (float): Rise slope ratio for triangle wave, range [0, 1].
        vref (float): Reference voltage (V), must be > 0.
        sample_rate (int): Number of samples per period, fixed at 50.
        dac_resolution (int): DS3502 resolution, fixed at 127 (7 bits).
        samples (list[int]): Precomputed DAC values for waveform samples.
        index (int): Current sample index.

    Methods:
        __init__(dac, frequency=1, amplitude=1.65, offset=1.65,
                 waveform="sine", rise_ratio=0.5, vref=3.3) -> None: Initialize waveform generator.
        generate_samples() -> list[int]: Generate waveform sample points.
        update(t: Timer) -> None: Timer callback to output next sample.
        start() -> None: Start waveform generator.
        stop() -> None: Stop waveform generator.

    Notes:
        - Number of samples per period is fixed at 50.
        - DS3502 resolution is 7 bits (128 levels).
        - Raises ValueError if parameters are out of range.
    """

    def __init__(self, dac: 'DS3502', frequency: float = 1, amplitude: float = 1.65, offset: float = 1.65,
                 waveform: str = 'sine', rise_ratio: float = 0.5, vref: float = 3.3) -> None:
        """
        初始化波形发生器。

        Args:
            dac (DS3502): DS3502 数字电位器实例。
            frequency (float, optional): 信号频率，默认 1 Hz，范围 (0, 10]。
            amplitude (float, optional): 信号幅度，默认 1.65V，范围 [0, vref]。
            offset (float, optional): 直流偏移，默认 1.65V，范围 [0, vref]。
            waveform (str, optional): 波形类型，可选 "sine"、"square"、"triangle"，默认 "sine"。
            rise_ratio (float, optional): 三角波上升比例，默认 0.5，范围 [0, 1]。
            vref (float, optional): 参考电压，默认 3.3V，必须 > 0。

        Raises:
            ValueError: 当输入参数超出范围时抛出。

        ==========================================

        Initialize waveform generator.

        Args:
            dac (DS3502): DS3502 digital potentiometer instance.
            frequency (float, optional): Signal frequency, default 1 Hz, range (0, 10].
            amplitude (float, optional): Signal amplitude, default 1.65V, range [0, vref].
            offset (float, optional): DC offset, default 1.65V, range [0, vref].
            waveform (str, optional): Waveform type, "sine", "square", or "triangle", default "sine".
            rise_ratio (float, optional): Rise slope ratio for triangle wave, default 0.5, range [0, 1].
            vref (float, optional): Reference voltage, default 3.3V, must be > 0.

        Raises:
            ValueError: If parameters are out of valid range.
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
        # 信号频率
        self.frequency = frequency
        # 信号幅度
        self.amplitude = amplitude
        # 直流偏移
        self.offset = offset
        # 波形类型
        self.waveform = waveform
        # 三角波上升沿比例
        self.rise_ratio = rise_ratio
        # 偏置电压
        self.vref = vref

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
        根据当前波形类型生成采样点数据。

        Returns:
            list[int]: 包含 DS3502 可写入值的采样点列表。

        ==========================================

        Generate waveform sample points.

        Returns:
            list[int]: List of DAC values corresponding to waveform samples.
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
        定时器回调函数，写入下一个采样点。

        Args:
            t (Timer): 定时器对象。

        ==========================================

        Timer callback function to output the next sample.

        Args:
            t (Timer): Timer instance.
        """
        # 将当前采样点的数据写入 DS3502
        self.dac.write_wiper(self.samples[self.index])
        # 更新采样点索引
        self.index = (self.index + 1) % self.sample_rate

    def start(self) -> None:
        """
        启动波形发生器。

        Notes:
            使用定时器按采样率输出波形。

        ==========================================

        Start waveform generator.

        Notes:
            Uses timer to output samples at defined rate.
        """
        self.timer.init(freq=self.frequency * self.sample_rate, mode=Timer.PERIODIC, callback=self.update)

    def stop(self) -> None:
        """
        停止波形发生器。

        Notes:
            停止定时器并重置采样索引。

        ==========================================

        Stop waveform generator.

        Notes:
            Stops timer and resets sample index.
        """
        self.timer.deinit()
        self.index = 0

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================