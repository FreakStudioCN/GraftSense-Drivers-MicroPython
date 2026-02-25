# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/9/29 下午2:43
# @Author  : 李清水
# @File    : gt911.py
# @Description : LCD屏幕触摸芯片GT911自定义类
# 参考代码 https://github.com/openmv/openmv/blob/master/scripts/libraries/gt911.py

# ======================================== 导入相关模块 ========================================

# 导入引脚相关模块
from machine import Pin, I2C

# 时间相关的模块
import time

# 导入micropython相关模块
import micropython
from micropython import const

# 导入数组相关模块
from array import array

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# 自定义GT911触摸芯片类
class GT911:
    """
    GT911 触摸控制器驱动类（自定义实现），通过 I2C 与 GT911 芯片通信，提供初始化、配置、触摸读取与中断回调支持。

    该类封装了 GT911 必需的寄存器访问、复位/初始化时序、配置刷新、触摸点读取与中断调度逻辑，
    适用于基于 MicroPython 的嵌入式设备（例如使用触摸屏的 ST7789 显示模块）。

    Attributes:
        i2c (machine.I2C): 与 GT911 通信的 I2C 接口实例。（MicroPython 内置类型：machine.I2C）
        addr (int): GT911 的 I2C 地址，通常为 0x5D 或 0x14。（MicroPython 内置类型：int）
        int_pin_label (int): 用于构造中断引脚的引脚编号标签/编号。（MicroPython 内置类型：int）
        rst_pin_label (int): 用于构造复位引脚的引脚编号标签/编号。（MicroPython 内置类型：int）
        rst_pin (machine.Pin): 复位引脚实例（配置为输出用于复位时序）。（MicroPython 内置类型：machine.Pin）
        int_pin (machine.Pin): 中断引脚实例（输入模式，用于检测触摸事件）。（MicroPython 内置类型：machine.Pin）
        user_callback (callable | None): 用户注册的中断回调函数，若未注册则为 None。（MicroPython 内置类型：callable/None）
        points_data (list): 长度为 5 的触摸点数据数组，每项为 array("H",[id,x,y,size]) 用于存放解包后的触摸点信息。（MicroPython 内置类型：list/array）
        width (int): 配置的触摸区域宽度（像素）。（MicroPython 内置类型：int）
        height (int): 配置的触摸区域高度（像素）。（MicroPython 内置类型：int）
        touch_points (int): 支持的最大触摸点数（1..5）。（MicroPython 内置类型：int）

    Constants (寄存器地址常量，均为 int):
        COMMAND, CONFIG_START, RESOLUTION_X, RESOLUTION_Y, TOUCH_POINTS, MODULE_SWITCH1,
        REFRESH_RATE, CONFIG_CHKSUM, CONFIG_FRESH, PRODUCT_ID, POINT_INFO, POINT_1
        （请参见类内定义，类型均为 int）

    Methods:
        __init__(self, i2c: I2C, int_pin: int, rst_pin: int, addr: int = 0x5D,
                 width: int = 240, height: int = 320, touch_points: int = 2,
                 reverse_x: bool = False, reverse_y: bool = False,
                 reverse_axis: bool = False, sito: bool = False,
                 refresh_rate: int = 240, user_callback: callable = None) -> None:
            初始化 GT911 驱动，配置 I2C 地址、复位/中断引脚、触摸区域与寄存器配置，并刷新配置到设备。
            Raises:
                ValueError: 当 addr 不在 (0x5D, 0x14) 或 touch_points > 5 时抛出。

        reset(self) -> None:
            根据 GT911 要求执行硬件复位时序：
            - 控制 RST/INT 电平以选择地址
            - 保持必要延时，然后将 INT 设为输入
            返回 None。

        _read_reg(self, reg: int, size: int = 1, buf: bytearray = None) -> bytearray | None:
            从指定寄存器读取字节数据。
            Args:
                reg (int): 16-bit 寄存器地址。
                size (int): 要读取的字节数（默认 1）。
                buf (bytearray | None): 可选预分配缓冲区，若提供则把读取数据写入该缓冲区并返回 None（直接在 buf 中填充）。
            Returns:
                bytearray | None: 若未提供 buf，则返回包含读取数据的 bytearray；若提供 buf，则直接写入 buf 并返回 None。
            Notes:
                使用 I2C readfrom_mem / readfrom_mem_into，addrsize=16。

        _write_reg(self, reg: int, val: int, size: int = 1) -> None:
            向寄存器写入整数值（按 size 大小打包为 1 或 2 字节并写入，addrsize=16）。

        reflash_config(self) -> None:
            计算配置区（CONFIG_START 起始）校验和并写入 CONFIG_CHKSUM，随后写入 CONFIG_FRESH 触发设备使用新配置。

        read_touch(self) -> tuple:
            读取触摸状态寄存器并在有数据时解包每个触摸点（最多 touch_points）。
            Returns:
                tuple: (touch_points: int, points_data: list)
                - touch_points: 当前检测到的触摸点数量（0..touch_points）
                - points_data: 存放解包后点信息的列表（每项为 array("H",[id,x,y,size])）
            Notes:
                - 本方法会在读取后清除 POINT_INFO 状态寄存器以允许下一次触摸上报。
                - 若 touch_points == 0，会把 points_data 清零以表示无触摸。

        available(self) -> bool:
            快速检查是否有新的触摸事件（通过检测 INT 引脚电平；INT 低电平表示有数据）。
            Returns:
                bool: True 表示有可读触摸事件。

        read_id(self) -> bytes:
            读取并返回 PRODUCT_ID 寄存器内容（长度 4 字节），用于确认芯片型号/版本。

        irq_callback(self, pin: Pin) -> None:
            中断服务回调（由硬件 IRQ 触发），若用户注册了 user_callback 则通过 micropython.schedule 安排其在软中断上下文执行。
            Notes:
                - 回调仅安排用户回调执行，不在 IRQ 中做耗时/阻塞操作。

    Usage Notes & Implementation Considerations:
        - I2C 地址：GT911 常见地址为 0x5D（INT 低电平）或 0x14（INT 高电平），__init__ 会依据 addr 控制启动时 INT 电平以选定地址。
        - addrsize=16：对 GT911 寄存器访问需要使用 16-bit 寄存器地址（MicroPython I2C 的 addrsize=16 参数用于此目的）。
        - 内存/缓冲：read_touch 使用预分配的 array("H") 列表以减少临时分配；若需要提高性能可复用 buf 以避免频繁分配。
        - 中断：若提供 user_callback，会在 __init__ 中为 int_pin 注册下降沿 IRQ（Pin.IRQ_FALLING）并在 irq_callback 中通过 micropython.schedule 调用用户回调。
        - 校验和：reflash_config 读取 CONFIG_START 区域（184 字节）计算补码校验和（~sum + 1）并写回 CONFIG_CHKSUM。
        - 错误处理：对 I2C/硬件可能出现的异常（总线错误、引脚配置错误等）不在内部吞掉，调用者应根据平台需要捕获并处理异常。
        - MicroPython 版本：此实现以 MicroPython v1.23.0 行为测试，某些底层 API（如 I2C readfrom_mem_into 的 addrsize 参数）在不同移植中可能存在差异，部署前请在目标板上验证。
    """

    # 寄存器和相应位段对应地址
    # 命令寄存器基地址
    COMMAND = const(0x8040)

    # 配置寄存器起始地址
    CONFIG_START = const(0x8047)
    # X 坐标输出最大值位段地址
    RESOLUTION_X = const(0x8048)
    # Y 坐标输出最大值位段地址
    RESOLUTION_Y = const(0x804A)
    # 输出触摸点数个数上限位段地址
    TOUCH_POINTS = const(0x804C)
    # 模式选择位段地址
    MODULE_SWITCH1 = const(0x804D)
    # 刷新率位段地址
    REFRESH_RATE = const(0x8056)
    # 校验和位段地址
    CONFIG_CHKSUM = const(0x80FF)
    # 配置已更新标记位段地址
    CONFIG_FRESH = const(0x8100)

    # 产品ID位段位段地址
    PRODUCT_ID = const(0x8140)
    # 状态位段地址
    POINT_INFO = const(0x814E)
    # 第一个触摸点位段地址
    POINT_1 = const(0x8150)

    def __init__(
        self,
        i2c: I2C,
        int_pin: int,
        rst_pin: int,
        addr: int = 0x5D,
        width: int = 240,
        height: int = 320,
        touch_points: int = 2,
        reverse_x: bool = False,
        reverse_y: bool = False,
        reverse_axis: bool = False,
        sito: bool = False,
        refresh_rate: int = 240,
        user_callback: callable = None,
    ) -> None:
        """
        初始化 GT911 触摸控制器。

        Args:
            i2c (machine.I2C): I2C 对象，用于与 GT911 进行通信。
            int_pin (int): 中断引脚的 GPIO 引脚编号。
            rst_pin (int): 复位引脚的 GPIO 引脚编号。
            addr (int, optional): I2C 地址，默认为 0x5D。
            width (int, optional): 屏幕触摸区域宽度，默认为 240。
            height (int, optional): 屏幕触摸区域高度，默认为 320。
            touch_points (int, optional): 支持的最大触摸点数，默认为 2。
            reverse_x (bool, optional): 是否反转 X 轴，默认为 False。
            reverse_y (bool, optional): 是否反转 Y 轴，默认为 False。
            reverse_axis (bool, optional): 是否反转坐标轴，默认为 False。
            sito (bool, optional): 是否交换 X 轴和 Y 轴，默认为 False。
            refresh_rate (int, optional): 刷新率，默认为 240Hz。
            user_callback (callable, optional): 用户提供的中断回调函数。

        Raises:
            ValueError: 如果 I2C 地址不正确或触摸点数大于 5。
        """
        # 判断输入地址是否为0x5D或0x14
        if addr not in (0x5D, 0x14):
            raise ValueError("GT911 I2C address must be 0x5D or 0x14")

        # 判断同时触摸点数是否大于5
        if touch_points > 5:
            raise ValueError("GT911 touch points must be less than 5")

        # 传入的 I2C 对象
        self.i2c = i2c
        # GT911 的 I2C 地址
        self.addr = addr
        self.int_pin_label = int_pin
        self.rst_pin_label = rst_pin
        # 复位引脚，配置为输出模式
        self.rst_pin = Pin(rst_pin, Pin.OUT, value=0)

        # 复位 GT911 芯片
        self.reset()
        # 中断引脚配置为输入状态
        self.int_pin = Pin(self.int_pin_label, Pin.IN)

        # 如果用户提供了中断回调函数
        if user_callback is not None:
            # 添加中断回调函数
            self.user_callback = user_callback
            # 设置INT引脚下降沿触发
            self.int_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.irq_callback)

        # 设置触摸屏幕范围
        self._write_reg(GT911.RESOLUTION_X, width, 2)
        self._write_reg(GT911.RESOLUTION_Y, height, 2)
        # 设置支持的最大触摸点数
        self._write_reg(GT911.TOUCH_POINTS, touch_points)
        # 设置配置寄存器中坐标轴选项: x轴和Y轴不翻转，反转坐标轴，交换X轴和Y轴，触摸时int_pin产生下降沿
        self._write_reg(GT911.MODULE_SWITCH1, (int(reverse_y) << 7) | (int(reverse_x) << 6) | (int(reverse_axis) << 3) | (int(sito) << 2) | 0x01)
        # 设置刷新率
        self._write_reg(GT911.REFRESH_RATE, (1000 * 1000) // (refresh_rate * 250))
        # 发送初始化命令
        self._write_reg(GT911.COMMAND, 0x00)
        # 更新配置
        self.reflash_config()

        # 定义记录触摸点数据的数组
        self.points_data = [array("H", [0, 0, 0, 0]) for x in range(5)]

    def reset(self) -> None:
        """
        复位 GT911 芯片并重新设置其状态。

        根据不同的 I2C 地址，控制复位引脚的状态，复位过程包括延时操作以确保 GT911 正常启动。

        Args:
            None
        Returns:
            None
        """
        # 设置复位引脚为输出并拉低
        self.rst_pin = Pin(self.rst_pin_label, Pin.OUT, value=0)
        # 设置中断引脚为输出
        int_pin = Pin(self.int_pin_label, Pin.OUT)

        if self.addr == 0x5D:
            # INT 拉低，指定地址 0x5D
            int_pin.value(0)
        elif self.addr == 0x14:
            # INT 拉高，指定地址 0x14
            int_pin.value(1)

        # 保持 RST 低电平至少 10ms
        time.sleep_ms(11)

        # 释放复位引脚（设置为高电平），芯片开始启动
        self.rst_pin.value(1)

        # 保持 INT 状态至少 50ms，确保芯片识别地址
        time.sleep_ms(55)

        # 设置 INT 引脚为输入模式（准备监听中断）
        self.int_pin = Pin(self.int_pin_label, Pin.IN)
        # 最终延时，确保启动完成
        time.sleep_ms(100)

    def _read_reg(self, reg: int, size: int = 1, buf: bytearray = None) -> bytearray:
        """
        读取寄存器数据。

        读取指定寄存器的数据并返回。

        Args:
            reg (int): 寄存器地址。
            size (int, optional): 读取的字节数，默认为 1。
            buf (bytearray, optional): 可选的缓冲区，用于存储读取的数据。

        Returns:
            bytearray: 读取的数据列表或存储在缓冲区的数据。
        """
        # 如果提供了 buffer，则读取数据到 buffer
        if buf is not None:
            self.i2c.readfrom_mem_into(self.addr, reg, buf, addrsize=16)
        else:
            # 否则，直接读取数据并返回
            return self.i2c.readfrom_mem(self.addr, reg, size, addrsize=16)

    def _write_reg(self, reg: int, val: int, size: int = 1) -> None:
        """
        向寄存器写入数据。

        向指定的寄存器地址写入数据。

        Args:
            reg (int): 寄存器地址。
            val (int): 要写入的数据。
            size (int, optional): 写入的数据长度，默认为 1 字节。

        Returns:
            None
        """
        # 根据写入字节数构建要写入的字节数组
        buf = bytes([val & 0xFF]) if size == 1 else bytes([val & 0xFF, val >> 8])
        # 使用I2C的writeto_mem方法写入数据到设备的寄存器
        self.i2c.writeto_mem(self.addr, reg, buf, addrsize=16)

    def reflash_config(self) -> None:
        """
        刷新 GT911 配置。

        计算配置数据的校验和并将其写入相应的寄存器。

        Args:
            None
        Returns:
            None
        """
        # 计算配置数据的校验和
        checksum = ~sum(self._read_reg(0x8047, 184)) + 1
        # 写入校验和到CONFIG_CHKSUM寄存器
        self._write_reg(GT911.CONFIG_CHKSUM, checksum)
        # 写入1到CONFIG_FRESH寄存器以刷新配置
        self._write_reg(GT911.CONFIG_FRESH, 0x01)

    def read_touch(self) -> tuple:
        """
        读取触摸点数据。

        从 GT911 获取触摸点信息，包括触摸点数量及其坐标。

        Args:
            None

        Returns:
            tuple: (touch_points, touches)，
                touch_points (int): 当前检测到的触摸点数量。
                touches (list): 触摸点数据列表，每个点包含 (id, x, y, size)。
        """
        # 首先读取状态寄存器
        status = self._read_reg(GT911.POINT_INFO)[0]
        # 状态寄存器的低 4 位表示触摸点数
        touch_points = status & 0x0F

        # 读取状态寄存器的 buffer status 数据位（最高位）
        ready = (status >> 7) & 1

        # 当buffer status数据位为1并且触摸点数大于0时，进行数据解包
        if ready and touch_points > 0:
            for i in range(touch_points):
                # 计算每个触摸点的数据起始地址，每个触摸点数据长度为 8 字节
                self._read_reg(GT911.POINT_1 + i * 8, buf=self.points_data[i])
                # 读取单个触摸点的数据
                self.points_data[i][-1] = self.points_data[i][-1] >> 8
        # 清除触摸状态，以便下一次触摸
        self._write_reg(GT911.POINT_INFO, 0)

        # 如果触摸点数量为0，则清空self.points_data数组
        if touch_points == 0:
            # 遍历每个触摸点的数据数组
            for point in self.points_data:
                # 将每个触摸点的数据设置为0
                for i in range(len(point)):
                    point[i] = 0

        # 返回触摸点数量和触摸点数据数组
        return touch_points, self.points_data

    def available(self) -> bool:
        """
        检查是否有新的触摸事件。

        Args:
            None

        Returns:
            bool: 如果有新的触摸事件，返回 True；否则返回 False。

        Description:
            通过检查中断引脚的电平状态来判断是否有新的触摸事件发生。
            当中断引脚为低电平时，表示有新的触摸事件。
        """
        # 当中断引脚为低电平时，表示有新数据
        return self.int_pin.value() == 0

    def read_id(self) -> bytes:
        """
        读取 GT911 的产品 ID。

        Args:
            None

        Returns:
            bytes: 返回 GT911 触摸芯片的 4 字节产品 ID。

        Description:
            通过 I2C 读取 GT911 的 ID 寄存器，获取产品 ID 信息。
        """
        # 读取ID寄存器
        id = self.i2c.readfrom_mem(self.addr, GT911.PRODUCT_ID, 4, addrsize=16)[0]
        # 返回ID
        return id

    def irq_callback(self, pin: Pin) -> None:
        """
        中断回调函数，用于处理中断事件。

        Args:
            pin (machine.Pin): 中断引脚实例。

        Returns:
            None

        Description:
            当中断引脚的状态发生变化时，调用此回调函数。
            如果用户定义了回调函数，调用 `micropython.schedule` 安排其尽快执行。
        """
        # 若用户传入了回调函数，则安排其尽快执行
        if self.user_callback is not None:
            micropython.schedule(self.user_callback, 0)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
