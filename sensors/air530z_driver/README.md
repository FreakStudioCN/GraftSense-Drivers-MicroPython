# GraftSense-基于 Air530Z 的北斗导航模块（MicroPython）

# GraftSense-基于 Air530Z 的北斗导航模块（MicroPython）

# GraftSense Air530Z 北斗导航模块

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

本模块是 FreakStudio GraftSense Air530Z 北斗导航模块，基于 Air530Z 芯片实现北斗/GPS 双模定位，支持卫星定位、导航信息输出、速度与时间测量，具备高灵敏度、接口兼容性好、易于开发等优势，兼容 Grove 接口标准。适用于无人车导航、电子 DIY 定位实验、物联网定位演示等场景，为系统提供可靠的位置感知能力。

## 主要功能

基于 MicroPython 实现完整的北斗/GPS 定位控制与数据解析能力，核心功能如下：

1. 双模定位：支持 BDS+GPS、BDS+GLONASS、GPS Only、BDS Only 等多卫星系统组合定位
2. 灵活配置：可通过 NMEA 指令动态调整波特率（9600/115200）、定位更新率（1/5/10 Hz）、卫星系统模式
3. 数据解析：稳健解析 GGA、RMC、GSA、GSV 等关键 NMEA 协议消息，提取经纬度、海拔、时间、卫星数等核心定位数据
4. 异常处理：缓存最后一次有效定位数据，无卫星信号时可回退使用，提升程序稳定性
5. 指令交互：支持产品信息查询、启动模式配置（冷/温/热启动）等功能

## 硬件要求

### 核心接口

- UART 通信接口：

  - MRX：对应 MCU 的串口 RXD，实际连接 Air530Z 的 R1OUT 引脚
  - MTX：对应 MCU 的串口 TXD，实际连接 Air530Z 的 T1IN 引脚
  - ⚠️ 注意：遵循 UART“收发交叉”规则，MRX 直接接 MCU RXD，MTX 直接接 MCU TXD，切勿交叉连接
- 电源接口：VCC（3.3V/5V 供电）、GND（接地）
- 拨码开关：

  - ON/OFF：控制模块工作状态（低电平关闭，高电平/悬空正常工作）
  - BDS_GLONASS：选择卫星系统（ON=BDS+GLONASS，OFF=BDS+GPS）
  - ⚠️ 注意：拨码开关功能需先断电再上电生效，无法在工作中切换

### 电路设计

- Air530Z 核心电路：实现北斗/GPS 双模定位，支持多卫星系统信号接收与处理
- 双电源切换电路：适配不同供电场景，提升兼容性
- 电平转换电路：实现 UART 信号电平匹配，保障通信稳定
- DC-DC 5V 转 3.3V 电路：为 Air530Z 芯片提供稳定 3.3V 供电
- 电源滤波电路：滤除电源噪声，提升定位精度
- 电源指示灯：直观显示模块供电状态

### 模块布局

- 正面：拨码开关（ON/OFF、BDS_GLONASS）、电源指示灯、UART 接口（MRX/MTX）、电源接口（GND/VCC），接口清晰标注，便于接线调试

## 文件说明

| 文件名        | 功能说明                                                                      |
| ------------- | ----------------------------------------------------------------------------- |
| air530z.py    | 核心驱动文件，定义 Air530Z 类，封装模块配置、指令发送、数据读取等核心功能     |
| nmeaparser.py | NMEA 协议解析文件，定义 NMEAParser、NMEASender 类，负责指令生成和定位数据解析 |
| main.py       | 测试示例文件，实现北斗/GPS 定位数据的实时读取与打印，包含基础使用示范         |

## 软件设计核心思想

1. 类结构分层设计：

   - 核心类 `Air530Z` 继承自 `NMEAParser`，整合“指令发送 + 数据解析”能力，对外提供统一 API
   - 辅助类 `NMEASender` 专注生成带校验和的 NMEA 配置指令，保证指令合法性
   - 解析类 `NMEAParser` 专注 NMEA 句子解析，独立处理不同类型消息，降低耦合度
