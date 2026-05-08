# TSL2561 MicroPython Driver

TSL2561 数字光照强度传感器的 MicroPython I2C 驱动，适用于 Raspberry Pi Pico 等 MicroPython 平台。

## 功能特性

- 支持双通道（可见光+红外 / 纯红外）原始数据读取
- 支持 lux 光照强度换算输出
- 支持三种积分时间：13.7ms / 101ms / 402ms 及手动模式
- 支持 1x / 16x 增益切换
- 支持上电 / 断电控制
- 支持 `machine.I2C` 和 `machine.SoftI2C`
- I2C 地址支持 0x29 / 0x39 / 0x49

## 安装

```python
import mip
mip.install("github:FreakStudioCN/MicroPython_Drivers/sensors/tsl2561_driver")
```

或手动复制 `tsl2561.py` 到设备。

## 接线

| TSL2561 | Pico |
|---------|------|
| VCC     | 3.3V |
| GND     | GND  |
| SDA     | GP4  |
| SCL     | GP5  |
| ADDR    | GND (0x39) |

## 快速上手

```python
from machine import Pin, SoftI2C
from tsl2561 import TSL2561, T_SLOW

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
sensor = TSL2561(i2c, addr=0x39)

# 读取 lux
print(sensor.lux)

# 读取原始双通道数据
ch0, ch1 = sensor.read_raw()
print("CH0:", ch0, "CH1:", ch1)
```

## API 参考

### 构造函数

```python
TSL2561(i2c, addr=0x39)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `i2c` | I2C / SoftI2C | 已初始化的 I2C 总线对象 |
| `addr` | int | I2C 地址，默认 0x39，可选 0x29 / 0x49 |

### 方法

| 方法 | 说明 |
|------|------|
| `set_power_up(state)` | 上电（True）或断电（False） |
| `set_timing_gain(timing, gain, manual_start)` | 设置积分时间和增益 |
| `get_id()` | 返回 (part_number, revision) |
| `read_raw()` | 返回 (channel_0, channel_1) 原始值 |
| `get_lumi()` | 返回 lux 光照强度（float） |

### 属性

| 属性 | 说明 |
|------|------|
| `lux` | 当前光照强度（等同于 `get_lumi()`） |

### 积分时间常量

| 常量 | 值 | 积分时间 |
|------|----|---------|
| `T_FAST` | 0b00 | ~13.7ms |
| `T_MEDIUM` | 0b01 | ~101ms |
| `T_SLOW` | 0b10 | ~402ms |
| `T_MANUAL` | 0b11 | 手动 |

## 示例

```python
from machine import Pin, SoftI2C
from tsl2561 import TSL2561, T_FAST
import time

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
sensor = TSL2561(i2c, addr=0x39)

# 切换为快速积分 + 16x 增益
sensor.set_timing_gain(T_FAST, gain=True)

while True:
    print("Lux: {:.2f}".format(sensor.lux))
    time.sleep(1)
```

## 许可证

MIT License — Copyright (c) 2026 leezisheng
