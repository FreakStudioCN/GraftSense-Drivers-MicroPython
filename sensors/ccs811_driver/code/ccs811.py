# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午6:00
# @Author  : Ledbelly2142
# @File    : ccs811.py
# @Description : CCS811空气质量传感器驱动 读取eCO2和TVOC值 适配Raspberry Pi Pico 参考自:https://github.com/Ledbelly2142/CCS811
# @License : MIT
__version__ = "0.1.0"
__author__ = "Ledbelly2142"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C

# ======================================== 全局变量 ============================================

# CCS811传感器默认I2C地址
CCS811_ADDR = const(0x5A)

# CCS811传感器寄存器/命令常量定义
# 状态寄存器地址
CCS811_STATUS = const(0x00)
# 测量模式寄存器地址
CCS811_MEAS_MODE = const(0x01)
# 算法结果数据寄存器地址（存储eCO2和TVOC值）
CCS811_ALG_RESULT_DATA = const(0x02)
# 原始数据寄存器地址
CCS811_RAW_DATA = const(0x03)
# 环境数据寄存器地址（用于补偿温度/湿度）
CCS811_ENV_DATA = const(0x05)
# NTC温度传感器数据寄存器地址
CCS811_NTC = const(0x06)
# 阈值设置寄存器地址
CCS811_THRESHOLDS = const(0x10)
# 基线值寄存器地址
CCS811_BASELINE = const(0x11)
# 硬件ID寄存器地址
CCS811_HW_ID = const(0x20)
# 硬件版本寄存器地址
CCS811_HW_VERSION = const(0x21)
# 启动固件版本寄存器地址
CCS811_FW_BOOT_VERSION = const(0x23)
# 应用固件版本寄存器地址
CCS811_FW_APP_VERSION = const(0x24)
# 错误ID寄存器地址
CCS811_ERROR_ID = const(0xE0)
# 启动应用程序命令
CCS811_APP_START = const(0xF4)
# 软件重置命令
CCS811_SW_RESET = const(0xFF)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class CCS811(object):
    """
    CCS811空气质量传感器驱动类（修复了关键bug）
    CCS811 Air Quality Sensor Driver Class (Key bugs fixed)

    Attributes:
        i2c (I2C): 已初始化的I2C总线对象
        addr (int): CCS811传感器I2C地址，默认0x5A
        tVOC (int): 总挥发性有机化合物浓度值，单位ppb
        CO2 (int): 等效二氧化碳浓度值，单位ppm
        i2c (I2C): Initialized I2C bus object
        addr (int): CCS811 sensor I2C address, default 0x5A
        tVOC (int): Total Volatile Organic Compounds concentration value, unit ppb
        CO2 (int): Equivalent Carbon Dioxide concentration value, unit ppm

    Methods:
        print_error(): 读取并打印传感器错误码对应的错误信息
        configure_ccs811(): 配置CCS811传感器，检查硬件ID和APP有效性，设置测量模式
        setup(): 传感器初始化入口函数，执行配置并打印基线值
        get_base_line(): 读取传感器基线值
        check_for_error(): 检查传感器是否发生错误
        app_valid(): 检查传感器应用程序是否有效
        set_drive_mode(mode): 设置传感器测量模式（采样间隔）
        data_available(): 检查是否有新的测量数据可用
        read_eCO2(): 读取等效二氧化碳浓度值（ppm）
        read_tVOC(): 读取总挥发性有机化合物浓度值（ppb）
        reset(): 软件重置传感器
        print_error(): Read and print error information corresponding to sensor error code
        configure_ccs811(): Configure CCS811 sensor, check hardware ID and APP validity, set measurement mode
        setup(): Sensor initialization entry function, execute configuration and print baseline value
        get_base_line(): Read sensor baseline value
        check_for_error(): Check if sensor error occurred
        app_valid(): Check if sensor application program is valid
        set_drive_mode(mode): Set sensor measurement mode (sampling interval)
        data_available(): Check if new measurement data is available
        read_eCO2(): Read equivalent Carbon Dioxide concentration value (ppm)
        read_tVOC(): Read Total Volatile Organic Compounds concentration value (ppb)
        reset(): Software reset sensor
    """

    def __init__(self, i2c=None,addr = CCS811_ADDR):
        """
        初始化CCS811传感器驱动对象
        Initialize CCS811 sensor driver object

        Args:
            i2c (I2C): 已初始化的I2C总线对象，默认None
            i2c (I2C): Initialized I2C bus object, default None

        Returns:
            None

        Notes:
            1. 初始化时会设置传感器I2C地址，并初始化tVOC和CO2值为0
            2. 需确保传入的I2C对象已正确初始化（适配Raspberry Pi Pico硬件）
            1. Sensor I2C address is set during initialization, and tVOC/CO2 values are initialized to 0
            2. Ensure the incoming I2C object is correctly initialized (adapted for Raspberry Pi Pico hardware)
        """
        self.i2c = i2c
        self.addr = addr
        self.tVOC = 0
        self.CO2 = 0

    def print_error(self):
        """
        读取错误码并打印对应的错误信息
        Read error code and print corresponding error information

        Args:
            None

        Returns:
            None

        Notes:
            1. 错误码共6位，分别对应不同的错误类型，支持同时显示多个错误
            2. 错误类型包括：HeaterSupply、HeaterFault、MaxResistance、MeasModeInvalid、ReadRegInvalid、MsgInvalid
            1. Error code has 6 bits, corresponding to different error types, supports displaying multiple errors at the same time
            2. Error types include: HeaterSupply, HeaterFault, MaxResistance, MeasModeInvalid, ReadRegInvalid, MsgInvalid
        """
        # 读取错误ID寄存器值
        error = self.i2c.readfrom_mem(self.addr, CCS811_ERROR_ID, 1)
        message = "Error: "

        # 检查第5位：HeaterSupply错误
        if (error[0] >> 5) & 1:
            message += "HeaterSupply "
        # 检查第4位：HeaterFault错误（修复：用if而非elif，避免只显示一个错误）
        if (error[0] >> 4) & 1:
            message += "HeaterFault "
        # 检查第3位：MaxResistance错误
        if (error[0] >> 3) & 1:
            message += "MaxResistance "
        # 检查第2位：MeasModeInvalid错误
        if (error[0] >> 2) & 1:
            message += "MeasModeInvalid "
        # 检查第1位：ReadRegInvalid错误
        if (error[0] >> 1) & 1:
            message += "ReadRegInvalid "
        # 检查第0位：MsgInvalid错误
        if (error[0] >> 0) & 1:
            message += "MsgInvalid "

        print(message)

    def configure_ccs811(self):
        """
        配置CCS811传感器，执行硬件校验和模式设置
        Configure CCS811 sensor, perform hardware verification and mode setting

        Args:
            None

        Returns:
            None

        Notes:
            1. 配置流程：检查硬件ID→检查错误→检查APP有效性→启动APP→设置测量模式
            2. 任意步骤失败会抛出ValueError异常，并打印错误信息
            1. Configuration process: Check hardware ID → Check error → Check APP validity → Start APP → Set measurement mode
            2. Any step failure will throw ValueError exception and print error information
        """
        # 检查硬件ID是否正确（CCS811硬件ID应为0x81）
        hardware_id = self.i2c.readfrom_mem(self.addr, CCS811_HW_ID, 1)
        if hardware_id[0] != 0x81:
            raise ValueError("CCS811 not found. Please check wiring.")

        # 检查传感器是否有错误
        if self.check_for_error():
            self.print_error()
            raise ValueError("Error at Startup.")

        # 检查应用程序是否有效
        if not self.app_valid():
            raise ValueError("Error: App not valid")

        # 发送启动应用程序命令（修复：添加bytes包装）
        self.i2c.writeto(self.addr, bytes([CCS811_APP_START]))

        # 检查启动APP后是否有错误
        if self.check_for_error():
            self.print_error()
            raise ValueError("Error at AppStart.")

        # 设置驱动模式为1（1秒读取一次数据）
        self.set_drive_mode(1)

        # 检查设置模式后是否有错误
        if self.check_for_error():
            self.print_error()
            raise ValueError("Error at setDriveMode.")

    def setup(self):
        """
        传感器初始化入口函数，执行配置并打印基线值
        Sensor initialization entry function, execute configuration and print baseline value

        Args:
            None

        Returns:
            None

        Notes:
            1. 初始化流程：打印启动信息→执行配置→读取并打印基线值
            2. 基线值用于传感器校准，不同传感器基线值不同
            1. Initialization process: Print startup info → Execute configuration → Read and print baseline value
            2. Baseline value is used for sensor calibration, different sensors have different baseline values
        """
        print("Starting CCS811 Initialization...")
        # 执行传感器配置
        self.configure_ccs811()

        # 获取并打印基线值
        baseline = self.get_base_line()
        print(f"Baseline for this sensor: 0x{baseline:04X} ({baseline})")

    def get_base_line(self):
        """
        读取传感器基线值
        Read sensor baseline value

        Args:
            None

        Returns:
            int: 传感器基线值（16位无符号整数）
            int: Sensor baseline value (16-bit unsigned integer)

        Notes:
            1. 基线值存储在2个寄存器中，需拼接为16位整数
            2. 基线值是传感器的校准参考值，可用于恢复校准状态
            1. Baseline value is stored in 2 registers and needs to be spliced into a 16-bit integer
            2. Baseline value is the calibration reference value of the sensor, which can be used to restore calibration state
        """
        # 读取基线值的2个寄存器数据
        b = self.i2c.readfrom_mem(self.addr, CCS811_BASELINE, 2)
        # 拼接为16位整数
        baseline = (b[0] << 8) | b[1]
        return baseline

    def check_for_error(self):
        """
        检查传感器是否发生错误
        Check if sensor error occurred

        Args:
            None

        Returns:
            bool: 有错误返回True，无错误返回False
            bool: Return True if error occurred, return False if no error

        Notes:
            1. 检查状态寄存器第0位（ERROR_BIT），该位为1表示有错误
            2. 修复：简化位运算逻辑，提升代码可读性
            1. Check the 0th bit (ERROR_BIT) of the status register, 1 means error occurred
            2. Fixed: Simplify bit operation logic to improve code readability
        """
        # 读取状态寄存器值
        value = self.i2c.readfrom_mem(self.addr, CCS811_STATUS, 1)
        # 返回错误位状态
        return value[0] & 0x01

    def app_valid(self):
        """
        检查传感器应用程序是否有效
        Check if sensor application program is valid

        Args:
            None

        Returns:
            bool: APP有效返回True，无效返回False
            bool: Return True if APP is valid, return False if invalid

        Notes:
            1. 检查状态寄存器第4位（APP_VALID_BIT），该位为1表示APP有效
            2. 修复：简化位运算逻辑，提升代码可读性
            1. Check the 4th bit (APP_VALID_BIT) of the status register, 1 means APP is valid
            2. Fixed: Simplify bit operation logic to improve code readability
        """
        # 读取状态寄存器值
        value = self.i2c.readfrom_mem(self.addr, CCS811_STATUS, 1)
        # 返回APP有效性状态
        return (value[0] & 0x10) != 0

    def set_drive_mode(self, mode):
        """
        设置传感器驱动模式（采样间隔）
        Set sensor drive mode (sampling interval)

        Args:
            mode (int): 驱动模式值，可选0-4
                        0=休眠模式，1=1秒/次，2=10秒/次，3=60秒/次，4=250ms/次
            mode (int): Drive mode value, optional 0-4
                        0=Sleep mode, 1=1s per measurement, 2=10s per measurement, 3=60s per measurement, 4=250ms per measurement

        Returns:
            None

        Notes:
            1. 模式值超过4时自动设为4，避免无效配置
            2. 配置流程：清空原有模式→等待100ms→读取当前配置→更新模式位→写入新配置
            1. Mode value exceeding 4 is automatically set to 4 to avoid invalid configuration
            2. Configuration process: Clear original mode → Wait 100ms → Read current configuration → Update mode bit → Write new configuration
        """
        # 限制模式值范围为0-4
        if mode > 4:
            mode = 4

        # 清空原有模式配置
        self.i2c.writeto_mem(self.addr, CCS811_MEAS_MODE, bytes([0x00]))
        # 缩短等待时间，提升效率（等待配置生效）
        time.sleep(0.1)

        # 读取当前配置
        setting = self.i2c.readfrom_mem(self.addr, CCS811_MEAS_MODE, 1)
        # 保留低4位，更新高4位的模式值（修复：正确的位操作）
        buf = (setting[0] & 0x0F) | (mode << 4)
        # 写入新的模式配置
        self.i2c.writeto_mem(self.addr, CCS811_MEAS_MODE, bytes([buf]))

    def data_available(self):
        """
        检查是否有新的测量数据可用（修复核心bug）
        Check if new measurement data is available (fix core bug)

        Args:
            None

        Returns:
            bool: 有新数据返回True，无新数据返回False
            bool: Return True if new data is available, return False if no new data

        Notes:
            1. 检查状态寄存器第3位（DATA_READY_BIT），该位为1表示有新数据
            2. 修复了原代码中位判断错误的核心问题，确保数据读取准确性
            1. Check the 3rd bit (DATA_READY_BIT) of the status register, 1 means new data is available
            2. Fixed the core problem of bit judgment error in the original code to ensure data reading accuracy
        """
        # 读取状态寄存器值
        value = self.i2c.readfrom_mem(self.addr, CCS811_STATUS, 1)
        # 正确的位判断：BIT3表示数据可用
        return (value[0] & 0x08) != 0

    def read_eCO2(self):
        """
        读取等效二氧化碳（eCO2）浓度值
        Read equivalent Carbon Dioxide (eCO2) concentration value

        Args:
            None

        Returns:
            int/None: 有新数据返回eCO2值（单位ppm，范围400-8192）；无数据或错误返回None
            int/None: Return eCO2 value (unit ppm, range 400-8192) if new data is available; return None if no data or error

        Notes:
            1. 仅当data_available()返回True时才读取数据
            2. eCO2值存储在算法结果数据寄存器的前2个字节
            1. Read data only when data_available() returns True
            2. eCO2 value is stored in the first 2 bytes of the algorithm result data register
        """
        # 检查是否有新数据可用
        if self.data_available():
            # 读取4字节算法结果数据
            d = self.i2c.readfrom_mem(self.addr, CCS811_ALG_RESULT_DATA, 4)
            # 拼接前2字节为eCO2值
            co2 = (d[0] << 8) | d[1]
            # 更新类属性CO2值
            self.CO2 = co2
            return co2
        # 无新数据时检查是否有错误
        elif self.check_for_error():
            self.print_error()
        return None

    def read_tVOC(self):
        """
        读取总挥发性有机化合物（TVOC）浓度值
        Read Total Volatile Organic Compounds (TVOC) concentration value

        Args:
            None

        Returns:
            int/None: 有新数据返回TVOC值（单位ppb）；无数据或错误返回None
            int/None: Return TVOC value (unit ppb) if new data is available; return None if no data or error

        Notes:
            1. 仅当data_available()返回True时才读取数据
            2. TVOC值存储在算法结果数据寄存器的后2个字节
            1. Read data only when data_available() returns True
            2. TVOC value is stored in the last 2 bytes of the algorithm result data register
        """
        # 检查是否有新数据可用
        if self.data_available():
            # 读取4字节算法结果数据
            d = self.i2c.readfrom_mem(self.addr, CCS811_ALG_RESULT_DATA, 4)
            # 拼接后2字节为TVOC值
            tvoc = (d[2] << 8) | d[3]
            # 更新类属性tVOC值
            self.tVOC = tvoc
            return tvoc
        # 无新数据时检查是否有错误
        elif self.check_for_error():
            self.print_error()
        return None

    def reset(self):
        """
        软件重置CCS811传感器
        Software reset CCS811 sensor

        Args:
            None

        Returns:
            None

        Notes:
            1. 重置序列为固定字节数组[0x11, 0xE5, 0x72, 0x8A]
            2. 重置后等待500ms让传感器稳定
            1. Reset sequence is fixed byte array [0x11, 0xE5, 0x72, 0x8A]
            2. Wait 500ms after reset for sensor stabilization
        """
        # 定义软件重置序列
        seq = bytearray([0x11, 0xE5, 0x72, 0x8A])
        # 发送重置命令
        self.i2c.writeto_mem(self.addr, CCS811_SW_RESET, seq)
        # 重置后等待稳定
        time.sleep(0.5)


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
