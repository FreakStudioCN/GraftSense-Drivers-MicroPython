# TCS34725 颜色识别模块驱动 - MicroPython版本

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
TCS34725是一款高精度RGB颜色识别传感器，集成了红外滤光片和16位ADC，可精确检测环境光和物体表面颜色。该模块支持I2C通信接口，工作电压范围为2.7V-3.6V，适用于颜色检测、光强度测量、产品分拣、环境光适应等场景。

本项目提供基于MicroPython的TCS34725模块驱动代码及测试程序，实现传感器初始化、参数配置、颜色数据采集与转换等功能，可直接与支持MicroPython的开发板（如树莓派Pico）配合使用。

---

## 主要功能
- 传感器基础控制：支持激活/休眠模式切换、强制采样触发
- 参数灵活配置：可设置积分时间（6.5ms-700ms）和增益（1x/4x/16x/60x）
- 数据采集功能：获取原始RGB清晰值（R/G/B/C）和红外值（IR）
- 颜色转换处理：支持RGB值转HSV格式、计算色温（CCT）和光照强度（Lux）
- 阈值检测功能：可设置低/高阈值，实现颜色触发报警功能
- 多平台兼容：适配支持MicroPython的各类开发板，无需修改核心代码

---

## 硬件要求
### 推荐测试硬件
- 支持MicroPython的开发板（如树莓派Pico/Pico W）
- TCS34725颜色识别模块（带I2C接口和LED补光灯）
- 杜邦线（公对母，至少4根）
- （可选）面包板（便于临时接线测试）
- （可选）3.3V电源模块（开发板供电不足时使用）

### 模块引脚说明
| TCS34725模块引脚 | 功能描述 | 开发板连接建议 |
|------------------|----------|---------------|
| VCC              | 电源正极 | 3.3V |
| GND              | 电源负极 | GND（需与开发板共地） |
| SDA              | I2C数据引脚 | 开发板I2C SDA引脚（如树莓派Pico的GP4） |
| SCL              | I2C时钟引脚 | 开发板I2C SCL引脚（如树莓派Pico的GP5） |
| LED              | 补光灯控制引脚 | 开发板GPIO（可选，如不接则默认常亮） |

---

## 文件说明
### 1. main.py
核心测试文件，包含`TCS34725`类及测试逻辑，主要功能如下：

- **核心类 `TCS34725`**：封装传感器控制逻辑
  - `__init__(self, i2c, address=0x29)`：初始化传感器；参数`i2c`为MicroPython的I2C对象，`address`为传感器I2C地址（默认0x29）
  - `activate(self)`：激活传感器（从休眠模式唤醒）
  - `deactivate(self)`：使传感器进入休眠模式（低功耗）
  - `set_integration_time(self, it)`：设置积分时间（影响采样精度和响应速度）
  - `set_gain(self, gain)`：设置增益（影响灵敏度，低光环境需提高增益）
  - `get_raw_data(self)`：获取原始RGBIR数据（返回元组：(clear, red, green, blue, ir)）
  - `calculate_colour_temperature(self, r, g, b)`：计算色温（CCT）
  - `calculate_lux(self, r, g, b)`：计算光照强度（Lux）
  - `rgb_to_hsv(self, r, g, b)`：将RGB值转换为HSV格式
  - `set_interrupt_thresholds(self, low, high)`：设置中断阈值
  - `clear_interrupt(self)`：清除中断标志

- **测试逻辑**：
  - 初始化I2C总线和传感器对象
  - 配置积分时间和增益参数
  - 循环采集颜色数据并打印（原始RGB值、色温、光照强度、HSV值、HEX颜色码）
  - 支持键盘中断（Ctrl+C）终止程序

---

## 软件设计核心思想
1. **硬件抽象层设计**：将传感器寄存器操作封装在类方法中，隐藏底层I2C通信细节，用户无需了解寄存器地址即可操作
2. **参数自适应配置**：通过积分时间和增益组合，实现不同光照环境下的最佳采样效果（强光用短积分时间+低增益，弱光用长积分时间+高增益）
3. **数据转换标准化**：提供RGB到HSV、HEX的转换功能，将原始传感器数据转换为更易理解的颜色格式
4. **低功耗优化**：支持休眠/激活模式切换，闲置时可进入休眠模式降低功耗（电流从12mA降至0.5mA）
5. **异常处理机制**：对I2C通信错误、参数范围超限等情况进行捕获和处理，提高程序稳定性

---

