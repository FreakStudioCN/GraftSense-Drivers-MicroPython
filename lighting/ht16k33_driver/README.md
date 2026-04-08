# HT16K33 Driver for MicroPython

# HT16K33 Driver for MicroPython

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

`ht16k33_driver` 是一个用于控制 **HT16K33 芯片** 的 MicroPython 库，支持驱动 LED 矩阵和 7 段数码管等显示设备。该库为各类 MicroPython 开发板提供了轻量、高效的 LED 显示驱动能力，无芯片与固件限制，通用性极强。

## 主要功能

- 支持 HT16K33 芯片的 I2C 通信控制
- 提供 LED 矩阵（8x8）显示驱动
- 提供 7 段数码管显示驱动
- 支持亮度调节、闪烁控制
- 兼容所有 MicroPython 芯片平台与固件
- 轻量无依赖，API 简洁易用

## 硬件要求

- 搭载任意 MicroPython 固件的开发板（ESP32、ESP8266、Raspberry Pi Pico、STM32 等）
- HT16K33 驱动的 LED 矩阵模块 或 7 段数码管模块
- 开发板硬件 I2C 接口（SDA/SCL 引脚）

## 文件说明

## 软件设计核心思想

- **模块化解耦**：将 LED 矩阵驱动与数码管驱动拆分为独立文件，开发者可根据硬件需求单独引入，减少资源占用
- **无依赖设计**：不依赖任何第三方固件（如 ulab、lvgl），支持所有 MicroPython 环境运行
- **通用兼容性**：适配全系列 MicroPython 芯片，无硬件平台限制
- **极简易用**：封装标准化 API，降低硬件驱动开发门槛
- **高效稳定**：基于原生 I2C 协议实现，通信稳定、响应速度快

## 使用说明

1. 将对应驱动文件（`ht16k33_matrix.py` 或 `ht16k33_seg.py`）上传至 MicroPython 开发板文件系统
2. 在项目代码中导入对应的驱动模块
3. 初始化开发板 I2C 总线
4. 创建 HT16K33 驱动实例，绑定 I2C 对象
5. 调用库提供的方法实现显示、亮度、闪烁等控制

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 上午10:16
# @Author  : mcauser
# @File    : main.py
# @Description : 基于HT16K33驱动的4位7段数码管显示测试程序

# ======================================== 导入相关模块 =========================================

# 从machine模块导入I2C和Pin类，用于硬件I2C通信和引脚控制
from machine import I2C, Pin

# 从ht16k33_seg模块导入Seg7x4类，用于控制4位7段数码管
from ht16k33_seg import Seg7x4

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# 定义I2C相关常量（标准化配置参数）
I2C_SCL_PIN = 5  # Pico I2C0的SCL引脚号
I2C_SDA_PIN = 4  # Pico I2C0的SDA引脚号
I2C_FREQ = 400000  # I2C通信频率（400KHz）
TARGET_SENSOR_ADDR = 0x70  # HT16K33数码管的I2C目标地址（十进制112）

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动后延时3秒，确保硬件初始化完成
time.sleep(3)
# 打印功能提示信息
print("FreakStudio: HT16K33 7-segment display test")

# 初始化I2C总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")
# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))
# 遍历地址列表初始化目标数码管
seg7 = None  # 初始化数码管对象变量
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            seg7 = Seg7x4(i2c=i2c_bus)
            print("Target sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No TargetSensor found")

# ========================================  主程序  ============================================

# 基础显示测试：显示数字1234
print("Display 1234")
# 清空数码管显示缓存
seg7.fill(False)
# 设置要显示的文本为"1234"
seg7.text("1234")
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 显示带小数点的数字：显示8.888
print("Display 8.888")
# 清空数码管显示缓存
seg7.fill(False)
# 设置要显示的文本为"8.888"
seg7.text("8.888")
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 显示十六进制数：显示0xFAB
print("Display hex 0xFAB")
# 清空数码管显示缓存
seg7.fill(False)
# 设置显示十六进制数0xFAB
seg7.hex(0xFAB)
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 显示单个字符：依次在4个位置显示9、8、7、6
print("Display number 9,8,7,6")
# 清空数码管显示缓存
seg7.fill(False)
# 在第0位显示字符'9'
seg7.put("9", index=0)
# 在第1位显示字符'8'
seg7.put("8", index=1)
# 在第2位显示字符'7'
seg7.put("7", index=2)
# 在第3位显示字符'6'
seg7.put("6", index=3)
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 亮度调节测试：循环调整亮度
print("Adjust brightness")
# 循环遍历亮度值，从0到15，步长为3
for brightness in range(0, 16, 3):
    # 设置数码管亮度
    seg7.brightness(brightness)
    # 每个亮度等级保持0.5秒
    time.sleep(0.5)

# 清空显示测试
print("Clear display")
# 清空数码管显示缓存
seg7.fill(False)
# 将清空后的缓存输出到数码管，实现清屏
seg7.show()

```

## 注意事项

1. 初始化 I2C 时，引脚编号需与开发板硬件定义保持一致
2. HT16K33 芯片默认 I2C 地址为 `0x70`，若硬件修改了地址，初始化时需手动传入参数
3. 显示刷新频率不宜过高，避免造成 I2C 通信阻塞
4. 调节亮度时请遵循硬件额定参数，防止电流过大损坏模块
5. 库文件无需修改，直接上传使用即可

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
**MIT License**
Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copyof this software and associated documentation files (the "Software"), to dealin the Software without restriction, including without limitation the rightsto use, copy, modify, merge, publish, distribute, sublicense, and/or sellcopies of the Software, and to permit persons to whom the Software isfurnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in allcopies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS ORIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THEAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHERLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THESOFTWARE.
```
