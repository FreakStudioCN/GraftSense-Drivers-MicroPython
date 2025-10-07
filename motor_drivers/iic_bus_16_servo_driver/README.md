# PCA9685  16路PWM驱动板示例程序 - MicroPython版本

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
基于 PCA9685 芯片的 16 路 PWM 控制扩展模块驱动，支持通过 I2C 接口控制多达 16 路 PWM 输出信号。该模块常用于舵机控制、LED 调光、机械臂、机器人等需要多通道 PWM 控制的场景。

本项目提供了 MicroPython 驱动代码及示例程序，方便开发者快速接入 PCA9685 模块，实现舵机角度控制、速度控制与脉宽直接控制。

---

## 主要功能
- **舵机支持**：
  - 180° 舵机角度控制（支持平滑移动速度）
  - 360° 舵机速度控制（正反转/停转）
- **多通道 PWM 控制**：最多支持 16 路独立输出
- **I2C 通信**：地址范围 0x40 ~ 0x4F，支持总线共享
- **通道管理**：提供统一接口`read_distance()`，便于快速集成
- **简洁 API**：set_angle() / set_speed() / stop() / detach_servo()

---

## 硬件要求
### 推荐测试硬件
- 树莓派 Pico / Pico W（MicroPython v1.23.0 测试）
- 驱动板
- 舵机（180°/360°）
- 杜邦线、电源模块

### 模块引脚说明
| PCA9685 引脚 | 功能描述 |
|--------------|----------|
| VCC          | 电源正极（3.3V-5V） |
| GND          | 电源负极 |
| SDA        | I2C 数据引脚 |
| SCL       | I2C 时钟引脚 |
| OE           | 输出使能（可接 GND）|


---

## 文件说明
### pca9685.py
PCA9685 芯片驱动，提供 I2C 通信、复位、频率设置、PWM/duty 设置功能。

### bus_servo.py
基于 PCA9685 的舵机控制器，提供 180°/360° 舵机角度与速度控制接口。

#### 类定义
```python
class BusPWMServoController:
    """
    基于 PCA9685 的 16 路 PWM 舵机控制器，支持 180° 舵机角度控制、360° 连续舵机速度控制，以及脉宽直接写入。

    Attributes:
        _pca: PCA9685 实例，需支持 freq(hz)、duty(channel, value) 方法。
        _freq (int): PWM 输出频率（Hz）。
        _cfg (dict): 通道配置字典。

    Methods:
        __init__(pca, freq=50): 初始化并设置频率。
        attach_servo(...): 注册通道与校准参数。
        detach_servo(channel): 取消注册并停止输出。
        set_angle(...): 设置 180° 舵机角度。
        set_speed(...): 设置 360° 舵机速度。
        set_pulse_us(channel, pulse_us): 直接写入脉宽。
        stop(channel): 回中或关闭输出。
        to_pwm_ticks(pulse_us): µs 转 tick。
    ==========================================
    16-channel PWM servo controller based on PCA9685. Supports 180°/360° servos and direct pulse write.

    Attributes:
        _pca: An instance of PCA9685, which needs to support the freq(hz) and duty(channel, value) methods.
        _freq (int): PWM output frequency (Hz).
        _cfg (dict): Channel configuration dictionary.

    Methods:
        __init__(pca, freq=50): Initialize and set the frequency.
        attach_servo(...): Register the channel and calibration parameters.
        detach_servo(channel): Unregister and stop the output.
        set_angle(...): Set the angle of a 180° servo.
        set_speed(...): Set the speed of a 360° servo.
        set_pulse_us(channel, pulse_us): Directly write the pulse width.
        stop(channel): Return to the middle position or turn off the output.
        to_pwm_ticks(pulse_us): Convert µs to ticks.
    """

    SERVO_180 = const(0x00)
    SERVO_360 = const(0x01)

    def __init__(self, pca, freq=50):
```

### main.py
示例主程序，演示如何绑定通道、设置舵机角度与速度。

## 软件设计核心思想
### 模块化设计
- pca9685.py：底层寄存器控制，硬件抽象层（HAL）

- bus_servo.py：基于 HAL 的舵机控制逻辑封装

- main.py：示例应用，调用接口实现功能


### 跨平台兼容

- 仅依赖 MicroPython 标准库：machine.I2C、time、ustruct、micropython.const

### 硬件抽象层设计

- pca9685.py 负责与硬件通信

- bus_servo.py 封装更高层 API，调用统一 freq() / duty() 接口

### 清晰的接口文档
- 提供函数说明、参数说明、返回值说明  
- 包含错误码定义及处理建议

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| PCA9685 引脚 | Pico GPIO 引脚 |
| ---------- | ------------ |
| VCC        | 3.3V/5V      |
| GND        | GND          |
| SDA        | GP6          |
| SCL        | GP7          |

> **注意：**
> - 确保舵机电源电流足够（单独供电更佳）
> - `I2C` 地址范围 0x40~0x4F，需要根据模块焊盘/拨码开关配置

---

### 软件依赖


