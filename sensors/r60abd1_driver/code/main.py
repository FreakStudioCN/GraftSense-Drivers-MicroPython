# Python env   : MicroPython v1.26.1
# -*- coding: utf-8 -*-
# @Time    : 2025/11/4 下午5:33
# @Author  : 李清水
# @File    : main.py
# @Description : 测试R60ABD1雷达设备驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin, Timer
import time
from data_flow_processor import DataFlowProcessor
from r60abd1 import R60ABD1, format_time

# ======================================== 全局变量 ============================================

# 上次打印时间
last_print_time = time.ticks_ms()
# 定时打印间隔：2秒打印一次
print_interval = 2000

# ======================================== 功能函数 ============================================


def print_report_sensor_data():
    """
    打印传感器上报数据到Thonny控制台。

    Note：此函数打印的是设备主动上报的数据，不是查询结果。
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

    Note：
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

    time.sleep(0.5)

    # 查询人体距离
    success, distance = device.query_human_distance(timeout)
    if success:
        print("Query Human Distance: %d cm" % distance)
    else:
        print("Query Human Distance: Failed")

    time.sleep(0.5)

    # 查询运动信息
    success, motion_status = device.query_human_motion_info(timeout)
    if success:
        motion_text = ["No motion", "Static", "Active"][motion_status] if motion_status < 3 else "Unknown"
        print("Query Motion Status: %s" % motion_text)
    else:
        print("Query Motion Status: Failed")

    time.sleep(0.5)

    # 查询体动参数
    success, motion_param = device.query_human_body_motion_param(timeout)
    if success:
        print("Query Movement Parameter: %d" % motion_param)
    else:
        print("Query Movement Parameter: Failed")

    time.sleep(0.5)

    # 查询存在状态
    success, presence_status = device.query_presence_status(timeout)
    if success:
        status_text = "Someone" if presence_status == 1 else "No one"
        print("Query Presence Status: %s" % status_text)
    else:
        print("Query Presence Status: Failed")

    time.sleep(0.5)

    # 查询心率数值
    success, heart_rate = device.query_heart_rate_value(timeout)
    if success:
        print("Query Heart Rate: %d bpm" % heart_rate)
    else:
        print("Query Heart Rate: Failed")

    time.sleep(0.5)

    # 查询心率波形
    success, heart_rate_waveform = device.query_heart_rate_waveform(timeout)
    if success:
        print("Query Heart Rate Waveform: %s" % str(heart_rate_waveform))
    else:
        print("Query Heart Rate Waveform: Failed")

    time.sleep(0.5)

    # 查询呼吸数值
    success, breath_rate = device.query_breath_value(timeout)
    if success:
        print("Query Breath Rate: %d bpm" % breath_rate)
    else:
        print("Query Breath Rate: Failed")

    time.sleep(0.5)

    # 查询呼吸波形
    success, breath_waveform = device.query_breath_waveform(timeout)
    if success:
        print("Query Breath Waveform: %s" % str(breath_waveform))
    else:
        print("Query Breath Waveform: Failed")

    time.sleep(0.5)

    # 查询呼吸信息
    success, breath_info = device.query_breath_info(timeout)
    if success:
        status_text = ["Normal", "High", "Low", "None"][breath_info - 1] if 1 <= breath_info <= 4 else "Unknown"
        print("Query Breath Info: %d - %s" % (breath_info, status_text))
    else:
        print("Query Breath Info: Failed")

    time.sleep(0.5)

    # 查询床状态
    success, bed_status = device.query_bed_status(timeout)
    if success:
        status_text = ["Leave bed", "Enter bed", "None"][bed_status] if bed_status < 3 else "Unknown"
        print("Query Bed Status: %d - %s" % (bed_status, status_text))
    else:
        print("Query Bed Status: Failed")

    time.sleep(0.5)

    # 查询无人计时状态
    success, no_person_timing_status = device.query_no_person_timing_status(timeout)
    if success:
        status_text = ["None", "Normal", "Abnormal"][no_person_timing_status] if no_person_timing_status < 3 else "Unknown"
        print("Query No Person Timing Status: %d - %s" % (no_person_timing_status, status_text))
    else:
        print("Query No Person Timing Status: Failed")

    time.sleep(0.5)

    # 查询睡眠状态
    success, sleep_status = device.query_sleep_status(timeout)
    if success:
        status_text = ["Deep sleep", "Light sleep", "Awake", "None"][sleep_status] if sleep_status < 4 else "Unknown"
        print("Query Sleep Status: %d - %s" % (sleep_status, status_text))
    else:
        print("Query Sleep Status: Failed")

    time.sleep(0.5)

    # 查询清醒时长
    success, awake_duration = device.query_awake_duration(timeout)
    if success:
        print("Query Awake Duration: %d min" % awake_duration)
    else:
        print("Query Awake Duration: Failed")

    time.sleep(0.5)

    # 查询浅睡时长
    success, light_sleep_duration = device.query_light_sleep_duration(timeout)
    if success:
        print("Query Light Sleep Duration: %d min" % light_sleep_duration)
    else:
        print("Query Light Sleep Duration: Failed")

    time.sleep(0.5)

    # 查询深睡时长
    success, deep_sleep_duration = device.query_deep_sleep_duration(timeout)
    if success:
        print("Query Deep Sleep Duration: %d min" % deep_sleep_duration)
    else:
        print("Query Deep Sleep Duration: Failed")

    time.sleep(0.5)

    # 查询睡眠质量评分
    success, sleep_quality_score = device.query_sleep_quality_score(timeout)
    if success:
        print("Query Sleep Quality Score: %d/100" % sleep_quality_score)
    else:
        print("Query Sleep Quality Score: Failed")

    time.sleep(0.5)

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

    time.sleep(0.5)

    # 查询睡眠异常
    success, sleep_anomaly = device.query_sleep_anomaly(timeout)
    if success:
        status_text = ["Short sleep (<4h)", "Long sleep (>12h)", "No person anomaly", "Normal"][sleep_anomaly] if sleep_anomaly < 4 else "Unknown"
        print("Query Sleep Anomaly: %d - %s" % (sleep_anomaly, status_text))
    else:
        print("Query Sleep Anomaly: Failed")

    time.sleep(0.5)

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

    time.sleep(0.5)

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
time.sleep(3)
# 打印调试信息
print("FreakStudio: Using R60ABD1 millimeter wave information collection")

# 初始化UART0：TX=16, RX=17，波特率115200
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

time.sleep(0.5)

success, product_id = device.query_product_id()
if success:
    print("Product ID: %s" % product_id)
else:
    print("Query Product ID failed")

time.sleep(0.5)

success, hardware_model = device.query_hardware_model()
if success:
    print("Hardware Model: %s" % hardware_model)
else:
    print("Query Hardware Model failed")

time.sleep(0.5)

success, firmware_version = device.query_firmware_version()
if success:
    print("Hardware Version: %s" % firmware_version)
else:
    print("Query Hardware Version failed")

time.sleep(0.5)

success, init_status = device.query_init_complete()
if success:
    print("Init Status: %s" % init_status)
else:
    print("Query Init Status failed")

time.sleep(0.5)

success, boundary_status = device.query_radar_range_boundary()
if success:
    status_text = "out of range" if boundary_status else "in range"
    print("Boundary Status: %s" % status_text)
else:
    print("Query Boundary Status failed")

time.sleep(0.5)

success, presence_switch_status = device.query_human_presence_switch()
if success:
    status_text = "ON" if presence_switch_status else "OFF"
    print("Boundary Status: %s" % status_text)
else:
    print("Query Boundary Status failed")

time.sleep(0.5)

success, heart_rate_monitor_switch_status = device.query_heart_rate_monitor_switch()
if success:
    status_text = "ON" if heart_rate_monitor_switch_status else "OFF"
    print("Heart Rate Monitor Switch: %s" % status_text)
else:
    print("Query Heart Rate Monitor Switch failed")

time.sleep(0.5)

success, heart_rate_waveform_report_switch_status = device.query_heart_rate_waveform_report_switch()
if success:
    status_text = "ON" if heart_rate_waveform_report_switch_status else "OFF"
    print("Heart Rate Waveform Report Switch: %s" % status_text)
else:
    print("Query Heart Rate Waveform Report Switch failed")

time.sleep(0.5)

# 查询呼吸监测开关状态
success, breath_monitor_switch_status = device.query_breath_monitor_switch()
if success:
    status_text = "ON" if breath_monitor_switch_status else "OFF"
    print("Breath Monitor Switch: %s" % status_text)
else:
    print("Query Breath Monitor Switch failed")

time.sleep(0.5)

# 设置低缓呼吸阈值为15次/分
success, set_result = device.set_low_breath_threshold(15)
if success:
    print("Set Low Breath Threshold: Success (15 bpm)")
else:
    print("Set Low Breath Threshold failed")

time.sleep(0.5)

# 查询当前低缓呼吸阈值
success, low_breath_threshold = device.query_low_breath_threshold()
if success:
    print("Query Low Breath Threshold: %d bpm" % low_breath_threshold)
else:
    print("Query Low Breath Threshold failed")

time.sleep(0.5)

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

time.sleep(0.5)

# 打开睡眠监测功能
success, result = device.enable_sleep_monitor()
if success:
    print("Enable Sleep Monitor: Success")
else:
    print("Enable Sleep Monitor failed")

time.sleep(0.5)

# 查询异常挣扎监测开关状态
success, abnormal_struggle_switch_status = device.query_abnormal_struggle_switch()
if success:
    status_text = "ON" if abnormal_struggle_switch_status else "OFF"
    print("Abnormal Struggle Monitor Switch: %s" % status_text)
else:
    print("Query Abnormal Struggle Monitor Switch failed")

time.sleep(0.5)

# 打开异常挣扎监测功能
success, result = device.enable_abnormal_struggle_monitor()
if success:
    print("Enable Abnormal Struggle Monitor: Success")
else:
    print("Enable Abnormal Struggle Monitor failed")

time.sleep(0.5)

# 查询挣扎灵敏度
success, struggle_sensitivity = device.query_struggle_sensitivity()
if success:
    sensitivity_text = ["Low", "Medium", "High"][struggle_sensitivity] if struggle_sensitivity < 3 else "Unknown"
    print("Struggle Sensitivity: %d - %s" % (struggle_sensitivity, sensitivity_text))
else:
    print("Query Struggle Sensitivity failed")

time.sleep(0.5)

# 设置挣扎灵敏度为中等
success, result = device.set_struggle_sensitivity(1)  # 1 = 中等灵敏度
if success:
    print("Set Struggle Sensitivity: Success (Medium)")
else:
    print("Set Struggle Sensitivity failed")

time.sleep(0.5)

# 查询无人计时功能开关状态
success, no_person_timing_switch_status = device.query_no_person_timing_switch()
if success:
    status_text = "ON" if no_person_timing_switch_status else "OFF"
    print("No Person Timing Switch: %s" % status_text)
else:
    print("Query No Person Timing Switch failed")

time.sleep(0.5)

# 打开无人计时功能
success, result = device.enable_no_person_timing()
if success:
    print("Enable No Person Timing: Success")
else:
    print("Enable No Person Timing failed")

time.sleep(0.5)

# 查询无人计时时长
success, no_person_timing_duration = device.query_no_person_timing_duration()
if success:
    print("No Person Timing Duration: %d minutes" % no_person_timing_duration)
else:
    print("Query No Person Timing Duration failed")

time.sleep(0.5)

# 设置无人计时时长为30分钟
success, result = device.set_no_person_timing_duration(30)
if success:
    print("Set No Person Timing Duration: Success (30 minutes)")
else:
    print("Set No Person Timing Duration failed")

time.sleep(0.5)

# 查询睡眠截止时长
success, sleep_end_duration = device.query_sleep_end_duration()
if success:
    print("Sleep End Duration: %d minutes" % sleep_end_duration)
else:
    print("Query Sleep End Duration failed")

time.sleep(0.5)

# 设置睡眠截止时长为10分钟
success, result = device.set_sleep_end_duration(10)
if success:
    print("Set Sleep End Duration: Success (10 minutes)")
else:
    print("Set Sleep End Duration failed")

time.sleep(0.5)

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

            time.sleep(0.2)

            success, heartbeat_status = device.query_heartbeat()
            if success:
                print("Heartbeat Status: %s" % ("Normal" if heartbeat_status == 1 else "Abnormal"))
            else:
                print("Query Heartbeat failed")

        # 小延迟，避免占用太多CPU
        time.sleep_ms(10)

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
