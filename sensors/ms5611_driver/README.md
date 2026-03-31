# MS5611 的压力温度传感器

# MS5611 的压力温度传感器

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

本项目是 **NXP MS5611 高精度气压 / 温度传感器** 的 MicroPython 驱动实现，支持温度和压力独立过采样率配置，内置传感器校准参数读取与低温补偿算法，可输出高精度温度（℃）和气压（KPa）数据。驱动参考自 [MicroPython_MS5611](https://github.com/jposada202020/MicroPython_MS5611)，基于 MIT 协议开源，兼容 MicroPython v1.23.0，专为 Raspberry Pi Pico（RP2040）等硬件优化。

---

## 主要功能

- ✅ **I2C 通信**：支持 400kHz 高速 I2C，自动检测传感器地址（0x76/0x77，由 CSB 引脚电平决定）
- ✅ **过采样率配置**：温度和压力独立支持 5 档过采样率（256/512/1024/2048/4096），平衡测量精度与速度
- ✅ **高精度测量**：

  - 温度：范围 -40℃ ~ +85℃，精度 0.01℃
  - 气压：范围 10 ~ 1200 mBar，精度 0.01 KPa
- ✅ **校准补偿**：内置传感器 Factory Calibration 数据读取，实现温度补偿与低温补偿算法，提升测量稳定性
- ✅ **异常处理封装**：提供 `safe_read_measurements`、`safe_set_oversample_rate` 等函数，统一处理 I2C 通信异常与参数错误
- ✅ **数据统计**：支持测量数据平均值、波动值、最大值 / 最小值计算
- ✅ **参数校验**：初始化与配置时校验参数合法性，避免无效设置

---

## 硬件要求

- **主控平台**：搭载 MicroPython v1.23.0 的开发板（推荐 Raspberry Pi Pico/RP2040）
- **传感器模块**：NXP MS5611 气压 / 温度传感器
- **通信方式**：I2C 总线（RP2040 推荐配置：SDA=GPIO4，SCL=GPIO5，通信频率 400kHz）
- **供电要求**：**3.3V 直流供电**，严禁接入 5V 避免损坏传感器
- **I2C 地址**：

  - CSB 引脚接 GND：地址 0x76
  - CSB 引脚接 VCC：地址 0x77

---

## 文件说明

---

## 软件设计核心思想

**辅助层抽象**：通过 `CBits` 类实现寄存器特定位段的读写，`RegisterStruct` 类实现结构化寄存器数据的打包 / 解包，简化底层 I2C 操作

**属性化配置**：使用 Python `@property` 和 `@setter` 装饰器管理温度 / 压力过采样率，接口直观易用，无需直接操作寄存器

**校准补偿机制**：初始化时读取传感器 Factory Calibration 数据，测量时基于校准参数实现温度补偿与低温补偿，确保高精度输出

**异常安全封装**：`safe_*` 系列函数统一捕获 I2C 通信异常、参数错误与传感器异常，提升程序健壮性

**灵活配置**：温度与压力过采样率独立配置，支持低精度高速（256）到高精度低速（4096）的多场景适配

**数据就绪保障**：测量时通过 I2C 命令触发转换，等待转换完成后读取数据，避免无效值

---

## 使用说明

### 文件部署

将 `ms5611.py` 复制到 MicroPython 设备文件系统（若使用示例程序，同时复制 `main.py`）

### 初始化 I2C 总线

```
from machine import Pin, I2C
# Raspberry Pi Pico I2C0 配置
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
```

### 创建传感器实例

```
from ms5611 import MS5611

# 初始化传感器（CSB 接 VCC，地址 0x77；若接 GND 则为 0x76）
ms_sensor = MS5611(i2c, address=0x77)
```

### 配置过采样率

```
# 设置温度过采样率为 4096（最高精度）
ms_sensor.temperature_oversample_rate = MS5611.TEMP_OSR_4096
# 设置压力过采样率为 4096（最高精度）
ms_sensor.pressure_oversample_rate = MS5611.PRESS_OSR_4096
```

### 读取测量数据

```
# 读取温度（℃）和气压（KPa）
temperature, pressure = ms_sensor.measurements
print(f"Temperature: {temperature:.2f}°C, Pressure: {pressure:.2f}KPa")
```

### 异常处理

```
from ms5611 import MS5611

def safe_read(sensor):try:return sensor.measurements, Trueexcept OSError as e:print(f"I2C Error: {e}")return (0.0, 0.0), False(temp, press), success = safe_read(ms_sensor)if success:print(f"Temp: {temp:.2f}°C, Press: {press:.2f}KPa")
```

---

## 示例程序

`main.py` 包含 4 个核心演示模块：

**温度过采样率配置**：固定压力 OSR=4096，遍历所有温度 OSR 档位，连续测量 3 次

**压力过采样率配置**：固定温度 OSR=4096，遍历所有压力 OSR 档位，连续测量 3 次

**组合过采样率演示**：测试低（256）、中（1024）、高（4096）精度组合，计算 5 次测量的平均值与波动值

**最高精度连续测量**：恢复最高精度配置（OSR=4096），连续测量 10 次，输出最终配置与数据

---

## 注意事项

**供电安全**：MS5611 为 3.3V 器件，接入 5V 会永久损坏传感器

**过采样率影响**：过采样率越高，测量精度越高但转换时间越长（如 OSR=4096 需约 10ms 转换时间），测量间隔需匹配（示例中 0.3~1.0s 延迟）

**I2C 地址**：传感器地址由 CSB 引脚电平决定，初始化前需确认硬件连接

**低温补偿**：当温度 < 20℃ 时自动启用低温补偿算法，避免低温下测量漂移

**校准依赖**：传感器 Factory Calibration 数据存储在 PROM 中，初始化时必须成功读取，否则测量无效

**异常处理**：推荐使用 `safe_read_measurements` 等封装函数，避免 I2C 通信中断导致程序崩溃

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源许可协议，可自由使用、修改与分发，完整协议内容见 `LICENSE` 文件。
