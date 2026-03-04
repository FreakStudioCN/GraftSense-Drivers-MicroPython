import utime

class SIM800Utils:
    @staticmethod
    def wait_for_response(uart, expected_response, timeout=5000):
        start_time = utime.ticks_ms()
        response = b''

        while utime.ticks_diff(utime.ticks_ms(), start_time) < timeout:
            if uart.any():
                response += uart.read(uart.any())
                if expected_response.encode() in response:
                    return response.decode('utf-8')
            utime.sleep_ms(100)

        return None

    @staticmethod
    def clear_uart_buffer(uart):
        while uart.any():
            uart.read()

    @staticmethod
    def send_command(uart, command, wait_for="OK", timeout=2000):
        SIM800Utils.clear_uart_buffer(uart)
        uart.write(command + '\r')
        return SIM800Utils.wait_for_response(uart, wait_for, timeout)
