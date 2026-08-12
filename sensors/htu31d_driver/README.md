# HTU31D 温湿度传感器 MicroPython 驱动

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

HTU31D 是 TE Connectivity 推出的高精度数字温湿度传感器，采用 I2C 通信接口。本驱动提供完整的 MicroPython 支持，封装了温度/湿度同步采集、加热器控制、分辨率配置、CRC-8 数据完整性校验等全部核心功能，适用于气象站、环境监测、工业控制、智能家居等场景。

## 主要功能

- 支持温度（-40~125°C）和相对湿度（0~100%RH）同步采集
- 支持 4 级可调分辨率：温度和湿度各 4 档
- 支持板载加热器开关控制（用于结露/去湿场景）
- 内置 CRC-8 数据完整性校验，确保通信可靠
- 支持 `with` 语句上下文管理器，自动释放资源
- 提供 debug 日志开关，便于调试
- 依赖注入设计：I2C 总线实例由外部传入，无硬件耦合
- `__slots__` 内存优化，适合资源受限的 MicroPython 环境

## 硬件要求

| 推荐硬件 | 说明 |
|----------|------|
| ESP32 / ESP32-S3 | 推荐测试平台 |
| Raspberry Pi Pico (RP2040) | 兼容 |
| HTU31D 传感器模块 | TE Connectivity |

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V-5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

> 示例接线（ESP32）：SCL → GPIO22，SDA → GPIO21。可根据实际硬件修改引脚号。

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖（仅标准库 `time`、`struct`、`micropython`） |

## 文件结构

