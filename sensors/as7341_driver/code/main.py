# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午9:00
# @Author  : hogeiha
# @File    : main.py
# @Description : Raspberry Pi Pico驱动AS7341光谱传感器 配置参数 读取光谱数据 控制LED和GPIO 配置中断 + 新增颜色识别功能

# ======================================== 导入相关模块 =========================================

import sys
import time
from machine import I2C, Pin

# 导入AS7341驱动并创建传感器对象
from as7341 import AS7341

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# 初始化I2C总线
def init_i2c():
    """
    初始化I2C总线
    Args:无

    Raises:无

    Notes:适用于RP2040平台，其他开发板需修改引脚定义

    ==========================================
    Initialize I2C bus
    Args:None

    Raises:None

    Notes:Adapted for RP2040 platform, modify pin definitions for other boards
    """
    try:
        # 创建I2C0对象，SCL=5，SDA=4，频率100kHz
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
        # 扫描I2C总线上的所有设备
        detected_devices = [hex(addr) for addr in i2c.scan()]
        # 打印检测到的设备地址
        print(f"I2C initialization successful, detected device addresses: {', '.join(detected_devices)}")
        # 检查AS7341传感器是否在线（默认地址0x39）
        if "0x39" not in detected_devices:
            print("Warning: AS7341 sensor not detected (default address 0x39)")
        return i2c
    except Exception as e:
        print(f"I2C initialization failed: {e}")
        return None


# 打印分隔线标题
def print_separator(title):
    """
    打印分隔线标题
    Args:title: 要显示的标题文字

    Raises:无

    Notes:提高输出可读性

    ==========================================
    Print separator title
    Args:title: Title text to display

    Raises:None

    Notes:Improve output readability
    """
    print("\n" + "=" * 70)
    print(f"=== {title}")
    print("=" * 70)


# 安全执行函数
def safe_execute(func, *args, desc="operation"):
    """
    安全执行函数并捕获异常
    Args:func: 要执行的函数
         *args: 函数参数
         desc: 操作描述

    Raises:无

    Notes:无

    ==========================================
    Safely execute function and catch exceptions
    Args:func: Function to execute
         *args: Function arguments
         desc: Operation description

    Raises:None

    Notes:None
    """
    try:
        result = func(*args)
        return result, True
    except Exception as e:
        print(f"  Operation {desc} failed: {e}")
        return None, False


# 光谱数据转RGB值
def spectrum_to_rgb(f1, f2, f3, f4, f5, f6, f7, f8):
    """
    将AS7341 8通道光谱数据转换为RGB值
    Args:f1-f8: 8个光谱通道的原始数据

    Raises:无

    Notes:通道对应关系：F1(紫)、F2(蓝)、F3(青)、F4(绿)、F5(绿黄)、F6(黄橙)、F7(橙红)、F8(红)

    ==========================================
    Convert AS7341 8-channel spectral data to RGB values
    Args:f1-f8: Raw data from 8 spectral channels

    Raises:None

    Notes:Channel mapping: F1(Violet), F2(Blue), F3(Cyan), F4(Green), F5(Green-Yellow), F6(Yellow-Orange), F7(Orange-Red), F8(Red)
    """
    # 获取所有通道的最大值用于归一化
    max_val = max(f1, f2, f3, f4, f5, f6, f7, f8)
    if max_val == 0:
        return (0, 0, 0)

    # 按波长分配RGB权重：红光通道使用F7和F8
    r = (f7 + f8 * 1.2) / max_val * 255
    # 绿光通道使用F4和F5
    g = (f4 + f5 * 1.1) / max_val * 255
    # 蓝光通道使用F2和F3
    b = (f2 + f3 * 0.9) / max_val * 255

    return (int(r), int(g), int(b))


