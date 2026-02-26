# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 上午11:20
# @Author  : 缪贵成
# @File    : pn532.py
# @Description : 基于PN532的NFC通信模块驱动程序，参考自：https://github.com/luiz-brandao/micropython_pn532/tree/main/pn532
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const
from machine import Pin

# ======================================== 全局变量 ============================================

_PREAMBLE = const(0x00)
_STARTCODE1 = const(0x00)
_STARTCODE2 = const(0xFF)
_POSTAMBLE = const(0x00)

_HOSTTOPN532 = const(0xD4)
_PN532TOHOST = const(0xD5)

# PN532 Commands
_COMMAND_DIAGNOSE = const(0x00)
_COMMAND_GETFIRMWAREVERSION = const(0x02)
_COMMAND_GETGENERALSTATUS = const(0x04)
_COMMAND_READREGISTER = const(0x06)
_COMMAND_WRITEREGISTER = const(0x08)
_COMMAND_READGPIO = const(0x0C)
_COMMAND_WRITEGPIO = const(0x0E)
_COMMAND_SETSERIALBAUDRATE = const(0x10)
_COMMAND_SETPARAMETERS = const(0x12)
_COMMAND_SAMCONFIGURATION = const(0x14)
_COMMAND_POWERDOWN = const(0x16)
_COMMAND_RFCONFIGURATION = const(0x32)
_COMMAND_RFREGULATIONTEST = const(0x58)
_COMMAND_INJUMPFORDEP = const(0x56)
_COMMAND_INJUMPFORPSL = const(0x46)
_COMMAND_INLISTPASSIVETARGET = const(0x4A)
_COMMAND_INATR = const(0x50)
_COMMAND_INPSL = const(0x4E)
_COMMAND_INDATAEXCHANGE = const(0x40)
_COMMAND_INCOMMUNICATETHRU = const(0x42)
_COMMAND_INDESELECT = const(0x44)
_COMMAND_INRELEASE = const(0x52)
_COMMAND_INSELECT = const(0x54)
_COMMAND_INAUTOPOLL = const(0x60)
_COMMAND_TGINITASTARGET = const(0x8C)
_COMMAND_TGSETGENERALBYTES = const(0x92)
_COMMAND_TGGETDATA = const(0x86)
_COMMAND_TGSETDATA = const(0x8E)
_COMMAND_TGSETMETADATA = const(0x94)
_COMMAND_TGGETINITIATORCOMMAND = const(0x88)
_COMMAND_TGRESPONSETOINITIATOR = const(0x90)
_COMMAND_TGGETTARGETSTATUS = const(0x8A)

_RESPONSE_INDATAEXCHANGE = const(0x41)
_RESPONSE_INLISTPASSIVETARGET = const(0x4B)

_WAKEUP = const(0x55)

_MIFARE_ISO14443A = const(0x00)

# Mifare Commands
MIFARE_CMD_AUTH_A = const(0x60)
MIFARE_CMD_AUTH_B = const(0x61)
MIFARE_CMD_READ = const(0x30)
MIFARE_CMD_WRITE = const(0xA0)
MIFARE_CMD_TRANSFER = const(0xB0)
MIFARE_CMD_DECREMENT = const(0xC0)
MIFARE_CMD_INCREMENT = const(0xC1)
MIFARE_CMD_STORE = const(0xC2)
MIFARE_ULTRALIGHT_CMD_WRITE = const(0xA2)

