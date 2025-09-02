# PCF8574驱动 - MicroPython版本
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

PCF8574 是一款基于 I²C 总线的 **8 位 GPIO 扩展芯片**，可通过两线接口实现额外的输入/输出端口扩展。
它支持独立控制或读取每个引脚状态，并具备外部中断功能，常用于键盘扫描、LED 控制、开关量采集等场景。

本项目提供基于 **MicroPython** 的驱动类，封装 I²C 通信、端口读写、引脚操作、中断回调等功能，便于快速集成。

> **注意**：设备地址范围为 **0x20 \~ 0x27**，由硬件 A0\~A2 引脚配置。

---

## 主要功能

* 设置或读取 **8 位端口值**
* 独立操作或翻转 **单个 GPIO 引脚**
* 支持 **外部中断触发**，可注册用户回调函数
* 内置端口状态缓存，减少不必要的 I²C 通信
* 提供设备存在性检查，确保总线连接正确

---

## 硬件要求

### 推荐测试硬件

* MicroPython 开发板（如 Raspberry Pi Pico、ESP32）
* PCF8574 I²C GPIO 扩展模块
* 杜邦线若干

### 模块引脚说明

| PCF8574 引脚 | 功能描述     | 连接说明                 |
| ---------- | -------- | -------------------- |
| VCC        | 电源输入     | 接开发板 **3.3V 或 5V**   |
| GND        | 接地       | 接开发板 **GND**         |
| SCL        | I²C 时钟信号 | 接开发板 **I²C SCL**     |
| SDA        | I²C 数据信号 | 接开发板 **I²C SDA**     |
| A0\~A2     | 地址选择引脚   | 高/低电平设置，决定 I²C 地址    |
| INT        | 中断输出引脚   | （可选）接开发板 GPIO，用于中断检测 |

---

## 文件说明

### pcf8574.py

该文件实现 PCF8574 GPIO 扩展芯片的核心驱动功能，仅包含 `PCF8574` 类，用于处理 I²C 总线上的端口读写与中断回调。

`PCF8574` 类通过封装 I²C 通信逻辑，提供端口级和引脚级的访问接口。类中包含四个主要私有属性：

* `_i2c`：存储外部传入的 I²C 实例，负责与 PCF8574 芯片通信。
* `_address`：PCF8574 的 I²C 地址，范围 0x20~~0x27，由 A0~~A2 引脚决定。
* `_port`：端口缓存，记录当前 8 位引脚的状态，减少总线读写次数。
* `_callback` / `_int_pin`：可选的中断回调和中断引脚，用于处理外部触发事件。

类的主要方法包括：

* `__init__(i2c, address=0x20, int_pin=None, callback=None, trigger=Pin.IRQ_FALLING)`：初始化驱动对象，完成地址配置和可选的中断绑定。
* `check() -> bool`：检查设备是否存在于 I²C 总线上。
* `port`（属性）：获取或设置完整的 8 位端口值。
* `pin(pin: int, value: Optional[int] = None) -> int`：读取或设置指定引脚的状态（0/1）。
* `toggle(pin: int) -> None`：翻转指定引脚的当前状态。
* `_read()` / `_write()`：底层通信方法，用于同步端口缓存与实际设备。
* `_scheduled_handler(_)`：中断触发时调用用户注册的回调函数。

---

### ssd1306.py

该文件实现 SSD1306 OLED 显示屏的驱动功能，包含 `SSD1306` 基类（继承自 `framebuf.FrameBuffer`），用于在 OLED 屏幕上绘制和显示内容。

`SSD1306` 类提供 OLED 的初始化、显示控制、对比度调节和数据刷新等功能。核心属性如下：

* `width` / `height`：屏幕分辨率，常见规格为 128x64 或 128x32。
* `external_vcc`：供电方式标志，决定初始化时的电源配置。
* `buffer`：屏幕显存缓冲区，存放待显示的数据。
* `pages`：页数量（height ÷ 8），用于按页刷新数据。

主要方法包括：

* `__init__(width: int, height: int, external_vcc: bool)`：初始化屏幕参数并分配缓冲区。
* `init_display()`：发送初始化命令并清屏。
* `poweroff()` / `poweron()`：控制屏幕电源开关。
* `contrast(contrast: int)`：调整屏幕对比度（0–255）。
* `invert(invert: bool)`：设置反显或正常显示模式。
* `show()`：将缓冲区数据刷新至屏幕。
* `write_cmd()` / `write_data()`：向设备写入命令或数据，需在 I²C/SPI 子类中实现。

---

### main.py

该文件为 PCF8574 与 SSD1306 的联合测试程序，程序入口为主循环 `while True`。

核心流程如下：

1. 初始化硬件 I²C 外设（指定 SDA/SCL 引脚和 400KHz 时钟频率）。
2. 扫描 I²C 总线并识别 OLED 地址（0x3C/0x3D）和 PCF8574 地址（0x20\~0x27）。
3. 创建 SSD1306 显示实例，显示测试图形与文字。
4. 创建 PCF8574 实例，配置中断回调函数 `handle_keys` 并设置端口初始状态。
5. 进入主循环，每隔 0.1 秒等待事件，保持 OLED 显示与 PCF8574 输入输出响应。

