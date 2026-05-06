# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2018/03/20 00:00
# @Author  : Nelio Goncalves Godoi
# @File    : si1145.py
# @Description : SI1145 紫外线/可见光/红外光/接近度传感器驱动（完整版）
# @License : MIT

__version__ = "0.3.0"
__author__ = "Nelio Goncalves Godoi"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

import time
from ustruct import unpack


# ======================================== 全局变量 ============================================

# 命令寄存器操作码
SI1145_PARAM_QUERY  = 0x80
SI1145_PARAM_SET    = 0xA0
SI1145_NOP          = 0x0
SI1145_RESET        = 0x01
SI1145_BUSADDR      = 0x02
SI1145_PS_FORCE     = 0x05
SI1145_ALS_FORCE    = 0x06
SI1145_PSALS_FORCE  = 0x07
SI1145_PS_PAUSE     = 0x09
SI1145_ALS_PAUSE    = 0x0A
SI1145_PSALS_PAUSE  = 0xB
SI1145_PS_AUTO      = 0x0D
SI1145_ALS_AUTO     = 0x0E
SI1145_PSALS_AUTO   = 0x0F
SI1145_GET_CAL      = 0x12

# 参数寄存器地址
SI1145_PARAM_I2CADDR              = 0x00
SI1145_PARAM_CHLIST               = 0x01
SI1145_PARAM_CHLIST_ENUV          = 0x80
SI1145_PARAM_CHLIST_ENAUX         = 0x40
SI1145_PARAM_CHLIST_ENALSIR       = 0x20
SI1145_PARAM_CHLIST_ENALSVIS      = 0x10
SI1145_PARAM_CHLIST_ENPS1         = 0x01
SI1145_PARAM_CHLIST_ENPS2         = 0x02
SI1145_PARAM_CHLIST_ENPS3         = 0x04
SI1145_PARAM_PSLED12SEL           = 0x02
SI1145_PARAM_PSLED12SEL_PS2NONE   = 0x00
SI1145_PARAM_PSLED12SEL_PS2LED1   = 0x10
SI1145_PARAM_PSLED12SEL_PS2LED2   = 0x20
SI1145_PARAM_PSLED12SEL_PS2LED3   = 0x40
SI1145_PARAM_PSLED12SEL_PS1NONE   = 0x00
SI1145_PARAM_PSLED12SEL_PS1LED1   = 0x01
SI1145_PARAM_PSLED12SEL_PS1LED2   = 0x02
SI1145_PARAM_PSLED12SEL_PS1LED3   = 0x04
SI1145_PARAM_PSLED3SEL            = 0x03
SI1145_PARAM_PSENCODE             = 0x05
SI1145_PARAM_ALSENCODE            = 0x06
SI1145_PARAM_PS1ADCMUX            = 0x07
SI1145_PARAM_PS2ADCMUX            = 0x08
SI1145_PARAM_PS3ADCMUX            = 0x09
SI1145_PARAM_PSADCOUNTER          = 0x0A
SI1145_PARAM_PSADCGAIN            = 0x0B
SI1145_PARAM_PSADCMISC            = 0x0C
SI1145_PARAM_PSADCMISC_RANGE      = 0x20
SI1145_PARAM_PSADCMISC_PSMODE     = 0x04
SI1145_PARAM_ALSIRADCMUX          = 0x0E
SI1145_PARAM_AUXADCMUX            = 0x0F
SI1145_PARAM_ALSVISADCOUNTER      = 0x10
SI1145_PARAM_ALSVISADCGAIN        = 0x11
SI1145_PARAM_ALSVISADCMISC        = 0x12
SI1145_PARAM_ALSVISADCMISC_VISRANGE = 0x20
SI1145_PARAM_ALSIRADCOUNTER       = 0x1D
SI1145_PARAM_ALSIRADCGAIN         = 0x1E
SI1145_PARAM_ALSIRADCMISC         = 0x1F
SI1145_PARAM_ALSIRADCMISC_RANGE   = 0x20
SI1145_PARAM_ADCCOUNTER_511CLK    = 0x70
SI1145_PARAM_ADCMUX_SMALLIR       = 0x00
SI1145_PARAM_ADCMUX_LARGEIR       = 0x03

