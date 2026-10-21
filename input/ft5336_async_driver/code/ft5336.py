# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Liz Clark, Adafruit Industries, FreakStudio
# @File    : ft5336.py
# @Description : FT5336 I2C touch controller driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "Liz Clark, Adafruit Industries, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time

# 导入 micropython 常量支持
try:
    from micropython import const
except ImportError:
    # CPython 兼容性回退
    def const(value):
        return value


# ======================================== 全局变量 ============================================

# FT5336 默认 I2C 从机地址
_DEFAULT_ADDR = const(0x38)
# 厂商 ID 寄存器地址
_REG_VENDID = const(0xA3)
# 芯片 ID 寄存器地址
_REG_CHIPID = const(0xA8)
# 期望的厂商 ID 值
_VENDID = const(0x11)
# 期望的芯片 ID 值
_CHIPID = const(0x79)
# 触摸点数量寄存器地址
_REG_NUMTOUCHES = const(0x02)
# 触摸状态寄存器地址
_TD_STATUS = const(0x02)
# 触摸点 1 X 坐标高字节寄存器地址
_TOUCH1_XH = const(0x03)
# 触摸点 1 X 坐标低字节寄存器地址
_TOUCH1_XL = const(0x04)
# 触摸点 1 Y 坐标高字节寄存器地址
_TOUCH1_YH = const(0x05)
# 触摸点 1 Y 坐标低字节寄存器地址
_TOUCH1_YL = const(0x06)
# 默认屏幕宽度
_SCREEN_WIDTH = 320
# 默认屏幕高度
_SCREEN_HEIGHT = 480

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# FT5336 触摸控制器驱动类
class FT5336:
    """
    FT5336 I2C 电容触摸控制器驱动
    ==========
    FT5336 I2C capacitive touch controller driver

    通过 I2C 总线与 FT5336 电容触摸控制器通信，提供触摸点检测、坐标读取和坐标变换功能。
    基于 Adafruit CircuitPython FT5336 驱动改编，移除了 CircuitPython 专用依赖，
    仅使用 machine.I2C 原生接口（readfrom_mem / readfrom_mem_into / writeto_mem）。

    Attributes:
        i2c (machine.I2C): I2C 总线实例。
        i2c_addr (int): 设备 I2C 地址（默认 0x38）。
        max_touches (int): 最大支持触摸点数（默认 5）。
        _touches (int): 当前检测到的触摸点数量。
        _screen_width (int): 屏幕触摸区域宽度（像素）。
        _screen_height (int): 屏幕触摸区域高度（像素）。
        _invert_x (bool): 是否翻转 X 轴。
        _invert_y (bool): 是否翻转 Y 轴。
        _swap_xy (bool): 是否交换 X 轴和 Y 轴。
        _read_buffer (bytearray): 预分配的数据读取缓冲区（32 字节）。
        _touch_x (list): 各触摸点 X 坐标缓存数组。
        _touch_y (list): 各触摸点 Y 坐标缓存数组。
        _touch_id (list): 各触摸点 ID 缓存数组。
        _debug (bool): 是否启用调试日志输出。

    Methods:
        __init__(self, i2c, address, width, height, max_touches,
                 invert_x, invert_y, swap_xy, verify, debug):
            初始化 FT5336 触摸控制器。
        touches(self):
            返回所有当前检测到的触摸点坐标列表。
        point(self, point_index):
            返回指定索引的单个触摸点坐标。
        deinit(self):
            释放硬件资源。

    Notes:
        - 纯 I2C 触摸驱动，不依赖任何显示驱动或 Adafruit 兼容层。
        - 仅使用 machine.I2C.readfrom_mem / readfrom_mem_into / writeto_mem 进行 I2C 通信。
        - 寄存器地址为 8 位（addrsize=8 默认）。
        - 坐标变换（翻转/交换）在读取触摸数据时实时执行。
        - 默认调试输出关闭，可通过 debug=True 启用。
    """

    # FT5336 默认 I2C 从机地址
    # 厂商 ID 寄存器地址
    # 芯片 ID 寄存器地址
    # 期望的厂商 ID 值
    # 期望的芯片 ID 值
    # 触摸点数量寄存器地址
    # 触摸状态寄存器地址
    # 触摸点 1 X 坐标高字节寄存器地址
    # 触摸点 1 X 坐标低字节寄存器地址
    # 触摸点 1 Y 坐标高字节寄存器地址
    # 触摸点 1 Y 坐标低字节寄存器地址

    def __init__(
        self,
        i2c: object,
        address: int = _DEFAULT_ADDR,
        width: int = _SCREEN_WIDTH,
        height: int = _SCREEN_HEIGHT,
        max_touches: int = 5,
        invert_x: bool = False,
        invert_y: bool = False,
        swap_xy: bool = False,
        verify: bool = True,
        debug: bool = False,
    ) -> None:
        """
        初始化 FT5336 触摸控制器
        ==========
        Initialize FT5336 touch controller over I2C

        配置 I2C 总线、屏幕尺寸、坐标变换选项和最大触摸点数，
        并可选校验芯片 ID 和厂商 ID。

        Args:
            i2c (machine.I2C): I2C 总线实例（须已由调用者初始化）。
            address (int, optional): I2C 从机地址，默认 0x38。
            width (int, optional): 触摸屏幕宽度（像素），默认 320。
            height (int, optional): 触摸屏幕高度（像素），默认 480。
            max_touches (int, optional): 最大支持触摸点数，默认 5。
            invert_x (bool, optional): 是否翻转 X 轴坐标，默认 False。
            invert_y (bool, optional): 是否翻转 Y 轴坐标，默认 False。
            swap_xy (bool, optional): 是否交换 X 轴和 Y 轴，默认 False。
            verify (bool, optional): 是否校验芯片 ID 和厂商 ID，默认 True。
            debug (bool, optional): 是否启用调试日志输出，默认 False。

        Raises:
            TypeError: i2c 参数不是有效的 I2C 总线实例。
            ValueError: 参数值无效（如宽度非正数、地址非整数）或芯片校验失败。
            RuntimeError: I2C 通信失败。

        Notes:
            - i2c 参数需至少具备 readfrom_mem / readfrom_mem_into / writeto_mem 方法。
            - 若 verify=True，初始化时会读取厂商 ID (0xA3, 期望 0x11) 和芯片 ID (0xA8, 期望 0x79) 进行校验。
            - max_touches 的取值范围为 1 到 10。
        """
        # 校验 I2C 总线实例是否具备必要方法
        if not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "readfrom_mem_into"):
            raise TypeError("i2c must have readfrom_mem and readfrom_mem_into methods")

        # 校验地址参数类型
        if not isinstance(address, int):
            raise TypeError("address must be an integer")

        # 校验屏幕宽度
        if not isinstance(width, int) or width <= 0:
            raise ValueError("width must be a positive integer")

        # 校验屏幕高度
        if not isinstance(height, int) or height <= 0:
            raise ValueError("height must be a positive integer")

        # 校验最大触摸点数
        if not isinstance(max_touches, int) or max_touches < 1 or max_touches > 10:
            raise ValueError("max_touches must be an integer between 1 and 10")

        # 校验布尔参数类型
        if not isinstance(invert_x, bool):
            raise TypeError("invert_x must be a boolean")
        if not isinstance(invert_y, bool):
            raise TypeError("invert_y must be a boolean")
        if not isinstance(swap_xy, bool):
            raise TypeError("swap_xy must be a boolean")
        if not isinstance(verify, bool):
            raise TypeError("verify must be a boolean")
        if not isinstance(debug, bool):
            raise TypeError("debug must be a boolean")

        # 保存 I2C 总线实例和设备地址
        self.i2c = i2c
        self.i2c_addr = address

        # 调试日志开关
        self._debug = debug

        # 当前检测到的触摸点数量
        self._touches = 0

        # 最大支持触摸点数
        self.max_touches = max_touches

        # 分配读取缓冲区
        self._read_buffer = bytearray(32)

        # 分配触摸点坐标和 ID 缓存数组
        self._touch_x = [0] * self.max_touches
        self._touch_y = [0] * self.max_touches
        self._touch_id = [0] * self.max_touches

        # 保存坐标变换配置
        self._invert_x = invert_x
        self._invert_y = invert_y
        self._swap_xy = swap_xy

        # 保存屏幕尺寸
        self._screen_width = width
        self._screen_height = height

        # 若启用芯片校验，则读取并校验厂商 ID 和芯片 ID
        if verify:
            vendor = self._read_reg(_REG_VENDID)
            if vendor != _VENDID:
                raise ValueError("Incorrect vendor ID: expected 0x{:02X}, got 0x{:02X}".format(_VENDID, vendor))
            chip = self._read_reg(_REG_CHIPID)
            if chip != _CHIPID:
                raise ValueError("Incorrect chip ID: expected 0x{:02X}, got 0x{:02X}".format(_CHIPID, chip))

    # ======================== 公开方法 ========================

    def touches(self) -> list:
        """
        获取所有当前检测到的触摸点
        ==========
        Get all currently detected touch points

        返回包含所有当前触摸点坐标的列表，每项为 (x, y, z) 元组。

        Returns:
            list: 触摸点坐标列表，每项为 (x, y, z) 元组。
                  z 固定为 1（压力值不可获取）。
                  若无触摸，返回空列表。

        Notes:
            - 内部调用 points 属性获取数据。
            - 坐标已根据 invert_x / invert_y / swap_xy 配置进行变换。
            - ISR-safe: 否。
        """
        return self.points

    def point(self, point_index: int) -> tuple:
        """
        获取指定索引的单个触摸点坐标
        ==========
        Get coordinates of a specific touch point by index

        从设备读取最新触摸数据，返回指定索引触摸点的坐标。

        Args:
            point_index (int): 触摸点索引，范围为 0 到 (max_touches - 1)。

        Returns:
            tuple: (x, y, z) 坐标元组，z 固定为 1。
                  若无触摸或索引超出当前触摸点数，返回 (0, 0, 0)。

        Raises:
            TypeError: point_index 不是整数类型。
            RuntimeError: I2C 通信失败。

        Notes:
            - 每次调用都会从设备读取最新触摸数据（副作用：更新内部缓存）。
            - ISR-safe: 否。
        """
        # 校验参数类型
        if not isinstance(point_index, int):
            raise TypeError("point_index must be an integer")

        # 从设备读取最新触摸数据
        self._read_data()

        # 若无触摸或索引超出当前触摸点数，返回零值
        if self._touches == 0 or point_index >= self._touches:
            return (0, 0, 0)

        return (self._touch_x[point_index], self._touch_y[point_index], 1)

    # ======================== 属性 ========================

    @property
    def touched(self) -> int:
        """
        获取当前检测到的触摸点数量
        ==========
        Get detected touch input count

        从设备寄存器读取当前触摸点数量。

        Returns:
            int: 当前触摸点数量（0 到 max_touches）。
                 若读取值超过 max_touches，返回 0。

        Raises:
            RuntimeError: I2C 通信失败。

        Notes:
            - 每次访问都会读取 _REG_NUMTOUCHES 寄存器（副作用：I2C 通信）。
            - ISR-safe: 否。
        """
        n = self._read_reg(_REG_NUMTOUCHES)
        if n > self.max_touches:
            return 0
        return n

    @property
    def points(self) -> list:
        """
        获取所有触摸点的坐标数据
        ==========
        Get X, Y and Z values from each available touch input

        从设备读取完整的触摸数据块并解析所有触摸点的坐标。

        Returns:
            list: 触摸点坐标列表，每项为 (x, y, z) 元组，z 固定为 1。
                  若无触摸点，返回空列表。

        Raises:
            RuntimeError: I2C 通信失败。

        Notes:
            - 每次访问都会从设备读取最新触摸数据（副作用：I2C 通信 + 内部缓存更新）。
            - 坐标已根据 invert_x / invert_y / swap_xy 配置进行变换。
            - ISR-safe: 否。
        """
        # 从设备读取最新触摸数据
        self._read_data()
        points = []
        # 取实际触摸点数和最大支持点数的较小值
        n = min(self._touches, self.max_touches)
        for i in range(n):
            points.append((self._touch_x[i], self._touch_y[i], 1))
        return points

    @property
    def invert_x(self) -> bool:
        """
        获取 X 轴翻转状态
        ==========
        Get whether the X axis is inverted

        Returns:
            bool: True 表示 X 轴已翻转，False 表示未翻转。
        """
        return self._invert_x

    @invert_x.setter
    def invert_x(self, value: bool) -> None:
        """
        设置 X 轴翻转状态
        ==========
        Set whether the X axis is inverted

        Args:
            value (bool): True 表示翻转 X 轴坐标。

        Notes:
            - 设置后立即生效，下一次读取触摸数据时将应用新的变换。
            - 副作用：修改内部配置状态。
        """
        self._invert_x = value

    @property
    def invert_y(self) -> bool:
        """
        获取 Y 轴翻转状态
        ==========
        Get whether the Y axis is inverted

        Returns:
            bool: True 表示 Y 轴已翻转，False 表示未翻转。
        """
        return self._invert_y

    @invert_y.setter
    def invert_y(self, value: bool) -> None:
        """
        设置 Y 轴翻转状态
        ==========
        Set whether the Y axis is inverted

        Args:
            value (bool): True 表示翻转 Y 轴坐标。

        Notes:
            - 设置后立即生效，下一次读取触摸数据时将应用新的变换。
            - 副作用：修改内部配置状态。
        """
        self._invert_y = value

    @property
    def swap_xy(self) -> bool:
        """
        获取 X/Y 轴交换状态
        ==========
        Get whether the X and Y axes are swapped

        Returns:
            bool: True 表示 X 和 Y 轴已交换，False 表示未交换。
        """
        return self._swap_xy

    @swap_xy.setter
    def swap_xy(self, value: bool) -> None:
        """
        设置 X/Y 轴交换状态
        ==========
        Set whether the X and Y axes are swapped

        Args:
            value (bool): True 表示交换 X 轴和 Y 轴。

        Notes:
            - 设置后立即生效，下一次读取触摸数据时将应用新的变换。
            - 副作用：修改内部配置状态。
        """
        self._swap_xy = value

    # ======================== 私有方法 ========================

    def _read_reg(self, register: int) -> int:
        """
        从指定寄存器读取 1 字节数据
        ==========
        Read 1 byte from the specified register

        从 FT5336 指定寄存器地址读取 1 字节数据，内置重试机制以应对
        I2C 总线瞬态故障。

        Args:
            register (int): 8 位寄存器地址。

        Returns:
            int: 寄存器值（0 到 255）。

        Raises:
            RuntimeError: I2C 通信失败（重试耗尽后）。

        Notes:
            - 最多重试 3 次，每次重试前延时 10 ms。
            - 使用 machine.I2C.readfrom_mem() 读取数据。
            - ISR-safe: 否（包含延时和异常抛出）。
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 从指定寄存器读取 1 字节数据
                val = self.i2c.readfrom_mem(self.i2c_addr, register, 1)[0]
                return val
            except OSError as e:
                if attempt < max_retries - 1:
                    # 延时后重试
                    time.sleep_ms(10)
                    continue
                raise RuntimeError("I2C read failed at register 0x{:02X}".format(register)) from e

    def _read_data(self) -> None:
        """
        从 FT5336 读取完整触摸数据块
        ==========
        Read all touch data from FT5336

        从设备地址 0x00 开始读取 32 字节触摸数据块，解析触摸点数量、
        各触摸点的 X/Y 坐标和 ID，并根据当前配置进行坐标变换。

        Raises:
            RuntimeError: I2C 通信失败（重试耗尽后）。

        Notes:
            - 内置重试机制：最多重试 3 次，每次延时 10 ms。
            - 坐标变换（翻转/交换）在数据解析时实时执行。
            - 副作用：更新 self._touches、self._touch_x、self._touch_y、self._touch_id。
            - ISR-safe: 否（包含延时和内存访问）。
        """
        buffer = self._read_buffer
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 从地址 0x00 开始读取 32 字节数据块
                self.i2c.readfrom_mem_into(self.i2c_addr, 0x00, buffer)
                break
            except OSError as e:
                if attempt < max_retries - 1:
                    # 延时后重试
                    time.sleep_ms(10)
                    continue
                raise RuntimeError("I2C read failed when reading touch data block") from e

        # 读取当前触摸点数量
        self._touches = buffer[_TD_STATUS]

        # 若触摸点数无效或为 0，提前返回
        if self._touches > self.max_touches or self._touches == 0:
            self._touches = 0
            return

        # 解析每个触摸点的数据（每个触摸点占 6 字节）
        for i in range(self._touches):
            # X 坐标：高 4 位在 XH 寄存器低半字节，低 8 位在 XL 寄存器
            x = (buffer[_TOUCH1_XH + i * 6] & 0x0F) << 8 | buffer[_TOUCH1_XL + i * 6]
            # Y 坐标：高 4 位在 YH 寄存器低半字节，低 8 位在 YL 寄存器
            y = (buffer[_TOUCH1_YH + i * 6] & 0x0F) << 8 | buffer[_TOUCH1_YL + i * 6]

            # 若启用 X 轴翻转
            if self._invert_x:
                x = self._screen_width - 1 - x

            # 若启用 Y 轴翻转
            if self._invert_y:
                y = self._screen_height - 1 - y

            # 若启用 X/Y 轴交换
            if self._swap_xy:
                x, y = y, x

            # 保存触摸点坐标和 ID
            self._touch_x[i] = x
            self._touch_y[i] = y
            self._touch_id[i] = buffer[_TOUCH1_YH + i * 6] >> 4

    def _log(self, msg: str) -> None:
        """
        输出调试日志
        ==========
        Output debug log message

        仅在 _debug 为 True 时输出日志信息。

        Args:
            msg (str): 日志消息字符串。

        Notes:
            - 通过 print() 输出，格式为 "FT5336: <message>"。
            - 可在子类中覆盖以实现自定义日志行为。
            - ISR-safe: 否。
        """
        if self._debug:
            print("FT5336:", msg)

    # ======================== 释放资源 ========================

    def deinit(self) -> None:
        """
        释放硬件资源
        ==========
        Release hardware resources

        释放 FT5336 驱动持有的硬件资源引用和缓冲区。

        Notes:
            - I2C 总线本身不由本方法关闭，需由调用者在适当时机管理。
            - 调用此方法后，驱动实例不应再使用。
            - 副作用：清空 I2C 总线引用和读取缓冲区。
        """
        # 清空 I2C 总线引用
        self.i2c = None

        # 清空读取缓冲区
        self._read_buffer = None

        # 输出调试信息
        self._log("driver deinitialized")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
