# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/10/1 上午11:13   
# @Author  : 李清水            
# @File    : sd_block_dev.py       
# @Description : 自定义SD卡块设备类
# 参考代码：https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py#L291
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

# 导入虚拟文件块设备的抽象基类
from AbstractBlockDevInterface import AbstractBlockDev
# 导入自定义SD卡读写类中定义的一些常量
from sdcard import TOKEN_CMD25,TOKEN_STOP_TRAN,TOKEN_DATA
# 导入自定义SD卡读写类
from sdcard import SDCard

# ======================================== 全局变量 ============================================

# 定义错误码常量，符合 POSIX 标准的错误码
ENOERR = 0       # 操作成功
EPERM = 1        # 操作不允许
EIO = 5          # I/O错误
ENODEV = 19      # 无效设备/块号
EROFS = 30       # 只读文件系统
EINVAL = 22      # 无效参数
ENOSPC = 28      # 没有空间

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class SDCARDBlockDevice(AbstractBlockDev):
    """
    SDCARDBlockDevice 类，实现 SD 卡块设备的读写操作。

    该类继承自 AbstractBlockDev，封装了对 SDCard 设备的块级读写操作，
    提供标准的 readblocks、writeblocks 和 ioctl 方法，符合 MicroPython 块设备接口规范。

    Attributes:
        sdcard (SDCard): 关联的 SDCard 实例，用于执行实际的 SD 卡操作。

    Methods:
        __init__(self, sdcard: SDCard):
            初始化 SDCARDBlockDevice 实例，绑定一个 SDCard 设备。

        readblocks(self, block_num: int, buf: bytearray, offset: int = 0):
            读取 SD 卡的一个或多个块的数据到缓冲区。

        writeblocks(self, block_num: int, buf: bytearray, offset: int = 0):
            将缓冲区数据写入 SD 卡的一个或多个块。

        ioctl(self, op: int, arg: int) -> int:
            设备控制接口，用于执行初始化、同步、获取块信息等操作。
    """
    def __init__(self, sdcard: SDCard) -> None:
        """
        初始化 SDCARDBlockDevice 实例。

        Args:
            sdcard (SDCard): 传入的 SDCard 实例。

        Raises:
            ValueError: 如果传入的 sdcard 不是 SDCard 实例。
        """

        # 检查传入的SDCard实例是否有效
        if not isinstance(sdcard, SDCard):
            raise ValueError("Invalid SDCard instance")

        # 调用父类构造函数
        super().__init__()

        # 保存传入的SDCard实例
        self.sdcard = sdcard

    def readblocks(self, block_num: int, buf: bytearray, offset: int = 0) -> None:
        """
        从 SD 卡读取数据块到缓冲区。

        Args:
            block_num (int): 起始块号。
            buf (bytearray): 用于存储读取数据的缓冲区，长度必须是 512 字节的倍数。
            offset (int, optional): 数据偏移量，默认为 0。

        Raises:
            OSError: 如果缓冲区长度不是 512 的倍数，或者读取失败。
        """
        # 检查缓冲区是否有效并且是否长度为512个字节
        if not buf or len(buf) % 512 != 0:
            raise OSError(EINVAL, "Buffer length must be multiple of 512")

        # 解决共享总线问题，确保在开始事务之前MOSI为高电平
        self.sdcard.spi.write(b"\xff")

        # 计算需要读取的块数
        nblocks = len(buf) // 512
        # 确保缓冲区长度有效
        assert nblocks and not len(buf) % 512, "Buffer length is invalid"

        if nblocks == 1:
            # CMD17: 设置单个块的读取地址
            if self.sdcard.cmd(17, block_num * self.sdcard.cdv, 0, release=False) != 0:
                # 释放卡片
                self.sdcard.cs(1)
                # EIO错误
                raise OSError(EIO, "Failed to read singe block")
            # 接收数据并释放卡片
            self.sdcard.readinto(buf)
        else:
            # CMD18: 设置多个块的读取地址
            if self.sdcard.cmd(18, block_num * self.sdcard.cdv, 0, release=False) != 0:
                # 释放卡片
                self.sdcard.cs(1)
                # EIO错误
                raise OSError(EIO, "Failed to read multi blocks")
            # 数据偏移量
            offset = 0

            # 创建内存视图
            mv = memoryview(buf)
            while nblocks:
                # 接收数据并释放卡片
                self.sdcard.readinto(mv[offset : offset + 512])
                # 更新偏移量
                offset += 512
                # 减少剩余块数
                nblocks -= 1
            if self.sdcard.cmd(12, 0, 0xFF, skip1=True):
                # EIO错误
                raise OSError(EIO, "Failed to stop multi blocks")

    def writeblocks(self, block_num: int, buf: bytearray, offset: int = 0) -> None:
        """
        将数据块从缓冲区写入 SD 卡。

        Args:
            block_num (int): 起始块号。
            buf (bytearray): 要写入的数据，长度必须是 512 字节的倍数。
            offset (int, optional): 数据偏移量，默认为 0。

        Raises:
            OSError: 如果缓冲区长度不是 512 的倍数，或者写入失败。
        """
        # 检查缓冲区是否有效并且是否长度为512字节
        if not buf or len(buf) % 512 != 0:
            raise OSError(EINVAL, "Buffer length must be multiple of 512")

        # 解决共享总线问题，确保在开始事务之前MOSI为高电平
        self.sdcard.spi.write(b"\xff")

        # 计算需要写入的块数
        nblocks, err = divmod(len(buf), 512)
        # 确保缓冲区长度有效
        assert nblocks and not err, "Buffer length is invalid"
        if nblocks == 1:
            # CMD24: 设置单个块的写入地址
            if self.sdcard.cmd(24, block_num * self.sdcard.cdv, 0) != 0:
                # EIO错误
                raise OSError(EIO, "Failed to write singe block")

            # 发送数据
            self.sdcard.write(TOKEN_DATA, buf)
        else:
            # CMD25: 设置第一个块的写入地址
            if self.sdcard.cmd(25, block_num * self.sdcard.cdv, 0) != 0:
                # EIO错误
                raise OSError(EIO, "Failed to write multi blocks")

            # 发送数据
            offset = 0

            # 创建内存视图
            mv = memoryview(buf)
            while nblocks:
                # 发送每块数据
                self.sdcard.write(TOKEN_CMD25, mv[offset : offset + 512])
                # 更新偏移量
                offset += 512
                # 减少剩余块数
                nblocks -= 1
            # 发送停止传输命令
            self.sdcard.write_token(TOKEN_STOP_TRAN)

    def ioctl(self, op: int, arg: int) -> int:
        """
        控制块设备并查询其参数。

        Args:
            op (int): 操作码，参考 AbstractBlockDev 定义。
            arg (int): 附加参数。

        Returns:
            int: 操作结果，成功返回 0，或相应的块数/字节数。

        Raises:
            OSError: 如果操作码无效或者擦除块号无效。
        """
        # 初始化设备
        if op == AbstractBlockDev.IOCTL_INIT:
            # 执行初始化操作
            self.sdcard.init_card(1320000)
            # 成功返回0
            return ENOERR
        # 关闭设备
        elif op == AbstractBlockDev.IOCTL_SHUTDOWN:
            return ENOERR
        # 同步设备
        elif op == AbstractBlockDev.IOCTL_SYNC:
            return ENOERR
        # 获取块数
        elif op == AbstractBlockDev.IOCTL_BLK_COUNT:
            # 返回扇区数
            return self.sdcard.sectors
        # 获取块大小（字节）
        elif op == AbstractBlockDev.IOCTL_BLK_SIZE:
            # 返回512个字节
            return 512
        # 擦除块
        elif op == AbstractBlockDev.IOCTL_BLK_ERASE:
            # 擦除指定块
            if arg < 0 or arg >= self.sdcard.sectors:
                # 如果块号无效，抛出错误
                raise OSError(ENOSPC, "Invalid block number")
            self.sdcard.erase_block(arg)
            return ENOERR
        else:
            # 无效的操作码，抛出异常
            raise OSError(EINVAL, "Invalid ioctl operation")

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================