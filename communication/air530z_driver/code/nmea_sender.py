# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : ben0i0d
# @File    : nmea_sender.py
# @Description : nmea驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC YB-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from time import ticks_diff
from machine import Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class NMEASender:
    """
    NMEASender 类，用于生成并封装通用 NMEA 配置指令字符串。  
    提供波特率、更新率、协议模式、系统模式、开机启动模式等配置命令的构造方法，  
    并支持产品信息查询。  

    本类仅负责生成带有校验和的完整 NMEA 指令字符串，不涉及 UART/串口的发送操作。  

    Methods:
        _checksum(sentence: str) -> str:
            计算 NMEA 指令的校验和（XOR 方式）。
        _build(body: str) -> str:
            构造完整的 NMEA 指令（包含起始符 '$'、校验和 '*'）。
        set_baudrate(baud: int) -> str:
            生成设置波特率的 NMEA 指令。
        set_update_rate(rate: int) -> str:
            生成设置更新率的 NMEA 指令。
        set_protocol(mode: int) -> str:
            生成设置协议模式的 NMEA 指令。
        set_system_mode(mode: int) -> str:
            生成设置系统工作模式的 NMEA 指令。
        set_startup_mode(mode: int) -> str:
            生成设置开机启动模式的 NMEA 指令。
        query_product_info() -> str:
            生成查询产品信息的 NMEA 指令。

    ==========================================

    NMEASender class for constructing general NMEA configuration commands.  
    Provides methods to generate commands for baud rate, update rate, protocol  
    mode, system mode, startup mode, and product info query.  

    This class only generates valid NMEA sentences with checksums,  
    but does not handle UART/serial transmission.  

    Methods:
        _checksum(sentence: str) -> str:
            Compute NMEA checksum (XOR).
        _build(body: str) -> str:
            Build full NMEA sentence (with '$' prefix and '*' checksum).
        set_baudrate(baud: int) -> str:
            Build NMEA command for setting baud rate.
        set_update_rate(rate: int) -> str:
            Build NMEA command for setting update rate.
        set_protocol(mode: int) -> str:
            Build NMEA command for setting protocol mode.
        set_system_mode(mode: int) -> str:
            Build NMEA command for setting system mode.
        set_startup_mode(mode: int) -> str:
            Build NMEA command for setting startup mode.
        query_product_info() -> str:
            Build NMEA command for querying product info.
    """

    @staticmethod
    def _checksum(sentence: str) -> str:
        """
        计算 NMEA 校验和（XOR 累加方式）。  

        Args:
            sentence (str): 不包含起始符 '$' 和校验符号 '*' 的 NMEA 主体字符串。  

        Returns:
            str: 两位大写十六进制校验和字符串。  

        ==========================================
        Compute NMEA checksum using XOR accumulation.  

        Args:
            sentence (str): NMEA body string (without '$' and '*').  

        Returns:
            str: Two-digit uppercase hexadecimal checksum string.
        """
        cs = 0
        for c in sentence:
            cs ^= ord(c)
        return f"{cs:02X}"

    def _build(self, body: str) -> str:
        """
        构造完整的 NMEA 指令字符串。  

        Args:
            body (str): NMEA 指令主体内容，不包含起始符和校验符号。  

        Returns:
            str: 带有起始符 `$` 和校验和 `*` 的完整 NMEA 指令。  

        ==========================================
        Build a complete NMEA sentence string.  

        Args:
            body (str): NMEA command body (without start '$' or checksum '*').  

        Returns:
            str: Full NMEA sentence with '$' prefix and '*' checksum.
        """
        cs = self._checksum(body)
        return f"${body}*{cs}"

    # ---------------- 配置方法 ----------------
    def set_baudrate(self, baud: int) -> str:
        """
        生成设置波特率的 NMEA 指令。  

        Args:
            baud (int): 波特率值，例如 9600, 115200。  

        Returns:
            str: 完整 NMEA 指令字符串。  

        ==========================================
        Build NMEA command for setting baud rate.  

        Args:
            baud (int): Baud rate value (e.g., 9600, 115200).  

        Returns:
            str: Full NMEA command string.
        """
        return self._build(f"PCAS01,{baud}")

    def set_update_rate(self, rate: int) -> str:
        """
        生成设置更新率的 NMEA 指令。  

        Args:
            rate (int): 更新率（单位 Hz）。  

        Returns:
            str: 完整 NMEA 指令字符串。  

        ==========================================
        Build NMEA command for setting update rate.  

        Args:
            rate (int): Update rate (in Hz).  

        Returns:
            str: Full NMEA command string.
        """
        return self._build(f"PCAS02,{rate}")

    def set_protocol(self, mode: int) -> str:
        """
        生成设置协议模式的 NMEA 指令。  

        Args:
            mode (int): 协议模式编号。  

        Returns:
            str: 完整 NMEA 指令字符串。  

        ==========================================
        Build NMEA command for setting protocol mode.  

        Args:
            mode (int): Protocol mode identifier.  

        Returns:
            str: Full NMEA command string.
        """
        return self._build(f"PCAS05,{mode}")

    def set_system_mode(self, mode: int) -> str:
        """
        生成设置系统工作模式的 NMEA 指令。  

        Args:
            mode (int): 系统模式编号。  

        Returns:
            str: 完整 NMEA 指令字符串。  

        ==========================================
        Build NMEA command for setting system mode.  

        Args:
            mode (int): System mode identifier.  

        Returns:
            str: Full NMEA command string.
        """
        return self._build(f"PCAS06,{mode}")

    def set_startup_mode(self, mode: int) -> str:
        """
        生成设置开机启动模式的 NMEA 指令。  

        Args:
            mode (int): 启动模式编号。  

        Returns:
            str: 完整 NMEA 指令字符串。  

        ==========================================
        Build NMEA command for setting startup mode.  

        Args:
            mode (int): Startup mode identifier.  

        Returns:
            str: Full NMEA command string.
        """
        return self._build(f"PCAS07,{mode}")

    def query_product_info(self) -> str:
        """
        生成查询产品信息的 NMEA 指令。  

        Returns:
            str: 完整 NMEA 指令字符串。  

        ==========================================
        Build NMEA command for querying product info.  

        Returns:
            str: Full NMEA command string.
        """
        return self._build("PCAS10,0")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
