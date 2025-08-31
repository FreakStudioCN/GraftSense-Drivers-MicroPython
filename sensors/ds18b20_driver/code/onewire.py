# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 下午3:01
# @Author  : 李清水
# @File    : onewire.py
# @Description : 单总线通信类
# 参考代码：https://github.com/robert-hh/Onewire_DS18X20/blob/master/onewire.py

# ======================================== 导入相关模块 ========================================

# 导入时间相关的模块
import time
# 导入硬件相关的模块
import machine
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 定义单总线通信类
class OneWire:
    """
    OneWire 类，用于通过单总线协议 (OneWire) 进行通信，支持与 OneWire 设备（如 DS18B20 温度传感器）交互。
    该类封装了 OneWire 通信的基本操作，如复位总线、发送和接收数据等，并提供了设备搜索功能。

    Attributes:
        pin (Pin): 用于 OneWire 通信的 GPIO 引脚实例。
        crctab1 (bytes): CRC校验查表法需要的第一个字节表。
        crctab2 (bytes): CRC校验查表法需要的第二个字节表。
        disable_irq (function): 禁用中断的函数。
        enable_irq (function): 使能中断的函数。

    Methods:
        reset(required: bool = False) -> bool: 重置单总线。
        readbit() -> int: 读取单总线上的一个数据位。
        readbyte() -> int: 读取单总线上的一个字节。
        readbytes(count: int) -> bytearray: 读取单总线上的多个字节。
        readinto(buf: bytearray) -> None: 读取单总线上的多个字节放到一个buf数组中。
        writebit(value: int, powerpin: machine.Pin = None) -> None: 向单总线写入一个数据位。
        writebyte(value: int, powerpin: machine.Pin = None) -> None: 向单总线写入一个字节。
        write(buf: bytearray) -> None: 将buf数组中的数据写入单总线。
        select_rom(rom: bytearray) -> None: 发送匹配ROM ID命令。
        crc8(data: bytearray) -> int: CRC校验，基于查表法实现。
        scan() -> list[bytearray]: 扫描单总线上的所有器件，返回所有匹配的ROM ID。
        _search_rom(l_rom: bytearray, diff: int) -> tuple[bytearray, int]: 搜索单总线上的对应ROM ID的器件。
    """
    # 单总线通信的ROM命令
    CMD_SEARCHROM   = const(0xf0)  # 搜索命令
    CMD_READROM     = const(0x33)  # 读取ROM ID命令
    CMD_MATCHROM    = const(0x55)  # 匹配ROM ID命令
    CMD_SKIPROM     = const(0xcc)  # 同时寻址所有器件命令
    # 高电平值
    PULLUP_ON       = 1

    def __init__(self, pin: machine.Pin) -> None:
        """
        初始化单总线类，传入使用的数据引脚对象。

        Args:
            pin (machine.Pin): 数据引脚对象。

        Returns:
            None
        """
        self.pin = pin
        # 初始化引脚为上拉、开漏模式
        self.pin.init(pin.OPEN_DRAIN, pin.PULL_UP)
        # 定义失能中断和使能中断方法
        self.disable_irq = machine.disable_irq
        self.enable_irq = machine.enable_irq
        # CRC校验查表法需要的两个bytes表
        self.crctab1 = (b"\x00\x5E\xBC\xE2\x61\x3F\xDD\x83"
                        b"\xC2\x9C\x7E\x20\xA3\xFD\x1F\x41")
        self.crctab2 = (b"\x00\x9D\x23\xBE\x46\xDB\x65\xF8"
                        b"\x8C\x11\xAF\x32\xCA\x57\xE9\x74")

    def reset(self, required: bool = False) -> bool:
        """
        重置单总线。

        Args:
            required (bool): 是否需要手动触发断言，默认为 False。

        Returns:
            bool: 如果设备发出了响应脉冲，返回 True；反之返回 False 表示失败。

        Raises:
            AssertionError: 如果 required 为 True 且设备未响应复位脉冲。
        """
        sleep_us = time.sleep_us
        pin = self.pin
        # 主机发送复位脉冲，拉低总线480us
        pin(0)
        sleep_us(480)
        # 禁用中断，避免中断服务程序打断通信执行
        i = self.disable_irq()
        # 拉高总线60us
        pin(1)
        sleep_us(60)
        # 等待从机发送响应脉冲，响应脉冲会将总线拉低60~240us
        # 读取总线状态
        status = not pin()
        self.enable_irq(i)
        # 空闲状态时，上拉电阻会拉高总线，主机接收响应脉冲至少480us
        # 480us - 60us = 420us
        sleep_us(420)
        # 若是总线上status为True，表示有设备响应复位脉冲
        # 当assert条件满足时，程序才会继续执行
        assert status is True or required is False, "Onewire device response"
        return status

    def readbit(self) -> int:
        """
        读取单总线上的一个数据位。

        Args:
            None

        Returns:
            int: 读取的数据位（0 或 1）。
        """
        sleep_us = time.sleep_us
        pin = self.pin

        # 对于某些设备，需要在读取数据前先拉高总线，以匹配CRC校验
        pin(1)
        # 禁用中断
        i = self.disable_irq()
        # 将单总线拉低，开始读取数据位
        # 主机读信号的产生是主机拉低总线至少1us然后释放总线实现的
        pin(0)
        # 跳过sleep_us(1)这一步，为了兼容一些对时序要求不严格的设备
        pin(1)
        # 在15us内，主机完成采样即可
        sleep_us(5)
        value = pin()
        # 使能中断
        self.enable_irq(i)
        # 主机拉高总线40us，表示数据位读取完成
        sleep_us(40)
        return value

    def readbyte(self) -> int:
        """
        读取单总线上的一个字节，通过调用8次readbit方法实现。

        Args:
            None

        Returns:
            int: 读取的字节（0~255）。
        """
        value = 0
        for i in range(8):
            # 将 self.readbit() 的返回值左移 i 位，并与 value 进行按位或运算
            # 得到一个由 8 个数据位组成的字节
            value |= self.readbit() << i
        return value

    def readbytes(self, count: int) -> bytearray:
        """
        读取单总线上的多个字节，通过调用多次readbyte方法实现。

        Args:
            count (int): 读取的字节数。

        Returns:
            bytearray: 读取的二进制字节数组。
        """
        buf = bytearray(count)
        for i in range(count):
            buf[i] = self.readbyte()
        return buf

    def readinto(self, buf: bytearray) -> None:
        """
        读取单总线上的多个字节放到一个buf数组中。

        Args:
            buf (bytearray): 放置需要读取数据的二进制数组。

        Returns:
            None
        """
        for i in range(len(buf)):
            buf[i] = self.readbyte()

    def writebit(self, value: int, powerpin: machine.Pin = None) -> None:
        """
        向单总线写入一个数据位。

        Args:
            value (int): 要写入的数据位，0 或 1。
            powerpin (machine.Pin): 供电引脚，采用寄生供电方式时需要传入此对象。
                                   默认采用独立供电，无需此引脚。

        Returns:
            None
        """
        sleep_us = time.sleep_us
        pin = self.pin

        # 禁用中断
        i = self.disable_irq()
        # 首先拉低总线至少1us（至多15us），这里省略即可，由于MicroPython执行速度慢
        # 实际上在pin(0)和pin(value)两条语句之间就已经有1us的延时了
        pin(0)
        # 若发送数据位为0，需要拉低总线
        # 若发送数据位为1，需要拉高总线
        pin(value)
        # 写信号时至少60us，从机在主机拉低总线15us后开始采样
        sleep_us(60)

        # 若是采用寄生供电方式并且定义了供电引脚
        if powerpin:
            # 单总线能间断的提供高电平给从机充电
            pin(1)
            powerpin(self.PULLUP_ON)
        else:
            pin(1)

        # 失能中断
        self.enable_irq(i)

    def writebyte(self, value: int, powerpin: machine.Pin = None) -> None:
        """
        向单总线写入一个字节，通过连续调用8次writebit方法实现。

        Args:
            value (int): 需要写入的值，0~255。
            powerpin (machine.Pin): 供电引脚，采用寄生供电方式时需要传入此对象。

        Returns:
            None
        """
        for i in range(7):
            self.writebit(value & 1)
            value >>= 1
        self.writebit(value & 1, powerpin)

    def write(self, buf: bytearray) -> None:
        """
        将buf数组中的数据写入单总线，通过调用多次writebyte方法实现。

        Args:
            buf (bytearray): 放置需要发送数据的二进制数组。

        Returns:
            None
        """
        for b in buf:
            self.writebyte(b)

    def select_rom(self, rom: bytearray) -> None:
        """
        发送匹配ROM ID命令。

        Args:
            rom (bytearray): ROM ID，8个字节的bytearray，8 bytes x 8 bits = 64 bits。

        Returns:
            None
        """
        # 初始化总线
        self.reset()
        # 发送匹配ROM ID命令
        self.writebyte(OneWire.CMD_MATCHROM)
        # 主机发送需要匹配器件的ROM ID来匹配器件
        self.write(rom)

    def crc8(self, data: bytearray) -> int:
        """
        CRC校验，基于查表法实现。

        Args:
            data (bytearray): 需要校验的数据。

        Returns:
            int: CRC校验值，为0则匹配成功。
        """

        # 初始化crc变量为0
        crc = 0
        # 使用for循环遍历输入数据data的每个字节
        for i in range(len(data)):
           # 将当前crc值与当前字节值进行异或运算,并将结果重新赋值给crc
           crc ^= data[i]
           # 取 crc 值的低 4 位作为索引,从 self.crctab1 表中查找对应的值
           # 取 crc 值的高 4 位作为索引,从 self.crctab2 表中查找对应的值
           # 将上述两个查找结果进行异或运算,得到新的 crc 值
           crc = (self.crctab1[crc & 0x0f] ^
                  self.crctab2[(crc >> 4) & 0x0f])
        return crc

    def scan(self) -> list[bytearray]:
        """
        扫描单总线上的所有器件，返回所有匹配的ROM ID。

        Args:
            None

        Returns:
            list[bytearray]: 返回所有连接设备的 ROM 列表。
                              每个 ROM 以 8 字节的字节对象形式返回。
        """
        # 存放设备ROM ID的列表
        devices = []
        diff = 65
        rom = False

        # 从0到255搜索所有ROM ID
        for i in range(0xff):
            rom, diff = self._search_rom(rom, diff)
            # 如果搜索成功,则将 ROM ID 添加到列表中
            if rom:
                devices += [rom]
            # 表示已经搜索完所有设备,退出循环
            if diff == 0:
                break
        return devices

    def _search_rom(self, l_rom: bytearray, diff: int) -> tuple[bytearray, int]:
        """
        搜索单总线上的对应ROM ID的器件。

        Args:
            l_rom (bytearray): 上次搜索到的 ROM ID。
            diff (int): 上次搜索的差异位置。

        Returns:
            tuple[bytearray, int]: 若是搜索成功，返回 ROM ID 和更新后的 diff 值。
        """

        # 重置总线，判断是否有从机响应
        if not self.reset():
            return None, 0
        # 发送OneWire.CMD_SEARCHROM命令
        self.writebyte(OneWire.CMD_SEARCHROM)
        # 若是没有传入ROM ID,则初始化一个空的ROM ID
        if not l_rom:
            l_rom = bytearray(8)
        # 初始化 rom 变量,用于存储最终搜索到的 ROM 地址
        rom = bytearray(8)
        # 初始化 next_diff 变量,用于记录下一个差异位置
        next_diff = 0
        i = 64

        # 从低到高遍历ROM ID，8个字节
        for byte in range(8):
            r_b = 0
            # 读取从机发送的ROM ID每个字节的8个数据位
            for bit in range(8):
                b = self.readbit()
                # 再次读取数据位
                if self.readbit():
                    # 若两次读取均为1,即都是高电平，表示没有读取成功
                    if b:
                        return None, 0
                # 若两次读取结果不同,表示读取成功
                # 从机会发送每位的原码和反码
                else:
                    if not b:
                        # 如果存在冲突且当前位置小于上次搜索的差异位置,或者当前位置与上次搜索的差异位置不同
                        if diff > i or ((l_rom[byte] & (1 << bit)) and diff != i):
                            b = 1
                            # 通过比较当前搜索位置与上次搜索位置的差异,来确定下一步的搜索方向
                            next_diff = i
                # 将 b 值写回到总线上，主机需要发送读取的ID每位数据
                # 从机会比较主机发送的主机读取的数据位和从机发送的数据位，判断二者是否匹配
                # 再来决定是否发送下一位数据
                self.writebit(b)
                if b:
                    r_b |= 1 << bit
                i -= 1
            rom[byte] = r_b
        # 返回搜索到的 rom 值和下一个差异位置 next_diff
        return rom, next_diff

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
