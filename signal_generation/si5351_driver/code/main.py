from silicon5351 import SI5351_I2C

import sys
if sys.implementation.name == 'circuitpython':
    import board, busio
    # i2c = busio.I2C(scl=board.SCL, sda=board.SDA) # XIAO RP2040
    i2c = busio.I2C(scl=board.GP5, sda=board.GP4)   # PICO
    while not i2c.try_lock():
        pass
else:
    import machine
    i2c = machine.I2C(1, scl=machine.Pin(7), sda=machine.Pin(6))

crystal = 25e6     # crystal frequency
mul = 15           # 15 * 25e6 = 375 MHz PLL frequency
freq = 2.0e6       # output frequency with an upper limit 200MHz
quadrature = True  # lower limit for quadrature is 375MHz / 128
invert = False     # invert option ignored when quadrature is true

si = SI5351_I2C(i2c, crystal=crystal)
si.setup_pll(pll=0, mul=mul)
si.init_clock(output=0, pll=0)
si.init_clock(output=1, pll=0, quadrature=quadrature, invert=invert)
si.set_freq_fixedpll(output=0, freq=freq) 
si.set_freq_fixedpll(output=1, freq=freq) 
si.enable_output(output=0)
si.enable_output(output=1)
print(f'done freq={freq} mul={mul} quadrature={quadrature} invert={invert}')


