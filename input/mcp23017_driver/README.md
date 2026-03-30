# MCP23017 Driver for MicroPython

# MCP23017 Driver for MicroPython

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

`mcp23017_driver` 是一个用于 **MicroPython** 的 MCP23017 芯片驱动库，提供了对 MCP23017 16 位 I/O 扩展器的便捷控制接口。该库封装了 I2C 通信逻辑，支持引脚方向配置、电平读写、中断等核心功能，可在各类支持 MicroPython 的开发板上快速部署。

---

## 主要功能

- 支持 I2C 接口通信，兼容标准 MCP23017 芯片
- 配置引脚为输入 / 输出模式
- 读写引脚电平（支持单个引脚 / 端口批量操作）
- 配置上拉电阻
- 支持中断触发配置
- 无特定芯片或固件依赖，可在大部分 MicroPython 环境运行

---

## 硬件要求

- 开发板：任意支持 MicroPython 且带有 I2C 外设的开发板（如 ESP32、ESP8266、RP2040 等）
- 外设芯片：MCP23017 16 位 I/O 扩展器
- 连接方式：通过 I2C 总线连接（SDA/SCL 引脚）
- 供电：3.3V 或 5V（根据开发板与芯片规格选择）

---

## 文件说明

<table>
<tr>
<td>**文件名**<br/></td><td>**用途**<br/></td></tr>
<tr>
<td>mcp23017.py<br/></td><td>驱动库核心实现，包含 MCP23017 类及所有操作方法<br/></td></tr>
<tr>
<td>package.json<br/></td><td>包管理配置文件，声明库名称、版本、作者、依赖等元数据<br/></td></tr>
<tr>
<td>LICENSE<br/></td><td>MIT 开源许可协议文本<br/></td></tr>
</table>

## 软件设计核心思想

- **简洁易用**：对外暴露直观的 API，隐藏底层 I2C 通信细节
- **兼容性优先**：不依赖特定固件或芯片，适配广泛的 MicroPython 环境
- **模块化设计**：核心功能与硬件操作分离，便于维护与扩展
- **资源轻量化**：代码精简，适合资源受限的嵌入式设备

---

## 使用说明

1. **准备环境**：确保开发板已烧录支持 I2C 的 MicroPython 固件
2. **文件上传**：将 `mcp23017.py` 上传至开发板的文件系统
3. **导入库**：在你的项目中导入 `mcp23017` 模块
4. **初始化 I2C**：根据开发板引脚配置初始化 I2C 总线
5. **创建驱动实例**：传入 I2C 对象与芯片地址（默认 0x20）
6. **调用 API**：配置引脚方向、读写电平或配置中断

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午6:20
# @Author  : hogeiha
# @File    : main.py
# @Description : MCP23017测试  配置I2C扫描、引脚输入输出、虚拟引脚操作、极性反转验证

# ======================================== 导入相关模块 =========================================

from machine import SoftI2C, Pin
import mcp23017  # 导入MCP23017驱动模块
import time

# ======================================== 全局变量 ============================================

# I2C硬件配置常量
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
# MCP23017目标I2C地址
TARGET_SENSOR_ADDR = 0x20
# 引脚定义常量
A1_PIN = 1  # A1引脚编号（输出）
A3_PIN = 3  # A3引脚编号（输入）
# 全局MCP23017对象
mcp = None

# ======================================== 功能函数 ============================================


