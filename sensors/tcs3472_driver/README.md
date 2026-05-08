# TCS3472 颜色传感器驱动 - MicroPython版本

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

TCS3472 是一款高精度 RGBC（红、绿、蓝、清晰）颜色传感器，通过 I2C 接口与主控通信。本驱动库封装了传感器的初始化、原始数据读取、归一化 RGB 输出、亮度计算及数据有效性检查等功能，适用于颜色识别、环境光检测等嵌入式应用场景。

## 主要功能

- 支持 I2C/SoftI2C 接口，兼容 MicroPython 标准 I2C 对象
- 读取原始 4 通道数据（Clear、Red、Green、Blue）
- 输出归一化 RGB 值（0.0~1.0）及 0~255 范围 RGB 分量
- 环境光亮度读取与亮度等级计算
- 数据有效性检查（状态寄存器 bit0）
- 内置颜色识别示例（黑/白/红/绿/蓝/黄）
- 完整参数校验，异常信息清晰

## 硬件要求

**推荐测试硬件：** Raspberry Pi Pico / Pico W（RP2040）

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（GPIO5） |
| SDA  | I2C 数据线（GPIO4） |

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `struct`（内置） |

## 文件结构

```
tcs3472_driver/
├── code/
│   ├── tcs3472.py   # 核心驱动
│   └── main.py      # 测试示例
├── package.json     # 包配置文件
├── README.md        # 说明文档
└── LICENSE          # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `tcs3472.py` | TCS3472 颜色传感器核心驱动，封装初始化、数据读取、RGB 输出、亮度计算等功能 |
| `main.py` | 测试示例，演示 I2C 扫描、传感器初始化、颜色识别主循环 |
| `package.json` | MicroPython 包管理配置文件 |
| `README.md` | 本说明文档 |
| `LICENSE` | MIT 开源许可证 |

## 快速开始

### 步骤一：复制文件

将 `tcs3472.py` 复制到 MicroPython 设备根目录或项目目录。

### 步骤二：接线

| 传感器引脚 | Pico 引脚 |
|-----------|-----------|
| VCC | 3V3 |
| GND | GND |
| SDA | GP4 |
| SCL | GP5 |

### 步骤三：运行示例

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午6:30
# @Author  : hogeiha
# @File    : main.py
# @Description : TCS3472颜色传感器驱动与测试

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
import tcs3472
import time

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x29]          

# I2C引脚和频率配置
I2C_SDA_PIN = 4  
I2C_SCL_PIN = 5   
I2C_FREQ = 400000


# ======================================== 功能函数 ============================================

def recognize_color(r, g, b):
    # 判断黑色（亮度极低）
    if r < 30 and g < 30 and b < 30:
        return "Black"
    # 判断白色（RGB全高且均衡）
    elif r > 110 and g > 110 and b > 110:
        return "White"
    # 判断红色：R最大且R>110
    elif r > 110 and r > g and r > b:
        return "Red"
    # 判断绿色：G最大且G>110
    elif g > 110 and g > r and g > b:
        return "Green"
    # 判断蓝色：B最大且B>110
    elif b > 110 and b > r and b > g:
        return "Blue"
    # 判断黄色：R和G都高
    elif r > 110 and g > 110 and b < 90:
        return "Yellow"
    # 其他颜色
    else:
        return "Unknown"

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: TCS3472 color sensor test")

# ========================================  主程序  ============================================

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = tcs3472.tcs3472(i2c_bus, device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 主循环
print("TCS3472 color sensor initialized successfully!")
while True:
    # 检查传感器数据是否有效
    if sensor.valid():
        # 获取环境光亮度
        light_val = sensor.light()
        # 获取RGB值(0-255)
        r, g, b = sensor.rgb()
        # 识别颜色名称
        color_name = recognize_color(r, g, b)
        
        # 打印结果
        print(f"Light: {light_val:>4} | RGB: ({r:3}, {g:3}, {b:3}) | Color: {color_name}")
    else:
        print("Sensor data invalid!")
    
    # 延时500ms，避免刷屏过快
    time.sleep(0.5)
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 传感器供电为 3.3V，请勿接 5V |
| I2C 地址 | 固定为 0x29，不可更改 |
| 数据有效性 | 每次读取前建议调用 `valid()` 确认数据就绪 |
| 积分时间 | 初始化写入 0x2b，积分时间约 154ms，影响采样速率 |
| 增益设置 | 配置寄存器 0x81 同时控制增益，默认 1x |
| 颜色识别阈值 | `recognize_color()` 中的阈值（30/110/90）针对特定光照条件，实际使用需根据环境调整 |
| MicroPython 版本 | 建议使用 v1.23.0 及以上 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-04-21 | tti0 | 初始版本，实现 RGBC 读取、归一化输出、亮度计算、数据有效性检查 |

## 联系方式

- 邮箱：请联系驱动作者 tti0
- GitHub：https://github.com/tti0/tcs3472-micropython

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
