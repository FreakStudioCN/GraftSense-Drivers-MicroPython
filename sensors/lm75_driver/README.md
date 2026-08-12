# LM75 I2C 数字温度传感器 MicroPython 驱动

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

本驱动为 LM75 I2C 数字温度传感器提供 MicroPython 支持。LM75 是一款 9-bit 分辨率的 I2C 温度传感器，测温精度为 0.5°C，广泛应用于嵌入式温度监控、环境数据采集和物联网终端设备。

驱动采用依赖注入设计，I2C 总线实例由外部传入，不占用特定引脚资源，可灵活适配 ESP32、ESP8266、RP2040 等多种 MicroPython 平台。

## 主要功能

- **温度采集**：支持原始两字节数据读取和格式化温度值输出
- **多地址支持**：通过地址引脚配置，支持 0x48~0x4F 共 8 个 I2C 地址
- **依赖注入**：I2C 总线实例由外部传入，引脚配置灵活，不受固定引脚约束
- **Debug 日志**：内置 debug 开关，方便开发调试
- **资源管理**：提供 `deinit()` 方法释放驱动资源
- **异常处理**：I2C 通信异常包装为 `RuntimeError`，参数校验异常为 `ValueError`

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| LM75 模块 | I2C 数字温度传感器（0x48 默认地址） |
| ESP32 开发板 | 或其他支持 MicroPython I2C 的开发板 |
| 杜邦线 | 4 根（VCC、GND、SCL、SDA） |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.8V-5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（ESP32: GPIO22） |
| SDA  | I2C 数据线（ESP32: GPIO21） |
| OS  | 过热关断输出（开漏，可选） |
| A0~A2 | I2C 地址选择引脚 |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无额外依赖（仅使用内置 `machine` 模块） |

## 文件结构

```
lm75_driver/
├── lm75.py        # LM75 核心驱动
├── main.py        # 测试示例
├── package.json   # mip 包配置文件
├── wiring.png     # 接线图
└── README.md      # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `lm75.py` | LM75 传感器核心驱动类，提供温度读取和资源管理功能 |
| `main.py` | 完整测试程序，包含 I2C 扫描、设备验证、定时温度采集、边界/异常参数测试 |
| `package.json` | 符合 mip 规范的包配置文件，支持 `mip install` 安装 |
| `wiring.png` | LM75 与开发板的接线示意图 |
| `README.md` | 本说明文档 |

## 快速开始

### 1. 接线

按如下方式连接 LM75 与开发板（以 ESP32 为例）：

| LM75 引脚 | ESP32 引脚 |
|-----------|------------|
| VCC       | 3.3V       |
| GND       | GND        |
| SCL       | GPIO22     |
| SDA       | GPIO21     |

### 2. 复制文件

将 `lm75.py` 上传到 MicroPython 设备的 `/lib/` 目录或项目根目录。

### 3. 运行测试

```python
from machine import Pin, I2C
from lm75 import LM75

# 创建 I2C 总线实例
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# 扫描 I2C 设备确认 LM75 存在
devices = i2c.scan()
print("Devices:", [hex(d) for d in devices])

