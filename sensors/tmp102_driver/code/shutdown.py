# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : shutdown.py
# @Description : TMP102 关断模式（Shutdown）配置扩展，支持低功耗休眠与唤醒
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

# 关断模式位掩码（config[0] bit 0）
_SHUTDOWN_BIT = micropython.const(0x01)

# ======================================== 功能函数 ============================================


def _extend_class():
    """
    向 Tmp102 类注入关断模式属性与方法
    Notes:
        - 副作用：直接修改 Tmp102 类的属性和方法
        - 关断模式下仅保持串行接口活动，温度转换停止以节省功耗
        - 唤醒后需等待首次转换完成才能读到有效温度
        - 函数执行后自动删除自身
    ==========================================
    Inject shutdown mode property and methods into Tmp102 class.
    Notes:
        - Side effect: directly modifies Tmp102 class attributes and methods
        - In shutdown mode only serial interface remains active to save power
        - After wake-up, first conversion must complete before valid temperature
        - Self-deletes after execution
    """
    # ---- 关断模式配置 ----

    def _apply_shutdown(self, config: bytearray, shutdown_set: bool) -> bytearray:
        """
        应用关断模式设置到配置字节
        Args:
            config (bytearray): 当前配置寄存器值
            shutdown_set (bool): True 进入关断模式，False 唤醒
        Returns:
            bytearray: 修改后的配置值
        ==========================================
        Apply shutdown mode setting to config bytes.
        Args:
            config (bytearray): Current config register value
            shutdown_set (bool): True to enter shutdown, False to wake
        Returns:
            bytearray: Modified config value
        """
        # 修改 config[0] 的 SD 位（bit 0）
        config[0] = _set_bit_for_boolean(config[0], _SHUTDOWN_BIT, shutdown_set)
        return config

    def _get_shutdown(self) -> bool:
        """
        读取当前关断模式状态
        Returns:
            bool: True 表示处于关断模式
        ==========================================
        Read the current shutdown mode status.
        Returns:
            bool: True if in shutdown mode
        """
        current_config = self._get_config()
        return (current_config[0] & _SHUTDOWN_BIT) == _SHUTDOWN_BIT

    def _set_shutdown(self, val: bool) -> None:
        """
        设置关断模式
        Args:
            val (bool): True 进入关断（低功耗），False 唤醒设备
        Notes:
            - 副作用：立即写入设备配置寄存器
            - 唤醒后温度转换不会立即就绪，需等待转换周期
        ==========================================
        Set shutdown mode.
        Args:
            val (bool): True to enter shutdown (low power), False to wake
        Notes:
            - Side effect: immediately writes device config register
            - After wake-up, temperature conversion needs time to complete
        """
        if not isinstance(val, bool):
            raise ValueError("shutdown must be bool")
        self._set_config(_apply_shutdown(bytearray(self._get_config()), val))

    Tmp102._apply_shutdown = _apply_shutdown
    Tmp102.shutdown = property(_get_shutdown, _set_shutdown)


# 执行类扩展注入
_extend_class()
# 清理注入函数
del _extend_class

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
