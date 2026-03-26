# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026-03-23 下午5:30
# @Author  : octaprog7
# @File    : bmp581.py
# @Description : BMP581压力传感器MicroPython驱动，支持温度和压力测量，可配置过采样、数据速率、中断等 参考自:https://github.com/octaprog7/bmp581
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# micropython
# mail: goctaprog@gmail.com
# MIT license

# ======================================== 导入相关模块 =========================================

import micropython
# import array

from sensor_pack import bus_service
from sensor_pack.base_sensor import BaseSensor, Iterator, check_value

# ======================================== 全局变量 ============================================

# 温度转换系数，将原始温度值转换为摄氏度
_kT = 2 ** -16
# 压力转换系数，将原始压力值转换为帕斯卡
_kP = 2 ** -6

# 温度过采样对应的时间倍数（单位：ms）
_osr_t_times = 1.0, 1.1, 1.5, 2.1, 3.3, 5.8, 10.8, 20.8
# 压力过采样对应的时间倍数（单位：ms）
_osr_p_times = 1.0, 1.7, 2.9, 5.4, 10.4, 20.4, 40.4, 80.4

# ======================================== 功能函数 ============================================

def _get_conv_time_ms(temp_only: bool, osr_t: int, osr_p: int) -> float:
    """
    计算单次测量转换时间（毫秒）
    Args:
        temp_only (bool): 是否仅测量温度
        osr_t (int): 温度过采样率索引 (0-7)
        osr_p (int): 压力过采样率索引 (0-7)

    Returns:
        float: 转换时间（毫秒）

    Notes:
        注意：这是单次转换时间，不是数据输出率。

    ==========================================
    Calculate conversion time for a single measurement (milliseconds)
    Args:
        temp_only (bool): Whether to measure only temperature
        osr_t (int): Temperature oversampling index (0-7)
        osr_p (int): Pressure oversampling index (0-7)

    Returns:
        float: Conversion time in milliseconds

    Notes:
        Note: This is single conversion time, not output data rate.
    """
    tmp = _osr_t_times[osr_t]
    if temp_only:
        return tmp
    return tmp + _osr_p_times[osr_p]


def _all_none(*args) -> bool:
    """
    检查所有参数是否均为 None
    Args:
        *args: 可变参数

    Returns:
        bool: 如果所有参数均为 None 则返回 True，否则返回 False

    ==========================================
    Check if all arguments are None
    Args:
        *args: Variable arguments

    Returns:
        bool: True if all arguments are None, False otherwise
    """
    for element in args:
        if element is not None:
            return False
    return True

# ======================================== 自定义类 ============================================

