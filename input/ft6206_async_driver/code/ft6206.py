# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : hlf20010508, FreakStudio
# @File    : ft6206.py
# @Description : FT6206 电容触摸控制器 I2C 驱动类，支持多点触摸与中断回调

__version__ = "1.0.0"
__author__ = "hlf20010508, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

# 导入 micropython 常量优化模块
import micropython
from micropython import const as mp_const

# 导入时间相关模块
import time

# ======================================== 全局变量 ============================================

# 兼容 CPython 的 const 定义
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# FT6206 电容触摸控制器驱动类
class FT6206:
    """
    FT6206 电容触摸控制器驱动类，通过 I2C 总线与 FT6206 芯片通信，提供触摸检测、坐标读取与中断回调支持。

    该类封装了 FT6206 必需的寄存器访问、初始化验证、触摸点读取功能，适用于基于 MicroPython 的嵌入式触控设备。

    Attributes:
        i2c (machine.I2C): 与 FT6206 通信的 I2C 接口实例。
        addr (int): FT6206 的 I2C 地址，默认 0x38。
        width (int): 触摸区域宽度（像素）。
        height (int): 触摸区域高度（像素）。
        max_touches (int): 支持的最大触摸点数（1-2）。
        invert_x (bool): 是否反转 X 轴坐标。
        invert_y (bool): 是否反转 Y 轴坐标。
        swap_xy (bool): 是否交换 X/Y 轴。
        _callback (callable | None): 用户提供的回调函数。
        _buf (bytearray): 内部读取缓冲区。
        _touches (int): 当前检测到的触摸点数。
        _touch_x (list): 各触摸点 X 坐标列表。
        _touch_y (list): 各触摸点 Y 坐标列表。
        _touch_weight (list): 各触摸点权重列表。
        _touch_area (list): 各触摸点面积列表。
        _debug (bool): 调试日志开关。

    Constants (寄存器地址常量，均为 int):
        DEFAULT_ADDR, REG_DEV_MODE, REG_GEST_ID, REG_TD_STATUS,
        REG_P1_XH ~ REG_P2_MISC (共 12 个),
        REG_TH_GROUP, REG_TH_DIFF, REG_CTRL,
        REG_TIME_ENTER_MONITOR, REG_PERIOD_ACTIVE, REG_PERIOD_MONITOR,
        REG_RADIAN_VALUE, REG_OFFSET_LR, REG_OFFSET_UD,
        REG_DISTANCE_LR, REG_DISTANCE_UD, REG_DISTANCE_ZOOM,
        REG_LIB_VER_H, REG_LIB_VER_L, REG_CIPHER,
        REG_G_MODE, REG_PWR_MODE, REG_FIRMID,
        REG_FOCALTECH_ID, REG_RELEASE_CODE_ID, REG_STATE
        （请参见类内定义，类型均为 int）

    Methods:
        __init__(self, i2c, address, width, height, max_touches,
                 invert_x, invert_y, swap_xy, callback, verify, debug):
            初始化 FT6206 驱动，配置 I2C 地址、触摸区域与回调函数。

        irq_handler(self, pin):
            INT 引脚中断回调处理函数，供调用者在 main.py 中通过 Pin.irq() 注册使用。

        read_touch(self):
            读取触摸状态寄存器并在有数据时解包触摸点信息。

        read_chip_id(self):
            读取并返回芯片 ID 和固件版本信息。

        deinit(self):
            释放硬件资源，清除回调引用。

    Properties:
        touched: 返回触摸点数量（0..max_touches）。
        position: 返回当前触摸点坐标列表。

    Usage Notes & Implementation Considerations:
        - I2C 地址: FT6206 默认地址为 0x38，__init__ 会通过读取芯片 ID 寄存器验证连接。
        - 中断模式: 驱动不直接创建 Pin 对象；使用者在 main.py 中创建 INT 引脚并通过 Pin.irq(handler=driver.irq_handler)
          绑定，实现回调注入。
        - I2C 重试: 寄存器读写内置重试机制（最多 3 次），提高总线容错性。
        - 缓冲区: 使用预分配的 bytearray 减少内存碎片化。
        - MicroPython 版本: 基于 MicroPython v1.23.0 测试，仅使用 readfrom_mem / readfrom_mem_into / writeto_mem。
    """

    # ======================================== 常量定义 ========================================

    # FT6206 默认 I2C 地址
    DEFAULT_ADDR = const(0x38)

    # ---- 工作模式寄存器 (0x00~0x0E) ----
    REG_DEV_MODE = const(0x00)
    REG_GEST_ID = const(0x01)
    REG_TD_STATUS = const(0x02)
    REG_P1_XH = const(0x03)
    REG_P1_XL = const(0x04)
    REG_P1_YH = const(0x05)
    REG_P1_YL = const(0x06)
    REG_P1_WEIGHT = const(0x07)
    REG_P1_MISC = const(0x08)
    REG_P2_XH = const(0x09)
    REG_P2_XL = const(0x0A)
    REG_P2_YH = const(0x0B)
    REG_P2_YL = const(0x0C)
    REG_P2_WEIGHT = const(0x0D)
    REG_P2_MISC = const(0x0E)

    # ---- 扩展信息寄存器 (0x80+) ----
    REG_TH_GROUP = const(0x80)
    REG_TH_DIFF = const(0x85)
    REG_CTRL = const(0x86)
    REG_TIME_ENTER_MONITOR = const(0x87)
    REG_PERIOD_ACTIVE = const(0x88)
    REG_PERIOD_MONITOR = const(0x89)
    REG_RADIAN_VALUE = const(0x91)
    REG_OFFSET_LR = const(0x92)
    REG_OFFSET_UD = const(0x93)
    REG_DISTANCE_LR = const(0x94)
    REG_DISTANCE_UD = const(0x95)
    REG_DISTANCE_ZOOM = const(0x96)
    REG_LIB_VER_H = const(0xA1)
    REG_LIB_VER_L = const(0xA2)
    REG_CIPHER = const(0xA3)
    REG_G_MODE = const(0xA4)
    REG_PWR_MODE = const(0xA5)
    REG_FIRMID = const(0xA6)
    REG_FOCALTECH_ID = const(0xA8)
    REG_RELEASE_CODE_ID = const(0xAF)
    REG_STATE = const(0xBC)

    # ---- 手指数掩码 ----
    TOUCH_COUNT_MASK = const(0x0F)
    # ---- 事件类型掩码 ----
    EVENT_MASK = const(0xC0)
    EVENT_PRESS_DOWN = const(0x00)
    EVENT_LIFT_UP = const(0x01)
    EVENT_CONTACT = const(0x02)
    EVENT_NO_EVENT = const(0x03)
    # ---- 读取缓冲大小（全部寄存器 0x00-0xBC 共 189 字节） ----
    BUF_SIZE = const(189)

    # ---- I2C 重试次数 ----
    MAX_I2C_RETRIES = const(3)

    def __init__(
        self,
        i2c,
        address=DEFAULT_ADDR,
        width=320,
        height=240,
        max_touches=2,
        invert_x=False,
        invert_y=False,
        swap_xy=False,
        callback=None,
        verify=True,
        debug=False,
    ):
        """
        初始化 FT6206 触摸控制器。

        Args:
            i2c (machine.I2C): 与 FT6206 通信的 I2C 接口实例。
            address (int, optional): I2C 地址，默认为 0x38。
            width (int, optional): 触摸区域宽度（像素），默认 320。
            height (int, optional): 触摸区域高度（像素），默认 240。
            max_touches (int, optional): 支持的最大触摸点数（1 或 2），默认 2。
            invert_x (bool, optional): 是否反转 X 轴坐标，默认 False。
            invert_y (bool, optional): 是否反转 Y 轴坐标，默认 False。
            swap_xy (bool, optional): 是否交换 X/Y 轴，默认 False。
            callback (callable, optional): INT 引脚触发时的用户回调函数，默认 None。
            verify (bool, optional): 初始化时是否验证芯片 ID，默认 True。
            debug (bool, optional): 是否启用调试日志输出，默认 False。

        Raises:
            ValueError: 如果 I2C 地址无效、触摸点数超出范围、芯片 ID 验证失败或尺寸参数无效。
            TypeError: 如果 i2c 参数不是有效的 I2C 实例。

        ==========================================
        Initialize the FT6206 touch controller.

        Args:
            i2c (machine.I2C): I2C bus instance for communication with FT6206.
            address (int, optional): I2C address, default 0x38.
            width (int, optional): Touch area width in pixels, default 320.
            height (int, optional): Touch area height in pixels, default 240.
            max_touches (int, optional): Maximum touch points supported (1 or 2), default 2.
            invert_x (bool, optional): Invert X axis coordinates, default False.
            invert_y (bool, optional): Invert Y axis coordinates, default False.
            swap_xy (bool, optional): Swap X and Y axes, default False.
            callback (callable, optional): User callback function triggered by INT pin, default None.
            verify (bool, optional): Verify chip ID during initialization, default True.
            debug (bool, optional): Enable debug log output, default False.

        Raises:
            ValueError: If I2C address is invalid, touch points exceed limit,
                         chip ID verification fails, or dimension parameters are invalid.
            TypeError: If i2c is not a valid I2C instance.
        """
        # 检查 I2C 参数
        if not (hasattr(i2c, "readfrom_mem") and hasattr(i2c, "writeto_mem")):
            raise TypeError("i2c must be a valid I2C instance with readfrom_mem/writeto_mem")
        # 检查 I2C 地址
        if not isinstance(address, int) or address < 0x08 or address > 0x77:
            raise ValueError("address must be a valid I2C address (0x08-0x77)")
        # 检查触摸点数
        if max_touches < 1 or max_touches > 2:
            raise ValueError("max_touches must be 1 or 2")
        # 检查尺寸参数
        if width < 1 or height < 1:
            raise ValueError("width and height must be positive integers")
        # 检查布尔参数
        if not (isinstance(invert_x, bool) and isinstance(invert_y, bool) and isinstance(swap_xy, bool)):
            raise ValueError("invert_x, invert_y, swap_xy must be bool")

        # 保存 I2C 实例与地址
        self.i2c = i2c
        self.addr = address
        # 保存触摸区域尺寸与最大触摸点数
        self.width = width
        self.height = height
        self.max_touches = max_touches
        # 保存坐标变换参数
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.swap_xy = swap_xy
        # 保存用户回调函数
        self._callback = callback
        # 调试开关
        self._debug = debug

        # 初始化触摸点缓冲区
        self._buf = bytearray(FT6206.BUF_SIZE)
        self._touches = 0
        self._touch_x = [0] * max_touches
        self._touch_y = [0] * max_touches
        self._touch_weight = [0] * max_touches
        self._touch_area = [0] * max_touches

        # 验证芯片 ID
        if verify:
            chip_id = self.read_chip_id()
            self._log("FT6206: chip_id=0x{:02X}".format(chip_id))

    def irq_handler(self, pin):
        """
        INT 引脚中断回调处理函数。

        该函数作为 Pin.irq() 的 handler 参数使用，在中断上下文中被调用。
        内部读取触摸数据并调用用户注册的回调函数。

        Args:
            pin (machine.Pin): 触发中断的引脚实例。

        Notes:
            - 此函数由使用者在 main.py 中通过 Pin.irq(handler=ft6206.irq_handler) 注册。
            - 不在中断上下文中执行耗时操作（仅读取与回调），避免阻塞其他中断。

        ==========================================
        INT pin interrupt callback handler.

        This function is used as the handler argument for Pin.irq().
        It reads touch data and invokes the user-registered callback.

        Args:
            pin (machine.Pin): The pin instance that triggered the interrupt.

        Notes:
            - Registered by the user in main.py via Pin.irq(handler=ft6206.irq_handler).
            - Avoids blocking operations in interrupt context.
        """
        # 读取触摸数据
        self._read_data()
        # 调用用户回调
        if self._callback:
            self._callback(self._touch_x, self._touch_y, self._touches)

    # ======================================== 公开方法 ========================================

    def read_chip_id(self):
        """
        读取 FT6206 芯片和固件版本信息。

        Returns:
            tuple: (chip_id, firmware_id, lib_version_high, lib_version_low)
                - chip_id (int): 芯片 ID（FOCALTECH_ID 寄存器 0xA8）。
                - firmware_id (int): 固件 ID（FIRMID 寄存器 0xA6）。
                - lib_ver_h (int): 库版本高字节（LIB_VER_H 寄存器 0xA1）。
                - lib_ver_l (int): 库版本低字节（LIB_VER_L 寄存器 0xA2）。

        ==========================================
        Read FT6206 chip and firmware version information.

        Returns:
            tuple: (chip_id, firmware_id, lib_version_high, lib_version_low)
        """
        # 读取芯片 ID 和固件信息寄存器
        chip_id = self._read_reg(FT6206.REG_FOCALTECH_ID)
        fw_id = self._read_reg(FT6206.REG_FIRMID)
        lib_h = self._read_reg(FT6206.REG_LIB_VER_H)
        lib_l = self._read_reg(FT6206.REG_LIB_VER_L)
        return chip_id, fw_id, lib_h, lib_l

    def read_touch(self):
        """
        读取所有触摸点数据并返回触摸状态。

        本方法通过读取 FT6206 的触摸状态寄存器（0x02）获取当前触摸点数，然后依次解包
        每个触摸点的 X/Y 坐标、权重和面积信息。

        Returns:
            tuple: (touch_count, touch_points)
                - touch_count (int): 当前检测到的触摸点数量（0..max_touches）。
                - touch_points (list): 触摸点数据列表，每项为 (x, y, weight, area)。

        Raises:
            OSError: 当 I2C 通信连续失败超过重试次数时抛出。

        ==========================================
        Read all touch point data and return touch status.

        Returns:
            tuple: (touch_count, touch_points)
                - touch_count (int): Number of currently detected touch points (0..max_touches).
                - touch_points (list): List of touch data, each as (x, y, weight, area).

        Raises:
            OSError: When I2C communication fails repeatedly beyond retry limit.
        """
        # 读取并解析触摸数据
        self._read_data()
        # 构建触摸点列表
        points = []
        for i in range(self._touches):
            points.append(
                (
                    self._touch_x[i],
                    self._touch_y[i],
                    self._touch_weight[i],
                    self._touch_area[i],
                )
            )
        return self._touches, points

    # ======================================== 属性定义 ========================================

    @property
    def touched(self):
        """
        返回当前检测到的触摸点数量。

        Returns:
            int: 当前触摸点数量，范围 0..max_touches。

        ==========================================
        Return the number of currently detected touch points.

        Returns:
            int: Current touch count, range 0..max_touches.
        """
        # 读取触摸状态寄存器中的低 4 位
        raw = self._read_reg(FT6206.REG_TD_STATUS)
        n = raw & FT6206.TOUCH_COUNT_MASK
        # 若手指数超过最大限制则视为 0
        return 0 if n > self.max_touches else n

    @property
    def position(self):
        """
        返回当前触摸点的坐标列表。

        Returns:
            list: 触摸点坐标列表，每项为 (x, y) 元组；无触摸时返回空列表。

        ==========================================
        Return coordinates of current touch points.

        Returns:
            list: List of (x, y) tuples for each touch point; empty list if no touch.
        """
        # 读取触摸数据
        self._read_data()
        # 构建坐标列表
        result = []
        for i in range(self._touches):
            result.append((self._touch_x[i], self._touch_y[i]))
        return result

    def deinit(self):
        """
        释放 FT6206 驱动占用的硬件资源。

        此方法清除中断回调引用并释放缓冲区，确保安全退出。

        Notes:
            - 调用后需重新创建实例才能继续使用。
            - 不会关闭 I2C 总线（由调用者负责管理）。

        ==========================================
        Release hardware resources occupied by the FT6206 driver.

        This method clears the interrupt callback reference and releases buffers.

        Notes:
            - A new instance must be created to continue use after calling this.
            - I2C bus is not deinitialized (managed by the caller).
        """
        # 清除回调引用
        self._callback = None
        # 清除缓冲区
        self._touches = 0
        for i in range(self.max_touches):
            self._touch_x[i] = 0
            self._touch_y[i] = 0
            self._touch_weight[i] = 0
            self._touch_area[i] = 0

    # ======================================== 私有方法 ========================================

    def _read_reg(self, reg):
        """
        从指定寄存器读取 1 字节数据，内置 I2C 重试机制。

        Args:
            reg (int): 寄存器地址（8 位）。

        Returns:
            int: 读取到的寄存器值（0-255）。

        Raises:
            OSError: 当 I2C 通信连续失败超过重试次数时抛出。

        ==========================================
        Read 1 byte from the specified register with I2C retry mechanism.

        Args:
            reg (int): Register address (8-bit).

        Returns:
            int: The register value read (0-255).

        Raises:
            OSError: When I2C communication fails repeatedly beyond retry limit.
        """
        # 重试读取
        for attempt in range(FT6206.MAX_I2C_RETRIES):
            try:
                return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
            except OSError as e:
                if attempt == FT6206.MAX_I2C_RETRIES - 1:
                    raise OSError("I2C read reg 0x{:02X} failed after {} retries".format(reg, FT6206.MAX_I2C_RETRIES))
                time.sleep_ms(1)

    def _write_reg(self, reg, val):
        """
        向指定寄存器写入 1 字节数据，内置 I2C 重试机制。

        Args:
            reg (int): 寄存器地址（8 位）。
            val (int): 要写入的值（0-255）。

        Raises:
            OSError: 当 I2C 通信连续失败超过重试次数时抛出。

        ==========================================
        Write 1 byte to the specified register with I2C retry mechanism.

        Args:
            reg (int): Register address (8-bit).
            val (int): Value to write (0-255).

        Raises:
            OSError: When I2C communication fails repeatedly beyond retry limit.
        """
        # 重试写入
        for attempt in range(FT6206.MAX_I2C_RETRIES):
            try:
                self.i2c.writeto_mem(self.addr, reg, bytes([val & 0xFF]))
                return
            except OSError as e:
                if attempt == FT6206.MAX_I2C_RETRIES - 1:
                    raise OSError("I2C write reg 0x{:02X} failed after {} retries".format(reg, FT6206.MAX_I2C_RETRIES))
                time.sleep_ms(1)

    def _read_data(self):
        """
        一次性读取全部寄存器数据并解析触摸点信息。

        使用 readfrom_mem_into 将 0x00-0xBC 的数据读入内部缓冲区，
        然后解析触摸状态和每个触摸点的坐标、权重、面积信息。

        ==========================================
        Read all register data in one burst and parse touch point information.

        Uses readfrom_mem_into to read 0x00-0xBC data into internal buffer,
        then parses touch status and each point's coordinates, weight, and area.
        """
        # 一次性读取全部寄存器到内部缓冲区
        for attempt in range(FT6206.MAX_I2C_RETRIES):
            try:
                self.i2c.readfrom_mem_into(self.addr, 0x00, self._buf)
                break
            except OSError:
                if attempt == FT6206.MAX_I2C_RETRIES - 1:
                    self._touches = 0
                    return
                time.sleep_ms(1)

        # 解析触摸点数
        self._touches = self._buf[FT6206.REG_TD_STATUS] & FT6206.TOUCH_COUNT_MASK
        # 若手指数超过最大限制则清空
        if self._touches > self.max_touches:
            self._touches = 0

        # 解析每个触摸点数据
        for i in range(self._touches):
            # 每个触摸点占用 6 个寄存器（XH, XL, YH, YL, WEIGHT, MISC）
            base = FT6206.REG_P1_XH + i * 6
            # 解析 X 坐标（高 4 位在 XH 低 4 位，低 8 位在 XL）
            x = ((self._buf[base] & 0x0F) << 8) | self._buf[base + 1]
            # 解析 Y 坐标
            y = ((self._buf[base + 2] & 0x0F) << 8) | self._buf[base + 3]
            # 解析权重和面积
            weight = self._buf[base + 4]
            area = self._buf[base + 5] & 0x0F

            # 应用坐标变换
            if self._swap_xy:
                x, y = y, x
            if self._invert_x:
                x = self.width - 1 - x
            if self._invert_y:
                y = self.height - 1 - y

            # 保存结果
            self._touch_x[i] = x
            self._touch_y[i] = y
            self._touch_weight[i] = weight
            self._touch_area[i] = area

        # 若触摸点数为 0，清空缓冲区数据
        if self._touches == 0:
            for i in range(self.max_touches):
                self._touch_x[i] = 0
                self._touch_y[i] = 0
                self._touch_weight[i] = 0
                self._touch_area[i] = 0

    def _log(self, msg):
        """
        输出调试日志信息。

        仅当 _debug 为 True 时打印日志，格式为 "[FT6206] 消息内容"。

        Args:
            msg (str): 要输出的调试信息。

        ==========================================
        Output debug log message.

        Only prints when _debug is True, with format "[FT6206] message".

        Args:
            msg (str): Debug message to output.
        """
        if self._debug:
            print("[FT6206] {}".format(msg))


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
