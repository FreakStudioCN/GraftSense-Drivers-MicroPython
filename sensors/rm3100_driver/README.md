# RM3100 MicroPython Driver

RM3100 是 PNI Sensor 出品的高精度三轴地磁传感器，支持 I2C 接口，内置自检功能，支持单次/连续测量模式。

## 硬件连接

| RM3100 引脚 | ESP32 引脚 |
|------------|-----------|
| VCC        | 3.3V      |
| GND        | GND       |
| SDA        | GPIO4     |
| SCL        | GPIO5     |
| ADDR0/1    | GND（地址 0x20）|

## 依赖

- [sensor_pack](https://github.com/octaprog7/sensor_pack)

## 快速开始

```python
from machine import Pin, SoftI2C
from sensor_pack.bus_service import I2cAdapter
from rm3100mod import RM3100, get_conversion_cycle_time
import time

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400_000)
sensor = RM3100(I2cAdapter(i2c), address=0x20)

sensor.start_measure(axis="XYZ", update_rate=6, single_mode=True)
time.sleep_us(get_conversion_cycle_time(6))
if sensor.is_data_ready():
    for axis in "XYZ":
        print("%s: %d" % (axis, sensor.get_meas_result(axis)))

sensor.deinit()
```

## API

### 构造函数

```python
RM3100(adapter, address=0x20)
```

- `adapter`：`BusAdapter` 实例（`I2cAdapter`）
- `address`：I2C 地址，范围 `0x20~0x23`

### 主要方法

| 方法 | 说明 |
|------|------|
| `get_id()` | 读取芯片版本 ID |
| `start_measure(axis, update_rate, single_mode, full_meas_seq)` | 启动测量 |
| `get_meas_result(axis)` | 读取指定轴测量结果 |
| `is_data_ready()` | 判断数据是否就绪 |
| `is_continuous_meas_mode()` | 判断是否为连续测量模式 |
| `is_single_meas_mode()` | 判断是否为单次测量模式 |
| `get_axis_cycle_count(axis_name)` | 读取指定轴周期计数 |
| `set_axis_cycle_count(axis_name, value)` | 设置指定轴周期计数 |
| `perform_self_test()` | 执行内置自检 |
| `setup()` | 配置 DRC 寄存器 |
| `deinit()` | 停止测量，释放资源 |

### 模块级函数

| 函数 | 说明 |
|------|------|
| `get_conversion_cycle_time(update_rate)` | 返回转换周期时间（微秒） |

### 更新率对照表

| update_rate | 频率 | 周期时间 |
|-------------|------|---------|
| 0  | ~600 Hz   | 1,667 µs      |
| 1  | ~300 Hz   | 3,334 µs      |
| 6  | ~9.4 Hz   | 106,688 µs    |
| 13 | ~0.075 Hz | 13,655,040 µs |

### 自检返回值

```python
(z_ok, y_ok, x_ok, timeout_period, lr_periods)
```

## License

MIT
