# 数字电位器芯片DS3502驱动 - MicroPython版本
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
---
## 简介

DS3502是一款I²C接口的可编程数字电位器芯片，通过写入寄存器可以精确设置电阻分压输出。相比传统线性滑动变阻器，DS3502无需物理滑动即可实现电阻调节，适用于亮度调节、音量控制、电机转速调节等场景。本项目提供基于MicroPython的驱动代码，封装I²C通信、寄存器写入、电压计算、归一化比例功能，支持快速集成。

> **注意**：本模块适用于DS3502芯片，不适用于线性滑动变阻器或其他数字电位器芯片，不可用于高精度模拟测量场景。

---

## 主要功能

* 通过I²C读取/写入DS3502的电阻值寄存器（0~~255），计算输出电压（0~~参考电压），输出归一化比例（0.0\~1.0）
* 支持直接设置指定比例值，方便外部控制应用（如亮度、音量）
* 聚合返回完整状态数据，包括寄存器值、电压值、比例
* 兼容MicroPython主流开发板，接口简洁易用

---

## 硬件要求

### 推荐测试硬件

* MicroPython开发板（如树莓派Pico）
* DS3502数字电位器芯片
* 杜邦线3根
* （可选）面包板

### 模块引脚说明

| DS3502引脚 | 功能描述    | 连接说明               |
| -------- | ------- | ------------------ |
| VDD      | 电源输入    | 接开发板3.3V           |
| GND      | 接地      | 接开发板GND            |
| SDA      | I²C数据   | 接开发板SDA（如Pico的GP0） |
| SCL      | I²C时钟   | 接开发板SCL（如Pico的GP1） |
| A0       | I²C地址选择 | 可接GND或VDD决定地址      |
| P0 / P1  | 电阻端口    | 连接负载以形成可调分压输出      |

---

## 文件说明

### ds3502.py

该文件实现 **DS3502 数字电位器** 的核心驱动功能，仅包含 `DS3502` 类，用于通过 I²C 总线读取和设置数字电位器的电阻值/输出电压。

`DS3502` 类通过封装 I²C 通信逻辑，提供电位器的多维度数据访问接口。类中包含两个私有属性：`_i2c` 用于存储外部传入的 I²C 实例，负责与 DS3502 通信；`_vref` 为参考电压（默认3.3V），用于计算输出电压。

类的主要方法包括：

* `__init__(i2c: I2C, addr: int = 0x28, vref: float = 3.3)`：初始化 DS3502 驱动对象，接收 I²C 实例、设备地址和可选参考电压参数，完成硬件接口绑定与参数配置。
* `write_wiper(value: int) -> None`：写入滑动寄存器（WR）设置电位器位置，取值范围 0\~127（7 位分辨率）。
* `read_wiper() -> int`：读取滑动寄存器值（0\~127）。
* `set_ratio(ratio: float) -> None`：通过归一化比例设置滑动寄存器，0.0 对应最小阻值，1.0 对应最大阻值。
* `read_voltage() -> float`：根据当前寄存器值计算输出电压，单位为伏特（V），公式为 `Vout = ratio * vref`。
* `read_ratio() -> float`：将寄存器值转换为归一化比例（0.0\~1.0）。
* `get_state() -> dict`：聚合返回电位器的完整状态数据，以字典形式包含 raw（寄存器值）、voltage（电压值）、ratio（比例值）三个关键参数，方便一次获取多维度信息。
* `i2c`（属性）：返回绑定的 I²C 实例，支持应用层直接操作 I²C 硬件。
* `vref`（属性）：返回当前参考电压值，用于校准验证或日志输出。

---

### main.py

该文件为 DS3502 的功能测试程序，无自定义类，仅包含 `main` 函数作为程序入口。

`main` 函数的核心功能是：初始化 I²C 总线并创建 DS3502 驱动实例，通过循环调用 `get_state()` 方法实时读取电位器状态数据并打印输出。程序支持通过 `interval` 参数（默认0.5秒）调整采样间隔，允许用户通过 Ctrl+C 手动终止测试，适用于验证数字电位器的硬件连接正确性和驱动功能完整性。

