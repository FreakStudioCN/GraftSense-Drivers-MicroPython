# GraftSense-基于 PCF8574 的 8 位 IO 扩展模块驱动（MicroPython）

# GraftSense-基于 PCF8574 的 8 位 IO 扩展模块驱动（MicroPython）

基于 **PCF8574** 的 8 位 IO 扩展模块驱动，专为 MicroPython 环境设计，支持端口级（2 位）和单引脚操作，适用于嵌入式项目的 IO 扩展需求。

---

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

本项目提供了 FreakStudio GraftSense 8-bit I/O Port Expansion Module V1.2 的 MicroPython 驱动，基于 **PCF8574** 芯片实现。通过 I2C 总线扩展 8 个准双向 IO 口，支持端口级（PORT0-PORT3，每端口 2 位）和单引脚（P0-P7）的输入输出控制，适用于多按键检测、LED 控制、嵌入式 DIY 扩展等场景。

- 模块提供 4 个 Grove 接口（PORT0-PORT3），对应 P0-P7 引脚。
- 支持 I2C 地址配置（0x20-0x27），可通过硬件跳线设置。
- 驱动采用分层设计，底层直接操作硬件，上层提供端口级抽象，提升易用性。

---

## 主要功能

### 底层驱动（`pcf8574.py`）

- 完整的 PCF8574 芯片控制：端口读写、单引脚设置 / 读取、引脚翻转。
- 支持外部中断触发：通过 INT 引脚检测端口状态变化，回调函数通过 `micropython.schedule` 调度执行。
- 设备存在性检查：通过 I2C 扫描确认芯片连接。

### 上层封装（`pcf8574_io8.py`）

- 端口级操作：支持 PORT0-PORT3（每端口 2 位）的配置、设置和读取。
- 缓存管理：内部缓存 8 位寄存器值，减少 I2C 操作次数，提升效率。
- 状态恢复：读取操作临时将引脚置为高阻态，读取后自动恢复默认状态。
- 单引脚控制：支持独立设置 / 读取任意引脚（P0-P7）。

---

## 硬件要求

- **核心芯片**：PCF8574（或 FreakStudio GraftSense 8-bit I/O Port Expansion Module V1.2）。
- **主控设备**：支持 MicroPython 的嵌入式平台（如 Raspberry Pi Pico、ESP32 等）。
- **通信接口**：I2C 总线（SCL/SDA 引脚），频率建议 100kHz。
- **可选组件**：

  - 中断引脚（INT）：用于检测端口状态变化。
  - 外部三极管 / MOSFET：驱动继电器、电机等大电流设备（PCF8574 驱动能力有限）。

---

## 文件说明

表格

---

## 软件设计核心思想

1. **分层架构**：

   - 底层驱动（`pcf8574.py`）专注于硬件交互，封装 I2C 读写和中断处理。
   - 上层封装（`pcf8574_io8.py`）提供更易用的端口级抽象，隐藏硬件细节，降低使用门槛。
2. **缓存优化**：

   - 内部缓存 8 位寄存器值，写操作先更新缓存再同步到硬件，减少 I2C 通信次数。
   - 读操作临时修改缓存以获取真实输入，读取后自动恢复，避免影响后续输出。
3. **中断安全**：

   - 中断回调通过 `micropython.schedule` 调度，避免在 ISR 中执行耗时操作，提升系统稳定性。
4. **状态管理**：

   - 支持端口默认状态配置，读取操作后自动恢复，确保 IO 行为可预测。

---

## 使用说明

### 1. 环境准备

- 安装 MicroPython 固件到目标设备（如 Raspberry Pi Pico）。
- 将 `pcf8574.py` 和 `pcf8574_io8.py` 复制到设备的文件系统。

### 2. 初始化步骤

```
from machine import I2C, Pin
from pcf8574 import PCF8574
from pcf8574_io8 import PCF8574IO8

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 扫描 I2C 设备，获取 PCF8574 地址（0x20-0x27）
devices = i2c.scan()
pcf_addr = next((d for d in devices if 0x20 <= d <= 0x27), None)

if not pcf_addr:
    raise OSError("PCF8574 not found on I2C bus")

# 初始化底层驱动
pcf = PCF8574(i2c, pcf_addr)

# 初始化上层端口封装，配置默认端口状态
ports_init = {0: (1, 1), 1: (1, 1), 2: (1, 1), 3: (1, 1)}  # 所有端口默认高阻态
io8 = PCF8574IO8(pcf, ports_init=ports_init)
```

### 3. 核心操作示例

- **设置端口输出**：

```
io8.set_port(1, 2)  # 设置 PORT1 为 2（二进制 10，对应 P3=1, P2=0）
```

- **读取端口输入**：

```
port0_state = io8.get_port(0)  # 读取 PORT0 状态（0-3）
```

- **单引脚控制**：

```
io8.set_pin(0, 0)  # 设置 P0 为低电平
pin0_state = io8.get_pin(0)  # 读取 P0 电平（0/1）
```

---

## 示例程序

以下为 `main.py` 中的测试逻辑，演示按键检测和端口控制：

```
import time
from machine import I2C, Pin
from pcf8574 import PCF8574
from pcf8574_io8 import PCF8574IO8

# 初始化 I2C
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 扫描并检测 PCF8574
devices = i2c.scan()
pcf_addr = next((d for d in devices if 0x20 <= d <= 0x27), None)
if not pcf_addr:
    raise OSError("PCF8574 not found")

# 初始化驱动
pcf = PCF8574(i2c, pcf_addr)
io8 = PCF8574IO8(pcf, ports_init={0: (1,1), 1: (1,1), 2: (1,1), 3: (1,1)})

# 测试端口闪烁
io8.set_port(1, 0)
time.sleep(1)
io8.set_port(1, 2)
time.sleep(1)

# 按键检测循环
while True:
    if not io8.get_pin(0):  # 检测 P0 低电平（按键触发）
        io8.set_port(1, 2)
        print("Button triggered, set PORT1 to 2")
    else:
        io8.set_port(1, 0)
    time.sleep(0.1)
```

---

## 注意事项

1. **准双向 IO 特性**：

   - PCF8574 输出为准双向（开漏 / 高阻），写 `1` 表示高阻态，而非强高电平。
   - 驱动大电流设备（如继电器、电机）时，必须外接三极管或 MOSFET 增强驱动能力。
2. **中断安全**：

   - 所有 I2C 操作均非 ISR-safe，不可在中断服务函数中直接调用。
   - 中断回调需通过 `micropython.schedule` 调度，避免阻塞系统。
3. **地址范围**：

   - PCF8574 的 I2C 地址范围为 `0x20-0x27`，可通过硬件跳线（A0/A1/A2）配置。
4. **状态恢复**：

   - 读取操作会临时将引脚置为高阻态，读取后自动恢复默认状态，确保输出行为一致。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议
