# GraftSense-基于 RCWL-9623 的收发一体式超声波模块（MicroPython）

# GraftSense-基于 RCWL-9623 的收发一体式超声波模块（MicroPython）

# GraftSense RCWL-9623 Ultrasonic Sensor Module

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

本项目是 **GraftSense 系列基于 RCWL-9623 的收发一体式超声波模块**，属于 FreakStudio 开源硬件项目。模块支持 GPIO/OneWire/UART/I2C 四种通信模式，可实现高精度超声波测距与物体检测，广泛适用于电子 DIY 距离测量实验、机器人避障演示、智能感应应用等场景。

---

## 主要功能

- **多模式通信**：支持 GPIO、OneWire、UART、I2C 四种工作模式，适配不同硬件接口需求。
- **收发一体设计**：集成超声波发射与接收单元，无需额外探头，结构紧凑。
- **可调测距范围**：通过外部电阻 R10 调节最大测距距离（47kΩ 对应 4-5 米，100kΩ 对应 6-7 米）。
- **高精度测距**：有效测量范围 25cm~700cm，测距结果保留两位小数，响应速度快。
- **统一接口抽象**：通过 `read_distance()` 方法统一封装不同模式的测距逻辑，降低使用门槛。

---

## 硬件要求

- **核心芯片**：RCWL-9623 收发一体式超声波芯片。
- **供电**：3.3V 直流供电，模块内置电源滤波与指示灯电路。
- **通信模式与引脚配置**：

  | 模式    | 引脚/接口要求                                                                 |
  | ------- | ----------------------------------------------------------------------------- |
  | GPIO    | TRIG（触发）、ECHO（回波）两个 GPIO 引脚                                      |
  | OneWire | 单数据引脚 DIO1（复用 TRIG 功能）                                             |
  | UART    | TX（DIO1）、RX（DIO0）串口引脚，波特率默认 9600（注意：不符合标准 UART 时序） |
  | I2C     | SCL（DIO0）、SDA（DIO1）I2C 引脚，固定地址 0x57                               |
- **测距调节**：R10 电阻选择 47kΩ 或 100kΩ 以适配不同测距需求。

---

## 文件说明

- `rcwl9623.py`：RCWL-9623 超声波模块驱动文件，封装了四种通信模式的测距实现，提供统一的 `read_distance()` 接口。
- `main.py`：驱动测试程序，演示了四种工作模式的初始化与实时测距流程，可直接用于功能验证。

---

## 软件设计核心思想

- **多模式抽象**：通过统一的 `read_distance()` 方法分发到不同模式的私有实现（`_read_gpio`/`_read_onewire`/`_read_uart`/`_read_i2c`），隐藏底层通信细节。
- **资源复用**：驱动不负责创建 UART/I2C 实例，仅复用外部传入的实例，便于总线共享与单元测试，减少硬件平台绑定。
- **时序严格性**：严格遵循 RCWL-9623 数据手册的通信时序要求，确保测距结果准确可靠。
- **错误处理**：测距失败或超出有效范围时返回 `None`，避免异常中断，便于上层应用容错处理。

---

## 使用说明

1. **硬件连接**：

   - 根据所选通信模式连接对应引脚（参考硬件要求表格）。
   - 选择合适的 R10 电阻调节测距范围。
2. **初始化配置**：

   ```python
   ```

from machine import Pin, I2C
from rcwl9623 import RCWL9623

# 示例：I2C 模式初始化

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
sensor = RCWL9623(mode=RCWL9623.I2C_MODE, i2c=i2c)

```

3. **测距操作**：
	```python
distance = sensor.read_distance()
if distance is not None:
    print("Distance: {:.2f} cm".format(distance))
else:
    print("Measurement failed or out of range")
```

---

## 示例程序

```python
# MicroPython v1.23.0
from machine import Pin, I2C
import time
from rcwl9623 import RCWL9623

# 上电延时
time.sleep(3)
print("FreakStudio: Test RCWL9623 Module")

# I2C 模式初始化
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
sensor = RCWL9623(mode=RCWL9623.I2C_MODE, i2c=i2c)
print("FreakStudio: I2C Mode")

# 循环测距
print("FreakStudio: Start Test")
try:
    while True:
        distance = sensor.read_distance()
        if distance is not None:
            print("Get Distance: %.2f cm" % distance)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("FreakStudio: Exit Test")
except Exception as e:
    print("FreakStudio: Error: %s" % e)
```

---

## 注意事项

1. **UART 模式限制**：UART 模式不符合标准 UART 时序要求，使用时需特别注意硬件连接与时序匹配。
2. **有效测距范围**：模块有效测量范围为 25cm~700cm，超出范围时 `read_distance()` 返回 `None`。
3. **I2C 地址固定**：I2C 模式下设备地址固定为 0x57，不可修改。
4. **中断安全**：所有测距方法均为阻塞操作，**非 ISR-safe**，不可在中断上下文调用。
5. **硬件配置**：不同通信模式需通过焊接电阻 R5/R7 切换，具体参考模块原理图。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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