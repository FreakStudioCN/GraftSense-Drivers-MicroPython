# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 19:19
# @Author  : Mika Tuupola
# @File    : mpu9250.py
# @Description : MPU9250 combined MPU6500 and AK8963 I2C driver
# @License : MIT

__version__ = "0.4.0"
__author__ = "Mika Tuupola"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


try:
    import utime as time
except ImportError:
    import time

from ak8963 import AK8963
from mpu6500 import MPU6500

# ======================================== 全局变量 ============================================

_INT_PIN_CFG = const(0x37)
_I2C_BYPASS_MASK = const(0b00000010)
_I2C_BYPASS_EN = const(0b00000010)
_I2C_BYPASS_DIS = const(0b00000000)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class MPU9250:
    """MPU9250 9-axis driver composed from MPU6500 and AK8963 drivers."""

    __slots__ = ("mpu6500", "ak8963")

    def __init__(self, i2c: object, mpu6500: object = None, ak8963: object = None) -> None:
        """初始化组合 MPU9250 驱动 / Initialize the combined MPU9250 driver."""
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must provide readfrom_mem_into")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")
        if mpu6500 is not None and not hasattr(mpu6500, "_register_char"):
            raise ValueError("mpu6500 must be an MPU6500 instance")
        if ak8963 is not None and not hasattr(ak8963, "magnetic"):
            raise ValueError("ak8963 must be an AK8963 instance")

        try:
            self.mpu6500 = mpu6500 if mpu6500 is not None else MPU6500(i2c)
            self._set_i2c_bypass(True)
            time.sleep_ms(10)
            self.ak8963 = ak8963 if ak8963 is not None else AK8963(i2c)
        except Exception:
            raise

    @property
    def acceleration(self) -> tuple:
        """读取加速度三轴数据 / Read three-axis acceleration."""
        return self.mpu6500.acceleration

    @property
    def gyro(self) -> tuple:
        """读取陀螺仪三轴数据 / Read three-axis gyroscope data."""
        return self.mpu6500.gyro

    @property
    def temperature(self) -> float:
        """读取温度 / Read the temperature."""
        return self.mpu6500.temperature

    @property
    def magnetic(self) -> tuple:
        """读取磁场三轴数据 / Read three-axis magnetic data."""
        return self.ak8963.magnetic

    @property
    def whoami(self) -> int:
        """读取设备标识 / Read the device identifier."""
        return self.mpu6500.whoami

    def deinit(self) -> None:
        """释放组合驱动资源 / Release combined-driver resources."""
        try:
            if hasattr(self, "ak8963") and hasattr(self.ak8963, "deinit"):
                self.ak8963.deinit()
            if hasattr(self, "mpu6500"):
                self._set_i2c_bypass(False)
                if hasattr(self.mpu6500, "deinit"):
                    self.mpu6500.deinit()
        except Exception:
            pass

    def _set_i2c_bypass(self, enabled: bool) -> None:
        if enabled not in (True, False):
            raise ValueError("enabled must be bool")
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be bool")

        char = self.mpu6500._register_char(_INT_PIN_CFG)
        char &= ~_I2C_BYPASS_MASK
        if enabled:
            char |= _I2C_BYPASS_EN
        else:
            char |= _I2C_BYPASS_DIS
        self.mpu6500._register_char(_INT_PIN_CFG, char)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        if exception_type is not None and not hasattr(exception_type, "__name__"):
            raise ValueError("exception_type must be an exception type")
        self.deinit()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序 ============================================
