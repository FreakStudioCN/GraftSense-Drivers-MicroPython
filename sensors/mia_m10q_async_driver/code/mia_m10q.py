# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Michael Calvin McCoy (calvin.mccoy@protonmail.com)
# @File    : mia_m10q.py
# @Description : NMEA GPS 句子解析器，适用于 MIA-M10Q 等 UART NMEA GNSS 模块（仅 NMEA，非 UBX 全协议驱动）
# @License : MIT

__version__ = "1.0.0"
__author__ = "Michael Calvin McCoy (calvin.mccoy@protonmail.com)"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from math import floor, modf

try:
    import utime as _utime
except ImportError:
    _utime = None

try:
    import time as _time
except ImportError:
    _time = None

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


# ======================================== 全局变量 ============================================

# 半球迷宫方向枚举
# Hemisphere direction enumeration
_HEMISPHERES = const(("N", "S", "E", "W"))

# 定位状态枚举
# Fix status enumeration
_FIX_NO_FIX = const(1)
_FIX_2D = const(2)
_FIX_3D = const(3)

# 罗盘方向枚举
# Compass direction enumeration
_COMPASS_DIRECTIONS = const(("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"))

# 月份名称枚举
# Month name enumeration
_MONTHS = const(("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"))

# NMEA 句子最大字符数（以 GGA 句子为基础）
# Maximum NMEA sentence character count (based on GGA sentence)
_SENTENCE_LIMIT = const(90)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MicropyGPS(object):
    """
    NMEA GPS 句子解析器，适用于 MIA-M10Q 等 UART NMEA GNSS 模块
    逐字符解析 NMEA 句子，存储 GPS 数据（时间、位置、速度、卫星信息等）
    仅支持 NMEA 协议，非 u-blox UBX 全协议驱动
    Attributes:
        timestamp (list): UTC 时间戳 [小时, 分钟, 秒]
        date (list): 日期 [日, 月, 年]
        latitude (list): 格式化后的纬度数据
        longitude (list): 格式化后的经度数据
        speed (list): 速度 [节, mph, km/h]
        course (float): 航向角度
        altitude (float): 海拔高度（米）
        satellites_in_view (int): 可见卫星数
        satellites_in_use (int): 已用卫星数
        hdop (float): 水平精度因子
        valid (bool): 定位数据是否有效
    Methods:
        update(new_char): 逐字符输入解析 NMEA 句子
        latitude_string(): 返回格式化纬度字符串
        longitude_string(): 返回格式化经度字符串
        speed_string(unit): 返回格式化速度字符串
        date_string(formatting, century): 返回格式化日期字符串
        compass_direction(): 返回当前航向罗盘方向
        time_since_fix(): 返回距上次定位的时间（毫秒）
        deinit(): 重置解析器状态
    Notes:
        - 仅支持 NMEA 协议，不提供 UBX 配置功能
        - UART 读写和超时控制由调用方在 main.py 中实现
        - 兼容 MicroPython 和标准 Python
    ==========================================
    NMEA GPS sentence parser for MIA-M10Q and similar UART NMEA GNSS modules.
    Parses NMEA sentences character by character, storing GPS data (time, position, speed, satellites, etc.).
    NMEA-only protocol support, NOT a full u-blox UBX driver.
    Attributes:
        timestamp (list): UTC timestamp [hours, minutes, seconds]
        date (list): Date [day, month, year]
        latitude (list): Formatted latitude data
        longitude (list): Formatted longitude data
        speed (list): Speed [knots, mph, km/h]
        course (float): Course bearing
        altitude (float): Altitude in meters
        satellites_in_view (int): Satellites visible
        satellites_in_use (int): Satellites used for fix
        hdop (float): Horizontal dilution of precision
        valid (bool): Whether position data is valid
    Methods:
        update(new_char): Feed characters one at a time to parse NMEA sentences
        latitude_string(): Return formatted latitude string
        longitude_string(): Return formatted longitude string
        speed_string(unit): Return formatted speed string
        date_string(formatting, century): Return formatted date string
        compass_direction(): Return current course as compass direction
        time_since_fix(): Return time since last fix in milliseconds
        deinit(): Reset parser state
    Notes:
        - NMEA-only protocol support, no UBX configuration capability
        - UART read/write and timeout control handled by caller in main.py
        - Compatible with both MicroPython and standard Python
    """

    def __init__(self, local_offset: int = 0, location_formatting: str = "ddm", debug: bool = False) -> None:
        """
        初始化 GPS 解析器实例
        Args:
            local_offset (int): 与 UTC 的时区偏移（小时），默认 0
            location_formatting (str): 坐标显示格式
                - 'ddm': 度分 (Decimal Degree Minute) - 40° 26.767' N
                - 'dms': 度分秒 (Degrees Minutes Seconds) - 40° 26' 46" N
                - 'dd': 十进制度 (Decimal Degrees) - 40.446° N
            debug (bool): 是否启用调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: location_formatting 值无效
        Notes:
            - 初始化后需通过 update() 方法逐字符输入 NMEA 数据进行解析
        ==========================================
        Initialize GPS parser instance.
        Args:
            local_offset (int): Timezone offset from UTC in hours, default 0
            location_formatting (str): Coordinate display format
                - 'ddm': Decimal Degree Minute - 40° 26.767' N
                - 'dms': Degrees Minutes Seconds - 40° 26' 46" N
                - 'dd': Decimal Degrees - 40.446° N
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: Invalid location_formatting value
        Notes:
            - After init, feed NMEA characters via update() to parse
        """
        if location_formatting not in ("ddm", "dms", "dd"):
            raise ValueError("location_formatting must be 'ddm', 'dms', or 'dd', got %s" % location_formatting)

        self._debug = debug

        # 状态标志位 / Status flags
        self.sentence_active = False
        self.active_segment = 0
        self.process_crc = False
        self.gps_segments = []
        self.crc_xor = 0
        self.char_count = 0
        self.fix_time = 0

        # 句子统计 / Sentence statistics
        self.crc_fails = 0
        self.clean_sentences = 0
        self.parsed_sentences = 0

        # 日志相关 / Logging
        self.log_handle = None
        self.log_en = False

        # 定位与运动 / Position and motion
        self.timestamp = [0, 0, 0.0]
        self.date = [0, 0, 0]
        self.local_offset = local_offset
        self._latitude = [0, 0.0, "N"]
        self._longitude = [0, 0.0, "W"]
        self.coord_format = location_formatting
        self.speed = [0.0, 0.0, 0.0]
        self.course = 0.0
        self.altitude = 0.0
        self.geoid_height = 0.0

        # 卫星信息 / Satellite info
        self.satellites_in_view = 0
        self.satellites_in_use = 0
        self.satellites_used = []
        self.last_sv_sentence = 0
        self.total_sv_sentences = 0
        self.satellite_data = dict()
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0
        self.valid = False
        self.fix_stat = 0
        self.fix_type = _FIX_NO_FIX

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        ==========================================
        Debug log output.
        """
        if self._debug:
            print("[MicropyGPS] %s" % msg)

    # ==========================================
    # 坐标格式化属性 / Coordinate format properties
    # ==========================================

    @property
    def latitude(self):
        """
        返回格式化后的纬度数据
        ==========================================
        Return formatted latitude data.
        """
        if self.coord_format == "dd":
            decimal_degrees = self._latitude[0] + (self._latitude[1] / 60)
            return [decimal_degrees, self._latitude[2]]
        elif self.coord_format == "dms":
            minute_parts = modf(self._latitude[1])
            seconds = round(minute_parts[0] * 60)
            return [self._latitude[0], int(minute_parts[1]), seconds, self._latitude[2]]
        else:
            return self._latitude

    @property
    def longitude(self):
        """
        返回格式化后的经度数据
        ==========================================
        Return formatted longitude data.
        """
        if self.coord_format == "dd":
            decimal_degrees = self._longitude[0] + (self._longitude[1] / 60)
            return [decimal_degrees, self._longitude[2]]
        elif self.coord_format == "dms":
            minute_parts = modf(self._longitude[1])
            seconds = round(minute_parts[0] * 60)
            return [self._longitude[0], int(minute_parts[1]), seconds, self._longitude[2]]
        else:
            return self._longitude

    # ==========================================
    # 日志功能 / Logging functions
    # ==========================================

    def start_logging(self, target_file: str, mode: str = "append") -> bool:
        """
        开始将 NMEA 原始数据记录到文件
        Args:
            target_file (str): 日志文件路径
            mode (str): 写入模式，'append' 为追加，'new' 为覆盖
        Returns:
            bool: 成功返回 True，失败返回 False
        Notes:
            - ISR-safe: 否
        ==========================================
        Start logging raw NMEA data to file.
        Args:
            target_file (str): Log file path
            mode (str): Write mode, 'append' or 'new'
        Returns:
            bool: True on success, False on failure
        Notes:
            - ISR-safe: No
        """
        mode_code = "w" if mode == "new" else "a"
        try:
            self.log_handle = open(target_file, mode_code)
        except (OSError, AttributeError) as e:
            self._log("Failed to open log file: %s" % e)
            return False
        self.log_en = True
        return True

    def stop_logging(self) -> bool:
        """
        关闭日志文件句柄并停止日志记录
        ==========================================
        Close log file handle and stop logging.
        """
        try:
            self.log_handle.close()
        except (OSError, AttributeError) as e:
            self._log("Failed to close log file: %s" % e)
            return False
        self.log_en = False
        return True

    def write_log(self, log_string: str) -> bool:
        """
        尝试将 NMEA 字符写入当前日志文件
        ==========================================
        Write the last valid NMEA character to the active log file.
        """
        try:
            self.log_handle.write(log_string)
        except (OSError, TypeError) as e:
            self._log("Log write failed: %s" % e)
            return False
        return True

    # ==========================================
    # NMEA 句子解析器 / NMEA sentence parsers
    # ==========================================

    def gprmc(self) -> bool:
        """
        解析 RMC（推荐最小定位信息）句子
        更新 UTC 时间戳、经纬度、航向、速度、日期和定位状态
        ==========================================
        Parse Recommended Minimum Specific GPS/Transit data (RMC) sentence.
        Updates UTC timestamp, latitude, longitude, course, speed, date, and fix status.
        """
        # UTC 时间戳解析 / Parse UTC timestamp
        try:
            utc_string = self.gps_segments[1]
            if utc_string:
                hours = (int(utc_string[0:2]) + self.local_offset) % 24
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = [hours, minutes, seconds]
            else:
                self.timestamp = [0, 0, 0.0]
        except (ValueError, IndexError):
            return False

        # 日期戳解析 / Parse date stamp
        try:
            date_string = self.gps_segments[9]
            if date_string:
                day = int(date_string[0:2])
                month = int(date_string[2:4])
                year = int(date_string[4:6])
                self.date = (day, month, year)
            else:
                self.date = (0, 0, 0)
        except (ValueError, IndexError):
            return False

        # 检查接收器数据有效标志 / Check receiver data valid flag
        if self.gps_segments[2] == "A":
            # 经纬度解析 / Parse latitude and longitude
            try:
                l_string = self.gps_segments[3]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[4]

                l_string = self.gps_segments[5]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[6]
            except (ValueError, IndexError):
                return False

            if lat_hemi not in _HEMISPHERES:
                return False
            if lon_hemi not in _HEMISPHERES:
                return False

            # 速度解析 / Parse speed
            try:
                spd_knt = float(self.gps_segments[7])
            except (ValueError, IndexError):
                return False

            # 航向解析 / Parse course
            try:
                if self.gps_segments[8]:
                    course = float(self.gps_segments[8])
                else:
                    course = 0.0
            except (ValueError, IndexError):
                return False

            # 更新对象数据 / Update object data
            self._latitude = [lat_degs, lat_mins, lat_hemi]
            self._longitude = [lon_degs, lon_mins, lon_hemi]
            self.speed = [spd_knt, spd_knt * 1.151, spd_knt * 1.852]
            self.course = course
            self.valid = True
            self.new_fix_time()
        else:
            # 无效数据时清除位置信息 / Clear position data if sentence is invalid
            self._latitude = [0, 0.0, "N"]
            self._longitude = [0, 0.0, "W"]
            self.speed = [0.0, 0.0, 0.0]
            self.course = 0.0
            self.valid = False

        return True

    def gpgll(self) -> bool:
        """
        解析 GLL（地理位置）句子
        更新 UTC 时间戳、经纬度和定位状态
        ==========================================
        Parse Geographic Latitude and Longitude (GLL) sentence.
        Updates UTC timestamp, latitude, longitude, and fix status.
        """
        # UTC 时间戳解析 / Parse UTC timestamp
        try:
            utc_string = self.gps_segments[5]
            if utc_string:
                hours = (int(utc_string[0:2]) + self.local_offset) % 24
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
                self.timestamp = [hours, minutes, seconds]
            else:
                self.timestamp = [0, 0, 0.0]
        except (ValueError, IndexError):
            return False

        # 检查接收器数据有效标志 / Check receiver data valid flag
        if self.gps_segments[6] == "A":
            # 经纬度解析 / Parse latitude and longitude
            try:
                l_string = self.gps_segments[1]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[2]

                l_string = self.gps_segments[3]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[4]
            except (ValueError, IndexError):
                return False

            if lat_hemi not in _HEMISPHERES:
                return False
            if lon_hemi not in _HEMISPHERES:
                return False

            # 更新对象数据 / Update object data
            self._latitude = [lat_degs, lat_mins, lat_hemi]
            self._longitude = [lon_degs, lon_mins, lon_hemi]
            self.valid = True
            self.new_fix_time()
        else:
            self._latitude = [0, 0.0, "N"]
            self._longitude = [0, 0.0, "W"]
            self.valid = False

        return True

    def gpvtg(self) -> bool:
        """
        解析 VTG（航迹和地面速度）句子
        更新速度和航向
        ==========================================
        Parse Track Made Good and Ground Speed (VTG) sentence.
        Updates speed and course.
        """
        try:
            course = float(self.gps_segments[1]) if self.gps_segments[1] else 0.0
            spd_knt = float(self.gps_segments[5]) if self.gps_segments[5] else 0.0
        except (ValueError, IndexError):
            return False

        self.speed = (spd_knt, spd_knt * 1.151, spd_knt * 1.852)
        self.course = course
        return True

    def gpgga(self) -> bool:
        """
        解析 GGA（GPS 定位数据）句子
        更新 UTC 时间戳、经纬度、定位状态、已用卫星数、HDOP、海拔高度等
        ==========================================
        Parse Global Positioning System Fix Data (GGA) sentence.
        Updates UTC timestamp, latitude, longitude, fix status, satellites in use,
        HDOP, altitude, geoid height, and fix status.
        """
        try:
            utc_string = self.gps_segments[1]
            if utc_string:
                hours = (int(utc_string[0:2]) + self.local_offset) % 24
                minutes = int(utc_string[2:4])
                seconds = float(utc_string[4:])
            else:
                hours = 0
                minutes = 0
                seconds = 0.0
            satellites_in_use = int(self.gps_segments[7])
            fix_stat = int(self.gps_segments[6])
        except (ValueError, IndexError):
            return False

        try:
            hdop = float(self.gps_segments[8])
        except (ValueError, IndexError):
            hdop = 0.0

        # 定位有效时解析位置和速度 / Parse position and speed if fix is good
        if fix_stat:
            try:
                l_string = self.gps_segments[2]
                lat_degs = int(l_string[0:2])
                lat_mins = float(l_string[2:])
                lat_hemi = self.gps_segments[3]

                l_string = self.gps_segments[4]
                lon_degs = int(l_string[0:3])
                lon_mins = float(l_string[3:])
                lon_hemi = self.gps_segments[5]
            except (ValueError, IndexError):
                return False

            if lat_hemi not in _HEMISPHERES:
                return False
            if lon_hemi not in _HEMISPHERES:
                return False

            try:
                altitude = float(self.gps_segments[9])
                geoid_height = float(self.gps_segments[11])
            except (ValueError, IndexError):
                altitude = 0
                geoid_height = 0

            self._latitude = [lat_degs, lat_mins, lat_hemi]
            self._longitude = [lon_degs, lon_mins, lon_hemi]
            self.altitude = altitude
            self.geoid_height = geoid_height

        self.timestamp = [hours, minutes, seconds]
        self.satellites_in_use = satellites_in_use
        self.hdop = hdop
        self.fix_stat = fix_stat

        if fix_stat:
            self.new_fix_time()

        return True

    def gpgsa(self) -> bool:
        """
        解析 GSA（GPS DOP 和活跃卫星）句子
        更新 GPS 定位类型、已用卫星列表、PDOP、HDOP、VDOP
        ==========================================
        Parse GNSS DOP and Active Satellites (GSA) sentence.
        Updates GPS fix type, satellites used list, PDOP, HDOP, VDOP, and fix status.
        """
        try:
            fix_type = int(self.gps_segments[2])
        except (ValueError, IndexError):
            return False

        # 读取最多 12 个活跃卫星 PRN 编号 / Read up to 12 active satellite PRN numbers
        sats_used = []
        for sats in range(12):
            sat_number_str = self.gps_segments[3 + sats]
            if sat_number_str:
                try:
                    sat_number = int(sat_number_str)
                    sats_used.append(sat_number)
                except ValueError:
                    return False
            else:
                break

        try:
            pdop = float(self.gps_segments[15])
            hdop = float(self.gps_segments[16])
            vdop = float(self.gps_segments[17])
        except (ValueError, IndexError):
            return False

        self.fix_type = fix_type
        if fix_type > _FIX_NO_FIX:
            self.new_fix_time()
        self.satellites_used = sats_used
        self.hdop = hdop
        self.vdop = vdop
        self.pdop = pdop

        return True

    def gpgsv(self) -> bool:
        """
        解析 GSV（可见卫星信息）句子
        更新可见卫星总数、SV 句子数量及每个卫星的仰角、方位角、信噪比
        ==========================================
        Parse Satellites in View (GSV) sentence.
        Updates total visible satellites, SV sentence count, and per-satellite
        elevation, azimuth, and SNR data.
        """
        try:
            num_sv_sentences = int(self.gps_segments[1])
            current_sv_sentence = int(self.gps_segments[2])
            sats_in_view = int(self.gps_segments[3])
        except (ValueError, IndexError):
            return False

        satellite_dict = dict()

        # 计算需要读取的卫星数据段数量
        # Calculate number of satellite data segments to read
        if num_sv_sentences == current_sv_sentence:
            sat_segment_limit = (sats_in_view - ((num_sv_sentences - 1) * 4)) * 5
        else:
            sat_segment_limit = 20

        # 解析最多 4 颗卫星的数据 / Parse data for up to 4 satellites
        for sats in range(4, sat_segment_limit, 4):
            if self.gps_segments[sats]:
                try:
                    sat_id = int(self.gps_segments[sats])
                except (ValueError, IndexError):
                    return False

                try:
                    elevation = int(self.gps_segments[sats + 1])
                except (ValueError, IndexError):
                    elevation = None

                try:
                    azimuth = int(self.gps_segments[sats + 2])
                except (ValueError, IndexError):
                    azimuth = None

                try:
                    snr = int(self.gps_segments[sats + 3])
                except (ValueError, IndexError):
                    snr = None
            else:
                break

            satellite_dict[sat_id] = (elevation, azimuth, snr)

        self.total_sv_sentences = num_sv_sentences
        self.last_sv_sentence = current_sv_sentence
        self.satellites_in_view = sats_in_view

        # 合并处理所有 GSV 句子的卫星数据
        # Merge satellite data from all GSV sentences
        if current_sv_sentence == 1:
            self.satellite_data = satellite_dict
        else:
            self.satellite_data.update(satellite_dict)

        return True

    # ==========================================
    # 数据流处理函数 / Data stream handler
    # ==========================================

    def new_sentence(self) -> None:
        """
        为新句子准备解析器状态
        重置分段缓冲区、CRC 校验值和活动标志
        ==========================================
        Prepare parser state for a new sentence.
        Resets segment buffer, CRC value, and active flags.
        """
        self.gps_segments = [""]
        self.active_segment = 0
        self.crc_xor = 0
        self.sentence_active = True
        self.process_crc = True
        self.char_count = 0

    def update(self, new_char: str):
        """
        逐字符输入 NMEA 数据并进行解析
        识别 $（开始）、,（分段）、*（CRC 标识）等特殊字符，
        自动构建句子分段并校验 CRC，校验通过后调用对应解析函数
        Args:
            new_char (str): 单个 ASCII 字符
        Returns:
            str or None: 解析成功返回句子类型标识（如 'GPRMC'），否则返回 None
        Notes:
            - ISR-safe: 是（仅做字符串处理，无内存分配）
        ==========================================
        Feed NMEA characters one at a time for parsing.
        Recognizes $ (start), , (delimiter), * (CRC marker) special characters,
        builds sentence segments, validates CRC, and calls corresponding parser.
        Args:
            new_char (str): Single ASCII character
        Returns:
            str or None: Sentence type identifier on successful parse (e.g., 'GPRMC'), None otherwise
        Notes:
            - ISR-safe: Yes (only string processing, no memory allocation)
        """
        valid_sentence = False

        # 验证输入字符是否可打印 / Validate new_char is printable
        ascii_char = ord(new_char)
        if not (10 <= ascii_char <= 126):
            return None

        self.char_count += 1

        # 若日志已启用，写入日志文件 / Write to log if enabled
        if self.log_en:
            self.write_log(new_char)

        # 句子开始标志 '$' / New sentence starting with '$'
        if new_char == "$":
            self.new_sentence()
            return None

        if self.sentence_active:
            # 句子结束标志 '*'  / Sentence ending with '*'
            if new_char == "*":
                self.process_crc = False
                self.active_segment += 1
                self.gps_segments.append("")
                return None

            # 分段标志 ',' / Section delimiter
            elif new_char == ",":
                self.active_segment += 1
                self.gps_segments.append("")

            # 普通字符 / Regular character
            else:
                self.gps_segments[self.active_segment] += new_char

                # CRC 校验 / CRC validation
                if not self.process_crc:
                    if len(self.gps_segments[self.active_segment]) == 2:
                        try:
                            final_crc = int(self.gps_segments[self.active_segment], 16)
                            if self.crc_xor == final_crc:
                                valid_sentence = True
                            else:
                                self.crc_fails += 1
                        except ValueError:
                            pass

            # 更新 CRC XOR 值 / Update CRC XOR
            if self.process_crc:
                self.crc_xor ^= ascii_char

            # 句子解析成功时调用对应解析函数 / Parse valid sentence
            if valid_sentence:
                self.clean_sentences += 1
                self.sentence_active = False

                if self.gps_segments[0] in self.supported_sentences:
                    if self.supported_sentences[self.gps_segments[0]](self):
                        self.parsed_sentences += 1
                        return self.gps_segments[0]

            # 防止缓冲区溢出 / Buffer overflow protection
            if self.char_count > _SENTENCE_LIMIT:
                self.sentence_active = False

        return None

    def new_fix_time(self) -> None:
        """
        记录最近一次有效定位的时间戳
        在 GGA、GSA 和 RMC 句子解析成功后调用
        ==========================================
        Record timestamp of the most recent valid fix.
        Called after successful GGA, GSA, or RMC sentence parse.
        """
        if _utime is not None:
            self.fix_time = _utime.ticks_ms()
        else:
            self.fix_time = _time.time()

    # ==========================================
    # 用户辅助函数 / User helper functions
    # ==========================================

    def satellite_data_updated(self) -> bool:
        """
        检查是否已接收完所有 GSV 句子，卫星数据是否完整
        Returns:
            bool: 所有 GSV 句子已接收完成返回 True
        ==========================================
        Check if all GSV sentences have been received, making satellite data complete.
        Returns:
            bool: True if all GSV sentences received
        """
        return bool(self.total_sv_sentences > 0 and self.total_sv_sentences == self.last_sv_sentence)

    def unset_satellite_data_updated(self) -> None:
        """
        标记 GSV 数据已使用，后续更新视为新数据
        ==========================================
        Mark GSV data as consumed so future updates are treated as fresh.
        """
        self.last_sv_sentence = 0

    def satellites_visible(self) -> list:
        """
        返回当前可见卫星的 PRN 编号列表
        Returns:
            list: PRN 编号列表
        ==========================================
        Return list of currently visible satellite PRN numbers.
        Returns:
            list: List of PRN numbers
        """
        return list(self.satellite_data.keys())

    def time_since_fix(self) -> int:
        """
        返回自上次有效定位以来经过的毫秒数
        Returns:
            int: 毫秒数，无定位记录返回 -1
        ==========================================
        Return milliseconds since the last valid fix.
        Returns:
            int: Milliseconds elapsed, -1 if no fix recorded
        """
        if self.fix_time == 0:
            return -1
        if _utime is not None:
            return _utime.ticks_diff(_utime.ticks_ms(), self.fix_time)
        return int((_time.time() - self.fix_time) * 1000)

    def compass_direction(self) -> str:
        """
        根据当前航向计算罗盘方向
        Returns:
            str: 罗盘方向（N, NNE, NE 等 16 个方向之一）
        ==========================================
        Calculate compass direction from current course.
        Returns:
            str: Compass direction (one of 16 directions)
        """
        if self.course >= 348.75:
            offset_course = 360 - self.course
        else:
            offset_course = self.course + 11.25
        dir_index = floor(offset_course / 22.5)
        return _COMPASS_DIRECTIONS[dir_index]

    def latitude_string(self) -> str:
        """
        返回当前纬度数据的格式化字符串
        Returns:
            str: 格式化后的纬度字符串
        ==========================================
        Return formatted string of current latitude.
        Returns:
            str: Formatted latitude string
        """
        if self.coord_format == "dd":
            formatted_latitude = self.latitude
            return str(formatted_latitude[0]) + "° " + str(self._latitude[2])
        elif self.coord_format == "dms":
            formatted_latitude = self.latitude
            return (
                str(formatted_latitude[0]) + "° " + str(formatted_latitude[1]) + "' " + str(formatted_latitude[2]) + '" ' + str(formatted_latitude[3])
            )
        else:
            return str(self._latitude[0]) + "° " + str(self._latitude[1]) + "' " + str(self._latitude[2])

    def longitude_string(self) -> str:
        """
        返回当前经度数据的格式化字符串
        Returns:
            str: 格式化后的经度字符串
        ==========================================
        Return formatted string of current longitude.
        Returns:
            str: Formatted longitude string
        """
        if self.coord_format == "dd":
            formatted_longitude = self.longitude
            return str(formatted_longitude[0]) + "° " + str(self._longitude[2])
        elif self.coord_format == "dms":
            formatted_longitude = self.longitude
            return (
                str(formatted_longitude[0])
                + "° "
                + str(formatted_longitude[1])
                + "' "
                + str(formatted_longitude[2])
                + '" '
                + str(formatted_longitude[3])
            )
        else:
            return str(self._longitude[0]) + "° " + str(self._longitude[1]) + "' " + str(self._longitude[2])

    def speed_string(self, unit: str = "kph") -> str:
        """
        返回当前速度的格式化字符串
        Args:
            unit (str): 速度单位，'kph'（km/h）、'mph'（英里/时）、'knot'（节）
        Returns:
            str: 格式化后的速度字符串
        ==========================================
        Return formatted string of current speed.
        Args:
            unit (str): Speed unit, 'kph', 'mph', or 'knot'
        Returns:
            str: Formatted speed string
        """
        if unit == "mph":
            return str(self.speed[1]) + " mph"
        elif unit == "knot":
            unit_str = " knot" if self.speed[0] == 1 else " knots"
            return str(self.speed[0]) + unit_str
        else:
            return str(self.speed[2]) + " km/h"

    def date_string(self, formatting: str = "s_mdy", century: str = "20") -> str:
        """
        返回当前日期的格式化字符串
        Args:
            formatting (str): 日期格式
                - 'long': 长格式（如 January 1st, 2014）
                - 's_mdy': 短格式月/日/年（MM/DD/YYYY）
                - 's_dmy': 短格式日/月/年（DD/MM/YYYY）
            century (str): 世纪前缀，默认 '20'
        Returns:
            str: 格式化后的日期字符串
        ==========================================
        Return formatted string of current date.
        Args:
            formatting (str): Date format
                - 'long': Long format (e.g., January 1st, 2014)
                - 's_mdy': Short format MM/DD/YYYY
                - 's_dmy': Short format DD/MM/YYYY
            century (str): Century prefix, default '20'
        Returns:
            str: Formatted date string
        """
        if formatting == "long":
            month = _MONTHS[self.date[1] - 1]
            if self.date[0] in (1, 21, 31):
                suffix = "st"
            elif self.date[0] in (2, 22):
                suffix = "nd"
            elif self.date[0] in (3, 23):
                suffix = "rd"
            else:
                suffix = "th"
            day = str(self.date[0]) + suffix
            year = century + str(self.date[2])
            return month + " " + day + ", " + year
        else:
            day = ("0" + str(self.date[0])) if self.date[0] < 10 else str(self.date[0])
            month = ("0" + str(self.date[1])) if self.date[1] < 10 else str(self.date[1])
            year = ("0" + str(self.date[2])) if self.date[2] < 10 else str(self.date[2])
            if formatting == "s_dmy":
                return day + "/" + month + "/" + year
            return month + "/" + day + "/" + year

    def deinit(self) -> None:
        """
        重置 GPS 解析器状态
        清除所有定位数据、卫星数据和统计计数器
        Notes:
            - 调用后解析器回到初始状态，可重新使用
        ==========================================
        Reset GPS parser state.
        Clears all position data, satellite data, and statistics counters.
        Notes:
            - Parser returns to initial state and can be reused
        """
        self._log("Resetting GPS parser state")
        self.sentence_active = False
        self.active_segment = 0
        self.process_crc = False
        self.gps_segments = []
        self.crc_xor = 0
        self.char_count = 0
        self.fix_time = 0
        self.crc_fails = 0
        self.clean_sentences = 0
        self.parsed_sentences = 0
        self.log_en = False
        self.timestamp = [0, 0, 0.0]
        self.date = [0, 0, 0]
        self._latitude = [0, 0.0, "N"]
        self._longitude = [0, 0.0, "W"]
        self.speed = [0.0, 0.0, 0.0]
        self.course = 0.0
        self.altitude = 0.0
        self.geoid_height = 0.0
        self.satellites_in_view = 0
        self.satellites_in_use = 0
        self.satellites_used = []
        self.last_sv_sentence = 0
        self.total_sv_sentences = 0
        self.satellite_data = dict()
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0
        self.valid = False
        self.fix_stat = 0
        self.fix_type = _FIX_NO_FIX

    # 所有当前支持的 NMEA 句子类型映射
    # All currently supported NMEA sentence type mapping
    supported_sentences = {
        "GPRMC": gprmc,
        "GLRMC": gprmc,
        "GPGGA": gpgga,
        "GLGGA": gpgga,
        "GPVTG": gpvtg,
        "GLVTG": gpvtg,
        "GPGSA": gpgsa,
        "GLGSA": gpgsa,
        "GPGSV": gpgsv,
        "GLGSV": gpgsv,
        "GPGLL": gpgll,
        "GLGLL": gpgll,
        "GNGGA": gpgga,
        "GNRMC": gprmc,
        "GNVTG": gpvtg,
        "GNGLL": gpgll,
        "GNGSA": gpgsa,
    }


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