# Prefixes for NDEF Records (to identify record type)
NDEF_URIPREFIX_NONE = const(0x00)
NDEF_URIPREFIX_HTTP_WWWDOT = const(0x01)
NDEF_URIPREFIX_HTTPS_WWWDOT = const(0x02)
NDEF_URIPREFIX_HTTP = const(0x03)
NDEF_URIPREFIX_HTTPS = const(0x04)
NDEF_URIPREFIX_TEL = const(0x05)
NDEF_URIPREFIX_MAILTO = const(0x06)
NDEF_URIPREFIX_FTP_ANONAT = const(0x07)
NDEF_URIPREFIX_FTP_FTPDOT = const(0x08)
NDEF_URIPREFIX_FTPS = const(0x09)
NDEF_URIPREFIX_SFTP = const(0x0A)
NDEF_URIPREFIX_SMB = const(0x0B)
NDEF_URIPREFIX_NFS = const(0x0C)
NDEF_URIPREFIX_FTP = const(0x0D)
NDEF_URIPREFIX_DAV = const(0x0E)
NDEF_URIPREFIX_NEWS = const(0x0F)
NDEF_URIPREFIX_TELNET = const(0x10)
NDEF_URIPREFIX_IMAP = const(0x11)
NDEF_URIPREFIX_RTSP = const(0x12)
NDEF_URIPREFIX_URN = const(0x13)
NDEF_URIPREFIX_POP = const(0x14)
NDEF_URIPREFIX_SIP = const(0x15)
NDEF_URIPREFIX_SIPS = const(0x16)
NDEF_URIPREFIX_TFTP = const(0x17)
NDEF_URIPREFIX_BTSPP = const(0x18)
NDEF_URIPREFIX_BTL2CAP = const(0x19)
NDEF_URIPREFIX_BTGOEP = const(0x1A)
NDEF_URIPREFIX_TCPOBEX = const(0x1B)
NDEF_URIPREFIX_IRDAOBEX = const(0x1C)
NDEF_URIPREFIX_FILE = const(0x1D)
NDEF_URIPREFIX_URN_EPC_ID = const(0x1E)
NDEF_URIPREFIX_URN_EPC_TAG = const(0x1F)
NDEF_URIPREFIX_URN_EPC_PAT = const(0x20)
NDEF_URIPREFIX_URN_EPC_RAW = const(0x21)
NDEF_URIPREFIX_URN_EPC = const(0x22)
NDEF_URIPREFIX_URN_NFC = const(0x23)

_GPIO_VALIDATIONBIT = const(0x80)
_GPIO_P30 = const(0)
_GPIO_P31 = const(1)
_GPIO_P32 = const(2)
_GPIO_P33 = const(3)
_GPIO_P34 = const(4)
_GPIO_P35 = const(5)

