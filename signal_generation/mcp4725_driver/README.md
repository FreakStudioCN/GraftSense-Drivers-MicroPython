# GraftSense MCP4725 数模转换模块 （MicroPython）

# GraftSense MCP4725 数模转换模块 （MicroPython）

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

本项目为 **GraftSense MCP4725 数模转换模块 V1.0** 提供了完整的 MicroPython 驱动支持，基于 MCP4725 12 位高精度 DAC 芯片，实现数字信号到模拟电压的转换输出，适用于电子 DIY 信号输出实验、模拟量控制演示等场景。模块遵循 Grove 接口标准，具备高精度、接口简便、低功耗的优势，支持 I2C 多地址级联，满足多设备扩展需求。

---

## 主要功能

- ✅ **12 位高精度转换**：支持 0–4095 数字值到模拟电压的线性转换，分辨率可达 0.8mV（以 3.3V 参考为例）
- ✅ **I2C 通信控制**：通过 I2C 接口（最高 400kHz）与主控通信，支持 8 个可选 I2C 地址（0x60–0x67），适配多设备级联
- ✅ **电源关断模式**：提供 4 种电源关断模式（Off、1kΩ、100kΩ、500kΩ），灵活降低待机功耗
- ✅ **EEPROM 配置存储**：支持将 DAC 输出值和电源模式写入 EEPROM，上电自动恢复配置
- ✅ **内置电压跟随器**：集成电压跟随器电路，提升输出带载能力，确保信号稳定
- ✅ **Grove 接口便捷连接**：提供 Grove 接口，支持直接接入 Grove 生态设备，无需额外杜邦线

---

## 硬件要求

1. **核心硬件**：GraftSense MCP4725 数模转换模块 V1.0（内置 MCP4725 芯片、电压跟随器、Grove 接口）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等，3.3V 电平兼容）
3. **接线方式**：

   - **I2C 连接**：模块 SDA → 主控 SDA 引脚（如 Raspberry Pi Pico GP4）；模块 SCL → 主控 SCL 引脚（如 GP5）
   - **电源连接**：模块 Grove 接口 VCC/GND → 主控板 3.3V/GND
   - **输出连接**：模块 DAC 输出引脚 → 目标模拟设备（如 LED、电机驱动、ADC 采集端）
4. **配件要求**：可选 ADC 模块（用于验证 DAC 输出波形）、串口调试助手（用于查看 ADC 采集数据）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **I2C 寄存器抽象**：将 MCP4725 的寄存器操作封装为高层 API，隐藏底层 I2C 读写细节，降低使用门槛
2. **参数校验与容错**：对 I2C 地址（0x60–0x67）、DAC 输出值（0–4095）、电源模式等参数进行严格校验，避免无效配置导致硬件异常
3. **状态同步管理**：内部维护 DAC 输出值与电源模式状态，通过 `read()` 方法同步芯片寄存器状态，确保配置一致性
4. **低功耗优化**：支持电源关断模式配置，通过 EEPROM 存储上电默认状态，减少待机功耗
5. **示例驱动验证**：通过正弦波生成与 ADC 采集反馈，直观验证 DAC 输出性能，便于快速上手与调试

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件（如 Raspberry Pi Pico 可使用官方固件）
- 将 `mcp4725.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

1. 模块 Grove 接口 → 主控板 Grove I2C 接口（或通过杜邦线连接 SDA/SCL/VCC/GND）
2. 模块 DAC 输出引脚 → ADC 输入引脚（如 Raspberry Pi Pico GP27，用于验证波形）
3. 确保模块与主控共地，避免信号干扰

### 核心操作流程

#### 初始化与扫描

```
from machine import I2C, Pin
from mcp4725 import MCP4725
import time

# 初始化 I2C（Raspberry Pi Pico 示例：I2C0，SDA=GP4，SCL=GP5，400kHz）
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

# 扫描 I2C 设备，获取 DAC 地址
devices = i2c.scan()
dac_addr = None
for dev in devices:
    if 0x60 <= dev <= 0x67:
        dac_addr = dev
        break

if dac_addr is None:
    raise RuntimeError("MCP4725 not found on I2C bus!")

# 创建 DAC 实例
dac = MCP4725(i2c, dac_addr)
```

#### 写入 DAC 输出值

```
# 输出 1.65V（对应数字值 2048，假设满量程 3.3V）
dac.write(2048)
```

#### 配置电源模式与 EEPROM

```
# 配置为正常模式，输出 0V，并写入 EEPROM（上电自动恢复）
dac.config(power_down='Off', value=0, eeprom=True)
time.sleep_ms(50)  # 配置后延时，避免读取错误
```

#### 读取芯片状态

```
# 读取 EEPROM 状态、电源模式、当前输出值等
eeprom_busy, pd_mode, current_val, eeprom_pd, eeprom_val = dac.read()
print(f"当前输出值: {current_val}, EEPROM 存储值: {eeprom_val}")
```

---

## 示例程序

### 正弦波生成与 ADC 验证（main.py）

```
from machine import ADC, Timer, Pin, I2C, UART
import time
import math
from mcp4725 import MCP4725

# 全局变量
DAC_ADDRESS = 0x00
adc_conversion_factor = 3.3 / 65535

def timer_callback(timer):
    global adc, adc_conversion_factor, uart
    value = adc.read_u16() * adc_conversion_factor
    formatted_value = "{:.2f}".format(value)
    uart.write(str(formatted_value) + '\r\n')
    print('dac generated voltage: ' + str(formatted_value))

# 初始化
time.sleep(3)
print("FreakStudio : Using DAC to generate sine wave")

i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
devices_list = i2c.scan()
for device in devices_list:
    if 0x60 <= device <= 0x61:
        DAC_ADDRESS = device

dac = MCP4725(i2c, DAC_ADDRESS)
dac.config(power_down='Off', value=0, eeprom=True)
time.sleep_ms(50)

adc = ADC(1)  # ADC1-GP27
timer = Timer(-1)
timer.init(period=5, mode=Timer.PERIODIC, callback=timer_callback)

uart = UART(0, 115200)
uart.init(baudrate=115200, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)

# 生成正弦波
for i in range(10000):
    value = 3.3 * math.sin(2 * math.pi * i / 100) + 3.3
    value = int(value * 4095 / 6.6)
    dac.write(value)
    time.sleep_ms(10)

timer.deinit()
```

---

## 注意事项

1. **I2C 地址约束**：MCP4725 仅支持 0x60–0x67 作为 I2C 地址，超出范围将触发 `ValueError`
2. **输出值范围**：DAC 输出数字值必须在 0–4095 之间，对应模拟电压由模块参考电压（通常 3.3V）决定
3. **配置后延时**：调用 `config()` 写入 EEPROM 后，需延时至少 50ms，避免立即读取导致状态错误
4. **电源关断模式**：电源关断模式下 DAC 输出将被拉至地（通过内部电阻），需根据应用场景选择合适模式
5. **ADC 采集验证**：示例中 ADC 采集用于验证 DAC 输出，实际使用时可根据需求移除，避免资源占用
6. **带载能力**：模块内置电压跟随器，可驱动轻负载设备，若需驱动大负载，建议增加外部运放电路

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源协议，具体内容如下：

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