---

## 软件设计核心思想

* **模块化**：分别实现 PCF8574 和 SSD1306 驱动类，主程序只负责设备初始化与测试逻辑。
* **硬件解耦**：I²C、ADC、Pin 等硬件对象由应用层传入，驱动类不依赖具体开发板，保证可移植性。
* **缓存优化**：PCF8574 内置端口缓存，避免频繁访问总线，提高效率。
* **回调驱动**：通过中断机制绑定用户函数，实现键盘/按钮等输入事件的响应式处理。
* **层次清晰**：驱动层 → 硬件抽象 → 应用逻辑，便于扩展 OLED 显示与 IO 控制的组合应用。

---

好的 ✅ 我帮你把这段 **滑动变阻器的使用说明**，改写成适用于 **PCF8574 + SSD1306（树莓派 Pico 示例）** 的风格：

---

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| 模块引脚                | Pico 引脚示例   | 功能说明        |
| ------------------- | ----------- | ----------- |
| VCC（PCF8574 & OLED） | 3.3V（Pin36） | 电源输入        |
| GND（PCF8574 & OLED） | GND（Pin38）  | 接地          |
| SDA                 | GP6（Pin9）   | I²C 数据线     |
| SCL                 | GP7（Pin10）  | I²C 时钟线     |
| INT（PCF8574，可选）     | GP29（Pin41） | 中断输入，用于按键检测 |

> 注：PCF8574 的地址范围为 **0x20\~0x27**，SSD1306 常见地址为 **0x3C 或 0x3D**，需根据实际接线确认。

---

### 软件依赖

* **固件**：MicroPython v1.23+
* **内置库**：`machine`（I²C、Pin 控制）、`framebuf`（图形缓冲）、`time`（延时）、`os`（文件操作）
* **开发工具**：Thonny / PyCharm / mpremote

---

### 安装步骤

1. 烧录 **MicroPython 固件** 到树莓派 Pico。
2. 上传 `pcf8574.py`、`ssd1306.py` 和 `main.py` 到开发板。
3. 根据实际接线修改 `main.py` 中的 **I²C 引脚定义**（例如 `I2C(1, sda=Pin(6), scl=Pin(7))`）。
4. 运行 `main.py`：

   * OLED 显示初始化界面（文字 + 边框）
   * PCF8574 初始化成功并设置端口输出
   * 按键或 IO 变化可通过中断触发回调函数响应

---
## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/3 下午9:34   
# @Author  : 李清水            
# @File    : main.py       
# @Description : I2C类实验，主要完成读取串口陀螺仪数据后显示在OLED屏幕上

# ======================================== 导入相关模块 ========================================

# 从SSD1306模块中导入SSD1306_I2C类
from SSD1306 import SSD1306_I2C
# 从pcf8574模块中导入PCF8574类
from pcf8574 import PCF8574
# 硬件相关的模块
from machine import I2C, Pin
# 导入时间相关的模块
import time
# 系统相关的模块
import os

# ======================================== 全局变量 ============================================

# OLED屏幕地址
OLED_ADDRESS = 0
# IO扩展芯片地址
PCF8574_ADDRESS = 0

# IO扩展芯片外接按键映射定义
keys = {'UP': 4, 'DOWN': 1, 'LEFT': 2, 'RIGHT': 0, 'CENTER': 3}
sides = {'SET': 5, 'RST': 6}
# IO扩展芯片外接LED引脚编号
LED_PIN = 7

# ======================================== 功能函数 ============================================

def display_key(name: str) -> None:
    """
    在 OLED 屏幕上显示当前按下的按键名称。

    Args:
        name (str): 按键名称，例如 'UP', 'DOWN', 'SET' 等。

    Returns:
        None

    Notes:
        调用后会清空屏幕并更新显示。
        仅适用于已初始化的 OLED 对象。

    ==========================================

    Display the currently pressed key name on the OLED screen.

    Args:
        name (str): Key name, e.g., 'UP', 'DOWN', 'SET'.

    Returns:
        None

    Notes:
        Clears the OLED screen before updating.
        Only works with an initialized OLED object.
    """
    oled.fill(0)
    oled.text("Key:", 0, 0)
    oled.text(name, 0, 10)
    oled.show()

