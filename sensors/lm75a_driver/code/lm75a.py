# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31
# @Author  : Mike Causer
# @File    : lm75a.py
# @Description : LM75A 数字温度传感器 I2C 驱动
# @License : MIT

__version__ = "0.0.3"
__author__ = "Mike Causer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import I2C

# ======================================== 全局变量 ============================================

# 模块级 I2C 读写复用缓冲区，避免频繁内存分配
_BUF1 = bytearray(1)
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================


def _twos_comp(val: int, bits: int) -> int:
    """
    二进制补码转换：将有符号整数的二进制补码表示转换为十进制值
    Args:
        val (int): 原始二进制值
        bits (int): 有效位数
    Returns:
        int: 转换后的有符号整数值
    ==========================================
    Two's complement conversion.
    Args:
        val (int): Raw binary value
        bits (int): Number of significant bits
    Returns:
        int: Signed integer value
    """
    mask = 2 ** (bits - 1)
    return -(val & mask) + (val & ~mask)


def _rev_twos_comp(val: int, bits: int) -> int:
    """
    反向补码转换：将有符号整数值转换为指定位宽的二进制补码表示
    Args:
        val (int): 有符号整数值
        bits (int): 目标位宽
    Returns:
        int: 二进制补码表示（无符号）
    ==========================================
    Reverse two's complement conversion.
    Args:
        val (int): Signed integer value
        bits (int): Target bit width
    Returns:
        int: Unsigned two's complement representation
    """
    return val & ((1 << bits) - 1)


# ======================================== 自定义类 ============================================


