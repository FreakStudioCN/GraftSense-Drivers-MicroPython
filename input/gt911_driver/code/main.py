# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/29 下午2:21   
# @Author  : 李清水            
# @File    : main.py       
# @Description : SPI类实验，LCD屏幕配合GT911触摸芯片完成键盘输入实验

# ======================================== 导入相关模块 ========================================

# 硬件相关的模块
from machine import Pin, SPI, I2C, Timer
from micropython import const
# 时间相关的模块
import time
# LCD屏幕相关的模块
from st7789 import ST7789
# 字库相关的模块
import vga1_16x32 as bigfont
import vga1_16x16 as mediumfont
import vga1_8x8   as smallfont
# 垃圾回收的模块
import gc
# 导入GT911触摸芯片相关模块
from gt911 import GT911

# ======================================== 全局变量 ============================================

# 触摸芯片地址为0x5D
GT911_ADDRESS = 0x5D
# 触摸状态标志变量，指示当前是否有触摸事件正在处理
touch_active = False
# 定义一个软件定时器，处理触摸事件
touch_timer = Timer(-1)
# 声明按钮1和按钮2
button1 = None
button2 = None

# ======================================== 功能函数 ============================================

def detect_touch(t: Timer) -> None:
    """
    读取触摸芯片的数据并处理触摸事件。

    该函数在触摸事件触发时被调用，首先读取触摸芯片的数据，然后判断是否有触摸点被按下，
    如果有，则根据触摸点的位置判断是否按下了按钮1或按钮2，并相应地控制LED和按钮状态。

    Args:
        t (Timer): 定时器实例，触发时用于调用此函数。

    Returns:
        None
    """
    # 声明全局变量
    global touch_active, touch_timer, button1, button2, LED

    # 读取触摸点数据
    touch_points, touches = gt911_dev.read_touch()

    # 如果没有正在处理的触摸事件
    if not touch_active:
        # 设置触摸状态为活动
        touch_active = True

        # 判断当前触摸点数量是否大于0
        if touch_points > 0:
            # 遍历每个触摸点
            for i in range(touch_points):
                id = i
                x = touches[i][0]
                y = touches[i][1]
                # 打印触摸点信息
                print("Touch ID:", id, "X:", x, "Y:", y)

            # 若是按钮1被按下
            if button1.is_touched(x, y):
                # 打开LED
                LED.on()
                # 改变LCD屏幕上按钮控件显示
                button1.press()

            # 若是按钮2被按下
            if button2.is_touched(x, y):
                # 关闭LED
                LED.off()
                # 改变LCD屏幕上按钮控件显示
                button2.press()

        # 启动定时器，延迟100ms重置状态标志
        touch_timer.init(period=100, mode=Timer.ONE_SHOT, callback=reset_touch)

def reset_touch(t: Timer) -> None:
    """
    重置触摸状态函数。

    该函数由定时器触发，用于重置触摸状态标志，表示可以处理新的触摸事件。同时释放按钮的状态。

    Args:
        t (Timer): 定时器实例，触发时用于调用此函数。

    Returns:
        None
    """
    # 声明全局变量
    global touch_active, button1, button2

    # 清除触摸状态标志，表示可以处理新的触摸事件
    touch_active = False
    # 按键释放
    button1.release()
    button2.release()

# ======================================== 自定义类 ============================================

