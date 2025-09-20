from machine import UART, Pin
from r60abd1 import R60ABD1
import time

uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

dev = R60ABD1(uart)

def show(label, value, unit=""):
        print(f"→ {label}：{value}{unit}")

dev.disable_all_reports_and_check()
print("\n【查询输出】")
while True:
    val = dev.q_presence();            show("人体存在", "存在" if val==1 else ("不存在" if val==0 else None))
    val = dev.q_motion_param();        show("体动参数", val)
    val = dev.q_distance();            show("距离", val, " cm")
    pos = dev.q_position()
    if pos is None:
        show("方位 (x,y,z)", None)
    else:
        x,y,z = pos; print(f"→ 方位 (x, y, z)：({x}, {y}, {z})")
        val = dev.q_hr_value();            show("心率", val, " bpm")
        wf = dev.q_hr_waveform()  # -> [-128..127] 的 5 个点，或 None
        if wf:print("HR waveform (centered):", wf)


    val = dev.q_sleep_end_time();      show("睡眠截止时间", val, " 分钟")
    val = dev.q_struggle_sensitivity()
    if val is None:
        show("挣扎灵敏度", None)
    else:
        mapping = {0:"低",1:"中",2:"高"}; show("挣扎灵敏度", mapping.get(val, f"未知({val})"))

