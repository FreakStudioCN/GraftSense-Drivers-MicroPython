# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/1 下午2:10   
# @Author  : 李清水            
# @File    : mcp4725.py       
# @Description : 12位DAC芯片mcp4725驱动模块，参考代码：https://github.com/wayoda/micropython-mcp4725/blob/master/mcp4725.py
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import I2C

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# DAC芯片MCP4725自定义类
class MCP4725:
    """
    MCP4725类用于控制MCP4725数字模拟转换器(DAC)芯片，通过I2C接口与主控芯片进行通信，输出模拟电压值。

    Attributes:
        i2c (machine.I2C): 用于与MCP4725通信的I2C接口对象。
        address (int): MCP4725的I2C地址，默认为0x60。
        _writeBuffer (bytearray): 存储要写入DAC的数据缓冲区。

    Class Variables:
        BUS_ADDRESS (list): MCP4725可能的I2C地址，默认为[0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67]。
        POWER_DOWN_MODE (dict): 电源关断模式映射字典，包含'Off', '1k', '100k', '500k'四种模式。

    Methods:
        __init__(i2c: machine.I2C, address: int = 0x60):
            初始化MCP4725实例并设置I2C通信对象和地址。

        write(value: int) -> bool:
            向MCP4725写入模拟值，模拟值范围为0至4095，并返回写入是否成功。

        read() -> tuple:
            从MCP4725读取状态信息，包括电源关断模式、DAC输出值等。

        config(power_down: str = 'Off', value: int = 0, eeprom: bool = False) -> bool:
            配置MCP4725的电源关断模式和输出值，并可选择是否写入EEPROM。

        _powerDownKey(value: int) -> str:
            将电源关断模式编码转换为模式名称，用于配置和读取操作中。
    """

    # 类变量
    # 定义MCP4725的I2C地址，一般可以选择0x60或0x61
    BUS_ADDRESS = [0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67]
    # 定义MCP4725的电源关断模式，键值为模式名称，对应的值为模式编码
    POWER_DOWN_MODE = {'Off': 0, '1k': 1, '100k': 2, '500k': 3}

    def __init__(self, i2c: I2C, address: int = 0x60) -> None:
        """
        初始化MCP4725芯片。

        该方法用于初始化MCP4725 DAC芯片的基本设置，包括I2C通信对象和I2C地址。

        Args:
            i2c (I2C): 用于与MCP4725芯片通信的I2C对象。
            address (int, optional): MCP4725的I2C地址，默认为0x62。

        Returns:
            None: 此方法没有返回值。

        Raises:
            ValueError: 如果传入的地址不在有效的I2C地址范围内，将抛出该异常。
        """

        if address not in self.BUS_ADDRESS:
            raise ValueError(f"Invalid I2C address: {hex(address)}. Valid addresses are: {self.BUS_ADDRESS}")

        # 初始化MCP4725的I2C通信和地址
        self.i2c = i2c
        self.address = address
        # 用于存储写入DAC的值的缓冲区
        self._writeBuffer = bytearray(2)

    def write(self, value: int) -> bool:
        """
        将模拟值写入MCP4725 DAC并输出。

        该方法将输入的模拟值转换为DAC能够识别的格式，并通过I2C接口写入MCP4725 DAC芯片。

        Args:
            value (int): 要输出的模拟值，范围为0到4095。

        Returns:
            bool: 如果成功写入数据并接收到2个ACK（确认响应），则返回True；否则返回False。

        Raises:
            ValueError: 如果传入的`value`不在0到4095的范围内，将抛出该异常。
        """
        if not (0 <= value <= 4095):
            raise ValueError("Value must be between 0 and 4095")

        # 将输入值限制在0到4095之间，并确保其为12位
        value = value & 0xFFF

        # 将高8位存入缓冲区的第一个字节
        self._writeBuffer[0] = (value >> 8) & 0xFF
        # 将低8位存入缓冲区的第二个字节
        self._writeBuffer[1] = value & 0xFF

        # 将缓冲区内容写入DAC，返回接收到的从机ACK数
        return self.i2c.writeto(self.address, self._writeBuffer) == 2

    def read(self) -> tuple:
        '''
        读取MCP4725芯片中电源关断数据位和DAC数据位。

        该方法从MCP4725芯片读取5个字节的数据，并解析出电源关断状态、DAC输出值和EEPROM中的数据。

        返回的数据包括：
        - EEPROM写入是否忙碌
        - 当前的电源关断模式
        - 当前的DAC输出值
        - EEPROM中的电源关断模式
        - EEPROM中的DAC输出值

        Returns:
            tuple: 如果读取成功，返回一个包含以下信息的元组：
                - eeprom_write_busy (布尔值): EEPROM写入是否忙碌，True表示未忙碌，False表示忙碌。
                - power_down (字符串): 当前电源关断模式（如“正常运行”或“关断”）。
                - value (整数): 当前DAC的输出值，范围为0到4095。
                - eeprom_power_down (字符串): EEPROM中的电源关断模式。
                - eeprom_value (整数): EEPROM中的DAC输出值，范围为0到4095。

            如果读取失败或数据长度不正确，返回None。

        Raises:
            None: 该方法不抛出异常。
        '''
        # 创建用于接收数据的缓冲区
        buf = bytearray(5)
        # 从MCP4725读取5个字节的数据并存入缓冲区
        self.i2c.readfrom_into(self.address, buf)
        # 判断缓冲区长度是否为5
        if len(buf) == 5:
            # 读取EEPROM写入忙碌状态
            eeprom_write_busy = (buf[0] & 0x80) == 0
            # 读取当前的电源关断模式
            power_down = self._powerDownKey((buf[0] >> 1) & 0x03)
            # 读取当前的输出值
            value = ((buf[1] << 8) | (buf[2])) >> 4
            # 读取EEPROM中的电源关断模式
            eeprom_power_down = self._powerDownKey((buf[3] >> 5) & 0x03)
            # 读取EEPROM中的输出值
            eeprom_value = ((buf[3] & 0x0f) << 8) | buf[4]
            # 返回包含所有读取数据的元组
            return (eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value)
        return None

    def config(self, power_down: str = 'Off', value: int = 0, eeprom: bool = False) -> bool:
        """
        配置MCP4725芯片的电源关断模式和输出值。

        该方法用于配置MCP4725芯片的电源关断模式、电压输出值以及是否将配置写入到EEPROM。

        Args:
            power_down (str, optional): 电源关断模式，默认为'Off'，可选值有'Mode1'、'Mode2'、'Mode3'等，具体取值参考MCP4725.POWER_DOWN_MODE。
            value (int, optional): 要输出的模拟值，范围为0到4095，默认为0。
            eeprom (bool, optional): 是否将配置写入到EEPROM，默认为False。

        Returns:
            bool: 如果写入成功，返回True，否则返回False。

        Raises:
            ValueError: 如果电源关断模式无效，或模拟值超出范围，或`eeprom`参数类型错误。
        """
        # 判断输入的电源关断模式是否有效
        if power_down not in MCP4725.POWER_DOWN_MODE.keys():
            raise ValueError("Invalid power down mode: {}".format(power_down))

        # 判断模拟值是否在0到4095之间
        if not (0 <= value <= 4095):
            raise ValueError("Value must be between 0 and 4095")

        # 判断eeprom是否为布尔值
        if not isinstance(eeprom, bool):
            raise ValueError("eeprom must be a boolean value")

        # 初始化用于配置的缓冲区
        buf = bytearray()
        # 设置配置字节，包含电源降模式
        conf = 0x40 | (MCP4725.POWER_DOWN_MODE[power_down] << 1)

        if eeprom:
            # 如果需要写入EEPROM，设置相应的标志位
            conf = conf | 0x60
        buf.append(conf)

        # 确保输出值在合理范围内
        value = value & 0xFFF

        # 将输出值的高8位存入缓冲区
        buf.append(value >> 4)
        # 将输出值的低4位存入缓冲区
        buf.append((value & 0x0F) << 4)

        # 将配置缓冲区写入MCP4725，返回写入成功与否
        return self.i2c.writeto(self.address, buf) == 3

    def _powerDownKey(self, value: int) -> str:
        """
        将电源关断模式编码转换为模式名称的方法。

        该方法根据给定的电源关断模式编码查找对应的模式名称。

        Args:
            value (int): 电源关断模式编码。

        Returns:
            str: 对应的电源关断模式名称。

        Raises:
            KeyError: 如果编码没有匹配的模式名称，抛出此异常。
        """
        for key, item in MCP4725.POWER_DOWN_MODE.items():
            if item == value:
                return key
        raise KeyError("No matching power down mode for value: {}".format(value))

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================