# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:00
# @Author  : December
# @File    : hds.py
# @Description : 敏源 HDS 湿度检测传感器 Modbus RTU 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "December"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import micropython
import time

# ======================================== 全局变量 ============================================

_U16_MAX = micropython.const(0xFFFF)

# ======================================== 功能函数 ============================================


def _u16_to_s16(value: int) -> int:
    """将无符号 16 位整数转换为有符号整数。"""
    if not isinstance(value, int):
        raise ValueError("value must be int")
    if value < 0 or value > _U16_MAX:
        raise ValueError("value must be in range 0..65535")
    if value & 0x8000:
        return value - 0x10000
    return value


# ======================================== 自定义类 ============================================


class HDSError(Exception):
    """HDS 驱动基础异常。"""


class HDSTimeoutError(HDSError):
    """HDS 响应超时异常。"""


class HDSCRCError(HDSError):
    """HDS Modbus CRC 校验异常。"""


class HDSProtocolError(HDSError):
    """HDS Modbus 协议异常。"""


class HDS:
    """
    敏源 HDS 湿度检测传感器 Modbus RTU 驱动类。

    Attributes:
        address (int): Modbus 从机地址。
    Methods:
        read_temperature(): 读取温度。
        read_capacitance(): 读取两路电容。
        read_basic_measurements(): 一次读取温度和两路电容。
        read_measurements(): 读取全部实时测量寄存器。
        read_device_info(): 读取设备信息。
        set_averaging(): 设置平均次数。
        set_device_address(): 设置 Modbus 从机地址。
        trigger_calibration(): 触发校准指令。
        deinit(): 释放驱动对通信主机的引用。
    Notes:
        - 依赖外部传入的 umodbus RTU 主机实例。
        - HDS 输出材料含水变化相关的电容值，不是环境相对湿度 %RH。
        - 所有通信方法均非 ISR-safe。

    ==========================================

    Mysentech HDS humidity detection sensor Modbus RTU driver.

    Attributes:
        address (int): Modbus slave address.
    Methods:
        read_temperature(): Read temperature.
        read_capacitance(): Read both capacitance channels.
        read_basic_measurements(): Read temperature and capacitance channels.
        read_measurements(): Read all live measurement registers.
        read_device_info(): Read device information.
        set_averaging(): Set the averaging count.
        set_device_address(): Set the Modbus slave address.
        trigger_calibration(): Trigger the calibration command.
        deinit(): Release the driver's reference to the communication host.
    Notes:
        - Requires an externally supplied umodbus RTU master instance.
        - HDS capacitance represents material moisture changes, not ambient %RH.
        - Communication methods are not ISR-safe.
    """

    DEFAULT_ADDRESS = micropython.const(0x01)
    DEFAULT_RETRIES = micropython.const(2)
    DEFAULT_RETRY_DELAY_MS = micropython.const(50)

    REG_DEVICE_ADDRESS = micropython.const(0x0002)
    REG_AVERAGING = micropython.const(0x0003)
    REG_HUMIDITY_LEVEL = micropython.const(0x0004)
    REG_ID = micropython.const(0x0005)
    REG_CALIBRATION_COMMAND = micropython.const(0x0006)
    REG_TEMPERATURE = micropython.const(0x0007)
    REG_C1 = micropython.const(0x0008)
    REG_C2 = micropython.const(0x0009)
    REG_REFERENCE_COUNT = micropython.const(0x000A)
    REG_CHANNEL1_COUNT = micropython.const(0x000B)
    REG_CHANNEL2_COUNT = micropython.const(0x000C)
    REG_REFERENCE_FREQUENCY = micropython.const(0x000D)
    REG_CHANNEL1_FREQUENCY = micropython.const(0x000E)
    REG_CHANNEL2_FREQUENCY = micropython.const(0x000F)
    REG_CHANNEL1_CALIBRATION = micropython.const(0x0010)
    REG_CHANNEL2_CALIBRATION = micropython.const(0x0011)
    REG_CHANNEL1_DIFFERENCE = micropython.const(0x0012)
    REG_CHANNEL2_DIFFERENCE = micropython.const(0x0013)
    REG_SOFTWARE_VERSION = micropython.const(0x0014)
    REG_HARDWARE_VERSION = micropython.const(0x0015)

    __slots__ = ("_host", "_address", "_retries", "_retry_delay_ms", "_debug")

    def __init__(
        self,
        host: object,
        address: int = DEFAULT_ADDRESS,
        retries: int = DEFAULT_RETRIES,
        retry_delay_ms: int = DEFAULT_RETRY_DELAY_MS,
        debug: bool = False,
    ) -> None:
        """
        初始化 HDS 驱动。

        Args:
            host (object): umodbus RTU 主机实例。
            address (int): Modbus 从机地址，范围 1～247。
            retries (int): 读取失败后的重试次数。
            retry_delay_ms (int): 每次重试前的等待时间，单位毫秒。
            debug (bool): 是否输出英文调试日志。
        Returns:
            None
        Raises:
            ValueError: 参数类型、范围或主机能力不正确。
        Notes:
            - 保存外部通信主机引用，不创建 UART，也不修改传感器状态。
            - ISR-safe: 否。

        ==========================================

        Initialize the HDS driver.

        Args:
            host (object): umodbus RTU master instance.
            address (int): Modbus slave address in range 1..247.
            retries (int): Retry count after a failed read.
            retry_delay_ms (int): Delay before each retry in milliseconds.
            debug (bool): Enable English debug output.
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type, range, or host capability.
        Notes:
            - Stores the injected host without creating UART or changing the sensor.
            - ISR-safe: No.
        """
        if host is None:
            raise ValueError("host must not be None")
        if not hasattr(host, "read_holding_registers"):
            raise ValueError("host must provide read_holding_registers")
        if not hasattr(host, "write_single_register"):
            raise ValueError("host must provide write_single_register")
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if address < 1 or address > 247:
            raise ValueError("address must be in range 1..247")
        if not isinstance(retries, int):
            raise ValueError("retries must be int")
        if retries < 0:
            raise ValueError("retries must be zero or greater")
        if not isinstance(retry_delay_ms, int):
            raise ValueError("retry_delay_ms must be int")
        if retry_delay_ms < 0:
            raise ValueError("retry_delay_ms must be zero or greater")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._host = host
        self._address = address
        self._retries = retries
        self._retry_delay_ms = retry_delay_ms
        self._debug = debug

    def read_registers(self, start_register: int, count: int = 1) -> tuple:
        """
        读取一个或多个保持寄存器。

        Args:
            start_register (int): 起始寄存器地址，范围 0～65535。
            count (int): 寄存器数量，范围 1～125。
        Returns:
            tuple: 无符号 16 位寄存器值。
        Raises:
            ValueError: 参数类型或范围错误。
            HDSError: Modbus 通信失败。
        Notes:
            - 执行 Modbus 0x03 操作，瞬态 I/O 错误会自动重试。
            - ISR-safe: 否。

        ==========================================

        Read one or more holding registers.

        Args:
            start_register (int): Start register in range 0..65535.
            count (int): Register count in range 1..125.
        Returns:
            tuple: Unsigned 16-bit register values.
        Raises:
            ValueError: Invalid parameter type or range.
            HDSError: Modbus communication failed.
        Notes:
            - Performs Modbus function 0x03 and retries transient I/O errors.
            - ISR-safe: No.
        """
        if not isinstance(start_register, int):
            raise ValueError("start_register must be int")
        if start_register < 0 or start_register > _U16_MAX:
            raise ValueError("start_register must be in range 0..65535")
        if not isinstance(count, int):
            raise ValueError("count must be int")
        if count < 1 or count > 125:
            raise ValueError("count must be in range 1..125")

        self._ensure_active()
        last_error = None
        for attempt in range(self._retries + 1):
            try:
                values = self._host.read_holding_registers(
                    self._address,
                    start_register,
                    count,
                    False,
                )
                return tuple(values)
            except OSError as error:
                last_error = error
                if attempt < self._retries:
                    self._log("Read failed; retrying")
                    time.sleep_ms(self._retry_delay_ms)
            except ValueError as error:
                raise HDSProtocolError("Invalid Modbus response") from error

        self._raise_communication_error(last_error)

    def read_register(self, register: int) -> int:
        """
        读取单个原始寄存器。

        Args:
            register (int): 寄存器地址。
        Returns:
            int: 无符号 16 位寄存器值。
        Raises:
            ValueError: 地址无效。
            HDSError: Modbus 通信失败。
        Notes:
            - 读取传感器，不修改硬件状态。
            - ISR-safe: 否。

        ==========================================

        Read one raw register.

        Args:
            register (int): Register address.
        Returns:
            int: Unsigned 16-bit register value.
        Raises:
            ValueError: Invalid address.
            HDSError: Modbus communication failed.
        Notes:
            - Reads the sensor without changing hardware state.
            - ISR-safe: No.
        """
        if register is None:
            raise ValueError("register must not be None")
        if not isinstance(register, int):
            raise ValueError("register must be int")
        return self.read_registers(register, 1)[0]

    def write_register(self, register: int, value: int) -> int:
        """
        写入单个保持寄存器。

        Args:
            register (int): 寄存器地址。
            value (int): 无符号 16 位写入值。
        Returns:
            int: 成功写入的值。
        Raises:
            ValueError: 参数类型或范围错误。
            HDSError: Modbus 通信失败或从机拒绝写入。
        Notes:
            - 执行 Modbus 0x06，会修改传感器状态或配置。
            - 为避免重复写副作用，写操作不自动重试。
            - ISR-safe: 否。

        ==========================================

        Write one holding register.

        Args:
            register (int): Register address.
            value (int): Unsigned 16-bit value.
        Returns:
            int: Successfully written value.
        Raises:
            ValueError: Invalid parameter type or range.
            HDSError: Modbus failure or rejected write.
        Notes:
            - Performs Modbus function 0x06 and changes sensor state or settings.
            - Writes are not retried to avoid duplicate side effects.
            - ISR-safe: No.
        """
        if not isinstance(register, int):
            raise ValueError("register must be int")
        if register < 0 or register > _U16_MAX:
            raise ValueError("register must be in range 0..65535")
        if not isinstance(value, int):
            raise ValueError("value must be int")
        if value < 0 or value > _U16_MAX:
            raise ValueError("value must be in range 0..65535")

        self._ensure_active()
        try:
            result = self._host.write_single_register(
                self._address,
                register,
                value,
                False,
            )
        except OSError as error:
            self._raise_communication_error(error)
        except ValueError as error:
            raise HDSProtocolError("Invalid Modbus write response") from error

        if not result:
            raise HDSError("Modbus write was not acknowledged")
        return value

    def read_temperature(self) -> float:
        """
        读取传感器温度。

        Returns:
            float: 摄氏温度。
        Raises:
            HDSError: Modbus 通信失败。
        Notes:
            - 读取寄存器 0x0007，不修改硬件状态。
            - ISR-safe: 否。

        ==========================================

        Read sensor temperature.

        Returns:
            float: Temperature in degrees Celsius.
        Raises:
            HDSError: Modbus communication failed.
        Notes:
            - Reads register 0x0007 without changing hardware state.
            - ISR-safe: No.
        """
        raw = self.read_register(self.REG_TEMPERATURE)
        return _u16_to_s16(raw) / 10.0

    def read_capacitance(self) -> tuple:
        """
        读取 C1 和 C2 电容。

        Returns:
            tuple: C1、C2 电容值，单位 pF。
        Raises:
            HDSError: Modbus 通信失败。
        Notes:
            - 一次读取寄存器 0x0008～0x0009，不修改硬件状态。
            - ISR-safe: 否。

        ==========================================

        Read C1 and C2 capacitance.

        Returns:
            tuple: C1 and C2 in pF.
        Raises:
            HDSError: Modbus communication failed.
        Notes:
            - Reads registers 0x0008..0x0009 in one request.
            - ISR-safe: No.
        """
        values = self.read_registers(self.REG_C1, 2)
        return values[0] / 1000.0, values[1] / 1000.0

    def read_basic_measurements(self) -> dict:
        """
        一次读取温度和两路电容。

        Returns:
            dict: 包含 temperature_c、c1_pf 和 c2_pf。
        Raises:
            HDSError: Modbus 通信失败。
        Notes:
            - 使用较短响应，推荐用于周期采样。
            - ISR-safe: 否。

        ==========================================

        Read temperature and both capacitance channels in one request.

        Returns:
            dict: Contains temperature_c, c1_pf, and c2_pf.
        Raises:
            HDSError: Modbus communication failed.
        Notes:
            - Uses a short response and is recommended for periodic sampling.
            - ISR-safe: No.
        """
        values = self.read_registers(self.REG_TEMPERATURE, 3)
        return {
            "temperature_c": _u16_to_s16(values[0]) / 10.0,
            "c1_pf": values[1] / 1000.0,
            "c2_pf": values[2] / 1000.0,
        }

    def read_humidity_level_raw(self) -> int:
        """
        读取原始湿度档位寄存器。

        Returns:
            int: 寄存器 0x0004 的原始值。
        Raises:
            HDSError: Modbus 通信失败。
        Notes:
            - 手册将该寄存器标为预留，驱动不解释为百分比。
            - ISR-safe: 否。

        ==========================================

        Read the raw humidity-level register.

        Returns:
            int: Raw value of register 0x0004.
        Raises:
            HDSError: Modbus communication failed.
        Notes:
            - The manual marks this register reserved; it is not interpreted as %RH.
            - ISR-safe: No.
        """
        return self.read_register(self.REG_HUMIDITY_LEVEL)

    def read_measurements(self) -> dict:
        """
        读取全部实时测量寄存器。

        Returns:
            dict: 温度、电容、计数、频率、校准值和通道差值。
        Raises:
            HDSError: Modbus 通信失败。
        Notes:
            - 一次读取 13 个寄存器，响应较长，不建议高频调用。
            - ISR-safe: 否。

        ==========================================

        Read all live measurement registers.

        Returns:
            dict: Temperature, capacitance, counts, frequencies, calibration, and differences.
        Raises:
            HDSError: Modbus communication failed.
        Notes:
            - Reads 13 registers; the longer response is not recommended at high rate.
            - ISR-safe: No.
        """
        values = self.read_registers(self.REG_TEMPERATURE, 13)
        return {
            "temperature_c": _u16_to_s16(values[0]) / 10.0,
            "c1_pf": values[1] / 1000.0,
            "c2_pf": values[2] / 1000.0,
            "reference_count": values[3],
            "channel1_count": values[4],
            "channel2_count": values[5],
            "reference_frequency_mhz": values[6] / 100.0,
            "channel1_frequency_mhz": values[7] / 100.0,
            "channel2_frequency_mhz": values[8] / 100.0,
            "channel1_calibration": values[9],
            "channel2_calibration": values[10],
            "channel1_difference": _u16_to_s16(values[11]),
            "channel2_difference": _u16_to_s16(values[12]),
        }

    def read_device_info(self) -> dict:
        """
        读取设备信息。

        Returns:
            dict: 地址、平均次数、湿度档位、ID 和软硬件版本。
        Raises:
            HDSError: Modbus 通信失败。
        Notes:
            - 版本寄存器返回 0xFFFF 时，对应版本值为 None。
            - ISR-safe: 否。

        ==========================================

        Read device information.

        Returns:
            dict: Address, averaging, humidity level, ID, and firmware versions.
        Raises:
            HDSError: Modbus communication failed.
        Notes:
            - A version register value of 0xFFFF is returned as None.
            - ISR-safe: No.
        """
        base = self.read_registers(self.REG_DEVICE_ADDRESS, 4)
        versions = self.read_registers(self.REG_SOFTWARE_VERSION, 2)

        software_version = None
        hardware_version = None
        if versions[0] != _U16_MAX:
            software_version = versions[0] / 10.0
        if versions[1] != _U16_MAX:
            hardware_version = versions[1] / 100.0

        return {
            "address": base[0],
            "averaging": base[1],
            "humidity_level_raw": base[2],
            "id": base[3],
            "software_version": software_version,
            "hardware_version": hardware_version,
        }

    def set_averaging(self, count: int) -> int:
        """
        设置平均次数。

        Args:
            count (int): 平均次数，范围 0～30。
        Returns:
            int: 成功写入的平均次数。
        Raises:
            ValueError: 参数类型或范围错误。
            HDSError: Modbus 通信失败。
        Notes:
            - 修改寄存器 0x0003，可能改变测量响应速度和稳定性。
            - ISR-safe: 否。

        ==========================================

        Set the averaging count.

        Args:
            count (int): Averaging count in range 0..30.
        Returns:
            int: Successfully written averaging count.
        Raises:
            ValueError: Invalid parameter type or range.
            HDSError: Modbus communication failed.
        Notes:
            - Changes register 0x0003 and may affect response speed and stability.
            - ISR-safe: No.
        """
        if not isinstance(count, int):
            raise ValueError("count must be int")
        if count < 0 or count > 30:
            raise ValueError("count must be in range 0..30")
        return self.write_register(self.REG_AVERAGING, count)

    def set_device_address(self, new_address: int) -> int:
        """
        修改传感器 Modbus 地址。

        Args:
            new_address (int): 新地址，范围 1～247。
        Returns:
            int: 新地址。
        Raises:
            ValueError: 地址类型或范围错误。
            HDSError: Modbus 通信失败。
        Notes:
            - 修改寄存器 0x0002，并同步更新驱动地址。
            - ISR-safe: 否。

        ==========================================

        Change the sensor Modbus address.

        Args:
            new_address (int): New address in range 1..247.
        Returns:
            int: New address.
        Raises:
            ValueError: Invalid address type or range.
            HDSError: Modbus communication failed.
        Notes:
            - Changes register 0x0002 and updates the driver's address.
            - ISR-safe: No.
        """
        if not isinstance(new_address, int):
            raise ValueError("new_address must be int")
        if new_address < 1 or new_address > 247:
            raise ValueError("new_address must be in range 1..247")

        self.write_register(self.REG_DEVICE_ADDRESS, new_address)
        self._address = new_address
        return new_address

    def trigger_calibration(self) -> int:
        """
        触发传感器校准指令。

        Returns:
            int: 成功写入的命令值 1。
        Raises:
            HDSError: Modbus 通信失败。
        Notes:
            - 向寄存器 0x0006 写入 1，会修改传感器校准状态。
            - 现有手册未说明完整校准工艺，使用前应确认安装状态。
            - ISR-safe: 否。

        ==========================================

        Trigger the sensor calibration command.

        Returns:
            int: Successfully written command value 1.
        Raises:
            HDSError: Modbus communication failed.
        Notes:
            - Writes 1 to register 0x0006 and changes sensor calibration state.
            - Confirm the installation state because the manual omits the full procedure.
            - ISR-safe: No.
        """
        return self.write_register(self.REG_CALIBRATION_COMMAND, 1)

    @property
    def address(self) -> int:
        """
        获取当前 Modbus 从机地址。

        Returns:
            int: 当前从机地址。
        Notes:
            - 无硬件副作用。
            - ISR-safe: 是。

        ==========================================

        Get the current Modbus slave address.

        Returns:
            int: Current slave address.
        Notes:
            - No hardware side effects.
            - ISR-safe: Yes.
        """
        return self._address

    def _ensure_active(self) -> None:
        if self._host is None:
            raise HDSError("HDS driver is deinitialized")

    def _log(self, message: str) -> None:
        if message is None:
            raise ValueError("message must not be None")
        if not isinstance(message, str):
            raise ValueError("message must be str")
        if self._debug:
            print("[HDS] %s" % message)

    @staticmethod
    def _raise_communication_error(error: object) -> None:
        message = str(error)
        lower_message = message.lower()
        if "crc" in lower_message:
            raise HDSCRCError("Modbus CRC validation failed") from error
        if "no data" in lower_message or "timeout" in lower_message:
            raise HDSTimeoutError("HDS response timeout") from error
        raise HDSError("HDS Modbus communication failed: %s" % message) from error

    def deinit(self) -> None:
        """
        释放驱动持有的通信主机引用。

        Returns:
            None
        Notes:
            - 不关闭外部注入的 Modbus 主机或 UART，其生命周期由调用者管理。
            - 调用后不能继续使用本驱动实例。
            - ISR-safe: 否。

        ==========================================

        Release the driver's communication-host reference.

        Returns:
            None
        Notes:
            - Does not close the injected Modbus host or UART; the caller owns them.
            - This driver instance cannot be used after the call.
            - ISR-safe: No.
        """
        self._host = None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
