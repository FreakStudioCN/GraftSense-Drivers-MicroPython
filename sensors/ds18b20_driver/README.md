# GraftSense-基于 DS18B20 的温度传感器模块（MicroPython）

# GraftSense-基于 DS18B20 的温度传感器模块（MicroPython）

# GraftSense 基于 DS18B20 的温度传感器模块

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

## 简介

本模块是 FreakStudio GraftSense 基于 DS18B20 的温度传感器模块，通过 DS18B20 芯片实现高精度环境温度测量，采用 Maxim（原 Dallas）定义的单总线通信协议，具备高精度、单总线通信、抗干扰能力强等核心优势，兼容 Grove 接口标准。适用于电子 DIY 温度监测实验、智能家居温控演示、多点测温等场景，为系统提供可靠的温度感知能力。

## 主要功能

1. 高精度温度测量：支持-55~125℃ 工作温度范围，9~12 位可配置分辨率（12 位精度达 0.0625℃）；
2. 单总线通信：仅需 1 根数据线实现双向数据传输，简化硬件接线；
3. 多设备共线：每个传感器拥有唯一 64 位 ROM 地址，支持单总线上挂载多个传感器实现多点测温；
4. 多温度单位转换：支持摄氏度、华氏度、开氏度之间的转换；
5. 电源模式灵活：支持独立供电（3.3V/5V）和寄生供电两种模式；
6. 数据校验：内置 CRC8 校验机制，保障数据传输的完整性。

## 硬件要求

### 核心接口

- 单总线通信接口（DIO）：

  - 仅需 1 根数据线（DIO）实现双向数据传输，DIO 为开漏输出结构，需外接 4.7kΩ 左右的上拉电阻到电源（如 VCC），使总线空闲时保持高电平
  - 每个设备拥有唯一 64 位 ROM 地址，可区分总线上的多个传感器，支持多设备共线挂载
- 电源与引脚：

  - VCC：模块供电（支持 3.3V/5V）
  - GND：接地
  - NC：未连接引脚
  - DIO：单总线数据引脚（与 MCU 的 GPIO 引脚直接连接）
- 电源指示灯：LED1 常亮表示模块供电正常

### 电路设计

- DS18B20 核心电路：DS18B20 芯片负责高精度温度采集，通过单总线输出 9 字节暂存器数据（包含温度值、配置寄存器、校验和）
- 传感器接口电路：提供 DIO、VCC、GND 引脚，兼容 Grove 接口标准，便于与主控板快速连接
- 输入供电滤波和指示灯：C1/C2 滤波电容抑制电源噪声，提升测量稳定性；R2 限流电阻保护电源指示灯

### 模块布局

- 正面：DS18B20 芯片、DIO 单总线接口、电源接口（GND/VCC）、电源指示灯（LED1），接口清晰标注，便于接线调试与多点测温部署

## 文件说明

| 文件名       | 功能说明                                                                                               |
| ------------ | ------------------------------------------------------------------------------------------------------ |
| `onewire.py` | 封装单总线通信的基础操作，包含复位、读写位/字节、ROM 地址扫描、CRC 校验等核心方法                      |
| `ds18x20.py` | 基于 OneWire 类封装 DS18B20/DS18S20 温度传感器操作，实现温度转换、读取、分辨率配置、温度单位转换等功能 |
| `main.py`    | 多点温度采集示例程序，演示单总线上多个 DS18B20 传感器的扫描和温度循环读取                              |

## 软件设计核心思想

### 核心类：OneWire（单总线通信）

基于 MicroPython 实现，封装单总线通信的基础操作，核心功能如下：

#### 1. 核心常量

| 常量                   | 说明                     |
| ---------------------- | ------------------------ |
| `CMD_SEARCHROM = 0xf0` | 搜索 ROM 命令            |
| `CMD_READROM = 0x33`   | 读取 ROM ID 命令         |
| `CMD_MATCHROM = 0x55`  | 匹配 ROM ID 命令         |
| `CMD_SKIPROM = 0xcc`   | 同时寻址所有器件命令     |
| `PULLUP_ON = 1`        | 寄生供电模式下的上拉控制 |

