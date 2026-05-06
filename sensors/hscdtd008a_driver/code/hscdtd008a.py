# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/01/20 10:00
# @Author  : goctaprog@gmail.com
# @File    : hscdtd008a.py
# @Description : HSCDTD008A 三轴地磁传感器驱动（AlpsAlpine）
# @License : MIT

__version__ = "1.0.0"
__author__ = "goctaprog@gmail.com"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
from sensor_pack import bus_service, geosensmod
from sensor_pack.base_sensor import check_value, Iterator, TemperatureSensor
import array
import time
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class HSCDTD008A(geosensmod.GeoMagneticSensor, Iterator, TemperatureSensor):
    """
    HSCDTD008A 三轴地磁传感器驱动类（AlpsAlpine）
    Attributes:
        adapter (bus_service.BusAdapter): 总线适配器实例
        _mag_field_comp (array): 磁场分量缓冲区 [X, Y, Z]
        _mag_field_offs (array): 磁场偏移缓冲区 [X, Y, Z]
        _use_offset (bool): 是否将偏移量叠加到输出数据
    Methods:
        start_measure(): 启动单次或周期性测量
        get_axis(): 读取指定轴或全部轴磁场分量
        get_temperature(): 读取传感器温度
        get_status(): 读取状态寄存器
        get_id(): 读取设备 ID（应为 0x49）
        perform_self_test(): 执行自检
        soft_reset(): 软件复位
        calibrate_offsets(): 校准偏移量
        set_offset_drift_values(): 写入偏移量寄存器
        enable_temp_meas(): 启用温度测量
        deinit(): 释放资源，进入待机模式
    Notes:
        - I2C 地址固定为 0x0C
        - 依赖外部传入 BusAdapter 实例，不在内部创建总线
        - 待机模式下可访问寄存器
    ==========================================
    HSCDTD008A three-axis geomagnetic sensor driver (AlpsAlpine).
    Attributes:
        adapter (bus_service.BusAdapter): Bus adapter instance
        _mag_field_comp (array): Magnetic field component buffer [X, Y, Z]
        _mag_field_offs (array): Magnetic field offset buffer [X, Y, Z]
        _use_offset (bool): Whether to add offset to output data
    Methods:
        start_measure(): Start single or periodic measurement
        get_axis(): Read specified or all axis magnetic field components
        get_temperature(): Read sensor temperature
        get_status(): Read status register
        get_id(): Read device ID (should be 0x49)
        perform_self_test(): Perform self-test
        soft_reset(): Software reset
        calibrate_offsets(): Calibrate offset values
        set_offset_drift_values(): Write offset registers
        enable_temp_meas(): Enable temperature measurement
        deinit(): Release resources, enter standby mode
    Notes:
        - I2C address is fixed at 0x0C
        - Requires externally provided BusAdapter instance
        - Registers are accessible in standby mode
    """

    # 默认 I2C 地址（固定，不可更改）
    I2C_DEFAULT_ADDR = micropython.const(0x0C)

    # 输出数据速率选项：0=0.5Hz, 1=10Hz, 2=20Hz, 3=100Hz
    ODR_0_5HZ = micropython.const(0)
    ODR_10HZ  = micropython.const(1)
    ODR_20HZ  = micropython.const(2)
    ODR_100HZ = micropython.const(3)

    # 寄存器地址
    _REG_STB   = micropython.const(0x0C)
    _REG_ID    = micropython.const(0x0F)
    _REG_OUT_X = micropython.const(0x10)
    _REG_STAT  = micropython.const(0x18)
    _REG_OFF_X = micropython.const(0x20)
    _REG_CTRL1 = micropython.const(0x1B)
    _REG_CTRL2 = micropython.const(0x1C)
    _REG_CTRL3 = micropython.const(0x1D)
    _REG_CTRL4 = micropython.const(0x1E)
    _REG_TEMP  = micropython.const(0x31)

    def __init__(self, adapter: bus_service.BusAdapter, debug: bool = False) -> None:
        """
        初始化 HSCDTD008A 传感器驱动
        Args:
            adapter (bus_service.BusAdapter): 总线适配器实例
            debug (bool): 是否启用调试输出，默认 False
        Returns:
            None
        Raises:
            ValueError: adapter 为 None 或不具备所需接口
        Notes:
            - ISR-safe: 否
            - 初始化时自动读取偏移量寄存器
        ==========================================
        Initialize HSCDTD008A sensor driver.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter instance
            debug (bool): Enable debug output, default False
        Returns:
            None
        Raises:
            ValueError: adapter is None or missing required interface
        Notes:
            - ISR-safe: No
            - Offset registers are read automatically on init
        """
        if adapter is None:
            raise ValueError("adapter must not be None")
        if not hasattr(adapter, "read_buf_from_mem"):
            raise ValueError("adapter must be a BusAdapter instance")
        super().__init__(adapter=adapter, address=self.I2C_DEFAULT_ADDR, big_byte_order=False)
        self._debug = debug
        # 磁场分量缓冲区（有符号 16 位，X/Y/Z）
        self._mag_field_comp = array.array("h", [0, 0, 0])
        # 偏移量缓冲区（有符号 16 位，X/Y/Z）
        self._mag_field_offs = array.array("h", [0, 0, 0])
        # 2 字节读缓冲区（单轴读取复用）
        self._buf_2 = bytearray(2)
        # 6 字节读缓冲区（三轴批量读取复用）
        self._buf_6 = bytearray(6)
        # 是否将偏移量叠加到输出
        self._use_offset = False
        # 初始化时读取偏移量寄存器
        self._read_offset()

    def _log(self, msg: str) -> None:
        if self._debug:
            print("[HSCDTD008A] %s" % msg)

    def read_buf_from_mem(self, mem_addr: int, buf: bytearray) -> None:
        """
        从设备指定地址读取数据到缓冲区
        Args:
            mem_addr (int): 设备内存地址
            buf (bytearray): 目标缓冲区，长度决定读取字节数
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read data from device memory address into buffer.
        Args:
            mem_addr (int): Device memory address
            buf (bytearray): Target buffer; length determines bytes read
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self.adapter.read_buf_from_mem(self.address, mem_addr, buf)

    @staticmethod
    def _copy(destination, source) -> None:
        for i, item in enumerate(source):
            destination[i] = item

    def _read_reg(self, reg_addr: int, bytes_count: int = 1) -> bytes:
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def _write_reg(self, reg_addr: int, value: int, bytes_count: int = 1) -> None:
        bo = self._get_byteorder_as_str()[0]
        self.adapter.write_register(self.address, reg_addr, value, bytes_count, bo)

    def _read_ctrl1(self) -> int:
        # 读取控制寄存器 1（CTRL1）
        return self._read_reg(self._REG_CTRL1)[0]

    def _read_field(self, offset: bool = False) -> None:
        # 根据 offset 标志选择读取磁场输出或偏移量寄存器
        source_addr = self._REG_OUT_X
        destination = self._mag_field_comp
        if offset:
            source_addr = self._REG_OFF_X
            destination = self._mag_field_offs
        b_val = self._buf_6
        self.read_buf_from_mem(source_addr, b_val)
        # 解包三个有符号 16 位整数（小端）
        self._copy(destination, self.unpack(fmt_char="hhh", source=b_val))

    def _read_offset(self) -> None:
        # 从传感器读取偏移量并存入 _mag_field_offs
        self._read_field(offset=True)

    @property
    def use_offset(self) -> bool:
        """
        是否将偏移量叠加到输出数据
        Returns:
            bool: True 表示叠加 OFFX/OFFY/OFFZ
        ==========================================
        Whether to add offset drift values to output data.
        Returns:
            bool: True means OFFX/OFFY/OFFZ are added to output
        """
        return self._use_offset

    @use_offset.setter
    def use_offset(self, value: bool) -> None:
        self._use_offset = value

    def get_conversion_cycle_time(self) -> int:
        """
        返回信号转换时间（毫秒）
        Args:
            无
        Returns:
            int: 转换时间，固定为 5 ms
        Notes:
            - ISR-safe: 是
            - 注意：此值为转换时间，非 update_rate
        ==========================================
        Return signal conversion time in milliseconds.
        Args:
            None
        Returns:
            int: Conversion time, fixed at 5 ms
        Notes:
            - ISR-safe: Yes
            - Note: this is conversion time, not update_rate
        """
        return 5

    def read_raw(self, axis: int) -> int:
        """
        读取指定轴的原始磁场值
        Args:
            axis (int): 轴编号，0=X, 1=Y, 2=Z
        Returns:
            int: 有符号 16 位原始值；若 use_offset 为 True，叠加偏移量
        Raises:
            ValueError: axis 不在 0~2 范围内
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw magnetic field value for specified axis.
        Args:
            axis (int): Axis index, 0=X, 1=Y, 2=Z
        Returns:
            int: Signed 16-bit raw value; offset added if use_offset is True
        Raises:
            ValueError: axis not in range 0~2
        Notes:
            - ISR-safe: No
        """
        check_value(axis, range(3), "Invalid axis value: %d" % axis)
        b_val = self._buf_2
        # 每轴寄存器间隔 2 字节
        self.read_buf_from_mem(self._REG_OUT_X + 2 * axis, b_val)
        # 解包有符号 16 位整数
        ret_val = self.unpack(fmt_char="h", source=b_val)[0]
        if self._use_offset:
            ret_val += self.offset_drift_values[axis]
        return ret_val

    def _get_all_meas_result(self) -> tuple:
        b_val = self._buf_6
        # 批量读取 X/Y/Z 三轴，共 6 字节
        self.read_buf_from_mem(self._REG_OUT_X, b_val)
        return self.unpack(fmt_char="hhh", source=b_val)

    def get_temperature(self) -> int:
        """
        读取传感器温度
        Args:
            无
        Returns:
            int: 传感器封装温度（有符号，单位℃）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 需先调用 enable_temp_meas(True) 启用温度测量
        ==========================================
        Read sensor package temperature.
        Args:
            None
        Returns:
            int: Signed temperature in Celsius
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Call enable_temp_meas(True) first to enable temperature measurement
        """
        b_val = self._read_reg(self._REG_TEMP)
        # 解包有符号 8 位整数
        return self.unpack("b", b_val)[0]

    def get_id(self) -> int:
        """
        读取设备 ID
        Args:
            无
        Returns:
            int: 设备 ID，正常应为 0x49
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read device ID.
        Args:
            None
        Returns:
            int: Device ID, should be 0x49
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._read_reg(self._REG_ID)[0]

    def get_status(self) -> tuple:
        """
        读取状态寄存器
        Args:
            无
        Returns:
            tuple: (drdy, dor, ffu, trdy)
                drdy (bool): 数据就绪（bit6）
                dor  (bool): 数据溢出（bit5）
                ffu  (bool): FIFO 满（bit2）
                trdy (bool): 温度数据就绪（bit1）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read status register.
        Args:
            None
        Returns:
            tuple: (drdy, dor, ffu, trdy)
                drdy (bool): Data ready (bit6)
                dor  (bool): Data overrun (bit5)
                ffu  (bool): FIFO full (bit2)
                trdy (bool): Temperature ready (bit1)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        stat = self._read_reg(self._REG_STAT)[0]
        # 解析各状态位
        drdy = bool(stat & 0b0100_0000)
        dor  = bool(stat & 0b0010_0000)
        ffu  = bool(stat & 0b0000_0100)
        trdy = bool(stat & 0b0000_0010)
        return drdy, dor, ffu, trdy

    def _control_1(
            self,
            active_power_mode: bool = True,
            output_data_rate: int = 1,
            force_state: bool = True,
    ) -> None:
        """
        写入控制寄存器 1（CTRL1）
        Args:
            active_power_mode (bool): True=激活模式，False=待机模式（bit7）
            output_data_rate (int): 输出数据速率 0~3（bit4:3）
            force_state (bool): True=单次测量模式（bit1）
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：修改传感器工作模式
        ==========================================
        Write Control Register 1 (CTRL1).
        Args:
            active_power_mode (bool): True=active, False=standby (bit7)
            output_data_rate (int): Output data rate 0~3 (bit4:3)
            force_state (bool): True=single measurement mode (bit1)
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: modifies sensor operating mode
        """
        val = self._read_ctrl1()
        # 设置激活/待机模式位（bit7）
        val &= ~(1 << 7)
        val |= int(active_power_mode) << 7
        # 设置输出数据速率位（bit4:3）
        val &= ~(0b11 << 3)
        val |= (output_data_rate & 0b11) << 3
        # 设置单次/周期测量模式位（bit1）
        val &= ~(1 << 1)
        val |= int(force_state) << 1
        self._write_reg(self._REG_CTRL1, val, 1)

    def _control_2(
            self,
            fco: bool = False,
            aor: bool = False,
            fifo_enable: bool = False,
            den: bool = False,
            data_ready_lvl_ctrl: bool = True,
    ) -> None:
        """
        写入控制寄存器 2（CTRL2）
        Args:
            fco (bool): FIFO 数据存储方式，False=直接，True=比较（bit6）
            aor (bool): FIFO 比较方式，False=OR，True=AND（bit5）
            fifo_enable (bool): FIFO 使能（bit4）
            den (bool): 数据就绪功能使能（bit3）
            data_ready_lvl_ctrl (bool): DRDY 有效电平，False=低，True=高（bit2）
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 测量期间修改 CTRL2 将在本次测量结束后生效
        ==========================================
        Write Control Register 2 (CTRL2).
        Args:
            fco (bool): FIFO storage method, False=Direct, True=Comparison (bit6)
            aor (bool): FIFO comparison method, False=OR, True=AND (bit5)
            fifo_enable (bool): FIFO enable (bit4)
            den (bool): Data ready function enable (bit3)
            data_ready_lvl_ctrl (bool): DRDY active level, False=LOW, True=HIGH (bit2)
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Changes take effect after current measurement completes
        """
        val = self._read_reg(self._REG_CTRL2)[0]
        # 设置各控制位
        val &= ~(1 << 6)
        val |= int(fco) << 6
        val &= ~(1 << 5)
        val |= int(aor) << 5
        val &= ~(1 << 4)
        val |= int(fifo_enable) << 4
        val &= ~(1 << 3)
        val |= int(den) << 3
        val &= ~(1 << 2)
        val |= int(data_ready_lvl_ctrl) << 2
        self._write_reg(self._REG_CTRL2, val, 1)

    def _control_3(
            self,
            soft_reset: bool = False,
            force_state: bool = False,
            self_test: bool = False,
            temp_measure: bool = False,
            calibrate_offset: bool = False,
    ) -> None:
        """
        写入控制寄存器 3（CTRL3）
        Args:
            soft_reset (bool): 软件复位（bit7）
            force_state (bool): 启动单次测量（bit6）
            self_test (bool): 自检使能（bit4）
            temp_measure (bool): 启动温度测量（bit1）
            calibrate_offset (bool): 启动偏移校准（bit0）
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 禁止同时设置多个控制位；优先级从 MSB 到 LSB
        ==========================================
        Write Control Register 3 (CTRL3).
        Args:
            soft_reset (bool): Software reset (bit7)
            force_state (bool): Start single measurement (bit6)
            self_test (bool): Self-test enable (bit4)
            temp_measure (bool): Start temperature measurement (bit1)
            calibrate_offset (bool): Start offset calibration (bit0)
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Setting multiple bits simultaneously is prohibited; priority is MSB first
        """
        val = self._read_reg(self._REG_CTRL3)[0]
        # 依次设置各控制位
        val &= ~(1 << 7)
        val |= int(soft_reset) << 7
        val &= ~(1 << 6)
        val |= int(force_state) << 6
        val &= ~(1 << 4)
        val |= int(self_test) << 4
        val &= ~(1 << 1)
        val |= int(temp_measure) << 1
        # 设置偏移校准位（bit0）
        val &= 0xFE
        val |= int(calibrate_offset)
        self._write_reg(self._REG_CTRL3, val, 1)

    def _control_4(self, hi_dynamic_range: bool = False) -> None:
        """
        写入控制寄存器 4（CTRL4）
        Args:
            hi_dynamic_range (bool): False=14位（默认），True=15位动态范围（bit4）
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 测量期间修改将在本次测量结束后生效
        ==========================================
        Write Control Register 4 (CTRL4).
        Args:
            hi_dynamic_range (bool): False=14-bit (default), True=15-bit range (bit4)
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Changes take effect after current measurement completes
        """
        # bit7 固定为 1（保留位要求）
        val = 0x80 | (int(hi_dynamic_range) << 4)
        self._write_reg(self._REG_CTRL4, val, 1)

    def perform_self_test(self) -> bool:
        """
        执行传感器自检
        Args:
            无
        Returns:
            bool: True=自检通过，False=自检失败
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 必须在激活模式（active_power_mode=True）下调用，待机模式下禁止执行
        ==========================================
        Perform sensor self-test.
        Args:
            None
        Returns:
            bool: True=passed, False=failed
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Must be called in active power mode; do NOT call in standby mode
        """
        # 读取 STB 寄存器，初始值应为 0x55
        val = self._read_reg(self._REG_STB)[0]
        if 0x55 != val:
            return False
        # 触发自检，STB 应变为 0xAA
        self._control_3(self_test=True)
        val = self._read_reg(self._REG_STB)[0]
        if 0xAA != val:
            return False
        # 自检完成后 STB 应恢复为 0x55
        return 0x55 == self._read_reg(self._REG_STB)[0]

    def soft_reset(self) -> None:
        """
        执行软件复位
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：复位所有寄存器至默认值
        ==========================================
        Perform software reset.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: resets all registers to default values
        """
        self._control_3(soft_reset=True)

    def is_continuous_meas_mode(self) -> bool:
        """
        判断是否处于周期测量模式
        Args:
            无
        Returns:
            bool: True=周期测量模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if sensor is in continuous measurement mode.
        Args:
            None
        Returns:
            bool: True=continuous measurement mode
        Notes:
            - ISR-safe: No
        """
        return not self.is_single_meas_mode()

    def is_single_meas_mode(self) -> bool:
        """
        判断是否处于单次测量模式
        Args:
            无
        Returns:
            bool: True=单次测量模式（Force State）
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if sensor is in single measurement (force state) mode.
        Args:
            None
        Returns:
            bool: True=single measurement mode
        Notes:
            - ISR-safe: No
        """
        # 检查 CTRL1 的 FS 位（bit1）
        tmp = 0x02 & self._read_ctrl1()
        return 0 != tmp

    def in_standby_mode(self) -> bool:
        """
        判断传感器是否处于待机模式
        Args:
            无
        Returns:
            bool: True=待机模式，False=激活模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if sensor is in standby mode.
        Args:
            None
        Returns:
            bool: True=standby mode, False=active mode
        Notes:
            - ISR-safe: No
        """
        # 检查 CTRL1 的 PC 位（bit7）
        tmp = 0x80 & self._read_ctrl1()
        return 0 == tmp

    def set_dynamic_range(self, hi: bool) -> None:
        """
        设置输出数据动态范围
        Args:
            hi (bool): True=15位（-16384~+16383），False=14位（-8192~+8191）
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Set output data dynamic range.
        Args:
            hi (bool): True=15-bit (-16384~+16383), False=14-bit (-8192~+8191)
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        self._control_4(hi)

    def get_dynamic_range(self) -> bool:
        """
        读取当前动态范围设置
        Args:
            无
        Returns:
            bool: True=15位，False=14位
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current dynamic range setting.
        Args:
            None
        Returns:
            bool: True=15-bit, False=14-bit
        Notes:
            - ISR-safe: No
        """
        ctrl4 = self._read_reg(self._REG_CTRL4)[0]
        return 0 != (ctrl4 & 0b0001_0000)

    @property
    def hi_dynamic_range(self) -> bool:
        """动态范围属性，True=15位，False=14位"""
        return self.get_dynamic_range()

    @hi_dynamic_range.setter
    def hi_dynamic_range(self, value: bool) -> None:
        self.set_dynamic_range(value)

    def start_measure(self, continuous_mode: bool = True, update_rate: int = 1, active_pwr_mode: bool = True) -> None:
        """
        启动测量
        Args:
            continuous_mode (bool): True=周期测量，False=单次测量（需每次调用）
            update_rate (int): 周期测量频率 0~3（0=0.5Hz, 1=10Hz, 2=20Hz, 3=100Hz）
            active_pwr_mode (bool): True=激活模式，False=待机模式
        Returns:
            None
        Raises:
            ValueError: update_rate 不在 0~3 范围内
        Notes:
            - ISR-safe: 否
            - 副作用：修改传感器工作模式和测量频率
            - update_rate 是数据更新频率，非转换时间（5ms）
        ==========================================
        Start measurement.
        Args:
            continuous_mode (bool): True=periodic, False=single shot (call each time)
            update_rate (int): Periodic measurement rate 0~3 (0=0.5Hz,1=10Hz,2=20Hz,3=100Hz)
            active_pwr_mode (bool): True=active mode, False=standby mode
        Returns:
            None
        Raises:
            ValueError: update_rate not in range 0~3
        Notes:
            - ISR-safe: No
            - Side effect: modifies sensor operating mode and measurement rate
            - update_rate is data update frequency, not conversion time (5ms)
        """
        check_value(update_rate, range(4), "Invalid update rate value: %d" % update_rate)
        # 配置 CTRL1：激活模式、数据速率、单次/周期模式
        self._control_1(active_pwr_mode, update_rate, not continuous_mode)
        if not continuous_mode:
            # 单次测量模式：触发一次测量
            self._control_3(force_state=True)

    def enable_temp_meas(self, enable: bool = True) -> None:
        """
        启用或禁用温度测量
        Args:
            enable (bool): True=启用，False=禁用
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 仅在激活模式下有效
        ==========================================
        Enable or disable temperature measurement.
        Args:
            enable (bool): True=enable, False=disable
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Only effective in active power mode
        """
        self._control_3(temp_measure=enable)

    @property
    def offset_drift_values(self) -> tuple:
        """
        偏移量漂移值（OFFX, OFFY, OFFZ）
        Returns:
            tuple: (offs_x, offs_y, offs_z) 三个有符号整数
        Notes:
            - ISR-safe: 是
        ==========================================
        Offset drift values (OFFX, OFFY, OFFZ).
        Returns:
            tuple: (offs_x, offs_y, offs_z) three signed integers
        Notes:
            - ISR-safe: Yes
        """
        return self._mag_field_offs[0], self._mag_field_offs[1], self._mag_field_offs[2]

    def set_offset_drift_values(self, offs_x: int = 0, offs_y: int = 0, offs_z: int = 0) -> None:
        """
        写入偏移量到传感器寄存器
        Args:
            offs_x (int): X 轴偏移量，范围 -8192~+8191
            offs_y (int): Y 轴偏移量，范围 -8192~+8191
            offs_z (int): Z 轴偏移量，范围 -8192~+8191
        Returns:
            None
        Raises:
            ValueError: 任意偏移量超出 -8192~+8191 范围
        Notes:
            - ISR-safe: 否
            - 副作用：修改传感器偏移量寄存器（0x20~0x25）
        ==========================================
        Write offset drift values to sensor registers.
        Args:
            offs_x (int): X-axis offset, range -8192~+8191
            offs_y (int): Y-axis offset, range -8192~+8191
            offs_z (int): Z-axis offset, range -8192~+8191
        Returns:
            None
        Raises:
            ValueError: Any offset value out of range -8192~+8191
        Notes:
            - ISR-safe: No
            - Side effect: modifies sensor offset registers (0x20~0x25)
        """
        t = (offs_x, offs_y, offs_z)
        ba = bytearray(6)
        for index, value in enumerate(t):
            check_value(value, range(-8192, 8192), "Invalid offset value: %d" % value)
            # 小端格式写入 2 字节有符号整数
            b = value.to_bytes(2, "little", True)
            ba[2 * index]     = b[0]
            ba[2 * index + 1] = b[1]
        # 从地址 0x20 开始批量写入 6 字节偏移量
        self.adapter.write_register(self.address, self._REG_OFF_X, ba, 0, "")

    def calibrate_offsets(self) -> None:
        """
        执行偏移量自动校准
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 仅在单次测量模式（Force State）下调用
            - 副作用：阻塞直到校准完成，更新 _mag_field_offs
        ==========================================
        Perform automatic offset calibration.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Call only in single measurement (Force State) mode
            - Side effect: blocks until calibration completes, updates _mag_field_offs
        """
        # 触发偏移校准
        self._control_3(calibrate_offset=True)
        # 轮询 CTRL3 的 OCL 位（bit0），等待校准完成
        while True:
            val = 0x01 & self._read_reg(self._REG_CTRL3)[0]
            if not val:
                break
            time.sleep_ms(10)
        # 校准完成后读取新偏移量到缓冲区
        self._read_field(offset=True)

    def __iter__(self):
        return self

    def __next__(self):
        """
        迭代器接口，仅在周期测量模式下返回数据
        Returns:
            tuple: (x, y, z) 三轴磁场原始值
        Notes:
            - ISR-safe: 否
            - 仅在 continuous_mode=True 时有效
        ==========================================
        Iterator interface, returns data only in continuous measurement mode.
        Returns:
            tuple: (x, y, z) raw magnetic field values
        Notes:
            - ISR-safe: No
            - Only valid when continuous_mode=True
        """
        if self.is_continuous_meas_mode():
            return self.get_axis(-1)

    def deinit(self) -> None:
        """
        释放资源，进入待机模式
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：传感器进入低功耗待机状态
        ==========================================
        Release resources and enter standby mode.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: sensor enters low-power standby state
        """
        self.start_measure(active_pwr_mode=False)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
