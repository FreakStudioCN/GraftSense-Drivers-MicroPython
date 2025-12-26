# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/13 下午2:21   
# @Author  : 李清水            
# @File    : neopixel_matrix.py       
# @Description : WS2812矩阵驱动库

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin
# 导入framebuf模块
import framebuf
# 导入WS2812驱动模块
import neopixel
# 导入MicroPython相关模块
import micropython
from micropython import const
# 导入json模块
import json

# ======================================== 全局变量 ============================================

# Gamma校正系数
# 红通道：线性，无校正
GAMMA_RED = 1.0
# 绿通道：线性，无校正
GAMMA_GREEN = 1.0
# 蓝通道：线性，无校正
GAMMA_BLUE = 1.0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# WS2812 矩阵驱动类
class NeopixelMatrix(framebuf.FrameBuffer):
    # 常用颜色（RGB565）
    COLOR_BLACK   = const(0x0000)
    COLOR_WHITE   = const(0xFFFF)
    COLOR_RED     = const(0xF800)
    COLOR_GREEN   = const(0x07E0)
    COLOR_BLUE    = const(0x001F)
    COLOR_YELLOW  = const(0xFFE0)
    COLOR_CYAN    = const(0x07FF)
    COLOR_MAGENTA = const(0xF81F)

    # RGB顺序常量（WS2812不同模块可能顺序不同）
    ORDER_RGB = 'RGB'
    ORDER_GRB = 'GRB'
    ORDER_BGR = 'BGR'
    ORDER_BRG = 'BRG'
    ORDER_RBG = 'RBG'
    ORDER_GBR = 'GBR'

    # 布局类型常量
    LAYOUT_ROW = 'row'
    LAYOUT_SNAKE = 'snake'

    # Gamma色准校正计算公式

    _GAMMA_TABLE_R = [round(255 * ((i / 255) ** (1 / GAMMA_RED))) for i in range(256)]
    _GAMMA_TABLE_G = [round(255 * ((i / 255) ** (1 / GAMMA_GREEN))) for i in range(256)]
    _GAMMA_TABLE_B = [round(255 * ((i / 255) ** (1 / GAMMA_BLUE))) for i in range(256)]

    # 图片JSON格式规范 (RGB565像素格式)
    # 说明：该JSON用于存储RGB565格式的像素图像数据，可被图像加载方法解析渲染
    # {
    #     "pixels": [    # 必需字段 - RGB565像素数组，每个值的数值范围为0-65535（对应十六进制0x0000-0xFFFF）
    #                    # 像素值**必须使用十进制整数**表示（如63488），禁止使用十六进制格式（如0xF800）
    #                    # 排版建议：每个像素值单独占一行，提升JSON文件的可读性并避免解析错误
    #         63488,     # 示例：纯红色（对应RGB565编码：R=31, G=0, B=0，十六进制0xF800转换为十进制63488）
    #         2016,      # 示例：纯绿色（对应RGB565编码：R=0, G=63, B=0，十六进制0x07E0转换为十进制2016）
    #         31         # 示例：纯蓝色（对应RGB565编码：R=0, G=0, B=31，十六进制0x001F转换为十进制31）
    #     ],
    #     "width": 128,   # 可选字段 - 图片宽度（单位：像素），默认使用显示器宽度
    #                     # 强制约束：像素数组长度len(pixels)必须能被width整除，否则会导致解析失败
    #     # 以下为可选元数据字段（仅用于描述信息，不影响图像渲染逻辑）
    #     "height": 64,   # 可选字段 - 图片高度（单位：像素），可通过公式自动计算：height = len(pixels) / width
    #     "description": "Sample image", # 可选字段 - 图片描述信息，建议使用英文表述
    #     "version": 1.0  # 可选字段 - 格式版本号，用于区分不同版本的规范定义
    # }

    def __init__(self, width, height, pin, layout=LAYOUT_ROW, brightness=1, order=ORDER_RGB,
                 flip_h=False, flip_v=False, rotate=0):
        # 检查参数是否合法
        if width < 1 or height < 1:
            raise ValueError('width and height must be greater than 0')

        # 检查布局类型是否合法
        if layout not in [NeopixelMatrix.LAYOUT_ROW, NeopixelMatrix.LAYOUT_SNAKE]:
            raise ValueError('layout must be one of "NeopixelMatrix.LAYOUT_ROW" or "NeopixelMatrix.LAYOUT_SNAKE"')

        # 检查颜色转换顺序是否合法
        if order not in [NeopixelMatrix.ORDER_RGB, NeopixelMatrix.ORDER_GRB, NeopixelMatrix.ORDER_BGR,
                         NeopixelMatrix.ORDER_BRG, NeopixelMatrix.ORDER_RBG, NeopixelMatrix.ORDER_GBR]:
            raise ValueError('order must be one of "NeopixelMatrix.ORDER_RGB", "NeopixelMatrix.ORDER_GRB", "NeopixelMatrix.ORDER_BGR", '
                             '"NeopixelMatrix.ORDER_BRG", "NeopixelMatrix.ORDER_RBG" or "NeopixelMatrix.ORDER_GBR"')

        # 检查翻转参数是否合法
        if not isinstance(flip_h, bool) or not isinstance(flip_v, bool):
            raise ValueError('flip_h and flip_v must be bool')

        # 检查旋转角度是否合法：只能为0、90、180、270
        if not (rotate == 0 or rotate == 90 or rotate == 180 or rotate == 270):
            raise ValueError('rotate must be 90, 180 or 270')

        # 创建 NeoPixel 对象，共 width*height 个像素
        self.np = neopixel.NeoPixel(pin, width * height)
        # 保存矩阵宽度、高度
        self.width = width
        self.height = height

        # 保存布局类型（行/蛇形）：
        #   行优先排列：每一行从左到右依次编号，每一行的方向都相同。
        #   蛇形排列：偶数行（第 0、2、4 行等）从左到右，奇数行（第 1、3、5 行等）从右到左。
        self.layout = layout
        # 创建用于 framebuf 的 RGB565 缓冲区（2 字节一个像素）
        self.buffer = memoryview(bytearray(width * height * 2))

        # 保存颜色转换顺序
        self.order = order
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.rotate = rotate % 360

        # 初始化 framebuf.FrameBuffer，使用 RGB565 模式
        super().__init__(self.buffer, width, height, framebuf.RGB565)

        # 初始化亮度
        self._brightness = brightness

    @property
    def brightness(self):
        """获取当前亮度"""
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        """设置亮度"""
        if not 0 <= value <= 1:
            raise ValueError("Brightness must be between 0 and 1")
        self._brightness = value

    @micropython.native
    def apply_brightness_gamma_balance(self, r, g, b, brightness=None, r_balance=1.0, g_balance=1.0, b_balance=1.0):
        """
        应用亮度调节、Gamma校正和三色调整
        """
        if brightness is None:
            brightness = self._brightness

        if not 0 <= brightness <= 1:
            raise ValueError("Brightness must be between 0 and 1")

        # 应用Gamma校正
        r = NeopixelMatrix._GAMMA_TABLE_R[r]
        g = NeopixelMatrix._GAMMA_TABLE_G[g]
        b = NeopixelMatrix._GAMMA_TABLE_B[b]

        # 应用亮度和三色调整
        r = int(r * brightness * r_balance)
        g = int(g * brightness * g_balance)
        b = int(b * brightness * b_balance)

        return r, g, b

    @micropython.native
    def _pos2index(self, x, y):
        """
        处理不同矩阵排列方式
        """
        # 1. 旋转处理
        if self.rotate == 90:
            x, y = y, self.width - 1 - x
        elif self.rotate == 180:
            x, y = self.width - 1 - x, self.height - 1 - y
        elif self.rotate == 270:
            x, y = self.height - 1 - y, x

        # 2. 翻转处理
        if self.flip_h:
            x = self.width - 1 - x
        if self.flip_v:
            y = self.height - 1 - y

        # 行优先：直接线性排列
        if self.layout == NeopixelMatrix.LAYOUT_ROW:
            return y * self.width + x
        # 蛇形排列：奇数行方向反转
        elif self.layout == NeopixelMatrix.LAYOUT_SNAKE:
            return y * self.width + (x if y % 2 == 0 else self.width - 1 - x)

    @micropython.native
    def rgb565_to_rgb888(self, val, brightness=None, order=None, r_balance=1.0, g_balance=1.0, b_balance=1.0):
        """
        将 RGB565 颜色转换为 RGB888（三元组），适配 WS2812。
        """
        if brightness is None:
            brightness = self._brightness

        if order is None:
            order = self.order

        if not 0 <= brightness <= 1:
            raise ValueError("Brightness must be between 0 and 1")

        # 提取 RGB565 颜色分量
        r = (val >> 11) & 0x1F
        g = (val >> 5) & 0x3F
        b = val & 0x1F

        # 转换为 8bit
        r8 = (r << 3) | (r >> 2)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 3) | (b >> 2)

        # 调用apply_brightness_gamma_balance进行亮度、Gamma校正和三色调整
        r8, g8, b8 = self.apply_brightness_gamma_balance(r8, g8, b8, brightness, r_balance, g_balance, b_balance)

        # 根据顺序组合
        if order == NeopixelMatrix.ORDER_RGB:
            rgb = (r8, g8, b8)
        elif order == NeopixelMatrix.ORDER_GRB:
            rgb = (g8, r8, b8)
        elif order == NeopixelMatrix.ORDER_BGR:
            rgb = (b8, g8, r8)
        elif order == NeopixelMatrix.ORDER_BRG:
            rgb = (b8, r8, g8)
        elif order == NeopixelMatrix.ORDER_RBG:
            rgb = (r8, b8, g8)
        elif order == NeopixelMatrix.ORDER_GBR:
            rgb = (g8, b8, r8)
        else:
            raise ValueError('Invalid order: {}'.format(order))

        return rgb

    @micropython.native
    def show(self, x1=0, y1=0, x2=None, y2=None):
        """
        刷新屏幕，将 FrameBuffer 中的内容写入 WS2812 灯带。
        支持局部刷新，通过指定 (x1, y1) 到 (x2, y2) 的区域。
        """
        # 如果没指定 x2，默认整行
        x2 = x2 if x2 is not None else self.width - 1
        # 如果没指定 y2，默认整列
        y2 = y2 if y2 is not None else self.height - 1

        # 检查区域参数是否合法
        # 检查起始坐标是否合法
        if not (0 <= x1 < self.width and 0 <= y1 < self.height):
            raise ValueError(f'Start coordinate ({x1},{y1}) out of range ')
        # 检查结束坐标是否合法
        if not (0 <= x2 < self.width and 0 <= y2 < self.height):
            raise ValueError(f'End coordinate ({x2},{y2}) out of range ')
        # 检查区域是否合法
        if x2 < x1 or y2 < y1:
            raise ValueError('Invalid area: ({x1},{y1})-({x2},{y2})'.format(x1=x1, y1=y1, x2=x2, y2=y2))

        # 遍历每一行
        for y in range(y1, y2 + 1):
            # 遍历每一列
            for x in range(x1, x2 + 1):
                # 计算 WS2812 的实际索引
                idx = self._pos2index(x, y)
                # 每个像素占 2 字节，计算在 buffer 中的偏移地址
                addr = (y * self.width + x) * 2
                # 从 FrameBuffer 中读取 RGB565 值， 注意，FrameBuffer是小端序
                val = (self.buffer[addr + 1] << 8) | self.buffer[addr]
                # 转换为 RGB888 后赋值给 WS2812
                self.np[idx] = self.rgb565_to_rgb888(val, self.brightness, self.order)

        # 写入所有像素数据到 WS2812 灯带，点亮屏幕
        self.np.write()

    @micropython.native
    def scroll(self, xstep, ystep, clear_color=None, wrap=False):
        """
        重写scroll方法，提供两种滚动模式
        参数:
            xstep: 水平滚动步数(正数向右，负数向左)
            ystep: 垂直滚动步数(正数向下，负数向上)
            clear_color: 清除残留区域使用的颜色(默认COLOR_BLACK)
            wrap: True=循环滚动 False=普通滚动(默认)
        需要注意：
            不允许同时设置水平和垂直滚动步数（xstep和ystep不能同时非零）
        """
        # 如果没有指定清除颜色，使用默认黑色
        if clear_color is None:
            clear_color = NeopixelMatrix.COLOR_BLACK

        # 检查滚动参数是否合法
        if not isinstance(xstep, int) or not isinstance(ystep, int):
            raise ValueError('xstep and ystep must be int')

        # 检查颜色参数是否合法
        if not isinstance(clear_color, int):
            raise ValueError('clear_color must be int')

        # 检查循环滚动设置参数是否合法
        if not isinstance(wrap, bool):
            raise ValueError('wrap must be bool')

        # 只能选择水平或垂直一个方向滚动
        if xstep != 0 and ystep != 0:
            raise ValueError('Cannot set xstep and ystep at the same time (only one direction allowed)')

        if wrap:
            # 循环滚动模式 - 保存原始缓冲区
            temp_buffer = bytearray(self.buffer)

            # 处理水平滚动
            if xstep != 0:
                abs_xstep = abs(xstep) % self.width
                if xstep > 0:
                    # 向右滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_x = (x - abs_xstep) % self.width
                            src_addr = (y * self.width + src_x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]
                else:
                    # 向左滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_x = (x + abs_xstep) % self.width
                            src_addr = (y * self.width + src_x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]

            # 处理垂直滚动
            if ystep != 0:
                abs_ystep = abs(ystep) % self.height
                if ystep > 0:
                    # 向下滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_y = (y - abs_ystep) % self.height
                            src_addr = (src_y * self.width + x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]
                else:
                    # 向上滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_y = (y + abs_ystep) % self.height
                            src_addr = (src_y * self.width + x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]
        else:
            # 普通滚动模式
            super().scroll(xstep, ystep)

            # 清除水平滚动残留
            if xstep > 0:
                # 向右滚动，清除左侧残留
                self.vline(0, 0, self.height, clear_color)
            elif xstep < 0:
                # 向左滚动，清除右侧残留
                self.vline(self.width - 1, 0, self.height, clear_color)

            # 清除垂直滚动残留
            if ystep > 0:
                # 向下滚动，清除顶部残留
                self.hline(0, 0, self.width, clear_color)
            elif ystep < 0:
                # 向上滚动，清除底部残留
                self.hline(0, self.height - 1, self.width, clear_color)

    @micropython.native
    def show_rgb565_image(self, image_data, offset_x=0, offset_y=0):
        """
        显示RGB565格式的JSON图片
        参数:
            image_data: 包含RGB565数据的JSON字符串或字典
            offset_x: X轴偏移(像素)
            offset_y: Y轴偏移(像素)
        """
        try:
            # 解析JSON数据
            if isinstance(image_data, str):
                image_data = json.loads(image_data)

            # 验证数据格式
            self._validate_rgb565_image(image_data)

            # 渲染图片
            self._draw_rgb565_data(
                image_data['pixels'],
                image_data.get('width', self.width),
                offset_x,
                offset_y
            )
        except Exception as e:
            print("Error: {}".format(e))

    @micropython.native
    def _validate_rgb565_image(self, data):
        """
        验证RGB565图像数据结构
        """
        required = ['pixels']
        if not all(key in data for key in required):
            raise ValueError('lack required keys: {}'.format(required))

        if not isinstance(data['pixels'], list):
            raise ValueError('pixels must be list')

        if 'width' in data and data['width'] <= 0:
            raise ValueError('width must be positive integer')

        for color in data['pixels']:
            if not 0 <= color <= 0xFFFF:
                raise ValueError('color must be 0-65535')

    @micropython.native
    def _draw_rgb565_data(self, pixels, img_width, offset_x, offset_y):
        """
        渲染RGB565像素数据
        参数:
            pixels: RGB565值数组
            img_width: 原图宽度
            offset_x: X偏移
            offset_y: Y偏移
        """
        for i, color in enumerate(pixels):
            x = i % img_width + offset_x
            y = i // img_width + offset_y

            if 0 <= x < self.width and 0 <= y < self.height:
                self.pixel(x, y, color)

    @micropython.native
    def load_rgb565_image(self, filename, offset_x=0, offset_y=0):
        """
        从JSON文件加载RGB565格式图片
        参数:
            filename: JSON文件路径
            offset_x: X轴偏移
            offset_y: Y轴偏移
        """
        try:
            with open(filename, 'r') as f:
                self.show_rgb565_image(f.read(), offset_x, offset_y)
        except OSError as e:
            print("Error: {}".format(e))

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================