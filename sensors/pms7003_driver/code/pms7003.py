# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025-04-01
# @Author  : pkucmus
# @File    : pms7003.py
# @Description : PMS7003 激光粉尘传感器驱动库，支持主动和被动模式
# @License : MIT
__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import machine
import struct
import time
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class UartError(Exception):
    """
    UART通信异常类 / UART Communication Exception Class
    """
    pass


class Pms7003:
    """
    PMS7003 激光粉尘传感器驱动类 / PMS7003 Laser Dust Sensor Driver Class

    Attributes:
        uart (machine.UART): 用于通信的UART对象 / UART object for communication.

    Methods:
        __init__(uart): 初始化传感器对象 / Initialize the sensor object.
        __repr__(): 返回对象的字符串表示 / Return string representation of the object.
        _assert_byte(byte, expected): 静态方法，验证字节是否符合预期 / Static method to verify if a byte matches the expected value.
        _format_bytearray(buffer): 静态方法，格式化字节数组为十六进制字符串 / Static method to format a bytearray into a hex string.
        _send_cmd(request, response): 发送命令到传感器并验证响应 / Send command to sensor and verify response.
        read(): 从传感器读取并解析一帧数据 / Read and parse a data frame from the sensor.

    Notes:
        此类用于PMS7003传感器的主动模式通信。 / This class is for active mode communication with the PMS7003 sensor.
    """

    # 数据帧中各个数据字段的索引常量 / Constants for data field indices in the frame
    START_BYTE_1 = 0x42
    START_BYTE_2 = 0x4d

    PMS_FRAME_LENGTH = 0
    PMS_PM1_0 = 1
    PMS_PM2_5 = 2
    PMS_PM10_0 = 3
    PMS_PM1_0_ATM = 4
    PMS_PM2_5_ATM = 5
    PMS_PM10_0_ATM = 6
    PMS_PCNT_0_3 = 7
    PMS_PCNT_0_5 = 8
    PMS_PCNT_1_0 = 9
    PMS_PCNT_2_5 = 10
    PMS_PCNT_5_0 = 11
    PMS_PCNT_10_0 = 12
    PMS_VERSION = 13
    PMS_ERROR = 14
    PMS_CHECKSUM = 15

    def __init__(self, uart: machine.UART) -> None:
        """
        初始化PMS7003传感器对象 / Initialize the PMS7003 sensor object.

        Args:
            uart (machine.UART): 已配置好的UART对象 / Pre-configured UART object.

        Raises:
            TypeError: 如果uart参数为None / If the uart parameter is None.
        """
        # 入口参数None显式检查 / Explicit check for None input parameter
        if uart is None:
            raise TypeError("UART object cannot be None")
        self.uart = uart

    def __repr__(self) -> str:
        """
        返回对象的字符串表示 / Return string representation of the object.

        Returns:
            str: 对象的描述字符串 / Descriptive string of the object.
        """
        return "Pms7003({})".format(self.uart)

    @staticmethod
    def _assert_byte(byte: bytes, expected: int) -> bool:
        """
        静态方法，验证读取的字节是否符合预期值 / Static method to verify if a read byte matches the expected value.

        Args:
            byte (bytes): 从UART读取的字节数据 / Byte data read from UART.
            expected (int): 期望的字节值（整数） / Expected byte value (integer).

        Returns:
            bool: 如果字节有效且等于期望值则返回True，否则返回False / Returns True if byte is valid and equals expected value, otherwise False.

        Notes:
            用于验证数据帧的起始字节。 / Used to verify the start bytes of a data frame.
        """
        # 检查字节是否为None、长度是否大于0、以及其整数值是否等于期望值 / Check if byte is None, has length > 0, and its integer value equals expected
        if byte is None or len(byte) < 1 or ord(byte) != expected:
            return False
        return True

    @staticmethod
    def _format_bytearray(buffer: bytearray) -> str:
        """
        静态方法，将字节数组格式化为十六进制字符串，用于调试 / Static method to format a bytearray into a hex string for debugging.

        Args:
            buffer (bytearray): 需要格式化的字节数组 / Bytearray to be formatted.

        Returns:
            str: 格式化的十六进制字符串，例如 "0x42 0x4d " / Formatted hex string, e.g., "0x42 0x4d ".
        """
        return "".join("0x{:02x} ".format(i) for i in buffer)

    def _send_cmd(self, request: bytearray, response: bytearray | None) -> None:
        """
        发送命令请求到传感器，并可选择性地验证响应 / Send a command request to the sensor and optionally verify the response.

        Args:
            request (bytearray): 要发送的命令字节数组 / Command bytearray to send.
            response (bytearray | None): 期望的响应字节数组，如果为None则不验证响应 / Expected response bytearray, if None, response is not verified.

        Raises:
            UartError: 如果写入的字节数与请求长度不符 / If the number of bytes written does not match the request length.
            UartError: 如果提供了响应但接收到的响应不匹配 / If a response is provided but the received response does not match.

        Notes:
            发送命令后，如果需要验证响应，会等待2秒再读取。 / After sending the command, if response verification is needed, it waits 2 seconds before reading.
        """
        # 将请求数据写入UART / Write request data to UART
        nr_of_written_bytes = self.uart.write(request)

        # 检查是否成功写入了所有字节 / Check if all bytes were written successfully
        if nr_of_written_bytes != len(request):
            raise UartError('Failed to write to UART')

        # 如果提供了期望的响应，则进行验证 / If an expected response is provided, verify it
        if response:
            # 等待传感器响应 / Wait for sensor response
            time.sleep(2)
            # 读取与期望响应长度相同的数据 / Read data of the same length as the expected response
            buffer = self.uart.read(len(response))

            # 比较接收到的数据与期望的响应 / Compare received data with expected response
            if buffer != response:
                raise UartError(
                    'Wrong UART response, expecting: {}, getting: {}'.format(
                        Pms7003._format_bytearray(response), Pms7003._format_bytearray(buffer)
                    )
                )

    def read(self) -> dict[str, int]:
        """
        从传感器读取并解析一帧完整的测量数据 / Read and parse a complete frame of measurement data from the sensor.

        Returns:
            dict[str, int]: 包含所有测量数据的字典，键为字段名，值为对应的整数值 / Dictionary containing all measurement data, keys are field names, values are corresponding integers.

        Notes:
            此方法会持续循环，直到读取到一个校验和正确的有效数据帧。 / This method loops continuously until a valid data frame with correct checksum is read.
            适用于传感器的主动模式（连续输出）。 / Suitable for the sensor's active mode (continuous output).
        """
        while True:
            # 读取第一个起始字节 / Read the first start byte
            first_byte = self.uart.read(1)
            # 验证第一个起始字节是否为0x42 / Verify the first start byte is 0x42
            if not self._assert_byte(first_byte, Pms7003.START_BYTE_1):
                continue

            # 读取第二个起始字节 / Read the second start byte
            second_byte = self.uart.read(1)
            # 验证第二个起始字节是否为0x4d / Verify the second start byte is 0x4d
            if not self._assert_byte(second_byte, Pms7003.START_BYTE_2):
                continue

            # 读取数据帧剩余部分（30字节） / Read the remaining part of the data frame (30 bytes)
            read_bytes = self.uart.read(30)
            # 如果读取的字节数不足30，则重新开始 / If less than 30 bytes are read, start over
            if len(read_bytes) < 30:
                continue

            # 使用struct模块按照大端序解析30个字节的数据 / Use struct module to parse the 30 bytes of data in big-endian order
            data = struct.unpack('!HHHHHHHHHHHHHBBH', read_bytes)

            # 计算校验和：两个起始字节 + 前28个数据字节 / Calculate checksum: two start bytes + first 28 data bytes
            checksum = Pms7003.START_BYTE_1 + Pms7003.START_BYTE_2
            checksum += sum(read_bytes[:28])

            # 如果计算的校验和与数据帧中的校验和不匹配，则重新开始 / If calculated checksum does not match the checksum in the frame, start over
            if checksum != data[Pms7003.PMS_CHECKSUM]:
                continue

            # 校验成功，将解析后的数据组织成字典并返回 / Checksum successful, organize parsed data into a dictionary and return
            return {
                'FRAME_LENGTH': data[Pms7003.PMS_FRAME_LENGTH],
                'PM1_0': data[Pms7003.PMS_PM1_0],
                'PM2_5': data[Pms7003.PMS_PM2_5],
                'PM10_0': data[Pms7003.PMS_PM10_0],
                'PM1_0_ATM': data[Pms7003.PMS_PM1_0_ATM],
                'PM2_5_ATM': data[Pms7003.PMS_PM2_5_ATM],
                'PM10_0_ATM': data[Pms7003.PMS_PM10_0_ATM],
                'PCNT_0_3': data[Pms7003.PMS_PCNT_0_3],
                'PCNT_0_5': data[Pms7003.PMS_PCNT_0_5],
                'PCNT_1_0': data[Pms7003.PMS_PCNT_1_0],
                'PCNT_2_5': data[Pms7003.PMS_PCNT_2_5],
                'PCNT_5_0': data[Pms7003.PMS_PCNT_5_0],
                'PCNT_10_0': data[Pms7003.PMS_PCNT_10_0],
                'VERSION': data[Pms7003.PMS_VERSION],
                'ERROR': data[Pms7003.PMS_ERROR],
                'CHECKSUM': data[Pms7003.PMS_CHECKSUM],
            }


