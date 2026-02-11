# GraftSense MAX30102 心率血氧传感器模块 （MicroPython）

# GraftSense MAX30102 心率血氧传感器模块 （MicroPython）

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本项目为 **GraftSense MAX30102 心率血氧传感器模块 V1.0** 提供了完整的 MicroPython 驱动支持，基于 MAX30102 高精度光学测量芯片，实现心率（HR）、血氧饱和度（SpO₂）检测、PPG（光电容积脉搏波）数据采集与芯片温度读取功能。模块遵循 Grove 接口标准，通过 I2C 通信（默认地址 0x57），兼容 3.3V 系统电平，内置电源转换与滤波电路，适用于可穿戴健康监测、生命体征实验、嵌入式健康设备等场景，具备高精度光学测量、接口易于连接的优势。

---

## 主要功能

- ✅ **高精度生理检测**：通过红光 / 红外光对射检测，精准采集 PPG 数据，支持心率（峰值检测）与血氧饱和度计算
- ✅ **芯片温度读取**：内置 Die Temperature 传感器，可实时读取芯片工作温度（单位：℃）
- ✅ **I2C 通信控制**：支持标准 I2C 通信速率（最高 400kHz），默认地址 0x57，可通过地址引脚配置多模块级联
- ✅ **多通道数据缓存**：基于环形缓冲区管理红光（RED）、红外（IR）、绿光（GREEN）通道数据，避免 FIFO 溢出
- ✅ **灵活参数配置**：支持采样率（50–3200 SPS）、LED 电流（0x02–0xFF）、FIFO 平均样本数（1–32）、脉冲宽度（69–411 μs）等参数调节
- ✅ **低功耗模式**：支持软复位、掉电（shutdown）与唤醒（wakeup）模式，适配可穿戴设备低功耗需求
- ✅ **峰值检测心率计算**：通过滑动窗口平滑与动态阈值峰值检测，实现简易心率（BPM）计算

---

## 硬件要求

1. **核心硬件**：GraftSense MAX30102 心率血氧传感器模块 V1.0（内置 MAX30102 芯片、3.3V/1.8V 电平转换电路、电源滤波与指示灯）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等，3.3V 电平兼容）
3. **接线方式**：

   - **Grove 接口**：模块左侧 Grove 接口 → 主控板 Grove I2C 接口（SDA/SCL、VCC/GND）
   - **杜邦线连接**：模块 SDA → 主控 SDA（如 Raspberry Pi Pico GP4），模块 SCL → 主控 SCL（如 GP5），模块 VCC → 3.3V，模块 GND → GND
4. **检测配件**：手指 / 耳垂贴合模块光学窗口（确保红光 / 红外光有效穿透组织，避免光线泄漏）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **面向对象分层封装**：

   - `MAX30102` 类：负责硬件抽象，封装 I2C 寄存器读写、FIFO 数据管理、模式配置等底层操作
   - `HeartRateMonitor` 类：负责数据处理，实现 PPG 数据平滑、峰值检测与心率计算
   - `CircularBuffer` 类：负责数据缓存，通过 deque 实现环形缓冲，避免 FIFO 数据丢失
2. **I2C 通信抽象**：通过 `machine.I2C` 实现底层通信，解耦硬件依赖，支持多平台移植，同时处理 OSError 等通信异常
3. **参数校验与容错**：对采样率、LED 模式、脉冲宽度等参数进行范围校验，避免无效配置导致硬件异常；环形缓冲区满时自动丢弃最早数据，保证数据连续性
4. **状态同步管理**：内部维护采样率、LED 模式等状态变量，确保配置与硬件状态一致；软复位后自动恢复默认配置
5. **低功耗优化**：支持掉电（shutdown）与唤醒（wakeup）模式，析构函数自动进入低功耗，减少待机功耗

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件（如 Raspberry Pi Pico 可使用官方固件）
- 将 `max30102.py`、`heartratemonitor.py`、`circular_buffer.py`、`heart_rate.py`（或 `basic_usage.py`）上传至开发板文件系统

### 硬件连接

1. 模块 Grove 接口 → 主控板 Grove I2C 接口（或通过杜邦线连接 SDA/SCL/VCC/GND）
2. 确保模块光学窗口与手指 / 耳垂紧密贴合，避免光线泄漏
3. 模块供电：3.3V（Grove 接口供电），无需额外外部电源转换

### 代码使用步骤

#### 步骤 1：初始化 I2C 与传感器

```python
from machine import I2C, Pin
import time
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from heartratemonitor import HeartRateMonitor

# 初始化 I2C（Raspberry Pi Pico 示例：I2C0，SDA=GP4，SCL=GP5，400kHz）
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# 扫描 I2C 总线，确认传感器连接
devices = i2c.scan()
if 0x57 not in devices:
    raise RuntimeError("MAX30102 sensor not found on I2C bus!")

# 创建传感器实例，初始化默认配置
sensor = MAX30102(i2c=i2c)
sensor.setup_sensor(
    led_mode=2,          # 红光 + 红外模式
    adc_range=16384,     # ADC 量程 16384
    sample_rate=400,     # 采样率 400 SPS
    led_power=MAX30105_PULSE_AMP_MEDIUM,  # LED 电流中档
    sample_avg=8,        # FIFO 平均 8 个样本
    pulse_width=411      # 脉冲宽度 411 μs
)

# 初始化心率监测器（采样率 = 400 / 8 = 50 Hz）
actual_rate = int(400 / 8)
hr_monitor = HeartRateMonitor(
    sample_rate=actual_rate,
    window_size=int(actual_rate * 3)  # 3 秒窗口
)
```