# 根据RGB值获取颜色名称
def get_color_name(r, g, b):
    """
    根据RGB值识别颜色名称
    Args:r: 红色分量（0-255）
         g: 绿色分量（0-255）
         b: 蓝色分量（0-255）

    Raises:无

    Notes:颜色识别阈值可根据实际光照条件调整

    ==========================================
    Get color name based on RGB values
    Args:r: Red component (0-255)
         g: Green component (0-255)
         b: Blue component (0-255)

    Raises:None

    Notes:Color recognition threshold can be adjusted based on actual lighting conditions
    """
    threshold = 40
    # 判断是否为黑色/无光
    if r < threshold and g < threshold and b < threshold:
        return "Black/No Light"
    # 判断是否为白色
    elif r > 200 and g > 200 and b > 200:
        return "White"
    # 判断是否为红色
    elif r > g + 50 and r > b + 50:
        return "Red"
    # 判断是否为绿色
    elif g > r + 50 and g > b + 50:
        return "Green"
    # 判断是否为蓝色
    elif b > r + 50 and b > g + 50:
        return "Blue"
    # 判断是否为黄色
    elif r > 150 and g > 150 and b < 100:
        return "Yellow"
    # 判断是否为紫色
    elif r > 150 and b > 150 and g < 100:
        return "Purple"
    # 判断是否为青色
    elif g > 150 and b > 150 and r < 100:
        return "Cyan"
    # 判断是否为橙色
    elif r > g and g > b:
        return "Orange"
    else:
        return "Mixed Color"


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒等待硬件稳定
time.sleep(3)
print("FreakStudio: AS7341 spectral sensor configuration and measurement demonstration on Raspberry Pi Pico")

# 初始化I2C总线
i2c = init_i2c()
if not i2c:
    sys.exit(1)

sensor = AS7341(i2c)

# 检查传感器连接状态
if not sensor.isconnected():
    print("Failed to connect to AS7341 sensor, program exited")
    sys.exit(1)
print("AS7341 sensor initialized successfully!")

# ========================================  主程序  ============================================

# 1. 基本配置演示（积分时间、增益、测量模式）
print_separator("1. Basic parameter configuration demonstration")

# 1.1 设置积分时间（ASTEP + ATIME）
print("\n  [Integration time configuration]")
# 设置ASTEP步长值为599
sensor.set_astep(599)
astep_time = sensor.get_astep_time()
print(f"    ASTEP set value: 599 -> step time: {astep_time:.3f} ms")

# 设置ATIME积分步数为29
sensor.set_atime(29)
int_time = sensor.get_integration_time()
overflow_count = sensor.get_overflow_count()
print(f"    ATIME set value: 29 -> total integration time: {int_time:.2f} ms")
print(f"    Maximum count value: {overflow_count}")

# 1.2 设置增益（AGAIN）
print("\n  [Gain configuration]")
# 通过增益代码设置（代码4对应增益8倍）
sensor.set_again(4)
gain_code = sensor.get_again()
gain_factor = sensor.get_again_factor()
print(f"    Gain code set to 4 -> actual gain code: {gain_code}, gain factor: {gain_factor}x")

# 通过增益倍数设置（自动转换为对应代码）
sensor.set_again_factor(16)
gain_code2 = sensor.get_again()
gain_factor2 = sensor.get_again_factor()
print(f"    Gain factor set to 16 -> actual gain code: {gain_code2}, gain factor: {gain_factor2}x")

# 1.3 设置测量模式为SPM单脉冲模式
sensor.set_measure_mode(AS7341.AS7341_MODE_SPM)
print("\n  Measurement mode set to SPM (single pulse mode)")
time.sleep(1)

# 2. 光谱测量演示（所有预设通道映射）
print_separator("2. Spectral measurement demonstration (all channels)")

# 定义通道映射描述字典
channel_maps = {
    "F1F4CN": "F1(405-425nm), F2(435-455nm), F3(470-490nm), F4(505-525nm), CLEAR, NIR",
    "F5F8CN": "F5(545-565nm), F6(580-600nm), F7(620-640nm), F8(670-690nm), CLEAR, NIR",
    "F2F7": "F2(435-455nm), F3(470-490nm), F4(505-525nm), F5(545-565nm), F6(580-600nm), F7(620-640nm)",
    "F3F8": "F3(470-490nm), F4(505-525nm), F5(545-565nm), F6(580-600nm), F7(620-640nm), F8(670-690nm)",
}

# 遍历所有预设通道映射进行测量
for map_name, desc in channel_maps.items():
    print(f"\n  Measurement channel: {map_name} -> {desc}")
    # 开始测量并指定通道映射
    sensor.start_measure(map_name)
    # 获取光谱数据
    data, success = safe_execute(sensor.get_spectral_data, desc=f"read {map_name} data")
    if success and data:
        # 根据不同通道映射格式化输出
        if map_name == "F1F4CN":
            f1, f2, f3, f4, clr, nir = data
            print(f"    F1: {f1:6d} | F2: {f2:6d} | F3: {f3:6d} | F4: {f4:6d} | CLEAR: {clr:6d} | NIR: {nir:6d}")
        elif map_name == "F5F8CN":
            f5, f6, f7, f8, clr, nir = data
            print(f"    F5: {f5:6d} | F6: {f6:6d} | F7: {f7:6d} | F8: {f8:6d} | CLEAR: {clr:6d} | NIR: {nir:6d}")
        elif map_name == "F2F7":
            f2, f3, f4, f5, f6, f7 = data
            print(f"    F2: {f2:6d} | F3: {f3:6d} | F3: {f3:6d} | F5: {f5:6d} | F6: {f6:6d} | F7: {f7:6d}")
        elif map_name == "F3F8":
            f3, f4, f5, f6, f7, f8 = data
            print(f"    F3: {f3:6d} | F4: {f4:6d} | F5: {f5:6d} | F6: {f6:6d} | F7: {f7:6d} | F8: {f8:6d}")
    time.sleep_ms(500)

