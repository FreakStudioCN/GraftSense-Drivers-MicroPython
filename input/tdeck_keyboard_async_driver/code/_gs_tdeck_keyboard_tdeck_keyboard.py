# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/21 00:00
# @Author  : FreakStudio
# @File    : tdeck_keyboard.py
# @Description : LILYGO T-Deck Plus 板载 T-Keyboard 驱动（I2C 0x55，ESP32-C3 键盘控制器）
# @License : MIT

__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# 导入相关模块
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import time

try:
    from machine import Pin
except ImportError:
    Pin = None

# 全局变量
# 键盘控制器 I2C 地址（ESP32-C3 从机）
TDECK_KEYBOARD_ADDR = const(0x55)

# 协议命令
# 设置背光亮度（0..255）
CMD_BRIGHTNESS = const(0x01)
# 设置 Alt+B 默认亮度（31..255）
CMD_ALT_B_BRIGHTNESS = const(0x02)
# 切换到 raw matrix 模式
CMD_MODE_RAW = const(0x03)
# 切换到普通按键模式
CMD_MODE_KEY = const(0x04)

# 特殊键码
# 无按键
KEY_NONE = const(0x00)
# 退格键
KEY_BACKSPACE = const(0x08)
# 回车键
KEY_ENTER = const(0x0D)
# Alt+C 组合键
KEY_ALT_C = const(0x0C)

# Raw 模式矩阵尺寸
RAW_COLUMNS = const(5)
RAW_ROWS = const(7)

# 功能函数

# 自定义类

# 键盘矩阵：5 列 × 7 行（普通模式）
KEY_MATRIX = (
    ("q", "w", None, "a", None, " ", None),
    ("e", "s", "d", "p", "x", "z", None),
    ("r", "g", "t", None, "v", "c", "f"),
    ("u", "h", "y", None, "b", "n", "j"),
    ("o", "l", "i", None, "$", "m", "k"),
)

# 符号层矩阵（按下 symbol 键时生效）
SYMBOL_MATRIX = (
    ("#", "1", None, "*", None, None, "0"),
    ("2", "4", "5", "@", "8", "7", None),
    ("3", "/", "(", None, "?", "9", "6"),
    ("_", ":", ")", None, "!", ",", ";"),
    ("+", '"', "-", None, None, ".", "'"),
)

# 特殊功能键位置映射 (col, row) -> 名称
SPECIAL_POSITIONS = {
    (0, 2): "symbol",
    (0, 4): "alt",
    (0, 6): "mic",
    (1, 6): "left_shift",
    (2, 3): "right_shift",
    (3, 3): "enter",
    (4, 3): "backspace",
}


