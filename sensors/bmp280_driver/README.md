# GraftSense-基于 BMP280 芯片的大气压强温度传感器模块（MicroPython）

# GraftSense-基于 BMP280 芯片的大气压强温度传感器模块（MicroPython）

# GraftSense 基于 BMP280 的大气压强温度传感器模块

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

本模块是 FreakStudio GraftSense 基于 BMP280 的大气压强温度传感器模块，通过 BMP280 芯片实现高精度环境气压与温度测量（兼容湿度扩展），支持 30000~110000 Pa 气压范围、-40~85 °C 温度范围，具备高精度、低功耗、接口简单等优势，兼容 Grove 接口标准。适用于电子 DIY 气象实验、天气监测演示、物联网环境感知等场景，为系统提供精准的大气环境数据交互能力。

## 主要功能

### 硬件层面核心能力

- 高精度测量：支持 30000~110000 Pa 气压范围、-40~85 °C 温度范围测量，可扩展湿度检测能力
- 灵活的 I2C 配置：支持通过拨码开关切换 2 个 I2C 地址（0x76/0x77），可同时挂载 2 个模块无冲突
- 宽电压兼容：支持 3.3V/5V 供电，内置 DC-DC 转换电路保障芯片稳定供电
- 直观状态指示：配备电源指示灯，便于快速确认模块供电状态

### 软件层面核心能力

- 完整的数据校准：自动加载芯片内置校准参数，实现温压湿数据精准补偿
- 多维度数据输出：支持原始数据、校准后浮点数据、格式化字符串数据输出
- 衍生计算能力：基于气压自动计算海拔高度，基于温湿度计算露点温度
- 灵活的工作模式：支持睡眠、单次触发、连续测量三种工作模式，可调节过采样倍数平衡精度与功耗

## 硬件要求

### 核心接口

- I2C 通信接口：SDA（数据）、SCL（时钟），支持标准 I2C 通信速率，兼容 3.3V/5V 电平
- 地址选择拨码开关：通过 ADDR 引脚电平切换，配置两种 I2C 地址：

  - 拨码 0（LOW）→ 地址 0x76
  - 拨码 1（HIGH）→ 地址 0x77
  - 支持 2 个模块同时挂载于同一 I2C 总线（地址唯一），保障多设备协同采集
- 电源接口：VCC（3.3V/5V 供电）、GND（接地）
- 电源指示灯：直观显示模块供电状态

### 电路与布局要求

- 核心电路：需包含 BMP280 核心电路、DC-DC 5V 转 3.3V 电路、地址选择电路、MCU 接口电路、电源滤波电路
- 模块布局：正面需清晰布局 BMP280 芯片、ADDR 拨码开关、I2C 接口（SDA/SCL）、电源接口（GND/VCC）、电源指示灯，接口标注清晰

### 供电要求

- 输入电压：3.3V/5V DC
- 电源稳定性：需保障电源纹波小，建议配合滤波电路使用，避免影响测量精度

## 文件说明

| 文件名          | 功能说明                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------ |
| bmp280_float.py | 核心驱动文件，包含 BMP280 浮点型版本的类定义，实现传感器初始化、数据读取、校准补偿、衍生计算等核心功能 |
| main.py         | 示例程序文件，实现 I2C 总线初始化、传感器扫描、温压湿数据采集、海拔计算与结果打印等功能                |

## 软件设计核心思想

1. **面向对象设计**：封装 BMP280 类，将传感器的硬件操作、数据存储、计算逻辑封装为独立的类属性和方法，提高代码复用性和可维护性
2. **内存优化**：内部复用缓冲区（_l1_barray/_l8_barray/_l3_resultarray），减少频繁的内存分配与释放，提升 MicroPython 环境下的运行性能
3. **精准校准机制**：初始化时自动读取芯片的校准寄存器（dig_T1~dig_T3/dig_P1~dig_P9/dig_H1~dig_H6），基于 t_fine 温度微调变量实现温压湿数据的精准补偿
4. **参数化配置**：通过类常量定义 I2C 地址、过采样模式、工作模式、超时时间等配置项，便于灵活调整传感器工作参数
5. **异常防护**：对关键参数（如海平面气压、过采样模式）设置合法范围校验，避免无效参数导致计算异常

