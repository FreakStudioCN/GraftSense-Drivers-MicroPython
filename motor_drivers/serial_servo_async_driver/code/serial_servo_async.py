"""Cooperative UART facade for the serial-servo packet protocol."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

class SerialServoAsync:
    """Async-only serial-servo subset used by the package example.

    The packet layout, checksum and 5 ms response settlement match the source.
    """
    MOVE_TIME_WRITE = 1
    MOVE_TIME_READ = 2

    def __init__(self, uart):
        self._uart = uart
        self._lock = asyncio.Lock()
        self._closed = False

    def _checksum(self, data):
        return ~(sum(data) & 0xFF) & 0xFF

    def _write(self, servo_id, command, params):
        packet = [0x55, 0x55, servo_id, 3 + len(params), command] + params
        packet.append(self._checksum(packet[2:]))
        self._uart.write(bytearray(packet))

    def _read(self, command, length):
        data = self._uart.read()
        if data is None or len(data) < 6 or data[0] != 0x55 or data[1] != 0x55:
            return []
        if data[4] != command or data[3] != length or data[-1] != self._checksum(data[2:-1]):
            return []
        return data[5:-1]

    async def move_servo_immediate_async(self, servo_id, angle, time_ms):
        if not 0 <= angle <= 240 or not 0 <= time_ms <= 30000:
            raise ValueError("angle or time out of range")
        value = int(angle / 0.24)
        async with self._lock:
            self._write(servo_id, self.MOVE_TIME_WRITE,
                        [value & 0xFF, value >> 8, time_ms & 0xFF, time_ms >> 8])

    async def get_servo_move_immediate_async(self, servo_id):
        params = await self._query_async(servo_id, self.MOVE_TIME_READ, 7)
        if len(params) != 4:
            return None
        angle = (params[0] + (params[1] << 8)) * 0.24
        time_ms = params[2] + (params[3] << 8)
        if not 0 <= angle <= 240:
            raise ValueError("Angle value is out of range.")
        if not 0 <= time_ms <= 30000:
            raise ValueError("Time value is out of range.")
        return angle, time_ms

    async def _query_async(self, servo_id, command, response_length):
        async with self._lock:
            self._write(servo_id, command, [])
            await asyncio.sleep_ms(5)
            return self._read(command, response_length)

    async def move_servo_with_time_delay_async(self, servo_id, angle, time_ms):
        if not 0 <= angle <= 240 or not 0 <= time_ms <= 30000:
            raise ValueError("angle or time out of range")
        value = int(angle / 0.24)
        async with self._lock:
            self._write(servo_id, 7, [value & 0xFF, value >> 8, time_ms & 0xFF, time_ms >> 8])
    async def get_servo_move_with_time_delay_async(self, servo_id):
        raise ValueError("This function is not working properly! You can use get_servo_move_immediate_async() instead.")

    async def start_servo_async(self, servo_id):
        async with self._lock: self._write(servo_id, 11, [])

    async def stop_servo_async(self, servo_id):
        async with self._lock: self._write(servo_id, 12, [])

    async def set_servo_id_async(self, servo_id, new_id):
        if not 0 <= new_id <= 253:
            raise ValueError("New ID must be in range 0~253.")
        async with self._lock: self._write(servo_id, 13, [new_id])

    async def get_servo_id_async(self, servo_id):
        params = await self._query_async(servo_id, 14, 4)
        if len(params) != 1:
            return None
        if not 0 <= params[0] <= 254:
            raise ValueError("Servo ID must be in range 0~254.")
        return params[0]

    async def set_servo_angle_offset_async(self, servo_id, angle, save_to_memory=False):
        if not -30 <= angle <= 30:
            raise ValueError("Angle must be in range -30~30.")
        offset = int(angle / 0.24) % 256
        async with self._lock:
            self._write(servo_id, 17, [offset])
            if save_to_memory:
                self._write(servo_id, 18, [])

    async def get_servo_angle_offset_async(self, servo_id):
        params = await self._query_async(servo_id, 19, 4)
        if len(params) != 1:
            return None
        offset = params[0] - 256 if params[0] > 127 else params[0]
        angle = offset * (30 / 125.0)
        if not -30 <= angle <= 30:
            raise ValueError("Angle offset must be in range -30~30.")
        return angle

    async def set_servo_angle_range_async(self, servo_id, min_angle, max_angle):
        if not 0 <= min_angle <= 240 or not 0 <= max_angle <= 240:
            raise ValueError("Angle must be in range 0~240.")
        if min_angle >= max_angle:
            raise ValueError("Max angle must be greater than min angle.")
        low, high = int(min_angle / .24), int(max_angle / .24)
        async with self._lock: self._write(servo_id, 20, [low & 255, low >> 8, high & 255, high >> 8])

    async def get_servo_angle_range_async(self, servo_id):
        params = await self._query_async(servo_id, 21, 7)
        if len(params) != 4:
            return None
        minimum = (params[0] + (params[1] << 8)) * 0.24
        maximum = (params[2] + (params[3] << 8)) * 0.24
        if not 0 <= minimum <= 240 or not 0 <= maximum <= 240:
            raise ValueError("Angle must be in range 0~240.")
        if minimum >= maximum:
            raise ValueError("Min angle must be less than max angle.")
        return minimum, maximum

    async def set_servo_vin_range_async(self, servo_id, min_vin, max_vin):
        if min_vin >= max_vin:
            raise ValueError("Minimum voltage must be less than maximum voltage.")
        if not 4.5 <= min_vin <= 14.0 or not 4.5 <= max_vin <= 14.0:
            raise ValueError("Voltage must be in range 4.5V ~ 14.0V.")
        low, high = int(min_vin * 1000), int(max_vin * 1000)
        async with self._lock: self._write(servo_id, 22, [low & 255, low >> 8, high & 255, high >> 8])

    async def get_servo_vin_range_async(self, servo_id):
        params = await self._query_async(servo_id, 23, 7)
        if len(params) != 4:
            return None
        minimum = (params[0] + (params[1] << 8)) / 1000
        maximum = (params[2] + (params[3] << 8)) / 1000
        if not 4.5 <= minimum <= 12.0 or not 4.5 <= maximum <= 14.0:
            raise ValueError("Voltage must be in range 4.5V ~ 14.0V.")
        if minimum >= maximum:
            raise ValueError("Min voltage must be less than max voltage.")
        return minimum, maximum

    async def set_servo_temp_range_async(self, servo_id, max_temp):
        if not 50 <= max_temp <= 100:
            raise ValueError("Temperature must be between 50 and 100 degrees Celsius.")
        async with self._lock: self._write(servo_id, 24, [max_temp])

    async def get_servo_temp_range_async(self, servo_id):
        params = await self._query_async(servo_id, 25, 4)
        if len(params) != 1:
            return None
        if not 50 <= params[0] <= 100:
            raise ValueError("Temperature limit is out of range.")
        return params[0]

    async def read_servo_temp_async(self, servo_id):
        params = await self._query_async(servo_id, 26, 4)
        if len(params) != 1:
            return None
        if not 0 <= params[0] <= 100:
            raise ValueError("Temperature is out of range.")
        return params[0]

    async def read_servo_voltage_async(self, servo_id):
        params = await self._query_async(servo_id, 27, 5)
        if len(params) != 2:
            return None
        voltage = (params[0] + (params[1] << 8)) / 1000.0
        if not 4.5 <= voltage <= 12.0:
            raise ValueError("Voltage is out of range.")
        return voltage

    async def read_servo_position_async(self, servo_id):
        params = await self._query_async(servo_id, 28, 5)
        if len(params) != 2:
            return None
        position = params[0] + (params[1] << 8)
        if position >= 0x8000:
            position -= 0x10000
        angle = (position / 1000) * 240
        if not 0 <= angle <= 240:
            raise ValueError("Position is out of range.")
        return angle

    async def set_servo_mode_and_speed_async(self, servo_id, mode, speed):
        if mode not in (0, 1):
            raise ValueError("Invalid mode, must be 0 or 1.")
        if mode == 1:
            if not -1000 <= speed <= 1000:
                raise ValueError("Speed must be between -1000 and 1000 in motor control mode.")
            speed %= 65536
        else:
            speed = 0
        async with self._lock: self._write(servo_id, 29, [mode, 0, speed & 255, (speed >> 8) & 255])

    async def get_servo_mode_and_speed_async(self, servo_id):
        params = await self._query_async(servo_id, 30, 7)
        if len(params) != 4:
            return None
        mode = params[0]
        if mode not in (0, 1):
            raise ValueError("Invalid servo mode.")
        if mode == 1:
            return mode, params[2] + (params[3] << 8)
        return mode, 0

    async def set_servo_motor_load_async(self, servo_id, unload):
        async with self._lock: self._write(servo_id, 31, [1 if unload else 0])

    async def get_servo_motor_load_status_async(self, servo_id):
        params = await self._query_async(servo_id, 32, 4)
        if len(params) != 1:
            return None
        if params[0] not in (0, 1):
            raise ValueError("Invalid motor status value.")
        return params[0] == 1

    async def set_servo_led_async(self, servo_id, led_on):
        async with self._lock: self._write(servo_id, 33, [1 if led_on else 0])

    async def get_servo_led_async(self, servo_id):
        params = await self._query_async(servo_id, 34, 4)
        if len(params) != 1:
            return None
        if params[0] not in (0, 1):
            raise ValueError("Invalid LED status value.")
        return params[0] == 1

    async def set_servo_led_alarm_async(self, servo_id, alarm_code):
        if not 0 <= alarm_code <= 7:
            raise ValueError("Invalid alarm code. Must be between 0 and 7.")
        async with self._lock: self._write(servo_id, 35, [alarm_code])

    async def get_servo_led_alarm_async(self, servo_id):
        params = await self._query_async(servo_id, 36, 4)
        if len(params) != 1:
            return None
        if not 0 <= params[0] <= 7:
            raise ValueError("Error alarm value is out of range.")
        return params[0]

    async def aclose(self):
        if self._closed: return
        self._closed = True
        self._uart.deinit()
