# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : sx1276.py
# @Description : SX1276 LoRa 射频收发器驱动，通过 SPI 接口实现数据包的发送与接收
# @License : MIT

import micropython

micropython.alloc_emergency_exception_buf(100)

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SPI
from micropython import const
import struct

try:
    import random
except ImportError:
    import urandom as random

# ======================================== 全局变量 ============================================

# SPI 读写复用缓冲区
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class SX1276:
    """
    SX1276 LoRa 射频收发器驱动类
    Attributes:
        src_id (int): 发送者 ID
        is_available (bool): 设备空闲标志，Tx 或 RxCont 完成后置 True
        _spi (SPI): SPI 总线实例
        _cs_pin (Pin): SPI 片选引脚
        _rst_pin (Pin): 复位引脚
    Methods:
        send(): 发送数据包
        spi_write(): 通过 SPI 写入寄存器
        spi_read(): 通过 SPI 读取寄存器
        read_fifo(): 读取接收 FIFO 缓冲区
        write_fifo(): 写入发送 FIFO 缓冲区
        set_freq(): 设置当前跳频通道频率
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 SPI 实例和 Pin 实例，不在内部创建总线对象
        - DIO0/DIO1 中断由内部的 _irq_handler 处理
        - 可通过重写 req_packet_handler/brd_packet_handler/after_TxDone 定制回调行为
        - 支持 FHSS 跳频扩频，列表长度为 1 时关闭跳频功能
    ==========================================
    SX1276 LoRa radio transceiver driver.
    Attributes:
        src_id (int): Sender ID
        is_available (bool): Device idle flag, set True after Tx or RxCont completes
        _spi (SPI): SPI bus instance
        _cs_pin (Pin): SPI chip select pin
        _rst_pin (Pin): Reset pin
    Methods:
        send(): Send a data packet
        spi_write(): Write to a register via SPI
        spi_read(): Read from a register via SPI
        read_fifo(): Read the receive FIFO buffer
        write_fifo(): Write to the transmit FIFO buffer
        set_freq(): Set frequency for current FHSS channel
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided SPI and Pin instances
        - DIO0/DIO1 interrupts handled by internal _irq_handler
        - Override req_packet_handler/brd_packet_handler/after_TxDone for custom callbacks
        - FHSS frequency hopping supported; single-element list disables hopping
    """

    # ==================== 类级常量：寄存器地址 ====================
    _REG_FIFO = const(0x00)
    _REG_OP_MODE = const(0x01)
    _REG_FRF_MSB = const(0x06)
    _REG_FRF_MID = const(0x07)
    _REG_FRF_LSB = const(0x08)
    _REG_PA_CONFIG = const(0x09)
    _REG_FIFO_ADDR_PTR = const(0x0D)
    _REG_FIFO_TX_BASE_ADDR = const(0x0E)
    _REG_FIFO_RX_BASE_ADDR = const(0x0F)
    _REG_FIFO_RX_CURRENT_ADDR = const(0x10)
    _REG_IRQ_FLAGS = const(0x12)
    _REG_RX_NB_BYTES = const(0x13)
    _REG_PKT_SNR_VALUE = const(0x19)
    _REG_PKT_RSSI_VALUE = const(0x1A)
    _REG_RSSI_VALUE = const(0x1B)
    _REG_HOP_CHANNEL = const(0x1C)
    _REG_MODEM_CONFIG1 = const(0x1D)
    _REG_MODEM_CONFIG2 = const(0x1E)
    _REG_PREAMBLE_MSB = const(0x20)
    _REG_PREAMBLE_LSB = const(0x21)
    _REG_PAYLOAD_LENGTH = const(0x22)
    _REG_HOP_PERIOD = const(0x24)
    _REG_MODEM_CONFIG3 = const(0x26)
    _REG_DIO_MAPPING1 = const(0x40)
    _REG_VERSION = const(0x42)
    _REG_PA_DAC = const(0x4D)

    # ==================== 类级常量：寄存器映射字典 ====================
    _REG_TABLE = {
        "RegFifo": _REG_FIFO,
        "RegOpMode": _REG_OP_MODE,
        "RegFrfMsb": _REG_FRF_MSB,
        "RegFrfMid": _REG_FRF_MID,
        "RegFrfLsb": _REG_FRF_LSB,
        "RegPaConfig": _REG_PA_CONFIG,
        "RegFifoTxBaseAddr": _REG_FIFO_TX_BASE_ADDR,
        "RegFifoRxBaseAddr": _REG_FIFO_RX_BASE_ADDR,
        "RegFifoAddrPtr": _REG_FIFO_ADDR_PTR,
        "RegFifoRxCurrentAddr": _REG_FIFO_RX_CURRENT_ADDR,
        "RegIrqFlags": _REG_IRQ_FLAGS,
        "RegRxNbBytes": _REG_RX_NB_BYTES,
        "RegPktSnrValue": _REG_PKT_SNR_VALUE,
        "RegPktRssiValue": _REG_PKT_RSSI_VALUE,
        "RegRssiValue": _REG_RSSI_VALUE,
        "RegHopChannel": _REG_HOP_CHANNEL,
        "RegModemConfig1": _REG_MODEM_CONFIG1,
        "RegModemConfig2": _REG_MODEM_CONFIG2,
        "RegPreambleMsb": _REG_PREAMBLE_MSB,
        "RegPreambleLsb": _REG_PREAMBLE_LSB,
        "RegPayloadLength": _REG_PAYLOAD_LENGTH,
        "RegHopPeriod": _REG_HOP_PERIOD,
        "RegModemConfig3": _REG_MODEM_CONFIG3,
        "RegDioMapping1": _REG_DIO_MAPPING1,
        "RegVersion": _REG_VERSION,
        "RegPaDac": _REG_PA_DAC,
    }

    # ==================== 类级常量：工作模式 ====================
    # 参见数据手册 Table 16: LoRa Operating Mode Functionality
    MODE_SLEEP = const(0b000)
    MODE_STANDBY = const(0b001)
    MODE_TX = const(0b011)
    MODE_RXCONTINUOUS = const(0b101)
    MODE_RXSINGLE = const(0b110)
    MODE_CAD = const(0b111)

    MODE = {
        "SLEEP": MODE_SLEEP,
        "STANDBY": MODE_STANDBY,
        "TX": MODE_TX,
        "RXCONTINUOUS": MODE_RXCONTINUOUS,
        "RXSINGLE": MODE_RXSINGLE,
        "CAD": MODE_CAD,
    }

    # ==================== 类级常量：数据包类型 ====================
    # REQ：发送者请求接收方回复 ACK
    # ACK：接收方发送确认应答
    # BRD：广播包，不需要应答
    PKT_TYPE_REQ = const(0)
    PKT_TYPE_ACK = const(1)
    PKT_TYPE_BRD = const(2)

    PKT_TYPE = {
        "REQ": PKT_TYPE_REQ,
        "ACK": PKT_TYPE_ACK,
        "BRD": PKT_TYPE_BRD,
    }

    # ==================== 类级常量：中断标志位 ====================
    _IRQ_RX_TIMEOUT = const(0b1 << 7)
    _IRQ_RX_DONE = const(0b1 << 6)
    _IRQ_PAYLOAD_CRC_ERROR = const(0b1 << 5)
    _IRQ_VALID_HEADER = const(0b1 << 4)
    _IRQ_TX_DONE = const(0b1 << 3)
    _IRQ_CAD_DONE = const(0b1 << 2)
    _IRQ_FHSS_CHANGE_CHANNEL = const(0b1 << 1)
    _IRQ_CAD_DETECTED = const(0b1 << 0)

    _IRQ_FLAGS = {
        "RxTimeout": _IRQ_RX_TIMEOUT,
        "RxDone": _IRQ_RX_DONE,
        "PayloadCrcError": _IRQ_PAYLOAD_CRC_ERROR,
        "ValidHeader": _IRQ_VALID_HEADER,
        "TxDone": _IRQ_TX_DONE,
        "CadDone": _IRQ_CAD_DONE,
        "FhssChangeChannel": _IRQ_FHSS_CHANGE_CHANNEL,
        "CadDetected": _IRQ_CAD_DETECTED,
    }

    # ==================== 类级常量：硬件参数 ====================
    # 晶振频率
    _FXOSC = 32000000.0
    # 频率步进值
    # 2**19
    _FSTEP = _FXOSC / const(524288)
    # FIFO 缓冲区起始地址
    _FIFO_BOTTOM = const(0x00)
    # 数据包头格式
    _HEADER_FMT = "HHHH"
    _HEADER_SIZE = const(8)

    def __init__(
        self,
        spi: SPI,
        cs_pin: Pin,
        rst_pin: Pin,
        dio0_pin: Pin,
        dio1_pin: Pin,
        src_id: int,
        fhss_list: list,
        plus20dBm: bool = False,
        debug: bool = False,
    ) -> None:
        """
        初始化 SX1276 LoRa 驱动实例
        Args:
            spi (SPI): SPI 总线实例（外部创建，需配置为 baudrate=10_000_000, polarity=0, phase=0）
            cs_pin (Pin): SPI 片选引脚实例（已初始化为输出模式）
            rst_pin (Pin): 复位引脚实例（已初始化为输出模式）
            dio0_pin (Pin): DIO0 中断引脚实例（已初始化为输入模式）
            dio1_pin (Pin): DIO1 中断引脚实例（已初始化为输入模式）
            src_id (int): 发送者 ID
            fhss_list (list): 跳频频率列表（Hz），单元素列表关闭跳频
            plus20dBm (bool): 是否启用 +20dBm 功率增强，默认 False
            debug (bool): 是否启用调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: 参数类型不正确
            RuntimeError: LoRa 初始化失败
        Notes:
            - SPI 必须配置为 mode 0（polarity=0, phase=0），最高 10MHz
            - ISR-safe: 否（init 中执行硬件复位和 SPI 通信）
        ==========================================
        Initialize SX1276 LoRa driver instance.
        Args:
            spi (SPI): SPI bus instance (externally created, must be baudrate=10_000_000, polarity=0, phase=0)
            cs_pin (Pin): SPI chip select pin instance (initialized as output)
            rst_pin (Pin): Reset pin instance (initialized as output)
            dio0_pin (Pin): DIO0 interrupt pin instance (initialized as input)
            dio1_pin (Pin): DIO1 interrupt pin instance (initialized as input)
            src_id (int): Sender ID
            fhss_list (list): FHSS frequency list in Hz (single element disables hopping)
            plus20dBm (bool): Enable +20dBm power boost, default False
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: LoRa initialization failed
        Notes:
            - SPI must be configured for mode 0 (polarity=0, phase=0), max 10MHz
            - ISR-safe: No (init performs hardware reset and SPI communication)
        """
        # ========== 参数校验 ==========
        if not hasattr(spi, "write"):
            raise ValueError("spi must be an SPI instance")
        if not isinstance(cs_pin, Pin):
            raise ValueError("cs_pin must be a Pin instance")
        if not isinstance(rst_pin, Pin):
            raise ValueError("rst_pin must be a Pin instance")
        if not isinstance(dio0_pin, Pin):
            raise ValueError("dio0_pin must be a Pin instance")
        if not isinstance(dio1_pin, Pin):
            raise ValueError("dio1_pin must be a Pin instance")
        if not isinstance(src_id, int):
            raise ValueError("src_id must be int, got %s" % type(src_id))
        if not isinstance(fhss_list, list):
            raise ValueError("fhss_list must be list, got %s" % type(fhss_list))
        if len(fhss_list) == 0:
            raise ValueError("fhss_list must not be empty")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        # ========== 保存硬件实例引用 ==========
        self._spi = spi
        self._cs_pin = cs_pin
        self._rst_pin = rst_pin
        self._dio0_pin = dio0_pin
        self._dio1_pin = dio1_pin

        # ========== 公共属性 ==========
        self.src_id = src_id

        # ========== 内部状态 ==========
        self._pkt_id = 0
        self._pkt_type = 0
        self._mode = None
        self._fhss_list = fhss_list
        self._debug = debug
        self.is_available = False
        self._irq_pending = False

        # #####################################
        # #  1. 复位调制解调器                #
        # #####################################
        # 拉低复位引脚至少 10ms 后拉高
        self._rst_pin.off()
        time.sleep(0.01)
        self._rst_pin.on()
        time.sleep(0.01)

        # #########################################
        # #  2. 初始化 SPI 通信                    #
        # #########################################
        # Tx：调制解调器的无线发送，Rx：接收
        # 调制解调器通过 SPI 接口与我们通信，受我们控制执行 Tx/Rx 操作
        # 首先拉高 CS 以禁用 SPI 通信，确保 Tx/Rx 操作仅在我们需要时发生
        self._cs_pin.on()

        # #####################################
        # #  3. LoRa 配置                     #
        # #####################################
        # 选择 LoRa 模式和测试读写函数
        # 选择 LoRa 模式（而非 FSK），并将模块置为休眠模式
        LongRangeMode = 0b1
        self.spi_write("RegOpMode", self.MODE["SLEEP"] | LongRangeMode << 7)
        # 验证读取功能
        if self.spi_read("RegOpMode") != (self.MODE["SLEEP"] | LongRangeMode << 7):
            raise RuntimeError("LoRa initialization failed")

        # 配置调制解调器参数：带宽、编码率、报头模式、扩频因子、CRC 等
        # 参见数据手册 4.4. LoRa Mode Register Map
        Bw = {"125KHz": 0b0111, "500kHz": 0b1001}
        CodingRate = {5: 0b001, 6: 0b010, 7: 0b011, 8: 0b100}
        ImplicitHeaderModeOn = {"Implicit": 0b1, "Explicit": 0b0}
        self.spi_write("RegModemConfig1", Bw["125KHz"] << 4 | CodingRate[5] << 1 | ImplicitHeaderModeOn["Explicit"])

        SpreadingFactor = {7: 0x7, 9: 0x9, 10: 0xA, 12: 0xC}
        TxContinuousMode = {"normal": 0b0, "continuous": 0b1}
        RxPayloadCrcOn = {"disable": 0b0, "enable": 0b1}
        # 配置扩频因子 10、正常发送模式、CRC 校验开启
        self.spi_write("RegModemConfig2", SpreadingFactor[10] << 4 | TxContinuousMode["normal"] << 3 | RxPayloadCrcOn["enable"] << 2 | 0x00)

        LowDataRateOptimize = {"Disabled": 0b0, "Enabled": 0b1}
        AgcAutoOn = {"register LnaGain": 0b0, "internal AGC loop": 0b1}
        self.spi_write("RegModemConfig3", LowDataRateOptimize["Enabled"] << 3 | AgcAutoOn["internal AGC loop"] << 2)

        # 前导码长度：使用 8 字节前导码
        self.spi_write("RegPreambleMsb", 0x0)
        self.spi_write("RegPreambleLsb", 0x8)

        # ========== FHSS 跳频配置 ==========
        # SX1276 芯片如何跳频？
        # 首先，两个 SX1276 芯片预先分配相同的频率序列（FHSS_list）
        # 发送方被配置为由 TxDone 和 FhssChangeChannel 触发中断
        # 接收方被配置为由 RxDone 和 FhssChangeChannel 触发中断
        # 当芯片在每个频率信道上停留足够时间（dwell time）后，FhssChangeChannel 中断被触发
        # 在 FhssChangeChannel 中断处理函数中设置新频率（FHSS_list 中的下一个元素）
        # 跳完足够多的信道后，Tx/Rx 完成，TxDone/RxDone 被触发
        #
        # 符号周期：Tsym = 2^SF / BW（如 SF=10, BW=125kHz → Tsym=8.192ms）
        # FCC 允许每个信道最多停留 400ms，因此至少每 48 个符号跳一次
        # HoppingPeriod（每个频率上的停留时间）= FreqHoppingPeriod * Tsym
        # 以下代码配置每 20 个符号跳频一次
        FreqHoppingPeriod = 20
        # 当只提供一个频率时，关闭 FHSS 跳频功能
        if len(fhss_list) == 1:
            FreqHoppingPeriod = 0
        self.spi_write("RegHopPeriod", FreqHoppingPeriod)

        # ========== 频率配置 ==========
        # 参见数据手册 4.1.4. Frequency Settings
        # 设置频率值 Frf = 目标频率 / FSTEP

        # ========== 输出功率配置 ==========
        # 使用 PA_BOOST 作为功率放大器，可输出 +2 ~ +17dBm 连续功率或最高 20dBm 峰值功率
        PaSelect = {"PA_BOOST": 0b1, "RFO": 0b0}
        MaxPower = {"15dBm": 0x7, "13dBm": 0x2}
        OutputPower = {"17dBm": 0xF, "2dBm": 0x0}
        self.spi_write("RegPaConfig", PaSelect["PA_BOOST"] << 7 | MaxPower["15dBm"] << 4 | OutputPower["2dBm"])

        # 启用 PA_BOOST 引脚的 +20dBm 选项
        if plus20dBm:
            PaDac = {"default": 0x04, "enable_PA_BOOST": 0x07}
            self.spi_write("RegPaDac", PaDac["enable_PA_BOOST"])

        # ========== FIFO 数据缓冲区配置 ==========
        # SX1276 有 256 字节的 FIFO 缓冲区用于 Tx/Rx 操作
        # 由于 SX1276 工作在半双工模式，将 Tx 和 Rx 基地址都设置为底部（0x00）
        # 以便在发送或接收时可以缓冲最多 256 字节的数据
        self.spi_write("RegFifoTxBaseAddr", self._FIFO_BOTTOM)
        self.spi_write("RegFifoRxBaseAddr", self._FIFO_BOTTOM)

        # #####################################
        # #  4. 中断配置                      #
        # #####################################
        # DIO 映射配置：
        # Dio0：TxDone/RxDone → 发送/接收完成中断
        # Dio1：FhssChangeChannel → 跳频信道切换中断
        _DIO_MAP_DIO0_TX_DONE = const(0b01 << 6)
        _DIO_MAP_DIO0_RX_DONE = const(0b00 << 6)
        _DIO_MAP_DIO1_FHSS = const(0b01 << 4)
        _DIO_MAP_TX = _DIO_MAP_DIO0_TX_DONE | _DIO_MAP_DIO1_FHSS
        _DIO_MAP_RX = _DIO_MAP_DIO0_RX_DONE | _DIO_MAP_DIO1_FHSS

        self._DIO_MAPPING = {
            "Tx": _DIO_MAP_TX,
            "Rx": _DIO_MAP_RX,
        }

        # 注册中断处理函数
        # DIO0：接收完成 / 发送完成
        self._dio0_pin.irq(handler=self._irq_handler, trigger=Pin.IRQ_RISING)
        # DIO1：跳频信道切换
        self._dio1_pin.irq(handler=self._irq_handler, trigger=Pin.IRQ_RISING)

        # 请求待机模式，使 SX1276 执行接收初始化
        self.mode = "STANDBY"

    # ==================== 公共方法 ====================

    def spi_write(self, reg: str, data, fifo: bool = False) -> None:
        """
        通过 SPI 写入寄存器
        Args:
            reg (str): 寄存器名称（对应 _REG_TABLE 中的键）
            data: 待写入的数据（int 或 bytes）
            fifo (bool): 是否为 FIFO 写入模式
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 仅在任务/主循环上下文使用：涉及同步 SPI I/O。
            - 副作用：修改芯片寄存器状态
        ==========================================
        Write to a register via SPI.
        Args:
            reg (str): Register name (key in _REG_TABLE)
            data: Data to write (int or bytes)
            fifo (bool): Whether this is a FIFO write
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Task-context only: performs synchronous SPI I/O.
            - Side effects: Modifies chip register state
        """
        # 构造写命令字节（最高位置 1 表示写操作）
        wb = bytes([self._REG_TABLE[reg] | 0x80])
        if fifo:
            data = wb + data
        else:
            data = wb + bytes([data])
        # 拉低 CS 片选使能通信
        self._cs_pin.value(0)
        try:
            self._spi.write(data)
        except OSError as e:
            self._cs_pin.value(1)
            raise RuntimeError("SPI write failed at register %s" % reg) from e
        # 拉高 CS 释放总线
        self._cs_pin.value(1)

    def spi_read(self, reg: str = None, length: int = None):
        """
        通过 SPI 读取寄存器
        Args:
            reg (str): 寄存器名称（对应 _REG_TABLE 中的键）
            length (int): 读取的字节数（含地址字节）
        Returns:
            int 或 bytes: 单字节返回 int，多字节返回 bytes
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 仅在任务/主循环上下文使用：涉及同步 SPI I/O。
        ==========================================
        Read from a register via SPI.
        Args:
            reg (str): Register name (key in _REG_TABLE)
            length (int): Number of bytes to read (including address byte)
        Returns:
            int or bytes: Single byte returns int, multiple bytes returns bytes
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Task-context only: performs synchronous SPI I/O.
        """
        self._cs_pin.value(0)
        try:
            if length is None:
                # https://docs.micropython.org/en/latest/library/machine.SPI.html#machine-softspi
                data = self._spi.read(2, self._REG_TABLE[reg])[1]
            else:
                data = self._spi.read(length + 1, self._REG_TABLE[reg])[1:]
        except OSError as e:
            self._cs_pin.value(1)
            raise RuntimeError("SPI read failed at register %s" % reg) from e
        self._cs_pin.value(1)
        return data

    def set_freq(self) -> None:
        """
        设置当前跳频信道的频率
        Notes:
            - 从 _fhss_list 中读取当前信道索引对应的频率
            - 将频率值写入 Frf 寄存器（MSB/MID/LSB）
            - 由 process_irq() 在任务/主循环上下文处理 FhssChangeChannel 时调用
            - 副作用：修改芯片频率寄存器
        ==========================================
        Set frequency for current FHSS channel.
        Notes:
            - Reads frequency from _fhss_list at current channel index
            - Writes frequency value to Frf registers (MSB/MID/LSB)
            - Called by process_irq() in task/main-loop context for FhssChangeChannel
            - Side effects: Modifies chip frequency registers
        """
        # 读取当前信道索引（低 6 位有效）
        FhssPresentChannel = self.spi_read("RegHopChannel") & 0b00_111_111
        # 计算频率寄存器的值
        Frf = int(self._fhss_list[FhssPresentChannel] / self._FSTEP)
        # 写入频率寄存器（MSB、MID、LSB）
        self.spi_write("RegFrfMsb", (Frf >> 16) & 0xFF)
        self.spi_write("RegFrfMid", (Frf >> 8) & 0xFF)
        self.spi_write("RegFrfLsb", Frf & 0xFF)

    def read_fifo(self) -> tuple:
        """
        读取接收 FIFO 缓冲区
        Returns:
            tuple: (packet: bytes, SNR: float, RSSI: float)
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - 由 process_irq() 在任务/主循环上下文处理 RxDone 时调用
            - 读取数据后自动计算 SNR 和 RSSI
        ==========================================
        Read the receive FIFO buffer.
        Returns:
            tuple: (packet: bytes, SNR: float, RSSI: float)
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - Called by process_irq() in task/main-loop context for RxDone
            - SNR and RSSI are calculated automatically after reading
        """
        # 设置 FIFO 地址指针到当前接收地址
        self.spi_write("RegFifoAddrPtr", self.spi_read("RegFifoRxCurrentAddr"))
        # 读取数据包
        packet = self.spi_read("RegFifo", self.spi_read("RegRxNbBytes"))
        # 读取信噪比
        PacketSnr = self.spi_read("RegPktSnrValue")
        SNR = struct.unpack_from("b", bytes([PacketSnr]))[0] / 4
        # 读取 RSSI
        PacketRssi = self.spi_read("RegPktRssiValue")
        if SNR < 0:
            RSSI = -157 + PacketRssi + SNR
        else:
            RSSI = -157 + 16 / 15 * PacketRssi
        # 参见数据手册 Table 7 Frequency Synthesizer Specification
        RSSI = round(RSSI, 2)
        return packet, SNR, RSSI

    def write_fifo(self, data: bytes) -> None:
        """
        写入发送 FIFO 缓冲区
        Args:
            data (bytes): 待发送的数据
        Raises:
            RuntimeError: SPI 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入 FIFO 并设置负载长度寄存器
        ==========================================
        Write to the transmit FIFO buffer.
        Args:
            data (bytes): Data to transmit
        Raises:
            RuntimeError: SPI communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes to FIFO and sets payload length register
        """
        # 设置 FIFO 地址指针到起始地址
        self.spi_write("RegFifoAddrPtr", self._FIFO_BOTTOM)
        # 写入数据到 FIFO
        self.spi_write("RegFifo", data, fifo=True)
        # 设置负载长度
        self.spi_write("RegPayloadLength", len(data))

    def send(self, dst_id: int = 0, pkt_id: int = 0, pkt_type: int = 0, msg: str = "", retry: int = 1, timeout: int = 9, debug: bool = False) -> None:
        """
        发送数据包
        Args:
            dst_id (int): 目标接收者 ID
            pkt_id (int): 数据包 ID（REQ 类型时自动随机生成）
            pkt_type (int): 数据包类型（PKT_TYPE_REQ / PKT_TYPE_ACK / PKT_TYPE_BRD）
            msg (str): 待发送的消息内容
            retry (int): REQ 模式下未收到 ACK 时的重试次数
            timeout (int): 等待 ACK 的超时时间（秒）
            debug (bool): 是否打印调试信息
        Notes:
            - REQ 类型：发送后等待 ACK，超时后重试
            - ACK/BRD 类型：发送后立即返回
            - 消息长度超过 240 字节会引发异常（FIFO 缓冲区限制）
            - ISR-safe: 否
            - 副作用：修改芯片工作模式、FIFO 内容
        ==========================================
        Send a data packet.
        Args:
            dst_id (int): Destination receiver ID
            pkt_id (int): Packet ID (auto-generated for REQ type)
            pkt_type (int): Packet type (PKT_TYPE_REQ / PKT_TYPE_ACK / PKT_TYPE_BRD)
            msg (str): Message content to send
            retry (int): Retry count for REQ mode when ACK not received
            timeout (int): ACK timeout in seconds
            debug (bool): Print debug information
        Notes:
            - REQ type: Waits for ACK, retries on timeout
            - ACK/BRD type: Returns immediately after sending
            - Messages longer than 240 bytes raise an exception (FIFO buffer limit)
            - ISR-safe: No
            - Side effects: Modifies chip mode and FIFO content
        """
        # 消息长度检查：FIFO 缓冲区为 256 字节，消息不能超过 240 字节
        # 本驱动工作在数据链路层，上层协议负责分片（fragmentation）
        if len(msg) > 240:
            raise ValueError("Message too long: %d bytes, max 240 bytes" % len(msg))

        # 设置数据包类型
        self._pkt_type = pkt_type
        if pkt_type == self.PKT_TYPE["REQ"]:
            # REQ 类型：随机生成数据包 ID
            pkt_id = random.randint(1, 65535)
            self._pkt_id = pkt_id

        # 构造数据包头：src_id, dst_id, pkt_id, pkt_type
        header = struct.pack(self._HEADER_FMT, self.src_id, dst_id, pkt_id, pkt_type)
        data = header + msg.encode()

        if pkt_type == self.PKT_TYPE["REQ"]:
            # REQ 模式：发送后等待 ACK 应答
            for _ in range(retry):
                self.mode = "STANDBY"
                self.write_fifo(data)
                # 切换到 TX 模式发送数据
                self.mode = "TX"
                # 等待 ACK 应答（process_irq() 在任务上下文将 _pkt_id 清零）
                for _ in range(timeout):
                    if self._pkt_id == 0:
                        break
                    time.sleep(1)
                else:
                    # 未收到 ACK，超时
                    if debug:
                        self._log("REQ is not ACKed before timeout is triggered")
                # 收到 ACK，退出重试循环
                if self._pkt_id == 0:
                    break
            else:
                # 所有重试均失败
                if debug:
                    self._log("Resend the REQ packet %d times but it is still not ACKed" % retry)
        elif pkt_type in [self.PKT_TYPE["ACK"], self.PKT_TYPE["BRD"]]:
            # ACK/BRD 模式：发送后立即返回
            self.mode = "STANDBY"
            self.write_fifo(data)
            self.mode = "TX"
        else:
            self._log("Unsupported packet type")

    def req_packet_handler(self, data: bytes, SNR: float, RSSI: float) -> None:
        """
        REQ 数据包回调处理函数（用户可重写）
        Args:
            data: 接收到的数据负载
            SNR: 信噪比
            RSSI: 接收信号强度指示
        Notes:
            - 当接收到匹配目标 ID 的 REQ 数据包时被调用
            - 由 process_irq() 在任务/主循环上下文调用；回调不得阻塞
        ==========================================
        REQ packet callback handler (override by user).
        Args:
            data: Received data payload
            SNR: Signal-to-noise ratio
            RSSI: Received signal strength indicator
        Notes:
            - Called when a REQ packet matching the target ID is received
            - Called by process_irq() in task/main-loop context; callbacks must not block
        """
        pass

    def brd_packet_handler(self, data: bytes, SNR: float, RSSI: float) -> None:
        """
        BRD 广播数据包回调处理函数（用户可重写）
        Args:
            data: 接收到的数据负载
            SNR: 信噪比
            RSSI: 接收信号强度指示
        Notes:
            - 当接收到 BRD 广播数据包时被调用
            - 由 process_irq() 在任务/主循环上下文调用；回调不得阻塞
        ==========================================
        BRD broadcast packet callback handler (override by user).
        Args:
            data: Received data payload
            SNR: Signal-to-noise ratio
            RSSI: Received signal strength indicator
        Notes:
            - Called when a BRD broadcast packet is received
            - Called by process_irq() in task/main-loop context; callbacks must not block
        """
        pass

    def after_TxDone(self, _) -> None:
        """
        发送完成回调处理函数（用户可重写）
        Args:
            _: 保留参数（兼容 Pin IRQ 回调签名）
        Notes:
            - 在每次 TxDone 中断后被调用
            - 由 process_irq() 在任务/主循环上下文调用；回调不得阻塞
        ==========================================
        After-transmit callback handler (override by user).
        Args:
            _: Reserved parameter (compatible with Pin IRQ callback signature)
        Notes:
            - Called after every TxDone interrupt
            - Called by process_irq() in task/main-loop context; callbacks must not block
        """
        pass

    # ==================== @property ====================

    @property
    def mode(self) -> str:
        """
        获取当前工作模式
        Returns:
            str: 当前模式字符串（SLEEP/STANDBY/TX/RXCONTINUOUS/RXSINGLE/CAD）
        ==========================================
        Get current operating mode.
        Returns:
            str: Current mode string (SLEEP/STANDBY/TX/RXCONTINUOUS/RXSINGLE/CAD)
        """
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """
        设置工作模式
        Args:
            value (str): 目标模式（TX/RXCONTINUOUS/STANDBY）
        Notes:
            - TX 模式：先设置频率和 DIO 映射，然后发送
            - RXCONTINUOUS 模式：先设置频率和 DIO 映射，然后持续监听
            - STANDBY 模式：清除 DIO 映射
            - 切换到 TX 或 RXCONTINUOUS 时会重置 is_available 标志
            - 仅在任务/主循环上下文切换模式；涉及同步 SPI I/O
            - 副作用：修改芯片工作模式寄存器
        ==========================================
        Set operating mode.
        Args:
            value (str): Target mode (TX/RXCONTINUOUS/STANDBY)
        Notes:
            - TX mode: Sets frequency and DIO mapping, then transmits
            - RXCONTINUOUS mode: Sets frequency and DIO mapping, then listens continuously
            - STANDBY mode: Clears DIO mapping
            - Resets is_available flag when switching to TX or RXCONTINUOUS
            - Task/main-loop context only; performs synchronous SPI I/O
            - Side effects: Modifies chip operating mode register
        """
        if value == "TX":
            # 发送模式：设置频率和发送 DIO 映射
            self.set_freq()
            self.spi_write("RegDioMapping1", self._DIO_MAPPING["Tx"])
            self.is_available = False
        elif value == "RXCONTINUOUS":
            # 持续接收模式：设置频率和接收 DIO 映射
            # 使用 RXCONTINUOUS 而非 RXSINGLE：
            # RXSINGLE 有时限机制（节能措施），接收方从休眠唤醒并监听信道
            # 若无信号则返回休眠。常规通信中需持续监听信道直至主动停止
            self.set_freq()
            self.spi_write("RegDioMapping1", self._DIO_MAPPING["Rx"])
            self.is_available = False
        elif value == "STANDBY":
            # 待机模式：清除 DIO 映射
            self.spi_write("RegDioMapping1", 0x00)
        else:
            self._log("Unknown working mode: %s" % value)
        # 仅在模式改变时切换
        if self._mode != value:
            self.spi_write("RegOpMode", self.MODE[value])
            self._mode = value

    # ==================== 私有方法 ====================

    def _irq_handler(self, pin: Pin) -> None:
        """Record an IRQ edge without allocation, I/O, logging, or callbacks."""
        self._irq_pending = True

    def process_irq(self) -> bool:
        """Handle a pending IRQ in task/main-loop context, not hard IRQ context."""
        if not self._irq_pending:
            return False
        self._irq_pending = False
        self._process_irq(None)
        return True

    def _process_irq(self, pin: Pin) -> None:
        """
        延后 IRQ 处理函数（DIO0/DIO1 共用）
        由 process_irq() 在协程或主循环上下文调用，处理 TxDone、RxDone 和
        FhssChangeChannel。硬件 IRQ 只设置 _irq_pending 标志。
        Args:
            pin (Pin): 保留的兼容参数；不在硬件 IRQ 中使用。
        Notes:
            - 在任务上下文执行，允许 SPI、协议解析、日志和用户回调
            - 调用方应定期执行 process_irq()；send_async() 在等待 ACK 时会执行
            - 处理完整 REQ/ACK 通信流程的 4 个关键点
        ==========================================
        Deferred IRQ processor shared by DIO0/DIO1.
        It is called by process_irq() in coroutine/main-loop context for TxDone,
        RxDone, and FhssChangeChannel. The hardware IRQ only sets _irq_pending.
        Args:
            pin (Pin): Retained for compatibility and unused by the hard IRQ.
        Notes:
            - Runs in task context, where SPI, parsing, logging, and callbacks are allowed
            - Call process_irq() regularly; send_async() does so while waiting for an ACK
            - Handles the four critical points of the REQ/ACK flow"""
        # 读取中断标志寄存器
        irq_flags = self.spi_read("RegIrqFlags")
        # 写入 0xFF 清除所有类型的中断标志
        self.spi_write("RegIrqFlags", 0xFF)

        # 一次完整的 REQ/ACK 通信流程包含 4 个关键点（CP）：
        # 步骤 0：接收方处于 RxCont 模式
        # 步骤 1：发送方发送数据，TxDone 中断在发送方触发（第 1 个 CP）
        # 步骤 2：发送方任务上下文将模式从 Tx 切换到 RxCont，准备监听 ACK 应答（步骤 8）
        # 步骤 3：RxDone 中断在所有接收方触发（第 2 个 CP）
        # 步骤 4：在任务上下文中，若 dst_id 匹配 self.src_id，接收方确认为正确的接收者
        # 步骤 5：正确的接收方将模式切换到 STANDBY，然后发送 ACK
        # 步骤 6：接收方发送 ACK 后，TxDone 中断在接收方触发（第 3 个 CP）
        # 步骤 7：在任务上下文中，接收方切换到 STANDBY 模式供后续使用
        # 步骤 8：发送方收到 ACK 应答（见步骤 2），RxDone 在发送方触发（第 4 个 CP）
        # 步骤 9：在任务上下文中，发送方模式从 RxCont 切换到 STANDBY。完成

        if irq_flags & self._IRQ_FLAGS["TxDone"]:
            # Tx 模式被请求且数据已发出时，TxDone 被触发
            if self._pkt_type == self.PKT_TYPE["REQ"]:
                # 发送方的 REQ 发送会满足此条件
                # 第 1 个关键点（CP）：模式从 Tx 切换到 RxCont
                self.mode = "RXCONTINUOUS"
            elif self._pkt_type == self.PKT_TYPE["ACK"]:
                # 第 3 个 CP：接收方的 ACK 应答会满足此条件
                # 完成双向通信，释放接收方
                self.is_available = True
            elif self._pkt_type == self.PKT_TYPE["BRD"]:
                # 广播完成后释放发送方
                self.is_available = True
            # 调用用户自定义的发送完成回调
            self.after_TxDone(None)

        elif irq_flags & self._IRQ_FLAGS["RxDone"]:
            # 读取 FIFO 数据
            packet, SNR, RSSI = self.read_fifo()
            if irq_flags & self._IRQ_FLAGS["PayloadCrcError"]:
                # CRC 校验错误
                self._log("PayloadCrcError: %s" % str(packet))
            else:
                # 数据包长度检查
                if len(packet) < self._HEADER_SIZE:
                    self._log("Packet too short: %s, SNR=%s, RSSI=%s" % (str(packet), SNR, RSSI))
                    return
                # 解析数据包头
                header, data = packet[: self._HEADER_SIZE], packet[self._HEADER_SIZE :]
                src_id, dst_id, pkt_id, pkt_type = struct.unpack(self._HEADER_FMT, header)

                if pkt_type == self.PKT_TYPE["REQ"]:
                    # 收到 REQ 数据包
                    if dst_id == self.src_id:
                        # 第 2 个 CP：接收方匹配目标 ID
                        self.mode = "STANDBY"
                        # 发送 ACK 应答
                        self.send(dst_id=src_id, pkt_id=pkt_id, pkt_type=self.PKT_TYPE["ACK"], msg="")
                        # 调用用户自定义的 REQ 处理回调
                        self.req_packet_handler(data, SNR, RSSI)
                        self._log("[RxDone] Right REQ receiver")
                    else:
                        # 收到 REQ 但目标 ID 不匹配，仍然显示内容但不确认
                        self.mode = "RXCONTINUOUS"
                        self._log("[RxDone] Wrong REQ receiver")

                elif pkt_type == self.PKT_TYPE["ACK"]:
                    # 收到 ACK 应答
                    if pkt_id == self._pkt_id:
                        # 第 4 个 CP：发送方收到正确的 ACK
                        self._pkt_id = 0
                        self.mode = "STANDBY"
                        self.is_available = True
                        self._log("[RxDone] Right ACK receiver")
                    else:
                        # 不是我们期待的 ACK
                        self.mode = "RXCONTINUOUS"
                        self._log("[RxDone] Wrong ACK receiver")

                elif pkt_type == self.PKT_TYPE["BRD"]:
                    # 收到 BRD 广播包
                    self.brd_packet_handler(data, SNR, RSSI)
                    self.mode = "RXCONTINUOUS"
                    self._log("[RxDone] BRD receiver")

                else:
                    self._log("Unknown packet type: %s, SNR=%s, RSSI=%s" % (str(packet), SNR, RSSI))

        elif irq_flags & self._IRQ_FLAGS["FhssChangeChannel"]:
            # 跳频信道切换中断：设置新频率
            self.set_freq()
        else:
            # 未识别的中断标志
            for name, flag in self._IRQ_FLAGS.items():
                if irq_flags & flag:
                    self._log("Unexpected interrupt: %s" % name)

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
            print("[SX1276] %s" % msg)

    def deinit(self) -> None:
        """
        释放硬件资源
        Notes:
            - 禁用 DIO0/DIO1 中断
            - 将芯片置为休眠模式
            - 释放 SPI 片选引脚
            - 不影响外部传入的 SPI 和 Pin 实例
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Notes:
            - Disables DIO0/DIO1 interrupts
            - Puts the chip in sleep mode
            - Releases SPI chip select pin
            - Does not affect externally provided SPI and Pin instances
            - ISR-safe: No
        """
        # 禁用中断
        self._dio0_pin.irq(handler=None)
        self._dio1_pin.irq(handler=None)
        # 将芯片置为休眠模式
        self.spi_write("RegOpMode", self.MODE["SLEEP"])
        self._mode = "SLEEP"
        # 拉高 CS 释放 SPI 总线
        self._cs_pin.on()
        self._log("deinitialized")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

# MicroPython omits private const fields; preserve source self/cls lookups.
SX1276._FIFO_BOTTOM = 0
SX1276._HEADER_SIZE = 8