```
htu31d_driver/
├── code/
│   ├── htu31d.py        # 核心驱动
│   └── main.py          # 测试示例
├── package.json         # 包配置
├── README.md            # 说明文档
└── LICENSE              # 许可协议
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `htu31d.py` | HTU31D 传感器核心驱动，包含完整类实现（命令常量、初始化、公共 API、分辨率配置、CRC-8 校验等） |
| `main.py` | 测试示例代码，演示 I2C 总线扫描、传感器初始化、温湿度定时采集、异常处理等完整流程 |

## 快速开始

### 1. 复制文件

将 `htu31d.py` 和 `main.py` 上传到 MicroPython 设备的 `/lib/` 或根目录。

### 2. 硬件接线

按 [硬件要求](#硬件要求) 中的引脚说明连接 HTU31D 传感器模块。

### 3. 运行测试

将以下代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 HTU31D 温湿度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C
from micropython_htu31d import htu31d

# ======================================== 全局变量 ============================================

# HTU31D I2C 地址（参见数据手册）
_I2C_ADDRESS = 0x40

# 定时打印参数
last_print_time = time.ticks_ms()
print_interval = 2000  # 打印间隔（ms）

# ======================================== 功能函数 ============================================

def scan_i2c_bus(i2c: I2C):
    """扫描 I2C 总线，验证 HTU31D 设备存在"""
    print("Scanning I2C bus...")
    devices = i2c.scan()
    # 检查总线是否扫描到任何设备
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    # 格式化输出扫描到的所有设备地址
    print("Found devices: %s" % str([hex(d) for d in devices]))
    # 验证目标地址是否存在
    found = _I2C_ADDRESS in devices
    if not found:
        raise RuntimeError("Device not found at expected address 0x%02X" % _I2C_ADDRESS)
    print("HTU31D detected at 0x%02X" % _I2C_ADDRESS)
    return found


def toggle_heater(sensor: htu31d.HTU31D):
    """切换加热器开关模式（模式切换，默认注释调用，可 REPL 手动触发）"""
    current = sensor.heater
    sensor.heater = not current
    print("Heater switched: %s -> %s" % (current, sensor.heater))


def test_resolutions(sensor: htu31d.HTU31D):
    """测试所有分辨率组合（模式切换，默认注释调用，可 REPL 手动触发）"""
    # 遍历温度分辨率选项
    for temp_res in ("0.040", "0.025", "0.016", "0.012"):
        sensor.temp_resolution = temp_res
        # 遍历湿度分辨率选项
        for hum_res in ("0.020%", "0.014%", "0.010%", "0.007%"):
            sensor.humidity_resolution = hum_res
            temp, hum = sensor.measurements
            print("T_res=%-5s H_res=%-6s  Temp=%-6.2fC  Hum=%-5.2f%%" %
                  (temp_res, hum_res, temp, hum))
            time.sleep(0.1)


def test_boundary_params(sensor: htu31d.HTU31D):
    """测试边界和异常参数（边界/异常参数场景，默认注释调用，可 REPL 手动触发）"""
    print("--- Boundary param tests ---")

    # 测试非法 heater 参数
    print("Test: heater = 1 (should raise ValueError)...")
    try:
        sensor.heater = 1
    except ValueError as e:
        print("  ValueError caught: %s" % str(e))

    # 测试非法温度分辨率
    print("Test: temp_resolution = 'invalid' (should raise ValueError)...")
    try:
        sensor.temp_resolution = "invalid"
    except ValueError as e:
        print("  ValueError caught: %s" % str(e))

    # 测试非法湿度分辨率
    print("Test: humidity_resolution = '0.050%' (should raise ValueError)...")
    try:
        sensor.humidity_resolution = "0.050%"
    except ValueError as e:
        print("  ValueError caught: %s" % str(e))

    print("--- Boundary tests done ---")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电等待（确保传感器供电稳定）
time.sleep(3)
print("FreakStudio: HTU31D temperature and humidity sensor driver test")

# 初始化 I2C 总线（ESP32: I2C(1, scl=Pin(22), sda=Pin(21))
# 根据实际硬件接线修改引脚编号）
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)

# I2C 总线扫描与设备存在性验证
scan_i2c_bus(i2c)

# 实例化传感器驱动（默认地址 0x40，开启 debug 日志）
sensor = htu31d.HTU31D(i2c, address=_I2C_ADDRESS, debug=False)

# 读取并打印传感器序列号
serial = sensor.serial_number
print("Serial number: %s" % str(serial[0]))

# 打印初始分辨率配置
print("Humidity resolution: %s" % sensor.humidity_resolution)
print("Temperature resolution: %s" % sensor.temp_resolution)

# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 定时打印温湿度数据（低频核心 API，自动执行）
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            temp, hum = sensor.measurements
            print("Temperature: %.2f C  |  Humidity: %.2f %%RH" % (temp, hum))
            last_print_time = current_time

        # toggle_heater(sensor)       # 模式切换，注释默认执行，可 REPL 手动触发
        # test_resolutions(sensor)    # 分辨率遍历测试，注释默认执行，可 REPL 手动触发
        # test_boundary_params(sensor) # 边界和异常参数测试，注释默认执行，可 REPL 手动触发

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except RuntimeError as e:
    print("Runtime error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 3.3V ~ 5V（推荐 3.3V，与多数 MCU 逻辑电平兼容） |
| 温度范围 | -40°C ~ 125°C |
| 湿度范围 | 0% ~ 100%RH（非冷凝环境） |
| I2C 地址 | 默认 0x40（HTU31D 地址固定，不可修改） |
| 转换时间 | 单次测量约 20~30ms（取决于分辨率配置） |
| 加热器 | 连续使用时功耗较高，建议仅在结露场景临时开启 |
| 分辨率 | 温度和湿度各 4 档独立可调，高分辨率对应更长转换时间 |
| CRC 校验 | 每次 `measurements` 调用自动执行 CRC-8 校验，校验失败抛出 RuntimeError |
| 复位 | 初始化时自动软复位，也可手动调用 `reset()` |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-25 | Jose D. Montoya | 初始版本，完成 GraftSense 规范化：中英双语 docstring、6 分区结构、I2C OSError 包装、CRC 抽离、`__slots__` 内存优化、上下文管理器 |

## 联系方式

- 作者：Jose D. Montoya
- GitHub：[https://github.com/jposada202020/MicroPython_HTU31D](https://github.com/jposada202020/MicroPython_HTU31D)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

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
