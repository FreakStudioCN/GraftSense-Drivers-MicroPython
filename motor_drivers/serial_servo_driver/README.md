# 目录/MENU
- [中文部分](#串口舵机扩展板（FreakStudio-多米诺系列）示例程序-MicroPython版本)
- [English Section](#Signal-Generator-Expansion-Board-(FreakStudio-Domino-Series)-Example-Program-MicroPython-Version)

# 串口舵机扩展板（FreakStudio-多米诺系列）示例程序-MicroPython版本

该示例程序展示了如何使用MicroPython控制串口舵机扩展板（FreakStudio-多米诺系列）。通过串口通信，用户可以控制多个舵机的角度、速度等参数，实现高效、灵活的舵机控制。
程序中使用了串口通讯与舵机进行数据交互，提供了完整的控制命令和反馈解析功能。

该软件必须在提供的串口舵机扩展板（由FreakStudio开发设计）上运行，才能确保其正常工作。请参阅硬件开源链接和商品链接获取详细信息。
- **商品链接**：[**串口舵机驱动板购买链接**](https://item.taobao.com/item.htm?ft=t&id=884719978741&spm=a21dvs.23580594.0.0.4fee2c1bkqiSEB)
- **硬件开源链接**：[**硬件开源资料链接**](https://github.com/leezisheng/Domino-Series-Expansion-Board/tree/main/Serial-Servo-Driver-Board/hardware)

## 主要特性

- 使用UART串口与舵机通信，支持多舵机控制。
- 支持舵机的角度、速度、工作模式等多种设置。
- 支持舵机温度、电压、角度等实时读取。
- 校验和机制确保数据传输的完整性，幻尔科技串口舵机28条指令全部实现，并且封装为类。
- 完整的异常捕获机制，对入口参数进行详细检查。
- 注释完善，所有方法和类均提供了类型注解。

## 文件说明

### 主要类和方法介绍

#### `SerialServo` 类

该类封装了舵机控制相关的所有功能，包括生成和发送控制指令、接收舵机反馈、读取舵机状态等。

![UART_SERVO_Class](../../image/UART_SERVO_Class.png)

- `__init__(self, uart: UART) -> None`：初始化串口舵机控制类。
- `calculate_checksum(data: list[int]) -> int`：计算校验和，确保数据的完整性和正确性。
- `build_packet(servo_id: int, cmd: int, params: list[int]) -> bytearray`：构建舵机控制指令包。
- `send_command(servo_id: int, cmd: int, params: list[int] = []) -> None`：发送控制指令到指定舵机。
- `receive_command(expected_cmd: int, expected_data_len: int) -> list`：接收并解析舵机返回的指令数据包。
- `move_servo_immediate(servo_id: int, angle: float, time_ms: int) -> None`：立即控制舵机转动到指定角度。
- `get_servo_move_immediate(servo_id: int) -> tuple`：获取舵机的预设角度和时间。
- `move_servo_with_time_delay(servo_id: int, angle: float, time_ms: int) -> None`：控制舵机延迟转动到指定角度。
- `get_servo_move_with_time_delay(servo_id: int) -> tuple`：获取舵机的延迟转动角度和时间。
- `start_servo(servo_id: int) -> None`：启动舵机的转动。
- `stop_servo(servo_id: int) -> None`：立即停止舵机转动并停在当前角度位置。
- `set_servo_id(servo_id: int, new_id: int) -> None`：设置舵机的新 ID 值。
- `get_servo_id(servo_id: int) -> int`：获取舵机的 ID。
- `set_servo_angle_offset(servo_id: int, angle: float, save_to_memory: bool = False) -> None`：根据角度值调整舵机的偏差。
- `get_servo_angle_offset(servo_id: int) -> float`：获取舵机的偏差角度。
- `set_servo_angle_range(servo_id: int, min_angle: float, max_angle: float) -> None`：设置舵机的最小和最大角度限制。
- `get_servo_angle_range(servo_id: int) -> tuple`：获取舵机的角度限位。
- `set_servo_vin_range(servo_id: int, min_vin: float, max_vin: float) -> None`：设置舵机的最小和最大输入电压限制。
- `get_servo_vin_range(servo_id: int) -> tuple`：获取舵机的电压限制值。
- `set_servo_temp_range(servo_id: int, max_temp: int) -> None`：设置舵机的最高温度限制。
- `get_servo_temp_range(servo_id: int) -> int`：获取舵机的内部最高温度限制值。
- `read_servo_temp(servo_id: int) -> int`：获取舵机的实时温度。
- `read_servo_voltage(servo_id: int) -> float`：获取舵机的实时输入电压。
- `read_servo_pos(servo_id: int) -> float`：获取舵机的实时角度位置。
- `set_servo_mode_and_speed(servo_id: int, mode: int, speed: int) -> None`：设置舵机的工作模式和电机转速。
- `get_servo_mode_and_speed(servo_id: int) -> tuple`：获取舵机的工作模式和转动速度。
- `set_servo_motor_load(servo_id: int, unload: bool) -> None`：设置舵机的电机是否卸载掉电。
- `get_servo_motor_load_status(servo_id: int) -> bool`：获取舵机电机是否装载或卸载。
- `set_servo_led(servo_id: int, led_on: bool) -> None`：设置舵机的 LED 灯的亮灭状态。
- `get_servo_led(servo_id: int) -> bool`：获取舵机 LED 的亮灭状态。
- `set_servo_led_alarm(servo_id: int, alarm_code: int) -> None`：设置舵机 LED 闪烁报警对应的故障值。
- `get_servo_led_alarm(servo_id: int) -> int`：获取舵机 LED 故障报警状态。

### 核心方法介绍

该类的核心是通过 UART（串口通信）与舵机通信。类中的常量定义包括了多种控制命令和舵机相关的设置。这些常量包括了指令的编号、参数长度和返回数据长度。例如：

* `SERVO_MOVE_TIME_WRITE` 和 `SERVO_MOVE_TIME_READ` 是与舵机位置控制相关的指令及其参数格式。
* `SERVO_ID_WRITE` 和 `SERVO_ID_READ` 是与舵机ID相关的读写指令。

这些常量帮助类在进行通信时，能确保发送正确的指令和正确解析返回的数据。

`READ_COMMANDS` 集合定义了所有读取命令的编号，这些命令对应舵机的数据读取请求，例如，读取舵机的实时电压、角度、温度等信息。
这个集合便于在 `receive_command()` 方法中判断接收到的数据是否为期望的读取命令。

串口舵机类的核心方法为：
* **构建数据包方法 `build_packet`**：该方法用于构建舵机控制的指令包，指令包由以下部分组成：
  * **帧头**：固定为 0x55, 0x55
  * **舵机ID**：唯一标识每个舵机 
  * **数据长度**：包括指令和参数
  * **指令编号**：具体的控制指令
  * **参数**：控制指令的参数
  * **校验和**：用于校验数据包的完整性

![build_packet](../../image/build_packet.png)

* **发送指令方法 `send_command`**：该方法构建指令包并通过 `UART` 发送给舵机，它调用了` build_packet() `来构造数据包，
  并通过` self.uart.write() `发送数据。

![send_command](../../image/send_command.png)

* **接收指令方法 `receive_command`**：`receive_command() `方法用于接收来自舵机的反馈数据，此方法的工作过程如下：
  1. **命令验证**：确认接收到的是读取命令，而不是其他类型的命令。
  2. **数据检查**：检查数据的帧头是否正确，命令编号是否匹配，数据长度是否符合预期。
  3. **校验和验证**：验证接收到的数据包的校验和是否正确，确保数据未被篡改。
  4. **数据解析**：根据返回的数据长度，解析并返回舵机的状态或数据（例如电压、角度等）。
  5. 如果数据包无效（如校验和错误、数据长度不符等），该方法将返回空列表。
  
![receive_command](../../image/receive_command.png)

SerialServo 类的设计通过封装舵机控制指令和数据包的构建逻辑，简化了舵机通信过程，核心思路是通过统一的数据包格式和校验机制确保指令的正确传输，
结合 UART 通信接口实现与舵机的高效交互。类内指令常量和参数处理使得操作更加清晰易懂，
同时通过校验和和数据长度的验证确保数据的完整性和可靠性。

## 如何使用

### 安装依赖
在运行示例程序之前，确保你的环境中安装了`machine`和`time`等模块。你可以通过MicroPython的包管理器安装依赖。

1. 将该程序文件保存为 `serial_servo.py`。
2. 确保使用的主控板通过舵机驱动扩展板已连接好舵机和串口，接线供电无异常。
3. 在MicroPython环境中，通过`import serial_servo`导入该模块。

### 使用示例

```python
from machine import Pin, UART
from serial_servo import SerialServo

# 配置UART串口
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# 初始化串口舵机控制类
servo = SerialServo(uart)

# 控制舵机转到指定角度
servo.move_servo_immediate(servo_id=1, angle=90.0, time_ms=1000)

# 获取舵机的角度和时间设置
angle, time = servo.get_servo_move_immediate(servo_id=1)
print(f"Servo ID: 1, Angle: {angle}, Time: {time}")
```

## 注意事项
* **硬件连接**：确保舵机的电源和控制线正确连接
* **串口通信参数设置**：串口通信的波特率必须与舵机的波特率匹配，为115200，数据位为8，无校验位，停止位为1。
* **响应等待**：每次发送指令后，最好等待舵机响应，避免指令丢失。

## 结语
通过本示例程序，用户可以快速上手并实现对多个舵机的灵活控制。
此程序支持多种舵机控制模式，提供了强大的舵机状态读取功能，适合需要多舵机控制的项目需求。

该项目的代码已封装为软件包并发布至PyPI，您可以通过以下链接访问：
[serial-servo](https://pypi.org/project/serial-servo/)

## 联系开发者
- 如有任何问题或需要帮助，请通过 [10696531183@qq.com](mailto:10696531183@qq.com) 联系开发者。
  ![FreakStudio_Contact](../../../image/FreakStudio_Contact.png)

## 许可协议
本项目采用 **[知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)** 许可协议。

# Signal-Generator-Expansion-Board-(FreakStudio-Domino-Series)-Example-Program-MicroPython-Version

This example program demonstrates how to control the Serial Servo Expansion Board (FreakStudio - Domino Series) using MicroPython. Through serial communication, users can control multiple servos' angles, speeds, and other parameters, enabling efficient and flexible servo control. The program uses serial communication to exchange data with the servos, providing complete control commands and feedback parsing functionality.

The software must run on the provided serial servo expansion board (designed by FreakStudio) to ensure proper operation. Please refer to the hardware open-source link and product link for detailed information.
- **Product Link**: [**Serial Servo Driver Board Purchase Link**](https://item.taobao.com/item.htm?ft=t&id=884719978741&spm=a21dvs.23580594.0.0.4fee2c1bkqiSEB)
- **Hardware Open Source Link**: [**Hardware Open Source Resources Link**](https://github.com/leezisheng/Domino-Series-Expansion-Board/tree/main/Serial-Servo-Driver-Board/hardware)


## Main Features

- Use UART serial communication to control multiple servos.
- Supports various settings for servo angles, speeds, and operating modes.
- Real-time reading of servo temperature, voltage, angle, etc.
- Checksum mechanism ensures data transmission integrity, implements all 28 control commands of the Phantom Technology serial servo, and encapsulates them into a class.
- Complete exception handling mechanism with detailed checks for input parameters.
- Well-commented code, with all methods and classes annotated with type hints.

## File Description

### Main Classes and Methods Introduction

#### `SerialServo` Class

This class encapsulates all servo control functions, including generating and sending control commands, receiving feedback from the servo, and reading servo status.

![UART_SERVO_Class](../../image/UART_SERVO_Class.png)

- `__init__(self, uart: UART) -> None`: Initializes the serial servo control class.
- `calculate_checksum(data: list[int]) -> int`: Calculates the checksum to ensure data integrity and correctness.
- `build_packet(servo_id: int, cmd: int, params: list[int]) -> bytearray`: Constructs the servo control command packet.
- `send_command(servo_id: int, cmd: int, params: list[int] = []) -> None`: Sends a control command to the specified servo.
- `receive_command(expected_cmd: int, expected_data_len: int) -> list`: Receives and parses the servo's response command packet.
- `move_servo_immediate(servo_id: int, angle: float, time_ms: int) -> None`: Immediately moves the servo to the specified angle.
- `get_servo_move_immediate(servo_id: int) -> tuple`: Retrieves the preset angle and time of the servo.
- `move_servo_with_time_delay(servo_id: int, angle: float, time_ms: int) -> None`: Moves the servo to the specified angle after a delay.
- `get_servo_move_with_time_delay(servo_id: int) -> tuple`: Retrieves the delayed movement angle and time of the servo.
- `start_servo(servo_id: int) -> None`: Starts the servo's movement.
- `stop_servo(servo_id: int) -> None`: Immediately stops the servo's movement and keeps it at the current angle.
- `set_servo_id(servo_id: int, new_id: int) -> None`: Sets the new ID value for the servo.
- `get_servo_id(servo_id: int) -> int`: Retrieves the servo's ID.
- `set_servo_angle_offset(servo_id: int, angle: float, save_to_memory: bool = False) -> None`: Adjusts the servo's offset based on the angle value.
- `get_servo_angle_offset(servo_id: int) -> float`: Retrieves the servo's angle offset.
- `set_servo_angle_range(servo_id: int, min_angle: float, max_angle: float) -> None`: Sets the servo's minimum and maximum angle limits.
- `get_servo_angle_range(servo_id: int) -> tuple`: Retrieves the servo's angle limits.
- `set_servo_vin_range(servo_id: int, min_vin: float, max_vin: float) -> None`: Sets the servo's minimum and maximum input voltage limits.
- `get_servo_vin_range(servo_id: int) -> tuple`: Retrieves the servo's voltage limits.
- `set_servo_temp_range(servo_id: int, max_temp: int) -> None`: Sets the servo's maximum temperature limit.
- `get_servo_temp_range(servo_id: int) -> int`: Retrieves the servo's internal maximum temperature limit.
- `read_servo_temp(servo_id: int) -> int`: Reads the servo's real-time temperature.
- `read_servo_voltage(servo_id: int) -> float`: Reads the servo's real-time input voltage.
- `read_servo_pos(servo_id: int) -> float`: Reads the servo's real-time angle position.
- `set_servo_mode_and_speed(servo_id: int, mode: int, speed: int) -> None`: Sets the servo's operation mode and motor speed.
- `get_servo_mode_and_speed(servo_id: int) -> tuple`: Retrieves the servo's operation mode and speed.
- `set_servo_motor_load(servo_id: int, unload: bool) -> None`: Sets whether to unload the servo motor.
- `get_servo_motor_load_status(servo_id: int) -> bool`: Retrieves the servo motor load status.
- `set_servo_led(servo_id: int, led_on: bool) -> None`: Sets the servo's LED light state (on/off).
- `get_servo_led(servo_id: int) -> bool`: Retrieves the servo's LED light state.
- `set_servo_led_alarm(servo_id: int, alarm_code: int) -> None`: Sets the servo's LED flashing alarm for specific fault codes.
- `get_servo_led_alarm(servo_id: int) -> int`: Retrieves the servo's LED fault alarm status.

### Core Method Introduction

The core of this class is communication with the servo via UART (serial communication). Constants in the class define various control commands and servo-related settings. These constants include the command numbers, parameter lengths, and return data lengths. For example:

* `SERVO_MOVE_TIME_WRITE` and `SERVO_MOVE_TIME_READ` are commands related to servo position control.
* `SERVO_ID_WRITE` and `SERVO_ID_READ` are commands related to servo ID read/write operations.

These constants help ensure correct command sending and data parsing during communication.

The class's core methods include:
* **Packet Construction Method `build_packet`**: This method constructs the servo control command packet, consisting of the following parts:
  * **Frame Header**: Fixed as 0x55, 0x55
  * **Servo ID**: Uniquely identifies each servo
  * **Data Length**: Including the command and parameters
  * **Command Number**: The specific control command
  * **Parameters**: The control command's parameters
  * **Checksum**: Used to verify the integrity of the data packet

![build_packet](../../image/build_packet.png)

* **Send Command Method `send_command`**: This method constructs the command packet and sends it to the servo via `UART`. It calls `build_packet()` to create the data packet and sends the data through `self.uart.write()`.
  
![send_command](../../image/send_command.png)

* **Receive Command Method `receive_command`**: The `receive_command()` method is used to receive feedback data from the servo. The process includes:
  1. **Command Validation**: Ensures the received command is a read command.
  2. **Data Check**: Verifies the frame header, command number, and data length.
  3. **Checksum Validation**: Verifies the checksum to ensure the data hasn't been tampered with.
  4. **Data Parsing**: Parses and returns the servo's status or data (e.g., voltage, angle).
  5. If the data packet is invalid (e.g., checksum error, data length mismatch), the method returns an empty list.
  
![receive_command](../../image/receive_command.png)


The `SerialServo` class simplifies servo communication by encapsulating the control commands and packet-building logic. The core idea is to use a unified packet format and checksum mechanism to ensure the correct transmission of commands and efficient interaction with the servos via the UART interface. The class's command constants and parameter handling make operations clear and easy to follow, while checksum and data length validation ensure data integrity and reliability.

## Usage

### Install Dependencies
Before running the example program, make sure your environment has the necessary modules like `machine` and `time`. You can install dependencies via the MicroPython package manager.

1. Save the program file as `serial_servo.py`.
2. Ensure that your main controller board is properly connected to the servo driver expansion board, with the servo and serial connections correctly wired and powered.
3. In the MicroPython environment, import the module via `import serial_servo`.

### Usage Example

```python
from machine import Pin, UART
from serial_servo import SerialServo

# Configure UART serial port
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# Initialize serial servo control class
servo = SerialServo(uart)

# Move servo to the specified angle
servo.move_servo_immediate(servo_id=1, angle=90.0, time_ms=1000)

# Get the servo's angle and time settings
angle, time = servo.get_servo_move_immediate(servo_id=1)
print(f"Servo ID: 1, Angle: {angle}, Time: {time}")
```

## Notes
- **Hardware Connections**: Ensure that the servo's power and control lines are correctly connected.
- **Serial Communication Settings**: The baud rate of serial communication must match the servo's baud rate (115200), with 8 data bits, no parity bit, and 1 stop bit.
- **Response Wait**: After sending each command, it is advisable to wait for the servo's response to avoid losing the command.

## Conclusion
This example program allows users to quickly get started and achieve flexible control of multiple servos. 
It supports various servo control modes and provides powerful servo status reading functionality, 
making it suitable for projects requiring multiple servo control.

The code for this project has been packaged and published on PyPI. You can access it at the following link:
[serial-servo](https://pypi.org/project/serial-servo/)

## Contact the Developer
- For any inquiries or assistance, feel free to contact the developer at [10696531183@qq.com](mailto:10696531183@qq.com).
  ![FreakStudio_Contact](../../../image/FreakStudio_Contact.png)

## License

This project is licensed under the **[Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)**.