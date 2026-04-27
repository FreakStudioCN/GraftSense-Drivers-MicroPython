"""
在本地生成一个 64x64 PNG 图标，不依赖 Pillow，纯手写 PNG 字节流。
画一个绿底白色 "H" 字母图标。
"""
import struct, zlib

W, H = 64, 64

def make_png(width, height, pixels):
    """pixels: list of (R,G,B) tuples, row-major"""
    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(name + data) & 0xFFFFFFFF)

    raw = b''
    for y in range(height):
        row = b'\x00'  # filter type None
        for x in range(width):
            r, g, b = pixels[y * width + x]
            row += bytes([r, g, b])
        raw += row

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw, 9)

    png  = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', idat)
    png += chunk(b'IEND', b'')
    return png

# --- 生成像素 ---
BG   = (34, 139, 34)   # 森林绿
FG   = (255, 255, 255) # 白色

pixels = [BG] * (W * H)

# 画字母 "H"（粗体，居中）
def fill_rect(px, x0, y0, x1, y1, color):
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[y * W + x] = color

# 左竖
fill_rect(pixels, 16, 14, 26, 50, FG)
# 右竖
fill_rect(pixels, 38, 14, 48, 50, FG)
# 横梁
fill_rect(pixels, 16, 27, 48, 37, FG)

png_bytes = make_png(W, H, pixels)

with open('icon_64x64.png', 'wb') as f:
    f.write(png_bytes)

print(f'Generated icon_64x64.png ({len(png_bytes)} bytes)')
