# MicroPython-SI1145
## SI1145: A digital sensor of UV Index/IR/Visible Light/Proximity
The SI1145 is a sensor from Silicon Laboratories with a calibrated light sensing algorithm that can calculate UV Index.
### DataSheet: 
https://www.silabs.com/documents/public/data-sheets/Si1145-46-47.pdf
### Features:
 - IR Sensor Spectrum: Wavelength: 550nm-1000nm (centered on 800)
 - Visible Light Sensor Spectrum: Wavelength: 400nm-800nm (centered on 530)
 - Voltage Supply: Power with 3-5VDC
 - Output Type: I2C address 0x60 (7-bit)
 - Operating Temperature: -40°C ~ 85°C
## Driver version for developers
The driver version for developers (si1145-dev.py) is slightly larger in size as it contains comments to help understanding
## Testing
Download one of the following codes for your device:
#### ESP8266
```python
# ESP8266 simple teste
import machine
import si1145
import time
i2c = machine.I2C(
    sda=machine.Pin(4),
    scl=machine.Pin(5))
sensor = si1145.SI1145(i2c=i2c)
for i in range(10):
    uv = sensor.read_uv
    ir = sensor.read_ir
    view = sensor.read_visible
    print(" UV: %f\n IR: %f\n Visible: %f" % (uv, ir, view))
    time.sleep(1)
```
#### ESP32
```python
# ESP32 simple teste
import machine
import si1145
import time
i2c = machine.I2C(
    sda=machine.Pin(21),
    scl=machine.Pin(22))
sensor = si1145.SI1145(i2c=i2c)
for i in range(10):
    uv = sensor.read_uv
    ir = sensor.read_ir
    view = sensor.read_visible
    print(" UV: %f\n IR: %f\n Visible: %f" % (uv, ir, view))
    time.sleep(1)
```
#### LoPy
```python
# LoPy simple teste
from machine import I2C
import si1145
import time
i2c = I2C(0, I2C.MASTER, baudrate=100000)
sensor = si1145.SI1145(i2c=i2c)
for i in range(10):
    uv = sensor.read_uv
    ir = sensor.read_ir
    view = sensor.read_visible
    print(" UV: %f\n IR: %f\n Visible: %f" % (uv, ir, view))
    time.sleep(1)
```
#### BBC Micro:bit
```python
# Micro:bit simple teste
from microbit import i2c
import si1145
import time

sensor = si1145.SI1145(i2c=i2c)
for i in range(10):
    uv = sensor.read_uv()
    ir = sensor.read_ir()
    view = sensor.read_visible()
    print(" UV: {}\n IR: {}\n Visible: {}".format(uv, ir, view))
    time.sleep(1)
```
