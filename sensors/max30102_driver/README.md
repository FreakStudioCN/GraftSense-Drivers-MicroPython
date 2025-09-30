# MAX30102 心率与PPG传感器驱动 - MicroPython版本

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

---

## 简介
MAX30102 是一款集成红外和红光 LED 的心率与血氧传感器，广泛应用于健康监测、可穿戴设备等领域。本项目提供 MicroPython 驱动及示例，支持心率、PPG 采集与温度读取，便于开发者快速集成到树莓派 Pico 等开发板。

---

## 主要功能
- **心率与PPG采集**：支持 RED/IR/GREEN 通道数据读取
- **温度测量**：芯片内置温度传感器
- **多参数配置**：LED电流、采样率、FIFO平均等可灵活设置
- **环形缓冲区**：高效管理采集数据
- **心率计算示例**：集成简易心率计算器
- **异常处理**：参数校验与错误提示

---

## 硬件要求
### 推荐测试硬件
- 树莓派 Pico/Pico W
- MAX30102 传感器模块
- 杜邦线若干

### 模块引脚说明
| MAX30102 引脚 | 功能描述 |
|--------------|----------|
| VCC          | 电源正极（3.3V） |
| GND          | 电源负极 |
| SDA          | I2C数据 |
| SCL          | I2C时钟 |
| INT          | 中断输出（可选） |

---

## 文件说明
### main.py
主程序，演示心率与温度采集及心率计算。

