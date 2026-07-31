# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 19:19
# @Author  : Mika Tuupola
# @File    : mpu6500.py
# @Description : MPU6500 accelerometer and gyroscope I2C driver
# @License : MIT

__version__ = "0.4.0"
__author__ = "Mika Tuupola"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    import micropython

    micropython.alloc_emergency_exception_buf(100)
    from micropython import const
except ImportError:

    def const(value):
        return value


try:
    import ustruct as struct
except ImportError:
    import struct

try:
    import utime as time
except ImportError:
    import time

# ======================================== 全局变量 ============================================

_BUF1 = bytearray(1)
_BUF2 = bytearray(2)
_BUF6 = bytearray(6)

_GYRO_CONFIG = const(0x1B)
_ACCEL_CONFIG = const(0x1C)
_ACCEL_XOUT_H = const(0x3B)
_TEMP_OUT_H = const(0x41)
_GYRO_XOUT_H = const(0x43)
_PWR_MGMT_1 = const(0x6B)
_WHO_AM_I = const(0x75)

ACCEL_FS_SEL_2G = const(0b00000000)
ACCEL_FS_SEL_4G = const(0b00001000)
ACCEL_FS_SEL_8G = const(0b00010000)
ACCEL_FS_SEL_16G = const(0b00011000)

_ACCEL_SO_2G = 16384.0
_ACCEL_SO_4G = 8192.0
_ACCEL_SO_8G = 4096.0
_ACCEL_SO_16G = 2048.0

GYRO_FS_SEL_250DPS = const(0b00000000)
GYRO_FS_SEL_500DPS = const(0b00001000)
GYRO_FS_SEL_1000DPS = const(0b00010000)
GYRO_FS_SEL_2000DPS = const(0b00011000)

_GYRO_SO_250DPS = 131.0
_GYRO_SO_500DPS = 62.5
_GYRO_SO_1000DPS = 32.8
_GYRO_SO_2000DPS = 16.4

_TEMP_SO = 333.87
_TEMP_OFFSET = 21.0

SF_G = 1.0
SF_M_S2 = 9.80665
SF_DEG_S = 1.0
SF_RAD_S = 0.017453292519943

