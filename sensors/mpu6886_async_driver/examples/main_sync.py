# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Mika Tuupola
# @File    : main.py
# @Description : 测试 MPU6886 6轴运动传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin
import micropython
from mpu6886 import MPU6886, SF_G, SF_DEG_S

# ======================================== 全局变量 ============================================
# I2C 引脚配置（ESP32 为例，可根据实际接线修改）
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
# MPU6886 设备参数
MPU6886_I2C_ADDR = 0x68
# WHO_AM_I 寄存器期望值
MPU6886_CHIP_ID = 0x19

# 打印间隔控制
last_print_time = 0
# 打印间隔（ms）
print_interval = 500
mpu = None


# ======================================== 功能函数 ============================================
def read_sensor_data():
    """
    读取传感器数据并打印（低频核心 API，保留自动执行）
    此函数在主循环中定时调用
    """
    # 读取加速度
    ax, ay, az = mpu.acceleration
    # 读取角速度
    gx, gy, gz = mpu.gyro
    # 读取温度
    temp = mpu.temperature

    print("Accel (m/s^2): X=%.3f, Y=%.3f, Z=%.3f" % (ax, ay, az))
    print("Gyro  (rad/s): X=%.3f, Y=%.3f, Z=%.3f" % (gx, gy, gz))
    print("Temperature: %.2f C" % temp)


def run_gyro_calibration():
    """
    执行陀螺仪校准（模式切换，默认注释调用，可 REPL 手动触发）
    设备必须保持静止状态
    """
    print("Starting gyroscope calibration...")
    print("Please keep the device stationary...")
    offset = mpu.calibrate(count=256, delay=10)
    print("Calibration complete, offset: X=%.4f, Y=%.4f, Z=%.4f" % offset)
    return offset


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 mpu6886.MPU6886

# ======================================== 初始化配置 ===========================================
# 等待设备就绪
time.sleep(3)
print("FreakStudio: MPU6886 6-axis motion sensor driver test")

# 创建 I2C 总线实例
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
print("I2C bus created on SCL=Pin(%d), SDA=Pin(%d)" % (I2C_SCL_PIN, I2C_SDA_PIN))

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found I2C devices at addresses: %s" % [hex(addr) for addr in devices])

# 检查目标设备是否存在
if MPU6886_I2C_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % MPU6886_I2C_ADDR)
print("Device found at 0x%02X" % MPU6886_I2C_ADDR)

# 创建 MPU6886 驱动实例
mpu = MPU6886(i2c, address=MPU6886_I2C_ADDR, debug=False)
print("MPU6886 driver instance created")

# 读取并验证芯片 ID
chip_id = mpu.whoami
if chip_id == MPU6886_CHIP_ID:
    print("Device verified: MPU6886 found (ID: 0x%02X)" % chip_id)
else:
    print("Warning: Unexpected chip ID 0x%02X (expected 0x%02X)" % (chip_id, MPU6886_CHIP_ID))

# 读取初始传感器数据
ax, ay, az = mpu.acceleration
gx, gy, gz = mpu.gyro
temp = mpu.temperature
print("Initial readings:")
print("  Acceleration (m/s^2): X=%.3f, Y=%.3f, Z=%.3f" % (ax, ay, az))
print("  Gyroscope (rad/s): X=%.3f, Y=%.3f, Z=%.3f" % (gx, gy, gz))
print("  Temperature: %.2f C" % temp)


# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

try:
    # 上下文管理器示例（读取一次进行对比）
    with MPU6886(i2c, address=MPU6886_I2C_ADDR) as ctx_mpu:
        ctx_ax, ctx_ay, ctx_az = ctx_mpu.acceleration
        ctx_gx, ctx_gy, ctx_gz = ctx_mpu.gyro
        ctx_temp = ctx_mpu.temperature
        print("Context manager test:")
        print("  Accel (m/s^2): X=%.3f, Y=%.3f, Z=%.3f" % (ctx_ax, ctx_ay, ctx_az))
        print("  Gyro  (rad/s): X=%.3f, Y=%.3f, Z=%.3f" % (ctx_gx, ctx_gy, ctx_gz))
        print("  Temperature: %.2f C" % ctx_temp)

    # 主循环：定时读取传感器数据
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            read_sensor_data()
            last_print_time = current_time

        # 陀螺仪校准，注释默认执行，可 REPL 手动触发
        # run_gyro_calibration()

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    mpu.deinit()
    mpu = None
    print("Program exited")
