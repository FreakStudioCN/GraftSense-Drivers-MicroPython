# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/1/16 上午11:35   
# @Author  : 李清水            
# @File    : bus_step_motor.py       
# @Description : 总线步进电机驱动模块，使用PCA9685芯片控制电机驱动芯片
# 本修改部分由 [leeqingshui] 发布，使用 CC BY-NC 4.0 许可证

# ======================================== 导入相关模块 =========================================

# 导入PCA9685模块
from pca9685 import PCA9685
# 导入硬件相关模块
from machine import Timer
# 导入MicroPython相关模块
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义总线步进电机驱动类
class BusStepMotor:
    """
    通过PCA9685芯片控制步进电机，支持多电机独立控制，能够实现步进电机的正反转、持续运动及定步运动控制，支持单相、双相、半步驱动模式。

    Class Variables:
        DRIVER_MODE_SINGLE (int): 单相驱动模式的常量值。
        DRIVER_MODE_DOUBLE (int): 双相驱动模式的常量值。
        DRIVER_MODE_HALF_STEP (int): 半步驱动模式的常量值。
        FORWARD (int): 步进电机的正转方向常量值。
        BACKWARD (int): 步进电机的反转方向常量值。
        PHASES (dict): 一个字典，包含不同驱动模式下的相位序列。

    Attributes:
        pca9685 (PCA9685): 控制PWM信号输出的PCA9685芯片实例。
        motor_count (int): 控制的步进电机数量，最大为4个。
        timers (list): 存储每个电机定时器的列表。
        steps (list): 存储每个电机目标步数的列表。
        step_counters (list): 存储每个电机当前步数的计数器列表。
        directions (list): 存储每个电机的运动方向（正转或反转）。
        driver_modes (list): 存储每个电机的驱动模式（单相、双相或半步驱动）。
        speeds (list): 存储每个电机的转速（控制驱动器输出脉冲的频率）。

    Methods:
        __init__(pca9685: PCA9685, motor_count: int = 2): 构造函数，初始化电机控制类。
        _next_step(motor_id: int): 计算并更新指定电机的步进状态。
        _start_timer(motor_id: int, speed: int): 启动定时器并设置回调函数，以控制电机连续运动。
        _stop_timer(motor_id: int): 停止指定电机的定时器，停止运动。
        start_continuous_motion(motor_id: int, direction: int, driver_mode: int, speed: int): 启动电机进行连续运动。
        stop_continuous_motion(motor_id: int): 停止电机的连续运动。
        start_step_motion(motor_id: int, direction: int, driver_mode: int, speed: int, steps: int): 启动步进电机的定步运动，按照指定步数执行。

    ===========================================
    Using the PCA9685 chip to control stepper motors, it supports independent control of multiple motors,
    enabling forward and reverse rotation, continuous motion, and step-by-step movement.
    It supports single-phase, dual-phase, and half-step driving modes.

    Class Variables:
        DRIVER_MODE_SINGLE (int): Constant value for single-phase driver mode.
        DRIVER_MODE_DOUBLE (int): Constant value for double-phase driver mode.
        DRIVER_MODE_HALF_STEP (int): Constant value for half-step driver mode.
        FORWARD (int): Constant value for forward direction.
        BACKWARD (int): Constant value for reverse direction.
        PHASES (dict): A dictionary containing the phase sequence for different driver modes.

    Attributes:
        pca9685 (PCA9685): PCA9685 instance for controlling PWM signals.
        motor_count (int): Number of motors to control. Default value is 2.
        timers (list): List of timers for each motor.
        steps (list): List of total steps for each motor.
        step_counters (list): List of step counters for each motor.
        directions (list): List of motor directions (forward or reverse).
        driver_modes (list): List of motor driver modes (single-phase, double-phase, or half-step).
        speeds (list): List of motor speeds (controls the frequency of the output pulses from the driver).

    Methods:
        __init__(pca9685: PCA9685, motor_count: int = 2): Constructor to initialize the motor control class.
        _next_step(motor_id: int): Calculates and updates the step state of the specified motor.
        _start_timer(motor_id: int, speed: int): Starts the timer and sets the callback function to control the motor's continuous motion.
        _stop_timer(motor_id: int): Stops the timer for the specified motor and stops the motion.
        start_continuous_motion(motor_id: int, direction: int, driver_mode: int, speed: int): Starts the motor for continuous motion.
        stop_continuous_motion(motor_id: int): Stops the continuous motion of the specified motor.
        start_step_motion(motor_id: int, direction: int, driver_mode: int, speed: int, steps: int): Starts the stepwise motion of the specified motor, executing according to the specified steps.
    """

    # 步进电机驱动模式：单相、双相、半步驱动
    DRIVER_MODE_SINGLE, DRIVER_MODE_DOUBLE, DRIVER_MODE_HALF_STEP = (0,1,2)
    # 步进电机方向：正转、反转
    FORWARD, BACKWARD = (0,1)

    # 不同驱动模式的相位序列
    PHASES = {
        DRIVER_MODE_SINGLE: [
            [1, 0, 0, 0],  # 步进1：A+
            [0, 1, 0, 0],  # 步进2：A-
            [0, 0, 1, 0],  # 步进3：B+
            [0, 0, 0, 1],  # 步进4：B-
        ],
        DRIVER_MODE_DOUBLE: [
            [1, 1, 0, 0],  # 步进1：A+ 和 A-
            [0, 1, 1, 0],  # 步进2：A- 和 B+
            [0, 0, 1, 1],  # 步进3：B+ 和 B-
            [1, 0, 0, 1],  # 步进4：A+ 和 B-
        ],
        DRIVER_MODE_HALF_STEP: [
            [1, 0, 0, 0],  # 步进1：A+
            [1, 1, 0, 0],  # 步进2：A+ 和 B+
            [0, 1, 0, 0],  # 步进3：B+
            [0, 1, 1, 0],  # 步进4：B+ 和 B-
            [0, 0, 1, 0],  # 步进5：B-
            [0, 0, 1, 1],  # 步进6：B- 和 A-
            [0, 0, 0, 1],  # 步进7：A-
            [1, 0, 0, 1],  # 步进8：A+ 和 A-
        ]
    }

    # 步进电机运动模式：定步运动、连续运动
    CONTINUOUS_MOTION, STEP_MOTION = (0,1)

    def __init__(self, pca9685: PCA9685, motor_count: int = 2):
        """
        构造函数，初始化电机控制类。

        Args:
            pca9685 (PCA9685): PCA9685实例，用于控制PWM信号。
            motor_count (int): 需要控制的电机数量。默认值为2个步进电机。

        Raises:
            ValueError: 如果电机数量超出范围（1-4）或传入的pca9685不是PCA9685实例。

        ============================================
        Constructor to initialize the motor control class.

        Args:
            pca9685 (PCA9685): PCA9685 instance to control PWM signals.
            motor_count (int): Number of motors to control. Default is 2 motors.

        Raise:
            ValueError: If motor count is out of range (1-4) or pca9685 is not an instance of PCA9685.
        """
        # 由于PCA9685芯片输出引脚限制，电机数量不可能大于四个
        if motor_count < 1 or motor_count > 4:
            raise ValueError(f"Invalid motor_count: {motor_count}. Motor count must be between 1 and 4.")

        # 判断pca9685是否为PCA9685实例
        if not isinstance(pca9685, PCA9685):
            raise ValueError("Invalid pca9685. pca9685 must be an instance of PCA9685.")

        self.pca9685 = pca9685
        self.motor_count = motor_count

        # 根据电机数量生成对应数量定时器列表
        self.timers = [Timer(-1) for _ in range(motor_count)]
        # 根据电机数量生成对应数量步进电机的总步数列表
        self.steps = [0 for _ in range(motor_count)]
        # 根据电机数量生成对应数量步进电机计步器列表
        self.step_counters = [0 for _ in range(motor_count)]
        # 根据电机数量生成对应数量步进电机方向列表
        self.directions = [0 for _ in range(motor_count)]
        # 根据电机数量生成对应数量步进电机驱动模式列表
        self.driver_modes = [0 for _ in range(motor_count)]
        # 根据电机数量生成对应数量步进电机转速列表
        # 这里转速并非是步进电机实际转速，而是指1s内驱动器输出脉冲的个数
        self.speeds = [0 for _ in range(motor_count)]
        # 根据电机数量生成对应数量步进电机运动模式列表
        self.motor_modes = [BusStepMotor.CONTINUOUS_MOTION for _ in range(motor_count)]

        # 初始化PCA9685芯片
        self.pca9685.reset()
        # 设置PCA9685芯片的频率为5000Hz
        self.pca9685.freq(5000)
        # 根据电机数量设置PCA9685芯片不同PWM通道占空比为0：一个步进电机对应四个PWM通道
        # 同时步进电机编号从0开始，对应PWM通道从0开始，以4个PWM通道递增
        for i in range(motor_count*4):
            self.pca9685.duty(i, 0)

    @micropython.native
    def _next_step(self, motor_id: int) -> None:
        """
        计算并更新当前步进电机的步进状态。

        根据步进电机的驱动模式、方向和当前步数来计算电机的下一步相位，并通过PCA9685输出相应的PWM信号来驱动电机。
        需要注意的是，这种方法基于每个电机的步进计数来实现控制，未考虑一些特殊情况，比如步进速度过快导致的失步问题，仅能在小负载和稳定情况下使用。

        Args:
            motor_id (int): 电机编号。

        =============================================

        Calculate and update the step state of the current motor.

        Args:
            motor_id (int): Motor ID.
        """

        # 计算步进电机当前的步数，并根据驱动模式和方向选择相应的相位序列
        current_step = self.step_counters[motor_id]
        driver_mode = self.driver_modes[motor_id]
        direction = self.directions[motor_id]

        # 获取相位序列
        phase_sequence = BusStepMotor.PHASES[driver_mode]
        # 获取当前相位
        current_phase = phase_sequence[current_step % len(phase_sequence)]

        # 输出PWM信号，控制步进电机运动
        base_channel = motor_id * 4
        # 首先将所有通道对应电机驱动输出设置为0
        for i in range(4):
            self.pca9685.duty(base_channel + i, 4095)

        for i in range(4):
            self.pca9685.duty(base_channel + i, current_phase[i] * 4095)
            # print(base_channel + i, current_phase[i] * 4095)

        # print("current_step:", current_step)

        # 更新步进计数器，决定下一个步进状态
        if direction == BusStepMotor.FORWARD:
            self.step_counters[motor_id] += 1
        else:
            self.step_counters[motor_id] -= 1

        # 判断是否完成指定步数，若完成，则停止运动
        if abs(self.step_counters[motor_id]) >= self.steps[motor_id]:
            # 如果是步进运动，则停止定时器
            if self.motor_modes[motor_id] == BusStepMotor.STEP_MOTION:
                self.stop_step_motion(motor_id + 1)
            # 如果是连续运动，则无须停止定时器
            else:
                return

    def _start_timer(self, motor_id: int, speed: int) -> None:
        """
        启动定时器并设置回调函数。
        定时器的精度和步进频率（速度）之间可能会存在一定的偏差，尤其是在高频率下，如果控制系统需要更高精度的步进控制，可能需要更专业的计时器硬件或通过更精确的算法调整定时器频率。

        Args:
            motor_id (int): 电机编号。
            speed (int): 电机的转速，并非步进电机的实际转速，而是指1s内驱动器输出脉冲的个数。

        ==============================================

        Start the timer and set the callback function to control the continuous motion of the motor.

        Args:
            motor_id (int): Motor ID.
            speed (int): Motor speed，not the actual speed of the stepper motor, but the number of pulses output by the driver per second.
        """
        # 计算定时器间隔时间（以毫秒为单位），最小间隔为1毫秒
        interval = max(1, int(1000 / speed))

        # 设置定时器，每隔 interval 毫秒调用 _next_step
        # 使用 lambda 函数来包裹 _next_step，并在调用时传递 motor_id，并使用 micropython.schedule 调度
        self.timers[motor_id].init(period=interval, mode=Timer.PERIODIC, callback=lambda t: self._next_step(motor_id))

    def _stop_timer(self, motor_id: int) -> None:
        """
        停止指定电机的定时器。

        Args:
            motor_id (int): 电机编号。

        ===============================================

        Stop the timer for the specified motor.

        Args:
            motor_id (int): Motor ID.
        """
        self.timers[motor_id].deinit()

    @micropython.native
    def start_continuous_motion(self, motor_id: int, direction: int, driver_mode: int, speed: int) -> None:
        """
        启动电机进行连续运动。

        Args:
            motor_id (int): 电机编号。
            direction (int): 运动方向（正转或反转）。
            driver_mode (int): 驱动模式（单相、双相、半步驱动）。
            speed (int): 电机的转速，并非步进电机的实际转速，而是指1s内驱动器输出脉冲的个数。

        Raises:
            ValueError: 如果速度不是0到1000之间的整数，或者电机编号无效，或者电机方向无效，或者驱动模式无效。

        ===============================================

        Start the motor for continuous motion.

        Args:
            motor_id (int): Motor ID.
            direction (int): Direction (FORWARD or BACKWARD).
            driver_mode (int): Driver mode (DRIVER_MODE_SINGLE, DRIVER_MODE_DOUBLE or DRIVER_MODE_HALF_STEP).
            speed (int): Motor speed，not the actual speed of the stepper motor, but the number of pulses output by the driver per second.

        Raises:
            ValueError: If speed is not an integer between 0 and 1000, or motor ID is invalid, or motor direction is invalid, or driver mode is invalid.
        """
        # 判断速度是不是在0到1000之间的整数
        if not isinstance(speed, int) or speed < 0 or speed > 1000:
            raise ValueError("Invalid speed: %d. Speed must be an integer between 0 and 1000." % speed)

        # 判断电机ID是否有效
        if motor_id < 1 or motor_id > self.motor_count:
            raise ValueError("Invalid motor_id: %d. Motor ID must be between 1 and %d." % (motor_id, self.motor_count))

        # 判断电机方向是否有效
        if direction != BusStepMotor.FORWARD and direction != BusStepMotor.BACKWARD:
            raise ValueError("Invalid direction: %d. Direction must be FORWARD or BACKWARD." % direction)

        # 判断驱动模式是否有效
        if driver_mode != BusStepMotor.DRIVER_MODE_SINGLE and driver_mode != BusStepMotor.DRIVER_MODE_DOUBLE and driver_mode != BusStepMotor.DRIVER_MODE_HALF_STEP:
            raise ValueError("Invalid driver_mode: %d. Driver mode must be DRIVER_MODE_SINGLE, DRIVER_MODE_DOUBLE or DRIVER_MODE_HALF_STEP." % driver_mode)

        # 调整 motor_id 从 1 开始
        motor_id -= 1

        self.directions[motor_id] = direction
        self.driver_modes[motor_id] = driver_mode
        self.speeds[motor_id] = speed
        self.motor_modes[motor_id] = BusStepMotor.CONTINUOUS_MOTION

        # 启动定时器，开始连续运动
        self._start_timer(motor_id, speed)

    @micropython.native
    def stop_continuous_motion(self, motor_id: int) -> None:
        """
        停止电机的连续运动。

        Args:
            motor_id (int): 电机编号。

        Raises:
            ValueError: 如果电机编号无效。

        ===============================================
        Stop the continuous motion of the specified motor.

        Args:
            motor_id (int): Motor ID.

        Raises:
            ValueError: If motor ID is invalid.
        """
        # 判断电机ID是否有效
        if motor_id < 1 or motor_id > self.motor_count:
            raise ValueError("Invalid motor_id: %d. Motor ID must be between 1 and %d." % (motor_id, self.motor_count))

        # 调整 motor_id 从 1 开始
        motor_id -= 1
        # 停止定时器，停止运动
        self._stop_timer(motor_id)

        # 清除步进计数器，以便下一次运动重新开始计数
        self.step_counters[motor_id] = 0
        # 清除目标步数
        self.steps[motor_id] = 0

        # 计算电机对应的PWM通道
        # 对于motor_id为1, 控制0到3通道；motor_id为2, 控制4到7通道
        pwm_start_index = (motor_id) * 4     # 计算对应的PWM通道起始索引
        pwm_end_index = pwm_start_index + 3  # 计算对应的PWM通道结束索引

        # 将控制通道的PWM占空比设置为0
        for pwm_index in range(pwm_start_index, pwm_end_index + 1):
            self.pca9685.duty(pwm_index, 0)

        print("stop_continuous_motion")

    @micropython.native
    def start_step_motion(self, motor_id: int, direction: int, driver_mode: int, speed: int, steps: int) -> None:
        """
        启动步进电机的定步运动。

        该方法用于启动步进电机进行指定步数的运动。电机在指定方向、驱动模式、转速下运动，并按照指定步数完成运动。

        Args:
            motor_id (int): 电机编号，用于标识需要控制的电机。
            direction (int): 电机运动方向，`FORWARD`（正转）或 `BACKWARD`（反转）。
            driver_mode (int): 电机驱动模式，`DRIVER_MODE_SINGLE`（单相驱动）、`DRIVER_MODE_DOUBLE`（双相驱动）或 `DRIVER_MODE_HALF_STEP`（半步驱动）。
            speed (int): 电机转速，单位为步/分钟，控制电机每分钟旋转多少步。
            steps (int): 需要执行的步数，电机将按指定的步数进行运动。

        Raises:
            ValueError: 如果目标步数不是正整数，或者速度不是0到1000之间的整数，或者电机编号无效，或者电机方向无效，或者驱动模式无效。

        ===============================================

        Start the step motion of the specified motor. This method is used to start the motor to perform a specified number of steps.
        The motor moves in the specified direction, driver mode, and speed, and completes the movement according to the specified steps.

        Args:
            motor_id (int): Motor ID, used to identify the motor to be controlled.
            direction (int): Motor direction, FORWARD (forward) or BACKWARD (reverse).
            driver_mode (int): Motor driver mode, DRIVER_MODE_SINGLE (single-phase driver),
                               DRIVER_MODE_DOUBLE (double-phase driver) or DRIVER_MODE_HALF_STEP (half-step driver).
            speed (int): Motor speed, in steps per minute, controlling how many steps the motor rotates per minute.
            steps (int): The number of steps to be executed, the motor will perform the movement according to the specified steps.

        Raises:
            ValueError: If the target steps is not a positive integer, or the speed is not an integer between 0 and 1000,
            or the motor ID is invalid, or the motor direction is invalid, or the driver mode is invalid.
        """
        # 判断目标步数是否为有效正整数
        if not isinstance(steps, int) or steps <= 0:
            raise ValueError("Invalid steps: %d. Steps must be a positive integer." % steps)

        # 判断速度是不是在0到1000之间的整数
        if not isinstance(speed, int) or speed < 0 or speed > 1000:
            raise ValueError("Invalid speed: %d. Speed must be an integer between 0 and 1000." % speed)

        # 判断电机ID是否有效
        if motor_id < 1 or motor_id > self.motor_count:
            raise ValueError("Invalid motor_id: %d. Motor ID must be between 1 and %d." % (motor_id, self.motor_count))

        # 判断电机方向是否有效
        if direction != BusStepMotor.FORWARD and direction != BusStepMotor.BACKWARD:
            raise ValueError("Invalid direction: %d. Direction must be FORWARD or BACKWARD." % direction)

        # 判断驱动模式是否有效
        if driver_mode != BusStepMotor.DRIVER_MODE_SINGLE and driver_mode != BusStepMotor.DRIVER_MODE_DOUBLE and driver_mode != BusStepMotor.DRIVER_MODE_HALF_STEP:
            raise ValueError(
                "Invalid driver_mode: %d. Driver mode must be DRIVER_MODE_SINGLE, DRIVER_MODE_DOUBLE or DRIVER_MODE_HALF_STEP." % driver_mode)

        # 调整 motor_id 从 1 开始
        motor_id -= 1

        # 设置步进电机的目标步数
        self.steps[motor_id] = steps
        self.directions[motor_id] = direction
        self.driver_modes[motor_id] = driver_mode
        self.speeds[motor_id] = speed
        self.motor_modes[motor_id] = BusStepMotor.STEP_MOTION

        # 启动定时器，开始定步运动
        self._start_timer(motor_id, speed)

    @micropython.native
    def stop_step_motion(self, motor_id: int) -> None:
        """
        停止步进电机的定步运动。

        该方法用于停止电机当前的步进运动，并清除相关的PWM信号输出，停止定时器的计时。

        Args:
            motor_id (int): 电机编号，用于标识需要停止的电机。

        Raises:
            ValueError: 如果电机编号无效。

        ===============================================

        Stop the step motion of the specified motor. This method is used to stop the motor's current step motion,
        clear the related PWM signal output, and stop the timer's timing.

        Args:
            motor_id (int): Motor ID, used to identify the motor to be stopped.

        Raises:
            ValueError: If motor ID is invalid.
        """
        # 判断电机ID是否有效
        if motor_id < 1 or motor_id > self.motor_count:
            raise ValueError("Invalid motor_id: %d. Motor ID must be between 1 and %d." % (motor_id, self.motor_count))

        # 调整 motor_id 从 1 开始
        motor_id -= 1

        # 停止定时器，停止定步运动
        self._stop_timer(motor_id)

        # 清除步进计数器，以便下一次运动重新开始计数
        self.step_counters[motor_id] = 0
        # 清除目标步数
        self.steps[motor_id] = 0

        # 停止步进电机的PWM信号输出
        # 计算电机对应的PWM通道
        # 对于motor_id为1, 控制0到3通道；motor_id为2, 控制4到7通道
        pwm_start_index = (motor_id) * 4     # 计算对应的PWM通道起始索引
        pwm_end_index = pwm_start_index + 3  # 计算对应的PWM通道结束索引

        # 将控制通道的PWM占空比设置为0
        for pwm_index in range(pwm_start_index, pwm_end_index + 1):
            self.pca9685.duty(pwm_index, 0)

        # 将电机运动模式设置为连续运动模式
        self.motor_modes[motor_id] = BusStepMotor.CONTINUOUS_MOTION

        print("stop_step_motion")

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================