_VALID_WHOAMI = (0x70, 0x71, 0x90)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class MPU6500:
    """MPU6500 accelerometer and gyroscope driver."""

    I2C_DEFAULT_ADDR = const(0x68)
    CALIBRATE_COUNT = const(256)
    CALIBRATE_DELAY_MS = const(0)

    __slots__ = ("_i2c", "_address", "_accel_so", "_gyro_so", "_accel_sf", "_gyro_sf", "_gyro_offset", "_debug")

    def __init__(
        self,
        i2c: object,
        address: int = I2C_DEFAULT_ADDR,
        accel_fs: int = ACCEL_FS_SEL_2G,
        gyro_fs: int = GYRO_FS_SEL_250DPS,
        accel_sf: float = SF_M_S2,
        gyro_sf: float = SF_RAD_S,
        gyro_offset: tuple = (0, 0, 0),
        debug: bool = False,
    ) -> None:
        """初始化 MPU6500 传感器 / Initialize the MPU6500 sensor."""
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must provide readfrom_mem_into")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if not isinstance(accel_fs, int):
            raise ValueError("accel_fs must be int")
        if not isinstance(gyro_fs, int):
            raise ValueError("gyro_fs must be int")
        if not isinstance(gyro_offset, tuple) or len(gyro_offset) != 3:
            raise ValueError("gyro_offset must be a tuple of three numbers")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        try:
            self._i2c = i2c
            self._address = address
            self._debug = debug
            self._gyro_offset = gyro_offset

            whoami = self.whoami
            if whoami not in _VALID_WHOAMI:
                raise RuntimeError("MPU6500 not found on I2C bus (WHOAMI=0x%02X)" % whoami)

            self._register_char(_PWR_MGMT_1, 0x80)
            time.sleep_ms(100)
            self._register_char(_PWR_MGMT_1, 0x00)
            time.sleep_ms(100)

            self._accel_so = self._accel_fs(accel_fs)
            self._gyro_so = self._gyro_fs(gyro_fs)
            self._accel_sf = accel_sf
            self._gyro_sf = gyro_sf
            self._log("init complete, accel_fs=0x%02X gyro_fs=0x%02X" % (accel_fs, gyro_fs))
        except Exception:
            raise

    def calibrate(self, count: int = CALIBRATE_COUNT, delay: int = CALIBRATE_DELAY_MS) -> tuple:
        """校准陀螺仪 / Calibrate the gyroscope.

        Returns:
            tuple: 陀螺仪偏移量 / Gyroscope offsets.
        """
        if not isinstance(count, int) or count <= 0:
            raise ValueError("count must be a positive int")
        if not isinstance(delay, int) or delay < 0:
            raise ValueError("delay must be a non-negative int")

        try:
            ox, oy, oz = (0.0, 0.0, 0.0)
            self._gyro_offset = (0.0, 0.0, 0.0)
            remaining = count
            while remaining:
                time.sleep_ms(delay)
                gx, gy, gz = self.gyro
                ox += gx
                oy += gy
                oz += gz
                remaining -= 1
            self._gyro_offset = (ox / count, oy / count, oz / count)
            self._log("calibrate done: gyro_offset=%s" % (self._gyro_offset,))
            return self._gyro_offset
        except Exception:
            raise

    @property
    def acceleration(self) -> tuple:
        """读取加速度三轴数据 / Read three-axis acceleration."""
        xyz = self._register_three_shorts(_ACCEL_XOUT_H)
        return tuple(value / self._accel_so * self._accel_sf for value in xyz)

    @property
    def gyro(self) -> tuple:
        """读取陀螺仪三轴数据 / Read three-axis gyroscope data."""
        ox, oy, oz = self._gyro_offset
        xyz = [value / self._gyro_so * self._gyro_sf for value in self._register_three_shorts(_GYRO_XOUT_H)]
        xyz[0] -= ox
        xyz[1] -= oy
        xyz[2] -= oz
        return tuple(xyz)

    @property
    def temperature(self) -> float:
        """读取温度 / Read the temperature."""
        temp = self._register_short(_TEMP_OUT_H)
        return ((temp - _TEMP_OFFSET) / _TEMP_SO) + _TEMP_OFFSET

    @property
    def whoami(self) -> int:
        """读取设备标识 / Read the device identifier."""
        return self._register_char(_WHO_AM_I)

    def _register_short(self, register: int, value=None, buf: bytearray = _BUF2, retries: int = 2, delay_ms: int = 5):
        if register < 0:
            raise ValueError("register must be non-negative")
        if value is None:
            self._readfrom_mem_into(register, buf, retries, delay_ms)
            return struct.unpack(">h", buf)[0]

        struct.pack_into(">h", buf, 0, value)
        self._writeto_mem(register, buf, retries, delay_ms)
        return None

    def _register_three_shorts(self, register: int, buf: bytearray = _BUF6, retries: int = 2, delay_ms: int = 5) -> tuple:
        if register < 0:
            raise ValueError("register must be non-negative")
        self._readfrom_mem_into(register, buf, retries, delay_ms)
        return struct.unpack(">hhh", buf)

    def _register_char(self, register: int, value=None, buf: bytearray = _BUF1, retries: int = 2, delay_ms: int = 5):
        if register < 0:
            raise ValueError("register must be non-negative")
        if value is None:
            self._readfrom_mem_into(register, buf, retries, delay_ms)
            return buf[0]

        buf[0] = value & 0xFF
        self._writeto_mem(register, buf, retries, delay_ms)
        return None

    def _readfrom_mem_into(self, register: int, buf: bytearray, retries: int, delay_ms: int) -> None:
        for attempt in range(retries + 1):
            try:
                self._i2c.readfrom_mem_into(self._address, register, buf)
                return
            except OSError:
                if attempt == retries:
                    raise RuntimeError("I2C read failed at register 0x%02X" % register)
                time.sleep_ms(delay_ms)

    def _writeto_mem(self, register: int, buf: bytearray, retries: int, delay_ms: int) -> None:
        for attempt in range(retries + 1):
            try:
                self._i2c.writeto_mem(self._address, register, buf)
                return
            except OSError:
                if attempt == retries:
                    raise RuntimeError("I2C write failed at register 0x%02X" % register)
                time.sleep_ms(delay_ms)

    def _accel_fs(self, value: int) -> float:
        if value not in (ACCEL_FS_SEL_2G, ACCEL_FS_SEL_4G, ACCEL_FS_SEL_8G, ACCEL_FS_SEL_16G):
            raise ValueError("invalid accel_fs value")
        self._register_char(_ACCEL_CONFIG, value)
        if value == ACCEL_FS_SEL_2G:
            return _ACCEL_SO_2G
        if value == ACCEL_FS_SEL_4G:
            return _ACCEL_SO_4G
        if value == ACCEL_FS_SEL_8G:
            return _ACCEL_SO_8G
        if value == ACCEL_FS_SEL_16G:
            return _ACCEL_SO_16G
        raise ValueError("invalid accel_fs value")

    def _gyro_fs(self, value: int) -> float:
        if value not in (GYRO_FS_SEL_250DPS, GYRO_FS_SEL_500DPS, GYRO_FS_SEL_1000DPS, GYRO_FS_SEL_2000DPS):
            raise ValueError("invalid gyro_fs value")
        self._register_char(_GYRO_CONFIG, value)
        if value == GYRO_FS_SEL_250DPS:
            return _GYRO_SO_250DPS
        if value == GYRO_FS_SEL_500DPS:
            return _GYRO_SO_500DPS
        if value == GYRO_FS_SEL_1000DPS:
            return _GYRO_SO_1000DPS
        if value == GYRO_FS_SEL_2000DPS:
            return _GYRO_SO_2000DPS
        raise ValueError("invalid gyro_fs value")

    def _log(self, msg: str) -> None:
        if msg is None:
            raise ValueError("msg must not be None")
        if self._debug:
            print("[MPU6500] %s" % msg)

    def deinit(self) -> None:
        """释放驱动资源 / Release driver resources."""
        try:
            self._register_char(_PWR_MGMT_1, 0x40)
            self._log("deinit: sleep mode")
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        if exception_type is not None and not hasattr(exception_type, "__name__"):
            raise ValueError("exception_type must be an exception type")
        pass


# ======================================== 初始化配置 ===========================================

# ========================================  主程序 ============================================
