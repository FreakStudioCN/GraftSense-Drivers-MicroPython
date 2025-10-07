# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/1/18 下午1:59   
# @Author  : 李清水            
# @File    : serial_servo.py       
# @Description : TTL串口舵机驱动类

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import UART
# 时间相关的模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 串口舵机自定义类
class SerialServo:
    """
    串口舵机控制类，用于生成和发送控制指令。

    该类通过UART串口与舵机进行通信，支持构建控制指令包、计算校验和以及发送指令。
    支持可调的波特率和不同舵机的控制。

    Attributes:
        uart (machine.UART): 用于与舵机通信的UART实例。

    Class Variables:
        - 指令及其参数长度或返回数据长度的定义。
        - 各种舵机控制指令的定义，包括写入命令和读取命令。
        - 舵机工作模式的定义。
        - LED报警故障类型的定义。

    Methods:
        calculate_checksum(data: list[int]) -> int:
            计算校验和，确保数据的完整性和正确性。
        build_packet(servo_id: int, cmd: int, params: list[int]) -> bytearray:
            构建舵机指令包。
        send_command(servo_id: int, cmd: int, params: list[int] = []) -> None:
            发送控制指令到舵机。
        receive_command(expected_cmd: int, expected_data_len: int) -> list:
            接收并处理舵机返回的指令数据包。
        move_servo_immediate(servo_id: int, angle: float, time_ms: int) -> None:
            立即控制舵机转动到指定角度。
        get_servo_move_immediate(servo_id: int) -> tuple:
            获取舵机的预设角度和时间。
        move_servo_with_time_delay(servo_id: int, angle: float, time_ms: int) -> None:
            控制舵机延迟转动到指定角度。
        get_servo_move_with_time_delay(servo_id: int) -> tuple:
            获取舵机的预设角度和时间（延迟转动）。
        start_servo(servo_id: int) -> None:
            启动舵机的转动。
        stop_servo(servo_id: int) -> None:
            立即停止舵机转动并停在当前角度位置。
        set_servo_id(servo_id: int, new_id: int) -> None:
            设置舵机的新ID值。
        get_servo_id(servo_id: int) -> int:
            获取舵机的ID。
        set_servo_angle_offset(servo_id: int, angle: float, save_to_memory: bool = False) -> None:
            根据角度值调整舵机的偏差。
        get_servo_angle_offset(servo_id: int) -> float:
            获取舵机的偏差角度。
        set_servo_angle_range(servo_id: int, min_angle: float, max_angle: float) -> None:
            设置舵机的最小和最大角度限制。
        get_servo_angle_range(servo_id: int) -> tuple:
            获取舵机的角度限位。
        set_servo_vin_range(servo_id: int, min_vin: float, max_vin: float) -> None:
            设置舵机的最小和最大输入电压限制。
        get_servo_vin_range(servo_id: int) -> tuple:
            获取舵机的电压限制值。
        set_servo_temp_range(servo_id: int, max_temp: int) -> None:
            设置舵机的最高温度限制。
        get_servo_temp_range(servo_id: int) -> int:
            获取舵机的内部最高温度限制值。
        read_servo_temp(servo_id: int) -> int:
            获取舵机的实时温度。
        read_servo_voltage(servo_id: int) -> float:
            获取舵机的实时输入电压。
        read_serv:pos_read(servo_id: int) -> float:
            获取舵机的实时角度位置。
        set_servo_mode_and_speed(servo_id: int, mode: int, speed: int) -> None:
            设置舵机的工作模式和电机转速。
        get_servo_mode_and_speed(servo_id: int) -> tuple:
            获取舵机的工作模式和转动速度。
        set_servo_motor_load(servo_id: int, unload: bool) -> None:
            设置舵机的电机是否卸载掉电。
        get_servo_motor_load_status(servo_id: int) -> bool:
            获取舵机电机是否装载或卸载。
        set_servo_led(servo_id: int, led_on: bool) -> None:
            设置舵机的LED灯的亮灭状态。
        get_servo_led(servo_id: int) -> bool:
            获取舵机LED的亮灭状态。
        set_servo_led_alarm(servo_id: int, alarm_code: int) -> None:
            设置舵机LED闪烁报警对应的故障值。
        get_servo_led_alarm(servo_id: int) -> int:
            获取舵机LED故障报警状态。

    =================================================

        SerialServo Class:
    A class to control the serial servo, used to generate and send control commands.

    This class communicates with the servo through UART serial, supporting the construction of control command packets,
    checksum calculation, and command sending.
    It supports adjustable baud rates and control for various servo models.

    Attributes:
        uart (machine.UART): UART instance for communication with the servo.

    Class Variables:
        - Definitions of command lengths or return data lengths.
        - Definitions of various servo control commands, including write and read commands.
        - Definitions of servo working modes.
        - Definitions of LED alarm fault types.

    Methods:
        calculate_checksum(data: list[int]) -> int:
            Calculate checksum to ensure data integrity and correctness.
        build_packet(servo_id: int, cmd: int, params: list[int]) -> bytearray:
            Construct servo control command packet.
        send_command(servo_id: int, cmd: int, params: list[int] = []) -> None:
            Send control command to the servo.
        receive_command(expected_cmd: int, expected_data_len: int) -> list:
            Receive and process the response from the servo.
        move_servo_immediate(servo_id: int, angle: float, time_ms: int) -> None:
            Control the servo to move immediately to a specified angle.
        get_servo_move_immediate(servo_id: int) -> tuple:
            Get the servo's preset angle and time for immediate movement.
        move_servo_with_time_delay(servo_id: int, angle: float, time_ms: int) -> None:
            Control the servo to move to a specified angle with a delay.
        get_servo_move_with_time_delay(servo_id: int) -> tuple:
            Get the servo's preset angle and time for delayed movement.
        start_servo(servo_id: int) -> None:
            Start the servo's movement.
        stop_servo(servo_id: int) -> None:
            Immediately stop the servo and hold at the current position.
        set_servo_id(servo_id: int, new_id: int) -> None:
            Set a new ID for the servo.
        get_servo_id(servo_id: int) -> int:
            Get the current ID of the servo.
        set_servo_angle_offset(servo_id: int, angle: float, save_to_memory: bool = False) -> None:
            Adjust the servo's angle offset based on a specified angle.
        get_servo_angle_offset(servo_id: int) -> float:
            Get the current angle offset of the servo.
        set_servo_angle_range(servo_id: int, min_angle: float, max_angle: float) -> None:
            Set the minimum and maximum angle limits for the servo.
        get_servo_angle_range(servo_id: int) -> tuple:
            Get the current angle limits of the servo.
        set_servo_vin_range(servo_id: int, min_vin: float, max_vin: float) -> None:
            Set the minimum and maximum input voltage range for the servo.
        get_servo_vin_range(servo_id: int) -> tuple:
            Get the current input voltage range of the servo.
        set_servo_temp_range(servo_id: int, max_temp: int) -> None:
            Set the maximum temperature limit for the servo.
        get_servo_temp_range(servo_id: int) -> int:
            Get the current maximum temperature limit for the servo.
        read_servo_temp(servo_id: int) -> int:
            Read the current temperature of the servo.
        read_servo_voltage(servo_id: int) -> float:
            Read the current input voltage of the servo.
        read_servo_pos(servo_id: int) -> float:
            Read the current angle position of the servo.
        set_servo_mode_and_speed(servo_id: int, mode: int, speed: int) -> None:
            Set the working mode and motor speed for the servo.
        get_servo_mode_and_speed(servo_id: int) -> tuple:
            Get the current working mode and motor speed of the servo.
        set_servo_motor_load(servo_id: int, unload: bool) -> None:
            Set whether the servo motor is loaded or unloaded.
        get_servo_motor_load_status(servo_id: int) -> bool:
            Get the current load status of the servo motor.
        set_servo_led(servo_id: int, led_on: bool) -> None:
            Set the LED light status (on/off) of the servo.
        get_servo_led(servo_id: int) -> bool:
            Get the current LED light status of the servo.
        set_servo_led_alarm(servo_id: int, alarm_code: int) -> None:
            Set the LED alarm fault code for the servo.
        get_servo_led_alarm(servo_id: int) -> int:
            Get the current LED alarm fault code of the servo.

    """

    # 类变量：指令及其参数长度或返回数据长度
    # 写入指令及其对应的参数长度
    # 读取指令及其对应的参数长度和返回数据长度

    # 舵机立即转动写入命令
    SERVO_MOVE_TIME_WRITE = (1, 7)
    # 舵机立即转动参数读取命令
    SERVO_MOVE_TIME_READ = (2, 3, 7)

    # 舵机延迟转动写入命令
    SERVO_MOVE_TIME_WAIT_WRITE = (7, 7)
    # 舵机延迟转动读取命令
    SERVO_MOVE_TIME_WAIT_READ = (8, 3, 7)

    # 舵机开启转动指令（配合SERVO_MOVE_TIME_WAIT_WRITE指令使用）
    SERVO_MOVE_START = (11, 3)
    # 舵机停止转动指令
    SERVO_MOVE_STOP = (12, 3)

    # 舵机ID写入命令（支持掉电保存）
    SERVO_ID_WRITE = (13, 4)
    # 舵机ID读取命令
    SERVO_ID_READ = (14, 3, 4)

    # 舵机偏差调节指令（不支持掉电保存）
    SERVO_ANGLE_OFFSET_ADJUST = (17, 4)
    # 舵机偏差调节指令（支持掉电保存）
    SERVO_ANGLE_OFFSET_WRITE = (18, 3)
    # 舵机偏差调节读取指令
    SERVO_ANGLE_OFFSET_READ = (19, 3, 4)

    # 舵机角度限位写入命令（支持掉电保存）
    SERVO_ANGLE_LIMIT_WRITE = (20, 7)
    # 舵机角度限位读取命令
    SERVO_ANGLE_LIMIT_READ = (21, 3, 7)

    # 舵机电压限制写入命令（支持掉电保存）
    SERVO_VIN_LIMIT_WRITE = (22, 7)
    # 舵机电压限制读取命令
    SERVO_VIN_LIMIT_READ = (23, 3, 7)

    # 舵机温度限制写入命令（支持掉电保存）
    SERVO_TEMP_MAX_LIMIT_WRITE = (24, 4)
    # 舵机温度限制读取命令
    SERVO_TEMP_MAX_LIMIT_READ = (25, 3, 4)

    # 舵机实时温度读取指令
    SERVO_TEMP_READ = (26, 3, 4)
    # 舵机实时电压读取指令
    SERVO_VIN_READ = (27, 3, 5)
    # 舵机当前角度读取指令
    SERVO_POS_READ = (28, 3, 5)

    # 舵机模式切换指令（不支持掉电保存）
    SERVO_OR_MOTOR_MODE_WRITE = (29, 7)
    # 舵机模式及参数读取指令
    SERVO_OR_MOTOR_MODE_READ = (30, 3, 7)

    # 舵机上电/掉电控制指令（不支持掉电保存）
    SERVO_LOAD_OR_UNLOAD_WRITE = (31, 4)
    # 舵机上电/掉电读取指令
    SERVO_LOAD_OR_UNLOAD_READ = (32, 3, 4)

    # 舵机LED控制指令（支持掉电保存）
    SERVO_LED_CTRL_WRITE = (33, 4)
    # 舵机LED读取指令
    SERVO_LED_CTRL_READ = (34, 3, 4)

    # 舵机LED报警闪烁指令
    SERVO_LED_ERROR_WRITE = (35, 4)
    # 舵机LED报警闪烁值读取指令
    SERVO_LED_ERROR_READ = (36, 3, 4)

    # 类变量：舵机工作模式
    # 0 代表位置控制模式
    MODE_POSITION = 0
    # 1 代表电机控制模式
    MODE_MOTOR = 1

    # 类变量：LED报警故障类型
    ERROR_NO_ALARM = 0              # 无报警
    ERROR_OVER_TEMP = 1             # 过温报警
    ERROR_OVER_VOLT = 2             # 过压报警
    ERROR_OVER_TEMP_AND_VOLT = 3    # 过温和过压报警
    ERROR_STALL = 4                 # 堵转报警
    ERROR_OVER_TEMP_AND_STALL = 5   # 过温和堵转报警
    ERROR_OVER_VOLT_AND_STALL = 6   # 过压和堵转报警
    ERROR_ALL = 7                   # 过温、过压和堵转报警

    # 读取命令集合：根据指令的元组长度来确定哪些是读取命令（命令编号，参数长度，返回数据长度）
    READ_COMMANDS = {
        2,  # SERVO_MOVE_TIME_READ
        8,  # SERVO_MOVE_TIME_WAIT_READ
        14, # SERVO_ID_READ
        19, # SERVO_ANGLE_OFFSET_READ
        21, # SERVO_ANGLE_LIMIT_READ
        23, # SERVO_VIN_LIMIT_READ
        25, # SERVO_TEMP_MAX_LIMIT_READ
        26, # SERVO_TEMP_READ
        27, # SERVO_VIN_READ
        28, # SERVO_POS_READ
        30, # SERVO_OR_MOTOR_MODE_READ
        32, # SERVO_LOAD_OR_UNLOAD_READ
        34, # SERVO_LED_CTRL_READ
        36  # SERVO_LED_ERROR_READ
    }

    def __init__(self, uart: UART) -> None:
        """
        初始化串口舵机控制类。

        Args:
            uart (UART): 使用的UART实例。

        ===================================================

        Initialize the Serial Servo Control Class.

        Args:
            uart (UART): The UART instance used for communication with the servo.

        """
        self.uart = uart

    def calculate_checksum(self, data: list[int]) -> int:
        """
        计算校验和。

        校验和通过对数据包进行求和并取反得到（低八位数据），确保数据的完整性和正确性。

        Args:
            data (list[int]): 数据包（不包括校验和本身）。

        Returns:
            int: 计算出的校验和，值范围为 0~255。

        ===================================================

        Calculate checksum to ensure data integrity and correctness.

        The checksum is obtained by summing the data packet and taking the one's complement (low eight bits of data).
        Args:
            data (list[int]): Data packet (excluding checksum itself).

        Returns:
            int: Calculated checksum, value range 0~255.

        """

        checksum = ~(sum(data) & 0xFF) & 0xFF

        return checksum

    def build_packet(self, servo_id: int, cmd: int, params: list[int]) -> bytearray:
        """
        构建舵机指令包。

        根据舵机ID、指令命令和参数生成一个完整的数据包，并附加校验和。

        Args:
            servo_id (int): 舵机ID，范围0~253，其中254为广播ID，表示所有舵机。
            cmd (int): 指令命令字节。
            params (list[int]): 参数列表。

        Returns:
            bytearray: 构建的舵机控制指令包。

        Raises:
            ValueError: 如果舵机ID不在 0~254 范围内，则抛出异常。

        ===================================================

        Build servo control command packet, including checksum.

        Args:
            servo_id (int): Servo ID, range 0~253, where 254 is broadcast ID, indicating all servos.
            cmd (int): Command byte.
            params (list[int]): Parameter list (default empty).

        Returns:
            bytearray: Built servo control command packet, including checksum.

        Raises:
            ValueError: If the servo ID is not in the range 0~254, an exception will be raised.
        """
        # 对传入参数进行检查
        # 检查舵机ID是否在 0~254 范围内
        if servo_id < 0 or servo_id > 254:
            raise ValueError("Servo ID must be in range 0~254.")

        # 数据包长度（指令+参数+校验和）
        length = 3 + len(params)
        # 构建数据包：帧头 + ID + 数据长度 + 命令 + 参数 + 校验和
        packet = [0x55, 0x55, servo_id, length, cmd] + params
        # 计算校验和（从ID到最后一个参数）
        checksum = self.calculate_checksum(packet[2:])
        # 增加校验和
        packet.append(checksum)

        return bytearray(packet)

    def send_command(self, servo_id: int, cmd: int, params: list[int] = []) -> None:
        """
        发送控制指令到舵机。

        通过UART将构建好的数据包发送给指定舵机，执行相应的控制命令。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            cmd (int): 指令命令字节。
            params (list[int], optional): 参数列表（默认为空）。

        Raises:
            ValueError: 如果舵机ID不在 0~254 范围内，则抛出异常。

        ===================================================

        Send control command to the servo.

        Args:
            servo_id (int): Servo ID, range 0~253.
            cmd (int): Command byte.
            params (list[int], optional): Parameter list (default empty).

        Raises:
            ValueError: If the servo ID is not in the range 0~254, an exception will be raised.

        """
        packet = self.build_packet(servo_id, cmd, params)
        self.uart.write(packet)

    def receive_command(self, expected_cmd: int, expected_data_len: int) -> list:
        """
        接收并处理舵机返回的指令数据包。

        该方法从UART串口接收数据，验证帧头、命令编号、数据长度及校验和，
        如果数据无误，解析并返回相关参数。

        Args:
            expected_cmd (int): 期望接收到的命令编号。
            expected_data_len (int): 期望的返回数据长度。

        Returns:
            list: 返回解析后的数据列表（包括参数），如果数据有误则返回空列表。

        Raises:
            ValueError: 如果期望接收到的命令编号不是读取命令，则抛出异常。

        ===================================================

        Receive and process the response from the servo.

        This method receives data from the UART serial interface, validates the frame header, command ID, data length, and checksum.
        If the data is correct, it parses and returns the relevant parameters.

        Args:
            expected_cmd (int): The expected command ID to be received.
            expected_data_len (int): The expected length of the returned data.

        Returns:
            list: A list of parsed data (including parameters). If the data is incorrect, an empty list is returned.

        Raises:
            ValueError: If the expected command ID is not a read command, an exception is raised.

        """
        # 判断期望接收到的命令编号是否是读取命令
        if expected_cmd not in SerialServo.READ_COMMANDS:
            raise ValueError("Expected command is not a read command.")

        # 接收数据
        data = self.uart.read()

        # # 打印接收到的数据
        # print('recv data:', data)

        # 如果接收到的数据长度没有，则返回空列表
        if data is None:
            return []

        # 检查帧头是否正确（前两个字节应该是0x55）
        if data[0] != 0x55 or data[1] != 0x55:
            return []

        # 检查命令编号是否与预期一致
        if data[4] != expected_cmd:
            return []

        # 检查数据长度是否与期望一致，data[3]为数据长度位
        length = data[3]
        if length != expected_data_len:
            # 如果返回数据长度不匹配，则返回空列表
            return []

        # 校验和计算
        checksum_received = data[-1]
        # 从ID开始到倒数第二个字节
        checksum_calculated = self.calculate_checksum(data[2:-1])
        if checksum_received != checksum_calculated:
            return []

        # 根据数据长度解析相关参数，数据区包括从第6个字节到倒数第二个字节
        params = data[5:-1]

        # 返回解析后的参数
        return params

    def move_servo_immediate(self, servo_id: int, angle: float, time_ms: int) -> None:
        """
        立即控制舵机转动到指定角度。

        该方法使用 SERVO_MOVE_TIME_WRITE 指令，在给定时间内将舵机转动到指定的角度。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            angle (float): 目标角度（0~240度范围内）。每个单位表示 0.24 度。
            time_ms (int): 转动时间（0~30000 毫秒），表示舵机转动到指定角度的时间。

        Raises:
            ValueError: 如果角度不在 0~240度范围内、舵机ID不在0~253或时间不在范围内，则抛出异常。

        ===================================================

        Immediately control the servo to rotate to the specified angle.

        Args:
            servo_id (int): Servo ID, range 0~253.
            angle (float): Target angle (0~240 degrees). Each unit represents 0.24 degrees.
            time_ms (int): Time to rotate (0~30000 milliseconds), indicating the time for the servo to rotate to the specified angle.

        Raises:
            ValueError: If the angle is not in the range 0~240, the servo ID is not in the range 0~253,
            or the time is not in the range, an exception will be raised.

        """
        # 判断角度是否在 0~240度范围内
        if angle < 0 or angle > 240:
            raise ValueError("Angle must be in range 0~240.")

        # 判断时间是否在 0~30000 毫秒范围内
        if time_ms < 0 or time_ms > 30000:
            raise ValueError("Time must be in range 0~30000.")

        # 将角度转换为舵机控制指令所需的低八位和高八位
        # 转换为整数并限制为低8位
        angle_low = int(angle / 0.24) & 0xFF
        # 获取高8位
        angle_high = (int(angle / 0.24) >> 8) & 0xFF

        # 将时间转换为低八位和高八位
        # 转换为低8位
        time_low = time_ms & 0xFF
        # 获取高8位
        time_high = (time_ms >> 8) & 0xFF

        # 发送 SERVO_MOVE_TIME_WRITE 指令
        self.send_command(servo_id, SerialServo.SERVO_MOVE_TIME_WRITE[0], [angle_low, angle_high, time_low, time_high])

    def get_servo_move_immediate(self, servo_id: int) -> tuple:
        """
        获取舵机的预设角度和时间。

        该方法通过舵机ID发送 `SERVO_MOVE_TIME_READ` 指令来读取舵机的预设角度和时间，
        然后延迟5ms，接收并解析返回的数据。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            tuple: 返回角度和时间的元组，角度范围 0~240 度，时间范围 0~30000 毫秒。
                   如果读取失败，则返回 None。

        Raises:
            ValueError: 如果角度或时间值不在合理范围内，则抛出异常。

        ===================================================

        Get the preset angle and time of the servo.

        This method sends the `SERVO_MOVE_TIME_READ` command to the servo using the servo ID to read the preset angle and time,
        then waits for 5ms before receiving and parsing the returned data.

        Args:
            servo_id (int): The ID of the servo.

        Returns:
            tuple: A tuple containing the angle and time. The angle range is 0 to 240 degrees, and the time range is 0 to 30,000 milliseconds.
                   Returns `None` if the reading fails.

        Raises:
            ValueError: If the angle or time values are out of the acceptable range, an exception is raised.
        """

        # 发送SERVO_MOVE_TIME_READ命令
        self.send_command(servo_id, SerialServo.SERVO_MOVE_TIME_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_MOVE_TIME_READ[0], SerialServo.SERVO_MOVE_TIME_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析角度值，低8位和高8位合并为一个16位整数
        angle_value = params[0] + (params[1] << 8)
        # 将angle_value转换为角度值
        angle_value = angle_value * 0.24
        # 判断角度是否在合理范围内
        if angle_value < 0 or angle_value > 240:
            raise ValueError("Angle value is out of range.")

        # 解析时间值，低8位和高8位合并为一个16位整数
        time_value = params[2] + (params[3] << 8)
        # 判断时间是否在合理范围内
        if time_value < 0 or time_value > 30000:
            raise ValueError("Time value is out of range.")

        return angle_value, time_value

    def move_servo_with_time_delay(self, servo_id: int, angle: float, time_ms: int) -> None:
        """
        控制舵机延迟转动到指定角度。

        该方法使用 SERVO_MOVE_TIME_WAIT_WRITE 指令，设定目标角度和转动时间，并
        发送 SERVO_MOVE_START 指令来开始转动。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            angle (float): 目标角度（0~240度范围内）。每个单位表示 0.24 度。
            time_ms (int): 转动时间（0~30000 毫秒），表示舵机转动到指定角度的时间。

        Raises:
            ValueError: 如果角度或时间值不在合理范围内，则抛出异常。

        ===================================================

        Control the servo to move to a specified angle with a delay.

        This method uses the `SERVO_MOVE_TIME_WAIT_WRITE` command to set the target angle and movement time,
        and sends the `SERVO_MOVE_START` command to initiate the movement.

        Args:
            servo_id (int): The ID of the servo, range 0~253.
            angle (float): The target angle (within the range of 0~240 degrees). Each unit represents 0.24 degrees.
            time_ms (int): The movement time (0~30,000 milliseconds), indicating the time the servo takes to reach the specified angle.

        Raises:
            ValueError: If the angle or time values are out of the acceptable range, an exception is raised.
        """
        # 判断角度是否在 0~240度范围内
        if angle < 0 or angle > 240:
            raise ValueError("Angle must be in range 0~240.")

        # 判断时间是否在 0~30000 毫秒范围内
        if time_ms < 0 or time_ms > 30000:
            raise ValueError("Time must be in range 0~30000.")

        # 将角度转换为舵机控制指令所需的低八位和高八位
        # 转换为整数并限制为低8位
        angle_low = int(angle / 0.24) & 0xFF
        # 获取高8位
        angle_high = (int(angle / 0.24) >> 8) & 0xFF

        # 将时间转换为低八位和高八位
        # 转换为低8位
        time_low = time_ms & 0xFF
        # 获取高8位
        time_high = (time_ms >> 8) & 0xFF

        # 发送 SERVO_MOVE_TIME_WAIT_WRITE 指令来设置预设角度和时间
        self.send_command(servo_id, SerialServo.SERVO_MOVE_TIME_WAIT_WRITE[0], [angle_low, angle_high, time_low, time_high])

    def get_servo_move_with_time_delay(self, servo_id: int) -> tuple:
        """
        获取舵机的预设角度和时间（延迟转动）。
        该方法无法正常工作，还没排查出问题！

        该方法通过舵机ID发送 `SERVO_MOVE_TIME_WAIT_READ` 指令来读取舵机的预设角度和时间，
        然后延迟5ms，接收并解析返回的数据。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            tuple: 返回角度和时间的元组，角度范围 0~240度，时间范围 0~30000 毫秒。
                   如果读取失败，则返回 None。

        Raises:
            ValueError: 如果角度或时间值不在合理范围内，则抛出异常。

        ===================================================

        Get the preset angle and time of the servo (for delayed movement).
        This method is not functioning correctly, and the issue has not been identified yet!

        This method sends the `SERVO_MOVE_TIME_WAIT_READ` command using the servo ID to read the preset angle and time,
        then waits for 5ms before receiving and parsing the returned data.

        Args:
            servo_id (int): The ID of the servo.

        Returns:
            tuple: A tuple containing the angle and time. The angle range is 0 to 240 degrees, and the time range is 0 to 30,000 milliseconds.
                   Returns `None` if the reading fails.

        Raises:
            ValueError: If the angle or time values are out of the acceptable range, an exception is raised.
        """
        # TODO: TODO: 获取舵机的预设角度和时间（延迟转动）函数无法正常工作，还没排查出问题！

        # 抛出异常
        raise ValueError("This function is not working properly! You can use get_servo_move_immediate() instead.")

        # 发送SERVO_MOVE_TIME_WAIT_READ命令
        self.send_command(servo_id, SerialServo.SERVO_MOVE_TIME_WAIT_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_MOVE_TIME_WAIT_READ[0], SerialServo.SERVO_MOVE_TIME_WAIT_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析角度值，低8位和高8位合并为一个16位整数
        angle_value = params[0] + (params[1] << 8)
        # 将angle_value转换为角度值
        angle_value = angle_value * 0.24
        # 判断角度是否在合理范围内
        if angle_value < 0 or angle_value > 240:
            raise ValueError("Angle value is out of range.")

        # 解析时间值，低8位和高8位合并为一个16位整数
        time_value = params[2] + (params[3] << 8)
        # 判断时间是否在合理范围内
        if time_value < 0 or time_value > 30000:
            raise ValueError("Time value is out of range.")

        return angle_value, time_value

    def start_servo(self, servo_id: int) -> None:
        """
        启动舵机的转动。

        该方法发送 `SERVO_MOVE_START` 指令来启动舵机的转动。通常与 `SERVO_MOVE_TIME_WAIT_WRITE`
        指令配合使用，在舵机准备好后启动转动。

        Args:
            servo_id (int): 舵机ID，范围0~253。

        Raises:
            ValueError: 如果舵机ID不在 0~254 范围内，则抛出异常。

        ===================================================

        Start the servo's movement.

        This method sends the `SERVO_MOVE_START` command to initiate the servo's movement. Typically used in conjunction with the
        `SERVO_MOVE_TIME_WAIT_WRITE` command to start the movement after the servo is ready.

        Args:
            servo_id (int): The ID of the servo, range 0~253.

        Raises:
            ValueError: If the servo ID is not within the range of 0~253, an exception is raised.
        """
        # 发送启动转动指令
        self.send_command(servo_id, SerialServo.SERVO_MOVE_START[0], [])

    def stop_servo(self, servo_id: int) -> None:
        """
        立即停止舵机转动并停在当前角度位置。

        该指令发送到舵机后，如果舵机正在转动，就会立即停止转动。

        Args:
            servo_id (int): 舵机ID，范围0~253。

        Raises:
            ValueError: 如果舵机ID不在 0~254 范围内，则抛出异常。

        ====================================================

        Immediately stop the servo's movement and hold its current position.

        This command stops the servo's movement immediately when sent. If the servo is in motion, it will stop and hold its current position.

        Args:
            servo_id (int): The ID of the servo, range 0~253.

        Raises:
            ValueError: If the servo ID is not within the range of 0~253, an exception is raised.
        """
        self.send_command(servo_id, SerialServo.SERVO_MOVE_STOP[0], [])

    def set_servo_id(self, servo_id: int, new_id: int) -> None:
        """
        设置舵机的新ID值。

        该指令将舵机的ID值更改为指定的新ID，并且会掉电保存。

        Args:
            servo_id (int): 当前舵机ID，范围0~253。
            new_id (int): 需要修改后的新舵机ID，范围0~253。

        Raises:
            ValueError: 如果当前舵机ID或修改后的新舵机ID不在 0~254 范围内，则抛出异常。

        ====================================================

        Set the new ID value for the servo.

        This command changes the servo's ID to the specified new ID and saves it permanently after power cycle.

        Args:
            servo_id (int): The current servo ID, range 0~253.
            new_id (int): The new servo ID to be set, range 0~253.

        Raises:
            ValueError: If the current or new servo ID is not within the range of 0~253, an exception is raised.

        """

        # 判断新ID是否在 0~253 范围内
        if new_id < 0 or new_id > 253:
            raise ValueError("New ID must be in range 0~253.")

        self.send_command(servo_id, SerialServo.SERVO_ID_WRITE[0], [new_id])

    def get_servo_id(self, servo_id: int) -> int:
        """
        获取舵机的ID。

        该方法通过舵机ID发送 `SERVO_ID_READ` 指令来读取舵机的ID，返回舵机的实际ID值。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            int: 返回舵机ID，如果读取失败则返回 None。

        Raises:
            ValueError: 如果舵机ID不在 0~254 范围内，则抛出异常。

        ====================================================

        Get the servo's ID.

        This method sends the `SERVO_ID_READ` command using the servo ID to read the servo's actual ID and returns it.

        Args:
            servo_id (int): The ID of the servo.

        Returns:
            int: The servo's ID. If the read operation fails, returns None.

        Raises:
            ValueError: If the servo ID is not within the range of 0~253, an exception is raised.

        """
        # 发送SERVO_ID_READ命令
        self.send_command(servo_id, SerialServo.SERVO_ID_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_ID_READ[0], SerialServo.SERVO_ID_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 返回舵机ID
        servo_id_value = params[0]
        # 判断ID是否在合理范围内
        if servo_id_value < 0 or servo_id_value > 254:
            raise ValueError("Servo ID must be in range 0~254.")

        return servo_id_value

    def set_servo_angle_offset(self, servo_id: int, angle: float, save_to_memory: bool = False) -> None:
        """
        根据角度值调整舵机的偏差，并根据需要选择是否保存偏差值。

        如果需要保存偏差值，使用 `SERVO_ANGLE_OFFSET_WRITE` 指令，如果不需要保存，使用
        `SERVO_ANGLE_OFFSET_ADJUST` 指令。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            angle (float): 角度值，范围-30°~30°，用于调整偏差。
            save_to_memory (bool): 是否保存偏差值，True表示保存，False表示不保存，默认不保存。

        Raises:
            ValueError: 如果角度不在 -30°~30° 范围内，则抛出异常。

        =====================================================

        Adjust the servo's angle offset based on the provided angle, and choose whether to save the offset value.

        If the offset value needs to be saved, the `SERVO_ANGLE_OFFSET_WRITE` command is used. If not, the
        `SERVO_ANGLE_OFFSET_ADJUST` command is used.

        Args:
            servo_id (int): The ID of the servo, in the range of 0~253.
            angle (float): The angle value, in the range of -30°~30°, used to adjust the offset.
            save_to_memory (bool): Whether to save the offset value. True to save, False not to save (default is False).

        Raises:
            ValueError: If the angle is not within the range of -30°~30°, an exception will be raised.

        """
        # 判断偏差角度是否在 -30°~30° 范围内
        if angle < -30 or angle > 30:
            raise ValueError("Angle must be in range -30~30.")

        # 将角度转换为偏差值，偏差值的范围为-125到125，每0.24°对应一个偏差单位
        offset = int(angle / 0.24)

        # 强制转换偏差值为无符号字节
        offset = (offset + 256) % 256

        # 判断是否需要保存偏差值
        if save_to_memory:
            # 首先写入偏差值
            self.send_command(servo_id, SerialServo.SERVO_ANGLE_OFFSET_ADJUST[0], [offset])
            # 保存偏差值
            self.send_command(servo_id, SerialServo.SERVO_ANGLE_OFFSET_WRITE[0], [])
        else:
            self.send_command(servo_id, SerialServo.SERVO_ANGLE_OFFSET_ADJUST[0], [offset])

    def get_servo_angle_offset(self, servo_id: int) -> float:
        """
        获取舵机的偏差角度。

        该方法通过舵机ID发送 `SERVO_ANGLE_OFFSET_READ` 指令来读取舵机的偏差角度值，
        然后将读取到的无符号字节转换为有符号字节，计算出偏差角度（范围-30度到30度）。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            float: 返回舵机的偏差角度，单位为度，范围为 -30 到 30 度。
                   如果读取失败，则返回 None。

        Raises:
            ValueError: 如果偏差角度不在 -30°~30° 范围内，则抛出异常。

        ====================================================

        Retrieve the servo's angle offset.

        This method sends the `SERVO_ANGLE_OFFSET_READ` command using the servo's ID to read the servo's offset angle value,
        then converts the retrieved unsigned byte into a signed byte, and calculates the offset angle (in the range of -30° to 30°).

        Args:
            servo_id (int): The ID of the servo.

        Returns:
            float: The servo's offset angle in degrees, in the range of -30° to 30°.
                   If reading fails, returns None.

        Raises:
            ValueError: If the offset angle is not within the range of -30°~30°, an exception will be raised.

        """
        # 发送SERVO_ANGLE_OFFSET_READ命令
        self.send_command(servo_id, SerialServo.SERVO_ANGLE_OFFSET_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_ANGLE_OFFSET_READ[0], SerialServo.SERVO_ANGLE_OFFSET_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 获取偏差值（无符号字节，范围 0~255）
        offset_value = params[0]
        # 转换为有符号字节，范围为 -125 到 125
        if offset_value > 127:
            # 处理负值偏差
            offset_value -= 256

        # 将偏差值转换为角度范围 -30 到 30 度
        angle_offset = offset_value * (30 / 125.0)

        # 判断偏差角度是否在合理范围内
        if angle_offset < -30 or angle_offset > 30:
            raise ValueError("Angle offset must be in range -30~30.")

        return angle_offset

    def set_servo_angle_range(self, servo_id: int, min_angle: float, max_angle: float) -> None:
        """
        设置舵机的最小和最大角度限制，并支持掉电保存。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            min_angle (float): 最小角度，范围0~240°。
            max_angle (float): 最大角度，范围0~240°。

        Raises:
            ValueError: 如果最小或最大角度不在 0~240度范围内，则抛出异常。

        ====================================================

        Set the minimum and maximum angle limits of the servo, and support power cycle saving.

        Args:
            servo_id (int): The ID of the servo, in the range of 0~253.
            min_angle (float): The minimum angle, in the range of 0~240°.
            max_angle (float): The maximum angle, in the range of 0~240°.

        Raises:
            ValueError: If the minimum or maximum angle is not within the range of 0~240°, an exception will be raised.
        """

        # 判断最小和最大角度是否在 0~240度范围内
        if min_angle < 0 or min_angle > 240:
            raise ValueError("Angle must be in range 0~240.")

        if max_angle < 0 or max_angle > 240:
            raise ValueError("Angle must be in range 0~240.")

        # 判断最小和最大角度是否合理
        if min_angle >= max_angle:
            raise ValueError("Max angle must be greater than min angle.")

        # 将角度转换为指令所需的范围0~1000，表示0~240°，每0.24°对应一个单位
        min_value = int(min_angle / 0.24)
        max_value = int(max_angle / 0.24)

        # 取最大角度和最小角度的低八位和高八位
        min_value_low = min_value & 0xFF
        min_value_high = (min_value >> 8) & 0xFF

        max_value_low = max_value & 0xFF
        max_value_high = (max_value >> 8) & 0xFF

        # 生成指令包并发送
        self.send_command(servo_id, SerialServo.SERVO_ANGLE_LIMIT_WRITE[0], [min_value_low, min_value_high, max_value_low, max_value_high])

    def get_servo_angle_range(self, servo_id: int) -> tuple:
        """
        获取舵机的角度限位。

        该方法通过舵机ID发送 `SERVO_ANGLE_LIMIT_READ` 指令来读取舵机的角度限位值，
        然后将读取到的参数解析为最小角度和最大角度。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            tuple: 返回舵机的角度限位，最小角度和最大角度的元组，单位为度。
                   如果读取失败，则返回 None。

        Raises:
            ValueError: 如果最小或最大角度不在 0~240度范围内，则抛出异常。

        ====================================================

        Retrieve the servo's angle limits.

        This method sends the `SERVO_ANGLE_LIMIT_READ` command using the servo's ID to read the servo's angle limit values,
        then parses the retrieved parameters into minimum and maximum angles.

        Args:
            servo_id (int): The ID of the servo.

        Returns:
            tuple: A tuple containing the servo's angle limits, with the minimum and maximum angles in degrees.
                   If reading fails, returns None.

        Raises:
            ValueError: If the minimum or maximum angle is not within the range of 0°~240°, an exception will be raised.

        """
        # 发送SERVO_ANGLE_LIMIT_READ命令
        self.send_command(servo_id, SerialServo.SERVO_ANGLE_LIMIT_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_ANGLE_LIMIT_READ[0], SerialServo.SERVO_ANGLE_LIMIT_READ[2])
        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析最小角度值，低8位和高8位合并为一个16位整数
        min_angle = params[0] + (params[1] << 8)
        # 将min_angle转换为角度值
        min_angle = min_angle * 0.24
        # 判断最小角度是否在合理范围内
        if min_angle < 0 or min_angle > 240:
            raise ValueError("Angle must be in range 0~240.")

        # 解析最大角度值，低8位和高8位合并为一个16位整数
        max_angle = params[2] + (params[3] << 8)
        # 将max_angle转换为角度值
        max_angle = max_angle * 0.24
        # 判断最大角度是否在合理范围内
        if max_angle < 0 or max_angle > 240:
            raise ValueError("Angle must be in range 0~240.")

        # 判断最小角度是否小于最大角度
        if min_angle >= max_angle:
            raise ValueError("Min angle must be less than max angle.")

        return min_angle, max_angle

    def set_servo_vin_range(self, servo_id: int, min_vin: float, max_vin: float) -> None:
        """
        设置舵机的最小和最大输入电压限制，并支持掉电保存。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            min_vin (float): 最小输入电压，单位伏特，范围为4.5V ~ 12.0V。
            max_vin (float): 最大输入电压，单位伏特，范围为4.5V ~ 12.0V。

        Raises:
            ValueError: 如果最小或最大电压不在 4.5V~12.0V范围内，则抛出异常。

        =====================================================

        Set the minimum and maximum input voltage limits of the servo, and support power cycle saving.

        Args:
            servo_id (int): The ID of the servo, in the range of 0~253.
            min_vin (float): The minimum input voltage, in volts, in the range of 4.5V ~ 12.0V.
            max_vin (float): The maximum input voltage, in volts, in the range of 4.5V ~ 12.0V.

        Raises:
            ValueError: If the minimum or maximum voltage is not within the range of 4.5V~12.0V, an exception will be raised.
        """
        # 确保最小电压小于最大电压
        if min_vin >= max_vin:
            raise ValueError("Minimum voltage must be less than maximum voltage.")

        # 确保电压限制值在4.5V ~ 14.0V范围内
        if min_vin < 4.5 or min_vin > 14.0:
            raise ValueError("Voltage must be in range 4.5V ~ 14.0V.")

        if max_vin < 4.5 or max_vin > 14.0:
            raise ValueError("Voltage must be in range 4.5V ~ 14.0V.")

        # 将电压转换为毫伏，范围4500~12000 毫伏
        min_vin_mV = int(min_vin * 1000)
        max_vin_mV = int(max_vin * 1000)

        # 取出最小电压的低八位和高八位
        min_vin_low = min_vin_mV & 0xFF
        min_vin_high = (min_vin_mV >> 8) & 0xFF

        max_vin_low = max_vin_mV & 0xFF
        max_vin_high = (max_vin_mV >> 8) & 0xFF

        # 生成指令包并发送
        self.send_command(servo_id, SerialServo.SERVO_VIN_LIMIT_WRITE[0], [min_vin_low, min_vin_high,  max_vin_low, max_vin_high])

    def get_servo_vin_range(self, servo_id: int) -> tuple:
        """
        获取舵机的电压限制值。

        该方法通过舵机ID发送 `SERVO_VIN_LIMIT_READ` 指令来读取舵机的电压限制值，
        然后将返回的电压值转换为伏特单位。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            tuple: 返回舵机的最大和最小电压限制值，单位为伏特，范围为4.5V到14.0V。

        Raises:
            ValueError: 如果最小或最大电压不在 4.5V~14.0V范围内，则抛出异常。

        =====================================================

        Retrieve the servo's voltage limit values.

        This method sends the `SERVO_VIN_LIMIT_READ` command using the servo's ID to read the servo's voltage limit values,
        then converts the returned voltage values to units of volts.

        Args:
            servo_id (int): The ID of the servo.

        Returns:
            tuple: A tuple containing the servo's minimum and maximum voltage limits in volts,
                   with a range from 4.5V to 14.0V.

        Raises:
            ValueError: If the minimum or maximum voltage is not within the range of 4.5V~14.0V, an exception will be raised.

        """

        # 发送SERVO_VIN_LIMIT_READ命令
        self.send_command(servo_id, SerialServo.SERVO_VIN_LIMIT_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_VIN_LIMIT_READ[0], SerialServo.SERVO_VIN_LIMIT_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析最小电压值，低8位和高8位合并为一个16位整数
        min_vin = params[0] + (params[1] << 8)
        # 将min_vin转换为伏特单位
        min_vin = min_vin / 1000
        # 判断最小电压是否在合理范围内
        if min_vin < 4.5 or min_vin > 12.0:
            raise ValueError("Voltage must be in range 4.5V ~ 14.0V.")

        # 解析最大电压值，低8位和高8位合并为一个16位整数
        max_vin = params[2] + (params[3] << 8)
        # 将max_vin转换为伏特单位
        max_vin = max_vin / 1000
        # 判断最大电压是否在合理范围内
        if max_vin < 4.5 or max_vin > 14.0:
            raise ValueError("Voltage must be in range 4.5V ~ 14.0V.")

        # 判断最小电压是否小于最大电压
        if min_vin >= max_vin:
            raise ValueError("Min voltage must be less than max voltage.")

        return min_vin, max_vin

    def set_servo_temp_range(self, servo_id: int, max_temp: int) -> None:
        """
        设置舵机的最高温度限制，并支持掉电保存。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            max_temp (int): 最高温度限制，单位℃，范围50~100℃。

        Raises:
            ValueError: 如果温度限制不在 50~100℃范围内，则抛出异常。

        ======================================================

        Set the servo's maximum temperature limit, with optional power-off saving.

        Args:
            servo_id (int): The servo's ID, range from 0 to 253.
            max_temp (int): The maximum temperature limit in °C, with a range from 50°C to 100°C.

        Raises:
            ValueError: If the temperature limit is not within the range of 50°C to 100°C, an exception will be raised.
        """
        # 确保温度限制在有效范围内
        if max_temp < 50 or max_temp > 100:
            raise ValueError("Temperature must be between 50 and 100 degrees Celsius.")

        # 生成指令包并发送
        self.send_command(servo_id, SerialServo.SERVO_TEMP_MAX_LIMIT_WRITE[0], [int(max_temp) & 0xFF])

    def get_servo_temp_range(self, servo_id: int) -> int:
        """
        获取舵机的内部最高温度限制值。

        该方法通过舵机ID发送 `SERVO_TEMP_MAX_LIMIT_READ` 指令来读取舵机的最高温度限制值，
        然后将返回的值转换为摄氏度单位。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            int: 返回舵机的内部最高温度限制值，单位为摄氏度，范围50~100℃。
                 如果读取失败，则返回 None。

        Raises:
            ValueError: 如果温度限制不在 50~100℃范围内，则抛出异常。

        =====================================================

        Retrieve the servo's internal maximum temperature limit.

        This method sends the `SERVO_TEMP_MAX_LIMIT_READ` command using the servo's ID to read the servo's internal maximum temperature limit,
        then converts the returned value to degrees Celsius.

        Args:
            servo_id (int): The ID of the servo.

        Returns:
            int: The internal maximum temperature limit of the servo, in degrees Celsius, with a range from 50°C to 100°C.
                 If reading fails, returns None.

        Raises:
            ValueError: If the temperature limit is not within the range of 50°C to 100°C, an exception will be raised.

        """

        # 发送SERVO_TEMP_MAX_LIMIT_READ命令
        self.send_command(servo_id, SerialServo.SERVO_TEMP_MAX_LIMIT_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_TEMP_MAX_LIMIT_READ[0], SerialServo.SERVO_TEMP_MAX_LIMIT_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 获取最高温度限制值
        max_temp_limit = params[0]

        # 判断温度是否在合理范围内
        if not (50 <= max_temp_limit <= 100):
            raise ValueError("Temperature limit is out of range.")

        return max_temp_limit

    def read_servo_temp(self, servo_id: int) -> int:
        """
        获取舵机的实时温度。

        该方法通过舵机ID发送 `SERVO_TEMP_READ` 指令来读取舵机的当前内部温度。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            int: 返回舵机当前的温度值，单位为摄氏度。
                 如果读取失败，则返回 None。

        Raises:
            ValueError: 如果温度不在 0~100℃范围内，则抛出异常。

        ======================================================

        Get the real-time temperature of the servo.

        This method sends the `SERVO_TEMP_READ` command using the servo's ID to read the current internal temperature of the servo.

        Args:
            servo_id (int): The servo's ID.

        Returns:
            int: The current temperature value of the servo, in degrees Celsius.
                 If the read operation fails, it returns None.

        Raises:
            ValueError: If the temperature is not within the range of 0°C to 100°C, an exception will be raised.

        """
        # 发送SERVO_TEMP_READ命令
        self.send_command(servo_id, SerialServo.SERVO_TEMP_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_TEMP_READ[0], SerialServo.SERVO_TEMP_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 获取温度值
        temperature = params[0]

        # 判断温度是否在合理范围内
        if not (0 <= temperature <= 100):
            raise ValueError("Temperature is out of range.")

        return temperature

    def read_servo_voltage(self, servo_id: int) -> float:
        """
        获取舵机的实时输入电压。

        该方法通过舵机ID发送 `SERVO_VIN_READ` 指令来读取舵机的当前输入电压。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            float: 返回舵机当前的输入电压，单位为伏特，范围为 4.5V 到 12.0V。
                   如果读取失败，则返回 None。

        Raises:
            ValueError: 如果电压不在 4.5V~12.0V范围内，则抛出异常。

        ======================================================

        Get the real-time input voltage of the servo.

        This method sends the `SERVO_VIN_READ` command using the servo's ID to read the current input voltage of the servo.

        Args:
            servo_id (int): The servo's ID.

        Returns:
            float: The current input voltage of the servo, in volts, with a range of 4.5V to 12.0V.
                   If the read operation fails, it returns None.

        Raises:
            ValueError: If the voltage is not within the range of 4.5V to 12.0V, an exception will be raised.

        """
        # 发送SERVO_VIN_READ命令
        self.send_command(servo_id, SerialServo.SERVO_VIN_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_VIN_READ[0], SerialServo.SERVO_VIN_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 将电压值的低高字节合并成一个整数
        voltage_value = params[0] + (params[1] << 8)

        # 将电压值转换为伏特，电压范围 4.5V 到 12.0V
        voltage = voltage_value / 1000.0
        # 判断电压是否在合理范围内
        if not (4.5 <= voltage <= 12.0):
            raise ValueError("Voltage is out of range.")

        return voltage

    def read_servo_position(self, servo_id: int) -> float:
        """
        获取舵机的实时角度位置。

        该方法通过舵机ID发送 `SERVO_POS_READ` 指令来读取舵机的当前角度位置。
        返回的角度位置值需要根据范围 0~1000 映射到角度 0~240°。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            float: 返回舵机当前的角度位置值，单位为度，范围 0~240°。
                   如果读取失败，则返回 None。

        Raises:
            ValueError: 如果角度位置不在 0~240 度范围内，则抛出异常。

        =======================================================

        Get the real-time position of the servo.

        This method sends the `SERVO_POS_READ` command using the servo's ID to read the current angle position of the servo.
        The returned position value needs to be mapped from the range 0~1000 to the angle range 0~240°.

        Args:
            servo_id (int): The servo's ID.

        Returns:
            float: The current angle position of the servo, in degrees, with a range of 0~240°.
                   If the read operation fails, it returns None.

        Raises:
            ValueError: If the position is not within the range of 0~240°, an exception will be raised.

        """
        # 发送SERVO_POS_READ命令
        self.send_command(servo_id, SerialServo.SERVO_POS_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_POS_READ[0], SerialServo.SERVO_POS_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 将角度位置的低高字节合并为一个16位整数
        position_value = params[0] + (params[1] << 8)

        # 将值转换为 signed short int 型数据（可能为负值）
        # 判断是否为负值
        if position_value >= 0x8000:
            # 如果是负值，进行补码转换
            position_value -= 0x10000

        # 将位置值转换为角度值，映射到 0~240° 范围
        position_angle = (position_value / 1000) * 240

        # 判断角度值是否在合理范围内
        if not (0 <= position_angle <= 240):
            raise ValueError("Position is out of range.")

        return position_angle

    def set_servo_mode_and_speed(self, servo_id: int, mode: int, speed: int) -> None:
        """
        设置舵机的工作模式和电机转速，只有在电机控制模式下，转动速度才有效。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            mode (int): 舵机模式，0为位置控制模式，1为电机控制模式。
            speed (int): 转动速度值，范围-1000 ~ 1000，负值表示反转，正值表示正转。

        Raises:
            ValueError: 如果模式无效，或在电机控制模式下转动速度超出范围（-1000 ~ 1000），或模式和速度不匹配。

        =======================================================

        Set the servo's working mode and motor speed.

        This method sets the servo's working mode and motor speed.
        Only in motor control mode, the rotation speed is valid.

        Args:
            servo_id (int): The servo's ID, range from 0 to 253.
            mode (int): The servo's mode, 0 for position control mode, 1 for motor control mode.
            speed (int): The rotation speed value, range -1000 to 1000, negative value for reverse, positive value for forward.

        Raises:
            ValueError: If the mode is invalid, or the rotation speed is out of range (-1000 to 1000) in motor control mode,
                        or the mode and speed do not match.

        """
        # 检查模式是否合法
        if mode not in [SerialServo.MODE_POSITION, SerialServo.MODE_MOTOR]:
            raise ValueError("Invalid mode, must be SerialServo.MODE_POSITION or SerialServo.MODE_MOTOR.")

        # 如果是电机控制模式，检查转动速度是否合法
        if mode == SerialServo.MODE_MOTOR:
            if speed < -1000 or speed > 1000:
                raise ValueError("Speed must be between -1000 and 1000 in motor control mode.")
            # 转动速度转换为 unsigned short int 格式
            # 负数转换为补码形式
            if speed < 0:
                speed = (speed + 65536) % 65536

            # 取低八位数据和高八位数据
            low_byte = (speed & 0xFF)
            high_byte = ((speed >> 8) & 0xFF)
        else:
            # 在位置控制模式下，转动速度无效，设置为0
            low_byte = 0
            high_byte = 0

        # 发送指令
        self.send_command(servo_id, SerialServo.SERVO_OR_MOTOR_MODE_WRITE[0], [mode, 0, low_byte, high_byte])

    def get_servo_mode_and_speed(self, servo_id: int) -> tuple:
        """
        获取舵机的工作模式和转动速度。

        该方法通过舵机ID发送 `SERVO_OR_MOTOR_MODE_READ` 指令来读取舵机的工作模式及转动速度，
        然后解析返回的数据。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            tuple: 返回舵机的工作模式、转动速度（单位：转/分钟）。如果读取失败，则返回 None。

        Raises:
            ValueError: 如果模式无效，或在电机控制模式下转动速度超出范围（-1000 ~ 1000），或模式和速度不匹配。

        =========================================================

        Get the working mode and speed of the servo.

        This method sends the `SERVO_OR_MOTOR_MODE_READ` command via the servo's ID to read the working mode and rotation speed
        of the servo, then parses the returned data.

        Args:
            servo_id (int): The servo's ID.

        Returns:
            tuple: A tuple containing the servo's working mode and rotation speed (in RPM). If the read fails, it returns None.

        Raises:
            ValueError: If the mode is invalid, or if the speed exceeds the range (-1000 ~ 1000) in motor control mode,
            or if the mode and speed are incompatible.

        """
        # 发送SERVO_OR_MOTOR_MODE_READ命令
        self.send_command(servo_id, SerialServo.SERVO_OR_MOTOR_MODE_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_OR_MOTOR_MODE_READ[0], SerialServo.SERVO_OR_MOTOR_MODE_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析舵机模式，0 为位置控制模式，1 为电机控制模式
        mode = params[0]
        if mode not in [SerialServo.MODE_POSITION, SerialServo.MODE_MOTOR]:
            raise ValueError("Invalid servo mode.")

        # 如果是电机控制模式，返回速度值；如果是位置控制模式，返回速度值为0
        if mode == SerialServo.MODE_MOTOR:
            # 解析转动速度，低8位和高8位合并为一个16位整数
            speed_value = params[2] + (params[3] << 8)
            # 返回工作模式和转动速度
            return mode, speed_value
        else:
            return mode, 0

    def set_servo_motor_load(self, servo_id: int, unload: bool) -> None:
        """
        设置舵机的电机是否卸载掉电。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            unload (bool): 是否卸载掉电，True代表装载电机，False代表卸载掉电。

        Raises:
            ValueError: 如果舵机ID无效。

        =======================================================

        Set whether the servo motor is unloaded on power off.

        Args:
            servo_id (int): The servo's ID, range from 0 to 253.
            unload (bool): Whether to unload the motor on power off. True means load the motor, False means unload the motor.

        Raises:
            ValueError: If the servo ID is invalid.

        """
        # 卸载掉电 (0) 或装载电机 (1)
        unload_value = 1 if unload else 0

        # 生成指令并发送
        self.send_command(servo_id, SerialServo.SERVO_LOAD_OR_UNLOAD_WRITE[0], [unload_value])

    def get_servo_motor_load_status(self, servo_id: int) -> bool:
        """
        获取舵机电机是否装载或卸载。

        该方法通过舵机ID发送 `SERVO_LOAD_OR_UNLOAD_READ` 指令来读取舵机电机的状态，
        如果电机装载，返回 `True`，如果电机卸载，返回 `False`。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            bool: 返回舵机电机状态，`True` 表示电机已装载，`False` 表示电机已卸载。
                  如果读取失败，则返回 `None`。

        Raises:
            ValueError: 如果舵机ID无效。

        =========================================================

        Get the status of the servo motor.

        This method sends the `SERVO_LOAD_OR_UNLOAD_READ` command via the servo's ID to read the status of the servo motor,
        and returns `True` if the motor is loaded, and `False` if the motor is unloaded.

        Args:
            servo_id (int): The servo's ID.

        Returns:
            bool: Returns the status of the servo motor, `True` means the motor is loaded, and `False` means the motor is unloaded.
                  If the read fails, it returns `None`.

        """
        # 发送SERVO_LOAD_OR_UNLOAD_READ命令
        self.send_command(servo_id, SerialServo.SERVO_LOAD_OR_UNLOAD_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_LOAD_OR_UNLOAD_READ[0], SerialServo.SERVO_LOAD_OR_UNLOAD_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析电机状态，0表示卸载电机，1表示装载电机
        motor_status = params[0]
        if motor_status not in [0, 1]:
            raise ValueError("Invalid motor status value.")

        # 如果状态为1，则表示电机已装载，返回True；如果为0，则表示电机已卸载，返回False
        return motor_status == 1

    def set_servo_led(self, servo_id: int, led_on: bool) -> None:
        """
        设置舵机的LED灯的亮灭状态。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            led_on (bool): LED灯状态，True表示LED常灭，False表示LED常亮。

        Raises:
            ValueError: 如果舵机ID无效。

        ========================================================

        Set the status of the servo's LED.

        Args:
            servo_id (int): The servo's ID, range from 0 to 253.
            led_on (bool): The status of the LED, True means the LED is always off, False means the LED is always on.

        Raises:
            ValueError: If the servo ID is invalid.

        """

        # 设置LED灯的亮灭状态 (0为常亮，1为常灭)
        led_value = 1 if led_on else 0

        # 生成指令并发送
        self.send_command(servo_id, SerialServo.SERVO_LED_CTRL_WRITE[0], [led_value])

    def get_servo_led(self, servo_id: int) -> bool:
        """
        获取舵机LED的亮灭状态。

        该方法通过舵机ID发送 `SERVO_LED_CTRL_READ` 指令来读取舵机LED灯的状态，
        如果LED常灭，返回 `True`，如果LED常亮，返回 `False`。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            bool: 返回LED的状态，`True` 表示LED常灭，`False` 表示LED常亮。
                  如果读取失败，则返回 `None`。

        Raises:
            ValueError: 如果舵机ID无效或接受的LED状态错误则抛出异常。

        =========================================================

        Get the status of the servo's LED.

        This method sends the `SERVO_LED_CTRL_READ` command using the servo ID to read the LED status.
        If the LED is off, it returns `True`; if the LED is on, it returns `False`.

        Args:
            servo_id (int): The servo's ID.

        Returns:
            bool: Returns the LED status. `True` means the LED is off, `False` means the LED is on.
                  If the reading fails, it returns `None`.

        Raises:
            ValueError: If the servo ID is invalid or if the LED state is incorrect, an exception is raised.

        """
        # 发送SERVO_LED_CTRL_READ命令
        self.send_command(servo_id, SerialServo.SERVO_LED_CTRL_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_LED_CTRL_READ[0], SerialServo.SERVO_LED_CTRL_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析LED状态，0表示常亮，1表示常灭
        led_status = params[0]
        if led_status not in [0, 1]:
            raise ValueError("Invalid LED status value.")

        # 如果状态为1，则表示LED常灭，返回True；如果为0，则表示LED常亮，返回False
        return led_status == 1

    def set_servo_led_alarm(self, servo_id: int, alarm_code: int) -> None:
        """
        设置舵机LED闪烁报警对应的故障值。

        Args:
            servo_id (int): 舵机ID，范围0~253。
            alarm_code (int): 故障报警代码，范围0~7，对应不同的故障组合。

        Raises:
            ValueError: 如果报警代码或舵机ID无效，抛出异常。

        ==========================================================

        Set the servo LED flashing alarm corresponding to the fault code.

        This method sets the servo LED to flash in response to a specific fault code. The fault code
        corresponds to different fault combinations and is indicated by the LED flashing pattern.

        Args:
            servo_id (int): The servo's ID, in the range 0~253.
            alarm_code (int): The fault alarm code, in the range 0~7, representing different fault combinations.

        Raises:
            ValueError: If the alarm code or servo ID is invalid, an exception is raised.

        """

        # 检查报警代码是否在合法范围内
        if alarm_code not in [SerialServo.ERROR_NO_ALARM,
                              SerialServo.ERROR_OVER_TEMP,
                              SerialServo.ERROR_OVER_VOLT,
                              SerialServo.ERROR_OVER_TEMP_AND_VOLT,
                              SerialServo.ERROR_STALL,
                              SerialServo.ERROR_OVER_TEMP_AND_STALL,
                              SerialServo.ERROR_OVER_VOLT_AND_STALL,
                              SerialServo.ERROR_ALL]:

            raise ValueError("Invalid alarm code. Must be between 0 and 7.")

        # 生成指令包并发送
        self.send_command(servo_id, 35, [alarm_code])

    def get_servo_led_alarm(self, servo_id: int) -> int:
        """
        获取舵机LED故障报警状态。

        该方法通过舵机ID发送 `SERVO_LED_ERROR_READ` 指令来读取舵机的故障报警值，
        该值表示哪些故障导致LED闪烁报警，范围为0~7。

        Args:
            servo_id (int): 舵机的ID。

        Returns:
            int: 返回LED闪烁报警值，范围为0~7，表示舵机的故障类型。
                  如果读取失败，则返回 `None`。

        Raises:
            ValueError: 如果舵机ID无效或接受的LED状态错误则抛出异常。

        =============================================================

        Get the servo LED fault alarm status.

        This method sends the `SERVO_LED_ERROR_READ` command through the servo ID to read the fault alarm value
        from the servo. The returned value indicates which faults are causing the LED to flash. The range of
        the returned value is 0~7, with each bit representing a different fault type.

        Args:
            servo_id (int): The servo's ID.

        Returns:
            int: The LED flashing alarm value, in the range 0~7, representing the servo's fault type.
                 If reading fails, it returns `None`.

        Raises:
            ValueError: If the servo ID is invalid or the LED state is not acceptable, an exception is raised.

        """
        # 发送SERVO_LED_ERROR_READ命令
        self.send_command(servo_id, SerialServo.SERVO_LED_ERROR_READ[0], [])

        # 延迟5ms再接收数据
        time.sleep_ms(5)

        # 接收并解析返回的数据
        params = self.receive_command(SerialServo.SERVO_LED_ERROR_READ[0], SerialServo.SERVO_LED_ERROR_READ[2])

        # 如果没有接收到数据，则返回None
        if len(params) == 0:
            return None

        # 解析LED故障报警值
        error_alarm_value = params[0]

        # 判断值是否在合法范围内
        if error_alarm_value not in [SerialServo.ERROR_NO_ALARM,
                                     SerialServo.ERROR_OVER_TEMP,
                                     SerialServo.ERROR_OVER_VOLT,
                                     SerialServo.ERROR_OVER_TEMP_AND_VOLT,
                                     SerialServo.ERROR_STALL,
                                     SerialServo.ERROR_OVER_TEMP_AND_STALL,
                                     SerialServo.ERROR_OVER_VOLT_AND_STALL,
                                     SerialServo.ERROR_ALL]:

            raise ValueError("Error alarm value is out of range.")

        # 返回LED故障报警值
        return error_alarm_value

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================