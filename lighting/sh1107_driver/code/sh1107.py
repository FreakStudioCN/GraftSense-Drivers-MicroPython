

from micropython import const
import time

try:
    import framebuf2 as framebuf
    _fb_variant = 2
except:
    import framebuf
    _fb_variant = 1
print("SH1107: framebuf is ", ("standard" if _fb_variant == 1 else "extended"))


_LOW_COLUMN_ADDRESS = const(0x00)
_HIGH_COLUMN_ADDRESS = const(0x10)
_MEM_ADDRESSING_MODE = const(0x20)

_SET_CONTRAST = const(0x8100)
_SET_SEGMENT_REMAP = const(0xa0)
_SET_MULTIPLEX_RATIO = const(0xA800)

_SET_NORMAL_INVERSE = const(0xa6)
_SET_DISPLAY_OFFSET = const(0xD300)


_SET_DC_DC_CONVERTER_SF = const(0xad81)


_SET_DISPLAY_OFF = const(0xae)
_SET_DISPLAY_ON = const(0xaf)
_SET_PAGE_ADDRESS = const(0xB0)
_SET_SCAN_DIRECTION = const(0xC0)
_SET_DISP_CLK_DIV = const(0xD550)

_SET_DIS_PRECHARGE = const(0xD922)

_SET_VCOM_DSEL_LEVEL = const(0xDB35)

_SET_DISPLAY_START_LINE = const(0xDC00)


