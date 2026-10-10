# ES8311 audio codec I2C configuration driver for MicroPython — MicroPython 异步驱动

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

`es8311_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`signal_acquisition/es8311_driver`。

## 主要功能

- 可解析的公开类：`ES8311`, `ES8311Async`, `ES8311ClockConfig`, `ES8311ClockConfigAsync`, `SyncAdapterMixin`。
- 可解析的公开调用入口：49 个（详见 API 矩阵）。
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
| 作者 | M5Stack Technology CO LTD, FreakStudio |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/es8311.py
├── code/es8311_async.py
├── code/main.py
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
    # @Time    : 2026/07/23
    # @Author  : FreakStudio
    # @File    : main.py
    # @Description : 测试 ES8311 音频编解码器 I2C 配置驱动类
    # @License : MIT

    # ======================================== 导入相关模块 =========================================

    try:
        from micropython import const
    except ImportError:

        def const(value):
            return value


    from machine import I2C, I2S, Pin
    from es8311 import ES8311, ES8311ClockConfig

    # ======================================== 全局变量 ============================================

    # --- 硬件引脚配置常量（请根据实际接线修改）---
    SCL_PIN = const(22)
    SDA_PIN = const(21)
    I2C_FREQ = const(400000)  # I2C 时钟频率（Hz）

    # I2S 音频总线引脚
    I2S_BCK_PIN = const(5)  # I2S 位时钟
    I2S_WS_PIN = const(25)  # I2S 字选择（LRCK）
    I2S_DOUT_PIN = const(26)  # I2S 数据输出（DAC 播放）
    I2S_DIN_PIN = const(35)  # I2S 数据输入（ADC 录音）

    # ES8311 设备地址
    ES8311_I2C_ADDR = const(0x18)

    # ES8311 芯片 ID 寄存器及期望值
    ES8311_CHIP_ID_REG = const(0xFD)
    ES8311_CHIP_ID_EXPECTED = const(0x83)

    # 采样率配置
    SAMPLE_RATE = const(48000)

    # 打印间隔（ms）
    PRINT_INTERVAL = const(3000)

    last_print_time = time.ticks_ms()

    # ======================================== 功能函数 ============================================


    def init_i2c_bus():
        """初始化 I2C 总线并扫描设备"""
        print("Initializing I2C bus...")
        i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
        # 扫描 I2C 总线
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus")
        print("I2C devices found: %s" % [hex(d) for d in devices])
        # 验证目标设备地址存在
        found = False
        for dev in devices:
            if dev == ES8311_I2C_ADDR:
                found = True
                break
        if not found:
            raise RuntimeError("Device not found at expected address 0x%02X" % ES8311_I2C_ADDR)
        print("ES8311 device found at 0x%02X" % ES8311_I2C_ADDR)
        return i2c


    def verify_chip_id(i2c):
        """验证 ES8311 芯片 ID"""
        try:
            chip_id = i2c.readfrom_mem(ES8311_I2C_ADDR, ES8311_CHIP_ID_REG, 1)[0]
        except OSError as e:
            raise RuntimeError("Failed to read chip ID register: %s" % e)
        if chip_id == ES8311_CHIP_ID_EXPECTED:
            print("Chip ID verified: 0x%02X (expected 0x%02X)" % (chip_id, ES8311_CHIP_ID_EXPECTED))
        else:
            print("Chip ID mismatch: read 0x%02X, expected 0x%02X" % (chip_id, ES8311_CHIP_ID_EXPECTED))


    def init_es8311_codec(i2c):
        """
        初始化 ES8311 编解码器
        Returns:
            ES8311: 编解码器驱动实例
        """
        print("Initializing ES8311 codec...")
        # 创建编解码器驱动实例（启用调试日志）
        codec = ES8311(i2c, address=ES8311_I2C_ADDR, debug=False)

        # 构建时钟配置
        clk_cfg = ES8311ClockConfig(
            mclk_inverted=False,
            sclk_inverted=False,
            mclk_from_mclk_pin=False,  # MCLK 来自 BCLK 引脚
            mclk_frequency=0,  # BCLK 模式下此值由驱动自动计算
            sample_frequency=SAMPLE_RATE,
        )

        # 执行编解码器初始化
        codec.init(clk_cfg, ES8311.ES8311_RESOLUTION_16, ES8311.ES8311_RESOLUTION_16)
        print("ES8311 codec initialized successfully")
        return codec


    def create_dac_i2s():
        """
        创建 DAC 播放 I2S 对象
        注意：I2S 对象在 main.py 中创建，不在驱动类内部创建
        Returns:
            I2S: DAC 输出 I2S 实例
        """
        audio_out = I2S(
            0,  # I2S 外设 ID
            sck=Pin(I2S_BCK_PIN),  # 位时钟
            ws=Pin(I2S_WS_PIN),  # 字选择 / LRCK
            sd=Pin(I2S_DOUT_PIN),  # 串行数据输出
            mode=I2S.TX,  # 发送模式（DAC 播放）
            bits=16,  # 16 位采样
            format=I2S.STEREO,  # 立体声
            rate=SAMPLE_RATE,  # 采样率
            ibuf=8192,  # 内部缓冲区大小
        )
        print("DAC I2S output created: %dHz, 16-bit stereo" % SAMPLE_RATE)
        return audio_out


    def create_adc_i2s():
        """
        创建 ADC 录音 I2S 对象
        注意：I2S 对象在 main.py 中创建，不在驱动类内部创建
        Returns:
            I2S: ADC 输入 I2S 实例
        """
        audio_in = I2S(
            0,  # I2S 外设 ID（部分平台可能需要不同 ID）
            sck=Pin(I2S_BCK_PIN),  # 位时钟
            ws=Pin(I2S_WS_PIN),  # 字选择 / LRCK
            sd=Pin(I2S_DIN_PIN),  # 串行数据输入
            mode=I2S.RX,  # 接收模式（ADC 录音）
            bits=16,  # 16 位采样
            format=I2S.STEREO,  # 立体声
            rate=SAMPLE_RATE,  # 采样率
            ibuf=8192,  # 内部缓冲区大小
        )
        print("ADC I2S input created: %dHz, 16-bit stereo" % SAMPLE_RATE)
        return audio_in


    def configure_microphone(codec, digital_mic=False):
        """配置麦克风模式（REPL 可手动调用）"""
        mode_name = "digital PDM" if digital_mic else "analog"
        print("Configuring microphone: %s mode" % mode_name)
        codec.microphone_config(digital_mic)
        print("Microphone configured: %s" % mode_name)


    def print_status(codec):
        """
        打印编解码器状态信息（低频调用）
        """
        volume = codec.voice_volume_get()
        print("[Status] DAC volume: %d/100" % volume)


    # ======================================== 初始化配置 ==========================================

    # 启动延时，等待硬件就绪
    await asyncio.sleep(3)

    print("FreakStudio: ES8311 audio codec configuration driver test")
    print("I2C config driver only - I2S data handling is at application layer")

    try:
        # 初始化 I2C 总线并验证设备
        i2c = init_i2c_bus()
        verify_chip_id(i2c)

        # 初始化编解码器
        codec = init_es8311_codec(i2c)

        # 设置音量
        codec.voice_volume_set(80)
        print("Volume set to 80")

        # 配置模拟麦克风
        configure_microphone(codec, digital_mic=False)

    except OSError as e:
        print("Hardware communication error: %s" % str(e))
        raise

    # ========================================  主程序  ===========================================

    # --- 以下为 I2S 使用示例（取消注释以启用） ---
    # 注意：I2S 初始化需要相应的 I2S 引脚，请在硬件就绪后取消注释
    #
    # # 创建 I2S 对象（DAC 播放和 ADC 录音各一个）
    # audio_out = create_dac_i2s()
    # audio_in = create_adc_i2s()
    #
    # # DAC 播放示例：从文件或缓冲区读取数据写入 I2S
    # # with open("audio_sample.raw", "rb") as f:
    # #     while True:
    # #         data = f.read(1024)
    # #         if not data:
    # #             break
    # #         audio_out.write(data)
    #
    # # ADC 录音示例：从 I2S 读取数据写入文件
    # # with open("recording.raw", "wb") as f:
    # #     while True:
    # #         data = audio_in.read(1024)
    # #         f.write(data)
    #
    # 取消注释至此

    try:
        while True:
            current_time = time.ticks_ms()
            # 低频打印编解码器状态
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
                print_status(codec)
                last_print_time = current_time

            # 以下为可选功能函数，默认注释调用，可 REPL 手动触发
            # configure_microphone(codec, digital_mic=True)   # 切换到数字麦克风
            # codec.voice_volume_set(50)                       # 调整音量到 50

            await asyncio.sleep_ms(100)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        try:
            codec.deinit()
            print("Codec deinitialized")
        except Exception:
            pass
        del codec
        print("Program exited")

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `BIT` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.clock_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.fmt_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.init` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.microphone_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.resolution_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.sample_frequency_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.voice_volume_get` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311.voice_volume_set` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.clock_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.fmt_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.init_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.microphone_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.resolution_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.sample_frequency_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.voice_volume_get_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ES8311Async.voice_volume_set_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `clock_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `clock_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `configure_microphone` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `const` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `create_adc_i2s` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `create_dac_i2s` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `fmt_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `fmt_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_coeff` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `init` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `init_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `init_es8311_codec` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `init_i2c_bus` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `microphone_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `microphone_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `resolution_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `resolution_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `sample_frequency_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `sample_frequency_config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `verify_chip_id` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voice_volume_get` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voice_volume_get_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voice_volume_set` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voice_volume_set_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | M5Stack Technology CO LTD, FreakStudio | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：M5Stack Technology CO LTD, FreakStudio。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
MIT License

Copyright (c) 2023 L-ING

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
