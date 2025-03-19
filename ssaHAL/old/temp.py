def validate_configuration(template, provided, path="config"):
    """
    Validates that the given configuration matches the expected template.

    This function recursively verifies that all required keys specified in the template are present
    in the provided configuration and that their values are of the expected types. If the expected
    type for a key is a dictionary, the corresponding sub-configuration is recursively validated.

    Parameters:
        template: A dictionary mapping keys to expected types or nested templates.
        provided: The configuration dictionary to validate.
        path: The current path in the configuration (used in error messages), defaults to "config".

    Raises:
        ValueError: If the provided configuration is not a dictionary or if a required key is missing.
        TypeError: If a configuration value does not match the expected type.
    """
    if not isinstance(provided, dict):
        raise ValueError(f"{path} must be a dictionary")

    for key, expected_type in template.items():
        if key not in provided:
            raise ValueError(f"Missing required key: {path}['{key}']")

        if isinstance(expected_type, dict):
            validate_configuration(expected_type, provided[key], f"{path}['{key}']")

        elif not isinstance(provided[key], expected_type):
            raise TypeError(
                f"Expected {path}['{key}'] to be {expected_type.__name__}, "
                f"but got {type(provided[key]).__name__}"
            )
