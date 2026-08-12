# BMX055 九轴 IMU 传感器 MicroPython 驱动

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

## 简介

BMX055 是 Bosch Sensortec 推出的九轴惯性测量单元 (IMU)，内部集成了 BMA2X2 三轴加速度计、BMG160 三轴陀螺仪和 BMM050 三轴磁力计。本驱动包通过 I2C 总线与传感器通信，提供完整的九轴数据读取、量程配置、滤波器设置和传感器校准功能，适用于姿态估计、运动检测、导航等嵌入式应用场景。

## 主要功能

- 九轴数据同步读取：加速度 (g)、角速度 (deg/s)、磁场强度 (μT)
- 加速度计量程可配置：2 / 4 / 8 / 16 g
- 陀螺仪量程可配置：125 / 250 / 500 / 1000 / 2000 deg/s
- 可调数字滤波器带宽，适配不同采样频率
- 内置传感器快速/慢速校准补偿
- 芯片温度读取
- 加速度计数据到横滚角/俯仰角的姿态解算工具
- 完整的参数校验与异常处理
- 调试日志开关，方便开发排查

## 硬件要求

### 推荐测试硬件

- BMX055 九轴传感器模块
- 支持 MicroPython 的开发板（ESP32 / RP2040 等）
- 杜邦线若干

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例接 GPIO5） |
| SDA  | I2C 数据线（示例接 GPIO4） |
| PS | 接 `3.3V`，选择 I²C 。接 `GND`，选择 SPI |
| SDO1 | 加速度计和磁力计地址选择                 |
| SDO2 | 陀螺仪数据地址选择 |
| CSB3 | 磁力计片选/地址选择 |

### BMX055 内部 I2C 地址

| 子传感器 | 芯片型号 | I2C 地址 |
|----------|----------|----------|
| 加速度计 | BMA2X2 | 0x18 (24) |
| 陀螺仪   | BMG160 | 0x68 (104) |
| 磁力计   | BMM050 | 0x10 (16) |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`（内置）、`math`（内置）、`micropython`（内置） |
| 开发板平台 | ESP32 / RP2040 / 任何支持 I2C 的 MicroPython 板 |

## 文件结构

```
bmx055_driver/
├── code/
│   ├── bmx055.py      # BMX055 九轴 IMU 复合驱动
│   ├── bma2x2.py      # BMA2X2 三轴加速度计驱动
│   ├── bmg160.py      # BMG160 三轴陀螺仪驱动
│   ├── bmm050.py      # BMM050 三轴磁力计驱动
│   ├── attitude.py    # 姿态解算工具（roll/pitch）
│   └── main.py        # 测试示例代码
├── package.json       # mip 包配置
├── README.md          # 说明文档
└── LICENSE            # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `bmx055.py` | BMX055 复合驱动，组合 BMA2X2/BMG160/BMM050 三个子传感器，提供统一的初始化和资源释放接口 |
| `bma2x2.py` | BMA2X2 三轴加速度计 I2C 驱动，支持量程/滤波器配置、校准补偿和温度读取 |
| `bmg160.py` | BMG160 三轴陀螺仪 I2C 驱动，支持量程/滤波器配置和校准补偿 |
| `bmm050.py` | BMM050 三轴磁力计 I2C 驱动，支持三轴磁场和霍尔电阻数据读取 |
| `attitude.py` | 姿态解算工具，从加速度计数据计算横滚角 (roll) 和俯仰角 (pitch) |
| `main.py` | 测试示例，包含 I2C 扫描、芯片 ID 验证、九轴数据循环读取及手动测试函数 |

## 快速开始

### 1. 将驱动文件复制到 MicroPython 设备

将所有 `.py` 文件上传到设备文件系统根目录或 `/lib/` 下。

### 2. 硬件接线

| BMX055 模块 | 开发板              |
| ----------- | ------------------- |
| VCC         | 3.3V                |
| GND         | GND                 |
| SCL         | GPIO5               |
| SDA         | GPIO4               |
| PS          | 3.3V（选择I2C模式） |
| SDO1        | GND                 |
| SDO2        | GND                 |
| CSB3        | GND                 |

