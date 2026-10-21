# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : es7210.py
# @Description : ES7210 四通道音频 ADC I2C 配置驱动（冷生成，未硬件验证）
# @License : MIT

__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# 为异常处理预留紧急缓冲区
try:
    from micropython import const, schedule, alloc_emergency_exception_buf

    alloc_emergency_exception_buf(100)
except ImportError:

    def const(value):
        return value

    def schedule(callback, arg):
        callback(arg)

    def alloc_emergency_exception_buf(size):
        pass


# 跨平台 time 模块兼容导入
try:
    from time import sleep_ms, ticks_diff, ticks_ms
except ImportError:
    import time

    def sleep_ms(ms):
        time.sleep(ms / 1000)

    def ticks_ms():
        return int(time.time() * 1000)

    def ticks_diff(new, old):
        return new - old


# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ES7210 默认 I2C 地址
DEFAULT_ADDRESS = const(0x40)

# 寄存器地址常量
RESET_REG00 = const(0x00)
CLOCK_OFF_REG01 = const(0x01)
MAINCLK_REG02 = const(0x02)
MASTER_CLK_REG03 = const(0x03)
LRCK_DIVH_REG04 = const(0x04)
LRCK_DIVL_REG05 = const(0x05)
POWER_DOWN_REG06 = const(0x06)
OSR_REG07 = const(0x07)
MODE_CONFIG_REG08 = const(0x08)
TIME_CONTROL0_REG09 = const(0x09)
TIME_CONTROL1_REG0A = const(0x0A)
SDP_INTERFACE1_REG11 = const(0x11)
SDP_INTERFACE2_REG12 = const(0x12)
ADC_AUTOMUTE_REG13 = const(0x13)
ADC34_HPF2_REG20 = const(0x20)
ADC34_HPF1_REG21 = const(0x21)
ADC12_HPF1_REG22 = const(0x22)
ADC12_HPF2_REG23 = const(0x23)
ANALOG_REG40 = const(0x40)
MIC12_BIAS_REG41 = const(0x41)
MIC34_BIAS_REG42 = const(0x42)
MIC1_GAIN_REG43 = const(0x43)
MIC2_GAIN_REG44 = const(0x44)
MIC3_GAIN_REG45 = const(0x45)
MIC4_GAIN_REG46 = const(0x46)
MIC1_POWER_REG47 = const(0x47)
MIC2_POWER_REG48 = const(0x48)
MIC3_POWER_REG49 = const(0x49)
MIC4_POWER_REG4A = const(0x4A)
MIC12_POWER_REG4B = const(0x4B)
MIC34_POWER_REG4C = const(0x4C)

# 采样位深常量
BITS_16 = const(16)
BITS_18 = const(18)
BITS_20 = const(20)
BITS_24 = const(24)
BITS_32 = const(32)

# 位深到 SDP_INTERFACE1 寄存器值的映射
BITS_REG_MAP = {
    BITS_16: 0x60,
    BITS_18: 0x40,
    BITS_20: 0x20,
    BITS_24: 0x00,
    BITS_32: 0x80,
}

# (mclk, sample_rate) 到寄存器系数的映射
# 格式：(ADC_DIV, DLL, DOUBLER, OSR, MCLK_SRC, LRCK_H, LRCK_L)
SAMPLE_RATE_COEFFICIENTS = {
    (4096000, 8000): (0x01, 0x01, 0x00, 0x20, 0x00, 0x02, 0x00),
    (12288000, 8000): (0x03, 0x01, 0x00, 0x20, 0x00, 0x06, 0x00),
    (4096000, 16000): (0x01, 0x01, 0x01, 0x20, 0x00, 0x01, 0x00),
    (12288000, 16000): (0x03, 0x01, 0x01, 0x20, 0x00, 0x03, 0x00),
    (12288000, 24000): (0x01, 0x01, 0x00, 0x20, 0x00, 0x02, 0x00),
    (12288000, 32000): (0x03, 0x00, 0x00, 0x20, 0x00, 0x01, 0x80),
    (11289600, 44100): (0x01, 0x01, 0x01, 0x20, 0x00, 0x01, 0x00),
    (12288000, 48000): (0x01, 0x01, 0x01, 0x20, 0x00, 0x01, 0x00),
    (12288000, 96000): (0x01, 0x01, 0x01, 0x20, 0x00, 0x00, 0x80),
}

