import machine
import time

class SIM7600:
    def __init__(self, uart_id, tx_pin, rx_pin, baudrate=115200):
        self.uart = machine.UART(uart_id, baudrate=baudrate, tx=tx_pin, rx=rx_pin)

    def send_command(self, command, timeout=3000):
        command += '\r\n'
        self.uart.write(command)
        start_time = time.ticks_ms()
        response = []
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            if self.uart.any():
                response.append(self.uart.read().decode())
        return ''.join(response)

    def power_on(self):
        return self.send_command('AT+CFUN=1')

    def power_off(self):
        return self.send_command('AT+CPOF')

    def reset_module(self):
        return self.send_command('AT+CRESET')

    def set_power_mode(self, mode):
        return self.send_command(f'AT+CSCLK={mode}')

    def monitor_voltage(self):
        return self.send_command('AT+CBC')

    def connect(self, apn, user='', password=''):
        self.send_command('AT+CGATT=1')
        self.send_command(f'AT+CSTT="{apn}","{user}","{password}"')
        self.send_command('AT+CIICR')
        return self.send_command('AT+CIFSR')

    def disconnect(self):
        return self.send_command('AT+CGATT=0')

    def get_network_status(self):
        return self.send_command('AT+CREG?')

    def set_flight_mode(self, enable):
        return self.send_command(f'AT+CFUN={0 if enable else 1}')
