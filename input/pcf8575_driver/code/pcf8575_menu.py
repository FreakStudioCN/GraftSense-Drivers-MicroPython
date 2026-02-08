# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/25 下午3:02   
# @Author  : 李清水            
# @File    : main.py       
# @Description : I2C类实验，使用PCF8575芯片读取5D摇杆数据并控制OLED屏幕菜单

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import I2C, Pin
# 时间相关的模块
import time
# 导入自定义的PCF8575类
from pcf8575 import PCF8575
# 导入OLED屏幕相关模块
from SSD1306 import SSD1306_I2C
# 导入自定义OLED菜单库
from menu import SimpleOLEDMenu

# ======================================== 全局变量 ============================================

# PCF8575芯片地址
PCF8575_ADDRESS = 0
# OLED屏幕地址
OLED_ADDRESS = 0

# 五向按键的定义
KEYS = {
    0b1000000011111111 : "UP",
    0b0000100011111111 : "DOWN",
    0b0100000011111111 : "LEFT",
    0b0010000011111111 : "RIGHT",
    0b0001000011111111 : "CENTER"
}

# 记录当前按下的按键
current_key = None
# 变量值
value = 10
# 参数值
param = 0

# ======================================== 功能函数 ============================================

def led_on() -> None:
    """
    打开LED灯。

    Args:
        None

    Returns:
        None
    """
    # 声明全局变量
    global LED

    # 设为高电平，打开LED
    LED.value(1)
    print("LED ON")

def led_off() -> None:
    """
    关闭LED灯。

    Args:
        None

    Returns:
        None
    """
    # 声明全局变量
    global LED

    # 设为低电平，关闭LED
    LED.value(0)
    print("LED OFF")

def print_message() -> None:
    """
    OLED屏幕显示提示消息。

    Args:
        None

    Returns:
        None
    """
    # 声明全局变量
    global menu

    # 显示提示消息
    menu.show_message("No Sub Option")

def view_variable() -> None:
    """
    OLED屏幕显示变量值。

    Args:
        None

    Returns:
        None
    """
    # 声明全局变量
    global value

    # 显示变量值
    menu.show_message(f"Variable: {value}")

def set_parameter() -> None:
    """
    OLED屏幕显示参数值，并更新参数。

    Args:
        None

    Returns:
        None
    """
    # 声明全局变量
    global param

    # 假设设置参数的逻辑是将参数加1
    param += 1
    # 显示参数值
    menu.show_message(f"Parameter: {param}")

def detect_interrupt(pin : Pin) -> None:
    """
    中断处理函数，当PCF8575芯片端口的输入引脚状态发生改变时触发。

    Args:
        pin (machine.Pin): 中断引脚实例。

    Returns:
        None
    """

    # 声明全局变量
    global pcf8575, current_key, KEYS, menu

    # 如果触发后PCF8575芯片端口不为二进制的 0000000011111111
    if pcf8575.port != 255:
        # 打印PCF8575芯片端口状态
        print("PCF8575 Port: {:016b}".format(pcf8575.port))

        # 检查端口状态,判断哪个按键被按下
        for key, name in KEYS.items():
            # 如果端口状态与当前按键编码匹配
            if pcf8575.port == key:
                # 那么记录上一次按键按下的状态
                current_key = name
                # 打印调试信息
                print(f"Button {current_key} pressed")

                # 根据按键操作更新菜单
                if current_key == "UP":
                    # 向上选择菜单项
                    menu.select_up()
                elif current_key == "DOWN":
                    # 向下选择菜单项
                    menu.select_down()
                elif current_key == "LEFT":
                    # 向左返回上级菜单
                    menu.select_back()
                elif current_key == "RIGHT":
                    # 向右删除当前选中的菜单
                    menu.delete_menu(menu.head.sub_menu[menu.selected_index].name)
                elif current_key == "CENTER":
                    # 按下选择当前菜单项并进入
                    menu.select_current()

                # 打印当前选中的菜单项
                print("Select Menu: {}".format(menu.get_current_menu_name()))

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Read the status of 5D button by PCF8575")

# 设置GPIO 25为LED输出引脚，下拉电阻使能
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c_pcf8575 = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c_pcf8575.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 便利从机设备地址列表
    for device in devices_list:
        # 判断设备地址是否为PCF8575的地址
        if device >= 0x20 and device <= 0x27:
            print("PCF8575 hexadecimal address: ", hex(device))
            PCF8575_ADDRESS = device

# 创建PCF8575类实例,中断引脚为8，回调函数为detect_interrupt
pcf8575 = PCF8575(i2c_pcf8575, PCF8575_ADDRESS, interrupt_pin=Pin(8), callback=detect_interrupt)
pcf8575.port = 0x00FF

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c_oled = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c_oled.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 便利从机设备地址列表
    for device in devices_list:
        if device >= 0x3C and device <= 0x3D:
            print("OLED hexadecimal address: ", hex(device))
            OLED_ADDRESS = device

# 创建SSD1306 OLED屏幕的实例，宽度为128像素，高度为64像素，不使用外部电源
oled = SSD1306_I2C(i2c_oled, OLED_ADDRESS, 128, 64,False)

# 打印PCF8575各个端口状态
print("PCF8575 16 bits state: {:016b}".format(pcf8575.port))

# ========================================  主程序  ===========================================

# 创建菜单实例
menu = SimpleOLEDMenu(oled, "Main Menu", 0, 0, 128, 64)

# 添加主菜单选项
menu.add_menu("Option1")
menu.add_menu("Option2")
menu.add_menu("Option3")
menu.add_menu("Option4")
menu.add_menu("Option5")
menu.add_menu("Option6")
menu.add_menu("Option7")
menu.add_menu("Option8")
menu.add_menu("Option9")
menu.add_menu("Option10")
menu.add_menu("Option11")
menu.add_menu("Option12")
menu.add_menu("LED Option")
menu.add_menu("Variable Option",enter_callback=view_variable)
menu.add_menu("Parameter Option",enter_callback=set_parameter)

# 在Option1下添加子菜单
menu.add_menu("Sub Option1", parent_name="Option1", enter_callback=print_message)
menu.add_menu("Sub Option2", parent_name="Option1")
menu.add_menu("Sub Option3", parent_name="Option1")
menu.add_menu("Sub Option4", parent_name="Option1")
menu.add_menu("Sub Option5", parent_name="Option1")
menu.add_menu("Sub Option6", parent_name="Option1")
menu.add_menu("Sub Option7", parent_name="Option1")
menu.add_menu("Sub Option8", parent_name="Option1")

# 在LED Option下添加LED控制菜单
menu.add_menu("LED ON", parent_name="LED Option", enter_callback=led_on)
menu.add_menu("LED OFF", parent_name="LED Option", enter_callback=led_off)

# 更新显示菜单
menu.display_menu()

# 主循环
while True:
    # 延时1s
    time.sleep(0.5)
    # 更改变量值
    value = value + 1