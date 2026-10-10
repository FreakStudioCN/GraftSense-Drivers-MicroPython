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

  v4.1 09/01/2017
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
<title>3-Phase Power</title>
<style>table {width:500px;}
table, th, td {border: 1px solid grey; border-collapse: collapse;}
th, td {padding: 5px; text-align: left;}
table#t01 tr:nth-child(even) { background-color: #eee;}
table#t01 tr:nth-child(odd) {background-color: #fff;}
table#t01 th {background-color: #99e; color: white;}
</style>
</head>
<body><h1>3-Phase Power and Energy</h1>
<table id="t01"><tr><th>Parameter</th><th>R Line</th><th>S Line</th><th>T Line</th></tr>%s</table>
Ver:4.1, Free Mem: %s bytes
</body>
</html>"""

null_page = """%s"""
json_page = """{
"power-and-energy":{
"R_Line":{
%s
"Name":"R"
},
"S_Line":{
%s
"Name":"S"
},
"T_Line":{
%s
"Name":"T"
},
"Resources":{
"Free Mem":%s    
}
}
}"""

MCP39F521.control_energy_acc(0, True)
MCP39F521.control_energy_acc(1, True)
MCP39F521.control_energy_acc(2, True)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

print('\n-- MCP39F521 3-phase read agent v4.1 (10/01/2017)\n-- (c)Piotr Oniszczuk\n')

mem_info()

print('\n-- Now Listening on port 80...\n')

try:
    while True: 
        conn, addr = s.accept()
        print("Got request from %s" % str(addr)) 

        request = conn.recv(1024) 
        request = str(request)

        data_R = MCP39F521.get_data(0)
        data_S = MCP39F521.get_data(1)
        data_T = MCP39F521.get_data(2)

        vals = [['Voltage'               ,data_R[2], data_S[2], data_T[2],  'V'   ], \
                ['Current'               ,data_R[3], data_S[3], data_T[3],  'A'   ], \
                ['Frequency'             ,data_R[4], data_S[4], data_T[4],  'Hz'  ], \
                ['Active Pwr'            ,data_R[5], data_S[5], data_T[5],  'W'   ], \
                ['Reactive Pwr'          ,data_R[6], data_S[6], data_T[6],  'W'   ], \
                ['Apparent Pwr'          ,data_R[7], data_S[7], data_T[7],  'W'   ], \
                ['Power Factor'          ,data_R[8], data_S[8], data_T[8],  ' '   ], \
                ['Import Active Eng'     ,data_R[9], data_S[9], data_T[9],  'kWh' ], \
                ['Export Active Eng'     ,data_R[10],data_S[10],data_T[10], 'kWh' ], \
                ['Import Reactive Eng'   ,data_R[11],data_S[11],data_T[11], 'kWh' ], \
                ['Export Reactive Eng'   ,data_R[12],data_S[12],data_T[12], 'kWh' ]]

        json      = request.find('/json')
        reboot    = request.find('/reboot')
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
            html = json_page
            rows_R = ['"%s":%.3f,' % (p[0], p[1]) for p in vals]
            rows_S = ['"%s":%.3f,' % (p[0], p[2]) for p in vals]
            rows_T = ['"%s":%.3f,' % (p[0], p[3]) for p in vals]
            response = html % ('\n'.join(rows_R), '\n'.join(rows_S), '\n'.join(rows_T), str(gc.mem_free())) 

        elif eng_acc_on == 6:
            MCP39F521.control_energy_acc(0, True)
            MCP39F521.control_energy_acc(1, True)
            MCP39F521.control_energy_acc(2, True)
            html = null_page
            response = html % '\n\nEnergy Acc. ON...\n\n'

        elif eng_acc_off == 6:
            MCP39F521.control_energy_acc(0, False)
            MCP39F521.control_energy_acc(1, False)
            MCP39F521.control_energy_acc(2, False)
            html = null_page
            response = html % '\n\nEnergy Acc. OFF...\n\n'

        else:
            rows = ['<tr><td>%s</td><td><b>%.3f %s</b></td><td><b>%.3f %s</b></td><td><b>%.3f %s</b></td></tr>' % (p[0], p[1], p[4], p[2], p[4], p[3], p[4]) for p in vals]
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

