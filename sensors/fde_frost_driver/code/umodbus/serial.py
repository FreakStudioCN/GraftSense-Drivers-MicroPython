# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午4:52
# @Author  : Anonymous
# @File    : modbus_rtu.py
# @Description : Modbus RTU 协议实现，包括串口通信、帧收发、CRC校验及请求处理。
# @License : MIT
__version__ = "0.1.0"
__author__ = "Anonymous"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# system packages
from machine import UART
from machine import Pin
import struct
import time

# custom packages
from . import const as Const
from . import functions
from .common import Request, CommonModbusFunctions
from .common import ModbusException
from .modbus import Modbus

# typing not natively supported on MicroPython
from .typing import List, Optional, Union

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class ModbusRTU(Modbus):
    """
    Modbus RTU 客户端类，继承自 Modbus 抽象类，使用串口作为物理层。

    该类通过串口实现 Modbus RTU 协议，支持指定从站地址、波特率、数据位、停止位、校验位等参数。
    内部使用 Serial 对象进行底层通信。

    Attributes:
        _itf (Serial): 串口接口对象。
        _addr_list (List[int]): 本设备支持的单元地址列表，此处为单个地址。

    Methods:
        __init__(): 初始化 Modbus RTU 客户端。

    Notes:
        继承自 Modbus 类，通过 Serial 封装了 UART 操作。

    ==========================================
    Modbus RTU client class, inherits from Modbus abstract class, uses serial as physical layer.

    This class implements Modbus RTU protocol over serial, supports parameters such as slave address,
    baudrate, data bits, stop bits, parity. Uses Serial object for low-level communication.

    Attributes:
        _itf (Serial): Serial interface object.
        _addr_list (List[int]): List of unit addresses supported by this device, here a single address.

    Methods:
        __init__(): Initialize Modbus RTU client.

    Notes:
        Inherits from Modbus class, wraps UART operations via Serial.
    """

    def __init__(
        self,
        addr: int,
        baudrate: int = 9600,
        data_bits: int = 8,
        stop_bits: int = 1,
        parity: Optional[int] = None,
        pins: List[Union[int, Pin], Union[int, Pin]] = None,
        ctrl_pin: int = None,
        uart_id: int = 1,
    ):
        """
        初始化 Modbus RTU 客户端。

        Args:
            addr (int): 本设备在总线上的地址。
            baudrate (int, optional): 波特率，默认9600。
            data_bits (int, optional): 数据位，默认8。
            stop_bits (int, optional): 停止位，默认1。
            parity (Optional[int], optional): 校验位，默认None。
            pins (List[Union[int, Pin], Union[int, Pin]], optional): 引脚列表 [TX, RX]。
            ctrl_pin (int, optional): 流控引脚（RS485方向控制）。
            uart_id (int, optional): UART ID，默认1。

        Notes:
            内部创建 Serial 对象并传入父类。

        ==========================================
        Initialize Modbus RTU client.

        Args:
            addr (int): The address of this device on the bus.
            baudrate (int, optional): The baudrate, default 9600.
            data_bits (int, optional): The data bits, default 8.
            stop_bits (int, optional): The stop bits, default 1.
            parity (Optional[int], optional): The parity, default None.
            pins (List[Union[int, Pin], Union[int, Pin]], optional): The pins as list [TX, RX].
            ctrl_pin (int, optional): The control pin (RS485 direction control).
            uart_id (int, optional): The ID of the used UART, default 1.

        Notes:
            Creates Serial object internally and passes to parent class.
        """
        super().__init__(
            # set itf to Serial object, addr_list to [addr]
            Serial(uart_id=uart_id, baudrate=baudrate, data_bits=data_bits, stop_bits=stop_bits, parity=parity, pins=pins, ctrl_pin=ctrl_pin),
            [addr],
        )


