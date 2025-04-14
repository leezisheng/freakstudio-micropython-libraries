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

    # 初始化常用颜色缓存（使用默认亮度 0.2）
    _COMMON_COLORS = [
        COLOR_BLACK,
        COLOR_WHITE,
        COLOR_RED,
        COLOR_GREEN,
        COLOR_BLUE,
        COLOR_YELLOW,
        COLOR_CYAN,
        COLOR_MAGENTA
    ]

    for c in _COMMON_COLORS:
        r = (c >> 11) & 0x1F
        g = (c >> 5) & 0x3F
        b = c & 0x1F
        r8 = int((r << 3) * 0.2)
        g8 = int((g << 2) * 0.2)
        b8 = int((b << 3) * 0.2)
        # BGR 顺序
        COLOR_CACHE[c] = (g8, b8, r8)

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

        # 保存亮度缩放比例
        self.brightness = brightness
        # 保存颜色转换顺序
        self.order = order
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.rotate = rotate % 360

        # 初始化 framebuf.FrameBuffer，使用 RGB565 模式
        super().__init__(self.buffer, width, height, framebuf.RGB565)

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
    @staticmethod
    def rgb565_to_rgb888(val, brightness=0.2, order='GRB'):
        """
        将 RGB565 格式的颜色值转换为 RGB888（三元组），适配 WS2812。
        实际上转换后为 BGR 顺序。
        使用缓存加速重复转换。
        """
        # 判断设定颜色值是否在缓存中
        if val not in NeopixelMatrix.COLOR_CACHE:
            # RGB565 格式：5 位红色 + 6 位绿色 + 5 位蓝色
            # 进行格式转换并应用亮度缩放
            # 提取红色部分（5位）
            r = (val >> 11) & 0x1F
            # 提取绿色部分（6位）
            g = (val >> 5) & 0x3F
            # 提取蓝色部分（5位）
            b = val & 0x1F

            # 计算亮度缩放
            r8 = int((r << 3) * brightness)
            g8 = int((g << 2) * brightness)
            b8 = int((b << 3) * brightness)

            # 转换为 8 位颜色（缩放），并写入缓存
            # 根据顺序组合
            if order == NeopixelMatrix.ORDER_RGB:
                return (r8, g8, b8)
            elif order == NeopixelMatrix.ORDER_GRB:
                return (g8, r8, b8)
            elif order == NeopixelMatrix.ORDER_BGR:
                return (b8, g8, r8)
            elif order == NeopixelMatrix.ORDER_BRG:
                return (b8, r8, g8)
            elif order == NeopixelMatrix.ORDER_RBG:
                return (r8, b8, g8)
            elif order == NeopixelMatrix.ORDER_GBR:
                return (g8, b8, r8)
            else:
                raise ValueError('Invalid order: {}'.format(order))

        return NeopixelMatrix.COLOR_CACHE[val]

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

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================