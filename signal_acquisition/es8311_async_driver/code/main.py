try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
try:
    from micropython import const
except ImportError:
    def const(value):
        return value
import time
from machine import I2C, I2S, Pin
from es8311 import ES8311
from es8311_async import ES8311Async, ES8311ClockConfigAsync

SCL_PIN = const(22)
SDA_PIN = const(21)
I2C_FREQ = const(400000)
ES8311_I2C_ADDR = const(0x18)
ES8311_CHIP_ID_REG = const(0xFD)
ES8311_CHIP_ID_EXPECTED = const(0x83)
SAMPLE_RATE = const(48000)
I2S_BCK_PIN = const(5)
I2S_WS_PIN = const(25)
I2S_DOUT_PIN = const(26)
I2S_DIN_PIN = const(35)
PRINT_INTERVAL = const(3000)


async def init_i2c_bus():
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
    if ES8311_I2C_ADDR not in i2c.scan():
        raise RuntimeError("Device not found at expected address 0x%02X" % ES8311_I2C_ADDR)
    return i2c


async def verify_chip_id(i2c):
    chip_id = i2c.readfrom_mem(ES8311_I2C_ADDR, ES8311_CHIP_ID_REG, 1)[0]
    if chip_id != ES8311_CHIP_ID_EXPECTED:
        print("Chip ID mismatch: read 0x%02X, expected 0x%02X" % (chip_id, ES8311_CHIP_ID_EXPECTED))


async def init_es8311_codec(i2c):
    codec = ES8311Async(i2c, address=ES8311_I2C_ADDR, debug=False)
    clock = ES8311ClockConfigAsync(False, False, False, 0, SAMPLE_RATE)
    await codec.init_async(clock, ES8311.ES8311_RESOLUTION_16, ES8311.ES8311_RESOLUTION_16)
    return codec


def create_dac_i2s():
    """Create the source-example DAC I2S endpoint; the caller owns deinit()."""
    return I2S(
        0,
        sck=Pin(I2S_BCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_DOUT_PIN),
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=SAMPLE_RATE,
        ibuf=8192,
    )


def create_adc_i2s():
    """Create the source-example ADC I2S endpoint; the caller owns deinit()."""
    return I2S(
        0,
        sck=Pin(I2S_BCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_DIN_PIN),
        mode=I2S.RX,
        bits=16,
        format=I2S.STEREO,
        rate=SAMPLE_RATE,
        ibuf=8192,
    )


async def configure_microphone(codec, digital_mic=False):
    await codec.microphone_config_async(digital_mic)


async def print_status(codec):
    print("[Status] DAC volume: %d/100" % await codec.voice_volume_get_async())

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2026/07/23
    # @Author  : FreakStudio
    # @File    : main.py
    # @Description : 测试 ES8311 音频编解码器 I2C 配置驱动类
    # @License : MIT

    # ======================================== 导入相关模块 =========================================

    # ======================================== 全局变量 ============================================

    last_print_time = time.ticks_ms()
    i2c = None
    codec = None

    # ======================================== 功能函数 ============================================


    # ======================================== 初始化配置 ==========================================

    # 启动延时，等待硬件就绪
    await asyncio.sleep(3)

    print("FreakStudio: ES8311 audio codec configuration driver test")
    print("I2C config driver only - I2S data handling is at application layer")

    try:
        # 初始化 I2C 总线并验证设备
        i2c = await init_i2c_bus()
        await verify_chip_id(i2c)

        # 初始化编解码器
        codec = await init_es8311_codec(i2c)

        # 设置音量
        await codec.voice_volume_set_async(80)
        print("Volume set to 80")

        # 配置模拟麦克风
        await configure_microphone(codec, digital_mic=False)

    except Exception as exc:
        print("Hardware initialization error: %s" % str(exc))
        try:
            if codec is not None:
                await codec.aclose()
        finally:
            if i2c is not None:
                i2c.deinit()
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
                await print_status(codec)
                last_print_time = current_time

            # 以下为可选功能函数，默认注释调用，可 REPL 手动触发
            # configure_microphone(codec, digital_mic=True)   # 切换到数字麦克风
            # codec.voice_volume_set(50)                       # 调整音量到 50

            await asyncio.sleep_ms(100)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        try:
            if codec is not None:
                await codec.aclose()
                print("Codec deinitialized")
        finally:
            if i2c is not None:
                i2c.deinit()
        print("Program exited")

if __name__ == '__main__':
    asyncio.run(main())