class TDeckKeyboard:
    """
    LILYGO T-Deck Plus 板载 T-Keyboard I2C 驱动

    键盘控制器为板载 ESP32-C3 运行 LILYGO 官方固件，主控 ESP32-S3 通过
    I2C 地址 0x55 与其通信。普通模式下读取 1 字节：0x00 表示无按键，否则
    返回 ASCII 或控制字符。Raw 模式读取 5 字节，每字节对应一列，bit0..bit6
    对应 7 行。支持背光亮度控制和模式切换。

    Attributes:
        address (int): 设备 I2C 地址
        _i2c (I2C): I2C 总线实例
        _debug (bool): 调试日志开关
    Methods:
        is_present(): 检测键盘是否存在
        set_brightness(duty): 设置背光亮度
        set_default_brightness(duty): 设置 Alt+B 默认亮度
        set_raw_mode(): 切换到 raw 矩阵模式
        set_key_mode(): 切换到普通按键模式
        read_keycode(): 读取原始键码
        read_key(): 读取按键字符
        read_key_name(): 读取按键名称
        wait_key(timeout_ms, poll_ms): 带超时的按键等待
        read_raw(): 读取 raw 矩阵数据
        pressed_positions(raw): 解析按下的矩阵位置
        pressed_keys(raw, include_special): 解析按下的按键标签
        decode_keycode(code): 将键码转换为可读标签
        self_test(verbose): 非破坏性通信检查
        deinit(power_off): 释放硬件资源
    Notes:
        - 这是一个 LILYGO 自定义 I2C 键盘协议，不是 TCA8418 等通用键盘扫描芯片
        - 驱动文件未在 T-Deck Plus 实物上硬件验证
        - 官方协议参考：Xinyuan-LilyGO/T-Deck Keyboard_ESP32C3.ino
          和 Keyboard_T_Deck_Master.ino
    ==========================================
    MicroPython driver for the LILYGO T-Deck keyboard controller.

    The keyboard is an onboard ESP32-C3 running LILYGO firmware. The ESP32-S3
    host reads it over I2C address 0x55. In key mode, a one-byte read returns
    0x00 when no key is pending, otherwise a character/control byte. In raw
    mode, a five-byte read returns one bitmask per keyboard matrix column.
    Backlight brightness control and mode switching are supported.

    Attributes:
        address (int): Device I2C address
        _i2c (I2C): I2C bus instance
        _debug (bool): Debug log toggle
    Methods:
        is_present(): Check if keyboard is present
        set_brightness(duty): Set backlight brightness
        set_default_brightness(duty): Set Alt+B default brightness
        set_raw_mode(): Switch to raw matrix mode
        set_key_mode(): Switch to normal key mode
        read_keycode(): Read raw keycode byte
        read_key(): Read key as character
        read_key_name(): Read key as readable name
        wait_key(timeout_ms, poll_ms): Wait for key with timeout
        read_raw(): Read raw matrix bytes
        pressed_positions(raw): Decode pressed matrix positions
        pressed_keys(raw, include_special): Decode pressed key labels
        decode_keycode(code): Convert keycode to readable label
        self_test(verbose): Non-destructive communication check
        deinit(power_off): Release hardware resources
    Notes:
        - This is a LILYGO custom I2C keyboard protocol, not a TCA8418-style
          generic keyboard scan IC
        - Driver not hardware-verified on a real T-Deck Plus
        - Official reference: Xinyuan-LilyGO/T-Deck Keyboard_ESP32C3.ino
          and Keyboard_T_Deck_Master.ino
    """

    def __init__(self, i2c, address: int = TDECK_KEYBOARD_ADDR, power_pin=None, startup_ms: int = 0, debug: bool = False) -> None:
        """
        初始化 T-Deck 键盘驱动

        检测 I2C 接口并设置通信参数。
        Args:
            i2c (I2C): I2C 总线实例（必须由外部创建并传入）
            address (int): 设备 I2C 地址，默认 0x55
            power_pin: 键盘供电控制引脚，可选
            startup_ms (int): 上电后等待时间（ms），默认 0
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            TypeError: i2c 参数无效
            ValueError: address/startup_ms 参数范围错误
            RuntimeError: Pin 模块不可用时传入了 power_pin
        Notes:
            - power_pin 用于控制键盘控制器供电，传入 None 表示外部供电
            - startup_ms 用于等待 ESP32-C3 固件启动完成
            - startup_ms < 0 时抛出 ValueError
        ==========================================
        Initialize T-Deck keyboard driver.

        Validates I2C interface and configures communication parameters.
        Args:
            i2c (I2C): I2C bus instance, externally created and passed in
            address (int): Device I2C address, default 0x55
            power_pin: Keyboard power control pin, optional
            startup_ms (int): Power-on wait time in ms, default 0
            debug (bool): Enable debug log output, default False
        Raises:
            TypeError: Invalid i2c parameter
            ValueError: address or startup_ms out of range
            RuntimeError: Pin module unavailable but power_pin provided
        Notes:
            - power_pin controls power; None means external power
            - startup_ms waits for ESP32-C3 firmware to boot
            - Raises ValueError when startup_ms < 0
        """
        # 参数校验：I2C 实例鸭子类型检查
        if not isinstance(debug, bool):
            raise TypeError("debug must be bool")
        self._debug = debug
        self._validate_i2c(i2c)
        self._validate_address(address)
        self._i2c = i2c
        self.address = address

        # 预分配 I2C 通信缓冲区
        self._one = bytearray(1)
        self._raw = bytearray(RAW_COLUMNS)
        self._cmd1 = bytearray(1)
        self._cmd2 = bytearray(2)
        self._power = None

        # 供电引脚初始化
        if power_pin is not None:
            if Pin is None:
                raise RuntimeError("machine.Pin is required for power_pin")
            self._power = self._make_output_pin(power_pin)
            self._power.value(1)

        if startup_ms:
            if startup_ms < 0:
                raise ValueError("startup_ms must be >= 0")
            raise RuntimeError("Use TDeckKeyboardAsync.initialize_async() for cooperative startup")

        self._log("init: addr=0x%02X" % self.address)

    def _log(self, msg: str) -> None:
        """
        条件日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - ISR-safe: 否（涉及 print 和字符串拼接）
        ==========================================
        Conditional log output.
        Args:
            msg (str): Log message
        Notes:
            - ISR-safe: No (uses print and string concatenation)
        """
        if self._debug:
            print("[TDeckKeyboard] %s" % msg)

    def is_present(self) -> bool:
        """
        检测键盘是否在 I2C 总线上可见

        尝试通过 I2C scan 或直接读取确认设备存在。
        Returns:
            bool: True 表示设备存在
        Notes:
            - 副作用：无
            - ISR-safe: 否（涉及 I2C 通信）
        ==========================================
        Check if the keyboard is visible on the I2C bus.

        Attempts I2C scan or direct read to confirm device presence.
        Returns:
            bool: True if device is present
        Notes:
            - Side effect: None
            - ISR-safe: No (involves I2C communication)
        """
        try:
            scan = self._i2c.scan
        except AttributeError:
            try:
                self._read_into(self._one)
                return True
            except RuntimeError:
                return False
        return self.address in scan()

    def set_brightness(self, duty: int) -> None:
        """
        设置键盘背光亮度

        向控制器发送背光亮度命令。
        Args:
            duty (int): 背光亮度值，范围 0..255
        Raises:
            TypeError: duty 不是整数
            ValueError: duty 超出范围
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：立即改变键盘背光亮度
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Set keyboard backlight brightness.

        Sends brightness command to the controller.
        Args:
            duty (int): Backlight brightness, range 0..255
        Raises:
            TypeError: duty is not int
            ValueError: duty out of range
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: immediately changes keyboard backlight
            - ISR-safe: No (blocking I2C operation)
        """
        duty = self._validate_u8(duty, "duty")
        self._write_command(CMD_BRIGHTNESS, duty)

    def set_default_brightness(self, duty: int) -> None:
        """
        设置 Alt+B 默认背光亮度

        此值在用户按 Alt+B 后恢复为默认亮度。
        Args:
            duty (int): 默认亮度值，范围 31..255
        Raises:
            TypeError: duty 不是整数
            ValueError: duty 超出范围
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改控制器存储的默认亮度
            - 合法范围 31..255，低于 31 的值会被拒绝
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Set Alt+B default backlight brightness.

        This value is restored when the user presses Alt+B.
        Args:
            duty (int): Default brightness, range 31..255
        Raises:
            TypeError: duty is not int
            ValueError: duty out of range
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: modifies stored default brightness in controller
            - Valid range 31..255; values below 31 are rejected
            - ISR-safe: No (blocking I2C operation)
        """
        duty = self._validate_u8(duty, "duty")
        if duty <= 30:
            raise ValueError("default brightness must be in range 31..255")
        self._write_command(CMD_ALT_B_BRIGHTNESS, duty)

    def set_raw_mode(self) -> None:
        """
        切换到 raw 矩阵模式

        在 raw 模式下，read_raw() 返回 5 字节列位掩码。
        Notes:
            - 副作用：改变键盘固件的工作模式
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Switch keyboard firmware to raw matrix mode.

        In raw mode, read_raw() returns 5 bytes of column bitmasks.
        Notes:
            - Side effect: changes keyboard firmware operating mode
            - ISR-safe: No (blocking I2C operation)
        """
        self._write_command(CMD_MODE_RAW)

    def set_key_mode(self) -> None:
        """
        切换到普通按键模式

        在普通模式下，read_keycode()/read_key() 返回单个按键字符。
        Notes:
            - 副作用：改变键盘固件的工作模式
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Switch keyboard firmware to normal key mode.

        In normal mode, read_keycode()/read_key() return single key characters.
        Notes:
            - Side effect: changes keyboard firmware operating mode
            - ISR-safe: No (blocking I2C operation)
        """
        self._write_command(CMD_MODE_KEY)

    def read_keycode(self):
        """
        读取普通模式下的原始键码

        从 I2C 读取 1 字节键码。0x00 表示无按键。
        Returns:
            int or None: 键码值（0x01..0xFF），无按键时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：消费一个按键事件
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Read raw keycode in normal key mode.

        Reads 1 byte from I2C. 0x00 means no key is pending.
        Returns:
            int or None: Keycode value (0x01..0xFF), None when no key
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: consumes one key event
            - ISR-safe: No (blocking I2C operation)
        """
        self._read_into(self._one)
        code = self._one[0]
        if code == KEY_NONE:
            return None
        return code

    def read_key(self):
        """
        读取普通模式下的按键字符

        将键码转换为对应的 Unicode 字符。
        Returns:
            str or None: 按键字符，无按键时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：消费一个按键事件
            - 控制字符 "\\b"、"\\r"、"\\f" 直接返回
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Read one key in normal key mode as a character string.

        Converts keycode to the corresponding Unicode character.
        Returns:
            str or None: Key character, None when no key
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: consumes one key event
            - Control characters "\\b", "\\r", "\\f" are returned directly
            - ISR-safe: No (blocking I2C operation)
        """
        code = self.read_keycode()
        if code is None:
            return None
        return chr(code)

    def read_key_name(self):
        """
        读取普通模式下的按键可读名称

        将键码解码为可读标签，例如 "backspace"、"enter"、"alt_c"。
        Returns:
            str or None: 按键名称，无按键时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：消费一个按键事件
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Read one key in normal key mode as a readable name.

        Decodes keycode to a readable label, such as "backspace".
        Returns:
            str or None: Key name, None when no key
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: consumes one key event
            - ISR-safe: No (blocking I2C operation)
        """
        code = self.read_keycode()
        if code is None:
            return None
        return self.decode_keycode(code)

    def wait_key(self, timeout_ms: int = 1000, poll_ms: int = 10):
        """
        带超时的按键等待

        轮询键盘直到有按键或超时。
        Args:
            timeout_ms (int): 最大等待时间（ms），默认 1000
            poll_ms (int): 轮询间隔（ms），默认 10
        Returns:
            str or None: 按键字符，超时时返回 None
        Raises:
            ValueError: timeout_ms 或 poll_ms 为负数
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：阻塞调用线程直到超时或有按键
            - 该方法有明确的超时边界，不会无限阻塞
            - ISR-safe: 否（阻塞轮询）
        ==========================================
        Poll until a key is available or timeout expires.

        Polls the keyboard until a key is detected or timeout.
        Args:
            timeout_ms (int): Maximum wait time in ms, default 1000
            poll_ms (int): Poll interval in ms, default 10
        Returns:
            str or None: Key character, None on timeout
        Raises:
            ValueError: timeout_ms or poll_ms is negative
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: blocks calling thread until timeout or keypress
            - Has an explicit timeout boundary; will never block indefinitely
            - ISR-safe: No (blocking poll)
        """
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")
        if poll_ms < 0:
            raise ValueError("poll_ms must be >= 0")

        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) <= timeout_ms:
            key = self.read_key()
            if key is not None:
                return key
            if poll_ms:
                time.sleep_ms(poll_ms)
        return None

    def read_raw(self) -> tuple:
        """
        读取 raw 矩阵模式下的原始列数据

        必须先调用 set_raw_mode() 切换到 raw 模式。
        Returns:
            tuple: 5 个整数的元组，每个对应一列的位掩码（bit0..bit6 对应行 0..6）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：读取当前矩阵状态
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        Read raw keyboard matrix bytes.

        Call set_raw_mode() before using this method.
        Returns:
            tuple: Five integers, one column bitmask each
            (bit0..bit6 for rows 0..6)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: reads current matrix state
            - ISR-safe: No (blocking I2C operation)
        """
        self._read_into(self._raw)
        return tuple(self._raw)

    def pressed_positions(self, raw=None) -> list:
        """
        解析 raw 矩阵数据，返回按下的 (col, row) 位置列表

        遍历 5 列 × 7 行，提取所有被按下的位。
        Args:
            raw: raw 矩阵数据（5 字节），为 None 时自动调用 read_raw()
        Returns:
            list: (col, row) 元组列表
        Raises:
            ValueError: raw 数据长度不是 5
        Notes:
            - 副作用：当 raw 为 None 时读取 I2C
            - ISR-safe: 否
        ==========================================
        Parse raw matrix data into pressed (col, row) positions.

        Iterates 5 columns × 7 rows to extract all pressed bits.
        Args:
            raw: Raw matrix data (5 bytes), calls read_raw() when None
        Returns:
            list: List of (col, row) tuples
        Raises:
            ValueError: raw data length is not 5
        Notes:
            - Side effect: reads I2C when raw is None
            - ISR-safe: No
        """
        if raw is None:
            raw = self.read_raw()
        if len(raw) != RAW_COLUMNS:
            raise ValueError("raw must contain 5 column bytes")

        out = []
        for col in range(RAW_COLUMNS):
            value = raw[col]
            for row in range(RAW_ROWS):
                if value & (1 << row):
                    out.append((col, row))
        return out

    def pressed_keys(self, raw=None, include_special: bool = False) -> list:
        """
        将 raw 矩阵数据解码为按键标签列表

        自动处理符号层（symbol 键按下时）和 Shift 层。
        Args:
            raw: raw 矩阵数据，为 None 时自动调用 read_raw()
            include_special (bool): 是否包含特殊功能键名称（symbol/shift/enter 等）
        Returns:
            list: 按键标签字符串列表
        Notes:
            - 副作用：当 raw 为 None 时读取 I2C
            - 符号层由 (col=0, row=2) 按键控制
            - Shift 由 left_shift (col=1, row=6) 或 right_shift (col=2, row=3) 控制
            - ISR-safe: 否
        ==========================================
        Decode raw matrix bytes into key labels.

        Automatically handles symbol layer and Shift layer.
        Args:
            raw: Raw matrix data, calls read_raw() when None
            include_special (bool): Whether to include special key names
        Returns:
            list: List of key label strings
        Notes:
            - Side effect: reads I2C when raw is None
            - Symbol layer is activated by (col=0, row=2) key
            - Shift is activated by left_shift or right_shift
            - ISR-safe: No
        """
        if raw is None:
            raw = self.read_raw()
        symbol = bool(raw[0] & (1 << 2))
        shifted = bool((raw[1] & (1 << 6)) or (raw[2] & (1 << 3)))
        matrix = SYMBOL_MATRIX if symbol else KEY_MATRIX

        out = []
        for col, row in self.pressed_positions(raw):
            key = matrix[col][row]
            if key is not None:
                if shifted and len(key) == 1 and "a" <= key <= "z":
                    key = key.upper()
                out.append(key)
            elif include_special:
                name = SPECIAL_POSITIONS.get((col, row))
                if name is not None:
                    out.append(name)
        return out

    def decode_keycode(self, code: int) -> str:
        """
        将普通模式键码转换为可读标签

        Args:
            code (int): 原始键码
        Returns:
            str: 可读标签（如 "backspace"、"enter"、"alt_c"、单个字符或 "0xNN"）
        Notes:
            - 副作用：无
            - ISR-safe: 是（纯计算）
        ==========================================
        Convert a normal-mode keycode byte to a readable label.

        Args:
            code (int): Raw keycode byte
        Returns:
            str: Readable label, single char, or "0xNN"
        Notes:
            - Side effect: None
            - ISR-safe: Yes (pure computation)
        """
        if code == KEY_BACKSPACE:
            return "backspace"
        if code == KEY_ENTER:
            return "enter"
        if code == KEY_ALT_C:
            return "alt_c"
        if 32 <= code <= 126:
            return chr(code)
        return "0x%02X" % code

    def self_test(self, verbose: bool = True) -> bool:
        """
        运行非破坏性通信检查

        检测设备是否存在并进行一次 I2C 读取测试。
        Args:
            verbose (bool): 是否打印诊断信息，默认 True
        Returns:
            bool: True 表示通信正常
        Notes:
            - 副作用：重置键盘为普通按键模式
            - 此方法只验证 I2C 通信，不证明完整硬件功能
            - 未在 T-Deck Plus 实物上验证
            - ISR-safe: 否（I2C 通信）
        ==========================================
        Run a non-destructive communication check.

        Checks device presence and performs a one-byte I2C read test.
        Args:
            verbose (bool): Whether to print diagnostic info, default True
        Returns:
            bool: True if communication is working
        Notes:
            - Side effect: resets keyboard to normal key mode
            - This only validates I2C communication, not full hardware function
            - Not verified on real T-Deck Plus hardware
            - ISR-safe: No (I2C communication)
        """
        try:
            present = self.is_present()
            if verbose:
                print("[TDeckKeyboard] address 0x%02X present: %s" % (self.address, present))
            self.set_key_mode()
            self._read_into(self._one)
            if verbose:
                print("[TDeckKeyboard] one-byte read: 0x%02X" % self._one[0])
            return present
        except RuntimeError as exc:
            if verbose:
                print("[TDeckKeyboard] self-test failed: %s" % exc)
            return False

    def _read_into(self, buf) -> None:
        """
        I2C 读取操作（带错误包装）

        Args:
            buf: 目标缓冲区
        Raises:
            RuntimeError: I2C 通信失败，包含地址信息
        Notes:
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        I2C read operation with error wrapping.

        Args:
            buf: Destination buffer
        Raises:
            RuntimeError: I2C communication failed, includes address context
        Notes:
            - ISR-safe: No (blocking I2C operation)
        """
        try:
            self._i2c.readfrom_into(self.address, buf)
        except OSError as exc:
            raise RuntimeError("I2C read failed at address 0x%02X: %s" % (self.address, exc))

    def _write_command(self, command: int, value=None) -> None:
        """
        I2C 写命令操作（带错误包装）

        Args:
            command (int): 命令字节
            value: 可选的值参数
        Raises:
            RuntimeError: I2C 通信失败，包含命令和地址信息
        Notes:
            - ISR-safe: 否（I2C 阻塞操作）
        ==========================================
        I2C write command operation with error wrapping.

        Args:
            command (int): Command byte
            value: Optional value parameter
        Raises:
            RuntimeError: I2C communication failed with command/address context
        Notes:
            - ISR-safe: No (blocking I2C operation)
        """
        if value is None:
            self._cmd1[0] = command
            buf = self._cmd1
        else:
            self._cmd2[0] = command
            self._cmd2[1] = value
            buf = self._cmd2
        try:
            self._i2c.writeto(self.address, buf)
        except OSError as exc:
            raise RuntimeError("I2C write command 0x%02X failed at address 0x%02X: %s" % (command, self.address, exc))

    def deinit(self, power_off: bool = False) -> None:
        """
        释放硬件资源

        恢复普通按键模式，可选关闭供电引脚。
        Args:
            power_off (bool): 是否关闭供电引脚，默认 False
        Notes:
            - 副作用：键盘恢复普通按键模式
            - ISR-safe: 否（I2C 通信）
        ==========================================
        Release hardware resources.

        Returns to normal key mode, optionally turns off power pin.
        Args:
            power_off (bool): Whether to turn off power pin, default False
        Notes:
            - Side effect: keyboard returns to normal key mode
            - ISR-safe: No (I2C communication)
        """
        self._log("deinit")
        try:
            self.set_key_mode()
        except RuntimeError:
            pass
        if power_off and self._power is not None:
            self._power.value(0)

    @staticmethod
    def _validate_i2c(i2c) -> None:
        """
        验证 I2C 接口
        Args:
            i2c: 待验证的 I2C 对象
        Raises:
            TypeError: 接口不兼容
        ==========================================
        Validate I2C interface.
        Args:
            i2c: I2C object to validate
        Raises:
            TypeError: Incompatible interface
        """
        if not hasattr(i2c, "readfrom_into"):
            raise TypeError("i2c must provide readfrom_into()")
        if not hasattr(i2c, "writeto"):
            raise TypeError("i2c must provide writeto()")

    @staticmethod
    def _validate_address(address: int) -> None:
        """
        验证 I2C 地址
        Args:
            address (int): I2C 地址
        Raises:
            TypeError: 地址不是整数
            ValueError: 地址超出 8 位范围
        ==========================================
        Validate I2C address.
        Args:
            address (int): I2C address
        Raises:
            TypeError: address is not int
            ValueError: address out of 8-bit range
        """
        if not isinstance(address, int):
            raise TypeError("address must be int")
        if address < 0x00 or address > 0x7F:
            raise ValueError("I2C address must be in range 0x00..0x7F")

    @staticmethod
    def _validate_u8(value: int, name: str) -> int:
        """
        验证 8 位无符号整数
        Args:
            value (int): 待验证的值
            name (str): 参数名（用于错误消息）
        Returns:
            int: 验证通过的值
        Raises:
            TypeError: 值不是整数
            ValueError: 值超出 0..255 范围
        ==========================================
        Validate 8-bit unsigned integer.
        Args:
            value (int): Value to validate
            name (str): Parameter name for error messages
        Returns:
            int: Validated value
        Raises:
            TypeError: value is not int
            ValueError: value out of 0..255 range
        """
        if not isinstance(value, int):
            raise TypeError("%s must be int" % name)
        if value < 0 or value > 255:
            raise ValueError("%s must be in range 0..255" % name)
        return value

    @staticmethod
    def _make_output_pin(pin):
        """
        获取输出 Pin 对象

        若传入的已是 Pin 对象则直接返回，否则创建新的输出 Pin。
        Args:
            pin: Pin 对象或引脚编号
        Returns:
            Pin: 输出模式 Pin 对象
        Notes:
            - ISR-safe: 否（可能创建 Pin 对象）
        ==========================================
        Get output Pin object.

        Returns the pin if it is already a Pin object, otherwise creates one.
        Args:
            pin: Pin object or pin number
        Returns:
            Pin: Output mode Pin object
        Notes:
            - ISR-safe: No (may create Pin object)
        """
        if hasattr(pin, "value"):
            return pin
        return Pin(pin, Pin.OUT)


# 初始化配置

# 主程序
