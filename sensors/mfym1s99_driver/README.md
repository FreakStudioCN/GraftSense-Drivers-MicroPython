# MFYM-1S-9-9 单点柔性压力传感器 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [设计思路](#设计思路)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本驱动用于在 MicroPython 中读取敏源 MFYM-1S-9-9 单点柔性压力传感器。模组通过 115200 baud UART 主动输出 `S/R/C0/C3/T` ASCII 数据，驱动负责流式接收、空白帧过滤、字段解析、温度换算、稳健空载置零和压力换算。

## 主要功能

- 支持 MFYM-1S-9-9 实测 ASCII 帧格式。
- 自动忽略有效帧之间的空格数据。
- UART 缓冲区清空带时间上限，避免连续数据导致阻塞。
- 先丢弃启动帧，再使用中位数执行空载置零。
- 置零过程包含数据稳定性检查。
- 支持标称灵敏度换算和安装后的两点线性标定。
- UART 实例由应用注入，便于复用硬件资源和模拟测试。

## 硬件要求

推荐测试硬件：

- Raspberry Pi Pico 或其他支持 MicroPython UART 的开发板。
- MFYM-1S-9-9 单点柔性压力传感器。
- 4 根连接线。

Raspberry Pi Pico 接线：

| Raspberry Pi Pico | MFYM-1S-9-9 | 功能描述 |
|---|---|---|
| 3V3(OUT) | VCC | 推荐先使用 3.3 V 供电 |
| GND | GND | 电源地，两端必须共地 |
| GP16 / UART0 TX | RXD | Pico 向模组发送数据 |
| GP17 / UART0 RX | TXD | Pico 接收模组数据 |

TX 和 RX 必须交叉连接。

## 软件环境

| 项目 | 版本或说明 |
|---|---|
| MicroPython | v1.23.0 或兼容版本 |
| 驱动版本 | v1.0.0 |
| UART 参数 | 115200 baud、8N1 |
| 第三方依赖 | 无 |

## 文件结构

```text
mfym1s99_driver/
├── code/
│   ├── mfym1s99.py
│   └── main.py
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|---|---|
| `code/mfym1s99.py` | 核心 UART 驱动、协议解析和标定逻辑 |
| `code/main.py` | Raspberry Pi Pico GP16/GP17 完整测试示例 |
| `package.json` | GraftSense/mip 包文件映射和元数据 |
| `README.md` | 接线、API 使用和注意事项 |
| `LICENSE` | MIT 许可证文本 |

## 设计思路

模组会主动输出如下数据：

```text
S:1045 pF,R:2000 pF,C0:1020 pF,C3:987 pF;T:2765 C
```

字段含义：

| 字段 | 说明 |
|---|---|
| `S` | 压力敏感通道，默认用于压力换算 |
| `R` | 参考值 |
| `C0`、`C3` | 补偿/参考通道 |
| `T` | 温度的 100 倍，例如 2765 表示 27.65°C |

默认标称换算公式为：

```text
P = polarity × (S / S_zero - 1) / sensitivity
```

产品简介给出的标称灵敏度为 `0.36 kPa^-1`。机械结构、接触面积和安装预紧力会影响实际结果，因此精准计量应使用已知压力执行两点标定。

## 快速开始

1. 将 `code/mfym1s99.py` 和 `code/main.py` 上传到 MicroPython 设备根目录。
2. 按硬件要求表连接传感器。
3. 保持敏感区域完全空载并重启设备。
4. 等待程序完成空载置零，然后观察实时输出。

最小示例：

```python
from machine import Pin, UART
from mfym1s99 import MFYM1S99

uart = UART(
    0,
    baudrate=115200,
    tx=Pin(16),
    rx=Pin(17),
    bits=8,
    parity=None,
    stop=1,
)
sensor = MFYM1S99(uart)
sensor.clear()
print("Zero raw:", sensor.zero(samples=7, discard=5))

while True:
    sample = sensor.read_sample()
    if sample is not None:
        raw = sensor.sample_value(sample)
        print(sensor.pressure_from_raw(raw), "kPa")
```

两点标定示例：

```python
sensor.set_two_point_calibration(
    raw1=1049.0,
    pressure1_kpa=0.0,
    raw2=3095.0,          # 替换为施加已知压力时的原始值
    pressure2_kpa=5.0,   # 替换为标准压力值
)
```

## 注意事项

| 分类 | 注意事项 |
|---|---|
| 通信 | 当前实测固件是主动 UART ASCII 数据流，不是 Modbus RTU，不需要 `umodbus`。 |
| 置零 | 启动提示出现后不要触碰敏感区域，错误零点会直接影响压力结果。 |
| 标定 | 标称灵敏度结果只适合快速验证，精准测量必须在最终机械安装状态下标定。 |
| 安装 | 受力点应尽量位于背部丝印敏感区域中心，避免尖锐物体和偏载。 |
| 温度 | 驱动将 `T` 字段除以 100；若厂家更换固件格式，应重新核对比例。 |
| 资源 | 调用 `sensor.deinit()` 只释放驱动引用；UART 由调用方负责 `deinit()`。 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| v1.0.0 | 2026-08-21 | December | 初始规范版本，支持实测 UART 协议、稳健置零和两点标定 |

## 联系方式

- GitHub：[Gypsyold](https://github.com/Gypsyold)
- Email：149050476+Gypsyold@users.noreply.github.com

## 许可协议

本项目采用 MIT License：

```text
MIT License

Copyright (c) 2026 December

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
