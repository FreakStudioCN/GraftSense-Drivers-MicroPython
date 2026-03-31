# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/1/1 12:00
# @Author  : Kevin Köck
# @File    : main.py
# @Description : PMS5003空气质量传感器驱动，支持主动/被动模式、节能模式、异步读取等。
# @License : MIT

__version__ = "0.1.0"
__author__ = "Kevin Köck"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import uasyncio as asyncio
import time

try:
    import struct
except ImportError:
    import ustruct as struct

# ======================================== 全局变量 ============================================
# 传感器唤醒后需要至少30秒稳定
WAIT_AFTER_WAKEUP = 40

# 正常数据帧长度
DATA_FRAME_LENGTH = 28
# 命令响应帧长度
CMD_FRAME_LENGTH = 4

# 命令失败最大重试次数，实际尝试次数是库尝试次数的两倍
MAX_COMMAND_FAILS = 3

DEBUG = False

# ======================================== 功能函数 ============================================
def set_debug(debug: bool) -> None:
    """设置调试输出开关

    Args:
        debug (bool): 是否启用调试输出

    Notes:
        启用后会在控制台打印更多调试信息

    ==========================================
    Set debug output switch

    Args:
        debug (bool): enable debug output or not

    Notes:
        More debug information will be printed to console when enabled
    """
    global DEBUG
    DEBUG = debug