# 寄存器地址
SI1145_REG_PARTID       = 0x00
SI1145_REG_REVID        = 0x01
SI1145_REG_SEQID        = 0x02
SI1145_REG_INTCFG       = 0x03
SI1145_REG_INTCFG_INTOE     = 0x01
SI1145_REG_INTCFG_INTMODE   = 0x02
SI1145_REG_IRQEN        = 0x04
SI1145_REG_IRQEN_ALSEVERYSAMPLE  = 0x01
SI1145_REG_IRQEN_PS1EVERYSAMPLE  = 0x04
SI1145_REG_IRQEN_PS2EVERYSAMPLE  = 0x08
SI1145_REG_IRQEN_PS3EVERYSAMPLE  = 0x10
SI1145_REG_IRQMODE1     = 0x05
SI1145_REG_IRQMODE2     = 0x06
SI1145_REG_HWKEY        = 0x07
SI1145_REG_MEASRATE0    = 0x08
SI1145_REG_MEASRATE1    = 0x09
SI1145_REG_PSRATE       = 0x0A
SI1145_REG_PSLED21      = 0x0F
SI1145_REG_PSLED3       = 0x10
SI1145_REG_UCOEFF0      = 0x13
SI1145_REG_UCOEFF1      = 0x14
SI1145_REG_UCOEFF2      = 0x15
SI1145_REG_UCOEFF3      = 0x16
SI1145_REG_PARAMWR      = 0x17
SI1145_REG_COMMAND      = 0x18
SI1145_REG_RESPONSE     = 0x20
SI1145_REG_IRQSTAT      = 0x21
SI1145_REG_IRQSTAT_ALS  = 0x01
SI1145_REG_ALSVISDATA0  = 0x22
SI1145_REG_ALSVISDATA1  = 0x23
SI1145_REG_ALSIRDATA0   = 0x24
SI1145_REG_ALSIRDATA1   = 0x25
SI1145_REG_PS1DATA0     = 0x26
SI1145_REG_PS1DATA1     = 0x27
SI1145_REG_PS2DATA0     = 0x28
SI1145_REG_PS2DATA1     = 0x29
SI1145_REG_PS3DATA0     = 0x2A
SI1145_REG_PS3DATA1     = 0x2B
SI1145_REG_UVINDEX0     = 0x2C
SI1145_REG_UVINDEX1     = 0x2D
SI1145_REG_PARAMRD      = 0x2E
SI1145_REG_CHIPSTAT     = 0x30

# SI1145 默认 I2C 地址
SI1145_ADDR = 0x60


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

