# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/26 12:00
# @Author  : hogeiha
# @File    : t117b.py
# @Description : T117B I2C 温度传感器驱动，支持连续/单次测量、报警阈值配置
# @License : MIT

__version__ = "1.0.0"
__author__  = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
from machine import I2C
import micropython
import time

# ======================================== 全局变量 ============================================
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class T117:
    """
    T117B I2C 温度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _msb_first (bool): 阈值写入时是否先写 MSB
        _last_status (int): 上次读取的状态寄存器原始值
        _debug (bool): 调试日志开关
    Methods:
        get_temp(): 读取摄氏温度
        get_temp_raw(): 读取原始温度整数
        get_status(): 读取报警状态字典
        get_status_raw(): 读取状态寄存器原始值
        set_measure_mode(mode): 设置测量模式
        set_avg(avg): 设置平均次数
        set_mps(mps): 设置测量频率
        set_sleep(enable): 进入/退出睡眠
        set_alert_thresholds(th, tl): 设置报警阈值
        set_alert_config(enable, polarity, mode): 配置报警引脚
        enable_alerts(th, tl, ...): 一键完整报警初始化
        wait_conv_ready(ms): 等待转换完成
        soft_reset(): 软件复位
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 状态寄存器为读清除，get_temp_raw() 内部已读取
    ==========================================
    T117B I2C temperature sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _msb_first (bool): Whether to write MSB first for thresholds
        _last_status (int): Last raw status register value
        _debug (bool): Debug log flag
    Methods:
        get_temp(): Read temperature in Celsius
        get_temp_raw(): Read raw temperature integer
        get_status(): Read alert status dict
        get_status_raw(): Read raw status register
        set_measure_mode(mode): Set measurement mode
        set_avg(avg): Set averaging count
        set_mps(mps): Set measurement rate
        set_sleep(enable): Enter/exit sleep mode
        set_alert_thresholds(th, tl): Set alert thresholds
        set_alert_config(enable, polarity, mode): Configure alert pin
        enable_alerts(th, tl, ...): Full alert setup in one call
        wait_conv_ready(ms): Wait for conversion
        soft_reset(): Software reset
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Status register is read-clear; get_temp_raw() reads it internally
    """

    # 寄存器地址
    REG_TEMP_LSB      = micropython.const(0x00)
    REG_TEMP_MSB      = micropython.const(0x01)
    REG_CRC_TEMP      = micropython.const(0x02)
    REG_STATUS        = micropython.const(0x03)
    REG_TEMP_CMD      = micropython.const(0x04)
    REG_TEMP_CFG      = micropython.const(0x05)
    REG_ALERT_MODE    = micropython.const(0x06)
    REG_TH_LSB        = micropython.const(0x07)
    REG_TH_MSB        = micropython.const(0x08)
    REG_TL_LSB        = micropython.const(0x09)
    REG_TL_MSB        = micropython.const(0x0A)
    REG_USER_DEF_BASE = micropython.const(0x0C)
    REG_E2PROM_CMD    = micropython.const(0x17)
    REG_ROM_ID_BASE   = micropython.const(0x18)

    # I2C 地址选项
    ADDR_GND = micropython.const(0x40)
    ADDR_VDD = micropython.const(0x41)
    ADDR_SDA = micropython.const(0x42)
    ADDR_SCL = micropython.const(0x43)

    # 测量模式
    MEAS_STOP     = micropython.const(0b01000000)
    MEAS_CONTINUE = micropython.const(0b00000000)
    MEAS_SINGLE   = micropython.const(0b11000000)

    # 平均次数（位 3,4）
    AVG_1  = micropython.const(0b00)
    AVG_8  = micropython.const(0b01)
    AVG_16 = micropython.const(0b10)
    AVG_32 = micropython.const(0b11)

    # 测量频率 MPS（位 5,6,7）
    MPS_8S   = micropython.const(0b000)
    MPS_4S   = micropython.const(0b001)
    MPS_2S   = micropython.const(0b010)
    MPS_1S   = micropython.const(0b011)
    MPS_2_1  = micropython.const(0b100)
    MPS_4_1  = micropython.const(0b101)
    MPS_8_1  = micropython.const(0b110)
    MPS_16_1 = micropython.const(0b111)

    E2PROM_SOFT_RST = micropython.const(0x6A)

    def __init__(self, i2c: I2C, addr: int = ADDR_GND,
                 msb_first: bool = True, debug: bool = False) -> None:
        """
        初始化 T117B 驱动
        Args:
            i2c (I2C): 外部传入的 I2C 总线实例
            addr (int): 设备 I2C 地址，默认 ADDR_GND (0x40)
            msb_first (bool): 阈值寄存器写入顺序，True 表示先写 MSB
            debug (bool): 是否开启调试日志
        Returns:
            None
        Raises:
            ValueError: i2c 不是有效 I2C 实例，或 addr 超出范围
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize T117B driver.
        Args:
            i2c (I2C): Externally provided I2C bus instance
            addr (int): Device I2C address, default ADDR_GND (0x40)
            msb_first (bool): Threshold register write order; True = MSB first
            debug (bool): Enable debug logging
        Returns:
            None
        Raises:
            ValueError: i2c is not a valid I2C instance, or addr out of range
        Notes:
            - ISR-safe: No
        """
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(addr, int) or addr < 0x00 or addr > 0x7F:
            raise ValueError("addr must be a 7-bit int, got %s" % addr)
        if not isinstance(msb_first, bool):
            raise ValueError("msb_first must be bool")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._i2c = i2c
        self._addr = addr
        self._msb_first = msb_first
        self._last_status = 0
        self._debug = debug

    # -------------------- 公共方法 --------------------

    def wait_conv_ready(self, ms: int = 500) -> None:
        """
        等待转换完成（固定延时）
        Args:
            ms (int): 等待毫秒数，默认 500
        Returns:
            None
        Raises:
            ValueError: ms 不是正整数
        Notes:
            - ISR-safe: 否
            - 使用固定延时而非轮询，避免消耗读清除的报警位
        ==========================================
        Wait for conversion to complete (fixed delay).
        Args:
            ms (int): Wait duration in milliseconds, default 500
        Returns:
            None
        Raises:
            ValueError: ms is not a positive integer
        Notes:
            - ISR-safe: No
            - Uses fixed delay instead of polling to avoid consuming read-clear alert bits
        """
        if not isinstance(ms, int) or ms <= 0:
            raise ValueError("ms must be a positive int")
        time.sleep_ms(ms)

    def get_temp_raw(self) -> int:
        """
        读取原始温度寄存器值（有符号 16 位整数）
        Args:
            无
        Returns:
            int: 原始温度值（有符号）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 内部会读取状态寄存器（读清除），更新 _last_status
        ==========================================
        Read raw temperature register as signed 16-bit integer.
        Args:
            None
        Returns:
            int: Raw signed temperature value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Reads status register (read-clear) internally, updates _last_status
        """
        self.wait_conv_ready()
        # 读取 LSB 和 MSB 两字节温度数据
        data = self._read_words(self.REG_TEMP_LSB, 2)
        # 读取状态寄存器（读清除报警位）
        self._last_status = self._read_reg(self.REG_STATUS)
        raw = (data[1] << 8) | data[0]
        # 转换为有符号整数
        return raw - 65536 if raw >= 0x8000 else raw

    def get_temp(self) -> float:
        """
        读取摄氏温度值
        Args:
            无
        Returns:
            float: 温度值（℃），超出 -105~155℃ 范围时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read temperature in Celsius.
        Args:
            None
        Returns:
            float: Temperature in Celsius; None if out of -105~155 range
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        raw = self.get_temp_raw()
        # 公式：T = raw / 256 + 25
        temp = raw / 256.0 + 25.0
        return round(temp, 2) if -105 <= temp <= 155 else None

    def get_status_raw(self) -> int:
        """
        获取上次读取的状态寄存器原始值
        Args:
            无
        Returns:
            int: 状态寄存器原始字节
        Raises:
            无
        Notes:
            - ISR-safe: 是
            - 返回的是 get_temp_raw() 最后一次读取时缓存的值
        ==========================================
        Get last cached raw status register value.
        Args:
            None
        Returns:
            int: Raw status register byte
        Raises:
            None
        Notes:
            - ISR-safe: Yes
            - Returns value cached during the last get_temp_raw() call
        """
        return self._last_status

    def get_status(self) -> dict:
        """
        解析报警状态字典
        Args:
            无
        Returns:
            dict: 含 high_alert(int), low_alert(int), alert_err(int), raw(int)
        Raises:
            无
        Notes:
            - ISR-safe: 是
            - 位定义基于常见芯片推测，请打印 raw 值确认
        ==========================================
        Parse alert status into a dict.
        Args:
            None
        Returns:
            dict: Keys: high_alert(int), low_alert(int), alert_err(int), raw(int)
        Raises:
            None
        Notes:
            - ISR-safe: Yes
            - Bit definitions are inferred; verify by printing raw value
        """
        sta = self.get_status_raw()
        return {
            "high_alert": (sta >> 7) & 1,
            "low_alert":  (sta >> 6) & 1,
            "alert_err":  (sta >> 2) & 1,
            "raw":        sta,
        }

    def set_measure_mode(self, mode: int) -> None:
        """
        设置测量模式
        Args:
            mode (int): MEAS_CONTINUE / MEAS_SINGLE / MEAS_STOP
        Returns:
            None
        Raises:
            ValueError: mode 不是有效整数
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Set measurement mode.
        Args:
            mode (int): MEAS_CONTINUE / MEAS_SINGLE / MEAS_STOP
        Returns:
            None
        Raises:
            ValueError: mode is not a valid int
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        if not isinstance(mode, int):
            raise ValueError("mode must be int")
        self._write_reg(self.REG_TEMP_CMD, mode)

    def set_avg(self, avg: int) -> None:
        """
        设置平均次数（位 3,4）
        Args:
            avg (int): AVG_1 / AVG_8 / AVG_16 / AVG_32
        Returns:
            None
        Raises:
            ValueError: avg 不在 0~3 范围内
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Set averaging count (bits 3,4 of CFG register).
        Args:
            avg (int): AVG_1 / AVG_8 / AVG_16 / AVG_32
        Returns:
            None
        Raises:
            ValueError: avg not in 0~3
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        if not isinstance(avg, int) or avg < 0 or avg > 3:
            raise ValueError("avg must be 0~3, got %s" % avg)
        # 读-改-写：保留其他位，更新位 3,4
        cfg = self._read_reg(self.REG_TEMP_CFG) & 0b11100111 | ((avg & 0x03) << 3)
        self._write_reg(self.REG_TEMP_CFG, cfg)

    def set_mps(self, mps: int) -> None:
        """
        设置测量频率（位 5,6,7）
        Args:
            mps (int): MPS_8S / MPS_4S / ... / MPS_16_1
        Returns:
            None
        Raises:
            ValueError: mps 不在 0~7 范围内
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Set measurement rate (bits 5,6,7 of CFG register).
        Args:
            mps (int): MPS_8S / MPS_4S / ... / MPS_16_1
        Returns:
            None
        Raises:
            ValueError: mps not in 0~7
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        if not isinstance(mps, int) or mps < 0 or mps > 7:
            raise ValueError("mps must be 0~7, got %s" % mps)
        # 读-改-写：保留其他位，更新位 5,6,7
        cfg = self._read_reg(self.REG_TEMP_CFG) & 0b00011111 | ((mps & 0x07) << 5)
        self._write_reg(self.REG_TEMP_CFG, cfg)

    def set_sleep(self, enable: bool) -> None:
        """
        进入或退出睡眠模式（位 0）
        Args:
            enable (bool): True 进入睡眠，False 退出睡眠
        Returns:
            None
        Raises:
            ValueError: enable 不是 bool
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Enter or exit sleep mode (bit 0 of CFG register).
        Args:
            enable (bool): True to sleep, False to wake
        Returns:
            None
        Raises:
            ValueError: enable is not bool
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        if not isinstance(enable, bool):
            raise ValueError("enable must be bool")
        # 读-改-写：保留其他位，更新位 0
        cfg = self._read_reg(self.REG_TEMP_CFG) & 0xFE | (1 if enable else 0)
        self._write_reg(self.REG_TEMP_CFG, cfg)

    def set_alert_config(self, enable: bool, polarity: int = 0, mode: int = 0) -> None:
        """
        配置报警模式寄存器 (0x06)
        Args:
            enable (bool): 使能报警
            polarity (int): 0=低有效（开漏），1=高有效
            mode (int): 0=比较模式（实时跟随），1=中断模式（锁存）
        Returns:
            None
        Raises:
            ValueError: 参数类型或范围错误
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 写入后等待 5ms 生效
        ==========================================
        Configure alert mode register (0x06).
        Args:
            enable (bool): Enable alert
            polarity (int): 0=active-low (open-drain), 1=active-high
            mode (int): 0=comparator (real-time), 1=interrupt (latch)
        Returns:
            None
        Raises:
            ValueError: Parameter type or range error
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Waits 5ms after write for setting to take effect
        """
        if not isinstance(enable, bool):
            raise ValueError("enable must be bool")
        if not isinstance(polarity, int) or polarity not in (0, 1):
            raise ValueError("polarity must be 0 or 1")
        if not isinstance(mode, int) or mode not in (0, 1):
            raise ValueError("mode must be 0 or 1")
        val = (0x80 if enable else 0x00) | ((polarity & 1) << 6) | ((mode & 1) << 5)
        self._write_reg(self.REG_ALERT_MODE, val)
        time.sleep_ms(5)

    def set_alert_thresholds(self, th_temp: float, tl_temp: float) -> None:
        """
        设置高温/低温报警阈值
        Args:
            th_temp (float): 高温阈值（℃）
            tl_temp (float): 低温阈值（℃）
        Returns:
            None
        Raises:
            ValueError: 参数不是数值，或 th_temp <= tl_temp
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 转换公式：raw = (T - 25) * 256，钳位到 16 位有符号范围
            - 写入后等待 5ms 生效
        ==========================================
        Set high/low temperature alert thresholds.
        Args:
            th_temp (float): High temperature threshold (°C)
            tl_temp (float): Low temperature threshold (°C)
        Returns:
            None
        Raises:
            ValueError: Not numeric, or th_temp <= tl_temp
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Conversion: raw = (T - 25) * 256, clamped to signed 16-bit range
            - Waits 5ms after write
        """
        if not isinstance(th_temp, (int, float)):
            raise ValueError("th_temp must be numeric")
        if not isinstance(tl_temp, (int, float)):
            raise ValueError("tl_temp must be numeric")
        if th_temp <= tl_temp:
            raise ValueError("th_temp must be greater than tl_temp")
        # 转换为寄存器原始值并钳位
        th_raw = max(-32768, min(32767, int((th_temp - 25.0) * 256)))
        tl_raw = max(-32768, min(32767, int((tl_temp - 25.0) * 256)))
        if self._msb_first:
            # 先写 MSB 再写 LSB
            self._write_reg(self.REG_TH_MSB, (th_raw >> 8) & 0xFF)
            self._write_reg(self.REG_TH_LSB, th_raw & 0xFF)
            self._write_reg(self.REG_TL_MSB, (tl_raw >> 8) & 0xFF)
            self._write_reg(self.REG_TL_LSB, tl_raw & 0xFF)
        else:
            # 先写 LSB 再写 MSB
            self._write_reg(self.REG_TH_LSB, th_raw & 0xFF)
            self._write_reg(self.REG_TH_MSB, (th_raw >> 8) & 0xFF)
            self._write_reg(self.REG_TL_LSB, tl_raw & 0xFF)
            self._write_reg(self.REG_TL_MSB, (tl_raw >> 8) & 0xFF)
        time.sleep_ms(5)

    def enable_alerts(self, th_temp: float, tl_temp: float,
                      mps: int = MPS_8S, avg: int = AVG_8,
                      polarity: int = 0, mode: int = 0) -> None:
        """
        一键完整配置报警功能
        Args:
            th_temp (float): 高温阈值（℃）
            tl_temp (float): 低温阈值（℃）
            mps (int): 测量频率，默认 MPS_8S
            avg (int): 平均次数，默认 AVG_8
            polarity (int): 报警极性，0=低有效，1=高有效
            mode (int): 报警模式，0=比较，1=中断
        Returns:
            None
        Raises:
            ValueError: 参数错误
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 依次设置：连续测量→频率→平均→阈值→报警配置→退出睡眠
        ==========================================
        Full alert setup in one call.
        Args:
            th_temp (float): High temperature threshold (°C)
            tl_temp (float): Low temperature threshold (°C)
            mps (int): Measurement rate, default MPS_8S
            avg (int): Averaging count, default AVG_8
            polarity (int): Alert polarity, 0=active-low, 1=active-high
            mode (int): Alert mode, 0=comparator, 1=interrupt
        Returns:
            None
        Raises:
            ValueError: Parameter error
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Sequence: continuous→rate→avg→thresholds→alert config→wake
        """
        # 1. 设置连续测量模式
        self.set_measure_mode(self.MEAS_CONTINUE)
        # 2. 设置测量频率和平均次数
        self.set_mps(mps)
        self.set_avg(avg)
        # 3. 写入报警阈值
        self.set_alert_thresholds(th_temp, tl_temp)
        # 4. 配置报警引脚
        self.set_alert_config(enable=True, polarity=polarity, mode=mode)
        # 5. 退出睡眠，等待配置生效
        self.set_sleep(False)
        time.sleep_ms(10)

    def soft_reset(self) -> None:
        """
        软件复位（通过 E2PROM 命令寄存器）
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 复位后等待 100ms
        ==========================================
        Software reset via E2PROM command register.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Waits 100ms after reset
        """
        self._write_reg(self.REG_E2PROM_CMD, self.E2PROM_SOFT_RST)
        time.sleep_ms(100)

    def deinit(self) -> None:
        """
        释放驱动资源
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 将设备置于停止测量模式
        ==========================================
        Release driver resources.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Sets device to stop measurement mode
        """
        try:
            self.set_measure_mode(self.MEAS_STOP)
        except RuntimeError:
            pass

    # -------------------- 私有方法 --------------------

    def _read_reg(self, reg: int) -> int:
        """读取单字节寄存器"""
        try:
            return self._i2c.readfrom_mem(self._addr, reg, 1)[0]
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg) from e

    def _write_reg(self, reg: int, val: int) -> None:
        """写入单字节寄存器"""
        try:
            self._i2c.writeto_mem(self._addr, reg, bytes([val & 0xFF]))
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % reg) from e

    def _read_words(self, reg: int, length: int) -> bytes:
        """读取多字节数据"""
        try:
            return self._i2c.readfrom_mem(self._addr, reg, length)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg) from e

    def _log(self, msg: str) -> None:
        """调试日志输出"""
        if self._debug:
            print("[T117] %s" % msg)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
