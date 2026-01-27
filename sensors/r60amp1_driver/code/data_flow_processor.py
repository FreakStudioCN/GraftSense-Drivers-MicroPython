# Python env   : MicroPython v1.26.1
# -*- coding: utf-8 -*-        
# @Time    : 2025/11/4 下午6:38   
# @Author  : 李清水            
# @File    : data_flow_processor.py
# @Description : 用于处理R60ABD1雷达设备串口通信协议的数据流处理器类相关代码
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class DataFlowProcessor:
    """
    R60ABD1 雷达设备串口通信协议的数据流处理器类。
    负责处理雷达设备的串口数据通信，包括数据帧的接收、解析、校验和发送。

    Attributes:
        uart (UART): 串口通信实例，用于数据收发。
        buffer (bytearray): 数据缓冲区，用于存储接收到的原始字节数据。
        stats (dict): 数据流转与解析统计信息字典，包含：
            total_bytes_received (int): 总接收字节数
            total_frames_parsed (int): 总解析帧数
            crc_errors (int): CRC校验错误次数
            frame_errors (int): 帧结构错误次数
            invalid_frames (int): 无效帧次数
        max_buffer_size (int): 缓冲区最大容量限制。

    Methods:
        __init__(uart): 初始化数据流处理器。
        read_and_parse(): 读取串口数据并解析完整帧。
        _find_header(start_pos=0): 在缓冲区中查找帧头位置。
        _parse_data_length(length_pos): 解析数据长度（大端格式）。
        _validate_trailer(frame_data): 验证帧尾。
        _validate_crc(frame_data): 验证CRC校验码。
        _parse_single_frame(frame_data): 解析单个数据帧。
        get_stats(): 获取数据流转与解析统计信息。
        clear_buffer(): 清空缓冲区。
        build_and_send_frame(control_byte, command_byte, data=b''): 构建并发送数据帧。
        _calculate_crc(data_bytes): 计算CRC校验码。

    ==========================================
    Data flow processor class for R60ABD1 radar device UART communication protocol.
    Handles UART data communication for radar devices, including data frame reception,
    parsing, validation, and transmission.

    Attributes:
        uart (UART): UART communication instance for data transmission and reception.
        buffer (bytearray): Data buffer for storing received raw byte data.
        stats (dict): Data flow and parsing statistics dictionary containing:
            total_bytes_received (int): Total bytes received
            total_frames_parsed (int): Total frames parsed
            crc_errors (int): CRC validation error count
            frame_errors (int): Frame structure error count
            invalid_frames (int): Invalid frame count
        max_buffer_size (int): Maximum buffer capacity limit.

    Methods:
        __init__(uart): Initialize data flow processor.
        read_and_parse(): Read UART data and parse complete frames.
        _find_header(start_pos=0): Find frame header position in buffer.
        _parse_data_length(length_pos): Parse data length (big-endian format).
        _validate_trailer(frame_data): Validate frame trailer.
        _validate_crc(frame_data): Validate CRC checksum.
        _parse_single_frame(frame_data): Parse single data frame.
        get_stats(): Get data flow and parsing statistics.
        clear_buffer(): Clear buffer.
        build_and_send_frame(control_byte, command_byte, data=b''): Build and send data frame.
        _calculate_crc(data_bytes): Calculate CRC checksum.
    """
    def __init__(self, uart):
        """
        初始化数据流处理器。

        Args:
            uart (UART): 已初始化的串口实例，用于数据收发。

        Returns:
            None

        Note:
            - 初始化时创建空缓冲区和统计信息字典。
            - 定义帧结构相关常量，包括帧头、帧尾、各字段长度等。
            - 设置缓冲区最大容量为128字节，防止内存溢出。

        ==========================================

        Initialize data flow processor.

        Args:
            uart (UART): Initialized UART instance for data transmission and reception.

        Returns:
            None

        Note:
            - Creates empty buffer and statistics dictionary during initialization.
            - Defines frame structure constants including header, trailer, field lengths, etc.
            - Sets maximum buffer capacity to 128 bytes to prevent memory overflow.
        """
        self.uart = uart
        self.buffer = bytearray()
        self.stats = {
            'total_bytes_received': 0,
            'total_frames_parsed': 0,
            'crc_errors': 0,
            'frame_errors': 0,
            'invalid_frames': 0
        }

        self.max_buffer_size = 128

        # 帧结构常量定义
        self.HEADER = bytes([0x53, 0x59])
        self.TRAILER = bytes([0x54, 0x43])
        self.HEADER_LEN = 2
        self.CONTROL_LEN = 1
        self.COMMAND_LEN = 1
        self.LENGTH_LEN = 2
        self.CRC_LEN = 1
        self.TRAILER_LEN = 2
        self.MIN_FRAME_LEN = self.HEADER_LEN + self.CONTROL_LEN + self.COMMAND_LEN + self.LENGTH_LEN + self.CRC_LEN + self.TRAILER_LEN

    def read_and_parse(self):
        """
        读取串口数据并解析完整帧。

        Args:
            无

        Returns:
            list: 解析成功的数据帧列表，每个元素为解析后的帧字典。
            []: 无完整帧或解析失败时返回空列表。

        Raises:
            Exception: 底层串口操作可能抛出的异常会向上传播。

        Note:
            - 每次读取最多32字节数据，避免阻塞时间过长。
            - 采用滑动窗口方式处理缓冲区，逐步解析完整帧。
            - 自动处理CRC校验和帧结构验证，统计各类错误信息。
            - 方法执行期间会更新统计信息，调用get_stats()可获取最新状态。

        ==========================================

        Read UART data and parse complete frames.

        Args:
            None

        Returns:
            list: List of successfully parsed data frames, each element is a parsed frame dictionary.
            []: Returns empty list when no complete frames or parsing fails.

        Raises:
            Exception: Underlying UART operations may raise exceptions that propagate upward.

        Note:
            - Reads up to 32 bytes per call to avoid long blocking times.
            - Uses sliding window approach to process buffer and gradually parse complete frames.
            - Automatically handles CRC validation and frame structure verification, statistics various error types.
            - Updates statistics during execution, call get_stats() to get latest status.
        """
        # 读取串口数据
        data = self.uart.read(32)
        if not data:
            return []

        # 更新统计信息
        self.stats['total_bytes_received'] += len(data)

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
            if current_pos + self.HEADER_LEN + self.CONTROL_LEN + self.COMMAND_LEN + self.LENGTH_LEN > len(self.buffer):
                break

            # 解析数据长度（大端格式）
            length_pos = current_pos + self.HEADER_LEN + self.CONTROL_LEN + self.COMMAND_LEN
            data_len = self._parse_data_length(length_pos)

            # 计算完整帧长度
            total_frame_len = self.HEADER_LEN + self.CONTROL_LEN + self.COMMAND_LEN + self.LENGTH_LEN + data_len + self.CRC_LEN + self.TRAILER_LEN

            # 检查是否有完整的帧
            if current_pos + total_frame_len > len(self.buffer):
                break

            # 提取完整帧数据
            frame_end = current_pos + total_frame_len
            frame_data = self.buffer[current_pos:frame_end]

            # 验证帧尾
            if not self._validate_trailer(frame_data):
                self.stats['frame_errors'] += 1
                # 帧尾错误，跳过这个帧头，继续查找下一个
                processed_bytes = current_pos + 1
                continue

            # 验证CRC
            if not self._validate_crc(frame_data):
                self.stats['crc_errors'] += 1
                # CRC错误，跳过这个帧，继续查找下一个
                processed_bytes = current_pos + total_frame_len
                continue

            # 解析单帧
            parsed_frame = self._parse_single_frame(frame_data)
            if parsed_frame:
                frames.append(parsed_frame)
                self.stats['total_frames_parsed'] += 1
            else:
                self.stats['invalid_frames'] += 1

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

        Note:
            - 帧头为固定字节序列 [0x53, 0x59]。
            - 搜索范围从start_pos到缓冲区末尾-1（需要连续两个字节）。
            - 采用线性搜索算法，时间复杂度O(n)。

        ==========================================

        Find frame header position in buffer.

        Args:
            start_pos (int): Starting search position, defaults to 0.

        Returns:
            int: Found header position index, returns -1 if not found.

        Note:
            - Frame header is fixed byte sequence [0x53, 0x59].
            - Search range from start_pos to buffer end-1 (requires two consecutive bytes).
            - Uses linear search algorithm with O(n) time complexity.
        """
        for i in range(start_pos, len(self.buffer) - 1):
            if self.buffer[i] == self.HEADER[0] and self.buffer[i + 1] == self.HEADER[1]:
                return i
        return -1

    def _parse_data_length(self, length_pos):
        """
        解析数据长度（大端格式）。

        Args:
            length_pos (int): 长度字段在缓冲区中的起始位置。

        Returns:
            int: 解析出的数据长度值，解析失败返回0。

        Note:
            - 长度字段采用大端格式存储：高字节在前，低字节在后。
            - 需要确保length_pos+1不超出缓冲区范围。
            - 返回值为数据部分的实际字节长度。

        ==========================================

        Parse data length (big-endian format).

        Args:
            length_pos (int): Starting position of length field in buffer.

        Returns:
            int: Parsed data length value, returns 0 if parsing fails.

        Note:
            - Length field uses big-endian format: high byte first, low byte last.
            - Ensures length_pos+1 does not exceed buffer bounds.
            - Return value is the actual byte length of data portion.
        """
        if length_pos + 1 >= len(self.buffer):
            return 0
        # 大端格式：高字节在前，低字节在后
        return (self.buffer[length_pos] << 8) | self.buffer[length_pos + 1]

    def _validate_trailer(self, frame_data):
        """
        验证帧尾。

        Args:
            frame_data (bytes|bytearray): 完整帧数据。

        Returns:
            bool: 帧尾验证通过返回True，否则返回False。

        Note:
            - 帧尾为固定字节序列 [0x54, 0x43]。
            - 检查帧数据最后两个字节是否匹配帧尾。
            - 帧尾验证失败表明帧结构不完整或数据损坏。

        ==========================================

        Validate frame trailer.

        Args:
            frame_data (bytes|bytearray): Complete frame data.

        Returns:
            bool: Returns True if trailer validation passes, False otherwise.

        Note:
            - Frame trailer is fixed byte sequence [0x54, 0x43].
            - Checks if last two bytes of frame data match trailer.
            - Trailer validation failure indicates incomplete frame structure or data corruption.
        """
        if len(frame_data) < 2:
            return False
        return (frame_data[-2] == self.TRAILER[0] and
                frame_data[-1] == self.TRAILER[1])

    def _validate_crc(self, frame_data):
        """
        验证CRC校验码。

        Args:
            frame_data (bytes|bytearray): 完整帧数据。

        Returns:
            bool: CRC验证通过返回True，否则返回False。

        Note:
            - CRC校验范围：帧头到数据部分（不包括CRC字节和帧尾）。
            - 计算方式：对校验数据求和后取低8位。
            - CRC位于帧数据倒数第3个字节位置。

        ==========================================

        Validate CRC checksum.

        Args:
            frame_data (bytes|bytearray): Complete frame data.

        Returns:
            bool: Returns True if CRC validation passes, False otherwise.

        Note:
            - CRC check range: from header to data portion (excluding CRC byte and trailer).
            - Calculation method: sum check data and take lower 8 bits.
            - CRC is located at the third last byte of frame data.
        """
        if len(frame_data) < 3:
            return False

        # 计算校验和（不包括CRC字节和帧尾）
        data_to_check = frame_data[:-3]
        calculated_crc = sum(data_to_check) & 0xFF
        received_crc = frame_data[-3]

        return calculated_crc == received_crc

    def _parse_single_frame(self, frame_data):
        """
        解析单个数据帧。

        Args:
            frame_data (bytes|bytearray): 完整帧数据。

        Returns:
            dict|None: 解析成功返回帧信息字典，解析失败返回None。

        Raises:
            Exception: 解析过程中发生异常时记录错误信息。

        Note:
            - 按协议格式依次解析：帧头→控制字→命令字→长度字段→数据→CRC→帧尾。
            - 返回字典包含所有解析出的字段和原始数据。
            - 解析失败会记录到invalid_frames统计中。

        ==========================================

        Parse single data frame.

        Args:
            frame_data (bytes|bytearray): Complete frame data.

        Returns:
            dict|None: Returns frame information dictionary on success, None on failure.

        Raises:
            Exception: Records error information when exceptions occur during parsing.

        Note:
            - Parses sequentially according to protocol format: header→control→command→length→data→CRC→trailer.
            - Return dictionary contains all parsed fields and raw data.
            - Parsing failures are recorded in invalid_frames statistics.
        """
        try:
            pos = 0

            # 解析帧头 (2字节)
            header = bytes(frame_data[pos:pos + 2])
            pos += 2

            # 控制字 (1字节)
            control_byte = frame_data[pos]
            pos += 1

            # 命令字 (1字节)
            command_byte = frame_data[pos]
            pos += 1

            # 长度标识 (2字节)
            data_length = (frame_data[pos] << 8) | frame_data[pos + 1]
            pos += 2

            # 数据 (n字节)
            data_end = pos + data_length
            if data_end > len(frame_data) - 3:  # -3 为CRC(1)+帧尾(2)
                return None
            data = bytes(frame_data[pos:data_end])
            pos = data_end

            # CRC (1字节)
            crc = frame_data[pos]
            pos += 1

            # 帧尾 (2字节)
            trailer = bytes(frame_data[pos:pos + 2])

            # 构建解析结果
            parsed_frame = {
                'header': header,
                'control_byte': control_byte,
                'command_byte': command_byte,
                'data_length': data_length,
                'data': data,
                'crc': crc,
                'trailer': trailer,
                'raw_data': bytes(frame_data)
            }

            return parsed_frame

        except Exception as e:
            print(f"Frame parsing error: {e}")
            return None

    def get_stats(self):
        """
        获取数据流转与解析统计信息。

        Args:
            无

        Returns:
            dict: 包含所有统计信息的字典副本。

        Note:
            - 返回统计信息的深拷贝，防止外部修改影响内部数据。
            - 统计信息包括：接收字节数、解析帧数、各类错误计数等。

        ==========================================

        Get data flow and parsing statistics.

        Args:
            None

        Returns:
            dict: Dictionary containing all statistics information (copy).

        Note:
            - Returns deep copy of statistics to prevent external modifications affecting internal data.
            - Statistics include: received bytes, parsed frames, various error counts, etc.
        """
        return self.stats.copy()

    def clear_buffer(self):
        """
        清空缓冲区。

        Args:
            无

        Returns:
            None

        Note:
            - 将缓冲区重置为空bytearray。
            - 通常在缓冲区过大或需要重新开始解析时调用。

        ==========================================

        Clear buffer.

        Args:
            None

        Returns:
            None

        Note:
            - Resets buffer to empty bytearray.
            - Typically called when buffer is too large or need to restart parsing.
        """
        self.buffer = bytearray()

    def build_and_send_frame(self, control_byte, command_byte, data=b''):
        """
        构建并发送数据帧。

        Args:
            control_byte (int): 控制字，1字节无符号整数。
            command_byte (int): 命令字，1字节无符号整数。
            data (bytes): 数据部分，默认为空字节。

        Returns:
            bytes|None: 构建好的完整帧数据（用于调试），发送失败返回None。

        Raises:
            Exception: 帧构建或发送过程中发生异常时记录错误信息。

        Note:
            - 按照协议格式构建完整帧：帧头→控制字→命令字→长度→数据→CRC→帧尾。
            - 自动计算数据长度和CRC校验码。
            - 通过串口发送构建好的帧数据。

        ==========================================

        Build and send data frame.

        Args:
            control_byte (int): Control byte, 1-byte unsigned integer.
            command_byte (int): Command byte, 1-byte unsigned integer.
            data (bytes): Data portion, defaults to empty bytes.

        Returns:
            bytes|None: Built complete frame data (for debugging), returns None on send failure.

        Raises:
            Exception: Records error information when exceptions occur during frame building or sending.

        Note:
            - Builds complete frame according to protocol format: header→control→command→length→data→CRC→trailer.
            - Automatically calculates data length and CRC checksum.
            - Sends built frame data via UART.
        """
        try:
            # 帧头
            header = self.HEADER

            # 控制字和命令字
            control = bytes([control_byte])
            command = bytes([command_byte])

            # 数据长度（大端格式）
            data_length = len(data)
            length_bytes = bytes([(data_length >> 8) & 0xFF, data_length & 0xFF])

            # 组装除CRC和帧尾的部分
            frame_without_crc = header + control + command + length_bytes + data

            # 计算CRC
            crc = self._calculate_crc(frame_without_crc)

            # 帧尾A
            trailer = self.TRAILER

            # 完整帧
            complete_frame = frame_without_crc + bytes([crc]) + trailer

            # 发送帧
            self.uart.write(complete_frame)

            return complete_frame

        except Exception as e:
            print(f"Frame building and sending error: {e}")
            return None

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

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================