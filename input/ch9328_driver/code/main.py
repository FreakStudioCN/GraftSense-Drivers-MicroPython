# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/19 下午5:33
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试CH9328示例
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

import time

from machine import UART, Pin

from ch9328 import CH9328

# ======================================== 全局变量 ============================================

# 根据硬件配置更改
mode = 0

# ======================================== 功能函数 ============================================

def test_mode0():
    """
    测试CH9328的Mode0工作模式。

    功能验证：
    - 设置键盘为Mode0模式
    - 发送字符串"Hello"
    - 发送回车换行符（CR/LF）
    - 发送字符串"Mode0"

    Mode0特点：
    - 支持可见ASCII字符转换为标准USB键值
    - 特殊处理：当接收到0x1B（ESC）时，丢弃当前包中0x1B之后的数据，并将0x1B转换成回车键
    - 使用crlf()方法发送0x1B实现回车功能

    Note:
        - Mode0适用于需要回车功能的ASCII字符发送场景
        - 回车功能通过0x1B转义实现

    ==========================================

    Test CH9328 Mode0 working mode.

    Function verification:
    - Set keyboard to Mode0 mode
    - Send string "Hello"
    - Send carriage return/line feed (CR/LF)
    - Send string "Mode0"

    Mode0 features:
    - Supports visible ASCII characters conversion to standard USB key values
    - Special handling: When receiving 0x1B (ESC), discards data after 0x1B in current packet, and converts 0x1B to Enter key
    - Uses crlf() method to send 0x1B for Enter function

    Note:
        - Mode0 is suitable for ASCII character transmission scenarios requiring Enter function
        - Enter function is implemented through 0x1B escape
    """
    key.set_keyboard_mode(0)
    key.send_string("Hello")
    key.crlf()
    key.send_string("Mode0")

def test_mode1():
    """
    测试CH9328的Mode1工作模式。

    功能验证：
    - 设置键盘为Mode1模式
    - 发送字符串"Hello"
    - 发送字符串"Mode1"

    Mode1特点：
    - 仅支持将可见ASCII码（如a-z、0-9、@、#、$等）对应的字符转成标准的USB键值
    - 无特殊字符转义功能
    - 最简单的ASCII发送模式

    Note:
        - Mode1适用于纯ASCII字符输入，无需回车功能
        - 不支持特殊控制字符转义

    ==========================================

    Test CH9328 Mode1 working mode.

    Function verification:
    - Set keyboard to Mode1 mode
    - Send string "Hello"
    - Send string "Mode1"

    Mode1 features:
    - Only supports converting visible ASCII codes (e.g., a-z, 0-9, @, #, $, etc.) to standard USB key values
    - No special character escape function
    - Simplest ASCII transmission mode

    Note:
        - Mode1 is suitable for pure ASCII character input without Enter function requirement
        - Does not support special control character escape
    """
    key.set_keyboard_mode(1)
    key.send_string("Hello")
    key.send_string("Mode1")

def test_mode2():
    """
    测试CH9328的Mode2工作模式。

    功能验证：
    - 设置键盘为Mode2模式
    - 发送字符串"Hello"
    - 发送回车换行符（CR/LF）
    - 发送字符串"Mode2"

    Mode2特点：
    - 支持可见ASCII字符转换为标准USB键值
    - 特殊功能：接收到的串口数据包如果遇到0x28时，将0x28转换成回车键
    - 使用crlf()方法发送0x28实现回车功能

    Note:
        - Mode2与Mode0类似，但使用不同的回车转义字符（0x28 vs 0x1B）
        - 适用于需要回车功能且可能使用0x1B作为普通字符的场景

    ==========================================

    Test CH9328 Mode2 working mode.

    Function verification:
    - Set keyboard to Mode2 mode
    - Send string "Hello"
    - Send carriage return/line feed (CR/LF)
    - Send string "Mode2"

    Mode2 features:
    - Supports visible ASCII characters conversion to standard USB key values
    - Special function: When receiving 0x28 in serial data packet, converts 0x28 to Enter key
    - Uses crlf() method to send 0x28 for Enter function

    Note:
        - Mode2 is similar to Mode0 but uses different Enter escape character (0x28 vs 0x1B)
        - Suitable for scenarios requiring Enter function where 0x1B might be used as normal character
    """
    key.set_keyboard_mode(2)
    key.send_string("Hello")
    key.crlf()
    key.send_string("Mode2")

def test_mode3():
    """
    测试CH9328的Mode3（透传）工作模式。

    功能验证：
    1. 设置键盘为Mode3模式
    2. 创建所有修饰键列表
    3. 延时3秒准备
    4. 轮流点击所有普通按键（HID码0x04~0x65）
    5. 轮流点击所有修饰键

    Mode3特点：
    - 透传模式，支持直接发送8字节HID数据包
    - 支持完整的HID键盘功能，包括修饰键
    - 提供最灵活的键盘模拟控制

    测试内容：
    - 遍历测试所有普通按键（字母、数字、功能键等）
    - 遍历测试所有修饰键（Ctrl、Shift、Alt、Win等）
    - 每个按键操作间隔50ms

    Note:
        - Mode3需要手动构造HID数据包
        - 适合需要精细控制键盘操作的场景
        - 测试前有3秒延时，确保用户切换到目标窗口

    ==========================================

    Test CH9328 Mode3 (passthrough) working mode.

    Function verification:
    1. Set keyboard to Mode3 mode
    2. Create list of all modifier keys
    3. Delay 3 seconds for preparation
    4. Cycle through clicking all normal keys (HID codes 0x04~0x65)
    5. Cycle through clicking all modifier keys

    Mode3 features:
    - Passthrough mode, supports direct transmission of 8-byte HID data packets
    - Supports complete HID keyboard functions, including modifier keys
    - Provides most flexible keyboard emulation control

    Test content:
    - Traverse and test all normal keys (letters, numbers, function keys, etc.)
    - Traverse and test all modifier keys (Ctrl, Shift, Alt, Win, etc.)
    - Each key operation interval is 50ms

    Note:
        - Mode3 requires manual construction of HID data packets
        - Suitable for scenarios requiring fine-grained keyboard control
        - 3-second delay before test ensures user switches to target window
    """
    key.set_keyboard_mode(3)
    # 创建所有修饰键的字典方便扫描
    modifier = [
        CH9328.MODIFIER_LEFT_CTRL,
        CH9328.MODIFIER_LEFT_SHIFT,
        CH9328.MODIFIER_LEFT_ALT,
        CH9328.MODIFIER_LEFT_GUI,
        CH9328.MODIFIER_RIGHT_CTRL,
        CH9328.MODIFIER_RIGHT_SHIFT,
        CH9328.MODIFIER_RIGHT_ALT,
        CH9328.MODIFIER_RIGHT_GUI
    ]
    time.sleep(3)
    # 轮流点击所有普通按键
    for key_code in range(0x04, 0x66):
        key.tap_key(key_code)
        time.sleep_ms(50)
    # 轮流点击修饰键
    for i in range(8):
        key.tap_key(key_code=CH9328.KEY_NONE,modifier=modifier[i])
        time.sleep_ms(50)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: CH9328 mode test example")

# 创建串口实例
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
# 创建CH9328实例
key = CH9328(uart)

# ========================================  主程序  ============================================

# 根据mode设置来运行示例
if mode == 0:
    print("Testing Mode 0...")
    test_mode0()
elif mode == 1:
    print("Testing Mode 1...")
    test_mode1()
elif mode == 2:
    print("Testing Mode 2...")
    test_mode2()
elif mode == 3:
    print("Testing Mode 3...")
    test_mode3()

