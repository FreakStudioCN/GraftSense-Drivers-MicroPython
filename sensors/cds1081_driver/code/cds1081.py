# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : hogeiha
# @File    : cds1081.py
# @Description : CDS1081 电容式尘雨霜传感器 Modbus RTU 驱动
# @License : MIT
__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from umodbus.serial import Serial as ModbusRTUMaster
from umodbus import functions

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

# 将无符号16位整数转换为有符号16位整数
def uint16_to_int16(raw: int) -> int:
    """
    将无符号16位整数转换为有符号16位整数
    Args:
        raw (int): 原始无符号16位整数值 (0-65535)

    Returns:
        int: 转换后的有符号16位整数值 (-32768 to 32767)

    Notes:
        当原始值大于等于32768时，减去65536得到负数表示

    ==========================================
    Convert unsigned 16-bit integer to signed 16-bit integer
    Args:
        raw (int): Raw unsigned 16-bit integer value (0-65535)

    Returns:
        int: Converted signed 16-bit integer value (-32768 to 32767)

    Notes:
        Subtract 65536 when raw value is greater than or equal to 32768 to get negative representation
    """
    return raw - 65536 if raw >= 32768 else raw


# 转换FDE温度传感器的原始数据为摄氏度值
def convert_fde_temperature(raw_data) -> float:
    """
    转换FDE温度传感器的原始数据为摄氏度值
    Args:
        raw_data: 包含两个字节的原始数据列表或元组

    Returns:
        float: 温度值，单位为摄氏度，精度为0.1度

    Notes:
        数据格式为16位有符号整数，实际温度值为原始值除以10

    ==========================================
    Convert FDE temperature sensor raw data to Celsius value
    Args:
        raw_data: Raw data list or tuple containing two bytes

    Returns:
        float: Temperature value in Celsius with 0.1 degree precision

    Notes:
        Data format is 16-bit signed integer, actual temperature is raw value divided by 10
    """
    raw = raw_data[0] * 256 + raw_data[1]
    if raw >= 32768:
        raw -= 65536
    return raw / 10


# 转换CDS1081电容传感器的原始数据为电容值
def convert_cds1081_capacitance(raw_data) -> float:
    """
    转换CDS1081电容传感器的原始数据为电容值
    Args:
        raw_data: 包含两个字节的原始数据列表或元组

    Returns:
        float: 电容值，单位为nF，精度为0.001nF

    Notes:
        原始值为16位无符号整数，实际电容值为原始值除以1000

    ==========================================
    Convert CDS1081 capacitance sensor raw data to capacitance value
    Args:
        raw_data: Raw data list or tuple containing two bytes

    Returns:
        float: Capacitance value in nF with 0.001nF precision

    Notes:
        Raw value is 16-bit unsigned integer, actual capacitance is raw value divided by 1000
    """
    raw = raw_data[0] * 256 + raw_data[1]
    return raw / 1000.0


# 转换雨量状态原始数据为整数值
def convert_rain_status(raw_data) -> str:
    """
    转换雨量状态原始数据为整数值
    Args:
        raw_data: 包含两个字节的原始数据列表或元组

    Returns:
        str: 雨量状态整数值

    Notes:
        直接返回组合后的整数值，无额外转换

    ==========================================
    Convert rain status raw data to integer value
    Args:
        raw_data: Raw data list or tuple containing two bytes

    Returns:
        str: Rain status integer value

    Notes:
        Directly return the combined integer value without additional conversion
    """
    raw = raw_data[0] * 256 + raw_data[1]
    return raw


# 将两个字节的原始数据转换为16位无符号整数
def convert_uint16(raw_data) -> int:
    """
    将两个字节的原始数据转换为16位无符号整数
    Args:
        raw_data: 包含两个字节的原始数据列表或元组

    Returns:
        int: 16位无符号整数值

    Notes:
        高字节在前，低字节在后

    ==========================================
    Convert two-byte raw data to 16-bit unsigned integer
    Args:
        raw_data: Raw data list or tuple containing two bytes

    Returns:
        int: 16-bit unsigned integer value

    Notes:
        High byte first, low byte second
    """
    return raw_data[0] * 256 + raw_data[1]


