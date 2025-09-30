# TM1637 四位数码管驱动 - MicroPython版本

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
本项目为基于 TM1637 芯片的四位七段数码管显示模块 MicroPython 驱动，支持亮度调节、数字/字符串/十六进制/温度显示、滚动文本等功能。广泛应用于时钟、温度计、计数器等嵌入式场景。

---

## 主要功能
- **亮度调节**：支持 0-7 级亮度设置
- **数字显示**：整数、双数、十六进制、温度等多种格式
- **字符串显示**：支持 4 字符显示与冒号点亮
- **滚动显示**：支持文本滚动动画
- **原始段码写入**：可自定义显示内容
- **高兼容性**：适配 MicroPython 标准库

---

## 硬件要求

### 推荐测试硬件
- 树莓派 Pico/Pico W 或其他 MicroPython 兼容开发板
- TM1637 四位数码管模块
- 杜邦线若干

### 模块引脚说明
| TM1637 引脚 | 功能描述         |
|-------------|------------------|
| VCC         | 电源正极（3.3V-5V） |
| GND         | 电源负极         |
| CLK         | 时钟引脚         |
| DIO         | 数据引脚         |

---

## 文件说明

### code/tm1637.py
TM1637 显示驱动核心类，提供高层 API（亮度、数字、字符串、滚动等显示）。
#### 类定义
```python
class TM1637:
    """
    TM1637 四位数码管驱动类，支持亮度调节、数字/字符串显示、滚动等功能。

    Attributes:
        clk (Pin): machine.Pin 实例，用于 CLK 引脚。
        dio (Pin): machine.Pin 实例，用于 DIO 引脚。
        brightness (int): 亮度级别，范围 0-7。
        colon (bool): 冒号显示状态。
    """
    ...class TM1637(object):
    """
       基于 TM1637 的四位七段数码管显示驱动类（MicroPython）。
       提供位/段写入、亮度调节、数字/字符串/十六进制/温度显示与滚动显示等高层 API；
       底层严格按 TM1637 时序实现（START/STOP、自动地址递增、显示控制）。

       Attributes:
           clk (Pin): 时钟引脚（输出模式）
           dio (Pin): 数据引脚（输出模式）
           _brightness (int): 当前亮度（0–7）

       Methods:
           __init__(clk, dio, brightness=7): 初始化引脚与默认亮度；写入数据与显示控制命令以启用显示。
           brightness(val): 设置并应用亮度（0–7）；越大越亮；非法值抛 `ValueError`。
           write(segments, pos=0): 从给定起始位写入原始段码（自动地址递增）；pos 超界抛 `ValueError`。
           encode_digit(digit): 将 0–9 编码为七段段码；返回单字节。
           encode_string(string): 将字符串（≤4 字符）批量编码为段码数组。
           encode_char(char): 编码单字符（0–9、a–z/A–Z、空格、破折号、星号）；不支持则抛 `ValueError`。
           hex(val): 以 4 位十六进制显示（小写）。
           number(num): 显示整数（-999..9999），自动裁剪到范围。
           numbers(num1, num2, colon=True): 显示两个 2 位整数（-9..99），可选显示冒号。
           temperature(num): 显示温度（-9..99），越界显示 “lo/hi”，并追加 ℃ 符号。
           show(string, colon=False): 直接显示字符串（≤4），可选点亮冒号位。
           scroll(string, delay=250): 左移滚动显示字符串；`delay` 为步进毫秒。

       Notes:
           - 使用 TM1637 的时序控制，避免在 ISR 或中断上下文中直接操作。
           - 显示亮度范围为 0–7，设置过高可能导致功耗增加。
           - 本类设计用于支持常见的 4 位显示模块，并支持可选冒号。

       ==========================================

       TM1637-based driver for 4-digit 7-segment displays (MicroPython).
       Provides high-level APIs for segment writes, brightness control, numeric/string/hex/temperature
       rendering, and text scrolling, while implementing low-level TM1637 timing
       (START/STOP, auto address increment, display control).

       Attributes:
           clk (Pin): Clock pin (output).
           dio (Pin): Data pin (output).
           _brightness (int): Current brightness level (0–7).

       Methods:
           __init__(clk, dio, brightness=7): Initialize pins/brightness and send init commands.
           brightness(val): Set and apply display brightness in [0..7]; out-of-range values raise `ValueError`.
           write(segments, pos=0): Write raw segment bytes starting at position; validates `pos`.
           encode_digit(digit): Encode a decimal digit (0–9) to a segment byte.
           encode_string(string): Encode a short string (≤4 chars) into segment bytes.
           encode_char(char): Encode a single char; unsupported chars raise `ValueError`.
           hex(val): Display a 16-bit value as 4-digit hex (lowercase).
           number(num): Display an integer within [-999, 9999] (clamped).
           numbers(num1, num2, colon=True): Display two 2-digit integers with optional colon.
           temperature(num): Show temperature value with ℃ indicator and out-of-range handling.
           show(string, colon=False): Show a short string with optional colon.
           scroll(string, delay=250): Scroll text left with step delay (ms).

       Notes:
           - Operates with TM1637 timing control; avoid direct calls from ISR or interrupt contexts.
           - Brightness range is 0–7; excessive settings may increase power consumption.
           - Designed for common 4-digit displays with optional colon support.
   """

    def __init__(self, clk, dio, brightness=7):
```
### code/main.py
示例主程序，演示各类显示效果（亮度调节、数字、字符串、温度、滚动等）。

