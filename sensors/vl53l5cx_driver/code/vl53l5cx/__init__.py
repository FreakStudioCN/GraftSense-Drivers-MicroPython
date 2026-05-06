# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : Mark Grosen
# @File    : __init__.py
# @Description : VL53L5CX 8x8 多区域 ToF 距离传感器驱动基类
# @License : MIT

__version__ = "1.0.0"
__author__ = "Mark Grosen"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import struct
from time import sleep

from ._config_file import ConfigDataFile as ConfigData

# ======================================== 全局变量 ============================================

NB_TARGET_PER_ZONE = 1

RANGING_MODE_AUTONOMOUS = 3
RANGING_MODE_CONTINUOUS = 1

POWER_MODE_SLEEP = 0
POWER_MODE_WAKEUP = 1

TARGET_ORDER_CLOSEST = 1
TARGET_ORDER_STRONGEST = 2

RESOLUTION_4X4 = 16
RESOLUTION_8X8 = 64

DATA_AMBIENT_PER_SPAD = 0
DATA_NB_SPADS_ENABLED = 1
DATA_NB_TARGET_DETECTED = 2
DATA_SIGNAL_PER_SPAD = 3
DATA_RANGE_SIGMA_MM = 4
DATA_DISTANCE_MM = 5
DATA_REFLECTANCE = 6
DATA_TARGET_STATUS = 7
DATA_MOTION_INDICATOR = 8

STATUS_NOT_UPDATED = 0
STATUS_RATE_TOO_LOW_SPAD = 1
STATUS_TARGET_PHASE = 2
STATUS_SIGMA_TOO_HIGH = 3
STATUS_FAILED = 4
STATUS_VALID = 5
STATUS_NO_WRAP = 6
STATUS_RATE_FAILED = 7
STATUS_RATE_TOO_LOW = 8
STATUS_VALID_LARGE_PULSE = 9
STATUS_NO_PREV_TARGET = 10
STATUS_MEASUREMENT_FAILED = 11
STATUS_BLURRED = 12
STATUS_INCONSISTENT = 13
STATUS_NO_TARGETS = 255

_OFFSET_BUFFER_SIZE = 488
_UI_CMD_STATUS = 0x2C00
_UI_CMD_START = 0x2C04
_UI_CMD_END = 0x2FFF
_DCI_PIPE_CONTROL = 0xCF78
_DCI_SINGLE_RANGE = 0xCD5C
_DCI_DSS_CONFIG = 0xAD38
_DCI_ZONE_CONFIG = 0x5450
_DCI_FREQ_HZ = 0x5458
_DCI_TARGET_ORDER = 0xAE64
_DCI_OUTPUT_LIST = 0xCD78
_DCI_OUTPUT_CONFIG = 0xCD60
_DCI_OUTPUT_ENABLES = 0xCD68
_DCI_INT_TIME = 0x545C
_DCI_RANGING_MODE = 0xAD30
_DCI_SHARPENER = 0xAED8

_START_BH = 0x0000000D
_METADATA_BH = 0x54B400C0
_COMMONDATA_BH = 0x54C00040
_AMBIENT_RATE_BH = 0x54D00104
_SPAD_COUNT_BH = 0x55D00404
_NB_TARGET_DETECTED_BH = 0xCF7C0401
_SIGNAL_RATE_BH = 0xCFBC0404
_RANGE_SIGMA_MM_BH = 0xD2BC0402
_DISTANCE_BH = 0xD33C0402
_REFLECTANCE_BH = 0xD43C0401
_TARGET_STATUS_BH = 0xD47C0401
_MOTION_DETECT_BH = 0xCC5008C0

