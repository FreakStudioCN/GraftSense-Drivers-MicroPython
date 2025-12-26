# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/17 16:35
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : DY-SV19T 示例
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

# 导入 UART 和 Pin 用于硬件串口与引脚配置
from machine import UART, Pin, Timer
# 导入 time 提供延时与时间控制
import time
# 导入驱动与常量（DYSV19T、VOLUME_MAX、DISK_*、MODE_*、CH_* 等）
from dy_sv19t import *

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def tick(timer):
    """
    定时器回调函数
    Args:
        timer:为监测播放进度条的定时器
    Raises:
        TypeError:计时器必须是Timer的一个实例

    ============================================================

    Args:
        timer: a timer used to monitor the playback progress bar
     Raises:
         TypeError:timer must be an instance of Timer
    """
    if not isinstance(timer, Timer):
        raise TypeError("timer must be an instance of Timer")
    # 查看播放进度方法
    hms = player.check_play_time_send()
    if hms:
        h, m, s = hms
        print("[auto time] h:m:s =", h, m, s)

def play_track_demo():
    """

    通过文件路径直接播放一段音频，监听播放进度并等待播放结束。

    ==========================================================

    Use the combined playback function to play multiple track combinations
    and end the combined playback after a specified time.

    """
    # 根据文件路径选择立即播放
    player.play_disk_path(DYSV19T.DISK_SD, "/AA./01.MP3")
    # 开始监听播放进度
    player.enable_play_time_send()
    print("Enable automatic reporting of playback time, monitoring 3 times...")
    # 关闭监听播放进度
    # player.disable_play_time_send()

    # 等待结束
    while player.query_status():
        pass
    print("play_track_demo ends")

def select_and_play_demo():

    """
    选择曲目但不立即播放，并展示暂停、恢复、切换曲目的用法。

    ==========================================================

    Select a track without playing it immediately, and demonstrate the usage of pause,
    resume, and track switching.
    """
    # 根据文件路径选择不播放：曲目序号是由存储顺序决定！
    player.select_track(1, play=False)
    print("Select track 1 no play")
    # 5秒后播放曲目1
    time.sleep(5)
    # 开始播放之前当前选择的曲目
    player.play()

    # 暂停当前播放
    # player.pause()
    # time.sleep(4)

    # 恢复播放到“播放”状态
    # player.play()
    # time.sleep(2)

    # 跳转到下一曲目
    # player.next_track()
    # time.sleep(4)

    # 返回上一曲目
    # player.prev_track()
    # time.sleep(4)

    # 停止播放
    # player.stop()
    # 等待结束
    while player.query_status():
        pass
    print("play_track_demo ends")


def repeat_area_demo():
    """
    设置 A-B 区间复读，并在一段时间后关闭复读。

    ==========================================================
    Set the A-B interval for repeated reading and turn off the repeated reading after a period of time.

    """
    print("repeat_area_demo")
    # 设置 A-B 复读区间（起点分:秒，终点分:秒）
    player.select_track(4, play=False)
    # 播放
    player.play()
    # 设置复读从0分20秒到0分25秒截取复读
    player.repeat_area(0, 20, 0, 25)
    # 等待复读效果
    time.sleep(20)
    # 关闭复读效果
    player.end_repeat()
    # 等待复读关闭后效果
    time.sleep(20)
    # 停止播放
    player.stop()
    print("repeat_area_demo ends")

def loop_mode_demo():
    """
    设置循环播放模式，并指定循环次数。

    ==========================================================
    Set the loop playback mode and specify the number of loops.

    """
    # 设置播放模式支持循环次数设置
    player.set_play_mode(DYSV19T.MODE_SINGLE_LOOP)
    # 设定循环次数为 3（注意部分模式不支持，若不支持会在驱动层抛参数错误）
    player.set_loop_count(3)
    # 播放第一段音频，立即播放
    player.select_track(1, play=True)
    time.sleep(10)
    # 设置播放模式为单曲停止
    player.set_play_mode(DYSV19T.MODE_SINGLE_STOP)



