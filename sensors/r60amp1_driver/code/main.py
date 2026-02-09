# Python env   : MicroPython v1.26.1
# -*- coding: utf-8 -*-
# @Time    : 2025/11/4 下午5:33
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试R60AMP1多人轨迹雷达设备驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin, Timer
import time
from data_flow_processor import DataFlowProcessor
from r60amp1 import R60AMP1, format_time
from hc08 import HC08

# ======================================== 全局变量 ============================================

# 启用调试模式（可选）
R60AMP1.DEBUG_ENABLED = True

# 上次打印时间
last_print_time = time.ticks_ms()

# 定时打印间隔：2秒打印一次
print_interval = 2000

# ======================================== 功能函数 ============================================

def print_report_sensor_data():
    """
    打印传感器上报数据到Thonny控制台。

    Note：此函数打印的是设备主动上报的数据，不是查询结果。
    数据来源于R60AMP1类的属性值，这些属性会在定时器回调中自动更新。

    ==========================================

    Print sensor reported data to Thonny console.

    Note: This function prints data actively reported by the device, not query results.
    Data comes from R60AMP1 class attributes, which are automatically updated in timer callbacks.
    """
    # 声明全局变量
    global device

    print("=" * 50)
    print("%s Sensor Data" % format_time())
    print("=" * 50)

    # 系统级信息
    print("System Initialized: %s" % ("Yes" if device.system_initialized else "No"))
    print("Radar Fault Status: %s" % ["Normal", "Radar chip error", "Encryption error"][
        device.radar_fault_status] if device.radar_fault_status < 3 else "Unknown")
    print("Environment Mode: %s" % ["Default", "Living Room", "Bedroom", "Bathroom"][
        device.environment_mode] if device.environment_mode < 4 else "Unknown")

    # 产品信息
    print("Product Model: %s" % device.product_model)
    print("Product ID: %s" % device.product_id)
    print("Hardware Model: %s" % device.hardware_model)
    print("Firmware Version: %s" % device.firmware_version)

    # 人体存在检测
    print("Presence Status: %s" % ("Someone" if device.presence_status == R60AMP1.PRESENCE_PERSON else "No one"))
    print("Motion Status: %s" % ["No motion", "Static", "Active"][
        device.motion_status] if device.motion_status < 3 else "Unknown")
    print("Body Motion Parameter: %d" % device.body_motion_param)
    print("Presence Function Enabled: %s" % ("ON" if device.presence_enabled else "OFF"))

    # 轨迹信息
    if device.trajectory_targets:
        print("\nTrajectory Targets (%d):" % len(device.trajectory_targets))
        for i, target in enumerate(device.trajectory_targets):
            print("  Target %d:" % (i + 1))
            print("    Index: %d" % target['index'])
            print("    Size: %d" % target['size'])
            print("    Feature: %s" % ("Static" if target['feature'] == R60AMP1.TARGET_FEATURE_STATIC else "Moving"))
            print("    Position: X=%d cm, Y=%d cm" % (target['x'], target['y']))
            print("    Height: %d cm" % target['height'])
            print("    Speed: %d cm/s" % target['speed'])
    else:
        print("\nNo trajectory targets detected")

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

    # 查询人体存在开关
    success, presence_switch = device.query_human_presence_switch(timeout)
    if success:
        print("Query Presence Switch: %s" % ("ON" if presence_switch else "OFF"))
    else:
        print("Query Presence Switch: Failed")

    time.sleep(0.2)

    # 查询存在状态
    success, presence_status = device.query_presence_status(timeout)
    if success:
        print("Query Presence Status: %s" % ("Someone" if presence_status == R60AMP1.PRESENCE_PERSON else "No one"))
    else:
        print("Query Presence Status: Failed")

    time.sleep(0.2)

    # 查询运动状态
    success, motion_status = device.query_motion_info(timeout)
    if success:
        status_text = ["No motion", "Static", "Active"][motion_status] if motion_status < 3 else "Unknown"
        print("Query Motion Status: %s" % status_text)
    else:
        print("Query Motion Status: Failed")

    time.sleep(0.2)

    # 查询体动参数
    success, body_motion_param = device.query_body_motion_param(timeout)
    if success:
        print("Query Body Motion Parameter: %d" % body_motion_param)
    else:
        print("Query Body Motion Parameter: Failed")

    time.sleep(0.2)

    # 查询轨迹信息
    success, trajectory_targets = device.query_trajectory_info(timeout)
    if success:
        print("Query Trajectory Info: Success")
        if trajectory_targets:
            print("  Number of targets: %d" % len(trajectory_targets))
            for i, target in enumerate(trajectory_targets):
                print("  Target %d: Index=%d, Size=%d, Feature=%s, Position=(%d, %d), Height=%d, Speed=%d" %
                      (i + 1, target['index'], target['size'],
                       "Static" if target['feature'] == R60AMP1.TARGET_FEATURE_STATIC else "Moving",
                       target['x'], target['y'], target['height'], target['speed']))
        else:
            print("  No targets detected")
    else:
        print("Query Trajectory Info: Failed")

    print("=" * 50)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时
time.sleep(3)
# 打印调试信息
print("FreakStudio: Using R60AMP1 Multi-person Trajectory Radar")

# 初始化UART0：TX=16, RX=17，波特率115200
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9), timeout=0)

# 蓝牙
hc0 = HC08(uart1)
# 创建DataFlowProcessor实例
processor = DataFlowProcessor(uart)

# 创建R60AMP1实例

device = R60AMP1(
    processor,
    parse_interval=200,  # 数据解析间隔200ms
    presence_enabled=True,  # 启用人体存在检测
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

# 打印当前设置
current_settings = config_status['current_settings']
print("\nCurrent Settings:")
print("  Presence Detection: %s" % ("ENABLED" if current_settings['presence_enabled'] else "DISABLED"))

time.sleep(1)

# ========================================  主程序  ===========================================

try:
    print("\nStarting main loop...")
    print("Press Ctrl+C to stop the program\n")

    while True:
        current_time = time.ticks_ms()

        # 定期打印传感器数据
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 打印主动上报的数据
            print_report_sensor_data()
            presence_status = device.presence_status
            motion_status = device.motion_status
            body_motion_param = device.body_motion_param
            trajectory_targets = device.trajectory_targets
            hc0.send_data("=== status ===\n")
            hc0.send_data(f"presence_status: {presence_status}\n")
            hc0.send_data(f"motion_status: {motion_status}\n")
            hc0.send_data(f"Body movement: {body_motion_param}\n")
            hc0.send_data(f"Target Quantity: {len(trajectory_targets)}\n")
            hc0.send_data("Trajectory Target:\n")
            for i, target in enumerate(trajectory_targets):
                hc0.send_data(f"  target{i + 1}: {target}\n")
            # 查询并打印存在状态
            success, presence_status = device.query_presence_status()
            if success:
                print("Active Query Presence Status: %s" % (
                    "Someone" if presence_status == R60AMP1.PRESENCE_PERSON else "No one"))
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