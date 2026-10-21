# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : GraftSense
# @File    : mlx90614_async.py
# @Description : MLX90614/MLX90615 显式异步读取接口
# @License : MIT

# ======================================== 导入相关模块 =========================================
from mlx90614 import SensorBase, MLX90614, MLX90615

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class _MLXAsyncMixin:
    async def read_ambient_async(self): return self.read_ambient()
    async def read_object_async(self): return self.read_object()
    async def read_object2_async(self): return self.read_object2()
    async def ambient_async(self): return self.ambient()
    async def object_async(self): return self.object()
    async def object2_async(self): return self.object2()
    async def read_async(self): return self.read()
    async def get_async(self): return self.get()
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()

class SensorBaseAsync(_MLXAsyncMixin, SensorBase):
    pass
class MLX90614Async(_MLXAsyncMixin, MLX90614):
    pass
class MLX90615Async(_MLXAsyncMixin, MLX90615):
    pass

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================