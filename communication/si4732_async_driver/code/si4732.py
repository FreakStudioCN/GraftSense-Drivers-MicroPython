# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : si4732.py
# @Description : SI4732 AM/FM/SW/LW 收音机接收器 I2C 命令驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


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


try:
    from machine import Pin
except ImportError:
    pass

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class SI4732:
    """
    SI4732 AM/FM/SW/LW 收音机接收器 I2C 命令驱动类
    Attributes:
        i2c: I2C 总线实例
        address (int): I2C 从设备地址
        reset_pin: 复位引脚实例（可选）
        timeout_ms (int): CTS 等待超时时间（毫秒）
    Methods:
        reset(): 硬件复位芯片
        power_up(): 上电初始化
        power_down(): 掉电
        get_revision(): 读取固件版本信息
        get_int_status(): 读取中断状态
        set_property(): 设置属性
        get_property(): 读取属性
        fm_tune_freq(): FM 调谐
        am_tune_freq(): AM 调谐
        get_tune_status(): 读取调谐状态
        self_test(): 自检流程
        deinit(): 释放硬件资源
    Notes:
        - 本驱动为冷生成草案，尚未经过硬件验证
        - I2C 总线实例和引脚由外部创建并注入
        - 当前实现覆盖电源、属性访问、固件版本和基本 FM/AM 调谐
        - RDS、Seek、SSB 和 NBFM 等功能不在此版本中声明支持
    ==========================================
    SI4732 AM/FM/SW/LW radio receiver I2C command driver.
    Attributes:
        i2c: I2C bus instance
        address (int): I2C slave address
        reset_pin: Reset pin instance (optional)
        timeout_ms (int): CTS wait timeout in milliseconds
    Methods:
        reset(): Hardware reset the chip
        power_up(): Power up and initialize
        power_down(): Power down
        get_revision(): Read firmware revision info
        get_int_status(): Read interrupt status
        set_property(): Set a property
        get_property(): Get a property
        fm_tune_freq(): FM tune to frequency
        am_tune_freq(): AM tune to frequency
        get_tune_status(): Read tune status
        self_test(): Self-test routine
        deinit(): Release hardware resources
    Notes:
        - This driver is cold-generated and has NOT been hardware verified
        - I2C bus instance and pins are externally created and injected
        - Current scope covers power, property access, firmware revision, basic FM/AM tuning
        - RDS, Seek, SSB, and NBFM are not claimed as supported in this version
    """

    # ==================== 类级常量：I2C 地址 ====================
    ADDR_SEN_LOW = const(0x11)
    ADDR_SEN_HIGH = const(0x63)

    # ==================== 类级常量：命令字节 ====================
    _POWER_UP = const(0x01)
    _GET_REV = const(0x10)
    _POWER_DOWN = const(0x11)
    _SET_PROPERTY = const(0x12)
    _GET_PROPERTY = const(0x13)
    _GET_INT_STATUS = const(0x14)

    _FM_TUNE_FREQ = const(0x20)
    _FM_TUNE_STATUS = const(0x22)
    _AM_TUNE_FREQ = const(0x40)
    _AM_TUNE_STATUS = const(0x42)

    # ==================== 类级常量：工作模式 ====================
    FUNC_FM = const(0x00)
    FUNC_AM = const(0x01)
    _OPMODE_ANALOG_AUDIO = const(0x05)
    _OPMODE_DIGITAL_AUDIO = const(0x0B)

    # ==================== 类级常量：状态标志位 ====================
    _STATUS_CTS = const(0x80)
    _STATUS_ERR = const(0x40)
    _STATUS_STCINT = const(0x01)

    # ==================== 类级常量：I2C 重试参数 ====================
    _I2C_RETRY_COUNT = const(3)

    # ==================== __init__ ====================

    def __init__(
        self,
        i2c,
        address: int = 0x63,
        reset_pin=None,
        timeout_ms: int = 1000,
        debug: bool = False,
    ) -> None:
        """
        初始化 SI4732 I2C 命令驱动实例
        Args:
            i2c: I2C 总线实例（需提供 writeto() 和 readfrom_into() 方法）
            address (int): I2C 从设备地址，默认 0x63（ADDR_SEN_HIGH）
            reset_pin: 复位引脚实例（可选，需预初始化为输出模式）
            timeout_ms (int): CTS 等待超时时间（毫秒），默认 1000
            debug (bool): 是否启用调试日志，默认 False
        Returns:
            None
        Raises:
            TypeError: i2c 缺少必要方法
            ValueError: I2C 地址超出范围或参数类型不正确
        Notes:
            - I2C 总线和引脚由外部创建并注入，不在此处创建
            - ISR-safe: 否（init 中不执行 I/O 操作）
            - 地址 0x11 为 SEN 拉低，0x63 为 SEN 拉高（默认）
        ==========================================
        Initialize SI4732 I2C command driver instance.
        Args:
            i2c: I2C bus instance (must provide writeto() and readfrom_into())
            address (int): I2C slave address, default 0x63 (ADDR_SEN_HIGH)
            reset_pin: Reset pin instance (optional, must be pre-initialized as output)
            timeout_ms (int): CTS wait timeout in milliseconds, default 1000
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            TypeError: i2c lacks required methods
            ValueError: I2C address out of range or invalid parameter type
        Notes:
            - I2C bus and pins are externally created and injected
            - ISR-safe: No (no I/O during init)
            - Address 0x11 for SEN low, 0x63 for SEN high (default)
        """
        # ========== 参数校验 ==========
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
            raise TypeError("i2c must provide writeto() and readfrom_into()")
        if not 0 <= address <= 0x7F:
            raise ValueError("I2C address must be in 0x00..0x7F")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        # ========== 保存硬件实例引用 ==========
        self._i2c = i2c
        self._address = address
        self._reset_pin = reset_pin
        self._timeout_ms = timeout_ms
        self._debug = debug

        # ========== 预分配 I/O 缓冲区 ==========
        self._status = bytearray(1)
        self._tx = bytearray(8)
        self._retry_count = self._I2C_RETRY_COUNT

    # ==================== 公共方法：设备基础操作 ====================

    def reset(self) -> None:
        """
        硬件复位 SI4732 芯片
        Notes:
            - 拉低复位引脚 10ms 后拉高，再等待 10ms
            - ISR-safe: 否（包含延时操作）
            - 副作用：芯片所有寄存器重置为默认值
            - 复位引脚需由调用方预初始化为输出模式
        ==========================================
        Hardware reset the SI4732 chip.
        Notes:
            - Pulls reset pin low for 10ms, then high, wait 10ms
            - ISR-safe: No (contains delay operations)
            - Side effects: All chip registers reset to default values
            - Reset pin must be pre-initialized as output by caller
        """
        if self._reset_pin is None:
            return
        self._reset_pin.value(0)
        sleep_ms(10)
        self._reset_pin.value(1)
        sleep_ms(10)

    def wait_cts(self, timeout_ms: int = None) -> int:
        """
        等待 CTS（Clear To Send）标志位，确保芯片准备就绪
        Args:
            timeout_ms (int): 超时时间（毫秒），默认使用实例的 timeout_ms
        Returns:
            int: 状态字节
        Raises:
            RuntimeError: CTS 超时或芯片报告 ERR 状态
        Notes:
            - CTS 为 1 时表示芯片可以接收下一条命令
            - 自动检测 STATUS_ERR 位，若置位则抛出异常
            - ISR-safe: 否（包含轮询循环）
        ==========================================
        Wait for CTS (Clear To Send) flag, ensuring chip is ready.
        Args:
            timeout_ms (int): Timeout in milliseconds, defaults to instance timeout_ms
        Returns:
            int: Status byte
        Raises:
            RuntimeError: CTS timeout or chip reports ERR status
        Notes:
            - CTS=1 means chip is ready for next command
            - Automatically checks STATUS_ERR bit and raises on error
            - ISR-safe: No (contains polling loop)
        """
        if timeout_ms is None:
            timeout_ms = self._timeout_ms
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            try:
                self._i2c.readfrom_into(self._address, self._status)
            except OSError as exc:
                raise RuntimeError("SI4732 I2C status read failed addr=0x%02X" % self._address) from exc
            if self._status[0] & self._STATUS_CTS:
                if self._status[0] & self._STATUS_ERR:
                    raise RuntimeError("SI4732 reported ERR in status byte 0x%02X" % self._status[0])
                return self._status[0]
            sleep_ms(2)
        raise RuntimeError("SI4732 CTS timeout addr=0x%02X" % self._address)

    def command(
        self,
        cmd: int,
        args=None,
        response_len: int = 0,
    ):
        """
        发送命令并可选读取响应
        Args:
            cmd (int): 命令字节
            args: 命令参数元组，默认空
            response_len (int): 期望的响应字节数，0 表示无响应
        Returns:
            bytearray 或 None: 响应数据（response_len > 0 时），否则 None
        Raises:
            ValueError: 命令参数过多
            RuntimeError: I2C 通信失败或 CTS 超时
        Notes:
            - 先等待 CTS，再发送命令，最后读取响应（如有）
            - ISR-safe: 否
            - 副作用：触发芯片执行命令
        ==========================================
        Send a command and optionally read response.
        Args:
            cmd (int): Command byte
            args: Command argument tuple, default empty
            response_len (int): Expected response byte count, 0 = no response
        Returns:
            bytearray or None: Response data if response_len > 0, else None
        Raises:
            ValueError: Too many command arguments
            RuntimeError: I2C communication failed or CTS timeout
        Notes:
            - Waits for CTS, sends command, then reads response (if any)
            - ISR-safe: No
            - Side effects: Triggers chip to execute command
        """
        if args is None:
            args = ()
        if len(args) > len(self._tx) - 1:
            raise ValueError("too many SI4732 command arguments")
        self.wait_cts()
        self._tx[0] = cmd & 0xFF
        for index, value in enumerate(args):
            self._tx[index + 1] = value & 0xFF
        self._i2c_write_with_retry(memoryview(self._tx)[: len(args) + 1])
        if response_len:
            return self.read_response(response_len)
        return None

    def read_response(self, length: int) -> bytearray:
        """
        读取命令响应数据
        Args:
            length (int): 期望读取的字节数
        Returns:
            bytearray: 响应数据
        Raises:
            RuntimeError: CTS 超时、I2C 通信失败或响应中 ERR 位置位
        Notes:
            - 读取前等待 CTS 标志
            - 自动检测响应首字节的 ERR 位
            - ISR-safe: 否
        ==========================================
        Read command response data.
        Args:
            length (int): Number of bytes to read
        Returns:
            bytearray: Response data
        Raises:
            RuntimeError: CTS timeout, I2C communication failed, or ERR bit set in response
        Notes:
            - Waits for CTS before reading
            - Automatically checks ERR bit in first response byte
            - ISR-safe: No
        """
        self.wait_cts()
        data = bytearray(length)
        self._i2c_read_with_retry(data)
        if data and data[0] & self._STATUS_ERR:
            raise RuntimeError("SI4732 response has ERR bit set: 0x%02X" % data[0])
        return data

    # ==================== 公共方法：电源管理 ====================

    def power_up(
        self,
        func: int = 0x00,
        analog_audio: bool = True,
        xoscen: bool = True,
        gpo2_output: bool = False,
    ) -> None:
        """
        上电并初始化芯片
        Args:
            func (int): 功能模式（FUNC_FM=0x00 或 FUNC_AM=0x01），默认 FM
            analog_audio (bool): 使用模拟音频输出，默认 True
            xoscen (bool): 启用晶振，默认 True
            gpo2_output (bool): 将 GPO2 配置为输出，默认 False
        Notes:
            - 上电后需等待晶振稳定（约 500ms）或 110ms（无晶振）
            - ISR-safe: 否
            - 副作用：芯片上电并进入指定工作模式
        ==========================================
        Power up and initialize the chip.
        Args:
            func (int): Function mode (FUNC_FM=0x00 or FUNC_AM=0x01), default FM
            analog_audio (bool): Use analog audio output, default True
            xoscen (bool): Enable crystal oscillator, default True
            gpo2_output (bool): Configure GPO2 as output, default False
        Notes:
            - Wait for crystal to stabilize (~500ms) or 110ms (no crystal)
            - ISR-safe: No
            - Side effects: Chip powers up and enters specified mode
        """
        arg1 = 0
        if gpo2_output:
            arg1 |= 0x40
        if xoscen:
            arg1 |= 0x10
        arg1 |= func & 0x0F
        opmode = self._OPMODE_ANALOG_AUDIO if analog_audio else self._OPMODE_DIGITAL_AUDIO
        self.command(self._POWER_UP, (arg1, opmode), 0)
        sleep_ms(500 if xoscen else 110)
        self.wait_cts()

    def power_down(self) -> None:
        """
        掉电模式
        Notes:
            - ISR-safe: 否
            - 副作用：芯片进入低功耗状态
        ==========================================
        Power down the chip.
        Notes:
            - ISR-safe: No
            - Side effects: Chip enters low-power state
        """
        self.command(self._POWER_DOWN)
        sleep_ms(3)

    # ==================== 公共方法：设备信息查询 ====================

    def get_revision(self) -> dict:
        """
        读取芯片固件版本和部件信息
        Returns:
            dict: 包含以下字段的字典
                - status: 状态字节
                - part_number: 部件号
                - firmware_major: 固件主版本
                - firmware_minor: 固件次版本
                - patch_high: 补丁号高字节
                - patch_low: 补丁号低字节
                - component_major: 组件主版本
                - component_minor: 组件次版本
                - chip_revision: 芯片版本
        Raises:
            RuntimeError: I2C 通信失败或 CTS 超时
        Notes:
            - ISR-safe: 否
        ==========================================
        Read chip firmware revision and part information.
        Returns:
            dict: Dictionary with fields:
                - status: Status byte
                - part_number: Part number
                - firmware_major: Firmware major version
                - firmware_minor: Firmware minor version
                - patch_high: Patch number high byte
                - patch_low: Patch number low byte
                - component_major: Component major version
                - component_minor: Component minor version
                - chip_revision: Chip revision
        Raises:
            RuntimeError: I2C communication failed or CTS timeout
        Notes:
            - ISR-safe: No
        """
        resp = self.command(self._GET_REV, (), 9)
        return {
            "status": resp[0],
            "part_number": resp[1],
            "firmware_major": resp[2],
            "firmware_minor": resp[3],
            "patch_high": resp[4],
            "patch_low": resp[5],
            "component_major": resp[6],
            "component_minor": resp[7],
            "chip_revision": resp[8],
        }

    def get_int_status(self) -> int:
        """
        读取中断状态字节
        Returns:
            int: 中断状态字节
        Raises:
            RuntimeError: I2C 通信失败或 CTS 超时
        ==========================================
        Read interrupt status byte.
        Returns:
            int: Interrupt status byte
        Raises:
            RuntimeError: I2C communication failed or CTS timeout
        """
        return self.command(self._GET_INT_STATUS, (), 1)[0]

    # ==================== 公共方法：属性访问 ====================

    def set_property(self, prop: int, value: int) -> None:
        """
        设置芯片属性
        Args:
            prop (int): 属性编号（16 位）
            value (int): 属性值（16 位）
        Notes:
            - 属性编号和值参见 AN332 编程指南
            - ISR-safe: 否
            - 副作用：修改芯片属性
        ==========================================
        Set a chip property.
        Args:
            prop (int): Property number (16-bit)
            value (int): Property value (16-bit)
        Notes:
            - See AN332 programming guide for property numbers and values
            - ISR-safe: No
            - Side effects: Modifies chip property
        """
        args = (
            0x00,
            (prop >> 8) & 0xFF,
            prop & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        )
        self.command(self._SET_PROPERTY, args, 0)
        sleep_ms(1)

    def get_property(self, prop: int) -> int:
        """
        读取芯片属性
        Args:
            prop (int): 属性编号（16 位）
        Returns:
            int: 属性值（16 位）
        Raises:
            RuntimeError: I2C 通信失败或 CTS 超时
        Notes:
            - ISR-safe: 否
        ==========================================
        Get a chip property.
        Args:
            prop (int): Property number (16-bit)
        Returns:
            int: Property value (16-bit)
        Raises:
            RuntimeError: I2C communication failed or CTS timeout
        Notes:
            - ISR-safe: No
        """
        args = (0x00, (prop >> 8) & 0xFF, prop & 0xFF)
        resp = self.command(self._GET_PROPERTY, args, 4)
        return (resp[2] << 8) | resp[3]

    # ==================== 公共方法：调谐控制 ====================

    def fm_tune_freq(
        self,
        freq_khz: int,
        antenna_cap: int = 0,
        freeze: bool = False,
        fast: bool = True,
    ) -> None:
        """
        FM 频段调谐到指定频率
        Args:
            freq_khz (int): 目标频率（kHz）
            antenna_cap (int): 天线调谐电容值，默认 0
            freeze (bool): 冻结当前 RDS 数据，默认 False
            fast (bool): 快速调谐模式，默认 True
        Notes:
            - 频率需在 FM 频段范围内（通常 64-108 MHz）
            - 频率分辨率基于 10kHz 步进
            - ISR-safe: 否
            - 副作用：启动 FM 调谐流程
        ==========================================
        Tune FM to specified frequency.
        Args:
            freq_khz (int): Target frequency in kHz
            antenna_cap (int): Antenna tuning capacitor value, default 0
            freeze (bool): Freeze current RDS data, default False
            fast (bool): Fast tune mode, default True
        Notes:
            - Frequency must be in FM band range (typically 64-108 MHz)
            - Frequency resolution based on 10kHz steps
            - ISR-safe: No
            - Side effects: Initiates FM tune process
        """
        freq_10khz = int(freq_khz // 10)
        arg1 = self._tune_arg(freeze, fast)
        args = (
            arg1,
            (freq_10khz >> 8) & 0xFF,
            freq_10khz & 0xFF,
            antenna_cap & 0xFF,
        )
        self.command(self._FM_TUNE_FREQ, args, 0)

    def am_tune_freq(
        self,
        freq_khz: int,
        antenna_cap: int = 1,
        freeze: bool = False,
        fast: bool = True,
    ) -> None:
        """
        AM 频段调谐到指定频率
        Args:
            freq_khz (int): 目标频率（kHz）
            antenna_cap (int): 天线调谐电容值，默认 1
            freeze (bool): 冻结当前数据，默认 False
            fast (bool): 快速调谐模式，默认 True
        Notes:
            - 频率需在 AM/SW/LW 频段范围内
            - ISR-safe: 否
            - 副作用：启动 AM 调谐流程
        ==========================================
        Tune AM to specified frequency.
        Args:
            freq_khz (int): Target frequency in kHz
            antenna_cap (int): Antenna tuning capacitor value, default 1
            freeze (bool): Freeze current data, default False
            fast (bool): Fast tune mode, default True
        Notes:
            - Frequency must be in AM/SW/LW band range
            - ISR-safe: No
            - Side effects: Initiates AM tune process
        """
        freq = int(freq_khz)
        arg1 = self._tune_arg(freeze, fast)
        args = (
            arg1,
            (freq >> 8) & 0xFF,
            freq & 0xFF,
            (antenna_cap >> 8) & 0xFF,
            antenna_cap & 0xFF,
        )
        self.command(self._AM_TUNE_FREQ, args, 0)

    def get_tune_status(
        self,
        am: bool = False,
        intack: bool = False,
        cancel: bool = False,
    ) -> dict:
        """
        读取调谐状态
        Args:
            am (bool): AM 模式，默认 False（FM）
            intack (bool): 清除中断标志，默认 False
            cancel (bool): 取消当前调谐，默认 False
        Returns:
            dict: 包含以下字段的字典
                - status: 状态字节
                - valid: 频率是否有效
                - afc_rail: AFC 是否触及限值
                - frequency: 当前频率（FM 为 10kHz 单位，AM 为 kHz 单位）
                - rssi: 接收信号强度
                - snr: 信噪比
                - freq_offset: 频率偏移
        Raises:
            RuntimeError: I2C 通信失败或 CTS 超时
        ==========================================
        Read tune status.
        Args:
            am (bool): AM mode, default False (FM)
            intack (bool): Clear interrupt flag, default False
            cancel (bool): Cancel current tune, default False
        Returns:
            dict: Dictionary with fields:
                - status: Status byte
                - valid: Whether frequency is valid
                - afc_rail: Whether AFC hit rail
                - frequency: Current frequency (FM in 10kHz units, AM in kHz)
                - rssi: Received signal strength
                - snr: Signal-to-noise ratio
                - freq_offset: Frequency offset
        Raises:
            RuntimeError: I2C communication failed or CTS timeout
        """
        arg = (0x01 if intack else 0x00) | (0x02 if cancel else 0x00)
        cmd = self._AM_TUNE_STATUS if am else self._FM_TUNE_STATUS
        resp = self.command(cmd, (arg,), 8)
        return {
            "status": resp[0],
            "valid": bool(resp[2] & 0x01),
            "afc_rail": bool(resp[2] & 0x02),
            "frequency": (resp[3] << 8) | resp[4],
            "rssi": resp[5],
            "snr": resp[6],
            "freq_offset": resp[7],
        }

    def self_test(self) -> dict:
        """
        自检流程：I2C 扫描、上电、读取版本号、掉电
        Returns:
            dict: 固件版本信息字典（同 get_revision() 返回值）
        Raises:
            RuntimeError: I2C 地址未找到、通信失败或 CTS 超时
        Notes:
            - 仅用于调试和硬件验证
            - 副作用：执行完整的上电/掉电循环
            - ISR-safe: 否
        ==========================================
        Self-test routine: I2C scan, power up, read revision, power down.
        Returns:
            dict: Firmware revision info dict (same as get_revision() return)
        Raises:
            RuntimeError: I2C address not found, I2C communication failed or CTS timeout
        Notes:
            - For debugging and hardware verification only
            - Side effects: Performs full power-up/power-down cycle
            - ISR-safe: No
        """
        if hasattr(self._i2c, "scan") and self._address not in self._i2c.scan():
            raise RuntimeError("SI4732 address 0x%02X not found on I2C bus" % self._address)
        self.reset()
        self.power_up(self.FUNC_FM)
        revision = self.get_revision()
        self.power_down()
        return revision

    # ==================== @property ====================

    # ==================== 私有方法 ====================

    @staticmethod
    def _tune_arg(freeze: bool, fast: bool) -> int:
        """
        构造调谐参数字节
        Args:
            freeze (bool): 冻结标志
            fast (bool): 快速调谐标志
        Returns:
            int: 调谐参数字节
        ==========================================
        Build tune argument byte.
        Args:
            freeze (bool): Freeze flag
            fast (bool): Fast tune flag
        Returns:
            int: Tune argument byte
        """
        arg = 0
        if freeze:
            arg |= 0x01
        if fast:
            arg |= 0x02
        return arg

    def _i2c_write_with_retry(self, data) -> None:
        """
        带重试的 I2C 写入操作
        Args:
            data: 待写入的数据（bytes 或 memoryview）
        Raises:
            RuntimeError: 多次重试后 I2C 写入仍然失败
        ==========================================
        I2C write with retry.
        Args:
            data: Data to write (bytes or memoryview)
        Raises:
            RuntimeError: I2C write failed after all retries
        """
        last_exc = None
        for attempt in range(self._retry_count):
            try:
                self._i2c.writeto(self._address, data)
                return
            except OSError as exc:
                last_exc = exc
                if attempt < self._retry_count - 1:
                    sleep_ms(1)
        raise RuntimeError("SI4732 I2C write failed addr=0x%02X after %d retries" % (self._address, self._retry_count)) from last_exc

    def _i2c_read_with_retry(self, data: bytearray) -> None:
        """
        带重试的 I2C 读取操作
        Args:
            data (bytearray): 预分配的读取缓冲区
        Raises:
            RuntimeError: 多次重试后 I2C 读取仍然失败
        ==========================================
        I2C read with retry.
        Args:
            data (bytearray): Pre-allocated read buffer
        Raises:
            RuntimeError: I2C read failed after all retries
        """
        last_exc = None
        for attempt in range(self._retry_count):
            try:
                self._i2c.readfrom_into(self._address, data)
                return
            except OSError as exc:
                last_exc = exc
                if attempt < self._retry_count - 1:
                    sleep_ms(1)
        raise RuntimeError("SI4732 I2C read failed addr=0x%02X after %d retries" % (self._address, self._retry_count)) from last_exc

    def _log(self, msg: str) -> None:
        """
        条件调试日志输出
        Args:
            msg (str): 日志消息
        ==========================================
        Conditional debug log output.
        Args:
            msg (str): Log message
        """
        if self._debug:
            print("[SI4732] %s" % msg)

    def deinit(self) -> None:
        """
        释放硬件资源
        Notes:
            - 将芯片置为掉电模式
            - 清除 I2C 总线和引脚引用
            - 不影响外部传入的 I2C 和 Pin 实例
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Notes:
            - Puts chip in power-down mode
            - Clears I2C bus and pin references
            - Does not affect externally provided I2C and Pin instances
            - ISR-safe: No
        """
        try:
            self.power_down()
        except Exception:
            pass
        self._i2c = None
        self._reset_pin = None
        self._log("deinitialized")


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
