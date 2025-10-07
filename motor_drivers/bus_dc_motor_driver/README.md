
---

# 总线直流电机驱动扩展板（FreakStudio-多米诺系列）- MicroPython版本

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
本项目为基于 PCA9685 芯片的总线直流电机驱动扩展板 MicroPython 驱动，支持 I2C 通信，可同时控制 1-4 路直流电机的速度与方向，适用于多电机机器人、自动化等场景。

---

## 主要功能
- **多电机独立控制**：最多支持 4 路直流电机，速度与方向可独立设置
- **PWM调速**：通过 PCA9685 芯片生成高精度 PWM 信号
- **正反转/刹车/停止**：支持电机正转、反转、平稳停止与快速刹车
- **高兼容性**：适配 MicroPython 标准库，易于集成

---

## 硬件要求

### 推荐测试硬件
- 树莓派 Pico/Pico W 或其他 MicroPython 兼容开发板
- FreakStudio 多米诺系列总线电机驱动扩展板
- 6V-18V 直流电机（最多 4 路）
- 杜邦线若干

### 模块引脚说明
| 扩展板引脚 | 功能描述         |
|------------|------------------|
| VCC        | 电源正极         |
| GND        | 电源负极         |
| SCL        | I2C 时钟         |
| SDA        | I2C 数据         |
| M1~M4      | 电机接口         |

---

## 文件说明

### `code/pca9685.py`
PCA9685 PWM 控制核心类，提供频率设置、占空比调节等功能。

#### 类定义
```python
class PCA9685:
    """
    PCA9685 PWM 控制类，支持频率设置、通道占空比调节。

    Methods:
        reset(): 重置模块
        freq(freq): 设置/获取 PWM 频率
        pwm(index, on, off): 设置/获取指定通道 PWM
        duty(index, value, invert=False): 设置指定通道占空比
    """
```

### `code/bus_dc_motor.py`
总线直流电机控制类，封装多路电机的速度与方向控制。

#### 类定义
```python
class BusDCMotor:
    """
    总线直流电机驱动类，支持 1-4 路电机的正反转、调速、停止与刹车。

    Attributes:
        pca9685 (PCA9685): PCA9685 实例
        motor_count (int): 电机数量（1-4）

    Methods:
        set_motor_speed(motor_id, speed, direction=0): 设置指定电机速度与方向
        stop_motor(motor_id): 平稳停止指定电机
        break_motor(motor_id): 快速刹车指定电机
    """
```

---

## 软件设计核心思想

- 高层 API 封装，简化多电机控制
- 严格遵循 PCA9685 通信协议，确保时序精度
- 易用性与扩展性，便于集成和二次开发

---

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| 扩展板引脚 | Pico GPIO 引脚 |
|------------|----------------|
| VCC        | 5V/3.3V        |
| GND        | GND            |
| SCL        | GP7            |
| SDA        | GP6            |

> **注意：**
> - SCL/SDA 可根据实际需求修改为其他 GPIO
> - 电机供电需满足电流需求

---

### 软件依赖

- **固件版本**：MicroPython v1.23.0+
- **内置库**：
  - `machine`（I2C 控制）
  - `time`（延时）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `code/pca9685.py` 和 `code/bus_dc_motor.py` 到开发板
3. 根据硬件连接修改初始化参数
4. 运行主程序，观察电机控制效果

---

## 示例程序

```python
from machine import Pin, I2C
from pca9685 import PCA9685
from bus_dc_motor import BusDCMotor
import time

i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)
pca9685 = PCA9685(i2c, 0x40)
motor = BusDCMotor(pca9685, 4)

motor.set_motor_speed(1, 2000, 0)  # 电机1正转
motor.set_motor_speed(2, 2000, 1)  # 电机2反转
time.sleep(5)
motor.stop_motor(1)
motor.break_motor(2)
```

---

## 注意事项
- **电源要求**：确保电机供电充足，避免电压过低导致失速
- **I2C通信稳定性**：布线需短且可靠，避免干扰
- **PWM频率设置**：建议 1000Hz，过高可能导致电机发热

---

## 联系方式
如有问题或建议，请联系开发者：  
📧 邮箱：10696531183@qq.com  
💻 GitHub：https://github.com/FreakStudioCN

---

## 许可协议
- `pca9685.py` 采用 MIT 许可证（Adafruit 原创）
- `bus_dc_motor.py` 及扩展部分采用 CC BY-NC 4.0 许可协议  
署名 — 请注明原作者及项目链接  
非商业性使用 — 禁止商业用途  
合理引用 — 可在代码注释、文档等注明来源  
版权归 FreakStudio 所有。

---