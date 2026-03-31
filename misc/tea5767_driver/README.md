# TEA5767 Driver for MicroPython

# TEA5767 Driver for MicroPython

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

`tea5767_driver` 是一个专为 **MicroPython** 环境开发的 **TEA5767 FM 收音模块** 驱动库，隶属于 GraftSense 驱动生态，由 FreakStudio 开发维护。该库封装了 TEA5767 芯片的核心通信协议，提供简洁易用的 API，帮助开发者快速在 MicroPython 项目中实现 FM 收音功能。

---

## 主要功能

- 支持 FM 频率设置（范围：87.5MHz ~ 108MHz）
- 支持电台自动搜索与手动调谐
- 支持静音控制功能
- 支持获取当前信号强度与立体声状态
- 兼容所有主流 MicroPython 芯片与标准固件

---

## 硬件要求

- **开发板**：任意支持 MicroPython 的开发板（如 ESP32、RP2040、STM32 等）
- **模块**：TEA5767 FM 收音模块（I2C 接口）
- **连接**：通过 I2C 总线连接开发板与 TEA5767 模块（SDA、SCL 引脚需对应连接）
- **电源**：3.3V 或 5V 供电（根据模块规格选择）

---

## 文件说明

## 软件设计核心思想

1. **轻量封装**：仅封装 TEA5767 核心功能，避免冗余代码，保证在资源受限的 MicroPython 设备上高效运行。
2. **I2C 原生支持**：基于 MicroPython 内置 `machine.I2C` 实现通信，无需额外依赖库。
3. **易用性优先**：提供直观的 API 接口，降低开发者使用门槛，快速完成 FM 功能集成。
4. **开源开放**：遵循 MIT 协议开源，允许自由修改、分发与商用，鼓励社区贡献与迭代。

---

## 使用说明

1. **文件部署**：将 `code/tea5767.py` 上传至 MicroPython 设备的文件系统（可通过 ampy、rshell 或 Thonny 等工具）。
2. **导入库**：在你的项目代码中导入 `tea5767` 模块。
3. **初始化 I2C**：根据开发板引脚定义，初始化 I2C 总线。
4. **创建驱动实例**：传入 I2C 对象与 TEA5767 设备地址（默认 `0x60`），创建 `TEA5767` 实例。
5. **调用 API**：通过实例方法控制 FM 功能（如设置频率、搜索电台等）。

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9
# @Author  : hogeiha
# @File    : tea5767_search_max_signal_simple.py
# @Description : 基于原有Radio类搜索最高信号频率（无新增类）

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin

# 导入原有Radio类
from tea5767 import Radio

# ======================================== 全局变量 ============================================

# Pico I2C SCL引脚
I2C_SCL = 5
# Pico I2C SDA引脚
I2C_SDA = 4
# Tea5767默认I2C地址
RADIO_ADDR = 0x60
# 搜索频段：US(87.5-108.0) / JP(76.0-91.0)
SEARCH_BAND = "US"
# FM频率步进（固定0.1MHz）
STEP = 0.1
# 2. 定义频段范围
freq_min, freq_max = Radio.FREQ_RANGE_US if SEARCH_BAND == "US" else Radio.FREQ_RANGE_JP
current_freq = freq_min
max_signal_freq = current_freq
max_signal_level = 0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 补充项目要求的初始化配置
time.sleep(3)
print("FreakStudio: Tea5767 max signal search start")

# 1. 初始化I2C和Radio实例
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)
devices_list: list[int] = i2c.scan()

print("START I2C SCANNER")

# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print("i2c devices found:", len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的RADIO地址
    if device == 0x60:
        # 找到的设备是RADIO地址
        print("I2c hexadecimal address:", hex(device))
        RADIO_ADDR = device

if RADIO_ADDR not in i2c.scan():
    print(f"Error: Tea5767 module not detected (I2C address {hex(RADIO_ADDR)})")
else:
    # 初始化Radio（关闭干扰检测的功能，保证信号读取准确）
    radio = Radio(
        i2c=i2c, addr=RADIO_ADDR, freq=87.5 if SEARCH_BAND == "US" else 76.0, band=SEARCH_BAND, soft_mute=False, noise_cancel=False, high_cut=False
    )
    print(f"Starting {SEARCH_BAND} band scanning...")

# ========================================  主程序  ===========================================

# 3. 逐频率扫描信号强度
while current_freq <= freq_max:
    # 设置当前频率并等待稳定
    radio.set_frequency(current_freq)
    time.sleep_ms(20)
    # 读取最新状态
    radio.read()

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
print("Scanning completed!")
print(f"Max signal frequency: {max_signal_freq} MHz")
print(f"Signal strength level: {max_signal_level} (0-15, higher is stronger)")
print(f"Stereo mode: {'Yes' if radio.is_stereo else 'No'}")
print("=" * 40)

while True:
    pass

```

## 注意事项

- **I2C 地址**：TEA5767 模块默认 I2C 地址为 `0x60`，若模块地址不同，需在创建实例时传入 `addr` 参数修改。
- **天线连接**：使用时需连接天线（如拉杆天线、软天线），否则信号接收效果较差。
- **电压兼容**：确保模块与开发板供电电压匹配（多数 TEA5767 模块支持 3.3V 与 5V 供电）。
- **频率范围**：TEA5767 支持的 FM 频率范围为 87.5MHz ~ 108MHz，超出范围的设置将被忽略。
- **固件依赖**：该库无特殊固件依赖，兼容所有标准 MicroPython 固件（`package.json` 中 `fw` 字段为 `all`）。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源许可协议，完整协议内容如下：

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
