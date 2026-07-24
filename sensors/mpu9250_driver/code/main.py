# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : FreakStudio / Mika Tuupola
# @File    : main.py
# @Description : RP2040 test entry for the MPU9250 driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

try:
    import micropython

    micropython.alloc_emergency_exception_buf(100)
except ImportError:
    pass

from machine import I2C, Pin
import time

from mpu9250 import MPU9250

# ======================================== 全局变量 ============================================

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000

MPU9250_ADDR = 0x68
EXPECTED_WHOAMI = 0x71
PRINT_INTERVAL_MS = 2000

sensor = None
last_print_time = 0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)

print("FreakStudio: MPU9250 9-axis IMU driver test")
print("=" * 62)

try:
    print("Initializing I2C bus (id=%d, SCL=GPIO%d, SDA=GPIO%d, %dkHz)..." % (I2C_ID, I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ // 1000))
    i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

    print("Scanning I2C bus...")
    devices = i2c.scan()
    print("Found I2C address(es): %s" % (["0x%02X" % address for address in devices],))

    if MPU9250_ADDR not in devices:
        raise RuntimeError("MPU9250 not found at address 0x%02X" % MPU9250_ADDR)

    print("MPU9250 address 0x%02X found" % MPU9250_ADDR)
    print("Initializing MPU9250...")
    sensor = MPU9250(i2c)

    whoami = sensor.whoami
    if whoami == EXPECTED_WHOAMI:
        print("Device verified: MPU9250 WHOAMI=0x%02X" % whoami)
    else:
        print("Warning: unexpected WHOAMI=0x%02X, expected 0x%02X" % (whoami, EXPECTED_WHOAMI))

    ak8963_id = sensor.ak8963.whoami
    print("AK8963 WHOAMI: 0x%02X" % ak8963_id)
    print("Fuse ROM adjustment: X=%.4f Y=%.4f Z=%.4f" % sensor.ak8963.adjustement)

    last_print_time = time.ticks_ms()
    print("Starting 9-axis data acquisition...")
except OSError as error:
    print("I2C initialization failed: %s" % error)
    raise
except RuntimeError as error:
    if "AK8963" in str(error):
        print("Magnetometer initialization failed: %s" % error)
    else:
        print("Sensor initialization failed: %s" % error)
    raise
except Exception as error:
    print("Unexpected initialization error: %s" % error)
    raise


def calibrate_gyro(sensor_instance, count=256):
    if not hasattr(sensor_instance, "mpu6500"):
        raise ValueError("sensor_instance must be an MPU9250 instance")
    if not isinstance(count, int) or count <= 0:
        raise ValueError("count must be a positive int")

    print("Starting gyroscope calibration...")
    print(">>> Keep sensor still")
    offset = sensor_instance.mpu6500.calibrate(count, 0)
    print("Gyro offset (rad/s): X=%.5f Y=%.5f Z=%.5f" % offset)
    return offset


def calibrate_magnetometer(sensor_instance, count=256, delay=200):
    if not hasattr(sensor_instance, "ak8963"):
        raise ValueError("sensor_instance must be an MPU9250 instance")
    if not isinstance(count, int) or count <= 0:
        raise ValueError("count must be a positive int")
    if not isinstance(delay, int) or delay < 0:
        raise ValueError("delay must be a non-negative int")

    print("Starting magnetometer calibration...")
    print(">>> Slowly rotate sensor in all directions")
    offset, scale = sensor_instance.ak8963.calibrate(count, delay)
    print("Hard-iron offset (uT): X=%.2f Y=%.2f Z=%.2f" % offset)
    print("Soft-iron scale: X=%.4f Y=%.4f Z=%.4f" % scale)
    return offset, scale


def print_nine_axis(sensor_instance, interval_ms=PRINT_INTERVAL_MS):
    global last_print_time

    if not hasattr(sensor_instance, "acceleration"):
        raise ValueError("sensor_instance must be an MPU9250 instance")
    if not isinstance(interval_ms, int) or interval_ms <= 0:
        raise ValueError("interval_ms must be a positive int")

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_print_time) < interval_ms:
        return

    ax, ay, az = sensor_instance.acceleration
    gx, gy, gz = sensor_instance.gyro
    mx, my, mz = sensor_instance.magnetic
    temp = sensor_instance.temperature

    print("=" * 62)
    print("Accel  (m/s^2): X=%+8.2f  Y=%+8.2f  Z=%+8.2f" % (ax, ay, az))
    print("Gyro   (rad/s): X=%+8.3f  Y=%+8.3f  Z=%+8.3f" % (gx, gy, gz))
    print("Magnet (uT):    X=%+8.1f  Y=%+8.1f  Z=%+8.1f" % (mx, my, mz))
    print("Temperature (C): %.1f" % temp)
    last_print_time = current_time


# ========================================  主程序 ============================================

try:
    while True:
        try:
            print_nine_axis(sensor, PRINT_INTERVAL_MS)
        except OSError as error:
            print("I2C data read failed: %s" % error)
        except RuntimeError as error:
            print("Sensor data read failed: %s" % error)
        time.sleep_ms(100)
except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    print("Cleaning up resources...")
    if sensor is not None:
        sensor.deinit()
    print("Program exited")
