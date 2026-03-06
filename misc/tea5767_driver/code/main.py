# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9
# @Author  : alankrantas
# @File    : tea5767_search_max_signal_simple.py
# @Description : 基于原有Radio类搜索最高信号频率（无新增类）

import time
from machine import I2C, Pin
from tea5767 import Radio  # 导入原有Radio类

# ======================== 硬件配置（根据实际接线修改）========================
I2C_SCL = 5  # Pico I2C SCL引脚
I2C_SDA = 4  # Pico I2C SDA引脚
RADIO_ADDR = 0x60  # Tea5767默认I2C地址
SEARCH_BAND = "US"  # 搜索频段：US(87.5-108.0) / JP(76.0-91.0)
STEP = 0.1  # FM频率步进（固定0.1MHz）

# ======================== 核心搜索逻辑 ========================

# 1. 初始化I2C和Radio实例
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)
if RADIO_ADDR not in i2c.scan():
    print(f"Error: Tea5767 module not detected (I2C address {hex(RADIO_ADDR)})")
else:
    # 初始化Radio（关闭干扰检测的功能，保证信号读取准确）
    radio = Radio(
        i2c=i2c,
        addr=RADIO_ADDR,
        freq=87.5 if SEARCH_BAND == "US" else 76.0,
        band=SEARCH_BAND,
        soft_mute=False,
        noise_cancel=False,
        high_cut=False
    )
    print(f"Starting {SEARCH_BAND} band scanning...")

    # 2. 定义频段范围
    freq_min, freq_max = (Radio.FREQ_RANGE_US if SEARCH_BAND == "US" else Radio.FREQ_RANGE_JP)
    current_freq = freq_min
    max_signal_freq = current_freq
    max_signal_level = 0

    # 3. 逐频率扫描信号强度
    while current_freq <= freq_max:
        # 设置当前频率并等待稳定
        radio.set_frequency(current_freq)
        time.sleep_ms(20)
        radio.read()  # 读取最新状态

        # 更新最高信号记录
        if radio.signal_adc_level > max_signal_level:
            max_signal_level = radio.signal_adc_level
            max_signal_freq = current_freq

        # 频率步进（保留1位小数避免浮点误差）
        current_freq = round(current_freq + STEP, 1)

    # 4. 切换到最高信号频率并输出结果
    radio.set_frequency(max_signal_freq)
    time.sleep_ms(50)
    radio.read()

    # 恢复优化配置（软静音/降噪）
    radio.soft_mute_mode = True
    radio.stereo_noise_cancelling_mode = True
    radio.update()

    # 打印最终结果
    print("=" * 40)
    print(f"Scanning completed!")
    print(f"Max signal frequency: {max_signal_freq} MHz")
    print(f"Signal strength level: {max_signal_level} (0-15, higher is stronger)")
    print(f"Stereo mode: {'Yes' if radio.is_stereo else 'No'}")
    print("=" * 40)