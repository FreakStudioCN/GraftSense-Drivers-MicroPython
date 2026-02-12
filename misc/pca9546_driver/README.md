# GraftSense PCA9546ADR 4 路 I2C 多路选择器扩展模块（MicroPython）

# GraftSense PCA9546ADR 4 路 I2C 多路选择器扩展模块 （MicroPython）

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

本项目为 **GraftSense PCA9546ADR 4 路 I2C 多路选择器扩展模块 V1.2** 提供了完整的 MicroPython 驱动支持，基于 PCA9546ADR 芯片实现 I2C 总线通道切换与同地址设备扩展管理，最多支持 4 路独立 I2C 通道，可有效解决多传感器系统中的 I2C 地址冲突问题，适用于多传感器系统搭建、I2C 地址冲突解决实验、复杂电子 DIY 等场景。模块遵循 Grove 接口标准，内置 DC-DC 5V 转 3.3V 电路与地址选择引脚，总线隔离性好、切换灵活。

---

## 主要功能

- ✅ **4 路 I2C 通道切换**：通过 PCA9546ADR 芯片实现 4 路独立 I2C 通道的切换，每路通道可连接不同 I2C 设备，解决地址冲突
- ✅ **地址冲突解决**：支持同地址 I2C 设备在不同通道上共存，通过通道切换实现分时访问
- ✅ **总线隔离**：通道间电气隔离，避免单通道设备故障影响整个 I2C 总线
- ✅ **地址可配置**：通过 A2/A1/A0 引脚配置模块 I2C 地址（默认 0x70），支持多模块级联
- ✅ **Grove 接口兼容**：提供 5 个 Grove 接口（1 个 MCU 侧 + 4 个传感器侧），接线便捷，无需额外杜邦线
- ✅ **内置电源转换**：集成 DC-DC 5V 转 3.3V 电路，支持 5V 供电，为模块和传感器提供稳定 3.3V 电源
- ✅ **状态管理**：支持读取当前通道掩码，实时监控通道使能状态

---

## 硬件要求

1. **核心硬件**：GraftSense PCA9546ADR 4 路 I2C 多路选择器扩展模块 V1.2（内置 PCA9546ADR 芯片、电源转换电路、地址选择引脚）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等）
3. **接线方式**：

   - **MCU 侧**：模块左侧 Grove 接口（I2C）→ 主控板 I2C 引脚（SDA/SCL）
   - **传感器侧**：模块右侧 4 个 Grove 接口（I2C0~I2C3）→ 各 I2C 传感器模块
   - **地址选择**：通过模块底部 A2/A1/A0 短接点配置 I2C 地址（默认 0x70）
4. **电源**：5V 直流电源（模块内置 DC-DC 转换，输出 3.3V 为芯片和传感器供电）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **面向对象封装**：将 I2C 多路复用器的控制逻辑封装为 `PCA9546ADR` 类，每个实例对应一个模块，支持多模块独立管理
2. **参数校验容错**：对通道号（0~3）进行严格范围校验，避免无效通道导致硬件异常
3. **状态同步管理**：内部维护 `_current_mask` 记录当前通道使能状态，仅在 I2C 写入成功后更新状态，确保状态一致性
4. **异常处理机制**：I2C 读写失败时抛出 `OSError`，便于调用者捕获并处理通信异常
5. **解耦硬件依赖**：依赖 `machine.I2C` 实现通信，不绑定特定主控硬件，提升代码可移植性

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `pca9546adr.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

1. 模块左侧 Grove 接口（I2C）→ 主控板 I2C 引脚（如 Raspberry Pi Pico 的 GP2/SCL、GP3/SDA）
2. 模块右侧 Grove 接口（I2C0~I2C3）→ 各 I2C 传感器模块（如传感器 A 接 I2C0，传感器 B 接 I2C1）
3. 模块 VCC/GND → 主控板 5V/GND（模块内置 3.3V 转换，无需额外供电）
4. （可选）通过 A2/A1/A0 短接点配置模块 I2C 地址（默认 0x70）

### 代码使用步骤

#### 步骤 1：导入模块并初始化 I2C

```python
from machine import Pin, I2C
import time
from pca9546adr import PCA9546ADR

# 初始化 I2C（Raspberry Pi Pico I2C1，SCL=GP2，SDA=GP3）
i2c = I2C(1, scl=Pin(2), sda=Pin(3))
```

#### 步骤 2：创建多路复用器实例

```
# 创建 PCA9546ADR 实例，默认地址 0x70
pca = PCA9546ADR(i2c)
```

#### 步骤 3：切换通道并操作设备

```python
# 关闭所有通道，避免干扰
pca.disable_all()# 选择通道 0，操作该通道上的设备
pca.select_channel(0)print("通道 0 上的 I2C 设备：", i2c.scan())# 关闭所有通道，切换到通道 1
pca.disable_all()
pca.select_channel(1)print("通道 1 上的 I2C 设备：", i2c.scan())
```

#### 步骤 4：读取通道状态

```python
# 获取当前通道掩码（低 4 位表示通道使能状态）
current_mask = pca.current_mask()
print("当前通道掩码：", bin(current_mask))
```

---

## 示例程序

```python
# -*- coding: utf-8 -*-
from machine import Pin, I2C
import time
from pca9546adr import PCA9546ADR

# 上电延时
time.sleep(3)
print("FreakStudio: Testing PCA9546ADR4 I2C Multiplexer Modules")

# 初始化 I2C
i2c = I2C(1, scl=Pin(2), sda=Pin(3))
pca = PCA9546ADR(i2c)

# 循环切换通道并扫描设备
while True:
    # 关闭所有通道，切换到通道 0
    pca.disable_all()
    pca.select_channel(0)
    print("通道 0 设备地址：", i2c.scan())
    time.sleep(4)
    
    # 关闭所有通道，切换到通道 1
    pca.disable_all()
    pca.select_channel(1)
    print("通道 1 设备地址：", i2c.scan())
    time.sleep(4)
```

---

## 注意事项

1. **通道范围约束**：通道号必须为 0~3，超出范围会触发 `ValueError`
2. **地址配置规则**：模块 I2C 地址由 A2/A1/A0 引脚电平决定，默认 0x70，多模块级联时需确保地址不冲突
3. **通道切换前隔离**：切换通道前建议调用 `disable_all()` 关闭所有通道，避免前一通道设备干扰当前通道通信
4. **I2C 频率建议**：I2C 总线频率建议不超过 400kHz，过高频率可能导致通道切换时通信不稳定
5. **内置上拉电阻**：模块内置 I2C 上拉电阻，无需额外外接，若连接长距离线缆可适当增加上拉电阻
6. **电源隔离**：模块与传感器侧电源隔离，避免传感器侧电源波动影响模块稳定性

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