def insert_track_demo():
    """
    在播放过程中插入另一段音频。

    ==========================================================
    Insert another audio segment during playback.

    """
    print("insert_track_demo")
    # 播放第四段音频，立即播放
    player.select_track(4, play=True)
    # 等待正常播放
    time.sleep(10)
    # 插入第一段音频
    player.insert_track(DYSV19T.DISK_SD, 1)
    # 等待结束
    while player.query_status():
        pass
    print("insert_track_demo ends")


def combination_playlist_demo():
    """

    播放多个曲目组合，并在指定时间后结束组合播放。

    =========================================================
    Use the combined playback function to play multiple
    track combinations and end the combined playback after a specified time.

    """
    print("combination_playlist_demo")
    player.start_combination_playlist(['Z1', 'Z2'])
    # 留出 2 秒以便组合播放启动
    time.sleep(10)
    # 结束组合播放
    player.end_combination_playlist()
    print("combination_playlist_demo ends")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试消息
print("FreakStudio:  DY-SV19T Play Test ")

# 初始化硬件串口：选择 UART0，波特率 9600，TX=GP16，RX=GP17（需与模块连线一致）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))

# 创建定时器
tim = Timer(-1)
# 初始化定时器：每 1000ms（1秒）触发一次
tim.init(period=1000, mode=Timer.PERIODIC, callback=tick)

# 创建播放器实例：设定默认音量/盘符/模式/通道与读取超时
player = DYSV19T(
    # 传入已配置的 UART 实例
    uart,
    # 默认音量设置为最大（0~30）
    default_volume=DYSV19T.VOLUME_MAX,
    # 默认工作盘符选择 SD 卡
    default_disk=DYSV19T.DISK_SD,
    # 默认播放模式设置为“单曲播放后停止”
    default_play_mode=DYSV19T.MODE_SINGLE_STOP,
    # 默认输出通道设置为 MP3 通道
    default_dac_channel=DYSV19T.CH_MP3,
    # 串口读取超时 600ms
    timeout_ms=600,
)

# ========================================  主程序  ===========================================

# 将音量调整到 20（范围 0~30）
player.set_volume(20)
# 设置均衡为摇滚 EQ_ROCK
player.set_eq(player.EQ_ROCK)
# 设置循环模式为目录顺序播放后停止 MODE_DIR_SEQUENCE
player.set_play_mode(player.MODE_SINGLE_STOP)
# 选择输出通道为 MP3 数字通道
player.set_dac_channel(player.CH_MP3)
# 通过曲目序号直接播放一段音频，监听播放进度并等待播放结束。

player.query_status()
# 查询当前盘符：返回 DISK_USB/DISK_SD/DISK_FLASH 或 None，并更新内部 current_disk
player.query_current_disk()
# 查询当前曲目号：返回 1..65535 或 None
player.query_current_track()
# 查询当前曲目总播放时间：返回 (h,m,s) 或 None
player.query_current_track_time()
# 查询当前短文件名（8.3）：返回 ASCII 短名或 None
player.query_short_filename()
# 查询设备总曲目数：返回整数或 None
player.query_total_tracks()
# 查询当前文件夹首曲：返回曲目号或 None
player.query_folder_first_track()
# 查询当前文件夹曲目总数：返回整数或 None
player.query_folder_total_tracks()
# 查询在线盘符位图：bit0=USB, bit1=SD, bit2=FLASH
player.query_online_disks()
player.enable_play_time_send()
player.play()

# 通过曲目序号直接播放一段音频，监听播放进度并等待播放结束。
# play_track_demo()

# 选择曲目但不立即播放，并展示暂停、恢复、切换曲目的用法
# select_and_play_demo()

# 设置 A-B 区间复读，并在一段时间后关闭复读。
# repeat_area_demo()

# 在播放过程中插入另一段音频。
# insert_track_demo()

# 播放多个曲目组合，并在指定时间后结束组合播放。
# combination_playlist_demo()

# 设置循环播放模式，并指定循环次数。
# loop_mode_demo()