### 3. 最小可运行示例

```python
from machine import I2C, Pin
from bmx055 import BMX055
from attitude import angles

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(5), sda=Pin(4))

# 初始化 BMX055
bmx = BMX055(i2c)

# 读取九轴数据
accel = bmx.accel.xyz()   # (x, y, z) 加速度 (g)
gyro = bmx.gyro.xyz()     # (x, y, z) 角速度 (deg/s)
mag = bmx.mag.xyz()       # (x, y, z) 磁场强度 (μT)
temp = bmx.accel.temperature()  # 温度 (℃)

# 计算姿态角
roll, pitch = angles(accel)

print("Accel: X=%.3f Y=%.3f Z=%.3f g" % accel)
print("Gyro:  X=%.1f Y=%.1f Z=%.1f deg/s" % gyro)
print("Mag:   X=%.1f Y=%.1f Z=%.1f uT" % mag)
print("Roll=%.2f Pitch=%.2f Temp=%.1fC" % (roll, pitch, temp))
```

### 4. 运行完整测试脚本

将以下 `main.py` 复制到设备并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Sebastian Plamauer
# @File    : main.py
# @Description : Bosch BMX055 九轴 IMU 测试代码
# @License : MIT


# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin

from bmx055 import BMX055
from attitude import angles

# ======================================== 全局变量 ============================================
# 打印间隔 (ms)
_PRINT_INTERVAL_MS = 1000

# BMX055 内部固定 I2C 地址
_EXPECTED_ACCEL_ADDR = 24   # BMA2X2: 0x18
_EXPECTED_GYRO_ADDR = 104   # BMG160: 0x68
_EXPECTED_MAG_ADDR = 16     # BMM050: 0x10

# BMA2X2 芯片 ID 寄存器与期望值
_CHIP_ID_REG_ACCEL = 0x00
_CHIP_ID_EXPECT_ACCEL = 0x03


# ======================================== 功能函数 ============================================
def test_range_switch(sensor: BMX055) -> None:
    """
    测试加速度计量程切换功能（正常/边界场景）
    可在 REPL 中手动调用：test_range_switch(bmx)
    """
    # 正常量程测试
    for r in (2, 4, 8, 16):
        sensor.accel.set_range(r)
        readback = sensor.accel.get_range()
        print("set_range(%d) -> get_range() = %d" % (r, readback))
    # 边界值测试
    sensor.accel.set_range(2)
    print("range restored to 2g")

    # 异常量程测试
    try:
        sensor.accel.set_range(3)
    except ValueError as e:
        print("Expected ValueError for range=3: %s" % e)


def test_gyro_range_switch(sensor: BMX055) -> None:
    """
    测试陀螺仪量程切换功能
    可在 REPL 中手动调用：test_gyro_range_switch(bmx)
    """
    for r in (125, 250, 500, 1000, 2000):
        sensor.gyro.set_range(r)
        readback = sensor.gyro.get_range()
        print("set_range(%d) -> get_range() = %d" % (r, readback))
    sensor.gyro.set_range(125)
    print("range restored to 125deg/s")


def test_filter_bw_switch(sensor: BMX055) -> None:
    """
    测试加速度计滤波器带宽切换功能（正常/边界场景）
    可在 REPL 中手动调用：test_filter_bw_switch(bmx)
    """
    valid_bw = (8, 16, 32, 64, 128, 256, 512, 1024)
    for bw in valid_bw:
        sensor.accel.set_filter_bw(bw)
        readback = sensor.accel.get_filter_bw()
        print("set_filter_bw(%d) -> get_filter_bw() = %d" % (bw, readback))
    sensor.accel.set_filter_bw(128)
    print("filter restored to 125Hz")

    # 异常带宽测试
    try:
        sensor.accel.set_filter_bw(100)
    except ValueError as e:
        print("Expected ValueError for bw=100: %s" % e)


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Using Bosch BMX055 9-axis IMU ...")

