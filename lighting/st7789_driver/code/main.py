# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/6 上午10:34
# @Author  : 李清水
# @File    : main.py
# @Description : SPI类实验，使用SPI类实现LCD屏的显示
# 字库文件和ST7789驱动文件参考
# 参考russhughes st7789py_mpy：https://github.com/russhughes/st7789py_mpy/blob/master/lib/st7789py.py

# ======================================== 导入相关模块 ========================================

# 硬件相关的模块
from machine import Pin, SPI, UART
# MicroPython相关模块
from micropython import const
# 时间相关的模块
import time
# LCD屏幕相关的模块
from st7789 import ST7789
# 字库相关的模块
import vga1_16x32 as bigfont
import vga1_16x16 as mediumfont
import vga1_8x8   as smallfont
# 陀螺仪相关的模块
from IMU import IMU
# 垃圾回收的模块
import gc

# ======================================== 全局变量 ============================================

# 用于记录IMU串口陀螺仪串口接收数据次数
IMU_RECV_COUNT = 0

# ======================================== 功能函数 ============================================

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
        VarShow: 变量显示控件
        waveformShow: 波形显示控件
        InfoShow: 调试信息显示控件
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

    # 嵌套类，变量显示控件
    class VarShow:
        """
        VarShow类，用于在LCD屏幕上显示变量名和值，并提供更新和删除显示内容的功能。

        该类封装了一个变量显示控件，用于在指定位置绘制变量名和值，并支持实时更新显示的变量值。
        可以通过调用update方法更新变量值，并通过delete方法清除显示内容。

        Attributes:
            name (str): 变量的名称，显示在LCD上的文本。
            value (int): 变量的值，显示在LCD上的数值。
            x (int): 控件的起始x坐标，用于定位LCD屏幕上控件的位置。
            y (int): 控件的起始y坐标，用于定位LCD屏幕上控件的位置。
            LCD_obj (LCD): LCD屏幕对象，用于绘制图形和文本。

        Methods:
            __init__(self, name, value, x, y, lcd_obj):
                初始化VarShow类实例，设置变量名、值以及显示位置。

            update(self, value):
                更新控件中的变量值，并重新绘制变量值。

            delete(self):
                清除变量显示控件的内容，恢复为背景色。
        """
        def __init__(self, name: str, value: int, x: int, y: int, lcd_obj: 'LCD') -> None:
            """
            变量显示控件，用于显示变量名和值。

            Args:
                name (str): 变量名。
                value (int): 变量的初始值。
                x (int): 变量显示框的起始x坐标。
                y (int): 变量显示框的起始y坐标。
                lcd_obj (LCD): LCD屏幕对象，用于在屏幕上绘制显示内容。

            Raises:
                ValueError: 如果变量名或变量值的长度超出限制，抛出此异常。
            """

            if len(name)*smallfont.WIDTH > 70:
                raise ValueError("NAME LENGTH MUST LESS THAN 8")

            if len(str(value))*smallfont.WIDTH > 30:
                raise ValueError("VALUE LENGTH MUST LESS THAN 7")

            self.name = name
            self.value = value
            self.x = x
            self.y = y
            # 嵌套类是不能直接使用外部类的属性和方法
            # 通过传递外部类的实例作为参数或通过其他方式将外部类的属性传递给嵌套类
            self.LCD_obj = lcd_obj

            # 绘制变量显示控件的矩形边框
            self.LCD_obj.rect(self.x, self.y, 100, 14, LCD.BLACK)
            # 绘制变量名，字体颜色为黑色，背景颜色为青色
            self.LCD_obj.text(smallfont, self.name+':', self.x+2, self.y+2, LCD.BLACK,LCD.CYAN)
            # 绘制变量值，字体颜色为黑色，背景颜色为白色
            self.LCD_obj.text(smallfont, str(self.value), self.x+int(len(self.name)*smallfont.WIDTH)+2, self.y+2, LCD.BLACK)

        def update(self, value: int) -> None:
            """
            更新显示控件中的变量值。

            Args:
                value (int): 待更新的变量值。

            Returns:
                None
            """

            # 清除原先变量值
            self.LCD_obj.fill_rect(self.x+int(len(self.name)*smallfont.WIDTH)+2, # 变量值起始点x坐标
                                   self.y+2,                                     # 变量值起始点y坐标
                                   95-int(len(str(self.name))*smallfont.WIDTH),  # 变量值宽度
                                   smallfont.HEIGHT,                             # 变量值高度
                                   LCD.WHITE                                     # 填充白色
                                   )
            # 绘制变量值，字体颜色为黑色，背景颜色为白色
            self.LCD_obj.text(smallfont, str(value), self.x + int(len(self.name) * smallfont.WIDTH) + 10, self.y + 2, LCD.BLACK)

        def delete(self) -> None:
            """
            清除变量显示控件。

            Returns:
                None
            """
            # 绘制白色填充矩形，将LCD上变量显示控件清除
            # 无需对创建的实例进行del销毁，使用gc模块的自动垃圾清除即可
            self.LCD_obj.fill_rect(self.x, self.y, 100, 14, LCD.WHITE)

    # 嵌套类，变量波形显示控件
    class waveformShow:
        """
        WaveformShow类，用于在LCD屏幕上显示波形数据，并支持实时更新显示。

        该类实现了波形显示控件的创建与管理，包含了绘制坐标轴、更新波形数据、清除波形显示等功能。
        波形数据通过一系列数据点进行展示，数据点会在屏幕上按比例映射为坐标，形成波形图。

        Attributes:
            x (int): 波形显示控件左上角的x坐标。
            y (int): 波形显示控件左上角的y坐标。
            width (int): 波形显示控件的宽度。
            height (int): 波形显示控件的高度。
            title (str): 波形显示控件的标题。
            LCD_obj (LCD): LCD屏幕对象，用于在屏幕上绘制内容。
            formwidth (int): 波形坐标图的宽度（控件宽度减去边距）。
            formheight (int): 波形坐标图的高度（控件高度减去边距）。
            formx (int): 波形坐标图的x坐标（控件内的起始坐标）。
            formy (int): 波形坐标图的y坐标（控件内的起始坐标）。
            lastdata_y (int): 上一个数据点的y坐标位置。
            nowdata_y (int): 当前数据点的y坐标位置。
            count (int): 当前数据点的计数，表示已绘制的数据点数量。

        Methods:
            __init__(self, x: int, y: int, width: int, height: int, title: str, LCD_obj: LCD):
                初始化WaveformShow类实例，设置控件位置、尺寸、标题及LCD对象。

            setaxis(self):
                绘制波形显示控件的坐标轴。

            update(self, value: int, max_value: int, color: int):
                更新波形显示控件，绘制新数据点。

            delete(self):
                清除波形显示控件，重绘白色矩形覆盖整个区域。
        """

        def __init__(self, x: int, y: int, width: int, height: int, title: str, lcd_obj: 'LCD') -> None:
            """
            初始化WaveformShow类实例，设置控件位置、尺寸、标题及LCD对象。

            Args:
                x (int): 波形显示控件左上角的x坐标。
                y (int): 波形显示控件左上角的y坐标。
                width (int): 波形显示控件的宽度。
                height (int): 波形显示控件的高度。
                title (str): 波形显示控件的标题。
                LCD_obj (LCD): LCD屏幕对象，用于在屏幕上绘制内容。

            Raises:
                ValueError: 如果波形显示控件的宽度或高度不是10的倍数，抛出此异常。
            """

            # 判断波形显示控件宽高是否为10的倍数
            if width % 10 != 0 or height % 10 != 0:
                raise ValueError("WIGHT MUST BE DIVIDED BY 10")

            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.title = title
            self.LCD_obj = lcd_obj

            # 波形坐标图的长宽和横纵坐标
            self.formwidth  = width - 10
            self.formheight = height - 25
            self.formx      = self.x+5
            self.formy      = self.y+10

            # 存储上一个数据的y轴坐标点位置
            self.lastdata_y = self.formy + self.formheight
            # 存储当前数据的y轴坐标点位置
            self.nowdata_y  = 0
            # 记录当前数据点数
            self.count      = 0

            # 绘制波形显示控件矩形填充
            self.LCD_obj.fill_rect(self.x, self.y, self.width, self.height, LCD.CYAN)
            # 绘制波形显示控件矩形边框
            self.LCD_obj.rect(self.x, self.y, self.width, self.height, LCD.BLACK)
            # 绘制标题，字体颜色为黑色，背景颜色为红色，标题位置在中间
            self.LCD_obj.text(smallfont, self.title, int(self.width/2)-int(len(self.title)/2 * smallfont.WIDTH), self.y+2, LCD.BLACK,LCD.RED)
            # 绘制坐标轴
            self.setaxis()

        def setaxis(self) -> None:
            """
            绘制波形显示控件的坐标轴。

            Args:
                None

            Returns:
                None
            """

            # 垂直于x轴的线段个数
            x_line_number = int(self.formwidth/5)
            # 垂直于y轴的线段个数
            y_line_number = int(self.formheight/5)

            # 绘制垂直于x轴的线段
            for i in range(x_line_number+1):
                # 绘制垂直于x轴的线段
                self.LCD_obj.vline(self.formx+i*5, self.formy, self.formheight, LCD.BLACK)

            # 绘制垂直于y轴的线段
            for i in range(y_line_number+1):
                # 绘制垂直于y轴的线段
                self.LCD_obj.hline(self.formx, self.formy+i*5, self.formwidth, LCD.BLACK)

            # 绘制原点字符串
            self.LCD_obj.text(smallfont, "(0,0)", self.formx, self.formy+self.formheight+2, LCD.RED,LCD.CYAN)
            # 在原点绘制一个红色填充圆
            self.LCD_obj.circle(self.formx, self.formy+self.formheight, 4, LCD.RED, True)

        def update(self, value: int, max_value: int, color: int) -> None:
            """
            更新波形显示控件，绘制新数据点。

            Args:
                value (int): 待更新数据的值。
                max_value (int): 数据的最大值，用于归一化显示。
                color (int): 绘制波形的颜色。

            Raises:
                ValueError: 如果数据值大于最大值，抛出此异常。

            Returns:
                None
            """

            # 若是数据大于数据最大范围值，则抛出异常
            if value > max_value:
                raise ValueError("VALUE MUST BE LESS THAN MAX_VALUE")

            # 若数据点数超过控件宽度，则清空曲线，重新绘图
            if self.count == int(self.formwidth/5):
                self.LCD_obj.fill_rect(self.formx, self.formy, self.formwidth, self.formheight, LCD.WHITE)
                # 重新设置坐标轴
                self.setaxis()
                # 计数值清零
                self.count = 0

            # 需要画的点距离waveformShow控件中formy的偏移量
            pixel_y_offset = int(value/max_value * self.formheight)

            # 绘制点
            if pixel_y_offset >= int(self.formheight/2):
                self.nowdata_y = self.formy + (self.formheight - pixel_y_offset)
            else:
                self.nowdata_y = self.formy + self.formheight - pixel_y_offset

            self.LCD_obj.line(self.formx+self.count*5, self.lastdata_y, self.formx+(self.count+1)*5, self.nowdata_y, color)
            self.lastdata_y = self.nowdata_y
            self.count += 1

        def delete(self) -> None:
            """
            清除波形显示控件，重绘白色矩形覆盖整个区域。

            Args:
                None

            Returns:
                None
            """
            # 绘制白色填充矩形，将LCD上波形显示控件
            # 无需对创建的实例进行del销毁，使用gc模块的自动垃圾清除即可
            self.LCD_obj.fill_rect(self.x, self.y, self.width, self.height, LCD.WHITE)

    # 嵌套类，调试信息输出控件
    class InfoShow:
        """
        InfoShow类，用于在LCD屏幕上显示调试信息的输出控件。

        该类封装了一个调试信息输出控件，用于显示调试信息，支持文本更新、内容清除和自定义样式。控件通过LCD对象进行绘制，可以通过更新方法刷新显示内容。当调试信息达到最大显示行数时，控件会自动清除旧的文本并重新显示。

        Attributes:
            x (int): 控件左上角的 x 坐标。
            y (int): 控件左上角的 y 坐标。
            width (int): 控件的宽度。
            height (int): 控件的高度。
            title (str): 控件的标题。
            LCD_obj (LCD): LCD 屏幕对象，用于绘制控件和显示内容。
            Infowidth (int): 调试信息输出窗口的宽度（根据控件宽度计算）。
            Infoheight (int): 调试信息输出窗口的高度（根据控件高度计算）。
            Infox (int): 调试信息输出窗口左上角的 x 坐标（根据控件左上角坐标计算）。
            Infoy (int): 调试信息输出窗口左上角的 y 坐标（根据控件左上角坐标计算）。
            count (int): 当前显示的调试信息行数。

        Methods:
            __init__(self, x, y, width, height, title, lcd_obj):
                初始化 InfoShow 类实例，设置控件的显示位置、尺寸、标题和LCD对象。

            update(self, text, text_index):
                更新调试信息输出控件显示的文本，超过最大行数时自动清除旧内容。

            delete(self):
                清除调试信息输出控件的显示内容，重绘控件背景。
        """
        def __init__(self, x: int, y: int, width: int, height: int, title: str, lcd_obj: 'LCD') -> None:
            """
            调试信息输出控件初始化。

            Args:
                x (int): 调试信息输出控件左上角的 x 坐标。
                y (int): 调试信息输出控件左上角的 y 坐标。
                width (int): 控件的宽度。
                height (int): 控件的高度。
                title (str): 控件的标题。
                lcd_obj (LCD): LCD 屏幕对象，用于绘制控件和显示内容。

            Returns:
                None
            """
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.title = title
            self.LCD_obj = lcd_obj

            # 调试信息输出窗口的长宽和横纵坐标
            self.Infowidth  = self.width - 10
            self.Infoheight = self.height - 15
            self.Infox      = self.x+5
            self.Infoy      = self.y+10

            # 调试信息计数
            self.count = 0

            # 绘制调试信息输出控件矩形填充
            self.LCD_obj.fill_rect(self.x, self.y, self.width, self.height, LCD.BLUE)
            # 绘制调试信息输出控件矩形边框
            self.LCD_obj.rect(self.x, self.y, self.width, self.height, LCD.BLACK)
            # 绘制标题，字体颜色为黑色，背景颜色为红色，标题位置在中间
            self.LCD_obj.text(smallfont, self.title, int(self.width/2)-int(len(self.title)/2 * smallfont.WIDTH), self.y+2, LCD.BLACK,LCD.BLUE)
            # 绘制调试信息输出窗口
            self.LCD_obj.fill_rect(self.Infox, self.Infoy, self.Infowidth, self.Infoheight, LCD.BLACK)

        def update(self, text: str, text_index: int) -> None:
            """
            更新调试信息输出控件显示的文本。

            Args:
                text (str): 待更新的调试信息文本。
                text_index (int): 调试信息的索引。

            Returns:
                None

            Raises:
                None
            """

            # 若是调试信息数量超过最大值，则清空文本，重新绘图
            if self.count == int(self.Infoheight/10) :
                self.LCD_obj.fill_rect(self.Infox, self.Infoy, self.Infowidth, self.Infoheight, LCD.BLACK)
                # 计数值清零
                self.count = 0

            # 绘制文本
            self.LCD_obj.text(smallfont, str(text_index)+': ' + text, self.Infox, self.Infoy + self.count*10, LCD.WHITE,LCD.BLACK)

            # 计数值加1
            self.count += 1

        def delete(self) -> None:
            """
            清除调试信息输出控件的显示内容。

            Args:
                None

            Returns:
                None

            Raises:
                None
            """
            # 绘制白色填充矩形，将LCD上波形显示控件
            # 无需对创建的实例进行del销毁，使用gc模块的自动垃圾清除即可
            self.LCD_obj.fill_rect(self.x, self.y, self.width, self.height, LCD.WHITE)

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using LCD to show IMU data")

