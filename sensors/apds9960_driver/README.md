# APDS9960 环境光/颜色/接近传感器 MicroPython 驱动

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

本驱动为 APDS9960 数字环境光/颜色/接近传感器提供 MicroPython 驱动支持。APDS9960 集成 ALS（环境光检测）、RGBC（红/绿/蓝/透明颜色检测）和接近检测三大功能于单芯片中，通过 I2C 接口与主控通信。

驱动采用低内存占用设计（LITE 版），通过将功能拆分为独立子类（`ALS` 和 `PROX`）实现清晰的代码结构，适用于 Raspberry Pi Pico、ESP32 等内存受限的 MicroPython 平台。

## 主要功能

- 完整的环境光（ALS）检测：支持 4 档可编程增益（1x/2x/16x/64x）
- RGBC 颜色分量读取：同时获取红、绿、蓝、环境光四通道数据
- 接近检测：内置 LED 驱动，支持 4 档驱动电流（12.5mA/25mA/50mA/100mA）和 4 档接收增益（1x/2x/4x/8x）
- 硬件中断支持：可为 ALS 和接近检测分别配置阈值中断，含可编程持续触发次数
- 设备状态查询：通过 statusRegister 属性获取芯片各功能模块状态
- 参数校验与异常处理：所有公共接口包含类型/范围校验，I2C 通信失败自动重试（2次）并包装为 RuntimeError
- 低内存占用：通过子类拆分和全局缓冲区复用优化内存使用
- 资源自动释放：提供 `deinit()` 方法安全关闭传感器

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| Raspberry Pi Pico / Pico W | RP2040 主控，3.3V I/O |
| ESP32 开发板 | ESP32 主控，3.3V I/O |
| APDS9960 模块 | I2C 接口传感器模块（3.3V 供电） |
| 面包板 + 杜邦线 | 接线用 |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（3.3V） |
| GND | 电源负极 |
| SCL | I2C 时钟线（接 GP5） |
| SDA | I2C 数据线（接 GP4） |
| INT | 中断输出（可选，本驱动默认未使用） |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖，仅使用标准 `machine` 和 `micropython` 库 |

## 文件结构

```
├── apds9960.py    # 核心驱动文件
├── main.py            # 测试示例文件
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `apds9960.py` | 核心驱动，包含 `I2CEX`（I2C 基类）、`ALS`（环境光/颜色）、`PROX`（接近检测）、`APDS9960LITE`（主驱动）四个类 |
| `main.py` | 测试示例程序，包含 I2C 总线扫描、芯片 ID 验证、传感器数据周期性读取，以及边界参数和异常参数测试函数 |

## 快速开始

### 步骤 1：复制文件

将 `apds9960.py` 和 `main.py` 复制到 MicroPython 设备的根目录。

### 步骤 2：接线

| APDS9960 模块 | Raspberry Pi Pico |
|---------------|-------------------|
| VCC | 3V3（第 36 脚） |
| GND | GND（第 38 脚） |
| SCL | GP5（第 7 脚） |
| SDA | GP4（第 6 脚） |

### 步骤 3：运行

将以下代码保存为 `main.py` 并运行，或在 REPL 中逐行执行：

```python
import machine
import time
from micropython import const
from apds9960 import APDS9960LITE

# APDS9960 I2C 地址和芯片 ID 常量
APDS9960_ADDR = const(0x39)
APDS9960_ID_REG = const(0x92)
# APDS9960 可能的芯片 ID 值
APDS9960_IDS = (0xAB, 0xA8, 0x9C, 0x9E)

# 引脚定义（GPIO 编号，对应 Raspberry Pi Pico / ESP32 等平台）
SDA_PIN = const(4)
SCL_PIN = const(5)

# 传感器数据打印间隔（毫秒）
PRINT_INTERVAL_MS = const(2000)
last_print_time = time.ticks_ms()

# ALS 增益值常量引用（来自 ALS 类）
GAIN_1X = 0
GAIN_2X = 1
GAIN_16X = 2
GAIN_64X = 3

# 接近增益常量引用（来自 PROX 类）
PGAIN_1X = 0
PGAIN_2X = 1
PGAIN_4X = 2
PGAIN_8X = 3

# LED 电流常量引用（来自 PROX 类）
LED_100MA = 0
LED_50MA = 1
LED_25MA = 2
LED_12_5MA = 3

# I2C 总线实例（在初始化配置区实例化）
i2c = None
apds9960 = None


