# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午2:21
# @Author  : hogeiha
# @File    : mems_air_module.py
# @Description : MEMS气体传感器及I2C多路复用器驱动代码，支持多类型气体检测、校零校准和多路通道管理
# @License : MIT

__version__ = "0.1.0"
__author__ = "leeqingshui"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import time
from machine import SoftI2C, Pin, Timer
from micropython import const

# ======================================== 自定义类 ============================================


class MEMSGasSensor:
    """
    MEMS气体传感器操作类
    支持多种气体类型的浓度读取和校零校准功能，基于SoftI2C通信协议
    传感器使用前需完成预热，通信速率限制为100KHz，确保I2C总线配置符合要求

    Attributes:
        TYPE_VOC (int): VOC气体类型标识常量。
        TYPE_H2 (int): 氢气(H2)气体类型标识常量。
        TYPE_CO (int): 一氧化碳(CO)气体类型标识常量。
        TYPE_NH3 (int): 氨气(NH3)气体类型标识常量。
        TYPE_H2S (int): 硫化氢(H2S)气体类型标识常量。
        TYPE_ETHANOL (int): 乙醇气体类型标识常量。
        TYPE_PROPANE (int): 丙烷气体类型标识常量。
        TYPE_FREON (int): 氟利昂气体类型标识常量。
        TYPE_NO2 (int): 二氧化氮(NO2)气体类型标识常量。
        TYPE_SMOKE (int): 烟雾气体类型标识常量。
        TYPE_HCHO (int): 甲醛(HCHO)气体类型标识常量。
        TYPE_ACETONE (int): 丙酮气体类型标识常量。
        ADDR7 (int): 传感器默认7位I2C地址（0x2A）。
        CMD_READ (int): 读取气体浓度的命令字（0xA1）。
        CMD_CAL (int): 校零校准的命令字（0x32）。
        PREHEAT_MS (int): 传感器预热时间（30000ms，即30秒）。
        OP_DELAY_MS (int): 传感器操作延迟时间（20ms）。
        MAX_I2C_FREQ (int): I2C最大允许通信速率（100000Hz）。
        CALIB_MIN (int): 校准值的最小范围（0）。
        CALIB_MAX (int): 校准值的最大范围（65535，2^16-1）。
        i2c (SoftI2C): I2C通信实例对象。
        addr (int): 传感器的7位I2C地址。
        sensor_type (int): 当前传感器检测的气体类型标识。

    Methods:
        __init__(self, i2c: SoftI2C, sensor_type: int, addr7: int = ADDR7) -> None:
            初始化传感器并绑定I2C通信接口，指定检测气体类型。
        read_concentration(self) -> int:
            读取当前气体浓度值，遵循传感器I2C读取时序。
        calibrate_zero(self, calib_value: int | None = None) -> bool:
            执行传感器校零校准操作，可选指定校准基准值。
        get_address(self) -> int:
            获取传感器的7位I2C地址。
        get_type(self) -> int:
            获取当前传感器检测的气体类型标识。

    Notes:
        传感器必须完成30秒预热后才能获得准确的浓度读数。
        校零校准建议在清洁空气环境中执行，校准后验证读数为0是理想状态，微小偏差属正常现象。
        支持的气体类型需使用类内置的TYPE_*常量，不可自定义数值。

    ==========================================
    MEMS Gas Sensor Operation Class
    Supports concentration reading and zero calibration for multiple gas types, based on SoftI2C communication protocol.
    The sensor must be preheated before use, the communication rate is limited to 100KHz, ensure I2C bus configuration meets requirements.

    Attributes:
        TYPE_VOC (int): VOC gas type identification constant.
        TYPE_H2 (int): Hydrogen (H2) gas type identification constant.
        TYPE_CO (int): Carbon monoxide (CO) gas type identification constant.
        TYPE_NH3 (int): Ammonia (NH3) gas type identification constant.
        TYPE_H2S (int): Hydrogen sulfide (H2S) gas type identification constant.
        TYPE_ETHANOL (int): Ethanol gas type identification constant.
        TYPE_PROPANE (int): Propane gas type identification constant.
        TYPE_FREON (int): Freon gas type identification constant.
        TYPE_NO2 (int): Nitrogen dioxide (NO2) gas type identification constant.
        TYPE_SMOKE (int): Smoke gas type identification constant.
        TYPE_HCHO (int): Formaldehyde (HCHO) gas type identification constant.
        TYPE_ACETONE (int): Acetone gas type identification constant.
        ADDR7 (int): Sensor default 7-bit I2C address (0x2A).
        CMD_READ (int): Command word for reading gas concentration (0xA1).
        CMD_CAL (int): Command word for zero calibration (0x32).
        PREHEAT_MS (int): Sensor preheating time (30000ms, i.e., 30 seconds).
        OP_DELAY_MS (int): Sensor operation delay time (20ms).
        MAX_I2C_FREQ (int): Maximum allowed I2C communication rate (100000Hz).
        CALIB_MIN (int): Minimum range of calibration value (0).
        CALIB_MAX (int): Maximum range of calibration value (65535, 2^16-1).
        i2c (SoftI2C): I2C communication instance object.
        addr (int): 7-bit I2C address of the sensor.
        sensor_type (int): Gas type identification for current sensor detection.

    Methods:
        __init__(self, i2c: SoftI2C, sensor_type: int, addr7: int = ADDR7) -> None:
            Initialize sensor and bind I2C communication interface, specify detection gas type.
        read_concentration(self) -> int:
            Read current gas concentration value, following the sensor's I2C read timing.
        calibrate_zero(self, calib_value: int | None = None) -> bool:
            Perform sensor zero calibration operation, optionally specify calibration reference value.
        get_address(self) -> int:
            Get the 7-bit I2C address of the sensor.
        get_type(self) -> int:
            Get the gas type identification of current sensor detection.

    Notes:
        The sensor must complete 30 seconds of preheating to obtain accurate concentration readings.
        Zero calibration is recommended to be performed in clean air environment, it is ideal to verify the reading is 0 after calibration, minor deviations are normal.
        Supported gas types must use the built-in TYPE_* constants of the class, custom values are not allowed.
    """

    # 气体类型标识常量
    TYPE_VOC = const(1)
    TYPE_H2 = const(2)
    TYPE_CO = const(3)
    TYPE_NH3 = const(4)
    TYPE_H2S = const(5)
    TYPE_ETHANOL = const(6)
    TYPE_PROPANE = const(7)
    TYPE_FREON = const(8)
    TYPE_NO2 = const(9)
    TYPE_SMOKE = const(10)
    TYPE_HCHO = const(11)
    TYPE_ACETONE = const(12)

    # 传感器通信配置常量
    ADDR7 = const(0x2A)
    CMD_READ = const(0xA1)
    CMD_CAL = const(0x32)
    PREHEAT_MS = const(30000)
    OP_DELAY_MS = const(20)

    # 校准与通信速率限制常量
    MAX_I2C_FREQ = const(100000)
    CALIB_MIN: int = 0
    CALIB_MAX: int = 65535

    def __init__(self, i2c: SoftI2C, sensor_type: int, addr7: int = ADDR7) -> None:
        """
        初始化传感器并绑定I2C通信接口，指定检测气体类型。

        Args:
            i2c (SoftI2C): SoftI2C实例（MicroPython的软I2C对象）。
            sensor_type (int): 气体类型标识，必须使用类内置的TYPE_*常量。
            addr7 (int): 传感器的7位I2C地址，默认为0x2A。

        Raises:
            TypeError: 如果i2c参数不是SoftI2C实例。
            ValueError: 如果sensor_type不是类内置的TYPE_*常量。

        ==========================================
        Initialize sensor and bind I2C communication interface, specify detection gas type.

        Args:
            i2c (SoftI2C): SoftI2C instance (MicroPython software I2C object).
            sensor_type (int): Gas type identification, must use built-in TYPE_* constants of the class.
            addr7 (int): 7-bit I2C address of the sensor, default is 0x2A.

        Raises:
            TypeError: If i2c parameter is not a SoftI2C instance.
            ValueError: If sensor_type is not a built-in TYPE_* constant of the class.
        """
        # 验证I2C实例类型
        if not isinstance(i2c, SoftI2C):
            raise TypeError("i2c must be a SoftI2C instance")

        # 验证气体类型合法性
        valid_types = {
            MEMSGasSensor.TYPE_VOC,
            MEMSGasSensor.TYPE_H2,
            MEMSGasSensor.TYPE_CO,
            MEMSGasSensor.TYPE_NH3,
            MEMSGasSensor.TYPE_H2S,
            MEMSGasSensor.TYPE_ETHANOL,
            MEMSGasSensor.TYPE_PROPANE,
            MEMSGasSensor.TYPE_FREON,
            MEMSGasSensor.TYPE_NO2,
            MEMSGasSensor.TYPE_SMOKE,
            MEMSGasSensor.TYPE_HCHO,
            MEMSGasSensor.TYPE_ACETONE,
        }
        if sensor_type not in valid_types:
            raise ValueError(f"Invalid sensor_type {sensor_type}, use TYPE_* constants")

        # 初始化实例属性
        self.i2c: SoftI2C = i2c
        self.addr: int = addr7
        self.sensor_type: int = sensor_type

    def read_concentration(self) -> int:
        """
        读取当前气体浓度值，遵循传感器I2C读取时序。

        Returns:
            int: 16位气体浓度值（高位*256 + 低位），读取失败返回0。

        Notes:
            使用I2C重复起始条件进行读取操作，先发送读取命令，再读取2字节数据。
            通信失败或数据不完整时会打印错误信息并返回0。

        ==========================================
        Read current gas concentration value, following the sensor's I2C read timing.

        Returns:
            int: 16-bit gas concentration value (high byte * 256 + low byte), returns 0 if read fails.

        Notes:
            Uses I2C repeated start condition for read operation, first sends read command, then reads 2 bytes of data.
            Prints error message and returns 0 when communication fails or data is incomplete.
        """
        try:
            # 发送读取命令（不发送停止位，实现重复起始）
            ack_count = self.i2c.writeto(self.addr, bytes([MEMSGasSensor.CMD_READ]), False)
            if ack_count != 1:
                raise OSError("No ACK for read command")

            # 读取2字节浓度数据（高位+低位）
            data = self.i2c.readfrom(self.addr, 2)
            if len(data) != 2:
                raise OSError("Incomplete data received")

            # 计算16位浓度值
            concentration = (data[0] << 8) | data[1]
            return concentration
        except OSError as e:
            print(f"Failed to read concentration: {str(e)}")
            return 0

    def calibrate_zero(self, calib_value: int | None = None) -> bool:
        """
        执行传感器校零校准操作，可选指定校准基准值。

        Args:
            calib_value (int | None): 校准值（16位整数），为None时使用当前读取的浓度值作为校准值。

        Returns:
            bool: 校准是否成功（True/False）。

        Raises:
            ValueError: 如果校准值超出0~65535范围。

        Notes:
            校零后会读取浓度值验证结果，理想状态下读数应为0，微小偏差属正常现象。
            校准命令需发送3字节数据:校零命令字 + 校准值高位 + 校准值低位。

        ==========================================
        Perform sensor zero calibration operation, optionally specify calibration reference value.

        Args:
            calib_value (int | None): Calibration value (16-bit integer), uses current read concentration value as calibration value if None.

        Returns:
            bool: Whether calibration succeeded (True/False).

        Raises:
            ValueError: If calibration value is outside 0~65535 range.

        Notes:
            Reads concentration value to verify result after zeroing, ideally the reading should be 0, minor deviations are normal.
            Calibration command needs to send 3 bytes of data: zero calibration command word + high byte of calibration value + low byte of calibration value.
        """
        # 若未指定校准值，读取当前浓度作为基准
        if calib_value is None:
            calib_value = self.read_concentration()

        # 验证校准值范围
        if calib_value > MEMSGasSensor.CALIB_MAX or calib_value < MEMSGasSensor.CALIB_MIN:
            raise ValueError("Calibration value must be between 0 and 65535")

        # 拆分校准值为高低字节
        high_byte: int = (calib_value >> 8) & 0xFF
        low_byte: int = calib_value & 0xFF

        try:
            # 发送校零命令+校准值（共3字节）
            ack_count = self.i2c.writeto(self.addr, bytes([MEMSGasSensor.CMD_CAL, high_byte, low_byte]))
            if ack_count != 1:
                raise OSError("No ACK for calibrate command or data")

            # 验证校准结果
            post_calib_value = self.read_concentration()
            if post_calib_value != 0:
                print(f"Calibration confirmation failed: Read value {post_calib_value} is not 0")
                return False

            return True

        except OSError as e:
            print(f"Failed to calibrate zero: {str(e)}")
            return False

    def get_address(self) -> int:
        """
        获取传感器的7位I2C地址。

        Returns:
            int: 传感器当前使用的7位I2C地址。

        ==========================================
        Get the 7-bit I2C address of the sensor.

        Returns:
            int: 7-bit I2C address currently used by the sensor.
        """
        return self.addr

    def get_type(self) -> int:
        """
        获取当前传感器检测的气体类型标识。

        Returns:
            int: 气体类型标识（对应类内置的TYPE_*常量）。

        ==========================================
        Get the gas type identification of current sensor detection.

        Returns:
            int: Gas type identification (corresponding to the built-in TYPE_* constants of the class).
        """
        return self.sensor_type


