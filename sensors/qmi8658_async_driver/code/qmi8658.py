# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : FreakStudio
# @File    : qmi8658.py
# @Description : QMI8658/QMI8658C 6-axis IMU driver
# @License : Apache-2.0

__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "Apache-2.0"
__platform__ = "MicroPython v1.23"

# const() 兼容导入
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import time

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# --- 寄存器地址常量 ---
REG_WHO_AM_I = const(0x00)  # 芯片 ID 寄存器
REG_REVISION = const(0x01)  # 版本号寄存器
REG_CTRL1 = const(0x02)  # 控制寄存器 1 (加速度配置)
REG_CTRL2 = const(0x03)  # 控制寄存器 2 (陀螺仪配置)
REG_CTRL3 = const(0x04)  # 控制寄存器 3 (功能配置)
REG_CTRL4 = const(0x05)  # 控制寄存器 4 (保留)
REG_CTRL5 = const(0x06)  # 控制寄存器 5 (低通滤波器)
REG_CTRL6 = const(0x07)  # 控制寄存器 6 (运动检测)
REG_CTRL7 = const(0x08)  # 控制寄存器 7 (使能)
REG_TIMESTAMP = const(0x30)  # 时间戳寄存器 (3 bytes)
REG_ACC_X_L = const(0x35)  # 加速度 X 轴低字节 (6 轴数据起始地址)

# 复用缓冲区：读取 12 字节原始数据 (6 轴 x 2 字节)
_BUF12 = bytearray(12)

# ======================================== 功能函数 ============================================


def _to_signed_16(value):
    """
    将无符号 16 位整数转换为有符号 16 位整数
    Args:
        value (int): 无符号 16 位整数 (0~65535)
    Returns:
        int: 有符号 16 位整数 (-32768~32767)
    ==========================================
    Convert unsigned 16-bit integer to signed 16-bit integer.
    Args:
        value (int): Unsigned 16-bit integer (0~65535)
    Returns:
        int: Signed 16-bit integer (-32768~32767)
    """
    if value >= 32768:
        value -= 65536
    return value


# ======================================== 自定义类 ============================================


