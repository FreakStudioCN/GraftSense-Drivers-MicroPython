# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : ch9328.py
# @Description : CH9328 串口USBHID键盘驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CH9328:
    """
    CH9328 UART转USB HID键盘模拟器驱动类。

    该类提供CH9328芯片的完整驱动功能，支持多种工作模式下的键盘模拟操作：
    - Mode0/1/2：直接ASCII字符发送
    - Mode3：透传模式，支持原始HID数据包发送
    支持单键按下、释放、组合键、字符串输入等功能。

    Attributes:
        MODIFIER_*: HID修饰键常量（Ctrl、Shift、Alt、Win等）。
        KEY_*: HID普通按键常量（字母、数字、功能键等）。
        KEYBOARD_MODE: 支持的工作模式列表 [0, 1, 2, 3]。
        CHAR_TO_HID: ASCII字符到HID键码的映射字典。
        SHIFT_CHARS: 需要Shift修饰键的字符集合。

    Methods:
        __init__(): 初始化CH9328实例。
        set_keyboard_mode(): 设置键盘工作模式。
        crlf(): 发送回车换行符。
        send_ascii(): 发送单个ASCII字符。
        send_string(): 发送字符串。
        send_hid_packet(): 发送8字节HID数据包。
        press_key(): 按下指定按键。
        release_key(): 释放按键。
        tap_key(): 单击按键。
        hotkey(): 触发组合键。
        type_text(): 模拟打字输入字符串。

    ==========================================

    CH9328 UART to USB HID keyboard emulator driver class.

    This class provides complete driver functionality for CH9328 chip,
    supporting keyboard emulation operations in multiple working modes:
    - Mode0/1/2: Direct ASCII character transmission
    - Mode3: Passthrough mode, supports raw HID data packet transmission
    Supports single key press, release, hotkeys, string input, etc.

    Attributes:
        MODIFIER_*: HID modifier key constants (Ctrl, Shift, Alt, Win, etc.).
        KEY_*: HID normal key constants (letters, numbers, function keys, etc.).
        KEYBOARD_MODE: Supported working mode list [0, 1, 2, 3].
        CHAR_TO_HID: ASCII character to HID key code mapping dictionary.
        SHIFT_CHARS: Character set requiring Shift modifier key.

    Methods:
        __init__(): Initialize CH9328 instance.
        set_keyboard_mode(): Set keyboard working mode.
        crlf(): Send carriage return/line feed characters.
        send_ascii(): Send single ASCII character.
        send_string(): Send string.
        send_hid_packet(): Send 8-byte HID data packet.
        press_key(): Press specified key.
        release_key(): Release key.
        tap_key(): Tap key (press and release).
        hotkey(): Trigger hotkey combination.
        type_text(): Simulate typing input string.
    """

    # 4. HID修饰键码（第1字节，bit位映射）
    # 无修饰键
    MODIFIER_NONE = 0x00
    # 左Ctrl
    MODIFIER_LEFT_CTRL = 0x01
    # 左Shift
    MODIFIER_LEFT_SHIFT = 0x02
    # 左Alt
    MODIFIER_LEFT_ALT = 0x04
    # 左Win键
    MODIFIER_LEFT_GUI = 0x08
    # 右Ctrl
    MODIFIER_RIGHT_CTRL = 0x10
    # 右Shift
    MODIFIER_RIGHT_SHIFT = 0x20
    # 右Alt
    MODIFIER_RIGHT_ALT = 0x40
    # 右Win键
    MODIFIER_RIGHT_GUI = 0x80

    # 5. 普通按键HID码（参考USB HID键盘规范，部分常用键）
    # 无按键
    KEY_NONE = 0x00
    KEY_A = 0x04
    KEY_B = 0x05
    KEY_C = 0x06
    KEY_D = 0x07
    KEY_E = 0x08
    KEY_F = 0x09
    KEY_G = 0x0A
    KEY_H = 0x0B
    KEY_I = 0x0C
    KEY_J = 0x0D
    KEY_K = 0x0E
    KEY_L = 0x0F
    KEY_M = 0x10
    KEY_N = 0x11
    KEY_O = 0x12
    KEY_P = 0x13
    KEY_Q = 0x14
    KEY_R = 0x15
    KEY_S = 0x16
    KEY_T = 0x17
    KEY_U = 0x18
    KEY_V = 0x19
    KEY_W = 0x1A
    KEY_X = 0x1B
    KEY_Y = 0x1C
    KEY_Z = 0x1D
    KEY_1 = 0x1E
    KEY_2 = 0x1F
    KEY_3 = 0x20
    KEY_4 = 0x21
    KEY_5 = 0x22
    KEY_6 = 0x23
    KEY_7 = 0x24
    KEY_8 = 0x25
    KEY_9 = 0x26
    KEY_0 = 0x27
    KEY_ENTER = 0x28
    KEY_ESCAPE = 0x29
    KEY_BACKSPACE = 0x2A
    KEY_TAB = 0x2B
    KEY_SPACE = 0x2C

    # -
    KEY_MINUS = 0x2D
    # =
    KEY_EQUAL = 0x2E
    # [
    KEY_LEFT_BRACKET = 0x2F
    # ]
    KEY_RIGHT_BRACKET = 0x30
    # \
    KEY_BACKSLASH = 0x31
    # ;
    KEY_SEMICOLON = 0x33
    # '
    KEY_APOSTROPHE = 0x34
    # `
    KEY_GRAVE = 0x35
    # ,
    KEY_COMMA = 0x36
    # .
    KEY_PERIOD = 0x37
    # /
    KEY_SLASH = 0x38
    # CAPS_LOCK
    KEY_CAPS_LOCK = 0x39

    # 功能键
    KEY_F1 = 0x3A
    KEY_F2 = 0x3B
    KEY_F3 = 0x3C
    KEY_F4 = 0x3D
    KEY_F5 = 0x3E
    KEY_F6 = 0x3F
    KEY_F7 = 0x40
    KEY_F8 = 0x41
    KEY_F9 = 0x42
    KEY_F10 = 0x43
    KEY_F11 = 0x44
    KEY_F12 = 0x45

    # 其他按键
    KEY_PRINT_SCREEN = 0x46
    KEY_SCROLL_LOCK = 0x47
    KEY_PAUSE = 0x48
    KEY_INSERT = 0x49
    KEY_HOME = 0x4A
    KEY_PAGE_UP = 0x4B
    KEY_DELETE = 0x4C
    KEY_END = 0x4D
    KEY_PAGE_DOWN = 0x4E
    KEY_RIGHT_ARROW = 0x4F
    KEY_LEFT_ARROW = 0x50
    KEY_DOWN_ARROW = 0x51
    KEY_UP_ARROW = 0x52
    KEY_NUM_LOCK = 0x53
    KEY_KP_SLASH = 0x54
    KEY_KP_ASTERISK = 0x55
    KEY_KP_MINUS = 0x56
    KEY_KP_PLUS = 0x57
    KEY_KP_ENTER = 0x58
    KEY_KP_1 = 0x59
    KEY_KP_2 = 0x5A
    KEY_KP_3 = 0x5B
    KEY_KP_4 = 0x5C
    KEY_KP_5 = 0x5D
    KEY_KP_6 = 0x5E
    KEY_KP_7 = 0x5F
    KEY_KP_8 = 0x60
    KEY_KP_9 = 0x61
    KEY_KP_0 = 0x62
    KEY_KP_DOT = 0x63
    KEY_MENU = 0x65

    KEYBOARD_MODE = [0, 1, 2, 3]

    # 字符到HID键码的映射（基本ASCII）
    CHAR_TO_HID = {
        # 小写字母
        "a": KEY_A,
        "b": KEY_B,
        "c": KEY_C,
        "d": KEY_D,
        "e": KEY_E,
        "f": KEY_F,
        "g": KEY_G,
        "h": KEY_H,
        "i": KEY_I,
        "j": KEY_J,
        "k": KEY_K,
        "l": KEY_L,
        "m": KEY_M,
        "n": KEY_N,
        "o": KEY_O,
        "p": KEY_P,
        "q": KEY_Q,
        "r": KEY_R,
        "s": KEY_S,
        "t": KEY_T,
        "u": KEY_U,
        "v": KEY_V,
        "w": KEY_W,
        "x": KEY_X,
        "y": KEY_Y,
        "z": KEY_Z,
        # 数字（不需要Shift）
        "1": KEY_1,
        "2": KEY_2,
        "3": KEY_3,
        "4": KEY_4,
        "5": KEY_5,
        "6": KEY_6,
        "7": KEY_7,
        "8": KEY_8,
        "9": KEY_9,
        "0": KEY_0,
        # 符号（不需要Shift）
        " ": KEY_SPACE,
        "-": KEY_MINUS,
        "=": KEY_EQUAL,
        "[": KEY_LEFT_BRACKET,
        "]": KEY_RIGHT_BRACKET,
        "\\": KEY_BACKSLASH,
        ";": KEY_SEMICOLON,
        "'": KEY_APOSTROPHE,
        "`": KEY_GRAVE,
        ",": KEY_COMMA,
        ".": KEY_PERIOD,
        "/": KEY_SLASH,
        # 需要Shift的字符（大写字母和符号）
        "A": KEY_A,
        "B": KEY_B,
        "C": KEY_C,
        "D": KEY_D,
        "E": KEY_E,
        "F": KEY_F,
        "G": KEY_G,
        "H": KEY_H,
        "I": KEY_I,
        "J": KEY_J,
        "K": KEY_K,
        "L": KEY_L,
        "M": KEY_M,
        "N": KEY_N,
        "O": KEY_O,
        "P": KEY_P,
        "Q": KEY_Q,
        "R": KEY_R,
        "S": KEY_S,
        "T": KEY_T,
        "U": KEY_U,
        "V": KEY_V,
        "W": KEY_W,
        "X": KEY_X,
        "Y": KEY_Y,
        "Z": KEY_Z,
        "!": KEY_1,
        "@": KEY_2,
        "#": KEY_3,
        "$": KEY_4,
        "%": KEY_5,
        "^": KEY_6,
        "&": KEY_7,
        "*": KEY_8,
        "(": KEY_9,
        ")": KEY_0,
        "_": KEY_MINUS,
        "+": KEY_EQUAL,
        "{": KEY_LEFT_BRACKET,
        "}": KEY_RIGHT_BRACKET,
        "|": KEY_BACKSLASH,
        ":": KEY_SEMICOLON,
        '"': KEY_APOSTROPHE,
        "~": KEY_GRAVE,
        "<": KEY_COMMA,
        ">": KEY_PERIOD,
        "?": KEY_SLASH,
        # 特殊字符（回车、制表符等）
        "\n": KEY_ENTER,
        "\t": KEY_TAB,
        "\b": KEY_BACKSPACE,
    }

    # 需要Shift键的字符集合
    SHIFT_CHARS = {
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
        "!",
        "@",
        "#",
        "$",
        "%",
        "^",
        "&",
        "*",
        "(",
        ")",
        "_",
        "+",
        "{",
        "}",
        "|",
        ":",
        '"',
        "~",
        "<",
        ">",
        "?",
    }

    def __init__(self, uart=UART):
        """
        初始化CH9328实例。

        Args:
            uart: 已配置的UART实例。

        Note:
            - 默认设置为Mode0（模式0）。
            - UART参数需提前配置（波特率、数据位、停止位等）。
            - 常见波特率：9600, 19200, 38400, 57600, 115200等。

        ==========================================

        Initialize CH9328 instance.

        Args:
            uart: Configured UART instance.

        Note:
            - Default setting is Mode0.
            - UART parameters must be configured in advance (baud rate, data bits, stop bits, etc.).
            - Common baud rates: 9600, 19200, 38400, 57600, 115200, etc.
        """
        self.uart = uart
        self.current_mode = 0  # 默认Mode0

    def set_keyboard_mode(self, mode: tuple) -> None:
        """
        设置键盘工作模式。

        Args:
            mode: 模式整数值，参考KEYBOARD_MODE [0, 1, 2, 3]。

        Raises:
            ValueError: 模式不在支持范围内时抛出。

        Note:
            - 模式0/1/2：ASCII模式，自动转HID码。
            - 模式3：透传模式，需手动构造HID数据包。
            - 模式设置需配合硬件IO2~IO4引脚电平。

        ==========================================

        Set keyboard working mode.

        Args:
            mode: Mode integer value, refer to KEYBOARD_MODE [0, 1, 2, 3].

        Raises:
            ValueError: Raised when mode is not in supported range.

        Note:
            - Mode 0/1/2: ASCII mode, automatically converts to HID codes.
            - Mode 3: Passthrough mode, requires manual construction of HID data packets.
            - Mode setting requires corresponding hardware IO2~IO4 pin levels.
        """
        # 校验模式合法性
        if mode not in CH9328.KEYBOARD_MODE:
            raise ValueError(f"无效工作模式，仅支持：{CH9328.KEYBOARD_MODE}")
        self.current_mode = mode

    def crlf(self):
        """
        发送回车换行符（CR/LF），根据当前模式选择不同的控制字符。

        该方法根据设备当前的工作模式发送相应的回车换行控制字符：
        - 当模式为0时，发送ESC字符（0x1B）
        - 当模式为2时，发送'('字符（0x28）

        Note:
            - 仅支持模式0和模式2，其他模式不执行任何操作。
            - 直接通过UART发送原始字节数据。
            - 调用前需要确保设备已初始化并处于正确的模式。
            - 此方法不验证发送是否成功，也不等待响应。

        ==========================================

        Send carriage return/line feed (CR/LF) characters, selecting different control
        characters based on the current mode.

        This method sends the corresponding carriage return/line feed control character
        according to the device's current working mode:
        - When mode is 0, sends ESC character (0x1B)
        - When mode is 2, sends '(' character (0x28)

        Note:
            - Only supports modes 0 and 2, other modes perform no operation.
            - Sends raw byte data directly via UART.
            - Ensure the device is initialized and in the correct mode before calling.
            - This method does not verify if transmission was successful, nor does it wait for a response.
        """
        # 验证current_mode是否等于0或2
        if self.current_mode not in (0, 2):
            # 返回当前模式，说明不可用
            print(f"错误：当前模式 {self.current_mode} 不支持此操作，仅支持模式0或2")
            return False

        # 验证通过，执行相应操作
        if self.current_mode == 0:
            send_byte = b"\x1b"
            self.uart.write(send_byte)
        elif self.current_mode == 2:
            send_byte = b"\x28"
            self.uart.write(send_byte)
        time.sleep_ms(50)

        # 返回成功标志
        return True

    def send_ascii(self, char: str) -> None:
        """
        发送单个ASCII字符（仅适配Mode0/1/2）。

        Args:
            char: 单个ASCII字符（如'a'、'1'、'@'）。

        Raises:
            ValueError: 字符长度不为1或不是可见ASCII字符时抛出。

        Note:
            - 仅支持可见ASCII字符（0x20=空格 ~ 0x7E=~）。
            - Mode3下不支持此方法。
            - 自动编码为ASCII字节发送。

        ==========================================

        Send single ASCII character (only adapts to Mode0/1/2).

        Args:
            char: Single ASCII character (e.g., 'a', '1', '@').

        Raises:
            ValueError: Raised when character length is not 1 or not visible ASCII character.

        Note:
            - Only supports visible ASCII characters (0x20=space ~ 0x7E=~).
            - Not supported in Mode3.
            - Automatically encodes as ASCII bytes for transmission.
        """
        # 校验工作模式
        if self.current_mode == 3:
            print("警告：透传模式（Mode3）不支持send_ascii，建议使用send_hid_packet")
            return

        # 发送ASCII码（仅单个字符）
        if len(char) != 1:
            raise ValueError("send_ascii仅支持单个字符")
        # 仅支持可见ASCII码（0x20=空格~0x7E=~）
        if ord(char) not in range(0x20, 0x7F):
            raise ValueError("仅支持可见ASCII字符（空格~波浪号）")

        self.uart.write(char.encode("ascii"))
        # 避免数据堆积，连键
        time.sleep_ms(1)

    def send_string(self, text: str) -> None:
        """
        发送字符串（Mode0/1/2下逐字符发送）。

        Args:
            text: 待发送字符串（仅含可见ASCII字符）。

        Note:
            - 逐字符调用send_ascii()方法。
            - 字符间添加5ms延时避免数据堆积。
            - Mode3下不支持此方法。

        ==========================================

        Send string (character-by-character transmission in Mode0/1/2).

        Args:
            text: String to send (contains only visible ASCII characters).

        Note:
            - Calls send_ascii() method character by character.
            - Adds 5ms delay between characters to avoid data congestion.
            - Not supported in Mode3.
        """
        # 校验工作模式
        if self.current_mode == 3:
            print("警告：透传模式（Mode3）不支持send_ascii，建议使用send_hid_packet")
            return
        for char in text:
            self.send_ascii(char)
            time.sleep_ms(5)  # 字符间延时，避免丢包

    def send_hid_packet(self, packet: bytes) -> bool:
        """
        透传模式（Mode3）下发送8字节HID数据包。

        Args:
            packet: 8字节HID数据包（键盘/鼠标格式）。

        Returns:
            bool: 发送成功返回True，失败返回False。

        Note:
            - 仅Mode3支持此方法。
            - 数据包必须为8字节。
            - 发送失败会打印错误信息。

        ==========================================

        Send 8-byte HID data packet in passthrough mode (Mode3).

        Args:
            packet: 8-byte HID data packet (keyboard/mouse format).

        Returns:
            bool: Returns True if transmission successful, False if failed.

        Note:
            - Only supported in Mode3.
            - Packet must be 8 bytes.
            - Prints error message on transmission failure.
        """
        # 1. 校验模式和数据包长度
        if self.current_mode != 3:
            print("错误：仅透传模式（Mode3）支持send_hid_packet")
            return False
        if len(packet) != 8:
            print("错误：HID数据包必须为8字节")
            return False

        # 2. 发送数据包
        try:
            self.uart.write(packet)
            time.sleep_ms(1)
            return True
        except Exception as e:
            print(f"发送失败：{e}")
            return False

    def press_key(self, key_code: int, modifier: int = MODIFIER_NONE) -> None:
        """
        按下指定按键（透传模式专属）。

        Args:
            key_code: 普通按键HID码（如KEY_A=0x04）。
            modifier: 修饰键码（如MODIFIER_LEFT_SHIFT=0x02，默认无）。

        Note:
            - 仅Mode3支持此方法。
            - 构造标准的8字节键盘按下数据包。
            - 未使用的按键位置填充0x00。

        ==========================================

        Press specified key (exclusive to passthrough mode).

        Args:
            key_code: Normal key HID code (e.g., KEY_A=0x04).
            modifier: Modifier key code (e.g., MODIFIER_LEFT_SHIFT=0x02, default none).

        Note:
            - Only supported in Mode3.
            - Constructs standard 8-byte keyboard press data packet.
            - Unused key positions filled with 0x00.
        """
        # 构造键盘按下数据包：[修饰键, 保留位, 按键1, 按键2~6]（未使用按键填0）
        packet = bytes(
            [
                # 第1字节：修饰键
                modifier,
                # 第2字节：保留位
                0x00,
                # 第3字节：主按键
                key_code,
                # 第4~6字节：未使用按键
                0x00,
                0x00,
                0x00,
                # 第7~8字节：未使用按键
                0x00,
                0x00,
            ]
        )
        self.send_hid_packet(packet)

    def release_key(self, key_code: int = None, modifier: int = MODIFIER_NONE) -> None:
        """
        释放按键（透传模式专属）。

        Args:
            key_code: 待释放按键HID码（可选，仅用于逻辑标识）。
            modifier: 待释放修饰键码（可选）。

        Note:
            - 发送全0数据包释放所有按键。
            - CH9328手册标准释放方式。
            - 简化处理，适用于单键按下场景。

        ==========================================

        Release key (exclusive to passthrough mode).

        Args:
            key_code: Key HID code to release (optional, only for logical identification).
            modifier: Modifier key code to release (optional).

        Note:
            - Sends all-zero data packet to release all keys.
            - Standard release method per CH9328 manual.
            - Simplified processing, suitable for single key press scenarios.
        """
        # 全0数据包→释放所有按键（手册示例标准释放方式）
        release_packet = b"\x00\x00\x00\x00\x00\x00\x00\x00"
        self.send_hid_packet(release_packet)

    def tap_key(self, key_code: int, modifier: int = MODIFIER_NONE, delay: int = 50) -> None:
        """
        单击指定按键（按下→延时→释放，透传模式专属）。

        Args:
            key_code: 按键HID码。
            modifier: 修饰键码（默认无）。
            delay: 按下后延时时间（单位ms，默认50ms）。

        Note:
            - 模拟完整的按键单击动作。
            - 延时确保主机识别按键事件。
            - 适用于单次按键操作。

        ==========================================

        Tap specified key (press → delay → release, exclusive to passthrough mode).

        Args:
            key_code: Key HID code.
            modifier: Modifier key code (default none).
            delay: Delay after press (in milliseconds, default 50ms).

        Note:
            - Simulates complete key tap action.
            - Delay ensures host recognizes key event.
            - Suitable for single key operations.
        """
        self.press_key(key_code, modifier)
        time.sleep_ms(delay)
        self.release_key()

    def hotkey(self, modifier: int, key_code: int, delay: int = 50) -> None:
        """
        触发组合键（如Ctrl+C，透传模式专属）。

        Args:
            modifier: 修饰键码（如MODIFIER_LEFT_CTRL=0x01）。
            key_code: 普通按键HID码（如KEY_C=0x06）。
            delay: 组合键按下延时（单位ms，默认50ms）。

        Note:
            - 模拟键盘组合键操作。
            - 常用于快捷键操作。
            - 调用tap_key()实现。

        ==========================================

        Trigger hotkey combination (e.g., Ctrl+C, exclusive to passthrough mode).

        Args:
            modifier: Modifier key code (e.g., MODIFIER_LEFT_CTRL=0x01).
            key_code: Normal key HID code (e.g., KEY_C=0x06).
            delay: Hotkey press delay (in milliseconds, default 50ms).

        Note:
            - Simulates keyboard hotkey operation.
            - Commonly used for shortcut operations.
            - Implemented by calling tap_key().
        """
        self.press_key(key_code, modifier)
        time.sleep_ms(delay)
        self.release_key()

    def type_text(self, text: str, delay: int = 10) -> None:
        """
        模拟打字输入字符串（透传模式专属）。

        Args:
            text: 待输入字符串。
            delay: 字符间延时（单位ms，默认10ms）。

        Note:
            - 支持大小写、数字、符号。
            - 自动处理Shift修饰键。
            - 不支持字符会跳过并警告。

        ==========================================

        Simulate typing input string (exclusive to passthrough mode).

        Args:
            text: String to input.
            delay: Delay between characters (in milliseconds, default 10ms).

        Note:
            - Supports uppercase, lowercase, numbers, symbols.
            - Automatically handles Shift modifier.
            - Skips and warns for unsupported characters.
        """
        for char in text:
            if char not in CH9328.CHAR_TO_HID:
                print(f"警告：字符{char}不支持，跳过发送")
                continue

            # 判断是否需要Shift修饰键（大写字母）
            modifier = CH9328.MODIFIER_LEFT_SHIFT if char.isupper() else CH9328.MODIFIER_NONE
            key_code = CH9328.CHAR_TO_HID[char]

            # 发送单个字符（单击）
            self.tap_key(key_code, modifier, delay=delay)
            time.sleep_ms(delay)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
