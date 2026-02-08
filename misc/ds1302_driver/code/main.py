# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/10/3 下午2:41   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 外置RTC类实验，使用DS1302实现闹钟

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import Pin, I2C, Timer, PWM, RTC
# 导入时间相关模块
import time
# 导入外部RTC实时时钟模块
from ds1302 import DS1302
# 从SSD1306模块中导入SSD1306_I2C类
from SSD1306 import SSD1306_I2C

# ======================================== 全局变量 ============================================

# OLED屏幕地址
OLED_ADDRESS = 0

# ======================================== 功能函数 ============================================

def display_time(timer: Timer) -> None:
    """
    定时器回调函数，用于在OLED屏幕上显示当前时间。

    该函数通过定时器周期性调用，从DS1302实时时钟芯片获取当前时间，
    并在OLED屏幕上居中显示日期和时间。同时，检查当前时间是否与设置的闹钟匹配，
    如果匹配则触发闹钟，否则停止闹钟蜂鸣器。

    Args:
        timer (Timer): Timer对象，用于周期性调用该函数。

    Returns:
        None
    """
    # 声明全局变量
    global ds1302, oled, alarm_clock

    # 获取当前时间
    current_time = ds1302.date_time()

    # 清空标题区域
    oled.fill_rect(0, 0, 128, 16, 0)

    # 显示标题
    title = "RTC Clock"
    title_width = len(title) * 8
    title_x = (128 - title_width) // 2
    oled.text(title, title_x, 0)

    # 格式化日期字符串
    date_str = "{:04}-{:02}-{:02}".format(current_time[0], current_time[1], current_time[2])
    # 计算位置以居中显示日期
    date_width = len(date_str) * 8
    date_x = (128 - date_width) // 2

    # 格式化时间字符串
    time_str = "{:02}:{:02}:{:02}".format(current_time[4], current_time[5], current_time[6])
    # 计算位置以居中显示时间
    time_width = len(time_str) * 8
    time_x = (128 - time_width) // 2

    # 清空日期和时间区域
    oled.fill_rect(0, 16, 128, 32, 0)

    # 显示日期和时间
    oled.text(date_str, date_x, 16)
    oled.text(time_str, time_x, 32)

    # 检查闹钟
    if alarm_clock.check_alarms(current_time):
        # 停止定时器
        timer.deinit()
        # 重新初始化定时器
        timer.init(period=100, mode=Timer.PERIODIC, callback=display_time)
    else:
        # 停止闹钟蜂鸣器
        alarm_clock.stop_alarm()
        # 刷新屏幕
        oled.show()

# ======================================== 自定义类 ============================================

