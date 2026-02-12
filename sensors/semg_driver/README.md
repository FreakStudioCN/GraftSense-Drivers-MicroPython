# GraftSense-表面肌电信号运放型采集模块（开放版）

# GraftSense-表面肌电信号运放型采集模块（开放版）

# GraftSense sEMG Op-Amp Acquisition Module

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

本项目是 **GraftSense 系列表面肌电信号运放型采集模块**，属于 FreakStudio 开源硬件项目。模块通过多级运放电路对微弱的表面肌电（sEMG）信号进行放大、滤波处理，输出与肌肉活动强度相关的模拟电压信号，广泛适用于生物信号采集教学实验、人机交互演示、肌电控制开关等场景。

---

## 主要功能

- **模拟信号输出**：AIN 引脚输出与肌肉活动强度正相关的模拟电压，可直接接入 MCU 的 ADC 引脚进行采样。
- **专业信号调理**：集成输入缓冲、前级放大（51 倍）、带通滤波（50Hz~500Hz）、50Hz 双 T 陷波滤波、1.5V 参考电压生成等电路，有效抑制电源干扰和基线漂移。
- **实时信号处理**：驱动支持 100Hz 采样率，内置滑动窗口去直流、0.5Hz 高通、35Hz 低通多级滤波，输出纯净的肌电信号。
- **串口数据输出**：通过 UART 实时输出原始信号和滤波后信号，便于上位机进行波形分析和动作识别。
- **Grove 接口兼容**：遵循 Grove 接口标准，连接便捷，适配主流 MCU 开发平台。

---

## 硬件要求

- **核心电路**：

  - 输入缓冲电路：稳定输入阻抗，减少信号衰减。
  - 前级放大电路：提供 51 倍增益，放大微弱肌电信号。
  - 带通滤波器：通带 50Hz~500Hz，保留有效肌电频段。
  - 50Hz 双 T 陷波滤波器：抑制工频电源干扰（电阻需 1% 精度金属膜，电容建议使用 NPO 陶瓷电容）。
  - 1.5V 参考电压生成电路：为信号处理提供稳定偏置。
- **供电**：3.3V 或 5V 直流供电，模块内置电源滤波和指示灯电路。
- **引脚连接**：

  - AIN：模拟输出引脚，必须连接 MCU 支持 ADC 功能的引脚（如示例中引脚 26）。
  - VCC/GND：电源引脚，遵循 Grove 接口定义。
- **精度要求**：双 T 陷波滤波器的电阻电容精度要求较高，否则会导致中心频率偏移，影响滤波效果。

---

## 文件说明

- `main.py`：SEMG 驱动主程序，实现 100Hz 采样、实时多级滤波、串口数据输出等核心功能，是模块的核心控制程序。

---

## 软件设计核心思想

- **实时性保障**：通过定时器（Timer）以 100Hz 频率触发采样，确保采样率稳定，满足肌电信号实时分析需求。
- **针对性滤波**：针对 sEMG 信号特点，设计 50Hz 陷波（抑制工频干扰）、0.5Hz 高通（去除基线漂移）、35Hz 低通（过滤高频噪声），结合滑动窗口去直流，显著提升信号质量。
- **状态化滤波**：通过维护滤波器状态（`zi_notch`/`zi_hp`/`zi_lp`）和滑动窗口（`dc_buffer`），实现实时连续滤波，避免数据丢失和相位失真。
- **可配置性**：采样率（`FS`）、去直流窗口（`DC_WINDOW`）、滤波带宽等参数可灵活调整，适配不同应用场景。

---

## 使用说明

1. **硬件连接**：

   - 将模块 AIN 引脚连接至 MCU 的 ADC 引脚（如引脚 26），VCC 接 3.3V/5V，GND 接地，遵循 Grove 接口标准。
   - 确保双 T 陷波滤波器的电阻电容符合精度要求，避免滤波效果下降。
2. **初始化配置**：

   ```python
   ```

from machine import ADC, Pin, Timer, UART
import time
from ulab import numpy as np, scipy as spy

# 初始化 ADC（AIN 接 Pin26）

adc = ADC(Pin(26))

# 初始化 UART（波特率 115200）

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

```

3. **启动实时处理**：
	- 配置定时器以 100Hz 频率触发采样，调用 `realtime_process` 函数进行信号采集和滤波。
	- 程序会自动通过串口输出原始值和滤波后值，格式为 `原始值,滤波后值`。

4. **停止程序**：
	- 通过 `KeyboardInterrupt`（Ctrl+C）或 Thonny 停止按钮，安全关闭定时器和程序，释放资源。

---



## 示例程序

```python
# Python env   : MicroPython v1.24.0
# -*- coding: utf-8 -*-
# @Time    : 2026/2/4 下午10:12
# @Author  : hogeiha
# @File    : main.py
# @Description : semg_driver 主程序（100Hz版）

from machine import ADC, Pin, Timer, UART
import time
from ulab import numpy as np, utils
from ulab import scipy as spy

# 100Hz采样率（可根据硬件能力调整）
FS = 100.0
DC_REMOVE_BASE = 0.0
# 200ms去直流窗口，抑制基线漂移
DC_WINDOW = 20
# 运行标志位，用于安全停止程序
running = True

