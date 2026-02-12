# GraftSense-基于 AT24C256 的 EEPROM 模块（MicroPython）

# GraftSense-基于 AT24C256 的 EEPROM 模块（MicroPython）

# GraftSense 基于 AT24C256 的 EEPROM 模块

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

本模块是 FreakStudio GraftSense 基于 AT24C256 的 EEPROM 模块，通过 AT24C256 芯片实现 256Kbit（32KB）非易失性数据存储，支持 I2C 总线读写，具备存储容量大、接口简便、数据保持可靠等优势，兼容 Grove 接口标准。适用于创客项目参数存储、工业设备配置信息备份等场景，为系统提供可靠的长期数据存储与交互能力。

## 主要功能

### 硬件功能

- 提供标准 I2C 通信接口（SDA/SCL），支持 3.3V/5V 电平兼容，通信速率符合 I2C 标准
- 支持通过 A0/A1/A2 拨码开关灵活配置 8 种不同的 I2C 地址，避免多设备地址冲突
- 集成电源指示灯，直观显示模块供电状态
- 内置 DC-DC 5V 转 3.3V 电路、电源滤波电路和 I2C 上拉电阻，保障通信与供电稳定
- 实现 32KB 非易失性数据存储，支持字节读写、页写入和顺序读取

### 软件功能

- 基于 MicroPython 封装 AT24CXX 通用类，兼容 AT24C32/64/128/256/512 等多型号 EEPROM 芯片
- 提供单字节读写、页写入、顺序读取等核心 API，自动处理跨页写入逻辑
- 支持指定区域数据擦除（写入 0xFF），便于数据重置
- 内置写入延时处理，无需手动等待 EEPROM 写入完成
- 具备地址范围校验，超出范围自动抛出异常，提升代码健壮性

## 硬件要求

### 核心接口要求

- I2C 通信接口：需连接 SDA（数据）、SCL（时钟）引脚，支持标准 I2C 100KHz 通信速率
- 电源接口：VCC 支持 3.3V/5V 供电，需正确连接 GND 接地
- 地址配置：根据实际需求通过 A0/A1/A2 拨码开关配置 I2C 地址（如 0xA0、0xA2 等）

### 电路适配要求

- 需保障电源稳定性，避免数据读写过程中电压波动
- I2C 总线建议匹配上拉电阻（模块已内置，外部无需额外添加）
- 供电电压需在 3.3V~5V 范围内，超出范围可能导致芯片损坏

### 物理布局要求

- 模块正面包含 AT24C256 芯片、地址拨码开关、I2C/电源接口及指示灯，接线时需按标注对应连接
- 建议在干燥、无强电磁干扰的环境下使用，避免影响通信稳定性

## 文件说明

| 文件名        | 功能说明                                                     |
| ------------- | ------------------------------------------------------------ |
| `at24c256.py` | EEPROM 驱动核心文件，封装 AT24CXX 类，提供所有数据读写 API   |
| `main.py`     | 功能示例文件，包含单字节读写、页写入、掉电验证等完整使用案例 |
| `README.md`   | 模块使用说明文档，包含功能介绍、使用方法、注意事项等内容     |

## 软件设计核心思想

1. **通用化封装**：设计 AT24CXX 通用类，通过 `chip_size` 参数适配 AT24C32/64/128/256/512 等不同容量芯片，无需为每种芯片单独编写驱动，提升代码复用性。
2. **易用性设计**：自动处理 EEPROM 页写入限制（64 字节/页），跨页写入时自动拆分数据并分段写入，降低用户使用门槛；内置 5ms 写入延时，无需用户手动处理等待逻辑。
3. **健壮性保障**：添加地址范围校验，当读写地址超出 `chip_size - 1` 时抛出 `ValueError`，避免非法地址操作；封装擦除函数，简化指定区域数据重置流程。
4. **面向对象设计**：将 I2C 实例、芯片容量、I2C 地址等作为类属性，通过实例化方式管理不同 EEPROM 设备，逻辑清晰且便于多设备管理。

## 使用说明

### 前期准备

1. 确保模块正确供电（3.3V/5V），并按标注连接 SDA、SCL 引脚到开发板对应 I2C 引脚。
2. 根据拨码开关配置，确定模块的 I2C 地址（默认 0x50）。
3. 将 `at24c256.py` 驱动文件放入开发板 MicroPython 环境中。

