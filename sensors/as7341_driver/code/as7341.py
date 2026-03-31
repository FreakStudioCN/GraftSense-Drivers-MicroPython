# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午10:00
# @Author  : Rob Hamerling
# @File    : as7341.py
# @Description : AS7341多光谱数字传感器MicroPython驱动 支持光谱测量 闪烁检测 GPIO/LED控制 中断配置 参考自:https://gitlab.com/robhamerling/micropython-as7341
# @License : MIT
__version__ = "0.1.0"
__author__ = "Rob Hamerling"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from time import sleep_ms
from struct import unpack, unpack_from

# ======================================== 全局变量 ============================================

# SMUX通道选择配置字典，键为配置名称，值为对应的配置字节数组
# SMUX channel selection configuration dictionary, key is configuration name, value is corresponding configuration byte array
AS7341_SMUX_SELECT = {
    # F1至F4通道、CLEAR通道、NIR通道配置
    "F1F4CN": b"\x30\x01\x00\x00\x00\x42\x00\x00\x50\x00\x00\x00\x20\x04\x00\x30\x01\x50\x00\x06",
    # F5至F8通道、CLEAR通道、NIR通道配置
    "F5F8CN": b"\x00\x00\x00\x40\x02\x00\x10\x03\x50\x10\x03\x00\x00\x00\x24\x00\x00\x50\x00\x06",
    # F2至F7通道配置
    "F2F7": b"\x20\x00\x00\x00\x05\x31\x40\x06\x00\x40\x06\x00\x10\x03\x50\x20\x00\x00\x00\x00",
    # F3至F8通道配置
    "F3F8": b"\x10\x00\x00\x60\x04\x20\x30\x05\x00\x30\x05\x00\x00\x02\x46\x10\x00\x00\x00\x00",
    # 仅闪烁检测配置
    "FD": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x60",
}

# AS7341传感器默认I2C地址
AS7341_I2C_ADDRESS = const(0x39)
# AS7341传感器型号识别值（不含低2位）
AS7341_ID_VALUE = const(0x24)

# 寄存器地址及位域符号常量定义
# Symbolic constants for register addresses and bit fields
# 注意：地址范围0x60--0x6F的ASTATUS、ITIME和CHx_DATA寄存器未使用
# Note: ASTATUS, ITIME and CHx_DATA registers in address range 0x60--0x6F are not used

# 配置寄存器（CONFIG）地址及位域
AS7341_CONFIG = const(0x70)  # 配置寄存器地址
AS7341_CONFIG_INT_MODE_SPM = const(0x00)  # SPM单脉冲测量模式
AS7341_MODE_SPM = AS7341_CONFIG_INT_MODE_SPM  # SPM模式别名
AS7341_CONFIG_INT_MODE_SYNS = const(0x01)  # SYNS同步测量模式（GPIO触发）
AS7341_MODE_SYNS = AS7341_CONFIG_INT_MODE_SYNS  # SYNS模式别名
AS7341_CONFIG_INT_MODE_SYND = const(0x03)  # SYND同步测量模式（GPIO+EDGE触发）
AS7341_MODE_SYND = AS7341_CONFIG_INT_MODE_SYND  # SYND模式别名
AS7341_CONFIG_INT_SEL = const(0x04)  # 中断选择位
AS7341_CONFIG_LED_SEL = const(0x08)  # LED选择位

# 状态寄存器（STAT）地址及位域
AS7341_STAT = const(0x71)  # 状态寄存器地址
AS7341_STAT_READY = const(0x01)  # 就绪标志位
AS7341_STAT_WAIT_SYNC = const(0x02)  # 等待同步标志位

# 边缘检测寄存器（EDGE）地址
AS7341_EDGE = const(0x72)

# GPIO寄存器（GPIO）地址及位域
AS7341_GPIO = const(0x73)  # GPIO寄存器地址
AS7341_GPIO_PD_INT = const(0x01)  # INT引脚下拉使能位
AS7341_GPIO_PD_GPIO = const(0x02)  # GPIO引脚下拉使能位

# LED控制寄存器（LED）地址及位域
AS7341_LED = const(0x74)  # LED控制寄存器地址
AS7341_LED_LED_ACT = const(0x80)  # LED激活位

# 使能寄存器（ENABLE）地址及位域
AS7341_ENABLE = const(0x80)  # 使能寄存器地址
AS7341_ENABLE_PON = const(0x01)  # 电源使能位
AS7341_ENABLE_SP_EN = const(0x02)  # 光谱测量使能位
AS7341_ENABLE_WEN = const(0x08)  # WTIME自动重启使能位
AS7341_ENABLE_SMUXEN = const(0x10)  # SMUX使能位
AS7341_ENABLE_FDEN = const(0x40)  # 闪烁检测使能位

# 积分时间寄存器（ATIME）地址
AS7341_ATIME = const(0x81)

# WTIME寄存器（WTIME）地址
AS7341_WTIME = const(0x83)

# 光谱阈值寄存器（SP_TH）地址
AS7341_SP_TH_LOW = const(0x84)  # 低阈值低字节地址
AS7341_SP_TH_L_LSB = const(0x84)  # 低阈值低字节别名
AS7341_SP_TH_L_MSB = const(0x85)  # 低阈值高字节地址
AS7341_SP_TH_HIGH = const(0x86)  # 高阈值低字节地址
AS7341_SP_TH_H_LSB = const(0x86)  # 高阈值低字节别名
AS7341_SP_TH_H_MSB = const(0x87)  # 高阈值高字节地址

# 辅助ID寄存器（AUXID）地址
AS7341_AUXID = const(0x90)

