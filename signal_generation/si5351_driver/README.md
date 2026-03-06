# GraftSense SI5351 时钟信号发生模块 (MicroPython)

# GraftSense SI5351 时钟信号发生模块 (MicroPython)

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

本项目为 **GraftSense SI5351-based Clock Signal Generator Module V1.0** 提供了完整的 MicroPython 驱动支持，基于 SI5351 芯片实现高精度、可编程多通道时钟信号生成。模块通过 I2C 接口配置 PLL 倍频与 Multisynth 分频，支持 4kHz~200MHz 频率输出，提供 3 路 SMA 接口输出时钟信号，适用于电子 DIY 实验、数字电路时序演示、创客项目等场景，具有频率稳定、可编程、多通道输出、高精度的优势，遵循 Grove 接口标准。

---

## 主要功能

- ✅ **I2C 通信**:支持标准 I2C 接口，默认地址 0x60，兼容 3.3V/5V 电平
- ✅ **PLL 配置**:支持两路 PLL（PLLA/PLLB）倍频，整数倍频范围 15~90，支持分数倍频（分子 0~1048574，分母 1~1048575）
- ✅ **Multisynth 分频**:支持 3 路输出通道的 Multisynth 分频，整数分频因子 4~2047，支持分数分频与附加 2^rdiv 分频（rdiv 0~7）
- ✅ **输出控制**:支持通道使能 / 禁用，可设置输出驱动强度（2/4/6/8 mA）、相位偏移（0~255 ticks）、正交输出与反相输出
- ✅ **禁用状态配置**:可设置输出禁用时的状态（低电平 / 高电平 / 高阻 / 永不禁用）
- ✅ **OEB 引脚控制**:支持屏蔽 OEB 引脚对输出通道的控制，提升灵活性
- ✅ **频率设置模式**:提供固定 PLL 调整分频（`set_freq_fixedpll`）和固定分频调整 PLL（`set_freq_fixedms`）两种频率配置方式
- ✅ **参数校验**:内置严格的类型与范围校验，避免非法配置导致芯片工作异常

---

## 硬件要求

1. **核心硬件**:GraftSense SI5351-based Clock Signal Generator Module V1.0（基于 SI5351 芯片，内置 DC-DC 5V 转 3.3V 电路，3 路 SMA 输出接口）
2. **主控设备**:支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等）
3. **接线配件**:

   - Grove 4Pin 线或杜邦线:连接模块的 SDA、SCL、GND、VCC 引脚
   - 同轴电缆:SMA 转 BNC 或 SMA 转 SMA 线缆，用于输出时钟信号
4. **电源**:3.3V~5V 稳定电源（模块内置电平转换电路，兼容两种供电方式）

---

## 文件说明

---

## 软件设计核心思想

1. **分层架构**:底层封装 I2C 读写操作（`_read`/`_write`/`_read_bulk`/`_write_bulk`），上层提供 PLL/Multisynth 配置、输出控制等高层 API，分离硬件操作与业务逻辑
2. **参数校验与容错**:对所有配置参数进行严格的类型检查（如 int/bool 校验）与范围校验（如 PLL 倍频 15~90、分频因子 4~2047），避免非法参数导致芯片异常
3. **状态缓存机制**:缓存 PLL VCO 频率、Multisynth 分频因子、输出通道配置（PLL 选择、驱动强度、相位等），避免重复读取寄存器，提升效率
4. **分数逼近算法**:内置基于连分数的分数逼近算法（`approximate_fraction`），将目标频率转换为芯片支持的分数分频 / 倍频参数，提升频率精度
5. **中断安全设计**:所有 I2C 操作均在主循环上下文执行，避免在中断服务程序（ISR）中调用驱动方法，确保系统稳定性
6. **可扩展性**:支持晶振频率、负载电容、I2C 地址等参数自定义，适配不同硬件版本

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `silicon5351.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线或杜邦线将模块的 **SDA** 引脚连接至开发板指定 GPIO 引脚（如树莓派 Pico 的 GP4）
- 将模块的 **SCL** 引脚连接至开发板指定 GPIO 引脚（如树莓派 Pico 的 GP5）
- 连接 `GND` 和 `VCC` 引脚，确保 3.3V~5V 供电稳定
- 使用同轴电缆连接模块的 SMA 输出接口（如 CLK0）至测试设备（如示波器）

### 代码配置

```python
from machine import Pin, I2C
from silicon5351 import SI5351_I2C

