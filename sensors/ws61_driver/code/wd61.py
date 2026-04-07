# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午4:00
# @Author  : hogeiha
# @File    : main.py
# @Description : 敏源WS61水浸传感器Modbus RTU驱动（无壳模组专用，严格匹配寄存器表V1.0）
# @License : MIT

__version__ = "1.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from umodbus.serial import Serial as ModbusRTUMaster

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class WS61Water:
    """
    敏源WS61电容式非接触水浸传感器 Modbus RTU 驱动类
    适配无壳模组，严格匹配官方寄存器表V1.0，自动处理低功耗唤醒、数据缩放与类型转换

    Attributes:
        slave_addr (int): Modbus 从机地址（默认1）
        baudrate (int): 串口波特率（固定9600）
        uart_id (int): UART 编号
        tx_pin (int): TX 引脚编号
        rx_pin (int): RX 引脚编号
        host (ModbusRTUMaster): Modbus RTU 主机实例

    Methods:
        wake_up(): 低功耗传感器唤醒（所有通信前必须调用）
        read_device_id(): 读取设备ID
        write_device_id(): 写入设备ID
        read_485_node_address(): 读取485节点地址
        read_capacitance(): 读取实时电容值(pF)
        read_temperature(): 读取环境温度(℃)
        read_water_status(): 读取水浸报警状态
        read_alarm_threshold(): 读取水浸报警电容阈值(pF)
        write_alarm_threshold(): 设置水浸报警电容阈值(pF)
        read_release_threshold(): 读取水浸解除报警电容阈值(pF)
        write_release_threshold(): 设置水浸解除报警电容阈值(pF)
        calibrate_sensor(): 执行空载校准

    Notes:
        1. WS61为低功耗设备，每次通信前自动调用 wake_up()
        2. 电容值缩放系数 ×1000，温度缩放系数 ×10
        3. 水浸状态：0=无水，1=有水报警
        4. 严格匹配寄存器表V1.0（202506-V1.0）

    ==========================================
    English description
    Attributes:
        slave_addr (int): Modbus slave address (default 1)
        baudrate (int): Serial baud rate (fixed 9600)
        uart_id (int): UART ID
        tx_pin (int): TX pin number
        rx_pin (int): RX pin number
        host (ModbusRTUMaster): Modbus RTU master instance

    Methods:
        wake_up(): Wake up low-power sensor (must be called before any communication)
        read_device_id(): Read device ID
        write_device_id(): Write device ID
        read_485_node_address(): Read 485 node address
        read_capacitance(): Read real-time capacitance (pF)
        read_temperature(): Read ambient temperature (℃)
        read_water_status(): Read water alarm status
        read_alarm_threshold(): Read water alarm capacitance threshold (pF)
        write_alarm_threshold(): Set water alarm capacitance threshold (pF)
        read_release_threshold(): Read water release alarm capacitance threshold (pF)
        write_release_threshold(): Set water release alarm capacitance threshold (pF)
        calibrate_sensor(): Perform no-load calibration

    Notes:
        1. WS61 is low-power, wake_up() is automatically called before each communication
        2. Capacitance scaling factor ×1000, temperature scaling factor ×10
        3. Water status: 0=dry, 1=water alarm
        4. Strictly matches register table V1.0 (202506-V1.0)
    """

    def __init__(self, slave_addr: int, uart_id: int, tx_pin: int, rx_pin: int) -> None:
        """
        初始化 Modbus 主机，WS61 固定波特率 9600，8N1

        Args:
            slave_addr (int): Modbus 从机地址
            uart_id (int): UART 编号
            tx_pin (int): TX 引脚
            rx_pin (int): RX 引脚

        ==========================================
        English description
        Args:
            slave_addr (int): Modbus slave address
            uart_id (int): UART ID
            tx_pin (int): TX pin
            rx_pin (int): RX pin
        """
        self.slave_addr = slave_addr
        self.baudrate = 9600  # WS61固定波特率
        self.uart_id = uart_id
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin

        # 初始化Modbus RTU主机（严格匹配WS61协议）
        self.host = ModbusRTUMaster(
            pins=(self.tx_pin, self.rx_pin), baudrate=self.baudrate, data_bits=8, stop_bits=1, parity=None, uart_id=self.uart_id
        )

    def wake_up(self) -> bool:
        """
        低功耗唤醒：发送 0x8F 指令，等待 30ms
        【WS61核心必备】所有通信前自动调用

        Returns:
            bool: 唤醒成功返回 True，失败返回 False

        ==========================================
        English description
        Wake up low-power sensor: send 0x8F command, wait 30ms
        [Essential for WS61] Automatically called before any communication

        Returns:
            bool: True if wake-up succeeded, False otherwise
        """
        try:
            # 发送唤醒指令
            self.host._uart.write(b"\x8F")
            time.sleep_ms(30)  # 官方要求≥30ms
            return True
        except:
            return False

    # 0x0001 设备ID（读写 1~252）
    def read_device_id(self) -> int | None:
        """
        读取设备 ID（寄存器 0x0001）

        Returns:
            int | None: 成功返回设备 ID(1-252)，失败返回 None

        ==========================================
        English description
        Read device ID (register 0x0001)

        Returns:
            int | None: Device ID (1-252) if successful, None otherwise
        """
        self.wake_up()
        try:
            return self.host.read_holding_registers(self.slave_addr, 0x01, 1, False)[0]
        except:
            return None

    def write_device_id(self, dev_id: int) -> bool:
        """
        写入设备 ID（寄存器 0x0001）

        Args:
            dev_id (int): 设备 ID，范围 1-252

        Returns:
            bool: 成功返回 True，失败返回 False

        ==========================================
        English description
        Write device ID (register 0x0001)

        Args:
            dev_id (int): Device ID, range 1-252

        Returns:
            bool: True if successful, False otherwise
        """
        self.wake_up()
        try:
            if 1 <= dev_id <= 252:
                self.host.write_single_register(self.slave_addr, 0x01, dev_id)
                return True
            return False
        except:
            return False

    # 0x0002 485节点地址（只读 1~252）
    def read_485_node_address(self) -> int | None:
        """
        读取 485 节点地址（寄存器 0x0002）

        Returns:
            int | None: 成功返回节点地址(1-252)，失败返回 None

        ==========================================
        English description
        Read 485 node address (register 0x0002)

        Returns:
            int | None: Node address (1-252) if successful, None otherwise
        """
        self.wake_up()
        try:
            return self.host.read_holding_registers(self.slave_addr, 0x02, 1, False)[0]
        except:
            return None

    # 0x0012 实时电容值（只读 ×1000pF）
    def read_capacitance(self) -> float | None:
        """
        读取实时电容值（寄存器 0x0012，原始值 ×1000）

        Returns:
            float | None: 成功返回电容值(pF)，精度 0.001pF，失败返回 None

        ==========================================
        English description
        Read real-time capacitance (register 0x0012, raw value ×1000)

        Returns:
            float | None: Capacitance in pF with 0.001pF resolution if successful, None otherwise
        """
        self.wake_up()
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x12, 1, False)[0]
            return round(raw / 1000.0, 3)
        except:
            return None

    # 0x0013 温度值（只读 ×10℃，无符号）
    def read_temperature(self) -> float | None:
        """
        读取环境温度（寄存器 0x0013，原始值 ×10）

        Returns:
            float | None: 成功返回温度(℃)，精度 0.1℃，失败返回 None

        ==========================================
        English description
        Read ambient temperature (register 0x0013, raw value ×10)

        Returns:
            float | None: Temperature in ℃ with 0.1℃ resolution if successful, None otherwise
        """
        self.wake_up()
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x13, 1, False)[0]
            return round(raw / 10.0, 1)
        except:
            return None

    # 0x0014 水浸报警状态（只读 0=无水，1=有水）
    def read_water_status(self) -> int | None:
        """
        读取水浸报警状态（寄存器 0x0014）

        Returns:
            int | None: 成功返回 0(无水)/1(有水报警)，失败返回 None

        ==========================================
        English description
        Read water alarm status (register 0x0014)

        Returns:
            int | None: 0 (dry) / 1 (water alarm) if successful, None otherwise
        """
        self.wake_up()
        try:
            return self.host.read_holding_registers(self.slave_addr, 0x14, 1, False)[0]
        except:
            return None

    # 0x0003 水浸报警电容阈值（读写 ×1000pF）
    def read_alarm_threshold(self) -> float | None:
        """
        读取水浸报警电容阈值（寄存器 0x0003，原始值 ×1000）

        Returns:
            float | None: 成功返回阈值(pF)，精度 0.001pF，失败返回 None

        ==========================================
        English description
        Read water alarm capacitance threshold (register 0x0003, raw value ×1000)

        Returns:
            float | None: Threshold in pF with 0.001pF resolution if successful, None otherwise
        """
        self.wake_up()
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x03, 1, False)[0]
            return round(raw / 1000.0, 3)
        except:
            return None

    def write_alarm_threshold(self, threshold: float) -> bool:
        """
        设置水浸报警电容阈值（寄存器 0x0003）

        Args:
            threshold (float): 报警阈值（单位 pF，范围 0~65.535pF）

        Returns:
            bool: 成功返回 True，失败返回 False

        ==========================================
        English description
        Set water alarm capacitance threshold (register 0x0003)

        Args:
            threshold (float): Alarm threshold in pF, range 0~65.535

        Returns:
            bool: True if successful, False otherwise
        """
        self.wake_up()
        try:
            raw_val = int(threshold * 1000)
            if 0 <= raw_val <= 65535:
                self.host.write_single_register(self.slave_addr, 0x03, raw_val)
                return True
            return False
        except:
            return False

    # 0x0004 水浸解除报警电容阈值（读写 ×1000pF）
    def read_release_threshold(self) -> float | None:
        """
        读取水浸解除报警电容阈值（寄存器 0x0004，原始值 ×1000）

        Returns:
            float | None: 成功返回阈值(pF)，精度 0.001pF，失败返回 None

        ==========================================
        English description
        Read water release alarm capacitance threshold (register 0x0004, raw value ×1000)

        Returns:
            float | None: Threshold in pF with 0.001pF resolution if successful, None otherwise
        """
        self.wake_up()
        try:
            raw = self.host.read_holding_registers(self.slave_addr, 0x04, 1, False)[0]
            return round(raw / 1000.0, 3)
        except:
            return None

    def write_release_threshold(self, threshold: float) -> bool:
        """
        设置水浸解除报警电容阈值（寄存器 0x0004）

        Args:
            threshold (float): 解除阈值（单位 pF，范围 0~65.535pF）

        Returns:
            bool: 成功返回 True，失败返回 False

        ==========================================
        English description
        Set water release alarm capacitance threshold (register 0x0004)

        Args:
            threshold (float): Release threshold in pF, range 0~65.535

        Returns:
            bool: True if successful, False otherwise
        """
        self.wake_up()
        try:
            raw_val = int(threshold * 1000)
            if 0 <= raw_val <= 65535:
                self.host.write_single_register(self.slave_addr, 0x04, raw_val)
                return True
            return False
        except:
            return False

    # 0x0007 空载校准（读写，写入1执行校准）
    def calibrate_sensor(self) -> bool:
        """
        执行空载校准（寄存器 0x0007，写入 1 触发）
        需在传感器无水、无遮挡、安装完成后执行

        Returns:
            bool: 成功返回 True，失败返回 False

        ==========================================
        English description
        Perform no-load calibration (register 0x0007, write 1 to trigger)
        Must be executed when sensor is dry, unobstructed, and properly installed

        Returns:
            bool: True if successful, False otherwise
        """
        self.wake_up()
        try:
            self.host.write_single_register(self.slave_addr, 0x07, 1)
            time.sleep_ms(500)  # 校准等待时间
            return True
        except:
            return False


# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================
