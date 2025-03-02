from ssa import SSA, ssa_main

class SimulatedLED():
    def __init__(self):
        self.is_on = False
        self.brighness = 0
        self.rgb = 0x000000

    def set_is_on(self, is_on: bool):
        self.is_on = is_on

    def set_brightness(self, brightness: int):
        self.brighness = brightness

    def set_rgb(self, rgb: int):
        self.rgb = rgb

def valid_led_name(led_name: str):
    return led_name.startswith("led_") and int(led_name[4:]) in range(1, 9)

def set_led_brightness(ssa: SSA, led_name: str, brightness: int):
    if not valid_led_name(led_name):
        print("Invalid LED name")
        return

    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100")
        return

    led_strip = ssa.get_property("led_strip")
    led_strip[led_name].set_brightness(brightness)
    ssa.set_property("led_strip", led_strip)

def set_led_rgb(ssa: SSA, led_name: str, rgb: str):
    if not valid_led_name(led_name):
        print("Invalid LED name")
        return

    try:
        int(rgb, 16)
    except ValueError:
        print("RGB value must be a hexadecimal string")
        return

    if rgb < 0 or rgb > 0xFFFFFF:
        print("RGB value must be between 0 and 0xFFFFFF")

    led_strip = ssa.get_property("led_strip")
    led_strip[led_name].set_rgb(rgb)
    ssa.set_property("led_strip", led_strip)

def toggle_led(ssa: SSA, led_name: str, state: bool):
    if not valid_led_name(led_name):
        print("Invalid LED name")
        return

    led_strip = ssa.get_property("led_strip")
    led_strip[led_name].set_is_on(state)
    ssa.set_property("led_strip", led_strip)

def toggle_led_strip(ssa: SSA, state: bool):
    led_strip = ssa.get_property("led_strip")
    for led in led_strip.values():
        led.set_is_on(state)
    ssa.set_property("led_strip", led_strip)

@ssa_main()
def main(ssa: SSA):
    N_LEDS = 8
    led_strip = {f"led_{i}": SimulatedLED() for i in range(1, N_LEDS + 1)}
    ssa.create_property("led_strip", led_strip)

    ssa.register_action("led_strip/toggle/{state}", toggle_led_strip)
    ssa.register_action("led_strip/{led_name}/toggle/{state}", toggle_led)
    ssa.register_action("led_strip/{led_name}/set_color/{rgb}", set_led_rgb)
    ssa.register_action("led_strip/{led_name}/set_brightness/{brighness}", set_led_brightness)
