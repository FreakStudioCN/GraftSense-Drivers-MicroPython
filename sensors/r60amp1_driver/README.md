# GraftSense-基于 R60AMP1 的多人轨迹毫米波雷达模块（开放版）

# GraftSense-基于 R60AMP1 的多人轨迹毫米波雷达模块（开放版）

# GraftSense R60AMP1 Multi-Person Trajectory Millimeter-Wave Radar Module

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

本模块是 **GraftSense 系列基于 R60AMP1 的多人轨迹毫米波雷达模块**，属于 FreakStudio 开源硬件项目。通过毫米波雷达技术，实现多人目标检测、运动轨迹跟踪与空间行为分析，适用于智能空间感知实验、人流监测演示教学等场景，为非接触式人体感知提供高稳定性的解决方案。

**核心优势**：支持多人识别、抗干扰能力强、稳定性高，严格遵守 Grove 接口标准，便于快速集成到主流开发平台。

---

## 主要功能

- **核心感知能力**：

  - 多人目标检测与轨迹跟踪，输出目标索引、大小、特征（静止/运动）、X/Y 坐标（cm）、高度（cm）、速度（cm/s）
  - 人体存在检测（有人/无人状态）
  - 运动状态检测（无运动/静止/活跃三级分类）
  - 体动参数监测（0-100 量化值，反映人体活动强度）
- **通信能力**：

  - 串口 UART 通信（默认波特率 115200），支持**主动数据上报**与**主动查询**两种模式
  - 集成 HC08 蓝牙模块驱动，支持感知数据无线透传至上位机
- **配置能力**：

  - 人体存在检测功能开关控制
  - 数据解析周期可配置（默认 200ms）
  - 查询重试机制（最大 3 次）与超时时间可调

---

## 硬件要求

### 模块接口

| 接口类型  | 引脚定义          | 连接说明                                    |
| --------- | ----------------- | ------------------------------------------- |
| UART 通信 | MRX（模块接收）   | 对应 MCU TX 引脚                            |
|           | MTX（模块发送）   | 对应 MCU RX 引脚                            |
| 电源      | VCC               | 5V 供电（模块内置 DC-DC 5V→3.3V 转换电路） |
|           | GND               | 接地                                        |
| 扩展接口  | GP1-GP6、SWC、SWD | 用于固件升级与功能扩展                      |

### 安装规范

- **探测范围**：水平 100°、俯仰 100° 的立体扇形区域
- **水平安装建议**：

  - 安装高度：1m ≤ H ≤ 1.5m，默认 1.4m
  - 前方无明显遮挡物，确保主波束覆盖探测区域
- **探测距离**：

  - 运动轨迹跟踪最大距离：1.3 ~ 10m
  - 人体静止位置检测最大距离：6 ~ 12m
- **多目标区分**：最小角度 ≥20°，最小距离 ≥0.5m

---

## 文件说明

| 文件名称                 | 功能描述                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `data_flow_processor.py` | 数据流处理器，实现 R60ABD1 雷达串口协议解析：帧接收、CRC 校验、解析、发送，统计通信错误（CRC/帧结构/无效帧） |
| `hc08.py`                | HC08 蓝牙模块驱动，支持串口数据透传，将雷达感知数据无线发送至上位机                                          |
| `r60amp1.py`             | R60AMP1 业务处理核心类，封装初始化、指令映射、数据解析、属性更新等业务逻辑                                   |
| `main.py`                | 示例测试程序，演示模块初始化、数据读取、状态打印与蓝牙透传的完整流程                                         |

---

## 软件设计核心思想

1. **分层架构**：

   - **数据流层**（`data_flow_processor.py`）：专注于串口帧协议的底层处理，确保数据传输可靠性
   - **业务逻辑层**（`r60amp1.py`）：封装雷达设备的状态管理与指令映射，提供统一的查询/上报接口
   - **应用层**（`main.py`）：基于业务逻辑层实现具体场景（如数据打印、蓝牙透传）
2. **帧协议解析**：严格遵循设备协议，帧结构为：

   ```
   ```

帧头(0x53 0x59) → 控制字 → 命令字 → 数据长度(大端) → 数据 → CRC(求和校验) → 帧尾(0x54 0x43)

