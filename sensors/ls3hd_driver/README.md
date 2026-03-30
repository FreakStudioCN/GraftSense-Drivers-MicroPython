# ls3hd_driver (MicroPython)

# ls3hd_driver (MicroPython)

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

这是一个适用于 **MicroPython** 环境的 **LIS3DH 三轴加速度传感器驱动库**，为开发者提供简洁易用的 API 来控制 LIS3DH 传感器、读取加速度数据，兼容主流 MicroPython 芯片与固件。

## 主要功能

- 支持 LIS3DH 传感器的 I2C 通信初始化与连接检测
- 可配置传感器量程（±2g/±4g/±8g/±16g）与数据输出速率
- 提供 X/Y/Z 三轴加速度数据读取接口
- 支持传感器寄存器的读写操作，便于高级功能定制
- 无特定芯片与固件依赖，兼容所有支持 I2C 的 MicroPython 开发板

## 硬件要求

- **传感器模块**：LIS3DH 三轴加速度传感器模块
- **开发板**：支持 I2C 通信的 MicroPython 开发板（如 ESP32、ESP8266、STM32、RP2040 等）
- **连接方式**：通过 I2C 总线连接（VCC、GND、SDA、SCL 引脚）
- **供电**：3.3V 直流供电（禁止直接使用 5V 供电，避免损坏传感器）

## 文件说明

## 软件设计核心思想

1. **轻量化设计**：仅封装传感器核心功能，适配 MicroPython 资源受限环境
2. **易用性优先**：提供直观的 API 接口，无需深入了解寄存器细节即可快速开发
3. **跨平台兼容**：无特定芯片与固件依赖（`chips` 和 `fw` 均标记为 `all`），支持多种开发板
4. **开源协作**：遵循 MIT 协议开源，鼓励社区贡献、二次开发与技术分享

## 使用说明

1. **环境准备**：确保开发板已烧录支持 I2C 的 MicroPython 固件
2. **文件上传**：将 `code/lis3dh.py` 上传至开发板文件系统（可通过 Thonny、ampy 等工具完成）
3. **导入库**：在脚本中导入 `lis3dh` 模块
4. **初始化 I2C**：配置开发板的 I2C 总线（指定 SDA、SCL 引脚与通信频率）
5. **初始化传感器**：通过 I2C 实例创建 LIS3DH 对象，配置量程与数据速率
6. **读取数据**：调用 API 获取三轴加速度数据

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午7:30
# @Author  : Embedded Developer
# @File    : main.py
# @Description : LIS3DH加速度传感器测试 读取加速度数据并转换为俯仰角和横滚角

# ======================================== 导入相关模块 =========================================

# 导入LIS3DH传感器驱动模块
import lis3dh

# 导入时间模块用于延时和时间戳获取
import time

# 导入数学模块用于角度计算
import math

# 导入Pin和I2C模块用于硬件通信
from machine import Pin, I2C

# ======================================== 全局变量 ============================================

# 定义I2C SCL引脚编号
I2C_SCL_PIN = 5
# 定义I2C SDA引脚编号
I2C_SDA_PIN = 4
# 定义I2C通信频率
I2C_FREQ = 400000
# 定义LIS3DH传感器目标I2C地址
TARGET_SENSOR_ADDR = 0x19

# 记录上次角度转换的时间戳
last_convert_time = 0
# 角度转换的时间间隔（毫秒）
convert_interval = 100
# 俯仰角（初始值）
pitch = 0
# 横滚角（初始值）
roll = 0

# ======================================== 功能函数 ============================================


