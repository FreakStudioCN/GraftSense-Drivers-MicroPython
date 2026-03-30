# ads1219_driver - ADS1219 MicroPython 驱动库

# ads1219_driver - ADS1219 MicroPython 驱动库

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

本项目是 **ADS1219 高精度 24 位模数转换器（ADC）** 的 MicroPython 驱动库，隶属于 GraftSense-Drivers-MicroPython 生态，用于在 MicroPython 环境下快速实现 ADS1219 芯片的配置与模拟信号采集，适用于工业传感、精密测量等场景。

## 主要功能

- 支持 ADS1219 芯片的 I2C 通信初始化与地址配置
- 可灵活选择输入通道、配置增益放大倍数
- 支持多种数据输出速率设置，适配不同采样需求
- 封装底层寄存器操作，提供简洁的单次 / 连续数据读取 API
- 无特定芯片 / 固件依赖，兼容主流 MicroPython 开发板

## 硬件要求

- **开发板**：支持 MicroPython 固件的设备（如 ESP32、RP2040、STM32 等）
- **核心芯片**：ADS1219 24 位高精度 ADC 芯片
- **通信接口**：I2C 总线（需连接 SDA/SCL 引脚，推荐 400kHz 通信频率）
- **电源**：ADS1219 供电电压 2.7V ~ 5.25V，需与开发板电平逻辑兼容

## 文件说明

## 软件设计核心思想

- **接口抽象**：将 ADS1219 底层 I2C 寄存器读写封装为高级 API，降低开发者使用门槛
- **兼容性设计**：通过 `package.json` 声明 `chips: all` 和 `fw: all`，确保适配主流 MicroPython 设备与固件版本
- **模块化解耦**：核心驱动代码与配置文件分离，便于后续功能扩展与维护
- **易用性优先**：提供极简的初始化流程和数据读取方法，支持快速集成到实际项目

## 使用说明

1. 将 `code/ads1219.py` 文件复制到 MicroPython 开发板的文件系统中
2. 初始化开发板的 I2C 总线，指定 SDA/SCL 引脚与通信频率
3. 导入 `ADS1219` 类，传入 I2C 实例与芯片地址（ADS1219 地址可选 `0x48`/`0x49`/`0x4A`/`0x4B`）
4. 调用 `configure()` 方法配置通道、增益、数据速率等参数
5. 调用 `read_data()` 方法获取 ADC 转换结果

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/23 下午2:23
# @Author  : hogeiha
# @File    : main.py
# @Description : ADS1219模数转换器单-shot转换模式数据读取，实现I2C设备扫描、传感器初始化及电压数据采集

# ======================================== 导入相关模块 =========================================

# 从machine模块导入Pin类，用于配置硬件引脚
from machine import Pin

# 从machine模块导入I2C类，用于I2C总线通信控制
from machine import I2C

# 从ads1219模块导入ADS1219类，用于操作ADS1219模数转换器
from ads1219 import ADS1219

# 导入utime模块，用于实现延时等时间相关操作
import utime

# ======================================== 全局变量 ============================================

# 定义I2C总线SCL引脚编号（对应Raspberry Pi Pico的GPIO5）
I2C_SCL_PIN = 5
# 定义I2C总线SDA引脚编号（对应Raspberry Pi Pico的GPIO4）
I2C_SDA_PIN = 4
# 定义I2C总线通信频率（标准100kHz，符合I2C总线规范）
I2C_FREQ = 100000
# 定义ADS1219的目标I2C地址列表（ADDR引脚可配置为0x40-0x43）
TARGET_SENSOR_ADDR_LIST = [0x40, 0x41, 0x42, 0x43]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保硬件设备完成上电稳定过程
utime.sleep(3)
# 打印初始化提示信息，标识功能用途
print("FreakStudio: ADS1219 I2C sensor initialization and data acquisition")

# 初始化I2C总线0，配置SCL/SDA引脚及通信频率
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描I2C总线上连接的所有设备，返回设备地址列表
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描启动提示
print("START I2C SCANNER")

# 检查I2C扫描结果，若未发现任何设备则终止程序
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印扫描到的I2C设备数量
    print("i2c devices found:", len(devices_list))

# 初始化ADC变量，用于存储ADS1219传感器实例
adc = None
# 遍历扫描到的I2C设备地址，匹配目标传感器地址
for device in devices_list:
    if device in TARGET_SENSOR_ADDR_LIST:
        # 打印匹配到的I2C设备十六进制地址
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化ADS1219传感器实例
            adc = ADS1219(i2c_bus)
            # 打印传感器初始化成功提示
            print("ADS1219 sensor initialization successful")
            break
        except Exception as e:
            # 打印传感器初始化失败信息及异常详情
            print(f"ADS1219 Initialization failed: {e}")
            continue
else:
    # 未找到目标传感器时抛出异常，包含目标地址和已发现地址信息
    raise Exception(
        f"No ADS1219 found! Target addresses: {[hex(addr) for addr in TARGET_SENSOR_ADDR_LIST]}, "
        f"Found addresses: {[hex(addr) for addr in devices_list]}"
    )

# ========================================  主程序  ============================================

# 设置ADS1219的采样通道为AIN0通道
adc.set_channel(ADS1219.CHANNEL_AIN0)
# 设置ADS1219的转换模式为单次转换模式
adc.set_conversion_mode(ADS1219.CM_SINGLE)
# 设置ADS1219的增益为1倍增益
adc.set_gain(ADS1219.GAIN_1X)
# 设置ADS1219的数据率为20 SPS（该速率下转换精度最高）
adc.set_data_rate(ADS1219.DR_20_SPS)
# 设置ADS1219的参考电压为内部参考电压
adc.set_vref(ADS1219.VREF_INTERNAL)

# 无限循环读取ADS1219转换数据并打印
while True:
    # 读取ADS1219单次转换后的数据
    result = adc.read_data()
    # 打印原始转换数据及转换后的毫伏值
    print("result = {}, mV = {:.2f}".format(result, result * ADS1219.VREF_INTERNAL_MV / ADS1219.POSITIVE_CODE_RANGE))
    # 延时0.1秒，控制数据读取频率
    utime.sleep(0.1)

```

## 注意事项

- 需确认 ADS1219 实际硬件地址，与初始化时传入的 `address` 参数一致
- 增益与数据速率设置会影响测量精度和功耗，需根据实际场景合理配置
- 模拟输入信号建议增加滤波电路，避免环境电磁干扰导致数据异常
- 确保开发板与 ADS1219 之间的电平匹配，防止过压 / 欠压损坏芯片

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源协议，完整内容如下：

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
