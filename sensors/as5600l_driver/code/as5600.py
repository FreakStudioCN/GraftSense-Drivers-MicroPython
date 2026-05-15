# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/05/15 11:17
# @Author  : hogeiha
# @File    : as5600.py
# @Description : AS5600/AS5600L 12位磁性旋转编码器驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# I2C 总线类型用于注解
from machine import I2C
# 常量声明
from micropython import const

# ======================================== 全局变量 ============================================

# AS5600 默认 I2C 地址（AS5600=0x36，AS5600L=0x40）
AS5600_DEFAULT_ADDR = const(0x36)

# 寄存器地址定义
_REG_ZMCO      = const(0x00)
_REG_ZPOS      = const(0x01)
_REG_MPOS      = const(0x03)
_REG_MANG      = const(0x05)
_REG_CONF      = const(0x07)
_REG_RAWANGLE  = const(0x0C)
_REG_ANGLE     = const(0x0E)
_REG_AGC       = const(0x1A)
_REG_STATUS    = const(0x1B)
_REG_MAGNITUDE = const(0x1C)
_REG_BURN      = const(0xFF)

# 复用读取缓冲区，避免循环中频繁分配
_BUF1 = bytearray(1)
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class AS5600:
    """
    AS5600/AS5600L 12位磁性旋转编码器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        readwrite(register, firstbit, lastbit, *args): 通用寄存器位域读写
        zmco/zpos/mpos/mang(*args): 配置寄存器读写
        pm/hyst/outs/pwmf/sf/fth/watchdog(*args): CONF 寄存器位域读写
        rawangle()/angle(): 角度读取
        md()/ml()/mh(): 磁铁状态
        agc()/magnitude(): AGC 与磁场强度
        burn_angle()/burn_setting(): 烧录配置（不可逆）
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - burn 系列方法不可逆，调用前请确认
    ==========================================
    AS5600/AS5600L 12-bit magnetic rotary encoder driver class.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        readwrite(register, firstbit, lastbit, *args): Generic bit-field R/W
        zmco/zpos/mpos/mang(*args): Config register R/W
        pm/hyst/outs/pwmf/sf/fth/watchdog(*args): CONF bit-field R/W
        rawangle()/angle(): Angle read
        md()/ml()/mh(): Magnet status
        agc()/magnitude(): AGC and magnitude
        burn_angle()/burn_setting(): Burn config (irreversible)
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Burn methods are irreversible
    """

    __slots__ = ("_i2c", "_addr", "_debug")

    def __init__(self, i2c: I2C, device: int = AS5600_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 AS5600 编码器驱动
        Args:
            i2c (I2C): MicroPython I2C 实例
            device (int): 设备 I2C 地址（AS5600=0x36，AS5600L=0x40）
            debug (bool): 是否启用调试日志
        Returns:
            None
        Raises:
            ValueError: 参数类型或取值不合法
        Notes:
            - 副作用：保存 I2C 实例引用，不发起通信
            - ISR-safe: 否
        ==========================================
        Initialize AS5600 encoder driver.
        Args:
            i2c (I2C): MicroPython I2C instance
            device (int): Device I2C address (AS5600=0x36, AS5600L=0x40)
            debug (bool): Enable debug logging
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type or value
        Notes:
            - Side effect: stores I2C reference, no I/O performed
            - ISR-safe: No
        """
        # 校验 i2c 实例：非空且支持寄存器读写接口
        if i2c is None:
            raise ValueError("i2c must not be None")
        if not (hasattr(i2c, "readfrom_mem_into") and hasattr(i2c, "writeto_mem")):
            raise ValueError("i2c must be an I2C-like instance")
        # 校验设备地址类型与范围
        if not isinstance(device, int):
            raise ValueError("device must be int, got %s" % type(device))
        if device < 0x00 or device > 0x7F:
            raise ValueError("device must be 0x00~0x7F, got 0x%02X" % device)
        # 校验调试开关类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))
        # 保存为私有实例属性
        self._i2c = i2c
        self._addr = device
        self._debug = debug

    def _log(self, msg: str) -> None:
        """
        内部调试日志输出
        Args:
            msg (str): 日志内容
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Internal debug log output.
        """
        # 仅在 debug 开启时输出
        if self._debug:
            print("[AS5600] %s" % msg)

    def readwrite(self, register: int, firstbit: int, lastbit: int, *args) -> int:
        """
        通用寄存器位域读写
        Args:
            register (int): 寄存器地址（0~0xFF）
            firstbit (int): 位域高位（含），范围 0~15
            lastbit (int): 位域低位（含），范围 0~firstbit
            *args: 长度 0 表示读取，长度 1 表示写入新值（int）
        Returns:
            int: 读模式返回位域值；写模式返回写入值
        Raises:
            ValueError: 参数错误
            RuntimeError: I2C 通信失败
        Notes:
            - firstbit>7 时按 2 字节寄存器处理（大端拼接）
            - 副作用：写模式将修改寄存器
            - ISR-safe: 否
        ==========================================
        Generic register bit-field read/write.
        Args:
            register (int): Register address (0~0xFF)
            firstbit (int): MSB of bit-field (inclusive), 0~15
            lastbit (int): LSB of bit-field (inclusive), 0~firstbit
            *args: 0 args = read, 1 arg = write value (int)
        Returns:
            int: Bit-field value (read) or written value (write)
        Raises:
            ValueError: Invalid argument
            RuntimeError: I2C communication failure
        Notes:
            - When firstbit>7, treat as 2-byte register (big-endian)
            - Side effect: write mode modifies register
            - ISR-safe: No
        """
        # 校验寄存器地址范围
        if not isinstance(register, int) or register < 0 or register > 0xFF:
            raise ValueError("register must be int in 0~0xFF")
        # 校验位域参数
        if not isinstance(firstbit, int) or not isinstance(lastbit, int):
            raise ValueError("firstbit/lastbit must be int")
        if firstbit < 0 or firstbit > 15 or lastbit < 0 or lastbit > firstbit:
            raise ValueError("invalid bitfield: firstbit=%d, lastbit=%d" % (firstbit, lastbit))
        # 根据高位决定字节宽度
        byte_num = 2 if firstbit > 7 else 1
        # 计算位域宽度对应掩码
        width = firstbit - lastbit + 1
        field_mask = (1 << width) - 1
        # 选择对应缓冲区
        buf = _BUF2 if byte_num == 2 else _BUF1
        # 读取寄存器原值
        try:
            self._i2c.readfrom_mem_into(self._addr, register, buf)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % register) from e
        # 拼接为整数（大端：高字节在前）
        if byte_num == 2:
            oldvalue = (buf[0] << 8) | buf[1]
        else:
            oldvalue = buf[0]
        # 读模式：右移到 LSB 后取位域宽度
        if len(args) == 0:
            return (oldvalue >> lastbit) & field_mask
        # 写模式：参数校验
        if len(args) == 1:
            value = args[0]
            if not isinstance(value, int):
                raise ValueError("write value must be int, got %s" % type(value))
            if value < 0 or value > field_mask:
                raise ValueError("value out of bitfield range, max=%d" % field_mask)
            # 字节宽度对应的整数掩码
            byte_mask = (1 << (byte_num * 8)) - 1
            # 清空目标位域并写入新值
            hole = (~(field_mask << lastbit)) & byte_mask
            newvalue = (oldvalue & hole) | ((value & field_mask) << lastbit)
            # 打包字节（大端：高字节在前）
            if byte_num == 1:
                write_data = bytes([newvalue & 0xFF])
            else:
                write_data = bytes([(newvalue >> 8) & 0xFF, newvalue & 0xFF])
            # 写入寄存器
            try:
                self._i2c.writeto_mem(self._addr, register, write_data)
            except OSError as e:
                raise RuntimeError("I2C write failed at reg 0x%02X" % register) from e
            # 调试日志
            self._log("reg 0x%02X bits[%d:%d] <- %d" % (register, firstbit, lastbit, value))
            return value
        # 参数数量超出支持范围
        raise ValueError("only 0 (read) or 1 (write) extra arg supported")

    # 配置寄存器：ZMCO（写次数计数器，2 位只读位域）
    def zmco(self, *args) -> int:
        """
        读取 ZMCO 烧录次数计数
        Returns:
            int: 已烧录次数（0~3）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read ZMCO burn counter.
        """
        return self.readwrite(_REG_ZMCO, 1, 0, *args)

    def zpos(self, *args) -> int:
        """
        读写起始角度寄存器 ZPOS（12 位）
        Args:
            *args: 无参读取，1 参写入（0~4095）
        Returns:
            int: 当前 ZPOS
        ==========================================
        Read/write start position register ZPOS (12-bit).
        """
        return self.readwrite(_REG_ZPOS, 11, 0, *args)

    def mpos(self, *args) -> int:
        """
        读写终止角度寄存器 MPOS（12 位）
        ==========================================
        Read/write stop position register MPOS (12-bit).
        """
        return self.readwrite(_REG_MPOS, 11, 0, *args)

    def mang(self, *args) -> int:
        """
        读写最大角度寄存器 MANG（12 位）
        ==========================================
        Read/write max angle register MANG (12-bit).
        """
        return self.readwrite(_REG_MANG, 11, 0, *args)

    # CONF 寄存器位域（16 位寄存器，逐位访问）
    def pm(self, *args) -> int:
        """
        电源模式（PM[1:0]）：0=NOM，1=LPM1，2=LPM2，3=LPM3
        ==========================================
        Power mode bits PM[1:0].
        """
        return self.readwrite(_REG_CONF, 1, 0, *args)

    def hyst(self, *args) -> int:
        """
        滞回设置（HYST[1:0]）
        ==========================================
        Hysteresis bits HYST[1:0].
        """
        return self.readwrite(_REG_CONF, 3, 2, *args)

    def outs(self, *args) -> int:
        """
        输出阶段（OUTS[1:0]）：0=模拟全量程，1=模拟缩量程，2=PWM
        ==========================================
        Output stage bits OUTS[1:0].
        """
        return self.readwrite(_REG_CONF, 5, 4, *args)

    def pwmf(self, *args) -> int:
        """
        PWM 频率（PWMF[1:0]）
        ==========================================
        PWM frequency bits PWMF[1:0].
        """
        return self.readwrite(_REG_CONF, 7, 6, *args)

    def sf(self, *args) -> int:
        """
        慢滤波器（SF[1:0]）
        ==========================================
        Slow filter bits SF[1:0].
        """
        return self.readwrite(_REG_CONF, 9, 8, *args)

    def fth(self, *args) -> int:
        """
        快滤波阈值（FTH[2:0]）
        ==========================================
        Fast filter threshold bits FTH[2:0].
        """
        return self.readwrite(_REG_CONF, 12, 10, *args)

    def watchdog(self, *args) -> int:
        """
        看门狗使能（WD）
        ==========================================
        Watchdog enable bit WD.
        """
        return self.readwrite(_REG_CONF, 13, 13, *args)

    # 角度寄存器（只读）
    def rawangle(self) -> int:
        """
        读取原始角度（未经映射，0~4095）
        Returns:
            int: 原始 12 位角度
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw angle (12-bit, 0~4095).
        """
        return self.readwrite(_REG_RAWANGLE, 11, 0)

    def angle(self) -> int:
        """
        读取经 ZPOS/MPOS/MANG 映射后的角度（0~4095）
        Returns:
            int: 映射后 12 位角度
        ==========================================
        Read mapped angle (12-bit, 0~4095).
        """
        return self.readwrite(_REG_ANGLE, 11, 0)

    # 状态寄存器（只读位）
    def md(self) -> int:
        """
        磁铁检测状态（1=检测到）
        ==========================================
        Magnet detected flag (1=present).
        """
        return self.readwrite(_REG_STATUS, 5, 5)

    def ml(self) -> int:
        """
        磁铁过弱标志（1=过弱）
        ==========================================
        Magnet too weak flag.
        """
        return self.readwrite(_REG_STATUS, 4, 4)

    def mh(self) -> int:
        """
        磁铁过强标志（1=过强）
        ==========================================
        Magnet too strong flag.
        """
        return self.readwrite(_REG_STATUS, 3, 3)

    def agc(self) -> int:
        """
        读取自动增益控制值（0~255）
        ==========================================
        Read AGC value (0~255).
        """
        return self.readwrite(_REG_AGC, 7, 0)

    def magnitude(self) -> int:
        """
        读取 CORDIC 磁场强度（12 位）
        ==========================================
        Read CORDIC magnitude (12-bit).
        """
        return self.readwrite(_REG_MAGNITUDE, 11, 0)

    def burn_angle(self) -> None:
        """
        烧录角度（ZPOS/MPOS）到 OTP，不可逆
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：永久修改 OTP，不可撤销
            - 数据手册推荐值为 0x80，此处沿用原驱动 0x08，使用前请按手册自行确认
            - ISR-safe: 否
        ==========================================
        Burn angle (ZPOS/MPOS) to OTP. Irreversible.
        """
        self.readwrite(_REG_BURN, 7, 0, 0x08)

    def burn_setting(self) -> None:
        """
        烧录配置（MANG/CONF）到 OTP，不可逆
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：永久修改 OTP，不可撤销
            - 数据手册推荐值为 0x40，此处沿用原驱动 0x04，使用前请按手册自行确认
            - ISR-safe: 否
        ==========================================
        Burn settings (MANG/CONF) to OTP. Irreversible.
        """
        self.readwrite(_REG_BURN, 7, 0, 0x04)

    def deinit(self) -> None:
        """
        释放驱动持有的资源引用
        Returns:
            None
        Notes:
            - 不关闭外部 I2C 总线（由调用方管理）
            - ISR-safe: 否
        ==========================================
        Release resource references held by the driver.
        Notes:
            - Does not close the external I2C bus
        """
        # 解除对外部 I2C 实例的引用
        self._i2c = None

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
