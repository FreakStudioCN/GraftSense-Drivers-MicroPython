from time import sleep_ms
from AS5600L import AS5600L



myPos = AS5600L(hyst=1)

print(myPos.getStatus())

while True:
    print('Degrees:', myPos.getAngleDegrees())
    sleep_ms(333)


