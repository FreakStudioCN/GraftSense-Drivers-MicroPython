# MAX9814 麦克风模块驱动 - MicroPython版本
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
MAX9814 是一款集成自动增益控制（AGC）和低噪声放大器的驻极体电容式麦克风模块，通过模拟信号输出声音强度，具有高灵敏度、低失真、增益可调等特点，广泛应用于声音检测、语音采集、环境噪声监测等场景（如智能家居声音触发、便携式录音设备、工业噪声预警）。

本项目提供基于 MicroPython 的 MAX9814 麦克风模块驱动代码及测试程序，封装了 ADC 信号采样、增益控制、电压转换、声音检测等核心功能，支持多维度数据读取与动态阈值校准，无需关注底层硬件细节，可快速集成到各类声音相关应用中。

> **注意**：该模块输出为模拟信号，依赖 ADC 采样获取数据，采样精度受开发板 ADC 分辨率影响；不适用于高精度语音识别场景，仅支持声音强度检测与基础采集。
---
## 主要功能
- **多维度数据读取**：
  - 读取原始 ADC 值（16 位精度，范围 0~65535），反映声音信号的原始电信号
  - 输出归一化值（0.0~1.0），便于直接映射到控制参数（如 LED 亮度随声音变化）
  - 计算实际电压值（0~参考电压，默认 3.3V），直观体现信号强度
- **硬件控制功能**：
  - 增益切换：支持高/低增益模式（需配置增益控制引脚），适应不同声音强度场景
- **声音检测与校准**：
  - 峰值检测：获取指定采样次数内的最大信号值，用于捕捉突发声音
  - 平均值计算：平滑短时噪声，提高数据稳定性
  - 环境基线校准：自动采集环境噪声平均值，用于动态调整声音检测阈值
  - 阈值触发：判断声音是否超过设定阈值，输出布尔值（True=检测到声音，False=安静）
- **状态管理**：
  - 聚合返回模块完整状态（启用状态、增益模式、当前读数、电压等）
  - 支持参数合法性校验（如采样次数、增益控制引脚配置），抛出明确错误提示
- **跨平台兼容**：仅依赖 MicroPython 标准库（`machine.ADC`、`machine.Pin`、`time`），经 Raspberry Pi Pico 验证，兼容多数支持 MicroPython 的开发板

---
## 硬件要求
### 推荐测试硬件
- 支持 MicroPython 的开发板（如 Raspberry Pi Pico/Pico W、ESP32）
- MAX9814 麦克风模块（带 AGC 功能，默认增益模式可选）
- 杜邦线（至少 4 根，用于电源、地、信号、控制引脚连接）
- （可选）面包板（用于临时接线测试，避免焊接）

### 模块引脚说明
MAX9814 模块核心引脚为 5 个，部分模块可能省略冗余引脚，关键功能引脚及连接要求如下：

| MAX9814 引脚 | 功能描述 | 连接说明 |
|--------------|----------|----------|
| VCC          | 电源正极 | 连接开发板 3.3V 或 5V 引脚（模块兼容 2.7V~5.5V 供电） |
| GND          | 电源负极 | 连接开发板 GND 引脚，必须与开发板共地 |
| OUT          | 信号输出 | 连接开发板 ADC 输入引脚（如 Pico 的 GP26/ADC0），输出模拟声音信号 |
| GAIN         | 增益控制 | 可选引脚，连接开发板 GPIO 输出引脚（如 Pico 的 GP15），高电平=高增益，低电平=低增益 |
| SHDN         | 关断控制 | 可选引脚，连接开发板 GPIO 输出引脚，高电平=启用模块，低电平=禁用模块（低功耗模式） |

> **关键说明**：GAIN 和 SHDN 为可选引脚，若不使用增益切换或关断功能，可悬空；但悬空时模块默认处于高增益或启用状态（具体取决于模块硬件设计），需参考模块手册确认。

---
## 文件说明
### max9814_mic.py（核心驱动文件）
实现 MAX9814 麦克风模块的核心驱动逻辑，仅包含 `MAX9814Mic` 类，专注于信号读取、硬件控制与数据处理，不涉及硬件引脚初始化（由应用层统一管理 ADC 与 GPIO 实例）。

