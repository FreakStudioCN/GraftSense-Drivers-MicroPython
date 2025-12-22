# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午2:21
# @Author  : leeqingshui
# @File    : jedm_gas_meas.py
# @Description : JED系列MEMS数字传感器模块的驱动代码

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入硬件相关模块
from machine import SoftI2C, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class JEDMGasMeas:
    """
    JEDM气体传感器操作类
    支持读取气体浓度和校零校准功能，基于SoftI2C通信
    """
    # 固定的命令寄存器地址（类属性）
    # 读取气体浓度的命令字
    READ_CMD: int = 0xA1
    # 校零校准的命令字
    CALIBRATE_CMD: int = 0x32
    # 类常量：I2C最大允许通信速率（100KHz）
    MAX_I2C_FREQ: int = 100000
    # 类常量：校准值的范围（16位无符号整数）
    CALIB_MIN: int = 0
    CALIB_MAX: int = 65535  # 2^16 - 1

    def __init__(self, i2c: SoftI2C, addr: int = 0x2A) -> None:
        """
        初始化方法
        :param i2c: SoftI2C实例（MicroPython的软I2C对象）
        :param addr: 传感器7位基础地址（不带读写位），默认0x2A
        """
        # 保存I2C实例和基础地址
        self.i2c: SoftI2C = i2c
        # 7位基础地址（私有属性）
        self._addr_7bit: int = addr

    def read_concentration(self) -> int:
        """
        读取气体浓度值（遵循传感器的I2C读取时序，使用标准I2C方法）
        :return: 16位气体浓度值（高位*256 + 低位），读取失败返回0
        """
        try:
            # 第一步：发送写操作（7位地址），写入读取命令，stop=False表示不发送停止位（实现重复起始）
            # writeto返回收到的ACK数量，需等于发送的字节数（这里是1个字节：READ_CMD）
            ack_count = self.i2c.writeto(self._addr_7bit, bytes([JEDMGasMeas.READ_CMD]), stop=False)
            if ack_count != 1:
                raise OSError("No ACK for read command")

            # 第二步：发送读操作（7位地址），读取2个字节的浓度数据（高位+低位），stop=True发送停止位
            data = self.i2c.readfrom(self._addr_7bit, 2)
            if len(data) != 2:
                raise OSError("Incomplete data received")

            # 计算16位浓度值（高位左移8位 + 低位）
            concentration = (data[0] << 8) | data[1]
            return concentration
        except OSError as e:
            print(f"Failed to read concentration: {str(e)}")
            return 0

    def calibrate_zero(self, calib_value: int | None = None) -> bool:
        """
        传感器校零校准方法
        :param calib_value: 校准值（16位整数），为None时使用当前读取的浓度值作为校准值
        :return: 校准是否成功（True/False）
        """
        # 若校准值超过0~65535，需要抛出异常
        if calib_value > JEDMGasMeas.CALIB_MAX or calib_value < JEDMGasMeas.CALIB_MIN:
            raise ValueError("Calibration value must be between 0 and 65535")

        # 若未指定校准值，先读取当前浓度作为校准值
        if calib_value is None:
            calib_value = self.read_concentration()

        # 将16位校准值拆分为高8位和低8位（确保在0-255范围内）
        high_byte: int = (calib_value >> 8) & 0xFF
        low_byte: int = calib_value & 0xFF

        try:
            # 发送写操作，写入校零命令+校准值高低字节，stop=True发送停止位
            # 发送的字节序列：[校零命令, 高位字节, 低位字节]
            ack_count = self.i2c.writeto(
                self._addr_7bit,
                bytes([JEDMGasMeas.CALIBRATE_CMD, high_byte, low_byte])
            )
            # 检查ACK数量，需等于发送的字节数（3个字节）
            if ack_count != 3:
                raise OSError("No ACK for calibrate command or data")

            # 写入后，读取一次浓度值，确认校零成功（判断读取结果是否为0）
            post_calib_value = self.read_concentration()
            if post_calib_value != 0:
                print(f"Calibration confirmation failed: Read value {post_calib_value} is not 0")
                return False

            return True

        except OSError as e:
            print(f"Failed to calibrate zero: {str(e)}")
            return False

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================