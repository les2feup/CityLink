import sys
import os


def _delete_all(directory=".", keep_this=True):
    """
    Recursively delete all files and directories in the specified path.

    This function removes every file and subdirectory under the given directory when
    running on a MicroPython device. When keep_this is True, the script file
    "_nuke.py" is not deleted. If the function is not running on a MicroPython board,
    it prints a message and exits without deleting anything.

    Args:
        directory: The target directory for deletion (default is ".").
        keep_this: If True, preserves the "_nuke.py" file (default is True).
    """
    try:
        import machine
    except:
        # not a micropython board so exit gracefully
        print("Not a micro-python board! Leaving it well alone.")
        return

    for fi in os.ilistdir(directory):
        fn, ft = fi[0:2]  # can be 3 or 4 items returned!
        if keep_this and fn == "_nuke.py":
            continue
        fp = "%s/%s" % (directory, fn)
        print("removing %s" % fp)
        if ft == 0x8000:
            os.remove(fp)
        else:
            _delete_all(fp)
            os.rmdir(fp)


if __name__ == "__main__":
    # Default to current directory if no argument is provided
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    _delete_all(root_dir)
