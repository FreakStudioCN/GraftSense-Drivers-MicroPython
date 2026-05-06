#! /usr/bin/python

# Simple script for pooling set of power MCP39F5xx meters and feeding reading to EMONCMS server.

# List of sensors with MCP39F521 and their type. Allowed types are: "1phase" and "3pahase"
sensors = {
    "MainPower"  :["192.168.1.178","3phase"],
    "ServerRoom" :["192.168.1.174","1phase"],
    "Lights"     :["192.168.1.175","1phase"],
}

# IP address of EMONCMS server
emoncms_server_ip = "192.168.1.254"

# API key for EMONCMS server
emoncms_api_key   = "712e90ebae780d638d89ad1axxxxxxx"

debug = 0

#-------------------------------------------------------------------------------















emoncms_url = 'http://' + emoncms_server_ip + '/emoncms/input/post.json?apikey=' + emoncms_api_key + '&node='

import urllib, json, time

def log(str):
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    timestamp = time.strftime('%H:%M:%S', localtime) + "." + milliseconds
    print timestamp + " " + str


def get_decode_json_from_url(url):
    try:
        response = urllib.urlopen(url + "/json")
        raw_data = response.read()
        if (debug): print(raw_data)
    except:
        log('ERROR: Can\'t get data from: ' + url)
        return False

    try:
        data = json.loads(raw_data)
        if (debug): print(data)
        return data
    except:
        log( 'ERROR: Can\'t decode data from: ' + url)
        print(raw_data)
        return False


def read_values_from_json(data, line):
    Voltage                = data['power-and-energy'][line]['Voltage']
    Current                = data['power-and-energy'][line]['Current']
    Frequency              = data['power-and-energy'][line]['Frequency']
    Active_Power           = data['power-and-energy'][line]['Active Pwr']
    Reactive_Power         = data['power-and-energy'][line]['Reactive Pwr']
    Apparent_Power         = data['power-and-energy'][line]['Apparent Pwr']
    Power_Factor           = data['power-and-energy'][line]['Power Factor']
    Import_Active_Energy   = data['power-and-energy'][line]['Import Active Eng']
    Export_Active_Energy   = data['power-and-energy'][line]['Export Active Eng']
    Import_Reactive_Energy = data['power-and-energy'][line]['Import Reactive Eng']
    Export_Reactive_Energy = data['power-and-energy'][line]['Export Reactive Eng']
    Free_Memory            = data['power-and-energy']['Resources']['Free Mem']

    if (debug):
        print "Line: " + line
        print "\n  Voltage                : " + str(Voltage)
        print "  Current                : " + str(Current)
        print "  Frequency              : " + str(Frequency)
        print "\n--Power--------"
        print "  Active Power           : " + str(Active_Power)
        print "  Reactive Power         : " + str(Reactive_Power)
        print "  Apparent Power         : " + str(Apparent_Power)
        print "  Power Factor           : " + str(Power_Factor)
        print "\n--Energy-------"
        print "  Import Active Energy   : " + str(Import_Active_Energy)
        print "  Export Active Energy   : " + str(Export_Active_Energy)
        print "  Import Reactive Energy : " + str(Import_Reactive_Energy)
        print "  Export Reactive Energy : " + str(Export_Reactive_Energy)
        print "\n--Resouces-----"
        print "  Free Memory            : " + str(Free_Memory)

    return [ \
            Voltage, \
            Current, \
            Frequency, \
            Active_Power, \
            Reactive_Power, \
            Apparent_Power, \
            Power_Factor, \
            Import_Active_Energy, \
            Export_Active_Energy, \
            Import_Reactive_Energy, \
            Export_Reactive_Energy, \
            Free_Memory \
            ]


def send_to_emoncms_node(node, values, emoncms_url):
    emoncms_url = emoncms_url + node + "&json={"
    emoncms_url = emoncms_url + "Voltage:"                 + str(values[0])
    emoncms_url = emoncms_url + ",Current:"                + str(values[1])
    emoncms_url = emoncms_url + ",Frequency:"              + str(values[2])
    emoncms_url = emoncms_url + ",Active_Power:"           + str(values[3])
    emoncms_url = emoncms_url + ",Reactive_Power:"         + str(values[4])
    emoncms_url = emoncms_url + ",Apparent_Power:"         + str(values[5])
    emoncms_url = emoncms_url + ",Power_Factor:"           + str(values[6])
    emoncms_url = emoncms_url + ",Import_Active_Energy:"   + str(values[7])
    emoncms_url = emoncms_url + ",Export_Active_Energy:"   + str(values[8])
    emoncms_url = emoncms_url + ",Import_Reactive_Energy:" + str(values[9])
    emoncms_url = emoncms_url + ",Export_Ractive_Energy:"  + str(values[10])
    emoncms_url = emoncms_url + ",Free_mamory:"            + str(values[11])
    emoncms_url = emoncms_url + "}"

    if (debug): print "Emocms feed URL:\n" + emoncms_url + "\n"

    try:
        response = urllib.urlopen(emoncms_url)
        rc = response.read()
        if (debug): print(rc)
    except:
        log("ERROR: Sending to emoncms fialed.\nURL was:" + emoncms_url + "\nAnswer was:"+ rc + "\n")



for name in sensors.iterkeys():
    if (debug): print "Sensor:" + name
    params = sensors[name]
    ip = params[0]
    sensor_type = params[1]
    if (debug):
        print "IP:" + ip
        print "Type:" + sensor_type

    if (sensor_type == "3phase"):

        url = "http://" + ip
        data = get_decode_json_from_url(url)

        if (data):
            line = "R_Line"
            node = name + "-R-Line"
            if (debug): print("--Feeding " + node)
            values = read_values_from_json(data, line)
            send_to_emoncms_node(node, values, emoncms_url)

            line = "S_Line"
            node = name + "-S-Line"
            if (debug): print("--Feeding " + node)
            values = read_values_from_json(data, line)
            send_to_emoncms_node(node, values, emoncms_url)

            line = "T_Line"
            node = name + "-T-Line"
            if (debug): print("--Feeding " + node)
            values = read_values_from_json(data, line)
            send_to_emoncms_node(node, values, emoncms_url)

    elif (sensor_type == "1phase"):

        url = "http://" + ip
        data = get_decode_json_from_url(url)

        if (data):
            line = "Line"
            node = name
            if (debug): print("--Feeding " + node)
            values = read_values_from_json(data, line)
            send_to_emoncms_node(node, values, emoncms_url)

    else:
        print "ERROR: Unknown sensor type!"

