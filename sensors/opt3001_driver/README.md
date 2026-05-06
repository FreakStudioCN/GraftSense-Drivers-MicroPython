# OPT3001 MicroPython Driver

OPT3001 是 TI 出品的环境光传感器（ALS），支持 I2C 接口，量程 0.01~83865.60 lux，支持自动量程选择。

## 硬件连接

| OPT3001 引脚 | ESP32 引脚 |
|-------------|-----------|
| VCC         | 3.3V      |
| GND         | GND       |
| SDA         | GPIO4     |
| SCL         | GPIO5     |
| ADDR        | GND（地址 0x44）|

## 依赖

- [sensor_pack_2](https://github.com/octaprog7/sensor_pack_2)

## 快速开始

```python
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from opt3001mod import OPT3001

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100_000)
sensor = OPT3001(I2cAdapter(i2c), address=0x44)

# 单次测量
sensor.start_measurement(continuously=False, lx_range_index=12)
import time; time.sleep_ms(150)
ds = sensor.get_data_status()
if ds.conversion_ready:
    result = sensor.get_measurement_value(value_index=1)
    print("Lux:", result.lux)

sensor.deinit()
```

## API

### 构造函数

```python
OPT3001(adapter, address=0x44)
```

- `adapter`：`BusAdapter` 实例（`I2cAdapter`）
- `address`：I2C 地址，范围 `0x44~0x47`

### 主要方法

| 方法 | 说明 |
|------|------|
| `get_id()` | 读取制造商 ID 和设备 ID，返回 `opt3001_id` |
| `start_measurement(continuously, lx_range_index, refresh)` | 配置并启动测量 |
| `get_measurement_value(value_index)` | 读取测量结果（0=原始，1=lux） |
| `get_data_status()` | 读取转换就绪和溢出状态 |
| `get_conversion_cycle_time()` | 获取当前转换周期（ms） |
| `read_config_from_sensor(return_value)` | 从传感器刷新配置缓存 |
| `write_config_to_sensor()` | 将缓存配置写入传感器 |
| `is_single_shot_mode()` | 是否为单次测量模式 |
| `is_continuously_mode()` | 是否为连续测量模式 |
| `deinit()` | 停止测量，进入省电模式 |

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `lux_range_index` | int | 量程索引 0~12（12=自动） |
| `long_conversion_time` | bool | False=100ms，True=800ms |
| `mode` | int | 0=省电，1=单次，2/3=连续 |
| `overflow` | bool | 溢出标志（只读） |
| `conversion_ready` | bool | 转换就绪标志（只读） |
| `flag_high` | bool | 高阈值标志（只读） |
| `flag_low` | bool | 低阈值标志（只读） |
| `latch` | bool | 锁存模式 |
| `polarity` | bool | INT 引脚极性 |
| `mask_exponent` | bool | 指数屏蔽位 |
| `fault_count` | int | 故障计数 |

### 返回数据类型

```python
opt3001_id(manufacturer_id, device_id)
opt3001_meas_raw(exponent, fractional)
opt3001_meas_data(lux, full_scale_range)
OPT3001_data_status(conversion_ready, overflow)
```

## 量程索引对照表

| 索引 | 满量程 (lux) | LSB (lux) |
|------|------------|-----------|
| 0    | 40.95      | 0.01      |
| 1    | 81.90      | 0.02      |
| 2    | 163.80     | 0.04      |
| 3    | 327.60     | 0.08      |
| 4    | 655.20     | 0.16      |
| 5    | 1310.40    | 0.32      |
| 6    | 2620.80    | 0.64      |
| 7    | 5241.60    | 1.28      |
| 8    | 10483.20   | 2.56      |
| 9    | 20966.40   | 5.12      |
| 10   | 41932.80   | 10.24     |
| 11   | 83865.60   | 20.48     |
| 12   | 自动量程    | —         |

## License

MIT
