# Python env   : MicroPython v1.23.0              
# -*- coding: utf-8 -*-        
# @Time    : 2024/6/24 上午10:32   
# @Author  : 李清水            
# @File    : imu.py       
# @Description : 串口IMU驱动代码
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import UART
# 时间相关的模块
import time
# 二进制/ASCII 转换的模块
import binascii

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def timed_function(f: callable, *args: tuple, **kwargs: dict) -> callable:
    """
    计时装饰器，用于计算并打印函数或方法的运行时间。

    Args:
        f (callable): 需要传入的函数或方法。
        args (tuple): 传递给函数的任意数量的位置参数。
        kwargs (dict): 传递给函数的任意数量的关键字参数。

    Returns:
        callable: 返回一个带有运行时间统计的函数。

    ==========================================

    Timing decorator to calculate and print the execution time 
    of a function or method.

    Args:
        f (callable): Function or method to wrap.
        args (tuple): Arbitrary positional arguments for f.
        kwargs (dict): Arbitrary keyword arguments for f.

    Returns:
        callable: A function with execution time measurement.
    """
    myname = str(f).split(' ')[1]

    def new_func(*args: tuple, **kwargs: dict) -> any:
        t: int = time.ticks_us()
        result = f(*args, **kwargs)
        delta: int = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta / 1000))
        return result

    return new_func

# ======================================== 自定义类 ============================================