# 实例化传感器并读取温度
sensor = LM75(i2c, addr=0x48)
temp_c, point = sensor.get_temp()
print("Temperature: %d.%d C" % (temp_c, point))
sensor.deinit()
```

### 完整测试程序

将以下代码保存为 `main.py` 直接运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : OldhamMade
# @File    : main.py
# @Description : 测试 LM75 驱动类
# @License : MIT

from machine import Pin, I2C
from lm75 import LM75
import time

# ======================================== 导入相关模块 =========================================
# ======================================== 全局变量 ============================================

# LM75 默认 I2C 地址
LM75_DEFAULT_ADDR = 0x48

# LM75 无芯片 ID 寄存器（纯温度传感器，通过读写验证设备存在）

# 打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000

# 上次打印时间戳
last_print_time = 0

# ======================================== 功能函数 ============================================


def test_boundary_params():
    """
    测试边界参数（可 REPL 手动调用）
    测试不同 I2C 地址和 debug 模式
    """
    print("--- Boundary Parameter Test ---")
    # 测试最高有效地址（LM75 地址引脚 A2/A1/A0 可配置 0x48~0x4F）
    try:
        sensor_high_addr = LM75(i2c, addr=0x4F, debug=True)
        temp_c, point = sensor_high_addr.get_temp()
        print("Addr 0x4F result: %d.%d C" % (temp_c, point))
        sensor_high_addr.deinit()
    except Exception as e:
        print("Addr 0x4F test skipped: %s" % str(e))

    # 测试最低有效地址
    try:
        sensor_low_addr = LM75(i2c, addr=0x48, debug=True)
        temp_c, point = sensor_low_addr.get_temp()
        print("Addr 0x48 result: %d.%d C" % (temp_c, point))
        sensor_low_addr.deinit()
    except Exception as e:
        print("Addr 0x48 test skipped: %s" % str(e))

    print("--- Boundary test done ---")


def test_exception_params():
    """
    测试异常参数（可 REPL 手动调用）
    验证非法参数是否正确抛出异常
    """
    print("--- Exception Parameter Test ---")

    # 测试无效 I2C 实例（非 I2C 对象）
    try:
        LM75("not_i2c")
    except ValueError as e:
        print("Invalid I2C caught: %s" % str(e))

    # 测试地址超出范围（>127）
    try:
        LM75(i2c, addr=128)
    except ValueError as e:
        print("Addr >127 caught: %s" % str(e))

    # 测试负地址
    try:
        LM75(i2c, addr=-1)
    except ValueError as e:
        print("Negative addr caught: %s" % str(e))

    # 测试地址类型错误
    try:
        LM75(i2c, addr="0x48")
    except ValueError as e:
        print("Wrong addr type caught: %s" % str(e))

    print("--- Exception test done ---")


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================

# 等待硬件稳定
time.sleep(3)

print("FreakStudio: Testing LM75 I2C Temperature Sensor Driver")

# 创建 I2C 总线实例
# ESP32 默认引脚: SCL=GPIO22, SDA=GPIO21
# ESP8266 默认引脚: SCL=GPIO5(D1), SDA=GPIO4(D2)
SCL_PIN = 22
SDA_PIN = 21
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found I2C devices: %s" % [hex(d) for d in devices])

# 检查 LM75 是否在预期地址
if LM75_DEFAULT_ADDR not in devices:
    raise RuntimeError(
        "LM75 not found at expected address 0x%02X" % LM75_DEFAULT_ADDR
    )

# LM75 无芯片 ID 寄存器，通过读取验证设备响应
print("Verifying LM75 at address 0x%02X..." % LM75_DEFAULT_ADDR)
try:
    # 尝试读取 2 字节确认设备响应
    verify_buf = bytearray(2)
    i2c.readfrom_into(LM75_DEFAULT_ADDR, verify_buf)
    print("LM75 device found and responding")
except OSError as e:
    raise RuntimeError("LM75 device not responding") from e

# 实例化 LM75 驱动（正常参数场景：默认地址，debug 关闭）
sensor = LM75(i2c, addr=LM75_DEFAULT_ADDR, debug=False)

# 记录初始时间戳
last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 低频核心 API：定时自动执行温度采集
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            # 读取温度值（核心 API）
            temp_c, point = sensor.get_temp()
            print("Temperature: %d.%d C" % (temp_c, point))

            # 读取原始数据（调试用）
            msb, lsb = sensor.get_output()
            print("  Raw: MSB=0x%02X LSB=0x%02X" % (msb, lsb))

            last_print_time = current_time

        # 边界参数测试（注释自动执行，可 REPL 手动调用）
        # test_boundary_params()

        # 异常参数测试（注释自动执行，可 REPL 手动调用）
        # test_exception_params()

        # 主循环延时
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
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
| 工作电压 | 2.8V ~ 5.5V，推荐 3.3V |
| 测温范围 | -55°C ~ +125°C |
| 测温精度 | ±2°C（-25°C ~ +100°C），±3°C（全量程） |
| 分辨率 | 9-bit（0.5°C 步进） |
| I2C 地址 | 默认 0x48，通过 A0/A1/A2 引脚配置（0x48 ~ 0x4F） |
| I2C 频率 | 最高 400kHz（Fast Mode），推荐 100kHz |
| 转换时间 | 约 300ms（典型值） |
| 兼容性 | 不兼容 LM75A（寄存器布局不同），本驱动仅适用于 LM75 |
| 依赖注入 | 类内不创建 I2C 总线，必须由外部传入 I2C 实例 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-24 | OldhamMade | 初始版本：支持 I2C 温度读取和资源管理 |

## 联系方式

- GitHub: [OldhamMade/LM75-MicroPython](https://github.com/OldhamMade/LM75-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 OldhamMade

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
