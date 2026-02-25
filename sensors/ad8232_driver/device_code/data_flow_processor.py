# Python env   : MicroPython v1.24.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : data_flow_processor.py
# @Description : 串口数据帧构建解析
# @License : MIT

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.24 with ulab"

# ======================================== 导入相关模块 =========================================


class DataFlowProcessor:
    """
    新协议数据处理器类。
    按照新协议格式处理串口数据通信，包括数据帧的接收、解析、校验和发送。

    协议格式：
    字段	字节数	取值 / 说明
    帧头	2	    0xAA 0x55	固定标识，区分有效帧
    类型	1	    0x01：指令帧；0x02：数据帧	区分上位机指令/模块数据
    长度	1	    后续"数据"字段的字节数（0~255）	便于解析
    数据	N	    指令/数据内容（见下文定义）	可变长度
    校验	1	    帧头+类型+长度+数据的校验和	校验帧完整性
    帧尾	2	    0x0D 0x0A	回车换行，简化上位机解析

    Attributes:
        uart (UART): UART串口通信实例。
        buffer (bytearray): 数据接收缓冲区。
        stats (dict): 数据流统计信息字典。
        max_buffer_size (int): 缓冲区最大容量。
        HEADER (bytes): 帧头常量字节序列。
        TRAILER (bytes): 帧尾常量字节序列。
        HEADER_LEN (int): 帧头长度。
        TYPE_LEN (int): 帧类型字段长度。
        LENGTH_LEN (int): 数据长度字段长度。
        CRC_LEN (int): CRC校验字段长度。
        TRAILER_LEN (int): 帧尾长度。
        MIN_FRAME_LEN (int): 最小有效帧长度。
        FRAME_TYPE_COMMAND (int): 指令帧类型标识。
        FRAME_TYPE_DATA (int): 数据帧类型标识。

    Methods:
        __init__(): 初始化数据处理器。
        read_and_parse(): 读取串口数据并解析完整帧。
        _find_header(): 在缓冲区中查找帧头位置。
        _validate_trailer(): 验证帧尾。
        _calculate_crc(): 计算CRC校验码。
        _parse_single_frame(): 解析单个数据帧。
        _get_frame_type_string(): 获取帧类型的字符串描述。
        get_stats(): 获取数据流转与解析统计信息。
        clear_buffer(): 清空缓冲区。
        build_and_send_frame(): 构建并发送数据帧。
        build_and_send_command(): 构建并发送指令帧（便捷方法）。
        build_and_send_data(): 构建并发送数据帧（便捷方法）。
        reset_stats(): 重置统计信息。

    ==========================================

    New protocol data processor class.
    Processes serial data communication according to new protocol format,
    including data frame reception, parsing, validation, and transmission.

    Protocol format:
    Field   Bytes   Value / Description
    Header  2       0xAA 0x55    Fixed identifier for valid frames
    Type    1       0x01: Command frame; 0x02: Data frame    Distinguishes host commands/module data
    Length  1       Number of bytes in following "Data" field (0~255)    Facilitates parsing
    Data    N       Command/data content (see definitions below)    Variable length
    CRC     1       Checksum of header+type+length+data    Verifies frame integrity
    Trailer 2       0x0D 0x0A    Carriage return line feed, simplifies host parsing

    Attributes:
        uart (UART): UART serial communication instance.
        buffer (bytearray): Data reception buffer.
        stats (dict): Data flow statistics dictionary.
        max_buffer_size (int): Maximum buffer capacity.
        HEADER (bytes): Frame header constant byte sequence.
        TRAILER (bytes): Frame trailer constant byte sequence.
        HEADER_LEN (int): Header length.
        TYPE_LEN (int): Frame type field length.
        LENGTH_LEN (int): Data length field length.
        CRC_LEN (int): CRC checksum field length.
        TRAILER_LEN (int): Trailer length.
        MIN_FRAME_LEN (int): Minimum valid frame length.
        FRAME_TYPE_COMMAND (int): Command frame type identifier.
        FRAME_TYPE_DATA (int): Data frame type identifier.

    Methods:
        __init__(): Initialize data processor.
        read_and_parse(): Read serial data and parse complete frames.
        _find_header(): Find header position in buffer.
        _validate_trailer(): Validate frame trailer.
        _calculate_crc(): Calculate CRC checksum.
        _parse_single_frame(): Parse single data frame.
        _get_frame_type_string(): Get frame type string description.
        get_stats(): Get data flow and parsing statistics.
        clear_buffer(): Clear buffer.
        build_and_send_frame(): Build and send data frame.
        build_and_send_command(): Build and send command frame (convenience method).
        build_and_send_data(): Build and send data frame (convenience method).
        reset_stats(): Reset statistics.
    """

    # ======================================== 全局变量 ============================================

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    def __init__(self, uart):
        """
        初始化数据处理器。

        Args:
            uart (UART): 已初始化的串口实例，用于数据收发。

        Note:
            - 初始化时会重置所有统计计数器。
            - 缓冲区默认最大容量为256字节。
            - 遵循AA55开头、0D0A结尾的帧协议格式。

        ==========================================

        Initialize data processor.

        Args:
            uart (UART): Initialized serial port instance for data transmission/reception.

        Note:
            - All statistical counters are reset upon initialization.
            - Default maximum buffer capacity is 256 bytes.
            - Follows frame protocol format starting with AA55 and ending with 0D0A.
        """
        self.uart = uart
        self.buffer = bytearray()
        self.stats = {
            "total_bytes_received": 0,
            "total_frames_parsed": 0,
            "crc_errors": 0,
            "frame_errors": 0,
            "invalid_frames": 0,
            "command_frames": 0,  # 指令帧计数
            "data_frames": 0,  # 数据帧计数
            "timeout_frames": 0,  # 超时帧计数（如果协议支持）
        }

        self.max_buffer_size = 256

        # 帧结构常量定义
        self.HEADER = bytes([0xAA, 0x55])
        self.TRAILER = bytes([0x0D, 0x0A])
        self.HEADER_LEN = 2
        self.TYPE_LEN = 1
        self.LENGTH_LEN = 1
        self.CRC_LEN = 1
        self.TRAILER_LEN = 2
        self.MIN_FRAME_LEN = self.HEADER_LEN + self.TYPE_LEN + self.LENGTH_LEN + self.CRC_LEN + self.TRAILER_LEN

        # 帧类型定义
        self.FRAME_TYPE_COMMAND = 0x01  # 指令帧
        self.FRAME_TYPE_DATA = 0x02  # 数据帧

    def read_and_parse(self):
        """
        读取串口数据并解析完整帧。

        Returns:
            list: 解析成功的数据帧列表，每个元素为解析后的帧字典。
            []: 无完整帧或解析失败时返回空列表。

        Process:
            1. 从串口读取最多32字节数据。
            2. 将数据追加到内部缓冲区。
            3. 在缓冲区中查找并解析所有完整帧。
            4. 更新相关统计信息。
            5. 清理已处理的缓冲区数据。

        ==========================================

        Read serial data and parse complete frames.

        Returns:
            list: List of successfully parsed data frames, each element is a parsed frame dictionary.
            []: Returns empty list when no complete frames are found or parsing fails.

        Process:
            1. Read up to 32 bytes of data from serial port.
            2. Append data to internal buffer.
            3. Find and parse all complete frames in buffer.
            4. Update relevant statistical information.
            5. Clean up processed buffer data.
        """
        # 读取串口数据
        data = self.uart.read(32)
        if not data:
            return []

        # 更新统计信息
        self.stats["total_bytes_received"] += len(data)

        # 检查缓冲区大小
        if len(self.buffer) > self.max_buffer_size:
            self.clear_buffer()

        # 将数据添加到缓冲区
        self.buffer.extend(data)

        frames = []
        processed_bytes = 0

        while len(self.buffer) - processed_bytes >= self.MIN_FRAME_LEN:
            # 查找帧头
            header_pos = self._find_header(processed_bytes)
            if header_pos == -1:
                # 没有找到更多帧头，跳出循环
                break

            # 从找到的帧头位置开始
            current_pos = header_pos

            # 检查是否有足够数据解析长度字段
            if current_pos + self.HEADER_LEN + self.TYPE_LEN + self.LENGTH_LEN > len(self.buffer):
                break

            # 解析数据长度（1字节）
            length_pos = current_pos + self.HEADER_LEN + self.TYPE_LEN
            data_len = self.buffer[length_pos]

            # 计算完整帧长度
            total_frame_len = self.HEADER_LEN + self.TYPE_LEN + self.LENGTH_LEN + data_len + self.CRC_LEN + self.TRAILER_LEN

            # 检查是否有完整的帧
            if current_pos + total_frame_len > len(self.buffer):
                break

            # 提取完整帧数据
            frame_end = current_pos + total_frame_len
            frame_data = self.buffer[current_pos:frame_end]

            # 验证帧尾
            if not self._validate_trailer(frame_data):
                self.stats["frame_errors"] += 1
                # 帧尾错误，跳过这个帧头，继续查找下一个
                processed_bytes = current_pos + 1
                continue

            # 验证校验和
            if frame_data[-3] != self._calculate_crc(frame_data[0:-3]):
                self.stats["crc_errors"] += 1
                # 校验错误，跳过这个帧，继续查找下一个
                processed_bytes = current_pos + total_frame_len
                continue

            # 解析单帧
            parsed_frame = self._parse_single_frame(frame_data)
            if parsed_frame:
                frames.append(parsed_frame)
                self.stats["total_frames_parsed"] += 1

                # 根据帧类型更新统计
                frame_type = parsed_frame.get("frame_type")
                if frame_type == self.FRAME_TYPE_COMMAND:
                    self.stats["command_frames"] += 1
                elif frame_type == self.FRAME_TYPE_DATA:
                    self.stats["data_frames"] += 1
            else:
                self.stats["invalid_frames"] += 1

            # 移动到下一帧
            processed_bytes = current_pos + total_frame_len

        # 清理已处理的数据
        if processed_bytes > 0:
            self.buffer = self.buffer[processed_bytes:]

        return frames

    def _find_header(self, start_pos=0):
        """
        在缓冲区中查找帧头位置。

        Args:
            start_pos (int): 起始搜索位置，默认为0。

        Returns:
            int: 找到的帧头位置索引，未找到返回-1。

        Algorithm:
            - 从start_pos开始遍历缓冲区，查找连续的0xAA 0x55字节序列。
            - 遇到缓冲区末尾前一个字节停止搜索。

        ==========================================

        Find header position in buffer.

        Args:
            start_pos (int): Starting search position, defaults to 0.

        Returns:
            int: Found header position index, returns -1 if not found.

        Algorithm:
            - Traverse buffer starting from start_pos, looking for consecutive 0xAA 0x55 byte sequence.
            - Stop search when reaching second-to-last byte of buffer.
        """
        for i in range(start_pos, len(self.buffer) - 1):
            if self.buffer[i] == self.HEADER[0] and self.buffer[i + 1] == self.HEADER[1]:
                return i
        return -1

    def _validate_trailer(self, frame_data):
        """
        验证帧尾。

        Args:
            frame_data (bytes|bytearray): 完整帧数据。

        Returns:
            bool: 帧尾验证通过返回True，否则返回False。

        Note:
            - 验证帧数据最后两个字节是否为0x0D 0x0A。
            - 帧尾错误通常表示数据损坏或同步丢失。

        ==========================================

        Validate frame trailer.

        Args:
            frame_data (bytes|bytearray): Complete frame data.

        Returns:
            bool: Returns True if trailer validation passes, otherwise False.

        Note:
            - Verifies if last two bytes of frame data are 0x0D 0x0A.
            - Trailer errors typically indicate data corruption or synchronization loss.
        """
        if len(frame_data) < 2:
            return False
        return frame_data[-2] == self.TRAILER[0] and frame_data[-1] == self.TRAILER[1]

    def _calculate_crc(self, data_bytes):
        """
        计算CRC校验码。

        Args:
            data_bytes (bytes): 需要计算CRC的数据字节序列。

        Returns:
            int: 计算出的CRC校验码（1字节）。

        Note:
            - 校验码计算：对输入数据所有字节求和后，取低8位。
            - 此CRC算法为简单求和校验，适用于基本错误检测。
            - CRC校验范围通常为帧头到数据部分。

        ==========================================

        Calculate CRC checksum.

        Args:
            data_bytes (bytes): Data byte sequence for CRC calculation.

        Returns:
            int: Calculated CRC checksum (1 byte).

        Note:
            - Checksum calculation: sum all input data bytes and take lower 8 bits.
            - This CRC algorithm uses simple sum check, suitable for basic error detection.
            - CRC check range typically from header to data portion.
        """
        return sum(data_bytes) & 0xFF

    def _parse_single_frame(self, frame_data):
        """
        解析单个数据帧。

        Args:
            frame_data (bytes|bytearray): 完整帧数据。

        Returns:
            dict|None: 解析成功返回帧信息字典，解析失败返回None。

        Frame structure:
            - Header (2 bytes): 0xAA 0x55
            - Frame type (1 byte): 0x01 or 0x02
            - Data length (1 byte): 0-255
            - Data (N bytes): Actual payload
            - CRC (1 byte): Checksum
            - Trailer (2 bytes): 0x0D 0x0A

        ==========================================

        Parse single data frame.

        Args:
            frame_data (bytes|bytearray): Complete frame data.

        Returns:
            dict|None: Returns frame information dictionary if parsing succeeds, otherwise None.

        Frame structure:
            - Header (2 bytes): 0xAA 0x55
            - Frame type (1 byte): 0x01 or 0x02
            - Data length (1 byte): 0-255
            - Data (N bytes): Actual payload
            - CRC (1 byte): Checksum
            - Trailer (2 bytes): 0x0D 0x0A
        """
        try:
            pos = 0

            # 解析帧头 (2字节)
            header = bytes(frame_data[pos : pos + 2])
            pos += 2

            # 帧类型 (1字节)
            frame_type = frame_data[pos]
            pos += 1

            # 数据长度 (1字节)
            data_length = frame_data[pos]
            pos += 1

            # 数据 (N字节)
            data_end = pos + data_length
            if data_end > len(frame_data) - 3:  # -3 为校验位(1)+帧尾(2)
                return None
            data = bytes(frame_data[pos:data_end])
            pos = data_end

            # 校验和 (1字节)
            crc_check = frame_data[pos]
            pos += 1

            # 帧尾 (2字节)
            trailer = bytes(frame_data[pos : pos + 2])

            # 构建解析结果
            parsed_frame = {
                "header": header,
                "frame_type": frame_type,
                "data_length": data_length,
                "data": data,
                "crc_check": crc_check,
                "trailer": trailer,
                "raw_data": bytes(frame_data),
                "frame_type_str": self._get_frame_type_string(frame_type),
            }

            return parsed_frame

        except Exception as e:
            print(f"Frame parsing error: {e}")
            return None

    def _get_frame_type_string(self, frame_type):
        """
        获取帧类型的字符串描述。

        Args:
            frame_type (int): 帧类型值。

        Returns:
            str: 帧类型字符串描述。

        Supported types:
            - 0x01: "指令帧" (Command frame)
            - 0x02: "数据帧" (Data frame)
            - Others: "未知帧类型(0xXX)" (Unknown frame type)

        ==========================================

        Get frame type string description.

        Args:
            frame_type (int): Frame type value.

        Returns:
            str: Frame type string description.

        Supported types:
            - 0x01: "Command frame"
            - 0x02: "Data frame"
            - Others: "Unknown frame type(0xXX)"
        """
        if frame_type == self.FRAME_TYPE_COMMAND:
            return "指令帧"
        elif frame_type == self.FRAME_TYPE_DATA:
            return "数据帧"
        else:
            return f"未知帧类型(0x{frame_type:02X})"

    def get_stats(self):
        """
        获取数据流转与解析统计信息。

        Returns:
            dict: 包含所有统计信息的字典副本。

        Statistics include:
            - total_bytes_received: 总接收字节数
            - total_frames_parsed: 总解析帧数
            - crc_errors: CRC校验错误数
            - frame_errors: 帧结构错误数
            - invalid_frames: 无效帧数
            - command_frames: 指令帧数量
            - data_frames: 数据帧数量
            - timeout_frames: 超时帧数量

        ==========================================

        Get data flow and parsing statistics.

        Returns:
            dict: Copy of dictionary containing all statistical information.

        Statistics include:
            - total_bytes_received: Total bytes received
            - total_frames_parsed: Total frames parsed
            - crc_errors: CRC check errors
            - frame_errors: Frame structure errors
            - invalid_frames: Invalid frames
            - command_frames: Command frame count
            - data_frames: Data frame count
            - timeout_frames: Timeout frame count
        """
        return self.stats.copy()

    def clear_buffer(self):
        """
        清空缓冲区。

        Returns:
            None

        Note:
            - 通常用于处理缓冲区溢出或重置通信状态。
            - 不会影响统计计数器。

        ==========================================

        Clear buffer.

        Returns:
            None

        Note:
            - Typically used to handle buffer overflow or reset communication state.
            - Does not affect statistical counters.
        """
        self.buffer = bytearray()

    def build_and_send_frame(self, frame_type, data=b""):
        """
        构建并发送数据帧。

        Args:
            frame_type (int): 帧类型（0x01=指令帧，0x02=数据帧）。
            data (bytes): 数据部分，默认为空字节。

        Returns:
            bytes|None: 构建好的完整帧数据，发送失败返回None。

        Frame construction process:
            1. 验证数据长度不超过255字节。
            2. 构建帧头+类型+长度+数据部分。
            3. 计算CRC校验和。
            4. 添加帧尾。
            5. 通过UART发送完整帧。

        Exceptions:
            - 数据长度超限会打印错误信息并返回None。
            - 发送过程中的异常会被捕获并打印错误信息。

        ==========================================

        Build and send data frame.

        Args:
            frame_type (int): Frame type (0x01=command frame, 0x02=data frame).
            data (bytes): Data portion, defaults to empty bytes.

        Returns:
            bytes|None: Complete frame data if built successfully, None if sending fails.

        Frame construction process:
            1. Verify data length does not exceed 255 bytes.
            2. Construct header+type+length+data portion.
            3. Calculate CRC checksum.
            4. Add trailer.
            5. Send complete frame via UART.

        Exceptions:
            - Data length exceeding limit prints error message and returns None.
            - Exceptions during sending are caught and error messages printed.
        """
        try:
            # 验证数据长度
            data_length = len(data)
            if data_length > 255:
                print(f"Data length {data_length} exceeds maximum 255 bytes")
                return None

            # 帧头
            header = self.HEADER

            # 帧类型和长度
            type_byte = bytes([frame_type])
            length_byte = bytes([data_length])

            # 组装类型+长度+数据部分（用于计算校验）
            data_for_crc = header + type_byte + length_byte + data

            # 计算校验和
            crc_value = self._calculate_crc(data_for_crc)

            # 帧尾
            trailer = self.TRAILER

            # 完整帧
            complete_frame = data_for_crc + bytes([crc_value]) + trailer

            # 发送帧
            self.uart.write(complete_frame)

            return complete_frame

        except Exception as e:
            print(f"Frame building and sending error: {e}")
            return None

    def build_and_send_command(self, command_data):
        """
        构建并发送指令帧（便捷方法）。

        Args:
            command_data (bytes): 指令数据。

        Returns:
            bytes|None: 构建好的完整帧数据，发送失败返回None。

        Note:
            - 内部调用build_and_send_frame方法，指定帧类型为0x01。
            - 适用于发送控制命令、参数设置等指令操作。

        ==========================================

        Build and send command frame (convenience method).

        Args:
            command_data (bytes): Command data.

        Returns:
            bytes|None: Complete frame data if built successfully, None if sending fails.

        Note:
            - Internally calls build_and_send_frame method with frame type set to 0x01.
            - Suitable for sending control commands, parameter settings, and other command operations.
        """
        return self.build_and_send_frame(self.FRAME_TYPE_COMMAND, command_data)

    def build_and_send_data(self, sensor_data):
        """
        构建并发送数据帧（便捷方法）。

        Args:
            sensor_data (bytes): 传感器数据。

        Returns:
            bytes|None: 构建好的完整帧数据，发送失败返回None。

        Note:
            - 内部调用build_and_send_frame方法，指定帧类型为0x02。
            - 适用于发送传感器读数、状态信息等数据操作。

        ==========================================

        Build and send data frame (convenience method).

        Args:
            sensor_data (bytes): Sensor data.

        Returns:
            bytes|None: Complete frame data if built successfully, None if sending fails.

        Note:
            - Internally calls build_and_send_frame method with frame type set to 0x02.
            - Suitable for sending sensor readings, status information, and other data operations.
        """
        return self.build_and_send_frame(self.FRAME_TYPE_DATA, sensor_data)

    def reset_stats(self):
        """
        重置统计信息。

        Returns:
            None

        Note:
            - 将所有统计计数器归零。
            - 不影响缓冲区内容和通信状态。
            - 用于开始新的数据统计周期。

        ==========================================

        Reset statistics.

        Returns:
            None

        Note:
            - Resets all statistical counters to zero.
            - Does not affect buffer content or communication state.
            - Used to start new data statistics period.
        """
        for key in self.stats:
            self.stats[key] = 0


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
