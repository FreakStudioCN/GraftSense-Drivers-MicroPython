# AS5600 / AS5600L 12位磁性旋转编码器驱动 - MicroPython版本

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

---

## 简介

适用于 AS5600 / AS5600L 12位磁性旋转编码器的 MicroPython 驱动，通过 I2C 接口读取角度、磁铁状态、AGC 及 CORDIC 磁场强度，并支持起始/终止角度与最大角度的配置写入。AS5600L 为 AS5600 的低电压变体，I2C 地址不同（0x40 vs 0x36），两者共用同一驱动文件 `as5600.py`，适用于旋转位置检测、电机换相、旋钮控制等场景。

---

## 主要功能

- 12位角度分辨率（0~4095 对应 0~360°），支持原始角度与映射角度读取
- I2C 接口，AS5600 默认地址 0x36，AS5600L 默认地址 0x40，构造时可指定
- 支持 ZPOS / MPOS / MANG 角度范围配置（起始/终止/最大角度）
- 支持 CONF 寄存器全位域读写（PM / HYST / OUTS / PWMF / SF / FTH / WD）
- 磁铁检测三态（MD / ML / MH）、AGC 与 CORDIC 磁场强度读取
- 通用寄存器位域读写底层接口 `readwrite()`，支持任意位域操作
- 支持 OTP 烧录（不可逆，谨慎使用）
- 调试模式（`debug=True`）通过 `print` 输出寄存器读写日志

---

## 硬件要求

**推荐测试硬件**

- 主控：ESP32 / RP2040 / 任意支持 MicroPython 的开发板
- 传感器：AS5600 或 AS5600L 磁性旋转编码器模块
- 配套磁铁：直径 6mm 径向充磁圆形磁铁（置于芯片正上方）

**引脚说明**

| 传感器引脚 | 功能描述 | 典型 MCU 引脚（示例） |
|-----------|----------|----------------------|
| VDD | 电源正极（3.3V） | 3.3V |
| GND | 电源负极 | GND |
| SCL | I2C 时钟线 | Pin(5) |
| SDA | I2C 数据线 | Pin(4) |
| DIR | 旋转方向选择 | GND（顺时针）/ VDD（逆时针） |

> 具体引脚请参考所用开发板的 I2C 引脚定义。

---

## 软件环境

- MicroPython 固件版本：v1.23.0 及以上
- 驱动版本：v1.0.0
- 依赖库：`machine`（内置）、`micropython`（内置），无需额外安装第三方库

---

## 文件结构

```
as5600l_driver/
├── code/
│   ├── as5600.py      # 核心驱动
│   └── main.py        # 测试示例
├── README.md          # 说明文档
├── package.json       # mip 包配置
└── LICENSE            # 许可证文件
```

---

## 文件说明

- `code/as5600.py`：核心驱动文件，实现 `AS5600` 类，封装所有寄存器读写、角度读取、磁铁状态、CONF 配置及 OTP 烧录接口。
- `code/main.py`：测试示例，演示 I2C 初始化、设备扫描与验证、角度实时读取、配置回读、边界参数测试及异常参数验证。
- `README.md`：驱动说明文档。
- `package.json`：mip 在线安装包配置文件。
- `LICENSE`：MIT 许可证。

---

## 快速开始

**第一步：复制驱动文件到设备**

```bash
mpremote cp as5600.py :as5600.py
```

**第二步：按引脚说明接线**

| 传感器引脚 | 连接至 |
|-----------|--------|
| VDD | 3.3V |
| GND | GND |
| SCL | Pin(5) |
| SDA | Pin(4) |
| DIR | GND（顺时针） |

**第三步：运行测试**

```bash
mpremote run main.py
```

**最小可运行代码示例**

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/05/15
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试 AS5600/AS5600L 12位磁性旋转编码器驱动类
# @License : MIT

__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

import time
from machine import I2C, Pin
from as5600 import AS5600

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000

AS5600_ADDR = 0x40

DEVICE_VERIFY_REG = 0x1B
DEVICE_VERIFY_MASK = 0xC7
DEVICE_VERIFY_EXPECTED = 0x00

PRINT_INTERVAL_MS = 1000
last_print_time = time.ticks_ms()

def print_realtime_angle():
    """高频读取实时角度（默认注释执行，可在 REPL 手动调用）"""
    raw = sensor.rawangle()
    mapped = sensor.angle()
    print("Raw: %d  Angle: %d  (%.2f deg)" % (raw, mapped, mapped * 360.0 / 4096.0))

def print_status():
    """打印磁铁状态、AGC 与磁场强度"""
    md = sensor.md()
    ml = sensor.ml()
    mh = sensor.mh()
    agc = sensor.agc()
    mag = sensor.magnitude()
    print("Magnet: detected=%d weak=%d strong=%d  AGC=%d  Magnitude=%d"
          % (md, ml, mh, agc, mag))

