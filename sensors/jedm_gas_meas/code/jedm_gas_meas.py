# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午2:21
# @Author  : leeqingshui
# @File    : jedm_gas_meas.py
# @Description : JED系列MEMS数字传感器模块的驱动代码
# @License : MIT

__version__ = "0.1.0"
__author__ = "leeqingshui"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time

# 导入硬件相关模块
from machine import SoftI2C, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class JEDMGasMeas:
    """
    JEDM气体传感器操作类
    支持读取气体浓度和校零校准功能，基于SoftI2C通信
    需要注意，该传感器模块仅适合于测试静态气体浓度，不适合于动态气体浓度测量，适合浓度分钟级～秒级变化

    Attributes:
    i2c (SoftI2C): I2C通信实例对象。
    _addr_7bit (int): 传感器的7位I2C地址。
    READ_CMD (int): 读取气体浓度的命令寄存器地址。
    CALIBRATE_CMD (int): 校零校准的命令寄存器地址。
    MAX_I2C_FREQ (int): I2C最大允许通信速率。
    CALIB_MIN (int): 校准值的最小范围。
    CALIB_MAX (int): 校准值的最大范围。

    Methods:
        __init__(self, i2c: SoftI2C, addr: int = 0x2A) -> None:
            初始化传感器并绑定I2C通信接口。
        read_concentration(self) -> int:
            读取气体浓度值。
        calibrate_zero(self, calib_value: int | None = None) -> bool:
            执行传感器的校零校准操作。

    Notes:
        该传感器模块适用于静态气体浓度测量，不适用于动态变化快速的气体浓度测量。
        建议在气体环境稳定后进行校零校准，以获得更准确的测量结果。
        通信速率限制为100KHz，使用时需确保I2C总线配置正确。

    ==========================================
    JED series MEMS digital gas sensor driver class.
    Supports reading gas concentration and zero calibration functions, based on SoftI2C communication protocol.

    Attributes:
        i2c (SoftI2C): I2C communication instance object.
        _addr_7bit (int): 7-bit I2C address of the sensor.
        READ_CMD (int): Command register address for reading gas concentration.
        CALIBRATE_CMD (int): Command register address for zero calibration.
        MAX_I2C_FREQ (int): Maximum allowed I2C communication rate.
        CALIB_MIN (int): Minimum range of calibration value.
        CALIB_MAX (int): Maximum range of calibration value.

    Methods:
        __init__(self, i2c: SoftI2C, addr: int = 0x2A) -> None:
            Initialize sensor and bind I2C communication interface.
        read_concentration(self) -> int:
            Read gas concentration value.
        calibrate_zero(self, calib_value: int | None = None) -> bool:
            Perform zero calibration operation of the sensor.

    Notes:
        This sensor module is suitable for static gas concentration measurement, not for rapidly changing dynamic gas concentration measurement.
        It is recommended to perform zero calibration when the gas environment is stable for more accurate measurement results.
        The communication rate is limited to 100KHz, ensure correct I2C bus configuration when using.

    """

    # 固定的命令寄存器地址（类属性）
    # 读取气体浓度的命令字
    READ_CMD: int = 0xA1
    # 校零校准的命令字
    CALIBRATE_CMD: int = 0x32
    # 类常量：I2C最大允许通信速率（100KHz）
    MAX_I2C_FREQ: int = 100000
    # 类常量：校准值的范围（16位无符号整数）
    CALIB_MIN: int = 0
    # 2^16 - 1
    CALIB_MAX: int = 65535

    def __init__(self, i2c: SoftI2C, addr: int = 0x2A) -> None:
        """
        初始化气体传感器并绑定I2C通信接口。

        Args:
            i2c (SoftI2C): SoftI2C实例（MicroPython的软I2C对象）。
            addr (int): 传感器的7位基础地址（不带读写位），默认为0x2A。

        Raises:
            TypeError: 如果i2c参数不是SoftI2C实例。

        ==========================================

        Initialize gas sensor and bind I2C communication interface.

        Args:
            i2c (SoftI2C): SoftI2C instance (MicroPython software I2C object).
            addr (int): 7-bit base address of the sensor (without R/W bit), default is 0x2A.

        Raises:
            TypeError: If i2c parameter is not a SoftI2C instance.
        """
        # 保存I2C实例和基础地址
        self.i2c: SoftI2C = i2c
        # 7位基础地址（私有属性）
        self._addr_7bit: int = addr

    def read_concentration(self) -> int:
        """
        读取气体浓度值，遵循传感器的I2C读取时序。

        Returns:
            int: 16位气体浓度值（高位*256 + 低位），读取失败返回0。

        Notes:
            使用标准的I2C重复起始条件进行读取操作。
            先发送读取命令，然后读取2个字节的数据。
            如果通信失败或数据不完整，会返回0并打印错误信息。

        ==========================================

        Read gas concentration value, following the sensor's I2C read timing.

        Returns:
            int: 16-bit gas concentration value (high byte * 256 + low byte), returns 0 if read fails.

        Notes:
            Uses standard I2C repeated start condition for read operation.
            First sends read command, then reads 2 bytes of data.
            If communication fails or data is incomplete, returns 0 and prints error message.
        """

        try:
            # 第一步：发送写操作（7位地址），写入读取命令，stop=False表示不发送停止位（实现重复起始）
            # writeto返回收到的ACK数量，需等于发送的字节数（这里是1个字节：READ_CMD）
            ack_count = self.i2c.writeto(self._addr_7bit, bytes([JEDMGasMeas.READ_CMD]), False)
            if ack_count != 1:
                raise OSError("No ACK for read command")

            # 第二步：发送读操作（7位地址），读取2个字节的浓度数据（高位+低位），stop=True发送停止位
            data = self.i2c.readfrom(self._addr_7bit, 2)
            if len(data) != 2:
                raise OSError("Incomplete data received")

            # 计算16位浓度值（高位左移8位 + 低位）
            concentration = (data[0] << 8) | data[1]
            return concentration
        except OSError as e:
            print(f"Failed to read concentration: {str(e)}")
            return 0

    def calibrate_zero(self, calib_value: int | None = None) -> bool:
        """
        执行传感器的校零校准操作。

        Args:
            calib_value (int | None): 校准值（16位整数），为None时使用当前读取的浓度值作为校准值。

        Returns:
            bool: 校准是否成功（True/False）。

        Raises:
            ValueError: 如果校准值超出0~65535范围。

        Notes:
            校零后会自动验证校准结果，读取当前浓度值应为0。
            如果验证失败，会打印警告信息并返回False。

        ==========================================

        Perform zero calibration operation of the sensor.

        Args:
            calib_value (int | None): Calibration value (16-bit integer), uses current read concentration value as calibration value if None.

        Returns:
            bool: Whether calibration succeeded (True/False).

        Raises:
            ValueError: If calibration value is outside 0~65535 range.

        Notes:
            Automatically verifies calibration result after zeroing, current read concentration value should be 0.
            If verification fails, prints warning message and returns False.
        """

        # 若未指定校准值，先读取当前浓度作为校准值
        if calib_value is None:
            calib_value = self.read_concentration()

        # 若校准值超过0~65535，需要抛出异常
        if calib_value > JEDMGasMeas.CALIB_MAX or calib_value < JEDMGasMeas.CALIB_MIN:
            raise ValueError("Calibration value must be between 0 and 65535")

        # 将16位校准值拆分为高8位和低8位（确保在0-255范围内）
        high_byte: int = (calib_value >> 8) & 0xFF
        low_byte: int = calib_value & 0xFF

        try:
            # 发送写操作，写入校零命令+校准值高低字节，stop=True发送停止位
            # 发送的字节序列：[校零命令, 高位字节, 低位字节]
            ack_count = self.i2c.writeto(self._addr_7bit, bytes([JEDMGasMeas.CALIBRATE_CMD, high_byte, low_byte]))
            # 检查ACK数量
            if ack_count != 1:
                raise OSError("No ACK for calibrate command or data")

            # 写入后，读取一次浓度值，确认校零成功（判断读取结果是否为0）
            post_calib_value = self.read_concentration()
            if post_calib_value != 0:
                print(f"Calibration confirmation failed: Read value {post_calib_value} is not 0")
                return False

            return True

        except OSError as e:
            print(f"Failed to calibrate zero: {str(e)}")
            return False


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
