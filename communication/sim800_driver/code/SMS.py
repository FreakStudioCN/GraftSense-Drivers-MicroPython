from sim800 import SIM800
from sim800 import SIM800SMS

sim800 = SIM800(uart_pin=1, baud=115200)

sim800 = SIM800SMS(uart_pin=1)
sim800.send_sms('+1234567890', 'Hello World')