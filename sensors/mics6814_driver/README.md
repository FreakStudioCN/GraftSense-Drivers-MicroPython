# MiCS6814 MicroPython Driver

MiCS6814 CO、NH3、NO2 三通道 ADC 采集驱动，适用于 MicroPython v1.23.0。

## 功能特性

- 支持 CO、NH3、NO2 三通道气体电阻读取
- 支持原始 ADC 值和电压值读取
- 支持多次采样平均
- 可配置负载电阻和参考电压

## 安装

```python
import mip
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/mics6814_driver")
```

## 接线

| MiCS6814 引脚 | Pico 引脚 |
|--------------|-----------|
| CO (REDUCING) | GPIO26 (ADC0) |
| NH3           | GPIO27 (ADC1) |
| NO2 (OX)      | GPIO28 (ADC2) |
| VCC           | 3.3V |
| GND           | GND |

## 使用示例

```python
from mics6814 import MICS6814

gas = MICS6814(co_pin=26, nh3_pin=27, no2_pin=28)

readings = gas.read_all()
print(readings)
# CO: 12345.67 Ohms
# NH3: 23456.78 Ohms
# NO2: 34567.89 Ohms

print(gas.read_co())
print(gas.read_nh3())
print(gas.read_no2())
```

## API

### `MICS6814(co_pin, nh3_pin, no2_pin, vref=3.3, load_resistor=56000, samples=1)`

初始化三通道 ADC 采集驱动。

| 参数 | 类型 | 说明 |
|------|------|------|
| co_pin | int/Pin/ADC | CO 通道 ADC 引脚 |
| nh3_pin | int/Pin/ADC | NH3 通道 ADC 引脚 |
| no2_pin | int/Pin/ADC | NO2 通道 ADC 引脚 |
| vref | float | ADC 参考电压，默认 3.3V |
| load_resistor | float | 负载电阻，默认 56000Ω |
| samples | int | 平均采样次数，默认 1 |

### 方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `read_all()` | `Mics6814Reading` | 读取三通道电阻、电压和原始值 |
| `read_raw_all()` | `dict` | 读取三通道原始 ADC 值 |
| `read_voltage_all()` | `dict` | 读取三通道电压值 |
| `read_co()` | `float` | 读取 CO 通道电阻（Ω） |
| `read_nh3()` | `float` | 读取 NH3 通道电阻（Ω） |
| `read_no2()` | `float` | 读取 NO2 通道电阻（Ω） |

## 许可证

MIT License - Copyright (c) 2026 leezisheng
