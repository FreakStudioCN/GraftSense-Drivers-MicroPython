# MQ系列气体传感器驱动 - MicroPython版本

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
MQ系列气体传感器是一类基于电化学原理的气体检测设备，可用于检测多种可燃性气体、有毒有害气体浓度。该系列传感器具有灵敏度高、响应速度快、成本低等特点，广泛应用于家庭安全监测、工业环境检测、智能家居等场景。

> **注意**：不能应用于高精度安全监测等特殊场合，仅作为参考性气体浓度指示。

本项目提供了基于 MicroPython 的驱动代码及示例程序，方便开发者快速接入 MQ 系列气体传感器，实现气体浓度检测功能。

---

## 主要功能
- **多种传感器支持**：
  - MQ2（可燃气体、烟雾）
  - MQ4（甲烷、天然气）
  - MQ7（一氧化碳）
  - 支持自定义传感器多项式校准
- **核心检测指标**：
  - 电压值（V）
  - 气体浓度（ppm）
- **中断支持**：通过比较器输出实现中断触发，支持上升沿/下降沿检测
- **数据处理**：
  - 多采样平均滤波
  - 多项式浓度转换
- **统一接口**：提供 `read_voltage()` 和 `read_ppm()` 标准接口，便于快速集成
- **跨平台支持**：兼容多种硬件平台（树莓派Pico等MicroPython兼容开发板）

---

## 硬件要求
### 推荐测试硬件
- 树莓派 Pico/Pico W
- MQ系列气体传感器（MQ2/MQ4/MQ7等）
- 杜邦线若干
- 10kΩ负载电阻（可选，部分模块已集成）

### 模块引脚说明
| MQ传感器引脚 | 功能描述 |
|--------------|----------|
| VCC          | 电源正极（3.3V-5V，具体参考传感器规格） |
| GND          | 电源负极 |
| AOUT         | 模拟输出（连接ADC） |
| DOUT         | 数字输出（比较器输出，可选） |

---

## 文件说明
### mqx.py
实现了 MQ 系列气体传感器的驱动，核心类 `MQX` 提供统一接口。

#### 类定义
```python
class MQX:
    """
    MQ 系列气体传感器驱动（安全版），支持 ADC 读取、电压转换、ppm 计算和中断回调。

    Attributes:
        adc (ADC): machine.ADC 实例，用于模拟输入。
        comp_pin (Pin): machine.Pin 实例，用于比较器数字输出。
        user_cb (Callable): 用户回调函数，参数为电压 (float)。
        rl (float): 负载电阻值，单位 Ω。
        vref (float): 参考电压，单位 V。
        _custom_poly (list[float]): 用户自定义多项式系数。
        _selected_builtin (str): 当前选择的内置传感器模型。
        last_raw (int): 最近一次 ADC 原始值。
        last_voltage (float): 最近一次电压值 (V)。

    Methods:
        read_voltage() -> float: 读取电压值 (V)。
        read_ppm(samples=1, delay_ms=0, sensor=None) -> float: 读取 ppm 浓度。
        select_builtin(name: str) -> None: 选择内置传感器模型。
        set_custom_polynomial(coeffs: list[float]) -> None: 设置用户自定义多项式。
        deinit() -> None: 释放传感器资源，取消中断。

    Notes:
        - 本类使用 micropython.schedule 保证中断安全。
        - 用户必须根据具体传感器环境自行标定多项式。

    ==========================================

    Safe driver for MQ gas sensors with ADC reading and comparator IRQ.

    Attributes:
        adc (ADC): machine.ADC instance for analog input.
        comp_pin (Pin): machine.Pin instance for digital comparator output.
        user_cb (Callable): user callback function, called with voltage (float).
        rl (float): Load resistor value in ohms.
        vref (float): Reference voltage in volts.
        _custom_poly (list[float]): User-defined polynomial coefficients.
        _selected_builtin (str): Currently selected builtin sensor model.
        last_raw (int): Last ADC raw value.
        last_voltage (float): Last measured voltage.

    Methods:
        read_voltage() -> float: Read voltage in volts.
        read_ppm(samples=1, delay_ms=0, sensor=None) -> float: Read gas concentration in ppm.
        select_builtin(name: str) -> None: Select builtin sensor polynomial.
        set_custom_polynomial(coeffs: list[float]) -> None: Set user-defined polynomial.
        deinit() -> None: Deinitialize sensor and disable IRQ.

    Notes:
        - Uses micropython.schedule to ensure IRQ safety.
        - Polynomial coefficients must be calibrated for actual environment.
    """
```  
### main.py
示例主程序，初始化传感器并循环读取气体浓度数据。

## 软件设计核心思想
### 模块化设计
- 将不同功能封装在独立方法中
- 通过统一接口 `read_voltage()` 和 `read_ppm()` 调用
- 支持灵活扩展新传感器类型（通过多项式系数扩展）

### 浓度计算原理
- 通过 ADC 读取传感器模拟输出电压
- 基于多项式拟合模型将电压转换为气体浓度（ppm）
- 支持多采样平均以提高数据稳定性

