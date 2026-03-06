##
# MS5803_I2C
# Library for MS5803 pressure sensor.
##
from utime import sleep_ms
from ucollections import namedtuple

OSR = namedtuple('OSR', ('address', 'sampling_time'))

TEMP_UNITS = ['fahrenheit', 'celcius']
PRESSURE_UNITS = ['pascals', 'bar']

def convert_temperature(temp, units='celcius'):
    '''
    Convert a raw temperature to a chosen unit
    
    Parameters
    ----------
    temp : int
        The raw temperature output from an MS5803 sensor
    units : {default: 'celcius', 'fahrenheit'}
        A string identifying the unit to convert to

    Returns
    ----------
    float
        The converted temperature
    '''
    if units == 'fahrenheit':
        converted_temp = temp / 100
        converted_temp = (((converted_temp) * 9) / 5) + 32
    elif units == 'celcius':
        converted_temp = temp / 100

    return converted_temp


def convert_pressure(pressure, units='pascals'):
    '''
    Convert a raw pressure to a chosen unit
    
    Parameters
    ----------
    pressure : int
        The raw pressure output from an MS5803 sensor
    units : {default: 'pascals', 'bar'}
        A string identifying the unit to convert to

    Returns
    ----------
    float
        The converted pressure
    '''
    if units == 'pascals':
        converted_pressure = pressure / 10
    elif units == 'bar':
        converted_pressure = pressure / 10000
    return converted_pressure