_ACK = b"\x00\x00\xFF\x00\xFF\x00"
_FRAME_START = b"\x00\x00\xFF"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# PN532 基类
class PN532:
    """
    PN532 NFC 模块驱动基类，提供高层 NFC 功能接口。
    低层 I/O 方法 (_wakeup, _wait_ready, _read_data, _write_data) 需由子类实现
    (支持 I2C/SPI/UART)。

    Attributes:
        debug (bool): 调试输出开关。
        _irq (Pin or None): IRQ 引脚。
        _reset_pin (Pin or None): Reset 引脚。
        low_power (bool): 低功耗状态标志。

    Methods:
        reset() -> None: 硬件复位并唤醒模块。
        call_function(command: int, response_length: int = 0, params: list = [], timeout: int = 1000) -> bytes|None:
            发送命令并获取响应数据。
        send_command(command: int, params: list = [], timeout: int = 1000) -> bool:
            发送命令并等待 ACK。
        process_response(command: int, response_length: int = 0, timeout: int = 1000) -> bytes:
            处理命令响应数据。
        power_down() -> bool: 进入低功耗模式。
        firmware_version -> tuple: 获取固件版本信息 (IC, Ver, Rev, Support)。
        SAM_configuration() -> None: 配置 PN532 用于 MiFare 卡读取。
        read_passive_target(card_baud: int = 0x00, timeout: int = 1000) -> bytes|None:
            读取被动感应卡。
        listen_for_passive_target(card_baud: int = 0x00, timeout: int = 1) -> bytes|bool:
            监听被动感应卡。
        get_passive_target(timeout: int = 1000) -> bytes|None:
            获取被动感应卡数据。
        mifare_classic_authenticate_block(uid: bytes, block_number: int, key_number: int, key: bytes) -> bool:
            验证 Mifare Classic 块。
        mifare_classic_read_block(block_number: int) -> bytes|None:
            读取 Mifare Classic 块。
        mifare_classic_write_block(block_number: int, data: bytes) -> bool:
            写入 Mifare Classic 块。
        ntag2xx_write_block(block_number: int, data: bytes) -> bool:
            写入 NTAG2XX 块。
        ntag2xx_read_block(block_number: int) -> bytes|None:
            读取 NTAG2XX 块。

    Notes:
        低层 I/O 方法 (_wakeup, _wait_ready, _read_data, _write_data) 需由子类实现。
        方法可能会调用 I2C/SPI/UART，非 ISR-safe。
        构造函数不会执行耗时 I/O，reset() 可在用户代码中调用。
        高层方法可用于获取固件版本、读写 Mifare / NTAG2XX 卡。

    ==========================================

    PN532 driver base class, providing high-level NFC functionality.
    Low-level I/O (_wakeup, _wait_ready, _read_data, _write_data) must
    be implemented by subclasses (I2C/SPI/UART).

    Attributes:
        debug (bool): enable debug print
        _irq (Pin or None): IRQ pin
        _reset_pin (Pin or None): Reset pin
        low_power (bool): low power state flag

    Methods:
        reset() -> None: Perform hardware reset and wakeup.
        call_function(command: int, response_length: int = 0, params: list = [], timeout: int = 1000) -> bytes|None:
            Send command and get response bytes.
        send_command(command: int, params: list = [], timeout: int = 1000) -> bool:
            Send command and wait for ACK.
        process_response(command: int, response_length: int = 0, timeout: int = 1000) -> bytes:
            Process command response.
        power_down() -> bool: Enter low power mode.
        firmware_version -> tuple: Get firmware version (IC, Ver, Rev, Support).
        SAM_configuration() -> None: Configure PN532 for MiFare card reading.
        read_passive_target(card_baud: int = 0x00, timeout: int = 1000) -> bytes|None:
            Read a passive target card.
        listen_for_passive_target(card_baud: int = 0x00, timeout: int = 1) -> bytes|bool:
            Listen for a passive target card.
        get_passive_target(timeout: int = 1000) -> bytes|None:
            Get passive target card data.
        mifare_classic_authenticate_block(uid: bytes, block_number: int, key_number: int, key: bytes) -> bool:
            Authenticate a Mifare Classic block.
        mifare_classic_read_block(block_number: int) -> bytes|None:
            Read a Mifare Classic block.
        mifare_classic_write_block(block_number: int, data: bytes) -> bool:
            Write a Mifare Classic block.
        ntag2xx_write_block(block_number: int, data: bytes) -> bool:
            Write an NTAG2XX block.
        ntag2xx_read_block(block_number: int) -> bytes|None:
            Read an NTAG2XX block.

    Notes:
        Low-level I/O methods (_wakeup, _wait_ready, _read_data, _write_data)
        must be implemented by subclass.
        Methods performing I2C/SPI/UART are not ISR-safe.
        Constructor does not perform blocking I/O. Use reset() in user code.
        High-level methods can be used to read firmware version and access Mifare / NTAG2XX cards.
    """

    def __init__(self, *, debug=False, irq=None, reset=None):
        """
        创建 PN532 类实例，用于 NFC 模块操作。

        Args:
            debug (bool): 是否启用调试输出。
            irq (Pin or None): IRQ 引脚。
            reset (Pin or None): Reset 引脚。

        Notes:
            构造函数不会执行耗时 I/O。
            可在用户代码中调用 reset() 进行硬件复位。
            初始化后可获取 firmware_version。

        ==========================================

        Create an instance of the PN532 class for NFC module operations.

        Args:
            debug (bool): enable debug print.
            irq (Pin or None): IRQ pin.
            reset (Pin or None): Reset pin.

        Notes:
            Constructor does not perform blocking I/O.
            reset() can be called in user code to perform hardware reset.
            Firmware version can be obtained after initialization.
        """
        self.debug = debug
        self._irq = irq
        self._reset_pin = reset
        self.low_power = True
        if self.debug:
            print("PN532 instance created, debug enabled")

    def _wakeup(self):
        """
        唤醒 PN532 模块，子类必须实现此方法。

        Raises:
            NotImplementedError: 子类未实现该方法时抛出。

        Notes:
            非 ISR-safe。
            必须由子类实现，具体 I2C/SPI/UART 方式由子类定义。

        ==========================================

        Wake up the PN532 module. Must be implemented by subclass.

        Raises:
            NotImplementedError: Raised if the subclass does not implement this method.

        Notes:
            Not ISR-safe.
            Subclass must implement low-level wakeup via I2C/SPI/UART.
        """
        raise NotImplementedError

    def _wait_ready(self, timeout) -> bool:
        """
        等待 PN532 就绪或超时，子类必须实现。

        Args:
            timeout (int): 最大等待时间，单位毫秒(ms)。

        Raises:
            NotImplementedError: 子类未实现该方法时抛出。

        Returns:
            bool: 就绪返回 True，超时返回 False。

        Notes:
            非 ISR-safe。
            子类必须实现低层等待逻辑。

        ==========================================

        Wait until PN532 is ready or timeout. Must be implemented by subclass.

        Args:
            timeout (int): maximum wait time in milliseconds (ms).

        Raises:
            NotImplementedError: Raised if the subclass does not implement this method.

        Returns:
            bool: True if ready, False if timeout.

        Notes:
            Not ISR-safe.
            Subclass must implement low-level wait logic.
        """
        raise NotImplementedError

    def _read_data(self, count) -> bytes:
        """
        从 PN532 读取原始字节数据，子类必须实现。

        Args:
            count (int): 需要读取的字节数。

        Raises:
            NotImplementedError: 子类未实现该方法时抛出。

        Returns:
            bytes: 读取到的数据。

        Notes:
            非 ISR-safe。
            子类必须实现低层读取逻辑。

        ==========================================

        Read raw bytes from PN532. Must be implemented by subclass.

        Args:
            count (int): number of bytes to read.

        Raises:
             NotImplementedError: Raised if the subclass does not implement this method.

        Returns:
            bytes: data read from PN532.

        Notes:
            Not ISR-safe.
            Subclass must implement low-level read logic.
        """
        raise NotImplementedError

    def _write_data(self, framebytes):
        """
        向 PN532 写入原始字节数据，子类必须实现。

        Args:
            framebytes (bytes): 待写入的数据字节。

        Raises:
            NotImplementedError: 子类未实现该方法时抛出。

        Notes:
            非 ISR-safe。
            子类必须实现低层写入逻辑。

        ==========================================

        Write raw bytes to PN532. Must be implemented by subclass.

        Args:
            framebytes (bytes): bytes to write.

        Raises:
            NotImplementedError: Raised if the subclass does not implement this method.

        Notes:
            Not ISR-safe.
            Subclass must implement low-level write logic.
        """
        raise NotImplementedError

    # ============================ 帧处理 ============================
    def _write_frame(self, data):
        """
        向 PN532 发送一帧数据，自动添加帧头、长度、校验和和帧尾。

        Args:
            data (bytearray): 待发送的数据字节，长度必须在 2-254 字节之间。

        Raises:
            ValueError: 当数据长度不在 2-254 字节范围内时抛出。

        Notes:
            非 ISR-safe。
            方法会调用低层 _write_data 写入总线。
            自动构建完整帧格式: PREAMBLE + STARTCODE + LEN + LCS + DATA + DCS + POSTAMBLE。

        ==========================================

        Write a frame to PN532, automatically adding header, length, checksum, and postamble.

        Args:
            data (bytearray): data bytes to send, length must be 2-254 bytes.

        Raises:
            ValueError: if data length is not within 2-254 bytes.

        Notes:
            Not ISR-safe.
            Calls low-level _write_data to send bytes on bus.
            Constructs complete frame: PREAMBLE + STARTCODE + LEN + LCS + DATA + DCS + POSTAMBLE.
        """
        if not (2 <= len(data) <= 254):
            raise ValueError("Data length must be between 2 and 254 bytes")
        length = len(data)
        frame = bytearray(length + 8)
        frame[0] = _PREAMBLE
        frame[1] = _STARTCODE1
        frame[2] = _STARTCODE2
        checksum = sum(frame[0:3])
        frame[3] = length & 0xFF
        frame[4] = (~length + 1) & 0xFF
        frame[5:-2] = data
        checksum += sum(data)
        frame[-2] = ~checksum & 0xFF
        frame[-1] = _POSTAMBLE
        # Send frame.
        if self.debug:
            print("Write frame: ", [hex(i) for i in frame])
        self._write_data(bytes(frame))

    def _read_frame(self, length) -> bytes:
        """
        从 PN532 读取响应帧并返回有效数据，自动校验帧头、长度和数据校验和。

        Args:
            length (int): 期望数据长度（不包含帧头、长度和校验字节）。

        Returns:
            bytes: 解析后的有效数据字节。

        Raises:
            RuntimeError:
                找到有效前导码时。
                起始码不正确时。
                长度校验失败。
                数据校验失败。

        Notes:
            非 ISR-safe。
            方法会调用低层 _read_data 读取总线数据。
            解析完整帧格式: PREAMBLE + STARTCODE + LEN + LCS + DATA + DCS + POSTAMBLE。

        ==========================================

        Read a response frame from PN532 and return the valid data bytes, automatically
        verifying header, length, and data checksum.

        Args:
            length (int): expected data length (excluding frame header, length, and checksum bytes).

        Returns:
            bytes: valid data bytes extracted from the frame.

        Raises:
            RuntimeError:
                No valid preamble found.
                Invalid start code.
                Length checksum mismatch.
                Data checksum mismatch.

        Notes:
            Not ISR-safe.
            Calls low-level _read_data to receive bytes from bus.
            Parses complete frame: PREAMBLE + STARTCODE + LEN + LCS + DATA + DCS + POSTAMBLE.
        """
        response = self._read_data(length + 7)
        if self.debug:
            print("Read frame:", [hex(i) for i in response])

        # Swallow all the 0x00 values that preceed 0xFF.
        offset = 0
        while response[offset] == 0x00:
            offset += 1
            if offset >= len(response):
                raise RuntimeError("Response frame preamble does not contain 0x00FF!")
        if response[offset] != 0xFF:
            raise RuntimeError("Response frame preamble does not contain 0x00FF!")
        offset += 1
        if offset >= len(response):
            raise RuntimeError("Response contains no data!")
        # Check length & length checksum match.
        frame_len = response[offset]
        if (frame_len + response[offset + 1]) & 0xFF != 0:
            raise RuntimeError("Response length checksum did not match length!")
        # Check frame checksum value matches bytes.
        checksum = sum(response[offset + 2 : offset + 2 + frame_len + 1]) & 0xFF
        if checksum != 0:
            raise RuntimeError("Response checksum did not match expected value: ", checksum)
        # Return frame data.
        return response[offset + 2 : offset + 2 + frame_len]

    # ============================ 高层方法 ============================
    def reset(self):
        """
        对 PN532 执行硬件复位（如果提供了 reset 引脚）并唤醒设备。

        Notes:
            调用会操作 GPIO 引脚和 I2C/SPI/UART，非 ISR-safe。
            硬件复位时间需大于 100ms。

        ==========================================

        Perform hardware reset on PN532 (if reset pin provided) and wakeup.

        Notes:
            Performs GPIO and I2C/SPI/UART operations, not ISR-safe.
            Hardware reset requires >100ms delay.
        """
        if self._reset_pin:
            if self.debug:
                print("Resetting PN532")
            self._reset_pin.init(Pin.OUT)
            self._reset_pin.value(0)
            time.sleep(0.1)
            self._reset_pin.value(1)
            time.sleep(0.1)
        self._wakeup()

    def call_function(self, command, response_length=0, params=[], timeout=1000) -> bytes | None:
        """
        发送命令到 PN532 并等待返回的数据。

        Args:
            command (int): 要发送的 PN532 命令。
            response_length (int): 期望返回数据长度，默认 0。
            params (list): 可选命令参数列表。
            timeout (int): 等待响应的超时时间，单位 ms。

        Returns:
            bytes 或 None: 返回响应数据，如果命令发送失败则返回 None。

        Notes:
            调用会进行 I2C/SPI/UART 写操作，非 ISR-safe。

        ==========================================

        Send a command to PN532 and wait for response bytes.

        Args:
            command (int): PN532 command.
            response_length (int): Expected response length, default 0.
            params (list): Optional command parameters.
            timeout (int): Timeout in ms.

        Returns:
            bytes or None: Response data or None if failed.

        Notes:
            Calling will perform I2C/SPI/UART write operation,Not ISR-safe.
        """
        if not self.send_command(command, params=params, timeout=timeout):
            return None
        return self.process_response(command, response_length=response_length, timeout=timeout)

    def send_command(self, command, params=[], timeout=1000) -> bool:
        """
        向 PN532 发送命令并等待 ACK 确认。

        Args:
            command (int): 要发送的 PN532 命令。
            params (list): 命令参数列表。
            timeout (int): 等待 ACK 超时时间，单位 ms。

        Returns:
            bool: ACK 是否成功接收。

        Raises:
            RuntimeError: 未收到 ACK 或通信失败。

        Notes:
            调用会进行 I2C/SPI/UART 写操作，非 ISR-safe。
            如果低功耗模式，调用前会唤醒设备。
        ==========================================

        Send command to PN532 and wait for ACK.

        Args:
            command (int): PN532 command.
            params (list): Command parameters.
            timeout (int): Timeout in ms.

        Returns:
            bool: True if ACK received, False otherwise.

        Raises:
            RuntimeError: If ACK not received or communication fails.

        Notes:
            Not ISR-safe. Wakes up device if in low power mode.
        """
        if self.low_power:
            self._wakeup()

        # Build frame data with command and parameters.
        data = bytearray(2 + len(params))
        data[0] = _HOSTTOPN532
        data[1] = command & 0xFF
        for i, val in enumerate(params):
            data[2 + i] = val
        # Send frame and wait for response.
        try:
            self._write_frame(data)
        except OSError:
            return False
        if not self._wait_ready(timeout):
            return False
        # Verify ACK response and wait to be ready for function response.
        if not _ACK == self._read_data(len(_ACK)):
            raise RuntimeError("Did not receive expected ACK from PN532!")
        return True

    def process_response(self, command, response_length=0, timeout=1000) -> bytes | None:
        """
        读取命令的响应数据。

        Args:
            command (int): 对应的 PN532 命令。
            response_length (int): 期望响应数据长度。
            timeout (int): 超时时间，单位 ms。

        Returns:
            bytes 或 None: 返回响应数据，如果超时则返回 None。

        Raises:
            RuntimeError: 响应格式异常或命令不匹配。

        Notes:
            调用会进行 I2C/SPI/UART 读操作，非 ISR-safe。

        ==========================================

        Read response of a PN532 command.

        Args:
            command (int): PN532 command.
            response_length (int): Expected response length.
            timeout (int): Timeout in ms.

        Returns:
            bytes or None: Response data or None on timeout.

        Raises:
            RuntimeError: On invalid response or unexpected command.

        Notes:
            Calling will perform I2C/SPI/UART read operation， Not ISR-safe.
        """
        if not self._wait_ready(timeout):
            return None
        # Read response bytes.
        response = self._read_frame(response_length + 2)
        # Check that response is for the called function.
        if not (response[0] == _PN532TOHOST and response[1] == (command + 1)):
            raise RuntimeError("Received unexpected command response!")
        # Return response data.
        return response[2:]

    def power_down(self) -> bool:
        """
        将 PN532 置于低功耗状态。

        如果 reset 引脚连接，则执行硬件断电；否则执行软断电（启用唤醒功能）。

        Returns:
            bool: 如果成功进入低功耗状态返回 True，否则返回 False。

        Notes:
            调用会操作 GPIO/I2C/SPI/UART。
            软件断电时，会发送 POWERDOWN 命令。

        ==========================================

        Put PN532 into low power state.

        Performs hard power down if reset pin is connected; otherwise soft power down.

        Returns:
            bool: True if powered down successfully, False otherwise.

        Notes:
            Soft power down sends POWERDOWN command.
        """
        # Hard Power Down if the reset pin is connected
        if self._reset_pin:
            self._reset_pin.value = False
            self.low_power = True
        else:
            # Soft Power Down otherwise. Enable wakeup on I2C, SPI, UART
            response = self.call_function(_COMMAND_POWERDOWN, params=[0xB0, 0x00])
            self.low_power = response[0] == 0x00
        time.sleep(0.005)
        return self.low_power

    @property
    def firmware_version(self) -> bytes:
        """
        获取 PN532 固件版本。

        Returns:
            tuple: 固件版本信息 (IC, Ver, Rev, Support)。

        Raises:
            RuntimeError: 固件版本读取失败。

        Notes:
            调用内部会发送 GETFIRMWAREVERSION 命令。

        ==========================================

        Return PN532 firmware version.

        Returns:
            tuple: Firmware version (IC, Ver, Rev, Support).

        Raises:
            RuntimeError: Failed to read firmware version.

        Notes:
            The call will send the GETFIRMWAREVERSION command internally
        """
        response = self.call_function(_COMMAND_GETFIRMWAREVERSION, 4, timeout=500)
        if response is None:
            raise RuntimeError("Failed to detect the PN532")
        return response

    def SAM_configuration(self):
        """
        配置 PN532 用于 MiFare 卡读取。

        Notes:
            调用内部会发送 SAMCONFIGURATION 命令。

        ==========================================

        Configure PN532 for MiFare card reading.

        Notes:
            The call will send the SAMCONFIGURATION command internally.
        """
        self.call_function(_COMMAND_SAMCONFIGURATION, params=[0x01, 0x14, 0x01])

    # ------------- 读卡 / Mifare -------------
    def read_passive_target(self, card_baud=_MIFARE_ISO14443A, timeout=1000) -> bytes | None:
        """
        读取被动目标卡（被动感应卡）。

        Args:
            card_baud (int): 卡片通信速率，默认为 ISO14443A。
            timeout (int): 等待响应超时时间，单位 ms。

        Returns:
            bytes 或 None: 卡片 UID，如果无卡或超时返回 None。

        Notes:
            内部调用 listen_for_passive_target 和 get_passive_target。

        ==========================================

        Read passive target card.

        Args:
            card_baud (int): Card baud rate, default ISO14443A.
            timeout (int): Timeout in ms.

        Returns:
            bytes or None: Card UID or None if no card detected.

        Notes:
            NInternally calls listen_for_passive_target and get_passive_target.
        """
        response = self.listen_for_passive_target(card_baud=card_baud, timeout=timeout)
        if not response:
            return None
        return self.get_passive_target(timeout=timeout)

    def listen_for_passive_target(self, card_baud=_MIFARE_ISO14443A, timeout=1) -> bytes | bool:
        """
        监听被动目标卡，返回是否检测到响应。

        Args:
            card_baud (int): 卡片通信速率，默认为 ISO14443A。
            timeout (int): 等待响应超时时间，单位 ms。

        Returns:
            bytes 或 bool: 响应数据，如果忙返回 False。

        Notes:
            内部调用 send_command。

        ==========================================

        Listen for passive target card.

        Args:
            card_baud (int): Card baud rate, default ISO14443A.
            timeout (int): Timeout in ms.

        Returns:
            bytes or bool: Response data, False if busy.

        Notes:
            Internally calls send_command.
        """
        response = self.send_command(_COMMAND_INLISTPASSIVETARGET, params=[0x01, card_baud], timeout=timeout)
        return response

    def get_passive_target(self, timeout=1000) -> bytes | None:
        """
        获取被动目标卡 UID。

        Args:
            timeout (int): 等待响应超时时间，单位 ms。

        Returns:
            bytes 或 None: 卡片 UID，如果无卡返回 None。

        Raises:
            RuntimeError: 检测到多张卡或 UID 长度异常。

        Notes:
            内部调用 process_response。
            非 ISR-safe。

        ==========================================

        Get passive target card UID.

        Args:
            timeout (int): Timeout in ms.

        Returns:
            bytes or None: Card UID or None if no card.

        Raises:
            RuntimeError: More than one card or unexpected UID length.

        Notes:
            Internally calls process_response
            Not ISR-safe.
        """
        response = self.process_response(_COMMAND_INLISTPASSIVETARGET, response_length=30, timeout=timeout)
        if response is None:
            return None
        if response[0] != 0x01:
            raise RuntimeError("More than one card detected")
        if response[5] > 7:
            raise RuntimeError("Unexpected long UID")
        return response[6 : 6 + response[5]]

    # ------------- Mifare Classic -------------
    def mifare_classic_authenticate_block(self, uid, block_number, key_number, key) -> bool:
        """
        验证 Mifare Classic 指定块的访问权限。

        Args:
            uid (bytes): 卡片 UID。
            block_number (int): 块号。
            key_number (int): 密钥编号（0=A, 1=B）。
            key (bytes): 密钥 6 字节。

        Returns:
            bool: 验证是否成功。

        Notes:
            Internal call call_function。
            `params` 内部构造为 bytearray，虽然写法类似 list，但实际上类型是 bytearray，不是 list。

        ==========================================

        Authenticate a Mifare Classic block.

        Args:
            uid (bytes): Card UID.
            block_number (int): Block number.
            key_number (int): Key type (0=A, 1=B).
            key (bytes): 6-byte key.

        Returns:
            bool: True if authentication succeeded.

        Notes:
            Internal call call_function.
            `params` is constructed as a bytearray, not a list.
        """
        uidlen, keylen = len(uid), len(key)
        params = bytearray(3 + uidlen + keylen)
        params[0] = 0x01
        params[1] = key_number & 0xFF
        params[2] = block_number & 0xFF
        params[3 : 3 + keylen] = key
        params[3 + keylen :] = uid
        response = self.call_function(_COMMAND_INDATAEXCHANGE, params=params, response_length=1)
        return response[0] == 0x00

    def mifare_classic_read_block(self, block_number) -> bytes | None:
        """
        读取 Mifare Classic 指定块的数据。

        Args:
            block_number (int): 要读取的块号。

        Returns:
            bytes or None: 读取到的块数据（16 字节），失败返回 None。

        Notes:
            内部调用 call_function 方法。

        ==========================================

        Read data from a specific Mifare Classic block.

        Args:
            block_number (int): Block number to read.

        Returns:
            bytes or None: Block data (16 bytes) or None if failed.

        Notes:
            Calls call_function internally.
        """
        response = self.call_function(_COMMAND_INDATAEXCHANGE, params=[0x01, MIFARE_CMD_READ, block_number & 0xFF], response_length=17)
        if response[0] != 0x00:
            return None
        return response[1:]

    def mifare_classic_write_block(self, block_number, data) -> bool:
        """
        写入 Mifare Classic 指定块的数据。

        Args:
            block_number (int): 要写入的块号。
            data (bytes): 块数据，必须 16 字节。

        Returns:
            bool: 写入是否成功。

        Raises:
            ValueError: 当数据长度不为 16 字节。

        Notes:
            内部调用 call_function 方法。
            `params` 内部构造为 bytearray，虽然写法类似 list，但实际上类型是 bytearray，不是 list。

        ==========================================

        Write data to a specific Mifare Classic block.

        Args:
            block_number (int): Block number to write.
            data (bytes): Block data, must be 16 bytes.

        Returns:
            bool: True if write successful, False otherwise.

        Raises:
            valueError: If data length is not 16 bytes.

        Notes:
            Calls call_function internally.
            `params` is constructed as a bytearray, not a list.
        """
        if data is None or len(data) != 16:
            raise ValueError("Data must be 16 bytes")
        params = bytearray([0x01, MIFARE_CMD_WRITE, block_number & 0xFF] + list(data))
        response = self.call_function(_COMMAND_INDATAEXCHANGE, params=params, response_length=1)
        return response[0] == 0x00

    # ------------- NTAG 2XX -------------
    def ntag2xx_write_block(self, block_number, data) -> bool:
        """
        写入 NTAG 2XX 指定块的数据。

        Args:
            block_number (int): 要写入的块号。
            data (bytes): 块数据，必须 4 字节。

        Returns:
            bool: 写入是否成功。

        Raises:
            ValueError: 当数据长度不为 4 字节。

        Notes:
            内部调用 call_function 方法。
            `params` 内部构造为 bytearray，虽然写法类似 list，但实际上类型是 bytearray，不是 list。

        ==========================================

        Write data to a specific NTAG 2XX block.

        Args:
            block_number (int): Block number to write.
            data (bytes): Block data, must be 4 bytes.

        Returns:
            bool: True if write successful, False otherwise.

        Raises:
            ValueError: If data length is not 4 bytes.

        Notes:
            Calls call_function internally.
            `params` is constructed as a bytearray, not a list.
        """
        if data is None or len(data) != 4:
            raise ValueError("Data must be 4 bytes")
        params = bytearray([0x01, MIFARE_ULTRALIGHT_CMD_WRITE, block_number & 0xFF] + list(data))
        response = self.call_function(_COMMAND_INDATAEXCHANGE, params=params, response_length=1)
        return response[0] == 0x00

    def ntag2xx_read_block(self, block_number) -> bytes | None:
        """
        读取 NTAG 2XX 指定块的数据。

        Args:
            block_number (int): 要读取的块号。

        Returns:
            bytes or None: 块数据（4 字节），失败返回 None。

        Notes:
            内部调用 mifare_classic_read_block 方法。

        ==========================================

        Read data from a specific NTAG 2XX block.

        Args:
            block_number (int): Block number to read.

        Returns:
            bytes or None: Block data (4 bytes) or None if failed.

        Notes:
            Calls mifare_classic_read_block internally.
        """
        ntag_block = self.mifare_classic_read_block(block_number)
        if ntag_block is not None:
            return ntag_block[0:4]
        return None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
