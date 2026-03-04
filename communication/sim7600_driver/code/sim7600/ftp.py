class FTP:
    def __init__(self, sim7600):
        self.sim7600 = sim7600

    def set_ftp_parameters(self, server, port=21, user='', password=''):
        self.sim7600.send_command(f'AT+FTPCID=1')
        self.sim7600.send_command(f'AT+FTPSERV="{server}"')
        self.sim7600.send_command(f'AT+FTPPORT={port}')
        self.sim7600.send_command(f'AT+FTPUN="{user}"')
        self.sim7600.send_command(f'AT+FTPPW="{password}"')

    def upload_file(self, local_path, remote_path):
        self.sim7600.send_command(f'AT+FTPPUTNAME="{remote_path}"')
        self.sim7600.send_command(f'AT+FTPPUTPATH="/"')
        self.sim7600.send_command('AT+FTPPUT=1')
        with open(local_path, 'rb') as file:
            for chunk in iter(lambda: file.read(512), b''):
                self.sim7600.write_uart(chunk)
        return self.sim7600.read_uart()

    def download_file(self, remote_path, local_path):
        self.sim7600.send_command(f'AT+FTPGETNAME="{remote_path}"')
        self.sim7600.send_command(f'AT+FTPGETPATH="/"')
        self.sim7600.send_command('AT+FTPGET=1')
        data = self.sim7600.read_uart()
        with open(local_path, 'wb') as file:
            file.write(data)
        return data

    def delete_file(self, remote_path):
        self.sim7600.send_command(f'AT+FTPDELE="{remote_path}"')
        return self.sim7600.read_uart()

    def list_files(self, remote_path):
        self.sim7600.send_command(f'AT+FTPLIST="{remote_path}"')
        return self.sim7600.read_uart()
