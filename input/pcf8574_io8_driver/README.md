# PCF8574 I2C转并行I/O扩展模块驱动 - MicroPython版本

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
PCF8574是一款单芯片8位I/O扩展器，通过I2C总线与主控制器通信，可将I2C信号转换为8路并行I/O信号，有效解决微控制器GPIO端口不足的问题。该芯片支持1.8V-5.5V宽电压供电，无内置上拉电阻，需要自行配置，每路I/O可独立配置为输入或输出，适用于按键矩阵、LED驱动、继电器控制等场景。

本项目提供基于MicroPython的PCF8574模块驱动代码及测试程序，实现I/O端口的灵活配置、数据读写及中断响应等功能，可直接与支持MicroPython的开发板（如树莓派Pico）配合使用。

---

## 主要功能
- 基础I/O控制：支持8路I/O端口的输入/输出模式切换（软件定义方向）
- 数据读写操作：批量读取输入状态或设置输出电平（8位数据一次性处理）
- 引脚独立控制：支持单独设置某一路I/O的电平状态或读取单个引脚值
- 地址灵活配置：通过硬件引脚（A0-A2）支持最多8个设备级联（地址0x20-0x27）
- 扩展类支持：提供`PCF8574_IO8`扩展类，简化8路设备的标准化控制

---

## 硬件要求
### 推荐测试硬件
- 支持MicroPython的开发板（如树莓派Pico/Pico W）
- PCF8574或PCF8574A I/O扩展模块（注意地址差异）
- 杜邦线（公对母，至少6根）
- （可选）面包板（便于临时接线测试）
- （可选）LED、按键、10KΩ电阻（用于功能验证）

### 模块引脚说明
| PCF8574模块引脚 | 功能描述 | 开发板连接建议 |
|-----------------|----------|----------------|
| VCC             | 电源正极 | 3.3V或5V（根据模块版本选择） |
| GND             | 电源负极 | GND（需与开发板共地） |
| SDA             | I2C数据引脚 | 开发板I2C SDA引脚（如树莓派Pico的GP4） |
| SCL             | I2C时钟引脚 | 开发板I2C SCL引脚（如树莓派Pico的GP5） |
| INT             | 中断输出引脚 | 开发板GPIO（如GP6，低电平触发） |
| A0-A2           | 地址选择引脚 | 接GND或VCC（配置I2C地址，默认全接GND为0x20） |
| P0-P7           | 8路并行I/O引脚 | 外部设备（LED、按键等） |

---

## 文件说明
### 1. pcf8574.py
核心驱动文件，实现`PCF8574`基础类，封装芯片底层操作：

- **核心类 `PCF8574`**：
  - `__init__(self, i2c, address=0x20)`：初始化设备；`i2c`为I2C对象，`address`为设备地址（默认0x20）
  - `write(self, data)`：写入8位数据到输出寄存器（控制P0-P7电平）
  - `read(self)`：读取8位输入状态（返回P0-P7的当前电平）
  - `pin_mode(self, pin, mode)`：设置单个引脚模式（输入/输出）
  - `digital_write(self, pin, value)`：设置单个引脚输出电平（0/1）
  - `digital_read(self, pin)`：读取单个引脚输入状态（返回0/1）
  - `toggle(self, pin)`：翻转单个引脚的输出电平

### 2. pcf8574_io8.py
扩展功能文件，定义`PCF8574_IO8`类，提供标准化8路设备控制：

- **扩展类 `PCF8574_IO8`（继承自`PCF8574`）**：
  - `configure_port(port: int, state: tuple[int, int]) -> None`: 配置某个端口的默认状态并立即写入。
  - `set_port(port: int, value: int) -> None`: 设置某个端口（2 位）的输出值。
  - `get_port(port: int) -> int`: 读取端口当前电平值（返回 0..3）。
  - `set_pin(pin: int, value: int) -> None`: 设置单个引脚电平（0=拉低，1=高阻）。
  - `get_pin(pin: int) -> int`: 读取单个引脚电平（0/1）。
  - `read_all() -> int`: 读取完整的 8 位输入状态。
  - `write_all(byte: int) -> None`: 写入完整的 8 位输出值。
  - `refresh() -> None`: 把缓存值写回设备。
  - `ports_state() -> dict`: 返回所有端口的默认状态字典。
  - `deinit() -> None`: 释放对象引用。

### 3. main.py
测试程序文件，包含功能验证逻辑：

- 初始化I2C总线和PCF8574设备实例
- 演示基本I/O操作：输出电平控制、输入状态读取
- 展示扩展类功能：批量配置、中断测试
- 提供LED闪烁、按键检测等示例场景
- 支持键盘中断（Ctrl+C）安全退出

---

