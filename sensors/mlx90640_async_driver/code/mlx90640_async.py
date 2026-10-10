"""Asynchronous MLX90640 frame acquisition driver."""

import time
import math
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from mlx90640 import MLX90640, RefreshRate


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class MLX90640Async(MLX90640):
    """MLX90640 with cooperative data-ready polling; calibration maths is upstream code."""

    async def get_frame_async(self, framebuf, timeout_ms=2000):
        if len(framebuf) != 768:
            raise ValueError("framebuf must have a length of 768")
        status = await self._get_frame_data_async(timeout_ms)
        if status < 0:
            raise RuntimeError("Frame data error")
        tr = self._get_ta() - self.openair_ta_shift
        await self._calculate_to_async(0.95, tr, framebuf)

    async def _get_frame_data_async(self, timeout_ms):
        data_ready = 0
        count = 0
        status_register = [0]
        control_register = [0]
        started = time.ticks_ms()
        while not data_ready:
            self._i2c_read_words(0x8000, status_register)
            data_ready = status_register[0] & 0x0008
            if data_ready:
                break
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise RuntimeError("MLX90640 frame-ready timeout")
            await asyncio.sleep_ms(5)
        while data_ready and count < 5:
            self._i2c_write_word(0x8000, 0x0030)
            await self._read_frame_words_async(0x0400, self.mlx90640_frame, 832)
            self._i2c_read_words(0x8000, status_register)
            data_ready = status_register[0] & 0x0008
            count += 1
            if data_ready:
                await asyncio.sleep_ms(0)
        if count > 4:
            raise RuntimeError("Too many retries")
        self._i2c_read_words(0x800D, control_register)
        self.mlx90640_frame[832] = control_register[0]
        self.mlx90640_frame[833] = status_register[0] & 0x0001
        return self.mlx90640_frame[833]

    async def _read_frame_words_async(self, address, buffer, word_count):
        """Read a frame in bounded I2C chunks, yielding between transactions."""
        chunk_words = min(self.i2c_read_len, 64)
        chunk = [0] * chunk_words
        offset = 0
        while offset < word_count:
            count = min(chunk_words, word_count - offset)
            self._i2c_read_words(address + offset, chunk, end=count)
            for index in range(count):
                buffer[offset + index] = chunk[index]
            offset += count
            await asyncio.sleep_ms(0)
    async def _calculate_to_async(self, emissivity: float, tr: float, result: list) -> None:
            """
            计算每个像素的目标温度（摄氏度）并存储到结果列表。
    
            Args:
                emissivity (float): 物体发射率，通常为0.95。
                tr (float): 参考温度，由环境温度计算得出。
                result (list): 用于存储目标温度的列表，长度必须为768。
    
            Raises:
                ValueError: 当result列表长度不等于768时抛出。
    
            Notes:
                - 需在读取帧数据并计算环境温度后调用。
                - 损坏或异常像素会被标记为-273.15°C。
    
            ==========================================
    
            Calculate the target temperature (in Celsius) for each pixel and store it in the result list.
    
            Args:
                emissivity (float): Object emissivity, usually 0.95.
                tr (float): Reference temperature, calculated from ambient temperature.
                result (list): List for storing target temperatures, must have a length of 768.
    
            Raises:
                ValueError: Thrown when result list length is not 768.
    
            Notes:
                - Must be called after reading frame data and calculating ambient temperature.
                - Broken or outlier pixels will be marked as -273.15°C.
            """
            if len(result) != 768:
                raise ValueError("Result list must have a length of 768")
            # 当前帧的子页面编号（0 或 1）
            sub_page = self.mlx90640_frame[833]
            # alpha 温度补偿系数数组（四个范围区间用）
            alpha_corr_r = [0.0] * 4
            # 控制像素（参考像素）的红外数据（两个值，对应两个参考像素）
            ir_data_cp = [0, 0]
            # 获取电源电压 (VDD) 和环境温度 (Ta)
            vdd = self._get_vdd()
            ta = self._get_ta()
            # 转换为绝对温度 (K)，并计算四次方
            ta4 = (ta + 273.15) ** 4
            tr4 = (tr + 273.15) ** 4
            ta_tr = tr4 - (tr4 - ta4) / emissivity
            # 计算反射温度修正
            kta_scale = math.pow(2, self.kta_scale)
            kv_scale = math.pow(2, self.kv_scale)
            alpha_scale = math.pow(2, self.alpha_scale)
            # Alpha 校正系数（不同温度范围的补偿）
            alpha_corr_r[0] = 1 / (1 + self.ks_to[0] * 40)
            alpha_corr_r[1] = 1.0
            alpha_corr_r[2] = 1 + self.ks_to[1] * self.ct[2]
            alpha_corr_r[3] = alpha_corr_r[2] * (1 + self.ks_to[2] * (self.ct[3] - self.ct[2]))
    
            # 增益计算（从帧数据中提取）
            gain = self.mlx90640_frame[778]
            if gain > 32767:
                gain -= 65536
            gain = self.gain_ee / gain
    
            mode = (self.mlx90640_frame[832] & 0x1000) >> 5
            # 控制原始像素值
            ir_data_cp[0] = self.mlx90640_frame[776]
            ir_data_cp[1] = self.mlx90640_frame[808]
            for i in range(2):
                if ir_data_cp[i] > 32767:
                    ir_data_cp[i] -= 65536
                ir_data_cp[i] *= gain
            # 控制像素补偿（基于偏移、温度、电压）
            ir_data_cp[0] -= self.cp_offset[0] * (1 + self.cp_kta * (ta - 25)) * (1 + self.cp_kv * (vdd - 3.3))
            if mode == self.calibration_mode_ee:
                ir_data_cp[1] -= self.cp_offset[1] * (1 + self.cp_kta * (ta - 25)) * (1 + self.cp_kv * (vdd - 3.3))
            else:
                ir_data_cp[1] -= (self.cp_offset[1] + self.il_chess_c[0]) * (1 + self.cp_kta * (ta - 25)) * (1 + self.cp_kv * (vdd - 3.3))
            # 遍历 768 个像素，计算每个像素的温度
            for pixel_number in range(768):
                if pixel_number and pixel_number % 32 == 0:
                    await asyncio.sleep_ms(0)
                if self._is_pixel_bad(pixel_number):
                    result[pixel_number] = -273.15
                    continue
                # 行列模式相关的采样补偿计算
                il_pattern = pixel_number // 32 - (pixel_number // 64) * 2
                conversion_pattern = ((pixel_number + 2) // 4 - (pixel_number + 3) // 4 + (pixel_number + 1) // 4 - pixel_number // 4) * (
                    1 - 2 * il_pattern
                )
    
                if mode == 0:
                    pattern = il_pattern
                else:
                    chess_pattern = il_pattern ^ (pixel_number - (pixel_number // 2) * 2)
                    pattern = chess_pattern
    
                if pattern == sub_page:
                    ir_data = self.mlx90640_frame[pixel_number]
    
                    if ir_data > 32767:
                        ir_data -= 65536
    
                    ir_data *= gain
                    # 应用像素自身的偏移补偿（随 Ta/Vdd）
                    kta = self.kta[pixel_number] / kta_scale
                    kv = self.kv[pixel_number] / kv_scale
                    ir_data -= self.offset[pixel_number] * (1 + kta * (ta - 25)) * (1 + kv * (vdd - 3.3))
    
                    if mode != self.calibration_mode_ee:
                        ir_data += self.il_chess_c[2] * (2 * il_pattern - 1) - self.il_chess_c[1] * conversion_pattern
                    # 去除 TGC（温度梯度系数）影响
                    ir_data = ir_data - self.tgc * ir_data_cp[sub_page]
                    ir_data /= emissivity
    
                    alpha_compensated = (self.scale_alpha * alpha_scale / self.alpha[pixel_number]) * (1 + self.ks_ta * (ta - 25))
                    # 计算温度（Stefan-Boltzmann 辐射公式的修正）
                    sx = math.sqrt(math.sqrt(alpha_compensated * alpha_compensated * alpha_compensated * (ir_data + alpha_compensated * ta_tr)))
                    to = math.sqrt(math.sqrt((ir_data / (alpha_compensated * (1 - self.ks_to[1] * 273.15) + sx) + ta_tr))) - 273.15
    
                    if to < self.ct[1]:
                        torange = 0
                    elif to < self.ct[2]:
                        torange = 1
                    elif to < self.ct[3]:
                        torange = 2
                    else:
                        torange = 3
                    # 再次修正，得到最终温度值
                    to = (
                        math.sqrt(
                            math.sqrt(ir_data / (alpha_compensated * alpha_corr_r[torange] * (1 + self.ks_to[torange] * (to - self.ct[torange]))) + ta_tr)
                        )
                        - 273.15
                    )
    
                    result[pixel_number] = to

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
