# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2017/01/09 00:00
# @Author  : Piotr Oniszczuk
# @File    : MCP39F521.py
# @Description : MCP39F521 单相电能计量芯片驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Piotr Oniszczuk"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin, reset
from time import sleep_ms
import uctypes


# ======================================== 全局变量 ============================================

bus = I2C(scl=Pin(5), sda=Pin(2), freq=100000)


# ======================================== 功能函数 ============================================

def send_raw_data(chipid, buf):
    """
    向指定芯片发送原始字节数据
    Args:
        chipid (int): 芯片编号（0~2），用于计算 I2C 地址
        buf (bytearray): 待发送的字节数据
    Returns:
        None
    Raises:
        无（内部捕获 I2C 异常并打印错误）
    Notes:
        - ISR-safe: 否
        - 芯片 I2C 地址 = 0x74 + chipid
    ==========================================
    Send raw bytes to the specified chip.
    Args:
        chipid (int): Chip index (0~2), used to calculate I2C address
        buf (bytearray): Bytes to send
    Returns:
        None
    Raises:
        None (I2C exceptions are caught internally and printed)
    Notes:
        - ISR-safe: No
        - Chip I2C address = 0x74 + chipid
    """
    # 计算目标芯片的 I2C 地址
    chip_addr = 0x74 + chipid

    try:
        # 向芯片写入原始数据
        bus.writeto(chip_addr, buf)
    except:
        print('Erorr durring write on I2C bus...')


def get_raw_data(chipid, buf):
    """
    向芯片发送命令后读取 35 字节原始响应数据
    Args:
        chipid (int): 芯片编号（0~2）
        buf (bytearray): 命令字节数据
    Returns:
        bytearray: 芯片返回的 35 字节原始数据
    Raises:
        无（内部捕获 I2C 异常并打印错误）
    Notes:
        - ISR-safe: 否
        - 发送命令后等待 10ms 再读取
    ==========================================
    Send command to chip then read 35 bytes of raw response.
    Args:
        chipid (int): Chip index (0~2)
        buf (bytearray): Command bytes
    Returns:
        bytearray: 35 bytes of raw data from chip
    Raises:
        None (I2C exceptions are caught internally and printed)
    Notes:
        - ISR-safe: No
        - Waits 10ms after sending command before reading
    """
    # 发送读取命令
    send_raw_data(chipid, buf)

    # 等待芯片处理命令
    sleep_ms(10)

    # 计算目标芯片的 I2C 地址
    chip_addr = 0x74 + chipid

    # 准备 35 字节接收缓冲区
    buf = bytearray(b'\x00' * 35)
    try:
        # 从芯片读取 35 字节数据
        bus.readfrom_into(chip_addr, buf)
    except:
        print('Erorr durring read on I2C bus...')

    return buf


def control_energy_acc(chipid, state):
    """
    控制指定芯片的电能累积功能开关
    Args:
        chipid (int): 芯片编号（0~2）
        state (bool): True 开启电能累积，False 关闭并清零
    Returns:
        None
    Raises:
        无
    Notes:
        - ISR-safe: 否
        - 写入寄存器地址 0x00DC，数据手册第 29 页
    ==========================================
    Enable or disable energy accumulation on the specified chip.
    Args:
        chipid (int): Chip index (0~2)
        state (bool): True to enable, False to disable and reset counters
    Returns:
        None
    Raises:
        None
    Notes:
        - ISR-safe: No
        - Writes to register 0x00DC, datasheet page 29
    """
    if state:
        # 写入 0x01 到 0x00DC 寄存器，开启电能累积
        buf = bytearray([0xA5, 0x0A, 0x41, 0x00, 0xDC, 0x4D, 0x02, 0x00, 0x01, 0x1C])
    else:
        # 写入 0x00 到 0x00DC 寄存器，关闭电能累积
        buf = bytearray([0xA5, 0x0A, 0x41, 0x00, 0xDC, 0x4D, 0x02, 0x00, 0x00, 0x1B])

    send_raw_data(chipid, buf)


