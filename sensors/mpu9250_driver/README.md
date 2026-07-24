# MPU9250 九轴运动追踪传感器 MicroPython 驱动

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

MPU9250 是一款系统级封装（SiP）九轴运动追踪传感器，内部集成两颗芯片：**MPU6500**（三轴陀螺仪 + 三轴加速度计）和 **AK8963**（三轴磁力计）。本驱动通过 I2C 总线与传感器通信，封装了 MPU6500 和 AK8963 的底层寄存器操作，提供简洁的属性式 API 读取全部九轴数据。

适用于姿态解算、惯性导航、运动追踪、无人机飞控等需要九轴 IMU 数据的嵌入式应用场景。

## 主要功能

- **九轴数据读取**：单次调用即可获取加速度（m/s²）、角速度（rad/s）、磁场（μT）、温度（℃）
- **组合驱动架构**：MPU9250 作为外观类（Facade），内部组合 MPU6500 和 AK8963 实例，也可独立使用子驱动
- **可注入子驱动实例**：构造时支持传入预配置的 MPU6500 / AK8963 实例，灵活控制量程和单位
- **陀螺仪零偏校准**：通过 `mpu6500.calibrate()` 自动采集静止数据计算零偏
- **磁力计硬铁/软铁校准**：通过 `ak8963.calibrate()` 自动采集多方向数据，计算硬铁偏移和软铁比例
- **出厂灵敏度补偿**：自动读取 AK8963 Fuse ROM 中的轴向灵敏度校准系数
- **单位缩放因子**：加速度支持 m/s² 和 g 两种单位，陀螺仪支持 rad/s 和 °/s
- **I2C 旁路模式**：初始化时自动启用 I2C 旁路，直接访问 AK8963
- **上下文管理器**：支持 `with` 语句，退出时自动释放资源
- **可配置重试机制**：I2C 通信失败自动重试，提高通信可靠性

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| MPU9250 模块 | 九轴运动追踪传感器模块（如 GY-91 / GY-9250） |
| ESP32 / RP2040 开发板 | 支持 MicroPython 的主控板 |
| 杜邦线 ×4 | VCC、GND、SCL、SDA 连接线 |

### 引脚说明

| MPU9250 引脚 | 功能描述 | ESP32 连接 |
|-------------|----------|-----------|
| VCC | 电源正极（3.3V） | 3.3V |
| GND | 电源负极 | GND |
| SCL | I2C 时钟线 | GPIO22 |
| SDA | I2C 数据线 | GPIO21 |

## 软件环境

| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0 或更高版本 |
| 驱动版本 | v0.4.0 |
| 依赖库 | 无外部依赖（仅使用 `micropython`、`ustruct`、`utime` 标准库） |

## 文件结构

