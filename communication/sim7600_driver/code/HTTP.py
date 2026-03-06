from sim7600.http import HTTP
from sim7600 import SIM7600
import machine

# Initialize the SIM7600 module
uart = machine.UART(1, baudrate=115200, tx=17, rx=16)
sim7600 = SIM7600(uart)
http = HTTP(sim7600)

# Set APN
http.set_apn("your_apn", "username", "password")

# Enable HTTP
http.enable_http()

# Set URL
http.set_url("http://example.com")

# Perform a GET request
response = http.get()
print(response)

# Perform a POST request
response = http.post("key1=value1&key2=value2")
print(response)

# Read HTTP response
response = http.read_response()
print(response)

# Disable HTTP
http.disable_http()
