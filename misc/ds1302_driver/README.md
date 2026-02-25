# DS1302闹钟系统（基于SSD1306 OLED）
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

本项目基于MicroPython开发，通过DS1302实时时钟芯片实现高精度时间管理，结合SSD1306 I2C接口OLED屏幕完成时间可视化显示，并搭配蜂鸣器实现闹钟提醒功能。项目适用于ESP32、ESP8266、RP2040等支持MicroPython的单片机，核心目标是提供一套轻量化、模块化的实时时钟+闹钟解决方案，可快速移植到各类嵌入式物联网项目中。

## 主要功能

1. 从DS1302芯片读取/设置年、月、日、星期、时、分、秒等时间信息；
2. 控制DS1302时钟的启停，支持掉电后时间保持（需外接备用电池）；
3. 在128x64分辨率的SSD1306 OLED屏幕上居中显示日期、时间及闹钟提醒；
4. 支持设置/删除多个闹钟，到达指定时间触发蜂鸣器报警；
5. 支持OLED屏幕对比度调整、反相显示、屏幕开关等基础控制；
6. 通过软件定时器周期性刷新屏幕显示，保证时间实时性；
7. 封装硬件驱动层，提供简洁的API接口，降低二次开发成本。

## 硬件要求

| 硬件模块                | 规格/参数                          | 接线说明（参考）                     |
|-------------------------|------------------------------------|--------------------------------------|
| 主控单片机              | 支持MicroPython（ESP32/ESP8266/RP2040） | -                                    |
| DS1302实时时钟模块      | 三线接口（CLK/DIO/CS）             | CLK→Pin10、DIO→Pin11、CS→Pin12       |
| SSD1306 OLED屏幕        | I2C接口、128x64分辨率              | SDA→Pin6、SCL→Pin7、VCC→3.3V、GND→GND |
| 蜂鸣器                  | 无源蜂鸣器（PWM控制）              | 控制引脚→Pin9、VCC→3.3V、GND→GND     |
| 辅助配件                | 杜邦线、5V/3.3V电源、DS1302备用电池 | -                                    |

## 文件说明

| 文件名       | 功能说明                                                                 |
|--------------|--------------------------------------------------------------------------|
| `SSD1306.py` | 封装SSD1306 OLED屏幕驱动，继承`framebuf.FrameBuffer`，实现I2C通信、屏幕初始化、显示刷新、对比度调整、反相显示等功能 |
| `ds1302.py`  | 封装DS1302实时时钟芯片驱动，实现时钟启停、时间读写、BCD码与十进制转换、RAM寄存器操作等功能                     |
| `main.py`    | 主程序入口，整合DS1302和SSD1306驱动，实现闹钟管理（设置/删除/触发）、屏幕显示刷新、蜂鸣器控制等核心业务逻辑     |

## 软件设计核心思想

1. **模块化设计**：将硬件驱动（DS1302、SSD1306）与业务逻辑（闹钟、显示）解耦，驱动层专注硬件通信，业务层专注功能实现，便于维护和扩展；
2. **面向对象封装**：通过类封装硬件操作细节，对外提供简洁API（如`ds1302.date_time()`读写时间、`alarm_clock.set_alarm()`设置闹钟）；
3. **定时器驱动**：使用软件定时器周期性读取时间并刷新OLED，避免主循环阻塞，保证显示实时性；
4. **分层架构**：
   - 底层：硬件驱动层（DS1302/SSD1306类），负责与硬件的底层通信；
   - 中层：功能层（AlarmClock类），负责闹钟的管理和触发逻辑；
   - 应用层：主程序，整合各模块完成完整业务流程；
5. **数据格式适配**：针对DS1302内部BCD码存储格式，通过`_dec2hex/_hex2dec`方法完成十进制与十六进制的转换，适配用户交互习惯。

## 使用说明

### 1. 环境准备

- 为目标单片机烧录MicroPython固件（参考对应硬件的官方烧录教程）；
- 通过Thonny/mpremote等工具将`SSD1306.py`、`ds1302.py`、`main.py`上传到单片机。

### 2. 硬件接线

按照【硬件要求】中的接线说明完成DS1302、OLED、蜂鸣器与单片机的连接，确保电源和地线连接稳定。