`MAX9814Mic` 类的核心结构与方法作用如下：
- **属性**：
  - `_adc`：绑定的 ADC 实例（外部传入），用于采集 OUT 引脚的模拟声音信号
  - `_gain_pin`：增益控制引脚对象（可选，外部传入），用于切换高/低增益
  - `_shdn_pin`：关断控制引脚对象（可选，外部传入），用于启用/禁用模块
  - `_high_gain`：当前增益状态（布尔值，无增益控制时为 None），True=高增益，False=低增益
  - `_enabled`：模块启用状态（布尔值），True=启用，False=禁用

- **方法**：
  - `__init__(adc: ADC, gain_pin: Pin = None, shdn_pin: Pin = None)`：初始化驱动，传入 ADC 实例及可选的增益/关断控制引脚；若配置增益引脚则默认设为低增益，若配置关断引脚则默认启用模块，无控制引脚时对应功能不可用。
  - `read() -> int`：读取 ADC 原始采样值（0~65535），直接返回声音信号的原始电信号，不做任何转换。
  - `read_normalized() -> float`：将原始 ADC 值归一化为 0.0~1.0 的比例，基于 16 位 ADC 分辨率计算，便于标准化控制。
  - `read_voltage(vref: float = 3.3) -> float`：计算声音信号对应的实际电压值，公式为“原始值 / 65535 × 参考电压”，默认参考电压 3.3V，可根据开发板供电调整。
  - `enable() -> None`：启用模块，仅当配置 `_shdn_pin` 时有效，通过设置引脚高电平实现；无关断引脚时模块始终启用。
  - `disable() -> None`：禁用模块（低功耗模式），仅当配置 `_shdn_pin` 时有效，通过设置引脚低电平实现；无关断引脚时无法禁用。
  - `set_gain(high: bool) -> None`：切换增益模式，`high=True` 设为高增益，`high=False` 设为低增益；仅当配置 `_gain_pin` 时有效，无增益引脚时抛出 `RuntimeError`。
  - `get_state() -> dict`：聚合返回模块完整状态，字典包含“启用状态（enabled）、增益模式（high_gain）、是否支持增益控制（has_gain_control）、是否支持关断（has_shdn_control）、当前原始值（current_reading）、当前电压（current_voltage）”，方便一次获取多参数。
  - `get_average_reading(samples: int = 10) -> int`：计算指定采样次数内的平均 ADC 值，默认 10 次采样，用于平滑短时噪声，采样次数需大于 0，否则抛出 `ValueError`。
  - `get_peak_reading(samples: int = 100) -> int`：获取指定采样次数内的最大 ADC 值（峰值），默认 100 次采样，用于捕捉突发声音（如拍手、说话），采样次数需大于 0，否则抛出 `ValueError`。
  - `detect_sound_level(threshold: int = 35000, samples: int = 50) -> bool`：检测声音是否超过设定阈值，默认阈值 35000、采样 50 次；若任一采样值超过阈值则返回 True（检测到声音），否则返回 False（安静）；采样次数需大于 0，否则抛出 `ValueError`。
  - `calibrate_baseline(samples: int = 100) -> int`：校准环境噪声基线，通过采集指定次数（默认 100 次）的平均 ADC 值作为基线，用于动态调整声音检测阈值（如阈值=基线+5000），采样次数需大于 0，否则抛出 `ValueError`。


### main.py（测试程序文件）
MAX9814 麦克风模块的功能测试程序，无自定义类，包含 3 个测试函数与 1 个辅助函数，覆盖模块核心功能：
- **辅助函数**：
  - `get_formatted_time() -> str`：返回格式化时间字符串（HH:MM:SS），用于日志打印时标记时间戳。
- **测试函数**：
  - `test_basic_reading() -> None`：基础读取测试，初始化 ADC 实例（默认 GP26/ADC0），循环读取并打印原始值、归一化值、电压值，持续约 10 秒，支持 Ctrl+C 退出。
  - `test_with_gain_control() -> None`：增益控制测试，配置增益控制引脚（默认 GP15），先切换为低增益模式采样 50 次，再切换为高增益模式采样 50 次，对比不同增益下的信号值差异。
  - `test_sound_detection() -> None`：声音检测测试，自动校准环境噪声基线，设置阈值=基线+5000，实时检测声音是否超过阈值，打印检测结果（安静/声音）及当前值、峰值，支持持续运行直到手动退出。
