# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 15:01
# @Author  : 李清水
# @File    : onewire.py
# @Description : 单总线通信类，参考代码:https://github.com/robert-hh/Onewire_DS18X20/blob/master/onewire.py
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
import machine
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class OneWire:
    """
    单总线通信类，支持与DS18B20等单总线设备交互
    封装了单总线协议的基本操作：复位总线、发送和接收数据、设备搜索及CRC校验
    Attributes:
        pin (Pin): 用于单总线通信的GPIO引脚实例
        crctab1 (bytes): CRC校验查表法第一个字节表
        crctab2 (bytes): CRC校验查表法第二个字节表
        disable_irq (function): 禁用中断的函数
        enable_irq (function): 使能中断的函数
    Methods:
        reset(): 复位总线
        readbit(): 读取一个比特
        readbyte(): 读取一个字节
        readbytes(): 读取多个字节
        readinto(): 读取到指定缓冲区
        writebit(): 写入一个比特
        writebyte(): 写入一个字节
        write(): 写入多个字节
        select_rom(): 发送匹配ROM命令
        crc8(): 执行CRC校验
        scan(): 扫描并返回所有ROM ID
        _search_rom(): 搜索ROM设备（内部方法）
    Notes:
        - 依赖外部传入Pin实例
        - 中断保护确保时序精确
    ==========================================
    OneWire communication class for devices such as DS18B20.
    Encapsulates basic OneWire protocol operations: bus reset, data transfer, device search, and CRC check.
    Attributes:
        pin (Pin): GPIO pin instance for OneWire communication
        crctab1 (bytes): First lookup table for CRC check
        crctab2 (bytes): Second lookup table for CRC check
        disable_irq (function): Function to disable interrupts
        enable_irq (function): Function to enable interrupts
    Methods:
        reset(): Reset bus
        readbit(): Read one bit
        readbyte(): Read one byte
        readbytes(): Read multiple bytes
        readinto(): Read into buffer
        writebit(): Write one bit
        writebyte(): Write one byte
        write(): Write multiple bytes
        select_rom(): Send ROM match command
        crc8(): Perform CRC check
        scan(): Scan and return all ROM IDs
        _search_rom(): Search ROM devices (internal)
    Notes:
        - Requires externally provided Pin instance
        - Interrupt protection ensures precise timing
    """

    # 搜索ROM命令
    CMD_SEARCHROM = const(0xF0)
    # 读取ROM ID命令
    CMD_READROM = const(0x33)
    # 匹配ROM ID命令
    CMD_MATCHROM = const(0x55)
    # 同时寻址所有器件命令
    CMD_SKIPROM = const(0xCC)
    # 高电平值
    PULLUP_ON = 1

    def __init__(self, pin: machine.Pin) -> None:
        """
        初始化单总线通信类
        Args:
            pin (machine.Pin): 用于通信的数据引脚对象
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：将引脚初始化为上拉开漏模式，初始化CRC查表
        ==========================================
        Initialize OneWire class.
        Args:
            pin (machine.Pin): Pin object used for communication
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Initializes pin as open-drain pull-up, initializes CRC lookup tables
        """
        self.pin = pin
        # 初始化引脚为上拉、开漏模式
        self.pin.init(pin.OPEN_DRAIN, pin.PULL_UP)
        # 定义失能中断和使能中断方法
        self.disable_irq = machine.disable_irq
        self.enable_irq = machine.enable_irq
        # CRC校验查表法需要的两个bytes表
        self.crctab1 = b"\x00\x5E\xBC\xE2\x61\x3F\xDD\x83" b"\xC2\x9C\x7E\x20\xA3\xFD\x1F\x41"
        self.crctab2 = b"\x00\x9D\x23\xBE\x46\xDB\x65\xF8" b"\x8C\x11\xAF\x32\xCA\x57\xE9\x74"

    def reset(self, required: bool = False) -> bool:
        """
        重置单总线
        Args:
            required (bool): 是否强制断言未响应情况，默认False
        Returns:
            bool: 有设备响应复位脉冲返回True，否则返回False
        Raises:
            AssertionError: required=True且设备未响应时抛出
        Notes:
            - ISR-safe: 否（内部使用disable_irq/enable_irq）
        ==========================================
        Reset the OneWire bus.
        Args:
            required (bool): Whether to assert on missing response, default False
        Returns:
            bool: True if device responded to reset pulse, False otherwise
        Raises:
            AssertionError: Raised if required=True and no response received
        Notes:
            - ISR-safe: No (uses disable_irq/enable_irq internally)
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
        status = not pin()
        self.enable_irq(i)
        # 空闲状态时上拉电阻拉高总线，主机接收响应脉冲至少480us（480-60=420us）
        sleep_us(420)
        # status为True表示有设备响应复位脉冲
        assert status is True or required is False, "Onewire device response"
        return status

    def readbit(self) -> int:
        """
        读取单总线上的一个数据位
        Args:
            无
        Returns:
            int: 读取的数据位（0或1）
        Notes:
            - ISR-safe: 否（内部使用disable_irq/enable_irq）
        ==========================================
        Read one bit from the OneWire bus.
        Args:
            None
        Returns:
            int: The read bit (0 or 1)
        Notes:
            - ISR-safe: No (uses disable_irq/enable_irq internally)
        """
        sleep_us = time.sleep_us
        pin = self.pin

        # 读取前先拉高总线，以匹配CRC校验
        pin(1)
        # 禁用中断
        i = self.disable_irq()
        # 主机拉低总线产生读信号（至少1us后释放）
        pin(0)
        # 跳过sleep_us(1)以兼容时序要求不严格的设备
        pin(1)
        # 在15us内完成采样
        sleep_us(5)
        value = pin()
        # 使能中断
        self.enable_irq(i)
        # 主机拉高总线40us，表示数据位读取完成
        sleep_us(40)
        return value

    def readbyte(self) -> int:
        """
        读取单总线上的一个字节
        Args:
            无
        Returns:
            int: 读取的字节（0~255）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read one byte from the OneWire bus.
        Args:
            None
        Returns:
            int: The read byte (0-255)
        Notes:
            - ISR-safe: No
        """
        value = 0
        for i in range(8):
            # 将readbit()返回值左移i位后与value按位或，组合为8位字节
            value |= self.readbit() << i
        return value

    def readbytes(self, count: int) -> bytearray:
        """
        读取单总线上的多个字节
        Args:
            count (int): 读取的字节数
        Returns:
            bytearray: 读取的字节数组
        Notes:
            - ISR-safe: 否
        ==========================================
        Read multiple bytes from the OneWire bus.
        Args:
            count (int): Number of bytes to read
        Returns:
            bytearray: Read bytes as a bytearray
        Notes:
            - ISR-safe: No
        """
        buf = bytearray(count)
        for i in range(count):
            buf[i] = self.readbyte()
        return buf

    def readinto(self, buf: bytearray) -> None:
        """
        读取多个字节并写入缓冲区
        Args:
            buf (bytearray): 用于存放读取数据的缓冲区
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Read multiple bytes into a buffer.
        Args:
            buf (bytearray): Buffer to store the read data
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        for i in range(len(buf)):
            buf[i] = self.readbyte()

    def writebit(self, value: int, powerpin: machine.Pin = None) -> None:
        """
        向单总线写入一个数据位
        Args:
            value (int): 要写入的数据位，0或1
            powerpin (machine.Pin): 寄生供电模式下的供电引脚，默认None
        Returns:
            None
        Notes:
            - ISR-safe: 否（内部使用disable_irq/enable_irq）
            - 副作用：若传入powerpin，写完后拉高供电引脚
        ==========================================
        Write one bit to the OneWire bus.
        Args:
            value (int): Bit value to write (0 or 1)
            powerpin (machine.Pin): Power pin for parasitic power mode, default None
        Returns:
            None
        Notes:
            - ISR-safe: No (uses disable_irq/enable_irq internally)
            - Side effects: If powerpin provided, pulls it high after write
        """
        sleep_us = time.sleep_us
        pin = self.pin

        # 禁用中断
        i = self.disable_irq()
        # 拉低总线（MicroPython执行速度慢，pin(0)和pin(value)之间已有约1us延时）
        pin(0)
        # 发送0时拉低，发送1时拉高
        pin(value)
        # 写信号至少60us，从机在主机拉低15us后开始采样
        sleep_us(60)

        # 寄生供电模式下，通过供电引脚为从机充电
        if powerpin:
            pin(1)
            powerpin(self.PULLUP_ON)
        else:
            pin(1)

        # 使能中断
        self.enable_irq(i)

    def writebyte(self, value: int, powerpin: machine.Pin = None) -> None:
        """
        向单总线写入一个字节
        Args:
            value (int): 要写入的字节值（0~255）
            powerpin (machine.Pin): 寄生供电模式下的供电引脚，默认None
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Write one byte to the OneWire bus.
        Args:
            value (int): Byte value to write (0-255)
            powerpin (machine.Pin): Power pin for parasitic power mode, default None
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        for i in range(7):
            self.writebit(value & 1)
            value >>= 1
        self.writebit(value & 1, powerpin)

    def write(self, buf: bytearray) -> None:
        """
        向单总线写入多个字节
        Args:
            buf (bytearray): 需要写入的数据数组
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Write multiple bytes to the OneWire bus.
        Args:
            buf (bytearray): Data buffer to write
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        for b in buf:
            self.writebyte(b)

    def select_rom(self, rom: bytearray) -> None:
        """
        发送匹配ROM命令，选择指定设备
        Args:
            rom (bytearray): 目标设备的ROM ID（8字节）
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：重置总线并发送MATCHROM命令及ROM ID
        ==========================================
        Send ROM match command to select target device.
        Args:
            rom (bytearray): ROM ID of target device (8 bytes)
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Resets bus and sends MATCHROM command with ROM ID
        """
        # 初始化总线
        self.reset()
        # 发送匹配ROM ID命令
        self.writebyte(OneWire.CMD_MATCHROM)
        # 发送目标器件的ROM ID
        self.write(rom)

    def crc8(self, data: bytearray) -> int:
        """
        执行CRC-8校验
        Args:
            data (bytearray): 需要校验的数据
        Returns:
            int: CRC校验结果，0表示通过
        Notes:
            - ISR-safe: 是
        ==========================================
        Perform CRC-8 check.
        Args:
            data (bytearray): Data to check
        Returns:
            int: CRC result (0 means valid)
        Notes:
            - ISR-safe: Yes
        """
        crc = 0
        for i in range(len(data)):
            # 当前crc值与当前字节异或
            crc ^= data[i]
            # 低4位查crctab1，高4位查crctab2，两者异或得新crc
            crc = self.crctab1[crc & 0x0F] ^ self.crctab2[(crc >> 4) & 0x0F]
        return crc

    def scan(self) -> list:
        """
        扫描总线上所有设备
        Args:
            无
        Returns:
            list: 所有设备的ROM ID列表，每个ROM为8字节bytearray
        Notes:
            - ISR-safe: 否
        ==========================================
        Scan all devices on the bus.
        Args:
            None
        Returns:
            list: List of device ROM IDs, each 8-byte bytearray
        Notes:
            - ISR-safe: No
        """
        # 存放设备ROM ID的列表
        devices = []
        diff = 65
        rom = False

        # 从0到255搜索所有ROM ID
        for i in range(0xFF):
            rom, diff = self._search_rom(rom, diff)
            # 搜索成功则将ROM ID添加到列表
            if rom:
                devices += [rom]
            # diff为0表示已搜索完所有设备
            if diff == 0:
                break
        return devices

    def _search_rom(self, l_rom: bytearray, diff: int) -> tuple:
        """
        搜索总线上的设备ROM（内部方法）
        Args:
            l_rom (bytearray): 上一次搜索到的ROM ID
            diff (int): 上一次的差异位置
        Returns:
            tuple: (rom, next_diff)，搜索到的ROM ID和新的差异位置
        Notes:
            - ISR-safe: 否
        ==========================================
        Search device ROM on the bus (internal method).
        Args:
            l_rom (bytearray): Previously found ROM ID
            diff (int): Previous difference position
        Returns:
            tuple: (rom, next_diff), found ROM ID and updated diff value
        Notes:
            - ISR-safe: No
        """
        # 重置总线，判断是否有从机响应
        if not self.reset():
            return None, 0
        # 发送搜索ROM命令
        self.writebyte(OneWire.CMD_SEARCHROM)
        # 若没有传入ROM ID，则初始化一个空的ROM ID
        if not l_rom:
            l_rom = bytearray(8)
        # 初始化rom变量，用于存储最终搜索到的ROM地址
        rom = bytearray(8)
        # 初始化next_diff，用于记录下一个差异位置
        next_diff = 0
        i = 64

        # 从低到高遍历ROM ID的8个字节
        for byte in range(8):
            r_b = 0
            # 读取从机发送的ROM ID每个字节的8个数据位
            for bit in range(8):
                b = self.readbit()
                # 再次读取数据位（从机发送原码和反码）
                if self.readbit():
                    # 两次读取均为1表示没有读取成功
                    if b:
                        return None, 0
                else:
                    if not b:
                        # 存在冲突且当前位置小于上次差异位置，或与上次差异位置不同
                        if diff > i or ((l_rom[byte] & (1 << bit)) and diff != i):
                            b = 1
                            # 记录下一步搜索方向的差异位置
                            next_diff = i
                # 将读取的数据位写回总线，从机据此判断是否继续发送
                self.writebit(b)
                if b:
                    r_b |= 1 << bit
                i -= 1
            rom[byte] = r_b
        # 返回搜索到的ROM值和下一个差异位置
        return rom, next_diff


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
