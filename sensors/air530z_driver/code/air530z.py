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

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class NMEAParser:
    def __init__(self):
        """
        callback(parsed_dict) -- 当解析到一条 NMEA 句子时被调用（无论有效与否）
        keep_last_fix: 是否缓存最后一次有效位置以便在无卫星时回退
        """
        # last_known_fix: {'time': unix_ts, 'latitude':.., 'longitude':.., 'source': 'GGA'/'RMC', 'raw': '...'}
        self.data = {}

    def feed(self, data):
        """喂入 bytes，自动按行分割并解析（内存友好）"""
        if not data:
            return
        lines = data.splitlines()
        for line in lines:
            parsed = self._parse_line(line.decode('utf-8'))
            # 如果句子提供了有效定位并允许回退，更新缓存
            self.data.update(parsed)

    def _parse_line(self, s):
        out = {'raw': s, 'valid': False, 'type': None, 'has_fix': False}
        if not s.startswith('$'):
            return out

        # checksum 校验（若存在）
        star = s.find('*')
        if star != -1 and star+3 <= len(s):
            given = int(s[star+1:star+3], 16)
            cs = 0
            for ch in s[1:star]:
                cs ^= ord(ch)
            out['valid'] = (cs == given)
            if not out['valid']:
                return out
            body = s[1:star]
        else:
            return out

        fields = body.split(',')
        header = fields[0]
        stype = header[-3:]
        out['type'] = stype

        # 分派解析
        if stype == 'GGA':
            out.update(self._parse_gga(fields))
        elif stype == 'RMC':
            out.update(self._parse_rmc(fields))
        elif stype == 'GSA':
            out.update(self._parse_gsa(fields))
        elif stype == 'GSV':
            out.update(self._parse_gsv(fields))
        else:
            # 未知句子，返回 fields 供上层查看
            out['fields'] = fields[1:]

        ns = out.get('num_satellites')
        if ns == '':
            out['num_satellites'] = 0
        return out

    # ---- 帮助函数 ----
    def _nmea_to_decimal(self, val, hemi):
        """ddmm.mmmm or dddmm.mmmm -> decimal degrees; 返回 None 而不是抛异常"""
        if not val:
            return None
        try:
            # 找小数点
            dot = val.find('.')
            if dot == -1:
                dot = len(val)
            # 分钟部分占 2 位之前（mm.mmmm），因此度数长度 = dot - 2
            deg_len = dot - 2
            if deg_len <= 0:
                return None
            deg = int(val[:deg_len])
            minutes = float(val[deg_len:])
            dec = deg + minutes / 60.0
            if hemi in ('S', 'W'):
                dec = -dec
            return dec
        except Exception:
            return None

    def _parse_time(self, t):
        if not t:
            return None
        try:
            hh = int(t[0:2]); mm = int(t[2:4]); ss = int(t[4:6])
            frac = 0.0
            if '.' in t:
                frac = float('0.' + t.split('.',1)[1])
            return {'hour': hh, 'minute': mm, 'second': ss, 'fraction': frac}
        except:
            return None

    def _parse_date(self, d):
        if not d or len(d) < 6:
            return None
        try:
            day = int(d[0:2]); month = int(d[2:4]); year = int(d[4:6]) + 2000
            return {'day': day, 'month': month, 'year': year}
        except:
            return None

    # ---- 各句子解析（更稳健） ----
    def _parse_gga(self, f):
        # fields index safe access
        out = {}
        out['time'] = self._parse_time(f[1])
        out['latitude'] = self._nmea_to_decimal(f[2], f[3])
        out['longitude'] = self._nmea_to_decimal(f[4], f[5])
        out['fix_quality'] = f[6]
        # 0 或 None 都表示无 fix
        out['num_satellites'] = f[7]
        out['hdop'] = f[8]
        out['altitude'] = f[9]
        return out

    def _parse_rmc(self, f):
        out = {}
        out['time'] = self._parse_time(f[1])
        out['status'] = f[2]
        out['latitude'] = self._nmea_to_decimal(f[3], f[4])
        out['longitude'] = self._nmea_to_decimal(f[5], f[6])
        out['speed_knots'] = f[7]
        out['course_deg'] = f[8]
        out['date'] = self._parse_date(f[9])
        out['mag_var'] = f[10]
        out['mag_var_dir'] = f[11]
        return out

    def _parse_gsa(self, f):
        out = {}
        out['mode'] = f[1]
        out['fix_type'] = f[2]
        sats = []
        for i in range(3, 15):
            if f[i] != '':
                sats.append(f[i])
        out['sv_used'] = sats
        out['pdop'] = f[15]
        out['hdop'] = f[16]
        out['vdop'] = f[17]
        # GSA 可作为判断卫星是否用于定位的辅助信息
        out['num_satellites'] = len(sats)
        return out

    def _parse_gsv(self, f):
        out = {}
        out['num_messages'] = f[1]
        out['message_number'] = int(f[2])
        out['sats_in_view'] = int(f[3])
        
        if out['sats_in_view'] == 0:
            out['sats'] = []
            out['num_satellites'] = 0
            return out
        
        sats = []
        for i in range(4, len(f), 4):
            prn = f[i]
            elev = f[i+1]
            az = f[i+2]
            cnr = f[i+3]
            sats.append({'prn': prn, 'elev': elev, 'az': az, 'cnr': cnr})
        out['sats'] = sats
        out['num_satellites'] = len(sats)
        return out

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

    def _checksum(self, sentence: str) -> str:
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
        return f"${body}*{cs}\r\n"

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

class Air530Z(NMEAParser):
    """
    Air530Z GPS 模块驱动类  
    - 继承自 NMEAParser，用于直接解析 GPS NMEA 数据  
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
    - Inherits from NMEAParser for direct NMEA parsing  
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
    def __init__(self, uart: UART, local_offset: int = 8):
        """
        初始化 Air530Z 模块驱动。  

        Args:
            uart (UART): 用于与 GPS 模块通信的 UART 实例。  

        ==========================================
        Initialize Air530Z driver.  

        Args:
            uart (UART): UART instance for GPS module communication.
        """
        super().__init__()
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
            self._uart.write(f'{sentence}\r\n'.encode())
            return True
        except Exception:
            return False

    def _recv(self) -> str:
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
        try:
            if self._uart.any():
                resp = self._uart.read()
            return True, resp.decode('utf-8', errors='ignore')
        except Exception as e:
            return False,'RECV NONE'

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
