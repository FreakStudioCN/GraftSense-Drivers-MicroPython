# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : GraftSense contributors and FreakStudio
# @File    : sx1262.py
# @Description : SX1262 LoRa initialization, TX, RX, and PA configuration
# @License : MIT

"""SX1262 chip-layer framework / SX1262 芯片层框架。"""

__version__ = "1.0.0"
__author__ = "GraftSense contributors; E H Ong; Jan Gromes; FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================
from _sx126x import (
    SX126X_CHIP_MAX_FREQUENCY_MHZ,
    SX126X_CHIP_MIN_FREQUENCY_MHZ,
    SX126X_MAX_OUTPUT_POWER_DBM,
    SX126X_PA_RAMP_200_US,
    SX126X_REG_OCP_CONFIGURATION,
)
from sx126x import SX126X, SX126XError, SX126XStateError


# ======================================== 全局变量 ============================================
# 初始化顺序参考 MIT 许可的 GraftSense communication/sx1262_driver。


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class SX1262(SX126X):
    """
    SX1262 LoRa 芯片驱动。
    Attributes:
        state (int): 当前芯片状态码。
        last_initialization_plan (tuple): 最后一次初始化计划。
    Methods:
        initialize_lora(): 初始化 LoRa 工作参数。
        transmit(): 阻塞发送一个数据包。
        receive_packet(): 阻塞接收一个数据包。
        deinit(): 清理 LoRa 状态。
    Notes:
        - 继承 SX126X 的依赖注入 SPI/Pin 传输。
        - 所有等待都有超时上限；非 ISR-safe。
    ==========================================
    SX1262 LoRa radio driver.
    Attributes:
        state (int): Current chip state code.
        last_initialization_plan (tuple): Last initialization plan.
    Methods:
        initialize_lora(): Initialize LoRa operating parameters.
        transmit(): Transmit one packet synchronously.
        receive_packet(): Receive one packet synchronously.
        deinit(): Clear LoRa state.
    Notes:
        - Inherits dependency-injected SPI/Pin transport from SX126X.
        - Every wait is bounded by a timeout; not ISR-safe.
    """

    __slots__ = ("_lora_configured", "_output_power_dbm", "_tx_preamble_length")

    def build_lora_initialization_plan(
        self,
        frequency_mhz: float,
        bandwidth_khz: float = 125.0,
        spreading_factor: int = 9,
        coding_rate: int = 7,
        output_power_dbm: int = 14,
        preamble_length: int = 8,
        tcxo_voltage: float = 1.6,
        enable_dio2_rf_switch: bool = True,
        use_regulator_ldo: bool = False,
    ) -> tuple:
        """
        生成通用 SX1262 LoRa 初始化计划。
        Args:
            frequency_mhz (float): 方法参数。
            bandwidth_khz (float): 方法参数。
            spreading_factor (int): 方法参数。
            coding_rate (int): 方法参数。
            output_power_dbm (int): 方法参数。
            preamble_length (int): 方法参数。
            tcxo_voltage (float): 方法参数。
            enable_dio2_rf_switch (bool): 方法参数。
            use_regulator_ldo (bool): 方法参数。
        Returns:
            tuple: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Build a generic SX1262 LoRa initialization plan.
        Args:
            frequency_mhz (float): Method parameter.
            bandwidth_khz (float): Method parameter.
            spreading_factor (int): Method parameter.
            coding_rate (int): Method parameter.
            output_power_dbm (int): Method parameter.
            preamble_length (int): Method parameter.
            tcxo_voltage (float): Method parameter.
            enable_dio2_rf_switch (bool): Method parameter.
            use_regulator_ldo (bool): Method parameter.
        Returns:
            tuple: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if frequency_mhz is None:
            raise ValueError("frequency_mhz must not be None")
        self._validate_lora_parameters(
            frequency_mhz,
            bandwidth_khz,
            spreading_factor,
            coding_rate,
            output_power_dbm,
            preamble_length,
            tcxo_voltage,
            enable_dio2_rf_switch,
            use_regulator_ldo,
        )

        return (
            ("reset",),
            ("standby",),
            ("set_tcxo", tcxo_voltage),
            ("set_dio2_rf_switch", enable_dio2_rf_switch),
            ("set_regulator_mode", "ldo" if use_regulator_ldo else "dcdc"),
            ("set_buffer_base_address", 0, 0),
            ("set_packet_type", "lora"),
            ("set_rx_tx_fallback", "standby_rc"),
            ("calibrate_all",),
            ("calibrate_image", frequency_mhz),
            ("set_frequency", frequency_mhz),
            (
                "set_lora_parameters",
                bandwidth_khz,
                spreading_factor,
                coding_rate,
                preamble_length,
            ),
            ("set_packet_parameters", preamble_length, 255),
            ("set_sync_word", "private"),
            ("apply_rx_sensitivity_workaround",),
            ("apply_pa_clamp_workaround",),
            ("set_pa_config", 0x04, 0x07, 0x00, 0x01),
            ("set_tx_params", output_power_dbm, SX126X_PA_RAMP_200_US),
            ("clear_irq",),
            ("standby",),
        )

    def initialize_lora(
        self,
        frequency_mhz: float,
        bandwidth_khz: float = 125.0,
        spreading_factor: int = 9,
        coding_rate: int = 7,
        output_power_dbm: int = 14,
        preamble_length: int = 8,
        tcxo_voltage: float = 1.6,
        enable_dio2_rf_switch: bool = True,
        use_regulator_ldo: bool = False,
    ) -> None:
        """
        校验并执行 LoRa 初始化计划。
        Args:
            frequency_mhz (float): 方法参数。
            bandwidth_khz (float): 方法参数。
            spreading_factor (int): 方法参数。
            coding_rate (int): 方法参数。
            output_power_dbm (int): 方法参数。
            preamble_length (int): 方法参数。
            tcxo_voltage (float): 方法参数。
            enable_dio2_rf_switch (bool): 方法参数。
            use_regulator_ldo (bool): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            SX126XStateError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Validate and execute a LoRa initialization plan.
        Args:
            frequency_mhz (float): Method parameter.
            bandwidth_khz (float): Method parameter.
            spreading_factor (int): Method parameter.
            coding_rate (int): Method parameter.
            output_power_dbm (int): Method parameter.
            preamble_length (int): Method parameter.
            tcxo_voltage (float): Method parameter.
            enable_dio2_rf_switch (bool): Method parameter.
            use_regulator_ldo (bool): Method parameter.
        Returns:
            None: No return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            SX126XStateError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if frequency_mhz is None:
            raise ValueError("frequency_mhz must not be None")
        plan = self.build_lora_initialization_plan(
            frequency_mhz,
            bandwidth_khz,
            spreading_factor,
            coding_rate,
            output_power_dbm,
            preamble_length,
            tcxo_voltage,
            enable_dio2_rf_switch,
            use_regulator_ldo,
        )
        if abs(float(tcxo_voltage) - 2.2) > 0.001:
            raise ValueError("E22-900M22S requires tcxo_voltage=2.2")
        if enable_dio2_rf_switch is not True:
            raise ValueError("E22-900M22S requires the DIO2 RF switch")
        self._lora_configured = False
        self.reset()
        self.standby()
        self.set_tcxo_2_2()
        self.set_regulator_mode(use_regulator_ldo)
        self.set_dio2_rf_switch(True)
        self.set_buffer_base_address(0, 0)
        self.set_packet_type_lora()
        self.set_rx_tx_fallback_standby()
        self.clear_irq_status()
        self.clear_device_errors()
        self.calibrate_all()
        self.calibrate_image(frequency_mhz)
        self.set_rf_frequency(frequency_mhz)
        self.set_lora_modulation_params(spreading_factor, bandwidth_khz, coding_rate)
        self.set_lora_packet_params(preamble_length, 255)
        self.set_lora_private_sync_word()
        self.apply_lora_rx_sensitivity_workaround()
        self._configure_output_power(output_power_dbm)
        self.clear_irq_status()
        self.standby()
        device_errors = self.get_device_errors()
        if device_errors:
            raise SX126XStateError("device errors after initialization: 0x%04X" % device_errors)
        self._tx_preamble_length = preamble_length
        self._output_power_dbm = output_power_dbm
        self._last_initialization_plan = plan
        self._lora_configured = True

    def transmit(self, data: bytes, timeout_ms: int) -> int:
        """
        执行 `transmit` 操作。
        Args:
            data (bytes): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
            SX126XStateError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Run the blocking FIFO-to-TX_DONE flow.
        Args:
            data (bytes): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
            SX126XStateError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if data is None:
            raise ValueError("data must not be None")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        if not 1 <= len(data) <= 255:
            raise ValueError("data length must be between 1 and 255")
        self._validate_timeout(timeout_ms, "timeout_ms")
        if not getattr(self, "_lora_configured", False):
            raise SX126XStateError("LoRa must be initialized before transmit")

        self.standby()
        try:
            self.set_lora_packet_params(self._tx_preamble_length, len(data))
            self.configure_tx_irq()
            self.set_buffer_base_address(0, 0)
            self.clear_irq_status()
            self.write_buffer(data, offset=0)
            self.apply_lora_rx_sensitivity_workaround()
            self.set_tx(timeout_ms)
            self.wait_for_tx_done(timeout_ms)
        except SX126XError:
            try:
                self.standby()
            except SX126XError:
                pass
            raise
        self.standby()
        return len(data)

    def receive_packet(self, max_length: int, timeout_ms: int) -> tuple:
        """
        执行 `receive_packet` 操作。
        Args:
            max_length (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            tuple: 方法返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
            ValueError: 参数、状态或通信异常。
            SX126XStateError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Receive one LoRa packet and return payload, RSSI, and SNR.
        Args:
            max_length (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            tuple: Method return value.
        Raises:
            TypeError: Parameter, state, or communication error.
            ValueError: Parameter, state, or communication error.
            SX126XStateError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(max_length, int):
            raise TypeError("max_length must be int")
        if not 1 <= max_length <= 255:
            raise ValueError("max_length must be between 1 and 255")
        self._validate_timeout(timeout_ms, "timeout_ms")
        if not getattr(self, "_lora_configured", False):
            raise SX126XStateError("LoRa must be initialized before receive")

        self.standby()
        try:
            self.set_lora_packet_params(self._tx_preamble_length, max_length)
            self.configure_rx_irq()
            self.set_buffer_base_address(0, 0)
            self.clear_irq_status()
            self.apply_lora_rx_sensitivity_workaround()
            self.set_rx(timeout_ms)
            irq_status = self.wait_for_rx_done(timeout_ms)
            payload_length, start_pointer = self.get_rx_buffer_status()
            if payload_length > max_length:
                raise SX126XStateError("received payload exceeds max_length")
            payload = self.read_buffer(start_pointer, payload_length)
            rssi_dbm, snr_db, _ = self.get_packet_status()
            self.clear_irq_status(irq_status)
        except SX126XError:
            try:
                self.standby()
            except SX126XError:
                pass
            raise
        self.standby()
        return payload, rssi_dbm, snr_db

    def deinit(self) -> None:
        """
        执行 `deinit` 操作。
        Args:
            无。
        Returns:
            None: 无返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Clear the minimal LoRa configuration and inherited transport state.
        Args:
            None.
        Returns:
            None: No return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        self._lora_configured = False
        super().deinit()

    def _configure_output_power(self, output_power_dbm: int) -> None:
        """Configure SX1262 PA and TX params while preserving the OCP register."""
        if output_power_dbm is None:
            raise ValueError("output_power_dbm must not be None")
        if not isinstance(output_power_dbm, int):
            raise TypeError("output_power_dbm must be int")
        if not -9 <= output_power_dbm <= SX126X_MAX_OUTPUT_POWER_DBM:
            raise ValueError("output_power_dbm must be between -9 and 22")

        ocp_value = self.read_register(SX126X_REG_OCP_CONFIGURATION, 1)
        try:
            self.apply_sx1262_pa_clamp_workaround()
            self.set_sx1262_pa_config()
            self.set_tx_params(output_power_dbm, SX126X_PA_RAMP_200_US)
        except SX126XError:
            try:
                self.write_register(SX126X_REG_OCP_CONFIGURATION, ocp_value)
            except SX126XError:
                pass
            raise
        self.write_register(SX126X_REG_OCP_CONFIGURATION, ocp_value)

    @staticmethod
    def _validate_lora_parameters(
        frequency_mhz: float,
        bandwidth_khz: float,
        spreading_factor: int,
        coding_rate: int,
        output_power_dbm: int,
        preamble_length: int,
        tcxo_voltage: float,
        enable_dio2_rf_switch: bool,
        use_regulator_ldo: bool,
    ) -> None:
        """Validate the generic SX1262 LoRa configuration."""
        if not isinstance(frequency_mhz, (int, float)):
            raise TypeError("frequency_mhz must be int or float")
        if not SX126X_CHIP_MIN_FREQUENCY_MHZ <= frequency_mhz <= SX126X_CHIP_MAX_FREQUENCY_MHZ:
            raise ValueError("frequency_mhz must be between 150.0 and 960.0")
        if not isinstance(bandwidth_khz, (int, float)):
            raise TypeError("bandwidth_khz must be int or float")
        if abs(float(bandwidth_khz) - 125.0) > 0.001:
            raise ValueError("this driver supports bandwidth_khz=125.0 only")
        if not isinstance(spreading_factor, int):
            raise TypeError("spreading_factor must be int")
        if not 5 <= spreading_factor <= 12:
            raise ValueError("spreading_factor must be between 5 and 12")
        if not isinstance(coding_rate, int):
            raise TypeError("coding_rate must be int")
        if not 5 <= coding_rate <= 8:
            raise ValueError("coding_rate must be between 5 and 8")
        if not isinstance(output_power_dbm, int):
            raise TypeError("output_power_dbm must be int")
        if not -9 <= output_power_dbm <= SX126X_MAX_OUTPUT_POWER_DBM:
            raise ValueError("output_power_dbm must be between -9 and 22")
        if not isinstance(preamble_length, int):
            raise TypeError("preamble_length must be int")
        if preamble_length <= 0:
            raise ValueError("preamble_length must be greater than zero")
        if not isinstance(tcxo_voltage, (int, float)):
            raise TypeError("tcxo_voltage must be int or float")
        if tcxo_voltage < 0:
            raise ValueError("tcxo_voltage must not be negative")
        if not isinstance(enable_dio2_rf_switch, bool):
            raise TypeError("enable_dio2_rf_switch must be bool")
        if not isinstance(use_regulator_ldo, bool):
            raise TypeError("use_regulator_ldo must be bool")


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
