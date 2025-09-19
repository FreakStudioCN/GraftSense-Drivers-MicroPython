while True:
    ok,resp = gps._recv()
    if ok:
        print(resp)
        for i in resp:
            parsed_sentence = gps.update(i)

        # 每解析1个有效句子，输出一次关键数据
        if parsed_sentence :  # 仅当定位有效时输出
            print("="*50)
            print(f"解析句子类型：{parsed_sentence}")
            print(f"本地时间：{gps.timestamp[0]:02d}:{gps.timestamp[1]:02d}:{gps.timestamp[2]:.1f}")
            print(f"本地日期：{gps.date_string(formatting='s_dmy', century='20')}")
            print(f"纬度：{gps.latitude_string()}")
            print(f"经度：{gps.longitude_string()}")
            print(f"速度：{gps.speed_string(unit='kph')}")
            print(f"海拔：{gps.altitude} 米")
            print(f"使用卫星数：{gps.satellites_in_use} 颗")
            print("="*50)