def test_mcp_functions():
    """
    演示MCP23017核心功能：基本电平读写、虚拟引脚操作、寄存器批量操作、输入极性反转
    Args:
        无

    Raises:
        无

    Notes:
        依次验证不同功能模块，输出关键调试信息

    ==========================================

    Demonstrate MCP23017 core functions: basic level read/write, virtual pin operation, batch register operation, input polarity inversion
    Args:
        None

    Raises:
        None

    Notes:
        Verify different function modules in sequence and output key debugging information
    """
    # ---------- 演示1：基本读写（A3输出，A3读取） ----------
    print("
=== Demo 1: Basic Level Read/Write ===")
    # 切换A3电平为高，读取A3验证（短接后A3应同步为高）
    mcp.pin(A1_PIN, value=1)
    a3_val = mcp.pin(A3_PIN)  # 读取A3电平（返回True/False）
    print(f"A3 Output Level: HIGH (1) | A3 Read Level: {'HIGH (1)' if a3_val else 'LOW (0)'}")

    # 切换A3电平为低，读取A3验证
    mcp.pin(A1_PIN, value=0)
    a3_val = mcp.pin(A3_PIN)
    print(f"A3 Output Level: LOW (0) | A3 Read Level: {'HIGH (1)' if a3_val else 'LOW (0)'}")

    # ---------- 演示2：虚拟引脚用法（更直观的引脚操作） ----------
    print("
=== Demo 2: Virtual Pin Operation ===")
    # 获取A3和A3的虚拟引脚对象
    A3_vpin = mcp[A1_PIN]
    a3_vpin = mcp[A3_PIN]

    # 用虚拟引脚设置A3为高
    A3_vpin.output(val=1)  # 等价于mcp.pin(A1_PIN, mode=0, value=1)
    a3_val = a3_vpin.value()  # 读取A3电平
    print(f"Virtual Pin A3 Output: HIGH (1) | Virtual Pin A3 Read: {'HIGH (1)' if a3_val else 'LOW (0)'}")

    # ---------- 演示3：批量配置/读取寄存器（进阶） ----------
    print("
=== Demo 3: Batch Register Operation ===")
    # 读取PortA（A0-A7）的整体模式（IODIR寄存器）
    porta_mode = mcp.porta.mode
    print(f"PortA Mode Register Value: 0x{porta_mode:02X} (A3=Output(0), A3=Input(1) As Expected)")

    # 读取PortA的上拉电阻配置（GPPU寄存器）
    porta_pullup = mcp.porta.pullup
    print(f"PortA Pullup Register Value: 0x{porta_pullup:02X} (A3 Pullup Enabled(1) As Expected)")

    # ---------- 演示4：输入极性反转（可选，取消注释后验证） ----------
    print("
=== Demo 4: Input Polarity Inversion ===")
    # 启用A3极性反转
    mcp.pin(A3_PIN, polarity=1)
    # 再次设置A3为高，A3读取应为低（因为极性反转）
    mcp.pin(A1_PIN, value=1)
    a3_val = mcp.pin(A3_PIN)
    print(f"A3 Output: HIGH (1) | A3 Inverted Read: {'HIGH (1)' if a3_val else 'LOW (0)'} (Expected LOW)")

    # 恢复A3极性为正常
    mcp.pin(A3_PIN, polarity=0)


def loop_verify():
    """
    循环验证A3输出与A3输入的电平同步性，每1秒切换一次A3电平
    Args:
        无

    Raises:
        无

    Notes:
        循环5次，输出每次的电平匹配结果，需短接A3和A3引脚

    ==========================================

    Cyclically verify the level synchronization between A3 output and A3 input, switch A3 level every 1 second
    Args:
        None

    Raises:
        None

    Notes:
        Loop 5 times, output the level matching result each time, need to short-circuit A3 and A3 pins
    """
    print("
=== Loop Verification (Switch A3 Level Every 1 Second) ===")
    print("Short-circuit A3 and A3, observe if A3 synchronizes with A3 level changes...")
    count = 0
    while count < 5:  # 循环5次
        # 切换A3电平
        current_val = count % 2  # 0/1交替
        mcp.pin(A1_PIN, value=current_val)
        # 读取A3
        a3_val = mcp.pin(A3_PIN)
        # 打印结果
        print(f"Round {count+1} - A3 Output: {current_val} | A3 Read: {1 if a3_val else 0} | Matched: {current_val == a3_val}")
        time.sleep(1)
        count += 1


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: MCP23017 I2C Expander Function Test - Short A3 and A3 Pins")

# 初始化I2C总线（适配Raspberry Pi Pico）
i2c_bus = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器（MCP23017）
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化MCP23017
            mcp = mcp23017.MCP23017(i2c=i2c_bus, address=TARGET_SENSOR_ADDR)
            print("Target sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标地址时抛出明确异常
    raise Exception("No MCP23017 found at target address 0x20")

# 配置引脚（核心：A3输出，A3输入）
# 配置A3为输出模式（mode=0），初始电平低（value=0）
mcp.pin(A1_PIN, mode=0, value=0)
# 配置A3为输入模式（mode=1），启用内部上拉电阻（pullup=1）
mcp.pin(A3_PIN, mode=1, pullup=1)

# ========================================  主程序  ============================================

if __name__ == "__main__":
    try:
        # 执行核心功能测试
        test_mcp_functions()
        # 执行循环验证
        loop_verify()
        print("
Program execution completed successfully!")
    except OSError as e:
        print(f"Error: {e}, Please check I2C wiring or MCP23017 address!")
    except Exception as e:
        print(f"Initialization Error: {e}")

```

## 注意事项

- 请确认 MCP23017 的 I2C 地址与代码中传入的地址一致（由 A0/A1/A2 引脚电平决定）
- 输入模式下如需稳定电平，建议开启内部上拉电阻
- 批量操作端口时，注意 8 位端口的位映射关系
- 中断功能需额外配置开发板外部中断引脚
- 运行前请检查硬件接线，避免短路或电压不匹配

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源协议，完整内容如下：

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
