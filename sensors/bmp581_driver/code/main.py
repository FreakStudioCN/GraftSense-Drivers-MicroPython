# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/23 下午2:00
# @Author  : octaprog7
# @File    : main.py
# @Description : BMP581温压传感器数据采集，支持I2C总线扫描、传感器初始化、温度单独测量、温压同时测量及按需测量模式

# ======================================== 导入相关模块 =========================================

# 导入软I2C和引脚控制模块
from machine import SoftI2C, Pin
# 导入BMP581传感器驱动模块
import bmp581mod
# 导入时间控制模块
import time
# 导入I2C适配器模块
from sensor_pack.bus_service import I2cAdapter

# ======================================== 全局变量 ============================================

# Raspberry Pi Pico的I2C SCL引脚编号
I2C_SCL_PIN = 3
# Raspberry Pi Pico的I2C SDA引脚编号
I2C_SDA_PIN = 2
# I2C总线通信频率
I2C_FREQ = 400_000
# BMP581传感器默认I2C地址（硬件配置可改为0x47）
TARGET_SENSOR_ADDR = 0x46
# 输出分隔符，由32个短横线组成
txt_break = 32 * "-"

# ======================================== 功能函数 ============================================

def get_wait_time_ms(output_data_rate: int) -> int:
    """
    根据输出数据率计算数据输出周期（毫秒）
    Args:输出数据率，单位为Hz，范围1-400
    Raises:ValueError - 当输出数据率小于1或大于400时抛出
    Notes:无
    
    ==========================================
    Calculate data output period (ms) based on output data rate
    Args:output_data_rate: int, unit is Hz, range 1-400
    Raises:ValueError - Raised when output data rate is less than 1 or greater than 400
    Notes:None
    """
    if output_data_rate < 1 or output_data_rate > 400:
        raise ValueError(f"Invalid output data rate!")
    return 1 + int(1000 / output_data_rate)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动延迟3秒，确保硬件稳定
time.sleep(3)
# 打印程序启动标识及功能说明
print("FreakStudio: BMP581 sensor data collection")

# 按指定风格初始化软I2C总线
i2c_bus = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描I2C总线上的所有设备
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描开始标识
print("START I2C SCANNER")

# 检查I2C扫描结果是否为空
if len(devices_list) == 0:
    # 打印无I2C设备提示
    print("No i2c device !")
    # 抛出异常并退出程序
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印找到的I2C设备数量
    print("i2c devices found:", len(devices_list))

# 初始化传感器变量为None
ps = None
# 遍历扫描到的I2C设备地址
for device in devices_list:
    # 判断当前地址是否为目标传感器地址
    if device == TARGET_SENSOR_ADDR:
        # 打印找到的目标传感器I2C十六进制地址
        print("I2c hexadecimal address:", hex(device))
        try:
            # 创建I2C适配器实例，适配传感器驱动
            adaptor = I2cAdapter(i2c_bus)
            # 初始化BMP581传感器
            ps = bmp581mod.Bmp581(adaptor)
            # 打印传感器初始化成功提示
            print("Target sensor (BMP581) initialization successful")
            # 找到目标传感器后退出循环
            break
        except Exception as e:
            # 打印传感器初始化失败信息
            print(f"Sensor Initialization failed: {e}")
            # 继续遍历下一个地址
            continue
else:
    # 未找到目标传感器时抛出异常
    raise Exception(f"No BMP581 found (target address: {hex(TARGET_SENSOR_ADDR)})")


# ========================================  主程序  ============================================

# 执行传感器软件复位
ps.soft_reset()
# 软件复位后延迟2毫秒（复位最大耗时2毫秒）
time.sleep_ms(2)

# 初始化传感器硬件配置
ps.init_hardware()

# 获取传感器芯片ID和版本ID
res = ps.get_id()
# 打印芯片ID和版本ID（十六进制格式）
print(f"chip id: 0x{res[0]:x}\trevision id: 0x{res[1]:x}")

# 获取传感器状态寄存器（类型2）的状态信息
status = ps.get_status(2)
# 解析状态寄存器数据
status_core_rdy, status_nvm_rdy, status_nvm_err, status_nvm_cmd_err, status_boot_err_corrected = status
# 打印状态寄存器解析结果
print(f"Status register: core_rdy: {status_core_rdy}, nvm_rdy: {status_nvm_rdy}, nvm_error: {status_nvm_err}, nvm_cmd_error: {status_nvm_cmd_err}")

# 获取传感器中断状态寄存器（类型1）的状态信息
status = ps.get_status(1)
# 解析中断状态寄存器数据
drdy_data_reg, fifo_full, fifo_ths, oor_p, por = status
# 打印中断状态寄存器解析结果
print(f"ISR Status: data_rdy: {drdy_data_reg}, FIFO full: {fifo_full}, FIFO Threshold: {fifo_ths}, Pressure data out of range: {oor_p}, POR or software reset complete: {por}")

