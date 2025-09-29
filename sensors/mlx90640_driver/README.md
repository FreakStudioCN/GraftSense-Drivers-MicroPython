# MLX90640 红外温度传感器驱动 - MicroPython版本

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
MLX90640是一款基于红外检测原理的24×32点阵温度传感器，可实现非接触式温度测量，检测范围广（-40℃至300℃），适用于体温检测、工业测温、智能家居环境监控等场景。

本项目提供基于MicroPython的MLX90640传感器驱动及测试程序，通过I2C接口与传感器通信，支持温度数据采集、刷新率配置等功能，适配多种MicroPython开发板。

---

## 主要功能
- **完整数据采集**：读取24×32点阵的全部温度数据
- **灵活配置**：支持多种刷新率设置（0.5Hz至64Hz）
- **数据处理**：提供温度数据转换与基本统计（最大值、最小值、平均值）
- **I2C通信**：通过标准I2C接口实现与传感器的通信
- **跨平台兼容**：树莓派Pico等开发板

---

## 硬件要求
### 推荐测试硬件
- MicroPython兼容开发板（ESP32/ESP8266/树莓派Pico）
- MLX90640红外温度传感器模块
- 杜邦线若干
- 面包板（可选，用于接线测试）

### 模块引脚说明
| MLX90640引脚 | 功能描述 |
|--------------|----------|
| VCC          | 电源正极（3.3V，不可接5V） |
| GND          | 电源负极 |
| SCL          | I2C时钟线 |
| SDA          | I2C数据线 |
| ADDR         | I2C地址选择（接地默认0x33，接VCC为0x34） |

---

## 文件说明
### 1. mlx90640.py
包含传感器驱动核心类及辅助类：

| 类/方法 | 类型 | 功能描述 |
|---------|------|----------|
| `RefreshRate` | 枚举类 | 定义传感器支持的刷新率选项，包括0.5Hz、1Hz、2Hz等多种速率 |
| `I2CDevice` | 通信类 | 封装I2C通信底层操作 |
| `I2CDevice.write_then_read_into(write_buf, read_buf, *, out_start=0, out_end=None, in_start=0, in_end=None)` | 实例方法 | 先向传感器写入数据（通常为寄存器地址），再从传感器读取数据到指定缓冲区；通过memoryview优化内存使用，非ISR-safe |
| `I2CDevice.write(buf, *, start=0, end=None)` | 实例方法 | 向传感器写入缓冲区数据；调用machine.I2C.writeto实现，要求buf为bytes或bytearray类型，写入失败抛出OSError，非ISR-safe |
| `MLX90640` | 传感器类 | 封装MLX90640传感器的高层操作接口（初始化、温度读取、刷新率设置等） |
| `MLX90640.__init__(i2c_device, address=0x33)` | 构造方法 | 初始化传感器实例，建立与I2C设备的连接 |
| `MLX90640.init()` | 实例方法 | 初始化传感器，加载校准数据 |
| `MLX90640.get_frame()` | 实例方法 | 读取一帧温度数据（24×32点阵），返回温度值数组 |
| `MLX90640.set_refresh_rate(rate)` | 实例方法 | 设置传感器数据刷新率，参数为RefreshRate枚举值 |

### 2. main.py
测试主程序，无自定义类，核心功能通过函数实现：
- 初始化I2C总线和传感器实例
- 配置传感器刷新率
- 循环读取温度数据并输出统计信息（最大值、最小值、平均值）
- 打印局部区域（如左上角4×4）温度分布

---

## 软件设计核心思想
### 分层设计
- 底层：`I2CDevice`类封装I2C通信协议，提供基础读写操作
- 中层：`MLX90640`类实现传感器特定命令解析与数据转换
- 高层：`main.py`实现应用级功能，如数据展示与统计

### 数据处理优化
- 采用缓冲区操作减少内存分配，提高处理效率
- 温度数据转换算法基于传感器 datasheet 实现，确保测量精度

### 跨平台兼容
- 仅依赖MicroPython标准库（machine.I2C、time）
- 硬件接口参数化，适配不同开发板的I2C引脚配置

---

## 使用说明
### 硬件接线（树莓派pico示例）

