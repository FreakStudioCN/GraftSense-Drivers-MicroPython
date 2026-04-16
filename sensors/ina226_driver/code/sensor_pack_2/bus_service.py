# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/15 14:30
# @Author  : Roman Shevchik
# @File    : bus_service.py
# @Description : MicroPython module for I/O bus operations (I2C/SPI)
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import math
from machine import I2C, SPI, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
def mpy_bl(value: int) -> int:
    """
    Returns the bit length of the integer value.
    Analog of int.bit_length() which is absent in MicroPython.

    Args:
        value (int): The integer value.

    Returns:
        int: Number of bits required to represent the value; 0 if value is 0.

    Notes:
        Uses logarithm to compute bit length.

    ==========================================
    English description
    Args:
        value (int): The integer value.

    Returns:
        int: Number of bits required to represent the value; 0 if value is 0.

    Notes:
        Uses logarithm to compute bit length.
    """
    if 0 == value:
        return 0
    return 1 + int(math.log2(abs(value)))

# ======================================== 自定义类 ============================================
class BusAdapter:
    """
    Adapter between an I/O bus and a device class.

    Attributes:
        bus (I2C | SPI): The bus instance (I2C or SPI).

    Methods:
        get_bus_type(): Returns the type of the bus.
        read_register(): Read from a device register.
        write_register(): Write to a device register.
        read(): Read raw bytes from device.
        read_to_buf(): Read into a buffer.
        write(): Write raw bytes to device.
        write_const(): Write a constant byte value repeatedly.
        read_buf_from_memory(): Read from device memory into buffer.
        write_buf_to_memory(): Write buffer to device memory.

    Notes:
        This is an abstract base class; subclasses must implement the abstract methods.

    ==========================================
    English description
    Attributes:
        bus (I2C | SPI): The bus instance (I2C or SPI).

    Methods:
        get_bus_type(): Returns the type of the bus.
        read_register(): Read from a device register.
        write_register(): Write to a device register.
        read(): Read raw bytes from device.
        read_to_buf(): Read into a buffer.
        write(): Write raw bytes to device.
        write_const(): Write a constant byte value repeatedly.
        read_buf_from_memory(): Read from device memory into buffer.
        write_buf_to_memory(): Write buffer to device memory.

    Notes:
        This is an abstract base class; subclasses must implement the abstract methods.
    """
    def __init__(self, bus: [I2C, SPI]) -> None:
        """
        Initialize the BusAdapter.

        Args:
            bus (I2C | SPI): The bus instance.

        ==========================================
        English description
        Args:
            bus (I2C | SPI): The bus instance.
        """
        self.bus = bus

    def get_bus_type(self) -> type:
        """
        Return the type of the bus.

        Returns:
            type: The class of the bus (I2C or SPI).

        ==========================================
        English description
        Returns:
            type: The class of the bus (I2C or SPI).
        """
        return type(self.bus)

    def read_register(self, device_addr: [int, Pin], reg_addr: int, bytes_count: int) -> bytes:
        """
        Read a value from a device register.

        Args:
            device_addr (int | Pin): Device address on the bus (for SPI, this is a Pin object).
            reg_addr (int): Register address.
            bytes_count (int): Number of bytes to read.

        Returns:
            bytes: The read data.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address on the bus (for SPI, this is a Pin object).
            reg_addr (int): Register address.
            bytes_count (int): Number of bytes to read.

        Returns:
            bytes: The read data.

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def write_register(self, device_addr: [int, Pin], reg_addr: int, value: [int, bytes, bytearray],
                       bytes_count: int, byte_order: str) -> None:
        """
        Write data to a device register.

        Args:
            device_addr (int | Pin): Device address on the bus.
            reg_addr (int): Register address.
            value (int | bytes | bytearray): Data to write.
            bytes_count (int): Number of bytes to write from value.
            byte_order (str): Byte order ('little' or 'big').

        Raises:
            NotImplementedError: Must be implemented by subclass.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address on the bus.
            reg_addr (int): Register address.
            value (int | bytes | bytearray): Data to write.
            bytes_count (int): Number of bytes to write from value.
            byte_order (str): Byte order ('little' or 'big').

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def read(self, device_addr: [int, Pin], n_bytes: int) -> bytes:
        """
        Read raw bytes from the device.

        Args:
            device_addr (int | Pin): Device address.
            n_bytes (int): Number of bytes to read.

        Returns:
            bytes: The read data.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address.
            n_bytes (int): Number of bytes to read.

        Returns:
            bytes: The read data.

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def read_to_buf(self, device_addr: [int, Pin], buf: bytearray) -> bytes:
        """
        Read into a buffer.

        Args:
            device_addr (int | Pin): Device address.
            buf (bytearray): Buffer to fill.

        Returns:
            bytes: Reference to the buffer.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address.
            buf (bytearray): Buffer to fill.

        Returns:
            bytes: Reference to the buffer.

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def write(self, device_addr: [int, Pin], buf: bytes) -> None:
        """
        Write raw bytes to the device.

        Args:
            device_addr (int | Pin): Device address.
            buf (bytes): Data to write.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address.
            buf (bytes): Data to write.

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def write_const(self, device_addr: [int, Pin], val: int, count: int) -> None:
        """
        Write a constant byte value repeatedly.

        Args:
            device_addr (int | Pin): Device address.
            val (int): Value to write (must fit in 8 bits).
            count (int): Number of times to write the value.

        Raises:
            ValueError: If val requires more than 8 bits.

        Notes:
            Not recommended for slow buses.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address.
            val (int): Value to write (must fit in 8 bits).
            count (int): Number of times to write the value.

        Raises:
            ValueError: If val requires more than 8 bits.

        Notes:
            Not recommended for slow buses.
        """
        if 0 == count:
            return
        # bit_length() is absent in MicroPython
        bl = mpy_bl(val)
        if bl > 8:
            raise ValueError(f"The value must take no more than 8 bits! Current: {bl}")
        _max = 16
        if count < _max:
            _max = count
        # Calculate number of loop repetitions
        repeats = count // _max
        b = bytearray([val for _ in range(_max)])
        for _ in range(repeats):
            self.write(device_addr, b)
        # Calculate remainder
        remainder = count - _max * repeats
        if remainder:
            b = bytearray([val for _ in range(remainder)])
            self.write(device_addr, b)

    def read_buf_from_memory(self, device_addr: [int, Pin], mem_addr, buf, address_size: int) -> None:
        """
        Read from device memory into a buffer.

        Args:
            device_addr (int | Pin): Device address.
            mem_addr: Memory address in the device.
            buf: Buffer to fill.
            address_size (int): Size of the address in bytes.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address.
            mem_addr: Memory address in the device.
            buf: Buffer to fill.
            address_size (int): Size of the address in bytes.

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError

    def write_buf_to_memory(self, device_addr: [int, Pin], mem_addr, buf) -> None:
        """
        Write buffer to device memory.

        Args:
            device_addr (int | Pin): Device address.
            mem_addr: Memory address in the device.
            buf: Data to write.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        ==========================================
        English description
        Args:
            device_addr (int | Pin): Device address.
            mem_addr: Memory address in the device.
            buf: Data to write.

        Raises:
            NotImplementedError: Must be implemented by subclass.
        """
        raise NotImplementedError


