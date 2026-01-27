# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : ba111_tds.py
# @Description : ba111_tds水质检测传感器驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import UART
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class BA111TDS:
    """
    BA111TDS水质检测传感器驱动类。

    该类提供BA111TDS水质检测传感器的完整驱动功能，支持TDS和温度检测、
    基线校准、NTC参数配置等操作。通过UART接口与传感器通信。

    Attributes:
        READ_TDS_TEMPERATURE (bytes): 读取TDS和温度指令。
        BASELINE_CALIBRATION (bytes): 基线校准指令。
        SET_NTC_RESISTANCE (bytes): 设置NTC电阻指令。
        SET_NTC_B (bytes): 设置NTC B值指令。
        SUCCESS_RESPONSE (bytes): 成功响应帧。
        ERROR_RESPONSE_PREFIX (bytes): 错误响应前缀。
        ERROR_RESPONSE_SUFFIX (bytes): 错误响应后缀。
        ERROR_CODES (dict): 错误代码映射表。
        _uart (UART): UART通信接口实例。
        _timeout (int): 通信超时时间（毫秒）。
        ntc_resistance (int): NTC常温电阻值（Ω）。
        ntc_b_value (int): NTC B值。
        tds_value (float): TDS测量值（ppm）。
        temperature (float): 温度测量值（℃）。

    Methods:
        __init__(): 初始化传感器实例。
        _calculate_crc(): 计算CRC校验码。
        _validate_crc(): 验证CRC校验码。
        _build_frame(): 构建通信帧。
        _send_and_receive(): 发送帧并接收响应。
        detect(): 执行TDS和温度检测。
        calibrate(): 执行基线校准。
        set_ntc_resistance(): 设置NTC电阻值。
        set_ntc_b_value(): 设置NTC B值。

    ==========================================

    BA111TDS water quality detection sensor driver class.

    This class provides complete driver functionality for BA111TDS water quality
    detection sensor, supporting TDS and temperature detection, baseline calibration,
    NTC parameter configuration, etc. Communicates with sensor via UART interface.

    Attributes:
        READ_TDS_TEMPERATURE (bytes): Read TDS and temperature command.
        BASELINE_CALIBRATION (bytes): Baseline calibration command.
        SET_NTC_RESISTANCE (bytes): Set NTC resistance command.
        SET_NTC_B (bytes): Set NTC B value command.
        SUCCESS_RESPONSE (bytes): Success response frame.
        ERROR_RESPONSE_PREFIX (bytes): Error response prefix.
        ERROR_RESPONSE_SUFFIX (bytes): Error response suffix.
        ERROR_CODES (dict): Error code mapping table.
        _uart (UART): UART communication interface instance.
        _timeout (int): Communication timeout (milliseconds).
        ntc_resistance (int): NTC room temperature resistance value (Ω).
        ntc_b_value (int): NTC B value.
        tds_value (float): TDS measurement value (ppm).
        temperature (float): Temperature measurement value (℃).

    Methods:
        __init__(): Initialize sensor instance.
        _calculate_crc(): Calculate CRC checksum.
        _validate_crc(): Validate CRC checksum.
        _build_frame(): Build communication frame.
        _send_and_receive(): Send frame and receive response.
        detect(): Execute TDS and temperature detection.
        calibrate(): Execute baseline calibration.
        set_ntc_resistance(): Set NTC resistance value.
        set_ntc_b_value(): Set NTC B value.
    """

    READ_TDS_TEMPERATURE = bytes([0xA0])
    BASELINE_CALIBRATION = bytes([0xA6])
    SET_NTC_RESISTANCE = bytes([0xA3])
    SET_NTC_B = bytes([0xA5])

    # 成功响应码和错误响应码
    SUCCESS_RESPONSE = bytes([0xAC, 0x00, 0x00, 0x00, 0x00, 0xAC])
    ERROR_RESPONSE_PREFIX = bytes([0xAC])
    ERROR_RESPONSE_SUFFIX = bytes([0x00, 0x00, 0x00, 0xAE])

    # 错误代码映射
    ERROR_CODES = {
        0x01: "Command Frame Exception",
        0x02: "Busy coding",
        0x03: "Calibration failed",
        0x04: "Detection temperature out of range"
    }

    def __init__(self, uart: UART):
        """
        初始化BA111TDS传感器实例。

        Args:
            uart: 已配置好的UART实例。

        Note:
            - 需要先配置好UART的波特率、数据位、停止位等参数。
            - 默认超时时间为2000毫秒。
            - 默认NTC参数：电阻10000Ω，B值3950。

        ==========================================

        Initialize BA111TDS sensor instance.

        Args:
            uart: Configured UART instance.

        Note:
            - UART parameters (baud rate, data bits, stop bits, etc.) must be configured first.
            - Default timeout is 2000 milliseconds.
            - Default NTC parameters: resistance 10000Ω, B value 3950.
        """
        self._uart = uart
        # 超时时间（毫秒）
        self._timeout = 2000
        # 默认NTC常温电阻（单位Ω）
        self.ntc_resistance = 10000
        # 默认NTC B值
        self.ntc_b_value = 3950
        # TDS值（ppm）
        self.tds_value = 0.0
        # 温度值（℃）
        self.temperature = 0.0

    def _calculate_crc(self, data_bytes):
        """
        计算CRC校验码。

        Args:
            data_bytes: 需要计算校验码的数据字节。

        Returns:
            int: 计算出的CRC校验码（0-255）。

        ==========================================

        Calculate CRC checksum.

        Args:
            data_bytes: Data bytes to calculate checksum.

        Returns:
            int: Calculated CRC checksum (0-255).
        """

        return sum(data_bytes) & 0xFF

    def _validate_crc(self, frame_data):
        """
        验证CRC校验码。

        Args:
            frame_data: 完整的帧数据，包含CRC字节。

        Returns:
            bool: CRC校验结果（True表示有效，False表示无效）。

        ==========================================

        Validate CRC checksum.

        Args:
            frame_data: Complete frame data including CRC byte.

        Returns:
            bool: CRC validation result (True for valid, False for invalid).
        """

        # 计算校验和（不包括CRC字节和帧尾）
        data_to_check = frame_data[:-1]
        calculated_crc = sum(data_to_check) & 0xFF
        received_crc = frame_data[-1]

        return calculated_crc == received_crc

    def _build_frame(self, command, parameters=bytes([0x00, 0x00, 0x00, 0x00])):
        """
        构建完整的帧结构：命令(1B) + 参数(4B) + CRC(1B)

        Args:
            command: 命令字节。
            parameters: 参数字节（默认4字节，全0）。

        Returns:
            bytes: 构建的完整帧。

        Raises:
            ValueError: 参数长度不是4字节时抛出异常。

        ==========================================

        Build complete frame structure: command(1B) + parameters(4B) + CRC(1B)

        Args:
            command: Command byte.
            parameters: Parameter bytes (default 4 bytes, all zeros).

        Returns:
            bytes: Built complete frame.

        Raises:
            ValueError: Raised when parameter length is not 4 bytes.
        """

        if len(parameters) != 4:
            raise ValueError("The parameter length must be 4 bytes")

        frame = command + parameters
        crc = self._calculate_crc(frame)
        return frame + bytes([crc])

    def _send_and_receive(self, frame, response_length=6):
        """
        发送帧并接收响应。

        Args:
            frame: 要发送的帧数据。
            response_length: 期望的响应长度（默认6字节）。

        Returns:
            bytes|None: 接收到的响应数据，超时或无数据时返回None。

        ==========================================

        Send frame and receive response.

        Args:
            frame: Frame data to send.
            response_length: Expected response length (default 6 bytes).

        Returns:
            bytes|None: Received response data, returns None on timeout or no data.
        """

        # 清空缓冲区
        while self._uart.any():
            self._uart.read()
        time.sleep_ms(50)

        # 发送帧
        self._uart.write(frame)

        # 等待并读取响应
        start_time = time.ticks_ms()
        response = bytearray()

        while len(response) < response_length:
            if time.ticks_diff(time.ticks_ms(), start_time) > self._timeout:
                return None

            if self._uart.any():
                response.append(self._uart.read(1)[0])

            time.sleep_ms(10)

        return bytes(response)

    def detect(self) -> tuple[float, float] | None:
        """
        发送检测指令，返回(TDS值(ppm), 温度值(℃))，失败返回None。

        Returns:
            tuple|None: (tds_value, temperature) 或失败时返回None。

        ==========================================

        Send detection command, return (TDS value (ppm), temperature (℃)), or None on failure.

        Returns:
            tuple|None: (tds_value, temperature) or None on failure.
        """
        # 构建检测指令帧
        frame = self._build_frame(self.READ_TDS_TEMPERATURE)

        # 发送并接收响应
        response = self._send_and_receive(frame)

        if not response:
            return None

        # 验证响应格式（首字节应为0xAA）
        if response[0] != 0xAA:
            return None

        # 验证CRC
        if not self._validate_crc(response):
            return None

        # 解析TDS值（第2-3字节，大端序）
        tds_raw = (response[1] << 8) | response[2]
        tds_value = float(tds_raw)  # 单位为ppm
        self.tds_value = tds_value
        print(tds_value)
        # 解析温度值（第4-5字节，大端序）
        temp_raw = (response[3] << 8) | response[4]
        # 除以100得到℃
        temp_value = float(temp_raw) / 100.0
        self.temperature = temp_value
        print(temp_value)

        return (tds_value, temp_value)

    def calibrate(self) -> bool:
        """

        发送基线校准指令，返回校准是否成功（True/False）。

        注意：校准前请确保传感器在25℃±5℃的纯净水中。

        Returns:
            bool: 校准是否成功。

        ==========================================

        Send baseline calibration command, return whether calibration succeeded (True/False).

        Note: Ensure the sensor is in pure water at 25℃±5℃ before calibration.

        Returns:
            bool: Whether calibration succeeded
        """

        # 构建校准指令帧
        frame = self._build_frame(self.BASELINE_CALIBRATION)

        # 发送并接收响应
        response = self._send_and_receive(frame)

        if not response or len(response) < 6:
            return False

        # 检查是否为成功响应
        if response == self.SUCCESS_RESPONSE:
            return True

        # 检查是否为错误响应格式
        if (response[0] == self.ERROR_RESPONSE_PREFIX[0] and
                response[5] == self.ERROR_RESPONSE_SUFFIX[3]):
            # 获取错误码
            error_code = response[1]
            if error_code in self.ERROR_CODES:
                print(f"Calibration failed: {self.ERROR_CODES[error_code]}")
            else:
                print(f"Calibration failed: Unknown error code 0x{error_code:02X}")

        return False

    def set_ntc_resistance(self, resistance: int) -> bool:
        """
        设置 NTC 常温电阻（单位 Ω），返回设置是否成功（True/False）。

        Args:
            resistance: NTC常温电阻值（Ω）。

        Returns:
            bool: 设置是否成功。

        ==========================================

        Set NTC room temperature resistance (unit Ω), return whether setting succeeded (True/False).

        Args:
            resistance: NTC room temperature resistance value (Ω).

        Returns:
            bool: Whether setting succeeded.
        """

        # 检查参数范围
        if resistance < 0 or resistance > 0xFFFFFFFF:
            print(f"Resistance value {resistance}Ω out of range")
            return False

        # 构建参数（4字节大端序）
        parameters = bytes([
            (resistance >> 24) & 0xFF,
            (resistance >> 16) & 0xFF,
            (resistance >> 8) & 0xFF,
            resistance & 0xFF
        ])

        # 构建指令帧
        frame = self._build_frame(self.SET_NTC_RESISTANCE, parameters)

        # 发送并接收响应
        response = self._send_and_receive(frame)

        if not response or len(response) < 6:
            return False

        # 检查是否为成功响应
        if response == self.SUCCESS_RESPONSE:
            self.ntc_resistance = resistance
            return True

        # 检查是否为错误响应
        if (response[0] == self.ERROR_RESPONSE_PREFIX[0] and
                response[5] == self.ERROR_RESPONSE_SUFFIX[3]):
            error_code = response[1]
            if error_code in self.ERROR_CODES:
                print(f"Failed to set NTC resistor: {self.ERROR_CODES[error_code]}")
            else:
                print(f"Failed to set NTC resistor: Unknown error code 0x{error_code:02X}")

        return False

    def set_ntc_b_value(self, b_value: int) -> bool:
        """
        设置 NTC B 值，返回设置是否成功（True/False）。

        Args:
            b_value: NTC B值。

        Returns:
            bool: 设置是否成功。

        ==========================================

        Set NTC B value, return whether setting succeeded (True/False).

        Args:
            b_value: NTC B value.

        Returns:
            bool: Whether setting succeeded.
        """
        # 检查参数范围
        if b_value < 0 or b_value > 0xFFFF:
            print(f"B value {b_value} is out of range")
            return False

        # 构建参数（第1-2字节为B值，第3-4字节为0）
        parameters = bytes([
            (b_value >> 8) & 0xFF,
            b_value & 0xFF,
            0x00,
            0x00
        ])

        # 构建指令帧
        frame = self._build_frame(self.SET_NTC_B, parameters)

        # 发送并接收响应
        response = self._send_and_receive(frame)

        if not response or len(response) < 6:
            return False

        # 检查是否为成功响应
        if response == self.SUCCESS_RESPONSE:
            self.ntc_b_value = b_value
            return True

        # 检查是否为错误响应
        if (response[0] == self.ERROR_RESPONSE_PREFIX[0] and
                response[5] == self.ERROR_RESPONSE_SUFFIX[3]):
            error_code = response[1]
            if error_code in self.ERROR_CODES:
                print(f"Failed to set NTC B value: {self.ERROR_CODES[error_code]}")
            else:
                print(f"Failed to set NTC B value: unknown error code 0x{error_code:02X}")

        return False

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================