- **主程序逻辑**：打印测试模式选择提示，默认调用 `test_sound_detection()`，可通过注释切换测试函数（`test_basic_reading()`/`test_with_gain_control()`）。

---
## 软件设计核心思想
### 模块化与职责分离
- 将数据读取（`read()`/`read_voltage()`）、硬件控制（`set_gain()`/`enable()`）、数据处理（`get_average_reading()`/`calibrate_baseline()`）拆分为独立方法，通过 `get_state()` 聚合调用，便于维护与扩展（如后续增加滤波功能）。
- 驱动仅负责信号处理与硬件控制逻辑，不初始化 ADC 与 GPIO 实例（由应用层传入），减少硬件耦合，兼容不同开发板的引脚配置。

### 模拟信号处理适配
- 基于 MAX9814 的模拟信号输出特性，采用 ADC 采样获取声音强度，通过 16 位 ADC 分辨率（0~65535）确保采样精度，同时提供归一化与电压转换接口，满足不同场景的数据需求（如控制场景用归一化值，计量场景用电压值）。
- 增益控制逻辑适配模块硬件设计：高电平对应高增益（适合弱声音采集），低电平对应低增益（适合强声音采集），无增益引脚时明确抛出错误，避免无效操作。

### 实用性与鲁棒性平衡
- 提供声音检测与基线校准功能：通过 `calibrate_baseline()` 自动适应不同环境噪声（如安静房间 vs 嘈杂车间），`detect_sound_level()` 支持自定义阈值，提高检测灵活性。
- 参数合法性校验：所有涉及采样次数的方法（如 `get_average_reading()`）均检查采样次数是否大于 0，无控制引脚时调用对应功能（如 `set_gain()`）抛出明确错误，便于问题排查。

### 跨平台兼容设计
- 仅依赖 MicroPython 标准库，不使用平台专属 API（如 Pico 特有的 ADC 函数），通过 `machine.ADC` 与 `machine.Pin` 抽象硬件接口，兼容 ESP32、Pico 等主流开发板。
- 参考电压可自定义（`read_voltage()` 的 `vref` 参数），适配不同开发板的 ADC 供电（如 3.3V 开发板用 3.3V，5V 开发板用 5.0V）。

---
## 使用说明
### 硬件接线（树莓派 Pico 示例）
以“使用增益控制、不使用关断控制”为例，接线如下（若无需增益控制，可省略 GAIN 引脚连接）：

| MAX9814 引脚 | Pico GPIO 引脚 | 接线功能 |
|--------------|----------------|----------|
| VCC          | 3.3V（Pin36） | 模块电源输入 |
| GND          | GND（Pin38） | 接地，与开发板共地 |
| OUT          | GP26/ADC0（Pin31） | 声音信号采样输入 |
| GAIN         | GP15（Pin20） | 增益控制引脚（输出） |
| SHDN         | 悬空 | 不使用关断功能 |

> **注意：**
> - 模块 VCC 可接 3.3V 或 5V，若接 5V，需确保 ADC 输入电压不超过开发板 ADC 最大耐压（通常 3.3V），部分 MAX9814 模块 OUT 引脚输出电压会随 VCC 变化，需确认模块手册（多数模块 OUT 输出范围为 0~VCC）。
> - 若使用 5V 供电且 ADC 耐压 3.3V，需在 OUT 引脚与 ADC 引脚之间串联分压电阻（如 1kΩ+2kΩ 分压，确保输入 ADC 电压不超过 3.3V），避免烧毁 ADC 模块。

---
### 软件依赖
- **固件版本**：MicroPython v1.23+  
- **内置库**：
  - `machine`：用于 ADC 实例创建、GPIO 控制
  - `time`：用于延时、时间戳获取
- **开发工具**：Thonny、PyCharm（带 MicroPython 插件）