# 转换校准值原始数据为浮点数
def convert_calibration_value(raw_data) -> float:
    """
    转换校准值原始数据为浮点数
    Args:
        raw_data: 包含两个字节的原始数据列表或元组

    Returns:
        float: 校准值，精度为0.001

    Notes:
        原始值为16位无符号整数，实际校准值为原始值除以1000

    ==========================================
    Convert calibration value raw data to float
    Args:
        raw_data: Raw data list or tuple containing two bytes

    Returns:
        float: Calibration value with 0.001 precision

    Notes:
        Raw value is 16-bit unsigned integer, actual calibration value is raw value divided by 1000
    """
    raw = raw_data[0] * 256 + raw_data[1]
    return raw / 1000.0


# ======================================== 自定义类 ============================================


class CDS1081:
    """
    CDS1081土壤湿度与温度传感器Modbus RTU驱动类
    Attributes:
        slave_addr (int): Modbus从站地址
        baudrate (int): 串口通信波特率
        uart_id (int): UART接口ID编号
        tx_pin (int): 发送引脚编号
        rx_pin (int): 接收引脚编号
        host (ModbusRTUMaster): Modbus RTU主机对象

    Methods:
        read_registers(): 读取Modbus保持寄存器
        get_temperature(): 获取温度值
        get_rain_status(): 获取雨量状态
        get_capacitance(): 获取电容值（土壤湿度）
        get_count0(): 获取计数寄存器值
        get_node_address(): 获取节点地址
        get_calibration_value(): 获取校准值
        get_alarm_threshold(): 获取报警阈值
        get_clear_threshold(): 获取清除阈值
        set_calibration(): 设置校准值
        set_alarm_threshold(): 设置报警阈值
        set_clear_threshold(): 设置清除阈值

    Notes:
        传感器默认Modbus从站地址为1，波特率9600，8数据位，1停止位，无校验

    ==========================================
    CDS1081 Soil Moisture and Temperature Sensor Modbus RTU Driver Class
    Attributes:
        slave_addr (int): Modbus slave address
        baudrate (int): Serial communication baudrate
        uart_id (int): UART interface ID number
        tx_pin (int): Transmit pin number
        rx_pin (int): Receive pin number
        host (ModbusRTUMaster): Modbus RTU master object

    Methods:
        read_registers(): Read Modbus holding registers
        get_temperature(): Get temperature value
        get_rain_status(): Get rain status
        get_capacitance(): Get capacitance value (soil moisture)
        get_count0(): Get count register value
        get_node_address(): Get node address
        get_calibration_value(): Get calibration value
        get_alarm_threshold(): Get alarm threshold
        get_clear_threshold(): Get clear threshold
        set_calibration(): Set calibration value
        set_alarm_threshold(): Set alarm threshold
        set_clear_threshold(): Set clear threshold

    Notes:
        Sensor default Modbus slave address is 1, baudrate 9600, 8 data bits, 1 stop bit, no parity
    """

    def __init__(self, slave_addr: int, uart_id: int, tx_pin: int, rx_pin: int) -> None:
        """
        初始化CDS1081传感器驱动
        Args:
            slave_addr (int): Modbus从站地址
            uart_id (int): UART接口ID编号
            tx_pin (int): 发送引脚编号
            rx_pin (int): 接收引脚编号

        Raises:
            None: 无异常定义

        Notes:
            初始化时设置波特率9600，8数据位，1停止位，无校验

        ==========================================
        Initialize CDS1081 sensor driver
        Args:
            slave_addr (int): Modbus slave address
            uart_id (int): UART interface ID number
            tx_pin (int): Transmit pin number
            rx_pin (int): Receive pin number

        Raises:
            None: No exceptions defined

        Notes:
            Set baudrate 9600, 8 data bits, 1 stop bit, no parity during initialization
        """
        # 设置Modbus从站地址
        self.slave_addr = slave_addr
        # 设置串口通信波特率
        self.baudrate = 9600
        # 设置UART接口ID
        self.uart_id = uart_id
        # 设置发送引脚编号
        self.tx_pin = tx_pin
        # 设置接收引脚编号
        self.rx_pin = rx_pin

        # 创建Modbus RTU主机对象
        self.host = ModbusRTUMaster(
            pins=(self.tx_pin, self.rx_pin), baudrate=self.baudrate, data_bits=8, stop_bits=1, parity=None, uart_id=self.uart_id
        )

    def read_registers(self, slave_addr: int, starting_addr: int, register_qty: int, signed: bool = True):
        """
        读取Modbus保持寄存器
        Args:
            slave_addr (int): Modbus从站地址
            starting_addr (int): 起始寄存器地址
            register_qty (int): 要读取的寄存器数量
            signed (bool): 是否返回有符号数据（默认True）

        Returns:
            bytes: 读取到的寄存器数据

        Raises:
            TimeoutError: Modbus通信超时，未收到传感器响应

        Notes:
            超时时间设置为2000毫秒

        ==========================================
        Read Modbus holding registers
        Args:
            slave_addr (int): Modbus slave address
            starting_addr (int): Starting register address
            register_qty (int): Number of registers to read
            signed (bool): Whether to return signed data (default True)

        Returns:
            bytes: Read register data

        Raises:
            TimeoutError: Modbus communication timeout, no sensor response received

        Notes:
            Timeout is set to 2000 milliseconds
        """
        # 构建Modbus读取保持寄存器的PDU
        modbus_pdu = functions.read_holding_registers(starting_address=starting_addr, quantity=register_qty)
        # 清空UART接收缓冲区
        self.host._uart.read()
        # 发送Modbus请求到从站
        self.host._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)
        # 设置超时时间2000毫秒
        TIMEOUT_MS = 2000
        # 记录开始时间
        start_time = time.ticks_ms()
        # 初始化响应数据为空
        response = b''
        # 循环等待接收响应数据
        while len(response) == 0:
            # 读取UART接收数据
            response = self.host._uart_read()
            # 检查是否超时
            if time.ticks_diff(time.ticks_ms(), start_time) > TIMEOUT_MS:
                raise TimeoutError(f"Modbus communication timeout: no sensor response received for {TIMEOUT_MS}ms")
        # 验证并返回响应数据
        return self.host._validate_resp_hdr(response=response, slave_addr=slave_addr, function_code=modbus_pdu[0], count=True)

    def get_temperature(self) -> float:
        """
        获取温度值
        Args:
            无

        Returns:
            float: 温度值，单位为摄氏度

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x07读取温度数据

        ==========================================
        Get temperature value
        Args:
            None

        Returns:
            float: Temperature value in Celsius

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read temperature data from register address 0x07
        """
        # 从寄存器地址0x07读取1个寄存器的数据
        data = self.read_registers(1, 0x07, 1, signed=False)
        # 转换并返回温度值
        return convert_fde_temperature(data)

    def get_rain_status(self) -> str:
        """
        获取雨量状态
        Args:
            无

        Returns:
            str: 雨量状态值

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x04读取雨量状态数据

        ==========================================
        Get rain status
        Args:
            None

        Returns:
            str: Rain status value

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read rain status data from register address 0x04
        """
        # 从寄存器地址0x04读取1个寄存器的数据
        data = self.read_registers(1, 0x04, 1, signed=False)
        # 转换并返回雨量状态
        return convert_rain_status(data)

    def get_capacitance(self) -> float:
        """
        获取电容值（土壤湿度）
        Args:
            无

        Returns:
            float: 电容值，单位为nF

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x08读取电容数据

        ==========================================
        Get capacitance value (soil moisture)
        Args:
            None

        Returns:
            float: Capacitance value in nF

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read capacitance data from register address 0x08
        """
        # 从寄存器地址0x08读取1个寄存器的数据
        data = self.read_registers(1, 0x08, 1, signed=False)
        # 转换并返回电容值
        return convert_cds1081_capacitance(data)

    def get_count0(self) -> int:
        """
        获取计数寄存器值
        Args:
            无

        Returns:
            int: 计数值

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x09读取计数数据

        ==========================================
        Get count register value
        Args:
            None

        Returns:
            int: Count value

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read count data from register address 0x09
        """
        # 从寄存器地址0x09读取1个寄存器的数据
        data = self.read_registers(1, 0x09, 1, signed=False)
        # 转换并返回计数值
        return convert_uint16(data)

    def get_node_address(self) -> int:
        """
        获取节点地址
        Args:
            无

        Returns:
            int: 节点地址值

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x02读取节点地址

        ==========================================
        Get node address
        Args:
            None

        Returns:
            int: Node address value

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read node address from register address 0x02
        """
        # 从寄存器地址0x02读取1个寄存器的数据
        data = self.read_registers(1, 0x02, 1, signed=False)
        # 转换并返回节点地址
        return convert_uint16(data)

    def get_calibration_value(self) -> float:
        """
        获取校准值
        Args:
            无

        Returns:
            float: 校准值

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x0E读取校准值

        ==========================================
        Get calibration value
        Args:
            None

        Returns:
            float: Calibration value

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read calibration value from register address 0x0E
        """
        # 从寄存器地址0x0E读取1个寄存器的数据
        data = self.read_registers(1, 0x0E, 1, signed=False)
        # 转换并返回校准值
        return convert_calibration_value(data)

    def get_alarm_threshold(self) -> int:
        """
        获取报警阈值
        Args:
            无

        Returns:
            int: 报警阈值

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x0F读取报警阈值

        ==========================================
        Get alarm threshold
        Args:
            None

        Returns:
            int: Alarm threshold

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read alarm threshold from register address 0x0F
        """
        # 从寄存器地址0x0F读取1个寄存器的数据
        data = self.read_registers(1, 0x0F, 1, signed=False)
        # 转换并返回报警阈值
        return convert_uint16(data)

    def get_clear_threshold(self) -> int:
        """
        获取清除阈值
        Args:
            无

        Returns:
            int: 清除阈值

        Raises:
            TimeoutError: Modbus通信超时

        Notes:
            从寄存器地址0x10读取清除阈值

        ==========================================
        Get clear threshold
        Args:
            None

        Returns:
            int: Clear threshold

        Raises:
            TimeoutError: Modbus communication timeout

        Notes:
            Read clear threshold from register address 0x10
        """
        # 从寄存器地址0x10读取1个寄存器的数据
        data = self.read_registers(1, 0x10, 1, signed=False)
        # 转换并返回清除阈值
        return convert_uint16(data)

    def set_calibration(self, value: int = None) -> bool:
        """
        设置校准值
        Args:
            value (int, optional): 要设置的校准值，如果为None则不设置

        Returns:
            bool: 设置成功返回True

        Raises:
            None: 无异常定义

        Notes:
            向寄存器地址0x0E写入校准值，写入后等待200毫秒

        ==========================================
        Set calibration value
        Args:
            value (int, optional): Calibration value to set, skip if None

        Returns:
            bool: Return True if set successfully

        Raises:
            None: No exceptions defined

        Notes:
            Write calibration value to register address 0x0E, wait 200ms after write
        """
        # 检查value参数是否为None
        if value is None:
            return False
        # 构建Modbus写单个寄存器的PDU
        modbus_pdu = functions.write_single_register(0x0E, value)
        # 清空UART接收缓冲区
        self.host._uart.read()
        # 发送Modbus请求到从站
        self.host._send(modbus_pdu=modbus_pdu, slave_addr=1)
        # 等待200毫秒确保写入完成
        time.sleep_ms(200)
        return True

    def set_alarm_threshold(self, value: int = None) -> bool:
        """
        设置报警阈值
        Args:
            value (int, optional): 要设置的报警阈值，如果为None则不设置

        Returns:
            bool: 设置成功返回True

        Raises:
            None: 无异常定义

        Notes:
            向寄存器地址0x0F写入报警阈值，写入后等待200毫秒

        ==========================================
        Set alarm threshold
        Args:
            value (int, optional): Alarm threshold to set, skip if None

        Returns:
            bool: Return True if set successfully

        Raises:
            None: No exceptions defined

        Notes:
            Write alarm threshold to register address 0x0F, wait 200ms after write
        """
        # 检查value参数是否为None
        if value is None:
            return False
        # 构建Modbus写单个寄存器的PDU
        modbus_pdu = functions.write_single_register(0x0F, value)
        # 清空UART接收缓冲区
        self.host._uart.read()
        # 发送Modbus请求到从站
        self.host._send(modbus_pdu=modbus_pdu, slave_addr=1)
        # 等待200毫秒确保写入完成
        time.sleep_ms(200)
        return True

    def set_clear_threshold(self, value: int = None) -> bool:
        """
        设置清除阈值
        Args:
            value (int, optional): 要设置的清除阈值，如果为None则不设置

        Returns:
            bool: 设置成功返回True

        Raises:
            None: 无异常定义

        Notes:
            向寄存器地址0x10写入清除阈值，写入后等待200毫秒

        ==========================================
        Set clear threshold
        Args:
            value (int, optional): Clear threshold to set, skip if None

        Returns:
            bool: Return True if set successfully

        Raises:
            None: No exceptions defined

        Notes:
            Write clear threshold to register address 0x10, wait 200ms after write
        """
        # 检查value参数是否为None
        if value is None:
            return False
        # 构建Modbus写单个寄存器的PDU
        modbus_pdu = functions.write_single_register(0x10, value)
        # 清空UART接收缓冲区
        self.host._uart.read()
        # 发送Modbus请求到从站
        self.host._send(modbus_pdu=modbus_pdu, slave_addr=1)
        # 等待200毫秒确保写入完成
        time.sleep_ms(200)
        return True


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
