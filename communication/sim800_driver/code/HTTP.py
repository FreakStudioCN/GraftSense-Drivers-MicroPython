from sim800 import SIM800
sim800 = SIM800(uart_pin=1, baud=115200)

from sim800 import SIM800TCPIP
sim800 = SIM800TCPIP(uart_pin=1)
sim800.http_init()
sim800.http_set_param("URL", "http://example.com")
response = sim800.http_get()
print(response)
sim800.http_terminate()