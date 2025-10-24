# 总线步进电机扩展板（FreakStudio-多米诺系列）- MicroPython版本

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
本项目为基于 PCA9685 芯片的总线步进电机扩展板 MicroPython 驱动，支持 I2C 通信，可同时控制 1-4 路单极性步进电机，支持单相、双相、半步三种驱动模式，适用于机器人、自动化等场景。

---

## 主要功能
- **多电机独立控制**：最多支持 4 路步进电机，速度与方向可独立设置
- **三种驱动模式**：单相、双相、半步驱动，兼容 28BYJ-48 等常见步进电机
- **正反转/定步/连续运动**：支持电机正转、反转、定步运动与连续运动
- **高兼容性**：适配 MicroPython 标准库，易于集成

---

## 硬件要求

### 推荐测试硬件
- 树莓派 Pico/Pico W 或其他 MicroPython 兼容开发板
- FreakStudio 多米诺系列总线步进电机扩展板
- 5线4相步进电机（如 28BYJ-48，最多 4 路）
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

### `code/bus_step_motor.py`
总线步进电机控制类，封装多路步进电机的驱动模式、速度、方向与运动方式。

#### 类定义
```python
class BusStepMotor:
    """
    总线步进电机驱动类，支持 1-4 路步进电机的正反转、定步/连续运动、三种驱动模式。

    Class Variables:
        DRIVER_MODE_SINGLE (int): 单相驱动模式
        DRIVER_MODE_DOUBLE (int): 双相驱动模式
        DRIVER_MODE_HALF_STEP (int): 半步驱动模式
        FORWARD (int): 正转
        BACKWARD (int): 反转
        PHASES (dict): 不同驱动模式下的相位序列

    Attributes:
        pca9685 (PCA9685): PCA9685 实例
        motor_count (int): 电机数量（1-4）
        timers (list): 定时器列表
        steps (list): 目标步数列表
        step_counters (list): 当前步数计数器
        directions (list): 运动方向列表
        driver_modes (list): 驱动模式列表
        speeds (list): 转速列表

    Methods:
        start_continuous_motion(motor_id, direction, driver_mode, speed): 启动连续运动
        stop_continuous_motion(motor_id): 停止连续运动
        start_step_motion(motor_id, direction, driver_mode, speed, steps): 启动定步运动
        stop_step_motion(motor_id): 停止定步运动
    """
```

---

## 软件设计核心思想

- 高层 API 封装，简化多电机控制
- 严格遵循 PCA9685 通信协议，确保时序精度
- 支持多种驱动模式，兼容主流步进电机
- 易用性与扩展性，便于集成和二次开发

---

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| 扩展板引脚 | Pico GPIO 引脚 |
|------------|--------------|
| VCC        | 5V/3.3V      |
| GND        | GND          |
| SCL        | GP5          |
| SDA        | GP4          |

> **注意：**
> - SCL/SDA 可根据实际需求修改为其他 GPIO
> - 电机供电需满足电流需求

---

### 软件依赖

- **固件版本**：MicroPython v1.23.0+
- **内置库**：
  - `machine`（I2C 控制、定时器）
  - `time`（延时）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `code/pca9685.py` 和 `code/bus_step_motor.py` 到开发板
3. 根据硬件连接修改初始化参数
4. 运行主程序，观察步进电机控制效果

---

## 示例程序

```python
from machine import Pin, I2C
from pca9685 import PCA9685
from bus_step_motor import BusStepMotor
import time

i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
pca9685 = PCA9685(i2c, 0x40)
step_motor = BusStepMotor(pca9685, 4)

# 连续运动：电机1正转，单相驱动，速度10
step_motor.start_continuous_motion(1, BusStepMotor.FORWARD, BusStepMotor.DRIVER_MODE_SINGLE, 10)
time.sleep(10)
step_motor.stop_continuous_motion(1)

# 定步运动：电机1正转，单相驱动，速度100，步数1000
step_motor.start_step_motion(1, BusStepMotor.FORWARD, BusStepMotor.DRIVER_MODE_SINGLE, 100, 1000)
```

---

## 注意事项
- **电源要求**：确保步进电机供电充足，避免电压过低导致失步或运行不稳定
- **I2C通信稳定性**：布线需短且可靠，避免干扰
- **PWM频率设置**：建议 5000Hz，过高可能导致电机发热或效率降低

---

## 联系方式
如有问题或建议，请联系开发者：  
📧 邮箱：10696531183@qq.com  
💻 GitHub：https://github.com/FreakStudioCN

---

## 许可协议
- `pca9685.py` 采用 MIT 许可证（Adafruit 原创）
- `bus_step_motor.py` 及扩展部分采用 CC BY-NC 4.0 许可协议  
署名 — 请注明原作者及项目链接  
非商业性使用 — 禁止商业用途  
合理引用 — 可在代码注释、文档等注明来源  
版权归 FreakStudio 所有。