---
### 安装步骤
1. **烧录固件**：将 MicroPython v1.23+ 固件烧录到开发板（如 Raspberry Pi Pico），参考 [MicroPython 官方文档](https://datasheets.raspberrypi.com/pico/getting-started-with-micropython.pdf)。
2. **硬件接线**：按上述接线图连接 MAX9814 模块与开发板，确保引脚接触良好（面包板测试建议使用短杜邦线，减少信号干扰）。
3. **文件上传**：通过开发工具将 `max9814_mic.py` 和 `main.py` 上传到开发板文件系统。
4. **配置修改**：根据实际接线修改 `main.py` 中的引脚参数（如 ADC 引脚、增益控制引脚），例如：
   - 若 ADC 接 GP27/ADC1，修改 `adc = ADC(27)`
   - 若增益控制接 GP14，修改 `gain_pin = Pin(14, Pin.OUT)`
5. **选择测试模式**：在 `main.py` 主程序中，通过注释/取消注释选择测试函数（`test_basic_reading()`/`test_with_gain_control()`/`test_sound_detection()`）。
6. **运行测试**：执行 `main.py`，根据选择的测试模式观察串口输出（如声音检测测试中，对着麦克风说话，观察是否打印“SOUND!”）。

---
## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28
# @Author  : 缪贵成
# @File    : main.py
# @Description : MAX9814麦克风驱动简化测试

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, ADC
from max9814_mic import MAX9814Mic

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def get_formatted_time() -> str:
    """
    获取格式化时间字符串 (HH:MM:SS)。

    Returns:
        str: 格式化后的时间字符串。

    Notes:
        使用 time.localtime() 获取本地时间。
        适用于日志打印。

    ==========================================

    Get formatted time string (HH:MM:SS).

    Returns:
        str: Formatted time string.

    Notes:
        Uses time.localtime().
        Useful for log printing.
    """
    # 获取当前本地时间元组
    t = time.localtime()
    # 格式化输出时分秒
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])

def test_basic_reading() -> None:
    """
    基本读取测试：连续打印原始值、归一化值和电压。

    Raises:
        KeyboardInterrupt: 用户中断时退出。

    Notes:
        默认使用 GP26 (ADC0)。
        循环运行约 10 秒。
    ==========================================

    Basic reading test: print raw, normalized, and voltage.

    Raises:
        KeyboardInterrupt: On user interrupt.

    Notes:
        Uses GP26 (ADC0).
        Runs ~10 seconds.
    """
    # 初始化配置
    time.sleep(3)
    print("FreakStudio:max9814_mic_driver test start")
    print("=== Basic Reading Test ===")
    # GP26 = ADC0 输入
    adc = ADC(26)

    # 初始化麦克风实例
    mic = MAX9814Mic(adc=adc)

    print("Microphone initialized on ADC0 (GP26)")
    # 打印模块状态
    print("State:", mic.get_state())
    print("Reading values for ~10 seconds...")

    try:
        # 每 0.1 秒一次，总共 10 秒
        for i in range(100):
            # 原始 ADC 值
            raw_value = mic.read()
            # 归一化值 (0–1)
            normalized = mic.read_normalized()
            # 电压值 (V)
            voltage = mic.read_voltage()
            print("[{}] Raw:{:5d} | Norm:{:.3f} | Volt:{:.3f}V".format(
                get_formatted_time(), raw_value, normalized, voltage
            ))
            # 延时 0.5 秒
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[{}] Basic test interrupted".format(get_formatted_time()))

