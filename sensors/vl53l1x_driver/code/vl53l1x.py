# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 07:00
# @Author  : FreakStudio
# @File    : vl53l1x.py
# @Description : VL53L1X 激光测距传感器（ToF）驱动，直接 I2C 接口
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import machine
from machine import I2C
from micropython import const

# ======================================== 全局变量 ============================================

# VL53L1X 默认配置寄存器数据（寄存器地址 0x2D~0x87）
# 注意：此配置数组由 ST 官方 API 提供，不得随意修改非用户可配置字段
VL51L1X_DEFAULT_CONFIGURATION = bytes([
    0x00, # 0x2d : I2C fast plus 模式（1MHz），不修改则保持默认
    0x00, # 0x2e : I2C 上拉电压选择（1.8V=0，AVDD=1）
    0x00, # 0x2f : GPIO 上拉电压选择（1.8V=0，AVDD=1）
    0x01, # 0x30 : 中断极性（bit4=0 高有效，=1 低有效），用 SetInterruptPolarity()
    0x02, # 0x31 : 中断触发方式，用 CheckForDataReady()
    0x00, # 0x32 : 不可用户修改
    0x02, # 0x33 : 不可用户修改
    0x08, # 0x34 : 不可用户修改
    0x00, # 0x35 : 不可用户修改
    0x08, # 0x36 : 不可用户修改
    0x10, # 0x37 : 不可用户修改
    0x01, # 0x38 : 不可用户修改
    0x01, # 0x39 : 不可用户修改
    0x00, # 0x3a : 不可用户修改
    0x00, # 0x3b : 不可用户修改
    0x00, # 0x3c : 不可用户修改
    0x00, # 0x3d : 不可用户修改
    0xff, # 0x3e : 不可用户修改
    0x00, # 0x3f : 不可用户修改
    0x0F, # 0x40 : 不可用户修改
    0x00, # 0x41 : 不可用户修改
    0x00, # 0x42 : 不可用户修改
    0x00, # 0x43 : 不可用户修改
    0x00, # 0x44 : 不可用户修改
    0x00, # 0x45 : 不可用户修改
    0x20, # 0x46 : 中断配置（0x20=新样本就绪）
    0x0b, # 0x47 : 不可用户修改
    0x00, # 0x48 : 不可用户修改
    0x00, # 0x49 : 不可用户修改
    0x02, # 0x4a : 不可用户修改
    0x0a, # 0x4b : 不可用户修改
    0x21, # 0x4c : 不可用户修改
    0x00, # 0x4d : 不可用户修改
    0x00, # 0x4e : 不可用户修改
    0x05, # 0x4f : 不可用户修改
    0x00, # 0x50 : 不可用户修改
    0x00, # 0x51 : 不可用户修改
    0x00, # 0x52 : 不可用户修改
    0x00, # 0x53 : 不可用户修改
    0xc8, # 0x54 : 不可用户修改
    0x00, # 0x55 : 不可用户修改
    0x00, # 0x56 : 不可用户修改
    0x38, # 0x57 : 不可用户修改
    0xff, # 0x58 : 不可用户修改
    0x01, # 0x59 : 不可用户修改
    0x00, # 0x5a : 不可用户修改
    0x08, # 0x5b : 不可用户修改
    0x00, # 0x5c : 不可用户修改
    0x00, # 0x5d : 不可用户修改
    0x01, # 0x5e : 不可用户修改
    0xdb, # 0x5f : 不可用户修改
    0x0f, # 0x60 : 不可用户修改
    0x01, # 0x61 : 不可用户修改
    0xf1, # 0x62 : 不可用户修改
    0x0d, # 0x63 : 不可用户修改
    0x01, # 0x64 : Sigma 阈值 MSB（14.2 格式，mm），用 SetSigmaThreshold()，默认 90mm
    0x68, # 0x65 : Sigma 阈值 LSB
    0x00, # 0x66 : 最小计数率 MSB（9.7 格式，MCPS），用 SetSignalThreshold()
    0x80, # 0x67 : 最小计数率 LSB
    0x08, # 0x68 : 不可用户修改
    0xb8, # 0x69 : 不可用户修改
    0x00, # 0x6a : 不可用户修改
    0x00, # 0x6b : 不可用户修改
    0x00, # 0x6c : 间隔测量周期 MSB（32位，ms），用 SetIntermeasurementInMs()
    0x00, # 0x6d : 间隔测量周期
    0x0f, # 0x6e : 间隔测量周期
    0x89, # 0x6f : 间隔测量周期 LSB
    0x00, # 0x70 : 不可用户修改
    0x00, # 0x71 : 不可用户修改
    0x00, # 0x72 : 距离阈值高 MSB（mm），用 SetDistanceThreshold()
    0x00, # 0x73 : 距离阈值高 LSB
    0x00, # 0x74 : 距离阈值低 MSB（mm），用 SetDistanceThreshold()
    0x00, # 0x75 : 距离阈值低 LSB
    0x00, # 0x76 : 不可用户修改
    0x01, # 0x77 : 不可用户修改
    0x0f, # 0x78 : 不可用户修改
    0x0d, # 0x79 : 不可用户修改
    0x0e, # 0x7a : 不可用户修改
    0x0e, # 0x7b : 不可用户修改
    0x00, # 0x7c : 不可用户修改
    0x00, # 0x7d : 不可用户修改
    0x02, # 0x7e : 不可用户修改
    0xc7, # 0x7f : ROI 中心，用 SetROI()
    0xff, # 0x80 : XY ROI（X=宽，Y=高），用 SetROI()
    0x9B, # 0x81 : 不可用户修改
    0x00, # 0x82 : 不可用户修改
    0x00, # 0x83 : 不可用户修改
    0x00, # 0x84 : 不可用户修改
    0x01, # 0x85 : 不可用户修改
    0x01, # 0x86 : 清除中断，用 ClearInterrupt()
    0x40  # 0x87 : 启动测距（0x40=启动），用 StartRanging()/StopRanging()
])

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class VL53L1X:
    """
    VL53L1X 激光测距传感器（ToF）驱动类，直接 I2C 接口
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址，默认 0x29
    Methods:
        read_model_id(): 读取型号 ID，应为 0xEACC
        reset(): 软件复位传感器
        read(): 读取当前测距结果（mm）
        write_reg(reg, value): 写入单字节寄存器
        write_reg_16bit(reg, value): 写入双字节寄存器
        read_reg(reg): 读取单字节寄存器
        read_reg_16bit(reg): 读取双字节寄存器
        deinit(): 停止测距，释放资源
    Notes:
        - 直接持有 I2C 实例，不使用 sensor_pack 框架
        - 初始化时自动写入默认配置并启动测距
    ==========================================
    VL53L1X Time-of-Flight distance sensor driver, direct I2C interface.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address, default 0x29
    Methods:
        read_model_id(): Read model ID, should be 0xEACC
        reset(): Software reset sensor
        read(): Read current ranging result (mm)
        write_reg(reg, value): Write single-byte register
        write_reg_16bit(reg, value): Write 16-bit register
        read_reg(reg): Read single-byte register
        read_reg_16bit(reg): Read 16-bit register
        deinit(): Stop ranging and release resources
    Notes:
        - Directly holds I2C instance, does not use sensor_pack framework
        - Auto-writes default config and starts ranging on init
    """

    I2C_DEFAULT_ADDR = const(0x29)

    def __init__(self, i2c: I2C, address: int = I2C_DEFAULT_ADDR) -> None:
        """
        初始化 VL53L1X 传感器
        Args:
            i2c (I2C): MicroPython I2C 总线实例
            address (int): I2C 设备地址，默认 0x29
        Returns:
            None
        Raises:
            ValueError: i2c 不是 I2C 实例
            RuntimeError: 型号 ID 不匹配（接线错误或设备不存在）
        Notes:
            - ISR-safe: 否
            - 副作用：写入默认配置寄存器，启动测距
        ==========================================
        Initialize VL53L1X sensor.
        Args:
            i2c (I2C): MicroPython I2C bus instance
            address (int): I2C device address, default 0x29
        Returns:
            None
        Raises:
            ValueError: i2c is not an I2C instance
            RuntimeError: Model ID mismatch (wiring error or device absent)
        Notes:
            - ISR-safe: No
            - Side effect: Writes default config registers, starts ranging
        """
        # 参数校验
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))

        self._i2c = i2c
        self._address = address

        # 软件复位，等待传感器启动
        self.reset()
        machine.lightsleep(1)

        # 校验型号 ID，确认设备存在且接线正确
        if self.read_model_id() != 0xEACC:
            raise RuntimeError("Failed to find expected ID 0xEACC. Check wiring!")

        # 写入 ST 官方默认配置（寄存器 0x2D~0x87）
        self._i2c.writeto_mem(self._address, 0x2D, VL51L1X_DEFAULT_CONFIGURATION, addrsize=16)

        # 参照 ST VL53L1_init_and_start_range() API 逻辑：
        # 将 0x0022（ALGO__PART_TO_PART_RANGE_OFFSET_MM）乘以 4 写入 0x001E，
        # 假设 MM1/MM2 均已禁用，此为官方初始化序列的必要步骤
        self.write_reg_16bit(0x001E, self.read_reg_16bit(0x0022) * 4)
        machine.lightsleep(200)

    def write_reg(self, reg: int, value: int) -> None:
        """
        写入单字节寄存器
        Args:
            reg (int): 16 位寄存器地址
            value (int): 写入值（单字节）
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write single-byte register.
        Args:
            reg (int): 16-bit register address
            value (int): Value to write (single byte)
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            self._i2c.writeto_mem(self._address, reg, bytes([value]), addrsize=16)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%04X" % reg) from e

    def write_reg_16bit(self, reg: int, value: int) -> None:
        """
        写入双字节（16 位）寄存器，大端序
        Args:
            reg (int): 16 位寄存器地址
            value (int): 写入值（16 位）
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write 16-bit register, big-endian.
        Args:
            reg (int): 16-bit register address
            value (int): Value to write (16-bit)
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            self._i2c.writeto_mem(self._address, reg,
                                  bytes([(value >> 8) & 0xFF, value & 0xFF]), addrsize=16)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%04X" % reg) from e

    def read_reg(self, reg: int) -> int:
        """
        读取单字节寄存器
        Args:
            reg (int): 16 位寄存器地址
        Returns:
            int: 寄存器值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read single-byte register.
        Args:
            reg (int): 16-bit register address
        Returns:
            int: Register value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            return self._i2c.readfrom_mem(self._address, reg, 1, addrsize=16)[0]
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%04X" % reg) from e

    def read_reg_16bit(self, reg: int) -> int:
        """
        读取双字节（16 位）寄存器，大端序
        Args:
            reg (int): 16 位寄存器地址
        Returns:
            int: 16 位寄存器值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read 16-bit register, big-endian.
        Args:
            reg (int): 16-bit register address
        Returns:
            int: 16-bit register value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            data = self._i2c.readfrom_mem(self._address, reg, 2, addrsize=16)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%04X" % reg) from e
        return (data[0] << 8) + data[1]

    def read_model_id(self) -> int:
        """
        读取传感器型号 ID
        Returns:
            int: 型号 ID，正常应为 0xEACC
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor model ID. Should be 0xEACC.
        Returns:
            int: Model ID, expected 0xEACC
        Notes:
            - ISR-safe: No
        """
        return self.read_reg_16bit(0x010F)

    def reset(self) -> None:
        """
        软件复位传感器
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：传感器重启，需重新初始化
        ==========================================
        Software reset sensor.
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Sensor restarts, requires re-initialization
        """
        # 拉低 XSHUT 引脚（写 0x00）触发复位
        self.write_reg(0x0000, 0x00)
        machine.lightsleep(100)
        # 释放复位，传感器重新启动
        self.write_reg(0x0000, 0x01)

    def read(self) -> int:
        """
        读取当前测距结果
        Returns:
            int: 测距结果（毫米）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 注意：原驱动注释掉了完整的 range_status 状态解析逻辑（17 种状态码），
              保留简化版仅返回距离值；如需状态判断请参考 ST VL53L1X ULD API
        ==========================================
        Read current ranging result in millimeters.
        Returns:
            int: Ranging result (mm)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Note: Full range_status parsing (17 status codes) was removed in original driver;
              only distance is returned. See ST VL53L1X ULD API for status handling.
        """
        # 从 0x0089 (RESULT__RANGE_STATUS) 起一次读取 17 字节
        try:
            data = self._i2c.readfrom_mem(self._address, 0x0089, 17, addrsize=16)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x0089") from e
        # data[13:15] = final_crosstalk_corrected_range_mm_sd0（经串扰校正的最终距离）
        return (data[13] << 8) + data[14]

    def deinit(self) -> None:
        """
        停止测距，释放传感器资源
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：写入 0x87 寄存器停止测距，传感器进入待机
        ==========================================
        Stop ranging and release sensor resources.
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Writes 0x87 to stop ranging, sensor enters standby
        """
        # 写入 0x00 到 0x0087 停止测距（StartRanging=0）
        self.write_reg(0x0087, 0x00)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