# 修订版本寄存器（REVID）地址
AS7341_REVID = const(0x91)

# 设备ID寄存器（ID）地址
AS7341_ID = const(0x92)

# 状态寄存器（STATUS）地址及位域
AS7341_STATUS = const(0x93)  # 状态寄存器地址
AS7341_STATUS_ASAT = const(0x80)  # 光谱饱和标志位
AS7341_STATUS_AINT = const(0x08)  # 光谱中断标志位
AS7341_STATUS_FINT = const(0x04)  # 闪烁检测中断标志位
AS7341_STATUS_C_INT = const(0x02)  # 清除中断标志位
AS7341_STATUS_SINT = const(0x01)  # 同步中断标志位

# ASTATUS寄存器地址及位域
AS7341_ASTATUS = const(0x94)  # ASTATUS寄存器起始地址（包含6个通道计数）
AS7341_ASTATUS_ASAT_STATUS = const(0x80)  # 光谱饱和状态位
AS7341_ASTATUS_AGAIN_STATUS = const(0x0F)  # 增益状态位

# 通道数据寄存器（CH_DATA）地址
AS7341_CH_DATA = const(0x95)  # 通道数据起始地址
AS7341_CH0_DATA_L = const(0x95)  # CH0数据低字节地址
AS7341_CH0_DATA_H = const(0x96)  # CH0数据高字节地址
AS7341_CH1_DATA_L = const(0x97)  # CH1数据低字节地址
AS7341_CH1_DATA_H = const(0x98)  # CH1数据高字节地址
AS7341_CH2_DATA_L = const(0x99)  # CH2数据低字节地址
AS7341_CH2_DATA_H = const(0x9A)  # CH2数据高字节地址
AS7341_CH3_DATA_L = const(0x9B)  # CH3数据低字节地址
AS7341_CH3_DATA_H = const(0x9C)  # CH3数据高字节地址
AS7341_CH4_DATA_L = const(0x9D)  # CH4数据低字节地址
AS7341_CH4_DATA_H = const(0x9E)  # CH4数据高字节地址
AS7341_CH5_DATA_L = const(0x9F)  # CH5数据低字节地址
AS7341_CH5_DATA_H = const(0xA0)  # CH5数据高字节地址

# 状态寄存器2（STATUS_2）地址及位域
AS7341_STATUS_2 = const(0xA3)  # 状态寄存器2地址
AS7341_STATUS_2_AVALID = const(0x40)  # 数据有效标志位

# 状态寄存器3（STATUS_3）地址
AS7341_STATUS_3 = const(0xA4)

# 状态寄存器5（STATUS_5）地址
AS7341_STATUS_5 = const(0xA6)

# 状态寄存器6（STATUS_6）地址
AS7341_STATUS_6 = const(0xA7)

# 配置寄存器0（CFG_0）地址及位域
AS7341_CFG_0 = const(0xA9)  # 配置寄存器0地址
AS7341_CFG_0_WLONG = const(0x04)  # 长等待时间使能位
AS7341_CFG_0_REG_BANK = const(0x10)  # 寄存器库选择位（数据表图82）
AS7341_CFG_0_LOW_POWER = const(0x20)  # 低功耗模式位

# 配置寄存器1（CFG_1）地址
AS7341_CFG_1 = const(0xAA)

# 配置寄存器3（CFG_3）地址
AS7341_CFG_3 = const(0xAC)

# 配置寄存器6（CFG_6）地址及位域
AS7341_CFG_6 = const(0xAF)  # 配置寄存器6地址
AS7341_CFG_6_SMUX_CMD_ROM = const(0x00)  # SMUX ROM命令位
AS7341_CFG_6_SMUX_CMD_READ = const(0x08)  # SMUX读命令位
AS7341_CFG_6_SMUX_CMD_WRITE = const(0x10)  # SMUX写命令位

# 配置寄存器8（CFG_8）地址
AS7341_CFG_8 = const(0xB1)

# 配置寄存器9（CFG_9）地址
AS7341_CFG_9 = const(0xB2)

# 配置寄存器10（CFG_10）地址
AS7341_CFG_10 = const(0xB3)

# 配置寄存器12（CFG_12）地址
AS7341_CFG_12 = const(0xB5)

# 中断持续寄存器（PERS）地址
AS7341_PERS = const(0xBD)

# GPIO2寄存器（GPIO_2）地址及位域
AS7341_GPIO_2 = const(0xBE)  # GPIO2寄存器地址
AS7341_GPIO_2_GPIO_IN = const(0x01)  # GPIO输入状态位
AS7341_GPIO_2_GPIO_OUT = const(0x02)  # GPIO输出使能位
AS7341_GPIO_2_GPIO_IN_EN = const(0x04)  # GPIO输入使能位
AS7341_GPIO_2_GPIO_INV = const(0x08)  # GPIO输出反转位

# ASTEP寄存器地址
AS7341_ASTEP = const(0xCA)  # ASTEP低字节地址
AS7341_ASTEP_L = const(0xCA)  # ASTEP低字节别名
AS7341_ASTEP_H = const(0xCB)  # ASTEP高字节地址

# AGC最大增益寄存器（AGC_GAIN_MAX）地址
AS7341_AGC_GAIN_MAX = const(0xCF)

# 自动零配置寄存器（AZ_CONFIG）地址
AS7341_AZ_CONFIG = const(0xD6)

# 闪烁检测时间寄存器（FD_TIME）地址
AS7341_FD_TIME_1 = const(0xD8)
AS7341_FD_TIME_2 = const(0xDA)

