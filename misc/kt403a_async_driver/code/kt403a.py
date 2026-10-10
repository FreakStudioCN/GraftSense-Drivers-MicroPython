# KT403A的MP3模块 MicroPython驱动
# -*- coding: utf-8 -*-
# @Time    : 2026/3/2
# @Author  : hogeiha
# @File    : kt403a.py
# @Description : KT403A MP3模块的MicroPython驱动，提供全面的音频控制功能，适用于基于MicroPython的项目开发。
# @License : MIT
# @Platform : MicroPython v1.23.0

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython的毫秒级延迟模块
from utime import sleep_ms

# 导入MicroPython的字节解包模块
from ustruct import unpack

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class KT403A:
    """
    KT403A 音频解码模块驱动类，基于UART串行通信接口实现对音频播放模块的全功能控制。
    提供音源切换、音量调节、EQ音效设置、曲目播放控制、循环模式配置等核心功能，
    同时支持设备状态查询、文件数量统计等辅助功能，适配MicroPython开发环境。

    Attributes:
        DEVICE_U_DISK (int): 音源设备常量 - U盘（值为1）
        DEVICE_SD (int): 音源设备常量 - SD卡（值为2）
        DEVICE_AUX (int): 音源设备常量 - AUX音频输入（值为3）
        DEVICE_SLEEP (int): 音源设备常量 - 睡眠模式（值为4）
        DEVICE_FLASH (int): 音源设备常量 - 内置Flash（值为5）
        EQ_NORMAL (int): EQ音效常量 - 普通模式（值为0）
        EQ_POP (int): EQ音效常量 - 流行模式（值为1）
        EQ_ROCK (int): EQ音效常量 - 摇滚模式（值为2）
        EQ_JAZZ (int): EQ音效常量 - 爵士模式（值为3）
        EQ_CLASSIC (int): EQ音效常量 - 古典模式（值为4）
        EQ_BASS (int): EQ音效常量 - 重低音模式（值为5）
        _uart (UART): MicroPython UART通信实例，用于与KT403A模块交互
        _device (int): 当前选中的音源设备类型标识

    Methods:
        __init__(uartBus, txPinNum, rxPinNum, device=None, volume=70, eq=None):
            初始化KT403A模块实例，配置UART总线参数，设置初始音源、音量和EQ模式
        _txCmd(cmd, dataL=0, dataH=0):
            私有方法 - 封装并发送指令帧到KT403A模块
        _rxCmd():
            私有方法 - 读取并解析KT403A模块返回的响应指令
        _readLastCmd():
            私有方法 - 循环读取直到获取最后一条有效响应指令
        PlayNext():
            控制模块播放下一曲目
        PlayPrevious():
            控制模块播放上一曲目
        PlaySpecific(trackIndex):
            播放指定索引的单个曲目
        VolumeUp():
            增加模块音量
        VolumeDown():
            减小模块音量
        SetVolume(percent):
            设置模块音量（0-100百分比）
        SetEqualizer(eq):
            设置EQ音效模式
        RepeatCurrent():
            开启当前曲目单曲循环模式
        SetDevice(device):
            切换音源设备类型
        SetLowPowerOn():
            开启模块低功耗模式
        SetLowPowerOff():
            关闭低功耗模式，恢复原音源设备
        ResetChip():
            软复位KT403A芯片
        Play():
            播放当前选中的曲目
        Pause():
            暂停当前正在播放的曲目
        PlaySpecificInFolder(folderIndex, trackIndex):
            播放指定文件夹中的指定曲目
        EnableLoopAll():
            开启全部曲目循环播放模式
        DisableLoopAll():
            关闭全部曲目循环播放模式
        PlayFolder(folderIndex):
            播放指定文件夹内的曲目
        Stop():
            停止当前音频播放
        LoopFolder(folderIndex):
            循环播放指定文件夹内的所有曲目
        RandomAll():
            开启所有曲目随机播放模式
        EnableLoop():
            开启通用循环播放模式
        DisableLoop():
            关闭通用循环播放模式
        EnableDAC():
            启用DAC音频输出功能
        DisableDAC():
            禁用DAC音频输出功能
        GetState():
            获取模块当前工作状态
        GetVolume():
            获取当前音量值（百分比）
        GetEqualizer():
            获取当前EQ音效模式
        GetFilesCount(device=None):
            获取指定音源设备中的文件总数
        GetFolderFilesCount(folderIndex):
            获取指定文件夹内的文件数量
        IsStopped():
            判断模块是否处于停止状态
        IsPlaying():
            判断模块是否处于播放状态
        IsPaused():
            判断模块是否处于暂停状态

    ==========================================

    KT403A audio decoding module driver class, implementing full-featured control of the audio playback module
    through the UART serial communication interface.
    Provides core functions such as audio source switching, volume adjustment, EQ effect setting, track playback
    control, loop mode configuration, and supports auxiliary functions like device status query and file count
    statistics, adapted to the MicroPython development environment.

    Attributes:
        DEVICE_U_DISK (int): Audio source device constant - U disk (value 1)
        DEVICE_SD (int): Audio source device constant - SD card (value 2)
        DEVICE_AUX (int): Audio source device constant - AUX audio input (value 3)
        DEVICE_SLEEP (int): Audio source device constant - Sleep mode (value 4)
        DEVICE_FLASH (int): Audio source device constant - Built-in Flash (value 5)
        EQ_NORMAL (int): EQ effect constant - Normal mode (value 0)
        EQ_POP (int): EQ effect constant - Pop mode (value 1)
        EQ_ROCK (int): EQ effect constant - Rock mode (value 2)
        EQ_JAZZ (int): EQ effect constant - Jazz mode (value 3)
        EQ_CLASSIC (int): EQ effect constant - Classic mode (value 4)
        EQ_BASS (int): EQ effect constant - Bass mode (value 5)
        _uart (UART): MicroPython UART communication instance for interacting with KT403A module
        _device (int): Identifier of currently selected audio source device type

    Methods:
        __init__(uartBus, txPinNum, rxPinNum, device=None, volume=70, eq=None):
            Initialize KT403A module instance, configure UART bus parameters, set initial audio source, volume and EQ mode
        _txCmd(cmd, dataL=0, dataH=0):
            Private method - Package and send command frame to KT403A module
        _rxCmd():
            Private method - Read and parse response command returned by KT403A module
        _readLastCmd():
            Private method - Loop to read until getting the last valid response command
        PlayNext():
            Control module to play next track
        PlayPrevious():
            Control module to play previous track
        PlaySpecific(trackIndex):
            Play a single track with specified index
        VolumeUp():
            Increase module volume
        VolumeDown():
            Decrease module volume
        SetVolume(percent):
            Set module volume (0-100 percentage)
        SetEqualizer(eq):
            Set EQ effect mode
        RepeatCurrent():
            Enable single track loop mode for current track
        SetDevice(device):
            Switch audio source device type
        SetLowPowerOn():
            Enable module low power mode
        SetLowPowerOff():
            Disable low power mode and restore original audio source device
        ResetChip():
            Soft reset KT403A chip
        Play():
            Play currently selected track
        Pause():
            Pause currently playing track
        PlaySpecificInFolder(folderIndex, trackIndex):
            Play specified track in specified folder
        EnableLoopAll():
            Enable all tracks loop playback mode
        DisableLoopAll():
            Disable all tracks loop playback mode
        PlayFolder(folderIndex):
            Play tracks in specified folder
        Stop():
            Stop current audio playback
        LoopFolder(folderIndex):
            Loop play all tracks in specified folder
        RandomAll():
            Enable random playback mode for all tracks
        EnableLoop():
            Enable general loop playback mode
        DisableLoop():
            Disable general loop playback mode
        EnableDAC():
            Enable DAC audio output function
        DisableDAC():
            Disable DAC audio output function
        GetState():
            Get current working state of the module
        GetVolume():
            Get current volume value (percentage)
        GetEqualizer():
            Get current EQ effect mode
        GetFilesCount(device=None):
            Get total number of files in specified audio source device
        GetFolderFilesCount(folderIndex):
            Get number of files in specified folder
        IsStopped():
            Determine if the module is in stopped state
        IsPlaying():
            Determine if the module is in playing state
        IsPaused():
            Determine if the module is in paused state
    """

    # 音源设备常量 - U盘
    DEVICE_U_DISK = 1
    # 音源设备常量 - SD卡
    DEVICE_SD = 2
    # 音源设备常量 - AUX音频输入
    DEVICE_AUX = 3
    # 音源设备常量 - 睡眠模式
    DEVICE_SLEEP = 4
    # 音源设备常量 - 内置Flash
    DEVICE_FLASH = 5

    # EQ音效常量 - 普通模式
    EQ_NORMAL = 0
    # EQ音效常量 - 流行模式
    EQ_POP = 1
    # EQ音效常量 - 摇滚模式
    EQ_ROCK = 2
    # EQ音效常量 - 爵士模式
    EQ_JAZZ = 3
    # EQ音效常量 - 古典模式
    EQ_CLASSIC = 4
    # EQ音效常量 - 重低音模式
    EQ_BASS = 5

    def __init__(self, uart, device=None, volume=70, eq=None):
        """
        初始化KT403A音频模块实例，配置UART通信参数并设置初始工作状态。

        Args:
            uartBus (int): UART总线编号
            txPinNum (int): TX发送引脚编号
            rxPinNum (int): RX接收引脚编号
            device (int, 可选): 初始音源设备类型，默认使用SD卡
            volume (int, 可选): 初始音量百分比（0-100），默认值70
            eq (int, 可选): 初始EQ音效模式，默认使用普通模式

        Raises:
            Exception: 模块初始化失败时抛出异常

        Notes:
            引脚编号会自动转换为"P+数字"格式的引脚ID；初始化时会验证模块通信状态

        ---
        Initialize KT403A audio module instance, configure UART communication parameters and set initial working state.

        Args:
            uartBus (int): UART bus number
            txPinNum (int): TX transmit pin number
            rxPinNum (int): RX receive pin number
            device (int, optional): Initial audio source device type, SD card is used by default
            volume (int, optional): Initial volume percentage (0-100), default value 70
            eq (int, optional): Initial EQ effect mode, normal mode is used by default

        Raises:
            Exception: Thrown when module initialization fails

        Notes:
            Pin numbers are automatically converted to pin IDs in "P+number" format; module communication status is verified during initialization
        """
        # 初始化UART通信实例，配置9600波特率、8位数据位、无校验、1位停止位
        self._uart = uart
        # 设置初始音源设备（未指定时默认使用SD卡）
        self.SetDevice(device if device else KT403A.DEVICE_SD)
        # 检查模块初始化状态，获取不到状态则抛出异常
        if not self.GetState():
            raise Exception("KT403A could not be initialized.")
        # 设置初始音量值
        self.SetVolume(volume)
        # 设置初始EQ音效模式（未指定时默认使用普通模式）
        self.SetEqualizer(eq if eq else KT403A.EQ_NORMAL)

    def _txCmd(self, cmd, dataL=0, dataH=0):
        """
        私有方法:封装并发送符合KT403A通信协议的指令帧。

        Args:
            cmd (int): 指令字（操作码）
            dataL (int, 可选): 数据低字节，默认值0
            dataH (int, 可选): 数据高字节，默认值0

        Notes:
            指令帧格式:7E FF 06 [cmd] 00 [dataH] [dataL] EF；
            根据指令类型设置不同的延迟时间，确保模块处理完成

        ---
        Private method: Package and send command frame complying with KT403A communication protocol.

        Args:
            cmd (int): Command word (operation code)
            dataL (int, optional): Data low byte, default value 0
            dataH (int, optional): Data high byte, default value 0

        Notes:
            Command frame format: 7E FF 06 [cmd] 00 [dataH] [dataL] EF;
            Different delay times are set according to command types to ensure module processing completion
        """
        # 发送指令帧起始字节（0x7E）
        self._uart.write(b"\x7E")
        # 发送固件版本字节（0xFF）
        self._uart.write(b"\xFF")
        # 发送指令长度字节（0x06）
        self._uart.write(b"\x06")
        # 发送指令字字节
        self._uart.write(bytes([cmd]))
        # 发送反馈标志字节（0x00）
        self._uart.write(b"\x00")
        # 发送数据高字节
        self._uart.write(bytes([dataH]))
        # 发送数据低字节
        self._uart.write(bytes([dataL]))
        # 发送指令帧结束字节（0xEF）
        self._uart.write(b"\xEF")
        # 根据指令类型设置延迟:0x09(切换设备)200ms，0x0C(复位)1000ms，其他30ms
        sleep_ms(200 if cmd == 0x09 else 1000 if cmd == 0x0C else 30)

    def _rxCmd(self):
        """
        私有方法:读取并解析KT403A模块返回的响应指令帧。

        Returns:
            tuple/None: 有效响应返回(cmd, data)元组，无效响应返回None
                        - cmd: 响应指令字（int）
                        - data: 响应数据（16位整数）

        Notes:
            仅解析符合协议格式的10字节响应帧；使用大端序解包数据字段

        ---
        Private method: Read and parse response command frame returned by KT403A module.

        Returns:
            tuple/None: Returns (cmd, data) tuple for valid response, None for invalid response
                        - cmd: Response command word (int)
                        - data: Response data (16-bit integer)

        Notes:
            Only parse 10-byte response frames complying with protocol format; unpack data field in big-endian order
        """
        # 检查UART接收缓冲区是否有可用数据
        if self._uart.any():
            # 读取10字节响应数据
            buf = self._uart.read(10)
            # 验证响应帧格式有效性:非空、长度10、帧头帧尾正确、版本和长度字段匹配
            if buf is not None and len(buf) == 10 and buf[0] == 0x7E and buf[1] == 0xFF and buf[2] == 0x06 and buf[9] == 0xEF:
                # 提取响应指令字
                cmd = buf[3]
                # 大端序解包5-7字节为16位整数数据
                data = unpack(">H", buf[5:7])[0]
                # 返回指令字和数据元组
                return (cmd, data)
        # 无有效响应返回None
        return None

    def _readLastCmd(self):
        """
        私有方法:循环读取UART响应，获取最后一条有效响应指令。

        Returns:
            tuple/None: 最后一条有效响应的(cmd, data)元组，无有效响应返回None

        Notes:
            用于处理模块可能返回的多条响应，确保获取最新状态

        ---
        Private method: Loop to read UART responses and get the last valid response command.

        Returns:
            tuple/None: (cmd, data) tuple of the last valid response, None if no valid response

        Notes:
            Used to handle multiple responses that the module may return, ensuring the latest status is obtained
        """
        # 初始化响应结果为None
        res = None
        # 循环读取响应
        while True:
            # 读取单次响应
            r = self._rxCmd()
            # 无响应则返回最后一次有效结果
            if not r:
                return res
            # 更新最后一次有效响应
            res = r

    def PlayNext(self):
        """
        控制KT403A模块播放下一曲目。

        Notes:
            仅在当前音源有多个曲目时有效

        ---
        Control KT403A module to play next track.

        Notes:
            Only effective when there are multiple tracks in the current audio source
        """
        # 发送播放下一曲指令（指令字0x01）
        self._txCmd(0x01)

    def PlayPrevious(self):
        """
        控制KT403A模块播放上一曲目。

        Notes:
            仅在当前音源有多个曲目时有效

        ---
        Control KT403A module to play previous track.

        Notes:
            Only effective when there are multiple tracks in the current audio source
        """
        # 发送播放上一曲指令（指令字0x02）
        self._txCmd(0x02)

    def PlaySpecific(self, trackIndex):
        """
        播放指定索引的单个曲目。

        Args:
            trackIndex (int): 曲目索引编号（从1开始）

        Notes:
            索引值会自动拆分为高低字节发送；索引超出范围时模块无响应

        ---
        Play a single track with specified index.

        Args:
            trackIndex (int): Track index number (starting from 1)

        Notes:
            The index value is automatically split into high and low bytes for transmission;
            the module has no response when the index is out of range
        """
        # 发送播放指定曲目指令（指令字0x03），拆分索引为高低字节
        self._txCmd(0x03, int(trackIndex % 256), int(trackIndex / 256))

    def VolumeUp(self):
        """
        增加KT403A模块的音量（单次增加1级）。

        Notes:
            音量范围0-30级（对应0-100%）；达到最大值后不再变化

        ---
        Increase the volume of KT403A module (increase 1 level at a time).

        Notes:
            Volume range is 0-30 levels (corresponding to 0-100%); no change after reaching maximum value
        """
        # 发送音量增加指令（指令字0x04）
        self._txCmd(0x04)

    def VolumeDown(self):
        """
        减小KT403A模块的音量（单次减小1级）。

        Notes:
            音量范围0-30级（对应0-100%）；达到最小值后不再变化

        ---
        Decrease the volume of KT403A module (decrease 1 level at a time).

        Notes:
            Volume range is 0-30 levels (corresponding to 0-100%); no change after reaching minimum value
        """
        # 发送音量减小指令（指令字0x05）
        self._txCmd(0x05)

    def SetVolume(self, percent):
        """
        设置KT403A模块的音量（百分比形式）。

        Args:
            percent (int): 音量百分比（0-100）

        Notes:
            百分比会自动转换为模块内部0-30级的音量值；超出范围会被限制在0或100

        ---
        Set the volume of KT403A module (in percentage form).

        Args:
            percent (int): Volume percentage (0-100)

        Notes:
            The percentage is automatically converted to the module's internal 0-30 level volume value;
            values outside the range are limited to 0 or 100
        """
        # 限制音量最小值为0
        if percent < 0:
            percent = 0
        # 限制音量最大值为100
        elif percent > 100:
            percent = 100
        # 转换百分比为模块音量级（0-30）并发送设置音量指令（指令字0x06）
        self._txCmd(0x06, int(percent * 0x1E / 100))

    def SetEqualizer(self, eq):
        """
        设置KT403A模块的EQ音效模式。

        Args:
            eq (int): EQ音效模式（0-5对应NORMAL/POP/ROCK/JAZZ/CLASSIC/BASS）

        Notes:
            超出0-5范围的EQ值会自动重置为普通模式（EQ_NORMAL）

        ---
        Set the EQ effect mode of KT403A module.

        Args:
            eq (int): EQ effect mode (0-5 corresponding to NORMAL/POP/ROCK/JAZZ/CLASSIC/BASS)

        Notes:
            EQ values outside the range of 0-5 are automatically reset to normal mode (EQ_NORMAL)
        """
        # 检查EQ值范围，超出则重置为普通模式
        if eq < 0 or eq > 5:
            eq = 0
        # 发送设置EQ音效指令（指令字0x07）
        self._txCmd(0x07, eq)

    def RepeatCurrent(self):
        """
        开启当前曲目的单曲循环播放模式。

        Notes:
            仅对当前播放的曲目生效；切换曲目后需要重新设置

        ---
        Enable single track loop playback mode for the current track.

        Notes:
            Only effective for the currently playing track; needs to be reset after switching tracks
        """
        # 发送单曲循环指令（指令字0x08）
        self._txCmd(0x08)

    def SetDevice(self, device):
        """
        切换KT403A模块的音源设备类型。

        Args:
            device (int): 音源设备类型（DEVICE_U_DISK/SD/AUX/SLEEP/FLASH）

        Notes:
            切换后会更新实例的_device属性；切换到睡眠模式会关闭音频输出

        ---
        Switch the audio source device type of KT403A module.

        Args:
            device (int): Audio source device type (DEVICE_U_DISK/SD/AUX/SLEEP/FLASH)

        Notes:
            The _device attribute of the instance is updated after switching;
            switching to sleep mode turns off audio output
        """
        # 保存当前选中的音源设备类型
        self._device = device
        # 发送切换音源设备指令（指令字0x09）
        self._txCmd(0x09, device)

    def SetLowPowerOn(self):
        """
        开启KT403A模块的低功耗模式。

        Notes:
            低功耗模式下模块会关闭部分功能以降低功耗；需调用SetLowPowerOff恢复

        ---
        Enable low power mode of KT403A module.

        Notes:
            The module turns off some functions to reduce power consumption in low power mode;
            call SetLowPowerOff to restore
        """
        # 发送开启低功耗模式指令（指令字0x0A）
        self._txCmd(0x0A)

    def SetLowPowerOff(self):
        """
        关闭KT403A模块的低功耗模式，恢复到切换前的音源设备。

        Notes:
            通过重新设置之前保存的_device属性恢复音源

        ---
        Disable low power mode of KT403A module and restore to the audio source device before switching.

        Notes:
            Restore the audio source by resetting the previously saved _device attribute
        """
        # 恢复到切换低功耗模式前的音源设备
        self.SetDevice(self._device)

    def ResetChip(self):
        """
        软复位KT403A芯片，恢复到初始工作状态。

        Notes:
            复位后音量、EQ、音源等设置会恢复默认值；复位需要1秒完成

        ---
        Soft reset KT403A chip to restore to initial working state.

        Notes:
            Settings such as volume, EQ, and audio source are restored to default values after reset;
            reset takes 1 second to complete
        """
        # 发送芯片复位指令（指令字0x0C）
        self._txCmd(0x0C)

    def Play(self):
        """
        播放当前选中的曲目（暂停/停止状态下恢复播放）。

        Notes:
            模块处于播放状态时调用无效果

        ---
        Play the currently selected track (resume playback in pause/stop state).

        Notes:
            No effect when the module is in playing state
        """
        # 发送播放指令（指令字0x0D）
        self._txCmd(0x0D)

    def Pause(self):
        """
        暂停当前正在播放的曲目。

        Notes:
            模块处于暂停/停止状态时调用无效果；调用Play()可恢复播放

        ---
        Pause the currently playing track.

        Notes:
            No effect when the module is in pause/stop state; call Play() to resume playback
        """
        # 发送暂停指令（指令字0x0E）
        self._txCmd(0x0E)

    def PlaySpecificInFolder(self, folderIndex, trackIndex):
        """
        播放指定文件夹中的指定曲目。

        Args:
            folderIndex (int): 文件夹索引编号（从1开始）
            trackIndex (int): 曲目索引编号（从1开始）

        Notes:
            仅对支持文件夹结构的音源（U盘/SD卡）有效；索引超出范围时模块无响应

        ---
        Play specified track in specified folder.

        Args:
            folderIndex (int): Folder index number (starting from 1)
            trackIndex (int): Track index number (starting from 1)

        Notes:
            Only effective for audio sources that support folder structure (U disk/SD card);
            the module has no response when the index is out of range
        """
        # 发送播放指定文件夹指定曲目指令（指令字0x0F）
        self._txCmd(0x0F, trackIndex, folderIndex)

    def EnableLoopAll(self):
        """
        开启全部曲目循环播放模式。

        Notes:
            对当前音源的所有曲目生效；与单曲循环互斥

        ---
        Enable all tracks loop playback mode.

        Notes:
            Effective for all tracks of the current audio source; mutually exclusive with single track loop
        """
        # 发送开启全部循环指令（指令字0x11，数据1）
        self._txCmd(0x11, 1)

    def DisableLoopAll(self):
        """
        关闭全部曲目循环播放模式。

        Notes:
            关闭后播放完所有曲目会停止

        ---
        Disable all tracks loop playback mode.

        Notes:
            Playback stops after playing all tracks after disabling
        """
        # 发送关闭全部循环指令（指令字0x11，数据0）
        self._txCmd(0x11, 0)

    def PlayFolder(self, folderIndex):
        """
        播放指定文件夹内的曲目。

        Args:
            folderIndex (int): 文件夹索引编号（从1开始）

        Notes:
            仅对支持文件夹结构的音源（U盘/SD卡）有效

        ---
        Play tracks in specified folder.

        Args:
            folderIndex (int): Folder index number (starting from 1)

        Notes:
            Only effective for audio sources that support folder structure (U disk/SD card)
        """
        # 发送播放指定文件夹指令（指令字0x12）
        self._txCmd(0x12, folderIndex)

    def Stop(self):
        """
        停止当前音频播放。

        Notes:
            模块处于停止状态时调用无效果；调用Play()可重新开始播放

        ---
        Stop current audio playback.

        Notes:
            No effect when the module is in stopped state; call Play() to start playback again
        """
        # 发送停止播放指令（指令字0x16）
        self._txCmd(0x16)

    def LoopFolder(self, folderIndex):
        """
        循环播放指定文件夹内的所有曲目。

        Args:
            folderIndex (int): 文件夹索引编号（从1开始）

        Notes:
            仅对支持文件夹结构的音源（U盘/SD卡）有效

        ---
        Loop play all tracks in specified folder.

        Args:
            folderIndex (int): Folder index number (starting from 1)

        Notes:
            Only effective for audio sources that support folder structure (U disk/SD card)
        """
        # 发送循环播放指定文件夹指令（指令字0x17）
        self._txCmd(0x17, folderIndex)

    def RandomAll(self):
        """
        开启所有曲目随机播放模式。

        Notes:
            对当前音源的所有曲目生效；播放顺序随机且不重复

        ---
        Enable random playback mode for all tracks.

        Notes:
            Effective for all tracks of the current audio source; playback order is random and non-repetitive
        """
        # 发送随机播放指令（指令字0x18）
        self._txCmd(0x18)

    def EnableLoop(self):
        """
        开启通用循环播放模式。

        Notes:
            与EnableLoopAll功能类似，具体行为取决于模块固件版本

        ---
        Enable general loop playback mode.

        Notes:
            Similar to EnableLoopAll function, specific behavior depends on module firmware version
        """
        # 发送开启循环模式指令（指令字0x19，数据0）
        self._txCmd(0x19, 0)

    def DisableLoop(self):
        """
        关闭通用循环播放模式。

        Notes:
            与DisableLoopAll功能类似，具体行为取决于模块固件版本

        ---
        Disable general loop playback mode.

        Notes:
            Similar to DisableLoopAll function, specific behavior depends on module firmware version
        """
        # 发送关闭循环模式指令（指令字0x19，数据1）
        self._txCmd(0x19, 1)

    def EnableDAC(self):
        """
        启用KT403A模块的DAC音频输出功能。

        Notes:
            默认状态下DAC输出为启用状态

        ---
        Enable DAC audio output function of KT403A module.

        Notes:
            DAC output is enabled by default
        """
        # 发送启用DAC指令（指令字0x1A，数据0）
        self._txCmd(0x1A, 0)

    def DisableDAC(self):
        """
        禁用KT403A模块的DAC音频输出功能。

        Notes:
            禁用后无音频输出；需调用EnableDAC恢复

        ---
        Disable DAC audio output function of KT403A module.

        Notes:
            No audio output after disabling; call EnableDAC to restore
        """
        # 发送禁用DAC指令（指令字0x1A，数据1）
        self._txCmd(0x1A, 1)

    def GetState(self):
        """
        获取KT403A模块的当前工作状态。

        Returns:
            int/None: 状态值（0x0200=停止，0x0201=播放，0x0202=暂停），获取失败返回None

        Notes:
            状态值为16位整数；通信异常时返回None

        ---
        Get current working state of KT403A module.

        Returns:
            int/None: State value (0x0200=stopped, 0x0201=playing, 0x0202=paused), returns None on failure

        Notes:
            The state value is a 16-bit integer; returns None when communication is abnormal
        """
        # 发送获取状态指令（指令字0x42）
        self._txCmd(0x42)
        # 读取最后一次响应
        r = self._readLastCmd()
        # 验证响应有效性并返回状态数据，无效返回None
        return r[1] if r and r[0] == 0x42 else None

    def GetVolume(self):
        """
        获取KT403A模块的当前音量值（百分比形式）。

        Returns:
            int: 音量百分比（0-100），获取失败返回0

        Notes:
            内部将模块返回的0-30级音量值转换为百分比

        ---
        Get current volume value of KT403A module (in percentage form).

        Returns:
            int: Volume percentage (0-100), returns 0 on failure

        Notes:
            Internally convert the 0-30 level volume value returned by the module to percentage
        """
        # 发送获取音量指令（指令字0x43）
        self._txCmd(0x43)
        # 读取最后一次响应
        r = self._readLastCmd()
        # 转换为百分比并返回，失败返回0
        return int(r[1] / 0x1E * 100) if r and r[0] == 0x43 else 0

    def GetEqualizer(self):
        """
        获取KT403A模块的当前EQ音效模式。

        Returns:
            int: EQ模式值（0-5），获取失败返回0

        Notes:
            返回值对应EQ_NORMAL/POP/ROCK/JAZZ/CLASSIC/BASS

        ---
        Get current EQ effect mode of KT403A module.

        Returns:
            int: EQ mode value (0-5), returns 0 on failure

        Notes:
            The return value corresponds to EQ_NORMAL/POP/ROCK/JAZZ/CLASSIC/BASS
        """
        # 发送获取EQ模式指令（指令字0x44）
        self._txCmd(0x44)
        # 读取最后一次响应
        r = self._readLastCmd()
        # 验证响应有效性并返回EQ模式值，失败返回0
        return r[1] if r and r[0] == 0x44 else 0

    def GetFilesCount(self, device=None):
        """
        获取指定音源设备中的文件总数。

        Args:
            device (int, 可选): 音源设备类型，默认使用当前选中的音源

        Returns:
            int: 文件总数，不支持的音源类型/获取失败返回0

        Notes:
            仅支持U盘(0x47)、SD卡(0x48)、内置Flash(0x49)三种音源；AUX/SLEEP返回0

        ---
        Get total number of files in specified audio source device.

        Args:
            device (int, optional): Audio source device type, uses currently selected source by default

        Returns:
            int: Total number of files, returns 0 for unsupported source types or on failure

        Notes:
            Only supports three audio sources: U disk(0x47), SD card(0x48), built-in Flash(0x49);
            AUX/SLEEP return 0
        """
        # 未指定设备时使用当前选中的音源
        if not device:
            device = self._device
        # 根据音源类型发送对应指令
        if device == KT403A.DEVICE_U_DISK:
            # 发送获取U盘文件数指令（指令字0x47）
            self._txCmd(0x47)
        elif device == KT403A.DEVICE_SD:
            # 发送获取SD卡文件数指令（指令字0x48）
            self._txCmd(0x48)
        elif device == KT403A.DEVICE_FLASH:
            # 发送获取Flash文件数指令（指令字0x49）
            self._txCmd(0x49)
        else:
            # 不支持的音源类型返回0
            return 0
        # 等待模块响应
        sleep_ms(200)
        # 读取最后一次响应
        r = self._readLastCmd()
        # 验证响应有效性并返回文件数，失败返回0
        return r[1] if r and r[0] >= 0x47 and r[0] <= 0x49 else 0

    def GetFolderFilesCount(self, folderIndex):
        """
        获取指定文件夹内的文件数量。

        Args:
            folderIndex (int): 文件夹索引编号（从1开始）

        Returns:
            int: 文件夹内文件数量，获取失败返回0

        Notes:
            仅对支持文件夹结构的音源（U盘/SD卡）有效

        ---
        Get number of files in specified folder.

        Args:
            folderIndex (int): Folder index number (starting from 1)

        Returns:
            int: Number of files in folder, returns 0 on failure

        Notes:
            Only effective for audio sources that support folder structure (U disk/SD card)
        """
        # 发送获取文件夹文件数指令（指令字0x4E）
        self._txCmd(0x4E, folderIndex)
        # 等待模块响应
        sleep_ms(200)
        # 读取最后一次响应
        r = self._readLastCmd()
        # 验证响应有效性并返回文件数，失败返回0
        return r[1] if r and r[0] == 0x4E else 0

    def IsStopped(self):
        """
        判断KT403A模块是否处于停止状态。

        Returns:
            bool: 停止状态返回True，否则返回False

        Notes:
            基于GetState()的返回值判断；通信异常时返回False

        ---
        Determine if KT403A module is in stopped state.

        Returns:
            bool: Returns True if stopped, False otherwise

        Notes:
            Judged based on the return value of GetState(); returns False when communication is abnormal
        """
        # 检查状态值是否为停止状态（0x0200）
        return self.GetState() == 0x0200

    def IsPlaying(self):
        """
        判断KT403A模块是否处于播放状态。

        Returns:
            bool: 播放状态返回True，否则返回False

        Notes:
            基于GetState()的返回值判断；通信异常时返回False

        ---
        Determine if KT403A module is in playing state.

        Returns:
            bool: Returns True if playing, False otherwise

        Notes:
            Judged based on the return value of GetState(); returns False when communication is abnormal
        """
        # 检查状态值是否为播放状态（0x0201）
        return self.GetState() == 0x0201

    def IsPaused(self):
        """
        判断KT403A模块是否处于暂停状态。

        Returns:
            bool: 暂停状态返回True，否则返回False

        Notes:
            基于GetState()的返回值判断；通信异常时返回False

        ---
        Determine if KT403A module is in paused state.

        Returns:
            bool: Returns True if paused, False otherwise

        Notes:
            Judged based on the return value of GetState(); returns False when communication is abnormal
        """
        # 检查状态值是否为暂停状态（0x0202）
        return self.GetState() == 0x0202


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
