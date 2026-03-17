# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午9:00
# @Author  : xreef
# @File    : pcf8591.py
# @Description : PCF8591 8位ADC/DAC转换芯片驱动 支持4通道模拟输入 1通道模拟输出
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython v1.23.0

__version__ = "1.0.0"
__author__ = "xreef"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入微秒级时间模块，用于I2C通信过程中的延时操作
import time

# 从machine模块导入I2C和Pin类，用于硬件I2C接口和引脚的控制
from machine import I2C, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class PCF8591:
    """
    PCF8591 8位ADC/DAC转换芯片驱动类
    实现PCF8591芯片的完整功能驱动，支持4通道8位模拟输入(ADC)采样和1通道8位模拟输出(DAC)，
    提供单通道/多通道采样、电压读取/输出、输入模式配置等功能，通过I2C接口与芯片通信

    Attributes:
        AIN0 (int): 模拟输入通道0常量，二进制值0b00000000
        AIN1 (int): 模拟输入通道1常量，二进制值0b00000001
        AIN2 (int): 模拟输入通道2常量，二进制值0b00000010
        AIN3 (int): 模拟输入通道3常量，二进制值0b00000011
        AUTOINCREMENT_READ (int): 自动增量读取模式常量，二进制值0b00000100
        SINGLE_ENDED_INPUT (int): 单端输入模式常量，二进制值0b00000000（默认输入模式）
        TREE_DIFFERENTIAL_INPUT (int): 三差分输入模式常量，二进制值0b00010000
        TWO_SINGLE_ONE_DIFFERENTIAL_INPUT (int): 两单端一差分输入模式常量，二进制值0b00100000
        TWO_DIFFERENTIAL_INPUT (int): 两差分输入模式常量，二进制值0b00110000
        ENABLE_OUTPUT (int): 启用DAC输出常量，二进制值0b01000000
        DISABLE_OUTPUT (int): 禁用DAC输出常量，二进制值0b00000000
        OUTPUT_MASK (int): 输出使能位掩码常量，二进制值0b01000000
        _last_operation (int | None): 上一次操作的配置字节，用于避免重复写入I2C配置
        _i2c (I2C): I2C通信总线对象，用于与PCF8591芯片进行I2C通信
        _address (int): PCF8591芯片的I2C地址，范围0x48-0x4F
        _output_status (int): DAC输出状态，取值为ENABLE_OUTPUT或DISABLE_OUTPUT

    Methods:
        __init__(address, i2c, i2c_id, sda, scl): 初始化PCF8591驱动对象
        begin() -> bool: 检测I2C总线上是否存在PCF8591芯片
        _get_operation(auto_increment, channel, read_type) -> int: 生成操作配置字节（内部方法）
        _write_operation(operation) -> None: 写入操作配置字节到芯片（内部方法）
        analog_read_all(read_type) -> tuple[int, int, int, int]: 读取所有4通道的模拟输入值
        analog_read(channel, read_type) -> int: 读取指定通道的模拟输入值
        voltage_read(channel, reference_voltage) -> float: 读取指定通道的电压值
        voltage_write(value, reference_voltage) -> None: 设置DAC输出的电压值
        analog_write(value) -> None: 设置DAC输出的模拟值
        disable_output() -> None: 禁用DAC输出，降低芯片功耗

    Notes:
        1. 初始化时支持两种方式：传入已初始化的I2C对象 或 传入SDA/SCL引脚号自动创建I2C对象
        2. DAC输出默认禁用，使用前需通过analog_write或voltage_write启用
        3. 所有模拟值范围为0-255，对应电压范围0-参考电压（默认3.3V）

    ==========================================
    PCF8591 8-bit ADC/DAC Conversion Chip Driver Class
    Implement the complete function driver for the PCF8591 chip, support 4-channel 8-bit analog input (ADC) sampling and 1-channel 8-bit analog output (DAC),
    provide single-channel/multi-channel sampling, voltage reading/output, input mode configuration and other functions, communicate with the chip through I2C interface

    Attributes:
        AIN0 (int): Constant for analog input channel 0, binary value 0b00000000
        AIN1 (int): Constant for analog input channel 1, binary value 0b00000001
        AIN2 (int): Constant for analog input channel 2, binary value 0b00000010
        AIN3 (int): Constant for analog input channel 3, binary value 0b00000011
        AUTOINCREMENT_READ (int): Constant for auto-increment read mode, binary value 0b00000100
        SINGLE_ENDED_INPUT (int): Constant for single-ended input mode, binary value 0b00000000 (default input mode)
        TREE_DIFFERENTIAL_INPUT (int): Constant for three differential input mode, binary value 0b00010000
        TWO_SINGLE_ONE_DIFFERENTIAL_INPUT (int): Constant for two single-ended one differential input mode, binary value 0b00100000
        TWO_DIFFERENTIAL_INPUT (int): Constant for two differential input mode, binary value 0b00110000
        ENABLE_OUTPUT (int): Constant for enabling DAC output, binary value 0b01000000
        DISABLE_OUTPUT (int): Constant for disabling DAC output, binary value 0b00000000
        OUTPUT_MASK (int): Constant for output enable bit mask, binary value 0b01000000
        _last_operation (int | None): Configuration byte of the last operation, used to avoid repeated I2C configuration writing
        _i2c (I2C): I2C communication bus object, used for I2C communication with PCF8591 chip
        _address (int): I2C address of PCF8591 chip, range 0x48-0x4F
        _output_status (int): DAC output status, value is ENABLE_OUTPUT or DISABLE_OUTPUT

    Methods:
        __init__(address, i2c, i2c_id, sda, scl): Initialize PCF8591 driver object
        begin() -> bool: Detect whether the PCF8591 chip exists on the I2C bus
        _get_operation(auto_increment, channel, read_type) -> int: Generate operation configuration byte (internal method)
        _write_operation(operation) -> None: Write operation configuration byte to the chip (internal method)
        analog_read_all(read_type) -> tuple[int, int, int, int]: Read analog input values of all 4 channels
        analog_read(channel, read_type) -> int: Read analog input value of the specified channel
        voltage_read(channel, reference_voltage) -> float: Read voltage value of the specified channel
        voltage_write(value, reference_voltage) -> None: Set the voltage value of DAC output
        analog_write(value) -> None: Set the analog value of DAC output
        disable_output() -> None: Disable DAC output to reduce chip power consumption

    Notes:
        1. Two initialization methods are supported: pass an initialized I2C object or pass SDA/SCL pin numbers to create an I2C object automatically
        2. DAC output is disabled by default, need to enable through analog_write or voltage_write before use
        3. All analog values range from 0 to 255, corresponding to voltage range 0 to reference voltage (default 3.3V)
    """

    # 模拟输入通道0常量，二进制值0b00000000
    AIN0 = CHANNEL0 = 0b00000000
    # 模拟输入通道1常量，二进制值0b00000001
    AIN1 = CHANNEL1 = 0b00000001
    # 模拟输入通道2常量，二进制值0b00000010
    AIN2 = CHANNEL2 = 0b00000010
    # 模拟输入通道3常量，二进制值0b00000011
    AIN3 = CHANNEL3 = 0b00000011

    # 自动增量读取模式常量，二进制值0b00000100
    AUTOINCREMENT_READ = 0b00000100

    # 单端输入模式常量，二进制值0b00000000（默认输入模式）
    SINGLE_ENDED_INPUT = 0b00000000
    # 三差分输入模式常量，二进制值0b00010000
    TREE_DIFFERENTIAL_INPUT = 0b00010000
    # 两单端一差分输入模式常量，二进制值0b00100000
    TWO_SINGLE_ONE_DIFFERENTIAL_INPUT = 0b00100000
    # 两差分输入模式常量，二进制值0b00110000
    TWO_DIFFERENTIAL_INPUT = 0b00110000

    # 启用DAC输出常量，二进制值0b01000000
    ENABLE_OUTPUT = 0b01000000
    # 禁用DAC输出常量，二进制值0b00000000
    DISABLE_OUTPUT = 0b00000000

    # 输出使能位掩码常量，二进制值0b01000000
    OUTPUT_MASK = 0b01000000

    def __init__(self, address: int, i2c: I2C | None = None, i2c_id: int = 0, sda: int | None = None, scl: int | None = None) -> None:
        """
        初始化PCF8591驱动对象
        支持两种初始化方式：传入已初始化的I2C对象 或 传入SDA/SCL引脚号自动创建I2C对象

        Args:
            address (int): PCF8591芯片的I2C地址，范围0x48-0x4F
            i2c (I2C | None): 已初始化的I2C总线对象，默认为None
            i2c_id (int): I2C控制器ID（Raspberry Pi Pico为0或1），默认为0
            sda (int | None): SDA引脚号，默认为None
            scl (int | None): SCL引脚号，默认为None

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或地址超出范围时抛出，或未提供有效的I2C参数时抛出

        Notes:
            1. 优先使用传入的I2C对象，若未提供则使用SDA/SCL引脚号创建新的I2C对象
            2. 初始化时默认禁用DAC输出，_last_operation初始化为None避免重复写入

        ==========================================
        Initialize PCF8591 driver object
        Support two initialization methods: pass an initialized I2C object or pass SDA/SCL pin numbers to create an I2C object automatically

        Args:
            address (int): I2C address of PCF8591 chip, range 0x48-0x4F
            i2c (I2C | None): Initialized I2C bus object, default None
            i2c_id (int): I2C controller ID (0 or 1 for Raspberry Pi Pico), default 0
            sda (int | None): SDA pin number, default None
            scl (int | None): SCL pin number, default None

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or address out of range, or when no valid I2C parameters provided

        Notes:
            1. Prioritize using the passed I2C object, create a new I2C object with SDA/SCL pin numbers if not provided
            2. DAC output is disabled by default during initialization, _last_operation is initialized to None to avoid repeated writing
        """
        # 参数验证
        if address is None:
            raise ValueError("address cannot be None")
        if not isinstance(address, int):
            raise TypeError("address must be int")
        if address < 0x48 or address > 0x4F:
            raise ValueError("address must be between 0x48 and 0x4F")

        if i2c is not None:
            if not isinstance(i2c, I2C):
                raise TypeError("i2c must be I2C object")
        if i2c_id is None:
            raise ValueError("i2c_id cannot be None")
        if not isinstance(i2c_id, int):
            raise TypeError("i2c_id must be int")
        if i2c_id < 0 or i2c_id > 1:
            raise ValueError("i2c_id must be 0 or 1")

        if sda is not None:
            if not isinstance(sda, int):
                raise TypeError("sda must be int")
            if sda < 0:
                raise ValueError("sda must be a non-negative integer")
        if scl is not None:
            if not isinstance(scl, int):
                raise TypeError("scl must be int")
            if scl < 0:
                raise ValueError("scl must be a non-negative integer")

        # 初始化上一次操作的配置字节为None，用于判断是否需要重新写入配置
        self._last_operation: int | None = None

        # 判断I2C初始化方式：优先使用传入的I2C对象
        if i2c:
            # 赋值已初始化的I2C对象到实例变量
            self._i2c = i2c
        elif sda and scl:
            # 根据引脚号和控制器ID创建新的I2C对象
            self._i2c = I2C(i2c_id, scl=Pin(scl), sda=Pin(sda))
        else:
            # 未提供有效I2C参数，抛出值错误异常
            raise ValueError("Either i2c or sda and scl must be provided")

        # 保存PCF8591芯片的I2C地址到实例变量
        self._address = address
        # 初始化DAC输出状态为禁用，降低初始功耗
        self._output_status = self.DISABLE_OUTPUT

    def begin(self) -> bool:
        """
        检测I2C总线上是否存在PCF8591芯片
        通过扫描I2C总线并检查指定地址是否存在来验证芯片连接状态

        Args:
            无

        Returns:
            bool: 检测结果，True表示芯片存在，False表示未检测到

        Notes:
            1. 该方法是初始化后的必要检测步骤，建议在使用其他功能前调用
            2. 依赖I2C总线的scan()方法，返回的地址列表中包含目标地址则表示芯片存在

        ==========================================
        Detect whether the PCF8591 chip exists on the I2C bus
        Verify the chip connection status by scanning the I2C bus and checking if the specified address exists

        Args:
            None

        Returns:
            bool: Detection result, True means the chip exists, False means not detected

        Notes:
            1. This method is a necessary detection step after initialization, it is recommended to call before using other functions
            2. Depends on the scan() method of the I2C bus, the target address is included in the returned address list means the chip exists
        """
        # 扫描I2C总线获取已连接设备的地址列表，检查目标地址是否存在
        if self._i2c.scan().count(self._address) == 0:
            # 未检测到目标地址，返回False
            return False
        else:
            # 检测到目标地址，返回True
            return True

    def _get_operation(self, auto_increment: bool = False, channel: int = AIN0, read_type: int = SINGLE_ENDED_INPUT) -> int:
        """
        生成操作配置字节（内部方法）
        组合输出使能位、输入模式位、自动增量位和通道位生成完整的8位配置字节

        Args:
            auto_increment (bool): 是否启用自动增量读取模式，默认为False
            channel (int): 模拟输入通道，可选AIN0/AIN1/AIN2/AIN3，默认为AIN0
            read_type (int): 输入模式，可选SINGLE_ENDED_INPUT/TREE_DIFFERENTIAL_INPUT等，默认为SINGLE_ENDED_INPUT

        Returns:
            int: 8位操作配置字节，格式为D7(输出使能)|D6-D5(输入模式)|D4(自动增量)|D3-D0(通道)

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出允许范围时抛出

        Notes:
            1. 配置字节的每一位对应PCF8591的控制寄存器位定义
            2. 内部方法仅供类内其他方法调用，不建议外部直接使用

        ==========================================
        Generate operation configuration byte (internal method)
        Combine output enable bit, input mode bits, auto-increment bit and channel bits to generate a complete 8-bit configuration byte

        Args:
            auto_increment (bool): Whether to enable auto-increment read mode, default False
            channel (int): Analog input channel, optional AIN0/AIN1/AIN2/AIN3, default AIN0
            read_type (int): Input mode, optional SINGLE_ENDED_INPUT/TREE_DIFFERENTIAL_INPUT etc., default SINGLE_ENDED_INPUT

        Returns:
            int: 8-bit operation configuration byte, format is D7(output enable)|D6-D5(input mode)|D4(auto-increment)|D3-D0(channel)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of allowed range

        Notes:
            1. Each bit of the configuration byte corresponds to the control register bit definition of PCF8591
            2. Internal method is only for internal calls of the class, not recommended for external direct use
        """
        # 参数验证
        if auto_increment is None:
            raise ValueError("auto_increment cannot be None")
        if not isinstance(auto_increment, bool):
            raise TypeError("auto_increment must be bool")
        if channel is None:
            raise ValueError("channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("channel must be int")
        if channel not in (self.AIN0, self.AIN1, self.AIN2, self.AIN3):
            raise ValueError("channel must be AIN0, AIN1, AIN2, or AIN3")
        if read_type is None:
            raise ValueError("read_type cannot be None")
        if not isinstance(read_type, int):
            raise TypeError("read_type must be int")
        valid_read_types = (
            self.SINGLE_ENDED_INPUT,
            self.TREE_DIFFERENTIAL_INPUT,
            self.TWO_SINGLE_ONE_DIFFERENTIAL_INPUT,
            self.TWO_DIFFERENTIAL_INPUT,
        )
        if read_type not in valid_read_types:
            raise ValueError("read_type must be one of the predefined input mode constants")

        # 组合各配置位生成完整的操作配置字节
        return 0 | (self._output_status & self.OUTPUT_MASK) | read_type | (self.AUTOINCREMENT_READ if auto_increment else 0) | channel

    def _write_operation(self, operation: int) -> None:
        """
        写入操作配置字节到芯片（内部方法）
        仅当配置字节与上一次不同时才执行写入，避免重复的I2C通信操作

        Args:
            operation (int): 8位操作配置字节，取值范围0-255

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出0-255范围时抛出

        Returns:
            无

        Notes:
            1. 写入配置后需要读取1字节数据完成同步（PCF8591硬件要求）
            2. 写入后更新_last_operation记录当前配置，避免重复写入
            3. 写入后延时1ms确保配置生效

        ==========================================
        Write operation configuration byte to the chip (internal method)
        Only perform writing when the configuration byte is different from the last one to avoid repeated I2C communication operations

        Args:
            operation (int): 8-bit operation configuration byte, range 0-255

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of 0-255 range

        Returns:
            None

        Notes:
            1. Need to read 1 byte of data to complete synchronization after writing configuration (PCF8591 hardware requirement)
            2. Update _last_operation to record the current configuration after writing to avoid repeated writing
            3. Delay 1ms after writing to ensure the configuration takes effect
        """
        # 参数验证
        if operation is None:
            raise ValueError("operation cannot be None")
        if not isinstance(operation, int):
            raise TypeError("operation must be int")
        if operation < 0 or operation > 0xFF:
            raise ValueError("operation must be between 0 and 255")

        # 仅当当前配置字节与上一次不同时执行写入操作
        if operation != self._last_operation:
            # 将配置字节转换为字节数组并写入到指定I2C地址的芯片
            self._i2c.writeto(self._address, bytearray([operation]))
            # 延时1ms确保配置字节写入完成并生效
            time.sleep_ms(1)
            # 读取1字节数据完成硬件同步（丢弃读取结果）
            self._i2c.readfrom(self._address, 1)
            # 更新上一次操作的配置字节为当前值
            self._last_operation = operation

    def analog_read_all(self, read_type: int = SINGLE_ENDED_INPUT) -> tuple[int, int, int, int]:
        """
        读取所有4通道的模拟输入值
        启用自动增量模式，依次读取AIN0-AIN3四个通道的8位模拟值

        Args:
            read_type (int): 输入模式，可选SINGLE_ENDED_INPUT/TREE_DIFFERENTIAL_INPUT等，默认为SINGLE_ENDED_INPUT

        Returns:
            tuple[int, int, int, int]: 四个通道的模拟值元组，依次为AIN0、AIN1、AIN2、AIN3，取值范围0-255

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或输入模式无效时抛出

        Notes:
            1. 读取前需启用DAC输出以支持多通道读取
            2. 每个通道的模拟值为8位无符号整数，对应0-Vref的电压范围

        ==========================================
        Read analog input values of all 4 channels
        Enable auto-increment mode to read 8-bit analog values of four channels AIN0-AIN3 in sequence

        Args:
            read_type (int): Input mode, optional SINGLE_ENDED_INPUT/TREE_DIFFERENTIAL_INPUT etc., default SINGLE_ENDED_INPUT

        Returns:
            tuple[int, int, int, int]: Tuple of analog values of four channels, AIN0, AIN1, AIN2, AIN3 in sequence, value range 0-255

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or input mode is invalid

        Notes:
            1. Need to enable DAC output to support multi-channel reading before reading
            2. The analog value of each channel is an 8-bit unsigned integer, corresponding to the voltage range of 0-Vref
        """
        # 参数验证
        if read_type is None:
            raise ValueError("read_type cannot be None")
        if not isinstance(read_type, int):
            raise TypeError("read_type must be int")
        valid_read_types = (
            self.SINGLE_ENDED_INPUT,
            self.TREE_DIFFERENTIAL_INPUT,
            self.TWO_SINGLE_ONE_DIFFERENTIAL_INPUT,
            self.TWO_DIFFERENTIAL_INPUT,
        )
        if read_type not in valid_read_types:
            raise ValueError("read_type must be one of the predefined input mode constants")

        # 启用DAC输出以支持多通道读取功能
        self._output_status = self.ENABLE_OUTPUT
        # 生成自动增量模式的操作配置字节
        operation = self._get_operation(auto_increment=True)
        # 写入配置字节到芯片
        self._write_operation(operation)

        # 初始化空列表用于存储四个通道的模拟值
        data = []
        # 依次读取四个通道的模拟值并转换为整数，添加到数据列表
        data.append(int.from_bytes(self._i2c.readfrom(self._address, 1), "big"))
        data.append(int.from_bytes(self._i2c.readfrom(self._address, 1), "big"))
        data.append(int.from_bytes(self._i2c.readfrom(self._address, 1), "big"))
        data.append(int.from_bytes(self._i2c.readfrom(self._address, 1), "big"))

        # 返回四个通道的模拟值元组（转换为整数）
        return int(data[0]), int(data[1]), int(data[2]), int(data[3])

    def analog_read(self, channel: int, read_type: int = SINGLE_ENDED_INPUT) -> int:
        """
        读取指定通道的模拟输入值
        单通道读取模式，根据DAC输出状态选择返回正确的采样值

        Args:
            channel (int): 模拟输入通道，可选AIN0/AIN1/AIN2/AIN3
            read_type (int): 输入模式，可选SINGLE_ENDED_INPUT/TREE_DIFFERENTIAL_INPUT等，默认为SINGLE_ENDED_INPUT

        Returns:
            int: 指定通道的8位模拟值，取值范围0-255

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出允许范围时抛出

        Notes:
            1. 读取时需要读取2字节数据，根据DAC输出状态选择返回第1或第2字节：
               - DAC启用时返回第1字节
               - DAC禁用时返回第2字节（PCF8591硬件特性）

        ==========================================
        Read analog input value of the specified channel
        Single-channel reading mode, select and return the correct sampling value according to the DAC output status

        Args:
            channel (int): Analog input channel, optional AIN0/AIN1/AIN2/AIN3
            read_type (int): Input mode, optional SINGLE_ENDED_INPUT/TREE_DIFFERENTIAL_INPUT etc., default SINGLE_ENDED_INPUT

        Returns:
            int: 8-bit analog value of the specified channel, value range 0-255

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of allowed range

        Notes:
            1. Need to read 2 bytes of data when reading, select to return the 1st or 2nd byte according to the DAC output status:
               - Return the 1st byte when DAC is enabled
               - Return the 2nd byte when DAC is disabled (PCF8591 hardware feature)
        """
        # 参数验证
        if channel is None:
            raise ValueError("channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("channel must be int")
        if channel not in (self.AIN0, self.AIN1, self.AIN2, self.AIN3):
            raise ValueError("channel must be AIN0, AIN1, AIN2, or AIN3")
        if read_type is None:
            raise ValueError("read_type cannot be None")
        if not isinstance(read_type, int):
            raise TypeError("read_type must be int")
        valid_read_types = (
            self.SINGLE_ENDED_INPUT,
            self.TREE_DIFFERENTIAL_INPUT,
            self.TWO_SINGLE_ONE_DIFFERENTIAL_INPUT,
            self.TWO_DIFFERENTIAL_INPUT,
        )
        if read_type not in valid_read_types:
            raise ValueError("read_type must be one of the predefined input mode constants")

        # 生成单通道读取的操作配置字节
        operation = self._get_operation(auto_increment=False, channel=channel, read_type=read_type)
        # 写入配置字节到芯片
        self._write_operation(operation)

        # 读取2字节数据用于获取采样值
        data = self._i2c.readfrom(self._address, 2)
        # 根据DAC输出状态返回对应字节的采样值
        return data[0] if self._output_status == self.ENABLE_OUTPUT else data[1]

    def voltage_read(self, channel: int, reference_voltage: float = 3.3) -> float:
        """
        读取指定通道的电压值
        将8位模拟值转换为实际电压值，计算公式：电压 = 模拟值 × 参考电压 / 255

        Args:
            channel (int): 模拟输入通道，可选AIN0/AIN1/AIN2/AIN3
            reference_voltage (float): 参考电压值（单位：伏），默认为3.3V

        Returns:
            float: 指定通道的电压值，取值范围0-reference_voltage

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或通道无效时抛出，参考电压必须为正数

        Notes:
            1. 采用单端输入模式读取模拟值
            2. 电压值精度取决于参考电压，3.3V参考电压下精度约为0.0129V/步

        ==========================================
        Read voltage value of the specified channel
        Convert 8-bit analog value to actual voltage value with formula: Voltage = analog value × reference voltage / 255

        Args:
            channel (int): Analog input channel, optional AIN0/AIN1/AIN2/AIN3
            reference_voltage (float): Reference voltage value (unit: Volts), default 3.3V

        Returns:
            float: Voltage value of the specified channel, value range 0-reference_voltage

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or channel is invalid, reference voltage must be positive

        Notes:
            1. Read analog value in single-ended input mode
            2. Voltage value precision depends on reference voltage, about 0.0129V/step under 3.3V reference voltage
        """
        # 参数验证
        if channel is None:
            raise ValueError("channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("channel must be int")
        if channel not in (self.AIN0, self.AIN1, self.AIN2, self.AIN3):
            raise ValueError("channel must be AIN0, AIN1, AIN2, or AIN3")
        if reference_voltage is None:
            raise ValueError("reference_voltage cannot be None")
        if not isinstance(reference_voltage, (int, float)):
            raise TypeError("reference_voltage must be int or float")
        if reference_voltage <= 0:
            raise ValueError("reference_voltage must be positive")

        # 赋值参考电压到局部变量，便于计算
        voltage_ref = reference_voltage
        # 读取指定通道的模拟值（单端输入模式）
        ana = self.analog_read(channel, self.SINGLE_ENDED_INPUT)
        # 将模拟值转换为电压值并返回
        return ana * voltage_ref / 255

    def voltage_write(self, value: float, reference_voltage: float = 3.3) -> None:
        """
        设置DAC输出的电压值
        将目标电压值转换为8位模拟值后写入DAC，计算公式：模拟值 = 电压值 × 255 / 参考电压

        Args:
            value (float): 目标输出电压值，取值范围0-reference_voltage
            reference_voltage (float): 参考电压值（单位：伏），默认为3.3V

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出范围时抛出，参考电压必须为正数

        Returns:
            无

        Notes:
            1. 转换后的模拟值会自动传入analog_write方法完成写入
            2. 输出电压精度为参考电压/255，例如3.3V参考电压下约0.0129V/步

        ==========================================
        Set the voltage value of DAC output
        Convert the target voltage value to 8-bit analog value and write to DAC with formula: Analog value = voltage value × 255 / reference voltage

        Args:
            value (float): Target output voltage value, value range 0-reference_voltage
            reference_voltage (float): Reference voltage value (unit: Volts), default 3.3V

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of range, reference voltage must be positive

        Returns:
            None

        Notes:
            1. The converted analog value is automatically passed to the analog_write method to complete writing
            2. Output voltage precision is reference voltage/255, e.g., about 0.0129V/step under 3.3V reference voltage
        """
        # 参数验证
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, (int, float)):
            raise TypeError("value must be int or float")
        if reference_voltage is None:
            raise ValueError("reference_voltage cannot be None")
        if not isinstance(reference_voltage, (int, float)):
            raise TypeError("reference_voltage must be int or float")
        if reference_voltage <= 0:
            raise ValueError("reference_voltage must be positive")
        if value < 0 or value > reference_voltage:
            raise ValueError("value must be between 0 and reference_voltage")

        # 将目标电压值转换为对应的8位模拟值
        ana = value * 255 / reference_voltage
        # 调用analog_write方法写入模拟值到DAC
        self.analog_write(ana)

    def analog_write(self, value: int | float) -> None:
        """
        设置DAC输出的模拟值
        验证输入值范围后，启用DAC输出并写入模拟值到芯片

        Args:
            value (int | float): 8位模拟输出值，取值范围0-255

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出0-255的范围时抛出

        Returns:
            无

        Notes:
            1. 输入值会自动转换为整数（超出范围则抛出异常）
            2. 写入前会重置_last_operation强制重新写入配置
            3. 写入配置字节和模拟值完成DAC输出设置

        ==========================================
        Set the analog value of DAC output
        After verifying the input value range, enable DAC output and write the analog value to the chip

        Args:
            value (int | float): 8-bit analog output value, value range 0-255

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of 0-255 range

        Returns:
            None

        Notes:
            1. The input value is automatically converted to an integer (exception is thrown if out of range)
            2. _last_operation is reset to force re-writing of configuration before writing
            3. Write configuration byte and analog value to complete DAC output setting
        """
        # 参数验证
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, (int, float)):
            raise TypeError("value must be int or float")

        # 验证输入值是否在0-255的有效范围内
        if value > 255 or value < 0:
            # 超出范围抛出异常
            raise Exception("Value must be between 0 and 255")

        # 启用DAC输出功能
        self._output_status = self.ENABLE_OUTPUT
        # 重置上一次操作的配置字节为None，强制重新写入配置
        self._last_operation = None
        # 写入DAC输出使能配置和模拟值到芯片
        self._i2c.writeto(self._address, bytearray([self.ENABLE_OUTPUT, int(value)]))

    def disable_output(self) -> None:
        """
        禁用DAC输出，降低芯片功耗
        更新输出状态并写入禁用配置字节到芯片

        Args:
            无

        Returns:
            无

        Notes:
            1. 禁用后DAC输出引脚变为高阻态，不再输出模拟电压
            2. 建议在程序结束或长时间不使用DAC时调用

        ==========================================
        Disable DAC output to reduce chip power consumption
        Update output status and write disable configuration byte to the chip

        Args:
            None

        Returns:
            None

        Notes:
            1. After disabling, the DAC output pin becomes high-impedance state and no longer outputs analog voltage
            2. It is recommended to call when the program ends or the DAC is not used for a long time
        """
        # 更新DAC输出状态为禁用
        self._output_status = self.DISABLE_OUTPUT
        # 写入禁用DAC输出的配置字节到芯片
        self._i2c.writeto(self._address, bytearray([self.DISABLE_OUTPUT]))


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
