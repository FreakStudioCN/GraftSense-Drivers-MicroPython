# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:35
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : DY-SV19T 驱动“满功能”示例：在一个脚本里串联演示尽量多的外部功能方法
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

# 导入 UART 和 Pin 用于硬件串口与引脚配置
from machine import UART, Pin
# 导入 time 提供延时与时间控制
import time
# 导入驱动与常量（DYSV19T、VOLUME_MAX、DISK_*、MODE_*、CH_* 等）
from dy_sv19t import *

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 定义状态打印函数：按标题统一查询并打印播放器各项状态
def dump_status(p: DYSV19T, title: str = "") -> None:
    # 查询播放状态：返回 0=停、1=播、2=暂停
    st = p.query_status()
    # 查询当前盘符：返回 DISK_USB/DISK_SD/DISK_FLASH 或 None，并更新内部 current_disk
    disk = p.query_current_disk()
    # 查询当前曲目号：返回 1..65535 或 None
    cur = p.query_current_track()
    # 查询当前曲目已播放时间：返回 (h,m,s) 或 None
    t = p.query_current_track_time()
    # 查询当前短文件名（8.3）：返回 ASCII 短名或 None
    short = p.query_short_filename()
    # 查询设备总曲目数：返回整数或 None
    tot = p.query_total_tracks()
    # 查询当前文件夹首曲：返回曲目号或 None
    f_first = p.query_folder_first_track()
    # 查询当前文件夹曲目总数：返回整数或 None
    f_tot = p.query_folder_total_tracks()
    # 查询在线盘符位图：bit0=USB, bit1=SD, bit2=FLASH
    online = p.query_online_disks()
    # 打印标题行用于分隔不同阶段的状态
    print("\n==== {} ====".format(title))
    # 打印汇总信息：便于一次检查所有关键字段
    print("status=", st, "disk=", disk, "track=", cur, "time=", t,
          "short=", short, "total_tracks=", tot,
          "folder_first=", f_first, "folder_total=", f_tot, "online_bitmap=", online)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 初始化硬件串口：选择 UART1，波特率 9600，TX=GP4，RX=GP5（需与模块连线一致）
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# 创建播放器实例：设定默认音量/盘符/模式/通道与读取超时
player = DYSV19T(
    # 传入已配置的 UART 实例
    uart,
    # 默认音量设置为最大（0~30）
    default_volume=VOLUME_MAX,
    # 默认工作盘符选择 SD 卡
    default_disk=DISK_SD,
    # 默认播放模式设置为“单曲播放后停止”
    default_play_mode=MODE_SINGLE_STOP,
    # 默认输出通道设置为 MP3 通道
    default_dac_channel=CH_MP3,
    # 串口读取超时 600ms
    timeout_ms=600,
)
# ========================================  主程序  ===========================================

# 启动后立即查询一次状态：确认默认参数与硬件连通
dump_status(player, "boot: after init")
# 设置音量、EQ、循环模式、输出通道，并再次查询状态核对
# 将音量调整到 20（范围 0~30）
player.set_volume(20)
# 设置均衡为摇滚 EQ_ROCK
player.set_eq(EQ_ROCK)
# 设置循环模式为目录顺序播放 MODE_DIR_SEQUENCE
player.set_loop_mode(MODE_DIR_SEQUENCE)
# 选择输出通道为 MP3 数字通道
player.set_dac_channel(CH_MP3)
# 打印设置后的状态以确认参数生效
dump_status(player, "after volume/EQ/loop/channel setup")

# 从 SD 卡按“盘符 + 路径”播放指定文件 /01.MP3
player.play_disk_path(DISK_SD, "/01.MP3")
# 等待 2 秒给设备缓冲与开始播放的时间
time.sleep(2)
# 打印当前状态，检查曲目、时间、短文件名是否随之更新
dump_status(player, "after play_disk_path('/01.MP3')")

# 播放控制流程：暂停 → 继续播放 → 下一首 → 上一首，并间隔打印状态
# 暂停当前播放
player.pause(); time.sleep(4); dump_status(player, "after pause")
# 恢复播放到“播放”状态
player.play(); time.sleep(2); dump_status(player, "after resume play")
# 跳转到下一曲目
player.next_track(); time.sleep(4); dump_status(player, "after next_track")
# 返回上一曲目
player.prev_track(); time.sleep(4); dump_status(player, "after prev_track")

# 选曲演示：先“选择并播放”曲目 2，然后“仅预选不播放”曲目 3
# 选择曲目 2 并立即开始播放（范围 1..65535）
player.select_track(2, play=True)
# 留出 4 秒以便切换与播放进度推进
time.sleep(4)
# 打印状态确认当前曲目已切至 2
dump_status(player, "after select_track(2, play=True)")
# 仅预选曲目 3，不立即开始播放
player.select_track_no_play(3)
# 留出 4 秒以便查询接口返回
time.sleep(4)
# 打印状态确认已预选曲目（部分设备可能仅在开始播放后更新）
dump_status(player, "after select_track_no_play(3)")

