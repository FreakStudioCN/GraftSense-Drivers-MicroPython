# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/20 下午4:52
# @Author  : 作者名
# @File    : main.py
# @Description : KT403A MP3模块功能测试，涵盖音量控制、EQ切换、播放控制、循环模式等核心功能

# ======================================== 导入相关模块 =========================================

# 导入KT403A模块驱动类
from kt403a import KT403A

# 导入UART、Pin、Timer硬件控制模块
from machine import UART, Pin

# 导入毫秒级延迟模块
from utime import sleep_ms

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动延迟3秒，确保硬件初始化完成
sleep_ms(3)
# 打印初始化完成提示
print("FreakStudio: KT403A MP3 module full function test")

# ========================================  主程序  ============================================

# 打印测试标题分隔线
print("-----------------")
# 打印测试标题
print(" Test KT403A MP3 ")
# 打印测试标题分隔线
print("-----------------")

# 初始化UART通信，设置波特率9600，TX引脚16，RX引脚17
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 初始化KT403A MP3模块实例
mp3 = KT403A(uart)

# ==================== 基础信息查询测试 ====================
# 打印基础信息查询测试标题
print("\n【Basic Information Query】")
# 获取当前音量值
current_vol = mp3.GetVolume()
# 打印当前音量
print(f"Current volume: {current_vol}%")

# 定义EQ模式映射字典
eq_mapping = {mp3.EQ_NORMAL: "Normal", mp3.EQ_POP: "Pop", mp3.EQ_ROCK: "Rock", mp3.EQ_JAZZ: "Jazz", mp3.EQ_CLASSIC: "Classic", mp3.EQ_BASS: "Bass"}
# 获取当前EQ模式值
current_eq = mp3.GetEqualizer()
# 打印当前EQ模式
print(f"Current EQ mode: {eq_mapping.get(current_eq, 'Unknown')}")

# 获取SD卡（TF卡）中的音频文件数量
file_count = mp3.GetFilesCount(mp3.DEVICE_SD)
# 打印SD卡文件数量
print(f"Number of audio files in SD card (TF card): {file_count}")

# 判断并打印当前播放状态
if mp3.IsPlaying():
    print("Current status: Playing")
elif mp3.IsPaused():
    print("Current status: Paused")
elif mp3.IsStopped():
    print("Current status: Stopped")

# 延迟1秒，确保模块响应完成
sleep_ms(1000)

# ==================== 音量控制测试 ====================
# 打印音量控制测试标题
print("\n【Volume Control Test】")
# 打印增大音量提示
print("Increase volume (+2 levels)...")
# 增大音量一级
mp3.VolumeUp()
# 延迟500毫秒
sleep_ms(500)
# 再次增大音量一级
mp3.VolumeUp()
# 延迟500毫秒
sleep_ms(500)
# 打印增大后的音量
print(f"Volume after increase: {mp3.GetVolume()}%")

# 打印减小音量提示
print("Decrease volume (-1 level)...")
# 减小音量一级
mp3.VolumeDown()
# 延迟500毫秒
sleep_ms(500)
# 打印减小后的音量
print(f"Volume after decrease: {mp3.GetVolume()}%")

# 打印设置音量提示
print("Set volume to 50%...")
# 设置音量为50%
mp3.SetVolume(50)
# 延迟500毫秒
sleep_ms(500)
# 打印设置后的音量
print(f"Volume after setting: {mp3.GetVolume()}%")

# 延迟1秒
sleep_ms(1000)

# ==================== EQ音效切换测试 ====================
# 打印EQ音效切换测试标题
print("\n【EQ Effect Switch Test】")
# 打印切换为摇滚模式提示
print("Switch to Rock mode...")
# 设置EQ为摇滚模式
mp3.SetEqualizer(mp3.EQ_ROCK)
# 延迟500毫秒
sleep_ms(500)
# 获取当前EQ模式
current_eq = mp3.GetEqualizer()
# 打印当前EQ模式
print(f"Current EQ mode: {eq_mapping.get(current_eq)}")

