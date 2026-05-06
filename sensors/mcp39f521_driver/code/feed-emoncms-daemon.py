#! /usr/bin/python


sensors = {
    "ServerRoom" :["192.168.1.101","1phase"],
    "MainPower"  :["192.168.1.100","3phase"],
    "Lights"     :["192.168.1.102","1phase"],
}
#    "MainPower"  :["192.168.1.178","3phase"],

emoncms_server_ip   = "192.168.1.254"
emoncms_api_key     = "712e90ebae780d638d89ad1a37f1a3ab"
feed_period         = 30
timeout_read_sensor = 10
debug               = 0

#-------------------------------------------------------------------------------















emoncms_url = 'http://' + emoncms_server_ip + '/emoncms/input/post.json?apikey=' + emoncms_api_key + '&node='
prev_message = ""
dup_cnt = 0

import urllib2, json, time


def log(message):
    repeat_limit = 120
    global prev_message
    global dup_cnt
    global timestamp

    if (message == prev_message):
        dup_cnt = dup_cnt + 1
        now = time.time()
        localtime = time.localtime(now)
        milliseconds = '%03d' % int((now - int(now)) * 1000)
        timestamp = time.strftime('%d/%m/%Y %H:%M:%S', localtime) + "." + milliseconds
        if (dup_cnt >= repeat_limit):
            message = "(lastly repeated " + str(repeat_limit) + " times):" + message
            print timestamp + " " + message
            dup_cnt = 0
        else:
            return
    else:
        if (dup_cnt > 0):
            prev_message = "(lastly repeated " + str(dup_cnt) + " times):" + prev_message
            print timestamp + " " + prev_message
            dup_cnt = 0

        now = time.time()
        localtime = time.localtime(now)
        milliseconds = '%03d' % int((now - int(now)) * 1000)
        timestamp = time.strftime('%d/%m/%Y %H:%M:%S', localtime) + "." + milliseconds
        print timestamp + " " + message
        prev_message = message


def log1(message):
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    timestamp = time.strftime('%d/%m/%Y %H:%M:%S', localtime) + "." + milliseconds
    print timestamp + " " + message


def get_decode_json_from_url(url):
    req = urllib2.Request(url + "/json")

    try:
        response = urllib2.urlopen(req, timeout=timeout_read_sensor)
        raw_data = response.read()
        if (debug): print(raw_data)
    except:
        log('ERROR: Can\'t get data from: ' + url + "  Retrying after 5sec...")
        time.sleep(5)
        try:
            response = urllib2.urlopen(req, timeout=timeout_read_sensor)
            raw_data = response.read()
            if (debug): print(raw_data)
        except:
            log('ERROR: 2nd time can\'t get data from: ' + url)
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

    req = urllib2.Request(emoncms_url)

    try:
        response = urllib2.urlopen(req, timeout=5)
        rc = response.read()
        if (debug): print(rc)
        return True
    except:
        log("ERROR: Sending to emoncms fialed.\nURL was:" + emoncms_url)
        return False


log("Emoncms feed daemon v1.0 (c) Piotr Oniszczuk")
log("feed period: " + str(feed_period) + "sec.\n")

while True:

    error = False

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
                rc = send_to_emoncms_node(node, values, emoncms_url)
                if not (rc): error = True

                line = "S_Line"
                node = name + "-S-Line"
                if (debug): print("--Feeding " + node)
                values = read_values_from_json(data, line)
                rc = send_to_emoncms_node(node, values, emoncms_url)
                if not (rc): error = True

                line = "T_Line"
                node = name + "-T-Line"
                if (debug): print("--Feeding " + node)
                values = read_values_from_json(data, line)
                rc = send_to_emoncms_node(node, values, emoncms_url)
                if not (rc): error = True
            else:
                error = True

        elif (sensor_type == "1phase"):

            url = "http://" + ip
            data = get_decode_json_from_url(url)

            if (data):
                line = "Line"
                node = name
                if (debug): print("--Feeding " + node)
                values = read_values_from_json(data, line)
                rc = send_to_emoncms_node(node, values, emoncms_url)
                if not (rc): error = True
            else:
                error = True

        else:
            print "ERROR: Unknown sensor type!"

    if not (error): log("Feed was successfull...")
    time.sleep(feed_period)
