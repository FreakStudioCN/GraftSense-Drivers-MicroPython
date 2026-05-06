# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 12:00
# @Author  : Jose D. Montoya
# @File    : isl29125.py
# @Description : ISL29125 RGB颜色传感器驱动，支持工作模式、量程、ADC分辨率、IR补偿及中断控制
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
from micropython_isl29125.i2c_helpers import CBits, RegisterStruct

# ======================================== 全局变量 ============================================

# 寄存器地址
_REG_WHOAMI    = const(0x00)
_CONFIG1       = const(0x01)
_CONFIG2       = const(0x02)
_CONFIG3       = const(0x03)
_FLAG_REGISTER = const(0x08)

# 工作模式常量
POWERDOWN      = const(0b000)
GREEN_ONLY     = const(0b001)
RED_ONLY       = const(0b010)
BLUE_ONLY      = const(0b011)
STANDBY        = const(0b100)
RED_GREEN_BLUE = const(0b101)
GREEN_RED      = const(0b110)
GREEN_BLUE     = const(0b111)

operation_values = (
    POWERDOWN, GREEN_ONLY, RED_ONLY, BLUE_ONLY,
    STANDBY, RED_GREEN_BLUE, GREEN_RED, GREEN_BLUE,
)

# 感光量程常量
LUX_375 = const(0b0)
LUX_10K = const(0b1)
sensing_range_values = (LUX_375, LUX_10K)

# ADC分辨率常量
RES_16BITS = const(0b0)
RES_12BITS = const(0b1)

# 中断通道常量
NO_INTERRUPT    = const(0b00)
GREEN_INTERRUPT = const(0b01)
RED_INTERRUPT   = const(0b10)
BLUE_INTERRUPT  = const(0b11)
interrupt_values = (NO_INTERRUPT, GREEN_INTERRUPT, RED_INTERRUPT, BLUE_INTERRUPT)

