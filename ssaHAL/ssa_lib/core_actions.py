import os


def vfs_list(input):
    raise NotImplementedError("This function is not implemented yet.")


def vfs_read(input):
    raise NotImplementedError("This function is not implemented yet.")


def vfs_write(input):
    file_path = input["path"]
    data = input["payload"].get("data")
    hash = int(input["payload"].get("hash"), 16)
    hash_algo = input["payload"].get("algo")

    if hash_algo != "crc32":
        raise NotImplementedError("Only CRC32 is supported for now.")

    from binascii import crc32

    actual_hash = crc32(data)
    if actual_hash != hash:
        raise ValueError(f"Hash mismatch, expected {hex(hash)}, got {hex(actual_hash)}")

    mode = "a" if input.get("append", False) else "w"

    file_path = file_path.rstrip("/")
    path_parts = file_path.split("/")
    file_name = path_parts[-1]

    if os.getcwd() != "/":
        os.chdir("/")

    for part in path_parts[:-1]:
        if part not in os.listdir():
            os.mkdir(part)
        os.chdir(part)

    with open(file_name, mode) as f:
        f.write(data)

    return file_path


def vfs_delete(input):
    raise NotImplementedError("This function is not implemented yet.")
