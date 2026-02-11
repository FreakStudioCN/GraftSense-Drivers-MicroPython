# GraftSense-基于 JY60 的串口陀螺仪模块（MicroPython）

# GraftSense-基于 JY60 的串口陀螺仪模块（MicroPython）

# 基于 JY60 的串口陀螺仪模块 MicroPython 驱动

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

本项目是 基于 JY60 的串口陀螺仪模块 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，支持六轴 IMU（三轴加速度 + 三轴陀螺仪）数据采集与姿态解算，通过 UART 接口输出角速度、加速度和角度数据，适用于电子 DIY 运动感应实验、机器人姿态控制演示等场景。

## 主要功能

- 六轴数据采集：支持三轴加速度、三轴角速度（陀螺仪）和三轴角度（倾角）数据实时输出
- 模式配置：可切换工作/睡眠模式、串口/I2C 传输模式、水平/垂直安装模式
- 校准与清零：内置加速度校准和 Z 轴角度清零指令，确保测量精度
- 数据解析：自动解析串口数据帧，完成原始数据到物理量（g、°/s、°）的转换
- 调试支持：提供运行时间统计装饰器，便于性能分析和调试

## 硬件要求

- JY60 串口陀螺仪模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如树莓派 Pico RP2040 等）
- 引脚连接：

  - 模块 MTX（SRX） → MCU UART_TX（如 GP8）
  - 模块 MRX（STX） → MCU UART_RX（如 GP9）
  - VCC → 3.3V/5V 电源
  - GND → MCU GND
- 模块核心：基于 JY60 六轴 IMU，通过 UART 接口输出姿态数据，支持 115200/9600 波特率切换

## 文件说明

| 接口引脚 | 功能描述                         |
| -------- | -------------------------------- |
| GND      | 接地引脚                         |
| VCC      | 电源输入引脚（3.3V/5V 兼容）     |
| MTX      | 模块 UART_TX（对应 MCU UART_RX） |
| MRX      | 模块 UART_RX（对应 MCU UART_TX） |
| LED1     | 电源指示灯，上电后常亮           |

## 软件设计核心思想

1. 协议解析轻量化：针对 JY60 模块 0x55 帧头的串口通信协议，设计轻量级数据解析逻辑，适配 MicroPython 的 MCU 资源限制，仅解析核心数据帧（加速度、角速度、角度），减少内存占用；
2. 易用性封装：将硬件控制、指令发送、数据解析等底层操作封装为高内聚的 IMU 类，对外暴露简洁的方法（RecvData、SendCMD）和类属性，降低开发者使用门槛；
3. 自动化校准：初始化阶段自动执行加速度校准和 Z 轴角度清零，无需手动发送指令，提升使用便捷性；
4. 兼容性适配：支持 115200/9600 双波特率，兼容 3.3V/5V 供电，适配主流 MicroPython 开发板（如 RP2040）。

## 使用说明

### 硬件连接

- 模块 MTX 引脚连接至 MCU 的 UART_RX（如 GP9）
- 模块 MRX 引脚连接至 MCU 的 UART_TX（如 GP8）
- VCC 引脚连接至 3.3V 或 5V 电源，GND 引脚连接至 MCU GND

### 驱动初始化

```python
from machine import UART
from imu import IMU

# 创建串口对象，设置波特率为115200
uart = UART(1, 115200)
uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)

# 初始化IMU对象（自动执行加速度校准和Z轴清零）
imu_obj = IMU(uart)
```

### 核心控制方法

| 方法/属性            | 功能描述                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| SendCMD(cmd)         | 发送控制指令（如校准、模式切换、波特率设置）                                                            |
| RecvData()           | 接收并解析 IMU 数据，返回(acc_x, acc_y, acc_z, temp, gyro_x, gyro_y, gyro_z, angle_x, angle_y, angle_z) |
| WORK_MODE/SLEEP_MODE | 工作/睡眠模式常量                                                                                       |
| UART_MODE/IIC_MODE   | 串口/I2C 传输模式常量                                                                                   |
| HORIZ_INST/VERT_INST | 水平/垂直安装模式常量                                                                                   |

## 示例程序

### 基础姿态数据读取

```python
import time
from machine import UART
from imu import IMU

# 初始化串口
uart = UART(1, 115200)
uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)

# 初始化IMU
imu_obj = IMU(uart)

# 上电延时3s
time.sleep(3)
print("FreakStudio: Using UART to communicate with IMU")

# 循环读取姿态数据
while True:
    # 接收并解析数据
    acc_x, acc_y, acc_z, temp, gyro_x, gyro_y, gyro_z, angle_x, angle_y, angle_z = imu_obj.RecvData()
    
    # 打印角度数据
    print("X-axis angle:", angle_x)
    print("Y-axis angle:", angle_y)
    print("Z-axis angle:", angle_z)
    
    time.sleep(0.1)
```

### 完整示例（含 LED 指示和上位机数据转发）

```python
import time
from machine import UART, Pin
import gc
from imu import IMU

# 初始化串口
uart = UART(1, 115200)
uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)

# 初始化上位机串口
uart_pc = UART(0, 115200)
uart_pc.init(bits=8, parity=None, stop=1, tx=0, rx=1, timeout=5)

# 初始化LED
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# 初始化IMU
imu_obj = IMU(uart)

try:
    while True:
        LED.on()
        # 接收陀螺仪数据
        imu_obj.RecvData()
        LED.off()

        # 打印角度数据
        print("X-axis angle:", imu_obj.angle_x)
        print("Y-axis angle:", imu_obj.angle_y)
        print("Z-axis angle:", imu_obj.angle_z)
        print("Free RAM:", gc.mem_free())

        # 格式化并转发角度数据到上位机
        angle_data = "{:.2f}, {:.2f}, {:.2f}\r\n".format(imu_obj.angle_x, imu_obj.angle_y, imu_obj.angle_z)
        uart_pc.write(angle_data)

        # 内存不足时触发垃圾回收
        if gc.mem_free() < 220000:
            gc.collect()

except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    LED.off()
    print("LED off, program exited.")
```

## 注意事项

1. 校准要求：加速度校准和 Z 轴角度清零时，传感器必须保持水平/垂直且静止，否则校准结果无效
2. 串口交叉连接：模块 MTX 对应 MCU UART_RX，模块 MRX 对应 MCU UART_TX，需注意交叉连接，避免收发方向错误
3. 波特率切换：支持 115200 和 9600 波特率切换，发送波特率指令后需重新初始化 UART 对象
4. 数据帧格式：IMU 输出数据帧以 0x55 为帧头，包含加速度（0x51）、角速度（0x52）、角度（0x53）三种类型，驱动自动识别并解析
5. 资源占用：RecvData()方法为阻塞式调用，需注意在实时系统中合理安排调用频率
6. 环境条件：避免在高温、高湿或强电磁干扰环境下使用，以免影响测量精度

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2026 FreakStudioCN

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