# ======================================== 自定义类 ============================================
class PMS5003_base:
    """
    PMS5003空气质量传感器基础类，实现与传感器的通信协议和基本控制。

    Attributes:
        _uart (UART): UART通信对象
        _set_pin (Pin): 控制SET引脚（可选）
        _reset_pin (Pin): 控制RESET引脚（可选）
        _active (bool): 传感器是否处于活动状态
        _active_mode (bool): 是否为主动模式
        _eco_mode (bool): 是否启用节能模式（仅被动模式有效）
        _sreader (StreamReader): UART异步流读取器
        _interval_passive_mode (int): 被动模式下的采样间隔（秒）
        _event (Event): 事件对象，用于通知新数据到达
        _lock (Lock): 异步锁，保护共享资源
        _timestamp (int): 最近一次数据的时间戳（毫秒）
        _sleeping_state (bool): 传感器是否处于睡眠状态
        _callback (callable): 数据更新回调函数或协程
        _pm10_standard (int): PM1.0标准浓度
        _pm25_standard (int): PM2.5标准浓度
        _pm100_standard (int): PM10标准浓度
        _pm10_env (int): PM1.0环境浓度
        _pm25_env (int): PM2.5环境浓度
        _pm100_env (int): PM10环境浓度
        _particles_03um (int): >0.3µm颗粒物计数
        _particles_05um (int): >0.5µm颗粒物计数
        _particles_10um (int): >1.0µm颗粒物计数
        _particles_25um (int): >2.5µm颗粒物计数
        _particles_50um (int): >5.0µm颗粒物计数
        _particles_100um (int): >10µm颗粒物计数

    Methods:
        setEcoMode(): 设置节能模式
        setActiveMode(): 切换到主动模式
        setPassiveMode(): 切换到被动模式
        sleep(): 使传感器进入睡眠状态
        wakeUp(): 唤醒传感器
        reset(): 硬件复位传感器
        stop(): 停止传感器并进入睡眠
        start(): 启动传感器读取任务
        registerCallback(): 注册数据更新回调
        registerEvent(): 注册事件通知
        print(): 打印当前测量数据
        read(): 获取当前所有测量数据
        timestamp(): 获取最后数据时间戳

    Notes:
        本类为异步驱动基础类，使用asyncio进行协程调度。
        在主动模式下传感器持续发送数据，被动模式需通过命令请求数据。

    ==========================================
    PMS5003 air quality sensor base class, implements communication protocol and basic control.

    Attributes:
        _uart (UART): UART communication object
        _set_pin (Pin): SET pin control (optional)
        _reset_pin (Pin): RESET pin control (optional)
        _active (bool): Sensor active state
        _active_mode (bool): Active mode flag
        _eco_mode (bool): Eco mode flag (only effective in passive mode)
        _sreader (StreamReader): UART async stream reader
        _interval_passive_mode (int): Sampling interval in passive mode (seconds)
        _event (Event): Event object for new data notification
        _lock (Lock): Async lock for shared resources
        _timestamp (int): Timestamp of last data (milliseconds)
        _sleeping_state (bool): Sensor sleeping state
        _callback (callable): Data update callback or coroutine
        _pm10_standard (int): PM1.0 standard concentration
        _pm25_standard (int): PM2.5 standard concentration
        _pm100_standard (int): PM10 standard concentration
        _pm10_env (int): PM1.0 environmental concentration
        _pm25_env (int): PM2.5 environmental concentration
        _pm100_env (int): PM10 environmental concentration
        _particles_03um (int): >0.3µm particle count
        _particles_05um (int): >0.5µm particle count
        _particles_10um (int): >1.0µm particle count
        _particles_25um (int): >2.5µm particle count
        _particles_50um (int): >5.0µm particle count
        _particles_100um (int): >10µm particle count

    Methods:
        setEcoMode(): Set eco mode
        setActiveMode(): Switch to active mode
        setPassiveMode(): Switch to passive mode
        sleep(): Put sensor to sleep
        wakeUp(): Wake up sensor
        reset(): Hardware reset sensor
        stop(): Stop sensor and put to sleep
        start(): Start sensor reading task
        registerCallback(): Register data update callback
        registerEvent(): Register event notification
        print(): Print current measurement data
        read(): Get all current measurement data
        timestamp(): Get last data timestamp

    Notes:
        This is an asynchronous base driver class, uses asyncio for coroutine scheduling.
        In active mode sensor continuously sends data; in passive mode data is requested by command.
    """

    def __init__(self, uart, lock=None, set_pin=None, reset_pin=None, interval_passive_mode=None,
                 event=None, active_mode=True, eco_mode=True, assume_sleeping=True) -> None:
        """
        初始化PMS5003传感器对象

        Args:
            uart (UART): UART通信对象
            lock (asyncio.Lock, optional): 外部异步锁，用于多任务同步
            set_pin (Pin, optional): SET引脚控制对象
            reset_pin (Pin, optional): RESET引脚控制对象
            interval_passive_mode (int, optional): 被动模式下的采样间隔（秒），默认60
            event (asyncio.Event, optional): 事件对象，新数据时设置
            active_mode (bool): 初始模式，True为主动模式，False为被动模式
            eco_mode (bool): 是否启用节能模式（仅被动模式有效）
            assume_sleeping (bool): 假设传感器初始处于睡眠状态

        Notes:
            set_pin和reset_pin若提供，将使用硬件引脚控制；否则使用软件命令。

        ==========================================
        Initialize PMS5003 sensor object

        Args:
            uart (UART): UART communication object
            lock (asyncio.Lock, optional): External async lock for multi-task synchronization
            set_pin (Pin, optional): SET pin control object
            reset_pin (Pin, optional): RESET pin control object
            interval_passive_mode (int, optional): Sampling interval in passive mode (seconds), default 60
            event (asyncio.Event, optional): Event object, set when new data arrives
            active_mode (bool): Initial mode, True for active mode, False for passive mode
            eco_mode (bool): Enable eco mode (only effective in passive mode)
            assume_sleeping (bool): Assume sensor initially in sleep state

        Notes:
            If set_pin and reset_pin are provided, hardware pin control will be used; otherwise software commands.
        """
        self._uart = uart  # accepts a uart object
        self._set_pin = set_pin
        if set_pin is not None:
            set_pin.value(1)
        self._reset_pin = reset_pin
        if reset_pin is not None:
            reset_pin.value(1)
        self._active = True
        self._active_mode = active_mode  # passive mode will be set on first wakeUp() in _read()
        self._eco_mode = eco_mode  # only works with passive mode as sleep is not possible in active_mode
        self._sreader = asyncio.StreamReader(uart)
        self._interval_passive_mode = interval_passive_mode or 60  # in case someone forgets to set it
        if self._eco_mode and self._active_mode is False and self._interval_passive_mode < WAIT_AFTER_WAKEUP + 5:
            self._error(
                "interval_passive_mode can't be less than DEVICE_WAKEUP_TIME of {!s}s".format(
                    WAIT_AFTER_WAKEUP + 5))
            self._interval_passive_mode = 60
        self._event = event
        self._lock = asyncio.Lock()
        self._timestamp = None
        self._sleeping_state = assume_sleeping  # assume sleeping on start by default
        self._invalidateMeasurements()
        self._callback = None  # can be a short coroutine too; no args given
        asyncio.create_task(self._read())

    @staticmethod
    def _error(message: str) -> None:
        """
        错误日志输出（可被子类重写）

        Args:
            message (str): 错误信息

        Notes:
            默认实现为打印到标准输出

        ==========================================
        Error log output (can be overridden by subclass)

        Args:
            message (str): Error message

        Notes:
            Default implementation prints to stdout
        """
        print(message)

    @staticmethod
    def _warn(message: str) -> None:
        """
        警告日志输出（可被子类重写）

        Args:
            message (str): 警告信息

        Notes:
            默认实现为打印到标准输出

        ==========================================
        Warning log output (can be overridden by subclass)

        Args:
            message (str): Warning message

        Notes:
            Default implementation prints to stdout
        """
        print(message)

    @staticmethod
    def _debug(message: str) -> None:
        """
        调试日志输出（可被子类重写）

        Args:
            message (str): 调试信息

        Notes:
            仅在全局DEBUG为True时输出

        ==========================================
        Debug log output (can be overridden by subclass)

        Args:
            message (str): Debug message

        Notes:
            Output only when global DEBUG is True
        """
        if DEBUG:
            print(message)

    def setEcoMode(self, value: bool = True) -> None:
        """
        设置节能模式

        Args:
            value (bool): True启用，False禁用

        Notes:
            仅在被动模式下有效，启用后传感器在两次读取之间进入睡眠

        ==========================================
        Set eco mode

        Args:
            value (bool): True enable, False disable

        Notes:
            Only effective in passive mode, sensor will sleep between readings when enabled
        """
        self._eco_mode = value
        if self._eco_mode and self._active_mode is False and self._interval_passive_mode < WAIT_AFTER_WAKEUP + 5:
            self._error(
                "interval_passive_mode can't be less than DEVICE_WAKEUP_TIME of {!s}s".format(
                    WAIT_AFTER_WAKEUP + 5))
            self._interval_passive_mode = 60

    async def setActiveMode(self) -> bool:
        """
        切换到主动模式

        Returns:
            bool: 成功返回True，失败返回False

        Notes:
            传感器将开始连续发送数据，不再需要主动请求

        ==========================================
        Switch to active mode

        Returns:
            bool: True on success, False on failure

        Notes:
            Sensor will start continuous data transmission, no need to request actively
        """
        if self._active is False:
            self._active_mode = True
            return True
        self._debug("setActiveMode")
        async with self._lock:
            self._debug("setActiveMode got lock")
            res = await self._sendCommand(0xe1, 0x01)
            if res is None:
                await asyncio.sleep_ms(100)
                res = await self._sendCommand(0xe1, 0x01)
                if res is None:
                    self._error("Error putting device in active mode")
                    return False
            self._active_mode = True
            self._debug("setActiveMode Done")
        return True

    async def setPassiveMode(self, interval: int = None) -> bool:
        """
        切换到被动模式

        Args:
            interval (int, optional): 采样间隔（秒），默认使用之前设置的值

        Returns:
            bool: 成功返回True，失败返回False

        Notes:
            传感器仅在收到请求时发送数据，适合低功耗场景

        ==========================================
        Switch to passive mode

        Args:
            interval (int, optional): Sampling interval (seconds), default uses previously set value

        Returns:
            bool: True on success, False on failure

        Notes:
            Sensor sends data only on request, suitable for low power scenarios
        """
        if self._active is False:
            self._active_mode = False
            return True
        self._debug("setPassiveMode")
        async with self._lock:
            self._debug("setPassiveMode got lock")
            res = await self._sendCommand(0xe1, 0x00)
            if res is None:
                await asyncio.sleep_ms(100)
                res = await self._sendCommand(0xe1, 0x00)
                if res is None:
                    self._error("Error putting device in passive mode")
                    return False
            if interval is not None:
                self._interval_passive_mode = interval
                if self._eco_mode and self._active_mode is False and self._interval_passive_mode < WAIT_AFTER_WAKEUP + 5:
                    self._error(
                        "interval_passive_mode can't be less than DEVICE_WAKEUP_TIME of {!s}s".format(
                            WAIT_AFTER_WAKEUP + 5))
                    self._interval_passive_mode = 60
            self._active_mode = False
            await asyncio.sleep_ms(100)
            self._flush_uart()  # no leftovers from active mode
        self._debug("setPassiveMode done")
        return True

    async def sleep(self) -> bool:
        """
        使传感器进入睡眠状态

        Returns:
            bool: 成功返回True，失败返回False

        Notes:
            睡眠状态下传感器停止测量，功耗极低

        ==========================================
        Put sensor to sleep

        Returns:
            bool: True on success, False on failure

        Notes:
            Sensor stops measuring in sleep state, very low power consumption
        """
        self._debug("sleep")
        async with self._lock:
            self._debug("sleep got lock")
            if self._set_pin is not None:
                self._set_pin.value(0)
                # response on pin change?
            else:
                res = await self._sendCommand(0xe4, 0x00)
                if res is None:
                    await asyncio.sleep_ms(100)
                    res = await self._sendCommand(0xe4, 0x00)
                    if res is None:
                        self._sleeping_state = True  # just to make it possible for wakeUp to try again
                        self._error("Error putting device to sleep")
                        return False
            self._sleeping_state = True
        self._debug("Putting device to sleep")
        return True

    async def wakeUp(self) -> bool:
        """
        唤醒传感器

        Returns:
            bool: 成功返回True，失败返回False

        Notes:
            唤醒后需要等待WAIT_AFTER_WAKEUP秒才能稳定测量

        ==========================================
        Wake up sensor

        Returns:
            bool: True on success, False on failure

        Notes:
            Need to wait WAIT_AFTER_WAKEUP seconds after wake up for stable measurement
        """
        self._debug("wakeUp")
        async with self._lock:
            self._debug("wakeUp got lock")
            self._flush_uart()
            if self._set_pin is not None:
                self._set_pin.value(1)
                self._debug("Waiting {!s}s".format(WAIT_AFTER_WAKEUP))
                await asyncio.sleep_ms(WAIT_AFTER_WAKEUP)
                self._flush_uart()
                res = await self._read_frame()
                if res is None:
                    self._error("No response to wakeup pin change")
                    return False
            else:
                res = await self._sendCommand(0xe4, 0x01, False, delay=16000,
                                              wait=WAIT_AFTER_WAKEUP * 1000)
                if res is None:
                    await asyncio.sleep_ms(100)
                    res = await self._sendCommand(0xe4, 0x01, False, delay=16000,
                                                  wait=WAIT_AFTER_WAKEUP * 1000)
                    if res is None:
                        self._error("No response to wakeup command")
                        return False
                self._flush_uart()
        self._debug("device woke up")
        self._sleeping_state = False
        if self._active_mode is False:
            if self._lock.locked():
                self._error("Lock should be released in wakeUp before setPassiveMode")
            await self.setPassiveMode()
            # device does not save passive state
        self._debug("wakeUp done")
        return True

    def isActive(self) -> bool:
        """
        检查传感器是否处于活动状态

        Returns:
            bool: 活动返回True，否则False

        ==========================================
        Check if sensor is active

        Returns:
            bool: True if active, otherwise False
        """
        return self._active

    async def reset(self) -> bool:
        """
        硬件复位传感器

        Returns:
            bool: 成功返回True，失败返回False

        Notes:
            需要提供reset_pin引脚

        ==========================================
        Hardware reset sensor

        Returns:
            bool: True on success, False on failure

        Notes:
            reset_pin pin must be provided
        """
        if self._reset_pin is not None:
            self._reset_pin.value(0)
            await asyncio.sleep(5)
            self._reset_pin.value(1)
            if self._active:
                async with self._lock:
                    if await self._read_frame() is None:
                        self._error("Reset did not work, reset manually")
                        return False
                    return True
        else:
            self._error("No reset pin defined, can't reset")
            return False

    async def _sendCommand(self, command: int, data: int, expect_command: bool = True, delay: int = 1000, wait: int = None) -> bool or tuple:
        """
        发送命令并等待响应

        Args:
            command (int): 命令字节
            data (int): 数据字节
            expect_command (bool): 是否期望命令响应帧
            delay (int): 超时等待时间（毫秒）
            wait (int, optional): 额外等待时间（毫秒）

        Returns:
            bool or tuple: 成功返回True（命令响应）或数据帧元组，失败返回None

        Notes:
            内部使用，处理命令发送和响应接收

        ==========================================
        Send command and wait for response

        Args:
            command (int): Command byte
            data (int): Data byte
            expect_command (bool): Expect command response frame
            delay (int): Timeout wait (milliseconds)
            wait (int, optional): Additional wait time (milliseconds)

        Returns:
            bool or tuple: True on success (command response) or data frame tuple, None on failure

        Notes:
            Internal use, handles command sending and response reception
        """
        self._debug(
            "Sending command: {!s},{!s},{!s},{!s}".format(command, data, expect_command, delay))
        arr = bytearray(7)
        arr[0] = 0x42
        arr[1] = 0x4d
        arr[2] = command
        arr[3] = 0x00
        arr[4] = data
        s = sum(arr[:5])
        arr[5] = int(s / 256)
        arr[6] = s % 256
        self._flush_uart()
        self._uart.write(arr)
        et = time.ticks_ms() + delay + (wait if wait else 0)
        frame_len = CMD_FRAME_LENGTH + 4 if expect_command else DATA_FRAME_LENGTH + 4
        # self._debug("Expecting {!s}".format(frame_len))
        if wait:
            self._debug("waiting {!s}s".format(wait / 1000))
            await asyncio.sleep_ms(wait)
            self._flush_uart()
        while time.ticks_ms() < et:
            await asyncio.sleep_ms(100)
            if self._uart.any() >= frame_len:
                # going through all pending data frames
                res = await self._read_frame()
                if res is True and expect_command:
                    self._debug("Got True")
                    return True
                elif res is not None:
                    self._debug("Got {!s}".format(res))
                    return res
                else:
                    pass  # try again until found a valid one or timeout
                await asyncio.sleep_ms(100)
        self._debug("Got no available bytes")
        return None

    async def stop(self) -> None:
        """
        停止传感器并进入睡眠

        Notes:
            调用后传感器不再读取数据，可通过start()重新启动

        ==========================================
        Stop sensor and put to sleep

        Notes:
            After call, sensor stops reading data, can be restarted with start()
        """
        self._active = False
        await self.sleep()

    async def start(self) -> None:
        """
        启动传感器读取任务

        Notes:
            如果传感器已停止，重新启动后台读取任务

        ==========================================
        Start sensor reading task

        Notes:
            If sensor is stopped, restart background reading task
        """
        # coroutine as everything else is a coroutine
        if self._active is False:
            self._active = True
            asyncio.create_task(self._read())
        else:
            self._warn("Sensor already active")

    def registerCallback(self, callback) -> None:
        """
        注册数据更新回调函数

        Args:
            callback (callable): 回调函数或协程，无参数

        Notes:
            支持多次调用以注册多个回调，回调应快速执行

        ==========================================
        Register data update callback

        Args:
            callback (callable): Callback function or coroutine, no arguments

        Notes:
            Multiple callbacks can be registered by calling multiple times, callbacks should be fast
        """
        # callback will be called on every new sensor value, should be fast in active mode
        if self._callback is None:
            self._callback = callback
        elif type(self._callback) == list:
            self._callback.append(callback)
        else:
            self._callback = [self._callback, callback]

    def registerEvent(self, event) -> None:
        """
        注册事件对象，新数据到达时设置事件

        Args:
            event (asyncio.Event): 异步事件对象

        Notes:
            便于在主动模式下快速响应新数据

        ==========================================
        Register event object, set event when new data arrives

        Args:
            event (asyncio.Event): Async event object

        Notes:
            Useful for quick response to new data in active mode
        """
        # enhances usability; by using an event with active mode a fast reaction to
        # changing values is possible
        self._event = event

    def print(self) -> None:
        """
        打印当前测量数据到控制台

        Notes:
            仅当有有效数据时打印

        ==========================================
        Print current measurement data to console

        Notes:
            Only prints if valid data exists
        """
        if self._active and self._timestamp is not None:
            print("")
            print("---------------------------------------------")
            t = time.localtime()
            print("Measurement {!s}ms ago at {}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                time.ticks_ms() - self._timestamp, t[0], t[1], t[2], t[3], t[4], t[5]))
            print("---------------------------------------------")
            print("Concentration Units (standard)")
            print("---------------------------------------------")
            print("PM 1.0: %d\tPM2.5: %d\tPM10: %d" % (
                self._pm10_standard, self._pm25_standard, self._pm100_standard))
            print("Concentration Units (environmental)")
            print("---------------------------------------------")
            print("PM 1.0: %d\tPM2.5: %d\tPM10: %d" % (
                self._pm10_env, self._pm25_env, self._pm100_env))
            print("---------------------------------------------")
            print("Particles > 0.3um / 0.1L air:", self._particles_03um)
            print("Particles > 0.5um / 0.1L air:", self._particles_05um)
            print("Particles > 1.0um / 0.1L air:", self._particles_10um)
            print("Particles > 2.5um / 0.1L air:", self._particles_25um)
            print("Particles > 5.0um / 0.1L air:", self._particles_50um)
            print("Particles > 10 um / 0.1L air:", self._particles_100um)
            print("---------------------------------------------")
            print("")
        else:
            print("PMS5003 Sensor not active")

    def _flush_uart(self) -> None:
        """
        清空UART接收缓冲区

        Notes:
            丢弃所有待读取数据

        ==========================================
        Flush UART receive buffer

        Notes:
            Discard all pending data
        """
        while self._uart.any():
            self._uart.read(self._uart.any())

    async def _read(self) -> None:
        """
        后台读取任务，循环获取传感器数据

        Notes:
            根据当前模式（主动/被动）和节能设置，定期读取数据并更新内部变量，
            同时触发回调或事件。若长时间无数据则尝试复位。

        ==========================================
        Background reading task, periodically fetch sensor data

        Notes:
            Depending on current mode (active/passive) and eco settings, periodically read data
            and update internal variables, trigger callbacks or events. Reset if no data for long time.
        """
        woke_up = None
        if self._sleeping_state:
            await self.wakeUp()  # just in case controller rebooted and left device in sleep mode
            woke_up = time.ticks_ms()
        elif self._active_mode is False:
            await self.setPassiveMode()
        last_reading = time.ticks_ms()
        while self._active:
            diff = time.ticks_ms() - last_reading
            if woke_up is not None:
                diff = time.ticks_ms() - woke_up
            if self._active_mode and diff > 60000:
                # in passive mode it would be detected when requesting new data
                # but maybe this does not work because of StreamReader
                self._warn("No new data since 60s, resetting device")
                if await self.reset() is False:
                    self._error("Disabling device as it can not be reset")
                    self._active = False
                    self._sleeping_state = True
                    # always assume sleeping state if device is started again as this also sets active_mode
            if self._sleeping_state is False:  # safeguard as wakeUp() while inside lock is not possible
                async with self._lock:
                    self._debug("_read got lock")
                    frame = None
                    counter = 0
                    while frame is None and counter < 5:
                        if self._active_mode:
                            frame = await self._read_frame(False, True)  # lock already acquired
                        else:
                            frame = await self._sendCommand(0xe2, 0x00, False, delay=10000)
                        if frame is not None:
                            self._pm10_standard = frame[0]
                            self._pm25_standard = frame[1]
                            self._pm100_standard = frame[2]
                            self._pm10_env = frame[3]
                            self._pm25_env = frame[4]
                            self._pm100_env = frame[5]
                            self._particles_03um = frame[6]
                            self._particles_05um = frame[7]
                            self._particles_10um = frame[8]
                            self._particles_25um = frame[9]
                            self._particles_50um = frame[10]
                            self._particles_100um = frame[11]
                            self._timestamp = time.ticks_ms()
                            if self._active and self._event is not None:
                                self._event.set()
                            if self._active and self._callback is not None:
                                cbs = [self._callback] if type(
                                    self._callback) != list else self._callback
                                for cb in cbs:
                                    # call callback or await coroutine, should be short.
                                    tmp = cb()
                                    if str(type(tmp)) == "<class 'generator'>":
                                        await tmp
                            last_reading = time.ticks_ms()
                        counter += 1
                        await asyncio.sleep_ms(100)
            if self._active_mode:
                await asyncio.sleep_ms(100)
                # give other commands time to send and receive response (keep lock free)
                woke_up = None
            else:
                sleep = self._interval_passive_mode - (time.ticks_ms() - last_reading) / 1000
                if self._eco_mode:
                    await self.sleep()
                    sleep -= (WAIT_AFTER_WAKEUP + 1)
                    # +1 is experience as commands to wakeup and set mode take time
                else:
                    woke_up = None  # probably changed mode during sleep
                if sleep < 2:  # making 2s between reading attempts the smallest interval
                    sleep = 2
                sleep = int(sleep)
                # a bit of rounding the value, a few hundred ms earlier is needed for commands
                self._debug("loop sleep for {!s}s".format(sleep))
                await asyncio.sleep(sleep)
                if self._sleeping_state:
                    await self.wakeUp()
                    woke_up = time.ticks_ms()

        self._invalidateMeasurements()  # set values to None if device is not active anymore

    async def _read_frame(self, with_lock: bool = False, with_async: bool = False) -> tuple or bool or None:
        """
        读取一个完整的数据帧或命令响应帧

        Args:
            with_lock (bool): 是否使用锁保护
            with_async (bool): 是否使用异步流读取器

        Returns:
            tuple or bool or None: 数据帧元组、命令响应成功True，或失败None

        Notes:
            内部使用，处理帧同步和校验

        ==========================================
        Read a complete data frame or command response frame

        Args:
            with_lock (bool): Use lock protection or not
            with_async (bool): Use async stream reader or not

        Returns:
            tuple or bool or None: Data frame tuple, command response True, or None on failure

        Notes:
            Internal use, handles frame synchronization and checksum
        """
        # using lock to prevent multiple coroutines from reading at the same time
        self._debug("readFrame {!s} {!s}".format(with_lock, with_async))
        if with_lock:
            async with self._lock:
                self._debug("readFrame got lock")
                res = await self.__read_frame(with_async)  # can be None
                self._debug("readFrame got: {!s}".format(res))
                return res
        else:
            res = await self.__read_frame(with_async)  # can be None
            self._debug("readFrame got: {!s}".format(res))
            return res

    async def __await_bytes(self, count: int, timeout: int) -> None:
        """
        等待UART接收指定字节数

        Args:
            count (int): 期望的字节数
            timeout (int): 超时时间（毫秒）

        Notes:
            内部辅助函数，循环等待直到收到足够数据或超时

        ==========================================
        Wait for UART to receive specified number of bytes

        Args:
            count (int): Desired number of bytes
            timeout (int): Timeout (milliseconds)

        Notes:
            Internal helper, loops until enough data or timeout
        """
        st = time.ticks_ms()
        while self._uart.any() < count:
            await asyncio.sleep_ms(20)
            if time.ticks_ms() - st > timeout:
                return

    async def __read_frame(self, with_async: bool) -> tuple or bool or None:
        """
        实际读取帧的核心实现

        Args:
            with_async (bool): 是否使用异步流读取器

        Returns:
            tuple or bool or None: 数据帧元组、命令响应True，或失败None

        Notes:
            内部函数，处理帧解析和校验

        ==========================================
        Core implementation of frame reading

        Args:
            with_async (bool): Use async stream reader or not

        Returns:
            tuple or bool or None: Data frame tuple, command response True, or None on failure

        Notes:
            Internal function, handles frame parsing and checksum
        """
        buffer = []
        start = time.ticks_ms()
        timeout = 200
        self._debug("__read_frame")
        available = self._uart.any()
        if available > 32 and available % 32 == 0:
            self._uart.read(available - 32)  # just throw away the oldest data_frames
            self._debug("Throwing away old data_frames, #bytes {!s}".format(available - 32))
        while True:
            if with_async is False and time.ticks_ms() - start > timeout:
                self._debug(
                    "Reading a lot of noise on RX line to exceed timeout of {!s}ms, availble bytes {!s}".format(
                        timeout, self._uart.any()))
                return None
            preframe_len = 4 + CMD_FRAME_LENGTH - len(buffer)
            if with_async:
                # StreamReader seems to have problems reading the correct amount of bytes
                data = b""
                count = 0
                while len(data) < preframe_len:
                    data += await self._sreader.read(preframe_len - len(data))
                    if count > 5:
                        break
                    count += 1
            else:
                await self.__await_bytes(preframe_len, 100)
                data = self._uart.read(preframe_len)
            if len(data) is None:
                self._debug("Read no data from uart despite having waited for data")
                return None
            if len(data) != preframe_len and len(data) > 0:
                self._error(
                    "Short read, expected {!s} bytes, got {!s}".format(preframe_len, len(data)))
                return None
            if data == b'':
                return None
            buffer += list(data)
            while len(buffer) >= 2 and buffer[0] != 0x42 and buffer[1] != 0x4d:
                buffer.pop(0)
            if len(buffer) == 0:
                continue
            elif len(buffer) < 4:
                continue
            frame_len = struct.unpack(">H", bytes(buffer[2:4]))[0]
            if frame_len == DATA_FRAME_LENGTH:
                if with_async:
                    # StreamReader seems to have problems reading the correct amount of bytes
                    data = b""
                    count = 0
                    while len(data) < frame_len - CMD_FRAME_LENGTH:
                        data += await self._sreader.read(frame_len - CMD_FRAME_LENGTH - len(data))
                        if count > 5:
                            break
                        count += 1
                else:
                    await self.__await_bytes(frame_len - CMD_FRAME_LENGTH, 100)
                    data = self._uart.read(frame_len - CMD_FRAME_LENGTH)
                if len(data) != DATA_FRAME_LENGTH - CMD_FRAME_LENGTH:
                    self._error(
                        "Short read, expected {!s} bytes, got {!s}".format(frame_len, len(data)))
                    return None
                buffer += list(data)
                check = buffer[-2] * 256 + buffer[-1]
                checksum = sum(buffer[0:frame_len + 2])
                if check == checksum:
                    if self._uart.any() > 32:
                        self._flush_uart()  # just to prevent getting flooded if a callback took too long
                        self._warn("Getting too many new data frames, callback too slow")
                    frame = struct.unpack(">HHHHHHHHHHHHHH", bytes(buffer[4:]))
                    no_values = True
                    for i in range(6, 12):
                        if frame[i] != 0:
                            no_values = False
                    if no_values:
                        buffer = []
                        self._debug("got no values")
                        await asyncio.sleep_ms(50)
                        start = time.ticks_ms()  # reset timeout counter
                        continue
                    else:
                        return frame
            elif frame_len == CMD_FRAME_LENGTH:
                check = buffer[-2] * 256 + buffer[-1]
                checksum = sum(buffer[0:frame_len + 2])
                if check == checksum:
                    self._debug("Received command response frame: {!s}".format(buffer))
                    return True
                else:
                    return None
            elif frame_len == 0:
                pass  # wrong frame/bytes received
            else:
                self._warn("Unexpected frame_len {!s}, probably random or scrambled bytes".format(
                    frame_len))

            buffer = []
            continue

            # pm10_standard, pm25_standard, pm100_standard, pm10_env,
            # pm25_env, pm100_env, particles_03um, particles_05um, particles_10um,
            # particles_25um, particles_50um, particles100um, skip, checksum=frame

    def _invalidateMeasurements(self) -> None:
        """
        将所有测量值设置为None

        Notes:
            当传感器未激活时调用

        ==========================================
        Set all measurement values to None

        Notes:
            Called when sensor is not active
        """
        self._pm10_standard = None
        self._pm25_standard = None
        self._pm100_standard = None
        self._pm10_env = None
        self._pm25_env = None
        self._pm100_env = None
        self._particles_03um = None
        self._particles_05um = None
        self._particles_10um = None
        self._particles_25um = None
        self._particles_50um = None
        self._particles_100um = None

    @property
    def pm10_standard(self) -> int:
        """获取PM1.0标准浓度"""
        return self._pm10_standard

    @property
    def pm25_standard(self) -> int:
        """获取PM2.5标准浓度"""
        return self._pm25_standard

    @property
    def pm100_standard(self) -> int:
        """获取PM10标准浓度"""
        return self._pm100_standard

    @property
    def pm10_env(self) -> int:
        """获取PM1.0环境浓度"""
        return self._pm10_env

    @property
    def pm25_env(self) -> int:
        """获取PM2.5环境浓度"""
        return self._pm25_env

    @property
    def pm100_env(self) -> int:
        """获取PM10环境浓度"""
        return self._pm100_env

    @property
    def particles_03um(self) -> int:
        """获取>0.3µm颗粒物计数"""
        return self._particles_03um

    @property
    def particles_05um(self) -> int:
        """获取>0.5µm颗粒物计数"""
        return self._particles_05um

    @property
    def particles_10um(self) -> int:
        """获取>1.0µm颗粒物计数"""
        return self._particles_10um

    @property
    def particles_25um(self) -> int:
        """获取>2.5µm颗粒物计数"""
        return self._particles_25um

    @property
    def particles_50um(self) -> int:
        """获取>5.0µm颗粒物计数"""
        return self._particles_50um

    @property
    def particles_100um(self) -> int:
        """获取>10µm颗粒物计数"""
        return self._particles_100um

    def read(self) -> tuple or None:
        """
        获取当前所有测量数据

        Returns:
            tuple or None: 包含12个测量值的元组，若传感器未激活则返回None

        ==========================================
        Get all current measurement data

        Returns:
            tuple or None: Tuple of 12 measurement values, or None if sensor not active
        """
        if self._active:
            return (self._pm10_standard, self._pm25_standard, self._pm100_standard,
                    self._pm10_env, self._pm25_env, self._pm100_env,
                    self._particles_03um, self._particles_05um, self._particles_10um,
                    self._particles_25um, self._particles_50um, self._particles_100um)
        return None

    @property
    def timestamp(self) -> int:
        """获取最后一次数据的时间戳（毫秒）"""
        return self._timestamp


class PMS5003(PMS5003_base):
    """
    PMS5003传感器增强类，增加了命令重试和自动复位机制。

    Methods:
        wakeUp(): 唤醒传感器（带重试）
        sleep(): 使传感器睡眠（带重试）
        setActiveMode(): 切换到主动模式（带重试）
        setPassiveMode(): 切换到被动模式（带重试）

    Notes:
        继承自PMS5003_base，所有方法均通过_makeResilient增加重试逻辑，
        当命令失败时会尝试复位传感器。

    ==========================================
    Enhanced PMS5003 sensor class with command retry and auto-reset mechanism.

    Methods:
        wakeUp(): Wake up sensor (with retry)
        sleep(): Put sensor to sleep (with retry)
        setActiveMode(): Switch to active mode (with retry)
        setPassiveMode(): Switch to passive mode (with retry)

    Notes:
        Inherits from PMS5003_base, all methods are wrapped with retry logic via _makeResilient,
        will attempt to reset sensor on command failure.
    """

    def __init__(self, uart, lock=None, set_pin=None, reset_pin=None, interval_passive_mode=None,
                 event=None, active_mode=True, eco_mode=True, assume_sleeping=True) -> None:
        """
        初始化PMS5003传感器对象（增强版）

        Args:
            参数同PMS5003_base.__init__

        Notes:
            提供命令重试和自动复位能力

        ==========================================
        Initialize PMS5003 sensor object (enhanced)

        Args:
            Same as PMS5003_base.__init__

        Notes:
            Provides command retry and auto-reset capability
        """
        super().__init__(uart, set_pin=set_pin, reset_pin=reset_pin,
                         interval_passive_mode=interval_passive_mode,
                         event=event, active_mode=active_mode, eco_mode=eco_mode,
                         assume_sleeping=assume_sleeping)

    async def _makeResilient(self, *args, **kwargs) -> bool:
        """
        包装原始方法，实现重试和复位逻辑

        Args:
            *args: 可变位置参数
            **kwargs: 可变关键字参数，可包含first_try标志

        Returns:
            bool: 最终成功返回True，否则False

        Notes:
            内部方法，被其他方法调用

        ==========================================
        Wrap original method to implement retry and reset logic

        Args:
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments, may include first_try flag

        Returns:
            bool: True on final success, False otherwise

        Notes:
            Internal method, called by other methods
        """
        if "first_try" not in kwargs:
            first_try = True
        else:
            first_try = kwargs["first_try"]
            del kwargs["first_try"]
        if "command" in kwargs:
            command = kwargs["command"]
            del kwargs["command"]
        else:
            command = args[0]
            args = args[1:]
        count = 0
        while count < MAX_COMMAND_FAILS:
            if await command(*args, **kwargs) is False:
                count += 1
                await asyncio.sleep(1)
            else:
                return True
        if first_try:
            self._warn("Resetting not responding device")
            if await self.reset() is False:
                self._error("Shutting device down as it is not responding")
                self._active = False
                return False
        else:
            self._error("Shutting device down as it responds wrong even after reset")
            self._active = False
            self._sleeping_state = True
            # always assume sleeping state if device is started again as this also sets active_mode
            return False
        args = (command,) + args
        kwargs["first_try"] = False
        await self._makeResilient(*args, **kwargs)

    async def wakeUp(self) -> bool:
        """
        唤醒传感器（带重试和复位）

        Returns:
            bool: 成功返回True，失败返回False

        ==========================================
        Wake up sensor (with retry and reset)

        Returns:
            bool: True on success, False on failure
        """
        await self._makeResilient(super().wakeUp)

    async def sleep(self) -> bool:
        """
        使传感器睡眠（带重试和复位）

        Returns:
            bool: 成功返回True，失败返回False

        ==========================================
        Put sensor to sleep (with retry and reset)

        Returns:
            bool: True on success, False on failure
        """
        await self._makeResilient(super().sleep)

    async def setActiveMode(self) -> bool:
        """
        切换到主动模式（带重试和复位）

        Returns:
            bool: 成功返回True，失败返回False

        Notes:
            若传感器正在睡眠，会等待唤醒后再执行

        ==========================================
        Switch to active mode (with retry and reset)

        Returns:
            bool: True on success, False on failure

        Notes:
            If sensor is sleeping, will wait for wake up before executing
        """
        while self._active is True and self._sleeping_state is True:
            await asyncio.sleep_ms(100)
            # device has to wake up first and after that we'll set the state or
            # weird behaviour possible otherwise
        await self._makeResilient(super().setActiveMode)

    async def setPassiveMode(self, interval: int = None) -> bool:
        """
        切换到被动模式（带重试和复位）

        Args:
            interval (int, optional): 采样间隔（秒）

        Returns:
            bool: 成功返回True，失败返回False

        Notes:
            若传感器正在睡眠，会等待唤醒后再执行

        ==========================================
        Switch to passive mode (with retry and reset)

        Args:
            interval (int, optional): Sampling interval (seconds)

        Returns:
            bool: True on success, False on failure

        Notes:
            If sensor is sleeping, will wait for wake up before executing
        """
        while self._active is True and self._sleeping_state is True:
            await asyncio.sleep_ms(100)
            # device has to wake up first and after that we'll set the state or
            # weird behaviour possible otherwise
        await self._makeResilient(super().setPassiveMode, interval=interval)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================