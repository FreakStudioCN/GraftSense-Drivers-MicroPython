"""
This is ESP8266 micropython script designed to serve ESP8266 as web server showing readings from Microchip MCP39F521. 
Script was developed and tested on esp8266-20161110-v1.8.6.bin micropython.

Script listens on port 80 and implements following commands:

  'http://<esp8266_ip>'               - shows web page with MCP39F521 readings
  'http://<esp8266_ip>/json'          - sends json formated MCP39F521 readings
  'http://<esp8266_ip>/eng_acc=on'    - turns ON energy accumulation
  'http://<esp8266_ip>/eng_acc=off'   - turns OFF energy accumulation (and reset accumulated energy counters)
  'http://<esp8266_ip>/reboot'        - reboots ESP8266

  To setup ESP8266 with micropython pls look on various tutorials. There is plenty of them on Internet

  v2.0 9/01/2017
  (c) Piotr Oniszczuk
"""

from time import sleep_ms
import socket
from micropython import mem_info
from machine import reset
import MCP39F521

html_page = """<!DOCTYPE html>
<html>
<head>
<title>1-Phase Power</title>
<style>table {width:300px;}
table, th, td {border: 1px solid grey; border-collapse: collapse;}
th, td {padding: 5px; text-align: left;}
table#t01 tr:nth-child(even) { background-color: #eee;}
table#t01 tr:nth-child(odd) {background-color: #fff;}
table#t01 th {background-color: #99e; color: white;}
</style>
</head>
<body><h1>1-Phase Power and Energy</h1>
<table id="t01"><tr><th>Parameter</th><th>Line</th></tr>%s</table>
Ver:2.0, Free Mem: %s bytes
</body>
</html>"""

null_page = """%s"""
json_page = """{
"power-and-energy":{
"Line":{
%s
"Name":"Line"
},
"Resources":{
"Free Mem":%s    
}
}
}"""

MCP39F521.control_energy_acc(0, True)  

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print('\n-- MCP39F521 read agent v2.0 (10/01/2017)\n-- (c)Piotr Oniszczuk\n')

mem_info()

print('\n-- Now Listening on port 80...\n')

try:
    while True: 
        conn, addr = s.accept()
        print("Got request from %s" % str(addr)) 

        request = conn.recv(1024) 
        request = str(request)

        data = MCP39F521.get_data(0)
        vals = [['Voltage'             ,data[2],  'V'   ], \
                ['Current'             ,data[3],  'A'   ], \
                ['Frequency'           ,data[4],  'Hz'  ], \
                ['Active Pwr'          ,data[5],  'W'   ], \
                ['Reactive Pwr'        ,data[6],  'W'   ], \
                ['Apparent Pwr'        ,data[7],  'W'   ], \
                ['Power Factor'        ,data[8],  ' '   ], \
                ['Import Active Eng'   ,data[9],  'kWh' ], \
                ['Export Active Eng'   ,data[10], 'kWh' ], \
                ['Import Reactive Eng' ,data[11], 'kWh' ], \
                ['Export Reactive Eng' ,data[12], 'kWh' ]]

        json        = request.find('/json')
        reboot      = request.find('/reboot')
        eng_acc_on  = request.find('/eng_acc=on')
        eng_acc_off = request.find('/eng_acc=off')

        if reboot == 6:
            html = null_page
            response = html % '\n\nRebooting...\n\n'
            conn.send(response)
            conn.close()
            sleep_ms(3000)
            reset()
 
        elif json == 6:
            rows = ['"%s":%.3f,' % (p[0], p[1]) for p in vals]
            html = json_page
            response = html % ('\n'.join(rows), str(gc.mem_free()))

        elif eng_acc_on == 6:
            MCP39F521.control_energy_acc(0, True)
            html = null_page
            response = html % '\n\nTurning ON Energy Accumulation...\n\n'

        elif eng_acc_off == 6:
            MCP39F521.control_energy_acc(0, False)
            html = null_page
            response = html % '\n\nTurning OFF Energy Accumulation...\n\n'

        else:
            rows = ['<tr><td>%s</td><td><b>%.3f %s</b></td></tr>' % (p[0], p[1], p[2]) for p in vals]
            html = html_page
            response = html % ('\n'.join(rows), str(gc.mem_free()))
 
        conn.sendall(response)
        conn.close()
        #print('-- Before GC free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))
        gc.collect()
        #print('-- After  GC free: {} allocated: {}'.format(gc.mem_free(), gc.mem_alloc()))

except:
        print ('\n\nException in main server loop. Rebooting...\n\n')
        sleep_ms(5000)
        reset()