def test_with_gain_control() -> None:
    """
    增益控制测试：切换低增益和高增益模式并采样。

    Raises:
        KeyboardInterrupt: 用户中断时退出。

    Notes:
        GP15 用于控制增益。
        低增益模式先运行，再切换到高增益模式。

    ==========================================

    Gain control test: switch low/high gain modes.

    Raises:
        KeyboardInterrupt: On user interrupt.

    Notes:
        GP15 controls gain pin.
        Runs low gain first, then high gain.
    """
    # 初始化配置
    time.sleep(3)
    print("FreakStudio:max9814_mic_driver test start")
    print("=== Basic Reading Test ===")
    # GP26 = ADC0 输入
    adc = ADC(26)

    # 初始化GP15 作为增益控制引脚
    gain_pin = Pin(15, Pin.OUT)
    mic = MAX9814Mic(adc=adc, gain_pin=gain_pin)
    try:
        # 低增益模式
        print("=== LOW GAIN mode ===")
        mic.set_gain(False)  # 设置为低增益
        print("State:", mic.get_state())
        for i in range(50):
            print("[LOW] {:5d}".format(mic.read()), end=" ")
            if (i + 1) % 5 == 0:  # 每 5 个值换行
                print()
            time.sleep(0.6)

        # 高增益模式
        print("\n=== HIGH GAIN mode ===")
        mic.set_gain(True)  # 设置为高增益
        print("State:", mic.get_state())
        for i in range(50):
            print("[HIGH]{:5d}".format(mic.read()), end=" ")
            if (i + 1) % 5 == 0:
                print()
            time.sleep(0.6)

    except KeyboardInterrupt:
        print("\n[{}] Gain test interrupted".format(get_formatted_time()))

def test_sound_detection() -> None:
    """
    声音检测测试：基于阈值判断环境是否有声音。
    Raises:
        KeyboardInterrupt: 用户中断时退出。
    Notes:
        自动校准环境噪声基线。
        阈值 = 基线 + 5000。
        检测结果实时打印。

    ==========================================

    Sound detection test: detect sound above threshold.

    Raises:
        KeyboardInterrupt: On user interrupt.

    Notes:
        Calibrates baseline automatically.
        Threshold = baseline + 5000.
        Prints detection results.
    """
    # 初始化配置
    time.sleep(3)
    print("FreakStudio:max9814_mic_driver test start")
    print("=== Basic Reading Test ===")
    # GP26 = ADC0 输入
    adc = ADC(26)

    # 初始化麦克风实例
    mic = MAX9814Mic(adc=adc)
    print("Calibrating baseline noise level...")
    # 获取环境噪声平均值
    baseline = mic.calibrate_baseline(samples=200)
    # 设置阈值
    threshold = baseline + 5000
    print("Baseline:", baseline)
    print("Threshold:", threshold)
    print("Make some noise near the mic! (Ctrl+C to stop)")

    try:
        # 计数器，记录静音周期
        silent_count = 0
        while True:
            # 当前读数
            current_value = mic.read()
            # 检测是否超阈值
            is_sound = mic.detect_sound_level(threshold=threshold, samples=10)
            if is_sound:
                # 获取峰值
                peak = mic.get_peak_reading(samples=20)
                print("[{}] SOUND! Current:{} Peak:{}".format(
                    get_formatted_time(), current_value, peak
                ))
                silent_count = 0
            else:
                silent_count += 1
                # 每检测 50 次安静，打印一次状态
                if silent_count % 50 == 0:
                    print("[{}] Silent... Current:{} (Th:{})".format(
                        get_formatted_time(), current_value, threshold
                    ))
            time.sleep(0.6)
    except KeyboardInterrupt:
        print("\n[{}] Detection stopped".format(get_formatted_time()))

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================

print("MAX9814 Microphone Simplified Test Suite")
print("Choose test mode by editing code:")
print("1. Basic reading test")
print("2. Gain control test")
print("3. Sound detection test")
time.sleep(5)

try:
    # 修改下面的函数调用来选择测试模式
    # test_basic_reading()
    # test_with_gain_control()
    test_sound_detection()
except Exception as e:
    print("Error:", e)

