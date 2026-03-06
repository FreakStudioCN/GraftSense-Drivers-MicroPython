from sim7600 import SIM7600
from sim7600.calling import Calling
import machine

# Initialize the SIM7600 module
uart = machine.UART(1, baudrate=115200, tx=17, rx=16)
sim7600 = SIM7600(uart)

calling = Calling(sim7600)

# Make a call
calling.make_call('+1234567890')

# Hang up the call
calling.hang_up()

# Answer an incoming call
calling.answer_call()

# Check call status
status = calling.call_status()
print(status)

# Set call volume
calling.set_call_volume(5)