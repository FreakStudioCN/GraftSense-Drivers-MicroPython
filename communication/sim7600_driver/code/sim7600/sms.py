class SMS:
    def __init__(self, sim7600):
        self.sim7600 = sim7600

    def send_sms(self, number, message):
        self.sim7600.send_command(f'AT+CMGS="{number}"')
        self.sim7600.write_uart(message + '\x1A')
        return self.sim7600.read_uart()

    def read_sms(self, index):
        return self.sim7600.send_command(f'AT+CMGR={index}')

    def delete_sms(self, index):
        return self.sim7600.send_command(f'AT+CMGD={index}')

    def list_sms(self, status):
        return self.sim7600.send_command(f'AT+CMGL="{status}"')
