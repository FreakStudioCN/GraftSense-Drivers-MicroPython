# TSic 506F 温度传感器 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本目录提供 TSic 506F 高精度温度传感器的 MicroPython 驱动。驱动基于 RP2040 PIO 实现 `ZACwire` 单线时序解码，读取 11 位温度数据，并使用中值滤波平滑输出，适合需要稳定温度采样、低主循环占用的嵌入式场景。

## 主要功能

1. 基于 RP2040 PIO 双状态机完成脉冲宽度采集和帧起始长脉冲检测；
2. 实现 `ZACwire` 11 位温度数据解码；
3. 支持中值滤波窗口配置；
4. 通过 `micropython.schedule` 将解码移到主上下文，并合并待处理帧以避免调度队列溢出；
5. IRQ 采集缓冲区具有固定上界，异常脉冲导致的非完整帧会在下一帧边界被安全丢弃；
6. 提供 `start()`、`stop()`、`deinit()` 完整的资源生命周期管理。

## 硬件要求

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V-5V） |
| GND  | 电源负极 |
| DATA | ZACwire 数据引脚，接 RP2040 GPIO |

推荐测试硬件：

- Raspberry Pi Pico / 其他 RP2040 开发板；
- TSic 506F 温度传感器模块；
- 杜邦线若干。

## 软件环境

| 项目 | 要求 |
|------|------|
| 固件 | MicroPython v1.23+，需包含 `rp2`/PIO 支持 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖 |

## 文件结构

```text
TSic_506F/
├── LICENSE
├── README.md
├── package.json
└── code/
    ├── tsic506.py
    └── main.py
```

## 文件说明

| 文件名 | 功能说明 |
|--------|----------|
| `code/tsic506.py` | TSIC 506F 核心驱动，包含 PIO 程序、解码逻辑和温度读取 |
| `code/main.py` | 测试示例，演示引脚初始化、驱动实例化和周期读取温度 |
| `package.json` | mip/upypi 包配置文件 |
| `LICENSE` | MIT 许可证文件 |

## 快速开始

1. 将 `code/tsic506.py` 和 `code/main.py` 上传到 MicroPython 设备；
2. 按硬件要求连接 TSic 506F 的 VCC、GND 和 DATA 引脚；
3. 运行 `main.py`，或使用以下最小示例：

```python
import time
from machine import Pin
from tsic506 import TSIC506F

time.sleep(3)
data_pin = Pin(6, Pin.OUT, value=0)
time.sleep_ms(10)
data_pin.init(Pin.IN)

sensor = TSIC506F(pin=data_pin, sm=(0, 1), start=True)

while True:
    try:
        print("TSic506F temperature: %.2f C" % sensor.T())
    except Exception as error:
        print("Read error: %s" % str(error))
    time.sleep_ms(500)
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 平台限制 | 驱动依赖 RP2040 PIO，不适用于无 `rp2` 模块的固件 |
| 状态机资源 | 默认占用状态机 0 和 1，避免与项目中的其他 PIO 程序冲突 |
| 首帧等待 | 驱动默认丢弃上电后的第 1 个有效帧（`startup_frames=1`），且首帧解码完成前 `T()` 会抛出 `TSIC506FNotRunning`，需在循环中捕获重试 |
| 引脚配置 | 上电后建议先下拉数据引脚再切换为输入，降低首次启动抖动 |
| 供电 | 确保传感器供电稳定，避免数据线上引入明显噪声 |
| 帧丢弃计数 | `dropped_frames` 记录因缓冲区溢出、非完整帧或调度背压而丢弃的帧。该值持续增加时，应降低主循环负载或检查数据线信号质量 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-09-07 | Robert Hammelrath | 初始版本 |

## 联系方式

如有问题，请通过以下方式联系：

- 作者：Robert Hammelrath
- GitHub：<https://github.com/robert-hh>

## 许可协议

本包采用 MIT 许可证，完整许可证及版权归属见同包 [LICENSE](LICENSE)。