class Serial(CommonModbusFunctions):
    """
    串口 Modbus 通信类，实现 RTU 帧的收发、CRC 校验和请求处理。

    负责底层 UART 操作，包括计算字符间延迟、帧间延迟、CRC16、发送和接收 Modbus 帧。

    Attributes:
        _has_uart_flush (bool): 指示 UART 是否支持 flush 方法。
        _uart (UART): machine.UART 对象。
        _ctrlPin (Pin): 方向控制引脚（可选）。
        _t1char (int): 一个字符传输时间（微秒）。
        _inter_frame_delay (int): 帧间延迟（微秒）。

    Methods:
        _calculate_crc16(): 计算 CRC16 校验值。
        _exit_read(): 判断响应是否已完整读取。
        _uart_read(): 从 UART 读取响应数据（带简单超时）。
        _uart_read_frame(): 读取一个完整的 Modbus 帧。
        _send(): 发送 Modbus 帧。
        _send_receive(): 发送并接收响应。
        _validate_resp_hdr(): 验证响应头部。
        send_response(): 发送响应给客户端。
        send_exception_response(): 发送异常响应。
        get_request(): 获取请求对象。

    Notes:
        根据波特率动态计算帧间延迟：≤19200bps 时为 3.5 字符时间，否则固定 1750us。
        支持可选的 RS485 方向控制引脚。

    ==========================================
    Serial Modbus communication class implementing RTU frame sending/receiving, CRC calculation and request handling.

    Handles low-level UART operations including character timing, inter-frame delay, CRC16,
    sending and receiving Modbus frames.

    Attributes:
        _has_uart_flush (bool): Indicates whether UART supports flush method.
        _uart (UART): machine.UART object.
        _ctrlPin (Pin): Direction control pin (optional).
        _t1char (int): Transmission time of one character (microseconds).
        _inter_frame_delay (int): Inter-frame delay (microseconds).

    Methods:
        _calculate_crc16(): Calculate CRC16 checksum.
        _exit_read(): Determine if response has been fully read.
        _uart_read(): Read response data from UART (with simple timeout).
        _uart_read_frame(): Read a complete Modbus frame.
        _send(): Send a Modbus frame.
        _send_receive(): Send and receive response.
        _validate_resp_hdr(): Validate response header.
        send_response(): Send response to client.
        send_exception_response(): Send exception response.
        get_request(): Get a request object.

    Notes:
        Inter-frame delay is calculated based on baudrate: ≤19200bps uses 3.5 character times,
        otherwise fixed to 1750us.
        Optional RS485 direction control pin is supported.
    """

    def __init__(
        self,
        uart_id: int = 1,
        baudrate: int = 9600,
        data_bits: int = 8,
        stop_bits: int = 1,
        parity=None,
        pins: List[Union[int, Pin], Union[int, Pin]] = None,
        ctrl_pin: int = None,
    ):
        """
        初始化串口 Modbus 通信实例。

        Args:
            uart_id (int, optional): UART ID，默认1。
            baudrate (int, optional): 波特率，默认9600。
            data_bits (int, optional): 数据位，默认8。
            stop_bits (int, optional): 停止位，默认1。
            parity (Optional[int], optional): 校验位，默认None。
            pins (List[Union[int, Pin], Union[int, Pin]], optional): 引脚列表 [TX, RX]。
            ctrl_pin (int, optional): 方向控制引脚，默认None。

        Notes:
            检查 UART 是否支持 flush 方法。计算 1 字符时间和帧间延迟。

        ==========================================
        Initialize Serial Modbus communication instance.

        Args:
            uart_id (int, optional): UART ID, default 1.
            baudrate (int, optional): Baudrate, default 9600.
            data_bits (int, optional): Data bits, default 8.
            stop_bits (int, optional): Stop bits, default 1.
            parity (Optional[int], optional): Parity, default None.
            pins (List[Union[int, Pin], Union[int, Pin]], optional): Pins list [TX, RX].
            ctrl_pin (int, optional): Direction control pin, default None.

        Notes:
            Checks whether UART supports flush method. Calculates 1-character time and inter-frame delay.
        """
        # UART flush function is introduced in Micropython v1.20.0
        self._has_uart_flush = callable(getattr(UART, "flush", None))
        self._uart = UART(
            uart_id,
            baudrate=baudrate,
            bits=data_bits,
            parity=parity,
            stop=stop_bits,
            # timeout_chars=2,  # WiPy only
            # pins=pins         # WiPy only
            tx=pins[0],
            rx=pins[1],
        )

        if ctrl_pin is not None:
            self._ctrlPin = Pin(ctrl_pin, mode=Pin.OUT)
        else:
            self._ctrlPin = None

        # timing of 1 character in microseconds (us)
        self._t1char = (1000000 * (data_bits + stop_bits + 2)) // baudrate

        # inter-frame delay in microseconds (us)
        # - <= 19200 bps: 3.5x timing of 1 character
        # - > 19200 bps: 1750 us
        if baudrate <= 19200:
            self._inter_frame_delay = (self._t1char * 3500) // 1000
        else:
            self._inter_frame_delay = 1750

    def _calculate_crc16(self, data: bytearray) -> bytes:
        """
        计算 CRC16 校验值（Modbus 标准）。

        Args:
            data (bytearray): 输入数据。

        Returns:
            bytes: 2 字节 CRC 值，小端格式。

        Notes:
            使用预先生成的 CRC16 查找表。

        ==========================================
        Calculate CRC16 checksum (Modbus standard).

        Args:
            data (bytearray): Input data.

        Returns:
            bytes: 2-byte CRC value, little-endian.

        Notes:
            Uses pre-generated CRC16 lookup table.
        """
        crc = 0xFFFF

        for char in data:
            crc = (crc >> 8) ^ Const.CRC16_TABLE[((crc) ^ char) & 0xFF]

        return struct.pack("<H", crc)

    def _exit_read(self, response: bytearray) -> bool:
        """
        判断响应是否已完整读取。

        Args:
            response (bytearray): 已读取的部分响应数据。

        Returns:
            bool: 如果响应已完整则返回 True，否则 False。

        Notes:
            根据功能码和响应长度判断是否需要继续读取。

        ==========================================
        Determine if the response has been fully read.

        Args:
            response (bytearray): Partially read response data.

        Returns:
            bool: True if entire response has been read, otherwise False.

        Notes:
            Decision based on function code and response length.
        """
        response_len = len(response)
        if response_len >= 2 and response[1] >= Const.ERROR_BIAS:
            if response_len < Const.ERROR_RESP_LEN:
                return False
        elif response_len >= 3 and (Const.READ_COILS <= response[1] <= Const.READ_INPUT_REGISTER):
            expected_len = Const.RESPONSE_HDR_LENGTH + 1 + response[2] + Const.CRC_LENGTH
            if response_len < expected_len:
                return False
        elif response_len < Const.FIXED_RESP_LEN:
            return False

        return True

    def _uart_read(self) -> bytearray:
        """
        从 UART 读取从站响应（简单循环读取，固定次数尝试）。

        Returns:
            bytearray: 读取到的响应数据。

        Notes:
            最多尝试 120 次循环，每次循环后等待帧间延迟。
            调用 _exit_read 判断是否完成。

        ==========================================
        Read incoming slave response from UART (simple loop with fixed attempts).

        Returns:
            bytearray: Read response data.

        Notes:
            Tries up to 120 loops, waits inter-frame delay after each loop.
            Uses _exit_read to determine completion.
        """
        response = bytearray()

        # TODO: use some kind of hint or user-configurable delay
        #       to determine this loop counter
        for x in range(1, 120):
            if self._uart.any():
                # WiPy only
                # response.extend(self._uart.readall())
                response.extend(self._uart.read())

                # variable length function codes may require multiple reads
                if self._exit_read(response):
                    break

            # wait for the maximum time between two frames
            time.sleep_us(self._inter_frame_delay)

        return response

    def _uart_read_frame(self, timeout: Optional[int] = None) -> bytearray:
        """
        读取一个完整的 Modbus 帧（基于帧间延迟识别帧结束）。

        Args:
            timeout (Optional[int], optional): 超时时间（微秒），默认使用 2 倍帧间延迟。

        Returns:
            bytearray: 接收到的帧数据（不含 CRC 检查）。

        Notes:
            通过检测帧间延迟判断帧结束。若超时时间内未收到任何数据，返回空字节数组。

        ==========================================
        Read a complete Modbus frame (frame end identified by inter-frame delay).

        Args:
            timeout (Optional[int], optional): Timeout in microseconds, defaults to 2 * inter-frame delay.

        Returns:
            bytearray: Received frame data (without CRC check).

        Notes:
            Frame end is detected by inter-frame delay. Returns empty bytearray if no data within timeout.
        """
        received_bytes = bytearray()

        # set default timeout to at twice the inter-frame delay
        if timeout == 0 or timeout is None:
            timeout = 2 * self._inter_frame_delay  # in microseconds

        start_us = time.ticks_us()

        # stay inside this while loop at least for the timeout time
        while time.ticks_diff(time.ticks_us(), start_us) <= timeout:
            # check amount of available characters
            if self._uart.any():
                # remember this time in microseconds
                last_byte_ts = time.ticks_us()

                # do not stop reading and appending the result to the buffer
                # until the time between two frames elapsed
                while time.ticks_diff(time.ticks_us(), last_byte_ts) <= self._inter_frame_delay:
                    # WiPy only
                    # r = self._uart.readall()
                    r = self._uart.read()

                    # if something has been read after the first iteration of
                    # this inner while loop (within self._inter_frame_delay)
                    if r is not None:
                        # append the new read stuff to the buffer
                        received_bytes.extend(r)

                        # update the timestamp of the last byte being read
                        last_byte_ts = time.ticks_us()

            # if something has been read before the overall timeout is reached
            if len(received_bytes) > 0:
                return received_bytes

        # return the result in case the overall timeout has been reached
        return received_bytes

    def _send(self, modbus_pdu: bytes, slave_addr: int) -> None:
        """
        通过 UART 发送 Modbus 帧（添加地址和 CRC）。

        Args:
            modbus_pdu (bytes): Modbus 协议数据单元。
            slave_addr (int): 从站地址。

        Notes:
            如果配置了流控引脚，会在发送前拉高，发送后拉低。
            根据 UART 是否支持 flush 采用不同的延迟策略。

        ==========================================
        Send Modbus frame via UART (prepend address and append CRC).

        Args:
            modbus_pdu (bytes): Modbus Protocol Data Unit.
            slave_addr (int): Slave address.

        Notes:
            If control pin is configured, it is set high before send and low after.
            Different delay strategies based on UART flush support.
        """
        # modbus_adu: Modbus Application Data Unit
        # consists of the Modbus PDU, with slave address prepended and checksum appended
        modbus_adu = bytearray()
        modbus_adu.append(slave_addr)
        modbus_adu.extend(modbus_pdu)
        modbus_adu.extend(self._calculate_crc16(modbus_adu))

        if self._ctrlPin:
            self._ctrlPin.on()
            # wait until the control pin really changed
            # 85-95us (ESP32 @ 160/240MHz)
            time.sleep_us(200)

        # the timing of this part is critical:
        # - if we disable output too early,
        #   the command will not be received in full
        # - if we disable output too late,
        #   the incoming response will lose some data at the beginning
        # easiest to just wait for the bytes to be sent out on the wire

        send_start_time = time.ticks_us()
        # 360-400us @ 9600-115200 baud (measured) (ESP32 @ 160/240MHz)
        self._uart.write(modbus_adu)
        send_finish_time = time.ticks_us()

        if self._has_uart_flush:
            self._uart.flush()
            time.sleep_us(self._t1char)
        else:
            sleep_time_us = (
                self._t1char * len(modbus_adu)  # total frame time in us
                - time.ticks_diff(send_finish_time, send_start_time)
                + 100  # only required at baudrates above 57600, but hey 100us
            )
            time.sleep_us(sleep_time_us)

        if self._ctrlPin:
            self._ctrlPin.off()

    def _send_receive(self, modbus_pdu: bytes, slave_addr: int, count: bool) -> bytes:
        """
        发送 Modbus 消息并接收响应。

        Args:
            modbus_pdu (bytes): 要发送的 PDU。
            slave_addr (int): 从站地址。
            count (bool): 是否期望响应中包含字节计数字段（用于确定响应头长度）。

        Returns:
            bytes: 验证后的响应数据（不含地址和 CRC）。

        Raises:
            OSError: 无数据接收或 CRC 错误。
            ValueError: 从站地址不匹配或返回异常。

        Notes:
            发送前清空接收 FIFO。调用 _validate_resp_hdr 验证响应。

        ==========================================
        Send a Modbus message and receive the response.

        Args:
            modbus_pdu (bytes): PDU to send.
            slave_addr (int): Slave address.
            count (bool): Whether the response is expected to contain a byte count field (used to determine response header length).

        Returns:
            bytes: Validated response data (excluding address and CRC).

        Raises:
            OSError: No data received or CRC error.
            ValueError: Slave address mismatch or exception returned.

        Notes:
            Flushes Rx FIFO before sending. Calls _validate_resp_hdr to validate response.
        """
        # flush the Rx FIFO buffer
        self._uart.read()

        self._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)

        return self._validate_resp_hdr(response=self._uart_read(), slave_addr=slave_addr, function_code=modbus_pdu[0], count=count)

    def _validate_resp_hdr(self, response: bytearray, slave_addr: int, function_code: int, count: bool) -> bytes:
        """
        验证响应头部：地址匹配、CRC 正确、非异常响应。

        Args:
            response (bytearray): 原始响应数据（含地址、PDU、CRC）。
            slave_addr (int): 期望的从站地址。
            function_code (int): 原始功能码。
            count (bool): 响应是否包含字节计数字段。

        Returns:
            bytes: 响应数据部分（PDU 内容，不含地址和 CRC）。

        Raises:
            OSError: 无数据或 CRC 无效。
            ValueError: 地址不匹配或从站返回异常。

        ==========================================
        Validate response header: address match, correct CRC, not an exception response.

        Args:
            response (bytearray): Raw response data (including address, PDU, CRC).
            slave_addr (int): Expected slave address.
            function_code (int): Original function code.
            count (bool): Whether response contains a byte count field.

        Returns:
            bytes: Response data part (PDU content, excluding address and CRC).

        Raises:
            OSError: No data or invalid CRC.
            ValueError: Address mismatch or slave returned exception.
        """
        if len(response) == 0:
            raise OSError("no data received from slave")

        resp_crc = response[-Const.CRC_LENGTH :]
        expected_crc = self._calculate_crc16(response[0 : len(response) - Const.CRC_LENGTH])

        if (resp_crc[0] is not expected_crc[0]) or (resp_crc[1] is not expected_crc[1]):
            raise OSError("invalid response CRC")

        if response[0] != slave_addr:
            raise ValueError("wrong slave address")

        if response[1] == (function_code + Const.ERROR_BIAS):
            raise ValueError("slave returned exception code: {:d}".format(response[2]))

        hdr_length = (Const.RESPONSE_HDR_LENGTH + 1) if count else Const.RESPONSE_HDR_LENGTH

        return response[hdr_length : len(response) - Const.CRC_LENGTH]

    def send_response(
        self,
        slave_addr: int,
        function_code: int,
        request_register_addr: int,
        request_register_qty: int,
        request_data: list,
        values: Optional[list] = None,
        signed: bool = True,
    ) -> None:
        """
        发送响应给客户端。

        Args:
            slave_addr (int): 从站地址。
            function_code (int): 功能码。
            request_register_addr (int): 请求的寄存器起始地址。
            request_register_qty (int): 请求的寄存器数量。
            request_data (list): 请求中的原始数据。
            values (Optional[list], optional): 要返回的数据值列表（用于读响应）。默认为None。
            signed (bool, optional): 是否使用有符号格式。默认为True。

        Notes:
            使用 functions.response 构造 PDU，然后调用 _send。

        ==========================================
        Send a response to a client.

        Args:
            slave_addr (int): Slave address.
            function_code (int): Function code.
            request_register_addr (int): Requested starting register address.
            request_register_qty (int): Requested register quantity.
            request_data (list): Raw data from request.
            values (Optional[list], optional): Data values to return (for read response). Defaults to None.
            signed (bool, optional): Whether to use signed format. Defaults to True.

        Notes:
            Uses functions.response to build PDU, then calls _send.
        """
        modbus_pdu = functions.response(
            function_code=function_code,
            request_register_addr=request_register_addr,
            request_register_qty=request_register_qty,
            request_data=request_data,
            value_list=values,
            signed=signed,
        )
        self._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)

    def send_exception_response(self, slave_addr: int, function_code: int, exception_code: int) -> None:
        """
        发送异常响应给客户端。

        Args:
            slave_addr (int): 从站地址。
            function_code (int): 原始功能码。
            exception_code (int): 异常码。

        Notes:
            使用 functions.exception_response 构造 PDU。

        ==========================================
        Send an exception response to a client.

        Args:
            slave_addr (int): Slave address.
            function_code (int): Original function code.
            exception_code (int): Exception code.

        Notes:
            Uses functions.exception_response to build PDU.
        """
        modbus_pdu = functions.exception_response(function_code=function_code, exception_code=exception_code)
        self._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)

    def get_request(self, unit_addr_list: List[int], timeout: Optional[int] = None) -> Union[Request, None]:
        """
        在指定超时内检查是否有请求。

        Args:
            unit_addr_list (List[int]): 本设备支持的单元地址列表。
            timeout (Optional[int], optional): 超时时间（微秒）。默认为None。

        Returns:
            Union[Request, None]: 请求对象，如果没有有效请求则返回 None。

        Notes:
            读取一帧，验证地址、CRC，然后构造 Request 对象。如果发生 ModbusException，
            自动发送异常响应并返回 None。

        ==========================================
        Check for request within the specified timeout.

        Args:
            unit_addr_list (List[int]): List of unit addresses supported by this device.
            timeout (Optional[int], optional): Timeout in microseconds. Defaults to None.

        Returns:
            Union[Request, None]: A request object, or None if no valid request.

        Notes:
            Reads a frame, validates address and CRC, then constructs a Request object.
            If ModbusException occurs, automatically sends exception response and returns None.
        """
        req = self._uart_read_frame(timeout=timeout)

        if len(req) < 8:
            return None

        if req[0] not in unit_addr_list:
            return None

        req_crc = req[-Const.CRC_LENGTH :]
        req_no_crc = req[: -Const.CRC_LENGTH]
        expected_crc = self._calculate_crc16(req_no_crc)

        if (req_crc[0] != expected_crc[0]) or (req_crc[1] != expected_crc[1]):
            return None

        try:
            request = Request(interface=self, data=req_no_crc)
        except ModbusException as e:
            self.send_exception_response(slave_addr=req[0], function_code=e.function_code, exception_code=e.exception_code)
            return None

        return request


# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================
