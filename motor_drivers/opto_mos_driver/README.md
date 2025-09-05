# OptoMosSimple 驱动 - MicroPython版本

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
OptoMosSimple 驱动用于控制基于光耦隔离 + MOS 管的电路，通过 PWM（脉冲宽度调制）信号的占空比调节负载（如电机、灯光等）的输出强度。该驱动具有接口简洁、兼容性强、控制精准等特点，适用于智能家居、机器人控制、灯光调节等场景。

本项目提供基于 MicroPython 的驱动代码及示例程序，方便开发者快速集成光耦隔离 MOS 电路的控制功能。

---

## 主要功能
- **灵活的占空比控制**：
  - 支持直接设置占空比计数值（0 至 PWM 最大计数）
  - 支持通过百分比设置占空比（0.0% 至 100.0%）
- **输出模式**：
  - 正常输出模式
  - 反向输出模式（占空比逻辑翻转）
- **便捷操作**：提供 `full_on()`（全功率）、`off()`（关闭）等快捷方法
- **状态反馈**：通过 `get_status()` 获取当前输出状态
- **资源管理**：支持释放 PWM 资源，避免硬件冲突
- **跨平台支持**：兼容所有支持 MicroPython 的开发板（如树莓派 Pico 等）

---

## 硬件要求
### 推荐测试硬件
- 支持 MicroPython 的开发板（如树莓派 Pico/Pico W）
- 光耦隔离 MOS 管模块（如基于 PC817 光耦 + IRF540 MOS 管的电路）
- 负载设备（如直流电机、LED 灯等）
- 杜邦线若干
- 电源（根据负载需求选择合适电压和电流的电源）

### 模块连接说明
| 光耦 MOS 模块引脚 | 开发板引脚 | 说明 |
|------------------|------------|------|
| VCC              | 3.3V/5V    | 模块电源（根据模块规格选择） |
| GND              | GND        | 接地 |
| IN               | GPIO 引脚  | 连接开发板的 PWM 输出引脚 |
| OUT+             | 负载正极   | 连接负载的正极 |
| OUT-             | 负载负极   | 连接负载的负极 |

> **注意**：负载电源需单独提供，与开发板电源共地以保证信号同步。

---

## 文件说明
### opto_mos_simple.py
- **核心类 `OptoMosSimple`**：  
  用于控制光耦+MOS管电路，通过PWM信号的占空比驱动负载，仅接收已创建的PWM对象。
  
  - **方法及作用**：  
    - `__init__()`：初始化PWM控制对象，需传入已创建的PWM实例，可指定PWM最大计数和是否反向输出。  
    - `init()`：初始化输出，将占空比置为0%（关闭状态）。  
    - `set_duty(duty)`：设置占空比计数值（范围0至PWM最大计数），超出范围自动裁剪。  
    - `set_percent(percent)`：通过百分比（0.0至100.0）设置占空比，超出范围自动裁剪。  
    - `full_on()`：将输出设为全功率（100%占空比）。  
    - `off()`：关闭输出（0%占空比）。  
    - `get_status()`：返回当前状态字典，包含占空比计数值、百分比、PWM最大计数和是否反向输出。  
    - `deinit()`：释放或复位PWM资源，若平台支持则调用`pwm.deinit()`，否则将占空比置为0。

### main.py
- 示例测试程序，用于演示`OptoMosSimple`类的各项功能。  
- 包含创建PWM对象、初始化驱动、测试占空比设置（计数值和百分比）、切换全功率/关闭状态、测试反向输出模式及释放资源等操作，帮助开发者快速理解驱动的使用方法。

---

## 软件设计核心思想
### 模块化设计
- 将 PWM 控制逻辑封装在 `OptoMosSimple` 类中，通过统一接口对外提供服务
- 分离 PWM 实例创建与控制逻辑，提高代码复用性（同一 PWM 实例可被多个类共享）

### 灵活性与兼容性
- 支持不同 PWM 最大计数范围（如 65535 或 1023），适配不同硬件平台
- 提供反向输出模式，兼容不同逻辑的光耦 MOS 电路（高电平导通/低电平导通）

### 健壮性设计
- 占空比参数自动裁剪，超出范围时自动限制在有效区间，避免错误输入导致的硬件异常
- 提供资源释放方法 `deinit()`，确保程序退出时硬件资源正确复位

### 易用性设计
- 提供百分比设置接口，简化用户操作（无需关注底层 PWM 计数细节）
- 提供状态查询接口，方便调试和状态监控

---

## 使用说明
### 硬件接线（树莓派 Pico 示例）
| 光耦 MOS 模块 | 树莓派 Pico 引脚 |
|--------------|------------------|
| VCC          | 3.3V             |
| GND          | GND              |
| IN           | GP15             |
| OUT+         | 电机正极（接外部电源） |
| OUT-         | 电机负极（接外部电源） |

