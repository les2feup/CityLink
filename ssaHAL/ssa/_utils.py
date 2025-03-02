def singleton(cls):
    """
    Decorator that enforces the singleton pattern on a class.
    
    When applied to a class, this decorator returns a function that creates a single instance
    of the class. On the first instantiation, it prints a debug message and creates the instance 
    using the provided arguments; subsequent calls simply return the existing instance.
    """
    instance = None
    def getinstance(*args, **kwargs):
        """
        Retrieves the singleton instance of the class.
        
        If an instance does not already exist, creates it using any provided arguments
        and prints a debug message. Subsequent calls return the previously created instance.
        """
        nonlocal instance
        if instance is None:
            print("[DEBUG] SSA instance created")
            instance = cls(*args, **kwargs)
        return instance
    return getinstance
