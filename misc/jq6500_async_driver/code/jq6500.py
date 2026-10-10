# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午4:52
# @Author  : rdagger
# @File    : jq6500.py
# @Description : JQ6500 mini MP3模块驱动（MicroPython），实现UART控制播放、暂停、音量调节等功能 参考自:https://github.com/rdagger/micropython-jq6500
# @License : MIT

__version__ = "0.1.0"
__author__ = "rdagger"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython的UART串口通信模块，用于与JQ6500模块通信
from machine import UART

# 导入时间延迟模块，用于等待模块返回数据
from time import sleep

# 兼容MicroPython的类型注解导入（解决flake8 F821错误）
try:
    from typing import Optional, List
except ImportError:
    # 若MicroPython无typing模块，定义占位符避免报错
    Optional = None
    List = None


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class Player(object):
    """
            JQ6500 迷你 MP3 模块驱动类，基于 UART 接口实现对 MP3 播放器的完整控制。
            支持播放/暂停/上一曲/下一曲、音量调节、EQ 设置、循环模式、文件定位播放等核心功能，
            同时提供状态查询、文件信息读取等辅助功能。

            Attributes:
                EQ_NORMAL (int): 音效模式-普通模式，值为0
                EQ_POP (int): 音效模式-流行模式，值为1
                EQ_ROCK (int): 音效模式-摇滚模式，值为2
                EQ_JAZZ (int): 音效模式-爵士模式，值为3
                EQ_CLASSIC (int): 音效模式-古典模式，值为4
                EQ_BASS (int): 音效模式-重低音模式，值为5
                SRC_SDCARD (int): 音源选择-SD卡（仅JQ6500-28P型号支持），值为1
                SRC_BUILTIN (int): 音源选择-内置Flash，值为4
                LOOP_ALL (int): 循环模式-全部循环，播放所有曲目并重复，值为0
                LOOP_FOLDER (int): 循环模式-文件夹循环，播放当前文件夹所有曲目并重复，值为1
                LOOP_ONE (int): 循环模式-单曲循环，播放当前曲目并重复，值为2
                LOOP_RAM (int): 循环模式-RAM循环（未明确定义），值为3
                LOOP_ONE_STOP (int): 循环模式-单曲播放停止，播放完当前曲目后停止，值为4
                LOOP_NONE (int): 循环模式-无循环，同LOOP_ONE_STOP，值为4
                STATUS_STOPPED (int): 播放状态-停止状态，值为0
                STATUS_PLAYING (int): 播放状态-播放状态，值为1
                STATUS_PAUSED (int): 播放状态-暂停状态，值为2
                READ_DELAY (float): 串口读取延迟时间（秒），确保模块有足够时间返回数据，值为0.1
                uart (UART): MicroPython UART 实例，用于与 JQ6500 模块通信

            Methods:
                __init__(uart: UART, volume: int = 20) -> None: 初始化播放器实例，指定UART对象并设置初始音量
                clean_up() -> None: 清理资源并释放UART端口
                play() -> None: 播放当前选中的音频文件
                play_pause() -> None: 切换播放/暂停状态
                restart() -> None: 重新播放当前文件（从头开始）
                pause() -> None: 暂停当前播放的音频文件
                next() -> None: 切换到下一个音频文件并播放
                prev() -> None: 切换到上一个音频文件并播放
                next_folder() -> None: 切换到下一个文件夹并播放其中的音频文件（仅SD卡有效）
                prev_folder() -> None: 切换到上一个文件夹并播放其中的音频文件（仅SD卡有效）
                play_by_index(file_index: int) -> None: 通过FAT表索引播放指定文件
                play_by_number(folder_number: int, file_number: int) -> None: 通过文件夹编号+文件编号播放指定文件（仅SD卡）
                volume_up() -> None: 音量加1（范围0-30）
                volume_down() -> None: 音量减1（范围0-30）
                set_volume(level: int) -> None: 设置指定音量值（0-30）
                set_equalizer(mode: int) -> None: 设置音效模式（普通/流行/摇滚/爵士/古典/重低音）
                set_looping(mode: int) -> None: 设置循环播放模式
                set_source(source: int) -> None: 设置音源（SD卡/内置Flash）
                sleep() -> None: 使模块进入睡眠模式（不建议SD卡使用）
                reset() -> None: 软复位模块（可靠性较低，建议断电重启）
                get_status() -> int: 获取当前播放状态（停止/播放/暂停）
                get_volume() -> int: 获取当前音量值
                get_equalizer() -> int: 获取当前音效模式
                get_looping() -> int: 获取当前循环模式
                get_file_count(source: int) -> int: 获取指定音源的文件总数
                get_folder_count(source: int) -> int: 获取指定音源的文件夹数量（仅SD卡有效）
                get_file_index(source: int) -> int: 获取当前播放文件的FAT索引
                get_position() -> int: 获取当前播放进度（秒）
                get_length() -> int: 获取当前文件的总时长（秒）
                get_name() -> Optional[bytes]: 获取当前播放文件的文件名（仅SD卡）
                get_version() -> int: 获取模块固件版本号
                read_buffer() -> Optional[bytes]: 读取UART缓冲区所有数据
                read_bytes() -> int: 读取4字节数据并转换为十六进制整数
                write_bytes(b: List[int]) -> None: 向模块发送指令字节（自动封装通信协议）

            Notes:
                1. SD卡功能仅JQ6500-28P型号支持
                2. 内置Flash无文件夹功能，所有文件按烧录顺序排列
                3. 软复位功能可靠性较低，建议优先使用断电重启

    ==========================================
            JQ6500 mini MP3 module driver class, which implements complete control of the MP3 player based on the UART interface.
            It supports core functions such as play/pause/previous/next track, volume adjustment, EQ setting, loop mode, file positioning playback,
            and also provides auxiliary functions such as status query and file information reading.

            Attributes:
                EQ_NORMAL (int): EQ mode - Normal mode, value is 0
                EQ_POP (int): EQ mode - Pop mode, value is 1
                EQ_ROCK (int): EQ mode - Rock mode, value is 2
                EQ_JAZZ (int): EQ mode - Jazz mode, value is 3
                EQ_CLASSIC (int): EQ mode - Classic mode, value is 4
                EQ_BASS (int): EQ mode - Bass mode, value is 5
                SRC_SDCARD (int): Audio source - SD card (only supported by JQ6500-28P model), value is 1
                SRC_BUILTIN (int): Audio source - Built-in Flash, value is 4
                LOOP_ALL (int): Loop mode - All loop, play all tracks and repeat, value is 0
                LOOP_FOLDER (int): Loop mode - Folder loop, play all tracks in the current folder and repeat, value is 1
                LOOP_ONE (int): Loop mode - Single loop, play the current track and repeat, value is 2
                LOOP_RAM (int): Loop mode - RAM loop (undefined), value is 3
                LOOP_ONE_STOP (int): Loop mode - Single play stop, stop after playing the current track, value is 4
                LOOP_NONE (int): Loop mode - No loop, same as LOOP_ONE_STOP, value is 4
                STATUS_STOPPED (int): Playback status - Stopped, value is 0
                STATUS_PLAYING (int): Playback status - Playing, value is 1
                STATUS_PAUSED (int): Playback status - Paused, value is 2
                READ_DELAY (float): Serial port read delay time (seconds) to ensure the module has enough time to return data, value is 0.1
                uart (UART): MicroPython UART instance for communication with the JQ6500 module

            Methods:
                __init__(uart: UART, volume: int = 20) -> None: Initialize the player instance, specify the UART object and set the initial volume
                clean_up() -> None: Clean up resources and release the UART port
                play() -> None: Play the currently selected audio file
                play_pause() -> None: Toggle play/pause status
                restart() -> None: Restart the current file (play from the beginning)
                pause() -> None: Pause the currently playing audio file
                next() -> None: Switch to and play the next audio file
                prev() -> None: Switch to and play the previous audio file
                next_folder() -> None: Switch to the next folder and play audio files in it (only valid for SD card)
                prev_folder() -> None: Switch to the previous folder and play audio files in it (only valid for SD card)
                play_by_index(file_index: int) -> None: Play the specified file by FAT table index
                play_by_number(folder_number: int, file_number: int) -> None: Play the specified file by folder number + file number (only valid for SD card)
                volume_up() -> None: Increase volume by 1 (range 0-30)
                volume_down() -> None: Decrease volume by 1 (range 0-30)
                set_volume(level: int) -> None: Set the specified volume value (0-30)
                set_equalizer(mode: int) -> None: Set EQ mode (Normal/Pop/Rock/Jazz/Classic/Bass)
                set_looping(mode: int) -> None: Set loop playback mode
                set_source(source: int) -> None: Set audio source (SD card/Built-in Flash)
                sleep() -> None: Put the module into sleep mode (not recommended for SD card use)
                reset() -> None: Soft reset the module (low reliability, power off and restart is recommended)
                get_status() -> int: Get the current playback status (Stopped/Playing/Paused)
                get_volume() -> int: Get the current volume value
                get_equalizer() -> int: Get the current EQ mode
                get_looping() -> int: Get the current loop mode
                get_file_count(source: int) -> int: Get the total number of files of the specified audio source
                get_folder_count(source: int) -> int: Get the number of folders of the specified audio source (only valid for SD card)
                get_file_index(source: int) -> int: Get the FAT index of the currently playing file
                get_position() -> int: Get the current playback progress (seconds)
                get_length() -> int: Get the total duration of the current file (seconds)
                get_name() -> Optional[bytes]: Get the file name of the currently playing file (only valid for SD card)
                get_version() -> int: Get the module firmware version number
                read_buffer() -> Optional[bytes]: Read all data in the UART buffer and return it
                read_bytes() -> int: Read 4 bytes of data from the UART port and convert to hexadecimal integer
                write_bytes(b: List[int]) -> None: Send command bytes to the module (automatically encapsulate JQ6500 communication protocol)

            Notes:
                1. SD card function is only supported by JQ6500-28P model
                2. Built-in Flash has no folder function, all files are arranged in burning order
                3. Soft reset function has low reliability, power off and restart is recommended
    """

    # 音效模式常量-普通模式
    EQ_NORMAL: int = 0
    # 音效模式常量-流行模式
    EQ_POP: int = 1
    # 音效模式常量-摇滚模式
    EQ_ROCK: int = 2
    # 音效模式常量-爵士模式
    EQ_JAZZ: int = 3
    # 音效模式常量-古典模式
    EQ_CLASSIC: int = 4
    # 音效模式常量-重低音模式
    EQ_BASS: int = 5

    # 音源选择常量-SD卡（仅JQ6500-28P型号支持）
    SRC_SDCARD: int = 1
    # 音源选择常量-内置Flash
    SRC_BUILTIN: int = 4

    # 循环模式常量-全部循环
    LOOP_ALL: int = 0
    # 循环模式常量-文件夹循环
    LOOP_FOLDER: int = 1
    # 循环模式常量-单曲循环
    LOOP_ONE: int = 2
    # 循环模式常量-RAM循环（未明确定义）
    LOOP_RAM: int = 3
    # 循环模式常量-单曲播放停止
    LOOP_ONE_STOP: int = 4
    # 循环模式常量-无循环
    LOOP_NONE: int = 4

    # 播放状态常量-停止状态
    STATUS_STOPPED: int = 0
    # 播放状态常量-播放状态
    STATUS_PLAYING: int = 1
    # 播放状态常量-暂停状态
    STATUS_PAUSED: int = 2

    # 串口读取延迟:确保模块有足够时间返回数据
    READ_DELAY: float = 0.1

    def __init__(self, uart: UART, volume: int = 20) -> None:
        """
                初始化 JQ6500 播放器实例。

                Args:
                    uart (UART): MicroPython的UART实例，已初始化好波特率等参数
                    volume (int, 可选): 初始音量值（范围 0-30），默认值为 20

                Raises:
                    TypeError: uart不是UART实例时触发
                    ValueError: volume超出0-30范围时触发

                Notes:
                    UART波特率需固定设置为9600，这是JQ6500模块的通信波特率

        ==========================================
                Initialize the JQ6500 player instance.

                Args:
                    uart (UART): MicroPython UART instance with initialized baud rate and other parameters
                    volume (int, optional): Initial volume level (range 0-30), default value is 20

                Raises:
                    TypeError: Triggered when uart is not a UART instance
                    ValueError: Triggered when volume is out of the range of 0-30

                Notes:
                    The UART baud rate must be fixed at 9600, which is the communication baud rate of the JQ6500 module
        """
        # 参数验证-检查uart是否为UART实例
        if not isinstance(uart, UART):
            raise TypeError(f"uart must be a UART instance, current type: {type(uart)}")
        # 参数验证-检查volume是否为0-30的整数
        if not isinstance(volume, int) or not (0 <= volume <= 30):
            raise ValueError(f"volume must be an integer between 0 and 30, current value: {volume}")

        # 初始化UART属性
        self.uart = uart
        # 清空UART缓冲区
        self.uart.read()
        # 复位模块
        self.reset()
        # 设置初始音量
        self.set_volume(volume)

    def clean_up(self) -> None:
        """
                清理资源并释放 UART 端口，避免资源泄漏。

                Args:
                    无

                Raises:
                    无

                Notes:
                    释放UART端口前先复位模块，确保模块处于初始状态

        ==========================================
                Clean up resources and release the UART port to avoid resource leaks.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Reset the module before releasing the UART port to ensure the module is in the initial state
        """
        # 复位模块
        self.reset()
        # 检查UART是否有deinit方法，有则释放端口
        if "deinit" in dir(self.uart):
            self.uart.deinit()

    def play(self) -> None:
        """
                播放当前选中的音频文件。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送播放指令0x0D到JQ6500模块

        ==========================================
                Play the currently selected audio file.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send play command 0x0D to the JQ6500 module
        """
        # 发送播放指令
        self.write_bytes([0x0D])

    def play_pause(self) -> None:
        """
                切换播放/暂停状态。

                Args:
                    无

                Raises:
                    无

                Notes:
                    根据当前播放状态自动切换，停止/暂停状态下执行播放，播放状态下执行暂停

        ==========================================
                Toggle play/pause status.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Automatically switch according to the current playback status, execute play in stopped/paused state, execute pause in playing state
        """
        # 获取当前播放状态
        status = self.get_status()
        # 停止或暂停状态则播放
        if status == self.STATUS_PAUSED or status == self.STATUS_STOPPED:
            self.play()
        # 播放状态则暂停
        elif status == self.STATUS_PLAYING:
            self.pause()

    def restart(self) -> None:
        """
                重新播放当前文件（从头开始）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    通过先切下一曲再切回上一曲的方式实现重新播放，过程中暂时静音避免爆音

        ==========================================
                Restart the current file (play from the beginning).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Achieve restart by switching to the next track first and then back to the previous track, mute temporarily during the process to avoid pop noise
        """
        # 保存当前音量
        old_volume = self.get_volume()
        # 暂时设置音量为0（静音）
        self.set_volume(0)
        # 切换到下一曲
        self.next()
        # 暂停播放
        self.pause()
        # 恢复原有音量
        self.set_volume(old_volume)
        # 切回上一曲（即当前文件开头）
        self.prev()

    def pause(self) -> None:
        """
                暂停当前播放的音频文件。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送暂停指令0x0E到JQ6500模块

        ==========================================
                Pause the currently playing audio file.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send pause command 0x0E to the JQ6500 module
        """
        # 发送暂停指令
        self.write_bytes([0x0E])

    def next(self) -> None:
        """
                切换到下一个音频文件并播放。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送下一曲指令0x01到JQ6500模块

        ==========================================
                Switch to and play the next audio file.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send next track command 0x01 to the JQ6500 module
        """
        # 发送下一曲指令
        self.write_bytes([0x01])

    def prev(self) -> None:
        """
                切换到上一个音频文件并播放。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送上一曲指令0x02到JQ6500模块

        ==========================================
                Switch to and play the previous audio file.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send previous track command 0x02 to the JQ6500 module
        """
        # 发送上一曲指令
        self.write_bytes([0x02])

    def next_folder(self) -> None:
        """
                切换到下一个文件夹并播放其中的音频文件（仅SD卡有效）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送下一个文件夹指令0x0F 0x01到JQ6500模块，该功能仅在使用SD卡作为音源时有效

        ==========================================
                Switch to the next folder and play audio files in it (only valid for SD card).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send next folder command 0x0F 0x01 to the JQ6500 module, this function is only valid when using SD card as audio source
        """
        # 发送下一个文件夹指令
        self.write_bytes([0x0F, 0x01])

    def prev_folder(self) -> None:
        """
                切换到上一个文件夹并播放其中的音频文件（仅SD卡有效）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送上一个文件夹指令0x0F 0x00到JQ6500模块，该功能仅在使用SD卡作为音源时有效

        ==========================================
                Switch to the previous folder and play audio files in it (only valid for SD card).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send previous folder command 0x0F 0x00 to the JQ6500 module, this function is only valid when using SD card as audio source
        """
        # 发送上一个文件夹指令
        self.write_bytes([0x0F, 0x00])

    def play_by_index(self, file_index: int) -> None:
        """
                通过 FAT 表索引播放指定文件。

                Args:
                    file_index (int): 文件在FAT表中的索引编号

                Raises:
                    ValueError: file_index为负数或非整数时触发

                Notes:
                    文件索引需为非负整数，指令格式为0x03 + 高位字节 + 低位字节

        ==========================================
                Play the specified file by FAT table index.

                Args:
                    file_index (int): File index number in the FAT table

                Raises:
                    ValueError: Triggered when file_index is negative or not an integer

                Notes:
                    The file index must be a non-negative integer, and the command format is 0x03 + high byte + low byte
        """
        # 参数验证-检查file_index是否为非负整数
        if not isinstance(file_index, int) or file_index < 0:
            raise ValueError(f"file_index must be a non-negative integer, current value: {file_index}")

        # 发送按索引播放指令，拆分索引为高低字节
        self.write_bytes([0x03, (file_index >> 8) & 0xFF, file_index & 0xFF])

    def play_by_number(self, folder_number: int, file_number: int) -> None:
        """
                通过文件夹编号和文件编号播放指定文件（仅SD卡有效）。

                Args:
                    folder_number (int): 文件夹名称编号（00-99）
                    file_number (int): 文件名称编号（000-999）

                Raises:
                    ValueError: folder_number超出0-99范围或file_number超出0-999范围时触发

                Notes:
                    该功能仅在使用SD卡作为音源时有效，文件夹编号和文件编号均需为非负整数

        ==========================================
                Play the specified file by folder number and file number (only valid for SD card).

                Args:
                    folder_number (int): Folder name number (00-99)
                    file_number (int): File name number (000-999)

                Raises:
                    ValueError: Triggered when folder_number is out of 0-99 range or file_number is out of 0-999 range

                Notes:
                    This function is only valid when using SD card as audio source, both folder number and file number must be non-negative integers
        """
        # 参数验证-检查folder_number是否为0-99的整数
        if not isinstance(folder_number, int) or not (0 <= folder_number <= 99):
            raise ValueError(f"folder_number must be an integer between 0 and 99, current value: {folder_number}")
        # 参数验证-检查file_number是否为0-999的整数
        if not isinstance(file_number, int) or not (0 <= file_number <= 999):
            raise ValueError(f"file_number must be an integer between 0 and 999, current value: {file_number}")

        # 发送按编号播放指令
        self.write_bytes([0x12, folder_number & 0xFF, file_number & 0xFF])

    def volume_up(self) -> None:
        """
                音量加1（范围0-30）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送音量加指令0x04到JQ6500模块，音量达到30后继续执行该指令无效

        ==========================================
                Increase volume by 1 (range 0-30).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send volume up command 0x04 to the JQ6500 module, executing this command after volume reaches 30 has no effect
        """
        # 发送音量加指令
        self.write_bytes([0x04])

    def volume_down(self) -> None:
        """
                音量减1（范围0-30）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送音量减指令0x05到JQ6500模块，音量达到0后继续执行该指令无效

        ==========================================
                Decrease volume by 1 (range 0-30).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send volume down command 0x05 to the JQ6500 module, executing this command after volume reaches 0 has no effect
        """
        # 发送音量减指令
        self.write_bytes([0x05])

    def set_volume(self, level: int) -> None:
        """
                设置指定音量值（0-30）。

                Args:
                    level (int): 音量值（范围 0-30）

                Raises:
                    ValueError: 音量值超出0-30范围时触发

                Notes:
                    发送音量设置指令0x06 + 音量值到JQ6500模块，音量值超出范围会触发异常

        ==========================================
                Set the specified volume value (0-30).

                Args:
                    level (int): Volume value (range 0-30)

                Raises:
                    ValueError: Triggered when the volume value is out of the range of 0-30

                Notes:
                    Send volume setting command 0x06 + volume value to the JQ6500 module, an exception will be triggered if the volume value is out of range
        """
        # 参数验证-检查level是否为0-30的整数
        if not isinstance(level, int) or not (0 <= level <= 30):
            raise ValueError(f"Volume level must be an integer between 0 and 30, current value: {level}")

        # 发送音量设置指令
        self.write_bytes([0x06, level])

    def set_equalizer(self, mode: int) -> None:
        """
                设置音效模式（6种预设模式可选）。

                Args:
                    mode (int): 音效模式（EQ_NORMAL/EQ_POP/EQ_ROCK/EQ_JAZZ/EQ_CLASSIC/EQ_BASS）

                Raises:
                    ValueError: mode不是有效音效模式时触发

                Notes:
                    发送音效设置指令0x07 + 模式值到JQ6500模块，仅支持预设的6种音效模式

        ==========================================
                Set EQ mode (6 preset modes available).

                Args:
                    mode (int): EQ mode (EQ_NORMAL/EQ_POP/EQ_ROCK/EQ_JAZZ/EQ_CLASSIC/EQ_BASS)

                Raises:
                    ValueError: Triggered when mode is not a valid EQ mode

                Notes:
                    Send EQ setting command 0x07 + mode value to the JQ6500 module, only 6 preset EQ modes are supported
        """
        # 定义有效音效模式列表
        valid_modes = [self.EQ_NORMAL, self.EQ_POP, self.EQ_ROCK, self.EQ_JAZZ, self.EQ_CLASSIC, self.EQ_BASS]
        # 参数验证-检查mode是否为有效音效模式
        if mode not in valid_modes:
            raise ValueError(f"Invalid EQ mode, valid values: {valid_modes}, current value: {mode}")

        # 发送音效设置指令
        self.write_bytes([0x07, mode])

    def set_looping(self, mode: int) -> None:
        """
                设置循环播放模式。

                Args:
                    mode (int): 循环模式（LOOP_ALL/LOOP_FOLDER/LOOP_ONE/LOOP_RAM/LOOP_ONE_STOP/LOOP_NONE）

                Raises:
                    ValueError: mode不是有效循环模式时触发

                Notes:
                    发送循环模式设置指令0x11 + 模式值到JQ6500模块，LOOP_NONE与LOOP_ONE_STOP效果相同

        ==========================================
                Set loop playback mode.

                Args:
                    mode (int): Loop mode (LOOP_ALL/LOOP_FOLDER/LOOP_ONE/LOOP_RAM/LOOP_ONE_STOP/LOOP_NONE)

                Raises:
                    ValueError: Triggered when mode is not a valid loop mode

                Notes:
                    Send loop mode setting command 0x11 + mode value to the JQ6500 module, LOOP_NONE has the same effect as LOOP_ONE_STOP
        """
        # 定义有效循环模式列表
        valid_modes = [self.LOOP_ALL, self.LOOP_FOLDER, self.LOOP_ONE, self.LOOP_RAM, self.LOOP_ONE_STOP, self.LOOP_NONE]
        # 参数验证-检查mode是否为有效循环模式
        if mode not in valid_modes:
            raise ValueError(f"Invalid loop mode, valid values: {valid_modes}, current value: {mode}")

        # 发送循环模式设置指令
        self.write_bytes([0x11, mode])

    def set_source(self, source: int) -> None:
        """
                设置MP3文件的音源位置（SD卡/内置Flash）。

                Args:
                    source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）

                Raises:
                    ValueError: source不是有效音源类型时触发

                Notes:
                    发送音源设置指令0x09 + 音源值到JQ6500模块，仅支持SD卡和内置Flash两种音源

        ==========================================
                Set the audio source position of MP3 files (SD card/Built-in Flash).

                Args:
                    source (int): Audio source type (SRC_SDCARD/SRC_BUILTIN)

                Raises:
                    ValueError: Triggered when source is not a valid audio source type

                Notes:
                    Send audio source setting command 0x09 + source value to the JQ6500 module, only SD card and Built-in Flash are supported
        """
        # 定义有效音源类型列表
        valid_sources = [self.SRC_SDCARD, self.SRC_BUILTIN]
        # 参数验证-检查source是否为有效音源类型
        if source not in valid_sources:
            raise ValueError(f"Invalid audio source, valid values: {valid_sources}, current value: {source}")

        # 发送音源设置指令
        self.write_bytes([0x09, source])

    def sleep(self) -> None:
        """
                使模块进入睡眠模式，降低功耗。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送睡眠指令0x0A到JQ6500模块，该功能不建议在使用SD卡作为音源时使用

        ==========================================
                Put the module into sleep mode to reduce power consumption.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send sleep command 0x0A to the JQ6500 module, this function is not recommended when using SD card as audio source
        """
        # 发送睡眠指令
        self.write_bytes([0x0A])

    def reset(self) -> None:
        """
                软复位模块，恢复到初始状态。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送复位指令0x0C到JQ6500模块，复位后模块音量恢复为默认值，软复位可靠性较低，建议优先使用断电重启

        ==========================================
                Soft reset the module to restore to the initial state.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send reset command 0x0C to the JQ6500 module, the module volume returns to the default value after reset, soft reset has low reliability, power off and restart is recommended
        """
        # 发送复位指令
        self.write_bytes([0x0C])
        # 延迟0.5秒，等待模块完成复位
        sleep(0.5)

    def get_status(self) -> int:
        """
                获取模块当前播放状态。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送状态查询指令0x42到JQ6500模块，返回值为0（停止）、1（播放）、2（暂停），查询失败返回-1

        ==========================================
                Get the current playback status of the module.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send status query command 0x42 to the JQ6500 module, the return value is 0 (stopped), 1 (playing), 2 (paused), returns -1 if query fails
        """
        # 发送状态查询指令
        self.write_bytes([0x42])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取返回数据
        status = self.uart.read()
        # 再次延迟确保数据读取完整
        sleep(self.READ_DELAY)
        # 检查返回数据是否为数字，是则转换为整数返回
        if status and status.isdigit():
            return int(status)
        # 数据无效则返回-1
        else:
            return -1

    def get_volume(self) -> int:
        """
                获取当前音量值（0-30）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送音量查询指令0x43到JQ6500模块，通过read_bytes方法读取返回的音量值

        ==========================================
                Get the current volume value (0-30).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send volume query command 0x43 to the JQ6500 module, read the returned volume value through the read_bytes method
        """
        # 发送音量查询指令
        self.write_bytes([0x43])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换音量值
        level = self.read_bytes()
        # 返回音量值
        return level

    def get_equalizer(self) -> int:
        """
                获取当前音效模式。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送音效模式查询指令0x44到JQ6500模块，返回值对应预设的6种音效模式

        ==========================================
                Get the current EQ mode.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send EQ mode query command 0x44 to the JQ6500 module, the return value corresponds to the 6 preset EQ modes
        """
        # 发送音效模式查询指令
        self.write_bytes([0x44])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换音效模式值
        eq = self.read_bytes()
        # 返回音效模式值
        return eq

    def get_looping(self) -> int:
        """
                获取当前循环模式。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送循环模式查询指令0x45到JQ6500模块，返回值对应预设的循环模式

        ==========================================
                Get the current loop mode.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send loop mode query command 0x45 to the JQ6500 module, the return value corresponds to the preset loop modes
        """
        # 发送循环模式查询指令
        self.write_bytes([0x45])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换循环模式值
        looping = self.read_bytes()
        # 返回循环模式值
        return looping

    def get_file_count(self, source: int) -> int:
        """
                获取指定音源的文件总数。

                Args:
                    source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）

                Raises:
                    ValueError: source不是有效音源类型时触发

                Notes:
                    发送文件总数查询指令到JQ6500模块，SD卡对应指令0x47，内置Flash对应指令0x49

        ==========================================
                Get the total number of files of the specified audio source.

                Args:
                    source (int): Audio source type (SRC_SDCARD/SRC_BUILTIN)

                Raises:
                    ValueError: Triggered when source is not a valid audio source type

                Notes:
                    Send file count query command to the JQ6500 module, 0x47 for SD card, 0x49 for Built-in Flash
        """
        # 定义有效音源类型列表
        valid_sources = [self.SRC_SDCARD, self.SRC_BUILTIN]
        # 参数验证-检查source是否为有效音源类型
        if source not in valid_sources:
            raise ValueError(f"Invalid audio source, valid values: {valid_sources}, current value: {source}")

        # 根据音源类型选择对应的查询指令
        if source == self.SRC_SDCARD:
            self.write_bytes([0x47])
        else:
            self.write_bytes([0x49])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换文件总数
        count = self.read_bytes()
        # 返回文件总数
        return count

    def get_folder_count(self, source: int) -> int:
        """
                获取指定音源的文件夹数量（仅SD卡有效）。

                Args:
                    source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）

                Raises:
                    ValueError: source不是有效音源类型时触发

                Notes:
                    发送文件夹数量查询指令0x53到JQ6500模块，仅SD卡有文件夹概念，内置Flash返回0

        ==========================================
                Get the number of folders of the specified audio source (only valid for SD card).

                Args:
                    source (int): Audio source type (SRC_SDCARD/SRC_BUILTIN)

                Raises:
                    ValueError: Triggered when source is not a valid audio source type

                Notes:
                    Send folder count query command 0x53 to the JQ6500 module, only SD card has folder concept, Built-in Flash returns 0
        """
        # 定义有效音源类型列表
        valid_sources = [self.SRC_SDCARD, self.SRC_BUILTIN]
        # 参数验证-检查source是否为有效音源类型
        if source not in valid_sources:
            raise ValueError(f"Invalid audio source, valid values: {valid_sources}, current value: {source}")

        # 仅SD卡查询文件夹数量，内置Flash直接返回0
        if source == self.SRC_SDCARD:
            # 发送文件夹数量查询指令
            self.write_bytes([0x53])
            # 延迟等待模块返回数据
            sleep(self.READ_DELAY)
            # 读取并转换文件夹数量
            count = self.read_bytes()
            # 返回文件夹数量
            return count
        else:
            # 内置Flash无文件夹，返回0
            return 0

    def get_file_index(self, source: int) -> int:
        """
                获取当前播放文件的FAT表索引。

                Args:
                    source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）

                Raises:
                    ValueError: source不是有效音源类型时触发

                Notes:
                    SD卡对应查询指令0x4B，内置Flash对应查询指令0x4D，内置Flash返回值需加1

        ==========================================
                Get the FAT table index of the currently playing file.

                Args:
                    source (int): Audio source type (SRC_SDCARD/SRC_BUILTIN)

                Raises:
                    ValueError: Triggered when source is not a valid audio source type

                Notes:
                    0x4B for SD card query command, 0x4D for Built-in Flash query command, the return value of Built-in Flash needs to be added 1
        """
        # 定义有效音源类型列表
        valid_sources = [self.SRC_SDCARD, self.SRC_BUILTIN]
        # 参数验证-检查source是否为有效音源类型
        if source not in valid_sources:
            raise ValueError(f"Invalid audio source, valid values: {valid_sources}, current value: {source}")

        # 根据音源类型选择对应的查询指令
        if source == self.SRC_SDCARD:
            self.write_bytes([0x4B])
            # 延迟等待模块返回数据
            sleep(self.READ_DELAY)
            # 读取并转换文件索引
            count = self.read_bytes()
            # 返回文件索引
            return count
        else:
            self.write_bytes([0x4D])
            # 延迟等待模块返回数据
            sleep(self.READ_DELAY)
            # 读取并转换文件索引，内置Flash需加1
            count = self.read_bytes()
            # 返回加1后的文件索引
            return count + 1

    def get_position(self) -> int:
        """
                获取当前文件的播放进度（秒）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送播放进度查询指令0x50到JQ6500模块，返回值为当前播放的秒数

        ==========================================
                Get the current playback progress of the file (seconds).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send playback progress query command 0x50 to the JQ6500 module, the return value is the number of seconds currently played
        """
        # 发送播放进度查询指令
        self.write_bytes([0x50])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换播放进度
        position = self.read_bytes()
        # 返回播放进度
        return position

    def get_length(self) -> int:
        """
                获取当前文件的总时长（秒）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送文件时长查询指令0x51到JQ6500模块，返回值为文件的总秒数

        ==========================================
                Get the total duration of the current file (seconds).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send file duration query command 0x51 to the JQ6500 module, the return value is the total number of seconds of the file
        """
        # 发送文件时长查询指令
        self.write_bytes([0x51])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换文件时长
        length = self.read_bytes()
        # 返回文件时长
        return length

    def get_name(self) -> Optional[bytes]:
        """
                获取当前播放文件的文件名（仅SD卡有效）。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送文件名查询指令0x52到JQ6500模块，仅SD卡能返回文件名，内置Flash返回None

        ==========================================
                Get the file name of the currently playing file (only valid for SD card).

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send file name query command 0x52 to the JQ6500 module, only SD card can return file name, Built-in Flash returns None
        """
        # 发送文件名查询指令
        self.write_bytes([0x52])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并返回文件名
        return self.uart.read()

    def get_version(self) -> int:
        """
                获取模块固件版本号。

                Args:
                    无

                Raises:
                    无

                Notes:
                    发送版本查询指令0x46到JQ6500模块，返回值为固件版本号的整数形式

        ==========================================
                Get the module firmware version number.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Send version query command 0x46 to the JQ6500 module, the return value is the integer form of the firmware version number
        """
        # 发送版本查询指令
        self.write_bytes([0x46])
        # 延迟等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换版本号
        version = self.read_bytes()
        # 返回版本号
        return version

    def read_buffer(self) -> Optional[bytes]:
        """
                读取UART缓冲区所有数据并返回。

                Args:
                    无

                Raises:
                    无

                Notes:
                    直接读取UART缓冲区数据，无数据时返回None

        ==========================================
                Read all data in the UART buffer and return it.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Directly read the UART buffer data, return None when there is no data
        """
        # 读取UART缓冲区数据并返回
        return self.uart.read()

    def read_bytes(self) -> int:
        """
                从UART端口读取4字节数据并转换为十六进制整数。

                Args:
                    无

                Raises:
                    无

                Notes:
                    读取4字节数据，转换为十六进制整数返回，数据不足或无效时返回-1

        ==========================================
                Read 4 bytes of data from the UART port and convert to hexadecimal integer.

                Args:
                    None

                Raises:
                    None

                Notes:
                    Read 4 bytes of data, convert to hexadecimal integer and return, return -1 when data is insufficient or invalid
        """
        # 读取4字节数据
        b = self.uart.read(4)
        # 打印原始字节数据（调试用）
        print(b)
        # 检查数据是否有效
        if b and len(b) > 0:
            # 转换为十六进制整数返回
            return int(b, 16)
        else:
            # 数据无效返回-1
            return -1

    def write_bytes(self, b: List[int]) -> None:
        """
                向模块发送指令字节（自动封装JQ6500通信协议）。

                Args:
                    b (List[int]): 要发送的指令字节列表

                Raises:
                    TypeError: b不是整数列表时触发

                Notes:
                    自动封装JQ6500通信协议，格式为0x7E + 长度 + 指令字节 + 0xEF

        ==========================================
                Send command bytes to the module (automatically encapsulate JQ6500 communication protocol).

                Args:
                    b (List[int]): List of command bytes to send

                Raises:
                    TypeError: Triggered when b is not a list of integers

                Notes:
                    Automatically encapsulate the JQ6500 communication protocol, the format is 0x7E + length + command bytes + 0xEF
        """
        # 参数验证-检查b是否为整数列表
        if not isinstance(b, list) or not all(isinstance(x, int) for x in b):
            raise TypeError(f"b must be a list of integers, current type: {type(b)}, content: {b}")

        # 计算指令长度
        message_length = len(b) + 1
        # 封装通信协议
        data = [0x7E, message_length] + b + [0xEF]
        # 清空UART缓冲区
        self.uart.read()
        # 发送封装后的指令
        self.uart.write(bytes(data))


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
