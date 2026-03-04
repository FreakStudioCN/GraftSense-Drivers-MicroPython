from sim7600 import SIM7600
from sim7600.sms import SMS
import machine

# Initialize the SIM7600 module
uart = machine.UART(1, baudrate=115200, tx=17, rx=16)
sim7600 = SIM7600(uart)




sms = SMS(sim7600)

# Send an SMS
sms.send_sms('+1234567890', 'Hello, world!')

# Read an SMS
response = sms.read_sms(1)
print(response)

# Delete an SMS
sms.delete_sms(1)

# List all SMS
response = sms.list_sms('ALL')
print(response)