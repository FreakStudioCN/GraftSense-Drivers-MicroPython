# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : oneshot.py
# @Description : TMP102 单次转换（One-Shot）功能扩展，支持关断模式下触发单次温度采样
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kevin Houlihan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

import micropython

# ======================================== 导入相关模块 =========================================
from _tmp102 import Tmp102
from _tmp102 import _set_bit_for_boolean
from shutdown import _SHUTDOWN_BIT

# ======================================== 全局变量 ============================================

# 单次转换触发位掩码（config[0] bit 7）
_ONE_SHOT_BIT = micropython.const(0x80)

# ======================================== 功能函数 ============================================


def _extend_class():
    """
    向 Tmp102 类注入单次转换方法与就绪状态属性
    Notes:
        - 副作用：直接修改 Tmp102 类的属性和方法
        - 必须在关断模式下使用，转换完成后设备保持关断状态
        - 依赖 tmp102.shutdown 模块提供关断位常量
        - 函数执行后自动删除自身
    ==========================================
    Inject one-shot conversion method and ready status property into Tmp102 class.
    Notes:
        - Side effect: directly modifies Tmp102 class attributes and methods
        - Must be in shutdown mode; device stays shut down after conversion
        - Depends on tmp102.shutdown module for shutdown bit constant
        - Self-deletes after execution
    """
    # ---- 单次转换触发 ----

    def initiate_conversion(self) -> None:
        """
        发起一次单次温度转换
        Raises:
            RuntimeError: 设备未处于关断模式时调用
        Notes:
            - 副作用：写入配置寄存器触发单次转换（OS 位）
            - 转换完成后设备自动回到关断模式
            - 可通过 conversion_ready 属性查询转换是否完成
        ==========================================
        Initiate a one-shot temperature conversion.
        Raises:
            RuntimeError: Device is not in shutdown mode
        Notes:
            - Side effect: writes config register to trigger one-shot (OS bit)
            - Device automatically returns to shutdown after conversion
            - Check conversion_ready property for completion status
        """
        # 读取当前配置
        current_config = self._get_config()
        # 校验设备处于关断模式
        if not current_config[0] & _SHUTDOWN_BIT:
            raise RuntimeError("Device must be shut down to initiate one-shot conversion")
        # 创建配置副本并置位 OS 位（bit 7）触发单次转换
        new_config = bytearray(current_config)
        new_config[0] = _set_bit_for_boolean(new_config[0], _ONE_SHOT_BIT, True)
        self._set_config(new_config)

    Tmp102.initiate_conversion = initiate_conversion

    # ---- 转换就绪状态查询 ----

    def _get_conversion_ready(self) -> bool:
        """
        查询单次转换是否已完成
        Returns:
            bool: True 表示转换完成（OS 位回到 1）
        ==========================================
        Check if one-shot conversion is complete.
        Returns:
            bool: True if conversion is complete (OS bit back to 1)
        """
        current_config = self._get_config()
        return (current_config[0] & _ONE_SHOT_BIT) == _ONE_SHOT_BIT

    Tmp102.conversion_ready = property(_get_conversion_ready)


# 执行类扩展注入
_extend_class()
# 清理注入函数
del _extend_class

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