---

## 软件设计核心思想

* **模块化**：拆分数据读取、寄存器写入、电压计算、比例计算为独立方法，聚合调用易维护
* **电压映射**：基于数字电位器寄存器值计算电压，确保电压与比例计算准确
* **硬件解耦**：I²C 实例由应用层传入，驱动不负责硬件初始化，兼容不同开发板

---
明白了，我把你的 **使用说明** 修改为针对 **DS3502 数字电位器** 的版本，保持原有结构和格式：

---

## 使用说明

### 硬件接线（树莓派Pico示例）

| DS3502引脚 | Pico引脚      | 接线功能            |
| -------- | ----------- | --------------- |
| VDD      | 3.3V（Pin36） | 电源输入            |
| GND      | GND（Pin38）  | 接地              |
| SDA      | GP0（Pin1）   | I²C数据线          |
| SCL      | GP1（Pin2）   | I²C时钟线          |
| A0       | GND/VDD     | I²C地址选择（根据实际情况） |
| P0 / P1  | 负载端         | 电位器输出连接负载形成分压   |

---

### 软件依赖

* 固件：MicroPython v1.23+
* 内置库：`machine`（I²C控制）、`time`（延时）
* 开发工具：Thonny / PyCharm

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `ds3502.py` 和 `main.py`，修改 `main.py` 中 I²C 引脚和设备地址为实际接线配置
3. 运行 `main.py`，通过打印输出观察数字电位器寄存器值、电压和比例变化

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/3/21 下午3:04   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 使用DS3502数字电位器输出任意波形

# ======================================== 导入相关模块 ========================================

# 导入硬件模块
from machine import ADC, Timer, Pin, I2C, UART
# 导入时间相关模块
import time
# 导入访问和控制 MicroPython 内部结构的模块
import micropython
# 导入ds3502模块用于控制数字电位器芯片
from ds3502 import DS3502
# 导入波形生成模块
from dac_waveformgenerator import WaveformGenerator

# ======================================== 全局变量 ============================================

# DS3502芯片地址
DAC_ADDRESS = 0x00
# 电压转换系数
adc_conversion_factor = 3.3 / (65535)

# ======================================== 功能函数 ============================================

def timer_callback(timer: Timer) -> None:
    """
    定时器回调函数，用于定时读取ADC数据并调用用户自定义的回调函数。

    Args:
        timer (machine.Timer): 定时器实例。

    Returns:
        None: 此函数没有返回值。

    Raises:
        None: 此函数不抛出异常。
    """

    # 声明全局变量
    global adc, adc_conversion_factor

    # 读取ADC数据
    value = adc.read_u16() * adc_conversion_factor
    # 调用用户自定义的回调函数
    micropython.schedule(user_callback, (value))

def user_callback(value: float) -> None:
    """
    用户自定义的回调函数，用于处理ADC采集到的电压值并通过串口发送。

    Args:
        value (float): ADC采集到的电压值。

    Returns:
        None: 此函数没有返回值。

    Raises:
        None: 此函数不抛出异常。
    """
    # 声明全局变量
    global uart

    # 获取浮点数并将其四舍五入到两位小数
    formatted_value = "{:.2f}".format(value)
    # 串口发送采集到的电压数据
    uart.write(str(formatted_value) + '\r\n')

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using Digital Potentiometer chip DS3502 to generate differential waveform")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c = I2C(id=1, sda=Pin(10), scl=Pin(11), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        # 如果设备地址在0x28-0x2B之间，则为DS3502芯片
        if 0x28 <= device <= 0x2B:
            print("I2C hexadecimal address: ", hex(device))
            DAC_ADDRESS = device

# 创建DS3502对象，使用I2C1外设，地址为DAC_ADDRESS
dac = DS3502(i2c, DAC_ADDRESS)
# 设置DS3502为快速模式（仅写入WR寄存器）
dac.set_mode(1)

