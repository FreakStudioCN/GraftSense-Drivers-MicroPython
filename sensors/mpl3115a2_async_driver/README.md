# A MicroPython library to control mpl3115a2_driver  — MicroPython 异步驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [异步设计与使用](#异步设计与使用)
- [API Async Matrix](#api-async-matrix)
- [Source Demo to Async Demo Mapping](#source-demo-to-async-demo-mapping)
- [超时、取消、并发与残余阻塞](#超时取消并发与残余阻塞)
- [Hardware Acceptance](#hardware-acceptance)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

`mpl3115a2_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/mpl3115a2_driver`。

## 主要功能

- 可解析的公开类：`MPL3115A2`, `MPL3115A2Async`, `MPL3115A2exception`, `MPL3115A2exceptionAsync`, `SyncAdapterMixin`。
- 可解析的公开调用入口：18 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, Pin( |
| 示例 GPIO | 示例未声明固定 GPIO 编号 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.1` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/main.cpython-313.pyc
├── code/__pycache__/mpl3115a2.cpython-313.pyc
├── code/main.py
├── code/mpl3115a2.py
├── code/mpl3115a2_async.py
├── examples/main_sync.py
├── LICENSE
└── package.json
```

## 文件说明

- `code/`：实际发布的运行时 Python 模块；以 `package.json.urls` 为安装映射依据。
- `code/main.py`（若存在）：异步演示入口，不是默认发布运行时映射。
- `examples/`（若存在）：同步保真基线或额外示例，不应当作安装后的运行时模块。
- `package.json`、`LICENSE`：发布元数据和许可证的唯一事实来源。

## 快速开始

1. 按 `package.json.urls` 将运行时文件复制到设备；不要把 `examples/` 当作运行时依赖。
2. 按上文硬件/运行环境配置总线、GPIO、网络或凭证。
3. 使用包内真实 `code/main.py` 的 import 与构造方式运行。以下是当前文件逐字读取的异步入口；部署时请保留 `try/finally` 并调用对象实际提供的 `deinit()` 或 `aclose()`。

```python
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2026/3/12 下午4:00
    # @Author  : PinsonJonas
    # @File    : main.py
    # @Description : MPL3115A2传感器测试 读取气压海拔温度 异常处理演示

    # ======================================== 导入相关模块 =========================================

    from machine import I2C, Pin
    from mpl3115a2 import MPL3115A2, MPL3115A2exception

    # ======================================== 全局变量 ============================================

    # I2C配置（Raspberry Pi Pico专属）
    I2C_BUS = 0  # Pico的I2C总线编号
    I2C_SCL_PIN = 5  # I2C时钟引脚
    I2C_SDA_PIN = 4  # I2C数据引脚
    I2C_FREQ = 400000  # MPL3115A2支持的400kHz高速I2C频率
    # MPL3115A2传感器参数
    MPL3115A2_ADDR = 0x60  # 传感器默认I2C地址
    SAMPLING_INTERVAL = 0.6  # 最小采样间隔（需大于传感器512ms的采样时间）
    LONG_MONITOR_DURATION = 10  # 长期监测总时长(秒)
    LONG_MONITOR_INTERVAL = 2  # 长期监测采样间隔(秒)

    # ======================================== 功能函数 ============================================


    def init_i2c():
        """
        初始化I2C总线（适配Raspberry Pi Pico硬件）
        Initialize I2C bus (adapted for Raspberry Pi Pico hardware)

        Args:
            None

        Returns:
            I2C: 初始化成功返回I2C对象；初始化失败返回None
            I2C: Return I2C object if initialization succeeds; return None if fails

        Notes:
            1. 仅适配Raspberry Pi Pico的I2C0总线，如需使用I2C1需修改引脚（SCL=15, SDA=14）
            2. 初始化时会扫描I2C总线上的设备，并检查MPL3115A2默认地址是否存在
            1. Only adapted for I2C0 bus of Raspberry Pi Pico, modify pins (SCL=15, SDA=14) if using I2C1
            2. Scan I2C bus devices during initialization and check if MPL3115A2 default address exists
        """
        try:
            # 初始化Pico的I2C0总线
            i2c = I2C(I2C_BUS, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
            detected_devices = [hex(addr) for addr in i2c.scan()]
            print(f"I2C initialization successful, detected device addresses: {', '.join(detected_devices)}")

            # 检查MPL3115A2传感器是否存在
            if hex(MPL3115A2_ADDR) not in detected_devices:
                print("Warning: MPL3115A2 sensor not detected (default address 0x60)")
                return None
            return i2c
        except Exception as e:
            print(f"I2C initialization failed: {e}")
            return None


    def print_separator(title):
        """
        打印分隔符，优化输出可读性
        Print separator to optimize output readability

        Args:
            title (str): 分隔符标题/演示模块名称
            title (str): Separator title / demonstration module name

        Returns:
            None

        Notes:
            输出格式为65个等号组成的分隔线，中间显示传入的标题文本
            Output format is a separator line composed of 65 equal signs with the incoming title text in the middle
        """
        print("\n" + "=" * 65)
        print(f"=== {title}")
        print("=" * 65)


    def safe_measure(func, desc="measurement"):
        """
        安全执行测量函数，捕获各类异常并返回结果状态
        Safely execute measurement function, catch all types of exceptions and return result status

        Args:
            func (function): 要执行的测量函数（如mpl.pressure/mpl.altitude/mpl.temperature）
            func (function): Measurement function to execute (e.g. mpl.pressure/mpl.altitude/mpl.temperature)
            desc (str): 测量操作描述文本，用于异常提示（默认值：measurement）
            desc (str): Measurement operation description text for exception prompt (default: measurement)

        Returns:
            tuple: (测量结果, 执行状态)
                   - 执行成功：(测量数值, True)
                   - 执行失败：(None, False)
            tuple: (measurement result, execution status)
                   - Success: (measurement value, True)
                   - Failure: (None, False)

        Notes:
            1. 捕获MPL3115A2传感器专属异常、I2C通信异常、通用异常
            2. 所有异常信息均以英文输出，便于调试定位问题
            1. Catch MPL3115A2 sensor-specific exceptions, I2C communication exceptions, and general exceptions
            2. All exception information is output in English for easy debugging and problem location
        """
        try:
            result = func()
            return result, True
        except MPL3115A2exception as e:
            print(f"   {desc} failed - sensor exception: {e}")
        except OSError as e:
            if "EIO" in str(e):
                print(f"   {desc} failed - I2C communication error(Errno 5): {e}")
            else:
                print(f"   {desc} failed - I2C error: {e}")
        except Exception as e:
            print(f"   {desc} failed - unknown error: {e}")
        return None, False


    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ===========================================

    await asyncio.sleep(3)
    print("FreakStudio: MPL3115A2 sensor test - read pressure/altitude/temperature with exception handling")
    # 初始化I2C总线
    i2c = init_i2c()
    if not i2c:
        print("I2C initialization failed, program exit")
        raise SystemExit(1)

    # ========================================  主程序  ============================================

    # 1. 气压计模式功能演示
    print_separator("1. Pressure mode demonstration")
    try:
        # 初始化气压模式传感器对象
        mpl_pressure = MPL3115A2(i2c, mode=MPL3115A2.PRESSURE)
        print("   MPL3115A2 pressure mode initialized successfully")

        # 连续5次气压+温度测量
        print("\n   5 consecutive pressure + temperature measurements:")
        for i in range(5):
            pressure, p_ok = safe_measure(mpl_pressure.pressure, "pressure reading")
            temp, t_ok = safe_measure(mpl_pressure.temperature, "temperature reading")

            if p_ok and t_ok:
                pressure_kpa = pressure / 4000.0  # 转换为kPa（原始值精度0.25Pa）
                print(f"     Measurement {i+1} - Pressure: {pressure_kpa:.2f} kPa | Temperature: {temp:.2f} °C")
            await asyncio.sleep(SAMPLING_INTERVAL)

        # 测试错误场景：气压模式下读取海拔（预期触发异常）
        print("\n   Test error scenario: Read altitude in pressure mode (expected exception):")
        alt, a_ok = safe_measure(mpl_pressure.altitude, "altitude reading")

    except MPL3115A2exception as e:
        print(f"   Pressure mode initialization failed: {e}")
    except Exception as e:
        print(f"   Pressure mode operation failed: {e}")

    # 2. 海拔模式功能演示
    print_separator("2. Altitude mode demonstration")
    try:
        # 初始化海拔模式传感器对象
        mpl_altitude = MPL3115A2(i2c, mode=MPL3115A2.ALTITUDE)
        print("   MPL3115A2 altitude mode initialized successfully")

        # 连续5次海拔+温度测量
        print("\n   5 consecutive altitude + temperature measurements:")
        for i in range(5):
            altitude, a_ok = safe_measure(mpl_altitude.altitude, "altitude reading")
            temp, t_ok = safe_measure(mpl_altitude.temperature, "temperature reading")

            if a_ok and t_ok:
                print(f"     Measurement {i+1} - Altitude: {altitude:.2f} m | Temperature: {temp:.2f} °C")
            await asyncio.sleep(SAMPLING_INTERVAL)

        # 测试错误场景：海拔模式下读取气压（预期触发异常）
        print("\n   Test error scenario: Read pressure in altitude mode (expected exception):")
        press, p_ok = safe_measure(mpl_altitude.pressure, "pressure reading")

    except MPL3115A2exception as e:
        print(f"   Altitude mode initialization failed: {e}")
    except Exception as e:
        print(f"   Altitude mode operation failed: {e}")

    # 3. 传感器异常处理演示
    print_separator("3. Sensor exception handling demonstration")
    # 测试无效模式初始化（预期触发异常）
    print("   Test error scenario: Initialize with invalid mode (expected exception):")
    try:
        mpl_invalid = MPL3115A2(i2c, mode=99)  # 传入无效模式值
    except MPL3115A2exception as e:
        print(f"   Expected exception caught: {e}")
    except Exception as e:
        print(f"   Unexpected exception caught: {e}")

    # 4. 长期监测功能演示
    print_separator("4. Long-term monitoring demonstration (10 seconds, 2s interval)")
    try:
        # 重新初始化气压计模式用于长期监测
        mpl_monitor = MPL3115A2(i2c, mode=MPL3115A2.PRESSURE)
        print(f"   Start {LONG_MONITOR_DURATION}s long-term monitoring (pressure + temperature):")

        start_time = time.time()
        while (time.time() - start_time) < LONG_MONITOR_DURATION:
            pressure, p_ok = safe_measure(mpl_monitor.pressure, "pressure reading")
            temp, t_ok = safe_measure(mpl_monitor.temperature, "temperature reading")

            if p_ok and t_ok:
                pressure_kpa = pressure / 4000.0
                current_time = time.localtime()
                time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
                print(f"     [{time_str}] Pressure: {pressure_kpa:.2f} kPa | Temperature: {temp:.2f} °C")

            await asyncio.sleep(LONG_MONITOR_INTERVAL)

    except Exception as e:
        print(f"   Long-term monitoring failed: {e}")

    # 程序结束提示
    print_separator("Demonstration completed")
    print("   All MPL3115A2 function demonstrations finished")

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `MPL3115A2.altitude` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MPL3115A2.pressure` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MPL3115A2.temperature` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MPL3115A2Async.altitude_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MPL3115A2Async.pressure_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MPL3115A2Async.temperature_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `altitude` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `altitude_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `init_i2c` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `pressure` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `pressure_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_separator` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `safe_measure` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `temperature` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `temperature_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `code/main.py` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

## 超时、取消、并发与残余阻塞

任何 `await` 不会自动使底层 I2C/SPI/UART/Pin 操作变为非阻塞。取消时应停止后台任务并在 `finally` 释放资源；没有实现超时参数的 API 不应被假定具有超时。协议命令、帧界限、ACK、静默间隔及错误含义只以当前实现和源示例可证明的内容为准。



## Hardware Acceptance

| Level | Evidence | Not covered |
|---|---|---|
| Link | 未实测：仅完成静态代码与文档取证。 | 总线/网络连接、设备身份响应。 |
| Basic function | 未实测。 | 一次真实业务 API 成功及结果正确性。 |
| Complete business flow | 未实测。 | 端到端设备、对端、供电、时序和异常恢复。 |

## 注意事项

| 类别 | 说明 |
|---|---|
| 并发 | 同一硬件实例应由调用方串行化；UART 额外遵守其并发契约。 |
| 阻塞 | 不把短同步总线访问或严格时序脉冲描述为真正可中断。 |
| 验收 | 文档生成不等于硬件验证；接入真实设备后分别记录三层验收证据。 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| `1.0.1` | 2026-09-17 | leeqingshui | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：leeqingshui。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
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
