# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:30
# @Author  : December
# @File    : mfym1s99.py
# @Description : 敏源 MFYM-1S-9-9 单点柔性压力传感器 UART 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "December"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const

# ======================================== 全局变量 ============================================

_MAX_LINE_BYTES = const(1024)
_TRIMMED_BUFFER_BYTES = const(512)

# ======================================== 功能函数 ============================================


def _validate_positive_int(value: int, name: str) -> None:
    """校验正整数参数。"""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("%s must be int" % name)
    if value <= 0:
        raise ValueError("%s must be greater than zero" % name)


def _validate_non_negative_int(value: int, name: str) -> None:
    """校验非负整数参数。"""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("%s must be int" % name)
    if value < 0:
        raise ValueError("%s must not be negative" % name)


def _validate_number(value: object, name: str) -> float:
    """校验数值参数并转换为浮点数。"""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("%s must be int or float" % name)
    return float(value)


def _extract_number(text: str) -> object:
    """从带单位文本中提取首个浮点数，失败时返回 None。"""
    if not isinstance(text, str):
        raise ValueError("text must be str")

    text = text.strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        pass

    allowed = "0123456789+-.eE"
    start = -1
    for index, char in enumerate(text):
        if char in "0123456789+-.":
            start = index
            break

    if start < 0:
        return None

    end = start
    while end < len(text) and text[end] in allowed:
        end += 1

    try:
        return float(text[start:end])
    except ValueError:
        return None


# ======================================== 自定义类 ============================================


