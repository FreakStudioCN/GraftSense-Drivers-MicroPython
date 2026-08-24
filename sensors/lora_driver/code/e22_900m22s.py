# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : e22_900m22s.py
# @Description : EBYTE E22-900M22S facade with minimal TX power configuration
# @License : MIT

"""E22-900M22S module facade framework / E22-900M22S 模块适配层框架。"""

__version__ = "1.0.0"
__author__ = "GraftSense contributors; E H Ong; Jan Gromes; FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================
from _sx126x import SX126X_MAX_PACKET_LENGTH
from sx1262 import SX1262


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class E22_900M22S:
    """
    EBYTE E22-900M22S 专用适配层。
    Attributes:
        initialized (bool): 初始化状态。
        state (int): SX1262 状态码。
    Methods:
        initialize(): 初始化 E22 LoRa 参数。
        send(): 发送数据包。
        receive(): 接收数据包并返回 RSSI/SNR。
        deinit(): 清理驱动状态。
    Notes:
        - 强制 850-930 MHz、TCXO 2.2 V、DIO2 RF switch 和 22 dBm 上限。
        - 所有硬件对象由外部注入。
    ==========================================
    EBYTE E22-900M22S-specific facade.
    Attributes:
        initialized (bool): Initialization state.
        state (int): SX1262 state code.
    Methods:
        initialize(): Initialize E22 LoRa parameters.
        send(): Transmit one packet.
        receive(): Receive one packet with RSSI/SNR.
        deinit(): Clear driver state.
    Notes:
        - Enforces 850-930 MHz, TCXO 2.2 V, DIO2 RF switch, and 22 dBm limit.
        - All hardware objects are injected by the caller.
    """

    MIN_FREQUENCY_MHZ = 850.0
    MAX_FREQUENCY_MHZ = 930.0
    MAX_OUTPUT_POWER_DBM = 22
    TCXO_VOLTAGE = 2.2

    __slots__ = ("_radio", "_initialized")

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
        注入组合层创建的硬件对象。
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
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Inject hardware objects created by the composition layer.
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
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if spi is None:
            raise ValueError("spi must not be None")
        self._radio = SX1262(
            spi,
            cs,
            reset,
            busy,
            dio1,
            busy_timeout_ms=busy_timeout_ms,
            debug=debug,
        )
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """
        返回初始化状态。 / Return the initialization state.
        Args:
            无。
        Returns:
            bool: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `initialized` operation.
        Args:
            None.
        Returns:
            bool: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return self._initialized

    @property
    def initialization_plan(self) -> tuple:
        """
        返回初始化步骤骨架。 / Return the initialization-plan skeleton.
        Args:
            无。
        Returns:
            tuple: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `initialization_plan` operation.
        Args:
            None.
        Returns:
            tuple: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return self._radio.last_initialization_plan

    @property
    def state(self) -> int:
        """
        执行 `state` 操作。
        Args:
            无。
        Returns:
            int: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return the current SX1262 state code.
        Args:
            None.
        Returns:
            int: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return self._radio.state

    def build_initialization_plan(
        self,
        frequency_mhz: float,
        bandwidth_khz: float = 125.0,
        spreading_factor: int = 9,
        coding_rate: int = 7,
        output_power_dbm: int = 14,
        preamble_length: int = 8,
        use_regulator_ldo: bool = False,
    ) -> tuple:
        """
        生成已应用 E22 板级约束的初始化计划。
        Args:
            frequency_mhz (float): 方法参数。
            bandwidth_khz (float): 方法参数。
            spreading_factor (int): 方法参数。
            coding_rate (int): 方法参数。
            output_power_dbm (int): 方法参数。
            preamble_length (int): 方法参数。
            use_regulator_ldo (bool): 方法参数。
        Returns:
            tuple: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Build an initialization plan with E22 board constraints applied.
        Args:
            frequency_mhz (float): Method parameter.
            bandwidth_khz (float): Method parameter.
            spreading_factor (int): Method parameter.
            coding_rate (int): Method parameter.
            output_power_dbm (int): Method parameter.
            preamble_length (int): Method parameter.
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
        self._validate_e22_frequency(frequency_mhz)
        return self._radio.build_lora_initialization_plan(
            frequency_mhz,
            bandwidth_khz,
            spreading_factor,
            coding_rate,
            output_power_dbm,
            preamble_length,
            self.TCXO_VOLTAGE,
            True,
            use_regulator_ldo,
        )

    def initialize(
        self,
        frequency_mhz: float,
        bandwidth_khz: float = 125.0,
        spreading_factor: int = 9,
        coding_rate: int = 7,
        output_power_dbm: int = 14,
        preamble_length: int = 8,
        use_regulator_ldo: bool = False,
    ) -> None:
        """
        执行 E22-900M22S LoRa TX/RX 初始化。
        Args:
            frequency_mhz (float): 方法参数。
            bandwidth_khz (float): 方法参数。
            spreading_factor (int): 方法参数。
            coding_rate (int): 方法参数。
            output_power_dbm (int): 方法参数。
            preamble_length (int): 方法参数。
            use_regulator_ldo (bool): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Initialize E22-900M22S LoRa TX/RX operation.
        Args:
            frequency_mhz (float): Method parameter.
            bandwidth_khz (float): Method parameter.
            spreading_factor (int): Method parameter.
            coding_rate (int): Method parameter.
            output_power_dbm (int): Method parameter.
            preamble_length (int): Method parameter.
            use_regulator_ldo (bool): Method parameter.
        Returns:
            None: No return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if frequency_mhz is None:
            raise ValueError("frequency_mhz must not be None")
        self._validate_e22_frequency(frequency_mhz)
        self._initialized = False
        self._radio.initialize_lora(
            frequency_mhz,
            bandwidth_khz,
            spreading_factor,
            coding_rate,
            output_power_dbm,
            preamble_length,
            self.TCXO_VOLTAGE,
            True,
            use_regulator_ldo,
        )
        self._initialized = True

    def send(self, data: bytes, timeout_ms: int) -> int:
        """
        阻塞发送并等待 TX_DONE。 / Transmit and block until TX_DONE.
        Args:
            data (bytes): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            RuntimeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `send` operation.
        Args:
            data (bytes): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            RuntimeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if data is None:
            raise ValueError("data must not be None")
        self._validate_payload(data)
        self._validate_timeout(timeout_ms)
        if not self._initialized:
            raise RuntimeError("device must be initialized before send")
        return self._radio.transmit(data, timeout_ms)

    def receive(self, max_length: int = 255, timeout_ms: int = 3000) -> tuple:
        """
        阻塞接收一个数据包并返回 payload、RSSI、SNR。
        Args:
            max_length (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            tuple: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
            RuntimeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `receive` operation.
        Args:
            max_length (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            tuple: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
            RuntimeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if max_length is None:
            raise ValueError("max_length must not be None")
        if not isinstance(max_length, int):
            raise TypeError("max_length must be int")
        if not 1 <= max_length <= SX126X_MAX_PACKET_LENGTH:
            raise ValueError("max_length must be between 1 and 255")
        self._validate_timeout(timeout_ms)
        if not self._initialized:
            raise RuntimeError("device must be initialized before receive")
        return self._radio.receive_packet(max_length, timeout_ms)

    def deinit(self) -> None:
        """
        清理框架状态，不释放注入资源。 / Clear state without releasing injected resources.
        Args:
            无。
        Returns:
            None: 无返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `deinit` operation.
        Args:
            None.
        Returns:
            None: No return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        self._initialized = False
        self._radio.deinit()

    @classmethod
    def _validate_e22_frequency(cls, frequency_mhz: float) -> None:
        """Validate the E22-900M22S module frequency range."""
        if frequency_mhz is None:
            raise ValueError("frequency_mhz must not be None")
        if not isinstance(frequency_mhz, (int, float)):
            raise TypeError("frequency_mhz must be int or float")
        if not cls.MIN_FREQUENCY_MHZ <= frequency_mhz <= cls.MAX_FREQUENCY_MHZ:
            raise ValueError("frequency_mhz must be between 850.0 and 930.0")

    @staticmethod
    def _validate_payload(data: bytes) -> None:
        """Validate a radio payload without performing I/O."""
        if data is None:
            raise ValueError("data must not be None")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        if not 1 <= len(data) <= SX126X_MAX_PACKET_LENGTH:
            raise ValueError("data length must be between 1 and 255")

    @staticmethod
    def _validate_timeout(timeout_ms: int) -> None:
        """Validate a positive operation timeout."""
        if not isinstance(timeout_ms, int):
            raise TypeError("timeout_ms must be int")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