# I2C 总线初始化
i2c = I2C(0, scl=Pin(5), sda=Pin(4))

# I2C 设备扫描
addresses = i2c.scan()
if not addresses:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found at: %s" % [hex(addr) for addr in addresses])

# 验证目标设备地址
for expected_addr, name in (
    (_EXPECTED_ACCEL_ADDR, "BMA2X2 accelerometer"),
    (_EXPECTED_GYRO_ADDR, "BMG160 gyroscope"),
    (_EXPECTED_MAG_ADDR, "BMM050 magnetometer"),
):
    if expected_addr in addresses:
        print("%s found at 0x%02X" % (name, expected_addr))
    else:
        print("WARNING: %s not found at 0x%02X" % (name, expected_addr))

# 芯片 ID 验证（加速度计）
try:
    chip_id = i2c.readfrom_mem(_EXPECTED_ACCEL_ADDR, _CHIP_ID_REG_ACCEL, 1)[0]
    if chip_id == _CHIP_ID_EXPECT_ACCEL:
        print("BMA2X2 chip ID verified: 0x%02X" % chip_id)
    else:
        print("BMA2X2 chip ID mismatch: expected 0x%02X, got 0x%02X" % (_CHIP_ID_EXPECT_ACCEL, chip_id))
except OSError as e:
    print("Failed to read chip ID: %s" % e)

# BMX055 复合驱动初始化
bmx = BMX055(i2c)
print("BMX055 initialized successfully")

last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= _PRINT_INTERVAL_MS:
            # 读取加速度计数据
            accel_data = bmx.accel.xyz()
            # 读取陀螺仪数据
            gyro_data = bmx.gyro.xyz()
            # 读取磁力计数据
            mag_data = bmx.mag.xyz()
            # 读取芯片温度
            temp = bmx.accel.temperature()
            # 计算横滚角和俯仰角
            roll, pitch = angles(accel_data)

            print("Accel(g):  X=%7.3f  Y=%7.3f  Z=%7.3f" % accel_data)
            print("Gyro(d/s): X=%7.1f  Y=%7.1f  Z=%7.1f" % gyro_data)
            print("Mag(uT):   X=%7.1f  Y=%7.1f  Z=%7.1f" % mag_data)
            print("Roll=%6.2f  Pitch=%6.2f  Temp=%.1fC" % (roll, pitch, temp))
            print("---")

            last_print_time = current_time

        # 高频测试函数 — 注释默认执行，可在 REPL 中手动调用
        # test_range_switch(bmx)
        # test_gyro_range_switch(bmx)
        # test_filter_bw_switch(bmx)

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    bmx.deinit()
    del bmx
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.4V ~ 3.6V（推荐 3.3V），超出范围可能损坏传感器 |
| I2C 地址 | BMX055 三个子传感器使用固定 I2C 地址（0x18 / 0x68 / 0x10），不可更改；避免同总线地址冲突 |
| 量程限制 | 加速度计最大 16g，陀螺仪最大 2000 deg/s；超出量程数据饱和 |
| 校准建议 | 首次使用建议运行 `compensation()` 进行传感器校准；长时间工作后可重新校准以消除温漂 |
| 姿态解算 | `attitude.angles()` 使用 atan 公式，仅适用于静态/准静态场景；动态场景需结合陀螺仪使用融合算法 |
| 初始化顺序 | `BMX055.__init__()` 内部依次初始化三个子传感器并执行校准，过程约需 0.3 秒 |
| 兼容性 | 本驱动仅支持 I2C 通信模式（BMX055 默认配置） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-24 | Sebastian Plamauer | 初始版本：九轴数据读取、量程/滤波器配置、校准补偿、姿态解算 |

## 联系方式

- 作者：Sebastian Plamauer
- 邮箱：oeplse@gmail.com
- GitHub：[https://github.com/oeplse](https://github.com/oeplse)

## 许可协议

MIT License

Copyright (c) 2016-2026 Sebastian Plamauer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
