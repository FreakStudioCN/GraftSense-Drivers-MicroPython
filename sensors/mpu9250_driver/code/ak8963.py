# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 19:19
# @Author  : Mika Tuupola
# @File    : ak8963.py
# @Description : AK8963 magnetometer I2C driver
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
_BUF6 = bytearray(6)

_WIA = const(0x00)
_ST1 = const(0x02)
_HXL = const(0x03)
_ST2 = const(0x09)
_CNTL1 = const(0x0A)
_ASAX = const(0x10)
_ASAY = const(0x11)
_ASAZ = const(0x12)

_MODE_POWER_DOWN = const(0b00000000)
MODE_SINGLE_MEASURE = const(0b00000001)
MODE_CONTINOUS_MEASURE_1 = const(0b00000010)
MODE_CONTINOUS_MEASURE_2 = const(0b00000110)
MODE_EXTERNAL_TRIGGER_MEASURE = const(0b00000100)
_MODE_SELF_TEST = const(0b00001000)
_MODE_FUSE_ROM_ACCESS = const(0b00001111)

OUTPUT_14_BIT = const(0b00000000)
OUTPUT_16_BIT = const(0b00010000)

_SO_14BIT = 0.6
_SO_16BIT = 0.15
_HOFL_BIT = const(0b00001000)
_DRDY_BIT = const(0b00000001)

