
import sys

SI5351_I2C_ADDRESS_DEFAULT        = 0x60

SI5351_CRYSTAL_LOAD_6PF           = 1
SI5351_CRYSTAL_LOAD_8PF           = 2
SI5351_CRYSTAL_LOAD_10PF          = 3

SI5351_CLK_DRIVE_STRENGTH_2MA     = 0
SI5351_CLK_DRIVE_STRENGTH_4MA     = 1
SI5351_CLK_DRIVE_STRENGTH_6MA     = 2
SI5351_CLK_DRIVE_STRENGTH_8MA     = 3

SI5351_DIS_STATE_LOW              = 0
SI5351_DIS_STATE_HIGH             = 1
SI5351_DIS_STATE_HIGH_IMPEDANCE   = 2
SI5351_DIS_STATE_NEVER_DISABLED   = 3


class SI5351_I2C:
    SI5351_MULTISYNTH_RX_MAX       = 7
    SI5351_MULTISYNTH_C_MAX        = 1048575 # fits in [19:0] or 2**20-1

    SI5351_MULTISYNTH_DIV_MIN      = 8       # 4 and 6 only allowed in integer mode
    SI5351_MULTISYNTH_DIV_MAX      = 2048    # DIV_MAX = 128 for quadrature

    SI5351_MULTISYNTH_MUL_MIN      = 15
    SI5351_MULTISYNTH_MUL_MAX      = 90

    # SI5351_REGISTER_PLL_RESET
    SI5351_PLL_RESET_A             = (1<<5)
    SI5351_PLL_RESET_B             = (1<<7)

    # SI5351_REGISTER_CLKn_CONTROL
    SI5351_CLK_POWERDOWN           = (1<<7)
    SI5351_CLK_INPUT_MULTISYNTH_N  = (3<<2)
    SI5351_CLK_INTEGER_MODE        = (1<<6)
    SI5351_CLK_PLL_SELECT_A        = (0<<5)
    SI5351_CLK_PLL_SELECT_B        = (1<<5)
    SI5351_CLK_INVERT              = (1<<4)

    # registers
    SI5351_REGISTER_DEVICE_STATUS = 0
    SI5351_REGISTER_OUTPUT_ENABLE_CONTROL = 3
    SI5351_REGISTER_OEB_ENABLE_CONTROL = 9
    SI5351_REGISTER_CLK0_CONTROL = 16
    SI5351_REGISTER_DIS_STATE_1 = 24
    SI5351_REGISTER_DIS_STATE_2 = 25
    SI5351_REGISTER_PLL_A = 26
    SI5351_REGISTER_PLL_B = 34
    SI5351_REGISTER_MULTISYNTH0_PARAMETERS_1 = 42
    SI5351_REGISTER_MULTISYNTH1_PARAMETERS_1 = 50
    SI5351_REGISTER_MULTISYNTH2_PARAMETERS_1 = 58
    SI5351_REGISTER_CLK0_PHOFF = 165
    SI5351_REGISTER_PLL_RESET = 177
    SI5351_REGISTER_CRYSTAL_LOAD = 183

    def read_bulk(self, register, nbytes):
        buf = bytearray(nbytes)
        if sys.implementation.name == 'circuitpython':
            self.i2c.writeto_then_readfrom(self.address, bytes([register]), buf)
        else:
            self.i2c.readfrom_mem_into(self.address, register, buf)
        return buf

    def write_bulk(self, register, values):
        if sys.implementation.name == 'circuitpython':
            self.i2c.writeto(self.address, bytes([register] + values))
        else:
            self.i2c.writeto_mem(self.address, register, bytes(values))

    def read(self, register):
        return self.read_bulk(register, 1)[0]

    def write(self, register, value):
        self.write_bulk(register, [value])

    def write_config(self, reg, whole, num, denom, rdiv):
        P1 = 128 * whole + int(128.0 * num / denom) - 512
        P2 = 128 * num - denom * int(128.0 * num / denom)
        P3 = denom
        self.write_bulk(reg, [ 
            (P3 & 0x0FF00) >> 8,
            (P3 & 0x000FF),
            (P1 & 0x30000) >> 16 | rdiv << 4,
            (P1 & 0x0FF00) >> 8,
            (P1 & 0x000FF),
            (P3 & 0xF0000) >> 12 | (P2 & 0xF0000) >> 16,
            (P2 & 0x0FF00) >> 8,
            (P2 & 0x000FF) ])

    def set_phase(self, output, div):
        self.write(self.SI5351_REGISTER_CLK0_PHOFF + output, int(div) & 0xFF)

    def reset_pll(self, pll):
        if pll == 0: value = self.SI5351_PLL_RESET_A 
        if pll == 1: value = self.SI5351_PLL_RESET_B
        self.write(self.SI5351_REGISTER_PLL_RESET, value)

    def init_multisynth(self, output, integer_mode):
        pll = self.pll[output]
        value = self.SI5351_CLK_INPUT_MULTISYNTH_N
        value |= self.drive_strength[output]
        if integer_mode:
            value |= SI5351_CLK_INTEGER_MODE
        if self.invert[output] or self.quadrature[output]:
            value |= self.SI5351_CLK_INVERT
        if pll == 0: 
            value |= self.SI5351_CLK_PLL_SELECT_A
        if pll == 1: 
            value |= self.SI5351_CLK_PLL_SELECT_B
        self.write(self.SI5351_REGISTER_CLK0_CONTROL + output, value)

    def approximate_fraction(self, n, d, max_denom):
        # https://github.com/python/cpython/blob/master/Lib/fractions.py
        denom = d
        if denom > max_denom:
            num = n
            p0 = 0; q0 = 1; p1 = 1; q1 = 0
            while denom != 0:
                a = num // denom
                b = num % denom
                q2 = q0 + a * q1
                if q2 > max_denom:
                    break
                p2 = p0 + a * p1
                p0 = p1; q0 = q1; p1 = p2; q1 = q2
                num = denom; denom = b
            n = p1; d = q1
        return n, d

    ###

    def __init__(self, 
            i2c,
            crystal, 
            load=SI5351_CRYSTAL_LOAD_10PF,
            address=SI5351_I2C_ADDRESS_DEFAULT):
        """Instantiate the SI5353_I2C class.  All clock outputs 
        (clkouts) will be shutdown and disabled.
        :param i2c The MicroPython or CircuitPython I2C object.
        :param crystal The crystal frequency in Hz.
        :param load The load capacitance of crystal.  Must use one of 
        the global constants defined in the library for this value.
        :param address The I2C address of the si5351 chip. 
        """
        self.i2c = i2c
        self.crystal = crystal
        self.address = address
        self.vco = {}
        self.pll = {}
        self.quadrature = {}
        self.invert = {}
        self.drive_strength = {}
        self.div = {}
        # wait until chip initializes before writing registers
        while self.read(self.SI5351_REGISTER_DEVICE_STATUS) & 0x80:
            pass
        # disable outputs 
        self.write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, 0xFF)
        # power down all 8 output drivers
        values = [ self.SI5351_CLK_POWERDOWN ] * 8
        self.write_bulk(self.SI5351_REGISTER_CLK0_CONTROL, values)
        # set crystal load value
        self.write(self.SI5351_REGISTER_CRYSTAL_LOAD, load << 6)

    def init_clock(self, 
            output, 
            pll, 
            quadrature=False, 
            invert=False, 
            drive_strength=SI5351_CLK_DRIVE_STRENGTH_8MA):
        """Initialize the given clock output (clkout).
        This method must be called before using set_freq_fixedpll() on 
        the output.  It makes no calls to the Si5351.  It only
        intializes the output clock's state within the library.
        :param output The number of the clock output (clkout) to initialize 
        :param pll The number of the PLL to select. (0=PLLA, 1=PLLB)
        :param invert Invert the output.
        :param quadrature Invert the output and also enable quadrature 
        logic in the library.
        :param drive_strength The drive strength in current to use 
        for the output. Must use one of the global constants defined 
        in the library for this value.
        """
        self.pll[output] = pll
        self.quadrature[output] = quadrature
        self.invert[output] = invert
        self.drive_strength[output] = drive_strength
        self.div[output] = None

    def enable_output(self, output):
        """Enable the given clock output (clkout).
        :param output The clock output (clkout) to enable.
        """
        mask = self.read(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL)
        self.write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, mask & ~(1 << output))

    def disable_output(self, output):
        """Disable the given clock output (clkout).
        :param output The clock output (clkout) to disable.
        """
        mask = self.read(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL)
        self.write(self.SI5351_REGISTER_OUTPUT_ENABLE_CONTROL, mask | (1 << output))

    def setup_pll(self, pll, mul, num=0, denom=1):
        """Set the frequency for the given PLL.
        The PLL frequency is set to the frequency given by 
        (mul + num / denom) times the crystal frequency.
        :param pll The number of the PLL to select. (0=PLLA, 1=PLLB)
        :param mul The whole number to multiply the crystal frequency 
        by.  This value must be in the range [15-90].
        :param num The numerator to multiply the crystal frequency 
        by. This value must be in the range [0-1048574].
        :param denom The denominator to multiply the crystal frequency by.
        This value must be in the range [1-1048575].
        """
        vco = self.crystal * (mul + num / denom)
        if pll == 0: 
            reg = self.SI5351_REGISTER_PLL_A
        if pll == 1: 
            reg = self.SI5351_REGISTER_PLL_B
        self.write_config(reg, whole=mul, num=num, denom=denom, rdiv=0)
        self.vco[pll] = vco

    def setup_multisynth(self, output, div, num=0, denom=1, rdiv=0):
        """Set the multisynth divisor of the PLL frequency.
        :param output The number of the clock output (clkout) to 
        set the frequency for.
        :param div The whole number divisor to set the multisynth to.
        This value must be in the range [4-2047]
        :param num The numerator to divide the pll frequency by. 
        This value must be in the range [0-1048574].
        :param denom The denominator to divide the pll frequency by. 
        This value must be in the range [1-1048575].
        :param rdiv The Rx divisor in log base 2 for additional vco division.
        """
        if type(div) is not int or div < 4:
            raise ValueError('bad multisynth divisor')
        if output == 0: reg = self.SI5351_REGISTER_MULTISYNTH0_PARAMETERS_1
        if output == 1: reg = self.SI5351_REGISTER_MULTISYNTH1_PARAMETERS_1
        if output == 2: reg = self.SI5351_REGISTER_MULTISYNTH2_PARAMETERS_1
        self.write_config(reg, whole=div, num=num, denom=denom, rdiv=rdiv)
        if self.div[output] != div:
            pll = self.pll[output]
            self.set_phase(output, div if self.quadrature[output] else 0)
            self.reset_pll(pll) # only after MS setup, syncs all clocks of pll 
            integer_mode = (num == 0)
            self.init_multisynth(output, integer_mode=integer_mode)
            self.div[output] = div

    def set_freq_fixedpll(self, output, freq):
        """Set the frequency for the clock output (clkout) by changing
        the multisynth divisors.
        Must call init_clock() and setup_pll() before calling this method.
        :param output The number of the clock output (clkout) to 
        set the frequency for.
        :param freq The frequency in Hz to set the clock output (clkout) to.
        """
        pll = self.pll[output]
        vco = self.vco[pll]

        # determine rdiv
        for rdiv in range(self.SI5351_MULTISYNTH_RX_MAX+1): 
            if freq * self.SI5351_MULTISYNTH_DIV_MAX > vco: break
            freq *= 2
        else:
            raise ValueError('maximum Rx divisor exceeded')

        # determine divisor: div + num / denom
        vco = int(10 * vco)
        denom = int(10 * freq)
        num = vco % denom
        div = vco // denom # div = 4,6,[8+0/1048575 to 2047]
        if (div < self.SI5351_MULTISYNTH_DIV_MIN or 
            div >= self.SI5351_MULTISYNTH_DIV_MAX):
            raise ValueError('multisynth divisor out of range')
        max_denom = self.SI5351_MULTISYNTH_C_MAX
        num, denom = self.approximate_fraction(num, denom, max_denom=max_denom)
        self.setup_multisynth(output, div=div, num=num, denom=denom, rdiv=rdiv)

    def set_freq_fixedms(self, output, freq):
        """Set the clock output (clkout) to the requested frequency by 
        changing the pll multiplier value.  Must call init_clock() and
        setup_multisynth() before calling this method.
        :param output The number of the clock output (clkout) to 
        set the frequency for.
        :param freq The frequency in Hz to set the clock output (clkout) to.
        """
        pll = self.pll[output]
        crystal = self.crystal
        vco = freq * div * 2**rdiv

        # determine multiplicand: mul + num / denom
        vco = int(10 * vco)
        denom = int(10 * crystal)
        num = vco % denom
        mul = vco // denom # mul = 15+0/1048575 to 90
        if (mul < self.SI5351_MULTISYNTH_MUL_MIN or 
            mul >= self.SI5351_MULTISYNTH_MUL_MAX):
            raise ValueError('pll multiplier out of range')
        max_denom = self.SI5351_MULTISYNTH_C_MAX
        num, denom = self.approximate_fraction(num, denom, max_denom=max_denom)
        self.setup_pll(pll, mul=mul, num=num, denom=denom)

    ###

    def disabled_states(self, output, state):
        """Set the state of the clock outputs (clkout) when one 
        or more clocks are disabled either in software or 
        as a result of the output enable (OEB) pin going active.
        The possible disabled states for an output are low voltage, high
        voltage, high impedance, and never disabled.
        :param output The clock output (clkout) to set the disabled state for.
        :param state The disabled state to set for the clock 
        output (clkout).  Must use one of the global constants defined in 
        the library for this value.
        """
        if output < 4:
            reg = self.SI5351_REGISTER_DIS_STATE_1
        else:
            reg = self.SI5351_REGISTER_DIS_STATE_2
            output -= 4
        value = self.read(reg)
        s = [ (value >> (n * 2)) & 0x3 for n in range(4) ]
        s[output] = state
        self.write(reg, s[3] << 6 | s[2] << 4 | s[1] << 2 | s[0])

    def disable_oeb(self, mask):
        """Disable the output enable (OEB) pin for the given 
        clock outputs (clkouts).
        :param mask A bit mask of the clock outputs (clkouts) to disable 
        output enable (OEB) pin support for.
        """
        self.write(self.SI5351_REGISTER_OEB_ENABLE_CONTROL, mask & 0xFF)


