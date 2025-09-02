# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/3 下午9:34   
# @Author  : 李清水            
# @File    : main.py       
# @Description : I2C类实验，主要完成读取串口陀螺仪数据后显示在OLED屏幕上

# ======================================== 导入相关模块 ========================================

# 从SSD1306模块中导入SSD1306_I2C类
from SSD1306 import SSD1306_I2C
# 从pcf8574模块中导入PCF8574类
from pcf8574 import PCF8574
# 硬件相关的模块
from machine import I2C, Pin
# 导入时间相关的模块
import time
# 系统相关的模块
import os

# ======================================== 全局变量 ============================================

# OLED屏幕地址
OLED_ADDRESS = 0
# IO扩展芯片地址
PCF8574_ADDRESS = 0

# IO扩展芯片外接按键映射定义
keys = {'UP': 4, 'DOWN': 1, 'LEFT': 2, 'RIGHT': 0, 'CENTER': 3}
sides = {'SET': 5, 'RST': 6}
# IO扩展芯片外接LED引脚编号
LED_PIN = 7

# ======================================== 功能函数 ============================================

def display_key(name: str) -> None:
    """
    在 OLED 屏幕上显示当前按下的按键名称。

    Args:
        name (str): 按键名称，例如 'UP', 'DOWN', 'SET' 等。

    Returns:
        None

    Notes:
        调用后会清空屏幕并更新显示。
        仅适用于已初始化的 OLED 对象。

    ==========================================

    Display the currently pressed key name on the OLED screen.

    Args:
        name (str): Key name, e.g., 'UP', 'DOWN', 'SET'.

    Returns:
        None

    Notes:
        Clears the OLED screen before updating.
        Only works with an initialized OLED object.
    """
    oled.fill(0)
    oled.text("Key:", 0, 0)
    oled.text(name, 0, 10)
    oled.show()

def handle_keys(port_value: int) -> None:
    """
    处理 PCF8574 读取到的按键端口值，判断按键状态并执行相应操作。
    优先检测普通方向键；若未检测到则检查 SET 和 RST 按键。

    Args:
        port_value (int): 从 PCF8574 读取的端口值，每一位对应一个引脚电平。

    Returns:
        None

    Notes:
        - 按键为高电平时表示按下。
        - SET 键会点亮 LED，RST 键会熄灭 LED。
        - 执行完成后会将所有按键引脚复位为低电平。

    ==========================================

    Handle key events from PCF8574 by checking pressed keys and executing actions.
    Normal keys have higher priority; if none pressed, check SET and RST keys.

    Args:
        port_value (int): Port value read from PCF8574, each bit maps to a pin level.

    Returns:
        None

    Notes:
        - Keys are active high (pressed when logic HIGH).
        - SET key turns on LED, RST key turns off LED.
        - All key pins are reset to LOW after handling.
    """
    # 按键为高电平表示按下
    for name, pin in keys.items():
        if (port_value >> pin) & 1:
            display_key(name)
            return

    # SET和RST处理
    if (port_value >> sides['SET']) & 1:
        # 点亮LED
        pcf8574.pin(LED_PIN, 0)
        display_key("SET")
    elif (port_value >> sides['RST']) & 1:
        # 熄灭LED
        pcf8574.pin(LED_PIN, 1)
        display_key("RST")

    # 将所有按键引脚置为低电平
    pcf8574.pin(0, 0)
    pcf8574.pin(1, 0)
    pcf8574.pin(2, 0)
    pcf8574.pin(3, 0)
    pcf8574.pin(4, 0)
    pcf8574.pin(5, 0)
    pcf8574.pin(6, 0)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试消息
print("FreakStudio: Testing OLED display and PCF8574-controlled LEDs & buttons")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 输出当前目录下所有文件
print('START LIST ALL FILES')
for file in os.listdir():
    print('file name:',file)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        print("I2C hexadecimal address: ", hex(device))
        if device == 0x3c or device == 0x3d:
            OLED_ADDRESS = device
        if 0x20 <= device <= 0x27:
            PCF8574_ADDRESS = device

# 创建SSD1306 OLED屏幕的实例，宽度为128像素，高度为64像素，不使用外部电源
oled = SSD1306_I2C(i2c, OLED_ADDRESS, 64, 32,False)
# 打印提示信息
print('OLED init success')

# 首先清除屏幕
oled.fill(0)
oled.show()
# (0,0)原点位置为屏幕左上角，右边为x轴正方向，下边为y轴正方向
# 绘制矩形外框
oled.rect(0, 0, 64, 32, 1)
# 显示文本
oled.text('Freak', 10, 5)
oled.text('Studio', 10, 15)
# 显示图像
oled.show()

# 创建PCF8574 IO扩展芯片的实例
pcf8574 = PCF8574(i2c, PCF8574_ADDRESS, int_pin=29, callback=handle_keys)
# 打印提示信息
print('PCF8574 init success')
# 设置PCF8574芯片的端口状态
pcf8574.port = 0x00

# ========================================  主程序  ============================================

while True:
    time.sleep(0.1)