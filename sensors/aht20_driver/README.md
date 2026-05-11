# AHT10 / AHT20 温湿度传感器驱动 | Temperature & Humidity Sensor Driver

[中文](#中文) | [English](#english)

---

## 中文

### 简介

适用于 AHT10 / AHT20 温湿度传感器的 MicroPython 驱动，通过 I2C 接口读取温度（℃）和相对湿度（%RH）。AHT20 为 AHT10 的升级版本，两者共用同一驱动文件 `ahtx0.py`，仅初始化命令不同。

### 特性

- 支持 AHT10 和 AHT20 两款芯片
- I2C 接口，默认地址 0x38
- 温度精度 ±0.3℃，湿度精度 ±2%RH
- 支持软复位与校准状态查询
- 兼容 MicroPython v1.23

### 硬件连接

| 传感器引脚 | 说明         | 典型 MCU 引脚（示例）|
|-----------|-------------|---------------------|
| VDD       | 电源 3.3V    | 3.3V                |
| GND       | 地| GND                 |
| SDA       | I2C 数据线   | PB7（I2C1 SDA）     |
| SCL       | I2C 时钟线   | PB6（I2C1 SCL）     |

> 具体引脚请参考所用开发板的 I2C 引脚定义。

### 安装方法

**方式一：mip 在线安装（需联网）**

```python
import mip
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/aht20_driver")
```

**方式二：手动复制**

将 `ahtx0.py` 复制到设备根目录或 `lib/` 目录：

```bash
mpremote cp ahtx0.py :ahtx0.py
```

### 快速开始

```python
from machine import I2C
import utime
import ahtx0

I2C_ID      = 1
INTERVAL_MS = 2500

i2c = I2C(I2C_ID)
sensor = ahtx0.AHT20(i2c)

print("AHT20 sensor test started")

while True:
    try:
        temp = sensor.temperature
        humi = sensor.relative_humidity
        print("Temperature : %5.1f C" % temp)
        print("  Humidity  : %5.1f %%rH" % humi)
        print("-" * 28)
    except RuntimeError as e:
        print("Sensor runtime error: %s" % e)
    except OSError as e:
        print("Sensor OS error: %s" % e)
    utime.sleep_ms(INTERVAL_MS)
```

### API 参考

| 接口 | 类型 | 说明 |
|------|------|------|
| `AHT10(i2c, address=0x38, debug=False)` | 构造函数 | 初始化 AHT10，执行软复位和校准（约 40ms） |
| `AHT20(i2c, address=0x38, debug=False)` | 构造函数 | AHT20 子类，初始化命令不同（0xBE） |
| `sensor.temperature` | `float` 属性 | 读取温度（℃），触发一次完整测量（约 80ms） |
| `sensor.relative_humidity` | `float` 属性 | 读取相对湿度（%RH），触发一次完整测量（约 80ms） |
| `sensor.status` | `int` 属性 | 读取状态字节原始值 |
| `sensor.reset()` | 方法 | 软复位传感器，等待 20ms |
| `sensor.initialize()` | `bool` 方法 | 发送初始化命令并等待校准，返回是否成功 |
| `sensor.deinit()` | 方法 | 释放传感器资源（不释放外部 I2C 总线） |

### 注意事项

- `temperature` 和 `relative_humidity` 各自独立触发一次测量，若需同时获取两个值，建议连续读取，两次调用间隔不必额外等待。
- 构造函数会自动执行软复位和校准，上电后约需 40ms 完成初始化。
- `deinit()` 不会释放外部传入的 I2C 总线，需由调用方自行管理。
- `debug=True` 时会通过 `print` 输出调试信息，生产环境建议关闭。

### License

MIT License — Copyright (c) Andreas Bühl, Kattni Rembor

---

## English

### Introduction

MicroPython driver for AHT10 / AHT20 temperature and humidity sensors. Reads temperature (°C) and relative humidity (%RH) over I2C. AHT20 is an improved version of AHT10; both share the same driver file `ahtx0.py` with only the initialization command differing.

### Features

- Supports both AHT10 and AHT20 chips
- I2C interface, default address 0x38
- Temperature accuracy ±0.3°C, humidity accuracy ±2%RH
- Soft reset and calibration status query
- Compatible with MicroPython v1.23

### Hardware Connection

| Sensor Pin | Description    | Typical MCU Pin (example) |
|-----------|----------------|---------------------------|
| VDD       | Power 3.3V     | 3.3V                      |
| GND       | Ground         | GND                       |
| SDA       | I2C Data       | PB7 (I2C1 SDA)            |
| SCL       | I2C Clock      | PB6 (I2C1 SCL)            |

> Refer to your board's pinout for the correct I2C pins.

### Installation

**Option 1: mip (requires network)**

```python
import mip
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/aht20_driver")
```

**Option 2: Manual copy**

Copy `ahtx0.py` to the device root or `lib/` directory:

```bash
mpremote cp ahtx0.py :ahtx0.py
```

### Quick Start

```python
from machine import I2C
import utime
import ahtx0

I2C_ID      = 1
INTERVAL_MS = 2500

i2c = I2C(I2C_ID)
sensor = ahtx0.AHT20(i2c)

print("AHT20 sensor test started")

while True:
    try:
        temp = sensor.temperature
        humi = sensor.relative_humidity
        print("Temperature : %5.1f C" % temp)
        print("  Humidity  : %5.1f %%rH" % humi)
        print("-" * 28)
    except RuntimeError as e:
        print("Sensor runtime error: %s" % e)
    except OSError as e:
        print("Sensor OS error: %s" % e)
    utime.sleep_ms(INTERVAL_MS)
```

### API Reference

| Interface | Type | Description |
|-----------|------|-------------|
| `AHT10(i2c, address=0x38, debug=False)` | Constructor | Initialize AHT10, performs soft reset and calibration (~40ms) |
| `AHT20(i2c, address=0x38, debug=False)` | Constructor | AHT20 subclass with different init command (0xBE) |
| `sensor.temperature` | `float` property | Read temperature in °C, triggers a full measurement (~80ms) |
| `sensor.relative_humidity` | `float` property | Read relative humidity in %RH, triggers a full measurement (~80ms) |
| `sensor.status` | `int` property | Read raw status byte |
| `sensor.reset()` | Method | Soft reset the sensor, waits 20ms |
| `sensor.initialize()` | `bool` method | Send init command and wait for calibration, returns success |
| `sensor.deinit()` | Method | Release sensor resources (does not release the I2C bus) |

### Notes

- `temperature` and `relative_humidity` each trigger an independent measurement. If both values are needed, read them consecutively without extra delay.
- The constructor automatically performs soft reset and calibration; allow ~40ms after power-on.
- `deinit()` does not release the externally provided I2C bus; the caller is responsible for managing it.
- Set `debug=True` to enable print-based debug output; disable in production.

### License

MIT License — Copyright (c) Andreas Bühl, Kattni Rembor
