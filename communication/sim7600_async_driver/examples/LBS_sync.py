# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : alankrantas
# @File    : main.py
# @Description : SIM7600模块全流程指令测试，包含SIM卡、信号、网络、基站定位、固件版本查询

# ======================================== 导入相关模块 =========================================

# 导入SIM7600核心类
from sim7600 import SIM7600

# 从sim7600模块导入lbs功能类
from sim7600 import LBS

# 从machine模块导入UART和Pin类，用于硬件引脚和串口配置
from machine import UART, Pin

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 配置UART0串口，波特率115200，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
# 实例化SIM7600核心类，传入配置好的UART对象
sim7600 = SIM7600(uart)
# 实例化lbs功能类，传入SIM7600核心实例
lbs = LBS(sim7600)
# 延时3秒，确保SIM7600模块完成初始化
time.sleep(3)
# 打印模块初始化完成并开始指令流程的提示信息
print("FreakStudio: SIM7600 module initialized, starting command flow")

# ========================================  主程序  ============================================

# 打印SIM7600指令流程开始提示
print("=== Starting SIM7600 Command Flow ===")

# 1. 检查SIM卡是否插入 (AT+CPIN?)
print("\n[1] Checking SIM card status...")
resp_cpin = sim7600.check_sim_card()
print("Response:", resp_cpin)


# 2. 检查信号质量 (AT+CSQ)
print("\n[2] Checking signal quality...")
resp_csq = sim7600.get_signal_quality()
print("Response:", resp_csq)


# 3. 检查网络注册状态 (AT+CEREG?)
print("\n[3] Checking network registration status...")
resp_cereg = sim7600.check_network_registration()
print("Response:", resp_cereg)


# 4. 检查网络附着状态 (AT+CGATT?)
print("\n[4] Checking network attach status...")
resp_cgatt = sim7600.check_network_attach()
print("Response:", resp_cgatt)


# 5. 打开网络 (AT+CNETSTART)
print("\n[5] Starting network bearer...")
resp_netstart = lbs.start_network()
print("Response:", resp_netstart)

# 6. 获取经纬度 (AT+CLBS=1)
print("\n[6] Getting LBS positioning latitude and longitude...")
resp_clbs1 = lbs.get_lbs_coords(1)
print("Response:", resp_clbs1)


# 7. 获取经纬度和日期时间 (AT+CLBS=4)
print("\n[7] Getting latitude, longitude + date and time...")
resp_clbs4 = lbs.get_lbs_full(4)
print("Response:", resp_clbs4)


# 8. 关闭网络 (AT+CNETSTOP)
print("\n[8] Stopping network bearer...")
resp_netstop = lbs.stop_network()
print("Response:", resp_netstop)


# 9. 查询固件版本 (AT+CGMR)
print("\n[9] Querying firmware version...")
resp_cgmr = sim7600.send_command("AT+CGMR")
print("Response:", resp_cgmr)

# 打印指令流程执行完成提示
print("\n=== Command flow execution completed ===")