_VALID_MODES = (MODE_SINGLE_MEASURE, MODE_CONTINOUS_MEASURE_1, MODE_CONTINOUS_MEASURE_2, MODE_EXTERNAL_TRIGGER_MEASURE)
_VALID_OUTPUTS = (OUTPUT_14_BIT, OUTPUT_16_BIT)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class AK8963:
    """AK8963 magnetometer driver."""

    I2C_DEFAULT_ADDR = const(0x0C)
    CALIBRATE_COUNT = const(256)
    CALIBRATE_DELAY_MS = const(200)

    __slots__ = ("_i2c", "_address", "_offset", "_scale", "_adjustement", "_so", "_mode", "_debug")

    def __init__(
        self,
        i2c: object,
        address: int = I2C_DEFAULT_ADDR,
        mode: int = MODE_CONTINOUS_MEASURE_1,
        output: int = OUTPUT_16_BIT,
        offset: tuple = (0, 0, 0),
        scale: tuple = (1, 1, 1),
        debug: bool = False,
    ) -> None:
        """初始化 AK8963 磁力计 / Initialize the AK8963 magnetometer."""
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must provide readfrom_mem_into")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if not isinstance(mode, int) or mode not in _VALID_MODES:
            raise ValueError("mode must be a valid AK8963 mode")
        if not isinstance(output, int) or output not in _VALID_OUTPUTS:
            raise ValueError("output must be a valid AK8963 output setting")
        if not isinstance(offset, tuple) or len(offset) != 3:
            raise ValueError("offset must be a tuple of three numbers")
        if not isinstance(scale, tuple) or len(scale) != 3:
            raise ValueError("scale must be a tuple of three numbers")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        try:
            self._i2c = i2c
            self._address = address
            self._offset = offset
            self._scale = scale
            self._debug = debug
            self._mode = mode
            self._so = _SO_16BIT if output == OUTPUT_16_BIT else _SO_14BIT

            if self.whoami != 0x48:
                raise RuntimeError("AK8963 not found on I2C bus")

            self._register_char(_CNTL1, _MODE_POWER_DOWN)
            time.sleep_ms(10)
            self._register_char(_CNTL1, _MODE_FUSE_ROM_ACCESS)
            time.sleep_ms(10)
            asax = self._register_char(_ASAX)
            asay = self._register_char(_ASAY)
            asaz = self._register_char(_ASAZ)
            self._register_char(_CNTL1, _MODE_POWER_DOWN)
            time.sleep_ms(10)

            self._adjustement = (
                (0.5 * (asax - 128)) / 128 + 1,
                (0.5 * (asay - 128)) / 128 + 1,
                (0.5 * (asaz - 128)) / 128 + 1,
            )

            self._register_char(_CNTL1, mode | output)
            time.sleep_ms(10)
            self._log("init complete, mode=0x%02X output=%dbit" % (mode, 16 if output == OUTPUT_16_BIT else 14))
        except Exception:
            raise

    def calibrate(self, count: int = CALIBRATE_COUNT, delay: int = CALIBRATE_DELAY_MS) -> tuple:
        """校准磁力计 / Calibrate the magnetometer.

        Returns:
            tuple: 偏移量与比例 / Offset and scale tuples.
        """
        if not isinstance(count, int) or count <= 0:
            raise ValueError("count must be a positive int")
        if not isinstance(delay, int) or delay < 0:
            raise ValueError("delay must be a non-negative int")

        try:
            self._offset = (0, 0, 0)
            self._scale = (1, 1, 1)
            reading = self.magnetic
            min_x = max_x = reading[0]
            min_y = max_y = reading[1]
            min_z = max_z = reading[2]

            remaining = count
            while remaining:
                time.sleep_ms(delay)
                mx, my, mz = self.magnetic
                if mx < min_x:
                    min_x = mx
                if mx > max_x:
                    max_x = mx
                if my < min_y:
                    min_y = my
                if my > max_y:
                    max_y = my
                if mz < min_z:
                    min_z = mz
                if mz > max_z:
                    max_z = mz
                remaining -= 1

            offset_x = (max_x + min_x) / 2
            offset_y = (max_y + min_y) / 2
            offset_z = (max_z + min_z) / 2
            self._offset = (offset_x, offset_y, offset_z)

            avg_delta_x = (max_x - min_x) / 2
            avg_delta_y = (max_y - min_y) / 2
            avg_delta_z = (max_z - min_z) / 2
            if avg_delta_x == 0 or avg_delta_y == 0 or avg_delta_z == 0:
                raise RuntimeError("Magnetometer calibration range is too small")

            avg_delta = (avg_delta_x + avg_delta_y + avg_delta_z) / 3
            self._scale = (avg_delta / avg_delta_x, avg_delta / avg_delta_y, avg_delta / avg_delta_z)
            self._log("calibrate done: offset=%s scale=%s" % (self._offset, self._scale))
            return self._offset, self._scale
        except Exception:
            raise

    def get_offset(self) -> tuple:
        """获取磁力计偏移量 / Get magnetometer offsets."""
        return self._offset

    def get_scale(self) -> tuple:
        """获取磁力计比例 / Get magnetometer scale values."""
        return self._scale

    @property
    def magnetic(self) -> tuple:
        """读取磁场三轴数据 / Read three-axis magnetic data."""
        status = self._register_char(_ST1)
        if not status & _DRDY_BIT:
            raise RuntimeError("AK8963 data is not ready")

        xyz = list(self._register_three_shorts(_HXL))
        status2 = self._register_char(_ST2)
        if status2 & _HOFL_BIT:
            raise RuntimeError("AK8963 magnetic sensor overflow")

        xyz[0] = ((xyz[0] * self._adjustement[0] * self._so) - self._offset[0]) * self._scale[0]
        xyz[1] = ((xyz[1] * self._adjustement[1] * self._so) - self._offset[1]) * self._scale[1]
        xyz[2] = ((xyz[2] * self._adjustement[2] * self._so) - self._offset[2]) * self._scale[2]

        if self._mode == MODE_SINGLE_MEASURE:
            self._register_char(_CNTL1, MODE_SINGLE_MEASURE | (OUTPUT_16_BIT if self._so == _SO_16BIT else OUTPUT_14_BIT))
            time.sleep_ms(10)

        return tuple(xyz)

    @property
    def adjustement(self) -> tuple:
        """获取灵敏度调整值 / Get sensitivity adjustment values."""
        return self._adjustement

    @property
    def whoami(self) -> int:
        """读取设备标识 / Read the device identifier."""
        return self._register_char(_WIA)

    def _register_three_shorts(self, register: int, buf: bytearray = _BUF6, retries: int = 2, delay_ms: int = 5) -> tuple:
        if register < 0:
            raise ValueError("register must be non-negative")
        self._readfrom_mem_into(register, buf, retries, delay_ms)
        return struct.unpack("<hhh", buf)

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

    def _log(self, msg: str) -> None:
        if msg is None:
            raise ValueError("msg must not be None")
        if self._debug:
            print("[AK8963] %s" % msg)

    def deinit(self) -> None:
        """释放驱动资源 / Release driver resources."""
        try:
            self._register_char(_CNTL1, _MODE_POWER_DOWN)
            time.sleep_ms(10)
            self._log("deinit: power down")
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
