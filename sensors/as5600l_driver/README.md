# AS5600 / AS5600L 12位磁性旋转编码器驱动 | 12-bit Magnetic Rotary Encoder Driver

[中文](#中文) | [English](#english)

---

## 中文

### 简介

适用于 AS5600 / AS5600L 12位磁性旋转编码器的 MicroPython 驱动，通过 I2C 接口读取角度、磁铁状态、AGC 及磁场强度，并支持起始/终止角度与最大角度的配置写入。AS5600L 为 AS5600 的低电压变体，I2C 地址不同（0x40 vs 0x36），两者共用同一驱动文件 `as5600.py`。

### 特性

- 12 位角度分辨率（0~4095 对应 0~360°）
- I2C 接口，AS5600 默认地址 0x36，AS5600L 默认地址 0x40
- 支持原始角度与映射角度读取
- 支持 ZPOS / MPOS / MANG 角度范围配置
- 支持 CONF 寄存器全位域读写（PM / HYST / OUTS / PWMF / SF / FTH / WD）
- 磁铁检测状态（MD / ML / MH）、AGC 与 CORDIC 磁场强度读取
- 支持 OTP 烧录（不可逆，谨慎使用）
- 兼容 MicroPython v1.23

### 硬件连接

| 传感器引脚 | 说明          | 典型 MCU 引脚（示例）     |
|-----------|--------------|--------------------------|
| VDD       | 电源 3.3V     | 3.3V                     |
| GND       | 地            | GND                      |
| SDA       | I2C 数据线    | Pin(4)（示例，按板卡调整）|
| SCL       | I2C 时钟线    | Pin(5)（示例，按板卡调整）|
| DIR       | 旋转方向选择  | GND（顺时针）/ VDD（逆时针）|

> 具体引脚请参考所用开发板的 I2C 引脚定义。

### 安装方法

**方式一：mip 在线安装（需联网）**

```python
import mip
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/as5600l_driver")
```

**方式二：手动复制**

将 `as5600.py` 复制到设备根目录或 `lib/` 目录：

```bash
mpremote cp as5600.py :as5600.py
```

### 快速开始

```python
from machine import I2C, Pin
import time
from as5600 import AS5600

# AS5600L 地址为 0x40，标准 AS5600 使用 0x36
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
sensor = AS5600(i2c, device=0x40)

while True:
    mapped = sensor.angle()
    print("Angle: %d (%.2f deg)  magnet=%d" % (mapped, mapped * 360.0 / 4096.0, sensor.md()))
    time.sleep_ms(1000)
```

### API 参考

| 接口 | 类型 | 说明 |
|------|------|------|
| `AS5600(i2c, device=0x36, debug=False)` | 构造函数 | 初始化驱动，校验参数，不发起 I2C 通信 |
| `sensor.rawangle()` | `int` 方法 | 读取原始角度（0~4095，未经映射） |
| `sensor.angle()` | `int` 方法 | 读取映射角度（0~4095，经 ZPOS/MPOS/MANG 映射） |
| `sensor.md()` | `int` 方法 | 磁铁检测状态（1=检测到） |
| `sensor.ml()` | `int` 方法 | 磁铁过弱标志（1=过弱） |
| `sensor.mh()` | `int` 方法 | 磁铁过强标志（1=过强） |
| `sensor.agc()` | `int` 方法 | 读取 AGC 值（0~255） |
| `sensor.magnitude()` | `int` 方法 | 读取 CORDIC 磁场强度（12 位） |
| `sensor.zmco(*args)` | `int` 方法 | 读取 OTP 烧录次数（0~3，只读） |
| `sensor.zpos(*args)` | `int` 方法 | 读写起始角度 ZPOS（0~4095） |
| `sensor.mpos(*args)` | `int` 方法 | 读写终止角度 MPOS（0~4095） |
| `sensor.mang(*args)` | `int` 方法 | 读写最大角度 MANG（0~4095） |
| `sensor.pm(*args)` | `int` 方法 | 电源模式 PM[1:0]（0=NOM，1~3=LPM） |
| `sensor.hyst(*args)` | `int` 方法 | 滞回 HYST[1:0] |
| `sensor.outs(*args)` | `int` 方法 | 输出阶段 OUTS[1:0] |
| `sensor.pwmf(*args)` | `int` 方法 | PWM 频率 PWMF[1:0] |
| `sensor.sf(*args)` | `int` 方法 | 慢滤波器 SF[1:0] |
| `sensor.fth(*args)` | `int` 方法 | 快滤波阈值 FTH[2:0] |
| `sensor.watchdog(*args)` | `int` 方法 | 看门狗使能 WD |
| `sensor.burn_angle()` | 方法 | 烧录 ZPOS/MPOS 到 OTP（**不可逆**） |
| `sensor.burn_setting()` | 方法 | 烧录 MANG/CONF 到 OTP（**不可逆**） |
| `sensor.readwrite(reg, firstbit, lastbit, *args)` | `int` 方法 | 通用寄存器位域读写（底层接口） |
| `sensor.deinit()` | 方法 | 释放驱动资源（不释放外部 I2C 总线） |

> 所有读写方法：无参数 = 读取，传入 1 个 `int` 参数 = 写入并返回写入值。

### 注意事项

- AS5600L 的 I2C 地址为 `0x40`，标准 AS5600 为 `0x36`，构造时请按实际芯片传入 `device` 参数。
- `burn_angle()` 和 `burn_setting()` 写入 OTP，**操作不可逆**，调用前请确认 ZPOS/MPOS/MANG/CONF 已正确配置。
- burn 命令值（0x08/0x04）沿用原驱动，与部分数据手册标注（0x80/0x40）存在差异，烧录前请自行核对所用芯片版本的数据手册。
- `deinit()` 不释放外部传入的 I2C 总线，需由调用方自行管理。
- `debug=True` 时通过 `print` 输出寄存器读写日志，生产环境建议关闭。

### License

MIT License — Copyright (c) hogeiha

---

## English

### Introduction

MicroPython driver for AS5600 / AS5600L 12-bit magnetic rotary encoders. Reads angle, magnet status, AGC, and magnitude over I2C, and supports writing start/stop angle and max angle configuration. AS5600L is a low-voltage variant of AS5600 with a different I2C address (0x40 vs 0x36); both share the same driver file `as5600.py`.

### Features

- 12-bit angle resolution (0~4095 maps to 0~360°)
- I2C interface; AS5600 default address 0x36, AS5600L default address 0x40
- Raw and mapped angle reading
- ZPOS / MPOS / MANG angle range configuration
- Full CONF register bit-field R/W (PM / HYST / OUTS / PWMF / SF / FTH / WD)
- Magnet detection (MD / ML / MH), AGC, and CORDIC magnitude reading
- OTP burn support (irreversible — use with caution)
- Compatible with MicroPython v1.23

### Hardware Connection

| Sensor Pin | Description        | Typical MCU Pin (example)       |
|-----------|--------------------|---------------------------------|
| VDD       | Power 3.3V         | 3.3V                            |
| GND       | Ground             | GND                             |
| SDA       | I2C Data           | Pin(4) (adjust per board)       |
| SCL       | I2C Clock          | Pin(5) (adjust per board)       |
| DIR       | Rotation direction | GND (CW) / VDD (CCW)            |

> Refer to your board's pinout for the correct I2C pins.

### Installation

**Option 1: mip (requires network)**

```python
import mip
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/as5600l_driver")
```

**Option 2: Manual copy**

Copy `as5600.py` to the device root or `lib/` directory:

```bash
mpremote cp as5600.py :as5600.py
```

### Quick Start

```python
from machine import I2C, Pin
import time
from as5600 import AS5600

# AS5600L address is 0x40; standard AS5600 uses 0x36
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
sensor = AS5600(i2c, device=0x40)

while True:
    mapped = sensor.angle()
    print("Angle: %d (%.2f deg)  magnet=%d" % (mapped, mapped * 360.0 / 4096.0, sensor.md()))
    time.sleep_ms(1000)
```

### API Reference

| Interface | Type | Description |
|-----------|------|-------------|
| `AS5600(i2c, device=0x36, debug=False)` | Constructor | Initialize driver, validate params, no I2C I/O |
| `sensor.rawangle()` | `int` method | Read raw angle (0~4095, unmapped) |
| `sensor.angle()` | `int` method | Read mapped angle (0~4095, via ZPOS/MPOS/MANG) |
| `sensor.md()` | `int` method | Magnet detected flag (1=present) |
| `sensor.ml()` | `int` method | Magnet too weak flag |
| `sensor.mh()` | `int` method | Magnet too strong flag |
| `sensor.agc()` | `int` method | Read AGC value (0~255) |
| `sensor.magnitude()` | `int` method | Read CORDIC magnitude (12-bit) |
| `sensor.zmco(*args)` | `int` method | Read OTP burn counter (0~3, read-only) |
| `sensor.zpos(*args)` | `int` method | Read/write start position ZPOS (0~4095) |
| `sensor.mpos(*args)` | `int` method | Read/write stop position MPOS (0~4095) |
| `sensor.mang(*args)` | `int` method | Read/write max angle MANG (0~4095) |
| `sensor.pm(*args)` | `int` method | Power mode PM[1:0] (0=NOM, 1~3=LPM) |
| `sensor.hyst(*args)` | `int` method | Hysteresis HYST[1:0] |
| `sensor.outs(*args)` | `int` method | Output stage OUTS[1:0] |
| `sensor.pwmf(*args)` | `int` method | PWM frequency PWMF[1:0] |
| `sensor.sf(*args)` | `int` method | Slow filter SF[1:0] |
| `sensor.fth(*args)` | `int` method | Fast filter threshold FTH[2:0] |
| `sensor.watchdog(*args)` | `int` method | Watchdog enable WD |
| `sensor.burn_angle()` | method | Burn ZPOS/MPOS to OTP (**irreversible**) |
| `sensor.burn_setting()` | method | Burn MANG/CONF to OTP (**irreversible**) |
| `sensor.readwrite(reg, firstbit, lastbit, *args)` | `int` method | Generic bit-field R/W (low-level) |
| `sensor.deinit()` | method | Release driver resources (does not close I2C bus) |

> All R/W methods: no args = read; one `int` arg = write and return written value.

### Notes

- AS5600L I2C address is `0x40`; standard AS5600 is `0x36`. Pass the correct `device` value to the constructor.
- `burn_angle()` and `burn_setting()` write to OTP and are **irreversible**. Verify ZPOS/MPOS/MANG/CONF before calling.
- Burn command values (0x08/0x04) follow the original driver; some datasheets specify 0x80/0x40. Verify against your chip's datasheet before burning.
- `deinit()` does not release the externally provided I2C bus; the caller is responsible for managing it.
- Set `debug=True` to enable register R/W logging via `print`; disable in production.

### License

MIT License — Copyright (c) hogeiha
