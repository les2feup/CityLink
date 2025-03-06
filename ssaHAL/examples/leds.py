from ssa import SSA, ssa_main

def get_led_index(led_index: str):
    try:
        return int(led_index, 10)
    except ValueError:
        print(f"Invalid LED index: {led_index}")
        return None

    if led_index < 0 or led_index >= N_LEDS:
        print(f"Invalid LED index: {led_index}")
        return None

    return led_index

async def set_led_brightness(ssa: SSA, _msg: str, led_index: str, brightness: str):
    led_index = get_led_index(led_index)
    if led_index is None:
        return

    led_strip = ssa.get_property("led_strip")
    
    brightness = int(brightness)
    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100")
        return

    led_strip[led_index]["brightness"] = brightness
    await ssa.set_property("led_strip", led_strip)

async def set_led_color(ssa: SSA, _msg: str, led_index: str, color: str):
    led_index = get_led_index(led_index)
    if led_index is None:
        return

    led_strip = ssa.get_property("led_strip")

    try:
        color = int(color, 16)
    except ValueError:
        print("Color value must be an hexadecimal RGB string")
        return

    if color < 0 or color > 0xFFFFFF:
        print("RGB value must be between 0 and 0xFFFFFF")
        return

    led_strip[led_index]["color"] = hex(color)
    await ssa.set_property("led_strip", led_strip)

async def toggle_led(ssa: SSA, _msg: str, led_index: str, state: str):
    led_index = get_led_index(led_index)
    if led_index is None:
        return

    led_strip = ssa.get_property("led_strip")

    if state not in ["on", "off"]:
        print(f"Invalid state: {state}, must be 'on' or 'off'")
        return

    led_strip[led_index]["is_on"] = state == "on"
    await ssa.set_property("led_strip", led_strip)

async def toggle_led_strip(ssa: SSA, _msg: str, state: str):
    if state not in ["on", "off"]:
        print(f"Invalid state: {state}")
        return

    led_strip = ssa.get_property("led_strip")
    for led in led_strip:
        led["is_on"] = state == "on"

    await ssa.set_property("led_strip", led_strip)

async def set_strip_brightness(ssa: SSA, _msg: str, brightness: str):
    led_strip = ssa.get_property("led_strip")

    brightness = int(brightness)
    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100")
        return

    for led in led_strip:
        led["brightness"] = brightness

    await ssa.set_property("led_strip", led_strip)

async def set_strip_color(ssa: SSA, _msg: str, color: str):
    led_strip = ssa.get_property("led_strip")

    try:
        color = int(color, 16)
    except ValueError:
        print("Color value must be an hexadecimal RGB string")
        return

    if color < 0 or color > 0xFFFFFF:
        print("RGB value must be between 0 and 0xFFFFFF")
        return

    for led in led_strip:
        led["color"] = hex(color)

    await ssa.set_property("led_strip", led_strip)

# Number of LEDs in the strip
N_LEDS = 8

@ssa_main()
def main(ssa: SSA):
    simulated_led = {
            "brightness": 100,
            "color": hex(0xFFFFFF),
            "is_on": False
            }
    led_strip = [simulated_led.copy() for i in range(N_LEDS)]
    ssa.create_property("led_strip", led_strip)

    ssa.register_action("led_strip/toggle/{state}", toggle_led_strip)
    ssa.register_action("led_strip/set_color/{color}", set_strip_color)
    ssa.register_action("led_strip/set_brightness/{brightness}", set_strip_brightness)

    ssa.register_action("led_strip/{led_index}/toggle/{state}", toggle_led)
    ssa.register_action("led_strip/{led_index}/set_color/{color}", set_led_color)
    ssa.register_action("led_strip/{led_index}/set_brightness/{brightness}", set_led_brightness)