# 自定义LCD类
class LCD(ST7789):
    """
    LCD类，继承自ST7789，提供增强的显示功能。

    该类扩展了ST7789的基础功能，增加了自定义颜色、字体大小控制、文本对齐显示、
    图形绘制以及嵌套的显示控件等功能，适用于需要复杂界面显示的嵌入式应用。

    Attributes:
        BLACK (int): 黑色 (0xFFFF)
        WHITE (int): 白色 (0x0000)
        MAGENTA (int): 品红色/浅紫色 (0x07E0)
        RED (int): 红色 (0x07FF)
        GREEN (int): 绿色 (0xF81F)
        BLUE (int): 蓝色 (0xFFE0)
        CYAN (int): 青色 (0xF800)
        YELLOW (int): 黄色 (0x001F)
        YEGR (int): 黄绿色 (0xFAEBD7)
        GATES (int): 品蓝色 (0x87CEEB)
        ANWHITE (int): 古董白 (0x191970)
        bigsize (int): 大字体尺寸 (32)
        mediumsize (int): 中等字体尺寸 (16)
        smallsize (int): 小字体尺寸 (8)

    Methods:
        __init__(self, spi, width, height, reset=None, dc=None, cs=None, backlight=None, rotation=0):
            初始化LCD屏幕。

        line_center_text(self, text, line, color=BLACK, size=bigsize):
            在一行中居中显示文字。

        line_left_text(self, text, line, color=BLACK, size=bigsize):
            在一行中居左显示文字。

        line_right_text(self, text, line, color=BLACK, size=bigsize):
            在一行中居右显示文字。

        circle(self, x, y, radius, color, fill=False):
            绘制圆形。

    Nested Classes:
        Button: 按钮控件
    """
    # 自定义颜色值
    BLACK   = const(0xFFFF)     # 黑色
    WHITE   = const(0x0000)     # 白色
    MAGENTA = const(0x07E0)     # 品红色/浅紫色
    RED     = const(0x07FF)     # 红色
    GREEN   = const(0xF81F)     # 绿色
    BLUE    = const(0xFFE0)     # 蓝色
    CYAN    = const(0xF800)     # 青色
    YELLOW  = const(0x001F)     # 黄色
    YEGR    = const(0xFAEBD7)   # 黄绿色
    GATES   = const(0x87CEEB)   # 品蓝色
    ANWHITE = const(0x191970)   # 古董白

    # 字体大小
    bigsize, mediumsize, smallsize = 32, 16, 8

    def __init__(self, spi: object, width: int, height: int, reset: object = None, dc: object = None, cs: object = None, backlight: object = None, rotation: int = 0) -> None:
        """
        初始化LCD屏幕。

        Args:
            spi (object): SPI类实例。
            width (int): 屏幕宽度。
            height (int): 屏幕高度。
            reset (object, optional): 复位引脚实例，默认为 None。
            dc (object, optional): 数据/命令引脚实例，默认为 None。
            cs (object, optional): 片选引脚实例，默认为 None。
            backlight (object, optional): 背光引脚实例，默认为 None。
            rotation (int, optional): 屏幕旋转角度，默认为 0。

        Returns:
            None
        """
        # 初始化ST7789，像素数据的顺序、选择角度使用默认值，使用内置的旋转命令
        super().__init__(spi, width, height, reset, dc, cs, backlight, rotation = rotation)

    def line_center_text(self, text: str, line: int, color: int = BLACK, size: int = bigsize) -> int:
        """
        在一行中居中显示文字。

        Args:
            text (str): 需要显示的字符串。
            line (int): 行数，即 y 坐标。
            color (int, optional): 文字颜色值，默认为黑色。
            size (int, optional): 字体大小，默认 32。

        Returns:
            int: 字体高度，用于下一行显示时 y 坐标的偏移量。

        Raises:
            ValueError: 如果字体大小不正确。
        """

        # 根据选用字体大小，获取字体宽度、高度
        if size == self.bigsize:
            font        = bigfont
            fontheight  = bigfont.HEIGHT
            fontwitdh   = bigfont.WIDTH
        elif size == self.mediumsize:
            font        = mediumfont
            fontheight  = mediumfont.HEIGHT
            fontwitdh   = mediumfont.WIDTH
        elif size == self.smallsize:
            font        = smallfont
            fontheight  = smallfont.HEIGHT
            fontwitdh   = smallfont.WIDTH
        else:
            raise ValueError("WRONG FONT SIZE")

        # 计算文字的x坐标
        x = int(self.width/2) - int(len(text)/2 * fontwitdh)
        self.text(font, text, x, line, color)

        return fontheight

    def line_left_text(self, text: str, line: int, color: int = BLACK, size: int = bigsize) -> int:
        """
        在一行中居左显示文字。

        Args:
            text (str): 需要显示的字符串。
            line (int): 行数，即 y 坐标。
            color (int, optional): 文字颜色值，默认为黑色。
            size (int, optional): 字体大小，默认 32。

        Returns:
            int: 字体高度，用于下一行显示时 y 坐标的偏移量。

        Raises:
            ValueError: 如果字体大小不正确。
        """

        # 根据选用字体大小，获取字体宽度
        if size == self.bigsize:
            font        = bigfont
            fontheight  = bigfont.HEIGHT
        elif size == self.mediumsize:
            font        = mediumfont
            fontheight  = mediumfont.HEIGHT
        elif size == self.smallsize:
            font        = smallfont
            fontheight  = smallfont.HEIGHT
        else:
            raise ValueError("WRONG FONT SIZE")

        self.text(font, text, 0, line, color)

        return fontheight

    def line_right_text(self, text: str, line: int, color: int = BLACK, size: int = bigsize) -> int:
        """
        在一行中居右显示文字。

        Args:
            text (str): 需要显示的字符串。
            line (int): 行数，即 y 坐标。
            color (int, optional): 文字颜色值，默认为黑色。
            size (int, optional): 字体大小，默认 32。

        Returns:
            int: 字体高度，用于下一行显示时 y 坐标的偏移量。

        Raises:
            ValueError: 如果字体大小不正确。
        """

        # 根据选用字体大小，获取字体宽度
        if size == self.bigsize:
            font        = bigfont
            fontheight  = bigfont.HEIGHT
            fontwitdh   = bigfont.WIDTH
        elif size == self.mediumsize:
            font        = mediumfont
            fontheight  = mediumfont.HEIGHT
            fontwitdh   = mediumfont.WIDTH
        elif size == self.smallsize:
            font        = smallfont
            fontheight  = smallfont.HEIGHT
            fontwitdh   = smallfont.WIDTH
        else:
            raise ValueError("WRONG FONT SIZE")

        self.text(font, text, self.width-len(text)*fontwitdh, line, color)

        return fontheight

    def circle(self, x: int, y: int, radius: int, color: int, fill: bool = False) -> None:
        """
        绘制一个圆。

        Args:
            x (int): 圆的中心点 x 坐标。
            y (int): 圆的中心点 y 坐标。
            radius (int): 圆的半径。
            color (int): 圆填充的颜色。
            fill (bool, optional): 是否填充，默认为 False。

        Returns:
            None
        """

        i, j = 0, 0

        if fill:
            # 存储点的列表
            pixel_list = []

        # 从圆心开始，以半径为步长，画圆
        while (i + j != radius) and (i + j != radius + 1):
            self.pixel(x + i, y + radius - j, color)
            self.pixel(x + i, y - radius + j, color)
            self.pixel(x - i, y + radius - j, color)
            self.pixel(x - i, y - radius + j, color)

            self.pixel(x + radius - j, y + i, color)
            self.pixel(x - radius + j, y + i, color)
            self.pixel(x + radius - j, y - i, color)
            self.pixel(x - radius + j, y - i, color)

            if fill:
                pixel_list.append((x + i, y + radius - j))
                pixel_list.append((x + i, y - radius + j))
                pixel_list.append((x - i, y + radius - j))
                pixel_list.append((x - i, y - radius + j))
                pixel_list.append((x + radius - j, y + i))
                pixel_list.append((x - radius + j, y + i))
                pixel_list.append((x + radius - j, y - i))
                pixel_list.append((x - radius + j, y - i))

            if 4 * (i + 1) ** 2 + (2 * radius - 2 * j + 1) ** 2 > 4 * radius ** 2:
                j += 1
            i += 1

        if fill:
            self.polygon(pixel_list, x, y, color = color)

    # 嵌套类，按钮控件
    class Button:
        """
        Button类，用于在LCD屏幕上创建和管理一个按钮控件。

        该类封装了一个按钮控件，按钮可以显示文本并支持触摸事件的响应。按钮可以在被按下时改变颜色，并提供按下和松开的状态切换功能。

        Attributes:
            lcd (LCD): LCD屏幕对象，用于绘制按钮。
            x (int): 按钮的左上角x坐标。
            y (int): 按钮的左上角y坐标。
            width (int): 按钮的宽度。
            height (int): 按钮的高度。
            text (str): 按钮上显示的文本。
            color (int): 按钮的默认颜色。
            pressed_color (int): 按钮被按下时的颜色。
            is_pressed (bool): 按钮的按下状态，初始为False。

        Methods:
            __init__(self, lcd, x, y, width, height, text, color, pressed_color):
                初始化Button类实例，设置按钮的显示属性和位置。

            draw(self):
                绘制按钮，如果按钮被按下则显示按下颜色，否则显示默认颜色。

            is_touched(self, touch_x, touch_y):
                判断触摸点是否在按钮范围内。

            press(self):
                设置按钮为按下状态，并重新绘制按钮。

            release(self):
                设置按钮为未按下状态，并重新绘制按钮。
        """
        def __init__(self, lcd_obj: 'LCD', x: int, y: int, width: int, height: int, text: str, color: int,
                     pressed_color: int) -> None:
            """
            初始化Button类实例，设置按钮的显示属性和位置。

            Args:
                lcd_obj (LCD): LCD屏幕对象，用于绘制按钮。
                x (int): 按钮的左上角x坐标。
                y (int): 按钮的左上角y坐标。
                width (int): 按钮的宽度。
                height (int): 按钮的高度。
                text (str): 按钮上显示的文本。
                color (int): 按钮的默认颜色。
                pressed_color (int): 按钮被按下时的颜色。
            """
            # 保存LCD实例
            self.lcd = lcd_obj

            # 保存按钮控件尺寸和位置信息
            self.x = x
            self.y = y
            self.width = width
            self.height = height

            # 按钮显示的文本
            self.text = text
            # 按钮的默认颜色
            self.color = color
            # 按钮被按下时的颜色
            self.pressed_color = pressed_color
            # 按钮的按下状态，初始为False
            self.is_pressed = False

            # 绘制按钮
            self.draw()

        def draw(self) -> None:
            """
            绘制按钮，显示按钮的文本及状态。

            Returns:
                None
            """
            # 如果按钮被按下，使用按下时的颜色
            if self.is_pressed:
                fill_color = self.pressed_color
            # 否则使用默认颜色
            else:
                fill_color = self.color

            # 绘制按钮矩形填充
            self.lcd.fill_rect(self.x, self.y, self.width, self.height, fill_color)
            # 绘制按钮的矩形边框
            self.lcd.rect(self.x, self.y, self.width, self.height, LCD.BLACK)

            # 计算文本位置并居中显示
            text_width = len(self.text) * 8
            # 计算文本的x坐标，使其在按钮中水平居中
            text_x = self.x + (self.width - text_width) // 2
            # 计算文本的y坐标，使其在按钮中垂直居中，假设文本高度为8像素
            text_y = self.y + (self.height - 8) // 2
            # 在按钮上绘制文本，使用小字体，文字颜色为黑色，背景为填充颜色
            self.lcd.text(smallfont, self.text, text_x, text_y, LCD.BLACK, fill_color)

        def is_touched(self, touch_x: int, touch_y: int) -> bool:
            """
            判断触摸点是否在按钮范围内。

            Args:
                touch_x (int): 触摸点的x坐标。
                touch_y (int): 触摸点的y坐标。

            Returns:
                bool: 如果触摸点在按钮范围内，返回True；否则返回False。
            """
            # 检查触摸点的x和y坐标是否在按钮的范围内
            return self.x <= touch_x <= self.x + self.width and self.y <= touch_y <= self.y + self.height

        def press(self) -> None:
            """
            按下按钮，设置按钮状态为按下，并重新绘制按钮。

            Returns:
                None
            """
            # 设置按钮为按下状态
            if not self.is_pressed:
                self.is_pressed = True
                # 重新绘制按钮，显示按下时的颜色
                self.draw()

        def release(self) -> None:
            """
            松开按钮，设置按钮状态为未按下，并重新绘制按钮。

            Returns:
                None
            """
            # 设置按钮为未按下状态
            if self.is_pressed:
                # 重新绘制按钮，恢复默认颜色
                self.is_pressed = False
                self.draw()

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print('FreakStudio : Using LCD with GT911 touch chip to complete keyboard input')