- **固件版本**：MicroPython v1.23.0 
- **内置库**：
  - `machine`（用于 GPIO、UART、I2C 控制）
  - `time`（用于延时与时间测量）
  - `ustruct`（用于打包解包）
  - `micropython.const`（常量）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 将 **MicroPython 固件** 烧录到树莓派 Pico  
2. 上传 `pca9685.py`,`bus_servo.py`,`main.py` 到 Pico  
3. 根据硬件连接修改 `main.py` 中的引脚配置  
4. 在开发工具中运行 `main.py`，测试程序


## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : PCA968516路PWM驱动板示例程序

# ======================================== 导入相关模块 =========================================

#导入时间模块
import time
# 导入MicroPython标准库模块
from machine import Pin, I2C
# 导入总线舵机控制器模块
from bus_servo import BusPWMServoController
# 导入PCA9685模块
from pca9685 import PCA9685

# ======================================== 全局变量 ============================================

# 自动扫描 PCA9685 地址（0x40~0x4F）
addr = 0x40

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Using PCA9685 to control the angles of two servos")
# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

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
        # 判断设备地址是否为PCF8575的地址
        if device >= 0x40 and device <= 0x4F:
            print("I2C hexadecimal address: ", hex(device))
pca = PCA9685(i2c,  address=device)

# 创建控制器（50Hz 常用于舵机）
srv = BusPWMServoController(pca, freq=50)

# --------------- 绑定两个通道 ---------------

# 通道0：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(0, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
# 通道1：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(1, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
# 通道2：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(2, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
# 通道3：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(3, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)

#设置360°舵机通道

# 通道1：360° 连续舵机，自带停转点在 1500us 附近；如需反向可 reversed=True
srv.attach_servo(4, BusPWMServoController.SERVO_360, min_us=1000, max_us=2000, neutral_us=1500)
# 通道1：360° 连续舵机，自带停转点在 1500us 附近；如需反向可 reversed=True
srv.attach_servo(5, BusPWMServoController.SERVO_360, min_us=1000, max_us=2000, neutral_us=1500)

# ========================================  主程序  ===========================================

# --------------- 演示 180° 角度控制 ---------------
srv.set_angle(0, 0.0)          # 转到 0°
srv.set_angle(1, 0.0)          # 转到 0°
srv.set_angle(2, 0.0)          # 转到 0°
srv.set_angle(3, 0.0)          # 转到 0°
time.sleep(1)
srv.set_angle(0, 90.0, speed_deg_per_s=120)  # 以约 120°/s 平滑转到 90°
srv.set_angle(1, 90.0, speed_deg_per_s=120)  # 以约 120°/s 平滑转到 90°
srv.set_angle(2, 90.0, speed_deg_per_s=120)  # 以约 120°/s 平滑转到 90°
srv.set_angle(3, 90.0, speed_deg_per_s=120)  # 以约 120°/s 平滑转到 90°
time.sleep(1)
srv.set_angle(0, 180.0, speed_deg_per_s=180) # 平滑转到 180°
srv.set_angle(1, 180.0, speed_deg_per_s=180) # 平滑转到 180°
srv.set_angle(2, 180.0, speed_deg_per_s=180) # 平滑转到 180°
srv.set_angle(3, 180.0, speed_deg_per_s=180) # 平滑转到 180°
time.sleep(1)
srv.stop(0)                     # 回中或停

# --------------- 演示 360° 速度控制 ---------------
srv.set_speed(4, +0.6)          # 顺时针中速
srv.set_speed(5, +0.6)          # 顺时针中速
time.sleep(20)
srv.set_speed(4, -0.6)          # 反向中速
srv.set_speed(5, -0.6)          # 反向中速
time.sleep(20)
srv.stop(4)                     # 4号通道回中或停
srv.stop(5)                     # 5号通道回中或停
time.sleep(0.5)                  # 回中或停
srv.detach_servo(0)             # 关闭输出并解除绑定
srv.detach_servo(1)             # 关闭输出并解除绑定
srv.detach_servo(2)             # 关闭输出并解除绑定
srv.detach_servo(3)             # 关闭输出并解除绑定
srv.detach_servo(4)             # 关闭输出并解除绑定
srv.detach_servo(5)             # 关闭输出并解除绑定

```

## 注意事项
### 使用限制
- `PCA9685` 输出频率需与舵机规格匹配（一般 50Hz）

- 舵机电源需独立供电，避免板载电源过载

- `I2C` 地址需正确配置（0x40~0x4F）

### 测距范围限制
- 有效范围约 **20cm ~ 7m**  
- 低于 20cm 或超过 7m 的数据视为无效  
- 实际盲区约为 **25cm**（模块物理特性决定）

---

### 模式配置要求

| 模式     | 注意事项 |
|----------|----------|
| I2C      | `I2C` 地址范围 0x40~0x4F，需要根据模块焊盘/拨码开关配置 |

---

### 电源要求
- 供电电压：**5V**
- 确保电源稳定，避免电压波动
- 大功率应用时建议单独供电

---

## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：1098875044@qq.com  
💻 **GitHub**：[https://github.com/hogeiha]

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


