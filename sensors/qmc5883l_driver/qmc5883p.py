# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午4:52
# @Author  : robert-hh
# @File    : main.py
# @Description : QMC5883P三轴磁力传感器驱动  读取原始/缩放磁力数据，配置采样率、量程、过采样等参数 参考自:https://github.com/robert-hh/QMC5883
# @License : MIT

__version__ = "0.1.0"
__author__ = "robert-hh"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class mag_base:
    """
    磁力传感器基础类，定义传感器通用接口
    Attributes:
        i2c: I2C总线对象，用于与传感器进行I2C通信

    Methods:
        read_scaled: 读取缩放后的磁力数据（X/Y/Z轴）和温度值
        read_raw: 读取原始磁力数据（X/Y/Z轴）
        set_sampling_rate: 设置采样率（空实现）
        set_range: 设置量程（空实现）
        set_oversampling: 设置过采样率（空实现）
        reset: 重置传感器（空实现）

    Notes:
        该类为抽象基类，需由具体传感器类继承并实现相关方法
    ==========================================
    Base class for magnetic sensor, defines common interfaces for sensors
    Attributes:
        i2c: I2C bus object for I2C communication with the sensor

    Methods:
        read_scaled: Read scaled magnetic data (X/Y/Z axis) and temperature value
        read_raw: Read raw magnetic data (X/Y/Z axis)
        set_sampling_rate: Set sampling rate (empty implementation)
        set_range: Set measurement range (empty implementation)
        set_oversampling: Set oversampling rate (empty implementation)
        reset: Reset sensor (empty implementation)

    Notes:
        This class is an abstract base class, which needs to be inherited and implemented by specific sensor classes
    """

    def __init__(self, i2c) -> None:
        """
        初始化磁力传感器基础类
        Args:
            i2c: I2C总线对象，用于与传感器通信

        Raises:
            无

        Notes:
            初始化I2C总线对象供后续方法使用


        ==========================================
        Initialize the base class of magnetic sensor
        Args:
            i2c: I2C bus object for communication with the sensor

        Raises:
            None

        Notes:
            Initialize the I2C bus object for use by subsequent methods
        """
        self.i2c = i2c

    def read_scaled(self) -> tuple[float, float, float, float]:
        """
        读取缩放后的磁力数据（X/Y/Z轴）和温度值（默认返回0）
        Args:
            无

        Raises:
            无

        Notes:
            基类中为默认实现，需子类重写


        ==========================================
        Read scaled magnetic data (X/Y/Z axis) and temperature value (returns 0 by default)
        Args:
            None

        Raises:
            None

        Notes:
            Default implementation in base class, needs to be overridden by subclasses
        """
        return (0.0, 0.0, 0.0, 0.0)

    def read_raw(self) -> tuple[int, int, int]:
        """
        读取原始磁力数据（X/Y/Z轴）（默认返回0）
        Args:
            无

        Raises:
            无

        Notes:
            基类中为默认实现，需子类重写


        ==========================================
        Read raw magnetic data (X/Y/Z axis) (returns 0 by default)
        Args:
            None

        Raises:
            None

        Notes:
            Default implementation in base class, needs to be overridden by subclasses
        """
        return (0, 0, 0)

    def set_sampling_rate(self, rate: int) -> None:
        """
        设置传感器采样率（空实现）
        Args:
            rate: 采样率参数

        Raises:
            无

        Notes:
            基类中为空实现，需子类重写


        ==========================================
        Set sensor sampling rate (empty implementation)
        Args:
            rate: Sampling rate parameter

        Raises:
            None

        Notes:
            Empty implementation in base class, needs to be overridden by subclasses
        """
        pass

    def set_range(self, val: int) -> None:
        """
        设置传感器量程（空实现）
        Args:
            val: 量程参数

        Raises:
            无

        Notes:
            基类中为空实现，需子类重写


        ==========================================
        Set sensor measurement range (empty implementation)
        Args:
            val: Range parameter

        Raises:
            None

        Notes:
            Empty implementation in base class, needs to be overridden by subclasses
        """
        pass

    def set_oversampling(self, val: int) -> None:
        """
        设置传感器过采样率（空实现）
        Args:
            val: 过采样率参数

        Raises:
            无

        Notes:
            基类中为空实现，需子类重写


        ==========================================
        Set sensor oversampling rate (empty implementation)
        Args:
            val: Oversampling rate parameter

        Raises:
            None

        Notes:
            Empty implementation in base class, needs to be overridden by subclasses
        """
        pass

    def reset(self) -> None:
        """
        重置传感器（空实现）
        Args:
            无

        Raises:
            无

        Notes:
            基类中为空实现，需子类重写


        ==========================================
        Reset sensor (empty implementation)
        Args:
            None

        Raises:
            None

        Notes:
            Empty implementation in base class, needs to be overridden by subclasses
        """
        pass


