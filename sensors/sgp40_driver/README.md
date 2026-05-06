# SGP40/SGP41 MicroPython Driver

SGP40/SGP41 是 Sensirion 出品的数字空气质量传感器，支持 I2C 接口。SGP40 测量 VOC 原始信号，SGP41 同时测量 VOC 和 NOx 原始信号。

## 硬件连接

| SGP40/41 引脚 | ESP32 引脚 |
|--------------|-----------|
| VCC          | 3.3V      |
| GND          | GND       |
| SDA          | GPIO4     |
| SCL          | GPIO5     |

## 依赖

- [sensor_pack_2](https://github.com/octaprog7/sensor_pack_2)

## 快速开始

```python
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from sgp4Xmod import SGP4X
import time

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100_000)
sensor = SGP4X(I2cAdapter(i2c), address=0x59, sensor_id=0)

while True:
    val = sensor.measure_raw_signal(rel_hum=50, temperature=25)
    print("VOC raw:", val.VOC)
    time.sleep_ms(1000)

sensor.deinit()
```

## API

### 构造函数

```python
SGP4X(adapter, address=0x59, sensor_id=0, check_crc=True)
```

- `adapter`：`BusAdapter` 实例（`I2cAdapter`）
- `address`：I2C 地址，固定为 `0x59`
- `sensor_id`：`0`=SGP40，`1`=SGP41
- `check_crc`：是否校验响应 CRC，默认 `True`

### 主要方法

| 方法 | 说明 |
|------|------|
| `get_id()` | 读取传感器序列号 |
| `get_sensor_id()` | 返回传感器型号（0=SGP40，1=SGP41） |
| `execute_self_test()` | 内置自检，返回 `0xD400`（通过）或 `0x4B00`（失败） |
| `execute_conditioning(rel_hum, temperature)` | SGP41 预热调节（仅 SGP41，建议 10s） |
| `measure_raw_signal(rel_hum, temperature)` | 启动/继续测量，返回 VOC（及 NOx）原始信号 |
| `turn_heater_off()` | 关闭加热器，进入待机模式 |
| `deinit()` | 释放资源，关闭加热器 |

### 返回数据类型

```python
serial_number_sgp4x(word_0, word_1, word_2)
measured_values_sgp4x(VOC, NOx)   # SGP40 时 NOx=None
```

### 注意事项

- 原始信号需通过 Sensirion Gas Index Algorithm 转换为 VOC/NOx 指数
- SGP41 `execute_conditioning` 建议执行 10 秒，不得超过 10 秒
- 连续测量建议每秒调用一次 `measure_raw_signal`，不关闭加热器

## License

MIT
