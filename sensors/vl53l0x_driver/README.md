# GraftSense VL53L0X 激光测距模块 （MicroPython）

# GraftSense VL53L0X 激光测距模块驱动 （MicroPython 驱动）

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

本项目为 **GraftSense VL53L0X-based Laser Ranging Module V1.1** 提供了完整的 MicroPython 驱动支持，基于飞行时间（ToF）原理实现高精度距离检测。驱动支持单测、连续测距、定时测距三种工作模式，可稳定传输 0-200cm 范围内的精准测距数据（绝对精度 ±3% 以内），不受目标颜色、材质影响，刷新频率最高可达 10Hz，适用于无人机避障、智能仓储、机器人导航与距离检测等场景，为非接触式精准测距类应用提供可靠的数据交互能力。

---

## 主要功能

- ✅ 支持 I2C 数字通信，默认地址为 0x29（可按需配置），兼容 3.3V 电平
- ✅ 提供三种测距模式：单测模式（单次触发）、连续测距模式（自动循环）、定时连续测距模式（自定义间隔）
- ✅ 支持测量时间预算配置、信号速率限制、VCSEL 脉冲周期调节等参数优化
- ✅ 内置传感器初始化校准（SPAD 配置、VHV 校准），确保测量精度
- ✅ 提供超时检测机制，避免 I2C 通信或测量过程中阻塞
- ✅ 遵循 Grove 接口标准，兼容主流开发板与传感器生态

---

## 硬件要求

1. **核心硬件**：GraftSense VL53L0X-based Laser Ranging Module V1.1 激光测距模块（基于 VL53L0CX 芯片，内置 DC-DC 5V 转 3.3V 电路）
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等）
3. **接线配件**：Grove 4Pin 线（用于连接模块的 SDA、SCL、VCC、GND 引脚与开发板）
4. **电源**：3.3V~5V 稳定电源（模块通过 DC-DC 电路转换为 3.3V 为传感器供电）

---

## 文件说明

---

## 软件设计核心思想

1. **底层寄存器封装**：通过 I2C 寄存器读写操作封装传感器底层通信，隐藏硬件细节，提供简洁的上层 API
2. **多模式测距支持**：支持单测、连续、定时三种测距模式，适配不同场景的实时性与功耗需求
3. **校准与精度保障**：内置 SPAD 配置、VHV 校准等初始化流程，确保测量精度与稳定性
4. **可配置参数优化**：支持测量时间预算、信号速率限制、VCSEL 周期等参数调节，平衡精度与响应速度
5. **超时与异常处理**：关键操作（如校准、测距）均设置超时机制，避免硬件异常导致程序阻塞
6. **可移植性设计**：依赖标准 MicroPython I2C 接口，便于移植到不同硬件平台

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `vl53l0x.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线将模块的 SDA、SCL 引脚连接至开发板指定 I2C 引脚（如树莓派 Pico 的 GP4=SDA、GP5=SCL）
- 连接 VCC（3.3V~5V）和 GND 引脚，确保供电稳定
- 模块默认 I2C 地址为 0x29，避免与总线上其他设备地址冲突

### 代码配置

- 在 `main.py` 中根据硬件连接修改 I2C 初始化参数（如 `scl`、`sda` 引脚）
- 如需修改测距模式，可调整 `start()` 方法的 `period` 参数（0 为单测，非 0 为定时测距）

### 运行测试

- 重启开发板，`main.py` 将自动执行 I2C 设备扫描、传感器初始化，并进入连续测距模式，实时打印距离数据

---

## 示例程序

```python
# 导入驱动模块
import time
import machine
from vl53l0x import VL53L0X

# 初始化I2C（树莓派Pico示例）
i2c = machine.I2C(0, scl=5, sda=4, freq=100000)

# 扫描I2C设备并获取传感器地址
devices = i2c.scan()
sensor_addr = next((d for d in devices if d == 0x29), None)

if sensor_addr:
    # 初始化VL53L0X传感器
    tof = VL53L0X(i2c, sensor_addr)
    print("传感器初始化成功")
    
    try:
        # 启动连续测距模式
        tof.start()
        while True:
            distance = tof.read()
            if 0 < distance < 2000:
                print(f"当前距离：{distance} mm")
            else:
                print("超出测量范围或读取错误")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("程序终止")
    finally:
        tof.stop()
        print("测距停止")
else:
    print("未检测到VL53L0X传感器")
```

---

## 注意事项

1. **地址与电平**：模块默认 I2C 地址为 0x29，仅支持 3.3V 通信，避免直接接入 5V 电平导致损坏
2. **测量范围**：有效测量范围为 0-200cm，超出范围可能返回无效值，强光环境下精度会受影响
3. **校准重要性**：传感器初始化时会自动执行校准，校准后精度更高，请勿随意跳过校准流程
4. **模式选择**：

   - 单测模式适合 “触发一次” 的点测需求，无需额外停止操作
   - 连续测距模式适合实时动态跟踪，需主动调用 `stop()` 停止
   - 定时连续模式适合周期性采样，需提前通过 API 设置间隔时间
5. **I2C 速率**：建议 I2C 频率设置为 100kHz，过高速率可能导致通信不稳定

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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