from sim800 import SIM800

sim800 = SIM800(uart_pin=1, baud=115200)
sim800.dial_number('+1234567890')

# To hang up the call
sim800.hang_up()