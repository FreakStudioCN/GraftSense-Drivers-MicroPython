# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午4:00
# @Author  : PinsonJonas
# @File    : main.py
# @Description : MPL3115A2传感器测试 读取气压海拔温度 异常处理演示

# ======================================== 导入相关模块 =========================================

import time
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

time.sleep(3)
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
        time.sleep(SAMPLING_INTERVAL)

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
        time.sleep(SAMPLING_INTERVAL)

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

        time.sleep(LONG_MONITOR_INTERVAL)

except Exception as e:
    print(f"   Long-term monitoring failed: {e}")

# 程序结束提示
print_separator("Demonstration completed")
print("   All MPL3115A2 function demonstrations finished")