def print_config():
    """打印当前配置寄存器（ZMCO/ZPOS/MPOS/MANG/CONF 各位域）"""
    zmco = sensor.zmco()
    zpos = sensor.zpos()
    mpos = sensor.mpos()
    mang = sensor.mang()
    pm = sensor.pm()
    hyst = sensor.hyst()
    outs = sensor.outs()
    pwmf = sensor.pwmf()
    sf = sensor.sf()
    fth = sensor.fth()
    wd = sensor.watchdog()
    print("ZMCO=%d ZPOS=%d MPOS=%d MANG=%d" % (zmco, zpos, mpos, mang))
    print("CONF: PM=%d HYST=%d OUTS=%d PWMF=%d SF=%d FTH=%d WD=%d"
          % (pm, hyst, outs, pwmf, sf, fth, wd))

def test_boundary_write():
    """边界参数场景：ZPOS 写入 0 与 4095（12 位最小/最大）"""
    sensor.zpos(0)
    v0 = sensor.zpos()
    sensor.zpos(4095)
    v1 = sensor.zpos()
    print("Boundary ZPOS write: 0 -> %d, 4095 -> %d" % (v0, v1))

def test_invalid_args():
    """异常参数场景：验证非法参数能正确抛出 ValueError"""
    try:
        sensor.readwrite(0x100, 7, 0)
    except ValueError as e:
        print("Caught register out-of-range: %s" % e)
    try:
        sensor.readwrite(0x07, 3, 5)
    except ValueError as e:
        print("Caught invalid bitfield: %s" % e)
    try:
        sensor.zpos(0x10000)
    except ValueError as e:
        print("Caught value out-of-range: %s" % e)
    try:
        sensor.zpos("bad")
    except ValueError as e:
        print("Caught wrong type: %s" % e)

def burn_angle_once():
    """烧录角度（ZPOS/MPOS）到 OTP，不可逆，仅 REPL 手动触发"""
    sensor.burn_angle()
    print("burn_angle issued")

def burn_setting_once():
    """烧录配置（MANG/CONF）到 OTP，不可逆，仅 REPL 手动触发"""
    sensor.burn_setting()
    print("burn_setting issued")

time.sleep(3)
print("FreakStudio: AS5600/AS5600L magnetic encoder driver test")

i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found")
print("I2C scan result: %s" % [hex(d) for d in devices])

if AS5600_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % AS5600_ADDR)
print("Target device 0x%02X present on bus" % AS5600_ADDR)

_probe = i2c.readfrom_mem(AS5600_ADDR, DEVICE_VERIFY_REG, 1)[0]
if (_probe & ~DEVICE_VERIFY_MASK) == DEVICE_VERIFY_EXPECTED:
    print("Device found (STATUS=0x%02X)" % _probe)
else:
    print("Device not found (STATUS=0x%02X, unexpected reserved bits)" % _probe)

sensor = AS5600(i2c, device=AS5600_ADDR, debug=False)

try:
    print_config()
    print_status()
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            raw = sensor.rawangle()
            mapped = sensor.angle()
            md = sensor.md()
            print("Angle raw=%d mapped=%d (%.2f deg)  magnet=%d"
                  % (raw, mapped, mapped * 360.0 / 4096.0, md))
            last_print_time = current_time
        # print_realtime_angle()
        # print_status()
        # print_config()
        # test_boundary_write()
        # test_invalid_args()
        # burn_angle_once()
        # burn_setting_once()
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    try:
        sensor.deinit()
    except Exception:
        pass
    del sensor
    print("Program exited")
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| I2C 地址 | AS5600L 地址为 `0x40`，标准 AS5600 为 `0x36`，构造时请按实际芯片传入 `device` 参数 |
| OTP 烧录 | `burn_angle()` 和 `burn_setting()` 写入 OTP，**操作不可逆**，调用前请确认 ZPOS/MPOS/MANG/CONF 已正确配置 |
| 烧录命令值 | burn 命令值（0x08/0x04）沿用原驱动，与部分数据手册标注（0x80/0x40）存在差异，烧录前请自行核对所用芯片版本的数据手册 |
| I2C 总线管理 | `deinit()` 不释放外部传入的 I2C 总线，需由调用方自行管理 |
| 调试模式 | `debug=True` 时通过 `print` 输出寄存器读写日志，生产环境建议关闭 |
| 工作电压 | AS5600 工作电压 3.3V~5V；AS5600L 为低电压变体，请参考数据手册确认供电范围 |
| 磁铁放置 | 磁铁需径向充磁，置于芯片正上方，间距建议 0.5~3mm，偏心或倾斜会影响精度 |

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2025-05-15 | hogeiha | 初始版本，支持 AS5600/AS5600L，完整寄存器位域读写 |

---

## 联系方式

- 邮箱：请填写联系邮箱
- GitHub：[FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

MIT License

Copyright (c) 2026 hogeiha

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
