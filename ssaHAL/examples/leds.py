from ssa.core import SSA, ssa_main


def get_led_index(led_index: str):
    """
    Converts a string LED index to an integer.
    
    Attempts to convert the provided LED index from its string representation to an
    integer using base-10 conversion. If the conversion fails, an error message is
    printed and None is returned.
    """
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
    """
    Set the brightness of a specific LED.
    
    Converts the LED index and brightness from their string representations. If the LED index is not valid or the brightness (after conversion to an integer) is not between 0 and 100, the function aborts without making any changes. Otherwise, it updates the LED's brightness in the simulated strip and persists the change asynchronously.
    """
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
    """
    Sets the color of a specific LED asynchronously.
    
    This function updates an LED's color in the LED strip using a hexadecimal RGB
    string. It validates the LED index and the color value, converting the latter to
    an integer and ensuring it lies between 0 and 0xFFFFFF. If any validation fails,
    an error message is printed and no update is performed.
    
    Args:
        led_index: String representing the target LED's index.
        color: Hexadecimal RGB string indicating the new color.
    """
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
    """
    Toggle a specified LED on or off.
    
    This asynchronous function converts the LED identifier from a string to an integer
    and updates the corresponding LED's state in the LED strip. The change is saved using
    the system's property mechanism. If the LED index is invalid or the state is not "on" or
    "off", the function prints an error message and makes no update.
    
    Args:
        led_index (str): The LED index as a string, to be validated and converted.
        state (str): The desired state ("on" or "off") for the LED.
    """
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
    """
    Toggles the on/off state of all LEDs in the strip.
    
    This asynchronous function updates each LED's "is_on" property based on the given state.
    If the state is "on", every LED is turned on; if "off", every LED is turned off.
    If an invalid state is provided, the function prints an error message and makes no changes.
    
    Args:
        state: Desired state for the LED strip, either "on" or "off".
    """
    if state not in ["on", "off"]:
        print(f"Invalid state: {state}")
        return

    led_strip = ssa.get_property("led_strip")
    for led in led_strip:
        led["is_on"] = state == "on"

    await ssa.set_property("led_strip", led_strip)


async def set_strip_brightness(ssa: SSA, _msg: str, brightness: str):
    """
    Sets the brightness for all LEDs on the strip.
    
    Converts the brightness input from a string to an integer and applies it to each LED if the
    value is between 0 and 100. If the brightness is outside this range, an error message is printed,
    and the update is aborted. The updated LED strip state is then saved asynchronously.
    """
    led_strip = ssa.get_property("led_strip")

    brightness = int(brightness)
    if brightness < 0 or brightness > 100:
        print("Brightness must be between 0 and 100")
        return

    for led in led_strip:
        led["brightness"] = brightness

    await ssa.set_property("led_strip", led_strip)


async def set_strip_color(ssa: SSA, _msg: str, color: str):
    """
    Set the color of all LEDs in the strip.
    
    Converts a hexadecimal RGB string to an integer and validates that it is within the
    allowable range (0 to 0xFFFFFF). If valid, each LED in the led_strip property is updated
    with the new color and the change is applied asynchronously. If the conversion fails or
    the value is out of range, an error message is printed and no update is performed.
    """
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
    """
    Initializes the LED strip and registers actions for LED control.
    
    This function sets up a simulated LED strip with default brightness, color, and state values,
    creates a corresponding property in the SSA system (disabling default updates), and registers
    actions to toggle and update color and brightness for the entire strip as well as individual LEDs.
    """
    simulated_led = {"brightness": 100, "color": hex(0xFFFFFF), "is_on": False}
    led_strip = [simulated_led.copy() for i in range(N_LEDS)]

    # We only want the property to be updated via the actions defined below
    # So we set use_default_action to False.
    # If we don't do this, the property can be updated via the default setter
    # which is accessible at (...)/ssa/set/{property_name}
    ssa.create_property("led_strip", led_strip, use_default_action=False)

    ssa.register_action("led_strip/toggle/{state}", toggle_led_strip)
    ssa.register_action("led_strip/set_color/{color}", set_strip_color)
    ssa.register_action("led_strip/set_brightness/{brightness}", set_strip_brightness)

    ssa.register_action("led_strip/{led_index}/toggle/{state}", toggle_led)
    ssa.register_action("led_strip/{led_index}/set_color/{color}", set_led_color)
    ssa.register_action(
        "led_strip/{led_index}/set_brightness/{brightness}", set_led_brightness
    )
