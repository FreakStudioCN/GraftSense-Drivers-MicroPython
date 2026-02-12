# GraftSense-基于 DS1307 芯片的 RTC 实时时钟模块（MicroPython）

# GraftSense-基于 DS1307 芯片的 RTC 实时时钟模块（MicroPython）

# GraftSense 基于 DS1307 的 RTC 实时时钟模块

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

本模块是 FreakStudio GraftSense 基于 DS1307 芯片的 RTC 实时时钟模块，通过 DS1307 芯片实现精准时间记录与掉电计时功能，采用 I2C 通信接口，具备掉电走时、接口简单、功耗低等核心优势，兼容 Grove 接口标准。适用于创客项目时间记录、嵌入式设备计时、工业仪表时间同步等场景，为系统提供可靠的实时时钟数据交互能力。

## 主要功能

### 硬件层面

- 支持 I2C 标准通信，兼容 3.3V/5V 电平，接口遵循 Grove 标准，接线简单
- 内置锂电池供电回路，掉电后仍可维持精准计时，48mAh 锂电池在 25℃ 下可工作十年
- 32.768kHz 高精度晶振，保障计时准确性，支持秒/分/时/日/月/年全维度时间记录
- 5V 转 3.3V 稳压电路 + 电源滤波设计，适配主流嵌入式系统供电，抗干扰能力强

### 软件层面

- 基于 MicroPython 封装 DS1307 驱动类，支持时间的读写、振荡器启停控制
- 提供兼容 MicroPython 内置 RTC 的时间格式，可直接同步系统时间
- 内置 BCD/十进制自动转换逻辑，适配 DS1307 寄存器编码规则
- 自动处理年份补全（两位年份 →20xx）、星期格式转换（0-6→1-7）等细节

## 硬件要求

### 核心接口

- I2C 通信接口：

  - 支持标准 I2C 通信速率，固定 I2C 设备地址为 0x68，兼容 3.3V/5V 电平
  - 引脚定义：SDA（I2C 数据）、SCL（I2C 时钟）、VCC（供电）、GND（接地），遵循 Grove 接口标准
- 锂电池座子：用于掉电后维持计时，DS1307 在掉电后仍能正常计时；若采用 48mAh 锂电池，在 25℃ 下可工作十年（数据手册）
- 电源指示灯：LED1 常亮表示模块供电正常

### 电路设计

- DS1307 核心电路：DS1307 芯片负责实时时钟计时，支持秒、分、时、日、月、年等时间数据读写，以及 56 字节 RAM 数据存取
- 时钟晶振：32.768kHz 晶振提供精准计时基准
- DC-DC 5V 转 3.3V 电路：适配 5V 供电系统，为 DS1307 提供稳定 3.3V 工作电压
- 上拉电阻：R1/R2 为 I2C 总线提供上拉，保障通信稳定性
- 电源滤波：C1/C4/C5 滤波电容抑制电源噪声，提升计时精度

### 模块布局

- 正面：DS1307 芯片、锂电池座子、I2C 接口（SDA/SCL）、电源接口（VCC/GND）、电源指示灯（LED1），接口清晰标注，便于接线调试与快速部署

## 文件说明

| 文件名    | 功能说明                                                                           |
| --------- | ---------------------------------------------------------------------------------- |
| ds1307.py | DS1307 RTC 模块的核心驱动文件，封装了 DS1307 类及所有时间操作、寄存器交互方法      |
| main.py   | 模块使用示例文件，包含 I2C 初始化、设备扫描、时间读写、系统 RTC 同步等完整演示代码 |
| README.md | 模块说明文档，包含功能介绍、硬件要求、使用方法、注意事项等全量信息                 |

## 软件设计核心思想

核心类：DS1307（RTC 驱动）

基于 MicroPython 实现，封装 DS1307 实时时钟的操作，核心设计思想如下：

### 1. 核心属性

| 属性                | 类型      | 说明                               |
| ------------------- | --------- | ---------------------------------- |
| i2c                 | I2C       | I2C 总线实例，用于与 DS1307 通信   |
| addr                | int       | DS1307 的 I2C 地址（默认 0x68）    |
| buf                 | bytearray | 7 字节缓冲区，用于读写时间寄存器   |
| buf1                | bytearray | 1 字节缓冲区，用于单字节寄存器操作 |
| _disable_oscillator | bool      | 振荡器禁用状态标志                 |

### 2. 核心方法

| 方法/属性                          | 功能                                | 参数说明                                                          | 返回值                                                                                          |
| ---------------------------------- | ----------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| datetime（属性，可读写）           | 获取/设置当前日期时间               | 设置时传入元组：(year, month, day, hour, minute, second, weekday) | 获取时返回元组：(year, month, day, hour, minute, second, weekday, None)                         |
| datetimeRTC（属性）                | 获取兼容 MicroPython RTC 的时间格式 | 无                                                                | 元组：(year, month, day, None, hour, minute, second, None)，可直接用于 machine.RTC().datetime() |
| disable_oscillator（属性，可读写） | 获取/设置振荡器禁用状态             | 设置时传入 bool：True 禁用，False 启用                            | 获取时返回 bool：True 表示振荡器禁用（计时停止）                                                |
| _bcd2dec(bcd: int)                 | BCD 转十进制（内部工具方法）        | bcd: BCD 编码值                                                   | 十进制数值                                                                                      |
| _dec2bcd(decimal: int)             | 十进制转 BCD（内部工具方法）        | decimal: 十进制数值                                               | BCD 编码值                                                                                      |

