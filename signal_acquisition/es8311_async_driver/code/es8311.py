# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : M5Stack Technology CO LTD, FreakStudio
# @File    : es8311.py
# @Description : ES8311 音频编解码器 I2C 配置驱动
# @License : MIT

# 参考源码：m5stack/uiflow-micropython m5stack/libs/driver/es8311
# 说明：将原 M5Stack 的 __init__.py 和 reg.py 机械合并为单文件后规范化
# 注意：本驱动仅负责 I2C 寄存器配置，I2S 音频数据流由应用层 machine.I2S 处理

__version__ = "1.0.0"
__author__ = "M5Stack Technology CO LTD, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# const() 兼容性导入（MicroPython 内置，部分端口可能不支持）
try:
    from micropython import const
except ImportError:

    def const(x):
        return x


import time

# ======================================== 全局变量 ============================================

# --- 寄存器地址常量（ES8311 寄存器映射表）---

ES8311_RESET_REG00 = const(0x00)  # 复位数字、CSM、时钟管理等

# 时钟方案寄存器
ES8311_CLK_MANAGER_REG01 = const(0x01)  # 选择 MCLK 时钟源，启用编解码器时钟
ES8311_CLK_MANAGER_REG02 = const(0x02)  # 时钟分频器和倍频器
ES8311_CLK_MANAGER_REG03 = const(0x03)  # ADC fs 模式和 OSR
ES8311_CLK_MANAGER_REG04 = const(0x04)  # DAC OSR
ES8311_CLK_MANAGER_REG05 = const(0x05)  # ADC 和 DAC 时钟分频器
ES8311_CLK_MANAGER_REG06 = const(0x06)  # BCLK 反相器和分频器
ES8311_CLK_MANAGER_REG07 = const(0x07)  # 三态，LRCK 分频器
ES8311_CLK_MANAGER_REG08 = const(0x08)  # LRCK 分频器

# SDP 串行数字端口
ES8311_SDPIN_REG09 = const(0x09)  # DAC 串行数字端口
ES8311_SDPOUT_REG0A = const(0x0A)  # ADC 串行数字端口

# 系统寄存器
ES8311_SYSTEM_REG0B = const(0x0B)  # 系统
ES8311_SYSTEM_REG0C = const(0x0C)  # 系统
ES8311_SYSTEM_REG0D = const(0x0D)  # 系统，电源上下电
ES8311_SYSTEM_REG0E = const(0x0E)  # 系统，电源上下电
ES8311_SYSTEM_REG0F = const(0x0F)  # 系统，低功耗
ES8311_SYSTEM_REG10 = const(0x10)  # 系统
ES8311_SYSTEM_REG11 = const(0x11)  # 系统
ES8311_SYSTEM_REG12 = const(0x12)  # 系统，启用 DAC
ES8311_SYSTEM_REG13 = const(0x13)  # 系统
ES8311_SYSTEM_REG14 = const(0x14)  # 系统，选择 DMIC，选择模拟 PGA 增益

# ADC 寄存器
ES8311_ADC_REG15 = const(0x15)  # ADC，ADC 斜坡率，DMIC 感应
ES8311_ADC_REG16 = const(0x16)  # ADC
ES8311_ADC_REG17 = const(0x17)  # ADC，音量
ES8311_ADC_REG18 = const(0x18)  # ADC，ALC 使能和窗口大小
ES8311_ADC_REG19 = const(0x19)  # ADC，ALC 最大电平
ES8311_ADC_REG1A = const(0x1A)  # ADC，ALC 自动静音
ES8311_ADC_REG1B = const(0x1B)  # ADC，ALC 自动静音，ADC HPF s1
ES8311_ADC_REG1C = const(0x1C)  # ADC，均衡器，HPF s2

# DAC 寄存器
ES8311_DAC_REG31 = const(0x31)  # DAC，静音
ES8311_DAC_REG32 = const(0x32)  # DAC，音量
ES8311_DAC_REG33 = const(0x33)  # DAC，偏移
ES8311_DAC_REG34 = const(0x34)  # DAC，DRC 使能，DRC 窗口大小
ES8311_DAC_REG35 = const(0x35)  # DAC，DRC 最大电平，最小电平
ES8311_DAC_REG37 = const(0x37)  # DAC，斜坡率