# 初始化SPI类，设置波特率、极性、相位、时钟引脚、数据引脚
spi = SPI(0, baudrate=10000000, polarity=0, phase=0, sck=Pin(6), mosi=Pin(7))
# 初始化LCD屏幕,并设置屏幕上下和左右都翻转
lcd = LCD(spi, 240, 320, reset=Pin(8), dc=Pin(9), cs=Pin(10), backlight=Pin(11),rotation = 2)

# 生成文本，offset为偏移量，用于下一行显示中y坐标的偏移量的确定
offset  = 0
offset  = lcd.line_center_text("Freak Studio", 0, lcd.RED, lcd.bigsize)
offset  = lcd.line_center_text("TORCHBEARERS OF CREATION", offset, lcd.MAGENTA, lcd.smallsize) + offset
offset  = lcd.line_center_text("Touch Keyboard Experiment", offset, lcd.BLACK, lcd.smallsize) + offset
# 绘制矩形填充
lcd.fill_rect(5,offset,230,265,LCD.YEGR)
# 绘制矩形边框
lcd.rect(5,offset,230,265,LCD.BLACK)

# 创建按键控件实例button1，位置为(10, offset + 20)，宽80，高20，显示文本"LED ON"，默认颜色为品蓝色，按下颜色为古董白
button1 = LCD.Button(lcd, 10, offset + 20, 80, 20, "LED ON",  LCD.GATES, LCD.ANWHITE)
# 创建按键控件实例button2，位置为(10, offset + 50)，宽80，高20，显示文本"LED OFF"，默认颜色为绿色，按下颜色为红色
button2 = LCD.Button(lcd, 10, offset + 50, 80, 20, "LED OFF", LCD.GREEN, LCD.RED)

# 创建硬件I2C的实例，使用I2C0外设，时钟频率为400KHz，SDA引脚为12，SCL引脚为13
i2c_gt911 = I2C(id=0, sda=Pin(12), scl=Pin(13), freq=400000)
# 创建GT911类实例，使用I2C1外设，地址为0x5D，同时最大支持触摸点数为2
gt911_dev = GT911(i2c_gt911, 15, 14, 0x14, touch_points = 5, reverse_x = True, reverse_y = True, user_callback = detect_touch)

# 设置GPIO 25为LED输出引脚，下拉电阻使能
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)

# ========================================  主程序  ============================================

# 无限循环
while True:
    # 延时1s
    time.sleep(1)
    # 当可用堆 RAM 的字节数小于 200000 时，手动触发垃圾回收功能
    if gc.mem_free() < 200000:
        # 手动触发垃圾回收功能
        gc.collect()