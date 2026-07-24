# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : Chris Balmer
# @File    : si7021.py
# @Description : Si7021 温湿度传感器 I2C 驱动，支持温度/湿度读取、CRC 校验、设备识别
# @License : MIT

__version__ = "1.0.0"
__author__ = "Chris Balmer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

import micropython
from time import sleep

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================
_BUF3 = bytearray(3)  # I2C 温湿度读取复用缓冲区（3 字节：MSB + LSB + CRC）

# ======================================== 功能函数 ============================================


class CRCError(Exception):
    """
    Si7021 CRC-8 校验失败异常
    ==========================================
    Raised when the CRC-8 checksum verification fails for data read from Si7021.
    """

    pass


def _crc8_si7021(data: bytearray) -> bool:
    """
    使用 Si7021 多项式 (x8 + x5 + x4 + 1 = 0x131) 对数据执行 CRC-8 校验
    Args:
        data (bytearray): 待校验的 3 字节数据 [MSB, LSB, CRC]
    Returns:
        bool: True 表示校验通过，False 表示失败
    Notes:
        - 此函数为无副作用的纯计算，不涉及硬件访问
    ==========================================
    Verify CRC-8 checksum using Si7021 polynomial (x8 + x5 + x4 + 1 = 0x131).
    Args:
        data (bytearray): 3-byte data [MSB, LSB, CRC]
    Returns:
        bool: True if checksum passes, False otherwise
    Notes:
        - Pure computation, no hardware access
    """
    crc = 0
    # 仅对前 2 字节（数据部分）计算 CRC
    for value in data[:2]:
        crc = crc ^ value
        # 逐位处理，多项式为 0x131 (x8 + x5 + x4 + 1)
        for _ in range(8):
            if crc & 0x80:  # 最高位为 1 时异或多项式
                crc = (crc << 1) ^ 0x131
            else:
                crc <<= 1
            crc &= 0xFF  # 保持 8 位
    checksum = data[2]
    return crc == checksum


def _bytes_to_int(data: bytearray) -> int:
    """
    将字节数组按大端序转换为整数
    Args:
        data (bytearray): 待转换的字节数组
    Returns:
        int: 转换后的整数值
    Notes:
        - 无副作用纯函数
    ==========================================
    Convert bytearray to integer in big-endian order.
    Args:
        data (bytearray): Byte array to convert
    Returns:
        int: Converted integer value
    Notes:
        - Pure function, no side effects
    """
    result = 0
    for byte_val in data:
        result = (result << 8) | byte_val
    return result


def _device_identifier(byte_val: int) -> str:
    """
    根据芯片标识字节解析设备型号（参考数据手册第 24 页）
    Args:
        byte_val (int): 设备标识字节
    Returns:
        str: 设备型号字符串
    Notes:
        - 无副作用纯函数
    ==========================================
    Parse device model from identifier byte (ref. datasheet page 24).
    Args:
        byte_val (int): Device identifier byte
    Returns:
        str: Device model string
    Notes:
        - Pure function, no side effects
    """
    _DEVICE_MAP = {
        0x00: "engineering sample",
        0xFF: "engineering sample",
        0x0D: "Si7013",
        0x14: "Si7020",
        0x15: "Si7021",
    }
    return _DEVICE_MAP.get(byte_val, "unknown")


def convert_celcius_to_fahrenheit(celcius: float) -> float:
    """
    摄氏度转华氏度
    Args:
        celcius (float): 摄氏温度值（℃）
    Returns:
        float: 华氏温度值（℉）
    Notes:
        - 无副作用纯函数
    ==========================================
    Convert Celsius to Fahrenheit.
    Args:
        celcius (float): Temperature in Celsius
    Returns:
        float: Temperature in Fahrenheit
    Notes:
        - Pure function, no side effects
    """
    return celcius * 1.8 + 32


# ======================================== 自定义类 ============================================