# 打印切换为重低音模式提示
print("Switch to Bass mode...")
# 设置EQ为重低音模式
mp3.SetEqualizer(mp3.EQ_BASS)
# 延迟500毫秒
sleep_ms(500)
# 获取当前EQ模式
current_eq = mp3.GetEqualizer()
# 打印当前EQ模式
print(f"Current EQ mode: {eq_mapping.get(current_eq)}")

# 打印恢复为普通模式提示
print("Restore to Normal mode...")
# 设置EQ为普通模式
mp3.SetEqualizer(mp3.EQ_NORMAL)
# 延迟500毫秒
sleep_ms(500)
# 获取当前EQ模式
current_eq = mp3.GetEqualizer()
# 打印当前EQ模式
print(f"Current EQ mode: {eq_mapping.get(current_eq)}")

# 延迟1秒
sleep_ms(1000)

# ==================== 播放控制测试（针对4个音频文件） ====================
# 打印播放控制测试标题
print("\n【Playback Control Test (for 4 audio files)】")
# 打印播放第1首曲目提示
print("Play the 1st track...")
# 播放第1首曲目
mp3.PlaySpecific(1)
# 播放3秒
sleep_ms(3000)

# 打印暂停播放提示
print("Pause playback...")
# 暂停播放
mp3.Pause()
# 延迟1秒
sleep_ms(1000)
# 打印暂停后的状态
print(f"Status after pause: {'Paused' if mp3.IsPaused() else 'Not paused'}")

# 打印继续播放提示
print("Resume playback...")
# 继续播放
mp3.Play()
# 继续播放2秒
sleep_ms(2000)

# 打印播放下一曲提示
print("Play next track (2nd track)...")
# 播放下一曲
mp3.PlayNext()
# 播放3秒
sleep_ms(3000)

# 打印播放上一曲提示
print("Play previous track (back to 1st track)...")
# 播放上一曲
mp3.PlayPrevious()
# 播放3秒
sleep_ms(3000)

# 打印播放第4首曲目提示
print("Play the 4th track directly...")
# 播放第4首曲目
mp3.PlaySpecific(4)
# 播放3秒
sleep_ms(3000)

# 延迟1秒
sleep_ms(1000)

# ==================== 循环模式测试 ====================
# 打印循环模式测试标题
print("\n【Loop Mode Test】")
# 打印关闭全部循环提示
print("Disable all tracks loop...")
# 关闭全部曲目循环
mp3.DisableLoopAll()
# 延迟500毫秒
sleep_ms(500)

# 打印开启单曲循环提示
print("Enable single track loop (4th track)...")
# 开启当前曲目单曲循环
mp3.RepeatCurrent()
# 单曲循环播放3秒
sleep_ms(3000)

# 打印恢复全部循环提示
print("Restore all tracks loop...")
# 开启全部曲目循环
mp3.EnableLoopAll()
# 延迟500毫秒
sleep_ms(500)

# ==================== 随机播放测试 ====================
# 打印随机播放测试标题
print("\n【Random Play Test】")
# 打印开启随机播放提示
print("Enable random playback of all tracks...")
# 开启所有曲目随机播放
mp3.RandomAll()
# 随机播放5秒
sleep_ms(5000)

# ==================== 停止播放测试 ====================
# 打印停止播放测试标题
print("\n【Stop Playback Test】")
# 打印停止播放提示
print("Stop playback...")
# 停止当前音频播放
mp3.Stop()
# 延迟500毫秒
sleep_ms(500)
# 打印停止后的状态
print(f"Status after stop: {'Stopped' if mp3.IsStopped() else 'Not stopped'}")

# ==================== 重置模块 ====================
# 打印重置模块测试标题
print("\n【Reset Module】")
# 打印软复位提示
print("Soft reset KT403A module...")
# 软复位KT403A芯片
mp3.ResetChip()
# 延迟1秒
sleep_ms(1000)
# 打印测试完成提示
print("Test completed!")
