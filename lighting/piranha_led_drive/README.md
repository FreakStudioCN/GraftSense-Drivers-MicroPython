# GraftSense 食人鱼 LED 灯模块 (MicroPython)

# GraftSense 食人鱼 LED 灯模块驱动 (MicroPython)

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

本项目为 **GraftSense Piranha LED module v1.1** 提供了完整的 MicroPython 驱动支持，可用于控制共阳极或共阴极连接方式的食人鱼 LED 灯模块。驱动采用面向对象设计，支持 LED 的点亮、熄灭、状态翻转及状态查询，同时提供清晰的异常处理机制，适用于树莓派 Pico 等 MicroPython 设备，可广泛应用于电子 DIY、创客互动、趣味装饰等场景。

---

## 主要功能

- ✅ 支持共阴极（高电平点亮）和共阳极（低电平点亮）两种 LED 连接方式
- ✅ 提供 `on()`、`off()`、`toggle()` 等核心控制方法
- ✅ 支持查询 LED 当前点亮状态（`is_on()`）
- ✅ 内置参数校验与异常捕获，提升代码健壮性
- ✅ 遵循 Grove 接口标准，兼容主流开发板

---

## 硬件要求

1. **核心硬件**：GraftSense Piranha LED module v1.1 食人鱼 LED 灯模块（三极管驱动电路）
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico 或其他 MicroPython 设备）
3. **接线配件**：Grove 4Pin 线（用于连接模块与开发板）
4. **电源**：3.3V / 5V 稳定电源（模块兼容 3.3V 和 5V 供电）

---

## 文件说明

---

## 软件设计核心思想

1. **单一职责原则**：`PiranhaLED` 类仅负责 LED 控制，不耦合其他业务逻辑
2. **显式依赖注入**：Pin 对象由外部传入或通过引脚号创建，提升可测试性
3. **最小副作用**：构造函数不执行硬件操作，避免阻塞与意外行为
4. **逻辑与 I/O 分离**：通过 `_calculate_output` 函数封装电平计算逻辑，与硬件操作解耦
5. **清晰异常策略**：对 GPIO 操作进行异常捕获，抛出明确的 `RuntimeError` 便于调试
6. **兼容设计**：通过极性常量支持共阳极 / 共阴极两种硬件连接方式，提升灵活性

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `piranha_led.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线将 LED 模块的 `DOUT` 引脚连接至开发板指定 GPIO 引脚（如示例中的 GPIO 6）
- 连接 `GND` 和 `VCC` 引脚，确保供电稳定

### 代码配置

- 在 `main.py` 中修改 `LED_PIN` 为实际连接的 GPIO 引脚号
- 根据 LED 连接方式设置 `IS_ANODE`：`True` 表示共阳极，`False` 表示共阴极

### 运行测试

- 重启开发板，`main.py` 将自动执行，LED 会进行闪烁和翻转演示

---

## 示例程序

```python
# 导入驱动模块
from piranha_led import PiranhaLED, POLARITY_CATHODE, POLARITY_ANODE
import time

# 初始化LED（GPIO 6，共阴极）
led = PiranhaLED(pin_number=6, polarity=POLARITY_CATHODE)

try:
    # 闪烁3次
    for _ in range(3):
        led.on()
        time.sleep(1)
        led.off()
        time.sleep(1)
    
    # 翻转状态
    led.toggle()  # 点亮
    time.sleep(1)
    led.toggle()  # 熄灭

finally:
    led.off()  # 确保安全退出
```

---

## 注意事项

1. **硬件极性**：共阳极 LED 需将 `polarity` 设为 `POLARITY_ANODE`，共阴极设为 `POLARITY_CATHODE`，否则 LED 状态与预期相反
2. **引脚选择**：避免使用开发板上已占用的特殊功能引脚（如 UART、I2C 引脚），防止冲突
3. **电源保护**：模块通过三极管驱动 LED，无需额外限流电阻，但需确保供电电压在 3.3V-5V 范围内
4. **异常处理**：生产环境中建议完善异常日志记录，便于排查问题
5. **用户中断**：`main.py` 中已处理 `KeyboardInterrupt`，可通过 Ctrl+C 安全终止程序

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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
