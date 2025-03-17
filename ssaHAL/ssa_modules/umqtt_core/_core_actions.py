import ssa_lib.core_actions as actions


def _add_timestamp(data):
    from time import gmtime, mktime

    event_data = event_data.update(
        {timestamp: {epoch: gmtime(0)[0], seconds: mktime(gmtime())}}
    )

    return event_data


def vfs_list(input):
    event_data = {
        action: "list",
        error: False,
    }

    try:
        ls_output = actions.vfs_list(input)
        return _add_timestamp(
            event_data.update(
                {
                    message: ls_output,
                }
            )
        )
    except Exception as e:
        return _add_timestamp(
            event_data.update(
                {
                    error: True,
                    message: f"Failed to list files: {e}",
                }
            )
        )

    return _add_timestamp(event_data)


def vfs_read(input):
    pass


def vfs_write(input):
    event_data = {
        action: "write",
        error: False,
    }

    try:
        actions.vfs_write(input)
        return _add_timestamp(
            event_data.update(
                {
                    message: input["path"],
                }
            )
        )
    except Exception as e:
        return _add_timestamp(
            event_data.update(
                {
                    error: True,
                    message: f"Failed to write file: {e}",
                }
            )
        )

    return _add_timestamp(event_data)


def vfs_delete(input):
    pass
