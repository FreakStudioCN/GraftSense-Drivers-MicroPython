# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : alert.py
# @Description : TMP102 温控器/告警功能扩展，提供温度阈值、告警极性与故障队列配置
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kevin Houlihan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

import micropython

# ======================================== 导入相关模块 =========================================
from _tmp102 import Tmp102
from _tmp102 import _set_bit_for_boolean

# ======================================== 全局变量 ============================================

# 温控器温度阈值寄存器地址
_REG_T_LOW = micropython.const(2)
_REG_T_HIGH = micropython.const(3)

# 配置寄存器位掩码
_POLARITY_BIT = micropython.const(0x04)
_THERMOSTAT_MODE_BIT = micropython.const(0x02)
_FAULT_QUEUE_BIT_0 = micropython.const(0x08)
_FAULT_QUEUE_BIT_1 = micropython.const(0x10)
_ALERT_BIT = micropython.const(0x20)

# ======================================== 功能函数 ============================================


def _extend_class():
    """
    向 Tmp102 类注入温控器/告警相关常量、方法与属性
    Notes:
        - 副作用：直接修改 Tmp102 类的属性和方法
        - 函数执行后自动删除自身，避免命名空间污染
    ==========================================
    Inject thermostat/alert constants, methods and properties into Tmp102 class.
    Notes:
        - Side effect: directly modifies Tmp102 class attributes and methods
        - Self-deletes after execution to avoid namespace pollution
    """
    # ---- 类级常量注入 ----

    # 故障队列长度选项
    Tmp102.FAULT_QUEUE_1 = 0
    Tmp102.FAULT_QUEUE_2 = 1
    Tmp102.FAULT_QUEUE_4 = 2
    Tmp102.FAULT_QUEUE_6 = 3

    # 温控器工作模式
    Tmp102.COMPARATOR_MODE = False
    Tmp102.INTERRUPT_MODE = True

    # 告警状态（注意：默认逻辑与直觉相反，参见数据手册）
    Tmp102.ALERT_HIGH = True
    Tmp102.ALERT_LOW = False

    # ---- 告警标志位读取 ----

    def _get_alert(self) -> bool:
        """
        读取告警标志位（ALERT bit）
        Returns:
            bool: 告警状态（True=ALERT_HIGH, False=ALERT_LOW）
        ==========================================
        Read the alert flag bit.
        Returns:
            bool: Alert status (True=ALERT_HIGH, False=ALERT_LOW)
        """
        # 读取配置寄存器并提取 ALERT 位（config[1] bit 5）
        current_config = self._get_config()
        return (current_config[1] & _ALERT_BIT) == _ALERT_BIT

    Tmp102.alert = property(_get_alert)

    # ---- 告警极性配置 ----

    def _apply_alert_polarity(self, config: bytearray, polarity_set: bool) -> bytearray:
        """
        应用告警极性设置到配置字节
        Args:
            config (bytearray): 当前配置寄存器值
            polarity_set (bool): 极性设置
        Returns:
            bytearray: 修改后的配置值
        ==========================================
        Apply alert polarity setting to config bytes.
        Args:
            config (bytearray): Current config register value
            polarity_set (bool): Polarity setting
        Returns:
            bytearray: Modified config value
        """
        # 修改 config[0] 的 POLARITY 位（bit 2）
        config[0] = _set_bit_for_boolean(config[0], _POLARITY_BIT, polarity_set)
        return config

    def _get_alert_polarity(self) -> bool:
        """
        读取告警极性设置
        Returns:
            bool: 当前极性（True=ALERT_HIGH, False=ALERT_LOW）
        ==========================================
        Read the alert polarity setting.
        Returns:
            bool: Current polarity (True=ALERT_HIGH, False=ALERT_LOW)
        """
        current_config = self._get_config()
        return (current_config[0] & _POLARITY_BIT) == _POLARITY_BIT

    def _set_alert_polarity(self, val: bool) -> None:
        """
        设置告警极性
        Args:
            val (bool): 极性值
        Notes:
            - 副作用：立即写入设备配置寄存器
        ==========================================
        Set the alert polarity.
        Args:
            val (bool): Polarity value
        Notes:
            - Side effect: immediately writes device config register
        """
        if not isinstance(val, bool):
            raise ValueError("alert polarity must be bool")
        # 读取当前配置 → 修改极性位 → 写回设备
        self._set_config(_apply_alert_polarity(bytearray(self._get_config()), val))

    Tmp102._apply_alert_polarity = _apply_alert_polarity
    Tmp102.alert_polarity = property(_get_alert_polarity, _set_alert_polarity)

    # ---- 温控器模式配置 ----

    def _apply_thermostat_mode(self, config: bytearray, mode_set: bool) -> bytearray:
        """
        应用温控器模式设置到配置字节
        Args:
            config (bytearray): 当前配置寄存器值
            mode_set (bool): 模式（True=中断模式, False=比较器模式）
        Returns:
            bytearray: 修改后的配置值
        ==========================================
        Apply thermostat mode setting to config bytes.
        Args:
            config (bytearray): Current config register value
            mode_set (bool): Mode (True=interrupt, False=comparator)
        Returns:
            bytearray: Modified config value
        """
        # 修改 config[0] 的 TM 位（bit 1）
        config[0] = _set_bit_for_boolean(config[0], _THERMOSTAT_MODE_BIT, mode_set)
        return config

    def _get_thermostat_mode(self) -> int:
        """
        读取温控器模式
        Returns:
            int: 当前模式值
        ==========================================
        Read the thermostat mode.
        Returns:
            int: Current mode value
        """
        current_config = self._get_config()
        return current_config[0] & _THERMOSTAT_MODE_BIT

    def _set_thermostat_mode(self, val: bool) -> None:
        """
        设置温控器模式
        Args:
            val (bool): 模式值（COMPARATOR_MODE 或 INTERRUPT_MODE）
        Notes:
            - 副作用：立即写入设备配置寄存器
        ==========================================
        Set the thermostat mode.
        Args:
            val (bool): Mode value (COMPARATOR_MODE or INTERRUPT_MODE)
        Notes:
            - Side effect: immediately writes device config register
        """
        if not isinstance(val, bool):
            raise ValueError("thermostat mode must be bool")
        self._set_config(_apply_thermostat_mode(bytearray(self._get_config()), val))

    Tmp102._apply_thermostat_mode = _apply_thermostat_mode
    Tmp102.thermostat_mode = property(_get_thermostat_mode, _set_thermostat_mode)

    # ---- 故障队列长度配置 ----

    def _apply_fault_queue_length(self, config: bytearray, length: int) -> bytearray:
        """
        应用故障队列长度设置到配置字节
        Args:
            config (bytearray): 当前配置寄存器值
            length (int): 故障队列长度（0~3，对应 1/2/4/6 次故障）
        Returns:
            bytearray: 修改后的配置值
        ==========================================
        Apply fault queue length setting to config bytes.
        Args:
            config (bytearray): Current config register value
            length (int): Fault queue length (0~3, for 1/2/4/6 faults)
        Returns:
            bytearray: Modified config value
        """
        # 计算 bit 3 和 bit 4 各自的目标值
        bit_0_set = (length << 3) & _FAULT_QUEUE_BIT_0
        bit_1_set = (length << 3) & _FAULT_QUEUE_BIT_1
        # 分别设置 F0 和 F1 位
        config[0] = _set_bit_for_boolean(config[0], _FAULT_QUEUE_BIT_0, bit_0_set)
        config[0] = _set_bit_for_boolean(config[0], _FAULT_QUEUE_BIT_1, bit_1_set)
        return config

    def _get_fault_queue_length(self) -> int:
        """
        读取故障队列长度
        Returns:
            int: 当前故障队列长度值（0~3）
        ==========================================
        Read the fault queue length.
        Returns:
            int: Current fault queue length (0~3)
        """
        current_config = self._get_config()
        # 提取 F0/F1 位（bit 3~4）并组合为整数值
        return (current_config[0] & (_FAULT_QUEUE_BIT_1 | _FAULT_QUEUE_BIT_0)) >> 3

    def _set_fault_queue_length(self, val: int) -> None:
        """
        设置故障队列长度
        Args:
            val (int): 故障队列长度（Tmp102.FAULT_QUEUE_1 ~ FAULT_QUEUE_6）
        Notes:
            - 副作用：立即写入设备配置寄存器
        ==========================================
        Set the fault queue length.
        Args:
            val (int): Fault queue length (Tmp102.FAULT_QUEUE_1 ~ FAULT_QUEUE_6)
        Notes:
            - Side effect: immediately writes device config register
        """
        if not isinstance(val, int) or val < 0 or val > 3:
            raise ValueError("fault queue length must be an int from 0 to 3")
        self._set_config(_apply_fault_queue_length(bytearray(self._get_config()), val))

    Tmp102._apply_fault_queue_length = _apply_fault_queue_length
    Tmp102.fault_queue_length = property(_get_fault_queue_length, _set_fault_queue_length)

    # ---- 温度阈值寄存器写入辅助方法 ----

    def _set_temperature_register(self, register: int, value: float) -> None:
        """
        将温度值编码为大端序格式并写入指定温度阈值寄存器
        Args:
            register (int): 目标温度寄存器地址
            value (float): 温度值（当前温度单位制）
        Raises:
            ValueError: 寄存器地址不可写
        Notes:
            - 副作用：立即写入设备寄存器
            - 通过 temperature_convertor 将当前单位制温度转换为摄氏温度
            - MicroPython 不支持大端序 to_bytes，手动进行字节序转换
        ==========================================
        Encode temperature value as big-endian and write to threshold register.
        Args:
            register (int): Target temperature register address
            value (float): Temperature in current unit scale
        Raises:
            ValueError: Register address is not writable
        Notes:
            - Side effect: immediately writes device register
            - Converts from current unit to Celsius via temperature_convertor
            - Manual byte-order swap since MicroPython lacks big-endian to_bytes
        """
        # 校验寄存器地址
        if register not in (_REG_T_HIGH, _REG_T_LOW):
            raise ValueError("Specified register cannot be set")
        # 若配置了单位转换器，将温度值转换回摄氏温度
        if self.temperature_convertor is not None:
            value = self.temperature_convertor.convert_from(value)
        if not isinstance(value, (int, float)):
            raise ValueError("temperature threshold must be int or float")
        # 根据扩展模式确定分辨率和移位量
        shift = 4
        if self._extended_mode:
            shift = 3
        raw_limit = 150.0 if self._extended_mode else 128.0
        if value < -25.0 or value > raw_limit:
            raise ValueError("temperature threshold is outside the TMP102 range")
        # 将温度转换为有效位的二进制补码，再移至寄存器高位。
        raw_bits = 13 if self._extended_mode else 12
        raw_temperature = int(value / 0.0625)
        raw_temperature &= (1 << raw_bits) - 1
        raw_temperature <<= shift
        rt = bytearray((raw_temperature >> 8, raw_temperature & 0xFF))
        # 写入目标温度阈值寄存器
        self._write_register(register, rt)

    Tmp102._set_temperature_register = _set_temperature_register

    # ---- 温控器高温阈值属性 ----

    def _get_thermostat_high_temperature(self) -> float:
        """
        读取温控器高温阈值
        Returns:
            float: 当前高温阈值温度
        ==========================================
        Read the thermostat high temperature threshold.
        Returns:
            float: Current high temperature threshold
        """
        _, t = self._read_temperature_register(_REG_T_HIGH)
        return t

    def _set_thermostat_high_temperature(self, val: float) -> None:
        """
        设置温控器高温阈值
        Args:
            val (float): 高温阈值温度值
        Notes:
            - 副作用：立即写入设备寄存器
        ==========================================
        Set the thermostat high temperature threshold.
        Args:
            val (float): High temperature threshold value
        Notes:
            - Side effect: immediately writes device register
        """
        _set_temperature_register(self, _REG_T_HIGH, val)

    Tmp102.thermostat_high_temperature = property(_get_thermostat_high_temperature, _set_thermostat_high_temperature)

    # ---- 温控器低温阈值属性 ----

    def _get_thermostat_low_temperature(self) -> float:
        """
        读取温控器低温阈值
        Returns:
            float: 当前低温阈值温度
        ==========================================
        Read the thermostat low temperature threshold.
        Returns:
            float: Current low temperature threshold
        """
        _, t = self._read_temperature_register(_REG_T_LOW)
        return t

    def _set_thermostat_low_temperature(self, val: float) -> None:
        """
        设置温控器低温阈值
        Args:
            val (float): 低温阈值温度值
        Notes:
            - 副作用：立即写入设备寄存器
        ==========================================
        Set the thermostat low temperature threshold.
        Args:
            val (float): Low temperature threshold value
        Notes:
            - Side effect: immediately writes device register
        """
        _set_temperature_register(self, _REG_T_LOW, val)

    Tmp102.thermostat_low_temperature = property(_get_thermostat_low_temperature, _set_thermostat_low_temperature)


# 执行类扩展注入
_extend_class()
# 清理注入函数，避免命名空间污染
del _extend_class

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
