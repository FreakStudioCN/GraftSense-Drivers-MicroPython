class TCPIP:
    def __init__(self, sim7600):
        self.sim7600 = sim7600

    def set_apn(self, apn, user='', password=''):
        self.sim7600.send_command(f'AT+CGDCONT=1,"IP","{apn}"')
        if user and password:
            self.sim7600.send_command(f'AT+CGAUTH=1,1,"{user}","{password}"')

    def open_connection(self, protocol, remote_ip, remote_port):
        self.sim7600.send_command('AT+NETOPEN')
        return self.sim7600.send_command(f'AT+CIPOPEN=0,"{protocol}","{remote_ip}",{remote_port}')

    def close_connection(self):
        return self.sim7600.send_command('AT+CIPCLOSE=0')

    def send_data(self, data):
        self.sim7600.send_command(f'AT+CIPSEND=0,{len(data)}')
        self.sim7600.write_uart(data)
        return self.sim7600.read_uart()

    def receive_data(self):
        return self.sim7600.send_command('AT+CIPRXGET=2,0')
