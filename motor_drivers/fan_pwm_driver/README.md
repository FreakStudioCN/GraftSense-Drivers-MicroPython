# GraftSense 散热风扇模块（MicroPython）

# GraftSense 散热风扇模块（MicroPython）

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

本项目为 **GraftSense 散热风扇模块 V1.0** 提供了完整的 MicroPython 驱动支持，基于 MOS 管（AO3400）实现 PWM 驱动散热风扇，支持全速运行、关闭、多档转速调节，适用于电子 DIY、创客实验、自动温控演示等场景。模块采用独立 5V 供电接口，内置二极管保护电路，避免风扇反向电动势损坏器件，遵循 Grove 接口标准，接线便捷、驱动高效。

---

## 主要功能

- ✅ **PWM 转速控制**：通过 PWM 输出不同占空比信号，调节 MOS 管导通时间，实现风扇转速精准控制（占空比 0–1023）
- ✅ **高效 MOS 驱动**：采用 AO3400 MOS 管，栅极耐压 30V、连续漏极电流 5.8A，满足风扇 5V/0.12A 工作需求
- ✅ **开关与调速接口**：提供 `on()`（全速）、`off()`（关闭）、`set_speed()`（自定义占空比）高层 API，简化控制逻辑
- ✅ **独立供电设计**：POWER 接口支持外部 +5V 直流电源，避免与 MCU 共用电产生干扰，保障风扇稳定运行
- ✅ **内置保护电路**：1N4148W 二极管用于续流，抑制风扇反向电动势，保护 MOS 管
- ✅ **Grove 接口兼容**：支持 Grove 4Pin 线直接连接，也可通过杜邦线适配其他开发板
- ✅ **底层对象访问**：通过 `digital` 和 `pwm` 属性，可直接操作引脚和 PWM 对象，兼顾易用性与灵活性

---

## 硬件要求

1. **核心硬件**：GraftSense 散热风扇模块 V1.0（内置 MOS 管、保护二极管、电源滤波电路）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等）
3. **接线方式**：

   - **DOUT**：模块数字输出端 → MCU PWM 引脚（如 Raspberry Pi Pico 的 GP6）
   - **VCC/GND**：模块电源端 → MCU 3.3V/GND（为模块供电）
   - **FANINF**：XH2.54 接口 → 散热风扇（为风扇供电并传输控制信号）
   - **POWER**：外部 +5V 直流电源接口 → 独立 5V 电源（避免与 MCU 共电干扰）
4. **电源**：外部 +5V 直流电源（推荐 1A 以上输出，保障风扇稳定运行）

---

## 文件说明

---

## 软件设计核心思想

1. **面向对象封装**：将 PWM 控制、引脚管理、转速调节封装为 `FanPWM` 类，每个风扇对应一个实例，支持多风扇独立控制
2. **参数校验容错**：对占空比（0–1023）、PWM 频率等输入参数进行范围校验，避免无效值导致硬件异常
3. **分离硬件操作与业务逻辑**：提供 `on()`/`off()`/`set_speed()` 等高层 API，隐藏 PWM 底层细节，降低开发门槛
4. **属性访问设计**：通过 `digital` 和 `pwm` 属性暴露底层引脚和 PWM 对象，支持高级操作（如直接修改占空比、停止 PWM）
5. **资源安全管理**：初始化时自动配置 PWM 频率和占空比，避免未初始化导致的硬件误操作

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `fan_pwm.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

1. 模块 `DOUT` → MCU PWM 引脚（如 Raspberry Pi Pico 的 GP6）
2. 模块 `VCC` → MCU 3.3V，`GND` → MCU GND
3. 模块 `FANINF` → 散热风扇（XH2.54 接口）
4. 模块 `POWER` → 外部 +5V 直流电源

### 代码使用步骤

#### 步骤 1：导入库

```
from fan_pwm import FanPWM
import time
```

#### 步骤 2：创建 `FanPWM` 实例

```
# 初始化风扇控制：DOUT 接 GP6，PWM 频率默认 25kHz
fan = FanPWM(pin=6)
```

#### 步骤 3：控制风扇

```
# 获取当前占空比
print("当前占空比:", fan.get_speed())

# 获取引脚对象（直接操作引脚）
pin_obj = fan.digital

# 获取 PWM 对象（直接操作 PWM）
pwm_obj = fan.pwm
```

#### 步骤 4：获取状态与底层对象

```
# 获取当前占空比print("当前占空比:", fan.get_speed())# 获取引脚对象（直接操作引脚）
pin_obj = fan.digital

# 获取 PWM 对象（直接操作 PWM）
pwm_obj = fan.pwm
```

---

## 示例程序

```
# -*- coding: utf-8 -*-
import time
from fan_pwm import FanPWM

# 上电延时
time.sleep(3)
print("FreakStudio:Testing PWM cooling fans")

# 创建风扇实例
fan = FanPWM(pin=6)

try:
    print("\n[Step 1] Turning fan ON (full speed)...")
    fan.on()
    print(f"Current duty: {fan.get_speed()}")
    time.sleep(5)

    print("\n[Step 2] Turning fan OFF...")
    fan.off()
    print(f"Current duty: {fan.get_speed()}")
    time.sleep(5)

    # 测试不同占空比
    for duty in [256, 512, 768, 1023]:
        print(f"\n[Step] Setting fan duty to {duty}...")
        fan.set_speed(duty)
        print(f"Current duty: {fan.get_speed()}")
        time.sleep(5)

    print("\n[Step 3] Testing digital property (Pin object)...")
    pin_obj = fan.digital
    print(f"Pin object: {pin_obj}")
    time.sleep(5)

    print("\n[Step 4] Testing pwm property (PWM object)...")
    pwm_obj = fan.pwm
    print(f"PWM object: {pwm_obj}")
    time.sleep(5)

except KeyboardInterrupt:
    print("\nTest interrupted by user.")

finally:
    print("\n[Cleanup] Turning fan OFF...")
    fan.off()
    print("Test complete.")
```

---

## 注意事项

1. **PWM 频率限制**：默认 PWM 频率为 25kHz，低频（<10kHz）会导致风扇产生可闻噪音，建议保持默认频率
2. **占空比范围**：占空比需设置为 0–1023，`duty=0` 表示关闭风扇，`duty=1023` 表示全速运行
3. **独立供电要求**：必须通过 `POWER` 接口连接外部 +5V 电源，避免与 MCU 共电导致电压波动，影响风扇稳定性
4. **风扇接口规范**：`FANINF` 接口为 XH2.54 规格，确保风扇接线正确，避免正负极接反
5. **中断安全限制**：不要在中断服务程序（ISR）中直接调用 `set_speed()`、`on()`、`off()` 等操作 PWM 的方法，避免阻塞中断
6. **保护电路依赖**：模块内置 1N4148W 二极管，用于抑制风扇反向电动势，请勿移除或替换该器件
7. **硬件兼容性**：确保开发板 PWM 引脚支持 25kHz 频率输出，部分低端 MCU 可能存在频率限制

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