# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/12 上午11:22
# @Author  : hogeiha
# @File    : ba111_tds.py
# @Description : DHT11温湿度传感器驱动代码
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
        0x01: "命令帧异常",
        0x02: "忙码中",
        0x03: "校正失败",
        0x04: "检测温度超出范围"
    }

    def __init__(self, uart: UART):
        self._uart = uart
        self._timeout = 2000  # 超时时间（毫秒）
        self.ntc_resistance = 10000  # 默认NTC常温电阻（单位Ω）
        self.ntc_b_value = 3950  # 默认NTC B值
        self.tds_value = 0.0  # TDS值（ppm）
        self.temperature = 0.0  # 温度值（℃）

    def _calculate_crc(self, data_bytes):
        """
        计算CRC校验码。
        """
        return sum(data_bytes) & 0xFF

    def _validate_crc(self, frame_data):
        """
        验证CRC校验码。
        """
        # 计算校验和（不包括CRC字节和帧尾）
        data_to_check = frame_data[:-1]
        calculated_crc = sum(data_to_check) & 0xFF
        received_crc = frame_data[-1]

        return calculated_crc == received_crc

    def _build_frame(self, command, parameters=bytes([0x00, 0x00, 0x00, 0x00])):
        """
        构建完整的帧结构：命令(1B) + 参数(4B) + CRC(1B)
        """
        if len(parameters) != 4:
            raise ValueError("参数长度必须为4字节")

        frame = command + parameters
        crc = self._calculate_crc(frame)
        return frame + bytes([crc])

    def _send_and_receive(self, frame, response_length=6):
        """
        发送帧并接收响应
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
        发送检测指令，返回(TDS值(ppm), 温度值(℃))，失败返回None
        """
        # 构建检测指令帧
        frame = self._build_frame(self.READ_TDS_TEMPERATURE)

        # 发送并接收响应
        response = self._send_and_receive(frame)

        if not response :
            return None

        # 验证响应格式（首字节应为0xAA）
        if response[0] != 0xAA:
            return None

        # 验证CRC
        if self._validate_crc(response):
            return None

        # 解析TDS值（第2-3字节，大端序）
        tds_raw = (response[1] << 8) | response[2]
        tds_value = float(tds_raw)  # 单位为ppm
        self.tds_value = tds_value
        print(tds_value)
        # 解析温度值（第4-5字节，大端序）
        temp_raw = (response[3] << 8) | response[4]
        temp_value = float(temp_raw) / 100.0  # 除以100得到℃
        self.temperature = temp_value
        print(temp_value)

        return (tds_value, temp_value)

    def calibrate(self) -> bool:
        """
        发送基线校准指令，返回校准是否成功（True/False）
        注意：校准前请确保传感器在25℃±5℃的纯净水中
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
                print(f"校准失败: {self.ERROR_CODES[error_code]}")
            else:
                print(f"校准失败: 未知错误码 0x{error_code:02X}")

        return False

    def set_ntc_resistance(self, resistance: int) -> bool:
        """
        设置 NTC 常温电阻（单位 Ω），返回设置是否成功（True/False）
        """
        # 检查参数范围
        if resistance < 0 or resistance > 0xFFFFFFFF:
            print(f"电阻值 {resistance}Ω 超出范围")
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
                print(f"设置NTC电阻失败: {self.ERROR_CODES[error_code]}")
            else:
                print(f"设置NTC电阻失败: 未知错误码 0x{error_code:02X}")

        return False

    def set_ntc_b_value(self, b_value: int) -> bool:
        """
        设置 NTC B 值，返回设置是否成功（True/False）
        """
        # 检查参数范围
        if b_value < 0 or b_value > 0xFFFF:
            print(f"B值 {b_value} 超出范围")
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
                print(f"设置NTC B值失败: {self.ERROR_CODES[error_code]}")
            else:
                print(f"设置NTC B值失败: 未知错误码 0x{error_code:02X}")

        return False

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
