# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2023/01/01 00:00
# @Author  : Jose D. Montoya
# @File    : mlx90393.py
# @Description : MLX90393 三轴磁力计传感器驱动（Melexis）
# @License : MIT

__version__ = "0.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
import struct
from micropython import const

# ======================================== 全局变量 ============================================

# I2C 命令字节
_CMD_RR       = const(0b01010000)
_CMD_WR       = const(0b01100000)
_CMD_SM       = const(0b00110000)
_CMD_RM       = const(0b01000000)
_CMD_AXIS_ALL = const(0xE)
_REG_WHOAMI   = const(0x0C)

# 增益常量
GAIN_5X    = const(0x00)
GAIN_4X    = const(0x01)
GAIN_3X    = const(0x02)
GAIN_2_5X  = const(0x03)
GAIN_2X    = const(0x04)
GAIN_1_67X = const(0x05)
GAIN_1_33X = const(0x06)
GAIN_1X    = const(0x07)

# 分辨率常量
RESOLUTION_0 = const(0x0)
RESOLUTION_1 = const(0x1)
RESOLUTION_2 = const(0x2)
RESOLUTION_3 = const(0x3)

# 数字滤波器常量
FILTER_0 = const(0x0)
FILTER_1 = const(0x1)
FILTER_2 = const(0x2)
FILTER_3 = const(0x3)
FILTER_4 = const(0x4)
FILTER_5 = const(0x5)
FILTER_6 = const(0x6)
FILTER_7 = const(0x7)

