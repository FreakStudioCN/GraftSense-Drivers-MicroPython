# GraftSense-基于 JED-MEMS 的气体浓度测量模块（MicroPython）

# GraftSense-基于 JED-MEMS 的气体浓度测量模块（MicroPython）

# 基于 JED-MEMS 的气体浓度测量模块说明

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

本项目是 基于 JED-MEMS 的气体浓度测量模块 的硬件说明文档，适配 FreakStudio GraftSense 传感器模块，支持多种 MEMS 探头（烟雾、一氧化碳、VOC、甲醛等）的数字气体浓度检测，通过 I2C 接口与主流单片机通信，适用于多气体检测场景、环境监测实验、智能家居空气质量检测等应用。

## 主要功能

- 多气体检测：支持烟雾、一氧化碳（CO）、VOC、甲醛等不同 MEMS 探头的数字气体浓度数据采集
- I2C 通信：提供标准 I2C 通信接口，兼容 3.3V/5V 电平，适配 Arduino、STM32 等主流单片机系统
- 探头兼容：探头更换后可稳定匹配检测数据交互，无需额外信号转换
- 电源适配：内置 DC-DC 转换电路，支持 5V 转 3.3V、3.3V 转 1.4V，适配不同探头供电需求

## 硬件要求

- JED-MEMS 气体浓度测量模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 I2C 通信的 MCU（如 Arduino、STM32、树莓派 Pico 等）
- MEMS 气体探头（烟雾、CO、VOC、甲醛等，根据检测需求选择）
- 供电电源：3.3V/5V 直流供电

## 接口与功能

| 接口引脚 | 功能描述                     |
| -------- | ---------------------------- |
| GND      | 接地引脚                     |
| VCC      | 电源输入引脚（3.3V/5V 兼容） |
| SDA      | I2C 串行数据引脚             |
| SCL      | I2C 串行时钟引脚             |
| LED1     | 电源指示灯，上电后常亮       |

## 使用说明

### 1. 硬件连接

- 将模块的 VCC 引脚连接至 MCU 的 3.3V 或 5V 电源
- GND 引脚连接至 MCU 的 GND
- SDA 和 SCL 引脚分别连接至 MCU 的 I2C_SDA 和 I2C_SCL 引脚
- 安装对应的 MEMS 气体探头至模块探头接口

### 2. 初始化与测量

1. 上电后，传感器需预热 30 秒左右，方可进入正常测量状态
2. 测量前，需先在 洁净空气中进行校零，消除环境基线影响
3. 通过 I2C 协议读取模块输出的数字气体浓度数据（具体寄存器定义需参考对应探头手册）

## 注意事项

1. 预热要求：传感器首次上电或长时间未使用后，必须预热 30 秒以上，否则测量数据可能不准确
2. 校零操作：每次测量前需在洁净空气中校零，避免基线漂移导致误差
3. 探头适配：不同 MEMS 探头的 I2C 地址和数据格式可能不同，更换探头后需确认通信协议匹配
4. 供电兼容：模块支持 3.3V/5V 供电，但需确保 MCU 与模块的 I2C 电平一致，避免电平不匹配损坏器件
5. 环境条件：避免在高温、高湿或强电磁干扰环境下使用，以免影响测量精度

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