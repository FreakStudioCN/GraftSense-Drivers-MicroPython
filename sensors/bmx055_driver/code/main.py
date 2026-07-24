# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Sebastian Plamauer
# @File    : main.py
# @Description : RP2040 test entry for Bosch BMX055 9-axis IMU
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin

from attitude import angles, heading
from bmx055 import BMX055

# ======================================== 全局变量 ============================================
I2C_ID = 0
SCL_PIN = 5
SDA_PIN = 4
I2C_FREQ = 100000
READ_INTERVAL_MS = 1000

ACCEL_ADDR = 0x18
GYRO_ADDR = 0x68
MAG_ADDR = 0x10
ACCEL_ADDR_CANDIDATES = (0x18, 0x19)
GYRO_ADDR_CANDIDATES = (0x68, 0x69)
MAG_ADDR_CANDIDATES = (0x10, 0x11, 0x12, 0x13)

ACCEL_CHIP_ID_REG = 0x00
GYRO_CHIP_ID_REG = 0x00
MAG_CHIP_ID_REG = 0x40
ACCEL_CHIP_ID = 0xFA
GYRO_CHIP_ID = 0x0F
MAG_CHIP_ID = 0x32

bmx = None


# ======================================== 功能函数 ============================================
def print_scan_result(addresses: list) -> None:
    if addresses is None:
        raise ValueError("addresses must not be None")
    print("I2C devices found: %s" % ["0x%02X" % addr for addr in addresses])
    for expected, name in (
        (ACCEL_ADDR_CANDIDATES, "BMA2X2 accelerometer"),
        (GYRO_ADDR_CANDIDATES, "BMG160 gyroscope"),
        (MAG_ADDR_CANDIDATES, "BMM050 magnetometer"),
    ):
        try:
            print("%s found at 0x%02X" % (name, find_address(addresses, expected, name)))
        except RuntimeError:
            print("WARNING: %s not found" % name)


def find_address(addresses: list, candidates: tuple, name: str) -> int:
    if addresses is None or candidates is None or name is None:
        raise ValueError("addresses, candidates and name must not be None")
    for candidate in candidates:
        if candidate in addresses:
            return candidate
    raise RuntimeError("%s address not found" % name)


def verify_chip_id(bus: I2C, addr: int, reg: int, expected: int, name: str) -> None:
    if bus is None:
        raise ValueError("bus must not be None")
    if getattr(bus, "readfrom_mem")(addr, reg, 1)[0] != expected:
        raise RuntimeError("%s chip ID mismatch: expected 0x%02X" % (name, expected))
    print("%s chip ID verified: 0x%02X" % (name, expected))


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: Using Bosch BMX055 9-axis IMU on RP2040 ...")

try:
    scl = Pin(SCL_PIN)
    sda = Pin(SDA_PIN)
    i2c = I2C(I2C_ID, scl=scl, sda=sda, freq=I2C_FREQ)

    scanned_addresses = i2c.scan()
    if not scanned_addresses:
        raise RuntimeError("No I2C device found on bus")
    print_scan_result(scanned_addresses)

    accel_addr = find_address(scanned_addresses, ACCEL_ADDR_CANDIDATES, "BMA2X2")
    gyro_addr = find_address(scanned_addresses, GYRO_ADDR_CANDIDATES, "BMG160")
    mag_addr = find_address(scanned_addresses, MAG_ADDR_CANDIDATES, "BMM050")

    verify_chip_id(i2c, accel_addr, ACCEL_CHIP_ID_REG, ACCEL_CHIP_ID, "BMA2X2")
    verify_chip_id(i2c, gyro_addr, GYRO_CHIP_ID_REG, GYRO_CHIP_ID, "BMG160")
    i2c.writeto_mem(mag_addr, 0x4B, b"\x01")
    time.sleep_ms(3)
    verify_chip_id(i2c, mag_addr, MAG_CHIP_ID_REG, MAG_CHIP_ID, "BMM050")

    bmx = BMX055(i2c, accel_addr=accel_addr, gyro_addr=gyro_addr, mag_addr=mag_addr)
    print("BMX055 initialized successfully")
except OSError as exc:
    print("Hardware initialization error: %s" % exc)
    raise
except Exception as exc:
    print("Initialization error: %s" % exc)
    raise

last_read_time = time.ticks_ms()

# ========================================  主程序  ============================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_read_time) >= READ_INTERVAL_MS:
            accel_data = bmx.accel.xyz()
            gyro_data = bmx.gyro.xyz()
            mag_data = bmx.mag.xyz()
            roll, pitch = angles(accel_data)
            yaw = heading(mag_data)

            print("Accel(g):  X=%7.3f  Y=%7.3f  Z=%7.3f" % accel_data)
            print("Gyro(d/s): X=%7.2f  Y=%7.2f  Z=%7.2f" % gyro_data)
            print("Mag(uT):   X=%7.2f  Y=%7.2f  Z=%7.2f" % mag_data)
            print("Attitude(deg): Roll=%6.2f  Pitch=%6.2f  Heading=%6.2f" % (roll, pitch, yaw))
            print("---")
            last_read_time = current_time
        time.sleep_ms(10)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as exc:
    print("Hardware communication error: %s" % exc)
    raise
except Exception as exc:
    print("Runtime error: %s" % exc)
    raise
finally:
    if bmx is not None:
        bmx.deinit()
    print("Program exited")
