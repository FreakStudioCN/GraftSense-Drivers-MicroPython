
# 串口舵机驱动 - MicroPython版本

## 目录
- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介
本项目提供了基于 MicroPython 的串口舵机驱动支持多种硬件平台（如树莓派 Pico）。  
舵机驱动支持多种控制功能，如角度控制、速度控制、温度监测等；
适用于机器人、智能设备等场景。

---

## 主要功能
### 舵机驱动
- **角度控制**：支持设置舵机角度范围（0~240°）。
- **速度控制**：支持电机模式下的速度调节。
- **状态监测**：支持实时读取舵机的角度、温度、电压等状态。
- **保护功能**：支持设置电压、温度等保护范围。

---

## 硬件要求

### 推荐测试硬件
- 树莓派 Pico/Pico W
- 舵机模块（支持串口控制）
- （可选）外接电源（用于大功率模块）

---

## 文件说明
### `serial_servo_driver.py`
#### 类定义
```python
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
```

### `main.py`
示例主程序，演示如何使用串口舵机驱动。

---

## 使用说明
### 硬件接线
#### 舵机接线
| 舵机引脚 | Pico GPIO引脚 |
|----------|-------------|
| VCC      | 5V          |
| GND      | GND         |
| TX       | 1           |
| RX       | 0           |


### 软件依赖
- **固件版本**：MicroPython v1.23+
- **内置库**：
  - `machine`（用于 GPIO 和 UART 控制）
  - `time`（用于延时）

### 安装步骤
1. 向树莓派 Pico 烧录 **MicroPython 固件**。
2. 将 `serial_servo_driver.py`、`atomization.py` 和 `main.py` 上传到 Pico。
3. 根据硬件连接修改 `main.py` 中的引脚配置。
4. 在开发工具中运行 `main.py` 开始测试。

---

## 示例程序
以下是一个简单的示例程序，演示如何控制舵机和雾化器：

```python
# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-        
# @Time    : 2025/1/3 下午11:00   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 串口类实验，通过串口控制串口舵机LX-1501转动

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import UART, Pin
# 时间相关的模块
import time
# 导入串口舵机库
from serial_servo import SerialServo

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

# 计时装饰器，用于计算函数运行时间
def timed_function(f: callable, *args: tuple, **kwargs: dict) -> callable:
    """
    计时装饰器，用于计算并打印函数/方法运行时间。

    Args:
        f (callable): 需要传入的函数/方法
        args (tuple): 函数/方法 f 传入的任意数量的位置参数
        kwargs (dict): 函数/方法 f 传入的任意数量的关键字参数

    Returns:
        callable: 返回计时后的函数
    """
    myname = str(f).split(' ')[1]

    def new_func(*args: tuple, **kwargs: dict) -> any:
        t: int = time.ticks_us()
        result = f(*args, **kwargs)
        delta: int = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta / 1000))
        return result

    return new_func

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using UART to control LX-1501 servo")

# 创建串口对象，设置波特率为115200
uart_servo = UART(0, 115200)
# 初始化uart对象，数据位为8，无校验位，停止位为1
# 设置串口超时时间为5ms
uart_servo.init(bits=8, parity=None, stop=1, tx=0, rx=1, timeout=5)

# 创建串口舵机对象
servo = SerialServo(uart_servo)

# 设置GPIO 25为LED输出引脚，下拉电阻使能
led = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# ========================================  主程序  ===========================================

# 立即移动舵机到指定位置
servo.move_servo_immediate(servo_id=1, angle=90.0, time_ms=1000)

# 获取舵机移动到指定位置后的角度和移动时间
angle, time = servo.get_servo_move_immediate(servo_id=1)
print(f"Servo ID: 1, Angle: {angle}, Time: {time}")
```

---

## 注意事项
### 舵机
- 确保舵机的供电电压稳定，避免电压波动。
- 设置合理的角度和速度范围，避免损坏舵机。
- 频繁切换可能会缩短舵机使用寿命。

---

## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 邮箱：10696531183@qq.com  
💻 GitHub：https://github.com/FreakStudioCN

---

## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (MIT)** 许可协议发布。

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  

**版权归 FreakStudio 所有。**