# 自定义闹钟类
class AlarmClock:
    """
    AlarmClock类，用于管理闹钟功能，支持设置、删除和触发闹钟。

    该类通过OLED显示屏显示闹钟状态，并通过蜂鸣器发出闹钟提示音。
    支持设置多个闹钟，并在指定时间触发闹钟。

    Attributes:
        oled (SSD1306_I2C): OLED实例，用于显示闹钟状态。
        buzzer (PWM): 蜂鸣器控制引脚，用于发出提示音。
        alarms (list): 存储闹钟时间的列表，格式为[(小时, 分钟), ...]。

    Methods:
        __init__(self, oled: SSD1306_I2C, buzzer_pin: Pin) -> None:
            初始化AlarmClock类实例。

        set_alarm(self, hours: int, minutes: int) -> None:
            设置闹钟。

        delete_alarm(self, hours: int, minutes: int) -> None:
            删除指定的闹钟。

        check_alarms(self, current_time: tuple[int, int, int]) -> None:
            检查当前时间是否与设定的闹钟时间匹配。

        trigger_alarm(self) -> None:
            触发闹钟，打开蜂鸣器。

        stop_alarm(self) -> None:
            停止闹钟，关闭蜂鸣器。
    """
    def __init__(self, oled: SSD1306_I2C, buzzer_pin: Pin) -> None:
        """
        初始化闹钟类。

        Args:
            oled (SSD1306_I2C): OLED实例，用于显示闹钟状态。
            buzzer_pin (Pin): 蜂鸣器控制引脚。
        """
        # 保存OLED实例
        self.oled = oled
        # 初始化蜂鸣器引脚为PWM输出，占空比为0
        self.buzzer = PWM(buzzer_pin, freq=1000, duty_u16=0)
        # 存储闹钟时间的列表
        self.alarms = []

    def set_alarm(self, hours: int, minutes: int) -> None:
        """
        设置闹钟。

        Args:
            hours (int): 小时，范围为0-23。
            minutes (int): 分钟，范围为0-59。

        Returns:
            None

        Raises:
            ValueError: 如果小时或分钟不在合法范围内。
        """
        # 验证小时和分钟是否在合法范围内
        if (hours < 0 or hours > 23) or (minutes < 0 or minutes > 59):
            # 抛出异常
            raise ValueError("Invalid time for alarm")
            # 添加闹钟时间到列表
        self.alarms.append((hours, minutes))

    def delete_alarm(self, hours: int, minutes: int) -> None:
        """
        删除指定的闹钟。

        Args:
            hours (int): 小时。
            minutes (int): 分钟。

        Returns:
            None
        """
        try:
            # 从列表中删除指定的闹钟
            self.alarms.remove((hours, minutes))
        except ValueError:
            # 如果闹钟未找到，打印提示信息
            print("Alarm not found")

    def check_alarms(self, current_time: tuple[int, int, int]) -> None:
        """
        检查当前时间是否与设定的闹钟时间匹配。

        Args:
            current_time (tuple[int, int, int]): 当前时间的元组（小时，分钟，秒）。

        Returns:
            None
        """
        # 获取当前小时和分钟
        current_hours, current_minutes = current_time[4], current_time[5]
        # 遍历所有设置的闹钟
        for alarm in self.alarms:
            # 如果闹钟时间到达
            if alarm[0] == current_hours and alarm[1] == current_minutes:
                # 触发闹钟
                self.trigger_alarm()
                # 清空屏幕
                self.oled.fill(0)
                # 在屏幕上显示“Alarm!”提示
                self.oled.text("Alarm!", 0, 0)
                # 刷新屏幕
                self.oled.show()

    def trigger_alarm(self) -> None:
        """
        触发闹钟，打开蜂鸣器。

        Args:
            None

        Returns:
            None
        """
        # 打开蜂鸣器
        self.buzzer.duty_u16(32000)

    def stop_alarm(self) -> None:
        """
        停止闹钟，关闭蜂鸣器。

        Returns:
            None
        """
        # 关闭蜂鸣器
        self.buzzer.duty_u16(0)

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Implement an alarm clock using DS1302")

# 创建DS1302对象
ds1302 = DS1302(clk=Pin(10), dio=Pin(11), cs=Pin(12))

# 在烧录程序之前，务必使用 mpremote rtc --set 命令设置内置RTC实时时钟时间为电脑主机时间
# 接着打开REPL，输入下面命令：
#   from machine import Pin,  RTC
#   from ds1302 import DS1302
#   rtc = RTC()
#   year, month, day, weekday, hour, minute, second, _ = rtc.datetime()
#   ds1302 = DS1302(clk=Pin(10), dio=Pin(11), cs=Pin(12))
#   ds1302.date_time([year, month, day, weekday, hour, minute, second])
# 然后退出REPL模式，重启设备：mpremote reset

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 便利从机设备地址列表
    for device in devices_list:
        # 判断从机设备地址是否为0x3c或0x3d（即OLED SSD1306的地址）
        if device == 0x3c or device == 0x3d:
            print("I2C hexadecimal address: ", hex(device))
            OLED_ADDRESS = device

# 创建SSD1306 OLED屏幕的实例，宽度为128像素，高度为64像素，不使用外部电源
oled = SSD1306_I2C(i2c, OLED_ADDRESS, 128, 64,False)

# 创建闹钟实例
alarm_clock = AlarmClock(oled, buzzer_pin=Pin(9))
# 设置闹钟示例
alarm_clock.set_alarm(18, 3)

# 创建软件定时器实例
timer = Timer(-1)
# 每100ms调用一次display_time函数更新显示
timer.init(period=100, mode=Timer.PERIODIC, callback=display_time)

# ========================================  主程序  ============================================

# 无限循环检查闹钟是否到达
while True:
    # 获取当前时间
    current_time = ds1302.date_time()
    # 延时1s
    time.sleep(1)
    # 打印当前时间
    print("Current Time: {:02}:{:02}:{:02}".format( current_time[4], current_time[5], current_time[6]))