# SGP40/SGP41 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [实现说明](#实现说明)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本驱动为 Sensirion SGP40/SGP41 VOC/NOx 空气质量传感器提供 MicroPython 支持，基于 sensor_pack_2 框架实现。SGP40 仅输出 VOC 原始信号，SGP41 同时输出 VOC 与 NOx 原始信号，两者通过 `sensor_id` 参数统一管理。驱动支持自检、序列号读取、加热器控制及温湿度补偿测量等功能。

---

## 主要功能

- 支持 SGP40（仅 VOC）与 SGP41（VOC + NOx）双型号，通过 `sensor_id` 切换
- 读取传感器序列号（3 个 16 位字）
- 执行内置自检，返回通过/失败状态码
- SGP41 专用预热调节（conditioning），最长 10 秒
- 带温湿度补偿的原始信号测量（`measure_raw_signal`）
- 支持迭代器协议，可直接 `for` 循环采集数据
- 关闭加热器进入待机模式（`turn_heater_off` / `deinit`）
- 可选 CRC 校验，提升数据可靠性

---

## 硬件要求

**推荐硬件：**

- 任意支持 MicroPython v1.23.0 的开发板（如 ESP32、RP2040）
- SGP40 或 SGP41 传感器模块
- 连接导线若干

**引脚连接：**

| 传感器引脚 | 开发板引脚 | 说明         |
|-----------|-----------|--------------|
| SDA       | GPIO4     | I2C 数据线   |
| SCL       | GPIO5     | I2C 时钟线   |
| VCC       | 3.3V      | 电源         |
| GND       | GND       | 地           |

---

## 软件环境

| 项目             | 版本 / 说明                        |
|-----------------|------------------------------------|
| MicroPython     | v1.23.0                            |
| 驱动版本         | v1.0.0                             |
| 依赖库           | sensor_pack_2（需一并部署到设备）   |
| I2C 频率         | 100 kHz（`I2C_FREQ = 100_000`）    |
| 传感器 I2C 地址  | 0x59（固定）                       |

---

## 文件结构

```
sensors/sgp40_driver/
├── code/
│   ├── sgp4Xmod.py
│   ├── main.py
│   └── sensor_pack_2/
│       ├── __init__.py
│       ├── base_sensor.py
│       ├── bitfield.py
│       ├── bus_service.py
│       └── crc_mod.py
├── package.json
├── LICENSE
└── README.md
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/sgp4Xmod.py` | SGP40/SGP41 主驱动文件，包含 `SGP4X` 类及全部公开 API |
| `code/main.py` | 测试示例程序，演示初始化、自检、调节及循环采集 |
| `code/sensor_pack_2/__init__.py` | sensor_pack_2 框架包初始化 |
| `code/sensor_pack_2/base_sensor.py` | 传感器基类，定义 `IDentifier`、`Iterator` 等接口 |
| `code/sensor_pack_2/bitfield.py` | 位域操作工具 |
| `code/sensor_pack_2/bus_service.py` | I2C/SPI 总线适配器，提供 `I2cAdapter` |
| `code/sensor_pack_2/crc_mod.py` | CRC 校验模块 |
| `package.json` | mip 包配置文件 |
| `LICENSE` | MIT 许可证文本 |
| `README.md` | 本文档 |

---

## 快速开始

**步骤一：复制文件到设备**

将 `code/` 目录下的所有文件上传到 MicroPython 设备根目录，保持 `sensor_pack_2/` 子目录结构不变。

```
# 使用 mpremote 上传（示例）
mpremote cp code/sgp4Xmod.py :sgp4Xmod.py
mpremote cp code/main.py :main.py
mpremote cp -r code/sensor_pack_2 :sensor_pack_2
```

**步骤二：按引脚表连接硬件**

参照 [硬件要求](#硬件要求) 中的引脚表，将 SGP40/SGP41 连接到开发板。

**步骤三：运行测试程序**

```
mpremote run code/main.py
```

**示例代码（main.py）：**

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 07:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : SGP40/SGP41 空气质量传感器驱动测试
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from sgp4Xmod import SGP4X

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x59]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000
SENSOR_ID = 0          # 0=SGP40, 1=SGP41

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: SGP40/SGP41 air quality sensor test")