def test_boundary_params():
    """
    边界参数场景：测试增益和中断阈值的极限值
    此函数演示硬件极限参数的设置，可 REPL 手动调用
    """
    print("--- Testing boundary parameters ---")

    # 测试 ALS 增益边界值：最小值 0（1x）和最大值 3（64x）
    print("Testing ALS gain min (0=1x)...")
    apds9960.als.eLightGain = GAIN_1X
    print("  ALS gain set to 1x")
    time.sleep_ms(500)

    print("Testing ALS gain max (3=64x)...")
    apds9960.als.eLightGain = GAIN_64X
    print("  ALS gain set to 64x")
    time.sleep_ms(500)

    # 恢复默认增益
    apds9960.als.eLightGain = GAIN_1X
    print("  ALS gain restored to 1x")

    # 测试接近增益边界值
    print("Testing proximity gain min (0=1x)...")
    apds9960.prox.eProximityGain = PGAIN_1X
    print("  Proximity gain set to 1x")
    time.sleep_ms(500)

    print("Testing proximity gain max (3=8x)...")
    apds9960.prox.eProximityGain = PGAIN_8X
    print("  Proximity gain set to 8x")
    time.sleep_ms(500)

    # 恢复默认增益
    apds9960.prox.eProximityGain = PGAIN_1X
    print("  Proximity gain restored to 1x")

    # 测试 LED 电流边界值
    print("Testing LED current min (3=12.5mA)...")
    apds9960.prox.eLEDCurrent = LED_12_5MA
    print("  LED current set to 12.5mA")
    time.sleep_ms(500)

    print("Testing LED current max (0=100mA)...")
    apds9960.prox.eLEDCurrent = LED_100MA
    print("  LED current set to 100mA")
    time.sleep_ms(500)

    # 恢复默认电流
    apds9960.prox.eLEDCurrent = LED_100MA
    print("  LED current restored to 100mA")

    # 测试中断阈值边界值
    print("Testing ALS interrupt threshold boundary...")
    apds9960.als.setInterruptThreshold(high=0, low=1025, persistance=0)
    print("  ALS threshold set to high=0, low=1025, persistance=0")

    print("Testing proximity interrupt threshold boundary...")
    apds9960.prox.setInterruptThreshold(high=0, low=255, persistance=0)
    print("  Proximity threshold set to high=0, low=255, persistance=0")

    print("--- Boundary parameter test complete ---")


def test_exception_params():
    """
    异常参数场景：测试非法参数是否触发正确的异常
    此函数演示异常处理，可 REPL 手动调用
    """
    print("--- Testing exception parameters ---")

    # 测试 ALS 增益非法值
    print("Testing ALS gain invalid value (99)...")
    try:
        apds9960.als.eLightGain = 99
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 ALS 增益非法类型
    print("Testing ALS gain invalid type (string)...")
    try:
        apds9960.als.eLightGain = "invalid"
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试接近增益非法值
    print("Testing proximity gain invalid value (-1)...")
    try:
        apds9960.prox.eProximityGain = -1
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 LED 电流非法值
    print("Testing LED current invalid value (10)...")
    try:
        apds9960.prox.eLEDCurrent = 10
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 enableSensor 非法类型
    print("Testing enableSensor invalid type...")
    try:
        apds9960.als.enableSensor("yes")
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 powerOn 非法类型
    print("Testing powerOn invalid type...")
    try:
        apds9960.powerOn(1)
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    print("--- Exception parameter test complete ---")


def switch_to_high_gain_mode():
    """
    切换到高增益模式（模式切换，默认注释调用，可 REPL 手动触发）
    适用于暗光环境下的检测
    """
    apds9960.als.eLightGain = GAIN_64X
    apds9960.prox.eProximityGain = PGAIN_8X
    print("Switched to high-gain mode (ALS: 64x, Proximity: 8x)")


def switch_to_low_gain_mode():
    """
    切换到低增益模式（模式切换，默认注释调用，可 REPL 手动触发）
    适用于强光环境下的检测
    """
    apds9960.als.eLightGain = GAIN_1X
    apds9960.prox.eProximityGain = PGAIN_1X
    print("Switched to low-gain mode (ALS: 1x, Proximity: 1x)")


def enable_interrupts():
    """
    启用硬件中断功能（模式切换，默认注释调用，可 REPL 手动触发）
    """
    apds9960.als.setInterruptThreshold(high=500, low=20, persistance=4)
    apds9960.als.enableInterrupt(True)
    apds9960.prox.setInterruptThreshold(high=100, low=20, persistance=4)
    apds9960.prox.enableInterrupt(True)
    print("Hardware interrupts enabled for ALS and Proximity")


# 上电稳定延时
time.sleep(3)
print("FreakStudio: Testing APDS9960LITE driver module")