# 循环与复读：设置“单曲循环”，设定循环次数 3，A-B 复读区间 00:20 ~ 00:25，等待 20 秒后结束复读
# 选择“单曲循环”模式 MODE_SINGLE_LOOP
player.set_loop_mode(MODE_SINGLE_LOOP)
# 设定循环次数为 3（注意部分模式不支持，若不支持会在驱动层抛参数错误）
player.set_loop_count(3)
# 设置 A-B 复读区间（起点分:秒，终点分:秒）
player.play()
player.repeat_area(0, 20, 0, 25)
# 等待 20 秒，让复读区间至少执行一次
time.sleep(20)
# 结束 A-B 复读并恢复正常播放
player.end_repeat()
# 打印状态确认当前复读已关闭
dump_status(player, "after loop_count & A-B repeat")

# 快进/快退演示：向前跳播 10 秒，再向后回退 5 秒
# 快进 10 秒（0..65535）
player.seek_forward(10)
# 留出 4 秒以便查询时间变化
time.sleep(4)
# 快退 5 秒（0..65535）
player.seek_back(5)
# 留出 4 秒以便查询时间变化
time.sleep(4)
# 打印状态确认时间点已变化
dump_status(player, "after seek forward/back")

# 音量微调：先“+1”、“-1”，最后直接设定为 22，并打印状态
# 音量加 1 级
player.volume_up(); time.sleep(0.5)
# 音量减 1 级
player.volume_down(); time.sleep(0.5)
# 直接指定音量为 22
player.set_volume(22)
# 打印状态确认音量与其余参数
dump_status(player, "after volume up/down & set 22")

# 插播曲目演示：从 SD 卡插播曲目 1，停留 4 秒后结束插播并打印状态
# 插播曲目号 1（插播期间优先播放插播内容）
player.insert_track(DISK_SD, 1)
# 留出 4 秒以便听到插播效果
time.sleep(4)
# 结束插播，恢复到插播前播放流程
player.end_insert()
# 打印状态确认插播已结束
dump_status(player, "after insert_track & end_insert")

# 插播路径演示：尝试插播 /02.MP3（若不存在会触发路径/字符集等校验异常）
try:
    # 插播指定路径文件（路径需以 ‘/’ 起始，名称建议 8.3）
    player.insert_path(DISK_SD, "/02.MP3")
    # 留出 4 秒以便插播生效
    time.sleep(4)
    # 结束插播恢复原播放
    player.end_insert()
    # 打印状态确认插播路径流程结束
    dump_status(player, "after insert_path('/02.MP3') & end_insert")
# 捕获路径校验或参数错误异常并提示
except ValueError as e:
    print("insert_path ValueError:", e)

# 组合播放演示（ZH 文件夹下短名）：按短名序列 '01' → '02' 进行组合播放后关闭
try:
    # 启动组合播放：短名必须是 2 字节 A-Z/0-9，例如 '01'
    player.start_combination_playlist(['01', '02'])
    # 留出 2 秒以便组合播放启动
    time.sleep(2)
    # 结束组合播放
    player.end_combination_playlist()
    # 打印状态确认组合播放已结束
    dump_status(player, "after combination playlist ['01','02']")
# 捕获短名格式不合法等参数错误
except ValueError as e:
    print("combination playlist ValueError:", e)

# 播放时间自动上报演示：使能后监听 3 次 0x25 上报帧（h:m:s）
# 开启播放时间自动上报（设备将周期性上报当前播放时间）
player.enable_play_time_send()
# 提示开始监听
print("Enable automatic reporting of playback time, monitoring 3 times...")
# 循环监听 3 次自动上报
for i in range(3):
    # 接收期望命令 0x25 的上报帧，超时 1500ms
    resp = player.recv_response(expected_cmd=0x25, timeout_ms=1500)
    # 若成功收到完整帧
    if resp:
        # 解析帧得到数据段
        parsed = player.parse_response(resp)
        d = parsed['data']
        # 数据长度为 3 字节时按 (h, m, s) 打印
        if len(d) == 3:
            print("[auto time] h:m:s =", (d[0], d[1], d[2]))
    # 超时未收到上报
    else:
        print("[auto time] No report submitted within the time limit")
# 关闭播放时间自动上报
player.disable_play_time_send()

# 最后停止播放，短暂等待后打印收尾状态
player.stop(); time.sleep(0.5)
dump_status(player, "final: after stop")
