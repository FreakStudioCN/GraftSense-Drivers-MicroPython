# GraftSense-基于 MPU6050 的六轴陀螺仪模块（开放版）

# GraftSense-基于 MPU6050 的六轴陀螺仪模块（开放版）

# GraftSense MPU6050 6-Axis Gyroscope Module

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

本项目是 **GraftSense 系列基于 MPU6050 的六轴陀螺仪模块**，属于 FreakStudio 开源硬件项目。模块通过 MPU6050 芯片实现三轴加速度与三轴角速度数据采集，支持串口与 I2C 双通信模式，适用于姿态检测、运动追踪、平衡控制等场景，为系统提供可靠的姿态感知和数据交互能力。

---

## 主要功能

- **六轴数据采集**：支持三轴加速度检测、三轴角速度检测与姿态角度计算，覆盖运动状态感知全维度。
- **双通信模式**：兼容串口（UART）与 I2C 通信，I2C 默认地址为 `0x68`，适配 3.3V/5V 系统电平，支持主流微控制器。
- **多模式切换**：支持工作/睡眠模式、串口/I2C 传输模式、水平/垂直安装模式切换，灵活适配不同应用场景。
- **参数可配置**：支持波特率（9600/115200）、带宽（5–256 Hz）等参数配置，满足不同采样需求。
- **Grove 接口兼容**：遵循 Grove 接口标准，便于快速集成到各类开发平台。

---

## 硬件要求

- **核心芯片**：MPU6050 六轴运动传感器芯片，内置 MCU 接口、电源滤波模块与电源指示灯电路。
- **通信接口**：

  - I2C 接口：SDA、SCL 引脚，默认地址 `0x68`，兼容 3.3V/5V 电平。
  - UART 接口：支持 9600/115200 波特率，可通过指令切换传输模式。
- **使用规范**：

  - 校准与 Z 轴清零时，需保持传感器水平/垂直静止，避免数据偏移。
  - 模块为消费级精度，不可用于医疗诊断或高精度工业控制场景。

---

## 文件说明

- `imu.py`：MPU6050 模块驱动文件，封装了指令发送、数据接收、模式切换与数据解析等核心功能，支持串口通信。
- `main.py`：驱动测试与示例程序，演示了串口初始化、IMU 对象创建、数据读取与姿态角度打印的完整流程。

---

## 软件设计核心思想

- **分层架构**：将驱动层（通信协议与指令封装）与应用层（数据处理与展示）分离，提升代码可维护性与可扩展性。
- **模式化设计**：通过类常量定义工作/睡眠、串口/I2C、水平/垂直安装模式，支持一键切换，降低配置复杂度。
- **数据校验机制**：内置校验和验证逻辑，确保串口数据传输的准确性，避免噪声干扰导致的解析错误。
- **状态管理**：通过接收完成标志量（`recv_acc_flag`/`recv_gyro_flag`/`recv_angle_flag`）管理数据帧同步，确保三轴数据一致性。

---

## 使用说明

1. **硬件连接**：

   - 串口模式：将模块的 TX/RX 引脚连接至微控制器的 UART 接口（示例中 UART1：TX=GP8，RX=GP9）。
   - I2C 模式：将 SDA/SCL 引脚连接至微控制器的 I2C 总线，默认地址 `0x68`。
2. **初始化配置**：

   ```python
   ```

from machine import UART
from imu import IMU
import time

# 初始化 UART（波特率 115200）

uart = UART(1, 115200)
uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)

# 创建 IMU 对象（自动执行加速度校准与 Z 轴清零）

imu_obj = IMU(uart)

```

3. **数据读取与解析**：
	```python
while True:
    # 接收并解析六轴数据
    acc_x, acc_y, acc_z, temp, gyro_x, gyro_y, gyro_z, angle_x, angle_y, angle_z = imu_obj.RecvData()
    print(f"Angle: X={angle_x:.2f}°, Y={angle_y:.2f}°, Z={angle_z:.2f}°")
    time.sleep_ms(100)
```

---

## 示例程序

```python
# MicroPython v1.23.0
from machine import UART, Pin
import time
import gc
from imu import IMU

# 上电延时
time.sleep(3)
print("FreakStudio: MPU6050 6-Axis Gyroscope Test")

# 初始化 UART（与 IMU 通信）
uart = UART(1, 115200)
uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)

# 初始化 UART（与上位机通信）
uart_pc = UART(0, 115200)
uart_pc.init(bits=8, parity=None, stop=1, tx=0, rx=1, timeout=5)

# 初始化 LED 引脚
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# 创建 IMU 对象
imu_obj = IMU(uart)

try:
    while True:
        LED.on()
        # 接收六轴数据
        imu_obj.RecvData()
        LED.off()

        # 打印姿态角度
        print(f"X: {imu_obj.angle_x:.2f}° | Y: {imu_obj.angle_y:.2f}° | Z: {imu_obj.angle_z:.2f}°")
        
        # 发送角度数据到上位机
        angle_data = "{:.2f}, {:.2f}, {:.2f}\r\n".format(imu_obj.angle_x, imu_obj.angle_y, imu_obj.angle_z)
        uart_pc.write(angle_data)

        # 内存管理：触发垃圾回收
        if gc.mem_free() < 220000:
            gc.collect()

except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    LED.off()
    print("LED turned off, program exited.")
```

---

## 注意事项

1. **校准规范**：执行加速度校准或 Z 轴清零指令时，需保持传感器水平/垂直静止，避免数据偏移；校准过程需等待 500ms 完成。
2. **模式切换**：切换串口/I2C 模式或波特率后，需重新初始化对应通信接口，确保参数同步。
3. **内存管理**：长时间运行时，需定期触发垃圾回收（`gc.collect()`），避免内存溢出。
4. **应用限制**：模块为消费级精度，不可用于医疗诊断、高精度工业控制等对数据可靠性要求极高的场景。

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
