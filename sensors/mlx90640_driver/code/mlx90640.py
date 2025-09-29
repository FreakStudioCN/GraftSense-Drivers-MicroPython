# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午11:14
# @Author  : 缪贵成
# @File    : mlx90640.py
# @Description : mlx90640点阵红外温度传感器模块驱动测试文件
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import array
import math
import struct
import machine
from machine import I2C, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def init_float_array(size: int) -> array.array:
    """
    初始化一个指定大小的浮点型数组。

    Args:
        size (int): 数组的大小。

    Returns:
        array.array: 初始化后的浮点型数组，元素初始值均为0。

    Raises:
        ValueError: 如果size不是正整数或者size不是负数。

    Notes:
        使用'f'类型码表示单精度浮点数。

    ==========================================

    Initialize a float array with specified size.

    Args:
        size (int): The size of the array.

    Returns:
        array.array: Initialized float array with all elements 0.

    Raises:
        ValueError: If size is not a positive integer or size is not a negative number.

    Notes:
        Uses 'f' type code for single-precision floating points.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("Size must be a positive integer.")
    return array.array('f', (0 for _ in range(size)))

def init_int_array(size: int) -> array.array:
    """
    初始化一个指定大小的整型数组。

    Args:
        size (int): 数组的大小。

    Returns:
        array.array: 初始化后的整型数组，元素初始值均为0。

    Raises:
        ValueError:  如果size不是正整数。

    Notes:
        使用'i'类型码表示整型。

    ==========================================

    Initialize an integer array with specified size.

    Args:
        size (int): The size of the array.

    Returns:
        array.array: Initialized integer array with all elements 0.

    Raises:
        ValueError: If size is not a positive integer.

    Notes:
        Uses 'i' type code for integers.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("Size must be a positive integer.")
    return array.array('i', (0 for _ in range(size)))

# ======================================== 自定义类 ============================================

class RefreshRate:
    """
    该类为MLX90640红外热像仪的刷新率提供枚举类型支持。

    Attributes:
        REFRESH_0_5_HZ (int): 0.5Hz刷新率，二进制值0b000。
        REFRESH_1_HZ (int): 1Hz刷新率，二进制值0b001。
        REFRESH_2_HZ (int): 2Hz刷新率，二进制值0b010。
        REFRESH_4_HZ (int): 4Hz刷新率，二进制值0b011。
        REFRESH_8_HZ (int): 8Hz刷新率，二进制值0b100。
        REFRESH_16_HZ (int): 16Hz刷新率，二进制值0b101。
        REFRESH_32_HZ (int): 32Hz刷新率，二进制值0b110。
        REFRESH_64_HZ (int): 64Hz刷新率，二进制值0b111。

    Notes:
        这些值对应MLX90640控制寄存器中的刷新率位字段。

    ==========================================

    Enum-like class for MLX90640's refresh rate options.

    Attributes:
        REFRESH_0_5_HZ (int): 0.5Hz refresh rate, binary value 0b000.
        REFRESH_1_HZ (int): 1Hz refresh rate, binary value 0b001.
        REFRESH_2_HZ (int): 2Hz refresh rate, binary value 0b010.
        REFRESH_4_HZ (int): 4Hz refresh rate, binary value 0b011.
        REFRESH_8_HZ (int): 8Hz refresh rate, binary value 0b100.
        REFRESH_16_HZ (int): 16Hz refresh rate, binary value 0b101.
        REFRESH_32_HZ (int): 32Hz refresh rate, binary value 0b110.
        REFRESH_64_HZ (int): 64Hz refresh rate, binary value 0b111.

    Notes:
        These values correspond to the refresh rate bit field in MLX90640's control register.
    """
    # 0.5Hz
    REFRESH_0_5_HZ = 0b000
    # 1Hz
    REFRESH_1_HZ = 0b001
    # 2Hz
    REFRESH_2_HZ = 0b010
    # 4Hz
    REFRESH_4_HZ = 0b011
    # 8Hz
    REFRESH_8_HZ = 0b100
    # 16Hz
    REFRESH_16_HZ = 0b101
    # 32Hz
    REFRESH_32_HZ = 0b110
    # 64Hz
    REFRESH_64_HZ = 0b111