def get_data(chipid):
    """
    读取指定芯片的完整电气测量数据
    Args:
        chipid (int): 芯片编号（0~2）
    Returns:
        list: 包含 13 个测量值的列表，顺序为：
              [SysVer, SysStatus, Voltage, Current, Frequency,
               ActivePwr, ReactvPwr, ApprntPwr, PwrFactor,
               ImportActEnergy, ExportActEnergy,
               ImportReactEnergy, ExportReactEnergy]
    Raises:
        无
    Notes:
        - ISR-safe: 否
        - 电压单位 V，电流单位 A，频率单位 Hz，功率单位 W，电能单位 kWh
        - 分两次读取：第一次从 0x0002 读 32 字节（实时量），第二次从 0x001E 读 32 字节（累积量）
    ==========================================
    Read complete electrical measurement data from the specified chip.
    Args:
        chipid (int): Chip index (0~2)
    Returns:
        list: 13 measurement values in order:
              [SysVer, SysStatus, Voltage, Current, Frequency,
               ActivePwr, ReactvPwr, ApprntPwr, PwrFactor,
               ImportActEnergy, ExportActEnergy,
               ImportReactEnergy, ExportReactEnergy]
    Raises:
        None
    Notes:
        - ISR-safe: No
        - Units: V, A, Hz, W, kWh
        - Two reads: first from 0x0002 (real-time), second from 0x001E (accumulated)
    """
    # 构造读取实时数据命令：从 0x0002 地址读 32 字节
    buf = bytearray([0xA5, 0x08, 0x41, 0x00, 0x02, 0x4E, 0x20, 0x5E])

    # 发送命令并获取原始响应
    buf = get_raw_data(chipid, buf)

    # 定义实时数据寄存器结构（小端序）
    desc = {
        "SysStatus": uctypes.UINT16 | 2,
        "SysVer":    uctypes.UINT16 | 4,
        "Voltage":   uctypes.UINT16 | 6,
        "Frequency": uctypes.UINT16 | 8,
        "PwrFactor": uctypes.INT16  | 12,
        "Current":   uctypes.UINT32 | 14,
        "ActivePwr": uctypes.UINT32 | 18,
        "ReactvPwr": uctypes.UINT32 | 22,
        "ApprntPwr": uctypes.UINT32 | 26,
    }

    # 按结构体解析原始数据
    values = uctypes.struct(uctypes.addressof(buf), desc, uctypes.LITTLE_ENDIAN)

    # 按数据手册换算各物理量
    SysVer    = values.SysVer
    SysStatus = values.SysStatus
    Voltage   = values.Voltage   / 10.0
    Current   = values.Current   / 10000.0
    Frequency = values.Frequency / 1000.0
    ActivePwr = values.ActivePwr / 100.0
    ReactvPwr = values.ReactvPwr / 100.0
    ApprntPwr = values.ApprntPwr / 100.0
    PwrFactor = values.PwrFactor * 0.000030517578125

    # 构造读取累积电能命令：从 0x001E 地址读 32 字节
    buf = bytearray([0xA5, 0x08, 0x41, 0x00, 0x1E, 0x4E, 0x20, 0x7A])

    # 发送命令并获取原始响应
    buf = get_raw_data(chipid, buf)

    # 定义累积电能寄存器结构（小端序）
    desc = {
        "ImportActEnergy":   uctypes.UINT64 | 2,
        "ExportActEnergy":   uctypes.UINT64 | 10,
        "ImportReactEnergy": uctypes.UINT64 | 18,
        "ExportReactEnergy": uctypes.UINT64 | 26,
    }

    # 按结构体解析累积电能数据
    values = uctypes.struct(uctypes.addressof(buf), desc, uctypes.LITTLE_ENDIAN)

    # 换算累积电能单位为 kWh
    ImportActEnergy   = values.ImportActEnergy   / 1000000.0
    ExportActEnergy   = values.ExportActEnergy   / 1000000.0
    ImportReactEnergy = values.ImportReactEnergy / 1000000.0
    ExportReactEnergy = values.ExportReactEnergy / 1000000.0

    return [SysVer,
            SysStatus,
            Voltage,
            Current,
            Frequency,
            ActivePwr,
            ReactvPwr,
            ApprntPwr,
            PwrFactor,
            ImportActEnergy,
            ExportActEnergy,
            ImportReactEnergy,
            ExportReactEnergy]


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