# 初始化SPI类，设置波特率、极性、相位、时钟引脚、数据引脚
spi = SPI(0, baudrate=10000000, polarity=0, phase=0, sck=Pin(6), mosi=Pin(7))
# 初始化LCD屏幕,并设置屏幕上下和左右都翻转
lcd = LCD(spi, 240, 320, reset=Pin(8), dc=Pin(9), cs=Pin(10), backlight=Pin(11), rotation = 2)

# 生成文本，offset为偏移量，用于下一行显示中y坐标的偏移量的确定
offset  = 0
offset  = lcd.line_center_text("Freak Studio", 0, lcd.RED, lcd.bigsize)
offset  = lcd.line_center_text("TORCHBEARERS OF CREATION", offset, lcd.MAGENTA, lcd.smallsize) + offset
offset  = lcd.line_left_text("ST7789 LCD experiment", offset, lcd.BLACK, lcd.smallsize) + offset
# 绘制矩形填充
lcd.fill_rect(5,offset,230,265,LCD.ANWHITE)
# 绘制矩形边框
lcd.rect(5,offset,230,265,LCD.BLACK)
# 绘制填充矩形
lcd.fill_rect(10,offset+10,220,10,LCD.CYAN)
lcd.fill_rect(10,offset+20,220,10,LCD.YELLOW)
lcd.fill_rect(10,offset+30,220,10,LCD.GREEN)
# 生成陀螺仪x轴角度的变量显示控件实例
var1 = LCD.VarShow("X_angle", 0, 10, offset+40, lcd)
# 生成陀螺仪y轴角度的变量显示控件实例
var2 = LCD.VarShow("Y_angle", 0, 120, offset+40, lcd)
# 生成波形显示控件
waveformShow = LCD.waveformShow(10, offset+60, 220, 100, "WAVEFORM", lcd)
# 生成调试信息输出控件
infoShow = LCD.InfoShow(10, offset+165, 220, 90, "DEBUG INFO", lcd)
# 调试信息输出控件输出调试信息，初始化LCD屏幕成功
infoShow.update("LCD SCREEN INIT", 0)