class IMU:
    """
    六轴陀螺仪类，负责与 IMU 传感器进行串口通信，支持指令发送、数据接收和解析。

    功能包括：
    - 设置陀螺仪的工作模式、传输模式和安装模式。
    - 接收三轴加速度、角速度（陀螺仪数据）和角度（倾角）。
    - 提供指令发送接口（如校准、清零、模式切换）。

    Attributes:
        k_acc (int): 加速度数据的转换系数 (raw → g)。
        k_temp (float): 温度数据的转换系数 (raw → °C)。
        c_temp (float): 温度偏移量。
        k_gyro (int): 角速度数据的转换系数 (raw → °/s)。
        k_angle (int): 角度数据的转换系数 (raw → °)。

        ZAXISCLEARCMD (list): Z 轴角度清零指令。
        ACCCALBCMD (list): 加速度校准指令。
        CONVSLEEPCMD (list): 睡眠/工作模式切换指令。
        UARTMODECMD (list): 串口模式指令。
        IICMODECMD (list): I²C 模式指令。
        HORIZINSTCMD (list): 水平安装模式指令。
        VERTINSTCMD (list): 垂直安装模式指令。
        BAUD115200CMD (list): 波特率 115200 指令。
        BAUD9600CMD (list): 波特率 9600 指令。

        WORK_MODE (int): 工作模式 = 1。
        SLEEP_MODE (int): 睡眠模式 = 0。
        UART_MODE (int): 串口模式 = 1。
        IIC_MODE (int): I²C 模式 = 0。
        HORIZ_INST (int): 水平安装模式 = 1。
        VERT_INST (int): 垂直安装模式 = 0。

    Methods:
        __init__(UART_Obj: UART) -> None:
            初始化 IMU 类并进行加速度校准与 Z 轴清零。
        SendCMD(cmd: list[int]) -> bool:
            发送控制指令到 IMU。
        RecvData() -> tuple[float, ...]:
            接收并解析 IMU 的加速度、角速度和角度数据。

    ==========================================
    6-axis gyroscope class for serial communication with IMU sensors.  
    Provides command transmission, data reception, and parsing.

    Features:
    - Configure work mode, transfer mode, and installation mode.
    - Receive 3-axis acceleration, angular velocity, and angle data.
    - Send control commands for calibration, reset, and mode switching.

    Attributes:
        k_acc (int): Conversion factor for acceleration (raw → g).
        k_temp (float): Conversion factor for temperature (raw → °C).
        c_temp (float): Temperature offset constant.
        k_gyro (int): Conversion factor for angular velocity (raw → °/s).
        k_angle (int): Conversion factor for angle (raw → °).

        ZAXISCLEARCMD (list): Reset Z-axis angle command.
        ACCCALBCMD (list): Accelerometer calibration command.
        CONVSLEEPCMD (list): Sleep/work mode toggle command.
        UARTMODECMD (list): UART transfer mode command.
        IICMODECMD (list): I²C transfer mode command.
        HORIZINSTCMD (list): Horizontal installation command.
        VERTINSTCMD (list): Vertical installation command.
        BAUD115200CMD (list): Set baudrate to 115200 command.
        BAUD9600CMD (list): Set baudrate to 9600 command.

        WORK_MODE (int): Work mode = 1.
        SLEEP_MODE (int): Sleep mode = 0.
        UART_MODE (int): UART transfer mode = 1.
        IIC_MODE (int): I²C transfer mode = 0.
        HORIZ_INST (int): Horizontal installation = 1.
        VERT_INST (int): Vertical installation = 0.

    Methods:
        __init__(UART_Obj: UART) -> None:
            Initialize IMU and perform calibration & Z-axis reset.
        SendCMD(cmd: list[int]) -> bool:
            Send control command to IMU.
        RecvData() -> tuple[float, ...]:
            Receive and parse acceleration, gyro, and angle data.
    """

    # 声明类变量：类变量在类的所有实例之间共享，用于存储与类相关的共享数据

    # 以下变量为用于陀螺仪数据转换的系数和常量
    k_acc = 16
    k_temp = 96.38
    c_temp = 36.53
    k_gyro = 2000
    k_angle = 180

    # 以下变量为各个指令的数据内容
    # z轴清零指令
    ZAXISCLEARCMD = [0XFF, 0XAA, 0X52]
    # 加速度校准指令
    ACCCALBCMD    = [0XFF, 0XAA, 0X67]
    # 切换睡眠模式和工作模式的指令
    CONVSLEEPCMD  = [0XFF, 0XAA, 0X60]
    # 串口传输模式指令
    UARTMODECMD   = [0XFF, 0XAA, 0X61]
    # IIC传输模式指令
    IICMODECMD    = [0XFF, 0XAA, 0X62]
    # 水平安装模式指令
    HORIZINSTCMD  = [0XFF, 0XAA, 0x65]
    # 垂直安装模式指令
    VERTINSTCMD   = [0XFF, 0XAA, 0x66]
    # 串口波特率设置为 115200 指令
    BAUD115200CMD = [0XFF, 0XAA, 0X63]
    # 串口波特率设置为 9600 指令
    BAUD9600CMD   = [0XFF, 0XAA, 0X64]
    # 带宽设置指令不常用，留给用户自行实现即可
    # ============ 带宽协议 ============
    # | HEARDER1 | HEARDER2 |  CMD  |
    # CMD可选为：
    # 0x81 - 带宽为 256 Hz
    # 0x82 - 带宽为 188 Hz
    # 0x83 - 带宽为 98  Hz
    # 0x84 - 带宽为 42  Hz
    # 0x85 - 带宽为 20  Hz
    # 0x86 - 带宽为 10  Hz
    # 0x87 - 带宽为 5   Hz
    # 需要注意的是，自行实现带宽相关指令后，
    # 需要在self.SendCMD方法的入口参数判断中添加对应类变量

    # 代表工作模式的类变量
    # WORK_MODE  - 工作模式：1
    # SLEEP_MODE - 睡眠模式：0
    WORK_MODE, SLEEP_MODE = (1, 0)

    # 代表数据传输模式的类变量
    # UART_MODE  - 串口传输模式：1
    # IIC_MODE   - IIC传输模式：0
    UART_MODE, IIC_MODE = (1, 0)

    # 代表安装模式的类变量
    # HORIZ_INST - 水平安装模式：1
    # VERT_INST  - 垂直安装模式：0
    HORIZ_INST, VERT_INST = (1, 0)

    # 初始化函数
    def __init__(self, UART_Obj: UART) -> None:
        """
        初始化 IMU 类，设置串口对象并执行校准与 Z 轴清零。

        Args:
            UART_Obj (UART): 串口对象，用于与 IMU 通信。

        Returns:
            None

        ==========================================
        Initialize IMU, set UART object, and perform 
        accelerometer calibration and Z-axis reset.

        Args:
            UART_Obj (UART): UART object for IMU communication.

        Returns:
            None
        """

        # IMU类的实例和UART类的实例为组合关系
        self.UART_Obj: UART = UART_Obj

        # 暂存接受自陀螺仪相关运动数据的变量
        # 三轴加速度数据
        self.acc_x: float = 0
        self.acc_y: float = 0
        self.acc_z: float = 0
        # 温度数据
        self.temp: float = 0
        # 三轴角速度数据
        self.gyro_x: float = 0
        self.gyro_y: float = 0
        self.gyro_z: float = 0
        # 三轴角度数据
        self.angle_x: float = 0
        self.angle_y: float = 0
        self.angle_z: float = 0

        # 串口校验和
        self.checksum: int = 0

        # 串口数据接收的临时缓存列表
        self.datalist: list[int] = [0] * 15

        # 记录串口接收数据次数的变量
        self.rcvcount: int = 0

        # 陀螺仪不同类型数据接收完成的标志量
        # 0：未接收完成，1：已接收完成
        # 加速度数据接收完成标志量
        self.recv_acc_flag: int = 0
        # 角加速度数据接收完成标志量
        self.recv_gyro_flag: int = 0
        # 角度数据接收完成标志量
        self.recv_angle_flag: int = 0

        # 陀螺仪工作模式
        self.workmode: int = IMU.WORK_MODE
        # 陀螺仪数据传输模式
        self.transmode: int = IMU.UART_MODE
        # 陀螺仪安装模式
        self.instmode: int = IMU.HORIZ_INST

        # 注意，在校准和z轴角度清零时，传感器务必保持水平/垂直的静止状态
        # Z轴角度清零
        self.SendCMD(IMU.ZAXISCLEARCMD)
        # 加速度校准
        self.SendCMD(IMU.ACCCALBCMD)

    # 私有方法：计算校验和是否正确
    def __CalChecksum(self) -> bool:
        """
        计算并验证接收数据的校验和。

        Returns:
            bool: 校验和正确返回 True，否则 False。

        ==========================================
        Calculate and verify checksum of received data.

        Returns:
            bool: True if checksum is valid, False otherwise.
        """

        # 获取串口接收到的校验和
        self.checksum = self.datalist[10]

        # 声明临时校验和
        tempchecksum: int = 0
        # 计算校验和
        for i in range(0, 10):
            tempchecksum = tempchecksum + self.datalist[i]

        # 取出计算校验和的低8位
        tempchecksum = tempchecksum & 0xff

        # 判断接收是否正确
        if tempchecksum != self.checksum:
            return False
        else:
            return True

    # 串口指令发送函数
    def SendCMD(self, cmd: list[int]) -> bool:
        """
        发送控制指令到 IMU。

        Args:
            cmd (list[int]): 指令列表。

        Returns:
            bool: 发送成功返回 True，否则 False。

        ==========================================
        Send control command to IMU.

        Args:
            cmd (list[int]): Command list.

        Returns:
            bool: True if command sent successfully, else False.
        """

        # 若指令未在IMU类变量中定义，则返回False
        if (cmd != IMU.ZAXISCLEARCMD
            and cmd != IMU.ACCCALBCMD
            and cmd != IMU.CONVSLEEPCMD
            and cmd != IMU.UARTMODECMD
            and cmd != IMU.IICMODECMD
            and cmd != IMU.HORIZINSTCMD
            and cmd != IMU.VERTINSTCMD
            and cmd != IMU.BAUD115200CMD
            and cmd != IMU.BAUD9600CMD):

            return False

        # 将指令内容发送
        for data in cmd:
            # UART.write(buf)方法中buf必须具有buffer protocol
            self.UART_Obj.write(bytes([data]))

        # 若为睡眠模式和工作模式切换指令
        if cmd == IMU.CONVSLEEPCMD:
            # 对self中workmode属性进行切换赋值
            if self.workmode == IMU.WORK_MODE:
                self.workmode = IMU.SLEEP_MODE
            else:
                self.workmode = IMU.WORK_MODE

        # 若发送串口传输模式指令
        if cmd == IMU.UARTMODECMD:
            # 陀螺仪数据传输模式为串口传输模式
            self.transmode = IMU.UART_MODE

        # 若发送IIC传输模式指令
        if cmd == IMU.IICMODECMD:
            # 陀螺仪数据传输模式为IIC传输模式
            self.transmode = IMU.IIC_MODE

        # 若发送水平安装模式指令
        if cmd == IMU.HORIZINSTCMD:
            # 陀螺仪安装模式为水平安装模式
            self.instmode = IMU.HORIZ_INST

        # 若发送垂直安装模式指令
        if cmd == IMU.VERTINSTCMD:
            # 陀螺仪安装模式为垂直安装模式
            self.instmode = IMU.VERT_INST

        # 若发送串口波特率设置为 115200 指令
        if cmd == IMU.BAUD115200CMD:
            # 串口波特率设置为 115200
            self.UART_Obj.init(baudrate = 115200)

        # 若发送串口波特率设置为 9600 指令
        if cmd == IMU.BAUD9600CMD:
            # 串口波特率设置为 9600
            self.UART_Obj.init(baudrate = 9600)

        # 如果指令是Z轴清零指令或加速度校准指令
        if cmd == IMU.ZAXISCLEARCMD or cmd == IMU.ACCCALBCMD:
            # 在陀螺仪校准进行时，等待100ms
            time.sleep_ms(500)

        return True

    # 串口数据接收函数
    # 使用@timed_function装饰器，计算IMU.RecvData方法运行时间
    # 无需计算程序运行时间时，去掉@timed_function装饰器即可
    @timed_function
    def RecvData(self) -> tuple[float, float, float]:
        """
        接收并解析 IMU 数据，包括加速度、角速度和角度。

        Returns:
            tuple: (acc_x, acc_y, acc_z, temp, gyro_x, gyro_y, gyro_z, angle_x, angle_y, angle_z)

        ==========================================
        Receive and parse IMU data, including acceleration, 
        angular velocity, and angle.

        Returns:
            tuple: (acc_x, acc_y, acc_z, temp, gyro_x, gyro_y, gyro_z, angle_x, angle_y, angle_z)
        """
        # 循环执行，直到三帧数据（加速度、角速度、角度）接收完毕
        while True:
            # 通过UART.any方法判断是否有数据
            if self.UART_Obj.any():
                # 接收一个串口数据，为bytes类型
                tempdata = self.UART_Obj.read(1)
                # 将数据对象中的字节转换为十六进制表示
                tempdata = binascii.hexlify(tempdata)
                # 将十六进制表示的bytes对象转为十进制的整型数字
                tempdata = int(tempdata, 16)

                # 将接收到的一个数据存入datalist列表中
                self.datalist[self.rcvcount] = tempdata

                # 如果接收到的不是帧头0x55，则重新开始接收
                if self.datalist[0] != 0x55:
                    # 串口接收数据次数变量清零
                    self.rcvcount = 0
                # 若是帧头0x55，则继续接收
                else:
                    # 串口接收数据次数变量加1
                    self.rcvcount = self.rcvcount + 1

                    # 一帧数据为11个数据包
                    # 若是为到11次，说明接收尚未完成，继续接收下一个数据
                    if self.rcvcount < 11:
                        continue
                    # 一帧数据接收完成，开始数据解析
                    # ============================================ 数据帧格式 ============================================
                    # | HEADER | TYPE | DATA0L | DATA0H | DATA1L | DATA1H | DATA2L | DATA2H | DATA3L | DATA3H | SUMCRC |
                    # | 0x55   | x    | x      | x      | x      | x      | x      | x      | x      | x      | x      |
                    # SUMCRC=0x55+TYPE+DATA1L+DATA1H+DATA2L+DATA2H+DATA3L+DATA3H+DATA4L+DATA4H，取校验和的低8位，为char类型
                    # ============================================ 数据帧格式 ============================================
                    else:
                        # 若校验和计算无误，则进行数据转换,否则重新进行下一帧数据的接收
                        if self.__CalChecksum():

                            # 如果为加速度类型数据
                            if self.datalist[1] == 0x51:
                                # 进行数据转换
                                self.acc_x = (self.datalist[3] << 8 | self.datalist[2]) / 32768 * IMU.k_acc
                                self.acc_y = (self.datalist[5] << 8 | self.datalist[4]) / 32768 * IMU.k_acc
                                self.acc_z = (self.datalist[7] << 8 | self.datalist[6]) / 32768 * IMU.k_acc
                                self.temp = (self.datalist[9] << 8 | self.datalist[8]) / 32768 * IMU.k_temp + IMU.c_temp

                                # 对加速度数据接收完成标志量赋值
                                self.recv_acc_flag = 1

                            # 如果为角速度类型数据
                            if self.datalist[1] == 0x52:
                                # 进行数据转换
                                self.gyro_x = (self.datalist[3] << 8 | self.datalist[2]) / 32768 * IMU.k_gyro
                                self.gyro_y = (self.datalist[5] << 8 | self.datalist[4]) / 32768 * IMU.k_gyro
                                self.gyro_z = (self.datalist[7] << 8 | self.datalist[6]) / 32768 * IMU.k_gyro
                                # 对角速度数据接收完成标志量赋值
                                self.recv_gyro_flag = 1

                            # 如果为角度类型数据
                            if self.datalist[1] == 0x53:
                                # 进行数据转换
                                self.angle_x = (self.datalist[3] << 8 | self.datalist[2]) / 32768 * IMU.k_angle
                                self.angle_y = (self.datalist[5] << 8 | self.datalist[4]) / 32768 * IMU.k_angle
                                self.angle_z = (self.datalist[7] << 8 | self.datalist[6]) / 32768 * IMU.k_angle
                                # 对角度数据接收完成标志量赋值
                                self.recv_angle_flag = 1

                            # 如果三帧数据都接收完毕，则返回一个时间段内接收到的陀螺仪数据
                            if self.recv_acc_flag == 1 and self.recv_gyro_flag == 1 and self.recv_angle_flag == 1:
                                # 对三个类型数据接收完成标志量清零
                                self.recv_acc_flag = 0
                                self.recv_gyro_flag = 0
                                self.recv_angle_flag = 0

                                # 返回一个时间段内接收到的陀螺仪数据
                                return self.acc_x, self.acc_y, self.acc_z, self.temp, self.gyro_x, self.gyro_y, self.gyro_z, self.angle_x, self.angle_y, self.angle_z

                        # 接受完一帧数据后，对串口接收数据次数的变量进行清零
                        self.rcvcount = 0