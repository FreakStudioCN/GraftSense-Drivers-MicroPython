# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Jose D. Montoya
# @File    : icm20948.py
# @Description : ICM20948 accelerometer, gyroscope, and temperature driver.
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from time import sleep

from micropython import const

from micropython_icm20948.i2c_helpers import CBits, RegisterStruct

# ======================================== 全局变量 ============================================

_REG_WHOAMI = const(0x00)
_REG_BANK_SEL = const(0x7F)
_PWR_MGMT_1 = const(0x06)
_PWR_MGMT_2 = const(0x07)
_ACCEL_CONFIG = const(0x14)
_GYRO_CONFIG_1 = const(0x01)
_GYRO_SMPLRT_DIV = const(0x00)
_ACCEL_SMPLRT_DIV_1 = const(0x10)
_ACCEL_XOUT_H = const(0x2D)
_GYRO_XOUT_H = const(0x33)
_TEMP_OUT = const(0x3A)
_DEVICE_ID_DEFAULT = const(0xEA)

CLK_SELECT_INTERNAL = const(0b000)
CLK_SELECT_BEST = const(0b001)
CLK_SELECT_STOP = const(0b111)
CLK_VALUES = (CLK_SELECT_INTERNAL, CLK_SELECT_BEST, CLK_SELECT_STOP)

ACC_DISABLED = const(0b111)
GYRO_DISABLED = const(0b111)
ACC_ENABLED = const(0b000)
GYRO_ENABLED = const(0b000)
TEMP_ENABLED = const(0b0)
TEMP_DISABLED = const(0b1)
GYRO_EN_VALUES = (GYRO_DISABLED, GYRO_ENABLED)
ACC_EN_VALUES = (ACC_DISABLED, ACC_ENABLED)
TEMP_EN_VALUES = (TEMP_DISABLED, TEMP_ENABLED)

USER_BANK_0 = const(0)
USER_BANK_1 = const(1)
USER_BANK_2 = const(2)
USER_BANK_3 = const(3)
USER_BANK_VALUES = (USER_BANK_0, USER_BANK_1, USER_BANK_2, USER_BANK_3)

RANGE_2G = const(0b00)
RANGE_4G = const(0b01)
RANGE_8G = const(0b10)
RANGE_16G = const(0b11)
ACC_RANGE_VALUES = (RANGE_2G, RANGE_4G, RANGE_8G, RANGE_16G)
ACC_RANGE_SENSITIVITY = (16384, 8192, 4096, 2048)

ACC_RATE_VALUES = {
    140.6: 7,
    102.3: 10,
    70.3: 15,
    48.9: 22,
    35.2: 31,
    17.6: 63,
    8.8: 127,
    4.4: 255,
    2.2: 513,
    1.1: 1022,
    0.55: 2044,
    0.27: 4095,
}
ACC_DATA_RATE_VALUES = (140.6, 102.3, 70.3, 48.9, 35.2, 17.6, 8.8, 4.4, 2.2, 1.1, 0.55, 0.27)
ACC_RATE_DIVISOR_VALUES = (7, 10, 15, 22, 31, 63, 127, 255, 513, 1022, 2044, 4095)

FREQ_246_0 = const(0b001)
FREQ_111_4 = const(0b010)
FREQ_50_4 = const(0b011)
FREQ_23_9 = const(0b100)
FREQ_11_5 = const(0b101)
FREQ_5_7 = const(0b110)
FREQ_473 = const(0b111)
ACC_FILTER_VALUES = (FREQ_246_0, FREQ_111_4, FREQ_50_4, FREQ_23_9, FREQ_11_5, FREQ_5_7, FREQ_473)

FS_250_DPS = const(0b00)
FS_500_DPS = const(0b01)
FS_1000_DPS = const(0b10)
FS_2000_DPS = const(0b11)
GYRO_FULL_SCALE_VALUES = (FS_250_DPS, FS_500_DPS, FS_1000_DPS, FS_2000_DPS)
GYRO_FULL_SCALE_SENSITIVITY = (131, 65.5, 32.8, 16.4)

