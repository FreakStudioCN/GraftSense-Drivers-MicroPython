# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/18 下午12:15   
# @Author  : 李清水            
# @File    : AbstractBlockDevInterface.py.py       
# @Description : 定义了块设备的抽象基类 AbstractBlockDev
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义抽象基类 AbstractBlockDev，表示块设备的基本操作接口
class AbstractBlockDev:
    """
    AbstractBlockDev 类，定义符合 MicroPython 规范的块设备操作接口。

    该类为块设备提供抽象接口，支持简单接口（块对齐操作）和扩展接口（任意偏移操作），
    兼容 MicroPython 文件系统（如 FAT 和 littlefs）的驱动需求。实现者需至少支持
    ioctl(4) 块数量查询，若需支持 littlefs 还需实现 ioctl(6) 块擦除功能。

    Attributes:
        (由具体子类实现以下属性)
        block_size (int): 块大小（字节），通常通过 ioctl(5) 暴露
        block_count (int): 总块数，通常通过 ioctl(4) 暴露

    Methods:
        __init__():
            初始化块设备抽象基类
        readblocks(block_num, buf, offset=0):
            从设备读取数据块到缓冲区
        writeblocks(block_num, buf, offset=0):
            将数据写入设备或擦除块
        ioctl(op, arg):
            控制设备操作和查询参数

    Note:
        - 简单接口：要求缓冲区长度与块大小对齐（offset=0）
        - 扩展接口：支持任意偏移和长度（offset≠0）
        - 写入时必须遵守：
            - 简单接口需自动处理擦除
            - 扩展接口禁止隐式擦除
    """
    # 标准操作码常量（类属性）
    IOCTL_INIT = 1      # 设备初始化
    IOCTL_SHUTDOWN = 2  # 设备关闭
    IOCTL_SYNC = 3      # 数据同步
    IOCTL_BLK_COUNT = 4 # 获取块数量（必须实现）
    IOCTL_BLK_SIZE = 5  # 获取块大小（可选）
    IOCTL_BLK_ERASE = 6 # 块擦除（littlefs必需）

    def __init__(self) -> None:
        """
        初始化块设备抽象基类。

        Args:
            None

        Returns:
            None

        Note:
            - 必须至少支持 ioctl(4) 获取块数量
            - 实现 littlefs 需额外支持 ioctl(6) 块擦除
        """
        pass

    def readblocks(self, block_num: int, buf: bytearray, offset: int = 0) -> None:
        """
        从设备读取数据块到缓冲区。

        Args:
            block_num (int): 起始块号（从 0 开始）。
            buf (bytearray): 存储读取数据的缓冲区。
            offset (int, optional): 块内字节偏移量（默认 0 表示完整块读取）。

        Returns:
            None

        Raises:
            OSError: 如果 block_num 无效（ENODEV）。
            OSError: 如果读取失败（EIO）。
            NotImplementedError: 如果扩展接口未实现（当 offset≠0）。
        """
        raise NotImplementedError("sub class must implement this method")

    def writeblocks(self, block_num: int, buf: bytearray | None, offset: int = 0) -> None:
        """
        将数据写入块设备。

        Args:
            block_num (int): 目标块号（从 0 开始）
            buf (bytearray | None): 要写入的数据（None 表示擦除块）
            offset (int, optional): 块内字节偏移量（默认 0 表示完整块写入）

        Returns:
            None

        Raises:
            OSError: 如果 block_num 无效（ENODEV）
            OSError: 如果写入失败（EIO）
            OSError: 如果设备为只读（EROFS）
            NotImplementedError: 如果扩展接口未实现（当 offset≠0）
        """
        raise NotImplementedError("sub class must implement this method")

    def ioctl(self, op: int, arg: int) -> int | None:
        """
        设备控制操作。

        Args:
            op (int): 操作码（应使用类常量）：
                - `AbstractBlockDev.IOCTL_INIT` (1)       : 设备初始化
                - `AbstractBlockDev.IOCTL_SHUTDOWN` (2)   : 设备关闭
                - `AbstractBlockDev.IOCTL_SYNC` (3)       : 数据同步
                - `AbstractBlockDev.IOCTL_BLK_COUNT` (4)  : 获取设备总块数（必须实现）
                - `AbstractBlockDev.IOCTL_BLK_SIZE` (5)   : 获取块大小（可选）
                - `AbstractBlockDev.IOCTL_BLK_ERASE` (6)  : 擦除块（littlefs 需要）

            arg (int): 操作参数（依赖 op），部分操作无需参数：
                - `IOCTL_BLK_ERASE` (6) 需要传入要擦除的块号
                - 其他操作可传 `0` 或 `None`，由子类具体定义

        Returns:
            int | None:
                - `IOCTL_BLK_COUNT` (4): 返回设备的总块数（int）
                - `IOCTL_BLK_SIZE` (5) : 返回块大小（int）
                - `IOCTL_BLK_ERASE` (6): 擦除成功返回 `0`
                - 其他操作默认返回 `None`

        Raises:
            NotImplementedError: 如果子类未实现该方法
        """
        raise NotImplementedError("sub class must implement this method")

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================