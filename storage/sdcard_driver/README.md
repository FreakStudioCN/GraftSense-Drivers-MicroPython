# SD卡块设备驱动 - MicroPython版本
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

本项目提供一套完整的SD卡存储解决方案，基于MicroPython实现SD卡的SPI协议通信、块设备接口封装和FAT文件系统挂载功能。通过三层架构设计（底层SPI驱动、中间块设备接口、上层文件系统），实现了在嵌入式系统中对SD卡的标准文件读写操作，适用于数据记录、文件存储、固件更新等场景。

> **注意**：本驱动适用于标准SD卡和SDHC/SDXC卡，支持FAT16/FAT32文件系统，不适用于exFAT文件系统或特殊加密SD卡，不可用于高实时性要求的连续数据流存储。

---

## 主要功能

* **完整的三层架构**：
  * SPI层：实现SD卡底层通信协议（CMD0-55）
  * 块设备层：提供标准块设备接口（readblocks/writeblocks/ioctl）
  * 文件系统层：支持FAT文件系统挂载和标准文件操作
* **自动卡类型检测**：支持标准容量卡（SDSC，<2GB）和高容量卡（SDHC/SDXC，2GB-2TB）
* **标准接口兼容**：完全符合MicroPython块设备规范，可与`os`、`open`等标准库无缝集成
* **错误处理**：内置超时重试、命令验证、数据校验机制

---

## 硬件要求

### 推荐测试硬件

* MicroPython开发板（如树莓派Pico、ESP32）
* SD卡模块（SPI接口）
* Micro SD卡（建议4GB-32GB，FAT32格式）
* 杜邦线6根
* （可选）面包板

### 模块引脚说明

| SD卡模块引脚 | 功能描述 | 连接说明 |
|------------|----------|----------|
| VCC        | 电源输入 | 接开发板3.3V或5V（根据模块电压要求） |
| GND        | 接地     | 接开发板GND |
| CS         | 片选信号 | 接开发板任意GPIO（如GP13） |
| MOSI       | 主出从入 | 接开发板SPI MOSI引脚（如GP11） |
| MISO       | 主入从出 | 接开发板SPI MISO引脚（如GP12） |
| SCK        | 时钟信号 | 接开发板SPI SCK引脚（如GP10） |

---

## 文件说明

### AbstractBlockDevInterface.py

该文件定义 **块设备抽象基类**，为SD卡驱动提供标准接口规范。

`AbstractBlockDev` 类定义了符合MicroPython规范的块设备操作接口，支持简单接口（块对齐操作）和扩展接口（任意偏移操作），兼容FAT和littlefs文件系统的驱动需求。实现者需至少支持`ioctl(4)`块数量查询，若需支持littlefs还需实现`ioctl(6)`块擦除功能。

**关键特性**：
- 定义标准块设备方法：`readblocks`、`writeblocks`、`ioctl`
- 支持简单接口（offset=0）和扩展接口（offset≠0）
- 为具体实现提供清晰的接口规范

**许可证**：CC BY-NC 4.0

---

### sdcard.py

该文件实现 **SD卡底层SPI通信驱动**，封装SD/MMC存储卡的物理层操作。

`SDCard` 类通过SPI总线操作SD/MMC存储卡，支持标准容量卡（SDSC）和高容量卡（SDHC/SDXC）的初始化、数据块读写和擦除操作。实现了完整的SPI模式协议栈，包括卡识别模式和数据传输模式。

**主要方法**：
- `__init__(spi, cs, baudrate=1320000)`：初始化SD卡控制器
- `init_card(baudrate)`：执行完整初始化流程
- `cmd(cmd, arg, crc, ...)`：发送SD卡命令并获取响应
- `readinto(buf)`：读取数据块到缓冲区
- `write(token, buf)`：写入数据块到卡片
- `init_card_v1()` / `init_card_v2()`：分别初始化标准容量卡和高容量卡

