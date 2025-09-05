# RCWL9623 收发一体超声波模块驱动 - MicroPython版本

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
基于RCWL9623芯片的超声波测距模块是一款集成收发功能的高性能测距设备，支持多种通信模式（GPIO、1-Wire、UART、I2C）。该模块通过超声波传播时间测算物体距离，具有响应速度快、测距准确、抗干扰能力强等特点，广泛应用于机器人避障、智能家居测距、安全监测等场景。

> **注意**：不能应用于高精度案例，如安全救生等特殊场合。

本项目提供了基于 MicroPython 的驱动代码及示例程序，方便开发者快速接入 RCWL9623 模块，实现距离测量功能。

---

## 主要功能
- **多种工作模式支持**：
  - GPIO触发/Echo回波
  - 单总线（1-Wire）
  - UART串口通信
  - I2C总线通信
- **测距范围**：约20cm到7m，超出范围返回无效
- **统一单位**：采用声波飞行时间计算距离，单位统一为厘米（cm）
- **简洁易用**：提供统一接口`read_distance()`，便于快速集成
- **跨平台支持**：兼容多种硬件平台（树莓派Pico等MicroPython兼容开发板）

---

## 硬件要求
### 推荐测试硬件
- 树莓派 Pico/Pico W
- RCWL9623 超声波模块
- 杜邦线若干

### 模块引脚说明
| RCWL9623 引脚 | 功能描述 |
|--------------|----------|
| VCC          | 电源正极（3.3V-5V） |
| GND          | 电源负极 |
| TRIG         | 触发引脚（GPIO模式） |
| ECHO         | 回波引脚（GPIO模式） |
| IO           | 单总线数据引脚 |
| RX/TX        | UART通信引脚 |
| SCL/SDA      | I2C通信引脚 |

---

## 文件说明
### rcwl9623.py
实现了 RCWL9623 模块的四种工作模式驱动，核心类 `RCWL9623` 提供统一接口。

#### 类定义
```python
class RCWL9623:
    """
    该类提供了对 RCWL9623 超声波测距模块的控制，支持 GPIO/OneWire/UART/I2C 四种工作模式。
    注意，该超声波芯片有效测量距离为25CM到700CM，超出范围将返回 None。

    Attributes:
        mode (int): 当前工作模式，取值为类常量之一：
            GPIO_MODE, ONEWIRE_MODE, UART_MODE, I2C_MODE。
        trig (Pin): GPIO 模式下的触发引脚对象（仅 GPIO 模式有效）。
        echo (Pin): GPIO 模式下的回波引脚对象（仅 GPIO 模式有效）。
        pin (Pin): OneWire 模式下的数据引脚对象（仅 OneWire 模式有效）。
        uart (UART): UART 模式下的串口实例（仅 UART 模式有效）。
        i2c (I2C): I2C 模式下的 I2C 实例（仅 I2C 模式有效）。
        addr (int): I2C 设备地址（仅 I2C 模式有效）。

    Methods:
        __init__(mode, *, gpio_pins=None, onewire_pin=None, uart=None, i2c=None, addr=None):
            初始化超声波模块，根据模式配置相应的接口。

        read_distance() -> float | None:
            读取距离（单位：厘米），如果失败则返回 None。

        _read_gpio() -> float | None:
            GPIO 模式下的测距实现（内部方法）。

        _read_onewire() -> float | None:
            OneWire 模式下的测距实现（内部方法）。

        _read_uart(max_retries=5) -> float | None:
            UART 模式下的测距实现（内部方法）。

        _read_i2c() -> float | None:
            I2C 模式下的测距实现（内部方法）。

    ==========================================
    This class provides control for the RCWL9623 ultrasonic distance sensor,
    supporting four operating modes: GPIO, OneWire, UART, and I2C.
    Note that the effective measurement distance of this ultrasonic chip is 25CM to 700CM,
    and the distance will return None if it exceeds the range.

    Attributes:
        mode (int): Current operating mode, one of the class constants:
            GPIO_MODE, ONEWIRE_MODE, UART_MODE, I2C_MODE.
        trig (Pin): Trigger pin object in GPIO mode (valid only in GPIO mode).
        echo (Pin): Echo pin object in GPIO mode (valid only in GPIO mode).
        pin (Pin): Data pin object in OneWire mode (valid only in OneWire mode).
        uart (UART): UART instance in UART mode (valid only in UART mode).
        i2c (I2C): I2C instance in I2C mode (valid only in I2C mode).
        addr (int): I2C device address (valid only in I2C mode).

    Methods:
        __init__(mode, *, gpio_pins=None, onewire_pin=None, uart=None, i2c=None, addr=None):
            Initialize the ultrasonic module with the specified interface configuration.

        read_distance() -> float | None:
            Read distance in centimeters, returns None on failure.

        _read_gpio() -> float | None:
            Distance measurement implementation for GPIO mode (internal method).

        _read_onewire() -> float | None:
            Distance measurement implementation for OneWire mode (internal method).

        _read_uart(max_retries=5) -> float | None:
            Distance measurement implementation for UART mode (internal method).

        _read_i2c() -> float | None:
            Distance measurement implementation for I2C mode (internal method).
    """
    # 工作模式常量
    GPIO_MODE, ONEWIRE_MODE, UART_MODE, I2C_MODE = [0, 1, 2, 3]
    # 固定I2C通信地址
    I2C_DEFAULT_ADDR = const(0x57)

    # 使用关键字参数传递，驱动只负责使用总线/串口实例，不负责创建/配置它们，硬件初始化（引脚选择、波特率、频率）由应用层统一管理，驱动变得更轻、更可复用，也减少驱动与硬件平台差异绑定的代码；
    # 同时，在实际嵌入式系统中，I2C 总线常被多个设备共享，强制传入实例可以避免驱动重复初始化并在外层统一管理总线资源；
    # 并且，使用 gpio_pins、onewire_pin、uart、i2c 这些命名参数，比通过一堆位置参数或混合参数更直观，减少调用出错概率（尤其是在多模式类里）。
    def __init__(self, mode: int, *, gpio_pins=None, onewire_pin=None, uart=None, i2c=None, addr=None):
```

