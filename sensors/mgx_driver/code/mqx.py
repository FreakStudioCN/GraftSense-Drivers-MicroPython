# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/20 10:21
# @Author  : 缪贵成
# @File    : mqx.py
# @Description : MQ系列电化学传感器模块驱动程序
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

from micropython import schedule
from time import sleep_ms
from machine import Pin, ADC

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class MQX:
    """
    MQ 系列气体传感器驱动（安全版），支持 ADC 读取、电压转换、ppm 计算和中断回调。

    Attributes:
        adc (ADC): machine.ADC 实例，用于模拟输入。
        comp_pin (Pin): machine.Pin 实例，用于比较器数字输出。
        user_cb (Callable): 用户回调函数，参数为电压 (float)。
        rl (float): 负载电阻值，单位 Ω。
        vref (float): 参考电压，单位 V。
        _custom_poly (list[float]): 用户自定义多项式系数。
        _selected_builtin (str): 当前选择的内置传感器模型。
        last_raw (int): 最近一次 ADC 原始值。
        last_voltage (float): 最近一次电压值 (V)。

    Methods:
        read_voltage() -> float: 读取电压值 (V)。
        read_ppm(samples=1, delay_ms=0, sensor=None) -> float: 读取 ppm 浓度。
        select_builtin(name: str) -> None: 选择内置传感器模型。
        set_custom_polynomial(coeffs: list[float]) -> None: 设置用户自定义多项式。
        deinit() -> None: 释放传感器资源，取消中断。

    Notes:
        - 本类使用 micropython.schedule 保证中断安全。
        - 用户必须根据具体传感器环境自行标定多项式。

    ==========================================

    Safe driver for MQ gas sensors with ADC reading and comparator IRQ.

    Attributes:
        adc (ADC): machine.ADC instance for analog input.
        comp_pin (Pin): machine.Pin instance for digital comparator output.
        user_cb (Callable): user callback function, called with voltage (float).
        rl (float): Load resistor value in ohms.
        vref (float): Reference voltage in volts.
        _custom_poly (list[float]): User-defined polynomial coefficients.
        _selected_builtin (str): Currently selected builtin sensor model.
        last_raw (int): Last ADC raw value.
        last_voltage (float): Last measured voltage.

    Methods:
        read_voltage() -> float: Read voltage in volts.
        read_ppm(samples=1, delay_ms=0, sensor=None) -> float: Read gas concentration in ppm.
        select_builtin(name: str) -> None: Select builtin sensor polynomial.
        set_custom_polynomial(coeffs: list[float]) -> None: Set user-defined polynomial.
        deinit() -> None: Deinitialize sensor and disable IRQ.

    Notes:
        - Uses micropython.schedule to ensure IRQ safety.
        - Polynomial coefficients must be calibrated for actual environment.
    """

    _builtin_polys = {
        "MQ2": [0.0, 100.0, -20.0],
        "MQ4": [0.0, 200.0, -40.0],
        "MQ7": [0.0, 50.0, -8.0],
    }

    def __init__(self, adc, comp_pin, user_cb, rl_ohm=10000, vref=3.3, irq_trigger=None):
        """
        初始化 MQX 传感器对象。

        Args:
            adc (ADC): machine.ADC 实例，用于模拟输入。
            comp_pin (Pin): machine.Pin 实例，用于比较器数字输出。
            user_cb (Callable): 用户回调函数，参数为电压 (float)。
            rl_ohm (float, optional): 负载电阻，单位 Ω，默认 10kΩ。
            vref (float, optional): 参考电压，默认 3.3V。
            irq_trigger (int, optional): IRQ 触发方式（如 Pin.IRQ_RISING）。

        Returns:
            None

        Notes:
            - irq_trigger 为 None 时，默认绑定上升沿+下降沿。
            - 中断回调仅调度后台处理，避免阻塞。

        ==========================================

        Initialize MQX sensor object.

        Args:
            adc (ADC): machine.ADC instance for analog input.
            comp_pin (Pin): machine.Pin instance for digital comparator output.
            user_cb (Callable): user callback function, called with voltage (float).
            rl_ohm (float, optional): Load resistor in ohms. Default 10kΩ.
            vref (float, optional): Reference voltage in volts. Default 3.3V.
            irq_trigger (int, optional): IRQ trigger type (e.g., Pin.IRQ_RISING).

        Returns:
            None

        Note:
            - If irq_trigger is None, defaults to rising + falling edges.
            - IRQ handler only schedules work to ensure safety.
        """
        self.adc = adc
        self.comp_pin = comp_pin
        self.user_cb = user_cb
        self.rl = float(rl_ohm)
        self.vref = float(vref)
        self._custom_poly = None
        self._selected_builtin = None
        self.last_raw = None
        self.last_voltage = None

        if irq_trigger is None and Pin is not None:
            try:
                irq_trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING
            except Exception:
                irq_trigger = None

        if self.comp_pin is not None and irq_trigger is not None:
            self.comp_pin.irq(handler=self._irq, trigger=irq_trigger)

    def _read_raw(self):
        """
        读取 ADC 原始整数值。

        Returns:
            int: ADC 原始值。

        Raises:
            RuntimeError: 当 ADC 对象无效时。

        ==========================================

        Read raw ADC value.

        Returns:
            int: Raw ADC value.

        Raises:
            RuntimeError: If ADC object is invalid.
        """
        if self.adc is None:
            raise RuntimeError("ADC object is None")
        if hasattr(self.adc, "read_u16"):
            raw = self.adc.read_u16()
        elif hasattr(self.adc, "read"):
            raw = self.adc.read()
        else:
            raise RuntimeError("ADC object has no read_u16() or read()")
        self.last_raw = int(raw)
        return int(raw)

    def adc_raw_to_voltage(self, raw):
        """
        将原始 ADC 数值转换为电压。

        Args:
            raw (int): ADC 原始值。

        Returns:
            float: 电压值 (V)。

        ==========================================

        Convert raw ADC value to voltage.

        Args:
            raw (int): Raw ADC value.

        Returns:
            float: Voltage in volts.
        """
        maxv = 65535.0
        v = (raw / maxv) * self.vref
        return float(v)

    def read_voltage(self):
        """
        阻塞方式读取电压。

        Returns:
            float: 电压值 (V)。

        ==========================================

        Blocking read of voltage.

        Returns:
            float: Voltage in volts.
        """
        raw = self._read_raw()
        v = self.adc_raw_to_voltage(raw)
        self.last_voltage = v
        return v

    def _irq(self, pin):
        """
        中断回调函数，仅做最小工作。

        Args:
            pin (Pin): 触发中断的引脚。

        Notes:
            - 调度后台任务，避免在 ISR 中执行耗时操作。

        ==========================================

        IRQ callback (minimal work).

        Args:
            pin (Pin): Triggering pin.

        Note:
            - Defers heavy work via micropython.schedule.
        """
        try:
            raw = self._read_raw()
        except Exception:
            return
        try:
            schedule(self._scheduled_handler, raw)
        except Exception:
            try:
                v = self.adc_raw_to_voltage(raw)
                self.last_voltage = v
                self.user_cb(v)
            except Exception:
                pass

    def _scheduled_handler(self, raw):
        """
        调度处理函数（主线程执行）。

        Args:
            raw (int): ADC 原始值。

        ==========================================

        Scheduled handler (runs in main thread).

        Args:
            raw (int): Raw ADC value.
        """
        try:
            v = self.adc_raw_to_voltage(int(raw))
            self.last_voltage = v
            try:
                self.user_cb(v)
            except Exception:
                pass
        except Exception:
            pass

    def select_builtin(self, name):
        """
        选择内置传感器多项式。

        Args:
            name (str): 传感器类型，如 'MQ2'、'MQ4'、'MQ7'。

        Raises:
            ValueError: 当输入的名称未知时。

        ==========================================

        Select builtin polynomial by name.

        Args:
            name (str): Sensor type, e.g. 'MQ2','MQ4','MQ7'.

        Raises:
            ValueError: If unknown name is provided.
        """
        key = str(name).upper()
        if key not in self._builtin_polys:
            raise ValueError("unknown builtin key: " + str(name))
        self._selected_builtin = key
        self._custom_poly = None

    def set_custom_polynomial(self, coeffs):
        """
        设置用户自定义多项式。

        Args:
            coeffs (list[float]): 多项式系数 [a0, a1, a2, ...]。

        Returns:
            None

        ==========================================

        Set custom polynomial.

        Args:
            coeffs (list[float]): Polynomial coefficients [a0, a1, a2, ...].

        Returns:
            None
        """
        self._custom_poly = list(coeffs)
        self._selected_builtin = None

    def _get_active_poly(self):
        """
        获取当前生效的多项式。

        Returns:
            list[float] or None: 多项式系数。

        ==========================================

        Get active polynomial.

        Returns:
            list[float] or None: Polynomial coefficients.
        """
        if self._custom_poly is not None:
            return self._custom_poly
        if self._selected_builtin is not None:
            return list(self._builtin_polys[self._selected_builtin])
        return None

    @staticmethod
    def _eval_poly(coeffs, x):
        """
        计算多项式值。

        Args:
            coeffs (list[float]): 多项式系数。
            x (float): 输入电压。

        Returns:
            float: ppm 计算结果。

        ==========================================

        Evaluate polynomial.

        Args:
            coeffs (list[float]): Polynomial coefficients.
            x (float): Input value.

        Returns:
            float: Result in ppm.
        """
        res = 0.0
        p = 1.0
        for a in coeffs:
            res += a * p
            p *= x
        return res

    def read_ppm(self, samples=1, delay_ms=0, sensor=None):
        """
        读取气体浓度 (ppm)。

        Args:
            samples (int, optional): 平均采样数，默认 1。
            delay_ms (int, optional): 采样间延时，默认 0。
            sensor (str, optional): 临时传感器类型。

        Returns:
            float: ppm 值，失败时为 NaN。

        Raises:
            RuntimeError: 若没有可用多项式。

        ==========================================

        Read gas concentration (ppm).

        Args:
            samples (int, optional): Number of samples. Default 1.
            delay_ms (int, optional): Delay between samples (ms). Default 0.
            sensor (str, optional): Temporary sensor type.

        Returns:
            float: ppm value, NaN on failure.

        Raises:
            RuntimeError: If no polynomial available.
        """
        old_sel = self._selected_builtin
        old_custom = self._custom_poly

        if sensor is not None:
            self.select_builtin(sensor)

        coeffs = self._get_active_poly()
        if coeffs is None:
            self._selected_builtin = old_sel
            self._custom_poly = old_custom
            raise RuntimeError("unknown sensor or no polynomial coefficients")

        vals = []
        for _ in range(max(1, int(samples))):
            v = self.read_voltage()
            if v is None:
                continue
            try:
                ppm = float(self._eval_poly(coeffs, v))
            except Exception:
                ppm = float("nan")
            vals.append(ppm)
            if delay_ms:
                sleep_ms(int(delay_ms))

        self._selected_builtin = old_sel
        self._custom_poly = old_custom

        if not vals:
            return float("nan")
        return sum(vals) / len(vals)

    def deinit(self):
        """
        释放传感器，取消中断。

        Returns:
            None

        ==========================================

        Deinitialize sensor, disable IRQ.

        Returns:
            None
        """
        try:
            if self.comp_pin is not None:
                self.comp_pin.irq(handler=None)
        except Exception:
            pass
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================