# 创建串口对象，设置波特率为115200
uart = UART(0, 115200)
# 初始化uart对象，波特率为115200，数据位为8，无校验位，停止位为1
# 设置串口超时时间为100ms
uart.init(baudrate=115200,
          bits=8,
          parity=None,
          stop=1,
          tx=0,
          rx=1,
          timeout=100)

# 创建ADC实例：ADC2-GP28
adc = ADC(2)
# 创建软件定时器对象
timer = Timer(-1)
# 启动定时器，每 1ms 触发一次 timer_callback 函数，ADC采集电压
timer.init(period=10, mode=Timer.PERIODIC, callback=timer_callback)

# ========================================  主程序  ===========================================

# 生成正弦波
print("FreakStudio : Generate Sine Waveform : 10Hz, 1.5V, 1.5V")
# 初始化波形生成器
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform='sine')
# 启动波形生成
wave.start()
# 运行一段时间后停止生成
time.sleep(6)
wave.stop()

# 生成方波
print("FreakStudio : Generate Square Waveform : 10Hz, 1.5V, 1.5V")
# 初始化波形生成器
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform='square')
# 启动波形生成
wave.start()
# 运行一段时间后停止生成
time.sleep(6)
wave.stop()

# 生成三角波
print("FreakStudio : Generate Triangle Waveform : 10Hz, 1.5V, 1.5V, 0.8")
# 初始化波形生成器
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform='triangle', rise_ratio=0.8)
# 启动波形生成
wave.start()
# 运行一段时间后停止生成
time.sleep(6)
wave.stop()

# 停止ADC采集
timer.deinit()
```
---
明白了，我将你的 **注意事项** 修改为针对 **DS3502 数字电位器芯片** 的版本，同时保留原有条理清晰的结构和格式：

---

## 注意事项

### 电气特性限制

* **电压限制**：DS3502 VDD 电压必须严格控制在 2.7V\~5.5V 范围内，推荐 3.3V；信号输出（P0/P1）最大不可超过 VDD，否则可能损坏芯片。
* **电流限制**：DS3502 输出电流最大推荐 1mA（典型应用负载），过大负载可能导致电位器损坏或寄存器值异常。
* **分辨率限制**：DS3502 为 7 位电位器，输出精度有限，超精密调节场景需使用高精度外部 DAC。

---

### 硬件接线与配置注意事项

* **共地要求**：DS3502 GND 必须与开发板 GND 可靠连接，否则输出电压会偏移，导致控制或测量不准确。
* **I²C 接线可靠性**：SDA、SCL 需可靠连接，避免松动或虚接，尤其在长线或面包板测试时，可使用短而粗的杜邦线；长期应用建议焊接。
* **I²C 地址选择**：A0 引脚决定 I²C 地址，确保与代码中 addr 配置一致，否则通信失败。
* **干扰防护**：I²C 信号线应远离电机、继电器等强电磁干扰源，必要时加拉电阻（4.7kΩ\~10kΩ）或屏蔽线。

---

### 环境影响

* **温度限制**：DS3502 工作温度范围为 -40℃\~85℃；高温环境（>85℃）可能加速芯片老化，低温环境（<-40℃）可能影响内部电阻稳定性。
* **湿度限制**：长期高湿环境（>85% RH）可能导致 PCB 和引脚氧化，影响 I²C 通信或输出电压稳定性；建议加防潮保护。
* **粉尘防护**：避免灰尘直接堆积在芯片和接线处，以防接触不良或短路；必要时用干燥气体吹拂清理 PCB 表面，禁止拆解芯片内部。

---

### 使用注意

* **负载匹配**：建议将 DS3502 输出端接高阻负载（>10kΩ）以保证线性输出与稳定性。
* **寄存器访问**：连续高速写入 WR 寄存器可能导致 I²C 总线拥堵或芯片响应延迟，建议控制写入频率。
* **初始化**：上电后应先读取寄存器确认电位器状态，再进行写入操作，避免异常电压输出。

---
### 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

---
### 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  

**版权归 FreakStudio 所有。**