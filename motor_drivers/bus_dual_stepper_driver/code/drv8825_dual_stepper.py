# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/10 下午2:30
# @Author  : AI Assistant
# @File    : main.py
# @Description : PCA9685 + DRV8825 双路步进电机驱动（硬件PWM脉冲优化版）
# @License : MIT
__version__ = "0.2.0"
__author__ = "AI Assistant"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

import time

# ======================================== 导入相关模块 =========================================
from pca9685 import PCA9685  # 导入用户提供的PCA9685驱动

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class DRV8825_Dual_Stepper:
    """
    中文简介
    双路步进电机驱动类，通过PCA9685扩展板控制两个DRV8825步进电机驱动模块
    【优化】STEP脉冲由PCA9685硬件PWM生成，无频繁I2C通信
    Attributes:
        MICROSTEP_TABLE (dict): 细分配置表，键为细分数，值为(M0, M1, M2)引脚状态元组
        motor1_pins (dict): 电机1的PCA9685通道映射表
        motor2_pins (dict): 电机2的PCA9685通道映射表
        pca (object): PCA9685对象实例
        motors (dict): 电机引脚配置字典，键为电机编号(1/2)，值为引脚映射字典
        _running (dict): 电机连续运行标志，键为电机编号，值为布尔运行状态

    Methods:
        _write_pin(): 写入PCA9685引脚电平（用于方向/细分/使能等静态引脚）
        _get_motor(): 获取电机配置字典
        set_microstep(): 设置电机细分数
        set_direction(): 设置电机方向
        enable_motor(): 使能电机
        disable_motor(): 禁用电机
        step(): 硬件PWM驱动电机走指定步数（阻塞）
        start_continuous(): 硬件PWM启动电机连续旋转
        stop_continuous(): 停止硬件PWM脉冲输出
        reset_motor(): 复位电机
        sleep_motor(): 让电机进入睡眠模式
        wake_motor(): 唤醒电机

    Notes:
        1. EN引脚低电平有效，高电平时电机处于禁用状态
        2. PCA9685所有通道共享PWM频率，双电机速度必须同步
        3. 最小脉冲延迟默认为1000微秒，可根据电机性能调整
    """

    # 细分配置表
    MICROSTEP_TABLE = {
        1: (0, 0, 0),
        2: (1, 0, 0),
        4: (0, 1, 0),
        8: (1, 1, 0),
        16: (0, 0, 1),
        32: (1, 0, 1),
    }

    # 电机1引脚配置
    motor1_pins = {
        "M0": 0,
        "M1": 1,
        "M2": 2,
        "STEP": 3,
        "DIR": 4,
        "EN": 5,
        "RST": 6,
        "SLP": 7
    }

    # 电机2引脚配置
    motor2_pins = {
        "M0": 8,
        "M1": 9,
        "M2": 10,
        "STEP": 11,
        "DIR": 12,
        "EN": 13,
        "RST": 14,
        "SLP": 15
    }

    def __init__(self, pca9685, motor1_pins: dict = motor1_pins, motor2_pins: dict = motor2_pins):
        """
        初始化双路步进电机驱动类
        Args:
            pca9685 (object): PCA9685对象实例
            motor1_pins (dict): 电机1引脚映射字典
            motor2_pins (dict): 电机2引脚映射字典
        """
        self.pca = pca9685
        self.motors = {
            1: motor1_pins,
            2: motor2_pins
        }
        self._running = {1: False, 2: False}  # 连续运行标志
        
        # 初始化默认状态
        for m in (1, 2):
            self.disable_motor(m)
            self.set_microstep(m, 1)

    # ==================== 基础IO控制 ====================
    def _write_pin(self, ch: int, val: int) -> None:
        """静态引脚电平控制（DIR/M0/M1/M2/EN等），沿用duty方法"""
        self.pca.duty(ch, 4095 if val else 0)

    def _get_motor(self, motor: int):
        """获取电机配置"""
        return self.motors.get(motor, None)

    # ==================== 功能接口 ====================
    def set_microstep(self, motor: int, mode: int) -> bool:
        """设置细分数（无修改）"""
        m = self._get_motor(motor)
        if m is None or mode not in self.MICROSTEP_TABLE:
            return False

        m0, m1, m2 = self.MICROSTEP_TABLE[mode]
        self._write_pin(m['M0'], m0)
        self._write_pin(m['M1'], m1)
        self._write_pin(m['M2'], m2)
        return True

    def set_direction(self, motor: int, dir: int) -> bool:
        """设置方向（无修改）"""
        m = self._get_motor(motor)
        if m is None:
            return False
        self._write_pin(m['DIR'], 1 if dir else 0)
        return True

    def enable_motor(self, motor: int) -> bool:
        """使能电机（无修改）"""
        m = self._get_motor(motor)
        if m is None:
            return False
        self._write_pin(m['EN'], 0)
        self._write_pin(m['SLP'], 1)
        self._write_pin(m['RST'], 1)
        return True

    def disable_motor(self, motor: int) -> bool:
        """禁用电机（无修改）"""
        m = self._get_motor(motor)
        if m is None:
            return False
        self._write_pin(m['EN'], 1)
        return True

    # ==================== 核心优化：硬件PWM脉冲 ====================
    def _start_step_pwm(self, step_ch: int, delay_us: int) -> None:
        """启动STEP通道硬件PWM输出（50%占空比方波）"""
        # 计算PWM频率：周期=2*delay_us(高+低)，频率=1e6/周期
        freq = 1000000 / (2 * delay_us)
        self.pca.freq(freq)
        # 50%占空比 = 2048，硬件自动生成脉冲
        self.pca.pwm(step_ch, 0, 2048)

    def _stop_step_pwm(self, step_ch: int) -> None:
        """停止STEP通道PWM输出（拉低电平）"""
        self.pca.pwm(step_ch, 0, 4096)

    def step(self, motor: int, steps: int, delay_us: int = 1000) -> bool:
        """
        【优化】硬件PWM驱动电机走指定步数（仅2次I2C通信）
        Args:
            motor: 电机编号
            steps: 步数（正负代表方向）
            delay_us: 脉冲间隔微秒
        """
        m = self._get_motor(motor)
        if m is None or steps == 0:
            return False

        # 1. 设置旋转方向
        direction = 0 if steps > 0 else 1
        self.set_direction(motor, direction)
        steps = abs(steps)
        step_ch = m["STEP"]

        # 2. 使能电机 + 启动硬件PWM
        self.enable_motor(motor)
        self._start_step_pwm(step_ch, delay_us)

        # 3. 纯软件计数脉冲（无I2C，仅计时）
        pulse_period = 2 * delay_us  # 单个脉冲总时长
        total_time = steps * pulse_period
        time.sleep_us(total_time)

        # 4. 停止PWM + 完成
        self._stop_step_pwm(step_ch)
        return True

    def start_continuous(self, motor: int, dir: int, delay_us: int = 1000) -> bool:
        """【优化】硬件PWM连续旋转（无阻塞软件循环）"""
        m = self._get_motor(motor)
        if m is None:
            return False

        # 【修复1】强制复位+唤醒电机，确保DRV8825工作
        self.reset_motor(motor)
        time.sleep_ms(5)
        self.wake_motor(motor)
        time.sleep_ms(5)
        
        # 设置方向 + 完全使能电机
        self.set_direction(motor, dir)
        self.enable_motor(motor)
        
        # 【修复2】启动硬件PWM脉冲
        self._start_step_pwm(m["STEP"], delay_us)
        self._running[motor] = True
        return True

    def stop_continuous(self, motor: int) -> bool:
        """【优化】停止硬件PWM输出"""
        m = self._get_motor(motor)
        if m is None:
            return False

        self._stop_step_pwm(m["STEP"])
        self._running[motor] = False
        return True

    # ==================== 辅助功能（无修改） ====================
    def reset_motor(self, motor: int) -> bool:
        m = self._get_motor(motor)
        if m is None:
            return False
        self._write_pin(m['RST'], 0)
        time.sleep_ms(10)
        self._write_pin(m['RST'], 1)
        return True

    def sleep_motor(self, motor: int) -> bool:
        m = self._get_motor(motor)
        if m is None:
            return False
        self._write_pin(m['SLP'], 0)
        return True

    def wake_motor(self, motor: int) -> bool:
        m = self._get_motor(motor)
        if m is None:
            return False
        self._write_pin(m['SLP'], 1)
        return True


# ======================================== 初始化配置 ===========================================
# 示例初始化（根据你的硬件I2C引脚修改）
from machine import I2C, Pin
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
pca = PCA9685(i2c)
motor_driver = DRV8825_Dual_Stepper(pca)

# ========================================  主程序  ============================================
# 示例用法
if __name__ == "__main__":
    # 测试1：step 阻塞运行（你已经验证可用）
    print("测试定长步数...")
    motor_driver.step(2, 200, 2000)
    time.sleep(1)

    # 测试2：连续旋转（核心：主线程必须保持运行！）
    print("测试连续旋转...")
    motor_driver.start_continuous(1, 0, 2000)  # 正转
    time.sleep(3)  # 让电机转3秒钟！！！这行是关键

    # 停止电机
    motor_driver.stop_continuous(1)
    motor_driver.disable_motor(1)
    print("停止旋转")