class PassivePms7003(Pms7003):
    """
    PMS7003 被动模式驱动类 / PMS7003 Passive Mode Driver Class

    Attributes:
        uart (machine.UART): 继承自父类的UART对象 / UART object inherited from parent class.

    Methods:
        __init__(uart): 初始化并切换到被动模式 / Initialize and switch to passive mode.
        sleep(): 使传感器进入睡眠模式 / Put the sensor into sleep mode.
        wakeup(): 唤醒传感器 / Wake up the sensor.
        read(): 在被动模式下请求并读取一帧数据 / Request and read a data frame in passive mode.

    Notes:
        此类用于PMS7003传感器的被动模式通信。 / This class is for passive mode communication with the PMS7003 sensor.
        被动模式下，主机需要发送请求命令，传感器才会返回数据。 / In passive mode, the host must send a request command for the sensor to return data.
        更多关于被动模式的信息请参考类文档字符串中的链接。 / More about passive mode can be found in the links in the class docstring.
    """
    # 进入被动模式的请求命令 / Request command to enter passive mode
    ENTER_PASSIVE_MODE_REQUEST = bytearray(
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe1, 0x00, 0x00, 0x01, 0x70]
    )
    # 进入被动模式的期望响应 / Expected response for entering passive mode
    ENTER_PASSIVE_MODE_RESPONSE = bytearray(
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0x00, 0x04, 0xe1, 0x00, 0x01, 0x74]
    )
    # 进入睡眠模式的请求命令 / Request command to enter sleep mode
    SLEEP_REQUEST = bytearray(
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe4, 0x00, 0x00, 0x01, 0x73]
    )
    # 进入睡眠模式的期望响应 / Expected response for entering sleep mode
    SLEEP_RESPONSE = bytearray(
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0x00, 0x04, 0xe4, 0x00, 0x01, 0x77]
    )
    # 唤醒传感器的请求命令（无响应） / Request command to wake up the sensor (no response)
    WAKEUP_REQUEST = bytearray(
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe4, 0x00, 0x01, 0x01, 0x74]
    )
    # 在被动模式下请求读取数据的命令（响应为数据帧） / Command to request reading data in passive mode (response is a data frame)
    READ_IN_PASSIVE_REQUEST = bytearray(
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe2, 0x00, 0x00, 0x01, 0x71]
    )

    def __init__(self, uart: machine.UART) -> None:
        """
        初始化被动模式传感器对象 / Initialize the passive mode sensor object.

        Args:
            uart (machine.UART): 已配置好的UART对象 / Pre-configured UART object.

        Raises:
            TypeError: 如果uart参数为None / If the uart parameter is None.

        Notes:
            初始化时会自动发送命令，将传感器切换到被动模式。 / Automatically sends a command to switch the sensor to passive mode during initialization.
        """
        # 调用父类初始化方法 / Call parent class initialization method
        super().__init__(uart=uart)
        # 发送命令使传感器进入被动模式 / Send command to make the sensor enter passive mode
        self._send_cmd(request=PassivePms7003.ENTER_PASSIVE_MODE_REQUEST,
                       response=PassivePms7003.ENTER_PASSIVE_MODE_RESPONSE)

    def sleep(self) -> None:
        """
        发送命令使传感器进入睡眠模式 / Send command to put the sensor into sleep mode.

        Raises:
            UartError: 如果UART通信失败或响应不正确 / If UART communication fails or response is incorrect.
        """
        self._send_cmd(request=PassivePms7003.SLEEP_REQUEST,
                       response=PassivePms7003.SLEEP_RESPONSE)

    def wakeup(self) -> None:
        """
        发送命令唤醒传感器 / Send command to wake up the sensor.

        Notes:
            此命令不期望从传感器收到响应。 / This command does not expect a response from the sensor.
        """
        self._send_cmd(request=PassivePms7003.WAKEUP_REQUEST, response=None)

    def read(self) -> dict[str, int]:
        """
        在被动模式下读取一帧数据 / Read a data frame in passive mode.

        Returns:
            dict[str, int]: 包含所有测量数据的字典，键为字段名，值为对应的整数值 / Dictionary containing all measurement data, keys are field names, values are corresponding integers.

        Notes:
            首先发送读取请求命令，然后调用父类的read()方法获取数据。 / First sends a read request command, then calls the parent class's read() method to get the data.
        """
        # 发送被动模式下的数据读取请求命令 / Send the data read request command in passive mode
        self._send_cmd(request=PassivePms7003.READ_IN_PASSIVE_REQUEST, response=None)
        # 调用父类的read方法读取并解析数据帧 / Call parent class's read method to read and parse the data frame
        return super().read()

# ======================================== 初始化配置 ===========================================
# ========================================  主程序  ============================================