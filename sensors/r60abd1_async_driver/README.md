# A MicroPython library to control R60ABD1 sensors — MicroPython 异步驱动

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

`r60abd1_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/r60abd1_driver`。

## 主要功能

- 可解析的公开类：`DataFlowProcessor`, `DataFlowProcessorAsync`, `DeviceInitializationError`, `R60ABD1`, `SyncAdapterMixin`。
- 可解析的公开调用入口：154 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

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
| 包版本 | `1.0.0` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/data_flow_processor.cpython-313.pyc
├── code/__pycache__/main.cpython-313.pyc
├── code/__pycache__/r60abd1.cpython-313.pyc
├── code/data_flow_processor.py
├── code/data_flow_processor_async.py
├── code/main.py
├── code/r60abd1.py
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
    # Python env   : MicroPython v1.26.1
    # -*- coding: utf-8 -*-
    # @Time    : 2025/11/4 下午5:33
    # @Author  : 李清水
    # @File    : main.py
    # @Description : 测试R60ABD1雷达设备驱动类的代码
    # @License : MIT

    # ======================================== 导入相关模块 =========================================

    from machine import UART, Pin, Timer
    from data_flow_processor import DataFlowProcessor
    from r60abd1 import R60ABD1, format_time

    # ======================================== 全局变量 ============================================

    # 上次打印时间
    last_print_time = time.ticks_ms()
    # 定时打印间隔:2秒打印一次
    print_interval = 2000

    # ======================================== 功能函数 ============================================


    def print_report_sensor_data():
        """
        打印传感器上报数据到Thonny控制台。

        Note:此函数打印的是设备主动上报的数据，不是查询结果。
        数据来源于R60ABD1类的属性值，这些属性会在定时器回调中自动更新。

        ==========================================

        Print sensor reported data to Thonny console.

        Note: This function prints data actively reported by the device, not query results.
        Data comes from R60ABD1 class attributes, which are automatically updated in timer callbacks.
        """
        # 声明全局变量
        global device

        print("=" * 50)
        print("%s Sensor Data" % format_time())
        print("=" * 50)

        # 心率数据
        print("Report Heart Rate: %d bpm" % device.heart_rate_value)
        print("Report Heart Rate Waveform: %s" % str(device.heart_rate_waveform))

        # 呼吸数据
        print("Report Breath Rate: %d bpm" % device.breath_value)
        print("Report Breath Status: %d" % device.breath_status)
        print("Report Breath Waveform: %s" % str(device.breath_waveform))

        # 人体存在数据
        print("Report Movement Parameter: %d" % device.movement_parameter)
        print("Report Presence Status: %s" % ("Someone" if device.presence_status == 1 else "No one"))
        print("Report Motion Status: %s" % ["No motion", "Static", "Active"][device.motion_status] if device.motion_status < 3 else "Unknown")

        # 距离和位置
        print("Report Human Distance: %d cm" % device.human_distance)
        print("Report Human Position: X=%d, Y=%d, Z=%d" % (device.human_position_x, device.human_position_y, device.human_position_z))

        # 雷达状态
        print("Report Radar in Range: %s" % ("Yes" if device.radar_in_range else "No"))

        print("=" * 50)


    def print_active_query_data(timeout=200):
        """
        主动查询并打印传感器数据（阻塞式查询）。

        Args:
            timeout: 单次查询超时时间，单位毫秒。

        Note:
            - 此函数执行阻塞式查询，会依次查询所有传感器数据。
            - 每个查询之间有500ms延时，避免设备处理不过来。
            - 查询失败会显示失败信息，成功则显示具体数据。

        ==========================================

        Actively query and print sensor data (blocking queries).

        Args:
            timeout: Single query timeout time in milliseconds.

        Note:
            - This function performs blocking queries, sequentially querying all sensor data.
            - Each query has 500ms delay to avoid overwhelming the device.
            - Failed queries display failure information, successful ones display specific data.
        """
        # 声明全局变量
        global device

        print("=" * 50)
        print("%s Active Query Sensor Data" % format_time())
        print("=" * 50)

        # 查询人体方位
        success, direction_data = device.query_human_direction(timeout)
        if success:
            x, y, z = direction_data
            print("Query Human Position: X=%d, Y=%d, Z=%d" % (x, y, z))
        else:
            print("Query Human Position: Failed")

        await asyncio.sleep(0.5)

        # 查询人体距离
        success, distance = device.query_human_distance(timeout)
        if success:
            print("Query Human Distance: %d cm" % distance)
        else:
            print("Query Human Distance: Failed")

        await asyncio.sleep(0.5)

        # 查询运动信息
        success, motion_status = device.query_human_motion_info(timeout)
        if success:
            motion_text = ["No motion", "Static", "Active"][motion_status] if motion_status < 3 else "Unknown"
            print("Query Motion Status: %s" % motion_text)
        else:
            print("Query Motion Status: Failed")

        await asyncio.sleep(0.5)

        # 查询体动参数
        success, motion_param = device.query_human_body_motion_param(timeout)
        if success:
            print("Query Movement Parameter: %d" % motion_param)
        else:
            print("Query Movement Parameter: Failed")

        await asyncio.sleep(0.5)

        # 查询存在状态
        success, presence_status = device.query_presence_status(timeout)
        if success:
            status_text = "Someone" if presence_status == 1 else "No one"
            print("Query Presence Status: %s" % status_text)
        else:
            print("Query Presence Status: Failed")

        await asyncio.sleep(0.5)

        # 查询心率数值
        success, heart_rate = device.query_heart_rate_value(timeout)
        if success:
            print("Query Heart Rate: %d bpm" % heart_rate)
        else:
            print("Query Heart Rate: Failed")

        await asyncio.sleep(0.5)

        # 查询心率波形
        success, heart_rate_waveform = device.query_heart_rate_waveform(timeout)
        if success:
            print("Query Heart Rate Waveform: %s" % str(heart_rate_waveform))
        else:
            print("Query Heart Rate Waveform: Failed")

        await asyncio.sleep(0.5)

        # 查询呼吸数值
        success, breath_rate = device.query_breath_value(timeout)
        if success:
            print("Query Breath Rate: %d bpm" % breath_rate)
        else:
            print("Query Breath Rate: Failed")

        await asyncio.sleep(0.5)

        # 查询呼吸波形
        success, breath_waveform = device.query_breath_waveform(timeout)
        if success:
            print("Query Breath Waveform: %s" % str(breath_waveform))
        else:
            print("Query Breath Waveform: Failed")

        await asyncio.sleep(0.5)

        # 查询呼吸信息
        success, breath_info = device.query_breath_info(timeout)
        if success:
            status_text = ["Normal", "High", "Low", "None"][breath_info - 1] if 1 <= breath_info <= 4 else "Unknown"
            print("Query Breath Info: %d - %s" % (breath_info, status_text))
        else:
            print("Query Breath Info: Failed")

        await asyncio.sleep(0.5)

        # 查询床状态
        success, bed_status = device.query_bed_status(timeout)
        if success:
            status_text = ["Leave bed", "Enter bed", "None"][bed_status] if bed_status < 3 else "Unknown"
            print("Query Bed Status: %d - %s" % (bed_status, status_text))
        else:
            print("Query Bed Status: Failed")

        await asyncio.sleep(0.5)

        # 查询无人计时状态
        success, no_person_timing_status = device.query_no_person_timing_status(timeout)
        if success:
            status_text = ["None", "Normal", "Abnormal"][no_person_timing_status] if no_person_timing_status < 3 else "Unknown"
            print("Query No Person Timing Status: %d - %s" % (no_person_timing_status, status_text))
        else:
            print("Query No Person Timing Status: Failed")

        await asyncio.sleep(0.5)

        # 查询睡眠状态
        success, sleep_status = device.query_sleep_status(timeout)
        if success:
            status_text = ["Deep sleep", "Light sleep", "Awake", "None"][sleep_status] if sleep_status < 4 else "Unknown"
            print("Query Sleep Status: %d - %s" % (sleep_status, status_text))
        else:
            print("Query Sleep Status: Failed")

        await asyncio.sleep(0.5)

        # 查询清醒时长
        success, awake_duration = device.query_awake_duration(timeout)
        if success:
            print("Query Awake Duration: %d min" % awake_duration)
        else:
            print("Query Awake Duration: Failed")

        await asyncio.sleep(0.5)

        # 查询浅睡时长
        success, light_sleep_duration = device.query_light_sleep_duration(timeout)
        if success:
            print("Query Light Sleep Duration: %d min" % light_sleep_duration)
        else:
            print("Query Light Sleep Duration: Failed")

        await asyncio.sleep(0.5)

        # 查询深睡时长
        success, deep_sleep_duration = device.query_deep_sleep_duration(timeout)
        if success:
            print("Query Deep Sleep Duration: %d min" % deep_sleep_duration)
        else:
            print("Query Deep Sleep Duration: Failed")

        await asyncio.sleep(0.5)

        # 查询睡眠质量评分
        success, sleep_quality_score = device.query_sleep_quality_score(timeout)
        if success:
            print("Query Sleep Quality Score: %d/100" % sleep_quality_score)
        else:
            print("Query Sleep Quality Score: Failed")

        await asyncio.sleep(0.5)

        # 查询睡眠综合状态
        success, sleep_comprehensive_status = device.query_sleep_comprehensive_status(timeout)
        if success:
            print("Query Sleep Comprehensive Status: Success")
            # 可以进一步解析和显示详细数据
            if len(sleep_comprehensive_status) >= 8:
                print("  - Presence: %s" % ("Someone" if sleep_comprehensive_status[0] == 1 else "No one"))
                print(
                    "  - Sleep Status: %s" % ["Deep sleep", "Light sleep", "Awake", "None"][sleep_comprehensive_status[1]]
                    if sleep_comprehensive_status[1] < 4
                    else "Unknown"
                )
                print("  - Avg Breath: %d bpm" % sleep_comprehensive_status[2])
                print("  - Avg Heart Rate: %d bpm" % sleep_comprehensive_status[3])
                print("  - Turnover Count: %d" % sleep_comprehensive_status[4])
                print("  - Large Movement Ratio: %d%%" % sleep_comprehensive_status[5])
                print("  - Small Movement Ratio: %d%%" % sleep_comprehensive_status[6])
                print("  - Apnea Count: %d" % sleep_comprehensive_status[7])
        else:
            print("Query Sleep Comprehensive Status: Failed")

        await asyncio.sleep(0.5)

        # 查询睡眠异常
        success, sleep_anomaly = device.query_sleep_anomaly(timeout)
        if success:
            status_text = ["Short sleep (<4h)", "Long sleep (>12h)", "No person anomaly", "Normal"][sleep_anomaly] if sleep_anomaly < 4 else "Unknown"
            print("Query Sleep Anomaly: %d - %s" % (sleep_anomaly, status_text))
        else:
            print("Query Sleep Anomaly: Failed")

        await asyncio.sleep(0.5)

        # 查询睡眠统计
        success, sleep_statistics = device.query_sleep_statistics(timeout)
        if success:
            print("Query Sleep Statistics: Success")
            # 可以进一步解析和显示详细数据
            if len(sleep_statistics) >= 11:
                print("  - Quality Score: %d/100" % sleep_statistics[0])
                print("  - Total Sleep Duration: %d min" % sleep_statistics[1])
                print("  - Awake Ratio: %d%%" % sleep_statistics[2])
                print("  - Light Sleep Ratio: %d%%" % sleep_statistics[3])
                print("  - Deep Sleep Ratio: %d%%" % sleep_statistics[4])
                print("  - Leave Bed Duration: %d min" % sleep_statistics[5])
                print("  - Leave Bed Count: %d" % sleep_statistics[6])
                print("  - Turnover Count: %d" % sleep_statistics[7])
                print("  - Avg Breath: %d bpm" % sleep_statistics[8])
                print("  - Avg Heart Rate: %d bpm" % sleep_statistics[9])
                print("  - Apnea Count: %d" % sleep_statistics[10])
        else:
            print("Query Sleep Statistics: Failed")

        await asyncio.sleep(0.5)

        # 查询睡眠质量评级
        success, sleep_quality_level = device.query_sleep_quality_level(timeout)
        if success:
            status_text = ["None", "Good", "Normal", "Poor"][sleep_quality_level] if sleep_quality_level < 4 else "Unknown"
            print("Query Sleep Quality Level: %d - %s" % (sleep_quality_level, status_text))
        else:
            print("Query Sleep Quality Level: Failed")

        print("=" * 50)


    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 上电延时
    await asyncio.sleep(3)
    # 打印调试信息
    print("FreakStudio: Using R60ABD1 millimeter wave information collection")

    # 初始化UART0:TX=16, RX=17，波特率115200
    uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)

    # 创建DataFlowProcessor实例
    processor = DataFlowProcessor(uart)

    # 创建R60ABD1实例
    device = R60ABD1(processor, parse_interval=200)

    success, product_model = device.query_product_model()
    if success:
        print("Product Model: %s" % product_model)
    else:
        print("Query Product Model failed")

    await asyncio.sleep(0.5)

    success, product_id = device.query_product_id()
    if success:
        print("Product ID: %s" % product_id)
    else:
        print("Query Product ID failed")

    await asyncio.sleep(0.5)

    success, hardware_model = device.query_hardware_model()
    if success:
        print("Hardware Model: %s" % hardware_model)
    else:
        print("Query Hardware Model failed")

    await asyncio.sleep(0.5)

    success, firmware_version = device.query_firmware_version()
    if success:
        print("Hardware Version: %s" % firmware_version)
    else:
        print("Query Hardware Version failed")

    await asyncio.sleep(0.5)

    success, init_status = device.query_init_complete()
    if success:
        print("Init Status: %s" % init_status)
    else:
        print("Query Init Status failed")

    await asyncio.sleep(0.5)

    success, boundary_status = device.query_radar_range_boundary()
    if success:
        status_text = "out of range" if boundary_status else "in range"
        print("Boundary Status: %s" % status_text)
    else:
        print("Query Boundary Status failed")

    await asyncio.sleep(0.5)

    success, presence_switch_status = device.query_human_presence_switch()
    if success:
        status_text = "ON" if presence_switch_status else "OFF"
        print("Boundary Status: %s" % status_text)
    else:
        print("Query Boundary Status failed")

    await asyncio.sleep(0.5)

    success, heart_rate_monitor_switch_status = device.query_heart_rate_monitor_switch()
    if success:
        status_text = "ON" if heart_rate_monitor_switch_status else "OFF"
        print("Heart Rate Monitor Switch: %s" % status_text)
    else:
        print("Query Heart Rate Monitor Switch failed")

    await asyncio.sleep(0.5)

    success, heart_rate_waveform_report_switch_status = device.query_heart_rate_waveform_report_switch()
    if success:
        status_text = "ON" if heart_rate_waveform_report_switch_status else "OFF"
        print("Heart Rate Waveform Report Switch: %s" % status_text)
    else:
        print("Query Heart Rate Waveform Report Switch failed")

    await asyncio.sleep(0.5)

    # 查询呼吸监测开关状态
    success, breath_monitor_switch_status = device.query_breath_monitor_switch()
    if success:
        status_text = "ON" if breath_monitor_switch_status else "OFF"
        print("Breath Monitor Switch: %s" % status_text)
    else:
        print("Query Breath Monitor Switch failed")

    await asyncio.sleep(0.5)

    # 设置低缓呼吸阈值为15次/分
    success, set_result = device.set_low_breath_threshold(15)
    if success:
        print("Set Low Breath Threshold: Success (15 bpm)")
    else:
        print("Set Low Breath Threshold failed")

    await asyncio.sleep(0.5)

    # 查询当前低缓呼吸阈值
    success, low_breath_threshold = device.query_low_breath_threshold()
    if success:
        print("Query Low Breath Threshold: %d bpm" % low_breath_threshold)
    else:
        print("Query Low Breath Threshold failed")

    await asyncio.sleep(0.5)

    # 查询呼吸波形上报开关状态
    success, breath_waveform_report_switch_status = device.query_breath_waveform_report_switch()
    if success:
        status_text = "ON" if breath_waveform_report_switch_status else "OFF"
        print("Breath Waveform Report Switch: %s" % status_text)
    else:
        print("Query Breath Waveform Report Switch failed")

    # 查询睡眠监测开关状态
    success, sleep_monitor_switch_status = device.query_sleep_monitor_switch()
    if success:
        status_text = "ON" if sleep_monitor_switch_status else "OFF"
        print("Sleep Monitor Switch: %s" % status_text)
    else:
        print("Query Sleep Monitor Switch failed")

    await asyncio.sleep(0.5)

    # 打开睡眠监测功能
    success, result = device.enable_sleep_monitor()
    if success:
        print("Enable Sleep Monitor: Success")
    else:
        print("Enable Sleep Monitor failed")

    await asyncio.sleep(0.5)

    # 查询异常挣扎监测开关状态
    success, abnormal_struggle_switch_status = device.query_abnormal_struggle_switch()
    if success:
        status_text = "ON" if abnormal_struggle_switch_status else "OFF"
        print("Abnormal Struggle Monitor Switch: %s" % status_text)
    else:
        print("Query Abnormal Struggle Monitor Switch failed")

    await asyncio.sleep(0.5)

    # 打开异常挣扎监测功能
    success, result = device.enable_abnormal_struggle_monitor()
    if success:
        print("Enable Abnormal Struggle Monitor: Success")
    else:
        print("Enable Abnormal Struggle Monitor failed")

    await asyncio.sleep(0.5)

    # 查询挣扎灵敏度
    success, struggle_sensitivity = device.query_struggle_sensitivity()
    if success:
        sensitivity_text = ["Low", "Medium", "High"][struggle_sensitivity] if struggle_sensitivity < 3 else "Unknown"
        print("Struggle Sensitivity: %d - %s" % (struggle_sensitivity, sensitivity_text))
    else:
        print("Query Struggle Sensitivity failed")

    await asyncio.sleep(0.5)

    # 设置挣扎灵敏度为中等
    success, result = device.set_struggle_sensitivity(1)  # 1 = 中等灵敏度
    if success:
        print("Set Struggle Sensitivity: Success (Medium)")
    else:
        print("Set Struggle Sensitivity failed")

    await asyncio.sleep(0.5)

    # 查询无人计时功能开关状态
    success, no_person_timing_switch_status = device.query_no_person_timing_switch()
    if success:
        status_text = "ON" if no_person_timing_switch_status else "OFF"
        print("No Person Timing Switch: %s" % status_text)
    else:
        print("Query No Person Timing Switch failed")

    await asyncio.sleep(0.5)

    # 打开无人计时功能
    success, result = device.enable_no_person_timing()
    if success:
        print("Enable No Person Timing: Success")
    else:
        print("Enable No Person Timing failed")

    await asyncio.sleep(0.5)

    # 查询无人计时时长
    success, no_person_timing_duration = device.query_no_person_timing_duration()
    if success:
        print("No Person Timing Duration: %d minutes" % no_person_timing_duration)
    else:
        print("Query No Person Timing Duration failed")

    await asyncio.sleep(0.5)

    # 设置无人计时时长为30分钟
    success, result = device.set_no_person_timing_duration(30)
    if success:
        print("Set No Person Timing Duration: Success (30 minutes)")
    else:
        print("Set No Person Timing Duration failed")

    await asyncio.sleep(0.5)

    # 查询睡眠截止时长
    success, sleep_end_duration = device.query_sleep_end_duration()
    if success:
        print("Sleep End Duration: %d minutes" % sleep_end_duration)
    else:
        print("Query Sleep End Duration failed")

    await asyncio.sleep(0.5)

    # 设置睡眠截止时长为10分钟
    success, result = device.set_sleep_end_duration(10)
    if success:
        print("Set Sleep End Duration: Success (10 minutes)")
    else:
        print("Set Sleep End Duration failed")

    await asyncio.sleep(0.5)

    # ========================================  主程序  ===========================================

    try:
        while True:
            current_time = time.ticks_ms()

            # 定期打印传感器数据
            if time.ticks_diff(current_time, last_print_time) >= print_interval:

                # print_report_sensor_data()

                success, presence_status = device.query_presence_status()
                if success:
                    print("Presence Status: %s" % ("Someone" if presence_status == 1 else "No one"))
                else:
                    print("Query Presence Status failed")
                last_print_time = current_time

                await asyncio.sleep(0.2)

                success, heartbeat_status = device.query_heartbeat()
                if success:
                    print("Heartbeat Status: %s" % ("Normal" if heartbeat_status == 1 else "Abnormal"))
                else:
                    print("Query Heartbeat failed")

            # 小延迟，避免占用太多CPU
            await asyncio.sleep_ms(10)

    except KeyboardInterrupt:
        print("%s Program interrupted by user" % format_time())

    finally:
        # 清理资源
        print("%s Cleaning up resources..." % format_time())
        # 停止实例运行
        device.close()
        # 销毁实例
        del device
        print("%s Program exited" % format_time())

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `DataFlowProcessor.build_and_send_frame` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DataFlowProcessor.clear_buffer` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DataFlowProcessor.get_stats` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DataFlowProcessor.read_and_parse` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DataFlowProcessorAsync.build_and_send_frame_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DataFlowProcessorAsync.clear_buffer_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DataFlowProcessorAsync.get_stats_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DataFlowProcessorAsync.read_and_parse_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.close` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_abnormal_struggle_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_breath_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_breath_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_heart_rate_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_heart_rate_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_human_presence` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_no_person_timing` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.disable_sleep_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_abnormal_struggle_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_breath_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_breath_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_heart_rate_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_heart_rate_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_human_presence` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_no_person_timing` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.enable_sleep_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.get_configuration_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_abnormal_struggle_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_abnormal_struggle_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_awake_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_bed_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_breath_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_breath_monitor_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_breath_value` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_breath_waveform` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_breath_waveform_report_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_deep_sleep_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_firmware_version` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_hardware_model` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_heart_rate_monitor_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_heart_rate_value` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_heart_rate_waveform` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_heart_rate_waveform_report_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_heartbeat` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_human_body_motion_param` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_human_direction` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_human_distance` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_human_motion_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_human_presence_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_init_complete` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_light_sleep_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_low_breath_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_no_person_timing_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_no_person_timing_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_no_person_timing_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_presence_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_product_id` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_product_model` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_radar_range_boundary` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_anomaly` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_comprehensive_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_end_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_monitor_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_quality_level` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_quality_score` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_statistics` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_sleep_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.query_struggle_sensitivity` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.reset_module` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.set_low_breath_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.set_no_person_timing_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.set_sleep_end_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.set_struggle_sensitivity` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `R60ABD1.update_properties_from_frame` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `build_and_send_frame` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `build_and_send_frame_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `clear_buffer` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `clear_buffer_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `close` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_abnormal_struggle_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_breath_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_breath_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_heart_rate_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_heart_rate_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_human_presence` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_no_person_timing` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_sleep_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_abnormal_struggle_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_breath_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_breath_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_heart_rate_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_heart_rate_waveform_report` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_human_presence` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_no_person_timing` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_sleep_monitor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `format_time` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_configuration_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_stats` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_stats_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `new_func` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_active_query_data` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_report_sensor_data` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_abnormal_struggle_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_abnormal_struggle_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_awake_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_bed_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_breath_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_breath_monitor_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_breath_value` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_breath_waveform` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_breath_waveform_report_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_deep_sleep_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_firmware_version` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_hardware_model` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_heart_rate_monitor_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_heart_rate_value` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_heart_rate_waveform` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_heart_rate_waveform_report_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_heartbeat` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_human_body_motion_param` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_human_direction` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_human_distance` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_human_motion_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_human_presence_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_init_complete` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_light_sleep_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_low_breath_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_no_person_timing_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_no_person_timing_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_no_person_timing_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_presence_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_product_id` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_product_model` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_radar_range_boundary` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_anomaly` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_comprehensive_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_end_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_monitor_switch` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_quality_level` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_quality_score` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_statistics` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_sleep_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `query_struggle_sensitivity` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_and_parse` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_and_parse_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset_module` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_low_breath_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_no_person_timing_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_sleep_end_duration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_struggle_sensitivity` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `timed_function` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `update_properties_from_frame` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `code/main.py` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

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
