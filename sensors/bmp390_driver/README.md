# BMP390 Driver for MicroPython

# BMP390 Driver for MicroPython

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

本项目是 **BMP390 气压 / 温度传感器** 的 MicroPython 驱动库，专为在 MicroPython 环境下控制 BMP390 传感器设计，可便捷获取高精度气压与温度数据，适用于环境监测、气象站、高度计等各类嵌入式项目。

## 主要功能

- 支持 BMP390 传感器的 I2C 通信初始化
- 提供温度数据读取接口（单位：℃）
- 提供气压数据读取接口（单位：Pa）
- 内置传感器数据校准逻辑，保障测量精度
- 轻量封装，无特定固件依赖，兼容多种 MicroPython 芯片
- 模块化设计，易于集成到现有项目

## 硬件要求

- **传感器模块**：BMP390 气压 / 温度传感器模块
- **开发板**：支持 MicroPython 且具备 I2C 接口的开发板（如 ESP32、ESP8266、Raspberry Pi Pico 等）
- **连接线**：杜邦线若干，用于连接传感器与开发板的 I2C 引脚（SDA、SCL）
- **供电**：3.3V 直流电源（请勿直接使用 5V 供电，避免损坏传感器）

## 文件说明

## 软件设计核心思想

1. **模块化封装**：将 BMP390 传感器的所有操作封装为独立类，对外提供简洁易用的 API，隐藏底层硬件通信细节。
2. **轻量高效**：遵循 MicroPython 资源受限的特点，精简代码逻辑，减少内存与算力占用，适配嵌入式设备运行环境。
3. **兼容性优先**：通过 `package.json` 声明无芯片、无固件依赖，确保可在所有支持 MicroPython 的平台上运行。
4. **可扩展性**：预留接口便于后续添加 SPI 通信、 oversampling 配置等高级功能。

## 使用说明

1. **文件上传**：将 `code/bmp390.py` 文件上传至 MicroPython 开发板的文件系统（可通过 Thonny、mpremote 等工具完成）。
2. **模块导入**：在你的主程序中通过 `import bmp390` 导入驱动模块。
3. **I2C 初始化**：根据开发板引脚定义，初始化 I2C 总线（需指定 SDA、SCL 引脚）。
4. **传感器实例化**：创建 BMP390 类实例，传入已初始化的 I2C 对象及传感器 I2C 地址。
5. **数据读取**：调用类方法读取温度、气压数据。

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : octaprog7
# @File    : main.py
# @Description : BMP390 压力传感器测试程序

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
import bmp390
import time
from bmp390 import I2cAdapter

# ======================================== 全局变量 ============================================
# 关键修改：定义I2C配置常量（对齐示例风格）
I2C_SCL_PIN = 5  # SCL引脚（针对Raspberry Pi Pico）
I2C_SDA_PIN = 4  # SDA引脚（针对Raspberry Pi Pico）
I2C_FREQ = 400_000  # I2C通信频率
TARGET_SENSOR_ADDR = 0x77  # BMP390默认I2C地址（可选0x76，根据硬件接线调整）


# ======================================== 功能函数 ============================================
def pa_mmhg(value: float) -> float:
    """
    将大气压力从帕斯卡转换为毫米汞柱。
    Args:
        value: 压力值，单位帕斯卡

    Returns:
        转换后的压力值，单位毫米汞柱

    Notes:
        转换系数为 7.50062e-3

    ==========================================
    Convert air pressure from Pascal to mm Hg.
    Args:
        value: pressure in Pascal

    Returns:
        pressure in mm Hg

    Notes:
        conversion factor is 7.50062e-3
    """
    return 7.50062e-3 * value


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: BMP390 sensor test starting...")

# 关键修改：按示例风格初始化I2C总线 + 扫描I2C设备
# 1. 初始化I2C总线（严格对齐示例代码风格）
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 2. 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 3. 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 4. 遍历地址列表初始化目标传感器（匹配示例逻辑）
ps = None  # 传感器对象初始化
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化I2C适配器和BMP390传感器
            adaptor = I2cAdapter(i2c_bus)
            ps = bmp390.Bmp390(adaptor)
            print("Target sensor (BMP390) initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 遍历完未找到目标地址时抛出异常
    raise Exception(f"No BMP390 found (target address: {hex(TARGET_SENSOR_ADDR)}, found addresses: {[hex(d) for d in devices_list]})")

# 原代码逻辑：传感器初始化后的配置（完全保留）
# 读取传感器 ID
res = ps.get_id()
print(f"chip_id: {res}")
# 软件复位传感器，确保进入已知状态
ps.soft_reset()
print(f"pwr mode: {ps.get_power_mode()}")

# 读取校准系数
calibration_data = [ps.get_calibration_coefficient(index) for index in range(14)]
print(f"Calibration data: {calibration_data}")

# 获取事件、中断状态和 FIFO 长度
print(f"Event: {ps.get_event()}; Int status: {ps.get_int_status()}; FIFO length: {ps.get_fifo_length()}")

# 设置延时函数别名
delay_func = time.sleep_ms

# 配置传感器参数
ps.set_oversampling(pressure_oversampling=2, temperature_oversampling=3)
ps.set_sampling_period(5)
ps.set_iir_filter(2)

# ========================================  主程序  ============================================
print("Single-shot measurement mode on demand!")
print(f"pwr mode: {ps.get_power_mode()}")
print(f"conversion time in [us]: {ps.get_conversion_cycle_time()}")
for _ in range(20):
    # 启动单次测量模式
    ps.start_measurement(enable_press=True, enable_temp=True, mode=1)
    delay_func(300)
    # 读取数据就绪状态
    temperature_ready, pressure_ready, cmd_ready = ps.get_data_status()
    if cmd_ready and pressure_ready:
        t, p = ps.get_temperature(), ps.get_pressure()
        pm = ps.get_power_mode()
        print(f"Temperature: {t} \xB0C; pressure: {p} Pa ({pa_mmhg(p)} mm Hg); pwr_mode: {pm} ")
    else:
        print(f"Data ready: temp {temperature_ready}, press {pressure_ready}")

print("Continuous periodic measurement mode!")
# 启动连续测量模式
ps.start_measurement(enable_press=True, enable_temp=True, mode=2)
print(f"pwr mode: {ps.get_power_mode()}")
for values in ps:
    delay_func(300)
    d_status = ps.get_data_status()
    if d_status.cmd_decoder_ready and d_status.press_ready:
        t, p, tme = values.T, values.P, ps.get_sensor_time()
        pm = ps.get_power_mode()
        print(f"Temperature: {t} \xB0C; pressure: {p} Pa ({pa_mmhg(p)} mm Hg); pwr_mode: {pm}")
    else:
        print(f"Data ready: temp {d_status.temp_ready}, press {d_status.press_ready}")

```

## 注意事项

1. **I2C 地址确认**：BMP390 的 I2C 地址由硬件引脚决定，常见地址为 `0x76`（SDO 接 GND）或 `0x77`（SDO 接 VCC），请根据实际接线确认并修改代码中 `address` 参数。
2. **供电安全**：BMP390 传感器额定供电电压为 1.71V–3.6V，**严禁使用 5V 直接供电**，否则会导致传感器永久损坏。
3. **数据读取间隔**：建议数据读取间隔不小于 10ms，避免频繁读取导致传感器内部状态异常。
4. **静电防护**：焊接或接线时请做好静电防护，避免静电击穿传感器芯片。
5. **精度校准**：首次使用或环境变化较大时，建议进行传感器校准，以提升测量精度。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
