import machine
import time
from micropython import const


class AD8232:
    def __init__(self, adc_pin=26, loff_plus_pin=16, loff_minus_pin=17,sdn_pin=None):
        """
        初始化AD8232心率传感器 (Pico版本)

        注意: Pico的ADC引脚是26-28 (GP26-28)，不是34
        参数:
            adc_pin: ADC输入引脚 (GP26, GP27, 或 GP28)
            loff_plus_pin: 导联脱落检测+ (GP16)
            loff_minus_pin: 导联脱落检测- (GP17)
        """
        # ADC引脚初始化 (Pico的ADC)
        self.adc = machine.ADC(adc_pin)

        # 导联脱落检测引脚
        self.loff_plus = machine.Pin(loff_plus_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.loff_minus = machine.Pin(loff_minus_pin, machine.Pin.IN, machine.Pin.PULL_UP)

        # 数据缓冲区参数
        self.MAX_BUFFER = const(100)
        self.prev_data = [0] * self.MAX_BUFFER
        self.sum_data = 0
        self.max_data = 0
        self.avg_data = 0
        self.roundrobin = 0
        self.count_data = 0
        self.sdn_pin = None
        self.lead_status = False
        # 心率计算参数
        self.period = 0
        self.last_period = 0
        self.millis_timer = time.ticks_ms()
        self.frequency = 0.0
        self.beats_per_min = 0.0
        # 工作状态可能浮空，所以默认值是2 (未知)
        self.operating_status = 2
        # 数据采集状态
        self.new_data = 0

        print(f"AD8232初始化完成 - ADC引脚: GP{adc_pin}")
        print(f"导联检测: LO+ GP{loff_plus_pin}, LO- GP{loff_minus_pin}")
    def off(self):
        """
        关闭AD8232传感器 (如果有SDN引脚)
        """
        if hasattr(self, 'sdn_pin') and self.sdn_pin is not None:
            self.sdn_pin.value(0)  # 设置为低电平关闭传感器
            self.operating_status = 3
            print("AD8232传感器已关闭")
        else:
            print("未配置SDN引脚，无法关闭传感器")
    def on(self):
        """
        打开AD8232传感器 (如果有SDN引脚)
        """
        if hasattr(self, 'sdn_pin') and self.sdn_pin is not None:
            self.sdn_pin.value(1)  # 设置为高电平打开传感器
            self.operating_status = 1
            print("AD8232传感器已打开")
        else:
            print("未配置SDN引脚，无法打开传感器")
    def read_raw(self):
        """
        读取原始ADC数据 (12位, 0-4095)
        对应Arduino: newData = analogRead(pin)
        """
        self.new_data = self.adc.read_u16() >> 4  # 16位转12位 (0-4095)
        return self.new_data

    def check_leads_off(self):
        """
        检查导联是否脱落
        返回: True - 导联脱落, False - 正常连接
        """
        # 当导联正常连接时，两个引脚都是低电平(0)
        # 当导联脱落时，至少一个引脚是高电平(1)
        self.lead_status = self.loff_plus.value() == 1 or self.loff_minus.value() == 1
        return self.lead_status

    def freq_detect(self):
        """
        心率信号处理 - 对应Arduino的freqDetec()函数
        逻辑与原始代码完全一致
        """
        # 1. 心跳检测 (缓冲区满后才开始检测)
        if self.count_data == self.MAX_BUFFER:
            if (self.prev_data[self.roundrobin] < self.avg_data * 1.5 and
                    self.new_data >= self.avg_data * 1.5):
                # 检测到心跳：计算周期
                current_time = time.ticks_ms()
                self.period = time.ticks_diff(current_time, self.millis_timer)
                self.millis_timer = current_time
                self.max_data = 0  # 重置最大值

        # 2. 环形缓冲区管理
        self.roundrobin += 1
        if self.roundrobin >= self.MAX_BUFFER:
            self.roundrobin = 0

        # 3. 移动平均计算 (增量计算提高效率)
        if self.count_data < self.MAX_BUFFER:
            self.count_data += 1
            self.sum_data += self.new_data
        else:
            self.sum_data += self.new_data - self.prev_data[self.roundrobin]

        self.avg_data = self.sum_data // self.count_data

        # 4. 更新最大值
        if self.new_data > self.max_data:
            self.max_data = self.new_data

        # 5. 存储当前数据
        self.prev_data[self.roundrobin] = self.new_data

    def calculate_hr(self):
        """
        计算心率 - 对应Arduino的心率计算部分
        返回: 心率值(BPM)或None(如果无效)
        """
        if self.period != self.last_period and self.period > 0:
            # 频率 = 1000 / 周期(ms) - 转换为Hz
            self.frequency = 1000.0 / self.period

            # 转换为每分钟心跳数
            bpm = self.frequency * 60.0

            # 过滤不合理的数据 (20-200 BPM)
            if 20.0 <= bpm <= 200.0:
                self.beats_per_min = bpm
                self.last_period = self.period
                return self.beats_per_min

        return None

    def read_heart_rate(self):
        """
        完整的心率读取流程
        返回: (原始数据, 心率BPM或None, 导联状态)
        """
        # 检查导联连接状态
        leads_off = self.check_leads_off()

        if leads_off:
            # 导联脱落，不进行心率计算
            raw_value = self.read_raw()
            # 但仍然更新缓冲区以保持数据流
            self.new_data = raw_value
            self.freq_detect()
            return raw_value, None, True

        # 1. 读取原始数据
        raw_value = self.read_raw()

        # 2. 信号处理
        self.freq_detect()

        # 3. 计算心率
        bpm = self.calculate_hr()

        return raw_value, bpm, False

    def get_signal_quality(self):
        """
        获取信号质量指标
        返回: 信号质量百分比 (0-100%)
        """
        if self.max_data > 0 and self.avg_data > 0:
            # 基于信号动态范围评估质量
            dynamic_range = (self.max_data - min(self.prev_data)) / 4095.0
            return min(100, int(dynamic_range * 100))
        return 0

    def get_buffer_stats(self):
        """
        获取缓冲区统计信息
        返回: 字典包含统计信息
        """
        return {
            'avg': self.avg_data,
            'max': self.max_data,
            'count': self.count_data,
            'buffer_size': self.MAX_BUFFER,
            'buffer_filled': self.count_data >= self.MAX_BUFFER,
            'signal_quality': self.get_signal_quality()
        }

    def reset(self):
        """
        重置所有参数 - 用于重新开始监测
        """
        self.prev_data = [0] * self.MAX_BUFFER
        self.sum_data = 0
        self.max_data = 0
        self.avg_data = 0
        self.roundrobin = 0
        self.count_data = 0
        self.period = 0
        self.last_period = 0
        self.millis_timer = time.ticks_ms()
        self.frequency = 0.0
        self.beats_per_min = 0.0
        print("AD8232参数已重置")

    def calibrate(self, duration_ms=2000):
        """
        校准传感器 - 获取基线值
        参数:
            duration_ms: 校准持续时间(毫秒)
        """
        print("开始校准... 请保持静止")
        samples = []
        start_time = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
            samples.append(self.read_raw())
            time.sleep_ms(5)

        baseline = sum(samples) // len(samples)
        print(f"校准完成 - 基线值: {baseline}")
        return baseline


# 使用示例
def example_basic():
    """
    基本使用示例 - 实时显示心率
    """
    # 创建AD8232实例
    # Pico的ADC引脚: 26, 27, 28
    ecg = AD8232(adc_pin=26, loff_plus_pin=16, loff_minus_pin=17)

    print("AD8232心率监测启动...")
    print("按Ctrl+C停止\n")

    # 可选: 进行校准
    # ecg.calibrate(2000)

    sample_count = 0

    try:
        while True:
            # 读取心率和原始数据
            raw_value, bpm, leads_off = ecg.read_heart_rate()

            # 每50次采样显示一次结果
            sample_count += 1
            if sample_count % 50 == 0:
                if leads_off:
                    print("警告: 导联脱落! 请检查电极连接")
                elif bpm is not None:
                    stats = ecg.get_buffer_stats()
                    quality = stats['signal_quality']
                    print(f"原始: {raw_value:4d} | 心率: {bpm:5.1f} BPM | 信号质量: {quality}%")
                else:
                    print(f"原始: {raw_value:4d} | 正在检测心跳...")

            # 延迟5ms (与Arduino的delay(5)对应)
            time.sleep_ms(5)

    except KeyboardInterrupt:
        print("\n程序结束")

    finally:
        # 显示最终统计
        stats = ecg.get_buffer_stats()
        print(f"\n最终统计:")
        print(f"缓冲区填充: {stats['count']}/{stats['buffer_size']}")
        print(f"平均信号值: {stats['avg']}")
        print(f"最大信号值: {stats['max']}")

