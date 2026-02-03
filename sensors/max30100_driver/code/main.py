from machine import I2C, Pin
import max30100
import time

red = None
ir = None


i2cMAX30100=I2C(0, scl=Pin((5)), sda=Pin((4)))
max30100Sensor = max30100.MAX30100(i2c = i2cMAX30100)
max30100Sensor.enable_spo2()
while True:
  max30100Sensor.read_sensor()
  red = max30100Sensor.red

  ir = max30100Sensor.ir

  print(f"red{red}")
  print(f"ir:{ir}")
  time.sleep_ms(200)