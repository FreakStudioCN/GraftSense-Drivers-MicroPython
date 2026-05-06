# AGS02MA MicroPython Driver

AGS02MA TVOC/气体传感器的 MicroPython I2C 驱动。

## 简介 | Overview

AGS02MA 是一款 TVOC（总挥发性有机物）气体传感器，通过 I2C 接口通信，默认地址 `0x1A`。本驱动支持读取 TVOC 浓度（ppb）和气敏电阻值，并提供固件版本查询和调试接口。

> 注意：传感器上电后需预热约 30 分钟才能输出稳定数据。

## 硬件连接 | Wiring

| AGS02MA | ESP32 |
|---------|-------|
| VCC     | 3.3V  |
| GND     | GND   |
| SDA     | GPIO4 |
| SCL     | GPIO5 |

> AGS02MA 需要低速 I2C（建议 ≤ 30 kHz），SDA/SCL 需要上拉电阻。

## 安装 | Installation

通过 `mip` 安装：

```python
import mip
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/ags02ma_driver")
```

或手动将 `ags02ma.py` 复制到设备根目录。

## 快速开始 | Quick Start

```python
import machine
from ags02ma import AGS02MA

i2c = machine.SoftI2C(scl=machine.Pin(5), sda=machine.Pin(4), freq=20000)
ags = AGS02MA(i2c)

print(ags.TVOC)           # TVOC 浓度，单位 ppb
print(ags.gas_resistance) # 气敏电阻，单位 0.1 kΩ
```

## API 参考 | API Reference

### `AGS02MA(i2c, addr=0x1A, debug=False)`

初始化传感器。

| 参数    | 类型 | 说明                       |
|---------|------|----------------------------|
| `i2c`   | I2C  | I2C 总线实例               |
| `addr`  | int  | I2C 地址，默认 `0x1A`      |
| `debug` | bool | 启用调试输出，默认 `False` |

### 属性

| 属性             | 返回类型 | 说明                    |
|------------------|----------|-------------------------|
| `TVOC`           | int      | TVOC 浓度，单位 ppb     |
| `gas_resistance` | int      | 气敏电阻值，单位 0.1 kΩ |

### 方法

| 方法                            | 返回类型  | 说明                         |
|---------------------------------|-----------|------------------------------|
| `firmware_version()`            | int       | 读取 24 位固件版本号         |
| `debug_read_raw(addr, delayms)` | bytearray | 读取寄存器原始字节（调试用） |
| `deinit()`                      | None      | 释放资源                     |

## 异常说明 | Exceptions

| 异常           | 触发条件                            |
|----------------|-------------------------------------|
| `ValueError`   | 参数类型或范围错误                  |
| `RuntimeError` | 传感器未就绪、预热中或 CRC 校验失败 |

## 许可证 | License

MIT License — © Tom Øyvind Hogstad
