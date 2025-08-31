# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/8/27 下午10:02   
# @Author  : 李清水            
# @File    : main.py       
# @Description : ADC类实验，读取摇杆两端电压

# ======================================== 导入相关模块 ========================================

# 导入硬件模块
from machine import ADC, Timer, Pin, I2C
# 导入时间相关模块
import time
# 导入访问和控制 MicroPython 内部结构的模块
import micropython
# 导入ssd1306屏幕相关模块
from ssd1306 import SSD1306_I2C

# ======================================== 全局变量 ============================================

# OLED屏幕地址
OLED_ADDRESS = 0

# ======================================== 功能函数 ============================================

def user_callback(data: tuple) -> None:
    """
    用户自定义的回调函数，用于处理采集到的摇杆数据。

    Args:
        data (tuple): 包含摇杆的X轴、Y轴电压值和按键状态的元组，格式为 (x_value, y_value, sw_value)。

    Returns:
        None
    """
    # 声明全局变量
    global ball

    # 打印摇杆数据值
    x_value, y_value, sw_value = data
    print("X: {:.2f}, Y: {:.2f}, Switch: {}".format(x_value, y_value, sw_value))

    # 移动小球
    ball.move_ball(x_value,y_value)

# ======================================== 自定义类 ============================================

# 自定义摇杆类
class Joystick:
    """
    摇杆类，用于通过ADC引脚采集摇杆的X轴、Y轴电压值和按键状态。

    该类封装了ADC引脚和定时器的初始化，提供了启动、停止采集以及获取当前电压值的功能。
    支持通过用户自定义回调函数处理采集到的数据。

    Attributes:
        conversion_factor (float): 电压转换系数，用于将ADC的原始值转换为实际电压值。
        adc_x (ADC): X轴的ADC实例。
        adc_y (ADC): Y轴的ADC实例。
        sw (Pin): 按键的数字输入引脚实例。
        timer (Timer): 定时器实例，用于定期采集数据。
        freq (int): 定时器频率，单位为Hz。
        x_value (float): 当前采集到的X轴电压值。
        y_value (float): 当前采集到的Y轴电压值。
        sw_value (int): 当前采集到的按键状态（0或1）。
        callback (Optional[Callable[[tuple], None]]): 用户自定义的回调函数，用于处理采集到的数据。
        filter_alpha (float): 低通滤波系数。
        filtered_x (float): 滤波后的X轴电压值。
        filtered_y (float): 滤波后的Y轴电压值。

    Methods:
        __init__(self, vrx_pin: int, vry_pin: int, vsw_pin: int, freq: int = 100, callback=None):
            初始化摇杆类实例。
        start(self):
            启动摇杆数据采集。
        _timer_callback(self, timer: Timer):
            定时器回调函数，用于采集摇杆的X轴、Y轴和按键状态。
        stop(self):
            停止数据采集。
        get_values(self) -> tuple:
            获取当前摇杆的X轴、Y轴和按键状态。
    """

    # 电压转换系数
    conversion_factor = 3.3 / (65535)

    def __init__(self, vrx_pin: int, vry_pin: int, vsw_pin: int, freq: int = 100, callback: callable[[tuple], None] = None) -> None:
        """
        初始化摇杆类。

        Args:
            vrx_pin (int): X轴的ADC引脚编号。
            vry_pin (int): Y轴的ADC引脚编号。
            vsw_pin (int): 按键的数字输入引脚编号。
            freq (int): 定时器频率，默认为100Hz。
            callback (Optional[Callable[[tuple], None]]): 数据采集后的用户自定义回调函数。

        Returns:
            None
        """
        # 初始化ADC引脚
        self.adc_x = ADC(vrx_pin)
        self.adc_y = ADC(vry_pin)
        # 初始化按键引脚
        self.sw = Pin(vsw_pin, Pin.IN, Pin.PULL_UP)

        # 初始化定时器
        self.timer = Timer(-1)
        self.freq = freq

        # 保存采集到的值
        self.x_value = 0
        self.y_value = 0
        self.sw_value = 1

        # 引用用户自定义的回调函数
        self.callback = callback

        # 初始化滤波器参数
        # 低通滤波系数
        self.filter_alpha = 0.2
        # 初始值为中间值
        self.filtered_x = 1.55
        # 初始值为中间值
        self.filtered_y = 1.55

    def start(self) -> None:
        """
        启动摇杆数据采集。

        Args:
            None

        Returns:
            None
        """
        self.timer.init(period=int(1000/self.freq), mode=Timer.PERIODIC, callback=self._timer_callback)

    def _timer_callback(self, timer: Timer) -> None:
        """
        定时器回调函数，用于采集摇杆的X轴、Y轴和按键状态。

        Args:
            timer (Timer): 定时器对象。

        Returns:
            None
        """
        # 读取X轴和Y轴的ADC值
        raw_x = self.adc_x.read_u16() * Joystick.conversion_factor
        raw_y = self.adc_y.read_u16() * Joystick.conversion_factor
        # 低通滤波
        self.filtered_x = self.filter_alpha * raw_x + (1 - self.filter_alpha) * self.filtered_x
        self.filtered_y = self.filter_alpha * raw_y + (1 - self.filter_alpha) * self.filtered_y
        # 更新值
        self.x_value = self.filtered_x
        self.y_value = self.filtered_y

        # 读取按键状态，按下为0，未按下为1
        self.sw_value = self.sw.value()

        # 调用用户自定义回调函数，传递采集到的X轴、Y轴电压值和按键状态
        micropython.schedule(self.callback, (self.x_value, self.y_value, self.sw_value))

    def stop(self) -> None:
        """
        停止数据采集。

        Args:
            None

        Returns:
            None
        """
        self.timer.deinit()

    def get_values(self) -> tuple:
        """
        获取当前摇杆的X轴、Y轴和按键状态。

        Args:
            None

        Returns:
            tuple: 包含X轴、Y轴电压值和按键状态的元组，格式为 (x_value, y_value, sw_value)。
        """
        return self.x_value, self.y_value, self.sw_value

