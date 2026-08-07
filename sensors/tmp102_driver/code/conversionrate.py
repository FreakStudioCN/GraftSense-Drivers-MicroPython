# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : conversionrate.py
# @Description : TMP102 转换速率配置扩展，提供 0.25/1/4/8 Hz 四档采样频率设置
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kevin Houlihan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import micropython

from _tmp102 import Tmp102
from _tmp102 import _set_bit_for_boolean

# ======================================== 全局变量 ============================================

# 配置寄存器 CR0/CR1 位掩码（config[1] bit 6~7）
_CR_BIT_0 = micropython.const(0x40)
_CR_BIT_1 = micropython.const(0x80)

# ======================================== 功能函数 ============================================


def _extend_class():
    """
    向 Tmp102 类注入转换速率常量与属性
    Notes:
        - 副作用：直接修改 Tmp102 类的属性和方法
        - 函数执行后自动删除自身
    ==========================================
    Inject conversion rate constants and property into Tmp102 class.
    Notes:
        - Side effect: directly modifies Tmp102 class attributes and methods
        - Self-deletes after execution
    """
    # ---- 类级速率常量注入 ----

    # 四档可选转换速率（CR0/CR1 = 00/01/10/11）
    Tmp102.CONVERSION_RATE_QUARTER_HZ = 0
    Tmp102.CONVERSION_RATE_1HZ = 1
    Tmp102.CONVERSION_RATE_4HZ = 2
    Tmp102.CONVERSION_RATE_8HZ = 3

    # ---- 转换速率配置 ----

    def _apply_conversion_rate(self, config: bytearray, rate: int) -> bytearray:
        """
        应用转换速率设置到配置字节
        Args:
            config (bytearray): 当前配置寄存器值
            rate (int): 速率值（0~3，对应 CONVERSION_RATE_* 常量）
        Returns:
            bytearray: 修改后的配置值
        ==========================================
        Apply conversion rate setting to config bytes.
        Args:
            config (bytearray): Current config register value
            rate (int): Rate value (0~3, matching CONVERSION_RATE_* constants)
        Returns:
            bytearray: Modified config value
        """
        # 计算 CR0 和 CR1 位各自的设定值
        bit_0_set = (rate << 6) & _CR_BIT_0
        bit_1_set = (rate << 6) & _CR_BIT_1
        # 分别设置 CR0（bit 6）和 CR1（bit 7）
        config[1] = _set_bit_for_boolean(config[1], _CR_BIT_0, bit_0_set)
        config[1] = _set_bit_for_boolean(config[1], _CR_BIT_1, bit_1_set)
        return config

    def _get_conversion_rate(self) -> int:
        """
        读取当前转换速率
        Returns:
            int: 速率值（0=0.25Hz, 1=1Hz, 2=4Hz, 3=8Hz）
        ==========================================
        Read the current conversion rate.
        Returns:
            int: Rate value (0=0.25Hz, 1=1Hz, 2=4Hz, 3=8Hz)
        """
        current_config = self._get_config()
        # 提取 CR0/CR1 位（config[1] bit 6~7）
        return current_config[1] >> 6

    def _set_conversion_rate(self, val: int) -> None:
        """
        设置转换速率
        Args:
            val (int): 速率值（Tmp102.CONVERSION_RATE_QUARTER_HZ ~ CONVERSION_RATE_8HZ）
        Notes:
            - 副作用：立即写入设备配置寄存器
        ==========================================
        Set the conversion rate.
        Args:
            val (int): Rate value (Tmp102.CONVERSION_RATE_QUARTER_HZ ~ CONVERSION_RATE_8HZ)
        Notes:
            - Side effect: immediately writes device config register
        """
        if not isinstance(val, int) or val < 0 or val > 3:
            raise ValueError("conversion rate must be an int from 0 to 3")
        self._set_config(_apply_conversion_rate(bytearray(self._get_config()), val))

    Tmp102._apply_conversion_rate = _apply_conversion_rate
    Tmp102.conversion_rate = property(_get_conversion_rate, _set_conversion_rate)


# 执行类扩展注入
_extend_class()
# 清理注入函数
del _extend_class

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