class LM75A:
    """
    LM75A 数字温度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _config (int): 当前配置寄存器值
        _debug (bool): 调试日志开关
    Methods:
        check(): 验证设备是否在 I2C 总线上
        config(): 读写配置寄存器
        temp(): 读取温度值
        tos(temp): 设置过热关断阈值
        thyst(temp): 设置迟滞阈值
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 温度分辨率 0.125°C，阈值分辨率 0.5°C
        - I2C 地址范围 0x48-0x4F（A2/A1/A0 引脚选择）
    ==========================================
    LM75A digital temperature sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _config (int): Current configuration register value
        _debug (bool): Debug log switch
    Methods:
        check(): Verify device presence on I2C bus
        config(): Read/write configuration register
        temp(): Read temperature value
        tos(temp): Set overtemperature shutdown threshold
        thyst(temp): Set hysteresis threshold
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Temperature resolution 0.125°C, threshold resolution 0.5°C
        - I2C address range 0x48-0x4F (selected by A2/A1/A0 pins)
    """

    # 寄存器地址
    _REG_TEMP = 0x00
    _REG_CONF = 0x01
    _REG_THYST = 0x02
    _REG_TOS = 0x03

    # 默认 I2C 地址（A2=A1=A0=0）
    _DEFAULT_ADDR = 0x48

    # 温度范围（°C）
    _TEMP_MIN = -55
    _TEMP_MAX = 125

    __slots__ = ("_i2c", "_addr", "_config", "_debug")

    def __init__(self, i2c: I2C, address: int = _DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 LM75A 传感器
        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x48
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型或值无效
            RuntimeError: 设备未在 I2C 总线上找到
        Notes:
            - 构造函数中自动调用 check() 验证设备存在
            - 构造函数中自动调用 config() 读取当前配置
            - 副作用: 执行 I2C 总线扫描和寄存器读取
        ==========================================
        Initialize LM75A sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x48
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type or value
            RuntimeError: Device not found on I2C bus
        Notes:
            - Automatically calls check() to verify device presence
            - Automatically calls config() to read current configuration
            - Side effects: Performs I2C bus scan and register read
        """
        # 参数校验：i2c 必须支持 I2C 协议方法
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：address 类型和范围
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0x48 or address > 0x4F:
            raise ValueError("address must be 0x48~0x4F, got 0x%02X" % address)
        # 参数校验：debug 类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = address
        self._config = 0x00
        self._debug = debug

        # 启动时验证设备存在
        self.check()
        # 读取当前配置寄存器
        self.config()

    def _log(self, msg: str) -> None:
        """
        输出调试日志
        Args:
            msg (str): 日志消息
        Notes:
            - 仅在 _debug 为 True 时输出
            - ISR-safe: 否
        ==========================================
        Output debug log.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug is True
            - ISR-safe: No
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str, got %s" % type(msg))
        if self._debug:
            print("[LM75A] %s" % msg)

    def check(self) -> None:
        """
        检查设备是否在 I2C 总线上存在
        Raises:
            RuntimeError: 设备未找到
        Notes:
            - ISR-safe: 否
            - 副作用: 执行 I2C 总线扫描
        ==========================================
        Verify device presence on I2C bus.
        Raises:
            RuntimeError: Device not found
        Notes:
            - ISR-safe: No
            - Side effects: Performs I2C bus scan
        """
        self._log("checking device at 0x%02X" % self._addr)
        # 扫描 I2C 总线，检查目标地址是否在响应列表中
        if self._i2c.scan().count(self._addr) == 0:
            raise RuntimeError("LM75A not found at I2C address 0x%02X" % self._addr)

    def config(
        self,
        shutdown: int = None,
        os_mode: int = None,
        os_polarity: int = None,
        os_fault_queue: int = None,
    ) -> None:
        """
        读写配置寄存器
        Args:
            shutdown (int): 关机模式，0=正常 1=关机
            os_mode (int): OS 模式，0=比较器 1=中断
            os_polarity (int): OS 极性，0=低有效 1=高有效
            os_fault_queue (int): 故障队列，0=1次 1=2次 2=4次 3=6次
        Raises:
            ValueError: 参数值无效
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 写入配置寄存器，修改硬件行为
            - 不传参数时仅读取当前配置（不执行 I2C 写入）
        ==========================================
        Read/write configuration register.
        Args:
            shutdown (int): Shutdown mode, 0=normal 1=shutdown
            os_mode (int): OS mode, 0=comparator 1=interrupt
            os_polarity (int): OS polarity, 0=active low 1=active high
            os_fault_queue (int): Fault queue, 0=1 1=2 2=4 3=6 faults
        Raises:
            ValueError: Invalid parameter value
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes configuration register, modifies hardware behavior
            - Without parameters, only reads current config (no I2C write)
        """
        # 位掩码修改各配置字段
        if shutdown is not None:
            if shutdown not in (0, 1):
                raise ValueError("shutdown must be 0 or 1")
            self._config = (self._config & ~1) | (shutdown & 1)

        if os_mode is not None:
            if os_mode not in (0, 1):
                raise ValueError("os_mode must be 0 or 1")
            self._config = (self._config & ~2) | ((os_mode << 1) & 2)

        if os_polarity is not None:
            if os_polarity not in (0, 1):
                raise ValueError("os_polarity must be 0 or 1")
            self._config = (self._config & ~4) | ((os_polarity << 2) & 4)

        if os_fault_queue is not None:
            if os_fault_queue not in (0, 1, 2, 3):
                raise ValueError("os_fault_queue must be 0~3")
            self._config = (self._config & ~24) | ((os_fault_queue << 3) & 24)

        # 将配置写入寄存器
        _BUF1[0] = self._config
        try:
            self._i2c.writeto_mem(self._addr, self._REG_CONF, _BUF1)
        except OSError as e:
            raise RuntimeError("I2C write failed at config register") from e
        self._log("config written: 0x%02X" % self._config)

    def temp(self) -> float:
        """
        读取温度值
        Returns:
            float: 温度值（°C），分辨率 0.125°C
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 执行 I2C 总线读取
        ==========================================
        Read temperature value.
        Returns:
            float: Temperature in Celsius, resolution 0.125°C
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Performs I2C bus read
        """
        # 读取 16 位温度寄存器
        try:
            self._i2c.readfrom_mem_into(self._addr, self._REG_TEMP, _BUF2)
        except OSError as e:
            raise RuntimeError("I2C read failed at temp register") from e

        # 温度数据为 11 位（高 8 位 + 低 3 位），对齐到 MSB
        val = (_BUF2[0] << 3) | (_BUF2[1] >> 5)
        # 补码转换后乘以分辨率 0.125°C
        temp_val = _twos_comp(val, 11) * 0.125
        self._log("temp: %.2f C" % temp_val)
        return temp_val

    def tos(self, temp: float) -> None:
        """
        设置过热关断阈值（TOS）
        Args:
            temp (float): 阈值温度（°C），范围 -55.0 ~ 125.0，分辨率 0.5°C
        Raises:
            ValueError: 温度值超出范围或类型无效
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 写入 TOS 寄存器
            - 温度值自动舍入到最近的 0.5°C 整数倍
        ==========================================
        Set overtemperature shutdown threshold (TOS).
        Args:
            temp (float): Threshold temperature (°C), range -55.0 ~ 125.0, resolution 0.5°C
        Raises:
            ValueError: Temperature out of range or invalid type
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes TOS register
            - Temperature is rounded to nearest 0.5°C increment
        """
        # 参数校验
        if isinstance(temp, (int, float)) is False:
            raise ValueError("temp must be int or float, got %s" % type(temp))
        if temp < self._TEMP_MIN or temp > self._TEMP_MAX:
            raise ValueError("temp must be %d~%d, got %.1f" % (self._TEMP_MIN, self._TEMP_MAX, temp))

        self._log("setting TOS: %.1f C" % temp)
        # 将温度值转换为 9 位寄存器格式
        self._temp_to_9bit_reg(temp)
        try:
            self._i2c.writeto_mem(self._addr, self._REG_TOS, _BUF2)
        except OSError as e:
            raise RuntimeError("I2C write failed at TOS register") from e

    def thyst(self, temp: float) -> None:
        """
        设置迟滞阈值（THYST）
        Args:
            temp (float): 阈值温度（°C），范围 -55.0 ~ 125.0，分辨率 0.5°C
        Raises:
            ValueError: 温度值超出范围或类型无效
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 写入 THYST 寄存器
            - 温度值自动舍入到最近的 0.5°C 整数倍
        ==========================================
        Set hysteresis threshold (THYST).
        Args:
            temp (float): Threshold temperature (°C), range -55.0 ~ 125.0, resolution 0.5°C
        Raises:
            ValueError: Temperature out of range or invalid type
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes THYST register
            - Temperature is rounded to nearest 0.5°C increment
        """
        # 参数校验
        if isinstance(temp, (int, float)) is False:
            raise ValueError("temp must be int or float, got %s" % type(temp))
        if temp < self._TEMP_MIN or temp > self._TEMP_MAX:
            raise ValueError("temp must be %d~%d, got %.1f" % (self._TEMP_MIN, self._TEMP_MAX, temp))

        self._log("setting THYST: %.1f C" % temp)
        # 将温度值转换为 9 位寄存器格式
        self._temp_to_9bit_reg(temp)
        try:
            self._i2c.writeto_mem(self._addr, self._REG_THYST, _BUF2)
        except OSError as e:
            raise RuntimeError("I2C write failed at THYST register") from e

    def deinit(self) -> None:
        """
        释放传感器资源
        Notes:
            - ISR-safe: 否
            - 副作用: 清除内部状态引用，不操作硬件总线（总线由调用者管理）
            - 调用后实例不可再使用
        ==========================================
        Release sensor resources.
        Notes:
            - ISR-safe: No
            - Side effects: Clears internal state references, does not touch hardware bus
            - Instance is unusable after this call
        """
        self._log("deinitializing")
        # 释放对总线实例的引用（总线生命周期由调用者管理）
        self._i2c = None
        self._config = 0x00
        self._debug = False

    def _temp_to_9bit_reg(self, temp: float) -> None:
        """
        将温度值转换为 9 位寄存器格式并写入全局 _BUF2
        Args:
            temp (float): 温度值（°C）
        Notes:
            - 内部方法，不对外暴露
            - 结果为 9 位补码格式，存储在模块级 _BUF2 中
            - 分辨率 0.5°C（temp / 0.5 取整）
        ==========================================
        Convert temperature to 9-bit register format and write to global _BUF2.
        Args:
            temp (float): Temperature in Celsius
        Notes:
            - Internal method
            - Result is 9-bit two's complement format stored in module-level _BUF2
            - Resolution 0.5°C (temp / 0.5 rounded to int)
        """
        if isinstance(temp, int) is False and isinstance(temp, float) is False:
            raise ValueError("temp must be int or float, got %s" % type(temp))
        # 将温度值除以分辨率 0.5 后取整，转换为 9 位补码
        val = _rev_twos_comp(int(temp / 0.5), 9)
        # 高 8 位放入 _BUF2[0]，最低位左移到 _BUF2[1] 的 MSB
        _BUF2[0] = val >> 1
        _BUF2[1] = val << 7


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
