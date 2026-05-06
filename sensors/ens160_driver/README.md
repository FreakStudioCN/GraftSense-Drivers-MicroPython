# ENS160 MicroPython Driver

ENS160 数字金属氧化物多气体传感器驱动，支持 eCO2、TVOC、AQI 测量，基于 `sensor_pack_2` I2C 适配器封装。

## 传感器简介

| 参数 | 值 |
|------|----|
| 型号 | ENS160 |
| 制造商 | ScioSense |
| 通信接口 | I2C |
| I2C 地址 | 0x52 / 0x53 |
| 供电电压 | 1.71V – 1.89V (VDD), 1.71V – 3.6V (VDDIO) |
| 测量参数 | eCO2 (400–65000 ppm), TVOC (0–65000 ppb), AQI (1–5) |

## 文件结构

```
ens160_driver/
├── code/
│   ├── ens160sciosense.py   # 驱动文件
│   ├── main.py              # 测试示例
│   └── sensor_pack_2/       # 依赖包
├── package.json
├── README.md
└── LICENSE
```

## 依赖

- [`sensor_pack_2`](https://github.com/octaprog7/sensor_pack_2) — I2C 适配器与基类

## 快速开始

```python
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
import ens160sciosense

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400_000)
adapter = I2cAdapter(i2c)
sensor = ens160sciosense.Ens160(adapter, address=0x52)

sensor.start_measurement(start=True)

import time
time.sleep_ms(sensor.get_conversion_cycle_time())

while True:
    data = next(sensor)
    if data:
        print("eCO2:", data.eco2, "ppm  TVOC:", data.tvoc, "ppb  AQI:", data.aqi)
    time.sleep_ms(1000)
```

## API 参考

### 构造函数

```python
Ens160(adapter, address=0x52, check_crc=True)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `adapter` | `I2cAdapter` | I2C 适配器实例 |
| `address` | `int` | I2C 地址，0x52 或 0x53 |
| `check_crc` | `bool` | 是否启用 CRC 校验，默认 True |

### 主要方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_id()` | `int` | 读取 Part Number（期望值 0x0160） |
| `soft_reset()` | — | 软件复位 |
| `start_measurement(start=True)` | — | 启动/暂停连续测量 |
| `get_measurement_value(index)` | `int` / `ens160_air_params` | 0=eCO2, 1=TVOC, 2=AQI, None=全部 |
| `get_data_status(raw=True)` | `int` / `ens160_status` | 读取数据就绪状态 |
| `get_config(raw=True)` | `int` / `ens160_config` | 读取中断配置 |
| `set_config(cfg)` | — | 写入中断配置，接受 int 或 ens160_config |
| `set_ambient_temp(celsius)` | — | 写入温度补偿值（°C） |
| `set_humidity(rh)` | — | 写入湿度补偿值（%，0–100） |
| `get_firmware_version()` | `ens160_firmware_version` | 读取固件版本 |
| `get_conversion_cycle_time()` | `int` | 返回测量周期（ms），固定 1000 |
| `is_continuously_mode()` | `bool` | 是否处于连续测量模式 |
| `__next__()` | `ens160_air_params` / `None` | 迭代器，新数据就绪时返回测量值 |

### 数据结构

```python
ens160_air_params(eco2, tvoc, aqi)
# eco2: eCO2 浓度 [ppm]
# tvoc: TVOC 浓度 [ppb]
# aqi:  空气质量指数 1(优秀)..5(极差)

ens160_status(stat_as, stat_error, validity_flag, new_data, new_gpr)
ens160_config(int_pol, int_cfg, int_gpr, int_dat, int_en)
ens160_firmware_version(major, minor, release)
```

### 温湿度补偿

ENS160 支持外部温湿度补偿以提高测量精度：

```python
sensor.set_ambient_temp(25.0)   # 摄氏度
sensor.set_humidity(50)          # 相对湿度 %
```

## AQI 等级说明

| AQI | 等级 | eCO2 范围 |
|-----|------|-----------|
| 1 | 优秀 | 400–600 ppm |
| 2 | 良好 | 600–800 ppm |
| 3 | 中等 | 800–1000 ppm |
| 4 | 较差 | 1000–1500 ppm |
| 5 | 极差 | > 1500 ppm |

## License

MIT License. Copyright (c) 2022 Roman Shevchik, 2026 FreakStudio.