# GPIO 寄存器
ES8311_GPIO_REG44 = const(0x44)  # GPIO，DAC 到 ADC 测试
ES8311_GP_REG45 = const(0x45)  # GP 控制

# 芯片 ID 和版本寄存器
ES8311_CHD1_REGFD = const(0xFD)  # 芯片 ID1
ES8311_CHD2_REGFE = const(0xFE)  # 芯片 ID2
ES8311_CHVER_REGFF = const(0xFF)  # 版本

ES8311_MAX_REGISTER = const(0xFF)


# --- 时钟系数数据结构（替代 namedtuple，避免依赖 collections 模块）---


class _CoeffDiv:
    """时钟系数数据容器，用于构建采样率查找表"""

    __slots__ = ("mclk", "rate", "pre_div", "pre_multi", "adc_div", "dac_div", "fs_mode", "lrck_h", "lrck_l", "bclk_div", "adc_osr", "dac_osr")

    def __init__(self, mclk, rate, pre_div, pre_multi, adc_div, dac_div, fs_mode, lrck_h, lrck_l, bclk_div, adc_osr, dac_osr):
        self.mclk = mclk
        self.rate = rate
        self.pre_div = pre_div
        self.pre_multi = pre_multi
        self.adc_div = adc_div
        self.dac_div = dac_div
        self.fs_mode = fs_mode
        self.lrck_h = lrck_h
        self.lrck_l = lrck_l
        self.bclk_div = bclk_div
        self.adc_osr = adc_osr
        self.dac_osr = dac_osr


# --- 采样率系数查找表（MCLK × 采样率 → 时钟分频配置）---