class Bmp581(BaseSensor, Iterator):
    """
    Bosh BMP581 压力传感器驱动类
    Attributes:
        adapter (bus_service.BusAdapter): 总线适配器
        address (int): I2C 设备地址
        big_byte_order (bool): 字节序（固定为小端）
        _buf_2 (bytearray): 2 字节缓冲区
        _buf_3 (bytearray): 3 字节缓冲区
        _osr_t (int): 温度过采样率
        _osr_p (int): 压力过采样率
        _mode (int): 当前工作模式
        _temperature_only (bool): 是否仅测量温度

    Methods:
        init_hardware(): 硬件初始化
        power_mode(): 获取当前电源模式
        temp_oversampling(): 温度过采样率属性
        pressure_oversampling(): 压力过采样率属性
        temperature_only(): 是否仅测量温度属性
        soft_reset(): 软件复位
        start_measurement(): 启动测量
        get_id(): 获取芯片 ID
        get_status(): 获取状态
        get_pressure(): 获取压力（Pa）
        get_temperature(): 获取温度（℃）
        is_data_ready(): 数据就绪标志
        get_conversion_cycle_time(): 获取转换周期时间（ms）
        __next__(): 迭代器接口，返回最新数据

    Notes:
        初始化后需要调用 init_hardware() 完成配置。
        电源电压必须为 3.3V，禁止接 5V。

    ==========================================
    Driver for Bosh BMP581 pressure sensor
    Attributes:
        adapter (bus_service.BusAdapter): Bus adapter
        address (int): I2C device address
        big_byte_order (bool): Byte order (fixed little-endian)
        _buf_2 (bytearray): 2-byte buffer
        _buf_3 (bytearray): 3-byte buffer
        _osr_t (int): Temperature oversampling
        _osr_p (int): Pressure oversampling
        _mode (int): Current operating mode
        _temperature_only (bool): Whether to measure only temperature

    Methods:
        init_hardware(): Initialize hardware
        power_mode(): Get current power mode
        temp_oversampling(): Temperature oversampling property
        pressure_oversampling(): Pressure oversampling property
        temperature_only(): Temperature-only measurement property
        soft_reset(): Software reset
        start_measurement(): Start measurement
        get_id(): Get chip ID
        get_status(): Get status
        get_pressure(): Get pressure (Pa)
        get_temperature(): Get temperature (℃)
        is_data_ready(): Data ready flag
        get_conversion_cycle_time(): Get conversion cycle time (ms)
        __next__(): Iterator interface, return latest data

    Notes:
        Must call init_hardware() after construction to complete configuration.
        Supply voltage must be 3.3V, do not connect to 5V.
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x47) -> None:
        """
        初始化 BMP581 传感器实例
        Args:
            adapter (bus_service.BusAdapter): 总线适配器对象
            address (int): I2C 设备地址，默认 0x47

        Notes:
            设置字节序为小端，初始化内部缓冲区，默认进入睡眠模式。

        ==========================================
        Initialize BMP581 sensor instance
        Args:
            adapter (bus_service.BusAdapter): Bus adapter object
            address (int): I2C device address, default 0x47

        Notes:
            Sets byte order to little-endian, initializes internal buffers,
            defaults to sleep mode.
        """
        super().__init__(adapter, address, False)
        self._buf_2 = bytearray((0 for _ in range(2)))  # for _read_buf_from_mem
        self._buf_3 = bytearray((0 for _ in range(3)))  # for _read_buf_from_mem
        # Temperature oversampling settings
        self._osr_t = 1
        # Pressure oversampling settings
        self._osr_p = 1
        self._mode = 0  # sleep mode
        self._temperature_only = False

    def init_hardware(self) -> None:
        """
        硬件初始化
        Notes:
            配置中断源为数据就绪，并使能中断。
            在构造后需调用此方法完成配置。

        ==========================================
        Initialize hardware
        Notes:
            Configures interrupt source to data ready and enables interrupts.
            Must be called after construction to complete configuration.
        """
        # Configure interrupts. Enable data ready interrupt
        # Bosch disappointed me! In older sensors you could
        # read data ready flag without enabling interrupts!!!
        self._int_source_sel(False, False, True, True)
        # Enable interrupts
        self._int_conf(None, True, None, None, None)

    def __del__(self) -> None:
        """
        析构方法，释放缓冲区
        ==========================================
        Destructor, release buffers
        """
        del self._buf_3
        del self._buf_2

    @property
    def power_mode(self) -> int:
        """
        获取当前电源模式
        Returns:
            int: 0=睡眠模式, 1=正常模式, 2=强制模式, 3=连续模式

        ==========================================
        Get current power mode
        Returns:
            int: 0=sleep mode, 1=normal mode, 2=forced mode, 3=continuous mode
        """
        return self._get_power_mode_or_odr()

    @property
    def temp_oversampling(self) -> int:
        """
        获取温度过采样率索引
        Returns:
            int: 0-7 表示过采样率

        ==========================================
        Get temperature oversampling index
        Returns:
            int: 0-7 representing oversampling rate
        """
        tmp = self._osr_config()
        return 0x07 & tmp

    @temp_oversampling.setter
    def temp_oversampling(self, value: int) -> None:
        """
        设置温度过采样率索引
        Args:
            value (int): 0-7 之间的值

        Raises:
            ValueError: 当 value 不在有效范围内时

        ==========================================
        Set temperature oversampling index
        Args:
            value (int): Value between 0-7

        Raises:
            ValueError: When value is out of valid range
        """
        r = range(8)
        check_value(value, r, f"Value out of range: {r.start}..{r.stop - 1}")
        self._osr_t = value

    @property
    def pressure_oversampling(self) -> int:
        """
        获取压力过采样率索引
        Returns:
            int: 0-7 表示过采样率

        ==========================================
        Get pressure oversampling index
        Returns:
            int: 0-7 representing oversampling rate
        """
        tmp = self._osr_config()
        return (0b0011_1000 & tmp) >> 3

    @pressure_oversampling.setter
    def pressure_oversampling(self, value: int) -> None:
        """
        设置压力过采样率索引
        Args:
            value (int): 0-7 之间的值

        Raises:
            ValueError: 当 value 不在有效范围内时

        ==========================================
        Set pressure oversampling index
        Args:
            value (int): Value between 0-7

        Raises:
            ValueError: When value is out of valid range
        """
        r = range(8)
        check_value(value, r, f"Value out of range: {r.start}..{r.stop - 1}")
        self._osr_p = value

    @property
    def temperature_only(self) -> bool:
        """
        获取是否仅测量温度
        Returns:
            bool: True 表示仅测量温度，False 表示同时测量温度和压力

        ==========================================
        Get whether only temperature is measured
        Returns:
            bool: True if only temperature, False if both temperature and pressure
        """
        return self._temperature_only

    @temperature_only.setter
    def temperature_only(self, value: bool) -> None:
        """
        设置是否仅测量温度
        Args:
            value (bool): True 表示仅测量温度，False 表示同时测量温度和压力

        ==========================================
        Set whether only temperature is measured
        Args:
            value (bool): True to measure only temperature, False to measure both
        """
        self._temperature_only = value

    def _cmd(self, command_code: int) -> None:
        """
        向命令寄存器写入命令
        Args:
            command_code (int): 命令码 (0-255)

        Raises:
            ValueError: 当 command_code 无效时

        ==========================================
        Write command to command register
        Args:
            command_code (int): Command code (0-255)

        Raises:
            ValueError: When command_code is invalid
        """
        check_value(command_code, range(0x100), f"Invalid CMD code: {command_code}")
        self._write_reg(0x7E, command_code)

    def _int_conf(
            self,
            pad_int_drv: [int, None] = None,   # bit 4..7,
            int_en: [bool, None] = None,       # bit 3,
            int_od: [bool, None] = None,       # bit 2,
            int_pol: [bool, None] = None,      # bit 1,
            int_mode: [bool, None] = None,     # bit 0,
    ) -> int:
        """
        配置中断寄存器（0x14）
        Args:
            pad_int_drv (int, None): 引脚驱动能力，0-15
            int_en (bool, None): 中断使能
            int_od (bool, None): 开漏输出使能
            int_pol (bool, None): 中断极性
            int_mode (bool, None): 中断模式

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        ==========================================
        Configure interrupt register (0x14)
        Args:
            pad_int_drv (int, None): Pin drive capability, 0-15
            int_en (bool, None): Interrupt enable
            int_od (bool, None): Open-drain output enable
            int_pol (bool, None): Interrupt polarity
            int_mode (bool, None): Interrupt mode

        Returns:
            int: Current register value (when all parameters are None)
        """
        val = self._read_reg(0x14)[0]
        if _all_none(int_mode, int_pol, int_od, int_en, pad_int_drv):
            return val
        check_value(pad_int_drv, range(0x10), f"Invalid pad_int_drv value: {pad_int_drv}")
        if pad_int_drv is not None:
            val &= ~0xF0  # mask
            val |= pad_int_drv << 4
        if int_en is not None:
            val &= ~(1 << 3)  # mask
            val |= int_en << 3
        if int_od is not None:
            val &= ~(1 << 2)  # mask
            val |= int_od << 2
        if int_pol is not None:
            val &= ~(1 << 1)  # mask
            val |= int_od << 1
        if int_mode is not None:
            val &= 0xFE  # mask
            val |= int_mode
        # print(f"DBG:int_conf: {val}")
        self._write_reg(0x14, val, 1)

    def _int_source_sel(
            self,
            oor_p_en: [int, None] = None,          # bit 3, Pressure data out-of-range (OOR_P)
            fifo_ths_en: [bool, None] = None,      # bit 2, FIFO Threshold/Watermark (FIFO_THS)
            fifo_full_en: [bool, None] = None,     # bit 1, FIFO Full (FIFO_FULL)
            drdy_data_reg_en: [bool, None] = None, # bit 0, Data Ready
    ) -> int:
        """
        配置中断源选择寄存器（0x15）
        Args:
            oor_p_en (int, None): 压力超出范围中断使能
            fifo_ths_en (bool, None): FIFO 阈值中断使能
            fifo_full_en (bool, None): FIFO 满中断使能
            drdy_data_reg_en (bool, None): 数据就绪中断使能

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        ==========================================
        Configure interrupt source selection register (0x15)
        Args:
            oor_p_en (int, None): Pressure out-of-range interrupt enable
            fifo_ths_en (bool, None): FIFO threshold interrupt enable
            fifo_full_en (bool, None): FIFO full interrupt enable
            drdy_data_reg_en (bool, None): Data ready interrupt enable

        Returns:
            int: Current register value (when all parameters are None)
        """
        val = self._read_reg(0x15)[0]
        if _all_none(oor_p_en, fifo_ths_en, fifo_full_en, drdy_data_reg_en):
            return val
        if oor_p_en is not None:
            val &= ~(1 << 3)  # mask
            val |= oor_p_en << 3
        if fifo_ths_en is not None:
            val &= ~(1 << 2)  # mask
            val |= fifo_ths_en << 2
        if fifo_full_en is not None:
            val &= ~(1 << 1)  # mask
            val |= fifo_full_en << 1
        if drdy_data_reg_en is not None:
            val &= 0xFE  # mask
            val |= drdy_data_reg_en
        # print(f"DBG:int_source_sel: {val}")
        self._write_reg(0x15, val, 1)

    def _fifo_config(
            self,
            fifo_mode: [bool, None] = None,
            fifo_threshold: [int, None] = None,
    ) -> int:
        """
        配置 FIFO 寄存器（0x16）
        Args:
            fifo_mode (bool, None): FIFO 模式
            fifo_threshold (int, None): FIFO 阈值 (0-31)

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        ==========================================
        Configure FIFO register (0x16)
        Args:
            fifo_mode (bool, None): FIFO mode
            fifo_threshold (int, None): FIFO threshold (0-31)

        Returns:
            int: Current register value (when all parameters are None)
        """
        val = self._read_reg(0x16)[0]
        if _all_none(fifo_mode, fifo_threshold):
            return val
        check_value(fifo_threshold, range(32), f"Invalid fifo_threshold value: {fifo_threshold}")
        if fifo_mode is not None:
            val &= ~(1 << 5)
            val |= fifo_mode << 5
        if fifo_threshold is not None:
            val &= ~0x1F
            val |= fifo_threshold
        self._write_reg(0x16, val, 1)

    def _odr_config(
            self,
            deep_dis: [bool, None] = None,          # bit 7
            output_data_rate: [int, None] = None,   # bit 6..2
            power_mode: [int, None] = None,         # bit 1..0
    ) -> int:
        """
        配置控制寄存器 0（0x37）
        Args:
            deep_dis (bool, None): 禁用深度睡眠模式
            output_data_rate (int, None): 输出数据率 (0-31)
            power_mode (int, None): 电源模式 (0-3)

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        Notes:
            ODR 设置可能与 OSR 配置不兼容，可通过 effective_osr_rating 检查。

        ==========================================
        Configure Control 0 register (0x37)
        Args:
            deep_dis (bool, None): Disable deep sleep mode
            output_data_rate (int, None): Output data rate (0-31)
            power_mode (int, None): Power mode (0-3)

        Returns:
            int: Current register value (when all parameters are None)

        Notes:
            ODR setting may be incompatible with OSR configuration, check effective_osr_rating.
        """
        val = self._read_reg(0x37)[0]
        if _all_none(deep_dis, output_data_rate, power_mode):
            return val
        check_value(output_data_rate, range(32), f"Invalid ODR value: {output_data_rate}")
        check_value(power_mode, range(4), f"Invalid power mode value: {power_mode}")
        if deep_dis is not None:
            val &= ~(1 << 7)  # mask
            val |= deep_dis << 7
        if output_data_rate is not None:
            val &= ~(0x1F << 2)  # mask
            val |= output_data_rate << 2
        if power_mode is not None:
            val &= ~0b11  # mask
            val |= power_mode
        self._write_reg(0x37, val, 1)

    def _get_frames_in_fifo(self) -> int:
        """
        获取 FIFO 中的帧数
        Returns:
            int: FIFO 中的帧数量

        ==========================================
        Get number of frames in FIFO
        Returns:
            int: Number of frames in FIFO
        """
        return 0x3F & self._read_reg(0x17)[0]

    def _fifo_sel_config(
            self,
            fifo_dec_sel: [int, None] = None,
            fifo_frame_sel: [int, None] = None,
    ) -> int:
        """
        配置 FIFO 选择寄存器（0x18）
        Args:
            fifo_dec_sel (int, None): FIFO 抽取选择 (0-7)
            fifo_frame_sel (int, None): FIFO 帧选择 (0-3)

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        ==========================================
        Configure FIFO selection register (0x18)
        Args:
            fifo_dec_sel (int, None): FIFO decimation selection (0-7)
            fifo_frame_sel (int, None): FIFO frame selection (0-3)

        Returns:
            int: Current register value (when all parameters are None)
        """
        val = self._read_reg(0x18)[0]
        if _all_none(fifo_dec_sel, fifo_frame_sel):
            return val
        check_value(fifo_dec_sel, range(8), f"Invalid fifo_dec_sel value: {fifo_dec_sel}")
        check_value(fifo_frame_sel, range(4), f"Invalid fifo_frame_sel value: {fifo_frame_sel}")
        if fifo_frame_sel is not None:
            val &= ~0b11
            val |= fifo_frame_sel
        if fifo_dec_sel is not None:
            val &= ~0b111 << 2
            val |= fifo_dec_sel << 2
        self._write_reg(0x18, val, 1)

    def _read_buf_from_mem(self, address: int, buf) -> bytes:
        """
        从设备内存地址读取数据到缓冲区
        Args:
            address (int): 起始内存地址
            buf: 目标缓冲区

        Returns:
            bytes: 读取的数据（即 buf 的内容）

        ==========================================
        Read data from device memory address into buffer
        Args:
            address (int): Start memory address
            buf: Destination buffer

        Returns:
            bytes: Read data (same as buf)
        """
        self.adapter.read_buf_from_mem(self.address, address, buf)
        return buf

    def _read_reg(self, reg_addr: int, bytes_count: int = 2) -> bytes:
        """
        读取寄存器
        Args:
            reg_addr (int): 寄存器地址
            bytes_count (int): 读取字节数

        Returns:
            bytes: 读取的数据

        ==========================================
        Read register
        Args:
            reg_addr (int): Register address
            bytes_count (int): Number of bytes to read

        Returns:
            bytes: Read data
        """
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def _write_reg(self, reg_addr: int, value: int, bytes_count: int = 2) -> int:
        """
        写入寄存器
        Args:
            reg_addr (int): 寄存器地址
            value (int): 要写入的值
            bytes_count (int): 写入字节数

        Returns:
            int: 写入操作的返回值（由总线适配器决定）

        ==========================================
        Write register
        Args:
            reg_addr (int): Register address
            value (int): Value to write
            bytes_count (int): Number of bytes to write

        Returns:
            int: Return value of write operation (determined by bus adapter)
        """
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def get_id(self) -> tuple:
        """
        获取芯片 ID 和版本 ID
        Returns:
            tuple: (chip_id, revision_id)

        ==========================================
        Get chip ID and revision ID
        Returns:
            tuple: (chip_id, revision_id)
        """
        buf = self._buf_2
        self._read_buf_from_mem(0x01, buf)
        # chip id, rev_id
        return buf[0], buf[1]

    def get_status(self, status_source: int = 2) -> tuple:
        """
        获取传感器状态
        Args:
            status_source (int): 状态源，0=ASIC状态，1=中断状态寄存器，2=状态寄存器

        Returns:
            tuple: 对应状态位的布尔值元组

        Raises:
            ValueError: 当 status_source 无效时

        ==========================================
        Get sensor status
        Args:
            status_source (int): Status source, 0=ASIC status, 1=interrupt status register, 2=status register

        Returns:
            tuple: Tuple of boolean values for status bits

        Raises:
            ValueError: When status_source is invalid
        """
        check_value(status_source, range(3), f"Invalid status source: {status_source}")
        if 0 == status_source:  # ASIC status
            val = self._read_reg(0x11, 1)[0]
            # i3c_err_3, i3c_err_0, hif_mode 0..3
            return 0 != (0x08 & val), 0 != (0x04 & val), 0x03 & val

        if 1 == status_source or 2 == status_source:  # Interrupt Status Register or Status register
            val = self._read_reg(0x27 if 1 == status_source else 0x28, 1)[0]
            _masks = map(lambda x: 1 << x, range(5))
            # drdy_data_reg, fifo_full, fifo_ths, oor_p, por from ISR (Interrupt status register)
            # status_core_rdy, status_nvm_rdy, status_nvm_err, status_nvm_cmd_err, status_boot_err_corrected from Status register
            return tuple([0 != (mask & val) for mask in _masks])

    def _dsp_config(self,
                    oor_sel_iir_p: [bool, None] = None,         # bit 7
                    fifo_sel_iir_p: [bool, None] = None,        # bit 6
                    shdw_sel_iir_p: [bool, None] = None,        # bit 5
                    fifo_sel_iir_t: [bool, None] = None,        # bit 4
                    shdw_sel_iir_t: [bool, None] = None,        # bit 3
                    iir_flush_forced_en: [bool, None] = None,   # bit 2
                    comp_pt_en: [int, None] = None,             # bit 1..0
                    ) -> int:
        """
        配置 DSP 寄存器（0x30）
        Args:
            oor_sel_iir_p (bool, None): OOR IIR 选择
            fifo_sel_iir_p (bool, None): FIFO IIR 压力数据选择
            shdw_sel_iir_p (bool, None): 影子寄存器 IIR 压力数据选择
            fifo_sel_iir_t (bool, None): FIFO IIR 温度数据选择
            shdw_sel_iir_t (bool, None): 影子寄存器 IIR 温度数据选择
            iir_flush_forced_en (bool, None): IIR 强制刷新使能
            comp_pt_en (int, None): 补偿使能（bit1:压力，bit0:温度）

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        ==========================================
        Configure DSP register (0x30)
        Args:
            oor_sel_iir_p (bool, None): OOR IIR selection
            fifo_sel_iir_p (bool, None): FIFO IIR pressure data selection
            shdw_sel_iir_p (bool, None): Shadow register IIR pressure data selection
            fifo_sel_iir_t (bool, None): FIFO IIR temperature data selection
            shdw_sel_iir_t (bool, None): Shadow register IIR temperature data selection
            iir_flush_forced_en (bool, None): IIR forced flush enable
            comp_pt_en (int, None): Compensation enable (bit1:pressure, bit0:temperature)

        Returns:
            int: Current register value (when all parameters are None)
        """
        val = self._read_reg(0x30)[0]
        if _all_none(oor_sel_iir_p, fifo_sel_iir_p, shdw_sel_iir_p, fifo_sel_iir_t, shdw_sel_iir_t, iir_flush_forced_en,
                     comp_pt_en):
            return val
        if oor_sel_iir_p is not None:
            val &= ~(1 << 7)  # mask
            val |= oor_sel_iir_p << 7
        if fifo_sel_iir_p is not None:
            val &= ~(1 << 6)  # mask
            val |= fifo_sel_iir_p << 6
        if shdw_sel_iir_p is not None:
            val &= ~(1 << 5)  # mask
            val |= shdw_sel_iir_p << 5
        if fifo_sel_iir_t is not None:
            val &= ~(1 << 4)  # mask
            val |= fifo_sel_iir_t << 4
        if shdw_sel_iir_t is not None:
            val &= ~(1 << 3)  # mask
            val |= shdw_sel_iir_t << 3
        if iir_flush_forced_en is not None:
            val &= ~(1 << 2)  # mask
            val |= iir_flush_forced_en << 2
        if comp_pt_en is not None:
            val &= ~0b11  # mask
            val |= comp_pt_en
        self._write_reg(0x30, val, 1)

    def _dsp_iir_config(self,
                        set_iir_p: [int, None] = None,   # bit 5..3
                        set_iir_t: [int, None] = None,   # bit 2..0
                        ) -> int:
        """
        配置 DSP IIR 滤波器系数寄存器（0x31）
        Args:
            set_iir_p (int, None): 压力 IIR 滤波器系数 (0-7)
            set_iir_t (int, None): 温度 IIR 滤波器系数 (0-7)

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        ==========================================
        Configure DSP IIR filter coefficient register (0x31)
        Args:
            set_iir_p (int, None): Pressure IIR filter coefficient (0-7)
            set_iir_t (int, None): Temperature IIR filter coefficient (0-7)

        Returns:
            int: Current register value (when all parameters are None)
        """
        val = self._read_reg(0x31)[0]
        if _all_none(set_iir_p, set_iir_t):
            return val
        if set_iir_p is not None:
            val &= ~(0b111 << 3)  # mask
            val |= set_iir_p << 3
        if set_iir_t is not None:
            val &= ~0b111  # mask
            val |= set_iir_t
        self._write_reg(0x31, val, 1)

    def set_iir_config(self, press_iir: int, temp_iir: int) -> None:
        """
        设置 IIR 滤波器系数
        Args:
            press_iir (int): 压力滤波器系数 (0-7)
            temp_iir (int): 温度滤波器系数 (0-7)

        Raises:
            ValueError: 当参数超出范围时

        Notes:
            系数 0=滤波器禁用，1=系数1，2=系数3，...，7=系数127。
            在传感器进行转换时无法写入。

        ==========================================
        Set IIR filter coefficients
        Args:
            press_iir (int): Pressure filter coefficient (0-7)
            temp_iir (int): Temperature filter coefficient (0-7)

        Raises:
            ValueError: When parameters are out of range

        Notes:
            Coefficient 0=filter off, 1=coefficient 1, 2=coefficient 3, ..., 7=coefficient 127.
            Cannot be written while sensor is converting.
        """
        check_value(press_iir, range(8), f"Invalid press_iir value: {press_iir}")
        check_value(temp_iir, range(8), f"Invalid press_iir value: {press_iir}")
        self._dsp_iir_config(press_iir, temp_iir)

    @property
    def iir_config(self) -> tuple:
        """
        获取 IIR 滤波器系数
        Returns:
            tuple: (压力系数, 温度系数)

        ==========================================
        Get IIR filter coefficients
        Returns:
            tuple: (pressure coefficient, temperature coefficient)
        """
        tmp = self._dsp_iir_config()
        return (0b0011_1000 & tmp) >> 3, 0b0000_0111 & tmp

    def _osr_config(self,
                    press_en: [bool, None] = None,   # bit 6
                    osr_p: [int, None] = None,       # bit 5..3
                    osr_t: [int, None] = None,       # bit 2..0
                    ) -> int:
        """
        配置过采样率寄存器（0x36）
        Args:
            press_en (bool, None): 压力测量使能
            osr_p (int, None): 压力过采样率 (0-7)
            osr_t (int, None): 温度过采样率 (0-7)

        Returns:
            int: 当前寄存器值（当所有参数为 None 时）

        ==========================================
        Configure oversampling register (0x36)
        Args:
            press_en (bool, None): Pressure measurement enable
            osr_p (int, None): Pressure oversampling (0-7)
            osr_t (int, None): Temperature oversampling (0-7)

        Returns:
            int: Current register value (when all parameters are None)
        """
        val = self._read_reg(0x36)[0]
        if _all_none(press_en, osr_p, osr_t):
            return val
        if press_en is not None:
            val &= ~(1 << 6)  # mask
            val |= press_en << 6
        if osr_p is not None:
            val &= ~(0b111 << 3)  # mask
            val |= osr_p << 3
        if osr_t is not None:
            val &= ~0b111  # mask
            val |= osr_t
        self._write_reg(0x36, val, 1)

    def _eff_osr_config(self) -> tuple:
        """
        读取有效过采样率配置（只读）
        Returns:
            tuple: (osr_t_eff, osr_p_eff, odr_is_valid)

        ==========================================
        Read effective oversampling configuration (read-only)
        Returns:
            tuple: (osr_t_eff, osr_p_eff, odr_is_valid)
        """
        val = self._read_reg(0x38)[0]
        #       osr_t_eff,      osr_p_eff,              odr_is_valid
        return 0b0111 & val, (0b0011_1000 & val) >> 3, 0 != (0b1000_0000 & val)

    @property
    def effective_osr_rating(self) -> tuple:
        """
        获取有效过采样率和 ODR 有效性标志（只读）
        Returns:
            tuple: (温度过采样有效值, 压力过采样有效值, ODR是否有效)

        ==========================================
        Get effective oversampling and ODR validity flag (read-only)
        Returns:
            tuple: (effective temperature oversampling, effective pressure oversampling, ODR valid)
        """
        return self._eff_osr_config()

    @micropython.native
    def _get_pressure_raw(self) -> int:
        """
        读取原始压力数据（24位）
        Returns:
            int: 原始压力值

        ==========================================
        Read raw pressure data (24-bit)
        Returns:
            int: Raw pressure value
        """
        buf = self._buf_3
        l, m, h = self._read_buf_from_mem(0x20, buf)
        return (h << 16) | (m << 8) | l

    def get_pressure(self) -> float:
        """
        获取压力值（帕斯卡）
        Returns:
            float: 压力值，单位 Pa

        ==========================================
        Get pressure value (Pascal)
        Returns:
            float: Pressure in Pa
        """
        return _kP * self._get_pressure_raw()

    @micropython.native
    def _get_temperature_raw(self) -> int:
        """
        读取原始温度数据（24位有符号）
        Returns:
            int: 原始温度值

        ==========================================
        Read raw temperature data (24-bit signed)
        Returns:
            int: Raw temperature value
        """
        buf = self._buf_3
        # signed 24 bit value
        l, m, h = self._read_buf_from_mem(0x1D, buf)
        return (h << 16) | (m << 8) | l

    def get_temperature(self) -> float:
        """
        获取温度值（摄氏度）
        Returns:
            float: 温度值，单位 ℃

        ==========================================
        Get temperature value (Celsius)
        Returns:
            float: Temperature in ℃
        """
        return _kT * self._get_temperature_raw()

    def soft_reset(self) -> None:
        """
        软件复位传感器
        ==========================================
        Software reset the sensor
        """
        self._write_reg(0x7E, 0xB6, 1)

    def start_measurement(self, mode: int = 1, output_data_rate: int = 10) -> bool:
        """
        启动测量
        Args:
            mode (int): 工作模式：0=待机，1=正常，2=强制单次，3=连续
            output_data_rate (int): 输出数据率（0-31）

        Returns:
            bool: odr_is_valid 标志，True 表示 ODR 与 OSR 配置兼容

        Raises:
            ValueError: 当 mode 无效时

        Notes:
            正常模式按 ODR 周期测量，强制模式仅测量一次，连续模式以最大速率测量。

        ==========================================
        Start measurement
        Args:
            mode (int): Operating mode: 0=standby, 1=normal, 2=forced single, 3=continuous
            output_data_rate (int): Output data rate (0-31)

        Returns:
            bool: odr_is_valid flag, True if ODR compatible with OSR configuration

        Raises:
            ValueError: When mode is invalid

        Notes:
            Normal mode measures at ODR period, forced mode measures once, continuous mode measures at max rate.
        """
        if mode not in range(4):
            raise ValueError(f"Invalid mode value: {mode}")
        _osr_t = self.temp_oversampling
        _osr_p = self.pressure_oversampling
        press_enable = not self.temperature_only
        self._osr_config(press_enable, _osr_p, _osr_t)
        self._odr_config(True, output_data_rate, mode)
        self._mode = mode
        # Update class fields to allow more accurate conversion time calculation
        self._osr_t, self._osr_p, odr_is_valid = self._eff_osr_config()
        # Return odr_is_valid field of OSR_EFF register
        return odr_is_valid

    def _get_power_mode_or_odr(self, odr: bool = False) -> int:
        """
        获取电源模式或输出数据率
        Args:
            odr (bool): True 返回 ODR，False 返回电源模式

        Returns:
            int: 电源模式或 ODR 值

        ==========================================
        Get power mode or output data rate
        Args:
            odr (bool): True to return ODR, False to return power mode

        Returns:
            int: Power mode or ODR value
        """
        tmp = self._odr_config()
        if odr:
            return (0b0111_1100 & tmp) >> 2
        return 0b0000_0011 & tmp

    @property
    def output_data_rate(self) -> int:
        """
        获取当前输出数据率
        Returns:
            int: ODR 值（0-31）

        ==========================================
        Get current output data rate
        Returns:
            int: ODR value (0-31)
        """
        return self._get_power_mode_or_odr(True)

    def get_oversampling(self) -> tuple:
        """
        获取过采样率配置
        Returns:
            tuple: (压力过采样率, 温度过采样率)

        ==========================================
        Get oversampling configuration
        Returns:
            tuple: (pressure oversampling, temperature oversampling)
        """
        tmp = self._osr_config()
        return (tmp & 0b0011_1000) >> 3, tmp & 0b0000_0111

    @property
    def oversampling(self) -> tuple:
        """
        过采样率属性，返回 (压力过采样, 温度过采样)
        ==========================================
        Oversampling property, returns (pressure oversampling, temperature oversampling)
        """
        return self.get_oversampling()

    def is_data_ready(self) -> bool:
        """
        检查数据是否就绪
        Returns:
            bool: True 表示有新的温度或压力数据可读

        ==========================================
        Check if data is ready
        Returns:
            bool: True if new temperature or pressure data is available
        """
        tmp = self.get_status(1)
        # print(f"DBG:is_data_ready: {tmp}")
        return tmp[0]

    @micropython.native
    def get_conversion_cycle_time(self) -> float:
        """
        获取转换周期时间（微秒）
        Returns:
            float: 转换时间（微秒）

        ==========================================
        Get conversion cycle time (microseconds)
        Returns:
            float: Conversion time in microseconds
        """
        return _get_conv_time_ms(self.temperature_only, self.temp_oversampling, self.pressure_oversampling)

    # Iterator
    def __next__(self) -> [tuple, float, None]:
        """
        迭代器接口，返回最新测量数据
        Returns:
            tuple, float, None: 如果仅温度模式则返回温度值，否则返回 (压力, 温度) 元组，
                                若无新数据则返回 None

        ==========================================
        Iterator interface, return latest measurement data
        Returns:
            tuple, float, None: If temperature-only mode returns temperature value,
                                otherwise returns (pressure, temperature) tuple,
                                returns None if no new data
        """
        if not self.is_data_ready():
            return None  # No data!
        temperature = self.get_temperature()
        if self.temperature_only:
            return temperature
        return self.get_pressure(), temperature

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================