# GraftSense-光耦隔离 MOS 管单电机驱动模块（MicroPython）

## GraftSense-光耦隔离 MOS 管单电机驱动模块（MicroPython）

# GraftSense 光耦隔离 MOS 单电机驱动模块

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

本模块是 FreakStudio GraftSense 光耦隔离 MOS 单电机驱动模块，专为单直流电机驱动、MOS 管开关控制、光耦隔离保护设计，适用于电子 DIY 电机控制实验、机器人驱动演示、嵌入式负载控制项目。模块通过光耦实现电气隔离，避免功率端干扰窜入控制端，同时借助 MOS 管实现对负载的高效开关驱动，具备强抗干扰能力、驱动稳定、操作可靠等优势，兼容 Grove 接口标准。

## 主要功能

### 硬件功能

1. **电气隔离**:采用 EL817S 光耦实现控制信号与功率回路的电气隔离，提升系统稳定性和安全性；
2. **高效驱动**:通过 IRFR9024NTRPBF MOS 管实现负载的高效开关驱动，适配直流电机等感性负载；
3. **续流保护**:集成 SS34 二极管，为感性负载提供续流保护，防止反向电动势损坏器件；
4. **状态指示**:LED1 指示灯直观显示模块工作状态（MOS 管导通时点亮）；
5. **滤波抗干扰**:多电容滤波电路保障电源和控制信号稳定，提升抗干扰能力；
6. **标准兼容**:兼容 Grove 接口标准，接口标注清晰，便于接线调试。

### 软件功能

1. **完整 API 支持**:基于 MicroPython 实现 `OptoMosSimple` 核心类，提供电机驱动全流程控制接口；
2. **灵活占空比控制**:支持计数值/百分比两种占空比设置方式，超范围参数自动裁剪；
3. **反向输出模式**:支持占空比逻辑反向输出，适配反向控制场景；
4. **状态监控**:提供状态查询接口，实时获取占空比、PWM 参数等信息；
5. **资源管理**:支持 PWM 资源初始化与释放，避免资源占用。

## 硬件要求

1. **电源要求**:

   - 功率电源（VIN）:需与负载（如电机）额定电压匹配，输出电流满足负载需求；
   - 控制端电源:需提供稳定的 +5V 电源，保障光耦和控制逻辑正常工作；
2. **接口要求**:

   - 控制信号接口（CONTROL）:支持高/低电平或 PWM 信号输入（频率推荐 1kHz-20kHz）；
   - 接地要求:控制地（GND）与 MCU 共地，功率地（PGND）与功率回路共地，可通过 0Ω 电阻 R4 统一地电位；
3. **器件兼容**:

   - 续流二极管:驱动感性负载时必须保留 SS34 续流二极管；
   - MOS 管驱动:需保留 R1（20kΩ）上拉电阻、R2（10kΩ）限流电阻，确保 MOS 管可靠通断。

## 文件说明

| 文件名             | 说明                                                                     |
| ------------------ | ------------------------------------------------------------------------ |
| opto_mos_simple.py | 核心驱动文件，实现 `OptoMosSimple` 类，提供 PWM 控制、占空比调节等核心功能 |
| main.py            | 测试示例文件，验证模块电机驱动功能，包含各类 API 的使用演示              |

## 软件设计核心思想

核心类:`OptoMosSimple`（基于 MicroPython 实现）

### 1. 类属性

| 属性     | 类型 | 说明                                                    |
| -------- | ---- | ------------------------------------------------------- |
| pwm      | PWM  | 已初始化的 PWM 对象，用于生成 PWM 信号                  |
| pwm_max  | int  | PWM 最大计数范围（默认 65535，对应 16 位 PWM）          |
| inverted | bool | 是否反向输出占空比（默认 False，True 时占空比逻辑取反） |
| _duty    | int  | 当前占空比计数值（内部维护）                            |

### 2. 核心方法

| 方法        | 功能                                                  | 参数说明                                                                                          | 返回值                                                          |
| ----------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **init**    | 构造函数，初始化 PWM 控制对象                         | pwm: 已创建的 PWM 对象；pwm_max: PWM 最大计数（默认 65535）；inverted: 是否反向输出（默认 False） | 无                                                              |
| init        | 初始化输出，默认关闭（0% 占空比）                     | 无                                                                                                | 无                                                              |
| set_duty    | 设置占空比（计数值，范围 0..pwm_max），超范围自动裁剪 | duty: 占空比计数值                                                                                | 无                                                              |
| set_percent | 设置占空比百分比（0.0..100.0），超范围自动裁剪        | percent: 占空比百分比                                                                             | 无                                                              |
| full_on     | 置为全速（100% 占空比）                               | 无                                                                                                | 无                                                              |
| off         | 关闭输出（0% 占空比）                                 | 无                                                                                                | 无                                                              |
| get_status  | 获取当前状态字典                                      | 无                                                                                                | dict，包含 duty（计数值）、percent（百分比）、pwm_max、inverted |
| deinit      | 释放或复位 PWM 资源                                   | 无                                                                                                | 无                                                              |

