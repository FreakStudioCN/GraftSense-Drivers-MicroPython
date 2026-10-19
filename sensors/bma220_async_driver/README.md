# Async conversion of bma220_driver — MicroPython 异步驱动

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

`bma220_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/bma220_driver`。

## 主要功能

- 可解析的公开类：`BMA220`, `BMA220_LOWG_DETECTION`, `BMA220_ORIENTATION`, `BMA220_SLOPE`, `BMA220_TAP`, `CBits`, `RegisterStruct`。
- 可解析的公开调用入口：86 个（详见 API 矩阵）。
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
| 包版本 | `1.0.0` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/main.cpython-313.pyc
├── code/main.py
├── code/_gs_bma220_micropython_bma220/__init__.py
├── code/_gs_bma220_micropython_bma220/__pycache__/__init__.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/__pycache__/bma220.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/__pycache__/bma220_const.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/__pycache__/bma220_lowg_detection.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/__pycache__/bma220_orientation.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/__pycache__/bma220_slope.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/__pycache__/bma220_tap_sensing.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/__pycache__/i2c_helpers.cpython-313.pyc
├── code/_gs_bma220_micropython_bma220/bma220.py
├── code/_gs_bma220_micropython_bma220/bma220_const.py
├── code/_gs_bma220_micropython_bma220/bma220_lowg_detection.py
├── code/_gs_bma220_micropython_bma220/bma220_orientation.py
├── code/_gs_bma220_micropython_bma220/bma220_slope.py
├── code/_gs_bma220_micropython_bma220/bma220_tap_sensing.py
├── code/_gs_bma220_micropython_bma220/i2c_helpers.py
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
    # @Time    : 2026/3/16 下午2:00
    # @Author  :
    # @File    : main.py
    # @Description : BMA220加速度传感器多功能测试程序，支持量程、双击检测、滤波器带宽等功能测试
    
    
    # ======================================== 导入相关模块 =========================================
    
    
    # 导入时间模块，用于延时操作
    # 导入机器模块中的Pin和I2C类，用于硬件引脚和I2C通信控制
    from machine import Pin, I2C
    
    # 导入BMA220传感器相关驱动模块
    from _gs_bma220_micropython_bma220 import bma220
    from _gs_bma220_micropython_bma220 import bma220_tap_sensing
    from _gs_bma220_micropython_bma220 import bma220_const as bma220_cnst
    from _gs_bma220_micropython_bma220 import bma220_lowg_detection
    from _gs_bma220_micropython_bma220 import bma220_orientation
    from _gs_bma220_micropython_bma220 import bma220_slope
    
    
    # ======================================== 全局变量 ============================================
    
    
    # BMA220标准I2C地址范围，0x0A对应CSB引脚接VDDIO，0x0B对应CSB引脚接GND，覆盖所有硬件配置
    TARGET_SENSOR_ADDRS = {0x0A, 0x0B}
    # RP2040开发板I2C0总线的SCL引脚编号
    I2C_SCL_PIN = 5
    # RP2040开发板I2C0总线的SDA引脚编号
    I2C_SDA_PIN = 4
    # I2C通信频率，设置为400000Hz（400KHz）
    I2C_FREQ = 400000
    # 初始化传感器状态标记，用于判断是否成功初始化BMA220
    sensor_initialized = False
    # 存储找到的BMA220设备地址
    found_addr = None
    
    # ======================================== 功能函数 ============================================
    
    
    def test_acc_range() -> None:
        """
        测试BMA220加速度传感器的量程设置功能，遍历所有支持的量程并输出加速度数据
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会循环输出X/Y/Z三轴加速度数据，每次输出间隔0.5秒，每个量程测试10次
    
        ==========================================
        Test the acceleration range setting function of BMA220 sensor, traverse all supported ranges and output acceleration data
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, X/Y/Z three-axis acceleration data will be output cyclically, with an interval of 0.5 seconds for each output, and each range is tested 10 times
        """
        # 打印测试开始提示信息
        print("\n=== Start testing acceleration range ===")
        # 初始化BMA220传感器实例
        bma = bma220.BMA220(i2c_bus)
        # 设置初始加速度量程为16g
        bma.acc_range = bma220.ACC_RANGE_16
    
        try:
            # 无限循环测试所有量程
            while True:
                await asyncio.sleep_ms(0)
                # 遍历所有支持的加速度量程
                for acc_range in bma220.acc_range_values:
                    # 打印当前量程设置
                    print(f"Current acceleration range setting: {bma.acc_range}")
                    # 每个量程测试10次
                    for _ in range(10):
                        # 获取X/Y/Z三轴加速度数据
                        accx, accy, accz = bma.acceleration
                        # 打印格式化的加速度数据
                        print(f"x:{accx:.2f}m/s², y:{accy:.2f}m/s², z:{accz:.2f}m/s²")
                        # 延时0.5秒
                        await asyncio.sleep(0.5)
                    # 设置下一个加速度量程
                    bma.acc_range = acc_range
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Acceleration range test stopped ===")
    
    
    def test_tap_sensing() -> None:
        """
        测试BMA220传感器的双击检测功能，配置相关参数并实时输出中断触发状态
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会每0.5秒输出一次双击中断触发状态，需敲击传感器触发检测
    
        ==========================================
        Test the double tap detection function of BMA220 sensor, configure relevant parameters and output interrupt trigger status in real time
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, the double tap interrupt trigger status is output every 0.5 seconds, and the sensor needs to be tapped to trigger detection
        """
        # 打印测试开始提示信息
        print("\n=== Start testing double tap sensing ===")
        # 初始化BMA220双击检测功能实例
        bma = bma220_tap_sensing.BMA220_TAP(i2c_bus)
    
        # 配置双击检测参数：设置锁存模式为1秒
        bma.latched_mode = bma220_cnst.LATCH_FOR_1S
        # 启用X轴双击检测
        bma.tt_x_enabled = bma220_tap_sensing.TT_X_ENABLED
        # 启用Y轴双击检测
        bma.tt_y_enabled = bma220_tap_sensing.TT_Y_ENABLED
        # 启用Z轴双击检测
        bma.tt_z_enabled = bma220_tap_sensing.TT_Z_ENABLED
        # 设置双击检测时长为500毫秒
        bma.tt_duration = bma220_tap_sensing.TIME_500MS
    
        try:
            # 无限循环输出双击中断状态
            while True:
                await asyncio.sleep_ms(0)
                # 打印双击中断触发状态
                print(f"Double Tap Interrupt Triggered: {bma.tt_interrupt}")
                # 延时0.5秒
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Double tap sensing test stopped ===")
    
    
    def test_filter_bandwidth() -> None:
        """
        测试BMA220传感器的滤波器带宽设置功能，遍历所有带宽并输出加速度数据
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会循环输出X/Y/Z三轴加速度数据，每个带宽配置测试10次，间隔0.5秒
    
        ==========================================
        Test the filter bandwidth setting function of BMA220 sensor, traverse all bandwidths and output acceleration data
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, X/Y/Z three-axis acceleration data will be output cyclically, each bandwidth configuration is tested 10 times with an interval of 0.5 seconds
        """
        # 打印测试开始提示信息
        print("\n=== Start testing filter bandwidth ===")
        # 初始化BMA220传感器实例
        bma = bma220.BMA220(i2c_bus)
        # 设置初始滤波器带宽为500Hz
        bma.filter_bandwidth = bma220.ACCEL_500HZ
    
        try:
            # 无限循环测试所有滤波器带宽
            while True:
                await asyncio.sleep_ms(0)
                # 遍历所有支持的滤波器带宽
                for filter_bandwidth in bma220.filter_bandwidth_values:
                    # 打印当前滤波器带宽设置
                    print(f"Current Filter bandwidth setting: {bma.filter_bandwidth}")
                    # 每个带宽测试10次
                    for _ in range(10):
                        # 获取X/Y/Z三轴加速度数据
                        accx, accy, accz = bma.acceleration
                        # 打印格式化的加速度数据
                        print(f"x:{accx:.2f}m/s², y:{accy:.2f}m/s², z:{accz:.2f}m/s²")
                        # 延时0.5秒
                        await asyncio.sleep(0.5)
                    # 设置下一个滤波器带宽
                    bma.filter_bandwidth = filter_bandwidth
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Filter bandwidth test stopped ===")
    
    
    def test_latched_mode() -> None:
        """
        测试BMA220传感器的锁存模式设置功能，遍历所有锁存模式并输出加速度数据
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会循环输出X/Y/Z三轴加速度数据，每个锁存模式测试10次，间隔0.5秒
    
        ==========================================
        Test the latched mode setting function of BMA220 sensor, traverse all latched modes and output acceleration data
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, X/Y/Z three-axis acceleration data will be output cyclically, each latched mode is tested 10 times with an interval of 0.5 seconds
        """
        # 打印测试开始提示信息
        print("\n=== Start testing latched mode ===")
        # 初始化BMA220传感器实例
        bma = bma220.BMA220(i2c_bus)
        # 设置初始锁存模式为2秒
        bma.latched_mode = bma220.LATCH_FOR_2S
    
        try:
            # 无限循环测试所有锁存模式
            while True:
                await asyncio.sleep_ms(0)
                # 遍历所有支持的锁存模式
                for latched_mode in bma220.latched_mode_values:
                    # 打印当前锁存模式设置
                    print(f"Current Latched mode setting: {bma.latched_mode}")
                    # 每个锁存模式测试10次
                    for _ in range(10):
                        # 获取X/Y/Z三轴加速度数据
                        accx, accy, accz = bma.acceleration
                        # 打印格式化的加速度数据
                        print(f"x:{accx:.2f}m/s², y:{accy:.2f}m/s², z:{accz:.2f}m/s²")
                        # 延时0.5秒
                        await asyncio.sleep(0.5)
                    # 设置下一个锁存模式
                    bma.latched_mode = latched_mode
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Latched mode test stopped ===")
    
    
    def test_lowg_detection() -> None:
        """
        测试BMA220传感器的低重力检测功能，配置锁存模式并实时输出中断触发状态
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会每0.5秒输出一次低重力中断触发状态，需使传感器处于低重力状态触发检测
    
        ==========================================
        Test the low gravity detection function of BMA220 sensor, configure latched mode and output interrupt trigger status in real time
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, the low gravity interrupt trigger status is output every 0.5 seconds, and the sensor needs to be in a low gravity state to trigger detection
        """
        # 打印测试开始提示信息
        print("\n=== Start testing low gravity detection ===")
        # 初始化BMA220低重力检测功能实例
        bma = bma220_lowg_detection.BMA220_LOWG_DETECTION(i2c_bus)
        # 设置锁存模式为1秒
        bma.latched_mode = bma220_cnst.LATCH_FOR_1S
    
        try:
            # 无限循环输出低重力中断状态
            while True:
                await asyncio.sleep_ms(0)
                # 打印低重力中断触发状态
                print(f"Low G Interrupt Triggered: {bma.lowg_interrupt}")
                # 延时0.5秒
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Low gravity detection test stopped ===")
    
    
    def test_orientation() -> None:
        """
        测试BMA220传感器的方向检测功能，配置相关参数并实时输出中断触发状态
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会遍历3种方向阻塞模式，每种模式测试50次，每次输出间隔0.1秒
    
        ==========================================
        Test the orientation detection function of BMA220 sensor, configure relevant parameters and output interrupt trigger status in real time
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, 3 orientation blocking modes are traversed, each mode is tested 50 times, and each output interval is 0.1 seconds
        """
        # 打印测试开始提示信息
        print("\n=== Start testing orientation detection ===")
        # 初始化BMA220方向检测功能实例
        bma = bma220_orientation.BMA220_ORIENTATION(i2c_bus)
        # 设置锁存模式为1秒
        bma.latched_mode = bma220_cnst.LATCH_FOR_1S
        # 设置初始方向阻塞模式为MODE1
        bma.orientation_blocking = bma220_orientation.MODE1
    
        try:
            # 无限循环测试所有方向阻塞模式
            while True:
                await asyncio.sleep_ms(0)
                # 遍历3种方向阻塞模式
                for orientation_blocking in (1, 2, 3):
                    # 打印当前方向阻塞模式设置
                    print(f"Current Orientation blocking setting: {bma.orientation_blocking}")
                    # 每种模式测试50次
                    for _ in range(50):
                        # 打印方向中断触发状态
                        print(f"Orientation Interrupt Triggered: {bma.orientation_interrupt}")
                        # 延时0.1秒
                        await asyncio.sleep(0.1)
                    # 设置下一个方向阻塞模式
                    bma.orientation_blocking = orientation_blocking
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Orientation detection test stopped ===")
    
    
    def test_basic_acceleration() -> None:
        """
        测试BMA220传感器的基础加速度数据读取功能，实时输出X/Y/Z三轴加速度数据
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会持续输出加速度数据，每次输出间隔0.5秒，无参数配置修改
    
        ==========================================
        Test the basic acceleration data reading function of BMA220 sensor, output X/Y/Z three-axis acceleration data in real time
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, acceleration data is continuously output, with an interval of 0.5 seconds for each output, and no parameter configuration modification
        """
        # 打印测试开始提示信息
        print("\n=== Start testing basic acceleration reading ===")
        # 初始化BMA220传感器实例
        bma = bma220.BMA220(i2c_bus)
    
        try:
            # 无限循环输出加速度数据
            while True:
                await asyncio.sleep_ms(0)
                # 获取X/Y/Z三轴加速度数据
                accx, accy, accz = bma.acceleration
                # 打印格式化的加速度数据
                print(f"x:{accx:.2f}m/s², y:{accy:.2f}m/s², z:{accz:.2f}m/s²")
                # 延时0.5秒
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Basic acceleration reading test stopped ===")
    
    
    def test_sleep_duration() -> None:
        """
        测试BMA220传感器的睡眠时长设置功能，遍历所有睡眠时长并输出加速度数据
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会循环输出X/Y/Z三轴加速度数据，每个睡眠时长测试10次，间隔0.5秒
    
        ==========================================
        Test the sleep duration setting function of BMA220 sensor, traverse all sleep durations and output acceleration data
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, X/Y/Z three-axis acceleration data will be output cyclically, each sleep duration is tested 10 times with an interval of 0.5 seconds
        """
        # 打印测试开始提示信息
        print("\n=== Start testing sleep duration ===")
        # 初始化BMA220传感器实例
        bma = bma220.BMA220(i2c_bus)
        # 设置初始睡眠时长为10毫秒
        bma.sleep_duration = bma220.SLEEP_10MS
    
        try:
            # 无限循环测试所有睡眠时长
            while True:
                await asyncio.sleep_ms(0)
                # 遍历所有支持的睡眠时长
                for sleep_duration in bma220.sleep_duration_values:
                    # 打印当前睡眠时长设置
                    print(f"Current Sleep duration setting: {bma.sleep_duration}")
                    # 每个睡眠时长测试10次
                    for _ in range(10):
                        # 获取X/Y/Z三轴加速度数据
                        accx, accy, accz = bma.acceleration
                        # 打印格式化的加速度数据
                        print(f"x:{accx:.2f}m/s², y:{accy:.2f}m/s², z:{accz:.2f}m/s²")
                        # 延时0.5秒
                        await asyncio.sleep(0.5)
                    # 设置下一个睡眠时长
                    bma.sleep_duration = sleep_duration
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Sleep duration test stopped ===")
    
    
    def test_slope_sign() -> None:
        """
        测试BMA220传感器的斜率符号设置功能，配置相关参数并实时输出斜率中断信息
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会遍历所有斜率符号，每个符号测试10次，输出斜率中断状态和三轴斜率信息
    
        ==========================================
        Test the slope sign setting function of BMA220 sensor, configure relevant parameters and output slope interrupt information in real time
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, all slope signs are traversed, each sign is tested 10 times, and the slope interrupt status and three-axis slope information are output
        """
        # 打印测试开始提示信息
        print("\n=== Start testing slope sign ===")
        # 初始化BMA220斜率检测功能实例
        bma = bma220_slope.BMA220_SLOPE(i2c_bus)
    
        # 配置斜率检测参数：设置锁存模式为1秒
        bma.latched_mode = bma220_cnst.LATCH_FOR_1S
        # 启用X轴斜率检测
        bma.slope_x_enabled = bma220_slope.SLOPE_X_ENABLED
        # 启用Y轴斜率检测
        bma.slope_y_enabled = bma220_slope.SLOPE_Y_ENABLED
        # 启用Z轴斜率检测
        bma.slope_z_enabled = bma220_slope.SLOPE_Z_ENABLED
        # 设置初始斜率符号为负
        bma.slope_sign = bma220_slope.SLOPE_SIGN_NEGATIVE
        # 设置斜率阈值为8
        bma.slope_threshold = 8
    
        try:
            # 无限循环测试所有斜率符号
            while True:
                await asyncio.sleep_ms(0)
                # 遍历所有支持的斜率符号
                for slope_sign in bma220_slope.slope_sign_values:
                    # 打印当前斜率符号设置
                    print(f"Current Slope sign setting: {bma.slope_sign}")
                    # 每个斜率符号测试10次
                    for _ in range(10):
                        # 打印斜率中断触发状态
                        print(f"Slope Interrupt Triggered: {bma.slope_interrupt}")
                        # 获取X/Y/Z三轴斜率中断信息
                        infox, infoy, infoz = bma.slope_interrupt_info
                        # 打印三轴斜率信息
                        print(f"Slope x:{infox}, y:{infoy}, z:{infoz}")
                        # 延时0.5秒
                        await asyncio.sleep(0.5)
                    # 设置下一个斜率符号
                    bma.slope_sign = slope_sign
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== Slope sign test stopped ===")
    
    
    def test_slope_x() -> None:
        """
        测试BMA220传感器的X轴斜率检测功能，配置相关参数并实时输出中断触发状态
        Args:
            无
    
        Raises:
            KeyboardInterrupt: 当用户按下Ctrl+C时触发，用于停止测试
    
        Notes:
            测试过程中会每0.5秒输出一次X轴斜率中断触发状态，仅启用X轴斜率检测
    
        ==========================================
        Test the X-axis slope detection function of BMA220 sensor, configure relevant parameters and output interrupt trigger status in real time
        Args:
            None
    
        Raises:
            KeyboardInterrupt: Triggered when the user presses Ctrl+C to stop the test
    
        Notes:
            During the test, the X-axis slope interrupt trigger status is output every 0.5 seconds, and only X-axis slope detection is enabled
        """
        # 打印测试开始提示信息
        print("\n=== Start testing X-axis slope detection ===")
        # 初始化BMA220斜率检测功能实例
        bma = bma220_slope.BMA220_SLOPE(i2c_bus)
        # 设置锁存模式为2秒
        bma.latched_mode = bma220_cnst.LATCH_FOR_2S
        # 启用X轴斜率检测
        bma.slope_x_enabled = bma220_slope.SLOPE_X_ENABLED
    
        try:
            # 无限循环输出X轴斜率中断状态
            while True:
                await asyncio.sleep_ms(0)
                # 打印斜率中断触发状态
                print(f"Slope Interrupt Triggered: {bma.slope_interrupt}")
                # 延时0.5秒
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            # 打印测试停止提示信息
            print("\n=== X-axis slope detection test stopped ===")
    
    
    def main_menu() -> None:
        """
        程序主菜单，提供BMA220传感器各功能测试的选择入口，支持用户交互选择测试项
        Args:
            无
    
        Raises:
            ValueError: 当用户输入非数字字符时触发，提示输入错误
            Exception: 当测试过程中出现未知错误时触发，输出错误信息
    
        Notes:
            用户输入0退出程序，输入1-10选择对应测试项，输入其他内容提示无效
    
        ==========================================
        Program main menu, providing selection entry for each function test of BMA220 sensor, supporting user interactive selection of test items
        Args:
            None
    
        Raises:
            ValueError: Triggered when the user enters non-numeric characters, prompting input error
            Exception: Triggered when an unknown error occurs during the test, outputting error information
    
        Notes:
            The user enters 0 to exit the program, 1-10 to select the corresponding test item, and other inputs to prompt invalid
        """
        # 定义主菜单提示文本
        menu = """
    ====================================
    BMA220 Function Test Menu
    Please enter the corresponding number to select the test function:
    1 - Acceleration Range Test
    2 - Double Tap Sensing Test
    3 - Filter Bandwidth Test
    4 - Latched Mode Test
    5 - Low Gravity Detection Test
    6 - Orientation Detection Test
    7 - Basic Acceleration Reading
    8 - Sleep Duration Test
    9 - Slope Sign Test
    10 - X-axis Slope Detection Test
    0 - Exit Program
    ====================================
    """
        # 无限循环显示主菜单
        while True:
            await asyncio.sleep_ms(0)
            # 打印主菜单
            print(menu)
            try:
                # 获取用户输入的选择
                choice = int(input("Please enter your selection (0-10): "))
                # 判断用户选择
                if choice == 0:
                    # 打印程序退出提示
                    print("Program exited")
                    # 退出循环
                    break
                elif choice == 1:
                    # 执行加速度量程测试
                    test_acc_range()
                elif choice == 2:
                    # 执行双击检测测试
                    test_tap_sensing()
                elif choice == 3:
                    # 执行滤波器带宽测试
                    test_filter_bandwidth()
                elif choice == 4:
                    # 执行锁存模式测试
                    test_latched_mode()
                elif choice == 5:
                    # 执行低重力检测测试
                    test_lowg_detection()
                elif choice == 6:
                    # 执行方向检测测试
                    test_orientation()
                elif choice == 7:
                    # 执行基础加速度读取测试
                    test_basic_acceleration()
                elif choice == 8:
                    # 执行睡眠时长测试
                    test_sleep_duration()
                elif choice == 9:
                    # 执行斜率符号测试
                    test_slope_sign()
                elif choice == 10:
                    # 执行X轴斜率检测测试
                    test_slope_x()
                else:
                    # 打印输入无效提示
                    print("Invalid input, please enter a number between 0 and 10")
            except ValueError:
                # 打印输入错误提示
                print("Input error, please enter a number")
            except Exception as e:
                # 打印运行错误提示
                print(f"Program error: {e}")
    
    
    # ======================================== 自定义类 ============================================
    
    
    # ======================================== 初始化配置 ===========================================
    
    
    # 延时3秒，等待传感器初始化完成
    await asyncio.sleep(3)
    # 打印初始化提示信息
    print("FreakStudio: BMA220 sensor test initialization")
    
    # 初始化I2C总线，使用RP2040的I2C0，指定SCL和SDA引脚，通信频率400KHz
    i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    
    # 扫描I2C总线上的所有设备，返回设备地址列表
    devices_list: list[int] = i2c_bus.scan()
    # 打印I2C扫描开始提示
    print("START I2C SCANNER")
    
    # 检查I2C扫描结果是否为空
    if len(devices_list) == 0:
        # 打印无I2C设备提示
        print("No i2c device !")
        # 抛出系统退出异常，终止程序
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        # 打印找到的I2C设备数量
        print("i2c devices found:", len(devices_list))
        # 打印扫描到的所有I2C设备地址（十六进制）
        print(f"Scanned I2C addresses: {[hex(addr) for addr in devices_list]}")
    
    # 遍历扫描到的所有I2C设备地址
    for device in devices_list:
        # 判断当前地址是否在BMA220标准地址范围内
        if device in TARGET_SENSOR_ADDRS:
            # 记录找到的BMA220地址
            found_addr = device
            # 打印找到的BMA220标准地址
            print(f"Found BMA220 standard address: {hex(found_addr)}")
            try:
                # 初始化BMA220传感器实例，验证通信是否正常
                test_sensor = bma220.BMA220(i2c=i2c_bus)
                # 打印传感器初始化成功提示
                print("Target sensor (BMA220) initialization successful")
                # 标记传感器初始化成功
                sensor_initialized = True
                # 退出地址遍历循环
                break
            except Exception as e:
                # 打印传感器初始化失败提示及错误信息
                print(f"Sensor Initialization failed at address {hex(found_addr)}: {e}")
                # 继续遍历下一个地址
                continue
    # 判断传感器是否初始化成功
    if not sensor_initialized:
        # 抛出异常，提示未找到BMA220传感器
        raise Exception(
            f"No BMA220 sensor found on I2C bus! "
            f"Expected addresses: {[hex(addr) for addr in TARGET_SENSOR_ADDRS]}, "
            f"Scanned addresses: {[hex(addr) for addr in devices_list]}"
        )
    
    
    # ========================================  主程序  ============================================
    
    
    # 程序入口，当直接运行该脚本时执行
    if __name__ == "__main__":
        # 打印程序启动提示信息
        print("BMA220 Multi-function Test Program (RP2040)")
        # 调用主菜单函数
        main_menu()
    

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `BMA220.acc_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.filter_bandwidth` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.latched_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.sleep_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.sleep_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.x_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.y_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220.z_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_LOWG_DETECTION.lowg_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_LOWG_DETECTION.lowg_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_LOWG_DETECTION.lowg_hysteresis` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_LOWG_DETECTION.lowg_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_LOWG_DETECTION.lowg_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_ORIENTATION.orientation_blocking` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_ORIENTATION.orientation_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_ORIENTATION.orientation_exchange` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_ORIENTATION.orientation_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_filter` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_interrupt_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_sign` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_x_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_y_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_SLOPE.slope_z_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.double_tap_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_filter` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_interrupt_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_sign` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_x_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_y_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMA220_TAP.tt_z_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `acc_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `double_tap_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `filter_bandwidth` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `latched_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `lowg_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `lowg_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `lowg_hysteresis` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `lowg_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `lowg_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main_menu` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `orientation_blocking` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `orientation_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `orientation_exchange` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `orientation_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `sleep_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `sleep_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_filter` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_interrupt_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_sign` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_x_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_y_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `slope_z_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_acc_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_basic_acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_filter_bandwidth` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_latched_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_lowg_detection` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_orientation` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_sleep_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_slope_sign` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_slope_x` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_tap_sensing` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_filter` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_interrupt_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_sign` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_x_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_y_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `tt_z_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `x_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `y_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `z_enabled` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | leeqingshui | 基于当前异步代码、来源包和许可证重新取证 README。 |

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
