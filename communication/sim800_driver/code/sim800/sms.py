from .core import SIM800

class SIM800SMS(SIM800):
    def set_sms_format(self, format="1"):
        return self.send_command(f'AT+CMGF={format}')

    def send_sms(self, number, message):
        self.send_command(f'AT+CMGS="{number}"')
        self.uart.write(message + chr(26))  
        return self.read_response()

    def read_sms(self, index=1):
        return self.send_command(f'AT+CMGR={index}')

    def delete_sms(self, index):
        return self.send_command(f'AT+CMGD={index}')

    def read_all_sms(self):
        return self.send_command('AT+CMGL="ALL"')

    def delete_all_sms(self):
        return self.send_command('AT+CMGDA="DEL ALL"')
