# cs1237_driver

# cs1237_driver

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

`cs1237_driver` 是一个用于控制 **CS1237 24 位高精度 ADC 芯片** 的 MicroPython 库，专为嵌入式信号采集场景设计，可在各类 MicroPython 固件上运行，实现低成本、高精度的模拟信号数字化采集。

---

## 主要功能

- 支持 CS1237 芯片的 SPI 通信与数据读取
- 提供简洁的 API 接口，便于快速集成到项目中
- 兼容所有支持 MicroPython 的芯片与固件
- 支持 24 位高精度 ADC 数据转换与处理
- 代码轻量、无额外依赖，适合资源受限的嵌入式环境

---

## 硬件要求

- 主控芯片：任意支持 MicroPython 的开发板（如 ESP32、RP2040、STM32 等）
- 外设芯片：CS1237 24 位 ADC 芯片
- 连接方式：通过 SPI 接口（CLK、DOUT）与主控连接
- 电源：3.3V 或 5V 供电（根据 CS1237 硬件设计要求）

---

## 文件说明

## 软件设计核心思想

- **极简设计**：仅保留 CS1237 芯片核心功能，避免冗余代码，确保运行效率
- **硬件无关**：通过抽象 SPI 通信接口，兼容不同主控的 MicroPython 实现
- **易用性优先**：提供直观的 API，降低嵌入式开发者的使用门槛
- **可移植性**：代码结构清晰，无平台特定依赖，便于在不同硬件平台间迁移

---

## 使用说明

1. 将 `cs1237.py` 文件复制到 MicroPython 设备的文件系统中
2. 在你的项目代码中导入 `CS1237` 类
3. 初始化 SPI 接口与 CS1237 驱动实例
4. 调用 `read()` 方法获取 ADC 原始数据或转换后的值

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/17 下午4:52
# @Author  : hogeiha
# @File    : main.py
# @Description : CS1237/CS1238系列ADC芯片驱动使用示例，涵盖基础读取、缓冲读取、温度校准、电源管理等功能

# ======================================== 导入相关模块 =========================================

# 导入数组模块，用于缓冲数据存储
import array

# 导入时间模块，用于延时操作
import time

# 导入Pin类，用于硬件引脚控制
from machine import Pin