# 创建硬件 I2C 实例（I2C0: SCL=GP5, SDA=GP4）
print("Initializing I2C0 (SCL=GP%d, SDA=GP%d, 100kHz)..." % (SCL_PIN, SDA_PIN))
i2c = machine.I2C(0, scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN), freq=100000)

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
print("I2C devices found: %s" % [hex(d) for d in devices])

# 检查总线上是否有设备
if len(devices) == 0:
    raise RuntimeError("No I2C device found on bus")

# 检查目标设备是否存在
if APDS9960_ADDR not in devices:
    raise RuntimeError(
        "Device not found at expected address 0x%02X" % APDS9960_ADDR
    )

print("Device found at address 0x%02X" % APDS9960_ADDR)

# 读取芯片 ID 验证设备
print("Reading chip ID from register 0x%02X..." % APDS9960_ID_REG)
try:
    chip_id = i2c.readfrom_mem(APDS9960_ADDR, APDS9960_ID_REG, 1)[0]
    print("Chip ID: 0x%02X" % chip_id)
    if chip_id in APDS9960_IDS:
        print("Device confirmed: APDS9960 (ID 0x%02X matched)" % chip_id)
    else:
        print("Warning: Unexpected ID 0x%02X, expected one of %s"
              % (chip_id, [hex(v) for v in APDS9960_IDS]))
except OSError as e:
    raise RuntimeError("Failed to read chip ID register") from e

# 实例化 APDS9960LITE 驱动
print("Initializing APDS9960LITE driver (debug=False)...")
apds9960 = APDS9960LITE(i2c, debug=False)
print("APDS9960LITE driver initialized successfully")

# 正常参数场景：启用所有传感器
print("Enabling proximity sensor...")
apds9960.prox.enableSensor(True)

print("Enabling ALS sensor...")
apds9960.als.enableSensor(True)

# 正常参数场景：设置默认增益
apds9960.als.eLightGain = GAIN_1X
apds9960.prox.eProximityGain = PGAIN_1X
apds9960.prox.eLEDCurrent = LED_100MA
print("Default gain and current configured")

# 读取初始化后的状态寄存器
print("Initial status register: 0x%02X" % apds9960.statusRegister)

try:
    while True:
        current_time = time.ticks_ms()

        # 低频查询：按间隔打印所有传感器数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            last_print_time = current_time

            # 读取状态寄存器
            status = apds9960.statusRegister

            # 读取接近检测数据
            prox_val = apds9960.prox.proximityLevel

            # 读取环境光数据
            ambient = apds9960.als.ambientLightLevel
            red = apds9960.als.redLightLevel
            green = apds9960.als.greenLightLevel
            blue = apds9960.als.blueLightLevel

            # 输出传感器数据
            print(
                "Status: 0x%02X | Prox: %3d | Ambient: %5d | "
                "R: %4d G: %4d B: %4d"
                % (status, prox_val, ambient, red, green, blue)
            )

        # 以下为高频或模式切换 API，默认注释，可 REPL 手动调用：
        # test_boundary_params()        # 边界参数场景测试，REPL 中调用
        # test_exception_params()       # 异常参数场景测试，REPL 中调用
        # switch_to_high_gain_mode()    # 切换到高增益模式（暗光环境）
        # switch_to_low_gain_mode()     # 切换到低增益模式（强光环境）
        # enable_interrupts()           # 启用硬件中断功能

        # 短延时避免占用 CPU
        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if apds9960 is not None:
        apds9960.deinit()
        del apds9960
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 3.3V，不可直接接 5V（需电平转换） |
| I2C 地址 | 固定为 0x39（7 位地址），不可更改 |
| 上电时序 | 芯片上电后需等待约 50ms 稳定，驱动构造函数已自动执行该时序 |
| ALS 测量范围 | 环境光 0-1025，增益 1x 时满量程；高增益模式下有效范围收缩 |
| 接近检测范围 | 0-255（8 位），检测距离约 10cm 以内，受增益和 LED 电流影响 |
| 采样速率 | 受内部 ADC 积分时间限制，最快约 2.78ms/样本 |
| 中断功能 | 本驱动提供中断配置接口（setInterruptThreshold + enableInterrupt），但未实现 ISR 回调注册；中断引脚（INT）的具体 ISR 处理逻辑需由用户自行完成 |
| 兼容性 | 适用于 Raspberry Pi Pico、ESP32、ESP8266 等支持 MicroPython I2C 的平台；使用 `machine.I2C` 标准接口，兼容 SoftI2C |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | Rune Langøy | 初始版本：实现 ALS/RGBC 颜色检测、接近检测、中断配置；添加完整参数校验、I2C 重试机制和资源释放 |

## 联系方式

- 作者：Rune Langøy
- 项目主页：请补充 GitHub 仓库地址

## 许可协议

MIT License

Copyright (c) 2026 Rune Langøy

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
