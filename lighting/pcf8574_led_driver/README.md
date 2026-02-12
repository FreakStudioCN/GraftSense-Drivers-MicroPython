# GraftSense 基于 PCF8574 的八段光条数码管模块 （MicroPython）

# GraftSense 基于 PCF8574 的八段光条数码管模块（MicroPython）

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

本项目为 **GraftSense PCF8574-based 8-Segment LED Bar Module V1.0** 提供了完整的 MicroPython 驱动支持，基于 PCF8574 I/O 扩展芯片实现 8 段 LED 光条的灵活控制，支持单个 / 多个 LED 开关、全局清除与电平显示（点亮前 N 个 LED），适用于电子 DIY 计数与状态显示、可视化数据演示等场景。模块通过 A0/A1/A2 跳线支持 8 种 I2C 地址（0x20–0x27），具备接口简便、占用 I2C 总线少、亮度均匀的优势。

---

## 主要功能

- ✅ **单 / 多 LED 精准控制**：支持指定 LED（0–7 索引）的点亮 / 熄灭，或通过 8 位二进制值批量设置所有 LED 状态
- ✅ **电平显示模式**：根据输入 level（0–8）自动点亮前 N 个 LED，适配电平指示、进度条等场景
- ✅ **全局状态管理**：一键清除所有 LED（熄灭），或批量更新 8 段光条状态
- ✅ **I2C 地址可配置**：通过 A0/A1/A2 跳线设置 8 种 I2C 地址（0x20–0x27），支持多设备级联
- ✅ **宽电压兼容**：支持 3.3V/5V 电平通信，适配不同主控设备的供电需求
- ✅ **中断支持（可选）**：PCF8574 驱动支持 INT 引脚触发中断，结合回调实现低功耗状态检测

---

## 硬件要求

1. **核心硬件**：GraftSense PCF8574-based 8-Segment LED Bar Module V1.0（内置 PCF8574 芯片、8 段 LED 光条、地址跳线）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等）
3. **接线配置**：
4. 表格
5. **地址设置**：通过模块背面 A0/A1/A2 跳线设置 I2C 地址：

   - A0/A1/A2 全下拉 → 地址 0x20
   - A0/A1/A2 全上拉 → 地址 0x27
   - 其余组合对应 0x21–0x26（详见模块背面地址表）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **分层驱动架构**：底层 `PCF8574` 类负责 I2C 通信与 GPIO 操作，上层 `LEDBar` 类专注 LED 光条控制，解耦硬件细节与业务逻辑
2. **参数校验防护**：对 LED 索引（0–7）、电平值（0–8）、端口值（0–255）进行严格校验，防止无效配置损坏硬件
3. **状态缓存优化**：通过 `port` 属性缓存 8 位端口状态，避免频繁 I2C 读取，提升响应效率
4. **中断安全设计**：中断回调通过 `micropython.schedule` 调度，避免在 ISR 中执行耗时 I2C 操作，提升系统稳定性
5. **方法封装易用**：将复杂的 I2C 操作封装为 `set_led`、`set_all`、`display_level`、`clear` 等高层 API，降低使用门槛

---

## 使用说明

### 初始化流程

```
from machine import I2C, Pin
from pcf8574 import PCF8574
from led_bar import LEDBar
import time

# 初始化 I2C（示例：Raspberry Pi Pico I2C0，SDA=GP4，SCL=GP5，100kHz）
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=100000)

# 扫描 I2C 设备，获取 PCF8574 地址
devices = i2c.scan()
pcf_addr = None
for dev in devices:
    if 0x20 <= dev <= 0x27:
        pcf_addr = dev
        break

if not pcf_addr:
    raise ValueError("PCF8574 not found on I2C bus!")

# 创建 PCF8574 实例
pcf = PCF8574(i2c, address=pcf_addr)

# 创建 8 段 LED 光条实例
ledbar = LEDBar(pcf)
```

### 核心操作

```
# 点亮第 3 个 LED（索引 2）
ledbar.set_led(2, True)

# 熄灭第 3 个 LED
ledbar.set_led(2, False)

# 批量设置：点亮前 4 个 LED（二进制 0b00001111）
ledbar.set_all(0b00001111)

# 电平显示：点亮前 6 个 LED
ledbar.display_level(6)

# 清除所有 LED（熄灭）
ledbar.clear()
```

---

## 示例程序

```
from machine import I2C, Pin
from pcf8574 import PCF8574
from led_bar import LEDBar
import time

# 上电延时
time.sleep(3)
print("FreakStudio: Test PCF8574 Eight-Segment LED Display Module ")

# 初始化 I2C
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=100000)

# 扫描 I2C 设备
devices_list = i2c.scan()
if not devices_list:
    print("No I2C device found!")
else:
    print(f"I2C devices found: {len(devices_list)}")
    for device in devices_list:
        if 0x20 <= device <= 0x27:
            print(f"I2C hexadecimal address: {hex(device)}")

# 初始化 PCF8574 与 LEDBar
pcf = PCF8574(i2c, address=device)
ledbar = LEDBar(pcf)

# 1. 单个 LED 点亮（第 3 个 LED，索引 2）
ledbar.set_led(2, True)
time.sleep(1)

# 2. 单个 LED 熄灭
ledbar.set_led(2, False)
time.sleep(1)

# 3. 批量设置：点亮前 4 个 LED
ledbar.set_all(0b00001111)
time.sleep(1)

# 4. 电平显示：点亮前 6 个 LED
ledbar.display_level(6)
time.sleep(1)

# 5. 跑马灯效果
for i in range(8):
    ledbar.set_all(1 << i)
    time.sleep(0.2)

# 6. 全部熄灭
ledbar.clear()
```

---

## 注意事项

1. **I2C 地址约束**：PCF8574 仅支持 0x20–0x27 作为 I2C 地址，通过 A0/A1/A2 跳线设置，超出范围将触发 `ValueError`
2. **LED 索引限制**：`set_led` 方法仅支持 0–7 的 LED 索引，超出范围将抛出 `ValueError`
3. **电平值范围**：`display_level` 方法仅支持 0–8 的电平值，对应点亮 0–8 个 LED，超出范围将抛出 `ValueError`
4. **端口值约束**：`set_all` 方法仅支持 0–255（0x00–0xFF）的 8 位值，超出范围将抛出 `ValueError`
5. **I2C 操作安全**：所有 I2C 读写操作非 ISR-safe，禁止在中断处理函数中直接调用，需通过 `micropython.schedule` 调度
6. **中断回调限制**：中断回调函数需轻量，避免执行耗时操作（如串口打印、复杂计算），防止中断调度器异常
7. **默认状态**：模块初始化时默认熄灭所有 LED，需主动调用 `set``_led`、`set_all` 或 `display_le``vel` 点亮

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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