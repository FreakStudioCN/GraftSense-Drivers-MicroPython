# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06
# @Author  : Jose D. Montoya / Fixed by MicroPython Expert
# @File    : isl29125.py
# @Description : 修复版ISL29125 RGB颜色传感器驱动（解决负数/寄存器冲突BUG）
# @License : MIT

__version__ = "1.0.1"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

from micropython import const
from micropython_isl29125.i2c_helpers import CBits, RegisterStruct

# ===================== 寄存器地址 =====================
_REG_WHOAMI    = const(0x00)
_CONFIG1       = const(0x01)
_CONFIG2       = const(0x02)
_CONFIG3       = const(0x03)
_FLAG_REGISTER = const(0x08)

# ===================== 工作模式 =====================
POWERDOWN      = const(0b000)
GREEN_ONLY     = const(0b001)
RED_ONLY       = const(0b010)
BLUE_ONLY      = const(0b011)
STANDBY        = const(0b100)
RED_GREEN_BLUE = const(0b101)
GREEN_RED      = const(0b110)
GREEN_BLUE     = const(0b111)

operation_values = (
    POWERDOWN, GREEN_ONLY, RED_ONLY, BLUE_ONLY,
    STANDBY, RED_GREEN_BLUE, GREEN_RED, GREEN_BLUE,
)

# ===================== 感光量程 =====================
LUX_375 = const(0b0)
LUX_10K = const(0b1)
sensing_range_values = (LUX_375, LUX_10K)

# ===================== ADC分辨率 =====================
RES_16BITS = const(0b0)
RES_12BITS = const(0b1)

# ===================== 中断配置 =====================
NO_INTERRUPT    = const(0b00)
GREEN_INTERRUPT = const(0b01)
RED_INTERRUPT   = const(0b10)
BLUE_INTERRUPT  = const(0b11)
interrupt_values = (NO_INTERRUPT, GREEN_INTERRUPT, RED_INTERRUPT, BLUE_INTERRUPT)

IC1 = const(0b00)
IC2 = const(0b01)
IC4 = const(0b10)
IC8 = const(0b11)
persistent_control_values = (IC1, IC2, IC4, IC8)