```
mpu9250/
├── mpu9250.py         # MPU9250 主驱动（九轴外观类）
├── mpu6500.py         # MPU6500 六轴陀螺仪/加速度计驱动
├── ak8963.py          # AK8963 三轴磁力计驱动
├── main.py            # 测试示例程序
├── LICENSE            # MIT 许可证
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `mpu9250.py` | MPU9250 外观类（Facade），组合 MPU6500 和 AK8963，启用 I2C 旁路模式，提供统一九轴数据接口 |
| `mpu6500.py` | MPU6500 六轴陀螺仪/加速度计底层驱动，含寄存器读写、量程配置、零偏校准 |
| `ak8963.py` | AK8963 三轴磁力计底层驱动，含 Fuse ROM 校准读取、硬铁/软铁校准 |
| `main.py` | 完整测试示例，含 I2C 扫描、设备验证、九轴数据采集、校准函数入口 |

## 快速开始

1. 将 `mpu9250.py`、`mpu6500.py`、`ak8963.py` 复制到 MicroPython 设备的 `/lib/` 或根目录
2. 按引脚说明接线（SCL→GPIO22, SDA→GPIO21）
3. 运行 `main.py` 或使用以下最小示例：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 MPU9250 九轴运动追踪传感器驱动类
# @License : MIT

import micropython
micropython.alloc_emergency_exception_buf(100)

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time

from mpu9250 import MPU9250

# ======================================== 全局变量 ============================================

# I2C 引脚配置（请根据实际接线修改）
I2C_SCL_PIN = const(22)
I2C_SDA_PIN = const(21)
I2C_FREQ = const(400000)

# 设备 I2C 地址
MPU9250_ADDR = const(0x68)
# MPU9250 SIP 模式 WHOAMI 期望值（0x71=集成磁力计, 0x70=独立 MPU6500）
EXPECTED_WHOAMI = const(0x71)

# 打印间隔（ms）
PRINT_INTERVAL_MS = const(2000)

# 全局时间追踪（用于主循环低频打印控制）
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================


def calibrate_gyro(sensor, count=256):
    """
    陀螺仪零偏校准。

    采集 count 次静止数据，计算零偏并更新内部补偿值。
    默认注释调用，可 REPL 手动触发。

    Args:
        sensor (MPU9250): 传感器实例
        count (int): 采样次数，默认 256

    Notes:
        - 校准期间传感器必须保持静止
    """
    print("Starting gyroscope calibration...")
    print(">>> Keep sensor STILL!")
    # 通过子驱动 mpu6500 执行陀螺仪零偏校准
    offset = sensor.mpu6500.calibrate(count, 0)
    print("Gyro offset (rad/s): X=%.5f Y=%.5f Z=%.5f" % offset)
    return offset


def calibrate_magnetometer(sensor, count=256, delay=200):
    """
    磁力计硬铁/软铁校准。

    采集多组磁场数据，计算硬铁偏移（圆心偏移）和软铁比例（椭圆校正）。
    默认注释调用，可 REPL 手动触发。

    Args:
        sensor (MPU9250): 传感器实例
        count (int): 采样次数，默认 256
        delay (int): 采样间隔（ms），默认 200

    Notes:
        - 校准期间需缓慢旋转传感器覆盖各方向
    """
    print("Starting magnetometer calibration...")
    print(">>> Slowly rotate sensor in ALL directions!")
    # 通过子驱动 ak8963 执行磁力计校准
    offset, scale = sensor.ak8963.calibrate(count, delay)
    print("Hard-iron offset (μT): X=%.2f Y=%.2f Z=%.2f" % offset)
    print("Soft-iron scale:       X=%.4f Y=%.4f Z=%.4f" % scale)
    return offset, scale


def print_nine_axis(sensor, interval_ms=PRINT_INTERVAL_MS):
    """
    定时打印全部九轴传感器数据。

    在指定间隔到达时读取并格式化输出加速度、陀螺仪、磁场和温度。

    Args:
        sensor (MPU9250): 传感器实例
        interval_ms (int): 打印间隔（ms）
    """
    global last_print_time
    current_time = time.ticks_ms()

    if time.ticks_diff(current_time, last_print_time) >= interval_ms:
        # 读取九轴数据
        ax, ay, az = sensor.acceleration
        gx, gy, gz = sensor.gyro
        mx, my, mz = sensor.magnetic
        temp = sensor.temperature

        # 格式化输出
        print("=" * 62)
        print("Accel  (m/s²):  X=%+8.2f  Y=%+8.2f  Z=%+8.2f" % (ax, ay, az))
        print("Gyro   (rad/s):  X=%+8.3f  Y=%+8.3f  Z=%+8.3f" % (gx, gy, gz))
        print("Magnet (μT):     X=%+8.1f  Y=%+8.1f  Z=%+8.1f" % (mx, my, mz))
        print("Temperature (℃): %.1f" % temp)

        last_print_time = current_time

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时，等待传感器稳定
time.sleep(3)

print("FreakStudio: MPU9250 9-axis IMU driver test")
print("=" * 62)

# 初始化 I2C 总线
print("Initializing I2C bus (SCL=GPIO%d, SDA=GPIO%d, %dkHz)..." %
      (I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ // 1000))
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# I2C 总线设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

# 验证 MPU9250 是否在预期地址上
if MPU9250_ADDR not in devices:
    raise RuntimeError(
        "MPU9250 not found at expected address 0x%02X" % MPU9250_ADDR
    )
print("Device found at 0x%02X" % MPU9250_ADDR)

# 初始化 MPU9250 传感器（组合 MPU6500 + AK8963）
print("Initializing MPU9250...")
sensor = MPU9250(i2c)

# 验证芯片 ID
whoami = sensor.whoami
if whoami == EXPECTED_WHOAMI:
    print("Device verified: MPU9250 SIP (WHOAMI=0x%02X)" % whoami)
else:
    print("Warning: unexpected WHOAMI=0x%02X (expected 0x%02X)" %
          (whoami, EXPECTED_WHOAMI))

# 验证磁力计子驱动
ak8963_id = sensor.ak8963.whoami
print("AK8963 WHOAMI: 0x%02X" % ak8963_id)
# 显示出厂 Fuse ROM 灵敏度校准系数
print("Fuse ROM adjustment: X=%.4f Y=%.4f Z=%.4f" % sensor.ak8963.adjustement)

print("=" * 62)
print("Starting 9-axis data acquisition...")
print("Tips:")
print("  - Press Ctrl+C to stop")
print("  - calibrate_gyro(sensor)     in REPL to calibrate gyro (keep still)")
print("  - calibrate_magnetometer(sensor) in REPL to calibrate magnetometer (rotate)")
print("")

# ========================================  主程序  ===========================================

try:
    while True:
        # 低频自动执行：定时打印九轴数据
        print_nine_axis(sensor, PRINT_INTERVAL_MS)

        # 高频采集函数（注释默认执行，可 REPL 手动调用）
        # 如需 100Hz 无打印数据采集，取消下行注释：
        # raw_accel = sensor.acceleration
        # raw_gyro = sensor.gyro
        # raw_mag = sensor.magnetic

        # 校准函数（注释默认执行，需手动触发）
        # calibrate_gyro(sensor)          # 陀螺仪零偏校准（保持静止）
        # calibrate_magnetometer(sensor)  # 磁力计硬铁/软铁校准（缓慢旋转）

        # 短暂延时避免总线过载
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("\nProgram interrupted by user")
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

## 注意事项

| 类别 | 说明 |
|------|------|
| **工作电压** | MPU9250 典型工作电压 3.3V，部分模块支持 5V（需确认模块规格） |
| **I2C 地址** | MPU6500/MPU9250 默认地址 `0x68`（AD0 接地），可接高改为 `0x69`；AK8963 固定地址 `0x0C` |
| **I2C 旁路** | AK8963 通过 MPU6500 的 I2C 旁路访问，`MPU9250.__init__()` 自动启用；若独立使用 AK8963 需手动开启旁路 |
| **陀螺仪校准** | 校准时传感器必须保持完全静止，否则零偏值不准确 |
| **磁力计校准** | 校准时需缓慢旋转传感器覆盖所有方向（至少 1 分钟）；建议将校准结果存入 NVRAM 避免每次启动重复校准 |
| **测量范围** | 加速度 ±2g/±4g/±8g/±16g 可配；陀螺仪 ±250/±500/±1000/±2000°/s 可配；磁力计 ±4900μT 固定 |
| **兼容性** | 兼容 MPU9250（0x71）、MPU6500（0x70）、MPU6700（0x90）WHOAMI |
| **软复位** | 软复位后如遇 `OSError: 26` 或 `i2c driver install error`，请执行硬复位（断电重启） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.4.0 | 2024-07-24 | Mika Tuupola | 规范化：添加中英双语 docstring、参数校验、类型注解、deinit()、__slots__、重试机制、debug 日志开关、OSError 包装重抛 |

## 联系方式

- **GitHub**: [tuupola/micropython-mpu9250](https://github.com/tuupola/micropython-mpu9250)
- **Email**: tuupola@appelsiini.net

## 许可协议

MIT License

Copyright (c) 2018-2023 Mika Tuupola

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
