from .core import SIM800

class SIM800TCPIP(SIM800):
    def start_tcp_connection(self, mode, ip, port):
        return self.send_command(f'AT+CIPSTART="{mode}","{ip}","{port}"')

    def send_data_tcp(self, data):
        self.send_command(f'AT+CIPSEND={len(data)}')
        self.uart.write(data + chr(26))  
        return self.read_response()

    def receive_data_tcp(self):
        return self.send_command('AT+CIPRXGET=2')

    def close_tcp_connection(self):
        return self.send_command('AT+CIPCLOSE=1')

    def start_udp_connection(self, ip, port):
        return self.send_command(f'AT+CIPSTART="UDP","{ip}","{port}"')

    def send_data_udp(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.send_command(f'AT+CIPSEND={len(data)}')
        self.uart.write(data + bytes([26]))  
        return self.read_response()

    def receive_data_udp(self, max_length=1460):
        return self.send_command(f'AT+CIPRXGET=2,{max_length}')

    def close_udp_connection(self):
        return self.send_command('AT+CIPCLOSE=1')

    def shutdown_gprs(self):
        return self.send_command('AT+CIPSHUT')

    def get_ip_address(self):
        return self.send_command('AT+CIFSR')

    def http_init(self):
        return self.send_command('AT+HTTPINIT')

    def http_set_param(self, param, value):
        return self.send_command(f'AT+HTTPPARA="{param}","{value}"')

    def http_get(self, url):
        self.http_set_param("URL", url)
        self.send_command('AT+HTTPACTION=0')
        return self.read_response()

    def http_post(self, url, data):
        self.http_set_param("URL", url)
        self.send_command(f'AT+HTTPDATA={len(data)},10000')
        self.uart.write(data)
        self.send_command('AT+HTTPACTION=1')
        return self.read_response()

    def http_terminate(self):
        return self.send_command('AT+HTTPTERM')

    def ftp_init(self, server, username, password, port=21):
        self.send_command('AT+SAPBR=3,1,"Contype","GPRS"')
        self.send_command('AT+SAPBR=1,1')
        self.send_command(f'AT+FTPCID=1')
        self.send_command(f'AT+FTPSERV="{server}"')
        self.send_command(f'AT+FTPPORT={port}')
        self.send_command(f'AT+FTPUN="{username}"')
        return self.send_command(f'AT+FTPPW="{password}"')

    def ftp_get_file(self, filename, remote_path):
        self.send_command(f'AT+FTPGETPATH="{remote_path}"')
        self.send_command(f'AT+FTPGETNAME="{filename}"')
        self.send_command('AT+FTPGET=1')
        return self.send_command('AT+FTPGET=2,1024', timeout=10000)

    def ftp_put_file(self, filename, remote_path, data):
        self.send_command(f'AT+FTPPUTPATH="{remote_path}"')
        self.send_command(f'AT+FTPPUTNAME="{filename}"')
        self.send_command('AT+FTPPUT=1')
        self.send_command(f'AT+FTPPUT=2,{len(data)}')
        self.uart.write(data if isinstance(data, bytes) else data.encode('utf-8'))
        return self.read_response()

    def ftp_close(self):
        return self.send_command('AT+SAPBR=0,1')
