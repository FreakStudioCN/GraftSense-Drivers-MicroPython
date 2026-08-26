# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : GraftSense contributors and FreakStudio
# @File    : sx126x.py
# @Description : Dependency-injected SX126X initialization, TX, and RX transport
# @License : MIT

"""Dependency-injected SX126X core framework / 依赖注入式 SX126X 核心框架。"""

__version__ = "1.0.0"
__author__ = "GraftSense contributors; E H Ong; Jan Gromes; FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================
try:
    from time import sleep_us, ticks_diff, ticks_ms
except ImportError:
    import time

    def ticks_ms() -> int:
        """
        执行 `ticks_ms` 操作。
        Args:
            无。
        Returns:
            int: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return host monotonic time in milliseconds.
        Args:
            None.
        Returns:
            int: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return int(time.monotonic() * 1000)

    def ticks_diff(end: int, start: int) -> int:
        """
        执行 `ticks_diff` 操作。
        Args:
            end (int): 方法参数。
            start (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return the host-side millisecond difference.
        Args:
            end (int): Method parameter.
            start (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return end - start

    def sleep_us(microseconds: int) -> None:
        """
        执行 `sleep_us` 操作。
        Args:
            microseconds (int): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Sleep for microseconds during host-side checks.
        Args:
            microseconds (int): Method parameter.
        Returns:
            None: No return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        time.sleep(microseconds / 1000000.0)


from _sx126x import (
    SX126X_CMD_GET_STATUS,
    SX126X_CMD_GET_IRQ_STATUS,
    SX126X_CMD_GET_PACKET_STATUS,
    SX126X_CMD_GET_RX_BUFFER_STATUS,
    SX126X_CMD_GET_DEVICE_ERRORS,
    SX126X_CMD_NOP,
    SX126X_CMD_CLEAR_IRQ_STATUS,
    SX126X_CMD_CLEAR_DEVICE_ERRORS,
    SX126X_CMD_CALIBRATE,
    SX126X_CMD_CALIBRATE_IMAGE,
    SX126X_CMD_READ_REGISTER,
    SX126X_CMD_READ_BUFFER,
    SX126X_CMD_SET_DIO2_AS_RF_SWITCH_CTRL,
    SX126X_CMD_SET_DIO3_AS_TCXO_CTRL,
    SX126X_CMD_SET_DIO_IRQ_PARAMS,
    SX126X_CMD_SET_BUFFER_BASE_ADDRESS,
    SX126X_CMD_SET_REGULATOR_MODE,
    SX126X_CMD_SET_RX_TX_FALLBACK_MODE,
    SX126X_CMD_SET_MODULATION_PARAMS,
    SX126X_CMD_SET_PACKET_PARAMS,
    SX126X_CMD_SET_PACKET_TYPE,
    SX126X_CMD_SET_PA_CONFIG,
    SX126X_CMD_SET_RF_FREQUENCY,
    SX126X_CMD_SET_STANDBY,
    SX126X_CMD_SET_TX,
    SX126X_CMD_SET_RX,
    SX126X_CMD_SET_TX_PARAMS,
    SX126X_CMD_WRITE_BUFFER,
    SX126X_CMD_WRITE_REGISTER,
    SX126X_DIO2_AS_IRQ,
    SX126X_DIO2_AS_RF_SWITCH,
    SX126X_DIO3_OUTPUT_2_2,
    SX126X_CALIBRATE_ALL,
    SX126X_FALLBACK_STANDBY_RC,
    SX126X_IRQ_ALL,
    SX126X_IRQ_CRC_ERROR,
    SX126X_IRQ_HEADER_ERROR,
    SX126X_IRQ_RX_DONE,
    SX126X_IRQ_TIMEOUT,
    SX126X_IRQ_TX_DONE,
    SX126X_LORA_BW_125_0,
    SX126X_LORA_CRC_ON,
    SX126X_LORA_HEADER_EXPLICIT,
    SX126X_LORA_IQ_STANDARD,
    SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_OFF,
    SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_ON,
    SX126X_LORA_SYNC_WORD_PRIVATE_LSB,
    SX126X_LORA_SYNC_WORD_PRIVATE_MSB,
    SX126X_PA_RAMP_200_US,
    SX126X_STANDBY_RC,
    SX126X_REGULATOR_DCDC,
    SX126X_REGULATOR_LDO,
    SX126X_STATUS_CMD_FAILED,
    SX126X_STATUS_CMD_INVALID,
    SX126X_STATUS_CMD_TIMEOUT,
    SX1262_PA_DEVICE_SEL,
    SX1262_PA_DUTY_CYCLE_22_DBM,
    SX1262_PA_HP_MAX_22_DBM,
    SX1262_PA_LUT,
    SX126X_STATE_DEINITIALIZED,
    SX126X_STATE_ERROR,
    SX126X_STATE_STANDBY,
    SX126X_STATE_RX,
    SX126X_STATE_TX,
    SX126X_STATE_UNINITIALIZED,
    SX126X_REG_LORA_SYNC_WORD_MSB,
    SX126X_REG_SENSITIVITY_CONFIG,
    SX126X_REG_TX_CLAMP_CONFIG,
)


# ======================================== 全局变量 ============================================
# 命令帧参考 MIT 许可的 GraftSense sx1262_driver 和 Semtech SX1261/2 数据手册。


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class SX126XError(RuntimeError):
    """
    SX126X runtime error / SX126X 运行时错误。
    Attributes:
        继承 RuntimeError 属性。
    Methods:
        继承 RuntimeError 方法。
    Notes:
        - 用于区分驱动错误类型。
    ==========================================
    SX126XError exception class.
    Attributes:
        Inherits RuntimeError attributes.
    Methods:
        Inherits RuntimeError methods.
    Notes:
        - Distinguishes a specific driver error category.
    """


class SX126XTimeoutError(SX126XError):
    """
    SX126X bounded-wait timeout / SX126X 有界等待超时。
    Attributes:
        继承 SX126XError 属性。
    Methods:
        继承 SX126XError 方法。
    Notes:
        - 用于区分驱动错误类型。
    ==========================================
    SX126XTimeoutError exception class.
    Attributes:
        Inherits SX126XError attributes.
    Methods:
        Inherits SX126XError methods.
    Notes:
        - Distinguishes a specific driver error category.
    """


class SX126XSPIError(SX126XError):
    """
    SX126X SPI communication error / SX126X SPI 通信错误。
    Attributes:
        继承 SX126XError 属性。
    Methods:
        继承 SX126XError 方法。
    Notes:
        - 用于区分驱动错误类型。
    ==========================================
    SX126XSPIError exception class.
    Attributes:
        Inherits SX126XError attributes.
    Methods:
        Inherits SX126XError methods.
    Notes:
        - Distinguishes a specific driver error category.
    """


class SX126XStateError(SX126XError):
    """
    SX126X invalid-state error / SX126X 非法状态错误。
    Attributes:
        继承 SX126XError 属性。
    Methods:
        继承 SX126XError 方法。
    Notes:
        - 用于区分驱动错误类型。
    ==========================================
    SX126XStateError exception class.
    Attributes:
        Inherits SX126XError attributes.
    Methods:
        Inherits SX126XError methods.
    Notes:
        - Distinguishes a specific driver error category.
    """


class SX126X:
    """
    SX126X 依赖注入式底层驱动。
    Attributes:
        state (int): 当前 SX126X 状态码。
        last_initialization_plan (tuple): 最后一次初始化计划。
    Methods:
        reset(): 执行硬件复位。
        standby(): 进入待机模式。
        set_tx(): 启动发送。
        set_rx(): 启动接收。
        deinit(): 清理传输状态。
    Notes:
        - 实现有界 BUSY 等待、SPI 命令以及 LoRa TX/RX 支持。
        - SPI 和 Pin 由外部注入；非 ISR-safe。
    ==========================================
    Dependency-injected SX126X low-level driver.
    Attributes:
        state (int): Current SX126X state code.
        last_initialization_plan (tuple): Last initialization plan.
    Methods:
        reset(): Perform a hardware reset.
        standby(): Enter standby mode.
        set_tx(): Start transmission.
        set_rx(): Start reception.
        deinit(): Clear transport state.
    Notes:
        - Implements bounded BUSY waits, SPI commands, and LoRa TX/RX support.
        - SPI and Pin objects are injected by the caller; not ISR-safe.
    """

    __slots__ = (
        "_spi",
        "_cs",
        "_reset",
        "_busy",
        "_dio1",
        "_busy_timeout_ms",
        "_debug",
        "_state",
        "_last_initialization_plan",
    )

    def __init__(
        self,
        spi: object,
        cs: object,
        reset: object,
        busy: object,
        dio1: object,
        busy_timeout_ms: int = 5000,
        debug: bool = False,
    ) -> None:
        """
        注入 SPI 与控制引脚对象，不创建硬件资源。
        Args:
            spi (object): 方法参数。
            cs (object): 方法参数。
            reset (object): 方法参数。
            busy (object): 方法参数。
            dio1 (object): 方法参数。
            busy_timeout_ms (int): 方法参数。
            debug (bool): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Inject SPI and control pin objects without creating hardware resources.
        Args:
            spi (object): Method parameter.
            cs (object): Method parameter.
            reset (object): Method parameter.
            busy (object): Method parameter.
            dio1 (object): Method parameter.
            busy_timeout_ms (int): Method parameter.
            debug (bool): Method parameter.
        Returns:
            None: No return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if spi is None:
            raise ValueError("spi must not be None")
        if cs is None:
            raise ValueError("cs must not be None")
        if reset is None:
            raise ValueError("reset must not be None")
        if busy is None:
            raise ValueError("busy must not be None")
        if dio1 is None:
            raise ValueError("dio1 must not be None")
        if not isinstance(busy_timeout_ms, int):
            raise TypeError("busy_timeout_ms must be int")
        if busy_timeout_ms <= 0:
            raise ValueError("busy_timeout_ms must be greater than zero")
        self._validate_spi(spi)
        self._validate_pin(cs, "cs")
        self._validate_pin(reset, "reset")
        self._validate_pin(busy, "busy")
        self._validate_pin(dio1, "dio1")
        self._validate_timeout(busy_timeout_ms, "busy_timeout_ms")
        if not isinstance(debug, bool):
            raise TypeError("debug must be bool")

        self._spi = spi
        self._cs = cs
        self._reset = reset
        self._busy = busy
        self._dio1 = dio1
        self._busy_timeout_ms = busy_timeout_ms
        self._debug = debug
        self._state = SX126X_STATE_UNINITIALIZED
        self._last_initialization_plan = ()

    @property
    def state(self) -> int:
        """
        返回驱动状态。 / Return the driver state.
        Args:
            无。
        Returns:
            int: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `state` operation.
        Args:
            None.
        Returns:
            int: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return self._state

    @property
    def last_initialization_plan(self) -> tuple:
        """
        返回最近生成的初始化步骤。 / Return the latest initialization plan.
        Args:
            无。
        Returns:
            tuple: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `last_initialization_plan` operation.
        Args:
            None.
        Returns:
            tuple: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return self._last_initialization_plan

    def wait_while_busy(self, timeout_ms: int = None, operation: str = "operation") -> None:
        """
        有界等待 BUSY 变低。
        Args:
            timeout_ms (int): 方法参数。
            operation (str): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
            ValueError: 参数、状态或通信异常。
            SX126XTimeoutError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Wait for BUSY to become low with a bounded timeout.
        Args:
            timeout_ms (int): Method parameter.
            operation (str): Method parameter.
        Returns:
            None: No return value.
        Raises:
            TypeError: Parameter, state, or communication error.
            ValueError: Parameter, state, or communication error.
            SX126XTimeoutError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        self._validate_timeout(timeout_ms, "timeout_ms")
        if not isinstance(operation, str):
            raise TypeError("operation must be str")
        if not operation:
            raise ValueError("operation must not be empty")

        started = ticks_ms()
        while self._busy.value():
            if ticks_diff(ticks_ms(), started) >= timeout_ms:
                raise SX126XTimeoutError("BUSY timeout during %s" % operation)
            sleep_us(50)

    def reset(self, timeout_ms: int = None) -> int:
        """
        执行 `reset` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Pulse NRST, wait for BUSY, and return the first valid status byte.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        self._validate_timeout(timeout_ms, "timeout_ms")

        self._cs.value(1)
        self._reset.value(1)
        sleep_us(150)
        self._reset.value(0)
        sleep_us(150)
        self._reset.value(1)
        sleep_us(150)
        self.wait_while_busy(timeout_ms, "reset")
        return self.get_status(timeout_ms)

    def standby(self, timeout_ms: int = None) -> int:
        """
        执行 `standby` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Enter STDBY_RC and return a status byte from a follow-up probe.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        self._validate_timeout(timeout_ms, "timeout_ms")
        self._write_command(SX126X_CMD_SET_STANDBY, bytes((SX126X_STANDBY_RC,)), timeout_ms)
        status = self.get_status(timeout_ms)
        self._state = SX126X_STATE_STANDBY
        return status

    def get_status(self, timeout_ms: int = None) -> int:
        """
        执行 `get_status` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: timeout_ms 不是 int 或 None。
            ValueError: timeout_ms 不是正整数。
            SX126XSPIError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Issue GetStatus and reject floating-bus 0x00/0xFF responses.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: timeout_ms is not int or None.
            ValueError: timeout_ms is not positive.
            SX126XSPIError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        self._validate_timeout(timeout_ms, "timeout_ms")
        receive = bytearray(2)
        self._transfer(bytes((SX126X_CMD_GET_STATUS, SX126X_CMD_NOP)), receive, timeout_ms)
        status = receive[1]
        if status == 0x00 or status == 0xFF:
            raise SX126XSPIError("invalid GetStatus response: 0x%02X" % status)
        return status

    def set_tcxo_2_2(self, delay_us: int = 5000, timeout_ms: int = None) -> int:
        """
        执行 `set_tcxo_2_2` 操作。
        Args:
            delay_us (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Configure DIO3 for the E22 TCXO at 2.2 V.
        Args:
            delay_us (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(delay_us, int):
            raise TypeError("delay_us must be int")
        if delay_us <= 0:
            raise ValueError("delay_us must be greater than zero")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        self._validate_timeout(timeout_ms, "timeout_ms")

        delay_units = (delay_us * 64) // 1000
        if delay_units > 0xFFFFFF:
            raise ValueError("delay_us exceeds the SX126X 24-bit delay field")
        payload = bytes(
            (
                SX126X_DIO3_OUTPUT_2_2,
                (delay_units >> 16) & 0xFF,
                (delay_units >> 8) & 0xFF,
                delay_units & 0xFF,
            )
        )
        self._write_command(SX126X_CMD_SET_DIO3_AS_TCXO_CTRL, payload, timeout_ms)
        return self.get_status(timeout_ms)

    def set_dio2_rf_switch(self, enable: bool = True, timeout_ms: int = None) -> int:
        """
        执行 `set_dio2_rf_switch` 操作。
        Args:
            enable (bool): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Enable or disable automatic RF-switch control on DIO2.
        Args:
            enable (bool): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if enable is None:
            raise ValueError("enable must not be None")
        if not isinstance(enable, bool):
            raise TypeError("enable must be bool")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        self._validate_timeout(timeout_ms, "timeout_ms")
        value = SX126X_DIO2_AS_RF_SWITCH if enable else SX126X_DIO2_AS_IRQ
        self._write_command(SX126X_CMD_SET_DIO2_AS_RF_SWITCH_CTRL, bytes((value,)), timeout_ms)
        return self.get_status(timeout_ms)

    def set_regulator_mode(self, use_ldo: bool = False, timeout_ms: int = None) -> int:
        """
        执行 `set_regulator_mode` 操作。
        Args:
            use_ldo (bool): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Select the SX1262 internal LDO or DC-DC regulator mode.
        Args:
            use_ldo (bool): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if use_ldo is None:
            raise ValueError("use_ldo must not be None")
        if not isinstance(use_ldo, bool):
            raise TypeError("use_ldo must be bool")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        mode = SX126X_REGULATOR_LDO if use_ldo else SX126X_REGULATOR_DCDC
        self._write_command(SX126X_CMD_SET_REGULATOR_MODE, bytes((mode,)), timeout_ms)
        return self._validated_status(timeout_ms, "SetRegulatorMode")

    def set_rx_tx_fallback_standby(self, timeout_ms: int = None) -> int:
        """
        执行 `set_rx_tx_fallback_standby` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return automatically to STDBY_RC after TX or RX completes.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        self._write_command(
            SX126X_CMD_SET_RX_TX_FALLBACK_MODE,
            bytes((SX126X_FALLBACK_STANDBY_RC,)),
            timeout_ms,
        )
        return self._validated_status(timeout_ms, "SetRxTxFallbackMode")

    def calibrate_all(self, timeout_ms: int = None) -> int:
        """
        执行 `calibrate_all` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Run the complete SX1262 calibration mask.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        self._write_command(SX126X_CMD_CALIBRATE, bytes((SX126X_CALIBRATE_ALL,)), timeout_ms)
        return self._validated_status(timeout_ms, "Calibrate")

    def calibrate_image(self, frequency_mhz: float, timeout_ms: int = None) -> int:
        """
        执行 `calibrate_image` 操作。
        Args:
            frequency_mhz (float): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Apply the Semtech image-calibration pair for the RF frequency.
        Args:
            frequency_mhz (float): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if frequency_mhz is None:
            raise ValueError("frequency_mhz must not be None")
        if not isinstance(frequency_mhz, (int, float)):
            raise TypeError("frequency_mhz must be int or float")
        if not 850.0 <= frequency_mhz <= 930.0:
            raise ValueError("frequency_mhz must be between 850.0 and 930.0")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        calibration = (0xE1, 0xE9) if frequency_mhz > 900.0 else (0xD7, 0xDB)
        self._write_command(SX126X_CMD_CALIBRATE_IMAGE, bytes(calibration), timeout_ms)
        return self._validated_status(timeout_ms, "CalibrateImage")

    def clear_device_errors(self, timeout_ms: int = None) -> int:
        """
        执行 `clear_device_errors` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Clear the SX1262 device-error register before calibration.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        self._write_command(SX126X_CMD_CLEAR_DEVICE_ERRORS, b"\x00\x00", timeout_ms)
        return self._validated_status(timeout_ms, "ClearDeviceErrors")

    def get_device_errors(self, timeout_ms: int = None) -> int:
        """
        执行 `get_device_errors` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return the 16-bit SX1262 device-error flags.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        data = self._read_command(SX126X_CMD_GET_DEVICE_ERRORS, 2, timeout_ms)
        return (data[0] << 8) | data[1]

    def set_packet_type_lora(self, timeout_ms: int = None) -> int:
        """
        执行 `set_packet_type_lora` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Select the LoRa packet type.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        self._write_command(SX126X_CMD_SET_PACKET_TYPE, bytes((0x01,)), timeout_ms)
        return self._validated_status(timeout_ms, "SetPacketType")

    def set_lora_private_sync_word(self, timeout_ms: int = None) -> int:
        """
        执行 `set_lora_private_sync_word` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Set the SX1262 private-network LoRa sync word (0x1424).
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        return self.write_register(
            SX126X_REG_LORA_SYNC_WORD_MSB,
            bytes((SX126X_LORA_SYNC_WORD_PRIVATE_MSB, SX126X_LORA_SYNC_WORD_PRIVATE_LSB)),
            timeout_ms,
        )

    def set_rf_frequency(self, frequency_mhz: float, timeout_ms: int = None) -> int:
        """
        执行 `set_rf_frequency` 操作。
        Args:
            frequency_mhz (float): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Encode and set an SX126X RF frequency in MHz.
        Args:
            frequency_mhz (float): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if frequency_mhz is None:
            raise ValueError("frequency_mhz must not be None")
        if not isinstance(frequency_mhz, (int, float)):
            raise TypeError("frequency_mhz must be int or float")
        if not 150.0 <= frequency_mhz <= 960.0:
            raise ValueError("frequency_mhz must be between 150.0 and 960.0")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        raw = int((frequency_mhz * (1 << 25)) / 32.0)
        payload = bytes(((raw >> 24) & 0xFF, (raw >> 16) & 0xFF, (raw >> 8) & 0xFF, raw & 0xFF))
        self._write_command(SX126X_CMD_SET_RF_FREQUENCY, payload, timeout_ms)
        return self._validated_status(timeout_ms, "SetRfFrequency")

    def set_lora_modulation_params(
        self,
        spreading_factor: int,
        bandwidth_khz: float,
        coding_rate: int,
        timeout_ms: int = None,
    ) -> int:
        """
        执行 `set_lora_modulation_params` 操作。
        Args:
            spreading_factor (int): 方法参数。
            bandwidth_khz (float): 方法参数。
            coding_rate (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Set the supported LoRa modulation parameters.
        Args:
            spreading_factor (int): Method parameter.
            bandwidth_khz (float): Method parameter.
            coding_rate (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if spreading_factor is None:
            raise ValueError("spreading_factor must not be None")
        if not isinstance(spreading_factor, int):
            raise TypeError("spreading_factor must be int")
        if not 5 <= spreading_factor <= 12:
            raise ValueError("spreading_factor must be between 5 and 12")
        if not isinstance(bandwidth_khz, (int, float)):
            raise TypeError("bandwidth_khz must be int or float")
        if abs(float(bandwidth_khz) - 125.0) > 0.001:
            raise ValueError("this driver supports bandwidth_khz=125.0 only")
        if not isinstance(coding_rate, int):
            raise TypeError("coding_rate must be int")
        if not 5 <= coding_rate <= 8:
            raise ValueError("coding_rate must be between 5 and 8")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        coding_rate_raw = coding_rate - 4
        symbol_time_ms = float(1 << spreading_factor) / 125.0
        ldro = SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_ON if symbol_time_ms >= 16.0 else SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_OFF
        payload = bytes((spreading_factor, SX126X_LORA_BW_125_0, coding_rate_raw, ldro))
        self._write_command(SX126X_CMD_SET_MODULATION_PARAMS, payload, timeout_ms)
        return self._validated_status(timeout_ms, "SetModulationParams")

    def set_lora_packet_params(
        self,
        preamble_length: int,
        payload_length: int,
        timeout_ms: int = None,
    ) -> int:
        """
        执行 `set_lora_packet_params` 操作。
        Args:
            preamble_length (int): 方法参数。
            payload_length (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Set explicit-header, CRC-on, standard-IQ LoRa packet parameters.
        Args:
            preamble_length (int): Method parameter.
            payload_length (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if preamble_length is None:
            raise ValueError("preamble_length must not be None")
        if not isinstance(preamble_length, int):
            raise TypeError("preamble_length must be int")
        if not 1 <= preamble_length <= 0xFFFF:
            raise ValueError("preamble_length must be between 1 and 65535")
        if not isinstance(payload_length, int):
            raise TypeError("payload_length must be int")
        if not 0 <= payload_length <= 255:
            raise ValueError("payload_length must be between 0 and 255")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        payload = bytes(
            (
                (preamble_length >> 8) & 0xFF,
                preamble_length & 0xFF,
                SX126X_LORA_HEADER_EXPLICIT,
                payload_length,
                SX126X_LORA_CRC_ON,
                SX126X_LORA_IQ_STANDARD,
            )
        )
        self._write_command(SX126X_CMD_SET_PACKET_PARAMS, payload, timeout_ms)
        return self._validated_status(timeout_ms, "SetPacketParams")

    def set_sx1262_pa_config(self, timeout_ms: int = None) -> int:
        """
        执行 `set_sx1262_pa_config` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Apply the Semtech/GraftSense high-power SX1262 PA configuration.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        payload = bytes(
            (
                SX1262_PA_DUTY_CYCLE_22_DBM,
                SX1262_PA_HP_MAX_22_DBM,
                SX1262_PA_DEVICE_SEL,
                SX1262_PA_LUT,
            )
        )
        self._write_command(SX126X_CMD_SET_PA_CONFIG, payload, timeout_ms)
        return self._validated_status(timeout_ms, "SetPaConfig")

    def set_tx_params(
        self,
        output_power_dbm: int,
        ramp_time: int = SX126X_PA_RAMP_200_US,
        timeout_ms: int = None,
    ) -> int:
        """
        执行 `set_tx_params` 操作。
        Args:
            output_power_dbm (int): 方法参数。
            ramp_time (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Set signed SX1262 TX power and the validated ramp-time code.
        Args:
            output_power_dbm (int): Method parameter.
            ramp_time (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if output_power_dbm is None:
            raise ValueError("output_power_dbm must not be None")
        if not isinstance(output_power_dbm, int):
            raise TypeError("output_power_dbm must be int")
        if not -9 <= output_power_dbm <= 22:
            raise ValueError("output_power_dbm must be between -9 and 22")
        if not isinstance(ramp_time, int):
            raise TypeError("ramp_time must be int")
        if not 0x00 <= ramp_time <= 0x07:
            raise ValueError("ramp_time must be a valid SX126X ramp code")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        payload = bytes((output_power_dbm & 0xFF, ramp_time))
        self._write_command(SX126X_CMD_SET_TX_PARAMS, payload, timeout_ms)
        return self._validated_status(timeout_ms, "SetTxParams")

    def read_register(self, address: int, length: int = 1, timeout_ms: int = None) -> bytes:
        """
        执行 `read_register` 操作。
        Args:
            address (int): 方法参数。
            length (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            bytes: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Read a bounded number of SX126X register bytes.
        Args:
            address (int): Method parameter.
            length (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            bytes: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if address is None:
            raise ValueError("address must not be None")
        if not isinstance(address, int):
            raise TypeError("address must be int")
        if not 0 <= address <= 0xFFFF:
            raise ValueError("address must be between 0 and 0xFFFF")
        if not isinstance(length, int):
            raise TypeError("length must be int")
        if not 1 <= length <= 255:
            raise ValueError("length must be between 1 and 255")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        parameters = bytes(((address >> 8) & 0xFF, address & 0xFF))
        return self._read_command(SX126X_CMD_READ_REGISTER, length, timeout_ms, parameters)

    def write_register(self, address: int, data: bytes, timeout_ms: int = None) -> int:
        """
        执行 `write_register` 操作。
        Args:
            address (int): 方法参数。
            data (bytes): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Write validated SX126X register bytes.
        Args:
            address (int): Method parameter.
            data (bytes): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if address is None:
            raise ValueError("address must not be None")
        if not isinstance(address, int):
            raise TypeError("address must be int")
        if not 0 <= address <= 0xFFFF:
            raise ValueError("address must be between 0 and 0xFFFF")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        if not 1 <= len(data) <= 255:
            raise ValueError("data length must be between 1 and 255")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        payload = bytes(((address >> 8) & 0xFF, address & 0xFF)) + bytes(data)
        self._write_command(SX126X_CMD_WRITE_REGISTER, payload, timeout_ms)
        return self._validated_status(timeout_ms, "WriteRegister")

    def apply_sx1262_pa_clamp_workaround(self, timeout_ms: int = None) -> int:
        """
        执行 `apply_sx1262_pa_clamp_workaround` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Apply Semtech's SX1262 antenna-mismatch PA clamp workaround.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        current = self.read_register(SX126X_REG_TX_CLAMP_CONFIG, 1, timeout_ms)[0]
        return self.write_register(
            SX126X_REG_TX_CLAMP_CONFIG,
            bytes((current | 0x1E,)),
            timeout_ms,
        )

    def apply_lora_rx_sensitivity_workaround(self, timeout_ms: int = None) -> int:
        """
        执行 `apply_lora_rx_sensitivity_workaround` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Apply the non-500-kHz LoRa sensitivity register workaround.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        current = self.read_register(SX126X_REG_SENSITIVITY_CONFIG, 1, timeout_ms)[0]
        return self.write_register(
            SX126X_REG_SENSITIVITY_CONFIG,
            bytes((current | 0x04,)),
            timeout_ms,
        )

    def configure_tx_irq(self, timeout_ms: int = None) -> int:
        """
        执行 `configure_tx_irq` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Route TX_DONE and TIMEOUT to injected DIO1 only.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        irq_mask = SX126X_IRQ_TX_DONE | SX126X_IRQ_TIMEOUT
        payload = bytes(
            (
                (irq_mask >> 8) & 0xFF,
                irq_mask & 0xFF,
                (SX126X_IRQ_TX_DONE >> 8) & 0xFF,
                SX126X_IRQ_TX_DONE & 0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
            )
        )
        self._write_command(SX126X_CMD_SET_DIO_IRQ_PARAMS, payload, timeout_ms)
        return self._validated_status(timeout_ms, "SetDioIrqParams")

    def configure_rx_irq(self, timeout_ms: int = None) -> int:
        """
        执行 `configure_rx_irq` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Route RX completion, receive errors, and timeout to DIO1.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        irq_mask = SX126X_IRQ_RX_DONE | SX126X_IRQ_HEADER_ERROR | SX126X_IRQ_CRC_ERROR | SX126X_IRQ_TIMEOUT
        payload = bytes(
            (
                (irq_mask >> 8) & 0xFF,
                irq_mask & 0xFF,
                (SX126X_IRQ_RX_DONE >> 8) & 0xFF,
                SX126X_IRQ_RX_DONE & 0xFF,
                0x00,
                0x00,
                0x00,
                0x00,
            )
        )
        self._write_command(SX126X_CMD_SET_DIO_IRQ_PARAMS, payload, timeout_ms)
        return self._validated_status(timeout_ms, "SetDioIrqParams RX")

    def set_buffer_base_address(
        self,
        tx_base: int = 0,
        rx_base: int = 0,
        timeout_ms: int = None,
    ) -> int:
        """
        执行 `set_buffer_base_address` 操作。
        Args:
            tx_base (int): 方法参数。
            rx_base (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Set injected-driver FIFO base addresses.
        Args:
            tx_base (int): Method parameter.
            rx_base (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(tx_base, int) or not isinstance(rx_base, int):
            raise TypeError("buffer base addresses must be int")
        if not 0 <= tx_base <= 255 or not 0 <= rx_base <= 255:
            raise ValueError("buffer base addresses must be between 0 and 255")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        self._write_command(
            SX126X_CMD_SET_BUFFER_BASE_ADDRESS,
            bytes((tx_base, rx_base)),
            timeout_ms,
        )
        return self._validated_status(timeout_ms, "SetBufferBaseAddress")

    def get_irq_status(self, timeout_ms: int = None) -> int:
        """
        执行 `get_irq_status` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Read the 16-bit SX126X IRQ status in normal execution context.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        data = self._read_command(SX126X_CMD_GET_IRQ_STATUS, 2, timeout_ms)
        return (data[0] << 8) | data[1]

    def clear_irq_status(self, irq_mask: int = SX126X_IRQ_ALL, timeout_ms: int = None) -> int:
        """
        执行 `clear_irq_status` 操作。
        Args:
            irq_mask (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Clear selected SX126X IRQ bits.
        Args:
            irq_mask (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if irq_mask is None:
            raise ValueError("irq_mask must not be None")
        if not isinstance(irq_mask, int):
            raise TypeError("irq_mask must be int")
        if not 0 <= irq_mask <= SX126X_IRQ_ALL:
            raise ValueError("irq_mask must be between 0 and 0x03FF")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        self._write_command(
            SX126X_CMD_CLEAR_IRQ_STATUS,
            bytes(((irq_mask >> 8) & 0xFF, irq_mask & 0xFF)),
            timeout_ms,
        )
        return self._validated_status(timeout_ms, "ClearIrqStatus")

    def write_buffer(self, data: bytes, offset: int = 0, timeout_ms: int = None) -> int:
        """
        执行 `write_buffer` 操作。
        Args:
            data (bytes): 方法参数。
            offset (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Write a validated payload to the SX126X FIFO.
        Args:
            data (bytes): Method parameter.
            offset (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if data is None:
            raise ValueError("data must not be None")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        if not isinstance(offset, int):
            raise TypeError("offset must be int")
        if not 0 <= offset <= 255:
            raise ValueError("offset must be between 0 and 255")
        if not 1 <= len(data) <= 255 or offset + len(data) > 256:
            raise ValueError("data must fit inside the 256-byte FIFO")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        self._write_command(SX126X_CMD_WRITE_BUFFER, bytes((offset,)) + bytes(data), timeout_ms)
        return self._validated_status(timeout_ms, "WriteBuffer")

    def get_rx_buffer_status(self, timeout_ms: int = None) -> tuple:
        """
        执行 `get_rx_buffer_status` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            tuple: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return received payload length and FIFO start pointer.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            tuple: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        data = self._read_command(SX126X_CMD_GET_RX_BUFFER_STATUS, 2, timeout_ms)
        return data[0], data[1]

    def read_buffer(self, offset: int, length: int, timeout_ms: int = None) -> bytes:
        """
        执行 `read_buffer` 操作。
        Args:
            offset (int): 方法参数。
            length (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            bytes: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Read bytes from the SX126X FIFO.
        Args:
            offset (int): Method parameter.
            length (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            bytes: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(offset, int) or not 0 <= offset <= 255:
            raise ValueError("offset must be an int between 0 and 255")
        if not isinstance(length, int) or not 1 <= length <= 255:
            raise ValueError("length must be an int between 1 and 255")
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        timeout_ms = self._resolve_timeout(timeout_ms)
        return self._read_command(
            SX126X_CMD_READ_BUFFER,
            length,
            timeout_ms,
            bytes((offset,)),
        )

    def get_packet_status(self, timeout_ms: int = None) -> tuple:
        """
        执行 `get_packet_status` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            tuple: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return LoRa RSSI, SNR, and signal RSSI values.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            tuple: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        timeout_ms = self._resolve_timeout(timeout_ms)
        data = self._read_command(SX126X_CMD_GET_PACKET_STATUS, 3, timeout_ms)
        snr_raw = data[1] if data[1] < 128 else data[1] - 256
        return -data[0] / 2.0, snr_raw / 4.0, -data[2] / 2.0

    def set_tx(self, timeout_ms: int) -> None:
        """
        执行 `set_tx` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Enter TX with a finite 24-bit timeout in 15.625-us units.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            None: No return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is None:
            raise ValueError("timeout_ms must not be None")
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        self._validate_timeout(timeout_ms, "timeout_ms")
        timeout_raw = timeout_ms * 64
        if timeout_raw > 0xFFFFFF:
            raise ValueError("timeout_ms exceeds the SX126X 24-bit timeout")
        payload = bytes(((timeout_raw >> 16) & 0xFF, (timeout_raw >> 8) & 0xFF, timeout_raw & 0xFF))
        self._write_command(SX126X_CMD_SET_TX, payload, timeout_ms)
        self._state = SX126X_STATE_TX

    def set_rx(self, timeout_ms: int) -> None:
        """
        执行 `set_rx` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Enter RX with a finite 24-bit timeout in 15.625-us units.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            None: No return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")
        self._validate_timeout(timeout_ms, "timeout_ms")
        timeout_raw = timeout_ms * 64
        if timeout_raw > 0xFFFFFF:
            raise ValueError("timeout_ms exceeds the SX126X 24-bit timeout")
        payload = bytes(((timeout_raw >> 16) & 0xFF, (timeout_raw >> 8) & 0xFF, timeout_raw & 0xFF))
        self._write_command(SX126X_CMD_SET_RX, payload, timeout_ms)
        self._state = SX126X_STATE_RX

    def wait_for_rx_done(self, timeout_ms: int) -> int:
        """
        执行 `wait_for_rx_done` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            SX126XTimeoutError: 参数、状态或通信异常。
            SX126XStateError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Wait for a receive IRQ and classify its result outside hard IRQ.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            SX126XTimeoutError: Parameter, state, or communication error.
            SX126XStateError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        self._validate_timeout(timeout_ms, "timeout_ms")
        started = ticks_ms()
        while not self._dio1.value():
            if ticks_diff(ticks_ms(), started) >= timeout_ms:
                irq_status = self.get_irq_status(self._busy_timeout_ms)
                self.clear_irq_status(irq_status or SX126X_IRQ_ALL, self._busy_timeout_ms)
                raise SX126XTimeoutError("host timeout waiting for RX_DONE")
            sleep_us(50)
        irq_status = self.get_irq_status(self._busy_timeout_ms)
        if irq_status & SX126X_IRQ_TIMEOUT:
            self.clear_irq_status(irq_status, self._busy_timeout_ms)
            raise SX126XTimeoutError("SX126X reported RX timeout")
        if irq_status & (SX126X_IRQ_HEADER_ERROR | SX126X_IRQ_CRC_ERROR):
            self.clear_irq_status(irq_status, self._busy_timeout_ms)
            raise SX126XStateError("SX126X reported RX packet error")
        if not irq_status & SX126X_IRQ_RX_DONE:
            self.clear_irq_status(irq_status or SX126X_IRQ_ALL, self._busy_timeout_ms)
            raise SX126XStateError("DIO1 asserted without RX_DONE")
        return irq_status

    def wait_for_tx_done(self, timeout_ms: int) -> int:
        """
        执行 `wait_for_tx_done` 操作。
        Args:
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            SX126XTimeoutError: 参数、状态或通信异常。
            SX126XStateError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Poll injected DIO1, then classify TX_DONE/TIMEOUT outside an IRQ handler.
        Args:
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            SX126XTimeoutError: Parameter, state, or communication error.
            SX126XStateError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if timeout_ms is None:
            raise ValueError("timeout_ms must not be None")
        self._validate_timeout(timeout_ms, "timeout_ms")
        started = ticks_ms()
        while True:
            if self._dio1.value():
                sleep_us(100)
                if self._dio1.value():
                    break
            if ticks_diff(ticks_ms(), started) >= timeout_ms:
                irq_status = self.get_irq_status(self._busy_timeout_ms)
                self.clear_irq_status(irq_status or SX126X_IRQ_ALL, self._busy_timeout_ms)
                raise SX126XTimeoutError("host timeout waiting for TX_DONE")
            sleep_us(50)
        irq_status = self.get_irq_status(self._busy_timeout_ms)
        self.clear_irq_status(irq_status or SX126X_IRQ_ALL, self._busy_timeout_ms)
        if irq_status & SX126X_IRQ_TIMEOUT:
            raise SX126XTimeoutError("SX126X reported TX timeout")
        if not irq_status & SX126X_IRQ_TX_DONE:
            raise SX126XStateError("DIO1 asserted without TX_DONE")
        return irq_status

    def deinit(self) -> None:
        """
        标记框架已清理；不释放外部注入资源。
        Args:
            无。
        Returns:
            None: 无返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Mark the framework deinitialized without releasing injected resources.
        Args:
            None.
        Returns:
            None: No return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        self._cs.value(1)
        self._last_initialization_plan = ()
        self._state = SX126X_STATE_DEINITIALIZED

    def _write_command(self, opcode: int, data: bytes, timeout_ms: int) -> None:
        """Write one SX126X command with a bounded BUSY check."""
        if data is None:
            raise ValueError("data must not be None")
        if not isinstance(opcode, int):
            raise TypeError("opcode must be int")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        self._validate_timeout(timeout_ms, "timeout_ms")
        frame = bytearray(1 + len(data))
        frame[0] = opcode
        frame[1:] = data
        self._transfer(frame, None, timeout_ms)

    def _read_command(
        self,
        opcode: int,
        read_length: int,
        timeout_ms: int,
        parameters: bytes = b"",
    ) -> bytes:
        """Read a command response after its mandatory status/dummy byte."""
        if opcode is None:
            raise ValueError("opcode must not be None")
        if not isinstance(opcode, int):
            raise TypeError("opcode must be int")
        if not isinstance(read_length, int):
            raise TypeError("read_length must be int")
        if read_length <= 0:
            raise ValueError("read_length must be greater than zero")
        if not isinstance(parameters, (bytes, bytearray)):
            raise TypeError("parameters must be bytes-like")
        self._validate_timeout(timeout_ms, "timeout_ms")
        tx = bytes((opcode,)) + bytes(parameters) + bytes(1 + read_length)
        rx = bytearray(len(tx))
        self._transfer(tx, rx, timeout_ms)
        status_index = 1 + len(parameters)
        self._check_command_status(
            rx[status_index],
            "read opcode 0x%02X response=%s" % (opcode, bytes(rx)),
        )
        return bytes(rx[-read_length:])

    def _validated_status(self, timeout_ms: int, operation: str) -> int:
        """Read and validate command-status bits for a completed write command."""
        if operation is None:
            raise ValueError("operation must not be None")
        status = self.get_status(timeout_ms)
        self._check_command_status(status, operation)
        return status

    @staticmethod
    def _check_command_status(status: int, operation: str) -> None:
        """Raise for SX126X timeout, invalid-command, and failed-command bits."""
        if status is None:
            raise ValueError("status must not be None")
        if not isinstance(status, int):
            raise TypeError("status must be int")
        if not isinstance(operation, str) or not operation:
            raise ValueError("operation must be a non-empty string")
        command_status = status & 0x0E
        if command_status == SX126X_STATUS_CMD_TIMEOUT:
            raise SX126XTimeoutError("chip command timeout during %s (status=0x%02X)" % (operation, status))
        if command_status == SX126X_STATUS_CMD_INVALID:
            raise SX126XSPIError("invalid chip command during %s (status=0x%02X)" % (operation, status))
        if command_status == SX126X_STATUS_CMD_FAILED:
            raise SX126XSPIError("chip command failed during %s (status=0x%02X)" % (operation, status))

    def _resolve_timeout(self, timeout_ms: int) -> int:
        """Return the default timeout or validate an explicit timeout."""
        if timeout_ms is not None and not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int or None")
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        self._validate_timeout(timeout_ms, "timeout_ms")
        return timeout_ms

    def _transfer(self, tx: bytes, rx: bytearray = None, timeout_ms: int = None) -> None:
        """Perform one CS-framed SPI transaction and wait for BUSY afterward."""
        if tx is None:
            raise ValueError("tx must not be None")
        if not isinstance(tx, (bytes, bytearray)):
            raise TypeError("tx must be bytes-like")
        if rx is not None and len(rx) != len(tx):
            raise ValueError("rx length must match tx length")
        if timeout_ms is None:
            timeout_ms = self._busy_timeout_ms
        self._validate_timeout(timeout_ms, "timeout_ms")

        self.wait_while_busy(timeout_ms, "before SPI command")
        self._cs.value(0)
        try:
            if rx is None:
                self._spi.write(tx)
            else:
                self._spi.write_readinto(tx, rx)
        except OSError as error:
            self._state = SX126X_STATE_ERROR
            raise SX126XSPIError("SPI transfer failed: %s" % error)
        finally:
            self._cs.value(1)
        self.wait_while_busy(timeout_ms, "after SPI command")

    def _log(self, message: str) -> None:
        """Print a debug message only when debugging is enabled."""
        if message is None:
            raise ValueError("message must not be None")
        if not isinstance(message, str):
            raise TypeError("message must be str")
        if self._debug:
            print("[SX126X] %s" % message)

    @staticmethod
    def _validate_spi(spi: object) -> None:
        """Validate the minimum injected SPI interface."""
        if spi is None:
            raise ValueError("spi must not be None")
        if not hasattr(spi, "write"):
            raise TypeError("spi must provide write()")
        if not hasattr(spi, "write_readinto"):
            raise TypeError("spi must provide write_readinto()")

    @staticmethod
    def _validate_pin(pin: object, name: str) -> None:
        """Validate the minimum injected Pin interface."""
        if not isinstance(name, str):
            raise TypeError("name must be str")
        if pin is None:
            raise ValueError("%s must not be None" % name)
        if not hasattr(pin, "value"):
            raise TypeError("%s must provide value()" % name)

    @staticmethod
    def _validate_timeout(timeout_ms: int, name: str) -> None:
        """Validate a positive millisecond timeout."""
        if not isinstance(name, str):
            raise TypeError("name must be str")
        if not isinstance(timeout_ms, int):
            raise TypeError("%s must be int" % name)
        if timeout_ms <= 0:
            raise ValueError("%s must be greater than zero" % name)


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
