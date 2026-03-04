class HTTP:
    def __init__(self, sim7600):
        self.sim7600 = sim7600

    def set_apn(self, apn, user='', password=''):
        self.sim7600.send_command(f'AT+SAPBR=3,1,"APN","{apn}"')
        if user and password:
            self.sim7600.send_command(f'AT+SAPBR=3,1,"USER","{user}"')
            self.sim7600.send_command(f'AT+SAPBR=3,1,"PWD","{password}"')

    def enable_http(self):
        self.sim7600.send_command('AT+SAPBR=1,1')
        self.sim7600.send_command('AT+SAPBR=2,1')
        self.sim7600.send_command('AT+HTTPINIT')

    def disable_http(self):
        self.sim7600.send_command('AT+HTTPTERM')
        self.sim7600.send_command('AT+SAPBR=0,1')

    def set_url(self, url):
        self.sim7600.send_command(f'AT+HTTPPARA="URL","{url}"')

    def set_content(self, content_type):
        self.sim7600.send_command(f'AT+HTTPPARA="CONTENT","{content_type}"')

    def get(self):
        self.sim7600.send_command('AT+HTTPACTION=0')
        return self.sim7600.read_uart()

    def post(self, data):
        self.sim7600.send_command(f'AT+HTTPDATA={len(data)},10000')
        self.sim7600.write_uart(data)
        self.sim7600.send_command('AT+HTTPACTION=1')
        return self.sim7600.read_uart()

    def read_response(self):
        return self.sim7600.send_command('AT+HTTPREAD')
