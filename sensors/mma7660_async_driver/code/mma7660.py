# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/20 下午2:15
# @Author  : hogeiha
# @File    : mma7660.py
# @Description : MMA7660加速度计驱动
# @License : MIT
__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from machine import I2C  # 取消注释，适配Pico的I2C导入

# ======================================== 全局变量 ============================================

# 无

# ======================================== 功能函数 ============================================

# 无

# ======================================== 自定义类 ============================================


class MMA7660_DATA:
    """
    存储MMA7660所有寄存器数据的容器类
    Attributes:
        X (int|None): X轴原始数据
        Y (int|None): Y轴原始数据
        Z (int|None): Z轴原始数据
        TILT (int|None): 倾斜状态寄存器数据
        SRST (int|None): 采样率状态寄存器数据
        SPCNT (int|None): 采样计数寄存器数据
        INTSU (int|None): 中断使能寄存器数据
        MODE (int|None): 模式寄存器数据
        SR (int|None): 采样率寄存器数据
        PDET (int|None): 方向检测寄存器数据
        PD (int|None): 方向寄存器数据

    Methods:
        __init__(): 初始化所有属性为None

    Notes:
        仅用于数据封装，不包含业务逻辑

    ==========================================
    A container class that stores all register data of the MMA7660
    Attributes:
        X (int|None): Raw X-axis data
        Y (int|None): Raw Y-axis data
        Z (int|None): Raw Z-axis data
        TILT (int|None): Tilt status register data
        SRST (int|None): Sample rate status register data
        SPCNT (int|None): Sample count register data
        INTSU (int|None): Interrupt enable register data
        MODE (int|None): Mode register data
        SR (int|None): Sample rate register data
        PDET (int|None): Orientation detection register data
        PD (int|None): Orientation register data

    Methods:
        __init__(): Initialize all attributes to None

    Notes:
        Only for data encapsulation, no business logic
    """

    def __init__(self):
        self.X = None
        self.Y = None
        self.Z = None
        self.TILT = None
        self.SRST = None
        self.SPCNT = None
        self.INTSU = None
        self.MODE = None
        self.SR = None
        self.PDET = None
        self.PD = None


class MMA7660_LOOKUP(object):
    """
    加速度-角度查找表条目类
    Attributes:
        g (float|None): 加速度值（单位g）
        xyAngle (float|None): XY平面角度（度）
        zAngle (float|None): Z轴角度（度）

    Methods:
        __init__(): 初始化所有属性为None

    Notes:
        用于存储预计算的加速度和角度值，加速传感器数据处理

    ==========================================
    Acceleration-Angle Lookup Table Entry Class
    Attributes:
        g (float|None): Acceleration value (in g)
        xyAngle (float|None): XY plane angle (degrees)
        zAngle (float|None): Z-axis angle (degrees)

    Methods:
        __init__(): Initialize all attributes to None

    Notes:
        Used to store precomputed acceleration and angle values for faster sensor data processing
    """

    def __init__(self):
        self.g = None  # 加速度值（g）
        self.xyAngle = None  # XY平面角度
        self.zAngle = None  # Z轴角度


