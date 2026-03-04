from sim7600.ftp import FTP
from sim7600 import SIM7600
import machine

# Initialize the SIM7600 module
uart = machine.UART(1, baudrate=115200, tx=17, rx=16)
sim7600 = SIM7600(uart)
ftp = FTP(sim7600)

# Set FTP parameters
ftp.set_ftp_parameters('ftp.example.com', user='username', password='password')

# Upload a file
ftp.upload_file('/local/path/file.txt', '/remote/path/file.txt')

# Download a file
ftp.download_file('/remote/path/file.txt', '/local/path/file.txt')

# Delete a file
ftp.delete_file('/remote/path/file.txt')

# List files
files = ftp.list_files('/remote/path/')
print(files)