| MLX90640引脚 | GPIO引脚        |
|--------------|---------------|
| VCC          | 3.3V          |
| GND          | GND           |
| SCL          | GPIO1         |
| SDA          | GPIO0         |
| ADDR         | GND（默认地址0x33） |

> **注意**：
> - 传感器必须使用3.3V供电，接5V会损坏芯片
> - 接线时确保I2C引脚与开发板配置一致

### 软件依赖
- **固件版本**：MicroPython v1.23.0及以上
- **内置库**：
  - `machine`（I2C总线与GPIO控制）
  - `time`（延时功能）

### 安装步骤
1. 将MicroPython固件烧录到开发板
2. 上传`mlx90640.py`和`main.py`到开发板
3. 根据硬件连接修改`main.py`中的I2C引脚配置
4. 运行`main.py`开始测试

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午11:14
# @Author  : 缪贵成
# @File    : main.py
# @Description :mlx90640点阵红外温度传感器模块驱动测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C
import time
from mlx90640 import MLX90640, RefreshRate

# ======================================== 全局变量 ============================================

mlxaddr=None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:Testing the MLX90640 fractional infrared temperature sensor")
# Initialize I2C bus (adjust pins if needed)

i2c = I2C(0, scl=1, sda=0, freq=100000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    if 0x31 <= device <= 0x35:
        print("I2c hexadecimal address:", hex(device))
        mlxaddr = device

# Initialize MLX90640
try:
    thermal_camera = MLX90640(i2c, mlxaddr)
    print("MLX90640 sensor initialized successfully")
except ValueError as init_error:
    print(f"Sensor initialization failed: {init_error}")
    raise SystemExit(1)
# Show sensor info
print(f"Device serial number: {thermal_camera.serial_number}")
# Set refresh rate
try:
    thermal_camera.refresh_rate = RefreshRate.REFRESH_2_HZ
    print(f"Refresh rate set to {thermal_camera.refresh_rate} Hz")
except ValueError as rate_error:
    print(f"Failed to set refresh rate: {rate_error}")
    raise SystemExit(1)
# 比如测人体时候发射率
thermal_camera.emissivity = 0.92
# Prepare temperature data buffer
temperature_frame = [0.0] * 768

# ========================================  主程序  ============================================

# Main measurement loop
try:
    while True:
        try:
            thermal_camera.get_frame(temperature_frame)
        except RuntimeError as read_error:
            print(f"Frame acquisition failed: {read_error}")
            time.sleep(0.5)
            continue

        # Statistics
        min_temp = min(temperature_frame)
        max_temp = max(temperature_frame)
        avg_temp = sum(temperature_frame) / len(temperature_frame)

        print("\n--- Temperature Statistics ---")
        print(f"Min: {min_temp:.2f} °C | Max: {max_temp:.2f} °C | Avg: {avg_temp:.2f} °C")

        # Print a few pixels (top-left 4*4 area)
        print("--- Sample Pixels (Top-Left 4x4) ---")
        # 打印左上角4*4像素
        for row in range(4):
            row_data = [
                # 这里row*32因为一行是32个像素点，所以这个row*32表示每一行的索引，第0行索引是0
                f"{temperature_frame[row*32 + col]:5.1f}"
                for col in range(4)
            ]
            print(" | ".join(row_data))

        # 等待下一次测量，用刷新率编号加1作为近似值来计算，防止读取数据过快
        time.sleep(1.0 / (thermal_camera.refresh_rate + 1))

except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    print("Testing process completed")


```
---

## 注意事项
- 传感器初始化失败时，检查I2C地址是否正确（默认0x33，ADDR引脚接VCC时为0x34）
- 刷新率设置过高可能导致数据读取不稳定，建议根据应用场景选择合适速率
- 传感器工作时会发热，可能影响测量精度，建议做好散热或进行温度补偿
- 避免在强电磁干扰环境中使用，以免影响I2C通信稳定性
- 测试到的结果最小值显示273.15摄氏度是因为像素点里面有坏点或者失效像素点，代码中将失效点标注为-273.15摄氏度
---
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：https://github.com/FreakStudioCN

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
- **说明** — 代码含参考部分,出现非技术问题和署名作者无关。  
**版权归 FreakStudio 所有。**