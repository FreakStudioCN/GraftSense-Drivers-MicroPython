# Python env   : MicroPython v1.26.1
# -*- coding: utf-8 -*-
# @Time    : 2025/11/4 下午5:33
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试R60AFD1雷达设备驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin, Timer
import time
from data_flow_processor import DataFlowProcessor
from r60afd1 import R60AFD1, format_time
from hc08 import HC08

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
    数据来源于R60AFD1类的属性值，这些属性会在定时器回调中自动更新。

    ==========================================

    Print sensor reported data to Thonny console.

    Note: This function prints data actively reported by the device, not query results.
    Data comes from R60AFD1 class attributes, which are automatically updated in timer callbacks.
    """
    # 声明全局变量
    global device

    print("=" * 50)
    print("%s Sensor Data" % format_time())
    print("=" * 50)

    # 系统级信息
    print("System Initialized: %s" % ("Yes" if device.system_initialized else "No"))
    print("Radar Fault Status: %d" % device.radar_fault_status)
    print("Working Duration: %d seconds" % device.working_duration)
    print("Scene Info: %d" % device.scene_info)

    # 安装配置
    print("Install Angle: X=%d, Y=%d, Z=%d" % (
        device.install_angle_x, device.install_angle_y, device.install_angle_z))
    print("Install Height: %d cm" % device.install_height)
    print("Auto Measured Height: %d cm" % device.auto_height)

    # 人体存在检测
    print("Presence Status: %s" % ("Someone" if device.presence_status == 1 else "No one"))
    print("Motion Status: %s" % ["No motion", "Static", "Active"][
        device.motion_status] if device.motion_status < 3 else "Unknown")
    print("Movement Parameter: %d" % device.movement_parameter)
    print("Max Energy Value: %d" % device.max_energy_value)

    # 高度占比信息
    if device.height_total_count > 0:
        print("Height Total Count: %d" % device.height_total_count)
        print("Height Ratio 0-0.5m: %d%%" % device.height_ratio_0_05)
        print("Height Ratio 0.5-1m: %d%%" % device.height_ratio_05_1)
        print("Height Ratio 1-1.5m: %d%%" % device.height_ratio_1_15)
        print("Height Ratio 1.5-2m: %d%%" % device.height_ratio_15_2)

    # 轨迹点信息
    print("Track Position: X=%d, Y=%d" % (device.track_position_x, device.track_position_y))

    # 距离设置
    print("Static Distance: %d cm" % device.static_distance)
    print("Motion Distance: %d cm" % device.motion_distance)

    # 阈值配置
    print("Presence Threshold: %d" % device.presence_threshold)
    print("No Person Timeout: %d seconds" % device.no_person_timeout)

    # 跌倒检测
    print("Fall Status: %s" % ("Fall detected" if device.fall_status == 1 else "No fall"))
    print("Fall Sensitivity: %d" % device.fall_sensitivity)
    print("Fall Duration Threshold: %d seconds" % device.fall_duration_threshold)

    # 静止驻留检测
    print("Static Stay Status: %s" % ("Stationary detected" if device.static_stay_status == 1 else "Not stationary"))
    print("Static Stay Duration: %d seconds" % device.static_stay_duration)

    # 高度相关参数
    print("Height Accumulation Time: %d seconds" % device.height_accumulation_time)
    print("Fall Break Height: %d cm" % device.fall_break_height)

    # 功能开关状态
    print("Presence Enabled: %s" % ("ON" if device.presence_enabled else "OFF"))
    print("Track Report Enabled: %s" % ("ON" if device.track_report_enabled else "OFF"))
    print("Energy Report Enabled: %s" % ("ON" if device.energy_report_enabled else "OFF"))
    print("Height Ratio Enabled: %s" % ("ON" if device.height_ratio_enabled else "OFF"))
    print("Fall Detection Enabled: %s" % ("ON" if device.fall_detection_enabled else "OFF"))
    print("Static Stay Enabled: %s" % ("ON" if device.static_stay_enabled else "OFF"))

    print("=" * 50)


def print_active_query_data(timeout=200):
    """
    主动查询并打印传感器数据（阻塞式查询）。

    Args:
        timeout: 单次查询超时时间，单位毫秒。

    Note：
        - 此函数执行阻塞式查询，会依次查询所有传感器数据。
        - 每个查询之间有200ms延时，避免设备处理不过来。
        - 查询失败会显示失败信息，成功则显示具体数据。

    ==========================================

    Actively query and print sensor data (blocking queries).

    Args:
        timeout: Single query timeout time in milliseconds.

    Note:
        - This function performs blocking queries, sequentially querying all sensor data.
        - Each query has 200ms delay to avoid overwhelming the device.
        - Failed queries display failure information, successful ones display specific data.
    """
    # 声明全局变量
    global device

    print("=" * 50)
    print("%s Active Query Sensor Data" % format_time())
    print("=" * 50)

    # 查询心跳
    success, heartbeat_result = device.query_heartbeat(timeout)
    if success:
        print("Query Heartbeat: Success")
    else:
        print("Query Heartbeat: Failed")

    time.sleep(0.2)

    # 查询产品型号
    success, product_model = device.query_product_model(timeout)
    if success:
        print("Query Product Model: %s" % product_model)
    else:
        print("Query Product Model: Failed")

    time.sleep(0.2)

    # 查询产品ID
    success, product_id = device.query_product_id(timeout)
    if success:
        print("Query Product ID: %s" % product_id)
    else:
        print("Query Product ID: Failed")

    time.sleep(0.2)

    # 查询硬件型号
    success, hardware_model = device.query_hardware_model(timeout)
    if success:
        print("Query Hardware Model: %s" % hardware_model)
    else:
        print("Query Hardware Model: Failed")

    time.sleep(0.2)

    # 查询固件版本
    success, firmware_version = device.query_firmware_version(timeout)
    if success:
        print("Query Firmware Version: %s" % firmware_version)
    else:
        print("Query Firmware Version: Failed")

    time.sleep(0.2)

    # 查询初始化状态
    success, init_status = device.query_init_complete(timeout)
    if success:
        print("Query Init Status: %s" % ("Completed" if init_status else "Not completed"))
    else:
        print("Query Init Status: Failed")

    time.sleep(0.2)

    # 查询场景信息
    success, scene_info = device.query_scene_info(timeout)
    if success:
        print("Query Scene Info: %d" % scene_info)
    else:
        print("Query Scene Info: Failed")

    time.sleep(0.2)

    # 查询安装角度
    success, angle_data = device.query_install_angle(timeout)
    if success:
        x, y, z = angle_data
        print("Query Install Angle: X=%d, Y=%d, Z=%d" % (x, y, z))
    else:
        print("Query Install Angle: Failed")

    time.sleep(0.2)

    # 查询安装高度
    success, install_height = device.query_install_height(timeout)
    if success:
        print("Query Install Height: %d cm" % install_height)
    else:
        print("Query Install Height: Failed")

    time.sleep(0.2)

    # 查询人体存在开关
    success, presence_switch = device.query_presence_switch(timeout)
    if success:
        print("Query Presence Switch: %s" % ("ON" if presence_switch else "OFF"))
    else:
        print("Query Presence Switch: Failed")

    time.sleep(0.2)

    # 查询存在状态
    success, presence_status = device.query_presence_status(timeout)
    if success:
        print("Query Presence Status: %s" % ("Someone" if presence_status == 1 else "No one"))
    else:
        print("Query Presence Status: Failed")

    time.sleep(0.2)

    # 查询运动状态
    success, motion_status = device.query_motion_status(timeout)
    if success:
        status_text = ["No motion", "Static", "Active"][motion_status] if motion_status < 3 else "Unknown"
        print("Query Motion Status: %s" % status_text)
    else:
        print("Query Motion Status: Failed")

    time.sleep(0.2)

    # 查询体动参数
    success, motion_param = device.query_body_motion_param(timeout)
    if success:
        print("Query Body Motion Parameter: %d" % motion_param)
    else:
        print("Query Body Motion Parameter: Failed")

    time.sleep(0.2)

    # 查询高度占比
    success, height_ratio = device.query_height_ratio(timeout)
    if success:
        total, ratio_0_05, ratio_05_1, ratio_1_15, ratio_15_2 = height_ratio
        print("Query Height Ratio:")
        print("  - Total: %d" % total)
        print("  - 0-0.5m: %d%%" % ratio_0_05)
        print("  - 0.5-1m: %d%%" % ratio_05_1)
        print("  - 1-1.5m: %d%%" % ratio_1_15)
        print("  - 1.5-2m: %d%%" % ratio_15_2)
    else:
        print("Query Height Ratio: Failed")

    time.sleep(0.2)

    # 查询轨迹点
    success, track_point = device.query_track_point(timeout)
    if success:
        x, y = track_point
        print("Query Track Point: X=%d, Y=%d" % (x, y))
    else:
        print("Query Track Point: Failed")

    time.sleep(0.2)

    # 查询轨迹点频率
    success, track_frequency = device.query_track_frequency(timeout)
    if success:
        print("Query Track Frequency: %d seconds" % track_frequency)
    else:
        print("Query Track Frequency: Failed")

    time.sleep(0.2)

    # 查询轨迹点开关
    success, track_switch = device.query_track_switch(timeout)
    if success:
        print("Query Track Switch: %s" % ("ON" if track_switch else "OFF"))
    else:
        print("Query Track Switch: Failed")

    time.sleep(0.2)

    # 查询静坐距离
    success, static_distance = device.query_static_distance(timeout)
    if success:
        print("Query Static Distance: %d cm" % static_distance)
    else:
        print("Query Static Distance: Failed")

    time.sleep(0.2)

    # 查询运动距离
    success, motion_distance = device.query_motion_distance(timeout)
    if success:
        print("Query Motion Distance: %d cm" % motion_distance)
    else:
        print("Query Motion Distance: Failed")

    time.sleep(0.2)

    # 查询无人时间
    success, no_person_time = device.query_no_person_time(timeout)
    if success:
        print("Query No Person Time: %d seconds" % no_person_time)
    else:
        print("Query No Person Time: Failed")

    time.sleep(0.2)

    # 查询存在阈值
    success, presence_threshold = device.query_presence_threshold(timeout)
    if success:
        print("Query Presence Threshold: %d" % presence_threshold)
    else:
        print("Query Presence Threshold: Failed")

    time.sleep(0.2)

    # 查询能量报告开关
    success, energy_report_switch = device.query_energy_report_switch(timeout)
    if success:
        print("Query Energy Report Switch: %s" % ("ON" if energy_report_switch else "OFF"))
    else:
        print("Query Energy Report Switch: Failed")

    time.sleep(0.2)

    # 查询最大能量值
    success, max_energy = device.query_max_energy(timeout)
    if success:
        print("Query Max Energy: %d" % max_energy)
    else:
        print("Query Max Energy: Failed")

    time.sleep(0.2)

    # 查询跌倒检测开关
    success, fall_detection_switch = device.query_fall_detection_switch(timeout)
    if success:
        print("Query Fall Detection Switch: %s" % ("ON" if fall_detection_switch else "OFF"))
    else:
        print("Query Fall Detection Switch: Failed")

    time.sleep(0.2)

    # 查询跌倒状态
    success, fall_status = device.query_fall_status(timeout)
    if success:
        print("Query Fall Status: %s" % ("Fall detected" if fall_status == 1 else "No fall"))
    else:
        print("Query Fall Status: Failed")

    time.sleep(0.2)

    # 查询跌倒时长
    success, fall_duration = device.query_fall_duration(timeout)
    if success:
        print("Query Fall Duration: %d seconds" % fall_duration)
    else:
        print("Query Fall Duration: Failed")

    time.sleep(0.2)

    # 查询静止驻留时长
    success, static_stay_duration = device.query_static_stay_duration(timeout)
    if success:
        print("Query Static Stay Duration: %d seconds" % static_stay_duration)
    else:
        print("Query Static Stay Duration: Failed")

    time.sleep(0.2)

    # 查询静止驻留开关
    success, static_stay_switch = device.query_static_stay_switch(timeout)
    if success:
        print("Query Static Stay Switch: %s" % ("ON" if static_stay_switch else "OFF"))
    else:
        print("Query Static Stay Switch: Failed")

    time.sleep(0.2)

    # 查询静止驻留状态
    success, static_stay_status = device.query_static_stay_status(timeout)
    if success:
        print("Query Static Stay Status: %s" % ("Stationary detected" if static_stay_status == 1 else "Not stationary"))
    else:
        print("Query Static Stay Status: Failed")

    time.sleep(0.2)

    # 查询高度累积时间
    success, height_accumulation_time = device.query_height_accumulation_time(timeout)
    if success:
        print("Query Height Accumulation Time: %d seconds" % height_accumulation_time)
    else:
        print("Query Height Accumulation Time: Failed")

    time.sleep(0.2)

    # 查询跌倒打破高度
    success, fall_break_height = device.query_fall_break_height(timeout)
    if success:
        print("Query Fall Break Height: %d cm" % fall_break_height)
    else:
        print("Query Fall Break Height: Failed")

    time.sleep(0.2)

    # 查询高度占比开关
    success, height_ratio_switch = device.query_height_ratio_switch(timeout)
    if success:
        print("Query Height Ratio Switch: %s" % ("ON" if height_ratio_switch else "OFF"))
    else:
        print("Query Height Ratio Switch: Failed")

    time.sleep(0.2)

    # 查询跌倒灵敏度
    success, fall_sensitivity = device.query_fall_sensitivity(timeout)
    if success:
        print("Query Fall Sensitivity: %d" % fall_sensitivity)
    else:
        print("Query Fall Sensitivity: Failed")

    print("=" * 50)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时
time.sleep(3)
# 打印调试信息
print("FreakStudio: Using R60AFD1 millimeter wave information collection")

# 初始化UART0：TX=16, RX=17，波特率115200
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9), timeout=0)
hc0 = HC08(uart1)
# 创建DataFlowProcessor实例
processor = DataFlowProcessor(uart)

# 创建R60AFD1实例
# 启用调试模式（可选）
R60AFD1.DEBUG_ENABLED = False

device = R60AFD1(
    processor,
    presence_enabled=True,  # 启用人体存在检测
    track_report_enabled=True,  # 启用轨迹点上报
    energy_report_enabled=True,  # 启用能量值上报
    height_ratio_enabled=True,  # 启用高度占比上报
    fall_detection_enabled=True,  # 启用跌倒检测
    static_stay_enabled=True,  # 启用静止驻留检测
    static_distance=50,  # 静坐水平距离50cm
    motion_distance=100,  # 运动水平距离100cm
    parse_interval=200,  # 数据解析间隔200ms
    max_retries=3,  # 最大重试次数3次
    retry_delay=100,  # 重试延迟100ms
    init_timeout=5000  # 初始化超时5秒
)

# 打印配置状态
print("\nDevice Configuration Status:")
config_status = device.get_configuration_status()
print("Initialization Complete: %s" % config_status['initialization_complete'])
print("Configuration Errors: %d" % len(config_status['configuration_errors']))

if len(config_status['configuration_errors']) > 0:
    print("Configuration Error Details:")
    for error in config_status['configuration_errors']:
        print("  - %s" % error)

# 打印设备信息
device_info = config_status['device_info']
print("\nDevice Information:")
print("  Product Model: %s" % device_info['product_model'])
print("  Product ID: %s" % device_info['product_id'])
print("  Hardware Model: %s" % device_info['hardware_model'])
print("  Firmware Version: %s" % device_info['firmware_version'])
print("  System Initialized: %s" % device_info['system_initialized'])
print("  Working Duration: %d seconds" % device_info['working_duration'])
print("  Radar Fault Status: %d" % device_info['radar_fault_status'])
print("  Scene Info: %d" % device_info['scene_info'])

# 打印功能开关状态
func_switches = config_status['function_switches']
print("\nFunction Switches:")

time.sleep(1)

# ========================================  主程序  ===========================================

try:
    print("\nStarting main loop...")
    print("Press Ctrl+C to stop the program\n")
    # 跌倒功能设置
    # 设置安装高度为200cm
    device.set_install_height(height_cm=240)
    # 打破跌倒高度
    device.set_fall_break_height(height_cm=100)
    # 跌倒灵敏度
    device.set_fall_sensitivity(sensitivity=3)
    # 跌倒时长
    device.set_fall_duration(seconds=6)

    # 驻留检测设置
    device.set_static_stay_duration(seconds=90)


    while True:
        current_time = time.ticks_ms()

        # 定期打印传感器数据
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 打印主动上报的数据
            print_report_sensor_data()
            fall_status = device.fall_status
            static_stay_status = device.static_stay_status
            presence_status = device.presence_status

            hc0.send_data("\n" + "=" * 40 + "\n")
            hc0.send_data("STATUS DETECTION\n")
            hc0.send_data("-" * 40 + "\n")
            hc0.send_data(f"Fall Status: {fall_status}\n")
            hc0.send_data(f"Static Stay Status: {static_stay_status}\n")
            hc0.send_data(f"Presence Status: {presence_status}\n")
            hc0.send_data("=" * 40 + "\n")
            # 查询并打印人体存在状态
            success, presence_status = device.query_presence_status()
            if success:
                print("Active Query Presence Status: %s" % ("Someone" if presence_status == 1 else "No one"))
            else:
                print("Active Query Presence Status: Failed")

            last_print_time = current_time

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