### heartratemonitor.py
驱动核心，包含 MAX30102 类、心率计算器、环形缓冲区等。
#### 类定义
```python
class MAX30102(object):
    """
    MAX30102/MAX30105 传感器 I2C 驱动（寄存器配置、FIFO 读取、温度读取等）。

    Attributes:
        i2c_address (int): I2C 地址（7 位）。
        _i2c (I2C): MicroPython I2C 实例。
        _active_leds (int|None): 当前启用的 LED 数量（1~3）。
        _pulse_width (int|None): 当前脉宽编码（寄存器位值）。
        _multi_led_read_mode (int|None): 每次 FIFO 读取的字节数（active_leds*3）。
        _sample_rate (int|None): 采样率（SPS）。
        _sample_avg (int|None): FIFO 内部平均的样本数。
        _acq_frequency (float|None): 有效采集频率（_sample_rate/_sample_avg）。
        _acq_frequency_inv (int|None): 建议读取间隔（ms）。
        sense (SensorData): 各通道环形缓存。

    Methods:
        setup_sensor(...): 一次性按常用配置初始化。
        soft_reset(): 软复位。
        shutdown()/wakeup(): 掉电/唤醒。
        set_led_mode()/set_adc_range()/set_sample_rate()/set_pulse_width(): 基本配置。
        set_pulse_amplitude_*(): LED 电流设置。
        set_fifo_average()/enable_fifo_rollover()/clear_fifo(): FIFO 管理。
        get_write_pointer()/get_read_pointer(): FIFO 指针读。
        read_temperature(): 读芯片温度。
        read_part_id()/check_part_id()/get_revision_id(): 器件信息。
        enable_slot()/disable_slots(): 多路 LED 时间槽配置。
        check()/safe_check(): 轮询新数据。

    Notes:
        - 本驱动未改动核心业务逻辑，仅补齐注释与文档；
        - "set_pulse_amplitude_it" 方法名沿用原代码（IR 电流），未更名以避免影响业务；
        - I2C 读写可能抛出 OSError（如 ETIMEDOUT）。

    =========================================
    I2C driver for MAX30102/30105 (register/config/FIFO/temperature, etc.).

    Attributes:
        i2c_address (int): 7-bit I2C address.
        _i2c (I2C): MicroPython I2C instance.
        _active_leds (int|None): Number of active LEDs (1..3).
        _pulse_width (int|None): Encoded pulse width (register value).
        _multi_led_read_mode (int|None): Bytes per FIFO read (active_leds*3).
        _sample_rate (int|None): Sample rate in SPS.
        _sample_avg (int|None): FIFO on-chip averaging.
        _acq_frequency (float|None): Effective acquisition rate.
        _acq_frequency_inv (int|None): Suggested read interval (ms).
        sense (SensorData): Channel ring buffers.

    Methods:
        setup_sensor(...): Initialize once with common configurations.
        soft_reset(): Soft reset.
        shutdown()/wakeup(): Power down/wake up.
        set_led_mode()/set_adc_range()/set_sample_rate()/set_pulse_width(): Basic configurations.
        set_pulse_amplitude_*(): LED current setting.
        set_fifo_average()/enable_fifo_rollover()/clear_fifo(): FIFO management.
        get_write_pointer()/get_read_pointer(): FIFO pointer reading.
        read_temperature(): Read chip temperature.
        read_part_id()/

    Notes:
        - Core logic unchanged; only documentation/comments were added;
        - The method name "set_pulse_amplitude_it" is kept as-is (IR current);
        - I2C ops may raise OSError (e.g., ETIMEDOUT).
    """

    def __init__(self, i2c: I2C, i2c_hex_address=MAX3010X_I2C_ADDRESS):
class SensorData:
    """
    传感器数据缓存（环形队列）。

    Attributes:
        red (CircularBuffer): 红光通道缓存。
        IR (CircularBuffer): 红外通道缓存。
        green (CircularBuffer): 绿光通道缓存。

    =========================================
    Sensor data container backed by ring buffers.

    Attributes:
        red (CircularBuffer): Red channel buffer.
        IR (CircularBuffer): Infrared channel buffer.
        green (CircularBuffer): Green channel buffer.
    """

    def __init__(self):
class HeartRateMonitor:
    """
    简易心率监测器：对输入样本做滑动窗口平滑与阈值峰值检测，估计 BPM。

    Attributes:
        sample_rate (int): 采样率（Hz）。
        window_size (int): 峰值检测窗口大小（样本数）。
        smoothing_window (int): 平滑窗口大小（样本数）。
        samples (list[float]): 原始样本序列。
        timestamps (list[int]): 样本的时间戳（ms, 使用 time.ticks_ms）。
        filtered_samples (list[float]): 平滑后的样本序列。

    Methods:
        add_sample(sample): 添加一个样本并更新平滑序列。
        find_peaks(): 在平滑序列中查找峰值点。
        calculate_heart_rate(): 根据相邻峰值时间差计算 BPM。

    Notes:
        - 峰值阈值采用近期窗口的动态阈值（min/max 的 50% 中点）。
        - 需要至少两个峰值才能计算心率。

    =========================================
    A light-weight HR monitor performing moving-window smoothing and threshold
    peak detection to estimate BPM.

    Attributes:
        sample_rate (int): Sampling rate in Hz.
        window_size (int): Peak detection window length in samples.
        smoothing_window (int): Moving average window length.
        samples (list[float]): Raw samples.
        timestamps (list[int]): Sample timestamps in ms (time.ticks_ms).
        filtered_samples (list[float]): Smoothed samples.

    Methods:
        add_sample(sample): Append a sample and update the smoothed list.
        find_peaks(): Detect peaks on the smoothed series.
        calculate_heart_rate(): Compute BPM from peak intervals.

    Notes:
        - The threshold is 50% between min and max of the recent window.
        - At least two peaks are required to compute BPM.
    """

    def __init__(self, sample_rate=100, window_size=10, smoothing_window=5):
class CircularBuffer(object):
    """
    基于 deque 的简易环形缓冲区实现。

    Attributes:
        data (deque): 底层存储。
        max_size (int): 最大容量。

    Methods:
        append(item): 追加元素（满则丢弃最早元素）。
        pop(): 弹出最早元素。
        pop_head(): 弹出最新元素（注意：原实现含边界逻辑）。
        clear(): 清空。
        is_empty(): 是否为空。

    Notes:
        - 为保持与原代码逻辑一致，未更改 `pop_head` 的实现；其行为较非常规环形缓冲，使用时请注意。

    =========================================
    A minimal ring buffer backed by deque.

    Attributes:
        data (deque): Underlying storage.
        max_size (int): Capacity.

    Methods:
       append(item): Append an element (if full, discard the earliest element).
        pop(): Pop the earliest element.
        pop_head(): Pop the latest element (Note: The original implementation includes boundary logic).
        clear(): Clear all elements.
        is_empty(): Check if it is empty.

    Notes:
        - The original `pop_head` behavior is preserved verbatim; it is unusual
          for a ring buffer, so use with care.
    """

    def __init__(self, max_size):
```
---