> **注意**：
> - 确保电源电压与负载匹配，避免过载损坏模块
> - 开发板与外部电源需共地，否则可能导致控制信号异常

---

### 软件依赖
- **固件版本**：MicroPython v1.23.0+
- **内置库**：
  - `machine`（用于 PWM、Pin 控制）
  - `time`（用于延时）
- **开发工具**：Thonny 或其他 MicroPython 开发环境

---

### 安装步骤
1. 将 MicroPython 固件烧录到开发板
2. 上传 `opto_mos_simple.py` 和 `main.py` 到开发板
3. 根据硬件连接修改 `main.py` 中的引脚配置（如 PWM 输出引脚）
4. 运行 `main.py`，测试光耦 MOS 模块的控制功能

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 上午9:42
# @Author  : 缪贵成
# @File    : main.py
# @Description : 光耦隔离 MOS 单电机驱动测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, PWM
from opto_mos_simple import OptoMosSimple

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

#上电延时
time.sleep(3)
print("FreakStudio:  OptoMosSimple Test Start ")
# 创建 PWM 对象，GPIO15 输出
pwm = PWM(Pin(15))
# Set PWM frequency to 1kHz
pwm.freq(1000)
print("PWM object created on Pin 15 with 1kHz frequency.")

# 创建驱动实例
driver = OptoMosSimple(pwm)
print("Driver object created.")

# 初始化驱动
driver.init()
print("[init] Initialized ->", driver.get_status())

# ======================================== 主程序 ===============================================

# 测试 set_duty 方法
print("[set_duty] Set duty=10000")
driver.set_duty(10000)
print("Status:", driver.get_status())

print("[set_duty] Set duty=70000 (out of range, auto clipped)")
driver.set_duty(70000)
print("Status:", driver.get_status())

# 测试 set_percent 方法
print("[set_percent] Set 25% duty cycle")
driver.set_percent(25.0)
print("Status:", driver.get_status())

print("[set_percent] Set 150% duty cycle (out of range, auto clipped)")
driver.set_percent(150.0)
print("Status:", driver.get_status())

# 测试 full_on 方法
print("[full_on] Full ON")
driver.full_on()
print("Status:", driver.get_status())
time.sleep(5)

# 测试 off 方法
print("[off] Turn OFF")
driver.off()
print("Status:", driver.get_status())
time.sleep(10)

# 测试 inverted 模式（创建新的 PWM 对象）
print("[inverted] Testing inverted mode")
pwm_inv = PWM(Pin(16))  # 使用不同 GPIO 避免与 driver 冲突
pwm_inv.freq(1000)
driver_inv = OptoMosSimple(pwm_inv, inverted=True)
driver_inv.init()
driver_inv.set_percent(30.0)
print("Inverted 30% ->", driver_inv.get_status())
driver_inv.full_on()
print("Inverted full_on ->", driver_inv.get_status())
driver_inv.off()
print("Inverted off ->", driver_inv.get_status())

# 释放资源
print("[deinit] Release resources")
driver.deinit()
driver_inv.deinit()
print("PWM released.")

print("=== OptoMosSimple Test End ===")


```
## 注意事项
###  PWM 频率选择
- 建议根据负载类型设置合适的 PWM 频率：
  - 直流电机：1kHz ~ 20kHz
  - LED 灯光：500Hz ~ 2kHz
  - 避免频率过低导致负载运行不稳定（如电机异响）

---

### 占空比范围
- 有效占空比计数值范围为 0 至 `pwm_max`（默认 65535）
- 百分比设置范围为 0.0% 至 100.0%，超出范围会自动裁剪
- 反向模式（`inverted=True`）下，实际输出占空比为 `pwm_max - 设置值`

---

### 电源要求
- 光耦 MOS 模块的 VCC 需与开发板 IO 电平匹配（3.3V 或 5V）
- 负载电源应根据负载额定参数选择，确保电流不超过 MOS 管的最大允许电流
- 大功率负载建议添加散热片，避免 MOS 管过热损坏

---

### 资源管理
- 多个负载控制时，需使用不同的 GPIO 引脚创建独立的 PWM 实例
- 程序退出前建议调用 `deinit()` 释放 PWM 资源
- 避免在短时间内频繁切换 PWM 状态，可能导致硬件寿命缩短

---

### 信号干扰
- 长距离连接时，建议使用屏蔽线传输 PWM 信号，减少电磁干扰
- 若控制信号不稳定，可在光耦模块的 IN 引脚与 GND 之间并联 100nF 电容滤波

---

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
- **声明** —此项目代码产生任何问题与署名作者无关。   
**版权归 FreakStudio 所有。**