class Si7021:
    """
    Si7021 温湿度传感器 I2C 驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例（外部注入）
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
        serial (int): 芯片唯一序列号
        identifier (str): 设备型号标识
    Methods:
        reset(): 软复位传感器
        temperature: 读取温度（℃），read-only property
        relative_humidity: 读取相对湿度（%），read-only property
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在类内创建总线对象
        - 每次访问 temperature/relative_humidity 均触发硬件读取，不做缓存
        - CRC 校验失败时抛出 CRCError
    ==========================================
    Si7021 I2C temperature and humidity sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance (externally injected)
        _addr (int): Device I2C address
        _debug (bool): Debug log switch
        serial (int): Chip unique serial number
        identifier (str): Device model identifier
    Methods:
        reset(): Soft-reset the sensor
        temperature: Read temperature (Celsius), read-only property
        relative_humidity: Read relative humidity (%), read-only property
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Each access to temperature/relative_humidity triggers a hardware read
        - CRCError raised on checksum failure
    """

    # 类级常量 — 用 micropython.const() 固化
    _DEFAULT_ADDR = micropython.const(0x40)

    _CMD_MEAS_TEMP_NOHOLD = micropython.const(0xF3)
    _CMD_MEAS_RH_NOHOLD = micropython.const(0xF5)
    _CMD_RESET = micropython.const(0xFE)
    _CMD_ID1 = micropython.const(0xFA)
    _CMD_ID1_ARG = micropython.const(0x0F)
    _CMD_ID2 = micropython.const(0xFC)
    _CMD_ID2_ARG = micropython.const(0xC9)

    # 温度转换公式常量（数据手册公式）
    _TEMP_SLOPE = micropython.const(17572)  # 175.72 * 100，整数化避免浮点误差累积
    _TEMP_OFFSET = micropython.const(4685)  # 46.85 * 100
    _TEMP_SCALE = micropython.const(65536)
    _TEMP_SCALE_100 = micropython.const(6553600)  # 65536 * 100，配合整数运算

    # 湿度转换公式常量
    _RH_SLOPE = micropython.const(12500)  # 125 * 100
    _RH_OFFSET = micropython.const(600)  # 6 * 100
    _RH_SCALE = micropython.const(65536)
    _RH_SCALE_100 = micropython.const(6553600)  # 65536 * 100

    # I2C 通信延时（数据手册要求最大转换时间约 10-12ms，25ms 含安全余量）
    _I2C_DELAY_MS = micropython.const(25)

    def __init__(self, i2c, address: int = _DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 Si7021 传感器实例
        Args:
            i2c (I2C): MicroPython I2C 总线实例（外部创建并注入）
            address (int): 传感器 I2C 地址，默认 0x40
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: i2c 参数无效时抛出
            RuntimeError: 读取设备信息失败时抛出
        Notes:
            - 初始化过程中会读取芯片序列号和型号标识
            - 副作用：通过 I2C 总线与传感器通信
        ==========================================
        Initialize Si7021 sensor instance.
        Args:
            i2c (I2C): MicroPython I2C bus instance (externally created)
            address (int): Sensor I2C address, default 0x40
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: If i2c parameter is invalid
            RuntimeError: If reading device info fails
        Notes:
            - Reads chip serial number and model identifier during init
            - Side effect: Communicates with sensor via I2C bus
        """
        # 参数校验：i2c 必须具有 I2C 接口方法
        if hasattr(i2c, "writeto") and hasattr(i2c, "readfrom_into"):
            pass
        else:
            raise ValueError("i2c must be an I2C instance with writeto/readfrom_into")
        # 参数校验：地址范围检查（7 位 I2C 地址）
        if isinstance(address, int) and 0x08 <= address <= 0x77:
            pass
        else:
            raise ValueError("address must be int in range 0x08~0x77, got %s" % address)
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = address
        self._debug = debug

        # 预声明所有实例属性（P0#9）
        self.serial = 0
        self.identifier = ""

        # 读取设备信息
        try:
            self.serial, self.identifier = self._read_device_info()
        except Exception:
            raise  # 已在 _read_device_info 中包装

        self._log("Si7021 initialized, serial=%d, id=%s" % (self.serial, self.identifier))

    # ==================== 公共方法 ====================

    def reset(self) -> None:
        """
        软复位传感器，将内部寄存器恢复为默认值
        Raises:
            RuntimeError: I2C 通信失败时抛出
        Notes:
            - 副作用：发送复位命令到传感器，需等待 25ms 后传感器才可响应
            - ISR-safe: 否
        ==========================================
        Soft-reset the sensor, restoring registers to defaults.
        Raises:
            RuntimeError: If I2C communication fails
        Notes:
            - Side effect: Sends reset command, sensor needs 25ms before responding
            - ISR-safe: No
        """
        self._log("resetting sensor")
        self._write_cmd(self._CMD_RESET)
        sleep(self._I2C_DELAY_MS / 1000.0)

    # ==================== Property ====================

    @property
    def temperature(self) -> float:
        """
        读取当前温度值（℃）
        Returns:
            float: 温度值，单位摄氏度
        Raises:
            CRCError: CRC 校验失败时抛出
            RuntimeError: I2C 通信失败时抛出
        Notes:
            - 每次访问均触发硬件测量（No Hold Master Mode）
            - 副作用：通过 I2C 总线发起测量并读取结果
            - ISR-safe: 否
        ==========================================
        Read current temperature in Celsius.
        Returns:
            float: Temperature in Celsius
        Raises:
            CRCError: If CRC check fails
            RuntimeError: If I2C communication fails
        Notes:
            - Each access triggers a hardware measurement (No Hold Master Mode)
            - Side effect: Initiates measurement and reads result via I2C
            - ISR-safe: No
        """
        raw = self._read_measurement(self._CMD_MEAS_TEMP_NOHOLD)
        # 温度转换公式：T = (raw * 175.72 / 65536) - 46.85
        return raw * 175.72 / 65536.0 - 46.85

    @temperature.setter
    def temperature(self, value) -> None:
        """
        温度属性为只读，禁止直接赋值
        Raises:
            AttributeError: 始终抛出
        ==========================================
        Temperature is read-only, setting is not allowed.
        Raises:
            AttributeError: Always raised
        """
        if isinstance(value, int) is False:
            raise ValueError("value must be int")
        raise AttributeError("temperature is read-only")

    @property
    def relative_humidity(self) -> float:
        """
        读取当前相对湿度值（%RH）
        Returns:
            float: 相对湿度百分比（如 35.6 表示 35.6%RH）
        Raises:
            CRCError: CRC 校验失败时抛出
            RuntimeError: I2C 通信失败时抛出
        Notes:
            - 每次访问均触发硬件测量（No Hold Master Mode）
            - 副作用：通过 I2C 总线发起测量并读取结果
            - ISR-safe: 否
        ==========================================
        Read current relative humidity in %RH.
        Returns:
            float: Relative humidity percentage (e.g., 35.6 = 35.6%RH)
        Raises:
            CRCError: If CRC check fails
            RuntimeError: If I2C communication fails
        Notes:
            - Each access triggers a hardware measurement (No Hold Master Mode)
            - Side effect: Initiates measurement and reads result via I2C
            - ISR-safe: No
        """
        raw = self._read_measurement(self._CMD_MEAS_RH_NOHOLD)
        # 湿度转换公式：RH = (raw * 125 / 65536) - 6
        return raw * 125.0 / 65536.0 - 6.0

    @relative_humidity.setter
    def relative_humidity(self, value) -> None:
        """
        湿度属性为只读，禁止直接赋值
        Raises:
            AttributeError: 始终抛出
        ==========================================
        Relative humidity is read-only, setting is not allowed.
        Raises:
            AttributeError: Always raised
        """
        if isinstance(value, int) is False:
            raise ValueError("value must be int")
        raise AttributeError("relative_humidity is read-only")

    # ==================== 私有方法 ====================

    def _write_cmd(self, cmd: int) -> None:
        """
        通过 I2C 总线发送单字节命令
        Args:
            cmd (int): 命令字节
        Raises:
            RuntimeError: I2C 写入失败时抛出
        Notes:
            - 副作用：通过 I2C 总线写入数据
            - ISR-safe: 否
        ==========================================
        Send a single-byte command via I2C bus.
        Args:
            cmd (int): Command byte
        Raises:
            RuntimeError: If I2C write fails
        Notes:
            - Side effect: Writes data via I2C bus
            - ISR-safe: No
        """
        if not isinstance(cmd, int) or not 0 <= cmd <= 0xFFFF:
            raise ValueError("cmd must be an integer command value")
        try:
            self._i2c.writeto(self._addr, bytes([cmd]))
        except OSError as e:
            raise RuntimeError("I2C write cmd 0x%02X failed" % cmd) from e

    def _write_cmd_buf(self, buf: bytearray) -> None:
        """
        通过 I2C 总线发送多字节命令序列
        Args:
            buf (bytearray): 命令字节序列
        Raises:
            RuntimeError: I2C 写入失败时抛出
        ==========================================
        Send a multi-byte command sequence via I2C bus.
        Args:
            buf (bytearray): Command byte sequence
        Raises:
            RuntimeError: If I2C write fails
        """
        if isinstance(buf, (bytes, bytearray, list, tuple)) is False:
            raise ValueError("buf must be a buffer or sequence")
        try:
            self._i2c.writeto(self._addr, buf)
        except OSError as e:
            raise RuntimeError("I2C write cmd buf failed") from e

    def _read_measurement(self, cmd: int) -> int:
        """
        发送测量命令并读取 3 字节结果（MSB + LSB + CRC），经 CRC 校验后返回原始值
        Args:
            cmd (int): 测量命令字节
        Returns:
            int: 16 位原始测量值
        Raises:
            CRCError: CRC-8 校验失败时抛出
            RuntimeError: I2C 通信失败时抛出
        Notes:
            - 副作用：发送测量命令并读取 I2C 数据
            - 使用全局复用缓冲区 _BUF3 减少内存分配
            - ISR-safe: 否
        ==========================================
        Send measurement command, read 3-byte result (MSB+LSB+CRC),
        verify CRC, and return raw value.
        Args:
            cmd (int): Measurement command byte
        Returns:
            int: 16-bit raw measurement value
        Raises:
            CRCError: If CRC-8 verification fails
            RuntimeError: If I2C communication fails
        Notes:
            - Side effect: Sends measurement command and reads I2C data
            - Uses global buffer _BUF3 to reduce memory allocation
            - ISR-safe: No
        """
        if not isinstance(cmd, int) or not 0 <= cmd <= 0xFFFF:
            raise ValueError("cmd must be an integer command value")
        global _BUF3
        # 步骤 1：发送测量命令
        self._write_cmd(cmd)
        # 步骤 2：等待转换完成（数据手册规定最大转换时间）
        sleep(self._I2C_DELAY_MS / 1000.0)
        # 步骤 3：读取 3 字节数据 [MSB, LSB, CRC]
        try:
            self._i2c.readfrom_into(self._addr, _BUF3)
        except OSError as e:
            raise RuntimeError("I2C read measurement failed") from e

        # 步骤 4：CRC-8 校验
        if not _crc8_si7021(_BUF3):
            raw_data = _BUF3[:2]
            crc_byte = _BUF3[2]
            raise CRCError("CRC check failed: data=[0x%02X, 0x%02X], crc=0x%02X" % (raw_data[0], raw_data[1], crc_byte))
        # 步骤 5：将 MSB、LSB 合并为 16 位整数
        return _bytes_to_int(_BUF3[:2])

    def _read_device_info(self) -> tuple:
        """
        读取芯片序列号和设备型号标识
        Returns:
            tuple: (serial (int), identifier (str))
        Raises:
            RuntimeError: I2C 通信失败时抛出
        Notes:
            - 调用两次 I2C 读取命令获取完整序列号
            - 副作用：通过 I2C 总线读取数据
            - ISR-safe: 否
        ==========================================
        Read chip serial number and device model identifier.
        Returns:
            tuple: (serial (int), identifier (str))
        Raises:
            RuntimeError: If I2C communication fails
        Notes:
            - Calls two I2C read commands to get complete serial number
            - Side effect: Reads data via I2C bus
            - ISR-safe: No
        """
        _ID_CMD1 = bytearray([self._CMD_ID1, self._CMD_ID1_ARG])
        _ID_CMD2 = bytearray([self._CMD_ID2, self._CMD_ID2_ARG])

        # 步骤 1：读取序列号前半部分（8 字节 SNA_3 + SNB_3）
        self._write_cmd_buf(_ID_CMD1)
        id1 = bytearray(8)
        sleep(self._I2C_DELAY_MS / 1000.0)
        try:
            self._i2c.readfrom_into(self._addr, id1)
        except OSError as e:
            raise RuntimeError("I2C read device ID part 1 failed") from e

        # 步骤 2：读取序列号后半部分（6 字节 SNB_2）
        self._write_cmd_buf(_ID_CMD2)
        id2 = bytearray(6)
        sleep(self._I2C_DELAY_MS / 1000.0)
        try:
            self._i2c.readfrom_into(self._addr, id2)
        except OSError as e:
            raise RuntimeError("I2C read device ID part 2 failed") from e

        # 步骤 3：按数据手册拼接序列号字节（SNA_3[0,2,4,6] + SNB_3[0,1,3,4]）
        combined = bytearray(
            [
                id1[0],
                id1[2],
                id1[4],
                id1[6],
                id2[0],
                id2[1],
                id2[3],
                id2[4],
            ]
        )

        serial = _bytes_to_int(combined)
        # id2[0] 为 SNB_3 的设备标识字节
        identifier = _device_identifier(id2[0])

        return serial, identifier

    def _log(self, msg: str) -> None:
        """
        调试日志输出（仅当 _debug=True 时打印）
        Args:
            msg (str): 日志消息
        Notes:
            - 无硬件副作用
            - ISR-safe: 否（print 涉及内存分配）
        ==========================================
        Output debug log (only when _debug=True).
        Args:
            msg (str): Log message
        Notes:
            - No hardware side effects
            - ISR-safe: No (print involves memory allocation)
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[Si7021] %s" % msg)

    def deinit(self) -> None:
        """
        释放传感器资源，清除内部状态
        Notes:
            - I2C 总线由外部管理，不在类内创建故不在此释放
            - 副作用：将 serial/identifier 清零
            - ISR-safe: 否
        ==========================================
        Release sensor resources and clear internal state.
        Notes:
            - I2C bus is externally managed, not released here
            - Side effect: Clears serial/identifier to zero
            - ISR-safe: No
        """
        self._log("deinitializing")
        self.serial = 0
        self.identifier = ""


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