### 中断安全设计
- 使用 `micropython.schedule` 确保中断处理安全
- 中断回调仅执行最小操作，避免阻塞系统
- 提供资源释放机制（`deinit()` 方法）

### 跨平台兼容
- 仅依赖 MicroPython 标准库，减少硬件耦合
- 通过抽象层设计屏蔽不同硬件平台的 ADC 差异
- 支持不同参考电压和负载电阻配置

### 灵活的校准机制
- 内置常见传感器多项式模型
- 支持用户自定义多项式校准
- 允许临时切换传感器类型进行测量

## 使用说明
### 硬件接线（树莓派 Pico 示例）

| MQ 传感器引脚 | Pico GPIO 引脚 |
|---------------|----------------|
| VCC           | 3.3V 或 5V（根据传感器规格） |
| GND           | GND            |
| AOUT          | GP26 (ADC0)    |
| DOUT          | GP15           |

> **注意：**
> - 确保 VCC 和 GND 接线正确，避免反向连接
> - AOUT 连接到 ADC 引脚，DOUT 为可选的数字输出引脚
> - 部分传感器需要预热时间（通常几分钟）

### 软件依赖
- **固件版本**：MicroPython v1.19+  
- **内置库**：
  - `machine`（用于 ADC、Pin 控制）
  - `time`（用于延时与时间测量）
  - `micropython`（用于中断调度）
- **开发工具**：PyCharm 或 Thonny（推荐）

### 安装步骤
1. 将 MicroPython 固件烧录到树莓派 Pico  
2. 上传 `mqx.py` 和 `main.py` 到 Pico  
3. 根据硬件连接修改 `main.py` 中的引脚配置  
4. 在开发工具中运行 `main.py`，开始气体检测

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/20 10:21
# @Author  : 缪贵成
# @File    : main.py
# @Description : 测试MQ系列电化学传感器模块驱动程序
# @License : MIT

__version__ = "0.1.0"         # 语义化版本规范：主版本.次版本.修订号
__author__ = "缪贵成"          # 运行时可获取的作者信息
__license__ = "MIT"           # 程序化许可证校验
__platform__ = "MicroPython v1.23"  # 明确兼容性边界

from machine import Pin, ADC
import time
from time import sleep
from mqx import MQX

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 用户回调函数
def mq_callback(voltage: float) -> None:
    """
    当比较器引脚触发中断时调用该函数，打印当前电压值。

    Args:
        voltage (float): 电压值 (单位: V)。

    Returns:
        None: 无返回值。

    Raises:
        None: 本函数不抛出异常。

    ==========================================

    This function is called when the comparator pin triggers an IRQ,
    and prints the measured voltage.

    Args:
        voltage (float): Voltage value in volts.

    Returns:
        None: No return value.

    Raises:
        None: This function does not raise exceptions.
    """
    print("[IRQ] Voltage: {:.3f} V".format(voltage))

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("Measuring Gas Concentration with MQ Series Gas Sensor Modules")

# Pico ADC0 (GPIO26)
adc = ADC(Pin(26))
# Comparator output (GPIO15, optional)
comp = Pin(15, Pin.IN)
mq = MQX(adc, comp, mq_callback, rl_ohm=10000, vref=3.3)

# 选择内置多项式（MQ2、MQ4、MQ7）
mq.select_builtin("MQ2")

# # 传入自定义的多项式
# mq.set_custom_polynomial([1.0, -2.5, 3.3])

# ========================================  主程序  ===========================================
def main():
    print("===== MQ Sensor Test Program Started =====")
    try:
        while True:
            # 读取电压
            v = mq.read_voltage()
            print("Voltage: {:.3f} V".format(v))

            # 读取 ppm（5 次采样，间隔 200 ms）
            ppm = mq.read_ppm(samples=5, delay_ms=200)
            print("Gas concentration: {:.2f} ppm".format(ppm))

            print("-" * 40)
            # 主循环间隔
            sleep(2)
    except KeyboardInterrupt:
        print("User interrupted, exiting program...")
    finally:
        mq.deinit()
        print("Sensor resources released.")

# ======================================== 主程序入口===========================================
if __name__ == "__main__":
    main()
```
## 注意事项

- **RL（负载电阻）**  
  会影响传感器输出电压，避免使用过低阻值以防传感器损坏。

- **中断回调**  
  回调函数中避免耗时操作，可使用 `micropython.schedule` 调度耗时任务，确保 ISR 不阻塞。

- **内置 MQ 多项式**  
  仅供参考，实际环境下需根据传感器和气体浓度进行标定。

- **采样频率**  
  建议 1~2 秒一次，高频采样可能导致 ADC 噪声增加。

- **高浓度有毒气体环境**  
  请使用专业设备进行检测，本驱动仅用于实验、教学或开发。
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/leezisheng](https://github.com/leezisheng)  

---

## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  

**版权归 FreakStudio 所有。**
