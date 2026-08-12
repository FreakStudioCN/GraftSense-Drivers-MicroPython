# BME680 温度/湿度/气压/气体传感器 MicroPython 驱动

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

BME680 是 Bosch Sensortec 推出的四合一 MEMS 环境传感器，集成温度、湿度、气压和气体（VOC/IAQ）检测功能。本驱动提供 MicroPython 下的 BME680 完整驱动支持，兼容 I2C 和 SPI 两种通信接口，通过统一的 `BME680_I2C` / `BME680_SPI` 类对外暴露简洁的 property 式 API，无需关心底层寄存器操作即可快速读取四类环境数据。

## 主要功能

- 温度、湿度、气压、气体电阻四合一同步读取
- 支持 I2C 和 SPI 双通信接口，按需选择
- Property 式 API 设计，读取 `temperature` / `pressure` / `humidity` / `gas` / `altitude` 即可获取补偿后的工程值
- 可配置的过采样率（0~16×）和 IIR 滤波器（0~127），灵活权衡速度与精度
- 内置采样间隔控制，防止高频读取导致的重复采样
- 硬件依赖注入设计，总线实例外部传入，不与特定引脚绑定
- 支持上下文管理器（`with` 语句），自动释放资源
- 中英双语 docstring，方便查阅

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| Raspberry Pi Pico / RP2040 | 主控开发板 |
| BME680 模块 | Bosch 四合一环境传感器 |
| 面包板 + 杜邦线 | 接线 |

### 引脚说明 — I2C 模式

| BME680 引脚 | Pico 引脚 | 功能描述 |
|-------------|-----------|----------|
| VCC | 3V3(OUT) | 电源正极（3.3V） |
| GND | GND | 电源负极 |
| SCL | GP1 | I2C 时钟线 |
| SDA | GP0 | I2C 数据线 |
| SDO | GND | I2C 地址选择（GND→0x77，VDD→0x76） |

### 引脚说明 — SPI 模式

| BME680 引脚 | Pico 引脚 | 功能描述 |
|-------------|-----------|----------|
| VCC | 3V3(OUT) | 电源正极（3.3V） |
| GND | GND | 电源负极 |
| SCK | GP18 | SPI 时钟线 |
| SDI (MOSI) | GP19 | SPI 主机输出/从机输入 |
| SDO (MISO) | GP16 | SPI 主机输入/从机输出 |
| CS | GP17 | SPI 片选信号 |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0+ |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`（内置）、`math`（内置）、`struct`/`ustruct`（内置）、`micropython`（内置） |
| 目标平台 | ESP32 / RP2040 / 其他支持 `machine.I2C` 和 `machine.SPI` 的 MicroPython 端口 |

## 文件结构

```
bme680/
├── bme680.py   # BME680 核心驱动（I2C + SPI）
├── main.py            # 测试示例代码
├── examples/test_i2c.py        # I2C 接口快速验证脚本
├── examples/test_spi.py        # SPI 接口快速验证脚本
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `bme680.py` | BME680 核心驱动文件，包含 `BME680` 基类、`BME680_I2C`（I2C 子类）和 `BME680_SPI`（SPI 子类），提供温度/湿度/气压/气体/海拔五项数据的读取与采样参数配置 |
| `main.py` | 完整测试示例，包含 I2C 总线扫描、芯片 ID 预检、默认参数采样循环、边界参数测试和异常参数测试，适用于首次验证硬件 |
| `examples/test_i2c.py` | 极简 I2C 模式验证脚本，快速确认传感器通信 |
| `examples/test_spi.py` | 极简 SPI 模式验证脚本，快速确认传感器通信 |

## 快速开始

### 1. 复制文件

将 `bme680.py` 上传到 MicroPython 设备的根目录（或 `lib/` 目录）。

### 2. 硬件接线

按上方"硬件要求"章节的引脚说明完成 I2C 或 SPI 接线。

### 3. 运行测试