#### 步骤 2：读取 PPG 数据与温度

```python
ref_time = time.ticks_ms()
while True:
    # 轮询 FIFO 数据
    sensor.check()
    if sensor.available():
        red = sensor.pop_red_from_storage()
        ir = sensor.pop_ir_from_storage()
        temp = sensor.read_temperature()
        print(f"RED: {red}, IR: {ir}, TEMP: {temp:.2f}°C")
        
        # 添加样本到心率计算
        hr_monitor.add_sample(ir)
    
    # 每 2 秒计算一次心率
    if time.ticks_diff(time.ticks_ms(), ref_time) / 1000 > 2:
        hr = hr_monitor.calculate_heart_rate()
        if hr:
            print(f"Heart Rate: {hr:.0f} BPM")
        else:
            print("Not enough data for HR calculation")
        ref_time = time.ticks_ms()
    
    time.sleep(0.5)
```

---

## 示例程序

### 示例 1：心率 + PPG + 温度读取（heart_rate.py）

```
from machine import I2C, Pin
import time
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from heartratemonitor import HeartRateMonitor

time.sleep(3)
print("FreakStudio: Use MAX30102 to read heart rate and temperature.")

# 初始化 I2C
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
sensor = MAX30102(i2c=i2c)
sensor.setup_sensor()

# 设置采样率与 FIFO 平均
sensor.set_sample_rate(400)
sensor.set_fifo_average(8)
sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
actual_rate = int(400 / 8)

# 初始化心率监测器
hr_monitor = HeartRateMonitor(
    sample_rate=actual_rate,
    window_size=int(actual_rate * 3)
)
ref_time = time.ticks_ms()

while True:
    sensor.check()
    if sensor.available():
        red = sensor.pop_red_from_storage()
        ir = sensor.pop_ir_from_storage()
        temp = sensor.read_temperature()
        print(f"RED: {red}, IR: {ir}, TEMP: {temp:.2f}°C")
        hr_monitor.add_sample(ir)
    
    if time.ticks_diff(time.ticks_ms(), ref_time) / 1000 > 2:
        hr = hr_monitor.calculate_heart_rate()
        if hr:
            print(f"Heart Rate: {hr:.0f} BPM")
        else:
            print("Not enough data to calculate heart rate")
        ref_time = time.ticks_ms()
    
    time.sleep(0.5)
```

### 示例 2：基础 PPG 与温度读取（basic_usage.py）

```
from machine import SoftI2C, Pin
from time import ticks_diff, ticks_us
import time
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM

# 初始化 I2C
i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
sensor = MAX30102(i2c=i2c)

# 检查传感器连接
if sensor.i2c_address not in i2c.scan():
    print("Sensor not found.")
elif not sensor.check_part_id():
    print("I2C device ID not corresponding to MAX30102.")
else:
    print("Sensor connected and recognized.")

# 初始化传感器
sensor.setup_sensor()
sensor.set_sample_rate(400)
sensor.set_fifo_average(8)
sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
time.sleep(1)

# 读取温度
print("Temperature:", sensor.read_temperature(), "°C")

# 采集 PPG 数据
t_start = ticks_us()
samples_n = 0
while True:
    sensor.check()
    if sensor.available():
        red = sensor.pop_red_from_storage()
        ir = sensor.pop_ir_from_storage()
        print(red, ",", ir)
        
        # 计算采集频率
        if ticks_diff(ticks_us(), t_start) >= 999999:
            print("Acquisition frequency:", samples_n, "Hz")
            samples_n = 0
            t_start = ticks_us()
        else:
            samples_n += 1
    
    time.sleep(0.01)
```

---

## 注意事项

1. **检测位置要求**：确保手指 / 耳垂与模块光学窗口紧密贴合，避免光线泄漏，否则会导致 PPG 数据异常或检测失败
2. **运动干扰防护**：检测过程中避免剧烈运动，减少肌肉抖动对光学信号的干扰，建议保持静止 5–10 秒以获取稳定数据
3. **I2C 地址配置**：模块默认 I2C 地址为 0x57，通过 A2/A1/A0 引脚短接点可修改地址，多模块级联时需确保地址不冲突
4. **供电稳定性**：使用 3.3V 稳定电源供电，避免电压波动导致模块复位或数据异常；模块内置 5V→3.3V、3.3V→1.8V 电平转换，无需额外电源转换电路
5. **数据滤波建议**：原始 PPG 数据存在噪声，建议在应用层增加滑动平均、带通滤波等算法，提升心率与血氧计算精度
6. **医疗级限制**：本模块为教育 / 实验级设备，**不可用于医疗诊断**，仅作为健康监测参考数据
7. **I2C 通信异常处理**：I2C 读写可能抛出 OSError（如 ETIMEDOUT），建议在应用层增加重试机制，避免程序崩溃
8. **LED 电流设置**：LED 电流过高会增加功耗，过低会导致检测距离不足，建议根据使用场景选择合适的电流档位（如 MAX30105_PULSE_AMP_MEDIUM）

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源协议，具体内容如下：

```
MIT License

Copyright (c) 2025 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