# 闪烁检测配置寄存器0（FD_CFG0）地址
AS7341_FD_CFG0 = const(0xD7)

# 闪烁检测状态寄存器（FD_STATUS）地址及位域
AS7341_FD_STATUS = const(0xDB)  # 闪烁检测状态寄存器地址
AS7341_FD_STATUS_FD_100HZ = const(0x01)  # 100Hz闪烁检测标志位
AS7341_FD_STATUS_FD_120HZ = const(0x02)  # 120Hz闪烁检测标志位
AS7341_FD_STATUS_FD_100_VALID = const(0x04)  # 100Hz检测有效标志位
AS7341_FD_STATUS_FD_120_VALID = const(0x08)  # 120Hz检测有效标志位
AS7341_FD_STATUS_FD_SAT_DETECT = const(0x10)  # 饱和检测标志位
AS7341_FD_STATUS_FD_MEAS_VALID = const(0x20)  # 测量有效标志位

# 中断使能寄存器（INTENAB）地址及位域
AS7341_INTENAB = const(0xF9)  # 中断使能寄存器地址
AS7341_INTENAB_SP_IEN = const(0x08)  # 光谱中断使能位

# 控制寄存器（CONTROL）地址
AS7341_CONTROL = const(0xFA)

# FIFO映射寄存器（FIFO_MAP）地址
AS7341_FIFO_MAP = const(0xFC)

# FIFO级别寄存器（FIFO_LVL）地址
AS7341_FIFO_LVL = const(0xFD)