将以下 `main.py` 上传到设备并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Limor 'Ladyada' Fried, Jeff Raber
# @File    : main.py
# @Description : BME680 传感器驱动测试代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from bme680 import BME680_I2C

# ======================================== 全局变量 ============================================

# --- I2C 引脚配置（Raspberry Pi Pico / RP2040） ---
# 也可使用 SPI 模式：from bme680 import BME680_SPI
I2C_ID = 0
SDA_PIN = 0
SCL_PIN = 1
I2C_FREQ = 400000

# --- BME680 设备地址 ---
# SDO 接 GND → 0x77（默认），SDO 接 VDD → 0x76
BME680_I2C_ADDR = 0x77
BME680_ALT_ADDR = 0x76

# --- 芯片 ID 验证参数 ---
BME680_CHIP_ID_REG = 0xD0
BME680_CHIP_ID_VAL = 0x61

# --- 打印控制 ---
PRINT_INTERVAL_MS = 2000
last_print_time = time.ticks_ms()

# --- 传感器实例引用（初始化配置区创建） ---
bme = None

# ======================================== 功能函数 ============================================

def test_boundary_params():
    """
    测试边界参数：最大/最小过采样率和滤波器
    注释自动调用，可 REPL 手动执行
    """
    global bme
    print("--- Boundary Parameter Test ---")

    # 测试最大过采样率
    bme.temperature_oversample = 16
    bme.pressure_oversample = 16
    bme.humidity_oversample = 16
    print("Max oversample (16x): temp=%.2f C, pres=%.2f hPa, hum=%.2f %%"
          % (bme.temperature, bme.pressure, bme.humidity))

    # 测试最小过采样率（跳过采样，仅返回上次值或默认值）
    bme.temperature_oversample = 0
    bme.pressure_oversample = 0
    bme.humidity_oversample = 0
    print("Min oversample (skip): temp=%.2f C, pres=%.2f hPa, hum=%.2f %%"
          % (bme.temperature, bme.pressure, bme.humidity))

    # 测试最大滤波器
    bme.filter_size = 127
    print("Max filter (127): temp=%.2f C" % bme.temperature)
    # 测试最小滤波器
    bme.filter_size = 0
    print("Min filter (0): temp=%.2f C" % bme.temperature)

    # 恢复默认配置
    bme.temperature_oversample = 4
    bme.pressure_oversample = 3
    bme.humidity_oversample = 2
    bme.filter_size = 3
    print("--- Boundary test done, defaults restored ---")


def test_exception_params():
    """
    测试异常参数：非法过采样率/滤波器值应正确抛出 ValueError
    注释自动调用，可 REPL 手动执行
    """
    global bme
    print("--- Exception Parameter Test ---")

    # 测试非法过采样率
    try:
        bme.temperature_oversample = 99
    except ValueError as e:
        print("Caught expected: %s" % e)

    # 测试非法滤波器值
    try:
        bme.filter_size = 255
    except ValueError as e:
        print("Caught expected: %s" % e)

    print("--- Exception test done ---")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: BME680 Temperature/Humidity/Pressure/Gas Sensor Test")
print("=" * 60)

# 初始化 I2C 总线
i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)

# I2C 设备扫描
devices = i2c.scan()
print("I2C bus scan result: %s" % (["0x%02x" % d for d in devices] if devices else "No devices found"))

if not devices:
    raise RuntimeError("No I2C device found on bus %d" % I2C_ID)

# 自动检测 BME680 地址
sensor_addr = BME680_I2C_ADDR if BME680_I2C_ADDR in devices else (
    BME680_ALT_ADDR if BME680_ALT_ADDR in devices else None)

if sensor_addr is None:
    raise RuntimeError(
        "BME680 not found at 0x%02x or 0x%02x. Check wiring and SDO pin."
        % (BME680_I2C_ADDR, BME680_ALT_ADDR))

print("BME680 candidate at 0x%02x, verifying chip ID..." % sensor_addr)