# 过采样常量
OSR_0 = const(0x0)
OSR_1 = const(0x1)
OSR_2 = const(0x2)
OSR_3 = const(0x3)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    MLX90393 I2C 寄存器位域读写描述符
    Attributes:
        bit_mask (int): 位掩码
        register (int): 寄存器地址
        star_bit (int): 起始位偏移
        lenght (int): 读取字节数（寄存器宽度+1，含状态字节）
        lsb_first (bool): 是否小端序
        cmd_read (int): 读命令字节
        cmd_write (int): 写命令字节
    Methods:
        __get__: 读取位域值
        __set__: 写入位域值
    Notes:
        - 作为类属性描述符使用，宿主类须有 _i2c、_address、_status_last 属性
        - MLX90393 每次读写均需发送命令字节，响应首字节为状态字节
    ==========================================
    MLX90393 I2C register bit-field read/write descriptor.
    Attributes:
        bit_mask (int): Bit mask
        register (int): Register address
        star_bit (int): Start bit offset
        lenght (int): Bytes to read (register width + 1 for status byte)
        lsb_first (bool): Whether LSB-first byte order
        cmd_read (int): Read command byte
        cmd_write (int): Write command byte
    Methods:
        __get__: Read bit-field value
        __set__: Write bit-field value
    Notes:
        - Used as class-level descriptor; host class must have _i2c, _address, _status_last
        - MLX90393 requires a command byte per transaction; first response byte is status
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 2,
        lsb_first: bool = True,
        cmd_read: int = None,
        cmd_write: int = None,
    ) -> None:
        """
        初始化位域描述符
        Args:
            num_bits (int): 位域宽度
            register_address (int): 寄存器地址
            start_bit (int): 起始位（LSB 位置）
            register_width (int): 寄存器字节宽度，默认 2
            lsb_first (bool): 字节序，True=小端，默认 True
            cmd_read (int): 读命令字节
            cmd_write (int): 写命令字节
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize bit-field descriptor.
        Args:
            num_bits (int): Bit-field width
            register_address (int): Register address
            start_bit (int): Start bit (LSB position)
            register_width (int): Register byte width, default 2
            lsb_first (bool): Byte order, True=little-endian, default True
            cmd_read (int): Read command byte
            cmd_write (int): Write command byte
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        # 计算位掩码
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.star_bit = start_bit
        # +1 用于容纳响应中的状态字节
        self.lenght = register_width + 1
        self.lsb_first = lsb_first
        self.cmd_read = cmd_read
        self.cmd_write = cmd_write

    def __get__(self, obj, objtype=None) -> int:
        """
        读取位域值
        Args:
            obj: 宿主对象
            objtype: 宿主类型（未使用）
        Returns:
            int: 位域当前值（已右移对齐）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read bit-field value.
        Args:
            obj: Host object
            objtype: Host type (unused)
        Returns:
            int: Current bit-field value (right-shifted)
        Notes:
            - ISR-safe: No
        """
        # 发送读命令 + 寄存器地址（左移2位为MLX90393协议要求）
        payload = bytes([self.cmd_read, self.register << 2])
        obj._i2c.writeto(obj._address, payload)

        data = bytearray(self.lenght)
        data = obj._i2c.readfrom(obj._address, self.lenght)
        # 跳过首字节状态字节，取寄存器数据
        mem_value = memoryview(data[1:])
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]
        # 提取目标位域并右移对齐
        reg = (reg & self.bit_mask) >> self.star_bit
        return reg

    def __set__(self, obj, value: int) -> None:
        """
        写入位域值（读-改-写）
        Args:
            obj: 宿主对象
            value (int): 待写入的位域值（未移位）
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：先读后写，保留寄存器其他位；更新 _status_last
        ==========================================
        Write bit-field value (read-modify-write).
        Args:
            obj: Host object
            value (int): Bit-field value to write (unshifted)
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Read-modify-write; updates _status_last
        """
        # 读取当前寄存器值
        payload = bytes([self.cmd_read, self.register << 2])
        obj._i2c.writeto(obj._address, payload)

        data = bytearray(self.lenght)
        data = obj._i2c.readfrom(obj._address, self.lenght)
        memory_value = memoryview(data[1:])
        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]
        # 清除目标位域，写入新值
        reg &= ~self.bit_mask
        value <<= self.star_bit
        reg |= value
        reg = reg.to_bytes(self.lenght - 1, "big")
        # 构造写命令帧：[CMD_WR, MSB, LSB, REG<<2]
        payload = bytearray(self.lenght + 1)
        payload[0] = self.cmd_write
        payload[3] = self.register << 2
        payload[1] = reg[0]
        payload[2] = reg[1]
        obj._i2c.writeto(obj._address, payload)
        # 读取状态字节
        data = obj._i2c.readfrom(obj._address, self.lenght)
        obj._status_last = data[0]


class RegisterStructCMD:
    """
    MLX90393 I2C 寄存器结构体读写描述符
    Attributes:
        format (str): struct 格式字符串
        register (int): 寄存器地址
        lenght (int): 读取字节数（含状态字节）
        cmd_read (int): 读命令字节
        cmd_write (int): 写命令字节
    Methods:
        __get__: 读取并解包寄存器值
        __set__: 打包并写入寄存器值
    Notes:
        - 作为类属性描述符使用，宿主类须有 _i2c、_address、_status_last 属性
        - 响应首字节为状态字节，数据从第 2 字节起
    ==========================================
    MLX90393 I2C register struct read/write descriptor.
    Attributes:
        format (str): struct format string
        register (int): Register address
        lenght (int): Bytes to read (including status byte)
        cmd_read (int): Read command byte
        cmd_write (int): Write command byte
    Methods:
        __get__: Read and unpack register value
        __set__: Pack and write register value
    Notes:
        - Used as class-level descriptor; host class must have _i2c, _address, _status_last
        - First response byte is status; data starts at byte 2
    """

    def __init__(
        self,
        register_address: int,
        form: str,
        cmd_read: int = None,
        cmd_write: int = None,
    ) -> None:
        """
        初始化寄存器结构体描述符
        Args:
            register_address (int): 寄存器地址
            form (str): struct 格式字符串（如 "H"=uint16）
            cmd_read (int): 读命令字节
            cmd_write (int): 写命令字节
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize register struct descriptor.
        Args:
            register_address (int): Register address
            form (str): struct format string (e.g. "H"=uint16)
            cmd_read (int): Read command byte
            cmd_write (int): Write command byte
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        self.format = form
        self.register = register_address
        # +1 用于容纳响应中的状态字节
        self.lenght = struct.calcsize(form) + 1
        self.cmd_read = cmd_read
        self.cmd_write = cmd_write

    def __get__(self, obj, objtype=None):
        """
        读取并解包寄存器值
        Args:
            obj: 宿主对象
            objtype: 宿主类型（未使用）
        Returns:
            int: 解包后的寄存器值
        Notes:
            - ISR-safe: 否
            - 副作用：更新 _status_last
        ==========================================
        Read and unpack register value.
        Args:
            obj: Host object
            objtype: Host type (unused)
        Returns:
            int: Unpacked register value
        Notes:
            - ISR-safe: No
            - Side effects: updates _status_last
        """
        # 发送读命令 + 寄存器地址
        payload = bytes([self.cmd_read, self.register << 2])
        obj._i2c.writeto(obj._address, payload)
        data = obj._i2c.readfrom(obj._address, self.lenght)
        # 解包：首字节为状态，后续为大端 uint16
        obj._status_last, val = struct.unpack(">BH", data)
        return val

    def __set__(self, obj, value: int) -> None:
        """
        打包并写入寄存器值
        Args:
            obj: 宿主对象
            value (int): 待写入的整数值
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：直接覆盖写入寄存器；更新 _status_last
        ==========================================
        Pack and write register value.
        Args:
            obj: Host object
            value (int): Integer value to write
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Direct register write; updates _status_last
        """
        # 构造写命令帧：[CMD_WR, MSB, LSB, REG<<2]
        payload = bytes([
            self.cmd_write,
            value >> 8,
            value & 0xFF,
            self.register << 2,
        ])
        obj._i2c.writeto(obj._address, payload)
        data = obj._i2c.readfrom(obj._address, self.lenght)
        obj._status_last = data[0]