_COMMONDATA_IDX = 0x54C0
_METADATA_IDX = 0x54B4
_AMBIENT_RATE_IDX = 0x54D0
_SPAD_COUNT_IDX = 0x55D0
_MOTION_DETECT_IDX = 0xCC50
_NB_TARGET_DETECTED_IDX = 0xCF7C
_SIGNAL_RATE_IDX = 0xCFBC
_RANGE_SIGMA_MM_IDX = 0xD2BC
_DISTANCE_IDX = 0xD33C
_REFLECTANCE_EST_PC_IDX = 0xD43C
_TARGET_STATUS_IDX = 0xD47C

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Results:
    """
    VL53L5CX 测距结果容器
    Attributes:
        ambient_per_spad: 每 SPAD 环境光强度列表
        distance_mm: 距离列表（mm）
        nb_spads_enabled: 使能 SPAD 数量列表
        nb_target_detected: 检测到目标数量列表
        target_status: 目标状态列表
        reflectance: 反射率列表
        motion_indicator: 运动检测数据
        range_sigma_mm: 测距 sigma 列表（mm）
        signal_per_spad: 每 SPAD 信号强度列表
    ==========================================
    VL53L5CX ranging result container.
    """

    def __init__(self) -> None:
        self.ambient_per_spad = None
        self.distance_mm = None
        self.nb_spads_enabled = None
        self.nb_target_detected = None
        self.target_status = None
        self.reflectance = None
        self.motion_indicator = None
        self.range_sigma_mm = None
        self.signal_per_spad = None


