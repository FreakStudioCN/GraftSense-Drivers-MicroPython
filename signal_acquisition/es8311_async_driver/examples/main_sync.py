# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 ES8311 音频编解码器 I2C 配置驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


from machine import I2C, I2S, Pin
import time
from es8311 import ES8311, ES8311ClockConfig

# ======================================== 全局变量 ============================================

# --- 硬件引脚配置常量（请根据实际接线修改）---
SCL_PIN = const(22)
SDA_PIN = const(21)
I2C_FREQ = const(400000)  # I2C 时钟频率（Hz）

# I2S 音频总线引脚
I2S_BCK_PIN = const(5)  # I2S 位时钟
I2S_WS_PIN = const(25)  # I2S 字选择（LRCK）
I2S_DOUT_PIN = const(26)  # I2S 数据输出（DAC 播放）
I2S_DIN_PIN = const(35)  # I2S 数据输入（ADC 录音）

# ES8311 设备地址
ES8311_I2C_ADDR = const(0x18)

# ES8311 芯片 ID 寄存器及期望值
ES8311_CHIP_ID_REG = const(0xFD)
ES8311_CHIP_ID_EXPECTED = const(0x83)

# 采样率配置
SAMPLE_RATE = const(48000)

# 打印间隔（ms）
PRINT_INTERVAL = const(3000)

last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================


def init_i2c_bus():
    """初始化 I2C 总线并扫描设备"""
    print("Initializing I2C bus...")
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
    # 扫描 I2C 总线
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    print("I2C devices found: %s" % [hex(d) for d in devices])
    # 验证目标设备地址存在
    found = False
    for dev in devices:
        if dev == ES8311_I2C_ADDR:
            found = True
            break
    if not found:
        raise RuntimeError("Device not found at expected address 0x%02X" % ES8311_I2C_ADDR)
    print("ES8311 device found at 0x%02X" % ES8311_I2C_ADDR)
    return i2c


def verify_chip_id(i2c):
    """验证 ES8311 芯片 ID"""
    try:
        chip_id = i2c.readfrom_mem(ES8311_I2C_ADDR, ES8311_CHIP_ID_REG, 1)[0]
    except OSError as e:
        raise RuntimeError("Failed to read chip ID register: %s" % e)
    if chip_id == ES8311_CHIP_ID_EXPECTED:
        print("Chip ID verified: 0x%02X (expected 0x%02X)" % (chip_id, ES8311_CHIP_ID_EXPECTED))
    else:
        print("Chip ID mismatch: read 0x%02X, expected 0x%02X" % (chip_id, ES8311_CHIP_ID_EXPECTED))


def init_es8311_codec(i2c):
    """
    初始化 ES8311 编解码器
    Returns:
        ES8311: 编解码器驱动实例
    """
    print("Initializing ES8311 codec...")
    # 创建编解码器驱动实例（启用调试日志）
    codec = ES8311(i2c, address=ES8311_I2C_ADDR, debug=False)

    # 构建时钟配置
    clk_cfg = ES8311ClockConfig(
        mclk_inverted=False,
        sclk_inverted=False,
        mclk_from_mclk_pin=False,  # MCLK 来自 BCLK 引脚
        mclk_frequency=0,  # BCLK 模式下此值由驱动自动计算
        sample_frequency=SAMPLE_RATE,
    )

    # 执行编解码器初始化
    codec.init(clk_cfg, ES8311.ES8311_RESOLUTION_16, ES8311.ES8311_RESOLUTION_16)
    print("ES8311 codec initialized successfully")
    return codec