class QMI8658:
    """
    QMI8658/QMI8658C 六轴 IMU 驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _reset_pin (Pin): 复位引脚实例
        _debug (bool): 调试日志开关
    Methods:
        who_am_i(): 读取芯片 ID 寄存器
        revision(): 读取芯片版本号
        reset(): 硬件复位设备
        configure_default(): 应用默认配置寄存器
        read_raw(): 读取原始六轴数据 (有符号整数)
        read_xyz(): 读取转换后的六轴数据 (g, dps)
        deinit(): 释放资源，禁用传感器
    Notes:
        - 依赖外部传入 I2C 实例，不在类内部创建总线对象
        - 默认配置：加速度 8g、陀螺仪 512dps、采样率 1000Hz
        - 参考 Waveshare Apache-2.0 驱动示例改写
        - 复位引脚 (reset_pin) 为可选参数，用于硬件复位
    ==========================================
    QMI8658/QMI8658C 6-axis IMU driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _reset_pin (Pin): Reset pin instance
        _debug (bool): Debug logging switch
    Methods:
        who_am_i(): Read chip ID register
        revision(): Read chip revision number
        reset(): Hardware reset the device
        configure_default(): Apply default configuration registers
        read_raw(): Read raw 6-axis data (signed integers)
        read_xyz(): Read converted 6-axis data (g, dps)
        deinit(): Release resources, disable sensor
    Notes:
        - Requires externally provided I2C instance
        - Default config: accelerometer 8g, gyroscope 512dps, ODR 1000Hz
        - Based on Waveshare Apache-2.0 driver reference
        - Reset pin is optional, used for hardware reset
    """

    # --- 设备识别常量 ---
    ADDR = const(0x6B)  # 默认 I2C 地址 (AD0 接 GND)
    WHO_AM_I_VALUE = const(0x05)  # 期望的 WHO_AM_I 返回值

    # --- 灵敏度常量 (与当前量程配置对应) ---
    # 加速度灵敏度：8g 量程下 1 LSB = 1/4096 g
    ACC_SENSITIVITY = 4096
    # 陀螺仪灵敏度：512dps 量程下 1 LSB = 1/64.0 dps
    GYRO_SENSITIVITY = 64.0

    # --- 默认配置寄存器值 ---
    # CTRL1: 加速度量程 8g, 采样率 1000Hz
    CFG_CTRL1 = const(0x60)
    # CTRL2: 陀螺仪量程 512dps, 采样率 1000Hz
    CFG_CTRL2 = const(0x23)
    # CTRL3: 使能加速度计和陀螺仪数据就绪中断
    CFG_CTRL3 = const(0x53)
    # CTRL4: 保留，默认值
    CFG_CTRL4 = const(0x00)
    # CTRL5: 低通滤波器带宽配置
    CFG_CTRL5 = const(0x11)
    # CTRL6: 运动检测关闭
    CFG_CTRL6 = const(0x00)
    # CTRL7: 使能加速度计和陀螺仪
    CFG_CTRL7_ENABLE = const(0x03)
    # CTRL7: 禁用所有传感器 (deinit 使用)
    CFG_CTRL7_DISABLE = const(0x00)

    __slots__ = ("_i2c", "_addr", "_reset_pin", "_debug")

    def __init__(self, i2c, address=ADDR, reset_pin=None, verify=True, debug=False):
        """
        初始化 QMI8658 驱动实例
        Args:
            i2c (I2C): I2C 总线实例
            address (int): I2C 设备地址，默认 0x6B
            reset_pin (Pin): 复位引脚实例，可选
            verify (bool): 是否验证 WHO_AM_I 寄存器，默认 True
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            ValueError: 参数类型错误
            RuntimeError: WHO_AM_I 验证不匹配，或 I2C 通信失败
        Notes:
            - 初始化时若提供 reset_pin 则自动执行硬件复位
            - verify=True 时自动读取并校验 WHO_AM_I
            - 初始化成功后自动应用 configure_default()
        ==========================================
        Initialize QMI8658 driver instance.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, default 0x6B
            reset_pin (Pin): Reset pin instance, optional
            verify (bool): Whether to verify WHO_AM_I register, default True
            debug (bool): Whether to enable debug log output, default False
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: WHO_AM_I verification mismatch, or I2C communication failed
        Notes:
            - Auto hardware reset if reset_pin provided
            - Auto verify WHO_AM_I if verify=True
            - Auto apply configure_default() after init
        """
        # 参数校验：i2c 必须提供 readfrom_mem 方法
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem()")
        # 参数校验：address 必须为 int
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        # 参数校验：verify 必须为 bool
        if not isinstance(verify, bool):
            raise ValueError("verify must be bool, got %s" % type(verify))
        # 参数校验：debug 必须为 bool
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = address
        self._reset_pin = reset_pin
        self._debug = debug

        # 如果提供了复位引脚，先执行硬件复位
        if reset_pin is not None:
            self.reset()

        # 验证芯片 ID
        if verify:
            chip_id = self.who_am_i()
            if chip_id != self.WHO_AM_I_VALUE:
                raise RuntimeError("QMI8658 WHO_AM_I mismatch: expected 0x%02X, got 0x%02X" % (self.WHO_AM_I_VALUE, chip_id))

        # 应用默认配置
        self._log("Init complete, applying default config")
        self.configure_default()

    def _log(self, msg):
        """输出调试日志 (仅 _debug=True 时打印)"""
        if self._debug:
            print("[QMI8658] %s" % msg)

    def who_am_i(self):
        """
        读取 WHO_AM_I 芯片 ID 寄存器
        Returns:
            int: 芯片 ID 值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read WHO_AM_I chip ID register.
        Returns:
            int: Chip ID value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self._log("Reading WHO_AM_I")
        return self._read_u8(REG_WHO_AM_I)

    def revision(self):
        """
        读取芯片版本号寄存器
        Returns:
            int: 芯片版本号
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read chip revision register.
        Returns:
            int: Chip revision number
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self._log("Reading revision")
        return self._read_u8(REG_REVISION)

    def reset(self):
        """
        硬件复位设备
        拉低复位引脚 10ms 后拉高，等待 50ms 启动
        Notes:
            - 副作用：复位引脚电平翻转，设备寄存器恢复默认值
            - 需要预先在 __init__ 中提供 reset_pin 参数
            - ISR-safe: 否
        ==========================================
        Hardware reset the device.
        Pull reset pin low for 10ms then high, wait 50ms for startup.
        Notes:
            - Side effect: reset pin toggled, registers restored to defaults
            - Requires reset_pin provided in __init__
            - ISR-safe: No
        """
        self._log("Hardware reset")
        # 拉低复位引脚 10ms
        self._reset_pin.value(0)
        time.sleep_ms(10)
        # 拉高复位引脚，等待设备启动
        self._reset_pin.value(1)
        time.sleep_ms(50)

    def configure_default(self):
        """
        写入默认配置寄存器
        Notes:
            - 副作用：修改芯片内部配置寄存器，设定加速度量程/采样率等
            - 写入的寄存器：CTRL1~CTRL7
            - ISR-safe: 否
        ==========================================
        Write default configuration registers.
        Notes:
            - Side effect: modifies chip configuration registers
            - Registers written: CTRL1~CTRL7
            - ISR-safe: No
        """
        self._log("Applying default config")
        # 加速度量程 8g, 采样率 1000Hz
        self._write_u8(REG_CTRL1, self.CFG_CTRL1)
        # 陀螺仪量程 512dps, 采样率 1000Hz
        self._write_u8(REG_CTRL2, self.CFG_CTRL2)
        # 使能数据就绪中断
        self._write_u8(REG_CTRL3, self.CFG_CTRL3)
        # 保留寄存器
        self._write_u8(REG_CTRL4, self.CFG_CTRL4)
        # 低通滤波器配置
        self._write_u8(REG_CTRL5, self.CFG_CTRL5)
        # 运动检测关闭
        self._write_u8(REG_CTRL6, self.CFG_CTRL6)
        # 使能加速度计和陀螺仪
        self._write_u8(REG_CTRL7, self.CFG_CTRL7_ENABLE)

    def read_raw(self):
        """
        读取原始六轴数据 (12 字节)
        Returns:
            tuple: (ax, ay, az, gx, gy, gz) 原始有符号 16 位整数值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 从 REG_ACC_X_L (0x35) 开始连续读取 12 字节
            - 数据顺序：加速度 X/Y/Z 低-高字节，陀螺仪 X/Y/Z 低-高字节
            - 每个轴由相邻两字节小端拼接后转为有符号整数
            - ISR-safe: 否
        ==========================================
        Read raw 6-axis data (12 bytes).
        Returns:
            tuple: (ax, ay, az, gx, gy, gz) raw signed 16-bit integer values
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads 12 bytes starting from REG_ACC_X_L (0x35)
            - Data order: accel X/Y/Z low-high byte, gyro X/Y/Z low-high byte
            - Each axis uses two adjacent bytes in little-endian, converted to signed int
            - ISR-safe: No
        """
        # 从加速度 X 轴低字节开始，连续读取 12 字节原始数据
        try:
            self._i2c.readfrom_mem_into(self._addr, REG_ACC_X_L, _BUF12)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X: %s" % (REG_ACC_X_L, str(e)))
        # 解析 6 轴有符号 16 位数据 (小端格式)
        out = []
        for index in range(6):
            # 低字节 | (高字节 << 8)
            value = _BUF12[index * 2] | (_BUF12[index * 2 + 1] << 8)
            # 无符号转有符号 16 位
            out.append(_to_signed_16(value))
        return tuple(out)

    def read_xyz(self):
        """
        读取转换后的六轴数据 (加速度单位 g，陀螺仪单位 dps)
        Returns:
            tuple: (ax_g, ay_g, az_g, gx_dps, gy_dps, gz_dps)
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 加速度原始值 / ACC_SENSITIVITY (4096) 得到 g 值 (8g 量程)
            - 陀螺仪原始值 / GYRO_SENSITIVITY (64.0) 得到 dps 值 (512dps 量程)
            - ISR-safe: 否
        ==========================================
        Read converted 6-axis data (g for accelerometer, dps for gyroscope).
        Returns:
            tuple: (ax_g, ay_g, az_g, gx_dps, gy_dps, gz_dps)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Raw accel / ACC_SENSITIVITY (4096) gives g (8g range)
            - Raw gyro / GYRO_SENSITIVITY (64.0) gives dps (512dps range)
            - ISR-safe: No
        """
        # 读取原始有符号数据
        raw = self.read_raw()
        # 加速度除以灵敏度转为 g；陀螺仪除以灵敏度转为 dps
        return (
            raw[0] / self.ACC_SENSITIVITY,
            raw[1] / self.ACC_SENSITIVITY,
            raw[2] / self.ACC_SENSITIVITY,
            raw[3] / self.GYRO_SENSITIVITY,
            raw[4] / self.GYRO_SENSITIVITY,
            raw[5] / self.GYRO_SENSITIVITY,
        )

    def deinit(self):
        """
        释放资源：向 CTRL7 写入 0x00 禁用加速度计和陀螺仪，降低功耗
        Notes:
            - 副作用：传感器停止工作，寄存器值被修改
            - ISR-safe: 否
        ==========================================
        Release resources: write 0x00 to CTRL7 to disable accelerometer
        and gyroscope, reducing power consumption.
        Notes:
            - Side effect: sensor stops, register value modified
            - ISR-safe: No
        """
        self._log("Deinitializing sensor")
        self._write_u8(REG_CTRL7, self.CFG_CTRL7_DISABLE)

    # --- 私有 I2C 底层通信方法 ---

    def _read_u8(self, reg):
        """从指定寄存器读取 1 字节"""
        try:
            return self._i2c.readfrom_mem(self._addr, reg, 1)[0]
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X: %s" % (reg, str(e)))

    def _write_u8(self, reg, value):
        """向指定寄存器写入 1 字节"""
        try:
            self._i2c.writeto_mem(self._addr, reg, bytes([value & 0xFF]))
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X: %s" % (reg, str(e)))


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
