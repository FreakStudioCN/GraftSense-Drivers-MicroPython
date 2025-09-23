# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : ben0i0d
# @File    : air530z.py
# @Description : Air530Z驱动
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC YB-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
from machine import UART
import time
from micropyGPS import MicropyGPS
from nmea_sender import NMEASender

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Air530Z(MicropyGPS):
    """
    Air530Z GPS 模块驱动类  
    - 继承自 MicropyGPS，用于直接解析 GPS NMEA 数据  
    - 内部组合 NMEASender，用于构造并发送配置指令  
    - 提供 UART 通信下的 AT/NMEA 配置方法  
    - 提供实时位置/状态数据解析接口  

    本类既可作为 GPS 数据解析器，也可作为配置控制器使用。  

    Methods:
        _send(sentence: str) -> bool:
            发送一条 NMEA 指令到 GPS 模块。
        _recv(timeout: int = 3) -> str:
            接收一条 GPS 模块返回的 NMEA 响应（默认 3 秒超时）。
        set_baudrate(baudrate: int) -> (bool, str):
            设置模块波特率（9600 / 115200）。
        set_update_rate(rate: int) -> (bool, str):
            设置定位更新率（1Hz / 5Hz / 10Hz）。
        set_protocol(mode: int) -> (bool, str):
            设置协议输出模式（NMEA v4.1 / BDS+GPS / GPS Only）。
        set_system_mode(mode: int) -> (bool, str):
            设置系统工作模式（BDS+GPS / GPS Only / BDS Only）。
        set_startup_mode(mode: int) -> (bool, str):
            设置开机启动模式（冷启动 / 温启动 / 热启动）。
        query_product_info() -> (bool, str):
            查询产品信息（型号、固件版本等）。
        read() -> dict:
            读取并解析实时位置信息（返回字典: latitude, longitude, satellites, altitude, timestamp）。

    ==========================================

    Air530Z GPS module driver class  
    - Inherits from MicropyGPS for direct NMEA parsing  
    - Composes NMEASender to construct and send configuration commands  
    - Provides AT/NMEA configuration APIs over UART  
    - Exposes real-time data parsing interface  

    This class can be used both as a GPS data parser and as a configuration controller.  

    Methods:
        _send(sentence: str) -> bool:
            Send one NMEA command to GPS module.
        _recv(timeout: int = 3) -> str:
            Receive one NMEA response from GPS module (3s timeout by default).
        set_baudrate(baudrate: int) -> (bool, str):
            Set baud rate (9600 / 115200).
        set_update_rate(rate: int) -> (bool, str):
            Set update rate (1Hz / 5Hz / 10Hz).
        set_protocol(mode: int) -> (bool, str):
            Set protocol output mode (NMEA v4.1 / BDS+GPS / GPS Only).
        set_system_mode(mode: int) -> (bool, str):
            Set system working mode (BDS+GPS / GPS Only / BDS Only).
        set_startup_mode(mode: int) -> (bool, str):
            Set startup mode (cold / warm / hot start).
        query_product_info() -> (bool, str):
            Query product information (model, firmware version, etc.).
        read() -> dict:
            Read and parse real-time location info (returns dict: latitude, longitude, satellites, altitude, timestamp).
    """

    # ---------------- 类属性（常量定义） ----------------
    # 波特率
    BAUDRATE_9600 = const(9600)
    BAUDRATE_115200 = const(115200)

    # 定位更新率（Hz）
    UPDATE_1HZ = const(1)
    UPDATE_5HZ = const(5)
    UPDATE_10HZ = const(10)

    # 协议输出类型（CAS05）
    NMEA_V41 = const(2)
    NMEA_BDS_GPS = const(5)
    NMEA_GPS_ONLY = const(9)

    # 工作系统模式
    MODE_BDS_GPS = const(1)
    MODE_GPS_ONLY = const(2)
    MODE_BDS_ONLY = const(3)

    # 启动模式
    COLD_START = const(1)
    WARM_START = const(2)
    HOT_START = const(3)

    # NMEA 消息类型
    MSG_GGA = const(1)
    MSG_GLL = const(2)
    MSG_GSA = const(3)
    MSG_GSV = const(4)
    MSG_RMC = const(5)
    MSG_VTG = const(6)
    MSG_ZDA = const(7)
    MSG_ANT = const(8)
    MSG_DHV = const(9)
    MSG_LPS = const(10)
    MSG_UTC = const(11)
    MSG_GST = const(12)
    MSG_TIM = const(13)

    # ---------------- 初始化 ----------------
    def __init__(self, uart: UART):
        """
        初始化 Air530Z 模块驱动。  

        Args:
            uart (UART): 用于与 GPS 模块通信的 UART 实例。  

        ==========================================
        Initialize Air530Z driver.  

        Args:
            uart (UART): UART instance for GPS module communication.
        """
        super().__init__(timezone=8)  # MicropyGPS 初始化（可根据需求修改时区）
        self._uart = uart
        self._sender = NMEASender()

    # ---------------- 内部方法 ----------------
    def _send(self, sentence: str) -> bool:
        """
        私有方法：发送一条 NMEA 配置指令到 GPS 模块。  

        Args:
            sentence (str): 完整的 NMEA 指令字符串。  

        Returns:
            bool: True 表示发送成功，False 表示失败。  

        ==========================================
        Private method: Send an NMEA command to GPS module.  

        Args:
            sentence (str): Full NMEA command string.  

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        try:
            self._uart.write(sentence + "\r\n")
            return True
        except Exception:
            return False

    def _recv(self, timeout=3) -> str:
        """
        私有方法：接收 GPS 模块返回的 NMEA 响应。  

        Args:
            timeout (int): 超时时间，默认 3 秒。  

        Returns:
            str: 返回的 NMEA 响应字符串，若超时则返回空字符串。  

        ==========================================
        Private method: Receive NMEA response from GPS module.  

        Args:
            timeout (int): Timeout duration in seconds (default 3).  

        Returns:
            str: Received NMEA response string, or empty string if timeout.
        """
        start = time.time()
        buffer = b""
        while time.time() - start < timeout:
            if self._uart.any():
                buffer += self._uart.read()
                if buffer.endswith(b"\r\n"):
                    return buffer.decode(errors="ignore")
        return ""

    # ---------------- API 方法 ----------------
    def set_baudrate(self, baudrate: int) -> (bool, str):
        """
        设置 GPS 模块波特率。  

        Args:
            baudrate (int): 波特率值，仅支持 9600 或 115200。  

        Returns:
            tuple(bool, str): (是否成功发送, 对应的 NMEA 指令字符串或错误信息)  

        ==========================================
        Set GPS module baud rate.  

        Args:
            baudrate (int): Baud rate (supports 9600 or 115200).  

        Returns:
            tuple(bool, str): (Success flag, NMEA command or error message)
        """
        if baudrate not in (self.BAUDRATE_9600, self.BAUDRATE_115200):
            return False, "Invalid baudrate"
        cmd = self._sender.set_baudrate(baudrate)
        ok = self._send(cmd)
        return ok, cmd

    def set_update_rate(self, rate: int) -> (bool, str):
        """
        设置定位更新率（Hz）。  

        Args:
            rate (int): 更新率值，仅支持 1Hz、5Hz、10Hz。  

        Returns:
            tuple(bool, str): (是否成功发送, 对应的 NMEA 指令字符串或错误信息)  

        ==========================================
        Set GPS update rate (Hz).  

        Args:
            rate (int): Update rate (supports 1Hz, 5Hz, 10Hz).  

        Returns:
            tuple(bool, str): (Success flag, NMEA command or error message)
        """
        if rate not in (self.UPDATE_1HZ, self.UPDATE_5HZ, self.UPDATE_10HZ):
            return False, "Invalid update rate"
        cmd = self._sender.set_update_rate(rate)
        ok = self._send(cmd)
        return ok, cmd

    def set_protocol(self, mode: int) -> (bool, str):
        """
        设置协议模式（NMEA 输出格式）。  

        Args:
            mode (int): 协议模式编号，仅支持 V4.1、BDS+GPS、GPS Only。  

        Returns:
            tuple(bool, str): (是否成功发送, 对应的 NMEA 指令字符串或错误信息)  

        ==========================================
        Set NMEA protocol mode.  

        Args:
            mode (int): Protocol mode (supports V4.1, BDS+GPS, GPS Only).  

        Returns:
            tuple(bool, str): (Success flag, NMEA command or error message)
        """
        if mode not in (self.NMEA_V41, self.NMEA_BDS_GPS, self.NMEA_GPS_ONLY):
            return False, "Invalid protocol mode"
        cmd = self._sender.set_protocol(mode)
        ok = self._send(cmd)
        return ok, cmd

    def set_system_mode(self, mode: int) -> (bool, str):
        """
        设置工作系统模式（卫星系统选择）。  

        Args:
            mode (int): 模式编号，仅支持 BDS+GPS、GPS Only、BDS Only。  

        Returns:
            tuple(bool, str): (是否成功发送, 对应的 NMEA 指令字符串或错误信息)  

        ==========================================
        Set working system mode (satellite system selection).  

        Args:
            mode (int): Mode (supports BDS+GPS, GPS Only, BDS Only).  

        Returns:
            tuple(bool, str): (Success flag, NMEA command or error message)
        """
        if mode not in (self.MODE_BDS_GPS, self.MODE_GPS_ONLY, self.MODE_BDS_ONLY):
            return False, "Invalid system mode"
        cmd = self._sender.set_system_mode(mode)
        ok = self._send(cmd)
        return ok, cmd

    def set_startup_mode(self, mode: int) -> (bool, str):
        """
        设置开机启动模式。  

        Args:
            mode (int): 模式编号，仅支持冷启动、温启动、热启动。  

        Returns:
            tuple(bool, str): (是否成功发送, 对应的 NMEA 指令字符串或错误信息)  

        ==========================================
        Set startup mode.  

        Args:
            mode (int): Mode (supports cold, warm, hot start).  

        Returns:
            tuple(bool, str): (Success flag, NMEA command or error message)
        """
        if mode not in (self.COLD_START, self.WARM_START, self.HOT_START):
            return False, "Invalid startup mode"
        cmd = self._sender.set_startup_mode(mode)
        ok = self._send(cmd)
        return ok, cmd

    def query_product_info(self) -> (bool, str):
        """
        查询产品信息（型号、固件版本等）。  

        Returns:
            tuple(bool, str): (是否成功发送, 模块返回的响应字符串)  

        ==========================================
        Query product information (model, firmware version, etc.).  

        Returns:
            tuple(bool, str): (Success flag, response string from module)
        """
        cmd = self._sender.query_product_info()
        ok = self._send(cmd)
        response = self._recv()
        return ok, response

    # ---------------- 实时数据接口 ----------------
    def read(self) -> dict:
        """
        读取并解析 GPS 实时数据。  
        - 自动从 UART 接收 NMEA 字符串  
        - 调用 MicropyGPS 的 update 方法逐字符解析  
        - 返回包含位置信息的字典  

        Returns:
            dict: 包含以下字段:  
                - latitude (float): 纬度  
                - longitude (float): 经度  
                - satellites (int): 正在使用的卫星数量  
                - altitude (float): 海拔高度（米）  
                - timestamp (tuple): 时间戳 (h, m, s)  

        ==========================================
        Read and parse GPS real-time data.  
        - Reads NMEA sentences from UART  
        - Parses them using MicropyGPS `update` method  
        - Returns a dictionary of position information  

        Returns:
            dict: Fields include:  
                - latitude (float): Latitude  
                - longitude (float): Longitude  
                - satellites (int): Number of satellites in use  
                - altitude (float): Altitude (meters)  
                - timestamp (tuple): Timestamp (h, m, s)
        """
        if self._uart.any():
            data = self._uart.read()
            for b in data:
                self.update(chr(b))  # MicropyGPS 的 update 方法解析单个字符

        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "satellites": self.satellites_in_use,
            "altitude": self.altitude,
            "timestamp": self.timestamp
        }

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
