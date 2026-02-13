# DDS信号发生器（AD9833 + MCP41010）

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

本项目基于MicroPython v1.23.0开发，通过AD9833 DDS信号发生器芯片与MCP41010单通道数字电位器芯片配合，实现**幅度、相位、频率可调**的DDS信号生成功能。项目采用模块化设计，驱动与业务逻辑分离，可便捷部署在支持MicroPython的主控板（如Raspberry Pi Pico）上。

## 主要功能

1. 控制AD9833生成多种波形：正弦波、方波、1/2频率方波、三角波；
2. 支持AD9833双频率/相位寄存器配置，可灵活切换不同频率（0~MHz级）、相位（0~360°）参数；
3. 通过MCP41010数字电位器精准调节DDS信号输出幅度（调节范围0~255）；
4. MCP41010支持电源关断模式，可降低闲置状态下的功耗；
5. 完善的参数校验机制，避免无效输入导致硬件异常。

## 硬件要求

1. 主控板：支持MicroPython的MCU板（如Raspberry Pi Pico、ESP32等）；
2. 核心芯片：AD9833 DDS信号发生器芯片、MCP41010单通道数字电位器芯片；
3. 外设配件：SPI总线连接所需的杜邦线、5V/3.3V稳压电源、面包板；
4. 引脚要求：主控板需提供至少1路SPI外设（含SCK、MOSI、CS引脚）。

## 文件说明

| 文件名       | 功能说明                                                                 |
|--------------|--------------------------------------------------------------------------|
| mcp41010.py  | MCP41010数字电位器驱动类，封装SPI通信、电位器值设置、关断模式等核心功能 |
| main.py      | 主程序，初始化AD9833/MCP41010，配置信号频率/相位/波形，演示核心功能     |
| ad9833.py    | AD9833 DDS芯片驱动类（代码中导入，需自行补充对应驱动）                   |

## 软件设计核心思想

1. **模块化封装**：将MCP41010硬件操作封装为独立类，提供`set_value`（设置电位值）、`set_shutdown`（关断模式）等简洁接口，便于复用和维护；
2. **SPI通信标准化**：统一配置SPI总线参数（波特率1MHz、极性0、相位0），保证AD9833与MCP41010通信的稳定性和兼容性；
3. **参数安全校验**：MCP41010的`set_value`方法对输入值做范围校验，超出0~max_value时抛出`ValueError`，避免硬件异常；
4. **分层解耦**：驱动类专注硬件底层通信，主程序专注业务逻辑（信号配置），降低代码耦合度，便于功能扩展。

## 使用说明

### 1. 硬件连接

| 芯片       | 引脚       | 主控板引脚（示例） |
|------------|------------|--------------------|
| AD9833     | SCLK       | GP18               |
| AD9833     | MOSI(SDO)  | GP19               |
| AD9833     | CS         | GP20               |
| MCP41010   | SCLK       | GP18               |
| MCP41010   | MOSI       | GP19               |
| MCP41010   | CS         | GP21               |

> 注：SPI总线支持多设备共享SCK/MOSI，通过独立CS引脚区分设备，需确保所有引脚电平匹配（3.3V）。

### 2. 环境准备

- 主控板烧录MicroPython v1.23.0固件；
- 将`mcp41010.py`、`ad9833.py`、`main.py`上传至主控板文件系统；

### 3. 运行程序

- 主控板上电，程序自动执行（上电延时3秒初始化）；
- 可修改`main.py`中的参数（频率、相位、电位器值、波形模式）自定义输出信号；
- 运行过程中可通过串口查看调试日志（如“FreakStudio: Using AD9833 and DS3502 to implement DDS signal generator”）。

## 示例程序

以下为核心功能示例（摘自`main.py`），演示AD9833与MCP41010的基础使用：

```python
# Python env   : MicroPython v1.23.0
# 导入依赖模块
from machine import Pin
import time
from ad9833 import AD9833
from mcp41010 import MCP41010

# 上电延时初始化
time.sleep(3)
print("初始化DDS信号发生器...")

# 初始化AD9833（SPI0：MOSI-GP19、SCLK-GP18、CS-GP20，主时钟25MHz）
ad9833 = AD9833(sdo=19, clk=18, cs=20, fmclk=25, spi_id=0)
# 初始化MCP41010（SPI0：MOSI-GP19、SCLK-GP18、CS-GP21，最大调节值255）
mcp41010 = MCP41010(clk_pin=18, cs_pin=21, mosi_pin=19, spi_id=0, max_value=255)

# 配置AD9833频率/相位
ad9833.set_frequency(5000, 0)  # 频率寄存器0：5000Hz
ad9833.set_phase(0, 0, rads=False)  # 相位寄存器0：0°
ad9833.set_frequency(1300, 1) # 频率寄存器1：1300Hz
ad9833.set_phase(180, 1, rads=False) # 相位寄存器1：180°

# 选择频率/相位寄存器0，输出正弦波
ad9833.select_freq_phase(0, 0)
ad9833.set_mode('SIN')

# 调节MCP41010电位器值（幅度调节）
mcp41010.set_value(125)

# 可选：切换为方波输出
# ad9833.set_mode('SQUARE')
# 可选：切换为三角波输出
# ad9833.set_mode('TRIANGLE')
# 可选：关断MCP41010降低功耗
# mcp41010.set_shutdown()
```

## 注意事项

1. SPI参数修改：AD9833/MCP41010的SPI波特率默认1MHz，修改前需确认芯片手册，避免超出通信速率范围；
2. 电位器值范围：MCP41010的`set_value`方法仅支持0~max_value（默认255），超出范围会抛出`ValueError`；
3. 硬件保护：接线前需断电，避免引脚接反/短路导致芯片损坏；
4. 时钟配置：AD9833的`fmclk`（主时钟）需与实际硬件匹配（默认25MHz），否则频率计算会偏差；
5. 关断模式：MCP41010进入关断模式后，电位器调节功能失效，需重新调用`set_value`恢复。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：<liqinghsui@freakstudio.cn>  
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
