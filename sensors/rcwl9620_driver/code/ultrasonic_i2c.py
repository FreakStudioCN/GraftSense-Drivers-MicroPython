import time

class UltrasonicI2C:
    MAX_DISTANCE = 4500

    def __init__(self, i2c, address: int = 0x57):
        self.i2c = i2c
        self.address = address

    def read(self):
        self.i2c.writeto(0x57, b'\x01')
        time.sleep_ms(120)
        raw_data = self.i2c.readfrom(0x57, 3)
        raw_mm = ((raw_data[0] << 16) + (raw_data[1] << 8) + raw_data[2]) / 1000
        return min(raw_mm, self.MAX_DISTANCE)
