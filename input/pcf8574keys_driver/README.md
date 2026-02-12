# GraftSense 基于 PCF8574 的五向按键模块 （MicroPython）

# GraftSense 基于 PCF8574 的五向按键模块 （MicroPython）

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

## 简介

本项目为 **GraftSense PCF8574-based 5-Way Button Module V1.0** 提供了完整的 MicroPython 驱动支持，基于 PCF8574 I/O 扩展芯片实现五向按键（上、下、左、右、中心）与两路轻触开关（SW1/SW2）的集中管理，支持定时器消抖、状态回调与 LED 控制，适用于电子 DIY 实验、机器人方向控制、嵌入式界面交互等场景。模块通过 A0/A1/A2 跳线支持 8 种 I2C 地址（0x20–0x27），具备节省主控 I/O 接口、响应灵敏、多按键集中管理的优势。

---

## 主要功能

- ✅ **五向按键 + 双开关输入**：支持上、下、左、右、中心五向按键及 SW1/SW2 轻触开关的状态读取
- ✅ **定时器消抖**：内置 10ms 定时器扫描 + 20ms 消抖逻辑，消除按键机械抖动干扰
- ✅ **状态回调机制**：按键状态变化时触发自定义回调函数，支持实时交互响应
- ✅ **LED 控制**：通过 SW1 开启模块 LED、SW2 关闭 LED，提供直观状态反馈
- ✅ **I2C 地址可配置**：通过 A0/A1/A2 跳线设置 8 种 I2C 地址（0x20–0x27），适配多设备级联
- ✅ **中断支持（可选）**：支持 INT 引脚触发中断，结合回调实现低功耗状态检测
- ✅ **状态缓存管理**：缓存按键状态，避免频繁 I2C 读取，提升响应效率

---

## 硬件要求

1. **核心硬件**：GraftSense PCF8574-based 5-Way Button Module V1.0（内置 PCF8574 芯片、五向按键、SW1/SW2 开关、LED 指示灯）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等）
3. **接线配置**：
4. 表格
5. **地址设置**：通过模块背面 A0/A1/A2 跳线设置 I2C 地址：

   - A0/A1/A2 全下拉 → 地址 0x20
   - A0/A1/A2 全上拉 → 地址 0x27
   - 其余组合对应 0x21–0x26（详见模块背面地址表）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **分层驱动架构**：底层 `PCF8574` 类负责 I2C 通信与 GPIO 操作，上层 `PCF8574Keys` 类专注按键管理，解耦硬件细节与业务逻辑
2. **定时器消抖机制**：10ms 定时器周期性扫描按键状态，结合 20ms 消抖时间过滤机械抖动，确保状态稳定
3. **状态缓存优化**：缓存按键状态，仅在定时器扫描时更新，避免频繁 I2C 读取，提升响应效率
4. **回调触发逻辑**：按键状态变化时自动触发回调函数，支持实时交互响应，避免轮询开销
5. **参数校验防护**：对 I2C 地址（0x20–0x27）、引脚编号（0–7）、按键名称等进行严格校验，防止无效配置损坏硬件
6. **中断安全设计**：中断回调通过 `micropython.schedule` 调度，避免在 ISR 中执行耗时 I2C 操作，提升系统稳定性

---

## 使用说明

### 初始化流程

```
from machine import I2C, Pin
from pcf8574 import PCF8574
from pcf8574keys import PCF8574Keys, KEYS_MAP
import time

# 初始化 I2C（示例：Raspberry Pi Pico I2C0，SDA=GP4，SCL=GP5，400kHz）
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)

# 扫描 I2C 设备，获取 PCF8574 地址
devices = i2c.scan()
pcf_addr = None
for dev in devices:
    if 0x20 <= dev <= 0x27:
        pcf_addr = dev
        break

if not pcf_addr:
    raise ValueError("PCF8574 not found on I2C bus!")

# 创建 PCF8574 实例
pcf = PCF8574(i2c, pcf_addr)

# 创建五向按键管理实例（使用默认 KEYS_MAP）
keys = PCF8574Keys(pcf, KEYS_MAP)
```

### 核心操作

```
# 读取单个按键状态（True=按下，False=未按下）
print("UP key state:", keys.read_key('UP'))

# 读取所有按键状态
all_states = keys.read_all()
print("All keys state:", all_states)

# 通过 SW1/SW2 控制 LED
if keys.read_key('SW1'):
    keys.led_on()
if keys.read_key('SW2'):
    keys.led_off()

# 释放资源（程序结束时调用）
keys.deinit()
```

### 自定义回调函数

```
def key_callback(key_name, state):
    print(f"Key {key_name} changed to {'pressed' if state else 'released'}")

# 初始化时绑定回调
keys = PCF8574Keys(pcf, KEYS_MAP, callback=key_callback)
```

---

## 示例程序

```
from machine import I2C, Pin
import time
from pcf8574 import PCF8574
from pcf8574keys import PCF8574Keys, KEYS_MAP

# I2C 配置
I2C_ID = 0
SCL_PIN = 5
SDA_PIN = 4
PCF8574_ADDR = None

# 上电延时
time.sleep(3)
print("FreakStudio:PCF8574 Five-way Button Test Program")

# 初始化 I2C
i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

# 扫描 I2C 设备
devices_list = i2c.scan()
if not devices_list:
    print("No I2C device found!")
else:
    print(f"I2C devices found: {len(devices_list)}")
    for device in devices_list:
        if 0x20 <= device <= 0x27:
            print(f"I2C hexadecimal address: {hex(device)}")
            PCF8574_ADDR = device

# 初始化 PCF8574 与五向按键
pcf = PCF8574(i2c, PCF8574_ADDR)
keys = PCF8574Keys(pcf, KEYS_MAP)

# 主循环
while True:
    # 打印所有按键状态
    all_states = keys.read_all()
    print(all_states)
    
    # SW1 控制 LED 开启，SW2 控制 LED 关闭
    if keys.read_key('SW1'):
        keys.led_on()
    if keys.read_key('SW2'):
        keys.led_off()
    
    # 100ms 刷新一次
    time.sleep(0.1)
```

---

## 注意事项

1. **I2C 地址约束**：PCF8574 仅支持 0x20–0x27 作为 I2C 地址，通过 A0/A1/A2 跳线设置，超出范围将触发 `ValueError`
2. **按键映射匹配**：`KEYS_MAP` 需与模块实际引脚接线一致，修改时需确保引脚编号（0–7）与硬件对应
3. **消抖时间调整**：默认消抖时间为 20ms，可通过修改 `DEBOUNCE_MS` 全局变量适配不同按键的机械特性
4. **定时器扫描频率**：内部定时器扫描周期为 10ms，请勿修改，否则会影响消抖效果与响应速度
5. **中断回调限制**：中断回调函数需轻量，避免执行耗时操作（如串口打印、复杂计算），建议通过 `micropython.schedule` 调度
6. **I2C 操作安全**：所有 I2C 读写操作非 ISR-safe，禁止在中断处理函数中直接调用，需通过调度机制间接执行
7. **LED 默认状态**：模块 LED 默认关闭，需通过 SW1 开启，SW2 关闭，硬件上 LED 由 PCF8574 引脚 6 控制

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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