**关键特性**：
- 自动检测卡类型（SDSC/SDHC/SDXC）
- 支持标准SPI模式协议（CMD0-55）
- 内置超时重试和错误处理机制

**许可证**：MIT

---

### sd_block_dev.py

该文件实现 **SD卡块设备接口层**，将底层SDCard驱动适配为标准块设备接口。

`SDCARDBlockDevice` 类继承自`AbstractBlockDev`，封装了对SDCard设备的块级读写操作，提供标准的`readblocks`、`writeblocks`和`ioctl`方法，符合MicroPython块设备接口规范。

**主要方法**：
- `__init__(sdcard)`：初始化块设备实例，绑定SDCard驱动
- `readblocks(block_num, buf, offset=0)`：读取一个或多个块的数据
- `writeblocks(block_num, buf, offset=0)`：写入一个或多个块的数据
- `ioctl(op, arg)`：设备控制接口（获取块大小、块数量等）

**关键特性**：
- 将物理扇区操作映射为逻辑块操作
- 实现完整的块设备接口规范
- 支持简单接口和扩展接口模式

**许可证**：MIT

---

### main.py

该文件为 **SD卡功能测试程序**，演示完整的文件系统操作流程。

`main.py` 展示了从硬件初始化到文件读写的完整流程：初始化SPI总线、创建SDCard驱动实例、封装为块设备、挂载FAT文件系统、执行文件读写操作。

**主要功能**：
- 硬件初始化和SD卡检测
- 文件系统创建和挂载
- CSV文件写入示例
- 目录列表和文件操作演示

---

## 软件设计核心思想

* **三层架构**：SPI驱动层 → 块设备接口层 → 文件系统层，各层职责清晰
* **接口标准化**：严格遵循MicroPython块设备规范，确保兼容性
* **自动适配**：自动检测卡类型和容量，适配不同规格SD卡
* **错误恢复**：内置超时重试、命令重发机制，提高可靠性

---

## 使用说明

### 硬件接线（树莓派Pico示例）

| SD卡模块引脚 | Pico引脚 | 接线功能 |
|-------------|----------|----------|
| VCC         | 3.3V（Pin36） | 电源输入 |
| GND         | GND（Pin38） | 接地 |
| CS          | GP13（Pin17） | 片选信号 |
| MOSI        | GP11（Pin15） | SPI数据输出 |
| MISO        | GP12（Pin16） | SPI数据输入 |
| SCK         | GP10（Pin14） | SPI时钟 |

---

### 软件依赖

* 固件：MicroPython v1.23+
* 内置库：`machine`（SPI、Pin控制）、`time`、`vfs`、`os`
* 开发工具：Thonny / PyCharm

---

### 安装步骤

1. 烧录MicroPython固件到开发板
2. 将所有.py文件上传到开发板
3. 将SD卡格式化为FAT32文件系统
4. 根据实际接线修改`main.py`中的引脚配置
5. 运行`main.py`，观察文件系统操作结果

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/30 下午12:13   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 文件系统类实验，使用SD卡挂载文件系统并读写

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import SPI, Pin
# 导入时间相关模块
import time
# 导入自定义SD卡块设备类
from sd_block_dev import SDCARDBlockDevice
# 导入自定义SD卡读写类
from sdcard import SDCard
# 导入虚拟文件类
import vfs
# 导入文件系统操作类
import os

# ======================================== 全局变量 ============================================

# 定义嵌入式知识学习网站及其网址
websites = [
    ("Embedded.com", "https://www.embedded.com"),
    ("Microchip", "https://www.microchip.com"),
    ("ARM Developer", "https://developer.arm.com"),
    ("SparkFun", "https://www.sparkfun.com"),
    ("Adafruit", "https://www.adafruit.com"),
    ("Embedded Systems Academy", "https://www.esacademy.com"),
    ("Electronics Hub", "https://www.electronicshub.org"),
]