class VL53L5CX:
    """
    VL53L5CX 8x8 多区域 ToF 距离传感器驱动基类
    Attributes:
        i2c: I2C 总线实例
        addr (int): 设备 I2C 地址
        _lpn: LPn 复位控制引脚实例
        _ntpz (int): 每区域目标数
    Methods:
        is_alive(): 检查传感器是否在线
        init(): 初始化传感器固件和配置
        start_ranging(enables): 启动测距
        check_data_ready(): 检查是否有新数据
        get_ranging_data(): 读取测距结果
        stop_ranging(): 停止测距
    Notes:
        - 基类不实现 I2C 读写，由子类实现
        - 依赖外部传入 I2C 实例
    ==========================================
    VL53L5CX 8x8 multi-zone ToF distance sensor base driver.
    """

    def __init__(self, i2c, addr: int = 0x29, lpn=None) -> None:
        """
        初始化 VL53L5CX 基类
        Args:
            i2c: MicroPython I2C 总线实例
            addr (int): I2C 设备地址，默认 0x29
            lpn: LPn 复位控制引脚实例，可选
        Returns:
            None
        Raises:
            ValueError: i2c 不是有效 I2C 实例
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize VL53L5CX base class.
        """
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(addr, int):
            raise ValueError("addr must be int, got %s" % type(addr))

        self.i2c = i2c
        self.addr = addr
        self._ntpz = NB_TARGET_PER_ZONE
        self._lpn = lpn
        self._b1 = bytearray(1)
        self._streamcount = 255
        self._data_read_size = 0
        self.config_data = ConfigData()

    def _poll_for_answer(self, size: int, pos: int, reg16: int,
                         mask: int, val: int) -> int:
        timeout = 0
        while True:
            data = self._rd_multi(reg16, size)
            if data and ((data[pos] & mask) == val):
                status = 0
                break
            if timeout >= 200:
                status = -1 if len(data) < 3 else data[2]
                break
            elif size >= 4 and data[2] >= 0x7f:
                status = -2
                break
            else:
                timeout = timeout + 1

        sleep(0.01)
        if status:
            raise ValueError("poll_for_answer failed")
        return status

    @staticmethod
    def _swap_buffer(data) -> None:
        for i in range(0, len(data), 4):
            data[i], data[i+1], data[i+2], data[i+3] = \
                data[i+3], data[i+2], data[i+1], data[i]

    def _send_offset_data(self, offset_data, resolution: int) -> bool:
        buf = bytearray(offset_data)
        if resolution == 16:
            buf[0x10:0x10+8] = bytes([0x0F, 0x04, 0x04, 0x00, 0x08, 0x10, 0x10, 0x07])
            self._swap_buffer(buf)

            # 注意：MicroPython 不支持 struct * 解包，使用 enumerate 逐元素赋值
            signal_grid = [0] * 64
            for i, w in enumerate(struct.unpack("64I", buf[0x3C:0x3C+256])):
                signal_grid[i] = w
            range_grid = [0] * 64
            for i, w in enumerate(struct.unpack("64h", buf[0x140:0x140+128])):
                range_grid[i] = w

            for j in range(4):
                for i in range(4):
                    signal_grid[i+(4*j)] = int((signal_grid[(2*i)+(16*j)] +
                                                signal_grid[(2*i)+(16*j)+1] +
                                                signal_grid[(2*i)+(16*j)+8] +
                                                signal_grid[(2*i)+(16*j)+9]) / 4)
                    range_grid[i+(4*j)] = int((range_grid[(2*i)+(16*j)] +
                                               range_grid[(2*i)+(16*j)+1] +
                                               range_grid[(2*i)+(16*j)+8] +
                                               range_grid[(2*i)+(16*j)+9]) / 4)

            for i in range(48):
                signal_grid[0x10 + i] = 0
                range_grid[0x10 + i] = 0

            buf[0x3C:0x3C+256] = struct.pack("64I", *signal_grid)
            buf[0x140:0x140+128] = struct.pack("64h", *range_grid)
            self._swap_buffer(buf)

        x = buf[8:-4]
        x.extend(bytes([0x00, 0x00, 0x00, 0x0F, 0x03, 0x01, 0x01, 0xE4]))
        self._wr_multi(0x2E18, x)
        return not self._poll_for_answer(4, 1, _UI_CMD_STATUS, 0xFF, 0x03)

    def _send_xtalk_data(self, resolution: int) -> bool:
        if resolution == RESOLUTION_4X4:
            xtalk_data = self.config_data.xtalk4x4_data
        else:
            xtalk_data = self.config_data.xtalk_data
        self._wr_multi(0x2CF8, xtalk_data)
        return not self._poll_for_answer(4, 1, _UI_CMD_STATUS, 0xFF, 0x03)

    def _dci_read_data(self, data, index: int) -> bool:
        data_size = len(data)
        cmd = bytearray(12)
        cmd[0] = index >> 8
        cmd[1] = index & 0xFF
        cmd[2] = (data_size & 0xFF0) >> 4
        cmd[3] = (data_size & 0xF) << 4
        cmd[7] = 0x0F
        cmd[9] = 0x02
        cmd[11] = 0x08
        self._wr_multi(_UI_CMD_END - 11, cmd)
        self._poll_for_answer(4, 1, _UI_CMD_STATUS, 0xFF, 0x03)

        buf = self._rd_multi(_UI_CMD_START, data_size + 12)
        for i in range(0, data_size, 4):
            data[i] = buf[4 + i + 3]
            data[i + 1] = buf[4 + i + 2]
            data[i + 2] = buf[4 + i + 1]
            data[i + 3] = buf[4 + i + 0]
        return True

    def _dci_replace_data(self, data, index: int, new_data, pos: int) -> bool:
        self._dci_read_data(data, index)
        for i in range(len(new_data)):
            data[pos + i] = new_data[i]
        self._dci_write_data(data, index)
        return True

    def _dci_write_data(self, data, index: int) -> bool:
        data_size = len(data)
        buf = bytearray(data_size + 12)

        # 写入 DCI 命令头
        buf[0] = index >> 8
        buf[1] = index & 0xFF
        buf[2] = (data_size & 0xFF0) >> 4
        buf[3] = (data_size & 0x0F) << 4

        # 写入数据（每4字节字节序翻转）
        for i in range(0, data_size, 4):
            buf[4 + i] = data[i + 3]
            buf[4 + i + 1] = data[i + 2]
            buf[4 + i + 2] = data[i + 1]
            buf[4 + i + 3] = data[i + 0]

        for i, b in enumerate([0x00, 0x00, 0x00, 0x0f, 0x05, 0x01,
                               (data_size + 8) >> 8,
                               (data_size + 8) & 0xFF], 4 + data_size):
            buf[i] = b

        address = _UI_CMD_END - (data_size + 12) + 1
        self._wr_multi(address, buf)
        return not self._poll_for_answer(4, 1, _UI_CMD_STATUS, 0XFF, 0x03)

    @staticmethod
    def _header(word: int) -> tuple:
        # 块头格式：type(4位) | size(12位) | idx(16位)
        return (word & 0xF), (word & 0xFFF0) >> 4, (word >> 16)

    @staticmethod
    def _ambient_per_spad(raw: bytes) -> list:
        data = []
        fmt = ">{}I".format(len(raw) // 4)
        for v in struct.unpack(fmt, raw):
            data.append(v // 2048)
        return data

    @staticmethod
    def _distance_mm(raw: bytes) -> list:
        data = []
        fmt = ">{}h".format(len(raw) // 2)
        for v in struct.unpack(fmt, raw):
            data.append(0 if v < 0 else v >> 2)
        return data

    @staticmethod
    def _nb_spads_enabled(raw: bytes) -> list:
        fmt = ">{}I".format(len(raw) // 4)
        return [v for v in struct.unpack(fmt, raw)]

    @staticmethod
    def _nb_target_detected(raw: bytes):
        return raw

    @staticmethod
    def _target_status(raw: bytes):
        return raw

    @staticmethod
    def _reflectance(raw: bytes):
        return raw

    @staticmethod
    def _motion_indicator(raw: bytes) -> tuple:
        return struct.unpack(">IIBBBB32I", raw)

    @staticmethod
    def _range_sigma_mm(raw: bytes) -> list:
        data = []
        fmt = ">{}H".format(len(raw) // 2)
        for r in struct.unpack(fmt, raw):
            data.append(r / 128)
        return data

    @staticmethod
    def _signal_per_spad(raw: bytes) -> list:
        data = []
        fmt = ">{}I".format(len(raw) // 4)
        for r in struct.unpack(fmt, raw):
            data.append(r / 2048)
        return data

    def is_alive(self) -> bool:
        """
        检查传感器是否在线（读取设备 ID）
        Returns:
            bool: True=在线（ID 为 0xF0, 0x02）
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if sensor is online by reading device ID.
        """
        self._wr_byte(0x7FFF, 0)
        buf = self._rd_multi(0, 2)
        self._wr_byte(0x7FFF, 2)
        return (buf[0] == 0xF0) and (buf[1] == 0x02)

    def init(self) -> int:
        """
        初始化传感器固件和配置
        Returns:
            int: 0=成功，负数=失败步骤码
        Notes:
            - ISR-safe: 否
            - 副作用：下载固件、写入默认配置、启动 MCU
        ==========================================
        Initialize sensor firmware and configuration.
        Returns:
            int: 0=success, negative=failure step code
        """
        # 软件复位序列
        self._wr_byte(0x7fff, 0x00)
        self._wr_byte(0x0009, 0x04)
        self._wr_byte(0x000F, 0x40)
        self._wr_byte(0x000A, 0x03)
        self._rd_byte(0x7FFF)

        self._wr_byte(0x000C, 0x01)
        self._wr_byte(0x0101, 0x00)
        self._wr_byte(0x0102, 0x00)
        self._wr_byte(0x010A, 0x01)
        self._wr_byte(0x4002, 0x01)
        self._wr_byte(0x4002, 0x00)
        self._wr_byte(0x010A, 0x03)
        self._wr_byte(0x0103, 0x01)
        self._wr_byte(0x000C, 0x00)
        self._wr_byte(0x000F, 0x43)
        sleep(0.001)

        self._wr_byte(0x000F, 0x40)
        self._wr_byte(0x000A, 0x01)
        sleep(0.1)

        # 等待传感器启动完成
        self._wr_byte(0x7fff, 0x00)
        if self._poll_for_answer(1, 0, 0x06, 0xff, 1):
            return -1

        self._wr_byte(0x000E, 0x01)
        self._wr_byte(0x7fff, 0x02)

        # 使能固件访问
        self._wr_byte(0x03, 0x0D)
        self._wr_byte(0x7fff, 0x01)
        if self._poll_for_answer(1, 0, 0x21, 0x10, 0x10):
            return -2
        self._wr_byte(0x7fff, 0x00)

        # 使能主机访问 GO1
        self._wr_byte(0x0C, 0x01)

        # 上电状态配置
        self._wr_byte(0x7fff, 0x00)
        self._wr_byte(0x101, 0x00)
        self._wr_byte(0x102, 0x00)
        self._wr_byte(0x010A, 0x01)
        self._wr_byte(0x4002, 0x01)
        self._wr_byte(0x4002, 0x00)
        self._wr_byte(0x010A, 0x03)
        self._wr_byte(0x103, 0x01)
        self._wr_byte(0x400F, 0x00)
        self._wr_byte(0x21A, 0x43)
        self._wr_byte(0x21A, 0x03)
        self._wr_byte(0x21A, 0x01)
        self._wr_byte(0x21A, 0x00)
        self._wr_byte(0x219, 0x00)
        self._wr_byte(0x21B, 0x00)

        # 唤醒 MCU
        self._wr_byte(0x7fff, 0x00)
        self._wr_byte(0x0C, 0x00)
        self._wr_byte(0x7fff, 0x01)
        self._wr_byte(0x20, 0x07)
        self._wr_byte(0x20, 0x06)

        # 分页写入固件（3页：0x8000 + 0x8000 + 0x5000）
        fw = self.config_data.fw_data(0x1000)
        for page, size in enumerate([0x8000, 0x8000, 0x5000], start=9):
            self._wr_byte(0x7fff, page)
            for sub in range(0, size, 0x1000):
                self._wr_multi(sub, next(fw))

        self._wr_byte(0x7fff, 0x01)

        # 校验固件是否下载成功
        self._wr_byte(0x7fff, 0x02)
        self._wr_byte(0x03, 0x0D)
        self._wr_byte(0x7fff, 0x01)
        if self._poll_for_answer(1, 0, 0x21, 0x10, 0x10):
            return -3
        self._wr_byte(0x7fff, 0x00)
        self._wr_byte(0x0C, 0x01)

        # 复位 MCU 并等待启动
        self._wr_byte(0x7FFF, 0x00)
        self._wr_byte(0x114, 0x00)
        self._wr_byte(0x115, 0x00)
        self._wr_byte(0x116, 0x42)
        self._wr_byte(0x117, 0x00)
        self._wr_byte(0x0B, 0x00)
        self._wr_byte(0x0C, 0x00)
        self._wr_byte(0x0B, 0x01)
        if self._poll_for_answer(1, 0, 0x06, 0xff, 0x00):
            return -4

        self._wr_byte(0x7fff, 0x02)

        # 读取 NVM 偏移数据并写入偏移缓冲区
        nvm_cmd = bytes([
            0x54, 0x00, 0x00, 0x40,
            0x9E, 0x14, 0x00, 0xC0,
            0x9E, 0x20, 0x01, 0x40,
            0x9E, 0x34, 0x00, 0x40,
            0x9E, 0x38, 0x04, 0x04,
            0x9F, 0x38, 0x04, 0x02,
            0x9F, 0xB8, 0x01, 0x00,
            0x9F, 0xC8, 0x01, 0x00,
            0x00, 0x00, 0x00, 0x0F,
            0x02, 0x02, 0x00, 0x24
        ])

        self._wr_multi(0x2fd8, nvm_cmd)
        if self._poll_for_answer(4, 0, 0x2C00, 0xff, 2):
            return -5

        self._offset_data = self._rd_multi(0x2C04, 492)
        if not self._send_offset_data(self._offset_data, RESOLUTION_4X4):
            return -6

        if not self._send_xtalk_data(RESOLUTION_4X4):
            return -7

        self._wr_multi(0x2C34, self.config_data.default_config_data)
        if self._poll_for_answer(4, 1, _UI_CMD_STATUS, 0xFF, 0x03):
            return -8

        PIPE_CTRL = bytes([self._ntpz, 0x00, 0x01, 0x00])
        if not self._dci_write_data(PIPE_CTRL, _DCI_PIPE_CONTROL):
            return -9

        SINGLE_RANGE = b'\x01\x00\x00\x00'
        if not self._dci_write_data(SINGLE_RANGE, _DCI_SINGLE_RANGE):
            return -10

        return 0

    def start_ranging(self, enables) -> bool:
        """
        启动测距，配置输出数据类型
        Args:
            enables: 可迭代，包含 DATA_* 常量，指定需要输出的数据类型
        Returns:
            bool: True=成功
        Notes:
            - ISR-safe: 否
            - 副作用：配置输出列表、启动测距会话
        ==========================================
        Start ranging with specified output data types.
        """
        resolution = self.resolution
        self._data_read_size = 0
        self._streamcount = 255

        output_bh_enable = [0x00000007, 0x00000000, 0x00000000, 0xC0000000]

        output = [
            _START_BH, _METADATA_BH, _COMMONDATA_BH, _AMBIENT_RATE_BH,
            _SPAD_COUNT_BH, _NB_TARGET_DETECTED_BH, _SIGNAL_RATE_BH,
            _RANGE_SIGMA_MM_BH, _DISTANCE_BH, _REFLECTANCE_BH,
            _TARGET_STATUS_BH, _MOTION_DETECT_BH
        ]

        # 固定输出的3个块（start + metadata + commondata）
        self._data_read_size += (0 + 4) + (4 + 0xc) + (4 + 0x4)

        for e in enables:
            btype, size, idx = self._header(output[e + 3])
            if (btype > 0) and (btype < 0xd):
                if (idx >= 0x54d0) and (idx < (0x54d0 + 960)):
                    size = resolution
                else:
                    size = resolution * self._ntpz
                self._data_read_size += (size * btype) + 4
                output[e + 3] = (idx << 16) | (size << 4) | btype
            else:
                self._data_read_size += size + 4
            output_bh_enable[0] |= 1 << (e + 3)

        # 头尾固定开销
        self._data_read_size += 20

        self._dci_write_data(struct.pack("<12I", *output), _DCI_OUTPUT_LIST)
        self._dci_write_data(struct.pack("<II", self._data_read_size, len(output) + 1),
                             _DCI_OUTPUT_CONFIG)
        self._dci_write_data(struct.pack("<IIII", *output_bh_enable), _DCI_OUTPUT_ENABLES)

        # 启动 xshut bypass（中断模式）
        self._wr_byte(0x7FFF, 0)
        self._wr_byte(0x09, 0x05)
        self._wr_byte(0x7FFF, 0x2)

        # 启动测距会话
        self._wr_multi(_UI_CMD_END - 3, b'\x00\x03\x00\x00')
        return not self._poll_for_answer(4, 1, _UI_CMD_STATUS, 0xFF, 0x03)

    def check_data_ready(self) -> bool:
        """
        检查是否有新的测距数据就绪
        Returns:
            bool: True=有新数据
        Notes:
            - ISR-safe: 否
        ==========================================
        Check if new ranging data is ready.
        """
        status = False
        buf = self._rd_multi(0, 4)
        if ((buf[0] != self._streamcount) and (buf[0] != 255) and
                (buf[1] == 0x5) and ((buf[2] & 0x5) == 0x5) and
                ((buf[3] & 0x10) == 0x10)):
            self._streamcount = buf[0]
            status = True
        return status

    def get_ranging_data(self) -> Results:
        """
        读取当前测距结果
        Returns:
            Results: 测距结果对象
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current ranging results.
        """
        results = Results()
        buf = self._rd_multi(0, self._data_read_size)
        self._streamcount = buf[0]

        # 跳过16字节头部，逐块解析
        offset = 16
        while offset < len(buf):
            bh = struct.unpack(">I", buf[offset:offset+4])[0]
            btype, size, idx = self._header(bh)

            if btype > 1 and btype < 0xD:
                msize = btype * size
            else:
                msize = size

            offset += 4
            raw = buf[offset:offset+msize]

            if idx == _AMBIENT_RATE_IDX:
                results.ambient_per_spad = self._ambient_per_spad(raw)
            elif idx == _SPAD_COUNT_IDX:
                results.nb_spads_enabled = self._nb_spads_enabled(raw)
            elif idx == _MOTION_DETECT_IDX:
                results.motion_indicator = self._motion_indicator(raw)
            elif idx == _NB_TARGET_DETECTED_IDX:
                results.nb_target_detected = self._nb_target_detected(raw)
            elif idx == _SIGNAL_RATE_IDX:
                results.signal_per_spad = self._signal_per_spad(raw)
            elif idx == _RANGE_SIGMA_MM_IDX:
                results.range_sigma_mm = self._range_sigma_mm(raw)
            elif idx == _DISTANCE_IDX:
                results.distance_mm = self._distance_mm(raw)
            elif idx == _REFLECTANCE_EST_PC_IDX:
                results.reflectance = self._reflectance(raw)
            elif idx == _TARGET_STATUS_IDX:
                results.target_status = self._target_status(raw)

            offset += msize

        return results

    def stop_ranging(self) -> None:
        """
        停止测距
        Returns:
            None
        Raises:
            ValueError: 停止 MCU 超时
        Notes:
            - ISR-safe: 否
            - 副作用：停止测距会话，关闭 xshut bypass
        ==========================================
        Stop ranging session.
        """
        buf = self._rd_multi(0x2FFC, 4)
        auto_stop_flag = struct.unpack("<I", buf)
        if auto_stop_flag != 0x4FF:
            self._wr_byte(0x7FFF, 0x00)
            self._wr_byte(0x15, 0x16)
            self._wr_byte(0x14, 0x01)

            timeout = 1000
            while timeout:
                flag = self._rd_byte(0x6)
                if (flag & 0x80):
                    break
                sleep(0.010)
                timeout -= 10

            if timeout == 0:
                raise ValueError("failed to stop MCU")

        # 撤销 MCU 停止状态
        self._wr_byte(0x7FFF, 0x00)
        self._wr_byte(0x14, 0x00)
        self._wr_byte(0x15, 0x00)

        # 关闭 xshut bypass
        self._wr_byte(0x09, 0x04)
        self._wr_byte(0x7FFF, 0x02)

    def deinit(self) -> None:
        """
        停止测距，释放传感器资源
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：停止测距会话
        ==========================================
        Stop ranging and release sensor resources.
        """
        self.stop_ranging()

    @property
    def integration_time_ms(self) -> float:
        """
        读取积分时间（ms）
        Returns:
            float: 积分时间（ms）
        Notes:
            - ISR-safe: 否
        ==========================================
        Get integration time (ms).
        """
        buf = bytearray(20)
        self._dci_read_data(buf, _DCI_INT_TIME)
        return struct.unpack("<I", buf[0:4])[0] / 1000

    @integration_time_ms.setter
    def integration_time_ms(self, itime: int) -> None:
        if (itime < 2) or (itime > 1000):
            raise ValueError("invalid integration time (2 < it < 1000)")
        buf = bytearray(20)
        self._dci_replace_data(buf, _DCI_INT_TIME, struct.pack("I", itime * 1000), 0)

    @property
    def resolution(self) -> int:
        """
        读取当前分辨率（区域数）
        Returns:
            int: 16=4x4，64=8x8
        Notes:
            - ISR-safe: 否
        ==========================================
        Get current resolution (zone count).
        """
        buf = bytearray(8)
        self._dci_read_data(buf, _DCI_ZONE_CONFIG)
        return buf[0] * buf[1]

    @resolution.setter
    def resolution(self, resolution: int) -> None:
        if (resolution != RESOLUTION_8X8) and (resolution != RESOLUTION_4X4):
            raise ValueError("invalid resolution")

        buf = bytearray(16)
        self._dci_read_data(buf, _DCI_DSS_CONFIG)
        if resolution == RESOLUTION_8X8:
            buf[0x04] = 16
            buf[0x06] = 16
            buf[0x09] = 1
        else:
            buf[0x04] = 64
            buf[0x06] = 64
            buf[0x09] = 4
        self._dci_write_data(buf, _DCI_DSS_CONFIG)

        buf = bytearray(8)
        self._dci_read_data(buf, _DCI_ZONE_CONFIG)
        if resolution == RESOLUTION_8X8:
            buf[0x00] = 8
            buf[0x01] = 8
            buf[0x04] = 4
            buf[0x05] = 4
        else:
            buf[0x00] = 4
            buf[0x01] = 4
            buf[0x04] = 8
            buf[0x05] = 8
        self._dci_write_data(buf, _DCI_ZONE_CONFIG)

        self._send_offset_data(self._offset_data, resolution)
        self._send_xtalk_data(resolution)

    @property
    def ranging_freq(self) -> int:
        """
        读取测距频率（Hz）
        Returns:
            int: 测距频率
        Notes:
            - ISR-safe: 否
        ==========================================
        Get ranging frequency (Hz).
        """
        buf = bytearray(4)
        self._dci_read_data(buf, _DCI_FREQ_HZ)
        return buf[1]

    @ranging_freq.setter
    def ranging_freq(self, freq: int) -> None:
        buf = bytearray(4)
        self._b1[0] = freq
        return self._dci_replace_data(buf, _DCI_FREQ_HZ, self._b1, 1)

    @property
    def target_order(self) -> int:
        """
        读取目标排序模式
        Returns:
            int: TARGET_ORDER_CLOSEST 或 TARGET_ORDER_STRONGEST
        Notes:
            - ISR-safe: 否
        ==========================================
        Get target order mode.
        """
        buf = bytearray(4)
        self._dci_read_data(buf, _DCI_TARGET_ORDER)
        return buf[0]

    @target_order.setter
    def target_order(self, order: int) -> None:
        buf = bytearray(4)
        self._b1[0] = order
        return self._dci_replace_data(buf, _DCI_TARGET_ORDER, self._b1, 0)

    @property
    def ranging_mode(self) -> int:
        """
        读取测距模式
        Returns:
            int: RANGING_MODE_CONTINUOUS 或 RANGING_MODE_AUTONOMOUS
        Notes:
            - ISR-safe: 否
        ==========================================
        Get ranging mode.
        """
        buf = bytearray(8)
        self._dci_read_data(buf, _DCI_RANGING_MODE)
        if buf[1] == 1:
            return RANGING_MODE_CONTINUOUS
        return RANGING_MODE_AUTONOMOUS

    @ranging_mode.setter
    def ranging_mode(self, mode: int) -> None:
        buf = bytearray(8)
        self._dci_read_data(buf, _DCI_RANGING_MODE)
        if mode == RANGING_MODE_CONTINUOUS:
            buf[1] = 0x1
            buf[3] = 0x3
            single_range = 0
        elif mode == RANGING_MODE_AUTONOMOUS:
            buf[1] = 0x3
            buf[3] = 0x2
            single_range = 1
        else:
            raise ValueError("invalid ranging mode")
        self._dci_write_data(buf, _DCI_RANGING_MODE)
        self._dci_write_data(struct.pack(">I", single_range), _DCI_SINGLE_RANGE)

    @property
    def power_mode(self) -> int:
        """
        读取电源模式
        Returns:
            int: POWER_MODE_WAKEUP、POWER_MODE_SLEEP 或 -1（未知）
        Notes:
            - ISR-safe: 否
        ==========================================
        Get power mode.
        """
        self._wr_byte(0x7FFF, 0x0)
        raw = self._rd_byte(0x9)
        self._wr_byte(0x7FFF, 0x2)
        if raw == 4:
            return POWER_MODE_WAKEUP
        elif raw == 2:
            return POWER_MODE_SLEEP
        return -1

    @power_mode.setter
    def power_mode(self, mode: int) -> None:
        if self.power_mode != mode and mode in [POWER_MODE_SLEEP, POWER_MODE_WAKEUP]:
            self._wr_byte(0x7FFF, 0)
            if mode == POWER_MODE_WAKEUP:
                self._wr_byte(0x9, 0x4)
                self._poll_for_answer(1, 0, 0x6, 0x01, 1)
            elif mode == POWER_MODE_SLEEP:
                self._wr_byte(0x09, 0x02)
                self._poll_for_answer(1, 0, 0x06, 0x01, 0)
            self._wr_byte(0x7FFF, 0x02)

    @property
    def sharpener_percent(self) -> int:
        """
        读取锐化百分比（0~100）
        Returns:
            int: 锐化百分比
        Notes:
            - ISR-safe: 否
        ==========================================
        Get sharpener percent (0~100).
        """
        buf = bytearray(16)
        self._dci_read_data(buf, _DCI_SHARPENER)
        return (buf[0xD] * 100) // 255

    @sharpener_percent.setter
    def sharpener_percent(self, value: int) -> None:
        if (value < 0) or (value > 100):
            raise ValueError("invalid sharpener percent")
        self._b1[0] = (value * 255) // 100
        self._dci_replace_data(bytearray(16), _DCI_SHARPENER, self._b1, 0xD)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