## 使用说明
### 1. 硬件接线
1. 确认开发板I2C引脚（如树莓派Pico的GP4=SDA，GP5=SCL）
2. 连接电源引脚：模块VCC→开发板3.3V，模块GND→开发板GND
3. 连接I2C引脚：模块SDA→开发板SDA，模块SCL→开发板SCL
4. （可选）连接LED引脚：模块LED→开发板GPIO（如GP6），用于控制补光灯

### 2. 软件准备
- 烧录MicroPython固件到开发板（推荐v1.20.0及以上版本）
- 安装支持MicroPython的开发工具（如Thonny、uPyCraft）

### 3. 程序运行
1. 将`main.py`文件上传到开发板根目录
2. 连接开发板到电脑，打开开发工具并选择对应端口
3. 运行程序，传感器将开始采集颜色数据并通过串口输出

---

## 示例程序
以下是`main.py`中的核心测试代码片段：
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/16 下午8:17
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于TCS34725的颜色识别模块驱动文件测试

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from tcs34725_color import TCS34725, html_rgb, html_hex

# ======================================== 全局变量 ============================================

tcs_addr = None
# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:test TCS34725 color recognition sensor")
# 根据硬件修改引脚
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list:list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    if 0x60 <= device <= 0x7A:
        print("I2c hexadecimal address:", hex(device))
        tcs_addr = device

sensor = TCS34725(i2c, tcs_addr)
# 获取并打印传感器 ID
led = Pin(2, Pin.OUT)
sensor_id = sensor.sensor_id()
print(f"Sensor ID: 0x{sensor_id:02X}")
time.sleep(3)
# 激活
print("Testing sensor activation...")
sensor.active(True, led)
print("Sensor activated:", sensor.active())
time.sleep(3)

# 积分时间
print("Testing integration time setting...")
sensor.integration_time(24.0)  # 设置 24ms
print("Integration time set to:", sensor.integration_time(), "ms")
time.sleep(3)

print("Testing gain setting...")
# 设置增益为 4
sensor.gain(4)
print("Gain set to:", sensor.gain(None))
time.sleep(3)

print("Testing threshold setting...")
# 设置阈值  小于100和大于2000，连续五次超范围触发中断
sensor.threshold(cycles=5, min_value=100, max_value=2000)
print("Threshold set. Reading back values...")
print("Threshold (cycles, min, max):", sensor.threshold())
time.sleep(3)

# ========================================  主程序  ============================================

while True:
    try:
        # 数据读取测试
        print("Testing color and lux data reading...")
        data_raw = sensor.read(raw=True)
        print("Raw data (R, G, B, C):", data_raw)
        # 色温和光照强度
        cct, lux = sensor.read(raw=False)
        print(f"Calculated CCT: {cct:.2f} K, Lux: {lux:.2f}")
        time.sleep(3)
        """
        # 中断测试
        print("Testing interrupt clear...")
        print("Interrupt status before clear:", sensor.interrupt())
        sensor.interrupt(False)
        print("Interrupt cleared. Status now:", sensor.interrupt())
        time.sleep(3)
        """
        # HTML RGB / HEX 测试
        print("Testing html_rgb and html_hex conversion...")
        rgb = html_rgb(data_raw)
        hex_color = html_hex(data_raw)
        print("RGB values:", rgb)
        print("HEX string:", hex_color)
        time.sleep(3)
    except Exception as e:
        print(" stopping program...")


```
---
## 注意事项
- **电源要求**：TCS34725 模块仅支持 3.3V 供电，严禁接 5V 电源，否则会烧毁传感器
- **I2C 地址冲突**：模块默认 I2C 地址为 0x29，若与其他 I2C 设备地址冲突，需检查硬件接线或更换设备
- **环境光干扰**：检测颜色时应避免强光直射或杂散光干扰，必要时使用补光灯（通过 LED 引脚控制）
- **积分时间与增益选择**：
  - 强光环境：建议使用短积分时间（如 6.5ms）+ 低增益（1x）
  - 弱光环境：建议使用长积分时间（如 700ms）+ 高增益（60x）
- **校准需求**：高精度颜色检测前需进行白平衡校准（可通过白色物体采集数据进行修正）
- **连接线长度**：I2C 连接线不宜过长（建议≤20cm），否则可能导致通信不稳定~~~~

---
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：https://github.com/FreakStudioCN 

---

## 许可协议
本项目中，除 machine 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。 
- **说明** — 代码含参考部分,出现非技术问题和署名作者无关。  
**版权归 FreakStudio 所有。**
