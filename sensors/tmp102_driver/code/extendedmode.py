# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : extendedmode.py
# @Description : TMP102 扩展模式（13-bit）配置扩展，提升温度测量上限至 150℃
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kevin Houlihan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
from _tmp102 import Tmp102
from _tmp102 import _set_bit_for_boolean, EXTENDED_MODE_BIT

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _extend_class():
    """
    向 Tmp102 类注入扩展模式属性
    Notes:
        - 副作用：直接修改 Tmp102 类的属性和方法
        - 扩展模式将温度分辨率从 12-bit 提升至 13-bit（上限 150℃）
        - 函数执行后自动删除自身
    ==========================================
    Inject extended mode property into Tmp102 class.
    Notes:
        - Side effect: directly modifies Tmp102 class attributes and methods
        - Extended mode improves resolution from 12-bit to 13-bit (max 150℃)
        - Self-deletes after execution
    """
    # ---- 扩展模式配置 ----

    def _apply_extended_mode(self, config: bytearray, mode_set: bool) -> bytearray:
        """
        应用扩展模式设置到配置字节
        Args:
            config (bytearray): 当前配置寄存器值
            mode_set (bool): True 启用扩展模式，False 使用正常模式
        Returns:
            bytearray: 修改后的配置值
        ==========================================
        Apply extended mode setting to config bytes.
        Args:
            config (bytearray): Current config register value
            mode_set (bool): True for extended mode, False for normal mode
        Returns:
            bytearray: Modified config value
        """
        # 修改 config[1] 的 EM 位（bit 4）
        config[1] = _set_bit_for_boolean(config[1], EXTENDED_MODE_BIT, mode_set)
        return config

    def _get_extended_mode(self) -> bool:
        """
        读取当前扩展模式状态
        Returns:
            bool: True 表示处于扩展模式（13-bit）
        ==========================================
        Read the current extended mode status.
        Returns:
            bool: True if in extended mode (13-bit)
        """
        # 直接返回由 _set_config 维护的实例属性
        return bool(self._extended_mode)

    def _set_extended_mode(self, val: bool) -> None:
        """
        设置扩展模式
        Args:
            val (bool): True 启用扩展模式（上限 150℃），False 使用正常模式（上限 128℃）
        Notes:
            - 副作用：立即写入设备配置寄存器
            - 写入后 _set_config 会自动更新 self._extended_mode
        ==========================================
        Set the extended mode.
        Args:
            val (bool): True for extended mode (max 150℃), False for normal (max 128℃)
        Notes:
            - Side effect: immediately writes device config register
            - _set_config automatically updates self._extended_mode after write
        """
        if not isinstance(val, bool):
            raise ValueError("extended mode must be bool")
        self._set_config(_apply_extended_mode(bytearray(self._get_config()), val))

    Tmp102._apply_extended_mode = _apply_extended_mode
    Tmp102.extended_mode = property(_get_extended_mode, _set_extended_mode)


# 执行类扩展注入
_extend_class()
# 清理注入函数
del _extend_class

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
