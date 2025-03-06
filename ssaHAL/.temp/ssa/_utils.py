def singleton(cls):
    instance = None

    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            print('[DEBUG] SSA instance created')
            instance = cls(*args, **kwargs)
        return instance
    return getinstance
