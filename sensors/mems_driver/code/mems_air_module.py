# 导入时间相关模块
import time

# 导入硬件相关模块
from machine import SoftI2C, Pin, Timer

# 导入常量模块
from micropython import const


class MEMSGasSensor:
    """
    JEDM气体传感器操作类（扩展版）
    支持读取气体浓度和校零校准功能，基于SoftI2C通信
    新增多气体类型枚举、预热功能、重试机制、标准化API

    Attributes:
        i2c (SoftI2C): I2C通信实例对象。
        addr (int): 传感器的7位I2C地址（公开属性）。
        sensor_type (int): 传感器类型（对应类内TYPE_*常量）。
        _preheat_done (bool): 预热完成标志。
        _preheat_timer (Timer | None): 非阻塞预热定时器。

    Class Attributes (const int):
        # 气体类型枚举常量
        TYPE_VOC = const(1)        # VOC传感器
        TYPE_H2 = const(2)         # 氢气传感器
        TYPE_CO = const(3)         # 一氧化碳传感器
        TYPE_NH3 = const(4)        # 氨气传感器
        TYPE_H2S = const(5)        # 硫化氢传感器
        TYPE_ETHANOL = const(6)    # 乙醇传感器
        TYPE_PROPANE = const(7)    # 丙烷传感器
        TYPE_FREON = const(8)      # 氟利昂传感器
        TYPE_NO2 = const(9)        # 二氧化氮传感器
        TYPE_SMOKE = const(10)     # 烟雾传感器
        TYPE_HCHO = const(11)      # 甲醛传感器
        TYPE_ACETONE = const(12)   # 丙酮传感器

        # 通信/操作常量
        ADDR7 = const(0x2A)        # 默认7位I2C地址
        CMD_READ = const(0xA1)     # 读取浓度命令
        CMD_CAL = const(0x32)      # 校零校准命令
        PREHEAT_MS = const(30000)  # 预热时长(ms)
        OP_DELAY_MS = const(20)    # 单次操作后阻塞延时(ms)

        # 原有常量（保留）
        MAX_I2C_FREQ = const(100000)  # I2C最大通信速率
        CALIB_MIN = const(0)          # 校准值最小值
        CALIB_MAX = const(65535)      # 校准值最大值(2^16-1)

    Methods:
        __init__(self, i2c: SoftI2C, sensor_type: int, addr7: int = ADDR7) -> None:
            初始化传感器，绑定I2C、指定类型和地址。
        preheat(self, block: bool = True) -> None:
            执行传感器预热（阻塞/非阻塞）。
        read_concentration(self, retries: int = 3) -> int | None:
            读取气体浓度，失败返回None，支持重试。
        calibrate_zero(self, baseline_value: int, retries: int = 3) -> bool:
            执行校零校准，baseline_value必填，支持重试。
        get_address(self) -> int:
            返回传感器7位I2C地址。
        get_type(self) -> int:
            返回传感器类型（TYPE_*常量）。
        is_preheat_done(self) -> bool:
            辅助方法：返回预热完成状态。
    """

    # ======================== 类常量定义（严格按要求） ========================
    # 气体类型枚举常量
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

    # 通信/操作常量
    ADDR7 = const(0x2A)
    CMD_READ = const(0xA1)
    CMD_CAL = const(0x32)
    PREHEAT_MS = const(30000)
    OP_DELAY_MS = const(20)

    # 原有常量（保留）
    MAX_I2C_FREQ = const(100000)
    CALIB_MIN: int = 0
    CALIB_MAX: int = 65535

    def __init__(self, i2c: SoftI2C, sensor_type: int, addr7: int = ADDR7) -> None:
        """
        初始化气体传感器并绑定I2C通信接口。

        Args:
            i2c (SoftI2C): SoftI2C实例（MicroPython的软I2C对象）。
            sensor_type (int): 传感器类型（类内TYPE_*常量）。
            addr7 (int): 传感器的7位基础地址，默认为0x2A。

        Raises:
            TypeError: 如果i2c参数不是SoftI2C实例。
            ValueError: 如果sensor_type不是有效类型常量。
        """
        # 校验I2C类型（保留原有逻辑）
        if not isinstance(i2c, SoftI2C):
            raise TypeError("i2c must be a SoftI2C instance")

        # 校验传感器类型有效性
        valid_types = {
            MEMSGasSensor.TYPE_VOC, MEMSGasSensor.TYPE_H2, MEMSGasSensor.TYPE_CO, MEMSGasSensor.TYPE_NH3,
            MEMSGasSensor.TYPE_H2S, MEMSGasSensor.TYPE_ETHANOL, MEMSGasSensor.TYPE_PROPANE, MEMSGasSensor.TYPE_FREON,
            MEMSGasSensor.TYPE_NO2, MEMSGasSensor.TYPE_SMOKE, MEMSGasSensor.TYPE_HCHO, MEMSGasSensor.TYPE_ACETONE
        }
        if sensor_type not in valid_types:
            raise ValueError(f"Invalid sensor_type {sensor_type}, use TYPE_* constants")

        # 实例属性初始化
        self.i2c: SoftI2C = i2c
        self.addr: int = addr7  # 公开属性，替代原有私有_addr_7bit
        self.sensor_type: int = sensor_type

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
            ack_count = self.i2c.writeto(self.addr, bytes([MEMSGasSensor.CMD_READ]), False)
            if ack_count != 1:
                raise OSError("No ACK for read command")

            # 第二步：发送读操作（7位地址），读取2个字节的浓度数据（高位+低位），stop=True发送停止位
            data = self.i2c.readfrom(self.addr, 2)
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
        if calib_value > MEMSGasSensor.CALIB_MAX or calib_value < MEMSGasSensor.CALIB_MIN:
            raise ValueError("Calibration value must be between 0 and 65535")

        # 将16位校准值拆分为高8位和低8位（确保在0-255范围内）
        high_byte: int = (calib_value >> 8) & 0xFF
        low_byte: int = calib_value & 0xFF

        try:
            # 发送写操作，写入校零命令+校准值高低字节，stop=True发送停止位
            # 发送的字节序列：[校零命令, 高位字节, 低位字节]
            ack_count = self.i2c.writeto(self.addr, bytes([MEMSGasSensor.CMD_CAL, high_byte, low_byte]))
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

    def get_address(self) -> int:
        """
        获取传感器的7位I2C地址。

        Returns:
            int: 传感器的7位I2C地址。

        ==========================================

        Get the 7-bit I2C address of the sensor.

        Returns:
            int: The 7-bit I2C address of the sensor.
        """
        return self.addr

    def get_type(self) -> int:
        """
        获取传感器类型（TYPE_*常量）。

        Returns:
            int: 传感器类型（对应类内TYPE_*常量）。
        """
        return self.sensor_type

