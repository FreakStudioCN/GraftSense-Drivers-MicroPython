# from machine import I2C

class MMA7660_DATA:
    def __init__(self):
        self.X = None
        self.Y = None
        self.Z = None
        self.TILT = None
        self.SRST = None
        self.SPCNT = None
        self.INTSU = None
        self.MODE = None
        self.SR = None
        self.PDET = None
        self.PD = None

# class MMA7660_ACC_DATA:
#     def __init__(self,x,y,z):
#         self.x = x
#         self.y = y
#         self.z = z

class MMA7660_LOOKUP(object):
    def __init__(self):
        self.g = None
        self.xyAngle = None
        self.zAngle = None

class Accelerometer(object):
    MMA7660_ADDR = 0x4c
    MMA7660TIMEOUT = 500

    MMA7660_X = 0x00
    MMA7660_Y = 0x01
    MMA7660_Z = 0x02
    MMA7660_TILT = 0x03
    MMA7660_SRST = 0x04
    MMA7660_SPCNT = 0x05
    MMA7660_INTSU = 0x06
    MMA7660_SHINTX = 0x80
    MMA7660_SHINTY = 0x40
    MMA7660_SHINTZ = 0x20
    MMA7660_GINT = 0x10
    MMA7660_ASINT = 0x08
    MMA7660_PDINT = 0x04
    MMA7660_PLINT = 0x02
    MMA7660_FBINT = 0x01
    MMA7660_MODE = 0x07
    MMA7660_STAND_BY = 0x00
    MMA7660_ACTIVE = 0x01
    MMA7660_SR = 0x08      # sample rate register
    AUTO_SLEEP_120 = 0X00     # 120 sample per second
    AUTO_SLEEP_64 = 0X01
    AUTO_SLEEP_32 = 0X02
    AUTO_SLEEP_16 = 0X03
    AUTO_SLEEP_8  = 0X04
    AUTO_SLEEP_4  = 0X05
    AUTO_SLEEP_2  = 0X06
    AUTO_SLEEP_1  = 0X07
    MMA7660_PDET = 0x09
    MMA7660_PD = 0x0A

    accLookup = []

    for i in range(64):
        s = MMA7660_LOOKUP()
        accLookup.insert(i,s)

    def __init__(self, i2c, address, interrupts=False):

        self.i2c = i2c
        self.address = address

        i2c.init(I2C.MASTER, baudrate=20000)

        initAccelTable()
        setMode(MMA7660_STAND_BY)
        setSampleRate(AUTO_SLEEP_32)

        if interrupts:
            write(MMA7660_INTSU, interrupts)

        setMode(MMA7660_ACTIVE)

    def write(self, register, data):
        register = bytearray([register])
        data = bytearray([data])

        self.i2c.writeto_mem(self.address, register, data)

    def read(self, register):
        register = bytearray([register])
        data = bytearray([data])
        buf = ''

        i2c.readfrom_mem_into(self.address,register,buf)

        return buf

    def initAccelTable(self):

        val = 0

        for i in range(32):
            accLookup[i].g = val
            val += 0.047

        val = -0.047

        for i in range(63,31,-1):
            accLookup[i].g = val
            val -= 0.047

        val = 0
        valZ = 90

        for i in range(22):
            accLookup[i].xyAngle = val
            accLookup[i].zAngle = valZ

            val -= 2.69
            valZ += 2.69

        val = -2.69
        valZ = -87.31

        for i in range(63, 42,-1):
            accLookup[i].xyAngle = val
            accLookup[i].zAngle = valZ

            val -= 2.69
            valZ += 2.69

        for i in range(22,43):
            accLookup[i].xyAngle = 255
            accLookup[i].zAngle = 255


    def setMode(self, mode):
        write(MMA7660_MODE,mode)

    def setSampleRate(self):
        write(MMA7660_SR,rate)

    def getXYZ(self, x, y, z):

		count = 0
		val = [64,64,64]

        i2c.readfrom(self.address,1)
        i2c.readfrom(self.address,3)





        return data = (x,y,z)

    def getAcceleration(self):
        return True
        return False

    def getAllData(self):
        count = 0



        return True
        return False
