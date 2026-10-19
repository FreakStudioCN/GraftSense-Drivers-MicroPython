# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : GraftSense contributors and FreakStudio
# @File    : _sx126x.py
# @Description : Shared SX126X constants for minimal initialization and TX
# @License : MIT

"""SX126X internal constants / SX126X 内部常量。"""

__version__ = "1.0.0"
__author__ = "GraftSense contributors; E H Ong; Jan Gromes; FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================
try:
    from micropython import const
except ImportError:
    # 该 CPython 回退仅用于主机端框架检查。
    def const(value: int) -> int:
        """
        执行 `const` 操作。
        Args:
            value (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return an unchanged constant value for host-side checks.
        Args:
            value (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return value


# ======================================== 全局变量 ============================================
# 本文件结构参考 MIT 许可的 GraftSense communication/sx1262_driver。
# 其实现谱系包含 ehong-tl/micropySX126X 和 Jan Gromes 的 RadioLib。

SX126X_MAX_PACKET_LENGTH = const(255)
SX126X_CHIP_MIN_FREQUENCY_MHZ = 150.0
SX126X_CHIP_MAX_FREQUENCY_MHZ = 960.0
SX126X_MAX_OUTPUT_POWER_DBM = const(22)

SX126X_CMD_SET_STANDBY = const(0x80)
SX126X_CMD_GET_STATUS = const(0xC0)
SX126X_CMD_NOP = const(0x00)
SX126X_CMD_SET_PACKET_TYPE = const(0x8A)
SX126X_CMD_SET_RF_FREQUENCY = const(0x86)
SX126X_CMD_SET_MODULATION_PARAMS = const(0x8B)
SX126X_CMD_SET_PACKET_PARAMS = const(0x8C)
SX126X_CMD_SET_PA_CONFIG = const(0x95)
SX126X_CMD_SET_TX_PARAMS = const(0x8E)
SX126X_CMD_SET_REGULATOR_MODE = const(0x96)
SX126X_CMD_CALIBRATE = const(0x89)
SX126X_CMD_CALIBRATE_IMAGE = const(0x98)
SX126X_CMD_SET_RX_TX_FALLBACK_MODE = const(0x93)
SX126X_CMD_GET_DEVICE_ERRORS = const(0x17)
SX126X_CMD_CLEAR_DEVICE_ERRORS = const(0x07)
SX126X_CMD_WRITE_REGISTER = const(0x0D)
SX126X_CMD_READ_REGISTER = const(0x1D)
SX126X_CMD_WRITE_BUFFER = const(0x0E)
SX126X_CMD_READ_BUFFER = const(0x1E)
SX126X_CMD_SET_TX = const(0x83)
SX126X_CMD_SET_RX = const(0x82)
SX126X_CMD_SET_BUFFER_BASE_ADDRESS = const(0x8F)
SX126X_CMD_GET_RX_BUFFER_STATUS = const(0x13)
SX126X_CMD_GET_PACKET_STATUS = const(0x14)
SX126X_CMD_SET_DIO_IRQ_PARAMS = const(0x08)
SX126X_CMD_GET_IRQ_STATUS = const(0x12)
SX126X_CMD_CLEAR_IRQ_STATUS = const(0x02)
SX126X_CMD_SET_DIO3_AS_TCXO_CTRL = const(0x97)
SX126X_CMD_SET_DIO2_AS_RF_SWITCH_CTRL = const(0x9D)

SX126X_PACKET_TYPE_GFSK = const(0x00)
SX126X_PACKET_TYPE_LORA = const(0x01)
SX126X_DIO2_AS_IRQ = const(0x00)
SX126X_DIO2_AS_RF_SWITCH = const(0x01)
SX126X_DIO3_OUTPUT_2_2 = const(0x03)
SX126X_STANDBY_RC = const(0x00)
SX126X_REGULATOR_LDO = const(0x00)
SX126X_REGULATOR_DCDC = const(0x01)
SX126X_FALLBACK_STANDBY_RC = const(0x20)
SX126X_CALIBRATE_ALL = const(0x7F)

SX126X_LORA_BW_125_0 = const(0x04)
SX126X_LORA_CR_4_5 = const(0x01)
SX126X_LORA_CR_4_6 = const(0x02)
SX126X_LORA_CR_4_7 = const(0x03)
SX126X_LORA_CR_4_8 = const(0x04)
SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_OFF = const(0x00)
SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_ON = const(0x01)
SX126X_LORA_HEADER_EXPLICIT = const(0x00)
SX126X_LORA_CRC_ON = const(0x01)
SX126X_LORA_IQ_STANDARD = const(0x00)

SX126X_IRQ_TX_DONE = const(0x0001)
SX126X_IRQ_RX_DONE = const(0x0002)
SX126X_IRQ_HEADER_ERROR = const(0x0020)
SX126X_IRQ_CRC_ERROR = const(0x0040)
SX126X_IRQ_TIMEOUT = const(0x0200)
SX126X_IRQ_ALL = const(0x03FF)

SX126X_STATUS_CMD_TIMEOUT = const(0x06)
SX126X_STATUS_CMD_INVALID = const(0x08)
SX126X_STATUS_CMD_FAILED = const(0x0A)

SX126X_REG_OCP_CONFIGURATION = const(0x08E7)
SX126X_REG_LORA_SYNC_WORD_MSB = const(0x0740)
SX126X_REG_TX_CLAMP_CONFIG = const(0x08D8)
SX126X_REG_SENSITIVITY_CONFIG = const(0x0889)
SX126X_LORA_SYNC_WORD_PRIVATE_MSB = const(0x14)
SX126X_LORA_SYNC_WORD_PRIVATE_LSB = const(0x24)
SX1262_PA_DUTY_CYCLE_22_DBM = const(0x04)
SX1262_PA_HP_MAX_22_DBM = const(0x07)
SX1262_PA_DEVICE_SEL = const(0x00)
SX1262_PA_LUT = const(0x01)
SX126X_PA_RAMP_200_US = const(0x04)

SX126X_STATE_UNINITIALIZED = const(0)
SX126X_STATE_STANDBY = const(1)
SX126X_STATE_RX = const(2)
SX126X_STATE_TX = const(3)
SX126X_STATE_SLEEP = const(4)
SX126X_STATE_ERROR = const(5)
SX126X_STATE_DEINITIALIZED = const(6)


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
