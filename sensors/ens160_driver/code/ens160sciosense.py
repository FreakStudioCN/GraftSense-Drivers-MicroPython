# MicroPython
# MIT license; Copyright (c) 2022 Roman Shevchik, 2026 FreakStudio
# ENS160 数字金属氧化物多气体传感器驱动

from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import IBaseSensorEx, DeviceEx, IDentifier, Iterator, check_value

ens160_firmware_version = namedtuple("ens160_firmware_version", "major minor release")
# eCO2: 等效二氧化碳浓度 [ppm]
# TVOC: 总挥发性有机化合物浓度 [ppb]
# AQI:  空气质量指数（UBA标准），1=优秀..5=极差
ens160_air_params = namedtuple("ens160_air_params", "eco2 tvoc aqi")
# stat_as: bit7, 运行模式激活标志
# stat_error: bit6, 错误标志
# validity_flag: bit2-3, 0=正常/1=预热/2=初始启动/3=无效
# new_data: bit1, 新数据就绪
# new_gpr: bit0, 新GPR数据就绪
ens160_status = namedtuple("ens160_status", "stat_as stat_error validity_flag new_data new_gpr")
# int_pol: bit6, 中断极性 0=低有效/1=高有效
# int_cfg: bit5, 引脚驱动 0=开漏/1=推挽
# int_gpr: bit3, GPR寄存器新数据中断使能
# int_dat: bit1, DATA寄存器新数据中断使能
# int_en:  bit0, 中断引脚总使能
ens160_config = namedtuple("ens160_config", "int_pol int_cfg int_gpr int_dat int_en")


