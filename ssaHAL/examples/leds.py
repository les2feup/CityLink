from ssa import SSA, ssa_main
import json

def valid_led_name(led_name: str):
    return led_name.startswith("led_") and int(led_name[4:]) in range(1, 9)

def set_led_brightness(ssa: SSA, _msg: str, led_name: str, brightness: str):
    if not valid_led_name(led_name):
        print("Invalid LED name")
        return

    brightness = int(brightness)
    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100")
        return

    led_strip = ssa.get_property("led_strip")
    led_strip[led_name]["brightness"] = brightness
    ssa.set_property("led_strip", led_strip)

def set_led_color(ssa: SSA, _msg:str, led_name: str, color: str):
    if not valid_led_name(led_name):
        print("Invalid LED name")
        return

    try:
        color = int(color, 16)
    except ValueError:
        print("Color value must be an hexadecimal RGB string")
        return

    if color < 0 or color > 0xFFFFFF:
        print("RGB value must be between 0 and 0xFFFFFF")

    led_strip = ssa.get_property("led_strip")
    led_strip[led_name]["color"] = color
    ssa.set_property("led_strip", led_strip)

def toggle_led(ssa: SSA, _msg: str, led_name: str, state: str):
    if not valid_led_name(led_name):
        print("Invalid LED name")
        return

    if state not in ["on", "off"]:
        print("Invalid state")
        return

    led_strip = ssa.get_property("led_strip")
    led_strip[led_name]["is_on"] = state == "on"
    ssa.set_property("led_strip", led_strip)

def toggle_led_strip(ssa: SSA, _msg: str, state: str):
    if state not in ["on", "off"]:
        print("Invalid state")
        return

    led_strip = ssa.get_property("led_strip")
    for led in led_strip.values():
        led["is_on"] = state == "on"

    ssa.set_property("led_strip", led_strip)

@ssa_main()
def main(ssa: SSA):
    N_LEDS = 8
    simulated_led = {
        "brightness": 100,
        "color": 0xFFFFFF,
        "is_on": False
    }
    led_strip = {f"led_{i}": simulated_led.copy() for i in range(1, N_LEDS + 1)}
    ssa.create_property("led_strip", led_strip)

    ssa.register_action("led_strip/toggle/{state}", toggle_led_strip)
    ssa.register_action("led_strip/{led_name}/toggle/{state}", toggle_led)
    ssa.register_action("led_strip/{led_name}/set_color/{color}", set_led_color)
    ssa.register_action("led_strip/{led_name}/set_brightness/{brightness}", set_led_brightness)
