try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from buzzer_async import BuzzerAsync

MELODY = [
    ("C4", 400), ("C4", 400), ("G4", 400), ("G4", 400),
    ("A4", 400), ("A4", 400), ("G4", 800), ("F4", 400),
    ("F4", 400), ("E4", 400), ("E4", 400), ("D4", 400),
    ("D4", 400), ("C4", 800), ("G4", 400), ("G4", 400),
    ("F4", 400), ("F4", 400), ("E4", 400), ("E4", 400),
    ("D4", 800), ("G4", 400), ("G4", 400), ("F4", 400),
    ("F4", 400), ("E4", 400), ("E4", 400), ("D4", 800),
    ("C4", 400), ("C4", 400), ("G4", 400), ("G4", 400),
    ("A4", 400), ("A4", 400), ("G4", 800), ("F4", 400),
    ("F4", 400), ("E4", 400), ("E4", 400), ("D4", 400),
    ("D4", 400), ("C4", 800),
]


async def main():
    buzzer = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio : Use PWM to drive a buzzer to play MIDI music")
        buzzer = BuzzerAsync(pin=6)
        while True:
            await buzzer.play_melody_async(MELODY)
    finally:
        if buzzer is not None:
            await buzzer.aclose()


asyncio.run(main())
