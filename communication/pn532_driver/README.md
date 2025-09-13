# PN532 NFC模块驱动 - MicroPython版本

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
PN532是一款高性能NFC近场通信芯片，支持多种卡型读写（Mifare Classic、NTAG2XX等）和通信接口。该芯片广泛应用于移动支付、身份识别、数据传输、门禁系统等场景。

本项目提供基于MicroPython的PN532模块驱动代码及测试程序，支持通过UART接口与模块通信，方便开发者快速实现NFC卡片的检测与数据读写功能。

---

## 主要功能
- **多种卡型支持**：
  - Mifare Classic系列（1K/4K）
  - NTAG2XX系列
  - 其他符合ISO 14443 Type A标准的卡片
- **完整操作集**：
  - 卡片检测与激活
  - 数据块读写
  - 卡片UID获取
  - 模块固件版本查询
- **低功耗支持**：提供休眠与唤醒功能
- **统一接口**：通过`PN532`类提供一致操作方法
- **跨平台兼容**：支持ESP32、ESP8266、树莓派Pico等MicroPython开发板

---

## 硬件要求
### 推荐测试硬件
- ESP32/ESP8266/树莓派Pico开发板
- PN532 NFC模块（UART接口版本）
- Mifare Classic或NTAG2XX系列测试卡片
- 杜邦线若干

### 模块引脚说明
| PN532引脚 | 功能描述 |
|-----------|----------|
| VCC       | 电源正极（3.3V，注意：部分模块支持5V） |
| GND       | 电源负极 |
| TX        | UART发送引脚 |
| RX        | UART接收引脚 |
| RST       | 复位引脚（低电平有效） |
| SDA       | I2C数据引脚（本项目未使用） |
| SCL       | I2C时钟引脚（本项目未使用） |
| SS        | SPI片选引脚（本项目未使用） |

---

## 文件说明
### pn532.py
包含`PN532`基类，提供NFC功能的核心接口：
- `__init__(uart, rst_pin, debug=False)`：初始化PN532模块，建立与硬件的连接
- `wake_up()`：唤醒休眠状态的模块并验证通信连接
- `get_firmware_version()`：获取模块固件版本信息，返回版本号
- `sam_configuration()`：配置安全访问模块(SAM)，设置卡片读取模式
- `read_passive_target()`：检测并激活附近的NFC卡片，返回卡片UID
- `mifare_classic_read_block(block_number)`：读取Mifare Classic卡片指定块的数据
- `mifare_classic_write_block(block_number, data)`：向Mifare Classic卡片指定块写入数据
- `ntag2xx_write_page(page_number, data)`：向NTAG2XX系列卡片指定页写入数据

### uart.py
包含`PN532_UART`类，继承自`PN532`基类，实现UART通信功能：
- `__init__(uart, rst_pin, debug=False)`：初始化UART通信接口
- `_write(data)`：通过UART发送数据帧到PN532模块
- `_read()`：通过UART从PN532模块接收数据帧并解析

### main.py
无类定义，包含测试主函数`main()`：
- 初始化硬件接口和PN532模块
- 执行模块自检（固件版本查询、SAM配置）
- 循环检测NFC卡片并输出卡片UID
- 提供可扩展的卡片读写测试框架

---

## 软件设计核心思想
### 分层设计
- 底层：UART通信协议实现（`uart.py`）
- 中层：PN532命令封装与解析（`pn532.py`）
- 高层：应用级API与测试流程（`main.py`）

### 通信协议
- 基于PN532的帧格式实现数据收发
- 包含校验机制确保数据完整性
- 实现命令超时重试机制

### 跨平台兼容
- 仅依赖MicroPython标准库
- 硬件接口通过参数注入，与具体平台解耦
- 统一的错误处理机制

---

## 使用说明
### 硬件接线（ESP32示例）

| PN532引脚 | ESP32 GPIO引脚 |
|-----------|----------------|
| VCC       | 3.3V           |
| GND       | GND            |
| TX        | GPIO4          |
| RX        | GPIO5          |
| RST       | GPIO15         |

> **注意：**
> - 确认模块工作电压，避免使用5V损坏3.3V模块
> - 接线前确保开发板已断电
> - 可根据实际需求修改引脚配置

---

### 软件依赖
- **固件版本**：MicroPython v1.23.0+
- **内置库**：
  - `machine`（GPIO与UART控制）
  - `time`（延时功能）

---

### 安装步骤
1. 将MicroPython固件烧录到开发板
2. 上传`pn532.py`、`uart.py`和`main.py`到开发板
3. 根据硬件连接修改`main.py`中的引脚配置
4. 运行`main.py`开始测试

---

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @File    : main.py
# @Description : PN532 NFC模块测试主程序

# 导入必要模块
from machine import Pin, UART
import time
from uart import PN532_UART

# 配置UART和引脚
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
rst_pin = Pin(15, Pin.OUT)

# 初始化PN532模块
nfc = PN532_UART(uart, rst_pin, debug=False)

def main():
    print("PN532 NFC模块测试程序")
    
    # 唤醒模块
    if not nfc.wake_up():
        print("无法连接到PN532模块")
        return
    
    # 获取固件版本
    version = nfc.get_firmware_version()
    if version:
        print(f"固件版本: {version}")
    else:
        print("获取固件版本失败")
        return
    
    # 配置SAM
    nfc.sam_configuration()
    print("等待NFC卡片...")
    
    try:
        while True:
            # 检测卡片
            uid = nfc.read_passive_target()
            if uid:
                print(f"发现卡片 UID: {[hex(i) for i in uid]}")
                
                # 这里可以添加卡片读写操作代码
                
                time.sleep(2)
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("程序已停止")

if __name__ == "__main__":
    main()
```
---

## 注意事项
### 通信问题
- 确保 UART 波特率与模块一致（默认通常为 115200）
- 过长的杜邦线可能导致通信不稳定
- 避免与其他 UART 设备共用同一总线

### 卡片兼容性
- Mifare Classic 4K 卡片需要特殊处理扇区结构
- NTAG2XX 系列卡片有不同的页大小和容量
- 部分加密卡片需要密钥才能读写数据

### 电源要求
- 建议使用 3.3V 稳定电源
- 模块在读写操作时电流会增大，确保电源能提供足够电流

### 使用环境
- 避免金属环境影响 NFC 信号
- 卡片与模块距离建议保持在 5cm 以内
- 高温高湿环境可能影响模块性能





---

## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：https://github.com/leezisheng

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
- **说明** — 代码含参考部分,出现非技术问题和署名作者无关。  
**版权归 FreakStudio 所有。**
