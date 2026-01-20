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

    """

    def __init__(self, uart):
        """
        初始化数据处理器。

        Args:
            uart (UART): 已初始化的串口实例，用于数据收发。
        """
        self.uart = uart
        self.buffer = bytearray()
        self.stats = {
            'total_bytes_received': 0,
            'total_frames_parsed': 0,
            'crc_errors': 0,
            'frame_errors': 0,
            'invalid_frames': 0,
            'command_frames': 0,  # 指令帧计数
            'data_frames': 0,  # 数据帧计数
            'timeout_frames': 0  # 超时帧计数（如果协议支持）
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
            if current_pos + self.HEADER_LEN + self.TYPE_LEN + self.LENGTH_LEN > len(self.buffer):
                break

            # 解析数据长度（1字节）
            length_pos = current_pos + self.HEADER_LEN + self.TYPE_LEN
            data_len = self.buffer[length_pos]

            # 计算完整帧长度
            total_frame_len = (self.HEADER_LEN + self.TYPE_LEN + self.LENGTH_LEN +
                               data_len + self.CRC_LEN + self.TRAILER_LEN)

            # 检查是否有完整的帧
            if current_pos + total_frame_len > len(self.buffer):
                break

            # 提取完整帧数据
            frame_end = current_pos + total_frame_len
            frame_data = self.buffer[current_pos:frame_end]

            # 验证帧尾
            if self._validate_trailer(frame_data):
                self.stats['frame_errors'] += 1
                # 帧尾错误，跳过这个帧头，继续查找下一个
                processed_bytes = current_pos + 1
                continue

            # 验证校验和
            if frame_data[-3] != self._calculate_crc(frame_data[0:-3]):
                self.stats['crc_errors'] += 1
                # 校验错误，跳过这个帧，继续查找下一个
                processed_bytes = current_pos + total_frame_len
                continue

            # 解析单帧
            parsed_frame = self._parse_single_frame(frame_data)
            if parsed_frame:
                frames.append(parsed_frame)
                self.stats['total_frames_parsed'] += 1

                # 根据帧类型更新统计
                frame_type = parsed_frame.get('frame_type')
                if frame_type == self.FRAME_TYPE_COMMAND:
                    self.stats['command_frames'] += 1
                elif frame_type == self.FRAME_TYPE_DATA:
                    self.stats['data_frames'] += 1
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
        """
        if len(frame_data) < 2:
            return False
        return (frame_data[-2] == self.TRAILER[0] and
                frame_data[-1] == self.TRAILER[1])

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
        """
        try:
            pos = 0

            # 解析帧头 (2字节)
            header = bytes(frame_data[pos:pos + 2])
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
            trailer = bytes(frame_data[pos:pos + 2])

            # 构建解析结果
            parsed_frame = {
                'header': header,
                'frame_type': frame_type,
                'data_length': data_length,
                'data': data,
                'crc_check': crc_check,
                'trailer': trailer,
                'raw_data': bytes(frame_data),
                'frame_type_str': self._get_frame_type_string(frame_type)
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
        """
        return self.stats.copy()

    def clear_buffer(self):
        """
        清空缓冲区。

        Returns:
            None
        """
        self.buffer = bytearray()

    def build_and_send_frame(self, frame_type, data=b''):
        """
        构建并发送数据帧。

        Args:
            frame_type (int): 帧类型（0x01=指令帧，0x02=数据帧）。
            data (bytes): 数据部分，默认为空字节。

        Returns:
            bytes|None: 构建好的完整帧数据，发送失败返回None。
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
        """
        return self.build_and_send_frame(self.FRAME_TYPE_COMMAND, command_data)

    def build_and_send_data(self, sensor_data):
        """
        构建并发送数据帧（便捷方法）。

        Args:
            sensor_data (bytes): 传感器数据。

        Returns:
            bytes|None: 构建好的完整帧数据，发送失败返回None。
        """
        return self.build_and_send_frame(self.FRAME_TYPE_DATA, sensor_data)

    def reset_stats(self):
        """
        重置统计信息。

        Returns:
            None
        """
        for key in self.stats:
            self.stats[key] = 0