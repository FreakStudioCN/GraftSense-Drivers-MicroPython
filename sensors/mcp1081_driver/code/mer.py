# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21
# @Author  : hogeiha
# @File    : mer.py
# @Description : MER-MCP1081-260-26 electronic water-level sensor Modbus RTU driver
# @License : MIT

__version__ = "2.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const

# ======================================== 全局变量 ============================================

_UINT16_MAX = const(0xFFFF)
_MODBUS_MAX_READ_REGISTERS = const(125)
_ADDRESS_CHANGE_SLAVE = const(0xFE)

# ======================================== 功能函数 ============================================


def uint16_to_int16(value: int) -> int:
    """将无符号16位数转换为有符号数。Convert uint16 to int16."""
    if not isinstance(value, int):
        raise ValueError("value must be int")
    if value < 0 or value > _UINT16_MAX:
        raise ValueError("value must be in range 0..65535")
    return value - 0x10000 if value & 0x8000 else value


# ======================================== 自定义类 ============================================


class MER:
    """
    MER-MCP1081-260-26电子水尺Modbus RTU驱动。

    Attributes:
        _host (object): 已初始化的umodbus主站。
        _slave_addr (int): Modbus节点地址。
    Methods:
        read_measurements(): 读取实时测量数据。
        read_device_uid(): 读取96位UID。
        deinit(): 释放驱动持有的引用。
    Notes:
        总线由调用方创建和释放；所有通信方法均非ISR-safe。

    ==========================================
    MER-MCP1081-260-26 water-level sensor Modbus RTU driver.

    Attributes:
        _host (object): Initialized umodbus master.
        _slave_addr (int): Modbus node address.
    Methods:
        read_measurements(): Read real-time measurements.
        read_device_uid(): Read the 96-bit UID.
        deinit(): Release references owned by the driver.
    Notes:
        The caller owns the bus; all communication methods are not ISR-safe.
    """

    DEFAULT_SLAVE_ADDR = const(1)
    DEFAULT_WAKE_DELAY_MS = const(35)
    DEFAULT_RETRIES = const(3)
    DEFAULT_RETRY_DELAY_MS = const(50)
    MAX_LEVEL_MM = const(260)

    REG_CALIBRATION = const(0x0000)
    REG_NODE_ADDRESS = const(0x0001)
    REG_LEVEL = const(0x0002)
    REG_TEMPERATURE = const(0x0003)
    REG_LOW_ALARM = const(0x0004)
    REG_OVERFLOW_ALARM = const(0x0005)
    REG_SF = const(0x0006)
    REG_CAP_SUM = const(0x0007)
    REG_FILTER_WINDOW = const(0x0010)
    REG_FIT_MODE = const(0x0011)
    REG_LOW_ALARM_LEVEL = const(0x0012)
    REG_OVERFLOW_ALARM_LEVEL = const(0x0013)
    REG_CAP1 = const(0x0014)
    REG_CAP2 = const(0x0015)
    REG_CAP3 = const(0x0016)
    REG_SF1 = const(0x001D)
    REG_LEVEL1 = const(0x001E)
    REG_FULL_LEVEL = const(0x0027)
    REG_HW_VERSION = const(0x0028)
    REG_HW_MINOR_VERSION = const(0x0029)
    REG_FW_VERSION = const(0x002A)
    REG_UID = const(0x002B)

    __slots__ = ("_host", "_slave_addr", "_wake_delay_ms", "_retries", "_retry_delay_ms")

    def __init__(
        self,
        host: object,
        slave_addr: int = DEFAULT_SLAVE_ADDR,
        wake_delay_ms: int = DEFAULT_WAKE_DELAY_MS,
        retries: int = DEFAULT_RETRIES,
        retry_delay_ms: int = DEFAULT_RETRY_DELAY_MS,
    ) -> None:
        """
        初始化驱动。Initialize the driver.

        Args:
            host (object): 提供寄存器读写和_uart.write的umodbus主站。
            slave_addr (int): 节点地址，范围1~252。
            wake_delay_ms (int): 唤醒等待时间，不小于30ms。
            retries (int): 每次读取的最大尝试次数，范围1~10。
            retry_delay_ms (int): 失败后的重试间隔，范围0~1000ms。
        Returns:
            None
        Raises:
            ValueError: 参数无效。
        Notes:
            不创建或接管总线；非ISR-safe。
        """
        if host is None:
            raise ValueError("host cannot be None")
        if not hasattr(host, "read_holding_registers") or not hasattr(host, "write_single_register"):
            raise ValueError("host must provide Modbus register methods")
        if not hasattr(host, "_uart") or not hasattr(host._uart, "write"):
            raise ValueError("host must provide a writable UART")
        self._validate_int_range("slave_addr", slave_addr, 1, 252)
        self._validate_int_range("wake_delay_ms", wake_delay_ms, 30, 1000)
        self._validate_int_range("retries", retries, 1, 10)
        self._validate_int_range("retry_delay_ms", retry_delay_ms, 0, 1000)
        self._host = host
        self._slave_addr = slave_addr
        self._wake_delay_ms = wake_delay_ms
        self._retries = retries
        self._retry_delay_ms = retry_delay_ms

    @property
    def slave_addr(self) -> int:
        """返回当前节点地址。Return the current node address."""
        return self._slave_addr

    def wake_up(self) -> None:
        """发送唤醒字节并等待。Send the wake byte and wait; not ISR-safe."""
        self._require_active()
        try:
            self._host._uart.write(b"\x8f")
        except OSError as error:
            raise RuntimeError("Sensor wake-up failed") from error
        time.sleep_ms(self._wake_delay_ms)

    def read_registers(self, address: int, count: int = 1) -> tuple:
        """
        读取保持寄存器。Read holding registers.

        Args:
            address (int): 起始地址。
            count (int): 寄存器数量。
        Returns:
            tuple: 无符号寄存器值。
        Raises:
            ValueError: 参数无效。
            RuntimeError: 通信失败。
        Notes:
            同一请求先重试，连续失败后才逐寄存器回退；非ISR-safe。
        """
        self._validate_int_range("address", address, 0, _UINT16_MAX)
        self._validate_int_range("count", count, 1, _MODBUS_MAX_READ_REGISTERS)
        block_error = None
        for attempt in range(self._retries):
            try:
                self.wake_up()
                values = tuple(self._host.read_holding_registers(self._slave_addr, address, count, False))
                if len(values) != count:
                    raise OSError("incomplete Modbus response")
                return values
            except (OSError, ValueError) as error:
                block_error = error
                if attempt + 1 < self._retries:
                    time.sleep_ms(self._retry_delay_ms)

        if count == 1:
            raise RuntimeError("Modbus read failed at 0x%04X after %d attempts: %s" % (address, self._retries, block_error)) from block_error

        values = []
        for offset in range(count):
            register_address = address + offset
            register_error = None
            for attempt in range(self._retries):
                try:
                    self.wake_up()
                    response = tuple(self._host.read_holding_registers(self._slave_addr, register_address, 1, False))
                    if len(response) != 1:
                        raise OSError("incomplete Modbus response")
                    values.append(response[0])
                    break
                except (OSError, ValueError) as error:
                    register_error = error
                    if attempt + 1 < self._retries:
                        time.sleep_ms(self._retry_delay_ms)
            else:
                raise RuntimeError(
                    "Modbus fallback read failed at 0x%04X after %d attempts: %s" % (register_address, self._retries, register_error)
                ) from register_error
        return tuple(values)

    def read_register(self, address: int) -> int:
        """读取单个寄存器。Read one register; not ISR-safe."""
        if address is None:
            raise ValueError("address cannot be None")
        if not isinstance(address, int):
            raise ValueError("address must be int")
        return self.read_registers(address, 1)[0]

    def write_register(self, address: int, value: int, unit_addr: int = -1) -> None:
        """写单个寄存器。Write one register; changes device state; not ISR-safe."""
        if not isinstance(address, int) or not isinstance(value, int):
            raise ValueError("address and value must be int")
        self._validate_int_range("address", address, 0, _UINT16_MAX)
        self._validate_int_range("value", value, 0, _UINT16_MAX)
        if not isinstance(unit_addr, int):
            raise ValueError("unit_addr must be int")
        if unit_addr != -1:
            self._validate_int_range("unit_addr", unit_addr, 1, 254)
        target = self._slave_addr if unit_addr == -1 else unit_addr
        try:
            self.wake_up()
            self._host.write_single_register(target, address, value, False)
        except OSError as error:
            raise RuntimeError("Modbus write failed at 0x%04X" % address) from error

    def read_node_address(self) -> int:
        """读取节点地址。Read node address; not ISR-safe."""
        return self.read_register(self.REG_NODE_ADDRESS)

    def write_node_address(self, new_address: int) -> None:
        """通过0xFE服务地址修改节点。Change node address via service address 0xFE."""
        if new_address is None:
            raise ValueError("new_address cannot be None")
        if not isinstance(new_address, int):
            raise ValueError("new_address must be int")
        self._validate_int_range("new_address", new_address, 1, 252)
        self.write_register(self.REG_NODE_ADDRESS, new_address, _ADDRESS_CHANGE_SLAVE)
        self._slave_addr = new_address

    def read_level(self) -> int:
        """读取液位毫米值。Read level in millimetres."""
        return self.read_register(self.REG_LEVEL)

    def read_temp(self) -> float:
        """读取摄氏温度。Read temperature in degrees Celsius."""
        return uint16_to_int16(self.read_register(self.REG_TEMPERATURE)) / 10.0

    def read_low_alarm(self) -> bool:
        """读取缺水报警。Read the low-level alarm."""
        return bool(self.read_register(self.REG_LOW_ALARM))

    def read_overflow_alarm(self) -> bool:
        """读取溢出报警。Read the overflow alarm."""
        return bool(self.read_register(self.REG_OVERFLOW_ALARM))

    def read_sf(self) -> float:
        """读取实时SF。Read the real-time SF ratio."""
        return self.read_register(self.REG_SF) / 1000.0

    def read_ratio(self) -> float:
        """读取实时SF兼容别名。Compatibility alias for read_sf()."""
        return self.read_sf()

    def read_capacitance(self) -> float:
        """读取实时算法电容和。Read the real-time combined capacitance in pF."""
        return self.read_register(self.REG_CAP_SUM) / 1000.0

    def read_frequency(self) -> float:
        """V2.1寄存器表未提供频率。Frequency is not exposed by this protocol."""
        raise NotImplementedError("Frequency is not exposed by the V2.1 register map")

    def read_cap_channels(self) -> tuple:
        """读取三个通道电容。Read CAP1, CAP2 and CAP3 in pF."""
        values = self.read_registers(self.REG_CAP1, 3)
        return values[0] / 1000.0, values[1] / 1000.0, values[2] / 1000.0

    def read_filter_count(self) -> int:
        """读取滑动平均窗口。Read the moving-average window length."""
        return self.read_register(self.REG_FILTER_WINDOW)

    def write_filter_count(self, count: int) -> None:
        """设置滑动平均窗口。Set the moving-average window; changes device state."""
        if count is None:
            raise ValueError("count cannot be None")
        if not isinstance(count, int):
            raise ValueError("count must be int")
        self._validate_int_range("count", count, 1, _UINT16_MAX)
        self.write_register(self.REG_FILTER_WINDOW, count)

    def read_fit_mode(self) -> int:
        """读取拟合模式。Read fitting mode 1 or 2."""
        return self.read_register(self.REG_FIT_MODE)

    def write_fit_mode(self, mode: int) -> None:
        """设置拟合模式。Set fitting mode; changes device state."""
        if mode is None:
            raise ValueError("mode cannot be None")
        if not isinstance(mode, int):
            raise ValueError("mode must be int")
        self._validate_int_range("mode", mode, 1, 2)
        self.write_register(self.REG_FIT_MODE, mode)

    def read_alarm_levels(self) -> tuple:
        """读取缺水与溢出阈值。Read low and overflow thresholds."""
        return self.read_registers(self.REG_LOW_ALARM_LEVEL, 2)

    def write_low_alarm_level(self, level_mm: int) -> None:
        """设置缺水阈值。Set low-level threshold; changes device state."""
        if level_mm is None:
            raise ValueError("level_mm cannot be None")
        if not isinstance(level_mm, int):
            raise ValueError("level_mm must be int")
        self._validate_level(level_mm)
        self.write_register(self.REG_LOW_ALARM_LEVEL, level_mm)

    def write_overflow_alarm_level(self, level_mm: int) -> None:
        """设置溢出阈值。Set overflow threshold; changes device state."""
        if level_mm is None:
            raise ValueError("level_mm cannot be None")
        if not isinstance(level_mm, int):
            raise ValueError("level_mm must be int")
        self._validate_level(level_mm)
        self.write_register(self.REG_OVERFLOW_ALARM_LEVEL, level_mm)

    def read_full_level(self) -> int:
        """读取满载高度。Read configured full-scale level."""
        return self.read_register(self.REG_FULL_LEVEL)

    def write_full_level(self, level_mm: int) -> None:
        """设置满载高度。Set full-scale level; changes device state."""
        if level_mm is None:
            raise ValueError("level_mm cannot be None")
        if not isinstance(level_mm, int):
            raise ValueError("level_mm must be int")
        self._validate_int_range("level_mm", level_mm, 1, self.MAX_LEVEL_MM)
        self.write_register(self.REG_FULL_LEVEL, level_mm)

    def calibrate_empty(self) -> None:
        """执行空载校准。Run empty calibration; changes calibration data."""
        self.write_register(self.REG_CALIBRATION, 1)

    def calibrate_full(self) -> None:
        """执行满载校准。Run full calibration; changes calibration data."""
        self.write_register(self.REG_CALIBRATION, 2)

    def read_calib_switch(self) -> int:
        """读取校准寄存器。Read calibration register."""
        return self.read_register(self.REG_CALIBRATION)

    def write_calib_switch(self, value: int) -> None:
        """写校准命令。Write calibration command 1 or 2."""
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise ValueError("value must be int")
        self._validate_int_range("value", value, 1, 2)
        self.write_register(self.REG_CALIBRATION, value)

    def read_reference_point(self, point: int) -> int:
        """读取五点拟合液位。Read one of five fitting levels."""
        if point is None:
            raise ValueError("point cannot be None")
        if not isinstance(point, int):
            raise ValueError("point must be int")
        self._validate_int_range("point", point, 1, 5)
        return self.read_register(self.REG_LEVEL1 + (point - 1) * 2)

    def write_reference_point(self, point: int, level_mm: int) -> None:
        """设置五点拟合液位。Set one of five fitting levels."""
        if not isinstance(point, int) or not isinstance(level_mm, int):
            raise ValueError("point and level_mm must be int")
        self._validate_int_range("point", point, 1, 5)
        self._validate_level(level_mm)
        self.write_register(self.REG_LEVEL1 + (point - 1) * 2, level_mm)

    def read_reference_sf(self, point: int) -> float:
        """读取五点拟合SF。Read one of five fitting SF values."""
        if point is None:
            raise ValueError("point cannot be None")
        if not isinstance(point, int):
            raise ValueError("point must be int")
        self._validate_int_range("point", point, 1, 5)
        return self.read_register(self.REG_SF1 + (point - 1) * 2) / 1000.0

    def write_reference_sf(self, point: int, sf: float) -> None:
        """设置五点拟合SF。Set one of five fitting SF values."""
        if point is None or sf is None:
            raise ValueError("point and sf cannot be None")
        if not isinstance(point, int):
            raise ValueError("point must be int")
        self._validate_int_range("point", point, 1, 5)
        if not isinstance(sf, (int, float)):
            raise ValueError("sf must be int or float")
        raw = int(round(sf * 1000)) if isinstance(sf, float) else sf
        self._validate_int_range("sf", raw, 0, 1000)
        self.write_register(self.REG_SF1 + (point - 1) * 2, raw)

    def read_ref_level1(self) -> int:
        """读取拟合液位1。Read fitting level 1."""
        return self.read_reference_point(1)

    def read_ref_level2(self) -> int:
        """读取拟合液位2。Read fitting level 2."""
        return self.read_reference_point(2)

    def read_ref_level3(self) -> int:
        """读取拟合液位3。Read fitting level 3."""
        return self.read_reference_point(3)

    def write_ref_level1(self, value: int) -> None:
        """设置拟合液位1。Set fitting level 1."""
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise ValueError("value must be int")
        self.write_reference_point(1, value)

    def write_ref_level2(self, value: int) -> None:
        """设置拟合液位2。Set fitting level 2."""
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise ValueError("value must be int")
        self.write_reference_point(2, value)

    def write_ref_level3(self, value: int) -> None:
        """设置拟合液位3。Set fitting level 3."""
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise ValueError("value must be int")
        self.write_reference_point(3, value)

    def read_hw_version_raw(self) -> tuple:
        """读取硬件主次版本。Read raw hardware major/minor versions."""
        return self.read_registers(self.REG_HW_VERSION, 2)

    def read_hw_version(self) -> str:
        """读取格式化硬件版本。Read formatted hardware version."""
        major, minor = self.read_hw_version_raw()
        return "%d.%d" % (major, minor)

    def read_fw_version(self) -> int:
        """读取固件原始版本。Read raw firmware version."""
        return self.read_register(self.REG_FW_VERSION)

    def read_device_uid(self) -> str:
        """读取96位设备UID。Read the 96-bit device UID."""
        values = self.read_registers(self.REG_UID, 6)
        return "".join("%04X" % value for value in values)

    def read_measurements(self) -> dict:
        """读取液位、温度、报警、SF与电容。Read all live measurements."""
        values = self.read_registers(self.REG_LEVEL, 6)
        return {
            "level_mm": values[0],
            "temperature_c": uint16_to_int16(values[1]) / 10.0,
            "low_alarm": bool(values[2]),
            "overflow_alarm": bool(values[3]),
            "sf": values[4] / 1000.0,
            "capacitance_pf": values[5] / 1000.0,
        }

    def deinit(self) -> None:
        """释放驱动引用但不关闭外部总线。Release references without closing the caller-owned bus."""
        self._host = None

    def _require_active(self) -> None:
        if self._host is None:
            raise RuntimeError("Driver is deinitialized")

    @staticmethod
    def _validate_int_range(name: str, value: int, minimum: int, maximum: int) -> None:
        if not isinstance(value, int):
            raise ValueError("%s must be int" % name)
        if value < minimum or value > maximum:
            raise ValueError("%s must be in range %d..%d" % (name, minimum, maximum))

    def _validate_level(self, level_mm: int) -> None:
        if level_mm is None:
            raise ValueError("level_mm cannot be None")
        if not isinstance(level_mm, int):
            raise ValueError("level_mm must be int")
        self._validate_int_range("level_mm", level_mm, 0, self.MAX_LEVEL_MM)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