# ===================== 传感器驱动类 =====================
class ISL29125:
    """修复版ISL29125驱动：解决寄存器位冲突 + 16位无符号数读取BUG"""
    # 寄存器定义：H = 无符号16位整数（修复负数问题）
    _device_id      = RegisterStruct(_REG_WHOAMI, "B")
    _conf_reg       = RegisterStruct(_CONFIG1, "B")
    _conf_reg2      = RegisterStruct(_CONFIG2, "B")
    _conf_reg3      = RegisterStruct(_CONFIG3, "B")
    _low_threshold  = RegisterStruct(0x04, "H")  # 修复：h → H
    _high_threshold = RegisterStruct(0x06, "H")  # 修复：h → H
    _flag_register  = RegisterStruct(0x08, "B")

    _green = RegisterStruct(0x09, "H")  # 修复：h → H
    _red   = RegisterStruct(0x0B, "H")  # 修复：h → H
    _blue  = RegisterStruct(0x0D, "H")  # 修复：h → H

    # ===================== 核心修复：寄存器位定义（ datasheet 标准） =====================
    _operation_mode               = CBits(3, _CONFIG1, 0)   # BIT0-2: 工作模式
    _rgb_sensing_range            = CBits(1, _CONFIG1, 3)   # BIT3: 量程（原代码正确）
    _adc_resolution               = CBits(1, _CONFIG1, 4)   # BIT4: 分辨率【修复！原代码错误用了BIT3】
    # ====================================================================================
    
    _ir_compensation              = CBits(1, _CONFIG2, 7)
    _ir_compensation_value        = CBits(6, _CONFIG2, 0)
    _interrupt_threshold_status   = CBits(2, _CONFIG3, 0)
    _interrupt_persistent_control = CBits(2, _CONFIG3, 2)
    _interrupt_triggered_status   = CBits(1, _FLAG_REGISTER, 0)
    _brown_out                    = CBits(1, _FLAG_REGISTER, 2)

    def __init__(self, i2c, address: int = 0x44) -> None:
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int) or not (0x00 <= address <= 0x7F):
            raise ValueError(f"address invalid: {address}")

        self._i2c = i2c
        self._address = address

        if self._device_id != 0x7D:
            raise RuntimeError("ISL29125 not found! Check wiring/address")

        # 初始化配置：RGB模式 + 10K量程 + 16位分辨率
        self._conf_reg = 0x0D
        self._conf_reg2 = 0xBF
        self.clear_register_flag()
        self._brown_out = 0

    @property
    def red(self) -> int:
        return self._red

    @property
    def green(self) -> int:
        return self._green

    @property
    def blue(self) -> int:
        return self._blue

    @property
    def colors(self) -> tuple:
        return self._red, self._green, self._blue

    @property
    def operation_mode(self) -> str:
        values = ("POWERDOWN", "GREEN_ONLY", "RED_ONLY", "BLUE_ONLY",
                  "STANDBY", "RED_GREEN_BLUE", "GREEN_RED", "GREEN_BLUE")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        if value not in operation_values:
            raise ValueError(f"Invalid mode: {value}")
        self._operation_mode = value

    @property
    def sensing_range(self) -> str:
        return ("LUX_375", "LUX_10K")[self._rgb_sensing_range]

    @sensing_range.setter
    def sensing_range(self, value: int) -> None:
        if value not in sensing_range_values:
            raise ValueError(f"Invalid range: {value}")
        self._rgb_sensing_range = value

    @property
    def adc_resolution(self) -> str:
        return ("RES_16BITS", "RES_12BITS")[self._adc_resolution]

    @adc_resolution.setter
    def adc_resolution(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("Resolution must be 0(16bit) or 1(12bit)")
        self._adc_resolution = value

    @property
    def ir_compensation(self) -> int:
        return self._ir_compensation

    @ir_compensation.setter
    def ir_compensation(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("IR comp must be 0 or 1")
        self._ir_compensation = value

    @property
    def ir_compensation_value(self) -> int:
        return self._ir_compensation_value

    @ir_compensation_value.setter
    def ir_compensation_value(self, value: int) -> None:
        if value not in (1,2,4,8,16,32):
            raise ValueError("IR value must be 1/2/4/8/16/32")
        self._ir_compensation_value = value

    @property
    def interrupt_threshold(self) -> str:
        values = ("No Interrupt", "Green Interrupt", "Red Interrupt", "Blue Interrupt")
        return values[self._interrupt_threshold_status]

    @interrupt_threshold.setter
    def interrupt_threshold(self, value: int) -> None:
        if value not in interrupt_values:
            raise ValueError(f"Invalid interrupt: {value}")
        self._interrupt_threshold_status = value

    @property
    def high_threshold(self) -> int:
        return self._high_threshold

    @high_threshold.setter
    def high_threshold(self, value: int) -> None:
        self._high_threshold = value

    @property
    def low_threshold(self) -> int:
        return self._low_threshold

    @low_threshold.setter
    def low_threshold(self, value: int) -> None:
        self._low_threshold = value

    @property
    def interrupt_triggered(self) -> int:
        return self._interrupt_triggered_status

    @property
    def persistent_control(self) -> str:
        return ("IC1", "IC2", "IC4", "IC8")[self._interrupt_persistent_control]

    @persistent_control.setter
    def persistent_control(self, value: int) -> None:
        if value not in persistent_control_values:
            raise ValueError(f"Invalid persistence: {value}")
        self._interrupt_persistent_control = value

    def clear_register_flag(self) -> int:
        return self._flag_register

    def deinit(self) -> None:
        self._operation_mode = POWERDOWN