class I2CDevice:
    """
    该类封装了machine.I2C设备，提供基础的读写和探测功能。

    Attributes:
        i2c (machine.I2C): machine.I2C实例，用于总线通信。
        device_address (int): I2C设备地址。
        _probe_for_device (bool): 是否在初始化时探测设备。

    Methods:
        read_into(buf: bytearray, *, start: int=0, end: int=None) -> None: 从设备读取数据到缓冲区。
        write(buf: bytes) -> None: 向设备写入数据。
        write_then_read_into(out_buffer: bytes, in_buffer: bytearray, *, out_start: int=0, out_end: int=None, in_start: int=0, in_end: int=None) -> None: 先写数据再读响应。
        __enter__() -> I2CDevice: 支持with上下文语法。
        __exit__(*exc) -> None: 上下文退出时关闭资源。

    Notes:
        - 该类是一个轻量级封装，并未复制I2C的所有方法。
        - 所有方法涉及I2C通信，均为非ISR安全。
        - 推荐使用with语句进行自动资源管理。

    ==========================================

    Wrapper for machine.I2C device. Provides read/write/probing utilities.

    Attributes:
        i2c (machine.I2C): machine.I2C instance for bus communication.
        device_address (int): I2C address of the device.
        _probe_for_device (bool): Whether to probe device during initialization.

    Methods:
        read_into(buf: bytearray, *, start: int=0, end: int=None) -> None: Read bytes into buffer.
        write(buf: bytes) -> None: Write bytes to device.
        write_then_read_into(out_buffer: bytes, in_buffer: bytearray, *, out_start: int=0, out_end: int=None, in_start: int=0, in_end: int=None) -> None: Write then read response.
        __enter__() -> I2CDevice: Enter context manager.
        __exit__(*exc) -> None: Exit context manager.

    Notes:
        - This is a minimal wrapper, not a full I2C API replacement.
        - All methods that perform I2C communication are not ISR-safe.
        - Prefer using "with" context for automatic resource handling.
    """

    def __init__(self, i2c: machine.I2C, device_address: int, probe: bool = True):
        """
        初始化I2CDevice实例。

        Args:
            i2c (machine.I2C): 已初始化的machine.I2C对象。
            device_address (int): 目标设备的I2C地址。
            probe (bool): 是否在初始化时探测设备，默认True。

        Raises:
            ValueError: 当探测失败时抛出。
            TypeError: 当i2c不是machine.I2C实例时抛出。
            TypeError: 如果device_address不是整数时抛出。
            ValueError: 如果device_address不在0x03 ~ 0x77范围内时抛出。
        Notes:
            - 如果probe=True，则会立即尝试访问设备确认是否存在。
            - 该方法会进行I2C读写，因此非ISR-safe。

        ==========================================

        Initialize I2CDevice instance.

        Args:
            i2c (machine.I2C): Initialized machine.I2C object.
            device_address (int): I2C address of target device.
            probe (bool): Whether to probe device on init (default True).

        Raises:
            ValueError: If device probe fails.
            ValueError: device_address must be an integer.
            TypeError: If i2c is not an instance of machine.I2C.
            TypeError: device_address must be in range 0x03 ~ 0x77.
        Notes:
            - If probe=True, device existence will be checked immediately.
            - Not ISR-safe (performs I2C operations).
        """
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an instance of machine.I2C")

        if not isinstance(device_address, int):
            raise TypeError("device_address must be an integer")

        if not (0x03 <= device_address <= 0x77):
            raise ValueError("device_address must be in range 0x03 ~ 0x77")

        if not isinstance(probe, bool):
            raise TypeError("probe must be a boolean value")
        self.i2c = i2c
        self.device_address = device_address

        if probe:
            self._probe_for_device()

    def read_into(self, buf: bytearray, *, start: int = 0, end: int = None) -> None:
        """
        从设备读取数据到缓冲区。

        Args:
            buf (bytearray): 存放数据的缓冲区。
            start (int): 缓冲区中开始存放数据的起始索引，默认0。
            end (int): 缓冲区中存放数据的结束索引，默认None（写到结尾）。

        Raises:
            TypeError: 当 buf 不是 bytearray 时。
            ValueError: 当 start/end 超出范围时。
            
        Notes:
            - buf长度必须等于需要读取的字节数。
            - 非ISR-safe。

        ==========================================

        Read data into buffer.

        Args:
            buf (bytearray): Buffer to store data.
            start (int): Start index in buffer for storing data (default 0).
            end (int): End index in buffer for storing data (default None).

        Raises:
            TypeError: If buf is not a bytearray.
            ValueError: If start/end are out of range.
            
        Notes:
            - Buffer length must match expected read size.
            - Not ISR-safe.
        """
        if not isinstance(buf, bytearray):
            raise TypeError("buf must be a bytearray")
        if end is None:
            end = len(buf)
        if not (0 <= start < end <= len(buf)):
            raise ValueError(f"Invalid start/end range: start={start}, end={end}, len={len(buf)}")

        self.i2c.readfrom_into(self.device_address, buf, start=start, end=end)

    def write(self, buf: bytes) -> None:
        """
        向I2C设备写入数据。

        Args:
            buf (bytes): 要写入的数据缓冲区。

        Raises:
            TypeError: 当 buf 不是 bytes时。
            
        Notes:
            - buf必须是bytes或bytearray类型。
            - 此方法直接调用machine.I2C.writeto。
            - 非ISR-safe。

        ==========================================

        Write data buffer to the I2C device.

        Args:
            buf (bytes): Data buffer to write.

        Raises:
            TypeError: If buf is not bytes.
            
        Notes:
            - buf must be of type bytes or bytearray.
            - Uses machine.I2C.writeto internally.
            - Not ISR-safe.
        """
        if not isinstance(buf, bytes):
            raise TypeError(f"buf must be bytes, got {type(buf).__name__}")
        self.i2c.writeto(self.device_address, buf)

    def write_then_read_into(self, out_buffer: bytes, in_buffer: bytearray, *, out_start: int = 0, out_end: int = None,
                             in_start: int = 0, in_end: int = None) -> None:
        """
        先向设备写入数据（通常是寄存器地址），再读取响应数据到缓冲区。

        Args:
            out_buffer (bytes): 要写入的数据（通常为寄存器地址）。
            in_buffer (bytearray): 用于存放读取数据的缓冲区。
            out_start (int): 写入数据的起始索引，默认0。
            out_end (int): 写入数据的结束索引，默认None（写到结尾）。
            in_start (int): 读取数据存放的起始索引，默认0。
            in_end (int): 读取数据存放的结束索引，默认None（读到结尾）。

        Raises:
            TypeError: out_buffer 不是 bytes 或 in_buffer 不是 bytearray。
            ValueError: out_start/out_end 或 in_start/in_end 超出缓冲区长度范围。
            
        Notes:
            - 常用于寄存器访问：先写寄存器地址再读寄存器内容。
            - 内部使用memoryview避免额外内存分配。
            - 非ISR-safe。

        ==========================================

        Write to the device, then read data into a buffer.

        Args:
            out_buffer (bytes): Data to write (usually register address).
            in_buffer (bytearray): Buffer to store read data.
            out_start (int): Start index in out_buffer (default 0).
            out_end (int): End index in out_buffer (default None).
            in_start (int): Start index in in_buffer (default 0).
            in_end (int): End index in in_buffer (default None).

        Raises:
            TypeError: If out_buffer is not bytes or in_buffer is not bytearray.
            ValueError: If out_start/out_end or in_start/in_end are out of buffer range.

        Notes:
            - Commonly used for register access: write address then read value.
            - Uses memoryview to avoid extra allocations.
            - Not ISR-safe.
        """
        # 类型检查
        if not isinstance(out_buffer, bytes):
            raise TypeError(f"out_buffer must be bytes, got {type(out_buffer).__name__}")
        if not isinstance(in_buffer, bytearray):
            raise TypeError(f"in_buffer must be bytearray, got {type(in_buffer).__name__}")

        # 默认索引
        if out_end is None:
            out_end = len(out_buffer)
        if in_end is None:
            in_end = len(in_buffer)

        # 索引范围检查
        if not (0 <= out_start <= out_end <= len(out_buffer)):
            raise ValueError(f"Invalid out_buffer range: start={out_start}, end={out_end}, len={len(out_buffer)}")
        if not (0 <= in_start <= in_end <= len(in_buffer)):
            raise ValueError(f"Invalid in_buffer range: start={in_start}, end={in_end}, len={len(in_buffer)}")
            
        self.i2c.writeto(self.device_address, memoryview(out_buffer)[out_start:out_end], False)
        self.i2c.readfrom_into(self.device_address, memoryview(in_buffer)[in_start:in_end])

    def _probe_for_device(self) -> None:
        """
        探测I2C设备是否存在。
        
        Raises:
            ValueError: 如果设备不存在或无法响应。

        Notes:
            - 优先尝试写空字节确认设备存在。
            - 如果写失败则尝试读一个字节。
            - 若两者均失败，则认定设备不存在。
            - 非ISR-safe。

        ==========================================

        Probe for device to ensure it responds on the bus.

        Raises:
            ValueError: Raised if the device is absent or does not respond.
            
        Notes:
            - First attempts empty write to probe device.
            - If write fails, tries reading 1 byte.
            - If both fail, device is considered absent.
            - Not ISR-safe.
        """
        try:
            self.i2c.writeto(self.device_address, b'')
        except OSError:
            try:
                result = bytearray(1)
                self.i2c.readfrom_into(self.device_address, result)
            except OSError:
                raise ValueError(f'No I2C device at address: 0x{self.device_address:x}')


