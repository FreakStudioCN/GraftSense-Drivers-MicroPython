# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : Nelio Goncalves Godoi
# @File    : veml6075_lowmem.py
# @Description : VEML6075 紫外线传感器驱动（低内存版），直接 I2C 接口
# @License : MIT

__version__ = "0.0.1"
__author__ = "Nelio Goncalves Godoi"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from ustruct import unpack

# ======================================== 全局变量 ============================================

# 注意：低内存版不使用 micropython.const 和寄存器常量，直接内联寄存器地址以节省内存
# 积分时间（ms）到寄存器值映射
_VEML6075_UV_IT = {50: 0x00, 100: 0x01, 200: 0x02, 400: 0x03, 800: 0x04}

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class VEML6075:
    """
    VEML6075 紫外线传感器驱动类（低内存版），直接 I2C 接口
    Attributes:
        _i2c: I2C 总线实例
        _addr (int): 设备 I2C 地址，固定 0x10
        _a, _b (float): UVA 补偿系数
        _c, _d (float): UVB 补偿系数
        _uvaresp (float): UVA 响应系数
        _uvbresp (float): UVB 响应系数
    Methods:
        uva: 读取校准后 UVA 值
        uvb: 读取校准后 UVB 值
        uv_index: 读取计算后 UV 指数
        integration_time: 读取/设置积分时间（ms）
        deinit(): 关闭传感器
    Notes:
        - 低内存版：不使用 micropython.const，寄存器地址直接内联
        - 依赖外部传入 I2C 实例，不在内部创建总线
    ==========================================
    VEML6075 UV sensor driver (low-memory version), direct I2C interface.
    Notes:
        - Low-memory: no micropython.const, register addresses inlined
        - Requires externally provided I2C instance
    """

    def __init__(self, i2c, integration_time: int = 50, high_dynamic: bool = True,
                 uva_a_coef: float = 2.22, uva_b_coef: float = 1.33,
                 uvb_c_coef: float = 2.95, uvb_d_coef: float = 1.74,
                 uva_response: float = 0.001461, uvb_response: float = 0.002591) -> None:
        """
        初始化 VEML6075 传感器（低内存版）
        Args:
            i2c: MicroPython I2C 总线实例
            integration_time (int): 积分时间（ms），可选 50/100/200/400/800，默认 50
            high_dynamic (bool): 是否启用高动态范围模式，默认 True
            uva_a_coef (float): UVA 补偿系数 a，默认 2.22
            uva_b_coef (float): UVA 补偿系数 b，默认 1.33
            uvb_c_coef (float): UVB 补偿系数 c，默认 2.95
            uvb_d_coef (float): UVB 补偿系数 d，默认 1.74
            uva_response (float): UVA 响应系数，默认 0.001461
            uvb_response (float): UVB 响应系数，默认 0.002591
        Returns:
            None
        Raises:
            ValueError: i2c 不是有效 I2C 实例
            RuntimeError: 设备 ID 不匹配
        Notes:
            - ISR-safe: 否
            - 副作用：写入配置寄存器，启动传感器
        ==========================================
        Initialize VEML6075 sensor (low-memory version).
        """
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")

        self._addr = 0x10
        self._a = uva_a_coef
        self._b = uva_b_coef
        self._c = uvb_c_coef
        self._d = uvb_d_coef
        self._uvaresp = uva_response
        self._uvbresp = uvb_response
        self._uvacalc = None
        self._uvbcalc = None
        self._i2c = i2c

        # 校验设备 ID
        veml_id = self._read_register(0x0C)
        if veml_id != 0x26:
            raise RuntimeError("Incorrect VEML6075 ID 0x%02X" % veml_id)

        # 关闭传感器（进入 shutdown 状态以便配置）
        self._write_register(0x00, 0x01)

        # 设置积分时间
        self.integration_time = integration_time

        # 读取当前配置，按需启用高动态范围，然后上电
        conf = self._read_register(0x00)
        if high_dynamic:
            conf |= 0x08
        # 注意：清除 bit0（SD=0）使传感器上电工作
        conf &= ~0x01
        self._write_register(0x00, conf)

    def _take_reading(self) -> None:
        """
        执行一次完整的 UV 采样和补偿计算
        Notes:
            - ISR-safe: 否
        ==========================================
        Perform a full UV sampling and compensation calculation.
        """
        time.sleep(0.1)
        uva = self._read_register(0x07)
        uvb = self._read_register(0x09)
        uvcomp1 = self._read_register(0x0A)
        uvcomp2 = self._read_register(0x0B)
        # App Note 公式1&2：UVA/UVB 减去可见光和红外补偿
        self._uvacalc = uva - (self._a * uvcomp1) - (self._b * uvcomp2)
        self._uvbcalc = uvb - (self._c * uvcomp1) - (self._d * uvcomp2)

    @property
    def uva(self) -> float:
        """
        读取校准后 UVA 值（计数值）
        Returns:
            float: 校准后 UVA 计数值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read calibrated UVA value (counts).
        """
        self._take_reading()
        return self._uvacalc

    @property
    def uvb(self) -> float:
        """
        读取校准后 UVB 值（计数值）
        Returns:
            float: 校准后 UVB 计数值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read calibrated UVB value (counts).
        """
        self._take_reading()
        return self._uvbcalc

    @property
    def uv_index(self) -> float:
        """
        读取计算后 UV 指数
        Returns:
            float: UV 指数
        Notes:
            - ISR-safe: 否
        ==========================================
        Read calculated UV Index.
        """
        self._take_reading()
        return ((self._uvacalc * self._uvaresp) + (self._uvbcalc * self._uvbresp)) / 2

    @property
    def integration_time(self) -> int:
        """
        读取当前积分时间（ms）
        Returns:
            int: 积分时间，50/100/200/400/800 之一
        Raises:
            RuntimeError: 寄存器值无效
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current integration time (ms).
        """
        key = (self._read_register(0x00) >> 4) & 0x7
        for k, val in enumerate(_VEML6075_UV_IT):
            if key == k:
                return val
        raise RuntimeError("Invalid integration time")

    @integration_time.setter
    def integration_time(self, val: int) -> None:
        if val not in _VEML6075_UV_IT:
            raise ValueError("integration_time must be one of %s" % list(_VEML6075_UV_IT.keys()))
        conf = self._read_register(0x00)
        # 清除 bit4:6（积分时间字段）
        conf &= ~0b01110000
        conf |= _VEML6075_UV_IT[val] << 4
        self._write_register(0x00, conf)

    def _read_register(self, register: int) -> int:
        """
        读取 16 位寄存器（小端序）
        Args:
            register (int): 寄存器地址
        Returns:
            int: 16 位寄存器值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read 16-bit register (little-endian).
        """
        try:
            result = unpack('BB', self._i2c.readfrom_mem(self._addr, register, 2))
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % register) from e
        return (result[1] << 8) | result[0]

    def _write_register(self, register: int, value: int) -> None:
        """
        写入 16 位寄存器（小端序）
        Args:
            register (int): 寄存器地址
            value (int): 写入值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write 16-bit register (little-endian).
        """
        try:
            self._i2c.writeto_mem(self._addr, register, bytes([value, value >> 8]))
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % register) from e

    def deinit(self) -> None:
        """
        关闭传感器，进入 shutdown 模式
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：写入 SD=1，传感器停止采样
        ==========================================
        Shut down sensor (SD=1).
        """
        conf = self._read_register(0x00)
        self._write_register(0x00, conf | 0x01)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
