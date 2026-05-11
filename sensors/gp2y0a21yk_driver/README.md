# GP2Y0A21YK0F 模拟红外测距传感器驱动 - MicroPython版本

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本驱动为 Sharp GP2Y0A21YK0F 模拟红外测距传感器提供 MicroPython 接口，适用于 Raspberry Pi Pico 等 MicroPython 平台。传感器通过模拟电压输出反映被测物体距离，驱动将 ADC 原始值转换为毫伏电压，再经幂函数曲线拟合公式估算厘米距离，有效测距范围为 10～80 cm。适用于障碍物检测、近距离感知、机器人避障等场景。

---

## 主要功能

- 支持直接传入引脚编号或已创建的 ADC 对象进行初始化
- 可配置采样平均次数，有效降低 ADC 噪声
- 支持可选电源控制引脚，实现硬件级传感器开关
- 提供原始 ADC 值、毫伏电压、厘米距离三种读取接口
- 内置近距离/远距离阈值判断方法（`is_closer` / `is_farther`）
- 距离结果自动限幅至有效范围（10～80 cm）
- 支持调试输出模式，便于开发调试
- 提供 `deinit()` 方法安全释放资源

---

## 硬件要求

**推荐测试硬件：**
- Raspberry Pi Pico / Pico W（RP2040）
- Sharp GP2Y0A21YK0F 模拟红外测距传感器

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（5V，传感器需5V供电） |
| GND  | 电源负极 |
| Vo   | 模拟电压输出，接 MCU ADC 引脚（Pico GP26，即 ADC0） |

> 注意：传感器 Vo 输出电压最高约 3.1V，可直接接入 Pico 3.3V ADC 引脚，但传感器本身需要 5V 供电。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`（内置）、`time`（内置） |

---

## 文件结构

```
gp2y0a21yk_driver/
├── code/
│   ├── gp2y0a21yk.py   # 核心驱动
│   └── main.py          # 测试示例
├── LICENSE
├── package.json
└── README.md            # 说明文档
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/gp2y0a21yk.py` | GP2Y0A21YK0F 传感器核心驱动，包含 `GP2Y0A21YK` 类及所有公共 API |
| `code/main.py` | 完整使用示例，演示初始化、多次采样平均、距离读取及阈值判断 |
| `LICENSE` | MIT 开源许可证 |
| `package.json` | 包描述文件，含版本、作者、依赖信息 |

---

## 快速开始

### 步骤一：复制文件

将 `gp2y0a21yk.py` 复制到 MicroPython 设备根目录或项目目录。

### 步骤二：接线

| 传感器引脚 | Pico 引脚 |
|-----------|-----------|
| VCC       | VBUS（5V）|
| GND       | GND       |
| Vo        | GP26（ADC0）|

### 步骤三：运行示例

将以下 `main.py` 内容上传并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : hogeiha
# @File    : main.py
# @Description : GP2Y0A21YK0F红外测距传感器读取示例
# @License : MIT


# ======================================== 导入相关模块 =========================================

import time
from gp2y0a21yk import GP2Y0A21YK


# ======================================== 全局变量 ============================================

# 传感器模拟输出接入的Pico ADC引脚
DISTANCE_ADC_PIN = 26

# Pico ADC参考电压
ADC_REF_VOLTAGE = 3.3

# 采样平均次数
AVERAGE_COUNT = 5

# 数据读取间隔时间（毫秒）
PRINT_INTERVAL = 500

# 近距离判断阈值（厘米）
CLOSE_THRESHOLD_CM = 20

# 远距离判断阈值（厘米）
FAR_THRESHOLD_CM = 40


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: GP2Y0A21YK distance sensor")

# 创建GP2Y0A21YK0F传感器对象
sensor = GP2Y0A21YK(distance_pin=DISTANCE_ADC_PIN)

# 设置ADC参考电压
sensor.set_ref_voltage(ADC_REF_VOLTAGE)

# 设置采样平均次数
sensor.set_averaging(AVERAGE_COUNT)

# 启用传感器读取
sensor.set_enabled(True)

# 初始化上次打印时间戳
last_print_time = time.ticks_ms()


# ========================================  主程序  ============================================

try:
    while True:

        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 按间隔时间读取并打印传感器数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:

            # 读取ADC原始值
            raw = sensor.get_distance_raw()

            # 读取传感器输出电压
            voltage = sensor.get_distance_volt()

            # 读取估算距离
            distance = sensor.get_distance_centimeter()

            # 打印测量结果
            print(
                "Raw: {}, Voltage: {:.1f} mV, Distance: {} cm".format(
                    raw,
                    voltage,
                    distance,
                )
            )

            # 判断物体是否小于近距离阈值
            if sensor.is_closer(CLOSE_THRESHOLD_CM):
                print("Object is close")

            # 判断物体是否大于远距离阈值
            if sensor.is_farther(FAR_THRESHOLD_CM):
                print("Object is far")

            # 更新上次打印时间戳
            last_print_time = current_time

        # 短暂休眠降低CPU占用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 供电要求 | 传感器 VCC 必须接 5V，不可使用 3.3V 供电，否则测量结果不准确 |
| ADC 引脚电压 | Vo 输出最高约 3.1V，可直接接入 Pico 3.3V ADC 引脚，无需分压 |
| 有效测距范围 | 10～80 cm；超出范围时返回边界值（10 或 80），不代表真实距离 |
| 近距离盲区 | 小于 10 cm 时传感器输出电压反而下降，驱动将结果限幅为 10 cm |
| 采样平均 | 增大 `AVERAGE_COUNT` 可降低噪声，但每次读取延时增加（每次约 5ms × 次数） |
| 电源控制引脚 | `vcc_pin` 为可选参数；未接时 `set_enabled(False)` 仅改变软件状态，不断电 |
| 兼容性 | 驱动依赖 `machine.ADC.read_u16()`，适用于 MicroPython v1.20.0 及以上版本 |
| 拟合公式精度 | 距离估算使用幂函数曲线拟合（系数 29.988，指数 -1.173），为近似值，实际误差约 ±1～3 cm |

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-04-22 | hogeiha | 初始版本，实现基础测距、电压读取、阈值判断功能 |

---

## 联系方式

- **作者**：hogeiha
- **GitHub**：[https://github.com/hogeiha](https://github.com/hogeiha)

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