## 软件设计核心思想
1. **寄存器虚拟化**：通过软件模拟I/O方向寄存器（硬件无专用方向寄存器），实现输入/输出灵活切换
2. **位操作优化**：采用位运算实现单个引脚控制，避免整体数据覆盖（如`digital_write`仅修改目标位）
3. **继承扩展架构**：基础类实现核心通信，扩展类针对特定场景封装高级功能，提高代码复用性
4. **状态缓存机制**：缓存输出寄存器状态，减少I2C通信次数，提高操作效率
5. **兼容性设计**：同时支持PCF8574（地址0x20-0x27）和PCF8574A（地址0x38-0x3F），通过地址参数区分

---

## 使用说明
### 1. 硬件接线
1. 确认开发板I2C引脚（如树莓派Pico的GP0=SDA，GP1=SCL）
2. 连接电源引脚：模块VCC→开发板3.3V/5V，模块GND→开发板GND
3. 连接I2C引脚：模块SDA→开发板SDA，模块SCL→开发板SCL
4. （可选）连接中断引脚：模块INT→开发板GPIO（如GP6）
5. （可选）配置地址引脚A0-A2：根据需要接GND/VCC设置设备地址

### 2. 软件准备
- 烧录MicroPython固件到开发板（推荐v1.20.0及以上版本）
- 将`pcf8574.py`、`pcf8574_io8.py`和`main.py`上传到开发板

### 3. 程序运行
1. 通过开发工具（如Thonny）连接开发板
2. 运行`main.py`，观察测试结果（默认测试LED闪烁和按键检测）
3. 根据需要修改`main.py`中的引脚配置和测试逻辑

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/23 下午5:44
# @Author  : 缪贵成
# @File    : main.py
# @Description : 8位IO扩展驱动测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time
from pcf8574 import PCF8574
from pcf8574_io8 import PCF8574IO8

# ======================================== 全局变量 ============================================

PCF8574_ADDR = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:PCF8574 Five-way Button Test Program")
# 初始化I2C
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的PCF8574地址
    if 0x20 <= device <= 0x28:
        # 找到的设备是PCF_8574地址
        print("I2c hexadecimal address:", hex(device))
        PCF8574_ADDR = device
# 初始化PCF8574
pcf = PCF8574(i2c, PCF8574_ADDR)
# check if device is present
try:
    if pcf.check():
        print("PCF8574 detected successfully.")
except OSError as e:
    print("Error: PCF8574 not found!", e)
# PCF8574IO8 init
# Example: PORT0=(0,1), PORT1=(1,0), PORT2=(1,1), PORT3=(0,0)
ports_init = {0: (0, 1), 1: (1, 0), 2: (1, 1), 3: (0, 0)}
io8 = PCF8574IO8(pcf, ports_init=ports_init)
print("PCF8574IO8 initialized with default port states:", io8.ports_state())
time.sleep(3)

# ========================================  主程序  ============================================

# Test PORT operations
print("\n--- Test PORT operations ---")

# Set PORT0 to 3 (11)
io8.set_port(0, 3)
print("PORT0 set to 3 ->", io8.get_port(0))
time.sleep(3)

# Set PORT1 to 0 (00)
io8.set_port(1, 0)
print("PORT1 set to 0 ->", io8.get_port(1))
time.sleep(3)

# Configure PORT2 default to (0,1) and refresh
io8.configure_port(2, (0,1))
print("PORT2 configured to (0,1) ->", io8.get_port(2))
time.sleep(3)

# ======================== Test pin operations ======================
print("\n--- Test pin operations ---")

# Set pin 4 to 0 (pull low)
io8.set_pin(4, 0)
print("Pin 4 set to 0 ->", io8.get_pin(4))
time.sleep(3)

# Set pin 7 to 1 (high impedance)
io8.set_pin(7, 1)
print("Pin 7 set to 1 ->", io8.get_pin(7))
time.sleep(3)

# ======================== Test full byte operations ================
print("\n--- Test full byte read/write ---")

# Write all pins to 0xAA (10101010)
io8.write_all(0xAA)
print("Full byte written 0xAA ->", bin(io8.read_all()))
time.sleep(3)

# clear
io8.deinit()
print("IO8 deinitialized.")

```
---

## 注意事项
1. **电源选择**：PCF8574支持3.3V-5V供电，若驱动5V外设（如继电器），需接5V电源；仅3.3V设备可接3.3V
2. **地址冲突处理**：多模块级联时，需通过A0-A2引脚设置不同地址（0x20-0x27），避免I2C地址冲突
3. **输入上拉配置**：作为输入时，引脚内部无上拉电阻，需外部接10KΩ上拉电阻至VCC，否则读取值不稳定
4. **速度限制**：I2C总线频率建议不超过400KHz，过高可能导致通信失败
5. **输出电流限制**：每路I/O最大输出电流为10mA，总电流不超过50mA，驱动大电流设备需外接三极管

---
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：https://github.com/FreakStudioCN 

---

## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (MIT)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  
- **声明** —此项目代码产生任何非技术性问题与署名作者无关。
**版权归 FreakStudio 所有。**