#### 2. 核心方法

| 方法                                                                                                               | 功能                                    | 参数说明                                               | 返回值                                      |
| ------------------------------------------------------------------------------------------------------------------ | --------------------------------------- | ------------------------------------------------------ | ------------------------------------------- |
| `__init__(pin: Pin)`                                                                                               | 初始化单总线通信引脚                    | pin: GPIO 引脚对象（配置为开漏上拉）                   | 无                                          |
| `reset(required: bool = False)`                                                                                    | 复位单总线，检测设备响应                | required: 是否强制断言未响应情况                       | bool，有设备响应返回 True                   |
| `readbit() / readbyte() / readbytes(count: int)`                                                                   | 读取单总线上的位/字节/多字节            | 无 / 无 / count: 读取字节数                            | int / int / bytearray                       |
| `writebit(value: int, powerpin: Pin = None) / writebyte(value: int, powerpin: Pin = None) / write(buf: bytearray)` | 向单总线写入位/字节/多字节              | value: 写入值；powerpin: 寄生供电引脚；buf: 写入缓冲区 | 无                                          |
| `select_rom(rom: bytearray)`                                                                                       | 发送匹配 ROM 命令，选择目标设备         | rom: 8 字节 ROM 地址                                   | 无                                          |
| `crc8(data: bytearray)`                                                                                            | 执行 CRC 校验，验证数据完整性           | data: 待校验数据                                       | int，0 表示校验通过                         |
| `scan()`                                                                                                           | 扫描总线上的所有设备，返回 ROM 地址列表 | 无                                                     | list[bytearray]，每个元素为 8 字节 ROM 地址 |

### 核心类：DS18X20（温度传感器）

基于 OneWire 类实现，封装 DS18B20/DS18S20 等温度传感器的操作，核心功能如下：

#### 1. 核心常量

| 常量                             | 说明                     |
| -------------------------------- | ------------------------ |
| `CMD_CONVERT = 0x44`             | 转换温度命令             |
| `CMD_RDSCRATCH = 0xbe`           | 读暂存器命令             |
| `CMD_WRSCRATCH = 0x4e`           | 写暂存器命令             |
| `CMD_RDPOWER = 0xb4`             | 读电源命令               |
| `CMD_COPYSCRATCH = 0x48`         | 拷贝暂存器命令           |
| `PULLUP_ON = 1 / PULLUP_OFF = 0` | 寄生供电模式下的上拉控制 |

#### 2. 核心方法

| 方法                                                  | 功能                                         | 参数说明                                                      | 返回值                                          |
| ----------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------- |
| `__init__(onewire: OneWire)`                          | 初始化 DS18X20 传感器                        | onewire: OneWire 实例                                         | 无                                              |
| `powermode(powerpin: Pin = None)`                     | 设置并返回电源模式                           | powerpin: 寄生供电引脚                                        | int，1=独立供电，0=寄生供电                     |
| `scan()`                                              | 扫描总线上的 DS18X20 设备，返回 ROM 地址列表 | 无                                                            | list[bytearray]，仅包含 DS18X20 设备的 ROM 地址 |
| `convert_temp(rom: bytearray = None)`                 | 启动温度转换                                 | rom: 目标设备 ROM 地址，None 表示广播给所有设备               | 无                                              |
| `read_scratch(rom: bytearray)`                        | 读取暂存器数据（9 字节）                     | rom: 目标设备 ROM 地址                                        | bytearray，暂存器数据                           |
| `write_scratch(rom: bytearray, buf: bytearray)`       | 写入暂存器数据                               | rom: 目标设备 ROM 地址；buf: 写入数据（9 字节）               | 无                                              |
| `read_temp(rom: bytearray)`                           | 读取温度值（℃）                             | rom: 目标设备 ROM 地址                                        | float，温度值，读取失败返回 None                |
| `resolution(rom: bytearray, bits: int = None)`        | 设置或获取分辨率（9~12 位）                  | rom: 目标设备 ROM 地址；bits: 分辨率位数，None 表示读取当前值 | int，分辨率位数                                 |
| `fahrenheit(celsius: float) / kelvin(celsius: float)` | 摄氏度转华氏度/开氏度                        | celsius: 摄氏度值                                             | float，转换后温度值                             |

