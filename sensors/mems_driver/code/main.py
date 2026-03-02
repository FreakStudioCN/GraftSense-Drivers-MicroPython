from machine import Pin, SoftI2C
import time
from mems_air_module import MEMSGasSensor, PCA9546ADR,AirQualityMonitor
i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
monitor = AirQualityMonitor(i2c)

monitor.register_sensor(0, MEMSGasSensor.TYPE_VOC)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_VOC)
monitor.register_sensor(1, MEMSGasSensor.TYPE_CO)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_CO)
monitor.register_sensor(2, MEMSGasSensor.TYPE_H2S)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_H2S)
monitor.register_sensor(3, MEMSGasSensor.TYPE_NO2)
monitor.calibrate_sensor(MEMSGasSensor.TYPE_NO2)
while True:
    try:
        # 获取当前气体浓度
        results = monitor.read_all()
        print(f"VOC: {results[MEMSGasSensor.TYPE_VOC]}")
        print(f"CO: {results[MEMSGasSensor.TYPE_CO]}")
        print(f"H2S: {results[MEMSGasSensor.TYPE_H2S]}")
        print(f"NO2: {results[MEMSGasSensor.TYPE_NO2]}")

    except Exception as e:
        print(f"Error reading concentration: {e}")
    # 每隔1s测试一次
    time.sleep(1)