coeff_div = (
    # 8k
    _CoeffDiv(12288000, 8000, 0x06, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(18432000, 8000, 0x03, 0x01, 0x03, 0x03, 0x00, 0x05, 0xFF, 0x18, 0x10, 0x10),
    _CoeffDiv(16384000, 8000, 0x08, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(8192000, 8000, 0x04, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 8000, 0x03, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(4096000, 8000, 0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 8000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(2048000, 8000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 8000, 0x03, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1024000, 8000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 11.025k
    _CoeffDiv(11289600, 11025, 0x04, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(5644800, 11025, 0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(2822400, 11025, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1411200, 11025, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 12k
    _CoeffDiv(12288000, 12000, 0x04, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 12000, 0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 12000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 12000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 16k
    _CoeffDiv(12288000, 16000, 0x03, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(18432000, 16000, 0x03, 0x01, 0x03, 0x03, 0x00, 0x02, 0xFF, 0x0C, 0x10, 0x10),
    _CoeffDiv(16384000, 16000, 0x04, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(8192000, 16000, 0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 16000, 0x03, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(4096000, 16000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 16000, 0x03, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(2048000, 16000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 16000, 0x03, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1024000, 16000, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 22.05k
    _CoeffDiv(11289600, 22050, 0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(5644800, 22050, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(2822400, 22050, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1411200, 22050, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(705600, 22050, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 24k
    _CoeffDiv(12288000, 24000, 0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(18432000, 24000, 0x03, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 24000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 24000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 24000, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 32k
    _CoeffDiv(12288000, 32000, 0x03, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(18432000, 32000, 0x03, 0x02, 0x03, 0x03, 0x00, 0x02, 0xFF, 0x0C, 0x10, 0x10),
    _CoeffDiv(16384000, 32000, 0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(8192000, 32000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 32000, 0x03, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(4096000, 32000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 32000, 0x03, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(2048000, 32000, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 32000, 0x03, 0x03, 0x01, 0x01, 0x01, 0x00, 0x7F, 0x02, 0x10, 0x10),
    _CoeffDiv(1024000, 32000, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 44.1k
    _CoeffDiv(11289600, 44100, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(5644800, 44100, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(2822400, 44100, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1411200, 44100, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 48k
    _CoeffDiv(12288000, 48000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(18432000, 48000, 0x03, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 48000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 48000, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 48000, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    # 64k
    _CoeffDiv(12288000, 64000, 0x03, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(18432000, 64000, 0x03, 0x02, 0x03, 0x03, 0x01, 0x01, 0x7F, 0x06, 0x10, 0x10),
    _CoeffDiv(16384000, 64000, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(8192000, 64000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 64000, 0x01, 0x02, 0x03, 0x03, 0x01, 0x01, 0x7F, 0x06, 0x10, 0x10),
    _CoeffDiv(4096000, 64000, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 64000, 0x01, 0x03, 0x03, 0x03, 0x01, 0x01, 0x7F, 0x06, 0x10, 0x10),
    _CoeffDiv(2048000, 64000, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 64000, 0x01, 0x03, 0x01, 0x01, 0x01, 0x00, 0xBF, 0x03, 0x18, 0x18),
    _CoeffDiv(1024000, 64000, 0x01, 0x03, 0x01, 0x01, 0x01, 0x00, 0x7F, 0x02, 0x10, 0x10),
    # 88.2k
    _CoeffDiv(11289600, 88200, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(5644800, 88200, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(2822400, 88200, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1411200, 88200, 0x01, 0x03, 0x01, 0x01, 0x01, 0x00, 0x7F, 0x02, 0x10, 0x10),
    # 96k
    _CoeffDiv(12288000, 96000, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(18432000, 96000, 0x03, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(6144000, 96000, 0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(3072000, 96000, 0x01, 0x03, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    _CoeffDiv(1536000, 96000, 0x01, 0x03, 0x01, 0x01, 0x01, 0x00, 0x7F, 0x02, 0x10, 0x10),
)

# ======================================== 功能函数 ============================================


def BIT(nr):
    """
    生成指定位的位掩码
    Args:
        nr (int): 位索引（0 起始）
    Returns:
        int: 位掩码值 (1 << nr)
    ==========================================
    Generate a bitmask for the given bit index.
    Args:
        nr (int): Bit index (0-based)
    Returns:
        int: Bitmask value (1 << nr)
    """
    return 1 << nr


def get_coeff(mclk: int, rate: int):
    """
    根据 MCLK 频率和采样率查找时钟系数索引
    Args:
        mclk (int): 主时钟频率（Hz）
        rate (int): 目标采样率（Hz）
    Returns:
        int: coeff_div 表中的索引，未找到返回 -1
    ==========================================
    Look up clock coefficient index by MCLK frequency and sample rate.
    Args:
        mclk (int): Master clock frequency in Hz
        rate (int): Target sample rate in Hz
    Returns:
        int: Index in coeff_div table, -1 if not found
    """
    for i in range(len(coeff_div)):
        if coeff_div[i].rate == rate and coeff_div[i].mclk == mclk:
            return i
    return -1


# ======================================== 自定义类 ============================================


class ES8311ClockConfig:
    """
    ES8311 时钟配置容器
    Attributes:
        mclk_inverted (bool): MCLK 是否反相
        sclk_inverted (bool): SCLK 是否反相
        mclk_from_mclk_pin (bool): MCLK 是否来自 MCLK 引脚（否则来自 BCLK）
        mclk_frequency (int): MCLK 频率（Hz）
        sample_frequency (int): 目标采样率（Hz）
    ==========================================
    ES8311 clock configuration container.
    Attributes:
        mclk_inverted (bool): Whether MCLK is inverted
        sclk_inverted (bool): Whether SCLK is inverted
        mclk_from_mclk_pin (bool): Whether MCLK comes from MCLK pin (else from BCLK)
        mclk_frequency (int): MCLK frequency in Hz
        sample_frequency (int): Target sample rate in Hz
    """

    mclk_inverted: bool
    sclk_inverted: bool
    mclk_from_mclk_pin: int
    mclk_frequency: int
    sample_frequency: int

    def __init__(self, mclk_inverted=False, sclk_inverted=False, mclk_from_mclk_pin=True, mclk_frequency=0, sample_frequency=48000):
        self.mclk_inverted = mclk_inverted
        self.sclk_inverted = sclk_inverted
        self.mclk_from_mclk_pin = mclk_from_mclk_pin
        self.mclk_frequency = mclk_frequency
        self.sample_frequency = sample_frequency


class ES8311:
    """
    ES8311 音频编解码器 I2C 配置驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例（外部注入）
        _addr (int): 设备 I2C 地址
        _dac_volume (int): 当前 DAC 音量值
        _debug (bool): 调试日志开关
    Methods:
        init(): 初始化编解码器寄存器
        clock_config(): 配置时钟参数
        fmt_config(): 配置音频数据格式
        sample_frequency_config(): 配置采样频率
        voice_volume_set(): 设置 DAC 音量
        voice_volume_get(): 获取当前 DAC 音量
        microphone_config(): 配置麦克风模式
        resolution_config(): 配置音频分辨率
        deinit(): 释放资源
    Notes:
        - 本驱动仅负责 I2C 寄存器配置，不处理 I2S 音频数据流
        - I2S 数据传输由应用层 machine.I2S 完成
        - I2C 实例由外部注入，不在类内创建
        - 参考源码：m5stack/uiflow-micropython
    ==========================================
    ES8311 audio codec I2C configuration driver.
    Attributes:
        _i2c (I2C): I2C bus instance (externally injected)
        _addr (int): Device I2C address
        _dac_volume (int): Current DAC volume value
        _debug (bool): Debug log switch
    Methods:
        init(): Initialize codec registers
        clock_config(): Configure clock parameters
        fmt_config(): Configure audio data format
        sample_frequency_config(): Configure sample frequency
        voice_volume_set(): Set DAC volume
        voice_volume_get(): Get current DAC volume
        microphone_config(): Configure microphone mode
        resolution_config(): Configure audio resolution
        deinit(): Release resources
    Notes:
        - This driver only handles I2C register configuration, not I2S audio data
        - I2S data transfer is handled by machine.I2S at application layer
        - I2C instance is externally injected, not created inside the class
        - Reference source: m5stack/uiflow-micropython
    """

    # 默认 I2C 地址
    I2C_DEFAULT_ADDR = const(0x18)

    # 音频分辨率常量
    ES8311_RESOLUTION_16 = const(16)
    ES8311_RESOLUTION_18 = const(18)
    ES8311_RESOLUTION_20 = const(20)
    ES8311_RESOLUTION_24 = const(24)
    ES8311_RESOLUTION_32 = const(32)

    # 分辨率到寄存器值的映射表
    RES_MAP = {
        ES8311_RESOLUTION_16: (3 << 2),
        ES8311_RESOLUTION_18: (2 << 2),
        ES8311_RESOLUTION_20: (1 << 2),
        ES8311_RESOLUTION_24: (0 << 2),
        ES8311_RESOLUTION_32: (4 << 2),
    }

    __slots__ = ("_i2c", "_addr", "_dac_volume", "_debug")

    def __init__(self, i2c, address: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 ES8311 驱动实例
        Args:
            i2c (I2C): I2C 总线实例（必须具有 readfrom_mem 和 writeto_mem 方法）
            address (int): 设备 I2C 地址，默认 0x18
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型或值无效
        Notes:
            - 构造函数不执行任何 I2C 通信
            - 调用 init() 方法进行硬件初始化
        ==========================================
        Initialize ES8311 driver instance.
        Args:
            i2c (I2C): I2C bus instance (must have readfrom_mem and writeto_mem methods)
            address (int): Device I2C address, default 0x18
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type or value
        Notes:
            - Constructor does not perform any I2C communication
            - Call init() method for hardware initialization
        """
        # 参数校验：I2C 实例鸭子类型检查
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：地址类型和范围检查
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0x00 or address > 0x7F:
            raise ValueError("address must be 0x00~0x7F, got 0x%02X" % address)
        # 参数校验：debug 类型检查
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))
        self._i2c = i2c
        self._addr = address
        self._dac_volume = 0
        self._debug = debug

    # ========== 私有方法 ==========

    def _log(self, msg: str) -> None:
        """
        输出调试日志（仅在 debug 模式下）
        Args:
            msg (str): 日志消息
        ==========================================
        Output debug log (only in debug mode).
        Args:
            msg (str): Log message
        """
        if self._debug:
            print("[ES8311] %s" % msg)

    def _read_reg(self, reg: int) -> int:
        """
        通过 I2C 读取单个寄存器值
        Args:
            reg (int): 寄存器地址
        Returns:
            int: 寄存器值（0-255）
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Read a single register value via I2C.
        Args:
            reg (int): Register address
        Returns:
            int: Register value (0-255)
        Raises:
            RuntimeError: I2C communication failed
        """
        try:
            return self._i2c.readfrom_mem(self._addr, reg, 1)[0]
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X: %s" % (reg, e))

    def _write_reg(self, reg: int, value: int) -> None:
        """
        通过 I2C 写入单个寄存器值
        Args:
            reg (int): 寄存器地址
            value (int): 要写入的值（0-255）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改硬件寄存器状态
        ==========================================
        Write a single register value via I2C.
        Args:
            reg (int): Register address
            value (int): Value to write (0-255)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: modifies hardware register state
        """
        try:
            self._i2c.writeto_mem(self._addr, reg, bytes([value & 0xFF]))
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X: %s" % (reg, e))

    # ========== 公共方法 ==========

    def init(self, clk_cfg, res_in: int, res_out: int) -> None:
        """
        初始化 ES8311 编解码器（复位 + 时钟配置 + 格式配置 + 系统寄存器）
        Args:
            clk_cfg (ES8311ClockConfig): 时钟配置实例
            res_in (int): ADC 输入分辨率（使用 ES8311_RESOLUTION_* 常量）
            res_out (int): DAC 输出分辨率（使用 ES8311_RESOLUTION_* 常量）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：复位并配置所有编解码器寄存器
            - 包含 20ms 复位延时
        ==========================================
        Initialize ES8311 codec (reset + clock config + format config + system regs).
        Args:
            clk_cfg (ES8311ClockConfig): Clock configuration instance
            res_in (int): ADC input resolution (use ES8311_RESOLUTION_* constants)
            res_out (int): DAC output resolution (use ES8311_RESOLUTION_* constants)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: resets and configures all codec registers
            - Includes 20ms reset delay
        """
        # 软件复位序列
        self._write_reg(ES8311_RESET_REG00, 0x1F)
        time.sleep(0.02)
        self._write_reg(ES8311_RESET_REG00, 0x00)
        self._write_reg(ES8311_RESET_REG00, 0x80)

        # 配置时钟方案
        self.clock_config(clk_cfg, res_out)

        # 配置音频数据格式
        self.fmt_config(res_in, res_out)

        # 系统寄存器初始化序列（来自 M5Stack 参考代码）
        self._write_reg(ES8311_SYSTEM_REG0D, 0x01)
        self._write_reg(ES8311_SYSTEM_REG0E, 0x02)
        self._write_reg(ES8311_SYSTEM_REG12, 0x00)
        self._write_reg(ES8311_SYSTEM_REG13, 0x10)
        self._write_reg(ES8311_ADC_REG1C, 0x6A)
        self._write_reg(ES8311_DAC_REG37, 0x08)

    def clock_config(self, clk_cfg: ES8311ClockConfig, res: int) -> None:
        """
        配置 ES8311 时钟方案（MCLK、SCLK、采样率）
        Args:
            clk_cfg (ES8311ClockConfig): 时钟配置实例
            res (int): 音频分辨率（用于计算 BCLK 频率）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改时钟管理器寄存器 REG01~REG08
        ==========================================
        Configure ES8311 clock scheme (MCLK, SCLK, sample rate).
        Args:
            clk_cfg (ES8311ClockConfig): Clock configuration instance
            res (int): Audio resolution (used to calculate BCLK frequency)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: modifies clock manager registers REG01~REG08
        """
        reg01 = 0x3F
        # 确定 MCLK 来源和频率
        if clk_cfg.mclk_from_mclk_pin:
            mclk_hz = clk_cfg.mclk_frequency
        else:
            mclk_hz = clk_cfg.sample_frequency * res * 2
            reg01 |= BIT(7)  # 选择 BCLK（即 SCK）引脚作为时钟源

        # MCLK 反相配置
        if clk_cfg.mclk_inverted:
            reg01 |= BIT(6)  # 反相 MCLK 引脚

        # 写入时钟管理器 REG01
        self._write_reg(ES8311_CLK_MANAGER_REG01, reg01)

        # SCLK 反相配置（读取-修改-写入 REG06 的 bit5）
        reg06 = self._read_reg(ES8311_CLK_MANAGER_REG06)
        if clk_cfg.sclk_inverted:
            reg06 |= BIT(5)
        else:
            reg06 &= ~BIT(5)
        self._write_reg(ES8311_CLK_MANAGER_REG06, reg06)

        # 根据 MCLK 和采样率设置分频系数
        self.sample_frequency_config(mclk_hz, clk_cfg.sample_frequency)

    def fmt_config(self, res_in: int, res_out: int) -> None:
        """
        配置音频数据格式（分辨率、串行数字端口）
        Args:
            res_in (int): ADC 输入分辨率
            res_out (int): DAC 输出分辨率
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改 SDP 输入/输出寄存器和 RESET 寄存器
        ==========================================
        Configure audio data format (resolution, serial digital port).
        Args:
            res_in (int): ADC input resolution
            res_out (int): DAC output resolution
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: modifies SDP in/out registers and RESET register
        """
        # 清除 RESET_REG00 的 bit6
        reg00 = self._read_reg(ES8311_RESET_REG00)
        reg00 &= 0xBF
        self._write_reg(ES8311_RESET_REG00, reg00)

        # 配置 DAC 和 ADC 的串行数字端口分辨率
        reg09 = self.resolution_config(res_in, 0)
        reg0a = self.resolution_config(res_out, 0)
        self._write_reg(ES8311_SDPIN_REG09, reg09)
        self._write_reg(ES8311_SDPOUT_REG0A, reg0a)

    def sample_frequency_config(self, mclk_frequency: int, sample_frequency: int) -> None:
        """
        根据 MCLK 频率和目标采样率配置时钟分频寄存器
        Args:
            mclk_frequency (int): MCLK 频率（Hz）
            sample_frequency (int): 目标采样率（Hz）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改 REG02~REG08 时钟分频寄存器
            - 若查找表中无匹配项，输出调试日志并静默返回
        ==========================================
        Configure clock divider registers based on MCLK frequency and target sample rate.
        Args:
            mclk_frequency (int): MCLK frequency in Hz
            sample_frequency (int): Target sample rate in Hz
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: modifies REG02~REG08 clock divider registers
            - If no match found in lookup table, logs debug message and returns silently
        """
        # 从系数表中查找匹配的时钟系数
        coeff = get_coeff(mclk_frequency, sample_frequency)
        if coeff < 0:
            self._log("Unable to configure sample rate %dHz with %dHz MCLK" % (sample_frequency, mclk_frequency))
            return

        selected_coeff = coeff_div[coeff]

        # 寄存器 0x02：时钟分频器和倍频器
        regv = self._read_reg(ES8311_CLK_MANAGER_REG02)
        regv &= 0x07
        regv |= (selected_coeff.pre_div - 1) << 5
        regv |= selected_coeff.pre_multi << 3
        self._write_reg(ES8311_CLK_MANAGER_REG02, regv)

        # 寄存器 0x03：ADC fs 模式和 OSR
        reg03 = (selected_coeff.fs_mode << 6) | selected_coeff.adc_osr
        self._write_reg(ES8311_CLK_MANAGER_REG03, reg03)

        # 寄存器 0x04：DAC OSR
        self._write_reg(ES8311_CLK_MANAGER_REG04, selected_coeff.dac_osr)

        # 寄存器 0x05：ADC 和 DAC 时钟分频器
        reg05 = ((selected_coeff.adc_div - 1) << 4) | (selected_coeff.dac_div - 1)
        self._write_reg(ES8311_CLK_MANAGER_REG05, reg05)

        # 寄存器 0x06：BCLK 反相器和分频器
        regv = self._read_reg(ES8311_CLK_MANAGER_REG06)
        regv &= 0xE0
        # BCLK 分频值处理（小于 19 时减 1 偏移）
        if selected_coeff.bclk_div < 19:
            regv |= (selected_coeff.bclk_div - 1) << 0
        else:
            regv |= (selected_coeff.bclk_div) << 0
        self._write_reg(ES8311_CLK_MANAGER_REG06, regv)

        # 寄存器 0x07：LRCK 分频器（高字节）
        regv = self._read_reg(ES8311_CLK_MANAGER_REG07)
        regv &= 0xC0
        regv |= selected_coeff.lrck_h << 0
        self._write_reg(ES8311_CLK_MANAGER_REG07, regv)

        # 寄存器 0x08：LRCK 分频器（低字节）
        self._write_reg(ES8311_CLK_MANAGER_REG08, selected_coeff.lrck_l)

    def voice_volume_set(self, volume: int) -> None:
        """
        设置 DAC 音量
        Args:
            volume (int): 音量值（0-100，0 为静音，100 为最大）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改 DAC 音量寄存器 REG32
            - 输入值自动钳位到 0-100 范围
        ==========================================
        Set DAC volume.
        Args:
            volume (int): Volume value (0-100, 0 is mute, 100 is maximum)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: modifies DAC volume register REG32
            - Input value is automatically clamped to 0-100 range
        """
        # 音量值范围钳位
        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 100
        self._dac_volume = volume

        # 计算寄存器值（0-100 映射到 0-255 的 DAC 音量寄存器空间）
        if volume == 0:
            reg32 = 0
        else:
            reg32 = int((volume) * 256 / 100) - 1

        self._write_reg(ES8311_DAC_REG32, reg32)

    def voice_volume_get(self) -> int:
        """
        获取当前 DAC 音量值
        Returns:
            int: 当前音量（0-100）
        Notes:
            - 返回的是缓存值，不执行 I2C 读取
        ==========================================
        Get current DAC volume value.
        Returns:
            int: Current volume (0-100)
        Notes:
            - Returns cached value, does not perform I2C read
        """
        return self._dac_volume

    def microphone_config(self, digital_mic: bool) -> None:
        """
        配置麦克风模式（模拟或数字）
        Args:
            digital_mic (bool): True 为数字 PDM 麦克风，False 为模拟麦克风
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改 ADC 增益寄存器 REG17 和系统寄存器 REG14
        ==========================================
        Configure microphone mode (analog or digital).
        Args:
            digital_mic (bool): True for digital PDM microphone, False for analog
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: modifies ADC gain register REG17 and system register REG14
        """
        # 默认启用模拟麦克风和最大 PGA 增益
        reg14 = 0x1A

        # PDM 数字麦克风使能/禁用
        if digital_mic:
            reg14 |= BIT(6)

        # 设置 ADC 增益为最大值
        self._write_reg(ES8311_ADC_REG17, 0xFF)

        # 写入系统寄存器 REG14
        self._write_reg(ES8311_SYSTEM_REG14, reg14)

    def resolution_config(self, res: int, reg: int) -> int:
        """
        根据分辨率配置寄存器值
        Args:
            res (int): 音频分辨率（使用 ES8311_RESOLUTION_* 常量）
            reg (int): 当前寄存器值
        Returns:
            int: 合并分辨率位后的寄存器值
        Raises:
            ValueError: 不支持的分辨率值
        Notes:
            - 该方法是 fmt_config 的内部辅助方法
        ==========================================
        Configure register value based on resolution.
        Args:
            res (int): Audio resolution (use ES8311_RESOLUTION_* constants)
            reg (int): Current register value
        Returns:
            int: Register value with resolution bits merged
        Raises:
            ValueError: Unsupported resolution value
        Notes:
            - This method is an internal helper for fmt_config
        """
        res_bits = self.RES_MAP.get(res)
        if res_bits is None:
            raise ValueError("Unsupported resolution: %s" % res)
        return reg | res_bits

    def deinit(self) -> None:
        """
        释放驱动资源
        Notes:
            - 重置内部状态为默认值
            - 不释放外部注入的 I2C 实例
        ==========================================
        Release driver resources.
        Notes:
            - Resets internal state to defaults
            - Does not release externally injected I2C instance
        """
        self._dac_volume = 0


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
