from machine import UART, Pin
import time

class CH9328:
    # 4. HID修饰键码（第1字节，bit位映射）
    MODIFIER_NONE = 0x00        # 无修饰键
    MODIFIER_LEFT_CTRL = 0x01   # 左Ctrl
    MODIFIER_LEFT_SHIFT = 0x02  # 左Shift
    MODIFIER_LEFT_ALT = 0x04    # 左Alt
    MODIFIER_LEFT_GUI = 0x08    # 左Win键
    MODIFIER_RIGHT_CTRL = 0x10  # 右Ctrl
    MODIFIER_RIGHT_SHIFT = 0x20 # 右Shift
    MODIFIER_RIGHT_ALT = 0x40   # 右Alt
    MODIFIER_RIGHT_GUI = 0x80   # 右Win键

    # 5. 普通按键HID码（参考USB HID键盘规范，部分常用键）
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
    KEY_BACKSPACE = 0x2A
    KEY_TAB = 0x2B
    KEY_SPACE = 0x2C
    KEY_MINUS = 0x2D    # -
    KEY_EQUAL = 0x2E    # =
    KEY_LEFT_BRACKET = 0x2F  # [
    KEY_RIGHT_BRACKET = 0x30 # ]
    KEY_BACKSLASH = 0x31     # \
    KEY_SEMICOLON = 0x33    # ;
    KEY_APOSTROPHE = 0x34    # '
    KEY_COMMA = 0x36         # ,
    KEY_PERIOD = 0x37        # .
    KEY_SLASH = 0x38         # /

    KEYBOARD_MODE = [0 , 1, 2, 3]

    # 字符到HID键码的映射（基本ASCII）
    CHAR_TO_HID = {
        # 小写字母
        'a': KEY_A, 'b': KEY_B, 'c': KEY_C, 'd': KEY_D, 'e': KEY_E,
        'f': KEY_F, 'g': KEY_G, 'h': KEY_H, 'i': KEY_I, 'j': KEY_J,
        'k': KEY_K, 'l': KEY_L, 'm': KEY_M, 'n': KEY_N, 'o': KEY_O,
        'p': KEY_P, 'q': KEY_Q, 'r': KEY_R, 's': KEY_S, 't': KEY_T,
        'u': KEY_U, 'v': KEY_V, 'w': KEY_W, 'x': KEY_X, 'y': KEY_Y, 'z': KEY_Z,

        # 数字（不需要Shift）
        '1': KEY_1, '2': KEY_2, '3': KEY_3, '4': KEY_4, '5': KEY_5,
        '6': KEY_6, '7': KEY_7, '8': KEY_8, '9': KEY_9, '0': KEY_0,

        # 符号（不需要Shift）
        ' ': KEY_SPACE, '-': KEY_MINUS, '=': KEY_EQUAL,
        '[': KEY_LEFT_BRACKET, ']': KEY_RIGHT_BRACKET,
        '\\': KEY_BACKSLASH, ';': KEY_SEMICOLON, "'": KEY_APOSTROPHE,
        '`': KEY_GRAVE, ',': KEY_COMMA, '.': KEY_PERIOD, '/': KEY_SLASH,

        # 需要Shift的字符（大写字母和符号）
        'A': KEY_A, 'B': KEY_B, 'C': KEY_C, 'D': KEY_D, 'E': KEY_E,
        'F': KEY_F, 'G': KEY_G, 'H': KEY_H, 'I': KEY_I, 'J': KEY_J,
        'K': KEY_K, 'L': KEY_L, 'M': KEY_M, 'N': KEY_N, 'O': KEY_O,
        'P': KEY_P, 'Q': KEY_Q, 'R': KEY_R, 'S': KEY_S, 'T': KEY_T,
        'U': KEY_U, 'V': KEY_V, 'W': KEY_W, 'X': KEY_X, 'Y': KEY_Y, 'Z': KEY_Z,
        '!': KEY_1, '@': KEY_2, '#': KEY_3, '$': KEY_4, '%': KEY_5,
        '^': KEY_6, '&': KEY_7, '*': KEY_8, '(': KEY_9, ')': KEY_0,
        '_': KEY_MINUS, '+': KEY_EQUAL,
        '{': KEY_LEFT_BRACKET, '}': KEY_RIGHT_BRACKET,
        '|': KEY_BACKSLASH, ':': KEY_SEMICOLON, '"': KEY_APOSTROPHE,
        '~': KEY_GRAVE, '<': KEY_COMMA, '>': KEY_PERIOD, '?': KEY_SLASH,

        # 特殊字符（回车、制表符等）
        '\n': KEY_ENTER, '\t': KEY_TAB, '\b': KEY_BACKSPACE,
    }

    # 需要Shift键的字符集合
    SHIFT_CHARS = {
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
        '_', '+', '{', '}', '|', ':', '"', '~', '<', '>', '?'
    }
    def __init__(self, uart=UART):
        # 3. 初始化工作状态（默认模式1、普通速度）
        self.uart = uart
        self.current_mode = 0  # 默认Mode0

    def set_keyboard_mode(self, mode: tuple) -> None:
        """
        设置键盘工作模式（需配置IO2~IO4引脚）
        :param mode: 模式元组（IO2电平, IO3电平, IO4电平），参考KEYBOARD_MODE_0~3
        """
        # 校验模式合法性
        if mode not in CH9328.KEYBOARD_MODE:
            raise ValueError(f"无效工作模式，仅支持：{CH9328.KEYBOARD_MODE}")
        self.current_mode = mode

    def send_ascii(self, char: str) -> None:
        """
        发送单个ASCII字符（仅适配Mode0/1/2，自动转HID码）
        :param char: 单个ASCII字符（如'a'、'1'、'@'）
        """
        # 校验工作模式
        if self.current_mode == 3:
            print("警告：透传模式（Mode3）不支持send_ascii，建议使用send_hid_packet")
            return
        
        # 发送ASCII码（仅单个字符）
        if len(char) != 1:
            raise ValueError("send_ascii仅支持单个字符")
        if ord(char) not in range(0x20, 0x7F):  # 仅支持可见ASCII码（0x20=空格~0x7E=~）
            raise ValueError("仅支持可见ASCII字符（空格~波浪号）")
        
        self.uart.write(char.encode('ascii'))
        # 避免数据堆积，连键
        time.sleep_ms(1)

    def send_string(self, text: str) -> None:
        """
        发送字符串（Mode0/1/2下逐字符转ASCII发送）
        :param text: 待发送字符串（仅含可见ASCII字符）
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
        透传模式（Mode3）下发送8字节HID数据包
        :param packet: 8字节HID数据包（键盘/鼠标格式）
        :return: 发送成功返回True，失败返回False
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
        按下指定按键（透传模式专属）
        :param key_code: 普通按键HID码（如KEY_A=0x04）
        :param modifier: 修饰键码（如MODIFIER_LEFT_SHIFT=0x02，默认无修饰键）
        """
        # 构造键盘按下数据包：[修饰键, 保留位, 按键1, 按键2~6]（未使用按键填0）
        packet = bytes([
            modifier,          # 第1字节：修饰键
            0x00,              # 第2字节：保留位
            key_code,          # 第3字节：主按键
            0x00, 0x00, 0x00,  # 第4~6字节：未使用按键
            0x00, 0x00         # 第7~8字节：未使用按键
        ])
        self.send_hid_packet(packet)

    def release_key(self, key_code: int = None, modifier: int = MODIFIER_NONE) -> None:
        """
        释放指定按键（透传模式专属，简化处理：释放时发送全0包，适用于单键按下场景）
        :param key_code: 待释放按键HID码（可选，仅用于逻辑标识）
        :param modifier: 待释放修饰键码（可选）
        """
        # 全0数据包→释放所有按键（手册示例标准释放方式）
        release_packet = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        self.send_hid_packet(release_packet)

    def tap_key(self, key_code: int, modifier: int = MODIFIER_NONE, delay: int = 50) -> None:
        """
        单击指定按键（按下→延时→释放，透传模式专属）
        :param key_code: 按键HID码
        :param modifier: 修饰键码（默认无）
        :param delay: 按下后延时时间（单位ms，默认50ms）
        """
        self.press_key(key_code, modifier)
        time.sleep_ms(delay)
        self.release_key()

    def hotkey(self, modifier: int, key_code: int, delay: int = 50) -> None:
        """
        触发组合键（如Ctrl+C，透传模式专属）
        :param modifier: 修饰键码（如MODIFIER_LEFT_CTRL=0x01）
        :param key_code: 普通按键HID码（如KEY_C=0x06）
        :param delay: 组合键按下延时（单位ms，默认50ms）
        """
        self.press_key(key_code, modifier)
        time.sleep_ms(delay)
        self.release_key()

    def type_text(self, text: str, delay: int = 10) -> None:
        """
        模拟打字输入字符串（透传模式专属，支持大小写、数字、符号）
        :param text: 待输入字符串
        :param delay: 字符间延时（单位ms，默认10ms）
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