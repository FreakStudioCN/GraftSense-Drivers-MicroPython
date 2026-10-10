# A MicroPython library to control gt911 driver — MicroPython 异步驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [异步设计与使用](#异步设计与使用)
- [API Async Matrix](#api-async-matrix)
- [Source Demo to Async Demo Mapping](#source-demo-to-async-demo-mapping)
- [超时、取消、并发与残余阻塞](#超时取消并发与残余阻塞)
- [Hardware Acceptance](#hardware-acceptance)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

`gt911_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`input/gt911_driver`。

## 主要功能

- 可解析的公开类：`Button`, `GT911`, `GT911Async`, `LCD`, `ST7789`, `SyncAdapterMixin`。
- 可解析的公开调用入口：90 个（详见 API 矩阵）。
- 异步等级：`event_bridge`；依据：IRQ/事件通知由协程消费；总线访问仍可能同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, SPI, Pin( |
| 示例 GPIO | 6、7、8、9、10、11、12、13、25 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.0` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/gt911.py
├── code/gt911_async.py
├── code/main.py
├── code/st7789.py
├── code/vga1_16x16.py
├── code/vga1_16x32.py
├── code/vga1_8x8.py
├── examples/main_sync.py
├── LICENSE
└── package.json
```

## 文件说明

- `code/`：实际发布的运行时 Python 模块；以 `package.json.urls` 为安装映射依据。
- `code/main.py`（若存在）：异步演示入口，不是默认发布运行时映射。
- `examples/`（若存在）：同步保真基线或额外示例，不应当作安装后的运行时模块。
- `package.json`、`LICENSE`：发布元数据和许可证的唯一事实来源。

## 快速开始

1. 按 `package.json.urls` 将运行时文件复制到设备；不要把 `examples/` 当作运行时依赖。
2. 按上文硬件/运行环境配置总线、GPIO、网络或凭证。
3. 使用包内真实 `code/main.py` 的 import 与构造方式运行。以下是当前文件逐字读取的异步入口；部署时请保留 `try/finally` 并调用对象实际提供的 `deinit()` 或 `aclose()`。

```python
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

async def main():
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

    # LCD屏幕相关的模块
    from st7789 import ST7789

    # 字库相关的模块
    import vga1_16x32 as bigfont
    import vga1_16x16 as mediumfont
    import vga1_8x8 as smallfont

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
        BLACK = const(0xFFFF)  # 黑色
        WHITE = const(0x0000)  # 白色
        MAGENTA = const(0x07E0)  # 品红色/浅紫色
        RED = const(0x07FF)  # 红色
        GREEN = const(0xF81F)  # 绿色
        BLUE = const(0xFFE0)  # 蓝色
        CYAN = const(0xF800)  # 青色
        YELLOW = const(0x001F)  # 黄色
        YEGR = const(0xFAEBD7)  # 黄绿色
        GATES = const(0x87CEEB)  # 品蓝色
        ANWHITE = const(0x191970)  # 古董白

        # 字体大小
        bigsize, mediumsize, smallsize = 32, 16, 8

        def __init__(
            self,
            spi: object,
            width: int,
            height: int,
            reset: object = None,
            dc: object = None,
            cs: object = None,
            backlight: object = None,
            rotation: int = 0,
        ) -> None:
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
            super().__init__(spi, width, height, reset, dc, cs, backlight, rotation=rotation)

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
                font = bigfont
                fontheight = bigfont.HEIGHT
                fontwitdh = bigfont.WIDTH
            elif size == self.mediumsize:
                font = mediumfont
                fontheight = mediumfont.HEIGHT
                fontwitdh = mediumfont.WIDTH
            elif size == self.smallsize:
                font = smallfont
                fontheight = smallfont.HEIGHT
                fontwitdh = smallfont.WIDTH
            else:
                raise ValueError("WRONG FONT SIZE")

            # 计算文字的x坐标
            x = int(self.width / 2) - int(len(text) / 2 * fontwitdh)
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
                font = bigfont
                fontheight = bigfont.HEIGHT
            elif size == self.mediumsize:
                font = mediumfont
                fontheight = mediumfont.HEIGHT
            elif size == self.smallsize:
                font = smallfont
                fontheight = smallfont.HEIGHT
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
                font = bigfont
                fontheight = bigfont.HEIGHT
                fontwitdh = bigfont.WIDTH
            elif size == self.mediumsize:
                font = mediumfont
                fontheight = mediumfont.HEIGHT
                fontwitdh = mediumfont.WIDTH
            elif size == self.smallsize:
                font = smallfont
                fontheight = smallfont.HEIGHT
                fontwitdh = smallfont.WIDTH
            else:
                raise ValueError("WRONG FONT SIZE")

            self.text(font, text, self.width - len(text) * fontwitdh, line, color)

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

                if 4 * (i + 1) ** 2 + (2 * radius - 2 * j + 1) ** 2 > 4 * radius**2:
                    j += 1
                i += 1

            if fill:
                self.polygon(pixel_list, x, y, color=color)

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

            def __init__(self, lcd_obj: "LCD", x: int, y: int, width: int, height: int, text: str, color: int, pressed_color: int) -> None:
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
    await asyncio.sleep(3)
    # 打印调试信息
    print("FreakStudio : Using LCD with GT911 touch chip to complete keyboard input")

    # 初始化SPI类，设置波特率、极性、相位、时钟引脚、数据引脚
    spi = SPI(0, baudrate=10000000, polarity=0, phase=0, sck=Pin(6), mosi=Pin(7))
    # 初始化LCD屏幕,并设置屏幕上下和左右都翻转
    lcd = LCD(spi, 240, 320, reset=Pin(8), dc=Pin(9), cs=Pin(10), backlight=Pin(11), rotation=2)

    # 生成文本，offset为偏移量，用于下一行显示中y坐标的偏移量的确定
    offset = 0
    offset = lcd.line_center_text("Freak Studio", 0, lcd.RED, lcd.bigsize)
    offset = lcd.line_center_text("TORCHBEARERS OF CREATION", offset, lcd.MAGENTA, lcd.smallsize) + offset
    offset = lcd.line_center_text("Touch Keyboard Experiment", offset, lcd.BLACK, lcd.smallsize) + offset
    # 绘制矩形填充
    lcd.fill_rect(5, offset, 230, 265, LCD.YEGR)
    # 绘制矩形边框
    lcd.rect(5, offset, 230, 265, LCD.BLACK)

    # 创建按键控件实例button1，位置为(10, offset + 20)，宽80，高20，显示文本"LED ON"，默认颜色为品蓝色，按下颜色为古董白
    button1 = LCD.Button(lcd, 10, offset + 20, 80, 20, "LED ON", LCD.GATES, LCD.ANWHITE)
    # 创建按键控件实例button2，位置为(10, offset + 50)，宽80，高20，显示文本"LED OFF"，默认颜色为绿色，按下颜色为红色
    button2 = LCD.Button(lcd, 10, offset + 50, 80, 20, "LED OFF", LCD.GREEN, LCD.RED)

    # 创建硬件I2C的实例，使用I2C0外设，时钟频率为400KHz，SDA引脚为12，SCL引脚为13
    i2c_gt911 = I2C(id=0, sda=Pin(12), scl=Pin(13), freq=400000)
    # 创建GT911类实例，使用I2C1外设，地址为0x5D，同时最大支持触摸点数为2
    gt911_dev = GT911(i2c_gt911, 15, 14, 0x14, touch_points=5, reverse_x=True, reverse_y=True, user_callback=detect_touch)

    # 设置GPIO 25为LED输出引脚，下拉电阻使能
    LED = Pin(25, Pin.OUT, Pin.PULL_DOWN)

    # ========================================  主程序  ============================================

    # 无限循环
    while True:
        # 延时1s
        await asyncio.sleep(1)
        # 当可用堆 RAM 的字节数小于 200000 时，手动触发垃圾回收功能
        if gc.mem_free() < 200000:
            # 手动触发垃圾回收功能
            gc.collect()

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `Button.draw` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Button.is_touched` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Button.press` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Button.release` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911.available` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911.irq_callback` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911.read_id` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911.read_touch` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911.reflash_config` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911.reset` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911Async.available_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911Async.irq_callback_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911Async.read_id_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911Async.read_touch_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911Async.reflash_config_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `GT911Async.reset_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LCD.circle` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LCD.line_center_text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LCD.line_left_text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `LCD.line_right_text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.bitmap` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.blit_buffer` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.fill` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.fill_rect` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.hard_reset` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.hline` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.init` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.inversion_mode` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.line` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.pbitmap` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.pixel` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.polygon` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.rect` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.rotation` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.sleep_mode` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.soft_reset` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.vline` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.vscrdef` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.vscsad` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.write` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ST7789.write_width` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `available` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `available_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `bitmap` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `blit_buffer` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `circle` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `color565` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `detect_touch` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `draw` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `fill` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `fill_rect` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `hard_reset` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `hline` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `init` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `inversion_mode` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `irq_callback` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `irq_callback_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `is_touched` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `line` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `line_center_text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `line_left_text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `line_right_text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `pbitmap` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `pixel` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `polygon` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `press` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_id` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_id_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_touch` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_touch_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `rect` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reflash_config` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reflash_config_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `release` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset_touch` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `rotation` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `sleep_mode` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `soft_reset` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `text` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `vline` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `vscrdef` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `vscsad` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_width` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `code/main.py` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

## 超时、取消、并发与残余阻塞

任何 `await` 不会自动使底层 I2C/SPI/UART/Pin 操作变为非阻塞。取消时应停止后台任务并在 `finally` 释放资源；没有实现超时参数的 API 不应被假定具有超时。协议命令、帧界限、ACK、静默间隔及错误含义只以当前实现和源示例可证明的内容为准。



## Hardware Acceptance

| Level | Evidence | Not covered |
|---|---|---|
| Link | 未实测：仅完成静态代码与文档取证。 | 总线/网络连接、设备身份响应。 |
| Basic function | 未实测。 | 一次真实业务 API 成功及结果正确性。 |
| Complete business flow | 未实测。 | 端到端设备、对端、供电、时序和异常恢复。 |

## 注意事项

| 类别 | 说明 |
|---|---|
| 并发 | 同一硬件实例应由调用方串行化；UART 额外遵守其并发契约。 |
| 阻塞 | 不把短同步总线访问或严格时序脉冲描述为真正可中断。 |
| 验收 | 文档生成不等于硬件验证；接入真实设备后分别记录三层验收证据。 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| `1.0.0` | 2026-09-17 | leeqingshui | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：leeqingshui。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