class MS5803():
    '''MS5803-14BA temperature and pressure over i2c.

    This will work for the TE Connectivity MS5803-14BA (14 bar) sensor, whose
    datasheet can be found at https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5803-14BA%7FB3%7Fpdf%7FEnglish%7FENG_DS_MS5803-14BA_B3.pdf%7FCAT-BLPS0013.
    
    This sensor is the basis for the SparkFun breakout board
    (https://www.sparkfun.com/products/12909).
    
    This class allows you to read both the pressure and temperature
    with the get_measurements() function
    
    You can read the temp and pressure at different OverSampling Rates (OSR).
    A higher OSR leads to greater resolution/accuracy but requires a longer
    conversion time. The available OSR rates are available in MS5803.OSRs.
    More info on OSR at https://www.cypress.com/file/236481/download.
    '''
    # Commands
    CMD_RESET    = const(0x1E)
    CMD_PROM     = const(0xA0)
    CMD_ADC_CONV = const(0x40)
    CMD_ADC_READ = const(0x00)

    # Measurements
    PRESSURE    = const(0x00)
    TEMPERATURE = const(0x10)

    # Precision
    OSRs = {
        256: OSR(0x00, 1),
        512: OSR(0x02, 2),
        1024: OSR(0x04, 3),
        2048: OSR(0x06, 5),
        4096: OSR(0x08, 10)
        }

    def __init__(self, i2c, address=0x76, temp_osr=256, pressure_osr=256, temp_units=None, pressure_units=None):
        '''
        Sensor initialisation
        
        Parameters
        ----------
        i2c : machine.I2C
            The I2C object that the sensor is connected to
        address : int
            The I2C address of the sensor
        temp_osr, pressure_osr : {default: 256, 512, 1024, 2048, 4096} *optional
            The oversampling rate (OSR) for the temperature and pressure reading
            If not set the stored OSRs will be used
        temp_units : {default: 'celcius', 'fahrenheit'} *optional
            A string identifying the unit to convert the temperature to
            If not set the stored units will be used
        pressure_units : {default: 'pascals', 'bar'} *optional
            A string identifying the unit to convert the pressure to
            If not set the stored units will be used

        '''
        self.i2c = i2c
        self.address = address
        self._begin()
        self.temp_osr = temp_osr
        self.pressure_osr = pressure_osr
        self.temp_units = temp_units
        self.pressure_units = pressure_units


    def reset(self):
        ''' Sensor reset function '''
        self.i2c.writeto_mem(self.address, self.CMD_RESET, b'')
        utime.sleep(3)


    def _begin(self):
        '''
        Read the factory callibration data from the sensor
        
        Returns # TODO chnge reference to be correct
        ----------
        C[0:5] : list of int
            C1 | Pressure sensitivity | SENS_T1
            C2 | Pressure offset | OFF T1
            C3 | Temperature coefficient of pressure sensitivity | TCS 
            C4 | Temperature coefficient of pressure offset | TCO 
            C5 | Reference temperature | T_REF
            C6 | Temperature coefficient of the temperature | TEMPSENS
        '''
        self.C = []
        for i in range(8):
            buf = self.i2c.readfrom_mem(self.address, self.CMD_PROM + (i * 2), 2)
            self.C.append((buf[0] << 8)|buf[1])


    @property
    def temp_units(self):
        return self._temp_units

    @temp_units.setter
    def temp_units(self, value):
        if value:
            assert value in TEMP_UNITS, 'The temperature unit must be one of {}'.format(TEMP_UNITS)
            self._temp_units = value
        else:
            self._temp_units = None

    @property
    def pressure_units(self):
        return self._temp_units

    @pressure_units.setter
    def pressure_units(self, value):
        if value:
            assert value in PRESSURE_UNITS, 'The pressure unit must be one of {}'.format(PRESSURE_UNITS)
            self._pressure_units = value
        else:
            self._pressure_units = None

    @property
    def temp_osr(self):
        return self._temp_osr

    @temp_osr.setter
    def temp_osr(self, value):
        assert value in self.OSRs.keys(), 'The sampling rate must be in the set {}'.format(self.OSRs.keys())
        self._temp_osr = self.OSRs[value]

    @property
    def pressure_osr(self):
        return self._pressure_osr

    @pressure_osr.setter
    def pressure_osr(self, value):
        assert value in self.OSRs.keys(), 'The sampling rate must be in the set {}'.format(self.OSRs.keys())
        self._pressure_osr = self.OSRs[value]

    def get_measurements(self, temp_osr=None, pressure_osr=None, temp_units=None, pressure_units=None):
        '''
        Collect measurements

        Parameters
        ----------
        temp_osr, pressure_osr : {256, 512, 1024, 2048, 4096} *optional
            The oversampling rate (OSR) for the temperature and pressure reading
            If not set the stored OSRs will be used
        temp_units : {default: 'celcius', 'fahrenheit'} *optional
            A string identifying the unit to convert the temperature to
            If not set the stored units will be used
        pressure_units : {default: 'pascals', 'bar'} *optional
            A string identifying the unit to convert the pressure to
            If not set the stored units will be used

        Returns
        ----------
        tuple of ints
            Returns a tuple containing the raw or converted temp and pressure values
        '''
        if not temp_osr:
            temp_osr = self.temp_osr
        else:
            self.temp_osr = temp_osr

        if not pressure_osr:
            pressure_osr = self.pressure_osr
        else:
            self.pressure_osr = pressure_osr

        if not temp_units:
            temp_units = self.temp_units
        else:
            self.temp_units = temp_units

        if not pressure_units:
            pressure_units = self.pressure_units
        else:
            self.pressure_units = pressure_units

        # Retrieve ADC result
        temp_raw = self._get_ADC_conversion(self.TEMPERATURE, temp_osr) # TODO
        pressure_raw = self._get_ADC_conversion(self.PRESSURE, pressure_osr) # TODO

        # Convert raw temp to actual
        dT = temp_raw - (self.C[5] << 8)
        temp = ((dT * self.C[6]) >> 23) + 2000

        # Calculate the second order temp
        if temp < 2000:
            T2 = 3 * ((dT * dT) >> 33)
            OFF2 = 3 * ((temp - 2000) * (temp - 2000)) >> 1
            SENS2 = 5 * ((temp - 2000) * (temp - 2000)) >> 3

            if temp < -1500:
                OFF2 = OFF2 + 7 * ((temp + 1500) * (temp + 1500))
                SENS2 = SENS2 + (((temp + 1500) * (temp + 1500)) << 2)
        else:
            T2 = 7 * (dT * dT) >> 37
            OFF2 = ((temp - 2000) * (temp - 2000)) >> 4
            SENS2 = 0

        # Bring it all together to apply offsets 
        OFF = (self.C[2] << 16) + (((self.C[4] * dT)) >> 7)
        SENS = (self.C[1] << 15) + (((self.C[3] * dT)) >> 8)

        temp = temp - T2
        OFF = OFF - OFF2
        SENS = SENS - SENS2

        # Calculate the pressure
        pressure = (((SENS * pressure_raw) >> 21 ) - OFF) >> 15

        if temp_units:
            temp = convert_temperature(temp, temp_units)
        if pressure_units:
            pressure = convert_pressure(pressure, pressure_units)

        return (temp, pressure)


    def _get_ADC_conversion(self, measurement, precision=None):
        '''
        Collect measurements
        
        Parameters
        ----------
        measurement: int 
            The address of the desired measurement on the chip
        precision: int 
            The address modifier of the desired precision on the chip

        Returns
        ----------
        int
            Returns a 3 byte int containing the reading from the ADC
        '''

        self.i2c.writeto_mem(self.address, CMD_ADC_CONV + measurement + precision.address, b'');

        # Wait for conversion to complete
        sleep_ms(precision.sampling_time)

        buf = self.i2c.readfrom_mem(self.address, self.CMD_ADC_READ, 3)
        
        result = (buf[0] << 16) + (buf[1] << 8) + buf[2]

        return result
