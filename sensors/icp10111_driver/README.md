# ICP10111 Driver for MicroPython

# ICP10111 Driver for MicroPython

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

本项目是 **ICP10111 高精度气压 / 温度传感器** 的 MicroPython 驱动库，隶属于 `GraftSense-Drivers-MicroPython` 生态，旨在为开发者提供简洁、高效的传感器控制接口，方便在各类 MicroPython 开发板上快速集成 ICP10111 传感器。

## 主要功能

- 支持 ICP10111 传感器的 **温度与气压数据读取**
- 基于标准 I2C 通信协议，适配主流 MicroPython 开发板
- 无特定芯片与固件依赖，支持 `all` 芯片型号与固件版本
- 封装轻量化 API，降低开发门槛，便于快速原型开发与产品集成

## 硬件要求

- **传感器**：ICP10111 高精度气压 / 温度传感器
- **开发板**：支持 MicroPython 且具备 I2C 接口的开发板（如 ESP32、RP2040、STM32 等）
- **连接线**：用于连接传感器与开发板的 I2C 总线（SDA、SCL）及供电线（VCC、GND）

## 文件说明

## 软件设计核心思想

- **I2C 通信抽象**：封装 I2C 底层读写操作，屏蔽硬件细节，提供统一的传感器交互接口
- **无依赖设计**：不依赖特定固件（如 ulab、lvgl）或芯片型号，确保库的通用性与可移植性
- **轻量化 API**：仅暴露核心功能接口，避免冗余代码，提升运行效率与代码可读性
- **开源协作**：遵循 MIT 协议开放源码，鼓励社区贡献与二次开发

## 使用说明

1. **文件部署**：将 `code/icp10111.py` 上传至 MicroPython 开发板的文件系统（可通过 ampy、rshell 或 IDE 工具）
2. **导入库**：在 MicroPython 脚本中导入 `icp10111` 模块
3. **初始化 I2C**：根据开发板硬件配置，初始化 I2C 总线（指定 SDA、SCL 引脚与频率）
4. **创建传感器实例**：传入已初始化的 I2C 对象，创建 `ICP10111` 实例
5. **读取数据**：调用实例方法获取温度（℃）与气压（Pa）数据

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/20 下午4:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 读取ICP10111传感器的气压和温度数据，并循环切换不同的操作模式

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于实现延时功能
import time
# 导入machine模块中的Pin和I2C类，用于硬件引脚和I2C通信配置
from machine import Pin, I2C
# 导入micropython_icp10111库中的icp10111模块，用于操作ICP10111传感器
import icp10111

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保传感器完成初始化
time.sleep(3)
# 打印初始化提示信息
print("FreakStudio: Read ICP10111 pressure and temperature data")

# 初始化I2C通信，使用RP2040的4号引脚作为SDA，5号引脚作为SCL
i2c = I2C(0, sda=Pin(4), scl=Pin(5))  # Correct I2C pins for RP2040
# 初始化ICP10111传感器对象，传入I2C通信实例
icp = icp10111.ICP10111(i2c)

# 设置传感器的操作模式为正常模式
icp.operation_mode = icp10111.NORMAL

# ========================================  主程序  ============================================

# 无限循环执行数据读取和模式切换操作
while True:
    # 遍历所有支持的操作模式
    for operation_mode in icp10111.operation_mode_values:
        # 打印当前传感器的操作模式设置
        print("Current Operation mode setting: ", icp.operation_mode)
        # 每个模式下读取10次数据
        for _ in range(10):
            # 获取传感器测量的气压和温度数据
            press, temp = icp.measurements
            # 打印气压数据，保留两位小数
            print(f"Pressure {press:.2f}KPa")
            # 打印温度数据，保留两位小数
            print(f"Temperature {temp:.2f}°C")
            # 打印空行，分隔每次的测量数据
            print()
            # 延时0.5秒后进行下一次测量
            time.sleep(0.5)
        # 将传感器切换到下一个操作模式
        icp.operation_mode = operation_mode
```

## 注意事项

- **I2C 引脚配置**：需根据开发板实际引脚定义调整 SDA/SCL 引脚编号，避免硬件通信失败
- **供电要求**：ICP10111 传感器通常支持 1.7V~3.6V 供电，需确保开发板供电电压匹配
- **数据精度**：传感器测量精度受环境温度、供电稳定性影响，使用时需注意环境干扰
- **协议约束**：代码遵循 MIT 协议，二次分发或修改时需保留原版权声明与许可协议

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源许可协议，完整协议内容如下：

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
