# -*- coding: utf-8 -*-
# @Time    : 2026/3/3
# @Author  : rdagger
# @File    : jq6500.py
# @Description : JQ6500 mini MP3模块驱动（MicroPython）参考自:https://github.com/rdagger/micropython-jq6500
# @License : MIT

__version__ = "0.1.0"
__author__ = "rdagger"
__license__ = "MIT"
__platform__ = "MicroPython"

# ======================================== 导入相关模块 =========================================
# 导入MicroPython的UART串口通信模块
from machine import UART

# 导入时间延迟模块
from time import sleep

# ======================================== 自定义类 ============================================


class Player(object):
    """
    JQ6500 迷你 MP3 模块驱动类，基于 UART 接口实现对 MP3 播放器的完整控制。
    支持播放/暂停/上一曲/下一曲、音量调节、EQ 设置、循环模式、文件定位播放等核心功能，
    同时提供状态查询、文件信息读取等辅助功能。

    Attributes:
        EQ_NORMAL/EQ_POP/EQ_ROCK/EQ_JAZZ/EQ_CLASSIC/EQ_BASS: 音效模式常量（0-5）。
        SRC_SDCARD/SRC_BUILTIN: 音源选择常量（SD卡/内置Flash）。
        LOOP_ALL/LOOP_FOLDER/LOOP_ONE/LOOP_RAM/LOOP_ONE_STOP/LOOP_NONE: 循环模式常量（0-4）。
        STATUS_STOPPED/STATUS_PLAYING/STATUS_PAUSED: 播放状态常量（0-2）。
        READ_DELAY: 串口读取延迟时间（秒），确保数据回传稳定。
        uart (UART): MicroPython UART 实例，用于与 JQ6500 模块通信。

    Methods:
        __init__(port=2, volume=20):
            初始化播放器实例，指定 UART 端口并设置初始音量。
        clean_up():
            清理资源并释放 UART 端口。
        play():
            播放当前文件。
        play_pause():
            切换播放/暂停状态。
        restart():
            重新播放当前文件（从头开始）。
        pause():
            暂停当前播放。
        next():
            播放下一曲。
        prev():
            播放上一曲。
        next_folder():
            切换到下一个文件夹播放。
        prev_folder():
            切换到上一个文件夹播放。
        play_by_index(file_index):
            通过 FAT 表索引播放指定文件。
        play_by_number(folder_number, file_number):
            通过文件夹编号+文件编号播放指定文件（仅SD卡）。
        volume_up():
            音量加1（范围 0-30）。
        volume_down():
            音量减1（范围 0-30）。
        set_volume(level):
            设置指定音量值（0-30）。
        set_equalizer(mode):
            设置音效模式（普通/流行/摇滚/爵士/古典/重低音）。
        set_looping(mode):
            设置循环播放模式。
        set_source(source):
            设置音源（SD卡/内置Flash）。
        sleep():
            使模块进入睡眠模式（不建议SD卡使用）。
        reset():
            软复位模块（可靠性较低，建议断电重启）。
        get_status():
            获取当前播放状态（停止/播放/暂停）。
        get_volume():
            获取当前音量值。
        get_equalizer():
            获取当前音效模式。
        get_looping():
            获取当前循环模式。
        get_file_count(source):
            获取指定音源的文件总数。
        get_folder_count(source):
            获取指定音源的文件夹数量（仅SD卡有效）。
        get_file_index(source):
            获取当前播放文件的 FAT 索引。
        get_position():
            获取当前播放进度（秒）。
        get_length():
            获取当前文件总时长（秒）。
        get_name():
            获取当前播放文件的文件名（仅SD卡）。
        get_version():
            获取模块固件版本号。
        read_buffer():
            读取 UART 缓冲区所有数据。
        read_bytes():
            读取 4 字节数据并转换为十六进制整数。
        write_bytes(b):
            向模块发送指令字节（自动封装通信协议）。

    ==========================================

    JQ6500 mini MP3 module driver class, implementing full control of the MP3 player via UART interface.
    Supports core functions such as play/pause/previous/next track, volume adjustment, EQ setting,
    loop mode, and file positioning playback, while providing auxiliary functions like status query
    and file information reading.

    Attributes:
        EQ_NORMAL/EQ_POP/EQ_ROCK/EQ_JAZZ/EQ_CLASSIC/EQ_BASS: EQ mode constants (0-5).
        SRC_SDCARD/SRC_BUILTIN: Source selection constants (SD card / built-in Flash).
        LOOP_ALL/LOOP_FOLDER/LOOP_ONE/LOOP_RAM/LOOP_ONE_STOP/LOOP_NONE: Loop mode constants (0-4).
        STATUS_STOPPED/STATUS_PLAYING/STATUS_PAUSED: Playback status constants (0-2).
        READ_DELAY: Serial port read delay time (seconds) to ensure stable data return.
        uart (UART): MicroPython UART instance for communication with JQ6500 module.

    Methods:
        __init__(port=2, volume=20):
            Initialize player instance, specify UART port and set initial volume.
        clean_up():
            Clean up resources and release UART port.
        play():
            Play current file.
        play_pause():
            Toggle play/pause status.
        restart():
            Restart current file (play from beginning).
        pause():
            Pause current playback.
        next():
            Play next track.
        prev():
            Play previous track.
        next_folder():
            Switch to next folder for playback.
        prev_folder():
            Switch to previous folder for playback.
        play_by_index(file_index):
            Play specified file via FAT table index.
        play_by_number(folder_number, file_number):
            Play specified file via folder number + file number (SD card only).
        volume_up():
            Increase volume by 1 (range 0-30).
        volume_down():
            Decrease volume by 1 (range 0-30).
        set_volume(level):
            Set specific volume value (0-30).
        set_equalizer(mode):
            Set EQ mode (Normal/Pop/Rock/Jazz/Classic/Bass).
        set_looping(mode):
            Set loop playback mode.
        set_source(source):
            Set audio source (SD card / built-in Flash).
        sleep():
            Put module into sleep mode (not recommended for SD card).
        reset():
            Soft reset module (low reliability, power cycling recommended).
        get_status():
            Get current playback status (Stopped/Playing/Paused).
        get_volume():
            Get current volume value.
        get_equalizer():
            Get current EQ mode.
        get_looping():
            Get current loop mode.
        get_file_count(source):
            Get total number of files on specified source.
        get_folder_count(source):
            Get number of folders on specified source (SD card only).
        get_file_index(source):
            Get FAT index of current playing file.
        get_position():
            Get current playback progress (seconds).
        get_length():
            Get total duration of current file (seconds).
        get_name():
            Get filename of current playing file (SD card only).
        get_version():
            Get module firmware version number.
        read_buffer():
            Read all data from UART buffer.
        read_bytes():
            Read 4 bytes and convert to hex integer.
        write_bytes(b):
            Send command bytes to module (auto-wrap communication protocol).
    """

    # 音效模式常量
    # 普通模式
    EQ_NORMAL = 0
    # 流行模式
    EQ_POP = 1
    # 摇滚模式
    EQ_ROCK = 2
    # 爵士模式
    EQ_JAZZ = 3
    # 古典模式
    EQ_CLASSIC = 4
    # 重低音模式
    EQ_BASS = 5

    # 音源选择常量
    # SD卡（仅JQ6500-28P型号支持）
    SRC_SDCARD = 1
    # 内置Flash
    SRC_BUILTIN = 4

    # 循环模式常量
    # 全部循环:播放所有曲目并重复
    LOOP_ALL = 0
    # 文件夹循环:播放当前文件夹所有曲目并重复
    LOOP_FOLDER = 1
    # 单曲循环:播放当前曲目并重复
    LOOP_ONE = 2
    # 未知模式:RAM循环（未明确定义）
    LOOP_RAM = 3
    # 单曲播放停止:播放完当前曲目后停止
    LOOP_ONE_STOP = 4
    # 无循环:同LOOP_ONE_STOP
    LOOP_NONE = 4

    # 播放状态常量
    # 停止状态
    STATUS_STOPPED = 0
    # 播放状态
    STATUS_PLAYING = 1
    # 暂停状态
    STATUS_PAUSED = 2

    # 串口读取延迟:确保模块有足够时间返回数据
    READ_DELAY = 0.1

    def __init__(self, port=2, volume=20):
        """
        初始化 JQ6500 播放器实例。

        Args:
            port (int, 可选): UART 端口号，默认值为 2。
            volume (int, 可选): 初始音量值（范围 0-30），默认值为 20。

        ---
        Initialize JQ6500 player instance.

        Args:
            port (int, optional): UART port number, default is 2.
            volume (int, optional): Initial volume level (range 0-30), default is 20.
        """
        # 初始化UART，波特率固定为9600
        self.uart = UART(port, 9600)
        # 清空串口缓冲区
        self.uart.read()
        # 复位模块
        self.reset()
        # 设置初始音量
        self.set_volume(volume)

    def clean_up(self):
        """
        清理资源并释放 UART 端口，避免资源泄漏。

        ---
        Clean up resources and release UART port to avoid resource leakage.
        """
        # 复位模块到初始状态
        self.reset()
        # 判断uart对象是否有deinit方法
        if "deinit" in dir(self.uart):
            # 释放UART硬件资源
            self.uart.deinit()

    def play(self):
        """
        播放当前选中的音频文件。

        ---
        Play the currently selected audio file.
        """
        # 发送播放指令（0x0D）
        self.write_bytes([0x0D])

    def play_pause(self):
        """
        切换播放/暂停状态:暂停/停止时播放，播放时暂停。

        ---
        Toggle play/pause status: play when paused/stopped, pause when playing.
        """
        # 获取当前播放状态
        status = self.get_status()
        # 暂停或停止状态则播放
        if status == self.STATUS_PAUSED or status == self.STATUS_STOPPED:
            self.play()
        # 播放状态则暂停
        elif status == self.STATUS_PLAYING:
            self.pause()

    def restart(self):
        """
        重新播放当前文件（从头开始），通过静音切换上下曲实现。

        ---
        Restart current file from the beginning (implemented by mute and track switch).
        """
        # 保存当前音量
        old_volume = self.get_volume()
        # 静音
        self.set_volume(0)
        # 切换到下一曲
        self.next()
        # 暂停播放
        self.pause()
        # 恢复原始音量
        self.set_volume(old_volume)
        # 切回上一曲（回到原文件开头）
        self.prev()

    def pause(self):
        """
        暂停当前播放的音频文件，调用 play() 可恢复播放。

        ---
        Pause the currently playing audio file, call play() to resume playback.
        """
        # 发送暂停指令（0x0E）
        self.write_bytes([0x0E])

    def next(self):
        """
        切换到下一个音频文件并播放。

        ---
        Switch to and play the next audio file.
        """
        # 发送下一曲指令（0x01）
        self.write_bytes([0x01])

    def prev(self):
        """
        切换到上一个音频文件并播放。

        ---
        Switch to and play the previous audio file.
        """
        # 发送上一曲指令（0x02）
        self.write_bytes([0x02])

    def next_folder(self):
        """
        切换到下一个文件夹并播放其中的音频文件（仅SD卡有效）。

        ---
        Switch to next folder and play audio files (SD card only).
        """
        # 发送切换下一个文件夹指令（0x0F, 0x01）
        self.write_bytes([0x0F, 0x01])

    def prev_folder(self):
        """
        切换到上一个文件夹并播放其中的音频文件（仅SD卡有效）。

        ---
        Switch to previous folder and play audio files (SD card only).
        """
        # 发送切换上一个文件夹指令（0x0F, 0x00）
        self.write_bytes([0x0F, 0x00])

    def play_by_index(self, file_index):
        """
        通过 FAT 表索引播放指定文件。

        Args:
            file_index (int): 文件在FAT表中的索引编号。

        Notes:
            索引编号与文件名无关，如需排序可使用FAT表排序工具。

        ---
        Play file by FAT table index.

        Args:
            file_index (int): File FAT table index number.

        Notes:
            The index number has nothing to do with the filename.
            To sort SD Card FAT table, search for a FAT sorting utility.
        """
        # 拆分文件索引为高低字节并发送播放指令（0x03 + 高字节 + 低字节）
        self.write_bytes([0x03, (file_index >> 8) & 0xFF, file_index & 0xFF])

    def play_by_number(self, folder_number, file_number):
        """
        通过文件夹编号和文件编号播放指定文件（仅SD卡有效）。

        Args:
            folder_number (int): 文件夹名称编号（00-99）。
            file_number (int): 文件名称编号（000-999）。

        Notes:
            仅适用于SD卡；文件夹需命名为00-99，文件需命名为000.mp3-999.mp3。

        ---
        Play file by folder number and file number (SD card only).

        Args:
            folder_number (int): Folder name number (00-99).
            file_number (int): Filename number (000-999).

        Notes:
            Only applies to SD Card.
            Folders must be named from 00 to 99, and files must be named from 000.mp3 to 999.mp3.
        """
        # 发送按编号播放指令（0x12 + 文件夹编号 + 文件编号）
        self.write_bytes([0x12, folder_number & 0xFF, file_number & 0xFF])

    def volume_up(self):
        """
        音量加1（音量范围 0-30）。

        ---
        Increase volume by 1 (Volume range 0-30).
        """
        # 发送音量加1指令（0x04）
        self.write_bytes([0x04])

    def volume_down(self):
        """
        音量减1（音量范围 0-30）。

        ---
        Decrease volume by 1 (Volume range 0-30).
        """
        # 发送音量减1指令（0x05）
        self.write_bytes([0x05])

    def set_volume(self, level):
        """
        设置指定音量值。

        Args:
            level (int): 音量值（范围 0-30）。

        Raises:
            AssertionError: 当音量值超出0-30范围时触发。

        ---
        Set volume to a specific level.

        Args:
            level (int): Volume level (Volume range 0-30).

        Raises:
            AssertionError: Triggered when volume level is out of 0-30 range.
        """
        # 断言检查音量值范围
        assert 0 <= level <= 30
        # 发送设置音量指令（0x06 + 音量值）
        self.write_bytes([0x06, level])

    def set_equalizer(self, mode):
        """
        设置音效模式（6种预设模式可选）。

        Args:
            mode (int): 音效模式（EQ_NORMAL/EQ_POP/EQ_ROCK/EQ_JAZZ/EQ_CLASSIC/EQ_BASS）。

        ---
        Set equalizer to 1 of 6 preset modes.

        Args:
            mode (int): EQ mode (EQ_NORMAL, EQ_POP, EQ_ROCK, EQ_JAZZ, EQ_CLASSIC, EQ_BASS).
        """
        # 发送设置音效模式指令（0x07 + 模式值）
        self.write_bytes([0x07, mode])

    def set_looping(self, mode):
        """
        设置循环播放模式。

        Args:
            mode (int): 循环模式（LOOP_ALL/LOOP_FOLDER/LOOP_ONE/LOOP_RAM/LOOP_ONE_STOP/LOOP_NONE）。

        ---
        Set looping mode.

        Args:
            mode (int): Loop mode (LOOP_ALL, LOOP_FOLDER, LOOP_ONE, LOOP_RAM, LOOP_ONE_STOP, LOOP_NONE).
        """
        # 发送设置循环模式指令（0x11 + 模式值）
        self.write_bytes([0x11, mode])

    def set_source(self, source):
        """
        设置MP3文件的音源位置（SD卡/内置Flash）。

        Args:
            source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）。

        Notes:
            SD卡需要JQ6500-28P型号支持。

        ---
        Set source location of MP3 files (on-board flash or SD card).

        Args:
            source (int): Audio source (SRC_SDCARD, SRC_BUILTIN).

        Notes:
            SD card requires JQ6500-28P model.
        """
        # 发送设置音源指令（0x09 + 音源类型）
        self.write_bytes([0x09, source])

    def sleep(self):
        """
        使模块进入睡眠模式，降低功耗。

        Notes:
            不建议在SD卡使用时调用此方法。

        ---
        Put the device to sleep to reduce power consumption.

        Notes:
            Not recommended for use with SD cards.
        """
        # 发送睡眠模式指令（0x0A）
        self.write_bytes([0x0A])

    def reset(self):
        """
        软复位模块，恢复到初始状态。

        Notes:
            该方法可靠性较低（尤其是SD卡使用时），建议优先使用断电重启。

        ---
        Soft reset of the device to restore initial state.

        Notes:
            Method is not reliable (especially with SD cards). Power-cycling is preferable.
        """
        # 发送复位指令（0x0C）
        self.write_bytes([0x0C])
        # 复位后等待模块稳定（500毫秒）
        sleep(0.5)

    def get_status(self):
        """
        获取模块当前播放状态。

        Returns:
            int: 播放状态（STATUS_STOPPED/STATUS_PLAYING/STATUS_PAUSED），获取失败返回-1。

        Notes:
            内置Flash仅返回播放/暂停状态；SD卡使用时该方法可靠性较低。

        ---
        Get device playback status.

        Returns:
            int: Playback status (STATUS_STOPPED/STATUS_PLAYING/STATUS_PAUSED), returns -1 on failure.

        Notes:
            Only returns playing or paused with built-in flash. Method is unreliable with SD cards.
        """
        # 发送获取状态指令（0x42）
        self.write_bytes([0x42])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取串口返回数据
        status = self.uart.read()
        # 再次短暂延迟确保数据完整
        sleep(self.READ_DELAY)
        # 检查返回数据是否为数字
        if status and status.isdigit():
            # 转换为整数返回
            return int(status)
        else:
            # 获取失败返回-1
            return -1

    def get_volume(self):
        """
        获取当前音量值（0-30）。

        Returns:
            int: 当前音量值，获取失败返回-1。

        ---
        Get current volume level (0-30).

        Returns:
            int: Current volume level, returns -1 on failure.
        """
        # 发送获取音量指令（0x43）
        self.write_bytes([0x43])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换返回数据
        level = self.read_bytes()
        # 返回音量值
        return level

    def get_equalizer(self):
        """
        获取当前音效模式。

        Returns:
            int: 音效模式（EQ_NORMAL/EQ_POP/EQ_ROCK/EQ_JAZZ/EQ_CLASSIC/EQ_BASS），获取失败返回-1。

        ---
        Get current equalizer mode.

        Returns:
            int: EQ mode (EQ_NORMAL, EQ_POP, EQ_ROCK, EQ_JAZZ, EQ_CLASSIC, EQ_BASS), returns -1 on failure.
        """
        # 发送获取音效模式指令（0x44）
        self.write_bytes([0x44])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换返回数据
        eq = self.read_bytes()
        # 返回音效模式值
        return eq

    def get_looping(self):
        """
        获取当前循环模式。

        Returns:
            int: 循环模式（LOOP_ALL/LOOP_FOLDER/LOOP_ONE/LOOP_RAM/LOOP_ONE_STOP/LOOP_NONE），获取失败返回-1。

        ---
        Get current looping mode.

        Returns:
            int: Loop mode (LOOP_ALL, LOOP_FOLDER, LOOP_ONE, LOOP_RAM, LOOP_ONE_STOP, LOOP_NONE), returns -1 on failure.
        """
        # 发送获取循环模式指令（0x45）
        self.write_bytes([0x45])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换返回数据
        looping = self.read_bytes()
        # 返回循环模式值
        return looping

    def get_file_count(self, source):
        """
        获取指定音源的文件总数。

        Args:
            source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）。

        Returns:
            int: 文件总数，获取失败返回-1。

        ---
        Return the number of files on the specified media.

        Args:
            source (int): Audio source (SRC_SDCARD, SRC_BUILTIN).

        Returns:
            int: Total number of files, returns -1 on failure.
        """
        # 判断音源类型
        if source == self.SRC_SDCARD:
            # 发送获取SD卡文件数指令（0x47）
            self.write_bytes([0x47])
        else:
            # SRC_BUILTIN 内置Flash
            # 发送获取内置Flash文件数指令（0x49）
            self.write_bytes([0x49])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换返回数据
        count = self.read_bytes()
        # 返回文件总数
        return count

    def get_folder_count(self, source):
        """
        获取指定音源的文件夹数量（仅SD卡有效）。

        Args:
            source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）。

        Returns:
            int: SD卡返回文件夹数量，内置Flash返回0，获取失败返回-1。

        Notes:
            只有SD卡支持文件夹结构。

        ---
        Return the number of folders on the specified media (SD card only).

        Args:
            source (int): Audio source (SRC_SDCARD, SRC_BUILTIN).

        Returns:
            int: Number of folders for SD card, 0 for built-in flash, -1 on failure.

        Notes:
            Only SD cards can have folders.
        """
        # 判断音源类型为SD卡
        if source == self.SRC_SDCARD:
            # 发送获取文件夹数量指令（0x53）
            self.write_bytes([0x53])
            # 等待模块返回数据
            sleep(self.READ_DELAY)
            # 读取并转换返回数据
            count = self.read_bytes()
            # 返回文件夹数量
            return count
        else:
            # 内置Flash返回0
            return 0

    def get_file_index(self, source):
        """
        获取当前播放文件的FAT表索引。

        Args:
            source (int): 音源类型（SRC_SDCARD/SRC_BUILTIN）。

        Returns:
            int: FAT表索引值，获取失败返回-1。

        Notes:
            索引对应当前播放/暂停的文件；停止状态下对应下一个要播放的文件。

        ---
        Get FAT file index of current file.

        Args:
            source (int): Audio source (SRC_SDCARD, SRC_BUILTIN).

        Returns:
            int: FAT table index value, returns -1 on failure.

        Notes:
            Refers to current playing or paused file. If stopped, refers to the next file to play.
        """
        # 判断音源类型
        if source == self.SRC_SDCARD:
            # 发送获取SD卡当前文件索引指令（0x4B）
            self.write_bytes([0x4B])
            # 等待模块返回数据
            sleep(self.READ_DELAY)
            # 读取并转换返回数据
            count = self.read_bytes()
            # 返回索引值
            return count
        else:
            # SRC_BUILTIN 内置Flash
            # 发送获取内置Flash当前文件索引指令（0x4D）
            self.write_bytes([0x4D])
            # 等待模块返回数据
            sleep(self.READ_DELAY)
            # 读取并转换返回数据
            count = self.read_bytes()
            # 返回索引值（+1修正）
            return count + 1

    def get_position(self):
        """
        获取当前文件的播放进度（秒）。

        Returns:
            int: 播放进度（秒），获取失败返回-1。

        ---
        Get current playback position in seconds of current file.

        Returns:
            int: Playback position in seconds, returns -1 on failure.
        """
        # 发送获取播放进度指令（0x50）
        self.write_bytes([0x50])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换返回数据
        position = self.read_bytes()
        # 返回播放进度
        return position

    def get_length(self):
        """
        获取当前文件的总时长（秒）。

        Returns:
            int: 文件总时长（秒），获取失败返回-1。

        ---
        Get total length in seconds of current file.

        Returns:
            int: File duration in seconds, returns -1 on failure.
        """
        # 发送获取文件总时长指令（0x51）
        self.write_bytes([0x51])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换返回数据
        length = self.read_bytes()
        # 返回文件总时长
        return length

    def get_name(self):
        """
        获取当前播放文件的文件名（仅SD卡有效）。

        Returns:
            bytes: 文件名字节数据，获取失败返回None。

        Notes:
            必须将SD卡设置为当前音源才能获取。

        ---
        Get the filename of the current file on the SD card.

        Returns:
            bytes: Filename byte data, returns None on failure.

        Notes:
            SD card must be active source.
        """
        # 发送获取文件名指令（0x52）
        self.write_bytes([0x52])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并返回文件名字节数据
        return self.uart.read()

    def get_version(self):
        """
        获取模块固件版本号。

        Returns:
            int: 版本号，获取失败返回-1。

        ---
        Get module firmware version number.

        Returns:
            int: Version number, returns -1 on failure.
        """
        # 发送获取版本号指令（0x46）
        self.write_bytes([0x46])
        # 等待模块返回数据
        sleep(self.READ_DELAY)
        # 读取并转换返回数据
        version = self.read_bytes()
        # 返回版本号
        return version

    def read_buffer(self):
        """
        读取UART缓冲区所有数据并返回。

        Returns:
            bytes: 缓冲区字节数据，无数据返回None。

        ---
        Return all data in UART buffer as bytes.

        Returns:
            bytes: Buffer byte data, returns None if empty.
        """
        # 读取UART缓冲区所有数据
        return self.uart.read()

    def read_bytes(self):
        """
        从UART端口读取4字节数据并转换为十六进制整数。

        Returns:
            int: 转换后的整数值，无数据返回-1。

        ---
        Read 4 bytes from UART port and convert to hex integer.

        Returns:
            int: Converted integer value, returns -1 if no data.
        """
        # 从串口读取4字节数据
        b = self.uart.read(4)
        # 打印原始字节数据（调试用）
        print(b)
        # 检查数据是否有效
        if b and len(b) > 0:
            # 转换为十六进制整数
            return int(b, 16)
        else:
            # 无数据返回-1
            return -1

    def write_bytes(self, b):
        """
        向模块发送指令字节（自动封装JQ6500通信协议）。

        Args:
            b (list): 要发送的指令字节列表。

        Protocol Format:
            7E [长度] [指令字节1] [指令字节2] ... EF
            - 7E: 帧头
            - 长度: 指令字节数 + 1
            - 指令字节: 具体操作指令
            - EF: 帧尾

        ---
        Write command bytes to the UART port (auto-wrap JQ6500 communication protocol).

        Args:
            b ([byte]): List of command bytes to write to the UART port.

        Protocol Format:
            7E [Length] [Cmd Byte1] [Cmd Byte2] ... EF
            - 7E: Frame header
            - Length: Number of command bytes + 1
            - Cmd Bytes: Specific operation commands
            - EF: Frame tail
        """
        # 计算消息长度（指令字节数 + 1）
        message_length = len(b) + 1
        # 封装通信协议帧（帧头 + 长度 + 指令字节 + 帧尾）
        data = [0x7E, message_length] + b + [0xEF]
        # 清空接收缓冲区
        self.uart.read()
        # 发送指令帧（转换为字节串）
        self.uart.write(bytes(data))