class I2cAdapter(BusAdapter):
    """
    I2C bus adapter.

    Attributes:
        bus (I2C): The I2C bus instance.

    Methods:
        write_register(): Write to a register over I2C.
        read_register(): Read from a register over I2C.
        read(): Read raw bytes from I2C device.
        read_to_buf(): Read into buffer.
        write(): Write raw bytes.
        read_buf_from_memory(): Read from memory into buffer.
        write_buf_to_memory(): Write buffer to memory.

    ==========================================
    English description
    Attributes:
        bus (I2C): The I2C bus instance.

    Methods:
        write_register(): Write to a register over I2C.
        read_register(): Read from a register over I2C.
        read(): Read raw bytes from I2C device.
        read_to_buf(): Read into buffer.
        write(): Write raw bytes.
        read_buf_from_memory(): Read from memory into buffer.
        write_buf_to_memory(): Write buffer to memory.
    """
    def __init__(self, bus: I2C) -> None:
        """
        Initialize I2C adapter.

        Args:
            bus (I2C): I2C bus instance.

        ==========================================
        English description
        Args:
            bus (I2C): I2C bus instance.
        """
        super().__init__(bus)

    def write_register(self, device_addr: int, reg_addr: int, value: [int, bytes, bytearray],
                       bytes_count: int, byte_order: str) -> None:
        """
        Write data to an I2C device register.

        Args:
            device_addr (int): I2C device address.
            reg_addr (int): Register address.
            value (int | bytes | bytearray): Data to write.
            bytes_count (int): Number of bytes to write.
            byte_order (str): Byte order for integer conversion.

        ==========================================
        English description
        Args:
            device_addr (int): I2C device address.
            reg_addr (int): Register address.
            value (int | bytes | bytearray): Data to write.
            bytes_count (int): Number of bytes to write.
            byte_order (str): Byte order for integer conversion.
        """
        buf = None
        if isinstance(value, int):
            buf = value.to_bytes(bytes_count, byte_order)
        if isinstance(value, (bytes, bytearray)):
            buf = value

        return self.bus.writeto_mem(device_addr, reg_addr, buf)

    def read_register(self, device_addr: int, reg_addr: int, bytes_count: int) -> bytes:
        """
        Read from an I2C device register.

        Args:
            device_addr (int): I2C device address.
            reg_addr (int): Register address.
            bytes_count (int): Number of bytes to read.

        Returns:
            bytes: The read data.

        ==========================================
        English description
        Args:
            device_addr (int): I2C device address.
            reg_addr (int): Register address.
            bytes_count (int): Number of bytes to read.

        Returns:
            bytes: The read data.
        """
        return self.bus.readfrom_mem(device_addr, reg_addr, bytes_count)

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        """
        Read raw bytes from I2C device.

        Args:
            device_addr (int): I2C device address.
            n_bytes (int): Number of bytes to read.

        Returns:
            bytes: The read data.

        ==========================================
        English description
        Args:
            device_addr (int): I2C device address.
            n_bytes (int): Number of bytes to read.

        Returns:
            bytes: The read data.
        """
        return self.bus.readfrom(device_addr, n_bytes)

    def read_to_buf(self, device_addr: int, buf: bytearray) -> bytes:
        """
        Read into buffer from I2C device.

        Args:
            device_addr (int): I2C device address.
            buf (bytearray): Buffer to fill.

        Returns:
            bytes: Reference to the buffer.

        ==========================================
        English description
        Args:
            device_addr (int): I2C device address.
            buf (bytearray): Buffer to fill.

        Returns:
            bytes: Reference to the buffer.
        """
        self.bus.readfrom_into(device_addr, buf)
        return buf

    def write(self, device_addr: int, buf: bytes) -> None:
        """
        Write raw bytes to I2C device.

        Args:
            device_addr (int): I2C device address.
            buf (bytes): Data to write.

        ==========================================
        English description
        Args:
            device_addr (int): I2C device address.
            buf (bytes): Data to write.
        """
        return self.bus.writeto(device_addr, buf)

    def read_buf_from_memory(self, device_addr: int, mem_addr, buf, address_size: int = 1) -> None:
        """
        Read from I2C device memory into buffer.

        Args:
            device_addr (int): I2C device address.
            mem_addr: Memory address.
            buf: Buffer to fill.
            address_size (int): Address size in bytes (ignored on ESP8266).

        Notes:
            Extension of base class.

        ==========================================
        English description
        Args:
            device_addr (int): I2C device address.
            mem_addr: Memory address.
            buf: Buffer to fill.
            address_size (int): Address size in bytes (ignored on ESP8266).

        Notes:
            Extension of base class.
        """
        self.bus.readfrom_mem_into(device_addr, mem_addr, buf)
        return buf

    def write_buf_to_memory(self, device_addr: int, mem_addr, buf) -> None:
        """
        Write buffer to I2C device memory.

        Args:
            device_addr (int): I2C device address.
            mem_addr: Memory address.
            buf: Data to write.

        ==========================================
        English description
        Args:
            device_addr (int): I2C device address.
            mem_addr: Memory address.
            buf: Data to write.
        """
        return self.bus.writeto_mem(device_addr, mem_addr, buf)


