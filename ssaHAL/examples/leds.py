from ssa import SSA, ssa_main

def set_led_brightness(ssa: SSA, _msg: str, led_name: str, brightness: str):
    """
    Adjusts the brightness of a specific LED.
    
    Retrieves the LED strip configuration from the SSA instance and checks whether the specified LED exists. Converts the brightness value provided as a string into an integer and validates that it falls within the range 0–100. If the LED exists and the brightness is within bounds, updates the LED's brightness; otherwise, prints an error message.
    """
    led_strip = ssa.get_property("led_strip")
    if led_name not in led_strip:
        print(f"Invalid LED name {led_name}")
        return

    brightness = int(brightness)
    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100")
        return

    led_strip[led_name]["brightness"] = brightness
    ssa.set_property("led_strip", led_strip)

def set_led_color(ssa: SSA, _msg: str, led_name: str, color: str):
    """
    Sets the color of a specified LED.
    
    Retrieves the current LED strip configuration, validates that the LED name
    exists, and converts the provided hexadecimal RGB string into an integer. If the
    conversion is successful and the color value is within 0 to 0xFFFFFF, the LED's
    color is updated and the new configuration is saved. Prints an error message if
    the LED name is invalid, the color string cannot be parsed, or the value is out
    of range.
    
    Parameters:
        led_name: Identifier of the LED to update.
        color: Hexadecimal RGB string representing the desired color.
    """
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
    ssa.set_property("led_strip", led_strip)

def toggle_led(ssa: SSA, _msg: str, led_name: str, state: str):
    """
    Toggles the state of a specified LED on the LED strip.
    
    Retrieves the current LED configuration from the SSA instance and verifies that the
    provided LED name exists and the state is valid ("on" or "off"). If both checks pass,
    the LED's state is updated accordingly and the new configuration is saved. Otherwise,
    an error message is printed.
    """
    led_strip = ssa.get_property("led_strip")
    if led_name not in led_strip:
        print("Invalid LED name")
        return

    if state not in ["on", "off"]:
        print("Invalid state")
        return

    led_strip[led_name]["is_on"] = state == "on"
    ssa.set_property("led_strip", led_strip)

def toggle_led_strip(ssa: SSA, _msg: str, state: str):
    """
    Toggles the state of all LEDs on the strip.
    
    If the provided state is "on", all LEDs are turned on; if "off", they are turned off.
    An invalid state prints an error message without modifying the LED strip.
    """
    if state not in ["on", "off"]:
        print(f"Invalid state: {state}")
        return

    led_strip = ssa.get_property("led_strip")
    for led in led_strip.values():
        led["is_on"] = state == "on"

    ssa.set_property("led_strip", led_strip)

@ssa_main()
def main(ssa: SSA):
    """
    Initializes a simulated LED strip and registers LED control actions.
    
    This function creates a simulated LED strip with eight LEDs, each initialized
    with a default brightness of 100, a white color, and turned off. It exposes the
    LED strip as a property in the SSA system and registers actions to toggle the
    entire strip, toggle individual LEDs, set an LED’s color, and adjust an LED’s
    brightness.
    """
    N_LEDS = 8
    simulated_led = {
            "brightness": 100,
            "color": hex(0xFFFFFF),
            "is_on": False
            }
    led_strip = {f"led_{i}": simulated_led.copy() for i in range(1, N_LEDS + 1)}
    ssa.create_property("led_strip", led_strip)

    ssa.register_action("led_strip/toggle/{state}", toggle_led_strip)
    ssa.register_action("led_strip/{led_name}/toggle/{state}", toggle_led)
    ssa.register_action("led_strip/{led_name}/set_color/{color}", set_led_color)
    ssa.register_action("led_strip/{led_name}/set_brightness/{brightness}", set_led_brightness)
