from ssa import SSA, ssa_main

async def set_led_brightness(ssa: SSA, _msg: str, led_name: str, brightness: str):
    led_strip = ssa.get_property("led_strip")
    if led_name not in led_strip:
        print(f"Invalid LED name {led_name}")
        return

    brightness = int(brightness)
    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100")
        return

    led_strip[led_name]["brightness"] = brightness
    await ssa.set_property("led_strip", led_strip)

async def set_led_color(ssa: SSA, _msg: str, led_name: str, color: str):
    led_strip = ssa.get_property("led_strip")
    if led_name not in led_strip:
        print(f"Invalid LED name: {led_name}")
        return

    try:
        color = int(color, 16)
    except ValueError:
        print("Color value must be an hexadecimal RGB string")
        return

    if color < 0 or color > 0xFFFFFF:
        print("RGB value must be between 0 and 0xFFFFFF")
        return

    led_strip[led_name]["color"] = hex(color)
    await ssa.set_property("led_strip", led_strip)

async def toggle_led(ssa: SSA, _msg: str, led_name: str, state: str):
    led_strip = ssa.get_property("led_strip")
    if led_name not in led_strip:
        print(f"Invalid LED name: {led_name}")
        return

    if state not in ["on", "off"]:
        print(f"Invalid state: {state}, must be 'on' or 'off'")
        return

    led_strip[led_name]["is_on"] = state == "on"
    await ssa.set_property("led_strip", led_strip)

async def toggle_led_strip(ssa: SSA, _msg: str, state: str):
    if state not in ["on", "off"]:
        print(f"Invalid state: {state}")
        return

    led_strip = ssa.get_property("led_strip")
    for led in led_strip.values():
        led["is_on"] = state == "on"

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
    led_strip = {f"led_{i}": simulated_led.copy() for i in range(1, N_LEDS + 1)}

    # We only want the property to be updated via the actions defined below
    # So we set uses_default_setter to False
    # If we don't do this, the property can be updated via the default setter
    # which is accessible at (...)/ssa/set/{property_name}
    ssa.create_property("led_strip", led_strip, uses_default_setter=False)

    ssa.register_action("led_strip/toggle/{state}", toggle_led_strip)
    ssa.register_action("led_strip/{led_name}/toggle/{state}", toggle_led)
    ssa.register_action("led_strip/{led_name}/set_color/{color}", set_led_color)
    ssa.register_action("led_strip/{led_name}/set_brightness/{brightness}", set_led_brightness)