# FIFO数据寄存器（FDATA）地址
AS7341_FDATA = const(0xFE)  # FDATA低字节地址
AS7341_FDATA_L = const(0xFE)  # FDATA低字节别名
AS7341_FDATA_H = const(0xFF)  # FDATA高字节地址

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class AS7341:
    """
    AS7341多光谱数字传感器类
    AS7341 11 Channel Multi-Spectral Digital Sensor Class

    Attributes:
        _bus (machine.I2C): I2C总线对象
                            I2C bus object
        _address (int): 传感器I2C地址，默认0x39
                        Sensor I2C address, default 0x39
        _buffer1 (bytearray): 1字节I2C读写缓冲区
                              1-byte I2C read/write buffer
        _buffer2 (bytearray): 2字节I2C读写缓冲区
                              2-byte I2C read/write buffer
        _buffer13 (bytearray): 13字节I2C读写缓冲区（用于读取所有通道数据）
                               13-byte I2C read/write buffer (for reading all channel data)
        _measuremode (int): 当前测量模式，默认SPM单脉冲模式
                            Current measurement mode, default SPM single pulse mode
        _connected (bool): 传感器连接状态标志
                           Sensor connection status flag

    Methods:
        enable: 启用传感器（仅上电）
                Enable sensor (power on only)
        disable: 禁用所有功能并断电
                 Disable all functions and power off
        reset: 重启传感器并检查连接状态
               Reset sensor and check connection status
        isconnected: 获取传感器连接状态
                     Get sensor connection status
        measurement_completed: 检查测量是否完成
                               Check if measurement is completed
        set_spectral_measurement: 启用/禁用光谱测量
                                  Enable/disable spectral measurement
        set_smux: 启用/禁用SMUX
                  Enable/disable SMUX
        set_measure_mode: 设置测量模式
                          Set measurement mode
        channel_select: 选择SMUX通道配置
                        Select SMUX channel configuration
        start_measure: 启动光谱测量
                       Start spectral measurement
        get_channel_data: 读取单个通道数据
                          Read single channel data
        get_spectral_data: 读取所有通道光谱数据
                           Read all channel spectral data
        set_flicker_detection: 启用/禁用闪烁检测
                               Enable/disable flicker detection
        get_flicker_frequency: 获取闪烁频率（100/120/0Hz）
                               Get flicker frequency (100/120/0Hz)
        set_gpio_input: 配置GPIO为输入模式
                        Configure GPIO as input mode
        get_gpio_value: 获取GPIO输入值
                        Get GPIO input value
        set_gpio_output: 配置GPIO为输出模式
                         Configure GPIO as output mode
        set_gpio_inverted: 反转GPIO输出状态
                           Invert GPIO output status
        set_gpio_mask: 直接设置GPIO寄存器值
                       Directly set GPIO register value
        set_astep: 设置ASTEP步长值
                   Set ASTEP step value
        get_astep_time: 获取ASTEP步长时间（毫秒）
                        Get ASTEP step time (milliseconds)
        set_atime: 设置积分时间（ASTEP步数）
                   Set integration time (ASTEP steps)
        get_overflow_count: 获取最大计数值
                            Get maximum count value
        get_integration_time: 获取总积分时间（毫秒）
                              Get total integration time (milliseconds)
        set_again: 设置增益码
                   Set gain code
        get_again: 获取当前增益码
                   Get current gain code
        set_again_factor: 通过增益倍数设置增益
                          Set gain by gain factor
        get_again_factor: 获取当前增益倍数
                          Get current gain factor
        set_wen: 启用/禁用WTIME自动重启
                 Enable/disable WTIME auto restart
        set_wtime: 设置WTIME值
                   Set WTIME value
        set_led_current: 设置板载LED电流
                         Set onboard LED current
        check_interrupt: 检查中断状态
                         Check interrupt status
        clear_interrupt: 清除所有中断
                         Clear all interrupts
        set_spectral_interrupt: 启用/禁用光谱中断
                                Enable/disable spectral interrupt
        set_interrupt_persistence: 设置中断持续次数
                                   Set interrupt persistence count
        set_spectral_threshold_channel: 选择中断阈值通道
                                        Select interrupt threshold channel
        set_thresholds: 设置光谱中断阈值
                        Set spectral interrupt thresholds
        get_thresholds: 获取光谱中断阈值
                        Get spectral interrupt thresholds
        set_syns_int: 配置SYNS模式中断
                      Configure SYNS mode interrupt
    """

    def __init__(self, i2c, addr=AS7341_I2C_ADDRESS):
        """
        初始化AS7341传感器对象
        Initialize AS7341 sensor object

        Args:
            i2c (machine.I2C): 已初始化的I2C总线对象
                               Initialized I2C bus object
            addr (int): 传感器I2C地址，默认0x39
                        Sensor I2C address, default 0x39

        Notes:
            必须传入有效的I2C总线对象，否则传感器无法通信
            Must pass a valid I2C bus object, otherwise the sensor cannot communicate
        """
        self._bus = i2c
        self._address = addr
        self._buffer1 = bytearray(1)  # 1字节I2C读写缓冲区
        self._buffer2 = bytearray(2)  # 2字节I2C读写缓冲区
        self._buffer13 = bytearray(13)  # 13字节I2C读写缓冲区
        self._measuremode = AS7341_MODE_SPM  # 默认测量模式为SPM
        self._connected = self.reset()  # 重启传感器并检查连接状态

    """ --------- 'private' methods ----------- """

    def _read_byte(self, reg):
        """
        读取单个寄存器字节值
        Read single register byte value

        Args:
            reg (int): 寄存器地址
                       Register address

        Returns:
            int: 寄存器字节值，读取失败返回-1
                 Register byte value, return -1 if read failed

        Notes:
            捕获I2C读取异常并打印错误信息
            Catch I2C read exceptions and print error information
        """
        try:
            self._bus.readfrom_mem_into(self._address, reg, self._buffer1)
            return self._buffer1[0]  # 返回寄存器整数值
        except Exception as err:
            print("I2C read_byte at 0x{:02X}, error: {}".format(reg, err))
            return -1  # 读取失败返回-1

    def _read_word(self, reg):
        """
        读取连续2个寄存器字节值（小端序）
        Read 2 consecutive register bytes (little endian)

        Args:
            reg (int): 起始寄存器地址
                       Start register address

        Returns:
            int: 16位整数值，读取失败返回-1
                 16-bit integer value, return -1 if read failed

        Notes:
            小端序转换，低字节在前，高字节在后
            Little endian conversion, low byte first, high byte last
        """
        try:
            self._bus.readfrom_mem_into(self._address, reg, self._buffer2)
            return int.from_bytes(self._buffer2, "little")  # 转换为小端序整数值
        except Exception as err:
            print("I2C read_word at 0x{:02X}, error: {}".format(reg, err))
            return -1  # 读取失败返回-1

    def _read_all_channels(self):
        """
        读取ASTATUS寄存器和所有6个通道数据
        Read ASTATUS register and all 6 channel data

        Returns:
            tuple: 6个通道的计数值元组，读取失败返回空列表
                   Tuple of 6 channel count values, return empty list if read failed

        Notes:
            读取ASTATUS寄存器会锁存通道计数值，确保数据一致性
            Reading ASTATUS register latches channel count values to ensure data consistency
        """
        try:
            self._bus.readfrom_mem_into(self._address, AS7341_ASTATUS, self._buffer13)
            return unpack_from("<HHHHHH", self._buffer13, 1)  # 跳过状态位，返回6个无符号短整型值
        except Exception as err:
            print("I2C read_all_channels at 0x{:02X}, error: {}".format(AS7341_ASTATUS, err))
            return []  # 读取失败返回空列表

    def _write_byte(self, reg, value):
        """
        写入单个字节到指定寄存器
        Write a single byte to the specified register

        Args:
            reg (int): 寄存器地址
                       Register address
            value (int): 写入的字节值（0-255）
                         Byte value to write (0-255)

        Returns:
            bool: 写入成功返回True，失败返回False
                  Return True if write succeeded, False if failed

        Notes:
            写入后延时10ms确保数据生效
            Delay 10ms after writing to ensure data takes effect
        """
        self._buffer1[0] = value & 0xFF
        try:
            self._bus.writeto_mem(self._address, reg, self._buffer1)
            sleep_ms(10)
        except Exception as err:
            print("I2C write_byte at 0x{:02X}, error: {}".format(reg, err))
            return False
        return True

    def _write_word(self, reg, value):
        """
        写入16位值到连续2个寄存器（小端序）
        Write 16-bit value to 2 consecutive registers (little endian)

        Args:
            reg (int): 起始寄存器地址
                       Start register address
            value (int): 16位整数值
                         16-bit integer value

        Returns:
            bool: 写入成功返回True，失败返回False
                  Return True if write succeeded, False if failed

        Notes:
            低字节写入reg地址，高字节写入reg+1地址，写入后延时20ms
            Low byte to reg address, high byte to reg+1 address, delay 20ms after writing
        """
        self._buffer2[0] = value & 0xFF  # 低字节
        self._buffer2[1] = (value >> 8) & 0xFF  # 高字节
        try:
            self._bus.writeto_mem(self._address, reg, self._buffer2)
            sleep_ms(20)
        except Exception as err:
            print("I2C write_word at 0x{:02X}, error: {}".format(reg, err))
            return False
        return True

    def _write_burst(self, reg, value):
        """
        批量写入字节数组到连续寄存器地址
        Burst write byte array to consecutive register addresses

        Args:
            reg (int): 起始寄存器地址
                       Start register address
            value (bytes/bytearray): 要写入的字节数组
                                     Byte array to write

        Returns:
            bool: 写入成功返回True，失败返回False
                  Return True if write succeeded, False if failed

        Notes:
            批量写入后延时100ms确保配置生效
            Delay 100ms after burst writing to ensure configuration takes effect
        """
        try:
            self._bus.writeto_mem(self._address, reg, value)
            sleep_ms(100)
        except Exception as err:
            print("I2C write_burst at 0x{:02X}, error: {}".format(reg, err))
            return False
        return True

    def _modify_reg(self, reg, mask, flag=True):
        """
        修改寄存器特定位值
        Modify specific bit values of register

        Args:
            reg (int): 寄存器地址
                       Register address
            mask (int): 位掩码（仅包含1的位会被修改）
                        Bit mask (only bits with 1 will be modified)
            flag (bool): True-置位（OR操作），False-复位（AND操作）
                         True - set bit (OR operation), False - reset bit (AND operation)

        Notes:
            1. 仅适用于掩码中为1的位（通常掩码仅包含单个1位）
               Only applicable to bits that are 1 in the mask (usually mask contains a single 1 bit)
            2. 若寄存器在0x60-0x74地址范围，调用者需预先选择寄存器库1
               If the register is in the 0x60-0x74 address range, the caller needs to pre-select register bank 1
        """
        data = self._read_byte(reg)  # 读取寄存器当前值
        if flag:
            data |= mask  # 置位指定位
        else:
            data &= ~mask  # 复位指定位
        self._write_byte(reg, data)  # 写回修改后的值

    def _set_bank(self, bank=1):
        """
        选择寄存器库
        Select register bank

        Args:
            bank (int): 0-选择0x80-0xFF地址寄存器，1-选择0x60-0x74地址寄存器
                        0 - select 0x80-0xFF address registers, 1 - select 0x60-0x74 address registers

        Notes:
            CFG_0寄存器（0xA9）在选择寄存器库1时仍可访问，否则无法重置REG_BANK位
            CFG_0 register (0xA9) is still accessible when register bank 1 is selected, otherwise REG_BANK bit cannot be reset
        """
        self._modify_reg(AS7341_CFG_0, AS7341_CFG_0_REG_BANK, bank != 0)

    """ ----------- 'public' methods ----------- """

    def enable(self):
        """
        启用传感器（仅上电）
        Enable sensor (power on only)

        Notes:
            仅设置PON位上电，不启用其他功能
            Only set PON bit to power on, do not enable other functions
        """
        self._write_byte(AS7341_ENABLE, AS7341_ENABLE_PON)

    def disable(self):
        """
        禁用所有功能并断电
        Disable all functions and power off

        Notes:
            先禁用测量模式和LED，再关闭电源
            Disable measurement mode and LED first, then power off
        """
        self._set_bank(1)  # CONFIG寄存器在库1
        self._write_byte(AS7341_CONFIG, 0x00)  # 关闭中断、LED，设置SPM模式
        self._set_bank(0)
        self._write_byte(AS7341_ENABLE, 0x00)  # 断电

    def reset(self):
        """
        重启传感器并检查连接状态
        Reset sensor and check connection status

        Returns:
            bool: 连接成功返回True，失败返回False
                  Return True if connection succeeded, False if failed

        Notes:
            重启过程：断电→延时→上电→读取设备ID→验证ID→配置测量模式
            Reset process: power off → delay → power on → read device ID → verify ID → configure measurement mode
        """
        self.disable()  # 断电（复位）
        sleep_ms(50)  # 等待稳定
        self.enable()  # 仅上电
        sleep_ms(50)  # 等待稳定
        id = self._read_byte(AS7341_ID)  # 读取设备ID
        if id < 0:  # 读取失败
            print("Failed to contact AS7341 at I2C address 0x{:02X}".format(self._address))
            return False
        else:
            if not (id & (~0x03)) == AS7341_ID_VALUE:  # 验证ID（高6位）
                print("No AS7341: found 0x{:02X}, expected 0x{:02X}".format(id, AS7341_ID_VALUE))
                return False
        self.set_measure_mode(self._measuremode)  # 配置测量模式
        return True

    def isconnected(self):
        """
        获取传感器连接状态
        Get sensor connection status

        Returns:
            bool: 已连接返回True，未连接返回False
                  Return True if connected, False if not connected
        """
        return self._connected

    def measurement_completed(self):
        """
        检查测量是否完成
        Check if measurement is completed

        Returns:
            bool: 测量完成返回True，未完成返回False
                  Return True if measurement completed, False if not completed
        """
        return bool(self._read_byte(AS7341_STATUS_2) & AS7341_STATUS_2_AVALID)

    def set_spectral_measurement(self, flag=True):
        """
        启用/禁用光谱测量
        Enable/disable spectral measurement

        Args:
            flag (bool): True-启用，False-禁用
                         True - enable, False - disable
        """
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_SP_EN, flag)

    def set_smux(self, flag=True):
        """
        启用/禁用SMUX
        Enable/disable SMUX

        Args:
            flag (bool): True-启用，False-禁用
                         True - enable, False - disable
        """
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_SMUXEN, flag)

    def set_measure_mode(self, mode=AS7341_CONFIG_INT_MODE_SPM):
        """
        设置传感器测量模式
        Set sensor measurement mode

        Args:
            mode (int): 测量模式，可选SPM/SYNS/SYND
                        Measurement mode, optional SPM/SYNS/SYND

        Notes:
            中断功能需单独配置
            Interrupt function needs to be configured separately
        """
        if mode in (
            AS7341_CONFIG_INT_MODE_SPM,  # SPM单脉冲模式（SP_EN触发）
            AS7341_CONFIG_INT_MODE_SYNS,  # SYNS同步模式（GPIO触发）
            AS7341_CONFIG_INT_MODE_SYND,
        ):  # SYND同步模式（GPIO+EDGE触发）
            self._measuremode = mode  # 保存新测量模式
            self._set_bank(1)  # CONFIG寄存器在库1
            data = self._read_byte(AS7341_CONFIG) & (~0x03)  # 复位低2位（模式位）
            data |= mode  # 设置新模式
            self._write_byte(AS7341_CONFIG, data)  # 写入新模式
            self._set_bank(0)  # 退出库1

    def channel_select(self, selection):
        """
        选择预设的SMUX通道配置
        Select preset SMUX channel configuration

        Args:
            selection (str): 配置名称，必须是AS7341_SMUX_SELECT的键
                             Configuration name, must be a key of AS7341_SMUX_SELECT

        Notes:
            会覆盖从0x00开始的20个寄存器值
            Will overwrite 20 register values starting from 0x00
        """
        if selection in AS7341_SMUX_SELECT:
            self._write_burst(0x00, AS7341_SMUX_SELECT[selection])
        else:
            print("{} is unknown in AS7341_SMUX_SELECT".format(selection))

    def start_measure(self, selection=None):
        """
        启动光谱测量
        Start spectral measurement

        Args:
            selection (str/None): SMUX配置名称，None则使用当前配置
                                  SMUX configuration name, use current configuration if None

        Notes:
            连续测量相同通道配置时，只需调用一次channel_select，后续可省略selection参数
            When continuously measuring with the same channel configuration, call channel_select once, and omit the selection parameter later
        """
        self._modify_reg(AS7341_CFG_0, AS7341_CFG_0_LOW_POWER, False)  # 禁用低功耗模式
        self.set_spectral_measurement(False)  # 暂停测量
        self._write_byte(AS7341_CFG_6, AS7341_CFG_6_SMUX_CMD_WRITE)  # 设置SMUX写模式
        if not selection == None:
            self.channel_select(selection)
        if self._measuremode == AS7341_CONFIG_INT_MODE_SPM:
            self.set_smux(True)
        elif self._measuremode == AS7341_CONFIG_INT_MODE_SYNS:
            self.set_smux(True)
            self.set_gpio_input(True)
        self.set_spectral_measurement(True)
        if self._measuremode == AS7341_CONFIG_INT_MODE_SPM:
            while not self.measurement_completed():
                sleep_ms(50)

    def get_channel_data(self, channel=0):
        """
        读取单个通道数据
        Read single channel data

        Args:
            channel (int): 通道号（0-5）
                           Channel number (0-5)

        Returns:
            int: 通道计数值，通道号无效返回0
                 Channel count value, return 0 if channel number is invalid

        Notes:
            计数值取决于之前选择的通道配置，自动零功能可能导致返回0
            Count value depends on the previously selected channel configuration, auto-zero function may cause return 0
        """
        data = 0  # 默认值
        if 0 <= channel <= 5:
            data = self._read_word(AS7341_CH_DATA + channel * 2)
            print("ch={:d}, addr={:02X}, buf2=0x{:02X}{:02X}".format(channel, AS7341_CH_DATA + channel * 2, self._buffer2[0], self._buffer2[1]))
        return data  # 返回计数值

    def get_spectral_data(self):
        """
        读取所有通道光谱数据
        Read all channel spectral data

        Returns:
            tuple: 6个通道计数值元组
                   Tuple of 6 channel count values

        Notes:
            读取状态寄存器会锁存数据，确保6个通道数据的一致性
            Reading status register latches data to ensure consistency of 6 channel data
        """
        return self._read_all_channels()  # 返回计数值元组

    def set_flicker_detection(self, flag=True):
        """
        启用/禁用闪烁检测
        Enable/disable flicker detection

        Args:
            flag (bool): True-启用，False-禁用
                         True - enable, False - disable
        """
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_FDEN, flag)

    def get_flicker_frequency(self):
        """
        获取闪烁频率
        Get flicker frequency

        Returns:
            int: 100（100Hz）、120（120Hz）、0（未检测到）
                 100 (100Hz), 120 (120Hz), 0 (not detected)

        Notes:
            闪烁检测的积分时间和增益与其他通道相同，不支持专用的FD_TIME和FD_GAIN
            Integration time and gain for flicker detection are the same as other channels, dedicated FD_TIME and FD_GAIN are not supported
        """
        self._modify_reg(AS7341_CFG_0, AS7341_CFG_0_LOW_POWER, False)  # 禁用低功耗模式
        self.set_spectral_measurement(False)
        self._write_byte(AS7341_CFG_6, AS7341_CFG_6_SMUX_CMD_WRITE)
        self.channel_select("FD")  # 选择仅闪烁检测配置
        self.set_smux(True)
        self.set_spectral_measurement(True)
        self.set_flicker_detection(True)
        for _ in range(10):  # 最多等待500ms测量完成
            fd_status = self._read_byte(AS7341_FD_STATUS)
            if fd_status & AS7341_FD_STATUS_FD_MEAS_VALID:
                break
            sleep_ms(50)
        else:  # 超时
            print("Flicker measurement timed out")
            return 0
        for _ in range(10):  # 最多等待500ms计算完成
            fd_status = self._read_byte(AS7341_FD_STATUS)
            if (fd_status & AS7341_FD_STATUS_FD_100_VALID) or (fd_status & AS7341_FD_STATUS_FD_120_VALID):
                break
            sleep_ms(50)
        else:  # 超时
            print("Flicker frequency calculation timed out")
            return 0
        self.set_flicker_detection(False)  # 禁用闪烁检测
        self._write_byte(AS7341_FD_STATUS, 0x3C)  # 复位FD_STATUS可清除位
        if (fd_status & AS7341_FD_STATUS_FD_100_VALID) and (fd_status & AS7341_FD_STATUS_FD_100HZ):
            return 100
        elif (fd_status & AS7341_FD_STATUS_FD_120_VALID) and (fd_status & AS7341_FD_STATUS_FD_120HZ):
            return 120
        return 0

    def set_gpio_input(self, enable=True):
        """
        配置GPIO为输入模式
        Configure GPIO as input mode

        Args:
            enable (bool): True-启用输入灵敏度，False-禁用
                           True - enable input sensitivity, False - disable

        Notes:
            GPIO引脚为开漏输出，需要上拉电阻
            GPIO pin is open drain output, pull-up resistor is required
        """
        mask = AS7341_GPIO_2_GPIO_OUT  # 激活GPIO引脚
        if enable:
            mask |= AS7341_GPIO_2_GPIO_IN_EN  # 启用输入灵敏度
        self._write_byte(AS7341_GPIO_2, mask)

    def get_gpio_value(self):
        """
        获取GPIO输入值
        Get GPIO input value

        Returns:
            bool: True-高电平，False-低电平
                  True - high level, False - low level

        Notes:
            仅在输入模式且输入灵敏度启用时有效
            Only valid in input mode and input sensitivity enabled
        """
        return bool(self._read_byte(AS7341_GPIO_2) & AS7341_GPIO_2_GPIO_IN)

    def set_gpio_output(self, inverted=False):
        """
        配置GPIO为输出模式
        Configure GPIO as output mode

        Args:
            inverted (bool): False-正常模式，True-反转模式
                             False - normal mode, True - inverted mode

        Notes:
            GPIO引脚为开漏输出，控制LED时需将LED阴极接GPIO，阳极通过电阻接+3.3V
            GPIO pin is open drain output, when controlling LED, connect LED cathode to GPIO, anode to +3.3V through resistor
        """
        mask = 0x00  # 复位所有位→输出模式
        if inverted:
            mask |= AS7341_GPIO_2_GPIO_INV
        self._write_byte(AS7341_GPIO_2, mask)

    def set_gpio_inverted(self, flag=True):
        """
        反转GPIO输出状态
        Invert GPIO output status

        Args:
            flag (bool): True-反转模式，False-正常模式
                         True - inverted mode, False - normal mode

        Notes:
            控制LED时：True-LED灭，False-LED亮
            When controlling LED: True - LED off, False - LED on
        """
        self._modify_reg(AS7341_GPIO_2, AS7341_GPIO_2_GPIO_INV, flag)

    def set_gpio_mask(self, mask=0x00):
        """
        直接设置GPIO寄存器值
        Directly set GPIO register value

        Args:
            mask (int): GPIO2寄存器值
                        GPIO2 register value

        Notes:
            常用掩码：
            0x00 - GPIO输出模式，LED亮
            0x08 - GPIO输出模式，LED灭
            0x06 - GPIO输入模式，启用输入灵敏度
            Common masks:
            0x00 - GPIO output mode, LED on
            0x08 - GPIO output mode, LED off
            0x06 - GPIO input mode, input sensitivity enabled
        """
        self._write_byte(AS7341_GPIO_2, mask)
        print("GPIO_2 = 0x{:02X}".format(self._read_byte(AS7341_GPIO_2)))

    def set_astep(self, value=599):
        """
        设置ASTEP步长值
        Set ASTEP step value

        Args:
            value (int): 步长值（0-65534），对应2.78μs-182ms
                         Step value (0-65534), corresponding to 2.78μs-182ms
        """
        if 0 <= value <= 65534:
            self._write_word(AS7341_ASTEP, value)

    def get_astep_time(self):
        """
        获取ASTEP步长时间
        Get ASTEP step time

        Returns:
            float: 步长时间（毫秒）
                   Step time (milliseconds)
        """
        return (self._read_word(AS7341_ASTEP) + 1) * 2.78 / 1000

    def set_atime(self, value=29):
        """
        设置积分时间（ASTEP步数）
        Set integration time (ASTEP steps)

        Args:
            value (int): 积分步数（0-255）
                         Integration steps (0-255)
        """
        if 0 <= value <= 255:
            self._write_byte(AS7341_ATIME, value)

    def get_overflow_count(self):
        """
        获取最大计数值
        Get maximum count value

        Returns:
            int: (ASTEP+1)*(ATIME+1)计算的最大计数值
                 Maximum count value calculated by (ASTEP+1)*(ATIME+1)
        """
        return (self._read_word(AS7341_ASTEP) + 1) * (self._read_byte(AS7341_ATIME) + 1)

    def get_integration_time(self):
        """
        获取总积分时间
        Get total integration time

        Returns:
            float: 总积分时间（毫秒）
                   Total integration time (milliseconds)

        Notes:
            仅在SPM和SYNS模式下有效
            Only valid in SPM and SYNS modes
        """
        return self.get_overflow_count() * 2.78 / 1000

    def set_again(self, code):
        """
        设置增益码
        Set gain code

        Args:
            code (int): 增益码（0-10），对应增益：0.5/1/2/4/8/16/32/64/128/256/512
                         Gain code (0-10), corresponding gain: 0.5/1/2/4/8/16/32/64/128/256/512

        Notes:
            增益倍数 = 2^(code-1)
            Gain factor = 2^(code-1)
        """
        if 0 <= code <= 10:
            self._write_byte(AS7341_CFG_1, code)

    def get_again(self):
        """
        获取当前增益码
        Get current gain code

        Returns:
            int: 增益码（0-10）
                 Gain code (0-10)
        """
        return self._read_byte(AS7341_CFG_1)

    def set_again_factor(self, factor):
        """
        通过增益倍数设置增益
        Set gain by gain factor

        Args:
            factor (float/int): 增益倍数，自动向下取整到最近的2的幂（0.5-512）
                                 Gain factor, auto round down to nearest power of 2 (0.5-512)
        """
        for code in range(10, -1, -1):  # 从高到低遍历增益码
            if 2 ** (code - 1) <= factor:
                break
        self._write_byte(AS7341_CFG_1, code)

    def get_again_factor(self):
        """
        获取当前增益倍数
        Get current gain factor

        Returns:
            float: 增益倍数（0.5-512）
                   Gain factor (0.5-512)
        """
        return 2 ** (self.get_again() - 1)

    def set_wen(self, flag=True):
        """
        启用/禁用WTIME自动重启
        Enable/disable WTIME auto restart

        Args:
            flag (bool): True-启用，False-禁用
                         True - enable, False - disable
        """
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_WEN, flag)

    def set_wtime(self, code):
        """
        设置WTIME自动重启间隔
        Set WTIME auto restart interval

        Args:
            code (int): WTIME码（0-255），间隔=2.78*(code+1)ms
                         WTIME code (0-255), interval=2.78*(code+1)ms

        Notes:
            需同时调用set_wen(True)启用自动重启
            Need to call set_wen(True) to enable auto restart
        """
        self._write_byte(AS7341_WTIME, code)

    def set_led_current(self, current):
        """
        设置板载LED电流
        Set onboard LED current

        Args:
            current (int): LED电流（4-20mA，仅偶数），超出范围则关闭LED
                           LED current (4-20mA, even numbers only), turn off LED if out of range

        Notes:
            LED电流范围4-20mA，仅支持偶数mA值
            LED current range 4-20mA, only even mA values are supported
        """
        self._set_bank(1)  # CONFIG和LED寄存器在库1
        if 4 <= current <= 20:  # 电流在有效范围
            self._modify_reg(AS7341_CONFIG, AS7341_CONFIG_LED_SEL, True)
            data = AS7341_LED_LED_ACT + ((current - 4) // 2)  # LED激活并设置电流
        else:
            self._modify_reg(AS7341_CONFIG, AS7341_CONFIG_LED_SEL, False)
            data = 0  # LED关闭
        self._write_byte(AS7341_LED, data)
        self._set_bank(0)
        sleep_ms(100)

    def check_interrupt(self):
        """
        检查光谱或闪烁检测饱和中断
        Check for Spectral or Flicker Detect saturation interrupt

        Returns:
            bool: 有中断返回True，无中断返回False
                  Return True if interrupt exists, False if not
        """
        data = self._read_byte(AS7341_STATUS)
        if data & AS7341_STATUS_ASAT:
            print("Spectral interrupt generation!")
            return True
        return False

    def clear_interrupt(self):
        """
        清除所有中断信号
        Clear all interrupt signals
        """
        self._write_byte(AS7341_STATUS, 0xFF)

    def set_spectral_interrupt(self, flag=True):
        """
        启用/禁用光谱中断
        Enable/disable spectral interrupts

        Args:
            flag (bool): True-启用，False-禁用
                         True - enable, False - disable
        """
        self._modify_reg(AS7341_INTENAB, AS7341_INTENAB_SP_IEN, flag)

    def set_interrupt_persistence(self, value):
        """
        设置中断持续次数
        Set interrupt persistence count

        Args:
            value (int): 持续次数（0-15）
                         Persistence count (0-15)
        """
        if 0 <= value <= 15:
            self._write_byte(AS7341_PERS, value)

    def set_spectral_threshold_channel(self, value):
        """
        选择中断阈值通道
        Select interrupt threshold channel

        Args:
            value (int): 通道号（0-4）
                         Channel number (0-4)
        """
        if 0 <= value <= 4:
            self._write_byte(AS7341_CFG_12, value)

    def set_thresholds(self, lo, hi):
        """
        设置光谱中断阈值
        Set spectral interrupt thresholds

        Args:
            lo (int): 低阈值
                      Low threshold
            hi (int): 高阈值（需大于低阈值）
                      High threshold (must be greater than low threshold)
        """
        if lo < hi:
            self._write_word(AS7341_SP_TH_LOW, lo)
            self._write_word(AS7341_SP_TH_HIGH, hi)
            sleep_ms(20)

    def get_thresholds(self):
        """
        获取光谱中断阈值
        Get spectral interrupt thresholds

        Returns:
            tuple: (低阈值, 高阈值)
                   (Low threshold, High threshold)
        """
        lo = self._read_word(AS7341_SP_TH_LOW)
        hi = self._read_word(AS7341_SP_TH_HIGH)
        return (lo, hi)

    def set_syns_int(self):
        """
        配置SYNS模式中断
        Configure SYNS mode interrupt

        Notes:
            INT引脚为开漏输出，需上拉电阻才能向外部设备发送信号
            INT pin is open drain output, pull-up resistor is required to send signals to external devices
        """
        self._set_bank(1)  # CONFIG寄存器在库1
        self._write_byte(AS7341_CONFIG, AS7341_CONFIG_INT_SEL | AS7341_CONFIG_INT_MODE_SYNS)
        self._set_bank(0)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