# 初始化 I2C 总线（树莓派 Pico I2C0，SDA=GP4，SCL=GP5，频率 100kHz）
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 初始化 SI5351 芯片（晶振 25MHz，负载 10pF，I2C 地址 0x60）
si = SI5351_I2C(i2c, crystal=25e6, load=SI5351_I2C.SI5351_CRYSTAL_LOAD_10PF)

# 配置 PLL0（PLLA）倍频:25MHz * 15 = 375MHz
si.setup_pll(pll=0, mul=15)

# 初始化输出通道 0，使用 PLL0，驱动强度 8mA，不启用正交/反相输出
si.init_clock(output=0, pll=0, drive_strength=SI5351_I2C.SI5351_CLK_DRIVE_STRENGTH_8MA)

# 设置输出频率:基于固定 PLL0，分频得到 2MHz 输出
si.set_freq_fixedpll(output=0, freq=2.0e6)
```

### 运行测试

- 重启开发板，`main.py` 将自动执行:

  - 配置 PLL0 为 375MHz
  - 设置通道 0 输出 2MHz 时钟并使能
  - 保持输出 20 秒后自动禁用通道 0
- 使用示波器观察 SMA 输出接口的时钟信号，验证频率与波形是否符合预期

---

## 示例程序

```python
from machine import Pin, I2C
import time
from silicon5351 import SI5351_I2C

# 全局配置
crystal = 25e6    # 晶振频率 25MHz
mul = 15           # PLL 倍频系数（25MHz * 15 = 375MHz）
freq = 2.0e6       # 目标输出频率 2MHz
quadrature = True  # 正交输出标志
invert = False     # 反相输出标志

# 上电延时
time.sleep(3)
print("FreakStudio: Use silicon5351 to output clock signals.")

# 初始化 I2C
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 初始化 SI5351
si = SI5351_I2C(i2c, crystal=crystal)

# 配置 PLL0
si.setup_pll(pll=0, mul=mul)

# 初始化输出通道 0
si.init_clock(output=0, pll=0)

# 设置输出频率
si.set_freq_fixedpll(output=0, freq=freq)

# 使能输出通道 0
si.enable_output(output=0)
print(f'done freq={freq} mul={mul} quadrature={quadrature} invert={invert}')

# 保持输出 20 秒
time.sleep(20)

# 禁用输出通道 0
si.disable_output(output=0)
```

---

## 注意事项

1. **I2C 地址**:模块默认 I2C 地址为 0x60，若存在地址冲突，可通过硬件修改（需参考模块原理图）
2. **晶振配置**:驱动默认晶振频率为 25MHz，若使用其他频率晶振，需在初始化时修改 `crystal` 参数，并确保晶振负载电容（6/8/10pF）与硬件匹配
3. **频率范围**:

   - PLL VCO 频率范围:600MHz~900MHz（由晶振与倍频系数决定，需满足 `crystal * (mul + num/denom) ∈ [600e6, 900e6]`）
   - 输出频率范围:最小 4kHz（由 PLL 频率与最大分频决定），最大 200MHz（由芯片规格决定）
4. **PLL 与 Multisynth 限制**:

   - PLL 倍频系数:整数部分 15~90，分数部分分子 0~1048574，分母 1~1048575
   - Multisynth 分频因子:整数部分 4~2047，分数部分同 PLL，附加 rdiv 分频 0~7（即 2^0~2^7 分频）
5. **SMA 接口要求**:输出时钟信号需使用 50Ω 同轴电缆，避免信号反射与衰减，建议使用 SMA 转 BNC 线缆连接测试设备
6. **禁用状态设置**:通过 `disabled_states` 方法设置输出禁用时的状态，需注意高阻状态可能导致测试设备误判
7. **电源滤波**:模块内置电源滤波电路，若使用高频率输出（>100MHz），建议额外增加电源去耦电容，提升信号质量
8. **中断安全**:驱动所有 I2C 操作均在主循环执行，禁止在 ISR 中调用驱动方法，避免时序错乱

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:

📧 **邮箱**:liqinghsui@freakstudio.cn

💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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