### 3. 设计关键点

- 数据格式适配：自动完成 BCD/十进制转换，屏蔽 DS1307 寄存器的编码细节，简化上层使用
- 兼容性设计：提供 datetimeRTC 属性，直接适配 MicroPython 内置 RTC 的时间格式，降低系统集成成本
- 异常场景处理：自动补全年份（2 位 →4 位）、转换星期格式，避免用户手动处理硬件底层规则
- 资源优化：使用固定缓冲区（buf/buf1）减少内存频繁分配，提升嵌入式场景下的运行效率

## 使用说明

### 前置准备

1. 硬件接线：将模块的 SDA/SCL 分别连接到开发板的 I2C 对应引脚（示例中为 Pin4/Pin5），VCC 接 5V/3.3V，GND 接地
2. 安装依赖：确保开发板已烧录 MicroPython 固件，无需额外安装第三方库
3. 电池安装：为模块安装锂电池（注意极性），确保掉电计时功能可用

### 基本使用流程

1. 初始化 I2C 总线，扫描并确认 DS1307 设备地址（默认 0x68）
2. 创建 DS1307 类实例，建立与模块的通信连接
3. （可选）启用振荡器（默认应启用，禁用会停止计时）
4. 读写时间：设置指定时间，或读取当前计时时间
5. （可选）将 DS1307 时间同步到开发板内置 RTC，实现系统时间校准

## 示例程序

以下是 main.py 中的核心示例代码，实现 DS1307 的时间设置、读取与系统 RTC 同步：

```python
from machine import Pin, I2C, RTC
import ds1307
import time

# 初始化配置
time.sleep(3)
print("FreakStudio: test ds1307 RTC now")

# 初始化I2C总线（SCL=Pin5, SDA=Pin4, 频率100kHz）
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 扫描I2C设备，定位DS1307地址
devices_list = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
    for device in devices_list:
        if 0x60 <= device <= 0x70:  # 筛选DS1307地址范围
            print("I2c hexadecimal address:", hex(device))
            DS1307_ADDRESS = device

# 初始化DS1307实例
ds1307rtc = ds1307.DS1307(i2c, DS1307_ADDRESS)
print("DS1307 attributes:", dir(ds1307rtc))

# 振荡器开关测试（禁用会停止计时）
ds1307rtc.disable_oscillator = True
print("disable_oscillator =", ds1307rtc.disable_oscillator)
ds1307rtc.disable_oscillator = False
print("disable_oscillator =", ds1307rtc.disable_oscillator, "\n")

# 读取当前时间
print("Current DS1307 datetime:", ds1307rtc.datetime, "\n")

# 设置时间：(2025年9月17日 17:47:17，星期6)
ds1307rtc.datetime = (2025, 9, 17, 17, 47, 17, 6)
print("After setting datetime:", ds1307rtc.datetime)

# 等待3.9秒后再次读取，验证计时
time.sleep(3.9)
print("After 3.9s:", ds1307rtc.datetime, "\n")

# 获取兼容Pico RTC的时间格式
print("DS1307 datetime formatted for Pico RTC:", ds1307rtc.datetimeRTC, "\n")

# 同步到Pico内部RTC
print("Pico internal RTC time:", time.localtime(), "\n")
rtc = RTC()
rtc.datetime(ds1307rtc.datetimeRTC)
print("Pico RTC set from DS1307, now:", time.localtime())
```

### 示例说明

1. I2C 初始化与设备扫描：通过 I2C 总线扫描定位 DS1307 地址，确保通信正常
2. 振荡器控制：测试振荡器禁用/启用，验证计时启停功能
3. 时间设置与读取：设置指定时间后读取，验证计时准确性
4. 系统 RTC 同步：将 DS1307 时间同步到 MicroPython 内置 RTC，实现系统时间校准

## 注意事项

1. I2C 地址固定：DS1307 的 I2C 地址为 0x68，不可修改，需确保总线上无地址冲突
2. 锂电池安装：安装锂电池时注意极性（+/-标识），避免反接损坏模块；锂电池寿命与容量相关，48mAh 电池在 25℃ 下可工作约十年
3. 时间格式限制：

- 年份仅支持 2000-2099（驱动自动补全 20xx）
- 星期（weekday）需传入 0-6（对应周一到周日，驱动内部转换为 1-7 存储）

1. 振荡器控制：禁用振荡器（disable_oscillator=True）会停止 DS1307 计时，仅在低功耗待机场景使用，恢复计时需重新启用
2. 掉电计时依赖电池：掉电后计时功能完全依赖锂电池，电池耗尽后时间会重置，需重新设置

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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

---
