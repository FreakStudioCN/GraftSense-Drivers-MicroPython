# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 ADT7410 高精度数字温度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from adt7410 import (
    ADT7410,
    CONTINUOUS,
    ONE_SHOT,
    SPS,
    SHUTDOWN,
    LOW_RESOLUTION,
    HIGH_RESOLUTION,
    COMP_DISABLED,
    COMP_ENABLED,
)


# ======================================== 全局变量 ============================================

# I2C 引脚配置（请根据实际接线修改）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4

# ADT7410 参数
I2C_ADDR = 0x48
WHOAMI_REG = 0x0B
EXPECTED_DEVICE_ID = 0xCB

# 打印间隔（毫秒）
PRINT_INTERVAL = 2000

# ======================================== 初始化配置 ==========================================


def print_temperature_detail(adt):
    """
    打印详细的温度信息（低频，自动执行）
    """
    temp = adt.temperature
    mode = adt.operation_mode
    resolution = adt.resolution_mode
    print("Temperature: %.4f C | Mode: %s | Resolution: %s" % (temp, mode, resolution))


def test_operation_modes(adt):
    """
    遍历所有工作模式并打印当前温度（模式切换，默认注释调用，可 REPL 手动触发）

    测试 CONTINUOUS → ONE_SHOT → SPS → SHUTDOWN 完整切换流程。
    SPS 模式下每秒一次转换，SHUTDOWN 模式下读取最后一次转换结果。
    """
    print("=== Testing All Operation Modes ===")
    for mode_val, mode_name in [
        (CONTINUOUS, "CONTINUOUS"),
        (ONE_SHOT, "ONE_SHOT"),
        (SPS, "SPS"),
        (SHUTDOWN, "SHUTDOWN"),
    ]:
        adt.operation_mode = mode_val
        print("Mode: %s" % mode_name)
        # SPS 模式需等待 1s 获取第一次转换结果
        if mode_val == SPS:
            time.sleep(1.5)
        else:
            time.sleep(0.3)
        print("  Temperature: %.4f C" % adt.temperature)
    # 恢复到连续模式
    adt.operation_mode = CONTINUOUS
    time.sleep(0.3)
    print("=== Operation Mode Test Complete ===\n")


def test_resolution_modes(adt):
    """
    测试分辨率切换对温度读数的影响（模式切换，默认注释调用，可 REPL 手动触发）

    对比 LOW_RESOLUTION（13 位，0.0625°C）和 HIGH_RESOLUTION（16 位，0.0078°C）。
    """
    print("=== Testing Resolution Modes ===")
    adt.resolution_mode = LOW_RESOLUTION
    time.sleep(0.3)
    temp_low = adt.temperature
    print("LOW_RESOLUTION  (13-bit): %.4f C" % temp_low)

    adt.resolution_mode = HIGH_RESOLUTION
    time.sleep(0.3)
    temp_high = adt.temperature
    print("HIGH_RESOLUTION (16-bit): %.4f C" % temp_high)
    print("Difference: %.4f C" % abs(temp_high - temp_low))
    print("=== Resolution Mode Test Complete ===\n")


def test_comparator_mode(adt):
    """
    测试比较器模式开关（模式切换，默认注释调用，可 REPL 手动触发）

    演示设置温度阈值后启用比较器模式，观察告警状态变化。
    """
    print("=== Testing Comparator Mode ===")
    current_temp = adt.temperature
    # 设置阈值：以当前温度为基准 ±5°C
    adt.high_temperature = int(current_temp) + 5
    adt.low_temperature = int(current_temp) - 5
    adt.critical_temperature = int(current_temp) + 20
    adt.hysteresis_temperature = 2
    print(
        "Thresholds set: High=%d C, Low=%d C, Critical=%d C, Hysteresis=%d C"
        % (
            adt.high_temperature,
            adt.low_temperature,
            adt.critical_temperature,
            adt.hysteresis_temperature,
        )
    )

    # 启用比较器模式
    adt.comparator_mode = COMP_ENABLED
    print("Comparator mode: %s" % adt.comparator_mode)
    alert = adt.alert_status
    print("Alert status: high=%s low=%s critical=%s" % (alert.high_alert, alert.low_alert, alert.critical_alert))

    # 恢复：禁用比较器
    adt.comparator_mode = COMP_DISABLED
    print("Comparator mode: %s" % adt.comparator_mode)
    print("=== Comparator Mode Test Complete ===\n")


