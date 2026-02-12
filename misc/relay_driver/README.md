# 目录/MENU

* [中文部分](#单通道继电器控制库-RelayController-MicroPython版本)
* [English Section](#Single-Channel-Relay-Control-Library-RelayController-MicroPython-Version)

---

## **单通道继电器控制库 RelayController MicroPython版本**

`RelayController` 库旨在提供在 MicroPython 环境下对单通道继电器的简洁且高效的控制方案，支持普通单线圈继电器（normal）和双稳态磁保持继电器（latching）两种类型，并提供开（on）、关（off）、切换（toggle）和状态查询等方法。

### **主要特性**

* **双类型支持**：同时兼容普通继电器和磁保持继电器，无需额外代码切换
* **简单易用 API**：`on()`, `off()`, `toggle()`, `get_state()`, `deinit()` 五个核心方法
* **非阻塞脉冲控制**：磁保持继电器采用短脉冲驱动，避免长时间通电
* **状态跟踪**：内置 `_last_state` 记录，方便查询和切换
* **资源释放**：`deinit()` 可安全复位定时器和引脚，确保设备断电状态安全

### **文件说明**

* **`main.py`**: 包含 `RelayController` 类的完整实现及示例用法注释

### **安装与依赖**

1. 将 `main.py` 拷贝到 MicroPython 设备文件系统中
2. 确保固件版本为 MicroPython v1.23.0 或更高
3. 依赖模块：`machine.Pin`, `machine.Timer`

### **用法示例**

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/28 下午3:00
# @Author  : 李清水
# @File    : main.py
# @Description : 继电器测试例程

# ======================================== 导入相关模块 ========================================

# 导入时间相关的模块
import time
# 导入继电器模块
from relay import RelayController

# ======================================== 全局变量 ============================================

# 继电器配置：在XIAO-RP2040开发板上
# 如果是 'normal' 类型继电器，使用GP29
RELAY_TYPE = 'normal'   # 'normal' 或 'latching'
RELAY_PIN1 = 27           # 控制引脚1
RELAY_PIN2 = 28           # 控制引脚2（磁保持继电器需要）
RELAY_PIN3 = 29           # 控制引脚3

# 音乐节奏定义 (单位：毫秒)
# 每个元组表示 (持续时间, 是否在结束时切换)
MUSIC_NOTES = [
    # 前奏强节奏
    (50, True), (50, False), (50, True), (50, False),  # 快速连续4拍
    (100, True), (100, False),  # 放慢2拍
    (50, True), (50, False), (50, True), (50, False),  # 重复快速4拍

    # 主歌部分
    (150, True), (50, True), (200, False),  # 重-轻-长停顿
    (100, True), (100, True), (100, True), (100, False),  # 连续三连击
    (80, True), (80, True), (160, False),  # 双拍+长停顿
    (60, True), (60, True), (60, True), (60, True), (120, False),  # 快速四连击

    # 副歌高潮
    (40, True), (40, False), (40, True), (40, False),  # 超高速8分音符
    (40, True), (40, False), (40, True), (40, False),
    (200, True), (200, False),  # 强重拍
    (300, True), (100, True), (200, False),  # 长-短组合

    # 桥段变速
    (120, True), (80, True), (120, True), (80, False),
    (200, True), (50, True), (50, True), (200, False),

    # 结尾渐慢
    (150, True), (150, False),
    (200, True), (200, False),
    (300, True), (300, False)
]
# ======================================== 功能函数 ============================================

# 简易音乐播放函数
def play_relay_music():
    for duration, should_toggle in MUSIC_NOTES:
        # 切换继电器状态
        relay.toggle()
        time.sleep_ms(duration)
        if should_toggle:
            # 再次切换回来
            relay.toggle()
            # 添加小间隔防止连续切换太快
            time.sleep_ms(50)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio: Using ESP32 WiFi to control relay")

# 初始化继电器控制器
if RELAY_TYPE == 'latching':
    relay = RelayController(RELAY_TYPE, RELAY_PIN1, RELAY_PIN2)
else:
    relay = RelayController(RELAY_TYPE, RELAY_PIN3)

# ========================================  主程序  ===========================================

# 打开继电器
relay.on()
# 延时1s
time.sleep(1)
# 关闭继电器
relay.off()

# 继电器开合音乐
while True:
    print("Playing relay music...")
    play_relay_music()
    # 每段音乐间隔1秒
    time.sleep(1)
```

### **注意事项**

* **引脚配置**：请确认 `pin1` 和 `pin2` 对应正确的 GPIO 编号
* **磁保持定时**：默认脉冲时长为 50ms，可根据继电器规格自行调整
* **电源安全**：操作前请确保继电器电源与主控电压匹配，并做好隔离保护

## 联系开发者
- 如有任何问题或需要帮助，请通过 [10696531183@qq.com](mailto:10696531183@qq.com) 联系开发者。
![FreakStudio_Contact](../../../image/FreakStudio_Contact.png)

### **作者与许可**

* **作者**: 李清水 / Freak
* **版权**: Copyright 2025 Lee Qingshui / Freak

**协议**: 本作品采用 **Creative Commons Attribution-NonCommercial 4.0 International License** 许可。您不得将本作品用于商业目的。您必须适当署名、提供许可链接，并说明是否对作品进行了修改。您应以合理方式进行，但不得以任何暗示许可方赞同您或您的使用的方式进行。

要查看本许可协议的副本，请访问：
[https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/)

---

## Single-Channel Relay Control Library RelayController MicroPython Version

The `RelayController` library provides a concise and efficient solution for controlling single-channel relays in MicroPython. It supports both standard single-coil relays (`normal`) and bistable latching relays (`latching`), offering methods for turning on (`on()`), turning off (`off()`), toggling (`toggle()`), querying state (`get_state()`), and resource cleanup (`deinit()`).

### **Key Features**

* **Dual Relay Support**: Seamlessly handle normal and latching relays with the same API
* **Straightforward API**: Core methods include `on()`, `off()`, `toggle()`, `get_state()`, and `deinit()`
* **Non-Blocking Pulse Control**: Short pulse drive for latching relays avoids continuous energizing
* **State Tracking**: Internal `_last_state` variable for reliable toggling and state queries
* **Resource Cleanup**: Safe deinitialization of timers and pins via `deinit()` ensures hardware safety

### **File Overview**

* **`main.py`**: Contains the full implementation of the `RelayController` class and usage examples

### **Installation & Dependencies**

1. Copy `main.py` into the MicroPython device filesystem
2. Ensure your firmware version is MicroPython v1.23.0 or newer
3. Dependencies: `machine.Pin`, `machine.Timer`

### **Usage Example**

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/28 下午3:00
# @Author  : 李清水
# @File    : main.py
# @Description : 继电器测试例程

# ======================================== 导入相关模块 ========================================

# 导入时间相关的模块
import time
# 导入继电器模块
from relay import RelayController

# ======================================== 全局变量 ============================================

# 继电器配置：在XIAO-RP2040开发板上
# 如果是 'normal' 类型继电器，使用GP29
RELAY_TYPE = 'normal'   # 'normal' 或 'latching'
RELAY_PIN1 = 27           # 控制引脚1
RELAY_PIN2 = 28           # 控制引脚2（磁保持继电器需要）
RELAY_PIN3 = 29           # 控制引脚3

# 音乐节奏定义 (单位：毫秒)
# 每个元组表示 (持续时间, 是否在结束时切换)
MUSIC_NOTES = [
    # 前奏强节奏
    (50, True), (50, False), (50, True), (50, False),  # 快速连续4拍
    (100, True), (100, False),  # 放慢2拍
    (50, True), (50, False), (50, True), (50, False),  # 重复快速4拍

    # 主歌部分
    (150, True), (50, True), (200, False),  # 重-轻-长停顿
    (100, True), (100, True), (100, True), (100, False),  # 连续三连击
    (80, True), (80, True), (160, False),  # 双拍+长停顿
    (60, True), (60, True), (60, True), (60, True), (120, False),  # 快速四连击

    # 副歌高潮
    (40, True), (40, False), (40, True), (40, False),  # 超高速8分音符
    (40, True), (40, False), (40, True), (40, False),
    (200, True), (200, False),  # 强重拍
    (300, True), (100, True), (200, False),  # 长-短组合

    # 桥段变速
    (120, True), (80, True), (120, True), (80, False),
    (200, True), (50, True), (50, True), (200, False),

    # 结尾渐慢
    (150, True), (150, False),
    (200, True), (200, False),
    (300, True), (300, False)
]
# ======================================== 功能函数 ============================================

# 简易音乐播放函数
def play_relay_music():
    for duration, should_toggle in MUSIC_NOTES:
        # 切换继电器状态
        relay.toggle()
        time.sleep_ms(duration)
        if should_toggle:
            # 再次切换回来
            relay.toggle()
            # 添加小间隔防止连续切换太快
            time.sleep_ms(50)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio: Using ESP32 WiFi to control relay")

# 初始化继电器控制器
if RELAY_TYPE == 'latching':
    relay = RelayController(RELAY_TYPE, RELAY_PIN1, RELAY_PIN2)
else:
    relay = RelayController(RELAY_TYPE, RELAY_PIN3)

# ========================================  主程序  ===========================================

# 打开继电器
relay.on()
# 延时1s
time.sleep(1)
# 关闭继电器
relay.off()

# 继电器开合音乐
while True:
    print("Playing relay music...")
    play_relay_music()
    # 每段音乐间隔1秒
    time.sleep(1)
```

### **Notes**

* **Pin Configuration**: Ensure `pin1` and `pin2` correspond to correct GPIO numbers
* **Pulse Timing**: Default pulse period is 50ms; adjust as needed for different relay specs
* **Power Safety**: Verify relay coil voltage matches MCU power supply and use appropriate isolation

## Contact the Developer
- For any inquiries or assistance, feel free to contact the developer at [10696531183@qq.com](mailto:10696531183@qq.com).
![FreakStudio_Contact](../../../image/FreakStudio_Contact.png)

### **Author & License**

* **Author**: Lee Qingshui / Freak
* **Copyright**: Copyright 2025 Lee Qingshui / Freak

**License**: This work is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License**. You may not use the material for commercial purposes. You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.

To view a copy of this license, visit:
[https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/)