from machine import Pin, SoftI2C
import time
from mems_air_module import MEMSGasSensor, PCA9546ADR
i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
pca = PCA9546ADR(i2c)
pca.disable_all()
pca.select_channel(0)
voc_sensor = MEMSGasSensor(i2c=i2c, sensor_type=MEMSGasSensor.TYPE_VOC, addr7=0x2A)
calib_success = voc_sensor.calibrate_zero()
