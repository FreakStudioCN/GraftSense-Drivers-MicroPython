# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/07 下午5:30
# @Author  : hogeiha
# @File    : fde_frost_sensor.py
# @Description : 敏源FDE冰霜冰冻传感器Modbus RTU驱动（匹配202512-V3.0寄存器）
# @License : MIT

__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于延时
import time

# 从umodbus库导入串口Modbus主站类
from umodbus.serial import Serial as ModbusRTUMaster

# 导入Modbus功能码函数
from umodbus import functions

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def uint16_to_int16(raw: int) -> int:
    """
    将16位无符号整数转换为16位有符号整数
    Args:
        raw (int): 0-65535范围内的无符号整数

    Raises:
        无

    Notes:
        当数值大于等于32768时减去65536得到负数表示

    ==========================================
    Convert 16-bit unsigned integer to signed integer
    Args:
        raw (int): Unsigned integer in range 0-65535

    Raises:
        None

    Notes:
        Subtract 65536 when value >= 32768 to get negative representation
    """
    # 若数值大于等于32768则转换为负数
    return raw - 65536 if raw >= 32768 else raw


def convert_fde_temperature(raw_data) -> float:
    """
    将Modbus原始字节数据转换为温度值（单位℃）
    Args:
        raw_data (bytes or list): 包含两个字节的字节序列

    Raises:
        无

    Notes:
        传感器协议：温度值扩大10倍，有符号整数，大端序

    ==========================================
    Convert Modbus raw byte data to temperature value (unit: ℃)
    Args:
        raw_data (bytes or list): Byte sequence containing two bytes

    Raises:
        None

    Notes:
        Sensor protocol: temperature value scaled by 10, signed integer, big-endian
    """
    # 拼接两个字节为大端16位整数
    raw = raw_data[0] * 256 + raw_data[1]
    # 处理有符号int16（适配传感器负温度）
    if raw >= 32768:
        raw -= 65536
    # 协议规定除以10得到实际温度
    return raw / 10


# ======================================== 自定义类 ============================================


