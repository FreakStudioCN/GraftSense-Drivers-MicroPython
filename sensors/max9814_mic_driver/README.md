# GraftSense-基于 MAX9814 的驻极体电容式麦克风模块（MicroPython）

# GraftSense-基于 MAX9814 的驻极体电容式麦克风模块（MicroPython）

# 基于 MAX9814 的驻极体电容式麦克风模块 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本项目是基于 MAX9814 的驻极体电容式麦克风模块的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 ADC 接口采集放大后的模拟音频信号，支持自动增益控制（AGC）、多档位增益切换、环境噪声基线校准等功能，适用于声音检测实验、语音触发识别、环境噪声监测、小型音频采集等场景。

---

## 主要功能

- 多维度信号读取:支持 16 位 ADC 原始值、归一化值（0–1）、电压值（基于参考电压）读取
- 多档位增益控制:通过 DOUT 引脚切换 40dB/50dB/60dB 增益档位，适配不同声音强度场景
- 信号噪声抑制:提供多采样平均值、峰值读取功能，降低瞬时噪声对信号的干扰
- 环境自适应校准:自动采集环境噪声基线，动态调整声音检测阈值，提升环境适配性
- 声音状态检测:基于阈值判断声音有无，支持自定义采样次数与触发阈值
- 模块状态管理:支持启用/禁用模块，实时获取当前工作状态（启用状态、增益档位等）
- 参数灵活配置:参考电压、采样次数等参数可自定义，适配不同硬件环境
- 标准接口兼容:兼容 MicroPython ADC/Pin 接口，支持 ESP32、RP2040 等主流 MCU

---

## 硬件要求

- MAX9814 驻极体电容式麦克风模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040、STM32 等）
- 引脚连接:

  - 模块 VCC → MCU 3.3V/5V 电源引脚
  - 模块 GND → MCU GND 引脚
  - 模块 AIN → MCU ADC 引脚（如 ESP32 的 GPIO26）
  - 模块 DOUT → MCU 数字 GPIO 引脚（如 ESP32 的 GPIO6，用于增益控制）
- 模块硬件特性:

  - 内置电源滤波电路（100nF/2.2μF 电容），滤除电源噪声
  - 集成自动增益控制（AGC），适配不同音量强度的声音采集
  - 支持 40dB/50dB/60dB 增益切换，通过 DOUT 引脚控制档位
  - 内置驻极体麦克风与放大电路，直接输出模拟音频信号

---

## 文件说明

| 文件名         | 说明                                                                                    |
| -------------- | --------------------------------------------------------------------------------------- |
| max9814_mic.py | 核心驱动文件，包含 `MAX9814Mic` 类，实现 ADC 信号读取、增益控制、基线校准、声音检测等功能 |
| main.py        | 测试示例程序，包含基础读取、增益控制、声音检测 3 种测试模式，演示驱动的各类功能         |

---

## 软件设计核心思想

1. 硬件操作封装:将 ADC 采集、增益引脚控制、模块状态管理封装为 `MAX9814Mic` 类，简化用户对硬件的直接操作
2. 多维度数据输出:同时支持原始 ADC 值、归一化值、电压值读取，适配不同场景的数据处理需求
3. 动态增益适配:通过 `set_gain()` 方法实现多档位增益切换，灵活匹配强弱声音的采集需求
4. 环境自适应校准:`calibrate_baseline()` 方法自动获取环境噪声基线，解决不同场景下的阈值适配问题
5. 噪声抑制处理:通过平均值/峰值读取功能，降低瞬时噪声对信号检测的干扰
6. 状态可视化管理:`get_state()` 方法统一返回模块工作状态，便于调试与状态监控
7. 安全兼容设计:明确标注 ISR 不安全方法，避免中断上下文的资源冲突

---

## 使用说明

1. 硬件连接

- 模块 VCC → MCU 3.3V/5V 电源引脚
- 模块 GND → MCU GND 引脚
- 模块 AIN → MCU ADC 引脚（如 ESP32 的 GPIO26）
- 模块 DOUT → MCU 数字 GPIO 引脚（如 ESP32 的 GPIO6）

1. 驱动初始化

```python
from machine import Pin, ADC
from max9814_mic import MAX9814Mic

# 初始化ADC（示例:ESP32 GPIO26对应ADC0）
adc = ADC(26)
# 初始化增益控制引脚
gain_pin = Pin(6, Pin.OUT)
# 初始化麦克风实例
mic = MAX9814Mic(adc=adc, gain_pin=gain_pin)
```

1. 基础操作示例

- 读取 16 位 ADC 原始值

```python
raw_value = mic.read()
print(f"ADC原始值: {raw_value}")
```

- 读取归一化值（0–1）

```python
normalized_val = mic.read_normalized()
print(f"归一化值: {normalized_val:.3f}")
```

