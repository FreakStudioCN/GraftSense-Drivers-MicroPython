# kt403a_driver - MicroPython KT403A 驱动库

# kt403a_driver - MicroPython KT403A 驱动库

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

`kt403a_driver` 是 **GraftSense-Drivers-MicroPython** 项目下的一个轻量级 MicroPython 驱动库，专为 KT403A 语音播放芯片设计。该库提供了简洁易用的 API，帮助开发者快速在 MicroPython 环境中实现对 KT403A 模块的控制，支持多种芯片平台与固件版本，遵循 MIT 开源协议。

## 主要功能

- ✅ 实现 KT403A 语音模块的基础控制：播放、暂停、停止、曲目切换
- ✅ 支持音量调节、曲目查询、播放状态检测
- ✅ 适配 MicroPython 轻量运行环境，无额外固件依赖
- ✅ 兼容多种 MicroPython 芯片平台（ESP32、RP2040 等）
- ✅ 模块化设计，便于移植与二次开发

## 硬件要求

- **开发板**：任意支持 MicroPython 的开发板（如 ESP32、Raspberry Pi Pico、STM32 等）
- **外设模块**：KT403A 语音播放模块
- **连接方式**：通过 UART 串口与开发板通信（需连接 TX/RX 引脚及共地）
- **电源**：3.3V/5V 稳定供电（根据模块规格选择）

## 文件说明

## 软件设计核心思想

1. **轻量无依赖**：不依赖特定固件（如 ulab、lvgl），可直接在标准 MicroPython 固件中运行
2. **模块化封装**：将 KT403A 通信协议封装为独立类，对外暴露简洁的控制方法，降低使用门槛
3. **跨平台兼容**：通过抽象硬件通信层（UART），支持多种 MicroPython 芯片平台
4. **易用性优先**：API 设计贴合嵌入式开发场景，减少配置成本，快速上手

## 使用说明

1. 将 `code/kt403a.py` 文件上传至 MicroPython 开发板的文件系统
2. 在项目中导入 `KT403A` 类，初始化 UART 串口通信
3. 调用类方法实现对 KT403A 模块的控制（如播放、暂停、音量调节等）

## 示例程序

```python
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
print("
【Basic Information Query】")
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
print("
【Volume Control Test】")
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
print("
【EQ Effect Switch Test】")
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
print("
【Playback Control Test (for 4 audio files)】")
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
print("
【Loop Mode Test】")
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
print("
【Random Play Test】")
# 打印开启随机播放提示
print("Enable random playback of all tracks...")
# 开启所有曲目随机播放
mp3.RandomAll()
# 随机播放5秒
sleep_ms(5000)

# ==================== 停止播放测试 ====================
# 打印停止播放测试标题
print("
【Stop Playback Test】")
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
print("
【Reset Module】")
# 打印软复位提示
print("Soft reset KT403A module...")
# 软复位KT403A芯片
mp3.ResetChip()
# 延迟1秒
sleep_ms(1000)
# 打印测试完成提示
print("Test completed!")

```

## 注意事项

- ⚠️ 请确保 KT403A 模块与开发板共地，避免通信异常
- ⚠️ KT403A 默认 UART 波特率为 9600，8N1 格式，请勿随意修改
- ⚠️ 曲目文件名需符合 KT403A 命名规范（如 0001.mp3、0002.mp3）
- ⚠️ 避免频繁快速发送指令，建议每次发送指令后间隔 50-100ms
- ⚠️ 电源不稳定可能导致模块工作异常，建议使用稳压电源供电

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copyof this software and associated documentation files (the "Software"), to dealin the Software without restriction, including without limitation the rightsto use, copy, modify, merge, publish, distribute, sublicense, and/or sellcopies of the Software, and to permit persons to whom the Software isfurnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in allcopies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS ORIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THEAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHERLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THESOFTWARE.
```