class MLX90640:
    """
    该类提供对MLX90640红外热像仪的控制和数据读取功能，支持温度计算和参数提取。

    Attributes:
        ee_data (array.array): 存储从EEPROM读取的校准数据。
        i2c_read_len (int): I2C单次读取的最大字数，固定为128。
        scale_alpha (float): alpha缩放因子，固定为1e-6。
        mlx90640_deviceid1 (int): 设备ID寄存器地址，固定为0x2407。
        openair_ta_shift (int): 环境温度偏移值，固定为8。
        inbuf (bytearray): I2C读取数据的缓冲区。
        addrbuf (bytearray): 存储I2C地址的缓冲区。
        i2c_device (I2CDevice): I2C设备实例。
        mlx90640_frame (array.array): 存储从传感器读取的帧数据。
        k_vdd (int): VDD校准参数。
        vdd25 (int): 25°C时的VDD参考值。
        kv_ptat (float): PTAT电压系数。
        kt_ptat (float): PTAT温度系数。
        v_ptat25 (int): 25°C时的PTAT参考电压。
        alpha_ptat (float): PTAT alpha系数。
        gain_ee (int): 增益校准值。
        tgc (float): 温度梯度补偿系数。
        resolution_ee (int): EEPROM中存储的分辨率。
        ks_ta (float): 环境温度补偿系数。
        ct (list): 温度范围临界点列表。
        ks_to (list): 目标温度补偿系数列表。
        cp_alpha (list): 补偿像素的alpha系数列表。
        cp_offset (list): 补偿像素的偏移系数列表。
        alpha (array.array): 每个像素的alpha系数数组。
        alpha_scale (int): alpha系数的缩放因子。
        offset (array.array): 每个像素的偏移系数数组。
        kta (array.array): 每个像素的温度补偿系数数组。
        kta_scale (int): kta系数的缩放因子。
        kv (array.array): 每个像素的电压补偿系数数组。
        kv_scale (int): kv系数的缩放因子。
        il_chess_c (list): 交错模式补偿系数列表。
        broken_pixels (set): 损坏像素的索引集合。
        outlier_pixels (set): 异常像素的索引集合。
        calibration_mode_ee (int): EEPROM中存储的校准模式。

    Methods:
        __init__(i2c_bus: machine.I2C, address: int=0x33) -> None: 初始化MLX90640实例。
        serial_number() -> list: 获取传感器的序列号。
        refresh_rate() -> int: 获取当前刷新率。
        refresh_rate(rate: int) -> None: 设置传感器的刷新率。
        get_frame(framebuf: list) -> None: 读取一帧温度数据并计算每个像素的温度。
        _get_frame_data() -> int: 从传感器读取帧数据。
        _get_ta() -> float: 计算环境温度。
        _get_vdd() -> float: 计算供电电压。
        _calculate_to(emissivity: float, tr: float, result: list) -> None: 计算目标温度。
        _extract_parameters() -> None: 从EEPROM数据中提取校准参数。
        _extract_vdd_parameters() -> None: 提取VDD相关校准参数。
        _extract_ptat_parameters() -> None: 提取PTAT相关校准参数。
        _extract_gain_parameters() -> None: 提取增益相关校准参数。
        _extract_tgc_parameters() -> None: 提取温度梯度补偿相关参数。
        _extract_resolution_parameters() -> None: 提取分辨率相关参数。
        _extract_ks_ta_parameters() -> None: 提取环境温度补偿系数。
        _extract_ks_to_parameters() -> None: 提取目标温度补偿系数。
        _extract_cp_parameters() -> None: 提取补偿像素相关参数。
        _extract_alpha_parameters() -> None: 提取每个像素的alpha系数。
        _extract_offset_parameters() -> None: 提取每个像素的偏移系数。
        _extract_kta_pixel_parameters() -> None: 提取每个像素的温度补偿系数。
        _extract_kv_pixel_parameters() -> None: 提取每个像素的电压补偿系数。
        _extract_cilc_parameters() -> None: 提取交错模式补偿参数。
        _extract_deviating_pixels() -> None: 提取异常像素信息。
        _unique_list_pairs(input_list: set) -> tuple: 生成集合中元素的唯一配对。
        _are_pixels_adjacent(pix1: int, pix2: int) -> bool: 判断两个像素是否相邻。
        _is_pixel_bad(pixel: int) -> bool: 判断像素是否损坏或异常。
        _i2c_write_word(write_address: int, data: int) -> None: 向指定地址写入一个字数据。
        _i2c_read_words(addr: int, buffer: array.array, *, end: int=None) -> None: 从指定地址读取多个字数据到缓冲区。

    Notes:
        - 该类需要通过I2C总线与MLX90640通信，所有I2C操作均非ISR-safe。
        - 初始化时会读取EEPROM中的校准数据并提取参数，耗时较长。
        - 最大支持768个像素（32x24）的温度数据读取和计算。

    ==========================================

    Interface to the MLX90640 infrared thermal camera, supporting temperature calculation and parameter extraction.

    Attributes:
        ee_data (array.array): Stores calibration data read from EEPROM.
        i2c_read_len (int): Maximum number of words for single I2C read, fixed at 128.
        scale_alpha (float): Alpha scaling factor, fixed at 1e-6.
        mlx90640_deviceid1 (int): Device ID register address, fixed at 0x2407.
        openair_ta_shift (int): Ambient temperature shift value, fixed at 8.
        inbuf (bytearray): Buffer for I2C read data.
        addrbuf (bytearray): Buffer for storing I2C addresses.
        i2c_device (I2CDevice): I2C device instance.
        mlx90640_frame (array.array): Stores frame data read from the sensor.
        k_vdd (int): VDD calibration parameter.
        vdd25 (int): VDD reference value at 25°C.
        kv_ptat (float): PTAT voltage coefficient.
        kt_ptat (float): PTAT temperature coefficient.
        v_ptat25 (int): PTAT reference voltage at 25°C.
        alpha_ptat (float): PTAT alpha coefficient.
        gain_ee (int): Gain calibration value.
        tgc (float): Temperature gradient compensation coefficient.
        resolution_ee (int): Resolution stored in EEPROM.
        ks_ta (float): Ambient temperature compensation coefficient.
        ct (list): List of temperature range critical points.
        ks_to (list): List of target temperature compensation coefficients.
        cp_alpha (list): List of alpha coefficients for compensation pixels.
        cp_offset (list): List of offset coefficients for compensation pixels.
        alpha (array.array): Array of alpha coefficients for each pixel.
        alpha_scale (int): Scaling factor for alpha coefficients.
        offset (array.array): Array of offset coefficients for each pixel.
        kta (array.array): Array of temperature compensation coefficients for each pixel.
        kta_scale (int): Scaling factor for kta coefficients.
        kv (array.array): Array of voltage compensation coefficients for each pixel.
        kv_scale (int): Scaling factor for kv coefficients.
        il_chess_c (list): List of interlaced mode compensation coefficients.
        broken_pixels (set): Set of indices for broken pixels.
        outlier_pixels (set): Set of indices for outlier pixels.
        calibration_mode_ee (int): Calibration mode stored in EEPROM.

    Methods:
        __init__(i2c_bus: machine.I2C, address: int=0x33) -> None: Initialize MLX90640 instance.
        serial_number() -> list: Get the serial number of the sensor.
        refresh_rate() -> int: Get current refresh rate.
        refresh_rate(rate: int) -> None: Set the refresh rate of the sensor.
        get_frame(framebuf: list) -> None: Read a frame of temperature data and calculate each pixel's temperature.
        _get_frame_data() -> int: Read frame data from the sensor.
        _get_ta() -> float: Calculate ambient temperature.
        _get_vdd() -> float: Calculate supply voltage.
        _calculate_to(emissivity: float, tr: float, result: list) -> None: Calculate target temperature.
        _extract_parameters() -> None: Extract calibration parameters from EEPROM data.
        _extract_vdd_parameters() -> None: Extract VDD-related calibration parameters.
        _extract_ptat_parameters() -> None: Extract PTAT-related calibration parameters.
        _extract_gain_parameters() -> None: Extract gain-related calibration parameters.
        _extract_tgc_parameters() -> None: Extract temperature gradient compensation parameters.
        _extract_resolution_parameters() -> None: Extract resolution-related parameters.
        _extract_ks_ta_parameters() -> None: Extract ambient temperature compensation coefficients.
        _extract_ks_to_parameters() -> None: Extract target temperature compensation coefficients.
        _extract_cp_parameters() -> None: Extract compensation pixel parameters.
        _extract_alpha_parameters() -> None: Extract alpha coefficients for each pixel.
        _extract_offset_parameters() -> None: Extract offset coefficients for each pixel.
        _extract_kta_pixel_parameters() -> None: Extract temperature compensation coefficients for each pixel.
        _extract_kv_pixel_parameters() -> None: Extract voltage compensation coefficients for each pixel.
        _extract_cilc_parameters() -> None: Extract interlaced mode compensation parameters.
        _extract_deviating_pixels() -> None: Extract information about deviating pixels.
        _unique_list_pairs(input_list: set) -> tuple: Generate unique pairs of elements in the set.
        _are_pixels_adjacent(pix1: int, pix2: int) -> bool: Determine if two pixels are adjacent.
        _is_pixel_bad(pixel: int) -> bool: Check if a pixel is broken or outlier.
        _i2c_write_word(write_address: int, data: int) -> None: Write a word of data to the specified address.
        _i2c_read_words(addr: int, buffer: array.array, *, end: int=None) -> None: Read multiple words from the specified address into buffer.

    Notes:
        - This class communicates with MLX90640 via I2C bus, all I2C operations are not ISR-safe.
        - Initialization reads calibration data from EEPROM and extracts parameters, which takes time.
        - Maximum support for 768 pixels (32x24) temperature data reading and calculation.
    """
    # 类常量定义
    i2c_read_len = 128
    scale_alpha = 1e-6
    mlx90640_deviceid1 = 0x2407
    openair_ta_shift = 8

    def __init__(self, i2c_bus: machine.I2C, address: int = None):
        """
        初始化MLX90640红外热像仪实例，建立I2C通信并读取校准数据。

        Args:
            i2c_bus (machine.I2C): 已初始化的I2C总线实例。
            address (int): MLX90640的I2C地址。

        Raises:
            TypeError: i2c_bus 不是 machine.I2C 实例，address 不是 int。
            ValueError: address 不在合法范围内。

        Notes:
            - 初始化过程会读取EEPROM数据并提取校准参数，耗时较长。
            - 若设备连接失败或参数提取错误，会抛出相应异常。
            - I2C默认地址根据手册来看是0x33,实际上我们通过判断连接设备后扫描到的符合范围的设备地址进行I2C地址的传入。

        ==========================================

        Initialize MLX90640 infrared thermal camera instance, establish I2C communication and read calibration data.

        Args:
            i2c_bus (machine.I2C): Initialized I2C bus instance.
            address (int): I2C address of MLX90640.

        Raises:
            TypeError: i2c_bus is not an instance of machine.I2C, address is not an int.
            ValueError: address is not within the valid range.

        Notes:
            - Initialization reads EEPROM data and extracts calibration parameters, which takes time.
            - Corresponding exceptions will be thrown if device connection fails or parameter extraction errors occur.
            - The default I2C address is 0x33 according to the manual, but in practice, we use the device address detected after connecting the device to set the I2C address.
        """
        # 参数校验
        if not isinstance(i2c_bus, machine.I2C):
            raise TypeError(f"i2c_bus must be a machine.I2C instance, got {type(i2c_bus).__name__}")
        if not isinstance(address, int):
            raise TypeError(f"address must be an int or None, got {type(address).__name__}")
        # 这里按手册默认范围，可根据实际修改
        if not (0x31 <= address <= 0x35):
            raise ValueError(f"Invalid MLX90640 I2C address: 0x{address:x}")
            
        # 初始化EEPROM数据缓冲区
        self.ee_data = init_int_array(1024)
        # 双缓存
        self.inbuf = bytearray(2 * self.i2c_read_len)
        self.addrbuf = bytearray(2)
        self.i2c_device = I2CDevice(i2c_bus, address)
        self.mlx90640_frame = init_int_array(834)

        # 读取EEPROM数据
        self._i2c_read_words(0x2400, self.ee_data)

        # 初始化校准参数
        self.k_vdd = 0
        self.vdd25 = 0
        self.kv_ptat = 0.0
        self.kt_ptat = 0.0
        self.v_ptat25 = 0
        self.alpha_ptat = 0.0
        self.gain_ee = 0
        self.tgc = 0.0
        self.resolution_ee = 0
        self.ks_ta = 0.0
        self.ct = [0] * 4
        self.ks_to = [0.0] * 5
        self.cp_alpha = [0.0, 0.0]
        self.cp_offset = [0, 0]
        self.alpha = None
        self.alpha_scale = 0
        self.offset = None
        self.kta = None
        self.kta_scale = 0
        self.kv = None
        self.kv_scale = 0
        self.il_chess_c = [0.0, 0.0, 0.0]
        self.broken_pixels = set()
        self.outlier_pixels = set()
        self.calibration_mode_ee = 0
        self.cp_kta = 0.0
        self.cp_kv = 0.0

        # 提取校准参数
        self._extract_parameters()

    @property
    def serial_number(self) -> list:
        """
        获取传感器的唯一序列号，由3个十六进制值组成。

        Returns:
            list: 包含3个整数的列表，代表传感器的序列号。

        Notes:
            序列号从设备寄存器中读取，每次访问都会执行I2C操作。

        ==========================================

        Get the unique serial number of the sensor, consisting of 3 hex values.

        Returns:
            list: List containing 3 integers representing the sensor's serial number.

        Notes:
            The serial number is read from the device register, and each access performs an I2C operation.
        """
        serial_words = [0, 0, 0]
        self._i2c_read_words(self.mlx90640_deviceid1, serial_words)
        return serial_words

    @property
    def refresh_rate(self) -> int:
        """
        获取当前传感器的刷新率，返回值对应RefreshRate类中的常量。

        Returns:
            int: 当前刷新率的二进制表示值，对应RefreshRate类的属性。

        Notes:
            读取过程会执行I2C操作，非ISR-safe。

        ==========================================

        Get the current refresh rate of the sensor, the return value corresponds to constants in RefreshRate class.

        Returns:
            int: Binary representation of current refresh rate, corresponding to attributes in RefreshRate class.

        Notes:
            Reading process performs I2C operation, not ISR-safe.
        """
        control_register = [0]
        self._i2c_read_words(0x800D, control_register)
        return (control_register[0] >> 7) & 0x07

    @refresh_rate.setter
    def refresh_rate(self, rate: int) -> None:
        """
        设置传感器的刷新率，需使用RefreshRate类中的常量。

        Args:
            rate (int): 目标刷新率，必须是RefreshRate类中定义的常量之一。

        Raises:
            ValueError: 当输入的刷新率值无效时抛出。

        Notes:
            - 设置过程会执行I2C读写操作，非ISR-safe。
            - 过高的刷新率可能导致I2C总线通信失败，建议从低到高逐步测试。

        ==========================================

        Set the refresh rate of the sensor, must use constants from RefreshRate class.

        Args:
            rate (int): Target refresh rate, must be one of the constants defined in RefreshRate class.

        Raises:
            ValueError: If input refresh rate value is invalid.

        Notes:
            - Setting process performs I2C read and write operations, not ISR-safe.
            - Excessively high refresh rates may cause I2C bus communication failures, it is recommended to test gradually from low to high.
        """
        # 验证刷新率值是否有效
        valid_rates = {
            RefreshRate.REFRESH_0_5_HZ,
            RefreshRate.REFRESH_1_HZ,
            RefreshRate.REFRESH_2_HZ,
            RefreshRate.REFRESH_4_HZ,
            RefreshRate.REFRESH_8_HZ,
            RefreshRate.REFRESH_16_HZ,
            RefreshRate.REFRESH_32_HZ,
            RefreshRate.REFRESH_64_HZ
        }
        if rate not in valid_rates:
            raise ValueError("Invalid refresh rate value")

        control_register = [0]
        value = (rate & 0x7) << 7
        self._i2c_read_words(0x800D, control_register)
        value |= control_register[0] & 0xFC7F
        self._i2c_write_word(0x800D, value)

    def get_frame(self, framebuf: list) -> None:
        """
        从传感器读取一帧完整数据，计算32x24共768个像素的温度（摄氏度），并存储到输入缓冲区。

        Args:
            framebuf (list): 用于存储温度数据的列表，长度必须为768。

        Raises:
            RuntimeError: 当帧数据读取错误时抛出。
            ValueError: 当输入缓冲区长度不等于768时抛出。

        Notes:
            - 调用前需确保framebuf长度为768，否则可能导致数据溢出或不完整。
            - 内部会执行多次I2C操作，非ISR-safe。
            - 发射率固定为0.95，如需修改需修改方法内部参数。

        ==========================================

        Read a complete frame of data from the sensor, calculate the temperature (in Celsius) for 768 pixels (32x24),
        and store it in the input buffer.

        Args:
            framebuf (list): List for storing temperature data, must have a length of 768.

        Raises:
            RuntimeError: Thrown when frame data reading error occurs.
            ValueError: Thrown when input buffer length is not 768.

        Notes:
            - Ensure framebuf has a length of 768 before calling, otherwise data overflow or incompleteness may occur.
            - Internally performs multiple I2C operations, not ISR-safe.
            - Emissivity is fixed at 0.95, modify internal parameters if needed.
        """
        # 验证输入缓冲区长度
        if len(framebuf) != 768:
            raise ValueError("framebuf must have a length of 768")

        emissivity = 0.95

        status = self._get_frame_data()

        if status < 0:
            raise RuntimeError('Frame data error')

        tr = self._get_ta() - self.openair_ta_shift

        self._calculate_to(emissivity, tr, framebuf)

    def _get_frame_data(self) -> int:
        """
        从传感器读取帧数据并存储到mlx90640_frame缓冲区。

        Returns:
            int: 帧状态值，0表示成功。

        Raises:
            RuntimeError: 当读取重试次数超过4次时抛出。

        Notes:
            - 内部会等待数据就绪信号，可能阻塞一定时间。
            - 执行多次I2C操作，非ISR-safe。

        ==========================================

        Read frame data from the sensor and store it in mlx90640_frame buffer.

        Returns:
            int: Frame status value, 0 indicates success.

        Raises:
            RuntimeError: Thrown when read retries exceed 4 times.

        Notes:
            - Internally waits for data ready signal, may block for a certain time.
            - Performs multiple I2C operations, not ISR-safe.
        """
        data_ready = 0
        cnt = 0
        status_register = [0]
        control_register = [0]

        while data_ready == 0:
            self._i2c_read_words(0x8000, status_register)
            data_ready = status_register[0] & 0x0008

        while (data_ready != 0) and (cnt < 5):
            self._i2c_write_word(0x8000, 0x0030)
            self._i2c_read_words(0x0400, self.mlx90640_frame, end=832)

            self._i2c_read_words(0x8000, status_register)
            data_ready = status_register[0] & 0x0008
            cnt += 1

        if cnt > 4:
            raise RuntimeError('Too many retries')

        self._i2c_read_words(0x800D, control_register)
        self.mlx90640_frame[832] = control_register[0]
        self.mlx90640_frame[833] = status_register[0] & 0x0001
        return self.mlx90640_frame[833]

    def _get_ta(self) -> float:
        """
        计算环境温度（摄氏度）。

        Returns:
            float: 环境温度值，单位为摄氏度。

        Notes:
            需在读取帧数据后调用，依赖mlx90640_frame中的数据。

        ==========================================

        Calculate ambient temperature (in Celsius).

        Returns:
            float: Ambient temperature value in Celsius.

        Notes:
            Must be called after reading frame data, depends on data in mlx90640_frame.
        """
        vdd = self._get_vdd()

        ptat = self.mlx90640_frame[800]
        if ptat > 32767:
            ptat -= 65536

        ptat_art = self.mlx90640_frame[768]
        if ptat_art > 32767:
            ptat_art -= 65536
        ptat_art = (ptat / (ptat * self.alpha_ptat + ptat_art)) * math.pow(2, 18)

        ta = ptat_art / (1 + self.kv_ptat * (vdd - 3.3)) - self.v_ptat25
        ta = ta / self.kt_ptat + 25
        return ta

    def _get_vdd(self) -> float:
        """
        计算传感器的供电电压（伏特）。

        Returns:
            float: 供电电压值，单位为伏特。

        Notes:
            需在读取帧数据后调用，依赖mlx90640_frame中的数据。

        ==========================================

        Calculate the supply voltage of the sensor (in volts).

        Returns:
            float: Supply voltage value in volts.

        Notes:
            Must be called after reading frame data, depends on data in mlx90640_frame.
        """
        vdd = self.mlx90640_frame[810]

        if vdd > 32767:
            vdd -= 65536

        resolution_ram = (self.mlx90640_frame[832] & 0x0C00) >> 10
        resolution_correction = math.pow(2, self.resolution_ee) / math.pow(2, resolution_ram)
        vdd = (resolution_correction * vdd - self.vdd25) / self.k_vdd + 3.3

        return vdd

    def _calculate_to(self, emissivity: float, tr: float, result: list) -> None:
        """
        计算每个像素的目标温度（摄氏度）并存储到结果列表。

        Args:
            emissivity (float): 物体发射率，通常为0.95。
            tr (float): 参考温度，由环境温度计算得出。
            result (list): 用于存储目标温度的列表，长度必须为768。

        Raises:
            ValueError: 当result列表长度不等于768时抛出。

        Notes:
            - 需在读取帧数据并计算环境温度后调用。
            - 损坏或异常像素会被标记为-273.15°C。

        ==========================================

        Calculate the target temperature (in Celsius) for each pixel and store it in the result list.

        Args:
            emissivity (float): Object emissivity, usually 0.95.
            tr (float): Reference temperature, calculated from ambient temperature.
            result (list): List for storing target temperatures, must have a length of 768.

        Raises:
            ValueError: Thrown when result list length is not 768.

        Notes:
            - Must be called after reading frame data and calculating ambient temperature.
            - Broken or outlier pixels will be marked as -273.15°C.
        """
        if len(result) != 768:
            raise ValueError("Result list must have a length of 768")
        # 当前帧的子页面编号（0 或 1）
        sub_page = self.mlx90640_frame[833]
        # alpha 温度补偿系数数组（四个范围区间用）
        alpha_corr_r = [0.0] * 4
        # 控制像素（参考像素）的红外数据（两个值，对应两个参考像素）
        ir_data_cp = [0, 0]
        # 获取电源电压 (VDD) 和环境温度 (Ta)
        vdd = self._get_vdd()
        ta = self._get_ta()
        # 转换为绝对温度 (K)，并计算四次方
        ta4 = (ta + 273.15) ** 4
        tr4 = (tr + 273.15) ** 4
        ta_tr = tr4 - (tr4 - ta4) / emissivity
        # 计算反射温度修正
        kta_scale = math.pow(2, self.kta_scale)
        kv_scale = math.pow(2, self.kv_scale)
        alpha_scale = math.pow(2, self.alpha_scale)
        # Alpha 校正系数（不同温度范围的补偿）
        alpha_corr_r[0] = 1 / (1 + self.ks_to[0] * 40)
        alpha_corr_r[1] = 1.0
        alpha_corr_r[2] = 1 + self.ks_to[1] * self.ct[2]
        alpha_corr_r[3] = alpha_corr_r[2] * (1 + self.ks_to[2] * (self.ct[3] - self.ct[2]))

        # 增益计算（从帧数据中提取）
        gain = self.mlx90640_frame[778]
        if gain > 32767:
            gain -= 65536
        gain = self.gain_ee / gain

        mode = (self.mlx90640_frame[832] & 0x1000) >> 5
        # 控制原始像素值
        ir_data_cp[0] = self.mlx90640_frame[776]
        ir_data_cp[1] = self.mlx90640_frame[808]
        for i in range(2):
            if ir_data_cp[i] > 32767:
                ir_data_cp[i] -= 65536
            ir_data_cp[i] *= gain
        # 控制像素补偿（基于偏移、温度、电压）
        ir_data_cp[0] -= self.cp_offset[0] * (1 + self.cp_kta * (ta - 25)) * (1 + self.cp_kv * (vdd - 3.3))
        if mode == self.calibration_mode_ee:
            ir_data_cp[1] -= self.cp_offset[1] * (1 + self.cp_kta * (ta - 25)) * (1 + self.cp_kv * (vdd - 3.3))
        else:
            ir_data_cp[1] -= (self.cp_offset[1] + self.il_chess_c[0]) * (1 + self.cp_kta * (ta - 25)) * (
                    1 + self.cp_kv * (vdd - 3.3))
        # 遍历 768 个像素，计算每个像素的温度
        for pixel_number in range(768):
            if self._is_pixel_bad(pixel_number):
                result[pixel_number] = -273.15
                continue
            # 行列模式相关的采样补偿计算
            il_pattern = pixel_number // 32 - (pixel_number // 64) * 2
            conversion_pattern = ((pixel_number + 2) // 4 - (pixel_number + 3) // 4 + (
                    pixel_number + 1) // 4 - pixel_number // 4) * (1 - 2 * il_pattern)

            if mode == 0:
                pattern = il_pattern
            else:
                chess_pattern = il_pattern ^ (pixel_number - (pixel_number // 2) * 2)
                pattern = chess_pattern

            if pattern == sub_page:
                ir_data = self.mlx90640_frame[pixel_number]

                if ir_data > 32767:
                    ir_data -= 65536

                ir_data *= gain
                # 应用像素自身的偏移补偿（随 Ta/Vdd）
                kta = self.kta[pixel_number] / kta_scale
                kv = self.kv[pixel_number] / kv_scale
                ir_data -= self.offset[pixel_number] * (1 + kta * (ta - 25)) * (1 + kv * (vdd - 3.3))

                if mode != self.calibration_mode_ee:
                    ir_data += self.il_chess_c[2] * (2 * il_pattern - 1) - self.il_chess_c[1] * conversion_pattern
                # 去除 TGC（温度梯度系数）影响
                ir_data = ir_data - self.tgc * ir_data_cp[sub_page]
                ir_data /= emissivity

                alpha_compensated = (
                        (self.scale_alpha * alpha_scale / self.alpha[pixel_number])
                        * (1 + self.ks_ta * (ta - 25))
                )
                # 计算温度（Stefan-Boltzmann 辐射公式的修正）
                sx = math.sqrt(math.sqrt(
                    alpha_compensated
                    * alpha_compensated
                    * alpha_compensated
                    * (ir_data + alpha_compensated * ta_tr)
                ))
                to = math.sqrt(math.sqrt(
                    (ir_data / (alpha_compensated * (1 - self.ks_to[1] * 273.15) + sx) + ta_tr)
                )) - 273.15

                if to < self.ct[1]:
                    torange = 0
                elif to < self.ct[2]:
                    torange = 1
                elif to < self.ct[3]:
                    torange = 2
                else:
                    torange = 3
                # 再次修正，得到最终温度值
                to = math.sqrt(math.sqrt(
                    ir_data / (
                            alpha_compensated
                            * alpha_corr_r[torange]
                            * (1 + self.ks_to[torange] * (to - self.ct[torange]))
                    ) + ta_tr
                )) - 273.15

                result[pixel_number] = to

    def _extract_parameters(self) -> None:
        """
        从EEPROM数据中提取所有校准参数，供温度计算使用。

        Notes:
            该方法在初始化时自动调用，会依次调用多个参数提取方法。

        ==========================================

        Extract all calibration parameters from EEPROM data for temperature calculation.

        Notes:
            This method is automatically called during initialization and will sequentially call multiple parameter extraction methods.
        """
        try:
            self._extract_vdd_parameters()
            self._extract_ptat_parameters()
            self._extract_gain_parameters()
            self._extract_tgc_parameters()
            self._extract_resolution_parameters()
            self._extract_ks_ta_parameters()
            self._extract_ks_to_parameters()
            self._extract_cp_parameters()
            self._extract_alpha_parameters()
            self._extract_offset_parameters()
            self._extract_kta_pixel_parameters()
            self._extract_kv_pixel_parameters()
            self._extract_cilc_parameters()
            self._extract_deviating_pixels()
        except Exception as e:
            raise RuntimeError(f"Failed to extract parameters: {e}")

    def _extract_vdd_parameters(self) -> None:
        """
        从EEPROM数据中提取VDD相关的校准参数。

        Notes:
            提取的参数包括k_vdd和vdd25，用于供电电压计算。

        ==========================================

        Extract VDD-related calibration parameters from EEPROM data.

        Notes:
            Extracted parameters include k_vdd and vdd25, used for supply voltage calculation.
        """
        # 提取VDD参数
        self.k_vdd = (self.ee_data[51] & 0xFF00) >> 8
        if self.k_vdd > 127:
            self.k_vdd -= 256  # 转换为有符号整数
        self.k_vdd *= 32
        self.vdd25 = self.ee_data[51] & 0x00FF
        self.vdd25 = ((self.vdd25 - 256) << 5) - 8192

    def _extract_ptat_parameters(self) -> None:
        """
        从EEPROM数据中提取PTAT（比例温度传感器）相关的校准参数。

        Notes:
            提取的参数包括kv_ptat、kt_ptat、v_ptat25和alpha_ptat，用于环境温度计算。

        ==========================================

        Extract PTAT (Proportional To Absolute Temperature) related calibration parameters from EEPROM data.

        Notes:
            Extracted parameters include kv_ptat, kt_ptat, v_ptat25 and alpha_ptat, used for ambient temperature calculation.
        """
        self.kv_ptat = (self.ee_data[50] & 0xFC00) >> 10
        if self.kv_ptat > 31:
            self.kv_ptat -= 64
        self.kv_ptat /= 4096
        self.kt_ptat = self.ee_data[50] & 0x03FF
        if self.kt_ptat > 511:
            self.kt_ptat -= 1024
        self.kt_ptat /= 8
        self.v_ptat25 = self.ee_data[49]
        self.alpha_ptat = (self.ee_data[16] & 0xF000) / math.pow(2, 14) + 8

    def _extract_gain_parameters(self) -> None:
        """
        从EEPROM数据中提取增益相关的校准参数。

        Notes:
            提取的参数为gain_ee，用于红外数据的增益补偿。

        ==========================================

        Extract gain-related calibration parameters from EEPROM data.

        Notes:
            Extracted parameter is gain_ee, used for gain compensation of infrared data.
        """
        self.gain_ee = self.ee_data[48]
        if self.gain_ee > 32767:
            self.gain_ee -= 65536

    def _extract_tgc_parameters(self) -> None:
        """
        从EEPROM数据中提取温度梯度补偿（TGC）相关参数。

        Notes:
            提取的参数为tgc，用于补偿温度梯度对测量的影响。

        ==========================================

        Extract Temperature Gradient Compensation (TGC) related parameters from EEPROM data.

        Notes:
            Extracted parameter is tgc, used to compensate for the influence of temperature gradient on measurement.
        """
        self.tgc = self.ee_data[60] & 0x00FF
        if self.tgc > 127:
            self.tgc -= 256
        self.tgc /= 32

    def _extract_resolution_parameters(self) -> None:
        """
        从EEPROM数据中提取分辨率相关参数。

        Notes:
            提取的参数为resolution_ee，用于电压和温度计算的分辨率校正。

        ==========================================

        Extract resolution-related parameters from EEPROM data.

        Notes:
            Extracted parameter is resolution_ee, used for resolution correction in voltage and temperature calculation.
        """
        self.resolution_ee = (self.ee_data[56] & 0x3000) >> 12

    def _extract_ks_ta_parameters(self) -> None:
        """
        从EEPROM数据中提取环境温度补偿系数（ks_ta）。

        Notes:
            ks_ta用于alpha系数的环境温度补偿。

        ==========================================

        Extract ambient temperature compensation coefficient (ks_ta) from EEPROM data.

        Notes:
            ks_ta is used for ambient temperature compensation of alpha coefficients.
        """
        self.ks_ta = (self.ee_data[60] & 0xFF00) >> 8
        if self.ks_ta > 127:
            self.ks_ta -= 256
        self.ks_ta /= 8192

    def _extract_ks_to_parameters(self) -> None:
        """
        从EEPROM数据中提取目标温度补偿系数（ks_to）和温度范围临界点（ct）。

        Notes:
            这些参数用于不同温度范围内的目标温度补偿。

        ==========================================

        Extract target temperature compensation coefficients (ks_to) and temperature range critical points (ct) from EEPROM data.

        Notes:
            These parameters are used for target temperature compensation in different temperature ranges.
        """
        step = ((self.ee_data[63] & 0x3000) >> 12) * 10
        self.ct[0] = -40
        self.ct[1] = 0
        self.ct[2] = (self.ee_data[63] & 0x00F0) >> 4
        self.ct[3] = (self.ee_data[63] & 0x0F00) >> 8
        self.ct[2] *= step
        self.ct[3] = self.ct[2] + self.ct[3] * step

        ks_to_scale = (self.ee_data[63] & 0x000F) + 8
        ks_to_scale = 1 << ks_to_scale

        self.ks_to[0] = self.ee_data[61] & 0x00FF
        self.ks_to[1] = (self.ee_data[61] & 0xFF00) >> 8
        self.ks_to[2] = self.ee_data[62] & 0x00FF
        self.ks_to[3] = (self.ee_data[62] & 0xFF00) >> 8

        for i in range(4):
            if self.ks_to[i] > 127:
                self.ks_to[i] -= 256
            self.ks_to[i] /= ks_to_scale
        self.ks_to[4] = -0.0

    def _extract_cp_parameters(self) -> None:
        """
        从EEPROM数据中提取补偿像素（CP）相关的校准参数。

        Notes:
            提取的参数包括cp_alpha、cp_offset、cp_kta和cp_kv，用于补偿像素的数据校正。

        ==========================================

        Extract calibration parameters related to Compensation Pixels (CP) from EEPROM data.

        Notes:
            Extracted parameters include cp_alpha, cp_offset, cp_kta and cp_kv, used for data correction of compensation pixels.
        """
        offset_sp = [0] * 2
        alpha_sp = [0.0] * 2

        alpha_scale = ((self.ee_data[32] & 0xF000) >> 12) + 27

        offset_sp[0] = self.ee_data[58] & 0x03FF
        if offset_sp[0] > 511:
            offset_sp[0] -= 1024

        offset_sp[1] = (self.ee_data[58] & 0xFC00) >> 10
        if offset_sp[1] > 31:
            offset_sp[1] -= 64
        offset_sp[1] += offset_sp[0]

        alpha_sp[0] = self.ee_data[57] & 0x03FF
        if alpha_sp[0] > 511:
            alpha_sp[0] -= 1024
        alpha_sp[0] /= math.pow(2, alpha_scale)

        alpha_sp[1] = (self.ee_data[57] & 0xFC00) >> 10
        if alpha_sp[1] > 31:
            alpha_sp[1] -= 64
        alpha_sp[1] = (1 + alpha_sp[1] / 128) * alpha_sp[0]

        cp_kta = self.ee_data[59] & 0x00FF
        if cp_kta > 127:
            cp_kta -= 256
        kta_scale1 = ((self.ee_data[56] & 0x00F0) >> 4) + 8
        self.cp_kta = cp_kta / math.pow(2, kta_scale1)

        cp_kv = (self.ee_data[59] & 0xFF00) >> 8
        if cp_kv > 127:
            cp_kv -= 256
        kv_scale = (self.ee_data[56] & 0x0F00) >> 8
        self.cp_kv = cp_kv / math.pow(2, kv_scale)

        self.cp_alpha = alpha_sp
        self.cp_offset = offset_sp

    def _extract_alpha_parameters(self) -> None:
        """
        从EEPROM数据中提取每个像素的alpha系数，用于温度计算。

        Notes:
            alpha系数是像素的关键校准参数，影响温度计算的精度。

        ==========================================

        Extract alpha coefficients for each pixel from EEPROM data, used for temperature calculation.

        Notes:
            Alpha coefficients are key calibration parameters for pixels, affecting the accuracy of temperature calculation.
        """
        acc_rem_scale = self.ee_data[32] & 0x000F
        acc_column_scale = (self.ee_data[32] & 0x00F0) >> 4
        acc_row_scale = (self.ee_data[32] & 0x0F00) >> 8
        alpha_scale = ((self.ee_data[32] & 0xF000) >> 12) + 30
        alpha_ref = self.ee_data[33]
        acc_row = init_int_array(24)
        acc_column = init_int_array(32)
        alpha_temp = init_float_array(768)

        for i in range(6):
            p = i * 4
            acc_row[p + 0] = self.ee_data[34 + i] & 0x000F
            acc_row[p + 1] = (self.ee_data[34 + i] & 0x00F0) >> 4
            acc_row[p + 2] = (self.ee_data[34 + i] & 0x0F00) >> 8
            acc_row[p + 3] = (self.ee_data[34 + i] & 0xF000) >> 12

        for i in range(24):
            if acc_row[i] > 7:
                acc_row[i] -= 16

        for i in range(8):
            p = i * 4
            acc_column[p + 0] = self.ee_data[40 + i] & 0x000F
            acc_column[p + 1] = (self.ee_data[40 + i] & 0x00F0) >> 4
            acc_column[p + 2] = (self.ee_data[40 + i] & 0x0F00) >> 8
            acc_column[p + 3] = (self.ee_data[40 + i] & 0xF000) >> 12

        for i in range(32):
            if acc_column[i] > 7:
                acc_column[i] -= 16

        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                alpha_temp[p] = (self.ee_data[64 + p] & 0x03F0) >> 4
                if alpha_temp[p] > 31:
                    alpha_temp[p] -= 64
                alpha_temp[p] *= 1 << acc_rem_scale
                alpha_temp[p] += (
                        alpha_ref
                        + (acc_row[i] << acc_row_scale)
                        + (acc_column[j] << acc_column_scale)
                )
                alpha_temp[p] /= math.pow(2, alpha_scale)
                alpha_temp[p] -= self.tgc * (self.cp_alpha[0] + self.cp_alpha[1]) / 2
                alpha_temp[p] = self.scale_alpha / alpha_temp[p]

        temp = max(alpha_temp)

        alpha_scale = 0
        while temp < 32768:
            temp *= 2
            alpha_scale += 1

        for i in range(768):
            temp_val = alpha_temp[i] * math.pow(2, alpha_scale)
            alpha_temp[i] = int(temp_val + 0.5)

        self.alpha = alpha_temp
        self.alpha_scale = alpha_scale

    def _extract_offset_parameters(self) -> None:
        """
        从EEPROM数据中提取每个像素的偏移系数，用于红外数据的偏移补偿。

        Notes:
            偏移系数会根据环境温度和供电电压进行动态调整。

        ==========================================

        Extract offset coefficients for each pixel from EEPROM data, used for offset compensation of infrared data.

        Notes:
            Offset coefficients are dynamically adjusted according to ambient temperature and supply voltage.
        """
        occ_row = [0] * 24
        occ_column = [0] * 32

        occ_rem_scale = self.ee_data[16] & 0x000F
        occ_column_scale = (self.ee_data[16] & 0x00F0) >> 4
        occ_row_scale = (self.ee_data[16] & 0x0F00) >> 8
        offset_ref = self.ee_data[17]
        if offset_ref > 32767:
            offset_ref -= 65536

        for i in range(6):
            p = i * 4
            occ_row[p + 0] = self.ee_data[18 + i] & 0x000F
            occ_row[p + 1] = (self.ee_data[18 + i] & 0x00F0) >> 4
            occ_row[p + 2] = (self.ee_data[18 + i] & 0x0F00) >> 8
            occ_row[p + 3] = (self.ee_data[18 + i] & 0xF000) >> 12

        for i in range(24):
            if occ_row[i] > 7:
                occ_row[i] -= 16

        for i in range(8):
            p = i * 4
            occ_column[p + 0] = self.ee_data[24 + i] & 0x000F
            occ_column[p + 1] = (self.ee_data[24 + i] & 0x00F0) >> 4
            occ_column[p + 2] = (self.ee_data[24 + i] & 0x0F00) >> 8
            occ_column[p + 3] = (self.ee_data[24 + i] & 0xF000) >> 12

        for i in range(32):
            if occ_column[i] > 7:
                occ_column[i] -= 16

        self.offset = init_float_array(768)

        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                self.offset[p] = (self.ee_data[64 + p] & 0xFC00) >> 10
                if self.offset[p] > 31:
                    self.offset[p] -= 64
                self.offset[p] *= 1 << occ_rem_scale
                self.offset[p] += (
                        offset_ref
                        + (occ_row[i] << occ_row_scale)
                        + (occ_column[j] << occ_column_scale)
                )

    def _extract_kta_pixel_parameters(self) -> None:
        """
        从EEPROM数据中提取每个像素的温度补偿系数（kta）。

        Notes:
            kta用于补偿环境温度变化对像素测量值的影响。

        ==========================================

        Extract temperature compensation coefficients (kta) for each pixel from EEPROM data.

        Notes:
            kta is used to compensate for the influence of ambient temperature changes on pixel measurements.
        """
        kta_rc = [0] * 4
        kta_temp = init_float_array(768)

        kta_ro_co = (self.ee_data[54] & 0xFF00) >> 8
        if kta_ro_co > 127:
            kta_ro_co -= 256
        kta_rc[0] = kta_ro_co

        kta_re_co = self.ee_data[54] & 0x00FF
        if kta_re_co > 127:
            kta_re_co -= 256
        kta_rc[2] = kta_re_co

        kta_ro_ce = (self.ee_data[55] & 0xFF00) >> 8
        if kta_ro_ce > 127:
            kta_ro_ce -= 256
        kta_rc[1] = kta_ro_ce

        kta_re_ce = self.ee_data[55] & 0x00FF
        if kta_re_ce > 127:
            kta_re_ce -= 256
        kta_rc[3] = kta_re_ce

        kta_scale1 = ((self.ee_data[56] & 0x00F0) >> 4) + 8
        kta_scale2 = self.ee_data[56] & 0x000F

        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                split = 2 * (p // 32 - (p // 64) * 2) + p % 2
                kta_temp[p] = (self.ee_data[64 + p] & 0x000E) >> 1
                if kta_temp[p] > 3:
                    kta_temp[p] -= 8
                kta_temp[p] *= 1 << kta_scale2
                kta_temp[p] += kta_rc[split]
                kta_temp[p] /= math.pow(2, kta_scale1)

        temp = max(abs(k) for k in kta_temp)

        kta_scale1 = 0
        while temp < 64:
            temp *= 2
            kta_scale1 += 1

        for i in range(768):
            temp_val = kta_temp[i] * math.pow(2, kta_scale1)
            if temp_val < 0:
                kta_temp[i] = int(temp_val - 0.5)
            else:
                kta_temp[i] = int(temp_val + 0.5)

        self.kta = kta_temp
        self.kta_scale = kta_scale1

    def _extract_kv_pixel_parameters(self) -> None:
        """
        从EEPROM数据中提取每个像素的电压补偿系数（kv）。

        Notes:
            kv用于补偿供电电压变化对像素测量值的影响。

        ==========================================

        Extract voltage compensation coefficients (kv) for each pixel from EEPROM data.

        Notes:
            kv is used to compensate for the influence of supply voltage changes on pixel measurements.
        """
        kv_t = [0] * 4
        kv_temp = init_float_array(768)

        kv_ro_co = (self.ee_data[52] & 0xF000) >> 12
        if kv_ro_co > 7:
            kv_ro_co -= 16
        kv_t[0] = kv_ro_co

        kv_re_co = (self.ee_data[52] & 0x0F00) >> 8
        if kv_re_co > 7:
            kv_re_co -= 16
        kv_t[2] = kv_re_co

        kv_ro_ce = (self.ee_data[52] & 0x00F0) >> 4
        if kv_ro_ce > 7:
            kv_ro_ce -= 16
        kv_t[1] = kv_ro_ce

        kv_re_ce = self.ee_data[52] & 0x000F
        if kv_re_ce > 7:
            kv_re_ce -= 16
        kv_t[3] = kv_re_ce

        kv_scale = (self.ee_data[56] & 0x0F00) >> 8

        for i in range(24):
            for j in range(32):
                p = 32 * i + j
                split = 2 * (p // 32 - (p // 64) * 2) + p % 2
                kv_temp[p] = kv_t[split]
                kv_temp[p] /= math.pow(2, kv_scale)

        temp = max(abs(kv) for kv in kv_temp)

        kv_scale = 0
        while temp < 64:
            temp *= 2
            kv_scale += 1

        for i in range(768):
            temp_val = kv_temp[i] * math.pow(2, kv_scale)
            if temp_val < 0:
                kv_temp[i] = int(temp_val - 0.5)
            else:
                kv_temp[i] = int(temp_val + 0.5)

        self.kv = kv_temp
        self.kv_scale = kv_scale

    def _extract_cilc_parameters(self) -> None:
        """
        从EEPROM数据中提取交错模式补偿（CILC）参数。

        Notes:
            这些参数用于补偿传感器交错读取模式带来的误差。

        ==========================================

        Extract Crosstalk Interference Light Compensation (CILC) parameters from EEPROM data.

        Notes:
            These parameters are used to compensate for errors caused by the sensor's interleaved reading mode.
        """
        self.calibration_mode_ee = (self.ee_data[10] & 0x0800) >> 4
        self.calibration_mode_ee = self.calibration_mode_ee ^ 0x80

        il_chess_c = [0.0] * 3
        il_chess_c[0] = self.ee_data[53] & 0x003F
        if il_chess_c[0] > 31:
            il_chess_c[0] -= 64
        il_chess_c[0] /= 16.0

        il_chess_c[1] = (self.ee_data[53] & 0x07C0) >> 6
        if il_chess_c[1] > 15:
            il_chess_c[1] -= 32
        il_chess_c[1] /= 2.0

        il_chess_c[2] = (self.ee_data[53] & 0xF800) >> 11
        if il_chess_c[2] > 15:
            il_chess_c[2] -= 32
        il_chess_c[2] /= 8.0

        self.il_chess_c = il_chess_c

    def _extract_deviating_pixels(self) -> None:
        """
        从EEPROM数据中提取损坏像素和异常像素的信息。

        Raises:
            RuntimeError: 当损坏像素或异常像素数量超过4个，或存在相邻的异常像素时抛出。

        Notes:
            异常像素信息用于在温度计算时标记无效数据。

        ==========================================

        Extract information about broken and outlier pixels from EEPROM data.

        Raises:
            RuntimeError: Thrown when the number of broken or outlier pixels exceeds 4, or there are adjacent abnormal pixels.

        Notes:
            Outlier pixel information is used to mark invalid data during temperature calculation.
        """
        pix_cnt = 0
        while (
                (pix_cnt < 768)
                and (len(self.broken_pixels) < 5)
                and (len(self.outlier_pixels) < 5)
        ):
            if self.ee_data[pix_cnt + 64] == 0:
                self.broken_pixels.add(pix_cnt)
            elif (self.ee_data[pix_cnt + 64] & 0x0001) != 0:
                self.outlier_pixels.add(pix_cnt)
            pix_cnt += 1

        if len(self.broken_pixels) > 4:
            raise RuntimeError('More than 4 broken pixels')
        if len(self.outlier_pixels) > 4:
            raise RuntimeError('More than 4 outlier pixels')
        if (len(self.broken_pixels) + len(self.outlier_pixels)) > 4:
            raise RuntimeError('More than 4 faulty pixels')

        for broken_pixel1, broken_pixel2 in self._unique_list_pairs(self.broken_pixels):
            if self._are_pixels_adjacent(broken_pixel1, broken_pixel2):
                raise RuntimeError('Adjacent broken pixels')

        for outlier_pixel1, outlier_pixel2 in self._unique_list_pairs(self.outlier_pixels):
            if self._are_pixels_adjacent(outlier_pixel1, outlier_pixel2):
                raise RuntimeError('Adjacent outlier pixels')

        for broken_pixel in self.broken_pixels:
            for outlier_pixel in self.outlier_pixels:
                if self._are_pixels_adjacent(broken_pixel, outlier_pixel):
                    raise RuntimeError('Adjacent broken and outlier pixels')

    def _unique_list_pairs(self, input_list: set):
        """
        生成集合中元素的所有唯一无序配对。

        Args:
            input_list (set): 输入的元素集合。

        Returns:
            generator:返回生成器对象，每次迭代产出一个包含两个元素的元组。

        Notes:
            每个配对仅出现一次，例如(a, b)和(b, a)会被视为同一个配对，只返回一次。
            该函数是一个生成器函数，函数本身返回值不是具体的元素配对而是生成器对象，迭代产出的值是具体的元素配对。

        ==========================================

        Generate all unique unordered pairs of elements in the set.

        Args:
            input_list (set): Input set of elements.

        Returns:
            generator:Returns an generator object that produces a tuple containing two elements with each iteration.

        Notes:
            Each pair appears only once, e.g., (a, b) and (b, a) are considered the same pair and only returned once.
            This function is a generator function, and its return value is an generator object, producing specific elements as pairs.
        """
        input_list = list(input_list)
        for i in range(len(input_list)):
            for j in range(i + 1, len(input_list)):
                yield input_list[i], input_list[j]

    def _are_pixels_adjacent(self, pix1: int, pix2: int) -> bool:
        """
        判断两个像素是否相邻。

        Args:
            pix1 (int): 第一个像素的索引。
            pix2 (int): 第二个像素的索引。

        Returns:
            bool: 若两个像素相邻则返回True，否则返回False。

        Notes:
            相邻包括水平相邻、垂直相邻和对角线相邻。

        ==========================================

        Determine if two pixels are adjacent.

        Args:
            pix1 (int): Index of the first pixel.
            pix2 (int): Index of the second pixel.

        Returns:
            bool: True if the two pixels are adjacent, False otherwise.

        Notes:
            Adjacency includes horizontal, vertical and diagonal adjacency.
        """
        pix_pos_dif = pix1 - pix2

        if -34 < pix_pos_dif < -30:
            return True
        if -2 < pix_pos_dif < 2:
            return True
        if 30 < pix_pos_dif < 34:
            return True

        return False

    def _is_pixel_bad(self, pixel: int) -> bool:
        """
        判断像素是否为损坏像素或异常像素。

        Args:
            pixel (int): 像素的索引。

        Returns:
            bool: 若像素是损坏或异常像素则返回True，否则返回False。

        ==========================================

        Check if a pixel is a broken or outlier pixel.

        Args:
            pixel (int): Index of the pixel.

        Returns:
            bool: True if the pixel is broken or outlier, False otherwise.
        """
        return pixel in self.broken_pixels or pixel in self.outlier_pixels

    def _i2c_write_word(self, write_address: int, data: int) -> None:
        """
        向传感器的指定地址写入一个16位字数据，并验证写入结果。

        Args:
            write_address (int): 要写入的地址。
            data (int): 要写入的16位数据。

        Notes:
            - 写入后会读取该地址的数据进行验证。
            - 执行I2C操作，非ISR-safe。

        ==========================================

        Write a 16-bit word data to the specified address of the sensor and verify the writing result.

        Args:
            write_address (int): Address to write to.
            data (int): 16-bit data to write.

        Notes:
            - Reads data from the address for verification after writing.
            - Performs I2C operation, not ISR-safe.
        """
        cmd = bytearray(4)
        cmd[0] = write_address >> 8
        cmd[1] = write_address & 0x00FF
        cmd[2] = data >> 8
        cmd[3] = data & 0x00FF
        data_check = [0]

        self.i2c_device.write(cmd)
        self._i2c_read_words(write_address, data_check)

    def _i2c_read_words(
            self,
            addr: int,
            buffer: array.array,
            *,
            end: int = None,
    ) -> None:
        """
        从传感器的指定地址读取多个16位字数据，并存储到缓冲区。

        Args:
            addr (int): 要读取的起始地址。
            buffer (array.array): 用于存储读取数据的缓冲区（整型数组）。
            end (int): 要读取的最大字数，默认None（读取整个缓冲区长度）。

        Raises:
            ValueError: 当缓冲区长度为0或end参数无效时抛出。

        Notes:
            - 单次I2C读取最多读取128个字，超过时会分多次读取。
            - 执行I2C操作，非ISR-safe。

        ==========================================

        Read multiple 16-bit words from the specified address of the sensor and store them in the buffer.

        Args:
            addr (int): Starting address to read from.
            buffer (array.array): Buffer for storing read data (integer array).
            end (int): Maximum number of words to read, default None (read entire buffer length).

        Raises:
            ValueError: If buffer length is 0 or end parameter is invalid.

        Notes:
            - A single I2C read reads at most 128 words, and multiple reads are performed when exceeding this.
            - Performs I2C operation, not ISR-safe.
        """
        if len(buffer) == 0:
            raise ValueError("Buffer cannot be empty")

        if end is not None and (end <= 0 or end > len(buffer)):
            raise ValueError("Invalid end parameter")

        remaining_words = len(buffer) if end is None else end
        offset = 0

        while remaining_words:
            self.addrbuf[0] = addr >> 8  # MSB
            self.addrbuf[1] = addr & 0xFF  # LSB
            read_words = min(remaining_words, self.i2c_read_len)
            self.i2c_device.write_then_read_into(
                self.addrbuf,
                self.inbuf,
                in_end=read_words * 2,
            )

            outwords = struct.unpack(
                '>' + 'H' * read_words,
                self.inbuf[:read_words * 2],
            )
            for i, w in enumerate(outwords):
                buffer[offset + i] = w

            offset += read_words
            remaining_words -= read_words
            addr += read_words
# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
