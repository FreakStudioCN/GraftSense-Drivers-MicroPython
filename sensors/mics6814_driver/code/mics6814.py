# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : hogeiha
# @File    : mics6814.py
# @Description : MiCS6814 CO、NH3、NO2 三通道 ADC 采集驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from machine import ADC, Pin

# ======================================== 全局变量 ============================================

# Pico ADC 16 位读取最大值，取值 65535
ADC_MAX_VALUE = 65535

# MiCS6814 模块默认负载电阻，取值 56000 欧姆
DEFAULT_LOAD_RESISTOR = 56000.0

# 默认 ADC 参考电压，取值 3.3V
DEFAULT_VREF = 3.3

# ======================================== 功能函数 ============================================


def _build_adc(pin) -> ADC:
    """
    根据传入引脚创建 ADC 对象。
    Args:
        pin (int | Pin | ADC): ADC 引脚编号、Pin 对象或 ADC 对象。

    Raises:
        ValueError: 参数为空时抛出。

    Notes:
        已创建的 ADC 对象会直接返回。

    ==========================================
    Create an ADC object from the input pin.
    Args:
        pin (int | Pin | ADC): ADC pin number, Pin object or ADC object.

    Raises:
        ValueError: Raised when the parameter is None.

    Notes:
        Existing ADC objects are returned directly.
    """
    if pin is None:
        raise ValueError("Pin cannot be None")

    if isinstance(pin, ADC):
        return pin

    if isinstance(pin, Pin):
        return ADC(pin)

    return ADC(Pin(pin))


# ======================================== 自定义类 ============================================


class Mics6814Reading:
    """
    MiCS6814 CO、NH3、NO2 三通道电阻读数结果。
    Attributes:
        co (float): CO 通道传感电阻值。
        nh3 (float): NH3 通道传感电阻值。
        no2 (float): NO2 通道传感电阻值。
        raw_co (int): CO 通道原始 ADC 值。
        raw_nh3 (int): NH3 通道原始 ADC 值。
        raw_no2 (int): NO2 通道原始 ADC 值。
        voltage_co (float): CO 通道电压值。
        voltage_nh3 (float): NH3 通道电压值。
        voltage_no2 (float): NO2 通道电压值。

    Methods:
        as_dict(): 返回字典格式的完整读数。

    Notes:
        电阻单位为欧姆，电压单位为伏。

    ==========================================
    MiCS6814 CO, NH3 and NO2 channel resistance reading result.
    Attributes:
        co (float): CO channel sensor resistance.
        nh3 (float): NH3 channel sensor resistance.
        no2 (float): NO2 channel sensor resistance.
        raw_co (int): Raw ADC value of CO channel.
        raw_nh3 (int): Raw ADC value of NH3 channel.
        raw_no2 (int): Raw ADC value of NO2 channel.
        voltage_co (float): Voltage of CO channel.
        voltage_nh3 (float): Voltage of NH3 channel.
        voltage_no2 (float): Voltage of NO2 channel.

    Methods:
        as_dict(): Return complete reading as a dictionary.

    Notes:
        Resistance is in ohms and voltage is in volts.
    """

    __slots__ = (
        "co",
        "nh3",
        "no2",
        "raw_co",
        "raw_nh3",
        "raw_no2",
        "voltage_co",
        "voltage_nh3",
        "voltage_no2",
    )

    def __init__(
        self,
        co: float,
        nh3: float,
        no2: float,
        raw_co: int,
        raw_nh3: int,
        raw_no2: int,
        voltage_co: float,
        voltage_nh3: float,
        voltage_no2: float,
    ) -> None:
        """
        初始化 MiCS6814 读数结果。
        Args:
            co (float): CO 通道传感电阻值。
            nh3 (float): NH3 通道传感电阻值。
            no2 (float): NO2 通道传感电阻值。
            raw_co (int): CO 通道原始 ADC 值。
            raw_nh3 (int): NH3 通道原始 ADC 值。
            raw_no2 (int): NO2 通道原始 ADC 值。
            voltage_co (float): CO 通道电压值。
            voltage_nh3 (float): NH3 通道电压值。
            voltage_no2 (float): NO2 通道电压值。

        Raises:
            无

        Notes:
            仅保存采集结果，不执行传感器采集。

        ==========================================
        Initialize MiCS6814 reading result.
        Args:
            co (float): CO channel sensor resistance.
            nh3 (float): NH3 channel sensor resistance.
            no2 (float): NO2 channel sensor resistance.
            raw_co (int): Raw ADC value of CO channel.
            raw_nh3 (int): Raw ADC value of NH3 channel.
            raw_no2 (int): Raw ADC value of NO2 channel.
            voltage_co (float): Voltage of CO channel.
            voltage_nh3 (float): Voltage of NH3 channel.
            voltage_no2 (float): Voltage of NO2 channel.

        Raises:
            None

        Notes:
            Stores sampling result only and does not sample the sensor.
        """
        self.co = co
        self.nh3 = nh3
        self.no2 = no2
        self.raw_co = raw_co
        self.raw_nh3 = raw_nh3
        self.raw_no2 = raw_no2
        self.voltage_co = voltage_co
        self.voltage_nh3 = voltage_nh3
        self.voltage_no2 = voltage_no2

    def as_dict(self) -> dict:
        """
        返回字典格式的完整读数。
        Args:
            无

        Raises:
            无

        Notes:
            适合串口打印或上传数据。

        ==========================================
        Return complete reading as a dictionary.
        Args:
            None

        Raises:
            None

        Notes:
            Suitable for serial printing or data upload.
        """
        return {
            "co": self.co,
            "nh3": self.nh3,
            "no2": self.no2,
            "raw_co": self.raw_co,
            "raw_nh3": self.raw_nh3,
            "raw_no2": self.raw_no2,
            "voltage_co": self.voltage_co,
            "voltage_nh3": self.voltage_nh3,
            "voltage_no2": self.voltage_no2,
        }

    def __repr__(self) -> str:
        return ("CO: {:.2f} Ohms\n" "NH3: {:.2f} Ohms\n" "NO2: {:.2f} Ohms").format(self.co, self.nh3, self.no2)

    __str__ = __repr__