### main.py
示例主程序，根据设置的工作模式初始化传感器并循环读取距离。

## 软件设计核心思想
## 软件设计核心思想

### 模块化设计
- 将不同通讯模式的读取逻辑封装在独立方法中  
- 通过统一接口 `read_distance()` 调用  
- 支持灵活扩展新功能（例如增加新的传感器类型或通讯模式）

### 飞行时间测距原理
- **GPIO模式**：通过触发 `Trig` 脚脉冲并计时 `Echo` 脚高电平宽度计算距离  
- **计算公式**：距离 = (高电平时间 × 声速) / 2，其中声速取 340 m/s（约 0.034 cm/μs）

### 数据有效性验证
- 通过范围检查滤除异常值（2cm ~ 700cm）
- **UART/I2C 模式**：提供数据读取重试机制
- 错误处理逻辑保证系统在异常情况下的稳定运行

### 跨平台兼容
- 仅依赖 **MicroPython 标准库**，减少硬件耦合
- 提供硬件抽象层（HAL）接口，方便在不同硬件平台移植

### 硬件抽象层设计
- 将底层硬件控制（GPIO、UART、I2C）与测距算法逻辑分离  
- 通过统一接口屏蔽硬件差异
- 便于后续维护与扩展

### 清晰的接口文档
- 提供函数说明、参数说明、返回值说明  
- 包含错误码定义及处理建议

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| RCWL9623 引脚 | Pico GPIO 引脚 |
|---------------|----------------|
| VCC           | 3.3V 或 5V     |
| GND           | GND            |
| TRIG          | GP5            |
| ECHO          | GP4            |

> **注意：**
> - 确保 **VCC** 和 **GND** 接线正确  
> - `TRIG` 为输出引脚，`ECHO` 为输入引脚  
> - 不同模式（GPIO/UART/I2C）使用的引脚可能不同，请参考示例程序进行修改

---

### 软件依赖

- **固件版本**：MicroPython v1.19+  
- **内置库**：
  - `machine`（用于 GPIO、UART、I2C 控制）
  - `time`（用于延时与时间测量）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 将 **MicroPython 固件** 烧录到树莓派 Pico  
