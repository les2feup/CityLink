import ssa_lib.core_actions as actions


def _add_timestamp(event_data):
    """Add a timestamp to the given event data.
    
    Updates the event data dictionary by adding a 'timestamp' key with two entries:
      - epoch: the base epoch year (typically 1970)
      - seconds: the current time in seconds.
    
    Args:
        event_data (dict): A dictionary containing event details to be updated.
    
    Returns:
        dict: The updated event data dictionary with the added timestamp.
    """
    from time import gmtime, mktime

    event_data.update(
        {"timestamp": {"epoch": gmtime(0)[0], "seconds": mktime(gmtime())}}
    )

    return event_data


def vfs_list(input):
    """
    List files in the virtual file system.
    
    Retrieves a listing of files by passing the given input to the underlying VFS
    operation. On success, returns a dictionary with the file list; on failure, the
    dictionary contains an error flag and an error message. A timestamp is appended
    to the result.
    
    Args:
        input: Data or criteria used to determine which files to list in the VFS.
    
    Returns:
        A dictionary with the following keys:
            "action": The type of action performed ("list").
            "error": A boolean indicating whether an error occurred.
            "message": The file listing on success or an error message on failure.
            Additional timestamp fields added by the helper.
    """
    event_data = {
        "action": "list",
        "error": False,
    }

    try:
        ls_output = actions.vfs_list(input)
        event_data.update(
            {
                "message": ls_output,
            }
        )

    except Exception as e:
        event_data.update(
            {
                "error": True,
                "message": f"Failed to list files: {e}",
            }
        )

    return _add_timestamp(event_data)


def vfs_read(input):
    """
    Reads a file from the virtual file system.
    
    This function is a placeholder for future implementation of file reading functionality.
    The input should include the necessary details to identify and retrieve the target file.
    
    :param input: Data required to specify which file to read (format TBD).
    """
    pass


def vfs_write(input):
    """
    Writes a file via the virtual file system (VFS) and returns event data with a timestamp.
    
    This function attempts to perform a file write operation using the provided input details. On
    success, the event data is updated with the file path; on failure, it reflects the error with a
    detailed message. A timestamp is appended to the returned event data.
        
    Args:
        input (dict): Dictionary of file details, which must include a 'path' key indicating the target file.
        
    Returns:
        dict: Event data indicating the outcome of the operation, including status, message, and a timestamp.
    """
    event_data = {
        "action": "write",
        "error": False,
    }

    try:
        actions.vfs_write(input)

        event_data.update(
            {
                "message": input["path"],
            }
        )

    except Exception as e:
        event_data.update(
            {
                "error": True,
                "message": f"Failed to write file: {e}",
            }
        )

    return _add_timestamp(event_data)


def vfs_delete(input):
    """
    Delete a file from the virtual file system.
    
    This function is a placeholder for a future implementation that will handle
    file deletion within the virtual file system. Currently, it does nothing.
    
    Args:
        input: Data required to identify the file to be deleted.
    """
    pass
