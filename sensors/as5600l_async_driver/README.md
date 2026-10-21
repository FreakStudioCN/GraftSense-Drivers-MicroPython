# Async conversion of as5600l_driver — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../as5600l_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
>
> 异步版本：本包 Python 源码及示例已通过 MicroPython 1.23 / 1.29 编译检查；软件回归只覆盖选定路径，不代表本包全部 API、实际器件及并发行为已验证。
>
> [仓库验证说明](../../README.md#异步驱动验证状态实验性) · [两轮软件检查](../../docs/pr119_validation.json) · [受限清单](../../docs/pr119_final_validation_limits.json) · [安装与初始化迁移](../../docs/PR119_INSTALL_MIGRATION.md)
<!-- async-validation-status:end -->

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

`as5600l_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/as5600l_driver`。

## 主要功能

- 可解析的公开类：`AS5600`, `AS5600Async`。
- 可解析的公开调用入口：100 个（详见 API 矩阵）。
- 异步等级：`not_async_safe`；异步包装不能消除同步 I2C 阻塞；在取得可复现阻塞上界前不得作为可用异步驱动交付。

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
| 作者 | hogeiha |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/as5600.cpython-313.pyc
├── code/__pycache__/main.cpython-313.pyc
├── code/as5600.py
├── code/as5600_async.py
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
    # @Time    : 2025/05/15
    # @Author  : hogeiha
    # @File    : main.py
    # @Description : 测试 AS5600/AS5600L 12位磁性旋转编码器驱动类
    # @License : MIT
    
    __version__ = "1.0.0"
    __author__ = "hogeiha"
    __license__ = "MIT"
    __platform__ = "MicroPython v1.23"
    
    # ======================================== 导入相关模块 =========================================
    
    # 时间相关接口
    # I2C 总线
    from machine import I2C, Pin
    # AS5600 驱动
    from as5600 import AS5600
    
    # ======================================== 全局变量 ============================================
    
    # I2C 总线参数
    I2C_ID = 0
    I2C_SCL_PIN = 5
    I2C_SDA_PIN = 4
    I2C_FREQ = 400000
    
    # AS5600L 默认地址（AS5600 标准件为 0x36）
    AS5600_ADDR = 0x40
    
    # AS5600 无 WHO_AM_I 寄存器，使用 STATUS 寄存器作为设备响应验证
    DEVICE_VERIFY_REG = 0x1B
    # STATUS 寄存器仅有效位为 bit5/bit4/bit3，其余位为 0
    DEVICE_VERIFY_MASK = 0xC7
    DEVICE_VERIFY_EXPECTED = 0x00
    
    # 主循环打印间隔（毫秒）
    PRINT_INTERVAL_MS = 1000
    last_print_time = time.ticks_ms()
    
    # ======================================== 功能函数 ============================================
    
    def print_realtime_angle():
        """高频读取实时角度（默认注释执行，可在 REPL 手动调用）"""
        # 读取原始与映射角度
        raw = sensor.rawangle()
        mapped = sensor.angle()
        # 12 位分辨率换算为度
        print("Raw: %d  Angle: %d  (%.2f deg)" % (raw, mapped, mapped * 360.0 / 4096.0))
    
    
    def print_status():
        """打印磁铁状态、AGC 与磁场强度"""
        # 磁铁检测三态
        md = sensor.md()
        ml = sensor.ml()
        mh = sensor.mh()
        # 自动增益与磁场强度
        agc = sensor.agc()
        mag = sensor.magnitude()
        print("Magnet: detected=%d weak=%d strong=%d  AGC=%d  Magnitude=%d"
              % (md, ml, mh, agc, mag))
    
    
    def print_config():
        """打印当前配置寄存器（ZMCO/ZPOS/MPOS/MANG/CONF 各位域）"""
        # 烧录次数
        zmco = sensor.zmco()
        # 角度映射相关
        zpos = sensor.zpos()
        mpos = sensor.mpos()
        mang = sensor.mang()
        # CONF 寄存器拆位
        pm = sensor.pm()
        hyst = sensor.hyst()
        outs = sensor.outs()
        pwmf = sensor.pwmf()
        sf = sensor.sf()
        fth = sensor.fth()
        wd = sensor.watchdog()
        print("ZMCO=%d ZPOS=%d MPOS=%d MANG=%d" % (zmco, zpos, mpos, mang))
        print("CONF: PM=%d HYST=%d OUTS=%d PWMF=%d SF=%d FTH=%d WD=%d"
              % (pm, hyst, outs, pwmf, sf, fth, wd))
    
    
    def test_boundary_write():
        """边界参数场景：ZPOS 写入 0 与 4095（12 位最小/最大）"""
        # 写入最小值
        sensor.zpos(0)
        v0 = sensor.zpos()
        # 写入最大值
        sensor.zpos(4095)
        v1 = sensor.zpos()
        print("Boundary ZPOS write: 0 -> %d, 4095 -> %d" % (v0, v1))
    
    
    def test_invalid_args():
        """异常参数场景：验证非法参数能正确抛出 ValueError"""
        # 非法寄存器地址
        try:
            sensor.readwrite(0x100, 7, 0)
        except ValueError as e:
            print("Caught register out-of-range: %s" % e)
        # 非法位域
        try:
            sensor.readwrite(0x07, 3, 5)
        except ValueError as e:
            print("Caught invalid bitfield: %s" % e)
        # 写入超出位域范围
        try:
            sensor.zpos(0x10000)
        except ValueError as e:
            print("Caught value out-of-range: %s" % e)
        # 错误类型
        try:
            sensor.zpos("bad")
        except ValueError as e:
            print("Caught wrong type: %s" % e)
    
    
    def burn_angle_once():
        """烧录角度（ZPOS/MPOS）到 OTP，不可逆，仅 REPL 手动触发"""
        sensor.burn_angle()
        print("burn_angle issued")
    
    
    def burn_setting_once():
        """烧录配置（MANG/CONF）到 OTP，不可逆，仅 REPL 手动触发"""
        sensor.burn_setting()
        print("burn_setting issued")
    
    # ======================================== 自定义类 ============================================
    
    # ======================================== 初始化配置 ==========================================
    
    await asyncio.sleep(3)
    print("FreakStudio: AS5600/AS5600L magnetic encoder driver test")
    
    # 初始化 I2C 总线
    i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    
    # 扫描 I2C 总线
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found")
    print("I2C scan result: %s" % [hex(d) for d in devices])
    
    # 验证目标地址在线
    if AS5600_ADDR not in devices:
        raise RuntimeError("Device not found at expected address 0x%02X" % AS5600_ADDR)
    print("Target device 0x%02X present on bus" % AS5600_ADDR)
    
    # 设备响应验证（AS5600 无 WHO_AM_I，改读 STATUS 寄存器并按掩码比对保留位）
    _probe = i2c.readfrom_mem(AS5600_ADDR, DEVICE_VERIFY_REG, 1)[0]
    if (_probe & ~DEVICE_VERIFY_MASK) == DEVICE_VERIFY_EXPECTED:
        print("Device found (STATUS=0x%02X)" % _probe)
    else:
        print("Device not found (STATUS=0x%02X, unexpected reserved bits)" % _probe)
    
    # 创建驱动实例
    sensor = AS5600(i2c, device=AS5600_ADDR, debug=False)
    
    # ========================================  主程序  ===========================================
    
    try:
        # 启动时打印一次配置与状态
        print_config()
        print_status()
        while True:
            await asyncio.sleep_ms(0)
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                # 低频核心采集：角度 + 状态
                raw = sensor.rawangle()
                mapped = sensor.angle()
                md = sensor.md()
                print("Angle raw=%d mapped=%d (%.2f deg)  magnet=%d"
                      % (raw, mapped, mapped * 360.0 / 4096.0, md))
                last_print_time = current_time
            # print_realtime_angle()   # 高频角度读取，默认注释，REPL 手动调用
            # print_status()           # 状态/AGC/magnitude，默认注释，REPL 手动调用
            # print_config()           # 配置回读，默认注释，REPL 手动调用
            # test_boundary_write()    # 边界参数，默认注释，REPL 手动调用
            # test_invalid_args()      # 异常参数，默认注释，REPL 手动调用
            # burn_angle_once()        # OTP 烧录不可逆，仅 REPL 手动触发
            # burn_setting_once()      # OTP 烧录不可逆，仅 REPL 手动触发
            await asyncio.sleep_ms(10)
    
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        try:
            sensor.deinit()
        except Exception:
            pass
        del sensor
        print("Program exited")
    

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `AS5600.agc` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.angle` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.burn_angle` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.burn_setting` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.deinit` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.fth` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.hyst` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.magnitude` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.mang` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.md` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.mh` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.ml` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.mpos` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.outs` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.pm` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.pwmf` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.rawangle` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.readwrite` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.sf` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.watchdog` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.zmco` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600.zpos` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.aclose` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.agc_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.angle_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.burn_angle_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.burn_setting_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.call_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.deinit_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.fth_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.hyst_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.magnitude_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.mang_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.md_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.mh_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.ml_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.mpos_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.outs_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.pm_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.pwmf_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.rawangle_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.readwrite_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.sf_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.watchdog_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.zmco_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `AS5600Async.zpos_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `aclose` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `agc` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `agc_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `angle` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `angle_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `burn_angle` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `burn_angle_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `burn_angle_once` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `burn_setting` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `burn_setting_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `burn_setting_once` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `call_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `deinit` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `deinit_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `fth` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `fth_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `hyst` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `hyst_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `magnitude` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `magnitude_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `main` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `mang` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `mang_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `md` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `md_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `mh` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `mh_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `ml` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `ml_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `mpos` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `mpos_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `outs` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `outs_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `pm` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `pm_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `print_config` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `print_realtime_angle` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `print_status` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `pwmf` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `pwmf_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `rawangle` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `rawangle_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `readwrite` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `readwrite_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `sf` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `sf_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `test_boundary_write` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `test_invalid_args` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `watchdog` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `watchdog_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `zmco` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `zmco_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `zpos` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `zpos_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `code/main.py` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

## 超时、取消、并发与残余阻塞

任何 `await` 不会自动使底层 I2C/SPI/UART/Pin 操作变为非阻塞。取消时应停止后台任务并在 `finally` 释放资源；没有实现超时参数的 API 不应被假定具有超时。协议命令、帧界限、ACK、静默间隔及错误含义只以当前实现和源示例可证明的内容为准。



## Sync Adapter Blocking Budget

所有标记为 `not_async_safe` 的 API 都直接委托给来源实现中的一个或多个同步 I2C 事务；协程包装本身不在事务内部让出执行权。阻塞来源是 `I2C.readfrom_mem`、`I2C.writeto_mem`、`I2C.readfrom` 或 `I2C.writeto`。未在目标硬件、总线频率、从机时钟拉伸和错误恢复条件下测得可证实的最大事务时长，因此最大阻塞时间为“未验证”，不能承诺 deadline 或实时性。

这些 API 没有事务内 timeout，也不能在 I2C 调用进行时响应取消；任务取消只会在同步调用返回后的下一个 `await` 处生效。调用者应避免在时延敏感的任务、IRQ 或 PIO 回调中调用，并在同一 I2C 总线的并发访问上自行串行化。保留风险：慢设备、时钟拉伸、总线故障或驱动恢复都可能使事件循环阻塞；尚未进行硬件验证。
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
| `1.0.0` | 2026-09-17 | hogeiha | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：hogeiha。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
MIT License

Copyright (c) 2026 leezisheng

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