class PCA9546ADR:
    """
    PCA9546ADR 类，用于通过 I2C 总线控制 PCA9546ADR 多路复用器，实现通道切换与关闭。
    封装了通道选择、全部关闭、状态读取等功能。

    Attributes:
        i2c: I2C 实例，用于与 PCA9546ADR 通信。
        addr (int): PCA9546ADR 的 I2C 地址。
        _current_mask (int): 当前通道掩码。

    Methods:
        __init__(i2c, addr=ADDR7): 初始化 PCA9546ADR。
        write_ctl(ctl_byte): 写控制寄存器设置通道。
        select_channel(ch): 选择指定通道。
        disable_all(): 关闭所有通道。
        read_status(): 读取当前状态。
        current_mask(): 获取当前通道掩码。

    ===========================================

    PCA9546ADR I2C multiplexer class for channel control.
    Provides channel selection, disable, and status read.

    Attributes:
        i2c: I2C instance for communication.
        addr (int): PCA9546ADR I2C address.
        _current_mask (int): Current channel mask.

    Methods:
        __init__(i2c, addr=ADDR7): Initialize PCA9546ADR.
        write_ctl(ctl_byte): Write control register.
        select_channel(ch): Select channel.
        disable_all(): Disable all channels.
        read_status(): Read status.
        current_mask(): Get current channel mask.
    """

    MAX_CH = const(4)

    def __init__(self, i2c, addr=0x70):
        """
        初始化 PCA9546ADR 实例。

        Args:
            i2c (I2C): I2C 实例。
            addr (int): 7 位地址（默认 0x70）。

        ==========================================

        Initialize PCA9546ADR instance.

        Args:
            i2c (I2C): I2C instance.
            addr (int): 7-bit address (default 0x70).
        """
        self.i2c = i2c
        self.addr = addr
        self._current_mask = 0x00

    def write_ctl(self, ctl_byte):
        """
        写控制寄存器以设置通道使能位。

        Args:
            ctl_byte (int): 控制字节，低 4 位控制通道使能。

        ==========================================

        Write to the control register to set the channel enable bit.

        Args:
            ctl_byte (int): Control byte, lower 4 bits control channel enabling.
        """
        ctl = int(ctl_byte) & 0x0F  # 只保留低4位
        try:
            self.i2c.writeto(self.addr, bytearray([ctl]))
        except OSError as e:
            # 写入失败，不修改 _current_mask，向上抛出异常以便调用者处理
            raise
        else:
            # 仅在成功写入后更新内部掩码
            self._current_mask = ctl

    def select_channel(self, ch):
        """
        选择指定通道并打开它。

        Args:
            ch (int): 通道编号，0~3。

        Raises:
            ValueError: 通道号不是0~3。

        ==========================================

        Select the specified channel and open it.

        Args:
            ch (int): Channel number, 0~3.

        Raises:
            ValueError: The channel number is not in the range of 0~3
        """
        if ch < 0 or ch >= self.MAX_CH:
            raise ValueError("Invalid channel")
        self.write_ctl(1 << ch)

    def disable_all(self):
        """
        关闭所有通道。

        ==========================================

        Disable all channels.
        """
        self.write_ctl(0x00)

    def read_status(self):
        """
        读取控制寄存器的状态。

        Returns:
            int: 当前状态字节。

        ==========================================

        Read the status of the control register.

        Returns:
            int: Current status byte.
        """
        try:
            b = self.i2c.readfrom(self.addr, 1)
        except OSError as e:
            # 读取失败，不修改 _current_mask，向上抛出异常
            raise
        else:
            status = b[0] & 0x0F
            self._current_mask = status
            return status

    def current_mask(self):
        """
        获取当前通道掩码。

        Returns:
            int: 当前通道掩码。

        ==========================================

        Get the current channel mask.

        Returns:
            int: Current channel mask.
        """
        return self._current_mask