# 芯片 ID 验证（通过直接读取寄存器进行预检）
# 此步骤在实例化驱动之前，用原始 I2C 读取确认硬件存在
try:
    chip_id = i2c.readfrom_mem(sensor_addr, BME680_CHIP_ID_REG, 1)[0]
    if chip_id == BME680_CHIP_ID_VAL:
        print("Device found: BME680 (chip ID 0x%02x verified)" % chip_id)
    else:
        print("Device not found: unexpected chip ID 0x%02x (expected 0x%02x)"
              % (chip_id, BME680_CHIP_ID_VAL))
        raise RuntimeError("Chip ID mismatch")
except OSError as e:
    raise RuntimeError("I2C communication failed during chip ID check") from e

# 实例化传感器（默认配置）
bme = BME680_I2C(i2c, address=sensor_addr)

# 可选：修改采样配置（取消注释以启用）
# bme.temperature_oversample = 8   # 温度 8 倍过采样
# bme.pressure_oversample = 4      # 压力 4 倍过采样
# bme.humidity_oversample = 4      # 湿度 4 倍过采样
# bme.filter_size = 7              # IIR 滤波器大小 7
# bme.sea_level_pressure = 1013.25 # 海平面气压校准

print("BME680 initialized successfully at 0x%02x" % sensor_addr)
print("Oversampling: T=%dx P=%dx H=%dx  Filter=%d"
      % (bme.temperature_oversample, bme.pressure_oversample,
         bme.humidity_oversample, bme.filter_size))
print("=" * 60)

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        # 按打印间隔输出低频核心数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            print("T: %.2f C  H: %.2f %%  P: %.2f hPa  Gas: %d ohm  Alt: %.2f m"
                  % (bme.temperature, bme.humidity, bme.pressure,
                     bme.gas, bme.altitude))
            last_print_time = current_time

        # test_boundary_params()   # 边界测试：最大/最小过采样率与滤波器
        # test_exception_params()  # 异常测试：非法参数校验
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if bme is not None:
        bme.deinit()
        del bme
    print("Program exited")
```

### 4. 最小代码示例（SPI 模式）

如需使用 SPI 接口，将导入和实例化替换为：

```python
from machine import Pin, SPI
from bme680 import BME680_SPI

cs = Pin(17, Pin.OUT, value=1)
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB,
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))
bme = BME680_SPI(spi, cs)
print("Temperature: %.2f C" % bme.temperature)
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作电压 | 1.71V ~ 3.6V（推荐 3.3V），不可直连 5V |
| 温度范围 | -40°C ~ +85°C，精度 ±0.5°C（25°C 时） |
| 湿度范围 | 0 ~ 100%RH，精度 ±3%RH |
| 气压范围 | 300 ~ 1100 hPa，精度 ±0.6 hPa |
| 气体电阻 | 用于 VOC/IAQ 定性判断，需稳定运行 30 分钟以上数据才有参考价值 |
| I2C 地址 | 默认 0x77（SDO 接 GND），切换 SDO 接 VDD 为 0x76 |
| SPI 模式 | 仅支持 SPI Mode 0（CPOL=0, CPHA=0） |
| 采样间隔 | 驱动内部通过 `refresh_rate` 参数控制最小采样间隔，默认每秒最多 10 次 |
| 海拔计算 | 依赖 `sea_level_pressure` 属性，默认值 1013.25 hPa，需根据当地海平面气压校准 |
| 加热器 | BME680 气体传感器需加热到 300°C 左右，首次上电后需稳定几分钟 |
| 过采样率 | 仅支持 0, 1, 2, 4, 8, 16 六档，传入其他值将抛出 `ValueError` |
| 滤波器 | 仅支持 0, 1, 3, 7, 15, 31, 63, 127 八档，传入其他值将抛出 `ValueError` |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | Limor 'Ladyada' Fried, Jeff Raber | 初始版本，支持 I2C/SPI 双接口 |

## 联系方式

- 原作者：Limor 'Ladyada' Fried (Adafruit Industries)
- SPI 支持：Jeff Raber
- 规范化与维护：FreakStudio
- GitHub：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