# 定义CSV文件地址
csv_file_path = '/sdcard/embedded_websites.csv'

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Mount the SD Card to the file system")

# 初始化SPI类，设置波特率、极性、相位、时钟引脚、数据引脚
spi = SPI(1, baudrate=1320000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
# 初始化SD卡类，使用GPIO13作为片选引脚
sdcard = SDCard(spi, cs=Pin(13))

# 创建块设备，使用SD卡，块大小为512个字节
block_device = SDCARDBlockDevice(sdcard = sdcard)
# 在块设备上创建一个 FAT 文件系统
vfs.VfsFat.mkfs(block_device)
# 将块设备挂载到虚拟文件系统的 /sdcard 目录
vfs.mount(block_device, '/sdcard')
# 打印当前目录
print("Current Directory : ",os.listdir())

# ========================================  主程序  ============================================

# 写入 CSV 文件
with open(csv_file_path, 'w') as f:
    # 写入表头
    f.write("Website Name,URL\n")
    for name, url in websites:
        # 写入每一行
        f.write(f"{name},{url}\n")

# 打印文件位置
print(f"CSV file written to SD card as '{csv_file_path}'.")
```

---

## 注意事项

### SD卡规格限制

* **容量限制**：支持最大2TB的SDXC卡，但建议使用4GB-32GB FAT32格式卡以获得最佳兼容性
* **速度等级**：Class 4及以上卡可获得较好性能，高速卡（UHS-I）在SPI模式下可能无法发挥全速
* **文件系统**：仅支持FAT16/FAT32，exFAT格式需要额外驱动支持

---

### 电气特性与电源管理

* **电压匹配**：确认SD卡模块工作电压（3.3V或5V），确保与开发板电压匹配
* **电源稳定性**：SD卡在写入时电流可达100mA，确保电源能提供足够电流
* **上电顺序**：先给开发板上电，稳定后再插入SD卡，避免热插拔损坏
* **去耦电容**：在SD卡模块VCC-GND间添加100nF电容可提高稳定性

---

### SPI配置与性能优化

* **波特率设置**：初始化时使用较低波特率（400kHz），初始化后可提高至1-10MHz
* **相位与极性**：SD卡SPI模式固定为（CPOL=0, CPHA=0）
* **片选管理**：确保在非访问期间CS保持高电平，避免总线冲突
* **线长限制**：SPI信号线建议不超过20cm，过长可能导致通信失败

---

### 文件系统使用规范

* **安全移除**：在断电前执行`umount()`或同步操作，避免文件系统损坏
* **频繁写操作**：避免频繁小文件写入，建议批量写入或使用缓冲区
* **目录结构**：避免创建过深目录层级（建议不超过5层）
* **文件名规范**：使用8.3格式（主名8字符，扩展名3字符）确保最大兼容性

---

### 错误处理与调试

* **初始化失败**：检查接线、电源、SD卡格式、波特率设置
* **读写错误**：尝试降低SPI频率、检查电源稳定性、更换SD卡
* **文件系统损坏**：在电脑上重新格式化（FAT32，分配单元大小4096）
* **容量识别错误**：确保使用标准SD卡，某些山寨卡可能无法正确识别

---

### 环境影响

* **温度范围**：商业级SD卡工作温度0-70℃，工业级-40-85℃
* **湿度防护**：避免凝露环境，高湿度可能导致触点氧化
* **机械振动**：固定SD卡模块，避免振动导致接触不良
* **静电防护**：SD卡对静电敏感，操作时注意防静电

---

### 使用建议

1. **首次使用**：先用`main.py`测试基本功能，确认硬件连接正确
2. **性能测试**：测试读写速度，根据应用需求调整SPI频率
3. **长期运行**：定期检查文件系统完整性，建议每日或每周同步一次
4. **数据安全**：重要数据建议双备份或添加校验机制

---
### 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

---
## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  

**版权归 FreakStudio 所有。**