# 导入CS1237系列ADC驱动类（需确保cs1237.py与当前文件同目录）
from cs1237 import CS1237

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def demo_cs1237_basic():
    """
    CS1237基础使用示例，包括芯片初始化、配置读取、数据读取、配置修改
    Args:无

    Raises:
        ValueError: 参数值无效时抛出
        TypeError: 参数类型错误时抛出
        OSError: 传感器无响应时抛出

    Notes:
        演示基础的ADC数据读取流程，包含配置修改前后的对比验证

    ==========================================
    Basic usage example of CS1237, including chip initialization, configuration reading, data reading and configuration modification
    Args:None

    Raises:
        ValueError: Raised when parameter value is invalid
        TypeError: Raised when parameter type is incorrect
        OSError: Raised when sensor does not respond

    Notes:
        Demonstrates the basic ADC data reading process, including comparative verification before and after configuration modification
    """
    print("
=== CS1237 Basic Read Example ===")
    try:
        # 初始化芯片（增益64，采样率10Hz，通道0）
        adc = CS1237(clock=CLK_PIN, data=DATA_PIN, gain=64, rate=10, channel=0)
        print(f"Chip initialization configuration: {adc}")

        # 获取当前配置
        gain, rate, channel = adc.get_config()
        print(f"Current configuration - Gain: {gain}, Sample rate: {rate}Hz, Channel: {channel}")

        # 循环读取数据（5次）
        print("Start reading ADC data：")
        for i in range(5):
            try:
                value = adc.read()  # 读取24位有符号数据
                print(f"Read {i + 1} times: {value}")
                time.sleep(0.5)
            except OSError as e:
                print(f"Read failed: {e}")

        # 修改配置（增益改为128，采样率改为40Hz）
        print("
Modify configuration (Gain 128, Sample rate 40Hz)...")
        adc.config(gain=128, rate=40)
        gain, rate, channel = adc.get_config()
        print(f"Modified configuration - Gain: {gain}, Sample rate: {rate}Hz, Channel: {channel}")

        # 再次读取验证
        value = adc.read()
        print(f"Read value under new configuration: {value}")

    except (ValueError, TypeError, OSError) as e:
        print(f"Initialization/Read failed: {e}")


def demo_buffered_read():
    """
    缓冲批量读取示例，实现一次性读取多个ADC数据并存储到数组缓冲区
    Args:无

    Raises:
        ValueError: 参数值无效时抛出
        TypeError: 参数类型错误时抛出
        OSError: 传感器无响应时抛出

    Notes:
        通过data_acquired标志位轮询判断缓冲读取是否完成，适用于批量数据采集场景

    ==========================================
    Buffered batch read example, realizes reading multiple ADC data at one time and storing them in array buffer
    Args:None

    Raises:
        ValueError: Raised when parameter value is invalid
        TypeError: Raised when parameter type is incorrect
        OSError: Raised when sensor does not respond

    Notes:
        Poll the data_acquired flag to determine whether the buffered reading is completed, suitable for batch data acquisition scenarios
    """
    print("
=== Buffered Batch Read Example ===")
    try:
        adc = CS1237(CLK_PIN, DATA_PIN)
        # 创建缓冲区（存储10个数据，类型为int）
        buffer = array.array("i", [0] * 10)

        # 启动缓冲读取
        print("Start buffered reading 10 data...")
        adc.read_buffered(buffer)

        # 等待数据读取完成（轮询标志位）
        while not adc.data_acquired:
            time.sleep(0.01)

        # 打印缓冲数据
        print("Buffered read results:")
        for idx, val in enumerate(buffer):
            print(f"Data {idx + 1}: {val}")

    except (ValueError, TypeError, OSError) as e:
        print(f"Buffered read failed: {e}")


def demo_temperature_calibration():
    """
    温度校准与读取示例，实现ADC芯片的温度校准和实时温度读取
    Args:无

    Raises:
        ValueError: 参数值无效时抛出
        TypeError: 参数类型错误时抛出
        OSError: 传感器无响应时抛出

    Notes:
        温度校准需在稳定环境温度下执行，校准后才能获取准确的温度值

    ==========================================
    Temperature calibration and reading example, realizes temperature calibration and real-time temperature reading of ADC chip
    Args:None

    Raises:
        ValueError: Raised when parameter value is invalid
        TypeError: Raised when parameter type is incorrect
        OSError: Raised when sensor does not respond

    Notes:
        Temperature calibration must be performed at a stable ambient temperature to obtain accurate temperature values after calibration
    """
    print("
=== Temperature Calibration and Read Example ===")
    try:
        adc = CS1237(CLK_PIN, DATA_PIN)

        # 步骤1：温度校准（假设当前环境温度25℃，自动读取参考值）
        print("Start temperature calibration (Current temperature 25℃)...")
        adc.calibrate_temperature(temp=25.0)  # ref_value=None时自动读取
        print(f"Calibration reference value: {adc.ref_value}, Reference temperature: {adc.ref_temp}℃")

        # 步骤2：读取当前温度
        print("Read current temperature...")
        for i in range(3):
            try:
                temp = adc.temperature()
                print(f"Temperature read {i + 1} times: {temp:.2f}℃")
                time.sleep(0.5)
            except OSError as e:
                print(f"Temperature read failed: {e}")

    except (ValueError, TypeError, OSError) as e:
        print(f"Temperature function failed: {e}")


def demo_power_management():
    """
    电源管理示例，演示ADC芯片的掉电模式进入和唤醒操作
    Args:无

    Raises:
        ValueError: 参数值无效时抛出
        TypeError: 参数类型错误时抛出
        OSError: 传感器无响应时抛出

    Notes:
        掉电模式可降低功耗，唤醒后需等待约100ms确保芯片稳定

    ==========================================
    Power management example, demonstrates entering power-down mode and wake-up operation of ADC chip
    Args:None

    Raises:
        ValueError: Raised when parameter value is invalid
        TypeError: Raised when parameter type is incorrect
        OSError: Raised when sensor does not respond

    Notes:
        Power-down mode can reduce power consumption, wait about 100ms after wake-up to ensure chip stability
    """
    print("
=== Power Management Example ===")
    try:
        adc = CS1237(CLK_PIN, DATA_PIN)

        # 读取掉电前数据
        print("Read value before power down:", adc.read())

        # 进入掉电模式
        print("Enter power down mode...")
        adc.power_down()
        time.sleep(2)  # 掉电2秒

        # 唤醒芯片
        print("Wake up chip...")
        adc.power_up()
        time.sleep(0.1)  # 唤醒后等待稳定

        # 读取唤醒后数据
        print("Read value after wake up:", adc.read())

    except (ValueError, TypeError, OSError) as e:
        print(f"Power management failed: {e}")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动延时3秒，确保硬件稳定
time.sleep(3)
# 打印程序启动标识
print("FreakStudio: CS1237 ADC driver demo")

# 定义CS1237芯片时钟引脚（GPIO5，输出模式）
CLK_PIN = Pin(5, Pin.OUT)
# 定义CS1237芯片数据引脚（GPIO4，输入模式）
DATA_PIN = Pin(4, Pin.IN)

# ========================================  主程序  ============================================

if __name__ == "__main__":
    # 执行顺序：基础读取 → 缓冲读取 → 温度校准 → 电源管理
    demo_cs1237_basic()
    demo_buffered_read()
    demo_temperature_calibration()
    demo_power_management()
    print("
=== All examples executed completed ===")

```

## 注意事项

- 请确保 SPI 时钟频率不超过 CS1237 芯片的最大规格
- 硬件连接时需注意 CS1237 的电源与信号电平匹配，避免损坏芯片
- 数据读取时需根据 CS1237 的配置寄存器设置，选择合适的增益与采样率
- 本库仅提供基础驱动功能，高级配置（如校准、滤波）需根据硬件需求自行实现

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源，完整协议内容如下：

```sql
MIT License

Copyright (c) 2026 FreakStudio

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