## 软件设计核心思想

### 模块化设计
- 传感器驱动、心率计算、数据缓冲分离
- 统一接口，易于扩展和维护

### 数据采集与处理
- 支持多通道采集
- 环形缓冲区高效管理数据
- 采样率、平均数等参数可灵活配置

### 错误处理与兼容性
- 参数类型与范围校验
- 兼容 MicroPython 标准库

---

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| MAX30102 引脚 | Pico GPIO 引脚 |
|---------------|----------------|
| VCC           | 3.3V           |
| GND           | GND            |
| SDA           | GP4            |
| SCL           | GP5            |

> **注意：**
> - 确保 VCC 和 GND 接线正确
> - SDA/SCL 对应 I2C0 的 GP4/GP5
> - INT 可选连接，用于中断检测

---

### 软件依赖

- **固件版本**：MicroPython v1.19+
- **内置库**：
  - `machine`（I2C控制）
  - `time`（延时与计时）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `heartratemonitor.py` 和 `main.py` 到开发板
3. 根据硬件连接修改 `main.py` 中的 I2C 配置
4. 运行 `main.py`，开始心率与温度采集

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/16 18:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : MAX30102 心率与PPG读取+简易心率计算器示例

from machine import I2C, Pin
import time
from heartratemonitor import MAX30102, MAX30105_PULSE_AMP_MEDIUM, HeartRateMonitor

time.sleep(3)
print("FreakStudio: Use MAX30102 to read heart rate and temperature.")
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
sensor = MAX30102(i2c=i2c)
sensor.setup_sensor()
sensor.set_sample_rate(400)
sensor.set_fifo_average(8)
sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
actual_acquisition_rate = int(400 / 8)
hr_monitor = HeartRateMonitor(sample_rate=actual_acquisition_rate, window_size=int(actual_acquisition_rate * 3))
ref_time = time.ticks_ms()

while True:
    sensor.check()
    time.sleep(0.5)
    if sensor.available():
        red_reading = sensor.pop_red_from_storage()
        ir_reading = sensor.pop_ir_from_storage()
        temp_reading = sensor.read_temperature()
        print("RED: {}, IR: {}, TEMP: {:.2f}".format(red_reading, ir_reading, temp_reading))
        hr_monitor.add_sample(ir_reading)
    if time.ticks_diff(time.ticks_ms(), ref_time) / 1000 > 2:
        heart_rate = hr_monitor.calculate_heart_rate()
        if heart_rate is not None:
            print("Heart Rate: {:.0f} BPM".format(heart_rate))
        else:
            print("Not enough data to calculate heart rate")
        ref_time = time.ticks_ms()
```
## 注意事项
- 测量范围与精度
- 建议手指贴合传感器，避免环境光干扰
- 温度测量为芯片内部温度，仅供参考
## 参数配置
- 采样率、LED电流、平均数等参数需根据实际应用调整
- 建议使用稳定 3.3V 电源
- 避免电压波动影响测量

## 联系方式
- 如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：1098875044@qq.com  
💻 **GitHub**：[https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython]

---

## 许可协议
- 本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用**知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  

**版权归 FreakStudio 所有。**
