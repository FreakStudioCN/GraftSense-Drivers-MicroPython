from machine import I2C, Pin, reset
from time import sleep_ms
import uctypes

bus =  I2C(scl=Pin(5), sda=Pin(2), freq=100000)


def send_raw_data(chipid, buf):

    chip_addr = 0x74 + chipid

    try:
        bus.writeto(chip_addr, buf)
    except:
        print ('Erorr durring write on I2C bus...')


def get_raw_data(chipid, buf):

    send_raw_data(chipid,buf)

    sleep_ms(10)

    chip_addr = 0x74 + chipid

    buf = bytearray(b'\x00' * 35)
    try:
        bus.readfrom_into(chip_addr, buf)
        #from ubinascii import hexlify
        #print ('\nMCP39F521 returns following data:')
        #print (hexlify(buf, b":"))
    except:
        print ('Erorr durring read on I2C bus...')

    return (buf)


def control_energy_acc(chipid, state):
    if (state):
        # Write 0x01 at 0x0002 address 0x00DC (data sheet page29)
        buf = bytearray([0xA5, 0x0A, 0x41, 0x00, 0xDC, 0x4D, 0x02, 0x00, 0x01, 0x1C])
    else:
        # Write 0x00 at 0x0002 address 0x00DC (data sheet page29)
        buf = bytearray([0xA5, 0x0A, 0x41, 0x00, 0xDC, 0x4D, 0x02, 0x00, 0x00, 0x1B])

    send_raw_data(chipid,buf)


def get_data(chipid):

    # Read 32 bytes starting at 0x0002 address
    buf = bytearray([0xA5, 0x08, 0x41, 0x00, 0x02, 0x4E, 0x20, 0x5E])

    buf = get_raw_data(chipid,buf)

    desc = {
    "SysStatus":    uctypes.UINT16 | 2,
    "SysVer":       uctypes.UINT16 | 4,
    "Voltage":      uctypes.UINT16 | 6,
    "Frequency":    uctypes.UINT16 | 8,
    "PwrFactor":    uctypes.INT16  | 12,
    "Current":      uctypes.UINT32 | 14,
    "ActivePwr":    uctypes.UINT32 | 18,
    "ReactvPwr":    uctypes.UINT32 | 22,
    "ApprntPwr":    uctypes.UINT32 | 26,
    }

    values = uctypes.struct(uctypes.addressof(buf), desc, uctypes.LITTLE_ENDIAN)

    SysVer    = values.SysVer
    SysStatus = values.SysStatus
    Voltage   = (values.Voltage)   / 10.0
    Current   = (values.Current)   / 10000.0
    Frequency = (values.Frequency) / 1000.0
    ActivePwr = (values.ActivePwr) / 100.0
    ReactvPwr = (values.ReactvPwr) / 100.0 
    ApprntPwr = (values.ApprntPwr) / 100.0
    PwrFactor = (values.PwrFactor) * 0.000030517578125

    # Read 32 bytes starting at 0x001E address
    buf = bytearray([0xA5, 0x08, 0x41, 0x00, 0x1E, 0x4E, 0x20, 0x7A])

    buf = get_raw_data(chipid,buf)

    desc = {
    "ImportActEnergy":   uctypes.UINT64 | 2,
    "ExportActEnergy":   uctypes.UINT64 | 10,
    "ImportReactEnergy": uctypes.UINT64 | 18,
    "ExportReactEnergy": uctypes.UINT64 | 26,
    }

    values = uctypes.struct(uctypes.addressof(buf), desc, uctypes.LITTLE_ENDIAN)

    ImportActEnergy   = values.ImportActEnergy   / 1000000.0
    ExportActEnergy   = values.ExportActEnergy   / 1000000.0
    ImportReactEnergy = values.ImportReactEnergy / 1000000.0
    ExportReactEnergy = values.ExportReactEnergy / 1000000.0
    
    return [SysVer,    \
            SysStatus, \
            Voltage,   \
            Current,   \
            Frequency, \
            ActivePwr, \
            ReactvPwr, \
            ApprntPwr, \
            PwrFactor, \
            ImportActEnergy,  \
            ExportActEnergy,  \
            ImportReactEnergy,\
            ExportReactEnergy]

