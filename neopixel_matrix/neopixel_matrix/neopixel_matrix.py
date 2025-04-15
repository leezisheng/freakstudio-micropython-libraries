# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/13 下午2:21   
# @Author  : 李清水            
# @File    : neopixel_matrix.py       
# @Description : WS2812矩阵驱动库

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

    # 缓存颜色转换结果，加速重复色值的处理
    COLOR_CACHE = {}

    # 图片JSON格式规范:
    # {
    #     "pixels": [    # 必需 - RGB565像素数组，每个值范围0-65535
    #         0xF800,    # 红色 (R=31, G=0, B=0)
    #         0x07E0,    # 绿色 (R=0, G=63, B=0)
    #         0x001F     # 蓝色 (R=0, G=0, B=31)
    #     ],
    #     "width": 128,   # 可选 - 图片宽度(像素)，默认使用显示器宽度
    #                     # 注: len(pixels)必须能被width整除
    #     # 以下为可选元数据(不影响渲染):
    #     "height": 64,   # 自动计算: len(pixels)/width
    #     "description": "示例图片",
    #     "version": 1.0
    # }

    def __init__(self, width, height, pin, layout=LAYOUT_ROW, brightness=0.2, order=ORDER_BRG,
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

        # 初始化亮度并缓存常用颜色
        self._brightness = brightness
        self._init_color_cache()

    def _init_color_cache(self):
        """根据当前亮度初始化常用颜色缓存"""
        NeopixelMatrix.COLOR_CACHE.clear()
        common_colors = [
            NeopixelMatrix.COLOR_BLACK,
            NeopixelMatrix.COLOR_WHITE,
            NeopixelMatrix.COLOR_RED,
            NeopixelMatrix.COLOR_GREEN,
            NeopixelMatrix.COLOR_BLUE,
            NeopixelMatrix.COLOR_YELLOW,
            NeopixelMatrix.COLOR_CYAN,
            NeopixelMatrix.COLOR_MAGENTA
        ]
        for color in common_colors:
            # 计算并缓存
            self.rgb565_to_rgb888(color)

    @property
    def brightness(self):
        """获取当前亮度"""
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        """设置亮度，并清空缓存"""
        if not 0 <= value <= 1:
            raise ValueError("Brightness must be between 0 and 1")
        self._brightness = value
        # 清空并重新初始化缓存
        self._init_color_cache()

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
    def rgb565_to_rgb888(self, val, brightness=None, order=None):
        """
        将 RGB565 颜色转换为 RGB888（三元组），适配 WS2812。
        使用缓存加速重复转换。
        """
        if brightness is None:
            brightness = self._brightness

        if order is None:
            order = self.order

        if not 0 <= brightness <= 1:
            raise ValueError("Brightness must be between 0 and 1")

        # 检查缓存
        cache_key = (val, brightness, order)
        if cache_key in NeopixelMatrix.COLOR_CACHE:
            return NeopixelMatrix.COLOR_CACHE[cache_key]

        # 提取 RGB565 颜色分量
        r = (val >> 11) & 0x1F
        g = (val >> 5) & 0x3F
        b = val & 0x1F

        # 转换为 8bit 并应用亮度
        r8 = int(((r * 527 + 23) >> 6) * brightness)
        g8 = int(((g * 259 + 33) >> 6) * brightness)
        b8 = int(((b * 527 + 23) >> 6) * brightness)

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

        # 写入缓存
        NeopixelMatrix.COLOR_CACHE[cache_key] = rgb

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
                # 从 FrameBuffer 中读取 RGB565 值（高字节在前）
                val = (self.buffer[addr] << 8) | self.buffer[addr + 1]
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