# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : Mark Grosen
# @File    : _config_file.py
# @Description : VL53L5CX 固件及配置数据从二进制文件加载
# @License : MIT

__version__ = "1.0.0"
__author__ = "Mark Grosen"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import sys
from os import stat

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _find_file(name: str, req_size: int) -> str:
    """
    在文件系统中查找指定名称和大小的固件文件
    Args:
        name (str): 文件名
        req_size (int): 期望文件大小（字节）
    Returns:
        str: 找到的文件路径
    Raises:
        ValueError: 文件未找到或大小不匹配
    Notes:
        - ISR-safe: 否
    ==========================================
    Find firmware file by name and expected size.
    """
    file = None
    size_on_disk = 0
    candidates = [name, "/" + name, "/lib/" + name]

    for d in sys.path:
        if d == "":
            candidates.append(name)
        else:
            candidates.append(d + "/" + name)

    for candidate in candidates:
        try:
            size_on_disk = stat(candidate)[6]
            file = candidate
            break
        except:
            file = None

    if file:
        if size_on_disk != req_size:
            raise ValueError("firmware file size incorrect")
    else:
        raise ValueError("could not find file: " + name)

    return file


# ======================================== 自定义类 ============================================


class ConfigDataFile:
    """
    从二进制文件加载 VL53L5CX 固件及配置数据
    Attributes:
        _file_name (str): 固件文件路径
    Methods:
        default_config_data: 读取默认配置数据
        xtalk_data: 读取 8x8 串扰校准数据
        xtalk4x4_data: 读取 4x4 串扰校准数据
        fw_data(chunk_size): 分块读取固件数据（生成器）
    Notes:
        - 固件文件格式：固件(0x15000) + 默认配置(972) + xtalk(776) + xtalk4x4(776)
    ==========================================
    Load VL53L5CX firmware and config data from binary file.
    """

    _FW_SIZE = 0x15000
    _DEFAULT_CONFIG_OFFSET = _FW_SIZE
    _DEFAULT_CONFIG_SIZE = 972
    _XTALK_OFFSET = _FW_SIZE + _DEFAULT_CONFIG_SIZE
    _XTALK_SIZE = 776
    _XTALK4X4_OFFSET = _FW_SIZE + _DEFAULT_CONFIG_SIZE + _XTALK_SIZE
    _XTALK4X4_SIZE = 776

    def __init__(self, name: str = "vl53l5cx/vl_fw_config.bin") -> None:
        """
        初始化配置数据加载器
        Args:
            name (str): 固件文件名，默认 "vl53l5cx/vl_fw_config.bin"
        Returns:
            None
        Raises:
            ValueError: 固件文件未找到或大小不匹配
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize config data loader.
        """
        self._file_name = _find_file(name, 88540)

    def _read_offset_data(self, offset: int, size: int) -> bytes:
        with open(self._file_name, "rb") as fw_file:
            fw_file.seek(offset)
            return fw_file.read(size)

    @property
    def default_config_data(self) -> bytes:
        return self._read_offset_data(self._DEFAULT_CONFIG_OFFSET, self._DEFAULT_CONFIG_SIZE)

    @property
    def xtalk_data(self) -> bytes:
        return self._read_offset_data(self._XTALK_OFFSET, self._XTALK_SIZE)

    @property
    def xtalk4x4_data(self) -> bytes:
        return self._read_offset_data(self._XTALK4X4_OFFSET, self._XTALK4X4_SIZE)

    def fw_data(self, chunk_size: int = 0x1000):
        """
        分块读取固件数据（生成器）
        Args:
            chunk_size (int): 每块大小，默认 0x1000
        Yields:
            bytes: 固件数据块
        Notes:
            - ISR-safe: 否
        ==========================================
        Read firmware data in chunks (generator).
        """
        with open(self._file_name, "rb") as fw_file:
            for _ in range(0, 0x15000, chunk_size):
                yield fw_file.read(chunk_size)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
