# BNO055 九轴惯性测量单元 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [API 参考](#api-参考)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本驱动为 Bosch BNO055 九轴惯性测量单元（IMU）提供完整的 MicroPython 支持。BNO055 芯片内置硬件传感器融合引擎，可直接输出欧拉角、四元数、线性加速度和重力矢量等融合数据，无需在 MCU 端进行复杂的数学运算。

驱动基于 [Adafruit CircuitPython 驱动](https://github.com/adafruit/Adafruit_CircuitPython_BNO055) 移植并扩展，支持 13 种工作模式切换、传感器量程/带宽配置、轴重映射（车载坐标系）、ISR 安全数据读取和校准偏移保存/恢复。

## 主要功能

- **硬件传感器融合**：芯片内置融合算法，直接输出姿态角、四元数等融合数据
- **13 种工作模式**：支持 NDOF、IMUplus、Compass、M4G 等全部芯片模式
- **传感器配置**：可独立配置加速度计量程（2~16G）/带宽（8~1000Hz）、陀螺仪量程（125~2000dps）/带宽（12~523Hz）、磁力计采样率（2~30Hz）
- **轴重映射**：支持车载/设备坐标系变换，通过 `transpose` 和 `sign` 参数实现任意方向安装
- **ISR 安全读取**：提供 `iget()` 方法和预分配缓冲区，支持在中断服务例程中读取数据
- **校准管理**：校准状态查询、校准偏移值保存/恢复
- **双文件架构**：`bno055_base.py` 为轻量基类（~9.7KB），适用于 RAM 受限设备；`bno055.py` 为完整驱动
- **跨平台**：支持 Pyboard、ESP32、ESP8266、Raspberry Pi Pico 等所有支持 `machine` 模块的平台

## 硬件要求

### 推荐测试硬件

- [Adafruit BNO055  breakout 板](https://www.adafruit.com/product/2472)
- 其他基于 Bosch BNO055 的模块（注意部分模块无外部晶振）

### 引脚连接

BNO055 使用 I2C 通信接口。以下接线以 Raspberry Pi Pico 为例（`SoftI2C`）：

| BNO055 引脚 | Pico 引脚 | 功能描述 |
|-------------|-----------|----------|
| VIN / VCC   | 3V3(OUT)  | 电源正极（3.3V-5V，Adafruit 板载稳压器） |
| GND         | GND       | 电源负极 |
| SCL         | GP17      | I2C 时钟线（可自定义） |
| SDA         | GP16      | I2C 数据线（可自定义） |
| INT         | （可选）   | 中断输出引脚（本驱动未使用） |

> **注意**：SCL 和 SDA 需要外接上拉电阻（典型 4.7KΩ-10KΩ 到 3.3V）。Pyboard 的 I2C(1)/I2C(2) 和 Adafruit BNO055 板已内置上拉。Raspberry Pi Pico 和多数 ESP32 板 **无内置上拉**，需外加 1KΩ-4.7KΩ 电阻。

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.18+（推荐 v1.23+） |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖（仅使用 `machine`、`utime`、`ustruct`、`micropython` 内置模块） |

## 文件结构

```
bno055_driver/
├── bno055_base.py    # BNO055 基类驱动（轻量版，可独立使用）
├── bno055.py         # BNO055 完整驱动（包含轴映射、配置、ISR）
├── main.py           # 测试示例程序
├── examples/bno055_test.py    # 原始简单测试程序
├── package.json      # mip 包配置文件
├── README.md         # 说明文档
└── LICENSE           # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `bno055_base.py` | BNO055 基类驱动。提供 I2C 通信、芯片检测、工作模式切换、传感器数据读取（mag/accel/gyro/euler/quaternion 等）、校准状态查询和偏移读写。可独立用于 RAM 受限设备。 |
| `bno055.py` | BNO055 完整驱动。继承基类，增加轴重映射（`orient()`）、传感器配置（`config()`）、ISR 安全数据读取（`iget()`）、模式常量定义。**推荐使用此文件。** |
| `main.py` | 完整测试程序。包含 I2C 总线扫描+芯片 ID 验证、全部公共 API 调用示例（自动执行+注释手动调用）、校准保存/恢复、异常测试场景。 |
| `examples/bno055_test.py` | 原始简单测试程序。保留作为最小化参考示例。 |

## 快速开始

### 1. 复制文件到设备

将 `bno055_base.py` 和 `bno055.py` 上传到 MicroPython 设备的 `/lib/` 或根目录：

```bash
mpremote cp bno055_base.py :/lib/bno055_base.py
mpremote cp bno055.py :/lib/bno055.py
```

### 2. 硬件接线

按 [硬件要求](#硬件要求) 中的引脚表连接 BNO055 模块。

### 3. 运行测试

将 `main.py` 上传到设备根目录并运行，或将以下最小代码粘贴到 REPL：

```python
import machine
import time
from bno055 import *

# 初始化 I2C（根据平台选择 SoftI2C 或硬件 I2C）
i2c = machine.SoftI2C(sda=machine.Pin(16), scl=machine.Pin(17), timeout=1000)

# 创建 BNO055 实例
imu = BNO055(i2c)

# 等待校准并读取姿态
while True:
    time.sleep(1)
    if imu.calibrated():
        heading, roll, pitch = imu.euler()
        print("Heading: %4.0f  Roll: %4.0f  Pitch: %4.0f" % (heading, roll, pitch))
    else:
        print("Calibrating... sys:%d gyro:%d accel:%d mag:%d" % tuple(imu.cal_status()))
```

### 完整测试代码

`main.py` 包含 I2C 扫描验证、全部 API 调用（自动+手动）、边界参数测试和异常测试：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Peter Hinch
# @File    : main.py
# @Description : 测试 BNO055 九轴 IMU 驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import machine
import time
from bno055 import *

# ======================================== 全局变量 ============================================

# BNO055 芯片 ID 寄存器地址与期望值
CHIP_ID_REG = 0x00
CHIP_ID_VAL = 0xA0
# BNO055 默认 I2C 地址（DOF 引脚低电平）
BNO055_ADDR = 0x28
# 主循环打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = time.ticks_ms()
# BNO055 驱动实例
imu = None

# ======================================== 功能函数 ============================================

def scan_i2c_bus(i2c, target_addr):
    """
    扫描 I2C 总线并验证 BNO055 设备是否存在。

    Args:
        i2c: I2C 总线实例
        target_addr: 预期的 BNO055 I2C 地址（7 位）

    Raises:
        RuntimeError: 总线上无设备或 BNO055 未找到
    """
    # 扫描 I2C 总线
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    print("I2C scan: %s" % [hex(d) for d in devices])
    # 验证 BNO055 是否在预期地址
    if target_addr not in devices:
        raise RuntimeError("BNO055 not found at 0x%02X, found: %s" % (target_addr, [hex(d) for d in devices]))
    # 读取芯片 ID 寄存器进行二次验证
    buf = bytearray(1)
    i2c.readfrom_mem_into(target_addr, CHIP_ID_REG, buf)
    if buf[0] != CHIP_ID_VAL:
        raise RuntimeError("Chip ID mismatch: expected 0x%02X, got 0x%02X" % (CHIP_ID_VAL, buf[0]))
    print("BNO055 verified at 0x%02X (chip ID: 0x%02X)" % (target_addr, buf[0]))


def print_raw_sensor_data(imu):
    """
    打印全部原始传感器数据（高频，默认注释调用，可 REPL 手动调用）。

    包括磁力计、加速度计、陀螺仪、线性加速度、重力矢量、四元数。
    """
    # 磁力计原始值（μT）
    mag = imu.mag()
    print("Mag    x %5.0f    y %5.0f    z %5.0f" % mag)
    # 加速度计原始值（m/s²）
    acc = imu.accel()
    print("Accel  x %5.1f    y %5.1f    z %5.1f" % acc)
    # 陀螺仪原始值（°/s）
    gyr = imu.gyro()
    print("Gyro   x %5.0f    y %5.0f    z %5.0f" % gyr)
    # 线性加速度（m/s²）
    lin = imu.lin_acc()
    print("LinAcc x %5.1f    y %5.1f    z %5.1f" % lin)
    # 重力矢量（m/s²）
    grav = imu.gravity()
    print("Grav   x %5.1f    y %5.1f    z %5.1f" % grav)
    # 四元数
    quat = imu.quaternion()
    print("Quat   w %5.3f    x %5.3f    y %5.3f    z %5.3f" % quat)


def print_isr_style_data(imu):
    """
    使用 ISR 安全方法读取并打印数据（高频，默认注释调用，可 REPL 手动调用）。

    通过 iget() 读取欧拉角数据，直接更新 w/x/y/z 属性。
    """
    # 使用 ISR 安全方法读取欧拉角
    imu.iget(EULER_DATA)
    print("ISR-Euler heading %4.0f roll %4.0f pitch %4.0f" % (imu.w, imu.x, imu.y))


def configure_sensor_limits(imu):
    """
    配置传感器边界参数（模式切换，默认注释调用，可 REPL 手动触发）。

    将加速度计量程设为最大 16G、陀螺仪量程设为最大 2000dps、
    磁力计采样率设为最高 30Hz。
    """
    # 加速度计：最大量程 16G，最小带宽 8Hz
    old_acc = imu.config(ACC, (3, 0))
    print("ACC config changed: %s -> (16G, 8Hz)" % str(old_acc))
    # 陀螺仪：最大量程 2000dps，中等带宽 116Hz
    old_gyro = imu.config(GYRO, (0, 2))
    print("GYRO config changed: %s -> (2000dps, 116Hz)" % str(old_gyro))
    # 磁力计：最高采样率 30Hz
    old_mag = imu.config(MAG, (7,))
    print("MAG config changed: %s -> (30Hz)" % str(old_mag))


def switch_operating_mode(imu, mode, mode_name):
    """
    切换传感器工作模式（模式切换，默认注释调用，可 REPL 手动触发）。

    Args:
        imu: BNO055 驱动实例
        mode: 新模式常量（如 NDOF_MODE, IMUPLUS_MODE 等）
        mode_name: 模式名称（用于日志输出）
    """
    old_mode = imu.mode(mode)
    print("Mode: %d -> %d (%s)" % (old_mode, mode, mode_name))


def save_and_restore_calibration(imu):
    """
    保存并恢复校准数据（低频，默认注释调用，可 REPL 手动触发）。

    读取当前校准偏移值并重新写入以验证读写通路。
    """
    # 读取校准偏移数据
    offsets = imu.sensor_offsets()
    print("Calibration offsets (%d bytes): %s" % (len(offsets), bytes(offsets).hex()))
    # 重新写入（验证写入通路）
    imu.set_offsets(offsets)
    print("Calibration offsets written back successfully")


# ======================================== 自定义类 ============================================



# ======================================== 初始化配置 ==========================================

# 等待设备就绪
time.sleep(3)
print("FreakStudio: BNO055 9-axis IMU sensor test")
print("===========================================")

# 初始化 I2C 总线
# 使用 SoftI2C（兼容性最好，timeout >= 1000μs）
# 可根据实际硬件修改 SDA/SCL 引脚号
i2c = machine.SoftI2C(sda=machine.Pin(16), scl=machine.Pin(17), timeout=1000)

# 可选：使用硬件 I2C（部分平台需要）
# i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))

# 扫描 I2C 总线并验证 BNO055 设备
scan_i2c_bus(i2c, BNO055_ADDR)

# 实例化 BNO055 驱动
# crystal=True: 使用外部 32.768kHz 晶振（大多数模块默认）
imu = BNO055(i2c, address=BNO055_ADDR, crystal=True, debug=False)
print("BNO055 initialized successfully")

# 打印初始状态
print("Crystal: %s" % ("External" if imu.external_crystal() else "Internal"))
print("Calibration: %s" % imu.cal_status())
print("Temperature: %d C" % imu.temperature())
print("===========================================")

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 按间隔打印低频传感器数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 温度
            temp = imu.temperature()
            print("Temp: %d C" % temp, end="  |  ")

            # 校准状态
            cal = imu.cal_status()
            calibrated = imu.calibrated()
            print("Cal [S:%d G:%d A:%d M:%d] %s" % (
                cal[0], cal[1], cal[2], cal[3],
                "READY" if calibrated else "calibrating..."
            ))

            # 欧拉角（融合姿态输出）
            heading, roll, pitch = imu.euler()
            print("  Euler: H=%4.0f R=%4.0f P=%4.0f" % (heading, roll, pitch))

            last_print_time = current_time

        # --- 高频传感器数据（默认注释，可 REPL 手动调用） ---
        # print_raw_sensor_data(imu)     # 全部原始传感器数据
        # print_isr_style_data(imu)      # ISR 安全方式读取欧拉角

        # --- 模式切换（默认注释，可 REPL 手动触发） ---
        # switch_operating_mode(imu, IMUPLUS_MODE, "IMUplus")   # 切换到 IMU 模式（无磁力计）
        # switch_operating_mode(imu, NDOF_MODE, "NDOF")         # 切换回 NDOF 九轴融合模式
        # switch_operating_mode(imu, COMPASS_MODE, "Compass")   # 切换到电子罗盘模式
        # imu.reset()                                           # 复位传感器

        # --- 传感器配置（默认注释，可 REPL 手动触发） ---
        # configure_sensor_limits(imu)  # 配置传感器为最大量程
        # 查询当前配置（不修改）
        # print("ACC config:", imu.config(ACC))
        # print("GYRO config:", imu.config(GYRO))
        # print("MAG config:", imu.config(MAG))

        # --- 校准操作（默认注释，可 REPL 手动触发） ---
        # save_and_restore_calibration(imu)  # 保存并恢复校准数据

        # --- 异常参数测试（默认注释，可 REPL 手动测试） ---
        # 非法设备类型 → ValueError
        # imu.config(0xFF, (0, 0))
        # 非法 value 格式 → ValueError
        # imu.config(ACC, "invalid")
        # 非法轴映射参数 → ValueError
        # BNO055(i2c, transpose=(0, 1, 3))  # 索引 3 超出范围
        # BNO055(i2c, sign=(0, 0, 2))       # sign 值只能为 0 或 1

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if imu is not None:
        imu.deinit()
        del imu
    print("Program exited")
```

## API 参考

### BNO055 类构造函数

```python
BNO055(i2c, address=0x28, crystal=True, transpose=(0,1,2), sign=(0,0,0), debug=False)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `i2c` | I2C 实例 | 必填 | 已初始化的 I2C 总线实例 |
| `address` | int | `0x28` | 设备 I2C 地址（DOF 低=0x28, DOF 高=0x29） |
| `crystal` | bool | `True` | 是否使用外部 32.768kHz 晶振 |
| `transpose` | tuple | `(0,1,2)` | 轴重映射顺序（0=X, 1=Y, 2=Z） |
| `sign` | tuple | `(0,0,0)` | 轴方向符号（0=正向, 1=反向） |
| `debug` | bool | `False` | 是否启用调试日志 |

### 传感器数据方法（只读）

| 方法 | 返回值 | 单位 | 说明 |
|------|--------|------|------|
| `mag()` | `(x, y, z)` | μT | 磁力计矢量 |
| `accel()` | `(x, y, z)` | m/s² | 加速度计矢量 |
| `gyro()` | `(x, y, z)` | °/s | 陀螺仪角速度 |
| `lin_acc()` | `(x, y, z)` | m/s² | 线性加速度（去除重力） |
| `gravity()` | `(x, y, z)` | m/s² | 重力矢量 |
| `euler()` | `(heading, roll, pitch)` | °（度） | 欧拉角（航向/横滚/俯仰） |
| `quaternion()` | `(w, x, y, z)` | 无量纲 | 四元数 |
| `temperature()` | int | °C | 芯片温度 |

### 校准方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `cal_status()` | `bytearray([sys, gyro, accel, mag])` | 各传感器校准状态（0~3，3=已校准） |
| `calibrated()` | bool | 所有传感器是否已完全校准 |
| `sensor_offsets()` | bytearray(22) | 读取校准偏移值原始数据 |
| `set_offsets(buf)` | None | 写入校准偏移值（22 字节） |

### 配置方法

| 方法 | 说明 |
|------|------|
| `mode(new_mode=None)` | 查询/切换工作模式，返回原模式值 |
| `config(dev, value=None)` | 查询/配置传感器量程和带宽 |
| `reset()` | 硬件复位传感器，恢复出厂设置 |
| `orient()` | 应用轴重映射配置（`__init__` 自动调用） |
| `external_crystal()` | 查询是否使用外部晶振 |
| `deinit()` | 释放资源，进入低功耗挂起模式 |

### 工作模式常量

| 常量 | 加速度计 | 磁力计 | 陀螺仪 | 绝对方向 | 融合 |
|------|:---:|:---:|:---:|:---:|:---:|
| `CONFIG_MODE` | - | - | - | - | N |
| `ACCONLY_MODE` | ✓ | - | - | - | N |
| `MAGONLY_MODE` | - | ✓ | - | - | N |
| `GYRONLY_MODE` | - | - | ✓ | - | N |
| `ACCMAG_MODE` | ✓ | ✓ | - | - | N |
| `ACCGYRO_MODE` | ✓ | - | ✓ | - | N |
| `MAGGYRO_MODE` | - | ✓ | ✓ | - | N |
| `AMG_MODE` | ✓ | ✓ | ✓ | - | N |
| `IMUPLUS_MODE` | ✓ | - | ✓ | - | ✓ |
| `COMPASS_MODE` | ✓ | ✓ | - | ✓ | ✓ |
| `M4G_MODE` | ✓ | ✓ | - | - | ✓ |
| `NDOF_FMC_OFF_MODE` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `NDOF_MODE`（默认） | ✓ | ✓ | ✓ | ✓ | ✓ |

### 传感器配置参数

**加速度计 `config(ACC, (range, bw))`**：
- Range: 2, 4, 8, 16 (G)
- Bandwidth: 8, 16, 31, 62, 125, 250, 500, 1000 (Hz)

**陀螺仪 `config(GYRO, (range, bw))`**：
- Range: 125, 250, 500, 1000, 2000 (dps)
- Bandwidth: 12, 23, 32, 47, 64, 116, 230, 523 (Hz)

**磁力计 `config(MAG, (rate,))`**：
- Rate: 2, 6, 8, 10, 15, 20, 25, 30 (Hz)

### ISR 安全读取

```python
# 在定时器回调中使用 iget() 读取数据
def timer_cb(t):
    imu.iget(EULER_DATA)
    # 读取后 w/x/y/z 属性被更新为原始整数值
    heading = imu.x * (1/16)   # 欧拉角缩放因子

t = machine.Timer(0)
t.init(period=200, callback=timer_cb)
```

ISR 数据寄存器及缩放因子：

| 常量 | 缩放因子 | 单位 |
|------|:------:|------|
| `ACC_DATA` | 1/100 | m/s² |
| `MAG_DATA` | 1/16 | μT |
| `GYRO_DATA` | 1/16 | °/s |
| `GRAV_DATA` | 1/100 | m/s² |
| `LIN_ACC_DATA` | 1/100 | m/s² |
| `EULER_DATA` | 1/16 | ° |
| `QUAT_DATA` | 1/(1<<14) | 无量纲 |

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 上电延时 | BNO055 启动需要约 400ms（外部晶振约 700ms+500ms），开机自动运行需加 `time.sleep(1.2)` |
| 晶振配置 | 若模块无外部晶振，必须设置 `crystal=False` |
| 工作电压 | 3.3V（Adafruit 板载稳压器支持 3.3V-5V 输入） |
| 融合模式限制 | `euler()`/`quaternion()`/`lin_acc()`/`gravity()` 仅在融合模式（NDOF/IMUplus 等）下有效，非融合模式返回零值 |

### I2C 通信

| 项目 | 说明 |
|------|------|
| 时钟拉伸 | BNO055 使用 I2C 时钟拉伸，`SoftI2C` 必须设置 `timeout >= 1000`（默认仅 255μs） |
| 上拉电阻 | SCL/SDA 必须接上拉到 3.3V，推荐 1KΩ-4.7KΩ |
| 速率 | 推荐 100KHz，400KHz 时上拉不足可能导致数据错误 |
| 双设备 | 通过 DOF 引脚可设置第二地址 0x29，支持同一总线挂两个 BNO055 |

### 平台兼容性

| 平台 | 注意事项 |
|------|----------|
| Pyboard | 硬件 I2C(1)/I2C(2) 已内置上拉，可直接使用 |
| ESP8266 | RAM 受限（~14KB），推荐使用 `bno055_base.py` 轻量版（~9.7KB） |
| ESP32 | 多数板无内置上拉，需外加电阻；硬件 I2C 和 SoftI2C 均可使用 |
| Raspberry Pi Pico | 无内置上拉，推荐 1KΩ 电阻；推荐使用最新的每日构建固件（1.18 存在已知 I2C 问题） |

### 校准要求

- **加速度计**：将设备分别以 6 个不同姿态静置数秒
- **陀螺仪**：将设备保持单个稳定姿态数秒
- **磁力计**：在空气中画 "8" 字形随机运动，直到 `cal_status()` 显示 mag=3
- 校准状态可能回退，但一旦达到良好状态通常可安全使用
- 校准偏移可通过 `sensor_offsets()`/`set_offsets()` 保存/恢复
- 参考视频：[Bosch BNO055 校准演示](https://youtu.be/Bw0WuAyGsnY)

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-24 | Peter Hinch | 规范化版本：标准文件头、中英双语 docstring、类型注解、参数校验、异常包装、ISR 安全标注、debug 日志 |

## 联系方式

- 作者：Peter Hinch
- GitHub：[micropython-bno055](https://github.com/micropython-IMU/micropython-bno055)
- 参考：[Adafruit BNO055 产品页](https://www.adafruit.com/product/2472)

## 许可协议

MIT License

Copyright (c) 2019 Peter Hinch

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
