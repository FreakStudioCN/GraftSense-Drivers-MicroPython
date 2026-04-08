# QMC5883L Driver for MicroPython

# QMC5883L Driver for MicroPython

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

`qmc5883l_driver` 是一个用于控制 **QMC5883L 三轴磁力计** 的 MicroPython 库，适用于各类支持 MicroPython 的开发板。该库提供了简洁的 API，方便开发者快速读取磁场数据、计算方位角，实现电子罗盘等功能。

## 主要功能

- 初始化 QMC5883L 传感器，配置测量模式、输出数据率和量程
- 读取 X/Y/Z 三轴原始磁场数据
- 计算方位角（电子罗盘功能）
- 支持软 / 硬铁校准接口（预留）
- 兼容主流 MicroPython 固件，无额外固件依赖

## 硬件要求

- 开发板：支持 MicroPython 的任意开发板（如 ESP32、ESP8266、Raspberry Pi Pico 等）
- 传感器：QMC5883L 三轴磁力计模块
- 连接方式：I2C 接口（SDA/SCL）

## 文件说明

## 软件设计核心思想

- **极简封装**：仅暴露必要的 API，降低使用门槛
- **硬件无关**：通过标准 I2C 接口与传感器通信，兼容所有支持 MicroPython I2C 的开发板
- **可扩展性**：预留校准、中断等接口，便于后续功能扩展
- **无依赖设计**：不依赖特定固件或第三方库，开箱即用

## 使用说明

1. 将 `code/qmc5883p.py` 文件上传至开发板的文件系统
2. 在 MicroPython 代码中导入 `qmc5883p` 模块
3. 初始化 I2C 总线，并创建 QMC5883L 实例
4. 调用相关方法读取磁场数据或计算方位角

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : robert-hh
# @File    : main.py
# @Description : QMC5883P磁力计传感器数据读取示例，通过I2C通信实时获取缩放后的三轴磁场数据并输出

# ======================================== 导入相关模块 =========================================
import math
from machine import I2C, Pin
import time
from qmc5883p import QMC5883P

# ======================================== 全局变量 ============================================

# SCL引脚号
I2C_SCL_PIN = 5  
# SDA引脚号
I2C_SDA_PIN = 4  
# I2C通信频率
I2C_FREQ = 400_000  
# QMC5883P默认I2C地址（十进制13）
QMC5883P_ADDR = 0x2C  

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保QMC5883P传感器完成初始化
time.sleep(3)
print("FreakStudio: QMC5883P magnetometer initialization start")

# 按指定风格初始化I2C总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

qmc5883 = None  # 初始化传感器对象变量
for device in devices_list:
    if device == QMC5883P_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            qmc5883 = QMC5883P(i2c=i2c_bus)
            print("QMC5883P sensor initialization successful")
            break
        except Exception as e:
            print(f"QMC5883P Initialization failed: {e}")
            continue
else:
    raise Exception("No QMC5883P sensor found on I2C bus")

# 打印传感器初始化完成提示信息
print("FreakStudio: QMC5883P magnetometer initialized successfully")

# ========================================  主程序  ============================================
# 无限循环读取磁力计传感器数据
while True:
    # 读取并打印缩放后的三轴磁场数据
    print(qmc5883.read_scaled())
    # 延时300毫秒后继续读取下一组数据
    time.sleep_ms(300)

```

## 注意事项

- 传感器 I2C 地址默认为 `0x0D`，若模块有地址修改需同步调整驱动代码
- 首次使用建议进行硬铁 / 软铁校准，以提高方位角精度
- 避免在强磁场环境下使用，否则会影响测量精度
- 数据读取频率需与传感器输出数据率匹配

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

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