# 3. 单通道数据读取演示
print_separator("3. Single channel data reading demonstration")
# 先切换到F1F4CN映射
sensor.start_measure("F1F4CN")
for ch in range(6):
    ch_data = sensor.get_channel_data(ch)
    ch_names = ["F1", "F2", "F3", "F4", "CLEAR", "NIR"]
    print(f"  Channel {ch} ({ch_names[ch]}): {ch_data}")

# 4. 板载LED控制演示
print_separator("4. On-board LED control demonstration")
# LED电流可选值：4,8,12,16,20 mA
led_currents = [4, 8, 12, 16, 20]
for curr in led_currents:
    sensor.set_led_current(curr)
    print(f"  Set LED current: {curr} mA (on for 2 seconds)")
    time.sleep(2)

# 关闭LED
sensor.set_led_current(0)
print("  LED turned off")

# 6. GPIO引脚控制演示
print_separator("6. GPIO pin control demonstration")
# 配置GPIO为输出模式（普通模式）
sensor.set_gpio_output(inverted=False)
print("  GPIO configured as output mode (normal) -> LED on (if connected)")
time.sleep(1)

# 反转GPIO输出
sensor.set_gpio_inverted(True)
print("  GPIO output inverted -> LED off (if connected)")
time.sleep(1)

# 配置GPIO为输入模式
sensor.set_gpio_input(enable=True)
gpio_value = sensor.get_gpio_value()
print(f"  GPIO configured as input mode -> current GPIO value: {gpio_value} (True=high, False=low)")

# 7. 中断配置演示
print_separator("7. Interrupt configuration demonstration")
# 设置光谱中断阈值（低阈值1000，高阈值10000）
sensor.set_thresholds(1000, 10000)
lo_th, hi_th = sensor.get_thresholds()
print(f"  Set spectral interrupt thresholds -> low threshold: {lo_th}, high threshold: {hi_th}")

# 设置中断持久性（连续3次超过阈值后触发）
sensor.set_interrupt_persistence(3)
print("  Set interrupt persistence: 3")

# 使能光谱中断
sensor.set_spectral_interrupt(True)
print("  Enabled spectral interrupt")

# 检查并清除中断
interrupt_status = sensor.check_interrupt()
print(f"  Current interrupt status: {interrupt_status}")
sensor.clear_interrupt()
print("  Cleared all interrupts")

# 8. 自动重启配置演示（WTIME）
print_separator("8. Auto restart (WTIME) configuration demonstration")
# 设置WTIME自动重启间隔为99
sensor.set_wtime(99)
# 使能自动重启功能
sensor.set_wen(True)
print("  Set WTIME=99 -> auto restart interval ~278ms, WEN enabled")

print_separator("9. Color Recognition Demonstration")

# 读取完整的8通道光谱数据
try:
    while True:
        # 读取F1-F4及CLEAR、NIR通道数据
        sensor.start_measure("F1F4CN")
        f1, f2, f3, f4, _, _ = sensor.get_spectral_data()
        # 读取F5-F8及CLEAR、NIR通道数据
        sensor.start_measure("F5F8CN")
        f5, f6, f7, f8, _, _ = sensor.get_spectral_data()

        # 打印原始光谱数据
        print(f"\n  8-channel raw data: F1={f1}, F2={f2}, F3={f3}, F4={f4}")
        print(f"                    F5={f5}, F6={f6}, F7={f7}, F8={f8}")

        # 转换为RGB值
        rgb = spectrum_to_rgb(f1, f2, f3, f4, f5, f6, f7, f8)
        color_name = get_color_name(rgb[0], rgb[1], rgb[2])

        # 输出识别结果
        print(f"  Converted RGB values: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}")
        print(f"  Recognition result: 【 {color_name} 】")

        time.sleep(1)

except Exception as e:
    print(f"  Color recognition failed: {e}")