# 小球游戏类：通过输入坐标控制小球移动
class Ballgame:
    """
    小球游戏类，用于通过摇杆输入控制小球在OLED屏幕上移动。

    该类封装了小球的初始化、绘制和移动逻辑，支持通过摇杆输入控制小球的移动，并检测小球是否碰到矩形边框。

    Attributes:
        ball_x (int): 小球的X轴坐标。
        ball_y (int): 小球的Y轴坐标。
        ball_size (int): 小球的尺寸。
        rect_w (int): 矩形边框的宽度。
        rect_h (int): 矩形边框的高度。
        rect_x (int): 矩形边框的X轴坐标。
        rect_y (int): 矩形边框的Y轴坐标。
        oled (SSD1306_I2C): OLED屏幕实例。

    Methods:
        __init__(self, oled_obj: SSD1306_I2C, rect_x: int, rect_y: int, rect_w: int, rect_h: int):
            初始化小球游戏类。
        draw_ball(self):
            绘制小球。
        move_ball(self, x: float, y: float):
            根据摇杆输入移动小球。
    """
    def __init__(self, oled_obj: SSD1306_I2C, rect_x: int, rect_y: int, rect_w: int, rect_h: int) -> None:
        """
        初始化小球游戏类。

        Args:
            oled_obj (SSD1306_I2C): 使用的OLED屏幕实例。
            rect_x (int): 矩形边框的X轴坐标。
            rect_y (int): 矩形边框的Y轴坐标。
            rect_w (int): 矩形边框的宽度。
            rect_h (int): 矩形边框的高度。

        Returns:
            None
        """

        # 设定小球初始化参数：坐标、尺寸
        self.ball_x = rect_x + int(rect_w/2)
        self.ball_y = rect_y + int(rect_h/2)
        self.ball_size = 5

        # 设定矩形边框参数
        self.rect_w = rect_w
        self.rect_h = rect_h
        self.rect_x = rect_x
        self.rect_y = rect_y

        # 设定要显示的OLED屏幕对象
        self.oled = oled_obj

        # 绘制矩形框
        self.oled.rect(self.rect_x, self.rect_y, self.rect_w, self.rect_h, 1)
        # 绘制小球
        self.draw_ball()
        # 显示图像
        self.oled.show()

    def draw_ball(self) -> None:
        """
        绘制小球。

        Args:
            None

        Returns:
            None
        """
        self.oled.fill_rect(int(self.ball_x - self.ball_size), int(self.ball_y - self.ball_size),
                            self.ball_size * 2, self.ball_size * 2, 1)

    def move_ball(self, x: float, y: float) -> None:
        """
        移动小球。

        Args:
            x (float): 摇杆X轴的电压值。
            y (float): 摇杆Y轴的电压值。

        Returns:
            None
        """

        # 校正摇杆输入，使中间值接近 0
        x -= 1.55  # 偏移量为中间值 1.65V
        y -= 1.55  # 偏移量为中间值 1.65V

        # # 反转Y轴值
        # y = -y

        # 添加死区范围：当ADC值在死区范围内时，视为摇杆未操作，小球不移动
        dead_zone = 0.2
        if abs(x) < dead_zone:
            x = 0
        if abs(y) < dead_zone:
            y = 0

        # 限制摇杆值范围
        x = max(min(x, 1.55), -1.55)
        y = max(min(y, 1.55), -1.55)

        # 将电压值映射到小球速度的范围（例如 -4 到 4 像素/帧）
        speed_x = (x / 1.55) * 4  # 速度范围从 -4 到 4
        speed_y = (y / 1.55) * 4  # 速度范围从 -4 到 4

        # 根据摇杆值移动小球
        self.ball_x += speed_x
        self.ball_y += speed_y

        # 检测小球是否碰到矩形边框，如果碰到则反弹
        if self.ball_x - self.ball_size < self.rect_x or self.ball_x + self.ball_size > self.rect_x + self.rect_w:
            self.ball_x = max(self.rect_x + self.ball_size,
                              min(self.ball_x, self.rect_x + self.rect_w - self.ball_size))
        if self.ball_y - self.ball_size < self.rect_y or self.ball_y + self.ball_size > self.rect_y + self.rect_h:
            self.ball_y = max(self.rect_y + self.ball_size,
                              min(self.ball_y, self.rect_y + self.rect_h - self.ball_size))

        # 清屏并重新绘制矩形框和小球
        self.oled.fill_rect(self.rect_x, self.rect_y, self.rect_w, self.rect_h, 0)
        self.oled.rect(self.rect_x, self.rect_y, self.rect_w, self.rect_h, 1)
        self.draw_ball()
        # 显示小球
        self.oled.show()

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试信息
print("FreakStudio : reading the voltage value of Joystick experiment")

# 创建硬件I2C的实例，使用I2C0外设，时钟频率为400KHz，SDA引脚为4，SCL引脚为5
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
# 打印提示信息
print('OLED init success')

# (0,0)原点位置为屏幕左上角，右边为x轴正方向，下边为y轴正方向
# 显示文本
oled.text('Freak Studio', 0, 5)
oled.text('Joystick Test', 0, 15)
# 显示图像
oled.show()

# 创建摇杆实例，使用ADC0-GP26、ADC1-GP27作为Y轴和X轴，GP28 作为按键
joystick = Joystick(vrx_pin=0, vry_pin=1, vsw_pin=22, freq=10, callback=user_callback)

# 创建小球游戏类
ball = Ballgame(oled, 5,25,120,35)

# ========================================  主程序  ===========================================

# 启动摇杆数据采集
joystick.start()
# 运行一段时间，观察摇杆的状态
time.sleep(30)
# 停止数据采集
joystick.stop()
# 获取最后一次读取的摇杆值
x_val, y_val, sw_val = joystick.get_values()
print("Final Joystick values: X = {:.2f}, Y = {:.2f}, Switch = {}".format(x_val, y_val, sw_val))