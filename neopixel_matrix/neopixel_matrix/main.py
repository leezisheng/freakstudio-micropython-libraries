# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/14 上午10:44   
# @Author  : 李清水            
# @File    : main.py       
# @Description : WS2812矩阵驱动库相关测试代码

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin
# 导入WS2812驱动模块
from neopixel_matrix import NeopixelMatrix
import math
from array import array
import random
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def color_wipe(color, delay=0.1):
    """颜色填充特效"""
    matrix.fill(0)
    for i in range(4):
        for j in range(4):
            matrix.pixel(i, j, color)
            matrix.show()
            time.sleep(delay)
    matrix.fill(0)
def optimized_scrolling_lines():
    """优化后的滚动线条动画：蓝横线下降→红竖线右移"""
    # 1. 蓝色横线从上向下滚动
    matrix.fill(0)
    matrix.show()
    matrix.hline(0, 0, 4, NeopixelMatrix.COLOR_BLUE)  # 顶部蓝线
    matrix.show()
    time.sleep(0.5)

    # 向下滚动3次，用红色填充空白
    for _ in range(3):
        matrix.scroll(0, 1, clear_color=NeopixelMatrix.COLOR_GREEN)
        matrix.show()
        time.sleep(0.3)

    # 2. 红色竖线从左向右循环滚动
    matrix.fill(0)
    # 左侧红线
    matrix.fill(NeopixelMatrix.COLOR_CYAN)
    matrix.vline(0, 0, 4, NeopixelMatrix.COLOR_RED)
    matrix.show()
    time.sleep(0.5)

    # 向右循环滚动8次(完整循环两次)
    for _ in range(8):
        matrix.scroll(1, 0,wrap=True)
        matrix.show()
        time.sleep(0.2)

    # 3. 结束清除
    matrix.fill(0)
    matrix.show()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

matrix = NeopixelMatrix(4, 4, Pin(22), layout=NeopixelMatrix.LAYOUT_ROW, brightness=0.2, order=NeopixelMatrix.ORDER_BRG, flip_v = True)
matrix.fill(0)
matrix.show()

# ========================================  主程序  ===========================================

# matrix.hline(0, 0, 4, matrix.COLOR_BLUE)
# matrix.vline(1, 1, 2, matrix.COLOR_RED)
# matrix.vline(2, 2, 2, matrix.COLOR_GREEN)
# matrix.show()