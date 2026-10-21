try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

class LCDAsync:
    def __init__(self, i2c, address=62):
        self.i2c=i2c; self.address=address; self.column=0; self.row=0; self._lock=asyncio.Lock()
    async def start(self):
        await asyncio.sleep_ms(50)
        for _ in range(3):
            await self._command(0x28); await asyncio.sleep_ms(10)
        await self.on_async(); await self.clear_async(); await self._command(0x06); await self.set_cursor_async(0,0)
    async def _command(self, value):
        self.i2c.writeto(self.address, bytes((0x80,value))); await asyncio.sleep_ms(1)
    async def on_async(self,cursor=False,blink=False):
        async with self._lock: await self._command(0x0c|(2 if cursor else 0)|(1 if blink else 0))
    async def off_async(self):
        async with self._lock: await self._command(0x08)
    async def clear_async(self):
        async with self._lock: await self._command(1); self.column=0; self.row=0; await self._cursor(0,0)
    async def _cursor(self,c,r):
        if not 0<=c<16 or not 0<=r<2: raise ValueError('cursor outside LCD1602 bounds')
        self.column=c; self.row=r; await self._command((0x80 if r==0 else 0xc0)|c)
    async def set_cursor_async(self,c,r):
        async with self._lock: await self._cursor(c,r)
    async def write_async(self,text):
        async with self._lock:
            for char in text:
                await asyncio.sleep_ms(10); self.i2c.writeto(self.address,b'\x40'+char.encode()); self.column+=1
                if self.column>=16: await self._cursor(0,(self.row+1)%2)

    async def aclose(self):
        await self.off_async()
