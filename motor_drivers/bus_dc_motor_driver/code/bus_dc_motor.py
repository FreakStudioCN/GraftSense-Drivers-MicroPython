# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/1/16 上午11:14   
# @Author  : 李清水            
# @File    : bus_dc_motor.py
# @Description : 总线直流电机驱动模块，使用PCA9685芯片控制电机驱动芯片
# 本修改部分由 [leeqingshui] 发布，使用 CC BY-NC 4.0 许可证

# ======================================== 导入相关模块 =========================================

# 导入PCA9685模块
from pca9685 import PCA9685

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义总线直流电机驱动类
class BusDCMotor:
    """
    BusDCMotor类，用于控制直流电机的正转、反转和调速。

    该类通过与PCA9685的接口交互，使用PWM信号控制四个电机的速度和转向。

    Attributes:
        pca9685 (PCA9685): 用于控制PWM信号的PCA9685实例。
        motor_count (int): 电机数量，这里假设最多控制4个电机。

    Methods:
        set_motor_speed(motor_id: int, speed: int, direction: int = 0) -> None:
            设置指定编号电机的速度和转向。
        stop_motor(motor_id: int) -> None:
            停止指定编号电机的转动。
        break_motor(motor_id: int) -> None:
            快速刹车，停止指定编号电机。

        stop_motor 方法通过设置PWM为0平稳停止电机，break_motor 方法通过设置PWM为最大值快速刹车电机。

    =============================================

    BusDCMotor class for controlling the direction and speed of DC motors.

    This class communicates with the PCA9685 to control the speed and direction of up to four motors via PWM signals.

    Attributes:
        pca9685 (PCA9685): The PCA9685 instance for controlling PWM signals.
        motor_count (int): Number of motors to control, assuming up to 4 motors.

    Methods:
        set_motor_speed(motor_id: int, speed: int, direction: int = 0) -> None:
            Set the speed and direction of the specified motor.
        stop_motor(motor_id: int) -> None:
            Stop the specified motor.
        break_motor(motor_id: int) -> None:
            Brake the specified motor.

        The stop_motor method smoothly stops the motor by setting PWM to 0, while the break_motor method quickly brakes the motor by setting PWM to the maximum value.
    """

    def __init__(self, pca9685: PCA9685, motor_count: int = 4):
        """
        构造函数，初始化电机控制类。

        Args:
            pca9685 (PCA9685): PCA9685实例，用于控制PWM信号。
            motor_count (int): 需要控制的电机数量。默认值为4个电机。

        Raises:
            ValueError: 如果电机数量超出范围（1-4）或传入的pca9685不是PCA9685实例。

        ============================================

        Constructor to initialize the motor control class.

        Args:
            pca9685 (PCA9685): PCA9685 instance to control PWM signals.
            motor_count (int): Number of motors to control. Default is 4 motors.

        Raise:
            ValueError: If motor count is out of range (1-4) or pca9685 is not an instance of PCA9685.
        """
        # 电机数量不可能大于4个
        if motor_count > 4 or motor_count < 1:
            raise ValueError(f"Invalid motor_count: {motor_count}. Motor count must be between 1 and 4.")

        # 判断pca9685是否为PCA9685实例
        if not isinstance(pca9685, PCA9685):
            raise ValueError("Invalid pca9685. pca9685 must be an instance of PCA9685.")

        self.pca9685 = pca9685
        self.motor_count = motor_count

        # 设定PWM信号频率为1000Hz
        self.pca9685.freq(1000)
        # 设定pca9685实例的8个PWM引脚占空比为4095，即刹车
        for i in range(8):
            self.pca9685.duty(i, 4095)

    def set_motor_speed(self, motor_id: int, speed: int, direction: int = 0) -> None:
        """
        设置指定编号电机的速度和转向。

        根据电机编号和方向，调整对应PWM引脚的占空比，以控制电机的转动方向和速度。

        Args:
            motor_id (int): 电机的编号（1至4）。
            speed (int): 电机的速度，占空比范围为1900到4095。
                         在5V供电的PWM控制芯片中，速度设置为1900时，PWM通道输出约为2.3V。
                         大多数电机驱动芯片的逻辑高电平约为2.2V，因此将速度设置为1900可以确保PWM信号满足电机驱动芯片的输入要求。
            direction (int, optional): 电机转向，0表示前进，1表示后退。默认为0（前进）。

        Raises:
            ValueError: 如果电机编号超出范围（1-4）或者速度值超出范围（1900-4095）。

        =============================================

        Set the speed and direction of the specified motor.

        Adjust the PWM duty cycle of the corresponding pins based on motor ID and direction to control the motor's rotation direction and speed.

        Args:
            motor_id (int): Motor ID (1 to 4).
            speed (int): Motor speed, PWM duty cycle range from 1900 to 4095.
                         In a PWM control chip with 5V supply, a speed of 1900 corresponds to a PWM channel output of about 2.3V.
                         Most motor driver chips have a logic high voltage of about 2.2V, so setting the speed to 1900 ensures that the PWM signal meets the input requirements of the motor driver chip.
            direction (int, optional): Motor direction, 0 for forward and 1 for backward. Default is 0 (forward).

        Raises:
            ValueError: If motor ID is out of range (1-4) or speed is out of range (1900-4095).
        """
        if motor_id < 1 or motor_id > self.motor_count:
            raise ValueError(f"Invalid motor_id: {motor_id}. Motor ID must be between 1 and {self.motor_count}.")

        if not 1900 <= speed <= 4095:
            raise ValueError(f"Invalid speed: {speed}. Speed must be between 1900 and 4095.")

        # 根据电机编号选择对应的PWM引脚
        pwm_index = (motor_id - 1) * 2

        # 设置前进（direction = 0）或后退（direction = 1）的方向
        if direction == 0:
            # 控制前进，FI引脚
            self.pca9685.duty(pwm_index, speed)
            print(pwm_index, speed)
            # 设置后退BI引脚为0
            self.pca9685.duty(pwm_index + 1, 0)
            print(pwm_index + 1, 0)
        elif direction == 1:
            # 控制后退，BI引脚
            self.pca9685.duty(pwm_index + 1, speed)
            print(pwm_index + 1, speed)
            # 设置前进FI引脚为0
            self.pca9685.duty(pwm_index, 0)
            print(pwm_index, 0)
        else:
            raise ValueError("Invalid direction. Use 0 for forward or 1 for backward.")

    def stop_motor(self, motor_id: int) -> None:
        """
        停止指定编号电机的转动，设置PWM信号为0。
        平稳的停止，设置一个电机通道的两个PWM引脚为低电平。

        Args:
            motor_id (int): 电机的编号（1至4）。

        Raise:
            ValueError: 如果电机编号超出范围（1-4）。

        =============================================

        Stop the motor with the specified ID by setting the PWM duty cycle to 0.
        To perform a smooth stop, set both PWM pins of the motor channel to low.

        Args:
            motor_id (int): Motor ID (1 to 4).

        Raise:
            ValueError: If motor ID is out of range (1-4).
        """
        if motor_id < 1 or motor_id > self.motor_count:
            raise ValueError(f"Invalid motor_id: {motor_id}. Motor ID must be between 1 and {self.motor_count}.")

        # 根据电机编号选择对应的PWM引脚
        pwm_index = (motor_id - 1) * 2

        # 将电机的两个方向引脚都设置为0，停止电机
        self.pca9685.duty(pwm_index, 0)
        self.pca9685.duty(pwm_index + 1, 0)

    def break_motor(self, motor_id: int) -> None:
        """
        刹车指定编号电机，设置PWM信号为最大占空比。
        快速刹车，设置一个电机通道的两个PWM引脚为最大占空比。

        Args:
            motor_id (int): 电机的编号（1至4）。

        Raise:
            ValueError: 如果电机编号超出范围（1-4）。

        =============================================

        Brake the motor with the specified ID by setting the PWM duty cycle to maximum.
        To perform a quick brake, set both PWM pins of the motor channel to maximum duty cycle.

        Args:
            motor_id (int): Motor ID (1 to 4).

        Raise:
            ValueError: If motor ID is out of range (1-4).
        """
        if motor_id < 1 or motor_id > self.motor_count:
            raise ValueError(f"Invalid motor_id: {motor_id}. Motor ID must be between 1 and {self.motor_count}.")

        # 根据电机编号选择对应的PWM引脚
        pwm_index = (motor_id - 1) * 2

        # 将电机的两个方向引脚都设置为最大占空比，进行刹车
        self.pca9685.duty(pwm_index, 4095)
        self.pca9685.duty(pwm_index + 1, 4095)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================