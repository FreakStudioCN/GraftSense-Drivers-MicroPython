# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/30 下午12:11   
# @Author  : 李清水            
# @File    : sdcard.py       
# @Description : 自定义用于SD卡读写的SDCard类
# 参考代码：https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py#L291
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

# 导入MicroPython相关模块
from micropython import const
# 导入时间相关的模块
import time
# 导入硬件相关模块
from machine import SPI, Pin

# ======================================== 全局变量 ============================================

# 定义SD卡相关常量
# 命令超时时间常量
CMD_TIMEOUT = const(100)
# R1响应状态：空闲状态
R1_IDLE_STATE = const(1 << 0)
# R1响应状态：非法命令
R1_ILLEGAL_COMMAND = const(1 << 2)
# 数据传输命令令牌
TOKEN_CMD25 = const(0xFC)
# 停止传输令牌
TOKEN_STOP_TRAN = const(0xFD)
# 数据令牌
TOKEN_DATA = const(0xFE)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义SD卡操作类
class SDCard:
    """
    SDCard类，用于通过SPI总线操作SD/MMC存储卡。
    该类封装了SD卡底层通信协议，支持标准容量卡(SDSC)和高容量卡(SDHC/SDXC)的初始化、
    数据块读写和擦除操作。实现了完整的SPI模式协议栈，包括卡识别模式和数据传输模式。

    Attributes:
        spi (SPI): SPI接口实例，用于与SD卡通信
        cs (Pin): 片选引脚实例，用于选择SD卡
        sectors (int): 卡片的总扇区数（只读）
        cdv (int): 块寻址因子（1表示块寻址，512表示字节寻址）
        cmdbuf (bytearray): 命令缓冲区（6字节）
        dummybuf (bytearray): 数据缓冲区（512字节）
        tokenbuf (bytearray): 令牌缓冲区（1字节）

    Methods:
        __init__(self, spi: machine.SPI, cs: machine.Pin, baudrate: int = 1320000) -> None:
            初始化SD卡控制器

        init_spi(self, baudrate: int) -> None:
            配置SPI接口参数

        init_card(self, baudrate: int) -> None:
            执行完整初始化流程

        cmd(self, cmd: int, arg: int, crc: int, final: int = 0, release: bool = True, skip1: bool = False) -> int:
            发送SD卡命令并获取响应

        readinto(self, buf: bytearray) -> None:
            读取数据块到缓冲区

        write(self, token: int, buf: bytearray) -> bool:
            写入数据块到卡片

        write_token(self, token: int) -> None:
            发送控制令牌

        erase_block(self, block_number: int) -> None:
            擦除指定数据块

        init_card_v1(self) -> None:
            初始化标准容量SD卡

        init_card_v2(self) -> None:
            初始化高容量SD卡

    Constants:
        CMD_TIMEOUT: 命令超时重试次数（100次）
        R1_IDLE_STATE: 卡片空闲状态标志（0x01）
        R1_ILLEGAL_COMMAND: 非法命令标志（0x04）
        TOKEN_CMD25: 多块写入开始令牌（0xFC）
        TOKEN_STOP_TRAN: 停止传输令牌（0xFD）
        TOKEN_DATA: 单块数据令牌（0xFE）
    """
    def __init__(self, spi: SPI, cs: Pin, baudrate: int = 1320000) -> None:
        """
        初始化SD卡控制器。

        Args:
            spi (machine.SPI): 配置好的SPI接口对象
            cs (machine.Pin): 片选引脚对象
            baudrate (int, optional): SPI波特率，默认为1320000

        Returns:
            None

        Raises:
            OSError: 如果初始化过程中出现硬件错误
            ValueError: 如果波特率超出有效范围
        """
        # 存储SPI接口
        self.spi = spi
        # 存储CS引脚
        self.cs = cs

        # 创建命令缓冲区，长度为6个字节
        self.cmdbuf = bytearray(6)
        # 创建虚拟数据缓冲区，长度为512个字节
        self.dummybuf = bytearray(512)
        # 创建令牌缓冲区，长度为1个字节
        self.tokenbuf = bytearray(1)

        # 初始化虚拟数据缓冲区为全FF
        for i in range(512):
            self.dummybuf[i] = 0xFF

        # 创建虚拟数据缓冲区的内存视图
        self.dummybuf_memoryview = memoryview(self.dummybuf)

        # 初始化SD卡
        self.init_card(baudrate)

    def init_spi(self, baudrate: int) -> None:
        """
        配置SPI接口参数。

        Args:
            baudrate (int): 目标通信速率（Hz）

        Returns:
            None

        Raises:
            ValueError: 如果波特率超出硬件支持范围
        """
        # 初始化SPI
        self.spi.init(baudrate=baudrate, phase=0, polarity=0)

    def init_card(self, baudrate: int) -> None:
        """
        执行完整的SD卡初始化流程。

        Args:
            baudrate (int): 目标数据传输波特率

        Returns:
            None

        Raises:
            OSError: 如果出现以下情况：
                - 卡片无响应
                - 版本识别失败
                - CSD格式不支持
                - 块大小设置失败
        """
        # 初始化CS引脚,设置CS引脚为输出高电平
        self.cs.init(self.cs.OUT, value=1)

        # 初始化SPI总线；使用低数据速率进行初始化
        self.init_spi(100000)

        # 发送命令前的空闲周期，保持CS高
        for i in range(16):
            # 发送16个空字节
            self.spi.write(b"\xff")

        # CMD0: 初始化卡片；应返回_IDLE_STATE（允许5次尝试）
        for _ in range(5):
            if self.cmd(0, 0, 0x95) == R1_IDLE_STATE:
                break
        else:
            # 如果未找到SD卡，则引发异常
            raise OSError("no SD card")

        # CMD8: 确定卡片版本
        r = self.cmd(8, 0x01AA, 0x87, 4)
        if r == R1_IDLE_STATE:
            # 初始化v2版本的卡片
            self.init_card_v2()
        elif r == (R1_IDLE_STATE | R1_ILLEGAL_COMMAND):
            # 初始化v1版本的卡片
            self.init_card_v1()
        else:
            # 无法确定SD卡版本
            raise OSError("couldn't determine SD card version")

        # 获取扇区数量
        # CMD9: 响应R2（R1字节 + 16字节块读取）
        if self.cmd(9, 0, 0, 0, False) != 0:
            # 如果没有响应，则引发异常
            raise OSError("no response from SD card")

        # 创建CSD缓冲区
        csd = bytearray(16)
        # 读取CSD数据
        self.readinto(csd)

        # CSD版本2.0
        if csd[0] & 0xC0 == 0x40:
            # 计算扇区数量
            self.sectors = ((csd[8] << 8 | csd[9]) + 1) * 1024
            # CSD版本1.0（旧，<=2GB）
        elif csd[0] & 0xC0 == 0x00:
            # 获取C_SIZE
            c_size = (csd[6] & 0b11) << 10 | csd[7] << 2 | csd[8] >> 6
            # 获取C_SIZE_MULT
            c_size_mult = (csd[9] & 0b11) << 1 | csd[10] >> 7
            # 获取读取块长度
            read_bl_len = csd[5] & 0b1111
            # 计算容量
            capacity = (c_size + 1) * (2 ** (c_size_mult + 2)) * (2**read_bl_len)
            # 计算扇区数量
            self.sectors = capacity // 512
        else:
            # 不支持的CSD格式
            raise OSError("SD card CSD format not supported")

        # CMD16: 设置块长度为512个字节
        if self.cmd(16, 512, 0) != 0:
            # 无法设置块大小
            raise OSError("can't set 512 block size")

        # 现在设置为高数据速率
        self.init_spi(baudrate)

    def init_card_v1(self) -> None:
        """
        初始化标准容量SD卡（SDSC）。

        Args:
            None

        Returns:
            None

        Raises:
            OSError: 如果初始化超时（100次尝试）
        """
        for i in range(CMD_TIMEOUT):
            time.sleep_ms(50)
            # 发送命令55
            self.cmd(55, 0, 0)

            # 尝试初始化卡片
            # SDSC卡，使用字节寻址方式进行读/写/擦除命令
            if self.cmd(41, 0, 0) == 0:
                # 设置块大小为512个字节
                self.cdv = 512
                # 成功返回
                return
        # 超时引发异常
        raise OSError("timeout waiting for v1 card")

    def init_card_v2(self) -> None:
        """
        初始化高容量SD卡（SDHC/SDXC）。

        Args:
            None

        Returns:
            None

        Raises:
            OSError: 如果初始化超时（100次尝试）
        """
        for i in range(CMD_TIMEOUT):
            # 等待50毫秒
            time.sleep_ms(50)
            # 发送命令58以获取OCR
            self.cmd(58, 0, 0, 4)
            # 发送命令55以准备初始化
            self.cmd(55, 0, 0)

            # 尝试初始化SDHC/SDXC卡
            if self.cmd(41, 0x40000000, 0) == 0:
                # 4个字节响应，负值表示保留首字节
                self.cmd(58, 0, 0, -4)
                # 获取OCR的首字节
                ocr = self.tokenbuf[0]
                # SDSC卡，使用字节寻址方式
                if not ocr & 0x40:
                    # 设置块大小为512个字节
                    self.cdv = 512
                else:
                    # SDHC/SDXC卡，使用块寻址方式
                    # 设置块大小为1个字节
                    self.cdv = 1
                # 成功返回
                return

        # 超时引发异常
        raise OSError("timeout waiting for v2 card")

    def cmd(self, cmd: int, arg: int, crc: int, final: int = 0, release: bool = True, skip1: bool = False) -> int:
        """
        发送SD卡命令并获取响应。

        Args:
            cmd (int): 命令编号（0-63）
            arg (int): 32位命令参数
            crc (int): CRC校验值
            final (int, optional): 额外读取字节数，默认为0
            release (bool, optional): 是否释放CS，默认为True
            skip1 (bool, optional): 是否跳过首字节，默认为False

        Returns:
            int: 响应状态：
                - 0x00: 正常
                - 0x01: 空闲状态
                - -1: 超时

        Raises:
            OSError: 如果SPI通信失败
        """
        # 拉低CS引脚，开始通信
        self.cs(0)

        # 创建并发送命令
        buf = self.cmdbuf

        # 设置命令头
        buf[0] = 0x40 | cmd
        # 设置命令参数（高字节）
        buf[1] = arg >> 24
        # 设置命令参数（次高字节）
        buf[2] = arg >> 16
        # 设置命令参数（次低字节）
        buf[3] = arg >> 8
        # 设置命令参数（低字节）
        buf[4] = arg
        # 设置CRC校验
        buf[5] = crc

        # 通过SPI发送命令
        self.spi.write(buf)

        # 如果需要跳过第一次响应
        if skip1:
            # 读取一个字节，丢弃
            self.spi.readinto(self.tokenbuf, 0xFF)

        # 等待响应 (response[7] == 0)
        for i in range(CMD_TIMEOUT):
            # 读取响应字节
            self.spi.readinto(self.tokenbuf, 0xFF)
            # 获取响应
            response = self.tokenbuf[0]

            # 检查响应是否有效
            if not (response & 0x80):
                # 处理大端整数的情况
                # 如果final为负
                if final < 0:
                    # 读取并丢弃一个字节
                    self.spi.readinto(self.tokenbuf, 0xFF)
                    # 更新final值
                    final = -1 - final

                # 读取额外的字节
                for j in range(final):
                    # 发送空字节以保持时序
                    self.spi.write(b"\xff")

                # 如果需要释放CS信号
                if release:
                    # 拉高CS引脚
                    self.cs(1)
                    # 发送空字节
                    self.spi.write(b"\xff")
                # 返回有效响应
                return response

        # 超时处理
        # 拉高CS引脚
        self.cs(1)
        # 发送空字节
        self.spi.write(b"\xff")
        # 返回-1表示超时
        return -1

    def readinto(self, buf: bytearray) -> None:
        """
        读取数据块到缓冲区。

        Args:
            buf (bytearray): 目标缓冲区（必须512字节）

        Returns:
            None

        Raises:
            ValueError: 如果缓冲区长度错误
            OSError: 如果读取超时或校验失败
        """
        # 拉低CS引脚，开始通信
        self.cs(0)

        # 读取直到开始字节 (0xff)
        for i in range(CMD_TIMEOUT):
            # 读取一个字节
            self.spi.readinto(self.tokenbuf, 0xFF)
            # 检查是否为数据开始标志
            if self.tokenbuf[0] == TOKEN_DATA:
                # 找到开始字节，退出循环
                break
            # 等待1毫秒
            time.sleep_ms(1)
        else:
            # 拉高CS引脚
            self.cs(1)
            # 抛出超时错误
            raise OSError("timeout waiting for response")

        # 读取数据，创建内存视图
        mv = self.dummybuf_memoryview
        # 如果缓冲区长度不匹配
        if len(buf) != len(mv):
            # 切片到缓冲区长度
            mv = mv[: len(buf)]
        # 读取数据到buf
        self.spi.write_readinto(mv, buf)

        # 发送空字节
        self.spi.write(b"\xff")
        self.spi.write(b"\xff")

        # 拉高CS引脚
        self.cs(1)
        # 发送空字节
        self.spi.write(b"\xff")

    def write(self, token: int, buf: bytearray) -> bool:
        """
        写入数据块到卡片。

        Args:
            token (int): 写入令牌（0xFC/0xFD/0xFE）
            buf (bytearray): 源数据（必须512字节）

        Returns:
            bool: 写入结果：
                - True: 成功
                - False: 失败

        Raises:
            ValueError: 如果数据长度错误
            OSError: 如果卡片响应异常
        """
        # 拉低CS引脚，开始通信
        self.cs(0)

        # 发送: 块开始标记，数据，校验和
        self.spi.read(1, token)
        self.spi.write(buf)
        self.spi.write(b"\xff")
        self.spi.write(b"\xff")

        # 检查响应是否为成功标志
        if (self.spi.read(1, 0xFF)[0] & 0x1F) != 0x05:
            # 拉高CS引脚
            self.cs(1)
            # 发送空字节
            self.spi.write(b"\xff")
            # 返回，写入失败
            return

        # 等待写入完成
        while self.spi.read(1, 0xFF)[0] == 0:
            # 等待直到写入完成
            pass

        # 拉高CS引脚
        self.cs(1)
        # 发送空字节
        self.spi.write(b"\xff")

    def write_token(self, token: int) -> None:
        """
        发送控制令牌。

        Args:
            token (int): 控制令牌（0xFC/0xFD/0xFE）

        Returns:
            None

        Raises:
            OSError: 如果卡片未响应
        """
        # 拉低CS引脚，开始通信
        self.cs(0)
        # 发送标记
        self.spi.read(1, token)
        # 发送空字节
        self.spi.write(b"\xff")

        # 等待写入完成
        while self.spi.read(1, 0xFF)[0] == 0x00:
            # 等待直到写入完成
            pass

        # 拉高CS引脚
        self.cs(1)
        # 发送空字节
        self.spi.write(b"\xff")

    def erase_block(self, block_number: int) -> None:
        """
        擦除指定数据块。

        Args:
            block_number (int): 块编号（LBA格式）

        Returns:
            None

        Raises:
            ValueError: 如果块号超出范围
            OSError: 如果擦除命令失败
        """
        # 拉低CS引脚，开始通信
        self.cs(0)

        # 发送擦除命令 CMD32 (erase start) 和 CMD33 (erase end)
        # 开始擦除
        self.cmd(32, block_number * 512, 0)
        # 结束擦除
        self.cmd(33, block_number * 512, 0)

        # 发送擦除命令 CMD38 (erase)
        self.cmd(38, 0, 0)

        # 等待擦除完成
        while True:
            # 查询状态
            response = self.cmd(13, 0, 0)
            # 擦除完成
            if response == 0:
                break

        # 拉高CS引脚
        self.cs(1)
        # 发送空字节
        self.spi.write(b"\xff")

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================