def test_boundary_thresholds(adt):
    """
    测试温度阈值的边界值设置（边界参数，默认注释调用，可 REPL 手动触发）

    验证 -55°C（最小值）和 150°C（最大值）的阈值设置与读取。
    """
    print("=== Testing Boundary Temperature Thresholds ===")
    original_high = adt.high_temperature
    original_low = adt.low_temperature
    original_critical = adt.critical_temperature
    original_hysteresis = adt.hysteresis_temperature

    # 测试极端值
    adt.high_temperature = 150
    print("High temperature set to max: %d C" % adt.high_temperature)

    adt.low_temperature = -55
    print("Low temperature set to min: %d C" % adt.low_temperature)

    adt.critical_temperature = 150
    print("Critical temperature set to max: %d C" % adt.critical_temperature)

    adt.hysteresis_temperature = 0
    print("Hysteresis set to min: %d C" % adt.hysteresis_temperature)

    adt.hysteresis_temperature = 15
    print("Hysteresis set to max: %d C" % adt.hysteresis_temperature)

    # 恢复原始值
    adt.high_temperature = original_high
    adt.low_temperature = original_low
    adt.critical_temperature = original_critical
    adt.hysteresis_temperature = original_hysteresis
    print("Thresholds restored to original values")
    print("=== Boundary Threshold Test Complete ===\n")


def test_invalid_operation_mode(adt):
    """
    测试无效操作模式的异常处理（异常参数，默认注释调用，可 REPL 手动触发）
    """
    print("=== Testing Invalid Operation Mode ===")
    try:
        adt.operation_mode = 99
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print("Caught expected ValueError: %s" % e)
    print("=== Invalid Operation Mode Test Complete ===\n")


def test_invalid_temperature_threshold(adt):
    """
    测试超出范围的温度阈值的异常处理（异常参数，默认注释调用，可 REPL 手动触发）
    """
    print("=== Testing Invalid Temperature Threshold ===")
    try:
        adt.high_temperature = 200
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print("Caught expected ValueError: %s" % e)
    try:
        adt.low_temperature = -100
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print("Caught expected ValueError: %s" % e)
    print("=== Invalid Temperature Threshold Test Complete ===\n")


def test_invalid_hysteresis(adt):
    """
    测试超出范围的迟滞值的异常处理（异常参数，默认注释调用，可 REPL 手动触发）
    """
    print("=== Testing Invalid Hysteresis ===")
    try:
        adt.hysteresis_temperature = 20
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print("Caught expected ValueError: %s" % e)
    try:
        adt.hysteresis_temperature = -5
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print("Caught expected ValueError: %s" % e)
    print("=== Invalid Hysteresis Test Complete ===\n")


def test_reset(adt):
    """
    测试传感器复位功能（模式切换，默认注释调用，可 REPL 手动触发）

    复位后验证传感器仍可正常读取温度。
    """
    print("=== Testing Sensor Reset ===")
    print("Before reset - Temperature: %.4f C" % adt.temperature)
    print("Before reset - Operation mode: %s" % adt.operation_mode)
    adt.reset()
    time.sleep(0.3)
    print("After reset  - Temperature: %.4f C" % adt.temperature)
    print("After reset  - Operation mode: %s" % adt.operation_mode)
    print("=== Sensor Reset Test Complete ===\n")


