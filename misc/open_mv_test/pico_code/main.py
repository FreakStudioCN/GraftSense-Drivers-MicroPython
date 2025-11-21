from machine import UART, Pin
import time

# Initialize UART1: TX=Pin8, RX=Pin9, baud rate 9600
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# Counter for test messages
count = 1

print("UART loopback test started. Sending data every 2 seconds...")

try:
    while True:
        
        # Send the message
        # Wait a short time for data to be received
        
        # Read and print received data
        if uart.any():
            time.sleep(0.2)
            received = uart.read(uart.any()).decode('utf-8')
            print(f"Received: {received}")


except KeyboardInterrupt:
    print("\nTest stopped by user")
