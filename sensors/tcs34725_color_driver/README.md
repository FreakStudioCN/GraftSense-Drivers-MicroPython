# GraftSense TCS34725 颜色识别模块 (MicroPython)

# GraftSense TCS34725 颜色识别模块驱动(MicroPython)

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

---

## 简介

本项目为 **GraftSense TCS34725-based Color Recognition Module V1.1** 提供了完整的 MicroPython 驱动支持，基于 TCS34725 芯片实现高精度 RGB 颜色识别与环境光数据采集。驱动支持传感器激活 / 关闭、积分时间与增益调节、原始 RGBC 数据读取及色温和亮度转换，并提供中断阈值配置功能，内置补光电路可改善暗光环境下的检测效果，适用于颜色分类实验、智能设备色彩感知、工业检测颜色辨别等场景，为颜色感知类应用提供精准的数字信号交互能力。

---

## 主要功能

- ✅ 支持 I2C 通信，默认地址 0x29，兼容 3.3V/5V 电平
- ✅ 提供传感器激活 / 关闭控制，可自动管理补光 LED 状态
- ✅ 支持积分时间（2.4~614.4ms）与增益（1/4/16/60）调节，平衡检测精度与灵敏度
- ✅ 可读取原始 RGBC 四通道数据，或转换为相关色温（CCT）与亮度（Lux）
- ✅ 提供中断阈值配置功能，支持持续周期与上下阈值设置，便于触发式检测
- ✅ 内置补光控制电路，可通过拨码开关打开补光，改善暗光环境检测效果
- ✅ 提供辅助函数，支持将原始 RGBC 数据转换为标准 RGB 值或 HTML 颜色代码

---

## 硬件要求

1. **核心硬件**：GraftSense TCS34725-based Color Recognition Module V1.1（基于 TCS34725 芯片，内置补光 LED 与 DC-DC 5V 转 3.3V 电路）
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等）
3. **接线配件**：Grove 4Pin 线或杜邦线，用于连接模块的 SDA、SCL、GND、VCC 引脚
4. **电源**：3.3V~5V 稳定电源（模块内置电平转换电路，兼容两种供电方式）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **寄存器抽象**：通过 `_register8()` 和 `_register16()` 方法封装 TCS34725 寄存器读写操作，隐藏底层 I2C 通信细节，提供简洁的上层接口
2. **状态机管理**：通过 `active()` 方法统一管理传感器电源与 ADC 使能状态，自动控制补光 LED 开关，简化用户操作
3. **参数校验**：对积分时间、增益、中断阈值等参数进行合法性校验，避免非法值导致传感器工作异常
4. **数据转换**：内置 RGBC 到 XYZ 颜色空间的线性变换及色温近似算法，支持直接输出色温和亮度，无需用户额外计算
5. **中断支持**：提供完整的中断阈值配置与清除接口，适配触发式检测场景，降低 CPU 占用

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `tcs34725_color.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线或杜邦线将模块的 **SDA** 引脚连接至开发板指定 GPIO 引脚（如树莓派 Pico 的 GP4）
- 将模块的 **SCL** 引脚连接至开发板指定 GPIO 引脚（如树莓派 Pico 的 GP5）
- 连接 `GND` 和 `VCC` 引脚，确保 3.3V~5V 供电稳定
- 若需补光，可通过模块上的拨码开关打开补光电路

### 代码配置

```python
import machine
from tcs34725_color import TCS34725, html_hex

# 初始化 I2C 总线
i2c = machine.I2C(id=0, sda=machine.Pin(4), scl=machine.Pin(5), freq=400000)

# 初始化 TCS34725 传感器（地址 0x29，补光 LED 引脚为 GP25）
sensor = TCS34725(i2c, address=0x29, led_pin=25)

# 设置积分时间 50ms，增益 4x
sensor.integration_time(50)
sensor.gain(4)
```

### 数据读取

```python
# 读取原始 RGBC 数据
r, g, b, c = sensor.read(raw=True)
print(f"Raw RGBC: R={r}, G={g}, B={b}, C={c}")

# 读取色温和亮度
cct, lux = sensor.read()
print(f"Color Temperature: {cct:.2f}K, Illuminance: {lux:.2f}")

# 转换为 HTML 颜色代码
rgb_data = sensor.read(raw=True)
hex_color = html_hex(rgb_data)
print(f"HTML Color: #{hex_color}")
```

---

## 示例程序

```python
import machine
import time
from tcs34725_color import TCS34725, html_hex

# 初始化 I2C
i2c = machine.I2C(id=0, sda=machine.Pin(4), scl=machine.Pin(5), freq=400000)

# 初始化传感器，启用补光 LED
sensor = TCS34725(i2c, address=0x29, led_pin=25)
sensor.active(True)  # 激活传感器并点亮补光 LED

# 配置检测参数
sensor.integration_time(100)  # 积分时间 100ms
sensor.gain(16)               # 增益 16x

try:
    while True:
        # 读取颜色数据
        r, g, b, c = sensor.read(raw=True)
        cct, lux = sensor.read()
        hex_color = html_hex((r, g, b, c))
        
        # 打印结果
        print(f"RGBC: R={r:4d}, G={g:4d}, B={b:4d}, C={c:4d} | "
              f"CCT: {cct:5.1f}K, Lux: {lux:6.1f} | "
              f"Color: #{hex_color}")
        
        time.sleep(1)

except KeyboardInterrupt:
    sensor.active(False)  # 关闭传感器并熄灭补光 LED
    print("Color sensing stopped.")
```

---

## 注意事项

1. **地址与电平**：模块默认 I2C 地址为 0x29，仅支持 3.3V 通信，5V 主控需确保引脚电平兼容
2. **补光使用**：补光电路可通过拨码开关独立控制，也可通过 `led_pin` 参数由软件控制，避免长时间高亮度补光导致功耗过高
3. **积分时间与增益**：积分时间越长、增益越大，检测精度越高，但响应速度越慢，需根据场景平衡配置
4. **环境干扰**：强光或多光源环境可能影响颜色识别精度，建议在均匀光照条件下使用，或通过补光电路稳定光照
5. **中断配置**：中断阈值设置后，需通过 `interrupt(False)` 手动清除中断标志，避免重复触发

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

```
MIT License

Copyright (c) 2025 FreakStudio

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