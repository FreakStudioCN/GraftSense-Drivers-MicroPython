# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Andre Peeters
# @File    : max17048.py
# @Description : MAX17048/MAX17049 锂电池电量计 I2C 驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================
from micropython import const
from machine import I2C
import time

# ======================================== 全局变量 ============================================
__version__ = "1.0.1"
__author__ = "Andre Peeters"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# VCELL 寄存器地址（电池电压）
_REG_VCELL = const(0x02)
# SOC 寄存器地址（荷电状态）
_REG_SOC = const(0x04)
# MODE 寄存器地址（模式控制）
_REG_MODE = const(0x06)
# VERSION 寄存器地址（芯片版本）
_REG_VERSION = const(0x08)
# CONFIG 寄存器地址（配置）
_REG_CONFIG = const(0x0C)
# COMMAND 寄存器地址（命令）
_REG_COMMAND = const(0xFE)

# MAX17048/MAX17049 默认 I2C 地址
_MAX17048_DEFAULT_ADDR = const(0x36)

# I2C 通信复用缓冲区（2 字节）
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================
# 无独立功能函数，所有操作封装在类中


# ======================================== 自定义类 ============================================
class MAX17048:
    """
    MAX17048/MAX17049 锂电池电量计 I2C 驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        sensor_exists(): 检测设备是否存在
        address(): 获取 I2C 地址
        reset(): 复位设备
        getVCell(): 获取电池电压（V）
        getSoc(): 获取电池荷电状态（%）
        getVersion(): 获取芯片版本号
        getCompensateValue(): 获取补偿值
        getAlertThreshold(): 获取报警阈值
        setAlertThreshold(): 设置报警阈值
        inAlert(): 检查是否处于报警状态
        clearAlert(): 清除报警状态
        quickStart(): 快速启动设备
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建 I2C 总线
        - 支持 MAX17048（MAX17049）锂电池电量计芯片
        - 支持单节锂电池电压和荷电状态监测
    ==========================================
    MAX17048/MAX17049 LiPo fuel gauge I2C driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        sensor_exists(): Check if device is present on bus
        address(): Get I2C address
        reset(): Reset the device
        getVCell(): Get battery voltage in volts
        getSoc(): Get state of charge percentage
        getVersion(): Get chip version number
        getCompensateValue(): Get compensation value
        getAlertThreshold(): Get alert threshold
        setAlertThreshold(): Set alert threshold
        inAlert(): Check if device is in alert state
        clearAlert(): Clear alert state
        quickStart(): Quick start the device
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided I2C instance
        - Supports MAX17048/MAX17049 fuel gauge chips
        - Monitors single-cell LiPo voltage and state of charge
    """

    def __init__(self, i2c: I2C, addr: int = _MAX17048_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 MAX17048 电量计驱动
        Args:
            i2c (I2C): I2C 总线实例
            addr (int): 设备 I2C 地址，默认 0x36
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型错误
            RuntimeError: 设备未在 I2C 总线上找到
        Notes:
            - 构造函数会检测设备是否存在
            - ISR-safe: 否
        ==========================================
        Initialize MAX17048 fuel gauge driver.
        Args:
            i2c (I2C): I2C bus instance
            addr (int): Device I2C address, default 0x36
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: Device not found on I2C bus
        Notes:
            - Constructor checks device presence
            - ISR-safe: No
        """
        # 参数校验：检查 i2c 参数是否具备 I2C 接口
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：检查 addr 参数类型和值范围
        if not isinstance(addr, int):
            raise ValueError("addr must be int, got %s" % type(addr))
        if addr < 0 or addr > 0x7F:
            raise ValueError("addr must be 0~0x7F, got 0x%02X" % addr)
        # 参数校验：检查 debug 参数类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = addr
        self._debug = debug

        # 检测设备是否在 I2C 总线上
        if not self.sensor_exists():
            raise RuntimeError("MAX1704X sensor not found on I2C bus at 0x%02X" % addr)

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 _debug=True 时输出
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug=True
        """
        if self._debug:
            print("[MAX17048] %s" % msg)

    def sensor_exists(self) -> bool:
        """
        检测 MAX1704X 设备是否在 I2C 总线上
        Returns:
            bool: 设备存在返回 True，否则返回 False
        Notes:
            - 通过读取 VERSION 寄存器确认设备连接
            - ISR-safe: 否
        ==========================================
        Check if MAX1704X device is on I2C bus.
        Returns:
            bool: True if device found, False otherwise
        Notes:
            - Confirms connection by reading VERSION register
            - ISR-safe: No
        """
        try:
            # 尝试读取版本寄存器以确认设备连接
            self._i2c.readfrom_mem(self._addr, _REG_VERSION, 1)
            return True
        except OSError:
            return False

    def address(self) -> int:
        """
        获取设备 I2C 地址
        Returns:
            int: 设备 I2C 地址
        Notes:
            - ISR-safe: 是（仅读取实例变量）
        ==========================================
        Get device I2C address.
        Returns:
            int: Device I2C address
        Notes:
            - ISR-safe: Yes (reads instance variable only)
        """
        return self._addr

    def reset(self) -> None:
        """
        复位 MAX1704X 设备
        Notes:
            - 向 COMMAND 寄存器写入复位命令（0x5400）
            - ISR-safe: 否
        ==========================================
        Reset MAX1704X device.
        Notes:
            - Writes reset command (0x5400) to COMMAND register
            - ISR-safe: No
        """
        self._log("resetting device")
        # 写入复位命令到 COMMAND 寄存器
        self._write_register(_REG_COMMAND, b"\x54\x00")

    def getVCell(self) -> float:
        """
        获取电池电压
        Returns:
            float: 电池电压（V）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 读取 VCELL 寄存器并转换为电压值
            - ISR-safe: 否
        ==========================================
        Get battery voltage.
        Returns:
            float: Battery voltage in volts
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads VCELL register and converts to voltage
            - ISR-safe: No
        """
        # 读取 VCELL 寄存器原始数据
        buf = self._read_register(_REG_VCELL)
        # 高 12 位为电压值（单位 1.25mV），转换为 V
        return (buf[0] << 4 | buf[1] >> 4) * 0.00125

    def getSoc(self) -> float:
        """
        获取电池荷电状态（State of Charge）
        Returns:
            float: 荷电状态百分比（0.0~100.0）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 读取 SOC 寄存器并计算百分比
            - ISR-safe: 否
        ==========================================
        Get state of charge.
        Returns:
            float: State of charge percentage (0.0~100.0)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads SOC register and computes percentage
            - ISR-safe: No
        """
        # 读取 SOC 寄存器原始数据
        buf = self._read_register(_REG_SOC)
        # 整数部分 + 小数部分（低字节/256）
        return buf[0] + (buf[1] / 256.0)

    def getVersion(self) -> int:
        """
        获取 MAX1704X 芯片版本号
        Returns:
            int: 芯片版本号
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Get MAX1704X chip version.
        Returns:
            int: Chip version number
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        # 读取 VERSION 寄存器
        buf = self._read_register(_REG_VERSION)
        return (buf[0] << 8) | buf[1]

    def getCompensateValue(self) -> int:
        """
        获取补偿值
        Returns:
            int: 补偿值（CONFIG 寄存器高字节）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Get compensation value.
        Returns:
            int: Compensation value (CONFIG register high byte)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        # 返回 CONFIG 寄存器高字节
        return self._read_config_register()[0]

    def getAlertThreshold(self) -> int:
        """
        获取报警阈值
        Returns:
            int: 报警阈值百分比（0~32）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 从 CONFIG 寄存器低 5 位读取并转换
            - ISR-safe: 否
        ==========================================
        Get alert threshold.
        Returns:
            int: Alert threshold percentage (0~32)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Reads lower 5 bits of CONFIG register and converts
            - ISR-safe: No
        """
        # 读取 CONFIG 寄存器，提取低 5 位并转换为百分比
        return 32 - (self._read_config_register()[1] & 0x1F)

    def setAlertThreshold(self, threshold: int) -> None:
        """
        设置报警阈值
        Args:
            threshold (int): 报警阈值（0~32，32 表示禁用报警）
        Raises:
            ValueError: 参数类型错误或超出范围
            RuntimeError: I2C 通信失败
        Notes:
            - 修改 CONFIG 寄存器中的报警阈值位
            - 执行读-修改-写操作
            - ISR-safe: 否
        ==========================================
        Set alert threshold.
        Args:
            threshold (int): Alert threshold (0~32, 32 disables alert)
        Raises:
            ValueError: Invalid parameter type or out of range
            RuntimeError: I2C communication failed
        Notes:
            - Modifies alert threshold bits in CONFIG register
            - Performs read-modify-write operation
            - ISR-safe: No
        """
        # 参数校验：阈值类型检查
        if not isinstance(threshold, int):
            raise ValueError("threshold must be int, got %s" % type(threshold))
        # 参数校验：阈值范围检查
        if threshold < 0 or threshold > 32:
            raise ValueError("threshold must be 0~32, got %d" % threshold)

        # 计算寄存器值（32 - threshold），最大不超过 32
        _threshold = 32 - threshold if threshold < 32 else 32
        # 读取当前 CONFIG 寄存器值
        buf = self._read_config_register()
        # 修改低 5 位为新的阈值（保留高 3 位不变）
        buf[1] = (buf[1] & 0xE0) | _threshold
        # 写回 CONFIG 寄存器
        self._write_config_register(buf)
        self._log("alert threshold set to %d" % threshold)

    def inAlert(self) -> bool:
        """
        检查设备是否处于报警状态
        Returns:
            bool: 处于报警状态返回 True，否则返回 False
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 检查 CONFIG 寄存器 ALRT 位（bit 5）
            - ISR-safe: 否
        ==========================================
        Check if device is in alert state.
        Returns:
            bool: True if in alert state, False otherwise
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Checks ALRT bit (bit 5) of CONFIG register
            - ISR-safe: No
        """
        # 检查 CONFIG 寄存器的 ALRT 位（bit 5）
        return bool(self._read_config_register()[1] & 0x20)

    def clearAlert(self) -> None:
        """
        清除报警状态
        Notes:
            - 将 CONFIG 寄存器 ALRT 位写 0 以清除报警状态
            - ISR-safe: 否
        ==========================================
        Clear alert state.
        Notes:
            - Writes CONFIG.ALRT bit to 0 to clear alert state
            - ISR-safe: No
        """
        # 清除 CONFIG.ALRT(bit 5)，保留其他配置位
        buf = self._read_config_register()
        buf[1] &= ~0x20
        self._write_config_register(buf)
        self._log("alert cleared")

    def quickStart(self) -> None:
        """
        快速启动 MAX1704X 设备
        Notes:
            - 向 MODE 寄存器写入快速启动命令（0x4000）
            - 强制设备立即重新估算 SOC，跳过稳定等待时间
            - ISR-safe: 否
        ==========================================
        Quick start MAX1704X device.
        Notes:
            - Writes quick-start command (0x4000) to MODE register
            - Forces immediate SOC re-estimation, skipping stabilization wait
            - ISR-safe: No
        """
        self._log("quick starting")
        # 写入快速启动命令到 MODE 寄存器
        self._write_register(_REG_MODE, b"\x40\x00")

    def __str__(self) -> str:
        """
        返回设备状态字符串表示
        Returns:
            str: 设备状态信息
        Notes:
            - ISR-safe: 否（执行 I2C 读取）
        ==========================================
        Return string representation of device state.
        Returns:
            str: Device state information
        Notes:
            - ISR-safe: No (performs I2C reads)
        """
        rs = "The I2C address is %s\n" % self._addr
        rs += "The version is %s\n" % self.getVersion()
        rs += "VCell is %s V\n" % self.getVCell()
        rs += "Compensate value is %s\n" % self.getCompensateValue()
        rs += "The alert threshold is %s %%\n" % self.getAlertThreshold()
        rs += "Is it in alert? %s\n" % self.inAlert()
        return rs

    # ==================== 私有方法 ====================

    def _read_register(self, reg: int, retries: int = 2, delay_ms: int = 5) -> bytearray:
        """
        读取指定寄存器的 2 字节数据（带重试）
        Args:
            reg (int): 寄存器地址
            retries (int): I2C 重试次数，默认 2
            delay_ms (int): 重试间隔（ms），默认 5
        Returns:
            bytearray: 2 字节寄存器数据（复用全局缓冲区 _BUF2）
        Raises:
            RuntimeError: I2C 通信失败，已重试
        Notes:
            - ISR-safe: 否
            - 使用全局缓冲区 _BUF2 复用内存
        ==========================================
        Read 2 bytes from specified register with retry.
        Args:
            reg (int): Register address
            retries (int): I2C retry count, default 2
            delay_ms (int): Retry interval in ms, default 5
        Returns:
            bytearray: 2-byte register data (reuses global buffer _BUF2)
        Raises:
            RuntimeError: I2C communication failed after retries
        Notes:
            - ISR-safe: No
            - Reuses global buffer _BUF2 for memory efficiency
        """
        for attempt in range(retries + 1):
            try:
                # 使用 readfrom_mem_into 复用 _BUF2 缓冲区
                self._i2c.readfrom_mem_into(self._addr, reg, _BUF2)
                return _BUF2
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (reg, retries)) from e
                # 重试前短暂延时
                time.sleep_ms(delay_ms)

    def _read_config_register(self) -> bytearray:
        """
        读取 CONFIG 寄存器
        Returns:
            bytearray: 2 字节配置寄存器数据
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read CONFIG register.
        Returns:
            bytearray: 2-byte config register data
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._read_register(_REG_CONFIG)

    def _write_register(self, reg: int, buf: bytes, retries: int = 2, delay_ms: int = 5) -> None:
        """
        向指定寄存器写入数据（带重试）
        Args:
            reg (int): 寄存器地址
            buf (bytes): 写入数据（2 字节）
            retries (int): I2C 重试次数，默认 2
            delay_ms (int): 重试间隔（ms），默认 5
        Raises:
            RuntimeError: I2C 通信失败，已重试
        Notes:
            - ISR-safe: 否
        ==========================================
        Write data to specified register with retry.
        Args:
            reg (int): Register address
            buf (bytes): Data to write (2 bytes)
            retries (int): I2C retry count, default 2
            delay_ms (int): Retry interval in ms, default 5
        Raises:
            RuntimeError: I2C communication failed after retries
        Notes:
            - ISR-safe: No
        """
        for attempt in range(retries + 1):
            try:
                self._i2c.writeto_mem(self._addr, reg, buf)
                return
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (reg, retries)) from e
                # 重试前短暂延时
                time.sleep_ms(delay_ms)

    def _write_config_register(self, buf: bytearray) -> None:
        """
        写入 CONFIG 寄存器
        Args:
            buf (bytearray): 2 字节配置数据
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write to CONFIG register.
        Args:
            buf (bytearray): 2-byte config data
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self._write_register(_REG_CONFIG, buf)

    def deinit(self) -> None:
        """
        释放硬件资源
        关闭 I2C 外设，释放总线。
        Notes:
            - ISR-safe: 否
            - 调用后设备不可再使用
            - 若 I2C 总线被其他设备共享，调用后也会影响其他设备
        ==========================================
        Release hardware resources.
        Deinitializes the I2C peripheral and releases the bus.
        Notes:
            - ISR-safe: No
            - Device is unusable after calling
            - If I2C bus is shared, other devices will also be affected
        """
        self._log("deinitializing MAX17048")
        try:
            self._i2c.deinit()
        except OSError:
            pass


# 保留模块级别类名别名，兼容旧代码
max1704x = MAX17048

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
