class Calling:
    def __init__(self, sim7600):
        self.sim7600 = sim7600

    def make_call(self, number):
        return self.sim7600.send_command(f'ATD{number};')

    def hang_up(self):
        return self.sim7600.send_command('ATH')

    def answer_call(self):
        return self.sim7600.send_command('ATA')

    def call_status(self):
        return self.sim7600.send_command('AT+CLCC')

    def set_call_volume(self, level):
        return self.sim7600.send_command(f'AT+CLVL={level}')