# 中断持续控制常量
IC1 = const(0b00)
IC2 = const(0b01)
IC4 = const(0b10)
IC8 = const(0b11)
persistent_control_values = (IC1, IC2, IC4, IC8)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class ISL29125:
    """
    ISL29125 RGB颜色传感器驱动类（I2C接口）
    Attributes:
        _i2c (I2C): I2C总线实例
        _address (int): 设备I2C地址，默认0x44
    Methods:
        colors: 读取RGB三通道原始值
        red / green / blue: 分别读取单通道原始值
        operation_mode: 获取/设置工作模式
        sensing_range: 获取/设置感光量程
        adc_resolution: 获取/设置ADC分辨率
        ir_compensation: 获取/设置IR补偿开关
        ir_compensation_value: 获取/设置IR补偿值
        interrupt_threshold: 获取/设置中断通道
        high_threshold / low_threshold: 获取/设置中断阈值
        interrupt_triggered: 读取中断触发状态
        persistent_control: 获取/设置中断持续控制
        clear_register_flag(): 清除标志寄存器
        deinit(): 释放资源
    Notes:
        - 依赖外部传入I2C实例，不在内部创建
        - 初始化时自动写入芯片推荐默认配置
    ==========================================
    ISL29125 RGB color sensor driver (I2C interface).
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address, default 0x44
    Methods:
        colors: Read raw RGB values for all three channels
        red / green / blue: Read individual channel raw values
        operation_mode: Get/set operating mode
        sensing_range: Get/set sensing range
        adc_resolution: Get/set ADC resolution
        ir_compensation: Get/set IR compensation enable
        ir_compensation_value: Get/set IR compensation level
        interrupt_threshold: Get/set interrupt channel
        high_threshold / low_threshold: Get/set interrupt thresholds
        interrupt_triggered: Read interrupt triggered status
        persistent_control: Get/set interrupt persistence control
        clear_register_flag(): Clear flag register
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Applies chip-recommended default config on init
    """

    # 类级寄存器描述符
    _device_id      = RegisterStruct(_REG_WHOAMI, "B")
    _conf_reg       = RegisterStruct(_CONFIG1, "B")
    _conf_reg2      = RegisterStruct(_CONFIG2, "B")
    _conf_reg3      = RegisterStruct(_CONFIG3, "B")
    _low_threshold  = RegisterStruct(0x04, "h")
    _high_threshold = RegisterStruct(0x06, "h")
    _flag_register  = RegisterStruct(0x08, "B")

    _green = RegisterStruct(0x09, "h")
    _red   = RegisterStruct(0x0B, "h")
    _blue  = RegisterStruct(0x0D, "h")

    _operation_mode               = CBits(3, _CONFIG1, 0)
    _rgb_sensing_range            = CBits(1, _CONFIG1, 3)
    _adc_resolution               = CBits(1, _CONFIG1, 3)
    _ir_compensation              = CBits(1, _CONFIG2, 7)
    _ir_compensation_value        = CBits(6, _CONFIG2, 0)
    _interrupt_threshold_status   = CBits(2, _CONFIG3, 0)
    _interrupt_persistent_control = CBits(2, _CONFIG3, 2)
    _interrupt_triggered_status   = CBits(1, _FLAG_REGISTER, 0)
    _brown_out                    = CBits(1, _FLAG_REGISTER, 2)

    def __init__(self, i2c, address: int = 0x44) -> None:
        """
        初始化ISL29125传感器
        Args:
            i2c: I2C总线实例，需支持 readfrom_mem / writeto_mem 接口
            address (int): I2C设备地址，默认0x44
        Returns:
            None
        Raises:
            ValueError: i2c参数不具备I2C接口特征，或address超出范围
            RuntimeError: 设备ID校验失败，传感器未找到
        Notes:
            - ISR-safe: 否
            - 副作用：向传感器写入默认CONFIG1/CONFIG2配置，清除标志寄存器，复位brownout位
        ==========================================
        Initialize ISL29125 sensor.
        Args:
            i2c: I2C bus instance supporting readfrom_mem / writeto_mem
            address (int): I2C device address, default 0x44
        Returns:
            None
        Raises:
            ValueError: i2c does not have I2C interface, or address out of range
            RuntimeError: Device ID check failed, sensor not found
        Notes:
            - ISR-safe: No
            - Side effects: Writes default CONFIG1/CONFIG2, clears flag register, resets brownout bit
        """
        # 鸭子类型检查I2C接口
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int) or not (0x00 <= address <= 0x7F):
            raise ValueError("address must be int in 0x00~0x7F, got %s" % address)

        self._i2c = i2c
        self._address = address

        # 校验设备ID（期望0x7D）
        if self._device_id != 0x7D:
            raise RuntimeError("Failed to find ISL29125, check wiring/address")

        # 写入CONFIG1默认值：RGB全通道+10K量程+16bit（0x0D = 0b00001101）
        self._conf_reg = 0x0D
        # 写入CONFIG2默认值：最大IR补偿（数据手册推荐，使高量程超过10000lux）
        self._conf_reg2 = 0xBF
        # 清除标志寄存器
        self.clear_register_flag()
        # 复位brownout位（数据手册推荐设为0）
        self._brown_out = 0

    @property
    def red(self) -> int:
        """
        读取红色通道原始ADC值
        Args:
            无
        Returns:
            int: 红色通道原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw ADC value for red channel.
        Args:
            None
        Returns:
            int: Raw red channel value
        Notes:
            - ISR-safe: No
        """
        return self._red

    @property
    def green(self) -> int:
        """
        读取绿色通道原始ADC值
        Args:
            无
        Returns:
            int: 绿色通道原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw ADC value for green channel.
        Args:
            None
        Returns:
            int: Raw green channel value
        Notes:
            - ISR-safe: No
        """
        return self._green

    @property
    def blue(self) -> int:
        """
        读取蓝色通道原始ADC值
        Args:
            无
        Returns:
            int: 蓝色通道原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw ADC value for blue channel.
        Args:
            None
        Returns:
            int: Raw blue channel value
        Notes:
            - ISR-safe: No
        """
        return self._blue

    @property
    def colors(self) -> tuple:
        """
        同时读取红、绿、蓝三通道原始ADC值
        Args:
            无
        Returns:
            tuple: (red, green, blue) 三通道原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw ADC values for all three channels simultaneously.
        Args:
            None
        Returns:
            tuple: (red, green, blue) raw channel values
        Notes:
            - ISR-safe: No
        """
        return self._red, self._green, self._blue

    @property
    def operation_mode(self) -> str:
        """
        获取当前工作模式
        Args:
            无
        Returns:
            str: 当前工作模式名称
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 可用模式：POWERDOWN/GREEN_ONLY/RED_ONLY/BLUE_ONLY/STANDBY/RED_GREEN_BLUE/GREEN_RED/GREEN_BLUE
        ==========================================
        Get current operating mode.
        Args:
            None
        Returns:
            str: Current operating mode name
        Notes:
            - ISR-safe: No
        """
        values = (
            "POWERDOWN", "GREEN_ONLY", "RED_ONLY", "BLUE_ONLY",
            "STANDBY", "RED_GREEN_BLUE", "GREEN_RED", "GREEN_BLUE",
        )
        # 读取CONFIG1寄存器低3位返回模式名称
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        if value not in operation_values:
            raise ValueError("operation_mode must be one of operation_values, got %s" % value)
        # 写入CONFIG1寄存器工作模式位
        self._operation_mode = value

    @property
    def sensing_range(self) -> str:
        """
        获取当前感光量程
        Args:
            无
        Returns:
            str: "LUX_375"（375lux）或 "LUX_10K"（10000lux）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Get current sensing range.
        Args:
            None
        Returns:
            str: "LUX_375" (375 lux) or "LUX_10K" (10000 lux)
        Notes:
            - ISR-safe: No
        """
        values = ("LUX_375", "LUX_10K")
        # 读取CONFIG1寄存器bit3量程标志
        return values[self._rgb_sensing_range]

    @sensing_range.setter
    def sensing_range(self, value: int) -> None:
        if value not in sensing_range_values:
            raise ValueError("sensing_range must be LUX_375 or LUX_10K, got %s" % value)
        # 写入CONFIG1寄存器量程位
        self._rgb_sensing_range = value

    @property
    def adc_resolution(self) -> str:
        """
        获取当前ADC分辨率
        Args:
            无
        Returns:
            str: "RES_16BITS" 或 "RES_12BITS"
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 分辨率影响ADC时钟周期数和积分时间
        ==========================================
        Get current ADC resolution.
        Args:
            None
        Returns:
            str: "RES_16BITS" or "RES_12BITS"
        Notes:
            - ISR-safe: No
        """
        values = ("RES_16BITS", "RES_12BITS")
        # 读取CONFIG1寄存器分辨率位
        return values[self._adc_resolution]

    @adc_resolution.setter
    def adc_resolution(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("adc_resolution must be 0 (16bit) or 1 (12bit), got %s" % value)
        # 写入CONFIG1寄存器ADC分辨率位
        self._adc_resolution = value

    @property
    def ir_compensation(self) -> int:
        """
        获取IR补偿开关状态
        Args:
            无
        Returns:
            int: 1表示开启，0表示关闭
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Get IR compensation enable state.
        Args:
            None
        Returns:
            int: 1=enabled, 0=disabled
        Notes:
            - ISR-safe: No
        """
        return self._ir_compensation

    @ir_compensation.setter
    def ir_compensation(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("ir_compensation must be 0 or 1, got %s" % value)
        # 写入CONFIG2寄存器IR补偿使能位
        self._ir_compensation = value

    @property
    def ir_compensation_value(self) -> int:
        """
        获取IR补偿值（CONFIG2寄存器低6位）
        Args:
            无
        Returns:
            int: 当前IR补偿原始值（位权：BIT5=32...BIT0=1）
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 有效补偿范围：寄存器值106~169（数据手册第15页）
        ==========================================
        Get IR compensation value (CONFIG2 lower 6 bits).
        Args:
            None
        Returns:
            int: Current IR compensation raw value (bit weights: BIT5=32...BIT0=1)
        Notes:
            - ISR-safe: No
        """
        return self._ir_compensation_value

    @ir_compensation_value.setter
    def ir_compensation_value(self, value: int) -> None:
        if value not in (1, 2, 4, 8, 16, 32):
            raise ValueError("ir_compensation_value must be one of (1,2,4,8,16,32), got %s" % value)
        # 写入CONFIG2寄存器IR补偿值
        self._ir_compensation_value = value

    @property
    def interrupt_threshold(self) -> str:
        """
        获取中断触发通道
        Args:
            无
        Returns:
            str: 当前中断通道名称
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 中断在光强超出阈值窗口（0x04~0x07）时触发
        ==========================================
        Get interrupt trigger channel.
        Args:
            None
        Returns:
            str: Current interrupt channel name
        Notes:
            - ISR-safe: No
        """
        values = ("No Interrupt", "Green Interrupt", "Red Interrupt", "Blue Interrupt")
        # 读取CONFIG3寄存器低2位中断通道状态
        return values[self._interrupt_threshold_status]

    @interrupt_threshold.setter
    def interrupt_threshold(self, value: int) -> None:
        if value not in interrupt_values:
            raise ValueError("interrupt_threshold must be one of interrupt_values, got %s" % value)
        # 写入CONFIG3寄存器中断通道位
        self._interrupt_threshold_status = value

    @property
    def high_threshold(self) -> int:
        """
        获取中断高阈值（16位）
        Args:
            无
        Returns:
            int: 当前高阈值寄存器值
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 光强超过此值时中断触发（寄存器地址0x06~0x07）
        ==========================================
        Get interrupt high threshold (16-bit).
        Args:
            None
        Returns:
            int: Current high threshold register value
        Notes:
            - ISR-safe: No
        """
        return self._high_threshold

    @high_threshold.setter
    def high_threshold(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("high_threshold must be int, got %s" % type(value).__name__)
        # 写入高阈值寄存器
        self._high_threshold = value

    @property
    def low_threshold(self) -> int:
        """
        获取中断低阈值（16位）
        Args:
            无
        Returns:
            int: 当前低阈值寄存器值
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 光强低于此值时中断触发（寄存器地址0x04~0x05）
        ==========================================
        Get interrupt low threshold (16-bit).
        Args:
            None
        Returns:
            int: Current low threshold register value
        Notes:
            - ISR-safe: No
        """
        return self._low_threshold

    @low_threshold.setter
    def low_threshold(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("low_threshold must be int, got %s" % type(value).__name__)
        # 写入低阈值寄存器
        self._low_threshold = value

    @property
    def interrupt_triggered(self) -> int:
        """
        读取中断触发状态位
        Args:
            无
        Returns:
            int: 1表示中断已触发，0表示未触发或已清除
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 调用 clear_register_flag() 后此位复位
        ==========================================
        Read interrupt triggered status bit.
        Args:
            None
        Returns:
            int: 1=triggered, 0=not triggered or cleared
        Notes:
            - ISR-safe: No
        """
        # 读取FLAG寄存器bit0中断触发状态
        return self._interrupt_triggered_status

    @property
    def persistent_control(self) -> str:
        """
        获取中断持续控制模式
        Args:
            无
        Returns:
            str: "IC1"/"IC2"/"IC4"/"IC8"
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - ICn表示需要连续n次越阈中断才驱动INT引脚为低
        ==========================================
        Get interrupt persistence control mode.
        Args:
            None
        Returns:
            str: "IC1"/"IC2"/"IC4"/"IC8"
        Notes:
            - ISR-safe: No
        """
        values = ("IC1", "IC2", "IC4", "IC8")
        # 读取CONFIG3寄存器bit2:3中断持续控制位
        return values[self._interrupt_persistent_control]

    @persistent_control.setter
    def persistent_control(self, value: int) -> None:
        if value not in persistent_control_values:
            raise ValueError("persistent_control must be one of persistent_control_values, got %s" % value)
        # 写入CONFIG3寄存器中断持续控制位
        self._interrupt_persistent_control = value

    def clear_register_flag(self) -> int:
        """
        清除中断标志寄存器（通过读操作自动清除）
        Args:
            无
        Returns:
            int: 读取到的标志寄存器原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 副作用：硬件FLAG寄存器被读取后自动复位
        ==========================================
        Clear the interrupt flag register (auto-cleared by read).
        Args:
            None
        Returns:
            int: Raw flag register value before clear
        Notes:
            - ISR-safe: No
            - Side effects: Hardware FLAG register resets after read
        """
        # 读取FLAG寄存器触发硬件自动清零
        return self._flag_register

    def deinit(self) -> None:
        """
        释放传感器资源，将设备置于掉电模式
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 副作用：向CONFIG1写入POWERDOWN模式，停止ADC采集
        ==========================================
        Release sensor resources and set device to power-down mode.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Writes POWERDOWN to CONFIG1, stops ADC conversion
        """
        # 写入掉电模式，停止ADC采集，降低功耗
        self._operation_mode = POWERDOWN


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
