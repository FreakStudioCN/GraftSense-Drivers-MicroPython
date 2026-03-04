class Phonebook:
    def __init__(self, sim7600):
        self.sim7600 = sim7600

    def add_contact(self, storage, index, name, number):
        self.sim7600.send_command(f'AT+CPBW={index},"{number}",129,"{name}"')

    def read_contact(self, storage, index):
        return self.sim7600.send_command(f'AT+CPBR={index}')

    def delete_contact(self, storage, index):
        return self.sim7600.send_command(f'AT+CPBW={index}')

    def list_contacts(self, storage):
        return self.sim7600.send_command(f'AT+CPBS="{storage}"')
