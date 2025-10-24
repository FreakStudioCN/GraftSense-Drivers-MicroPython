# silicon5351时钟信号发生模块驱动 - MicroPython版本
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

silicon5351是一款I²C接口的时钟信号发生芯片，通过写入寄存器可以精确设置时钟信号频率输出。

---

## 主要功能

* 多通道独立时钟输出：Si5351A 可生成多达 3 路独立的时钟信号（CLK0/CLK1/CLK2），每路输出都可以独立配置为不同的频率，满足不同电路模块对时钟信号的多样化需求。
* 宽频率范围输出：输出频率范围广泛，通常为 8kHz 至 160MHz，能够为各种对时钟频率要求不同的设备提供时钟信号。
* 兼容MicroPython主流开发板，接口简洁易用

---

## 硬件要求

### 推荐测试硬件

* MicroPython开发板（如树莓派Pico）
* silicon5351模块
* 杜邦线若干
* （可选）面包板

### 模块引脚说明

| ilicon5351引脚 | 功能描述    | 连接说明               |
| -------- | ------- | ------------------ |
| VDD      | 电源输入    | 接开发板3.3V           |
| GND      | 接地      | 接开发板GND            |
| SDA      | I²C数据   | 接开发板SDA（如Pico的GP0） |
| SCL      | I²C时钟   | 接开发板SCL（如Pico的GP1） |
---

## 文件说明

### silicon5351.py

该文件实现 **silicon5351时钟信号发送芯片** 的核心驱动功能，仅包含 `SI5351_I2C` 类，用于通过 I²C 总线读取和设置芯片寄存器，实现时钟信号的配置与控制。

类的主要方法包括：

* `__init__(i2c: I2C, crystal`: float, load: int = SI5351_CRYSTAL_LOAD_10PF, address: int = SI5351_I2C_ADDRESS_DEFAULT)：初始化 Si5351 驱动对象，接收 I²C 实例、晶振频率、晶振负载电容（默认 10PF）和设备地址（默认 0x60），完成硬件绑定与初始化（等待芯片自检、禁用输出、配置晶振负载）。
* `_read_bulk(register: int, nbytes: int) -> bytearray`：从指定寄存器连续读取 连续 n 字节数据，返回字节数组。
* `_write_bulk(register: int, values: list[int]) -> None`：向指定寄存器连续写入字节列表数据。
* `_read(register: int) -> int`：读取单个寄存器的 8 位值。
* `_write(register: int, value: int) -> None`：向单个个寄存器写入 8 位值。
* `write_config(reg: int, whole: int, num: int, denom: int, rdiv: int) -> None`：向 PLL 或 Multisynth 寄存器写入分频配置参数（整数部分、分数分子 / 分母、附加分频因子）。
* `set_phase(output: int, div: int) -> None`：设置指定输出通道（0~2）的相位偏移（0~255 分频周期 tick）。
* `reset_pll(pll: int) -> None`：复位指定 PLL（0=PLLA，1=PLLB），使配置生效并同步时钟。
* `init_multisynth(output: int, integer_mode: bool) -> None`：初始化指定输出通道的 Multisynth 控制寄存器，配置分频模式、相位 / 极性和绑定的 PLL。
* `approximate_fraction(n: int, d: int, max_denom: int) -> tuple[int, int]`：将分数 n/d 近似为分母不超过 max_denom 的分数，返回（分子，分母）元组。
* `init_clock(output: int, pll: int, quadrature: bool = False, invert: bool = False, drive_strength`: int = SI5351_CLK_DRIVE_STRENGTH_8MA) -> None：初始化输出通道（0~2）基础参数，包括绑定的 PLL、正交 / 反相输出设置和驱动强度（2/4/6/8MA）。
* `enable_output(output: int) -> None`：使能指定输出通道（0~2）。
* `disable_output(output: int) -> None`：禁用指定输出通道（0~2）。
* `setup_pll(pll: int, mul: int, num: int = 0, denom: int = 1) -> None`：配置 PLL（0=PLLA，1=PLLB）倍频参数，整数倍频（15~90）+ 分数倍频（num/denom），生成 VCO 信号。
* `setup_multisynth(output: int, div: int, num: int = 0, denom`: int = 1, rdiv: int = 0) -> None：配置输出通道的 Multisynth 分频器，整数分频（4~2047）+ 分数分频（num/denom）+ 附加二分频（2^rdiv）。
* `set_freq_fixedpll(output: int, freq: float) -> None`：在固定 PLL 配置下，自动计算分频参数并设置输出通道频率（需先初始化通道和 PLL）。
* `set_freq_fixedms(output: int, freq: float) -> None`：在固定 Multisynth 配置下，自动计算 PLL 倍频参数并设置输出通道频率（需先初始化通道和分频器）。
* `disabled_states(output: int, state: int) -> None`：设置输出通道（0~7）禁用时的状态（0 = 低电平，1 = 高电平，2 = 高阻，3 = 永不禁用）。
* `disable_oeb(mask: int) -> None`：通过 8 位掩码禁用指定通道（0~7）的 OEB 引脚控制功能（1 = 禁用）。
* `i2c（属性）`：返回绑定的 I²C 实例，支持直接操作硬件。
* `crystal（属性）`：返回晶振频率值（Hz），用于校准或日志输出。
* `address（属性）`：返回设备 I2C 地址，用于通信验证。

