# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : ben0i0d
# @File    : hc14_lora.py
# @Description : hc14_lora驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC YB-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
from machine import UART
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class HC14_Lora:
    """
    HC14_Lora 类，用于通过 UART 串口操作 HC14 LoRa 模块，实现参数配置和透明传输通信。  
    封装了 AT 命令交互，提供波特率、信道、发射功率、无线速率等设置接口，  
    并支持透传模式下的数据收发。  

    Attributes:
        _uart (UART): MicroPython UART 实例，用于与 HC14 模块通信。
        baud (int): 当前串口波特率（默认 9600，可查询/设置）。
        channel (int): 当前无线信道编号（1–50）。
        rate (int): 当前无线速率 S 值（1–8）。
        power (int): 当前发射功率（dBm，6–20）。
        firmware_version (str): 模块固件版本信息字符串。
        in_at_mode (bool): 模块是否处于 AT 命令模式。
        _line_terminator (bytes): AT 命令行结束符（默认 b'\\r\\n'）。

    Methods:
        __init__(uart, baud=9600, line_terminator=b'\\r\\n'):
            初始化驱动类，绑定 UART 并设置默认参数。
        test_comm() -> (bool, str|None):
            测试 AT 通信是否正常。
        reset_defaults() -> (bool, str|None):
            恢复出厂设置。
        get_baud() / set_baud(baud):
            查询/设置模块波特率。
        get_channel() / set_channel(ch):
            查询/设置信道。
        get_rate() / set_rate(s):
            查询/设置无线速率。
        get_power() / set_power(p_dbm):
            查询/设置发射功率。
        get_version():
            获取固件版本信息。
        get_params():
            一次性查询并返回所有关键参数。
        transparent_send(data, wait_between_packets_s=0.01):
            透明传输模式下发送数据（自动分包）。
        transparent_recv(max_total_bytes=1024):
            透明传输模式下接收数据。
        close():
            关闭串口资源。

    ==========================================

    HC14_Lora driver class for controlling HC14 LoRa module via UART.  
    Provides AT command communication methods for configuring parameters  
    such as baud rate, channel, RF rate, transmit power, and supports  
    transparent data transmission and reception.  

    Attributes:
        _uart (UART): MicroPython UART instance for communication.
        baud (int): Current UART baud rate (default 9600).
        channel (int): Current RF channel (1–50).
        rate (int): Current RF rate S value (1–8).
        power (int): Current transmit power (dBm, 6–20).
        firmware_version (str): Firmware version string.
        in_at_mode (bool): Whether module is in AT command mode.
        _line_terminator (bytes): AT command line terminator (default b'\\r\\n').

    Methods:
        __init__(uart, baud=9600, line_terminator=b'\\r\\n'):
            Initialize driver class with UART and defaults.
        test_comm() -> (bool, str|None):
            Test if AT communication works.
        reset_defaults() -> (bool, str|None):
            Restore factory settings.
        get_baud() / set_baud(baud):
            Query/set module baud rate.
        get_channel() / set_channel(ch):
            Query/set RF channel.
        get_rate() / set_rate(s):
            Query/set RF rate.
        get_power() / set_power(p_dbm):
            Query/set TX power.
        get_version():
            Get firmware version string.
        get_params():
            Query all key parameters at once.
        transparent_send(data, wait_between_packets_s=0.01):
            Send data in transparent mode (with auto packetization).
        transparent_recv(max_total_bytes=1024):
            Receive data in transparent mode.
        close():
            Close UART resource.
    """

    # 波特率常量
    BAUD_1200  = const(1200)
    BAUD_2400  = const(2400)
    BAUD_4800  = const(4800)
    BAUD_9600  = const(9600)
    BAUD_19200 = const(19200)
    BAUD_38400 = const(38400)
    BAUD_57600 = const(57600)
    BAUD_115200= const(115200)
    BAUD_DEFAULT = BAUD_9600

    # 无线速率 S 值常量（1..8）
    S1 = const(1); S2 = const(2); S3 = const(3); S4 = const(4)
    S5 = const(5); S6 = const(6); S7 = const(7); S8 = const(8)
    S_DEFAULT = S3

    # 发射功率范围与默认
    POWER_MIN = const(6)    # dBm
    POWER_MAX = const(20)   # dBm
    POWER_DEFAULT = const(20)

    # 信道范围与默认（编号为整数 1..50）
    CH_MIN = const(1)
    CH_MAX = const(50)
    CH_DEFAULT = const(28)

    # 透明传输：每个无线速率每包最大字节数（厂商说明）
    # 注意这里用 const 的值放在 dict 中（dict 的值也为 const）
    MAX_PAYLOAD_PER_RATE = {
        1: const(40),
        2: const(40),
        3: const(80),
        4: const(80),
        5: const(160),
        6: const(160),
        7: const(250),
        8: const(250),
    }

    # 私有：接收超时时间（秒），固定 3s（接口要求）
    _RECV_TIMEOUT_S = const(3)

    def __init__(self, uart : UART, baud: int = BAUD_DEFAULT):
        """
        初始化 HC14_Lora 驱动类，绑定 UART 并设置默认参数。

        Args:
            uart (UART): 已打开的 MicroPython UART 实例。
            baud (int, optional): 串口波特率，默认 9600。
            line_terminator (bytes, optional): AT 命令行结束符，默认 b'\\r\\n'。

        Notes:
            初始化时不主动查询模块，仅配置内部缓存：
            baud/rate/power/channel/firmware_version。
        ==========================================
        Initialize HC14_Lora driver, bind UART and set default parameters.

        Args:
            uart (UART): Opened MicroPython UART instance.
            baud (int, optional): UART baud rate, default 9600.
            line_terminator (bytes, optional): AT command line terminator, default b'\\r\\n'.

        Notes:
            Does not query module on init, only sets internal cache:
            baud/rate/power/channel/firmware_version.
        """

        self._uart = uart
        self.in_at_mode = False
        self.baud = baud
        self.rate = HC14_Lora.S_DEFAULT
        self.power = HC14_Lora.POWER_DEFAULT
        self.channel = HC14_Lora.CH_DEFAULT
        self.firmware_version = ''

    def _send(self, cmd: bytes) -> (bool, None|str):
        """
        向模块发送 AT 命令

        Args:
            cmd (bytes): 待发送的数据。
            append_lt (bool, optional): 是否自动追加行结束符，默认 True。

        Returns:
            Tuple[bool, None|str]: 成功返回 (True, None)，失败返回 (False, "io error")。

        Notes:
            低级私有方法，直接调用 UART.write。
        ==========================================
        Send AT command to the module.

        Args:
            cmd (bytes): Data to send.
            append_lt (bool, optional): Whether to append line terminator, default True.

        Returns:
            Tuple[bool, None|str]: (True, None) if success, (False, "io error") if failure.

        Notes:
            Low-level private method, directly writes to UART.
        """

        try:
            self._uart.write(cmd)
            # 50ms 确保回传稳定
            time.sleep(0.05)
            return (True, None)
        except Exception as e:
            return (False, "send error")

    def _recv(self) -> (bool, None|str):
        """
        从模块接收数据

        Returns:
            Tuple[bool, None|str]: 成功返回 (True, 接收到的 bytes)，
                                超时或错误返回 (False, "timeout"/错误信息)。

        Notes:
            低级私有方法，直接调用 UART.read。
        ==========================================
        Receive data from the module

        Returns:
            Tuple[bool, None|str]: (True, received bytes) if success,m
                                (False, "timeout"/error) if failed.

        Notes:
            Low-level private method, directly reads from UART.
        """
        try:
            resp = self._uart.read()
            if resp == None:
                return False,'RECV NONE'
            if resp.decode('utf-8').strip() == 'ORDER ERROR':
                return False,'ORDER ERROR'
            try:
                return True,resp.decode('utf-8').strip().split(':')[1]
            except:
                return True,resp.decode('utf-8').strip()
        except Exception as e:
            return (False, "recv error")

    def test_comm(self) -> (bool, None|str):
        """
        发送 `AT` 测试模块是否进入 AT 模式。

        Returns:
            Tuple[bool, None|str]: 成功返回 (True, None)，
                                失败返回 (False, "timeout"/"unexpected resp")。

        Notes:
            调用 _send + _recv 完成测试，成功后设置 self.in_at_mode = True。
        ==========================================
        Send `AT` command to test if module enters AT mode.

        Returns:
            Tuple[bool, None|str]: (True, None) if success,
                                (False, "timeout"/"unexpected resp") if failed.

        Notes:
            Uses _send + _recv to perform test. Sets self.in_at_mode = True if successful.
        """

        ok, err = self._send(f'AT'.encode())
        if not ok: return (False, err)
        ok, resp = self._recv()
        if not ok:
            return (False, resp)
        if resp == 'OK':return (True, None)
        
    def reset_defaults(self) -> (bool, None|str):
        """
        发送 `AT+DEFAULT` 恢复模块出厂设置。

        Returns:
            Tuple[bool, str|None]: 成功返回 (True, "OK+DEFAULT")，
                                失败返回 (False, 错误信息)。

        Notes:
            成功后调用方应重新同步内部缓存，或内部可调用 get_params。
        ==========================================
        Send `AT+DEFAULT` to restore factory settings.

        Returns:
            Tuple[bool, str|None]: (True, "OK+DEFAULT") if success,
                                (False, error message) if failed.

        Notes:
            Caller should refresh internal cache after success, or get_params can be called internally.
        """

        ok, err = self._send(f'AT+DEFAULT'.encode())
        if not ok: return (False, err)
        ok, resp = self._recv()
        if not ok:
            return (False, resp)
        if resp == 'OK+DEFAULT':return (True, None)

    def get_baud(self) -> (bool, int|str):
        """
        查询模块当前 UART 波特率，发送 `AT+B?` 并解析返回 `OK+B:xxxx`。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, baud)，
                                失败返回 (False, "parse error"/"timeout")。

        Notes:
            不修改本地 UART 配置，仅返回模块设置；如需切换请调用 set_baud。
        ==========================================
        Query module current UART baud rate by sending `AT+B?` and parsing `OK+B:xxxx`.

        Returns:
            Tuple[bool, int|str]: (True, baud) if success,
                                (False, "parse error"/"timeout") if failed.

        Notes:
            Does not change local UART, only returns module setting; use set_baud to switch.
        """

        ok, err = self._send(f'AT+B?'.encode())
        if not ok: return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        return True,resp
    
    def set_baud(self, baud: int) -> (bool, int|str):
        """
        设置模块 UART 波特率，发送 `AT+B{baud}`。

        Args:
            baud (int): 目标波特率，必须在 BAUD_* 集合内。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, baud)，失败返回 (False, "invalid param"/"error")。

        Notes:
            成功后需调用方或本方法同步 UART 实例波特率。
        ==========================================
        Set module UART baud rate by sending `AT+B{baud}`.

        Args:
            baud (int): Target baud rate, must be in BAUD_* set.

        Returns:
            Tuple[bool, int|str]: (True, baud) if success, (False, "invalid param"/"error") if failed.

        Notes:
            Caller or this method must sync UART instance baud rate after success.
        """

        if baud not in [HC14_Lora.BAUD_1200,HC14_Lora.BAUD_2400,HC14_Lora.BAUD_4800,
                        HC14_Lora.BAUD_9600,HC14_Lora.BAUD_19200,HC14_Lora.BAUD_38400,
                        HC14_Lora.BAUD_57600,HC14_Lora.BAUD_115200]:
            return (False, "invalid param")
        ok, err = self._send(f'AT+B{baud}'.encode())
        if not ok:return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        self.baud = baud
        return True,resp

    def get_channel(self) -> (bool, int|str):
        """
        查询模块信道，发送 `AT+C?` 并解析返回 `OK+C:xxx`。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, ch)，失败返回 (False, "parse error"/"timeout")。

        Notes:
            返回信道编号 int（1–50）。
        ==========================================
        Query module RF channel by sending `AT+C?` and parsing `OK+C:xxx`.

        Returns:
            Tuple[bool, int|str]: (True, channel) if success, (False, "parse error"/"timeout") if failed.

        Notes:
            Returns integer channel number (1–50).
        """

        ok, err = self._send(f'AT+C?'.encode())
        if not ok: return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        return True,resp

    def set_channel(self, ch: int) -> (bool, int|str):
        """
        设置模块信道，发送 `AT+C{ch:03d}`。

        Args:
            ch (int): 信道编号 1–50。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, ch)，失败返回 (False, "invalid param"/"error")。

        Notes:
            成功后更新 self.channel。
        ==========================================
        Set module RF channel by sending `AT+C{ch:03d}`.

        Args:
            ch (int): Channel number 1–50.

        Returns:
            Tuple[bool, int|str]: (True, ch) if success, (False, "invalid param"/"error") if failed.

        Notes:
            Updates self.channel on success.
        """

        if not (self.CH_MIN <= ch <= self.CH_MAX):
            return (False, "invalid param")
        ok, err = self._send(f'AT+C{ch:03d}'.encode())
        if not ok:return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        self.channel = ch
        return True,resp

    def get_rate(self) -> (bool, int|str):
        """
        查询无线速率 S 值，发送 `AT+S?` 并解析返回 `OK+S:x`。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, s)，失败返回 (False, "parse error"/"timeout")。

        Notes:
            返回值范围 1–8。
        ==========================================
        Query module RF rate S value by sending `AT+S?` and parsing `OK+S:x`.

        Returns:
            Tuple[bool, int|str]: (True, s) if success, (False, "parse error"/"timeout") if failed.

        Notes:
            Returns value in range 1–8.
        """

        ok, err = self._send(f'AT+S?'.encode())
        if not ok: return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        return True,resp

    def set_rate(self, s: int) -> (bool, int|str):
        """
        设置无线速率 S 值，发送 `AT+S{s}`。

        Args:
            s (int): 目标速率 1–8。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, s)，失败返回 (False, "invalid param"/"error")。

        Notes:
            成功后更新 self.rate。
        ==========================================
        Set module RF rate S value by sending `AT+S{s}`.

        Args:
            s (int): Target rate 1–8.

        Returns:
            Tuple[bool, int|str]: (True, s) if success, (False, "invalid param"/"error") if failed.

        Notes:
            Updates self.rate on success.
        """

        if not (1 <= s <= 8):
            return (False, "invalid param")
        ok, err = self._send(f'AT+S{s}'.encode())
        if not ok:return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        self.rate = s
        return True,resp

    def get_power(self) -> (bool, int|str):
        """
        查询发射功率，发送 `AT+P?` 并解析 `OK+P:+XdBm`。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, dBm)，失败返回 (False, "parse error"/"timeout")。

        Notes:
            返回 int 单位 dBm。
        ==========================================
        Query module transmit power by sending `AT+P?` and parsing `OK+P:+XdBm`.

        Returns:
            Tuple[bool, int|str]: (True, dBm) if success, (False, "parse error"/"timeout") if failed.

        Notes:
            Returns integer in dBm.
        """

        ok, err = self._send(f'AT+P?'.encode())
        if not ok: return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        return True,resp

    def set_power(self, p_dbm: int) -> (bool, int|str):
        """
        设置发射功率，发送 `AT+P{p_dbm}`。

        Args:
            p_dbm (int): 功率 dBm，范围 POWER_MIN–POWER_MAX。

        Returns:
            Tuple[bool, int|str]: 成功返回 (True, p_dbm)，失败返回 (False, "invalid param"/"error")。

        Notes:
            成功后更新 self.power。
        ==========================================
        Set module transmit power by sending `AT+P{p_dbm}`.

        Args:
            p_dbm (int): Power in dBm, range POWER_MIN–POWER_MAX.

        Returns:
            Tuple[bool, int|str]: (True, p_dbm) if success, (False, "invalid param"/"error") if failed.

        Notes:
            Updates self.power on success.
        """

        if not (self.POWER_MIN <= p_dbm <= self.POWER_MAX):
            return (False, "invalid param")
        ok, err = self._send(f'AT+P{p_dbm}'.encode())
        if not ok:return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        self.power = p_dbm
        return True,resp

    def get_version(self) -> (bool, str):
        """
        查询模块固件版本，发送 `AT+V`。

        Returns:
            Tuple[bool, str]: 成功返回 (True, firmware_str)，失败返回 (False, 错误信息)。

        Notes:
            成功时更新 self.firmware_version。
        ==========================================
        Query module firmware version by sending `AT+V`.

        Returns:
            Tuple[bool, str]: (True, firmware_str) if success, (False, error message) if failed.

        Notes:
            Updates self.firmware_version on success.
        """

        ok, err = self._send(b'AT+V?')
        if not ok: return (False, err)
        ok, resp = self._recv()
        if not ok:return (False, resp)
        return True,resp

    def get_params(self) -> (bool, dict|str):
        """
        查询模块所有参数，发送 `AT+RX` 并解析多行响应：
        OK+B:..., OK+C:..., OK+S:..., OK+P:...

        Returns:
            Tuple[bool, dict|str]: 成功返回 (True, {'baud':int,'channel':int,'rate':int,'power':int})，
                                失败返回 (False, "timeout or parse error")。

        Notes:
            成功时同步更新内部缓存属性 self.baud/self.channel/self.rate/self.power。
        ==========================================
        Query all module parameters by sending `AT+RX` and parsing multiple lines:
        OK+B:..., OK+C:..., OK+S:..., OK+P:...

        Returns:
            Tuple[bool, dict|str]: (True, {'baud':int,'channel':int,'rate':int,'power':int}) if success,
                                (False, "timeout or parse error") if failed.

        Notes:
            Updates internal cache self.baud/self.channel/self.rate/self.power on success.
        """
        ok, err = self._send(f'AT+RX'.encode())
        if not ok: return (False, err)
        
        try:
            lines = self._uart.read().decode('utf-8').strip().split('\r\n')
            values = [item.split(':')[1] for item in lines if ':' in item]
            return True,{'baud': values[0],'channel': values[1],'rate': values[2],'power': values[3]}
        except:
            return False,'get params error'

    def transparent_send(self, data: bytes, wait_between_packets_s: float = 0.01) -> (bool, dict|str):
        """
        透明传输发送，将任意 bytes 分包并发送。

        Args:
            data (bytes): 待发送数据。
            wait_between_packets_s (float, optional): 分包间隔，默认 0.01s。

        Returns:
            Tuple[bool, dict|str]: 成功返回 (True, {'packets': n, 'bytes_sent': total_bytes})，
                                失败返回 (False, "send error"/异常信息)。

        Notes:
            根据当前 self.rate 从 MAX_PAYLOAD_PER_RATE 取得每包最大字节数 M。
            仅在串口层分包写入，不做高阶重组。
        ==========================================
        Transparent send, split bytes into packets and send.

        Args:
            data (bytes): Data to send.
            wait_between_packets_s (float, optional): Interval between packets, default 0.01s.

        Returns:
            Tuple[bool, dict|str]: (True, {'packets': n, 'bytes_sent': total_bytes}) if success,
                                (False, "send error"/exception) if failed.

        Notes:
            Splits data according to self.rate using MAX_PAYLOAD_PER_RATE. Only splits at UART layer.
        """

        M = self.MAX_PAYLOAD_PER_RATE.get(self.rate, 80)
        try:
            n = 0
            for i in range(0, len(data), M):
                packet = data[i:i+M]
                if self._uart.write(packet) != len(packet):
                    return (False, f"send error, wrote {ok}/{len(packet)} bytes")
                n += 1
                time.sleep(wait_between_packets_s)
            return (True, {"packets":n, "bytes_sent":len(data)})
        except Exception as e:
            return (False, str(e))

    def transparent_recv(self, max_total_bytes: int = 1024, timeout_ms: int = 5000, quiet_ms: int = 2300):
        """
        从 UART 读取并合并分片：当在 quiet_ms 时间内没有新数据到达时返回。
        timeout_ms 为最大等待时间，避免死等。
        """
        t_start = time.ticks_ms()
        last_activity = time.ticks_ms()
        buf = bytearray()

        while True:
            # 有数据就读并重置 last_activity
            if self._uart.any():
                chunk = self._uart.read()  # 读走当前缓冲区内的所有字节
                if chunk:
                    buf.extend(chunk)
                    last_activity = time.ticks_ms()
                    # 如果已达到最大允许字节数，立即返回
                    if len(buf) >= max_total_bytes:
                        return (True, bytes(buf[:max_total_bytes]))
            else:
                # 若无数据，检查 quiet/timeout
                if len(buf) > 0:
                    # 如果在 quiet_ms 内没有新数据，则认为包完整
                    if time.ticks_diff(time.ticks_ms(), last_activity) >= quiet_ms:
                        return (True, bytes(buf))
                # 超时处理：如果起始等待时间超过 timeout_ms 且没有收到任何数据，超时返回
                if time.ticks_diff(time.ticks_ms(), t_start) >= timeout_ms:
                    if len(buf) > 0:
                        return (True, bytes(buf))  # 收到部分数据但超时，还是返回
                    else:
                        return (False, "timeout")
            time.sleep_ms(5)  # 小延时，避免 busy-loop


    def close(self) -> (bool, None|str):
        """
        关闭并释放串口资源（如果实例负责打开串口）。

        Returns:
            Tuple[bool, None|str]: 成功返回 (True, None)，失败返回 (False, 错误信息)。
        ==========================================
        Close and release UART resource (if instance opened it).

        Returns:
            Tuple[bool, None|str]: (True, None) if success, (False, error message) if failed.
        """
        try:
            self._uart.deinit()
            return (True, None)
        except Exception as e:
            return (False, str(e))

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
