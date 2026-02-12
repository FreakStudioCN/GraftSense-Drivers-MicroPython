# GraftSense-串口舵机驱动模块（MicroPython）

# GraftSense-串口舵机驱动模块（MicroPython）

# GraftSense UART 串口舵机驱动模块

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

本模块是 FreakStudio GraftSense UART 串口舵机驱动模块，专为 TTL 串口舵机设计，支持舵机位置控制、速度与角度可编程，适用于机器人舵机控制实验、电子 DIY 机械臂演示、智能设备运动演示等场景。模块通过 UART 串口与主控通信，内置全双工转半双工电路，兼容常用主控 IO 电平，提供稳定可靠的舵机控制能力。

## 主要功能

### 硬件功能

1. **核心接口**

   - UART 通信接口：MRX（接 MCU 的 RXD，对应模块 TXD）、MTX（接 MCU 的 TXD，对应模块 RXD），支持标准 TTL 电平通信
   - 舵机接线端子：支持多舵机级联，通过 CN1 接口连接串口总线舵机
   - 电源接口：5V 外部供电，内置滤波与保护电路，保障供电稳定性
2. **电路特性**

   - 全双工转半双工电路：74HC126D 增强信号驱动能力，74HC1G04W 生成 TXEN 使能信号控制通信方向
   - 电源保护：SS34 二极管防反接、1.5A 保险丝限流，避免过流损坏
3. **模块布局**：正面集成 UART 接口、舵机端子、指示灯；背面清晰标注引脚定义，便于接线调试

### 软件功能

基于 MicroPython 实现的 `SerialServo` 核心类，提供全维度舵机控制能力：

1. **运动控制**：支持立即转动、延迟转动、启动/停止舵机等操作
2. **参数配置**：可修改舵机 ID、角度偏差/限位、电压/温度范围、工作模式/速度、LED 状态等（多数参数掉电保存）
3. **状态读取**：可获取舵机实时角度、温度、电压、工作模式、负载状态等关键信息

## 硬件要求

1. 电源：5V/2A 以上直流供电，确保舵机正常工作无功率不足问题
2. 主控：支持 MicroPython 且具备 UART 串口的 MCU（如树莓派 Pico、ESP32 等）
3. 接线：UART 接口需严格对应 MRX-MCU RXD、MTX-MCU TXD，禁止交叉连接
4. 扩展：多舵机级联时，总电流不得超过电源输出能力，避免过载
5. 适配舵机：TTL 串口总线舵机，兼容本模块通信协议

## 文件说明

| 文件名            | 功能说明                                                  |
| ----------------- | --------------------------------------------------------- |
| `serial_servo.py` | 核心驱动文件，定义 `SerialServo` 类，封装所有舵机控制 API   |
| `main.py`         | 示例程序文件，演示舵机基础控制逻辑（循环转动 + 状态打印） |
| `README.md`       | 模块使用说明文档，包含功能、使用方法、注意事项等          |

## 软件设计核心思想

1. **模块化封装**：将舵机控制逻辑封装为 `SerialServo` 类，对外提供简洁统一的 API，降低使用门槛
2. **功能分层设计**：按“运动控制-参数设置-状态读取”三类场景拆分方法，逻辑清晰，便于维护和扩展
3. **兼容性与鲁棒性**：参数设置均限定合法范围（如角度 0-240°、电压 4.5-12V），避免非法输入导致舵机异常；关键参数支持掉电保存，保障配置持久性
4. **易用性优先**：API 命名直观（如 `move_servo_immediate`、`read_servo_position`），参数说明清晰，适配新手快速上手

## 使用说明

### 硬件接线

1. 电源连接：模块 5V 接口接外部 5V/2A 电源，GND 与主控 GND 共地
2. UART 连接：MRX 接 MCU 的 RXD 引脚，MTX 接 MCU 的 TXD 引脚（切勿交叉）
3. 舵机连接：串口总线舵机接入 CN1 端子，多舵机可级联扩展

### 软件环境

1. 主控烧录 MicroPython 固件（如 Raspberry Pi Pico、ESP32 对应版本）
2. 将 `serial_servo.py` 上传至主控文件系统
3. 确认 UART 波特率配置为 115200（模块默认通信波特率）

### 基础使用流程

1. 初始化 UART 对象，指定 TX/RX 引脚与波特率
2. 创建 `SerialServo` 实例，关联初始化后的 UART
3. 调用对应 API 实现舵机控制（如 `move_servo_immediate` 控制转动）
4. 可选：调用状态读取 API 获取舵机实时信息

## 示例程序

以下示例实现 4 号舵机在 0° 和 90° 之间循环转动，并打印目标角度与转动时间：

```python
from machine import UART, Pin
import time
from serial_servo import SerialServo

# 延时3s等待设备上电
time.sleep(3)
print("FreakStudio: Serial Servo Test")

# 初始化UART（波特率115200，TX=GP16，RX=GP17，以Raspberry Pi Pico为例）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

# 创建舵机控制实例
servo = SerialServo(uart)

# 主循环：控制4号舵机在0°和90°之间切换
while True:
    # 控制4号舵机立即转到0°，耗时1000ms
    servo.move_servo_immediate(servo_id=4, angle=0.0, time_ms=1000)
    time.sleep(2)  # 等待舵机到位
    
    # 获取并打印当前设置的角度和时间
    angle, time_ms = servo.get_servo_move_immediate(servo_id=4)
    print(f"Servo ID: 4, Angle: {angle}, Time: {time_ms}")

    # 控制4号舵机立即转到90°，耗时1000ms
    servo.move_servo_immediate(servo_id=4, angle=90.0, time_ms=1000)
    time.sleep(2)  # 等待舵机到位
    
    # 获取并打印当前设置的角度和时间
    angle, time_ms = servo.get_servo_move_immediate(servo_id=4)
    print(f"Servo ID: 4, Angle: {angle}, Time: {time_ms}")
```

## 注意事项

1. UART 连接：MRX 对应 MCU 的 RXD，MTX 对应 MCU 的 TXD，切勿交叉连接，否则通信失败
2. 电源要求：模块需 5V/2A 以上电源供电，避免因功率不足导致舵机抖动或通信异常
3. 参数范围：

   - 舵机 ID：0-253（254 为广播 ID，控制所有舵机）
   - 角度范围：0-240°，偏差范围：-30°~30°
   - 转动时间：0-30000ms，电压范围：4.5V-12V，温度范围：50-100℃
4. 已知问题：`get_servo_move_with_time_delay` 方法暂不可用，可使用 `get_servo_move_immediate` 替代
5. 级联扩展：通过舵机总线端子可级联多台舵机，需确保总电流不超过电源输出能力

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

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