class SpiAdapter(BusAdapter):
    """
    SPI bus adapter.

    Attributes:
        bus (SPI): The SPI bus instance.
        data_mode_pin (Pin | None): Pin to indicate data (high) or command (low).
        use_data_mode_pin (bool): Whether to use data_mode_pin.
        data_packet (bool): Flag for write methods: True for data, False for command.
        _address_index (int): Index of the register address byte in the buffer.
        _prepare_before_send_ref (callable | None): Function to prepare buffer before sending.

    Methods:
        prepare_func: Property to get/set the preparation function.
        read(): Read bytes from SPI device.
        read_to_buf(): Read into buffer.
        write(): Write bytes.
        write_and_read(): Write and read simultaneously.
        read_buf_from_memory(): Read from memory (not implemented).
        write_buf_to_memory(): Write to memory (not implemented).

    ==========================================
    English description
    Attributes:
        bus (SPI): The SPI bus instance.
        data_mode_pin (Pin | None): Pin to indicate data (high) or command (low).
        use_data_mode_pin (bool): Whether to use data_mode_pin.
        data_packet (bool): Flag for write methods: True for data, False for command.
        _address_index (int): Index of the register address byte in the buffer.
        _prepare_before_send_ref (callable | None): Function to prepare buffer before sending.

    Methods:
        prepare_func: Property to get/set the preparation function.
        read(): Read bytes from SPI device.
        read_to_buf(): Read into buffer.
        write(): Write bytes.
        write_and_read(): Write and read simultaneously.
        read_buf_from_memory(): Read from memory (not implemented).
        write_buf_to_memory(): Write to memory (not implemented).
    """
    def __init__(self, bus: SPI, data_mode: Pin = None) -> None:
        """
        Initialize SPI adapter.

        Args:
            bus (SPI): SPI bus instance.
            data_mode (Pin | None): Pin to indicate data (high) or command (low). Used e.g. with ILI9481.

        ==========================================
        English description
        Args:
            bus (SPI): SPI bus instance.
            data_mode (Pin | None): Pin to indicate data (high) or command (low). Used e.g. with ILI9481.
        """
        super().__init__(bus)
        # MCU pin for data mode
        self.data_mode_pin = data_mode
        # Whether to use the data mode pin
        self.use_data_mode_pin = False
        # Flag for write methods: if True, data_mode pin will be set to True, otherwise False
        self.data_packet = False
        # Index of the register address byte in the buffer sent to the device
        self._address_index = 0
        # Reference to a function that prepares the buffer before sending
        # Signature: prepare(buf: bytearray, address_index: int) -> bytes: ...
        self._prepare_before_send_ref = None

    @property
    def prepare_func(self):
        """
        Get the buffer preparation function.

        Returns:
            callable | None: The preparation function or None.

        ==========================================
        English description
        Returns:
            callable | None: The preparation function or None.
        """
        return self._prepare_before_send_ref

    @prepare_func.setter
    def prepare_func(self, value) -> None:
        """
        Set the buffer preparation function.

        Args:
            value (callable | None): The preparation function.

        ==========================================
        English description
        Args:
            value (callable | None): The preparation function.
        """
        self._prepare_before_send_ref = value

    def _call_prepare(self, buf: bytearray) -> None:
        """
        Call the preparation function if set.

        Args:
            buf (bytearray): Buffer to prepare.

        ==========================================
        English description
        Args:
            buf (bytearray): Buffer to prepare.
        """
        ref = self._prepare_before_send_ref
        if ref is not None:
            ref(buf, self._address_index)

    def read(self, device_addr: Pin, n_bytes: int) -> bytes:
        """
        Read a number of bytes from SPI device while continuously writing 0x00.

        Args:
            device_addr (Pin): Chip select pin.
            n_bytes (int): Number of bytes to read.

        Returns:
            bytes: The read data.

        ==========================================
        English description
        Args:
            device_addr (Pin): Chip select pin.
            n_bytes (int): Number of bytes to read.

        Returns:
            bytes: The read data.
        """
        try:
            device_addr.low()
            return self.bus.read(n_bytes)
        finally:
            device_addr.high()

    def read_to_buf(self, device_addr: Pin, buf) -> bytes:
        """
        Read into buffer from SPI device.

        Args:
            device_addr (Pin): Chip select pin.
            buf (bytearray): Buffer to fill.

        Returns:
            bytes: Reference to the buffer.

        ==========================================
        English description
        Args:
            device_addr (Pin): Chip select pin.
            buf (bytearray): Buffer to fill.

        Returns:
            bytes: Reference to the buffer.
        """
        try:
            device_addr.low()
            self.bus.readinto(buf, 0x00)
            return buf
        finally:
            device_addr.high()

    def write(self, device_addr: Pin, buf: bytes) -> None:
        """
        Write bytes to SPI device.

        Args:
            device_addr (Pin): Chip select pin.
            buf (bytes): Data to write.

        Notes:
            If use_data_mode_pin is True, sets data_mode_pin to data_packet value.

        ==========================================
        English description
        Args:
            device_addr (Pin): Chip select pin.
            buf (bytes): Data to write.

        Notes:
            If use_data_mode_pin is True, sets data_mode_pin to data_packet value.
        """
        try:
            device_addr.low()
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write(buf)
        finally:
            device_addr.high()

    def write_and_read(self, device_addr: Pin, wr_buf: bytes, rd_buf: bytes) -> None:
        """
        Write and read simultaneously over SPI.

        Args:
            device_addr (Pin): Chip select pin.
            wr_buf (bytes): Buffer to write.
            rd_buf (bytes): Buffer to read into (must be same length as wr_buf).

        Notes:
            Extension of base class.

        ==========================================
        English description
        Args:
            device_addr (Pin): Chip select pin.
            wr_buf (bytes): Buffer to write.
            rd_buf (bytes): Buffer to read into (must be same length as wr_buf).

        Notes:
            Extension of base class.
        """
        try:
            device_addr.low()
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write_readinto(wr_buf, rd_buf)
        finally:
            device_addr.high()

    def read_buf_from_memory(self, device_addr: Pin, mem_addr, buf, address_size: int) -> None:
        """
        Read from device memory into buffer (not implemented for SPI).

        Args:
            device_addr (Pin): Chip select pin.
            mem_addr: Memory address.
            buf: Buffer to fill.
            address_size (int): Address size in bytes.

        Raises:
            NotImplementedError: Always.

        ==========================================
        English description
        Args:
            device_addr (Pin): Chip select pin.
            mem_addr: Memory address.
            buf: Buffer to fill.
            address_size (int): Address size in bytes.

        Raises:
            NotImplementedError: Always.
        """
        try:
            device_addr.low()
            raise NotImplementedError
        finally:
            device_addr.high()

    def write_buf_to_memory(self, device_addr: Pin, mem_addr, buf) -> None:
        """
        Write buffer to device memory (not implemented for SPI).

        Args:
            device_addr (Pin): Chip select pin.
            mem_addr: Memory address.
            buf: Data to write.

        Raises:
            NotImplementedError: Always.

        ==========================================
        English description
        Args:
            device_addr (Pin): Chip select pin.
            mem_addr: Memory address.
            buf: Data to write.

        Raises:
            NotImplementedError: Always.
        """
        try:
            device_addr.low()
            self._call_prepare(buf)
            raise NotImplementedError
        finally:
            device_addr.high()

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================