GYRO_RATE_VALUES = {
    562.5: 1,
    375.0: 2,
    281.3: 3,
    225.0: 4,
    187.5: 5,
    140.6: 7,
    125.0: 8,
    102.3: 10,
    70.3: 15,
    66.2: 16,
    48.9: 22,
    35.2: 31,
    34.1: 32,
    17.6: 63,
    17.3: 64,
    4.4: 255,
}
GYRO_DATA_RATE_VALUES = (562.5, 375.0, 281.3, 225.0, 187.5, 140.6, 125.0, 102.3, 70.3, 66.2, 48.9, 35.2, 34.1, 17.6, 17.3, 4.4)
GYRO_RATE_DIVISOR_VALUES = (1, 2, 3, 4, 5, 7, 8, 10, 15, 16, 22, 31, 32, 63, 64, 255)

G_FREQ_196_6 = const(0b000)
G_FREQ_151_8 = const(0b001)
G_FREQ_119_5 = const(0b010)
G_FREQ_51_2 = const(0b011)
G_FREQ_23_9 = const(0b100)
G_FREQ_11_6 = const(0b101)
G_FREQ_5_7 = const(0b110)
G_FREQ_361_4 = const(0b111)
GYRO_FILTER_VALUES = (G_FREQ_196_6, G_FREQ_151_8, G_FREQ_119_5, G_FREQ_51_2, G_FREQ_23_9, G_FREQ_11_6, G_FREQ_5_7, G_FREQ_361_4)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class ICM20948:
    """ICM20948 I2C driver."""

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _pwr_mgt_1 = RegisterStruct(_PWR_MGMT_1, "B")
    _pwr_mgt_2 = RegisterStruct(_PWR_MGMT_2, "B")

    _clock_select = CBits(3, _PWR_MGMT_1, 0)
    _temp_enabled = CBits(1, _PWR_MGMT_1, 3)
    _sleep = CBits(1, _PWR_MGMT_1, 6)
    _reset = CBits(1, _PWR_MGMT_1, 7)

    _gyro_enable = CBits(3, _PWR_MGMT_2, 0)
    _acc_enable = CBits(3, _PWR_MGMT_2, 3)

    _raw_accel_data = RegisterStruct(_ACCEL_XOUT_H, ">hhh")
    _raw_gyro_data = RegisterStruct(_GYRO_XOUT_H, ">hhh")
    _raw_temp_data = RegisterStruct(_GYRO_XOUT_H, ">hhhh")

    _user_bank = CBits(2, _REG_BANK_SEL, 4)

    _gyro_rate_divisor = RegisterStruct(_GYRO_SMPLRT_DIV, ">B")
    _acc_rate_divisor = RegisterStruct(_ACCEL_SMPLRT_DIV_1, ">H")

    _acc_choice = CBits(1, _ACCEL_CONFIG, 0)
    _acc_data_range = CBits(2, _ACCEL_CONFIG, 1)
    _acc_dplcfg = CBits(3, _ACCEL_CONFIG, 3)

    _gyro_choice = CBits(0, _GYRO_CONFIG_1, 0)
    _gyro_full_scale = CBits(2, _GYRO_CONFIG_1, 1)
    _gyro_dplcfg = CBits(3, _GYRO_CONFIG_1, 3)

    def __init__(self, i2c, address: int = 0x69, debug: bool = False) -> None:
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if address < 0x08 or address > 0x77:
            raise ValueError("address must be a 7-bit I2C address")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self._address = address
        self._debug = debug
        self._memory_accel_range = RANGE_2G
        self._memory_gyro_fs = FS_500_DPS

        if self._device_id != _DEVICE_ID_DEFAULT:
            raise RuntimeError("Failed to find the ICM20948 sensor")
        self._log("ICM20948 found at 0x%02X" % address)

        self.reset = 1
        self._sleep = 0
        self.clock_select = CLK_SELECT_BEST
        self.accelerometer_range = RANGE_2G
        self.gyro_full_scale = FS_500_DPS
        self.acc_data_rate_divisor = 22
        self.gyro_data_rate_divisor = 10

    @property
    def clock_select(self) -> str:
        values = {0: "CLK_SELECT_INTERNAL", 1: "CLK_SELECT_BEST", 7: "CLK_SELECT_STOP"}
        return values[self._clock_select]

    @clock_select.setter
    def clock_select(self, value: int) -> None:
        if value not in CLK_VALUES:
            raise ValueError("Select a valid Clock Select setting")
        self._clock_select = value

    @property
    def reset(self) -> int:
        return self._reset

    @reset.setter
    def reset(self, value: int = 1) -> None:
        if value not in (0, 1, False, True):
            raise ValueError("reset must be 0 or 1")
        self._reset = int(value)
        sleep(1)

    @property
    def gyro_enabled(self) -> str:
        values = {GYRO_DISABLED: "GYRO_DISABLED", GYRO_ENABLED: "GYRO_ENABLED"}
        return values[self._gyro_enable]

    @gyro_enabled.setter
    def gyro_enabled(self, value: int) -> None:
        if value not in GYRO_EN_VALUES:
            raise ValueError("Value must be a valid Gyro Enabled setting")
        self._gyro_enable = value

    @property
    def acc_enabled(self) -> str:
        values = {ACC_DISABLED: "ACC_DISABLED", ACC_ENABLED: "ACC_ENABLED"}
        return values[self._acc_enable]

    @acc_enabled.setter
    def acc_enabled(self, value: int) -> None:
        if value not in ACC_EN_VALUES:
            raise ValueError("Value must be a valid Accelerometer Enabled setting")
        self._acc_enable = value

    @property
    def temperature_enabled(self) -> str:
        values = {TEMP_DISABLED: "TEMP_DISABLED", TEMP_ENABLED: "TEMP_ENABLED"}
        return values[self._temp_enabled]

    @temperature_enabled.setter
    def temperature_enabled(self, value: int) -> None:
        if value not in TEMP_EN_VALUES:
            raise ValueError("Value must be a valid Temperature Enabled setting")
        self._temp_enabled = value

    @property
    def acceleration(self) -> tuple:
        raw_measurement = self._raw_accel_data
        sensitivity = ACC_RANGE_SENSITIVITY[self._memory_accel_range]
        x = raw_measurement[0] / sensitivity * 9.80665
        y = raw_measurement[1] / sensitivity * 9.80665
        z = raw_measurement[2] / sensitivity * 9.80665
        return x, y, z

    @property
    def gyro(self) -> tuple:
        raw_measurement = self._raw_gyro_data
        sensitivity = GYRO_FULL_SCALE_SENSITIVITY[self._memory_gyro_fs]
        x = raw_measurement[0] / sensitivity * 0.017453293
        y = raw_measurement[1] / sensitivity * 0.017453293
        z = raw_measurement[2] / sensitivity * 0.017453293
        return x, y, z

    @property
    def power_bank(self) -> int:
        return self._user_bank

    @power_bank.setter
    def power_bank(self, value: int) -> None:
        if value not in USER_BANK_VALUES:
            raise ValueError("Value must be a valid user bank")
        self._user_bank = value
        sleep(0.005)

    @property
    def accelerometer_range(self) -> str:
        values = ("RANGE_2G", "RANGE_4G", "RANGE_8G", "RANGE_16G")
        return values[self._memory_accel_range]

    @accelerometer_range.setter
    def accelerometer_range(self, value: int) -> None:
        if value not in ACC_RANGE_VALUES:
            raise ValueError("Value must be a valid Accelerometer Range Setting")
        self._user_bank = USER_BANK_2
        self._acc_data_range = value
        self._memory_accel_range = value
        self._user_bank = USER_BANK_0

    @property
    def gyro_full_scale(self) -> str:
        values = ("FS_250_DPS", "FS_500_DPS", "FS_1000_DPS", "FS_2000_DPS")
        return values[self._memory_gyro_fs]

    @gyro_full_scale.setter
    def gyro_full_scale(self, value: int) -> None:
        if value not in GYRO_FULL_SCALE_VALUES:
            raise ValueError("Value must be a valid gyro_full_scale setting")
        self._user_bank = USER_BANK_2
        self._gyro_full_scale = value
        self._memory_gyro_fs = value
        self._user_bank = USER_BANK_0

    @property
    def temperature(self) -> float:
        return (self._raw_temp_data[3] / 333.87) + 21

    @property
    def gyro_data_rate(self) -> float:
        return list(GYRO_RATE_VALUES.keys())[list(GYRO_RATE_VALUES.values()).index(self.gyro_data_rate_divisor)]

    @gyro_data_rate.setter
    def gyro_data_rate(self, value: int) -> None:
        if value not in GYRO_DATA_RATE_VALUES:
            raise ValueError("Gyro data rate must be a valid setting")
        self.gyro_data_rate_divisor = GYRO_RATE_VALUES[value]

    @property
    def gyro_data_rate_divisor(self) -> int:
        self._user_bank = USER_BANK_2
        raw_rate_divisor = self._gyro_rate_divisor
        self._user_bank = USER_BANK_0
        return raw_rate_divisor

    @gyro_data_rate_divisor.setter
    def gyro_data_rate_divisor(self, value: int) -> None:
        if value not in GYRO_RATE_DIVISOR_VALUES:
            raise ValueError("Value must be a valid gyro data rate divisor setting")
        self._user_bank = USER_BANK_2
        self._gyro_rate_divisor = value
        self._user_bank = USER_BANK_0

    @property
    def acc_data_rate(self) -> float:
        return list(ACC_RATE_VALUES.keys())[list(ACC_RATE_VALUES.values()).index(self.acc_data_rate_divisor)]

    @acc_data_rate.setter
    def acc_data_rate(self, value: int) -> None:
        if value not in ACC_DATA_RATE_VALUES:
            raise ValueError("Accelerometer data rate must be a valid setting")
        self.acc_data_rate_divisor = ACC_RATE_VALUES[value]

    @property
    def acc_data_rate_divisor(self) -> int:
        self._user_bank = USER_BANK_2
        raw_rate_divisor = self._acc_rate_divisor
        self._user_bank = USER_BANK_0
        return raw_rate_divisor

    @acc_data_rate_divisor.setter
    def acc_data_rate_divisor(self, value: int) -> None:
        if value not in ACC_RATE_DIVISOR_VALUES:
            raise ValueError("Value must be a valid acceleration data rate divisor setting")
        self._user_bank = USER_BANK_2
        self._acc_rate_divisor = value
        self._user_bank = USER_BANK_0

    @property
    def acc_dlpf_cutoff(self) -> str:
        values = ("FREQ_246_0", "FREQ_111_4", "FREQ_50_4", "FREQ_23_9", "FREQ_11_5", "FREQ_5_7", "FREQ_473")
        self._user_bank = USER_BANK_2
        raw_value = self._acc_dplcfg
        self._user_bank = USER_BANK_0
        return values[raw_value - 1]

    @acc_dlpf_cutoff.setter
    def acc_dlpf_cutoff(self, value: int) -> None:
        if value not in ACC_FILTER_VALUES:
            raise ValueError("Value must be a valid dlpf setting")
        self._user_bank = USER_BANK_2
        self._acc_dplcfg = value
        self._user_bank = USER_BANK_0

    @property
    def acc_filter_choice(self) -> int:
        self._user_bank = USER_BANK_2
        raw_value = self._acc_choice
        self._user_bank = USER_BANK_0
        return raw_value

    @acc_filter_choice.setter
    def acc_filter_choice(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("Value must be a valid accelerometer filter choice")
        self._user_bank = USER_BANK_2
        self._acc_choice = value
        self._user_bank = USER_BANK_0

    @property
    def gyro_dlpf_cutoff(self) -> str:
        values = ("G_FREQ_196_6", "G_FREQ_151_8", "G_FREQ_119_5", "G_FREQ_51_2", "G_FREQ_23_9", "G_FREQ_11_6", "G_FREQ_5_7", "G_FREQ_361_4")
        self._user_bank = USER_BANK_2
        raw_value = self._gyro_dplcfg
        self._user_bank = USER_BANK_0
        return values[raw_value]

    @gyro_dlpf_cutoff.setter
    def gyro_dlpf_cutoff(self, value: int) -> None:
        if value not in GYRO_FILTER_VALUES:
            raise ValueError("Value must be a valid dlpf setting")
        self._user_bank = USER_BANK_2
        self._gyro_dplcfg = value
        self._user_bank = USER_BANK_0

    @property
    def gyro_filter_choice(self) -> int:
        self._user_bank = USER_BANK_2
        raw_value = self._gyro_choice
        self._user_bank = USER_BANK_0
        return raw_value

    @gyro_filter_choice.setter
    def gyro_filter_choice(self, value: int) -> None:
        if value not in (0,):
            raise ValueError("Value must be a valid gyroscope filter choice")
        self._user_bank = USER_BANK_2
        self._gyro_choice = value
        self._user_bank = USER_BANK_0

    def _log(self, msg: str) -> None:
        if type(msg) is not str:
            raise ValueError("msg must be str")
        if self._debug:
            print("[ICM20948] %s" % msg)

    def deinit(self) -> None:
        self._sleep = 1


# ======================================== 初始化配置 ===========================================

# ========================================  主程序 ============================================
