# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : hogeiha
# @File    : mer.py
# @Description : MER水尺液位传感器 Modbus RTU 驱动
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


class MER:
    """
    MER水尺Modbus RTU驱动类
    Attributes:
        slave_addr (int): Modbus从站地址
        baudrate (int): 串口通信波特率
        uart_id (int): UART接口ID编号
        tx_pin (int): 发送引脚编号
        rx_pin (int): 接收引脚编号
        host (ModbusRTUMaster): Modbus RTU主机对象

    Methods:
        wake_up(): 唤醒低功耗传感器
        read_node_address(): 读取节点地址
        write_node_address(): 写入节点地址
        read_level(): 读取液位值
        read_temp(): 读取温度值
        read_capacitance(): 读取电容值
        read_ratio(): 读取比值
        read_frequency(): 读取频率值
        read_filter_count(): 读取滤波次数
        write_filter_count(): 写入滤波次数
        read_calib_switch(): 读取校准开关状态
        write_calib_switch(): 写入校准开关状态
        read_low_power_enable(): 读取低功耗使能状态
        write_low_power_enable(): 写入低功耗使能状态
        read_hw_version(): 读取硬件版本号
        read_fw_version(): 读取固件版本号
        read_device_uid(): 读取设备唯一标识符
        read_ref_level1(): 读取参考液位1
        write_ref_level1(): 写入参考液位1
        read_ref_level2(): 读取参考液位2
        write_ref_level2(): 写入参考液位2
        read_ref_level3(): 读取参考液位3
        write_ref_level3(): 写入参考液位3

    Notes:
        传感器默认Modbus从站地址为1，波特率9600，8数据位，1停止位，None校验
        每次通信前需调用wake_up()唤醒传感器

    ==========================================
    WS61 Capacitive Liquid Level Sensor Modbus RTU Driver Class
    Attributes:
        slave_addr (int): Modbus slave address
        baudrate (int): Serial communication baudrate
        uart_id (int): UART interface ID number
        tx_pin (int): Transmit pin number
        rx_pin (int): Receive pin number
        host (ModbusRTUMaster): Modbus RTU master object

    Methods:
        wake_up(): Wake up low-power sensor
        read_node_address(): Read node address
        write_node_address(): Write node address
        read_level(): Read level value
        read_temp(): Read temperature value
        read_capacitance(): Read capacitance value
        read_ratio(): Read ratio value
        read_frequency(): Read frequency value
        read_filter_count(): Read filter count
        write_filter_count(): Write filter count
        read_calib_switch(): Read calibration switch status
        write_calib_switch(): Write calibration switch status
        read_low_power_enable(): Read low power enable status
        write_low_power_enable(): Write low power enable status
        read_hw_version(): Read hardware version
        read_fw_version(): Read firmware version
        read_device_uid(): Read device unique identifier
        read_ref_level1(): Read reference level 1
        write_ref_level1(): Write reference level 1
        read_ref_level2(): Read reference level 2
        write_ref_level2(): Write reference level 2
        read_ref_level3(): Read reference level 3
        write_ref_level3(): Write reference level 3

    Notes:
        Sensor default Modbus slave address is 1, baudrate 9600, 8 data bits, 1 stop bit, no parity
        Must call wake_up() before each communication
    """

    def __init__(self, slave_addr: int, uart_id: int, tx_pin: int, rx_pin: int) -> None:
        """
        初始化Modbus主机，WS61固定波特率9600，8N1
        Args:
            slave_addr (int): Modbus从机地址
            uart_id (int): UART编号
            tx_pin (int): TX引脚
            rx_pin (int): RX引脚

        Raises:
            ValueError: 当slave_addr不在1-252范围内时抛出

        Notes:
            初始化时设置波特率9600，8数据位，1停止位，None校验

        ==========================================
        Initialize the Modbus master, WS61 fixed baud rate 9600, 8N1
        Args:
            slave_addr (int): Modbus slave address
            uart_id (int): UART ID
            tx_pin (int): TX pin
            rx_pin (int): RX pin

        Raises:
            ValueError: Raised when slave_addr is not in range 1-252

        Notes:
            Set baudrate 9600, 8 data bits, 1 stop bit, no parity during initialization
        """
        # 校验从站地址参数合法性
        if not (1 <= slave_addr <= 252):
            raise ValueError(f"Invalid slave_addr: {slave_addr}, must be in range 1-252")
        if not isinstance(uart_id, int) or uart_id not in (0, 1, 2):
            raise ValueError("uart_id must be integer 0, 1 or 2")

        if not isinstance(tx_pin, int) or tx_pin < 0:
            raise ValueError("tx_pin must be valid positive integer pin number")

        if not isinstance(rx_pin, int) or rx_pin < 0:
            raise ValueError("rx_pin must be valid positive integer pin number")
        # 设置Modbus从站地址
        self.slave_addr = slave_addr
        # WS61固定波特率
        self.baudrate = 9600
        # 设置UART接口ID
        self.uart_id = uart_id
        # 设置发送引脚编号
        self.tx_pin = tx_pin
        # 设置接收引脚编号
        self.rx_pin = rx_pin

        # 初始化Modbus RTU主机
        self.host = ModbusRTUMaster(
            pins=(self.tx_pin, self.rx_pin), baudrate=self.baudrate, data_bits=8, stop_bits=1, parity=None, uart_id=self.uart_id
        )

    def wake_up(self) -> bool:
        """
        低功耗唤醒：发送0x8F指令，等待30ms
        Returns:
            bool: 唤醒成功返回True，失败返回False

        Raises:
            None: None异常定义

        Notes:
            每次通信前必须调用此函数

        ==========================================
        Wake up low-power sensor: send 0x8F command, wait 30ms
        Returns:
            bool: True if wake-up succeeded, False otherwise

        Raises:
            None: No exceptions defined

        Notes:
            Must be called before each communication
        """
        try:
            # 发送唤醒指令
            self.host._uart.write(b"\x8F")
            # 官方要求大于等于30毫秒
            time.sleep_ms(30)
            return True
        except Exception:
            return False

    # 0x0001 节点地址
    def read_node_address(self) -> int | None:
        """
        读取节点地址
        Args:
            None

        Returns:
            int | None: 节点地址值，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x01读取节点地址

        ==========================================
        Read node address
        Args:
            None

        Returns:
            int | None: Node address value, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read node address from register address 0x01
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x01读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x01, 1, False)[0]
        except Exception:
            return None

    # 0x0001 节点地址 写函数
    def write_node_address(self, addr: int) -> bool:
        """
        写入节点地址
        Args:
            addr (int): 要设置的节点地址，范围1-252

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            ValueError: 当addr不在1-252范围内时抛出

        Notes:
            向寄存器地址0x01写入节点地址

        ==========================================
        Write node address
        Args:
            addr (int): Node address to set, range 1-252

        Returns:
            bool: True if set successfully, False otherwise

        Raises:
            ValueError: Raised when addr is not in range 1-252

        Notes:
            Write node address to register address 0x01
        """
        # 校验参数合法性
        if addr is None:
            raise ValueError("addr cannot be None")
        if not (1 <= addr <= 252):
            raise ValueError(f"Invalid addr: {addr}, must be in range 1-252")
        # 唤醒传感器
        self.wake_up()
        try:
            # 向寄存器地址0x01写入节点地址
            self.host.write_single_register(self.slave_addr, 0x01, addr)
            return True
        except Exception:
            return False

    # 0x0002 液位 mm
    def read_level(self) -> int | None:
        """
        读取液位值
        Args:
            None

        Returns:
            int | None: 液位值，单位为毫米，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x02读取液位数据

        ==========================================
        Read level value
        Args:
            None

        Returns:
            int | None: Level value in millimeters, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read level data from register address 0x02
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x02读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x02, 1, False)[0]
        except Exception:
            return None

    # 0x0003 温度 ℃（×10）
    def read_temp(self) -> float | None:
        """
        读取温度值
        Args:
            None

        Returns:
            float | None: 温度值，单位为摄氏度，精度0.1度，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x03读取温度数据，原始值需除以10

        ==========================================
        Read temperature value
        Args:
            None

        Returns:
            float | None: Temperature value in Celsius with 0.1 degree precision, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read temperature data from register address 0x03, raw value needs to be divided by 10
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x03读取1个寄存器的数据
            raw = self.host.read_holding_registers(self.slave_addr, 0x03, 1, False)[0]
            # 转换并返回温度值，保留一位小数
            return round(raw / 10.0, 1)
        except Exception:
            return None

    # ==================== 以下为补全的寄存器函数 ====================
    # 0x0004 电容值 pf（×1000）只读
    def read_capacitance(self) -> float | None:
        """
        读取电容值
        Args:
            None

        Returns:
            float | None: 电容值，单位为皮法，精度0.001pF，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x04读取电容数据，原始值需除以1000

        ==========================================
        Read capacitance value
        Args:
            None

        Returns:
            float | None: Capacitance value in picofarads with 0.001pF precision, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read capacitance data from register address 0x04, raw value needs to be divided by 1000
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x04读取1个寄存器的数据
            raw = self.host.read_holding_registers(self.slave_addr, 0x04, 1, False)[0]
            # 转换并返回电容值，保留三位小数
            return round(raw / 1000.0, 3)
        except Exception:
            return None

    # 0x0005 比值（×1000）只读
    def read_ratio(self) -> float | None:
        """
        读取比值
        Args:
            None

        Returns:
            float | None: 比值，精度0.001，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x05读取比值数据，原始值需除以1000

        ==========================================
        Read ratio value
        Args:
            None

        Returns:
            float | None: Ratio value with 0.001 precision, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read ratio data from register address 0x05, raw value needs to be divided by 1000
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x05读取1个寄存器的数据
            raw = self.host.read_holding_registers(self.slave_addr, 0x05, 1, False)[0]
            # 转换并返回比值，保留三位小数
            return round(raw / 1000.0, 3)
        except Exception:
            return None

    # 0x0006 实测频率 MHz（×1000）只读
    def read_frequency(self) -> float | None:
        """
        读取频率值
        Args:
            None

        Returns:
            float | None: 频率值，单位为兆赫兹，精度0.001MHz，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x06读取频率数据，原始值需除以1000

        ==========================================
        Read frequency value
        Args:
            None

        Returns:
            float | None: Frequency value in megahertz with 0.001MHz precision, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read frequency data from register address 0x06, raw value needs to be divided by 1000
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x06读取1个寄存器的数据
            raw = self.host.read_holding_registers(self.slave_addr, 0x06, 1, False)[0]
            # 转换并返回频率值，保留三位小数
            return round(raw / 1000.0, 3)
        except Exception:
            return None

    # 0x0007 均值滤波次数 读写
    def read_filter_count(self) -> int | None:
        """
        读取均值滤波次数
        Args:
            None

        Returns:
            int | None: 滤波次数值，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x07读取滤波次数

        ==========================================
        Read filter count
        Args:
            None

        Returns:
            int | None: Filter count value, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read filter count from register address 0x07
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x07读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x07, 1, False)[0]
        except Exception:
            return None

    def write_filter_count(self, count: int) -> bool:
        """
        写入均值滤波次数
        Args:
            count (int): 要设置的滤波次数，范围0-65535

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            ValueError: 当count不在0-65535范围内时抛出

        Notes:
            向寄存器地址0x07写入滤波次数

        ==========================================
        Write filter count
        Args:
            count (int): Filter count to set, range 0-65535

        Returns:
            bool: True if set successfully, False otherwise

        Raises:
            ValueError: Raised when count is not in range 0-65535

        Notes:
            Write filter count to register address 0x07
        """
        # 校验参数合法性
        if count is None:
            raise ValueError("count cannot be None")
        if not (0 <= count <= 65535):
            raise ValueError(f"Invalid count: {count}, must be in range 0-65535")
        # 唤醒传感器
        self.wake_up()
        try:
            # 向寄存器地址0x07写入滤波次数
            self.host.write_single_register(self.slave_addr, 0x07, count)
            return True
        except Exception:
            return False

    # 0x000E 校准开关 读写（0=关闭，1=校准1，2=校准2，3=完成）
    def read_calib_switch(self) -> int | None:
        """
        读取校准开关状态
        Args:
            None

        Returns:
            int | None: 校准开关状态（0=关闭，1=校准1，2=校准2，3=完成），失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x0E读取校准开关状态

        ==========================================
        Read calibration switch status
        Args:
            None

        Returns:
            int | None: Calibration switch status (0=off, 1=calibration1, 2=calibration2, 3=complete), None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read calibration switch status from register address 0x0E
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x0E读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x0E, 1, False)[0]
        except Exception:
            return None

    def write_calib_switch(self, switch: int) -> bool:
        """
        写入校准开关状态
        Args:
            switch (int): 要设置的校准开关状态（0=关闭，1=校准1，2=校准2，3=完成）

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            ValueError: 当switch不在[0,1,2,3]中时抛出

        Notes:
            向寄存器地址0x0E写入校准开关状态

        ==========================================
        Write calibration switch status
        Args:
            switch (int): Calibration switch status to set (0=off, 1=calibration1, 2=calibration2, 3=complete)

        Returns:
            bool: True if set successfully, False otherwise

        Raises:
            ValueError: Raised when switch is not in [0,1,2,3]

        Notes:
            Write calibration switch status to register address 0x0E
        """
        # 校验参数合法性
        if switch is None:
            raise ValueError("switch cannot be None")
        if switch not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid switch: {switch}, must be 0, 1, 2, or 3")
        # 唤醒传感器
        self.wake_up()
        try:
            # 向寄存器地址0x0E写入校准开关状态
            self.host.write_single_register(self.slave_addr, 0x0E, switch)
            return True
        except Exception:
            return False

    # 0x000F 低功耗使能 读写（0=关闭，1=开启）
    def read_low_power_enable(self) -> int | None:
        """
        读取低功耗使能状态
        Args:
            None

        Returns:
            int | None: 低功耗使能状态（0=关闭，1=开启），失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x0F读取低功耗使能状态

        ==========================================
        Read low power enable status
        Args:
            None

        Returns:
            int | None: Low power enable status (0=off, 1=on), None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read low power enable status from register address 0x0F
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x0F读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x0F, 1, False)[0]
        except Exception:
            return None

    def write_low_power_enable(self, enable: int) -> bool:
        """
        写入低功耗使能状态
        Args:
            enable (int): 要设置的低功耗使能状态（0=关闭，1=开启）

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            ValueError: 当enable不在[0,1]中时抛出

        Notes:
            向寄存器地址0x0F写入低功耗使能状态

        ==========================================
        Write low power enable status
        Args:
            enable (int): Low power enable status to set (0=off, 1=on)

        Returns:
            bool: True if set successfully, False otherwise

        Raises:
            ValueError: Raised when enable is not in [0,1]

        Notes:
            Write low power enable status to register address 0x0F
        """
        # 校验参数合法性
        if enable is None:
            raise ValueError("enable cannot be None")
        if enable not in [0, 1]:
            raise ValueError(f"Invalid enable: {enable}, must be 0 or 1")
        # 唤醒传感器
        self.wake_up()
        try:
            # 向寄存器地址0x0F写入低功耗使能状态
            self.host.write_single_register(self.slave_addr, 0x0F, enable)
            return True
        except Exception:
            return False

    # 0x0017 硬件版本号 只读（高8位主版本，低8位次版本）
    def read_hw_version(self) -> str | None:
        """
        读取硬件版本号
        Args:
            None

        Returns:
            str | None: 硬件版本号字符串（格式：主版本.次版本），失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x17读取硬件版本，高8位为主版本，低8位为次版本

        ==========================================
        Read hardware version
        Args:
            None

        Returns:
            str | None: Hardware version string (format: major.minor), None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read hardware version from register address 0x17, high 8 bits are major version, low 8 bits are minor version
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x17读取1个寄存器的数据
            raw = self.host.read_holding_registers(self.slave_addr, 0x17, 1, False)[0]
            # 提取高8位主版本
            main_ver = (raw >> 8) & 0xFF
            # 提取低8位次版本
            sub_ver = raw & 0xFF
            # 返回版本号字符串
            return f"{main_ver}.{sub_ver}"
        except Exception:
            return None

    # 0x0018 固件版本号 只读（高8位主版本，低8位次版本）
    def read_fw_version(self) -> str | None:
        """
        读取固件版本号
        Args:
            None

        Returns:
            str | None: 固件版本号字符串（格式：主版本.次版本），失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x18读取固件版本，高8位为主版本，低8位为次版本

        ==========================================
        Read firmware version
        Args:
            None

        Returns:
            str | None: Firmware version string (format: major.minor), None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read firmware version from register address 0x18, high 8 bits are major version, low 8 bits are minor version
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x18读取1个寄存器的数据
            raw = self.host.read_holding_registers(self.slave_addr, 0x18, 1, False)[0]
            # 提取高8位主版本
            main_ver = (raw >> 8) & 0xFF
            # 提取低8位次版本
            sub_ver = raw & 0xFF
            # 返回版本号字符串
            return f"{main_ver}.{sub_ver}"
        except Exception:
            return None

    # 0x0019~0x001E 设备唯一标识符UID 只读（96bit，6个寄存器）
    def read_device_uid(self) -> str | None:
        """
        读取设备唯一标识符
        Args:
            None

        Returns:
            str | None: 设备唯一标识符十六进制字符串（96位，共24个十六进制字符），失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x19到0x1E读取6个寄存器的UID数据

        ==========================================
        Read device unique identifier
        Args:
            None

        Returns:
            str | None: Device unique identifier hex string (96 bits, 24 hex characters), None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read UID data from 6 registers at addresses 0x19 to 0x1E
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x19开始读取6个寄存器的数据
            uid_regs = self.host.read_holding_registers(self.slave_addr, 0x19, 6, False)
            # 将每个寄存器转换为4位十六进制字符串并拼接
            uid_hex = "".join([f"{reg:04X}" for reg in uid_regs])
            return uid_hex
        except Exception:
            return None

    # 0x0026 参考液位1 mm 读写
    def read_ref_level1(self) -> int | None:
        """
        读取参考液位1
        Args:
            None

        Returns:
            int | None: 参考液位1值，单位为毫米，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x26读取参考液位1

        ==========================================
        Read reference level 1
        Args:
            None

        Returns:
            int | None: Reference level 1 value in millimeters, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read reference level 1 from register address 0x26
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x26读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x26, 1, False)[0]
        except Exception:
            return None

    def write_ref_level1(self, level: int) -> bool:
        """
        写入参考液位1
        Args:
            level (int): 要设置的参考液位1，单位为毫米，范围0-65535

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            ValueError: 当level不在0-65535范围内时抛出

        Notes:
            向寄存器地址0x26写入参考液位1

        ==========================================
        Write reference level 1
        Args:
            level (int): Reference level 1 to set in millimeters, range 0-65535

        Returns:
            bool: True if set successfully, False otherwise

        Raises:
            ValueError: Raised when level is not in range 0-65535

        Notes:
            Write reference level 1 to register address 0x26
        """
        # 校验参数合法性
        if level is None:
            raise ValueError("level cannot be None")
        if not (0 <= level <= 65535):
            raise ValueError(f"Invalid level: {level}, must be in range 0-65535")
        # 唤醒传感器
        self.wake_up()
        try:
            # 向寄存器地址0x26写入参考液位1
            self.host.write_single_register(self.slave_addr, 0x26, level)
            return True
        except Exception:
            return False

    # 0x0027 参考液位2 mm 读写
    def read_ref_level2(self) -> int | None:
        """
        读取参考液位2
        Args:
            None

        Returns:
            int | None: 参考液位2值，单位为毫米，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x27读取参考液位2

        ==========================================
        Read reference level 2
        Args:
            None

        Returns:
            int | None: Reference level 2 value in millimeters, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read reference level 2 from register address 0x27
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x27读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x27, 1, False)[0]
        except Exception:
            return None

    def write_ref_level2(self, level: int) -> bool:
        """
        写入参考液位2
        Args:
            level (int): 要设置的参考液位2，单位为毫米，范围0-65535

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            ValueError: 当level不在0-65535范围内时抛出

        Notes:
            向寄存器地址0x27写入参考液位2

        ==========================================
        Write reference level 2
        Args:
            level (int): Reference level 2 to set in millimeters, range 0-65535

        Returns:
            bool: True if set successfully, False otherwise

        Raises:
            ValueError: Raised when level is not in range 0-65535

        Notes:
            Write reference level 2 to register address 0x27
        """
        # 校验参数合法性
        if level is None:
            raise ValueError("level cannot be None")
        if not (0 <= level <= 65535):
            raise ValueError(f"Invalid level: {level}, must be in range 0-65535")
        # 唤醒传感器
        self.wake_up()
        try:
            # 向寄存器地址0x27写入参考液位2
            self.host.write_single_register(self.slave_addr, 0x27, level)
            return True
        except Exception:
            return False

    # 0x0028 参考液位3 mm 读写
    def read_ref_level3(self) -> int | None:
        """
        读取参考液位3
        Args:
            None

        Returns:
            int | None: 参考液位3值，单位为毫米，失败返回None

        Raises:
            None: None异常定义

        Notes:
            从寄存器地址0x28读取参考液位3

        ==========================================
        Read reference level 3
        Args:
            None

        Returns:
            int | None: Reference level 3 value in millimeters, None if failed

        Raises:
            None: No exceptions defined

        Notes:
            Read reference level 3 from register address 0x28
        """
        # 唤醒传感器
        self.wake_up()
        try:
            # 从寄存器地址0x28读取1个寄存器的数据
            return self.host.read_holding_registers(self.slave_addr, 0x28, 1, False)[0]
        except Exception:
            return None

    def write_ref_level3(self, level: int) -> bool:
        """
        写入参考液位3
        Args:
            level (int): 要设置的参考液位3，单位为毫米，范围0-65535

        Returns:
            bool: 设置成功返回True，失败返回False

        Raises:
            ValueError: 当level不在0-65535范围内时抛出

        Notes:
            向寄存器地址0x28写入参考液位3

        ==========================================
        Write reference level 3
        Args:
            level (int): Reference level 3 to set in millimeters, range 0-65535

        Returns:
            bool: True if set successfully, False otherwise

        Raises:
            ValueError: Raised when level is not in range 0-65535

        Notes:
            Write reference level 3 to register address 0x28
        """
        # 校验参数合法性
        if level is None:
            raise ValueError("level cannot be None")
        if not (0 <= level <= 65535):
            raise ValueError(f"Invalid level: {level}, must be in range 0-65535")
        # 唤醒传感器
        self.wake_up()
        try:
            # 向寄存器地址0x28写入参考液位3
            self.host.write_single_register(self.slave_addr, 0x28, level)
            return True
        except Exception:
            return False


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