## 使用说明

### 1. 环境准备

- 硬件：支持 MicroPython 的 MCU（如 ESP32/ESP8266）、GraftSense DS18B20 模块、4.7kΩ 上拉电阻、杜邦线；
- 软件：MicroPython 固件、串口工具（如 Thonny/VSCode+PyMakr）。

### 2. 硬件接线

| DS18B20 模块 | MCU               | 其他                       |
| ------------ | ----------------- | -------------------------- |
| VCC          | 3.3V/5V           | -                          |
| GND          | GND               | -                          |
| DIO          | GPIO6（可自定义） | 串联 4.7kΩ 上拉电阻到 VCC |

### 3. 代码部署

- 将 `onewire.py`、`ds18x20.py` 上传到 MCU 文件系统；
- 将示例程序（main.py）上传到 MCU，或直接在串口工具中逐行执行。

### 4. 运行程序

- 重启 MCU 或直接运行 main.py；
- 通过串口工具查看输出的传感器 ROM 地址和实时温度值。

## 示例程序

以下是 main.py 中的核心示例代码，实现单总线上多点 DS18B20 温度采集：

```python
from machine import Pin
import time
from onewire import OneWire
from ds18x20 import DS18X20

# 初始化配置
time.sleep(3)  # 上电延时，等待模块稳定
print('FreakStudio : Using OneWire to read DS18B20 temperature')

# 定义单总线通信引脚（GPIO6）
ow_pin = OneWire(Pin(6))
# 定义温度传感器实例
ds18x20 = DS18X20(ow_pin)

# 扫描总线上的DS18B20，获取设备地址列表
roms_list = ds18x20.scan()
# 打印设备地址列表
for rom in roms_list:
    print('ds18b20 sensor devices rom id:', rom)

# 让所有挂载在总线上的DS18B20启动温度转换
ds18x20.convert_temp()

# 主循环：循环读取温度
while True:
    time.sleep_ms(500)  # 等待温度转换完成
    for rom in roms_list:
        # 读取并打印温度
        temp = ds18x20.read_temp(rom)
        print('ds18b20 sensor {} devices temp {}'.format(rom, temp))
    # 再次启动温度转换，为下一次读取做准备
    ds18x20.convert_temp()
```

### 示例说明

1. 单总线初始化：使用 GPIO6 作为单总线通信引脚，创建 OneWire 实例；
2. 设备扫描：通过 scan()方法获取总线上所有 DS18B20 设备的 ROM 地址；
3. 温度转换：调用 convert_temp()启动所有设备的温度转换；
4. 多点读取：循环遍历 ROM 地址列表，通过 read_temp()读取每个设备的温度值并打印。

## 注意事项

1. 单总线接线规范：

- DIO 引脚需直接连接 MCU 的 GPIO 引脚，确保 4.7kΩ 上拉电阻正常焊接，使总线空闲时保持高电平；
- 多设备共线时，每个设备的 ROM 地址唯一，通过 scan()方法区分不同设备。

1. 电源模式选择：

- 独立供电：模块直接连接 VCC 和 GND，稳定性高，推荐使用；
- 寄生供电：通过单总线供电，需通过 powermode()方法设置 powerpin，适用于布线受限场景。

1. 分辨率设置：DS18B20 支持 9~12 位分辨率，分辨率越高，温度精度越高（12 位分辨率精度为 0.0625℃），但转换时间越长（12 位转换时间约 750ms）。
2. CRC 校验：读取暂存器数据时会自动进行 CRC 校验，若校验失败会抛出 AssertionError，需检查通信干扰或模块故障。
3. 温度转换间隔：两次温度转换间隔需足够长，确保转换完成（12 位分辨率建议间隔 ≥750ms），否则读取的温度值可能为上一次转换的结果。
4. 环境适应性：DS18B20 的工作温度范围为-55~125℃，适用于严苛的工业与户外场景。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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