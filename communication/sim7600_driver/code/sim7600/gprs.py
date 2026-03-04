class GPRS:
    def __init__(self, sim7600):
        self.sim7600 = sim7600

    def set_apn(self, apn, user='', password=''):
        self.sim7600.send_command(f'AT+CGDCONT=1,"IP","{apn}"')
        if user and password:
            self.sim7600.send_command(f'AT+CGAUTH=1,1,"{user}","{password}"')

    def enable_gprs(self):
        self.sim7600.send_command('AT+CGATT=1')
        self.sim7600.send_command('AT+CGACT=1,1')

    def disable_gprs(self):
        self.sim7600.send_command('AT+CGACT=0,1')
        self.sim7600.send_command('AT+CGATT=0')

    def get_ip_address(self):
        return self.sim7600.send_command('AT+CIFSR')

    def send_data(self, data):
        self.sim7600.write_uart(data)

    def receive_data(self):
        return self.sim7600.read_uart()