class PCA9546ADR:
    """
    PCA9546ADR I2C多路复用器操作类
    支持4通道I2C通道切换、禁用所有通道和读取通道状态功能，用于扩展I2C设备数量

    Attributes:
        addr7 (int): 多路复用器默认7位I2C地址（0x70）。
        MAX_CH (int): 最大支持通道数（4）。
        i2c (SoftI2C): I2C通信实例对象。
        addr (int): 多路复用器的7位I2C地址。
        _current_mask (int): 当前通道掩码（低4位有效）。

    Methods:
        __init__(self, i2c, addr=addr7):
            初始化多路复用器并绑定I2C通信接口。
        write_ctl(self, ctl_byte):
            写入通道控制字节，设置多路复用器通道状态。
        select_channel(self, ch):
            选择单个I2C通道（0-3），自动禁用其他通道。
        disable_all(self):
            禁用所有I2C通道。
        read_status(self):
            读取当前通道状态掩码。
        current_mask(self):
            获取当前通道掩码。

    Notes:
        通道控制字节仅低4位有效，每一位对应一个通道（0位=通道0，1位=通道1，依此类推）。
        切换通道后建议等待10ms确保通道切换完成，避免I2C通信冲突。

    ==========================================
    PCA9546ADR I2C Multiplexer Operation Class
    Supports 4-channel I2C channel switching, disabling all channels and reading channel status functions, used to expand the number of I2C devices.

    Attributes:
        addr7 (int): Multiplexer default 7-bit I2C address (0x70).
        MAX_CH (int): Maximum supported channels (4).
        i2c (SoftI2C): I2C communication instance object.
        addr (int): 7-bit I2C address of the multiplexer.
        _current_mask (int): Current channel mask (lower 4 bits valid).

    Methods:
        __init__(self, i2c, addr=addr7):
            Initialize multiplexer and bind I2C communication interface.
        write_ctl(self, ctl_byte):
            Write channel control byte to set multiplexer channel status.
        select_channel(self, ch):
            Select a single I2C channel (0-3), automatically disable other channels.
        disable_all(self):
            Disable all I2C channels.
        read_status(self):
            Read current channel status mask.
        current_mask(self):
            Get current channel mask.

    Notes:
        Only the lower 4 bits of the channel control byte are valid, each bit corresponds to a channel (bit 0 = channel 0, bit 1 = channel 1, and so on).
        It is recommended to wait 10ms after switching channels to ensure the channel switch is completed and avoid I2C communication conflicts.
    """

    # 多路复用器配置常量
    addr7 = const(0x70)
    MAX_CH = const(4)

    def __init__(self, i2c, addr=addr7):
        """
        初始化多路复用器并绑定I2C通信接口。

        Args:
            i2c (SoftI2C): SoftI2C实例（MicroPython的软I2C对象）。
            addr (int): 多路复用器的7位I2C地址，默认为0x70。

        ==========================================
        Initialize multiplexer and bind I2C communication interface.

        Args:
            i2c (SoftI2C): SoftI2C instance (MicroPython software I2C object).
            addr (int): 7-bit I2C address of the multiplexer, default is 0x70.
        """
        self.i2c = i2c
        self.addr = addr
        self._current_mask = 0x00

    def write_ctl(self, ctl_byte):
        """
        写入通道控制字节，设置多路复用器通道状态。

        Args:
            ctl_byte (int): 通道控制字节（仅低4位有效）。

        Raises:
            OSError: I2C写入失败时抛出异常。

        Notes:
            控制字节低4位分别对应4个通道，1表示启用对应通道，0表示禁用。
            例如:0x01=启用通道0，0x02=启用通道1，0x00=禁用所有通道。

        ==========================================
        Write channel control byte to set multiplexer channel status.

        Args:
            ctl_byte (int): Channel control byte (only lower 4 bits valid).

        Raises:
            OSError: Throws exception when I2C write fails.

        Notes:
            The lower 4 bits of the control byte correspond to 4 channels respectively, 1 means enable the corresponding channel, 0 means disable.
            For example: 0x01 = enable channel 0, 0x02 = enable channel 1, 0x00 = disable all channels.
        """
        ctl = int(ctl_byte) & 0x0F  # 仅保留低4位
        try:
            self.i2c.writeto(self.addr, bytearray([ctl]))
        except OSError as e:
            # 抛出异常供上层处理
            raise
        else:
            # 更新当前通道掩码
            self._current_mask = ctl

    def select_channel(self, ch):
        """
        选择单个I2C通道（0-3），自动禁用其他通道。

        Args:
            ch (int): 通道号（0-3）。

        Raises:
            ValueError: 如果通道号超出0-3范围。
            OSError: I2C写入失败时抛出异常。

        ==========================================
        Select a single I2C channel (0-3), automatically disable other channels.

        Args:
            ch (int): Channel number (0-3).

        Raises:
            ValueError: If channel number is out of 0-3 range.
            OSError: Throws exception when I2C write fails.
        """
        if ch < 0 or ch >= PCA9546ADR.MAX_CH:
            raise ValueError("Invalid channel")
        self.write_ctl(1 << ch)

    def disable_all(self):
        """
        禁用所有I2C通道。

        Raises:
            OSError: I2C写入失败时抛出异常。

        ==========================================
        Disable all I2C channels.

        Raises:
            OSError: Throws exception when I2C write fails.
        """
        self.write_ctl(0x00)

    def read_status(self):
        """
        读取当前通道状态掩码。

        Returns:
            int: 通道状态掩码（低4位有效）。

        Raises:
            OSError: I2C读取失败时抛出异常。

        Notes:
            返回值低4位对应4个通道的启用状态，1=启用，0=禁用。

        ==========================================
        Read current channel status mask.

        Returns:
            int: Channel status mask (lower 4 bits valid).

        Raises:
            OSError: Throws exception when I2C read fails.

        Notes:
            The lower 4 bits of the return value correspond to the enable status of 4 channels, 1 = enable, 0 = disable.
        """
        try:
            b = self.i2c.readfrom(self.addr, 1)
        except OSError as e:
            # 抛出异常供上层处理
            raise
        else:
            status = b[0] & 0x0F
            self._current_mask = status
            return status

    def current_mask(self):
        """
        获取当前通道掩码。

        Returns:
            int: 当前通道掩码（低4位有效）。

        ==========================================
        Get current channel mask.

        Returns:
            int: Current channel mask (lower 4 bits valid).
        """
        return self._current_mask


