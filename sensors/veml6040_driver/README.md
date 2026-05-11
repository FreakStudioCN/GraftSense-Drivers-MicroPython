# VEML6040 RGBW 颜色传感器驱动 - MicroPython版本

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [设计思路](#设计思路)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本驱动为 Vishay VEML6040 RGBW 颜色传感器提供 MicroPython I2C 接口，支持红、绿、蓝、白四通道颜色数据采集，可配置积分时间并支持自动连续和单次触发两种测量模式。驱动基于 `sensor_pack_2` 框架，提供迭代器协议和 Lux 换算辅助函数，并附带基础颜色识别算法示例。适用于颜色检测、环境光照监测、智能照明控制等场景。

---

## 主要功能

- 支持 RGBW 四通道 16 位原始 ADC 值读取
- 支持自动连续测量和单次触发两种模式
- 可配置积分时间（0～5，对应 40ms～1280ms）
- 积分时间与 G_SENSITIVITY / MAX_DETECTABLE_LUX 自动联动
- 提供 `get_g_max_lux()` 辅助函数，快速获取当前积分时间对应的灵敏度和最大可检测照度
- 实现 Python 迭代器协议，支持 `for colors in sensor` 连续采集（自动模式）
- 支持软件关断（`shutdown` 属性），低功耗待机
- I2C 总线自动扫描，地址固定 `0x10`
- 附带基础颜色识别算法（`detect_color`）和 Lux 计算函数（`get_als_lux`）

---

## 硬件要求

**推荐测试硬件：**
- Raspberry Pi Pico / Pico W（RP2040）
- Vishay VEML6040 RGBW 颜色传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.7V～3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（Pico GP5） |
| SDA  | I2C 数据线（Pico GP4） |

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `sensor_pack_2`（随驱动附带）、`machine`（内置）、`time`（内置）、`array`（内置） |

---

## 文件结构

```
veml6040_driver/
├── code/
│   ├── veml6040mod.py                 # 核心驱动
│   ├── main.py                        # 测试示例
│   └── sensor_pack_2/                 # 基础传感器框架包
│       ├── __init__.py                # 包初始化
│       ├── base_sensor.py             # 传感器基类与总线抽象
│       └── bus_service.py             # I2C/SPI 总线适配器
├── LICENSE
└── README.md                          # 说明文档
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/veml6040mod.py` | VEML6040 核心驱动，包含 `VEML6040` 类及 `get_g_max_lux()` 辅助函数，实现 RGBW 读取、积分时间配置、自动/单次模式、迭代器协议 |
| `code/main.py` | 完整使用示例，演示 I2C 初始化、单次测量模式、Lux 计算及基础颜色识别 |
| `code/sensor_pack_2/__init__.py` | 包版本信息 |
| `code/sensor_pack_2/base_sensor.py` | 传感器基类，提供 I2C/SPI 总线读写、字节序管理、迭代器协议基类 |
| `code/sensor_pack_2/bus_service.py` | I2C 和 SPI 总线适配器，封装 `machine.I2C`/`machine.SPI` 操作 |
| `LICENSE` | MIT 开源许可证 |

---

## 快速开始

### 步骤一：复制文件

将 `veml6040mod.py` 和整个 `sensor_pack_2/` 目录复制到 MicroPython 设备根目录。

### 步骤二：接线

| 传感器引脚 | Pico 引脚 |
|-----------|-----------|
| VCC       | 3.3V      |
| GND       | GND       |
| SCL       | GP5       |
| SDA       | GP4       |

### 步骤三：运行示例

将以下 `main.py` 内容上传并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : FreakStudio
# @File    : main.py
# @Description : VEML6040 RGBW 颜色传感器读取示例

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
from sensor_pack_2.bus_service import I2cAdapter
from veml6040mod import VEML6040, get_g_max_lux
import time

# ======================================== 全局变量 ============================================

# VEML6040 默认 I2C 地址
TARGET_SENSOR_ADDRS = [0x10]

# I2C 数据线连接到 Pico GPIO4
I2C_SDA_PIN = 4

# I2C 时钟线连接到 Pico GPIO5
I2C_SCL_PIN = 5

# I2C 通信频率设置为 400kHz
I2C_FREQ = 400000

# 积分时间配置为 80ms
INTEGRATION_TIME = 1

# ======================================== 功能函数 ============================================


def get_als_lux(green_channel: int, sensitivity: float) -> float:
    """
    根据绿色通道计算环境光照度。
    Args:
        green_channel (int): 绿色通道原始值。
        sensitivity (float): 当前积分时间对应的灵敏度。

    Raises:
        ValueError: 参数为空或取值非法时抛出。
        TypeError: 参数类型非法时抛出。

    Notes:
        VEML6040 使用绿色通道估算环境光照度。

    ==========================================
    Calculate ambient light lux from green channel.
    Args:
        green_channel (int): Green channel raw value.
        sensitivity (float): Sensitivity for current integration time.

    Raises:
        ValueError: Raised when parameter is None or invalid.
        TypeError: Raised when parameter type is invalid.

    Notes:
        VEML6040 estimates ambient lux from green channel.
    """
    if green_channel is None:
        raise ValueError("Green channel cannot be None")

    if sensitivity is None:
        raise ValueError("Sensitivity cannot be None")

    if not isinstance(green_channel, int):
        raise TypeError("Green channel must be integer")

    if sensitivity < 0:
        raise ValueError("Sensitivity must not be negative")

    return sensitivity * green_channel


def detect_color(red: int, green: int, blue: int, white: int) -> str:
    """
    根据 RGBW 原始通道识别基础颜色。
    Args:
        red (int): 红色通道原始值。
        green (int): 绿色通道原始值。
        blue (int): 蓝色通道原始值。
        white (int): 白光通道原始值。

    Raises:
        ValueError: 参数为空或取值非法时抛出。
        TypeError: 参数类型非法时抛出。

    Notes:
        该算法用于基础颜色判断，实际项目可按光源和外壳校准阈值。

    ==========================================
    Detect basic color from RGBW raw channels.
    Args:
        red (int): Red channel raw value.
        green (int): Green channel raw value.
        blue (int): Blue channel raw value.
        white (int): White channel raw value.

    Raises:
        ValueError: Raised when parameter is None or invalid.
        TypeError: Raised when parameter type is invalid.

    Notes:
        This algorithm is for basic color detection and can be calibrated.
    """
    channels = (red, green, blue, white)

    for value in channels:
        if value is None:
            raise ValueError("Color channel cannot be None")

        if not isinstance(value, int):
            raise TypeError("Color channel must be integer")

        if value < 0:
            raise ValueError("Color channel must not be negative")

    rgb_max = max(red, green, blue)
    rgb_min = min(red, green, blue)
    rgb_sum = red + green + blue

    if white < 20 or rgb_max < 10:
        return "Black"

    if rgb_sum == 0:
        return "Black"

    balance = rgb_max - rgb_min

    if balance < rgb_max * 0.18:
        if white > rgb_max * 1.2:
            return "White"

        return "Gray"

    red_ratio = red / rgb_sum
    green_ratio = green / rgb_sum
    blue_ratio = blue / rgb_sum

    if red_ratio > 0.45 and green_ratio > 0.35:
        return "Yellow"

    if green_ratio > 0.42 and blue_ratio > 0.32:
        return "Cyan"

    if red_ratio > 0.42 and blue_ratio > 0.32:
        return "Magenta"

    if red_ratio > green_ratio and red_ratio > blue_ratio:
        return "Red"

    if green_ratio > red_ratio and green_ratio > blue_ratio:
        return "Green"

    if blue_ratio > red_ratio and blue_ratio > green_ratio:
        return "Blue"

    return "Unknown"


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: VEML6040 RGBW color sensor")

# 初始化 I2C 总线
i2c_bus = I2C(id=0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")

# 判断是否扫描到 I2C 设备
if len(devices_list) == 0:
    print("No i2c device")
    raise SystemExit("I2C scan found no devices")

# 判断是否扫描到 VEML6040 默认地址
if TARGET_SENSOR_ADDRS[0] not in devices_list:
    print("VEML6040 address not found")
    raise SystemExit("No VEML6040 device found")

# 打印 VEML6040 地址
print("I2C hexadecimal address:", hex(TARGET_SENSOR_ADDRS[0]))

# 创建 I2C 适配器
adapter = I2cAdapter(i2c_bus)

# 创建 VEML6040 传感器对象
sensor = VEML6040(adapter)

# 确保传感器处于工作状态
if sensor.shutdown:
    sensor.shutdown = False

# 启动单次测量模式
sensor.start_measurement(integr_time=INTEGRATION_TIME, auto_mode=False)

# 获取测量等待时间
wait_time_ms = sensor.get_conversion_cycle_time()

# 获取当前积分时间对应的光照灵敏度
green_sensitivity, max_lux = get_g_max_lux(sensor.integration_time)

# 打印初始化信息
print("Sensor initialization successful")
print("Integration time:", sensor.integration_time)
print("Wait time ms:", wait_time_ms)
print("Green sensitivity:", green_sensitivity)
print("Max detectable lux:", max_lux)

# ========================================  主程序  ============================================

try:
    while True:
        # 等待单次测量完成
        time.sleep_ms(wait_time_ms)

        # 读取 RGBW 原始通道
        red, green, blue, white = sensor.get_colors()

        # 根据绿色通道计算 lux
        lux = get_als_lux(green, green_sensitivity)

        # 根据 RGBW 原始通道识别颜色
        color_name = detect_color(red, green, blue, white)

        # 打印英文格式的颜色和光照数据
        print(
            "Red: {}  Green: {}  Blue: {}  White: {}  Lux: {:.2f}  Color: {}".format(
                red,
                green,
                blue,
                white,
                lux,
                color_name,
            )
        )

        # 再次启动单次测量
        sensor.start_measurement(integr_time=INTEGRATION_TIME, auto_mode=False)
except KeyboardInterrupt:
    # 关闭传感器
    sensor.shutdown = True

    # 打印停止提示
    print("Measurement stopped")
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 供电要求 | 传感器工作电压 1.7V～3.6V，可直接接 Pico 3.3V |
| I2C 地址 | 固定地址 `0x10`，不可更改 |
| I2C 频率 | 示例使用 400kHz（Fast Mode） |
| 积分时间 | 索引 0～5 对应 40/80/160/320/640/1280ms；积分时间越长，灵敏度越高，但最大可检测照度越低 |
| 单次模式读取时序 | 单次模式下需先调用 `start_measurement()`，等待至少一个转换周期（`get_conversion_cycle_time()` 返回值）后再调用 `get_colors()` |
| 自动模式迭代器 | 使用 `for colors in sensor` 前必须先调用 `start_measurement(auto_mode=True)`；关断状态或非自动模式下迭代器返回 `None` |
| Lux 换算精度 | `get_als_lux()` 仅使用绿色通道估算，适用于白光光源；有色光源下结果偏差较大 |
| 颜色识别算法 | `detect_color()` 为基础比例算法，受光源色温和传感器安装角度影响，建议在实际使用环境中校准阈值 |
| 关断与唤醒 | `sensor.shutdown = True` 进入低功耗模式；`sensor.shutdown = False` 唤醒后需重新调用 `start_measurement()` |
| 兼容性 | 依赖 `sensor_pack_2` 框架，适用于 MicroPython v1.20.0 及以上版本 |

---

## 设计思路

**1. CONF 寄存器统一读写（`_settings()`）**
所有配置（积分时间、触发、自动/手动、关断）均通过同一个 `_settings()` 方法操作 CONF 寄存器（地址 `0x00`）。参数为 `None` 时表示不修改对应位，全部为 `None` 时执行只读操作返回当前寄存器值，避免多次 I2C 读写。

**2. 配置缓存（`_get_settings()`）**
初始化和每次 `start_measurement()` 后均调用 `_get_settings()` 从寄存器重新读取并缓存配置，确保 `integration_time`、`auto_mode`、`shutdown` 等属性与硬件状态一致。

**3. 积分时间与灵敏度联动（`get_g_max_lux()`）**
G_SENSITIVITY 和 MAX_DETECTABLE_LUX 均以积分时间 0（40ms）为基准，通过 `k = 1 / (1 << integr_time)` 线性缩放，无需查表，计算简洁。

**4. 迭代器协议**
`__next__()` 在关断或非自动模式时返回 `None` 而非抛出 `StopIteration`，使迭代器可无限运行，由调用方决定何时退出循环。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2022-01-01 | Roman Shevchik | 初始版本，实现 RGBW 读取、积分时间配置、自动/单次模式、迭代器协议 |

---

## 联系方式

- **作者**：Roman Shevchik
- **邮箱**：goctaprog@gmail.com
- **GitHub**：请填写作者 GitHub 地址

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
