# MHT04-IIC MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [通信协议详解](#通信协议详解)
- [设计思路](#设计思路)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本项目为敏源 MHT04-IIC 工业级温湿度传感器提供 MicroPython 驱动。驱动通过 I2C 读取温度、电容和 EEPROM 出厂校准参数，并按照产品手册完成湿度换算与温度补偿，适用于 RP2040 Pico、ESP32、STM32 等支持 MicroPython I2C API 的开发板。

## 主要功能

- 支持 MHT04-IIC 默认 7 位地址 `0x44`
- 支持温度与电容通道 1 联合转换命令 `0x2C10`
- 自动读取并缓存出厂湿度斜率、偏置和电容配置
- 校验寄存器、温度和电容响应的 CRC-8
- 支持有限 I2C 错误重试及可选调试日志
- 提供基础、原始和详细三种读取接口
- 可选将相对湿度限制在 `0~100 %RH`
- 使用外部 I2C 依赖注入，不占用调用者之外的硬件资源

## 硬件要求

推荐测试硬件：

- Raspberry Pi Pico / RP2040 开发板
- 敏源 MHT04-IIC 温湿度传感器
- SDA、SCL 各一个约 4.7 kΩ 上拉电阻
- 杜邦线或可靠焊接连接

RP2040 Pico 示例接线：

| MHT04-IIC 引脚 | 功能 | Pico 连接 | 物理引脚 |
|---|---|---|---:|
| V | 电源 | 3V3(OUT) | 36 |
| G | 地 | GND | 任选，例如 38 |
| D | SDA | GP4 / I2C0 SDA | 6 |
| C | SCL | GP5 / I2C0 SCL | 7 |

SDA 和 SCL 应上拉到 **3.3V**。RP2040 GPIO 不耐 5V，不要将 I2C 总线上拉到 5V。

## 软件环境

- MicroPython：v1.23.0 及以上
- 驱动版本：v1.0.0
- 内置依赖：`machine`、`micropython`、`time`
- 第三方依赖：无，因此不需要 `umodbus`

## 文件结构

```text
mht04iic_driver/
├── code/
│   ├── mht04.py          # 核心驱动
│   └── main.py           # RP2040 Pico 测试程序
├── package.json          # GraftSense/mip 包配置
├── README.md             # 使用说明
└── LICENSE               # MIT 许可证
```

## 文件说明

- `code/mht04.py`：传感器驱动，包含 CRC、校准参数、电容、温湿度换算及错误重试。
- `code/main.py`：使用 RP2040 Pico 的 GP4/GP5，执行总线扫描、响应验证和连续读取。
- `package.json`：发布与安装所需的包元数据，仅发布核心驱动。
- `LICENSE`：MIT 许可文本。

## 快速开始

1. 将 `code/mht04.py` 和 `code/main.py` 上传到开发板根目录。
2. 按接线表连接传感器，并确认 SDA、SCL 上拉到 3.3V。
3. 复位开发板；程序应扫描到 `0x44` 并每秒输出温湿度。

最小示例：

```python
from machine import I2C, Pin
from mht04 import MHT04

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
sensor = MHT04(i2c)
temperature, humidity = sensor.read()
print("Temperature: %.2f C, Humidity: %.2f %%RH" % (temperature, humidity))
```

主要 API：

| API | 返回值 | 说明 |
|---|---|---|
| `refresh_configuration()` | `dict` | 重新读取并缓存出厂校准参数 |
| `read_raw()` | `tuple` | 返回温度和电容原始值 |
| `read()` | `tuple` | 返回 `(温度 ℃, 湿度 %RH)` |
| `read_detailed()` | `dict` | 返回温度、湿度、电容和原始值 |
| `set_conversion_time_ms(ms)` | `None` | 设置不小于 30 ms 的转换等待时间 |
| `set_clamp_humidity(enable)` | `None` | 开启或关闭湿度物理范围限幅 |
| `deinit()` | `None` | 清除驱动缓存，不释放外部 I2C 总线 |

## 通信协议详解

### 协议类型与总线参数

MHT04-IIC 使用敏源 MDC04 的 **I2C 私有命令协议**，不是 Modbus RTU/TCP。

| 项目 | 参数 |
|---|---|
| 接口 | I2C |
| 7 位从机地址 | `0x44` |
| 推荐时钟 | `100 kHz` |
| 命令字节序 | 高字节在前 |
| 数据字节序 | 高字节在前 |
| SDA/SCL | 开漏输出，均需外部上拉 |

这里的 `0x44` 是 I2C 从机地址，不是 Modbus 从机地址。协议中没有 Modbus 功能码、保持寄存器帧或 CRC-16，因此不能直接使用 Modbus Poll。

### 测量命令 `0x2C10`

`0x2C10` 用于启动温度和电容通道 1 的联合转换。主机按以下顺序操作：

```text
START → 0x44 + W → 0x2C → 0x10 → STOP
等待至少 30 ms
START → 0x44 + R → 读取 6 字节 → STOP
```

MicroPython 对应的底层操作：

```python
from time import sleep_ms

i2c.writeto(0x44, b"\x2c\x10")
sleep_ms(30)
data = i2c.readfrom(0x44, 6)
```

返回数据格式：

| 索引 | 字段 | 说明 |
|---:|---|---|
| Byte0 | `Temp_H` | 温度原始值高字节 |
| Byte1 | `Temp_L` | 温度原始值低字节 |
| Byte2 | `Temp_CRC` | Byte0~Byte1 的 CRC-8 |
| Byte3 | `Cap_H` | 电容原始值高字节 |
| Byte4 | `Cap_L` | 电容原始值低字节 |
| Byte5 | `Cap_CRC` | Byte3~Byte4 的 CRC-8 |

温度和电容必须分别校验 CRC，不能对前 5 个字节统一计算一次 CRC。

### 单字节寄存器读取命令 `0xD2xx`

读取内部单字节寄存器时，16 位命令为 `0xD200 | register`。发送命令后使用重复起始条件进入读阶段：

```text
START → 0x44 + W → 0xD2 → register
REPEATED START → 0x44 + R → Value → 0xFF → CRC → STOP
```

MicroPython 对应操作：

```python
register = 0x08
i2c.writeto(0x44, bytes((0xD2, register)), False)
response = i2c.readfrom(0x44, 3)
```

返回值固定为 `[Value, 0xFF, CRC]`，CRC 对前两个字节 `Value` 和 `0xFF` 计算。

驱动使用的寄存器如下：

| 地址 | 名称 | 作用 |
|---:|---|---|
| `0x08` | `HumA_H` | 湿度斜率高字节 |
| `0x09` | `HumA_L` | 湿度斜率低字节 |
| `0x0A` | `HumB_H` | 湿度偏置高字节 |
| `0x0B` | `HumB_L` | 湿度偏置低字节 |
| `0x1D` | `COS` | 电容中心/偏置配置 |
| `0x22` | `CFB` | 电容量程及 COS_RANGE 配置 |

### CRC-8 算法

协议 CRC 参数：

| 参数 | 值 |
|---|---:|
| 多项式 | `0x31`（完整表示为 `0x131`） |
| 初始值 | `0xFF` |
| 输入/输出反转 | 否 |
| 最终异或值 | `0x00` |

参考实现：

```python
def crc8(data):
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc
```

校验示例：`crc8(b"\xBE\xEF") == 0x92`。

### 原始温度换算

温度原始值是高字节在前的有符号 16 位整数：

```text
TempRaw = signed16((Temp_H << 8) | Temp_L)
Temperature(℃) = TempRaw / 256.0 + 40.0
```

若组合后的值大于等于 `0x8000`，应先减去 `0x10000` 转换为有符号数。

### 出厂湿度校准系数

每只传感器的校准参数不同，必须从本机 EEPROM 读取：

```text
HumA_raw = (HumA_H << 8) | HumA_L
HumB_raw = (HumB_H << 8) | HumB_L

HumA = HumA_raw / 100.0
HumB = HumB_raw / 10.0
```

这些参数可在首次测量时读取并缓存，但不能硬编码或复制其他传感器的参数。

### 电容偏置 `Co`

按照产品手册，`COS` 每一位对应一个带正负号的权重：

```text
Co = 51.75
     + 20*q7 + 16*q6 + 8*q5 + 4*q4
     + 2*q3 + 1*q2 + 0.5*q1 + 0.25*q0

qi = +1（COS 对应位为 1）
qi = -1（COS 对应位为 0）
```

该公式等价于把 `COS` 中置 1 的位按以下权重直接求和：

| COS 位 | bit7 | bit6 | bit5 | bit4 | bit3 | bit2 | bit1 | bit0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 权重（pF） | 40 | 32 | 16 | 8 | 4 | 2 | 1 | 0.5 |

### 电容量程 `Cr`

`CFB[5:0]` 用于计算反馈电容；`CFB[7:6]` 为 `COS_RANGE` 配置位，不参与下式的反馈电容求和：

```text
Cfeedback = 2
            + 2*bit0 + 4*bit1 + 8*bit2
            + 16*bit3 + 32*bit4 + 46*bit5

Cr = (0.507 / 3.6) * Cfeedback
```

出厂默认量程约为 `15.492 pF`。

### 原始电容与湿度换算

```text
CapRaw = (Cap_H << 8) | Cap_L

Capacitance(pF) = 2 * (CapRaw / 65535.0 - 0.5) * Cr + Co

RH_base(%RH) = HumA * Capacitance - HumB

RH(%RH) = RH_base - 0.2 * (30.0 - Temperature)
```

最后可根据应用需求把湿度限制到 `0~100 %RH`。驱动默认启用限幅，可通过 `MHT04(i2c, clamp_humidity=False)` 查看未限幅结果。

### 完整读取流程

```text
上电
  ↓
扫描并确认 I2C 地址 0x44
  ↓
读取 0x08~0x0B、0x1D、0x22，并逐项验证 CRC
  ↓
发送 0x2C10
  ↓
等待 ≥30 ms
  ↓
直读 6 字节并分别验证温度、电容 CRC
  ↓
换算温度 → 电容 → 基础湿度 → 温度补偿 → 可选限幅
```

## 设计思路

MHT04-IIC 内部 MDC04 输出的是温度和湿敏电容原始量，不能直接返回相对湿度。驱动首次测量时读取 EEPROM 中每只传感器独有的 `HumA`、`HumB`、`COS` 和 `CFB` 参数，然后按手册公式计算电容与相对湿度，并应用 `-0.2 %RH/℃` 的温度补偿。所有有效载荷均按官方 CRC-8 算法验证。

## 注意事项

| 类别 | 说明 |
|---|---|
| 工作电压 | 传感器支持 2.0~5.5V；连接 RP2040 时推荐整体使用 3.3V |
| I2C 频率 | 示例使用 100 kHz，与 MDC04 规格相符 |
| I2C 地址 | MHT04-IIC 默认 7 位地址为 `0x44` |
| 上拉电阻 | SDA、SCL 必须上拉；不要上拉到超过 MCU GPIO 容限的电压 |
| 转换时间 | `0x2C10` 后必须等待至少 30 ms，驱动拒绝更短配置 |
| 校准参数 | 不同传感器的 EEPROM 参数不同，不能硬编码或跨传感器复制 |
| CRC 错误 | 检查线长、接地、供电和上拉，并保持 I2C 不超过 100 kHz |
| 资源所有权 | `deinit()` 不释放外部传入的 I2C 总线 |

参考资料：

- [敏源 MHT04/MHT04-IIC 产品页](https://www.mysentech.com/productinfo/506263.html)
- 本地产品手册：`MHT04+MHT04H温湿度传感器产品手册-敏源202607.pdf`

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| v1.0.0 | 2026-08-21 | December | 初始规范版本，支持 CRC、校准换算、重试和 RP2040 示例 |

## 联系方式

- GitHub：[FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)
- Issues：[提交问题](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython/issues)
- Email：149050476+Gypsyold@users.noreply.github.com

## 许可协议

本项目采用 MIT License：

```text
MIT License

Copyright (c) 2026 December

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