class Accelerometer(object):
    """
    MMA7660三轴加速度计驱动类
    Attributes:
        i2c (I2C): I2C总线对象
        address (int): 设备I2C地址
        accLookup (list[MMA7660_LOOKUP]): 加速度-角度查找表

    Methods:
        write(register, data): 向指定寄存器写入1字节数据
        read(register): 从指定寄存器读取1字节数据
        initAccelTable(): 初始化加速度-角度查找表
        setMode(mode): 设置传感器模式（待机/工作）
        setSampleRate(rate): 设置采样率
        getXYZ(): 读取X/Y/Z轴原始数据并转换为g值
        getAcceleration(): 获取加速度值（m/s²）
        getAllData(): 读取所有寄存器数据并返回MMA7660_DATA对象

    Notes:
        基于I2C通信，支持待机/工作模式切换，内置6位数据到g值的查找表转换

    ==========================================
    MMA7660 Three-Axis Accelerometer Driver Class
    Attributes:
        i2c (I2C): I2C bus object
        address (int): Device I2C address
        accLookup (list[MMA7660_LOOKUP]): Acceleration-angle lookup table

    Methods:
        write(register, data): Write 1 byte to specified register
        read(register): Read 1 byte from specified register
        initAccelTable(): Initialize acceleration-angle lookup table
        setMode(mode): Set sensor mode (standby/active)
        setSampleRate(rate): Set sample rate
        getXYZ(): Read raw X/Y/Z axis data and convert to g-values
        getAcceleration(): Get acceleration values (m/s²)
        getAllData(): Read all register data and return MMA7660_DATA object

    Notes:
        I2C-based communication, supports standby/active mode switching, built-in lookup table for 6-bit data to g-value conversion
    """

    # MMA7660 I2C地址（默认0x4C）
    MMA7660_ADDR = 0x4C
    # 超时时间（毫秒）
    MMA7660TIMEOUT = 500

    # 寄存器地址定义
    MMA7660_X = 0x00
    MMA7660_Y = 0x01
    MMA7660_Z = 0x02
    MMA7660_TILT = 0x03
    MMA7660_SRST = 0x04
    MMA7660_SPCNT = 0x05
    MMA7660_INTSU = 0x06
    # INTSU寄存器位定义
    MMA7660_SHINTX = 0x80
    MMA7660_SHINTY = 0x40
    MMA7660_SHINTZ = 0x20
    MMA7660_GINT = 0x10
    MMA7660_ASINT = 0x08
    MMA7660_PDINT = 0x04
    MMA7660_PLINT = 0x02
    MMA7660_FBINT = 0x01
    # 模式寄存器
    MMA7660_MODE = 0x07
    MMA7660_STAND_BY = 0x00
    MMA7660_ACTIVE = 0x01
    # 采样率寄存器
    MMA7660_SR = 0x08
    # 采样率配置值
    AUTO_SLEEP_120 = 0x00  # 统一小写0x，规范格式
    AUTO_SLEEP_64 = 0x01
    AUTO_SLEEP_32 = 0x02
    AUTO_SLEEP_16 = 0x03
    AUTO_SLEEP_8 = 0x04
    AUTO_SLEEP_4 = 0x05
    AUTO_SLEEP_2 = 0x06
    AUTO_SLEEP_1 = 0x07
    # 其他寄存器
    MMA7660_PDET = 0x09
    MMA7660_PD = 0x0A

    def __init__(self, i2c: I2C, address: int = MMA7660_ADDR, interrupts: bool = False) -> None:
        """
        初始化加速度计对象，配置I2C接口和传感器参数
        Args:
            i2c (I2C): 已初始化的I2C总线对象
            address (int): 设备I2C地址，默认0x4C
            interrupts (bool): 是否启用中断，默认False

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数取值错误

        Notes:
            初始化后传感器进入工作模式

        ==========================================
        Initialize the accelerometer object and configure the I2C interface and sensor parameters
        Args:
            i2c (I2C): Initialized I2C bus object
            address (int): Device I2C address, default 0x4C
            interrupts (bool): Whether to enable interrupts, default False

        Raises:
            TypeError: Parameter type error
            ValueError: Parameter value error

        Notes:
            Sensor enters active mode after initialization
        """
        # 参数验证
        if i2c is None:
            raise ValueError("I2C object cannot be None")
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be I2C object")
        if not isinstance(address, int):
            raise TypeError("address must be int")
        if address < 0 or address > 0x7F:
            raise ValueError("address must be in range 0-127")
        if not isinstance(interrupts, bool):
            raise TypeError("interrupts must be bool")

        # 初始化I2C对象和设备地址
        self.i2c: I2C = i2c
        self.address: int = address

        # 初始化加速度查找表
        self.accLookup: list[MMA7660_LOOKUP] = [MMA7660_LOOKUP() for _ in range(64)]  # 列表推导式更高效
        self.initAccelTable()

        # 初始化传感器
        self.setMode(self.MMA7660_STAND_BY)  # 待机模式才能写寄存器
        self.setSampleRate(self.AUTO_SLEEP_32)  # 设置采样率

        if interrupts:
            # 若开启中断，设置INTSU寄存器（示例值，可根据需求调整）
            self.write(self.MMA7660_INTSU, interrupts)

        self.setMode(self.MMA7660_ACTIVE)  # 切换到工作模式

    def write(self, register: int, data: int) -> bool:
        """
        向指定寄存器写入1字节数据
        Args:
            register (int): 寄存器地址（0-127）
            data (int): 待写入数据（0-255）

        Returns:
            bool: 写入成功返回True，失败返回False

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数取值错误

        Notes:
            使用MicroPython的writeto_mem方法

        ==========================================
        Write 1 byte of data to the specified register
        Args:
            register (int): Register address (0-127)
            data (int): Data to write (0-255)

        Returns:
            bool: True on success, False on failure

        Raises:
            TypeError: Parameter type error
            ValueError: Parameter value error

        Notes:
            Uses MicroPython's writeto_mem method
        """
        # 参数验证
        if register is None:
            raise ValueError("register cannot be None")
        if not isinstance(register, int):
            raise TypeError("register must be int")
        if register < 0 or register > 0x7F:
            raise ValueError("register address must be in range 0-127")
        if data is None:
            raise ValueError("data cannot be None")
        if not isinstance(data, int):
            raise TypeError("data must be int")
        if data < 0 or data > 0xFF:
            raise ValueError("data must be in range 0-255")

        try:
            # MicroPython的writeto_mem参数：地址、寄存器（整数）、数据（字节数组）
            self.i2c.writeto_mem(self.address, register, bytearray([data]))
            return True
        except OSError as e:
            print(f"写入寄存器0x{register:02X}失败: {e}")
            return False

    def read(self, register: int) -> int | None:
        """
        从指定寄存器读取1字节数据
        Args:
            register (int): 寄存器地址（0-127）

        Returns:
            int | None: 读取到的数据（0-255），失败返回None

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数取值错误

        Notes:
            使用MicroPython的readfrom_mem方法

        ==========================================
        Read 1 byte of data from the specified register
        Args:
            register (int): Register address (0-127)

        Returns:
            int | None: Read data (0-255), None on failure

        Raises:
            TypeError: Parameter type error
            ValueError: Parameter value error

        Notes:
            Uses MicroPython's readfrom_mem method
        """
        # 参数验证
        if register is None:
            raise ValueError("register cannot be None")
        if not isinstance(register, int):
            raise TypeError("register must be int")
        if register < 0 or register > 0x7F:
            raise ValueError("register address must be in range 0-127")

        try:
            # MicroPython的readfrom_mem：地址、寄存器、读取长度
            buf = self.i2c.readfrom_mem(self.address, register, 1)
            return buf[0]  # 返回整数，而非字节数组，更易处理
        except OSError as e:
            print(f"Failed to read register 0x{register:02X}: {e}")
            return None

    def initAccelTable(self) -> None:
        """
        初始化加速度-角度查找表（适配6位数据格式）
        Args:
            无

        Returns:
            None

        Raises:
            无

        Notes:
            计算64个条目的g值和角度值

        ==========================================
        Initialize acceleration-angle lookup table (adapted for 6-bit data format)
        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            Calculates g-value and angle for 64 entries
        """
        # 计算X/Y/Z轴的g值（范围：-1.5g ~ +1.5g，6位数据，分辨率~0.047g/位）
        val = 0.0
        # 0~31：正方向（0 ~ +1.453g）
        for i in range(32):
            self.accLookup[i].g = val
            val += 0.047  # 分辨率约0.047g/位

        # 32~63：负方向（-0.047 ~ -1.5g）
        val = -0.047
        for i in range(63, 31, -1):
            self.accLookup[i].g = val
            val -= 0.047

        # 计算角度值（XY平面和Z轴）
        val = 0.0
        valZ = 90.0
        # 0~21：0° ~ -56.49°（XY），90° ~ 146.49°（Z）
        for i in range(22):
            self.accLookup[i].xyAngle = val
            self.accLookup[i].zAngle = valZ
            val -= 2.69
            valZ += 2.69

        val = -2.69
        valZ = -87.31
        # 63~42：-2.69° ~ -59.18°（XY），-87.31° ~ -146.49°（Z）
        for i in range(63, 42, -1):
            self.accLookup[i].xyAngle = val
            self.accLookup[i].zAngle = valZ
            val -= 2.69
            valZ += 2.69

        # 22~42：无效值（标记为255）
        for i in range(22, 43):
            self.accLookup[i].xyAngle = 255
            self.accLookup[i].zAngle = 255

    def setMode(self, mode: int) -> bool:
        """
        设置传感器模式（待机/工作）
        Args:
            mode (int): 模式值，0=待机，1=工作

        Returns:
            bool: 写入成功返回True，失败返回False

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数取值错误

        Notes:
            模式寄存器地址0x07

        ==========================================
        Set sensor mode (standby/active)
        Args:
            mode (int): Mode value, 0=standby, 1=active

        Returns:
            bool: True on success, False on failure

        Raises:
            TypeError: Parameter type error
            ValueError: Parameter value error

        Notes:
            Mode register address 0x07
        """
        # 参数验证
        if mode is None:
            raise ValueError("mode cannot be None")
        if not isinstance(mode, int):
            raise TypeError("mode must be int")
        if mode not in (self.MMA7660_STAND_BY, self.MMA7660_ACTIVE):
            raise ValueError("mode must be 0 (standby) or 1 (active)")

        return self.write(self.MMA7660_MODE, mode)

    def setSampleRate(self, rate: int) -> bool:
        """
        设置采样率（修复原代码缺少rate参数的问题）
        Args:
            rate (int): 采样率配置值（0-7）

        Returns:
            bool: 写入成功返回True，失败返回False

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数取值错误

        Notes:
            采样率寄存器地址0x08，取值范围0-7

        ==========================================
        Set the sampling rate (fix the problem of the original code missing the rate parameter)
        Args:
            rate (int): Sample rate configuration value (0-7)

        Returns:
            bool: True on success, False on failure

        Raises:
            TypeError: Parameter type error
            ValueError: Parameter value error

        Notes:
            Sample rate register address 0x08, value range 0-7
        """
        # 参数验证
        if rate is None:
            raise ValueError("rate cannot be None")
        if not isinstance(rate, int):
            raise TypeError("rate must be int")
        if rate < 0 or rate > 0x07:
            raise ValueError("rate must be in range 0-7")

        return self.write(self.MMA7660_SR, rate)

    def getXYZ(self) -> tuple[float, float, float]:
        """
        读取X/Y/Z轴原始数据并转换为g值（核心方法）
        Args:
            无

        Returns:
            tuple[float, float, float]: (x_g, y_g, z_g) 加速度值，单位g。读取失败返回(0.0,0.0,0.0)

        Raises:
            无

        Notes:
            原始数据为6位有效位，通过查找表转换为g值

        ==========================================
        Read the raw data of X/Y/Z axes and convert it to g values (core method)
        Args:
            None

        Returns:
            tuple[float, float, float]: (x_g, y_g, z_g) acceleration values in g. Returns (0.0,0.0,0.0) on failure

        Raises:
            None

        Notes:
            Raw data uses 6 valid bits, converted to g-value via lookup table
        """
        # 读取X/Y/Z寄存器（6位有效数据，需处理溢出位）
        x_raw = self.read(self.MMA7660_X)
        y_raw = self.read(self.MMA7660_Y)
        z_raw = self.read(self.MMA7660_Z)

        if None in [x_raw, y_raw, z_raw]:
            return (0.0, 0.0, 0.0)  # 读取失败返回0

        # 提取6位有效数据（MMA7660的X/Y/Z寄存器只有低6位有效）
        x_6bit = x_raw & 0x3F  # 掩码保留低6位
        y_6bit = y_raw & 0x3F
        z_6bit = z_raw & 0x3F

        # 通过查找表获取g值
        x_g = self.accLookup[x_6bit].g
        y_g = self.accLookup[y_6bit].g
        z_g = self.accLookup[z_6bit].g

        return (x_g, y_g, z_g)

    def getAcceleration(self) -> tuple[float, float, float]:
        """
        获取加速度值（m/s²），1g=9.81m/s²
        Args:
            无

        Returns:
            tuple[float, float, float]: (x, y, z) 加速度值，单位m/s²。读取失败返回(0.0,0.0,0.0)

        Raises:
            无

        Notes:
            无

        ==========================================
        Obtain the acceleration value (m/s²), 1g = 9.81 m/s²
        Args:
            None

        Returns:
            tuple[float, float, float]: (x, y, z) acceleration values in m/s². Returns (0.0,0.0,0.0) on failure

        Raises:
            None

        Notes:
            None
        """
        x_g, y_g, z_g = self.getXYZ()
        x = x_g * 9.81
        y = y_g * 9.81
        z = z_g * 9.81
        return (x, y, z)

    def getAllData(self) -> MMA7660_DATA:
        """
        读取所有寄存器数据并返回MMA7660_DATA对象
        Args:
            无

        Returns:
            MMA7660_DATA: 包含所有寄存器数据的对象

        Raises:
            无

        Notes:
            依次读取每个寄存器，读取失败的寄存器对应属性为None

        ==========================================
        Read all register data and return an MMA7660_DATA object
        Args:
            None

        Returns:
            MMA7660_DATA: Object containing all register data

        Raises:
            None

        Notes:
            Reads each register sequentially, failed reads result in None attribute
        """
        data = MMA7660_DATA()
        data.X = self.read(self.MMA7660_X)
        data.Y = self.read(self.MMA7660_Y)
        data.Z = self.read(self.MMA7660_Z)
        data.TILT = self.read(self.MMA7660_TILT)
        data.SRST = self.read(self.MMA7660_SRST)
        data.SPCNT = self.read(self.MMA7660_SPCNT)
        data.INTSU = self.read(self.MMA7660_INTSU)
        data.MODE = self.read(self.MMA7660_MODE)
        data.SR = self.read(self.MMA7660_SR)
        data.PDET = self.read(self.MMA7660_PDET)
        data.PD = self.read(self.MMA7660_PD)
        return data


# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================