class FDEFrostSensor:
    """
    敏源FDE冰霜冰冻传感器Modbus RTU驱动类
    Attributes:
        slave_addr (int): Modbus从机地址
        baudrate (int): 串口波特率
        uart_id (int): UART编号
        tx_pin (int): TX引脚号
        rx_pin (int): RX引脚号
        host (ModbusRTUMaster): Modbus主站对象

    Methods:
        read_registers(): 读取保持寄存器
        fde_temperature(): 读取温度
        fde_c1(): 读取C1电容
        fde_c2(): 读取C2电容
        fde_c3(): 读取C3电容
        fde_c2_c3_sum(): 读取C2+C3电容和
        fde_no_load_cap(): 读取空载电容预值
        fde_hw_ver(): 读取硬件版本
        fde_fw_ver(): 读取固件版本
        fde_set_calibration(): 设置或读取校准值

    Notes:
        寄存器地址及定义遵循传感器手册202512-V3.0
        所有读取方法默认从机地址为1，如需修改请在调用时传入参数

    ==========================================
    Minyuan FDE Frost Sensor Modbus RTU Driver Class
    Attributes:
        slave_addr (int): Modbus slave address
        baudrate (int): Serial baud rate
        uart_id (int): UART number
        tx_pin (int): TX pin number
        rx_pin (int): RX pin number
        host (ModbusRTUMaster): Modbus master object

    Methods:
        read_registers(): Read holding registers
        fde_temperature(): Read temperature
        fde_c1(): Read C1 capacitance
        fde_c2(): Read C2 capacitance
        fde_c3(): Read C3 capacitance
        fde_c2_c3_sum(): Read C2+C3 sum capacitance
        fde_no_load_cap(): Read no-load capacitance preset
        fde_hw_ver(): Read hardware version
        fde_fw_ver(): Read firmware version
        fde_set_calibration(): Set or read calibration value

    Notes:
        Register addresses follow sensor datasheet 202512-V3.0
        All read methods use slave address 1 by default
    """

    def __init__(self, slave_addr: int, uart_id: int, tx_pin: int, rx_pin: int) -> None:
        """
        初始化传感器驱动，配置Modbus RTU主站
        Args:
            slave_addr (int): Modbus从机地址
            uart_id (int): UART编号（0或1）
            tx_pin (int): TX引脚GPIO编号
            rx_pin (int): RX引脚GPIO编号

        Raises:
            无

        Notes:
            波特率固定为9600，8数据位，1停止位，无校验

        ==========================================
        Initialize sensor driver and configure Modbus RTU master
        Args:
            slave_addr (int): Modbus slave address
            uart_id (int): UART number (0 or 1)
            tx_pin (int): TX pin GPIO number
            rx_pin (int): RX pin GPIO number

        Raises:
            None

        Notes:
            Baud rate fixed to 9600, 8 data bits, 1 stop bit, no parity
        """
        # 保存从机地址
        self.slave_addr = slave_addr
        # 固定波特率9600
        self.baudrate = 9600
        # 保存UART编号
        self.uart_id = uart_id
        # 保存TX引脚
        self.tx_pin = tx_pin
        # 保存RX引脚
        self.rx_pin = rx_pin

        # 创建Modbus RTU主站对象
        self.host = ModbusRTUMaster(
            pins=(self.tx_pin, self.rx_pin), baudrate=self.baudrate, data_bits=8, stop_bits=1, parity=None, uart_id=self.uart_id
        )

    def read_registers(self, slave_addr: int, starting_addr: int, register_qty: int, signed: bool = True):
        """
        读取Modbus保持寄存器（原始字节数据）
        Args:
            slave_addr (int): 从机地址
            starting_addr (int): 起始寄存器地址
            register_qty (int): 寄存器数量（每个寄存器2字节）
            signed (bool): 是否返回有符号数据（当前未使用）

        Raises:
            无（可能隐式抛出异常）

        Notes:
            返回值为解析后的字节列表，内部逻辑包含清空缓冲区、发送请求、校验响应

        ==========================================
        Read Modbus holding registers (raw byte data)
        Args:
            slave_addr (int): Slave address
            starting_addr (int): Starting register address
            register_qty (int): Number of registers (2 bytes each)
            signed (bool): Whether to return signed data (currently unused)

        Raises:
            None (exceptions may be raised implicitly)

        Notes:
            Returns parsed byte list, internal logic clears buffer, sends request, validates response
        """
        # 构建读保持寄存器的Modbus PDU
        modbus_pdu = functions.read_holding_registers(starting_address=starting_addr, quantity=register_qty)
        # 清空UART接收缓冲区
        self.host._uart.read()

        # 发送Modbus请求
        self.host._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)
        # 读取响应并校验
        response = self.host._uart_read()
        return self.host._validate_resp_hdr(response=self.host._uart_read(), slave_addr=slave_addr, function_code=modbus_pdu[0], count=True)

    def fde_temperature(self) -> float:
        """
        读取传感器温度值
        Args:
            无

        Raises:
            无

        Notes:
            返回值为摄氏度，支持负数，分辨率0.1℃

        ==========================================
        Read sensor temperature value
        Args:
            None

        Raises:
            None

        Notes:
            Return value in Celsius, supports negative values, resolution 0.1℃
        """
        # 读取寄存器0x0009（温度寄存器）
        data = self.read_registers(1, 0x09, 1, signed=False)
        # 转换原始数据为温度
        return convert_fde_temperature(data)

    # C1电容 0x04
    def fde_c1(self) -> float:
        """
        读取C1电容值（单位pF）
        Args:
            无

        Raises:
            无

        Notes:
            寄存器原始值扩大1000倍，返回值除以1000得到实际pF值

        ==========================================
        Read C1 capacitance value (unit: pF)
        Args:
            None

        Raises:
            None

        Notes:
            Register raw value scaled by 1000, return value divided by 1000 to get actual pF
        """
        # 读取寄存器0x0004（C1电容）
        data = self.read_registers(1, 0x04, 1, signed=False)
        # 拼接大端16位整数并除以1000
        return (data[0] * 256 + data[1]) / 1000

    # C2电容 0x07
    def fde_c2(self) -> float:
        """
        读取C2电容值（单位pF）
        Args:
            无

        Raises:
            无

        Notes:
            寄存器原始值扩大1000倍，返回值除以1000得到实际pF值

        ==========================================
        Read C2 capacitance value (unit: pF)
        Args:
            None

        Raises:
            None

        Notes:
            Register raw value scaled by 1000, return value divided by 1000 to get actual pF
        """
        # 读取寄存器0x0007（C2电容）
        data = self.read_registers(1, 0x07, 1, signed=False)
        # 拼接大端16位整数并除以1000
        return (data[0] * 256 + data[1]) / 1000

    # C3电容 0x08
    def fde_c3(self) -> float:
        """
        读取C3电容值（单位pF）
        Args:
            无

        Raises:
            无

        Notes:
            寄存器原始值扩大1000倍，返回值除以1000得到实际pF值

        ==========================================
        Read C3 capacitance value (unit: pF)
        Args:
            None

        Raises:
            None

        Notes:
            Register raw value scaled by 1000, return value divided by 1000 to get actual pF
        """
        # 读取寄存器0x0008（C3电容）
        data = self.read_registers(1, 0x08, 1, signed=False)
        # 拼接大端16位整数并除以1000
        return (data[0] * 256 + data[1]) / 1000

    # C2+C3电容总和 0x0A
    def fde_c2_c3_sum(self) -> float:
        """
        读取C2与C3电容之和（单位pF）
        Args:
            无

        Raises:
            无

        Notes:
            寄存器原始值扩大1000倍，返回值除以1000得到实际pF值

        ==========================================
        Read sum of C2 and C3 capacitance (unit: pF)
        Args:
            None

        Raises:
            None

        Notes:
            Register raw value scaled by 1000, return value divided by 1000 to get actual pF
        """
        # 读取寄存器0x000A（C2+C3和）
        data = self.read_registers(1, 0x0A, 1, signed=False)
        # 拼接大端16位整数并除以1000
        return (data[0] * 256 + data[1]) / 1000

    # 空载电容预值 0x0F
    def fde_no_load_cap(self) -> int:
        """
        读取空载电容预值（原始整数，单位pF，未扩大）
        Args:
            无

        Raises:
            无

        Notes:
            该值直接来自寄存器0x000F，不进行缩放

        ==========================================
        Read no-load capacitance preset (raw integer, unit: pF, not scaled)
        Args:
            None

        Raises:
            None

        Notes:
            Value directly from register 0x000F, no scaling applied
        """
        # 读取寄存器0x000F（空载电容预值）
        data = self.read_registers(1, 0x0F, 1, signed=False)
        # 拼接大端16位整数并直接返回
        return data[0] * 256 + data[1]

    # 硬件版本 0x12
    def fde_hw_ver(self) -> int:
        """
        读取硬件版本号（编码整数，如0x2A表示版本2.A）
        Args:
            无

        Raises:
            无

        Notes:
            高8位为主版本，低8位为次版本（ASCII或数字）

        ==========================================
        Read hardware version (encoded integer, e.g. 0x2A means version 2.A)
        Args:
            None

        Raises:
            None

        Notes:
            High byte is major version, low byte is minor version (ASCII or digit)
        """
        # 读取寄存器0x0012（硬件版本）
        data = self.read_registers(1, 0x12, 1, signed=False)
        # 拼接大端16位整数并返回
        return data[0] * 256 + data[1]

    # 固件版本 0x13
    def fde_fw_ver(self) -> int:
        """
        读取固件版本号（编码整数）
        Args:
            无

        Raises:
            无

        Notes:
            格式同硬件版本，高8位主版本，低8位次版本

        ==========================================
        Read firmware version (encoded integer)
        Args:
            None

        Raises:
            None

        Notes:
            Same format as hardware version, high byte major, low byte minor
        """
        # 读取寄存器0x0013（固件版本）
        data = self.read_registers(1, 0x13, 1, signed=False)
        # 拼接大端16位整数并返回
        return data[0] * 256 + data[1]

    # 写入校准值（带参数传入，有参数=写入，无参数=仅查看）
    def fde_set_calibration(self, value: int = None):
        """
        设置或读取校准值（寄存器0x000E）
        Args:
            value (int, optional): 校准值，写入1执行校准；None时仅读取

        Raises:
            无

        Notes:
            当value不为None时，向寄存器0x000E写入value；否则调用内部读取方法（当前未实现读取）

        ==========================================
        Set or read calibration value (register 0x000E)
        Args:
            value (int, optional): Calibration value, write 1 to calibrate; None to read only

        Raises:
            None

        Notes:
            If value is not None, write to register 0x000E; otherwise call internal read method (currently not implemented)
        """
        # 显式检查参数是否为None
        if value is None:
            # 无参数时，返回当前校准值（方法未实现，此处保留原逻辑）
            return self.fde_get_calibration()
        # 有参数 → 写入校准寄存器
        modbus_pdu = functions.write_single_register(0x0E, value)
        # 清空UART接收缓冲区
        self.host._uart.read()
        # 发送写寄存器请求
        self.host._send(modbus_pdu=modbus_pdu, slave_addr=1)
        # 等待200ms确保写入完成
        time.sleep_ms(200)
        return True


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
