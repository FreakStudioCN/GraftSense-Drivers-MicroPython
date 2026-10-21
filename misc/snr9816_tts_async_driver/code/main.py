try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

"""Original blocking demonstration retained as a non-runtime reference.

async def main():
    # Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
    # -*- coding: utf-8 -*-
    # @Time    : 2026/1/5 10:57
    # @Author  : hogeiha
    # @File    : main.py
    # @Description : SNR9816 TTS 示例程序

    # ======================================== 导入相关模块 =========================================

    from snr9816_tts import SNR9816_TTS
    from machine import Pin, UART

    # ======================================== 全局变量 ============================================

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 上电延时3s
    await asyncio.sleep(3)
    # 打印调试消息
    print("FreakStudio: SNR9816 TTS Driver Example")

    # 创建 UART 对象，使用 UART0，波特率 115200，数据位 8，无奇偶校验，停止位 1，TX 引脚 GPIO16，RX 引脚 GPIO17
    uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))
    # 创建 TTS 对象（使用 UTF-8 编码）
    tts = SNR9816_TTS(uart)

    # ========================================  主程序  ===========================================

    # 查看TTS 状态
    tts.query_status()

    # 设置参数
    # 设置声音编号 0=女声，1=男声
    while not tts.set_voice(1):
        continue
    print("Voice set to male.")

    # 设置音量 0~9
    while not tts.set_volume(9):
        await asyncio.sleep(1)
        continue
    print("Volume set to 9.")

    # 设置语速 0~9
    while not tts.set_speed(9):
        await asyncio.sleep(1)
        continue
    print("Speed set to 9.")

    # 设置音调 0~9
    while not tts.set_tone(9):
        await asyncio.sleep(1)
        continue
    print("Tone set to 9.")

    # 播放铃声
    for i in range(5):
        while not tts.play_ringtone(i + 1):
            await asyncio.sleep(1)
            continue
        print(f"Playing ringtone {i+1}/5...")
    print("Ringtone playback finished.")

    # 播放提示音
    for i in range(5):
        while not tts.play_message_tone(i + 1):
            await asyncio.sleep(1)
            continue
        print(f"Playing message tone {i+1}/5...")
    print("Message tone playback finished.")

    # 播放警报音
    for i in range(5):
        while not tts.play_alert_tone(i + 1):
            await asyncio.sleep(1)
            continue
        print(f"Playing prompt tone {i+1}/5...")
    print("Alert tone playback finished.")

    # 合成文本
    while not tts.synthesize_text(
        "欢迎使用我司的TTS语音合[w0]成测试模块。请注意以下发音细节:这个要[=yao1]求很重[=zhong4]要[=yao4]。（避免“要[yao]求”和“重[chong]要”的错误发音）本次会议共有[n1]25人参加。"
    ):
        await asyncio.sleep(1)
        continue
    print("Text synthesis started.")

    # 终端输入任意键暂停播放
    input("Press any key to pause")
    # 暂停合成
    tts.pause_synthesis()
    print("Synthesis paused.")

    # 终端输入任意键继续合成播放
    input("Press any key to play")
    # 继续合成
    tts.resume_synthesis()
    print("Synthesis resumed.")

    # 终端输入任意键停止取消合成播放
    input("Press any key to stop")
    # 停止合成
    tts.stop_synthesis()
    print("Synthesis stopped.")

"""

from machine import Pin, UART
from snr9816_tts_async import SNR9816_TTSAsync


async def _retry(operation, attempts=3):
    for _ in range(attempts):
        if await operation():
            return True
        await asyncio.sleep_ms(20)
    return False


async def main():
    uart = None
    tts = None
    try:
        uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))
        tts = SNR9816_TTSAsync(uart)
        await asyncio.sleep(3)
        await tts.query_status_async()
        if not await _retry(lambda: tts.set_voice_async(1)):
            raise RuntimeError("SNR9816 did not accept the voice command")
        for command in (tts.set_volume_async(9), tts.set_speed_async(9), tts.set_tone_async(9)):
            if not await command:
                raise RuntimeError("SNR9816 did not accept a level command")
        for command in (tts.play_ringtone_async(1), tts.play_message_tone_async(1), tts.play_alert_tone_async(1)):
            if not await command:
                raise RuntimeError("SNR9816 did not accept a tone command")
        if not await tts.synthesize_text_async("SNR9816 async driver example."):
            raise RuntimeError("SNR9816 did not accept the synthesis command")
        await tts.pause_synthesis_async()
        await tts.resume_synthesis_async()
        await tts.stop_synthesis_async()
    finally:
        if tts is not None:
            await tts.aclose()


if __name__ == '__main__':
    asyncio.run(main())
