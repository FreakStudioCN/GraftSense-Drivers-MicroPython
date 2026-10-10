try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
class AD9833Async:
    def __init__(self, spi, cs, clk, fmclk=25):
        self._spi, self._cs, self._clk, self._fmclk = spi, cs, clk, fmclk
        self._lock = asyncio.Lock()
        self._state = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self._write_mode = "BOTH"

    def _write(self, values):
        self._clk.value(1); self._cs.value(0)
        self._spi.init(baudrate=1000000)
        self._spi.write(bytearray(values))
        self._cs.value(1)

    async def initialize_async(self):
        """Perform the source constructor's reset write after board assembly."""
        async with self._lock:
            self._control()

    async def write_data_async(self, data):
        if not 0 <= data <= 0xffff:
            raise ValueError("data must be a 16-bit word")
        async with self._lock:
            self._write(((data >> 8) & 0xff, data & 0xff))

    def _control(self):
        value = sum(bit << shift for bit, shift in zip(self._state, (13,12,11,10,8,7,6,5,3,1)))
        self._write(((value >> 8) & 0xff, value & 0xff))

    async def set_frequency_async(self, fout, freqSelect):
        async with self._lock:
            if not 0 <= fout <= 12500000 or freqSelect not in (0, 1): raise ValueError("invalid frequency")
            value = int(fout * (2 ** 28) / self._fmclk)
            address = (1 if freqSelect == 0 else 2) << 14
            words = (value & 0x3fff | address, (value >> 14) & 0x3fff | address)
            if self._write_mode == "LSB": words = words[:1]
            elif self._write_mode == "MSB": words = words[1:]
            frame = []
            for word in words: frame.extend(((word >> 8) & 0xff, word & 0xff))
            self._write(frame)

    async def set_phase_async(self, pout, phaseSelect, rads=True):
        async with self._lock:
            if phaseSelect not in (0, 1): raise ValueError("invalid phase select")
            if not rads: pout = pout * 3.141592653589793 / 180
            word = int(pout * 4096 / (2 * 3.141592653589793)) | 0xc000 | (phaseSelect << 13)
            self._write(((word >> 8) & 0xff, word & 0xff))

    async def set_mode_async(self, mode="SIN"):
        async with self._lock:
            modes = {"SIN":(0,0,0,0),"TRIANGLE":(0,0,0,1),"SQUARE":(0,1,1,0),"SQUARE/2":(0,1,0,0),"RESET":(1,0,0,0),"OFF":(1,1,1,0)}
            if mode not in modes: raise ValueError("invalid mode")
            self._state[4], self._state[6], self._state[7], self._state[9] = modes[mode]
            self._control()

    async def set_control_reg_async(self, B28=1, HLB=0, FS=0, PS=0, RESET=0, SLP1=0, SLP12=0, OP=0, DIV2=0, MODE=0):
        async with self._lock:
            self._state = [B28, HLB, FS, PS, RESET, SLP1, SLP12, OP, DIV2, MODE]
            self._control()

    async def set_write_mode_async(self, writeMode="BOTH"):
        if writeMode not in ("BOTH", "MSB", "LSB"): raise ValueError("invalid write mode")
        async with self._lock:
            self._write_mode = writeMode
            self._state[0], self._state[1] = (1, 0) if writeMode == "BOTH" else (0, 1 if writeMode == "MSB" else 0)
            self._control()

    async def select_freq_phase_async(self, FS, PS):
        async with self._lock:
            if FS not in (0, 1) or PS not in (0, 1): raise ValueError("frequency and phase selections must be 0 or 1")
            self._state[2], self._state[3] = FS, PS
            self._control()

    async def aclose(self):
        self._closed = True