# I2C 重试参数
I2C_RETRIES = const(2)
I2C_RETRY_DELAY_MS = const(5)

# 麦克风增益范围
MIC_GAIN_MIN_DB = const(0)
MIC_GAIN_MAX_DB = const(37.5)

# I2C 地址有效范围
I2C_ADDR_MIN = const(0x00)
I2C_ADDR_MAX = const(0x7F)

# 复用缓冲区（减少 I2C 通信内存分配）
_BUF1 = bytearray(1)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class ES7210:
    """
    ES7210 四通道音频 ADC I2C 配置控制驱动
    本驱动仅通过 I2C 配置 ES7210 寄存器（时钟、位深、采样率、增益等）。
    音频 I2S 数据流由应用层使用 machine.I2S(..., mode=I2S.RX) 独立处理，
    不在本驱动内部创建 I2S 对象。
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        sample_rate (int): 当前采样率（Hz）
        bits_per_sample (int): 当前采样位深
        mic_gain_db (float): 当前麦克风增益（dB）
        tdm (bool): 是否启用 TDM 模式
        _debug (bool): 调试日志开关
    Methods:
        scan(): 扫描 I2C 总线确认设备存在
        read_reg(): 读取单个寄存器
        write_reg(): 写入单个寄存器
        update_bits(): 更新寄存器指定位
        configure(): 完整配置设备
        reset(): 复位设备
        configure_i2s_format(): 配置 I2S 数字音频格式
        configure_sample_rate(): 配置采样率
        set_mic_gain(): 设置麦克风增益
        mute(): 静音控制
        self_test(): 自检通信功能
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 状态：冷生成草稿，未经过硬件验证
        - 音频数据读取需由应用层单独创建 machine.I2S 对象
        - I2S 数据与 I2C 配置使用不同总线，不可混淆
    ==========================================
    ES7210 four-channel audio ADC I2C configuration control driver.
    This driver only configures ES7210 registers (clock, bit depth,
    sample rate, gain, etc.) via I2C. Audio I2S data streaming is
    handled separately by the application layer using
    machine.I2S(..., mode=I2S.RX). This driver does NOT create I2S.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        sample_rate (int): Current sample rate in Hz
        bits_per_sample (int): Current bit depth
        mic_gain_db (float): Current microphone gain in dB
        tdm (bool): TDM mode enabled
        _debug (bool): Debug log switch
    Methods:
        scan(): Scan I2C bus for device presence
        read_reg(): Read single register
        write_reg(): Write single register
        update_bits(): Update specific register bits
        configure(): Full device configuration
        reset(): Reset device
        configure_i2s_format(): Configure I2S digital audio format
        configure_sample_rate(): Configure sample rate
        set_mic_gain(): Set microphone gain
        mute(): Mute control
        self_test(): Communication self-test
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided I2C instance
        - Status: Cold-generated draft, NOT hardware verified
        - Audio data reading requires separate machine.I2S object
        - I2S data and I2C config use different buses
    """

    def __init__(
        self,
        i2c,
        address: int = DEFAULT_ADDRESS,
        sample_rate: int = 16000,
        bits_per_sample: int = BITS_16,
        mic_gain_db: float = 24,
        tdm: bool = False,
        init: bool = True,
        debug: bool = False,
    ) -> None:
        """
        初始化 ES7210 音频 ADC 控制驱动
        Args:
            i2c (I2C): MicroPython I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x40
            sample_rate (int): 采样率（Hz），支持 8000/16000/24000/32000/44100/48000/96000
            bits_per_sample (int): 采样位深，支持 16/18/20/24/32
            mic_gain_db (float): 麦克风增益（dB），范围 0~37.5
            tdm (bool): 是否启用 TDM 模式，默认 False（标准 I2S）
            init (bool): 是否在初始化时自动配置设备，默认 True
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            ValueError: 参数类型或值无效
            TypeError: i2c 参数缺少必要的 I2C 方法
        Notes:
            - 驱动仅进行 I2C 寄存器配置，不创建 I2S 对象
            - 音频数据读取请使用 machine.I2S(..., mode=I2S.RX)
        ==========================================
        Initialize ES7210 audio ADC control driver.
        Args:
            i2c (I2C): MicroPython I2C bus instance
            address (int): Device I2C address, default 0x40
            sample_rate (int): Sample rate in Hz, supports 8000/16000/24000/32000/44100/48000/96000
            bits_per_sample (int): Bit depth, supports 16/18/20/24/32
            mic_gain_db (float): Microphone gain in dB, range 0~37.5
            tdm (bool): Enable TDM mode, default False (standard I2S)
            init (bool): Auto-configure device on init, default True
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: Invalid parameter type or value
            TypeError: i2c lacks required I2C methods
        Notes:
            - Driver only configures I2C registers, does not create I2S
            - For audio data, use machine.I2S(..., mode=I2S.RX)
        """
        # 参数校验：I2C 对象必须具有读写方法
        if not hasattr(i2c, "writeto_mem") or not hasattr(i2c, "readfrom_mem_into"):
            raise TypeError("i2c must provide writeto_mem() and readfrom_mem_into()")

        # 参数校验：I2C 地址范围
        if not isinstance(address, int) or not I2C_ADDR_MIN <= address <= I2C_ADDR_MAX:
            raise ValueError("address must be int in 0x00..0x7F, got %s" % repr(address))

        # 参数校验：采样率
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise ValueError("sample_rate must be positive int, got %s" % repr(sample_rate))

        # 参数校验：位深
        if bits_per_sample not in BITS_REG_MAP:
            raise ValueError("bits_per_sample must be 16, 18, 20, 24, or 32, got %s" % repr(bits_per_sample))

        # 参数校验：增益范围
        if not isinstance(mic_gain_db, (int, float)):
            raise ValueError("mic_gain_db must be int or float, got %s" % type(mic_gain_db))
        if mic_gain_db < MIC_GAIN_MIN_DB or mic_gain_db > MIC_GAIN_MAX_DB:
            raise ValueError("mic_gain_db must be %.1f~%.1f, got %s" % (MIC_GAIN_MIN_DB, MIC_GAIN_MAX_DB, mic_gain_db))

        # 参数校验：debug 标志
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = address
        self._debug = debug
        self.sample_rate = sample_rate
        self.bits_per_sample = bits_per_sample
        self.mic_gain_db = mic_gain_db
        self.tdm = bool(tdm)

        # 初始化时自动配置设备
        if init:
            self.configure(sample_rate, bits_per_sample, mic_gain_db, tdm)

    # ==================== 公共方法 ====================

    def scan(self) -> bool:
        """
        扫描 I2C 总线确认设备地址是否可见
        Returns:
            bool: True 表示设备地址在 I2C 扫描列表中
        Raises:
            RuntimeError: I2C 总线不支持 scan() 方法
        Notes:
            - 依赖 I2C 实例的 scan() 方法
            - ISR-safe: 否
        ==========================================
        Scan I2C bus to confirm device address is visible.
        Returns:
            bool: True if device address found in I2C scan
        Raises:
            RuntimeError: I2C bus does not support scan()
        Notes:
            - Requires I2C instance scan() method
            - ISR-safe: No
        """
        if not hasattr(self._i2c, "scan"):
            raise RuntimeError("I2C bus does not support scan()")
        return self._addr in self._i2c.scan()

    def read_reg(self, reg: int) -> int:
        """
        读取单个 8 位寄存器值
        Args:
            reg (int): 寄存器地址（0x00~0xFF）
        Returns:
            int: 寄存器当前值（0~255）
        Raises:
            RuntimeError: I2C 读取失败（重试后仍失败）
        Notes:
            - 带自动重试机制
            - ISR-safe: 否
        ==========================================
        Read single 8-bit register value.
        Args:
            reg (int): Register address (0x00~0xFF)
        Returns:
            int: Current register value (0~255)
        Raises:
            RuntimeError: I2C read failed after retries
        Notes:
            - Includes automatic retry mechanism
            - ISR-safe: No
        """
        _BUF1[0] = 0
        for attempt in range(I2C_RETRIES + 1):
            try:
                self._i2c.readfrom_mem_into(self._addr, reg & 0xFF, _BUF1)
                return _BUF1[0]
            except OSError as e:
                if attempt == I2C_RETRIES:
                    raise RuntimeError(
                        "ES7210 I2C read failed addr=0x%02X reg=0x%02X after %d retries" % (self._addr, reg & 0xFF, I2C_RETRIES)
                    ) from e
                sleep_ms(I2C_RETRY_DELAY_MS)

    def write_reg(self, reg: int, value: int) -> None:
        """
        写入单个 8 位寄存器值
        Args:
            reg (int): 寄存器地址（0x00~0xFF）
            value (int): 要写入的值（0~255）
        Raises:
            RuntimeError: I2C 写入失败（重试后仍失败）
        Notes:
            - 带自动重试机制
            - ISR-safe: 否
        ==========================================
        Write single 8-bit register value.
        Args:
            reg (int): Register address (0x00~0xFF)
            value (int): Value to write (0~255)
        Raises:
            RuntimeError: I2C write failed after retries
        Notes:
            - Includes automatic retry mechanism
            - ISR-safe: No
        """
        _BUF1[0] = value & 0xFF
        for attempt in range(I2C_RETRIES + 1):
            try:
                self._i2c.writeto_mem(self._addr, reg & 0xFF, _BUF1)
                return
            except OSError as e:
                if attempt == I2C_RETRIES:
                    raise RuntimeError(
                        "ES7210 I2C write failed addr=0x%02X reg=0x%02X value=0x%02X after %d retries"
                        % (self._addr, reg & 0xFF, value & 0xFF, I2C_RETRIES)
                    ) from e
                sleep_ms(I2C_RETRY_DELAY_MS)

    def update_bits(self, reg: int, mask: int, value: int) -> None:
        """
        更新寄存器中指定位的数据（读-修改-写操作）
        Args:
            reg (int): 寄存器地址
            mask (int): 位掩码，指定要修改的位
            value (int): 要设置的新值（仅 mask 指定的位生效）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：执行读-修改-写操作，修改寄存器内容
            - 非原子操作，ISR 中使用需谨慎
            - ISR-safe: 否
        ==========================================
        Update specific bits in a register (read-modify-write).
        Args:
            reg (int): Register address
            mask (int): Bit mask specifying which bits to modify
            value (int): New value (only bits within mask take effect)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: Performs read-modify-write on register
            - Non-atomic operation, use with caution in ISR
            - ISR-safe: No
        """
        current = self.read_reg(reg)
        updated = (current & (~mask & 0xFF)) | (value & mask)
        self.write_reg(reg, updated)

    def configure(self, sample_rate: int = None, bits_per_sample: int = None, mic_gain_db: float = None, tdm: bool = None) -> None:
        """
        完整配置 ES7210 所有功能寄存器
        依次执行：复位 → 时钟 → 高通滤波 → I2S 格式 → 采样率 → 增益 → 电源
        Args:
            sample_rate (int): 采样率，None 表示使用当前值
            bits_per_sample (int): 采样位深，None 表示使用当前值
            mic_gain_db (float): 麦克风增益（dB），None 表示使用当前值
            tdm (bool): TDM 模式，None 表示使用当前值
        Raises:
            RuntimeError: I2C 通信失败
            ValueError: 参数值无效
        Notes:
            - 副作用：修改数十个寄存器，彻底重新配置设备
            - 状态：冷生成代码，寄存器值未经硬件验证
            - ISR-safe: 否
        ==========================================
        Full ES7210 register configuration.
        Sequential: reset → clock → HPF → I2S format → sample rate → gain → power
        Args:
            sample_rate (int): Sample rate, None to keep current
            bits_per_sample (int): Bit depth, None to keep current
            mic_gain_db (float): Mic gain in dB, None to keep current
            tdm (bool): TDM mode, None to keep current
        Raises:
            RuntimeError: I2C communication failed
            ValueError: Invalid parameter value
        Notes:
            - Side effect: Modifies dozens of registers, fully reconfigures device
            - Status: Cold-generated code, register values not hardware verified
            - ISR-safe: No
        """
        # 更新配置参数
        if sample_rate is not None:
            self.sample_rate = sample_rate
        if bits_per_sample is not None:
            self.bits_per_sample = bits_per_sample
        if mic_gain_db is not None:
            self.mic_gain_db = mic_gain_db
        if tdm is not None:
            self.tdm = bool(tdm)

        # 按数据手册推荐顺序配置寄存器
        self.reset()
        self.write_reg(CLOCK_OFF_REG01, 0x3F)
        self.write_reg(TIME_CONTROL0_REG09, 0x30)
        self.write_reg(TIME_CONTROL1_REG0A, 0x30)
        self.write_reg(ADC12_HPF2_REG23, 0x2A)
        self.write_reg(ADC12_HPF1_REG22, 0x0A)
        self.write_reg(ADC34_HPF2_REG20, 0x0A)
        self.write_reg(ADC34_HPF1_REG21, 0x2A)
        self.update_bits(MODE_CONFIG_REG08, 0x01, 0x00)
        self.write_reg(ANALOG_REG40, 0xC3)
        self.write_reg(MIC12_BIAS_REG41, 0x70)
        self.write_reg(MIC34_BIAS_REG42, 0x70)
        self.configure_i2s_format(self.bits_per_sample, self.tdm)
        self.configure_sample_rate(self.sample_rate)
        self.set_mic_gain(self.mic_gain_db)
        # 使能四路麦克风通道
        self.write_reg(MIC1_POWER_REG47, 0x08)
        self.write_reg(MIC2_POWER_REG48, 0x08)
        self.write_reg(MIC3_POWER_REG49, 0x08)
        self.write_reg(MIC4_POWER_REG4A, 0x08)
        self.write_reg(POWER_DOWN_REG06, 0x04)
        self.write_reg(MIC12_POWER_REG4B, 0x0F)
        self.write_reg(MIC34_POWER_REG4C, 0x0F)
        # 启动设备正常模式
        self.write_reg(RESET_REG00, 0x71)
        self.write_reg(RESET_REG00, 0x41)

    def reset(self) -> None:
        """
        软复位设备
        Notes:
            - 副作用：重置所有寄存器为默认值
            - 复位过程需要约 4ms（两次 2ms 延时）
            - ISR-safe: 否
        ==========================================
        Soft reset the device.
        Notes:
            - Side effect: Resets all registers to defaults
            - Reset takes approximately 4ms (two 2ms delays)
            - ISR-safe: No
        """
        self.write_reg(RESET_REG00, 0xFF)
        sleep_ms(2)
        self.write_reg(RESET_REG00, 0x32)
        sleep_ms(2)

    def configure_i2s_format(self, bits_per_sample: int = None, tdm: bool = None) -> None:
        """
        配置 I2S 数字音频接口格式（位深和 TDM 模式）
        Args:
            bits_per_sample (int): 采样位深（16/18/20/24/32），None 使用当前值
            tdm (bool): TDM 模式，None 使用当前值
        Raises:
            ValueError: bits_per_sample 不支持
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改 SDP_INTERFACE1 和 SDP_INTERFACE2 寄存器
            - 更新实例的 bits_per_sample 和 tdm 属性
            - ISR-safe: 否
        ==========================================
        Configure I2S digital audio interface format (bit depth and TDM).
        Args:
            bits_per_sample (int): Bit depth (16/18/20/24/32), None to keep current
            tdm (bool): TDM mode, None to keep current
        Raises:
            ValueError: Unsupported bits_per_sample
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: Modifies SDP_INTERFACE1 and SDP_INTERFACE2 registers
            - Updates instance bits_per_sample and tdm attributes
            - ISR-safe: No
        """
        if bits_per_sample is not None:
            if isinstance(bits_per_sample, int):
                pass
            else:
                bits_per_sample = self.bits_per_sample
        else:
            bits_per_sample = self.bits_per_sample
        if tdm is not None:
            tdm = bool(tdm)
        else:
            tdm = self.tdm

        if bits_per_sample not in BITS_REG_MAP:
            raise ValueError("bits_per_sample must be 16, 18, 20, 24, or 32, got %s" % repr(bits_per_sample))

        self.write_reg(SDP_INTERFACE1_REG11, BITS_REG_MAP[bits_per_sample])
        self.write_reg(SDP_INTERFACE2_REG12, 0x02 if tdm else 0x00)
        self.bits_per_sample = bits_per_sample
        self.tdm = tdm

    def configure_sample_rate(self, sample_rate: int) -> None:
        """
        配置采样率（通过设置 MCLK 分频器和相关寄存器）
        Args:
            sample_rate (int): 目标采样率（Hz），支持 8000/16000/24000/32000/44100/48000/96000
        Raises:
            ValueError: 采样率不支持
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改 MAINCLK/OSR/MASTER_CLK/LRCK_DIV 等多个寄存器
            - MCLK = sample_rate * 256（自动计算）
            - ISR-safe: 否
        ==========================================
        Configure sample rate (via MCLK divider and related registers).
        Args:
            sample_rate (int): Target sample rate in Hz, supports 8000/16000/24000/32000/44100/48000/96000
        Raises:
            ValueError: Unsupported sample rate
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: Modifies MAINCLK/OSR/MASTER_CLK/LRCK_DIV registers
            - MCLK = sample_rate * 256 (auto-calculated)
            - ISR-safe: No
        """
        mclk = sample_rate * 256
        coeff = SAMPLE_RATE_COEFFICIENTS.get((mclk, sample_rate))
        if coeff is None:
            raise ValueError("Unsupported sample_rate/mclk pair: %d Hz (mclk=%d)" % (sample_rate, mclk))

        # 解包系数并写入对应寄存器
        adc_div, dll, doubler, osr, mclk_src, lrck_h, lrck_l = coeff
        self.write_reg(MAINCLK_REG02, adc_div | (doubler << 6) | (dll << 7))
        self.write_reg(OSR_REG07, osr)
        self.write_reg(MASTER_CLK_REG03, mclk_src)
        self.write_reg(LRCK_DIVH_REG04, lrck_h)
        self.write_reg(LRCK_DIVL_REG05, lrck_l)
        self.sample_rate = sample_rate

    def set_mic_gain(self, mic_gain_db: float) -> None:
        """
        设置四通道麦克风增益
        Args:
            mic_gain_db (float): 增益值（dB），范围 0.0~37.5
        Raises:
            ValueError: 增益值超出范围
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改四路 MICx_GAIN 寄存器
            - 增益步进为 3dB，通过查表映射
            - 四路通道设置为相同增益值
            - ISR-safe: 否
        ==========================================
        Set four-channel microphone gain.
        Args:
            mic_gain_db (float): Gain value in dB, range 0.0~37.5
        Raises:
            ValueError: Gain value out of range
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: Modifies four MICx_GAIN registers
            - Gain step is 3 dB, mapped via lookup table
            - All four channels set to the same gain value
            - ISR-safe: No
        """
        reg_value = self._gain_to_reg(mic_gain_db)
        for reg in (MIC1_GAIN_REG43, MIC2_GAIN_REG44, MIC3_GAIN_REG45, MIC4_GAIN_REG46):
            self.update_bits(reg, 0x10, 0x10)
            self.update_bits(reg, 0x0F, reg_value)
        self.mic_gain_db = mic_gain_db

    def mute(self, enabled: bool = True) -> None:
        """
        控制音频输出静音
        Args:
            enabled (bool): True 静音，False 取消静音
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改 ADC_AUTOMUTE 寄存器
            - ISR-safe: 否
        ==========================================
        Control audio output mute.
        Args:
            enabled (bool): True to mute, False to unmute
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: Modifies ADC_AUTOMUTE register
            - ISR-safe: No
        """
        self.write_reg(ADC_AUTOMUTE_REG13, 0x0F if enabled else 0x00)

    def self_test(self, timeout_ms: int = 1000) -> bool:
        """
        基本通信自检：写入测试寄存器并回读验证
        Args:
            timeout_ms (int): 超时时间（毫秒），默认 1000ms
        Returns:
            bool: True 表示通信正常
        Raises:
            RuntimeError: 设备未找到或通信超时
        Notes:
            - 先恢复原始寄存���值再返回
            - 状态：自检逻辑未经过硬件验证
            - ISR-safe: 否
        ==========================================
        Basic communication self-test: write test register and read back.
        Args:
            timeout_ms (int): Timeout in milliseconds, default 1000ms
        Returns:
            bool: True if communication is working
        Raises:
            RuntimeError: Device not found or communication timeout
        Notes:
            - Restores original register value before returning
            - Status: Self-test logic not hardware verified
            - ISR-safe: No
        """
        # 先确认 I2C 地址可见
        if not self.scan():
            raise RuntimeError("ES7210 address 0x%02X not found on I2C bus" % self._addr)

        start = ticks_ms()
        test_reg = TIME_CONTROL0_REG09
        original = self.read_reg(test_reg)
        self.write_reg(test_reg, 0x30)

        # 带超时的回读验证
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            if self.read_reg(test_reg) == 0x30:
                self.write_reg(test_reg, original)
                return True
            sleep_ms(5)

        # 超时恢复原始值
        self.write_reg(test_reg, original)
        raise RuntimeError("ES7210 self-test timed out reading back reg 0x%02X" % test_reg)

    def deinit(self) -> None:
        """
        释放硬件资源
        Notes:
            - 副作用：静音输出并关闭设备电源
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Notes:
            - Side effect: Mutes output and powers down device
            - ISR-safe: No
        """
        self.mute(True)
        self.write_reg(POWER_DOWN_REG06, 0xFF)

    # ==================== 私有方法 ====================

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅在 debug=True 时输出
            - ISR-safe: 否
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Output only when debug=True
            - ISR-safe: No
        """
        if self._debug:
            print("[ES7210] %s" % msg)

    # ==================== 静态方法 ====================

    @staticmethod
    def _gain_to_reg(mic_gain_db: float) -> int:
        """
        将 dB 增益值转换为寄存器值
        Args:
            mic_gain_db (float): 增益值（dB）
        Returns:
            int: 寄存器低 4 位值（0~14）
        Raises:
            ValueError: 增益值超出范围
        ==========================================
        Convert dB gain value to register value.
        Args:
            mic_gain_db (float): Gain value in dB
        Returns:
            int: Register lower 4-bit value (0~14)
        Raises:
            ValueError: Gain value out of range
        """
        if mic_gain_db < MIC_GAIN_MIN_DB or mic_gain_db > MIC_GAIN_MAX_DB:
            raise ValueError("mic_gain_db must be between %d and %.1f, got %.1f" % (MIC_GAIN_MIN_DB, MIC_GAIN_MAX_DB, mic_gain_db))
        gain = mic_gain_db + 0.5
        if gain <= 33:
            return int(gain / 3) & 0x0F
        if gain < 36:
            return 12
        if gain < 37:
            return 13
        return 14


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