# 创建串口对象，设置波特率为115200
uart = UART(1, 115200)
# 初始化uart对象，数据位为8，无校验位，停止位为1
# 设置串口超时时间为5ms
uart.init(bits=8,
          parity=None,
          stop=1,
          tx=4,
          rx=5,
          timeout=5)
# 初始化一个IMU对象
imu = IMU(uart)
# 调试信息输出控件输出调试信息，初始化串口陀螺仪成功
infoShow.update("UART IMU INIT", 1)

# 设置GPIO 25为LED输出引脚，下拉电阻使能
LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)
# 调试信息输出控件输出调试信息，初始化LED灯成功
infoShow.update("LED INIT SUNCCESS", 2)

# 调试信息输出控件输出调试信息，设备初始化完成
infoShow.update("DEVICE INIT COMPLETE", 3)

# 延时，等待设备初始化完成
time.sleep(3)

# ========================================  主程序  ============================================

while True:
    # 点亮LED灯
    LED.on()
    # 接收陀螺仪数据
    imu.RecvData()
    # 熄灭LED灯
    LED.off()
    # 调试信息输出控件输出调试信息，接收陀螺仪数据成功
    infoShow.update("RECV IMU DATA", IMU_RECV_COUNT + 4)
    # 陀螺仪x轴角度的整数值-变量显示控件更新数值
    var1.update(int(imu.angle_x))
    # 陀螺仪y轴角度的整数值-变量显示控件更新数值
    var2.update(int(imu.angle_y))
    # 陀螺仪z轴角度的整数值-波形显示控件更新数值
    waveformShow.update(int(imu.angle_z), 360, LCD.RED)

    # 当可用堆 RAM 的字节数小于 200000 时，手动触发垃圾回收功能
    if gc.mem_free() < 200000:
        # 手动触发垃圾回收功能
        gc.collect()

    # 陀螺仪数据接收计数加1
    IMU_RECV_COUNT = IMU_RECV_COUNT + 1
    if  IMU_RECV_COUNT == 1000:
        IMU_RECV_COUNT = 0