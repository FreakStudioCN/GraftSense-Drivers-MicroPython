# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午5:20
# @Author  : alankrantas
# @File    : main.py
# @Description : SIM800模块基础信息查询示例，优化打印格式提取关键信息

# ======================================== 导入相关模块 =========================================

# 导入SIM800短信扩展类
from sim800 import SIM800SMS

# 从machine模块导入UART和Pin类，用于硬件引脚和串口配置
from machine import UART, Pin

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def parse_phone_number(response: bytes) -> str:
    """
    解析手机号响应数据，提取关键手机号信息
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        解析失败时返回友好的未知提示，避免程序崩溃

    ==========================================
    Parse phone number response data to extract key phone number information
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        Return a friendly unknown prompt when parsing fails to avoid program crash
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("\r\n", "")
        # 提取手机号部分
        phone_part = resp_str.split("+CNUM:")[1].split(",")[1].replace('"', "")
        return f"SIM Card Phone Number: {phone_part if phone_part else 'Not configured'}"
    except (IndexError, ValueError):
        return "SIM Card Phone Number: Unknown"


def parse_manufacturer(response: bytes) -> str:
    """
    解析制造商响应数据，提取模块制造商信息
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        解析失败时返回友好的未知提示，避免程序崩溃

    ==========================================
    Parse manufacturer response data to extract module manufacturer information
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        Return a friendly unknown prompt when parsing fails to avoid program crash
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("\r\n", "")
        # 提取制造商名称部分
        manufacturer = resp_str.split("OK")[0].strip()
        return f"Module Manufacturer: {manufacturer if manufacturer else 'Unknown'}"
    except (IndexError, ValueError):
        return "Module Manufacturer: Unknown"


def parse_signal_quality(response: bytes) -> str:
    """
    解析信号质量响应数据，提取信号强度和误码率
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        RSSI范围0-31（数值越大信号越好），99表示无信号；BER范围0-7（数值越小误码率越低），99表示未知

    ==========================================
    Parse signal quality response data to extract signal strength and bit error rate
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        RSSI range 0-31 (higher value = better signal), 99 means no signal; BER range 0-7 (lower value = lower bit error rate), 99 means unknown
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("\r\n", "")
        # 提取信号质量数值部分
        csq_part = resp_str.split("+CSQ:")[1].split("OK")[0].strip()
        # 拆分信号强度和误码率
        rssi, ber = csq_part.split(",")
        # 生成信号强度描述文本
        rssi_desc = "No signal" if rssi == "99" else f"{rssi} (0-31, higher value = better signal)"
        # 生成误码率描述文本
        ber_desc = "Unknown" if ber == "99" else f"{ber} (0-7, lower value = lower bit error rate)"
        return f"Signal Quality - RSSI: {rssi_desc}, BER: {ber_desc}"
    except (IndexError, ValueError):
        return "Signal Quality: Unknown"


def parse_serial_number(response: bytes) -> str:
    """
    解析序列号响应数据，提取模块IMEI号
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        解析失败时返回友好的未知提示，避免程序崩溃

    ==========================================
    Parse serial number response data to extract module IMEI number
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        Return a friendly unknown prompt when parsing fails to avoid program crash
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("\r\n", "")
        # 提取IMEI号部分
        imei = resp_str.split("OK")[0].strip()
        return f"Module IMEI Number: {imei if imei else 'Unknown'}"
    except (IndexError, ValueError):
        return "Module IMEI Number: Unknown"


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保SIM800模块完成初始化
time.sleep(3)
# 打印模块初始化完成提示信息
print("FreakStudio: SIM800 module initialized successfully")
# 配置UART0串口，波特率9600，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 实例化SIM800SMS类，传入配置好的UART对象
sim800 = SIM800SMS(uart=uart)

# ========================================  主程序  ============================================

# 获取手机号响应数据并解析打印
phone_resp = sim800.get_phone_number()
print(parse_phone_number(phone_resp))

# 获取制造商响应数据并解析打印
manufacturer_resp = sim800.get_manufacturer()
print(parse_manufacturer(manufacturer_resp))

# 获取信号质量响应数据并解析打印
signal_resp = sim800.get_signal_quality()
print(parse_signal_quality(signal_resp))

# 获取序列号响应数据并解析打印
serial_resp = sim800.get_serial_number()
print(parse_serial_number(serial_resp))
