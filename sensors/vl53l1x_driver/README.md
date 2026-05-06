# VL53L1X MicroPython Driver

VL53L1X 是 ST 出品的激光测距传感器（ToF），支持 I2C 接口，测距范围最远 4m，精度 ±1mm。

## 硬件连接

| VL53L1X 引脚 | ESP32 引脚 |
|-------------|-----------|
| VCC         | 3.3V      |
| GND         | GND       |
| SDA         | GPIO4     |
| SCL         | GPIO5     |

## 快速开始

```python
from machine import Pin, SoftI2C
from vl53l1x import VL53L1X
import time

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400_000)
sensor = VL53L1X(i2c=i2c, address=0x29)

while True:
    print("range: %d mm" % sensor.read())
    time.sleep_ms(50)

sensor.deinit()
```

## API

### 构造函数

```python
VL53L1X(i2c, address=0x29)
```

- `i2c`：MicroPython I2C 总线实例
- `address`：I2C 地址，默认 `0x29`

### 主要方法

| 方法 | 说明 |
|------|------|
| `read()` | 读取当前测距结果（mm） |
| `read_model_id()` | 读取型号 ID，应为 `0xEACC` |
| `reset()` | 软件复位传感器 |
| `write_reg(reg, value)` | 写入单字节寄存器 |
| `write_reg_16bit(reg, value)` | 写入 16 位寄存器（大端序） |
| `read_reg(reg)` | 读取单字节寄存器 |
| `read_reg_16bit(reg)` | 读取 16 位寄存器（大端序） |
| `deinit()` | 停止测距，传感器进入待机 |

### 注意事项

- 初始化时自动写入 ST 官方默认配置并启动测距
- `read()` 返回经串扰校正的最终距离值
- 完整的 range_status 状态解析请参考 ST VL53L1X ULD API

## License

MIT
