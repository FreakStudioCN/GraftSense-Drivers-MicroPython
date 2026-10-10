# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : cc1101.py
# @Description : CC1101 sub-GHz SPI 收发器驱动，通过 SPI 接口实现寄存器操作与数据包收发
# @License : GPL-3.0

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "GPL-3.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


try:
    from time import sleep_ms, sleep_us, ticks_diff, ticks_ms
except ImportError:
    import time

    def sleep_ms(ms):
        time.sleep(ms / 1000)

    def sleep_us(us):
        time.sleep(us / 1000000)

    def ticks_ms():
        return int(time.time() * 1000)

    def ticks_diff(new, old):
        return new - old


try:
    from machine import Pin
except ImportError:
    pass

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class CC1101:
    """
    CC1101 sub-GHz SPI 收发器驱动类
    Attributes:
        spi: SPI 总线实例
        cs: SPI 片选引脚
        gdo0: GDO0 中断引脚（可选）
        crystal_hz (int): 晶振频率（Hz），默认 26MHz
    Methods:
        reset(): 硬件复位芯片
        strobe(): 发送命令选通
        read_reg(): 读取单个配置寄存器
        write_reg(): 写入单个配置寄存器
        read_burst(): 批量读取寄存器
        write_burst(): 批量写入寄存器
        verify(): 验证芯片身份（部件号和版本号）
        configure(): 批量配置寄存器
        set_frequency(): 设置载波频率
        send_packet(): 发送数据包
        read_packet(): 读取数据包
        power_down(): 进入掉电模式
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 SPI 实例和 CS Pin 实例，不在内部创建总线对象
        - GDO0 引脚可选，可用于中断或状态查询
        - 发送前需根据当地法规配置正确的频率和功率参数
        - 基于 CC1101 数据手册命令模型和 eydam-prototyping/cc1101 寄存器结构
    ==========================================
    CC1101 sub-GHz SPI transceiver driver.
    Attributes:
        spi: SPI bus instance
        cs: SPI chip select pin
        gdo0: GDO0 interrupt pin (optional)
        crystal_hz (int): Crystal frequency in Hz, default 26MHz
    Methods:
        reset(): Hardware reset the chip
        strobe(): Send a command strobe
        read_reg(): Read a single configuration register
        write_reg(): Write a single configuration register
        read_burst(): Burst read multiple registers
        write_burst(): Burst write multiple registers
        verify(): Verify chip identity (part number and version)
        configure(): Batch configure registers
        set_frequency(): Set carrier frequency
        send_packet(): Transmit a data packet
        read_packet(): Read a received data packet
        power_down(): Enter power-down mode
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided SPI and CS Pin instances
        - GDO0 pin is optional, can be used for interrupts or status queries
        - Configure correct frequency and power for your region before transmitting
        - Based on CC1101 datasheet command model and eydam-prototyping/cc1101 register structure
    """

    # ==================== 类级常量：SPI 指令类型 ====================
    _WRITE_SINGLE = const(0x00)
    _WRITE_BURST = const(0x40)
    _READ_SINGLE = const(0x80)
    _READ_BURST = const(0xC0)

    # ==================== 类级常量：配置寄存器地址 ====================
    _IOCFG2 = const(0x00)
    _IOCFG1 = const(0x01)
    _IOCFG0 = const(0x02)
    _FIFOTHR = const(0x03)
    _SYNC1 = const(0x04)
    _SYNC0 = const(0x05)
    _PKTLEN = const(0x06)
    _PKTCTRL1 = const(0x07)
    _PKTCTRL0 = const(0x08)
    _ADDR = const(0x09)
    _CHANNR = const(0x0A)
    _FSCTRL1 = const(0x0B)
    _FSCTRL0 = const(0x0C)
    _FREQ2 = const(0x0D)
    _FREQ1 = const(0x0E)
    _FREQ0 = const(0x0F)
    _MDMCFG4 = const(0x10)
    _MDMCFG3 = const(0x11)
    _MDMCFG2 = const(0x12)
    _MDMCFG1 = const(0x13)
    _MDMCFG0 = const(0x14)
    _DEVIATN = const(0x15)
    _MCSM2 = const(0x16)
    _MCSM1 = const(0x17)
    _MCSM0 = const(0x18)
    _FOCCFG = const(0x19)
    _BSCFG = const(0x1A)
    _AGCCTRL2 = const(0x1B)
    _AGCCTRL1 = const(0x1C)
    _AGCCTRL0 = const(0x1D)
    _WOREVT1 = const(0x1E)
    _WOREVT0 = const(0x1F)
    _WORCTRL = const(0x20)
    _FREND1 = const(0x21)
    _FREND0 = const(0x22)
    _FSCAL3 = const(0x23)
    _FSCAL2 = const(0x24)
    _FSCAL1 = const(0x25)
    _FSCAL0 = const(0x26)
    _RCCTRL1 = const(0x27)
    _RCCTRL0 = const(0x28)
    _FSTEST = const(0x29)
    _PTEST = const(0x2A)
    _AGCTEST = const(0x2B)
    _TEST2 = const(0x2C)
    _TEST1 = const(0x2D)
    _TEST0 = const(0x2E)

    # ==================== 类级常量：命令选通 ====================
    _SRES = const(0x30)
    _SFSTXON = const(0x31)
    _SXOFF = const(0x32)
    _SCAL = const(0x33)
    _SRX = const(0x34)
    _STX = const(0x35)
    _SIDLE = const(0x36)
    _SWOR = const(0x38)
    _SPWD = const(0x39)
    _SFRX = const(0x3A)
    _SFTX = const(0x3B)
    _SWORRST = const(0x3C)
    _SNOP = const(0x3D)
    _PATABLE = const(0x3E)
    _TXFIFO = const(0x3F)
    _RXFIFO = const(0x3F)

    # ==================== 类级常量：状态寄存器地址 ====================
    _PARTNUM = const(0x30)
    _VERSION = const(0x31)
    _FREQEST = const(0x32)
    _LQI = const(0x33)
    _RSSI = const(0x34)
    _MARCSTATE = const(0x35)
    _WORTIME1 = const(0x36)
    _WORTIME0 = const(0x37)
    _PKTSTATUS = const(0x38)
    _VCO_VC_DAC = const(0x39)
    _TXBYTES = const(0x3A)
    _RXBYTES = const(0x3B)
    _RCCTRL1_STATUS = const(0x3C)
    _RCCTRL0_STATUS = const(0x3D)

    # ==================== 类级常量：芯片状态（MARCSTATE 低 5 位） ====================
    _STATE_IDLE = const(0x01)
    _STATE_RX = const(0x0D)
    _STATE_TX = const(0x13)
    _STATE_RXFIFO_OVERFLOW = const(0x11)
    _STATE_TXFIFO_UNDERFLOW = const(0x16)

    # ==================== 类级常量：寄存器地址别名（兼容旧 API） ====================
    IOCFG2 = _IOCFG2
    IOCFG1 = _IOCFG1
    IOCFG0 = _IOCFG0
    FIFOTHR = _FIFOTHR
    SYNC1 = _SYNC1
    SYNC0 = _SYNC0
    PKTLEN = _PKTLEN
    PKTCTRL1 = _PKTCTRL1
    PKTCTRL0 = _PKTCTRL0
    ADDR = _ADDR
    CHANNR = _CHANNR
    FSCTRL1 = _FSCTRL1
    FSCTRL0 = _FSCTRL0
    FREQ2 = _FREQ2
    FREQ1 = _FREQ1
    FREQ0 = _FREQ0
    MDMCFG4 = _MDMCFG4
    MDMCFG3 = _MDMCFG3
    MDMCFG2 = _MDMCFG2
    MDMCFG1 = _MDMCFG1
    MDMCFG0 = _MDMCFG0
    DEVIATN = _DEVIATN
    MCSM2 = _MCSM2
    MCSM1 = _MCSM1
    MCSM0 = _MCSM0
    FOCCFG = _FOCCFG
    BSCFG = _BSCFG
    AGCCTRL2 = _AGCCTRL2
    AGCCTRL1 = _AGCCTRL1
    AGCCTRL0 = _AGCCTRL0
    WOREVT1 = _WOREVT1
    WOREVT0 = _WOREVT0
    WORCTRL = _WORCTRL
    FREND1 = _FREND1
    FREND0 = _FREND0
    FSCAL3 = _FSCAL3
    FSCAL2 = _FSCAL2
    FSCAL1 = _FSCAL1
    FSCAL0 = _FSCAL0
    RCCTRL1 = _RCCTRL1
    RCCTRL0 = _RCCTRL0
    FSTEST = _FSTEST
    PTEST = _PTEST
    AGCTEST = _AGCTEST
    TEST2 = _TEST2
    TEST1 = _TEST1
    TEST0 = _TEST0
    SRES = _SRES
    SFSTXON = _SFSTXON
    SXOFF = _SXOFF
    SCAL = _SCAL
    SRX = _SRX
    STX = _STX
    SIDLE = _SIDLE
    SWOR = _SWOR
    SPWD = _SPWD
    SFRX = _SFRX
    SFTX = _SFTX
    SWORRST = _SWORRST
    SNOP = _SNOP
    PATABLE = _PATABLE
    TXFIFO = _TXFIFO
    RXFIFO = _RXFIFO
    PARTNUM = _PARTNUM
    VERSION = _VERSION
    FREQEST = _FREQEST
    LQI = _LQI
    RSSI = _RSSI
    MARCSTATE = _MARCSTATE
    WORTIME1 = _WORTIME1
    WORTIME0 = _WORTIME0
    PKTSTATUS = _PKTSTATUS
    VCO_VC_DAC = _VCO_VC_DAC
    TXBYTES = _TXBYTES
    RXBYTES = _RXBYTES
    RCCTRL1_STATUS = _RCCTRL1_STATUS
    RCCTRL0_STATUS = _RCCTRL0_STATUS
    STATE_IDLE = _STATE_IDLE
    STATE_RX = _STATE_RX
    STATE_TX = _STATE_TX
    STATE_RXFIFO_OVERFLOW = _STATE_RXFIFO_OVERFLOW
    STATE_TXFIFO_UNDERFLOW = _STATE_TXFIFO_UNDERFLOW

    # ==================== __init__ ====================

    def __init__(
        self,
        spi,
        cs: Pin,
        gdo0=None,
        crystal_hz: int = 26000000,
        reset: bool = True,
        debug: bool = False,
    ) -> None:
        """
        初始化 CC1101 SPI 收发器驱动实例
        Args:
            spi: SPI 总线实例（需提供 write() 和 write_readinto() 方法）
            cs (Pin): SPI 片选引脚实例（已初始化为输出模式）
            gdo0: GDO0 引脚实例（可选），用于中断或状态查询
            crystal_hz (int): 晶振频率（Hz），默认 26000000（26MHz）
            reset (bool): 是否在初始化时执行硬件复位，默认 True
            debug (bool): 是否启用调试日志输出，默认 False
        Returns:
            None
        Raises:
            TypeError: spi 缺少必要方法或 cs 不是有效的 Pin 实例
            ValueError: crystal_hz 参数值不合法
        Notes:
            - SPI 总线和控制引脚由外部创建并传入，不在此处创建
            - ISR-safe: 否（init 中执行硬件复位和 SPI 通信）
            - 副作用：若 reset=True 则执行芯片复位
        ==========================================
        Initialize CC1101 SPI transceiver driver instance.
        Args:
            spi: SPI bus instance (must provide write() and write_readinto() methods)
            cs (Pin): SPI chip select pin instance (initialized as output)
            gdo0: GDO0 pin instance (optional), for interrupt or status query
            crystal_hz (int): Crystal frequency in Hz, default 26000000 (26MHz)
            reset (bool): Perform hardware reset during init, default True
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            TypeError: spi lacks required methods or cs is not a valid Pin instance
            ValueError: crystal_hz has an invalid value
        Notes:
            - SPI bus and control pins are externally created and injected
            - ISR-safe: No (init performs hardware reset and SPI communication)
            - Side effects: Performs chip reset if reset=True
        """
        # ========== 参数校验 ==========
        if not hasattr(spi, "write") or not hasattr(spi, "write_readinto"):
            raise TypeError("spi must provide write() and write_readinto()")
        if not hasattr(cs, "value"):
            raise TypeError("cs must be a machine.Pin-like object")
        if crystal_hz <= 0:
            raise ValueError("crystal_hz must be positive")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        # ========== 保存硬件实例引用 ==========
        self._spi = spi
        self._cs = cs
        self._gdo0 = gdo0
        self._crystal_hz = crystal_hz
        self._debug = debug

        # ========== 预分配 I/O 缓冲区 ==========
        self._tx1 = bytearray(1)
        self._rx1 = bytearray(1)
        self._buf2 = bytearray(2)

        # ========== 初始化 SPI 片选 ==========
        self._cs.value(1)

        # ========== 执行硬件复位 ==========
        if reset:
            self.reset()

    # ==================== 公共方法：基础 SPI 操作 ====================

    def reset(self) -> None:
        """
        硬件复位 CC1101 芯片
        Notes:
            - 先拉低 CS 触发芯片复位时序，再发送 SRES 命令
            - ISR-safe: 否（包含 SPI I/O 和延时操作）
            - 副作用：芯片所有寄存器重置为默认值
        ==========================================
        Hardware reset the CC1101 chip.
        Notes:
            - Pulls CS low to trigger reset sequence, then sends SRES command
            - ISR-safe: No (contains SPI I/O and delay operations)
            - Side effects: All chip registers reset to default values
        """
        self._cs.value(1)
        sleep_us(5)
        self._cs.value(0)
        sleep_us(10)
        self._cs.value(1)
        sleep_us(45)
        self.strobe(self._SRES)
        sleep_ms(1)

    def strobe(self, command: int) -> int:
        """
        发送命令选通并读取状态字节
        Args:
            command (int): 命令字节（低 8 位有效）
        Returns:
            int: 芯片返回的状态字节
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - ISR-safe: 是（仅执行单次 SPI 传输，无内存分配）
            - 副作用：触发芯片状态机迁移
        ==========================================
        Send a command strobe and read status byte.
        Args:
            command (int): Command byte (lower 8 bits used)
        Returns:
            int: Status byte returned by chip
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - ISR-safe: Yes (single SPI transfer, no memory allocation)
            - Side effects: Triggers chip state machine transition
        """
        self._tx1[0] = command & 0xFF
        self._rx1[0] = 0
        self._cs.value(0)
        try:
            self._spi.write_readinto(self._tx1, self._rx1)
        except OSError as e:
            raise RuntimeError("SPI write_readinto failed for command 0x%02X" % command) from e
        finally:
            self._cs.value(1)
        return self._rx1[0]

    def read_reg(self, register: int) -> int:
        """
        读取单个配置寄存器
        Args:
            register (int): 寄存器地址（低 6 位有效）
        Returns:
            int: 寄存器值（0-255）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - ISR-safe: 否（分配临时缓冲区）
        ==========================================
        Read a single configuration register.
        Args:
            register (int): Register address (lower 6 bits used)
        Returns:
            int: Register value (0-255)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - ISR-safe: No (allocates temporary buffer)
        """
        self._buf2[0] = (register & 0x3F) | self._READ_SINGLE
        self._buf2[1] = 0
        rx = bytearray(2)
        self._cs.value(0)
        try:
            self._spi.write_readinto(self._buf2, rx)
        except OSError as e:
            raise RuntimeError("SPI read failed for register 0x%02X" % register) from e
        finally:
            self._cs.value(1)
        return rx[1]

    def write_reg(self, register: int, value: int) -> None:
        """
        写入单个配置寄存器
        Args:
            register (int): 寄存器地址（低 6 位有效）
            value (int): 待写入的值（低 8 位有效）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - ISR-safe: 否（SPI 阻塞写入）
            - 副作用：修改芯片配置寄存器
        ==========================================
        Write a single configuration register.
        Args:
            register (int): Register address (lower 6 bits used)
            value (int): Value to write (lower 8 bits used)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - ISR-safe: No (SPI blocking write)
            - Side effects: Modifies chip configuration register
        """
        self._buf2[0] = (register & 0x3F) | self._WRITE_SINGLE
        self._buf2[1] = value & 0xFF
        self._cs.value(0)
        try:
            self._spi.write(self._buf2)
        except OSError as e:
            raise RuntimeError("SPI write failed for register 0x%02X" % register) from e
        finally:
            self._cs.value(1)

    def read_burst(self, register: int, length: int) -> bytearray:
        """
        批量读取寄存器数据
        Args:
            register (int): 起始寄存器地址（低 6 位有效）
            length (int): 读取的字节数
        Returns:
            bytearray: 读取到的数据
        Raises:
            ValueError: length 为负数
            RuntimeError: SPI 通信失败
        Notes:
            - ISR-safe: 否（分配动态缓冲区）
        ==========================================
        Burst read multiple registers.
        Args:
            register (int): Start register address (lower 6 bits used)
            length (int): Number of bytes to read
        Returns:
            bytearray: Data read from registers
        Raises:
            ValueError: length is negative
            RuntimeError: SPI communication failed
        Notes:
            - ISR-safe: No (allocates dynamic buffer)
        """
        if length < 0:
            raise ValueError("length must be >= 0")
        tx = bytearray(length + 1)
        rx = bytearray(length + 1)
        tx[0] = (register & 0x3F) | self._READ_BURST
        self._cs.value(0)
        try:
            self._spi.write_readinto(tx, rx)
        except OSError as e:
            raise RuntimeError("SPI burst read failed for register 0x%02X len=%d" % (register, length)) from e
        finally:
            self._cs.value(1)
        return rx[1:]

    def write_burst(self, register: int, data) -> None:
        """
        批量写入寄存器数据
        Args:
            register (int): 起始寄存器地址（低 6 位有效）
            data: 待写入的数据（bytes 或可迭代的字节序列）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - ISR-safe: 否（分配动态缓冲区）
            - 副作用：修改多个芯片寄存器
        ==========================================
        Burst write multiple registers.
        Args:
            register (int): Start register address (lower 6 bits used)
            data: Data to write (bytes or iterable byte sequence)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - ISR-safe: No (allocates dynamic buffer)
            - Side effects: Modifies multiple chip registers
        """
        payload = bytes(data)
        tx = bytearray(len(payload) + 1)
        tx[0] = (register & 0x3F) | self._WRITE_BURST
        tx[1:] = payload
        self._cs.value(0)
        try:
            self._spi.write(tx)
        except OSError as e:
            raise RuntimeError("SPI burst write failed for register 0x%02X len=%d" % (register, len(payload))) from e
        finally:
            self._cs.value(1)

    # ==================== 公共方法：状态寄存器读取 ====================

    def read_status_reg(self, register: int) -> int:
        """
        读取状态寄存器（使用 Burst 读取方式）
        Args:
            register (int): 状态寄存器地址（低 6 位有效）
        Returns:
            int: 状态寄存器值（0-255）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 状态寄存器与配置寄存器共享地址空间，但使用不同的访问方式
            - ISR-safe: 否（分配临时缓冲区）
        ==========================================
        Read a status register (using burst read mode).
        Args:
            register (int): Status register address (lower 6 bits used)
        Returns:
            int: Status register value (0-255)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Status registers share address space with config registers
            - ISR-safe: No (allocates temporary buffer)
        """
        self._buf2[0] = (register & 0x3F) | self._READ_BURST
        self._buf2[1] = 0
        rx = bytearray(2)
        self._cs.value(0)
        try:
            self._spi.write_readinto(self._buf2, rx)
        except OSError as e:
            raise RuntimeError("SPI status read failed for register 0x%02X" % register) from e
        finally:
            self._cs.value(1)
        return rx[1]

    # ==================== 公共方法：设备信息查询 ====================

    def partnum(self) -> int:
        """
        读取芯片部件号
        Returns:
            int: 部件号（0x00-0xFF）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 正常情况下 CC1101 应返回 0x00
            - 0xFF 表示 SPI 通信异常或芯片未连接
        ==========================================
        Read the chip part number.
        Returns:
            int: Part number (0x00-0xFF)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - CC1101 should normally return 0x00
            - 0xFF indicates SPI communication error or chip not connected
        """
        return self.read_status_reg(self._PARTNUM)

    def version(self) -> int:
        """
        读取芯片版本号
        Returns:
            int: 版本号（0x00-0xFF）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 0x00 或 0xFF 表示 SPI 通信异常或芯片未连接
        ==========================================
        Read the chip version number.
        Returns:
            int: Version number (0x00-0xFF)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - 0x00 or 0xFF indicates SPI communication error or chip not connected
        """
        return self.read_status_reg(self._VERSION)

    def marcstate(self) -> int:
        """
        读取主无线电控制状态机当前状态
        Returns:
            int: MARCSTATE 值（低 5 位有效，0x00-0x1F）
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Read the Main Radio Control state machine status.
        Returns:
            int: MARCSTATE value (lower 5 bits, 0x00-0x1F)
        Raises:
            RuntimeError: SPI communication failed
        """
        return self.read_status_reg(self._MARCSTATE) & 0x1F

    def rssi_raw(self) -> int:
        """
        读取 RSSI 原始值
        Returns:
            int: RSSI 原始值（0x00-0xFF）
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Read raw RSSI value.
        Returns:
            int: Raw RSSI value (0x00-0xFF)
        Raises:
            RuntimeError: SPI communication failed
        """
        return self.read_status_reg(self._RSSI)

    def rssi_dbm(self) -> int:
        """
        计算 RSSI 值（dBm）
        Returns:
            int: RSSI 值（dBm）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 根据 CC1101 数据手册 RSSI 计算公式转换
            - 原始值 >= 128 时为负值（需要符号扩展）
        ==========================================
        Calculate RSSI value in dBm.
        Returns:
            int: RSSI value in dBm
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Converted using CC1101 datasheet RSSI formula
            - Raw values >= 128 represent negative values (sign extension)
        """
        raw = self.rssi_raw()
        if raw >= 128:
            return ((raw - 256) // 2) - 74
        return (raw // 2) - 74

    def available(self) -> int:
        """
        查询 RX FIFO 中可读取的字节数
        Returns:
            int: 可读取的字节数（0-127）
        Raises:
            RuntimeError: RX FIFO 溢出或 SPI 通信失败
        Notes:
            - 最高位为 1 时表示 RX FIFO 溢出，自动执行 FIFO 刷新
            - 调用 flush_rx() 后芯片进入空闲模式
        ==========================================
        Query number of bytes available in RX FIFO.
        Returns:
            int: Number of bytes available (0-127)
        Raises:
            RuntimeError: RX FIFO overflow or SPI communication failed
        Notes:
            - MSB set indicates RX FIFO overflow, triggers automatic flush
            - After flush_rx() the chip enters idle mode
        """
        value = self.read_status_reg(self._RXBYTES)
        if value & 0x80:
            self.flush_rx()
            raise RuntimeError("CC1101 RX FIFO overflow")
        return value & 0x7F

    def tx_bytes(self) -> int:
        """
        查询 TX FIFO 中待发送的字节数
        Returns:
            int: TX FIFO 中的字节数（0-127）
        Raises:
            RuntimeError: TX FIFO 下溢或 SPI 通信失败
        Notes:
            - 最高位为 1 时表示 TX FIFO 下溢，自动执行 FIFO 刷新
        ==========================================
        Query number of bytes in TX FIFO.
        Returns:
            int: Number of bytes in TX FIFO (0-127)
        Raises:
            RuntimeError: TX FIFO underflow or SPI communication failed
        Notes:
            - MSB set indicates TX FIFO underflow, triggers automatic flush
        """
        value = self.read_status_reg(self._TXBYTES)
        if value & 0x80:
            self.flush_tx()
            raise RuntimeError("CC1101 TX FIFO underflow")
        return value & 0x7F

    # ==================== 公共方法：芯片验证 ====================

    def verify(self) -> tuple:
        """
        验证芯片身份（部件号和版本号）
        Returns:
            tuple: (partnum, version) 二者均为 int
        Raises:
            RuntimeError: 身份验证失败或 SPI 通信失败
        Notes:
            - 若部件号为 0xFF 或版本号为 0x00/0xFF，表示芯片未正确连接或响应
            - 在依赖驱动中作为 SPI 设备检测手段
        ==========================================
        Verify chip identity (part number and version).
        Returns:
            tuple: (partnum, version), both int
        Raises:
            RuntimeError: Identity check failed or SPI communication failed
        Notes:
            - 0xFF partnum or 0x00/0xFF version indicates chip not properly connected
            - Used as SPI device presence check in dependent drivers
        """
        part = self.partnum()
        ver = self.version()
        if part == 0xFF or ver in (0x00, 0xFF):
            raise RuntimeError("CC1101 identity check failed part=0x%02X version=0x%02X" % (part, ver))
        return part, ver

    # ==================== 公共方法：芯片配置 ====================

    def configure(self, registers) -> None:
        """
        批量配置寄存器
        Args:
            registers: 寄存器配置（dict 或 (register, value) 可迭代对象）
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：批量修改芯片寄存器
        ==========================================
        Batch configure registers.
        Args:
            registers: Register configuration (dict or iterable of (register, value) pairs)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Batch modifies chip registers
        """
        if isinstance(registers, dict):
            items = registers.items()
        else:
            items = registers
        for register, value in items:
            self.write_reg(register, value)

    def set_frequency(self, freq_hz: int) -> None:
        """
        设置载波频率
        Args:
            freq_hz (int): 目标频率（Hz）
        Notes:
            - 频率字计算公式：FREQ = freq_hz * 2^16 / crystal_hz
            - 写入 FREQ2、FREQ1、FREQ0 三个寄存器
            - ISR-safe: 否
            - 副作用：修改频率寄存器
        ==========================================
        Set carrier frequency.
        Args:
            freq_hz (int): Target frequency in Hz
        Notes:
            - Frequency word formula: FREQ = freq_hz * 2^16 / crystal_hz
            - Writes to FREQ2, FREQ1, FREQ0 registers
            - ISR-safe: No
            - Side effects: Modifies frequency registers
        """
        freq_word = int((int(freq_hz) << 16) // self._crystal_hz)
        self.write_reg(self._FREQ2, (freq_word >> 16) & 0xFF)
        self.write_reg(self._FREQ1, (freq_word >> 8) & 0xFF)
        self.write_reg(self._FREQ0, freq_word & 0xFF)

    def set_packet_length(self, length: int) -> None:
        """
        设置数据包长度（固定长度模式）
        Args:
            length (int): 数据包长度（0-255）
        Raises:
            ValueError: 长度超出范围
        Notes:
            - ISR-safe: 否
            - 副作用：修改 PKTLEN 寄存器
        ==========================================
        Set packet length (fixed length mode).
        Args:
            length (int): Packet length (0-255)
        Raises:
            ValueError: Length out of range
        Notes:
            - ISR-safe: No
            - Side effects: Modifies PKTLEN register
        """
        if not 0 <= length <= 255:
            raise ValueError("packet length must be in 0..255")
        self.write_reg(self._PKTLEN, length)

    def set_pa_table(self, values) -> None:
        """
        设置功率放大器功率表（PATABLE）
        Args:
            values: 功率值列表（1-8 个字节）
        Raises:
            ValueError: 功率表为空或超过 8 个值
        Notes:
            - PATABLE 包含 1-8 个功率设置值，用于功率斜坡控制
            - ISR-safe: 否
            - 副作用：修改 PATABLE 寄存器
        ==========================================
        Set Power Amplifier table (PATABLE).
        Args:
            values: Power value list (1-8 bytes)
        Raises:
            ValueError: PA table empty or exceeds 8 values
        Notes:
            - PATABLE holds 1-8 power settings for power ramping
            - ISR-safe: No
            - Side effects: Modifies PATABLE register
        """
        if not values:
            raise ValueError("PA table must contain at least one value")
        if len(values) > 8:
            raise ValueError("PA table can contain at most 8 values")
        self.write_burst(self._PATABLE, values)

    # ==================== 公共方法：模式控制 ====================

    def idle(self) -> None:
        """
        进入空闲模式
        Notes:
            - ISR-safe: 否
            - 副作用：停止当前收发操作，进入空闲状态
        ==========================================
        Enter idle mode.
        Notes:
            - ISR-safe: No
            - Side effects: Stops current TX/RX and enters idle state
        """
        self.strobe(self._SIDLE)

    def rx(self) -> None:
        """
        进入接收模式
        Notes:
            - ISR-safe: 否
            - 副作用：开启接收状态机
        ==========================================
        Enter receive mode.
        Notes:
            - ISR-safe: No
            - Side effects: Starts receive state machine
        """
        self.strobe(self._SRX)

    def tx(self) -> None:
        """
        进入发送模式
        Notes:
            - ISR-safe: 否
            - 副作用：开启发送状态机
        ==========================================
        Enter transmit mode.
        Notes:
            - ISR-safe: No
            - Side effects: Starts transmit state machine
        """
        self.strobe(self._STX)

    def power_down(self) -> None:
        """
        进入掉电模式
        Notes:
            - 先进入空闲模式再发送 SPWD 命令
            - ISR-safe: 否
            - 副作用：芯片进入最低功耗状态
        ==========================================
        Enter power-down mode.
        Notes:
            - Enters idle mode first, then sends SPWD command
            - ISR-safe: No
            - Side effects: Chip enters lowest power state
        """
        self.idle()
        self.strobe(self._SPWD)

    def flush_rx(self) -> None:
        """
        刷新 RX FIFO 缓冲区
        Notes:
            - 先进入空闲模式再发送 SFRX 命令
            - ISR-safe: 否
            - 副作用：清除 RX FIFO
        ==========================================
        Flush RX FIFO buffer.
        Notes:
            - Enters idle mode first, then sends SFRX command
            - ISR-safe: No
            - Side effects: Clears RX FIFO
        """
        self.idle()
        self.strobe(self._SFRX)

    def flush_tx(self) -> None:
        """
        刷新 TX FIFO 缓冲区
        Notes:
            - 先进入空闲模式再发送 SFTX 命令
            - ISR-safe: 否
            - 副作用：清除 TX FIFO
        ==========================================
        Flush TX FIFO buffer.
        Notes:
            - Enters idle mode first, then sends SFTX command
            - ISR-safe: No
            - Side effects: Clears TX FIFO
        """
        self.idle()
        self.strobe(self._SFTX)

    # ==================== 公共方法：状态等待 ====================

    def wait_for_state(self, state: int, timeout_ms: int = 1000) -> bool:
        """
        等待芯片进入指定状态
        Args:
            state (int): 目标状态值（MARCSTATE 低 5 位）
            timeout_ms (int): 超时时间（毫秒），默认 1000
        Returns:
            bool: True 表示进入目标状态
        Raises:
            RuntimeError: 超时或 FIFO 异常
        Notes:
            - ISR-safe: 否（包含轮询循环）
            - 自动检测并处理 RX/TX FIFO 溢出/下溢
        ==========================================
        Wait for chip to enter specified state.
        Args:
            state (int): Target state value (MARCSTATE lower 5 bits)
            timeout_ms (int): Timeout in milliseconds, default 1000
        Returns:
            bool: True if target state reached
        Raises:
            RuntimeError: Timeout or FIFO exception
        Notes:
            - ISR-safe: No (contains polling loop)
            - Automatically detects and handles RX/TX FIFO overflow/underflow
        """
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            current = self.marcstate()
            if current == state:
                return True
            if current == self._STATE_RXFIFO_OVERFLOW:
                self.flush_rx()
                raise RuntimeError("CC1101 RX FIFO overflow detected in wait_for_state")
            if current == self._STATE_TXFIFO_UNDERFLOW:
                self.flush_tx()
                raise RuntimeError("CC1101 TX FIFO underflow detected in wait_for_state")
            sleep_ms(2)
        raise RuntimeError("CC1101 state timeout waiting for 0x%02X" % state)

    # ==================== 公共方法：数据收发 ====================

    def send_packet(
        self,
        payload,
        timeout_ms: int = 1000,
        variable_length: bool = True,
    ) -> None:
        """
        发送数据包
        Args:
            payload: 待发送的数据（bytes 或可迭代字节序列）
            timeout_ms (int): 发送完成超时时间（毫秒），默认 1000
            variable_length (bool): 是否使用可变长度模式（首字节为长度），默认 True
        Raises:
            ValueError: 可变长度模式下 payload 超过 255 字节
            RuntimeError: 发送超时或 SPI 通信失败
        Notes:
            - 可变长度模式：首字节自动加入长度信息
            - 固定长度模式：直接发送数据，需事先通过 set_packet_length() 配置长度
            - ISR-safe: 否
            - 副作用：刷新 TX FIFO、写入 FIFO、切换为发送模式
        ==========================================
        Send a data packet.
        Args:
            payload: Data to send (bytes or iterable byte sequence)
            timeout_ms (int): Send completion timeout in milliseconds, default 1000
            variable_length (bool): Use variable length mode (first byte = length), default True
        Raises:
            ValueError: Payload exceeds 255 bytes in variable length mode
            RuntimeError: Send timeout or SPI communication failed
        Notes:
            - Variable length mode: First byte auto-prepended with length
            - Fixed length mode: Direct send, must pre-configure via set_packet_length()
            - ISR-safe: No
            - Side effects: Flushes TX FIFO, writes FIFO, switches to TX mode
        """
        data = bytes(payload)
        if variable_length:
            if len(data) > 255:
                raise ValueError("variable length payload must be <= 255 bytes")
            fifo = bytes([len(data)]) + data
        else:
            fifo = data
        self.idle()
        self.flush_tx()
        self.write_burst(self._TXFIFO, fifo)
        self.tx()
        self.wait_for_state(self._STATE_IDLE, timeout_ms)

    def read_packet(self, timeout_ms: int = 0, with_status: bool = False):
        """
        读取接收到的数据包
        Args:
            timeout_ms (int): 等待超时时间（毫秒），0 表示非阻塞立即返回
            with_status (bool): 是否返回附加状态字节，默认 False
        Returns:
            bytes 或 None: 接收到的数据负载，超时返回 None
            若 with_status=True 则返回 (payload, status_bytes) 元组
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 非阻塞模式（timeout_ms=0）：若无数据立即返回 None
            - 阻塞模式（timeout_ms>0）：等待直到收到数据或超时
            - ISR-safe: 否（包含轮询循环和动态缓冲区分配）
            - 副作用：读取 FIFO 内容
        ==========================================
        Read a received data packet.
        Args:
            timeout_ms (int): Wait timeout in milliseconds, 0 = non-blocking
            with_status (bool): Return additional status bytes, default False
        Returns:
            bytes or None: Received payload, None on timeout
            If with_status=True returns (payload, status_bytes) tuple
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Non-blocking (timeout_ms=0): Returns None immediately if no data
            - Blocking (timeout_ms>0): Waits until data received or timeout
            - ISR-safe: No (contains polling loop and dynamic buffer allocation)
            - Side effects: Reads FIFO content
        """
        start = ticks_ms()
        while self.available() == 0:
            if timeout_ms <= 0 or ticks_diff(ticks_ms(), start) >= timeout_ms:
                return None
            sleep_ms(2)

        length = self.read_burst(self._RXFIFO, 1)[0]
        if length == 0:
            return b""
        total = length + (2 if with_status else 0)
        raw = self.read_burst(self._RXFIFO, total)
        payload = bytes(raw[:length])
        if not with_status:
            return payload
        return payload, raw[length:]

    # ==================== @property ====================

    # ==================== 私有方法 ====================

    def _log(self, msg: str) -> None:
        """
        条件调试日志输出
        Args:
            msg (str): 日志消息
        ==========================================
        Conditional debug log output.
        Args:
            msg (str): Log message
        """
        if self._debug:
            print("[CC1101] %s" % msg)

    def deinit(self) -> None:
        """
        释放硬件资源
        Notes:
            - 将芯片置为掉电模式
            - 释放 SPI 片选引脚（拉高）
            - 清除总线实例引用
            - 不影响外部传入的 SPI 和 Pin 实例
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Notes:
            - Puts chip in power-down mode
            - Releases SPI chip select pin (set high)
            - Clears bus instance references
            - Does not affect externally provided SPI and Pin instances
            - ISR-safe: No
        """
        try:
            self.power_down()
        except Exception:
            pass
        if self._cs is not None:
            try:
                self._cs.value(1)
            except Exception:
                pass
        self._spi = None
        self._cs = None
        self._gdo0 = None
        self._log("deinitialized")


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
