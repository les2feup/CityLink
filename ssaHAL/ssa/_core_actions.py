

async def vfs_action(ssa, input):
    action = input["action"]



    from binascii import crc32
    from os import mkdir, listdir
    from machine import soft_reset

    script = update["script"]
    expected_crc = int(update["crc32"], 16)
    script_crc = crc32(script)

    if script_crc != expected_crc:
        print(f"[ERROR] CRC32 mismatch: expected:{hex(expected_crc)}, \
                got {hex(script_crc)} Firmware update failed.")
        return

    if "user" not in listdir():
        mkdir("user")

    print("[INFO] Writing firmware to device")
    with open("user/app.py", "w") as f:
        f.write(script)

async def reload_action(*_):
    from machine import soft_reset
    soft_reset()

async def property_update(ssa, value, prop):
    """
    Asynchronously updates a property on the given SSA instance.    

    This function checks whether the specified property exists on the SSA 
    object and updates the property using the SSA setter with the provided value.
    If an error occurs during this process, an error message is printed with the details.
    
    Args:
        ssa: The object whose property is to be updated.
        value: The new value for the property.
        prop: The name of the property to update.
    """
    if not ssa.has_property(prop):
        print(f"[ERROR] Property '{prop}' does not exist.")
        return

    if not ssa.uses_default_set_action(prop):
        print(f"[ERROR] Property '{prop}' cannot be updated via the default setter.")
        return

    try:
        await ssa.set_property(prop, value)
    except Exception as e:
        print(f"[ERROR] Failed to update property '{prop}': {e}")
