from .core import SIM800

class SIM800GPRS(SIM800):
    def attach_gprs(self):
        return self.send_command('AT+CGATT=1')

    def detach_gprs(self):
        return self.send_command('AT+CGATT=0')

    def set_apn(self, apn, user='', pwd=''):
        self.send_command(f'AT+CSTT="{apn}","{user}","{pwd}"')
        return self.send_command('AT+CIICR')

    def get_ip_address(self):
        return self.send_command('AT+CIFSR')

    def start_tcp_connection(self, mode, ip, port):
        return self.send_command(f'AT+CIPSTART="{mode}","{ip}","{port}"')

    def send_data_tcp(self, data):
        self.send_command(f'AT+CIPSEND={len(data)}')
        self.uart.write(data + chr(26))
        return self.read_response()

    def close_tcp_connection(self):
        return self.send_command('AT+CIPCLOSE=1')

    def shutdown_gprs(self):
        return self.send_command('AT+CIPSHUT')

    def get_gsm_location(self):
        response = self.send_command('AT+CIPGSMLOC=1,1')
        return response