- 读取电压值（默认参考电压 3.3V）

```python
voltage = mic.read_voltage(vref=3.3)
print(f"信号电压: {voltage:.3f}V")
```

- 切换增益档位（以高增益为例）

```python
mic.set_gain(high=True)  # 高增益对应60dB，低增益对应40dB
print("当前增益状态: 高增益")
```

- 校准环境噪声基线

```python
baseline = mic.calibrate_baseline(samples=200)
print(f"环境噪声基线: {baseline}")
```

- 检测声音（基于基线 + 阈值）

```python
is_sound = mic.detect_sound_level(threshold=baseline + 5000, samples=10)
print(f"是否检测到声音: {is_sound}")
```

---

## 示例程序

### 1. 基础读取测试

```python
def test_basic_reading() -> None:
    time.sleep(3)
    print("FreakStudio:max9814_mic_driver test start")
    print("=== Basic Reading Test ===")
    adc = ADC(26)
    mic = MAX9814Mic(adc=adc)
    print("Microphone initialized on ADC0 (GP26)")
    print("State:", mic.get_state())
    print("Reading values for ~10 seconds...")
    try:
        for i in range(100):
            raw_value = mic.read()
            normalized = mic.read_normalized()
            voltage = mic.read_voltage()
            print(f"[{get_formatted_time()}] Raw:{:5d} | Norm:{:.3f} | Volt:{:.3f}V".format(
                raw_value, normalized, voltage
            ))
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[{}] Basic test interrupted".format(get_formatted_time()))
```

### 2. 增益控制测试

```python
def test_with_gain_control() -> None:
    time.sleep(3)
    print("=== Gain Control Test ===")
    adc = ADC(26)
    gain_pin = Pin(6, Pin.OUT)
    mic = MAX9814Mic(adc=adc, gain_pin=gain_pin)
    try:
        # 低增益模式（40dB）
        print("=== LOW GAIN mode (40dB) ===")
        mic.set_gain(False)
        print("State:", mic.get_state())
        for i in range(50):
            print(f"[LOW] {mic.read():5d}", end=" ")
            if (i + 1) % 5 == 0:
                print()
            time.sleep(0.6)
        
        # 高增益模式（60dB）
        print("\n=== HIGH GAIN mode (60dB) ===")
        mic.set_gain(True)
        print("State:", mic.get_state())
        for i in range(50):
            print(f"[HIGH]{mic.read():5d}", end=" ")
            if (i + 1) % 5 == 0:
                print()
            time.sleep(0.6)
    except KeyboardInterrupt:
        print("\n[{}] Gain test interrupted".format(get_formatted_time()))
```

### 3. 声音检测测试

```python
def test_sound_detection() -> None:
    time.sleep(3)
    print("=== Sound Detection Test ===")
    adc = ADC(26)
    mic = MAX9814Mic(adc=adc)
    print("Calibrating baseline noise level...")
    baseline = mic.calibrate_baseline(samples=200)
    threshold = baseline + 5000
    print(f"Baseline: {baseline} | Threshold: {threshold}")
    print("Make some noise near the mic! (Ctrl+C to stop)")
    try:
        silent_count = 0
        while True:
            current_value = mic.read()
            is_sound = mic.detect_sound_level(threshold=threshold, samples=10)
            if is_sound:
                peak = mic.get_peak_reading(samples=20)
                print(f"[{get_formatted_time()}] SOUND! Current: {current_value} Peak: {peak}")
                silent_count = 0
            else:
                silent_count += 1
                if silent_count % 50 == 0:
                    print(f"[{get_formatted_time()}] Silent... Current: {current_value} (Th: {threshold})")
            time.sleep(0.6)
    except KeyboardInterrupt:
        print("\n[{}] Detection stopped".format(get_formatted_time()))
```

---

## 注意事项

1. ADC 引脚限制:AIN 接口为模拟信号输出，必须连接到 MCU 支持 ADC 功能的引脚，不可接入普通数字 GPIO
2. 参考电压匹配:`read_voltage()` 方法的 `vref` 参数需与 MCU 的 ADC 参考电压一致（默认 3.3V），否则电压计算结果会偏差
3. 增益档位说明:DOUT 引脚高电平对应 60dB 增益，低电平对应 40dB 增益，浮空状态对应 50dB 增益
4. 基线校准环境:校准基线时需保持环境安静，否则会导致声音检测阈值不准确
5. ISR 安全限制:包含 ADC 读取、引脚操作的方法（如 `read()`、`set_gain()`）不可在中断服务例程（ISR）中直接调用
6. 采样次数调整:平均值/峰值读取、基线校准的采样次数可根据环境噪声调整，次数越多结果越稳定但耗时更长

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:

📧 **邮箱**:liqinghsui@freakstudio.cn

💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

```
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```