# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/07 00:00
# @Author  : Roman Shevchik
# @File    : sgp4Xmod.py
# @Description : SGP40/SGP41 VOC/NOx 空气质量传感器驱动，基于 sensor_pack_2 框架
# @License : MIT

__version__ = "1.0.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
import micropython
from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, IDentifier, Iterator, check_value
from sensor_pack_2.crc_mod import crc8

# ======================================== 全局变量 ============================================

# 传感器序列号（三个 16 位字）
serial_number_sgp4x = namedtuple("serial_number_sgp4x", "word_0 word_1 word_2")
# 测量结果：VOC 原始信号（SGP40/SGP41），NOx 原始信号（仅 SGP41，SGP40 为 None）
measured_values_sgp4x = namedtuple("measured_values_sgp4x", "VOC NOx")

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class SGP4X(IDentifier, Iterator):
    """
    SGP40/SGP41 空气质量传感器驱动类，基于 sensor_pack_2 框架
    Attributes:
        _sensor_id (int): 传感器型号，0=SGP40，1=SGP41
        _check_crc (bool): 是否校验 CRC
        _connector (DeviceEx): I2C 通信代理
    Methods:
        get_id(): 读取传感器序列号
        get_sensor_id(): 返回传感器型号标识
        get_last_cmd_code(): 返回最后发送的命令码
        execute_self_test(): 执行内置自检
        execute_conditioning(): 执行 SGP41 预热调节（仅 SGP41）
        measure_raw_signal(): 启动/继续 VOC 测量，返回原始信号
        turn_heater_off(): 关闭加热器，进入待机模式
        deinit(): 释放资源，关闭加热器
    Notes:
        - 依赖外部传入 BusAdapter 实例，不在内部创建总线
        - SGP40 仅支持 VOC 测量；SGP41 同时支持 VOC 和 NOx
        - 原始信号需通过 Sensirion Gas Index Algorithm 转换为 VOC/NOx 指数
        - 使用 sensor_pack_2 框架，多重继承 IDentifier + Iterator（框架强制，不可更改）
    ==========================================
    SGP40/SGP41 air quality sensor driver, based on sensor_pack_2 framework.
    Attributes:
        _sensor_id (int): Sensor model, 0=SGP40, 1=SGP41
        _check_crc (bool): Whether to verify CRC
        _connector (DeviceEx): I2C communication proxy
    Methods:
        get_id(): Read sensor serial number
        get_sensor_id(): Return sensor model identifier
        get_last_cmd_code(): Return last sent command code
        execute_self_test(): Run built-in self-test
        execute_conditioning(): Run SGP41 conditioning (SGP41 only)
        measure_raw_signal(): Start/continue VOC measurement, return raw signal
        turn_heater_off(): Turn off heater, enter idle mode
        deinit(): Release resources, turn off heater
    Notes:
        - Requires externally provided BusAdapter instance
        - SGP40 supports VOC only; SGP41 supports both VOC and NOx
        - Raw signals require Sensirion Gas Index Algorithm for index conversion
        - Uses sensor_pack_2 framework with multiple inheritance IDentifier + Iterator (framework-forced)
    """

    # 命令响应参数（响应字节数 + 等待时间 ms）
    answer_params_sgp4x = namedtuple("answer_params_sgp4x", "length wait_time")

    # 默认 I2C 地址
    I2C_DEFAULT_ADDR = micropython.const(0x59)
    # SGP41 预热调节命令，响应 3 字节，等待 50ms
    _CMD_EXECUTE_CONDITIONING = micropython.const(0x2612)
    # 启动/继续 VOC 测量，SGP40 响应 3 字节/30ms，SGP41 响应 6 字节/50ms
    _CMD_MEASURE_RAW_SIGNAL = micropython.const(0x260F)
    # 内置自检命令，响应 3 字节，等待 320ms
    _CMD_EXECUTE_SELF_TEST = micropython.const(0x280E)
    # 关闭加热器命令，无响应，等待 1ms
    _CMD_TURN_HEATER_OFF = micropython.const(0x3615)
    # 读取序列号命令，响应 9 字节，等待 1ms
    _CMD_GET_SERIAL_NUMBER = micropython.const(0x3682)

    def __init__(self, adapter: bus_service.BusAdapter, address: int = I2C_DEFAULT_ADDR, sensor_id: int = 0, check_crc: bool = True) -> None:
        """
        初始化 SGP4X 传感器驱动
        Args:
            adapter (BusAdapter): sensor_pack_2 总线适配器实例
            address (int): I2C 设备地址，固定为 0x59
            sensor_id (int): 传感器型号，0=SGP40，1=SGP41
            check_crc (bool): 是否校验响应 CRC，默认 True
        Returns:
            None
        Raises:
            ValueError: adapter 为 None 或类型错误、address/sensor_id 超出范围、check_crc 类型错误
        Notes:
            - ISR-safe: 否
            - 副作用：初始化通信代理和缓冲区，不写入硬件寄存器
        ==========================================
        Initialize SGP4X sensor driver.
        Args:
            adapter (BusAdapter): sensor_pack_2 bus adapter instance
            address (int): I2C device address, fixed at 0x59
            sensor_id (int): Sensor model, 0=SGP40, 1=SGP41
            check_crc (bool): Whether to verify response CRC, default True
        Returns:
            None
        Raises:
            ValueError: adapter is None or wrong type, address/sensor_id out of range, check_crc wrong type
        Notes:
            - ISR-safe: No
            - Side effect: Initializes communication proxy and buffers, no hardware writes
        """
        if adapter is None:
            raise ValueError("adapter must not be None")
        if not hasattr(adapter, "read_reg"):
            raise ValueError("adapter must be a BusAdapter instance")
        if not isinstance(check_crc, bool):
            raise ValueError("check_crc must be bool, got %s" % type(check_crc))
        check_value(address, range(0x59, 0x5A), "Invalid I2C address: 0x%02X" % address)
        check_value(sensor_id, range(2), "Invalid sensor_id: %d" % sensor_id)
        self._connector = DeviceEx(adapter=adapter, address=address, big_byte_order=True)
        self._check_crc = check_crc
        self._sensor_id = sensor_id
        self._last_cmd_code = None
        # 缓存字节序字符串，避免重复调用
        self._byte_order = self._connector._get_byteorder_as_str()
        # 预分配各长度响应缓冲区，复用避免频繁分配
        self._buf_3 = bytearray(3)
        self._buf_6 = bytearray(6)
        self._buf_9 = bytearray(9)
        self._cmd_buf = bytearray(8)

    def get_sensor_id(self) -> int:
        """
        返回传感器型号标识
        Args:
            无
        Returns:
            int: 0=SGP40，1=SGP41
        Notes:
            - ISR-safe: 是
        ==========================================
        Return sensor model identifier.
        Returns:
            int: 0=SGP40, 1=SGP41
        Notes:
            - ISR-safe: Yes
        """
        return self._sensor_id

    def get_last_cmd_code(self) -> int:
        """
        返回最后一次发送给传感器的命令码
        Args:
            无
        Returns:
            int 或 None
        Notes:
            - ISR-safe: 是
        ==========================================
        Return last command code sent to sensor.
        Returns:
            int or None
        Notes:
            - ISR-safe: Yes
        """
        return self._last_cmd_code

    def get_id(self) -> serial_number_sgp4x:
        """
        读取传感器序列号（三个 16 位字）
        Args:
            无
        Returns:
            serial_number_sgp4x: word_0, word_1, word_2
        Raises:
            RuntimeError: I2C 通信失败
            ValueError: CRC 校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor serial number (three 16-bit words).
        Returns:
            serial_number_sgp4x: word_0, word_1, word_2
        Raises:
            RuntimeError: I2C communication failed
            ValueError: CRC check failed
        Notes:
            - ISR-safe: No
        """
        _t = self._send_command_and_read_answer(cmd_code=SGP4X._CMD_GET_SERIAL_NUMBER, unpack_format="HBHBH")
        return serial_number_sgp4x(word_0=_t[0], word_1=_t[2], word_2=_t[4])

    def turn_heater_off(self) -> None:
        """
        关闭加热器，传感器进入待机模式
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：停止所有测量，进入低功耗待机状态
        ==========================================
        Turn off heater, sensor enters idle mode.
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Stops all measurements, enters low-power idle state
        """
        self._send_command(SGP4X._CMD_TURN_HEATER_OFF)

    def execute_self_test(self) -> int:
        """
        执行内置自检，验证加热器和 MOX 材料完整性
        Args:
            无
        Returns:
            int: 0xD400=全部通过，0x4B00=一项或多项失败
        Raises:
            RuntimeError: I2C 通信失败
            ValueError: CRC 校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Run built-in self-test.
        Returns:
            int: 0xD400=all passed, 0x4B00=one or more failed
        Raises:
            RuntimeError: I2C communication failed
            ValueError: CRC check failed
        Notes:
            - ISR-safe: No
        """
        _t = self._send_command_and_read_answer(cmd_code=SGP4X._CMD_EXECUTE_SELF_TEST, unpack_format="HB")
        return _t[0]

    def execute_conditioning(self, rel_hum: int = 50, temperature: int = 25) -> measured_values_sgp4x:
        """
        执行 SGP41 预热调节（仅 SGP41 支持，建议执行 10s，不得超过 10s）
        Args:
            rel_hum (int): 相对湿度补偿值（%），0~100，默认 50
            temperature (int): 温度补偿值（°C），-45~130，默认 25
        Returns:
            measured_values_sgp4x: VOC 原始信号，NOx 为 None
        Raises:
            ValueError: 参数超出范围或 CRC 校验失败
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Run SGP41 conditioning (SGP41 only, recommended 10s, must not exceed 10s).
        Args:
            rel_hum (int): Relative humidity compensation (%), 0~100, default 50
            temperature (int): Temperature compensation (°C), -45~130, default 25
        Returns:
            measured_values_sgp4x: VOC raw signal, NOx is None
        Raises:
            ValueError: Parameter out of range or CRC check failed
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        t = self._send_command_and_read_answer(
            cmd_code=SGP4X._CMD_EXECUTE_CONDITIONING, unpack_format="HB", with_params=True, rel_hum=rel_hum, temperature=temperature
        )
        return measured_values_sgp4x(VOC=t[0], NOx=None)

    def measure_raw_signal(self, rel_hum: int = 50, temperature: int = 25) -> measured_values_sgp4x:
        """
        启动/继续 VOC（及 NOx）测量，返回原始信号
        Args:
            rel_hum (int): 相对湿度补偿值（%），0~100，默认 50
            temperature (int): 温度补偿值（°C），-45~130，默认 25
        Returns:
            measured_values_sgp4x: VOC 原始信号；SGP41 时 NOx 有效，SGP40 时 NOx 为 None
        Raises:
            ValueError: 参数超出范围或 CRC 校验失败
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 建议每秒调用一次，不关闭加热器
        ==========================================
        Start/continue VOC (and NOx) measurement, return raw signal.
        Args:
            rel_hum (int): Relative humidity compensation (%), 0~100, default 50
            temperature (int): Temperature compensation (°C), -45~130, default 25
        Returns:
            measured_values_sgp4x: VOC raw; NOx valid for SGP41, None for SGP40
        Raises:
            ValueError: Parameter out of range or CRC check failed
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Recommended: call once per second without turning off heater
        """
        sen_id = self.get_sensor_id()
        # SGP41 响应 6 字节（VOC + NOx），SGP40 响应 3 字节（仅 VOC）
        fmt = "HBHB" if sen_id else "HB"
        _t = self._send_command_and_read_answer(
            cmd_code=SGP4X._CMD_MEASURE_RAW_SIGNAL, unpack_format=fmt, with_params=True, rel_hum=rel_hum, temperature=temperature
        )
        _NOx = _t[2] if sen_id else None
        return measured_values_sgp4x(VOC=_t[0], NOx=_NOx)

    def __iter__(self):
        """
        返回迭代器自身（Iterator 协议）
        Returns:
            self
        Notes:
            - ISR-safe: 是
        ==========================================
        Return iterator self (Iterator protocol).
        Returns:
            self
        Notes:
            - ISR-safe: Yes
        """
        return self

    def __next__(self) -> measured_values_sgp4x:
        """
        迭代器接口：以默认参数执行一次原始信号测量
        Returns:
            measured_values_sgp4x
        Notes:
            - ISR-safe: 否
            - 如需温湿度补偿，请直接调用 measure_raw_signal()
        ==========================================
        Iterator: one raw signal measurement with default params (50% RH, 25°C).
        Returns:
            measured_values_sgp4x
        Notes:
            - ISR-safe: No
            - For compensation, call measure_raw_signal() directly
        """
        return self.measure_raw_signal()

    @staticmethod
    def _calc_crc(sequence: bytes) -> int:
        """计算 CRC8 校验值（多项式 0x31，初始值 0xFF）"""
        return crc8(sequence, polynomial=0x31, init_value=0xFF)

    @staticmethod
    def _get_answer_params(cmd_code: int, sensor_id: int = 0):
        """根据命令码和传感器型号返回响应参数（字节数 + 等待时间）"""
        _wt, _l = None, None
        if SGP4X._CMD_TURN_HEATER_OFF == cmd_code:
            _l, _wt = 0, 1
        elif SGP4X._CMD_EXECUTE_SELF_TEST == cmd_code:
            _l, _wt = 3, 320
        elif sensor_id == 1 and SGP4X._CMD_EXECUTE_CONDITIONING == cmd_code:
            _l, _wt = 3, 50
        elif SGP4X._CMD_MEASURE_RAW_SIGNAL == cmd_code:
            # SGP40 响应 3 字节/30ms，SGP41 响应 6 字节/50ms
            _l, _wt = (3, 30) if sensor_id == 0 else (6, 50)
        elif SGP4X._CMD_GET_SERIAL_NUMBER == cmd_code:
            _l, _wt = 9, 1
        if _wt is None or _l is None:
            raise ValueError("Invalid cmd_code: 0x%04X or sensor_id: %d" % (cmd_code, sensor_id))
        return SGP4X.answer_params_sgp4x(length=_l, wait_time=_wt)

    @staticmethod
    def _get_data_place(answ_length: int, data: bool = True):
        """返回响应缓冲区中数据字节或 CRC 字节的索引范围"""
        check_value(answ_length, (0, 3, 6, 9), "Invalid answer length: %d" % answ_length)
        if answ_length == 0:
            return None
        for index in range(answ_length // 3):
            _start = 3 * index
            if data:
                yield range(_start, 2 + _start)
            else:
                yield range(2 + _start, 3 + _start)

    @staticmethod
    def _check_answer_length(answ_length: int):
        """校验响应长度合法性（0, 3, 6, 9）"""
        check_value(value=answ_length, valid_range=(0, 3, 6, 9), error_msg="Invalid answer length: %d" % answ_length)

    @staticmethod
    def _check_rh_temp(rh, temp):
        """校验相对湿度（0~100%）和温度（-45~130°C）范围"""
        if rh is not None:
            check_value(rh, range(101), "rh out of range: %s" % rh)
        if temp is not None:
            check_value(temp, range(-45, 131), "temp out of range: %s" % temp)

    @staticmethod
    def _get_raw_relhum(rel_hum: int) -> int:
        """将相对湿度（%）转换为传感器原始格式"""
        SGP4X._check_rh_temp(rh=rel_hum, temp=None)
        return round(65.35 * rel_hum)

    @staticmethod
    def _get_raw_temp(temperature: int) -> int:
        """将温度（°C）转换为传感器原始格式"""
        SGP4X._check_rh_temp(rh=None, temp=temperature)
        return round(374.4857142857 * (45 + temperature))

    def _get_buf_by_answ_length(self, answ_length: int):
        """根据响应长度返回对应的预分配缓冲区"""
        SGP4X._check_answer_length(answ_length)
        if answ_length == 0:
            return None
        if answ_length == 3:
            return self._buf_3
        if answ_length == 6:
            return self._buf_6
        if answ_length == 9:
            return self._buf_9
        raise ValueError("Invalid buffer length: %d" % answ_length)

    @staticmethod
    def _check_answer(answer: bytes, answ_length: int) -> bool:
        """逐段校验响应 CRC，不匹配时抛出 ValueError"""
        SGP4X._check_answer_length(answ_length)
        for data_place in SGP4X._get_data_place(answ_length):
            calc = SGP4X._calc_crc(answer[data_place.start : data_place.stop])
            recv = answer[data_place.stop]
            if calc != recv:
                raise ValueError("CRC mismatch: calc=0x%02X recv=0x%02X" % (calc, recv))
        return True

    def _read_answer(self):
        """读取上一条命令的响应，可选 CRC 校验，返回缓冲区引用"""
        _cmd = self.get_last_cmd_code()
        _ap = SGP4X._get_answer_params(_cmd, self.get_sensor_id())
        _al = _ap.length
        if _al == 0:
            return None
        _buf = self._get_buf_by_answ_length(_al)
        try:
            self._connector.read_to_buf(_buf)
        except OSError as e:
            raise RuntimeError("I2C read answer failed") from e
        if self._check_crc:
            SGP4X._check_answer(_buf, _al)
        return _buf

    def _send_command_and_read_answer(
        self, cmd_code: int, unpack_format: str, with_params: bool = False, rel_hum: int = None, temperature: int = None
    ):
        """发送命令并等待响应，返回解包后的元组"""
        if with_params:
            SGP4X._check_rh_temp(rel_hum, temperature)
            self._send_command(cmd_code, SGP4X._get_raw_relhum(rel_hum), SGP4X._get_raw_temp(temperature))
        else:
            self._send_command(cmd_code)
        _ap = SGP4X._get_answer_params(cmd_code, self.get_sensor_id())
        time.sleep_ms(_ap.wait_time)
        _buf = self._read_answer()
        return self._connector.unpack(unpack_format, _buf)

    def _send_command(self, cmd_code: int, raw_rel_hum: int = None, raw_temp: int = None) -> None:
        """
        向传感器发送命令（含或不含温湿度参数）
        Notes:
            - 温湿度参数必须同时提供或同时为 None
            - 带参数命令格式：[cmd_hi, cmd_lo, rh_hi, rh_lo, rh_crc, t_hi, t_lo, t_crc]
        """
        _bo = self._byte_order[0]
        if raw_rel_hum is not None and raw_temp is not None:
            _cmd_buf = self._cmd_buf
            _cmd_buf[0:2] = cmd_code.to_bytes(2, _bo)
            _cmd_buf[2:4] = raw_rel_hum.to_bytes(2, _bo)
            # 先写湿度数据，再计算湿度 CRC
            _cmd_buf[4] = SGP4X._calc_crc(_cmd_buf[2:4])
            _cmd_buf[5:7] = raw_temp.to_bytes(2, _bo)
            # 先写温度数据，再计算温度 CRC
            _cmd_buf[7] = SGP4X._calc_crc(_cmd_buf[5:7])
            try:
                self._connector.write(_cmd_buf)
            except OSError as e:
                raise RuntimeError("I2C write command with params failed") from e
        else:
            try:
                self._connector.write(cmd_code.to_bytes(2, _bo))
            except OSError as e:
                raise RuntimeError("I2C write command failed") from e
        self._last_cmd_code = cmd_code

    def deinit(self) -> None:
        """
        释放传感器资源，关闭加热器进入待机模式
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：关闭加热器，停止所有测量
        ==========================================
        Release sensor resources, turn off heater and enter idle mode.
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Turns off heater, stops all measurements
        """
        self.turn_heater_off()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