## 使用说明

### 硬件接线

1. 将模块的 VCC 引脚连接到主控板的 3.3V/5V 电源引脚
2. 将模块的 GND 引脚连接到主控板的接地引脚
3. 将模块的 SDA 引脚连接到主控板的 I2C SDA 引脚
4. 将模块的 SCL 引脚连接到主控板的 I2C SCL 引脚
5. 根据需求设置 ADDR 拨码开关（0 或 1），确定传感器 I2C 地址

### 环境准备

1. 主控板需烧录 MicroPython 固件
2. 将 bmp280_float.py 文件上传到主控板文件系统
3. 确保主控板支持 I2C 总线操作

### 基本使用流程

1. 初始化 I2C 总线，指定 SCL、SDA 引脚和通信频率
2. 扫描 I2C 总线，确认 BMP280 传感器的地址
3. 创建 BMP280 类实例，传入 I2C 实例和传感器地址
4. 调用相关方法读取温压湿数据，或获取海拔、露点等衍生数据
5. 根据需求处理和输出数据

## 示例程序

以下是 main.py 中的核心示例代码，实现环境温压湿实时采集与海拔计算：

```python
import time
from machine import I2C
from bmp280_float import BMP280

# 初始化配置
time.sleep(3)
print("FreakStudio:Testing BMP280 pressure, temperature, and humidity sensor")

# 初始化I2C总线（I2C1，SCL=3，SDA=2，100kHz）
i2c = I2C(1, scl=3, sda=2, freq=100000)

# 扫描I2C设备，获取BMP280地址
devices_list = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
    for device in devices_list:
        if 0x60 <= device <= 0x7A:
            print("I2c hexadecimal address:", hex(device))
            bmp_addr = device

# 创建BMP280传感器实例
bmp = BMP280(i2c=i2c, address=bmp_addr)

# 主循环：持续采集温压湿并计算海拔
try:
    print("FreakStudio: Testing BMP280 sensor (Temperature, Humidity, Pressure)")
    while True:
        # 获取校准后的温压湿数据
        temp, press, hum = bmp.read_compensated_data()
        # 转换气压为百帕（hPa）
        press_hpa = press / 100.0
        # 计算海拔高度（基于默认海平面气压1013.25 hPa）
        altitude = 44330.0 * (1.0 - (press_hpa / 1013.25) ** 0.1903)
        
        # 打印结果
        print("Temperature: {:.2f} °C | Humidity: {:.2f}% | Pressure: {:.2f} hPa".format(
            temp, hum, press_hpa
        ))
        print("Altitude: {:.2f} m".format(altitude))
        time.sleep(2)
except KeyboardInterrupt:
    print("\nTest stopped")
```

### 示例说明

1. I2C 初始化：使用 GPIO3（SCL）和 GPIO2（SDA）初始化 I2C，扫描总线获取 BMP280 地址（0x76 或 0x77）
2. 传感器初始化：创建 BMP280 实例，自动加载芯片校准参数
3. 数据采集：循环调用 read_compensated_data 获取校准后的温压湿数据
4. 衍生计算：将气压转换为百帕，基于海平面气压计算海拔高度
5. 结果打印：格式化输出温度、湿度、气压和海拔信息

## 注意事项

1. I2C 地址匹配：ADDR 拨码 0 对应地址 0x76，拨码 1 对应 0x77，代码中 address 参数需与拨码设置一致，否则通信失败
2. 过采样模式合法性：过采样模式必须为 BMP280_OSAMPLE_1~BMP280_OSAMPLE_16，超出范围会触发 ValueError
3. 海平面气压范围：sealevel 属性需设置在 30000~120000 Pa 之间，超出范围将被忽略，避免海拔计算异常
4. 湿度限制：湿度计算结果会被限制在 0~100% 范围内，避免出现无效值
5. ISR 安全限制：I2C 操作不是 ISR-safe，禁止在中断服务程序中调用传感器方法
6. 校准数据加载：初始化时会自动读取芯片校准寄存器，确保温压湿补偿计算准确
7. 缓冲区复用：类内部复用缓冲区（_l1_barray/_l8_barray/_l3_resultarray），减少内存分配，提升性能

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
