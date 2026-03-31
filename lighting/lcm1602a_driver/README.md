# GraftSense-Drivers-MicroPython: lcm1602a_driver

# GraftSense-Drivers-MicroPython: lcm1602a_driver

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

`lcm1602a_driver` 是一个适用于 **MicroPython** 的 LCM1602A 字符液晶显示器驱动库，支持通过 I2C 接口控制 16×2 字符 LCD 模块，方便在嵌入式开发中快速实现文本显示功能。

---

## 主要功能

- 支持 I2C 接口的 LCM1602A 16×2 字符液晶显示
- 提供基础文本显示、清屏、光标控制等核心操作
- 兼容主流 MicroPython 固件与芯片平台
- 轻量封装，易于集成到各类 MicroPython 项目中

---

## 硬件要求

- 主控板：支持 MicroPython 且带有 I2C 外设的开发板（如 ESP32、ESP8266、RP2040 等）
- 显示模块：LCM1602A 字符液晶（带 I2C 转接板）
- 连接线：用于连接主控板 I2C 引脚与液晶模块

---

## 文件说明

## 软件设计核心思想

- **轻量封装**：仅保留 LCM1602A 核心显示功能，避免冗余代码，适配 MicroPython 资源受限环境
- **硬件无关**：通过标准 I2C 接口抽象，兼容不同主控芯片与固件版本
- **易用性优先**：提供简洁 API，降低开发者使用门槛，快速实现文本显示需求
- **可扩展性**：代码结构清晰，便于后续扩展更多显示特性（如自定义字符、滚动显示等）

---

## 使用说明

1. 将 `code/LCD_I2C.py` 文件复制到 MicroPython 设备的文件系统中
2. 在你的项目代码中导入 `LCD_I2C` 类
3. 初始化 I2C 总线与 LCD 对象，调用相关 API 实现显示操作

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午5:00
# @Author  : bhavi-thiran
# @File    : main.py
# @Description : 基于I2C接口驱动LCD1602显示屏，实现显示控制、光标管理、字符输出等核心功能

# ======================================== 导入相关模块 =========================================
# 导入LCD1602显示屏I2C驱动相关的所有内容
from LCD_I2C import LCD

# 从machine模块导入I2C类（用于I2C总线配置）和Pin类（用于引脚配置）
from machine import I2C, Pin

# 导入时间模块（用于延时和程序启动等待）
import time

# ======================================== 全局变量 ============================================
# I2C SCL引脚编号
I2C_SCL_PIN = 5
# I2C SDA引脚编号
I2C_SDA_PIN = 4
# I2C通信频率（Hz）
I2C_FREQ = 400000
# LCD1602常见I2C目标地址（十进制：39=0x27，62=0x3E）
TARGET_LCD_ADDRS = [39, 62]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
# 程序启动延时3秒，确保硬件完成初始化
time.sleep(3)
# 打印功能标识，说明当前功能为通过I2C控制LCD1602显示屏
print("FreakStudio: Control LCD1602 via I2C")

# -------------------------- 关键修改点1：标准化I2C初始化格式 --------------------------
# 初始化I2C总线0，严格对齐指定风格（使用全局变量定义引脚/频率）
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# -------------------------- 关键修改点2：添加I2C设备扫描逻辑 --------------------------
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# -------------------------- 关键修改点3：遍历地址匹配目标LCD设备 --------------------------
# 遍历地址列表初始化目标LCD1602
lcd = None  # 初始化LCD对象占位符
for device in devices_list:
    if device in TARGET_LCD_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 找到目标地址，初始化LCD对象
            lcd = LCD(i2c_bus)
            print("LCD1602 initialization successful")
            break
        except Exception as e:
            print(f"LCD1602 Initialization failed: {e}")
            continue
else:
    # 遍历完所有设备未找到目标地址，抛出明确异常
    raise Exception("No LCD1602 device found in I2C bus (target addresses: 0x27/0x3E)")

# ========================================  主程序  ============================================
# 设置LCD1602光标位置为第0行第0列
lcd.set_cursor(0, 0)
# 在当前光标位置写入字符串"Hello World"
lcd.write("Hello World")
# 延时1秒，保持显示内容1秒
time.sleep(1)

# 关闭LCD1602显示屏的显示功能
lcd.off()
# 延时1秒，保持关闭状态1秒
time.sleep(1)

# 打开LCD1602显示屏的显示功能
lcd.on()
# 延时1秒，保持开启状态1秒
time.sleep(1)

# 打开LCD1602显示，关闭光标显示，开启光标闪烁效果
lcd.on(cursor=False, blink=True)
# 延时1秒，保持该显示状态1秒
time.sleep(1)

# 打开LCD1602显示，开启光标显示，关闭光标闪烁效果
lcd.on(cursor=True, blink=False)
# 延时1秒，保持该显示状态1秒
time.sleep(1)

# 打开LCD1602显示，同时开启光标显示和光标闪烁效果
lcd.on(cursor=True, blink=True)
# 延时1.5秒，保持该显示状态1.5秒
time.sleep(1.5)

# 清空LCD1602显示屏的所有显示内容
lcd.clear()

```

## 注意事项

- 请根据硬件实际连接情况调整 I2C 引脚号、总线号与 LCD I2C 地址
- 确保供电稳定，避免电压波动导致显示异常
- 清屏操作（`clear()`）会重置光标位置，如需保留显示内容请谨慎使用
- 部分 LCM1602A 模块对比度需要通过电位器手动调节

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