# ========================================  主程序  ============================================

if __name__ == '__main__':
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    devices_list = i2c_bus.scan()
    print("START I2C SCANNER")

    if not devices_list:
        raise SystemExit("I2C scan found no devices")
    print("i2c devices found:", len(devices_list))

    sensor = None
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2C address:", hex(device))
            try:
                sensor = SGP4X(I2cAdapter(i2c_bus), address=device, sensor_id=SENSOR_ID)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print("Sensor init failed:", e)

    if sensor is None:
        raise SystemExit("No target sensor found on I2C bus")

    try:
        sn = sensor.get_id()
        print("Serial number: 0x%04X 0x%04X 0x%04X" % (sn.word_0, sn.word_1, sn.word_2))

        result = sensor.execute_self_test()
        print("Self test: %s (0x%04X)" % ("PASS" if result == 0xD400 else "FAIL", result))

        if SENSOR_ID == 1:
            print("Conditioning SGP41 for 10s...")
            for _ in range(10):
                val = sensor.execute_conditioning(rel_hum=50, temperature=25)
                print("Conditioning VOC raw:", val.VOC)
                time.sleep_ms(1000)

        print("Starting measurement loop (Ctrl+C to stop)...")
        while True:
            val = sensor.measure_raw_signal(rel_hum=50, temperature=25)
            if SENSOR_ID == 1:
                print("VOC raw: %d  NOx raw: %d" % (val.VOC, val.NOx))
            else:
                print("VOC raw:", val.VOC)
            time.sleep_ms(1000)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        sensor.deinit()
        print("Sensor deinitialized")
```

---

## 注意事项

| 项目 | 说明 |
|------|------|
| 测量范围 | VOC 原始信号：0–65535；NOx 原始信号：0–65535（仅 SGP41） |
| 采样间隔 | 建议每次测量间隔 ≥ 1 秒（1 Hz），与 Sensirion 官方推荐一致 |
| SGP41 预热 | 首次上电后需执行最多 10 秒的 `execute_conditioning`，期间 NOx 输出无效 |
| 型号兼容性 | `sensor_id=0` 对应 SGP40，`sensor_id=1` 对应 SGP41；两者 I2C 地址均为 0x59 |
| NOx 字段 | SGP40 的 `measured_values_sgp4x.NOx` 始终为 `None`，请勿直接格式化输出 |
| 加热器关闭 | 不使用时调用 `deinit()` 或 `turn_heater_off()` 以降低功耗 |
| CRC 校验 | 默认启用（`check_crc=True`），如遇通信异常可尝试关闭排查 |

---

## 实现说明

**sensor_pack_2 适配器模式**

驱动不直接操作 `machine.I2C`，而是通过 `I2cAdapter`（来自 `sensor_pack_2.bus_service`）进行总线通信。`I2cAdapter` 封装了读写操作并统一了错误处理接口，使驱动与底层硬件解耦，便于在不同平台间移植。实例化时需先创建 `SoftI2C` 对象，再包装为 `I2cAdapter` 传入 `SGP4X`。

**SGP40 与 SGP41 分支逻辑**

`SGP4X` 类通过构造函数的 `sensor_id` 参数区分两种型号：

- `sensor_id=0`（SGP40）：`measure_raw_signal` 仅返回 VOC 原始值，`measured_values_sgp4x.NOx` 为 `None`；`execute_conditioning` 不适用。
- `sensor_id=1`（SGP41）：`measure_raw_signal` 同时返回 VOC 与 NOx 原始值；上电后应先调用 `execute_conditioning` 完成预热，再进入正常测量循环。

在 `main.py` 中通过 `if SENSOR_ID == 1` 分支分别处理两种型号的输出格式，避免对 `None` 值执行格式化操作导致运行时错误。

---

## 版本记录

| 版本   | 日期       | 作者          | 说明     |
|--------|------------|---------------|----------|
| v1.0.0 | 2026-05-07 | Roman Shevchik | 初始版本 |

---

## 联系方式

- Email: goctaprog@gmail.com
- GitHub: [https://github.com/your-github-username](https://github.com/your-github-username)

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