2. 配置与解析分离：将 NMEA 指令生成（配置）和 NMEA 数据解析拆分为独立逻辑，便于维护和扩展
3. 异常容错设计：缓存 `last_known_fix` 最后一次有效定位数据，无卫星信号时避免程序崩溃，提升鲁棒性
4. 标准化接口：封装常用配置方法（`set_baudrate`/`set_system_mode` 等），参数标准化，降低使用门槛

## 使用说明

### 基础接线

1. 电源接线：VCC 接 3.3V/5V 电源，GND 接系统地
2. UART 接线：MRX 接 MCU 的 RXD 引脚，MTX 接 MCU 的 TXD 引脚（切勿交叉）
3. 拨码配置（可选）：根据需求设置 ON/OFF 和 BDS_GLONASS 拨码，配置后断电重启生效

### 核心配置操作

1. 初始化模块：绑定 UART 实例，创建 Air530Z 对象
2. 动态配置卫星系统：通过 `set_system_mode` 方法切换 BDS+GPS/GPS Only/BDS Only 模式
3. 读取定位数据：调用 `read` 方法自动解析 UART 数据，返回结构化定位信息

## 示例程序

### 基础定位测试

```python
import time
from machine import UART, Pin
from air530z import Air530Z

# 上电延时3s，等待模块稳定
time.sleep(3)
print("FreakStudio: air530z test")

# 初始化UART（按硬件接线调整TX/RX引脚）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建Air530Z实例
gps = Air530Z(uart0)

# 主循环：实时读取定位数据
while True:
    try:
        gps_data = gps.read()

        if gps_data:
            print("=" * 40)
            print("GPS_DATA")
            print("=" * 40)

            # 打印经纬度
            print(f"longitude: {gps_data['longitude']}°")
            print(f"latitude: {gps_data['latitude']}°")

            # 打印海拔
            print(f"altitude: {gps_data['altitude']}")

            # 打印时间戳
            if gps_data['timestamp'] is None:
                print("time: None")
            else:
                ts = gps_data['timestamp']
                print(f"time: {ts['hour']:02d}:{ts['minute']:02d}:{ts['second']:02d}")

            # 打印卫星数
            print(f"satellites: {gps_data['satellites']}")
            print("=" * 40)
    except Exception as e:
        print("Error reading GPS data:", e)

    time.sleep(1)
```

### 动态切换卫星系统模式

```python
# 初始化后，切换为GPS Only模式
success, cmd = gps.set_system_mode(gps.MODE_GPS_ONLY)
if success:
    print(f"切换为GPS Only模式成功，发送指令：{cmd}")
else:
    print("切换模式失败")

# 延时5秒后，切换回BDS+GPS双模模式
time.sleep(5)
success, cmd = gps.set_system_mode(gps.MODE_BDS_GPS)
if success:
    print(f"切换为BDS+GPS模式成功，发送指令：{cmd}")
else:
    print("切换模式失败")
```

### 示例说明

1. UART 初始化：根据硬件接线配置 UART 引脚（TX=16, RX=17），波特率 9600（与模块默认一致）
2. 定位读取：`gps.read()` 自动从 UART 接收 NMEA 数据，解析后返回位置字典
3. 动态配置：`set_system_mode` 方法可在运行时切换卫星系统模式，无需重启模块
4. 数据打印：实时打印经纬度、海拔、时间、卫星数，直观展示定位状态
5. 异常处理：捕获并打印读取异常，提升程序稳定性

## 注意事项

1. UART 接线规范：MRX 直接接 MCU RXD，MTX 直接接 MCU TXD，切勿交叉连接，否则通信失败
2. 拨码开关生效条件：ON/OFF 和 BDS_GLONASS 拨码开关功能需先断电再上电生效，无法在工作中切换
3. 定位环境要求：必须将模块放置在户外开阔场地，才能正确获取经纬度信息，室内/遮挡环境无法定位
4. 电源稳定性：模块供电需稳定，避免电压波动导致定位精度下降
5. NMEA 指令校验：所有配置指令需包含正确的校验和，否则模块不响应
6. 无卫星处理：NMEAParser 会缓存最后一次有效定位数据，无卫星时可回退使用，避免程序崩溃

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