# GraftSense 红外收发模块驱动（MicroPython）

# GraftSense 红外收发模块驱动驱动（MicroPython）

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

本项目为 **GraftSense IR Receiver v1.1（基于 TSOP34138 的红外接收模块）** 提供了完整的 MicroPython 驱动支持，支持红外信号的接收解码与发射，兼容 NEC 协议（包括 NEC_8、NEC_16 及三星变体），并提供协议嗅探与回放功能。驱动采用分层设计，在树莓派 Pico 等 RP2 平台上通过 PIO 实现高性能红外发射，适用于红外遥控实验、智能家居控制演示、电子 DIY 无线控制等场景，为非接触式红外交互提供可靠的信号处理能力。

---

## 主要功能

- ✅ 支持 NEC 协议解码:包含 NEC_8（8 位地址）、NEC_16（16 位地址）及三星 NEC 变体
- ✅ 支持红外信号发射:通过 PWM/PIO 生成 38kHz 载波，发送 NEC 协议指令
- ✅ 提供协议嗅探与回放:捕获原始红外脉冲序列，支持协议识别与数据存储
- ✅ RP2 平台专属优化:使用 PIO 状态机实现高精度脉冲发射，降低 CPU 占用
- ✅ 回调机制解耦:接收信号后自动触发用户回调，支持地址、命令及重复码解析
- ✅ 完善的错误处理:定义多种异常码（如 REPEAT、BADSTART 等），便于调试
- ✅ 遵循 Grove 接口标准，兼容主流开发板与传感器生态

---

## 硬件要求

1. **核心硬件**:GraftSense IR Receiver v1.1 红外接收模块（基于 TSOP34138 芯片，支持 38kHz 载波解调）
2. **主控设备**:支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等，RP2 平台支持 PIO 发射优化）
3. **接线配件**:Grove 4Pin 线（用于连接模块的 DIN、GND、VCC 引脚与开发板）
4. **电源**:3.3V~5V 稳定电源（模块兼容 3.3V 和 5V 供电，内置滤波电路）

---

## 文件说明

---

## 软件设计核心思想

1. **分层架构**:将发射（`ir_tx`）与接收（`ir_rx`）功能分离，降低模块耦合，便于扩展其他协议
2. **协议抽象**:通过 `NEC_ABC` 基类封装 NEC 协议核心逻辑，子类实现不同地址模式（8 位 / 16 位）与三星变体
3. **硬件加速**:RP2 平台使用 PIO 状态机实现红外发射，将脉冲生成卸载到硬件，提升实时性与 CPU 利用率
4. **回调驱动**:接收解码完成后通过回调函数通知用户，解耦硬件检测与业务逻辑
5. **可移植性**:核心协议逻辑依赖标准 MicroPython 接口，PIO 驱动仅作为平台专属优化，不影响核心功能移植
6. **错误码设计**:定义统一的异常码体系，便于快速定位协议解析或硬件通信问题

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `ir_tx`、`ir_rx` 目录及 `main.py` 上传至开发板文件系统

### 硬件连接

- **接收模块**:使用 Grove 线将模块的 `DIN` 引脚连接至开发板指定 GPIO 引脚（如示例中的 GPIO 14），连接 `GND` 和 `VCC` 引脚
- **发射模块**:将红外发射管连接至开发板指定 GPIO 引脚（如示例中的 GPIO 6），确保供电稳定
- **注意**:RP2 平台使用 PIO 发射时，需确保引脚与状态机配置匹配

### 代码配置

- 在 `main.py` 中修改 `TX_PIN` 和 `RX_PIN` 为实际连接的 GPIO 引脚号
- 如需切换协议，可替换 `NEC_16` 为 `NEC_8` 或 `SAMSUNG`，并调整回调函数参数

### 运行测试

- 重启开发板，`main.py` 将自动执行，循环发送 NEC 信号并实时打印接收到的地址、命令及重复码信息

---

## 示例程序

### NEC 协议收发测试（main.py）

```python
import time
from machine import Pin
from ir_tx.nec import NEC
from ir_rx.nec import NEC_16

def ir_callback(addr: int, cmd: int, repeat: bool) -> None:
    print(f"[RX] Address=0x{addr:04X}, Cmd=0x{cmd:02X}, Repeat={repeat}")

time.sleep(3)
print("FreakStudio:Infrared transceiver test")

TX_PIN = Pin(6, Pin.OUT)
RX_PIN = Pin(14, Pin.IN)

ir_tx = NEC(TX_PIN, freq=38000)
ir_rx = NEC_16(RX_PIN, ir_callback)

print("[System] Ready... TX=GP6, RX=GP14")

while True:
    print("[TX] Sending NEC signal...")
    ir_tx.transmit(0x10, 0x20)
    time.sleep(2)
```

---

## 注意事项

1. **载波频率**:模块默认支持 38kHz 载波，发射时需设置 `freq=38000`，避免与其他设备干扰
2. **电平兼容**:模块输出低电平有效（无有效信号时为高电平），需确保主控 GPIO 输入模式配置正确
3. **平台限制**:`rp2_rmt.py` 仅支持 RP2 平台（如树莓派 Pico），其他平台需使用通用 PWM 发射实现
4. **回调函数**:回调函数应保持简洁，避免执行耗时操作，确保不阻塞中断处理
5. **环境干扰**:强光环境可能影响红外接收灵敏度，建议在室内或弱光环境下使用
6. **重复码处理**:NEC 协议支持长按重复码，回调函数中通过 `repeat` 参数区分首次触发与长按重复

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:

📧 **邮箱**:liqinghsui@freakstudio.cn

💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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