```

3. **状态管理**：通过类属性维护设备状态（初始化状态、存在状态、运动状态、轨迹目标等），支持主动上报与主动查询双模式更新

4. **异常处理**：内置查询重试（最大 3 次）、超时控制（默认 200ms），统计通信异常，便于调试与稳定性优化

5. **定时器驱动**：通过硬件定时器周期性触发数据解析（默认 200ms），确保感知数据实时更新，避免阻塞主循环

---



## 使用说明

### 1. 硬件连接

- **UART 接线**（以 Raspberry Pi Pico 为例）：
	- 模块 MTX → MCU RX（GP17）
	- 模块 MRX → MCU TX（GP16）
	- 模块 VCC → 5V，模块 GND → GND

- **蓝牙模块（可选）**：HC08 连接至 MCU UART1（TX=GP8, RX=GP9），波特率 9600

### 2. 初始化流程

```python
from machine import UART, Pin
import time
from data_flow_processor import DataFlowProcessor
from r60amp1 import R60AMP1
from hc08 import HC08

# 初始化UART0（与雷达通信，波特率115200）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)
# 初始化UART1（与蓝牙通信，波特率9600）
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9), timeout=0)

# 创建蓝牙实例
hc0 = HC08(uart1)
# 创建数据流处理器
processor = DataFlowProcessor(uart)
# 创建R60AMP1实例（启用人体存在检测，解析间隔200ms）
device = R60AMP1(
    processor,
    parse_interval=200,
    presence_enabled=True,
    max_retries=3,
    retry_delay=100,
    init_timeout=5000
)
```

### 3. 数据读取与应用

```python
# 主动查询存在状态
success, presence_status = device.query_presence_status()
if success:
    print("Presence Status:", "Someone" if presence_status == R60AMP1.PRESENCE_PERSON else "No one")

# 主动查询轨迹信息
success, trajectory_targets = device.query_trajectory_info()
if success:
    for target in trajectory_targets:
        print(f"Target {target['index']}: X={target['x']}cm, Y={target['y']}cm")

# 主循环中读取主动上报数据
while True:
    print("Presence Status:", device.presence_status)
    print("Motion Status:", device.motion_status)
    print("Trajectory Targets:", len(device.trajectory_targets))
    time.sleep_ms(200)
```

---

## 示例程序

完整示例代码见 `main.py`，核心功能包括：

- 设备初始化与状态校验
- 定期打印传感器主动上报的存在状态、运动状态、轨迹信息
- 通过 HC08 蓝牙模块将感知数据透传至上位机
- 主动查询存在状态并打印结果
- 异常捕获与资源清理

```python
# 主循环核心逻辑
try:
    last_print_time = time.ticks_ms()
    print_interval = 2000
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 打印上报数据
            print_report_sensor_data()
            # 蓝牙透传
            hc0.send_data(f"Presence: {device.presence_status}\n")
            hc0.send_data(f"Targets: {len(device.trajectory_targets)}\n")
            # 主动查询存在状态
            success, status = device.query_presence_status()
            if success:
                print("Active Query Presence:", "Someone" if status else "No one")
            last_print_time = current_time
        time.sleep_ms(10)
except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    device.close()
    del device
```

---

## 注意事项

1. **安装规范**：

   - 必须水平安装，避免倾斜导致探测范围偏移
   - 安装高度建议 1.4m，前方无金属、厚墙等遮挡物，避免干扰雷达信号
2. **应用限制**：

   - 本模块为消费级感知设备，**不可用于医疗诊断、工业安全等对精度和可靠性要求极高的场景**
   - 多目标跟踪精度受环境干扰（如墙壁反射、移动物体密度）影响，实际使用需进行场景校准
3. **通信稳定性**：

   - UART 波特率需与模块配置一致（默认 115200），避免数据乱码
   - 查询操作避免过于频繁（建议间隔 ≥200ms），防止设备处理过载
4. **内存管理**：

   - 长时间运行时，定期触发垃圾回收（`gc.collect()`），避免内存溢出
   - 设备关闭时调用 `device.close()`，释放定时器与缓冲区资源

---

## 联系方式

如有问题或技术支持，请联系：

- 邮箱：liqinghsui@freakstudio.cn
- GitHub：[FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

```
MIT License

Copyright (c) 2025 FreakStudio

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