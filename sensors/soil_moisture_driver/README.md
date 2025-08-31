# 电容式土壤湿度传感器驱动 - MicroPython版本

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
电容式土壤湿度传感器是一种通过检测土壤介电常数变化来测量湿度的设备，具有耐腐蚀、响应速度快、测量稳定等特点。相比传统电阻式传感器，它能有效避免电解腐蚀问题，延长使用寿命。

本项目提供了基于 MicroPython 的驱动代码及示例程序，支持原始数据读取、干湿校准和湿度等级判断，方便开发者快速集成到智能农业、盆栽监测、自动灌溉等场景。

---

## 主要功能
- **核心功能**：
  - 读取 ADC 原始数值
  - 支持干湿状态校准（空气/水中环境）
  - 计算相对湿度百分比（0~100%）
  - 湿度等级判断（干燥/湿润/潮湿）
- **便捷特性**：
  - 提供属性访问接口（raw/moisture/level）
  - 校准参数手动设置与获取
  - 校准状态检查
- **跨平台支持**：兼容多种 MicroPython 开发板（树莓派 Pico 等）

---

## 硬件要求
### 推荐测试硬件
- 树莓派 Pico/Pico W
- 电容式土壤湿度传感器（如 ESP32-SOIL-MOISTURE 等）
- 杜邦线若干

### 模块引脚说明
| 传感器引脚 | 功能描述 |
|------------|----------|
| VCC        | 电源正极（3.3V） |
| GND        | 电源负极 |
| OUT        | 模拟输出引脚（连接到 ADC 引脚） |

---
## 文件说明
### soil_moisture.py
实现了电容式土壤湿度传感器的驱动功能，核心类 `SoilMoistureSensor` 提供完整控制接口。

#### 类定义：`SoilMoistureSensor`
- **`__init__(pin: int)`**：初始化土壤湿度传感器，参数为传感器接入的 ADC 引脚编号。
- **`read_raw() -> int`**：读取 ADC 原始数值，返回值范围取决于 ADC 分辨率（Pico 上为 0~65535）。
- **`calibrate_dry() -> int`**：校准干燥参考值，需将传感器置于空气中，返回干燥状态下的原始 ADC 数值。
- **`calibrate_wet() -> int`**：校准湿润参考值，需将传感器浸入水中，返回湿润状态下的原始 ADC 数值。
- **`set_calibration(dry: int, wet: int) -> None`**：手动设置干湿校准值，允许导入外部记录的校准参数。
- **`get_calibration() -> tuple`**：获取当前校准参数，返回 (dry, wet) 元组，未校准则返回 (None, None)。
- **`read_moisture() -> float`**：返回相对湿度百分比（0~100），基于线性插值计算，未校准会抛出 ValueError。
- **`get_level() -> str`**：返回湿度等级（"dry" / "moist" / "wet"），其中 dry <30%，moist 30~70%，wet >70%。
- **`is_calibrated (property)`**：属性，返回布尔值表示是否已完成干湿校准。
- **`raw (property)`**：属性，获取 ADC 原始值。
- **`moisture (property)`**：属性，获取相对湿度百分比。
- **`level (property)`**：属性，获取湿度等级。

### main.py
示例测试程序，演示传感器初始化、校准、数据读取等完整功能，包含传感器初始化、原始值读取、校准操作、湿度计算和等级判断等测试步骤。

---

## 软件设计核心思想
### 模块化设计
- 将传感器操作封装为独立类，职责单一
- 分离原始数据获取与数据处理逻辑
- 提供统一接口，简化集成难度

### 校准机制
- 基于干湿两点校准实现相对湿度计算
- 支持手动设置校准参数，适应不同环境
- 校准状态检查，避免无效数据输出

### 数据处理
- 采用线性插值算法将 ADC 值转换为百分比
- 湿度等级划分（干燥<30%、湿润30%~70%、潮湿>70%）
- 边界值处理，确保输出在有效范围内

### 易用性设计
- 提供属性访问方式，简化代码编写
- 完善的异常处理，提高鲁棒性
- 清晰的文档注释，降低使用门槛

---

## 使用说明
### 硬件接线（树莓派 Pico 示例）

| 传感器引脚 | Pico GPIO 引脚 |
|------------|----------------|
| VCC        | 3.3V           |
| GND        | GND            |
| OUT        | GP26 (ADC0)    |

> **注意：**
> - 务必使用 3.3V 电源，避免损坏传感器
> - 确保接线牢固，接触良好
> - 传感器探针部分应完全插入土壤中进行测量

---

### 软件依赖

- **固件版本**：MicroPython v1.23+  
- **内置库**：
  - `machine`（用于 ADC 控制）
  - `time`（用于延时）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 将 **MicroPython 固件** 烧录到树莓派 Pico  
2. 上传 `soil_moisture.py` 和 `main.py` 到 Pico  
3. 根据硬件连接修改 `main.py` 中的引脚配置（默认使用 GP26）  
4. 在开发工具中运行 `main.py`，开始测试

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 下午12:49
# @Author  : 缪贵成
# @File    : main.py
# @Description : 电容式土壤湿度传感器测试文件

# ======================================== 导入相关模块 =========================================

import time
from soil_moisture import SoilMoistureSensor

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: SoilMoistureSensor Test Start")
print(">>> Please prepare the sensor for calibration (dry and wet)...")

# 初始化传感器 (例：ADC 引脚 26)
sensor = SoilMoistureSensor(pin=26)
print("Sensor initialized on ADC pin 26")

# ======================================== 主程序 ===============================================

# Step 1: 校准干燥值
input(">>> Place sensor in DRY air/soil and press Enter...")
dry_value = sensor.calibrate_dry()
print("Calibrated dry value:", dry_value)

# Step 2: 校准湿润值
input(">>> Place sensor in WATER (fully wet) and press Enter...")
wet_value = sensor.calibrate_wet()
print("Calibrated wet value:", wet_value)

# Step 3: 设置校准值
sensor.set_calibration(dry_value, wet_value)
print("Calibration set: dry={}, wet={}".format(dry_value, wet_value))

# Step 4: 循环读取传感器数据
print("\n>>> Calibration completed. Start reading moisture...\n")
try:
    while True:
        raw = sensor.read_raw()
        moisture_percent = sensor.read_moisture()
        level = sensor.get_level()

        print(
            "Raw ADC: {:>5} | Moisture: {:>5.1f}% | Level: {}".format(
                raw, moisture_percent, level
            )
        )
        time.sleep(2)

except KeyboardInterrupt:
    print("\nTest stopped by user.")

print("SoilMoistureSensor Test Completed")
```
---
## 注意事项

### 校准注意事项
- **干燥校准**：将传感器置于空气中（无水分环境）
- **湿润校准**：将传感器探针完全浸入水中
- 建议每种土壤类型重新校准，提高测量准确性
- 校准后可通过 `set_calibration()` 保存参数，避免重复校准

---

### 测量建议
- 传感器探针应插入土壤 2-3 厘米深度
- 避免探针接触肥料或高盐分土壤
- 测量前确保土壤与探针充分接触
- 同一位置多次测量取平均值，提高稳定性

---

### 硬件维护
- 长期使用后应清洁探针，避免盐分积累
- 避免剧烈震动或冲击传感器
- 存储时保持探针干燥，防止腐蚀

---

### 环境影响
- 温度变化可能影响测量精度
- 土壤质地（沙质/黏土）会导致读数差异
- 高湿度环境下应缩短测量间隔

## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/leezisheng](https://github.com/leezisheng)  

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