class AirQualityMonitor:
    """
    空气质量监测器类
    整合I2C多路复用器和多个MEMS气体传感器，实现多通道传感器注册、数据读取和校准管理

    Attributes:
        RESTART_DELAY_MS (int): 重启延迟时间（5000ms，即5秒）。
        i2c (SoftI2C): I2C通信实例对象。
        pca (PCA9546ADR): PCA9546ADR多路复用器实例。
        sensors (dict): 传感器注册表，{通道号: 传感器实例}。
        channel_map (dict): 气体类型-通道映射表，{传感器类型: 通道号}。
        enabled_mask (int): 启用的通道掩码。
        _restart_pending (bool): 是否有重启操作待执行。
        _restart_target_mask (int): 重启目标通道掩码。
        _restart_start_time (int): 重启开始时间戳。

    Methods:
        __init__(self, i2c, pca_addr=PCA9546ADR.addr7):
            初始化空气质量监测器，绑定I2C接口和多路复用器。
        register_sensor(self, channel, sensor_type, sensor_addr=MEMSGasSensor.ADDR7):
            将指定类型的传感器注册到多路复用器指定通道。
        read_sensor(self, sensor_type):
            读取指定气体类型传感器的浓度值。
        read_all(self):
            读取所有已注册传感器的浓度值，返回映射字典。
        calibrate_sensor(self, sensor_type):
            校准指定气体类型的传感器。
        _sensor_type_name(self, sensor_type):
            将传感器类型常量转换为易读的名称（内部方法）。

    Notes:
        注册传感器时会自动切换到目标通道并禁用其他通道，避免I2C地址冲突。
        读取多个传感器数据时会自动切换通道，并添加20ms操作延迟确保数据稳定。

    ==========================================
    Air Quality Monitor Class
    Integrates I2C multiplexer and multiple MEMS gas sensors to implement multi-channel sensor registration, data reading and calibration management.

    Attributes:
        RESTART_DELAY_MS (int): Restart delay time (5000ms, i.e., 5 seconds).
        i2c (SoftI2C): I2C communication instance object.
        pca (PCA9546ADR): PCA9546ADR multiplexer instance.
        sensors (dict): Sensor registry, {channel number: sensor instance}.
        channel_map (dict): Gas type-channel mapping table, {sensor type: channel number}.
        enabled_mask (int): Enabled channel mask.
        _restart_pending (bool): Whether there is a restart operation pending.
        _restart_target_mask (int): Restart target channel mask.
        _restart_start_time (int): Restart start timestamp.

    Methods:
        __init__(self, i2c, pca_addr=PCA9546ADR.addr7):
            Initialize air quality monitor, bind I2C interface and multiplexer.
        register_sensor(self, channel, sensor_type, sensor_addr=MEMSGasSensor.ADDR7):
            Register the specified type of sensor to the specified channel of the multiplexer.
        read_sensor(self, sensor_type):
            Read the concentration value of the specified gas type sensor.
        read_all(self):
            Read the concentration values of all registered sensors and return a mapping dictionary.
        calibrate_sensor(self, sensor_type):
            Calibrate the sensor of the specified gas type.
        _sensor_type_name(self, sensor_type):
            Convert sensor type constant to human-readable name (internal method).

    Notes:
        When registering a sensor, it will automatically switch to the target channel and disable other channels to avoid I2C address conflicts.
        When reading data from multiple sensors, it will automatically switch channels and add 20ms operation delay to ensure data stability.
    """

    # 重启延迟配置常量
    RESTART_DELAY_MS = const(5000)

    def __init__(self, i2c, pca_addr=PCA9546ADR.addr7):
        """
        初始化空气质量监测器，绑定I2C接口和多路复用器。

        Args:
            i2c (SoftI2C): SoftI2C实例（MicroPython的软I2C对象）。
            pca_addr (int): 多路复用器的7位I2C地址，默认为0x70。

        ==========================================
        Initialize air quality monitor, bind I2C interface and multiplexer.

        Args:
            i2c (SoftI2C): SoftI2C instance (MicroPython software I2C object).
            pca_addr (int): 7-bit I2C address of the multiplexer, default is 0x70.
        """
        self.i2c = i2c
        self.pca = PCA9546ADR(i2c, pca_addr)
        self.sensors = {}  # {通道号: 传感器实例}
        self.channel_map = {}  # {传感器类型: 通道号}
        self.enabled_mask = 0x00

        self._restart_pending = False
        self._restart_target_mask = 0x00
        self._restart_start_time = 0

    def register_sensor(self, channel, sensor_type, sensor_addr=MEMSGasSensor.ADDR7):
        """
        将指定类型的传感器注册到多路复用器指定通道。

        Args:
            channel (int): 多路复用器通道号（0-3）。
            sensor_type (int): 气体类型标识，必须使用MEMSGasSensor的TYPE_*常量。
            sensor_addr (int): 传感器的7位I2C地址，默认为0x2A。

        Returns:
            MEMSGasSensor: 已注册的传感器实例。

        Raises:
            ValueError: 如果通道号超出0-3范围。

        Notes:
            注册前会先禁用所有通道，再切换到目标通道，避免I2C地址冲突。
            若通道已注册传感器，会打印警告信息并覆盖原有传感器实例。

        ==========================================
        Register the specified type of sensor to the specified channel of the multiplexer.

        Args:
            channel (int): Multiplexer channel number (0-3).
            sensor_type (int): Gas type identification, must use TYPE_* constants of MEMSGasSensor.
            sensor_addr (int): 7-bit I2C address of the sensor, default is 0x2A.

        Returns:
            MEMSGasSensor: Registered sensor instance.

        Raises:
            ValueError: If channel number is out of 0-3 range.

        Notes:
            Before registration, all channels will be disabled first, then switch to the target channel to avoid I2C address conflicts.
            If a sensor is already registered on the channel, a warning message will be printed and the original sensor instance will be overwritten.
        """
        if channel < 0 or channel >= PCA9546ADR.MAX_CH:
            raise ValueError(f"Channel must be 0-{PCA9546ADR.MAX_CH - 1}")
        if channel in self.sensors:
            print(f"Warning: Channel {channel} already has a sensor, overwriting")

        # 切换到目标通道（先禁用所有通道避免冲突）
        self.pca.disable_all()
        self.pca.select_channel(channel)
        # 创建传感器实例
        sensor = MEMSGasSensor(self.i2c, sensor_type, sensor_addr)
        # 注册传感器到映射表
        self.sensors[channel] = sensor
        self.channel_map[sensor_type] = channel
        self.enabled_mask |= 1 << channel
        print(f"Registered {self._sensor_type_name(sensor_type)} sensor on channel {channel}")
        return sensor

    def read_sensor(self, sensor_type):
        """
        读取指定气体类型传感器的浓度值。

        Args:
            sensor_type (int): 气体类型标识，必须使用MEMSGasSensor的TYPE_*常量。

        Returns:
            int: 16位气体浓度值，读取失败返回0。

        Raises:
            ValueError: 如果指定的气体类型未注册传感器。

        Notes:
            读取前会自动切换到目标传感器对应的多路复用器通道。

        ==========================================
        Read the concentration value of the specified gas type sensor.

        Args:
            sensor_type (int): Gas type identification, must use TYPE_* constants of MEMSGasSensor.

        Returns:
            int: 16-bit gas concentration value, returns 0 if read fails.

        Raises:
            ValueError: If no sensor is registered for the specified gas type.

        Notes:
            Automatically switch to the multiplexer channel corresponding to the target sensor before reading.
        """
        if sensor_type not in self.channel_map:
            raise ValueError(f"No sensor registered for type {sensor_type}")

        channel = self.channel_map[sensor_type]
        self.pca.disable_all()
        self.pca.select_channel(channel)
        concentration = self.sensors[channel].read_concentration()
        return concentration

    def read_all(self):
        """
        读取所有已注册传感器的浓度值，返回映射字典。

        Returns:
            dict: {传感器类型: 浓度值}的映射字典，浓度值读取失败返回0。

        Notes:
            读取每个传感器前会切换对应通道，并添加20ms操作延迟确保数据稳定。

        ==========================================
        Read the concentration values of all registered sensors and return a mapping dictionary.

        Returns:
            dict: Mapping dictionary of {sensor type: concentration value}, returns 0 if concentration value read fails.

        Notes:
            Switch to the corresponding channel before reading each sensor, and add 20ms operation delay to ensure data stability.
        """
        results = {}
        for sensor_type, channel in self.channel_map.items():
            self.pca.disable_all()
            self.pca.select_channel(channel)
            results[sensor_type] = self.sensors[channel].read_concentration()
            time.sleep_ms(MEMSGasSensor.OP_DELAY_MS)
        return results

    def calibrate_sensor(self, sensor_type):
        """
        校准指定气体类型的传感器。

        Args:
            sensor_type (int): 气体类型标识，必须使用MEMSGasSensor的TYPE_*常量。

        Returns:
            bool: 校准是否成功（True/False）。

        Raises:
            ValueError: 如果指定的气体类型未注册传感器。

        Notes:
            校准前会自动切换到目标传感器对应的多路复用器通道。
            校准结果验证时读数非0属正常现象，微小偏差不影响使用。

        ==========================================
        Calibrate the sensor of the specified gas type.

        Args:
            sensor_type (int): Gas type identification, must use TYPE_* constants of MEMSGasSensor.

        Returns:
            bool: Whether calibration succeeded (True/False).

        Raises:
            ValueError: If no sensor is registered for the specified gas type.

        Notes:
            Automatically switch to the multiplexer channel corresponding to the target sensor before calibration.
            It is normal for the reading to be non-zero during calibration result verification, minor deviations do not affect use.
        """
        if sensor_type not in self.channel_map:
            raise ValueError(f"No sensor registered for type {sensor_type}")

        channel = self.channel_map[sensor_type]
        self.pca.disable_all()
        self.pca.select_channel(channel)
        success = self.sensors[channel].calibrate_zero()
        return success

    def _sensor_type_name(self, sensor_type):
        """
        将传感器类型常量转换为易读的名称（内部方法）。

        Args:
            sensor_type (int): 气体类型标识，必须使用MEMSGasSensor的TYPE_*常量。

        Returns:
            str: 气体类型名称，未知类型返回"UNKNOWN(类型值)"。

        ==========================================
        Convert sensor type constant to human-readable name (internal method).

        Args:
            sensor_type (int): Gas type identification, must use TYPE_* constants of MEMSGasSensor.

        Returns:
            str: Gas type name, returns "UNKNOWN(type value)" for unknown types.
        """
        type_names = {
            MEMSGasSensor.TYPE_VOC: "VOC",
            MEMSGasSensor.TYPE_H2: "H2",
            MEMSGasSensor.TYPE_CO: "CO",
            MEMSGasSensor.TYPE_NH3: "NH3",
            MEMSGasSensor.TYPE_H2S: "H2S",
            MEMSGasSensor.TYPE_ETHANOL: "ETHANOL",
            MEMSGasSensor.TYPE_PROPANE: "PROPANE",
            MEMSGasSensor.TYPE_FREON: "FREON",
            MEMSGasSensor.TYPE_NO2: "NO2",
            MEMSGasSensor.TYPE_SMOKE: "SMOKE",
            MEMSGasSensor.TYPE_HCHO: "HCHO",
            MEMSGasSensor.TYPE_ACETONE: "ACETONE",
        }
        return type_names.get(sensor_type, f"UNKNOWN({sensor_type})")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