2. 上传 `rcwl9623.py` 和 `main.py` 到 Pico  
3. 根据硬件连接修改 `main.py` 中的引脚配置  
4. 在开发工具中运行 `main.py`，开始测距


## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/13 17:45
# @Author  : 缪贵成
# @File    : main.py
# @Description : RCWL9623 超声波模块测试主程序，测试了 GPIO/OneWire/UART/I2C 四种模式

# ======================================== 导入相关模块 =========================================

# 导入硬件模块
from machine import Pin, UART, I2C
# 导入时间相关模块
import time
# 导入超声波相关模块
from rcwl9623 import RCWL9623

# ======================================== 全局变量 ============================================

# I2C 时钟频率 (Hz)，默认 100kHz
I2C_DEFAULT_FREQ = 100_000
# I2C 固定通信地址
I2C_DEFAULT_ADDR = 0x57

# 测试模式:可选 RCWL9623.GPIO_MODE, RCWL9623.ONEWIRE_MODE, RCWL9623.UART_MODE, RCWL9623.I2C_MODE
test_mode = RCWL9623.ONEWIRE_MODE
# 测试间隔时间，单位秒
test_interval = 1

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Test RCWL9623 Module")

# 根据不同模式选择引脚/创建通信接口，并实例化 RCWL9623 对象
if test_mode == RCWL9623.GPIO_MODE:
    # GPIO的引脚元组(trig_pin, echo_pin)
    gpio_pins = (5, 4)
    sensor = RCWL9623(mode=RCWL9623.GPIO_MODE, gpio_pins=gpio_pins)
    print("FreakStudio: GPIO Mode")
elif test_mode == RCWL9623.ONEWIRE_MODE:
    onewire_pin = 5
    sensor = RCWL9623(mode=RCWL9623.ONEWIRE_MODE, onewire_pin=onewire_pin)
    print("FreakStudio: OneWire Mode")
elif test_mode == RCWL9623.UART_MODE:
    uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
    sensor = RCWL9623(mode=RCWL9623.UART_MODE, uart=uart)
    print("FreakStudio: UART Mode")
elif test_mode == RCWL9623.I2C_MODE:
    i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=I2C_DEFAULT_FREQ)
    sensor = RCWL9623(mode=RCWL9623.I2C_MODE, i2c=i2c)
    print("FreakStudio: I2C Mode")
else:
    raise ValueError("unknown mode: %s" % test_mode)

# ======================================== 主程序 ===============================================

# 循环测距
print("FreakStudio: Start Test")
try:
    while True:
        # 测距
        distance = sensor.read_distance()
        # 判断测距结果是否有效
        # 注意，该超声波芯片有效测量距离为25CM到700CM，超出范围将返回 None。
        if distance is not None:
            # 打印测距结果
            print("Get Distance: %.2f cm" % distance)
        # 延时
        time.sleep(test_interval)
except KeyboardInterrupt:
    print("FreakStudio: Exit Test")
except Exception as e:
    print("FreakStudio: Error: %s" % e)

```

## 注意事项

## 注意事项

### 测距范围限制
- 有效范围约 **20cm ~ 7m**  
- 低于 20cm 或超过 7m 的数据视为无效  
- 实际盲区约为 **25cm**（模块物理特性决定）

---

### 模式配置要求

| 模式     | 注意事项 |
|----------|----------|
| GPIO     | `Trig` 为输出，`Echo` 为输入，避免信号干扰 |
| OneWire  | 确保单总线时序准确 |
| UART     | 确认模块波特率设置（默认 9600） |
| I2C      | 确认设备地址（默认 `0x57`） |

---

### 电源要求
- 供电电压：**5V**
- 确保电源稳定，避免电压波动
- 大功率应用时建议单独供电

---

### 采样频率
- 建议保持在 **1 秒** 左右  
- 避免采样过快导致数据不稳定  
- 高频率测量时应考虑模块散热

---

### 环境因素
- 避免在 **高温、高湿** 环境下使用  
- **强风环境** 可能影响测距精度  
- 光滑表面可能导致 **信号反射异常**

## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

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


