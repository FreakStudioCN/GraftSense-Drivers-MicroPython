# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/15 上午10:32
# @Author  : hogeiha
# @File    : main_mpu6050_gyro_kalman.py
# @Description : MPU6050陀螺仪和卡尔曼滤波角度对比

# ======================================== 导入相关模块 ========================================

from machine import UART, Pin, SoftI2C
import time
import gc
from mpu6050 import MPU6050, ComplementaryKalmanFilter
from math import degrees

# ======================================== 全局变量 ============================================

# 程序起始时间点变量
start_time = 0
# mpu默认地址
MPU6050_ADDRESS = 0x68

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
print("MPU6050 Gyroscope and Kalman Filter Angle Comparison Program")

# 创建串口对象，设置波特率为115200
uart = UART(1, 115200)
# 初始化uart对象，数据位为8，无校验位，停止位为1
# 设置串口超时时间为5ms
uart.init(bits=8,
          parity=None,
          stop=1,
          tx=8,
          rx=9,
          timeout=5)

# 设置GPIO 25为LED输出引脚
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# 初始化I2C接口
i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        print("I2C hexadecimal address: ", hex(device))
        if device == 0x68 or device == 0x69:
            MPU6050_ADDRESS = device
mpu = MPU6050(i2c = i2c, addr= MPU6050_ADDRESS)

print("MPU6050 initialized successfully")

# 创建互补卡尔曼滤波器
filter = ComplementaryKalmanFilter(dt=0.01, gyro_weight=0.98)
print("Kalman filter initialized successfully")

# 陀螺仪积分角度（仅用于对比）
gyro_roll_deg = 0.0
gyro_pitch_deg = 0.0

# 上次更新时间
last_update_time = time.ticks_ms()

while True:
    LED.on()
    time.sleep(0.5)
    LED.off()
    time.sleep(0.5)

# ========================================  主程序  ============================================

    try:
        # 打印表头
        print("\n" + "=" * 90)
        print("Time (s) | Gyroscope_Roll | Kalman_Roll | Gyroscope_Pitch | Kalman_Pitch | Temperature (°C)")
        print("-" * 90)

        # 开始时间记录
        start_time = time.ticks_ms()

        while True:
            # 点亮LED灯
            LED.on()

            try:
                # 读取加速度计数据
                accel_data = mpu.read_accel_data(g=False)

                # 读取陀螺仪数据
                gyro_data = mpu.read_gyro_data()

                # 读取温度数据
                temperature = mpu.read_temperature()

                # 计算时间间隔
                current_time = time.ticks_ms()
                dt = time.ticks_diff(current_time, last_update_time) / 1000.0
                last_update_time = current_time

                # 计算运行时间
                elapsed_time = time.ticks_diff(current_time, start_time) / 1000.0

                # 更新陀螺仪积分角度（仅使用陀螺仪）
                if dt > 0 and dt < 0.1:  # 防止时间间隔异常
                    gyro_roll_deg += gyro_data['y'] * dt  # Roll对应陀螺仪Y轴
                    gyro_pitch_deg += gyro_data['x'] * dt  # Pitch对应陀螺仪X轴

                # 使用卡尔曼滤波器更新角度估计（加速度计+陀螺仪融合）
                kalman_roll_rad, kalman_pitch_rad = filter.update_roll_pitch(accel_data, gyro_data)
                kalman_roll_deg = degrees(kalman_roll_rad)
                kalman_pitch_deg = degrees(kalman_pitch_rad)

                # 提取角速度和加速度原始数据
                gyro_x = gyro_data['x']
                gyro_y = gyro_data['y']
                gyro_z = gyro_data['z']

                accel_x = accel_data['x']
                accel_y = accel_data['y']
                accel_z = accel_data['z']

                # 打印完整数据（包含角速度和加速度）
                print("%7.2f | %10.2f° | %10.2f° | %11.2f° | %11.2f° | %6.1f°C | %5.1f/%5.1f/%5.1f | %4.2f/%4.2f/%4.2f" % (
                    elapsed_time,
                    gyro_roll_deg,
                    kalman_roll_deg,
                    gyro_pitch_deg,
                    kalman_pitch_deg,
                    temperature,
                    gyro_x, gyro_y, gyro_z,
                    accel_x, accel_y, accel_z
                ))

                # 准备发送给上位机的数据
                # 串口发送格式：角度数据 - 陀螺仪_Roll,卡尔曼_Roll,陀螺仪_Pitch,卡尔曼_Pitch
                angle_data = "{:.2f}, {:.2f}, {:.2f}, {:.2f}\r\n".format(
                    gyro_roll_deg,
                    kalman_roll_deg,
                    gyro_pitch_deg,
                    kalman_pitch_deg,
                )

                # 通过串口发送数据到上位机（可以根据需要选择发送哪一种格式）
                # 发送角度数据
                uart.write(angle_data)

                # 如果需要发送原始数据，可以取消下面这行的注释
                # uart.write("RAW," + raw_data)

                # 熄灭LED灯
                LED.off()

                # 延时控制采样率
                time.sleep_ms(50)  # 20Hz采样率

                # 每50次采样重置陀螺仪积分角度（避免漂移累积）
                # 20Hz采样率
                static_sample_count = int(elapsed_time * 20)
                # 检测设备是否静止（加速度模值接近9.8）
                if static_sample_count % 50 == 0 and static_sample_count > 0:
                    accel_magnitude = (accel_x ** 2 + accel_y ** 2 + accel_z ** 2) ** 0.5
                    # 设备相对静止
                    if 9.0 < accel_magnitude < 10.5:
                        # 使用卡尔曼滤波角度重置陀螺仪积分
                        gyro_roll_deg = kalman_roll_deg
                        gyro_pitch_deg = kalman_pitch_deg
                        if static_sample_count % 100 == 0:
                            print("\n[Device Stationary] Resetting gyroscope integrated angle...")
                            print(f"[Current Acceleration Magnitude]: {accel_magnitude:.2f} g]")

                # 垃圾回收
                if gc.mem_free() < 80000:
                    gc.collect()
                    print("[GC] Memory cleanup, available memory: {} bytes".format(gc.mem_free()))

            except Exception as e:
                print("Error reading data:", e)
                LED.off()
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nThe program was interrupted by the user")
    finally:
        LED.off()
        print("Program exited")

