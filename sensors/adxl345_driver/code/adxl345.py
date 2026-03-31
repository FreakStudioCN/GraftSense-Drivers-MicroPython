# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/14 下午3:00
# @Author  : fanday
# @File    : adxl345.py
# @Description : ADXL345三轴加速度传感器驱动 初始化传感器 配置参数 读取XYZ轴加速度数据 参考自:https://github.com/fanday/adxl345_micropython

__version__ = "1.0.0"
__author__ = "fanday"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入Pin模块用于硬件引脚控制
from machine import Pin

# 导入I2C模块用于I2C总线通信
from machine import I2C

# 导入时间模块用于延时操作
import time

# 导入ustruct模块用于数据解包
import ustruct

# ======================================== 全局变量 ============================================

# ADXL345数据格式配置寄存器地址
DATA_FORMAT = 0x31
# ADXL345带宽/输出速率配置寄存器地址
BW_RATE = 0x2C
# ADXL345电源控制寄存器地址
POWER_CTL = 0x2D
# ADXL345中断使能寄存器地址
INT_ENABLE = 0x2E
# X轴偏移校准寄存器地址
OFSX = 0x1E
# Y轴偏移校准寄存器地址
OFSY = 0x1F
# Z轴偏移校准寄存器地址
OFSZ = 0x20

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class adxl345:
    """
    ADXL345三轴加速度传感器驱动类

    Attributes:
        scl (int): I2C SCL引脚编号
        sda (int): I2C SDA引脚编号
        cs (Pin): 片选引脚对象
        i2c (I2C): I2C总线通信对象
        slvAddr (int): 传感器I2C从机地址

    Methods:
        __init__(bus, scl, sda, cs): 初始化传感器并配置参数
        readXYZ(): 读取XYZ三轴加速度数据
        writeByte(addr, data): 向传感器寄存器写入单个字节
        readByte(addr): 从传感器寄存器读取单个字节

    Notes:
        适配Raspberry Pi Pico硬件，支持16g量程、100Hz输出速率，I2C通信频率10000Hz

    ==========================================
    ADXL345 three-axis acceleration sensor driver class

    Attributes:
        scl (int): I2C SCL pin number
        sda (int): I2C SDA pin number
        cs (Pin): Chip select pin object
        i2c (I2C): I2C bus communication object
        slvAddr (int): Sensor I2C slave address

    Methods:
        __init__(bus, scl, sda, cs): Initialize sensor and configure parameters
        readXYZ(): Read XYZ three-axis acceleration data
        writeByte(addr, data): Write a single byte to the sensor register
        readByte(addr): Read a single byte from the sensor register

    Notes:
        Adapted for Raspberry Pi Pico hardware, supports 16g range, 100Hz output rate, I2C communication frequency 10000Hz
    """

    def __init__(self, bus: int, scl: int, sda: int, cs: Pin) -> None:
        """
        传感器初始化并配置工作参数

        Args:
            bus (int): I2C总线编号（通常为0或1）
            scl (int): I2C SCL引脚编号（有效GPIO引脚号）
            sda (int): I2C SDA引脚编号（有效GPIO引脚号）
            cs (Pin): 片选引脚对象（已配置的Pin实例）

        Raises:
            ValueError: 任何参数为None
            TypeError: 参数类型不符合要求
            OSError: I2C总线初始化失败或传感器未找到

        Notes:
            初始化流程：配置片选引脚→初始化I2C总线→扫描并匹配传感器地址→配置数据格式/输出速率/电源模式等参数

        ==========================================
        Initialize sensor and configure working parameters

        Args:
            bus (int): I2C bus number (usually 0 or 1)
            scl (int): I2C SCL pin number (valid GPIO pin number)
            sda (int): I2C SDA pin number (valid GPIO pin number)
            cs (Pin): Chip select pin object (configured Pin instance)

        Raises:
            ValueError: Any parameter is None
            TypeError: Parameter type does not meet requirements
            OSError: I2C bus initialization failed or sensor not found

        Notes:
            Initialization process: Configure chip select pin → Initialize I2C bus → Scan and match sensor address → Configure data format/output rate/power mode and other parameters
        """
        # 参数验证
        if bus is None:
            raise ValueError("bus cannot be None")
        if not isinstance(bus, int):
            raise TypeError(f"bus must be int, got {type(bus).__name__}")
        if bus not in (0, 1):
            raise ValueError(f"bus must be 0 or 1, got {bus}")
        if scl is None:
            raise ValueError("scl cannot be None")
        if not isinstance(scl, int):
            raise TypeError(f"scl must be int, got {type(scl).__name__}")
        if scl < 0:
            raise ValueError(f"scl must be a valid GPIO pin number, got {scl}")
        if sda is None:
            raise ValueError("sda cannot be None")
        if not isinstance(sda, int):
            raise TypeError(f"sda must be int, got {type(sda).__name__}")
        if sda < 0:
            raise ValueError(f"sda must be a valid GPIO pin number, got {sda}")
        if cs is None:
            raise ValueError("cs cannot be None")
        if not isinstance(cs, Pin):
            raise TypeError(f"cs must be Pin object, got {type(cs).__name__}")

        # 赋值SCL引脚编号
        self.scl = scl
        # 赋值SDA引脚编号
        self.sda = sda
        # 赋值片选引脚对象
        self.cs = cs
        # 设置片选引脚为高电平
        cs.value(1)
        # 延时1秒等待硬件稳定
        time.sleep(1)
        # 初始化I2C总线通信对象
        self.i2c = I2C(bus, scl=self.scl, sda=self.sda, freq=10000)
        # 扫描I2C总线上的从机地址
        slv = self.i2c.scan()
        # 打印扫描到的从机地址列表
        print(slv)
        # 遍历扫描到的地址匹配ADXL345传感器
        for s in slv:
            # 读取传感器设备ID寄存器（地址0）验证
            buf = self.i2c.readfrom_mem(s, 0, 1)
            # 打印读取到的设备ID
            print(buf)
            # 验证设备ID为0xe5（ADXL345默认ID）
            if buf[0] == 0xE5:
                # 记录匹配到的传感器I2C地址
                self.slvAddr = s
                # 打印传感器找到的提示
                print("adxl345 found")
                # 找到传感器后退出循环
                break
        # 低电平中断输出,13位全分辨率,输出数据右对齐,16g量程
        self.writeByte(DATA_FORMAT, 0x2B)
        # 数据输出速度为100Hz
        self.writeByte(BW_RATE, 0x0A)
        # 不使用中断
        self.writeByte(INT_ENABLE, 0x00)

        # X轴偏移校准值设为0
        self.writeByte(OFSX, 0x00)
        # Y轴偏移校准值设为0
        self.writeByte(OFSY, 0x00)
        # Z轴偏移校准值设为0
        self.writeByte(OFSZ, 0x00)
        # 链接使能,测量模式
        self.writeByte(POWER_CTL, 0x28)
        # 延时1秒等待参数配置生效
        time.sleep(1)

    def readXYZ(self) -> tuple[float, float, float]:
        """
        读取XYZ三轴加速度数据并转换为实际值

        Returns:
            tuple[float, float, float]: 包含X、Y、Z三轴加速度值的元组（单位：mg）

        Raises:
            OSError: I2C读取失败
            AttributeError: 传感器地址未初始化

        Notes:
            数据转换公式：原始值 × 3.9mg/LSB（16g量程下分辨率为3.9mg/LSB）；使用小端模式解包16位数据

        ==========================================
        Read XYZ three-axis acceleration data and convert to actual values

        Returns:
            tuple[float, float, float]: Tuple containing X, Y, Z three-axis acceleration values (unit: mg)

        Raises:
            OSError: I2C read failure
            AttributeError: Sensor address not initialized

        Notes:
            Data conversion formula: Raw value × 3.9mg/LSB (resolution is 3.9mg/LSB under 16g range); unpack 16-bit data using little-endian mode
        """
        # 定义数据解包格式为小端模式16位有符号整数
        fmt = "<h"  # little-endian
        # 读取X轴低字节寄存器（0x32）
        buf1 = self.readByte(0x32)
        # 读取X轴高字节寄存器（0x33）
        buf2 = self.readByte(0x33)
        # 拼接高低字节为字节数组
        buf = bytearray([buf1[0], buf2[0]])
        # 解包获取X轴原始值
        (x,) = ustruct.unpack(fmt, buf)
        # 转换为实际加速度值（mg）
        x = x * 3.9
        # print('x:',x)

        # 读取Y轴低字节寄存器（0x34）
        buf1 = self.readByte(0x34)
        # 读取Y轴高字节寄存器（0x35）
        buf2 = self.readByte(0x35)
        # 拼接高低字节为字节数组
        buf = bytearray([buf1[0], buf2[0]])
        # 解包获取Y轴原始值
        (y,) = ustruct.unpack(fmt, buf)
        # 转换为实际加速度值（mg）
        y = y * 3.9
        # print('y:',y)

        # 读取Z轴低字节寄存器（0x36）
        buf1 = self.readByte(0x36)
        # 读取Z轴高字节寄存器（0x37）
        buf2 = self.readByte(0x37)
        # 拼接高低字节为字节数组
        buf = bytearray([buf1[0], buf2[0]])
        # 解包获取Z轴原始值
        (z,) = ustruct.unpack(fmt, buf)
        # 转换为实际加速度值（mg）
        z = z * 3.9
        # print('z:',z)
        # print('************************')
        # time.sleep(0.5)
        # 返回三轴加速度值
        return (x, y, z)

    def writeByte(self, addr: int, data: int) -> None:
        """
        向传感器指定寄存器写入单个字节数据

        Args:
            addr (int): 寄存器地址（8位，0x00-0x3F）
            data (int): 要写入的字节数据（0-255）

        Raises:
            ValueError: 参数为None
            TypeError: 参数类型错误
            ValueError: 参数值超出范围
            AttributeError: 传感器地址未初始化
            OSError: I2C写入失败

        Notes:
            采用I2C内存写操作，将数据写入指定寄存器地址

        ==========================================
        Write a single byte of data to the specified register of the sensor

        Args:
            addr (int): Register address (8-bit, 0x00-0x3F)
            data (int): Byte data to be written (0-255)

        Raises:
            ValueError: Parameter is None
            TypeError: Parameter type error
            ValueError: Parameter value out of range
            AttributeError: Sensor address not initialized
            OSError: I2C write failure

        Notes:
            Use I2C memory write operation to write data to the specified register address
        """
        # 参数验证
        if addr is None:
            raise ValueError("addr cannot be None")
        if not isinstance(addr, int):
            raise TypeError(f"addr must be int, got {type(addr).__name__}")
        if addr < 0 or addr > 0x3F:
            raise ValueError(f"addr must be 0x00-0x3F, got {hex(addr)}")
        if data is None:
            raise ValueError("data cannot be None")
        if not isinstance(data, int):
            raise TypeError(f"data must be int, got {type(data).__name__}")
        if data < 0 or data > 255:
            raise ValueError(f"data must be 0-255, got {data}")

        # 将数据转换为字节数组
        d = bytearray([data])
        # 写入数据到指定寄存器
        self.i2c.writeto_mem(self.slvAddr, addr, d)

    def readByte(self, addr: int) -> bytearray:
        """
        从传感器指定寄存器读取单个字节数据

        Args:
            addr (int): 寄存器地址（8位，0x00-0x3F）

        Returns:
            bytearray: 包含读取字节的字节数组（长度为1）

        Raises:
            ValueError: 参数为None
            TypeError: 参数类型错误
            ValueError: 参数值超出范围
            AttributeError: 传感器地址未初始化
            OSError: I2C读取失败

        Notes:
            采用I2C内存读操作，从指定寄存器地址读取1个字节数据

        ==========================================
        Read a single byte of data from the specified register of the sensor

        Args:
            addr (int): Register address (8-bit, 0x00-0x3F)

        Returns:
            bytearray: Byte array containing the read byte (length 1)

        Raises:
            ValueError: Parameter is None
            TypeError: Parameter type error
            ValueError: Parameter value out of range
            AttributeError: Sensor address not initialized
            OSError: I2C read failure

        Notes:
            Use I2C memory read operation to read 1 byte of data from the specified register address
        """
        # 参数验证
        if addr is None:
            raise ValueError("addr cannot be None")
        if not isinstance(addr, int):
            raise TypeError(f"addr must be int, got {type(addr).__name__}")
        if addr < 0 or addr > 0x3F:
            raise ValueError(f"addr must be 0x00-0x3F, got {hex(addr)}")

        # 读取指定寄存器的1个字节数据
        return self.i2c.readfrom_mem(self.slvAddr, addr, 1)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