### 基本使用流程

1. **初始化 I2C**：创建 I2C 实例，指定 SDA/SCL 引脚及通信频率。
2. **实例化 AT24CXX**：传入 I2C 实例、芯片容量（AT24C256）和 I2C 地址。
3. **数据操作**：调用 `write_byte`/`read_byte` 实现单字节读写，调用 `write_page`/`read_sequence` 实现多字节读写。
4. **数据验证**：可通过掉电重启后读取数据，验证 EEPROM 非易失性存储特性。
5. **数据擦除**：调用 `erase_data` 函数可将指定区域数据擦除为 0xFF，便于重新写入。

## 示例程序

以下是 `main.py` 中的核心示例代码，实现单字节读写、多字节页写入和数据掉电验证：

```python
from machine import I2C, Pin
from at24c256 import AT24CXX
import time

# 全局变量
AT24C256_ADDRESS = 0x50
DATA_SIZE = 128
data_to_write = bytes(range(DATA_SIZE))  # 生成0-127的字节序列

# 擦除指定区域数据（写入0xFF）
def erase_data(at24cxx, start_address, length):
    data_to_erase = bytes([0xFF] * length)
    at24cxx.write_page(start_address, data_to_erase)

# 初始化配置
time.sleep(3)
print("FreakStudio: Read and Write AT24C256")

# 初始化I2C（SDA=4, SCL=5, 100KHz）
i2c_at24c256 = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=100000)
# 创建AT24C256实例（32KB容量，地址0x50）
at24c256 = AT24CXX(i2c_at24c256, AT24CXX.AT24C256, AT24C256_ADDRESS)

# 验证掉电存储：若地址0为0xAB且后续128字节匹配，则数据已保存
if at24c256.read_byte(0) == 0xAB and list(at24c256.read_sequence(1, DATA_SIZE)) == list(data_to_write):
    print("Data verification successful. Data retained after power cycle.")
    erase_data(at24c256, 0, DATA_SIZE + 1)  # 擦除数据
else:
    # 初次写入实验
    print("Erase the data of the first three pages")
    erase_data(at24c256, 0, DATA_SIZE + 1)  # 先擦除前129字节

    # 单字节写入：地址0写入0xAB
    print("Writing single byte...")
    at24c256.write_byte(0x00, 0xAB)
    print("Written single byte 0xAB at address 0x00.")

    # 单字节读取：地址0读取数据
    print("Reading single byte...")
    single_byte = at24c256.read_byte(0x00)
    print(f"Read single byte: {single_byte:#04x}")

    # 页写入：地址1开始写入128字节（0-127）
    print("Writing 128 bytes...")
    at24c256.write_page(0x01, data_to_write)
    print("Written 128 bytes starting at address 0x01.")

    # 顺序读取：地址1开始读取128字节
    print("Reading 128 bytes...")
    read_data = at24c256.read_sequence(0x01, DATA_SIZE)
    print(f"Read 128 bytes: {list(read_data)}")
```

### 示例说明

1. I2C 初始化：使用 GPIO4（SDA）和 GPIO5（SCL）初始化 I2C，频率 100KHz，与模块通信
2. 数据擦除：通过 erase_data 函数将指定区域数据擦除为 0xFF，避免旧数据干扰
3. 单字节操作：向地址 0 写入 0xAB，再读取验证，测试单字节读写功能
4. 页写入与顺序读取：向地址 1 开始写入 128 字节（0-127），再顺序读取验证，测试多字节读写和跨页处理
5. 掉电验证：重启后检查数据是否保留，验证 EEPROM 非易失性存储特性

## 注意事项

1. I2C 地址配置：通过 A0、A1、A2 拨码开关设置 I2C 地址，需与代码中 addr 参数一致，避免通信失败
2. 页写入限制：EEPROM 页大小为 64 字节，write_page 方法会自动处理跨页写入，每段写入后延时 5ms 等待写入完成
3. 地址范围：地址范围为 0 到 chip_size-1（本模块为 0-32767），超出范围会抛出 ValueError
4. 写入延时：EEPROM 写入需要时间（典型 5ms），驱动已在写入操作后自动延时，无需手动处理
5. 电源稳定性：数据读写时需保证电源稳定，避免电压波动导致数据损坏
6. 掉电验证：模块支持非易失性存储，数据写入后掉电不会丢失，可通过重启验证

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2024 FreakStudio

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
