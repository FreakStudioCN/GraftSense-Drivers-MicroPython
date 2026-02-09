# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/12/27 上午11:09   
# @Author  : 李清水            
# @File    : mcp41010.py       
# @Description : MCP41010数字电位器芯片的驱动程序
# 这部分代码由 leeqingshui 开发，采用 MIT 协议。

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import Pin, SPI

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# MCP41010单通道数字电位器自定义类
class MCP41010:
    """
    MCP41010类用于控制MCP41010单通道数字电位器，通过SPI接口与主控芯片进行通信，调节电位器的值。

    Attributes:
        cs (Pin): 用于控制片选引脚的GPIO对象。
        spi (SPI): 用于与MCP41010通信的SPI接口对象。
        max_value (int): 电位器的最大调节值，默认值为255。

    Methods:
        __init__(clk_pin: int, cs_pin: int, mosi_pin: int, spi_id: int = 0, max_value: int = 255) -> None:
            初始化MCP41010实例，配置SPI接口及电位器最大值。

        set_value(value: int) -> None:
            设置MCP41010电位器的值，范围为0到max_value。

        set_shutdown() -> None:
            将MCP41010电位器设置为电源关断模式（Shutdown Mode），以减少功耗。

        _send_command(command_byte: int, data_byte: int) -> None:
            通过SPI发送16位数据，执行MCP41010的操作（如设置电位器值、关断模式等）。
    """

    def __init__(self, clk_pin: int, cs_pin: int, mosi_pin: int, spi_id: int = 0, max_value: int = 255) -> None:
        """
        初始化 MCP41010 实例。

        该方法用于初始化 MCP41010 数字电位器的 SPI 接口和片选引脚，并配置通信参数。

        Args:
            clk_pin (int): SCK（时钟引脚）GPIO编号，用于提供时钟信号。
            cs_pin (int): CS（片选引脚）GPIO编号，用于选择该设备进行通信。
            mosi_pin (int): MOSI（主输出从输入引脚）GPIO编号，用于传输数据。
            spi_id (int, optional): SPI 外设ID，默认为 0，表示使用第一个 SPI 外设。
            max_value (int, optional): 电位器的最大值，默认为 255，表示电位器的最大调节值。

        Returns:
            None: 此方法没有返回值。

        Raises:
            None: 该方法不抛出异常。
        """
        # 初始化CS引脚为输出模式
        self.cs = Pin(cs_pin, Pin.OUT)
        # 初始化CS为高电平
        self.cs.value(1)

        # 使用的SPI外设
        self.spi = SPI(spi_id,
                       baudrate=1000000,    # SPI时钟频率（1 MHz）
                       polarity=0,          # 时钟空闲时为低电平
                       phase=0,             # 数据在时钟上升沿采样
                       sck=Pin(clk_pin),    # 时钟SCK引脚
                       mosi=Pin(mosi_pin))  # 数据MOSI引脚
        self.max_value = max_value

    def set_value(self, value: int) -> None:
        """
        设置 MCP41010 的电位器值。

        该方法用于设置 MCP41010 数字电位器的输出值。电位器的值应在 0 到最大值之间。

        Args:
            value (int): 电位器值，范围应为 0 到 `max_value`。

        Returns:
            None: 此方法没有返回值。

        Raises:
            ValueError: 如果输入的值超出有效范围（0 到 `max_value`），将抛出该异常。
        """

        # 检查输入值是否在有效范围内
        if value < 0 or value > self.max_value:
            raise ValueError("Value must be between 0 and %d" % self.max_value)

        # 命令字节：C1=0, C0=1（写入数据），P1=0, P0=1（电位器选择）
        command_byte = 0b00010001
        data_byte = value
        self._send_command(command_byte, data_byte)

    def set_shutdown(self) -> None:
        """
        将电位器设置为电源关断模式（Shutdown Mode）。

        该方法用于将 MCP41010 数字电位器设置为关断模式，以减少功耗。

        Args:
            None

        Returns:
            None: 此方法没有返回值。
        """

        # 命令字节：C1=1, C0=0（关闭模式），P1=0, P0=1（电位器选择）
        command_byte = 0b00100001
        # 数据位为“无关位”
        data_byte = 0x00
        self._send_command(command_byte, data_byte)

    def _send_command(self, command_byte: int, data_byte: int) -> None:
        """
        通过SPI发送16位数据。

        该方法通过SPI总线发送16位命令和数据字节，以与MCP41010数字电位器进行通信。

        Args:
            command_byte (int): 前8位命令字节，用于指定操作类型（如写入数据、关闭模式等）。
            data_byte (int): 后8位数据字节，表示实际操作的数据或参数（如电位器的值）。

        Returns:
            None: 此方法没有返回值。
        """

        # CS拉低以开始通信
        self.cs.value(0)
        # 调整SPI速率
        self.spi.init(baudrate=1000000)
        # 写入16位数据
        self.spi.write(bytearray([command_byte, data_byte]))
        # CS拉高以结束通信
        self.cs.value(1)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================