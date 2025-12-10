# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午11:25
# @Author  : 缪贵成
# @File    : bmp280_float.py
# @Description : 基于BMP280的大气压强温湿度传感器模块驱动（浮点型版本），代码参考自：https://github.com/robert-hh/BME280/blob/master
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const
from struct import unpack, unpack_from
from array import array
from math import log
from math import pow

# ======================================== 全局变量 ============================================

# BMP280默认地址
BMP280_I2CADDR = 0x76

# 操作模式
BMP280_OSAMPLE_1 = 1
BMP280_OSAMPLE_2 = 2
BMP280_OSAMPLE_4 = 3
BMP280_OSAMPLE_8 = 4
BMP280_OSAMPLE_16 = 5

# 湿度数据的过采样
BMP280_REGISTER_CONTROL_HUM = 0xF2
BMP280_REGISTER_STATUS = 0xF3

# 通过0xF4寄存器的不同位配置从而实现对温度压力和湿度的过采样和模式控制 详细参考数据手册第3.3章节转换图
BMP280_REGISTER_CONTROL = 0xF4
MODE_SLEEP = const(0)
MODE_FORCED = const(1)
MODE_NORMAL = const(3)

# 阻塞时间
BMP280_TIMEOUT = const(100)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class BMP280:
    """
    该类控制 BMP280 大气压、温度和湿度传感器，提供浮点型数据读取接口。

    Attributes:
        i2c (I2C): machine.I2C 实例，用于总线通信。
        address (int): BMP280 I2C 地址。
        _mode_hum (int): 湿度采样模式。
        _mode_temp (int): 温度采样模式。
        _mode_press (int): 气压采样模式。
        __sealevel (int): 海平面标准气压，单位 Pa。
        t_fine (int): 温度微调变量，用于压力和湿度计算。
        _l1_barray (bytearray): 临时 1 字节缓冲区。
        _l8_barray (bytearray): 临时 8 字节缓冲区。
        _l3_resultarray (array): 临时数组用于存储原始读数。
        dig_T1..dig_T3, dig_P1..dig_P9, dig_H1..dig_H6: 校准参数，用于补偿计算。

    Methods:
        read_raw_data(result) -> None:
            读取原始传感器数据（温度、气压、湿度）。
        read_compensated_data(result=None) -> array:
            返回经过校准的浮点型温度(°C)、气压(Pa)和湿度(%)。
        sealevel(value: int) -> None:
            设置或获取海平面标准气压。
        altitude() -> float:
            根据当前气压计算海拔高度（米）。
        dew_point() -> float:
            计算露点温度（°C）。
        values() -> tuple:
            返回格式化的温度、气压、湿度字符串。

    Notes:
        - 调用方法会进行 I2C 读写操作，非 ISR-safe。
        - 类初始化时会加载校准数据并创建复用缓冲区，避免重复分配。
        - 海平面气压合理范围 30000~120000 Pa。
        - 湿度限制在 0~100% 范围内。

    ==========================================

    BMP280 driver for temperature, pressure, and humidity sensors (float version).

    Attributes:
        i2c (I2C): machine.I2C instance for bus communications.
        address (int): I2C address.
        _mode_hum (int): Humidity sampling mode.
        _mode_temp (int): Temperature sampling mode.
        _mode_press (int): Pressure sampling mode.
        __sealevel (int): Sea level standard pressure, in Pa.
        t_fine (int): Fine-tuned temperature used in pressure/humidity calculations.
        _l1_barray (bytearray): Temporary 1-byte buffer.
        _l8_barray (bytearray): Temporary 8-byte buffer.
        _l3_resultarray (array): Temporary array to hold raw readings.
        dig_T1..dig_T3, dig_P1..dig_P9, dig_H1..dig_H6: Calibration parameters.

    Methods:
        read_raw_data(result) -> None:Reads raw sensor data (temperature, pressure, humidity).
        read_compensated_data(result=None) -> array:Returns calibrated floating-point temperature (°C), pressure (Pa), and humidity (%).
        sealevel(value: int) -> None:Sets or gets the standard sea level pressure.
        altitude() -> float:Calculates the altitude (meters) based on the current pressure.
        dew_point() -> float:Calculates the dew point temperature (°C).
        values() -> tuple:Returns a formatted string of temperature, pressure, and humidity.

    Notes:
        - I2C operations are not ISR-safe.
        - Initialization loads calibration data and allocates reusable buffers.
        - Sea level pressure is reasonable between 30000~120000 Pa.
        - Humidity is clipped to 0~100%.
    """

    def __init__(self,
                 mode=BMP280_OSAMPLE_8,
                 address=None,
                 i2c=None,
                 **kwargs):
        """
        初始化 BMP280 传感器，加载校准数据并配置采样模式。

        Args:
            mode (int or tuple): 采样模式，可为单一模式或三元组 (hum, temp, press)。
            address (int): I2C 地址。
            i2c (I2C): machine.I2C 实例。
            **kwargs: 其他未使用参数。

        Raises:
            ValueError: 当 mode 类型 或 i2c参数不合法时抛出异常。

        Notes:
            - 初始化时会读取传感器校准寄存器。
            - 创建复用缓冲区以减少内存分配。
            - 非 ISR-safe。

        ==========================================

        Initialize BMP280 sensor, load calibration data, and set sampling mode.

        Args:
            mode (int or tuple): Sampling mode, single value or (hum, temp, press) tuple.
            address (int): I2C address.
            i2c (I2C): machine.I2C instance.
            **kwargs: other unused args.

        Raises:
            ValueError: Raises an exception when the mode type or i2c parameters are invalid.

        Notes:
            - Loads calibration registers.
            - Allocates reusable buffers.
            - Not ISR-safe.
        """
        # Check that mode is valid.
        if type(mode) is tuple and len(mode) == 3:
            self._mode_hum, self._mode_temp, self._mode_press = mode
        elif type(mode) == int:
            self._mode_hum, self._mode_temp, self._mode_press = mode, mode, mode
        else:
            raise ValueError("Wrong type for the mode parameter, must be int or a 3 element tuple")

        for mode in (self._mode_hum, self._mode_temp, self._mode_press):
            if mode not in [BMP280_OSAMPLE_1, BMP280_OSAMPLE_2, BMP280_OSAMPLE_4,
                            BMP280_OSAMPLE_8, BMP280_OSAMPLE_16]:
                raise ValueError(
                    'Unexpected mode value {0}. Set mode to one of '
                    'BMP280_OSAMPLE_1, BMP280_OSAMPLE_2, BMP280_OSAMPLE_4, '
                    'BMP280_OSAMPLE_8 or BMP280_OSAMPLE_16'.format(mode))

        self.address = address
        if i2c is None:
            raise ValueError('An I2C object is required.')
        self.i2c = i2c
        # 海平面大气压
        self.__sealevel = 101325
        # 加载校准数据
        # load calibration data
        dig_88_a1 = self.i2c.readfrom_mem(self.address, 0x88, 26)
        dig_e1_e7 = self.i2c.readfrom_mem(self.address, 0xE1, 7)

        self.dig_T1, self.dig_T2, self.dig_T3, self.dig_P1, \
            self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, \
            self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9, \
            _, self.dig_H1 = unpack("<HhhHhhhhhhhhBB", dig_88_a1)

        self.dig_H2, self.dig_H3, self.dig_H4,\
            self.dig_H5, self.dig_H6 = unpack("<hBbhb", dig_e1_e7)
        # unfold H4, H5, keeping care of a potential sign
        self.dig_H4 = (self.dig_H4 * 16) + (self.dig_H5 & 0xF)
        self.dig_H5 //= 16

        # temporary data holders which stay allocated
        self._l1_barray = bytearray(1)
        self._l8_barray = bytearray(8)
        self._l3_resultarray = array("i", [0, 0, 0])

        self._l1_barray[0] = self._mode_temp << 5 | self._mode_press << 2 | MODE_SLEEP
        self.i2c.writeto_mem(self.address, BMP280_REGISTER_CONTROL,
                             self._l1_barray)
        self.t_fine = 0

    def read_raw_data(self, result):
        """
        读取原始传感器数据到传入数组。

        Args:
            result (array): 长度为 3 的整型数组，用于存储原始温度、气压和湿度读数。

        Raises:
            RuntimeError: 当传感器未就绪时。

        Notes:
            - 调用会进行 I2C 写入控制寄存器和读取原始数据。
            - 非 ISR-safe。

        ==========================================

        Read raw temperature, pressure, and humidity data.

        Args:
            result (array): 3-element int array to hold raw data.

        Raises:
            RuntimeError: If sensor is not ready.

        Notes:
            Not ISR-safe.
        """
        self._l1_barray[0] = self._mode_hum
        self.i2c.writeto_mem(self.address, BMP280_REGISTER_CONTROL_HUM,
                             self._l1_barray)
        self._l1_barray[0] = self._mode_temp << 5 | self._mode_press << 2 | MODE_FORCED
        self.i2c.writeto_mem(self.address, BMP280_REGISTER_CONTROL,
                             self._l1_barray)

        # wait up to about 5 ms for the conversion to start
        for _ in range(5):
            if self.i2c.readfrom_mem(self.address, BMP280_REGISTER_STATUS, 1)[0] & 0x08:
                break  # The conversion is started.
            time.sleep_ms(1)  # still not busy
        # Wait for conversion to complete
        for _ in range(BMP280_TIMEOUT):
            if self.i2c.readfrom_mem(self.address, BMP280_REGISTER_STATUS, 1)[0] & 0x08:
                time.sleep_ms(10)  # still busy
            else:
                break  # Sensor ready
        else:
            raise RuntimeError("Sensor BMP280 not ready")

        # burst readout from 0xF7 to 0xFE, recommended by datasheet
        self.i2c.readfrom_mem_into(self.address, 0xF7, self._l8_barray)
        readout = self._l8_barray
        # pressure(0xF7): ((msb << 16) | (lsb << 8) | xlsb) >> 4
        raw_press = ((readout[0] << 16) | (readout[1] << 8) | readout[2]) >> 4
        # temperature(0xFA): ((msb << 16) | (lsb << 8) | xlsb) >> 4
        raw_temp = ((readout[3] << 16) | (readout[4] << 8) | readout[5]) >> 4
        # humidity(0xFD): (msb << 8) | lsb
        raw_hum = (readout[6] << 8) | readout[7]

        result[0] = raw_temp
        result[1] = raw_press
        result[2] = raw_hum
    def read_compensated_data(self, result=None):
        """
        返回经过校准的浮点型温度(°C)、气压(Pa)和湿度(%).

        Args:
            result (array, optional): 如果提供，将结果存入该数组，否则返回新 array("f")。

        Returns:
            array: 长度为 3 的浮点型数组 [温度, 气压, 湿度]。该方法存在返回值，但是由于不使用Typing从而无法进行返回值注解，对代码本身无影响。

        Notes:
            - 自动应用 BMP280 校准参数进行补偿。
            - 温度范围：-40~85 °C，气压范围：30000~110000 Pa，湿度范围：0~100%。
            - 非 ISR-safe。

        ==========================================

        Return compensated floating point temperature, pressure, and humidity.

        Args:
            result (array, optional): Array to store result. If None, returns new array.The method has a return value,
            but since Typing is not applicable, it cannot have a return value annotation, which has no effect on the code itself.

        Returns:
            array: 3-element float array [temperature, pressure, humidity].

        Notes:
            - Non-ISR-safe.
            - Automatically apply BMP280 calibration parameters for compensation.
            - Temperature range: -40~85 °C, pressure range: 30000~110000 Pa, humidity range: 0~100%.
        """
        self.read_raw_data(self._l3_resultarray)
        raw_temp, raw_press, raw_hum = self._l3_resultarray
        # temperature
        var1 = (raw_temp/16384.0 - self.dig_T1/1024.0) * self.dig_T2
        var2 = raw_temp/131072.0 - self.dig_T1/8192.0
        var2 = var2 * var2 * self.dig_T3
        self.t_fine = int(var1 + var2)
        temp = (var1 + var2) / 5120.0
        temp = max(-40, min(85, temp))

        # pressure
        var1 = (self.t_fine/2.0) - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0 + var1 * self.dig_P5 * 2.0
        var2 = (var2 / 4.0) + (self.dig_P4 * 65536.0)
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if (var1 == 0.0):
            pressure = 30000  # avoid exception caused by division by zero
        else:
            p = ((1048576.0 - raw_press) - (var2 / 4096.0)) * 6250.0 / var1
            var1 = self.dig_P9 * p * p / 2147483648.0
            var2 = p * self.dig_P8 / 32768.0
            pressure = p + (var1 + var2 + self.dig_P7) / 16.0
            pressure = max(30000, min(110000, pressure))

        # humidity
        h = (self.t_fine - 76800.0)
        h = ((raw_hum - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * h)) *
             (self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * h *
                                       (1.0 + self.dig_H3 / 67108864.0 * h))))
        humidity = h * (1.0 - self.dig_H1 * h / 524288.0)
        if (humidity < 0):
            humidity = 0
        if (humidity > 100):
            humidity = 100.0

        if result:
            result[0] = temp
            result[1] = pressure
            result[2] = humidity
            return result

        return array("f", (temp, pressure, humidity))

    @property
    def sealevel(self) -> int:
        """
        获取或返回海平面标准气压（Pa）。

        Returns:
            int: 当前设置的海平面气压，单位为帕（Pa）。

        Notes:
            - 海平面气压用于根据气压计算海拔。
            - 默认值为 101325 Pa。

        ==========================================

        Get or return the sea level standard pressure (Pa).

        Returns:
            int: Currently set sea level pressure in Pa.

        Notes:
            - Used to compute altitude from pressure.
            - Default value is 101325 Pa.
        """
        return self.__sealevel

    @sealevel.setter
    def sealevel(self, value):
        """
        设置海平面标准气压（Pa）。

        Args:
            value (int): 海平面气压值，单位 Pa，合理范围 30000 ~ 120000。

        Notes:
            - 设置值超出合理范围将被忽略。
            - 非 ISR-safe，需要在普通任务中调用。

        ==========================================

        Set sea level standard pressure (Pa).

        Args:
            value (int): Sea level pressure in Pa, reasonable range 30000 ~ 120000.

        Notes:
            - Values outside range are ignored.
            - Not ISR-safe.
        """
        # just ensure some reasonable value
        if 30000 < value < 120000:
            self.__sealevel = value

    @property
    def altitude(self) -> float:
        """
        根据当前气压计算海拔高度（米）。

        Returns:
            float: 海拔高度，单位米。如果读取传感器失败返回 0.0。

        Notes:
            - 使用公式: h = 44330 * (1 - (p / sealevel)^0.1903)
            - 海拔计算依赖于当前气压和设定的海平面气压。

        ==========================================

        Calculate altitude in meters from current pressure.

        Returns:
            float: Altitude in meters. Returns 0.0 if sensor read fails.

        Notes:
            - Formula used: h = 44330 * (1 - (p / sealevel)^0.1903)
            - Depends on current pressure and sea level setting.
        """

        try:
            p = 44330 * (1.0 - pow(self.read_compensated_data()[1] /
                                   self.__sealevel, 0.1903))
        except:
            p = 0.0
        return p

    @property
    def dew_point(self) -> float:
        """
        计算露点温度（°C）。

        Returns:
            float: 当前露点温度（°C）。

        Notes:
            - 使用 Magnus-Tetens 公式近似计算。
            - 依赖于当前温度和湿度读数。

        ==========================================

        Calculate dew point temperature (°C).

        Returns:
            float: Dew point temperature in °C.

        Notes:
            - Uses Magnus-Tetens approximation formula.
            - Depends on current temperature and humidity readings.
        """
        t, p, h = self.read_compensated_data()
        h = (log(h, 10) - 2) / 0.4343 + (17.62 * t) / (243.12 + t)
        return 243.12 * h / (17.62 - h)

    @property
    def values(self) -> tuple:
        """
        返回格式化的温度、气压、湿度字符串。

        Returns:
            tuple: 三元组 ("xx.xxC", "xxxx.xxhPa", "xx.xx%")。

        Notes:
            - 温度单位为摄氏度（°C）。
            - 气压单位为百帕（hPa）。
            - 湿度单位为百分比（%）。
            - 适用于直接显示或打印。

        ==========================================

        Return formatted temperature, pressure, and humidity strings.

        Returns:
            tuple: ("xx.xxC", "xxxx.xxhPa", "xx.xx%").

        Notes:
            - Temperature in °C, pressure in hPa, humidity in %.
            - Suitable for direct display or print.
        """
        t, p, h = self.read_compensated_data()

        return ("{:.2f}C".format(t), "{:.2f}hPa".format(p/100),
                "{:.2f}%".format(h))

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================

