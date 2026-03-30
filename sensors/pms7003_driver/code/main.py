# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/1/10 下午3:00
# @Author  : hogeiha
# @File    : main.py
# @Description : PMS7003空气质量传感器数据读取与AQI计算程序

# ======================================== 导入相关模块 =========================================

# 导入AQI计算模块
from aqi import AQI
# 导入PMS7003传感器驱动模块
from pms7003 import Pms7003
# 导入机器模块的UART和Pin类
from machine import UART,Pin
# 导入时间模块
import time

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

def demo_active_mode():
    """
    演示传感器主动模式数据读取
    Args:无

    Raises:
        UartError: UART通信异常
        Exception: 其他读取异常

    Notes:主动模式下传感器持续输出数据，无需唤醒操作

    ==========================================
    Demo sensor data reading in active mode
    Args:None

    Raises:
        UartError: UART communication error
        Exception: Other reading errors

    Notes:Sensor continuously outputs data in active mode, no wake-up required
    """
    print("=== Active Mode: Start reading PMS7003 data ===")
    
    # 初始化UART0，波特率9600，TX引脚16，RX引脚17
    uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
    # 初始化PMS7003传感器对象
    sensor = Pms7003(uart=uart0)
    # 等待传感器稳定
    time.sleep(30)

    while True:
        try:
            # 读取传感器数据
            data = sensor.read()
            # 提取PM2.5浓度数据
            pm25 = data['PM2_5_ATM']
            # 提取PM10浓度数据
            pm10 = data['PM10_0_ATM']
            # 计算空气质量指数AQI
            aqi_value = AQI.aqi(pm25, pm10)

            # 打印数据分隔线
            print("-" * 50)
            # 打印PM2.5浓度值
            print(f"PM2.5: {pm25} μg/m³")
            # 打印PM10浓度值
            print(f"PM10 : {pm10} μg/m³")
            # 打印计算得到的AQI值
            print(f"AQI  : {aqi_value:.1f}")
            # 打印数据分隔线
            print("-" * 50)

        except UartError as e:
            print(f"UART error: {e}")
        except Exception as e:
            print(f"Read failed: {e}")
        
        # 2秒后进行下一次读取
        time.sleep(2)

def demo_passive_mode():
    """
    演示传感器被动模式数据读取
    Args:无

    Raises:
        UartError: UART通信异常
        Exception: 其他读取异常

    Notes:被动模式下传感器需要唤醒才能输出数据，读取完成后可进入睡眠模式降低功耗

    ==========================================
    Demo sensor data reading in passive mode
    Args:None

    Raises:
        UartError: UART communication error
        Exception: Other reading errors

    Notes:Sensor needs to be woken up to output data in passive mode, can enter sleep mode after reading to reduce power consumption
    """
    print("=== Passive Mode: Start reading PMS7003 data ===")
    
    # 初始化UART0，波特率9600，TX引脚16，RX引脚17
    uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
    # 初始化被动模式PMS7003传感器对象
    sensor = PassivePms7003(uart=uart0)
    # 等待传感器初始化
    time.sleep(2)

    while True:
        try:
            # 打印唤醒提示
            print("Waking up sensor...")
            # 唤醒传感器
            sensor.wakeup()
            # 等待传感器响应
            time.sleep(2)

            # 读取传感器数据
            data = sensor.read()
            # 提取PM2.5浓度数据
            pm25 = data['PM2_5_ATM']
            # 提取PM10浓度数据
            pm10 = data['PM10_0_ATM']
            # 计算空气质量指数AQI
            aqi_value = AQI.aqi(pm25, pm10)

            # 打印数据分隔线
            print("-" * 50)
            # 打印PM2.5浓度值
            print(f"PM2.5: {pm25} μg/m³")
            # 打印PM10浓度值
            print(f"PM10 : {pm10} μg/m³")
            # 打印计算得到的AQI值
            print(f"AQI  : {aqi_value:.1f}")
            # 打印数据分隔线
            print("-" * 50)

            # 打印睡眠提示
            print("Putting sensor to sleep...")
            # 让传感器进入睡眠模式
            sensor.sleep()

        except UartError as e:
            print(f"UART error: {e}")
        except Exception as e:
            print(f"Read failed: {e}")
        
        # 10秒后进行下一次读取
        time.sleep(10)

# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统启动稳定
time.sleep(3)
print("FreakStudio: PMS7003 sensor system initialized")

# ========================================  主程序  ============================================

# 主程序入口
if __name__ == "__main__":
    # 执行主动模式演示函数
    demo_active_mode()