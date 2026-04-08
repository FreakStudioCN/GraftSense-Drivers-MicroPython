# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : hogeiha
# @File    : main.py
# @Description : MSE土壤温湿度传感器Modbus RTU驱动，提供寄存器读写接口
# @License : MIT

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from umodbus.serial import Serial as ModbusRTUMaster

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MSESoilSensor:
    """
    MSE土壤温湿度传感器Modbus RTU驱动类
    提供传感器所有寄存器的读写操作，自动处理缩放系数和数据类型转换。

    Attributes:
        slave_addr (int): Modbus从机地址
        baudrate (int): 串口波特率
        uart_id (int): UART编号
        tx_pin (int): TX引脚编号
        rx_pin (int): RX引脚编号
        host (ModbusRTUMaster): Modbus RTU主机实例

    Methods:
        read_node_address(): 读取从机地址
        read_temperature(): 读取温度值(℃)
        read_capacitance(): 读取原始电容值(pF)
        read_cap_center(): 读取电容中心值(pF)
        read_cap_range(): 读取电容量程(pF)
        read_filter_count(): 读取电容滤波次数
        write_filter_count(): 写入电容滤波次数
        read_avg_window_size(): 读取滑动平均窗口大小
        write_avg_window_size(): 写入滑动平均窗口大小
        read_temp_comp_A(): 读取温度补偿系数A
        write_temp_comp_A(): 写入温度补偿系数A
        read_temp_comp_B(): 读取温度补偿系数B
        write_temp_comp_B(): 写入温度补偿系数B
        read_hw_version(): 读取硬件版本号
        read_firmware_version(): 读取固件版本号
        read_device_uid(): 读取96位设备唯一UID

    Notes:
        所有只读寄存器读取失败时返回None，写操作返回bool表示成功与否。
        温度值缩放系数为10，电容值缩放系数为100，补偿系数缩放系数为1000。

    ==========================================
    Modbus RTU driver class for MSE soil moisture/temperature sensor.
    Provides read/write operations for all sensor registers with automatic scaling.

    Attributes:
        slave_addr (int): Modbus slave address
        baudrate (int): Serial baudrate
        uart_id (int): UART ID
        tx_pin (int): TX pin number
        rx_pin (int): RX pin number
        host (ModbusRTUMaster): Modbus RTU master instance

    Methods:
        read_node_address(): Read slave address
        read_temperature(): Read temperature (degree Celsius)
        read_capacitance(): Read raw capacitance (pF)
        read_cap_center(): Read capacitance center value (pF)
        read_cap_range(): Read capacitance range (pF)
        read_filter_count(): Read capacitance filter count
        write_filter_count(): Write capacitance filter count
        read_avg_window_size(): Read moving average window size
        write_avg_window_size(): Write moving average window size
        read_temp_comp_A(): Read temperature compensation coefficient A
        write_temp_comp_A(): Write temperature compensation coefficient A
        read_temp_comp_B(): Read temperature compensation coefficient B
        write_temp_comp_B(): Write temperature compensation coefficient B
        read_hw_version(): Read hardware version
        read_firmware_version(): Read firmware version
        read_device_uid(): Read 96-bit device unique ID

    Notes:
        Read methods return None on failure, write methods return bool.
        Scaling factors: temperature x10, capacitance x100, compensation x1000.
    """

    def __init__(self, slave_addr: int, baudrate: int, uart_id: int, tx_pin: int, rx_pin: int) -> None:
        """
        初始化Modbus RTU主机并保存传感器参数

        Args:
            slave_addr (int): Modbus从机地址
            baudrate (int): 串口波特率
            uart_id (int): UART编号
            tx_pin (int): TX引脚编号
            rx_pin (int): RX引脚编号

        Raises:
            无

        Notes:
            使用umodbus库创建Modbus RTU主机实例，配置8数据位、1停止位、无校验。

        ==========================================
        Initialize Modbus RTU master and store sensor parameters

        Args:
            slave_addr (int): Modbus slave address
            baudrate (int): Serial baudrate
            uart_id (int): UART ID
            tx_pin (int): TX pin number
            rx_pin (int): RX pin number

        Raises:
            None

        Notes:
            Create Modbus RTU master instance using umodbus library with 8 data bits,
            1 stop bit, no parity.
        """
        self.slave_addr = slave_addr
        self.baudrate = baudrate
        self.uart_id = uart_id
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin

        # 初始化Modbus主机
        self.host = ModbusRTUMaster(
            pins=(self.tx_pin, self.rx_pin), baudrate=self.baudrate, data_bits=8, stop_bits=1, parity=None, uart_id=self.uart_id
        )

    # 0x0001 节点地址 (只读)
    def read_node_address(self) -> int | None:
        """
        读取Modbus从机地址（寄存器0x0001）

        Args:
            无

        Returns:
            int | None: 成功时返回从机地址(1-247)，失败返回None

        Raises:
            无

        Notes:
            只读寄存器，用于验证传感器响应。

        ==========================================
        Read Modbus slave address (register 0x0001)

        Args:
            None

        Returns:
            int | None: Slave address (1-247) on success, None on failure

        Raises:
            None

        Notes:
            Read-only register, used to verify sensor response.
        """
        try:
            return self.host.read_holding_registers(self.slave_addr, 0x01, 1, False)[0]
        except:
            return None

    # 0x0002 温度 (只读 ×10)
    def read_temperature(self) -> float | None:
        """
        读取温度值（寄存器0x0002，原始值×10）

        Args:
            无

        Returns:
            float | None: 成功时返回温度(℃)，精度0.1℃，失败返回None

        Raises:
            无

        Notes:
            原始寄存器值为整数，除以10得到实际温度。

        ==========================================
        Read temperature (register 0x0002, raw value x10)

        Args:
            None

        Returns:
            float | None: Temperature in degree Celsius with 0.1 precision on success,
                         None on failure

        Raises:
            None

        Notes:
            Raw register value is integer, divide by 10 to get actual temperature.
        """
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x02, 1, True)[0]
            return round(raw / 10.0, 1)
        except:
            return None

    # 0x0003 电容值 (只读 ×100)
    def read_capacitance(self) -> float | None:
        """
        读取原始电容值（寄存器0x0003，原始值×100）

        Args:
            无

        Returns:
            float | None: 成功时返回电容值(pF)，精度0.01pF，失败返回None

        Raises:
            无

        Notes:
            原始寄存器值为整数，除以100得到实际电容值。

        ==========================================
        Read raw capacitance (register 0x0003, raw value x100)

        Args:
            None

        Returns:
            float | None: Capacitance in pF with 0.01 precision on success,
                         None on failure

        Raises:
            None

        Notes:
            Raw register value is integer, divide by 100 to get actual capacitance.
        """
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x03, 1, False)[0]
            return round(raw / 100.0, 2)
        except:
            return None

    # 0x0004 电容中心值 (只读 ×100)
    def read_cap_center(self) -> float | None:
        """
        读取电容中心值（寄存器0x0004，原始值×100）

        Args:
            无

        Returns:
            float | None: 成功时返回中心电容值(pF)，精度0.01pF，失败返回None

        Raises:
            无

        Notes:
            用于校准的参考值。

        ==========================================
        Read capacitance center value (register 0x0004, raw value x100)

        Args:
            None

        Returns:
            float | None: Center capacitance in pF with 0.01 precision on success,
                         None on failure

        Raises:
            None

        Notes:
            Reference value for calibration.
        """
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x04, 1, False)[0]
            return round(raw / 100.0, 2)
        except:
            return None

    # 0x0005 电容量程 (只读 ×100)
    def read_cap_range(self) -> float | None:
        """
        读取电容量程（寄存器0x0005，原始值×100）

        Args:
            无

        Returns:
            float | None: 成功时返回量程(pF)，精度0.01pF，失败返回None

        Raises:
            无

        Notes:
            传感器测量范围。

        ==========================================
        Read capacitance range (register 0x0005, raw value x100)

        Args:
            None

        Returns:
            float | None: Capacitance range in pF with 0.01 precision on success,
                         None on failure

        Raises:
            None

        Notes:
            Measurement range of the sensor.
        """
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x05, 1, False)[0]
            return round(raw / 100.0, 2)
        except:
            return None

    # 0x0006 电容滤波次数 (读写 0-65535)
    def read_filter_count(self) -> int | None:
        """
        读取电容滤波次数（寄存器0x0006）

        Args:
            无

        Returns:
            int | None: 成功时返回滤波次数(0-65535)，失败返回None

        Raises:
            无

        Notes:
            值越大输出越平滑但响应变慢。

        ==========================================
        Read capacitance filter count (register 0x0006)

        Args:
            None

        Returns:
            int | None: Filter count (0-65535) on success, None on failure

        Raises:
            None

        Notes:
            Larger value gives smoother output but slower response.
        """
        try:
            return self.host.read_holding_registers(self.slave_addr, 0x06, 1, False)[0]
        except:
            return None

    def write_filter_count(self, value: int) -> bool:
        """
        写入电容滤波次数（寄存器0x0006）

        Args:
            value (int): 滤波次数，范围0-65535

        Returns:
            bool: 成功返回True，失败返回False

        Raises:
            无

        Notes:
            写入后立即生效，掉电保存。

        ==========================================
        Write capacitance filter count (register 0x0006)

        Args:
            value (int): Filter count, range 0-65535

        Returns:
            bool: True on success, False on failure

        Raises:
            None

        Notes:
            Takes effect immediately, saved in non-volatile memory.
        """
        try:
            self.host.write_single_register(self.slave_addr, 0x06, value)
            return True
        except:
            return False

    # 0x0007 滑动平均窗口大小 (读写 0-65535)
    def read_avg_window_size(self) -> int | None:
        """
        读取滑动平均窗口大小（寄存器0x0007）

        Args:
            无

        Returns:
            int | None: 成功时返回窗口大小(0-65535)，失败返回None

        Raises:
            无

        Notes:
            窗口越大输出越平滑。

        ==========================================
        Read moving average window size (register 0x0007)

        Args:
            None

        Returns:
            int | None: Window size (0-65535) on success, None on failure

        Raises:
            None

        Notes:
            Larger window gives smoother output.
        """
        try:
            return self.host.read_holding_registers(self.slave_addr, 0x07, 1, False)[0]
        except:
            return None

    def write_avg_window_size(self, value: int) -> bool:
        """
        写入滑动平均窗口大小（寄存器0x0007）

        Args:
            value (int): 窗口大小，范围0-65535

        Returns:
            bool: 成功返回True，失败返回False

        Raises:
            无

        Notes:
            写入后立即生效，掉电保存。

        ==========================================
        Write moving average window size (register 0x0007)

        Args:
            value (int): Window size, range 0-65535

        Returns:
            bool: True on success, False on failure

        Raises:
            None

        Notes:
            Takes effect immediately, saved in non-volatile memory.
        """
        try:
            self.host.write_single_register(self.slave_addr, 0x07, value)
            return True
        except:
            return False

    # 0x0008 温补系数A (读写 ×1000)
    def read_temp_comp_A(self) -> float | None:
        """
        读取温度补偿系数A（寄存器0x0008，原始值×1000）

        Args:
            无

        Returns:
            float | None: 成功时返回系数A，精度0.001，失败返回None

        Raises:
            无

        Notes:
            原始寄存器值为有符号整数，除以1000得到实际系数。

        ==========================================
        Read temperature compensation coefficient A (register 0x0008, raw value x1000)

        Args:
            None

        Returns:
            float | None: Coefficient A with 0.001 precision on success, None on failure

        Raises:
            None

        Notes:
            Raw register value is signed integer, divide by 1000 to get actual coefficient.
        """
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x08, 1, True)[0]
            return round(raw / 1000.0, 3)
        except:
            return None

    def write_temp_comp_A(self, value: float) -> bool:
        """
        写入温度补偿系数A（寄存器0x0008，实际值×1000后写入）

        Args:
            value (float): 系数A，范围-32.768 ~ 32.767

        Returns:
            bool: 成功返回True，失败返回False

        Raises:
            无

        Notes:
            自动限制范围并转换为有符号整数写入。

        ==========================================
        Write temperature compensation coefficient A (register 0x0008, write actual value x1000)

        Args:
            value (float): Coefficient A, range -32.768 ~ 32.767

        Returns:
            bool: True on success, False on failure

        Raises:
            None

        Notes:
            Automatically clamp range and convert to signed integer before writing.
        """
        try:
            val = max(-32768, min(32767, int(value * 1000)))
            self.host.write_single_register(self.slave_addr, 0x08, val, signed=True)
            return True
        except:
            return False

    # 0x0009 温补系数B (读写 ×1000)
    def read_temp_comp_B(self) -> float | None:
        """
        读取温度补偿系数B（寄存器0x0009，原始值×1000）

        Args:
            无

        Returns:
            float | None: 成功时返回系数B，精度0.001，失败返回None

        Raises:
            无

        Notes:
            原始寄存器值为有符号整数，除以1000得到实际系数。

        ==========================================
        Read temperature compensation coefficient B (register 0x0009, raw value x1000)

        Args:
            None

        Returns:
            float | None: Coefficient B with 0.001 precision on success, None on failure

        Raises:
            None

        Notes:
            Raw register value is signed integer, divide by 1000 to get actual coefficient.
        """
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x09, 1, True)[0]
            return round(raw / 1000.0, 3)
        except:
            return None

    def write_temp_comp_B(self, value: float) -> bool:
        """
        写入温度补偿系数B（寄存器0x0009，实际值×1000后写入）

        Args:
            value (float): 系数B，范围-32.768 ~ 32.767

        Returns:
            bool: 成功返回True，失败返回False

        Raises:
            无

        Notes:
            自动限制范围并转换为有符号整数写入。

        ==========================================
        Write temperature compensation coefficient B (register 0x0009, write actual value x1000)

        Args:
            value (float): Coefficient B, range -32.768 ~ 32.767

        Returns:
            bool: True on success, False on failure

        Raises:
            None

        Notes:
            Automatically clamp range and convert to signed integer before writing.
        """
        try:
            val = max(-32768, min(32767, int(value * 1000)))
            self.host.write_single_register(self.slave_addr, 0x09, val, signed=True)
            return True
        except:
            return False

    # 0x000C 硬件版本号 (只读) ✅ 修复：读取1个寄存器
    def read_hw_version(self) -> str | None:
        """
        读取硬件版本号（寄存器0x000C）

        Args:
            无

        Returns:
            str | None: 成功返回格式"Vmajor.minor"，失败返回None

        Raises:
            无

        Notes:
            高8位为主版本，低8位为次版本。

        ==========================================
        Read hardware version (register 0x000C)

        Args:
            None

        Returns:
            str | None: Format "Vmajor.minor" on success, None on failure

        Raises:
            None

        Notes:
            High byte is major version, low byte is minor version.
        """
        try:
            data = self.host.read_holding_registers(self.slave_addr, 0x0C, 1, False)[0]
            major = (data >> 8) & 0xFF
            minor = data & 0xFF
            return f"V{major}.{minor}"
        except:
            return None

    # 0x000D 固件版本号 (只读) ✅ 修复：无符号数
    def read_firmware_version(self) -> int | None:
        """
        读取固件版本号（寄存器0x000D）

        Args:
            无

        Returns:
            int | None: 成功返回固件版本号(无符号整数)，失败返回None

        Raises:
            无

        Notes:
            数值含义参考传感器手册。

        ==========================================
        Read firmware version (register 0x000D)

        Args:
            None

        Returns:
            int | None: Firmware version (unsigned integer) on success, None on failure

        Raises:
            None

        Notes:
            Refer to sensor manual for value interpretation.
        """
        try:
            return self.host.read_holding_registers(self.slave_addr, 0x0D, 1, False)[0]
        except:
            return None

    # 0x0014 ~ 0x0019 设备UID ✅ 修复：正确96bit移位
    def read_device_uid(self) -> str | None:
        """
        读取96位设备唯一UID（寄存器0x0014~0x0019，共6个寄存器）

        Args:
            无

        Returns:
            str | None: 成功返回格式"0x" + 24位十六进制字符串，失败返回None

        Raises:
            无

        Notes:
            96bit UID组合为6个连续16位寄存器，按大端顺序组合。

        ==========================================
        Read 96-bit device unique ID (registers 0x0014~0x0019, total 6 registers)

        Args:
            None

        Returns:
            str | None: Format "0x" + 24-digit hexadecimal string on success,
                       None on failure

        Raises:
            None

        Notes:
            96-bit UID is composed of 6 consecutive 16-bit registers,
            combined in big-endian order.
        """
        try:
            # 读取6个连续寄存器：0x14,0x15,0x16,0x17,0x18,0x19
            data = self.host.read_holding_registers(self.slave_addr, 0x14, 6, False)
            if data and len(data) == 6:
                # 96bit 正确移位组合（6个16bit寄存器）
                uid_96bit = (
                    (data[0] << 80)  # 第1个寄存器(0x14)：最高16bit
                    | (data[1] << 64)  # 第2个寄存器(0x15)
                    | (data[2] << 48)  # 第3个寄存器(0x16)
                    | (data[3] << 32)  # 第4个寄存器(0x17)
                    | (data[4] << 16)  # 第5个寄存器(0x18)
                    | data[5]  # 第6个寄存器(0x19)：最低16bit
                )
                # 格式化输出：完整24位十六进制 = 96bit
                return f"0x{uid_96bit:024X}"
            return None
        except:
            return None


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