def test_context_manager(i2c):
    """
    测试上下文管理器（with 语句）自动资源释放（批量操作，默认注释调用，可 REPL 一键执行）
    """
    print("=== Testing Context Manager ===")
    with ADT7410(i2c, address=I2C_ADDR) as adt:
        temp = adt.temperature
        print("Temperature via context manager: %.4f C" % temp)
    print("Context manager exited, resources released")
    print("=== Context Manager Test Complete ===\n")


def i2c_scan_and_verify(i2c, expected_addr):
    """
    扫描 I2C 总线并验证目标设备是否存在

    Args:
        i2c: I2C 总线实例
        expected_addr: 期望的设备地址

    Returns:
        bool: 设备是否找到并验证通过

    Raises:
        RuntimeError: 总线上无设备或目标设备未找到
    """
    print("Scanning I2C bus...")
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    print("Found %d device(s): %s" % (len(devices), str([hex(d) for d in devices])))

    # 查找目标设备
    if expected_addr not in devices:
        raise RuntimeError("Device not found at expected address 0x%02X, found: %s" % (expected_addr, str([hex(d) for d in devices])))
    print("Target device found at 0x%02X" % expected_addr)

    # 读取芯片 ID 寄存器进行验证
    try:
        whoami = i2c.readfrom_mem(expected_addr, WHOAMI_REG, 1)[0]
    except OSError as e:
        raise RuntimeError("Failed to read WHOAMI register at 0x%02X" % WHOAMI_REG) from e

    if whoami == EXPECTED_DEVICE_ID:
        print("Device ID verified: 0x%02X (expected 0x%02X) - ADT7410 confirmed" % (whoami, EXPECTED_DEVICE_ID))
        return True
    else:
        print("Device ID mismatch: got 0x%02X, expected 0x%02X" % (whoami, EXPECTED_DEVICE_ID))
        return False


# ======================================== 自定义类 ============================================

# ======================================== 功能函数 ============================================

# 上电稳定等待
time.sleep(3)

print("FreakStudio: ADT7410 High-Accuracy Digital Temperature Sensor Test")
print("=" * 60)

# 初始化 I2C 总线
print("Initializing I2C bus: SCL=Pin(%d), SDA=Pin(%d)" % (I2C_SCL_PIN, I2C_SDA_PIN))
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
last_print_time = time.ticks_ms()

# I2C 设备扫描与 ID 验证
i2c_scan_and_verify(i2c, I2C_ADDR)

# 创建 ADT7410 驱动实例
print("Initializing ADT7410 sensor at address 0x%02X..." % I2C_ADDR)
adt = ADT7410(i2c, address=I2C_ADDR)

# 初始化信息打印
print("ADT7410 initialized successfully")
print("Current temperature: %.4f C" % adt.temperature)
print("Operation mode: %s" % adt.operation_mode)
print("Resolution mode: %s" % adt.resolution_mode)
print("Alert status: %s" % str(adt.alert_status))
print("=" * 60)
print("Entering main loop (Ctrl+C to exit)...\n")

# ======================================== 主程序 ==============================================

try:
    while True:
        current_time = time.ticks_ms()

        # 定时打印温度（低频，自动执行）
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            print_temperature_detail(adt)
            last_print_time = current_time

        # --- 以下函数默认注释调用，可在 REPL 中手动执行 ---

        # test_operation_modes(adt)           # 遍历所有工作模式
        # test_resolution_modes(adt)          # 测试分辨率切换对比
        # test_comparator_mode(adt)            # 测试比较器模式与告警
        # test_boundary_thresholds(adt)        # 测试温度阈值边界值
        # test_invalid_operation_mode(adt)     # 测试无效操作模式异常
        # test_invalid_temperature_threshold(adt)  # 测试超范围温度阈值异常
        # test_invalid_hysteresis(adt)         # 测试超范围迟滞值异常
        # test_reset(adt)                      # 测试传感器复位
        # test_context_manager(i2c)            # 测试上下文管理器（将创建新实例）

        # 主循环节流
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    adt.deinit()
    del adt
    print("Program exited")