## 使用说明

**PWM 初始化**:选择合适的 GPIO 口创建 PWM 对象，频率建议设置为 1kHz-20kHz（避免可听噪声）；

**驱动实例化**:基于已创建的 PWM 对象初始化 `OptoMosSimple` 驱动实例，可指定是否反向输出；

通过 `set_duty` 设置计数值占空比，或 `set_percent` 设置百分比占空比，超范围参数会自动裁剪；

通过 `full_on`/`off` 快速实现电机全速/停止；

**状态监控**:调用 `get_status` 获取当前驱动状态，便于调试和逻辑控制；

**资源释放**:使用完成后调用 `deinit` 释放 PWM 资源，避免资源占用。

## 示例程序

以下是 `main.py` 中的核心测试代码，用于验证模块的电机驱动功能:

```python
import time
from machine import Pin, PWM
from opto_mos_simple import OptoMosSimple

# 上电延时，等待模块稳定
time.sleep(3)
print("FreakStudio:  OptoMosSimple Test Start ")

# 创建 PWM 对象，GPIO6 输出，频率1kHz
pwm = PWM(Pin(6))
pwm.freq(1000)
print("PWM object created on Pin 6 with 1kHz frequency.")

# 创建驱动实例
driver = OptoMosSimple(pwm)
print("Driver object created.")

# 初始化驱动（默认关闭输出）
driver.init()
print("[init] Initialized ->", driver.get_status())

# 测试 set_duty 方法:设置占空比计数值
print("[set_duty] Set duty=10000")
driver.set_duty(10000)
print("Status:", driver.get_status())

print("[set_duty] Set duty=70000 (out of range, auto clipped)")
driver.set_duty(70000)  # 超出65535，自动裁剪为65535
print("Status:", driver.get_status())

# 测试 set_percent 方法:设置占空比百分比
print("[set_percent] Set 25% duty cycle")
driver.set_percent(25.0)
print("Status:", driver.get_status())

print("[set_percent] Set 150% duty cycle (out of range, auto clipped)")
driver.set_percent(150.0)  # 超出100%，自动裁剪为100%
print("Status:", driver.get_status())

# 测试 full_on 方法:全速输出（100%占空比）
print("[full_on] Full ON")
driver.full_on()
print("Status:", driver.get_status())
time.sleep(5)  # 保持全速5秒

# 测试 off 方法:关闭输出（0%占空比）
print("[off] Turn OFF")
driver.off()
print("Status:", driver.get_status())
time.sleep(10)  # 保持关闭10秒

# 测试 inverted 模式（反向输出，使用不同GPIO避免冲突）
print("[inverted] Testing inverted mode")
pwm_inv = PWM(Pin(16))
pwm_inv.freq(1000)
driver_inv = OptoMosSimple(pwm_inv, inverted=True)  # 反向输出
driver_inv.init()
driver_inv.set_percent(30.0)  # 实际输出70%占空比（反向）
print("Inverted 30% ->", driver_inv.get_status())
driver_inv.full_on()  # 实际输出0%占空比（反向）
print("Inverted full_on ->", driver_inv.get_status())
driver_inv.off()  # 实际输出100%占空比（反向）
print("Inverted off ->", driver_inv.get_status())

# 释放资源
print("[deinit] Release resources")
driver.deinit()
driver_inv.deinit()
print("PWM released.")

print("=== OptoMosSimple Test End ===")
```

## 注意事项

1. **电气隔离**:光耦实现了控制端与功率端的电气隔离，接线时需确保控制端（CONTROL、GND）与功率端（VIN、VOUT、PGND）的电源独立，避免共地干扰；
2. **续流保护**:驱动感性负载（如电机）时，必须保留 SS34 二极管，防止 MOS 管关断时产生的反向电动势损坏器件；
3. **PWM 频率**:PWM 频率需根据负载特性选择，电机驱动通常使用 1kHz-20kHz 的频率，避免产生 audible noise（可听噪声）；
4. **电源匹配**:VIN 输入电压需与负载（如电机）额定电压匹配，VOUT 输出电流需满足负载需求，避免过载；
5. **地连接**:R4（0Ω 电阻）用于连接 PGND 与 GND，若系统中控制地与功率地已统一，可保留该电阻；若需严格隔离，可移除该电阻，实现两地完全隔离；
6. **反向模式**:使用 `inverted=True` 时，需注意占空比逻辑取反，避免控制逻辑错误。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:

📧 **邮箱**:liqinghsui@freakstudio.cn

💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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