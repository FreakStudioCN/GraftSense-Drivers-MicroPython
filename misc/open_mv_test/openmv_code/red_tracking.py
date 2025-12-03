import sensor
import time
from pyb import UART
# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)  # 使用较低分辨率提高性能
sensor.skip_frames(time=1000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()
# 固定红色阈值 (LAB颜色空间)
# 这些值可能需要根据您的环境调整
red_threshold = (20, 70, 30, 80, 15, 65)
uart = UART(1, 9600)
print("开始寻找红色色块...")

while True:
    clock.tick()
    img = sensor.snapshot()

    # 寻找红色色块
    blobs = img.find_blobs(
        [red_threshold],
        pixels_threshold=100,
        area_threshold=100,
        merge=True,
        margin=10
    )

    if blobs:
        # 找到所有红色色块
        for blob in blobs:
            # 绘制色块矩形和中心十字
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())

            # 打印坐标信息
            uart.write("Red Blob - X:%d, Y:%d, W:%d, H:%d\n" % (
                blob.cx(), blob.cy(), blob.w(), blob.h()))
            print("红色色块 - X:%d, Y:%d, 宽度:%d, 高度:%d" % (
                blob.cx(), blob.cy(), blob.w(), blob.h()))
    else:
        # 没有找到红色色块
       # uart.write("No red blob found\n")
        print("未发现红色色块")

    # 打印帧率
    print("帧率: %d" % clock.fps())