### 3. 初始化DS1302时间

首次使用需将单片机内置RTC时间同步到DS1302，步骤如下：

1. 连接单片机到电脑，打开REPL终端；
2. 执行以下代码：

   ```python
   from machine import Pin, RTC
   from ds1302 import DS1302
   rtc = RTC()
   year, month, day, weekday, hour, minute, second, _ = rtc.datetime()
   ds1302 = DS1302(clk=Pin(10), dio=Pin(11), cs=Pin(12))
   ds1302.date_time([year, month, day, weekday, hour, minute, second])
   ```

### 4. 配置并运行程序

- 修改`main.py`中`alarm_clock.set_alarm(18, 3)`的参数，设置目标闹钟时间（小时、分钟）；
- 重启单片机，程序自动运行，OLED屏幕显示当前时间，到达闹钟时间后蜂鸣器触发。

## 示例程序

以下是核心功能示例代码（简化版）：

```python
# 导入核心模块
from machine import Pin, I2C, Timer, PWM
from ds1302 import DS1302
from SSD1306 import SSD1306_I2C

# 初始化DS1302
ds1302 = DS1302(clk=Pin(10), dio=Pin(11), cs=Pin(12))

# 初始化I2C和OLED
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)
oled = SSD1306_I2C(i2c, 0x3c, 128, 64, False)

# 初始化闹钟（蜂鸣器Pin9）
class AlarmClock:
    def __init__(self, oled, buzzer_pin):
        self.oled = oled
        self.buzzer = PWM(buzzer_pin, freq=1000, duty_u16=0)
        self.alarms = []
    def set_alarm(self, hours, minutes):
        if 0<=hours<=23 and 0<=minutes<=59:
            self.alarms.append((hours, minutes))
    def check_alarms(self, current_time):
        ch, cm = current_time[4], current_time[5]
        for (h, m) in self.alarms:
            if h == ch and m == cm:
                self.buzzer.duty_u16(32000)
                self.oled.text("Alarm!", 0, 48)
                return True
        self.buzzer.duty_u16(0)
        return False

alarm_clock = AlarmClock(oled, Pin(9))
alarm_clock.set_alarm(18, 3)  # 设置18:03的闹钟

# 定时器刷新显示
def display_time(timer):
    current_time = ds1302.date_time()
    oled.fill(0)
    # 显示标题
    oled.text("RTC Clock", (128 - 6*8)//2, 0)
    # 显示日期
    date_str = f"{current_time[0]:04}-{current_time[1]:02}-{current_time[2]:02}"
    oled.text(date_str, (128 - len(date_str)*8)//2, 16)
    # 显示时间
    time_str = f"{current_time[4]:02}:{current_time[5]:02}:{current_time[6]:02}"
    oled.text(time_str, (128 - len(time_str)*8)//2, 32)
    # 检查闹钟
    alarm_clock.check_alarms(current_time)
    oled.show()

# 启动定时器（100ms刷新一次）
timer = Timer(-1)
timer.init(period=100, mode=Timer.PERIODIC, callback=display_time)

# 主循环
while True:
    pass
```

## 注意事项

1. DS1302时间初始化：首次使用必须同步时间，否则显示的时间可能异常；
2. I2C地址适配：SSD1306 OLED的I2C地址通常为0x3c或0x3d，程序会自动扫描总线，若未检测到设备需检查接线；
3. 引脚兼容性：不同单片机的引脚定义不同，需根据硬件调整`main.py`中DS1302、OLED、蜂鸣器的引脚号；
4. DS1302电源：建议为DS1302模块接备用电池，防止掉电后时间丢失；
5. 蜂鸣器适配：若使用有源蜂鸣器，需修改`AlarmClock`类中蜂鸣器的控制逻辑（直接使用GPIO高低电平，而非PWM）；
6. 参数合法性：设置闹钟时，小时需在0-23范围内，分钟需在0-59范围内，否则会抛出`ValueError`；
7. 定时器周期：默认100ms刷新一次显示，可根据性能需求调整，过小的周期可能导致单片机资源占用过高。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：<liqinghsui@freakstudio.cn>  
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