class MICS6814:
    """
    MiCS6814 CO、NH3、NO2 三通道 ADC 采集驱动。
    Attributes:
        adc_co (ADC): CO 通道 ADC 对象。
        adc_nh3 (ADC): NH3 通道 ADC 对象。
        adc_no2 (ADC): NO2 通道 ADC 对象。
        vref (float): ADC 参考电压。
        load_resistor (float): 负载电阻值。
        samples (int): 单次读数平均采样次数。

    Methods:
        read_all(): 读取三个通道的气体电阻。
        read_raw_all(): 读取三个通道的原始 ADC 值。
        read_voltage_all(): 读取三个通道的电压值。
        read_co(): 读取 CO 通道电阻。
        read_nh3(): 读取 NH3 通道电阻。
        read_no2(): 读取 NO2 通道电阻。

    Notes:
        CO 对应原 reducing 通道，NO2 对应原 oxidising 通道。

    ==========================================
    MiCS6814 CO, NH3 and NO2 channel ADC sampling driver.
    Attributes:
        adc_co (ADC): ADC object for CO channel.
        adc_nh3 (ADC): ADC object for NH3 channel.
        adc_no2 (ADC): ADC object for NO2 channel.
        vref (float): ADC reference voltage.
        load_resistor (float): Load resistor value.
        samples (int): Average sample count per reading.

    Methods:
        read_all(): Read gas resistance from all three channels.
        read_raw_all(): Read raw ADC values from all three channels.
        read_voltage_all(): Read voltage values from all three channels.
        read_co(): Read CO channel resistance.
        read_nh3(): Read NH3 channel resistance.
        read_no2(): Read NO2 channel resistance.

    Notes:
        CO maps to the original reducing channel and NO2 maps to the original oxidising channel.
    """

    def __init__(
        self,
        co_pin,
        nh3_pin,
        no2_pin,
        vref: float = DEFAULT_VREF,
        load_resistor: float = DEFAULT_LOAD_RESISTOR,
        samples: int = 1,
    ) -> None:
        """
        初始化 MiCS6814 ADC 采集驱动。
        Args:
            co_pin (int | Pin | ADC): CO 通道 ADC 引脚。
            nh3_pin (int | Pin | ADC): NH3 通道 ADC 引脚。
            no2_pin (int | Pin | ADC): NO2 通道 ADC 引脚。
            vref (float): ADC 参考电压，默认 3.3V。
            load_resistor (float): 负载电阻值，默认 56000 欧姆。
            samples (int): 平均采样次数，默认 1。

        Raises:
            ValueError: 参数为空或取值非法时抛出。
            TypeError: 参数类型非法时抛出。

        Notes:
            Pico 常用 ADC 引脚为 GPIO26、GPIO27、GPIO28。

        ==========================================
        Initialize MiCS6814 ADC sampling driver.
        Args:
            co_pin (int | Pin | ADC): ADC pin for CO channel.
            nh3_pin (int | Pin | ADC): ADC pin for NH3 channel.
            no2_pin (int | Pin | ADC): ADC pin for NO2 channel.
            vref (float): ADC reference voltage, default 3.3V.
            load_resistor (float): Load resistor value, default 56000 ohms.
            samples (int): Average sample count, default 1.

        Raises:
            ValueError: Raised when a value is missing or out of range.
            TypeError: Raised when a parameter type is invalid.

        Notes:
            Common Pico ADC pins are GPIO26, GPIO27 and GPIO28.
        """
        if vref is None:
            raise ValueError("Vref cannot be None")

        if load_resistor is None:
            raise ValueError("Load resistor cannot be None")

        if samples is None:
            raise ValueError("Samples cannot be None")

        if not isinstance(samples, int):
            raise TypeError("Samples must be integer")

        if vref <= 0:
            raise ValueError("Vref must be greater than zero")

        if load_resistor <= 0:
            raise ValueError("Load resistor must be greater than zero")

        if samples < 1:
            raise ValueError("Samples must be greater than zero")

        self.adc_co = _build_adc(co_pin)
        self.adc_nh3 = _build_adc(nh3_pin)
        self.adc_no2 = _build_adc(no2_pin)
        self.vref = float(vref)
        self.load_resistor = float(load_resistor)
        self.samples = samples

    def _read_raw(self, adc: ADC) -> int:
        """
        读取单个 ADC 通道原始值。
        Args:
            adc (ADC): ADC 对象。

        Raises:
            ValueError: ADC 参数为空时抛出。

        Notes:
            当 samples 大于 1 时返回平均值。

        ==========================================
        Read raw value from one ADC channel.
        Args:
            adc (ADC): ADC object.

        Raises:
            ValueError: Raised when ADC parameter is None.

        Notes:
            Returns average value when samples is greater than one.
        """
        if adc is None:
            raise ValueError("Adc cannot be None")

        total = 0

        for _ in range(self.samples):
            total += adc.read_u16()

        return total // self.samples

    def _raw_to_voltage(self, raw: int) -> float:
        """
        将原始 ADC 值转换为电压。
        Args:
            raw (int): 原始 ADC 值。

        Raises:
            ValueError: 原始值为空或越界时抛出。
            TypeError: 原始值类型非法时抛出。

        Notes:
            Pico MicroPython 的 read_u16 返回 0 到 65535。

        ==========================================
        Convert raw ADC value to voltage.
        Args:
            raw (int): Raw ADC value.

        Raises:
            ValueError: Raised when raw value is None or out of range.
            TypeError: Raised when raw value type is invalid.

        Notes:
            Pico MicroPython read_u16 returns 0 to 65535.
        """
        if raw is None:
            raise ValueError("Raw value cannot be None")

        if not isinstance(raw, int):
            raise TypeError("Raw value must be integer")

        if raw < 0 or raw > ADC_MAX_VALUE:
            raise ValueError("Raw value out of range")

        return raw / ADC_MAX_VALUE * self.vref

    def _voltage_to_resistance(self, voltage: float) -> float:
        """
        将气体通道电压换算为传感电阻。
        Args:
            voltage (float): 气体通道电压值。

        Raises:
            ValueError: 电压参数为空或为负数时抛出。

        Notes:
            使用原驱动公式 voltage * load_resistor / (vref - voltage)。

        ==========================================
        Convert gas channel voltage to sensor resistance.
        Args:
            voltage (float): Gas channel voltage.

        Raises:
            ValueError: Raised when voltage is None or negative.

        Notes:
            Uses the original formula voltage * load_resistor / (vref - voltage).
        """
        if voltage is None:
            raise ValueError("Voltage cannot be None")

        if voltage < 0:
            raise ValueError("Voltage must not be negative")

        if voltage >= self.vref:
            return 0.0

        return voltage * self.load_resistor / (self.vref - voltage)

    def read_raw_all(self) -> dict:
        """
        读取 CO、NH3、NO2 三个通道的原始 ADC 值。
        Args:
            无

        Raises:
            无

        Notes:
            返回键名为 co、nh3 和 no2。

        ==========================================
        Read raw ADC values from CO, NH3 and NO2 channels.
        Args:
            None

        Raises:
            None

        Notes:
            Return keys are co, nh3 and no2.
        """
        return {
            "co": self._read_raw(self.adc_co),
            "nh3": self._read_raw(self.adc_nh3),
            "no2": self._read_raw(self.adc_no2),
        }

    def read_voltage_all(self) -> dict:
        """
        读取 CO、NH3、NO2 三个通道的电压值。
        Args:
            无

        Raises:
            无

        Notes:
            电压由原始 ADC 值按 vref 线性换算。

        ==========================================
        Read voltage values from CO, NH3 and NO2 channels.
        Args:
            None

        Raises:
            None

        Notes:
            Voltage is converted from raw ADC value with vref.
        """
        raw = self.read_raw_all()

        return {
            "co": self._raw_to_voltage(raw["co"]),
            "nh3": self._raw_to_voltage(raw["nh3"]),
            "no2": self._raw_to_voltage(raw["no2"]),
        }

    def read_all(self) -> Mics6814Reading:
        """
        读取 CO、NH3、NO2 三个通道的气体电阻。
        Args:
            无

        Raises:
            无

        Notes:
            返回值同时包含电阻、电压和原始 ADC 值。

        ==========================================
        Read gas resistance from CO, NH3 and NO2 channels.
        Args:
            None

        Raises:
            None

        Notes:
            Return value includes resistance, voltage and raw ADC values.
        """
        raw = self.read_raw_all()
        voltage = {
            "co": self._raw_to_voltage(raw["co"]),
            "nh3": self._raw_to_voltage(raw["nh3"]),
            "no2": self._raw_to_voltage(raw["no2"]),
        }

        return Mics6814Reading(
            self._voltage_to_resistance(voltage["co"]),
            self._voltage_to_resistance(voltage["nh3"]),
            self._voltage_to_resistance(voltage["no2"]),
            raw["co"],
            raw["nh3"],
            raw["no2"],
            voltage["co"],
            voltage["nh3"],
            voltage["no2"],
        )

    def read_co(self) -> float:
        """
        读取 CO 通道电阻。
        Args:
            无

        Raises:
            无

        Notes:
            CO 使用 MiCS6814 的还原性气体通道。

        ==========================================
        Read CO channel resistance.
        Args:
            None

        Raises:
            None

        Notes:
            CO uses the MiCS6814 reducing gas channel.
        """
        return self.read_all().co

    def read_nh3(self) -> float:
        """
        读取 NH3 通道电阻。
        Args:
            无

        Raises:
            无

        Notes:
            返回 MiCS6814 NH3 通道的传感电阻。

        ==========================================
        Read NH3 channel resistance.
        Args:
            None

        Raises:
            None

        Notes:
            Returns sensor resistance from MiCS6814 NH3 channel.
        """
        return self.read_all().nh3

    def read_no2(self) -> float:
        """
        读取 NO2 通道电阻。
        Args:
            无

        Raises:
            无

        Notes:
            NO2 使用 MiCS6814 的氧化性气体通道。

        ==========================================
        Read NO2 channel resistance.
        Args:
            None

        Raises:
            None

        Notes:
            NO2 uses the MiCS6814 oxidising gas channel.
        """
        return self.read_all().no2


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
