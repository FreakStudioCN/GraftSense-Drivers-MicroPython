from machine import Pin, SoftI2C
i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=400000)

radio = Radio(i2c, freq=106.7)
print('Frequency: FM {}\nReady: {}\nStereo: {}\nADC level: {}'.format(
    radio.frequency, radio.is_ready,  radio.is_stereo, radio.signal_adc_level))