class MFYM1S99:
    """
    敏源 MFYM-1S-9-9 单点柔性压力传感器驱动类。

    Attributes:
        _uart (object): 由调用方创建并注入的 UART 实例。
        _timeout_ms (int): 单次读取超时时间，单位毫秒。
        _value_key (str): 用作压力输入的字段名称，默认使用 S。
        _zero_raw (float): 空载零点原始值。

    Methods:
        parse_line(): 解析传感器 ASCII 数据帧。
        read_sample(): 读取一帧结构化数据。
        zero(): 执行稳健空载置零。
        read_pressure_kpa(): 读取标定后的压力值。
        set_two_point_calibration(): 设置两点线性标定。
        deinit(): 释放驱动持有的资源引用。

    Notes:
        - UART 必须由调用方创建并注入，驱动不会修改其配置。
        - 实测帧格式为 S/R/C0/C3/T 字段组成的 ASCII 文本。
        - 标称灵敏度换算仅用于快速验证，精准测量应执行两点标定。
        - 公共读取方法会轮询 UART，不适合在 ISR 中调用。

    ==========================================
    MYSENTECH MFYM-1S-9-9 single-point flexible pressure sensor driver.

    Attributes:
        _uart (object): UART instance created and injected by the caller.
        _timeout_ms (int): Read timeout in milliseconds.
        _value_key (str): Field selected as pressure input, default S.
        _zero_raw (float): Unloaded raw baseline.

    Methods:
        parse_line(): Parse an ASCII sensor frame.
        read_sample(): Read one structured sample.
        zero(): Perform robust unloaded zeroing.
        read_pressure_kpa(): Read calibrated pressure.
        set_two_point_calibration(): Configure two-point calibration.
        deinit(): Release resources held by the driver.

    Notes:
        - UART is created and configured by the caller.
        - The measured frame contains S/R/C0/C3/T ASCII fields.
        - Nominal sensitivity conversion is for evaluation only.
        - Public read methods poll UART and are not ISR-safe.
    """

    BAUDRATE = const(115200)
    DEFAULT_TIMEOUT_MS = const(2000)
    DEFAULT_VALUE_INDEX = const(0)
    DEFAULT_ZERO_SAMPLES = const(7)
    DEFAULT_DISCARD_SAMPLES = const(5)

    __slots__ = (
        "_uart",
        "_timeout_ms",
        "_value_index",
        "_value_key",
        "_sensitivity",
        "_polarity",
        "_zero_raw",
        "_linear_slope",
        "_linear_offset",
        "_rx_buffer",
        "_debug",
    )

    def __init__(
        self,
        uart: object,
        value_key: str = "s",
        value_index: int = DEFAULT_VALUE_INDEX,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        sensitivity: float = 0.36,
        polarity: int = 1,
        debug: bool = False,
    ) -> None:
        """
        初始化 MFYM-1S-9-9 驱动。

        Args:
            uart (object): 已配置为 115200、8N1 的 UART 实例。
            value_key (str): 压力敏感字段名，默认 ``s``；传入 None 时按索引取值。
            value_index (int): 无字段名时使用的数值索引。
            timeout_ms (int): UART 读取超时时间，单位毫秒。
            sensitivity (float): 相对电容变化灵敏度，单位 kPa^-1。
            polarity (int): 原始值随压力升高时为 1，降低时为 -1。
            debug (bool): 是否输出驱动调试信息。

        Returns:
            None

        Raises:
            ValueError: 参数类型、范围或 UART 能力不符合要求。

        Notes:
            - 副作用：保存 UART 引用，但不创建或重新配置 UART。
            - ISR-safe: 否。

        ==========================================
        Initialize the MFYM-1S-9-9 driver.

        Args:
            uart (object): UART configured for 115200 baud and 8N1.
            value_key (str): Pressure field name, default ``s``; None selects by index.
            value_index (int): Numeric index used when value_key is None.
            timeout_ms (int): UART read timeout in milliseconds.
            sensitivity (float): Relative sensitivity in kPa^-1.
            polarity (int): 1 when raw value rises with pressure, otherwise -1.
            debug (bool): Enable driver debug messages.

        Returns:
            None

        Raises:
            ValueError: Invalid parameter or UART capability.

        Notes:
            - Side effect: Stores the UART reference without reconfiguring it.
            - ISR-safe: No.
        """
        if uart is None:
            raise ValueError("uart must not be None")
        if not hasattr(uart, "any") or not hasattr(uart, "read"):
            raise ValueError("uart must provide any() and read()")
        if value_key is not None and not isinstance(value_key, str):
            raise ValueError("value_key must be str or None")
        _validate_non_negative_int(value_index, "value_index")
        _validate_positive_int(timeout_ms, "timeout_ms")
        sensitivity_value = _validate_number(sensitivity, "sensitivity")
        if sensitivity_value <= 0:
            raise ValueError("sensitivity must be greater than zero")
        if not isinstance(polarity, int) or isinstance(polarity, bool) or polarity not in (-1, 1):
            raise ValueError("polarity must be 1 or -1")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._uart = uart
        self._timeout_ms = timeout_ms
        self._value_index = value_index
        self._value_key = value_key.lower() if value_key else None
        self._sensitivity = sensitivity_value
        self._polarity = polarity
        self._zero_raw = None
        self._linear_slope = None
        self._linear_offset = None
        self._rx_buffer = b""
        self._debug = debug

    @classmethod
    def parse_line(cls, data: object) -> object:
        """
        解析一行 UART ASCII 数据。

        Args:
            data (object): bytes 或 str 类型的数据行。

        Returns:
            dict: 包含 raw、line、values、fields 和可选 temperature_c。
            None: 数据行为空白。

        Raises:
            ValueError: data 不是 bytes 或 str。

        Notes:
            - 副作用：无。
            - ISR-safe: 否，解析过程会创建对象。

        ==========================================
        Parse one UART ASCII line.

        Args:
            data (object): Input line as bytes or str.

        Returns:
            dict: Parsed raw, line, values, fields, and optional temperature_c.
            None: The line is blank.

        Raises:
            ValueError: data is not bytes or str.

        Notes:
            - Side effects: None.
            - ISR-safe: No, parsing allocates objects.
        """
        if isinstance(data, (bytes, str)) is False:
            raise ValueError("data must be bytes or str")

        if isinstance(data, bytes):
            raw = data
            try:
                line = data.decode("utf-8").strip()
            except UnicodeError:
                line = data.decode("ascii", "ignore").strip()
        else:
            line = data.strip()
            raw = line.encode()

        if not line:
            return None

        # 将实测分号分隔符和制表符统一转换为逗号。
        normalized = line.replace(";", ",").replace("\t", ",")
        if "," not in normalized:
            normalized = normalized.replace(" ", ",")

        values = []
        fields = {}
        for token in normalized.split(","):
            token = token.strip()
            if not token:
                continue

            separator = "=" if "=" in token else (":" if ":" in token else None)
            if separator:
                key, value_text = token.split(separator, 1)
                value = _extract_number(value_text)
                if value is not None:
                    fields[key.strip().lower()] = value
                    values.append(value)
            else:
                value = _extract_number(token)
                if value is not None:
                    values.append(value)

        sample = {
            "raw": raw,
            "line": line,
            "values": tuple(values),
            "fields": fields,
        }
        if "t" in fields:
            # 实测固件的温度字段以摄氏度的 100 倍输出。
            sample["temperature_c"] = fields["t"] / 100.0
        return sample

    @staticmethod
    def field(sample: dict, name: str, default: object = None) -> object:
        """
        获取结构化样本中的命名字段。

        Args:
            sample (dict): parse_line() 返回的样本。
            name (str): 字段名称，不区分大小写。
            default (object): 字段不存在时的默认值。

        Returns:
            object: 字段值或默认值。

        Raises:
            ValueError: sample 或 name 类型错误。

        Notes:
            - 副作用：无。
            - ISR-safe: 否。

        ==========================================
        Get a named field from a structured sample.

        Args:
            sample (dict): Sample returned by parse_line().
            name (str): Case-insensitive field name.
            default (object): Value returned when the field is absent.

        Returns:
            object: Field value or default value.

        Raises:
            ValueError: Invalid sample or name type.

        Notes:
            - Side effects: None.
            - ISR-safe: No.
        """
        if isinstance(sample, dict) is False:
            raise ValueError("sample must be dict")
        if isinstance(name, str) is False:
            raise ValueError("name must be str")
        return sample.get("fields", {}).get(name.lower(), default)

    @staticmethod
    def temperature_c(sample: dict) -> object:
        """
        获取样本温度。

        Args:
            sample (dict): parse_line() 返回的样本。

        Returns:
            float: 温度，单位摄氏度。
            None: 帧中没有温度字段。

        Raises:
            ValueError: sample 不是 dict。

        Notes:
            - 副作用：无。
            - ISR-safe: 否。

        ==========================================
        Get sample temperature.

        Args:
            sample (dict): Sample returned by parse_line().

        Returns:
            float: Temperature in degrees Celsius.
            None: Temperature field is unavailable.

        Raises:
            ValueError: sample is not dict.

        Notes:
            - Side effects: None.
            - ISR-safe: No.
        """
        if isinstance(sample, dict) is False:
            raise ValueError("sample must be dict")
        return sample.get("temperature_c")

    def clear(self, max_wait_ms: int = 50) -> None:
        """
        清空待处理的 UART 数据，且不会无限追随连续数据流。

        Args:
            max_wait_ms (int): 最大清空时间，单位毫秒。

        Returns:
            None

        Raises:
            ValueError: max_wait_ms 不是正整数。
            RuntimeError: UART 读取失败。

        Notes:
            - 副作用：丢弃 UART 缓冲区内尚未处理的数据。
            - ISR-safe: 否。

        ==========================================
        Clear pending UART data without following a stream forever.

        Args:
            max_wait_ms (int): Maximum clear duration in milliseconds.

        Returns:
            None

        Raises:
            ValueError: max_wait_ms is not a positive integer.
            RuntimeError: UART read failed.

        Notes:
            - Side effect: Discards pending UART data.
            - ISR-safe: No.
        """
        if not isinstance(max_wait_ms, int) or isinstance(max_wait_ms, bool) or max_wait_ms <= 0:
            raise ValueError("max_wait_ms must be positive int")
        self._ensure_active()
        self._rx_buffer = b""
        started = time.ticks_ms()

        try:
            while time.ticks_diff(time.ticks_ms(), started) < max_wait_ms:
                available = self._uart.any()
                if not available:
                    break
                self._uart.read(available)
        except OSError:
            raise RuntimeError("UART clear failed")

    def read_raw_line(self, timeout_ms: object = None) -> object:
        """
        读取一行完整的 UART 原始数据。

        Args:
            timeout_ms (object): 超时时间；None 使用初始化配置。

        Returns:
            bytes: 包含换行符的完整数据行。
            None: 超时前未收到完整行。

        Raises:
            ValueError: timeout_ms 类型或范围错误。
            RuntimeError: UART 读取失败或驱动已释放。

        Notes:
            - 副作用：消费 UART 接收数据并更新内部缓冲区。
            - ISR-safe: 否。

        ==========================================
        Read one complete raw UART line.

        Args:
            timeout_ms (object): Timeout; None uses the configured value.

        Returns:
            bytes: Complete line including its newline.
            None: No complete line before timeout.

        Raises:
            ValueError: Invalid timeout_ms.
            RuntimeError: UART read failed or driver is deinitialized.

        Notes:
            - Side effect: Consumes UART input and updates the receive buffer.
            - ISR-safe: No.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be positive int or None")

        if timeout_ms is not None:
            timeout = timeout_ms
        else:
            timeout = self._timeout_ms

        self._ensure_active()
        started = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), started) < timeout:
            newline = self._rx_buffer.find(b"\n")
            if newline >= 0:
                line = self._rx_buffer[: newline + 1]
                self._rx_buffer = self._rx_buffer[newline + 1 :]
                return line

            try:
                available = self._uart.any()
                if available:
                    chunk = self._uart.read(available)
                    if chunk:
                        self._rx_buffer += chunk
                        if len(self._rx_buffer) > _MAX_LINE_BYTES:
                            # 异常无终止符数据只保留末尾，防止内存持续增长。
                            self._rx_buffer = self._rx_buffer[-_TRIMMED_BUFFER_BYTES:]
                else:
                    time.sleep_ms(1)
            except OSError:
                raise RuntimeError("UART read failed")
        return None

    def read_sample(self, timeout_ms: object = None) -> object:
        """
        读取并解析下一帧有效样本，自动忽略空格帧。

        Args:
            timeout_ms (object): 超时时间；None 使用初始化配置。

        Returns:
            dict: 结构化样本。
            None: 超时前未收到有效样本。

        Raises:
            ValueError: timeout_ms 类型或范围错误。
            RuntimeError: UART 通信失败。

        Notes:
            - 副作用：消费 UART 接收数据。
            - ISR-safe: 否。

        ==========================================
        Read and parse the next valid sample while skipping blank frames.

        Args:
            timeout_ms (object): Timeout; None uses the configured value.

        Returns:
            dict: Structured sample.
            None: No valid sample before timeout.

        Raises:
            ValueError: Invalid timeout_ms.
            RuntimeError: UART communication failed.

        Notes:
            - Side effect: Consumes UART input.
            - ISR-safe: No.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be positive int or None")

        if timeout_ms is not None:
            timeout = timeout_ms
        else:
            timeout = self._timeout_ms

        started = time.ticks_ms()
        while True:
            elapsed = time.ticks_diff(time.ticks_ms(), started)
            remaining = timeout - elapsed
            if remaining <= 0:
                return None

            raw_line = self.read_raw_line(remaining)
            if raw_line is None:
                return None

            sample = self.parse_line(raw_line)
            if sample is not None and sample["values"]:
                return sample

    def sample_value(self, sample: dict) -> float:
        """
        从样本中选择配置的压力输入值。

        Args:
            sample (dict): parse_line() 返回的结构化样本。

        Returns:
            float: 选中的原始值。

        Raises:
            ValueError: 样本无效或目标字段不存在。

        Notes:
            - 副作用：无。
            - ISR-safe: 否。

        ==========================================
        Select the configured pressure input from a sample.

        Args:
            sample (dict): Structured sample returned by parse_line().

        Returns:
            float: Selected raw value.

        Raises:
            ValueError: Invalid sample or missing selected field.

        Notes:
            - Side effects: None.
            - ISR-safe: No.
        """
        if not isinstance(sample, dict):
            raise ValueError("sample must be dict")

        if self._value_key:
            fields = sample.get("fields", {})
            if self._value_key not in fields:
                raise ValueError("field '%s' not present in: %s" % (self._value_key, sample.get("line", "")))
            return float(fields[self._value_key])

        values = sample.get("values", ())
        if self._value_index >= len(values):
            raise ValueError("value_index %d not present in: %s" % (self._value_index, sample.get("line", "")))
        return float(values[self._value_index])

    def read_raw_value(self, timeout_ms: object = None) -> object:
        """
        读取配置字段的原始值。

        Args:
            timeout_ms (object): 超时时间；None 使用初始化配置。

        Returns:
            float: 原始值。
            None: 读取超时。

        Raises:
            ValueError: timeout_ms 无效或帧缺少目标字段。
            RuntimeError: UART 通信失败。

        Notes:
            - 副作用：消费一帧 UART 数据。
            - ISR-safe: 否。

        ==========================================
        Read the configured raw field.

        Args:
            timeout_ms (object): Timeout; None uses the configured value.

        Returns:
            float: Raw value.
            None: Read timed out.

        Raises:
            ValueError: Invalid timeout or missing selected field.
            RuntimeError: UART communication failed.

        Notes:
            - Side effect: Consumes one UART sample.
            - ISR-safe: No.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be positive int or None")
        sample = self.read_sample(timeout_ms)
        if sample is None:
            return None
        return self.sample_value(sample)

    def average_raw(self, samples: int = 20, interval_ms: int = 10) -> float:
        """
        读取多个有效原始值并计算平均值。

        Args:
            samples (int): 有效样本数量。
            interval_ms (int): 样本间附加延时，单位毫秒。

        Returns:
            float: 原始值平均数。

        Raises:
            ValueError: 参数无效。
            RuntimeError: 未能读取足够样本。

        Notes:
            - 副作用：消费多帧 UART 数据并产生阻塞延时。
            - ISR-safe: 否。

        ==========================================
        Read and average several valid raw values.

        Args:
            samples (int): Number of valid samples.
            interval_ms (int): Additional delay between samples.

        Returns:
            float: Mean raw value.

        Raises:
            ValueError: Invalid parameter.
            RuntimeError: Not enough samples were received.

        Notes:
            - Side effect: Consumes UART frames and blocks while sampling.
            - ISR-safe: No.
        """
        _validate_positive_int(samples, "samples")
        _validate_non_negative_int(interval_ms, "interval_ms")

        total = 0.0
        count = 0
        attempts = 0
        while count < samples and attempts < samples * 3:
            value = self.read_raw_value()
            attempts += 1
            if value is not None:
                total += value
                count += 1
            if interval_ms:
                time.sleep_ms(interval_ms)

        if count != samples:
            raise RuntimeError("UART timeout: received %d of %d samples" % (count, samples))
        return total / count

    def zero(
        self,
        samples: int = DEFAULT_ZERO_SAMPLES,
        discard: int = DEFAULT_DISCARD_SAMPLES,
        interval_ms: int = 10,
        max_spread_ratio: float = 0.10,
    ) -> float:
        """
        使用启动帧丢弃、中位数和稳定性门限执行空载置零。

        Args:
            samples (int): 用于计算中位数的有效样本数量。
            discard (int): 置零前丢弃的有效启动帧数量。
            interval_ms (int): 样本间附加延时，单位毫秒。
            max_spread_ratio (float): 允许的最大极差/中位数比例。

        Returns:
            float: 保存的空载零点。

        Raises:
            ValueError: 参数无效、零点为零或采样不稳定。
            RuntimeError: UART 超时。

        Notes:
            - 副作用：更新零点并清除已有两点标定。
            - ISR-safe: 否。

        ==========================================
        Perform robust unloaded zeroing with discarded startup frames,
        a median, and a stability gate.

        Args:
            samples (int): Valid samples used for the median.
            discard (int): Valid startup frames discarded before zeroing.
            interval_ms (int): Additional delay between samples.
            max_spread_ratio (float): Maximum allowed range-to-median ratio.

        Returns:
            float: Stored unloaded baseline.

        Raises:
            ValueError: Invalid parameter, zero baseline, or unstable data.
            RuntimeError: UART timeout.

        Notes:
            - Side effect: Updates zero baseline and clears two-point calibration.
            - ISR-safe: No.
        """
        _validate_positive_int(samples, "samples")
        if samples < 3:
            raise ValueError("samples must be at least 3")
        _validate_non_negative_int(discard, "discard")
        _validate_non_negative_int(interval_ms, "interval_ms")
        spread_limit = _validate_number(max_spread_ratio, "max_spread_ratio")
        if spread_limit <= 0:
            raise ValueError("max_spread_ratio must be greater than zero")

        discarded = 0
        attempts = 0
        while discarded < discard and attempts < max(1, discard * 3):
            attempts += 1
            if self.read_raw_value() is not None:
                discarded += 1

        if discarded != discard:
            raise RuntimeError("UART timeout while discarding startup samples")

        values = []
        attempts = 0
        while len(values) < samples and attempts < samples * 3:
            attempts += 1
            value = self.read_raw_value()
            if value is not None:
                values.append(value)
            if interval_ms:
                time.sleep_ms(interval_ms)

        if len(values) != samples:
            raise RuntimeError("UART timeout: received %d of %d zero samples" % (len(values), samples))

        values.sort()
        middle = samples // 2
        if samples & 1:
            baseline = values[middle]
        else:
            baseline = (values[middle - 1] + values[middle]) / 2.0

        if baseline == 0:
            raise ValueError("zero reading is 0; use two-point calibration")

        spread_ratio = (values[-1] - values[0]) / abs(baseline)
        if spread_ratio > spread_limit:
            raise ValueError("unstable zero: min=%.1f max=%.1f; keep sensor unloaded" % (values[0], values[-1]))

        self._zero_raw = baseline
        self._linear_slope = None
        self._linear_offset = None
        self._log("zero baseline=%.3f" % baseline)
        return self._zero_raw

    def set_two_point_calibration(
        self,
        raw1: float,
        pressure1_kpa: float,
        raw2: float,
        pressure2_kpa: float,
    ) -> None:
        """
        设置安装后的两点线性压力标定。

        Args:
            raw1 (float): 第一个标定点原始值。
            pressure1_kpa (float): 第一个标定点压力，单位 kPa。
            raw2 (float): 第二个标定点原始值。
            pressure2_kpa (float): 第二个标定点压力，单位 kPa。

        Returns:
            None

        Raises:
            ValueError: 参数不是数值或两个原始值相同。

        Notes:
            - 副作用：更新线性斜率和偏移量。
            - ISR-safe: 否。

        ==========================================
        Configure installation-specific two-point pressure calibration.

        Args:
            raw1 (float): Raw value at the first point.
            pressure1_kpa (float): First pressure in kPa.
            raw2 (float): Raw value at the second point.
            pressure2_kpa (float): Second pressure in kPa.

        Returns:
            None

        Raises:
            ValueError: Non-numeric parameter or identical raw points.

        Notes:
            - Side effect: Updates linear slope and offset.
            - ISR-safe: No.
        """
        raw1_value = _validate_number(raw1, "raw1")
        pressure1_value = _validate_number(pressure1_kpa, "pressure1_kpa")
        raw2_value = _validate_number(raw2, "raw2")
        pressure2_value = _validate_number(pressure2_kpa, "pressure2_kpa")
        if raw2_value == raw1_value:
            raise ValueError("raw calibration points must differ")

        self._linear_slope = (pressure2_value - pressure1_value) / (raw2_value - raw1_value)
        self._linear_offset = pressure1_value - self._linear_slope * raw1_value

    def pressure_from_raw(self, raw: float) -> float:
        """
        将原始压力通道值转换为 kPa。

        Args:
            raw (float): 压力通道原始值。

        Returns:
            float: 压力值，单位 kPa。

        Raises:
            ValueError: raw 不是数值。
            RuntimeError: 尚未置零或设置两点标定。

        Notes:
            - 副作用：无。
            - ISR-safe: 否。

        ==========================================
        Convert a raw pressure-channel value to kPa.

        Args:
            raw (float): Raw pressure-channel value.

        Returns:
            float: Pressure in kPa.

        Raises:
            ValueError: raw is not numeric.
            RuntimeError: Zeroing or two-point calibration is missing.

        Notes:
            - Side effects: None.
            - ISR-safe: No.
        """
        raw_value = _validate_number(raw, "raw")
        if self._linear_slope is not None:
            return self._linear_slope * raw_value + self._linear_offset
        if self._zero_raw is None:
            raise RuntimeError("call zero() or set_two_point_calibration() first")
        return self._polarity * (raw_value / self._zero_raw - 1.0) / self._sensitivity

    def read_pressure_kpa(self, timeout_ms: object = None) -> object:
        """
        读取一帧并返回压力值。

        Args:
            timeout_ms (object): 超时时间；None 使用初始化配置。

        Returns:
            float: 压力值，单位 kPa。
            None: 读取超时。

        Raises:
            ValueError: timeout_ms 无效或帧缺少目标字段。
            RuntimeError: UART 通信失败或尚未标定。

        Notes:
            - 副作用：消费一帧 UART 数据。
            - ISR-safe: 否。

        ==========================================
        Read one sample and return pressure in kPa.

        Args:
            timeout_ms (object): Timeout; None uses the configured value.

        Returns:
            float: Pressure in kPa.
            None: Read timed out.

        Raises:
            ValueError: Invalid timeout or missing selected field.
            RuntimeError: UART failure or missing calibration.

        Notes:
            - Side effect: Consumes one UART sample.
            - ISR-safe: No.
        """
        if timeout_ms is not None and (not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or timeout_ms <= 0):
            raise ValueError("timeout_ms must be positive int or None")
        raw = self.read_raw_value(timeout_ms)
        if raw is None:
            return None
        return self.pressure_from_raw(raw)

    def get_zero_raw(self) -> object:
        """
        获取当前空载零点。

        Returns:
            float: 空载零点。
            None: 尚未置零。

        Notes:
            - 副作用：无。
            - ISR-safe: 是。

        ==========================================
        Get the current unloaded baseline.

        Returns:
            float: Unloaded baseline.
            None: Zeroing has not been performed.

        Notes:
            - Side effects: None.
            - ISR-safe: Yes.
        """
        return self._zero_raw

    def get_sensitivity(self) -> float:
        """
        获取当前标称灵敏度。

        Returns:
            float: 灵敏度，单位 kPa^-1。

        Notes:
            - 副作用：无。
            - ISR-safe: 是。

        ==========================================
        Get nominal sensitivity.

        Returns:
            float: Sensitivity in kPa^-1.

        Notes:
            - Side effects: None.
            - ISR-safe: Yes.
        """
        return self._sensitivity

    def set_sensitivity(self, sensitivity: float) -> None:
        """
        设置标称灵敏度。

        Args:
            sensitivity (float): 正数灵敏度，单位 kPa^-1。

        Returns:
            None

        Raises:
            ValueError: sensitivity 不是正数。

        Notes:
            - 副作用：改变后续标称公式换算结果。
            - ISR-safe: 否。

        ==========================================
        Set nominal sensitivity.

        Args:
            sensitivity (float): Positive sensitivity in kPa^-1.

        Returns:
            None

        Raises:
            ValueError: sensitivity is not positive.

        Notes:
            - Side effect: Changes subsequent nominal conversions.
            - ISR-safe: No.
        """
        sensitivity_value = _validate_number(sensitivity, "sensitivity")
        if sensitivity_value <= 0:
            raise ValueError("sensitivity must be greater than zero")
        self._sensitivity = sensitivity_value

    def _ensure_active(self) -> None:
        """确保驱动仍持有可用 UART 引用。"""
        if self._uart is None:
            raise RuntimeError("driver is deinitialized")

    def _log(self, message: str) -> None:
        """按需输出英文调试信息。"""
        if isinstance(message, str) is False:
            raise ValueError("message must be str")
        if self._debug:
            print("[MFYM1S99] %s" % message)

    def deinit(self) -> None:
        """
        释放驱动内部缓冲区和 UART 引用。

        Returns:
            None

        Notes:
            - 副作用：驱动实例不可再读取；不会调用外部 UART 的 deinit()。
            - ISR-safe: 否。

        ==========================================
        Release the internal buffer and UART reference.

        Returns:
            None

        Notes:
            - Side effect: The driver can no longer read; external UART remains active.
            - ISR-safe: No.
        """
        self._rx_buffer = b""
        self._uart = None


MFYM = MFYM1S99

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