# 判断传感器核心状态是否正常
status_ok = status_nvm_rdy and not status_nvm_err and por
if status_ok:
    # 打印传感器状态正常提示
    print("Sensor status is normal!")
else:
    # 打印传感器状态异常提示
    print("Sensor status is abnormal. Possible malfunction!")

# 打印分隔符
print(txt_break)
# 打印传感器当前配置读取提示
print("Current settings read from the sensor.")

# 获取传感器过采样配置
_oversampling = ps.oversampling
# 获取传感器电源模式
_pwr_mode = ps.power_mode
# 获取传感器输出数据率
_output_data_rate = ps.output_data_rate
# 获取传感器IIR滤波器配置
iir_conf = ps.iir_config

# 打印电源模式和输出数据率
print(f"power mode: {_pwr_mode}; output data rate: {_output_data_rate}")
# 打印压力和温度过采样配置
print(f"pressure oversampling: {_oversampling[0]}; temperature oversampling: {_oversampling[1]}")
# 打印压力和温度IIR滤波器配置
print(f"pressure iir: {iir_conf[0]}; temperature iir: {iir_conf[1]}")
# 打印分隔符
print(txt_break)

# 获取传感器有效过采样等级
osr_r = ps.effective_osr_rating
# 打印有效过采样等级及ODR配置验证结果
print(f"Effective OSR T: {osr_r[0]}; Effective OSR P: {osr_r[1]}; ODR setting is correct: {osr_r[2]}")

# 打印分隔符
print(txt_break)
# 打印仅温度测量模式提示
print("Measuring temperature only!")
# 设置传感器为仅温度测量模式
ps.temperature_only = True
# 设置温度过采样系数为2
ps.temp_oversampling = 2
# 设置压力过采样系数为2
ps.pressure_oversampling = 2
# 设置输出数据率为10Hz
odr = 10
# 计算数据输出等待时间（毫秒）
wt_ms = get_wait_time_ms(odr)
# 打印数据输出周期
print(f"Data output period [ms]: {wt_ms}")
# 启动传感器测量（模式1：连续测量）
tmp = ps.start_measurement(mode=1, output_data_rate=odr)
if tmp:
    # 打印数据率匹配提示
    print("Sensor data update rate matches temperature and pressure oversampling values!")

# 循环100次读取温度数据
for _ in range(100):
    # 等待数据输出周期
    time.sleep_ms(wt_ms)
    # 检查数据是否准备就绪
    if ps.is_data_ready():
        # 获取温度数据
        temperature = ps.get_temperature()
        # 打印温度数据（摄氏度）
        print(f"Temperature [°C]: {temperature}")
    else:
        # 打印无数据可读提示
        print(f"No data to read!")

# 打印分隔符
print(txt_break)
# 打印温压同时测量模式提示
print("Measuring temperature and pressure!")
# 关闭仅温度测量模式，启用温压同时测量
ps.temperature_only = False
# 设置输出数据率为20Hz
odr = 20
# 计算数据输出等待时间（毫秒）
wt_ms = get_wait_time_ms(odr)
# 启动传感器测量（模式1：连续测量）
tmp = ps.start_measurement(mode=1, output_data_rate=odr)
# 循环200次读取温压数据
for _ in range(200):
    # 等待数据输出周期
    time.sleep_ms(wt_ms)
    # 检查数据是否准备就绪
    if ps.is_data_ready():
        # 获取温度和压力数据
        temperature, pressure = ps.get_temperature(), ps.get_pressure()
        # 打印温度（摄氏度）和压力（帕斯卡）数据
        print(f"Temperature [°C]: {temperature}; Pressure [Pa]: {pressure}")
    else:
        # 打印无数据可读提示
        print(f"No data to read!")

# 打印分隔符
print(txt_break)
# 设置按需测量模式下的输出数据率为5Hz
odr = 5
# 计算数据输出等待时间（毫秒）
wt_ms = get_wait_time_ms(odr)
# 打印按需测量模式提示
print("On-demand measurement mode! Temperature and pressure!")
# 打印迭代器协议使用提示
print("Applying iterator protocol.")

# 使用迭代器遍历传感器数据
for items in ps:
    if items:
        # 解析压力和温度数据
        pressure, temperature = items
        # 打印温度（摄氏度）和压力（帕斯卡）数据
        print(f"Temperature [°C]: {temperature}; Pressure [Pa]: {pressure}")
    else:
        # 打印无数据可读提示
        print(f"No data to read!")
    # 启动传感器按需测量（模式2：按需测量）
    tmp = ps.start_measurement(mode=2, output_data_rate=0)
    # 等待数据输出周期
    time.sleep_ms(wt_ms)

# 打印分隔符
print(txt_break)