---

### main.py

该文件为 silicon5351 的功能测试程序

`main` 函数的核心功能是：初始化 I²C 总线并创建 silicon5351 驱动实例，设置通道0输出 2Mhz的时钟信号。

---

## 软件设计核心思想

* **模块化**：拆分数据读取、寄存器写入、通道选择、信号输出与关闭为独立方法，聚合调用易维护
* **硬件解耦**：I²C 实例由应用层传入，驱动不负责硬件初始化，兼容不同开发板

---

## 使用说明

### 硬件接线（树莓派Pico示例）

| DS3502引脚 | Pico引脚      | 接线功能            |
| -------- | ----------- | --------------- |
| VDD      | 3.3V（Pin36） | 电源输入            |
| GND      | GND（Pin38）  | 接地              |
| SDA      | GP0（Pin1）   | I²C数据线          |
| SCL      | GP1（Pin2）   | I²C时钟线          |

---

### 软件依赖

* 固件：MicroPython v1.23+
* 内置库：`machine`（I²C控制）、`time`（延时）
* 开发工具：Thonny / PyCharm

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `silicon5351.py` 和 `main.py`，修改 `main.py` 中 I²C 引脚和设备地址为实际接线配置
3. 运行 `main.py`，通过示波器观察输出波形

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : silicon5351时钟示例 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

#导入micropython自带库
from machine import Pin
#导入时间模块
import time
#导入silicon5351
from silicon5351 import SI5351_I2C

# ======================================== 全局变量 ============================================

crystal = 25e6     # 晶振频率 25 MHz
mul = 15           # PLL 倍频系数 (25MHz * 15 = 375 MHz)
freq = 2.0e6       # 输出频率 2 MHz（最大 200 MHz）
quadrature = True  # 正交输出标志（最低输出频率 = PLL / 128）
invert = False     # 反相输出标志（四相模式下忽略）

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Use silicon5351 to output clock signals.")
i2c = machine.I2C(0, scl=Pin(5), sda=Pin(4), freq = 100000)

# 初始化 SI5351 芯片
si = SI5351_I2C(i2c, crystal=crystal)
# 配置 PLL0 = 375 MHz
si.setup_pll(pll=0, mul=mul)
# 初始化输出通道 0 和 1，使用 PLL0
si.init_clock(output=0, pll=0)
# 设置输出频率为 2 MHz（基于固定 PLL）
si.set_freq_fixedpll(output=0, freq=freq)

# ========================================  主程序  ===========================================
# 打开输出 0 和 1
si.enable_output(output=0)
print(f'done freq={freq} mul={mul} quadrature={quadrature} invert={invert}')
# 保持输出 20 秒
time.sleep(20)
# 关闭输出 0
si.disable_output(output=0)


```
## 注意事项

### 电气特性限制

* **电压限制**：DS3502 VDD 电压必须严格控制在 2.7V\~5.5V 范围内，推荐 3.3V；信号输出（P0/P1）最大不可超过 VDD，否则可能损坏芯片。
* **电流限制**：DS3502 输出电流最大推荐 1mA（典型应用负载），过大负载可能导致电位器损坏或寄存器值异常。

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
📧 **邮箱**：1098875044@qq.com  
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