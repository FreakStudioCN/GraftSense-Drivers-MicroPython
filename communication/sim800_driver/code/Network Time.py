from sim800 import SIM800

sim800 = SIM800(uart_pin=1, baud=115200)

time = sim800.get_network_time()
print(time)
