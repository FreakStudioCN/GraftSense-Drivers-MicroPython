from machine import UART, Pin
import time

# Initialize UART1: TX=Pin8, RX=Pin9, baud rate 9600
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# Counter for test messages
count = 1

print("UART loopback test started. Sending data every 2 seconds...")

try:
    while True:
        # Create test message with counter
        test_msg = f"Test message {count}: Hello, UART loopback!"
        print(f"\nSent: {test_msg}")
        
        # Send the message
        uart.write(test_msg.encode('utf-8'))
        
        # Wait a short time for data to be received
        time.sleep(0.1)
        
        # Read and print received data
        if uart.any():
            received = uart.read(uart.any()).decode('utf-8')
            print(f"Received: {received}")
        else:
            print("Received: No data (check connections)")
        
        # Increment counter and wait 2 seconds before next send
        count += 1
        time.sleep(2)

except KeyboardInterrupt:
    print("\nTest stopped by user")