# ===================== SEMG专用滤波器系数 =====================
# 1. 50Hz陷波滤波器：抑制电源干扰（SEMG核心需求）
notch_b0 = 1.0
notch_b1 = -1.0
notch_b2 = 1.0
notch_a0 = 1.080
notch_a1 = -1.0
notch_a2 = 0.920
sos_notch = np.array(
    [[notch_b0 / notch_a0, notch_b1 / notch_a0, notch_b2 / notch_a0, 1.0, notch_a1 / notch_a0, notch_a2 / notch_a0]],
    dtype=np.float)

# 2. 0.5Hz高通滤波器：去除基线漂移（SEMG核心需求）
hp_b0 = 0.9605960596059606
hp_b1 = -1.9211921192119212
hp_b2 = 0.9605960596059606
hp_a0 = 1.0
hp_a1 = -1.918416309168257
hp_a2 = 0.9206736526946108
sos_hp = np.array([[hp_b0 / hp_a0, hp_b1 / hp_a0, hp_b2 / hp_a0, 1.0, hp_a1 / hp_a0, hp_a2 / hp_a0]], dtype=np.float)

# 3. 35Hz低通滤波器：过滤高频噪声（可根据需求调整，SEMG典型带宽20-500Hz）
lp_b0 = 0.2266686574849259
lp_b1 = 0.4533373149698518
lp_b2 = 0.2266686574849259
lp_a0 = 1.0
lp_a1 = -0.18587530329589845
lp_a2 = 0.19550632911392405
sos_lp = np.array([[lp_b0 / lp_a0, lp_b1 / lp_a0, lp_b2 / lp_a0, 1.0, lp_a1 / lp_a0, lp_a2 / lp_a0]], dtype=np.float)

# ===================== 滤波器状态维护 =====================
zi_notch = np.zeros((sos_notch.shape[0], 2), dtype=np.float)
zi_hp = np.zeros((sos_hp.shape[0], 2), dtype=np.float)
zi_lp = np.zeros((sos_lp.shape[0], 2), dtype=np.float)
dc_buffer = np.zeros(DC_WINDOW, dtype=np.float)
dc_idx = 0


def realtime_process(timer):
    global DC_REMOVE_BASE, dc_buffer, dc_idx, zi_notch, zi_hp, zi_lp

    if not running:
        return

    # 1. 采集原始ADC数据
    adc_raw = adc.read_u16()
    raw_val = adc_raw * 3.3 / 65535

    # 2. 滑动窗口去直流（抑制基线漂移）
    dc_buffer[dc_idx] = raw_val
    dc_idx = (dc_idx + 1) % DC_WINDOW
    DC_REMOVE_BASE = np.mean(dc_buffer)
    raw_val_dc = raw_val - DC_REMOVE_BASE

    # 3. 多阶滤波（电源干扰+基线漂移+高频噪声）
    raw_arr = np.array([raw_val_dc], dtype=np.float)
    notch_arr, zi_notch = spy.signal.sosfilt(sos_notch, raw_arr, zi=zi_notch)
    hp_arr, zi_hp = spy.signal.sosfilt(sos_hp, notch_arr, zi=zi_hp)
    filtered_arr, zi_lp = spy.signal.sosfilt(sos_lp, hp_arr, zi=zi_lp)
    filtered_val = filtered_arr[0] * 1.5  # 幅值校准

    # 4. 串口输出（原始值+滤波后值）
    uart_str = f"{raw_val_dc:.6f},{filtered_val:.6f}\r\n"
    uart.write(uart_str.encode('utf-8'))

    # 5. 调试打印
    print_str = f"Original value:{raw_val_dc:.6f}, Filtered value:{filtered_val:.6f}"
    print(print_str)

# 上电延时3s
time.sleep(3)
print("FreakStudio: SEMG Driver (100Hz version)")

# ADC初始化
adc = ADC(Pin(26))

# 串口初始化
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)

print("===== Surface Electromyography System (100Hz Version) =====")
print(f"Sampling Frequency: {FS}Hz | 50Hz Notch Filter | Baseline Drift Removal")
print("Press Ctrl+C/Thonny Stop Button to terminate the program")

uart.write("===== Surface Electromyography System (100Hz Version) =====\r\n".encode('utf-8'))
uart.write(f"Sampling Frequency: {FS}Hz | Output: Raw Value, Filtered Value\r\n".encode('utf-8'))

# 启动定时器采样
timer = Timer(-1)
timer.init(freq=int(FS), mode=Timer.PERIODIC, callback=realtime_process)

# 主线程等待停止信号
try:
    while running:
        time.sleep(0.1)
except KeyboardInterrupt:
    running = False
    timer.deinit()
    print("\nThe program has stopped!")
    uart.write("\nThe program has stopped!\r\n".encode('utf-8'))
```

---

## 注意事项

1. **采样率稳定性**：`FS=100Hz` 为推荐采样率，可根据硬件能力调整，但需确保定时器频率稳定，避免采样率波动影响信号质量。
2. **滤波组件精度**：双 T 陷波滤波器的电阻需选用 1% 精度金属膜电阻，电容建议使用 NPO 陶瓷电容，否则会导致中心频率偏移，滤波效果下降。
3. **去直流窗口调整**：`DC_WINDOW=20`（对应 200ms 窗口）可根据基线漂移情况调整，窗口过大可能导致信号响应延迟。
4. **串口输出格式**：串口输出格式为 `原始值,滤波后值`，上位机解析时需注意逗号分隔符，避免数据解析错误。
5. **ADC 引脚要求**：AIN 引脚必须连接 MCU 支持模拟输入的 ADC 引脚，否则无法采集有效肌电信号。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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