---

## 软件设计核心思想

### 高层 API 封装
- 统一接口，简化显示操作
- 支持多种显示模式和自定义内容

### 时序精确控制
- 严格遵循 TM1637 通信协议
- 采用低级引脚操作确保兼容性

### 易用性与扩展性
- 亮度、显示内容、动画均可灵活配置
- 便于集成到各类 MicroPython 项目

---

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| TM1637 引脚 | Pico GPIO 引脚 |
|-------------|----------------|
| VCC         | 3.3V 或 5V     |
| GND         | GND            |
| CLK         | GP4            |
| DIO         | GP5            |

> **注意：**
> - CLK/DIO 可根据实际需求修改为其他 GPIO
> - 确保电源电压与模块兼容

---

### 软件依赖

- **固件版本**：MicroPython v1.23.0+
- **内置库**：
  - `machine`（GPIO 控制）
  - `time`（延时）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `code/tm1637.py` 和 `code/main.py` 到开发板
3. 根据硬件连接修改 `main.py` 中的引脚配置
4. 运行 `main.py`，观察数码管显示效果

---

## 示例程序

```python
from machine import Pin
import tm1637
import time

tm = tm1637.TM1637(clk=Pin(4), dio=Pin(5))

while True:
    tm.brightness(4)
    tm.show("dEMo", colon=True)
    tm.numbers(12, 34, colon=True)
    tm.number(256)
    tm.hex(0xBEEF)
    tm.temperature(25)
    tm.scroll("HELLO TM1637  ", delay=180)
    time.sleep(1)
```
## 注意事项
**显示范围限制**
- 单次最多显示 4 字符
- 数字范围：-999 ~ 9999
- 温度范围：-9 ~ 99，超出显示 lo/hi
**电源要求**
- 推荐 5V 供电，确保电源稳定
**环境因素**
- 避免高温高湿环境
**联系方式**
如有问题或建议，请联系开发者： 📧 邮箱：1098875044@qq.com 💻 GitHub：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython

许可协议
本项目除 MicroPython 官方模块外，所有驱动与扩展代码均采用 CC BY-NC 4.0 许可协议发布。
署名 — 请注明原作者及项目链接
非商业性使用 — 禁止商业用途
合理引用 — 可在代码注释、文档等注明来源
版权归 FreakStudio 所有。