class SI1145(object):
    """
    SI1145 紫外线/可见光/红外光/接近度传感器驱动类（完整版，含命名常量）
    Attributes:
        _i2c: I2C 总线实例
        _addr (int): 设备 I2C 地址，默认 0x60
    Methods:
        read_uv: 读取紫外线指数
        read_visible: 读取可见光强度
        read_ir: 读取红外光强度
        read_prox: 读取接近度值
    Notes:
        - 初始化时自动执行硬件复位和校准加载
        - 基于 Joe Gutting 的 Python_SI1145 移植
    ==========================================
    SI1145 UV/visible/IR/proximity sensor driver (full version with named constants).
    Attributes:
        _i2c: I2C bus instance
        _addr (int): Device I2C address, default 0x60
    Methods:
        read_uv: Read UV index
        read_visible: Read visible light level
        read_ir: Read IR light level
        read_prox: Read proximity value
    Notes:
        - Hardware reset and calibration are performed automatically on init
        - Ported from Joe Gutting's Python_SI1145
    """

    def __init__(self, i2c=None, addr=SI1145_ADDR):
        """
        初始化 SI1145 传感器
        Args:
            i2c: I2C 总线实例，不可为 None
            addr (int): I2C 设备地址，默认 0x60
        Returns:
            None
        Raises:
            ValueError: i2c 为 None 时抛出
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize SI1145 sensor.
        Args:
            i2c: I2C bus instance, must not be None
            addr (int): I2C device address, default 0x60
        Returns:
            None
        Raises:
            ValueError: Raised when i2c is None
        Notes:
            - ISR-safe: No
        """
        if i2c is None:
            raise ValueError('An I2C object is required.')
        self._i2c = i2c
        self._addr = addr
        # 复位硬件
        self._reset()
        # 加载校准参数
        self._load_calibration()

    def _read8(self, register):
        """
        读取单字节寄存器值
        Args:
            register (int): 寄存器地址
        Returns:
            int: 读取到的字节值（0x00~0xFF）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read a single byte from a register.
        Args:
            register (int): Register address
        Returns:
            int: Byte value read (0x00~0xFF)
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        result = unpack(
            'B',
            self._i2c.readfrom_mem(self._addr, register, 1)
        )[0] & 0xFF
        return result

    def _read16(self, register, little_endian=True):
        """
        读取双字节寄存器值
        Args:
            register (int): 寄存器起始地址
            little_endian (bool): True 为小端序，False 为大端序
        Returns:
            int: 16 位整数值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read two bytes from a register.
        Args:
            register (int): Register start address
            little_endian (bool): True for little-endian, False for big-endian
        Returns:
            int: 16-bit integer value
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        result = unpack('BB', self._i2c.readfrom_mem(self._addr, register, 2))
        result = ((result[1] << 8) | (result[0] & 0xFF))
        if not little_endian:
            result = ((result << 8) & 0xFF00) + (result >> 8)
        return result

    def _write8(self, register, value):
        """
        写入单字节到寄存器
        Args:
            register (int): 寄存器地址
            value (int): 写入值，自动截取低 8 位
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Write a single byte to a register.
        Args:
            register (int): Register address
            value (int): Value to write, low 8 bits are used
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        value = value & 0xFF
        self._i2c.writeto_mem(self._addr, register, bytes([value]))

    def _reset(self):
        """
        复位硬件传感器
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 复位后等待 10ms 再写入硬件密钥
        ==========================================
        Reset the hardware sensor.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Waits 10ms after reset before writing hardware key
        """
        # 清零测量速率和中断配置寄存器
        self._write8(SI1145_REG_MEASRATE0, 0x00)
        self._write8(SI1145_REG_MEASRATE1, 0x00)
        self._write8(SI1145_REG_IRQEN, 0x00)
        self._write8(SI1145_REG_IRQMODE1, 0x00)
        self._write8(SI1145_REG_IRQMODE2, 0x00)
        self._write8(SI1145_REG_INTCFG, 0x00)
        # 清除中断状态标志
        self._write8(SI1145_REG_IRQSTAT, 0xFF)
        # 发送复位命令
        self._write8(SI1145_REG_COMMAND, SI1145_RESET)
        time.sleep(.01)
        # 写入硬件密钥以解锁寄存器
        self._write8(SI1145_REG_HWKEY, 0x17)
        time.sleep(.01)

    def _write_param(self, parameter, value):
        """
        写入参数寄存器
        Args:
            parameter (int): 参数地址
            value (int): 参数值
        Returns:
            int: 写入后从 PARAMRD 寄存器读回的确认值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Write to a parameter register.
        Args:
            parameter (int): Parameter address
            value (int): Parameter value
        Returns:
            int: Confirmation value read back from PARAMRD register
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        # 先写入参数值到 PARAMWR
        self._write8(SI1145_REG_PARAMWR, value)
        # 再写入带 SET 标志的参数地址到 COMMAND
        self._write8(SI1145_REG_COMMAND, parameter | SI1145_PARAM_SET)
        # 读回确认值
        param_val = self._read8(SI1145_REG_PARAMRD)
        return param_val

    def _load_calibration(self):
        """
        加载传感器校准参数
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 启用 UV/ALS/PS 通道，配置 LED 电流和 ADC 参数，启动自动测量
        ==========================================
        Load sensor calibration parameters.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Enables UV/ALS/PS channels, configures LED current and ADC, starts auto measurement
        """
        # 写入 UV 指数计算系数
        self._write8(SI1145_REG_UCOEFF0, 0x7B)
        self._write8(SI1145_REG_UCOEFF1, 0x6B)
        self._write8(SI1145_REG_UCOEFF2, 0x01)
        self._write8(SI1145_REG_UCOEFF3, 0x00)

        # 启用 UV/辅助/红外/可见光/PS1 通道
        self._write_param(
            SI1145_PARAM_CHLIST,
            SI1145_PARAM_CHLIST_ENUV |
            SI1145_PARAM_CHLIST_ENAUX |
            SI1145_PARAM_CHLIST_ENALSIR |
            SI1145_PARAM_CHLIST_ENALSVIS |
            SI1145_PARAM_CHLIST_ENPS1)

        # 每次采样触发中断
        self._write8(SI1145_REG_INTCFG, SI1145_REG_INTCFG_INTOE)
        self._write8(SI1145_REG_IRQEN, SI1145_REG_IRQEN_ALSEVERYSAMPLE)

        # 设置 LED1 电流为 20mA
        self._i2c.writeto_mem(SI1145_ADDR, SI1145_REG_PSLED21, b'0x03')

        # PS1 使用大 IR ADC 通道
        self._write_param(SI1145_PARAM_PS1ADCMUX, SI1145_PARAM_ADCMUX_LARGEIR)

        # PS1 使用 LED1
        self._write_param(SI1145_PARAM_PSLED12SEL, SI1145_PARAM_PSLED12SEL_PS1LED1)

        # PS ADC 时钟分频为 1（最快）
        self._write_param(SI1145_PARAM_PSADCGAIN, 0)

        # PS ADC 采样 511 个时钟周期
        self._write_param(SI1145_PARAM_PSADCOUNTER, SI1145_PARAM_ADCCOUNTER_511CLK)

        # PS ADC 高量程模式
        self._write_param(
            SI1145_PARAM_PSADCMISC,
            SI1145_PARAM_PSADCMISC_RANGE | SI1145_PARAM_PSADCMISC_PSMODE)

        # IR ADC 使用小 IR 通道
        self._write_param(SI1145_PARAM_ALSIRADCMUX, SI1145_PARAM_ADCMUX_SMALLIR)

        # IR ADC 时钟分频为 1
        self._write_param(SI1145_PARAM_ALSIRADCGAIN, 0)

        # IR ADC 采样 511 个时钟周期
        self._write_param(SI1145_PARAM_ALSIRADCOUNTER, SI1145_PARAM_ADCCOUNTER_511CLK)

        # IR ADC 高量程模式
        self._write_param(SI1145_PARAM_ALSIRADCMISC, SI1145_PARAM_ALSIRADCMISC_RANGE)

        # 可见光 ADC 时钟分频为 1
        self._write_param(SI1145_PARAM_ALSVISADCGAIN, 0)

        # 可见光 ADC 采样 511 个时钟周期
        self._write_param(SI1145_PARAM_ALSVISADCOUNTER, SI1145_PARAM_ADCCOUNTER_511CLK)

        # 可见光 ADC 高量程模式
        self._write_param(SI1145_PARAM_ALSVISADCMISC, SI1145_PARAM_ALSVISADCMISC_VISRANGE)

        # 设置自动测量速率：255 × 31.25μs ≈ 8ms
        self._write8(SI1145_REG_MEASRATE0, 0xFF)

        # 启动自动连续测量
        self._write8(SI1145_REG_COMMAND, SI1145_PSALS_AUTO)

    @property
    def read_uv(self):
        """
        读取紫外线指数
        Args:
            无
        Returns:
            float: UV 指数值（原始值除以 100）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read UV index.
        Args:
            None
        Returns:
            float: UV index (raw value divided by 100)
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x2C, little_endian=True) / 100

    @property
    def read_visible(self):
        """
        读取可见光强度
        Args:
            无
        Returns:
            int: 可见光 + 红外光 ADC 原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read visible light level.
        Args:
            None
        Returns:
            int: Visible + IR light ADC raw value
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x22, little_endian=True)

    @property
    def read_ir(self):
        """
        读取红外光强度
        Args:
            无
        Returns:
            int: 红外光 ADC 原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read IR light level.
        Args:
            None
        Returns:
            int: IR light ADC raw value
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x24, little_endian=True)

    @property
    def read_prox(self):
        """
        读取接近度值
        Args:
            无
        Returns:
            int: 接近度 ADC 原始值（需外接红外 LED）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read proximity value.
        Args:
            None
        Returns:
            int: Proximity ADC raw value (requires external IR LED)
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x26, little_endian=True)


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
