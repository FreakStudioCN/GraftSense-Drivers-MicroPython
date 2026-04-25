# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import gc
import webrepl
import network

webrepl.start()
gc.collect()

def do_connect():
    import network

    SSID     = '<WiFi networkid'
    PASSWORD = '<WiFi pass>'

    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        print('-- Disablig AP mode...')
        ap_if.active(False)
    if not sta_if.isconnected():
        print('-- Connecting to WiFI network...')
        sta_if.active(True)
        sta_if.connect(SSID, PASSWORD)
        while not sta_if.isconnected():
            pass
    print('-- Network configuration:', sta_if.ifconfig())

do_connect()