def handle_keys(port_value: int) -> None:
    """
    处理 PCF8574 读取到的按键端口值，判断按键状态并执行相应操作。
    优先检测普通方向键；若未检测到则检查 SET 和 RST 按键。

    Args:
        port_value (int): 从 PCF8574 读取的端口值，每一位对应一个引脚电平。

    Returns:
        None

    Notes:
        - 按键为高电平时表示按下。
        - SET 键会点亮 LED，RST 键会熄灭 LED。
        - 执行完成后会将所有按键引脚复位为低电平。

    ==========================================

    Handle key events from PCF8574 by checking pressed keys and executing actions.
    Normal keys have higher priority; if none pressed, check SET and RST keys.

    Args:
        port_value (int): Port value read from PCF8574, each bit maps to a pin level.

    Returns:
        None

    Notes:
        - Keys are active high (pressed when logic HIGH).
        - SET key turns on LED, RST key turns off LED.
        - All key pins are reset to LOW after handling.
    """
    # 按键为高电平表示按下
    for name, pin in keys.items():
        if (port_value >> pin) & 1:
            display_key(name)
            return

    # SET和RST处理
    if (port_value >> sides['SET']) & 1:
        # 点亮LED
        pcf8574.pin(LED_PIN, 0)
        display_key("SET")
    elif (port_value >> sides['RST']) & 1:
        # 熄灭LED
        pcf8574.pin(LED_PIN, 1)
        display_key("RST")

    # 将所有按键引脚置为低电平
    pcf8574.pin(0, 0)
    pcf8574.pin(1, 0)
    pcf8574.pin(2, 0)
    pcf8574.pin(3, 0)
    pcf8574.pin(4, 0)
    pcf8574.pin(5, 0)
    pcf8574.pin(6, 0)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试消息
print("FreakStudio: Testing OLED display and PCF8574-controlled LEDs & buttons")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 输出当前目录下所有文件
print('START LIST ALL FILES')
for file in os.listdir():
    print('file name:',file)

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
        print("I2C hexadecimal address: ", hex(device))
        if device == 0x3c or device == 0x3d:
            OLED_ADDRESS = device
        if 0x20 <= device <= 0x27:
            PCF8574_ADDRESS = device

# 创建SSD1306 OLED屏幕的实例，宽度为128像素，高度为64像素，不使用外部电源
oled = SSD1306_I2C(i2c, OLED_ADDRESS, 64, 32,False)
# 打印提示信息
print('OLED init success')

# 首先清除屏幕
oled.fill(0)
oled.show()
# (0,0)原点位置为屏幕左上角，右边为x轴正方向，下边为y轴正方向
# 绘制矩形外框
oled.rect(0, 0, 64, 32, 1)
# 显示文本
oled.text('Freak', 10, 5)
oled.text('Studio', 10, 15)
# 显示图像
oled.show()

# 创建PCF8574 IO扩展芯片的实例
pcf8574 = PCF8574(i2c, PCF8574_ADDRESS, int_pin=29, callback=handle_keys)
# 打印提示信息
print('PCF8574 init success')
# 设置PCF8574芯片的端口状态
pcf8574.port = 0x00

# ========================================  主程序  ============================================

while True:
    time.sleep(0.1)
```
---

## 注意事项

### 电气特性限制

* **电源电压**：PCF8574 工作电压范围为 **2.5V\~5.5V**，常见为 3.3V 或 5V；SSD1306 OLED 常见电压为 3.3V，部分模块支持 5V。使用时需确认模块丝印标注，避免电压不匹配导致芯片烧毁。
* **I²C 总线电平**：Pico 的 I²C 引脚为 3.3V 逻辑，如外设为 5V 模块，需确保具备电平转换或模块内置电平兼容。
* **电流消耗**：PCF8574 每个引脚最大灌电流/拉电流约 20mA，总电流不宜超过 100mA；SSD1306 正常显示时电流约 20\~30mA，峰值可能更高，需保证供电能力充足。
* **负载限制**：PCF8574 引脚不适合直接驱动大电流负载（如电机、继电器），需通过三极管或 MOSFET 进行扩展。

---

### 硬件接线与配置注意事项

* **共地要求**：PCF8574、SSD1306 与 Pico 必须共用 **GND**，否则 I²C 通信将异常或无响应。
* **上拉电阻**：I²C 总线（SCL/SDA）需有上拉电阻（常见 4.7kΩ\~10kΩ），部分模块已集成，若未集成需手动添加。
* **I²C 地址冲突**：PCF8574 地址范围为 **0x20\~0x27**，SSD1306 常见为 **0x3C/0x3D**；若接入多个 PCF8574 模块，需通过 A0\~A2 引脚正确配置，避免地址冲突。
* **中断引脚**：PCF8574 的 INT 引脚为低电平触发，需接至 Pico 的 GPIO 并配置中断回调；注意避免浮空，必要时外部上拉。
* **接线牢固性**：面包板实验时需确保杜邦线完全插入，避免 I²C 通信受虚接影响出现闪屏或按键误触发；长期使用建议焊接。

---

### 环境影响

* **温度限制**：PCF8574 和 SSD1306 的典型工作温度范围为 **-40℃\~85℃**；极端温度可能导致 OLED 显示亮度下降或响应延迟，PCF8574 在高温下也可能出现逻辑电平不稳。
* **湿度限制**：高湿环境（>85%RH）下，OLED 模块排线及 PCF8574 焊点易受潮氧化，可能引起接触不良；建议加装外壳或使用防潮涂层。
* **电磁干扰**：I²C 通信对干扰较敏感，应避免数据线靠近电机、继电器等强干扰源；必要时缩短连线或使用屏蔽线。
* **机械应力**：OLED 屏幕玻璃较脆，不可受力挤压或弯折；PCF8574 模块焊点过度受力也可能脱焊，建议固定在外壳或支架内。

---
### 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/yourusername](https://github.com/yourusername)  

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