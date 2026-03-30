# MEMS气体传感器多通道读取驱动

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
本项目是基于MicroPython v1.23.0开发的MEMS气体传感器多通道读取驱动及示例代码，实现了对VOC、CO、H2S、NO2等多种气体的浓度检测、校零校准功能，并通过PCA9546ADR I2C多路复用器实现4通道传感器的统一管理。代码遵循模块化设计思想，提供简洁易用的接口，适用于ESP32/ESP8266等支持MicroPython的开发板。

## 主要功能
1. 支持12种MEMS气体传感器类型（VOC、CO、H2S、NO2、H2、NH3等）的浓度读取；
2. 提供传感器校零校准功能，支持自定义校准基准值；
3. 实现PCA9546ADR I2C多路复用器驱动，支持4通道切换、状态读取及全通道禁用；
4. 封装AirQualityMonitor类，统一管理多通道传感器的注册、读取和校准；
5. 内置I2C通信异常捕获机制，示例程序添加全局异常处理，避免程序崩溃；
6. 严格遵循MicroPython I2C通信规范，通信速率限制为100KHz，保证数据稳定性。

## 硬件要求
1. 支持MicroPython v1.23.0的开发板（如ESP32、ESP8266等）；
2. MEMS气体传感器（支持I2C通信，默认7位地址0x2A）；
3. PCA9546ADR I2C多路复用器（默认7位地址0x70）；
4. 接线要求：SDA接开发板Pin4，SCL接开发板Pin5，传感器/多路复用器需接好3.3V/5V电源和GND；
5. 传感器需30秒预热时间，确保浓度读数准确。

## 文件说明
| 文件名                | 功能说明                                                                 |
|-----------------------|--------------------------------------------------------------------------|
| `main.py`             | 示例代码，实现VOC/CO/H2S/NO2四种传感器的注册、校准和实时浓度读取（每秒打印一次） |
| `mems_air_module.py`  | 核心驱动代码，包含3个核心类：<br>- `MEMSGasSensor`：MEMS传感器操作类<br>- `PCA9546ADR`：I2C多路复用器驱动类<br>- `AirQualityMonitor`：多传感器整合管理类 |

## 软件设计核心思想
1. **模块化设计**：将传感器操作、多路复用器管理、多传感器整合拆分为独立类，降低代码耦合度，便于扩展和维护；
2. **接口统一化**：通过`AirQualityMonitor`类封装底层I2C操作和通道切换逻辑，对外提供统一的`register_sensor`、`read_sensor`、`calibrate_sensor`等接口；
3. **冲突避免**：切换I2C通道前先禁用所有通道，避免地址冲突；读取传感器数据时添加20ms操作延迟，保证数据稳定；
4. **异常鲁棒性**：捕获I2C通信异常（如无ACK、数据不完整），示例程序中捕获全局异常，避免程序崩溃；
5. **常量规范化**：使用`const`定义气体类型、I2C地址、命令字等固定值，提高代码可读性和可维护性。

## 使用说明
### 1. 环境准备
确保开发板已烧录MicroPython v1.23.0固件，可通过串口工具或开发板管理工具验证固件版本。

### 2. 硬件接线
- 开发板Pin4 → PCA9546ADR的SDA引脚；
- 开发板Pin5 → PCA9546ADR的SCL引脚；
- PCA9546ADR的4个通道分别连接不同类型的MEMS气体传感器；
- 所有设备接好电源（3.3V/5V）和GND，确保接线牢固。

### 3. 文件上传
将`mems_air_module.py`和`main.py`上传到开发板的文件系统中（可使用Thonny、ampy等工具）。

### 4. 运行程序
1. 给传感器上电，等待30秒预热完成；
2. 执行`main.py`，程序会自动完成：
   - 初始化I2C总线和空气质量监测器；
   - 注册并校准0-3通道的VOC/CO/H2S/NO2传感器；
   - 每秒读取一次所有传感器浓度值并打印；
3. 若需停止程序，按下`Ctrl+C`中断。

### 5. 自定义扩展
- 新增传感器类型：通过`monitor.register_sensor(通道号, MEMSGasSensor.TYPE_XXX)`注册（如TYPE_H2、TYPE_NH3等）；
- 单独校准传感器：调用`monitor.calibrate_sensor(MEMSGasSensor.TYPE_XXX)`；
- 单独读取某类气体浓度：调用`monitor.read_sensor(MEMSGasSensor.TYPE_XXX)`。

## 示例程序
以下是`main.py`的核心代码（完整代码见项目文件）：
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午2:21
# @Author  : hogeiha
# @File    : main.py
# @Description : MEMS气体传感器多通道读取示例代码，实现VOC/CO/H2S/NO2四种气体的校准和实时浓度读取

from machine import Pin, SoftI2C
import time
from mems_air_module import MEMSGasSensor, PCA9546ADR, AirQualityMonitor

# 延时等待设备初始化
time.sleep(3)
print("FreakStudio : Using IIC to read MEMS sensor")

# 初始化I2C总线
i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
monitor = AirQualityMonitor(i2c)

# 注册并校准各通道传感器
monitor.register_sensor(0, MEMSGasSensor.TYPE_VOC)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_VOC)

monitor.register_sensor(1, MEMSGasSensor.TYPE_CO)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_CO)

monitor.register_sensor(2, MEMSGasSensor.TYPE_H2S)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_H2S)

monitor.register_sensor(3, MEMSGasSensor.TYPE_NO2)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_NO2)

# 实时读取并打印浓度值
print("\nStart reading gas concentration (press Ctrl+C to stop)...")
print("-" * 50)
while True:
    try:
        results = monitor.read_all()
        print(f"VOC concentration: {results[MEMSGasSensor.TYPE_VOC]}")
        print(f"CO concentration: {results[MEMSGasSensor.TYPE_CO]}")
        print(f"H2S concentration: {results[MEMSGasSensor.TYPE_H2S]}")
        print(f"NO2 concentration: {results[MEMSGasSensor.TYPE_NO2]}")
        print("-" * 50)
    except Exception as e:
        print(f"Error reading concentration: {str(e)}")
        print("-" * 50)
    time.sleep(1)
```

## 注意事项
1. **传感器预热**：传感器上电后必须等待30秒预热，否则浓度读数会严重偏离实际值；
2. **I2C速率限制**：I2C通信速率必须设置为100KHz，超出该速率会导致通信失败；
3. **通道范围限制**：PCA9546ADR仅支持0-3通道，注册传感器时通道号超出范围会抛出`ValueError`；
4. **校准环境**：校零校准需在清洁空气环境中执行，校准后读数理想值为0，±5以内的偏差属正常现象；
5. **气体类型规范**：必须使用`MEMSGasSensor`类内置的`TYPE_*`常量（如`TYPE_VOC`），不可自定义数值；
6. **接线检查**：若出现“I2C No ACK”错误，需检查硬件接线是否牢固、传感器/多路复用器地址是否正确；
7. **操作延迟**：切换多路复用器通道后建议等待10ms，确保通道切换完成后再进行I2C通信。

## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：liqinghsui@freakstudio.cn  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议
本项目采用MIT开源许可协议，详细条款见代码内注释。您可以自由使用、修改和分发本代码，无需额外授权，但需保留原作者信息和许可声明。