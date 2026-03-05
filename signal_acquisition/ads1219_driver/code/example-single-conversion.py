from machine import Pin
from machine import I2C
from ads1219 import ADS1219
import utime

# This example demonstrates how to use the ADS1219 using single-shot conversion mode 
# The ADC1219 will initiate a conversion when adc.read_data() is called 

i2c = I2C(scl=Pin(26), sda=Pin(27))
adc = ADS1219(i2c)

adc.set_channel(ADS1219.CHANNEL_AIN0)
adc.set_conversion_mode(ADS1219.CM_SINGLE)
adc.set_gain(ADS1219.GAIN_1X)
adc.set_data_rate(ADS1219.DR_20_SPS)  # 20 SPS is the most accurate
adc.set_vref(ADS1219.VREF_INTERNAL)

while True:
    result = adc.read_data()
    print('result = {}, mV = {:.2f}'.format(result, 
            result * ADS1219.VREF_INTERNAL_MV / ADS1219.POSITIVE_CODE_RANGE))
    utime.sleep(0.5)      