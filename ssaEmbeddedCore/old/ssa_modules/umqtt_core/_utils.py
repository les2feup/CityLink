def with_exponential_backoff(func, retries, base_timeout_ms):
    """
    Attempts to execute a function with exponential backoff on failure.

    This function calls the provided callable, retrying up to the specified number of times.
    After each failure, it waits for an exponentially increasing delay starting at base_timeout_ms
    milliseconds. If the callable succeeds, its result is returned immediately; if all attempts fail,
    an Exception is raised.

    Args:
        func: The callable to execute.
        retries: The maximum number of retry attempts.
        base_timeout_ms: The initial wait time in milliseconds, which doubles after each attempt.

    Returns:
        The result of the callable if execution is successful.

    Raises:
        Exception: If the callable fails on all retry attempts.
    """
    from time import sleep_ms

    for i in range(retries):
        retry_timeout = base_timeout_ms * (2**i)
        print(f"[INFO] Trying {func.__name__} (attempt {i + 1}/{retries})")
        try:
            return func()
        except Exception as e:
            print(
                f"[ERROR] {func.__name__} failed: {e}, retrying in {retry_timeout} milliseconds"
            )
            sleep_ms(retry_timeout)

    raise Exception(f"[ERROR] {func.__name__} failed after {retries} retries")


def iterative_dict_diff(old, new):
    """
    Compute the difference between two dictionaries.

    Compares the original dictionary 'old' with the updated dictionary 'new' and
    returns a dictionary capturing any key additions or value updates. Nested
    dictionaries are processed iteratively, and empty dictionary entries are
    removed from the result.

    Args:
        old: The original dictionary.
        new: The updated dictionary.

    Returns:
        A dictionary representing the differences from 'old' to 'new'.
    """
    diff = {}
    # Stack holds tuples: (parent_dict, key, old_sub, new_sub)
    # For the top level, parent_dict is diff and key is None.
    stack = [(diff, None, old, new)]

    while stack:
        parent_diff, key, old_d, new_d = stack.pop()
        # For the top level, key is None so container is parent_diff.
        # For nested levels, create a new dict if needed.
        container = parent_diff if key is None else parent_diff.setdefault(key, {})

        for k, new_val in new_d.items():
            if k not in old_d:
                container[k] = new_val
            else:
                old_val = old_d[k]
                if isinstance(new_val, dict) and isinstance(old_val, dict):
                    # Instead of recursing, push the nested dictionaries onto the stack.
                    stack.append((container, k, old_val, new_val))
                elif new_val != old_val:
                    container[k] = new_val

    def remove_empty(d):
        # Recursively remove empty dictionaries from the diff.
        keys_to_delete = []
        for k, v in d.items():
            if isinstance(v, dict):
                remove_empty(v)
                if not v:
                    keys_to_delete.append(k)
        for k in keys_to_delete:
            del d[k]

    remove_empty(diff)
    return diff