def create_dac_i2s():
    """
    创建 DAC 播放 I2S 对象
    注意：I2S 对象在 main.py 中创建，不在驱动类内部创建
    Returns:
        I2S: DAC 输出 I2S 实例
    """
    audio_out = I2S(
        0,  # I2S 外设 ID
        sck=Pin(I2S_BCK_PIN),  # 位时钟
        ws=Pin(I2S_WS_PIN),  # 字选择 / LRCK
        sd=Pin(I2S_DOUT_PIN),  # 串行数据输出
        mode=I2S.TX,  # 发送模式（DAC 播放）
        bits=16,  # 16 位采样
        format=I2S.STEREO,  # 立体声
        rate=SAMPLE_RATE,  # 采样率
        ibuf=8192,  # 内部缓冲区大小
    )
    print("DAC I2S output created: %dHz, 16-bit stereo" % SAMPLE_RATE)
    return audio_out


def create_adc_i2s():
    """
    创建 ADC 录音 I2S 对象
    注意：I2S 对象在 main.py 中创建，不在驱动类内部创建
    Returns:
        I2S: ADC 输入 I2S 实例
    """
    audio_in = I2S(
        0,  # I2S 外设 ID（部分平台可能需要不同 ID）
        sck=Pin(I2S_BCK_PIN),  # 位时钟
        ws=Pin(I2S_WS_PIN),  # 字选择 / LRCK
        sd=Pin(I2S_DIN_PIN),  # 串行数据输入
        mode=I2S.RX,  # 接收模式（ADC 录音）
        bits=16,  # 16 位采样
        format=I2S.STEREO,  # 立体声
        rate=SAMPLE_RATE,  # 采样率
        ibuf=8192,  # 内部缓冲区大小
    )
    print("ADC I2S input created: %dHz, 16-bit stereo" % SAMPLE_RATE)
    return audio_in


def configure_microphone(codec, digital_mic=False):
    """配置麦克风模式（REPL 可手动调用）"""
    mode_name = "digital PDM" if digital_mic else "analog"
    print("Configuring microphone: %s mode" % mode_name)
    codec.microphone_config(digital_mic)
    print("Microphone configured: %s" % mode_name)


def print_status(codec):
    """
    打印编解码器状态信息（低频调用）
    """
    volume = codec.voice_volume_get()
    print("[Status] DAC volume: %d/100" % volume)


# ======================================== 初始化配置 ==========================================

# 启动延时，等待硬件就绪
time.sleep(3)

print("FreakStudio: ES8311 audio codec configuration driver test")
print("I2C config driver only - I2S data handling is at application layer")

try:
    # 初始化 I2C 总线并验证设备
    i2c = init_i2c_bus()
    verify_chip_id(i2c)

    # 初始化编解码器
    codec = init_es8311_codec(i2c)

    # 设置音量
    codec.voice_volume_set(80)
    print("Volume set to 80")

    # 配置模拟麦克风
    configure_microphone(codec, digital_mic=False)

except OSError as e:
    print("Hardware communication error: %s" % str(e))
    raise

# ========================================  主程序  ===========================================

# --- 以下为 I2S 使用示例（取消注释以启用） ---
# 注意：I2S 初始化需要相应的 I2S 引脚，请在硬件就绪后取消注释
#
# # 创建 I2S 对象（DAC 播放和 ADC 录音各一个）
# audio_out = create_dac_i2s()
# audio_in = create_adc_i2s()
#
# # DAC 播放示例：从文件或缓冲区读取数据写入 I2S
# # with open("audio_sample.raw", "rb") as f:
# #     while True:
# #         data = f.read(1024)
# #         if not data:
# #             break
# #         audio_out.write(data)
#
# # ADC 录音示例：从 I2S 读取数据写入文件
# # with open("recording.raw", "wb") as f:
# #     while True:
# #         data = audio_in.read(1024)
# #         f.write(data)
#
# 取消注释至此

try:
    while True:
        current_time = time.ticks_ms()
        # 低频打印编解码器状态
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            print_status(codec)
            last_print_time = current_time

        # 以下为可选功能函数，默认注释调用，可 REPL 手动触发
        # configure_microphone(codec, digital_mic=True)   # 切换到数字麦克风
        # codec.voice_volume_set(50)                       # 调整音量到 50

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    try:
        codec.deinit()
        print("Codec deinitialized")
    except Exception:
        pass
    del codec
    print("Program exited")