class Ens160(IBaseSensorEx, IDentifier, Iterator):
    """ENS160 数字金属氧化物多气体传感器驱动类。"""
    _CRC_POLY = 0x1D

    @staticmethod
    def _to_raw_config(cfg: ens160_config) -> int:
        n_bits = 6, 5, 3, 1, 0
        return sum(int(cfg[i]) << n_bits[i] for i in range(len(n_bits)))

    @staticmethod
    def _to_config(raw_cfg: int) -> ens160_config:
        n_bits = 6, 5, 3, 1, 0
        return ens160_config(*[bool(raw_cfg & (1 << b)) for b in n_bits])

    @staticmethod
    def _to_status(st: int) -> ens160_status:
        return ens160_status(
            stat_as=bool(st & 0x80),
            stat_error=bool(st & 0x40),
            validity_flag=(st & 0x0C) >> 2,
            new_data=bool(st & 0x02),
            new_gpr=bool(st & 0x01),
        )

    @staticmethod
    def _crc8(sequence, polynomial: int, init_value: int) -> int:
        # Sciosense 专有 CRC8 算法，需单独读取校验值
        crc = init_value & 0xFF
        for item in sequence:
            tmp = 0xFF & ((crc << 1) ^ item)
            crc = tmp if not (crc & 0x80) else tmp ^ polynomial
        return crc

    def __init__(self, adapter: bus_service.I2cAdapter, address: int = 0x52, check_crc: bool = True):
        self._connector = DeviceEx(adapter=adapter, address=address, big_byte_order=False)
        self._check_crc = check_crc

    def _read_register(self, reg_addr: int, bytes_count: int = 2) -> bytes:
        before = self._get_last_checksum() if self._check_crc else 0
        conn = self._connector
        b = conn.read_reg(reg_addr, bytes_count)
        if self._check_crc and 0 <= reg_addr < 0x38:
            crc = Ens160._crc8(b, Ens160._CRC_POLY, before)
            after = self._get_last_checksum()
            if crc != after:
                raise IOError(f"CRC error: calc={hex(crc)} != read={hex(after)}")
        return b

    def __del__(self):
        self._set_mode(0x00)

    # IDentifier
    def get_id(self) -> int:
        """返回传感器 Part Number。"""
        return self._connector.unpack("H", self._read_register(0x00, 2))[0]

    def soft_reset(self):
        """软件复位传感器。"""
        self._set_mode(0xF0)

    def _set_mode(self, new_mode: int):
        """设置工作模式：0x00=深度睡眠, 0x01=空闲, 0x02=标准测量, 0xF0=软复位。"""
        nm = check_value(new_mode, (0, 1, 2, 0xF0), f"Invalid mode: {new_mode}")
        self._connector.write_reg(0x10, nm, 1)

    def _get_mode(self) -> int:
        return self._read_register(0x10, 1)[0]

    def get_config(self, raw: bool = True):
        """返回当前配置，raw=True 返回 int，否则返回 ens160_config。"""
        raw_val = self._read_register(0x11, 1)[0]
        return raw_val if raw else Ens160._to_config(raw_val)

    def set_config(self, new_config):
        """设置传感器配置，接受 int 或 ens160_config。"""
        if isinstance(new_config, ens160_config):
            new_config = Ens160._to_raw_config(new_config)
        self._connector.write_reg(0x11, new_config, 1)

    def _exec_cmd(self, cmd: int) -> bytes:
        """执行内部命令：0x00=NOP, 0x0E=获取固件版本, 0xCC=清除GPR。"""
        check_value(cmd, (0x00, 0x0E, 0xCC), f"Invalid command: {cmd}")
        self._connector.write_reg(0x12, cmd, 1)
        return self._read_register(0x48, 8)

    def set_ambient_temp(self, value_in_celsius: float):
        """写入环境温度补偿值（摄氏度）。"""
        self._connector.write_reg(0x13, int(64 * (273.15 + value_in_celsius)), 2)

    def set_humidity(self, rel_hum: int):
        """写入相对湿度补偿值（%，0-100）。"""
        check_value(rel_hum, range(101), f"Invalid humidity: {rel_hum}")
        self._connector.write_reg(0x15, rel_hum << 9, 2)

    def _get_status(self, raw: bool = True):
        reg_val = self._read_register(0x20, 1)[0]
        return reg_val if raw else Ens160._to_status(reg_val)

    def _get_aqi(self) -> int:
        return 0x07 & self._read_register(0x21, 1)[0]

    def _get_tvoc(self) -> int:
        return self._connector.unpack("H", self._read_register(0x22, 2))[0]

    def _get_eco2(self) -> int:
        return self._connector.unpack("H", self._read_register(0x24, 2))[0]

    def _get_last_checksum(self) -> int:
        return self._connector.read_reg(0x38, 1)[0]

    def get_firmware_version(self) -> ens160_firmware_version:
        """返回固件版本 ens160_firmware_version(major, minor, release)。"""
        b = self._exec_cmd(0x0E)
        return ens160_firmware_version(major=b[4], minor=b[5], release=b[6])

    # IBaseSensorEx
    def get_conversion_cycle_time(self) -> int:
        """返回测量周期时间（ms）。"""
        return 1000

    def start_measurement(self, start: bool = True):
        """启动（start=True）或暂停（start=False）连续测量。"""
        self._set_mode(2 if start else 1)

    def get_measurement_value(self, value_index):
        """返回测量值：0=eCO2, 1=TVOC, 2=AQI, None=ens160_air_params 全部。"""
        if value_index == 0:
            return self._get_eco2()
        if value_index == 1:
            return self._get_tvoc()
        if value_index == 2:
            return self._get_aqi()
        if value_index is None:
            return ens160_air_params(eco2=self._get_eco2(), tvoc=self._get_tvoc(), aqi=self._get_aqi())

    def get_data_status(self, raw: bool = True):
        """返回数据就绪状态，raw=True 返回 int，否则返回 ens160_status。"""
        return self._get_status(raw=raw)

    def is_single_shot_mode(self) -> bool:
        return False

    def is_continuously_mode(self) -> bool:
        return self._get_mode() == 0x02

    # Iterator
    def __next__(self):
        """迭代器：连续模式下返回 ens160_air_params，无新数据返回 None。"""
        if not self.is_continuously_mode():
            return None
        status = self.get_data_status(raw=False)
        if status.new_data:
            return self.get_measurement_value(None)
        return None
