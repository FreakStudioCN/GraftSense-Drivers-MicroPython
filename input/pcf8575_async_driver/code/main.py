try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from pcf8575_async import PCF8575Async as PCF8575
from _gs_pcf8575_SSD1306 import SSD1306_I2C
from _gs_pcf8575_menu import SimpleOLEDMenu

LED_COUNT = 8
KEYS = {
    0b1000000011111111: "UP",
    0b0000100011111111: "DOWN",
    0b0100000011111111: "LEFT",
    0b0010000011111111: "RIGHT",
    0b0001000011111111: "CENTER",
}


async def main():
    print("FreakStudio: PCF8575 async LED and menu demo")
    led = Pin(25, Pin.OUT, Pin.PULL_DOWN)
    i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)
    address = 0x20
    for device in i2c.scan():
        if 0x20 <= device <= 0x27:
            address = device
            break
    pcf8575 = PCF8575(i2c, address, interrupt_pin=Pin(8))
    oled = SSD1306_I2C(i2c, 0x3C, 128, 64, False)
    menu = SimpleOLEDMenu(oled, "Main Menu", 0, 0, 128, 64)

    def led_on():
        led.value(1)

    def led_off():
        led.value(0)

    def print_message():
        menu.show_message("No Sub Option")

    def view_variable():
        menu.show_message("Variable")

    def set_parameter():
        menu.show_message("Parameter")

    menu.add_menu("Option1")
    menu.add_menu("Option2")
    menu.add_menu("LED Option")
    menu.add_menu("Variable Option", enter_callback=view_variable)
    menu.add_menu("Parameter Option", enter_callback=set_parameter)
    menu.add_menu("Sub Option1", parent_name="Option1", enter_callback=print_message)
    menu.add_menu("LED ON", parent_name="LED Option", enter_callback=led_on)
    menu.add_menu("LED OFF", parent_name="LED Option", enter_callback=led_off)
    menu.display_menu()
    try:
        await pcf8575.initialize_async()
        await pcf8575.set_port_async(0x00FF)
        index = 0
        while True:
            if await pcf8575.dispatch_pending_async():
                state = await pcf8575.get_port_async()
                key = KEYS.get(state)
                if key == "UP":
                    menu.select_up()
                elif key == "DOWN":
                    menu.select_down()
                elif key == "LEFT":
                    menu.select_back()
                elif key == "RIGHT":
                    menu.delete_menu(menu.head.sub_menu[menu.selected_index].name)
                elif key == "CENTER":
                    menu.select_current()
                if key is not None:
                    print("Select Menu: {}".format(menu.get_current_menu_name()))
            await pcf8575.pin_async(index, False)
            await asyncio.sleep_ms(200)
            print("Lower 8 bits state: {:08b}".format((await pcf8575.get_port_async()) & 0xFF))
            await pcf8575.set_port_async(0x00FF)
            index = (index + 1) % LED_COUNT
            await asyncio.sleep_ms(50)
    finally:
        await pcf8575.aclose()


if __name__ == "__main__":
    asyncio.run(main())