```
---
## 注意事项
#### 信号干扰
- 声音信号为微弱模拟信号（幅值通常仅几十到几百毫伏），极易受电磁干扰（如电机、继电器、高频振荡电路）影响，导致读数跳变或噪声增大。需注意：
  1. ADC 信号线（OUT 引脚到开发板 ADC 引脚）需使用短而粗的导线（如 24AWG 杜邦线），长度控制在 10cm 以内；
  2. 信号线需远离干扰源（如电机驱动线路、无线模块天线），避免平行走线；
  3. 必要时可在信号线外层包裹铝箔屏蔽层，屏蔽层仅单端（靠近开发板端）接地，避免形成地环流引入新干扰。
#### 增益匹配
- 低增益模式（GAIN 引脚接低电平）：适合强声音环境（如工厂车间、马路旁），可避免高强度声音导致 ADC 采样值饱和（固定为 65535）；
- 高增益模式（GAIN 引脚接高电平）：适合弱声音环境（如安静卧室、办公室），可提高模块对微弱声音的检测灵敏度；
- 若未配置 GAIN 引脚（悬空），模块默认增益可能为高增益（具体取决于硬件设计），强声音下易出现采样值饱和，需参考模块手册通过修改板载电阻调整默认增益（如更换增益配置电阻阻值）。
### 硬件接线与配置注意事项
#### 共地要求
- MAX9814 的 GND 引脚必须与开发板 GND 引脚 **可靠共地**，否则模拟信号会因电平漂移导致读数异常（如无声音时 ADC 值忽高忽低、有声音时信号无规律波动）。建议：
  1. 使用单独的 GND 导线连接模块与开发板，不与大功率设备（如电机、LED 阵列）共用 GND 线路；
  2. 面包板测试时，优先选择靠近开发板电源接口的 GND 插孔，减少地阻差异。

#### 接线可靠性
- 模块引脚（尤其是 OUT、GAIN、SHDN）引脚较细（通常为 2.0mm 间距排针），面包板测试时需确保引脚完全插入插孔，避免因接触不良导致：
  1. 信号中断（如 OUT 引脚虚接，ADC 读数固定为 0 或最大值）；
  2. 控制失效（如 GAIN 引脚虚接，增益模式无法切换）。
- 长期使用或嵌入式项目中，建议将模块引脚焊接杜邦线或端子座，提高接线稳定性。

#### ADC 引脚选择
- 需确认开发板的 ADC 专用引脚（如 Raspberry Pi Pico 的 GP26~GP28 为 ADC0~ADC2，ESP32 的 GPIO32~GPIO39 为 ADC 引脚），**不可将普通 GPIO 引脚作为 ADC 输入**：
  1. 普通 GPIO 无 ADC 采样电路，无法读取模拟信号；
  2. 部分开发板的 GPIO 虽支持 ADC，但可能存在精度低、噪声大等问题（如 ESP32 的 GPIO2 虽支持 ADC，但受射频干扰影响较大）。

### 软件使用建议
#### 采样间隔与频率
- 建议采样间隔 ≥0.05 秒：频繁采样（如间隔 <0.01 秒）会导致 CPU 资源占用过高（MicroPython 单线程环境下可能阻塞其他任务），同时增加电源消耗；
- 不同场景采样间隔推荐：
  1. 声音检测场景（如触发式报警）：0.1~0.5 秒，兼顾实时性与资源消耗；
  2. 环境噪声监测场景：1~2 秒，减少数据冗余；
- 若需提高采样频率（如高速声音波形采集），需减少单次采样次数（如 `get_average_reading(samples=5)` 而非默认 10 次），避免平均计算阻塞主线程，同时需关闭不必要的后台任务（如日志打印、无线通信）。

### 环境影响
#### 温度与湿度
- 模块最佳工作温度为 **-10℃~60℃**：
  1. 高温环境（>60℃）会导致内部运算放大器漂移，增益稳定性下降，声音信号精度降低；
  2. 低温环境（<-10℃）会使驻极体麦克风的电容性能劣化，灵敏度显著降低，甚至无法输出有效信号；
- 高湿环境（相对湿度 >85% RH）需为模块添加防潮外壳（如亚克力外壳、防水透气膜），防止空气中的水汽进入模块内部，导致引脚氧化、电路受潮短路或麦克风振膜霉变。

#### 声学环境
- 避免在强回声环境（如空旷大厅、金属容器内）使用：回声会与原始声音叠加，导致声音检测误触发（如无实际声源时检测到“声音”），可通过在环境内增加吸音材料（如海绵、地毯）减少回声；
- 麦克风拾音方向存在指向性（通常为正面拾音灵敏度最高，侧面和背面较低），需将模块的拾音孔（通常为板载麦克风的圆形开孔）朝向声音来源方向，避免被导线、外壳、元器件遮挡拾音孔，导致灵敏度下降或声音信号衰减。
---
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/leezisheng](https://github.com/leezisheng)  
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