class MLX90393:
    """
    MLX90393 三轴磁力计传感器驱动类（Melexis）
    Attributes:
        _i2c: I2C 总线实例
        _address (int): 设备 I2C 地址，默认 0x0C
        _status_last (int): 最近一次操作的状态字节
    Methods:
        magnetic: 读取 X/Y/Z 三轴磁场值（微特斯拉）
        gain: 获取/设置模拟增益
        resolution_x / resolution_y / resolution_z: 获取/设置各轴分辨率
        digital_filter: 获取/设置数字滤波器
        oversampling: 获取/设置过采样率
        deinit(): 释放资源
    Notes:
        - I2C 地址默认 0x0C，可通过硬件引脚配置为 0x0C~0x0F
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 每次读取 magnetic 会阻塞等待转换完成（由 TCONV 表决定）
    ==========================================
    MLX90393 three-axis magnetometer sensor driver (Melexis).
    Attributes:
        _i2c: I2C bus instance
        _address (int): Device I2C address, default 0x0C
        _status_last (int): Status byte from last operation
    Methods:
        magnetic: Read X/Y/Z magnetic field values in microteslas
        gain: Get/set analog gain
        resolution_x / resolution_y / resolution_z: Get/set per-axis resolution
        digital_filter: Get/set digital filter setting
        oversampling: Get/set oversampling ratio
        deinit(): Release resources
    Notes:
        - Default I2C address 0x0C; configurable to 0x0C~0x0F via hardware pins
        - Requires externally provided I2C instance
        - Each magnetic read blocks for conversion time (determined by TCONV table)
    """

    # XY 轴各分辨率/增益灵敏度查找表（单位 µT/LSB）
    _res0_xy = {
        0: (0.751, 0.601, 0.451, 0.376, 0.300, 0.250, 0.200, 0.150),
        1: (0.787, 0.629, 0.472, 0.393, 0.315, 0.262, 0.21,  0.157),
    }
    _res1_xy = {
        0: (1.502, 1.202, 0.901, 0.751, 0.601, 0.501, 0.401, 0.300),
        1: (1.573, 1.258, 0.944, 0.787, 0.629, 0.524, 0.419, 0.315),
    }
    _res2_xy = {
        0: (3.004, 2.403, 1.803, 1.502, 1.202, 1.001, 0.801, 0.601),
        1: (3.146, 2.517, 1.888, 1.573, 1.258, 1.049, 0.839, 0.629),
    }
    _res3_xy = {
        0: (6.009, 4.840, 3.605, 3.004, 2.403, 2.003, 1.602, 1.202),
        1: (6.292, 5.034, 3.775, 3.146, 2.517, 2.097, 1.678, 1.258),
    }

    # Z 轴各分辨率/增益灵敏度查找表（单位 µT/LSB）
    _res0_z = {
        0: (1.210, 0.968, 0.726, 0.605, 0.484, 0.403, 0.323, 0.242),
        1: (1.267, 1.014, 0.760, 0.634, 0.507, 0.422, 0.338, 0.253),
    }
    _res1_z = {
        0: (2.420, 1.936, 1.452, 1.210, 0.968, 0.807, 0.645, 0.484),
        1: (2.534, 2.027, 1.521, 1.267, 1.014, 0.845, 0.676, 0.507),
    }
    _res2_z = {
        0: (4.840, 3.872, 2.904, 2.420, 1.936, 1.613, 1.291, 0.968),
        1: (5.068, 4.055, 3.041, 2.534, 2.027, 1.689, 1.352, 1.014),
    }
    _res3_z = {
        0: (9.680,  7.744, 5.808, 4.840, 3.872, 3.227, 2.581, 1.936),
        1: (10.137, 8.109, 6.082, 5.068, 4.055, 3.379, 2.703, 2.027),
    }

    # 转换时间查找表（毫秒），索引 [DIGFILT][OSR]
    _TCONV = (
        (1.27,  1.84,  3.00,   5.30),
        (1.46,  2.23,  3.76,   6.84),
        (1.84,  3.00,  5.30,   9.91),
        (2.61,  4.53,  8.37,  16.05),
        (4.15,  7.60, 14.52,  28.34),
        (7.22, 13.75, 26.80,  52.92),
        (13.36, 26.04, 51.38, 102.07),
        (25.65, 50.61, 100.53, 200.37),
    )

    # 分辨率查找表（按轴分类）
    _resolutionsxy = {0: _res0_xy, 1: _res1_xy, 2: _res2_xy, 3: _res3_xy}
    _resolutionsz  = {0: _res0_z,  1: _res1_z,  2: _res2_z,  3: _res3_z}

    # 寄存器描述符
    _reg_0 = RegisterStructCMD(0x00, "H", _CMD_RR, _CMD_WR)
    _reg_2 = RegisterStructCMD(0x02, "H", _CMD_RR, _CMD_WR)
    _bits  = CBits(3, 0x02, 3, 2, False, _CMD_RR, _CMD_WR)

    # 寄存器 0x00 位域
    _hall = CBits(4, 0x00, 0, 2, False, _CMD_RR, _CMD_WR)
    _gain = CBits(3, 0x00, 4, 2, False, _CMD_RR, _CMD_WR)

    # 寄存器 0x02 位域
    _oversampling = CBits(2, 0x02, 0, 2, False, _CMD_RR, _CMD_WR)
    _digfilt      = CBits(3, 0x02, 2, 2, False, _CMD_RR, _CMD_WR)
    _res_x        = CBits(2, 0x02, 5, 2, False, _CMD_RR, _CMD_WR)
    _res_y        = CBits(2, 0x02, 7, 2, False, _CMD_RR, _CMD_WR)
    _res_z        = CBits(2, 0x02, 9, 2, False, _CMD_RR, _CMD_WR)

    def __init__(self, i2c, address: int = 0x0C) -> None:
        """
        初始化 MLX90393 传感器驱动
        Args:
            i2c: I2C 总线实例，需支持 writeto / readfrom 接口
            address (int): I2C 设备地址，默认 0x0C
        Returns:
            None
        Raises:
            ValueError: i2c 不具备 I2C 接口特征，或 address 超出范围
        Notes:
            - ISR-safe: 否
            - 初始化时写入默认配置：RESOLUTION_3、FILTER_7、OSR_3、GAIN_1X
        ==========================================
        Initialize MLX90393 sensor driver.
        Args:
            i2c: I2C bus instance supporting writeto / readfrom
            address (int): I2C device address, default 0x0C
        Returns:
            None
        Raises:
            ValueError: i2c missing I2C interface, or address out of range
        Notes:
            - ISR-safe: No
            - Writes default config on init: RESOLUTION_3, FILTER_7, OSR_3, GAIN_1X
        """
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int) or not (0x00 <= address <= 0x7F):
            raise ValueError("address must be int in 0x00~0x7F, got %s" % address)
        self._i2c = i2c
        self._address = address
        self._status_last = None
        # 写入默认配置
        self._res_x = self._res_y = self._res_z = RESOLUTION_3
        self._digfilt = FILTER_7
        self._oversampling = OSR_3
        self._gain = GAIN_1X

    @property
    def gain(self) -> str:
        """
        获取当前模拟增益设置
        Args:
            无
        Returns:
            str: 增益名称（如 "GAIN_1X"）
        Notes:
            - ISR-safe: 否
        ==========================================
        Get current analog gain setting.
        Args:
            None
        Returns:
            str: Gain name (e.g. "GAIN_1X")
        Notes:
            - ISR-safe: No
        """
        gain_values = (
            "GAIN_5X", "GAIN_4X", "GAIN_3X", "GAIN_2_5X",
            "GAIN_2X", "GAIN_1_67X", "GAIN_1_33X", "GAIN_1X",
        )
        return gain_values[self._gain]

    @gain.setter
    def gain(self, value: int) -> None:
        if value not in range(0, 8):
            raise ValueError("gain must be in range 0~7, got %s" % value)
        self._gain = value

    @property
    def resolution_x(self) -> str:
        """
        获取 X 轴分辨率设置
        Args:
            无
        Returns:
            str: 分辨率名称（"RESOLUTION_0"~"RESOLUTION_3"）
        Notes:
            - ISR-safe: 否
        ==========================================
        Get X-axis resolution setting.
        Args:
            None
        Returns:
            str: Resolution name ("RESOLUTION_0"~"RESOLUTION_3")
        Notes:
            - ISR-safe: No
        """
        res_values = ("RESOLUTION_0", "RESOLUTION_1", "RESOLUTION_2", "RESOLUTION_3")
        return res_values[self._res_x]

    @resolution_x.setter
    def resolution_x(self, value: int) -> None:
        if value not in range(0, 4):
            raise ValueError("resolution_x must be in range 0~3, got %s" % value)
        self._res_x = value

    @property
    def resolution_y(self) -> str:
        """
        获取 Y 轴分辨率设置
        Args:
            无
        Returns:
            str: 分辨率名称（"RESOLUTION_0"~"RESOLUTION_3"）
        Notes:
            - ISR-safe: 否
        ==========================================
        Get Y-axis resolution setting.
        Args:
            None
        Returns:
            str: Resolution name ("RESOLUTION_0"~"RESOLUTION_3")
        Notes:
            - ISR-safe: No
        """
        res_values = ("RESOLUTION_0", "RESOLUTION_1", "RESOLUTION_2", "RESOLUTION_3")
        return res_values[self._res_y]

    @resolution_y.setter
    def resolution_y(self, value: int) -> None:
        if value not in range(0, 4):
            raise ValueError("resolution_y must be in range 0~3, got %s" % value)
        self._res_y = value

    @property
    def resolution_z(self) -> str:
        """
        获取 Z 轴分辨率设置
        Args:
            无
        Returns:
            str: 分辨率名称（"RESOLUTION_0"~"RESOLUTION_3"）
        Notes:
            - ISR-safe: 否
        ==========================================
        Get Z-axis resolution setting.
        Args:
            None
        Returns:
            str: Resolution name ("RESOLUTION_0"~"RESOLUTION_3")
        Notes:
            - ISR-safe: No
        """
        res_values = ("RESOLUTION_0", "RESOLUTION_1", "RESOLUTION_2", "RESOLUTION_3")
        return res_values[self._res_z]

    @resolution_z.setter
    def resolution_z(self, value: int) -> None:
        if value not in range(0, 4):
            raise ValueError("resolution_z must be in range 0~3, got %s" % value)
        self._res_z = value

    @property
    def digital_filter(self) -> str:
        """
        获取数字滤波器设置
        Args:
            无
        Returns:
            str: 滤波器名称（"FILTER_0"~"FILTER_7"）
        Notes:
            - ISR-safe: 否
            - 滤波器与过采样共同决定转换时间，参见 TCONV 查找表
        ==========================================
        Get digital filter setting.
        Args:
            None
        Returns:
            str: Filter name ("FILTER_0"~"FILTER_7")
        Notes:
            - ISR-safe: No
            - Filter and oversampling together determine conversion time (see TCONV table)
        """
        digfilt_values = (
            "FILTER_0", "FILTER_1", "FILTER_2", "FILTER_3",
            "FILTER_4", "FILTER_5", "FILTER_6", "FILTER_7",
        )
        return digfilt_values[self._digfilt]

    @digital_filter.setter
    def digital_filter(self, value: int) -> None:
        if value not in range(0, 8):
            raise ValueError("digital_filter must be in range 0~7, got %s" % value)
        self._digfilt = value

    @property
    def oversampling(self) -> str:
        """
        获取过采样率设置
        Args:
            无
        Returns:
            str: 过采样名称（"OSR_0"~"OSR_3"）
        Notes:
            - ISR-safe: 否
            - 过采样与数字滤波器共同决定转换时间
        ==========================================
        Get oversampling ratio setting.
        Args:
            None
        Returns:
            str: Oversampling name ("OSR_0"~"OSR_3")
        Notes:
            - ISR-safe: No
            - Oversampling and digital filter together determine conversion time
        """
        oversampling_values = ("OSR_0", "OSR_1", "OSR_2", "OSR_3")
        return oversampling_values[self._oversampling]

    @oversampling.setter
    def oversampling(self, value: int) -> None:
        if value not in range(0, 4):
            raise ValueError("oversampling must be in range 0~3, got %s" % value)
        self._oversampling = value

    @property
    def magnetic(self) -> tuple:
        """
        读取三轴磁场值（微特斯拉）
        Args:
            无
        Returns:
            tuple: (x, y, z) 三轴磁场值，单位 µT，有符号浮点数
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：阻塞等待转换完成（时间由 TCONV[DIGFILT][OSR] 决定，最长约 200ms）
            - 每次调用均发送 SM 命令触发单次测量
        ==========================================
        Read three-axis magnetic field values in microteslas.
        Args:
            None
        Returns:
            tuple: (x, y, z) magnetic field values in µT, signed floats
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Blocks for conversion time (TCONV[DIGFILT][OSR], up to ~200ms)
            - Each call sends SM command to trigger a single measurement
        """
        # 根据当前 DIGFILT 和 OSR 计算转换等待时间（加 10% 余量），单位秒
        delay = self._TCONV[self._digfilt][self._oversampling] / 1000 * 1.1
        # 发送 SM 命令触发全轴单次测量
        payload = bytes([_CMD_SM | _CMD_AXIS_ALL])
        self._i2c.writeto(self._address, payload)
        data = self._i2c.readfrom(self._address, 1)
        self._status_last = data[0]
        # 等待转换完成
        time.sleep(delay)
        # 发送 RM 命令读取测量结果（7字节：1状态+2X+2Y+2Z）
        payload = bytes([_CMD_RM | _CMD_AXIS_ALL])
        self._i2c.writeto(self._address, payload)
        data2 = self._i2c.readfrom(self._address, 7)
        self._status_last = data2[0]
        # 解包各轴原始值
        x = self._unpack_axis_data(self._res_x, data2[1:3])
        y = self._unpack_axis_data(self._res_y, data2[3:5])
        z = self._unpack_axis_data(self._res_z, data2[5:7])
        # 根据 HALLCONF 选择灵敏度表索引（0x0C=12 对应 index 0，其他对应 index 1）
        hallconf_index = 0 if self._hall == 12 else 1
        # 乘以对应灵敏度系数转换为 µT
        x = x * self._resolutionsxy[self._res_x][hallconf_index][self._gain]
        y = y * self._resolutionsxy[self._res_y][hallconf_index][self._gain]
        z = z * self._resolutionsz[self._res_z][hallconf_index][self._gain]
        return x, y, z

    @staticmethod
    def _unpack_axis_data(resolution: int, data: bytes) -> int:
        """
        根据分辨率设置解包单轴原始数据
        Args:
            resolution (int): 分辨率常量（RESOLUTION_0~RESOLUTION_3）
            data (bytes): 2 字节原始数据（大端）
        Returns:
            int: 有符号整数原始值
        Notes:
            - ISR-safe: 是
            - RESOLUTION_3/2 使用无符号解包后减去偏置；RESOLUTION_1/0 使用有符号解包
        ==========================================
        Unpack single-axis raw data based on resolution setting.
        Args:
            resolution (int): Resolution constant (RESOLUTION_0~RESOLUTION_3)
            data (bytes): 2-byte raw data (big-endian)
        Returns:
            int: Signed integer raw value
        Notes:
            - ISR-safe: Yes
            - RESOLUTION_3/2 use unsigned unpack with offset; RESOLUTION_1/0 use signed unpack
        """
        if resolution == RESOLUTION_3:
            # 无符号解包，减去 0x4000 偏置
            (value,) = struct.unpack(">H", data)
            value -= 0x4000
        elif resolution == RESOLUTION_2:
            # 无符号解包，减去 0x8000 偏置
            (value,) = struct.unpack(">H", data)
            value -= 0x8000
        else:
            # 有符号解包
            value = struct.unpack(">h", data)[0]
        return value

    def deinit(self) -> None:
        """
        释放传感器资源
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 当前实现仅清除内部引用，不向硬件发送掉电命令
        ==========================================
        Release sensor resources.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Current implementation clears internal references only; no power-down command sent
        """
        self._i2c = None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
