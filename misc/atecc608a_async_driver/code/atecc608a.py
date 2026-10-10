# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : stewedio
# @File    : atecc608a.py
# @Description : ATECC608A / ATECC508A crypto authentication chip driver via I2C
# @License : MIT

__version__ = "1.0.0"
__author__ = "stewedio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import machine
import ubinascii
import utime
import micropython

import constant as ATCA_CONSTANTS
import exceptions as ATCA_EXCEPTIONS
import status as ATCA_STATUS
from basic import ATECCBasic

# ======================================== 全局变量 ============================================
# I2C 通信常量
# 7位 I2C 地址 (0x60)
I2C_ADDRESS = micropython.const(0xC0 >> 1)
# 默认 I2C 波特率 1MHz
BAUDRATE = micropython.const(1000000)
# 唤醒后等待延时 (us) = tWHI + tWLO
WAKE_DELAY = micropython.const(150)
# 默认接收重试次数
RX_RETRIES = micropython.const(20)
# 支持的芯片型号
SUPPORTED_DEVICES = {0x50: "ATECC508A", 0x60: "ATECC608A"}

# ======================================== 功能函数 ============================================
# 本驱动无独立的类外功能函数，所有功能由 ATECCX08A 类提供

# ======================================== 自定义类 ============================================


class ATECCX08A(ATECCBasic):
    """
    ATECCX08A 系列加密认证芯片 I2C 驱动

    提供通过 I2C 总线与 ATECC508A/ATECC608A 通信的底层接口，
    包括唤醒、空闲、休眠以及带重试的指令执行机制。
    Attributes:
        _bus (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _retries (int): 通信失败重试次数
        _device (str): 设备型号名称
        _debug (bool): 调试日志开关
    Methods:
        wake(): 唤醒设备
        idle(): 设备进入空闲状态
        sleep(): 设备进入休眠状态
        execute(): 执行加密指令包
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 I2C 实例（依赖注入）
        - 执行方法内置重试机制应对瞬态 I2C 错误
        - 自动识别 ATECC508A 和 ATECC608A 芯片型号
        - ATECC608A 是本类的别名
    ==========================================
    ATECCX08A series crypto authentication chip I2C driver.

    Provides low-level I2C communication with ATECC508A/ATECC608A,
    including wake, idle, sleep, and command execution with retry.
    Attributes:
        _bus (I2C): I2C bus instance
        _address (int): Device I2C address
        _retries (int): Communication retry count
        _device (str): Device model name
        _debug (bool): Debug log toggle
    Methods:
        wake(): Wake up the device
        idle(): Put device into idle state
        sleep(): Put device into sleep state
        execute(): Execute a crypto command packet
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided I2C instance (dependency injection)
        - Execute method has built-in retry for transient I2C errors
        - Auto-detects ATECC508A and ATECC608A chip models
        - ATECC608A is an alias for this class
    """

    def __init__(self, bus: machine.I2C, address: int = I2C_ADDRESS, retries: int = RX_RETRIES, debug: bool = False) -> None:
        """
        初始化 ATECCX08A 驱动

        检测设备是否存在并识别芯片型号。
        Args:
            bus (I2C): I2C 总线实例（必须由外部创建并传入）
            address (int): 设备 I2C 地址，默认 0x60
            retries (int): 通信失败重试次数，默认 20
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            ValueError: bus 不是有效的 I2C 实例
            NoDevicesFoundError: 指定地址未找到设备
            UnsupportedDeviceError: 不支持的芯片型号
        Notes:
            - bus 参数必须为有效 I2C 实例（鸭子类型检查）
            - 初始化时读取芯片信息以自动识别型号
        ==========================================
        Initialize ATECCX08A driver.

        Detects device presence and identifies chip model.
        Args:
            bus (I2C): I2C bus instance (must be externally created and passed in)
            address (int): Device I2C address, default 0x60
            retries (int): Communication retry count, default 20
            debug (bool): Whether to enable debug log output, default False
        Raises:
            ValueError: bus is not a valid I2C instance
            NoDevicesFoundError: No device found at specified address
            UnsupportedDeviceError: Unsupported chip model
        Notes:
            - bus must be a valid I2C instance (duck-type check)
            - Reads chip info during init to auto-detect model
        """
        # 参数校验：I2C 实例鸭子类型检查
        if not hasattr(bus, "readfrom_into"):
            raise ValueError("bus must be an I2C instance")
        # 参数校验：地址必须为整数
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        # 参数校验：重试次数必须为正整数
        if not isinstance(retries, int) or retries < 0:
            raise ValueError("retries must be a non-negative int")
        # 参数校验：debug 必须为 bool
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        # 设备扫描：检查目标地址是否存在
        if address not in bus.scan():
            raise ATCA_EXCEPTIONS.NoDevicesFoundError()

        self._bus = bus
        self._address = address
        self._retries = retries
        self._debug = debug

        # 读取芯片信息以识别型号
        try:
            self._device = SUPPORTED_DEVICES[self.atcab_info()[1 + 2]]
        except KeyError:
            raise ATCA_EXCEPTIONS.UnsupportedDeviceError()

        self._log("init: %s at addr=0x%02x" % (self._device, address))

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
            print("[ATECCX08A] %s" % msg)

    def __str__(self) -> str:
        return "<{:s} address=0x{:02x} retries={:d}>".format(self._device or self.__class__.__name__, self._address, self._retries)

    def __repr__(self) -> str:
        return str(self)

    @property
    def device(self) -> str:
        """
        获取设备型号名称
        Returns:
            str: 设备型号（如 "ATECC608A"）
        ==========================================
        Get device model name.
        Returns:
            str: Device model name (e.g. "ATECC608A")
        """
        return self._device

    def wake(self) -> None:
        """
        唤醒设备

        向 I2C 总线发送零地址写入，产生唤醒脉冲（tWLO）。
        Notes:
            - 唤醒后需等待 tWHI + tWLO（~150us）才能通信
            - 副作用：改变设备状态从休眠到活动
        ==========================================
        Wake up the device.

        Sends a zero-address write on the I2C bus to generate a wake pulse (tWLO).
        Notes:
            - Must wait tWHI + tWLO (~150us) after wake before communicating
            - Side effect: changes device state from sleep to active
        """
        self._log("wake")
        self._bus.writeto(self._address, b"\x00\x00")

    def idle(self) -> None:
        """
        设备进入空闲状态

        发送空闲字节使设备进入低功耗空闲模式。
        Notes:
            - 副作用：结束当前活动会话
        ==========================================
        Put device into idle state.

        Sends idle byte to enter low-power idle mode.
        Notes:
            - Side effect: ends current active session
        """
        self._log("idle")
        self._bus.writeto(self._address, b"\x02")

    def sleep(self) -> None:
        """
        设备进入休眠状态

        发送休眠字节使设备进入深度休眠模式。
        Notes:
            - 副作用：设备进入休眠，需 wake() 唤醒
        ==========================================
        Put device into sleep state.

        Sends sleep byte to enter deep sleep mode.
        Notes:
            - Side effect: device enters sleep, requires wake() to resume
        """
        self._log("sleep")
        self._bus.writeto(self._address, b"\x01")

    def execute(self, packet) -> None:
        """
        执行加密指令包

        带重试的 I2C 通信核心方法。每个周期：唤醒→等待→发送指令→
        循环读取响应→检查错误→处理特殊情况（看门狗、唤醒成功）。
        Args:
            packet (ATCAPacket): 待执行的指令包对象
        Raises:
            ATCA_EXCEPTIONS.CheckmacVerifyFailedError: CheckMac/Verify 验证失败
            ATCA_EXCEPTIONS.ParseError: 响应解析错误
            ATCA_EXCEPTIONS.EccFaultError: ECC 故障
            ATCA_EXCEPTIONS.ExecutionError: 指令执行错误
            ATCA_EXCEPTIONS.GenericError: 重试耗尽
        Notes:
            - 内置重试机制（最多 retries 次）
            - 看门狗即将到期时自动休眠以重置
            - ISR-safe: 否（阻塞 I2C 操作）
        ==========================================
        Execute a crypto command packet.

        Core I2C communication method with retry. Each cycle: wake -> wait ->
        send command -> poll for response -> check errors -> handle special cases.
        Args:
            packet (ATCAPacket): Command packet object to execute
        Raises:
            ATCA_EXCEPTIONS.CheckmacVerifyFailedError: CheckMac/Verify failed
            ATCA_EXCEPTIONS.ParseError: Response parse error
            ATCA_EXCEPTIONS.EccFaultError: ECC fault
            ATCA_EXCEPTIONS.ExecutionError: Command execution error
            ATCA_EXCEPTIONS.GenericError: Retries exhausted
        Notes:
            - Built-in retry mechanism (up to retries times)
            - Auto-sleeps when watchdog is about to expire
            - ISR-safe: No (blocking I2C operation)
        """
        retries = self._retries
        while retries:
            try:
                # 唤醒设备
                self.wake()
                # 等待 tWHI + tWLO 延时
                utime.sleep_us(WAKE_DELAY)

                # 设置设备名称用于延时计算
                if isinstance(self._device, str):
                    packet.device = self._device

                # 发送指令包（带 0x03 字标志）
                self._bus.writeto(self._address, b"\x03" + packet.to_buffer())

                resp = packet.response_data_mv

                # 循环读取响应，直至计算完成或超过 tEXEC
                d_t = packet.delay
                p_t = utime.ticks_ms()
                while utime.ticks_diff(utime.ticks_ms(), p_t) <= min(d_t, 250):
                    try:
                        self._bus.readfrom_into(self._address, resp[0:1])
                        self._bus.readfrom_into(self._address, resp[1 : resp[0]])
                    except OSError:
                        continue
                    else:
                        break

                # 检查响应状态
                err, exc = self.is_error(resp)
                if err == ATCA_STATUS.ATCA_SUCCESS:
                    # 成功：保存响应数据
                    packet._response_data = resp[: resp[0]]
                    return
                elif err == ATCA_STATUS.ATCA_WAKE_SUCCESS:
                    # 设备刚被唤醒（发送休眠字节后的状态）
                    return
                elif err == ATCA_STATUS.ATCA_WATCHDOG_ABOUT_TO_EXPIRE:
                    # 看门狗即将到期，先休眠重置
                    self.sleep()
                else:
                    # 已知错误：可能抛出异常
                    if exc is not None:
                        packet._response_data = resp[: resp[0]]
                        raise exc(ubinascii.hexlify(packet._response_data))
            except OSError:
                # I2C 通信瞬态错误，递减重试计数
                retries -= 1
        else:
            # 重试耗尽
            raise ATCA_EXCEPTIONS.GenericError("max retry")

    def deinit(self) -> None:
        """
        释放硬件资源

        将设备置于休眠状态并清除总线引用。
        Notes:
            - ISR-safe: 否
        ==========================================
        Release hardware resources.

        Puts device to sleep and clears bus reference.
        Notes:
            - ISR-safe: No
        """
        self._log("deinit")
        try:
            self.sleep()
        except Exception:
            pass
        self._bus = None


# ATECC608A 别名（与 ATECC508A 共用同一驱动类）
ATECC608A = ATECCX08A

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