def convert_accell_rotation(vec):
    """
    将加速度数据转换为俯仰角(Pitch)和横滚角(Roll)
    Args:
        vec: 包含x、y、z三轴加速度值的列表/元组

    Returns:
        元组，包含当前计算的横滚角和俯仰角（单位：度）

    Notes:
        每100毫秒重新计算一次角度，降低计算频率；角度计算使用反正切函数，转换为角度制
    ==========================================
    Convert acceleration data to Pitch and Roll angles
    Args:
        vec: List/tuple containing x, y, z three-axis acceleration values

    Returns:
        Tuple containing the currently calculated roll angle and pitch angle (unit: degrees)

    Notes:
        Recalculate angles every 100 milliseconds to reduce calculation frequency; angle calculation uses arctangent function and converts to degrees
    """
    x_Buff = vec[0]  # 提取x轴加速度值
    y_Buff = vec[1]  # 提取y轴加速度值
    z_Buff = vec[2]  # 提取z轴加速度值

    global last_convert_time, convert_interval, roll, pitch

    # 判断是否达到角度重新计算的时间间隔
    if last_convert_time < time.ticks_ms():
        last_convert_time = time.ticks_ms() + convert_interval

        # 计算横滚角（Roll），转换为角度制
        roll = math.atan2(y_Buff, z_Buff) * 57.3
        # 计算俯仰角（Pitch），转换为角度制
        pitch = math.atan2((-x_Buff), math.sqrt(y_Buff * y_Buff + z_Buff * z_Buff)) * 57.3

    # 返回当前的横滚角和俯仰角
    return (roll, pitch)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: LIS3DH Accelerometer Test and Angle Calculation")

# 初始化I2C总线，指定引脚和通信频率
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 扫描I2C总线上的所有设备，获取设备地址列表
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描开始提示
print("START I2C SCANNER")
# 检查是否扫描到I2C设备
if len(devices_list) == 0:
    # 打印无设备提示
    print("No i2c device !")
    # 抛出异常并终止程序
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印扫描到的设备数量
    print("i2c devices found:", len(devices_list))
    # 初始化传感器对象为None
    imu = None
    # 遍历扫描到的I2C设备地址
    for device in devices_list:
        # 判断是否匹配目标传感器地址
        if device == TARGET_SENSOR_ADDR:
            # 打印匹配到的传感器十六进制地址
            print("I2c hexadecimal address:", hex(device))
            try:
                # 初始化LIS3DH传感器
                imu = lis3dh.LIS3DH_I2C(i2c=i2c_bus, address=TARGET_SENSOR_ADDR)
                # 打印传感器初始化成功提示
                print("Target sensor initialization successful")
                # 找到目标传感器后退出循环
                break
            except Exception as e:
                # 打印传感器初始化失败信息
                print(f"Sensor Initialization failed: {e}")
                # 继续遍历其他地址
                continue
    # 判断是否成功初始化传感器
    if imu is None:
        # 抛出未找到传感器的异常
        raise Exception("No LIS3DH found")

# ========================================  主程序  ============================================

# 检查传感器设备是否正常
if imu.device_check():
    # 设置加速度传感器量程为2G
    imu.range = lis3dh.RANGE_2_G

    # 无限循环读取传感器数据
    while True:
        # 读取三轴加速度值并转换为G值（除以标准重力加速度）
        x, y, z = [value / lis3dh.STANDARD_GRAVITY for value in imu.acceleration]
        # 打印x、y、z轴的G值
        print("x = %0.3f G, y = %0.3f G, z = %0.3f G" % (x, y, z))

        # 调用函数将加速度数据转换为俯仰角和横滚角
        p, r = convert_accell_rotation(imu.acceleration)
        # 打印俯仰角和横滚角
        print("pitch = %0.2f, roll = %0.2f" % (p, r))

        # 延时100毫秒，平衡响应性和资源占用
        time.sleep(0.1)

```

## 注意事项

- **I2C 地址确认**：LIS3DH 的 I2C 地址由 SA0 引脚电平决定：SA0=LOW 时为 `0x18`，SA0=HIGH 时为 `0x19`，需根据硬件连接确认地址
- **量程与精度**：量程越大，测量精度越低，需根据应用场景选择合适量程
- **供电稳定性**：确保传感器供电稳定，电压波动会导致数据异常
- **引脚冲突**：I2C 引脚需与开发板其他外设引脚无冲突，否则会导致通信失败
- **固件版本**：本库无特定固件依赖，若出现兼容性问题，建议更新至最新版 MicroPython 固件

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源，完整协议内容如下：

```
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
