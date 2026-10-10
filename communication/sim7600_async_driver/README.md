# Async MicroPython SIM7600 UART AT driver — MicroPython 异步驱动

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

`sim7600_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`communication/sim7600_driver`。

## 主要功能

- 可解析的公开类：`Calling`, `CallingAsync`, `GPS`, `GPSAsync`, `HTTP`, `HTTPAsync`, `LBS`, `LBSAsync`, `SIM7600`, `SIM7600Async`, `SIM7600AsyncV2`, `SIM7600AsyncV3`, `SIM7600AsyncV4`, `SMS`, `SMSAsync`, `TCPIP`。
- 可解析的公开调用入口：175 个（详见 API 矩阵）。
- 异步等级：`native_async`；依据：代码使用协程/流或可轮询 I/O。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | UART, Pin( |
| 示例 GPIO | 16、17 |
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
├── async_source_examples.json
├── code/calling.py
├── code/main.py
├── code/sim7600/__init__.py
├── code/sim7600/calling.py
├── code/sim7600/core.py
├── code/sim7600/http.py
├── code/sim7600/location.py
├── code/sim7600/sms.py
├── code/sim7600/tcpip.py
├── code/sim7600_async.py
├── code/sim7600_async_v2.py
├── code/sim7600_async_v3.py
├── code/sim7600_async_v4.py
├── code/sms.py
├── examples/calling_sync.py
├── examples/GPS_sync.py
├── examples/HTTP_sync.py
├── examples/LBS_sync.py
├── examples/sms_sync.py
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
from machine import UART, Pin
from sim7600_async_v4 import SIM7600AsyncV4 as SIM7600
from sim7600_async import CallingAsync as Calling, SMSAsync as SMS, GPSAsync as GPS, LBSAsync as LBS, HTTPAsync as HTTP

async def main():
    uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
    sim7600 = SIM7600(uart); calling = Calling(sim7600); sms = SMS(sim7600); gps = GPS(sim7600); lbs = LBS(sim7600); http = HTTP(sim7600)
    try:
        await sim7600.check_sim_card_async(); await sim7600.get_signal_quality_async(); await sim7600.check_network_registration_async(); await sim7600.check_network_attach_async(); await sim7600.send_command_async("AT+CGMR")
        await calling.make_call_async("+8619524162376"); await calling.hang_up_async(); await calling.answer_call_async(); await calling.call_status_async(); await calling.set_call_volume_async(5)
        await sms.set_sms_mode_async(); await sms.send_sms_async("19524162399", "FreakStudio: SIM7600 SMS module initialized successfully"); await sms.list_sms_async("ALL")
        await gps.disable_gps_async(); await gps.set_satellite_beidou_async(); await gps.enable_gps_async(); await gps.start_search_satellite_async(); await gps.get_gps_info_async()
        await lbs.start_network_async(); await lbs.get_lbs_coords_async(1); await lbs.get_lbs_full_async(4); await lbs.stop_network_async()
        await http.set_apn_async(); await http.get_ip_async(); await http.enable_http_async(); await http.set_url_async("https://example.invalid"); await http.http_data_async(0); await http.send_head_async(0); await http.get_head_async(); await http.get_read_async(); await http.disable_http_async()
    finally: await sim7600.aclose()
if __name__ == "__main__": asyncio.run(main())
```

## 异步设计与使用

源状态：`source_incomplete`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `Calling.answer_call` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Calling.call_status` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Calling.hang_up` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Calling.make_call` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Calling.set_call_volume` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CallingAsync.answer_call_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CallingAsync.call_status_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CallingAsync.hang_up_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CallingAsync.make_call_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CallingAsync.set_call_volume_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPS.disable_gps` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPS.enable_gps` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPS.get_gps_info` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPS.set_satellite_all` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPS.set_satellite_beidou` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPS.set_satellite_custom` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPS.start_search_satellite` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPSAsync.disable_gps_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPSAsync.enable_gps_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPSAsync.get_gps_info_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPSAsync.set_satellite_beidou_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GPSAsync.start_search_satellite_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.disable_http` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.enable_http` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.get_head` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.get_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.get_read` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.http_data` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.http_post_file` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.send_head` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.set_apn` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTP.set_url` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.disable_http_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.enable_http_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.get_head_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.get_ip_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.get_read_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.http_data_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.send_head_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.set_apn_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `HTTPAsync.set_url_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBS.get_lbs_coords` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBS.get_lbs_full` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBS.start_network` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBS.stop_network` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBSAsync.get_lbs_coords_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBSAsync.get_lbs_full_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBSAsync.start_network_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LBSAsync.stop_network_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.check_network_attach` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.check_network_registration` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.check_sim_card` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.connect` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.disconnect` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.get_network_status` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.get_signal_quality` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.monitor_voltage` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.power_off` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.power_on` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.reset_module` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.send_command` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.set_flight_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600.set_power_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600Async.aclose` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600Async.check_network_attach_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600Async.check_network_registration_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600Async.check_sim_card_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600Async.command_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600Async.get_signal_quality_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV2.send_command_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV3.check_network_attach_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV3.check_network_registration_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV3.check_sim_card_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV3.get_signal_quality_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV4.check_network_attach_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV4.check_network_registration_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV4.check_sim_card_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV4.get_signal_quality_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SIM7600AsyncV4.send_command_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMS.delete_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMS.list_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMS.read_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMS.send_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMS.set_sms_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMSAsync.list_sms_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMSAsync.send_sms_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SMSAsync.set_sms_mode_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPIP.close_connection` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPIP.open_connection` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPIP.receive_data` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPIP.send_data` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPIP.set_apn` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `answer_call` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `answer_call_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `call_status` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `call_status_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `check_network_attach` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `check_network_attach_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `check_network_registration` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `check_network_registration_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `check_sim_card` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `check_sim_card_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `close_connection` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `command_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `connect` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `delete_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_gps` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_gps_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_http` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_http_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disconnect` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_gps` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_gps_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_http` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_http_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_gps_info` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_gps_info_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_head` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_head_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_ip_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_lbs_coords` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_lbs_coords_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_lbs_full` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_lbs_full_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_network_status` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_read` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_read_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_signal_quality` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_signal_quality_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `hang_up` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `hang_up_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `http_data` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `http_data_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `http_post_file` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `list_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `list_sms_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `make_call` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `make_call_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `monitor_voltage` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `open_connection` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `power_off` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `power_on` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `receive_data` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset_module` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_command` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_command_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_data` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_head` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_head_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_sms` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_sms_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_apn` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_apn_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_call_volume` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_call_volume_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_flight_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_power_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_satellite_all` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_satellite_beidou` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_satellite_beidou_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_satellite_custom` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_sms_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_sms_mode_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_url` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_url_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `start_network` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `start_network_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `start_search_satellite` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `start_search_satellite_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `stop_network` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `stop_network_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `未找到可运行源示例` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

## 超时、取消、并发与残余阻塞

任何 `await` 不会自动使底层 I2C/SPI/UART/Pin 操作变为非阻塞。取消时应停止后台任务并在 `finally` 释放资源；没有实现超时参数的 API 不应被假定具有超时。协议命令、帧界限、ACK、静默间隔及错误含义只以当前实现和源示例可证明的内容为准。



## UART Concurrency Contract

Model: caller-owned
Reader owner: 调用方协程；不得让多个协程同时读取同一 UART。
Frame and unsolicited-data policy: 仅按当前运行时已有帧解析规则处理；未定义的非请求数据不得静默丢弃。

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