class SH1107(framebuf.FrameBuffer):

    def __init__(self, width, height, external_vcc, delay_ms=200, rotate=0):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.delay_ms = delay_ms
        self.flip_flag = False
        self.rotate90 = rotate == 90 or rotate == 270
        self.rotate = rotate
        self.inverse = False
        if self.rotate90:
            self.width, self.height = self.height, self.width
        self.pages = self.height // 8
        self.row_width = self.width // 8
        self.bufsize = self.pages * self.width
        self.displaybuf = bytearray(self.bufsize)
        self.displaybuf_mv = memoryview(self.displaybuf)
        self.pages_to_update = 0
        self._is_awake = False
        if self.rotate90:
            super().__init__(self.displaybuf, self.width, self.height,
                             framebuf.MONO_VLSB)
        else:
            super().__init__(self.displaybuf, self.width, self.height,
                             framebuf.MONO_HMSB)
        self.init_display()

    def init_display(self):
        multiplex_ratio = 0x7F if (self.height == 128) else 0x3F
        self.reset()
        self.poweroff()
        self.fill(0)
        self.write_command(
            (_SET_MULTIPLEX_RATIO | multiplex_ratio).to_bytes(2, "big"))
        self.write_command((_MEM_ADDRESSING_MODE | (
            0x00 if self.rotate90 else 0x01)).to_bytes(1, "big"))
        self.write_command(_SET_PAGE_ADDRESS.to_bytes(1, "big"))
        self.write_command(_SET_DC_DC_CONVERTER_SF.to_bytes(2, "big"))
        self.write_command(_SET_DISP_CLK_DIV.to_bytes(2, "big"))
        self.write_command(_SET_VCOM_DSEL_LEVEL.to_bytes(2, "big"))
        self.write_command(_SET_DIS_PRECHARGE.to_bytes(2, "big"))
        self.contrast(0)
        self.invert(0)

        self.flip(self.flip_flag)
        self.poweron()

    def poweron(self):
        self.write_command(_SET_DISPLAY_ON.to_bytes(1, "big"))
        self._is_awake = True
        time.sleep_ms(self.delay_ms)

    def poweroff(self):
        self.write_command(_SET_DISPLAY_OFF.to_bytes(1, "big"))
        self._is_awake = False

    def sleep(self, value=True):
        if value == True:
            self.poweroff()
        else:
            self.poweron()

    @property
    def is_awake(self) -> bool:
        return self._is_awake

    def flip(self, flag=None, update=True):
        if flag is None:
            flag = not self.flip_flag
        if self.height == 128 and self.width == 128:
            row_offset = 0x00
        elif self.rotate90:
            row_offset = 0x60
        else:
            row_offset = 0x20 if (self.rotate == 180) ^ flag else 0x60
        remap = 0x00 if (self.rotate in (90, 180)) ^ flag else 0x01
        direction = 0x08 if (self.rotate in (180, 270)) ^ flag else 0x00
        self.write_command(
            (_SET_DISPLAY_OFFSET | row_offset).to_bytes(2, "big"))
        self.write_command((_SET_SEGMENT_REMAP | remap).to_bytes(1, "big"))
        self.write_command(
            (_SET_SCAN_DIRECTION | direction).to_bytes(1, "big"))
        self.flip_flag = flag
        if update:
            self.show(True)

    def display_start_line(self, value):
        self.write_command(
            (_SET_DISPLAY_START_LINE | (value & 0x7F)).to_bytes(2, "big"))

    def contrast(self, contrast):
        self.write_command(
            (_SET_CONTRAST | (contrast & 0xFF)).to_bytes(2, "big"))

    def invert(self, invert=None):
        if invert == None:
            invert = not self.inverse
        self.write_command(
            (_SET_NORMAL_INVERSE | (invert & 1)).to_bytes(1, "big"))
        self.inverse = invert

    def show(self, full_update: bool = False):

        (w, p, db_mv) = (self.width, self.pages, self.displaybuf_mv)
        current_page = 1
        if full_update:
            pages_to_update = (1 << p) - 1
        else:
            pages_to_update = self.pages_to_update
        if self.rotate90:
            buffer_3Bytes = bytearray(3)
            buffer_3Bytes[1] = _LOW_COLUMN_ADDRESS
            buffer_3Bytes[2] = _HIGH_COLUMN_ADDRESS
            for page in range(p):
                if pages_to_update & current_page:
                    buffer_3Bytes[0] = _SET_PAGE_ADDRESS | page
                    self.write_command(buffer_3Bytes)
                    page_start = w * page
                    self.write_data(db_mv[page_start: page_start + w])
                current_page <<= 1
        else:
            row_bytes = w // 8
            buffer_2Bytes = bytearray(2)
            for start_row in range(0, p * 8, 8):
                if pages_to_update & current_page:
                    for row in range(start_row, start_row + 8):
                        buffer_2Bytes[0] = row & 0x0f
                        buffer_2Bytes[1] = _HIGH_COLUMN_ADDRESS | (row >> 4)
                        self.write_command(buffer_2Bytes)
                        slice_start = row * row_bytes
                        self.write_data(
                            db_mv[slice_start: slice_start + row_bytes])
                current_page <<= 1
        self.pages_to_update = 0

    def pixel(self, x, y, c=None):
        if c is None:
            return super().pixel(x, y)
        else:
            super().pixel(x, y, c)
            page = y // 8
            self.pages_to_update |= 1 << page

    def text(self, text, x, y, c=1):
        super().text(text, x, y, c)
        self.register_updates(y, y + 7)

    def line(self, x0, y0, x1, y1, c):
        super().line(x0, y0, x1, y1, c)
        self.register_updates(y0, y1)

    def hline(self, x, y, w, c):
        super().hline(x, y, w, c)
        self.register_updates(y)

    def vline(self, x, y, h, c):
        super().vline(x, y, h, c)
        self.register_updates(y, y + h - 1)

    def fill(self, c):
        super().fill(c)
        self.pages_to_update = (1 << self.pages) - 1

    def blit(self, fbuf, x, y, key=-1, palette=None):
        super().blit(fbuf, x, y, key, palette)
        self.register_updates(y, y + self.height)

    def scroll(self, x, y):

        super().scroll(x, y)
        self.pages_to_update = (1 << self.pages) - 1

    def fill_rect(self, x, y, w, h, c):
        try:
            super().fill_rect(x, y, w, h, c)
        except:
            super().rect(x, y, w, h, c, f=True)
        self.register_updates(y, y + h - 1)

    def rect(self, x, y, w, h, c, f=None):
        if f == None or f == False:
            super().rect(x, y, w, h, c)
        else:
            try:
                super().rect(x, y, w, h, c, f)
            except:
                super().fill_rect(x, y, w, h, c)
        self.register_updates(y, y + h - 1)

    def ellipse(self, x, y, xr, yr, c, *args, **kwargs):
        super().ellipse(x, y, xr, yr, c, *args, **kwargs)
        self.register_updates(y - yr, y + yr)

    def poly(self, *args, **kwargs):
        super().poly(*args, **kwargs)
        self.pages_to_update = (1 << self.pages) - 1

    if _fb_variant == 2:
        def large_text(self, s, x, y, m, c=1, r=0, *args, **kwargs):
            try:
                super().large_text(s, x, y, m, c, r, *args, **kwargs)
            except:
                raise Exception("extended framebuffer v206+ required")
            h = (8 * m) * (1 if r is None or r %
                           360 // 90 in (0, 2) else len(s))
            self.register_updates(y, y + h - 1)

        def circle(self, x, y, radius, c, f: bool = None):
            super().circle(x, y, radius, c, f)
            self.register_updates(y-radius, y+radius)

        def triangle(self, x0, y0, x1, y1, x2, y2, c, f: bool = None):
            super().triangle(x0, y0, x1, y1, x2, y2, c, f)
            self.register_updates(min(y0, y1, y2), max(y0, y1, y2))

    def register_updates(self, y0, y1=None):
        y1 = min((y1 if y1 is not None else y0), self.height - 1)

        start_page = y0 // 8
        end_page = (y1 // 8) if (y1 is not None) else start_page

        if start_page > end_page:
            start_page, end_page = end_page, start_page

        if end_page >= 0:
            if start_page < 0:
                start_page = 0
            for page in range(start_page, end_page + 1):
                self.pages_to_update |= 1 << page

    def reset(self, res):
        if res is not None:
            res(1)
            time.sleep_ms(1)
            res(0)
            time.sleep_ms(20)
            res(1)
            time.sleep_ms(20)


class SH1107_I2C(SH1107):
    def __init__(self, width, height, i2c, res=None, address=0x3d,
                 rotate=0, external_vcc=False, delay_ms=200):
        self.i2c = i2c
        self.address = address
        self.res = res
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, delay_ms, rotate)

    def write_command(self, command_list):
        self.i2c.writeto(self.address, b"\x00" + command_list)

    def write_data(self, buf):
        self.i2c.writevto(self.address, (b"\x40", buf))

    def reset(self):
        super().reset(self.res)


class SH1107_SPI(SH1107):
    def __init__(self, width, height, spi, dc, res=None, cs=None,
                 rotate=0, external_vcc=False, delay_ms=0):
        dc.init(dc.OUT, value=0)
        if res is not None:
            res.init(res.OUT, value=0)
        if cs is not None:
            cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        super().__init__(width, height, external_vcc, delay_ms, rotate)

    def write_command(self, cmd):
        if self.cs is not None:
            self.cs(1)
            self.dc(0)
            self.cs(0)
            self.spi.write(cmd)
            self.cs(1)
        else:
            self.dc(0)
            self.spi.write(cmd)

    def write_data(self, buf):
        if self.cs is not None:
            self.cs(1)
            self.dc(1)
            self.cs(0)
            self.spi.write(buf)
            self.cs(1)
        else:
            self.dc(1)
            self.spi.write(buf)

    def reset(self):
        super().reset(self.res)
