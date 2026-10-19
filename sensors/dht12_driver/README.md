# DHT12 温湿度传感器 MicroPython 驱动

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

本驱动用于在 MicroPython 平台通过 I2C 总线驱动 Aosong DHT12 数字温湿度传感器。DHT12 内置电容式湿度传感元件和 NTC 温度传感元件，通过 I2C 接口输出已校准的数字信号，适用于环境监测、智能家居、气象站等场景。

## 主要功能

- 通过 I2C 总线读取温度和相对湿度
- 内置数据校验（校验和验证）确保数据完整性
- 支持负温度测量（-20℃ ~ +60℃）
- 简洁 API：只需 `measure()` → `temperature()` / `humidity()` 三步获取数据
- 符合 GraftSense MicroPython 驱动编写规范，完善的类型注解和 docstring

## 硬件要求

**推荐测试硬件：**

- Raspberry Pi Pico / Pico W（RP2040）
- DHT12 温湿度传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VIN  | 电源正极（2.4V ~ 5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（RP2040: GP5） |
| SDA  | I2C 数据线（RP2040: GP4） |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0+ |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`（内置） |

## 文件结构

```
dht12_driver/
├── code/
│   ├── dht12.py      # DHT12 核心驱动
│   └── main.py       # RP2040 测试示例（GP5/GP4）
├── package.json      # mip 包配置
├── README.md         # 说明文档
└── LICENSE           # MIT 许可证
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `code/dht12.py` | DHT12 温湿度传感器 I2C 驱动类，提供 `check()`、`measure()`、`temperature()`、`humidity()`、`deinit()` 方法 |
| `code/main.py` | 测试程序：使用 RP2040 I2C0（SCL=GP5，SDA=GP4），自动扫描总线、验证设备在线、每 2 秒采集温湿度并打印；异常参数测试可通过 REPL 手动触发 |
| `package.json` | 驱动包元数据，用于 mip/upypi 安装 |
| `README.md` | 使用说明文档 |
| `LICENSE` | MIT 许可证 |

## 快速开始

**1. 接线：**

| DHT12 | Raspberry Pi Pico（RP2040） |
|-------|-----------------------------|
| VIN   | 3V3                          |
| GND   | GND                          |
| SCL   | GP5                         |
| SDA   | GP4                         |

**2. 上传文件：**

将 `code/dht12.py` 和 `code/main.py` 上传至 MicroPython 设备根目录。

**3. 运行测试：**

复位设备自动运行，或在 REPL 中执行：

```python
from machine import I2C, Pin
from dht12 import DHT12

i2c = I2C(0, scl=Pin(5), sda=Pin(4))
sensor = DHT12(i2c)

sensor.measure()
print("Temperature: %.1f C" % sensor.temperature())
print("Humidity: %.1f %%" % sensor.humidity())
```

**4. 完整测试代码（main.py）：**

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31
# @Author  : Mike Causer
# @File    : main.py
# @Description : 测试 DHT12 温湿度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from dht12 import DHT12

# ======================================== 全局变量 ============================================

# DHT12 固定 I2C 地址
DHT12_I2C_ADDR = 0x5C
# 打印间隔（ms）
PRINT_INTERVAL_MS = 2000
# 上次打印时间戳
_last_print_time = 0

# ======================================== 功能函数 ============================================


def scan_i2c_devices(i2c):
    """
    扫描 I2C 总线，返回设备地址列表
    """
    scan = i2c.scan
    return scan()


def find_dht12(i2c, expected_addr):
    """
    在 I2C 总线上查找 DHT12 传感器

    Args:
        i2c (I2C): I2C 总线实例
        expected_addr (int): 期望的传感器 I2C 地址

    Returns:
        bool: 找到传感器返回 True

    Raises:
        RuntimeError: 未在期望地址找到设备
    """
    device_found = False
    # 遍历扫描结果，打印设备地址并查找目标地址
    for addr in scan_i2c_devices(i2c):
        device_found = True
        print("I2C device found at 0x%02X" % addr)
        if addr == expected_addr:
            print("DHT12 found at 0x%02X" % addr)
            return True
    if device_found is False:
        raise RuntimeError("No I2C device found on the bus")
    raise RuntimeError("DHT12 not found at expected address 0x%02X" % expected_addr)


def test_invalid_params(i2c):
    """
    测试异常参数场景（边界/错误参数，注释默认执行，可 REPL 手动调用）

    覆盖场景：
    1. i2c=None → 预期 ValueError
    2. addr 超出 0x00~0x7F 范围 → 预期 ValueError
    3. addr 类型错误 → 预期 ValueError
    """
    print("=== Testing invalid parameters ===")

    # 场景 1：i2c=None
    try:
        DHT12(None)
    except ValueError as e:
        print("  [PASS] i2c=None raised ValueError: %s" % e)

    # 场景 2：addr 超出范围
    try:
        DHT12(i2c, addr=0x80)
    except ValueError as e:
        print("  [PASS] addr=0x80 raised ValueError: %s" % e)

    # 场景 3：addr 类型错误
    try:
        DHT12(i2c, addr="0x5C")
    except ValueError as e:
        print("  [PASS] addr='0x5C' raised ValueError: %s" % e)

    print("=== Parameter tests completed ===")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 等待 3 秒，确保硬件上电稳定
time.sleep(3)

print("FreakStudio: Testing DHT12 temperature and humidity sensor driver")

# 初始化 RP2040 的 I2C0 总线
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 扫描 I2C 总线并验证 DHT12 存在
find_dht12(i2c, DHT12_I2C_ADDR)

# 实例化传感器驱动
sensor = DHT12(i2c)
print("DHT12 driver initialized successfully")

# ========================================  主程序  ===========================================

try:
    # 边界参数场景：使用自定义地址实例化（与默认地址相同，验证参数传递正常）
    # sensor_custom = dht12.DHT12(i2c, addr=0x5C)  # 可 REPL 手动测试

    # 首次 sensor.check() 验证设备在线
    sensor.check()
    print("Sensor check passed")

    # 主循环：定期采集温湿度数据
    while True:
        current_time = time.ticks_ms()

        if time.ticks_diff(current_time, _last_print_time) >= PRINT_INTERVAL_MS:
            # 低频核心 API：保留自动执行
            sensor.measure()
            print("Temperature: %.1f C" % sensor.temperature())
            print("Humidity: %.1f %%" % sensor.humidity())
            _last_print_time = current_time

        # test_invalid_params(i2c)  # 异常参数测试，注释默认执行，可 REPL 手动调用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % e)
except Exception as e:
    print("Unknown error: %s" % e)
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| I2C 地址 | 固定地址 `0x5C`，不可更改 |
| 工作电压 | 2.4V ~ 5.5V，推荐 3.3V |
| 温度范围 | -20℃ ~ +60℃，精度 ±0.5℃ |
| 湿度范围 | 20% ~ 95% RH，精度 ±5% RH |
| 使用限制 | 必须先调用 `measure()` 再读取 `temperature()` / `humidity()` |
| 测量间隔 | DHT12 数据手册采样周期要求 ≥ 2 秒；当前示例设置为 2 秒（2000 ms） |
| 校验机制 | 驱动自动验证校验和，失败时抛出 `ValueError` |
| 依赖注入 | I2C 总线实例必须外部创建后传入，驱动内部不创建总线 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-31 | Mike Causer | 按 GraftSense 规范重构：添加完整 docstring、参数校验、类型注解、deinit()、分区标注 |

## 联系方式

- GitHub: [mcauser/micropython-dht12](https://github.com/mcauser/micropython-dht12)

## 许可协议

```text
MIT License

Copyright (c) 2016 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