class QMC5883P(mag_base):
    """
    QMC5883P三轴磁力传感器具体实现类，继承自mag_base
    Attributes:
        i2c: I2C总线对象，用于与QMC5883P传感器通信
        range: 当前传感器量程配置值
        temp_offset: 温度偏移量，用于温度校准

    Methods:
        __init__: 初始化QMC5883P传感器，配置默认参数
        i2c_readregs: 从指定寄存器读取指定字节数的数据
        i2c_writereg: 向指定寄存器写入数据（字节或整数）
        range_sel: 自动选择合适的量程，避免数据溢出
        _set_cnf: 配置寄存器的指定位段值
        set_samplingrate: 设置传感器采样率
        set_oversampling: 设置传感器过采样率
        set_range: 设置传感器量程
        reset: 软件重置传感器
        ready: 等待传感器数据就绪
        read_raw: 读取原始X/Y/Z轴磁力数据
        read_scaled: 读取缩放后的X/Y/Z轴磁力数据和温度值

    Notes:
        1. 传感器I2C地址固定为0x2C
        2. 量程可选2/8/12/30高斯，对应不同的LSB/G系数
        3. 采样率可选10/50/100/200Hz
    ==========================================
    Concrete implementation class for QMC5883P 3-axis magnetic sensor, inherited from mag_base
    Attributes:
        i2c: I2C bus object for communication with QMC5883P sensor
        range: Current sensor range configuration value
        temp_offset: Temperature offset for temperature calibration

    Methods:
        __init__: Initialize QMC5883P sensor and configure default parameters
        i2c_readregs: Read specified number of bytes from specified register
        i2c_writereg: Write data (bytes or integer) to specified register
        range_sel: Automatically select appropriate range to avoid data overflow
        _set_cnf: Configure specified bit segment value of register
        set_samplingrate: Set sensor sampling rate
        set_oversampling: Set sensor oversampling rate
        set_range: Set sensor measurement range
        reset: Software reset of the sensor
        ready: Wait for sensor data to be ready
        read_raw: Read raw X/Y/Z axis magnetic data
        read_scaled: Read scaled X/Y/Z axis magnetic data and temperature value

    Notes:
        1. The sensor's I2C address is fixed at 0x2C
        2. Measurement range can be 2/8/12/30 Gauss, corresponding to different LSB/G coefficients
        3. Sampling rate can be 10/50/100/200Hz
    """

    # QMC5883P传感器I2C地址
    ADDR = const(0x2C)

    # 量程配置常量 - 2高斯
    CONFIG_2GAUSS = const(3)
    # 量程配置常量 - 8高斯
    CONFIG_8GAUSS = const(2)
    # 量程配置常量 - 12高斯
    CONFIG_12GAUSS = const(1)
    # 量程配置常量 - 30高斯
    CONFIG_30GAUSS = const(0)

    # 控制寄存器2常量 - 软件重置
    CR2_SOFT_RESET = const(0x80)

    # 控制寄存器1模式常量 - 挂起模式
    CR1_MODE_SUSPEND = const(0)
    # 控制寄存器1模式常量 - 普通模式
    CR1_MODE_NORMAL = const(1)
    # 控制寄存器1模式常量 - 单次测量模式
    CR1_MODE_SINGLE = const(2)
    # 控制寄存器1模式常量 - 连续测量模式
    CR1_MODE_CONT = const(3)

    # 控制寄存器1输出数据率常量 - 10Hz
    CR1_ODR_10HZ = const(0)
    # 控制寄存器1输出数据率常量 - 50Hz
    CR1_ODR_50HZ = const(1 << 2)
    # 控制寄存器1输出数据率常量 - 100Hz
    CR1_ODR_100HZ = const(2 << 2)
    # 控制寄存器1输出数据率常量 - 200Hz
    CR1_ODR_200HZ = const(3 << 2)

    # 控制寄存器1过采样常量 - 8次采样
    CR1_OVR_SMPL8 = const(0)
    # 控制寄存器1过采样常量 - 4次采样
    CR1_OVR_SMPL4 = const(1 << 4)
    # 控制寄存器1过采样常量 - 2次采样
    CR1_OVR_SMPL2 = const(2 << 4)
    # 控制寄存器1过采样常量 - 1次采样
    CR1_OVR_SMPL1 = const(3 << 4)

    # 控制寄存器1下采样常量 - 1次采样
    CR1_DOWN_SMPL1 = const(0)
    # 控制寄存器1下采样常量 - 2次采样
    CR1_DOWN_SMPL2 = const(1 << 6)
    # 控制寄存器1下采样常量 - 4次采样
    CR1_DOWN_SMPL4 = const(2 << 6)
    # 控制寄存器1下采样常量 - 8次采样
    CR1_DOWN_SMPL8 = const(3 << 6)

    # 不同量程对应的LSB/高斯系数 [30GAUSS,12GAUSS,8GAUSS,2GAUSS]
    _lsb_per_G = [1000, 2500, 3750, 15000]

    def __init__(self, i2c, temp_offset=0) -> None:
        """
        初始化QMC5883P传感器，配置默认参数
        Args:
            i2c: I2C总线对象，用于与传感器通信
            temp_offset: 温度偏移量，默认值为0

        Raises:
            无

        Notes:
            1. 调用父类初始化方法
            2. 重置传感器
            3. 配置SYZ轴符号
            4. 设置默认量程、采样率、过采样率等参数
            5. 等待传感器就绪


        ==========================================
        Initialize QMC5883P sensor and configure default parameters
        Args:
            i2c: I2C bus object for communication with the sensor
            temp_offset: Temperature offset, default value is 0

        Raises:
            None

        Notes:
            1. Call the parent class initialization method
            2. Reset the sensor
            3. Configure SYZ axis sign
            4. Set default range, sampling rate, oversampling rate and other parameters
            5. Wait for the sensor to be ready
        """
        super().__init__(i2c)
        self.reset()

        # 配置SYZ轴的符号位
        self.i2c_writereg(0x29, b"\x06")  # define the sign for syz axis
        self.set_range(0)
        # 配置控制寄存器1：8次下采样、8次过采样、200Hz输出率、普通模式
        self.i2c_writereg(0x0A, QMC5883P.CR1_DOWN_SMPL8 | QMC5883P.CR1_OVR_SMPL8 | QMC5883P.CR1_ODR_200HZ | QMC5883P.CR1_MODE_NORMAL)
        self.ready()
        self.set_range(0)

    def i2c_readregs(self, regAddr: int, bytenum: int) -> bytes:
        """
        从指定寄存器地址读取指定字节数的数据
        Args:
            regAddr: 寄存器地址
            bytenum: 要读取的字节数

        Raises:
            无

        Notes:
            1. 先向传感器写入要读取的寄存器地址
            2. 再从传感器读取指定字节数的数据


        ==========================================
        Read specified number of bytes from specified register address
        Args:
            regAddr: Register address
            bytenum: Number of bytes to read

        Raises:
            None

        Notes:
            1. First write the register address to be read to the sensor
            2. Then read the specified number of bytes from the sensor
        """
        self.i2c.writeto(QMC5883P.ADDR, bytes([regAddr]))
        return self.i2c.readfrom(QMC5883P.ADDR, bytenum)

    def i2c_writereg(self, regAddr: int, buff: bytes | int) -> None:
        """
        向指定寄存器地址写入数据（字节或整数）
        Args:
            regAddr: 寄存器地址
            buff: 要写入的数据，可以是bytes类型或int类型

        Raises:
            无

        Notes:
            1. 构建包含寄存器地址和数据的字节数组
            2. 若为int类型，转换为小端序字节
            3. 通过I2C总线写入数据到传感器


        ==========================================
        Write data (bytes or integer) to specified register address
        Args:
            regAddr: Register address
            buff: Data to be written, can be bytes type or int type

        Raises:
            None

        Notes:
            1. Construct a byte array containing register address and data
            2. If it is int type, convert to little-endian bytes
            3. Write data to sensor via I2C bus
        """
        r = bytearray([regAddr])
        if type(buff) is bytes:
            r.extend(buff)
        elif type(buff) is int:
            r.extend(buff.to_bytes(((len(bin(buff)) - 3) // 8) + 1, "little"))

        self.i2c.writeto(QMC5883P.ADDR, r)

    def range_sel(self) -> None:
        """
        自动选择合适的量程，避免数据溢出
        Args:
            无

        Raises:
            无

        Notes:
            1. 读取状态寄存器检查溢出标志
            2. 若溢出则降低量程（增大测量范围）
            3. 更新量程配置寄存器


        ==========================================
        Automatically select appropriate range to avoid data overflow
        Args:
            None

        Raises:
            None

        Notes:
            1. Read status register to check overflow flag
            2. If overflow occurs, reduce the range (increase measurement range)
            3. Update range configuration register
        """
        self.range = QMC5883P.CONFIG_2GAUSS
        status = self.i2c_readregs(0x09, 1)
        if status[0] & 0x02 != 0x00:
            if self.range == 0:
                return
            else:
                self.range -= 1
                self.i2c_writereg(0x0B, bytes([self.range << 2]))

    def _set_cnf(self, val: int, offset: int, sz: int) -> None:
        """
        配置寄存器的指定位段值（私有方法）
        Args:
            val: 要设置的位段值
            offset: 位段偏移量
            sz: 位段长度

        Raises:
            无

        Notes:
            1. 读取当前寄存器值
            2. 清除指定位段的原有值
            3. 设置新的位段值
            4. 写回寄存器


        ==========================================
        Configure specified bit segment value of register (private method)
        Args:
            val: Bit segment value to set
            offset: Bit segment offset
            sz: Bit segment length

        Raises:
            None

        Notes:
            1. Read current register value
            2. Clear original value of specified bit segment
            3. Set new bit segment value
            4. Write back to register
        """
        cur = self.i2c_readregs(0x0A, 1)[0]
        cur &= ~(((1 << sz) - 1) << offset)
        cur |= val << offset
        self.i2c_writereg(0x0A, cur)

    def set_samplingrate(self, rate: int) -> None:
        """
        设置传感器采样率
        Args:
            rate: 采样率参数（0-3对应10/50/100/200Hz）

        Raises:
            无

        Notes:
            调用私有方法_set_cnf配置控制寄存器1的采样率位段（偏移6，长度2）


        ==========================================
        Set sensor sampling rate
        Args:
            rate: Sampling rate parameter (0-3 corresponds to 10/50/100/200Hz)

        Raises:
            None

        Notes:
            Call private method _set_cnf to configure sampling rate bit segment (offset 6, length 2) of control register 1
        """
        self._set_cnf(rate, 6, 2)

    def set_oversampling(self, val: int) -> None:
        """
        设置传感器过采样率
        Args:
            val: 过采样率参数（0-3对应8/4/2/1次采样）

        Raises:
            无

        Notes:
            调用私有方法_set_cnf配置控制寄存器1的过采样位段（偏移4，长度2）


        ==========================================
        Set sensor oversampling rate
        Args:
            val: Oversampling rate parameter (0-3 corresponds to 8/4/2/1 samples)

        Raises:
            None

        Notes:
            Call private method _set_cnf to configure oversampling bit segment (offset 4, length 2) of control register 1
        """
        self._set_cnf(val, 4, 2)

    def set_range(self, val: int) -> None:
        """
        设置传感器量程
        Args:
            val: 量程参数（0-3对应2/8/12/30高斯）

        Raises:
            无

        Notes:
            1. 转换量程参数为传感器寄存器对应的配置值
            2. 写入配置寄存器设置量程


        ==========================================
        Set sensor measurement range
        Args:
            val: Range parameter (0-3 corresponds to 2/8/12/30 Gauss)

        Raises:
            None

        Notes:
            1. Convert range parameter to configuration value corresponding to sensor register
            2. Write to configuration register to set range
        """
        self.range = QMC5883P.CONFIG_2GAUSS - val
        self.i2c_writereg(0x0B, self.range << 2)

    def reset(self) -> None:
        """
        软件重置传感器
        Args:
            无

        Raises:
            无

        Notes:
            1. 向控制寄存器2写入软件重置指令
            2. 延时1毫秒等待重置完成


        ==========================================
        Software reset of the sensor
        Args:
            None

        Raises:
            None

        Notes:
            1. Write software reset command to control register 2
            2. Delay 1 millisecond to wait for reset completion
        """
        self.i2c_writereg(0x0B, QMC5883P.CR2_SOFT_RESET)
        time.sleep_ms(1)

    def ready(self) -> None:
        """
        等待传感器数据就绪
        Args:
            无

        Raises:
            IOError: 等待超时（超过100毫秒）时抛出

        Notes:
            1. 循环读取状态寄存器检查数据就绪标志
            2. 超时时间为100毫秒，超时则抛出IOError


        ==========================================
        Wait for sensor data to be ready
        Args:
            None

        Raises:
            IOError: Thrown when waiting times out (more than 100 milliseconds)

        Notes:
            1. Cyclically read status register to check data ready flag
            2. Timeout is 100 milliseconds, IOError is thrown if timeout
        """
        status = b"\x02"
        i = 0
        while status[0] & 0x01 == 0x00:
            i += 1
            time.sleep_ms(1)
            status = self.i2c_readregs(0x09, 1)
            if i > 100:
                raise IOError("request timeout")

    def read_raw(self) -> tuple[int, int, int]:
        """
        读取原始X/Y/Z轴磁力数据
        Args:
            无

        Raises:
            无

        Notes:
            1. 从0x01寄存器读取6字节数据
            2. 按小端序解析为3个短整型（X/Y/Z轴）


        ==========================================
        Read raw X/Y/Z axis magnetic data
        Args:
            None

        Raises:
            None

        Notes:
            1. Read 6 bytes of data from register 0x01
            2. Parse into 3 short integers (X/Y/Z axis) in little-endian order
        """
        return struct.unpack("<hhh", self.i2c_readregs(0x01, 6))

    def read_scaled(self) -> tuple[float, float, float, float]:
        """
        读取缩放后的X/Y/Z轴磁力数据和温度值（温度值默认返回0）
        Args:
            无

        Raises:
            无

        Notes:
            1. 读取原始数据
            2. 根据当前量程对应的LSB/高斯系数进行缩放
            3. 温度值暂未实现，返回0


        ==========================================
        Read scaled X/Y/Z axis magnetic data and temperature value (temperature value returns 0 by default)
        Args:
            None

        Raises:
            None

        Notes:
            1. Read raw data
            2. Scale according to LSB/Gauss coefficient corresponding to current range
            3. Temperature value is not implemented yet, returns 0
        """
        x, y, z = self.read_raw()
        scale = QMC5883P._lsb_per_G[self.range]
        return (x / scale, y / scale, z / scale, 0)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
