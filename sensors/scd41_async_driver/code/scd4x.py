# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2022/01/01 00:00
# @Author  : ladyada, peter-l5
# @File    : scd4x.py
# @Description : SCD4X CO2/温湿度传感器驱动，支持周期测量、低功耗模式、自检、强制校准及EEPROM持久化
# @License : MIT

__version__ = "v103"
__author__ = "ladyada, peter-l5"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C
from micropython import const
import struct

# ======================================== 全局变量 ============================================

SCD4X_DEFAULT_ADDR = 0x62

# 寄存器命令常量
_SCD4X_REINIT = const(0x3646)
_SCD4X_FACTORYRESET = const(0x3632)
_SCD4X_FORCEDRECAL = const(0x362F)
_SCD4X_SELFTEST = const(0x3639)
_SCD4X_DATAREADY = const(0xE4B8)
_SCD4X_STOPPERIODICMEASUREMENT = const(0x3F86)
_SCD4X_STARTPERIODICMEASUREMENT = const(0x21B1)
_SCD4X_STARTLOWPOWERPERIODICMEASUREMENT = const(0x21AC)
_SCD4X_READMEASUREMENT = const(0xEC05)
_SCD4X_SERIALNUMBER = const(0x3682)
_SCD4X_GETTEMPOFFSET = const(0x2318)
_SCD4X_SETTEMPOFFSET = const(0x241D)
_SCD4X_GETALTITUDE = const(0x2322)
_SCD4X_SETALTITUDE = const(0x2427)
_SCD4X_SETPRESSURE = const(0xE000)
_SCD4X_PERSISTSETTINGS = const(0x3615)
_SCD4X_GETASCE = const(0x2313)
_SCD4X_SETASCE = const(0x2416)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class SCD4X:
    """
    SCD4X CO2/温湿度传感器驱动类（I2C接口）
    Attributes:
        address (int): I2C设备地址，默认0x62
        i2c_device (I2C): I2C总线实例
        _buffer (bytearray): 18字节通用读写缓冲区
        _cmd (bytearray): 2字节命令缓冲区
        _crc_buffer (bytearray): 2字节CRC校验缓冲区
        _temperature (float): 缓存的温度值（摄氏度）
        _relative_humidity (float): 缓存的相对湿度值（%rH）
        _co2 (int): 缓存的CO2浓度值（ppm）
    Methods:
        CO2: 读取CO2浓度（ppm）
        temperature: 读取温度（℃）
        relative_humidity: 读取相对湿度（%rH）
        data_ready: 检查新数据是否就绪
        serial_number: 读取传感器序列号
        self_calibration_enabled: 自动自校准开关
        temperature_offset: 温度偏移量
        altitude: 海拔高度
        reinit(): 重新初始化（从EEPROM加载用户设置）
        factory_reset(): 恢复出厂设置
        force_calibration(): 强制校准
        self_test(): 执行自检
        stop_periodic_measurement(): 停止周期测量
        start_periodic_measurement(): 启动周期测量（约5s/次）
        start_low_periodic_measurement(): 启动低功耗周期测量（约30s/次）
        persist_settings(): 将设置持久化到EEPROM
        set_ambient_pressure(): 设置环境气压
        deinit(): 停止测量并释放资源
    Notes:
        - 依赖外部传入I2C实例，不在驱动内部创建总线
        - 初始化时自动调用stop_periodic_measurement()
    ==========================================
    SCD4X CO2/temperature/humidity sensor driver (I2C interface).
    Attributes:
        address (int): I2C device address, default 0x62
        i2c_device (I2C): I2C bus instance
        _buffer (bytearray): 18-byte general read/write buffer
        _cmd (bytearray): 2-byte command buffer
        _crc_buffer (bytearray): 2-byte CRC check buffer
        _temperature (float): Cached temperature value (Celsius)
        _relative_humidity (float): Cached relative humidity (%rH)
        _co2 (int): Cached CO2 concentration (ppm)
    Methods:
        CO2: Read CO2 concentration (ppm)
        temperature: Read temperature (Celsius)
        relative_humidity: Read relative humidity (%rH)
        data_ready: Check if new data is available
        serial_number: Read sensor serial number
        self_calibration_enabled: Auto self-calibration switch
        temperature_offset: Temperature offset
        altitude: Altitude above sea level
        reinit(): Re-initialize (reload user settings from EEPROM)
        factory_reset(): Factory reset
        force_calibration(): Forced recalibration
        self_test(): Perform self-test
        stop_periodic_measurement(): Stop periodic measurement
        start_periodic_measurement(): Start periodic measurement (~5s/cycle)
        start_low_periodic_measurement(): Start low-power periodic measurement (~30s/cycle)
        persist_settings(): Persist settings to EEPROM
        set_ambient_pressure(): Set ambient pressure
        deinit(): Stop measurement and release resources
    Notes:
        - Requires externally provided I2C instance
        - Automatically calls stop_periodic_measurement() on init
    """

    def __init__(self, i2c_bus: I2C, address: int = SCD4X_DEFAULT_ADDR) -> None:
        """
        初始化SCD4X传感器
        Args:
            i2c_bus (I2C): I2C总线实例
            address (int): I2C设备地址，默认0x62
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：调用stop_periodic_measurement()停止已有测量
        ==========================================
        Initialize SCD4X sensor.
        Args:
            i2c_bus (I2C): I2C bus instance
            address (int): I2C device address, default 0x62
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Calls stop_periodic_measurement() to stop any ongoing measurement
        """
        # 参数校验
        if not hasattr(i2c_bus, "writeto"):
            raise ValueError("i2c_bus must be an I2C instance")
        if not isinstance(address, int) or not (0x00 <= address <= 0x7F):
            raise ValueError("address must be int in 0x00~0x7F, got %s" % address)

        self.address = address
        self.i2c_device = i2c_bus
        self._buffer = bytearray(18)
        self._cmd = bytearray(2)
        self._crc_buffer = bytearray(2)

        # 缓存最近一次测量值
        self._temperature = None
        self._relative_humidity = None
        self._co2 = None

        self.stop_periodic_measurement()

    @property
    def CO2(self) -> int:  # pylint:disable=invalid-name
        """
        读取CO2浓度（ppm）
        Returns:
            int: CO2浓度（ppm）；两次测量之间返回缓存值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read CO2 concentration (ppm).
        Returns:
            int: CO2 concentration (ppm); returns cached value between measurements
        Notes:
            - ISR-safe: No
        """
        if self.data_ready:
            self._read_data()
        return self._co2

    @property
    def temperature(self) -> float:
        """
        读取当前温度（摄氏度）
        Returns:
            float: 温度值（℃）；两次测量之间返回缓存值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current temperature (Celsius).
        Returns:
            float: Temperature in Celsius; returns cached value between measurements
        Notes:
            - ISR-safe: No
        """
        if self.data_ready:
            self._read_data()
        return self._temperature

    @property
    def relative_humidity(self) -> float:
        """
        读取当前相对湿度（%rH）
        Returns:
            float: 相对湿度（%rH）；两次测量之间返回缓存值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current relative humidity (%rH).
        Returns:
            float: Relative humidity (%rH); returns cached value between measurements
        Notes:
            - ISR-safe: No
        """
        if self.data_ready:
            self._read_data()
        return self._relative_humidity

    def reinit(self) -> None:
        """
        重新初始化传感器（从EEPROM重新加载用户设置）
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：先调用stop_periodic_measurement()
        ==========================================
        Reinitialize sensor by reloading user settings from EEPROM.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Calls stop_periodic_measurement() first
        """
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_REINIT, cmd_delay=0.02)

    def factory_reset(self) -> None:
        """
        恢复出厂设置（清除EEPROM中的FRC和ASC历史记录）
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：先调用stop_periodic_measurement()
        ==========================================
        Factory reset: clears all EEPROM settings and erases FRC/ASC history.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Calls stop_periodic_measurement() first
        """
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_FACTORYRESET, cmd_delay=1.2)

    def force_calibration(self, target_co2: int) -> None:
        """
        强制校准传感器至指定CO2浓度
        Args:
            target_co2 (int): 目标CO2浓度（ppm）
        Returns:
            None
        Raises:
            RuntimeError: 强制校准失败（传感器需先运行至少3分钟）
        Notes:
            - ISR-safe: 否
            - 副作用：先调用stop_periodic_measurement()
        ==========================================
        Force sensor recalibration to a given CO2 concentration.
        Args:
            target_co2 (int): Target CO2 concentration (ppm)
        Returns:
            None
        Raises:
            RuntimeError: Forced recalibration failed (sensor must be active for 3 minutes first)
        Notes:
            - ISR-safe: No
            - Side effects: Calls stop_periodic_measurement() first
        """
        self.stop_periodic_measurement()
        self._set_command_value(_SCD4X_FORCEDRECAL, target_co2)
        time.sleep(0.5)
        self._read_reply(self._buffer, 3)
        correction = struct.unpack_from(">h", self._buffer[0:2])[0]
        if correction == 0xFFFF:
            raise RuntimeError(
                "Forced recalibration failed.\
            Make sure sensor is active for 3 minutes first"
            )

    @property
    def self_calibration_enabled(self) -> bool:
        """
        自动自校准（ASC）开关状态
        Returns:
            bool: True=已启用，False=已禁用
        Notes:
            - ISR-safe: 否
            - 此值不会持久化，重启后重置，需调用persist_settings()保存
            - ASC正常工作需传感器连续运行7天，且每天至少1小时暴露在新鲜空气中
        ==========================================
        Auto self-calibration (ASC) enable state.
        Returns:
            bool: True=enabled, False=disabled
        Notes:
            - ISR-safe: No
            - Value is NOT saved on reboot unless persist_settings() is called
            - ASC requires 7 days of continuous operation with 1h/day fresh air exposure
        """
        self._send_command(_SCD4X_GETASCE, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return self._buffer[1] == 1

    @self_calibration_enabled.setter
    def self_calibration_enabled(self, enabled: bool) -> None:
        self._set_command_value(_SCD4X_SETASCE, enabled)

    def self_test(self) -> None:
        """
        执行传感器自检（最长耗时10秒）
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: 自检失败
        Notes:
            - ISR-safe: 否
            - 副作用：先调用stop_periodic_measurement()
        ==========================================
        Perform sensor self-test (takes up to 10 seconds).
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: Self test failed
        Notes:
            - ISR-safe: No
            - Side effects: Calls stop_periodic_measurement() first
        """
        self.stop_periodic_measurement()
        self._send_command(_SCD4X_SELFTEST, cmd_delay=10)
        self._read_reply(self._buffer, 3)
        if (self._buffer[0] != 0) or (self._buffer[1] != 0):
            raise RuntimeError("Self test failed")

    def _read_data(self) -> None:
        """
        从传感器读取温度/湿度/CO2并缓存
        Notes:
            - ISR-safe: 否
            - 副作用：更新_temperature/_relative_humidity/_co2缓存
        ==========================================
        Read temperature/humidity/CO2 from sensor and cache values.
        Notes:
            - ISR-safe: No
            - Side effects: Updates _temperature/_relative_humidity/_co2 cache
        """
        self._send_command(_SCD4X_READMEASUREMENT, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        self._co2 = (self._buffer[0] << 8) | self._buffer[1]
        temp = (self._buffer[3] << 8) | self._buffer[4]
        self._temperature = -45 + 175 * (temp / 2**16)
        humi = (self._buffer[6] << 8) | self._buffer[7]
        self._relative_humidity = 100 * (humi / 2**16)

    @property
    def data_ready(self) -> bool:
        """
        检查传感器是否有新数据就绪
        Returns:
            bool: True=有新数据，False=无新数据
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if new measurement data is available.
        Returns:
            bool: True=new data available, False=no new data
        Notes:
            - ISR-safe: No
        """
        self._send_command(_SCD4X_DATAREADY, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return not ((self._buffer[0] & 0x07 == 0) and (self._buffer[1] == 0))

    @property
    def serial_number(self) -> tuple:
        """
        读取传感器唯一序列号
        Returns:
            tuple: 6元素元组，包含序列号各字节
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor unique serial number.
        Returns:
            tuple: 6-element tuple containing serial number bytes
        Notes:
            - ISR-safe: No
        """
        self._send_command(_SCD4X_SERIALNUMBER, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        return (
            self._buffer[0],
            self._buffer[1],
            self._buffer[3],
            self._buffer[4],
            self._buffer[6],
            self._buffer[7],
        )

    def stop_periodic_measurement(self) -> None:
        """
        停止周期测量模式
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Stop periodic measurement mode.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self._send_command(_SCD4X_STOPPERIODICMEASUREMENT, cmd_delay=0.5)

    def start_periodic_measurement(self) -> None:
        """
        启动周期测量模式（约5秒/次）
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 工作模式下仅以下命令可用：CO2/temperature/relative_humidity/data_ready/
              reinit/factory_reset/force_calibration/self_test/set_ambient_pressure
        ==========================================
        Start periodic measurement mode (~5s per measurement).
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Only the following commands work in measurement mode:
              CO2/temperature/relative_humidity/data_ready/
              reinit/factory_reset/force_calibration/self_test/set_ambient_pressure
        """
        self._send_command(_SCD4X_STARTPERIODICMEASUREMENT)

    def start_low_periodic_measurement(self) -> None:
        """
        启动低功耗周期测量模式（约30秒/次）
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 可用命令与start_periodic_measurement()相同
        ==========================================
        Start low-power periodic measurement mode (~30s per measurement).
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Available commands same as start_periodic_measurement()
        """
        self._send_command(_SCD4X_STARTLOWPOWERPERIODICMEASUREMENT)

    def persist_settings(self) -> None:
        """
        将温度偏移、海拔偏移和自校准设置持久化到EEPROM
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Save temperature offset, altitude offset, and self-calibration settings to EEPROM.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self._send_command(_SCD4X_PERSISTSETTINGS, cmd_delay=0.8)

    def set_ambient_pressure(self, ambient_pressure: int) -> None:
        """
        设置环境气压以修正CO2计算值
        Args:
            ambient_pressure (int): 环境气压（hPa），范围0~65535
        Returns:
            None
        Raises:
            AttributeError: ambient_pressure超出范围
        Notes:
            - ISR-safe: 否
        ==========================================
        Set ambient pressure to adjust CO2 calculations.
        Args:
            ambient_pressure (int): Ambient pressure (hPa), range 0~65535
        Returns:
            None
        Raises:
            AttributeError: ambient_pressure out of range
        Notes:
            - ISR-safe: No
        """
        if ambient_pressure < 0 or ambient_pressure > 65535:
            raise AttributeError("`ambient_pressure` must be from 0~65535 hPascals")
        self._set_command_value(_SCD4X_SETPRESSURE, ambient_pressure)

    @property
    def temperature_offset(self) -> float:
        """
        温度偏移量（摄氏度，分辨率0.01℃，最大374℃）
        Returns:
            float: 当前温度偏移量（℃）
        Notes:
            - ISR-safe: 否
            - 此值不会持久化，重启后重置，需调用persist_settings()保存
        ==========================================
        Temperature offset in Celsius (resolution 0.01°C, max 374°C).
        Returns:
            float: Current temperature offset (Celsius)
        Notes:
            - ISR-safe: No
            - Value is NOT saved on reboot unless persist_settings() is called
        """
        self._send_command(_SCD4X_GETTEMPOFFSET, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        temp = (self._buffer[0] << 8) | self._buffer[1]
        return 175.0 * temp / 2**16

    @temperature_offset.setter
    def temperature_offset(self, offset) -> None:
        if offset > 374:
            raise AttributeError(
                "Offset value must be less than or equal to 374 degrees Celsius"
            )
        temp = int(offset * 2**16 / 175)
        self._set_command_value(_SCD4X_SETTEMPOFFSET, temp)

    @property
    def altitude(self) -> int:
        """
        海拔高度（米），用于修正CO2测量值
        Returns:
            int: 当前海拔高度（米）
        Notes:
            - ISR-safe: 否
            - 此值不会持久化，重启后重置，需调用persist_settings()保存
        ==========================================
        Altitude above sea level in metres, used to adjust CO2 measurements.
        Returns:
            int: Current altitude (metres)
        Notes:
            - ISR-safe: No
            - Value is NOT saved on reboot unless persist_settings() is called
        """
        self._send_command(_SCD4X_GETALTITUDE, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return (self._buffer[0] << 8) | self._buffer[1]

    @altitude.setter
    def altitude(self, height: int) -> None:
        if height > 65535:
            raise AttributeError("Height must be less than or equal to 65535 metres")
        self._set_command_value(_SCD4X_SETALTITUDE, height)

    def _check_buffer_crc(self, buf: bytearray) -> bool:
        """
        校验缓冲区中每3字节数据的CRC
        Args:
            buf (bytearray): 待校验缓冲区（每3字节为一组：2字节数据+1字节CRC）
        Returns:
            bool: 校验通过返回True
        Raises:
            RuntimeError: CRC校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Verify CRC for every 3-byte group in buffer.
        Args:
            buf (bytearray): Buffer to check (every 3 bytes: 2 data + 1 CRC)
        Returns:
            bool: True if all CRC checks pass
        Raises:
            RuntimeError: CRC check failed
        Notes:
            - ISR-safe: No
        """
        for i in range(0, len(buf), 3):
            self._crc_buffer[0] = buf[i]
            self._crc_buffer[1] = buf[i + 1]
            if self._crc8(self._crc_buffer) != buf[i + 2]:
                raise RuntimeError("CRC check failed while reading data")
        return True

    def _send_command(self, cmd: int, cmd_delay: float = 0) -> None:
        """
        向传感器发送2字节命令
        Args:
            cmd (int): 命令码（16位）
            cmd_delay (float): 命令执行后等待时间（秒），默认0
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败（工作模式下部分命令不可用）
        Notes:
            - ISR-safe: 否
        ==========================================
        Send 2-byte command to sensor.
        Args:
            cmd (int): Command code (16-bit)
            cmd_delay (float): Wait time after command (seconds), default 0
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed (some commands unavailable in working mode)
        Notes:
            - ISR-safe: No
        """
        self._cmd[0] = (cmd >> 8) & 0xFF
        self._cmd[1] = cmd & 0xFF

        try:
            self.i2c_device.writeto(self.address, self._cmd)
        except OSError as err:
            raise RuntimeError(
                "Could not communicate via I2C, some commands/settings "
                "unavailable while in working mode"
            ) from err
        time.sleep(cmd_delay)

    def _set_command_value(self, cmd, value, cmd_delay=0):
        """
        向传感器发送带参数值的命令
        Args:
            cmd: 命令码（16位）
            value: 参数值（16位）
            cmd_delay (float): 命令执行后等待时间（秒），默认0
        Notes:
            - ISR-safe: 否
        ==========================================
        Send command with parameter value to sensor.
        Args:
            cmd: Command code (16-bit)
            value: Parameter value (16-bit)
            cmd_delay (float): Wait time after command (seconds), default 0
        Notes:
            - ISR-safe: No
        """
        self._buffer[0] = (cmd >> 8) & 0xFF
        self._buffer[1] = cmd & 0xFF
        self._crc_buffer[0] = self._buffer[2] = (value >> 8) & 0xFF
        self._crc_buffer[1] = self._buffer[3] = value & 0xFF
        self._buffer[4] = self._crc8(self._crc_buffer)
        self.i2c_device.writeto(self.address, self._buffer[:5])
        time.sleep(cmd_delay)

    def _read_reply(self, buff, num):
        """
        从传感器读取响应并校验CRC
        Args:
            buff: 读取缓冲区
            num (int): 校验字节数
        Notes:
            - ISR-safe: 否
        ==========================================
        Read response from sensor and verify CRC.
        Args:
            buff: Read buffer
            num (int): Number of bytes to CRC-check
        Notes:
            - ISR-safe: No
        """
        self.i2c_device.readfrom_into(self.address, buff)
        self._check_buffer_crc(self._buffer[0:num])

    @staticmethod
    def _crc8(buffer: bytearray) -> int:
        """
        计算CRC-8校验值（多项式0x31，初始值0xFF）
        Args:
            buffer (bytearray): 待校验字节数组
        Returns:
            int: CRC-8校验值（低8位）
        Notes:
            - ISR-safe: 是
        ==========================================
        Calculate CRC-8 checksum (polynomial 0x31, initial value 0xFF).
        Args:
            buffer (bytearray): Byte array to check
        Returns:
            int: CRC-8 checksum (lower 8 bits)
        Notes:
            - ISR-safe: Yes
        """
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF

    def deinit(self) -> None:
        """
        停止测量并释放传感器资源
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：调用stop_periodic_measurement()停止测量
        ==========================================
        Stop measurement and release sensor resources.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Calls stop_periodic_measurement()
        """
        self.stop_periodic_measurement()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
