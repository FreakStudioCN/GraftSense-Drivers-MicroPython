# SSD1306 OLED 显示屏驱动 - MicroPython版本

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
本项目为基于 SSD1306 芯片的 OLED 显示屏 MicroPython 驱动，支持 I2C 通信，提供显示文本、图形、对比度调节、反相显示等功能。适用于各类嵌入式显示场景。

---

## 主要功能
- **文本显示**：支持自定义文本、字符显示
- **图形绘制**：支持点、线、矩形等基本图形
- **对比度调节**：可设置 0-255 级对比度
- **反相显示**：支持正常/反相模式切换
- **多分辨率支持**：兼容 128x64、128x32、64x48 等常见尺寸
- **高兼容性**：适配 MicroPython 标准库

---

## 硬件要求

### 推荐测试硬件
- 树莓派 Pico/Pico W 或其他 MicroPython 兼容开发板
- SSD1306 OLED 显示屏模块（I2C接口）
- 杜邦线若干

### 模块引脚说明
| SSD1306 引脚 | 功能描述         |
|--------------|------------------|
| VCC          | 电源正极（3.3V） |
| GND          | 电源负极         |
| SCL          | I2C 时钟         |
| SDA          | I2C 数据         |

---

## 文件说明

### code/ssd1306.py
SSD1306 显示驱动核心类，提供高层 API（文本、图形、对比度、反相等显示）。
#### 类定义
```python
class SSD1306(framebuf.FrameBuffer):
    """
    SSD1306 OLED 屏幕驱动类，支持文本、图形、对比度调节、反相显示等功能。

    Attributes:
        width (int): 屏幕宽度（像素）。
        height (int): 屏幕高度（像素）。
        external_vcc (bool): 是否使用外部电源。
        buffer (bytearray): 显示数据缓冲区。
        pages (int): 屏幕页数。

    Methods:
        __init__(width, height, external_vcc): 初始化屏幕参数与缓冲区。
        init_display(): 初始化显示设置。
        poweroff(): 关闭显示屏。
        poweron(): 打开显示屏。
        contrast(contrast): 设置对比度（0-255）。
        invert(invert): 设置反相/正常显示。
        show(): 刷新显示内容到屏幕。
        write_cmd(cmd): 发送命令字节。
        write_data(buf): 发送数据字节。
    """

class SSD1306_I2C(SSD1306):
    """
    基于 I2C 的 SSD1306 OLED 屏幕驱动类。

    Attributes:
        i2c (I2C): I2C 总线对象。
        addr (int): 屏幕 I2C 地址。

    Methods:
        __init__(i2c, addr, width, height, external_vcc): 初始化 I2C 接口与屏幕参数。
        write_cmd(cmd): 发送命令字节。
        write_data(buf): 发送数据字节。
    """
```
### code/pcf8574.py
PCF8574 I2C GPIO 扩展芯片驱动，提供端口读写、单引脚控制和翻转功能。

---

## 软件设计核心思想

### 高层 API 封装
- 统一接口，简化显示和绘图操作
- 支持多种显示模式和自定义内容

### 时序精确控制
- 严格遵循 SSD1306 通信协议
- 采用低级 I2C 操作确保兼容性

### 易用性与扩展性
- 对比度、显示内容、图形均可灵活配置
- 便于集成到各类 MicroPython 项目

---

## 使用说明

### 硬件接线（树莓派 Pico 示例）

| SSD1306 引脚 | Pico GPIO 引脚 |
|--------------|----------------|
| VCC          | 3.3V           |
| GND          | GND            |
| SCL          | GP1            |
| SDA          | GP0            |

> **注意：**
> - SCL/SDA 可根据实际需求修改为其他 GPIO
> - 确保电源电压与模块兼容

---

### 软件依赖

- **固件版本**：MicroPython v1.23.0+
- **内置库**：
  - `machine`（I2C 控制）
  - `framebuf`（帧缓冲区）
- **开发工具**：PyCharm 或 Thonny（推荐）

---

### 安装步骤

1. 烧录 MicroPython 固件到开发板
2. 上传 `code/ssd1306.py` 到开发板
3. 根据硬件连接修改初始化参数
4. 运行主程序，观察 OLED 显示效果

---

## 示例程序

```python
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

i2c = I2C(0, scl=Pin(1), sda=Pin(0))
oled = SSD1306_I2C(i2c, addr=0x3C, width=128, height=64, external_vcc=False)

oled.fill(0)
oled.text("Hello SSD1306!", 0, 0)
oled.show()
```

---

## 注意事项
**显示范围限制**
- 显示内容受分辨率限制
- 建议使用 3.3V 供电，避免高温高湿环境

**环境因素**
- 避免强光直射和高湿度

---

## 联系方式
如有问题或建议，请联系开发者：  
📧 邮箱：1098875044@qq.com  
💻 GitHub：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython

---

## 许可协议
本项目除 MicroPython 官方模块外，所有驱动与扩展代码均采用 CC BY-NC 4.0 许可协议发布。  
署名 — 请注明原作者及项目链接  
非商业性使用 — 禁止商业用途  
合理引用 — 可在代码注释、文档等注明来源  
版权归 FreakStudio 所有。